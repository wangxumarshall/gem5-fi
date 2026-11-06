# LSU Platform v3.2.1 — Data-Value Propagation Repair

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use `- [ ]` checkboxes.

**Goal:** Upgrade the existing v3.2 Trace from event/address propagation to real data-value propagation, real request/response identity, explicit producer-consumer edges, forwarding decisions, and observable replay/squash, without changing the 12 models, 60 samples, or seeds.

**Architecture:** Extend CHAOSPropagation's CSV node contract with data hashes/hex, unique request/response/fragment IDs, LQ/SQ IDs, and explicit `prop_edge` rows. Convert those to Trace v3.1 JSONL. Add real replay/squash hooks in LSQUnit. Add F6 forwarding decision nodes. Wire EventOrdinal into the C++ trigger for A01/A03/FW02.

**Spec:** user v3.2.1 task + `LSU_End_to_End_Propagation_Audit_v3.2.md`.

## Global Constraints

- Preserve 12 models, 60 SampleRunIDs, original RunID/SubTaskID/Seed, F0/F5/F6 intent, W1-W8.
- No 60 formal runs; no history deletion; no fabricated propagation edges or values.
- Null remains null when gem5 does not expose a field.
- Every claim must be backed by a real run log/trace.

## Review Focus

1. PA must never be written as load/writeback data.
2. Consumer edges must come from the taint set / physical-register dependency, not ptag order.
3. Entry generations and request/response IDs must be real counters, not dyn_inst_seq aliases.
4. Replay/squash nodes must come from actual LSQ reschedule/squash paths.
5. EventOrdinal must select the real target event; seeds alone are not context coverage.

---

### Task 1: Data-value fields and explicit IDs in CHAOSPropagation

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{hh,cc}`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/lsu_unit.cc`, `lsq_unit.hh`
- Test: real A01/A03/FW02 runs after rebuild.

- [ ] Add `writeNode` return value and `writeEdgeRow`.
- [ ] Add request/response/fragment counters keyed by `Request*`.
- [ ] Record packet data length, FNV hash and hex (bounded) in `resp`.
- [ ] Record writeback value/hash, phys/arch reg, source response node in `taint_reg`.
- [ ] Record `lq_entry_id`, `sq_entry_id`, `entry_generation`, `execution_attempt_id`, `replay_generation`, `commit_seq`.
- [ ] Emit explicit `prop_edge` rows for taint→consumer with source/destination value hashes.
- [ ] Build and run A01/A03/FW02; verify no null data on resp/writeback.

### Task 2: Replay/Squash hooks

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/{hh,cc}`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/dyn_inst.hh`

- [ ] Add `noteReplay(inst, reason)` and `noteSquash(inst, reason)`.
- [ ] Call at real `rescheduleMemInst` sites and LSQ `squash` loop.
- [ ] Add `executionAttemptId`/`replayGeneration` fields and increment at execute/replay.
- [ ] Run W7 pilot-like workload; if no replay/squash occurs, record zero honestly.

### Task 3: Store-to-load forwarding decision record

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/{hh,cc}`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/{hh,cc}`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`

- [ ] Add `noteForwarding(ptag, load_seq, store_seq, addr, size, store_data, fwd_data, decision)`.
- [ ] FW02 suppression records store_seq/load_seq, store data hash, byte range, `decision=suppressed`, `memory_path=1`.
- [ ] Normal full-coverage forwarding records source store and forwarded data hash.
- [ ] Re-run FW02; JSONL must contain the trigger pair.

### Task 4: EventOrdinal / R01-R05 C++ wiring

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/{hh,cc,py}`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/{hh,cc,py}`
- Modify: `configs/se/lsu_proxy.py`
- Modify: `platform/run_pilot.py`

- [ ] Add `eventOrdinal` to F0/F5 trigger selection; F0 fires at warmup+ordinal, F5 starts at warmup+ordinal.
- [ ] Add F6 ordinal to FW02 (`f6_observed == ordinal`).
- [ ] Pass Excel `EventOrdinal` into the pilot command; record `event_ordinal` and actual observed ordinal in trace/meta.
- [ ] Re-run A01/A03/FW02 with ordinal 1; verify trace event ordinal matches.
- [ ] Run R01-R05 ordinal sweep (5 per model) and record distinct target seq/addresses.

### Task 5: Trace/terminal completeness split

**Files:**
- Modify: `platform/trace_completeness.py`, `platform/terminal.py`, `platform/trace_writer.py`
- Modify: `LSU_Trace_Schema_v3.2.json`

- [ ] Add `TraceRecordIntegrity`, `PropagationCoverage`, `OracleOutcome` independent fields.
- [ ] Do not infer MASKED from checksum equality without data-value evidence.
- [ ] Add tests for schema-valid but propagation-incomplete traces.

### Task 6: v3.2.1 pilots, workbook, audit package

**Files:**
- Update: `pilots/{A01F0,A03F5,FW02F6}`
- Update: `gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.1.xlsx`
- Create: `LSU_End_to_End_Propagation_Audit_v3.2.1.zip`

- [ ] Re-run three pilots with new binary; save all artifacts.
- [ ] Verify actual data values in JSONL, explicit consumer edges, forwarding pair, replay/squash state.
- [ ] Set formal WarmUp/ROI to `NEEDS_RESEARCHER_CONFIRMATION`; do not use pilot 0/full as formal authority.
- [ ] Package real logs/traces/diffs and unresolved list.

### Task 7: Gate 3 continuation

- [ ] Safety review LQ04/RP01.
- [ ] Implement next model only after Tasks 1-4 pass; do not block other models on one BLOCKED model.
- [ ] Record per-model status honestly.
