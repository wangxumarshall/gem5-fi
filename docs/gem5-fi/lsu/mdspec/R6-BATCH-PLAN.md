# R6 FORMAL batch plan — launcher, concurrency, output isolation, resume

Lane **L15-v2** (`r6-blocked`, base `97f74786`). Tool: `tools/lsu_r6_schedule.sh`
(the FORMAL batch launcher / resume driver). This document is the launch spec.
**This lane does NOT start the campaign** — the mission forbids it; everything
below is prepared and self-checked only.

Authorities read: `docs/gem5-fi/lsu/mdspec/ready_contract.json`
(`seeds_per_cell=3`, `max_parallel=1`, `formal_outdir=runs/lsu/formal_325`,
`fs_checkpoint=.../fs_cpt_boot/cpt.237949797015`, `verdict.formal_phase=screening`,
`verdict.screening_target=385`, `verdict.focus_target=2401`), `tools/lsu_guard.py`
(lock/claim, gate, monitor), `tools/lsu_campaign.py` (CLI + per-cell outdir),
`docs/gem5-fi/lsu/mdspec/R5-FS-PILOT-EVIDENCE.md` and `STATUS.md` (E1: FS budget
must be 2700 s).

---

## 1. Exact FORMAL command

The contract's per-cell command, verbatim, is the unit of work (one RunID per
invocation, `--max-parallel 1` inside the campaign). The launcher wraps each one
in a guard-supervised session with a dedicated outdir. Exact command for one
RunID `R` (SE cell; contract target `T` is 385, or 2401 for the 14 READY focus
cells):

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt \
LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs \
LSU_GUARD_SLOTS=8 LSU_GUARD_DIR=/home/sdc/gem5-fi-ding/runs/lsu/guard \
python3 tools/lsu_guard.py run \
    --type experiment --desc "R6-BATCH R" --runid R \
    --log /home/sdc/gem5-fi-ding/runs/lsu/formal_325/R/guard_rsrc.log \
    --interval 60 --max-seconds 86400 -- \
  python3 tools/lsu_campaign.py \
    --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
    --outdir /home/sdc/gem5-fi-ding/runs/lsu/formal_325 \
    --cells R --phase screening --screening-target T \
    --max-seeds-per-cell 100000 --max-parallel 1 \
    --timeout 300 --fs-timeout 2700
```

FS cells (`family=armtlb`) add `--fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`.
The whole batch is one command:

```bash
tools/lsu_r6_schedule.sh                 # resume is the default; --force to rerun
```

Verified against the live contract:

| field | value (from contract / measured) |
|---|---|
| READY cells | 241 (SE 232, FS 9) |
| focus cells (target 2401) | 14 READY of 21 contract `focus_runids` (7 are BLOCKED) |
| screening target | 385 |
| per-RunID outdir | `/home/sdc/gem5-fi-ding/runs/lsu/formal_325/<RunID>/` |
| `--fs-timeout` | 2700 (E1) |
| binary sha256 | `f4dbfb9a66e0df80…` — MATCHES `gate.binary_sha256` |

## 2. Output dirs (isolation)

* Root: `/home/sdc/gem5-fi-ding/runs/lsu/formal_325` (the contract's
  `formal_outdir` basename rooted at `runs/lsu`). **Never `/tmp`** — the launcher
  hard-refuses any `--runroot` under `/tmp` (15 GiB tmpfs; an FS batch would fill
  it and `/tmp` is not durable evidence).
* Per RunID: `formal_325/<RunID>/` holds `cell_results.json`, `chain_report.json`,
  `chain_summary.md`, `identity.json`, `guard.out`, `guard_rsrc.log`, and
  `seed<N>/prop_evt.txt.gz`. The campaign is invoked with `--outdir <root>`, which
  is what makes it write `<root>/<RunID>/…`.
* Batch files at the root: `plan.tsv`, `selected_cells.txt`, `focus_cells.txt`,
  `runs.tsv`, `resource_samples.jsonl`, `cap_state.json`.
* Event compression: any raw `prop_evt.txt` is gzipped after a successful run;
  `--compress-logs` also gzips `run.out`/`run.err` > 8 MiB.

## 3. Concurrency policy

Model: one FS gem5 ≈ 2.5–2.7 GiB (measured: RSS 2706–2719 MiB per FS process),
29.9 GiB total RAM, ~16.8 GiB available at plan time.

* **Start at 6.** Raise to 8 only if `MemAvailable > 8 GiB` **and** iowait < 10 %
  **and** no swap growth (2 consecutive ticks) **and** no new `oom_kill`.
* **Drop to 6** if `MemAvailable < 6 GiB` **or** swap grows **or** iowait > 15 %.
* Sampler every **300 s** prints `MemAvailable`, `SwapFree`, iowait (permille),
  load1, gem5 process count and per-process RSS.
* Two extra floors come from `lsu_guard.py` itself and are honoured by the
  dispatcher: `GATE_MEM_MIN_GIB=12` (acquire refused below) and
  `STOP_DISPATCH=10 GiB` (`_try_acquire` refuses). The launcher **never launches
  when the guard would refuse** (in-process `can_acquire()` backpressure), so the
  effective ramp floor is **12 GiB**, not 8 — with 6 FS residents (~16 GiB) the
  8-ramp is realistically reachable only on mostly-SE stretches. This is the
  honest behaviour, not a bug.
* `rc=1` (GATE BLOCKED) and `rc=2` (ACQUIRE REFUSED) are backpressure, not cell
  failure: recorded as `GATE_BLOCKED(requeue)` / `ACQUIRE_REFUSED(requeue)` and
  retried once, serially at cap 1.

## 4. Per-run timeout and orphan reaping

* Inner: `lsu_guard.py --max-seconds 86400` (24 h outer anti-hang cap per RunID).
  On its max-seconds path the guard `SIGTERM`s the group but does **not** SIGKILL,
  so gem5 children can survive a timed-out guard.
* Outer: the launcher's watchdog kills the whole session (`killpg`, TERM → 30 s →
  KILL → `pkill -KILL -s`) once a run exceeds `--max-seconds + 60`. This is the
  step that actually reaps orphans.
* `--max-seconds` must exceed `--fs-timeout`; the launcher refuses a config where
  it does not (`--per-run-timeout must exceed --fs-timeout`).
* Per-sample timeouts are the campaign's own: `--timeout 300` (SE) and
  `--fs-timeout 2700` (FS). Do **not** lower the FS budget — E1/`STATUS.md`
  ("FS 预算需 2700") and `round3_findings.md` confirm shorter budgets truncate the
  evidence stream (and the outer kill then loses it).

## 5. Resume after interruption

Resume is the **default**; no flag needed. Re-run the identical command (same
`--runroot`, which defaults to a stable path so nothing must be retyped):

```bash
tools/lsu_r6_schedule.sh                       # skips complete RunIDs
tools/lsu_r6_schedule.sh --force               # rerun everything selected
tools/lsu_r6_schedule.sh --verify              # no launch: audit identity+completion
```

A RunID is skipped iff **both**:

1. `formal_325/<RunID>/cell_results.json` exists with a non-empty `stop_reason`
   (the campaign always sets one: `screening-target-met`, `seed-cap(N)`, …); and
2. `formal_325/<RunID>/identity.json` matches the current environment —
   `binary_sha256`, `contract_sha256`, `matrix_sha256`, `target`, `phase`.

`identity.json` is written **at launch** (`status=launched`) and rewritten on
success (`status=complete`), so a killed run still leaves a post-mortem identity
record. **Verify a resumed run's identity** with `--verify`, which prints per
RunID: kind, target, `COMPLETE` (yes/no), `IDENTITY` (match / MISMATCH-absent),
and the recorded binary-sha prefix + checkpoint basename + status. The four
identity axes are exactly: **binary sha256 · checkpoint · RunID · seed base**
(seed base 1, recorded in `identity.json`).

If the binary, contract or matrix changes, every identity check fails and the
whole batch is re-run — deliberately: mixing binaries across a formal batch is the
stale-binary failure mode this repo has been bitten by.

## 6. Resource ceilings (measured 2026-10-23)

| resource | ceiling | now | verdict |
|---|---|---|---|
| RAM | 29.9 GiB total; guard gate ≥ 12 GiB free | 14.1–16.8 GiB free | OK (RAM is NOT the binding limit) |
| FS gem5 RSS | ~2.7 GiB each | measured 2706–2719 MiB | 6 residents ≈ 16 GiB |
| swap | guard gate ≥ 4 GiB free | 13.6 GiB free | OK |
| **disk `/home`** | **guard floor = max(50, 20 %×353) = 70.6 GiB free** | **66.5 GiB free (81 % used)** | **BLOCKED** |
| `/tmp` | 15 GiB tmpfs — never used for results | — | enforced by refusal |
| gem5 concurrency | guard hard max 8 slots | — | cap_max ≤ 8 |

## 7. Findings / gaps this lane could not close

1. **The gate is currently BLOCKED on disk, not RAM.** `lsu_guard.py gate`
   reports `磁盘 free 66.5 GiB < 红线 70.6 GiB (=max(50, 20%×353))`. The batch
   cannot acquire until ≈4.1 GiB is freed on `/home` (the 12 `runs/lsu/r6_tlb_*`
   pilot scratch dirs are the obvious first candidates). This is a real,
   reproducible blocker; the launcher now fail-fasts on it (rc=2) instead of
   dispatching 241 runs that would each return `rc=1`.
2. **`tools/lsu_guard.py gate`/`run` crash with a bare GUARD_DIR.** When
   `GUARD_DIR` does not exist, `snapshot()` yields `disk_total_gib=None` and
   `_disk_guard_reason` computes `DISK_MIN_FREE_PCT * total_gib` *before* its own
   `None` check → `TypeError`. The launcher avoids this by always
   `mkdir -p`-ing and exporting `LSU_GUARD_DIR=/home/sdc/gem5-fi-ding/runs/lsu/guard`.
   The underlying ordering bug is in a file owned by another lane — **not fixed
   here** (out of lane scope), reported only.
3. **7 of the 21 contract `focus_runids` are BLOCKED** (`O01/O05-F0-W7`,
   `O09-F0-W13`, `P09-F0-W13` FS-MULTICORE; `T04-F0-W4`, `T10-F0-W4` FS-INFRA;
   `T10-F0-W11` LICENSE). Only the 14 READY focus cells get target 2401; the
   excluded 7 never enter this batch.
4. `--max-seeds-per-cell 100000` is the contract's compute bound, but one RunID
   at 385 (SE) seeds × up to 300 s could exceed the 24 h outer cap on a slow
   host; if a legitimately-long cell is ever clipped, raise `--per-run-timeout`
   (never lower `--fs-timeout`).
5. `--phase main` is wired (`--main-target`) but untested end-to-end here; the
   formal phase is `screening`, per the contract.

---

Self-check (real output, nothing launched):

```
[r6-batch] binary sha256 MATCHES contract gate (f4dbfb9a66e0df80)
[r6-batch] plan written: .../formal_325/plan.tsv (241 rows; FS=9 SE=232 focus=14)
[r6-batch] FS assets OK in /home/sdc/gem5-fi-ding/gem5-fs (9 FS cell(s))
SELF-CHECK: PASS  (validated: args, contract parse, binary sha256, checkpoint dir, FS assets, runroot isolation, plan generation)
SELF-CHECK: selected=241 FS=9 runroot=/home/sdc/gem5-fi-ding/runs/lsu/formal_325 binary_sha=f4dbfb9a66e0df80
```
