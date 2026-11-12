# LSU v3.3.3 Final Binary Provenance (Freeze Reconciliation)

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`

## 1. Commit fields (corrected semantics)

| Field | Value | Meaning |
|---|---|---|
| `baseline_source_commit` | `78ac9ba730afb5bf9a5714568a8b8fa197cf0bbb` | Start of the trace-closure round. |
| `build_source_commit` | `e3293856` | Commit whose **tree content** is identical to the working tree used for the build. The build itself ran from that working tree before the commit was created. |
| `audited_source_head` | `3d37218d` | HEAD audited by independent Agent E. `git diff e3293856..3d37218d -- CHAOS/gem5/src` is empty. |
| `final_cpp_source_commit` | `e3293856` | Commit whose tree contains the final C++ source content. No C++ change after it. |
| `metadata_freeze_head` | `db14c143` | Metadata-only HEAD (provenance/checksums/runbook); `git diff e3293856..db14c143 -- CHAOS/gem5/src` is empty. |
| `git_status_at_freeze` | tracked tree clean | `git status --porcelain --untracked-files=no` is empty. |
| `final_binary_sha256` | `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd` | Measured `sha256sum build/ARM/gem5.opt`. |
| `config_sha256` | `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` | Measured `sha256sum configs/se/lsu_proxy.py` (unchanged). |

**The old “HEAD at generation = 78ac9ba7” line was misleading**: `78ac9ba7` is the round
baseline, not the build/source commit. The binary was built from the working tree whose C++
content was committed as `e3293856`; `db14c143` is the metadata-freeze HEAD; the final C++ content commit is `e3293856`.

## 2. Build evidence (no rebuild this round)

```console
$ stat -c '%y %n' CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc \
    CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc CHAOS/gem5/src/cpu/o3/lsq_unit.cc
2026-11-12 21:06:25 .../CHAOSPropagation.cc
2026-11-12 21:13:31 .../CHAOSLSQFwd.cc
2026-11-12 21:07:00 .../lsq_unit.cc

$ stat -c '%y %n' audit_v3_3_3/trace_closure/baseline/build.log
2026-11-12 21:20:22 .../build.log

$ stat -c '%y %s %n' CHAOS/gem5/build/ARM/gem5.opt build/ARM/gem5.opt
2026-11-12 21:20:16 1149269352 CHAOS/gem5/build/ARM/gem5.opt
2026-11-12 21:33:13 1149269352 build/ARM/gem5.opt

$ sha256sum CHAOS/gem5/build/ARM/gem5.opt build/ARM/gem5.opt
62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd  CHAOS/gem5/build/ARM/gem5.opt
62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd  build/ARM/gem5.opt
```

The build log (`audit_v3_3_3/trace_closure/baseline/build.log`) contains:

```
[     CXX] src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc -> ARM/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.o
[     CXX] src/cpu/o3/lsq_unit.cc -> ARM/cpu/o3/lsq_unit.o
[     CXX] src/cpu/o3/lsq.cc -> ARM/cpu/o3/lsq.o
[     CXX] src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc -> ARM/cpu/o3/CHAOSPropagation/CHAOSPropagation.o
scons: done building targets.
```

All C++ edits are older than the build log; the built binary and the installed repo-root
binary are byte-identical (`62e1b1be…`). No C++ edit exists after the build:

```console
$ git diff --stat e3293856..HEAD -- CHAOS/gem5/src
(empty)
$ git diff e3293856..HEAD -- CHAOS/gem5/src | wc -l
0
```

## 3. Consistency verdict

**The final binary is consistent with the audited source content.** The build was made from the
working tree that is content-identical to commit `e3293856`; independent Agent E audited
`3d37218d`; no C++ file changed afterward. This is a **content-and-timeline consistency chain**,
not a reproducible-build attestation (no build-time source snapshot was cryptographically signed).

No recompilation was performed in this freeze round, and the binary was not replaced.

**Do not use** `/home/sdc/gem5-fi-ding/build/ARM/gem5.opt`
(`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`); it is a different build.

## 4. Frozen inputs

| Item | SHA256 |
|---|---|
| `build/ARM/gem5.opt` | `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd` |
| `configs/se/lsu_proxy.py` | `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` |
| `agu_addrmodes` ELF | `90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b` |
| `sq_reload_v3212` ELF | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| `replay_partial_v332` ELF | `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42` |

The full frozen workload table remains in
`audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md`.

## 5. Source-file manifest at freeze

`audit_v3_3_3/trace_closure/final_config/SOURCE_MANIFEST.sha256` records the seven changed C++
files at the final C++ content commit `e3293856` (identical at `db14c143`). It is a post-build content manifest; combined with the mtime/diff
evidence above it pins the audited source state.
