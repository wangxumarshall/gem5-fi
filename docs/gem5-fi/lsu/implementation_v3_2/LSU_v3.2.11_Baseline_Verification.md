# LSU v3.2.11 — Baseline Verification (Task 1)

**Date:** 2026-11-09
**Round:** LSU v3.2.11 (LQ04 closure, 11-model propagation audit, RP01 design)
**Authoritative baseline worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10`
(branch `lsu-platform-v3.2.10`, tip `1394fb499d95e604a5c686572943d6a9884393e1`)
**Task worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.11`
(branch `lsu-platform-v3.2.11`, started at the baseline commit)
**Binding spec:** `docs/superpowers/specs/2026-11-09-lsu-v3.2.11-scope.md` (created in this task)
**Implementing plan:** `docs/superpowers/plans/2026-11-09-lsu-v3.2.11.md`

This document records the real, re-verified state of the v3.2.10 baseline that the
v3.2.11 round builds on. Every command below was run on 2026-11-09 from the v3.2.11
worktree (unless a different working directory is stated) and its real output is
quoted verbatim. **No `git reset --hard`, no `git clean -fd`, and no `git add -A`
was run in any worktree during this task**, and none may be run during this round.
Nothing in this task modified code, the v3.2.10 worktree, the main `fi-ding`
worktree, or any of the 12 models' frozen identities.

---

## 1. Task-1 state capture (brief Step 1, verbatim output)

All six commands from the task brief, run from
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.11`:

```
$ git branch --show-current
lsu-platform-v3.2.11

$ git rev-parse HEAD
1394fb499d95e604a5c686572943d6a9884393e1

$ git status --short
?? docs/superpowers/plans/2026-11-09-lsu-v3.2.11.md

$ git log -5 --oneline
1394fb49 [LSU][MDSPEC][V3.2.10][DOCS] record the provenance refresh in the fix-wave report
b327c30c [LSU][MDSPEC][V3.2.10][PACKAGE] refresh provenance after the v3.2.5 consistency fix
e11fbf82 [LSU][MDSPEC][V3.2.10][DOCS] record the v3.2.5 workbook consistency fix in the fix-wave report
0b1cfc22 [LSU][MDSPEC][V3.2.10][DOCS] point the v3.2.9 consistency check at the v3.2.5 workbook
3fa9a1bc [LSU][MDSPEC][V3.2.10][DOCS] close the LQ04 round after the final review and fix wave

$ sha256sum build/ARM/gem5.opt 2>/dev/null || echo "build/ absent in fresh worktree"
build/ absent in fresh worktree

$ df -h /home | tail -1
/dev/mapper/openeuler-home  354G  250G   86G   75% /home
```

Reading of the state:

- The v3.2.11 worktree starts **exactly at the v3.2.10 branch tip**
  `1394fb499d95e604a5c686572943d6a9884393e1` — the same commit as the v3.2.10
  worktree (verified independently in §5).
- The only untracked file at task start is the round plan
  (`docs/superpowers/plans/2026-11-09-lsu-v3.2.11.md`); it is committed together
  with this task's three outputs.
- The fresh worktree has **no `build/` directory** (it is untracked and therefore
  not copied by `git worktree add`). The baseline binary must be restored from the
  v3.2.10 worktree before the Task 5 watchdog build (SDD preflight ruling); see §3.
- Disk: **86 GiB free** on `/home`, above the 70.6 GiB safety threshold (§4).

---

## 2. HEAD reconciliation (delivery record vs branch tip)

The v3.2.10 delivery record `GIT_COMMIT_v3210.txt` records the delivery HEAD as
`e11fbf82…`; the branch tip is `1394fb49…`. The two commits are reconciled by the
following real commands (run from the v3.2.11 worktree):

```
$ git merge-base --is-ancestor e11fbf82d072c63653a30b0dc5200c0b784b478b 1394fb499d95e604a5c686572943d6a9884393e1 && echo "e11fbf82 IS ancestor of 1394fb49"
e11fbf82 IS ancestor of 1394fb49

$ git log --oneline e11fbf82..1394fb49
1394fb49 [LSU][MDSPEC][V3.2.10][DOCS] record the provenance refresh in the fix-wave report
b327c30c [LSU][MDSPEC][V3.2.10][PACKAGE] refresh provenance after the v3.2.5 consistency fix

$ git branch -r --contains 1394fb499d95e604a5c686572943d6a9884393e1
  origin/lsu-platform-v3.2.10

$ git log --oneline origin/lsu-platform-v3.2.10 -1
1394fb49 [LSU][MDSPEC][V3.2.10][DOCS] record the provenance refresh in the fix-wave report
```

Commit metadata (real output):

```
$ git log --format='%H %ci %s' -2 1394fb49
1394fb499d95e604a5c686572943d6a9884393e1 2026-11-09 22:47:02 +0800 [LSU][MDSPEC][V3.2.10][DOCS] record the provenance refresh in the fix-wave report
b327c30cc73bf4b393b6a24a694f24ca5a0082d6 2026-11-09 22:44:15 +0800 [LSU][MDSPEC][V3.2.10][PACKAGE] refresh provenance after the v3.2.5 consistency fix
```

What the two intervening commits changed — provenance/package files only, no
source, config, tool or workload file (full real output):

```
$ git diff --stat e11fbf82..1394fb49
 .../2026-11-08-lsu-v3.2.10-lq04/fix-wave-report.md |  85 +++++++++++++++++++++
 LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip  | Bin 12346387 -> 12358594 bytes
 ...10_LQ04_Implementation_Pilot_Package.zip.sha256 |   2 +-
 .../DELIVERABLES_SHA256_v3210.txt                  |  14 ++--
 .../lsu/implementation_v3_2/GIT_COMMIT_v3210.txt   |  39 ++++++----
 .../implementation_v3_2/GIT_DIFF_CODE_v3210.txt    |  32 ++++++--
 .../implementation_v3_2/GIT_DIFF_STAT_v3210.txt    |   22 +++---
 .../implementation_v3_2/GIT_STATUS_v3210.txt       |   31 ++++----
 8 files changed, 172 insertions(+), 53 deletions(-)
```

**Reconciliation verdict:** the delivery record's `e11fbf82…` is an **ancestor**
of the branch tip; the two later commits `b327c30c` (PACKAGE) and `1394fb49`
(DOCS) are provenance-refresh commits (fix-wave report, re-packed zip, GIT_*
snapshots) that are **already on `origin/lsu-platform-v3.2.10`**. The v3.2.11
round therefore starts from the true remote tip `1394fb499d95e604a5c686572943d6a9884393e1`;
no code changed between `e11fbf82` and `1394fb49`, so the delivery record's code
and binary claims remain valid at the tip. The delivery record itself (head of
`docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v3210.txt`) reads:

```
Package:   LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip
Branch:    lsu-platform-v3.2.10
HEAD:      e11fbf82d072c63653a30b0dc5200c0b784b478b
Base:      37692d2beffcb73fc9303ad9de4c6bb341d5de71
           (lsu-platform-v3.2.9 final closeout; the v3.2.10 round starts
            from this commit)
Commits:   35 (git rev-list --count 37692d2b..HEAD)

Binary SHA256 (gem5 v25.1.0.1, built 2026-11-09 13:36:41):
  build/ARM/gem5.opt                    f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694
  CHAOS/gem5/build/ARM/gem5.opt         f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694
  (both copies identical; every tool invokes the repo-root binary)
```

---

## 3. Baseline binary identity

The v3.2.11 worktree has no `build/` directory, so the baseline binary was
verified **in the authoritative v3.2.10 worktree** (read-only; nothing was
modified there). Real output, run from
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10`:

```
$ sha256sum build/ARM/gem5.opt
f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694  build/ARM/gem5.opt

$ sha256sum CHAOS/gem5/build/ARM/gem5.opt
f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694  CHAOS/gem5/build/ARM/gem5.opt
```

**Baseline binary SHA256 (both copies identical):
`f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694`** — matching
the value recorded in `GIT_COMMIT_v3210.txt`. Every v3.2.11 document that cites
the *baseline* binary cites this value; the *post-watchdog-fix* binary gets its
own new SHA in Task 5, and evidence from the two binaries must never be merged.

**Action carried forward (SDD preflight ruling):** copy `build/` and
`CHAOS/gem5/build/` from the v3.2.10 worktree into the v3.2.11 worktree before
the Task 5 watchdog build, then run incremental `scons -j16` (full rebuild only
if SCons invalidates). Both SHA256 values are recorded in Task 5.

---

## 4. Disk safety check

```
$ df -h /home | tail -1
/dev/mapper/openeuler-home  354G  250G   86G   75% /home
```

**86 GiB free** vs the **70.6 GiB** threshold (the historical red line
`max(50, 20% × 353)` quoted by the platform disk guard; fixed at 70.6 GiB in the
plan's Global Constraints). 86 > 70.6, so runtime work is currently permitted;
the check must be re-run before the Task 5 watchdog smoke, and if free space has
dropped below the threshold the runtime part is skipped and `RUNTIME_NOT_VERIFIED`
recorded.

---

## 5. Worktree topology and preservation

```
$ git worktree list | grep -E "lsu-platform-v3.2.10|lsu-platform-v3.2.11|/home/sdc/gem5-fi-ding "
/home/sdc/gem5-fi-ding                                                  6f98088a [fi-ding]
/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10           1394fb49 [lsu-platform-v3.2.10]
/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.11           1394fb49 [lsu-platform-v3.2.11]
```

| Worktree | Branch | HEAD | Role | State (2026-11-09) |
|---|---|---|---|---|
| `.claude/worktrees/lsu-platform-v3.2.10` | `lsu-platform-v3.2.10` | `1394fb49…` | **authoritative v3.2.10 baseline** (final binary `f3c2a442…`, pilots, Excel v3.2.5) | only `?? .tmp_lsu_conc/` untracked (672 KB) — verified below, preserved as-is |
| `.claude/worktrees/lsu-platform-v3.2.11` | `lsu-platform-v3.2.11` | `1394fb49…` (at task start) | v3.2.11 task worktree | only the untracked round plan at task start; no `build/` |
| `/home/sdc/gem5-fi-ding` (main repo) | `fi-ding` | `6f98088a…` | main repo, **not** an LSU branch | 265 pre-existing deletions/untracked entries — unrelated to this round, untouched |

### 5.1 v3.2.10 worktree state (preserved)

Real output, run from `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10`:

```
$ git status --short
?? .tmp_lsu_conc/

$ du -sh .tmp_lsu_conc
672K	.tmp_lsu_conc
```

The v3.2.10 worktree is clean apart from the 672 KB scratch directory
`.tmp_lsu_conc/`. It is left exactly as found.

### 5.2 Main `fi-ding` worktree state (untouched)

Real output, run from `/home/sdc/gem5-fi-ding` (read-only):

```
$ git branch --show-current
fi-ding

$ git rev-parse HEAD
6f98088a7144d7f6fb22d985be3023ac5658e71b

$ git status --short | wc -l
265
```

The 265 entries are pre-existing deletions (e.g.
` D docs/gem5-fi/lsu/evidence/P0/…`, ` D docs/gem5-fi/lsu/evidence/P1/det/…`) and
untracked files that predate this round. **They are unrelated to the v3.2.11
round and were not touched, staged, restored or deleted.** This status is
recorded here so that any later claim of "the main repo was dirty" is attributed
correctly.

### 5.3 Preservation statement

During Task 1 no write operation of any kind was performed outside the v3.2.11
worktree, and inside it only the four files committed by this task were created.
**No `git reset --hard`, no `git clean -fd`, and no `git add -A` was run** — in
this worktree, the v3.2.10 worktree, or the main repo — and the round's Global
Constraints forbid them for every later task. Historical pilot artifacts
(`pilots_v3_2_*`), SampleRunIDs, Seeds and the 60-row identity block are frozen.

---

## 6. Pilot-evidence map (verified inventory at plan time)

The verified inventory of authoritative pilot sets and raw-trace locations for
all 11 audited models (copied from the plan; this is the input contract for
Tasks 8–21):

| Model | Authoritative pilot set | Raw trace location | Notes |
|---|---|---|---|
| A01 | `pilots_v3_2_1/A01-R01..R05`, re-runs `pilots_v3_2_2/A01-R01,R03` | in-tree | v3.2.1 traces mostly small; re-runs carry full traces |
| A03 | `pilots_v3_2_1/A03-R01..R05`, re-run `pilots_v3_2_2/A03-R01` | in-tree | CRASH ×5 in old matrix |
| FW02 | `pilots_v3_2_1/FW02-R01,R04,R05`, `pilots_v3_2_4/FW02-R01,R05` | in-tree | v3.2.4 traces ~5.9 MB each |
| SQ01 | `pilots_v3_2_3/SQ01-R01..R05`, `pilots_v3_2_4/SQ01-R01..R05` | `LSU_v3.2.3_Propagation_Closure_Package.zip` (worktree `lsu-platform-v3.2`) | in-tree dirs keep `trace_v31.jsonl.sha256` only |
| DA04 | `pilots_v3_2_6/DA04-R04,R05` (authoritative), `pilots_v3_2_4/DA04-R01..R05` | in-tree | 20–34 MB each |
| LP01 | `pilots_v3_2_6/LP01-R01..R05` | in-tree | 43 MB each |
| MD04 | `pilots_v3_2_6/MD04-R01..R05` | in-tree | 26–27 MB each; v3.2.7 dirs are meta-only |
| FW05 | `pilots_v3_2_7/FW05-R01..R05` | `LSU_v3.2.7_MD04_Config_Freeze_FW05_Implementation_Package.zip` (v3.2.10 worktree root) | 39 MB JSONL each in the zip |
| SQ03 | `pilots_v3_2_8/SQ03-R01..R05` | `LSU_v3.2.8_FW05_ConfigFreeze_SQ03_Pilot_Package.zip` (`/tmp` and `lsu-platform-v3.2` root) | 196 MB each |
| SP05 | `LSU_v3.2.9_..._Package.zip` → `A_SP05/pilots/SP05-R01..R05` | same zip | 92 MB each; in-tree only `SP05_v329_EVIDENCE.csv` |
| LQ04 | `pilots_v3_2_10/LQ04-R01..R05` + `LQ04-CONTROL-R01..R05` | in-tree | 17 MB each |

Rules attached to this inventory (frozen for the round): extraction of archived
traces goes only into `implementation_v3_2/audit_v3_2_11/extracted_evidence/`,
never over `pilots_v3_2_*`; every extracted `trace_v31.jsonl` is hash-verified
against the recorded checksums; a hash mismatch marks that pilot
`missing=HASH_MISMATCH`.

---

## 7. Verdict

| Check | Expected | Observed | Result |
|---|---|---|---|
| Task worktree branch | `lsu-platform-v3.2.11` | same | PASS |
| Baseline HEAD | `1394fb499d95e604a5c686572943d6a9884393e1` (v3.2.10 tip) | same, in both worktrees | PASS |
| Delivery-record reconciliation | `e11fbf82…` ancestor; `b327c30c`, `1394fb49` on origin | confirmed (merge-base + `branch -r --contains`) | PASS |
| Intervening commits | docs/package provenance only | 8 files: fix-wave report, zip + sha256, 5 `GIT_*_v3210.txt`; no source | PASS |
| Baseline binary | `f3c2a442…` (both copies) | verified at v3.2.10 worktree, matches `GIT_COMMIT_v3210.txt` | PASS |
| `build/` in v3.2.11 worktree | absent (fresh worktree) | absent; restore before Task 5 (ruling recorded) | PASS (recorded) |
| Disk | ≥ 70.6 GiB free | 86 GiB free | PASS |
| v3.2.10 worktree | only `?? .tmp_lsu_conc/` (672 KB) | confirmed, preserved | PASS |
| Main `fi-ding` repo | pre-existing dirt untouched | 265 entries, untouched | PASS (recorded) |
| Destructive git ops | none | none run; forbidden for the round | PASS |

**Baseline verified.** The v3.2.11 round proceeds from commit
`1394fb499d95e604a5c686572943d6a9884393e1` (identical code state to the delivery
record `e11fbf82…`), baseline binary `f3c2a442…`, with the scope frozen in
`docs/superpowers/specs/2026-11-09-lsu-v3.2.11-scope.md` and the git baseline
recorded in `GIT_BASELINE_v3211.txt`.
