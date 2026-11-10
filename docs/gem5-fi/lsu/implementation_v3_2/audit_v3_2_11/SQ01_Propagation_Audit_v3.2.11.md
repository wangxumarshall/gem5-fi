# SQ01 Propagation Audit — v3.2.11

**Model:** SQ01  **SubUnit:** SQ  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** Store data byte0 corruption → store_writeback → store_mem_write → a later Load reads the lane → memory_response → register_writeback → consumer → commit

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| SQ01-R01@evidence | PILOT-SQ01-R01 | 591611458 | 1 | `8eb7ce8d76ab63d9` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |
| SQ01-R02@evidence | PILOT-SQ01-R02 | 576447973 | 2 | `8eb7ce8d76ab63d9` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |
| SQ01-R03@evidence | PILOT-SQ01-R03 | 1257175390 | 3 | `8eb7ce8d76ab63d9` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |
| SQ01-R04@evidence | PILOT-SQ01-R04 | 3116972755 | 4 | `8eb7ce8d76ab63d9` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |
| SQ01-R05@evidence | PILOT-SQ01-R05 | 172636228 | 5 | `8eb7ce8d76ab63d9` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| SQ01-R01@evidence | yes | yes | missing | missing | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |
| SQ01-R02@evidence | yes | yes | missing | missing | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |
| SQ01-R03@evidence | yes | yes | missing | missing | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |
| SQ01-R04@evidence | yes | yes | missing | missing | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |
| SQ01-R05@evidence | yes | yes | missing | missing | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |

## 3. Per-pilot evidence

### SQ01-R01@evidence — LIFECYCLE_ONLY

- Injection seq **18**, PC `0x4008d0`, tick 140910, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ01_v3_2_3/SQ01-R01.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 15 seq 14.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_INTERMEDIATE_PROPAGATION_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SQ01-R02@evidence — LIFECYCLE_ONLY

- Injection seq **19**, PC `0x4008d0`, tick 141295, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ01_v3_2_3/SQ01-R02.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 15 seq 15.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_INTERMEDIATE_PROPAGATION_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SQ01-R03@evidence — LIFECYCLE_ONLY

- Injection seq **23**, PC `0x4008d8`, tick 141680, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ01_v3_2_3/SQ01-R03.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 15 seq 19.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_INTERMEDIATE_PROPAGATION_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SQ01-R04@evidence — LIFECYCLE_ONLY

- Injection seq **24**, PC `0x4008d8`, tick 142065, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ01_v3_2_3/SQ01-R04.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 15 seq 20.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_INTERMEDIATE_PROPAGATION_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SQ01-R05@evidence — LIFECYCLE_ONLY

- Injection seq **28**, PC `0x4008e4`, tick 142450, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ01_v3_2_3/SQ01-R05.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 15 seq 24.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_EARLY_ANOMALY_EVENT, NO_INTERMEDIATE_PROPAGATION_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

## 3.1 Model-specific evidence quote

`site=lsq_write_sq_entry;mode=sq01_bit3;queue=SQ;index=1;generation=1;old_byte=0x0;new_byte=0x8;value_changed=1`.

## 4. Terminal and causality

All five pilots show the corrupted store data reaching store_writeback and the L1D write. No later load reads the corrupted lane in any pilot; the terminal is MASKED with reason STORE_COMMITTED_LANE_NOT_READ. The fault effect stops at the store-queue/cache state; it is not a data-propagation chain.

## 5. Missing evidence

NO_CONSUMER_EDGE (no later load of the lane) in 5/5; NO_EARLY_ANOMALY_EVENT (the trace has no explicit byte0 old/new anomaly node)

## 6. Verdict

- LIFECYCLE_ONLY: 5/5 pilots

Model verdict: **LIFECYCLE_ONLY** (see per-pilot split above).

## 7. Supplementary pilot recommendation

A workload with a same-address reload after the store is required to test propagation: 5 pilots with preserved identities. Not executed this round.
