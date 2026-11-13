# LSU v3.3.3 — Final Formal Archive (frozen)

**Status:** formal campaign complete and accepted. This branch is the **preservation archive**, not a development branch.

**Campaign:** `LSU-V333-FINAL-20261112` — 12 fault models × 5 dynamic contexts × 2 roles = **120 runs** (60 fault + 60 control).

## Frozen identities

| Identity | Value |
|---|---|
| Formal build source commit (C++ tree content) | `e329385616ba6c5f13bf44bc019e829d27e0c81f` |
| Final tooling commit (campaign tooling/docs; **no C++ drift**) | `7067805d9d24b185872cc06e3768a1e4dc5fa475` |
| Formal binary | `build/ARM/gem5.opt` (not committed) |
| Binary SHA256 | `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd` |
| Config | `configs/se/lsu_proxy.py` |
| Config SHA256 | `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` |
| Campaign ID | `LSU-V333-FINAL-20261112` |
| Results archive ZIP SHA256 | `cece176a894edf139209c21fd219d031f4c0ea99a60cc2664addd743ac2df235` |
| Archive tag | `lsu-v3.3.3-formal-accepted` |
| Archive branch | `lsu-formal-v3.3.3-frozen` |

> **Do not claim this branch HEAD is the binary's build commit.** `e3293856` is the C++ content commit; `7067805d` is the final tooling commit and this archive's base. The archive commits after `7067805d` add documentation/manifests/results only. See `PROVENANCE.md`.

## What this branch contains

- The complete vendored gem5 tree and the 12 LSU fault models (C++ under `CHAOS/gem5/src/`), unchanged from `7067805d`.
- The frozen runner/collector/oracle/propagation/report tooling (`tools/`, `tests/`, `configs/`, `workloads/`).
- `audit_v3_3_3/trace_closure/final_config/`: the authoritative binary provenance, runbook, launch/collect/manifest/report scripts and checksum manifest.
- `docs/lsu/formal-v3.3.3/LSU_Formal_Source_Closure_Manifest.csv`: source/tooling closure.
- `docs/lsu/formal-v3.3.3/LSU_Formal_Workload_Context_Manifest.csv`: 12 models, 60 SampleRunIDs, 60 seeds, ROI/percentile/ordinal evidence, 9 ELF hashes.
- `docs/lsu/formal-v3.3.3/LSU_Formal_Raw_Data_Archive_Manifest.csv`: 120-run index (attempt, file count, hashes, terminal state, identity).
- `docs/lsu/formal-v3.3.3/LSU_Formal_vs_Pilot_Separation.csv`: formal vs historical pilot evidence.
- `docs/lsu/formal-v3.3.3/results/`: the small final result index (Excel, propagation CSV, control audit, oracle summary, acceptance report, campaign index, checksum manifests).
- `docs/lsu/formal-v3.3.3/LSU_Git_Branch_Cleanup_Candidates.csv` and `LSU_Server_Cleanup_Candidates.csv`: **proposals only — nothing deleted**.
- `docs/lsu/formal-v3.3.3/LSU_Proposed_Deletion_Plan.md`: the approval-gated deletion plan.
- `docs/lsu/formal-v3.3.3/repro/`: reproduction wrapper (see below).

## Raw data location

The full 120-run raw archive (traces, attempts, summaries, stdout/stderr, oracle logs, manifests, campaign index, checksums) is **not in git**. It is preserved on the server at:

```
/home/sdc/lsu-v333-archive/
├── raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip      # 400,982,936 B, SHA cece176a…
├── raw_extracted/formal_v333_final_20261112/             # extracted verification copy
├── binary/gem5.opt.v333-62e1b1be                         # 1,149,269,352 B, SHA 62e1b1be…
├── build/build.log
├── config/lsu_proxy.py
├── manifests/{SOURCE_MANIFEST.sha256,final_config/}
├── packages/                                             # v3.3.1–v3.3.3 launch/readiness packages
└── approval/LSU_Final_Cleanup_Approval_Packet.zip
```

Two independent on-host copies exist (the worktree ZIP + this archive ZIP/extracted tree). No off-host copy was made: the GitHub repository is public, so publishing raw experiment data needs explicit researcher approval.

## Reproduction

The frozen shell scripts hardcode `ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`. A fresh clone must use the wrapper, which rewrites `ROOT` at runtime and records the transformed-script hashes; the originals are never edited:

```bash
git clone --branch lsu-formal-v3.3.3-frozen git@github.com:wangxumarshall/gem5-fi.git lsu-repro
bash docs/lsu/formal-v3.3.3/repro/reproduce_from_clone.sh "$PWD/../lsu-repro" /home/sdc/lsu-v333-archive
```

The wrapper verifies the 7-file source manifest, config hash and binary hash, then runs the 120-task dry run. Add `--regen` to rebuild the collector and final reports from the archived raw data (it does **not** rerun the 120 experiments).

## Frozen limitations (carried from the accepted campaign)

- **SP05** R01–R05 remain `QUALIFIED` (frozen `writeback_event` unsatisfiable; real suppressed-writeback evidence retained).
- **RP01** R01–R05 remain `TRACE_INCOMPLETE` (internal-watchdog HANG; terminal metadata complete).
- **A03-R02** is `COMPLETE_CAUSAL_CHAIN`.
- **Trace coverage:** 105 of 120 runs carry `trace_v31.jsonl`; the 15 direct-driver runs (A03 fault R01–R05; RP01 fault and control R01–R05) do not. All 120 carry `prop_trace.csv.gz`. This is a design property of the direct-driver path, not archive loss.
- `collector_manifest.stage2-failed-20261113/` is preserved but marked `NON_CANONICAL`; do not use it as formal evidence.
- Historical Pre-Formal evidence under `audit_v3_3_3/runs/` and `audit_v3_3_3/runs_685d88f7/` is pilot data and is never mixed into the formal set.

## Preservation warnings

- `audit_v3_3_3/LSU_Final_Binary_Provenance.md` (one level above `trace_closure/final_config/`) still records the **pre-closure** binary `1126e0fd…` and must be treated as **superseded**. The authoritative file is `audit_v3_3_3/trace_closure/final_config/LSU_Final_Binary_Provenance.md` (`62e1b1be…`).
- `audit_v3_3_2/binary/gem5.opt.v332-070d68a6` is a hardlink whose content is the **formal v3.3.3 binary** `62e1b1be…`, despite the `v332` name. Do not judge it by name.
- `/home/sdc/gem5-fi-ding/build/ARM/gem5.opt` (`6db026e7…`) is a **different** build. Never substitute it for the formal binary.

## Deletion status

**No file, worktree, branch, or tag was deleted in the preservation round.** All cleanup items are proposals requiring explicit researcher approval; see `LSU_Proposed_Deletion_Plan.md`.
