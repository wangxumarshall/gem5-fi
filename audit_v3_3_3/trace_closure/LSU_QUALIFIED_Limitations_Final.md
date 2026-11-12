# LSU v3.3.3 — Final QUALIFIED / Documented Limitations

**Freeze date:** 2026-11-12
**Status:** `READY_WITH_DOCUMENTED_LIMITATIONS`

## 1. SP05 R01–R05 — `QUALIFIED` (5 contexts)

**Root cause:** SP05 is a **lost-writeback** fault: the selected store is completed before its
cache write is sent (`write_skipped=1; mem_sent=0; stores_to_wb_after=0`). A positive
`writeback_event` therefore **does not exist** in this fault.

**What is now proven (real evidence, no fabrication):**

- real architectural commit: `store_commit`, `commit_tick_source=commit_stage_capture`,
  `commit_tick < inject_tick` (Δ=770 ticks on all five);
- independent negative evidence: `store_writeback_suppressed` with
  `writeback_state=SUPPRESSED_BEFORE_SEND; request_sent_before=0; request_sent_after=0;
  mem_sent=0; write_skipped=1; drain_tick=0; visibility_tick=0; visibility_state=NEVER_WRITTEN`;
- reload of the old value: `reload_data_hash=a8c7f832281a39c5`;
- consumer commit (`errant_commit`) and the application oracle (`ORACLE_FAIL`), byte-identical to
  the frozen baseline.

**Why it stays `QUALIFIED`:** the frozen `SP05_FIELDS` rule requires a positive
`writeback_event`. `store_writeback_suppressed` is deliberately not named `writeback` and is not
accepted as one. No PASS upgrade was performed.

**Researcher decision needed only if a PASS label is required:** redefine the field as a
writeback *outcome* accepting `SUPPRESSED_BEFORE_SEND`. This round did **not** make that
redefinition.

## 2. RP01 R01–R05 — `TRACE_INCOMPLETE` (5 contexts)

**Root cause:** the RP01 fault intentionally skips a replay reschedule and stalls the ROB; the
model's internal watchdog terminates the simulation through `fatal()`/`::exit(1)`. The run stops
at the expected HANG terminal; it is not a normal execution.

**What is now proven:**

- `trace_flush_start` → `watchdog_terminal` → `trace_flush_complete` present exactly once each;
- `last_valid_event_id` / `prev_last_event_id` = 5282/5486/5690/5894/6098, matching the previous
  node of each historical trace;
- `terminal_source=MODEL_INTERNAL_WATCHDOG`; `fault_id=1`, eligible 26/77/128/179/230;
- last eligible load/PC/LQ/SQ, `replay_decision=SKIP`, `replay_skip=1`, LQ/SQ occupancy,
  `silent_ticks` ≈ 7.68e9 (true no-progress, not lost data);
- gzip container valid (`gzip -t` OK).

**Why it stays `TRACE_INCOMPLETE`:** the simulation genuinely stopped at the watchdog. Terminal
metadata completeness must not be described as normal-execution trace completeness.
`stats.txt` remains 0 bytes because `stats.dump` runs on the Python `atexit` path skipped by
`fatal()`; fixing it would require changing the termination path or periodic stat dumps, which
was out of scope for a read-only observation hook.

## 3. A03-R02 — not a limitation

A03-R02 is `COMPLETE_CAUSAL_CHAIN` (SDC). 13718 is a squashed speculative instance; the causal
anchor is 13772 (`resp 0xab → taint x1 → consumers 13774/13775 → checksum d48b947fc08d5a75`).
The squash is preserved as provenance, not used as the terminal.

## 4. Official wording for the paper/report

> 49 contexts use historical Pre-Formal evidence under binary `1126e0fd…`; 11 restricted
> contexts were re-run under final binary `62e1b1be…`. The final 60-context synthesis is a
> classification/readiness product, not a single-binary 60-run formal result set. The formal
> campaign will re-run all 120 tasks under the final binary.
>
> SP05 remains `QUALIFIED` because the frozen `writeback_event` field is unsatisfiable for a
> lost-writeback fault; the actual commit and suppressed-writeback outcome are fully evidenced.
> RP01 remains `TRACE_INCOMPLETE` because the watchdog HANG is the expected terminal; the terminal
> record set is complete.
