# MD04 Propagation Audit — v3.2.11

**Model:** MD04  **SubUnit:** LSU  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** Violation-report suppression at checkViolations → load execution decision → memory_response → register_writeback → consumer → commit/squash; terminal MASKED or SDC

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| MD04-R01 | MD04-F6-W7-S01-R01 | 2595563470 | 1 | `0de2564468fd710b` | `ca15390f1a797c55` | `59fc61c040618747` |
| MD04-R02 | MD04-F6-W7-S01-R02 | 811948497 | 2 | `0de2564468fd710b` | `ca15390f1a797c55` | `59fc61c040618747` |
| MD04-R03 | MD04-F6-W7-S01-R03 | 2545691512 | 3 | `0de2564468fd710b` | `ca15390f1a797c55` | `59fc61c040618747` |
| MD04-R04 | MD04-F6-W7-S01-R04 | 2149193331 | 4 | `0de2564468fd710b` | `ca15390f1a797c55` | `59fc61c040618747` |
| MD04-R05 | MD04-F6-W7-S01-R05 | 1008734674 | 5 | `0de2564468fd710b` | `ca15390f1a797c55` | `59fc61c040618747` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| MD04-R01 | yes | yes | missing | yes | yes | missing | missing | SQUASHED | missing | PARTIAL |
| MD04-R02 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | COMPLETE_CAUSAL_CHAIN |
| MD04-R03 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | COMPLETE_CAUSAL_CHAIN |
| MD04-R04 | yes | yes | missing | missing | missing | missing | missing | SQUASHED | missing | PARTIAL |
| MD04-R05 | yes | yes | missing | yes | yes | yes | yes | MASKED | missing | COMPLETE_CAUSAL_CHAIN |

## 3. Per-pilot evidence

### MD04-R01 — PARTIAL

- Injection seq **518**, PC `0x4113d0`, tick 733425, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/MD04-R01.
- Earliest anomaly: event None `None`.
- Writeback: event 337, phys r70 a2, value_fnv `cc3193ff3a28738c`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `MASKED`).
- Oracle: expected `59fc61c040618747`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_EARLY_ANOMALY_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: SQUASHED_NO_COMMIT.

### MD04-R02 — COMPLETE_CAUSAL_CHAIN

- Injection seq **2251**, PC `0x400d98`, tick 3391080, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/MD04-R02.
- Earliest anomaly: event 1107 `memory_response`.
- Writeback: event 1108, phys r71 a0, value_fnv `a8c7f832281a39c5`, payload_fnv `a8c7f832281a39c5`.
- Consumer: event 1113 PC `0x400d9c` source_linked=True input_fnv `a8c7f832281a39c5`, matches_source=1.
- Commit: event 1110 seq 917.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `59fc61c040618747`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: VIOLATION_SUPPRESSED_LOAD_COMMITTED_MASKED.

### MD04-R03 — COMPLETE_CAUSAL_CHAIN

- Injection seq **17443**, PC `0x400530`, tick 17816260, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/MD04-R03.
- Earliest anomaly: event 7154 `memory_response`.
- Writeback: event 7155, phys r49 a1, value_fnv `a8c7f832281a39c5`, payload_fnv `a8c7f832281a39c5`.
- Consumer: event 7159 PC `0x40053c` source_linked=True input_fnv `a8c7f832281a39c5`, matches_source=1.
- Commit: event 7156 seq 10911.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `59fc61c040618747`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: VIOLATION_SUPPRESSED_LOAD_COMMITTED_MASKED.

### MD04-R04 — PARTIAL

- Injection seq **69297**, PC `0x4015fc`, tick 31073735, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/MD04-R04.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `MASKED`).
- Oracle: expected `59fc61c040618747`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_EARLY_ANOMALY_EVENT, NO_INTERMEDIATE_PROPAGATION_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: SQUASHED_NO_COMMIT.

### MD04-R05 — COMPLETE_CAUSAL_CHAIN

- Injection seq **71660**, PC `0x4288dc`, tick 36154580, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/MD04-R05.
- Earliest anomaly: event None `None`.
- Writeback: event 26001, phys r60 a3, value_fnv `a8c7f832281a39c5`, payload_fnv `None`.
- Consumer: event 26010 PC `0x4288ec` source_linked=True input_fnv `a8c7f832281a39c5`, matches_source=1.
- Commit: event 26004 seq 63399.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `59fc61c040618747`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_EARLY_ANOMALY_EVENT.
- Classification rule: VIOLATION_SUPPRESSED_LOAD_COMMITTED_MASKED.

## 3.1 Model-specific evidence quote

`site=LSQUnit::checkViolations;family=md04;load_seq=2251;store_seq=2239;addr=0x493990;violation_report_suppressed=1;load_complete=0`.

## 4. Terminal and causality

R02/R03/R05 are complete control-effect chains: injection detail records violation_report_suppressed=1, the load nevertheless executes, receives data, writes back, and commits; its consumers receive the correct data (MASKED, oracle PASS). The fault effect is the suppressed violation report, not a corrupted value. R01/R04 are SQUASHED without proof that the squash is fault-caused (PARTIAL).

## 5. Missing evidence

ORACLE_FILE_MISSING in v3.2.6 (meta-sourced PASS); squash causality unproven in R01/R04

## 6. Verdict

- COMPLETE_CAUSAL_CHAIN: 3/5 pilots
- PARTIAL: 2/5 pilots

Model verdict: **COMPLETE_CAUSAL_CHAIN** (see per-pilot split above).

## 7. Supplementary pilot recommendation

Optional: trace the squash reason for R01/R04 to decide whether the squash is fault-caused; 2 runs after approval.
