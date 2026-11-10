# CLOSURE_INPUTS_v3.2.12.md — input checklist for Tasks 16–20

Prepared by the evidence-verification / closure-prep agent, 2026-11-10.
Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`,
branch `lsu-platform-v3.2.12`, HEAD `778abce1667a448e1e7fc00d70fa5319ae82476b`.
This document inventories every record set, column source, command, and
entry point Tasks 16–20 consume, and states what is still missing. All facts
below were verified with real commands on 2026-11-10 (see
`.superpowers/sdd/2026-11-10-lsu-v3-2-12-propagation-closure/task-prep-report.md`).

---

## 0. Shared preconditions (state at prep time)

| Item | Verified state |
|---|---|
| Branch / HEAD | `lsu-platform-v3.2.12` @ `778abce1` (clean at HEAD) |
| Concurrent WIP in this worktree (uncommitted, A03 owner) | `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc`, `.hh`, `tests/test_addrpath_a01_coords.cc` |
| `build/ARM/gem5.opt` SHA256 | `e527f26af7c2661995f456a2c96695ff6b366d5d787351172947ed259fad04ed` (both copies identical; Task-1 baseline build, mtime 2026-11-10 10:17/10:21) |
| **Binary staleness** | The binary predates the committed v3.2.12 trace code: A01 `3d7b11c5` (CHAOSAddrPath) and FWD-SQ `7c67fa99` (CHAOSLSQFwd + CHAOSPropagation) landed *after* the build. `fw02_decision` / `sq01_chain` / `sq03_effect` / `sp05_stage` / `a01_ea` trace nodes are **not** in the current binary. **Tasks 11–15 pilots and Task 18 baselines require a rebuild first** (`scons -j126`, publish to repo root, record both SHAs in `GIT_COMMIT_v3212.txt`). |
| Disk gate | `df -h /home` → 72G available (≥ 70.6 GiB threshold), 79% used |
| Canonical unaffected regression | `build/ARM/gem5.opt --outdir=/tmp/<d> configs/se/arm_chaos.py --cmd workloads/directed/reg_chain --cpu O3` → golden `f247ef3fe6f02cfd`, exit 0 |

---

## 1. Task 16 — unified 12-model closure matrix + per-model summaries

**Outputs to create:** `audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix.csv`,
`audit_v3_2_12/LSU_12Model_Propagation_Closure_Summary_v3.2.12.md`.

### 1.1 Tool and commands (exact)

```bash
# per model: build per-pilot records
python3 tools/lsu_12model_closure.py record --model <M> \
  --pilot-dir <dir> [--pilot-dir ...] --json audit_v3_2_12/<M>_records_v3.2.12.json \
  [--binary-sha <final binary SHA256>]
# then: one row per model
python3 tools/lsu_12model_closure.py matrix \
  --records audit_v3_2_12/<M>_records_v3.2.12.json [--records ...] \
  --out audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix.csv
```

`record` flags: `--model` (required), `--pilot-dir` (repeatable, required),
`--json`, `--binary-sha` (purity check — pass the final binary SHA so
mixed-binary pilots are split, never merged). `matrix` / `features` consume
the record JSONs.

### 1.2 Matrix column source (24 columns, brief §11)

`CLOSURE_MATRIX_COLUMNS` at `tools/lsu_12model_closure.py:141-151` — the 20
v3.2.11 audit-matrix columns (`EvidencePaths` renamed `EvidencePath`) plus
`RecordIntegrity`, `TraceCompleteness`, `StructuralChainCompleteness`,
`FaultEffectPropagationCoverage`, `ObservedTerminal`, `ApplicationOracle`,
`FaultCausality`, `FinalClassification`, `MissingEvidence`,
`SupplementaryPilotRequired`, `EvidencePath`:
`ModelID, SubUnit, FaultDefinition, PilotCount, InjectionVerified,
ActivationVerified, EarlyAnomalyVerified, IntermediatePropagationVerified,
RegisterWritebackVerified, ConsumerVerified, CommitVerified,
TerminalVerified, OracleVerified, RecordIntegrity, TraceCompleteness,
StructuralChainCompleteness, FaultEffectPropagationCoverage,
ObservedTerminal, ApplicationOracle, FaultCausality, FinalClassification,
MissingEvidence, SupplementaryPilotRequired, EvidencePath`.
Writer raises on empty cells / bare `PASS` / `COMPLETE_CAUSAL_CHAIN` with
`InjectionVerified=no`. Verdicts are tool-computed only — never hand-set.

### 1.3 Record sets ALREADY PRESENT (verified)

| Record set | Location | Count |
|---|---|---|
| Historical pilot roots | `pilots_v3_2_1`(15) `pilots_v3_2_2`(7) `pilots_v3_2_3`(8) `pilots_v3_2_4`(15) `pilots_v3_2_5`(11) `pilots_v3_2_6`(13) `pilots_v3_2_7`(12) `pilots_v3_2_8`(6) `pilots_v3_2_9`(2, SQ03-PROBE) `pilots_v3_2_10`(10) | 99 dirs |
| v3.2.12 SUPP oracle pilots | `pilots_v3_2_12/SUPP-DA04-R04,R05`, `SUPP-LP01-R01..R05`, `SUPP-MD04-R02,R03,R05`, `SUPP-FW05-R02..R05` | 14 dirs |
| SUPP oracle manifest | `audit_v3_2_12/SUPPLEMENTARY_ORACLE_MANIFEST_v3.2.12.csv` | 14 rows (DA04 FAIL/FAIL, LP01 PASS observed) |
| LQ04 verdict (already adjudicated COMPLETE_CAUSAL_CHAIN / MASKED via senderState) | `audit_v3_2_12/LQ04_verdict_v3.2.12.json` + `LQ04_Propagation_Audit_v3.2.12.md` | 5 pilots |
| Missing-evidence matrix (root-cause baseline) | `audit_v3_2_12/MissingEvidenceMatrix.csv` + `.md` | 194 rows — per model: A01 12, A03 24, FW02 13, SQ01 35, DA04 18, LP01 11, MD04 34, FW05 20, SQ03 15, LQ04 10, SP05 1, RP01 1 |
| Acceptance standard / schema (enum authority) | `LSU_Propagation_Acceptance_Standard_v3.2.12.md`, `audit_v3_2_12/pilot_record.schema.md` | — |

### 1.4 Record sets STILL MISSING (produced by Tasks 7–15 before Task 16 can run)

| Model | Missing record set | Owning task |
|---|---|---|
| A01 | `SUPP-A01-R01..R05` + matched controls; **also the `a01_ea`/`a01_consumed` prop-trace sink in CHAOSPropagation + 2 read-only `lsq.cc` call-site lines (task-7 handoff, NOT yet landed)** | Task 7 (in progress) |
| A03 | `SUPP-A03-R01..R05` + controls; a03 stream records (WIP in this worktree, uncommitted) | Task 8 |
| FW02 | `SUPP-FW02-R01..R05` (trace code landed `7c67fa99`, pilots not run) | Task 9 (in progress) |
| SQ01 | `SUPP-SQ01-R01..R05` on `sq_reload_v3212` (trace code landed, pilots not run) | Task 11 |
| SQ03 | `SUPP-SQ03-R01..R05` on `sq_reload_v3212` | Task 12 |
| SP05 | `SUPP-SP05-R01..R05` on `sq_reload_v3212` | Task 13 |
| RP01 | `RP01_CountOnly_Preflight_v3.2.12.csv` (Task 14) + `RP01-R01..R05` and `RP01-CONTROL-R01..R05` (Task 15); selector host test landed (`778abce1`), simulator wiring in progress in an isolated worktree | Tasks 14–15 |
| All of the above | **Rebuilt final binary** + its SHA recorded | global precondition |

### 1.5 Acceptance arithmetic (Task 16 Step 2)

Count models with ≥2 complete contexts; list the terminal distribution;
flag any model whose only chain is single-context (`VERIFIED_SINGLE_CONTEXT`
must not be upgraded). Numbers must be derived from the matrix CSV, not from
historical summaries (v3.2.11 audit sheet values are superseded).

---

## 2. Task 17 — diagnostic feature dataset

**Output:** `audit_v3_2_12/LSU_12Model_Diagnostic_Feature_Dataset.csv`.

```bash
python3 tools/lsu_12model_closure.py features \
  --records <record JSONs> --out audit_v3_2_12/LSU_12Model_Diagnostic_Feature_Dataset.csv
```

- **Column source (five feature groups, brief §12):** `FEATURE_GROUP_COLUMNS`
  at `tools/lsu_12model_closure.py:156-176` —
  (1) provenance/identity: `ModelID, PilotID, SampleRunID, Seed, EventOrdinal,
  BinarySHA256, WorkloadSHA256, EvidencePath, RowKind, FragmentOrdinal,
  FragmentStage, FragmentEventID, SupplementaryOf`;
  (2) injection site: `PrimaryFaultModel, InjectionSeq, InjectionPC,
  InjectionTick, ActivationStatus, InjectionCount`;
  (3) chain path: `ChainEventCount, ChainEdgeCount, EarliestAnomalyType,
  EarliestAnomalyEventID, WritebackValueFnv, ConsumerInputFnv,
  ConsumerSourceLinked, CommitSeq`;
  (4) outcome: `ObservedTerminal, TerminalReason, ApplicationOracle,
  OracleExpected, OracleActual`;
  (5) verdict: `RecordIntegrity, TraceCompleteness,
  StructuralChainCompleteness, FaultEffectPropagationCoverage, FaultCausality,
  FinalClassification, MissingEvidence`.
- One row per pilot (`RowKind=PILOT`) then per path fragment
  (`RowKind=PATH_FRAGMENT`) in canonical chain order; `EventOrdinal` is the
  pilot's frozen ordinal on every row and must stay monotonic per pilot.
- **Verification:** no blank cells (literal `NULL`/`NOT_APPLICABLE` only);
  every row has `ModelID, PrimaryFaultModel, InjectionTick, ObservedTerminal`;
  `LIFECYCLE_ONLY` rows carry `NOT_APPLICABLE` (never zeros) for
  consumer/commit fields.
- Inputs: the same record JSONs as Task 16 — nothing extra; dataset cannot be
  generated until 1.4 is closed.

---

## 3. Task 18 — W1–W8 no-fault baselines + full test suite on the final binary

**Outputs:** `logs_v3_2_12/baselines_w1_w8/` (one subdir per workload) +
`baselines_w1_w8/BASELINE_SUMMARY.csv`.

### 3.1 Mapping source (frozen)

- Authoritative: workbook sheet `5.60个样本执行矩阵` in
  `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx`
  (`SampleRunID` col A, format `*-W<n>-*`; `WorkloadPath` col S;
  `BinarySHA256` col T = workload ELF SHA; `Oracle` col V).
- Frozen extraction: **`audit_v3_2_12/W1_W8_Baseline_Map_v3.2.12.csv`** —
  9 rows (W1–W7 one workload each; **W8 spans two workloads**), 60 frozen
  SampleRunIDs, every binary SHA recomputed and **matching** the workbook,
  every golden file **matching** the workbook Oracle:

| W | Workload | Models | #SRIDs | golden |
|---|---|---|---|---|
| W1 | `workloads/agu_addrmodes` | A01, A03 | 10 | `728e604ffcec539d` |
| W2 | `workloads/lq_lifetime_ordinal` | LQ04 | 5 | `b097eb83f71545cb` |
| W3 | `workloads/sq_drain` | SQ01, SQ03 | 10 | `ba3b3185e541ad03` |
| W4 | `workloads/sq_forward` | FW02 | 5 | `1f4cbf14327717df` |
| W5 | `workloads/load_response` | LP01 | 5 | `99c106541150be0e` |
| W6 | `workloads/store_path` | SP05 | 5 | `2543a2a60de01795` |
| W7 | `workloads/replay_dependency` | MD04, RP01 | 10 | `59fc61c040618747` |
| W8a | `FW05_Workload_Archive/bin/fw05_forward` | FW05 | 5 | `67afad307642983e` (golden in `FW05_Workload_Archive/golden/`) |
| W8b | `workloads/alignment` | DA04 | 5 | `3f89eab79392ce69` |

Caveats recorded in the CSV NOTES: workbook paths are anchored at the
`lsu-platform-v3.2` worktree (W2 at `lsu-platform-v3.2.10`) — re-anchor the
`--cmd` path to this worktree when running (file contents identical, SHAs
verified); `lq_lifetime_ordinal.golden` and `store_path.golden` and
`alignment.golden` use a `checksum=0x…` prefix format while the others are
bare hex; `sq_reload_v3212` (golden `7df5034c23f3e703`) is a supplementary
workload for SUPP-SQ01/SQ03/SP05 pilots and is **not** part of W1–W8.

### 3.2 Baseline command per W (on the FINAL rebuilt binary)

```bash
build/ARM/gem5.opt --outdir=docs/gem5-fi/lsu/implementation_v3_2/logs_v3_2_12/baselines_w1_w8/<W> \
  configs/se/lsu_proxy.py --cpu O3 --cmd=<WorkloadPath_v3_2_12 from the map CSV>
```

Expected per row: printed checksum equals the frozen golden, exit 0, oracle
PASS. Record exit code, binary SHA, workload SHA per row into
`BASELINE_SUMMARY.csv` (columns should mirror the map CSV plus
ActualChecksum, ExitCode, BinarySHA256, RunDate).

### 3.3 Full test suite (Task 18 Step 3)

```bash
pytest tests/ -q                                        # repo tests, expect 0 failures
pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/ -q   # 13 platform test files
```

Platform tests present: `test_config_parser.py, test_context_sweep.py,
test_cross_attempt_chain.py, test_fault_manager.py, test_manifest_oracle.py,
test_md04_trace_fields.py, test_prop_converter.py, test_terminal.py,
test_terminal_rules.py, test_trace.py, test_trace_chain_integrity.py,
test_trace_coverage.py, test_v323_judgment.py`.
Also keep the canonical `reg_chain` golden `f247ef3fe6f02cfd` check (§0).

### 3.4 Still missing for Task 18

`baselines_w1_w8/` directory and `BASELINE_SUMMARY.csv` do not exist yet
(to be created by Task 18); the final rebuilt binary (§0).

---

## 4. Task 19 — Excel v3.2.7, MODEL_STATUS_MATRIX, 60-sample freeze audit

**Outputs:** `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`,
updated `MODEL_STATUS_MATRIX.csv`, new `tools/update_lsu_v327_audit.py`,
new `tests/test_lsu_v327_workbook.py`.

### 4.1 Entry points (verified to exist)

- Base workbook: `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx`
  — 20 sheets (listed in the prep report), sheet 5 header = **43 columns**
  (`SampleRunID` … `v3.2_ConfigProvenance`).
- Predecessor audit-sheet builder: `tools/update_lsu_v326_audit.py`
  (v3.2.11 pattern: add sheet `20.v3.2.11传播链审计`, append verdicts to
  sheet-3 Notes col R, append change rows to sheet `19.v3.2.11变更记录`;
  every other cell keeps its v3.2.5/v3.2.6 value). Create the v3.2.7
  successor along this pattern; do not fork the classifier.
- Workbook builder predecessors: `tools/build_lsu_v322_workbook.py` …
  `tools/build_lsu_v326_workbook.py` (if a full rebuild is preferred).
- CSV twin: `excel/60_SAMPLE_MATRIX.csv` (same 43-column layout as sheet 5).
- Consistency script: `tools/check_v329_consistency.py` (currently checks
  Excel **v3.2.5** vs the CSV vs FW05 archive SHA
  `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` vs
  `pilots_v3_2_9`); tests `tests/test_v328_consistency.py`,
  `tests/test_v329_consistency.py`. Task 19 Step 3 requires running it or a
  successor that targets the v3.2.7 workbook.
- Existing workbook tests to model on: `tests/test_lsu_v322_workbook.py`,
  `test_lsu_v323_workbook.py`, `test_lsu_v324_workbook.py`,
  `test_lsu_v325_workbook.py`, `test_lsu_v326_workbook.py`,
  `test_lsu_v326_audit.py`.

### 4.2 Required invariants (Task 19 Step 1 test)

Sheet count and 43-column sheet-5 header unchanged; highlighted cells
preserved; 60 SampleRunIDs/Seeds byte-identical to v3.2.6; per-model verdict
columns equal the Task 16 closure matrix **by key**; `ConfigFrozen=NO`;
formal `ExecutionStatus=NOT_STARTED`; `DecisionStatus` not silently flipped.
`MODEL_STATUS_MATRIX.csv` (11 columns: `model, unit, stage, DESIGNED,
SOURCE_AUDITED, IMPLEMENTED, COMPILED, UNIT_TESTED, PILOT_RUN,
PROPAGATION_VERIFIED, evidence`) updated only from tool-derived verdicts.

### 4.3 Still missing for Task 19

`tools/update_lsu_v327_audit.py` (or extension), `tests/test_lsu_v327_workbook.py`
(absent today — verified), the Task 16 closure matrix it consumes, and a
consistency-script decision (extend `check_v329_consistency.py` to v3.2.7 or
add a `check_v3212_consistency.py` successor).

---

## 5. Task 20 — package, final acceptance report, blockers

**Outputs:** `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.12_Final_Acceptance_Report.md`,
`LSU_v3.2.12_12Model_Propagation_Closure_Package.zip`,
`docs/gem5-fi/lsu/implementation_v3_2/DELIVERABLES_SHA256_v3212.txt`.

- **13-question report (brief §16):** every number must come from the Task 16
  matrix; any model below `COMPLETE_CAUSAL_CHAIN` stated honestly with the
  minimal fix. Record final git state (branch, HEAD, status, binary SHA,
  disk free) in the report.
- **20-item ZIP (brief §15):** must not include `build/`, `.git/`, or
  superseded packages; verify with `unzip -t`, file count, `sha256sum`; no
  historical file overwritten.
- **Candidate item inventory already on disk** (the exact 20-item list is
  defined by the researcher brief, which is NOT checked into the repo):
  acceptance standard; pilot-record schema; closure matrix CSV; closure
  summary MD; feature dataset CSV; MissingEvidenceMatrix CSV+MD; 12
  per-model audit reports (LQ04 done; A01/A03/FW02/SQ01/SQ03/SP05/RP01
  pending; DA04/LP01/MD04/FW05 re-adjudication from the SUPP manifest);
  LQ04 verdict JSON; SUPPLEMENTARY_ORACLE_MANIFEST; W1_W8_Baseline_Map CSV;
  baselines BASELINE_SUMMARY; RP01 preflight CSV; workbook v3.2.7;
  MODEL_STATUS_MATRIX.csv; final report; DELIVERABLES_SHA256.
- **Open input:** the main agent holding the researcher's frozen v3.2.12
  brief must supply the verbatim §15 item list and §16 question list —
  they are not in the repository (only the plan references them).
- **Still missing:** everything downstream of Tasks 16–19.

---

## 6. Cross-cutting constraints (carry into every closure task)

1. **Binary purity:** every pilot/baseline records its own `BinarySHA256` and
   `WorkloadSHA256`; the closure tool splits verdicts by binary SHA — never
   merge traces from two binaries. Rebuild before any new pilot/baseline.
2. **No hand-set verdicts:** all classifications come from
   `tools/lsu_12model_closure.py`; `ConfigFrozen=NO`; formal
   `ExecutionStatus=NOT_STARTED`.
3. **Never modify** a frozen SampleRunID, Seed, Oracle, golden value, or any
   historical pilot/trace/ZIP; new outputs go to `*_v3_2_12` namespaces.
4. **Disk gate:** no pilot may start while `/home` free < 70.6 GiB.
5. **Concurrency:** A03 WIP is uncommitted in this worktree (see §0); RP01
   simulator wiring is being implemented in an isolated worktree — rebase
   order and rebuild timing must be coordinated by the main agent before
   Task 18's "final binary" is declared.
