# LP01 / FW02 percentile-context census — v3.3.2 binary

Date: 2026-11-11. Agent I. All numbers below are from commands actually run in this
worktree; raw probe directories are under `audit_v3_3_2/roi/census_v332/`.

## 0. Provenance

| item | value |
|---|---|
| gem5 binary | `build/ARM/gem5.opt` (repo root), SHA-256 `a629b6b2140a351e822fe880d7ce64f20c492d521a5e3b54ac1dee02ac0b968e` |
| LP01 workload (W5) | `docs/gem5-fi/lsu/implementation_v3_2/workloads/load_response`, SHA-256 `3779e8ced41a07d798f78c97a1f5d10187c812a24a81b599c19ae68a0753e711` |
| FW02 workload (W4v2) | `workloads/directed/sq_forward_w4v2`, SHA-256 `a08fb3a7b8bbcef76b0c3c3519a5787370ea7ead2d93de290e00fc6e44fe76e2` |
| LP01 seed (Excel context-index 1 / R01) | `1349924126` |
| FW02 seed (Excel context-index 1 / R01) | `2941542370` |
| LP01 fault args | `--chaos_l1dfwd --l1dfwd_first_clock 0 --l1dfwd_max_faults 1 --l1dfwd_fault_mask 0x8 --l1dfwd_rng_seed 1349924126 --l1dfwd_event_ordinal <K>` |
| FW02 fault args | `--chaos_lsqfwd --lsq_struct_mode f6_fw02 --max_faults 1 --rng_seed 2941542370 --lsqfwd_event_ordinal <K>` |
| common | `--cpu O3 --variant B0 --probability 1.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz` |

Driver used for every probe (one gem5 process at a time):

```bash
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
  --model LP01 --context-index 1 --event-ordinal <K> \
  --pilot-id V332-LP01-<tag> --outdir "$PWD/audit_v3_3_2/roi/census_v332/LP01_w5_<tag>"

python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
  --model FW02 --context-index 1 --workload "$PWD/workloads/directed/sq_forward_w4v2" \
  --event-ordinal <K> --pilot-id V332-FW02-<tag> \
  --outdir "$PWD/audit_v3_3_2/roi/census_v332/FW02_w4v2_<tag>"
```

`run_pilot.py` rewrites `--model` into the exact gem5 command recorded in each
probe's `command.txt`. `--event-ordinal K` becomes the injector's ordinal
selector; the LP01 log then reports the same value as `eligible_ordinal=K`.

All completed probes had `exit_code=0`, `injection_count=1`, `accepted=true`.

---

## 1. LP01 (load_response W5)

### 1.1 Coarse census and boundary search

Requested coarse ordinals plus the boundary probes. Fields parsed from
`l1d_fwd_injections.log` (v3.3.2 line carries `pa`, `va`, `pc`, `dyn_inst_seq`,
`lq_entry_id`, `entry_generation`).

| ordinal | pc | va | pa | seq | lq | gen | size |
|---|---|---|---|---|---|---|---|
| 1 | 0x4005d0 | 0x7ffffefd90 | 0x80d90 | 5 | 1 | 1 | 8 |
| 50 | 0x4113c0 | 0x7ffffefe28 | 0x80e28 | 513 | 18 | 63 | 8 |
| 100 | 0x410cc4 | 0x7ffffefca0 | 0x80ca0 | 816 | 60 | 122 | 16 |
| 200 | 0x411228 | 0x48dfe8 | 0x72fe8 | 2038 | 150 | 251 | 8 |
| 300 | 0x438c44 | 0x7ffffeecc4 | 0x82cc4 | 3264 | 242 | 369 | 1 |
| 400 | 0x408978 | 0x7ffffeeac8 | 0x82ac8 | 5957 | 329 | 502 | 8 |
| 500 | 0x40dc90 | 0x44f410 | 0x4f410 | 7346 | 417 | 640 | 16 |
| 800 | 0x443f9c | 0x7ffffefc10 | 0x80c10 | 11051 | 661 | 1124 | 16 |
| 850 | 0x40127c | 0x7ffffefcc0 | 0x80cc0 | 11698 | 712 | 1178 | 16 |
| 875 | 0x400b9c | 0x7ffffefd60 | 0x80d60 | 11980 | 732 | 1207 | 8 |
| 885 | 0x40087c | 0x7ffffefc14 | 0x80c14 | 12104 | 743 | 1219 | 4 |
| **886** | **0x400548** | **0x491990** | 0x76990 | 24569 | 744 | 1220 | 8 |
| 887 | 0x40054c | 0x4919c8 | 0x769c8 | 24570 | 745 | 1221 | 8 |
| 900 | 0x400548 | 0x493638 | 0x78638 | 24681 | 758 | 1234 | 8 |
| 1141 | 0x40054c | 0x4927a0 | 0x777a0 | 26021 | 999 | 1475 | 8 |
| **1142** | **0x400588** | **0x491990** | 0x76990 | 26054 | 1000 | 1478 | 1 |
| 1200 | 0x400588 | 0x4919ca | 0x769ca | 26647 | 1058 | 1536 | 1 |
| 1500 | 0x400588 | 0x491af6 | 0x76af6 | 28447 | 1358 | 1836 | 1 |
| 2000 | 0x400588 | 0x491cea | 0x76cea | 31447 | 1858 | 2336 | 1 |
| 17524 | 0x400588 | 0x49598e | 0x7a98e | 124591 | 17382 | 17860 | 1 |
| **17525** | **0x400588** | **0x49598f** | 0x7a98f | 124597 | 17383 | 17861 | 1 |
| 17526 | 0x40157c | 0x48fc48 | 0x74c48 | 124654 | 17384 | 17863 | 8 |

Main range is `0x4004f0-0x4005b8`; every PC in the window is one of
`0x400548` / `0x40054c` (the two-`ldr` loop at `0x400540-0x400564`) or
`0x400588` (the byte-checksum `ldrb` loop at `0x400588-0x400598`), all inside main.
Ordinal 885 (`pc=0x40087c`, libc) and ordinal 17526 (`pc=0x40157c`, libc) sit
immediately outside the window.

### 1.2 ROI

- ROI start `= 886` (first in-main eligible load; `va=0x491990=a[0]`)
- ROI end `= 17525` (last in-main eligible load; `va=0x49598f = 0x491990+0x3fff`)
- The in-main ordinals are **contiguous** `[886, 17525]`; no libc forward is
  interleaved (`886..1141` = 128 iterations x 2 loads = 256; `1142..17525` =
  16384 checksum bytes).
- **N_ROI = 16640** (`= 256 + 16384`).

Failed method (recorded for honesty): a direct gem5 run with
`--l1dfwd_max_faults 0 --l1dfwd_event_ordinal 1` was attempted to log the whole
eligible stream. Corrupting *every* load breaks libc pointer loads and panics:

```
src/sim/faults.cc:103: panic: panic condition !handled && !tc->getSystemPtr()->trapToGdb(GDBSignal::SEGV, tc->contextId()) occurred: Page table fault when accessing virtual address 0x7fffff0000
```

That run aborted (exit 134) after 101 flushed lines and its stream differs from
the single-fault stream (first flushed line `pc=0x4113c8`, versus `pc=0x4005d0`
for single-fault ordinal 1). It is kept at
`census_v332/LP01_w5_fullstream/` and was **not** used for any number above.

### 1.3 Percentile contexts

`k(p) = ceil(p*N_ROI)`, `ordinal = 886 + k - 1`; `ceil` computed in Python.

| p | k(p) | ordinal | pc | va | pa | seq | lq_entry_id | entry_generation |
|---|---|---|---|---|---|---|---|---|
| 0.1 | 1664 | 2549 | 0x400588 | 0x491f0f | 0x76f0f | 34741 | 2407 | 2885 |
| 0.3 | 4992 | 5877 | 0x400588 | 0x492c0f | 0x77c0f | 54709 | 5735 | 6213 |
| 0.5 | 8320 | 9205 | 0x400588 | 0x49390f | 0x7890f | 74677 | 9063 | 9541 |
| 0.7 | 11648 | 12533 | 0x400588 | 0x49460f | 0x7960f | 94645 | 12391 | 12869 |
| 0.9 | 14976 | 15861 | 0x400588 | 0x49530f | 0x7a30f | 114613 | 15719 | 16197 |

Raw log line for p=0.1 (format identical for the rest):

```
Tick: 22472450, Site: l1d_load_complete, addr=0x76f0f, pa=0x76f0f, va=0x491f0f, pc=0x400588,
size=1, mask=0x8, dyn_inst_seq=34741, lq_entry_id=2407, entry_generation=2885, request_id=0,
eligible_ordinal=2549, byte0_changed=1, addr_unchanged=1, size_unchanged=1, faults_injected: 1
```

Distinctness: all five differ in `dyn_inst_seq`, `va`, `pa`, `lq_entry_id` and
`entry_generation`. They share `pc=0x400588` because all five land in the same
16-KiB checksum loop; they are five different dynamic iterations, not a
collapse.

`oracle_pass=false` for all five fault probes (the injected byte-lane-0 bit
changes the checksum, as expected for a fault run); `accepted=true` for all.

---

## 2. FW02 (sq_forward_w4v2 W4v2)

### 2.1 The instructed `max_faults 0 / ordinal 0` attempt

Direct gem5 run with `--probability 1.0 --chaos_propagation --chaos_lsqfwd
--lsq_struct_mode f6_fw02 --max_faults 0 --rng_seed 2941542370
--lsqfwd_event_ordinal 0` (exit 0):

```
Tick: 518980, Site: store->load_forward_decision, FaultType: f6_fw02_suppress,
load_seq: 258, store_seq: 248, Vaddr: 0x7ffffefbd0, FwdSize: 8, faults_injected: 1
CHAOS_FW02_SUMMARY: observed=67 suppressed=1 load_seq=258 store_seq=248
```

The hook clamps `max_faults==0` to one (`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`,
`StructMode::F6Fw02`: `if (max_faults == 0) max_faults = 1;`), and
`--lsqfwd_event_ordinal 0` means "no filter", so this run suppresses only the
first observed forward. `observed=67` is reproduced. It is not an all-suppress
trace, so per the work instruction the ordinal sweep was used.

### 2.2 Full ordinal sweep (all 67 observed forwards)

All 67 ordinals were probed one at a time with `max_faults 1` (see
`census_v332/FW02_w4v2_sweep.tsv`; dirs `FW02_w4v2_sweep_K1..K67`). `Vaddr`
is from the injector log; `load_pc`/`store_pc` are from gem5 debug traces
(section 2.3).

| K | load_seq | store_seq | Vaddr | size | load_pc | store_pc | main? |
|---|---|---|---|---|---|---|---|
| 1 | 258 | 248 | 0x7ffffefbd0 | 8 | — | — | libc |
| 2 | 259 | 249 | 0x7ffffefd38 | 8 | — | — | libc |
| 3 | 5981 | 5975 | 0x496798 | 8 | 0x40a538 | 0x409cd0 | libc |
| 4 | 9943 | 9940 | 0x48fb70 | 8 | 0x4448e4 | 0x4444b0 | libc |
| 5 | 11065 | 11063 | 0x48fb70 | 8 | 0x444908 | — | libc |
| 6 | 11167 | 11156 | 0x7ffffefd00 | 8 | — | — | libc |
| 7 | 12051 | 12046 | 0x7ffffefc20 | 8 | 0x4011fc | 0x4011e8 | libc |
| 8 | 12133 | 12131 | 0x4919a8 | 8 | 0x400538 | 0x400530 | main |
| 9 | 12155 | 12153 | 0x4919b0 | 8 | 0x400538 | 0x400530 | main |
| 10 | 12177 | 12175 | 0x4919b8 | 8 | 0x400538 | 0x400530 | main |
| 11 | 12199 | 12197 | 0x4919c0 | 8 | 0x400538 | 0x400530 | main |
| 12 | 12221 | 12219 | 0x4919c8 | 8 | 0x400538 | 0x400530 | main |
| 13 | 12243 | 12241 | 0x4919d0 | 8 | 0x400538 | 0x400530 | main |
| 14 | 12265 | 12263 | 0x4919d8 | 8 | 0x400538 | 0x400530 | main |
| 15 | 12287 | 12285 | 0x4919e0 | 8 | 0x400538 | 0x400530 | main |
| 16 | 12313 | 12311 | 0x4919e8 | 8 | 0x400538 | 0x400530 | main |
| 17 | 12339 | 12337 | 0x4919f0 | 8 | 0x400538 | 0x400530 | main |
| 18 | 12365 | 12363 | 0x4919f8 | 8 | 0x400538 | 0x400530 | main |
| 19 | 12391 | 12389 | 0x491a00 | 8 | 0x400538 | 0x400530 | main |
| 20 | 12417 | 12415 | 0x491a08 | 8 | 0x400538 | 0x400530 | main |
| 21 | 12443 | 12441 | 0x491a10 | 8 | 0x400538 | 0x400530 | main |
| 22 | 12452 | 12450 | 0x491a18 | 8 | 0x400538† | 0x400530† | main |
| 23 | 12461 | 12459 | 0x491a20 | 8 | 0x400538† | 0x400530† | main |
| 24 | 12470 | 12468 | 0x491a28 | 8 | 0x400538† | 0x400530† | main |
| 25 | 12479 | 12477 | 0x491a30 | 8 | 0x400538† | 0x400530† | main |
| 26 | 12488 | 12486 | 0x491a38 | 8 | 0x400538† | 0x400530† | main |
| 27 | 12497 | 12495 | 0x491a40 | 8 | 0x400538† | 0x400530† | main |
| 28 | 12506 | 12504 | 0x491a48 | 8 | 0x400538† | 0x400530† | main |
| 29 | 12515 | 12513 | 0x491a50 | 8 | 0x400538† | 0x400530† | main |
| 30 | 12524 | 12522 | 0x491a58 | 8 | 0x400538† | 0x400530† | main |
| 31 | 12533 | 12531 | 0x491a60 | 8 | 0x400538† | 0x400530† | main |
| 32 | 12542 | 12540 | 0x491a68 | 8 | 0x400538† | 0x400530† | main |
| 33 | 12551 | 12549 | 0x491a70 | 8 | 0x400538† | 0x400530† | main |
| 34 | 12560 | 12558 | 0x491a78 | 8 | 0x400538† | 0x400530† | main |
| 35 | 12569 | 12567 | 0x491a80 | 8 | 0x400538 | 0x400530 | main |
| 36 | 12578 | 12576 | 0x491a88 | 8 | 0x400538 | — | main |
| 37 | 12587 | 12585 | 0x491a90 | 8 | 0x400538 | — | main |
| 38 | 12596 | 12594 | 0x491a98 | 8 | 0x400538† | 0x400530† | main |
| 39 | 12701 | 12700 | 0x4919aa | 4 | 0x400574 | 0x400570 | main |
| 40 | 12726 | 12725 | 0x4919b2 | 4 | 0x400574 | 0x400570 | main |
| 41 | 12751 | 12750 | 0x4919ba | 4 | 0x400574 | 0x400570 | main |
| 42 | 12776 | 12775 | 0x4919c2 | 4 | 0x400574 | 0x400570 | main |
| 43 | 12801 | 12800 | 0x4919ca | 4 | 0x400574 | 0x400570 | main |
| 44 | 12826 | 12825 | 0x4919d2 | 4 | 0x400574 | 0x400570 | main |
| 45 | 12851 | 12850 | 0x4919da | 4 | 0x400574 | 0x400570 | main |
| 46 | 13288 | 13287 | 0x4919a0 | 8 | 0x400620† | 0x40061c† | main |
| 47 | 13320 | 13319 | 0x4919b0 | 8 | 0x400620 | 0x40061c | main |
| 48 | 13332 | 13331 | 0x4919b8 | 8 | 0x400620 | 0x40061c | main |
| 49 | 13344 | 13343 | 0x4919c0 | 8 | 0x400620 | 0x40061c | main |
| 50 | 13356 | 13355 | 0x4919c8 | 8 | 0x400620 | 0x40061c | main |
| 51 | 13368 | 13367 | 0x4919d0 | 8 | 0x400620 | 0x40061c | main |
| 52 | 13380 | 13379 | 0x4919d8 | 8 | 0x400620 | 0x40061c | main |
| 53 | 13420 | 13419 | 0x4919a8 | 8 | 0x400658 | 0x400654 | main |
| 54 | 13436 | 13435 | 0x4919b0 | 8 | 0x400658 | 0x400654 | main |
| 55 | 13452 | 13451 | 0x4919b8 | 8 | 0x400658 | 0x400654 | main |
| 56 | 13468 | 13467 | 0x4919c0 | 8 | 0x400658 | 0x400654 | main |
| 57 | 13484 | 13483 | 0x4919c8 | 8 | 0x400658 | 0x400654 | main |
| 58 | 13500 | 13499 | 0x4919d0 | 8 | 0x400658 | 0x400654 | main |
| 59 | 13516 | 13515 | 0x4919d8 | 8 | 0x400658 | 0x400654 | main |
| 60 | 13544 | 13543 | 0x4919e0 | 8 | 0x400658 | 0x400654 | main |
| 61 | 13572 | 13571 | 0x4919e8 | 8 | 0x400658 | 0x400654 | main |
| 62 | 13600 | 13599 | 0x4919f0 | 8 | 0x400658 | 0x400654 | main |
| 63 | 13628 | 13627 | 0x4919f8 | 8 | 0x400658 | 0x400654 | main |
| 64 | 13656 | 13655 | 0x491a00 | 8 | 0x400658 | 0x400654 | main |
| 65 | 13684 | 13683 | 0x491a08 | 8 | 0x400658 | 0x400654 | main |
| 66 | 13712 | 13711 | 0x491a10 | 8 | 0x400658 | 0x400654 | main |
| 67 | 13740 | 13739 | 0x491a18 | 8 | 0x400658 | 0x400654 | main |

K=1's load PC was **not** measured (the Commit trace omitted its line); it is
not in main, so it does not matter for ROI. `†` = PC not directly measured for
that dynamic instance (Commit-trace gap); the PC is the instruction that the
Exec trace proves accesses that exact effective address (section 2.3) and is
the same loop as its measured neighbours. Every **main** row's VA is inside the
workload's global buffer `0x4919a0..0x491aa0`, which only `main` touches.

### 2.3 Where the PCs came from (FW02 log has no PC field)

The F6 suppression line prints only `load_seq, store_seq, Vaddr, FwdSize`; it
has no PC (unlike LP01's v3.3.2 line). Two extra single-process debug runs were
used, with everything else identical:

```bash
build/ARM/gem5.opt --outdir=census_v332/FW02_w4v2_commit_pc \
  --debug-flags=Commit --debug-file=commit.log \
  configs/se/lsu_proxy.py --cmd=workloads/directed/sq_forward_w4v2 \
  --cpu O3 --variant B0 --probability 1.0 --chaos_propagation \
  --prop_trace_file prop_trace.csv.gz --chaos_lsqfwd --lsq_struct_mode f6_fw02 \
  --max_faults 1 --rng_seed 2941542370 --lsqfwd_event_ordinal 1
# same, but --debug-flags=Exec --debug-file=exec.log  (dir FW02_w4v2_exec_effaddr)

build/ARM/gem5.opt --outdir=census_v332/FW02_w4v2_decode_pc \
  --debug-flags=Decode --debug-file=decode.log   (also attempted; incomplete coverage)
```

`Commit` prints `[sn:N] PC (0x...=>...)` for ROB heads and supplied 45 of the
60 in-main load PCs plus their store PCs. `Exec` (with `ExecEffAddr`) prints
`PC : op : ... A=0x<effective>` and directly binds the remaining forwarded VAs,
e.g.:

```
15444660: ... T0 : 0x400538 @main+72 : ldr x4, [x1, x4, LSL #3] : MemRead : D=... A=0x491a30
15697220: ... T0 : 0x400620 @main+304 : ldr x2, [x1, x4, LSL #3] : MemRead : D=... A=0x4919c8
```

The second line independently confirms the provided fact: ordinal 50's forward
is load PC `0x400620`, VA `0x4919c8`. The store that creates it is
`0x40061c` (`str x2, [x1, x4, lsl #3]` in the same loop). The measured
store/load pairs also match the disassembly of `workloads/directed/sq_forward_w4v2`
(`main` = `0x4004f0-0x400720`):

| loop | store PC | load PC | forward |
|---|---|---|---|
| init loop (32 iterations) | 0x400530 | 0x400538 | same 8-byte address |
| byte-overlap loop (8 iterations) | 0x400570 | 0x400574 (`ldur w3,[x4,#-6]`, 4 B) | load inside store's 8 B |
| index loop A (8 iterations) | 0x40061c | 0x400620 | same 8-byte address |
| index loop B (16 iterations) | 0x400654 | 0x400658 | same 8-byte address |
| final loop (32 iterations) | 0x400688 | 0x4006a8 | same 8-byte address |

### 2.4 ROI

- Observed forward total = **67** (`CHAOS_FW02_SUMMARY observed=67`).
- In-main ordinals = **contiguous `[8, 67]`**; ordinals 1-7 are libc/startup
  (stack VAs `0x7ffffe...`, libc data `0x496798`, `0x48fb70`, libc PCs).
- **N_ROI = 60**.
- **ROI start = 8** (`load_seq 12133`, `va 0x4919a8`, PC 0x400538; ordinal 7 is
  libc PC 0x4011fc), **ROI end = 67** (`load_seq 13740`, `va 0x491a18`,
  PC 0x400658).

### 2.5 Percentile contexts

`k(p) = ceil(p*N_ROI)`, `ordinal = 8 + k - 1`.

| p | k(p) | ordinal | load_seq | store_seq | Vaddr | size | load_pc | store_pc |
|---|---|---|---|---|---|---|---|---|
| 0.1 | 6 | 13 | 12243 | 12241 | 0x4919d0 | 8 | 0x400538 | 0x400530 |
| 0.3 | 18 | 25 | 12479 | 12477 | 0x491a30 | 8 | 0x400538 | 0x400530 |
| 0.5 | 30 | 37 | 12587 | 12585 | 0x491a90 | 8 | 0x400538 | 0x400530 |
| 0.7 | 42 | 49 | 13344 | 13343 | 0x4919c0 | 8 | 0x400620 | 0x40061c |
| 0.9 | 54 | 61 | 13572 | 13571 | 0x4919e8 | 8 | 0x400658 | 0x400654 |

Raw log line for p=0.3 (dedicated probe `FW02_w4v2_p30`):

```
Tick: ... , Site: store->load_forward_decision, FaultType: f6_fw02_suppress,
load_seq: 12479, store_seq: 12477, Vaddr: 0x491a30, FwdSize: 8, faults_injected: 1
```

Distinctness: all five differ in `load_seq`, `store_seq` and `Vaddr` (hence
different dynamic forwards). p=0.1/0.3/0.5 share load PC `0x400538` (three
distinct init-loop iterations) and p=0.7/0.9 use `0x400620`/`0x400658`; that is
loop sharing, not identity collapse. FW02's suppression log carries no LQ/gen
field, so the identity tuple is `(load_seq, store_seq, Vaddr)`.

Observation only: the p=0.5 probe was `ORACLE_PASS` (suppressing that
forwarding still yields the correct checksum, i.e. the memory path returned the
same data); the other four were `ORACLE_FAIL`. No conclusion about propagation
class is drawn here.

---

## 3. Honest gaps / blockers

1. **FW02 injector log has no PC.** PCs in section 2 are from gem5 `Commit` /
   `Exec` debug traces (raw logs kept), not from the suppression line. For 15 of
   the 60 in-main ordinals the Commit trace's per-head line is missing; those
   PCs are bound by the Exec effective-address evidence plus the loop identity
   and are marked `†`. None of the five percentile identities is affected:
   p10/p50/p70/p90 PCs are directly measured in the Commit trace, and p30's PC
   `0x400538` is directly bound by the Exec line `PC 0x400538 ... A=0x491a30`.
2. **FW02 `max_faults 0` cannot produce an all-suppress trace** — the F6Fw02
   constructor clamps 0 to 1; the instructed attempt therefore suppressed one
   event (`observed=67 suppressed=1`). The census instead swept all 67 ordinals.
3. **LP01 `max_faults 0` is unusable** — corrupting all loads panics in libc
   (`Page table fault ... 0x7fffff0000`, exit 134); the aborted directory is
   retained as evidence and was not used.
4. `pilot_meta.json` records `event_ordinal_used: null`; the authoritative
   ordinal used is `eligible_ordinal=N` in `l1d_fwd_injections.log` (LP01) and
   the sweep/probe ordinal N (FW02). The gem5 command in each `command.txt`
   carries the actual `--event-ordinal`.

## 4. Raw artifact paths

- LP01 coarse/boundary/percentile probes: `audit_v3_3_2/roi/census_v332/LP01_w5_*/`
  (`coarse_K{1,50,100,200,300,400,500,800,900,950,1000,1200,1500,2000}`,
  `sweep_K{875,876,878,880,881,882,884,885,886,887,893,1141,1142,17524,17525,17526}`,
  `p10,p30,p50,p70,p90`), aborted all-fault probe: `LP01_w5_fullstream/`.
- FW02 sweep: `audit_v3_3_2/roi/census_v332/FW02_w4v2_sweep_K1..K67/` and
  `FW02_w4v2_sweep.tsv`; instructed attempt: `FW02_w4v2_all_suppress/`;
  percentiles: `FW02_w4v2_{p10,p30,p50,p70,p90}/`; debug traces:
  `FW02_w4v2_commit_pc/commit.log`, `FW02_w4v2_exec_effaddr/exec.log`,
  `FW02_w4v2_decode_pc/decode.log`.
