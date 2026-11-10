# A01 Propagation Audit — v3.2.11

**Model:** A01  **SubUnit:** AGU  **Audit date:** 2026-11-10  
**Tool:** `tools/lsu_propagation_audit.py` + raw `trace_v31.jsonl` re-inspection  
**Expected path:** EA^0x8 at pushRequest PRE → address_formed → memory_request → memory_response → register_writeback → consumer → commit; crash only if the fault address is causal

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 | WorkloadSHA256 | Oracle expected |
|---|---|---|---|---|---|---|
| A01-R01 | PILOT-A01-R01 | 2108120075 | 1 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A01-R02 | PILOT-A01-R02 | 1113826800 | 2 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A01-R03 | PILOT-A01-R03 | 1302709433 | 3 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A01-R04 | PILOT-A01-R04 | 2194451614 | 4 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A01-R05 | PILOT-A01-R05 | 3228552887 | 5 | `275111d805a71bc3` | `90a1900377d24996` | `728e604ffcec539d` |
| A01-R01 | PILOT-A01-R01 | 2108120075 | 1 | `0fa610c21b6a3c40` | `90a1900377d24996` | `728e604ffcec539d` |
| A01-R03 | PILOT-A01-R03 | 1302709433 | 3 | `0fa610c21b6a3c40` | `90a1900377d24996` | `728e604ffcec539d` |

## 2. Seven-stage table

| Pilot | Injection | Activation | Early anomaly | Intermediate | Writeback | Consumer | Commit | Terminal | Oracle | Final classification |
|---|---|---|---|---|---|---|---|---|---|---|
| A01-R01 | yes | yes | yes | yes | yes | yes | yes | CRASH | missing | PARTIAL |
| A01-R02 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | PARTIAL |
| A01-R03 | yes | yes | yes | yes | missing | missing | missing | SQUASHED | missing | PARTIAL |
| A01-R04 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | PARTIAL |
| A01-R05 | yes | yes | yes | yes | yes | yes | yes | MASKED | missing | PARTIAL |
| A01-R01 | yes | yes | yes | yes | yes | yes | yes | CRASH | missing | PARTIAL |
| A01-R03 | yes | yes | yes | yes | missing | missing | missing | SQUASHED | yes | PARTIAL |

## 3. Per-pilot evidence

### A01-R01 — PARTIAL

- Injection seq **5**, PC `0x400790`, tick 80080, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A01-R01.
- Earliest anomaly: event 3 `address_formed`.
- Writeback: event 6, phys r45 a1, value_fnv `None`, payload_fnv `None`.
- Consumer: event 8 PC `0x400a9c` source_linked=False input_fnv `None`, matches_source=None.
- Commit: event 7 seq 5.
- Terminal: `CRASH` / `None` (observed `CRASH`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=False.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: WRONG_EA_PROPAGATED_NO_REFERENCE_VALUE_OR_CRASH_MISMATCH.

### A01-R02 — PARTIAL

- Injection seq **48**, PC `0x400ad0`, tick 197890, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A01-R02.
- Earliest anomaly: event 3 `address_formed`.
- Writeback: event 6, phys r68 a3, value_fnv `None`, payload_fnv `None`.
- Consumer: event 8 PC `0x400ad4` source_linked=False input_fnv `None`, matches_source=None.
- Commit: event 7 seq 44.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: WRONG_EA_PROPAGATED_NO_REFERENCE_VALUE_OR_CRASH_MISMATCH.

### A01-R03 — PARTIAL

- Injection seq **169**, PC `0x40c0f0`, tick 470085, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A01-R03.
- Earliest anomaly: event 3 `address_formed`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `MASKED`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING, NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: WRONG_EA_AND_RESPONSE_NO_WRITEBACK.

### A01-R04 — PARTIAL

- Injection seq **272**, PC `0x40c0f0`, tick 494340, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A01-R04.
- Earliest anomaly: event 3 `address_formed`.
- Writeback: event 6, phys r2 a1, value_fnv `None`, payload_fnv `None`.
- Consumer: event 8 PC `0x40c104` source_linked=False input_fnv `None`, matches_source=None.
- Commit: event 7 seq 130.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: WRONG_EA_PROPAGATED_NO_REFERENCE_VALUE_OR_CRASH_MISMATCH.

### A01-R05 — PARTIAL

- Injection seq **280**, PC `0x40c110`, tick 495880, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1/A01-R05.
- Earliest anomaly: event 3 `address_formed`.
- Writeback: event 6, phys r48 a0, value_fnv `None`, payload_fnv `None`.
- Consumer: event 8 PC `0x40c114` source_linked=False input_fnv `None`, matches_source=None.
- Commit: event 7 seq 138.
- Terminal: `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT` (observed `MASKED`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=True.
- Missing: ORACLE_FILE_MISSING.
- Classification rule: WRONG_EA_PROPAGATED_NO_REFERENCE_VALUE_OR_CRASH_MISMATCH.

### A01-R01 — PARTIAL

- Injection seq **5**, PC `0x400790`, tick 80080, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_2/A01-R01.
- Earliest anomaly: event 4 `address_formed`.
- Writeback: event 18, phys r45 a1, value_fnv `None`, payload_fnv `None`.
- Consumer: event 21 PC `0x400a9c` source_linked=False input_fnv `None`, matches_source=None.
- Commit: event 19 seq 5.
- Terminal: `CRASH` / `None` (observed `CRASH`).
- Oracle: expected `728e604ffcec539d`, actual `None`, pass=False.
- Missing: ORACLE_MALFORMED.
- Classification rule: WRONG_EA_PROPAGATED_NO_REFERENCE_VALUE_OR_CRASH_MISMATCH.

### A01-R03 — PARTIAL

- Injection seq **169**, PC `0x40c0f0`, tick 470085, detail epoch docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_2/A01-R03.
- Earliest anomaly: event 95 `address_formed`.
- Writeback: event None, phys rNone aNone, value_fnv `None`, payload_fnv `None`.
- Consumer: event None PC `0xNone` source_linked=None input_fnv `None`, matches_source=None.
- Commit: event None seq None.
- Terminal: `SQUASHED` / `TARGET_SQUASHED_NO_COMMIT` (observed `UNRESOLVED`).
- Oracle: expected `728e604ffcec539d`, actual `728e604ffcec539d`, pass=True.
- Missing: NO_REGISTER_WRITEBACK_EVENT, NO_CONSUMER_EDGE, NO_COMMIT_EVENT.
- Classification rule: WRONG_EA_AND_RESPONSE_NO_WRITEBACK.

## 3.1 Model-specific evidence quote

`old_addr=7ffffefda0;new_addr=7ffffefda8` (v3.2.2 R01); stderr `Page table fault when accessing virtual address 0` (injected EA 0x7ffffefda8 — no match).

## 4. Terminal and causality

The EA transform and its downstream request/response/writeback/consumer are present. The audit cannot prove the delivered value is wrong: the trace records no reference value for the correct EA. The two crash runs do not establish fault causality — A01 v3.2.2 R01 panicked on VA 0 while the injected EA was 0x7ffffefda8, and the v3.2.1 stderr contains no page-table-fault address. v3.2.1 has no oracle.log.

## 5. Missing evidence

NO_REFERENCE_VALUE_AT_CORRECT_EA; CRASH_ADDRESS_MISMATCH; ORACLE_FILE_MISSING (v3.2.1); truncated v3.2.1 traces lack commit/consumer in R03

## 6. Verdict

- PARTIAL: 7/7 pilots

Model verdict: **PARTIAL** (see per-pilot split above).

## 7. Supplementary pilot recommendation

Optional: add the correct-EA reference data hash and the page-table-fault address to the A01 trace, then 1-2 supplementary pilots. Not needed for the current verdict; awaiting approval.
