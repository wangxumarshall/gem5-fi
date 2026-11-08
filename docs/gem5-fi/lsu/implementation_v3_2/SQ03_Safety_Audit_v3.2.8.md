# SQ03 safety audit and hardening (v3.2.8)

## 1. `max_faults` semantics (source-verified)

`CHAOSLSQFwd` treats `max_faults == 0` as **unlimited** in the general
injection paths (`if (max_faults != 0 && faults_injected_count >= max_faults)
return ...`). DA04 and FW02 clamp it to 1 in their constructor branches;
SQ03 did not before this round, so `max_faults=0` in `sq03_canwb` set
`_canWB` for every store and could hang.

## 2. Hardening implemented

- **Hard cap**: `chaos_sq03::shouldSetCanWB` clamps `max_faults==0` to 1;
  the constructor also sets `max_faults=1` for `Sq03CanWB`.
- **Independent one-shot**: `CHAOSLSQFwd::sq03_fired` is checked before any
  eligibility logic and set on the injection, so a duplicate call cannot
  apply a second premature `canWB`.
- **Assertion**: `assert(faults_injected_count == 1 && "SQ03 must inject
  exactly once")` after the increment.
- **In-simulator watchdog**: an `EventFunctionWrapper` scheduled at
  `sq03WatchdogCycles` (default 500,000,000 ticks; config
  `--sq03_watchdog_cycles`) logs
  `CHAOS_SQ03_WATCHDOG=EXPIRED fired=... injected=... eligible=... tick=...`
  and calls `fatal(...)`, so the process exits non-zero and is not a normal
  MAX_TICK exit.
- **External timeout**: `run_pilot.py` will catch `TimeoutExpired`, preserve
  partial stdout/stderr/trace and classify `TIMEOUT` (never MASKED). This is
  implemented in the next task.

## 3. Evidence

- `tests/test_sq03_rules.cc`: PASS, including `max_faults==0` clamp.
- `max_faults=0` smoke: exit 0, checksum equals no-fault baseline
  `0xba3b3185e541ad03`, exactly one injection
  (`fired=1 injected=1 eligible=1`).
- `max_faults=1` smoke: same single injection.
- Watchdog smoke (`--sq03_watchdog_cycles 1000`): exit **1**,
  `fatal: CHAOS_SQ03_WATCHDOG_EXPIRED tick=385000 injected=1 eligible=1`,
  injector log keeps the `EXPIRED` line and the injection line.

Logs: `evidence_v3_2_8/SQ03_safety/`.

## 4. Residual risk

- The watchdog is a wall-clock-independent simulation-tick watchdog. A
  pathological event-queue livelock that still advances ticks will trip it;
  a host-level stall is covered by the external timeout in Task 6.
- `fatal()` intentionally aborts; partial JSONL is flushed per event by the
  tracer and the runner must keep it.
