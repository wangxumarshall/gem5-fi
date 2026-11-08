# SP05 definition freeze and first step (v3.2.8)

## Identity

- Model: SP05 (SQ completion state error)
- FaultConfigID: SP05-CFG01
- Unit: SQ
- Target: `SQEntry::_completed` / paired `storesToWB`
- Hook point: `LSQUnit::completeStore` (`lsq_unit.cc`, `_completed = true;
  --storesToWB`)
- Source anchors: `lsq_unit.hh:159,187-188`; audit v3.2.3 SP05 row

## Mechanism

Normally a store is marked completed and removed from `storesToWB` only in
`completeStore`, after writeback/commit ordering. SP05 marks one selected
live store complete early (entry-keyed by SQ index + generation) and keeps
the `storesToWB` decrement paired, so the accounting does not underflow.

## Safety constraints (from the v3.2.3 audit)

- Entry-keyed one-shot, not a "next completeStore call" flag (instant-
  complete paths defeat that flag).
- `max_faults==0` is clamped to one completion.
- A watchdog is required; a drain assert/HANG must be classified HANG, not
  SimulatorError.
- No address/size/data change; no request destruction.

## Implemented this round

- `chaos_sp05::shouldComplete(sq_idx, sq_gen, target_idx, target_gen,
  injected, max_faults)` with the clamp.
- `tests/test_sp05_rules.cc`: PASS.

## Not yet done

- Live hook in `completeStore`, config mode, trace nodes, watchdog wiring,
  five pilots, terminal/oracle adjudication. SP05 is SOURCE_AUDITED only;
  it is not marked implemented from the rules/test alone.
