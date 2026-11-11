# LSU v3.3.2 — Provenance (final)

Date: 2026-11-11
Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
Branch: `lsu-v3.3.1-context-workload-20261111`

## Baseline (round start)

- Base commit: `3504ec23733ad1de550554693a8e10c87a3a81ad`
- Base binary: `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`
- Backup: `audit_v3_3_2/binary/gem5.opt.v331-d3807fbe` (byte-identical to the v3.3.1 binary)

## Final frozen build

- Source HEAD when the matrix was run:
  `fc60822408cbb3f5af4788bd99fc82c114917367`
- Binary: repo-root `build/ARM/gem5.opt`
- Binary SHA256:
  `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca`
- Binary size: 1,149,044,528 bytes
- Build logs: `/tmp/v332_build.log` (first build, A03+LP01 hooks) and
  `/tmp/v332_build2.log` (second build, A03 log cap) — 0 `error:` lines.
- Source/binary consistency: `git diff --stat HEAD -- CHAOS/gem5/src` is empty;
  no C++ change exists between the built tree and HEAD.
- A hardlink/copy of the final binary is kept at
  `audit_v3_3_2/binary/gem5.opt.v332-070d68a6` (not committed to git).

## Toolchain

- Host: native aarch64 openEuler; `gcc -O2 -static` for workload ELFs.
- gem5: vendored v25.1.0.1 under `CHAOS/gem5`, built with `scons -j16`.
- Python 3.11, pytest, openpyxl.

## Evidence roots

- `audit_v3_3_2/runs/` — 120 run directories (60 fault + 60 control), each
  with `summary.json`, `command.txt`, `config.ini`, `pilot_meta.json` (where
  the runner produced one), model-specific injection logs, stdout/stderr.
- `audit_v3_3_2/roi/` — ROI/percentile mapping, distinctness audit, census.
- `audit_v3_3_2/controls/` — 60 matched fault/control pairs.
- `audit_v3_3_2/propagation/` — 60 causal propagation rows.
- `audit_v3_3_2/workloads/` — W4/RP01/MD04 candidate evidence.
- `audit_v3_3_2/sq_workload/` — SQ01/SQ03/SP05 decision dossier.
- `audit_v3_3_2/subagent_reports/` — Agent F independent acceptance.

## Rules preserved

- Historical evidence keeps its own binary SHA; no chain is stitched across
  binaries.
- Candidate workloads (FW02/RP01/MD04/SQ01/SQ03/SP05) are **not** written into
  the frozen workbook. `git diff 8f7a1354 -- docs/.../excel` is empty.
- No SampleRunID, seed, or frozen verdict was modified.
- No formal campaign was launched.
