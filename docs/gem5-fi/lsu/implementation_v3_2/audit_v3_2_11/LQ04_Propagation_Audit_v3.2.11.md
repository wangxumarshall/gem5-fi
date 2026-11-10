# LQ04 Propagation Audit — v3.2.11

**Model:** LQ04  **SubUnit:** LQ  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** LQ entry valid/request cleared → response via senderState → register_writeback (correct payload) → consumer → commit; the fault effect is the invalid window

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| LQ04-R01 | LQ04-F0-W2-S01-R01 | 1842987246 | 1 | `f3c2a4423aab81ca` | `fa25f785a4822eb5` | `b097eb83f71545cb` |
| LQ04-R02 | LQ04-F0-W2-S01-R02 | 2188214204 | 2 | `f3c2a4423aab81ca` | `fa25f785a4822eb5` | `b097eb83f71545cb` |
| LQ04-R03 | LQ04-F0-W2-S01-R03 | 3953171871 | 3 | `f3c2a4423aab81ca` | `fa25f785a4822eb5` | `b097eb83f71545cb` |
| LQ04-R04 | LQ04-F0-W2-S01-R04 | 4153250964 | 4 | `f3c2a4423aab81ca` | `fa25f785a4822eb5` | `b097eb83f71545cb` |
| LQ04-R05 | LQ04-F0-W2-S01-R05 | 3410523942 | 5 | `f3c2a4423aab81ca` | `fa25f785a4822eb5` | `b097eb83f71545cb` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| LQ04-R01 | yes | yes | yes | yes | yes | yes | yes | MASKED | yes | LIFECYCLE_ONLY |
| LQ04-R02 | yes | yes | yes | yes | yes | yes | yes | MASKED | yes | LIFECYCLE_ONLY |
| LQ04-R03 | yes | yes | yes | yes | yes | yes | yes | MASKED | yes | LIFECYCLE_ONLY |
| LQ04-R04 | yes | yes | yes | yes | yes | yes | yes | MASKED | yes | LIFECYCLE_ONLY |
| LQ04-R05 | yes | yes | yes | yes | yes | yes | yes | MASKED | yes | LIFECYCLE_ONLY |

## 3. Per-pilot evidence

### LQ04-R01 — LIFECYCLE_ONLY

- Injection seq **3**, PC `0x400338`, tick 80080, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R01.
- Earliest anomaly: event 8 `memory_response`.
- Writeback: event 9, phys r44 a2, value_fnv `c6d4496e17859d5`, payload_fnv `c6d4496e17859d5`.
- Consumer: event 18 PC `0x40034c` source_linked=True input_fnv `c6d4496e17859d5`, matches_source=1.
- Commit: event 10 seq 3.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `b097eb83f71545cb`, actual `b097eb83f71545cb`, pass=True.
- Missing: none.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### LQ04-R02 — LIFECYCLE_ONLY

- Injection seq **4**, PC `0x40033c`, tick 80465, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R02.
- Earliest anomaly: event 8 `memory_response`.
- Writeback: event 9, phys r45 a3, value_fnv `46f9187bab44bc35`, payload_fnv `46f9187bab44bc35`.
- Consumer: event 18 PC `0x400350` source_linked=True input_fnv `46f9187bab44bc35`, matches_source=1.
- Commit: event 11 seq 4.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `b097eb83f71545cb`, actual `b097eb83f71545cb`, pass=True.
- Missing: none.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### LQ04-R03 — LIFECYCLE_ONLY

- Injection seq **5**, PC `0x400340`, tick 133210, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R03.
- Earliest anomaly: event 8 `memory_response`.
- Writeback: event 9, phys r46 a4, value_fnv `14fe41788a431ad5`, payload_fnv `14fe41788a431ad5`.
- Consumer: event 18 PC `0x400354` source_linked=True input_fnv `14fe41788a431ad5`, matches_source=1.
- Commit: event 12 seq 5.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `b097eb83f71545cb`, actual `b097eb83f71545cb`, pass=True.
- Missing: none.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### LQ04-R04 — LIFECYCLE_ONLY

- Injection seq **6**, PC `0x400344`, tick 133595, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R04.
- Earliest anomaly: event 12 `memory_response`.
- Writeback: event 13, phys r47 a5, value_fnv `4f8a555d540fe9f5`, payload_fnv `4f8a555d540fe9f5`.
- Consumer: event 18 PC `0x400358` source_linked=True input_fnv `4f8a555d540fe9f5`, matches_source=1.
- Commit: event 14 seq 6.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `b097eb83f71545cb`, actual `b097eb83f71545cb`, pass=True.
- Missing: none.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

### LQ04-R05 — LIFECYCLE_ONLY

- Injection seq **7**, PC `0x400348`, tick 133980, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R05.
- Earliest anomaly: event 12 `memory_response`.
- Writeback: event 13, phys r48 a6, value_fnv `f9468ffeedcb9ad5`, payload_fnv `f9468ffeedcb9ad5`.
- Consumer: event 19 PC `0x40035c` source_linked=True input_fnv `f9468ffeedcb9ad5`, matches_source=1.
- Commit: event 15 seq 7.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `b097eb83f71545cb`, actual `b097eb83f71545cb`, pass=True.
- Missing: none.
- Classification rule: STORE_OR_ENTRY_LIFECYCLE_ONLY.

## 3.1 Model-specific evidence quote

`valid_before=1;valid_after=0;request_before=1;request_after=0;data_unchanged=1;no_pop=1;no_reuse=1`.

## 4. Terminal and causality

All five pilots reproduce the frozen v3.2.10 verdict: the structural chain is complete, but every writeback and consumer carries the correct payload (data_corruption=0, consumer_input_matches_source=1), and the oracle PASSes. The fault effect is confined to the LQ entry lifecycle; PROPAGATION_VERIFIED=0.

## 5. Missing evidence

none for the lifecycle verdict

## 6. Verdict

- LIFECYCLE_ONLY: 5/5 pilots

Model verdict: **LIFECYCLE_ONLY** (see per-pilot split above).

## 7. Supplementary pilot recommendation

None; the literal definition is frozen and must not be changed to obtain SDC.
