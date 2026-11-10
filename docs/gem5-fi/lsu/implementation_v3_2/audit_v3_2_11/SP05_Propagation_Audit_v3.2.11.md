# SP05 Propagation Audit — v3.2.11

**Model:** SP05  **SubUnit:** SQ  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** Suppressed completeStore → _completed/storesToWB unchanged → entry lifetime/drain; a later load would extend the chain

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| SP05-R01@evidence | SP05-F6-W6-S01-R01 | 1489155957 | 1 | `303c610d2dcca813` | `906b3798adc618f3` | `2543a2a60de01795` |
| SP05-R02@evidence | SP05-F6-W6-S01-R02 | 1290498198 | 2 | `303c610d2dcca813` | `906b3798adc618f3` | `2543a2a60de01795` |
| SP05-R03@evidence | SP05-F6-W6-S01-R03 | 2768710389 | 3 | `303c610d2dcca813` | `906b3798adc618f3` | `2543a2a60de01795` |
| SP05-R04@evidence | SP05-F6-W6-S01-R04 | 2741073922 | 4 | `303c610d2dcca813` | `906b3798adc618f3` | `2543a2a60de01795` |
| SP05-R05@evidence | SP05-F6-W6-S01-R05 | 4098160626 | 5 | `303c610d2dcca813` | `906b3798adc618f3` | `2543a2a60de01795` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| SP05-R01@evidence | yes | yes | missing | yes | missing | missing | missing | MASKED | yes | LIFECYCLE_ONLY |
| SP05-R02@evidence | yes | yes | missing | yes | missing | missing | missing | MASKED | yes | LIFECYCLE_ONLY |
| SP05-R03@evidence | yes | yes | missing | yes | missing | missing | missing | MASKED | yes | LIFECYCLE_ONLY |
| SP05-R04@evidence | yes | yes | missing | yes | missing | missing | missing | MASKED | yes | LIFECYCLE_ONLY |
| SP05-R05@evidence | yes | yes | missing | yes | missing | missing | missing | MASKED | yes | LIFECYCLE_ONLY |

## 3. Per-pilot evidence

### SP05-R01@evidence — LIFECYCLE_ONLY

- Injection seq **18**, PC `0xNone`, tick 150150, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SP05_v3_2_9/SP05-R01.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `2543a2a60de01795`, actual `2543a2a60de01795`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SP05-R02@evidence — LIFECYCLE_ONLY

- Injection seq **19**, PC `0xNone`, tick 150150, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SP05_v3_2_9/SP05-R02.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `2543a2a60de01795`, actual `2543a2a60de01795`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SP05-R03@evidence — LIFECYCLE_ONLY

- Injection seq **23**, PC `0xNone`, tick 150150, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SP05_v3_2_9/SP05-R03.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `2543a2a60de01795`, actual `2543a2a60de01795`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SP05-R04@evidence — LIFECYCLE_ONLY

- Injection seq **24**, PC `0xNone`, tick 150150, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SP05_v3_2_9/SP05-R04.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `2543a2a60de01795`, actual `2543a2a60de01795`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SP05-R05@evidence — LIFECYCLE_ONLY

- Injection seq **28**, PC `0xNone`, tick 150535, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SP05_v3_2_9/SP05-R05.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `2543a2a60de01795`, actual `2543a2a60de01795`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

## 3.1 Model-specific evidence quote

`site=writebackStores_prematureComplete;completed_before=0;completed_after=1;stores_to_wb_before=4;stores_to_wb_after=3;mem_sent=0`.

## 4. Terminal and causality

All five pilots inject the completion suppression (storesToWB before/after differ by one) and the run completes MASKED, but the trace contains no register writeback, consumer or commit node for the store chain; the effect is confined to the store entry lifetime.

## 5. Missing evidence

NO_REGISTER_WRITEBACK_EVENT/NO_CONSUMER_EDGE/NO_COMMIT_EVENT; entry-free/drain event absent

## 6. Verdict

- LIFECYCLE_ONLY: 5/5 pilots

Model verdict: **LIFECYCLE_ONLY** (see per-pilot split above).

## 7. Supplementary pilot recommendation

Instrument the entry-free/drain path in the SP05 trace (C++ hook change) and run 1-2 pilots if a lifecycle-complete chain is required. Approval required.
