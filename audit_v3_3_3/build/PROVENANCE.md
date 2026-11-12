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
| Tools/tests commit | `93bca301bdecc99e7a7d9cbc85a5bd80c02cc951` (final source HEAD at build time) |
| Final binary | repo-root `build/ARM/gem5.opt` |
| Binary SHA256 | `685d88f77324d8ba75916e577b8bb68947ddf20fc13b51e859cff1cbdc1b8187` |
| Build log | `audit_v3_3_3/build/v333_build.log` |
| Build result | `scons: done building targets.`; `error:` count = 0 |
| Source/binary consistency | `git diff --stat HEAD -- CHAOS/gem5/src` empty after the commits |
| Config | `configs/se/lsu_proxy.py` SHA256 `7fd7e12ded42c319d6e33b14b9df4c0505b65cf9c89219e34bc1197fce3e2a72` |

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
| A03-R01 fault | `A03_WATCHDOG_EXPIRED` at tick 400,963,640; `A03_STUCK_LIFECYCLE` (activation ordinal 1059, first affected 1060); final checksum `32a11657db750fc1` ≠ golden; `SDC / POST_ORACLE_SIM_HANG`; `timed_out=False`; `gzip -t` OK |
| A03-R01 control | injection=0, golden `728e604ffcec539d` |
| Full pytest | 232 passed |
| Platform pytest | 121 passed |

## 5. A01/A03 re-census (approved v3.3.3 change)

After excluding translation retries, the measured main-loop eligible window is `[1040, 1222]` (N=183). The five percentile ordinals are `1058, 1094, 1131, 1168, 1204` (`start + ceil(p*N) - 1`). The A03 per-event stream shows the target PCs in `main` (`0x4005c0`, `0x40068c`, `0x4006a8`, `0x4006d0`, `0x4006d0`). SampleRunID and Seed are unchanged; the v3.3.2 window `[1040, 1234]` / N=195 is retained as history.

## 6. Packaging note

The 1.1 GB binary is preserved as a copy at `audit_v3_3_3/binary/gem5.opt.v333-685d88f7` for the delivery zip. It is not committed to git; the SHA above is the authority.
