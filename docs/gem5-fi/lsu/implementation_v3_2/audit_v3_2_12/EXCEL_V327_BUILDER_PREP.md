# EXCEL_V327_BUILDER_PREP — Task 19 prep (Excel v3.2.7 builder, tests, finalization plan)

Date: 2026-11-11. Worktree
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
(branch `lsu-platform-v3.2.12`, HEAD `eec513e5` at prep time).

Status: **builder + tests ready; v3.2.7 NOT published.** The v3.2.12
closure matrix is still the intermediate regeneration (it changed twice
during this prep: sha256 `e45c2b13…` -> `27f48841…`, RP01 still has no
row), so the published workbook must be built only after the final matrix
lands. This document records the exact finalization command and the
preconditions that must hold before it is run.

## 1. What was built (prep deliverables)

- `tools/build_lsu_v327_workbook.py` — extends the v3.2.6 builder
  pattern (two-end verification, frozen source, deterministic content):
  - reads the frozen
    `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx`
    (never writes it; refuses `--output == --source`);
  - derives every status from the closure matrix CSV passed via
    `--closure-matrix` — **no verdict is hand-typed anywhere**; models
    with no matrix row are recorded `PENDING_NO_ROW`;
  - adds sheet `22.v3.2.12传播链闭包矩阵` (the matrix rows verbatim,
    24 columns keyed `ModelID@BinarySHA256`, plus a derived per-model
    status mapping in sheet-3 model order);
  - adds sheet `21.v3.2.12变更记录` (change record; records the sha256
    of the matrix actually consumed, the regeneration precondition and
    the unchanged scope);
  - appends one ` | v3.2.12 audit: …` segment to the Notes cell
    (column R) of each of the 12 sheet-3 model rows — the v3.2.11
    precedent (additive evidence, no status column rewritten);
  - verifies the saved file: every other cell of the 20 pre-existing
    sheets byte-identical to v3.2.6, every highlight fill identical,
    the 60 identities intact, ConfigFrozen=NO, sheet 9 formal Status
    NOT_STARTED, audit rows byte-for-byte equal to the CSV.
- `tests/test_lsu_v327_workbook.py` — 10 tests that build a throw-away
  copy from the current matrix and assert all of the above, with the
  expected statuses re-derived independently from the same CSV (so the
  suite stays valid when the final matrix replaces the intermediate
  one). Result at prep time (temp-built from the current matrix,
  sha256 `27f48841…`):

  ```
  tests/test_lsu_v327_workbook.py::test_builder_self_check_and_pending_warning PASSED
  tests/test_lsu_v327_workbook.py::test_sheet_count_and_order PASSED
  tests/test_lsu_v327_workbook.py::test_43_columns_60_rows_identity_frozen PASSED
  tests/test_lsu_v327_workbook.py::test_formal_execution_not_started PASSED
  tests/test_lsu_v327_workbook.py::test_highlights_preserved PASSED
  tests/test_lsu_v327_workbook.py::test_only_sheet3_notes_differ PASSED
  tests/test_lsu_v327_workbook.py::test_audit_sheet_matches_csv_byte_for_byte PASSED
  tests/test_lsu_v327_workbook.py::test_audit_sheet_rollup_matches_csv_derivation PASSED
  tests/test_lsu_v327_workbook.py::test_changelog_records_provenance_and_preconditions PASSED
  tests/test_lsu_v327_workbook.py::test_deterministic_content PASSED
  ============================== 10 passed in 3.59s ==============================
  ```

  Regression (frozen inputs untouched):
  `pytest tests/test_lsu_v326_workbook.py tests/test_lsu_v326_audit.py`
  -> `14 passed in 4.92s`; the v3.2.6 xlsx sha256 is unchanged
  (`472628244c924859de4215f9d550141af9b8b0cc918ca744c1d6eb6131572d13`).

## 2. Exact finalization command

Run once ALL preconditions in §3 hold (the three flags equal the
builder's defaults, so the bare command is equivalent — explicit form
quoted for the record):

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
python3 tools/build_lsu_v327_workbook.py \
  --source docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx \
  --closure-matrix docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv \
  --output docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx
python3 -m pytest tests/test_lsu_v327_workbook.py -v
```

Expected builder output ends with (counts follow the final matrix):

```
verified: 12 Notes segments appended; <N> matrix rows byte-for-byte; 12 rollup rows; 5 change-log rows; highlights and identities intact
wrote docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx
```

If any model still lacks a matrix row at finalization time, the builder
prints the `not publishable` warning — do not publish until that is
either resolved or explicitly accepted and re-derived from the final
matrix.

## 3. Preconditions before the finalization command is run

1. **Final closure matrix landed.** The
   `LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv` currently on
   disk is the Task 16/17–intermediate regeneration (29 rows; RP01 has
   no row; A01/A03/SQ01/SQ03/SP05 re-run rows still being extended by
   Tasks 42–45; sha256 at prep time `27f488417d7557541d0217496eabe53a
   0dedcda3f38486eafc50f61dd1d9e3d`). Regenerate it with
   `tools/lsu_12model_closure.py` after the pilot re-runs and the RP01
   (Task 15) verdicts land, pass the runbook §5 checks 1–8 and the
   closure pytest suite, and only then build the workbook. The built
   workbook's `21.v3.2.12变更记录` sheet records the sha256 of the
   matrix it consumed — a published v3.2.7 must carry the FINAL
   matrix's sha there. If the matrix changes afterwards, delete the
   published v3.2.7 and rebuild; the builder always starts from the
   frozen v3.2.6, so regeneration is idempotent.
2. **Final binary SHA confirmed.** The final-candidate binary SHA is
   recorded as sha8 `68c6ce73` (full
   `68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`,
   `logs_v3_2_12/binary_v3212_final_candidate.sha256`). The matrix is
   keyed per `BinarySHA256`; confirm the final matrix's new rows are
   keyed to the confirmed final binary and that `build/ARM/gem5.opt`
   still hashes to it at build time. Verdicts are never merged across
   binaries, so this keying is what makes the workbook statuses
   attributable.
3. **W1–W8 rebaseline recorded.** Task 18's
   `audit_v3_2_12/W1_W8_Baseline_Map_v3.2.12.csv` (9 rows, W1–W8) must
   be final and the sample rows' `WorkloadPath`/`BinarySHA256`
   anchoring verified for the final binary. The builder preserves the
   60 sheet-5 rows by construction, so the rebaseline is a round-level
   precondition, not a workbook edit.
4. **Post-build validation.** `pytest tests/test_lsu_v327_workbook.py`
   must pass (it builds its own temp copy from the same matrix).
   `tools/check_v329_consistency.py` (plan Task 19 step 3: "or its
   successor") currently hardcodes the v3.2.5 workbook — repoint or
   replace it against v3.2.7 before citing it.
5. **Same round, same commit.** Task 19's `MODEL_STATUS_MATRIX.csv`
   refresh (PROPAGATION_VERIFIED flags from the final matrix) is a
   separate step of the same task; keep it derived-only and land it in
   the same commit sequence as the published workbook.

## 4. Scope guarantees (what the finalization will NOT do)

- Never modify the frozen v3.2.6 workbook or any historical Excel file
  (source is opened read-only in effect; `--output == --source` is
  refused; all v3.2.6 tests still pass).
- Never rewrite identity or freeze fields: the 60
  SampleRunID/RunID/SubTaskID/Seeds, ConfigFrozen=NO, Warm-up/ROI
  NEEDS_RESEARCHER_CONFIRMATION, sheet 9 formal Status NOT_STARTED, the
  RP01 DecisionStatus NEEDS_USER_DECISION, and every highlighted cell
  are preserved and post-verified.
- Never hand-type a verdict: statuses, counts and group verdicts are
  parsed from the closure matrix at build time; an unparseable
  `FinalClassification`, an empty CSV cell, a mixed-count that does not
  sum to `PilotCount`, or a matrix model absent from sheet 3 fails the
  build loudly.
