# FW05 Propagation Audit — v3.2.11

**Model:** FW05  **SubUnit:** FWD  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** Wrong older-store source → forwarding_decision (selected alt_store) → load data = alt data → register_writeback → consumer → commit → application SDC

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| FW05-R01@evidence | FW05-F6-W8-S01-R01 | 1025137124 | 1 | `8377c011bb5916be` | `0cf405092e338827` | `67afad307642983e` |
| FW05-R02@evidence | FW05-F6-W8-S01-R02 | 1653118510 | 2 | `8377c011bb5916be` | `0cf405092e338827` | `67afad307642983e` |
| FW05-R03@evidence | FW05-F6-W8-S01-R03 | 2442802213 | 3 | `8377c011bb5916be` | `0cf405092e338827` | `67afad307642983e` |
| FW05-R04@evidence | FW05-F6-W8-S01-R04 | 899944922 | 4 | `8377c011bb5916be` | `0cf405092e338827` | `67afad307642983e` |
| FW05-R05@evidence | FW05-F6-W8-S01-R05 | 2836530945 | 5 | `8377c011bb5916be` | `0cf405092e338827` | `67afad307642983e` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| FW05-R01@evidence | yes | yes | yes | yes | yes | missing | missing | SQUASHED | yes | PARTIAL |
| FW05-R02@evidence | yes | yes | yes | yes | yes | yes | yes | SDC | yes | COMPLETE_CAUSAL_CHAIN |
| FW05-R03@evidence | yes | yes | yes | yes | yes | yes | yes | SDC | yes | COMPLETE_CAUSAL_CHAIN |
| FW05-R04@evidence | yes | yes | yes | yes | yes | yes | yes | SDC | yes | COMPLETE_CAUSAL_CHAIN |
| FW05-R05@evidence | yes | yes | yes | yes | yes | yes | yes | SDC | yes | COMPLETE_CAUSAL_CHAIN |

## 3. Per-pilot evidence

### FW05-R01@evidence — PARTIAL

- Injection seq **12114**, PC `0x400564`, tick 15969415, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/FW05_v3_2_7/FW05-R01.
- Earliest anomaly: event 5033 `forwarding_decision`.
- Writeback: event 5034, phys r122 a0, value_fnv `6407d731d902cbed`, payload_fnv `6407d731d902cbed`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `MASKED`).
- Oracle: expected `67afad307642983e`, actual `67afad307642983e`, pass=True.
- Missing: NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: SQUASHED_BEFORE_CONSUMER.

### FW05-R02@evidence — COMPLETE_CAUSAL_CHAIN

- Injection seq **12156**, PC `0x400564`, tick 16032170, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/FW05_v3_2_7/FW05-R02.
- Earliest anomaly: event 5047 `forwarding_decision`.
- Writeback: event 5048, phys r3 a0, value_fnv `a06ea71be9c5aa88`, payload_fnv `a06ea71be9c5aa88`.
- Consumer: event 5055 PC `0x400568` source_linked=True input_fnv `a06ea71be9c5aa88`, matches_source=1.
- Commit: event 5052 seq 5810.
- Terminal: `SDC` / `ORACLE_FAIL` (observed `SDC`).
- Oracle: expected `67afad307642983e`, actual `549c9e0347adaf23`, pass=False.
- Missing: none.
- Classification rule: ALT_SOURCE_DATA_REACHED_CONSUMER_AND_ORACLE_FAILED.

### FW05-R03@evidence — COMPLETE_CAUSAL_CHAIN

- Injection seq **12191**, PC `0x400564`, tick 16039870, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/FW05_v3_2_7/FW05-R03.
- Earliest anomaly: event 5062 `forwarding_decision`.
- Writeback: event 5063, phys r93 a0, value_fnv `141ad82d6cd5f32f`, payload_fnv `141ad82d6cd5f32f`.
- Consumer: event 5070 PC `0x400568` source_linked=True input_fnv `141ad82d6cd5f32f`, matches_source=1.
- Commit: event 5067 seq 5829.
- Terminal: `SDC` / `ORACLE_FAIL` (observed `SDC`).
- Oracle: expected `67afad307642983e`, actual `549c9e0347adaf25`, pass=False.
- Missing: none.
- Classification rule: ALT_SOURCE_DATA_REACHED_CONSUMER_AND_ORACLE_FAILED.

### FW05-R04@evidence — COMPLETE_CAUSAL_CHAIN

- Injection seq **12226**, PC `0x400564`, tick 16047570, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/FW05_v3_2_7/FW05-R04.
- Earliest anomaly: event 5075 `forwarding_decision`.
- Writeback: event 5076, phys r45 a0, value_fnv `fe9b431f6a056432`, payload_fnv `fe9b431f6a056432`.
- Consumer: event 5083 PC `0x400568` source_linked=True input_fnv `fe9b431f6a056432`, matches_source=1.
- Commit: event 5080 seq 5848.
- Terminal: `SDC` / `ORACLE_FAIL` (observed `SDC`).
- Oracle: expected `67afad307642983e`, actual `549c9e0347adaf27`, pass=False.
- Missing: none.
- Classification rule: ALT_SOURCE_DATA_REACHED_CONSUMER_AND_ORACLE_FAILED.

### FW05-R05@evidence — COMPLETE_CAUSAL_CHAIN

- Injection seq **12261**, PC `0x400564`, tick 16055270, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/FW05_v3_2_7/FW05-R05.
- Earliest anomaly: event 5088 `forwarding_decision`.
- Writeback: event 5089, phys r126 a0, value_fnv `5b96aecb6003c639`, payload_fnv `5b96aecb6003c639`.
- Consumer: event 5096 PC `0x400568` source_linked=True input_fnv `5b96aecb6003c639`, matches_source=1.
- Commit: event 5093 seq 5867.
- Terminal: `SDC` / `ORACLE_FAIL` (observed `SDC`).
- Oracle: expected `67afad307642983e`, actual `549c9e0347adaf19`, pass=False.
- Missing: none.
- Classification rule: ALT_SOURCE_DATA_REACHED_CONSUMER_AND_ORACLE_FAILED.

## 3.1 Model-specific evidence quote

`true_store_seq=12155;alt_store_seq=12154;true_data_fnv=12446998b6871244;alt_data_fnv=a06ea71be9c5aa88;selected_source=alt_store`; oracle `got=549c9e0347adaf23` vs golden `67afad307642983e`.

## 4. Terminal and causality

R02-R05 are complete SDC chains. The injection record names true_store_seq and alt_store_seq, with true_data_fnv != alt_data_fnv; selected_source=alt_store; the writeback and the first consumer carry the alt data hash; the oracle FAIL prints checksums 0x549c9e0347adaf23/f25/f27/f19 against golden 0x67ad…398e. R01 is SQUASHED before a consumer (PARTIAL).

## 5. Missing evidence

R01 squash causality unproven; no other gap

## 6. Verdict

- COMPLETE_CAUSAL_CHAIN: 4/5 pilots
- PARTIAL: 1/5 pilots

Model verdict: **COMPLETE_CAUSAL_CHAIN** (see per-pilot split above).

## 7. Supplementary pilot recommendation

None for R02-R05. Optional: trace the R01 squash reason to classify it.
