# LSU v3.2.11 — Final Report

**Branch / HEAD:** `lsu-platform-v3.2.11` @ **`f3bfd27b9cf3e78f1fddb4ee788f8b9d96163075`** (baseline `lsu-platform-v3.2.10` @ `1394fb49…`)
**Final binary SHA256:** `3dccaa10ec5073ca90f2622bd37d5adac1b705bd9faf2497c2d13e46beadd4ed`
**LQ04 workload SHA256:** `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba`
**RP01 workload SHA256:** `ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4`
**Formal 60-sample experiment: NOT_STARTED.**

## 0. Direct answers

### LQ04
1. **All four leftovers fixed?** Yes — (A1) the platform now emits separate `structural_chain_completeness` and `fault_effect_propagation_coverage` fields; (A2) the v3.2.6 workbook corrects the LQ04 hook line numbers and five stale cells across sheets 4/7/11; (A3) the watchdog exits through gem5's registered FAIL event with exit code 1; (A4) controls have role-exclusive validity. Historical pilots were not modified.
2. **Watchdog runtime-verified?** Yes — `CHAOS_LQ04_WATCHDOG_EXPIRED` at tick 7700000, exit=1, no `NotImplementedError`, gzip trace intact with 10011 events (last at tick 7699615), classification HANG (never MASKED). A normal completion still exits 0.
3. **Control semantics correct?** Yes — `run_role=CONTROL`, `control_valid=true`, `fault_activation_status=NOT_TRIGGERED`, `oracle_outcome=PASS`, `accepted=true` for a valid zero-injection control; a misfiring control is `control_misfire=true`, `accepted=false`.
4. **Final LQ04 propagation verdict:** `RecordIntegrity=VALID`, `TraceCompleteness=COMPLETE`, `StructuralChainCompleteness=COMPLETE`, `FaultEffectPropagationCoverage=LIFECYCLE_ONLY`, `PROPAGATION_VERIFIED=0`; 5/5 injections, 5/5 oracle PASS, 5/5 MASKED, no response loss, no wrong-data propagation, no application SDC.

### The 11 models
1. **Complete causal chains:** DA04 (2/5 unique pilots), LP01 (5/5), MD04 (3/5), FW05 (4/5). FW02 has 1/5 control-path chain (suppressed forward, identical data) and is not counted as a data-effect verified model.
2. **Lifecycle/local evidence only:** SQ01, SQ03, SP05, LQ04 (5/5 each; the corrupted lane/entry is never consumed).
3. **Propagation-chain gaps:** A01 and A03 are PARTIAL (wrong EA reaches the response/consumer, but there is no correct-EA reference value and the crashes are not address-matched); FW02 4/5 PARTIAL; DA04 3/7, MD04 2/5 and FW05 1/5 partial pilots (squash causality or a vintage without the chain).
4. **Terminal causality not yet proven:** A01/A03 crashes (address mismatch); FW02 R01/R05 and MD04 R01/R04 squashes; DA04 v3.2.4 R04/R05 (SDC terminal without a chain in that vintage).
5. **Supplementary experiments:** A01, A03, FW02, DA04 (raw oracle files), MD04 (squash reason), FW05 (R01 squash), SQ01, SQ03, SP05 — all listed in `SUPPLEMENTARY_PILOT_PLAN_v3.2.11.md`; none executed.
6. **Models truly verified: 4** (DA04, LP01, MD04, FW05).
7. **Verified pilots: 14/55 unique pilots** with a data-effect complete chain; **15/55** including FW02-R04's control-path chain.
8. **Terminal split (14):** SDC **6**, MASKED **8**, SQUASHED **0**, CRASH **0**. Including FW02-R04: SDC 6, MASKED 9.

### RP01
1. **Most reasonable candidate:** A (partial-forward replay loss at `lsq_unit.cc:2016`).
2. **Implementable in current gem5?** Yes, with conditions; the hook is real and distinct from MD04.
3. **HANG/state risk?** High — the expected terminal is HANG/TIMEOUT because the skipped load is never pushed to `instsToReplay`; watchdog/timeout is mandatory.
4. **Five dynamic contexts constructible?** Five distinct replay tuples are observed in an existing probe, but five contexts under the five frozen RP01 seeds are **not yet proven**; a clean count-only preflight is required.
5. **Need researcher modification/confirmation?** Yes. Gate = `IMPLEMENTABLE_WITH_CONDITIONS`; `DecisionStatus` remains `NEEDS_USER_DECISION`. No C++ was implemented.

### Formal experiment
- **Ready for 60 formal runs?** **No.**
- **Blockers:** RP01 definition approval and count-only preflight; supplementary evidence for the partial/lifecycle models; raw oracle files for DA04 R04/R05; Warm-up/ROI not frozen; `ConfigFrozen=NO`.
- **Warm-up/ROI frozen?** No — both remain `NEEDS_RESEARCHER_CONFIRMATION`.

## 1. Baseline and version management

- Delivery record HEAD `e11fbf82…` is an ancestor of the verified v3.2.10 tip `1394fb49…`; the two later commits are docs/package provenance commits already on origin. The binary at v3.2.10 matched `f3c2a442…`.
- Worktree: `.claude/worktrees/lsu-platform-v3.2.11`; branch `lsu-platform-v3.2.11`.
- Disk: 75 GiB free (> 70.6 GiB threshold); the 2.5 GiB extracted audit traces are gitignored scratch and regenerable from the archives.
- No `git reset --hard`, `git clean -fd`, or `git add -A` was used. Historical `pilots_v3_2_*` directories were not modified.

## 2. LQ04 closure

1. Definition freeze: `LQ04_Definition_Freeze_v3.2.10.md` (unchanged).
2. Fault-pilot evidence index: `pilots_v3_2_10/LQ04-R01..R05/` + `LQ04_PILOT_SUMMARY.csv`.
3. Control evidence index: `pilots_v3_2_10/LQ04-CONTROL-R01..R05/`.
4. Propagation semantics: `platform/fault_effect_coverage.py`, `trace_completeness.py`, `run_pilot.py`; LQ04 verdict `LIFECYCLE_ONLY`.
5. Excel source lines: `LQ04_Source_Audit_line_corrections_v3.2.11.md`; v3.2.6 cells G4/D20/F19/F33/F45.
6. Watchdog: `CHAOSLQ04.cc` + `lsu_proxy.py` exit-code propagation; `logs_v3_2_11/watchdog_fix.md` and smoke evidence.
7. Control semantics: `platform/run_roles.py` + `tests/test_run_pilot_control.py`; historical controls untouched.
8. Research adjudication: `LQ04_ResearchAdjudication_v3.2.11.md`.

**Honesty note:** the first Excel commit (`123b16d5`) was followed by test failures in two v3.2.6 workbook invariants that still assumed "only five cells differ". The follow-up `f3bfd27b` extends those invariants to the new Notes column and audit sheet; all 67 relevant tests pass at HEAD. The failure and fix are recorded here rather than hidden.

## 3. 11-model audit

- Matrix: `audit_v3_2_11/LSU_11Model_Propagation_Audit_Matrix.csv` (20 columns, 11 rows).
- Summary: `audit_v3_2_11/LSU_11Model_Propagation_Audit_Summary_v3.2.11.md`.
- Per-model reports: `audit_v3_2_11/<MODEL>_Propagation_Audit_v3.2.11.md` + `<MODEL>_verdict.json`.
- Evidence extraction: `audit_v3_2_11/EVIDENCE_EXTRACTION.md` (35 hash matches, 5 SQ01 sibling-vintage divergences documented; no pilot missing=HASH_MISMATCH).
- Supplementary plan: `audit_v3_2_11/SUPPLEMENTARY_PILOT_PLAN_v3.2.11.md`.
- Methodological finding: the generic payload check under-reports LP01 and FW05; their model-specific `orig/inj` and `true/alt` records are the decisive evidence and are quoted in the reports.

## 4. RP01 design

- `rp01_design_v3_2_11/RP01_Source_Audit_v3.2.11.md` (exact lines, normal/fault paths, Q-A/B/C/D).
- `RP01_Candidate_Comparison_v3.2.11.md` (A/B/C, recommendation A, conditions).
- `RP01_Workload_Verification_v3.2.11.md` (hash/oracle verified; partial-forward capability observed; count-only preflight still required).
- `RP01_Dynamic_Contexts_v3.2.11.md` (five observed events, mapping hypothesis, preflight plan).
- `RP01_Final_Design_Gate_v3.2.11.md` (12 items, `IMPLEMENTABLE_WITH_CONDITIONS`).

## 5. Authoritative configuration

- Excel: `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx` (v3.2.5 + LQ04 line corrections + sheet 20 audit + v3.2.11 change log).
- `MODEL_STATUS_MATRIX.csv`: PROPAGATION_VERIFIED=1 for DA04/LP01/MD04/FW05; 0 for the rest; LQ04 0; RP01 SOURCE_AUDITED=1, IMPLEMENTED=0.
- 60 SampleRunIDs/RunIDs/SubTaskIDs/Seeds unchanged; `ConfigFrozen=NO`; Warm-up/ROI `NEEDS_RESEARCHER_CONFIRMATION`; RP01 `NEEDS_USER_DECISION`.
- Binary/workload SHA and git provenance: `GIT_COMMIT_v3211.txt`, `GIT_STATUS_v3211.txt`, `GIT_DIFF_v3211.txt`, `DELIVERABLES_SHA256_v3211.txt`.

## 6. Open issues

1. RP01 definition approval and the count-only preflight.
2. Five dynamic RP01 contexts not yet proven under the frozen seeds.
3. DA04 R04/R05 raw oracle files missing (meta/E2E only).
4. A01/A03 reference-value/crash-attribution evidence missing.
5. SQ01/SQ03/SP05 have no consumer workload.
6. FW02/MD04 squash causality unproven in the partial pilots.
7. Warm-up/ROI not frozen; formal campaign NOT_STARTED.
