# LSU v3.3.3 — Agent F Independent Launch Acceptance (Final)

**Date:** 2026-11-12
**Auditor:** Agent F (independent launch preflight; read-only)
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111` · HEAD `b8405580`
**Scope:** 12 models × R01–R05; 60 fault + 60 matched control = 120 runs.
**Final verdict:** **`READY_TO_LAUNCH_FORMAL_CAMPAIGN = YES`**

> The packaged artifacts (`LSU_Launch_Preflight_Report.md`, `LSU_Final_Blockers.md`) declare `NO`
> on one blocker (B1: A01 census/executed `dyn_inst_seq` mismatch). I independently reproduced
> the reported numbers and then found the blocker is a **misdiagnosis**: the executed stream
> selects the *same eligible event* as the census at all five A01 contexts (identical PC and EA),
> with a **constant +157 dynamic-instruction offset** caused by the census being launched with a
> relative `--cmd` path. The percentile calibration is defined on the *eligible-event ordinal* axis,
> which is preserved. B1 therefore does not invalidate the A01 mapping/calibration and does not
> block launch. Two non-semantic metadata defects are reported as QUALIFIED below.

## 0. Method / integrity of this audit

All checks were executed read-only (Python `csv`/`json`/`openpyxl` read-only, `git`, `sha256sum`,
`df`, `free`, `pgrep`, `diff`, `zcat`). No source, config, tool, test, data, Excel or existing
artifact was modified. No gem5/scons was run. The only file written is this report.

## 1. Gate results (independent)

| # | Gate | Result | Key evidence (real) |
|---|------|--------|---------------------|
| 1 | 12/12 models; 60/60 SampleRunID+Seed; fault/control same seed; 60/60 pairs | **PASS** | manifest: 120 rows, 12 models ×10, fault 60/control 60, 60 unique fault `SampleRunID`+`Seed`, 0 duplicate (model,ctx,role); every pair fault.Seed==control.Seed and fault.SampleRunID==control.SampleRunID; no `V332`-style IDs |
| 2 | 60/60 control zero proof, 3-way class 35/25/0, applied 0, oracle PASS, paired target identity | **PASS** | `LSU_Control_Zero_Injection_Proof.csv`: 35 `MOUNTED_BUT_DISABLED` + 25 `INJECTOR_ABSENT` + 0 suppressed; `InjectionAppliedCount`={0} for all 60; `ControlOracle`=PASS 60; control manifest rows carry the fault's `DynInstSeq/PC/VA/PA` (0 mismatches) |
| 3 | 60/60 causal rows; terminal/oracle consistency; MASKED mechanisms; RP01 HANG | **PASS** | causal CSV: 60 rows, 16 cols, 0 blank cells; `(Terminal,Oracle)` = (SDC,FAIL)×43, (MASKED,PASS)×12, (HANG_WATCHDOG,NO_CHECKSUM)×5; 6 distinct masking mechanisms; RP01 5× `RP01_WATCHDOG_EXPIRED` ordinals 26/77/128/179/230 |
| 4 | 60/60 application oracle; 43 SDC FAIL / 12 MASKED PASS / 5 NO_CHECKSUM | **PASS (QUALIFIED)** | causal: FAIL 43 / PASS 12 / NO_CHECKSUM 5. **Defect:** manifest & pair map label the 5 RP01 rows `FAIL` (48 FAIL), disagreeing with the authoritative causal `NO_CHECKSUM` (see F-1) |
| 5 | Binary provenance b5031bf7 / 1126e0fd / 8309da72; 120 summaries one SHA | **PASS** | `git diff --stat b5031bf7 -- CHAOS/gem5/src` empty; `sha256sum build/ARM/gem5.opt` = `1126e0fd…f338` (== hardlink `audit_v3_3_3/binary/gem5.opt.v333-1126e0fd`); `sha256sum configs/se/lsu_proxy.py` = `8309da72…b225`; 120/120 `summary.json` carry `1126e0fd…` |
| 6 | 120-run manifest completeness; per-run `campaign_manifest.json` 120/120; dry-run 120 cmds, 0 collisions, no `audit_v3_3_3`, frozen seeds | **PASS** | manifest 40 cols, 0 blank in 13 critical fields; `find audit_v3_3_3/runs -name campaign_manifest.json` = 120; `dry_run_final.log`: 120 commands (105 run_pilot + 15 direct), 120 unique outdirs, `audit_v3_3_3` refs = 0, all under `runs/lsu/formal_v333`, `2108120075` present (A01 R01), `1842987246` present (LQ04 R01), 105× `--preserve-sample-id` |
| 7 | 51G free, 25G RAM, 126 cores, 0 gem5, output base writable | **PASS** | `df`: 51 GiB free /home; `free`: 25 GiB available; `nproc`=126; `pgrep -x gem5.opt`=none (0); `runs/` writable, new base `runs/lsu/formal_v333` absent (only `runs/guard`) |
| 8 | Config freeze YES; workbook 8 sheets / 60 IDs / 60 seeds | **PASS (QUALIFIED)** | `audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx`: 8 sheets, `Fault_Sample_Manifest` 60 unique IDs/60 seeds, `Control_Manifest` 60/60; `Binary_Config` ConfigFrozen=YES (approved 2026-11-12). **Defect:** the runner's identity file `60_SAMPLE_MATRIX.csv` still has ConfigFrozen=NO×60 and 35 `NEEDS_USER_DECISION` (legacy columns; see F-2) |
| 9 | Adversarial A01 blocker assessment | **BLOCKER NOT REAL → YES** | see §2 |
| 10 | Preflight-artifact honesty | **PASS (QUALIFIED)** | no blank PASS found; archived propagation versions listed with SHAs that match on disk; 6 agent reports present; pre-correction `685d88f7` binary overwrite + LQ04 `rngSeed=0` history are disclosed, not hidden; RP01 mislabel (F-1) is the one honesty defect |

## 2. The declared blocker B1 — independent adjudication (decisive)

**Claim (artifact):** census ordinal 597 → `dyn_inst_seq=12752`; executed fault ordinal 597 →
`dyn_inst_seq=12909`; same PC/EA; therefore the percentile calibration (N=129; 597/623/649/675/701)
"was measured on the census stream, which does not match the executed stream."

**Independent reproduction and refutation.** I compared the census ordinal table against all five
executed pre-formal fault contexts (`audit_v3_3_3/runs/A01-R0{1..5}-fault/addrpath_injections.log`)
and the paired control probe traces:

| Ctx | Ordinal | Census dyn | Executed dyn | Δ | Census PC / EA | Executed PC / EA |
|-----|--------:|-----------:|-------------:|--:|----------------|------------------|
| R01 | 597 | 12752 | 12909 | **+157** | 0x400578 / 0x493020 | 0x400578 / 0x493020 |
| R02 | 623 | 13267 | 13424 | **+157** | 0x4005e0 / 0x4930f0 | 0x4005e0 / 0x4930f0 |
| R03 | 649 | 14415 | 14572 | **+157** | 0x4006d0 / 0x493200 | 0x4006d0 / 0x493200 |
| R04 | 675 | 14815 | 14972 | **+157** | 0x4006d0 / 0x4932d0 | 0x4006d0 / 0x4932d0 |
| R05 | 701 | 14971 | 15128 | **+157** | 0x4006d0 / 0x4933a0 | 0x4006d0 / 0x4933a0 |

Every ordinal maps to the **same static PC and the same effective address** in both streams; the
`dyn_inst_seq` difference is a **constant +157** across all five. The executed dyn deltas
(515, 1148, 400, 156) are byte-identical to the census dyn deltas — i.e. the executed stream is the
census eligible-event stream shifted by a fixed non-eligible-instruction prefix.

**Root cause identified (the artifact says "not conclusively identified").** The census
(`audit_launch_v333/artifacts/A01_census_match`) was launched with a **relative** `--cmd` path
(`docs/.../agu_addrmodes`) and `countOnly=true`, whereas the fault/control runs use the absolute
path and `countOnly=false`. In SE mode the argv[0] string length shifts the emulated stack; the
propagation traces diverge first at row 113 (a store-to-load-forwarding event at tick 518980) with
a stack EA 0x80 apart (`7ffffefc10` vs `7ffffefb90`). The fault and control traces are **byte-identical
through row 5188** (the injection itself), and both have `simInsts=6753` / `simTicks=19642700` /
target tick 15674890, while the census has `simInsts=6722` / different stream. So the executed stream
is the real one; the census differs only in its non-eligible instruction count, not in the eligible
ordinal → PC/EA sequence.

**Why the calibration still holds.** The percentile rule (`CENSUS.md`, and `%` labels) is
`start + ceil(p·N) − 1` over the **main-window eligible ordinals** [585,713], N=129. Because the
executed stream's ordinal→PC/EA mapping is identical at 597/623/649/675/701 (which span that window)
and the total eligible count is identical (817), the ordinal axis — and therefore the 10/30/50/70/90
labels — is preserved. The +157 is a dynamic-instruction label offset, not an eligible-event offset;
it does not move any percentile.

**Is the rest of the A01 evidence valid?** Yes. The fault trace for A01-R01 contains the complete,
real chain: `injection` → `address_formed` (493020→493028, bit 3, size 8) → `register_writeback`
(arch_reg=1) → `commit` (commit_seq=61) → `errant_commit` (commit_seq=6169) → `a01_consumed` →
394 `consumer_commit` plus 48 `taint_value_mismatch`; oracle `expected=728e604ffcec539d
got=7218ee89e1894154` = FAIL, while the matched control is `ORACLE_PASS` with the same golden.
The fault/control pair is byte-identical up to the injection and differs only in the faulted EA.
A01 R03's correction smoke independently shows injection=1 / writeback=1 / oracle FAIL / control PASS.

**Decision.** B1 does **not** invalidate the A01 context mapping or percentile calibration, and it
does **not** block launch. The verdict is therefore **YES**. Condition already satisfied: the formal
campaign re-runs the same executed configuration (absolute `--cmd`, `countOnly=false`), in which
ordinals 597/623/649/675/701 select the same PC/EA — verified against the five pre-formal fault runs
and the five paired control probes. A re-census with the exact formal `--cmd` path would only align
the cosmetic `DynInstSeq` labels; it is not required for calibration validity. (If a reviewer insists
on label-level identity, run option (a) from `LSU_Final_Blockers.md`; this is a provenance
tidy-up, not a gate.)

## 3. Findings (raw paths)

**F-1 (QUALIFIED, non-semantic, should be fixed in the manifest post-step).**
RP01's five fault rows are labeled `OracleResult=FAIL` / `FaultOracle=FAIL` in
`audit_launch_v333/artifacts/LSU_120Run_Campaign_Manifest.csv` and
`audit_launch_v333/artifacts/LSU_60Fault_60Control_Pair_Map.csv`, but the authoritative causal file
`audit_launch_v333/artifacts/LSU_60Context_Causal_Propagation_Final.csv` (and the source
`audit_v3_3_3/runs/RP01-R0*-fault/summary.json`, `oracle=false, checksum=null`) classifies them
`NO_CHECKSUM`. This is a classifier drift: `tools/lsu_v333_launch.py` maps `summary.oracle is False`
to `FAIL` while the happens-before classifier maps "hang with no checksum" to `NO_CHECKSUM`. Gate 4's
expected 43/12/5 breakdown is correct in the causal file; the manifest/pair map show 48/12/0. The
formal post-step will reproduce the drift unless the manifest rule defers to the causal terminal for
HANG/`checksum=None`. Impact: metadata only — experiment evidence and causal classification are sound.

**F-2 (QUALIFIED, provenance drift).**
`docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` (the identity file the runner and
`lsu_v333_launch.py` load) still carries `ConfigFrozen=NO` for all 60 rows and
`DecisionStatus` = 35 `NEEDS_USER_DECISION` / 15 `PILOT_VERIFIED_FORMAL_NOT_RUN` /
5 `ACCEPTED_BY_RESEARCHER_2026-11-08` / 5 `FROZEN_FW05_WORKLOAD`, while the launch workbook
`audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx` (`Binary_Config`) and
`LSU_60Context_Final_Readiness.csv` record freeze = YES / approval 2026-11-12 / 60 `READY`.
The runner only consumes `RunID/SampleRunID/Seed`, so execution is unaffected, but a reader comparing
the two cannot reconcile the freeze state. Recommend annotating the legacy columns as superseded.

**F-3 (INFO).** The launch config workbook `audit_launch_v333/artifacts/LSU_Formal_Experiment_Config_Final.xlsx`
has 5 sheets (README, Fault_Config, Control_Config, ROI_Census, Config_Validation); the "8 sheets"
requirement is met by the design workbook `audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx`
(8 sheets). Both carry 60 IDs / 60 seeds. Not a defect — a naming/expectation mismatch.

**F-4 (INFO).** A03 `InjectionCount` = 51,310 / 51,303 / 51,304 / 51,283 / 51,253 in the manifest is
the persistent-fault per-eligible-event application count (summary `injection_count`), not a
one-shot count; the other models report 1. Semantically correct for the F5 persistent model, but the
column mixes two count definitions. Recommend documenting the column semantics.

**F-5 (INFO, disclosed history).** Per `LSU_Binary_Provenance.md` §6 the pre-correction
`685d88f7` binary was overwritten in place and is not retained; its 120 runs live at
`audit_v3_3_3/runs_685d88f7/` and are never mixed with the final set. Historical LQ04 runs used
`rngSeed=0` (F0 ordinal selection is deterministic) and are kept as history; the formal runner now
passes the frozen `--lq04_rng_seed`. Both are disclosed, not hidden.

**F-6 (INFO).** `audit_v3_3_2/binary/gem5.opt.v332-070d68a6` is a pre-existing hardlink to the final
binary (hashes `1126e0fd`) and lies outside the v3.3.3 package; noted for packaging hygiene only.

## 4. Prep-artifact honesty checks (Gate 10 detail)

- No blank `PASS` cells found (`grep` for `| PASS | |` style returns none); `Config_Validation` in
  the config workbook is computed from the actual CSVs (all True / 60 rows).
- `LSU_ARCHIVED_Propagation_Versions.csv` lists exactly the two lossy 14-column copies as ARCHIVED,
  and both on-disk SHA256 values match the listed values (`c824f36f…`, `b98eeed3…`). The authoritative
  file is the 16-column `LSU_60Context_Causal_Propagation_Final.csv` (60 rows, 0 blanks).
- Six preflight agent reports present: `Agent_A_Excel_Identity_Report.md`,
  `Agent_B_Manifest_Consistency_Report.md`, `Agent_C_Control_Zero_Proof_Report.md`,
  `Agent_D_Propagation_Oracle_Report.md`, `Agent_E_Runner_Preflight_Report.md`,
  `Agent_F_Independent_Preflight_Baseline.md`.

## 5. Conditions / residual

- Launch may proceed with the A01 contexts as frozen (option (b) effectively already satisfied:
  the executed identities are real and the percentile labels are ordinal-preserved).
- Before the formal manifest is treated as authoritative, fix F-1 so RP01 is classified
  `NO_CHECKSUM`, not `FAIL` (one-classifier rule). F-2..F-6 are documentation hygiene.
- None of F-1..F-6 changes the 120-run experiment semantics, the fault/control pairing, the binary
  provenance, or the resource/runner readiness.

## 6. FINAL VERDICT

```
READY_TO_LAUNCH_FORMAL_CAMPAIGN = YES
```

Sole packaged blocker B1 (A01 census/executed `dyn_inst_seq` mismatch) is independently shown to be
a constant +157 dynamic-instruction label offset (`--cmd` path / SE stack layout), with identical
ordinal→PC/EA at all five contexts and an intact byte-identical fault/control pair; it does not
invalidate the A01 mapping or percentile calibration. Remaining items are non-blocking metadata
(F-1..F-6, with F-1 the only one worth fixing before the formal manifest is cited).

Report file: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/audit_launch_v333/reports/Agent_F_Independent_Launch_Acceptance.md`
