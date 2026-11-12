# LSU v3.3.3 — Ground Truth for Phase-1 Auditors (2026-11-11)

This file is the shared, verified baseline for every v3.3.3 audit agent. Trust it
over any summary report; if you find a contradiction, report it with raw evidence.

## 1. Workspace and provenance

| Item | Value |
|---|---|
| Worktree | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` |
| Branch | `lsu-v3.3.1-context-workload-20261111` |
| Git HEAD | `3097ad82e7066f18fc35cf64dcb612a05c1fc021` |
| Source-equivalent HEAD | `fc60822408cbb3f5af4788bd99fc82c114917367` (HEAD adds only results/evidence/package commits) |
| Final binary | `build/ARM/gem5.opt`, SHA256 `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca` (verified live) |
| Config | `configs/se/lsu_proxy.py` |
| Runner | `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py` |
| Matrix driver | `tools/lsu_v332_matrix.py` (tracked/corrected in v3.3.2; verify) |
| Build log convention | `/tmp/v332_build*.log`, 0 `error:` lines |

Working tree currently has untracked audit outputs under `audit_v3_3_2/`.
Do not rewrite or delete them.

## 2. Authoritative experimental identity (read-only)

- Frozen sample matrix: `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv`
- Latest authoritative workbook: `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`
- Pre-formal 60-sample workbook: `docs/gem5-fi/lsu/implementation_v3_2/preformal_v3_3/LSU_12Model_60Sample_PreFormal_v3.3.xlsx`
- SampleRunID and Seed MUST come from these files. No invented seeds/hashes.
  The v3.3.2 working tables use provisional IDs `V332-<model>-R<ctx>`; the frozen
  workbook uses `A01-F0-W1-S01-R01`-style IDs. Resolving this mapping is part of
  the v3.3.3 Excel defect (do not silently replace authoritative IDs).

## 3. Scope: 12 models × R01–R05 = 60 contexts

Ordinals in the current matrix (verify each against its run `command.txt`):

| Model | ROI start–end (N) | R01/R02/R03/R04/R05 |
|---|---|---|
| A01 | 1040–1234 (195) | 1059 / 1098 / 1137 / 1176 / 1215 |
| A03 | 1040–1234 (195) | 1059 / 1098 / 1137 / 1176 / 1215 |
| FW02 | 8–67 (60) | 13 / 25 / 37 / 49 / 61 |
| FW05 | 1–2000 (2000) | 200 / 600 / 1000 / 1400 / 1800 |
| SQ01 | 1006–1133 (128) | 1018 / 1044 / 1069 / 1095 / 1121 |
| SQ03 | 1009–1136 (128) | 1021 / 1047 / 1072 / 1098 / 1124 |
| SP05 | 940–1067 (128) | 952 / 978 / 1003 / 1029 / 1055 |
| DA04 | 33–1056 (1024) | 135 / 340 / 544 / 749 / 954 |
| LP01 | 886–17525 (16640) | 2549 / 5877 / 9205 / 12533 / 15861 |
| MD04 | 3–10 (8) | 3 / 5 / 6 / 8 / 10 |
| LQ04 | 1–5 (5) | 1 / 2 / 3 / 4 / 5 |
| RP01 | 1–255 (255) | 26 / 77 / 128 / 179 / 230 |

Percentile rule: `k = ceil(p·N)`, absolute ordinal = ROI_start + k − 1, for
p = 0.10 / 0.30 / 0.50 / 0.70 / 0.90.

## 4. Evidence root

- `audit_v3_3_2/runs/<MODEL>-R<NN>-{fault,control}/` — 120 run dirs
  (`command.txt`, `summary.json`, `pilot_meta.json`, `stdout.log`,
  `stderr.log`, `oracle.log`, `trace_v31.jsonl` where applicable, model logs).
- `audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final.csv`
- `audit_v3_3_2/propagation/LSU_60Context_Causal_Propagation_Final.csv`
- `audit_v3_3_2/roi/LSU_60Context_ROI_Percentile_Mapping.csv`
- `audit_v3_3_2/roi/LSU_60Context_Distinctness_Audit.csv`
- `audit_v3_3_2/LSU_60Context_Final_Readiness_Matrix.csv`
- `audit_v3_3_2/LSU_Workload_Oracle_Final_Audit.csv`
- `audit_v3_3_2/LSU_12Model_Source_Hook_Audit.csv`
- `audit_v3_3_2/sq_workload/LSU_SQ_Workload_Decision.md` + `evidence/`
- `audit_v3_3_2/workloads/`, `audit_v3_3_2/patches/`, `audit_v3_3_2/binary/`
- Source: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/`, `CHAOSLSQFwd/`, `CHAOSL1DForward/`,
  `CHAOSMD04/`, `CHAOSLQ04/`, `CHAOSPropagation/`, `src/cpu/o3/lsq.cc`, `lsq.hh`.

## 5. Known blockers recorded by v3.3.2 (verify, refute, or refine — do not assume)

- B1: 30 candidate contexts pending researcher approval (FW02 W4-v2, RP01
  partial-overlap, MD04 violations, SQ01/SQ03/SP05 `sq_reload_v3212`).
- B2: A01-R03 has no register-writeback divergence evidence → `UNRESOLVED`.
- B3: A03 uses an external 30 s timeout, not an in-simulator watchdog; partial logs.
- B4: SP05 `store_data_fnv=null` → `RELOAD_UNVERIFIABLE`; early-anomaly event missing.
- B5: SQ03 must be labelled MASKED / visibility shift, not SDC.
- B6: `ConfigFrozen=NO`; ROI/warm-up/binary approval pending.

## 6. Staleness warnings (verified today)

- `audit_v3_3_2/roi/LSU_60Context_ROI_Percentile_Mapping.csv` NOW contains the
  corrected FW02 absolute ordinals 25/37/49/61 (R02–R05). The v3.3.2 acceptance
  report §3 and `subagent_reports/Agent_F_Independent_Acceptance_v332.md` still
  claim 18/30/42/54. Treat those prose claims as stale; verify the CSV and the
  run commands (`runs/FW02-R02-fault/command.txt` shows `--lsqfwd_event_ordinal 25`).
- A03 `addrpath_injections.log` shows real PCs (e.g. `pc=400598`), so the former
  "A03 PC=0" symptom may already be fixed. Verify before reporting it as live.
- `audit_v3_3_2/report/PROVENANCE.md` is stale relative to HEAD/binary; verify.

## 7. Hard rules for every Phase-1 agent

1. **Read-only.** Do not edit any file under `CHAOS/`, `configs/`, `workloads/`,
   `docs/gem5-fi/lsu/implementation_v3_2/`, `tools/`, `audit_v3_3_2/`, or the Excel.
   The ONLY file you write is your assigned report under `audit_v3_3_3/reports/`.
2. **No gem5 runs** in Phase 1 (no `build/ARM/gem5.opt` invocation, no pilot).
   Static inspection, parsing existing logs/traces, `objdump`, `readelf`, `sha256sum`,
   `python3` read-only analysis are allowed.
3. **No verdict inflation.** Quote real paths and real command output. If evidence
   is absent, write `n/a` + why. Never infer PASS from a summary table alone.
4. Report every issue with: model/context, root cause, raw evidence path, affected
   files, affected contexts, proposed one-shot fix, validation command, approval
   required (Y/N), regression risk.
5. Classify each issue: **A** code/hook defect, **B** workload/dynamic-context design,
   **C** trace/propagation/oracle evidence, **D** Excel/seed/control/binary/runner.
6. Merge multiple symptoms of one root cause into one issue; propose the source-level
   fix, never a downstream CSV patch.
7. End with a short "Bottom line" and an explicit list of anything you could not verify.

## 8. Environment limits

- Host: native aarch64 openEuler, 126 cores, 59 GiB free on /home (20 GiB floor).
- gem5 hard cap: 4 concurrent processes (not used in Phase 1).
