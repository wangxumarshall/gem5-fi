# LSU v3.3.3 — Final Workload Provenance

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**Tool:** `tools/lsu_v333_provenance.py` (read-only; hashes computed from file bytes)
**Tests:** `tests/test_lsu_v333_provenance.py` — 14 passed

## 1. Three explicit fields

- `WorkloadSourcePath` — canonical source artifact in this worktree. Resolution
  order: `workloads/directed/<name>` (git-tracked build output), then
  `docs/gem5-fi/lsu/implementation_v3_2/workloads/<name>`.
- `FormalExecutionPath` — exactly
  `tools/lsu_v332_matrix.resolve_workload(model, CONTEXTS[model].get("workload"))`.
  This is imported, never re-derived.
- `ELF_SHA256` — the real `sha256` of the bytes at `FormalExecutionPath`.

`ELF` in the manifest template equals `FormalExecutionPath`: it is the only
execution path.

## 2. Model -> path -> SHA (measured 2026-11-12)

| Model | FormalExecutionPath | ELF_SHA256 |
|---|---|---|
| A01 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/agu_addrmodes` | `90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b` |
| A03 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/agu_addrmodes` | `90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b` |
| FW02 | `workloads/directed/sq_forward_w4v2` | `a08fb3a7b8bbcef76b0c3c3519a5787370ea7ead2d93de290e00fc6e44fe76e2` |
| FW05 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/fw05_forward` | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` |
| SQ01 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| SQ03 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| SP05 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| DA04 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/alignment` | `89ff937a73a01708c5781385e9a9f9740254a456d4f07042b2b480c4677918c0` |
| LP01 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/load_response` | `3779e8ced41a07d798f78c97a1f5d10187c812a24a81b599c19ae68a0753e711` |
| MD04 | `workloads/directed/md04_violations_v332` | `dd241c3097e61495141e614ce493ba4b2901a7df751baa95e69365bdf8f95c43` |
| LQ04 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal` | `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba` |
| RP01 | `workloads/directed/replay_partial_v332` | `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42` |

All 12 `MatchesFrozen=True` against the 9-workload frozen table in
`audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md`.
Paths are relative to the worktree root above; none contains `v3.2/`,
`v3.2.10/`, or `archive`.

`WorkloadSourcePath` differs from `FormalExecutionPath` only for A01/A03:
the source build output is `workloads/directed/agu_addrmodes`; the runner
executes the frozen copy `docs/.../workloads/agu_addrmodes`. Both paths hold
the same bytes (`90a19003…`), verified by hashing both files.

## 3. Frozen binary and config (read-only)

```console
$ sha256sum build/ARM/gem5.opt
62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd  build/ARM/gem5.opt
$ sha256sum configs/se/lsu_proxy.py
8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225  configs/se/lsu_proxy.py
```

Both match the launch plan's frozen values. No rebuild was performed.

## 4. Regenerated manifest template

`audit_v3_3_3/trace_closure/final_config/LSU_Final_Campaign_Manifest_Template.csv`

```console
$ python3 audit_v3_3_3/trace_closure/final_config/_generate.py
...
59f32c0c9e0f9f779744690782913f9452fbd9bc8ba09010d502b4e09412dd41  ./LSU_Final_Campaign_Manifest_Template.csv
$ sha256sum -c SHA256SUMS.txt
# all 10 listed files: 成功
```

- 120 data rows; 60 unique `SampleRunID`; 60 unique `Seed`.
- Every SampleRunID has exactly two rows, roles `{fault, control}`, same
  `Seed`, same `ModelID`, same `ContextID` — pairing errors: none.
- New columns present: `WorkloadSourcePath`, `FormalExecutionPath`;
  `ELF_SHA256` refreshed from real bytes; all pre-existing columns kept.
- `ELF` equals `FormalExecutionPath`; `Evidence` is
  `runs/lsu/formal_v333_final_20261112/<ModelID>-<ContextID>-<Role>`.
- Regeneration is idempotent (same template SHA256 on two consecutive runs).

`_generate.py` now imports `tools/lsu_v333_provenance.py`, so the template and
the provenance tool cannot drift. It no longer overwrites the
pipeline-owned `launch_commands_final.sh` when that file already exists.

## 5. Disclosed observations (not hidden)

1. **Stale binary line in the authorization provenance document.**
   `audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md` §1
   still records `1126e0fd…`; the actual `build/ARM/gem5.opt` is `62e1b1be…`
   (trace-closure rebuild). The frozen workload table in that same document is
   correct (all 9 hashes match). The current authority for the binary is the
   launch plan / `final_config/LSU_Final_Binary_Provenance.md`. The
   authorization file was **not** modified.
2. **Old same-basename copy outside the runner roots.**
   `docs/gem5-fi/lsu/final_paper_audit_v3_1/workload_sources/alignment`
   (`755c238b954b4b6faaad285b5f645762e0c91f5fea718843e89fae8168efbba4`)
   differs from the formal `alignment`
   (`89ff937a…`). It is not reachable from `resolve_workload` and is outside
   both runner roots; the duplicate-basename check therefore scopes to the
   two runner roots and the formal execution paths, where no ambiguity exists.
3. **Concurrent-worktree transient.** During one `_generate.py` invocation,
   `tools/lsu_v332_matrix.py` was mid-write by a concurrent agent and failed
   to import (`NameError: contextmanager`); the immediately repeated run
   succeeded. No state from the failed run was written.

## 6. Verification commands (real output quoted above)

```console
$ python3 -m pytest tests/test_lsu_v333_provenance.py -q
14 passed in 1.90s
$ python3 tools/lsu_v333_provenance.py
... all 12 models [ok]; manifest rows=120 SampleRunID=60 seeds=60; binary/config [ok]
PASS: all 12 models resolve to frozen ELF bytes; manifest template consistent
$ sha256sum <9 formal workload paths>   # values identical to §2
```
