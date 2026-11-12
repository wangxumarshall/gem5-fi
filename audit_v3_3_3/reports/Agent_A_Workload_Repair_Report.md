# Agent A — Workload Root-Cause & Design Audit (FW02 / RP01 / MD04)

LSU v3.3.3 closure round — read-only Phase-1 audit. Date 2026-11-11.
Scope: FW02 (`sq_forward_w4v2`), RP01 (`replay_partial_v332`), MD04 (`md04_violations_v332`).
No file under `CHAOS/`, `configs/`, `workloads/`, `docs/gem5-fi/lsu/implementation_v3_2/`,
`tools/`, `audit_v3_3_2/` or the Excel was modified. No gem5/pilot was run. The native
static ELFs were executed on the host (aarch64) to check the goldens; that is not a gem5 run.

## 0. Provenance and method

| Item | Value |
|---|---|
| Worktree | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` |
| HEAD | `3097ad82e7066f18fc35cf64dcb612a05c1fc021` (matches `README_GROUND_TRUTH.md`) |
| Final binary | `build/ARM/gem5.opt` SHA256 `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca` (re-hashed live) |
| Config | `configs/se/lsu_proxy.py` (`--cpu O3 --variant B0 --probability 1.0 --chaos_propagation`) |
| Evidence root | `audit_v3_3_2/runs/<MODEL>-R0x-{fault,control}/`, `audit_v3_3_2/roi/census_v332/`, `audit_v3_3_2/workloads/` |

All 30 run summaries for the three models report `binary_sha = 070d68a6…` (parsed from
`summary.json` of every `{FW02,RP01,MD04}-R0*-{fault,control}` dir). FW02/MD04 exit 0;
RP01 control exit 0 and RP01 fault exit 1 (watchdog `fatal`, see §2).

Candidate artifacts (all tracked, working tree clean for these paths — `git ls-files` +
`git status --short`):

| File | SHA256 |
|---|---|
| `workloads/directed/sq_forward_w4v2` | `a08fb3a7b8bbcef76b0c3c3519a5787370ea7ead2d93de290e00fc6e44fe76e2` |
| `workloads/directed/sq_forward_w4v2.c` | `472b1eef62be94b85ea8b07b11b16806347597ac0ad9d01b45dcf9e1b89e340e` |
| `workloads/directed/sq_forward_w4v2.golden` | `668cacca3762804dcb1c00f0ddc96bb4f43d9b42ad2f2ebea3347457f1a63921` (=`1f4cbf14327717df`) |
| `workloads/directed/replay_partial_v332` | `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42` |
| `workloads/directed/replay_partial_v332.c` | `ab0365411d8d084d215cc87856801618938e706282fe007d1d8642098794e35b` |
| `workloads/directed/replay_partial_v332.golden` | `0f06282f962c7254df2d1b8a8dda791a8523437f88c1ab914aa58a069c10e56b` (`0xf3b1c554273d23f7`) |
| `workloads/directed/md04_violations_v332` | `dd241c3097e61495141e614ce493ba4b2901a7df751baa95e69365bdf8f95c43` |
| `workloads/directed/md04_violations_v332.c` | `9b1f57a901205ae8f855392f99b1f059c73d69d7c240adc1eae019747c7e6a6d` |
| `workloads/directed/md04_violations_v332.golden` | `19570bca402ede050e8c3d51225b0791f2cf89662c2b4b9a6cb0d8830a7830b0` (`0x22be5ae3364d0c9f`) |

**Reproduction proof (source → ELF):** recompiling each committed `.c` with the committed
flags (`gcc -O2 -static`) in `/tmp/provcheck` produced byte-identical ELFs:

```
a08fb3a7…  sq_forward_w4v2     (== repo)
3f880cba…  replay_partial_v332 (== repo)
dd241c30…  md04_violations_v332(== repo)
```

**Golden proof (ELF → golden):** running the repo ELFs natively on the aarch64 host:

```
$ ./sq_forward_w4v2        -> 1f4cbf14327717df        (golden ==)
$ ./replay_partial_v332    -> checksum=0xf3b1c554273d23f7 (golden ==)
$ ./md04_violations_v332   -> checksum=0x22be5ae3364d0c9f (golden ==)
```

**Original (frozen) W4:** `docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_forward`
SHA256 `132a84f7f21be052bc1f2c9baf1c12d5bd3462aae03b1d42778c94e69b0af297`, golden
`1f4cbf14327717df`. Its `static unsigned long buf[N]` is non-volatile.

---

## 1. FW02 — `sq_forward_w4v2` (W4-v2)

### (a) Design claim

"Same seven designed scenarios as frozen W4, but every array access is `volatile`, so at
`-O2` the store→load pairs are preserved; detection surface unchanged (checksum)." The
source comment (`workloads/directed/sq_forward_w4v2.c:1-8`) claims full-overlap and
"8B store / 4B load at +2 partial" pairs.

### (b) Static evidence (`objdump -d --disassemble=main`)

Full-overlap `str`/`ldr` pair, phase 1 (same buffer index, 8B/8B):

```
  400530: f8247823  str x3, [x1, x4, lsl #3]
  400534: 8b050063  add x3, x3, x5
  400538: f8647824  ldr x4, [x1, x4, lsl #3]     <- load PC 0x400538, 32 iterations
```

8B store / 4B load at +2, phase 2 (`x4` advanced by 8; `[x4,#-6]` = buffer byte +2):

```
  400570: f8237825  str x5, [x1, x3, lsl #3]
  400574: b85fa083  ldur w3, [x4, #-6]           <- load PC 0x400574, 8 iterations
```

Other in-main pairs used by the five contexts:

```
  40061c: f8247822  str x2, [x1, x4, lsl #3]     phase 5 dependency chain
  400620: f8647822  ldr x2, [x1, x4, lsl #3]     <- load PC 0x400620, 8 iterations
  400654: f8237824  str x4, [x1, x3, lsl #3]     phase 6 interleaved (two stores)
  400658: f8637823  ldr x3, [x1, x3, lsl #3]     <- load PC 0x400658, 16 iterations
```

Census of `main` (`objdump … | grep -oE '\b(ldr|ldur|ldrb|ldp|ldar|str|stur|strb|stp)\b'`):
`1 ldp, 8 ldr, 1 ldur, 8 str, 1 stur, 2 strb, 1 stp` = 10 loads / 12 stores, of which
9 buffer data loads and 10 buffer data stores; the `ldp`/`stp` are the stack frame and one
`strb` is the local `put_hex` scratch. This matches `audit_v3_3_2/workloads/W4_v2_evidence.md §2c`.

Note on "partial": the loop-2 load at +2 covers bytes [2,6), which is **fully inside** the
8B store [0,8). It is a *sub-width byte-mask partial forward*, not a
`PartialAddrRangeCoverage` event. That is correct for FW02 because
`CHAOS/gem5/src/cpu/o3/lsu_unit.cc:1782-1792` calls `maybeSuppressForwarding()` only inside
the `FullAddrRangeCoverage` branch. (The true partial-range scenario is RP01, §2.)

**Frozen W4 failure (static):** `docs/…/workloads/sq_forward` main contains
`1 ldp, 9 stp, 5 str, 1 strb` and **zero** `ldr/ldur/ldrb` — the non-volatile buffer
loads were folded (e.g. loop 1 at 0x400530-0x400544 does `str x1,[x2],#8` then
`eor x0,x0,x1` on the register, never re-loading). The frozen W4 therefore cannot form a
store→load forwarding pair. `W4_v2_evidence.md §2c` records the same ("Frozen W4
non-volatile build had 1 load / 15 stores"; the "1 load" is the stack `ldp`).

### (c) Dynamic evidence

Census: `audit_v3_3_2/roi/census_v332/FW02_w4v2_all_suppress/run.log` ends with
`1f4cbf14327717df`; `lsq_fwd_injections.log` ends
`CHAOS_FW02_SUMMARY: observed=67 suppressed=1 load_seq=258 store_seq=248`.

Independent parse of all 67 `FW02_w4v2_sweep_K*` probe logs (each probe fires at ordinal K;
Vaddr/load_seq/store_seq read from `lsq_fwd_injections.log`):

| ordinal range | zone | count | samples |
|---|---|---|---|
| 1–7 | pre-main (stack/libc) | 7 | K1 `0x7ffffefbd0`, K3 `0x496798`, K4/K5 `0x48fb70`, K6/K7 stack |
| 8–67 | `main` buffer `0x4919a0–0x491a9f` | 60 | K8 `0x4919a8` (buf[1]) … K67 `0x491a18` |

So the run-level `observed=67` is **7 pre-main + 60 in-main**. The claim
"67 in-main forwarding events" (`audit_v3_3_2/report/LSU_v3.3.2_Final_Acceptance_Report.md:74`)
is off by 7. The correct in-main count is 60, which is exactly ROI N=60 (ordinals 8–67).
The W4_v2 evidence text itself only says "67 eligible … decisions", not "in-main".

Ordinal segmentation in main (from the sweep): 8–38 = phase-1 loop1 (`0x400538`, i=1..31;
i=0 is not observed, the store has drained), 39–45 = phase-2 loop (`0x400574`, i=1..7),
46–53 = phase-5 (`0x400620`), 54–67 = phase-6 (`0x400658`).

The injected fault runs match the seed-`2941542370` sweep exactly even though R02–R05 use
different seeds:

| ctx | command ordinal | load_seq/store_seq | Vaddr | observed |
|---|---|---|---|---|
| R01 | 13 | 12243/12241 | 0x4919d0 | 67 |
| R02 | 25 | 12479/12477 | 0x491a30 | 68 |
| R03 | 37 | 12587/12585 | 0x491a90 | 68 |
| R04 | 49 | 13344/13343 | 0x4919c0 | 67 |
| R05 | 61 | 13572/13571 | 0x4919e8 | 67 |

(`runs/FW02-R0x-fault/command.txt` each carry `--lsqfwd_event_ordinal 13/25/37/49/61`.)

### (d) Five-context table (ROI 8–67, N=60; `k=ceil(p·N)` = 6/18/30/42/54; ordinal = 8+k−1)

| ctx | p | k | ordinal | load PC | VA | store_seq | static site | terminal |
|---|---|---|---|---|---|---|---|---|
| R01 | .10 | 6 | 13 | 0x400538 | 0x4919d0 (buf[6]) | 12241 | phase-1 full 8B/8B | SDC |
| R02 | .30 | 18 | 25 | 0x400538 | 0x491a30 (buf[18]) | 12477 | phase-1 full 8B/8B | SDC |
| R03 | .50 | 30 | 37 | 0x400538 | 0x491a90 (buf[30]) | 12585 | phase-1 full 8B/8B | MASKED |
| R04 | .70 | 42 | 49 | 0x400620 | 0x4919c0 (buf[4]) | 13343 | phase-5 dependency | SDC |
| R05 | .90 | 54 | 61 | 0x400658 | 0x4919e8 (buf[9]) | 13571 | phase-6 interleaved | SDC |

All five are real distinct dynamic events (distinct load_seq, store_seq, VA). Diversity is
limited: R01–R03 are the *same static load site* (0x400538) with different iteration
indices; only two distinct static load PCs appear across the five contexts (0x400538 ×3,
0x400620, 0x400658).

### (e) Golden / oracle

- Golden `1f4cbf14327717df` is produced by this ELF (host run above) and is byte-identical
  to the frozen W4 golden (`668cacca…`), as designed.
- All five controls (`--probability 0.0`, no injector) print `1f4cbf14327717df` →
  `ORACLE_PASS`.
- Faults: R01/R02/R04/R05 → `ORACLE_FAIL` (SDC); R03 → `ORACLE_PASS` (MASKED, 1/5).
- R03 MASKED is mechanism-consistent, not a fabricated pass: the FW02 trace record for
  R03 (`runs/FW02-R03-fault/trace_v31.jsonl`, `event_type=fw02_decision`) reads
  `normal_decision=forwarded; fault_decision=suppressed; memory_path=1; replay_count=0`.
  Suppressing the forward sent the load to memory and the memory read returned the same
  value (the older store had already become visible), so the checksum is unchanged. The
  exact store-drain state at that moment is not separately instrumented. R01's record is
  identical in shape but its memory read returned the stale value → SDC. This is a
  timing-dependent benign false miss and is honestly labelled MASKED.

### (f) Defects / recommendation

See issues **A-01 … A-05** in §4.

**Recommendation: ADOPT (conditional on documentation fixes).**
Fault semantics preserved: suppression is a conditional false miss at a real full-coverage
pair, no bytes mutated (`lsq_unit.cc:1782-1809`). Five-context feasibility: yes, but only
two static sites; contexts differ by dynamic instance/iteration, not by independent seed.
Golden/oracle valid: yes (host + 5/5 control pass, 4/5 fault SDC, 1 explained MASKED).
Risk: low. Main residual risks are the inflated "67 in-main" prose (A-01) and the
run-dependent stream length 67/68 (A-02).

---

## 2. RP01 — `replay_partial_v332`

### (a) Design claim

256 fixed iterations; per iteration an 8-byte store at `buf + 8*i` and a 4-byte load at
`buf + 8*i + 6`; the load range [8i+6, 8i+10) is not contained in the store range
[8i, 8i+8) (2 bytes overlap, 2 bytes outside) → `PartialAddrRangeCoverage`; skip exactly one
`rescheduleMemInst()` call → the load never replays → HANG/TIMEOUT expected.

### (b) Static evidence (`objdump -d --disassemble=main`)

`readelf -sW`: `buf` at `0x4919c0`, size 2064. `main` loop:

```
  40055c: f9000080  str  x0, [x4]        <- 8B store at buf + 8*i
  400560: b8406080  ldur w0, [x4, #6]    <- 4B load at buf + 8*i + 6   (load_pc=0x400560)
  400564: 91002084  add  x4, x4, #0x8
  400578: eb04013f  cmp  x9, x4         (x9 = buf+0x800)
  40057c: 54fffe21  b.ne 400540
```

This is a genuine partial-range overlap: load bytes [8i+6,8i+10), store bytes [8i,8i+8).
A load at +2 would have been fully covered and would not take this branch (the source and
`audit_v3_3_2/workloads/RP01_evidence.md §1` both state this).

### (c) Dynamic evidence

Count-only preflight `audit_v3_3_2/workloads/RP01_runs/p1/` (mode `rp01_count_only`,
`--rp01_event_ordinal 0`, exit 0). Independent parse of `p1/stdout.log`:

```
total RP01_ELIGIBLE lines: 260
with load_pc=4195680 (0x400560): 255
distinct main tuples (ordinal,load_seq,lq_idx,lq_gen,store_seq,replay_gen_pre/post): 255
ordinals contiguous 1..260: True
```

So the authoritative eligible set is **260 total, 255 in main** (ordinals 1–255), exactly
matching ROI 1–255 (N=255). Ordinals 256–260 are libc PCs after `main` returns
(`RP01_evidence.md §6`).

Every in-main line has `store_seq = load_seq − 1` and `replay_gen 0→1`; the load is the
`ldur` at 0x400560. For the five selected ordinals the count-only stream reads:

```
ordinal=26  load_seq=16293 load_pc=4195680 lq_idx=774 lq_gen=1283 store_seq=16292 tick=16967335
ordinal=77  load_seq=23229 … lq_idx=825 lq_gen=1334 store_seq=23228 tick=18359880
ordinal=128 load_seq=30165 … lq_idx=876 lq_gen=1385 store_seq=30164 tick=20011915
ordinal=179 load_seq=37101 … lq_idx=927 lq_gen=1436 store_seq=37100 tick=21404460
ordinal=230 load_seq=44037 … lq_idx=978 lq_gen=1487 store_seq=44036 tick=23040325
```

These are genuinely distinct dynamic executions (different dyn seq, LQ index/generation,
store seq, tick), but they are the **same static load PC and the same access geometry**
(one iteration apart in the same loop). This is a legitimate "dynamic context" in the
identity-tuple sense, but it is homogeneous — effectively five determinism replications of
one microarchitectural situation, not five different situations.

Fault runs (`--lsq_struct_mode rp01_skip_replay`, ordinals 26/77/128/179/230):

```
R01 lsq_fwd_injections.log last two lines:
  Tick: 16967335, Site: read_partial_reschedule, skipped_call=1, load_seq=16293, load_pc=4195680,
    lq_idx=774, lq_gen=1283, store_seq=16292, replay_gen_pre=0, replay_gen_post=1,
    in_instsToReplay_pre=0, in_instsToReplay_post=0, eligible_ordinal=26, faults_injected: 1
  CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1 eligible=26 tick=7700000000
```

(same shape for R02/R03/R04/R05 with eligible=77/128/179/230). All five fault runs have
`exit_code=1`, no checksum, `oracle=False`, elapsed ≈21.3–21.5 s.

The source is explicit that HANG is the intended terminal
(`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/rp01_rules.hh:29-31`: "Expected terminals: HANG/TIMEOUT
(no older squash) or SQUASHED … Never MASKED … no SDC mechanism exists") and
`CHAOSLSQFwd.cc:604-624` (`fatal("CHAOS_RP01_WATCHDOG_EXPIRED …")`). The skip is the only
route into `MemDepUnit::instsToReplay`, so the skipped load never re-issues and the ROB
stalls until the 20M-cycle watchdog (`--rp01_watchdog_cycles 20000000` × 385 ticks/cycle =
7.7e9 ticks, matches `tick=7700000000`).

**Finding:** the watchdog line is written **only** to `lsq_fwd_injections.log`; it is not
in `stdout.log`. `tools/lsu_v332_matrix.py:parse_rp01_stdout()` reads `stdout.log`, so the
committed `summary.json` records `rp01.watchdog=false` and a derived terminal of `CRASH`
(exit 1, not timed out), while `propagation/LSU_60Context_Causal_Propagation_Final.csv`
correctly says `HANG_WATCHDOG`. See A-06.

### (d) Five-context table (ROI 1–255, N=255; `k=ceil(p·N)` = 26/77/128/179/230)

| ctx | p | k | ordinal | load_pc | load_seq | lq_idx/gen | store_seq | tick | skip | terminal |
|---|---|---|---|---|---|---|---|---|---|---|
| R01 | .10 | 26 | 26 | 0x400560 | 16293 | 774/1283 | 16292 | 16967335 | yes | HANG_WATCHDOG |
| R02 | .30 | 77 | 77 | 0x400560 | 23229 | 825/1334 | 23228 | 18359880 | yes | HANG_WATCHDOG |
| R03 | .50 | 128 | 128 | 0x400560 | 30165 | 876/1385 | 30164 | 20011915 | yes | HANG_WATCHDOG |
| R04 | .70 | 179 | 179 | 0x400560 | 37101 | 927/1436 | 37100 | 21404460 | yes | HANG_WATCHDOG |
| R05 | .90 | 230 | 230 | 0x400560 | 44037 | 978/1487 | 44036 | 23040325 | yes | HANG_WATCHDOG |

Percentile arithmetic verified (26/77/128/179/230). Each run's `command.txt` carries
`--rp01_event_ordinal` = the same value and `--rp01_watchdog_cycles 20000000`.

### (e) Golden / oracle

- Golden `0xf3b1c554273d23f7`; the repo ELF prints it on the host.
- All five controls run to completion (`exit 0`) and print `checksum=0xf3b1c554273d23f7`,
  `oracle=True`. Note the controls omit `--chaos_lsqfwd`, so `rp01.eligible=0` — they
  validate the golden only, not the observe-only path (the count-only p1 run is the
  separate evidence for that).
- The five fault runs have **no** oracle outcome: the in-simulator watchdog aborts them.
  This is consistent with the frozen RP01 design gate (HANG is the expected terminal), not
  an implementation escape.

### (f) Defects / recommendation

See **A-06, A-07, A-08**.

**Recommendation: ADOPT (conditional).**
Fault semantics preserved: skipping the single reschedule call is the freeze-described
fault, and HANG is the source-documented expected terminal; no SDC is claimed. Five-context
feasibility: technically yes (distinct dynamic instances), but diversity is one static
PC/geometry and the outcome is identical for all five. Golden/oracle valid for the control;
fault runs are correctly characterized as HANG_WATCHDOG in the propagation CSV, but
`summary.json` misreports it (A-06 must be fixed before the summary artifacts are trusted).
Risk: low technical, medium on "five distinct contexts" evidence strength.

---

## 3. MD04 — `md04_violations_v332`

### (a) Design claim

Eight distinct in-main 8B-store → younger-load violation pairs (plus 2 libc startup and 1
libc printf = 11 eligible total); the store's data depends on a late load from a large
array while the younger load's address is ready, producing a deterministic race; the
`StoreSet` predictor makes each distinct (store PC, load PC) pair worth about one eligible
event. ROI 3–10 (N=8); ordinals 3/5/6/8/10.

### (b) Static evidence (`objdump -d --no-show-raw-insn --disassemble=main`)

Eight in-main pairs (v2 layout; `main = 0x4004f0–0x4009bf`):

| pair | store PC | load PC | geometry (source) |
|---|---|---|---|
| L1 | 0x4005e8 `str x4,[x5,x2,lsl#3]` | 0x4005ec `ldr x4,[x5,x2,lsl#3]` | 8B/8B same address |
| L2 | 0x400640 `str x2,[x12,x4,lsl#3]` | 0x400644 `ldp x2,x3,[x7],#16` | 8B store slot i+1, 16B load two slots |
| L3 | 0x4006a0 `stur x4,[x2,#4]` | 0x4006a4 `ldr x4,[x2],#16` | 8B unaligned +4, 4B overlap |
| L4 | 0x4006f4 `str x7,[x6,x4,lsl#3]` | 0x4006f8 `ldr x4,[x6,x4,lsl#3]` | 8B/8B dynamic index |
| L5 | 0x400750 `str x2,[x13,x6,lsl#3]` | 0x400754 `ldp x2,x3,[x4]` | 8B store, 16B load |
| L6 | 0x4007b4 `str x7,[x6,x4,lsl#3]` | 0x4007b8 `ldr x4,[x6,x4,lsl#3]` | 8B/8B dynamic index |
| L7 | 0x400800 `stur x4,[x2,#-6]` | 0x400804 `ldr x4,[x2],#16` | 8B at +2, 8B at +8 (2B overlap) |
| L8 | 0x400850 `str x2,[x5,x4,lsl#3]` | 0x400854 `ldp x2,x3,[x7]` | 8B slot i+1, 16B load |

These match `audit_v3_3_2/workloads/MD04_evidence_v2.md` and the current ELF (the v1 PCs
0x4005f8/0x400650… in the older `MD04_evidence.md` are a different layout, see A-09/A-11).

### (c) Dynamic evidence

Selected-ordinal run logs (`runs/MD04-R0x-fault/md04_injections.log`, v2 ELF, 070d68a6):

| ctx | ord | store_pc | load_pc | load/store addr,size | load_complete | oracle |
|---|---|---|---|---|---|---|
| R01 | 3 | 0x4005e8 | 0x4005ec | 0x491990,8 / 0x491990,8 | 1 | PASS (MASKED) |
| R02 | 5 | 0x4006a0 | 0x4006a4 | 0x494990,8 / 0x494994,8 | 0 | FAIL (SDC) |
| R03 | 6 | 0x4006f4 | 0x4006f8 | 0x4929c8,8 / 0x4929c8,8 | 0 | FAIL (SDC) |
| R04 | 8 | 0x4007b4 | 0x4007b8 | 0x4939e8,8 / 0x4939e8,8 | 0 | FAIL (SDC) |
| R05 | 10 | 0x400850 | 0x400854 | 0x491990,16 / 0x491998,8 | 0 | FAIL (SDC) |

Each selected ordinal maps to a **different real pair** (L1, L3, L4, L6, L8), not just a
counter value. All are `Site: checkViolations`; the five have distinct sq/lq entry
identities (e.g. R01 `sq_entry_id=20908 gen=21279, lq_entry_id=750 gen=1226`, R05
`sq_entry_id=26528 gen=26933, lq_entry_id=14038 gen=14601`).

Count / libc split: `audit_v3_3_2/workloads/MD04_runs/p2/md04_injections.log` =
`CHAOS_ELIGIBLE_COUNT=11`; the per-ordinal probes `p2_K1..K11` give 2 libc-startup
(ord 1 stack `0x7ffffefbc0`, ord 2 `0x59f990`), 8 main (ord 3–10), 1 libc/printf (ord 11
`0x428cdc`). **Provenance caveat:** those probes ran on the v1 ELF (v1 PCs/addresses,
e.g. p2_K3 `store_pc=0x4005f8 load_pc=0x4005fc addr=0x49d990`), before the v2 ELF was
rebuilt at 22:07. The v2 total of 11 is therefore inferred, not directly re-measured
(A-09). The eight static pairs and the five selected v2 ordinals are directly verified.

### (d) Five-context table (ROI 3–10, N=8; `k=ceil(p·N)` = 1/3/4/6/8; ordinal = 3+k−1)

| ctx | p | k | ordinal | pair | store_pc/load_pc | terminal |
|---|---|---|---|---|---|---|
| R01 | .10 | 1 | 3 | L1 | 0x4005e8 / 0x4005ec | MASKED |
| R02 | .30 | 3 | 5 | L3 | 0x4006a0 / 0x4006a4 | SDC |
| R03 | .50 | 4 | 6 | L4 | 0x4006f4 / 0x4006f8 | SDC |
| R04 | .70 | 6 | 8 | L6 | 0x4007b4 / 0x4007b8 | SDC |
| R05 | .90 | 8 | 10 | L8 | 0x400850 / 0x400854 | SDC |

Percentile arithmetic verified. All commands carry `--md04_event_ordinal 3/5/6/8/10`.

### (e) Golden / oracle, hook semantics, causality

- Golden `0x22be5ae3364d0c9f`; host ELF prints it.
- All five controls (`--probability 0.0`, no `--chaos_md04`) print it → `ORACLE_PASS`
  (`runs/MD04-R0x-control/oracle.log`), exit 0.
- Hook: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:673-690` (store branch of
  `checkViolations`) calls `cpu->chaosMD04->maybeSkipViolation(...)`; on `true` it
  `break`s — the `M5PanicFault`/`memDepViolator`/`memOrderViolation` bookkeeping for that
  pair is skipped and no address/size/data is changed. `CHAOSMD04.cc:77-160` gates on
  `md04_rules.hh::isEligibleViolationPair` (store size 8, load size ≥8, real overlap,
  shifted-range predicate, younger load) and on the ordinal. This is exactly "suppress the
  violation report for one real pair", as designed.
- Causality: R01 is MASKED and its log shows `load_complete=1` — the younger load's
  response was already consumed, so suppressing the report lets the already-correct value
  commit; checksum unchanged. R02–R05 have `load_complete=0` — the violated load is still
  in flight and commits stale data → oracle FAIL. The correlation is perfect across the
  five contexts and is the recorded trace identity (`TARGET_COMMITTED_DATA_VALUE_PRESENT`
  for R01; `MEMORY_RESPONSE → errant_commit` for R02–R05).

### (f) Defects / recommendation

See **A-09, A-10, A-11**.

**Recommendation: ADOPT (conditional on A-09 re-measurement for v2).**
Fault semantics preserved: one real violation report suppressed, no data mutation. Five
distinct in-main pairs available and four of five static sites are represented among the
five contexts (L1/L3/L4/L6/L8). Golden/oracle valid (host + 5/5 controls pass; 1 MASKED /
4 SDC with causal `load_complete`). Risk: low. The main residual is that the 11-total and
the 2+8+1 split were measured on the v1 ELF, not the v2/final binary.

---

## 4. Consolidated issue list

Classification: **A** code/hook defect, **B** workload/dynamic-context design,
**C** trace/propagation/oracle evidence, **D** Excel/seed/control/binary/runner.

### A-01 — FW02 "67 in-main forwarding events" is inflated by 7 — C (report/claim)
- Root cause: `observed=67` is the total over the whole run; ordinals 1–7 are pre-main
  stack/libc forwarding matches (K1 `0x7ffffefbd0`, K3 `0x496798`, K4/K5 `0x48fb70`,
  K6/K7 stack), ordinals 8–67 are the 60 in-main matches.
- Affected: `audit_v3_3_2/report/LSU_v3.3.2_Final_Acceptance_Report.md:74`; any prose
  that repeats "67 in-main". The ROI 8–67 (N=60) is itself correct.
- Fix: change the prose to "60 in-main (ordinals 8–67); 67 total = 7 pre-main + 60".
  No source change.
- Validation: `grep -h Vaddr audit_v3_3_2/roi/census_v332/FW02_w4v2_sweep_K*/lsq_fwd_injections.log`
  and the classification table in §1(c).
- Approval required: N. Regression risk: none.

### A-02 — FW02 eligible-stream length is run-dependent (67 vs 68) — B/C
- Root cause: a suppressed forwarding changes later timing; `FW02_w4v2_sweep_K*` runs at
  K19–K26 and K36–K38 report `observed=68`, all others `observed=67`. The five formal
  contexts R02/R03 also report 68. The extra event appears after the injected ordinal, so
  the prefix up to each selected ordinal (≤61) is stable, but the ROI tail ordinal 67 is
  not a deterministic constant, and the in-main count can be 60 or 61.
- Affected: FW02 ROI end 67 / N=60 in the frozen matrix; any claim that N=60 is
  run-invariant.
- Fix (source/matrix level): define FW02 ROI over the no-fault stream and record both
  "prefix-stable ordinals ≤61" and "N=60 (observed=67) / 61 (observed=68)". Do not select
  ordinals near the tail (none are today).
- Validation: rerun a count-only (probability 0.0) and a K20 fault; confirm 67/68.
- Approval required: Y (matrix methodology wording). Risk: low.

### A-03 — FW02 seeds are inert; contexts are ordinals, not independent samples — B/D
- Root cause: `f6_fw02` selection uses `f6_event_ordinal` only; the RNG/seed is not
  consulted on this path. R02–R05 use seeds 2129071279/1336081385/527667424/3622278636 yet
  produce sequence numbers/addresses byte-identical to the seed-2941542370 sweep.
- Affected: FW02 rows of the matrix/Excel (Seed column); the "five distinct contexts"
  rationale.
- Fix: document that the seed is inert for `f6_fw02`; distinctness comes from the ordinal
  (iteration index), and the five contexts are determinism replications of two static sites,
  not independent samples.
- Validation: compare `runs/FW02-R0x-fault/lsq_fwd_injections.log` with
  `census_v332/FW02_w4v2_sweep_K*/lsq_fwd_injections.log` (identical identities).
- Approval required: N. Risk: none.

### A-04 — FW02 census "all_suppress" is mislabeled and actually injects — D
- Root cause: `FW02_w4v2_all_suppress/run.log` command has `--max_faults 0
  --lsqfwd_event_ordinal 0 --probability 1.0`. In `CHAOSLSQFwd.cc:1034`, `max_faults==0`
  means unlimited and `f6_event_ordinal==0` means no ordinal filter, so the first event is
  suppressed (`faults_injected: 1`). The genuine observe-only run is the
  `--probability 0.0` run documented in `W4_v2_evidence.md §5`
  (`CHAOS_FW02_SUMMARY: observed=67 suppressed=0`).
- Affected: `audit_v3_3_2/roi/census_v332/FW02_w4v2_all_suppress/` label/semantics.
- Fix: rename or re-run with `--probability 0.0`; keep the existing 67 count (it agrees
  with the true observe-only run).
- Validation: rerun with probability 0.0 and confirm `suppressed=0 observed=67`.
- Approval required: N (results unchanged); Y if re-censused. Risk: none.

### A-05 — FW02 census provenance cites a different binary — D
- Root cause: `audit_v3_3_2/roi/LP01_FW02_census.md` states binary
  `a629b6b2…`; all 30 formal run summaries state `070d68a6…`. The sweep identities match
  the formal runs exactly, so the workload stream is binary-stable, but the census doc is
  stale relative to the final binary.
- Affected: `LP01_FW02_census.md §0`.
- Fix: update the provenance table to cite both binaries and state that the FW02
  ordinal→identity stream was reproduced identically on 070d68a6.
- Validation: diff the sweep and run logs (identities equal).
- Approval required: N. Risk: none.

### A-06 — RP01 watchdog is invisible to `parse_rp01_stdout` → summary says CRASH — D
- Root cause: `CHAOSLSQFwd::rp01Watchdog()` writes `CHAOS_RP01_WATCHDOG=EXPIRED …` only to
  `lsq_fwd_injections.log`, then `fatal()` exits 1. `tools/lsu_v332_matrix.py:140-155`
  scans `stdout.log`, so `summary.json` gets `rp01.watchdog=false` and a terminal derived as
  `CRASH`; `propagation/LSU_60Context_Causal_Propagation_Final.csv` and the readiness matrix
  correctly say `HANG_WATCHDOG`.
- Affected: all five `runs/RP01-R0x-fault/summary.json` (and therefore any downstream
  consumer of the summary); the CSV artifacts are already correct.
- Fix: also print the watchdog line to stdout (one `std::cout` in `rp01Watchdog()`), or make
  `parse_rp01_stdout` fall back to `lsq_fwd_injections.log`; recompute the summaries.
- Validation: `grep -c CHAOS_RP01_WATCHDOG runs/RP01-R01-fault/stdout.log` must be ≥1 and
  `summary.json` must read `rp01.watchdog=true`, terminal `HANG`.
- Approval required: Y (runner/source touch). Regression risk: low (log/evidence only).

### A-07 — RP01 five contexts are one static PC and one geometry — B
- Root cause: the workload has a single partial-overlap loop; all 255 in-main events are
  the same `ldur` at 0x400560 with the same 8B-store/4B-load+6 geometry. The five selected
  contexts are distinct dynamic instances (different seq/lq/tick) but do not exercise a
  different microarchitectural situation; all five outcomes are the same HANG.
- Affected: RP01 R01–R05 framing in the matrix ("five distinct contexts").
- Fix (optional): add a second partial-overlap loop with a different store/load PC and
  size/offset (e.g. 16B store + 8B load at +8, or a 4B store + 8B load) so the percentile
  contexts span ≥2 static geometries. If not changed, label the five as five determinism
  replications of one scenario.
- Validation: count-only stream shows ≥2 distinct load PCs in main.
- Approval required: Y (workload change). Risk: medium (new ELF/golden/ROI).

### A-08 — RP01 controls omit the injector, so `eligible=0` — D (note, not a defect)
- Root cause: control commands omit `--chaos_lsqfwd`; `rp01.eligible=0`. The count-only p1
  run is the separate observe-only evidence. The control is a valid golden-only control.
- Fix: documentation note; no change required.
- Approval required: N. Risk: none.

### A-09 — MD04 v2 count-only 11 is v1 provenance; v2 not re-measured on the final binary — C/D
- Root cause: `MD04_evidence_v2.md` says "Count-only on the final binary (070d68a6…):
  CHAOS_ELIGIBLE_COUNT=11", but the `p2` run is timestamped 18:00 (before the v2 ELF
  rebuild at 22:07 and before the final binary), and its `p2_K*` probes carry v1 PCs/addrs
  (`store_pc=0x4005f8 load_pc=0x4005fc addr=0x49d990`). The current ELF is
  `dd241c30…`, and the v2 formal runs (22:21–22:28) are the first v2 executions.
- Affected: the "11 = 2 libc + 8 main + 1 printf" decomposition and the ROI 3–10 rationale;
  ordinals 1,2,4,7,9,11 are not individually verified on v2.
- Fix: re-run `--chaos_md04 --md04_count_only --md04_event_ordinal 0` with the v2 ELF on
  `070d68a6`, record the binary SHA and the workload SHA, and confirm `CHAOS_ELIGIBLE_COUNT=11`
  and the 2/8/1 split (probe ordinals 1,2,11 at minimum).
- Validation: `lsq_fwd_injections.log`/`md04_injections.log` of the new run.
- Approval required: Y. Regression risk: low (measurement only; if it yields ≠11 the ROI
  must be recomputed).

### A-10 — MD04 baseline tolerance of the detected violations is not fully traced — C
- Root cause: the control has `lsq0.memOrderViolation = 12` and
  `iew.memOrderViolationEvents = 12` yet completes with the golden checksum; the fault run
  has 13. The `M5PanicFault` returned by `checkViolations` is therefore not raised on these
  baseline violations in this configuration. I did not find the exact reason (commit-time
  fault suppression vs. store re-execution) within the audit budget.
- Affected: the mechanism narrative "suppression of the violation report"; the observed
  SDC/MASKED outcomes are nonetheless real and correlate with `load_complete`.
- Fix: add a DPRINTF/trace on the `M5PanicFault` return and on the fault's commit-time
  handling, or document explicitly that baseline gem5 tolerates these (possible) violations.
- Validation: a single instrumented run showing which path consumes the fault.
- Approval required: N (investigation). Risk: low.

### A-11 — stale v1 MD04 evidence is not marked superseded — D
- Root cause: `audit_v3_3_2/workloads/MD04_evidence.md` describes the v1 ELF
  (`7820d67f…`, source `24e80596…`, golden `0x6f38c01e3ceacc74`, PCs 0x4005f8…) and sits
  next to `MD04_evidence_v2.md`. The `iter1_4loops_superseded` dir is labelled, but the v1
  evidence doc is not.
- Affected: anyone reading the evidence tree; the current v2 SHAs are
  `dd241c30… / 9b1f57a9… / 0x22be5ae3364d0c9f`.
- Fix: add a "SUPERSEDED by MD04_evidence_v2.md" banner to the v1 doc (or move it under a
  `_superseded/` path).
- Validation: grep the header.
- Approval required: N. Risk: none.

---

## 5. Bottom line

- **FW02 (`sq_forward_w4v2`): ADOPT (conditional).** The workload genuinely forms in-main
  store→load forwarding pairs (full-overlap 0x400530/0x400538, 0x40061c/0x400620,
  0x400654/0x400658; sub-width 8B-store/4B-load at +2 at 0x400570/0x400574) and the frozen
  W4 does not (zero data loads). The real in-main eligible count is **60**, not 67 (the
  67 total includes 7 pre-main stack/libc forwards); ROI 8–67 (N=60) and ordinals
  13/25/37/49/61 are arithmetically correct and match every run `command.txt`. Golden
  `1f4cbf14327717df` is reproduced by the ELF, all five controls pass, 4/5 faults SDC and
  the R03 MASKED is mechanism-consistent (`memory_path=1, replay_count=0`).
- **RP01 (`replay_partial_v332`): ADOPT (conditional).** True 2-byte partial-range overlap
  (store 0x40055c, load `ldur` 0x400560 at +6), 255 in-main eligible events verified by a
  count-only run, ROI 1–255 and ordinals 26/77/128/179/230 correct. The five contexts are
  distinct dynamic executions but the same static PC/geometry, and all five faults are an
  in-simulator-watchdog HANG — the source-documented expected terminal, not SDC. The
  committed `summary.json` wrongly records `watchdog=false`/CRASH because the watchdog line
  goes only to `lsq_fwd_injections.log` (A-06); the propagation CSV is correct.
- **MD04 (`md04_violations_v332`): ADOPT (conditional).** Eight in-main 8B-store→younger-load
  pairs exist statically at the current PCs; the five selected ordinals 3/5/6/8/10 map to
  five *distinct real pairs* (L1/L3/L4/L6/L8), not counters. Golden `0x22be5ae3364d0c9f`
  is reproduced, all five controls pass, R01 is MASKED with `load_complete=1`, R02–R05 are
  SDC with `load_complete=0`. The 11-total and the 2+8+1 libc/main split are v1-provenance
  only (A-09): the count-only was not re-run on the v2 ELF/final binary, although all eight
  static pairs and the five chosen ordinals are verified on v2.

No candidate has a rebuilt-ELF mismatch: all three committed ELFs reproduce byte-identically
from their committed sources, and all 30 run summaries name the final binary `070d68a6…`.

## 6. Could not verify

- **FW02 R03's exact benign-miss mechanism**: the trace proves `memory_path=1,
  replay_count=0` and the oracle passes, but the store-drain/visibility state that made the
  memory read return the correct value is not instrumented. The MASKED classification is
  consistent with the mechanism, not proven down to the cache event.
- **FW02 run-dependent tail (67 vs 68)**: I can see the count change, but I did not trace
  which dynamic load is the extra event in the `observed=68` runs (it is after the injected
  ordinal, so the selected contexts are unaffected).
- **MD04 baseline panic path**: why the 12 detected baseline violations (`memOrderViolation
  =12`) do not raise `M5PanicFault` in the control. The fault outcomes are real and causal,
  but the baseline tolerance mechanism is not fully traced (A-10).
- **MD04 v2 total = 11**: not directly re-measured on the v2 ELF; only the v1 count (11) and
  the v2 five selected ordinals (all in main) are verified (A-09).
- **RP01 eligible stream beyond ordinal 230 on the fault path**: the fault runs stop at the
  injected ordinal (watchdog), so N=255 is taken from the count-only p1 run, not from a
  fault run. The count-only p1 stream is deterministic (p2 byte-identical) and is the
  correct evidence.
- **The frozen-W4 original gem5 evidence**: I verified the frozen ELF statically (zero data
  loads in `main`) and its golden, but did not run a gem5 census on the frozen W4 (Phase-1
  forbids gem5 runs); the "no forwarding" conclusion for the frozen W4 is static + the
  `W4_v2_evidence.md` prose.

---

### Appendix — commands actually run (representative)

```
sha256sum build/ARM/gem5.opt
objdump -d --disassemble=main workloads/directed/sq_forward_w4v2
objdump -d --disassemble=main workloads/directed/replay_partial_v332
objdump -d --no-show-raw-insn --disassemble=main workloads/directed/md04_violations_v332
objdump -d --disassemble=main docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_forward
readelf -sW workloads/directed/replay_partial_v332 | grep -E ' buf$| main$'
gcc -O2 -static -o /tmp/provcheck/<elf> workloads/directed/<src>.c     # byte-identical SHAs
workloads/directed/sq_forward_w4v2 ; workloads/directed/replay_partial_v332 ; workloads/directed/md04_violations_v332
python3 parse of audit_v3_3_2/roi/census_v332/FW02_w4v2_sweep_K*/lsq_fwd_injections.log
python3 parse of audit_v3_3_2/workloads/RP01_runs/p1/stdout.log (260 total / 255 main)
python3 parse of audit_v3_3_2/runs/{FW02,RP01,MD04}-R0*/summary.json, oracle.log, md04_injections.log, lsq_fwd_injections.log
grep -c 'CHAOS_RP01_WATCHDOG' audit_v3_3_2/runs/RP01-R01-fault/{stdout.log,lsq_fwd_injections.log}
```
