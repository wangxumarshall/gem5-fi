# LSU v3.3.3 — Proposed Deletion Plan (approval required)

**Status: NOT EXECUTED.** No deletion, move, prune, or remote branch operation has been performed. This document is the request for approval.

The machine-readable inventory is `LSU_Git_Branch_Cleanup_Candidates.csv` and `LSU_Server_Cleanup_Candidates.csv`. Every deletion row carries `NeedsApproval=YES`; every server deletion row carries `DependsOnFormalRun=NO`.

## Approval gates (all must hold before any deletion)

1. `lsu-formal-v3.3.3-frozen` is pushed and visible on origin.
2. `lsu-v3.3.3-formal-accepted` tag is pushed and visible on origin.
3. `LSU_Reproducibility_Verification.md` reports PASS on all ten checks.
4. The archive ZIP `cece176a…` and binary `62e1b1be…` verify from `/home/sdc/lsu-v333-archive/`.
5. The researcher signs the approval block below, listing every approved phase.

## Phase D1 — prune stale remote-tracking refs (local metadata only)

- Count: **36** refs under `refs/remotes/origin/*` whose upstream branch no longer exists on origin (36 LSU-role; verified by comparing `git ls-remote --heads` to local tracking refs).
- Action: `git remote prune origin` (no remote branch is deleted; only local stale tracking metadata).
- Evidence: `LSU_Git_Branch_Cleanup_Candidates.csv` rows with `SuggestedAction=DELETE_CANDIDATE_STALE_TRACKING`.
- Risk: low; re-fetch recreates tracking refs for live branches.

## Phase D2 — delete superseded **remote** LSU branches

- Count: **38** live remote branches, each fully contained in the freeze base `7067805d` or `origin/fi-ding` (verified per row with `git rev-list --count <branch> --not 7067805d` and `--not origin/fi-ding`).
- Rule: **one exact branch per command; no wildcard; no force.**
- Command template (repeat per approved row, never a glob):
  ```bash
  git push origin --delete <exact-branch-name>
  ```
- Pre-check per branch: `git rev-list --count <branch> --not 7067805d --not origin/fi-ding --not origin/main --not main` must be `0`.
- Stop immediately if any branch's count is non-zero; remove it from the batch and report.

## Phase D3 — delete superseded **local** LSU branches

- Count: **35** local branches, each fully contained in the freeze base or `origin/fi-ding`.
- Rule: use `git branch -d` (safe delete), never `-D`. If `-d` refuses, the branch is not fully merged — stop and report.
- Command template:
  ```bash
  git branch -d <exact-local-branch-name>
  ```

## Phase D4 — remove 25 superseded worktrees

- Count: **25** registered worktrees, total **24,516,427,498 B (22.83 GiB)**, all clean or containing only transient `.tmp_lsu_conc` output; none is the formal worktree or the current session worktree.
- Rule: `git worktree remove <exact-path>` only after confirming `git status --porcelain` is empty. If dirty, stop; do not use `--force`.
- **Keep 10 worktrees with uncommitted content** (13,897,399,025 B): removing them would destroy changes that exist nowhere else. Keep their branches even if the worktree is later cleaned.
- Keep the branches of the 9 `r6-*` worktrees with 175–470 commits not in freeze/origin-fi-ding.

## Phase D5 — delete historical pilot/run directories

- Count: **11 inventory rows**, **26,580,350,476 B (24.76 GiB)**, including `runs/lsu/r6_p_unit` (15.1 GB) and the `r6_a_*` census/pilot trees (9.25 GB).
- **Warning: this raw data is not archived anywhere.** The verdicts are committed in git docs, but the raw traces are not. Deletion is permanent.
- Candidate only after the researcher confirms these R4/R6 pilot rounds are not needed for any paper, rebuttal, or follow-up analysis.

## Phase D6 — delete the SHA-proven duplicate formal binary

- Count: **1 file**, `audit_v3_3_2/binary/gem5.opt.v332-070d68a6`, 1,149,269,352 B.
- Its SHA256 is `62e1b1be…` — it is a duplicate of the formal binary under a misleading `v332` name. The formal binary is preserved in the archive and in the formal worktree; the pre-closure `1126e0fd` binary is separately preserved under `audit_v3_3_3/trace_closure/baseline/`.
- Delete only after re-verifying both preserved copies.

## Explicit DO-NOT-DELETE list

- `fi-ding`, `main`, `origin/fi-ding`, `origin/main` — public baselines.
- `lsu-v3.3.1-context-workload-20261111` (local + remote) — freeze base, head `7067805d`.
- `lsu-formal-v3.3.3-frozen` and tag `lsu-v3.3.3-formal-accepted`.
- All 36 branches checked out in registered worktrees.
- The 8 branches with unique unarchived commits (`KEEP_UNIQUE_UNARCHIVED`).
- `origin/r6-gate` (kept because a local safety tag references it).
- The formal worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` and its `audit_v3_3_1/2/3`, campaign root, formal binary, `final_config/`.
- `/home/sdc/lsu-v333-archive/` — the preserved archive itself.
- Any non-LSU/other-project/MMU worktree or file.
- All active lock files and the current session worktree.
- `audit_v3_3_2/binary/gem5.opt.v331-d3807fbe` (unique) and `audit_v3_3_3/trace_closure/baseline/gem5.opt.v333-old-1126e0fd` (pre-closure evidence).

## Summary

| Phase | Items | Size | Reversible? |
|---|---|---|---|
| D1 stale tracking prune | 36 refs | metadata | yes (re-fetch) |
| D2 remote branch deletion | 38 branches | metadata | no (re-push possible only if refs preserved locally) |
| D3 local branch deletion | 35 branches | metadata | no (reflog short-term) |
| D4 worktree removal | 25 worktrees | 24.52 GB | no (data not archived) |
| D5 run-dir deletion | 11 groups | 26.58 GB | **no (raw pilot data unarchived)** |
| D6 duplicate binary | 1 file | 1.15 GB | yes (archive copy) |
| **Total server space** | | **52,247,674,557 B (48.66 GiB)** | |

## Approval block

> I approve Phase(s): ______ (list D1–D6 explicitly).
> I understand D4 and D5 are irreversible and their data is not archived.
> Signed: ____________________  Date: __________
