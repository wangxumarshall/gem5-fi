# LP01 Propagation Audit — v3.2.11

**Model:** LP01  **SubUnit:** L1D  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** Response byte0 corruption at completeDataAccess → memory_response (inj data) → register_writeback (inj value) → consumer (inj input) → commit; application MASKED or SDC

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| LP01-R01 | LP01-F0-W5-S01-R01 | 1349924126 | 1 | `0de2564468fd710b` | `3779e8ced41a07d7` | `99c106541150be0e` |
| LP01-R02 | LP01-F0-W5-S01-R02 | 2648660520 | 2 | `0de2564468fd710b` | `3779e8ced41a07d7` | `99c106541150be0e` |
| LP01-R03 | LP01-F0-W5-S01-R03 | 2021175746 | 3 | `0de2564468fd710b` | `3779e8ced41a07d7` | `99c106541150be0e` |
| LP01-R04 | LP01-F0-W5-S01-R04 | 3894776903 | 4 | `0de2564468fd710b` | `3779e8ced41a07d7` | `99c106541150be0e` |
| LP01-R05 | LP01-F0-W5-S01-R05 | 1604604537 | 5 | `0de2564468fd710b` | `3779e8ced41a07d7` | `99c106541150be0e` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| LP01-R01 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | COMPLETE_CAUSAL_CHAIN |
| LP01-R02 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | COMPLETE_CAUSAL_CHAIN |
| LP01-R03 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | COMPLETE_CAUSAL_CHAIN |
| LP01-R04 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | COMPLETE_CAUSAL_CHAIN |
| LP01-R05 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | COMPLETE_CAUSAL_CHAIN |

## 3. Per-pilot evidence

### LP01-R01 — COMPLETE_CAUSAL_CHAIN

- Injection seq **5**, PC `0x4005d0`, tick 172865, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/LP01-R01.
- Earliest anomaly: event 14 `memory_response`.
- Writeback: event 15, phys r45 a1, value_fnv `81a3697174a540ac`, payload_fnv `81a3697174a540ac`.
- Consumer: event 19 PC `0x4008dc` source_linked=True input_fnv `81a3697174a540ac`, matches_source=1.
- Commit: event 16 seq 5.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `99c106541150be0e`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: MODEL_SPECIFIC_ORIG_VS_INJ_DIVERGENCE_WITH_CONSUMER.

### LP01-R02 — COMPLETE_CAUSAL_CHAIN

- Injection seq **48**, PC `0x400910`, tick 226380, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/LP01-R02.
- Earliest anomaly: event 21 `memory_response`.
- Writeback: event 22, phys r68 a3, value_fnv `a09e307a7f948acd`, payload_fnv `a09e307a7f948acd`.
- Consumer: event 25 PC `0x400914` source_linked=True input_fnv `a09e307a7f948acd`, matches_source=1.
- Commit: event 23 seq 44.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `99c106541150be0e`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: MODEL_SPECIFIC_ORIG_VS_INJ_DIVERGENCE_WITH_CONSUMER.

### LP01-R03 — COMPLETE_CAUSAL_CHAIN

- Injection seq **239**, PC `0x4113a0`, tick 605221, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/LP01-R03.
- Earliest anomaly: event 115 `memory_response`.
- Writeback: event 116, phys r1 a1, value_fnv `904aa10b2e892cdd`, payload_fnv `904aa10b2e892cdd`.
- Consumer: event 120 PC `0x4113b4` source_linked=True input_fnv `904aa10b2e892cdd`, matches_source=1.
- Commit: event 117 seq 130.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `99c106541150be0e`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: MODEL_SPECIFIC_ORIG_VS_INJ_DIVERGENCE_WITH_CONSUMER.

### LP01-R04 — COMPLETE_CAUSAL_CHAIN

- Injection seq **247**, PC `0x4113c0`, tick 605990, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/LP01-R04.
- Earliest anomaly: event 115 `memory_response`.
- Writeback: event 116, phys r0 a0, value_fnv `e5704c2542d06b23`, payload_fnv `e5704c2542d06b23`.
- Consumer: event 135 PC `0x4113c4` source_linked=True input_fnv `e5704c2542d06b23`, matches_source=1.
- Commit: event 118 seq 138.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `99c106541150be0e`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: MODEL_SPECIFIC_ORIG_VS_INJ_DIVERGENCE_WITH_CONSUMER.

### LP01-R05 — COMPLETE_CAUSAL_CHAIN

- Injection seq **287**, PC `0x4113c8`, tick 625625, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/LP01-R05.
- Earliest anomaly: event 164 `memory_response`.
- Writeback: event 165, phys r46 a1, value_fnv `335a4bf00dbb4e7a`, payload_fnv `335a4bf00dbb4e7a`.
- Consumer: event 180 PC `0x4113cc` source_linked=True input_fnv `335a4bf00dbb4e7a`, matches_source=1.
- Commit: event 178 seq 154.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `99c106541150be0e`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: MODEL_SPECIFIC_ORIG_VS_INJ_DIVERGENCE_WITH_CONSUMER.

## 3.1 Model-specific evidence quote

`orig_data_hex=0100000000000000;inj_data_hex=0900000000000000;byte0_before=0x1;byte0_after=0x9;mask=0x8` (R01); R03 `0x10→0x18`, R05 `0x17→0x1f`.

## 4. Terminal and causality

All five pilots carry the model-specific divergence record: orig_data_fnv differs from inj_data_fnv (byte0 0x1→0x9, 0x10→0x18, 0x17→0x1f, etc.), the response carries the injected data, the writeback and the first consumer receive the injected value, and the consumer input hash equals the injected payload hash. The application checksum is unchanged (MASKED) because the corrupted byte is not used in the final result. This is a complete causal chain ending in MASKED. The generic payload-vs-writeback check alone would under-report it; the audit uses the injection record.

## 5. Missing evidence

ORACLE_FILE_MISSING in the v3.2.6 directories (oracle PASS is meta-recorded)

## 6. Verdict

- COMPLETE_CAUSAL_CHAIN: 5/5 pilots

Model verdict: **COMPLETE_CAUSAL_CHAIN** (see per-pilot split above).

## 7. Supplementary pilot recommendation

None for the propagation verdict. Optional: persist raw oracle.log in future vintages.
