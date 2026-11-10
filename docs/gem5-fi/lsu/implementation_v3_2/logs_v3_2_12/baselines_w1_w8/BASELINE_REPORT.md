# BASELINE_REPORT.md — Task 18 W1–W8 no-fault baselines + test suites (LSU v3.2.12)

Run date: 2026-11-10 (all runs 21:16:00–21:19:31 local).
Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`, HEAD
`f15fe483` ("[LSU][MDSPEC][V3.2.12][BUILD] record the trace-enabled binary SHA").
Mapping source (frozen): `audit_v3_2_12/W1_W8_Baseline_Map_v3.2.12.csv` (9 rows: W1–W7 one
workload each; W8 spans two workloads — W8a `fw05_forward`, W8b `alignment`).
Runbook: `audit_v3_2_12/CLOSURE_INPUTS_v3.2.12.md` §3, `CLOSURE_RUNBOOK_v3.2.12.md`.

## 0. Binary identity

- `build/ARM/gem5.opt` SHA256 =
  `720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070`
  (verified **before and after** all runs — unchanged; gem5 banner: compiled Nov 10 2026
  20:25:20, version 25.1.0.1).
- This is the trace-enabled v3.2.12 binary recorded at HEAD `f15fe483` and in
  `logs_v3_2_12/binary_v3212_trace.sha256`. **Caveat (per task brief): if the binary is
  rebuilt again later, these baselines must be re-run under the new SHA — never merge
  baselines across binaries.**

## 1. Pre-run verification (Task 18 Step 1)

- All 9 workload paths from the map CSV resolve in THIS worktree (workbook paths anchored
  at `lsu-platform-v3.2` / `lsu-platform-v3.2.10` were re-anchored here; contents identical
  per SHA).
- Recomputed workload SHA256: **9/9 match** the map CSV `SHA256_actual` and the workbook
  `SHA256_workbook_recorded` column (identical values).
- Golden files read and compared: **9/9 match** the map's `ExpectedGoldenOracle` /
  workbook `Oracle` (see per-row details in `BASELINE_SUMMARY.csv`).
- Disk gate: `df -h /home` → 67 GiB free (≥ 20 GiB task gate: PASS; note: below the
  campaign tool's own 70.6 GiB redline — see §4).
- No gem5 process running before each run (checked `ps aux | grep gem5`); runs executed
  strictly sequentially, one gem5 process at a time.

## 2. Baseline runs (Task 18 Step 2)

Command per row (outdirs kept in /tmp per task instructions):

```bash
build/ARM/gem5.opt --outdir=/tmp/w<N>_baseline configs/se/lsu_proxy.py --cpu O3 \
  --cmd=<workload absolute path>
```

| W | Workload | Exit | Printed checksum (verbatim last stdout line) | Golden | Verdict |
|---|---|---|---|---|---|
| W1 | workloads/agu_addrmodes | 0 | `728e604ffcec539d` | `728e604ffcec539d` | PASS |
| W2 | workloads/lq_lifetime_ordinal | 0 | `checksum=0xb097eb83f71545cb` | `b097eb83f71545cb` | PASS |
| W3 | workloads/sq_drain | 0 | `checksum=0xba3b3185e541ad03` | `ba3b3185e541ad03` | PASS |
| W4 | workloads/sq_forward | 0 | `1f4cbf14327717df` | `1f4cbf14327717df` | PASS |
| W5 | workloads/load_response | 0 | `checksum=0x99c106541150be0e` | `99c106541150be0e` | PASS |
| W6 | workloads/store_path | 0 | `checksum=0x2543a2a60de01795` | `2543a2a60de01795` | PASS |
| W7 | workloads/replay_dependency | 0 | `checksum=0x59fc61c040618747` | `59fc61c040618747` | PASS |
| W8a | FW05_Workload_Archive/bin/fw05_forward | 0 | `checksum=0x67afad307642983e` | `67afad307642983e` | PASS |
| W8b | workloads/alignment | 0 | `checksum=0x3f89eab79392ce69` | `3f89eab79392ce69` | PASS |

**Result: 9/9 PASS (0 FAIL, 0 SKIP).** Every row: exit 0, printed checksum equals the
frozen golden (oracle PASS). No workload was NOT_APPLICABLE — all 9 print a checksum.
Full per-row detail (workload SHA, binary SHA, run timestamp, outdir): see
`baselines_w1_w8/BASELINE_SUMMARY.csv` (this directory).

Format observation (informational, no impact on the verdict): the map NOTES say the
`checksum=0x…` prefix format applies to the `lq_lifetime_ordinal` / `store_path` /
`alignment` *golden files* (verified true). The **stdout** print format differs from the
golden-file format for four workloads (W3/W5/W7 print the prefix while their golden files
are bare hex; W8a's golden is `0x…` without the `checksum=` label). Oracle comparison is
on the 16-hex-digit value in all cases; all values match.

### Canonical unaffected regression (CLOSURE_INPUTS §0/§3.3)

```bash
build/ARM/gem5.opt --outdir=/tmp/reg_chain_3212 configs/se/arm_chaos.py \
  --cmd workloads/directed/reg_chain --cpu O3
```

Exit 0, printed checksum `f247ef3fe6f02cfd` == canonical golden → **PASS**.

## 3. Test suites (Task 18 Step 3; no gem5 involved)

### 3.1 Repo suite

```
$ python3 -m pytest tests/ -q
3 failed, 131 passed in 18.69s
```

Failed (3), all pre-existing at clean HEAD `f15fe483` (no tracked file modified by this
task; `git status` shows only untracked pilot dirs owned by other concurrent tasks):

1. `tests/test_claim_concurrency.py::test_d_run_concurrency_cap` — the campaign tool
   aborts its helper run with `"reasons": ["磁盘 free 66.7 GiB < 红线 70.6 GiB
   (=max(50, 20%×353))"]`. **Environmental**: current /home free space (66.7 GiB) is
   below the campaign tool's own disk redline (70.6 GiB).
2. `tests/test_claim_concurrency.py::test_e_heartbeat` — same root cause (helper run
   rc=1 on the same disk redline).
3. `tests/test_lsu_v325_workbook.py::test_model_status_matrix_lq04_and_others` — expects
   the LQ04 `evidence` cell to be the v3.2.10 text, but
   `MODEL_STATUS_MATRIX.csv` now carries the v3.2.11 ResearchAdjudication text
   ("structural COMPLETE, fault-effect LIFECYCLE_ONLY, 5/5 MASKED, oracle PASS, no
   corruption; PROPAGATION_VERIFIED=0"). A data/test-expectation mismatch, not caused by
   this task; recorded, not modified (tests must not be touched per task brief).

### 3.2 Platform suite

```
$ python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests -q
78 passed in 2.32s
```

**78 passed, 0 failed.**

## 4. Concerns / notes for the closer

1. **Disk redline**: /home free is 66.7 GiB — above this task's 20 GiB gate but below
   the campaign tool redline 70.6 GiB (=max(50, 20%×353)). It already fails
   `test_claim_concurrency.py` (2 tests) and would abort any campaign-based run
   (CLOSURE_RUNBOOK gate P3 expects ≥ 70.6 GiB). Disk was 72 GiB at runbook prep time;
   other tasks' pilot outputs and the rebuilt binary consumed the difference. Needs
   ~4 GiB reclaimed before campaign-dependent work.
2. **LQ04 evidence-cell mismatch** (§3.1 item 3): `MODEL_STATUS_MATRIX.csv` vs
   `test_lsu_v325_workbook.py` expectation — needs an owner (likely resolved by Task 19
   Excel v3.2.7 / MODEL_STATUS_MATRIX update).
3. **Binary finality**: baselines were run on `720eb780…`. If Tasks 7–15 force another
   rebuild, re-run all 9 baselines on the new SHA before closing Task 18.
4. Run outputs are in `/tmp/w1_baseline … /tmp/w8b_baseline`, `/tmp/reg_chain_3212`
   (per task brief: only the summary CSV and this report are written to the repo).
5. Nothing was committed (per task brief); the two files in this directory are staged
   for the main agent to commit.
