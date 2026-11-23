# WHEN-5X3 deliverables index

- `experiment_status.csv` — 120-condition status matrix
- `run_manifest.json` — provenance, hashes and run rows
- `final_acceptance.md` / `acceptance.json` — A01–A22
- `blocked_tasks.md` — N/A/BLOCKED/FAILED reasons
- `runs/W5X3/<SampleRunID>/` — raw trace, terminal, manifest, command
- `runs/W5X3/<ControlID>/` — golden pre-scan/control
- `analysis/eligible_events/<ControlID>.csv` — full eligible-event stream
- `analysis/timing_map.csv` — N, ceil(pN), actual ordinal/event id
- `analysis/propagation_chains.csv` — observed causal stages
- `analysis/fault_control_compare.csv` — oracle diff per sample
- `campaign/` — runner, rcS generator, condition map, analysis code
- `provenance/` — old-workspace hashes, A01–A03 audit
