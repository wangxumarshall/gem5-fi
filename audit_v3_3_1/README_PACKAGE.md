# LSU v3.3.1 — Context & Workload Finalization Package

Date: 2026-11-11
Status: **PARTIALLY_READY** · `12_MODEL_FORMAL_READY = NO`
Binary: `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`
Base commit: `8f7a1354c36e9511505940dd27f59df66cb1b328`

## Headline

- Decision A (10/30/50/70/90 % of the per-model eligible stream) was executed
  for every model whose observation hook exposes the ROI.
- **40/60 contexts mapped**: 20 MAPPED (A01, FW05, DA04, LQ04), 5
  MAPPED_WITH_SEMANTIC_CAVEAT (A03), 15 MAPPED_ON_RECOMMENDED_WORKLOAD
  (SQ01/SQ03/SP05 on `sq_reload_v3212`, approval pending).
- **20/60 not mappable**: FW02 (W4 has no data load), MD04 (N_ROI=1),
  RP01 (W7 has no partial-overlap event), LP01 (record has no PC/VA).
- The v3.3.0 EventOrdinal 1–5 configuration is outside the ROI for A01/A03,
  DA04 ordinals 1–3, MD04 ordinals 1/2/4/5, and the SQ literal ordinals.
- SQ recommendation: `ADOPT_SQ_RELOAD` for all three, pending approval.
- Controls: 2/60 valid on the on-disk binary; 16 need redo; 42 missing.
- No formal campaign; no frozen design, seed, SampleRunID or workbook edit.

## Contents

```
report/
  LSU_v3.3.1_Finalization_Report.md     11-question report
  LSU_Researcher_Approval_Required.md   approval table A1–A10
  PROVENANCE.md, ROUND_LOG.md, ROUND_PLAN.md
  GIT_STATUS.txt, BINARY_SHA256.txt, SOURCE_DIFF.txt
roi/
  LSU_ROI_Boundaries.csv
  LSU_60Context_ROI_Percentile_Mapping.csv   60 rows
  LSU_60Context_Distinctness_Audit.csv       60 rows
  census/*.jsonl                             parsed census rows
  census/*/K*/                               injection/oracle logs + commands
propagation/
  LSU_60Context_Causal_Chain_Reaudit.csv     60 rows
controls/
  LSU_60Context_Control_Readiness.csv        60 rows
audits/
  Agent_B_Workload_Disassembly_Findings.md + LSU_12Model_Workload_Readiness.csv
  Agent_C_Causal_Reaudit_Findings.md
  Agent_E_Control_Readiness_Findings.md
sq_workload/
  SQ01_Workload_Comparison.md
  SQ03_Workload_Comparison.md
  SP05_Workload_Comparison.md
subagent_reports/
  Agent_F_Independent_Acceptance_v3.3.1.md
tools/ (at repo root)
  lsu_v331_census.py, lsu_v331_build_mapping.py
```

The prior v3.3.0 package extract is excluded from this ZIP; it remains at
`LSU_12Model_PreFormal_Readiness_Package.zip` in the worktree.

## Verification actually run this round

- `pytest tests/ -q` → **180 passed in 95.74s**
- platform tests → **107 passed in 3.45s**
- Census: 175 probes, 18 JSONL tags, 15 intentional post-activation timeouts
  with partial records retained.
- Independent Agent F: 12/15 checks confirmed; contradictions corrected and
  recorded in report §4.
