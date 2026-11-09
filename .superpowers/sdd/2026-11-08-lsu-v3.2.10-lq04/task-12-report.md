# Task 12 Report — Authoritative Excel v3.2.5 and the 12-model status matrix

**Date:** 2026-11-09
**Branch / HEAD:** `lsu-platform-v3.2.10` @ `6b52ab6e` (this task's code commit; base was `522aad45`)
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10`
**Deliverable:** `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx`
**SHA256 (v3.2.5 workbook):** `c429fb9388ccca57f3430bc0fc870b80d64e5d72dbcf156f642cb1157d205c6e`
**Authority transcribed:** `LQ04_Definition_Freeze_v3.2.10.md` (D1–D6) and
`LQ04_Propagation_Audit_v3.2.10.md` (§0 controller ruling, §5 verdicts).

---

## 1. What was built

- `tools/build_lsu_v325_workbook.py` — new builder following the
  `build_lsu_v324_workbook.py` pattern. Before writing anything it **verifies
  its inputs and aborts loudly on mismatch**: workload SHA256
  (`fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba`,
  re-hashed from `workloads/lq_lifetime_ordinal`), the golden oracle
  (`b097eb83f71545cb` present in `lq_lifetime_ordinal.golden`), and for each
  of the five pilots the `pilot_meta.json` identity (sample_run_id, ordinal
  used, workload path, the four required CLI flags, terminal MASKED,
  TRIGGERED, trace COMPLETE, oracle PASS). FullCommand is copied **verbatim**
  from each pilot's `command` argv — not reconstructed.
- `gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx` — generated from the
  committed v3.2.4 workbook; only LQ04 cells and a new revision sheet differ.
- `excel/60_SAMPLE_MATRIX.csv` — the derived round-trip copy of sheet 5
  (inspected first: the v3.2.4 builder itself rewrites this CSV, so the new
  builder rewrites it identically; the full-file sheet↔CSV equality is
  asserted by tests).
- `MODEL_STATUS_MATRIX.csv` — LQ04 row updated in place, **CRLF line endings
  preserved** (the file is uniformly CRLF; the builder replaces exactly the
  one matching old LQ04 line and fails if it does not find exactly one).
- `tests/test_lsu_v325_workbook.py` — 10 tests (TDD, written first).
- `tests/test_v328_consistency.py` — one-line collateral: `XL_LATEST` moved
  from v3.2.4 to v3.2.5 per that file's own documented convention
  ("the CSV must mirror the newest authoritative book"; the same pointer was
  moved v3.2.3→v3.2.4 when v3.2.9 superseded it).

## 2. TDD evidence

**RED** (test written first, before the builder; v3.2.5 did not exist and the
matrix still had the old LQ04 stages):

```
$ python3 -m pytest tests/test_lsu_v325_workbook.py -v
FAILED tests/test_lsu_v325_workbook.py::test_exactly_60_rows_and_identities_unchanged
FAILED tests/test_lsu_v325_workbook.py::test_lq04_rows_new_workload_identity_and_status
FAILED tests/test_lsu_v325_workbook.py::test_lq04_fault_definition_cells_unchanged
FAILED tests/test_lsu_v325_workbook.py::test_other_models_rows_identical
FAILED tests/test_lsu_v325_workbook.py::test_config_frozen_and_warmup_roi_unchanged
FAILED tests/test_lsu_v325_workbook.py::test_sheet3_lq04_status_and_others_unchanged
FAILED tests/test_lsu_v325_workbook.py::test_sheet4_lq04_hook_audit_and_others_unchanged
FAILED tests/test_lsu_v325_workbook.py::test_revision_sheet_exists
FAILED tests/test_lsu_v325_workbook.py::test_sample_csv_roundtrip_matches_lq04
FAILED tests/test_lsu_v325_workbook.py::test_model_status_matrix_lq04_and_others
============================== 10 failed in 2.15s ==============================
```

(One representative assertion body: `AssertionError: SOURCE_AUDITED
assert '0' == '1'` — the not-yet-updated matrix row.)

**Builder run (real output):**

```
$ python3 tools/build_lsu_v325_workbook.py
wrote .../excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx
wrote .../excel/60_SAMPLE_MATRIX.csv
updated .../MODEL_STATUS_MATRIX.csv
```

**GREEN:**

```
$ python3 -m pytest tests/test_lsu_v325_workbook.py -v
... 10 passed in 2.98s
```

**Unaffected regression:**

```
$ python3 -m pytest tests/test_lsu_v324_workbook.py -q
..... 5 passed in 1.42s
```

**Whole workbook-family suite** (v322/v323/v324/v325 + consistency + LQ04
platform):

```
$ python3 -m pytest tests/test_lsu_v322_workbook.py tests/test_lsu_v323_workbook.py \
    tests/test_lsu_v324_workbook.py tests/test_lsu_v325_workbook.py \
    tests/test_v328_consistency.py tests/test_lq04_platform.py -q
...................................  35 passed in 7.25s
```

(`test_v328_consistency.py::test_csv_mirrors_sheet5` initially failed with the
CSV pointing at v3.2.5 and `XL_LATEST` still at v3.2.4 — fixed by the
documented pointer move above; that is the only collateral test change.)

## 3. Change scope (independently re-verified, not just via the tests)

Full sheet-by-sheet cell diff v3.2.4 → v3.2.5 (openpyxl, all cells):

- 16 of 17 pre-existing sheets **UNCHANGED** (sheets 1, 2, 6, 7, 8, 9, 10,
  11, 12, 13, 13.v3.2.1, 14, 15, 17 — plus nothing else).
- Sheet `3.最终12模型矩阵`: exactly **4 cells** differ, all row 4 (LQ04):
  WorkloadName, ImplementationStatus, OverallStatus, Notes.
- Sheet `4.源码Hook审计`: exactly **4 cells** differ, all row 4 (LQ04):
  RequiredSourceChange, ExistingHook, ImplementationStatus, Evidence.
- Sheet `5.60个样本执行矩阵`: exactly **60 cells** differ = 12 fields × the
  5 LQ04 rows (12–16), and per-model census of changed columns reports
  `LQ04 -> [BinaryPath, BinarySHA256, DecisionStatus, ExecutionStatus,
  FaultActivationStatus, FullCommand, Oracle, RunStatus, TerminalState_v31,
  TraceCompleteness_v31, WorkloadPath, v3.2_ConfigProvenance]` with
  `models with changes: ['LQ04']`.
- New sheet `18.v3.2.10变更记录` (18 sheets total).
- `MODEL_STATUS_MATRIX.csv`: one line changed (`git diff` shows only the LQ04
  row; other 11 rows byte-identical, CRLF intact).
- `60_SAMPLE_MATRIX.csv`: 5 data lines changed (the LQ04 rows).

## 4. LQ04 row dump (v3.2.5, read back with openpyxl `data_only=True`)

### Sheet 3 `3.最终12模型矩阵` row 4 (changed fields)

```
WorkloadName:         'lq_lifetime_ordinal'
WorkloadStatus:       'READY'
ImplementationStatus:'PILOT_IMPLEMENTED_VERIFIED_F0 (literal _valid/_request clear; boundary restore; MASKED 5/5)'
OverallStatus:        'PILOT_RUN_MASKED_5/5'
Notes:                'literal semantics accepted by the researcher 2026-11-08; response binds via pkt->senderState, no response loss; expected MASKED confirmed 5/5; ordinal anchors 1-5 (lq_lifetime_ordinal); PROPAGATION_VERIFIED=0 (LIFECYCLE_ONLY, no SDC)'
```
(Unchanged in that row: Unit, FaultType, SubTaskID, RunID, InjectionMode,
WorkloadID, FaultLocation, TargetField, ResearchQuestion,
ExpectedPropagation, ExpectedObservation, SourceAuditStatus, FaultConfigID,
BitEntryByteIndex, NormalValue, FaultValue, DecisionNeeded, Options,
Recommended, DecisionStatus — the frozen fault definition is intact.)

### Sheet 4 `4.源码Hook审计` row 4 (changed fields)

```
ExistingHook:         'CHAOSLQ04'                                   (was '无')
RequiredSourceChange: 'implemented: CHAOSLQ04 SimObject + LQEntry side channel + executeLoad hook'
ImplementationStatus:'IMPLEMENTED_VERIFIED'                          (was 'NEEDS_HOOK')
Evidence:             'CHAOS/gem5/src/cpu/o3/lsq_unit.cc; CHAOS/gem5/src/cpu/o3/lsq_unit.hh; CHAOS/gem5/src/cpu/o3/CHAOSLQ04/; lsq_unit.hh side channel; pilots_v3_2_10'
```
(Unchanged: TargetField, both NormalValue columns, both FaultValue columns,
InjectionTiming, Duration, and every other definition cell.)

### Sheet 5 `5.60个样本执行矩阵` rows 12–16 (all five share; R01 shown, R05 differs only in ID/Seed/Ordinal/paths-for-R05)

```
SampleRunID:            'LQ04-F0-W2-S01-R01'  (R02..R05 analogous; seeds 1842987246 / 2188214204 / 3953171871 / 4153250964 / 3410523942 unchanged)
EventOrdinal:           1 .. 5 (unchanged)
WorkloadPath:           '/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10/docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal'
BinaryPath:             (same new path; see concern C1)
BinarySHA256:           'fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba'
Oracle:                 'b097eb83f71545cb'
FullCommand:            '/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10/build/ARM/gem5.opt --outdir=.../pilots_v3_2_10/LQ04-R01 .../configs/se/lsu_proxy.py --cmd=.../workloads/lq_lifetime_ordinal --cpu O3 --variant B0 --probability 1.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz --chaos_lq04 --lq04_event_ordinal 1 --lq04_max_faults 1 --lq04_watchdog_cycles 500000000'
ExecutionStatus:        'PILOT_RUN'
RunStatus:              'PILOT_MASKED'
FaultActivationStatus:  'TRIGGERED'
TerminalState_v31:      'MASKED'
TraceCompleteness_v31:  'COMPLETE'
EvidencePath:           'runs/lsu/final/LQ04-F0-W2-S01-R01/'   (pattern unchanged)
DecisionStatus:         'ACCEPTED_BY_RESEARCHER_2026-11-08'
ConfigFrozen:           'NO'                                     (all 60 rows)
WarmUp / ROI:           'NEEDS_RESEARCHER_CONFIRMATION'         (all 60 rows, unchanged)
v3.2_ConfigProvenance:  '<v3.2.4 text unchanged>; v3.2.10 LQ04 pilot round (accepted by researcher 2026-11-08): literal definition executed per LQ04_Definition_Freeze_v3.2.10.md D1-D6 - literal _valid/_request cleared at executeLoad_post (no pop, no reuse) with boundary restore at commit/squash; ordinal anchors 1-5 via workload lq_lifetime_ordinal and --lq04_event_ordinal (D3/D4, supersedes the seeded-tier note above for LQ04); propagation grading per LQ04_Propagation_Audit_v3.2.10.md: MASKED 5/5, TraceCompleteness COMPLETE, PropagationCoverage LIFECYCLE_ONLY, PROPAGATION_VERIFIED=0, no SDC; response binds via pkt->senderState (no response loss); see pilots_v3_2_10;'
```

### MODEL_STATUS_MATRIX.csv row 12

```
LQ04,LQ,lifetime,1,1,1,1,1,1,0,v3.2.10: literal fields cleared; boundary restore; 5/5 pilots MASKED; consumers correct data (no corrupting propagation); no SDC
```
(Stages: DESIGNED=1, SOURCE_AUDITED=1, IMPLEMENTED=1, COMPILED=1,
UNIT_TESTED=1, PILOT_RUN=1, **PROPAGATION_VERIFIED=0** — the audit grading,
not the structural tool label. Other 11 rows untouched.)

### New sheet `18.v3.2.10变更记录`

Item/Change/Reason table with 11 rows: workload identity (D3), BinaryPath
alignment, FullCommand (real command), sample statuses, sheet 3 changes,
sheet 4 changes, matrix stages, the per-pilot audit verdicts
(RecordIntegrity VALID / TraceCompleteness COMPLETE / PropagationCoverage
LIFECYCLE_ONLY / PROPAGATION_VERIFIED=0 / SDC no / MASKED), the five matched
controls, the D6 identity freeze, and the unchanged-scope statement.

## 5. Files changed (commit 6b52ab6e)

- `tools/build_lsu_v325_workbook.py` (new)
- `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx` (new)
- `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` (derived)
- `docs/gem5-fi/lsu/implementation_v3_2/MODEL_STATUS_MATRIX.csv` (LQ04 row)
- `tests/test_lsu_v325_workbook.py` (new)
- `tests/test_v328_consistency.py` (XL_LATEST pointer, one line)

## 6. Self-review

- The task's enumerated field lists were followed exactly for sheets 3/4/5;
  the frozen LQ04 fault definition (TargetField, NormalValue, FaultValue,
  InjectionTiming, FaultDuration, and the duplicate definition columns in
  sheet 4) is bit-identical to v3.2.4 — asserted by
  `test_lq04_fault_definition_cells_unchanged` and the sheet-4
  only-four-cells-may-diff assert.
- All 60 identities (SampleRunID/RunID/SubTaskID/Seed) are unchanged;
  ConfigFrozen is NO for all 60; WarmUp/ROI are unchanged — asserted
  cell-by-cell against v3.2.4.
- Every other model's rows are identical to v3.2.4 in sheets 3, 4 and 5
  (row-tuple comparison) and in MODEL_STATUS_MATRIX.csv (literal expected
  rows embedded in the test).
- The propagation grading follows the audit's controller ruling (§0):
  PROPAGATION_VERIFIED=0 with LIFECYCLE_ONLY, not the tool's structural
  COMPLETE label; no SDC claim anywhere.
- The builder is idempotent against its committed inputs and fails loudly
  (SystemExit) on any workload/pilot/verdict mismatch, so a stale or tampered
  input cannot silently produce a "verified" workbook.
- Explicit `git add` of six paths only; no `git add -A`; no Co-Authored-By
  trailer.

## 7. Concerns

- **C1 — BinaryPath was updated (small, disclosed deviation beyond the
  enumerated sheet-5 list).** The task enumerated WorkloadPath/SHA/Oracle but
  not BinaryPath. Leaving BinaryPath at the old `lq_lifetime` while
  BinarySHA256 names `lq_lifetime_ordinal` would make the row internally
  inconsistent (a false record). D6 authorizes "LQ04's workload
  path/SHA/Oracle/status cells"; BinaryPath is a workload-path cell. The
  change is recorded in revision-sheet row 2. (FW05's rows keep a stale
  BinaryPath from v3.2.3 — pre-existing, untouched.)
- **C2 — PreflightStatus stays `BLOCKED_NO_HOOK` on the LQ04 rows** (not in
  the task's enumerated list; FW05/SQ03/SP05 pilot rounds kept theirs too).
  The label is stale wording, but the formal preflight/Gates have genuinely
  not run; the revision sheet states this explicitly ("Formal preflight /
  Gate 4 has not run; the pilots are not the formal 60-sample campaign").
- **C3 — Sheet 3/4 DecisionStatus cells remain `NEEDS_USER_DECISION`** (the
  task enumerated DecisionStatus only for sheet 5, where it is
  ACCEPTED_BY_RESEARCHER_2026-11-08). The researcher acceptance is recorded
  in sheet 3 Notes, sheet 5 DecisionStatus, the provenance cell and the
  revision sheet. If the controller wants the sheet 3/4 cells flipped too,
  that is a one-cell-each follow-up.
- **C4 — Sheet 6 (工作负载及无故障基线) row 3 still describes W2/lq_lifetime
  with the old SHA/oracle.** Out of the task's enumerated sheet scope; D3
  keeps the original workload archived, so the row remains factually true as
  the archived-original record. A future round may want a W2 row for
  `lq_lifetime_ordinal`.
- **C5 — `OutputDir` and `gem5Commit` cells unchanged** (not enumerated):
  OutputDir still points at the legacy v3.2 worktree runs path, and
  gem5Commit is the uniform repo-level value `6f98088a…` shared by all 60
  rows. The real pilot outdir is preserved verbatim in FullCommand.
- **C6 —** `tests/test_lq04_platform.py` still pins
  `run_pilot.EXCEL.name.endswith("-v3.2.4.xlsx")` — intentionally untouched:
  the pilots' frozen identity source is the v3.2.4 workbook (they were
  produced against it); v3.2.5 is the publication of those results.
