# MMU Final Directory Tree

```
gem5-fi/  (branch mmu-final-reproducible)
├── CHAOS/gem5/                  vendored gem5 + M01-M08 hooks
├── configs/fs/                  mmu_*.rcS run scripts
├── workloads/mmu{, _rev}/       W9-W14/W10S guest binaries + sources
├── tools/mmu_*.py               runner, preflight, validators, slices
├── phase3/freeze/authority/     frozen sample matrix + formal config
├── phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2/  parity authority
├── phase3/run_scripts/          path-independent case launcher
└── MMU_FINAL/
│   ├── MMU_FINAL
│   ├── MMU_FINAL/provenance
│   ├── MMU_FINAL/reproduction
│   ├── MMU_FINAL/reproduction/__pycache__
│   ├── MMU_FINAL/results
│   ├── MMU_FINAL/results/diagnostic
│   ├── MMU_FINAL/results/diagnostic/consumption
│   ├── MMU_FINAL/results/diagnostic/data
│   ├── MMU_FINAL/results/diagnostic/discriminability
│   ├── MMU_FINAL/results/diagnostic/feature_library
│   ├── MMU_FINAL/results/diagnostic/leakage
│   ├── MMU_FINAL/results/diagnostic/observable_features
│   ├── MMU_FINAL/results/diagnostic/real_case
│   ├── MMU_FINAL/results/diagnostic/terminal_semantics
│   ├── MMU_FINAL/results/diagnostic/views
│   ├── MMU_FINAL/results/formal
│   ├── MMU_FINAL/results/formal/audit
│   ├── MMU_FINAL/results/formal/campaign_package
│   ├── MMU_FINAL/results/formal/controls
│   ├── MMU_FINAL/results/formal/samples
│   ├── MMU_FINAL/results/formal/superseded_attempt_A01
│   ├── MMU_FINAL/results/history
│   ├── MMU_FINAL/results/packages
│   ├── MMU_FINAL/results/provenance
│   ├── MMU_FINAL/results/provenance/evidence
│   ├── MMU_FINAL/results/provenance/final_closure
│   ├── MMU_FINAL/results/repeatability
│   ├── MMU_FINAL/results/repeatability/analysis
│   ├── MMU_FINAL/results/repeatability/repeats
│   ├── MMU_FINAL/runtime_assets
│   ├── MMU_FINAL/runtime_assets/checkpoint
│   ├── MMU_FINAL/runtime_assets/checkpoint/cpt.244799013609
│   ├── MMU_FINAL/runtime_assets/gem5-fs
```
