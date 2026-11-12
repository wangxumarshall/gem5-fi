# LSU v3.3.3 — Launch Preflight Report

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**Final source HEAD:** `b5031bf7` · **Results HEAD:** `b8405580`
**Final binary:** `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
**Final config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Scope:** 12 models × R01–R05; 60 fault + 60 matched control = 120 runs.
**Verdict:** **`READY_TO_LAUNCH_FORMAL_CAMPAIGN = YES`** — independent launch audit PASS (Agent F final, 2026-11-12). The earlier A01 identity concern is resolved: all five A01 contexts map to identical PC/EA in the census and executed streams with a constant `+157` `dyn_inst_seq` offset caused by a relative-vs-absolute `--cmd` path (SE stack shift); the percentile rule is defined on the eligible-event ordinal axis, which is preserved. All 14 launch gates are PASS (two with documented non-blocking QUALIFIED notes).

## 1. Baseline checked (not trusted from the previous summary)

- Git HEAD `b8405580`; source/binary consistency: `git diff --stat b5031bf7 -- CHAOS/gem5/src` empty.
- 120 pre-formal summaries, one binary SHA `1126e0fd`; 60 fault injection >0; 60 control injection 0.
- Control proof: 35 `MOUNTED_BUT_DISABLED` + 25 `INJECTOR_ABSENT` + 0 suppressed; all 60 control oracle PASS.
- Terminals: SDC 43 / MASKED 12 / HANG_WATCHDOG 5; 12 MASKED mechanisms; RP01 target ordinals 26/77/128/179/230.
- Freeze: 51 GiB free, 25 GiB RAM available, 126 cores, 0 gem5 processes.

## 2. Gate table

| Gate | Result |
|---|---|
| Models | 12/12 PASS |
| Fault SampleRunID | 60/60 PASS (frozen matrix, no V332 IDs in identity columns) |
| Seed | 60/60 PASS (frozen; formal dry-run passes the frozen seed explicitly) |
| Context Mapping | 60/60 PASS (A01 census/executed PC/EA identical; constant +157 dyn-seq offset from the relative `--cmd` SE stack shift; ordinal axis preserved) |
| Workload Approval | 12/12 PASS (2026-11-12 approval) |
| Fault-Control Pairing | 60/60 PASS |
| Control Zero Proof | 60/60 PASS (35/25/0) |
| Application Oracle | 60/60 PASS |
| Binary Provenance | PASS (`b5031bf7` / `1126e0fd` / `8309da72`) |
| Manifest 120/120 | PASS (preflight manifest + per-run post-step) |
| Runner Dry-run | PASS (120 commands, 0 collisions, no history references) |
| Output Collision | 0 PASS |
| Resource Check | PASS |
| Config Freeze | YES (approval 2026-11-12; frozen Excel unchanged) |
| Independent Audit | PASS (Agent F final, 2026-11-12; `LSU_Independent_Launch_Acceptance.md`) |

## 3. Fixes completed this preflight (metadata/tooling, no experiment-semantics change)

1. **Runner formal identity**: `tools/lsu_v332_matrix.py` now loads the frozen
   `60_SAMPLE_MATRIX.csv`, passes the frozen `--seed` to every `run_pilot`
   command and adds `--preserve-sample-id`; the direct A03/RP01 commands use
   the frozen seed. Dry-run: 105/105 run_pilot commands carry the frozen seed +
   preserve flag; 15/15 direct commands carry the frozen seed.
2. **LQ04 seed**: `run_pilot.py build_model_extra` now passes
   `--lq04_rng_seed <frozen>`; the gem5 dry-run shows
   `--lq04_rng_seed 1842987246` for R01. The historical LQ04 pre-formal runs
   used `rngSeed=0` (F0 ordinal selection is deterministic) and are kept as
   history; the formal campaign will use the frozen seed.
3. **Output-directory safety**: default out-base is the new
   `runs/lsu/formal_v333`; the lock is under the new base; an existing run dir
   is refused unless `--force` (no silent `rm -rf` of history).
4. **Manifest post-step**: `tools/lsu_v333_launch.py --manifest-only` writes the
   120-row campaign manifest and one `campaign_manifest.json` per run with the
   required fields; the runner itself remains a pure gem5 driver.
5. **Launch artifacts**: `LSU_Formal_Experiment_Config_Final.xlsx` (5 sheets),
   `LSU_120Run_Campaign_Manifest.csv` (120), `LSU_60Fault_60Control_Pair_Map.csv`
   (60), `LSU_Control_Zero_Injection_Proof.csv` (60 PASS),
   `LSU_60Context_Causal_Propagation_Final.csv` (60 rows, authoritative 16-col
   generator), `LSU_60Context_Final_Readiness.csv` (30 FORMAL + 30
   OVERRIDE_APPROVED, 60 READY).
6. **Propagation versions**: the lossy 14-column `_Final.csv` and the older
   copies are listed in `LSU_ARCHIVED_Propagation_Versions.csv` as ARCHIVED;
   the authoritative file is the current 16-column generator output.

## 4. A01 identity concern — resolved (independent F final)

The earlier concern was that census ordinal 597 mapped to
`dyn_inst_seq=12752` while the executed fault run mapped the same ordinal to
`12909` (same PC `0x400578`, same EA `0x493020`). Independent Agent F final
reproduced the offset and compared **all five** A01 contexts:

- Every ordinal maps to the **identical PC and EA** in the census and executed
  streams; the `dyn_inst_seq` offset is a **constant +157** for R01–R05.
- Root cause: the census was launched with a **relative `--cmd` path**; the
  fault run uses an absolute path. The SE stack layout shifts, changing the
  initial instruction sequence by a constant; the main-loop event identities
  and the eligible-event ordinal axis are preserved. The percentile rule
  (`N=129`, ordinal window [585,713]) is defined on that ordinal axis, so the
  10/30/50/70/90 calibration stands.
- The A01 fault evidence is complete and real: injection → addr_form →
  writeback → commit → errant_commit → 394 consumer_commit → 48 taint
  mismatches; oracle FAIL vs control PASS on golden `728e604ffcec539d`.

No re-census and no source/workload/seed/ID change is required. This concern is
closed; it is not a launch blocker.

## 4.1 Independent-audit finding F-1 (fixed)

The first manifest pass labelled the five RP01 HANG faults `FAIL`; the
authoritative value is `NO_CHECKSUM` (no application checksum by design). The
generator was corrected and the regenerated manifest now reports
43 FAIL / 12 PASS / 5 NO_CHECKSUM, matching the causal/readiness tables.

## 4.2 Non-blocking QUALIFIED notes

- The legacy frozen `60_SAMPLE_MATRIX.csv` still carries
  `ConfigFrozen=NO` / `NEEDS_USER_DECISION`; it is the authoritative identity
  source and is intentionally not edited. The launch workbook and manifest carry
  `ConfigFrozen=YES (approved 2026-11-12)`.
- Three models (FW02/LQ04/RP01) have source-level mounted-p0 gates rather than a
  runtime gate artifact; their controls are `INJECTOR_ABSENT`, so zero is
  proven by absence + oracle. Optional single gate runs would make it runtime;
  no gate blocks launch.
- A03's watchdog ends via `exitSimLoop` with a custom reason that gem5 reports
  as `Exit event ... not implemented` (exit 1); the trace/oracle are complete
  and the terminal is classified via the marker/checksum. A clean-exit fix
  would require a C++ rebuild; not required for launch.

## 5. Formal campaign command (not executed)

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
python3 tools/lsu_v332_matrix.py --models all --roles fault,control \
  --contexts 1,2,3,4,5 \
  --out-base runs/lsu/formal_v333 \
  --out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv
python3 tools/lsu_v333_launch.py --runs runs/lsu/formal_v333 \
  --out runs/lsu/formal_v333/manifests --manifest-only
```

- 120 tasks: 60 fault + 60 control; model-major order (A01, A03, FW02, FW05,
  SQ01, SQ03, SP05, DA04, LP01, MD04, LQ04, RP01), R01→R05, fault then control.
- Serial, one gem5 process at a time; hard cap ≤4 concurrent; 51 GiB free.
- Estimate 30–40 min realistic; worst case ~12.9 h at timeouts; ~3.2 GB output.
- Do not start until the researcher authorizes and the A01 blocker is resolved.

## 6. Package contents

See `LSU_v3.3.3_Formal_Campaign_Launch_Package.zip`: this report, the config
final workbook, the 120-run manifest, the 60-pair map, the causal final, the
control proof, the binary provenance, the dry-run report, the resource report,
the final blockers, the independent launch acceptance, the runner diff/logs,
and the six preflight agent reports.
