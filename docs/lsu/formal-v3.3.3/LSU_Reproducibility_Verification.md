# LSU v3.3.3 — Remote Reproducibility Verification

**Date:** 2026-11-13
**Source of reproduction:** `git@github.com:wangxumarshall/gem5-fi.git`, branch `lsu-formal-v3.3.3-frozen`
**Clone:** `/home/sdc/lsu-v333-repro-20261113` (shallow, single-branch, submodules not initialized)
**Verdict:** **REPRODUCIBLE — PASS on 9/10 checks; check 5 (test suite) is PARTIAL with documented, state- and path-dependent failures.** No experiment was rerun. No byte-identical rebuild is claimed.

## 1. Source fetch

```console
$ git clone --depth 1 --single-branch --branch lsu-formal-v3.3.3-frozen git@github.com:wangxumarshall/gem5-fi.git /home/sdc/lsu-v333-repro-20261113
$ git rev-parse HEAD
45eb57c100c23eb861d327aedf87082db045c9bc
$ git ls-remote --heads origin refs/heads/lsu-formal-v3.3.3-frozen
45eb57c100c23eb861d327aedf87082db045c9bc	refs/heads/lsu-formal-v3.3.3-frozen
$ git rev-parse HEAD:CHAOS/gem5/src
fdcf53f6b0b8427827e1442ada1f94e245584a2b
```
**PASS.** Clone HEAD equals the remote head; the `CHAOS/gem5/src` subtree equals the freeze-base subtree recorded in `LSU_GitHub_Frozen_Branch_Report.md`.

## 2. Submodules and external dependencies

`gem5-fs/` is empty (submodule intentionally not initialized). The formal campaign is SE (syscall-emulation); it does not use the FS kernel/disk images. No other submodule is required.

**PASS with explicit omission.** A future FS reproduction would require `gem5-fs` and a checkpoint; that is out of scope for this campaign.

## 3. Workload sources and ELFs

The 120-task dry run re-hashed all executed ELFs and reported:

```json
"elf_ok": true, "errors": [],
"task_count": 120, "unique_outdirs": 120, "unique_sample_run_ids": 60, "unique_seeds": 60, "pairing_ok": true
```

All 9 workload hashes match `campaign_identity.json`. Sources exist for all 9; 8 have compile scripts, `fw05_forward` does not (recorded as a limitation; ELF hash still verified).

**PASS.**

## 4. Formal config

```console
$ sha256sum configs/se/lsu_proxy.py
8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225  configs/se/lsu_proxy.py
```
**PASS.**

## 5. Tests

Two runs were performed, one in the clone and one in the original formal worktree (control):

| Location | Result |
|---|---|
| Clone (12 v3.3.3 test files) | **294 passed, 38 failed, 1 skipped** |
| Original formal worktree (same files) | **316 passed, 4 failed, 13 errors** |
| Clone, path-insensitive subset (control_proof, lock_resume, qualified, runner_errors, shell_pipeline, workbook) | **145 passed, 1 skipped** |

**PARTIAL — honest interpretation:**

- The 4 `test_lsu_v333_final_launch_acceptance.py` failures occur **identically in both locations**. They assert pre-launch conditions (`existing_outdir_collisions == 0`, campaign dir absent). After the campaign, `runs/lsu/formal_v333_final_20261112` exists, so those gates correctly report `READY_TO_LAUNCH_FORMAL_CAMPAIGN=NO`. They are **state-dependent post-campaign failures**, not content regressions.
- The extra clone failures are path- and fixture-dependent: the frozen manifest template embeds the original absolute path `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`, so tests that compare `FormalExecutionPath` to the current checkout fail by construction. The first failure quotes this directly:
  `row 2 ... FormalExecutionPath /home/sdc/gem5-fi-ding/... != resolve_workload /home/sdc/lsu-v333-repro-20261113/...`
- The propagation tests error in the original worktree as well (13 errors), so this file is not a clean gate even at the source.
- No failure indicates missing or corrupted campaign evidence; all data-derived reports regenerate identically (check 10).

**Conclusion:** the test suite is executable but is not a clean reproduction gate; the path-insensitive subset is 145/145, and the data-level checks pass. This limitation is carried into the archive rather than hidden.

## 6. 120-task dry run

```console
$ bash .repro/01_launch_campaign.sh --dry-run
...
dry-run: 120 commands; no run dirs written
DRY_RUN_SUMMARY {"binary_sha_ok": true, "config_sha_ok": true, "campaign_id_ok": true,
 "elf_ok": true, "pairing_ok": true, "sample_run_ids_ok": true, "seeds_ok": true,
 "task_count": 120, "unique_outdirs": 120, "unique_sample_run_ids": 60, "unique_seeds": 60,
 "existing_outdir_collisions": 0, "ok": true}
READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES
runner_exit=0
```
**PASS.** The frozen scripts were runtime-transformed (`ROOT=` rewritten to the clone); the originals were not edited. Transformed-script SHA256 values are in `.repro/transformed.sha256`.

## 7. 60 SampleRunIDs and 60 seeds

The dry-run summary reports `unique_sample_run_ids: 60`, `unique_seeds: 60`, `pairing_ok: true`, `unique_tasks: true`. The workload/context manifest independently confirms 60/60 and fault/control seed equality.

**PASS.**

## 8. Hash checks

```console
$ sha256sum build/ARM/gem5.opt
62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
$ sha256sum --quiet -c audit_v3_3_3/trace_closure/final_config/SOURCE_MANIFEST.sha256 && echo SOURCE_OK
SOURCE_OK
$ cd /home/sdc/lsu-v333-archive/raw_extracted/formal_v333_final_20261112
$ sha256sum --quiet -c SHA256SUMS.raw_runs && echo RAW_OK
RAW_OK
$ sha256sum --quiet -c SHA256SUMS.deliverables && echo DELIVERABLES_OK
DELIVERABLES_OK
```
**PASS.** 2193/2193 raw-run entries and 22/22 deliverable entries verify.

## 9. Raw archive readability

The extracted archive contains 120 run dirs (60 fault + 60 control), 120 attempts, 3 non-run collector dirs, `campaign_index.json` (120 tasks), and the checksum manifests. All 120 carry `prop_trace.csv.gz`; 105 carry `trace_v31.jsonl` (the 15 direct-driver runs do not, by design). The ZIP itself is `cece176a…` and passes `unzip -t`.

**PASS.**

## 10. Regenerate final reports and Excel

The archived campaign root was copied into the clone and stages 2–4 were rerun (`--regen`); no experiments were executed.

| Output | Comparison |
|---|---|
| `LSU_60Context_Causal_Propagation_Final.csv` | byte-identical (`d5b63c18…`) |
| `LSU_60Context_Final_Readiness.csv` | byte-identical (`421b010d…`) |
| `LSU_11Context_Repair_Validation.csv` | byte-identical (`c09c266c…`) |
| `LSU_Control_Audit_Formal.csv` | byte-identical (`a703b2ba…`) |
| `LSU_Evidence_Completeness_Audit.csv` | byte-identical (`b2d159fe…`) |
| `LSU_A03_Injection_Count_Semantics.csv` | byte-identical (`a2b95e5c…`) |
| `collector_full/LSU_60Context_Final_Readiness.csv` | byte-identical (`9146a161…`) |
| `collector_full/LSU_120Run_Campaign_Manifest.csv` | normalized-identical (only checkout paths differ) |
| `collector_full/LSU_60Fault_60Control_Pair_Map.csv` | normalized-identical |
| `collector_full/LSU_Control_Zero_Proof_Final.csv` | normalized-identical |
| `LSU_Final_Experiment_Config.xlsx` (8 sheets) | cell-identical after path normalization; binary differs due to XLSX zip timestamps |
| `collector_full/LSU_Formal_Experiment_Config_Final.xlsx` | same |

Readiness distribution reproduced exactly: `COMPLETE_CAUSAL_CHAIN=38`, `VALID_TERMINAL_CHAIN=12`, `QUALIFIED=5`, `TRACE_INCOMPLETE=5`; control audit 60/60 `ControlInjected=NO`.

**PASS.**

## 11. Independent audit and call-outs

Agent E independently re-ran checks 1–10 and returned **ACCEPT — PASS 9/10, check 7 PARTIAL**, no blocking findings (`LSU_Independent_Acceptance_v333_Preservation.md`). Call-outs incorporated here:

1. **Dry-run sequencing.** The §6 console output was captured **before** the archived campaign root was copied into the clone for `--regen`. It is a real pre-copy result. After the copy, a repeat dry run correctly reports `existing_outdir_collisions: 120` and `READY_TO_LAUNCH_FORMAL_CAMPAIGN=NO` — the same post-campaign state that the 4 launch-acceptance tests exercise. Both results are truthful; they describe different clone states.
2. **The 1.1 GB binary is not on the remote branch.** A fresh clone cannot produce the formal binary by itself; reproduction supplies it from `/home/sdc/lsu-v333-archive/binary/gem5.opt.v333-62e1b1be` and verifies `62e1b1be…`. Binary preservation therefore rests on the external archive, not on git.
3. **Tag state.** At verification time the remote had no `lsu-v3.3.3-formal-accepted` tag; the tag is pushed in the final step. The verified branch commit is `45eb57c1`; the tag target and archive HEAD are stated in `LSU_GitHub_Frozen_Branch_Report.md` and the tag message.
4. **Untracked launch packages.** The 6 formerly untracked v3.3.3 ZIPs are archived: 5 in `packages/` (Formal_Experiment_Ready, Formal_Campaign_Launch, Launch_Critical_Fix, Final_Formal_Launch, FINAL_LAUNCH_READY) and the Results ZIP in `raw/`. `LSU_Package_Archive_Manifest.csv` records the tracked/untracked status of each.

## Overall

- **PASS:** source, config, workloads, dry run, 60 IDs/seeds, all hashes, raw archive, report/Excel regeneration.
- **PARTIAL:** test-suite gate, with the state- and path-dependent failures documented above.
- **Not claimed:** byte-identical binary rebuild; 120-run re-execution; off-host raw-data copy (public repo).
- **Independent verdict:** ACCEPT, PASS 9/10 (the PARTIAL is check 5/7), no blocking findings.
