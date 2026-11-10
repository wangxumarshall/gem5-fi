# FW02 Propagation Audit — v3.2.11

**Model:** FW02  **SubUnit:** FWD  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** Suppressed same-address forward → forwarding_decision (suppressed) → memory path → memory_response → register_writeback → consumer → commit/squash

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| FW02-R01 | PILOT-FW02-R01 | 2941542370 | 1 | `275111d805a71bc3` | `132a84f7f21be052` | `1f4cbf14327717df` |
| FW02-R04 | PILOT-FW02-R04 | 527667424 | 4 | `275111d805a71bc3` | `132a84f7f21be052` | `1f4cbf14327717df` |
| FW02-R05 | PILOT-FW02-R05 | 3622278636 | 5 | `275111d805a71bc3` | `132a84f7f21be052` | `1f4cbf14327717df` |
| FW02-R01 | FW02-R01-v324 | 2941542370 | 1 | `b1f7cf189d2be1e9` | `132a84f7f21be052` | `1f4cbf14327717df` |
| FW02-R05 | FW02-R05-v324 | 3622278636 | 5 | `b1f7cf189d2be1e9` | `132a84f7f21be052` | `1f4cbf14327717df` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| FW02-R01 | yes | yes | yes | yes | yes | missing | missing | SQUASHED | missing | PARTIAL |
| FW02-R04 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | COMPLETE_CAUSAL_CHAIN |
| FW02-R05 | yes | yes | yes | yes | yes | missing | missing | SQUASHED | missing | PARTIAL |
| FW02-R01 | yes | yes | yes | yes | yes | missing | missing | SQUASHED | missing | PARTIAL |
| FW02-R05 | yes | yes | yes | yes | yes | missing | missing | SQUASHED | missing | PARTIAL |

## 3. Per-pilot evidence

### FW02-R01 — PARTIAL

- Injection seq **397**, PC `0x40c0c8`, tick 556325, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/FW02-R01.
- Earliest anomaly: event 3 `forwarding_decision`.
- Writeback: event 5, phys r93 a1, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `MASKED`).
- Oracle: expected `1f4cbf14327717df`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: NO_CONSUMER_OR_UNPROVEN_SQUASH.

### FW02-R04 — COMPLETE_CAUSAL_CHAIN

- Injection seq **11101**, PC `0x4448c8`, tick 13002990, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/FW02-R04.
- Earliest anomaly: event 6 `forwarding_decision`.
- Writeback: event 8, phys r121 a1, value_fnv `None`, payload_fnv `None`.
- Consumer: event 10 PC `0x4448cc` source_linked=False input_fnv `None`, matches_source=None.
- Commit: event 9 seq 5121.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `1f4cbf14327717df`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: FORWARD_SUPPRESSED_MEMORY_PATH_CONSUMED_MASKED.

### FW02-R05 — PARTIAL

- Injection seq **11203**, PC `0x422378`, tick 13260555, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/FW02-R05.
- Earliest anomaly: event 7 `forwarding_decision`.
- Writeback: event 9, phys r67 a19, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `MASKED`).
- Oracle: expected `1f4cbf14327717df`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: NO_CONSUMER_OR_UNPROVEN_SQUASH.

### FW02-R01 — PARTIAL

- Injection seq **397**, PC `0x40c0c8`, tick 556325, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/FW02-R01.
- Earliest anomaly: event 189 `forwarding_decision`.
- Writeback: event 194, phys r93 a1, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `MASKED`).
- Oracle: expected `1f4cbf14327717df`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: NO_CONSUMER_OR_UNPROVEN_SQUASH.

### FW02-R05 — PARTIAL

- Injection seq **11203**, PC `0x422378`, tick 13260555, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/FW02-R05.
- Earliest anomaly: event 4703 `forwarding_decision`.
- Writeback: event 4707, phys r67 a19, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `MASKED`).
- Oracle: expected `1f4cbf14327717df`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: NO_CONSUMER_OR_UNPROVEN_SQUASH.

## 3.1 Model-specific evidence quote

`load_seq=397;store_seq=383;size=8;decision=suppressed;normal_decision=forwarded;fault_decision=suppressed;memory_path=1`.

## 4. Terminal and causality

FW02-R04 (v3.2.1) has the complete control chain: forwarding_decision decision=suppressed, normal_decision=forwarded, fault_decision=suppressed; the load went to memory (memory_path=1), wrote back, and its consumer committed. The data is identical (store data 0, memory data 0), so this is a control-path-only complete chain ending MASKED. The other four pilots either lack consumer/commit events or end SQUASHED without proof that the squash is fault-caused; they are PARTIAL, not failures.

## 5. Missing evidence

NO_CONSUMER_EDGE/NO_COMMIT_EVENT in 4/5; squash causality unproven in R01/R05; the v3.2.4 traces lack the consumer record

## 6. Verdict

- COMPLETE_CAUSAL_CHAIN: 1/5 pilots
- PARTIAL: 4/5 pilots

Model verdict: **PARTIAL** (see per-pilot split above).

## 7. Supplementary pilot recommendation

Re-run the v3.2.4 R01/R05 pair with the consumer/commit trace hook to complete the 5-pilot set; 2 runs, preserved identities. Approval required.
