# LSU v3.3.3 — Final Binary Provenance (Trace Closure / Final Launch)

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**C++ source content commit:** `e3293856` (unchanged; verified `git diff e3293856..HEAD -- CHAOS/gem5/src` empty)
**Campaign ID:** `LSU-V333-FINAL-20261112`
**Campaign root:** `runs/lsu/formal_v333_final_20261112`

## 1. Executable actually used by the runner

The runner resolves `GEM5 = ROOT/build/ARM/gem5.opt` where `ROOT` is the
**worktree** root. Measured on 2026-11-12:

```console
$ sha256sum build/ARM/gem5.opt
62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd  build/ARM/gem5.opt
$ stat -c '%s bytes' build/ARM/gem5.opt
1149269352 bytes
```

This is the trace-closure build frozen for the formal campaign. It is
hard-linked at `audit_v3_3_3/binary/gem5.opt.v333-62e1b1be` (same inode and
SHA256). The superseded pre-trace-closure build is archived read-only at
`audit_v3_3_3/trace_closure/baseline/gem5.opt.v333-old-<superseded-sha>`;
its SHA is recorded in that directory's build log, and it must not be used.

**Do not use** the main-repo binary
`/home/sdc/gem5-fi-ding/build/ARM/gem5.opt`: it is a different build
(`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`,
dated 2026-10-30) and would fail the runner's preflight SHA gate. The formal
campaign must be launched from this worktree.

## 2. Config

```console
$ sha256sum configs/se/lsu_proxy.py
8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225  configs/se/lsu_proxy.py
```

The runner's `CONFIG` is `configs/se/lsu_proxy.py`. `configs/se/ooo_proxy.py`
is a different file and is not the formal campaign config.

## 3. Workload ELF SHA256 (frozen table)

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

`tools/lsu_v333_provenance.py` recomputes every hash from the bytes and checks
`FormalExecutionPath == resolve_workload(model)`. The runner writes
`campaign_identity.json` at the campaign root before the first task; the
collector cross-checks every canonical `attempt.json`/`campaign.json` against
it.

## 4. Source/binary consistency

```console
$ git diff --stat e3293856..HEAD -- CHAOS/gem5/src | wc -l
0
```

No C++ file changed between the build's source content commit and the current
HEAD. No `scons` invocation was made in this round; the binary was not
rebuilt. Simulation semantics, workloads, seeds, SampleRunIDs, ROI ordinals,
dynamic-context selection and Fault/Control pairing are unchanged.

## 5. Identity freeze

- 12 models / 5 contexts / 60 `SampleRunID` / 60 seeds read from
  `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv`.
- ROI ordinals read from the frozen mapping; no ID, seed, ROI or workload was
  changed.
