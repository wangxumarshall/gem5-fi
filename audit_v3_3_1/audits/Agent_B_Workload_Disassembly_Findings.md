# Agent B — Workload & Disassembly Audit (LSU v3.3.1)

Date: 2026-11-11. Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
(branch `fix/r6-s-w1-continuation-20261101`, HEAD `f1291067`). Read-only audit:
no gem5/gem5.opt or scons was run, and no tracked file was modified. Scope is
exactly 12 models x R01-R05 (`A01, A03, FW02, FW05, SQ01, SQ03, SP05, DA04,
LP01, MD04, LQ04, RP01`); the 74-model baseline is out of scope.

Companion data: `audit_v3_3_1/audits/LSU_12Model_Workload_Readiness.csv` (12 rows).

**Round baseline binary** `build/ARM/gem5.opt` SHA256
`d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`
(recomputed with `sha256sum` this round; matches the round plan). Historical
pilots and goldens were produced on other binaries (`720eb780`, `68c6ce73`,
`e527f26a`, ...); no chain is merged across binary SHAs here.

Tools actually used: `python3/openpyxl 3.1.5`, `sha256sum`, `file`, `nm -n -S`,
`readelf -sW`, `objdump -d --disassemble=main/_start`, `csv`.

---

## 1. Authoritative model -> workload map (from the workbook, not memory)

Sources read with openpyxl:
`docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`
sheets `3.最终12模型矩阵` (rows 2-13), `5.60个样本执行矩阵` (rows 2-61),
`6.工作负载及无故障基线` (rows 2-9); plus the frozen
`audit_v3_2_12/W1_W8_Baseline_Map_v3.2.12.csv` and
`audit_v3_2_12/CLOSURE_INPUTS_v3.2.12.md`.

| Model | Workbook WorkloadID / Name | Frozen formal ELF | Actual closure ELF |
|---|---|---|---|
| A01 | W1 `agu_addrmodes` | `agu_addrmodes` | same |
| A03 | W1 `agu_addrmodes` | `agu_addrmodes` | same |
| LQ04 | W2 `lq_lifetime_ordinal` (sheet5/map); sheet6 says stale `lq_lifetime` | `lq_lifetime_ordinal` | same |
| SQ01 | W3 `sq_drain` | `sq_drain` | `sq_reload_v3212` |
| SQ03 | W3 `sq_drain` | `sq_drain` | `sq_reload_v3212` |
| LP01 | W5 `load_response` | `load_response` | same |
| SP05 | W6 `store_path` | `store_path` | `sq_reload_v3212` |
| FW02 | W4 `sq_forward` | `sq_forward` | same |
| FW05 | sheet3 says W8 `alignment` (historical); frozen to `fw05_forward` (W8a) | `FW05_Workload_Archive/bin/fw05_forward` | same |
| MD04 | W7 `replay_dependency` | `replay_dependency` | same |
| RP01 | W7 `replay_dependency` | `replay_dependency` | same |
| DA04 | W8 `alignment` (W8b) | `alignment` | same |

The workbook is internally inconsistent in three places (real defects, not ELF
defects): sheet6 W2 names the superseded `lq_lifetime`; sheet3/sheet6 never add
`fw05_forward` as its own row; sheet5 FW05 `BinaryPath` says
`workloads/alignment` while `BinarySHA256` is `fw05_forward`. The frozen map
(W1-W8 = 9 rows, W8 split W8a/W8b) is the authoritative formal map and was used
for the CSV.

---

## 2. ELF and source identity (recomputed this round)

All ELFs are `ELF 64-bit LSB executable, ARM aarch64, statically linked, not
stripped` (`file` on each). Repo-relative paths are under
`docs/gem5-fi/lsu/implementation_v3_2/workloads/` unless noted.

| Workload | ELF SHA256 (recomputed) | Source SHA256 (recomputed) | main range (`nm -n -S`) | static buffer |
|---|---|---|---|---|
| agu_addrmodes | `90a19003…406b49b` | `26fd7f61…107e3a` | `0x4004f0-0x40074c` | `array 0x493000, 512 B` |
| lq_lifetime_ordinal | `fa25f785…48d97ba` | c `416cf409…dc92d`; S `5be6b3d7…8b20a` | `0x400180-0x400330` (_start `0x400330-0x40036c`) | `arr.4 0x420060, 4096 B`; `guard.3 0x420020, 64 B` |
| sq_drain | `d423539c…867f188f` | `23f93a3f…8b7d0cc2` | `0x4004f0-0x4005bc` | `a.0 0x491990, 65536 B` |
| sq_forward | `132a84f7…69b0af297` | `af19ca80…422d4bab` | `0x4004f0-0x4006e8` | `buf 0x4919a0, 256 B` |
| load_response | `3779e8ce…0753e711` | `411919a1…bd0d85651f` | `0x4004f0-0x4005b8` | `a.0 0x491990, 16384 B` |
| store_path | `906b3798…55fbcf` | `8b7076dd…27e5016` | `0x4004f0-0x4006c4` | `a.0 0x491990, 32768 B` |
| replay_dependency | `ca15390f…41d838f4` | `b0a5073d…415f4d7421` | `0x4004f0-0x400598` | `a.0 0x491990, 8192 B` |
| alignment | `89ff937a…4677918c0` | `dd6f70a1…c04f013a` | `0x4004f0-0x4005e0` | `a.0 0x491990, 4096 B` |
| fw05_forward (W8a) | `0cf40509…f39f5b1cf` | `c79b4be9…347dfdfa4` | `0x4004f0-0x4005d0` | `buf.0 0x491990, 512 B` |
| sq_reload_v3212 | `bcab9cc5…c2567d178de6` | `abbb0dcd…db0614133` | `0x4004f0-0x4005d0` | `buf 0x491990, 2048 B` |

`FW05_Workload_Archive/bin/fw05_forward` is byte-identical to
`workloads/fw05_forward` (same SHA and same `BuildID=75b753ba…`).
All nine W1-W8b ELF SHAs equal the frozen map; `sq_reload_v3212` equals
`WORKLOADS.md`.

Note the sheet6 W2 row `7c69fd27…` is the **superseded** `lq_lifetime` ELF
(source `a1d87a3a…`); the frozen formal ELF is `lq_lifetime_ordinal`
`fa25f785…`. Both files exist in the workload directory; only the latter is in
the frozen map.

---

## 3. Disassembly — is each designed event really present?

All quotes are literal `objdump -d` output on the tracked ELF.

### W1 `agu_addrmodes` — YES (loads + stores, all addressing modes)
```
400558: f8408441  ldr x1, [x2], #8
400604: f8408c41  ldr x1, [x2, #8]!      (pre-index)
400648: a9401841  ldp x1, x6, [x2]
400678: 38403441  ldrb w1, [x2], #3
40068c: f947fc82  ldr x2, [x4, #4088]    (page-end)
4006a0: 3dc000a1  ldr q1, [x5]
4006a8: 3ce26880  ldr q0, [x4, x2]       (SIMD/register-offset)
```
`array` is `0x493000` (512 B). There are 13+ load PCs and 8-iteration loops.

### W2 `lq_lifetime_ordinal` — YES (freestanding; five anchors + main load loop)
```
_start:
400338: f9400022  ldr x2, [x1]
40033c: f9400423  ldr x3, [x1, #8]
400340: f9400824  ldr x4, [x1, #16]
400344: f9400c25  ldr x5, [x1, #24]
400348: f9401026  ldr x6, [x1, #32]
main:
400210: 3861c881  ldrb w1, [x4, w1, sxtw]
400214: 3860c880  ldrb w0, [x4, w0, sxtw]
4002a8: 38401481  ldrb w1, [x4], #1
```
The five anchors are the designed ordinal targets; main's load loop
`0x400200-0x40023c` runs 64 iterations.

### W3 `sq_drain` — YES (stores) + full-array read-back
```
400530: 39000020  strb w0, [x1]
400538: 39000423  strb w3, [x1, #1]
400540: b81fc022  stur w2, [x1, #-4]
400560: 38010420  strb w0, [x1], #16
400590: 384014a2  ldrb w2, [x5], #1     (FNV re-read of all 64 KiB)
```
The store loop `0x400528-0x400548` runs 4096 iterations (4 stores each);
`0x400560` runs ~3943 iterations.

### W4 `sq_forward` — **NO DATA LOAD IN main** (FW02 pair absent)
```
400534: f8008441  str x1, [x2], #8
40055c: f80084e1  str x1, [x7], #8
4005dc: f82178c2  str x2, [x6, x1, lsl #3]
400614: f82178a1  str x1, [x5, x1, lsl #3]
40064c..400668: ad0000c0  stp q0, q0, [x6, #0] .. (memset block)
4006ac: 381ff462  strb w2, [x3], #-1
4006e0: a8c27bfd  ldp x29, x30, [sp], #32   <-- only load, stack epilogue
```
`grep`-equivalent inspection of the whole `main` shows no `ldr/ldrb/ldp` from
`buf` (`0x4919a0`, 256 B). The source
(`workloads/sq_forward.c`) does contain `acc = fnv(acc, buf[i])` after each
store, but `buf` is non-volatile, so gcc `-O2` constant-folded every reload.

### W5 `load_response` — YES (two independent loads per iteration)
```
400548: f8627862  ldr x2, [x3, x2, lsl #3]
40054c: f8617861  ldr x1, [x3, x1, lsl #3]
400588: 38401460  ldrb w0, [x3], #1
```
Loop `0x400540-0x400564` runs 128 iterations ((25223-7)/197).

### W6 `store_path` — YES (store stream; SP05 target real)
```
400558: 3c810400  str q0, [x0], #16
4005a0: 3c810400  str q0, [x0], #16
4005d8: 3c810400  str q0, [x0], #16
400620: ad000001  stp q1, q0, [x0]
400644: 38206841  strb w1, [x2, x0]
400670: 38004401  strb w1, [x0], #4
400698: 38401480  ldrb w0, [x4], #1      (read-back)
```
Half/word stores were vectorised into `STR Q`/`STP Q`, but the store stream
that SP05's `completeStore` bookkeeping observes is real.

### W7 `replay_dependency` — YES (real same-address alias)
```
40050c: f8217840  str x0, [x2, x1, lsl #3]   (init loop)
40052c: f8247840  str x0, [x2, x4, lsl #3]   (older store, 8 B)
400530: f8647841  ldr x1, [x2, x4, lsl #3]   (younger load, same address)
```
Alias loop `0x400528-0x400544` runs 256 iterations. Store and load are both 8 B
at the same address: full coverage, never partial.

### W8a `fw05_forward` — YES (four stores to one address, then load)
```
400548: f8247862  str x2, [x3, x4, lsl #3]
400554: f8207861  str x1, [x3, x0, lsl #3]
400558: f8207865  str x5, [x3, x0, lsl #3]
40055c: f8207866  str x6, [x3, x0, lsl #3]
400560: f8207867  str x7, [x3, x0, lsl #3]
400564: f8607860  ldr x0, [x3, x0, lsl #3]
```
Loop terminates after 2000 iterations (`cmp x2, x9` with
`x9 = 0x3333333333333b03`).

### W8b `alignment` — YES (unaligned 4 B pair)
```
400538: b8004420  str w0, [x1], #4       (x1 = x6+0x991, mod 4 = 1)
400558: b8404440  ldr w0, [x2], #4       (x2 = x6+0x991, mod 4 = 1)
400584: 381f8002  sturb w2, [x0, #-8]
400588: 381fb001  sturb w1, [x0, #-5]
```
The `str` loop `0x400538-0x400544` runs 1023 iterations
(`k*0x9e3779b1 = 0x3faf4a4f mod 2^32` with k = 1023).

### sq_reload_v3212 — YES (store -> dmb ish -> same-address load -> branch)
```
40053c: f8207906  str x6, [x8, x0, lsl #3]     /* the store */
400540: d5033bbf  dmb ish
400544: f8607904  ldr x4, [x8, x0, lsl #3]     /* same-address reload */
40056c: eb06009f  cmp x4, x6
400570: 540001a1  b.ne 4005a4                  /* equality-dependent branch */
```
128 iterations (`cmp w7, #0x80`); source `sq_reload_v3212.c:41-52` matches.

---

## 4. No-fault golden and oracle line re-verification

`logs_v3_2_12/baselines_w1_w8/FINAL_BASELINE_SUMMARY.csv` has **9/9 PASS** on
FINAL binary `68c6ce73…4e4e8`, exit 0, printed checksum == golden, workload SHA
== frozen map. Rows: W1 `728e604ffcec539d`, W2 `b097eb83f71545cb`, W3
`ba3b3185e541ad03`, W4 `1f4cbf14327717df`, W5 `99c106541150be0e`, W6
`2543a2a60de01795`, W7 `59fc61c040618747`, W8a `67afad307642983e`, W8b
`3f89eab79392ce69`.

Every workload has a runtime oracle line in its source (no hard-coded value):

- `agu_addrmodes.c:12` prints a 16-hex buffer via `write(1,...)`; `sq_forward.c:13` same.
- `lq_lifetime_ordinal.c:83-93` prints `checksum=0x...` with raw `write`.
- `sq_drain.c:8`, `load_response.c:7`, `store_path.c:53`, `replay_dependency.c:7`,
  `alignment.c:38`, `fw05_forward.c:44`, `sq_reload_v3212.c:54`, and
  `sq03_probe.c:38` call `printf("checksum=0x%016llx\n", ...)`.

Golden files exist for all ten: e.g. `sq_drain.golden` = `ba3b3185e541ad03`,
`alignment.golden` = `checksum=0x3f89eab79392ce69`, `sq_reload_v3212.golden` =
`7df5034c23f3e703` with `sq_reload_v3212.host.out` =
`checksum=0x7df5034c23f3e703`.

**sq_reload_v3212 is not in `FINAL_BASELINE_SUMMARY.csv`** (that CSV is the
9-row W1-W8b set). Its no-fault evidence is `WORKLOADS.md` (branch-root
`build/ARM/gem5.opt`, O3, exit 0, `checksum=0x7df5034c23f3e703`,
`simTicks 28387975`), the host double-run golden, and the 5/5 SUPP pilot
oracle logs on `bcab9cc5`. This round did not run gem5, so that baseline is
reported from its recorded artifact, not re-executed.

---

## 5. Every recorded injection PC -> symbol (data-driven)

Method: dumped `InjectionPC` from all 173 records in
`audit_v3_2_12/*_records_v3.2.12*.json`, then resolved each PC against
`nm -n -S --defined-only <ELF>` for the ELF whose SHA256 is the record's
`WorkloadSHA256`. `None`/`0` PCs are reported as unrecorded, not fabricated.

| Workload | Distinct recorded PCs | Symbol resolution | In main? |
|---|---|---|---|
| W1 / A01 | 0x400790, 0x400ad0, 0x40c0f0, 0x40c110 | `_start+0x10`, `__libc_start_main_impl+0x40`, `_dl_aux_init+0x30`, `_dl_aux_init+0x50` | **0/4** |
| W1 / A03 | none (InjectionPC null or 0) | `addrpath_injections.log` prints `pc=0`; EAs `0x7ffffefd90..0x7ffffefb90` are stack | n/a (EA says startup) |
| W2 / LQ04 | 0x400338, 0x40033c, 0x400340, 0x400344, 0x400348 | `_start+0x8..+0x18` (the five designed anchors) | 0/5 in main; **5/5 on designed anchors** |
| W3 / SQ01 | none on sq_drain; 0x40053c on sq_reload | sq_drain: `NO_INJECTION`; sq_reload: `main+0x4c` (store) | 0/5 on W3; **5/5 on sq_reload** |
| W3 / SQ03 | none on sq_drain; 0x40053c on sq_reload | ditto | 0/5 on W3; **5/5 on sq_reload** |
| W5 / LP01 | 0x4005d0, 0x400910, 0x4113a0, 0x4113c0, 0x4113c8 | `_start+0x10`, `__libc_start_main_impl+0x40`, `_dl_aux_init+0x30/+0x50/+0x58` | **0/5** |
| W6 / SP05 | 0x400a10, 0x400a18, 0x400a24 (v3.2.9, store_path); 0x400544 (records) / 0x40053c (trace `store_pc`) on sq_reload | `__libc_start_main_impl+0x0/+0x8/+0x14` (prologue `stp` stack stores); sq_reload `main+0x54` record / `main+0x4c` store | 0/5 on W6; **5/5 on sq_reload** |
| W4 / FW02 | 0x40c0c8, 0x40a4f8, 0x4448a4, 0x4448c8, 0x422378 | `_dl_aux_init+0x88`, `sbrk+0x98`, `_dl_find_object_init+0x40/+0x64`, `_dl_protect_relro+0x48` | **0/5** |
| W7 / MD04 | 0x4113d0, 0x400d98, 0x400530, 0x4015fc, 0x4288dc | `_dl_aux_init+0x60`, `__libc_setup_tls+0xd8`, `main+0x40`, `printf+0x8c`, `_IO_new_file_overflow+0x88` | **1/5** (R03 only) |
| W7 / RP01 | 0x4015fc, 0x42a6d8, 0x42a6dc, 0x422a58, 0x44e2ec | `printf+0x8c`, `_IO_doallocbuf+0x18`, `_IO_doallocbuf+0x1c`, `__printf_buffer_done+0x8`, `_fini+0xc` | **0/5** |
| W8a / FW05 | 0x400564 | `main+0x74` (the designed load) | **4/4** (SUPP-R02..R05); base R01-R05 `NO_INJECTION` |
| W8b / DA04 | 0x41143c, 0x411454, 0x41126c, 0x400538 | `_dl_aux_init+0x8c`, `_dl_aux_init+0xa4`, `__tunable_get_val+0x2c`, `main+0x48` (unaligned str) | **2/5** (R04/R05) |

Two PC-attribution facts worth carrying forward:

1. **A03 records no PC at all.** All A03 records have `InjectionPC=null` or
   `"0"`; `pilots_v3_2_12/SUPP-A03-R01/addrpath_injections.log` prints
   `pc=0` on every `A03_STREAM` line, and the injected EAs are stack addresses.
   Therefore "is A03's injection inside main?" cannot be answered from a PC —
   only from the EA domain, and the EA domain is startup stack, not
   `array 0x493000`.
2. **SP05 records the consumer PC, not the store PC.** For
   `SUPP-SP05-R01B` the record says `InjectionPC=400544`, but the trace's
   injection event carries `store_pc="0x40053c"` and
   `store_seq=12108`, `sq_entry_id=944` (the `str x6` at `main+0x4c`).
   `0x400544` is the reload `ldr`. Both are in main, but the record field is
   the reload consumer.

---

## 6. ROI feasibility per workload

The v3.3.1 Decision A selects R01-R05 at 10/30/50/70/90 % of the
model-specific eligible-event stream **inside the ROI**. Readiness therefore
requires (a) a real `main` region containing the designed event, and (b) at
least 5 distinct eligible dynamic contexts inside it. "Static YES" below means
the instruction set and loop structure exist; the exact `N_ROI` must be
measured by the T2 census (not run here).

| Workload | Real main loop? | Eligible event count (static) | >=5 distinct contexts? | Notes / recommendation |
|---|---|---|---|---|
| W1 agu | yes (13+ load PCs, 8-iteration loops) | A01/A03 load EA | YES | Add a PC/opcode filter or a startup skip; ordinals 1-5 currently hit libc. A03 must also record the PC. |
| W2 lq_lifetime_ordinal | yes (`0x400200-0x40023c`, 64 iters) | LQ allocation/request | YES | The 5 designed anchors are in `_start`; keep them, or move ROI into the main load loop. Fix sheet6/run script. |
| W3 sq_drain | yes (4096 + ~3943 iters) | SQ write / executeStore | YES (4 store PCs x thousands of dynamic events) | W3 has no recorded injection. Decide W3 vs `sq_reload_v3212` (approval input). |
| W4 sq_forward | **no data loads** | forwarding match | **NO** | FW02 impossible on this ELF. Rebuild or replace. |
| W5 load_response | yes (128 iters, 2 loads/iter) | load response | YES (256 events) | Add warm-up/PC filter; add a matched control. |
| W6 store_path | yes (six store loops: 256/512/512/256/4093/1024 iterations) | completeStore | YES | Historical injections are libc prologue stores. Freeze the HANG-vs-SDC terminal. |
| W7 replay_dependency | yes (256 alias pairs) | MD04 violation / RP01 partial forward | MD04 YES; **RP01 NO** | RP01's designed partial coverage never occurs (8 B store + 8 B load, full overlap). |
| W8a fw05_forward | yes (2000 iters) | wrong-source forwarding | YES | Injection already in main. Add a matched control on the FINAL binary. |
| W8b alignment | yes (1023 iters) | 4 B byte-enable | YES (2 unaligned 4 B PCs x 1023) | 2/5 recorded in main. Add a matched control; low ordinals hit libc. |
| sq_reload_v3212 | yes (128 iters) | SQ01 store data / SQ03 canWB / SP05 completion | YES (5 distinct `buf[0..4]` addresses, K*=1006/1009/940) | Valid alternative ELF; see §7. |

---

## 7. Direct answers to the three required questions

### Q1. Does the frozen W4 ELF execute FW02's store→load pair?
**NO.** `objdump -d --disassemble=main sq_forward` (ELF `132a84f7…`,
the exact artifact the frozen matrix names) contains stores at
`0x400534/0x40055c/0x4005dc/0x400614/0x40064c-0x400668/0x4006ac` and exactly
one load, `0x4006e0: a8c27bfd ldp x29, x30, [sp], #32`, which restores the
stack frame. There is no data load from `buf` (`0x4919a0`) in `main`. The
source does write `acc = fnv(acc, buf[i])` after each store, so this is a
compiler artifact: `buf` is non-volatile and gcc `-O2` constant-folded every
reload. FW02's forwarding target is unproducible on W4; historical FW02 PCs
are 5/5 in libc (`_dl_aux_init`, `sbrk`, `_dl_find_object_init`,
`_dl_protect_relro`).

### Q2. Do W3/W6 execute SQ01/SQ03/SP05's designed stores?
**YES.** W3 `sq_drain` has four real store instructions in `main`
(`0x400530 strb`, `0x400538 strb`, `0x400540 stur`, `0x400560 strb`) and
`0x400590 ldrb` re-reads the whole 64 KiB; the SQ01/SQ03 targets are real.
W6 `store_path` has six real store PCs (`0x400558/0x4005a0/0x4005d8 STR Q`,
`0x400620 STP Q`, `0x400644/0x400670 STRB`) plus `0x400698 ldrb` read-back;
the SP05 `completeStore` target is real. What is missing is not the event but
the **injection**: every SQ01/SQ03 record on `sq_drain` is `NO_INJECTION`
(binaries `8eb7ce8d`, `b1f7cf18`, `b988b750`), and the five v3.2.9 SP05
injections on `store_path` are `__libc_start_main_impl` prologue stack stores
(`0x400a10/0x400a18/0x400a24`), not the workload store stream. The working
5/5 in-main evidence for all three models is on `sq_reload_v3212`.

### Q3. Is `sq_reload_v3212` a valid alternative ELF (SHA/golden/source)?
**YES as an ELF; it is not a frozen formal workload.** Recomputed this round:
ELF SHA `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6`
(matches `WORKLOADS.md`), source `workloads/sq_reload_v3212.c` SHA
`abbb0dcd3c22666a9b0e05a80743c32256d415e33a089b5755269d3db0614133`,
`sq_reload_v3212.golden` = `7df5034c23f3e703`, host output
`checksum=0x7df5034c23f3e703`; `file` reports a static aarch64 ELF. The
designed sequence is real: `str x6` at `0x40053c`, `dmb ish` at `0x400540`,
same-address `ldr x4` at `0x400544`, `cmp`+`b.ne` at `0x40056c/0x400570`.
The 5/5 SUPP records on it inject at `main+0x4c` (store) with the reload as
consumer. However: (a) it is explicitly **not** part of W1-W8 (frozen map and
`CLOSURE_INPUTS_v3.2.12.md` §3.1); (b) it has no row in
`FINAL_BASELINE_SUMMARY.csv` (only the `WORKLOADS.md` no-fault baseline); and
(c) sheet3/sheet5/sheet6 still map SQ01/SQ03 to W3 and SP05 to W6. Migrating
the formal RunIDs is a researcher decision, not an audit action.

---

## 8. Verdicts (12 models)

| Model | Workload | Status | One-line reason |
|---|---|---|---|
| A01 | W1 | PARTIAL | Valid ELF/golden; ordinals 1-5 land in `_start`/libc, not main |
| A03 | W1 | PARTIAL | Same workload; injection PC unrecorded (`pc=0`), EAs are startup stack |
| LQ04 | W2 | PARTIAL | 5/5 on the designed freestanding anchors; sheet6 W2 stale + no run script; oracle lifecycle-only |
| SQ01 | W3 | PARTIAL | W3 valid but `NO_INJECTION`; working 5/5 is on off-map `sq_reload_v3212` |
| SQ03 | W3 | PARTIAL | same as SQ01 |
| LP01 | W5 | PARTIAL | Valid two-load loop; 0/5 recorded PCs in main; no matched control |
| SP05 | W6 | PARTIAL | W6 store stream valid; historical injections are libc prologue; closure on `sq_reload`; may HANG |
| FW02 | W4 | DESIGN_CHANGE_REQUIRED | W4 `main` has zero data loads; forwarding pair does not execute |
| FW05 | W8a | READY | 4 stores + load in main; injections at `main+0x74`; SDC observed; add a FINAL-binary control |
| MD04 | W7 | PARTIAL | Real 8 B alias pair; only 1/5 recorded PCs in main; no matched control |
| RP01 | W7 | DESIGN_CHANGE_REQUIRED | No partial-coverage store→load exists in W7; 0/5 recorded PCs in main |
| DA04 | W8b | READY | Unaligned 4 B pair; 2/5 recorded PCs in main with SDC; add a FINAL-binary control |

Tally: **READY 2, PARTIAL 8, DESIGN_CHANGE_REQUIRED 2, BLOCKED 0** (12 model
rows). W8a/W8b are ready workload-wise; both still lack a matched control on
the final binary (`68c6ce73`).

---

## 9. Recommendations / blockers to carry forward

1. **FW02 (W4) — rebuild required.** Make the reload survive `-O2`
   (`volatile`/opaque asm or a different frozen workload), re-run the host and
   gem5 goldens, record the new SHA. Do not overwrite `sq_forward` in place.
2. **RP01 (W7) — design decision required.** W7 has full 8 B overlap only.
   Either add a partial-overlap store→load workload, or adopt RP01 option C
   (violation/snoop replay) on the existing alias. This is a researcher
   decision, not a workload-ELF defect.
3. **SQ01/SQ03/SP05 — decide W3/W6 vs `sq_reload_v3212`.** Both W3 and W6 do
   execute the designed stores, but their recorded injections are
   `NO_INJECTION` (W3) or libc prologue (W6). The only 5/5 in-main evidence is
   on `sq_reload_v3212`, which the frozen map excludes. Approval input only;
   no mapping change was made here.
4. **Warm-up/ROI (A01, A03, LP01, MD04, DA04 partly).** Frozen ordinals 1-5/14
   count from process start and select `_start`/libc. Add a warm-up event
   count or a PC/opcode filter before freezing R01-R05. A03 additionally needs
   PC recording in the addrpath stream.
5. **Matched controls.** No control pilot directories exist for LQ04-final,
   LP01, FW05, MD04, DA04 in `pilots_v3_2_12` (LQ04 has only
   `pilots_v3_2_10` controls). Also re-adjudicate `SUPP-FW02-C01`: it ran with
   `--probability 0.0` but its closure record says
   `InjectionVerified=yes, InjectionCount=1, InjectionPC=40c0c8`; C02 is clean.
6. **Workbook hygiene (no ELF defect).** Fix sheet6 W2 (stale
   `lq_lifetime` SHA), add `fw05_forward` as its own W8a row, fix sheet5 FW05
   `BinaryPath`, and add `run_lq_lifetime_ordinal.sh`.

---

## 10. What was NOT verified

- No gem5/`gem5.opt` run and no scons in this audit; all dynamic claims come
  from recorded `*_records_v3.2.12*.json`, `pilot_meta.json`,
  `addrpath_injections.log`, `trace_v31.jsonl`, `oracle.log` and
  `FINAL_BASELINE_SUMMARY.csv`.
- Sibling-worktree paths named in the workbook were not visited; the
  re-anchored copies were verified by SHA256 instead.
- No workload was recompiled; the W4 finding is a property of the tracked
  ELF `132a84f7…`.
- `N_ROI` and the exact percentile contexts are T2 census outputs, not part of
  this static audit. The "EligibleEventSufficiency" values in the CSV are
  static lower-bound statements from the disassembly loop structure.
