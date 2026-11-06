# LSU Platform v3.2 — implementation bundle

This directory is the Gate-1/Gate-2 delivery for the LSU v3.2 task.

## Accepted evidence

- `platform/` — config parser, manifest, F0/F5/F6 manager, Trace v3.1
  writer/validator/completeness/summary, terminal classifier, oracle adapter.
- `LSU_Trace_Schema_v3.2.json` — published JSON Schema.
- `LSU_Trace_Sample_v3.2.jsonl` — validated sample.
- `workloads/` — W1-W8 sources, binaries, compile/run scripts, goldens,
  oracle checker and the W6/W8 guard-page probe.
- `baselines/` — eight no-fault gem5 baselines with config/stats/stdout/
  stderr/oracle/run metadata and target-event proof logs.
- `pilots/` — A01/F0, A03/F5 and FW02/F6 with command, manifest, raw gem5
  logs, `trace_v31.jsonl`, validator/completeness output and `GATE2_REPORT.md`.
- `gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.xlsx` — 60 preserved
  SampleRunIDs/seeds, all real workload paths/SHAs/goldens, actual statuses.
- `LSU_Implementation_Status_v3.2.md` — gate-by-gate status, including what
  is not done.
- `preexisting_rejected/` — the 09:43-09:45 artifacts, preserved but not used.

## Reproduce Gate 1

```bash
platform/run_gate1.sh
```

## Reproduce Gate 2

```bash
workloads/compile_<name>.sh
workloads/run_<name>.sh
baselines/run_baselines.sh
platform/run_pilot.py --model A01 --pilot-id PILOT-A01-F0-W1-R01 \
  --seed 2108120075 --outdir pilots/A01F0
platform/run_pilot.py --model A03 --pilot-id PILOT-A03-F5-W1-R01 \
  --seed 663646247 --outdir pilots/A03F5
platform/run_pilot.py --model FW02 --pilot-id PILOT-FW02-F6-W4-R01 \
  --seed 2941542370 --outdir pilots/FW02F6
```

Gate 3 and Gate 4 are not started. No formal `SampleRunID` was executed.
