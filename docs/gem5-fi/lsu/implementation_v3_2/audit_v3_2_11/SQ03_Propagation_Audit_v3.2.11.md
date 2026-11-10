# SQ03 Propagation Audit — v3.2.11

**Model:** SQ03  **SubUnit:** SQ  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** Premature _canWB at commitStores → store_writeback → store_mem_write → completeStore; a later load consuming the lane would extend the chain

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| SQ03-R01@evidence | SQ03-F0-W3-S02-R01 | 2214819981 | 1 | `b988b7503cdf1fea` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |
| SQ03-R02@evidence | SQ03-F0-W3-S02-R02 | 1486471869 | 2 | `b988b7503cdf1fea` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |
| SQ03-R03@evidence | SQ03-F0-W3-S02-R03 | 3102670938 | 3 | `b988b7503cdf1fea` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |
| SQ03-R04@evidence | SQ03-F0-W3-S02-R04 | 3974203372 | 4 | `b988b7503cdf1fea` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |
| SQ03-R05@evidence | SQ03-F0-W3-S02-R05 | 729970077 | 5 | `b988b7503cdf1fea` | `d423539c68ec2b4f` | `ba3b3185e541ad03` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| SQ03-R01@evidence | yes | yes | yes | yes | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |
| SQ03-R02@evidence | yes | yes | yes | yes | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |
| SQ03-R03@evidence | yes | yes | yes | yes | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |
| SQ03-R04@evidence | yes | yes | yes | yes | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |
| SQ03-R05@evidence | yes | yes | yes | yes | missing | missing | yes | MASKED | yes | LIFECYCLE_ONLY |

## 3. Per-pilot evidence

### SQ03-R01@evidence — LIFECYCLE_ONLY

- Injection seq **18**, PC `0x4008d0`, tick 140910, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ03_v3_2_8/SQ03-R01.
- Earliest anomaly: event 8 `store_writeback`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 17 seq 14.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SQ03-R02@evidence — LIFECYCLE_ONLY

- Injection seq **19**, PC `0x4008d0`, tick 141295, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ03_v3_2_8/SQ03-R02.
- Earliest anomaly: event 16 `store_writeback`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 15 seq 15.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SQ03-R03@evidence — LIFECYCLE_ONLY

- Injection seq **23**, PC `0x4008d8`, tick 141680, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ03_v3_2_8/SQ03-R03.
- Earliest anomaly: event 16 `store_writeback`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 15 seq 19.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SQ03-R04@evidence — LIFECYCLE_ONLY

- Injection seq **24**, PC `0x4008d8`, tick 142065, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ03_v3_2_8/SQ03-R04.
- Earliest anomaly: event 16 `store_writeback`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 15 seq 20.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### SQ03-R05@evidence — LIFECYCLE_ONLY

- Injection seq **28**, PC `0x4008e4`, tick 142450, detail epoch docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ03_v3_2_8/SQ03-R05.
- Earliest anomaly: event 16 `store_writeback`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 15 seq 24.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `ba3b3185e541ad03`, actual `ba3b3185e541ad03`, pass=True.
- Missing: NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

## 3.1 Model-specific evidence quote

`site=executeStore_canWB;canwb_before=0;canwb_after=1;stores_to_wb_before=0;stores_to_wb_after=1;inject_tick=140910`.

## 4. Terminal and causality

All five pilots show premature writeback permission, the store data write and completion, but no later load consumes the lane; the terminal is MASKED with STORE_COMMITTED_LANE_NOT_READ. The fault effect stays in the store-queue lifecycle.

## 5. Missing evidence

NO_REGISTER_WRITEBACK_EVENT/NO_CONSUMER_EDGE (no load of the lane) in 5/5

## 6. Verdict

- LIFECYCLE_ONLY: 5/5 pilots

Model verdict: **LIFECYCLE_ONLY** (see per-pilot split above).

## 7. Supplementary pilot recommendation

A same-address reload workload would be required to test propagation: 5 pilots, preserved identities. Not executed.
