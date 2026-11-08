# LSU v3.2.8 — FW05 config freeze + SQ03 safety/pilots

**Branch:** `lsu-platform-v3.2.8` (from `f26218f8`, v3.2.7 tip)
**Scope:** FW05 formal workload freeze + archive + no-fault baselines +
Excel v3.2.3; SQ03 one-shot/watchdog/timeout hardening + trace + five
pilots. No 60-sample formal run.

## A. FW05

- Definition remains `FW05-DEF-v1` (wrong-source selection, not a
  multi-store splice).
- `fw05_forward` is now the only formal workload. The exact v3.2.7 pilot
  binary is archived: SHA256
  `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf`.
  All five v3.2.7 manifests record the same hash; they are reused.
- Archive: `FW05_Workload_Archive/` (source, binary, build/run scripts,
  golden, inputs statement, compiler version, provenance, SHA256SUMS,
  README). Rebuild reproduces the exact binary SHA in this environment.
- Five no-fault baselines (same seeds, injection disabled): all exit 0,
  all `0x67afad307642983e`, oracle PASS.
- Excel v3.2.3 changes only the five FW05 rows: WorkloadPath
  `fw05_forward`, workload SHA, Oracle `67afad307642983e`, PilotStatus
  (`PILOT_RUN_ACCEPTED`; R01 SQUASHED, R02–R05 SDC). Identity columns and
  the other 11 models are cell-identical; `ConfigFrozen` remains NO for
  all 60.
- Historical W8 alignment configuration and the v3.2.7 pilots/traces are
  retained; the revision sheet records all five required reasons.

## B. SQ03

- `max_faults==0` was unlimited for SQ03; it is now clamped to 1, with an
  independent `sq03_fired` one-shot and an injection-count assert.
- In-simulator watchdog (`--sq03_watchdog_cycles`, default 500M ticks)
  logs `CHAOS_SQ03_WATCHDOG=EXPIRED` and calls `fatal` (exit 1).
- External `run_pilot.py --timeout` preserves partial logs/trace and
  classifies `TIMEOUT/HANG/INCOMPLETE`, never MASKED.
- Trace: `inj_sq03` → `store_wb` → `store_mem` → `sq03_complete`, plus
  commit; later loads would link through the store registry.
- Five pilots (W3 `sq_drain`, Excel seeds/ordinals): all accepted,
  MASKED, oracle PASS, exactly one injection, `canWB 0→1`,
  `storesToWB +1`, trace VALID/COMPLETE, chain PASS.
- Timing: R01 writes back 9,240 ticks earlier than no-fault, R05 385
  ticks earlier; R02–R04 at the baseline tick. No consumer reads the
  target store, so no SDC.
- `PROPAGATION_VERIFIED=0` because the store-side chain has no consumer.

## C. Verification and open issues

- Build exit 0; unit tests MD04/FW05/SQ03 PASS; platform 78 passed;
  workbook 4 passed; v3.2.8 consistency 4 passed.
- Open: no SQ03 consumer/SDC pilot; FW05 R02–R05 SDC is model-level, not
  a formal 60-sample result; global Warm-up/ROI still unresolved;
  60-sample formal run not started.
