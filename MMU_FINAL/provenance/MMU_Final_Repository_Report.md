# MMU Final Repository Report

Date: 2026-11-15
Server: 0202 (openEuler 22.03 LTS, aarch64)

## 1. Authoritative branch

| Item | Value |
|---|---|
| Repository | https://github.com/wangxumarshall/gem5-fi |
| Branch | `mmu-final-reproducible` |
| Published head | `efbc0979` (subsequent metadata commits may advance it) |
| Base freeze commit | `872953c2` |
| Source closure | `60f1a8760410288128061d85582e5395b24c0106` |
| Frozen binary SHA256 | `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185` |
| MMU branches on GitHub | **1** (verified with `git ls-remote`) |

No MMU branch existed on GitHub before publication, so there is no remote MMU
branch deletion to perform. `main`, `fsu`, the LSU branches and all other
research branches were left untouched.

## 2. Result invariants (verified from the archive)

| Item | Value |
|---|---|
| Formal samples | 40/40 completed and activated |
| Terminal | **31 SDC · 5 DETECTED_CONTAINED · 4 SQUASHED** |
| Propagation | 36 FULL · 4 PARTIAL (M03 R01-R04, legal squash) |
| Trace completeness | 40/40 COMPLETE |
| Controls | 28 independent controls, 28/28 ZERO_PROVEN, all PASS |
| Repeatability | 10/10 activation · 10/10 propagation · 10/10 terminal |
| Attempts | A01 40 samples; A02 reruns for M06-R04 and M08-R04 |

`verify_archive.py` and `validate_results.py` both PASS; see
`MMU_Archive_Integrity_Report.md`.

## 3. Server inventory and cleanup

| Location | Size | Classification |
|---|---|---|
| `/home/sdc/gem5-fi-mmu-impl-v2` | 445.6 GB | KEEP_ACTIVE (authoritative worktree) |
| `runs/MMU_FORMAL_CAMPAIGN_20261113` | 80.7 GB | KEEP_ARCHIVE |
| `runs/disks` | 20.1 GB | KEEP_ACTIVE (runtime assets) |
| 28 control dirs | 43.3 GB | KEEP_ARCHIVE |
| 150 non-control `TEST-*` pilot dirs | 229.3 GB | SAFE_TO_DELETE (evidence packed) |
| `phase2`, `phase2_1`, `phase2_2` | 57.4 GB | KEEP_ARCHIVE (37 disk.img are template-identical) |
| `/home/sdc/gem5-fi-mmu-stage2` | 64.4 GB | NEEDS_REVIEW (shared FSU worktree; do not delete) |
| `/home/sdc/mmu_phase1_work` | 74 MB | KEEP_ARCHIVE |
| `/home/sdc/gem5-fi-mmu` | 16.3 GB | NEEDS_REVIEW (displaced FSU worktree) |
| `/home/sdc/gem5-fi-ding` | 15.6 GB | KEEP_ACTIVE (repo with GitHub origin) |
| `/home/sdc/wangxu/gem5-fi` | 13.5 GB | KEEP_OTHER_PROJECT |
| `/home/sdc/w10_scratch` | 4 KB (empty) | SAFE_TO_DELETE |

The exact deletion white-list is in `MMU_Server_Cleanup_Plan.csv` and
`MMU_Cleanup_Classification.csv`. Nothing irreversible has been executed:
`MMU_Deletion_Execution_Log.csv` has no data rows.

Proposed safe cleanup (requires researcher approval):

1. Delete 150 non-control `TEST-*` pilot directories after the evidence pack
   (`results/history/pilot_evidence.tar.gz.part00/01`, 3890 files, SHA256
   `168f0584...`) is confirmed — frees 229.3 GB.
2. Delete the 37 `disk.img` files under `phase2/phase2_1/phase2_2`; all are
   byte-identical to `runs/disks/mmu_template.img` — frees ~57 GB actual.
3. Remove the empty `w10_scratch` directory.
4. `git worktree prune` the stale `gem5-fi-fsu` registration (metadata only).
5. Delete the local `mmu-formal-freeze-2026-11-12` branch after the final
   branch is verified; it has no unique commits.

Items 1–5 are **not executed** in this round.

## 4. What is preserved

- Complete M01-M08 hooks, configs, workloads and frozen runner.
- 40 formal sample trees: raw trace, logs, oracle, verdict, manifest, SHA256.
- 28 control oracles and their zero-injection evidence.
- 10 repeat traces and the activation/propagation/terminal comparisons.
- Diagnostic feature library, model propagation signatures, blinded and
  observable views, leakage audit, consumption evidence, real-case mapping.
- Historical pilot evidence (packed) and superseded A01 attempts.
- Frozen authority, v3.0.2 parity authority and pilot evidence.
- Checkpoint and bootloader (bundled); kernel and disk template are external.

## 5. Known limitations

1. `vmlinux` (227 MB) and `mmu_template.img` (2.36 GB) are
   `EXTERNAL_ASSET_NOT_YET_DISTRIBUTED`; external full-system execution is
   blocked until they are published. Code, results and archive verification
   are complete without them.
2. The checkpoint's originally recorded digest `4aa1ba38...` could not be
   reproduced from the current directory; the recomputed manifest digest
   `ab200657...` is recorded. The checkpoint is exercised by the smoke test.
3. No standalone `MMU决策树.md` exists on the 0202 server. The decision logic
   is present as `Model_Propagation_Signatures.md` (model signatures, key
   discriminators, confusable paths, ranked root-cause features). This is
   reported rather than fabricated.
4. The frozen binary does not emit full IFU fetch/decode/commit events;
   instruction-side evidence stops at the Execute Request and guest oracle.
5. Ten repeats establish determinism for the selected contexts, not a
   statistical distribution.
6. The simulator models are abstractions, not bit-exact physical ARM claims.

## 6. Independent reproduction

| Check | Result |
|---|---|
| Fresh GitHub clone | PASS (commit `100f9ce3`, no path/symlink to the old workspace) |
| Independent clean build | PASS (`16a954c7...`, 8/8 hooks, gcc 10.3.1, `-j16`) |
| Archive check in clone | PASS (1514 files) |
| 40 describe plans with archived controls | PASS 40/40 (rebuilt-binary waiver recorded) |
| 8-model smoke test | **PASS 8/8**, terminals match the frozen matrix |

Details: `MMU_Reproduction_Validation_Report.md` and
`MMU_8_Model_Smoke_Test_Results.csv`.

## 7. Status

`MMU_FINAL_CONSOLIDATION_READY`

The code, results, archive and independent reproduction gates pass. The only
remaining action is the researcher's approval of the permanent-deletion
white-list (`MMU_Server_Cleanup_Plan.csv`). No deletion has been executed, so
this is **not** `MMU_FINAL_CLEANUP_COMPLETE`.
