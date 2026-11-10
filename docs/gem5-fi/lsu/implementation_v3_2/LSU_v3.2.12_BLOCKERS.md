# LSU v3.2.12 — Open Blockers (final acceptance, 2026-11-11)

Companion to `LSU_v3.2.12_Final_Acceptance_Report.md` (plan Task 20). Every
item below is an honest open limit of the round, none silently folded into a
verdict. The evidence layer of the 12-model propagation closure is complete
(12/12 `COMPLETE_CAUSAL_CHAIN`, W1–W8 9/9 PASS on the final binary
`68c6ce73…`); these are the items that remain before the 60-sample formal
experiment can run and before every record-level residual is closed.

## 1. FW05 — v3.2.12-native consumer edge still open

`FW05@8377c011` closes via the §12.5 keyed frozen prior-audit import (4/5
complete, prior-audit verdicts verbatim). The v3.2.12-native rows prove the
effect (`FW05@e527f26a`: SDC 4/4, oracle FAIL 4/4) but the store-committed
lane is never read — no consumer edge → LIFECYCLE_ONLY under the generic
classifier. **Fix:** FW05 ordinal/workload re-selection that binds a reload
consumer to the FW05 store lane (the §2.2 preflight method that closed
SQ01/SQ03/SP05). Owner: next round.

## 2. A01 — crash attribution + matched-control reference leg

- `SUPP-A01-R01C` crash stays `UNRESOLVED` / `TEMPORAL_ASSOCIATION_ONLY`
  (panic VA `0` matches nothing on-chain; E7's CRASH branch requires a panic
  VA equal to the on-chain `a01_ea.actual_ea`). A01 closes via the three
  wrong-EA MASKED contexts, so this is a record-level residual, not a model
  gap.
- The matched-control reference leg (golden-EA DataDelta comparison) is
  structurally inexecutable: control runs record zero memory nodes.
  **Fix:** control-mode registration change (register the control run's
  loads with the chain-scoped tracer), then re-run 5 fault + 2 control
  contexts and compute the reference value per context
  (`A01_A03_Rerun_NodePresence_DataDelta_v3.2.12.md` §2–§4).

## 3. A03 — crash-cut trace grading policy

E6 (`STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH`) grades the five crash contexts
complete on the identity-linked panic-VA == on-chain `a03_stream.actual_ea`
match, but the records keep `RecordIntegrity=TRUNCATED` (fatal cut) and
structural PARTIAL (the panic is the terminal). Older vintages
(`0fa610c2`/`275111d8`/`720eb780`) stay UNRESOLVED — no stream/abort identity
evidence in their traces. **Open:** a future standard revision may formalize
the crash-terminal truncation policy beyond the frozen §12/E6 conjunction.

## 4. RP01 — watchdog trace finalization + squash identity

- E5 grades the three HANG contexts complete with the **watchdog partial
  trace** retained (≥1 chain event survived the fatal cut); the
  `RecordIntegrity=TRUNCATED` / `TraceCompleteness=INCOMPLETE` platform
  values stay honest. **Open design decisions:** the FAIL-event watchdog
  contract or a converter truncation policy for HANG records
  (`rp01-task15-report.md` concerns 1/3).
- R02/R03 stay PARTIAL: proven P5 squash discards, but the `lsq_squash` site
  records `triggering_seq=0`. **Fix:** on-chain `triggering_seq` at the
  squash site.

## 5. Finalization files uncommitted (concurrent agent's Task 19/49 sequence)

- `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx` — published in
  the working tree (uncommitted); carried in the package in that state.
- `MODEL_STATUS_MATRIX.csv` — derived rewrite (12/12 verified), uncommitted.
- `GIT_COMMIT_v3212.txt` — amended with the FINAL binary section,
  uncommitted.
- `Closure_Matrix_Status_v3.2.12.md` — still documents the **intermediate**
  149-record matrix (pre-E5/E6/E7); the final 32-row/173-record regeneration
  is pending. Until it lands, `FINAL_GRADING_RULES_v3.2.12.md` §3 is the
  authoritative final-matrix status record.
- The main agent commits these (and this package/report) in its commit
  sequence; if the status MD lands after this ZIP was built, the ZIP should
  be rebuilt to carry the final version.

## 6. 60 formal runs — NOT_STARTED

- `ConfigFrozen = NO` on all 60 workbook rows; formal `ExecutionStatus` =
  NOT_STARTED; Warm-up/ROI = NEEDS_RESEARCHER_CONFIRMATION.
- The evidence layer is ready (12/12 chains, 9/9 baselines, 60 frozen
  SampleRunIDs/Seeds unchanged from v3.2.6, oracle/golden map verified);
  the configuration decision is the researcher's.

## 7. SUPP-MD04-R05 adjudication delta — retained, by design

Original `MD04-R05@0de25644` (MASKED, complete in-group) vs
`SUPP-MD04-R05@e527f26a` (SQUASHED, PARTIAL) remain two visible per-binary
rows, never merged (the by-design per-binary discipline). Not a blocker —
recorded here so no later reader "resolves" the two-row split by merging.

## 8. Disk headroom below campaign redline

`/home` free 67 GB < the ~70.6 GiB campaign redline — campaign-based formal
runs abort until ~4 GiB is reclaimed (the 20 GiB pilot gate remains
satisfied). `logs_v3_2_12/disk_reclaim_v3212.txt` records the reclaim state.

## 9. Verbatim brief §15/§16 reconciliation

The 20-item package list and the thirteen report questions are reconstructions
(see the report's Provenance section); reconcile against the researcher's
frozen v3.2.12 brief before final submission.
