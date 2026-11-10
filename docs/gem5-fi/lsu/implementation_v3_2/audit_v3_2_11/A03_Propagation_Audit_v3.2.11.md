# A03 Propagation Audit — v3.2.11

**Model:** A03  **SubUnit:** AGU  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** F5 per-event EA bit3 clear → address_formed → memory_request → memory_response → register_writeback → consumer → commit, or an address-matched crash

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| A03-R01 | PILOT-A03-R01 | 663646247 | 1 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A03-R02 | PILOT-A03-R02 | 1626885462 | 2 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A03-R03 | PILOT-A03-R03 | 110775855 | 3 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A03-R04 | PILOT-A03-R04 | 2766846323 | 4 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A03-R05 | PILOT-A03-R05 | 1156093484 | 5 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A03-R01 | PILOT-A03-R01 | 663646247 | 1 | `0fa610c21b6a3c40` | `90a1900377d24996` | `728e604ffcec539d` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| A03-R01 | yes | yes | yes | yes | missing | missing | missing | CRASH | missing | PARTIAL |
| A03-R02 | yes | yes | yes | yes | missing | missing | missing | CRASH | missing | PARTIAL |
| A03-R03 | yes | yes | yes | yes | missing | missing | missing | CRASH | missing | PARTIAL |
| A03-R04 | yes | yes | yes | yes | missing | missing | missing | CRASH | missing | PARTIAL |
| A03-R05 | yes | yes | yes | yes | missing | missing | missing | CRASH | missing | PARTIAL |
| A03-R01 | yes | yes | yes | yes | missing | missing | missing | CRASH | missing | PARTIAL |

## 3. Per-pilot evidence

### A03-R01 — PARTIAL

- Injection seq **1146**, PC `0xNone`, tick 1633555, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A03-R01.
- Earliest anomaly: event 590 `address_formed`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `CRASH` / `None` (observed `CRASH`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: WRONG_EA_AND_RESPONSE_NO_WRITEBACK.

### A03-R02 — PARTIAL

- Injection seq **1146**, PC `0xNone`, tick 1633555, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A03-R02.
- Earliest anomaly: event 589 `address_formed`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `CRASH` / `None` (observed `CRASH`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: WRONG_EA_AND_RESPONSE_NO_WRITEBACK.

### A03-R03 — PARTIAL

- Injection seq **1146**, PC `0xNone`, tick 1633555, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A03-R03.
- Earliest anomaly: event 582 `address_formed`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `CRASH` / `None` (observed `CRASH`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: WRONG_EA_AND_RESPONSE_NO_WRITEBACK.

### A03-R04 — PARTIAL

- Injection seq **1146**, PC `0xNone`, tick 1633555, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A03-R04.
- Earliest anomaly: event 581 `address_formed`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `CRASH` / `None` (observed `CRASH`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: WRONG_EA_AND_RESPONSE_NO_WRITEBACK.

### A03-R05 — PARTIAL

- Injection seq **1146**, PC `0xNone`, tick 1633555, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A03-R05.
- Earliest anomaly: event 580 `address_formed`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `CRASH` / `None` (observed `CRASH`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: WRONG_EA_AND_RESPONSE_NO_WRITEBACK.

### A03-R01 — PARTIAL

- Injection seq **1146**, PC `0xNone`, tick 1633555, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_2/A03-R01.
- Earliest anomaly: event 1327 `address_formed`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `CRASH` / `None` (observed `CRASH`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=False.
- Missing: ORACLE_MALFORMED, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: WRONG_EA_AND_RESPONSE_NO_WRITEBACK.

## 3.1 Model-specific evidence quote

`old_addr=7ffffefdb8;new_addr=7ffffefdb0`; stderr `Page table fault when accessing virtual address 0xffffffffffb73c50` (injected EA 0x7ffffefdb0 — no match).

## 4. Terminal and causality

F5 is per-event (not a latch): the traces show repeated corrupted EAs. The response is present, but most traces stop before writeback/consumer, and every crash is address-mismatched (v3.2.2 R01 panicked at 0xffffffffffb73c50 while the injected EA was 0x7ffffefdb0; v3.2.1 stderr has no fault address). ObservedTerminal=CRASH, FaultCausality=NOT_ATTRIBUTED.

## 5. Missing evidence

NO_REGISTER_WRITEBACK_EVENT/NO_CONSUMER_EDGE in 5/6 pilots; CRASH_ADDRESS_MISMATCH; ORACLE_FILE_MISSING (v3.2.1)

## 6. Verdict

- PARTIAL: 6/6 pilots

Model verdict: **PARTIAL** (see per-pilot split above).

## 7. Supplementary pilot recommendation

Optional: instrument the F5 eligible stream and address-match the crash; 1-2 supplementary pilots after approval.
