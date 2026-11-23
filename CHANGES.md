# WHEN-5X3 MMU final-evidence correction — change notes

## Round 0202c — 23-chain propagation completion (observation-only)

2026-11-17 · `gem5-fi-mmu-when5x3`.  No git commit / push.  Frozen
Where/When semantics unchanged (all 8 re-run Controls reproduce frozen N).
Re-runs in `runs/W5X3_RETRY2/`; originals untouched.

- **FULL 117 / PARTIAL 0 / N/A 3** (was 94/23/3).  All 23 remaining chains
  closed with real causal edges.
- **gem5 observational instrumentation (5 files, trace-only)**:
  1. `CHAOSPropagation.{hh,cc}` — IFU hooks (`mmuTakeFetchTxn` /
     `mmuNoteIfuResponse` / `mmuRegisterFetchSeq`; `mmu_req_txn` keyed by
     real Request identity), M05 poisoned-DTB-entry registration, bounded
     warm-hit fan-out (`MMU_CONSUMER_REUSE_CAP=16`), `masked_reason`.
  2. `fetch.{cc,hh}` — `fetchBufferTxnId[tid]` threads the fetch translation
     through `finishTranslation` → `processCacheCompletion` →
     `buildInst`; emits `ifu_response` / `ifu_decode`.
  3. `tlb.cc` — M05 in `phase3_entry_model`; bounded warm-hit adoption.
- **Class results**:
  - 12 instruction-fetch chains (M03/M04/M05-C02, M07-C05): IFU
    response/decode/commit now fault-tagged via `translation_id` +
    real `dyn_inst_seq`.
  - 6 M05-C04/C05 commit-consumer + 3 M05-C03 masked: poisoned-DTB-entry
    warm-hit adoption reaches the fault-tagged committing consumer.
  - 2 M07-C02 masked: explicit `masked_reason`.
- **Binaries**: `eb327197c073dddf…` (IFU + masked_reason) and
  `fb1b6f010034f273…` (bounded fan-out; M05 data faults re-run under it).
- **Evidence-index fix**: `analysis/retry2_map.json` +
  `retry2_evidence_index.json`; `finalize/export_evidence/acceptance/validate`
  resolve fault manifests to RETRY2 (fixes the round-0202b stale-path /
  trace-SHA mismatch).  `validate.py` ALL CHECKS PASSED; A01–A22 all PASS.
- `campaign/propagation.py`: `ifu_response`/`ifu_decode` stage mapping,
  `fault_entry_lineage` edge basis, M05 mutation handoff, `masked_reason`
  not-applicable declaration.

---

Round 0202 + 0202b · 2026-11-17 · `gem5-fi-mmu-when5x3`
No git commit / push / branch operation.  Frozen Where/When semantics and all
historical raw results are untouched.

## 0. Round 0202b additions (unfinished-chain completion)

- **M01 13 → FULL** (analysis-only, no re-run): 8 retained-entry→DTB-entry
  UNKNOWN edges resolved via `mutation_handoff()` (explicit disarming-hit + DTB
  insert bridge already in the raw trace); 5 ACTIVATED_UNCONSUMED resolved by
  recognizing the explicit `mmu_fault_unconsumed` endpoint event.
- **gem5 observational changes (2)**, rebuilt (new SHA256
  `d720e508206b6c94eb36a26ffb3f1e6f2db93459d8abfa58f1e7014db7047efa`):
  1. `src/arch/arm/mmu.cc` — M07 Execute activation joins the open synthetic
     fetch transaction via `mmuTxnForVa` (was `translation_id=0` / co-temporal).
  2. `src/arch/arm/tlb.cc` — M04 Execute activation mints the consumer
     transaction from `chaosLookupSyntheticSeq` (was no translation at all).
  Both are trace-only (no fault-injection semantics change).
- **Targeted re-runs** (into `runs/W5X3_RETRY/`, originals untouched): M07-C05
  and M04-C02 Control + T01/T02/T03.  New-build Controls match old N (M07 N=3,
  M04 N=20005).  Result: M04-C02/M07-C05 causal chains are now explicit
  (translation_id + parent_event_id + fault-tagged downstream), still
  PARTIAL_ARCHITECTURE (IFU response/decode/commit NOT_EMITTED).
- **Final completeness: FULL 94 / PARTIAL 23 / N/A 3.**

## 1. Four-dimensional completeness (was: conflated "file = chain")

`campaign/finalize.py` + `campaign/acceptance.py` + `campaign/propagation.py`
now report four orthogonal dimensions per sample:

- **file** — raw trace present with a recorded sha256
- **edges** — every causal edge carries an explicit basis (no UNKNOWN)
- **terminal** — an observed terminal endpoint exists
- **architecture** — every expected stage observed (no NOT_EMITTED boundary, no
  raw gap)

FULL requires all four.  Result: **FULL 94 / PARTIAL 23** (the previous 96
FULL collapsed because 27 of them had unobserved/NOT_EMITTED stages and were
silently counted complete).  The deficient dimension is named per sample
(`PARTIAL_ARCHITECTURE`, `PARTIAL_EDGES`, `PARTIAL_TERMINAL`, `FILE_MISSING`).

`experiment_status.csv` gains `FileComplete` / `EdgesExplicit` /
`TerminalObserved` / `ArchitectureComplete` / `Completeness` columns;
`analysis/completeness.csv` mirrors them.

## 2. Multi-branch DAG + correct SDC terminal (was: first consumer, even if squashed)

`campaign/propagation.py`:
- `build_branches()` splits the fault-tagged stream into consumer branches by
  translation_id, associating the zero-translation_id consume/reuse anchors via
  `parent_event_id`/`request_id`.
- `select_effect_branch()` uses the tracer's own summary anchors
  (`result_event_id`, faulted `tlb_entry_id`/`entry_generation`) then the first
  committing branch.
- `resolve_terminal()` applies the tracer's `faulting_inst_squashed` signal so a
  replay squash (walk still completes) is not reported as the terminal.

Result: **12 SDC samples that previously terminated on a squash now terminate on
a commit (M01) or a declared lsu_request boundary (M05 C04/C05)**.  Zero SDC
samples terminate on a squash.  `analysis/chain_branches.csv` records the DAG.

## 3. M04-C02 / M07-C05 re-review

- M07-C05 (3): recovered from the existing trace via the co-temporal
  permission_eval join (terminal = Execute lsu_request; IFU commit NOT_EMITTED).
- M04-C02 (3): re-read the full trace; only activation + lineage are
  fault-tagged (downstream fetch NOT_EMITTED by the frozen binary).  Recovery
  would require observational instrumentation in the gem5 TLB tracer + a
  targeted Fault/Control re-run; recorded as a declared boundary, not performed.

## 4. M06-C05 N/A wording (A06/A21)

Clarified that the 3 N/A are a **feasibility boundary of the frozen
configuration validated by the Pilot run**, not a global infeasibility claim.

## 5. Automated validation

`campaign/validate.py` — re-derives status counts, granular terminal states,
four-dimensional completeness, per-model FULL/PARTIAL, and the SDC-terminal
invariant directly from `per_condition.json` + manifests, and asserts they match
`experiment_status.csv` / `acceptance.json` / `final_acceptance.md`.  Exits
nonzero on any mismatch.

```
python3 campaign/validate.py   # ALL CHECKS PASSED
```

## Regenerated artifacts

`experiment_status.csv`, `run_manifest.json`, `analysis/per_condition.json`,
`analysis/propagation_chains.csv`, `analysis/chain_branches.csv`,
`analysis/chain_edges.csv`, `analysis/completeness.csv`,
`analysis/fault_control_compare.csv`, `analysis/summary_by_model.csv`,
`analysis/per_model_propagation.md`, `acceptance.json`, `final_acceptance.md`,
`blocked_tasks.md`, `FINAL_EVIDENCE_REPORT.md`.
