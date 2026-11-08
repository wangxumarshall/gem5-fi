# LSU v3.2.9 — final report

**Branch:** `lsu-platform-v3.2.9` (base `d5c15309`). **Final HEAD:** see
`GIT_COMMIT_v329.txt`. **Final binary:**
`303c610d2dcca81340f0feae58fc449c8550d1daac6ff965a3387efd2189a0c0`.
No 60-sample formal run; ConfigFrozen NO for all 60.

## SP05

- **Real source implementation?** Yes. `sp05_complete` mode; target selected
  in `commitStores` (Nth store earning `canWB`), premature `completeStore`
  in `writebackStores` before the cache send; entry-keyed one-shot, clamp,
  assert, watchdog, trace nodes `inj_sp05`/`sp05_complete`.
- **Five pilots?** Yes, all accepted: seq 18/19/23/24/28, one injection each,
  `_completed` 0→1, `storesToWB` −1, cache write skipped, trace
  COMPLETE/VALID, chain PASS, MASKED, oracle PASS.
- **Complete propagation chain?** No: store side is complete, but no later
  load reads the target in `store_path`. `PROPAGATION_VERIFIED=0`.
- **SDC?** No.

## SQ03

- **Original five pilots preserved?** Yes; no rerun or overwrite.
- **Did the probe observe data propagation?** It observed 136 SQ-forwarding
  decisions with identical `(load_seq, data_fnv, store_seq)` multisets in
  fault and control.
- **Did early writeback permission make data visible earlier?** No. `_canWB`
  at 140910; actual `store_mem_write` at 200970; the same-address loads are
  SQ-forwarded with unchanged data.
- **Application effect?** None: identical checksum `0x1053baee7edccdb1`.

## FW05

- **Independently reproducible workload?** Yes: `run_pilot.sh` works from a
  `/tmp` copy with `GEM5_ROOT`, runs `bin/fw05_forward`, golden
  `0x67afad307642983e`; archive SHA `0cf40509…` unchanged.
- **Strict matched baselines?** Yes: `fw05_older_src`/probability 0.0 on the
  final binary, all five golden; matched fault-on reproduces R01 PASS and
  R02–R05 SDC `549c9e0347adaf23/25/27/19`.
- **Evidence for the four SDCs?** Yes: original pilots retained, v3.2.8
  final-binary recheck, and v3.2.9 matched fault-on; Excel v3.2.4 and
  manifests agree.
- **Excel ↔ manifest consistent?** Yes:
  `tools/check_v329_consistency.py` → 60 rows, 0 errors.

## Verification

Build exit 0; SP05 rules PASS; five pilots + five controls; safety smokes;
consistency 0 errors. Full `pytest tests`: 39 passed, 2 failed (admission
guard refuses due to 22.9 GiB free < 70.6 GiB red line; environmental).
