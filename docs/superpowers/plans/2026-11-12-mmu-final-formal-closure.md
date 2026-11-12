# MMU Final Formal Closure — Plan (2026-11-12)

Workspace: `/home/sdc/gem5-fi-mmu-impl-v2` (original `/home/sdc/gem5-fi-mmu` is read-only).
Baseline package: `phase3/freeze/MMU_Formal_Ready_Package.zip` (SHA256 in its `.sha256`).
Prior verdict: `MMU_FORMAL_READINESS = PARTIAL`, 18/40 READY (see
`phase3/freeze/MMU_Final_Blockers.md`, B1–B10).

## Frozen decisions (not to be changed)

- Models M01–M08 only, 40 SampleRunIDs, Seed literal `N/A_DETERMINISTIC`,
  SeedPolicy `DETERMINISTIC`, SampleIDStatus `FROZEN`.
- M07 R03 = PROT_EXEC + EL0 Load; M07 R05 = valid XN mapping + indirect-branch fetch.
  ModelID/FaultModel/SampleRunID/count/one-shot constraints unchanged.
- No formal SampleRunID is launched this round; all runs use TEST IDs.

## Baseline (recorded before any edit)

- branch `mmu-formal-freeze-2026-11-12`, HEAD `f24b6b77af9f4217c026d9a39e58e5a04c69dea3`
- tracked diff 200 paths (see `phase3/freeze/baseline_tracked_diff.patch`)
- frozen gem5 binary `CHAOS/gem5/build/ARM/gem5.opt`
  SHA256 `a71ce0ca21de143d9aa5ab05e29d9bee86dff213576941a3191a256f1d842024`
- guest kernel 5.15.36, `CONFIG_ARM64_EPAN=y`, `CONFIG_ARM64_PAN=y` (extracted
  from `gem5-fs/vmlinux` IKCFG_ST) — PROT_EXEC-only maps PAGE_EXECONLY (AP=00).

## Tasks (one commit per unit; no bundling)

- [ ] T1 Agent A: M01–M04 evidence closure (M01 R02 commit/squash truth, M02 R02
      PFN per-context, M03/M04 final-binary regression, M04 committed wrong-PA witness).
- [ ] T2 Agent B: M05 R05 Execute-path trace transaction (observability C++ only)
      and M06 R03–R05 terminal re-audit (DETECTED_CONTAINED only with real
      `exception_delivery`; otherwise record the true terminal and propose an
      Excel terminal amendment).
- [ ] T3 Agent C: M07 W14 R03 PROT_EXEC + EL0 load and R05 valid XN + indirect
      branch; verify real AP/XN PTE bits from `pte_decode`; independent controls.
- [ ] T4 Agent D: M08 R02–R05 propagation evidence, R03 raw trace, R05 store
      redirect, W10S runtime TargetVA (WorkloadID stays W10, internal Variant).
- [ ] T5 Agent E: authority Excel/JSON/YAML, runner M02 old_pfn resolution,
      preflight, package (tools only).
- [ ] T6 Main: integrate all C++ patches, one audit, one build, freeze new binary SHA.
- [ ] T7 Main: rerun all 40 contexts + controls on the frozen binary (concurrency 4).
- [ ] T8 Main: validate, readiness matrix, preflight 40/40, final package.

## Verification per task

- Build: `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` exit 0, no new warnings.
- Run: `tools/mmu_formal_runner.py --pilot TEST-F1-...` exits 0 with
  `sample_manifest.json` recording `gem5_sha256`, `source_sha256`,
  `workload_sha256`; validator verdict written under `Validation/`.
- Regression: at least one unaffected model reruns `exit: pass`, no SIGSEGV.
- No result is reported unless the command output is quoted.

## Boundaries

Never delete historical runs; never `git reset`/`git clean`; never overwrite a
run directory; never edit the original workspace; never lower validator
standards to manufacture PASS; never fabricate evidence.
