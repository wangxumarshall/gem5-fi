# LSU v3.3.3 — Provenance Chain

This file separates the identities that must never be conflated: the C++ source content commit, the final tooling commit, the archive tag commit, the archive branch HEAD, and the binary bytes.

## 1. Commit chain

| Field | Value | Meaning |
|---|---|---|
| `round_baseline` | `78ac9ba730afb5bf9a5714568a8b8fa197cf0bbb` | Start of the trace-closure round. |
| `build_source_commit` | `e329385616ba6c5f13bf44bc019e829d27e0c81f` | Commit whose **C++ tree content** is identical to the working tree used for the build. The build ran from that working tree before the commit was created. |
| `audited_source_head` | `3d37218d` | HEAD independently audited by Agent E. `git diff e3293856..3d37218d -- CHAOS/gem5/src` is empty. |
| `final_cpp_source_commit` | `e3293856` | Final C++ content. No C++ change after it. |
| `metadata_freeze_head` | `db14c143` | Metadata-only HEAD (provenance/checksums/runbook); no C++ change. |
| `final_tooling_commit` | `7067805d9d24b185872cc06e3768a1e4dc5fa475` | Final campaign tooling/docs; **this archive's base**. 24 commits after `e3293856`, none under `CHAOS/gem5/src`. |
| `archive_tag_commit` | created by this round (annotated tag `lsu-v3.3.3-formal-accepted`) | Tag on the archive HEAD after reproduction evidence is added. |
| `archive_branch_head` | created by this round (`lsu-formal-v3.3.3-frozen`) | May be one docs-only commit ahead of the tag; see the tag message. |

Verified at preservation time:

```console
$ git merge-base --is-ancestor e3293856 7067805d && echo YES
YES
$ git diff --stat e3293856 7067805d -- CHAOS/gem5/src | wc -l
0
$ git diff --stat 7067805d -- CHAOS/gem5/src | wc -l
0
$ git status --porcelain --untracked-files=no | wc -l
0
```

The 24 commits between `e3293856` and `7067805d` touch `tests/`, `audit_v3_3_3/`, `tools/`, `audit_launch_fix_v333/`, `docs/`, and two ZIPs — never `CHAOS/` or `configs/`.

## 2. Frozen bytes

| Item | SHA256 | Size |
|---|---|---|
| `build/ARM/gem5.opt` | `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd` | 1,149,269,352 B |
| `configs/se/lsu_proxy.py` | `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` | 68,993 B |
| Results ZIP | `cece176a894edf139209c21fd219d031f4c0ea99a60cc2664addd743ac2df235` | 400,982,936 B |
| `SOURCE_MANIFEST.sha256` | `d1248447d84d5e531f52b6853113bb79901f776e40b4bde0beedaa54eb5b730d` | 770 B |

The binary is preserved as a **real byte copy** in `/home/sdc/lsu-v333-archive/binary/gem5.opt.v333-62e1b1be` (distinct inode; not a hardlink). The worktree copy may be hardlinked to other names; the archive copy is authoritative.

## 3. Build evidence

From `audit_v3_3_3/trace_closure/final_config/LSU_Final_Binary_Provenance.md` and the archived build log:

- C++ edits (`CHAOSPropagation.cc`, `CHAOSLSQFwd.cc`, `lsq_unit.cc`) are older than the build log; the build log is `2026-11-12 21:20:22`, the installed binary `2026-11-12 21:33:13`.
- The build log contains `[LINK] -> ARM/gem5.opt` and `scons: done building targets.`, with no new warning class.
- `audit_v3_3_3/trace_closure/baseline/build.log` (SHA `1004b780…`, 1,188 lines) is an **incremental SCons build**, not a from-scratch reproducible build.
- **No rebuild was performed in this preservation round.** No byte-identical rebuild is claimed; `date.cc` and link ordering can differ.

## 4. Source closure

`audit_v3_3_3/trace_closure/final_config/SOURCE_MANIFEST.sha256` records the seven changed C++ files at `e3293856`:

- `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` / `.hh`
- `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc` / `.hh`
- `CHAOS/gem5/src/cpu/o3/lsq.cc` / `lsq.hh` / `lsq_unit.cc`

All seven verify against the working tree and against `git show e3293856:<path>`. See `LSU_Formal_Source_Closure_Manifest.csv`.

## 5. Workload identity

The nine executed ELF SHA256 values are frozen in `campaign_identity.json` and in `LSU_Final_Binary_Provenance.md`:

| Workload | SHA256 |
|---|---|
| `agu_addrmodes` | `90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b` |
| `alignment` | `89ff937a73a01708c5781385e9a9f9740254a456d4f07042b2b480c4677918c0` |
| `fw05_forward` | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` |
| `load_response` | `3779e8ced41a07d798f78c97a1f5d10187c812a24a81b599c19ae68a0753e711` |
| `lq_lifetime_ordinal` | `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba` |
| `md04_violations_v332` | `dd241c3097e61495141e614ce493ba4b2901a7df751baa95e69365bdf8f95c43` |
| `replay_partial_v332` | `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42` |
| `sq_forward_w4v2` | `a08fb3a7b8bbcef76b0c3c3519a5787370ea7ead2d93de290e00fc6e44fe76e2` |
| `sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |

`fw05_forward` has its source and ELF but no compile script in the tree; this is recorded honestly, not guessed.

## 6. Authoritative vs superseded provenance

| File | Binary hash | Status |
|---|---|---|
| `audit_v3_3_3/trace_closure/final_config/LSU_Final_Binary_Provenance.md` | `62e1b1be…` | **AUTHORITATIVE** |
| `audit_v3_3_3/LSU_Final_Binary_Provenance.md` | `1126e0fd…` | **SUPERSEDED** (pre-trace-closure; do not delete, do not trust) |
| `audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md` | `62e1b1be…` | authorisation copy |

The stale file is retained because it documents the pre-closure campaign state; it must never be cited as the formal binary identity.

## 7. Mislabeled artifact

`audit_v3_3_2/binary/gem5.opt.v332-070d68a6` shares an inode with the formal binary and its content is `62e1b1be…`. The `v332`/`070d68a6` name is misleading. The actual v3.3.2 `070d68a6` binary is **not** preserved under its own name. Do not delete or rely on the name; verify content by SHA.
