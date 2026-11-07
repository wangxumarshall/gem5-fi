# LSU v3.2.3 — W1–W8 Fault-Free Baseline

**Binary:** `build/ARM/gem5.opt`
**SHA256:** `8eb7ce8d76ab63d90dbd00694efb90c7c2545da47ad07ecf5325399274a3b682`
**Source:** branch `lsu-platform-v3.2.3`, HEAD `4c53f50e` (code commit `f9c15737`)
**Runner:** `baselines/run_baselines_v323.sh`
**Results:** `baselines_v3_2_3/` (the v3.2.2 `baselines_v3_2_2/` and v3.2.1
`baselines/` trees are untouched)

## Result: 8/8 exit 0 and 8/8 oracle PASS

| W | Workload | Exit | Oracle | finalTick | Loads | Stores | Forwards | Rescheduled |
|---|---|---|---:|---:|---:|---:|---:|---:|
| W1 | agu_addrmodes | 0 | PASS | 19,544,525 | 1,066 | 1,221 | 6 | 1 |
| W2 | lq_lifetime | 0 | PASS | 37,983,715 | 5,476 | 5,485 | 11 | 6 |
| W3 | sq_drain | 0 | PASS | 149,995,615 | 66,721 | 31,092 | 10 | 6 |
| W4 | sq_forward | 0 | PASS | 19,112,940 | 898 | 1,205 | 6 | 1 |
| W5 | load_response | 0 | PASS | 55,153,560 | 17,829 | 3,429 | 11 | 5 |
| W6 | store_path | 0 | PASS | 92,581,720 | 34,985 | 10,609 | 11 | 6 |
| W7 | replay_dependency | 0 | PASS | 40,653,690 | 9,641 | 2,660 | 267 | 5 |
| W8 | alignment | 0 | PASS | 34,556,445 | 6,305 | 3,048 | 11 | 5 |

The numbers are identical to the v3.2.2 baseline, as expected: the v3.2.3 code
changes are inert without a fault (SQ01 mode is off; replay-commit nodes require
the propagation tracer; the baseline runs do not attach it).

Target microarchitectural events confirmed: loads/stores commit in every
workload; W7 has 267 forwards and 5 reschedules (the replay mechanism); squashes
are present in the per-workload stats. Each `baselines_v3_2_3/<workload>/run_meta.json`
records the command, binary SHA256, workload/stats/config hashes and oracle.
