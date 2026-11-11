# RP01 Workload Evidence — LSU v3.3.2 (P0-2)

**Round:** LSU v3.3.2  **Agent:** G  **Date:** 2026-11-11
**Workload:** `workloads/directed/replay_partial_v332`
**Verdict:** **SUFFICIENT** — 255 distinct `PartialAddrRangeCoverage`-eligible
events inside `main` (requirement: >=5), count-only, no injection, normal exit.

## 1. Source and identity

| Item | Value |
|---|---|
| Source | `workloads/directed/replay_partial_v332.c` |
| Source SHA256 | `ab0365411d8d084d215cc87856801618938e706282fe007d1d8642098794e35b` |
| ELF | `workloads/directed/replay_partial_v332` |
| ELF SHA256 | `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42` |
| Build | `workloads/directed/compile_replay_partial_v332.sh` (`gcc -O2 -static`, native aarch64) |
| Golden | `workloads/directed/replay_partial_v332.golden` = `0xf3b1c554273d23f7` |
| Golden SHA256 | `0f06282f962c7254df2d1b8a8dda791a8523437f88c1ab914aa58a069c10e56b` |

Design: 256 fixed iterations. Per iteration `i`:

- 8-byte store at `buf + 8*i`  — covers bytes `[8i, 8i+8)`
- 4-byte load  at `buf + 8*i + 6` — covers bytes `[8i+6, 8i+10)`

The load range is **not contained** in the store range (2 bytes covered, 2 bytes
outside), so `LSQUnit::read()` computes `PartialAddrRangeCoverage`, not
`FullAddrRangeCoverage`. The task brief's suggested 4-byte load at `+2` would be
**fully** covered by the 8-byte store (`req_s >= st_s && req_e <= st_e`) and
would take the full-forward branch, not the partial branch. Its replacement by
`+6` is the correction.

The stored value runs a 16-step dependent
`eor/mul/eor` chain before the store, so the store data is not ready for many
cycles while the younger load's address (loop induction) is ready. The load
therefore executes while the 8-byte store is still in the store queue and not
completed. The loaded 4 bytes feed the checksum, so the oracle is meaningful.

Determinism: fixed trip count, no randomness, no external input; seed is
`0x9E3779B97F4A7C15 ^ argc` (runtime value, not constant-folded).

## 2. Host verification (real output)

```
$ ./replay_partial_v332
checksum=0xf3b1c554273d23f7
$ ./replay_partial_v332
checksum=0xf3b1c554273d23f7
$ cat replay_partial_v332.golden
0xf3b1c554273d23f7
```

The gem5 run produced the same checksum (`checksum=0xf3b1c554273d23f7`), i.e. the
count-only observer did not perturb the program result.

## 3. Disassembly of `main` (objdump)

`main` spans `0x4004f0`–`0x4005c8`. The relevant pair:

```
  40055c:	f9000080 	str	x0, [x4]        <- 8-byte store at buf + 8*i
  400560:	b8406080 	ldur	w0, [x4, #6]    <- 4-byte load at buf + 8*i + 6
  400564:	91002084 	add	x4, x4, #0x8
```

The store and the load are adjacent in the compiled loop body (no reordering;
volatile accesses preserve order). All 255 in-`main` RP01 events carry
`load_pc=4195680` = `0x400560`, exactly this `ldur`.

## 4. Exact count-only preflight command

```
build/ARM/gem5.opt --outdir=audit_v3_3_2/workloads/RP01_runs/p1 \
  configs/se/lsu_proxy.py \
  --cmd=$PWD/workloads/directed/replay_partial_v332 \
  --cpu O3 --variant B0 --probability 1.0 \
  --chaos_propagation --prop_trace_file prop_trace.csv.gz \
  --chaos_lsqfwd --lsq_struct_mode rp01_count_only \
  --max_faults 0 --rng_seed 3135797961 \
  --rp01_event_ordinal 0 --rp01_watchdog_cycles 500000000
```

Exit status `0`. Result: `simInsts=40477`, `simTicks=36304345`, no panic, no
watchdog. Summary line from `lsq_fwd_injections.log`:

```
CHAOS_RP01_STATUS: fired=0 injected=0 eligible=260 load_seq=0 load_pc=0 lq_idx=0 lq_gen=0 store_seq=0 replay_gen=0
```

`fired=0` / `injected=0` is correct for count-only mode (observe, never skip).

Raw outputs: `audit_v3_3_2/workloads/RP01_runs/p1/` (stdout.log = the RP01
event stream, stats.txt, lsq_fwd_injections.log, prop_trace.csv.gz).

## 5. First five `RP01_ELIGIBLE` lines (verbatim)

```
RP01_ELIGIBLE ordinal=1 load_seq=12370 load_pc=4195680 lq_idx=748 lq_gen=1234 store_seq=12369 replay_gen_pre=0 replay_gen_post=1 in_instsToReplay_pre=0 in_instsToReplay_post=1 tick=15946315
RP01_ELIGIBLE ordinal=2 load_seq=13030 load_pc=4195680 lq_idx=750 lq_gen=1259 store_seq=13029 replay_gen_pre=0 replay_gen_post=1 in_instsToReplay_pre=0 in_instsToReplay_post=1 tick=16131885
RP01_ELIGIBLE ordinal=3 load_seq=13168 load_pc=4195680 lq_idx=751 lq_gen=1260 store_seq=13167 replay_gen_pre=0 replay_gen_post=1 in_instsToReplay_pre=0 in_instsToReplay_post=1 tick=16161915
RP01_ELIGIBLE ordinal=4 load_seq=13304 load_pc=4195680 lq_idx=752 lq_gen=1261 store_seq=13303 replay_gen_pre=0 replay_gen_post=1 in_instsToReplay_pre=0 in_instsToReplay_post=1 tick=16186940
RP01_ELIGIBLE ordinal=5 load_seq=13437 load_pc=4195680 lq_idx=753 lq_gen=1262 store_seq=13436 replay_gen_pre=0 replay_gen_post=1 in_instsToReplay_pre=0 in_instsToReplay_post=1 tick=16214275
```

## 6. Distinctness argument

Programmatic parse of `stdout.log` (`RP01_ELIGIBLE` lines, ordinal 1..260):

| Metric | Value |
|---|---|
| Total eligible lines | 260 |
| Distinct `(load_seq,lq_idx,lq_gen,store_seq,replay_gen_post)` tuples | **260** |
| Distinct `load_seq` / `store_seq` | 260 / 260 |
| Lines with `load_pc = 0x400560` (inside `main`) | **255** (ordinals 1–255) |
| Distinct tuples among the 255 in-`main` lines | **255** |
| `store_seq == load_seq - 1` for all in-`main` lines | yes |
| `replay_gen_pre/post` for all in-`main` lines | 0 / 1 |
| Ordinal numbering contiguous 1..260 | yes |

Each in-`main` event is a different dynamic load (`load_seq` all distinct), and
every one is paired with the immediately preceding dynamic store
(`store_seq = load_seq - 1`), i.e. the 8-byte store emitted at `0x40055c` in the
same loop iteration. `lq_idx`/`lq_gen` differ per event as well (748/1234 …
1003/1512). Hence the five required contexts are distinct on every recorded
dimension: dynamic load identity, LQ entry identity, stalling-store identity,
and replay generation transition (0->1).

Honest note: ordinals 256–260 (5 events) occur after `main` returns, at libc PCs
`0x40163c`, `0x422a98`, `0x42a718`, `0x42a71c`, `0x44e32c`. They are outside
`main` and are excluded from the 255-event count above. The requirement's
"all load_pc in main's range" is satisfied for ordinals 1–255, which include the
first five.

## 7. Determinism replication

The same command was re-run into `audit_v3_3_2/workloads/RP01_runs/p2`:

```
$ diff <(grep RP01_ELIGIBLE p1/stdout.log) <(grep RP01_ELIGIBLE p2/stdout.log)
$ echo $?
0
```

Byte-identical event stream (all 260 lines), identical checksum
`0xf3b1c554273d23f7`, exit status 0. This is a determinism replication, not an
independent sample.

## 8. Relationship to the frozen RP01 seeds

This evidence proves the **workload capability** under the R01 seed
(3135797961) used in the task's preflight command. A second count-only run with
the R02 seed (226489823, outdir `RP01_runs/p3_r02seed`) produced a
**byte-identical** 260-line event stream and the same checksum:

```
$ diff <(grep RP01_ELIGIBLE p1/stdout.log) \
       <(grep RP01_ELIGIBLE p3_r02seed/stdout.log) >/dev/null; echo $?
0
```

Count-only mode consumes no RNG on this path, so the eligible stream is
seed-independent here. Mapping R01–R05 to specific ordinals remains a
downstream step.

## 9. Files

- `workloads/directed/replay_partial_v332.c`
- `workloads/directed/compile_replay_partial_v332.sh`
- `workloads/directed/replay_partial_v332` (ELF)
- `workloads/directed/replay_partial_v332.golden`
- `audit_v3_3_2/workloads/RP01_evidence.md` (this file)
- `audit_v3_3_2/workloads/RP01_runs/p1/` (R01 seed preflight)
- `audit_v3_3_2/workloads/RP01_runs/p2/` (R01 seed determinism replication)
- `audit_v3_3_2/workloads/RP01_runs/p3_r02seed/` (R02 seed cross-seed check)
