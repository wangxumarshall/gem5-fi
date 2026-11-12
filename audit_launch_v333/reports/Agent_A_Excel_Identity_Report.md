# Agent A — Excel / SampleRunID / Seed Identity Audit (LSU v3.3.3)

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Git HEAD at audit:** `b8405580b09e9d85c59af0b64ed2215aba41a95a` (branch `lsu-v3.3.1-context-workload-20261111`)
**Mode:** read-only. No Excel/runner/source/artifact written; no gem5/scons run. The only file written is this report.
**Tools:** `sha256sum`, `unzip -l`, openpyxl (read-only), `csv`/`json`/`hashlib`/`re` via `python3`.

**Inputs audited**

- `audit_v3_3_3/README_GROUND_TRUTH.md`
- `audit_v3_3_3/LSU_v3.3.3_Final_Acceptance_Report.md`
- `audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx`
- `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv`
- `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`
- `audit_v3_3_3/LSU_60Context_Final_Readiness.csv`
- `audit_v3_3_3/LSU_60Context_Causal_Propagation.csv`
- `audit_v3_3_3/runs/<MODEL>-R<NN>-{fault,control}/` (120 dirs)
- `audit_v3_3_3/LSU_v3.3.3_Master_Defect_Ledger.csv`, `audit_v3_3_3/decisions/LSU_v3.3.3_Researcher_Approval.md`
- `tools/lsu_v333_workbook.py`, `tests/test_lsu_v333_workbook.py`

---

## 0. Verdict summary

| # | Check | Verdict |
|---|---|---|
| 1 | Authoritative 60 SampleRunID + Seed used by workbook/manifest; list mismatches | **PASS for the workbook (60/60), FAIL for the run artifacts (0/120 carry the authoritative ID), PARTIAL for `ROI_Context_Mapping` (authoritative ID + intentional `V332-*` source column)** |
| 2 | 60/60 IDs unique; fault & control share SampleRunID and Seed | **PASS** |
| 3 | 60/60 seeds non-empty, match the frozen matrix, match `command.txt`/`pilot_meta.json` | **FAIL — 5/60 fault rows (LQ04) executed with injector seed 0, not the frozen seed; 30/120 commands carry no seed flag (25 of those are `INJECTOR_ABSENT` controls where the seed has no effect)** |
| 4 | Oracle block per context (type/golden, fault output, control output, expected vs actual terminal, evidence); SDC/MASKED/HANG; normal exit not PASS | **FAIL on completeness (no actual-output or expected-terminal columns), PASS on classification integrity** |
| 5 | Config completeness; every blank critical field marked PASS | **FAIL — 10 rows have `DynInstSeq=PENDING`, 5 have `PC=PENDING`, all 60 marked `ExecutionStatus=MEASURED_TERMINAL` and `Readiness_Gate=PASS`; `ConfigSHA256` and `ExpectedTerminal` are absent columns** |
| 6 | Proposed `LSU_Formal_Experiment_Config_Final.xlsx` layout + minimal generator change | **Delivered below (not generated)** |

**Bottom line:** the authoritative identity is correct **inside the workbook** (60/60 SampleRunID, 60/60 Seed, 60/60 unique, 60/60 pairs), and the terminal/oracle classification is internally consistent (43 SDC / 12 MASKED / 5 HANG; 60/60 control oracle PASS based on checksum, not exit code). The defects are in **provenance and completeness**: LQ04 fault runs did not receive their frozen seed (actual `rngSeed=0`), 10 rows carry `PENDING` identity fields while being marked MEASURED/PASS, the workbook has no per-row `ConfigSHA256`, no expected-terminal, and no actual fault/control checksum columns, and several packaged CSVs still contradict the approved state (`CANDIDATE_PENDING_APPROVAL`, `NEEDS_USER_DECISION`, stale A01 terminal wording). The v3.3.3 summary's claim "no blank critical field marked PASS" is **false** under the field list in this audit; it is only true for the four columns hard-coded in `enforce_no_blank_pass`.

---

## 1. Check 1 — authoritative identity and mismatches

### 1.1 Frozen sources agree with each other

`60_SAMPLE_MATRIX.csv` and the v3.2.7 workbook sheet `5.60个样本执行矩阵` agree on all 60:

```
v3.2.7 matrix rows 60 cols 43
v3.2.7 unique ids 60
CSV ids not in v3.2.7: []
v3.2.7 ids not in CSV: []
seed mismatches CSV vs v3.2.7: 0
```

The frozen matrix contains 60 rows, 60 unique `SampleRunID`, 60 unique seeds, no empty seed, and no non-conforming ID (all match `^[A-Z0-9]+-F\d+-W\d+-S\d+-R\d\d$`).

### 1.2 The v3.3.3 workbook uses the authoritative IDs and seeds

```
C1 manifest rows=60 uniqueIDs=60 inAuth=60 seedEqual=60
C1 control rows=60 inAuth=60 seedEqual=60 unique=60
C1 ROI rows=60 inAuth=60 seedEqual=60 srcV332=60
C1 readiness sample rows=69 inAuth=60
```

- `Fault_Sample_Manifest`: 60/60 authoritative IDs and 60/60 authoritative seeds.
- `Control_Manifest`: 60/60 authoritative IDs and 60/60 authoritative seeds.
- `ROI_Context_Mapping`: `SampleRunID` is authoritative 60/60; the 60 `V332-*` cells are confined to the `SourceSampleRunID` provenance column (`V332-A01-R01` style) and each maps to the same model/context.
- `Readiness_Gate`: 60 sample rows are authoritative; the extra 9 truthy rows are the gate legend (`Gate`, `Identity`, …), not samples.
- **No `V332-*` appears in any identity column** (global scan: 60 `V332` cells, all in `ROI_Context_Mapping.SourceSampleRunID`).

### 1.3 Mismatches: the run artifacts do **not** carry the authoritative SampleRunID

Every one of the 120 run directories uses `MODEL-R<NN>-<role>` in the fields that are literally named as the sample identity:

```
C1 run manifest sample_run_id authoritative-style=0/120 ; run-dir-style=120/120
```

Examples (`audit_v3_3_3/runs/A01-R01-fault/manifest.json`):

```json
"sample_run_id": "A01-R01-fault",
"run_id": "PILOT-A01",
"sub_task_id": "PILOT-A01-S01",
```

`pilot_meta.json` repeats this in `excel_identity.sample_run_id = "A01-R01-fault"` and `event_ordinal = 1` (the design ordinal), while `event_ordinal_used = 597`. The authoritative identity `A01-F0-W1-S01-R01` is recoverable only through `model + context + seed + ordinal`; there is no authoritative-ID field in any run artifact.

Additional mismatches in the run artifacts:

- Two manifest schemas: `lsu-run-manifest-v3.2` (105 runs) and `LSU_V333_DIRECT_MANIFEST` (15 runs: all five A03 faults and all ten RP01 fault/control runs).
- `warmup`/`roi`: `NEEDS_RESEARCHER_CONFIRMATION` in 105 manifests, `None` in 15, despite `ConfigFrozen=YES` in the workbook.
- Ledger item **L-D16** is marked `CLOSED_V333` with validation "Every trace carries the authoritative SampleRunID". That is **not** true of `manifest.json`/`pilot_meta.json`: 0/120 carry it. The workbook binds it; the raw run evidence does not.

### 1.4 Workload identity: paths are stale, hashes are correct

30/60 manifest rows name a `WorkloadPath` in an **older worktree** than the one executed:

| Model | `WorkloadPath` worktree | Executed path (run `summary.json`) |
|---|---|---|
| A01, A03, LP01, FW05, DA04 | `lsu-platform-v3.2` | `lsu-platform-v3.2.12` |
| LQ04 | `lsu-platform-v3.2.10` | `lsu-platform-v3.2.12` |

The frozen `WorkloadPath` was copied verbatim (`build_fault_manifest` line 382: `cand["AbsolutePath"] if cand else r.get("WorkloadPath")`). All 30 paths still exist and their ELF SHA equals the manifest `WorkloadELF_SHA256` **today**, so no ELF mismatch is observable, but the path is not the executed artifact and can drift (the v3.2.10 worktree is a different tree).

### 1.5 Approved workload overrides change the golden, not the ID/seed

`60_SAMPLE_MATRIX.csv` still carries the frozen goldens for the six overridden workloads. The v3.3.3 workbook replaces them with the approved candidate goldens for five models (25 rows):

| Model | Frozen matrix `Oracle` | Workbook `Oracle` |
|---|---|---|
| SQ01 | `ba3b3185e541ad03` | `7df5034c23f3e703` |
| SQ03 | `ba3b3185e541ad03` | `7df5034c23f3e703` |
| SP05 | `2543a2a60de01795` | `7df5034c23f3e703` |
| MD04 | `59fc61c040618747` | `0x22be5ae3364d0c9f` |
| RP01 | `59fc61c040618747` | `0xf3b1c554273d23f7` |

This is **authorized** by `decisions/LSU_v3.3.3_Researcher_Approval.md` decision #1 ("all six adopted … SampleRunID/Seed unchanged") and is explicitly labelled `OracleSource = candidate workload golden (OVERRIDE_APPROVED)`. It is not an ID/seed mismatch. It is a trap for any consumer that joins on the frozen matrix `Oracle` without also reading `WorkloadIdentityStatus`.

**Check 1 verdict: PASS for the v3.3.3 workbook identity; FAIL for run-artifact identity binding (L-D16 over-claimed); PARTIAL for workload path provenance.**

---

## 2. Check 2 — uniqueness and fault/control pairing

```
authoritative rows: 60
unique SampleRunIDs: 60
unique seeds: 60
C2 fault IDs ∩ control IDs=60 ; same-seed=60
```

- 60/60 unique SampleRunIDs, 60/60 unique seeds (also in the workbook).
- 60/60 `Control_Manifest` rows share a `SampleRunID` with a fault row.
- 60/60 pairs have the same Seed in the workbook, and 60/60 pairs have the same executed ordinal (checked against `summary.json`; 0 mismatches).
- The fault and control **run directories** are separate (`A01-R01-fault`, `A01-R01-control`) and each has its own run-level `pilot_id`; pairing is only recoverable by model+context.

One `Fault_Sample_Manifest` caveat that is not a pairing failure: `DecisionStatus` is `NEEDS_USER_DECISION` for 35 rows (DA04, LP01, MD04, RP01, SP05, SQ01, SQ03) even though the researcher approved the workloads on 2026-11-12. See defect D-A05.

**Check 2 verdict: PASS.**

---

## 3. Check 3 — seeds reproduce the authoritative value

### 3.1 Metadata layer: PASS

```
C3 pilot_meta+summary seed exact=120/120
```

For all 120 runs, `pilot_meta.json.seed` and `summary.json.seed` equal the frozen seed (and `manifest.json.seed` does too; 0 mismatches against the authoritative matrix). No seed is null/empty/invented.

### 3.2 Executed-command layer: FAIL on 5 fault rows

```
C3 command seed flag present=90/120 ; missing=30
C3 fault commands missing seed: ['LQ04-R01-fault', ..., 'LQ04-R05-fault']
C3 LQ04 fault config.ini rngSeed = rngSeed=0 rngSeed=0 rngSeed=0 rngSeed=0 rngSeed=0
```

- 90/120 `command.txt` files pass a `*rng_seed` flag and in every one of those the value equals the frozen seed. This includes 55/60 fault runs and the 35 `MOUNTED_BUT_DISABLED` controls.
- **5/60 fault runs (LQ04-F0-W2-S01-R01 … R05) never pass `--lq04_rng_seed`.** The injector does support it (`configs/se/lsu_proxy.py:309`, `CHAOS/gem5/src/cpu/o3/CHAOSLQ04/CHAOSLQ04.py:50`), and `config.ini` proves the executed value is the default `0`, while the workbook claims `1842987246`, `2188214204`, `3953171871`, `4153250964`, `3410523942`.
- 25/120 missing-seed commands are exactly the `INJECTOR_ABSENT` controls (DA04, FW02, LQ04, MD04, RP01 controls): no injector is mounted, so the seed has no functional effect. The workbook still claims the same Seed on both sides of the pair; that claim is metadata-only for these 25 controls and cannot be corroborated from `command.txt`.
- Functionally LQ04 is F0 ("draws no RNG", per the config help string), so the 5 faults are not rendered irreproducible by ordinal, but the reported `Seed` is **not the seed the run used**. This is an honesty/provenance defect, not (on current evidence) an outcome-changing one.

`LSU_v3.3.3_Final_Acceptance_Report.md` Q7 says "60/60 authoritative IDs and seeds copied from the frozen matrix; no null seed, no invented value" — true at the workbook/metadata layer, false at the executed-command layer for LQ04.

**Check 3 verdict: FAIL (5/60 fault rows executed with `rngSeed=0`; 25 controls unverifiable but seed-inert).**

---

## 4. Check 4 — Oracle block and classification integrity

### 4.1 What the workbook actually carries

`Fault_Sample_Manifest` has `Oracle` (golden), `OracleSource`, `TerminalState`, `TerminalReason`, `TraceCompleteness`, `EvidencePath`. It does **not** have: an explicit `OracleType`, the fault's observed output, the control's observed output, or an `ExpectedTerminal` column (only per-model prose in `Model_Design.TerminalExpectation`). `Control_Manifest` has `ControlOracle` but no observed control checksum.

The observed values do exist on disk and were independently parsed:

```
C4 fault oracle: {'FAIL': 48, 'PASS': 12} no-checksum: 5
C4 control oracle: {'PASS': 60}
```

Cross-checked against the workbook terminal labels:

| TerminalState | Count | oracle.log verdict | Workbook `FaultOracle` / causal `ApplicationOracle` |
|---|---:|---|---|
| SDC | 43 | `ORACLE_FAIL` with a divergent `got=` | FAIL |
| MASKED | 12 | `ORACLE_PASS` (got == golden) | PASS |
| HANG_WATCHDOG | 5 | `ORACLE_FAIL: no checksum line` | NO_CHECKSUM |

0 terminal/oracle contradictions across 60 rows. Examples:

```
A01-R01-fault   expected=728e604ffcec539d got=7218ee89e1894154  ORACLE_FAIL
FW02-R03-fault  expected=1f4cbf14327717df got=1f4cbf14327717df  ORACLE_PASS
SQ03-R01-fault  expected=7df5034c23f3e703 got=7df5034c23f3e703  ORACLE_PASS
RP01-R01-fault  ORACLE_FAIL: no checksum line
RP01-R01-control expected=f3b1c554273d23f7 got=f3b1c554273d23f7 ORACLE_PASS
```

The MASKED/Oracle-PASS rows are not mislabelled as SDC: every one of the 12 has both `TerminalState=MASKED` and a mechanism in `Causal_Propagation.MaskingMechanism` (FW02-R03 `SUPPRESSED_FORWARD_NORMAL_VALUE`; SQ03 4× `VISIBILITY_TIMING_SHIFT` + 1× `LIFECYCLE_ONLY`; MD04-R01 `INERT_AFTER_COMPLETION`; LQ04 5× `ENTRY_INVALIDATED_RESTORED`).

### 4.2 "gem5 normal exit" is **not** treated as oracle PASS

- 50 fault runs have `exit_code=0` (normal gem5 exit) and `ORACLE_FAIL`/SDC (e.g. all A01 rows). So exit code is not the oracle.
- All 60 controls have `exit_code=0`, `injection_count=0`, and `ORACLE_PASS` based on `got == golden`; 55 of them have `ControlTerminal=UNRESOLVED`, which is a control-classification state, not an oracle PASS.
- A03 faults have `exit_code=1` (post-oracle watchdog) but a measured divergent checksum and `TerminalState=SDC`; RP01 faults have `exit_code=1` and `NO_CHECKSUM`. Neither is treated as PASS.

### 4.3 Completeness verdict

The workbook cannot answer "what did the fault actually print, and what did its control print?" without leaving the workbook for `oracle.log`. `Fault_Sample_Manifest` records the observed checksum only indirectly for A03 (inside `TerminalReason=ORACLE_FAIL;checksum=…;golden=…;POST_ORACLE_SIM_HANG`) and SP05 (`store_data_fnv=…`); the other 43 SDC rows and all 12 MASKED rows omit the fault's `got=` value, and all 60 controls omit their `got=` value.

Minor format inconsistency: `Oracle` for MD04 and RP01 carries a `0x` prefix (`0x22be5ae3364d0c9f`, `0xf3b1c554273d23f7`) while `oracle.log` and `pilot_meta` comparison normalize to bare hex. A naive consumer comparing the cell text to `oracle.log` will see a mismatch.

**Check 4 verdict: FAIL on oracle-block completeness (no actual-output or expected-terminal columns); PASS on SDC/MASKED/HANG consistency and on not equating normal exit with PASS.**

---

## 5. Check 5 — config completeness and blank fields marked PASS

### 5.1 Schema inventory

`Fault_Sample_Manifest` has 50 columns and **0 empty cells**. Required fields vs actual:

| Required field | Present? | Column(s) |
|---|---|---|
| ModelID | Yes | `FaultModelID` (naming differs) |
| ContextID | Yes | `ContextID` |
| SampleRunID | Yes | `SampleRunID` |
| Seed | Yes | `Seed` |
| Workload | Yes (stale path for 30 rows) | `WorkloadPath` |
| ELF SHA256 | Yes | `WorkloadELF_SHA256` |
| Binary SHA256 | Yes | `Gem5BinarySHA256` |
| **Config SHA256** | **No per-row column** | only `Binary_Config.ConfigSHA256`, 12 model rows, all `8309da72…b225`; present per run in `manifest.json.gem5.config_script_sha256` |
| ROI | Yes | `ROI`, `ROI_Start`, `ROI_N` |
| Warm-up | Yes | `WarmUp` (0 ×60) |
| Percentile | Yes | `Percentile` (0.1/0.3/0.5/0.7/0.9 ×12) |
| EligibleEventOrdinal | Yes | `EligibleEventOrdinal` (= `Executed_EventOrdinal`, arithmetic verified 60/60) |
| DynInstSeq | Yes, but 10 `PENDING` | `DynInstSeq` |
| PC | Yes, but 5 `PENDING` | `PC` |
| Injection Config | Yes (split) | `InjectionMode`, `InjectionTiming`, `FaultDuration`, `FaultConfigID`, plus run command only in the audit CSV |
| **Expected Terminal** | **No column** | only `Model_Design.TerminalExpectation` prose |
| Oracle | Yes | `Oracle`, `OracleSource` |

`Binary_Config` is 22 rows: 12 model rows plus a blank row and 9 `Field | Value | Provenance` legend rows appended into the same table. `Readiness_Gate` is 70 rows: 60 samples plus a blank row and 9 legend rows. Any consumer iterating the table must special-case these.

### 5.2 Blank/PENDING critical fields marked PASS

All 60 rows have `ExecutionStatus=MEASURED_TERMINAL` and `Readiness_Gate=ReadyGate=PASS`, yet:

```
C5 PENDING/n-a while ExecutionStatus=MEASURED_TERMINAL:
 {'DynInstSeq': 10, 'PC': 5, 'VA': 10, 'PA': 36,
  'InstructionType': 10, 'LQEntry': 25, 'SQEntry': 10, 'DynamicState': 10}
```

| Field | Rows | Affected contexts |
|---|---:|---|
| `DynInstSeq` | 10 | A03 R01–R05, RP01 R01–R05 |
| `PC` | 5 | RP01 R01–R05 |
| `VA` | 10 | A03 R01–R05, RP01 R01–R05 |
| `PA` | 36 | A03 (PENDING ×5), RP01 (PENDING ×5), SQ01/SQ03/SP05/FW05/DA04 (n/a ×26) |
| `InstructionType` | 10 | A03, RP01 |
| `LQEntry` | 25 | A03, RP01, SQ01, SQ03, SP05 |
| `SQEntry` | 10 | A03, RP01 |
| `DynamicState` | 10 | A03, RP01 |

This directly contradicts the acceptance report's claim that the workbook has "no blank critical field marked PASS". Root cause: `enforce_no_blank_pass` (`tools/lsu_v333_workbook.py:659-685`) hard-codes only `TerminalState`, `TerminalReason`, `TraceCompleteness`, `EvidencePath` (for `ExecutionStatus`) and five readiness fields. It never checks `DynInstSeq`, `PC`, `Seed`, `SampleRunID`, `ConfigSHA256`, `Oracle`, `Workload`, or the ELF/binary hashes.

**Importantly, the missing identity data exists in the raw artifacts** — it is a generator parsing gap, not absent evidence:

- A03 causal `Injection` contains `dyn_inst_seq=13204;pc=4005c0;golden_ea=493098;actual_ea=493090`.
- RP01 `summary.json.rp01.first_skip` contains `load_seq=16293 load_pc=4195680 lq_idx=774 … tick=16967335`.
- `parse_identity` (`tools/lsu_v333_workbook.py:282-294`) only looks for keys `seq`, `va`, `pa`, `lq`, `sq`, `gen`, `state`, so A03/RP01 aliases (`dyn_inst_seq`, `load_seq`, `load_pc`, `lq_idx`, `golden_ea`, `actual_ea`) become `PENDING`.

### 5.3 Additional provenance inconsistency: A01 census vs A01 fault stream

For the same binary, workload, ordinal and event (`ordinal=597`, `pc=0x400578`, `ea=0x493020`):

- census (`audit_v3_3_3/census/A01_8B/addrpath_injections.log`, count-only): `dyn_inst_seq=12752`
- fault run (`audit_v3_3_3/runs/A01-R01-fault/addrpath_injections.log` / `summary.first_injection`): `dyn_inst_seq=12909`
- `audit_v3_3_3/census/A01_8B/CENSUS.md` table text says `seq 12488` (a third value; the prose table is stale against its own raw log).

The PC/EA match, so the ROI ordinal selects the same static event class, but the dynamic-instruction counter differs between the census run and the fault run. Either the census and fault runs are not on the same dynamic stream (the ROI definition is then not exactly the executed stream), or one of the two `seq` counters is not the quantity the workbook claims. This needs a cross-check against the trace; see "Could not verify".

**Check 5 verdict: FAIL.**

---

## 6. Check 6 — proposed `LSU_Formal_Experiment_Config_Final.xlsx` layout and minimal generator change

### 6.1 Workbook layout (one row per fault sample, 60 rows; separate Control rows/sheet)

**Sheet `README`** (1 row per attribute): `schema_version`, `generated_at_utc`, `git_head`, `gem5_binary_path`, `gem5_binary_sha256`, `config_script_path`, `config_sha256`, `frozen_matrix_path`, `frozen_matrix_sha256`, `row_counts`, `identity_rule` ("SampleRunID/Seed copied verbatim from `60_SAMPLE_MATRIX.csv`; never rewritten"), `oracle_rule` ("expected terminal + golden from the executed workload; observed from `oracle.log`"), `blank_rule` ("any blank/PENDING critical field forces the row verdict to INCOMPLETE, never PASS").

**Sheet `Fault_Config` — 60 rows, columns in this order**

1. Identity: `RowID` (1–60), `SampleRunID`, `RunID`, `SubTaskID`, `ModelID`, `ContextID`, `Seed`, `WorkloadIdentityStatus`
2. Workload: `WorkloadName`, `WorkloadPath_Executed`, `WorkloadELF_SHA256`, `WorkloadPath_Frozen`, `InputHash`, `Golden`
3. Execution: `Gem5BinaryPath`, `Gem5BinarySHA256`, `ConfigScriptPath`, `ConfigSHA256`, `WarmUp`, `ROI_Start`, `ROI_End`, `ROI_N`, `Percentile`, `Rank_k`, `EligibleEventOrdinal`, `Executed_EventOrdinal`
4. Fault: `FaultLocation`, `TargetField`, `BitEntryByteIndex`, `NormalValue`, `FaultValue`, `InjectionMode`, `InjectionTiming`, `FaultDuration`, `TargetInstruction`, `EligibleEventCondition`, `FaultConfigID`, `InjectionMaxFaults`, `InjectionRngSeedExecuted`
5. Dynamic identity: `DynInstSeq`, `PC`, `VA_Pre`, `VA_Post`, `PA`, `InstructionType`, `LQEntry`, `SQEntry`, `DynamicState`, `InjectionTick`
6. CLI: `FaultCommand` (full argv, one token per cell or a single space-joined string), `TimeoutSeconds`
7. Oracle: `OracleType` (`checksum|no_checksum|store_data_fnv`), `OracleSource`, `ExpectedTerminal`, `ExpectedTerminalRule`
8. Observed: `ObservedChecksum`, `ObservedTerminal`, `ObservedTerminalReason`, `OracleResult` (`PASS|FAIL|NO_CHECKSUM`)
9. Evidence: `EvidenceDir`, `SummaryPath`, `ManifestPath`, `CommandPath`, `OracleLogPath`, `TracePath`, `TraceCompleteness`
10. Provenance: `ConfigFrozen`, `DecisionStatus`, `Provenance`

**Sheet `Control_Config` — 60 rows, matched by `SampleRunID`**

`SampleRunID`, `ModelID`, `ContextID`, `Seed`, `Ordinal`, `ControlRole` (`matched_control`), `ControlCommand`, `ControlProbability`, `ControlMountFlags`, `ControlZeroProof` (`MOUNTED_BUT_DISABLED|INJECTOR_ABSENT`), `ControlInjectionCount`, `ControlExitCode`, `ControlTerminal`, `ObservedChecksum` (the control's `got=`), `OracleResult` (`PASS`), `Gem5BinarySHA256`, `ConfigSHA256`, `EvidenceDir`, `ControlEvidencePath`, `Provenance`.

Optionally a **`Fault_vs_Control`** join sheet: `SampleRunID`, `Seed`, `Ordinal`, `Golden`, `FaultObservedChecksum`, `ControlObservedChecksum`, `FaultOracle`, `ControlOracle`, `FaultTerminal`, `ControlTerminal`, `DeltaClass` (`SDC|MASKED|HANG`).

**Sheet `ROI_Census` — 12 rows, one per model**: `ModelID`, `ROI_Start`, `ROI_End`, `ROI_N`, `EligibleStreamSize`, `CensusEvidencePath`, `CensusBinarySHA256`, `Percentile→Ordinal` table (R01–R05), `SupersededWindow` (e.g. A01 `1040–1222/183` superseded by `585–713/129`).

**Sheet `Config_Validation` — 60+ rows**, each with `SampleRunID`, `Check`, `Expected`, `Observed`, `Verdict` (`PASS|FAIL|n/a`), `Reason`: ID uniqueness; Seed non-empty; ID/Seed equal frozen matrix; ELF SHA; binary SHA; config SHA; ROI arithmetic `start+ceil(p·N)−1`; executed ordinal inside ROI; `rng_seed` flag equals frozen seed; fault/control same ID/Seed/ordinal; control injection 0; control oracle checksum == golden; fault oracle consistent with terminal; no critical field blank/PENDING; trace completeness.

### 6.2 Minimal generator change (do **not** generate here)

Recommended minimal path, reusing `tools/lsu_v333_workbook.py` (it already has `load_matrix`, `load_csv`, `index_rows`, `gem5_sha`, `summary_ordinal`, `run_provenance`, `parse_identity`, `kv`, `DESIGN_ROI`):

1. Add `build_fault_config(matrix, runs, causal_idx, …)`, `build_control_config(matrix, controls, runs)`, `build_roi_census(...)`, `build_config_validation(...)` returning the sheet row lists above.
2. Add `FORMAL_CONFIG_SHEETS = ("README","Fault_Config","Control_Config","ROI_Census","Config_Validation")` and a `--config-out PATH` argument to `main()`. In `build()`, when `--config-out` is supplied, open a second `openpyxl.Workbook()`, write the config sheets, call a new `validate_config_workbook(wb)` (the same invariant style as `enforce_no_blank_pass` but with the full critical-field map), and save.
3. Fill rows from the existing per-run artifacts: `command.txt` (full argv + executed `rng_seed`), `manifest.json.gem5.config_script_sha256`, `manifest.json.seed`, `pilot_meta.json.oracle_expected/oracle_source`, `oracle.log` (`expected=`, `got=`, ORACLE_PASS/FAIL), `summary.json` (`ordinal`, `terminal`, `terminal_reason`, `exit_code`, `binary_sha`, `workload`), and `config.ini` (`rngSeed` as executed, so the LQ04=0 case is visible).
4. Do **not** duplicate constants: import `DESIGN_ROI`, `PERCENTILES`, `CANDIDATE_BY_MODEL`, `GOLDEN` from the existing module.
5. Single source of truth for the golden: use `pilot_meta.oracle_expected` normalized (strip optional `0x`, strip `checksum=`) and record the raw string in `GoldenRaw` if preserving the original is required.

**Same-commit fix set that the new config workbook should also close** (all are in `tools/lsu_v333_workbook.py`):

- Extend `parse_identity` with aliases: `dyn_inst_seq→DynInstSeq`, `load_seq→DynInstSeq`, `load_pc→PC`, `lq_idx→LQEntry`, `store_seq→SQEntry`, `golden_ea→VA_Pre`, `actual_ea→VA_Post` (fixes the 10/5 PENDING rows).
- `TERMINAL_EXPECTATION["A01"]` is stale: currently `"R01/R04/R05 SDC; R02 SQUASHED+UNRELATED_SQUASH_NO_ARCH_ENTRY; R03 INJECTION_NOT_ACTIVATED"` (line 134); final evidence is **5/5 SDC**. Update it (or derive `TerminalExpectation` from measured rows).
- Add `ConfigSHA256` per manifest row (constant `CONFIG_SHA` already exists at line 62) and `ExpectedTerminal`.
- Use the executed workload path (`summary.json["workload"]`) for `WorkloadPath_Executed`; keep the frozen path in a separate `WorkloadPath_Frozen` column.
- Normalize the `Oracle` column to bare hex (or add `GoldenRaw`) for MD04/RP01.
- Replace copied `DecisionStatus` (`NEEDS_USER_DECISION` ×35) with the approved status after 2026-11-12.
- Extend `enforce_no_blank_pass` `CRITICAL` to the exact field list in §5.1 so a PENDING `DynInstSeq`/`PC` cannot coexist with `ExecutionStatus=MEASURED_TERMINAL`.

**Validation command after the change:**

```bash
python3 tools/lsu_v333_workbook.py \
  --runs audit_v3_3_3/runs \
  --mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \
  --controls audit_v3_3_3/controls/LSU_Fault_Control_Pair_Final.csv \
  --causal audit_v3_3_3/LSU_60Context_Causal_Propagation.csv \
  --out /tmp/v333_design_regen.xlsx \
  --config-out /tmp/LSU_Formal_Experiment_Config_Final.xlsx
# then assert: 60 fault rows, 60 control rows, 60/60 IDs/seeds equal 60_SAMPLE_MATRIX.csv,
# 60/60 ConfigSHA256 == sha256sum(configs/se/lsu_proxy.py), 0 PENDING in the critical map,
# 5/5 LQ04 rows show InjectionRngSeedExecuted == 0 with a Validation verdict FAIL
# (or the LQ04 fault runs are re-executed with --lq04_rng_seed <frozen seed>).
```

Approval required: **N** for the workbook generator; **Y** if the fix is chosen to re-run the 5 LQ04 faults with their frozen seed (it changes evidence artifacts, though not the current classification).

---

## 7. Defect list

### D-A01 — LQ04 fault runs executed with injector seed 0, not the frozen seed (HIGH, category D)

- **Root cause:** `tools/lsu_v332_matrix.py` (and/or the LQ04 dispatch in `run_pilot.py`) does not emit `--lq04_rng_seed` for the LQ04 fault role; the config default (`lsu_proxy.py:309`) is `0`. The same omission applies to the 25 `INJECTOR_ABSENT` controls, where it is harmless.
- **Affected rows:** `LQ04-F0-W2-S01-R01` … `R05` (run dirs `audit_v3_3_3/runs/LQ04-R01-fault` … `LQ04-R05-fault`).
- **Evidence:** `audit_v3_3_3/runs/LQ04-R01-fault/command.txt` (no seed flag); `audit_v3_3_3/runs/LQ04-R01-fault/config.ini:475` `rngSeed=0`; workbook `Fault_Sample_Manifest.Seed=1842987246`; `pilot_meta.json.seed=1842987246`.
- **One-shot fix:** pass `--lq04_rng_seed <frozen Seed>` in the LQ04 fault command; re-run the 5 faults; or, if F0 is declared seed-inert, replace the reported Seed with `n/a (injector draws no RNG; executed rngSeed=0)` in the LQ04 rows and document it. Do not silently report a seed that was not passed.
- **Validation:** `grep -c -- --lq04_rng_seed audit_v3_3_3/runs/LQ04-R0*-fault/command.txt` = 1 each; `grep '^rngSeed' .../config.ini` = frozen seed; workbook `Seed` == command value for all 60 fault rows.
- **Approval required:** N for the label fix; Y for re-running evidence.
- **Regression risk:** Low (F0 draws no RNG); re-run changes `runs/` artifacts and package SHAs.

### D-A02 — 10 rows marked MEASURED_TERMINAL/PASS with PENDING identity fields (HIGH, category D)

- **Root cause:** `parse_identity` (`tools/lsu_v333_workbook.py:282-294`) looks only for `seq/pc/va/pa/lq/sq/gen/state`, while the causal generator emits A03 keys `dyn_inst_seq/golden_ea/actual_ea` and RP01 keys `load_seq/load_pc/lq_idx/store_seq`. `enforce_no_blank_pass` does not include these fields.
- **Affected rows:** A03 R01–R05 (`DynInstSeq`, `VA`, `PA`, `InstructionType`, `LQEntry`, `SQEntry`, `DynamicState`); RP01 R01–R05 (`DynInstSeq`, `PC`, `VA`, `PA`, `InstructionType`, `LQEntry`, `SQEntry`, `DynamicState`); plus `PA=n/a` on 26 store/other rows (SQ01/SQ03/SP05/FW05/DA04; legitimate only if the model has no PA by design and the cell says why).
- **Evidence:** §5.2 table; `audit_v3_3_3/LSU_60Context_Causal_Propagation.csv` A03-R01 `Injection` string; `audit_v3_3_3/runs/RP01-R01-fault/summary.json.rp01.first_skip`.
- **One-shot fix:** add the key aliases in `parse_identity`; populate `PC`/`LQEntry` for RP01 from `summary.json.rp01.first_skip`; add the identity fields to `enforce_no_blank_pass`.
- **Validation:** re-run the builder; assert 0 `PENDING` in `DynInstSeq`, `PC`, `VA`, `InstructionType`, `SQEntry`, `DynamicState` across 60 rows, and `LQEntry` non-empty for all 60.
- **Approval required:** N.
- **Regression risk:** Low (reporting only).

### D-A03 — Oracle block lacks actual outputs and expected terminal (MEDIUM, category D)

- **Root cause:** `build_fault_manifest`/`build_control_manifest` never read `oracle.log`'s `got=` or the `.golden`/`pilot_meta.oracle_expected` as separate columns; there is no `ExpectedTerminal` schema.
- **Affected rows:** all 60 (43 SDC + 12 MASKED missing fault `got=`; 60 controls missing control `got=`; 60 missing expected terminal).
- **Evidence:** §4.1; `oracle.log` files contain `expected=… got=…`.
- **One-shot fix:** add `ObservedChecksum`, `ControlObservedChecksum`, `ExpectedTerminal`, `OracleType` columns and fill from `oracle.log`/`pilot_meta`.
- **Validation:** 60/60 fault observed checksums populated (or `n/a` for the 5 RP01 no-checksum rows); 60/60 control checksums populated; 60/60 expected terminals populated from the model rule.
- **Approval required:** N.
- **Regression risk:** None (additive columns).

### D-A04 — No per-row `ConfigSHA256`; `ConfigFrozen=YES` not corroborated by run manifests (MEDIUM, category D)

- **Root cause:** config SHA exists only in `Binary_Config` (12 model rows) and in `manifest.json.gem5.config_script_sha256`; `Fault_Sample_Manifest` has no config column. 105 run manifests still say `warmup=NEEDS_RESEARCHER_CONFIRMATION`, `roi=NEEDS_RESEARCHER_CONFIRMATION`.
- **Affected rows:** all 60 (schema); 105 manifest files (warmup/roi).
- **Evidence:** live `sha256sum configs/se/lsu_proxy.py` = `8309da72…b225`, matching all 120 manifests and `Binary_Config`; `manifest.json` A01-R01-fault `"warmup": "NEEDS_RESEARCHER_CONFIRMATION"`.
- **One-shot fix:** add `ConfigSHA256` to every config row; regenerate the run manifests' `warmup`/`roi` fields from the approval, or state "manifest field is historical; authoritative values are in the workbook".
- **Validation:** 60/60 `ConfigSHA256` equal the live hash; no `NEEDS_RESEARCHER_CONFIRMATION` in a final artifact.
- **Approval required:** N.
- **Regression risk:** Low.

### D-A05 — Packaged CSVs contradict the approved workload state (HIGH for release integrity, category D)

- **Root cause:** `LSU_60Context_Final_Readiness.csv` and `LSU_Fault_Control_Final_Audit.csv` were regenerated at 12:41/12:07 but still label the six overridden workloads `CANDIDATE_PENDING_APPROVAL` (30 rows) and `TECHNICALLY_READY_APPROVAL_PENDING` (30 rows), while the workbook says `OVERRIDE_APPROVED`, the approval record is dated 2026-11-12, and the acceptance report says "Workload 12/12 approved and frozen". `Fault_Sample_Manifest.DecisionStatus` also still says `NEEDS_USER_DECISION` for 35 rows.
- **Affected rows:** FW02, MD04, RP01, SP05, SQ01, SQ03 × R01–R05 (30 rows in each CSV); 35 manifest rows for `DecisionStatus`.
- **Evidence:** §5 / §8 outputs; `audit_v3_3_3/LSU_60Context_Final_Readiness.csv`; `audit_v3_3_3/LSU_Fault_Control_Final_Audit.csv`.
- **One-shot fix:** regenerate both CSVs and the manifest `DecisionStatus` from the approval record (`OVERRIDE_APPROVED`, `APPROVED_2026-11-12`) so every deliverable agrees.
- **Validation:** `WorkloadStatus` = FORMAL 30 / OVERRIDE_APPROVED 30 in both CSVs; `Ready` = TECHNICALLY_READY 60; no `NEEDS_USER_DECISION`/`CANDIDATE_PENDING_APPROVAL` string anywhere in `audit_v3_3_3/*.csv` or the workbook.
- **Approval required:** N (already approved; this is a label reconciliation).
- **Regression risk:** Low.

### D-A06 — Run artifacts do not carry the authoritative SampleRunID (MEDIUM, category D; residual of L-D16)

- **Root cause:** `run_pilot.py`/`lsu_v332_matrix.py` write `sample_run_id = "<Model>-R<NN>-<role>"`, `run_id = "PILOT-<Model>"`, `sub_task_id = "PILOT-<Model>-S01"`. 105 runs use `lsu-run-manifest-v3.2`, 15 use `LSU_V333_DIRECT_MANIFEST`.
- **Affected rows:** all 120 run manifests / `pilot_meta.json`.
- **Evidence:** §1.3.
- **One-shot fix:** add `authoritative_sample_run_id` (and keep `run_id` for the run-instance) to both manifest schemas; set it from `60_SAMPLE_MATRIX.csv` by model+context; unify the two schemas or add a schema-version field to both.
- **Validation:** 120/120 manifests carry the exact authoritative ID; `grep -L authoritative_sample_run_id audit_v3_3_3/runs/*/manifest.json` empty.
- **Approval required:** N.
- **Regression risk:** Low.

### D-A07 — `WorkloadPath` points at old worktrees (LOW–MEDIUM, category D)

- **Root cause:** `build_fault_manifest` copies `r.get("WorkloadPath")` from the frozen matrix; the frozen path names `lsu-platform-v3.2`/`v3.2.10`, while execution used `v3.2.12`.
- **Affected rows:** A01, A03, DA04, FW05, LP01 (v3.2); LQ04 (v3.2.10) — 30 rows.
- **Evidence:** §1.4; ELF hashes happen to match today.
- **One-shot fix:** record the executed path from `summary.json["workload"]` as `WorkloadPath_Executed`; keep the frozen path in a separate column.
- **Validation:** 60/60 executed paths begin with the worktree actually used in `command.txt`; ELF SHA equal.
- **Approval required:** N.
- **Regression risk:** Low.

### D-A08 — Golden text format inconsistent for MD04/RP01 (LOW, category D)

- **Root cause:** `CANDIDATE_WORKLOADS` stores `0x…` for RP01/MD04 while `Workload_Oracle.ControlChecksum` and `oracle.log` use bare hex.
- **Affected rows:** MD04 R01–R05, RP01 R01–R05 (10 rows).
- **One-shot fix:** normalize the execution-facing column to bare hex; retain the raw string in `GoldenRaw`.
- **Validation:** text equality between `Fault_Sample_Manifest.Oracle` and `oracle.log expected=` for all 60 rows after stripping `checksum=`.
- **Approval required:** N.
- **Regression risk:** None.

### D-A09 — `Model_Design` A01 terminal expectation and approval reference are stale (LOW, category D)

- **Root cause:** `TERMINAL_EXPECTATION["A01"]` (line 134) still says `R02 SQUASHED+UNRELATED_SQUASH_NO_ARCH_ENTRY; R03 INJECTION_NOT_ACTIVATED`; `ApprovalReference` is `n/a` for A01/A03 although approval #2 covers them. The same stale wording appears in `LSU_60Context_Final_Readiness.csv` `Qualifier` for all five A01 rows.
- **Affected rows:** `Model_Design` A01 (and A03 reference); 5 A01 rows in the readiness CSV.
- **Evidence:** `model_controls` dump in §8; A01 run summaries all `TerminalState=SDC`.
- **One-shot fix:** derive the expectation from the measured rows (`SDC` ×5) or update the constant; set the approval reference for A01/A03.
- **Validation:** `Model_Design.A01.TerminalExpectation` contains no `SQUASHED`/`INJECTION_NOT_ACTIVATED`; all five A01 rows agree with `TerminalState=SDC`.
- **Approval required:** N.
- **Regression risk:** None (documentation).

### D-A10 — `enforce_no_blank_pass` coverage too narrow (MEDIUM, category A/D)

- **Root cause:** the checker covers 4 manifest fields + 5 readiness fields; it does not cover `SampleRunID`, `Seed`, `ConfigSHA256`, `Oracle`, `DynInstSeq`, `PC`, `Workload`, or hashes. This is why D-A02/D-A04 passed the "no blank critical field marked PASS" gate and its unit test.
- **Affected rows:** all 60 (gate-level).
- **One-shot fix:** extend `CRITICAL` with the §5.1 field list; add a test that a synthetic PENDING `DynInstSeq` with `MEASURED_TERMINAL` fails the build.
- **Validation:** `pytest tests/test_lsu_v333_workbook.py -q` still passes, and a negative test fails as expected.
- **Approval required:** N.
- **Regression risk:** Low.

### D-A11 — Data-table pollution by legend rows (LOW, category D)

- **Root cause:** `build_binary_config` and `build_readiness` append `[]` and `Field/Value/Provenance` / `Gate/Definition/Status` rows into the same sheet.
- **Affected rows:** `Binary_Config` rows 13–22 (1 blank + 9 legend), `Readiness_Gate` rows 61–70.
- **One-shot fix:** move legend blocks to a separate `Legend` sheet or tag them with a `RecordType` column.
- **Validation:** `Binary_Config` has exactly 12 data rows; `Readiness_Gate` exactly 60.
- **Approval required:** N.
- **Regression risk:** Low (test `test_eight_sheets` must be updated if a sheet is added).

### D-A12 — A01 census vs fault-run `dyn_inst_seq` divergence (MEDIUM, category C/D; needs trace confirmation)

- **Root cause:** unknown; the census count-only run and the fault run disagree on `dyn_inst_seq` for the same ordinal/PC/EA (12752 vs 12909), and `CENSUS.md` prose says 12488. The census and fault commands differ in `--addrpath_span_events` (1000 vs 10), `--chaos_propagation`, and max-faults.
- **Affected rows:** A01 R01–R05 (DynInstSeq/PC identity), possibly A03 (same re-census method).
- **Evidence:** §5.3.
- **One-shot fix:** re-derive the A01 ROI ordinals from a census command that uses the **same** ELIGIBLE-stream configuration as the fault run (same span/propagation/global flags), or record the census-stream `dyn_inst_seq` alongside the executed-stream `dyn_inst_seq` and state the difference explicitly.
- **Validation:** census `CHAOS_ELIGIBLE` line for each selected ordinal has the same `dyn_inst_seq`, `pc`, `ea` as the executed run's `A01_EA`/first_injection record; `CENSUS.md` table matches its own raw log.
- **Approval required:** Y if the ordinals are re-censused (affects the frozen ROI).
- **Regression risk:** Medium (ordinals would shift; would require re-running the 5 A01 faults).

---

## 8. Could not verify

1. **Which `dyn_inst_seq` is authoritative for A01** — census (12752) vs fault (12909) vs CENSUS.md prose (12488). I did not open `trace_v31.jsonl` deeply enough to determine whether the two runs are on the same dynamic stream; a trace-level join is needed (D-A12).
2. **A03 `DynInstSeq`/`VA` correctness** — the causal string provides `dyn_inst_seq=13204; golden_ea=493098; actual_ea=493090`, but the workbook records neither; I verified the data exists, not that it matches `prop_trace.csv.gz`.
3. **Whether the 5 LQ04 faults are numerically unaffected by `rngSeed=0`** — the config help says F0 draws no RNG, but I did not inspect `CHAOSLQ04.cc` execution to prove the seed is never read on the F0 path.
4. **Whether the 25 `INJECTOR_ABSENT` controls would have used the frozen seed** — no injector is mounted, so the seed is inert by construction; the identity claim is metadata-only.
5. **The `LSU_v3.3.3_Formal_Experiment_Ready_Package.zip` internal consistency** — I listed contents and SHA (`168a1330…cf23`) but did not extract/compare every file against the working tree.
6. **`60_SAMPLE_MATRIX.csv` provenance itself** — I treated it as authoritative per `README_GROUND_TRUTH.md` and cross-checked it against v3.2.7 sheet 5 (exact match); I did not attempt to re-derive the seeds from any earlier source.
7. **Registry of the requested filename** — `LSU_Formal_Experiment_Config_Final.xlsx` does not exist anywhere in the repo (the v3.3.2 `audit_v3_3_2/LSU_Formal_Experiment_Config.xlsx` is an older artifact, not in the v3.3.3 zip). The layout in §6 is a proposal, not a verification of an existing file.

---

## 9. Exact commands used (reproducible, read-only)

```bash
# frozen-source cross-check
python3 - <<'PY'
import csv, openpyxl
r = list(csv.DictReader(open('docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv')))
wb = openpyxl.load_workbook('docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx', data_only=True, read_only=True)
ws = wb['5.60个样本执行矩阵']; it = ws.iter_rows(values_only=True); h = list(next(it))
rows = [dict(zip(h, x)) for x in it]
print(len(r), len(rows), [x['SampleRunID'] for x in rows] == [x['SampleRunID'] for x in r])
PY

# workbook identity / seed / pair checks
python3 - <<'PY'
# (see §1.2, §2, §3, §4, §5 for the full script)
PY

# live hashes
sha256sum build/ARM/gem5.opt configs/se/lsu_proxy.py
# 1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338  build/ARM/gem5.opt
# 8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225  configs/se/lsu_proxy.py

# LQ04 seed proof
grep '^rngSeed' audit_v3_3_3/runs/LQ04-R0*-fault/config.ini
grep -L 'seed' audit_v3_3_3/runs/*/command.txt

# ox output / exit-code proof
for d in A01-R01-fault A01-R01-control RP01-R01-fault FW02-R03-fault; do
  echo "== $d"; cat audit_v3_3_3/runs/$d/oracle.log
done
```

Key quoted outputs are embedded in §1–§5 above.

---

## 10. Bottom line

- **Identity is trustworthy in the workbook**: 60/60 authoritative SampleRunIDs, 60/60 seeds, 60 unique IDs/seeds, 60/60 matched pairs with the same seed and ordinal, one binary (`1126e0fd…`) and one config (`8309da72…`) across 120 manifests.
- **Identity is not trustworthy end-to-end**: the raw run artifacts never carry the authoritative SampleRunID, the LQ04 faults ran with `rngSeed=0` instead of the frozen seed, and 10 rows carry `PENDING` dynamic identity while labelled `MEASURED_TERMINAL`/`PASS`. The v3.3.3 claim "no blank critical field marked PASS" is false under the required field list.
- **Oracle classification is sound but incompletely recorded**: 43 SDC / 12 MASKED / 5 HANG is consistent with every `oracle.log`; normal exit is correctly *not* treated as oracle PASS; but actual fault/control outputs and expected terminals are absent from the workbook.
- **Release blockers to fix before formal launch:** D-A01 (LQ04 seed), D-A02 (PENDING identity + gate coverage), D-A03/D-A04 (oracle/config completeness), D-A05 (packaged CSVs still say "pending approval"), D-A06 (run-artifact identity binding). D-A12 needs a decision because it questions the A01 ROI stream definition.
