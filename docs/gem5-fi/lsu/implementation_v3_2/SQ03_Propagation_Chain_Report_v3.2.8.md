# SQ03 propagation-chain verification (v3.2.8)

Evidence: `pilots_v3_2_8/SQ03-R01..R05/pilot_meta.json`,
`trace_v31.jsonl`, `lsq_fwd_injections.log`, `oracle.log`;
`evidence_v3_2_8/SQ03_v328_EVIDENCE.csv`; baselines in
`evidence_v3_2_8/SQ03_baselines/`.

Definition: **Premature Store Writeback Permission** — one real store has
`SQEntry::_canWB` set early in `LSQUnit::executeStore`, with `storesToWB`
incremented in the same step. Address/size/data are unchanged.

## Per-pilot identity and injection

| Pilot | SampleRunID | seed | ordinal | store seq | store PC | store addr | size | SQ entry | gen | canWB | storesToWB | inject tick |
|---|---|---|---:|---:|---|---|---:|---:|---:|---|---|---:|
| R01 | SQ03-F0-W3-S02-R01 | 2214819981 | 1 | 18 | 0x4008d0 | 0x7ffffefd10 | 8 | 1 | 1 | 0→1 | 0→1 | 140910 |
| R02 | SQ03-F0-W3-S02-R02 | 1486471869 | 2 | 19 | 0x4008d0 | 0x7ffffefd18 | 8 | 2 | 2 | 0→1 | 0→1 | 141295 |
| R03 | SQ03-F0-W3-S02-R03 | 3102670938 | 3 | 23 | 0x4008d8 | 0x7ffffefd20 | 8 | 3 | 3 | 0→1 | 0→1 | 141680 |
| R04 | SQ03-F0-W3-S02-R04 | 3974203372 | 4 | 24 | 0x4008d8 | 0x7ffffefd28 | 8 | 4 | 4 | 0→1 | 0→1 | 142065 |
| R05 | SQ03-F0-W3-S02-R05 | 729970077 | 5 | 28 | 0x4008e4 | 0x7ffffefd30 | 8 | 5 | 5 | 0→1 | 0→1 | 142450 |

Every pilot: `fired=1 injected=1`, `injection_count=1`, no duplicate
one-shot application, address/size/data unchanged
(`all_address_size_unchanged=true`), `storesToWB` delta +1 and no
underflow/`_completed` inconsistency reported.

## Store-side chain (all five)

Real trace stages, linked by dynamic seq / SQ entry / generation:

```text
Target Store execution (executeStore)      -> injection record (inj_sq03 equivalent: "injection")
        ↓
Writeback Permission granted early         -> canWB 0→1, storesToWB 0→1
        ↓
Store Writeback                            -> store_writeback records
        ↓
Store Memory Write                         -> store_mem_write
        ↓
Store Completion                           -> sq03_complete
```

Per-pilot trace verdict (from `pilot_meta.json`):
`record_integrity=VALID`, `trace_completeness=COMPLETE`,
`propagation_coverage=COMPLETE`, `chain_integrity=PASS`,
`missing_stages=[]`, `execution_attempt_link=SAME_ATTEMPT`,
`injections=1`, `activations=5`, `edges=4`, `events=198060`.

## Timing vs no-fault baseline

| Pilot | fault writeback tick | baseline writeback tick | delta (ticks) |
|---|---:|---:|---:|
| R01 | 140910 | 150150 | −9240 |
| R02 | 150150 | 150150 | 0 |
| R03 | 150150 | 150150 | 0 |
| R04 | 150150 | 150150 | 0 |
| R05 | 150150 | 150535 | −385 |

R01 gets its `_canWB` 9,240 ticks earlier and actually drains earlier; R05
shifts by 385 ticks; R02–R04 obtain permission early but their actual drain
timing is unchanged.

## Consumer / application outcome

`consumer_instructions=0`, `consumer_operand_records=0`,
`taint_value_mismatch_records=0` for all five. No later load reads the target
store, so there is no register-writeback or consumer-commit stage, and the
application checksum is the golden `0xba3b3185e541ad03` in all five
(`ORACLE_PASS`). Terminal state: MASKED
(`STORE_COMMITTED_LANE_NOT_READ`). **Time shift is not counted as SDC.**

## Failure / HANG / TIMEOUT record

None of the five pilots hung or timed out: all `exit_code=0`,
`run_status=COMPLETED`, watchdog not tripped. The watchdog path is separately
demonstrated by an intentional smoke (`--sq03_watchdog_cycles 1000`) that
logs `CHAOS_SQ03_WATCHDOG=EXPIRED tick=385000 injected=1 eligible=1` and exits
1; see `evidence_v3_2_8/SQ03_safety/watchdog_*`.
