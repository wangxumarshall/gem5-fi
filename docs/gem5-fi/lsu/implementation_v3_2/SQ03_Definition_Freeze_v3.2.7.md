# SQ03 definition freeze and first hook (v3.2.7)

## Identity

- Model: SQ03 (SQ state error — premature writeback permission)
- FaultConfigID: SQ03-CFG01, option A (researcher-recommended)
- Unit: SQ (store queue)
- Target: `SQEntry::_canWB`
- Hook: `LSQUnit::executeStore`, after `assert(store_fault == NoFault)`
- Source anchors: `lsq_unit.hh:155,185-186,484`; `lsq_unit.cc` executeStore
  (audit v3.2.3 lines 731-791; renumbered in this tree)

## Mechanism

Normally a plain store's `_canWB` is set in `commitStores`; `writebackStores`
uses it and `completeStore` pops the entry. SQ03 sets `_canWB` early for one
selected real store at `executeStore` and increments `storesToWB` in the same
step, keeping the writeback/complete accounting balanced. No address, size,
store data or request is changed. Store-conditional and atomic stores have
their own `canWB` path and are excluded.

## Selection and safety

- One injection per sample (`max_faults=1`); the eligible ordinal is the
  `--lsqfwd_event_ordinal` value (1-based). `max_faults=0` is **unsafe** for
  this mode (it sets canWB for every store and the workload can hang); the
  run must bound it.
- A watchdog is still required for the formal pilot; a hang must be
  classified HANG, not SimulatorError.

## Implemented in this round

- `chaos_sq03::shouldSetCanWB` rules header + `tests/test_sq03_rules.cc`
  (PASS).
- `CHAOSLSQFwd::maybeSetCanWB` and the `sq03_canwb` struct mode.
- `LSQUnit::executeStore` hook: `canWB=true; ++storesToWB` once.
- Smoke: `sq_drain`, `--lsq_struct_mode sq03_canwb --max_faults 1
  --lsqfwd_event_ordinal 1` exits 0, injects once at store seq 18
  (`lsq_fwd_injections.log`), checksum equals the no-fault baseline
  `0xba3b3185e541ad03` (MASKED at this event).

## Not yet done

- Trace event (`inj_sq03`) and propagation edges.
- run_pilot / manifest / matrix PILOT_RUN wiring.
- The five SQ03 pilots, terminal/oracle adjudication and watchdog.
- A bounded-selection mechanism that makes `max_faults=0` safe.
