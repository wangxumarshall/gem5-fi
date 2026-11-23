# MMU Final Execution Report — package index

This archive contains the executed WHEN-5X3 campaign report and analysis
artifacts (not the raw per-sample trace corpus; those live in
`runs/W5X3/` on 0202 and in `MMU_When_Golden_Evidence.tar.gz` for controls).

- FINAL_REPORT.md, final_acceptance.md, acceptance.json
- experiment_status.csv (120-condition matrix)
- run_manifest.json (provenance + all run rows)
- blocked_tasks.md (3 M06-C05 N/A)
- analysis/ (timing map, eligible-event lists, propagation chains,
  fault/control comparison, per-condition evidence)
- provenance/ (A01-A03 audit, old-workspace manifests and hashes)
- campaign/ (runner, generators, conditions, rcS scripts)
- resume.sh (idempotent resume entry point)

No Git operation was performed. Raw fault traces: `/home/sdc/gem5-fi-mmu-when5x3/runs/W5X3/<SampleRunID>/`.
