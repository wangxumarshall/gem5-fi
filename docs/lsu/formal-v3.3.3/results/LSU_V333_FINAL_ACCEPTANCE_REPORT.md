# LSU v3.3.3 Formal Campaign — Final Acceptance Report

- **Campaign ID:** `LSU-V333-FINAL-20261112`
- **Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
- **Branch:** `lsu-v3.3.1-context-workload-20261111`
- **Frozen binary SHA256:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
- **Frozen config SHA256:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
- **Campaign root:** `runs/lsu/formal_v333_final_20261112/` (3.2 GiB)
- **Scope executed:** 12 models × 5 contexts × {fault, control} = **120 runs**

## 1. Stage results

| Stage | Command | Result |
|---|---|---|
| 0 preflight | `launch_commands_final.sh preflight` | PASS — both hashes OK, root empty |
| 0b dry-run | `01_launch_campaign.sh --dry-run` | PASS — 120 commands, 60 SampleRunID/Seed, 60 pairs, 120 unique dirs, 9 ELF hashes OK, `READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES` |
| 1 launch | `01_launch_campaign.sh` | PASS — `runner_exit=0` |
| 2 manifest | `02_manifest_only.sh` | PASS — `formal=120 non_formal=0`, exit 0 |
| 3 collector | `03_full_collector.sh` | PASS — exit 0 |
| 4 reports | `04_final_reports.sh` | PASS — exit 0 |

Runner accounting at the end of Stage 1: `COMPLETED=77, ORACLE_FAIL=43, FAILED=0, TIMEOUT=0,
HASH_MISMATCH=0, OUTPUT_INCOMPLETE=0, PENDING=0`.

## 2. Final result counts

### Fault runs (60)

| Terminal | Count |
|---|---|
| SDC (`ORACLE_FAIL` = measured divergence) | 43 |
| MASKED | 12 |
| HANG_WATCHDOG (`TRACE_INCOMPLETE`) | 5 |

Collector status: `ORACLE_FAIL 43`, `COMPLETED 12`, `TRACE_INCOMPLETE 5`.

### Control runs (60)

- Oracle PASS: **60/60**
- `InjectionCount = 0`: **60/60**
- Zero-injection proof: `MOUNTED_BUT_DISABLED` 35, `INJECTOR_ABSENT` 25
- Control audit `ControlInjected`: **NO = 60**, no `UNKNOWN`, no `INVALID`
- `zero_injection_proven=60, not_proven=0`

### Readiness (60 contexts, one per fault run)

| ChainClass | Count |
|---|---|
| COMPLETE_CAUSAL_CHAIN | 38 |
| VALID_TERMINAL_CHAIN | 12 |
| QUALIFIED | 5 |
| TRACE_INCOMPLETE | 5 |

Propagation evidence class: `DIRECT_DATAFLOW_EVIDENCE` 43, `MASKING_EVIDENCE` 12,
`TERMINAL_WITNESS_EVIDENCE` 5.

### Per-model fault terminal

| Model | Terminals | QualifiedStatus |
|---|---|---|
| A01 | SDC×5 | n/a |
| A03 | SDC×5 | PASS |
| FW02 | SDC×4, MASKED×1 | n/a |
| FW05 | SDC×5 | n/a |
| SQ01 | SDC×5 | n/a |
| SQ03 | MASKED×5 | n/a |
| SP05 | SDC×5 | **QUALIFIED×5 (preserved)** |
| DA04 | SDC×5 | n/a |
| LP01 | SDC×5 | n/a |
| MD04 | SDC×4, MASKED×1 | n/a |
| LQ04 | MASKED×5 | n/a |
| RP01 | HANG_WATCHDOG×5 | **TRACE_INCOMPLETE×5 (preserved)** |

## 3. Preserved frozen limitations (not upgraded)

- **SP05 R01–R05:** `QUALIFIED` — frozen `writeback_event` unsatisfiable; suppressed-writeback evidence retained.
- **RP01 R01–R05:** `TRACE_INCOMPLETE` — internal-watchdog HANG; terminal metadata complete.
- Neither was upgraded to PASS.

## 4. Evidence traceability

- All 60 fault runs carry `injection_count > 0` and a raw `prop_trace.csv.gz`.
- 50/60 fault runs also carry the converted `trace_v31.jsonl`.
- The 10 fault runs without `trace_v31.jsonl` are the **direct-driver** runs:
  - RP01 R01–R05 (HANG_WATCHDOG / TRACE_INCOMPLETE). Raw `prop_trace.csv.gz` present; terminal metadata complete.
  - A03 R01–R05. `trace_v31.jsonl` is not produced by the direct driver. The
    normalization round parsed the raw `prop_trace.csv.gz` directly and now records the
    selected event, first affected instruction, first affected squash, first committed
    affected instruction, first consumer, response/taint/consumer event IDs and the
    writeback/consumer hash linkage. See
    `LSU_V333_FINAL_EVIDENCE_NORMALIZATION_REPORT.md` §1–2 and the new columns in
    `LSU_60Context_Causal_Propagation_Final.csv`. R02 seq 13718 is recorded as an
    unrelated squash; R03 ordinal 1131 is the `ALREADY_STUCK` selected event and 1150
    is the first affected instruction. No event is merged into a single `FirstDivergence`.
  - The five distinct statuses are in `LSU_Evidence_Completeness_Audit.csv`
    (`TraceV31Status`, `RawPropTraceStatus`, `RawTraceIntegrity`,
    `PropagationCoverage`, `CausalChainCompleteness`).
- Every one of the 120 run directories retains its attempt dir with `summary.json`, `campaign.json`,
  `oracle.log`, `prop_trace.csv.gz`, `stdout.log`, `stderr.log`, `config.ini`, `stats.txt`,
  `attempt.json`, and the per-model injection log where the driver produces one.
- All 120 `campaign.json` carry the frozen campaign id and the exact frozen Binary/Config SHA;
  all 60 fault/control pairs share one Seed and SampleRunID.

## 5. Collector defects found and fixed during collection

The experiment itself was not modified: no Binary, Config, Seed, SampleRunID, Workload or run output
was changed. Two collection-tool defects were found by the fail-closed pipeline and fixed:

1. **`535be32b` — N/A input-hash sentinel + stale workload name.** The design matrix spells "no input
   hash" as `N/A` and `无（内建输入）`, but the collector only accepted lowercase `n/a`; for six models
   whose matrix `WorkloadPath` also carried a stale abstract basename it compared the run's ELF SHA
   against the literal sentinel. Fixed by normalising the sentinels and recovering the authorized ELF
   basename from `campaign_identity.elf_sha` by hash; the run summary is now the Workload/ELF authority.
2. **`7e5b598b` — direct-driver trace requirement.** The collector required `trace_v31.jsonl` for all
   non-partial runs, while the authorized runner only requires it for `run_pilot` tasks (RP01 is always
   direct; A03 fault is direct). Fixed by mirroring the runner's rule. No other check was relaxed.

Both commits are pushed to `origin/lsu-v3.3.1-context-workload-20261111`.

## 6. Non-blocking warnings carried into the report

`04_final_reports.sh` emitted:

- `WARNING: W6: v3.2.7 ExpectedGolden='7284dc0b3f6c64cf' is stale; using verified Oracle='2543a2a60de01795' (ledger L-D09)`
- `WARNING: W8: v3.2.7 ExpectedGolden='8009aab3f75f7417' is stale; using verified Oracle='3f89eab79392ce69' (ledger L-D09)`

These are documented ledger overrides; the verified oracle values were used.

## 7. Deliverables (campaign root)

- `LSU_Fault_Control_Pair_RAW.csv` — 120 raw rows (Stage 1)
- `collector_manifest/LSU_120Run_Campaign_Manifest.csv` — 120-row formal manifest (Stage 2)
- `collector_manifest/LSU_60Fault_60Control_Pair_Map.csv` — 60 pairs (Stage 2)
- `collector_manifest/LSU_Control_Zero_Proof_Final.csv` — 60 control proofs (Stage 2)
- `collector_full/LSU_Formal_Experiment_Config_Final.xlsx` — collector workbook (Stage 3)
- `collector_full/LSU_60Context_Final_Readiness.csv` (Stage 3)
- `LSU_60Context_Causal_Propagation_Final.csv` — 60 fault propagation chains (Stage 4)
- `LSU_60Context_Final_Readiness.csv` — 60 readiness rows (Stage 4)
- `LSU_11Context_Repair_Validation.csv` (Stage 4)
- `LSU_Control_Audit_Formal.csv` — 60 rows, `ControlInjected=NO` (Stage 4)
- `LSU_Final_Experiment_Config.xlsx` — 8 sheets: Model_Design, Fault_Sample_Manifest,
  Control_Manifest, ROI_Context_Mapping, Causal_Propagation, Workload_Oracle, Binary_Config,
  Readiness_Gate (Stage 4)
- `LSU_Evidence_Completeness_Audit.csv` — 120 rows, five distinct status columns
- `LSU_A03_Injection_Count_Semantics.csv` — raw count + activation/stream/affected sub-metrics
- `LSU_V333_FINAL_EVIDENCE_NORMALIZATION_REPORT.md` — normalization and A03 chain detail
- `SHA256SUMS.campaign` — current full-tree manifest (verification exit 0)
- `SHA256SUMS.campaign.pre_normalization` — preserved pre-normalization manifest
- `SHA256SUMS.raw_runs` — original 120-run evidence tree (2,193 files, exit 0)
- `SHA256SUMS.deliverables` — SHA256 over the final delivery files

## 8. Verdict

`LSU_V333_FINAL_CAMPAIGN=COMPLETE`

120/120 runs accepted as FORMAL evidence; 60/60 fault-control pairs intact; 60/60 controls prove
zero injection; all frozen limitations preserved unmodified.
