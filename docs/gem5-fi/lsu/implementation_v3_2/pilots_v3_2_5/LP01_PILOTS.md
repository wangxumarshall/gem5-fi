# LP01 — Five Pilot Results (LSU v3.2.5)

**Date:** 2026-11-08
**Binary:** `build/ARM/gem5.opt` sha256 `69a1ca9c5b1cbfb160d0502a8cad8acf7d17101625228978ec79ede588b2287d`
**Workload:** `implementation_v3_2/workloads/load_response` (W5)
**Event selection:** `TEMPORARY_EVENT_SELECTION` — Excel SampleRunID/Seed/EventOrdinal
are frozen; the clinical ordinal used for each pilot is recorded in
`LP01_EVENT_SELECTION.md` and in `pilot_meta.json`
(`excel_identity.event_ordinal` vs `event_ordinal_used`).
Warm-up/ROI are not frozen.

## Model definition (Excel v3.2.1 Sheet 3/4/5)

`TargetField=Packet::data[0]`, `BitEntryByteIndex=byte0 bit3`,
`FaultValue=data[0] ^= 0x08（严格按size逐字节）`, recommended option A.
The injected fault changes exactly response byte 0 by XOR 0x08; address,
access size and request identity are unchanged. The five pilots use
`fault_mask=0x8`, `maxFaults=1`, probability 1.0.

## Per-pilot evidence

### R01 — MASKED (target committed, value present, oracle PASS)

- Excel identity: `LP01-F0-W5-S01-R01`, seed `1349924126`, Excel ordinal 1,
  clinical ordinal **1**.
- Injection: seq 5, tick 172865, addr `0x80e10`, size 8, mask `0x8`,
  request tick 80080, LQ entry 1 / generation 1, phys reg `int:45`.
  - `orig_data_hex=0100000000000000` (`fnv=89cd31291d2aefa4`)
  - `inj_data_hex=0900000000000000` (`fnv=81a3697174a540ac`)
  - only byte 0 changed: `0x01 -> 0x09` (bit 3); address/size unchanged.
- Response (post-injection): `data_hex=0900000000000000`,
  `data_fnv=81a3697174a540ac`, `response_id=1`.
- Actual register writeback: `writeback_value=9`,
  `writeback_value_fnv=81a3697174a540ac`,
  `hash_basis=payload_equals_regval`, `value_matches_payload=1`,
  `phys_reg=45`, `arch_reg=1`.
- First consumer: seq 25, pc `0x4008dc`, `consumer_input_value=9`,
  `consumer_input_fnv=81a3697174a540ac`,
  `consumer_input_matches_source=1`; 183 consumer commits on the chain.
- Commit: seq 5, `commit_seq=5`, `is_load=1`.
- Oracle: PASS (`checksum=0x99c106541150be0e`, golden `0x99c106541150be0e`).
- Terminal: **MASKED** / `TARGET_COMMITTED_DATA_VALUE_PRESENT`.
- Trace: coverage COMPLETE, chain integrity PASS, validator VALID.
