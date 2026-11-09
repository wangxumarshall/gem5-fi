# A3 watchdog exit fix + runtime smoke (LSU v3.2.11, Task 5)

Date: 2026-11-10. Worktree: `.claude/worktrees/lsu-platform-v3.2.11`, branch
`lsu-platform-v3.2.11`. Baseline HEAD before this task: `83eaaf4c`.

## 1. Root cause

`CHAOSLQ04::watchdog()` (CHAOS/gem5/src/cpu/o3/CHAOSLQ04/CHAOSLQ04.cc:221)
exited with `exitSimLoop("lq04 watchdog expired", 1)`. The stdlib
`Simulator.run()` dispatches every exit event through
`ExitEvent.translate_exit_status()` (gem5/src/python/gem5/simulate/exit_event.py,
invoked from gem5/src/python/gem5/simulate/exit_handler.py:647), which raises

```
NotImplementedError: Exit event 'lq04 watchdog expired' not implemented
```

for any string outside its fixed table (exit_event.py:131). The registered
string for a simulation failure is `"m5_fail instruction encountered"`
(exit_event.py:91-92 -> `ExitEvent.FAIL`). The default FAIL handler is
`exit_generator()` (exit_handler.py:556-563), so `Simulator.run()` returns
normally instead of crashing the Python stack.

A second defect compounded the first: `configs/se/lsu_proxy.py` ended with a
bare `simulator.run()`, so even a FAIL exit carrying code 1 left the gem5
process exiting 0 — the watchdog could never produce a clear non-zero exit
status.

## 2. The supported exit mechanism (the fix)

1. `CHAOS/gem5/src/cpu/o3/CHAOSLQ04/CHAOSLQ04.cc` — the watchdog now calls
   `exitSimLoop("m5_fail instruction encountered", 1);` (registered FAIL
   event; the experimental reason stays in the CHAOS_LQ04_WATCHDOG_EXPIRED
   log/stdout line directly above, which is unchanged).
2. `configs/se/lsu_proxy.py` — after `simulator.run()`, the exit event code
   is read via `simulator.get_last_exit_event_code()` and propagated with
   `sys.exit(code)` when non-zero. Normal completions carry code 0 and keep
   exiting 0 (behavior unchanged).

## 3. Build

The build trees (`build/`, `CHAOS/gem5/build/`) were copied with `cp -a` from
the v3.2.10 worktree (identical C++ source under `CHAOS/gem5/src` per
`git diff lsu-platform-v3.2.10..HEAD -- CHAOS/gem5/src`, empty). Three build
findings, recorded for future rounds that copy build trees:

- The copied scons configure cache (`build/ARM/gem5.build/scons_config` +
  `sconsign.dblite`) does not survive the worktree move: the link-requiring
  conftest checks (`-Wl,--as-needed`, linker `-gz`, `CheckPythonLib`) miss the
  SConf decision cache and try to relink conftest executables whose
  intermediate `.o` files were cleaned as scons intermediates ->
  `ld: cannot find ... .o` -> `Error: Can't find a working Python installation`.
  Fix: `scons -j16 --config=force build/ARM/gem5.opt` (SConf clones the env
  for configure only; the main build decider is untouched). All fresh check
  outcomes matched the v3.2.10 build exactly (as-needed yes, Python 3.11.6,
  tcmalloc/protobuf yes, no capstone/png/hdf5).
- The forced configure invalidated the generated headers, so ~2583 targets
  recompiled (including `src/cpu/o3/CHAOSLQ04/CHAOSLQ04.cc`, cleanly, no new
  warnings; the only warning lines are the pre-existing
  "Unrecognized architecture for systemc" and missing-optional-lib notes that
  also appear in the v3.2.10 log).
- SCons then skipped the final link: the copied `sconsign.dblite` still
  vouched for the stale `gem5.opt` (its stored dep signature
  `db6adcd8...` for CHAOSLQ04.o vs the new `e8c2fbcf...` on disk). Removing
  the stale binary and re-running scons produced the clean final link.

Build output tail (`logs_v3_2_11/build_watchdog.log`, final run):

```
 [     CXX] src/base/date.cc -> ARM/base/date.o
scons: done building targets.
```
(with `[    LINK]  -> ARM/gem5.opt` at log line 1116; exit status 0)

Binary SHA256 (both copies identical, `logs_v3_2_11/binary_v3211_watchdog.sha256`):

```
3dccaa10ec5073ca90f2622bd37d5adac1b705bd9faf2497c2d13e46beadd4ed  CHAOS/gem5/build/ARM/gem5.opt
3dccaa10ec5073ca90f2622bd37d5adac1b705bd9faf2497c2d13e46beadd4ed  build/ARM/gem5.opt
```

(The stale copy this replaced was byte-identical to v3.2.10's
`f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694`; the old
file was moved to `/tmp/gem5_opt_stale_v3210_copy` during the relink.)

## 4. Regression (unaffected test)

```
build/ARM/gem5.opt --outdir=/tmp/lq04_reg_v3211 configs/se/arm_chaos.py \
  --cmd workloads/directed/reg_chain --cpu O3
```
Result: exit=0, no SIGSEGV, golden checksum printed (`logs_v3_2_11/regression_lq04_v3211.txt`):

```
f247ef3fe6f02cfd
```

## 5. Watchdog smoke

Disk checked first (`df -h /home`: 78G free > 70.6 GiB). Command:

```
build/ARM/gem5.opt --outdir=/tmp/lq04_watchdog_smoke configs/se/lsu_proxy.py \
  --cpu O3 --variant B0 --chaos_propagation --prop_trace_file prop_trace.csv.gz \
  --chaos_lq04 --lq04_event_ordinal 999 --lq04_max_faults 1 \
  --lq04_watchdog_cycles 20000 \
  --cmd=$PWD/docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal
```

- Exit code: `1`. Before the fix this run instead died mid-run with an
  unhandled `NotImplementedError` traceback; with only the C++ fix it would
  have exited the FAIL event cleanly but with process status 0 — the config
  change is what propagates the event's code 1 to the process exit status.
- stdout tail (`watchdog_smoke/stdout.log`):

```
[lsu_proxy] B0 caches applied (variant=B0): L1D 32KiB/2-way lat222 MSHR6/t8/wb16 + L1I 32KiB/2 lat111 MSHR2 + L2 1MiB/16 lat12 MSHR16 + StridePrefetcher(8,1,on)@L2
CHAOS_LQ04_WATCHDOG_EXPIRED: selected=0 injected=0 eligible=821 ordinal=999 tick=7700000
```

- stderr (`watchdog_smoke/stderr.log`): 8 lines, all standard gem5 warnings
  (dot file, DRAM capacity, se_workload OS, legacy stats, bucket sizes, gdb
  sockets). **No `NotImplementedError`.**
- Trace census (`watchdog_smoke/trace_census.txt`): `prop_trace.csv.gz`
  exists (284931 bytes), `gzip -t` OK — the exit callbacks closed the gzip
  stream cleanly; 10012 lines = 1 header + 10011 events; first event tick
  78540, last valid event retained at tick 7699615 (immediately before the
  watchdog at tick 7700000):

```
10010,7699615,0,lq_lifecycle,31674,,,816,,queue=LQ;action=free;index=816;generation=826;reason=commit
```

## 6. Classification check (`watchdog_smoke/classify_check.{py,txt}`)

The harness replays the exact `run_pilot.py` watchdog branch
(`CHAOS_LQ04_WATCHDOG_EXPIRED` in stdout/stderr, before the generic
non-zero-returncode CRASH branch) on the real smoke outputs, converts the
real trace through the platform pipeline (`tools.prop_trace_to_v31.convert`),
and calls `terminal_rules.adjudicate` exactly as run_pilot.py:885-889 does:

```
gem5 exit code            : 1
NotImplementedError seen  : False
watchdog_hit              : True
injected (lq04 log)       : 0
run_status/activation     : SIMULATOR_ERROR/NOT_TRIGGERED
terminal/completeness     : HANG/INCOMPLETE
rows=10011 truncated=False
final_terminal            : HANG          (terminal_rules.adjudicate, observed_terminal=HANG)
terminal_reason           : None
MASKED in verdict         : False
adversarial probe (oracle_pass=True): final_terminal=HANG, MASKED in verdict: False
CLASSIFICATION_CHECK: PASS
```

`HANG` is in `terminal_rules.HARD_TERMINALS`, so `adjudicate` returns it
before any MASKED/SDC path can be reached — a watchdog run can never be
adjudicated MASKED, even if an oracle had passed. The converted trace closes
with `terminal=HANG`, `completeness=INCOMPLETE`, `truncated=False` (clean
gzip EOF, last valid event retained).

## 7. Verdict

A3 fixed and runtime-verified: the watchdog now exits through gem5's
registered FAIL event, the gem5 process fails with exit code 1 and the
CHAOS_LQ04_WATCHDOG_EXPIRED reason line, the propagation trace is retained
intact, and the platform adjudication of such a run is HANG/INCOMPLETE —
never MASKED.
