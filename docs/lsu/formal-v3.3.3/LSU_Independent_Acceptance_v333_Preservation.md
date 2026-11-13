# LSU v3.3.3 Final Preservation — Independent Acceptance Audit (Agent E)

**Date:** 2026-11-13
**Auditor:** Agent E, independent. I did not create, modify, or clean any artifact under audit. All commands below were actually run during this audit; all quoted outputs are real observed output.
**Scope:** `/home/sdc/lsu-v333-archive/`, remote branch `lsu-formal-v3.3.3-frozen`, clone `/home/sdc/lsu-v333-repro-20261113`, formal worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`, and the reports under `/home/sdc/lsu-v333-archive/analysis/` and `/tmp/lsu-freeze-20261113/docs/lsu/formal-v3.3.3/`.
**Constraints honored:** read-only on all evidence; no deletion, no move, no `git add/commit/push`, no gem5 experiment, no subagent; the only file written by this audit is this report (scratch regeneration outputs went to `/tmp/lsu-audit-regen/`). Git state of the formal worktree was re-checked after my test runs and is unchanged (0 tracked modifications before and after).

---

## Frozen identity under audit (recomputed by me)

| Item | Audited value | My recomputation | Match |
|---|---|---|---|
| Results ZIP SHA256 | `cece176a894edf139209c21fd219d031f4c0ea99a60cc2664addd743ac2df235` | `sha256sum raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip` → `cece176a…df235` | YES |
| Binary SHA256 | `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd` | `sha256sum binary/gem5.opt.v333-62e1b1be` → `62e1b1be…7a6cd` | YES |
| Config SHA256 | `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` | `sha256sum config/lsu_proxy.py` → `8309da72…cb225` | YES |
| Campaign | `LSU-V333-FINAL-20261112`, 120 tasks | `campaign_index.json` `campaign_id` + `task_count: 120` | YES |
| C++ source commit / freeze base | `e3293856` / `7067805d`, zero C++ drift | subtree `CHAOS/gem5/src` = `fdcf53f6b0b8427827e1442ada1f94e245584a2b` at **all three** of `e3293856`, `7067805d`, frozen HEAD; `git diff --stat e3293856 7067805d -- CHAOS/gem5/src` → empty | YES |

---

## Check 1 — Archive hashes and checksum manifests: **PASS**

Commands and real output:

```console
$ cd /home/sdc/lsu-v333-archive && sha256sum raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip binary/gem5.opt.v333-62e1b1be config/lsu_proxy.py
cece176a894edf139209c21fd219d031f4c0ea99a60cc2664addd743ac2df235  raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip
62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd  binary/gem5.opt.v333-62e1b1be
8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225  config/lsu_proxy.py

$ unzip -t raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip | tail -1
No errors detected in compressed data of raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip.

$ cd raw_extracted/formal_v333_final_20261112
$ sha256sum --quiet -c SHA256SUMS.raw_runs && echo RAW_OK      → RAW_OK      (2193 entries)
$ sha256sum --quiet -c SHA256SUMS.deliverables && echo OK     → DELIVERABLES_OK (22 entries)

# In the formal worktree (the 7 frozen C++ sources):
$ sha256sum --quiet -c /home/sdc/lsu-v333-archive/manifests/SOURCE_MANIFEST.sha256 && echo OK
SOURCE_MANIFEST_OK_7x

$ cd /home/sdc/lsu-v333-archive/packages && sha256sum --quiet -c SHA256SUMS && echo OK
PACKAGES_OK   (10 entries)
```

All hashes match the frozen identity and the preservation report §3 (sizes verified: ZIP 400,982,936 B; binary 1,149,269,352 B; config 68,993 B; build.log 98,134 B). The sidecar `raw/*.zip.sha256` records the formal-worktree path and the same `cece176a…` hash. The archive binary is a **real byte copy**: inode 15765571, `links=1`, distinct from the worktree binary's inode 7341432 — confirming the report's "real copy (distinct inode)" claim.

## Check 2 — Run inventory and status counts: **PASS** (with two clarifications)

Real output:

```console
$ cd raw_extracted/formal_v333_final_20261112
$ ls | wc -l                       → 140
$ ls -d *-fault   | wc -l           → 60
$ ls -d *-control | wc -l           → 60
$ ls -d */ | grep -vE '^[A-Z0-9]+-R[0-9]+-(fault|control)/$'
collector_full/  collector_manifest/  collector_manifest.stage2-failed-20261113/
$ find . -maxdepth 3 -type d -name attempt_001 | wc -l           → 123
$ find . -maxdepth 3 -type d -name attempt_001 | grep -cE '^\./[A-Z0-9]+-R[0-9]+-(fault|control)/attempts/attempt_001$'  → 120
```

- 120 run dirs = 60 fault + 60 control; exactly 3 non-run dirs; 17 root files (140 total). Every run dir has exactly one attempt (`attempt_001`); 0 retries (confirmed per-run: no run dir has ≠1 attempts).
- The 3 additional `attempt_001` paths live inside the collector dirs (`collector_full/per_run/attempt_001` etc., each containing `campaign_manifest.json`); they are collector artifacts, not run attempts. The "120 attempt_001 dirs" claim is correct for run dirs.
- `campaign_index.json`: `task_count: 120` (field and actual list length), `counts {COMPLETED: 77, ORACLE_FAIL: 43, FAILED/TIMEOUT/HASH_MISMATCH/OUTPUT_INCOMPLETE/PENDING/RUNNING: 0}`, per-task `state` 77/43, per-task `role` 60/60.
- **Collector 72+43+5 vs index 77+43 — difference explained and independently reproduced.** I reran the collector myself from the archive-identical run data (see check 6):

```console
$ python3 tools/lsu_v333_launch.py --runs runs/lsu/formal_v333_final_20261112 … --out /tmp/lsu-audit-regen/collector_full
collected 120 tasks … formal=120 non_formal=0
statuses {"COMPLETED": 72, "ORACLE_FAIL": 43, "TRACE_INCOMPLETE": 5}
```

  The 5 RP01 `INTERNAL_WATCHDOG_DEADLINE` (HANG_WATCHDOG) runs are `COMPLETED` in the runner's index (the runner finished them via the watchdog) but `TRACE_INCOMPLETE` in the collector (no complete trace chain). 72 + 5 = 77. The acceptance report §2 documents exactly this (collector: ORACLE_FAIL 43, COMPLETED 12, TRACE_INCOMPLETE 5 for fault runs, plus 60 control COMPLETED).
- **"63/60" clarification:** the "63/60 split" figure in the audit request does **not** appear in any audited report, and no count of 63 is derivable from the data (I checked role, state, reason, TerminalState, ApplicationOracle, InjectionCount, TraceV31Status, PropagationCoverage, per-model distributions). The split every report actually claims — and which I verified three independent ways (filesystem, `campaign_index` roles, `LSU_Final_Oracle_Summary.csv`) — is **60 fault / 60 control**. The request's figure appears to be an error (possibly a garbled "60/60" or a misreading of the 123 subdirectories / 123 attempt dirs). No report overstates anything here; the reports' 60/60 is correct.
- Consistency note (not a discrepancy, to preempt confusion): the raw-data manifest's `TerminalState` `MASKED=17` counts all 120 runs (12 fault MASKED + 5 control `STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS`), while the acceptance report's fault-only table says MASKED 12. Both are internally consistent.

## Check 3 — 105/120 trace_v31.jsonl vs 120/120 prop_trace.csv.gz: **PASS**

Real output:

```console
$ python3 - … glob('*-R0*/attempts/attempt_001/trace_v31.jsonl')   → 105
$ … glob('…/prop_trace.csv.gz')                                   → 120
runs WITHOUT trace_v31.jsonl: 15
  A03-R01-fault  A03-R02-fault  A03-R03-fault  A03-R04-fault  A03-R05-fault
  RP01-R01-control RP01-R02-control RP01-R03-control RP01-R04-control RP01-R05-control
  RP01-R01-fault   RP01-R02-fault   RP01-R03-fault   RP01-R04-fault   RP01-R05-fault
```

Exactly 15 runs lack `trace_v31.jsonl` — A03 fault R01–R05 and RP01 fault+control R01–R05 — and all 120 carry `prop_trace.csv.gz`. This matches the preservation report §4 ("15 direct-driver runs … documented design property, not loss") exactly. The evidence audit CSV independently carries `TraceV31Status {PRESENT: 105, ABSENT_DIRECT_DRIVER: 15}` and `RawPropTraceStatus {PRESENT_DECOMPRESSIBLE: 120}`.

## Check 4 — Remote freeze branch, subtree equality, tag absence: **PASS**

Real output:

```console
$ git ls-remote origin refs/heads/lsu-formal-v3.3.3-frozen
45eb57c100c23eb861d327aedf87082db045c9bc	refs/heads/lsu-formal-v3.3.3-frozen
$ git ls-remote --tags origin | wc -l        → 0        (remote carries NO tags)
$ git log --oneline 7067805d..lsu-formal-v3.3.3-frozen   (in the formal worktree's object store)
45eb57c1 [LSU][V3.3.3][ARCHIVE] record frozen branch push and identity chain
ce6972cf [LSU][V3.3.3][CLEANUP] add branch and server deletion candidates (no deletion executed)
d81f0d0a [LSU][V3.3.3][ARCHIVE] add final result index and acceptance evidence
780129bb [LSU][V3.3.3][MANIFEST] freeze 12 models, 60 contexts, 60 seeds and 120-run archive index
e72c055c [LSU][V3.3.3][ARCHIVE] freeze formal source provenance and source closure manifest
$ git show --stat --oneline 45eb57c1
 …/LSU_GitHub_Frozen_Branch_Report.md | 64 +++++++++++++++  (1 file changed, 64 insertions)
$ for ref in e3293856… 7067805d… lsu-formal-v3.3.3-frozen; do git rev-parse $ref:CHAOS/gem5/src; done
fdcf53f6b0b8427827e1442ada1f94e245584a2b   (all three identical)
$ git diff --stat e3293856 7067805d -- CHAOS/gem5/src      → (empty)
$ git diff --stat 7067805d lsu-formal-v3.3.3-frozen -- CHAOS/gem5/src  → (empty)
```

- Remote HEAD `45eb57c1` matches the tasking and the reproducibility report. It is one docs-only commit ahead of the push-time HEAD `ce6972cf` recorded in `LSU_GitHub_Frozen_Branch_Report.md`; that commit adds only the frozen-branch report itself. Chronology is consistent.
- Zero C++ drift verified **independently of the reports**: identical subtree hash at the binary's build commit `e3293856`, the freeze base `7067805d`, and the frozen branch HEAD; empty diffs both ways.
- No tag `lsu-v3.3.3-formal-accepted` exists; the remote has zero tags, exactly as the frozen-branch report states (the tag is deliberately deferred until after the reproduction evidence, per its §Tag).

## Check 5 — Independent 120-task dry run: **PASS** (with a state-dependent caveat)

First, an honesty note about what is reproducible today: the campaign data was later copied into the clone (for check-10 regeneration), so the wrapper's fail-closed guard now triggers:

```console
$ bash .repro/01_launch_campaign.sh --dry-run
refusing to reuse a non-empty formal output dir: runs/lsu/formal_v333_final_20261112
```

This proves the reproducibility report's §6 console output (collisions=0, READY=YES) was captured **before** the campaign copy was placed in the clone — a sequencing fact the report implies but does not state. I therefore reran the underlying runner directly (its `--dry-run` branch is validation-only: "no campaign directory, no gem5 process"; I verified the code before running it):

(a) Frozen out-base, current clone state — all identity gates OK, only the state-dependent collision gate differs:

```console
{'task_count': 120, 'unique_task_count': 120, 'unique_tasks': True, 'unique_sample_run_ids': 60,
 'unique_seeds': 60, 'sample_run_ids_ok': True, 'seeds_ok': True, 'pairing_ok': True,
 'unique_outdirs': 120, 'existing_outdir_collisions': 120, 'binary_sha_ok': True,
 'config_sha_ok': True, 'elf_ok': True, 'campaign_id': 'LSU-V333-FINAL-20261112', 'campaign_id_ok': True}
READY_TO_LAUNCH_FORMAL_CAMPAIGN=NO        (state-dependent, as expected)
```

(b) Neutral non-existent out-base — full reproduction of the report's gate, nothing written:

```console
… "existing_outdir_collisions": 0, "ok": true, "task_count": 120, "unique_sample_run_ids": 60,
  "unique_seeds": 60, "binary_sha_ok": true, "config_sha_ok": true, "elf_ok": true,
  "pairing_ok": true …
READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES
$ ls /tmp/lsu-audit-nonexistent-outbase
ls: cannot access '…': No such file or directory     (dry run wrote nothing)
```

All 12 model→workload ELF checks show `observed == expected` for all 9 workloads (matching `campaign_identity.json`). Transformed scripts verify: `sha256sum -c .repro/transformed.sha256` → all 成功.

**Caveat the reports should carry more loudly (the repro report is technically honest but understated):** the clone's 1.1 GB `build/ARM/gem5.opt` is **not** fetched from the remote branch — it is untracked and git-ignored in the clone (`git rev-parse HEAD:build/ARM/gem5.opt` fails; `.git` is only 349 MB). It was locally supplied and hash-verified (`62e1b1be`). So the dry run proves the *frozen binary's hash and compatibility with the frozen matrix*, not remote availability of the binary. A fresh cloner cannot obtain the frozen binary from GitHub; binary preservation rests on the archive byte copy (and the 4 on-disk worktree copies). The reproducibility report's "No byte-identical rebuild is claimed" covers this, but it does not explicitly say the binary is not on the remote.

## Check 6 — Independent regeneration vs archive: **PASS** (every claim reproduced; no blanket "identical" accepted)

I first proved the clone's raw data equals the archive: `sha256sum --quiet -c SHA256SUMS.raw_runs` inside the clone's campaign root → exit 0 (all 2193 entries). I then ran my **own** full regeneration chain (collector → propagation → trace closure → control proof → workbook → evidence audit), with outputs only under `/tmp/lsu-audit-regen/`, using my own collector output as the control-proof input — i.e., not trusting any file the repro agent wrote.

| Output | Archive vs my regen |
|---|---|
| `LSU_60Context_Causal_Propagation_Final.csv` | **byte-identical** (`d5b63c18…`) |
| `LSU_60Context_Final_Readiness.csv` | **byte-identical** (`421b010d…`) |
| `LSU_11Context_Repair_Validation.csv` | **byte-identical** (`c09c266c…`) |
| `LSU_Control_Audit_Formal.csv` | **byte-identical** (`a703b2ba…`) |
| `LSU_Evidence_Completeness_Audit.csv` | **byte-identical** (`b2d159fe…`) |
| `LSU_A03_Injection_Count_Semantics.csv` | **byte-identical** (`a2b95e5c…`) |
| `collector_full/LSU_60Context_Final_Readiness.csv` | **byte-identical** (`9146a161…`) |
| `collector_full/LSU_120Run_Campaign_Manifest.csv` | **path-normalized-identical**: field-by-field CSV comparison after mapping both checkout roots to `ROOT` → 121 rows × all columns, **0 differing rows/fields** |
| `collector_full/LSU_60Fault_60Control_Pair_Map.csv` | **path-normalized-identical** |
| `collector_full/LSU_Control_Zero_Proof_Final.csv` | **path-normalized-identical** |
| `LSU_Final_Experiment_Config.xlsx` (8 sheets) | **cell-identical after path normalization**: openpyxl cell-by-cell, 8723 cells, **0 differences**; sheet names/order equal; binary differs (zip timestamps), as the report states |
| `collector_full/LSU_Formal_Experiment_Config_Final.xlsx` (5 sheets) | **cell-identical after path normalization**: 7056 cells, **0 differences** |

My SHA-256 prefixes equal the exact values quoted in the reproducibility report §10 — the report's "byte-identical" claims are precise, not approximate. Readiness distribution reproduced: `COMPLETE_CAUSAL_CHAIN=38, VALID_TERMINAL_CHAIN=12, QUALIFIED=5, TRACE_INCOMPLETE=5`; control audit 60/60 `ControlInjected=NO`; `zero_injection_proven=60`. As a determinism cross-check, my 7 regen CSVs are also **byte-identical to the repro agent's in-clone regenerated files**, so the agent's regen was a genuine rerun, not a copy.

Note on normalization: a naive single-substitution diff of the 120Run manifest "fails" because the archive rows carry the formal-worktree path in the ELF column (run-time provenance, correctly preserved) while my regen carries clone paths there for the Evidence column — after applying both root substitutions to both files, the match is exact. This is precisely "only checkout paths differ".

## Check 7 — Test-suite claim: **PARTIAL** (same as the report's own verdict; the failures are state/path-dependent and pre-existing — reproduced)

Real output (three runs):

```console
# Clone, path-insensitive subset (control_proof, lock_resume, qualified, runner_errors, shell_pipeline, workbook):
145 passed, 1 skipped in 11.39s
# Clone, all 12 v3.3.3 files:
38 failed, 294 passed, 1 skipped in 19.79s
# Original formal worktree, same 12 files (control):
4 failed, 316 passed, 13 errors in 54.91s
```

All three numbers match the reproducibility report §5 **exactly**. Nature of the failures, verified by me:

- The 4 worktree failures are exactly `test_lsu_v333_final_launch_acceptance.py::{test_dry_run_summary_gate_fields, test_dry_run_emits_120_unique_commands, test_dry_run_prints_ready_line_only_when_safe, test_dry_run_does_not_create_the_campaign_dir}` — pre-launch gates asserting `existing_outdir_collisions == 0`; the campaign root now exists in both locations, so they fail identically in both. **State-dependent post-campaign failures, not content regressions.**
- The 13 worktree errors are all `test_lsu_v333_propagation.py` fixture errors (EOFError) — the file is not a clean gate even at the source worktree, as the report states.
- Clone-only failures are path/fixture-dependent, verified on two examples: `test_a03_bare_hex_oracle[1]` fails with `FileNotFoundError: …/lsu-v333-repro-20261113/audit_v3_3_2/runs/A03-R01-fault/stdout.log` (historical v3.3.2 run data exists only on the server, not in the remote branch); the launch-acceptance failures quote `existing_outdir_collisions` directly. The frozen manifest template's embedded formal-worktree `FormalExecutionPath` makes path-comparison tests fail by construction in any other checkout, as the report says.

Conclusion: the test suite is executable but is not a clean reproduction gate; the report carries this limitation honestly, and the data-level checks (my check 6) are the real gate. Worktree cleanliness was unchanged after my runs (0 tracked modifications before and after).

## Check 8 — Dependency-risk audit of cleanup candidates: **PASS** (no candidate is required by the formal experiment)

**Server CSV (`LSU_Server_Cleanup_Candidates.csv`, 104 rows).** Programmatic verification:

```console
RecommendedAction: KEEP 31, KEEP_ACTIVE_WORKTREE 1, KEEP_UNCOMMITTED_CHANGES 10, KEEP_ACTIVE 1,
  KEEP_WITH_PARENT 4, DELETE_CANDIDATE_WORKTREE 25, DELETE_CANDIDATE_RUN_DIR 11,
  DELETE_CANDIDATE 3, DELETE_CANDIDATE_DUPLICATE 12, DELETE_WITH_PARENT 6
Cross-tab (action × NeedsApproval × DependsOnFormalRun): every DELETE-family row is (YES, NO).
DELETE rows violating NeedsApproval!=YES or DependsOnFormalRun!=NO: 0
```

All 57 DELETE-family rows carry `NeedsApproval=YES`, `DependsOnFormalRun=NO` — the invariant holds with zero exceptions. **Every** DELETE and KEEP path (including the wildcard group rows' base paths) still exists on disk — nothing has been deleted.

Dependency audit of each DELETE class (my independent checks):

- **Worktrees (25):** the formal worktree `lsu-platform-v3.2.12` is NOT among them (it is the single `KEEP_ACTIVE_WORKTREE`); nor is the reproduction clone, the current session worktree (`r6-s-w1-continuation-20261101`, `KEEP_ACTIVE`), or any of the 10 KEEP_UNCOMMITTED worktrees. For the 9 candidate worktrees whose branches carry unique-vs-freeze commits (e.g. `r6-chain-checker`, 175), the CSV notes correctly instruct **keeping the branch while removing only the worktree** — I verified `lost` vs the kept-set is 0 for every one of them (below), so no commit is orphaned.
- **Run dirs (11 rows, main repo `runs/lsu/`):** `det, engineering, fs_cpt_boot, golden, guard, __pycache__, r6_a_*, R6_COMPLETE_PROPAGATION_PATHS, r6_* other, r6_p_unit, stale .lock files`. None is the formal campaign root (which lives in the formal worktree and is a KEEP row with `DependsOnFormalRun=YES`). The 10 authoritative registries are all KEEP. No active lock is a candidate: no live `gem5.opt`/`lsu_` process exists (`ps` → empty), and every `*.lock` under `runs/lsu` is zero-byte (`-size +0` count = 0).
- **Duplicates:** the `audit_v3_3_2/binary/gem5.opt.v332-070d68a6` DELETE row is SHA-verified by me — content `62e1b1be…` (the formal binary), hardlink inode 7341432 shared with `build/ARM/gem5.opt` and `audit_v3_3_3/binary/gem5.opt.v333-62e1b1be` (`links=3`), plus the separate-inode `CHAOS/gem5/build/ARM` copy and the archive's distinct-inode copy — deleting that one path loses nothing. Zip-duplicate spot check: agent-worktree `LSU_v3.2.7…zip` = `186e7059…` = the tracked copy in the formal worktree, byte-identical.
- **No source, final_config, campaign data, or other-project path appears in any DELETE row** (the full DELETE path list was reviewed; all 57 are superseded worktrees / pilot run dirs / SHA-proven duplicates / tmp slot dirs inside the gem5-fi-ding tree; the out-of-scope non-LSU branches are all `KEEP_OUT_OF_SCOPE`).

**Branch CSV (`LSU_Git_Branch_Cleanup_Candidates.csv`, 206 rows).** I recomputed Agent D's `lost` measure (commits reachable from the branch but from no kept ref; kept-set = freeze base `7067805d` + `fi-ding` + `origin/fi-ding` + `main` + `origin/main` + both local safety tags + all worktree-checked-out branches) for **every** DELETE-family row and all 8 KEEP_UNIQUE rows:

```console
All 109 DELETE-family rows (35 LOCAL + 38 REMOTE + 36 STALE_TRACKING): lost = 0   (0 exceptions)
KEEP_UNIQUE_UNARCHIVED (8): backup/fi-ding-pre-sync-b34a=23, integration/lsu-xlsx2md-20261019=7,
  r4-6-a06-loadsize=4, r4-6-s10-platformfix=3, r4-6-t08-realwalk=6,
  origin/fix/0202-six-chain-20261026=17, origin/hotfix/observer-tool-identity=1,
  origin/integration/lsu-xlsx2md-20261019=7
```

The 8 KEEP_UNIQUE lost-counts reproduce Agent D's §3 numbers **exactly** (23/7/4/3/6/17/1/7) — these branches really would orphan unarchived commits if deleted, and the 109 delete candidates really orphan nothing. All 10 KEEP_UNCOMMITTED worktrees have real uncommitted content (1–167 paths each); `r6-c-unit-20261102` confirmed with 3 modified CHAOS C++ sources (`CHAOSLSQFwd.cc/.hh`, `lsq_unit.cc`) preserved nowhere else. Minor prose/CSV inconsistency (conservative in both directions): Agent D's §7.5 prose lists `r6-s-w1-continuation` among "10 KEEP_UNCOMMITTED / active" while the CSV's 10 `KEEP_UNCOMMITTED_CHANGES` rows include `r4-8-fsmcc` separately and classify the session worktree `KEEP_ACTIVE` — everything named is KEEP either way; no audit impact.

**Flagged candidates that are actually required: none.** I found no DELETE row the formal experiment depends on.

## Check 9 — No deletion or move has occurred: **PASS**

- Formal worktree evidence all present: campaign root `runs/lsu/formal_v333_final_20261112` (140 entries, matching the archive copy; worktree ZIP re-hashed `cece176a…`, byte-identical to the archive ZIP); all three formal binary copies + `CHAOS/gem5/build/ARM` copy (all `62e1b1be`); `1126e0fd` baseline binary; `final_config` (13 files); `audit_v3_3_1/2/3`, `audit_launch_v333`, `audit_launch_fix_v333` all present.
- Formal worktree tracked tree clean: `git status --porcelain` → 0 `M/A/D/R` lines (33 untracked evidence paths, unchanged after my test runs).
- **No remote branch deleted:** current live remote heads = 72 = Agent D's pre-round 71 + exactly one new branch (`lsu-formal-v3.3.3-frozen`). Comparing every CSV remote-scope row against a live `git ls-remote --heads`: the 52 CSV rows absent from the live remote are precisely Agent D's documented **pre-existing** stale tracking refs (36 LSU-role + 16 non-LSU, branches already gone from origin before this round — that is why they are `DELETE_CANDIDATE_STALE_TRACKING`); zero live-at-inventory branches disappeared. Head mismatches: only the 2 remote-only branches Agent D marked `NOT_TRACKED_LOCALLY` and the out-of-scope `fsu` (its remote head advanced — another project's activity, not an LSU deletion).
- Worktree count grew 38 → 39: the 39th is the freeze worktree `/tmp/lsu-freeze-20261113` (added by Task 6, not a removal). Nothing was moved or removed.

## Check 10 — Preservation warnings: **PASS** (all three statements accurate)

1. **Stale `1126e0fd` provenance file:** `audit_v3_3_3/LSU_Final_Binary_Provenance.md` (2026-11-12 12:07) exists and stamps `1126e0fd1fea…` as "the authority" (lines 19, 63, 77, 84); the authoritative `trace_closure/final_config/LSU_Final_Binary_Provenance.md` stamps `62e1b1be…`/`8309da72…`. The superseded file is preserved, exactly as the preservation report §7 warns.
2. **Mislabeled hardlink:** `audit_v3_3_2/binary/gem5.opt.v332-070d68a6` — I re-hashed it: content is `62e1b1be…` (the v333 formal binary), **not** `070d68a6`; `stat` shows inode 7341432 with `links=3`, the same inode as `build/ARM/gem5.opt` and `audit_v3_3_3/binary/gem5.opt.v333-62e1b1be`. The real v3.3.2 `070d68a6` binary is indeed not preserved under its own name. Report statement accurate.
3. **Main-repo binary:** `/home/sdc/gem5-fi-ding/build/ARM/gem5.opt` re-hashed → `6db026e7ffa1ec3c…` — a different build from the formal `62e1b1be`; "never substitute" is correct, and it is KEEP (canonical regression path), not a deletion candidate.

---

## Report claims I could NOT reproduce verbatim (honesty ledger)

1. **Reproducibility report §6 console output** (wrapper dry run with `collisions=0`, `READY=YES`): not reproducible through the wrapper in the clone's *current* state, because the campaign copy was placed there afterwards and the fail-closed guard now refuses. I reproduced the full gate by invoking the underlying runner with a neutral out-base (identical result, zero writes). This is a sequencing artifact, not a false claim — but the report should have noted that its §6 and §10 snapshots are from different clone states.
2. **The binary is not remote-sourced.** The report's §8 `sha256sum build/ARM/gem5.opt` is true for the clone as *set up*, but the 1.1 GB binary is untracked/ignored in the clone and absent from the remote branch — a fresh clone cannot fetch it. No false statement is made ("No byte-identical rebuild is claimed"), but the archive, not GitHub, is the only source of the frozen binary bytes.
3. **`LSU_Reproducibility_Verification.md` is not yet on the remote branch** (the branch carries docs/manifests/results/repro scripts, but not this file). This matches the frozen-branch report's plan (it is the anticipated tag-commit content) and the preservation report §6's "Remote reproduction: PENDING — filled after Task 7" — listed here so the tag step (Task 8) does not get skipped.
4. **"63/60 split"** (audit-request figure): untraceable — no report claims it and no data count equals it; the verified split is 60/60 (see check 2).
5. Not re-executed (out of scope by instruction): the 120 gem5 experiments; a binary rebuild; the ZIP's internal-file-by-file equivalence to the extracted tree beyond the 2193+22 manifest entries (which all verify).

## Residual risks (for the approval decision)

1. **Binary reproducibility** rests on the archive byte copy (+4 on-disk copies, incl. 3 hardlinks of one inode) — not on the public remote; no rebuild was performed or claimed. `SOURCE_MANIFEST.sha256` (7/7 verified against the worktree sources) + `build/build.log` support a rebuild but it is untested.
2. **No off-host raw-data copy** (explicitly deferred: public repo, needs approval).
3. **Six untracked v3.3.3 launch ZIPs** in the formal worktree root are in no branch; only the Results ZIP is archived (Agent D flagged this — recommend archiving before any cleanup round).
4. **26.58 GB of `runs/lsu` candidate data is unarchived**; deleting it is irreversible (approval-gated; correctly marked).
5. **Test suite is not a clean gate** (documented): 4 state-dependent gate failures + 13 propagation fixture errors exist even at the source worktree.
6. **Remote carries no tags at all**; both R6 safety tags are local-only. Agent D's recommendation to push them before any remote branch deletion remains open, as does the planned `lsu-v3.3.3-formal-accepted` tag.
7. `collector_manifest.stage2-failed-20261113` is preserved stale (marked NON_CANONICAL) — intentional, but anyone using it must respect the marking.

## Final verdict

**ACCEPT — PASS on 9 of 10 checks; check 7 (test-suite gate) PARTIAL, which is the reports' own honest verdict and was fully reproduced.**

The archive is internally consistent and cryptographically intact; the frozen identity chain (ZIP `cece176a`, binary `62e1b1be`, config `8309da72`, campaign `LSU-V333-FINAL-20261112`, zero C++ drift `e3293856`→`7067805d`→frozen branch) was independently re-established, not just re-read. The reproducibility report's specific hash-level claims (7 byte-identical CSVs, 3 normalized-identical CSVs, 2 cell-identical workbooks, 38/12/5/5 readiness, 60/60 zero-injection controls) all reproduced exactly under my own independent regeneration. The cleanup CSVs' two load-bearing invariants — every DELETE row approval-gated and formal-independent (57/57 server rows), and every DELETE branch commit-preserving (109/109 rows, lost=0) — held under complete recomputation, and the 8 KEEP_UNIQUE + 10 KEEP_UNCOMMITTED classifications were independently confirmed. No deletion or move has occurred on server, worktree, or remote. No report claim was found to be false; the overstatement risk is confined to the two presentation nuances in the honesty ledger (dry-run sequencing, binary not remote-fetchable).
