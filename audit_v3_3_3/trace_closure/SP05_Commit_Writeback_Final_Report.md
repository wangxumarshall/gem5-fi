# SP05 Commit / Writeback Trace Hook — Final Report

**Model:** SP05 (premature store completion / lost writeback) · **Contexts:** R01–R05
**New binary:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
**Config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Evidence:** `audit_v3_3_3/trace_closure/runs/SP05-R0{1..5}-{fault,control}/`
**Status:** **Commit event: FIXED (real architectural commit). Writeback: honestly SUPPRESSED, not fabricated. Qualified status remains `QUALIFIED` under the frozen field rule (only `writeback_event` missing).**

## 1. Root cause

- **Commit**: the target store's architectural commit happens in `Commit::commitHead`
  (`commit.cc:1318`) **before** the SP05 injection point (`writebackStores`, `lsq_unit.cc:1072-1101`).
  The target identity is only registered when the fault is injected, so `noteCommit` had no way to
  know which store to capture. The old record's `commit_tick` was the injection tick and was
  correctly labelled `commit_tick_source=caller_supplied`; the grader rejects it.
- **Writeback**: SP05's semantics is deliberately a **skipped cache write**
  (`write_skipped=1; mem_sent=0; stores_to_wb_after=0`). A positive `writeback_event` does not
  exist in this fault. The old `sp05_write_skipped` record is negative evidence and must not be
  relabelled as a writeback.

## 2. Implementation (read-only hooks)

| Hook | Location | What it records |
|---|---|---|
| H1 capture | `CHAOSPropagation::noteCommit` (`CHAOSPropagation.cc`) | While `CHAOSLSQFwd::sp05Mode()`, capture `commit_tick`, tracer `commit_seq`, PC, SQ idx/generation, size, attempt, replay generation for every committing store. |
| H2 `store_commit` | `CHAOSPropagation::noteSP05Injection` | Emit one `store_commit` node on the injection ptag **before** `inj_sp05`; timestamp = the real commit tick; `commit_state=ARCHITECTURAL_COMMIT`, `commit_tick_source=commit_stage_capture`. |
| H3 `store_writeback_suppressed` | `LSQUnit::writebackStores` after `completeStore()` | Emit one negative-evidence node: `writeback_state=SUPPRESSED_BEFORE_SEND; request_sent_before=0; request_sent_after=0; mem_sent=0; write_skipped=1; drain_tick=0; visibility_tick=0; visibility_state=NEVER_WRITTEN`. |
| H4 honest tick | `noteSP05Injection` | Removed the caller-tick fallback. A missing capture records `commit_tick=0; commit_tick_source=unavailable`; never a fabricated tick. |

Event format: all nodes use the existing CSV row (`node_id,tick,ptag,kind,dyn_inst_seq,…`) and the
existing `ptag` chain. `fault_id` / `event_id` / `parent_event_id` remain the shared converter's
fields; no per-model ID system was introduced.

Ordering observed on every run: `store_commit` → `inj_sp05` → `sp05_write_skipped` →
`sp05_complete` → `store_writeback_suppressed` → reload/consumer. `sp05_complete` is emitted
inside the real `completeStore()`; the suppression record follows the completion (the code
captures the pre-completion counters so the post-completion values are honest). Commit is
structurally earlier than injection because `canWB` is granted only after `doneSeqNum` has
advanced and `writebackStores()` runs before `commitStores()` in the same cycle.

## 3. Validation (new binary, 5 Fault + 5 Control)

| Ctx | store_seq | commit_tick | inject_tick | source | mem_sent | request_sent_after | visibility | Qualified |
|---|---:|---:|---:|---|---:|---:|---|---|
| R01 | 13328 | 16376745 | 16377515 | commit_stage_capture | 0 | 0 | NEVER_WRITTEN | QUALIFIED |
| R02 | 15122 | 17005835 | 17006605 | commit_stage_capture | 0 | 0 | NEVER_WRITTEN | QUALIFIED |
| R03 | 16847 | 17492475 | 17493245 | commit_stage_capture | 0 | 0 | NEVER_WRITTEN | QUALIFIED |
| R04 | 18641 | 17991435 | 17992205 | commit_stage_capture | 0 | 0 | NEVER_WRITTEN | QUALIFIED |
| R05 | 20435 | 18632460 | 18633230 | commit_stage_capture | 0 | 0 | NEVER_WRITTEN | QUALIFIED |

- `commit_tick < inject_tick` on all five (Δ=770 ticks); `store_commit` and injection share the
  target `dyn_inst_seq / pc / sq_entry_id / sq_entry_generation`; the injection's parent is the
  `store_commit` event.
- Exactly one `store_commit` and one `store_writeback_suppressed` per fault run; zero of either in
  the five controls. Controls have `injection_count=0`, `ORACLE_PASS`.
- Reload evidence: `reload_data_hash=a8c7f832281a39c5` (the old zero word) on all five; the store's
  intended bytes are `b6180e0c195fd2e9 / 9f995d89be67e92d / fde383c67ac034f1 /
  aa2be3d3d60e3c9d / c7d78aff5e06edf9`.
- Oracle output is byte-identical to the frozen baseline:
  R01 `c7a1b3a591c68328`, R02 `34890178967da568`, R03 `225c6839dd319a5c`,
  R04 `d42d86ee46895884`, R05 `c6e1c98b1480efd4` (expected `7df5034c23f3e703`).

## 4. Honest status

- **`commit_event` is now found from a real observation**, not a caller-supplied tick.
- **`writeback_event` remains missing** because the fault's mechanism is "the cache write did not
  happen". `store_writeback_suppressed` proves the negative outcome together with the reload's old
  value; it is deliberately not named `writeback` and does not satisfy the frozen field.
- Therefore the five SP05 contexts remain **`QUALIFIED`** (missing only `writeback_event`) and are
  classified **`QUALIFIED`** in the final readiness table. The mechanism chain is fully observed,
  but the frozen field rule still blocks a `COMPLETE_CAUSAL_CHAIN` / `PASS` label. No PASS upgrade
  was performed.

## 5. Behavior impact

No change to instruction order, LSU scheduling, `canWB`/`storesToWB`, store/load decisions,
forwarding, replay, commit decisions, injection time/probability/state, or RNG consumption. The
hooks are single-threaded reads/writes of trace data under the existing per-node `Z_SYNC_FLUSH`
contract. Binary SHA changes, so all formal manifests must be re-frozen (done in
`final_config/`).

## 6. Residual limitations

1. `store_commit` is written at injection time with the real commit timestamp; if an auditor
   requires the commit record to be on disk at commit cycle, H2 can be moved to the target-selection
   point, but this does not change the evidence.
2. `stats.txt` and `trace_v31.jsonl` generation are unchanged.
3. The SP05 selector still does not exclude LLSC/release stores; the five frozen targets are
   ordinary stores at `pc=0x40053c`, so this did not affect this round. Excluding them would change
   injection eligibility and must be a separately approved change, not part of an observation hook.
