# W4 v2 (`sq_forward_w4v2`) evidence — LSU v3.3.2 P0-1 / FW02

Date: 2026-11-11. Scope: prove the W4 candidate ELF executes real store→load
forwarding pairs in `main` under `-O2`, and that the FW02 forwarding decision
fires on an in-`main` load. All numbers below are real command output.

## 1. Files and SHA256

| File | SHA256 |
|---|---|
| `workloads/directed/sq_forward_w4v2.c` | `472b1eef62be94b85ea8b07b11b16806347597ac0ad9d01b45dcf9e1b89e340e` |
| `workloads/directed/compile_sq_forward_w4v2.sh` | `7dad6c9a3e3fbceefa387a9098e3471ba85b86fe9abeedd321d6c7eccf2f44b0` |
| `workloads/directed/sq_forward_w4v2` (ELF) | `a08fb3a7b8bbcef76b0c3c3519a5787370ea7ead2d93de290e00fc6e44fe76e2` |
| `workloads/directed/sq_forward_w4v2.golden` | `668cacca3762804dcb1c00f0ddc96bb4f43d9b42ad2f2ebea3347457f1a63921` |

Build (host is native aarch64, no cross toolchain):

```
gcc -O2 -static -o workloads/directed/sq_forward_w4v2 workloads/directed/sq_forward_w4v2.c
```

The source is `sq_forward_v33.c` with the header comment updated to v3.3.2 W4
candidate; the seven designed phases and the oracle output format are
unchanged from the frozen W4. The only difference from frozen `sq_forward.c`
is `static volatile unsigned long buf[N]` + `volatile` accesses (and phase 7
uses an explicit `volatile` fill loop instead of `memset`, which cannot write
through a `volatile` object).

## 2. Static proof (`objdump -d --disassemble=main`)

`main` spans `[0x4004f0, 0x400740)` (`T main` at 0x4004f0, `T _start` at
0x400740), 141 instructions.

### (a) Full-overlap: `str` then `ldr` from the same buffer index

Phase 5 dependency chain (store then immediately load, same `x1 + x4*8`):

```
  40061c:	f8247822 	str	x2, [x1, x4, lsl #3]
  400620:	f8647822 	ldr	x2, [x1, x4, lsl #3]
  400624:	ca000040 	eor	x0, x2, x0
  400628:	9b057c00 	mul	x0, x0, x5
```

Phase 1 full-overlap loop (store at 0x400530, load at 0x400538, same index):

```
  400530:	f8247823 	str	x3, [x1, x4, lsl #3]
  400534:	8b050063 	add	x3, x3, x5
  400538:	f8647824 	ldr	x4, [x1, x4, lsl #3]
```

### (b) Partial-overlap: 8-byte `str`, then 4-byte `ldur w..` at +2

Phase 2 (`x4` was advanced by 8 before the load, so `[x4, #-6]` = base+2):

```
  400570:	f8237825 	str	x5, [x1, x3, lsl #3]
  400574:	b85fa083 	ldur	w3, [x4, #-6]      // 4-byte load at buffer byte +2
```

### (c) Load/store census in `main`

- Loads: **10** total — 9 buffer data loads
  (`ldr x4`, `ldur w3`, `ldr x0`, `ldr x4`, `ldr x6`, `ldr x4`, `ldr x2`,
  `ldr x3`, `ldr x3`) plus exactly one stack epilogue `ldp x29, x30, [sp], #32`.
- Stores: **12** total — 10 buffer data stores (incl. `strb`, `stur`, `stp`
  is NOT among them) plus one stack prologue `stp x29, x30, [sp, #-32]!` and
  one `strb w2, [x3], #-1` in the local `put_hex` scratch buffer.

So the main data path is not "stores only + a stack epilogue load": there are
9 real buffer loads and 10 real buffer stores. (Frozen W4 non-volatile build
had 1 load / 15 stores.)

Census command:

```
awk '/<main>:/{inm=1;next} /Disassembly of section .fini/{inm=0} inm' main.dis > body
grep -cE '\s(ldr|ldur|ldp|ldrb|ldrh)\b' body   # 10
grep -cE '\s(str|stur|stp|strb|strh)\b' body   # 12
```

## 3. Host oracle

```
$ ./workloads/directed/sq_forward_w4v2
1f4cbf14327717df
EXIT_RC=0
```

Matches the frozen W4 golden `1f4cbf14327717df`.

## 4. gem5 baseline (B0, no fault)

```
build/ARM/gem5.opt --outdir=/tmp/v332_w4_base configs/se/lsu_proxy.py \
  --cmd=$PWD/workloads/directed/sq_forward_w4v2 --cpu O3 --variant B0 \
  --probability 0.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz
```

- Exit code: 0
- stdout: `1f4cbf14327717df` (equals host oracle)
- B0 params + CHAOSPropagation attached as logged.

## 5. FW02 selector mounted, no injection

```
... --chaos_lsqfwd --lsq_struct_mode f6_fw02 --max_faults 0 \
    --rng_seed 1113826800 --lsqfwd_event_ordinal 0
```

Exit 0; stdout `1f4cbf14327717df`; `lsq_fwd_injections.log`:

```
CHAOS_FW02_SUMMARY: observed=67 suppressed=0 load_seq=0 store_seq=0
```

FW02 observed **67** eligible full-coverage store→load forwarding decisions in
the run; none suppressed (probability 0.0 is the matched no-fault control).
All CLI flags used (`--max_faults`, `--rng_seed`, `--lsqfwd_event_ordinal`,
`--lsq_struct_mode f6_fw02`) were accepted as-is by `configs/se/lsu_proxy.py`.

## 6. Injected pairs (probability 1.0, max_faults 1)

### Ordinal 50 — in-`main`, real forward, produces an SDC

```
Tick: 15700300, Site: store->load_forward_decision, FaultType: f6_fw02_suppress,
load_seq: 13356, store_seq: 13355, Vaddr: 0x4919c8, FwdSize: 8, faults_injected: 1
CHAOS_FW02_SUMMARY: observed=67 suppressed=1 load_seq=13356 store_seq=13355
```

Trace `prop_trace.csv.gz` records:

```
...,fw02_decision,13356,,4919c8,,,
  record=fw02_decision;family=fw02;model=FW02;load_seq=13356;store_seq=13355;
  normal_decision=forwarded;fault_decision=suppressed;memory_path=1;
  replay_count=0;vaddr=0x4919c8;size=8
...,fwd,13356,,4919c8,,,
  ...;load_seq=13356;store_seq=13355;byte_begin=4790728;byte_end=4790736;size=8;
  store_data_fnv=429c2f3e0e35be8a;store_data_hex=0fe0000000000000;
  forward_data_fnv=0;forward_data_hex=null;decision=suppressed;memory_path=1
...,resp,13356,70,769c8,,,
  ...;data_hex=05b0000000000000;...;pa=769c8
...,commit,13356,,,,,
  trigger=fault_instruction_commit;tracked=fault;pc=400620;...
...,errant_commit,13356,,,,,trigger=faulting_load_commit;pc=400620;...
```

- **load PC = 0x400620** (directly logged by the commit/errant-commit records;
  inside `main`).
- **store PC = 0x40061c** — not directly logged (FW02 traces do not emit a
  store PC), but uniquely determined: `store_seq 13355` immediately precedes
  `load_seq 13356`; the disassembly at 0x40061c is the `str x2, [x1, x4, lsl #3]`
  immediately before the load at 0x400620; the forwarded store bytes
  `0fe0000000000000` are little-endian `0x000000000000E00F`, exactly the
  phase-5 value `prev+i` at `i=5` (0xE000+0+1+2+3+4+5 = 0xE00F); and the load
  vaddr `0x4919c8` = `buf + 0x28` = `buf[5]` (buf at 0x4919a0 from the
  `adrp x7,491000; add x1,x7,#0x9a0` prologue). So this is a genuine older
  store / younger load full-coverage forward in `main`.
- The suppressed load fell through to the memory path and read the **stale**
  value `05b0000000000000` = `0xB005` (the phase-2 value of `buf[5]`, the
  store to `buf[5]` had not drained). Program stdout changed accordingly:
  `0b97cade7dfd1781` instead of `1f4cbf14327717df` — an observable SDC caused
  by suppressing a real in-`main` store→load forward.

### Ordinal 1 — first eligible forward, a libc/startup pair (not `main`)

```
Tick: 518980, Site: store->load_forward_decision, FaultType: f6_fw02_suppress,
load_seq: 258, store_seq: 248, Vaddr: 0x7ffffefbd0, FwdSize: 8, faults_injected: 1
CHAOS_FW02_SUMMARY: observed=67 suppressed=1 load_seq=258 store_seq=248
```

- load PC = **0x40c0e0** (squash record `dyn_inst_seq=258;...;pc=40c0e0`,
  inside `_dl_non_dynamic_init` [0x40c180,0x40c9b0) — libc startup, NOT main).
- vaddr `0x7ffffefbd0` is a stack address; store PC not logged.
- Checksum stayed `1f4cbf14327717df`; the faulting load was later squashed
  (`reason=lsq_squash`, `triggering_seq=257`, `squash_cause=unrelated`), so
  suppressing this pair had no architectural effect.

## 7. Residual limitations (honest statement)

1. **The F6/FW02 event ordinal is global over all eligible full-coverage
   forwards, including libc/startup code.** `--lsqfwd_event_ordinal N` counts
   every eligible forward in dynamic order, so `ordinal 1` selects a libc
   startup pair (PC 0x40c0e0, stack vaddr), not a `main` pair. The current CLI
   has no "restrict to main's PC range" selector. Selecting an in-`main` pair
   therefore requires a sufficiently large ordinal (here 50 lands on
   `main+0x130`, load seq 13356).
2. **Store PC is not emitted by the FW02 trace records.** `fw02_decision`,
   `fwd`, `inj`, `addr_form`, `resp` carry `load_seq`, `store_seq` and `vaddr`
   only. The store PC given above is a deterministic deduction (adjacent
   dynamic seq, disassembly adjacency, and the exact forwarded store value +
   buffer index), not a directly logged field. The load PC is directly logged.
3. Invalidating a suppressed forward is only meaningful when the store has not
   yet drained: ordinal 50 demonstrates the stale-read SDC; ordinal 1
   demonstrates a benign/squashed case. Both are real forwards; neither is a
   fabricated event.
4. No C++/config changes were made; this evidence is workload + observation
   only. The candidate ELF is not yet promoted to the frozen formal W4 ELF.
