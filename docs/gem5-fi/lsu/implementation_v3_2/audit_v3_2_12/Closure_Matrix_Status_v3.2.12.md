# Closure Matrix Status — LSU v3.2.12 (FINAL regeneration)

Date: 2026-11-11. Worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
(branch `lsu-platform-v3.2.12`, HEAD `278913ba` at regeneration time; final binary
`68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`).

This is the **FINAL** status document for the 12-model propagation closure,
regenerated from the committed FINAL matrix
`audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv`
(sha256 `064e28b456b9498e1c26d9ded203d8dd0127f09027113104c3879ac43d88474d`,
32 rows / 173 records, landed by commit `36614647` and finalized through
`278913ba`). The matrix is `tools/lsu_12model_closure.py` output under the
frozen standard `LSU_Propagation_Acceptance_Standard_v3.2.12.md` (amendments
§10 E1, §11 E2/E3/E4, §12 E5/E6/E7 + §12.5 keyed frozen prior-audit import —
conjunctions recorded in `audit_v3_2_12/FINAL_GRADING_RULES_v3.2.12.md`);
nothing in this document is hand-set. It **supersedes** the intermediate
149-record status MD (which described the pre-E5/E6/E7 matrix regenerated at
`eec513e5`); every number below was recomputed programmatically from the
FINAL matrix CSV and the committed record JSONs on 2026-11-11.

Deliverables (committed, final):

- `LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv` — 24 columns, **32 rows**
  (one row per (model, binary) group), **173 records**.
- `LSU_12Model_Diagnostic_Feature_Dataset_v3.2.12.csv` — 39 columns (five
  feature groups), **607 rows** = 173 `PILOT` + 434 `PATH_FRAGMENT`.

What changed vs the intermediate 29-row/149-record matrix (commit `51907109`
era, documented by the superseded status MD): **+3 rows / +24 records** —
`A01@68c6ce73` (7: `SUPP-A01-R01C..R05C` + `C01C`/`C02C`), `A03@68c6ce73`
(7: `SUPP-A03-R01C..R05C` + `C01C`/`C05C`), and `RP01` (10: `RP01-R01..R05` +
`RP01-CONTROL-R01..R05`, the first RP01 row ever) — plus the §12 terminal
exceptions E5/E6/E7 re-grading the new A01/A03/RP01 records, and the §12.5
keyed frozen prior-audit import replacing the generic records of exactly
five (model, binary) keys (`DA04@0de25644` 2, `DA04@3e9148fc` 5,
`LP01@0de25644` 5, `MD04@0de25644` 5, `FW05@8377c011` 5 = 22 imported
records) with the frozen v3.2.11 per-pilot verdicts, verbatim. No other row
changed.

## 1. Record set (keyed by BinarySHA256 — verdicts are never merged across binaries)

173 records over 32 per-binary groups = 151 effective generic records + 22
frozen-imported records (the generic records of the five frozen keys are
superseded with a loud exclusion note, never double-counted). Group map
(binary sha8 → models): `68c6ce73` A01(7)/A03(7)/RP01(10) — the final binary ·
`720eb780` SUPP A01(7)/A03(7)/FW02(7)/SQ01(12)/SQ03(12)/SP05(12) ·
`0fa610c2` A01(2)/A03(1) · `275111d8` A01(5)/A03(5)/FW02(3) ·
`8eb7ce8d` SQ01(5) · `b1f7cf18` FW02(2)/SQ01(5) · `3e9148fc` DA04(5, frozen) ·
`6808c56e` DA04(2)/LP01(1 SMOKE) · `69a1ca9c` LP01(5) · `0de25644`
DA04(2)/LP01(5)/MD04(5, all frozen) · `8377c011` FW05(5, frozen)/MD04(5) ·
`b988b750` SQ03(5) · `e527f26a` SUPP DA04(2)/LP01(5)/MD04(3)/FW05(4) ·
`f3c2a442` LQ04(10 incl. 5 controls). Single-binary models (`LQ04`, `SP05`,
`RP01`) carry no `@<sha8>` suffix; the suffix appears only on multi-binary
splits.

Binary purity: **0** `BINARY_SHA_MISMATCH` / **0** `BINARY_SHA_UNRECORDED`
across all 151 effective generic records (rescanned 2026-11-11); the frozen
imports are keyed by their recorded 64-hex `binary_sha` by construction.

Controls in the record set: **26** — 16 SUPP controls (A01 C01/C02 +
C01C/C02C; A03 C01/C05 + C01C/C05C; FW02 C01/C02; SQ01/SQ03/SP05 C01 + C01B
each) plus the 5 by-design LQ04 zero-injection determinism controls plus the
5 RP01 controls. **Control-valid tally: 25/26.** The one exception is the
recorded and annotated misfire `SUPP-FW02-C01` (`--probability 0.0` ignored
by the F6 FW02 injector; `control_valid=False`, `control_misfire=True` per
`FW02_CONTROL_FIX_v3.2.12.md`) — it stays visible in the matrix/feature
dataset, graded on its own evidence (`PARTIAL`/`SQUASHED`), and is excluded
from control-valid counts; `SUPP-FW02-C02` (injector omitted entirely) is the
valid probability-zero control.

## 2. Per-model closure status (matrix-level, post-in-group-upgrade)

Every model closes at `COMPLETE_CAUSAL_CHAIN` via ≥2 distinct complete
contexts inside **one** binary group (standard §4; the derived rollup
`tools/update_lsu_v327_audit.py` against this matrix prints
"PROPAGATION_VERIFIED=1 for 12 model(s); no cell hand-set"). The
`FinalClassification` column of the matrix carries the post-upgrade
aggregate; the per-pilot `VERIFIED_SINGLE_CONTEXT` verdicts live in the
record/verdict JSONs.

| Model | n | groups | Authoritative group (binary) | Complete contexts | FinalClassification (173-record model total) | ObservedTerminal (model total) | Mechanism (frozen §10–§12 / prior audit) |
|---|---|---|---|---|---|---|---|
| A01 | 21 | 4 | `A01@68c6ce73` | **3** (R02C/R04C/R05C wrong-EA MASKED; +3 on `@720eb780` keyed separately) | COMPLETE 6, LIFECYCLE_ONLY 3, PARTIAL 3, UNRESOLVED 9 | CRASH 4, MASKED 9, NO_INJECTION 4, SQUASHED 2, UNRESOLVED 2 | E7 `WRONG_EA_LOAD_DELIVERED_AND_CONSUMED` |
| A03 | 20 | 4 | `A03@68c6ce73` | **5** (R01C–R05C crash contexts) | COMPLETE 5, UNRESOLVED 15 | CRASH 16, NO_INJECTION 4 | E6 `STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH` |
| FW02 | 12 | 3 | `FW02@720eb780` | **2** (R03/R04 MASKED) | COMPLETE 2, LIFECYCLE_ONLY 1, PARTIAL 7, UNRESOLVED 2 | CRASH 1, MASKED 3, NO_INJECTION 1, SQUASHED 7 | generic §4 ≥2-context upgrade |
| SQ01 | 22 | 3 | `SQ01@720eb780` | **5** (`R01B..R05B` SDC, oracle FAIL 5/5) | COMPLETE 5, LIFECYCLE_ONLY 5, UNRESOLVED 12 | MASKED 5, NO_INJECTION 12, SDC 5 | E2 `SQ_ENTRY_DATA_CORRUPTION_MEM_RELOAD_CONSUMER` |
| DA04 | 11 | 4 | `DA04@0de25644` (frozen import) | **2** (R04/R05 SDC, oracle FAIL 2/2) | COMPLETE 6, LIFECYCLE_ONLY 2, PARTIAL 3 | MASKED 2, SDC 8, SQUASHED 1 | prior audit `DISABLED_LANE_REACHED_CONSUMER_AND_ORACLE_FAILED` |
| LP01 | 16 | 4 | `LP01@0de25644` (frozen import) | **5** (MASKED×5) | COMPLETE 9, LIFECYCLE_ONLY 7 | MASKED 16 | prior audit `MODEL_SPECIFIC_ORIG_VS_INJ_DIVERGENCE_WITH_CONSUMER` |
| MD04 | 13 | 3 | `MD04@0de25644` (frozen import) | **3** (R02/R03/R05 MASKED) | COMPLETE 5, PARTIAL 3, UNRESOLVED 5 | MASKED 5, NO_INJECTION 5, SQUASHED 3 | prior audit violation-report-suppressed chain |
| FW05 | 9 | 2 | `FW05@8377c011` (frozen import) | **4** (R02–R05 SDC) | COMPLETE 4, LIFECYCLE_ONLY 4, PARTIAL 1 | SDC 8, SQUASHED 1 | prior audit true-vs-alt store source → SDC to consumer |
| SQ03 | 17 | 2 | `SQ03@720eb780` | **5** (`R01B..R05B` MASKED, oracle PASS 5/5) | COMPLETE 5, LIFECYCLE_ONLY 5, UNRESOLVED 7 | MASKED 10, NO_INJECTION 7 | E3 `SQ_CANWB_VISIBILITY_MOVED_DRAIN_BEFORE_COMMIT` |
| SP05 | 12 | 1 | `SP05` (`720eb780`, single-binary) | **5** (`R01B..R05B` SDC, oracle FAIL 5/5) | COMPLETE 5, LIFECYCLE_ONLY 5, UNRESOLVED 2 | MASKED 5, NO_INJECTION 2, SDC 5 | E4 `STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED` |
| LQ04 | 10 | 1 | `LQ04` (`f3c2a442`, single-binary) | **5** (fault pilots MASKED×5; 5 controls UNRESOLVED by design) | COMPLETE 5, UNRESOLVED 5 | MASKED 5, NO_INJECTION 5 | E1 `RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE` |
| RP01 | 10 | 1 | `RP01` (`68c6ce73`, single-binary) | **3** (R01/R04/R05 HANG contexts) | COMPLETE 3, PARTIAL 2, UNRESOLVED 5 | HANG 3, NO_INJECTION 5, SQUASHED 2 | E5 `REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT` |

Record-level aggregates over the 173 records (recomputed programmatically
from the FINAL matrix; every distribution sums to 173):

- FinalClassification — COMPLETE_CAUSAL_CHAIN 60, UNRESOLVED 62,
  LIFECYCLE_ONLY 32, PARTIAL 19.
- ObservedTerminal — MASKED 60, NO_INJECTION 45, SDC 26, CRASH 21,
  SQUASHED 16, HANG 3, UNRESOLVED 2.
- ApplicationOracle — PASS 103, MISSING 43, FAIL 24, NOT_APPLICABLE 3
  (the 3 NOT_APPLICABLE are RP01 HANG records whose oracle cannot run past
  the watchdog).
- FaultCausality — PROVEN 71, UNPROVEN 66, PARTIAL 14, NULL 22 (the NULLs
  are exactly the 22 frozen-imported records whose five §1 fields the
  v3.2.11 prior audit did not record per pilot — §12.5, never fabricated).

Authoritative-group evidence paths (pilot dirs; all under
`docs/gem5-fi/lsu/implementation_v3_2/` unless noted):
`A01@68c6ce73` → `pilots_v3_2_12/SUPP-A01-R01C..R05C`, `SUPP-A01-C01C/C02C`;
`A03@68c6ce73` → `pilots_v3_2_12/SUPP-A03-R01C..R05C`, `SUPP-A03-C01C/C05C`;
`FW02@720eb780` → `pilots_v3_2_12/SUPP-FW02-R01..R05`, `SUPP-FW02-C01/C02`;
`SQ01@720eb780` → `pilots_v3_2_12/SUPP-SQ01-R01..R05`, `R01B..R05B`,
`C01`, `C01B`; `DA04@0de25644` → `pilots_v3_2_6/DA04-R04,R05`;
`LP01@0de25644` → `pilots_v3_2_6/LP01-R01..R05`;
`MD04@0de25644` → `pilots_v3_2_6/MD04-R01..R05`;
`FW05@8377c011` → `audit_v3_2_11/extracted_evidence/FW05_v3_2_7/FW05-R01..R05`;
`SQ03@720eb780` → `pilots_v3_2_12/SUPP-SQ03-R01..R05`, `R01B..R05B`,
`C01`, `C01B`; `SP05` → `pilots_v3_2_12/SUPP-SP05-R01..R05`, `R01B..R05B`,
`C01`, `C01B`; `LQ04` → `pilots_v3_2_10/LQ04-R01..R05`, `LQ04-CONTROL-R01..R05`;
`RP01` → `pilots_v3_2_12/RP01-R01..R05`, `RP01-CONTROL-R01..R05`.
Non-authoritative vintages keep their own rows and evidence paths in the
matrix `EvidencePath` column (`pilots_v3_2_1` A01/A03/FW02, `pilots_v3_2_2`
A01/A03, `pilots_v3_2_3` SQ01, `pilots_v3_2_4` DA04/FW02/SQ01, `pilots_v3_2_5`
DA04/LP01, `pilots_v3_2_7` MD04, `pilots_v3_2_8` SQ03, `pilots_v3_2_12/SUPP-*`
raw-oracle runs).

### 2.1 The seven frozen exceptions and the frozen import (summary)

- **E1 (LQ04)** — 5 fault pilots `COMPLETE_CAUSAL_CHAIN`/MASKED with
  `RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE`; controls `UNRESOLVED`/`NO_INJECTION`
  by design.
- **E2/E3/E4 (SQ01/SQ03/SP05)** — the `R01B..R05B` eligible-ordinal reruns
  close each model with five distinct frozen contexts (terminals SDC/MASKED/SDC;
  SQ01/SP05 oracle FAIL 5/5, SQ03 oracle PASS 5/5); the pre-re-selection
  `R01..R05` vintages stay visible as `LIFECYCLE_ONLY` in the same rows;
  each `C01B` control is a valid zero-injection replication.
- **E5 (RP01 HANG/TIMEOUT)** — R01/R04/R05 grade complete through the
  identity-linked replay/skip record, the verbatim `CHAOS_RP01_WATCHDOG=EXPIRED`
  sidecar line, and the retained watchdog partial trace (≥1 chain event
  survived the fatal cut) — `RecordIntegrity=TRUNCATED` /
  `TraceCompleteness=INCOMPLETE` keep their honest values. R02/R03 stay
  PARTIAL (P5 squash discards proven, `triggering_seq=0` — squash causation
  unproven); the 5 controls are UNRESOLVED by design.
- **E6 (A03 CRASH)** — the five `68c6ce73` crash contexts grade complete on
  the identity-linked DIRECT_ADDRESS_MATCH (panic VA == on-chain
  `a03_stream.actual_ea` of an affected load, 5/5; abort
  `last_injection_dyn_seq` == that record's `dyn_inst_seq`); the crash-cut
  records keep `RecordIntegrity=TRUNCATED` and structural PARTIAL (the panic
  is the terminal).
- **E7 (A01 wrong-EA)** — R02C/R04C/R05C grade complete on the on-chain
  wrong-EA proof (`golden_ea != actual_ea`, hash-equal writeback → consumer →
  `a01_consumed.input_hash`); the discard companion grades R03C PARTIAL
  (`a01_ea_discarded`, `applied_to_request=0`); R01C's temporal-only crash
  (panic VA `0`) stays UNRESOLVED. E7 also fires on the old-binary
  `A01@720eb780` reruns (3 complete, keyed to their own row).
- **§12.5 frozen import (DA04/LP01/MD04/FW05)** — the frozen v3.2.11
  per-pilot verdicts are imported verbatim, keyed by (model + binary SHA +
  evidence path), superseding only the same-key generic records; the five §1
  fields the prior audit did not record per pilot are the literal `NULL`.

## 3. Record-level residuals and caveats (all visible in the final matrix)

All twelve models close; the residuals below are record-level, none hidden:

- **FW05 — frozen prior + open native consumer edge.** `FW05@8377c011` closes
  via the §12.5 frozen import (COMPLETE 4 + PARTIAL 1; R01 squash-causality
  unproven per the prior audit, carried verbatim). The v3.2.12-native rows
  prove the effect (`FW05@e527f26a`: SDC 4/4, oracle FAIL 4/4) but stay
  LIFECYCLE_ONLY — the store-committed lane is never read (no consumer edge
  under the generic classifier). Minimal fix: FW05 ordinal/workload
  re-selection binding a reload consumer to the FW05 store lane (the same
  §2.2 preflight method that closed SQ01/SQ03/SP05).
- **A01 — temporal crash + reference leg.** `SUPP-A01-R01C` stays UNRESOLVED /
  TEMPORAL_ASSOCIATION_ONLY (panic VA `0` matches nothing on-chain; E7's
  CRASH branch requires the panic VA to equal the on-chain `a01_ea.actual_ea`).
  `SUPP-A01-R03C` is PARTIAL via the E7 discard companion (the corrupted EA
  provably never reached a Request). The matched-control golden-EA DataDelta
  reference leg remains structurally inexecutable (control runs record zero
  memory nodes; prerequisite is the control-mode registration change —
  `A01_A03_Rerun_NodePresence_DataDelta_v3.2.12.md` §2–§4). Older vintages
  (`0fa610c2`, `275111d8`) stay UNRESOLVED/PARTIAL (no `a01_ea`-era trace
  evidence).
- **A03 — crash-cut traces.** The five complete contexts keep
  `RecordIntegrity=TRUNCATED` (the `fatal` cut) and structural PARTIAL —
  E6 grades complete on the identity-linked address match while both
  platform fields keep their honest values. Older vintages (`0fa610c2`,
  `275111d8`, `720eb780`) stay UNRESOLVED — no `a03_stream`/abort identity
  evidence exists in their traces. A future standard revision may formalize
  the crash-terminal truncation policy beyond the frozen §12/E6 conjunction.
- **RP01 — HANG partial trace + squash identity.** The three complete HANG
  contexts run on the retained watchdog partial trace; the FAIL-event
  watchdog contract / converter truncation policy and the on-chain squash
  `triggering_seq` (R02/R03 stay PARTIAL) are open design decisions
  (`rp01-task15-report.md` concerns 1/3).
- **SUPP-MD04-R05 adjudication delta — two rows, never merged.** Original
  `MD04-R05@0de25644` (MASKED, complete in-group) vs `SUPP-MD04-R05@e527f26a`
  (SQUASHED, PARTIAL) stay as two per-binary facts (`MD04@0de25644` vs
  `MD04@e527f26a`); the SUPP run corroborates the raw oracle and never
  replaces the original verdict. The same discipline keeps the DA04
  `@3e9148fc` vs `@e527f26a` split.
- **FW02 — squash causality.** First complete verdicts (R03/R04, MASKED) but
  the squashed runs stay PARTIAL (squash causation unproven per the frozen
  §6 line), R02's crash aborted the checksum (UNRESOLVED), and the C01
  misfire is annotated (§1).
- **Never-fired historical vintages.** `SQ01@8eb7ce8d`, `SQ01@b1f7cf18`,
  `SQ03@b988b750`, `MD04@8377c011` are UNRESOLVED/NO_INJECTION
  (TRACE_FILE_MISSING / trigger never fired) — kept visible, graded on their
  own evidence, closed as decision-moot in `MissingEvidenceMatrix_v3.2.12.md`.
- **Frozen-four squash residuals** (carried verbatim from the prior audit,
  never re-graded): MD04 R01/R04 and FW05 R01 stay PARTIAL
  (squash-causality unproven).

## 4. Validation (all run for real, 2026-11-11, against the committed FINAL artifacts)

| Check | Expected | Observed |
|---|---|---|
| 1. base model IDs (strip `@sha8`) | 12 | 12 present: A01 A03 DA04 FW02 FW05 LQ04 LP01 MD04 RP01 SP05 SQ01 SQ03 (RP01 now has its own row) |
| 2. blank cells | 0 | matrix 32 rows × 24 cols, 0 blanks; dataset 607 rows × 39 cols, 0 blanks |
| 3. complete verdict over InjectionVerified≠yes | none | `complete-over-unverified defects: []` (173 effective records: 151 generic + 22 frozen) |
| 4. LQ04 complete/masked (E1) | 5 fault pilots MASKED+complete | `LQ04`: COMPLETE 5 / UNRESOLVED 5; MASKED 5 / NO_INJECTION 5; controls by design |
| 5. SUPP-MD04-R05 per-binary split | 3 `MD04@` rows, split retained | 3 rows: `@0de25644` MASKED 3+SQUASHED 2 (COMPLETE 3/PARTIAL 2) vs `@e527f26a` MASKED 2+SQUASHED 1 (COMPLETE 2/PARTIAL 1) vs `@8377c011` UNRESOLVED/NO_INJECTION — never merged |
| 6. RP01 row | present post-Task-15 | 1 row, 10 records: COMPLETE 3 / PARTIAL 2 / UNRESOLVED 5; HANG 3 / SQUASHED 2 / NO_INJECTION 5 |
| 7. SQ01/SQ03/SP05 complete (≥2 contexts) with terminals SDC/MASKED/SDC | all three | SQ01 5 complete / SDC×5; SQ03 5 / MASKED×5; SP05 5 / SDC×5; mechanisms on every complete record |
| 8. feature dataset | all green | 39 cols; RowKind {PILOT 173, PATH_FRAGMENT 434}; 0 blank cells |
| 9. binary purity | 0 defects | 0 `BINARY_SHA_MISMATCH` / 0 `BINARY_SHA_UNRECORDED` across the 151 effective generic records |
| 10. frozen import keying | same-key supersession only | 22 imported records over 5 keys (DA04@0de25644 2, DA04@3e9148fc 5, LP01@0de25644 5, MD04@0de25644 5, FW05@8377c011 5); 151 + 22 = 173, no double count |
| 11. tool test suites | green | closure suite `36 passed in 0.26s`; v3.2.7 audit+workbook suites `24 passed in 3.62s` |
| 12. artifact hashes | match committed | matrix sha256 `064e28b4…74d`; dataset sha256 `0bcda53a…786` |

## 5. Notes and concerns

1. **Matrix classes are post-upgrade.** The matrix `FinalClassification`
   column carries the in-group ≥2-distinct-context upgrade
   (`VERIFIED_SINGLE_CONTEXT` → `COMPLETE_CAUSAL_CHAIN`); no matrix cell
   contains `VERIFIED_SINGLE_CONTEXT`. Upgrades apply inside one binary
   group only — no cross-binary merge ever happens (the derived rollup
   refuses to sum complete contexts across groups).
2. **The frozen imports carry `NULL`, not re-derived values**, in the five
   §1 fields the v3.2.11 prior audit did not record per pilot
   (RecordIntegrity, TraceCompleteness, StructuralChainCompleteness,
   FaultEffectPropagationCoverage, FaultCausality), plus
   `PriorAudit="v3.2.11"`; the prior terminal/oracle/classification ride
   verbatim (`FINAL_GRADING_RULES_v3.2.12.md` §2).
3. **FW05@8377c011 evidence paths point at the v3.2.11 package's
   extracted-evidence extraction** (`audit_v3_2_11/extracted_evidence/FW05_v3_2_7/`)
   — the import is keyed by that recorded path and is not restaged under
   `pilots_v3_2_12/`.
4. **`GIT_COMMIT_v3212.txt` now records the FINAL binary `68c6ce73…` in its
   FINAL section** (historical `e527f26a` baseline entries retained), so
   the mis-keying concern of the superseded status MD is resolved; the W1–W8
   9/9 PASS baselines live in
   `logs_v3_2_12/baselines_w1_w8/FINAL_BASELINE_SUMMARY.csv`.
5. **Hard-terminal precedence held everywhere**: HANG/TIMEOUT/SQUASHED/CRASH
   terminals beat a passing oracle, and a missing injection never grades an
   outcome (check 3). The 45 NO_INJECTION records are the 26 controls minus
   the misfire plus never-fired vintages — all graded on their own evidence.
6. **What would change this document**: any new pilot dir or binary would
   add a (model, binary) group and require matrix regeneration via
   `tools/lsu_12model_closure.py` (runbook
   `audit_v3_2_12/CLOSURE_RUNBOOK_v3.2.12.md` §2/§3); the 60-sample formal
   experiment (ConfigFrozen=NO, ExecutionStatus NOT_STARTED) is the next
   consumer of this closure and is not part of it.
