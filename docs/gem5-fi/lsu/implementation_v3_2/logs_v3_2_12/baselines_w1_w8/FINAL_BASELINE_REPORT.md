# FINAL_BASELINE_REPORT.md — Task 18 W1–W8 no-fault baselines re-run on the final-candidate binary (LSU v3.2.12)

Run date: 2026-11-11, 00:21:13–00:23:33 local (baselines) and 00:21:53–00:23:19 (reg_chain).
Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`, HEAD
`86813b91` ("[LSU][MDSPEC][V3.2.12][A01-A03] relocate the rerun pilots under the evidence tree").
Mapping source (frozen): `audit_v3_2_12/W1_W8_Baseline_Map_v3.2.12.csv` (9 rows: W1–W7 one
workload each; W8 spans two workloads — W8a `fw05_forward`, W8b `alignment`).
Supersedes: `BASELINE_SUMMARY.csv` / `BASELINE_REPORT.md` in this directory, which were run
on the earlier trace binary `720eb780…` at HEAD `f15fe483`.

## 0. Binary identity — final-candidate confirmation

- `build/ARM/gem5.opt` SHA256 =
  `68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`
  (recomputed **before and after** all runs — unchanged; file mtime Nov 10 23:39, gem5
  version 25.1.0.1).
- This matches, byte for byte:
  1. the final-candidate SHA recorded in the repo at
     `logs_v3_2_12/binary_v3212_final_candidate.sha256` (commit `eec513e5`
     "[LSU][MDSPEC][V3.2.12][BUILD] record the final-candidate binary SHA");
  2. the binary used by the RP01 Task 15 pilots/controls
     (`audit_v3_2_12/RP01_Task15_Evidence_v3.2.12.md`);
  3. the binary used by the A01/A03 reruns
     (`audit_v3_2_12/A01_A03_Rerun_Records_v3.2.12.csv`, every row keyed
     `68c6ce737a…`).
- **68c6ce73… IS CONFIRMED as the final binary for these baselines.** It is the designated
  final-candidate on which all v3.2.12 closure evidence (RP01, A01/A03 reruns) is keyed, and
  this re-run proves its no-fault behavior is checksum-identical to the previous trace
  binary (see §2). Standing caveat (unchanged from the previous report): if the binary is
  ever rebuilt again, these baselines must be re-run under the new SHA — never merge
  baselines across binaries. Note `binary_v3212_trace.sha256` still records the historical
  `720eb780…` (the trace binary of the superseded run); do not confuse the two records.

## 1. Pre-run verification

- All 9 workload paths from the map CSV resolve in THIS worktree (workbook paths anchored
  at `lsu-platform-v3.2` / `lsu-platform-v3.2.10` re-anchored here; contents identical per
  SHA). Recomputed workload SHA256: **9/9 match** the map `SHA256_actual` and the workbook
  `SHA256_workbook_recorded` columns.
- Golden files read and compared: **9/9 match** the map's `ExpectedGoldenOracle`.
- Disk gate: `df -h /home` → 67 GiB free ≥ 20 GiB task gate (PASS; still below the campaign
  tool's own 70.6 GiB redline — see §4).
- Slot discipline: `pgrep -a gem5` checked before every run; no other gem5 was active;
  runs executed strictly sequentially, one gem5 process at a time. Binary SHA re-verified
  unchanged after the last run.

## 2. Baseline runs

Command per row:

```bash
build/ARM/gem5.opt --outdir=/tmp/w<N>_final configs/se/lsu_proxy.py --cpu O3 \
  --cmd=<workload absolute path>
```

| W | Workload | Exit | Printed checksum (verbatim last stdout line) | Golden | Verdict | vs 720eb780 run |
|---|---|---|---|---|---|---|
| W1 | workloads/agu_addrmodes | 0 | `728e604ffcec539d` | `728e604ffcec539d` | PASS | identical |
| W2 | workloads/lq_lifetime_ordinal | 0 | `checksum=0xb097eb83f71545cb` | `b097eb83f71545cb` | PASS | identical |
| W3 | workloads/sq_drain | 0 | `checksum=0xba3b3185e541ad03` | `ba3b3185e541ad03` | PASS | identical |
| W4 | workloads/sq_forward | 0 | `1f4cbf14327717df` | `1f4cbf14327717df` | PASS | identical |
| W5 | workloads/load_response | 0 | `checksum=0x99c106541150be0e` | `99c106541150be0e` | PASS | identical |
| W6 | workloads/store_path | 0 | `checksum=0x2543a2a60de01795` | `2543a2a60de01795` | PASS | identical |
| W7 | workloads/replay_dependency | 0 | `checksum=0x59fc61c040618747` | `59fc61c040618747` | PASS | identical |
| W8a | FW05_Workload_Archive/bin/fw05_forward | 0 | `checksum=0x67afad307642983e` | `67afad307642983e` | PASS | identical |
| W8b | workloads/alignment | 0 | `checksum=0x3f89eab79392ce69` | `3f89eab79392ce69` | PASS | identical |

**Result: 9/9 PASS (0 FAIL, 0 SKIP).** Every row: exit code 0, zero SIGSEGV, each outdir
contains real simulation products (`stats.txt`, `config.ini`, `config.json`,
`citations.bib`); stderr shows only the benign `warn: ignoring syscall mprotect(...)`
plus gem5 startup chatter.

**Comparison with the previous summary (`BASELINE_SUMMARY.csv`, binary `720eb780…`):**
all 9 rows have identical exit codes (0) and identical printed checksums. **No
difference exists to explain** — exactly as required, since the binary delta
(`720eb780…` → `68c6ce73…`) was trace-emission only (A03 stream/activation nodes, RP01
skip markers); this re-run empirically confirms the delta had zero effect on no-fault
architectural behavior. The only cosmetic variance remains the print-format split noted
before: W3/W5/W7 print a `checksum=0x…` prefix while their golden files are bare hex;
oracle comparison is on the 16-hex-digit value in all cases.

### Canonical unaffected regression

```bash
build/ARM/gem5.opt --outdir=/tmp/reg_chain_final configs/se/arm_chaos.py \
  --cmd workloads/directed/reg_chain --cpu O3
```

Exit 0, printed checksum `f247ef3fe6f02cfd` == canonical golden → **PASS** (identical to
the previous run; 00:21:53–00:23:19, real `stats.txt` produced).

## 3. Test suites (no gem5 involved)

### 3.1 Repo suite

```
$ pytest tests/ -q
3 failed, 151 passed in 21.91s
```

Failed (3) — **all pre-existing** (the same 3 failed in the previous baseline run on
`720eb780…`; none was caused by this task, no test was modified):

1. `tests/test_claim_concurrency.py::test_d_run_concurrency_cap` — the campaign tool
   aborts its helper run rc=1: `"reasons": ["磁盘 free 66.1 GiB < 红线 70.6 GiB
   (=max(50, 20%×353))"]`. **Environmental** (disk below the campaign tool's own
   redline).
2. `tests/test_claim_concurrency.py::test_e_heartbeat` — same root cause, verified by
   re-running the test: helper rc=1 with the identical disk-redline reason
   (`disk_free_gib: 66.1 < 70.6`).
3. `tests/test_lsu_v325_workbook.py::test_model_status_matrix_lq04_and_others` — expects
   the LQ04 `evidence` cell to be the v3.2.10 text, but `MODEL_STATUS_MATRIX.csv`
   carries the v3.2.11 ResearchAdjudication text ("structural COMPLETE, fault-effect
   LIFECYCLE_ONLY, 5/5 MASKED, oracle PASS, no corruption; PROPAGATION_VERIFIED=0").
   Data/test-expectation mismatch; recorded, not modified (tests must not be touched).

Delta vs the previous run: passed count grew 131 → 151 (20 new tests added by concurrent
v3.2.12 tasks at HEAD, e.g. the Excel v3.2.7 builder commit `f028126b`); the failed set is
unchanged — no previously-passing test now fails.

### 3.2 Platform suite

```
$ pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests -q
107 passed in 3.38s
```

**107 passed, 0 failed** (previous run: 78 passed; 29 new tests added by the platform
work at HEAD — all green).

## 4. Concerns / notes for the closer

1. **Disk redline**: /home free is 66–67 GiB — above this task's 20 GiB gate but below
   the campaign tool redline 70.6 GiB (=max(50, 20%×353)). It already fails 2
   `test_claim_concurrency.py` tests and would abort any campaign-based run. Needs
   ~4 GiB reclaimed before campaign-dependent work (e.g. Task 20 packaging).
2. **LQ04 evidence-cell mismatch** (§3.1 item 3): needs an owner (Excel v3.2.7 builder /
   MODEL_STATUS_MATRIX task).
3. **Binary finality**: confirmed (see §0) — baselines now exist for the final-candidate
   binary `68c6ce73…` and match the closure-evidence binary. If any later rebuild occurs,
   re-run all 9 baselines before closing.
4. Run outputs are in `/tmp/w1_final … /tmp/w8b_final`, `/tmp/reg_chain_final` (per task
   brief, only the summary CSV and this report are written to the repo).
5. Nothing was committed (per task brief); the two files in this directory are left for
   the main agent to commit.
