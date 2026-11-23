# WHEN-5X3 per-model propagation summary (multi-branch, 0202c)

Identity-based causal chains reconstructed from the raw PROP-EVT stream by
`campaign/propagation.py`.  The terminal is a **multi-branch DAG**: every
consumer transaction (origin + later reuses) of a faulted state is a branch,
and the terminal is the branch that actually commits the fault's effect —
never a transient squash on the first consumer.

## Four completeness dimensions

Every COMPLETE sample is scored on four orthogonal dimensions (see
`analysis/completeness.csv` and `acceptance.json` → `CausalCompleteness`):

| dim | meaning |
|---|---|
| **file** | raw trace present with a recorded sha256 |
| **edges** | every recorded causal edge carries an explicit basis (no UNKNOWN) |
| **terminal** | an observed terminal endpoint exists |
| **architecture** | every expected stage observed (no NOT_EMITTED boundary, no raw gap) |

`FULL` = all four.  A stage the frozen binary does not emit is a declared
**boundary** (NOT_EMITTED_BY_FROZEN_BINARY), distinct from a structural
**not-applicable** (e.g. M06 detection has no LSU request) and from an honest
**unobserved** gap.

Terminal-state totals: SDC 74, ACTIVATED_MASKED 17,
PROPAGATED_BUT_SQUASHED 9, ACTIVATED_UNCONSUMED 5, DETECTED_DELIVERED 9,
DETECTED_LOCALLY 3, N/A 3 (=120).  Causal completeness **FULL 117 / N/A 3**.

## Per-model

- **M01** (retained-entry stale DTB): FULL 15/15.  The retained entry's stale
  PA is cached into a DTB entry and reused by later consumers; terminal is the
  first committing consumer; T03 is a natural `mmu_fault_unconsumed` endpoint.
- **M02** (leaf-PFN refill corrupt): FULL 15/15.  Corrupted refill → entry
  lineage → committing consumer.
- **M03** (lookup pointer substitution): FULL 15/15.  C02 (instruction-side)
  now carries the complete IFU chain: `mmu_fault_activate → tlb_lookup_hit →
  translation_result → lsu_request(Execute) → ifu_response → ifu_decode →
  commit` (0202c IFU instrumentation).
- **M04** (resident PFN substitution): FULL 15/15.  C02 fetch chain closed by
  the 0202c IFU instrumentation (activation → lineage → consume →
  translation_result(decoy) → lsu_request(Execute) → ifu_response →
  ifu_decode → commit).
- **M05** (partial next-table-base substitution): FULL 15/15.
  - C02 (instruction-side partial walk): full IFU chain.
  - C03/C04/C05 (data side): the corrupted partial entry poisons the DTB
    entries a faulted walk fills; the 0202c bounded warm-hit adoption tags the
    committing consumer (`partial_entry_insert → tlb_entry_insert →
    fault_entry_reuse → translation_result → lsu_request → memory_response →
    rf_writeback → commit`).  C03 is ACTIVATED_MASKED (committed decoy value,
    oracle unchanged); C04/C05 are SDC.
- **M06** (descriptor bit clear): FULL 12, N/A 3 (C05 speculative wrong-path —
  frozen-configuration feasibility boundary, see `blocked_tasks.md`).
- **M07** (permission grant inversion): FULL 15/15.  C05 (Execute fetch) closed
  by the 0202c IFU instrumentation; C02 (read_exec_only) is ACTIVATED_MASKED
  with an explicit `masked_reason=request_issued_not_completed_at_roi_end`
  (the inverted-grant access was issued but never consumed).
- **M08** (request PA flip): FULL 15/15.

## Totals

| Model | FULL | N/A |
|---|---:|---:|
| M01 | 15 | 0 |
| M02 | 15 | 0 |
| M03 | 15 | 0 |
| M04 | 15 | 0 |
| M05 | 15 | 0 |
| M06 | 12 | 3 |
| M07 | 15 | 0 |
| M08 | 15 | 0 |

**Total FULL 117 / N/A 3.**  Each row is traceable to the sample's
`analysis/per_condition.json` chain and its raw trace under
`runs/W5X3/` or `runs/W5X3_RETRY2/`.
