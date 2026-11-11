# MMU Formal Freeze Package

Status: **PARTIAL** (see STATUS.txt). This is the complete frozen-authority,
source/binary, tooling, evidence and preflight package for the 40-sample MMU
experiment.

Contents:
- `Authority/` — frozen 40-sample workbook, matrix CSV, formal config JSON/YAML.
- `Readiness/` — per-model and per-context final readiness matrices.
- `Reports/` — binary/source version, seed audit, preflight, trace validation,
  blockers, change log, confirmed pilot verdicts.
- `Evidence/<PilotRunID>/` — real manifest, verdict, command, terminal, trace,
  SHA256 for every READY context.
- `Controls/` — independent no-fault golden controls.
- `Tools/` — formal runner, preflight, validators, evidence-index builder,
  freeze generator, case runner, build log.
- `Source_Diff/` — C++ diff of the M08 gate, the changed workload sources,
  compressed worktree diff, untracked-file inventory.

Reproduce the preflight:
```
python3 Tools/mmu_build_evidence_index.py --manifest preflight_pilot_runs.json \
  --out evidence_index.json   # mapping also in Reports
python3 Tools/mmu_formal_preflight.py --outdir preflight_out
```
