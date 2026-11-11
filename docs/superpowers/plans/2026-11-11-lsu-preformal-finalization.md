# LSU 12-Model Pre-Formal Finalization — Round Plan (v3.3.0)

Date: 2026-11-11. Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`,
branch `lsu-preformal-v3.3.0-20261111` (base `lsu-platform-v3.2.12` @ `9e3d104c`).
Baseline binary: `68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`.

Scope is the researcher's 2026-11-11 decision: **12 models × R01–R05 = 60 contexts only**.
The 74-model / 4075-SampleRunID full baseline is out of scope for this round and must not
be reported as a blocker.

## Goal

Bring the 12 models / 60 distinct dynamic contexts to a rigorously verifiable pre-formal
state: context eligibility, workload+golden, injection semantics, causal propagation,
matched fault-control, and frozen experiment configuration. No formal campaign launch.

## Authoritative inputs (read-only)

- Design: `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`
  (sheet `5.60个样本执行矩阵`: 60 SampleRunIDs, 12 models, seeds; sheets `3`, `4`, `6`).
- Closure: `audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv`,
  `Closure_Matrix_Status_v3.2.12.md`, `FINAL_GRADING_RULES_v3.2.12.md`,
  `LSU_Propagation_Acceptance_Standard_v3.2.12.md`.
- Records: `audit_v3_2_12/*_records_*.json`, `*_verdict_*.json`.
- Pilots: `pilots_v3_2_{1..12}/`, `audit_v3_2_11/extracted_evidence/`.

## Tasks (one commit per unit)

- [x] P0.1 Dispatch Subagents A–F (read-only static audits in parallel)
- [x] P0.2 Main-agent baseline: 60-context design extraction + seed/SampleRunID identity check
- [x] P1.1 FW05 reload observation node (store→reload edge NOT proven; register chain proven)
- [x] P1.2 A01 control-mode golden-EA probe + memory nodes (control_valid)
- [x] P1.3 RP01 on-chain squash `triggering_seq` (squash remains fault-unlinked)
- [x] P1.4 A03 native `a03_fault` crash-address link (5/5 contexts)
- [ ] P2 Count-only preflight (blocked on approved warm-up/ordinals)
- [x] P3 Representative fault/control pilots for every modified mechanism
- [ ] P4 60-context full acceptance — BLOCKED: 42 controls missing, 45 historical-only, warm-up unfrozen
- [ ] P5 Final regression done (180+107); freeze BLOCKED (no runner dry-run)
- [ ] P6 Independent acceptance (Subagent F, second pass)
- [ ] Deliverables + `LSU_12Model_PreFormal_Readiness_Package.zip`

## Verification rules

- No gem5 campaign; pilots only, single-slot, ≤4 concurrent gem5.
- No modification of Excel identities/seeds/semantics, frozen verdicts, or history.
- Build with `scons -j16` (clean) / `-j126` (incremental); quote real output before commit.
- Every readiness row cites an evidence path or is BLOCKED with a reason.
