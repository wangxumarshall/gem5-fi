# SQ03 implementation and five pilots (v3.2.8)

## Definition

`SQ03_Definition_Freeze_v3.2.7.md`: **Premature Store Writeback
Permission**. Hook: `LSQUnit::executeStore`, after `assert(store_fault ==
NoFault)`. For one selected real store, `SQEntry::_canWB` is set early and
`storesToWB` is incremented in the same step. No address/size/data change.

## Safety changes

- `max_faults==0` is clamped to 1 (`chaos_sq03::shouldSetCanWB` and ctor).
- Independent `sq03_fired` one-shot flag + `assert(injected == 1)`.
- In-simulator watchdog (`--sq03_watchdog_cycles`, default 500M ticks):
  logs `CHAOS_SQ03_WATCHDOG=EXPIRED` and calls `fatal`, exit 1.
- External wall-clock timeout (`run_pilot.py --timeout`), preserving partial
  logs/trace and classifying `TIMEOUT/HANG/INCOMPLETE` (never MASKED).
- See `SQ03_Safety_Audit_v3.2.8.md`.

## Trace

`inj_sq03` (store seq/PC/addr/size, SQ idx/gen, canWB before/after,
storesToWB before/after, tick, ordinal, seed) → `store_wb` (existing
store-chain node) → `store_mem` (BaseCache) → `sq03_complete`;
commit/squash and any later load response/consumer are linked by the real
dynamic identity through `fault_store_registry`.

## Five pilots (Excel seeds, ordinals 1..5, W3 `sq_drain`)

| Pilot | seed | ordinal | store seq | addr | canWB | storesToWB | inject | fault WB | baseline WB | terminal | oracle |
|---|---:|---:|---:|---|---|---|---:|---:|---:|---|---|
| R01 | 2214819981 | 1 | 18 | 0x7ffffefd10 | 0→1 | 0→1 | 140910 | 140910 | 150150 | MASKED | PASS |
| R02 | 1486471869 | 2 | 19 | 0x7ffffefd18 | 0→1 | 0→1 | 141295 | 150150 | 150150 | MASKED | PASS |
| R03 | 3102670938 | 3 | 23 | 0x7ffffefd20 | 0→1 | 0→1 | 141680 | 150150 | 150150 | MASKED | PASS |
| R04 | 3974203372 | 4 | 24 | 0x7ffffefd28 | 0→1 | 0→1 | 142065 | 150150 | 150150 | MASKED | PASS |
| R05 | 729970077 | 5 | 28 | 0x7ffffefd30 | 0→1 | 0→1 | 142450 | 150150 | 150535 | MASKED | PASS |

All five: exactly one injection, canWB 0→1, storesToWB delta +1, no HANG,
trace VALID/COMPLETE, chain PASS, accepted, oracle PASS. R01's store
writes back 9,240 ticks earlier than baseline; R05 385 ticks earlier;
R02–R04 exactly at the baseline writeback tick (the early permission did
not advance their actual drain). **No SDC**: the application checksum is
unchanged and no later load/consumer reads the target store, so the
store-side chain stops at writeback/completion (consumer 0). Time shift
alone is not called SDC.

## Non-claims

- No consumer/SDC pilot for SQ03.
- No 60-sample formal run.
- The release workload (W3 `sq_drain`) is the Excel workload; no override.
