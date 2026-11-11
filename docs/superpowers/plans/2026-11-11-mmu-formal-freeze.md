# MMU Formal Freeze & Readiness Closure — Execution Plan

Date: 2026-11-11
Workspace: `/home/sdc/gem5-fi-mmu-impl-v2` (original `/home/sdc/gem5-fi-mmu` is read-only)
Starting point: branch `fsu`, HEAD `2a8422b4`, binary `3ec51b2c…`
Research decision (already approved by the researcher): 40 SampleRunIDs frozen,
`Seed = N/A_DETERMINISTIC`, `SeedPolicy = DETERMINISTIC`.

Rule: every task below is exactly one commit. No task is closed until its
verification command's real output is quoted in this file (or a linked report).
No formal sample is launched; only TEST-ID pilots/controls.

## Phase 0 — Baseline and provenance (Main)

- [ ] 0.1 Record branch/HEAD/status/binary/source/workload SHA256 in
      `phase3/freeze/BASELINE_SNAPSHOT.txt` (done 2026-11-11T15:50:34Z).
- [ ] 0.2 Resolve the "two binary SHA256" question: `1f9d3de…` = read-only
      original workspace; `3ec51b2c…` = this workspace final; `d80a52…` =
      earlier impl-v2 pilot binary. Map every phase3 pilot to its binary.
- [ ] 0.3 Freeze the current worktree state as a local safety commit/branch
      (no reset/clean, no deletion).

## Phase 1 — Investigation (5 subagents, read-only first)

- [ ] 1.A M05 R03–R05 trace truncation + real consumption proof; M06 R02 true
      cold store walk. Output: root cause, minimal patch, exact rerun plan.
- [ ] 1.B M07 R02/R03/R05 permission-grant hook extension (same logical model,
      one injection per sample); M08 R02–R04 non-speculative consumption.
- [ ] 1.C W10S runtime TargetVA / cold-store / W14 context verification and
      golden controls (native + SHA256).
- [ ] 1.D Frozen Excel design; `N/A_DETERMINISTIC` runner/preflight support;
      FS-config random-source audit (actually run config `configs/fs/lsu_b0_fs.py`).
- [ ] 1.E Independent read-only audit of existing M01–M08 evidence, binary
      provenance, oracle independence, validator honesty.

## Phase 2 — C++ / workload implementation (owned files only)

- [ ] 2.1 (Agent A) `arch/arm/table_walker.cc/.hh` M05 trace flush + M06 cold
      descriptor path fixes.
- [ ] 2.2 (Agent B) `arch/arm/mmu.cc` M07 authorization hook extension; M08
      consumed-translation gating. One commit each.
- [ ] 2.3 (Agent C) `workloads/mmu/W10S`, `workloads/mmu/W14`, rcS generators;
      rebuild binaries, update SHA256 and GOLDEN.md.
- [ ] 2.4 Build with `scons -j16` (Main only), 0 errors, record new binary SHA.
- [ ] 2.5 M05–M08 pilots, 5 contexts each, on the frozen binary; capture full
      trace + validator verdict. Failed runs preserved.
- [ ] 2.6 Necessary M01–M04 regressions on the frozen binary (static
      invariance proof where a full 5-context rerun is not warranted; record).

## Phase 3 — Authority freeze

- [ ] 3.1 Create frozen workbook `gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx`
      (SampleIDStatus=FROZEN, Seed=N/A_DETERMINISTIC, SeedPolicy,
      SeedSource, SampleFreezeStatus) without touching the source workbook.
- [ ] 3.2 Frozen `MMU_40_Sample_Matrix.csv`, `MMU_Formal_Config.json/.yaml`,
      cross-checked against the workbook (40/40, 8 models × 5 contexts).
- [ ] 3.3 `mmu_formal_runner.py` / `mmu_formal_preflight.py` /
      `mmu_formal_validate.py`: deterministic-seed policy, frozen-ID policy,
      binary/source SHA gate, no-overwrite, real evidence citations.

## Phase 4 — Preflight and audit

- [ ] 4.1 40/40 preflight, no gem5 launch; every non-READY row names its
      blocker + evidence path.
- [ ] 4.2 Agent E final independent read-only audit after integration.
- [ ] 4.3 Package `MMU_Formal_Ready_Package.zip` with the 18 required items +
      SHA256 manifest.
- [ ] 4.4 Final status report; `MMU_FORMAL_READINESS` value. Stop and wait for
      researcher approval before any formal sample.

## Non-negotiables

- Never fabricate evidence; quote real command output.
- Never generate/hash/timestamp a numeric seed.
- Never edit the original Excel or `/home/sdc/gem5-fi-mmu`.
- Never lower validator thresholds to manufacture PASS.
- Preserve every failed run, control, pilot trace and SHA256 manifest.
- Max 2 concurrent large FS pilots; max 4 gem5 processes.
