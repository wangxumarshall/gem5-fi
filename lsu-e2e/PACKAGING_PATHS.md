# Packaging path adaptation

The frozen experiment code used the original absolute workspace
`/home/sdc/gem5-fi-LSU/e2e_extension` and `/home/sdc/gem5-fi-LSU/repo`.
For the release branch, only path resolution was changed; fault models,
hooks, workloads, contexts, timings, seeds, ROI, fault/control pairing and
all numeric parameters are unchanged.

The release copy resolves paths as follows:

| Variable | Default in this project |
|---|---|
| `LSU_E2E_ROOT` | `<clone>/lsu-e2e/code` (runner/configs/workloads/results) |
| `LSU_WORKSPACE_ROOT` | `<clone>/lsu-e2e` (inputs/evidence/reports) |
| `LSU_GEM5_ROOT` | `<clone>/CHAOS/gem5` |
| `LSU_INPUT_XLSX` | `<clone>/lsu-e2e/inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx` |

`run_campaign.sh` exports these before invoking the campaign runner.
`run_representative.sh` invokes the frozen gem5 command line directly with
clone-relative paths.

The original frozen commit is
`780099c805867ad194d74a81c3b6273aa0be8e5a` and the tag is
`LSU_SE_PAPER_FINAL_FROZEN_20261119_SUPP1`; `SOURCE_VERSIONS.json` records
the mapping. No experimental result was regenerated for this adaptation.
