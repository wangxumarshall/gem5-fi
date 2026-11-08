# LSU v3.2.9 — SP05 implementation, SQ03 probe, FW05 closure

**Branch:** `lsu-platform-v3.2.9` (from `d5c15309`, v3.2.8 tip)
**Final binary:** `d6e60863bb63f85398b5aaa35539c0c6c3fdf582e3d969aace27611d5db97b90`
No 60-sample formal run. `ConfigFrozen=NO` for all 60.

## A. SP05

- Real hook: target selection in `commitStores`, premature `completeStore`
  in `writebackStores` before the cache send; entry-keyed one-shot, clamp
  `max_faults 0→1`, `assert(injected==1)`, watchdog, external timeout.
- Five pilots (Excel seeds/ordinals, `store_path`): one injection each,
  seq 18/19/23/24/28, `_completed` false→true, `storesToWB` −1, cache write
  skipped, trace COMPLETE/VALID, chain PASS, terminal MASKED, oracle PASS,
  consumer 0. Matched controls identical golden.
- `PROPAGATION_VERIFIED=0` (no consumer in this workload).

## B. SQ03

- Original five pilots/traces unchanged. Analysis separates `_canWB`
  (140910) from the actual `store_mem_write` (198275; 203665 for R02–R05).
- New independent probe P00/P01 (seed 3141592653): identical checksums and
  136 identical SQ-forwarding decisions; early permission does not make data
  visible earlier; no consumer, no SDC. `PROPAGATION_VERIFIED=0`.

## C. FW05

- `run_pilot.sh` locates the repo via GEM5_ROOT/git and runs the archived
  `bin/fw05_forward`; tested from `/tmp` (exit 0, golden). Archived SHA
  `0cf40509…` unchanged.
- Strict matched baselines (`fw05_older_src`, probability 0.0) on the final
  binary: all five golden; matched fault-on reproduces R01 PASS and R02–R05
  SDC `549c9e0347adaf23/25/27/19`.
- Excel v3.2.4: FW05 WorkloadPath points at the archive binary; SQ03/SP05
  status are `PILOT_RUN_ACCEPTED`; identities unchanged; revision sheet 17.

## D. Verification

- Build exit 0 (logs `build_sp05*.log`).
- SP05 unit rules PASS; five pilots accepted; safety smokes (clamp,
  non-target, control, watchdog) pass.
- Full `pytest tests`: **39 passed, 2 failed**. The five former fixture
  errors are gone after installing pytest-check 2.4.0 and supplying the
  expected `check(name,condition,message)` fixture. The two failures are
  `test_claim_concurrency` d/e: the admission guard refuses to run because
  disk free 22.9 GiB < red line 70.6 GiB — environmental, not code.
- Consistency: `tools/check_v329_consistency.py` → 60 rows, 0 errors.
