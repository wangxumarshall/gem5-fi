# PACKAGE MANIFEST — LSU v3.2.12 12-Model Propagation Closure Package

Target artifact: `LSU_v3.2.12_12Model_Propagation_Closure_Package.zip`
(+ `LSU_v3.2.12_12Model_Propagation_Closure_Package.zip.sha256` and
`DELIVERABLES_SHA256_v3212.txt`), per plan Task 20.

**Status: ASSEMBLED (final rebuild, 2026-11-11).** The ZIP
`LSU_v3.2.12_12Model_Propagation_Closure_Package.zip` is built with the FINAL
committed files. The final closure matrix landed (32 rows / 173 records,
sha256 `064e28b4…`, E5/E6/E7 + §12.5 frozen-four import + the RP01 / A01 / A03
`68c6ce73` record groups, commit `36614647`), the Excel v3.2.7 workbook and the
derived `MODEL_STATUS_MATRIX.csv` were published (commit `b5e87eba`), the final
acceptance report + blockers were published (commit `278913ba`), and the
closure status MD was regenerated from the FINAL matrix. The first assembly
(2026-11-11 ~01:30, HEAD `87287cbd`) shipped the intermediate 149-record status
MD; this rebuild replaces it with the FINAL 32-row/173-record version. All 20
items below are READY.

## Provenance of this 20-item list (state explicitly, do not delete)

- The researcher brief's **§15 defines the verbatim 20-item package contents
  and §15 is not in the repository.** `audit_v3_2_12/CLOSURE_INPUTS_v3.2.12.md`
  §5 records: "the exact 20-item list is defined by the researcher brief,
  which is NOT checked into the repo … the main agent holding the researcher's
  frozen v3.2.12 brief must supply the verbatim §15 item list."
- The list below is therefore **reconstructed** from (a) plan Task 20
  ("Build the ZIP with the 20 items; do not include `build/`, `.git/`, or
  superseded packages"), (b) the CLOSURE_INPUTS §5 candidate-item inventory
  ("acceptance standard; pilot-record schema; closure matrix CSV; closure
  summary MD; feature dataset CSV; MissingEvidenceMatrix CSV+MD; 12
  per-model audit reports; LQ04 verdict JSON; SUPPLEMENTARY_ORACLE_MANIFEST;
  W1_W8_Baseline_Map CSV; baselines BASELINE_SUMMARY; RP01 preflight CSV;
  workbook v3.2.7; MODEL_STATUS_MATRIX.csv; final report;
  DELIVERABLES_SHA256"), and (c) the v3.2.11 package layout
  (`LSU_v3.2.11_…Package.zip`, folders A–E) as the structural precedent.
- **The main agent must reconcile this list against the verbatim brief §15
  before ZIP assembly.** Items the brief names that this reconstruction
  groups differently must be re-split/merged accordingly; anything here the
  brief does not name stays out of the ZIP and is recorded as an extra, not
  silently included.

## The 20 required items

Paths are relative to the repo root unless absolute. READY = file exists at the
stated path with final-round content; PENDING = must be (re)generated after
the final closure matrix / workbook finalization.

| # | Item | Source path(s) | Status |
|---|------|----------------|--------|
| 1 | Acceptance standard (frozen, amended E1–E4) | `docs/gem5-fi/lsu/implementation_v3_2/LSU_Propagation_Acceptance_Standard_v3.2.12.md` | READY |
| 2 | Pilot-record schema (normative with the standard) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/pilot_record.schema.md` | READY |
| 3 | 12-model propagation closure matrix (FINAL regeneration) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv` | READY — FINAL, sha256 `064e28b456b9498e1c26d9ded203d8dd0127f09027113104c3879ac43d88474d`, **32 rows / 173 records** (E5/E6/E7 + §12.5 frozen-four import + RP01 / A01 / A03 `68c6ce73` groups; commit `36614647`); runbook §5 checks re-verified |
| 4 | Closure summary / matrix-status report (FINAL) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/Closure_Matrix_Status_v3.2.12.md` (plan also names `LSU_12Model_Propagation_Closure_Summary_v3.2.12.md` — naming decision for the main agent) | READY — regenerated 2026-11-11 from the FINAL matrix (32 rows / 173 records, 12/12 COMPLETE_CAUSAL_CHAIN, E1–E7 + frozen-import caveats); supersedes the intermediate 149-record version |
| 5 | Diagnostic feature dataset (FINAL regeneration) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LSU_12Model_Diagnostic_Feature_Dataset_v3.2.12.csv` | READY — FINAL, sha256 `0bcda53aef4bc5358a1c4580f1fdb98c7431a7b9dfabba735acbdd539eed1786`, **607 rows = 173 PILOT + 434 PATH_FRAGMENT**, 0 blank cells |
| 6 | Missing-evidence matrix CSV | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/MissingEvidenceMatrix.csv` | READY |
| 7 | Missing-evidence narrative report | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/MissingEvidenceMatrix_v3.2.12.md` | READY |
| 8 | Per-model audit report: LQ04 (senderState masking chain, E1) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LQ04_Propagation_Audit_v3.2.12.md` + `LQ04_verdict_v3.2.12.json` | READY |
| 9 | Per-model audit report: A01 (incl. `68c6ce73` rerun evidence) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/A01_Propagation_Audit_v3.2.12.md` + `A01_verdict_v3.2.12.json` + `A01_verdict_v3.2.12_v3.json` + `A01_A03_Rerun_Records_v3.2.12.csv` + `A01_A03_Rerun_NodePresence_DataDelta_v3.2.12.md` | READY (evidence layer final; the A01 rows in items 3/5 must be regenerated) |
| 10 | Per-model audit report: A03 (incl. `68c6ce73` rerun evidence) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/A03_Propagation_Audit_v3.2.12.md` + `A03_verdict_v3.2.12.json` + `A03_verdict_v3.2.12_v3.json` + rerun CSV/MD shared with item 9 | READY (same regeneration caveat) |
| 11 | Per-model audit report: FW02 (+ control-fix pair) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/FW02_SQ01_SQ03_SP05_Evidence_Audit_v3.2.12.md` (§1 FW02) + `FW02_CONTROL_FIX_v3.2.12.md` + `FW02_CONTROL_FIX_VERIFIED_v3.2.12.md` + `FW02_verdict_v3.2.12.json` | READY |
| 12 | Per-model audit report: SQ01 (eligible-ordinal closure, E2) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/SQ_Ordinal_Eligibility_Preflight_v3.2.12.md` + `SQ01_SQ03_SP05_Eligible_Run_Records_v3.2.12.csv` + `SQ01_verdict_elig_v3.2.12.json` + `SQ01_verdict_v3.2.12.json` | READY |
| 13 | Per-model audit report: SQ03 (E3) | same preflight/records set + `SQ03_verdict_elig_v3.2.12.json` + `SQ03_verdict_v3.2.12.json` | READY |
| 14 | Per-model audit report: SP05 (E4) | same preflight/records set + `SP05_verdict_elig_v3.2.12.json` + `SP05_verdict_v3.2.12.json` | READY |
| 15 | Per-model re-adjudication evidence: DA04 / LP01 / MD04 / FW05 (the frozen four) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/SUPPLEMENTARY_ORACLE_MANIFEST_v3.2.12.csv` + `pilots_v3_2_12/SUPP-DA04-R04,R05`, `SUPP-LP01-R01..R05`, `SUPP-MD04-R02,R03,R05`, `SUPP-FW05-R02..R05` + `FROZEN_PRIOR_PROPAGATION_VERDICTS_v3.2.12.json` + `MODEL_STATUS_MATRIX_v3.2.11_frozen.csv` | READY (evidence); the four models' standalone v3.2.12 re-adjudication narrative lives in items 3/4 rows + Q8 of the final report — write standalone MDs only if the verbatim §15 requires one file per model |
| 16 | RP01 package (preflight + implementation evidence + verdict) | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/RP01_CountOnly_Preflight_v3.2.12.csv` + `.md` + `rp01_preflight_raw/` + `RP01_Task15_Runbook_v3.2.12.md` + `RP01_Task15_Evidence_v3.2.12.md` + `RP01_verdict_v3.2.12.json` + `RP01_records_v3.2.12.binary-68c6ce73.json` + `pilots_v3_2_12/RP01-R01..R05` + `RP01-CONTROL-R01..R05` | READY (records archived at `86813b91`; the RP01 rows in items 3/5 must be regenerated) |
| 17 | W1–W8 baseline map + FINAL baselines on the final binary | `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/W1_W8_Baseline_Map_v3.2.12.csv` + `logs_v3_2_12/baselines_w1_w8/FINAL_BASELINE_SUMMARY.csv` + `FINAL_BASELINE_REPORT.md` (9/9 PASS on `68c6ce73…`) | READY (the superseded `BASELINE_SUMMARY.csv`/`BASELINE_REPORT.md` on `720eb780…` stay on disk but out of the ZIP) |
| 18 | Excel workbook v3.2.7 (published) | `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx` | READY — published (commit `b5e87eba`), sha256 `3b219ee060b51cb9f07567e7c60e57b431b366cd432aaf4c1e0ec8f35d03db1c`, 21 sheets; builder + 10 tests green; carries the final matrix sha `064e28b4…` in its change record |
| 19 | MODEL_STATUS_MATRIX.csv (derived rewrite) + derivation tooling | `docs/gem5-fi/lsu/implementation_v3_2/MODEL_STATUS_MATRIX.csv` ← derived by `tools/update_lsu_v327_audit.py` (test: `tests/test_lsu_v327_audit.py`) | READY — committed rewrite (commit `b5e87eba`), derived only from the FINAL matrix: 12 rows, `PROPAGATION_VERIFIED=1` for 12 model(s), no cell hand-set; frozen v3.2.11 copy archived as item 15 |
| 20 | Final acceptance report (published) + ZIP + SHA records | `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.12_Final_Acceptance_Report.md` + `LSU_v3.2.12_12Model_Propagation_Closure_Package.zip` + `.zip.sha256` + `docs/gem5-fi/lsu/implementation_v3_2/DELIVERABLES_SHA256_v3212.txt` | READY — report + blockers published (commit `278913ba`), 13 questions answered from the final matrix; ZIP rebuilt 2026-11-11 with the FINAL status MD/manifest/git-state/validation captures (`unzip -t` clean, file count and SHA recorded in `.zip.sha256` + `DELIVERABLES_SHA256_v3212.txt`; no historical file overwritten, no `build/`, no `.git/`, no superseded packages) |

## Ready vs pending summary

- **READY: all 20 of 20.** Items 3/4/5 landed with the final closure matrix
  (commit `36614647`); items 18/19 landed with commit `b5e87eba`; item 20's
  report/blockers landed with commit `278913ba`; the ZIP was rebuilt on
  2026-11-11 to carry the FINAL status MD, manifest, git-state and validation
  captures (the first assembly at HEAD `87287cbd` had shipped the intermediate
  149-record status MD).
- **Still pending (outside this manifest's 20 items, recorded so no reader
  mistakes them for package gaps):** (a) the verbatim researcher-brief §15/§16
  reconciliation (see Provenance above); (b) the record-level residuals named in
  `Closure_Matrix_Status_v3.2.12.md` §3 and `LSU_v3.2.12_BLOCKERS.md`
  (FW05 native consumer edge, A01 crash attribution/reference leg, A03
  crash-cut policy, RP01 watchdog contract) — none blocks package completeness;
  (c) the 60-sample formal experiment (ConfigFrozen=NO, NOT_STARTED).

## Assembly rules (carry into the ZIP build)

1. Never include `build/`, `.git/`, `m5out/`, scratch dirs, or superseded
   packages (the v3.2.10/v3.2.11 ZIPs and their contents stay out).
2. Never modify or repackage any historical file; everything lands under new
   `*_v3_2_12` names or in the v3.2.11-precedent folder layout.
3. Verify with `unzip -t`, file count == 20 items (files as listed), record
   `sha256sum` of the ZIP and every item in `DELIVERABLES_SHA256_v3212.txt`.
4. Confirm `git status --porcelain` shows no historical path modified after
   assembly.
