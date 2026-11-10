# DA04 Propagation Audit — v3.2.11

**Model:** DA04  **SubUnit:** SQ  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** Byte-enable 0xF→0xE → store_writeback (lane0 disabled) → store_mem_write (lane0 unchanged) → later load response with stale lane0 → register_writeback → consumer → application oracle

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| DA04-R04 | DA04-F0-W8-S02-R04 | 3815557835 | 4 | `0de2564468fd710b` | `89ff937a73a01708` | `3f89eab79392ce69` |
| DA04-R05 | DA04-F0-W8-S02-R05 | 2016743094 | 5 | `0de2564468fd710b` | `89ff937a73a01708` | `3f89eab79392ce69` |
| DA04-R01 | DA04-F0-W8-S02-R01 | 4185444934 | 1 | `3e9148fc380c8491` | `89ff937a73a01708` | `3f89eab79392ce69` |
| DA04-R02 | DA04-F0-W8-S02-R02 | 2627302015 | 2 | `3e9148fc380c8491` | `89ff937a73a01708` | `3f89eab79392ce69` |
| DA04-R03 | DA04-F0-W8-S02-R03 | 3592849939 | 3 | `3e9148fc380c8491` | `89ff937a73a01708` | `3f89eab79392ce69` |
| DA04-R04 | DA04-F0-W8-S02-R04 | 3815557835 | 4 | `3e9148fc380c8491` | `89ff937a73a01708` | `3f89eab79392ce69` |
| DA04-R05 | DA04-F0-W8-S02-R05 | 2016743094 | 5 | `3e9148fc380c8491` | `89ff937a73a01708` | `3f89eab79392ce69` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| DA04-R04 | yes | yes | yes | yes | yes | yes | yes | SDC | missing | COMPLETE_CAUSAL_CHAIN |
| DA04-R05 | yes | yes | yes | yes | yes | yes | yes | SDC | missing | COMPLETE_CAUSAL_CHAIN |
| DA04-R01 | yes | yes | missing | missing | missing | missing | missing | SQUASHED | missing | PARTIAL |
| DA04-R02 | yes | yes | yes | yes | missing | missing | yes | MASKED | missing | LIFECYCLE_ONLY |
| DA04-R03 | yes | yes | yes | yes | missing | missing | yes | MASKED | missing | LIFECYCLE_ONLY |
| DA04-R04 | yes | yes | yes | yes | yes | yes | yes | SDC | missing | PARTIAL |
| DA04-R05 | yes | yes | yes | yes | yes | yes | yes | SDC | missing | PARTIAL |

## 3. Per-pilot evidence

### DA04-R04 — COMPLETE_CAUSAL_CHAIN

- Injection seq **13832**, PC `0x400538`, tick 17040870, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/DA04-R04.
- Earliest anomaly: event 6216 `store_writeback`.
- Writeback: event 8267, phys r118 a0, value_fnv `a959f41d27dbce18`, payload_fnv `d9a56276a6025898`.
- Consumer: event 8273 PC `0x40055c` source_linked=True input_fnv `a959f41d27dbce18`, matches_source=1.
- Commit: event 6213 seq 6683.
- Terminal: `SDC` / `ORACLE_FAIL` (observed `SDC`).
- Oracle: expected `3f89eab79392ce69`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: DISABLED_LANE_REACHED_CONSUMER_AND_ORACLE_FAILED.

### DA04-R05 — COMPLETE_CAUSAL_CHAIN

- Injection seq **14582**, PC `0x400538`, tick 17156370, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6/DA04-R05.
- Earliest anomaly: event 6516 `store_writeback`.
- Writeback: event 8567, phys r111 a0, value_fnv `bdb2b3575183d5c`, payload_fnv `7cc505782442859c`.
- Consumer: event 8573 PC `0x40055c` source_linked=True input_fnv `bdb2b3575183d5c`, matches_source=1.
- Commit: event 6513 seq 7433.
- Terminal: `SDC` / `ORACLE_FAIL` (observed `SDC`).
- Oracle: expected `3f89eab79392ce69`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: DISABLED_LANE_REACHED_CONSUMER_AND_ORACLE_FAILED.

### DA04-R01 — PARTIAL

- Injection seq **320**, PC `0x41143c`, tick 606760, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04-R01.
- Earliest anomaly: event None `None`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `MASKED`).
- Oracle: expected `3f89eab79392ce69`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_EARLY_ANOMALY_EVENT, NO_INTERMEDIATE_PROPAGATION_EVENT, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: SQUASHED_NO_CONSUMER.

### DA04-R02 — LIFECYCLE_ONLY

- Injection seq **727**, PC `0x411454`, tick 877415, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04-R02.
- Earliest anomaly: event 487 `store_writeback`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 484 seq 282.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `3f89eab79392ce69`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_LANE_NEVER_READ.

### DA04-R03 — LIFECYCLE_ONLY

- Injection seq **3030**, PC `0x41126c`, tick 4957645, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04-R03.
- Earliest anomaly: event 1435 `store_writeback`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event 1434 seq 1324.
- Terminal: `MASKED` / `STORE_COMMITTED_LANE_NOT_READ` (observed `MASKED`).
- Oracle: expected `3f89eab79392ce69`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE.
- Classification rule: STORE_LANE_NEVER_READ.

### DA04-R04 — PARTIAL

- Injection seq **13832**, PC `0x400538`, tick 17040870, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04-R04.
- Earliest anomaly: event 6215 `store_writeback`.
- Writeback: event 8265, phys r118 a0, value_fnv `None`, payload_fnv `None`.
- Consumer: event 8271 PC `0x40055c` source_linked=True input_fnv `None`, matches_source=None.
- Commit: event 6212 seq 6683.
- Terminal: `SDC` / `ORACLE_FAIL` (observed `SDC`).
- Oracle: expected `3f89eab79392ce69`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: SDC_TERMINAL_WITHOUT_CHAIN_IN_THIS_VINTAGE.

### DA04-R05 — PARTIAL

- Injection seq **14582**, PC `0x400538`, tick 17156370, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04-R05.
- Earliest anomaly: event 6515 `store_writeback`.
- Writeback: event 8565, phys r111 a0, value_fnv `None`, payload_fnv `None`.
- Consumer: event 8571 PC `0x40055c` source_linked=True input_fnv `None`, matches_source=None.
- Commit: event 6512 seq 7433.
- Terminal: `SDC` / `ORACLE_FAIL` (observed `SDC`).
- Oracle: expected `3f89eab79392ce69`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: SDC_TERMINAL_WITHOUT_CHAIN_IN_THIS_VINTAGE.

## 3.1 Model-specific evidence quote

`size=4;old_be=0xf;new_be=0xe;store_data_hex=c114af81`; store_mem_write `be_mask=0xe;lane0_packet=0xc1;lane0_before=0xa5;lane0_after=0xa5`; later load response `a514af81`; writeback `81af14a5`.

## 4. Terminal and causality

v3.2.6 R04/R05 are complete causal chains. R04: be 0xF→0xE, store writes c114af81 with lane0 disabled; store_mem_write records lane0_before=a5/lane0_after=a5 (disabled_unchanged=1); a later load returns a514af81, writes back 81af14a5, and its consumer receives 0x81af14a5; the E2E evidence records 1009 consumers and oracle FAIL (SDC). R05 is the same pattern with 7714 consumers. The raw oracle.log/stdout for these two runs is absent from the v3.2.6 directory; the oracle FAIL is recorded in pilot_meta and DA04_v326_E2E_EVIDENCE.txt. v3.2.4 R01 is SQUASHED (PARTIAL); R02/R03 read no lane (LIFECYCLE_ONLY); v3.2.4 R04/R05 carry an SDC terminal but no chain in the older trace.

## 5. Missing evidence

ORACLE_RAW_FILE_MISSING for v3.2.6 R04/R05 (meta/E2E only); v3.2.4 R04/R05 chain absent (superseded by v3.2.6)

## 6. Verdict

- COMPLETE_CAUSAL_CHAIN: 2/7 pilots
- LIFECYCLE_ONLY: 2/7 pilots
- PARTIAL: 3/7 pilots

Model verdict: **PARTIAL** (see per-pilot split above).

## 7. Supplementary pilot recommendation

Recover or regenerate the raw oracle.log/stdout for the two v3.2.6 runs (2 runs, preserved identities) if a raw application-layer checksum is required. The microarchitectural chain is already complete.
