# LSU v3.2.12 — 12-Model Propagation Closure: Final Acceptance Report

**Status: FINAL (published 2026-11-11, plan Task 20).** Every number below is
derived from the FINAL closure matrix
`audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv`
(sha256 `064e28b456b9498e1c26d9ded203d8dd0127f09027113104c3879ac43d88474d`,
regenerated 2026-11-11 with the §12 terminal-grading rules E5/E6/E7 + the §12.5
keyed frozen prior-audit import; commit `36614647`), the final W1–W8 baselines
(`logs_v3_2_12/baselines_w1_w8/FINAL_BASELINE_SUMMARY.csv`), and the recorded
git/binary state. No verdict in this report is hand-set: every classification is
`tools/lsu_12model_closure.py` output over committed artifacts, the
`PROPAGATION_VERIFIED` rollup is derived by `tools/update_lsu_v327_audit.py`,
and every distribution below was recomputed from the final matrix CSV by script
at publication time (sum checks: every distribution totals 173 records).

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
  the A01/A03/RP01 verdict files); and (d) the dispatching agent's restatement
  of the thirteen questions (12/12 implemented; 12/12 five-context audits;
  propagation chains; per-model complete-context counts; terminal
  SDC/MASKED/SQUASHED/CRASH/HANG counts; earliest signals; final
  application/system-visible results; distinguishing diagnostic features;
  readiness for the 60 formal runs with ConfigFrozen=NO and Warm-up/ROI
  pending) — answered explicitly in §0 and inside Q1–Q13.
- **The main agent must reconcile these thirteen headings against the verbatim
  brief §16 before final submission.** If the verbatim questions differ, the
  headings are edited (the answers below are organized to map onto any
  numbering); no answer here is invented — every claim cites its artifact.

Scope: the twelve LSU fault models A01, A03, FW02, SQ01, DA04, LP01, MD04,
FW05, SQ03, SP05, LQ04, RP01 under the frozen v3.2.12 acceptance standard
(`LSU_Propagation_Acceptance_Standard_v3.2.12.md`, amended three times through
its own revise path: §10 exception E1 for LQ04, §11 exceptions E2/E3/E4 for
SQ01/SQ03/SP05, §12 exceptions E5/E6/E7 + §12.5 keyed frozen prior-audit
import). Worktree `lsu-platform-v3.2.12`; final binary `build/ARM/gem5.opt`
SHA256 `68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`
(`logs_v3_2_12/binary_v3212_final_candidate.sha256`; confirmed by the final
W1–W8 baselines and re-recorded in `GIT_COMMIT_v3212.txt`'s FINAL section).
**ConfigFrozen = NO. The 60-sample formal experiment runs are NOT_STARTED.
Warm-up/ROI remain NEEDS_RESEARCHER_CONFIRMATION.**

---

## 0. Result at a glance (the thirteen questions in one table)

| Question | Answer |
|---|---|
| How many models implemented? | **12/12** — every model DESIGNED→PILOT_RUN=1 in the derived `MODEL_STATUS_MATRIX.csv`; RP01 (the only v3.2.11 gap) was implemented this round as a new `StructMode` of `CHAOSLSQFwd` (count-only selector + one-shot skip at `lsq_unit.cc` partial-coverage reschedule). |
| How many models audited over five contexts? | **12/12** — each model carries its five frozen contexts R01–R05 (plus controls and, where required, eligible reruns) in the final matrix; 173 records over 32 per-(model, binary) groups. |
| How many models close at COMPLETE_CAUSAL_CHAIN? | **12/12** — every model has ≥2 distinct complete contexts inside one binary group (`tools/update_lsu_v327_audit.py` dry run against the final matrix: "PROPAGATION_VERIFIED=1 for 12 model(s); no cell hand-set"). |
| Propagation chains proven? | 60 records grade `COMPLETE_CAUSAL_CHAIN` (chain: injection → activation → early anomaly → intermediate propagation → register writeback → consumer edge → commit → terminal → oracle, with per-model §10–§12 exceptions as frozen in the standard); 71 records carry `FaultCausality=PROVEN`. |
| Terminal distribution (173 records)? | MASKED 60, NO_INJECTION 45, SDC 26, CRASH 21, SQUASHED 16, HANG 3, UNRESOLVED 2. |
| Oracle distribution (173 records)? | PASS 103, MISSING 43, FAIL 24, NOT_APPLICABLE 3. |
| Classification distribution? | COMPLETE_CAUSAL_CHAIN 60, UNRESOLVED 62, LIFECYCLE_ONLY 32, PARTIAL 19. |
| Earliest signals? | A01/A03 `address_formed`; FW02/FW05 `forwarding_decision`; SQ01/SQ03/DA04 `store_writeback`; LP01/LQ04/MD04 `memory_response`; SP05/RP01 no early-anomaly event (first on-chain evidence is the completion-accounting / replay-skip marker itself). |
| Final application/system-visible results? | SDC → oracle FAIL: SQ01 5/5, SP05 5/5, FW05 4/5 (frozen), DA04 2/2 (frozen) — corrupted data reaches the application checksum; MASKED → oracle PASS: LP01 5/5, LQ04 5/5, SQ03 5/5, MD04 3/5, A01 3+3, FW02 2 — fault absorbed before the checksum; CRASH → simulator panic: A03 5/5 (panic VA == the fault's own stuck EA); HANG → watchdog: RP01 3/5 fault runs at 20M cycles (`CHAOS_RP01_WATCHDOG_EXPIRED`), never MASKED/SDC. |
| Distinguishing diagnostic features? | Per-model §10–§12 mechanisms (Q1 table below): each model's chain is distinguishable by its earliest-signal stage, its masking/SDC mechanism, and its terminal shape — e.g. A03 is the only model whose panic VA identity-matches the on-chain stuck EA; RP01 is the only HANG-only model; SQ01/SP05 are SDC-through-reload while SQ03 is MASKED-through-visibility-move. Full per-record features in `LSU_12Model_Diagnostic_Feature_Dataset_v3.2.12.csv` (607 rows = 173 PILOT + 434 PATH_FRAGMENT). |
| Baselines clean? | W1–W8 **9/9 PASS** on the final binary `68c6ce73…` (Q11). |
| Controls valid? | 26 controls in the record set, 25 valid + 1 recorded/annotated misfire (`SUPP-FW02-C01`, Q10). |
| Ready for the 60 formal runs? | Evidence layer yes; configuration **no** — ConfigFrozen=NO (all 60 rows), formal `ExecutionStatus` NOT_STARTED, Warm-up/ROI NEEDS_RESEARCHER_CONFIRMATION; the 60 SampleRunIDs/Seeds and every highlighted cell are unchanged from v3.2.6 (Q12). |

---

## Q1. How many of the twelve models close at COMPLETE_CAUSAL_CHAIN, and which?

**All twelve.** Final matrix: 32 per-(model, binary) rows, 173 records. Every
model has at least one binary group with ≥2 distinct complete contexts
(record-level `COMPLETE_CAUSAL_CHAIN`), which is the standard §4 verification
rule applied inside one binary group only:

| Model | Best binary group | Complete contexts | Mechanism (frozen §10–§12 / prior-audit name) |
|---|---|---|---|
| A01 | `A01@68c6ce73` (also 3 on `@720eb780`) | **3** — R02C/R04C/R05C wrong-EA MASKED contexts | E7 `WRONG_EA_LOAD_DELIVERED_AND_CONSUMED` |
| A03 | `A03@68c6ce73` | **5** — R01C–R05C crash contexts | E6 `STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH` |
| FW02 | `FW02@720eb780` | **2** — R03/R04 MASKED contexts | generic §4 ≥2-context upgrade |
| SQ01 | `SQ01@720eb780` | **5** — SDC×5, oracle FAIL 5/5 | E2 `SQ_ENTRY_DATA_CORRUPTION_MEM_RELOAD_CONSUMER` |
| DA04 | `DA04@0de25644` (frozen import) | **2** — R04/R05 SDC, oracle FAIL 2/2 | prior audit `DISABLED_LANE_REACHED_CONSUMER_AND_ORACLE_FAILED` |
| LP01 | `LP01@0de25644` (frozen import) | **5** — MASKED×5 | prior audit `MODEL_SPECIFIC_ORIG_VS_INJ_DIVERGENCE_WITH_CONSUMER` |
| MD04 | `MD04@0de25644` (frozen import) | **3** — R02/R03/R05 MASKED | prior audit `violation_report_suppressed → load executes → … → commit` |
| FW05 | `FW05@8377c011` (frozen import) | **4** — R02–R05 SDC | prior audit true-vs-alt store source, SDC to consumer |
| SQ03 | `SQ03@720eb780` | **5** — MASKED×5, oracle PASS 5/5 | E3 `SQ_CANWB_VISIBILITY_MOVED_DRAIN_BEFORE_COMMIT` |
| SP05 | `SP05` (720eb780) | **5** — SDC×5, oracle FAIL 5/5 | E4 `STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED` |
| LQ04 | `LQ04` (f3c2a442) | **5** — MASKED×5 (5 fault + 5 controls in group) | E1 `RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE` |
| RP01 | `RP01` (68c6ce73) | **3** — R01/R04/R05 HANG contexts | E5 `REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT` |

Every complete verdict carries the standard's §6 invariant set (RecordIntegrity
VALID, TraceCompleteness COMPLETE, StructuralChainCompleteness COMPLETE,
FaultCausality PROVEN) — except where a frozen §10–§12 exception explicitly
names the relaxed field (E5 RP01 keeps `RecordIntegrity=TRUNCATED` /
`TraceCompleteness=INCOMPLETE`; E6 A03 keeps `RecordIntegrity=TRUNCATED` /
structural PARTIAL — both platform fields keep their honest values), and
except the frozen imports, whose five §1 fields the v3.2.11 prior audit did not
record per pilot and are the literal `NULL` — never fabricated (§12.5).
Binary purity held everywhere: 0 `BINARY_SHA_MISMATCH`, 0
`BINARY_SHA_UNRECORDED`, 0 blank cells, 0 bare `PASS` outside
`ApplicationOracle`, 0 complete-over-unverified defects
(`FINAL_GRADING_RULES_v3.2.12.md` §3).

## Q2. Which models remain below COMPLETE_CAUSAL_CHAIN, and what is each one's minimal fix?

**None at model level** — 12/12 close (Q1). The honest residuals are
record-level, all visible in the final matrix, none hidden:

- **A01** — R01C stays `UNRESOLVED`: the crash is a temporal association only
  (panic VA `0` ≠ the on-chain actual EA `7ffffefd98`), so E7's CRASH branch
  does not fire; R03C is `PARTIAL` via the E7 discard companion
  (`a01_ea_discarded` with `applied_to_request=0` — runtime proof the
  corrupted EA never reached a Request). Minimal fix for these two records:
  the matched-control reference leg is structurally inexecutable today
  (control runs record zero memory nodes); the prerequisite is the
  control-mode registration change (register the control run's loads with the
  chain-scoped tracer), then a golden-EA reference value per context
  (`A01_A03_Rerun_NodePresence_DataDelta_v3.2.12.md` §2–§4). Older vintages
  (`0fa610c2`, `275111d8`) stay UNRESOLVED/PARTIAL — no `a01_ea`-era trace
  evidence in those runs.
- **A03** — closed via E6 on `68c6ce73`; the crash-cut records keep
  `RecordIntegrity=TRUNCATED` and structural PARTIAL (the panic is the
  terminal). Older vintages (`0fa610c2`, `275111d8`, `720eb780`) stay
  UNRESOLVED — no `a03_stream`/abort identity evidence exists in their traces.
- **RP01** — R02/R03 stay `PARTIAL` (proven P5 squash discards, but the
  `lsq_squash` site records `triggering_seq=0`, so squash causation is
  unproven). Minimal fix: an on-chain `triggering_seq` at the squash site, or
  the FAIL-event watchdog contract / converter truncation policy for the HANG
  records' retained partial traces (design decision,
  `rp01-task15-report.md` concerns 1/3).
- **FW05** — verified via the frozen prior-audit import (`FW05@8377c011`
  4/5 complete); the v3.2.12-native consumer edge is still open:
  `FW05@e527f26a` proves SDC 4/4 with oracle FAIL 4/4 but the store-committed
  lane is never read (no consumer edge → LIFECYCLE_ONLY under the generic
  classifier). Minimal fix: an FW05 ordinal/workload re-selection that binds a
  reload consumer to the FW05 store lane (the same §2.2 preflight method that
  closed SQ01/SQ03/SP05).
- **Frozen-four squash residuals** (carried verbatim from the v3.2.11 prior
  audit, never re-graded): MD04 R01/R04 and FW05 R01 stay PARTIAL
  (squash-causality unproven per the prior audit).
- Historical-vintage lifecycle-only rows (DA04 `@3e9148fc`, LP01/MD04
  raw-oracle vintages, FW02 older groups, SQ01/SQ03 pre-eligibility groups)
  are already closed in `MissingEvidenceMatrix_v3.2.12.md` (SUPP supply /
  decision-moot) and remain visible as their own binary-keyed rows.

## Q3. How many closure records, over how many binary groups — and are verdicts ever merged across binaries?

**173 records over 32 per-(model, binary) groups** (final matrix, 24 columns;
feature dataset 607 rows = 173 `PILOT` + 434 `PATH_FRAGMENT`). Binary purity:
0 `BINARY_SHA_MISMATCH` / 0 `BINARY_SHA_UNRECORDED`. Verdicts are **never**
merged across binaries: every row is keyed `ModelID@<sha8>` (single-binary
models carry no suffix), the SUPP-MD04-R05 delta stays as two rows (Q9), and
the ≥2-context verification rule is applied inside one binary group only
(`tools/update_lsu_v327_audit.py` refuses to sum complete contexts across
groups — pinned by
`tests/test_lsu_v327_audit.py::test_never_merges_complete_contexts_across_binaries`).
The frozen prior-audit import supersedes generic records of the **same
(model, binary) key only**, with a loud exclusion note — never merged, no
double count (`FINAL_GRADING_RULES_v3.2.12.md` §2).

## Q4. What is the terminal and oracle distribution over the record set?

Final matrix, record level, 173 records (script-recomputed at publication;
each distribution sums to 173):

- **ObservedTerminal** — MASKED 60, NO_INJECTION 45, SDC 26, CRASH 21,
  SQUASHED 16, HANG 3, UNRESOLVED 2.
- **ApplicationOracle** — PASS 103, MISSING 43, FAIL 24, NOT_APPLICABLE 3.
- **FinalClassification** — COMPLETE_CAUSAL_CHAIN 60, UNRESOLVED 62,
  LIFECYCLE_ONLY 32, PARTIAL 19.
- **FaultCausality** — PROVEN 71, UNPROVEN 66, PARTIAL 14, NULL 22 (the NULLs
  are exactly the 22 frozen-imported records whose fields the prior audit did
  not record per pilot — §12.5).

Hard-terminal precedence held everywhere: HANG/TIMEOUT/SQUASHED/CRASH
terminals beat a passing oracle, and a missing injection never grades an
outcome. The 45 NO_INJECTION records are the 26 controls minus the one
misfire plus never-fired vintages (e.g. `FW05@8377c011` pre-rework R01 set,
`SQ01@8eb7ce8d`, `SQ03@b988b750`, `MD04@8377c011`) — all graded on their own
evidence, never silently dropped.

## Q5. A01 — honest status?

**Verified (E7).** The v3.2.12 rerun (5 fault + 2 matched controls on the final
binary `68c6ce73…`, `pilots_v3_2_12/SUPP-A01-R01C..R05C`, `C01C/C02C`)
reproduced the frozen terminal profile (CRASH, MASKED, UNRESOLVED, MASKED,
MASKED across R01C–R05C; R03C is the replay-discard context) and added the trace evidence the standard's
E7 requires: on-chain `a01_ea` with `golden_ea != actual_ea` (xor_delta=8,
bit=3) and `request_va==actual_ea` on the fault's own chain; verified
register writeback + consumer edges with `WritebackValueFnv ==
ConsumerInputFnv == a01_consumed.input_hash` (hash-equal, R02C/R04C/R05C);
the R03C replay-discard is an on-chain explained fact (`a01_ea_discarded`,
`applied_to_request=0` → PARTIAL, never UNRESOLVED, never complete). The
three wrong-EA MASKED contexts close the model (≥2 distinct complete
contexts, `VERIFIED_SINGLE_CONTEXT` each). Honest limits, stated plainly:
R01C's crash stays `TEMPORAL_ASSOCIATION_ONLY` (panic VA `0` matches nothing
on-chain; UNRESOLVED under rule 1); the divergent-value reference comparison
the original acceptance leg wanted (a matched-control golden-EA DataDelta) is
**still not produced** — the only computable DataDelta is one cross-context
pair with delta = 0 bits, because the matched-control reference leg is
structurally inexecutable (control-mode registration prerequisite, Q2). E7
closes the model on the wrong-EA-delivered-and-consumed proof instead; this
is the frozen standard's own amendment path (§12), not an inference upgrade.
Evidence: `audit_v3_2_12/A01_Propagation_Audit_v3.2.12.md`,
`A01_verdict_v3.2.12_v3.json`, `A01_A03_Rerun_Records_v3.2.12.csv`,
`A01_A03_Rerun_NodePresence_DataDelta_v3.2.12.md`.

## Q6. A03 — honest status?

**Verified (E6).** The rerun (5 fault + 2 controls on `68c6ce73…`) reproduced
the frozen terminals exactly: 5/5 CRASH with the same crash chain (dyn seq
1014 @ tick 1657040, panic VA `0xffffffffffb73c50`) and the same injection
counts (141/140/139/138/137). The trace evidence E6 requires is on-chain:
`a03_activation` exactly 1 per fault run (the five activation start
positions) and `a03_stream` 141/140/139/138/137 rows per run with the
STUCK_APPLIED / ALREADY_STUCK masking path visible; the crash attribution is
**DIRECT_ADDRESS_MATCH** — the panic VA equals the on-chain
`a03_stream.actual_ea` of an affected load (5/5), with the abort's
`last_injection_dyn_seq` equal to that record's `dyn_inst_seq`. All five
crash contexts close the model. Honest limits: the crash-cut records keep
`RecordIntegrity=TRUNCATED` (the `fatal` cut) and structural PARTIAL (the
panic is the terminal) — E6 grades complete on the identity-linked address
match while both platform fields keep their honest values; the older vintages
(`0fa610c2`, `275111d8`, `720eb780`) stay UNRESOLVED because their traces
carry no `a03_stream`/abort identity evidence. Evidence:
`audit_v3_2_12/A03_Propagation_Audit_v3.2.12.md`, `A03_verdict_v3.2.12_v3.json`,
rerun CSV/MD.

## Q7. RP01 — honest status?

**Implemented this round and verified (E5).** The researcher-approved design
(`APPROVED_BY_RESEARCHER_V3.2.12`, standard scope) was implemented as a new
`StructMode` of `CHAOSLSQFwd` (count-only selector + one-shot skip at
`lsq_unit.cc`'s partial-coverage reschedule site; code diff in
`GIT_DIFF_CODE_v3.2.12.txt`). Task 14 preflight: five frozen seeds, five
distinct eligible events each (`RP01_CountOnly_Preflight_v3.2.12.csv`).
Task 15 executed **10/10 runs** (`pilots_v3_2_12/RP01-R01..R05` +
`RP01-CONTROL-R01..R05`, binary `68c6ce73…`): fault pilots HANG×3 (R01/R04/R05,
watchdog `CHAOS_RP01_WATCHDOG_EXPIRED` at 20M cycles, exit 1, fatal) and
SQUASHED×2 (R02/R03 — proven P5 discards: an unrelated `lsq_squash` freed the
skipped load's LQ entry; golden checksum from correct-path re-execution, not
a recovery); controls 5/5 exit 0 with the golden checksum `59fc61c040618747`,
zero RP01 lines. **HANG is never MASKED** — zero MASKED/SDC across all ten
records (design-gate condition 4 CONFIRMED). The three HANG contexts close
the model under E5: causality PROVEN through the identity-linked
`RP01_SKIP_REPLAY`/`replay` records, the watchdog line parsed verbatim, and
the **watchdog partial trace retained** (≥1 chain event survived the fatal
cut) — while `RecordIntegrity=TRUNCATED` and `TraceCompleteness=INCOMPLETE`
keep their honest values. R02/R03 stay PARTIAL (`fault_caused=0`,
`triggering_seq=0` — Q2); the five controls are UNRESOLVED by design (zero
injection). Evidence: `audit_v3_2_12/RP01_verdict_v3.2.12.json`,
`RP01_records_v3.2.12.binary-68c6ce73.json`, `RP01_Task15_Evidence_v3.2.12.md`,
`RP01_CountOnly_Preflight_v3.2.12.csv`.

## Q8. The four frozen models (DA04, LP01, MD04, FW05) — status under v3.2.12 rules?

The v3.2.11 audit froze `PROPAGATION_VERIFIED=1` for exactly DA04, LP01, MD04,
FW05 ("Four models have a verified fault-effect propagation chain: DA04,
LP01, MD04, FW05" — `LSU_11Model_Propagation_Audit_Summary_v3.2.11.md` §1).
v3.2.12 closes all four **through the §12.5 keyed frozen prior-audit import**
(`tools/lsu_12model_closure.py frozen`), which imports the prior per-pilot
verdicts as closure records keyed by (model + binary SHA + evidence path),
carrying the prior verdict **verbatim** plus `PriorAudit="v3.2.11"`; the five
§1 fields the prior audit did not record per pilot are the literal NULL:

- **DA04** — `DA04@0de25644` COMPLETE 2/2 (R04/R05 SDC, oracle FAIL — the
  byte-enable 0xF→0xE disabled-lane contexts); `DA04@3e9148fc` keeps the
  older vintage's PARTIAL/LIFECYCLE_ONLY verdicts (0/5 there);
  `DA04@6808c56e` 2/2 and `DA04@e527f26a` 2/2 are generic complete rows.
- **LP01** — `LP01@0de25644` COMPLETE 5/5 (all five prior MASKED verdicts);
  generic complete rows on `@69a1ca9c` (3) and the SMOKE (1).
- **MD04** — `MD04@0de25644` COMPLETE 3 + PARTIAL 2 (R01/R04
  squash-causality unproven per the prior audit, carried verbatim).
- **FW05** — `FW05@8377c011` COMPLETE 4 + PARTIAL 1 (R02–R05 SDC; R01 squash
  unproven); `FW05@e527f26a` (the Task 5 raw-oracle SUPP runs) proves
  SDC 4/4 with oracle FAIL 4/4 but stays LIFECYCLE_ONLY — the
  v3.2.12-native consumer edge is still open (Q2's minimal fix stands).

The Task 5 SUPP raw-oracle runs (14 pilots on `e527f26a…`) closed the
v3.2.11 `ORACLE_FILE_MISSING` raw-artifact gap and corroborate — never
replace — the original verdicts, each on its own binary key. The derived
status rollup against the final matrix reports all four **"VERIFIED by
matrix"** (not by sidecar fiat): the frozen import put their complete
contexts into the matrix itself. Sidecar cross-checks still refuse to
verify FW02/LQ04 from the prior audit (frozen 0 there) — the tool cannot
hand-set a model the prior audit did not verify.

## Q9. The SUPP-MD04-R05 adjudication delta — how is it recorded?

As **two per-binary rows, never merged** (runbook §5 check 5): the original
`MD04-R05` on binary `0de25644…` grades MASKED and is upgraded in-group to
complete via the ≥2-distinct-context rule (`MD04@0de25644`: COMPLETE 3 +
PARTIAL 2), while the Task 5 raw-oracle supplementary `SUPP-MD04-R05` on
binary `e527f26a…` grades SQUASHED / PARTIAL (visible in `MD04@e527f26a`:
MASKED 2 + SQUASHED 1). This is the by-design per-binary discipline: the
SUPP run corroborates the raw oracle and never replaces the original
verdict, and the two different outcomes on two binaries remain two visible
facts. The same discipline keeps the DA04 `@3e9148fc` (LIFECYCLE_ONLY 4,
PARTIAL 1) vs `@e527f26a` (SDC 2/2, oracle FAIL 2/2) split. Verified
retained in the final matrix.

## Q10. Controls — how many, and are they valid?

**26 controls in the record set**: 16 SUPP controls (A01×4 — C01/C02 on
`720eb780` plus C01C/C02C on `68c6ce73`; A03×4 — C01/C05 and C01C/C05C;
FW02×2; SQ01/SQ03/SP05×2 each) plus the 5 by-design LQ04 zero-injection
determinism controls plus the 5 RP01 controls. **Control-valid tally 25/26.**
The one exception is the recorded and annotated misfire: `SUPP-FW02-C01` was
run with `--probability 0.0`, but the F6 FW02 injector ignores probability by
design and fired identically to R01 (`control_valid=False`,
`control_misfire=True` — `FW02_CONTROL_FIX_v3.2.12.md`); it stays visible in
the matrix/feature dataset graded on its own evidence (SQUASHED, oracle PASS)
and is excluded from control-valid counts. The valid probability-zero control
is `SUPP-FW02-C02` (injector omitted entirely). All other controls complete
with zero injections and the golden checksum (25/26 NO_INJECTION+PASS in the
record set; the misfire is the single SQUASHED+PASS control). Directed
controls are determinism replications, never independent samples.

## Q11. W1–W8 no-fault baselines on the final binary — all PASS?

**Yes — 9/9 PASS on the final binary `68c6ce73…`.**
`logs_v3_2_12/baselines_w1_w8/FINAL_BASELINE_SUMMARY.csv` (run 2026-11-11
00:21–00:23, HEAD `86813b91`): W1 `728e604ffcec539d`, W2 `b097eb83f71545cb`,
W3 `ba3b3185e541ad03`, W4 `1f4cbf14327717df`, W5 `99c106541150be0e`, W6
`2543a2a60de01795`, W7 `59fc61c040618747`, W8a `67afad307642983e`, W8b
`3f89eab79392ce69` — every printed checksum equals its frozen golden from
`W1_W8_Baseline_Map_v3.2.12.csv` (60 frozen SampleRunIDs; workbook paths
re-anchored, workload SHAs recomputed and matching). The earlier
`BASELINE_SUMMARY.csv` (trace binary `720eb780…`) is superseded but retained
on disk, out of the package. The canonical unaffected regression (`reg_chain`
via `configs/se/arm_chaos.py`, O3) prints the golden `f247ef3fe6f02cfd`,
exit 0 — re-run under the FINAL binary 2026-11-11
(`GIT_COMMIT_v3212.txt` FINAL section). Test suites at publication:
closure suite `tests/test_lsu_12model_closure.py` **36 passed**; v3.2.7
audit+workbook suites **24 passed** (14 audit + 10 workbook). Caveat: if the
binary is ever rebuilt again, all baselines must be re-run under the new SHA.

## Q12. Workbook v3.2.7 and MODEL_STATUS_MATRIX — consistency state?

- **`MODEL_STATUS_MATRIX.csv`**: the v3.2.11-era file is frozen as
  `audit_v3_2_12/MODEL_STATUS_MATRIX_v3.2.11_frozen.csv` (sha256 `ccd65763…`)
  and the v3.2.12 rewrite is **derived only**, by
  `tools/update_lsu_v327_audit.py` from the final closure matrix. The
  derivation run against the FINAL matrix reports: *"12 rows,
  PROPAGATION_VERIFIED=1 for 12 model(s); no cell hand-set"* — every model
  line reads "VERIFIED by matrix — best group <Model>@<sha8>
  COMPLETE_CAUSAL_CHAIN=<n>". The rewritten CSV is present in the working
  tree (2026-11-11 01:19, the concurrent finalization agent's uncommitted
  deliverable) and is included in the package in that state; it lands in the
  same commit sequence as the workbook.
- **Excel v3.2.7**: the workbook
  `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx` is published in
  the working tree (2026-11-11 01:19, same uncommitted finalization
  sequence; 22 sheets including `21.v3.2.12变更记录` and
  `22.v3.2.12传播链闭包矩阵`). Builder (`tools/build_lsu_v327_workbook.py`)
  and its 10 tests are green; the workbook carries the final matrix's
  sha256 `064e28b4…` in its change record per `EXCEL_V327_BUILDER_PREP.md`
  §3 preconditions.
- **Invariants preserved**: ConfigFrozen = **NO** (all 60 rows); formal
  `ExecutionStatus` = **NOT_STARTED**; the 60 SampleRunIDs/Seeds and every
  highlighted cell unchanged from v3.2.6; Warm-up/ROI stay
  NEEDS_RESEARCHER_CONFIRMATION; the v3.2.6 workbook itself is untouched
  (sha256 `47262824…`, v3.2.6 tests still pass).

## Q13. Remaining blockers, and the final git state?

**Open blockers (honest list, updated at publication):**

1. **FW05 v3.2.12-native consumer edge still open** — the model closes via the
   frozen prior-audit import; a native complete chain needs the
   ordinal/workload re-selection that binds a reload consumer to the FW05
   store lane (Q2/Q8).
2. **A01 crash attribution + reference leg** — R01C stays
   TEMPORAL_ASSOCIATION_ONLY (panic VA `0`); the matched-control golden-EA
   DataDelta comparison remains structurally inexecutable without the
   control-mode registration change (Q2/Q5).
3. **A03 crash-cut traces** — E6 grades the five crash contexts complete on
   the identity-linked panic-VA match, but the records keep
   `RecordIntegrity=TRUNCATED` / structural PARTIAL; a future standard
   revision may formalize the crash-terminal truncation policy (Q6).
4. **RP01 watchdog trace finalization** — E5 grades the three HANG contexts
   complete with the watchdog partial trace retained; the FAIL-event
   watchdog contract / converter truncation policy and the squash
   `triggering_seq` remain open design decisions (Q2/Q7).
5. **Excel v3.2.7 + MODEL_STATUS_MATRIX rewrite are working-tree files, not
   yet committed** — they are the concurrent finalization agent's
   deliverables and land in its commit; the package carries them in that
   state (Q12). `Closure_Matrix_Status_v3.2.12.md` still documents the
   intermediate 149-record matrix (pre-E5/E6/E7 regeneration) — the final
   32-row/173-record status MD regeneration is the same agent's pending
   item; `FINAL_GRADING_RULES_v3.2.12.md` §3 is the authoritative final-matrix
   status record in the meantime.
6. **60 formal runs not started** — ConfigFrozen=NO (all 60 rows),
   ExecutionStatus NOT_STARTED, Warm-up/ROI NEEDS_RESEARCHER_CONFIRMATION;
   the evidence layer (12/12 chains, baselines 9/9, workloads frozen, oracle
   map) is ready, the configuration decision is not.
7. **Disk**: `/home` free 67 GB is below the ~70.6 GiB campaign redline —
   future campaign-based formal runs abort until ~4 GiB is reclaimed (the
   20 GiB pilot gate remains satisfied).
8. **Verbatim brief §15/§16 reconciliation** (see Provenance above) — the
   20-item package list and the thirteen questions remain reconstructions
   until reconciled against the researcher's frozen brief.

**Final git state** (recorded 2026-11-11 ~01:20 CST, per plan Task 20 Step 4):

- Branch `lsu-platform-v3.2.12`, HEAD `87287cbd1aa6e8940146966705190a31507df71f`
  (`[LSU][MDSPEC][V3.2.12][DOCS] prepare the final acceptance report and status
  derivation`), 46 commits after the round baseline `c02976b2`
  (lsu-platform-v3.2.11 tip; `GIT_BASELINE_v3212.txt`).
- Working tree (uncommitted, the concurrent finalization agent's Task 19/49
  deliverables plus this round's Task 20 outputs):
  `M docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v3212.txt` (now records
  the FINAL binary `68c6ce73…` in a FINAL section, historical `e527f26a`
  entries retained),
  `M docs/gem5-fi/lsu/implementation_v3_2/MODEL_STATUS_MATRIX.csv` (derived
  rewrite, 12/12),
  `?? docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`,
  `?? LSU_v3.2.12_12Model_Propagation_Closure_Package.zip` (+ `.sha256`),
  `?? docs/gem5-fi/lsu/implementation_v3_2/DELIVERABLES_SHA256_v3212.txt`,
  this report and `LSU_v3.2.12_BLOCKERS.md` (modified/new).
- Binary SHA256 `68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`
  on both copies (`build/ARM/gem5.opt` and `CHAOS/gem5/build/ARM/gem5.opt`),
  re-verified 2026-11-11.
- Disk free: 67 GB on `/home` (354 GB total, 81% used).

---

*Every classification quoted above is deterministic tool output over committed
artifacts (`tools/lsu_12model_closure.py`, `tools/update_lsu_v327_audit.py`);
nothing in this report upgrades, relabels, or hand-sets a verdict. A wrong
application result is FAIL/SDC, never changed to PASS.*
