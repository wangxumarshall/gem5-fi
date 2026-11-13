# MMU Final Runner Parameter Parity Repair — Implementation Plan

Date: 2026-11-13
Repo: `/home/sdc/gem5-fi-mmu-impl-v2` (branch `mmu-formal-freeze-2026-11-12`)
Scope: formal-runner parameter resolution + parity validation only. No C++,
workload, binary, Seed, SampleRunID, Pilot rerun, Control rerun or formal
experiment launch.

## Frozen facts (verified)

- gem5 binary SHA256: `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`.
- M05 F1 pilots R01-R05 all pass `--mmu_m05_decoy_table_base 0
  --mmu_m05_decoy_va 0x4010200000`.
- `workloads/mmu/W13/mmu_w13.c` defines `W13_DECOY_VA 0x4010200000`
  (`W13_TARGET_VA 0x4010000000`, exact +2 MiB).
- `workloads/mmu/W14/mmu_w14.c` defines `W14_XN_VA 0x400d400000`,
  `CODE_OFF 0x100`; `W14_NONE_CODE_VA 0x400d600000`, `R05_CODE_OFF 0x180`.
- Final F1 M07 pilots: R01 `0x400d000000`, R02 `0x400d000000`,
  R03 `0x400d200000`, R04 `0x400d400100`, R05 `0x400d600180`.
- The older closure pilot TEST-M07-R05 used `0x400d600100`; it is superseded
  by the final F1 pilot `0x400d600180` and by `R05_CODE_OFF 0x180`.
- v3.0.1 authority Excel/CSV do not record an M05 DecoyVA column. The exact
  M07 R04/R05 address is present in the symbolic `TargetVA` text.

## Unit 1 — new versioned authority v3.0.2 (v3.0.1 preserved)

Files (new, under `phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2/`):
- `gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx` — copy of v3.0.1 plus
  `TargetVAExact`, `M05DecoyVA`, `M05DecoyTableBase` columns in
  `07_Sample_Matrix`, plus sheet `18_Parameter_Authority_v3.0.2`.
- `MMU_40_Sample_Matrix.csv` — same three columns appended.
- `MMU_Parameter_Authority_v3.0.2.json` — machine-readable per-sample values,
  pilot-manifest paths+SHA256, W13/W14 source paths+SHA256, supersession note.
- `MMU_Change_Log_v3.0.2.md`, `README_v3.0.2.md`.
- `pilot_evidence/` — copies of the seven sources of truth
  (M05 R01-R05, M07 R04/R05) plus their SHA256 list.

Values: M05 `M05DecoyVA=0x4010200000`, `M05DecoyTableBase=0` for all five;
M07 R04 `TargetVAExact=0x400d400100`, R05 `0x400d600180`.

- [ ] Build files, reload, compare every original cell to v3.0.1.
- [ ] Prove v3.0.1 files unchanged (SHA256 before/after).
- [ ] Commit unit 1.

## Unit 2 — M07 exact VA resolution

Files:
- `tools/mmu_formal_preflight.py`: `resolve_target_va()` precedence becomes
  explicit `TargetVAExact` -> numeric `TargetVA` -> unique embedded `0x...`
  token -> workload macro fallback; `load_samples()` cross-checks the new
  columns when present.
- `tools/tests/test_mmu_parameter_parity.py`: focused tests.

- [ ] Exact resolution for M07 R04/R05; R01-R03 and M03 R05 unchanged.
- [ ] Existing authority test passes.
- [ ] Commit unit 2.

## Unit 3 — M05 decoy VA in the formal command

Files:
- `tools/mmu_formal_runner.py`: load v3.0.2 parameter authority
  (`--param-authority`, default discovery next to the Excel); resolve
  `M05DecoyVA` / `M05DecoyTableBase` from the authority row; pass
  `--mmu_m05_decoy_va <value>` explicitly; fail closed on missing/zero/
  mismatch.
- Document `table_walker.cc:2979-3001` precedence: nonzero `decoy_va` selects
  the FORMAL path and forbids live-scan fallback.

- [ ] Describe M05 R01-R05 contains both flags and approved value.
- [ ] No `live_partial_scan` path possible from the emitted command.
- [ ] Commit unit 3.

## Unit 4 — parity gate and READY semantics

Files: `tools/mmu_formal_runner.py`.
Gate checks:
- global: authority row identity, seed gate, binary/source/workload hashes,
  control oracle, no seed flag.
- M05: DecoyVA present, equal to authority+pilot+W13, explicit flag present,
  table base explicit, no live-scan fallback.
- M07: exact target VA equal to authority+pilot, same 4 KiB page as the
  workload mapping base, target mode and target instruction equal to
  authority, `--mmu_target_n 12`, page-masked match key unchanged.
Status: READY only when every check passes; otherwise `PARITY_FAIL`
(exit 5) or `BLOCKED_PARITY_EVIDENCE_MISSING`.

- [ ] Describe exposes `parameter_parity` and `status=READY` only on pass.
- [ ] Commit unit 4.

## Unit 5 — audit harness

New `tools/mmu_final_runner_describe_audit.py`: drive 40 `--describe`
commands, capture raw JSON, validate every field in the task list, emit
M05/M07 parity reports, preflight report, provenance, git status/HEAD,
gem5 process check (before/after), output-directory integrity (before/after),
execution log, SHA256 manifest, CSV/JSON summaries and the v2 ZIP.

- [ ] Harness produces all 14 required artifacts.
- [ ] Commit unit 5.

## Unit 6 — final verification (no gem5)

- [ ] 40/40 READY, 0 BLOCKED, 0 PARITY_FAIL, 40/40 `would_run=false`.
- [ ] `pgrep -x gem5.opt` = 0 before and after.
- [ ] New formal output dirs = 0.
- [ ] Binary SHA unchanged.
- [ ] Build package and `.sha256`; list contents.
- [ ] Commit package artifacts and push to the non-main branch.
