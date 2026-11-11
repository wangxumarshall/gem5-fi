# LSU v3.3.2 — Provenance and Baseline

Date: 2026-11-11 (round start)
Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
Branch: `lsu-v3.3.1-context-workload-20261111`
Base commit: `3504ec23733ad1de550554693a8e10c87a3a81ad`
Base binary: `build/ARM/gem5.opt`
Binary SHA256: `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`

## Resource gate

- `/home` free: 66 GiB (new 20 GiB floor satisfied)
- RAM: 29 GiB total, 25 GiB available
- CPUs: 126; gem5 build uses `-j16`
- gem5 concurrency cap: 4 (this round keeps ≤3 workload probes in flight)

## Inputs (verified on disk)

- `LSU_v3.3.1_Context_Workload_Finalization_Package.zip` (SHA256 in `.sha256`)
- `audit_v3_3_1/` extracted evidence tree
- Frozen workbook: `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`
- Workload sources/ELFs under `docs/gem5-fi/lsu/implementation_v3_2/workloads/` and `workloads/directed/`

## Commands actually run at round start

```
git rev-parse HEAD
sha256sum build/ARM/gem5.opt
df -h .
free -g
nproc
```

## Rules

- Historical evidence keeps its own binary SHA; no cross-binary chain stitching.
- Candidate workloads are not written into the frozen workbook without researcher approval.
- Every later artifact must cite FINAL_HEAD + FINAL_BINARY_SHA.
