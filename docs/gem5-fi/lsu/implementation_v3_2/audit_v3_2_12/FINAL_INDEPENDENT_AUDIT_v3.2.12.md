# FINAL INDEPENDENT AUDIT — LSU v3.2.12 12-Model Propagation Closure

**Auditor:** independent final auditor (read-only on evidence/source; only this report written).
**Date:** 2026-11-11.
**Worktree audited:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`, HEAD `278913ba`
(`[LSU][MDSPEC][V3.2.12][DOCS] publish the final acceptance report and blockers`), branch
`lsu-platform-v3.2.12`, working tree: 1 modified (`audit_v3_2_12/Closure_Matrix_Status_v3.2.12.md`,
the pending final regeneration) + untracked (closure ZIP + `.sha256`, `DELIVERABLES_SHA256_v3212.txt`, `.tmp_lsu_conc/`).
**Inputs:** the final acceptance report, the final closure matrix (sha256
`064e28b456b9498e1c26d9ded203d8dd0127f09027113104c3879ac43d88474d` — verified byte-identical),
the feature dataset, the frozen v3.2.11 audits, the acceptance standard, the grading rules, all
36 record-JSON groups + 4 frozen-import JSONs, the Excel v3.2.7/v3.2.6 workbooks, and live runs
of the closure/audit/workbook test suites and the derivation tool. No gem5/scons runs; no commits.

## Verdict

**Overall: PASS with findings.** All eight independent checks pass. The headline claim set
(12/12 models closed, 173 records / 32 binary-keyed groups, terminal distribution MASKED 60 /
NO_INJECTION 45 / SDC 26 / CRASH 21 / SQUASHED 16 / HANG 3 / UNRESOLVED 2, frozen-four carried
verbatim from v3.2.11, baselines 9/9 PASS on binary `68c6ce73…`, ConfigFrozen=NO, formal runs
NOT_STARTED, 60 SampleRunIDs/Seeds unchanged) is **accurate and reproducible from the raw
evidence**. I recomputed every distribution from the matrix independently and re-derived the
MODEL_STATUS_MATRIX byte-for-byte as tool output. One Important prose error (A01 Q5 terminal
profile) and several Minor inaccuracies are listed in §8; none changes any count, verdict, or
the closure claim.

---

## Check 1 — 12/12 models present, ≥2 distinct complete contexts per authoritative binary group, evidence paths real: **PASS (one traceability caveat)**

- The matrix carries exactly 12 models: A01, A03, DA04, FW02, FW05, LP01, LQ04, MD04, RP01,
  SP05, SQ01, SQ03 — 32 (model, binary) rows summing to 173 records (recomputed from
  `PilotCount`; also confirmed at per-record level by loading all 36 generic + 4 frozen record
  JSONs, applying the §12.5 same-key supersede).
- Best-group complete-context counts (recomputed from the matrix AND the per-record JSONs; all
  contexts distinct in SampleRunID/EventOrdinal; never merged across binaries — A01 has 3
  complete on `68c6ce73` AND 3 on `720eb780` as two separate rows):

  | Model | Best group | Complete contexts | Source |
  |---|---|---|---|
  | A01 | A01@68c6ce73 | 3 (ordinals 2/4/5) | native E7 rerun |
  | A03 | A03@68c6ce73 | 5 (1–5) | native E6 rerun |
  | DA04 | DA04@0de25644 | 2 (4/5) | frozen v3.2.11 import |
  | FW02 | FW02@720eb780 | 2 (3/4) | generic §4 upgrade |
  | FW05 | FW05@8377c011 | 4 (2–5) | frozen v3.2.11 import |
  | LP01 | LP01@0de25644 | 5 (1–5) | frozen v3.2.11 import |
  | LQ04 | LQ04 (f3c2a442) | 5 (1–5) | E1 |
  | MD04 | MD04@0de25644 | 3 (2/3/5) | frozen v3.2.11 import |
  | RP01 | RP01 (68c6ce73) | 3 (1/4/5) | E5 |
  | SP05 | SP05 (720eb780) | 5 (1–5) | E4 |
  | SQ01 | SQ01@720eb780 | 5 (1–5) | E2 |
  | SQ03 | SQ03@720eb780 | 5 (1–5) | E3 |

  All ≥2. The tool refuses cross-binary summation (pinned by
  `test_never_merges_complete_contexts_across_binaries`); the matrix row keys confirm.
- Evidence paths: 168 of 173 matrix evidence paths exist on disk. The 5 exceptions are the
  **FW05@8377c011 frozen-import rows**, whose `EvidencePath` points to
  `audit_v3_2_11/extracted_evidence/FW05_v3_2_7/FW05-R01…R05` — a **gitignored scratch
  extraction** from the v3.2.11 round that was never committed, so the directory does not exist
  in this worktree. The underlying evidence is nevertheless real and archived in-tree:
  `audit_v3_2_11/EVIDENCE_EXTRACTION.md` records the extraction (zip source, SHA256
  `186e7059a47b404f…`, exact script), the git-tracked
  `LSU_v3.2.7_MD04_Config_Freeze_FW05_Implementation_Package.zip` at the worktree root hashes
  to exactly that value today, the committed v3.2.11 audit/verdict/pilot-index document the
  same five pilots, and `pilots_v3_2_7/FW05-R*` hold the non-trace artifacts (the raw
  `trace_v31.jsonl`/`oracle.log` live only inside the zip). This is a **traceability defect
  (the matrix path is dangling), not a fabrication** — but any future reader must know to
  extract the v3.2.7 zip to reach the raw traces. Suggest a one-line annotation or re-keying
  of those five rows to the zip path.

## Check 2 — COMPLETE_CAUSAL_CHAIN record integrity: **PASS**

All 60 complete-graded records (matrix-level; see §8-M5 for the per-record split) verified
individually from the record JSONs:

- `InjectionVerified=yes` and `ActivationVerified=yes`: 60/60.
- `RecordIntegrity`: 38 VALID; 5 TRUNCATED (A03, the E6-frozen crash-cut relaxation); 3
  TRUNCATED (RP01, the E5-frozen watchdog relaxation); 14 NULL (the frozen imports, §12.5:
  the five §1 fields the v3.2.11 audit did not record per pilot, literally NULL). 0 outside
  the standard's allowed set.
- `TraceCompleteness`: 43 COMPLETE (38 + A03's 5, whose traces are COMPLETE while the records
  are crash-cut); 3 INCOMPLETE (RP01, E5-allowed); 14 NULL (frozen). 0 outside the allowed set.
- Real terminal: all 60 terminals ∈ {SDC, MASKED, SQUASHED, CRASH, HANG} — SDC 18, MASKED 21,
  CRASH 5, HANG 3, SQUASHED 0 at complete-graded level (the terminals were cross-checked
  against `AdjudicatedTerminal`).
- Mechanism spot-verification (all pass, 0 failures): LQ04 E1 5/5 (senderState association on
  both response and writeback, `WritebackValueFnv == ConsumerInputFnv`, MASKED/PASS/PROVEN);
  SQ01 E2 5/5 (`mem_write_hash == reload_data_hash == consumer_hash`, SDC/FAIL); SQ03 E3 5/5
  (`drain_tick < commit_tick`, `visible_before_commit=1`, MASKED/PASS); SP05 E4 5/5
  (`write_skipped=1`, SDC/FAIL); RP01 E5 3/3 (watchdog `CHAOS_RP01_WATCHDOG=EXPIRED` parsed,
  replay identity on chain, HANG, honest TRUNCATED/INCOMPLETE); A03 E6 5/5 (panic VA
  `0xffffffffffb73c50` == on-chain `a03_stream.actual_ea` `ffffffffffb73c50` with
  `last_injection_dyn_seq == dyn_inst_seq` (1014), CRASH); A01 E7 3/3 (`a01_ea`
  golden≠actual affected=1; `a01_consumed.input_hash == WritebackValueFnv == ConsumerInputFnv`,
  MASKED). Honest negatives verified too: A01 R01C stays UNRESOLVED (temporal-only crash, no
  mechanism fired) and R03C is PARTIAL via the on-chain `a01_ea_discarded` /
  `applied_to_request=0` companion.

## Check 3 — no HANG/TIMEOUT graded MASKED/SDC; no zero-injection graded complete: **PASS**

- The only HANG records in the 173 are RP01-R01/R04/R05: terminal HANG, adjudicated HANG,
  causality PROVEN, per-record `VERIFIED_SINGLE_CONTEXT` (model-level COMPLETE under E5).
  Zero MASKED/SDC anywhere on any HANG/TIMEOUT record; the SQ03/MD04/RP01 squashes that are
  unproven stay PARTIAL (RP01-R02/R03 causality PARTIAL, `fault_caused=0`).
- All 45 NO_INJECTION records grade UNRESOLVED (and only UNRESOLVED); no record with
  `InjectionVerified=no`/`InjectionCount=0` is graded complete or verified. The 45 = 25 valid
  controls + 20 never-fired vintage records (SQ01@8eb7ce8d ×5, SQ01@b1f7cf18 ×5,
  SQ03@b988b750 ×5, MD04@8377c011 ×5) — note the FW05 example cited in report Q4 is stale,
  see §8-M1.

## Check 4 — frozen four (DA04/LP01/MD04/FW05) carried from v3.2.11 with real per-pilot evidence; no hand-set override; SUPP-MD04-R05 split retained: **PASS**

- Verbatim carry verified: all 22 frozen records match `audit_v3_2_11/{DA04,LP01,MD04,FW05}_verdict.json`
  pilots exactly, keyed by (pilot_id, binary_sha) — classification, terminal, oracle, evidence
  path identical; `PriorAudit="v3.2.11"` on every record; the five §1 fields literally NULL
  (0 fabrication). The DA04 verdict's 7 pilots span two binaries (2 COMPLETE @0de25644,
  R04/R05; 5 PARTIAL/LIFECYCLE_ONLY @3e9148fc), both carried under their own keys.
- Per-pilot evidence is real: the v3.2.11 per-model audit MDs contain per-pilot evidence
  sections (e.g. DA04-R04 injection seq 13832 @ PC 0x400538, tick 17040870) and the pilots
  directories cited by the frozen records exist (DA04/LP01/MD04 under `pilots_v3_2_6/`;
  FW05's raw traces inside the git-tracked v3.2.7 zip, sha-verified — see Check 1 caveat).
- No hand-set override: I re-derived `MODEL_STATUS_MATRIX.csv` from the final matrix with
  `tools/update_lsu_v327_audit.py` and it reproduces the committed file **byte-for-byte**
  (the only inputs are the frozen v3.2.11 template plus the tool's `--set RP01:{IMPLEMENTED,
  COMPILED,UNIT_TESTED,PILOT_RUN}=1` — the six workflow-flag columns only; `--set` on
  `PROPAGATION_VERIFIED` or evidence is rejected by the tool, which I confirmed by triggering
  the rejection). The derivation banner "12 rows, PROPAGATION_VERIFIED=1 for 12 model(s); no
  cell hand-set" reproduced exactly. The frozen-import mechanism itself is tool-enforced
  (keyed by model + binary SHA + evidence path, refuses foreign keys/malformed keys, pins in
  `test_frozen_import_*`).
- SUPP-MD04-R05 delta: still two rows, never merged — original `MD04-R05@0de25644` MASKED /
  COMPLETE_CAUSAL_CHAIN (in-group frozen) vs `SUPP-MD04-R05@e527f26a` SQUASHED / PARTIAL
  (coverage NONE). Same discipline visible in DA04@3e9148fc (0 complete) vs DA04@e527f26a
  (SDC 2/2, FAIL 2/2). FW05@e527f26a stays LIFECYCLE_ONLY 4/4 (SDC/FAIL) — the native
  consumer-edge gap is honestly not closed.

## Check 5 — terminal counts recomputed: **PASS — the report's numbers are exactly right**

Independently recomputed from the 32 matrix rows (parsing the `mixed(...)` annotations
weighted by `PilotCount`; every distribution sums to 173; cross-checked against the
per-record JSONs after frozen-supersede):

- **ObservedTerminal: MASKED 60, NO_INJECTION 45, SDC 26, CRASH 21, SQUASHED 16, HANG 3,
  UNRESOLVED 2** — identical to the report.
- ApplicationOracle: PASS 103, MISSING 43, FAIL 24, NOT_APPLICABLE 3 — identical.
- FinalClassification: COMPLETE_CAUSAL_CHAIN 60, UNRESOLVED 62, LIFECYCLE_ONLY 32, PARTIAL 19
  — identical.
- FaultCausality: PROVEN 71, UNPROVEN 66, PARTIAL 14, NULL 22 — identical.
- Structural checks: 0 blank cells, 0 bare `PASS` outside `ApplicationOracle`, 0
  malformed/missing record `BinarySHA256` (64-hex everywhere), 0 complete-over-unverified
  defects — matching FINAL_GRADING_RULES §3. Feature dataset: 607 rows = 173 PILOT + 434
  PATH_FRAGMENT, as claimed.
- Baselines verified: `FINAL_BASELINE_SUMMARY.csv` shows 9/9 PASS on `68c6ce73…`
  (W1 `728e604ffcec539d`, W2 `b097eb83f71545cb`, W3 `ba3b3185e541ad03`, W4 `1f4cbf14327717df`,
  W5 `99c106541150be0e`, W6 `2543a2a60de01795`, W7 `59fc61c040618747`, W8a `67afad307642983e`,
  W8b `3f89eab79392ce69`); `build/ARM/gem5.opt` hashes to `68c6ce73…` today;
  `GIT_COMMIT_v3212.txt` FINAL section records both binary copies and the reg_chain golden
  re-run. Test claims verified live: closure suite **36 passed**; v3.2.7 audit+workbook
  suites **24 passed** (14+10, matching the report).
- Numeric spot-claims verified in the raw records: A03 rerun 5/5 CRASH with injection counts
  **141/140/139/138/137**, dyn seq **1014**, tick **1657040**, panic VA
  **0xffffffffffb73c50**; RP01 watchdog HANG pilots with retained partial chains; A01 rerun
  terminals (see Check 2 and §8-I1); FW02 control misfire (C01 fired, SQUASHED/PASS,
  InjectionCount=1; C02 clean NO_INJECTION/PASS).

## Check 6 — ConfigFrozen=NO, formal NOT_STARTED, 60 SampleRunIDs/Seeds unchanged: **PASS (wording caveat §8-M3)**

- `ConfigFrozen=NO` on **all 60 rows** of sheet `5.60个样本执行矩阵` (v3.2.7), identical to
  v3.2.6.
- The 60 (SampleRunID, Seed) pairs are **identical** between the v3.2.6 and v3.2.7 workbooks,
  and **zero non-status cells differ** — "unchanged from v3.2.6" holds at cell level.
- The v3.2.6 workbook is untouched: sha256 `472628244c924859…` matches the report's
  `47262824…`; 20 sheets preserved; the v3.2.7 workbook has 22 sheets (see §8-M2) including
  `21.v3.2.12变更记录` (which cites the final matrix sha `064e28b4…`) and
  `22.v3.2.12传播链闭包矩阵` (32 matrix rows verbatim + a derived per-model mapping block whose
  groups/records/complete totals all match my recomputation).
- Formal status: sheet `9.实验执行计划` Status values are NOT_STARTED for the formal phases
  (including `NOT_STARTED: WarmUp/ROI need researcher confirmation`); sheet-5
  `DecisionStatus` keeps `NEEDS_USER_DECISION`/`FROZEN_FW05_WORKLOAD` etc.; Warm-up/ROI stay
  NEEDS_RESEARCHER_CONFIRMATION. The literal string `NOT_STARTED` is NOT the value of the
  sheet-5 column named `ExecutionStatus` (that column holds NOT_RUN/PILOT_RUN/
  PILOT_RUN_ACCEPTED — the pilot-tracking values, identical to v3.2.6; the builder enforces
  the sheet-9 formal Status starts with `NOT_STARTED`). The substance of the claim (no
  formal run started) is true; the report's column-name phrasing is imprecise (§8-M3).
- `MODEL_STATUS_MATRIX.csv`: committed (b5e87eba) and exactly reproducible as tool output
  (Check 4). The frozen v3.2.11 CSV is retained as
  `audit_v3_2_12/MODEL_STATUS_MATRIX_v3.2.11_frozen.csv`.

## Check 7 — caveats honest and complete: **PASS**

Every caveat the report makes was verified against raw evidence, and nothing material is
hidden:

- **FW05 native edge open** (blocker 1): true — the native rows are LIFECYCLE_ONLY 4/4
  (SDC/FAIL) and closure comes only from the frozen import; `ModelRuleRecord=null` in the
  e527f26a vintage. Wording imprecision §8-M6.
- **A01 temporal crash** (blocker 2): true — R01C panic VA `0`, UNRESOLVED; the
  matched-control reference leg is not produced (structurally inexecutable), honestly stated.
- **A03 crash-cut** (blocker 3): true — TRUNCATED / structural PARTIAL kept on all five
  complete crash contexts; older vintages stay UNRESOLVED (0fa610c2/275111d8/720eb780 carry
  no stream evidence).
- **RP01 partial trace** (blocker 4): true — E5 records keep TRUNCATED/INCOMPLETE; R02/R03
  stay PARTIAL (`triggering_seq=0`, causality PARTIAL); watchdog contract left open.
- **Controls** (Q10): true — 26 controls; the single misfire `SUPP-FW02-C01` is annotated and
  visible (SQUASHED/PASS, fired identically to R01); `SUPP-FW02-C02` is the valid clean
  control; 25 NO_INJECTION+PASS.
- **Disk** (blocker 8): verified live — 67 GB free on `/home` (354 GB total, 81% used), below
  the ~70.6 GiB campaign redline; the 20 GiB pilot gate is satisfied.
- **§15/§16 provenance** (blocker 9): honest — the brief is not in the repo; the report
  flags its thirteen questions as reconstructions to reconcile; `CLOSURE_INPUTS_v3.2.12.md`
  §5 records the same open input.
- **Uncommitted finalization files** (blocker 5): the `Closure_Matrix_Status_v3.2.12.md`
  final regeneration and the closure ZIP are indeed still uncommitted at HEAD (the former as
  a working-tree modification); see §8-M4 for the parts that this stale-at-publication.

## Check 8 — unsupported / overstated claims

### Critical
None. I found no fabricated number, no hand-set verdict, no HANG/zero-injection upgraded, no
cross-binary merge, and no distribution that fails recomputation.

### Important
- **I1 — Report Q5 misstates the A01 rerun terminal profile.** "reproduced the frozen
  terminal profile exactly (CRASH, MASKED, MASKED, MASKED, MASKED across R01C–R05C)" — the
  actual rerun terminals are **CRASH, MASKED, UNRESOLVED, MASKED, MASKED** (R03C is the
  on-chain-discard UNRESOLVED context, graded PARTIAL). The report's own Q1/Q2 and the matrix
  state R03C correctly, and the rerun matched the run plan's prediction ("R01 CRASH,
  R02/R04/R05 MASKED, R03 UNRESOLVED") exactly — but the Q5 parenthetical as written is
  wrong (it also mis-calls it the "frozen" profile; the v3.2.1/2.2-era profile for the same
  seeds was CRASH/MASKED/SQUASHED/MASKED/MASKED). No count or verdict is affected; a reader
  of Q5 alone would be misled about R03C.

### Minor
- **M1 — Stale example in Q4:** the 45 NO_INJECTION records are said to include the
  "`FW05@8377c011` pre-rework R01 set" — those five generic records were superseded by the
  frozen import and are NOT in the final 173. The count 45 is still correct without them
  (25 valid controls + 20 never-fired vintage records).
- **M2 — Sheet count:** Q12 says the v3.2.7 workbook has "21 sheets"; it has **22**.
- **M3 — Column-name conflation:** "formal `ExecutionStatus` = NOT_STARTED" — the column
  literally named `ExecutionStatus` (sheet 5) holds NOT_RUN/PILOT_RUN/PILOT_RUN_ACCEPTED
  (unchanged pilot-tracking values); NOT_STARTED is the sheet-9 formal-plan Status. The
  semantic claim is true.
- **M4 — Git-state snapshot stale at publication:** Q13 records HEAD `87287cbd` and calls
  the Excel/MODEL_STATUS rewrite uncommitted, but b5e87eba committed both (and
  `GIT_COMMIT_v3212.txt`) before the report's own publication commit 278913ba. Honest
  snapshot, imprecise at HEAD. What genuinely remains uncommitted at HEAD: the final
  `Closure_Matrix_Status_v3.2.12.md` regeneration (working-tree modification), the closure
  ZIP, and `DELIVERABLES_SHA256_v3212.txt` — matching blocker 5's warning that the ZIP would
  need rebuilding if the status MD landed after the ZIP was built.
- **M5 — "60 records grade COMPLETE_CAUSAL_CHAIN" (Q0):** accurate at matrix level, but 36
  of the 60 are per-record `VERIFIED_SINGLE_CONTEXT` upgraded to COMPLETE at the group level
  under §4/§11.4/§12.4 (24 per-record COMPLETE + 36 VSC). The report discloses this per
  model (Q1/Q5/Q7) but the Q0 phrasing alone could be read as 60 per-record complete
  verdicts.
- **M6 — FW05 "no consumer edge" wording (Q2/Q8/blocker 1):** the e527f26a records show
  `Stages.consumer_verified=yes` and `consumer_commit` on the chain with hash-equal
  WB/CI; the honest deficiency is that the generic classifier cannot bind the FW05
  model-specific divergence (true-vs-alt source) and `ModelRuleRecord=null` in that vintage,
  so coverage stays LIFECYCLE_ONLY. "No consumer edge" oversimplifies; the substantive claim
  (native chain not closed) is correct.
- **M7 — "rebuilt all 33 groups" (FINAL_GRADING_RULES §4):** the matrix has 32 groups; 33 is
  the generic record-file count including FW05@8377c011's superseded generic file.
- **M8 — Dangling FW05 evidence paths (see Check 1 caveat):** the five FW05@8377c011 matrix
  rows point at a never-committed scratch directory. Recommend annotating/re-keying these
  rows to the git-tracked v3.2.7 zip (sha `186e7059a47b404f…`) or the in-tree
  `pilots_v3_2_7/FW05-R*` directories.

## Concerns (non-blocking)

1. The frozen-import rows inherit v3.2.11 verdicts without the v3.2.12 tightening T1
   (single-context corroboration) — legitimate and disclosed (frozen means verbatim), but a
   future re-run of those four models under a current binary would likely need the §4
   corroboration afresh; DA04@0de25644 in particular closes on exactly 2 frozen contexts.
2. The DA04@0de25644 frozen rows carry `ApplicationOracle=FAIL` from pilot_meta-era records
   while the raw oracle artifacts were absent at v3.2.11 (`ORACLE_FILE_MISSING` in the same
   row, T3). The v3.2.12 SUPP runs (DA04@e527f26a, FAIL 2/2) close the raw-artifact gap on a
   different binary key. Disclosed; noting the subtlety for future readers.
3. At publication HEAD the final status MD and the closure ZIP remain uncommitted — the
   packaged ZIP therefore cannot contain the final status MD it promises (blocker 5
   anticipates this: "the ZIP should be rebuilt"). Recommend landing both, then rebuilding
   the ZIP and re-verifying its sha256.
4. `/home` free (67 GB) is below the ~70.6 GiB campaign redline — formal runs will abort
   until ~4 GiB is reclaimed (the report says this; it is a real operational blocker for the
   60 formal runs).

**Bottom line:** the v3.2.12 closure claim set survives independent recomputation from raw
evidence. Fix I1 (Q5's R03C parenthetical) and the M1/M2 wording nits, land the pending
status MD + ZIP, and re-key or annotate the five FW05 frozen-import evidence paths; with
that, every published number and verdict in the final report stands as written.
