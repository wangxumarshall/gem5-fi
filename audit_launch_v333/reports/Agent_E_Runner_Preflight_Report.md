# Agent E — Runner, Dry-Run & Output-Path Preflight (LSU v3.3.3)

Audit date: 2026-11-12. Read-only preflight. No runner/source/Excel/workload was modified; **gem5 was not invoked**; no pilot or formal run was started.

Repo root (all relative paths below resolve here): `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
HEAD at audit time: `b8405580` (working tree has unrelated untracked dirs; the four audited files are unchanged).

The only file written is this report: `audit_launch_v333/reports/Agent_E_Runner_Preflight_Report.md`.

## Commands actually run (all read-only or write-free)

```
python3 tools/lsu_v332_matrix.py --help
python3 tools/lsu_v332_matrix.py --models all --roles fault,control --dry-run
python3 tools/lsu_v332_matrix.py --models all --roles fault,control --contexts 1,2,3,4,5 \
  --out-base <ROOT>/runs/lsu/formal_v333 \
  --out-csv  <ROOT>/runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv --dry-run
python3 tools/lsu_v332_matrix.py --models all --roles fault,control --jobs 4 --dry-run   (negative test)
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py --help
python3  # structure/uniqueness/pairing analysis of the captured dry-run output
python3  # config_parser.load_config(Excel) dump of per-model SampleRunID/Seed/EventOrdinal
sha256sum build/ARM/gem5.opt configs/se/lsu_proxy.py <9 workload ELFs>
ls -ld / du -sh / df -h / test -w   # collision, permissions, space
json/csv inspection of audit_v3_3_3/runs/*/{summary,pilot_meta,manifest}.json and the ROI/controls CSVs
```

The exact emitted dry-run output is retained at `/tmp/dryrun.txt` (default out-base) and `/tmp/dryrun_formal.txt` (proposed out-base). Neither invocation created a run dir, summary, manifest or CSV: `ls -ld runs/lsu/formal_v333` → `No such file or directory`.

---

## 0. Environment / frozen inputs (verified live)

| Item | Value |
|---|---|
| Binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/build/ARM/gem5.opt`, SHA256 `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338` (1,149,173,888 B) |
| Config | `configs/se/lsu_proxy.py`, SHA256 `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` |
| Excel identity source | `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx` — exists; 5 rows per model, rows map R01…R05 in order |
| Frozen CSV | `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` — 60 rows; authoritative SampleRunID form `A01-F0-W1-S01-R01` |
| Free space | `/home` 354G total, 285G used, **51G free** (the Final Acceptance Report says 58 GiB; stale, still > the 20 GiB rule) |
| Prior rehearsal evidence | `audit_v3_3_3/runs/` — 120 dirs, 120 `manifest.json`, 105 `trace_v31.jsonl`, 3.2 GB |

---

## 1. Runner interface (Check 1)

`python3 tools/lsu_v332_matrix.py --help` (real output):

```
usage: lsu_v332_matrix.py [-h] [--models MODELS] [--roles ROLES]
                          [--contexts CONTEXTS] [--out-base OUT_BASE]
                          [--out-csv OUT_CSV] [--dry-run]

options:
  -h, --help           show this help message and exit
  --models MODELS
  --roles ROLES
  --contexts CONTEXTS
  --out-base OUT_BASE  run directory base (default: the v3.3.3 round)
  --out-csv OUT_CSV
  --dry-run            print the exact command for every row and exit; no run
                       dir, summary or CSV is written
```

| # | Item | Result | Evidence |
|---|---|---|---|
| 1.1 | argparse surface | **PASS** | Above. There is **no `--jobs`** (see defect D-7). |
| 1.2 | `MODELS` | **PASS** | `tools/lsu_v332_matrix.py:51-52` = 12 ids A01,A03,FW02,FW05,SQ01,SQ03,SP05,DA04,LP01,MD04,LQ04,RP01. |
| 1.3 | `CONTEXTS` | **PASS** | `:58-89`; 12 entries; each has `roi`, `n`, 5 ordinals; A01/A03 use the v3.3.3 re-census (A01 585-713/129, A03 1040-1222/183). |
| 1.4 | roles / counts | **PASS** | `--roles fault,control` → 60 fault + 60 control in the dry-run. |
| 1.5 | out-base / out-csv defaults | **FAIL (unsafe)** | `:743-747` defaults point at the existing v3.3.3 evidence tree: `audit_v3_3_3/runs` and `audit_v3_3_3/controls/LSU_Fault_Control_Pair_RAW.csv`. A real run with defaults would `rm -rf` each rehearsal run dir (`:611-612`) and overwrite the RAW CSV. Explicit flags avoid it (see §3). |
| 1.6 | model→workload | **PASS** | Table below; every ELF exists and SHA was recomputed. |
| 1.7 | Seed source | **PASS** | run_pilot path: `--context-index` → Excel row seed (`run_pilot.py:749-757`), no `--seed` on argv. A03/RP01 direct path uses `CONTEXTS[...]["seeds"]`; all 5 values per model equal the Excel rows. |
| 1.8 | SampleRunID source | **FAIL / gap** | run_pilot replaces the frozen id with the pilot id (`run_pilot.py:758-766`) because the matrix never passes `--preserve-sample-id` (`matrix:388-399`). Direct A03/RP01 manifests set `sample_run_id: null` with an honest note (`matrix:517-519`). Downstream `tools/lsu_v332_report.py:339` then **invents** `V332-<MODEL>-R<NN>` (see D-6). |
| 1.9 | Binary path | **PASS** | `matrix:40` → repo-root `build/ARM/gem5.opt`, SHA above; matches rehearsal manifests. |
| 1.10 | Config path | **PASS** | `matrix:41` → `configs/se/lsu_proxy.py`, SHA above. |
| 1.11 | Output dir naming | **PASS** | `<OUT_BASE>/<MODEL>-R<NN>-<role>` (`matrix:609-610`), 2-digit context; 120/120 unique. |
| 1.12 | Parallel scheduling | **PASS (serial by design)** | Nested loops `model → context → role` (`:781-786`); one `subprocess.run` at a time. A process-wide `fcntl.flock(LOCK_EX)` on `audit_v3_3_2/controls/.lsu_v332_matrix.lock` (`:49`, `:560-572`, `:780`) serializes concurrent matrix invocations. No gem5 runs concurrently. |
| 1.13 | Retry / failure handling | **PARTIAL** | No retry at all. Per-row exceptions are caught and recorded as `{"error": ...}` (`:785-791`); the runner still **returns 0** (`:794`) even if every row failed. The run_pilot branch's `subprocess.run(..., timeout=400)` (`:683-685`) is not wrapped, so `TimeoutExpired` becomes an error row with no `summary.json`. Direct runs do handle timeout (`run_direct`, `:575-595`). |
| 1.14 | Manifest generation | **PASS (with caveats)** | run_pilot runs: `manifest.json` written **before** gem5 starts (`run_pilot.py:803-819`), so it survives crashes. Direct runs: written after the run (`matrix:481-521`). Rehearsal evidence: 120/120 manifests. Caveat: direct manifests have `sample_run_id: null`. |
| 1.15 | Trace naming | **PARTIAL** | gem5 writes `prop_trace.csv.gz` → run_pilot converts to `trace_v31.jsonl`. Direct A03/RP01 runs never convert (`matrix:621-680` call no converter), so 15 dirs have no `trace_v31.jsonl` (A03 fault ×5, RP01 fault ×5, RP01 control ×5). Rehearsal: 105/120. |
| 1.16 | summary / CSV writing | **PASS (with caveats)** | `summary.json` per run (`:733`), rehearsal 120/120. CSV written only on a real run, inside the lock, after all rows (`:792`); columns `:797-808`. Caveat: no SampleRunID column; exit status always 0 (D-4). |

### 1.6 Model → workload (verified on disk)

| Model | Workload path (RUNS) | ELF SHA prefix | Source | Golden |
|---|---|---|---|---|
| A01 | `docs/gem5-fi/lsu/implementation_v3_2/workloads/agu_addrmodes` | `90a1900377d2` | `run_pilot._workload_for` | `728e604ffcec539d` |
| A03 | same `agu_addrmodes` (explicit in CONTEXTS) | `90a1900377d2` | CONTEXTS | `728e604ffcec539d` |
| FW02 | `workloads/directed/sq_forward_w4v2` | `a08fb3a7b8bb` | CONTEXTS | `1f4cbf14327717df` |
| FW05 | `docs/.../workloads/fw05_forward` | `0cf405092e33` | `_workload_for` | `0x67afad307642983e` |
| SQ01 | `docs/.../workloads/sq_reload_v3212` | `bcab9cc5e1e4` | CONTEXTS | `7df5034c23f3e703` |
| SQ03 | same `sq_reload_v3212` | `bcab9cc5e1e4` | CONTEXTS | `7df5034c23f3e703` |
| SP05 | same `sq_reload_v3212` | `bcab9cc5e1e4` | CONTEXTS | `7df5034c23f3e703` |
| DA04 | `docs/.../workloads/alignment` | `89ff937a73a0` | `_workload_for` | `checksum=0x3f89eab79392ce69` |
| LP01 | `docs/.../workloads/load_response` | `3779e8ced41a` | `_workload_for` | `99c106541150be0e` |
| MD04 | `workloads/directed/md04_violations_v332` | `dd241c3097e6` | CONTEXTS | `0x22be5ae3364d0c9f` |
| LQ04 | `docs/.../workloads/lq_lifetime_ordinal` | `fa25f785a482` | CONTEXTS | `checksum=0xb097eb83f71545cb` |
| RP01 | `workloads/directed/replay_partial_v332` | `3f880cba7b6d` | CONTEXTS | `0xf3b1c554273d23f7` |

All 9 distinct ELF paths exist; all goldens exist.

---

## 2. Dry-run proof: 120 commands (Check 2)

Command:

```bash
python3 tools/lsu_v332_matrix.py --models all --roles fault,control --dry-run
```

Real tail of output:

```
DRY-RUN RP01 R05 fault: <ROOT>/build/ARM/gem5.opt --outdir=<ROOT>/audit_v3_3_3/runs/RP01-R05-fault <ROOT>/configs/se/lsu_proxy.py --cmd=<ROOT>/workloads/directed/replay_partial_v332 --cpu O3 --variant B0 --probability 1.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz --chaos_lsqfwd --lsq_struct_mode rp01_skip_replay --max_faults 1 --rng_seed 3984724524 --rp01_event_ordinal 230 --rp01_watchdog_cycles 20000000
DRY-RUN RP01 R05 control: <ROOT>/build/ARM/gem5.opt --outdir=<ROOT>/audit_v3_3_3/runs/RP01-R05-control <ROOT>/configs/se/lsu_proxy.py --cmd=<ROOT>/workloads/directed/replay_partial_v332 --cpu O3 --variant B0 --probability 0.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz
dry-run: 120 commands; no run dirs written
```

Machine-checked properties (script over the captured output):

| Property | Result |
|---|---|
| Line count | **120** (60 fault / 60 control) |
| Models × contexts | **12 × 5** = 60 (model, context) pairs, all present, 5 roles each |
| Missing `(model, context, role)` combos | **0** |
| Duplicate combos | **0** |
| Unique `--outdir` | **120 / 120**; no duplicates |
| Fault/control pairing | **60 / 60 complete**; each pair shares the same `--cmd` (A03 control is implicit via `_workload_for` → same `agu_addrmodes`; RP01 control explicit) |
| Event ordinal | Identical ordinal in every pair. A03 expresses the same value via a different flag (`--addrpath_event_ordinal` on the direct fault vs `--event-ordinal` on the run_pilot control). RP01 control omits the ordinal because the injector is omitted by design (INJECTOR_ABSENT). |
| Seed | run_pilot runs carry no `--seed`; seed = Excel row via `--context-index`. A03/RP01 direct runs carry `--rng_seed`, equal to the Excel Seed for every context (verified against `load_config`). |
| SampleRunID | **Not present in argv for any of the 120** (run_pilot path derives the pilot id from `--pilot-id`; direct commands have no identity flag). See D-5/D-6. |
| Manifest | Expected 120/120. Evidence: the 120/120 rehearsal manifests. run_pilot writes pre-run; direct writes post-run. |
| Audit history untouched | With an explicit `--out-base`, the emitted commands contain **no** `audit_v3_3_3` reference (grep = 0). With the **default** out-base they all target `audit_v3_3_3/runs` and would delete the rehearsal (D-1/D-2). |

### 2.1 SampleRunID / Seed per pair (representative, from argv + Excel)

| Model | R01 seed (Excel = argv) | R01 ordinal (argv) | SampleRunID in argv |
|---|---|---|---|
| A01 | 2108120075 (Excel) | 597 | absent |
| A03 | 663646247 (`--addrpath_rng_seed`) | 1058 | absent |
| FW02 | 2941542370 (Excel) | 13 | absent |
| FW05 | 1025137124 (Excel) | 200 | absent |
| SQ01 | 591611458 (Excel) | 1018 | absent |
| SQ03 | 2214819981 (Excel) | 1021 | absent |
| SP05 | 1489155957 (Excel) | 952 | absent |
| DA04 | 4185444934 (Excel) | 135 | absent |
| LP01 | 1349924126 (Excel) | 2549 | absent |
| MD04 | 2595563470 (Excel) | 3 | absent |
| LQ04 | 1842987246 (Excel) | 1 | absent |
| RP01 | 3135797961 (`--rng_seed`) | 26 | absent |

All 60 seeds match the frozen workbook (A03/RP01 CONTEXTS seeds were compared row-by-row and are equal).

---

## 3. Output paths, collision, lock, CSV separation (Check 3)

| Check | Result | Evidence |
|---|---|---|
| Proposed formal out-base `runs/lsu/formal_v333` | **PASS** | Does not exist (`ls` → No such file); parent `runs/lsu` is `drwxr-xr-x sdc:sdc` and writable (`test -w`). `main()` creates it with `mkdir(parents=True)` (`:775`). |
| Collision with `audit_v3_3_3` history | **PASS only with explicit flags** | `--out-base`/`--out-csv` override the destructive defaults. Dry-run with the formal flags emitted 120 unique paths all under `runs/lsu/formal_v333`, zero `audit_v3_3_3` references. |
| CSV path separation | **PASS with explicit flags** | RAW CSV at `runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv`; curated FINAL CSV is written by `tools/lsu_v332_report.py` to a separate `--out` dir. The v3.3.2 `_J` collision file is not touched. Default CSV would overwrite `audit_v3_3_3/controls/LSU_Fault_Control_Pair_RAW.csv` (D-2). |
| Lock | **PASS (by code; not exercised concurrently)** | Fixed lock `audit_v3_3_2/controls/.lsu_v332_matrix.lock`; dir exists and is writable; exclusive `flock` held across the whole run set and the CSV write. Because the path is fixed (not derived from `--out-base`), two campaigns with different out-bases still serialize. |
| Re-run behavior | **FAIL (operational)** | `run_context` does `rm -rf <outdir>` unconditionally (`:611-612`). A re-run deletes completed formal results and starts over; there is no resume/skip (D-3). |
| Relative-path portability | **WARN** | `--out-base` is stored as given (`:752`). Direct runs pass a possibly-relative `--outdir` to gem5 (`:579`) while Python creates it relative to the caller's CWD; gem5 runs with `cwd=ROOT`. Use an absolute `--out-base` (as in §4) or launch from repo root (D-8). |
| Disk | **PASS** | Rehearsal 120 dirs = 3.2 GB; 51 GB free. Per-model: MD04 1,199 MB, LP01 607 MB, FW05 369 MB, DA04 261 MB, A03 200 MB. |
| Batching caveat | **WARN** | `write_csv` opens with `"w"` (`:804`), so each invocation rewrites the CSV with only its own rows. Do not split the campaign into several `--models` batches sharing one `--out-csv`; use one invocation (or distinct CSVs and merge). |

---

## 4. Proposed formal launch command (do NOT run yet)

Parameter-verified against the current interface; the dry-run form exits 0 with 120 commands. Absolute paths are used deliberately (D-8). Do **not** add `--jobs` (D-7).

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
python3 tools/lsu_v332_matrix.py \
  --models all \
  --roles fault,control \
  --contexts 1,2,3,4,5 \
  --out-base /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/runs/lsu/formal_v333 \
  --out-csv  /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv
```

Pre-flight gate before launching (all write-free):

```bash
# 1. the exact dry-run must still say 120 and reference only formal_v333
python3 tools/lsu_v332_matrix.py --models all --roles fault,control \
  --out-base <ROOT>/runs/lsu/formal_v333 \
  --out-csv  <ROOT>/runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv --dry-run | tail -1
# expected: dry-run: 120 commands; no run dirs written

# 2. no prior formal output, binary/config unchanged
test ! -e <ROOT>/runs/lsu/formal_v333 && echo CLEAN
sha256sum build/ARM/gem5.opt configs/se/lsu_proxy.py
# expected: 1126e0fd... and 8309da72...

# 3. enough space
[ "$(df -Pk /home | awk 'NR==2{print int($4/1048576)}')" -ge 20 ] && echo SPACE_OK
```

### 4.1 Built-in scheduling order (120 tasks, strictly serial)

The runner's order is **model-major → context R01…R05 → role fault then control** (`:781-786`; `MODELS` order at `:51-52`). Each fault is immediately followed by its matched control, which is good for pair review:

```
A01 R01 fault, A01 R01 control, A01 R02 fault, A01 R02 control, … A01 R05 control
A03 R01 fault, A03 R01 control, … A03 R05 control
FW02 … FW05 … SQ01 … SQ03 … SP05 … DA04 … LP01 … MD04 … LQ04 …
RP01 R01 fault, RP01 R01 control, … RP01 R05 control
```

The captured output confirms this (`A01 R01 fault`, `A01 R01 control`, `A01 R02 fault`, …; last = `RP01 R05 control`). Because the runner is serial and does not resume, the simplest correct schedule is **one invocation in this order**.

### 4.2 Runtime / resource estimate (1 gem5 at a time)

Measured from the 120-dir rehearsal (`summary.elapsed` is the gem5 subprocess only; wall span is dir mtime):

| Metric | Value |
|---|---|
| Sum of recorded gem5 elapsed | **429.1 s (7.2 min)** |
| Observed rehearsal wall span | 10:54:42 → 11:23:13 = **28.5 min** (one continuous sweep) |
| Long poles (gem5) | RP01 fault ~21 s/run (5 runs), A03 fault ~14 s/run (5 runs) |
| Wall-heavy models (log parsing/size) | MD04 ~42 s/run (6.98 min for 10), LP01 3.61 min/10, FW05 2.50 min/10 |
| Disk | 3.2 GB for 120 dirs (MD04 1.2 GB, LP01 0.6 GB); 51 GB free |
| Concurrency | **1 gem5 process** (serial); CPU ~1 core busy; host RAM is not a constraint (cap of 4 concurrent is not approached) |
| Realistic wall estimate | **~30–40 min** on this host (matches the Final Acceptance Report), plus ~1 min report generation |
| Worst-case timeout bound | 105 run_pilot × 400 s + 15 direct × 300 s ≈ **46 500 s ≈ 12.9 h** if every run hangs |

The wall estimate exceeds the 7.2 min gem5 sum because per-run trace conversion/manifest/log parsing (MD04 is the dominant case) is not included in `elapsed`.

---

## 5. Defect list (file:line, severity, one-shot fix)

| ID | Severity | Location | Defect | One-shot fix |
|---|---|---|---|---|
| D-1 | High | `tools/lsu_v332_matrix.py:743` | `--out-base` defaults to `audit_v3_3_3/runs`, i.e. the existing 120-run evidence tree; combined with D-3 it deletes history. | Make it required: `ap.add_argument("--out-base", required=True, ...)` (or default to `ROOT/"runs/lsu/formal_v333"`). |
| D-2 | High | `tools/lsu_v332_matrix.py:745-747` | `--out-csv` defaults to the existing `audit_v3_3_3/controls/LSU_Fault_Control_Pair_RAW.csv`; overwrites rehearsal evidence. | `default=None`, then in `main`: `SUMMARY_CSV = Path(args.out_csv) if args.out_csv else OUT_BASE/"LSU_Fault_Control_Pair_RAW.csv"`. |
| D-3 | Medium | `tools/lsu_v332_matrix.py:611-612` | Unconditional `rm -rf <outdir>`: re-run destroys completed formal results; no resume/skip. | Before deleting, if `(outdir/"summary.json")` exists and its `binary_sha` matches the current binary, `return` that summary; else move the old dir to `<outdir>.bak.<ts>`. |
| D-4 | Medium | `tools/lsu_v332_matrix.py:785-794` | Always `return 0`; a campaign with 120 error rows reports success. | After `write_csv`, `failed = sum(1 for r in rows if r.get("error") or not r.get("binary_sha"))`; `print(f"FAILED {failed}")`; `return 2 if failed else 0`. |
| D-5 | High (provenance) | `tools/lsu_v332_matrix.py:388-399`; `run_pilot.py:758-766,1063,1106` | No run artifact carries the frozen SampleRunID: run_pilot replaces it with the pilot id (`<MODEL>-R<NN>-<role>`); direct manifests set it to `null`. | In `run_pilot_cmd` add `"--preserve-sample-id"`; in `run_pilot.py` change both `convert(..., sample_run_id=args.pilot_id, ...)` calls to `sample_run_id=sample["sample_run_id"]`. Manifest and trace then carry `A01-F0-W1-S01-R01` etc. (Alternatively keep pilot ids and rejoin downstream, but then rename the mapping column — see D-6.) |
| D-6 | High (provenance) | `tools/lsu_v332_report.py:339` | Emits `"SampleRunID": f"V332-{model}-R{ctx:02d}"` — an invented id; the frozen matrix has `A01-F0-W1-S01-R01`. Existing artifact `audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv` contains `V332-A01-R01`. | Join `60_SAMPLE_MATRIX.csv` on `(FaultModelID, ordinal)` and emit its `SampleRunID`; or rename the column to `ContextMapID` and add a separate authoritative `SampleRunID`. |
| D-7 | Medium (docs) | `docs/superpowers/plans/2026-11-12-lsu-v333-final-closure.md:453` | Documented launch is `… --jobs 4`; the current runner has no `--jobs` → argparse **exit 2** (`error: unrecognized arguments: --jobs 4`, verified). | Replace with the §4 command (no `--jobs`; the runner is already serial). The Final Acceptance Report §5 command is correct apart from using relative paths. |
| D-8 | Low | `tools/lsu_v332_matrix.py:752,579` | Relative `--out-base` is passed to gem5 unchanged for direct runs while Python resolves against CWD; only safe when launched from repo root. | `OUT_BASE = Path(args.out_base).resolve()` at `:752` (and use the resolved path everywhere). |
| D-9 | Medium (gap) | `tools/lsu_v332_matrix.py:621-680` | Direct A03/RP01 runs produce `prop_trace.csv.gz` but no `trace_v31.jsonl`; 15/120 rehearsal dirs have no trace. | After `run_direct`, call `tools.prop_trace_to_v31.convert(...)` as run_pilot does, or explicitly write `trace_completeness: PARTIAL_PROP_TRACE` into `summary.json`/`pilot_meta.json` (the report tool already special-cases these models). |
| D-10 | Low | `tools/lsu_v332_matrix.py:683-685` | run_pilot `subprocess.run(..., timeout=400)` not wrapped: `TimeoutExpired` → error row, no `summary.json` (manifest exists). | Wrap in `try/except subprocess.TimeoutExpired` and record `timed_out: true`, `terminal: HANG` in the row. |
| D-11 | Low (docs) | `audit_v3_3_3/LSU_v3.3.3_Final_Acceptance_Report.md` §5 | Says "58 GiB free"; live `df` shows **51 G**. The 20 GiB rule still holds. | Update the figure at package time. |
| — | Info | `tools/lsu_v332_matrix.py:44,49` | Module-level `OUT_BASE`/`SUMMARY_CSV` still point at `audit_v3_3_2`; overridden in `main`, but helpers such as `classify_controls()` use the stale global if called outside `main`. | Set the globals from `args` before any helper use (already true in `main`); optional cleanup. |

No defect was found in the _shape_ of the 120-command set: counts, pairing, uniqueness, ordinals, seeds and context coverage are all correct.

---

## 6. Verdict per check

| Check | Verdict |
|---|---|
| 1. Runner interface (structure, models/contexts/roles, seeds, binary/config, naming, serial scheduling, manifests, summaries) | **PASS** with the provenance and failure-status gaps D-4/D-5/D-9/D-10 |
| 1. Safe defaults for out-base/out-csv | **FAIL** (D-1/D-2) — the explicit flags in §4 must always be used |
| 2. 120-command dry-run | **PASS** — real output captured; 60 fault + 60 control, 12×5, unique paths, complete pairs, correct seeds/ordinals, no history writes with explicit flags, 120 manifests expected |
| 3. Formal out-base / permissions / lock / CSV separation | **PASS** with the §4 command; **FAIL** with defaults. Lock is process-wide and fixed; CSV paths are separate; 51 G free vs ~3.2 G needed |
| 4. Launch command + order + runtime | **PASS** — command verified by dry-run; order is model-major, serial; estimate ~30–40 min wall, 3.2 GB |

**Overall: READY to launch the formal campaign with the §4 command.** The two blockers are operational, not structural: (a) never omit `--out-base`/`--out-csv` until D-1/D-2 are fixed, and (b) decide the SampleRunID policy (D-5/D-6) before the results are used as formal evidence.

---

## 7. Could not verify

- Actual injection counts, terminals, oracle outcomes and control zero-proofs for a **formal** run — no gem5 was executed by design; the rehearsal artifacts were inspected instead.
- Peak RSS / peak CPU of gem5 (no process launched); the serial schedule makes the 4-process cap irrelevant.
- `flock` behavior under two truly concurrent matrix invocations (reasoned from `matrix_lock`, not exercised).
- Whether an adding `--preserve-sample-id` is the researcher's intended identity policy (D-5 is a decision as well as a code change).
- Long-run stability of the 20M-cycle RP01 watchdog and the 1M-cycle A03 watchdog beyond the rehearsal observations (21 s / 14 s per run).
