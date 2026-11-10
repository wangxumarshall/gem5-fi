# RP01 Count-Only Preflight — v3.2.12 (Task 14, Steps 3–5)

**Status: COMPLETE — all five frozen seeds PASS. `WORKLOAD_INSUFFICIENT_FOR_FIVE_CONTEXTS` was NOT triggered for any seed.**

Executed 2026-11-10 by the RP01 preflight owner (one gem5 slot, sequential runs).
No Task 15 skip/watchdog pilots were run (per instructions — main agent decides
after reviewing this preflight and the wake-up audit).

## 1. Provenance

| Item | Value |
|---|---|
| Worktree | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` |
| Branch / HEAD | `lsu-platform-v3.2.12` @ `f15fe483` (RP01 patch commit `512d937c` is an ancestor, verified) |
| Binary | repo-root `build/ARM/gem5.opt`, SHA `720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070` — byte-identical to the recorded trace-enabled SHA (`logs_v3_2_12/binary_v3212_trace.sha256`, commit `f15fe483`); compiled Nov 10 2026 20:25:20 |
| Workload | `docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency` (W7), SHA `ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4` |
| Seeds (R01–R05) | 3135797961, 226489823, 1735144973, 2455796178, 3984724524 |
| Disk gate | `df -h /home`: 67 GiB free before every run (>= 20 GiB required) — PASS |
| Slot gate | `pgrep -a gem5` checked before each run; zero other gem5 processes at every check; exactly one gem5 process owned by this preflight at a time |

## 2. Seed flag and RP01 flags (Task-1 verification, real quotes)

The LSQFwd/RP01 observer takes the **shared injector seed flag `--rng_seed`**
(there is no separate `--lsq_fwd_rng_seed`/`--lsq_struct_seed`/`--chaos_seed`):

```python
# configs/se/lsu_proxy.py:216
p.add_argument("--rng_seed", type=lambda x: int(x, 0), default=20260825)
```

passed to the SimObject at `configs/se/lsu_proxy.py:907` (`rngSeed=args.rng_seed,`
inside the `CHAOSLSQFwd(...)` construction; `--chaos_lsqfwd` gates it).

RP01 flags present and reaching the SimObject:

```python
# configs/se/lsu_proxy.py:257-262 (choices include both RP01 modes)
p.add_argument("--lsq_struct_mode", default="byte_flip",
               choices=["byte_flip", ..., "rp01_count_only", "rp01_skip_replay"])
# configs/se/lsu_proxy.py:284-289
p.add_argument("--rp01_event_ordinal", type=lambda x: int(x,0), default=0, ...)
p.add_argument("--rp01_watchdog_cycles", type=lambda x: int(x,0),
               default=500000000, ...)
# configs/se/lsu_proxy.py:901-902 (pass-through)
        rp01EventOrdinal=args.rp01_event_ordinal,
        rp01WatchdogCycles=args.rp01_watchdog_cycles,
```

Exact command template (per seed `<S>`; `--outdir` and the log suffix are the
only per-seed differences):

```bash
build/ARM/gem5.opt --outdir=/tmp/rp01_preflight_s<S> configs/se/lsu_proxy.py \
  --cpu O3 --chaos_lsqfwd --lsq_struct_mode rp01_count_only \
  --rp01_event_ordinal 0 --rng_seed <S> \
  --cmd=$PWD/docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency
```

`--chaos_propagation/--prop_trace_file` was NOT needed: `RP01_ELIGIBLE` lines
are printed unconditionally to stdout by `CHAOSLSQFwd::maybeSkipPartialReplay`
(`CHAOSLSQFwd.cc:663-673`) and mirrored into the outdir's
`lsq_fwd_injections.log` with the site name `read_partial_reschedule`.

## 3. Results — canonical five-context stream

All five runs exited 0, produced **exactly 5 `RP01_ELIGIBLE` lines** each, with
**5/5 distinct `(dyn_inst_seq, pc, lq_gen, store_seq)` tuples**, zero
`RP01_SKIP_REPLAY` lines, zero panic/fatal/SIGSEGV, and the **byte-identical
RP01_ELIGIBLE stream across all five seeds** (verified by full-line diff R01 vs
R02–R05 — identical). The canonical stream (any seed):

| Ordinal | dyn_inst_seq | PC | Tick | Cycle | LQ idx | LQ gen | store_seq | replay gen pre→post | in_instsToReplay pre→post |
|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| 1 | 69341 | 0x4015fc | 31072965 | 80709 | 9201 | 9693 | 69334 | 0→1 | 0→1 |
| 2 | 71013 | 0x42a6d8 | 35427700 | 92020 | 9349 | 9915 | 71007 | 0→1 | 0→1 |
| 3 | 71014 | 0x42a6dc | 35428085 | 92021 | 9350 | 9916 | 71003 | 0→1 | 0→1 |
| 4 | 72018 | 0x422a58 | 36564990 | 94974 | 9427 | 10049 | 72000 | 0→1 | 0→1 |
| 5 | 72350 | 0x44e2ec | 37424310 | 97206 | 9467 | 10096 | 72346 | 0→1 | 0→1 |

Per-seed summary (all real output from the runs):

| Pilot | Seed | Eligible events | Distinct tuples | Duplicates | Verdict | Exit-status line (injector log) |
|---|---:|---:|---:|---:|---|---|
| R01 | 3135797961 | 5 | 5/5 | 0 | **PASS** | `CHAOS_RP01_STATUS: fired=0 injected=0 eligible=5` |
| R02 | 226489823 | 5 | 5/5 | 0 | **PASS** | `CHAOS_RP01_STATUS: fired=0 injected=0 eligible=5` |
| R03 | 1735144973 | 5 | 5/5 | 0 | **PASS** | `CHAOS_RP01_STATUS: fired=0 injected=0 eligible=5` |
| R04 | 2455796178 | 5 | 5/5 | 0 | **PASS** | `CHAOS_RP01_STATUS: fired=0 injected=0 eligible=5` |
| R05 | 3984724524 | 5 | 5/5 | 0 | **PASS** | `CHAOS_RP01_STATUS: fired=0 injected=0 eligible=5` |

Every run ended with the workload's own `checksum=0x59fc61c040618747` — the
recorded W7 golden (`final_paper_audit_v3_1/workload_sources/replay_dependency.golden`;
also `LSU_End_to_End_Propagation_Audit_v3.2.md` line 254). The count-only
observer perturbs nothing: the run stays on the fault-free baseline.

## 4. Agreement with the v3.2.11 design table (probe vs clean preflight)

`RP01_Dynamic_Contexts_v3.2.11.md` §2 listed the five events from the FW02
fault-on probe (`REPLAY-RW02`). Comparison with this clean count-only stream:

| Ordinal | Probe PC (fault-on) | Preflight PC (clean) | Probe tick | Preflight tick | Probe seq (lq_idx/lq_gen) | Preflight seq (lq_idx/lq_gen) |
|---:|---|---|---:|---:|---|---|
| 1 | 0x4015fc | 0x4015fc | 31072965 | 31072965 | 69296 (9200/9690) | 69341 (9201/9693) |
| 2 | 0x42a6d8 | 0x42a6d8 | 35427700 | 35427700 | 70968 (9348/9912) | 71013 (9349/9915) |
| 3 | 0x42a6dc | 0x42a6dc | 35428085 | 35428085 | 70969 (9349/9913) | 71014 (9350/9916) |
| 4 | 0x422a58 | 0x422a58 | 36564990 | 36564990 | 71973 (9426/10046) | 72018 (9427/10049) |
| 5 | 0x44e2ec | 0x44e2ec | 37424310 | 37424310 | 72305 (9466/10093) | 72350 (9467/10096) |

**PCs and ticks match exactly.** `dyn_inst_seq` and `lq_idx/lq_gen` differ by a
small constant offset (+45 seq; +1/+3 lq) because the v3.2.11 probe ran with an
FW02 fault on — its injected forwarding suppression perturbed the dynamic
instruction numbering — while this preflight is the clean stream. The design
doc itself required this re-proof ("evidence of the event stream, not of RP01
causality... must be re-proven by a clean count-only preflight"). The clean
stream above is now the authoritative identity table for ordinals 1–5; the
frozen R01→1 ... R05→5 ordinal mapping stands against it.

## 5. Observations and concerns for the main agent

1. **Seed-invariance is expected and confirmed.** In `rp01_count_only` mode the
   injector never draws RNG (the legacy forwarding-corruption hook returns
   early, `CHAOSLSQFwd.cc:332-333`; the selector is purely ordinal-based), so
   the five seeds produce byte-identical eligible streams. The pilots R01–R05
   therefore differ by **ordinal (1–5)**, not by seed-driven stream variation.
   The seeds stay frozen for protocol reproducibility (SampleRunIDs
   `RP01-F6-W7-S01-R01..R05`) and for any future RNG-consuming component in the
   same run; they are not what distinguishes the five contexts.
2. **The workload is exactly saturated at five.** `eligible_events_total = 5`
   for every seed — ordinal 999 (select-none control) and any ordinal > 5
   select nothing, by design. There is no sixth context; if a pilot needs a
   spare context, the workload must change (out of scope this round).
3. **`in_instsToReplay_pre=0 / post=1` on every event** — matches the task-14
   wake-up audit conclusion P1: the `rescheduleMemInst` call this hook guards
   is the sole insertion route into `MemDepUnit::instsToReplay`, and no stale
   membership exists.
4. **Count-only never skipped** (`fired=0 injected=0`, zero `RP01_SKIP_REPLAY`
   lines) and every run reproduced the W7 golden checksum — the preflight is a
   clean observation, not a perturbation.
5. **PC coverage:** each event's load PC is distinct, and the five PCs match
   the v3.2.11 probe exactly — the workload exercises five distinct partial
   forward-mismatch sites, satisfying the five-context design table's
   dimensions at the `(seq, pc, lq_gen, store_seq)` level required by the
   brief.
6. **Not run (by instruction):** Task 15 `rp01_skip_replay` pilots and the
   watchdog ordinal controls. The preflight alone does NOT prove the skip
   semantics or the HANG/SQUASHED terminals — those belong to Task 15 after
   the main agent reviews this preflight and the wake-up audit
   (`task-14-audit-report.md`, which proved no other path re-issues a skipped
   load).

## 6. Deliverables and raw evidence

- CSV (25 rows = 5 seeds x 5 ordinals): `audit_v3_2_12/RP01_CountOnly_Preflight_v3.2.12.csv`
  — columns: `seed, run_id, event_ordinal, dyn_inst_seq, pc_hex, pc_dec, tick,
  lq_idx, lq_gen, store_seq, replay_gen_pre, replay_gen_post,
  in_instsToReplay_pre, in_instsToReplay_post, cycle, eligible_events_total,
  distinct_tuple_count, five_contexts_verdict`.
- This narrative: `audit_v3_2_12/RP01_CountOnly_Preflight_v3.2.12.md`.
- Raw evidence (archived from the run scratch dirs): `audit_v3_2_12/rp01_preflight_raw/`
  — per seed: `console_s<seed>.log` (full stdout incl. the 5 RP01_ELIGIBLE
  lines and the command line), `lsq_fwd_injections_s<seed>.log` (cycle-tagged
  site records + `CHAOS_RP01_STATUS` exit line), `config_s<seed>.ini`
  (verified: the five configs differ ONLY in `rngSeed=<seed>`). The outdirs
  `/tmp/rp01_preflight_s<seed>/` also retain `stats.txt`/`config.json`.
- Report to the SDD plan: `.superpowers/sdd/2026-11-10-lsu-v3-2-12-propagation-closure/rp01-preflight-report.md`.

## 7. Verification commands actually run (proof excerpts)

```
$ grep -c RP01_ELIGIBLE /tmp/rp01_preflight_s3135797961.console.log
5
$ tail -1 /tmp/rp01_preflight_s3135797961.console.log
checksum=0x59fc61c040618747
$ diff <(grep RP01_ELIGIBLE .../s3135797961...) <(grep RP01_ELIGIBLE .../s226489823...)
R01_STREAM == R02_STREAM            (identical for R03/R04/R05 too)
$ sha256sum build/ARM/gem5.opt
720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070  build/ARM/gem5.opt
$ python3 /tmp/rp01_verify.py
R01..R05: eligible_events=5 distinct_tuples=5/5 verdict=PASS duplicates=none
ALL_FIVE_PASS=True
```
