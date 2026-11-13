# LSU v3.3.3 — GitHub Frozen Branch Report

**Date:** 2026-11-13
**Repository:** `git@github.com:wangxumarshall/gem5-fi.git` (public)
**Push performed:** yes, non-force, new branch.

## Frozen branch

| Field | Value |
|---|---|
| Branch | `lsu-formal-v3.3.3-frozen` |
| Remote | `origin/lsu-formal-v3.3.3-frozen` |
| Remote HEAD at push | `ce6972cfde6a628685dcb7989f3bd0cd416c2a53` |
| Local HEAD at push | `ce6972cfde6a628685dcb7989f3bd0cd416c2a53` |
| Freeze base | `7067805d9d24b185872cc06e3768a1e4dc5fa475` |
| Base tree | `f211528b2c52958ae3eb207535fabe5583e98d46` |
| `CHAOS/gem5/src` subtree at base | `fdcf53f6b0b8427827e1442ada1f94e245584a2b` |
| C++ drift `e3293856..branch` | 0 files under `CHAOS/gem5/src/` |
| Commits added to base | 4 docs/manifest/result/cleanup commits (archive only) |

Push output (real):

```text
 * [new branch]        lsu-formal-v3.3.3-frozen -> lsu-formal-v3.3.3-frozen
分支 'lsu-formal-v3.3.3-frozen' 设置为跟踪 'origin/lsu-formal-v3.3.3-frozen'。
```

Remote verification (real):

```text
ce6972cfde6a628685dcb7989f3bd0cd416c2a53	refs/heads/lsu-formal-v3.3.3-frozen
```

## Commit chain added

| Commit | Subject |
|---|---|
| `e72c055c` | `[LSU][V3.3.3][ARCHIVE] freeze formal source provenance and source closure manifest` |
| `780129bb` | `[LSU][V3.3.3][MANIFEST] freeze 12 models, 60 contexts, 60 seeds and 120-run archive index` |
| `d81f0d0a` | `[LSU][V3.3.3][ARCHIVE] add final result index and acceptance evidence` |
| `ce6972cf` | `[LSU][V3.3.3][CLEANUP] add branch and server deletion candidates (no deletion executed)` |

## Tag

`lsu-v3.3.3-formal-accepted` is created **after** the remote reproduction evidence is added, so its message can state exactly what was verified. The tag commit may be one docs-only commit ahead of the reproduced commit; that commit adds only `LSU_Reproducibility_Verification.md`, `LSU_Archive_SHA256SUMS`, and the updated preservation report.

## Three identities (never conflated)

1. **Formal build source commit:** `e329385616ba6c5f13bf44bc019e829d27e0c81f` — final C++ tree content.
2. **Final tooling commit / archive base:** `7067805d9d24b185872cc06e3768a1e4dc5fa475`.
3. **Binary SHA256:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd` — preserved as a real byte copy in `/home/sdc/lsu-v333-archive/binary/`.

The archive branch HEAD is not the binary's build commit and is not claimed to be.

## Pre-existing remote state (verified before creation)

- `refs/heads/lsu-formal-v3.3.3-frozen`: absent.
- `refs/tags/lsu-v3.3.3-formal-accepted`: absent.
- The remote carries **no tags at all**; both R6 safety tags exist only locally.
- The freeze base `7067805d` is **not** contained in `origin/fi-ding`; it lives on `origin/lsu-v3.3.1-context-workload-20261111` (head `7067805d`).

## Result

The freeze branch is pushed and traceable to the real formal source. No force push, no branch overwrite, and no deletion were performed.
