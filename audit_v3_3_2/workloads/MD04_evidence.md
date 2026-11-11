# MD04 context workload evidence — `md04_violations_v332` (LSU v3.3.2 / P0-3)

Status: **ENOUGH — 8 eligible store→younger-load violation pairs inside `main`**
(requirement: >= 5). All numbers below are copied from real command output in this
worktree; nothing is inferred or fabricated.

- Workload branch/worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
- gem5 binary: `build/ARM/gem5.opt` sha256 prefix `d3807fbef631354a41d9`
  (1149087848 bytes, mtime 2026-11-11 12:33)
- Date: 2026-11-11

## 1. Artifacts

| Artifact | SHA-256 |
|---|---|
| `workloads/directed/md04_violations_v332.c` | `24e80596b22a8f88b913c4a07d487fb079b63d7e94c732f421c3e63158c0b16b` |
| `workloads/directed/md04_violations_v332` (ELF) | `7820d67fc8d45df8dc940e0b5bbd6c20fd03dd80d184bd0dfae7ea3d2763fa56` |
| `workloads/directed/md04_violations_v332.golden` | `c207bee765bacfd17b84b5c8a4147b99e05cf0d6015840d4b80416bec8baf59f` |
| `workloads/directed/compile_md04_violations_v332.sh` | (build script) |

Build (host is native aarch64):

```
$ workloads/directed/compile_md04_violations_v332.sh
7820d67fc8d45df8dc940e0b5bbd6c20fd03dd80d184bd0dfae7ea3d2763fa56  md04_violations_v332
24e80596b22a8f88b913c4a07d487fb079b63d7e94c732f421c3e63158c0b16b  md04_violations_v332.c
```

```
$ file workloads/directed/md04_violations_v332
ELF 64-bit LSB executable, ARM aarch64, version 1 (GNU/Linux), statically linked,
BuildID[sha1]=2a7075cc3d53d2f586a90af2f01fa3b7b24005dc, for GNU/Linux 3.7.0, not stripped
```

Host oracle (real host execution):

```
$ workloads/directed/md04_violations_v332
checksum=0x6f38c01e3ceacc74
```

`md04_violations_v332.golden` contains exactly `0x6f38c01e3ceacc74`.

## 2. Why this workload produces violations (source-verified mechanism)

1. `LSQUnit::read()` (`CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1720-1731`) scans the store
   queue for forwarding but **skips any older store whose `SQEntry::size()` is 0**.
   `SQEntry::size()` is set only in `LSQUnit::write()` at line 2107, i.e. when the
   store actually executes.
2. Therefore a younger load can execute past an older, not-yet-executed same-address
   store. When that store later executes,
   `LSQUnit::executeStore()` → `checkViolations()` (line 919, store branch
   lines 669-708) sees the younger load with a valid effective address and reports
   the store→younger-load violation. This is the MD04 hook site
   (`CHAOSMD04::maybeSkipViolation`, `lsq_unit.cc:677-690`).
3. To make the race deterministic instead of accidental, every loop makes the
   **store data depend on a load from a 1 MiB array** (`src_big`, long latency)
   while the **younger load address depends only on the loop index**. The store
   executes late; the younger load executes early.
4. The StoreSet memory-dependence predictor is trained by
   `IEW -> InstructionQueue::violation -> MemDepUnit::violation -> StoreSet::violation`
   (`iew.cc:1334`, `inst_queue.cc:1401-1405`, `mem_dep_unit.cc:573-580`,
   `store_set.cc:113`). After the first violation of a given (store PC, load PC)
   pair, that pair is predicted dependent and the load waits for the store, so a
   pair contributes about **one** eligible event. Consequently the eligible count
   is driven by the number of **distinct (store PC, load PC) pairs**, not by the
   iteration count — which is exactly why the workload defines eight distinct
   store/load loops instead of one loop with many iterations.

MD04 eligibility (`md04_rules.hh`, MD04-ELIG-v1, frozen v3.2.7) requires: store size
exactly 8, load size >= 8, real byte overlap, the same shifted-range predicate as
`checkViolations`, and load.seq > store.seq. All eight pairs below satisfy it.

## 3. `main` range and disassembly (store/load PCs and sizes)

`main` = `[0x4004f0, 0x4009bf]`; the next symbol is `_start` at `0x4009c0`:

```
$ nm -n workloads/directed/md04_violations_v332 | awk '$3=="main"{print; getline; print "next: "$0}'
00000000004004f0 T main
next: 00000000004009c0 T _start
```

Quoted `objdump -d --no-show-raw-insn` lines (all inside `main`):

```
  4005f8:	str	x4, [x5, x2, lsl #3]      <- L1 store 8B
  4005fc:	ldr	x4, [x5, x2, lsl #3]      <- L1 load  8B, same address
  400650:	str	x2, [x8, x4, lsl #3]      <- L2 store 8B at slot i+1
  400654:	ldp	x2, x3, [x7], #16         <- L2 load 16B at slot i
  4006b0:	stur	x4, [x2, #4]              <- L3 store 8B at +4 (unaligned)
  4006b4:	ldr	x4, [x2], #16             <- L3 load 8B at +0 (4B overlap)
  4006fc:	str	x6, [x10, x4, lsl #3]     <- L4 store 8B at dynamic index
  400700:	ldr	x4, [x10, x4, lsl #3]     <- L4 load 8B, same address
  400758:	str	x2, [x8, x6, lsl #3]      <- L5 store 8B
  40075c:	ldp	x2, x3, [x4]              <- L5 load 16B covering the store
  4007b4:	str	x6, [x9, x4, lsl #3]      <- L6 store 8B at dynamic index
  4007b8:	ldr	x4, [x9, x4, lsl #3]      <- L6 load 8B, same address
  400810:	stur	x4, [x2, #-6]             <- L7 store 8B at +2 (unaligned)
  400814:	ldr	x4, [x2], #16             <- L7 load 8B at +8 (2B overlap)
  400860:	str	x2, [x5, x4, lsl #3]      <- L8 store 8B at slot i+1
  400864:	ldp	x2, x3, [x7]              <- L8 load 16B at slot i
```

`nm -n` symbol containment check for every violation PC (real output):

```
0x4005f8 -> main   0x4005fc -> main   0x400650 -> main   0x400654 -> main
0x4006b0 -> main   0x4006b4 -> main   0x4006fc -> main   0x400700 -> main
0x400758 -> main   0x40075c -> main   0x4007b4 -> main   0x4007b8 -> main
0x400810 -> main   0x400814 -> main   0x400860 -> main   0x400864 -> main
```

## 4. Exact gem5 commands

Env: `cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`;
`W=$PWD/workloads/directed/md04_violations_v332`; one gem5 process at a time.

**(a) Count-only, no ROI gate (raw eligibility, suggested flags):**

```
build/ARM/gem5.opt --outdir=audit_v3_3_2/workloads/MD04_runs/p2 \
  configs/se/lsu_proxy.py --cmd=$W \
  --cpu O3 --variant B0 --probability 1.0 \
  --chaos_md04 --md04_first_clock 0 --md04_max_faults 0 \
  --md04_probability 1.0 --md04_rng_seed 1 --md04_event_ordinal 0 --md04_count_only
```

`audit_v3_3_2/workloads/MD04_runs/p2/md04_injections.log`:

```
CHAOS_ELIGIBLE_COUNT=11
CHAOS_MD04_TARGET_STATUS=NOT_TRIGGERED eligible_count=11 target_ordinal=0
```

stdout: `checksum=0x6f38c01e3ceacc74` (matches the host oracle; count-only returns
false before the injection block, so no fault is applied).

The same command with the propagation flags used by the v3.3.1 census
(`--chaos_propagation --prop_trace_file prop_trace.csv.gz`) gives the identical
`CHAOS_ELIGIBLE_COUNT=11` and checksum (`p2_prop/`), so the count is invariant
under the full pipeline mount.

**(b) Count-only, ROI gate `--md04_first_clock 50000` (cycles):**

```
build/ARM/gem5.opt --outdir=audit_v3_3_2/workloads/MD04_runs/p2_roi \
  configs/se/lsu_proxy.py --cmd=$W \
  --cpu O3 --variant B0 --probability 1.0 \
  --chaos_md04 --md04_first_clock 50000 --md04_max_faults 0 \
  --md04_probability 1.0 --md04_rng_seed 1 --md04_event_ordinal 0 --md04_count_only
```

```
CHAOS_ELIGIBLE_COUNT=9
```

The gate excludes exactly the two libc-startup pairs (see §6). Probes
`p2_roi_K1..K8` confirm ordinals 1..8 are the eight in-main pairs, and
`p2_roi_K9` confirms ordinal 9 is the libc printf pair
(`load_pc=0x428cdc`, `store_pc=0x428dc0`, `_IO_new_file_overflow`). Checksum
unchanged: `0x6f38c01e3ceacc74`.

**(c) Injection probes (census/proof only, not used to select contexts):**

```
build/ARM/gem5.opt --outdir=audit_v3_3_2/workloads/MD04_runs/p2_roi_K<k> \
  configs/se/lsu_proxy.py --cmd=$W \
  --cpu O3 --variant B0 --probability 1.0 \
  --chaos_md04 --md04_first_clock 50000 --md04_max_faults 1 \
  --md04_probability 1.0 --md04_rng_seed 1 --md04_event_ordinal <k>
```

for k = 1..8 (all `CHAOS_MD04_TARGET_STATUS=INJECTED count=1`). The ungated probes
`p2_K1..p2_K11` use `--md04_first_clock 0` and the same ordinal.

## 5. First five in-main violation identities (ROI-gated ordinals 1..5)

Verbatim from `p2_roi_K1..K5/md04_injections.log`:

| Ord | Tick | load_pc | store_pc | load_seq | store_seq | load addr/size | store addr/size | sq id/gen | lq id/gen | load_complete |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 286869660 | 0x4005fc | 0x4005f8 | 854643 | 854642 | 0x49d990 / 8 | 0x49d990 / 8 | 146348/146713 | 750/1223 | 1 |
| 2 | 344226960 | 0x400654 | 0x400650 | 929467 | 929466 | 0x49b990 / 16 | 0x49b998 / 8 | 154540/154914 | 17134/17627 | 0 |
| 3 | 371213150 | 0x4006b4 | 0x4006b0 | 975923 | 975922 | 0x499990 / 8 | 0x499994 / 8 | 158636/159019 | 25326/25838 | 0 |
| 4 | 406422555 | 0x400700 | 0x4006fc | 1014076 | 1014075 | 0x4979c8 / 8 | 0x4979c8 / 8 | 162724/163114 | 33503/34029 | 0 |
| 5 | 465690225 | 0x40075c | 0x400758 | 1097361 | 1097359 | 0x49b990 / 16 | 0x49b990 / 8 | 170916/171311 | 58078/58627 | 0 |

All five have `address_modified=0, size_modified=0, data_modified=0` and
`faults_injected: 1`. Ordinals 6..8 (also in main):

| Ord | Tick | load_pc | store_pc | load_seq | store_seq | load addr/size | store addr/size |
|---|---|---|---|---|---|---|---|
| 6 | 545639325 | 0x4007b8 | 0x4007b4 | 1196965 | 1196964 | 0x4939e8 / 8 | 0x4939e8 / 8 |
| 7 | 599122755 | 0x400814 | 0x400810 | 1280139 | 1280138 | 0x499998 / 8 | 0x499992 / 8 |
| 8 | 635446735 | 0x400864 | 0x400860 | 1318322 | 1318320 | 0x49d990 / 16 | 0x49d998 / 8 |

The eight pairs have eight distinct (store PC, load PC) combinations and distinct
dynamic sequence numbers. Real-byte-overlap check: ord 3 store
`[0x499994,0x49999b]` vs load `[0x499990,0x499997]` overlap 4 bytes; ord 7 store
`[0x499992,0x499999]` vs load `[0x499998,0x49999f]` overlap 2 bytes; ords 2/5/8 are
16B loads covering the 8B store; ords 1/4/6 are exact same-address 8B/8B pairs.

## 6. Full-census ordering without the ROI gate (honest accounting)

With `--md04_first_clock 0` the 11 eligible events are, in order (from
`p2_K1..K11`):

| Ord | load_pc / store_pc | enclosing symbol | in main? |
|---|---|---|---|
| 1 | 0x4117d0 / 0x4117c4 | `_dl_aux_init` | no (libc startup) |
| 2 | 0x401198 / 0x410390 | `__libc_setup_tls` / `_dl_tls_static_surplus_init` | no (libc startup) |
| 3 | 0x4005fc / 0x4005f8 | `main` L1 | **yes** |
| 4 | 0x400654 / 0x400650 | `main` L2 | **yes** |
| 5 | 0x4006b4 / 0x4006b0 | `main` L3 | **yes** |
| 6 | 0x400700 / 0x4006fc | `main` L4 | **yes** |
| 7 | 0x40075c / 0x400758 | `main` L5 | **yes** |
| 8 | 0x4007b8 / 0x4007b4 | `main` L6 | **yes** |
| 9 | 0x400814 / 0x400810 | `main` L7 | **yes** |
| 10 | 0x400864 / 0x400860 | `main` L8 | **yes** |
| 11 | 0x428cdc / 0x428dc0 | `_IO_new_file_overflow` | no (libc printf) |

So: **11 eligible pairs total, 8 inside `main`**, 2 in libc process startup, 1 in
libc `printf`. The two startup pairs are a property of static glibc startup on
this platform (they exist for any dynamically-loaded-target-independent SE binary
in this config), not of this workload. The ROI gate `--md04_first_clock 50000`
(cycles; the startup pairs occur at ticks 735350 and 3364515) is a fixed boundary
that removes them so that the first eligible events of a formal run are in `main`.
It is not outcome-based selection: no main pair is excluded by this boundary.

## 7. Determinism

A byte-for-byte repeat of command (a) (`p2_repeat/`) gives
`CHAOS_ELIGIBLE_COUNT=11` and `checksum=0x6f38c01e3ceacc74`, identical to `p2/`.
The per-ordinal injection probes reproduce the same Tick/pc/seq identities as the
count-only census (ordinals 3..10 of the ungated run equal ordinals 1..8 of the
gated run).

## 8. Iteration history

- **Iteration 1 (superseded):** the first build had four in-main loops and gave
  `CHAOS_ELIGIBLE_COUNT=7` (2 libc startup + 4 in main + 1 libc printf). Its raw
  probe directories are retained under
  `audit_v3_3_2/workloads/MD04_runs/iter1_4loops_superseded*`; their PCs refer to
  that pre-extension build (`main` then ended at `0x4007ff`) and are **not** the
  final artifact. The final source adds loops L5-L8.
- **Iteration 2 (final):** eight in-main pairs, 11 total, proof above.

## 9. Honest limitations

- The eligible-event count is bounded by the number of distinct
  (store PC, load PC) pairs because the StoreSet predictor trains a pair after its
  first violation (source path quoted in §2). This is a fixed property of the B0
  O3 memory-dependence machinery, not a workload defect; the workload therefore
  exposes eight distinct pairs rather than thousands of repeats.
- Fault-on runs (max_faults=1) are legal probes only. Their architectural
  checksum may or may not change (e.g. `p2_roi_K1` still prints
  `0x6f38c01e3ceacc74`, while `p2_roi_K2` prints `0x55d6afcabec97835`); no SDC
  claim is made here. The evidence is the `md04_injections.log` identity plus the
  `address_modified=0, size_modified=0, data_modified=0` fields.
- `--variant B0` sets `LSQDepCheckShift=0` (printed by `lsu_proxy.py`), so the
  shifted-range predicate equals the raw byte-range predicate. MD04-ELIG-v1 still
  requires a real byte overlap, which every pair above has; no different-address
  same-block pair is counted.
- The two libc-startup pairs and the libc-printf pair are real eligible pairs of
  the same program. They are reported, not hidden; the ROI gate only removes the
  startup pair when a formal run needs main-only ordinals.
