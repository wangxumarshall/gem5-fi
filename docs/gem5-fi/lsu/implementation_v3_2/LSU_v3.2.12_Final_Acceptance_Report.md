# LSU v3.2.12 — 12-Model Propagation Closure: Final Acceptance Report

**Status: DRAFT (structured pre-final template).** This report is the Task 20
deliverable skeleton: every heading below is one of the thirteen questions the
final report must answer, and every number that depends on the final closure
matrix, the final baselines, or the final git state is a literal
`[FROM FINAL MATRIX]` placeholder. The draft quotes the *current intermediate*
closure-matrix values (sha256 `27f48841…`, regenerated 2026-11-11 at HEAD
`28c566d5`) only as working values; the final grading round (terminal-grading
rules E5/E6/E7 + frozen-four import + the `RP01@68c6ce73` and
`A01/A03@68c6ce73` record groups, SDD tasks #50/#49) will regenerate the matrix
and every `[FROM FINAL MATRIX]` cell must be re-derived from it before this
report is published.

## Provenance of this structure (state explicitly, do not delete)

- The researcher brief's **§15 (20-item package contents) and §16 (the thirteen
  questions) are not in the repository.** `audit_v3_2_12/CLOSURE_INPUTS_v3.2.12.md`
  §5 records this as an open input: "the main agent holding the researcher's
  frozen v3.2.12 brief must supply the verbatim §15 item list and §16 question
  list — they are not in the repository (only the plan references them)."
- The thirteen question headings below are therefore **reconstructed** from:
  (a) plan Task 20 Step 1 — "Write the report answering the 13 questions
  directly, each number derived from the closure matrix. State honestly any
  model that remains below `COMPLETE_CAUSAL_CHAIN`, with the minimal fix";
  (b) plan Task 20 Step 4 — "Record the final git state — branch, HEAD,
  status, binary SHA, disk free; append to the report"; (c) the round's frozen
  audit documents (`LSU_Propagation_Acceptance_Standard_v3.2.12.md`,
  `audit_v3_2_12/Closure_Matrix_Status_v3.2.12.md`,
  `audit_v3_2_12/EXCEL_V327_BUILDER_PREP.md`, the W1–W8 baseline reports, and
  the A01/A03/RP01 verdict files).
- **The main agent must reconcile these thirteen headings against the verbatim
  brief §16 before publication.** If the verbatim questions differ, the
  headings are edited (the answers below are organized to map onto any
  numbering); no answer here is invented — every claim cites its artifact.

Scope: the twelve LSU fault models A01, A03, FW02, SQ01, DA04, LP01, MD04,
FW05, SQ03, SP05, LQ04, RP01 under the frozen v3.2.12 acceptance standard.
Worktree `lsu-platform-v3.2.12`; final binary
`build/ARM/gem5.opt` SHA256
`68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`
(`logs_v3_2_12/binary_v3212_final_candidate.sha256`; confirmed by the final
W1–W8 baselines). **ConfigFrozen = NO. The 60-sample formal experiment runs
are NOT_STARTED.** No verdict in this report is hand-set: every classification
is `tools/lsu_12model_closure.py` output over committed artifacts, and the
`PROPAGATION_VERIFIED` rollup is derived by `tools/update_lsu_v327_audit.py`.

---

## Q1. How many of the twelve models close at COMPLETE_CAUSAL_CHAIN, and which?

[FROM FINAL MATRIX]

Working value (intermediate matrix, sha256 `27f48841…`, 29 rows / 149 records):
**9 of 12 models have at least one binary group with ≥2 distinct complete
contexts** — SQ01, SQ03, SP05, LQ04, FW02, DA04, LP01, MD04 (verified inside a
single binary group each; `FW02@720eb780` carries 2 complete records), plus the
frozen-four carry for FW05 (see Q8). Three models do not close on the current
matrix: **A01, A03 (no complete verdict on any binary) and RP01 (no matrix row
yet — its Task 15 pilot directories were archived after the current matrix was
regenerated)**. The final matrix (with the E5/E6/E7 terminal-grading rules,
the frozen-four import, and the RP01 / A01 / A03 `68c6ce73` record groups) is
authoritative: recount from it.

Per-model complete-context detail (current matrix): SQ01 5 (SDC×5, oracle
FAIL 5/5, E2 `SQ_ENTRY_DATA_CORRUPTION_MEM_RELOAD_CONSUMER`); SQ03 5 (MASKED×5,
oracle PASS 5/5, E3 `SQ_CANWB_VISIBILITY_MOVED_DRAIN_BEFORE_COMMIT`); SP05 5
(SDC×5, oracle FAIL 5/5, E4 `STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED`);
LQ04 5 (MASKED×5, E1 `RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE`); DA04
complete on 3 of 4 binary rows (`@0de25644`/`@6808c56e` 2 each, `@e527f26a`
2, all SDC); LP01 `@69a1ca9c` 3 + `@6808c56e` SMOKE 1 (MASKED); MD04
`@0de25644` 3 + `@e527f26a` 2 (MASKED); FW02 `@720eb780` 2 (MASKED). Each
complete verdict carries the standard's §6 invariant set (RecordIntegrity
VALID, TraceCompleteness COMPLETE, StructuralChainCompleteness COMPLETE,
FaultCausality PROVEN) — enforced by the closure tool, never hand-checked.

## Q2. Which models remain below COMPLETE_CAUSAL_CHAIN, and what is each one's minimal fix?

[FROM FINAL MATRIX — the final list may change under E5/E6/E7 and the frozen-four import]

Current honest state (intermediate matrix + the archived rerun evidence):

- **A01** — no complete verdict on any of 3 binary groups (14 records:
  LIFECYCLE_ONLY 6, PARTIAL 2, UNRESOLVED 6). Minimal fix: the matched-control
  reference leg is structurally inexecutable (controls record zero memory
  nodes); the prerequisite is the control-mode registration change (register
  the control run's loads with the chain-scoped tracer), then re-run the
  5 fault + 2 control contexts and compute the golden-EA reference value per
  context. (`A01_A03_Rerun_NodePresence_DataDelta_v3.2.12.md` §2–§4.)
- **A03** — all 13 records UNRESOLVED; the crash chains now carry on-chain
  `DIRECT_ADDRESS_MATCH` evidence (`a03_stream.actual_ea` == panic VA, 5/5)
  but stay capped by two frozen rules: the abort node is an off-chain
  `simulator_abort` carrying no chain identity, and crash-cut records grade
  TRUNCATED. Minimal fix: the §10-style standard revision for crash-terminal
  grading (on-chain abort identity + a truncation policy for crash-cut
  records). (`a01-a03-rerun-report.md` §7 concern 3.)
- **FW05** — `FW05@e527f26a` proves SDC 4/4 with oracle FAIL 4/4 but the
  store-committed lane is never read (no consumer edge) → LIFECYCLE_ONLY;
  `FW05@8377c011` never triggered (NO_INJECTION 5/5). PROPAGATION_VERIFIED
  stays 1 only via the frozen v3.2.11 prior audit (Q8). Minimal fix: an FW05
  ordinal/workload re-selection that binds a reload consumer to the FW05
  store lane (the same §2.2 preflight method that closed SQ01/SQ03/SP05).
- **RP01** — no closure-matrix row at the current sha; Task 15 evidence exists
  (Q7). HANG pilots grade causality PROVEN but cap at UNRESOLVED
  (RecordIntegrity TRUNCATED from the watchdog `fatal`); squash pilots grade
  PARTIAL (the lsq_squash site records `triggering_seq=0`). Minimal fix: the
  FAIL-event watchdog contract or a converter truncation policy for HANG
  (design decision, `rp01-task15-report.md` concerns 1/3), plus the pending
  E5/E6 terminal-grading rules.
- Squash-terminal residuals (FW02 3, MD04 1 per binary group) stay PARTIAL per
  the frozen v3.2.11 line (squash causation unproven); DA04 `@3e9148fc` and
  LP01/MD04 lifecycle-only vintages are historical raw-oracle rows already
  closed in `MissingEvidenceMatrix_v3.2.12.md` (SUPP supply / decision-moot).

## Q3. How many closure records, over how many binary groups — and are verdicts ever merged across binaries?

[FROM FINAL MATRIX]

Working value: **149 records over 29 per-(model, binary) groups** in the
intermediate matrix; binary purity 0 `BINARY_SHA_MISMATCH` / 0
`BINARY_SHA_UNRECORDED`. Verdicts are **never** merged across binaries: every
row is keyed `ModelID@<sha8>` (single-binary models carry no suffix), the
SUPP-MD04-R05 delta stays as two rows (Q9), and the ≥2-context verification
rule is applied inside one binary group only (`tools/update_lsu_v327_audit.py`
refuses to sum complete contexts across groups — pinned by
`tests/test_lsu_v327_audit.py::test_never_merges_complete_contexts_across_binaries`).
The final matrix adds the RP01 and A01/A03 `68c6ce73` groups; recount.

## Q4. What is the terminal and oracle distribution over the record set?

[FROM FINAL MATRIX]

Working value (intermediate matrix, record level, 149 records):
ObservedTerminal — MASKED 57, NO_INJECTION 41, CRASH 15, SQUASHED 13, SDC 22,
UNRESOLVED 1; ApplicationOracle — PASS 74, MISSING 59, FAIL 16;
FinalClassification — UNRESOLVED 57, LIFECYCLE_ONLY 42, VERIFIED_SINGLE_CONTEXT
27, PARTIAL 13, COMPLETE_CAUSAL_CHAIN 10. Hard-terminal precedence held
everywhere: HANG/TIMEOUT/SQUASHED terminals beat a passing oracle, and a
missing injection never grades an outcome. Recount from the final matrix.

## Q5. A01 — honest status?

**Not verified.** The v3.2.12 rerun (5 fault + 2 matched controls on the final
binary `68c6ce73…`, `pilots_v3_2_12/SUPP-A01-R01C..R05C`, `C01C/C02C`)
reproduced the frozen terminal profile exactly (CRASH, MASKED, UNRESOLVED,
MASKED, MASKED) and added the missing trace evidence: `a01_ea` 5/5 with real
PCs, `xor_delta=8/bit=3`, `request_va==actual_ea`; `a01_consumed` 4/5 with
hash-equal consumer edges; the R03C replay-discard is now an on-chain
explained fact (`a01_ea_discarded` + `a01_golden_resp`). What it did NOT
produce: a divergent-value reference comparison — the only computable
DataDelta is one cross-context pair with delta = 0 bits, so the acceptance leg
"≥2 contexts with non-zero DataDelta AND a consumer edge" is **not met**.
Crash attribution: A01-R01C stays `TEMPORAL_ASSOCIATION_ONLY` (panic VA ≠
actual EA; no identity-linked abort node). All 14 eight-field rerun records
grade identically to the old-binary records — the new binary changed the
evidence layer, not the frozen grades. No upgrade on inference;
`PROPAGATION_VERIFIED=0` unless the final matrix's E-rules change the grades.
Evidence: `audit_v3_2_12/A01_Propagation_Audit_v3.2.12.md`,
`A01_verdict_v3.2.12_v3.json`, `A01_A03_Rerun_Records_v3.2.12.csv`,
`A01_A03_Rerun_NodePresence_DataDelta_v3.2.12.md`.

## Q6. A03 — honest status?

**Not verified.** The rerun (5 fault + 2 controls on `68c6ce73…`) reproduced
the frozen terminals exactly: 5/5 CRASH with the same crash chain (dyn seq
1014 @ tick 1657040, panic VA `0xffffffffffb73c50`) and the same injection
counts (141/140/139/138/137). New trace evidence: `a03_activation` exactly 1
per fault run (the five activation start positions) and `a03_stream`
141/140/139/138/137 rows with the STUCK_APPLIED / ALREADY_STUCK masking path
now on-chain — and the crash attribution upgraded to **DIRECT_ADDRESS_MATCH**
(panic VA == the crashing load's on-chain `a03_stream.actual_ea`, 5/5).
The records still grade UNRESOLVED under the frozen rules: the abort is an
off-chain `simulator_abort` with no chain identity, and crash-cut records are
TRUNCATED. `PROPAGATION_VERIFIED=0` on the current evidence. Minimal fix as in
Q2. Evidence: `audit_v3_2_12/A03_Propagation_Audit_v3.2.12.md`,
`A03_verdict_v3.2.12_v3.json`, rerun CSV/MD.

## Q7. RP01 — honest status?

**Implemented and flown this round; not yet a complete verdict.** The
researcher-approved design (`APPROVED_BY_RESEARCHER_V3.2.12`, standard scope)
was implemented as a new `StructMode` of `CHAOSLSQFwd` (count-only selector +
one-shot skip at `lsq_unit.cc`'s partial-coverage reschedule site). Task 14
preflight: five frozen seeds, five distinct eligible events each
(`RP01_CountOnly_Preflight_v3.2.12.csv`). Task 15 executed **10/10 runs**
(`pilots_v3_2_12/RP01-R01..R05` + `RP01-CONTROL-R01..R05`, binary `68c6ce73…`):
pilots HANG×3 (R01/R04/R05, watchdog `CHAOS_RP01_WATCHDOG_EXPIRED` at
20M cycles, exit 1, fatal) and SQUASHED×2 (R02/R03 — proven P5 discards: an
unrelated `lsq_squash` freed the skipped load's LQ entry; golden checksum from
correct-path re-execution, not a recovery); controls 5/5 exit 0 with the
golden checksum `59fc61c040618747`, zero RP01 lines. **HANG is never MASKED**
— zero MASKED/SDC across all ten records (design-gate condition 4 CONFIRMED).
The HANG pilots' causality is PROVEN (bridged `RP01_SKIP_REPLAY` injection
identity-linked to the on-chain `replay` marker) but their classification caps
at UNRESOLVED solely by RecordIntegrity=TRUNCATED (the `fatal` cut leaves the
gz stream without its trailer); the squashes stay PARTIAL (`fault_caused=0`,
`triggering_seq=0`). No closure-matrix row exists at the current sha — the
pilot dirs landed after the last regeneration; the final matrix (E5/E6) is
authoritative for the graded outcome. Evidence: `audit_v3_2_12/RP01_verdict_v3.2.12.json`,
`RP01_records_v3.2.12.binary-68c6ce73.json`, `RP01_Task15_Evidence_v3.2.12.md`,
`RP01_CountOnly_Preflight_v3.2.12.csv`.

## Q8. The four frozen models (DA04, LP01, MD04, FW05) — status under v3.2.12 rules?

The v3.2.11 audit froze `PROPAGATION_VERIFIED=1` for exactly DA04, LP01, MD04,
FW05 ("Four models have a verified fault-effect propagation chain: DA04,
LP01, MD04, FW05" — `LSU_11Model_Propagation_Audit_Summary_v3.2.11.md` §1).
v3.2.12 handles each honestly:

- **DA04, LP01, MD04 — re-verified from the v3.2.12 matrix itself**, not by
  fiat: each has a binary group with ≥2 distinct complete contexts
  (`DA04@0de25644` SDC 2/2 and two further complete binary rows; LP01 `@69a1ca9c`
  MASKED 3 + SMOKE 1; MD04 `@0de25644` MASKED 3, `@e527f26a` 2). The Task 5
  SUPP raw-oracle runs (14 pilots on `e527f26a…`) closed the v3.2.11
  `ORACLE_FILE_MISSING` raw-artifact gap (T3) and corroborate — never
  replace — the original verdicts.
- **FW05 — carried by the frozen prior audit.** The v3.2.12 matrix has FW05
  rows (`@8377c011` trigger never fired; `@e527f26a` SDC 4/4 oracle FAIL 4/4)
  but no binary group with ≥2 complete contexts, because the store-committed
  lane is never read (no consumer edge → LIFECYCLE_ONLY under the generic
  classifier). The frozen verdict is carried by
  `tools/update_lsu_v327_audit.py` through
  `audit_v3_2_12/FROZEN_PRIOR_PROPAGATION_VERDICTS_v3.2.12.json`, which is
  cross-checked at load time against the frozen v3.2.11 audit matrix and the
  frozen v3.2.11-era status matrix copy — a sidecar cannot verify FW02 (1/5
  control-path, frozen 0) or LQ04 (frozen 0). The carry is honest about the
  current matrix state in the evidence cell. Minimal fix for a matrix-native
  FW05 verdict: Q2.
- The pending final grading round's **frozen-four import** (SDD task #50) may
  re-key these verdicts into the final matrix; recount from it when it lands.

## Q9. The SUPP-MD04-R05 adjudication delta — how is it recorded?

As **two per-binary rows, never merged** (runbook §5 check 5): the original
`MD04-R05` on binary `0de25644…` grades MASKED / VERIFIED_SINGLE_CONTEXT
(upgraded in-group to complete via the ≥2-distinct-context rule) while the
Task 5 raw-oracle supplementary `SUPP-MD04-R05` on binary `e527f26a…` grades
SQUASHED / PARTIAL. This is the by-design per-binary discipline: the SUPP run
corroborates the raw oracle and never replaces the original verdict, and the
two different outcomes on two binaries remain two visible facts. The same
discipline keeps the DA04 `@3e9148fc` (LIFECYCLE_ONLY 4, PARTIAL 1) vs
`@e527f26a` (SDC 2/2, oracle FAIL 2/2) split. Final matrix: re-verify the
split is retained.

## Q10. Controls — how many, and are they valid?

[FROM FINAL MATRIX for the final counts]

Working value: **17 controls in the record set** — 12 SUPP controls (A01×2 +
A03×2 + FW02×2 + SQ01/SQ03/SP05×2 each) plus the 5 by-design LQ04
zero-injection determinism controls. **SUPP control-valid tally 11/12.** The
one exception is the recorded and annotated misfire: `SUPP-FW02-C01` was run
with `--probability 0.0`, but the F6 FW02 injector ignores probability by
design and fired identically to R01 (`control_valid=False`,
`control_misfire=True` — `FW02_CONTROL_FIX_v3.2.12.md`); it stays visible in
the matrix/feature dataset graded on its own evidence (PARTIAL/SQUASHED) and is
excluded from control-valid counts. The valid probability-zero control is
`SUPP-FW02-C02` (injector omitted entirely). Each SQ-family `C01B` control is
a valid zero-injection replication; RP01's five controls all complete with the
golden checksum and zero injector lines. Directed controls are determinism
replications, never independent samples.

## Q11. W1–W8 no-fault baselines on the final binary — all PASS?

**Yes — 9/9 PASS on the final binary `68c6ce73…`.**
`logs_v3_2_12/baselines_w1_w8/FINAL_BASELINE_SUMMARY.csv` (run 2026-11-11
00:21–00:23, HEAD `86813b91`): W1 `728e604ffcec539d`, W2 `b097eb83f71545cb`,
W3 `ba3b3185e541ad03`, W4 `1f4cbf14327717df`, W5 `99c106541150be0e`, W6
`2543a2a60de01795`, W7 `59fc61c040618747`, W8a `67afad307642983e`, W8b
`3f89eab79392ce69` — every printed checksum equals its frozen golden from
`W1_W8_Baseline_Map_v3.2.12.csv` (60 frozen SampleRunIDs; workbook paths
re-anchored, workload SHAs recomputed and matching). The earlier
`BASELINE_SUMMARY.csv` (trace binary `720eb780…`) is superseded but retained.
The canonical unaffected regression (`reg_chain` via `configs/se/arm_chaos.py`,
O3) prints the golden `f247ef3fe6f02cfd`, exit 0. Test suites: platform suite
green (107 passed after the RP01 bridge round); repo `pytest tests/ -q` has
three pre-existing/environmental failures recorded and not fixed by this round
(claim-concurrency disk-redline ×2 — `/home` free 66.7 GiB vs the 70.6 GiB
campaign redline; and `test_lsu_v325_workbook.py`'s LQ04 evidence-text
expectation vs the v3.2.11-era `MODEL_STATUS_MATRIX.csv` — owned by Task 19's
derived rewrite). Caveat: if the binary is ever rebuilt again, all baselines
must be re-run under the new SHA.

## Q12. Workbook v3.2.7 and MODEL_STATUS_MATRIX — consistency state?

- **`MODEL_STATUS_MATRIX.csv`**: the v3.2.11-era file is frozen as
  `audit_v3_2_12/MODEL_STATUS_MATRIX_v3.2.11_frozen.csv` (sha256
  `ccd65763…`) and the v3.2.12 rewrite is **derived only**, by
  `tools/update_lsu_v327_audit.py` from the closure matrix:
  `PROPAGATION_VERIFIED=1` only when one binary group has ≥2
  COMPLETE_CAUSAL_CHAIN records, or the frozen prior audit (v3.2.11 frozen
  four) says so; a missing model row is a loud rejection unless explicitly
  declared pending; no cell is hand-set (`tests/test_lsu_v327_audit.py`, 14
  tests). Dry run on the intermediate matrix: 9 verified / A01, A03, RP01 = 0
  (RP01 `PENDING_NO_ROW`). The published rewrite runs against the FINAL
  matrix at Task 19 finalization.
- **Excel v3.2.7**: builder (`tools/build_lsu_v327_workbook.py`) and its 10
  tests are ready and green; **not published** — the published workbook must
  carry the FINAL matrix's sha256 in its change-record sheet
  (`EXCEL_V327_BUILDER_PREP.md` §3 preconditions 1–5: final matrix landed,
  final binary SHA confirmed, W1–W8 rebaseline recorded — satisfied, post-build
  validation, same-commit landing as the status matrix).
- **Invariants preserved**: ConfigFrozen = **NO** (all 60 rows); formal
  `ExecutionStatus` = **NOT_STARTED** (sheet 9); the 60 SampleRunIDs/Seeds
  and every highlighted cell unchanged from v3.2.6; Warm-up/ROI stay
  NEEDS_RESEARCHER_CONFIRMATION; the v3.2.6 workbook itself is untouched
  (sha256 `47262824…`, v3.2.6 tests still pass).

## Q13. Remaining blockers, and the final git state?

**Open blockers (honest list):**
1. **Final closure matrix not yet regenerated** — the E5/E6/E7 terminal-grading
   rules + frozen-four import (SDD task #50) and the RP01 / A01 / A03
   `68c6ce73` record groups must land; every `[FROM FINAL MATRIX]` cell in this
   report, the status-matrix rewrite and the published workbook depend on it.
2. **`GIT_COMMIT_v3212.txt` still records the pre-rebuild SHA `e527f26a…`**
   while the final binary is `68c6ce73…`
   (`logs_v3_2_12/binary_v3212_final_candidate.sha256`) — a reader keying the
   final-binary group off the wrong file will mis-key it.
3. **FW05** has no v3.2.12-native complete chain (Q8) — carried by the frozen
   prior audit until an ordinal/workload re-selection binds a reload consumer.
4. **RP01 HANG verdicts cap at UNRESOLVED** (TRUNCATED integrity from the
   watchdog `fatal`); needs the FAIL-event watchdog contract or a converter
   truncation policy; squashes need an on-chain `triggering_seq`.
5. **A01's matched-control reference leg** is structurally inexecutable
   (control-mode registration is the prerequisite); **A03's crash grading**
   needs the standard revision for on-chain abort identity.
6. **Disk**: `/home` free 66.7 GiB is below the 70.6 GiB campaign redline —
   future campaign-based runs abort until ~4 GiB is reclaimed (the 20 GiB
   pilot gate remains satisfied).
7. **Verbatim brief §15/§16** reconciliation (see Provenance above).

**Final git state** (append at publication, per plan Task 20 Step 4):
[FROM FINAL MATRIX — branch `lsu-platform-v3.2.12`, HEAD `<sha>`, status clean
at publication, binary SHA `68c6ce737a…` (both copies), disk free `<GiB>`]

---

*Every classification quoted above is deterministic tool output over committed
artifacts (`tools/lsu_12model_closure.py`, `tools/update_lsu_v327_audit.py`);
nothing in this report upgrades, relabels, or hand-sets a verdict. A wrong
application result is FAIL/SDC, never changed to PASS.*
