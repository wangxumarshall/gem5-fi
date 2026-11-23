# LSU final server/GitHub release — executed plan

- [x] Inventory all LSU directories and Git repos; do not delete during inventory.
- [x] Identify final versions: gem5 `2bbf2907`, experiment `780099c`,
      tag `LSU_SE_PAPER_FINAL_FROZEN_20261119_SUPP1`.
- [x] Audit remote branches by actual `git ls-remote`; only
      `lsu-formal-v3.3.3-frozen` matched LSU; `lsu` and `lsu-frozen` absent.
- [x] Build a clean release branch `lsu` from `2bbf2907` with `lsu-e2e/`
      (code, configs, workloads, inputs, manifests, FINAL reports).
- [x] Exclude >100 MB derived evidence and raw traces; record exclusions.
- [x] Add path-portable campaign/representative scripts; no model or
      experiment-parameter changes.
- [x] Commit and push `lsu`; create/push annotated release tag.
- [x] Delete obsolete remote LSU branch `lsu-formal-v3.3.3-frozen`
      (recorded `d8fcc14d91fa0e97461562390ed1728cd2e193a1`).
- [x] Fresh `--single-branch --branch lsu` clone.
- [x] Run code-level tests in the clone (50 passed).
- [ ] Fresh gem5 build in the clone (`scons -j16 build/ARM/gem5.opt`).
- [x] Representative fault and control run from the clone; prop/commit/
      micro/stdout artifacts present.
- [ ] Server cleanup after clone/build validation, with deletion manifest.
- [ ] Final report.

Notes: the frozen experiment code is unchanged except path resolution
(`LSU_E2E_ROOT`, `LSU_WORKSPACE_ROOT`, `LSU_GEM5_ROOT`, `LSU_INPUT_XLSX`).
Large server evidence remains in the frozen SUPP1 ZIP and raw-trace backup.
