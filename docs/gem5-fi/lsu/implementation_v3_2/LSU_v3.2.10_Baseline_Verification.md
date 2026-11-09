# LSU v3.2.10 — Baseline Verification (LQ04 round, Task 1)

**Date:** 2026-11-09
**Round:** LSU v3.2.10 (LQ04 — LQEntry lifetime fault)
**Authoritative baseline worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2`
(branch `lsu-platform-v3.2.9`)
**Task worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10`
(branch `lsu-platform-v3.2.10`, started at the baseline commit)
**Binding spec:** `docs/superpowers/specs/2026-11-08-lsu-v3.2.10-lq04-design.md`

This document records the real, re-verified state of the v3.2.9 baseline that the
v3.2.10 LQ04 round builds on. Every command below was re-run on 2026-11-09 and its
real output is quoted. Nothing in this task modified code, the v3.2.9 worktree, or
any of the 12 models' frozen identities.

---

## 1. Verification commands and real output

All commands were run against the authoritative v3.2.9 worktree
(`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2`).

### 1.1 Baseline HEAD and parent

```
$ git rev-parse HEAD
37692d2beffcb73fc9303ad9de4c6bb341d5de71

$ git log -1 --format='parent: %P' 37692d2b
parent: ecf0fdf93f03e33490a409e7eb3345daffc4832e

$ git branch --show-current
lsu-platform-v3.2.9
```

Commit metadata (real output):

```
$ git log -1 --format='%H %ci %s' 37692d2b
37692d2beffcb73fc9303ad9de4c6bb341d5de71 2026-11-08 22:31:49 +0800 [LSU][MDSPEC][V3.2.9][DOCS] refresh provenance after the review fix

$ git log -1 --format='%H %ci %s' ecf0fdf9
ecf0fdf93f03e33490a409e7eb3345daffc4832e 2026-11-08 22:31:35 +0800 [LSU][MDSPEC][V3.2.9][SP05] fix cross-model corruption and unreachable-ordinal selection
```

The parent `ecf0fdf9` is the SP05 code-fix commit; `37692d2b` is the docs-only
provenance refresh on top of it. `git log --oneline -6` at HEAD:

```
37692d2b [LSU][MDSPEC][V3.2.9][DOCS] refresh provenance after the review fix
ecf0fdf9 [LSU][MDSPEC][V3.2.9][SP05] fix cross-model corruption and unreachable-ordinal selection
daf9a298 [LSU][MDSPEC][V3.2.9][DOCS] refresh git provenance to the closeout commit
316f690a [LSU][MDSPEC][V3.2.9][DOCS] check off the plan and add the package README
525be053 [LSU][MDSPEC][V3.2.9][PACKAGE] final report, open issues and git provenance
f38ce587 [LSU][MDSPEC][V3.2.9][DOCS] status report and cross-artifact consistency check
```

### 1.2 Parent → HEAD diff (code unchanged)

```
$ git diff --stat ecf0fdf9..37692d2b
 .../lsu/implementation_v3_2/GIT_COMMIT_v329.txt    |  6 +-
 .../lsu/implementation_v3_2/GIT_DIFF_CODE_v329.txt | 85 +++++++++++++++-------
 .../lsu/implementation_v3_2/GIT_DIFF_STAT_v329.txt | 20 ++---
 .../lsu/implementation_v3_2/GIT_LOG_v329.txt       |  6 +-
 .../lsu/implementation_v3_2/GIT_STATUS_v329.txt    | 14 ++++
 5 files changed, 90 insertions(+), 41 deletions(-)
```

The diff touches **only the five `GIT_*_v329.txt` provenance snapshots** — no
source, config, tool or workload file changes between the SP05 fix commit and the
final v3.2.9 HEAD. The v3.2.10 code baseline is therefore exactly the code state
produced by `ecf0fdf9`.

### 1.3 Final binary identity (both locations)

```
$ sha256sum build/ARM/gem5.opt CHAOS/gem5/build/ARM/gem5.opt
303c610d2dcca81340f0feae58fc449c8550d1daac6ff965a3387efd2189a0c0  build/ARM/gem5.opt
303c610d2dcca81340f0feae58fc449c8550d1daac6ff965a3387efd2189a0c0  CHAOS/gem5/build/ARM/gem5.opt
```

Both the repo-root binary and the vendored-tree binary hash to
`303c610d2dcca81340f0feae58fc449c8550d1daac6ff965a3387efd2189a0c0`. This is the
**final v3.2.9 binary** and is the binary the v3.2.10 round must rebuild from and
re-hash after any code change.

### 1.4 v3.2.9 pytest truth

```
$ grep -E 'passed|failed' docs/gem5-fi/lsu/implementation_v3_2/logs_v3_2_9/pytest_full.log | tail -1
2 failed, 40 passed in 10.73s
```

The two failures (`pytest_full.log:157-158`):

```
FAILED tests/test_claim_concurrency.py::test_d_run_concurrency_cap - Assertio...
FAILED tests/test_claim_concurrency.py::test_e_heartbeat - AssertionError: e_...
```

Both are the **disk guard**, not code defects (`pytest_full.log:102` and `:148`):

```
message = 'task5 异常退出 rc=1: \'"reasons": ["磁盘 free 22.9 GiB < 红线 70.6 GiB (=max(50, 20%×353))"], ...
"disk_free_gib": 22.9, "disk_total_gib": 353.2}, "experiment_slots_occupied": 0, ...\'
E       AssertionError: d_no_fatal: task5 异常退出 rc=1: ...
```

**Recorded truth: 40 passed, 2 failed** (42 tests total; both failures are the
disk-free guard `disk_free_gib: 22.9` vs the 70.6 GiB red line
`max(50, 20%×353)`). The claim in `LSU_v3.2.9_Final_Report.md:49` —
"Full `pytest tests`: 39 passed, 2 failed" — is **wrong** (39+2=41 ≠ 42; the log
summary line says 40 passed). v3.2.10 documents must cite 40/2, not 39/2.

---

## 2. Binary hash reconciliation (stale `d6e60863` → final `303c610d`)

The committed v3.2.9 tree still records the **pre-fix** binary hash
`d6e60863bb63f85398b5aaa35539c0c6c3fdf582e3d969aace27611d5db97b90` in places
where the final binary is meant. Verified evidence:

| Location | Committed (HEAD 37692d2b) | Working tree | Verdict |
|---|---|---|---|
| `docs/gem5-fi/lsu/implementation_v3_2/PACKAGE_README_v3.2.9.md:4` | `d6e60863…` | `303c610d…` | stale in git; fixed only as an **uncommitted** working-tree edit |
| `docs/gem5-fi/lsu/implementation_v3_2/SQ03_Probe_Report_v3.2.9.md:8` | "## Results (final binary d6e60863…)" | same | **stale in both** — still claims d6e60863 is the "final binary" |
| `docs/gem5-fi/lsu/implementation_v3_2/FW05_No_Fault_Baselines_v3.2.8.md:38` | "matched pair on the final v3.2.9 binary (`d6e60863…`)" | same | **stale in both** — same wrong claim |
| `docs/gem5-fi/lsu/implementation_v3_2/SP05_Review_Fixes_v3.2.9.md:13` | "RED (pre-fix binary `d6e60863…`, …)" | same | **correct** — legitimate historical reference to the pre-fix binary |

Real output for the README (committed vs working tree):

```
$ git show HEAD:docs/gem5-fi/lsu/implementation_v3_2/PACKAGE_README_v3.2.9.md | grep -n -E 'd6e60863|303c610d|gem5.opt' | head -1
4:`d6e60863bb63f85398b5aaa35539c0c6c3fdf582e3d969aace27611d5db97b90`.

$ grep -n -E 'd6e60863|303c610d|gem5.opt' docs/gem5-fi/lsu/implementation_v3_2/PACKAGE_README_v3.2.9.md | head -1
4:`303c610d2dcca81340f0feae58fc449c8550d1daac6ff965a3387efd2189a0c0`.
```

Corroboration — the untracked post-commit provenance note
(`docs/gem5-fi/lsu/implementation_v3_2/POST_COMMIT_PROVENANCE_v329.txt`, first
lines):

```
final HEAD: 37692d2beffcb73fc9303ad9de4c6bb341d5de71
base: d5c15309
branch: lsu-platform-v3.2.9
final binary SHA256: 303c610d2dcca81340f0feae58fc449c8550d1daac6ff965a3387efd2189a0c0
package zip SHA256: in the adjacent .sha256 sidecar
```

**Ruling for v3.2.10:** the v3.2.9 final binary is `303c610d…`. The
`d6e60863…` value is the pre-fix binary and must not be cited as the v3.2.9
final binary. The two v3.2.9 docs that still carry the stale "final binary"
phrasing (SQ03_Probe_Report, FW05_No_Fault_Baselines) are recorded here as known
stale references; v3.2.10 does not retro-edit v3.2.9 documents.

---

## 3. Preserved v3.2.9 worktree state (dirty + untracked, no source changes)

`git status --porcelain` in the authoritative v3.2.9 worktree (2026-11-09) shows
**13 modified files** and a set of **untracked** files/dirs. Summary of the real
output:

Modified (all docs/evidence; none under `CHAOS/`, `configs/`, `tools/`,
`workloads/`, `tests/`, `schemas/`):

```
 M docs/gem5-fi/lsu/implementation_v3_2/PACKAGE_README_v3.2.9.md
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R01-off/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R01-on/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R02-off/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R02-on/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R03-off/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R03-on/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R04-off/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R04-on/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R05-off/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R05-on/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_9/SQ03-PROBE-F0-P00/stdout.log
 M docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_9/SQ03-PROBE-F0-P01/stdout.log
```

Untracked (categories): delivery zips and `.sha256` sidecars
(`LSU_v3.2.3…` through `LSU_v3.2.9_SP05_Implementation_SQ03_Propagation_FW05_Closure_Package.zip`),
`POST_COMMIT_PROVENANCE_v329.txt`, run-artifact directories under
`docs/gem5-fi/lsu/implementation_v3_2/{baselines_v3_2_4,evidence_v3_2_8,evidence_v3_2_9,pilots_v3_2_3,…,pilots_v3_2_9}/`
(`config.ini`, `config.json`, `stats.txt`, `prop_trace.csv.gz`,
`trace_v31.jsonl`, `citations.bib`), and scratch dirs `.tmp_lsu_conc/`,
`pilots_v3_2_2/`.

**There are no source modifications.** The dirty state is docs/evidence stdout
logs plus untracked delivery artifacts. This state is **preserved as-is**: no
`git reset --hard`, no `git clean -fd`, no `git add -A` was performed, and none
may be performed on this worktree by the v3.2.10 round.

---

## 4. Worktree topology and source identity

| Worktree | Branch | HEAD | Role |
|---|---|---|---|
| `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2` | `lsu-platform-v3.2.9` | `37692d2beffcb73fc9303ad9de4c6bb341d5de71` | **authoritative v3.2.9 baseline** (final binary, evidence, Excel v3.2.4) |
| `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10` | `lsu-platform-v3.2.10` | `37692d2beffcb73fc9303ad9de4c6bb341d5de71` (at task start) | v3.2.10 task worktree; untracked: the round plan + design spec |
| `/home/sdc/gem5-fi-ding` (main repo) | `fi-ding` | `6f98088a7144d7f6fb22d985be3023ac5658e71b` | main repo — **not** the v3.2.9 branch; its HEAD is the `gem5Commit` value recorded in the Excel v3.2.4 sample rows |

The four audited LSQ source files are **byte-identical** between the v3.2.9
baseline worktree and the v3.2.10 task worktree (both at commit `37692d2b`;
the v3.2.9 worktree has no source modifications):

`sha256sum` was run over all eight paths (each file in both worktrees); every
file pair produced the identical hash:

| File (`CHAOS/gem5/src/cpu/o3/`) | SHA256 (both worktrees) |
|---|---|
| `lsq_unit.hh` | `a95b9513c17252afc3ffdf78c4b67c677e58387a41a6022c7f21ed597a22774c` |
| `lsq_unit.cc` | `d716754b6aee818f64522605cc51d1b356af768a62d732a8cf90486c9e957569` |
| `lsq.hh` | `83d39aa1d9487cf5cc2e2b9956178efc5e1fe1e0545eae19b155707ea32f353c` |
| `lsq.cc` | `94dcac70f34cf0616d4fff6cf7eb772f6b73f2ab96fcd608828077208de78d32` |

The source audit in `LQ04_Source_Audit_v3.2.10.md` therefore applies equally to
both worktrees.

---

## 5. Verdict

| Check | Expected | Observed | Result |
|---|---|---|---|
| Baseline branch/HEAD | `lsu-platform-v3.2.9` @ `37692d2b…` | same | PASS |
| Parent | `ecf0fdf9…` (SP05 fix) | same | PASS |
| Parent→HEAD diff | only 5 `GIT_*_v329.txt` files | same | PASS |
| Final binary (both paths) | `303c610d…` | same | PASS |
| README hash | `d6e60863…` stale (pre-fix) | confirmed; working tree corrected (uncommitted) | PASS (recorded) |
| Dirty state | docs/evidence only, no source mods | confirmed, preserved | PASS |
| pytest | `2 failed, 40 passed`, disk guard 22.9 < 70.6 | confirmed; Final Report's "39 passed" is wrong | PASS (recorded) |

**Baseline verified.** The v3.2.10 round proceeds from commit `37692d2b`
(code state of `ecf0fdf9`), final binary `303c610d…`, with the gate verdict and
decisions frozen in `LQ04_Definition_Freeze_v3.2.10.md`.
