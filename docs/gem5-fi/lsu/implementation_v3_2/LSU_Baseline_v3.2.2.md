# LSU v3.2.2 — Final W1–W8 Fault-Free Baseline

**Binary:** `build/ARM/gem5.opt`
**SHA256:** `7a584a08d55df148eebe090530f56a14679b38567c936f6ed9723aa59dff278d`
**Source:** branch `lsu-platform-v3.2.2`, HEAD `398f585ce0426ce381200ef5ca9a8ca7e73a6c80`
**Runner:** `baselines/run_baselines_v322.sh`
**Results root:** `baselines_v3_2_2/` (the v3.2.1 `baselines/` tree is untouched)

The binary was rebuilt from the final commit's C++ tree (scons product copied to
the repo-root path used by the platform; the two SHA256 values are identical,
recorded in `GIT_COMMIT_v322.txt`).

## Results (8/8)

| W | Workload | Exit | Oracle | finalTick | Loads committed | Stores committed | Forwards | Rescheduled |
|---|---|---|---:|---:|---:|---:|---:|---:|
| W1 | agu_addrmodes | 0 | PASS | 19,544,525 | 1,066 | 1,221 | 6 | 1 |
| W2 | lq_lifetime | 0 | PASS | 37,983,715 | 5,476 | 5,485 | 11 | 6 |
| W3 | sq_drain | 0 | PASS | 149,995,615 | 66,721 | 31,092 | 10 | 6 |
| W4 | sq_forward | 0 | PASS | 19,112,940 | 898 | 1,205 | 6 | 1 |
| W5 | load_response | 0 | PASS | 55,153,560 | 17,829 | 3,429 | 11 | 5 |
| W6 | store_path | 0 | PASS | 92,581,720 | 34,985 | 10,609 | 11 | 6 |
| W7 | replay_dependency | 0 | PASS | 40,653,690 | 9,641 | 2,660 | 267 | 5 |
| W8 | alignment | 0 | PASS | 34,556,445 | 6,305 | 3,048 | 11 | 5 |

**Target microarchitecture events confirmed:** every workload commits real loads
and stores; W4/W7 exercise store-to-load forwarding (W7 has 267 forwards, the
highest); W7 has 5 rescheduled loads, matching the 5 replays observed in the
replay pilot; all workloads record squashed loads/stores, so the squash path is
live. The counters are from `stats.txt`
(`commitStats0.numLoadInsts/numStoreInsts`, `lsq0.forwLoads/rescheduledLoads`).

## Provenance

Each `baselines_v3_2_2/<workload>/run_meta.json` records the command, exit code,
oracle result, binary SHA256, workload SHA256, stats SHA256 and config SHA256.
The v3.2.1 baselines under `baselines/` remain labelled with the older binary
(`b233a4cb…`) and are not presented as v3.2.2 results.

## Caveat

The baseline is fault-free; it proves the platform and the target events, not a
fault model. Formal Warm-up/ROI values remain `NEEDS_RESEARCHER_CONFIRMATION`
(see `LSU_Warmup_ROI_Recommendation_v3.2.2.md`).
