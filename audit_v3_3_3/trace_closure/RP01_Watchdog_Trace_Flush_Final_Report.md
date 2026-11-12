# RP01 Internal-Watchdog Trace Flush — Final Report

**Model:** RP01 (replay suppression) · **Contexts:** R01–R05
**New binary:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
**Config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Evidence:** `audit_v3_3_3/trace_closure/runs/RP01-R0{1..5}-{fault,control}/`
**Status:** **Terminal record set COMPLETE (`trace_flush_start` → `watchdog_terminal` → `trace_flush_complete`). The run remains `TRACE_INCOMPLETE` by construction (the simulation stopped at the internal watchdog); no upgrade was performed.**

## 1. Root cause

`CHAOSLSQFwd::rp01Watchdog()` called `fatal()`, which is `Logger::getFatal()` →
`FatalLogger::exit() { ::exit(1); }` (`base/logging.cc:65-71`). `::exit(1)` does **not** run
gem5's Python `atexit` exit callbacks (`simulate.py:262-265` → `sim/core.cc:153-157`), so the
terminal record, deferred chain records and the gzip trailer were never written. The pre-watchdog
history was **not lost**: every node is followed by `gzflush(Z_SYNC_FLUSH)`
(`CHAOSPropagation.cc:190-220`). The file was a trailer-less but readable prefix; `stats.txt`
stayed 0 bytes because `stats.dump` also runs on the skipped `atexit` path.

## 2. Implementation (read-only flush before fatal)

- `CHAOSPropagation::flushWatchdogTerminal(const WatchdogTerminalInfo &)`:
  - idempotent (`terminal_flushed` set before writing);
  - writes `trace_flush_start` → `watchdog_terminal` → `trace_flush_complete` through the existing
    `writeNode()` path (same CSV/ID/`gzflush` contract);
  - records trigger, reason, fault ID, last valid event ID, last eligible dynamic instruction,
    replay eligibility/decision/skip, LQ/SQ occupancy and heads, LSU stalled, last trace tick,
    silent ticks, commit sequence and last commit;
  - ends with `gzflush` + `gzclose` so the gzip container is valid; **does not** mark the trace
    COMPLETE.
- `CHAOSLSQFwd::rp01Watchdog()` builds a POD snapshot and calls the flush **before** `fatal()`.
  New read-only bookkeeping: armed tick/cycles and the last eligible event identity in
  `maybeSkipPartialReplay` (it never feeds `shouldRP01Skip`).
- `CHAOSPropagation` tracks `last_node_tick`, `last_commit_dyn_seq`, `last_commit_tick`; `LSQ`
  gained read-only `getLSQUnit()`/`numLSQUnits()` accessors for the LQ/SQ snapshot.

Terminal classification remains the existing `terminal_source()` logic:
`MODEL_INTERNAL_WATCHDOG` for the in-simulator marker; `EXTERNAL_TIMEOUT` (exit 124) and
`PYTHON_TIMEOUT` (`timed_out`) can only be produced by the driver and are **physically unable**
to produce model-internal terminal nodes.

## 3. Validation (new binary, 5 Fault + 5 Control)

| Ctx | exit | timed_out | nodes (old→new) | prev/last event ID | eligible / skip | LQ / SQ | silent ticks | gzip |
|---|---:|---|---:|---|---|---|---:|---|
| R01 | 1 | false | 5283 → 5286 | 5282 / 5282 | 26 / SKIP | 1+15 / 0+16 | 7,683,031,125 | valid |
| R02 | 1 | false | 5487 → 5490 | 5486 / 5486 | 77 / SKIP | 1+15 / 0+16 | 7,681,638,580 | valid |
| R03 | 1 | false | 5691 → 5694 | 5690 / 5690 | 128 / SKIP | 1+15 / 0+16 | 7,679,986,545 | valid |
| R04 | 1 | false | 5895 → 5898 | 5894 / 5894 | 179 / SKIP | 1+15 / 0+16 | 7,678,594,000 | valid |
| R05 | 1 | false | 6099 → 6102 | 6098 / 6098 | 230 / SKIP | 1+15 / 0+16 | 7,676,958,135 | valid |

Each fault trace has exactly one `trace_flush_start`, one `watchdog_terminal` and one
`trace_flush_complete`, in node-ID order. The `watchdog_terminal` row includes
`terminal_source=MODEL_INTERNAL_WATCHDOG`, `trigger_reason=INTERNAL_WATCHDOG_DEADLINE`,
`fault_id=1`, `injected=1`, `last_valid_event_id`, last eligible load/PC/LQ/SQ, `replay_decision=SKIP`,
`replay_skip=1`, and `silent_ticks` ≈ 7.68e9.

Controls: 0 injection, exit 0, `ORACLE_PASS`, gzip valid, exactly the same node count as the old
controls (12817), and **zero** flush nodes — the watchdog is not armed at `probability=0`.

## 4. Honest status

- The terminal **metadata** is now complete and the trace container is valid.
- The run is still **`TRACE_INCOMPLETE`**: there is no architectural progress after the skip, no
  checksum, and the watchdog is the model's expected HANG terminal.
- `stats.txt` remains 0 bytes. That file is created at startup and only written by `stats.dump`
  on the Python `atexit` path; fixing it would require changing the termination path
  (e.g. `exitSimLoopNow`) or periodic stat dumps, which is outside a read-only observation hook
  and was not done.
- The `trace_v31.jsonl` file is absent because RP01 is dispatched by the `direct` driver; the
  qualified grader reads `prop_trace.csv.gz` instead.

## 5. Behavior impact / safety

No change to replay eligibility, `shouldSkip`, scheduling, injection probability/state, RNG, or
event order. `CHAOSPropagation` is a single-threaded per-CPU tracer with no locks; the flush does
only memory reads and local file writes, takes no port/SimObject locks, schedules no event, and is
idempotent. A second call (or a future exit callback) is a no-op.

## 6. Residual limitation

The terminal snapshot cannot include per-instruction ROB/IQ contents (the existing public ROB API
does not expose them); it records the LQ/SQ heads/occupancy and the last commit instead.
External/Python timeouts remain driver-classified and never receive model-internal terminal nodes.
