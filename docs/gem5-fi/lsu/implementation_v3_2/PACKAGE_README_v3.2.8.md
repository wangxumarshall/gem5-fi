# LSU v3.2.8 package — FW05 config freeze + SQ03 pilots

Package: `LSU_v3.2.8_FW05_ConfigFreeze_SQ03_Pilot_Package.zip`
Branch: `lsu-platform-v3.2.8`, base `f26218f8` (v3.2.7 tip)
HEAD at package build: see `C_Global/GIT_COMMIT_v328.txt`
Final gem5 binary SHA256: `b988b7503cdf1feab10b99d09ec85df84b42eb385396142e0b7be6a197c63a45`

No 60-sample formal run was started. `ConfigFrozen=NO` for all 60 rows.

## A_FW05 — formal workload freeze

- `FW05_Definition_Freeze_v3.2.7.md` — model definition (`FW05-DEF-v1`,
  wrong-source selection; **not** multi-store splicing).
- `FW05_Workload_Archive/` — source, exact pilot binary
  (`0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf`),
  build/run scripts, golden `0x67afad307642983e`, compiler version, inputs
  statement, `PROVENANCE.md`, `SHA256SUMS`, README, per-seed baselines.
- `FW05_No_Fault_Baselines_v3.2.8.md` +
  `evidence/FW05_no_fault_baselines.csv` — five per-seed no-fault runs, all
  PASS.
- `pilots/FW05-R01..R05/` — the five original v3.2.7 pilots with raw
  `trace_v31.jsonl` and `prop_trace.csv.gz`, manifests, oracle logs.
- `excel/` — `gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx`
  (authoritative), `60_SAMPLE_MATRIX.csv`, `FW05_CONFIG_v3.2.3.md`,
  `FW05_OLD_NEW_DIFF_v3.2.3.md`, and the retained v3.2.2 workbook with the
  historical W8 alignment configuration.
- `recheck/RECHECK_v328_FINAL_BINARY.csv` — all five pilots re-run on the
  final binary; R02–R05 reproduce their historical SDC checksums exactly,
  R01 reproduces the golden.

## B_SQ03 — safety hardening and five pilots

- `SQ03_Definition_Freeze_v3.2.7.md`, `SQ03_Safety_Audit_v3.2.8.md`,
  `SQ03_Implementation_v3.2.8.md`.
- `src/` — the changed C++ sources (`CHAOSLSQFwd.cc/.hh/.py`,
  `sq03_rules.hh`, `sp05_rules.hh`, `CHAOSPropagation.cc/.hh`,
  `lsq_unit.cc`) and `GIT_DIFF_CODE_v328.txt`.
- `tests/test_sq03_rules.cc` + run log; build log.
- `evidence/SQ03_safety/` — `max_faults=0` vs `1` smokes and the watchdog
  smoke (exit 1 with `CHAOS_SQ03_WATCHDOG=EXPIRED`).
- `pilots/SQ03-R01..R05/` — raw `trace_v31.jsonl`, manifests, injection logs,
  oracle logs, stats.
- `evidence/SQ03_v328_EVIDENCE.csv`, `SQ03_baselines/`,
  `recheck/` (final-binary reproduction of R01).

## C_Global — provenance and status

- `MODEL_STATUS_MATRIX.csv` (12-model state matrix).
- `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx`,
  `excel/60_SAMPLE_MATRIX.csv`.
- `GIT_COMMIT_v328.txt` (branch, full 40-char HEAD, binary SHA),
  `GIT_LOG_v328.txt`, `GIT_STATUS_v328.txt`, `GIT_DIFF_STAT_v328.txt`,
  `GIT_DIFF_CODE_v328.txt`.
- `LSU_v3.2.8_Status_Report.md`, `LSU_v3.2.8_Final_Report.md`,
  `OPEN_ISSUES_v3.2.8.md`.
- `SHA256SUMS` — checksum of every file in this package.

## How to verify

```bash
sha256sum -c SHA256SUMS                     # inside the extracted package
sha256sum A_FW05/FW05_Workload_Archive/bin/fw05_forward
# expect 0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf
python3 -m pytest tests/test_fw05_archive.py tests/test_v328_consistency.py \
                 tests/test_lsu_v323_workbook.py -q   # in the worktree
```

Reproduce a pilot with `A_FW05/FW05_Workload_Archive/run_pilot.sh OUTDIR SEED ORDINAL`
(FW05) and the command in `B_SQ03/pilots/SQ03-R01/command.txt` (SQ03). SQ03
requires `--max_faults 1` and keeps the watchdog enabled
(`--sq03_watchdog_cycles`, default 500,000,000 ticks).

## Honesty notes

- SQ03's five pilots are MASKED (oracle PASS) with zero consumers; the store
  chain ends at `sq03_complete`. `PROPAGATION_VERIFIED=0`.
- FW05's four SDCs are reproducible model-level pilots, not a formal 60-sample
  result.
- Large JSONL traces are included here but are not committed to Git
  (`SQ03_TRACE_STORAGE.md` lists their hashes).
