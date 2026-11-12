# LSU v3.3.3 — Final Binary Provenance

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`

## 1. Chain

| Item | Value |
|---|---|
| v3.3.2 baseline HEAD | `3097ad82e7066f18fc35cf64dcb612a05c1fc021` |
| Diagnosis commit | `200e31f5e3523ae730511f93533d59658c2b63a8` |
| A01/A03 source fix | `7a33dc5f` (PRE retry exclusion + A03 in-simulator watchdog) |
| SP05 source fix | `960084dc` (store-data binding + write-skipped node) |
| Control-gate fix | `c66af09f` (probability<=0 true disable; LQ04 gate) |
| Tools/tests commit | `93bca301bdecc99e7a7d9cbc85a5bd80c02cc951` |
| A01 8-byte correction | `b5031bf7d857ca7901810a3bf3629f5649ddaaac` (final source HEAD) |
| Final binary | repo-root `build/ARM/gem5.opt` |
| Binary SHA256 | `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338` |
| Build log | `audit_v3_3_3/build/v333_build2.log` (final correction build; the first build log `v333_build.log` is the pre-correction `685d88f7` build) |
| Build result | `scons: done building targets.`; `error:` count = 0 |
| Source/binary consistency | `git diff --stat HEAD -- CHAOS/gem5/src` empty after the commits |
| Config | `configs/se/lsu_proxy.py` SHA256 `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` (final; matches every final run manifest) |

## 2. Workload ELF SHA256

| Workload | SHA256 |
|---|---|
| `agu_addrmodes` | `90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b` |
| `fw05_forward` | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` |
| `sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| `alignment` | `89ff937a73a01708c5781385e9a9f9740254a456d4f07042b2b480c4677918c0` |
| `load_response` | `3779e8ced41a07d798f78c97a1f5d10187c812a24a81b599c19ae68a0753e711` |
| `lq_lifetime_ordinal` | `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba` |
| `sq_forward_w4v2` | `a08fb3a7b8bbcef76b0c3c3519a5787370ea7ead2d93de290e00fc6e44fe76e2` |
| `replay_partial_v332` | `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42` |
| `md04_violations_v332` | `dd241c3097e61495141e614ce493ba4b2901a7df751baa95e69365bdf8f95c43` |

## 3. Build warnings

The build log contains the same warning set as the v3.3.2 log: `CHAOSCache.cc` `-Wreorder` (pre-existing), and `CHAOSPropagation.cc:990/1171` unused variables (pre-existing). No warning was introduced by the v3.3.3 changes; the counts match `/tmp/v332_build.log`.

## 4. Pre-matrix verification on this binary

| Check | Real result |
|---|---|
| A01-R01 fault | injection=1, `a01_ea_discarded`=0, `register_writeback`=1, terminal SDC, oracle FAIL |
| A01-R01 control | injection=0, `pre_retry_skipped`=22, golden `728e604ffcec539d` |
| SP05-R01 fault | `store_data_fnv=b6180e0c195fd2e9`, `data_correct=0`, `stage_outcome=CHAIN_VISIBILITY_LOST`, `sp05_write_skipped` node, reload hash `a8c7f832281a39c5` |
| A03-R01 fault | `A03_WATCHDOG_EXPIRED` at tick 400,958,635; `A03_STUCK_LIFECYCLE` (activation ordinal 1058, first affected 1059); final checksum `1cf7a5a9f11dab7e` ≠ golden; `SDC / POST_ORACLE_SIM_HANG`; `timed_out=False`; `gzip -t` OK |
| A03-R01 control | injection=0, golden `728e604ffcec539d` |
| Full pytest | 232 passed |
| Platform pytest | 121 passed |

## 5. A01/A03 re-census (approved v3.3.3 change)

- **A03 (size-agnostic persistent fault):** after excluding translation retries, the measured main-loop eligible window is `[1040, 1222]` (N=183); percentile ordinals `1058, 1094, 1131, 1168, 1204`.
- **A01 (final correction, ledger L-A12):** the model targets an 8-byte GPR load; the 16-byte vector load at the old 50% context is excluded. The count-only 8-byte stream has 817 eligible events; the main-loop window is `[585, 713]` (N=129); percentile ordinals `597, 623, 649, 675, 701` (all `size=8`, PCs in `main`). The v3.3.2 window `[1040, 1234]` / N=195 and the pre-correction `[1040, 1222]` / N=183 are history.
SampleRunID and Seed are unchanged.

## 6. Packaging note

The final 1.1 GB binary is preserved as a hardlink at `audit_v3_3_3/binary/gem5.opt.v333-1126e0fd` (SHA verified). The pre-correction `685d88f7` binary was overwritten in place by the correction install and is **not** retained; its 120 runs are archived at `audit_v3_3_3/runs_685d88f7/` and are never mixed with the final set. The final binary is not committed to git; the SHA above is the authority.

---

## 7. Correction build (v3.3.3 final)

The A01 16-byte/vector-load root cause (ledger L-A12) required one correction
cycle: restrict A01 eligibility to 8-byte loads and add a count-only
eligible-stream census mode.

| Item | Value |
|---|---|
| Correction source HEAD | `b5031bf7d857ca7901810a3bf3629f5649ddaaac` |
| Correction build log | `audit_v3_3_3/build/v333_build2.log` |
| Final binary SHA256 | `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338` |
| Source/binary consistency | `git diff --stat HEAD -- CHAOS/gem5/src` empty |
| A01 8-byte census | 817 eligible, main window 585–713 (N=129), ordinals 597/623/649/675/701 |
| A01-R03 correction smoke | injection=1, `register_writeback`=1, commit+errant_commit, oracle FAIL, SDC; control golden |
| Build result | `scons: done building targets.`; `error:` count = 0; no new warning class |
| Pre-correction binary | `685d88f7…`; its 120 runs are archived at `audit_v3_3_3/runs_685d88f7/` (not mixed with the final set) |

The final 120-pair matrix is run on `1126e0fd…`; every row must carry this SHA.
