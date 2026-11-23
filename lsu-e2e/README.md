# LSU SE final reproducible project

This directory is the final LSU Syscall-Emulation (SE) experiment project,
derived from the frozen release:

* gem5 source: commit `2bbf2907668f78e0b67473caf5a63153b70bede3`
* experiment project: commit `780099c805867ad194d74a81c3b6273aa0be8e5a`
* frozen tag: `LSU_SE_PAPER_FINAL_FROZEN_20261119_SUPP1`
* package: `LSU_E2E_PAPER_FINAL_FROZEN_R2_SUPP1`
* design: 12 LSU models x 5 contexts x 3 timings = 180 faults + 60 controls

No fault model, injection hook, workload, context, timing, seed, ROI,
fault/control pairing, or frozen statistic was changed. The only release
adaptation is path portability (see `PACKAGING_PATHS.md`) so the project can
build and run outside `/home/sdc/gem5-fi-LSU`.

## Layout

```
<clone>/
├── CHAOS/gem5/          final gem5 ARM O3CPU source (build here)
├── CHAOS/               LSU observation modules
└── lsu-e2e/
    ├── code/
    │   ├── runner/      campaign, trace analysis, report/freeze tools
    │   ├── tests/       ARM64 semantics, strict-edge and acceptance tests
    │   ├── configs/     lsu_proxy_e2e.py
    │   └── workloads/   sources, build script, prebuilt bin/, frozen goldens
    ├── inputs/          final experiment workbook
    ├── evidence/        controls, RP01, semantic summaries, squash, manifests
    ├── reports/         FINAL_* authoritative reports
    ├── verification/    frozen verification records
    └── run_*.sh         representative and full campaign entry points
```

## Quick start

```bash
# 1. Build gem5 (from the clone root)
cd CHAOS/gem5
scons build/ARM/gem5.opt -j"$(nproc)"
cd ../..

# 2. Check the workload binaries (prebuilt) or rebuild them
ls lsu-e2e/code/workloads/bin/agu_C03
# optional: (cd lsu-e2e/code/workloads && ./build_e2e_workloads.sh)

# 3. Reproduce one fault and its control
./lsu-e2e/run_representative.sh fault
./lsu-e2e/run_representative.sh control

# 4. Run the full 180 fault + 60 control matrix (long)
./lsu-e2e/run_campaign.sh --jobs 8 --resume
```

See `REPRODUCE.md` for details and expected outputs.

## Evidence kept on the server, not in Git

The full 163 MB frozen ZIP, the 735 raw prop/commit/stdout traces, the
1,141,566-row semantic ledger, per-run causal-chain CSVs, and the 262 MB
aggregate edge CSV are retained on the original server and in the frozen
ZIP. They are not required to rebuild or rerun the experiment. See
`EVIDENCE_EXCLUSIONS.md` for exact paths and SHA256 sources.

## Important

* SE only. Do not run full-system (FS) workloads with this project.
* The frozen `LSU_E2E_PAPER_FINAL_FROZEN_R2_SUPP1` ZIP remains the
  authoritative evidence archive.
* The release branch is a packaging snapshot; the original experiment
  commit/tag are recorded in `SOURCE_VERSIONS.json` and
  `FREEZE_MANIFEST.json`.
