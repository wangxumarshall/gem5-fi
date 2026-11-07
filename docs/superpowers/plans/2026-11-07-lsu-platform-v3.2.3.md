# LSU v3.2.3 — Propagation Judgment Closure + SQ01 Start

**Goal:** fix the four audited defects (address-match clearing, A01-R03
terminal, propagation coverage, replay commit), separate observed terminal from
fault causality, then start SQ01. No formal 60-sample run; no change to the 12
models, 60 samples or seeds.

**Branch:** `lsu-platform-v3.2.3` in the existing v3.2 worktree, base `97fb263f`.

---

## Task 1 — address-match bug + structured fault evidence

- [ ] Move `events = []` before the A01/A03 branch; never clear after reading.
- [ ] Parse the Page Table Fault address from stderr and record it in a
      structured `simulator_abort` event and in `pilot_meta` (not stderr-only).
- [ ] Re-run A03 R01–R05; verify last injection dyn seq 1146, new address
      `0xffffffffffb73c50`, PT fault address identical → `DIRECT_ADDRESS_MATCH`.

## Task 2 — A01-R03 SQUASHED

- [ ] When MASKED lacks data values, test: squash node for the fault seq and no
      commit/consumer for it → `SQUASHED` (reason `TARGET_SQUASHED_NO_COMMIT`);
      otherwise `UNRESOLVED`.
- [ ] Update JSONL summary, pilot_meta and the sweep consistently.

## Task 3 — PropagationCoverage profiles

- [ ] Expected stages per (model, terminal): A01 MASKED/SQUASHED/CRASH,
      A03 CRASH/SQUASHED, FW02 MASKED/CRASH.
- [ ] Missing required stage → PARTIAL; no stages → NONE.
- [ ] RecordIntegrity, TraceCompleteness and PropagationCoverage judged
      independently.

## Task 4 — replay-tracked commit

- [ ] Register every replay-tracked dyn seq; `noteCommit` emits a real commit
      node for it with dyn seq, attempt, replay generation, commit_seq.
- [ ] Squash remains from the real LSQ squash path.
- [ ] Re-run the replay pilot; all 5 replays must have a commit or squash node.

## Task 5 — FaultCausality and accepted semantics

- [ ] Add `fault_causality`: DIRECT_ADDRESS_MATCH / DIRECT_DATAFLOW_EVIDENCE /
      INDIRECT_EVIDENCE / TEMPORAL_ASSOCIATION_ONLY / UNKNOWN.
- [ ] `observed_terminal` and `fault_causality` are separate fields in meta,
      JSONL summary and sweep.
- [ ] `accepted` means the record is valid; it does not assert causation.

## Task 6 — rerun and evidence

- [ ] Rebuild, 15-context sweep, replay pilot, unit tests; commit each unit.

## Task 7 — SQ01

- [ ] Unique fault: SQ entry byte0 bit3 after `LSQUnit::write()`.
- [ ] Real hook, config parsing, F0 trigger, unit test, compile, target-event
      proof, trace node, independent pilot on `sq_drain`.
- [ ] Safety note: data-only, one entry, no state-machine change.

## Task 8 — package

- [ ] `LSU_v3.2.3_Propagation_Closure_Package.zip` + status report.
