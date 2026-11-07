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

### R02 — MASKED (target committed, value present, oracle PASS)

- Excel identity: `LP01-F0-W5-S01-R02`, seed `2648660520`, Excel ordinal 2,
  clinical ordinal **2**.
- Injection: seq 48, tick 226380, addr `0x80e28`, size 8, mask `0x8`,
  request tick 225610, LQ entry 2 / generation 2, phys reg `int:68`.
  - `orig_data_hex=0000000000000000` (`fnv=a8c7f832281a39c5`)
  - `inj_data_hex=0800000000000000` (`fnv=a09e307a7f948acd`)
  - only byte 0 changed: `0x00 -> 0x08`; address/size unchanged.
- Response: `data_hex=0800000000000000`, `data_fnv=a09e307a7f948acd`,
  `response_id=1`, `request_tick=225610`, `response_tick=226380`.
- Actual register writeback: `writeback_value=8`,
  `writeback_value_fnv=a09e307a7f948acd`,
  `hash_basis=payload_equals_regval`, `value_matches_payload=1`,
  `phys_reg=68`, `arch_reg=3`.
- First consumer: seq 50, pc `0x400914`, `consumer_input_value=8`,
  `consumer_input_fnv=a09e307a7f948acd`,
  `consumer_input_matches_source=1` (1 consumer commit).
- Commit: seq 48, `commit_seq=44`, `is_load=1`.
- Oracle: PASS (`checksum=0x99c106541150be0e`).
- Terminal: **MASKED** / `TARGET_COMMITTED_DATA_VALUE_PRESENT`.
- Trace: coverage COMPLETE, chain integrity PASS, validator VALID.

### R03 — MASKED (target committed, value present, oracle PASS)

- Excel identity: `LP01-F0-W5-S01-R03`, seed `2021175746`, Excel ordinal 3,
  clinical ordinal **3**.
- Injection: seq 239, tick 605221, addr `0x80e30`, size 8, mask `0x8`,
  request tick 573650, LQ entry 3 / generation 4, phys reg `int:1`.
  - `orig_data_hex=1000000000000000` (`fnv=987468c2d70edbd5`)
  - `inj_data_hex=1800000000000000` (`fnv=904aa10b2e892cdd`)
  - only byte 0 changed: `0x10 -> 0x18`; address/size unchanged.
- Response: `data_hex=1800000000000000`, `data_fnv=904aa10b2e892cdd`,
  `response_id=1`, `request_tick=573650`, `response_tick=605221`.
- Actual register writeback: `writeback_value=18`,
  `writeback_value_fnv=904aa10b2e892cdd`,
  `hash_basis=payload_equals_regval`, `value_matches_payload=1`,
  `phys_reg=1`, `arch_reg=1`.
- First consumer: seq 244, pc `0x4113b4`, `consumer_input_value=18`,
  `consumer_input_fnv=904aa10b2e892cdd`,
  `consumer_input_matches_source=1` (6 consumer commits).
- Commit: seq 239, `commit_seq=130`, `is_load=1`.
- Oracle: PASS (`checksum=0x99c106541150be0e`).
- Terminal: **MASKED** / `TARGET_COMMITTED_DATA_VALUE_PRESENT`.
- Trace: coverage COMPLETE, chain integrity PASS, validator VALID.

### R04 — MASKED (target committed, value present, oracle PASS)

- Excel identity: `LP01-F0-W5-S01-R04`, seed `3894776903`, Excel ordinal 4,
  clinical ordinal **4**.
- Injection: seq 247, tick 605990, addr `0x80e38`, size 8, mask `0x8`,
  request tick 600600, LQ entry 4 / generation 5, phys reg `int:0`.
  - `orig_data_hex=fbf7d0cc00000000` (`fnv=1505defdf2164c5b`)
  - `inj_data_hex=f3f7d0cc00000000` (`fnv=e5704c2542d06b23`)
  - only byte 0 changed: `0xfb -> 0xf3`; address/size unchanged.
- Response: `data_hex=f3f7d0cc00000000`, `data_fnv=e5704c2542d06b23`,
  `response_id=1`, `request_tick=600600`, `response_tick=605990`.
- Actual register writeback: `writeback_value=ccd0f7f3`
  (i.e. 0x00000000ccd0f7f3),
  `writeback_value_fnv=e5704c2542d06b23`,
  `hash_basis=payload_equals_regval`, `value_matches_payload=1`,
  `phys_reg=0`, `arch_reg=0`.
- First consumer: seq 248, pc `0x4113c4`, `src_idx=2`,
  `consumer_input_value=ccd0f7f3`,
  `consumer_input_fnv=e5704c2542d06b23`,
  `consumer_input_matches_source=1` (1 consumer commit).
- Commit: seq 247, `commit_seq=138`, `is_load=1`.
- Oracle: PASS (`checksum=0x99c106541150be0e`).
- Terminal: **MASKED** / `TARGET_COMMITTED_DATA_VALUE_PRESENT`.
- Trace: coverage COMPLETE, chain integrity PASS, validator VALID.
