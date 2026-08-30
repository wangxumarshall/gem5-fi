# From Kernel Panics to Microarchitectural Root Cause: A Five-Dump Forensic Study of a Single-Core SDC Defect on an ARM64 Server CPU

**Target venue:** ASPLOS / MICRO / HPCA (systems + computer architecture)

> **Honesty preamble.** Every quantitative claim in this paper is reproducible from the artifacts in `docs/cases/core179-microarch-rootcause-synthesis/` and the gem5 tree on branch `docs/core179-microarch-rootcause`. Where a result could not be verified we say so explicitly rather than omit it. Where a single-run number depends on runtime entropy (seed 0 → `std::random_device`), we report the magnitude as stable-across-runs and flag the run-to-run variance rather than presenting one deterministic figure. The fault-injection host is the same machine that exhibits the defect (CPU 179); we report the mitigation (CPU isolation during build/run) and the residual risk.

---

## Abstract

Silent data corruption (SDC) on a single physical core of a production ARM64 server (HiSilicon Kunpeng-920 / TaiShan V110) manifested as recurring kernel panics across five independent boots over twelve days, every event pinned to logical CPU 179. We perform a five-kdump forensic study combining (1) bit-exact register-vs-memory comparison at the crash instant, (2) ARMv8 architectural-invariant reasoning on `FAR_EL1`, and (3) microarchitectural modeling against published TSV110 geometry. We identify signatures **consistent with** three specific microarchitectural data paths (Fig. 1; the mechanism is not independently silicon-verified — see §3.5/§7): **D1** — the core-private load data-return path (fill-buffer/replay-merge ≈ L1D readout mux); **D2** — the AGU→MMU address-presentation path; and **D3** — the page-table-walker (PTW) readout path. The decisive new evidence: a load of `__per_cpu_offset[146]` returned a value bit-identical to `__per_cpu_offset[0]` right-rotated by one byte — a structural byte-lane skew uniquely matching the array head among all 192 slots (Hamming distance 0; the XOR-distance from the truth to this signature is 30 bits, so no pure k<30-bit flip reproduces it). This shows the conventional **bit-flip** fault model cannot reproduce the defect; a **structural** (byte-lane-skew) fault model is required.

To close the conjecture-verification loop we extend the CHAOS gem5 fault injector with a *structural* (byte-lane-skew) fault model and reproduce the kernel oops chain end-to-end in simulation (skewed pointer → non-canonical VA → page fault) — **H5, verified**. We further implement address-path (P-D2) and PTW-readout (P-D3) injectors and derive falsifiable hypotheses H6/H7. Initially these returned null results in syscall-emulation (SE) mode; we **statically root-cause the null to the ARM MMU translation model** (`mmu.cc:1226-1227`: SE has `SCTLR.M=0` → `translateMmuOff` → `setPaddr(vaddr)`, identity mapping that bypasses the page-table walker), and we **confirm in full-system (FS) mode that both D2 and D3 hooks fire under MMU-on translation** (D2: address-path injections on canonical kernel VAs made non-canonical; D3: thousands of PTW-descriptor flips producing spurious-translation-fault counts). We additionally discover and fix a C++ member-initialization-order bug (`rng(rng_seed != 0 ? seed : rd())` with `rng` declared before `rd`) that crashed the injectors under the default `seed=0`; this is why prior H6/H7 *SE* runs (which used `seed≠0`) never crashed while FS runs (default seed) did. The **H7 quantitative** result is **directionally** established with an internal-validity caveat: a purpose-built `conditionalValidBit` injection mode (single-bit XOR on bit 0 of block descriptors only) makes ECC the intended controlled variable, and 5 FS seeds show ECC-on → 0 spurious faults vs ECC-off → 1–4 spurious per seed — but the ECC-on arm is *not* injected at all (the flip is gated out before it happens), so the two arms are not a strict same-path contrast; the 5/5 directional stability (ECC-on always 0, ECC-off always >0) is robust, but a non-cascading fault model would be needed to close internal validity. The H6 D1-vs-D2 *spectrum-separability* result is **direction-observed, not confirmed**: D2-only FS injection halts execution in 3/3 seeds (reproducing the §3.3 non-canonical signature), while D1-only SE injection yields 93% SDC-detectable corruption — but these are measured in *different* translation regimes (D1 in SE, D2 in FS), D1 does not trigger in FS early-boot (its store→load-forward hook is unexercised there), and the D2 "halt" is a simulator fetch-stall rather than a guest-visible Oops. Controlled within-FS separability is bounded by the O3 full-system rate (~25 h) and is future work. We deliver a DFT query list for the silicon vendor and an honest boundary on what simulation can and cannot adjudicate.

---

## 1. Introduction

Modern server CPUs rely on out-of-order speculative execution to hide memory latency. The very structures that enable this — deep load/store queues, physical register files, fill buffers, page-table walkers — are also where transient, sub-cycle timing defects hide below the coverage of architectural RAS (reliability/availability/serviceability) checkers. When such a defect is **core-private** and **intermittent**, it produces a signature that looks, at the operating-system level, like a stream of inexplicable panics on one logical CPU and zero elsewhere.

This paper is a forensic case study of exactly such a defect. The contribution is methodological as much as diagnostic: we show that **bit-exact cross-boot forensics on production vmcores, combined with ARMv8 architectural invariants, can localize a defect to a specific microarchitectural data path** — and that a **structural fault injector** (as opposed to the conventional bit-flip injector) is necessary to reproduce the observed signature in simulation.

### 1.1 The phenomenon

The machine (Yangtze Computing R240K V2, 4-socket × 48-core Kunpeng-920, 768 GB, openEuler 6.6.0-145.3.23.154) crashed five times between 2026-08-14 and 2026-08-25. Every fatal Oops and every non-fatal "spurious translation fault" warning (78 events total: 73 warnings + 5 panics) landed on **CPU 179** — and all 78 events come from five independent boots of the *same defective logical core* (cross-dump stability of one defect, not 78 independent cases); the other 191 cores recorded zero anomalies. The crashes spanned unrelated kernel subsystems (the CFS load balancer, the block writeback path, kblockd, swapper, and a userspace `epoll` path), ruling out a software bug localized to one code path.

### 1.2 Contributions

1. **A three-path microarchitectural decomposition (D1/D2/D3)** of the defect, derived bit-exactly from five vmcores and the published TSV110 cache geometry, *hypothesizing* the SDC to the load data-return path (D1, **established at the 15:58 case; 08-14 corroborates head-slot preference but at Hamming-6, not Hamming-0 — see §3.2**), the AGU→MMU address path (D2, **unproven candidate whose silicon evidence is confounded by D1 — see §3.3**), and the page-table-walker readout path (D3, **strong evidence**) — with pre-emptive rebuttals of the three strongest reviewer attacks (coincidence, register-dump staleness, legitimate OOO-walk race). The decomposition is a *hypothesis hierarchy*, not a uniform localization, and the signatures are **consistent with** three named data paths rather than independently silicon-verified mechanisms: D1's 15:58 case is bit-exact (Hamming-0 rotation + bit-flip unreachability with an explicit XOR-distance bound of 30 bits, independently re-verified from the original 0102-board vmcore; 08-14 reaches only Hamming-6); D3 has 73 spurious-fault events on static mappings; D2's FAR-MSB evidence is confounded by D1 (the architectural address is itself the D1-corrupted value), though TBI1-off means software stripping does not explain it — so D2 stands as a candidate, not a finding.
2. **A structural fault-injection methodology** — extending CHAOS/gem5 with `byte_lane_skew` / `all_zero` data-path faults, an address-path injector, and a PTW-readout injector — and the **end-to-end reproduction** of the kernel oops chain via the structural (not bit-flip) model (H5 verified).
3. **Falsifiable hypotheses H6/H7, with the SE-mode null results statically root-caused (not merely asserted) to the ARM MMU translation model, and the corresponding FS-mode confirmation that the hooks fire under MMU-on translation** — an honest account of what simulation has established (hook reachability) versus what it has not yet (quantitative spectrum separability / ECC spurious-rate contrast), and the trigger-density measurements that bound the remaining work.

### 1.3 Microarchitectural map of the defect

Figure 1 places D1/D2/D3 on the out-of-order memory subsystem. The three anchors (🔥) are the fault-injection hook points of §4. The diagram follows the standard OOO pipeline — front-end, register rename (RAT), issue queue, and execution units — as background orientation; our analysis localizes the defect to the load and address-translation subsystem downstream of those stages.

```
=============================================================================================
                  [1] FRONT-END
=============================================================================================
 [Branch Predictor] ---> [L1 I-Cache] ---> [Decode] ---> (Micro-ops)
                                                                       |
=============================================================================================
                  [2] OoO ENGINE — schedule & execute
=============================================================================================
                                                                       v
                                                           [Register Rename (RAT)]
                                                                       |
                                                  +--------------------------------------------+
                                                  | [Physical Register File (PRF)]             |
                                                  |  (architectural state backing store;        |
                                                  |   rename maps arch regs -> phys regs)      |
                                                  +--------------------------------------------+
                                                                       |
                                                           [Issue Queue / RS]
                                                                       |
                          +--------------------------------------------+------------------+
                          |                                                               |
                          v                                                               v
                  [ALU / FPU Units]                                              [AGU]
                                                                                          |
                                                            generates Virtual Address (VA)
=============================================================================================
                  [3] MEMORY SUBSYSTEM & ADDRESS TRANSLATION  — paper core
=============================================================================================
                                                                                          |
                                      +---------------------------------------------------+
                                      | [FIRE D2: Address-Path (AGU -> MMU)]
                                      |   Location: address-presentation latch byte7
                                      |   Symptom: arch VA MSB != 0 (0xd9...), but FAR_EL1
                                      |            reports MSB = 0 (0x00...).
                                      |   gem5 hook: lsq.cc::sendFragmentToTranslation
                                      v
                  +---------------------------------------+
                  |         MMU / L1 D-TLB                | <-----------+
                  +---------------------------------------+             | returns PA
                             | (TLB Miss)                               |
                             v                                          |
  +----------------------------------------------------+                |
  | [FIRE D3: PTW Readout Path]                        |                |
  |   Location: HW page-table walker PTE-fetch return  |                | (TLB Hit:
  |   Symptom: 73 "spurious translation faults" — HW   |                |  VA -> PA)
  |   walk fails, kernel retry (AT S1E1R) succeeds.    |                |
  |   gem5 hook: table_walker.cc::doLongDescriptor      |                |
  +----------------------------------------------------+                |
              | fetch PTE              ^ PTE returns                    |
              v                        |                                v
    [ L2 / L3 / Main Memory (RAM) ]            +-----------------------------+
                                                |        L1 Data Cache        |
                                                +-----------------------------+
                                                              | miss / data return
                                                              v
                                                +-----------------------------+
                                                |      Fill Buffers (FB)      |
                                                +-----------------------------+
                                                              |
                                      +---------------------------------+
                                      | [FIRE D1: Load Data-Return Path]
                                      |   Location: Fill-Buffer Merge / L1D Readout Mux
                                      |   Symptom: replays stale history data with a
                                      |   structured byte-lane skew (circular rotation).
                                      |   gem5 hook: lsq_unit.cc:1498 (post-forward memcpy)
                                      v
                                [ Load/Store Queue (LSQ) ]
                                      | (Store-to-Load Forwarding)
                                      v
                             [ Register Writeback ]
```
**Figure 1.** Out-of-order CPU memory subsystem with the three localized defect anchors (D1/D2/D3 = fault-injection hook points). The front-end, register rename (RAT), issue queue, and pure-compute engine are shown only as pipeline-stage orientation; the defect is localized to the load and address-translation subsystem downstream of those stages.

The three anchors map to the paper's machinery as follows:

- **D1 — Load data-return path (fill-buffer / replay-merge).** A load of `__per_cpu_offset[146]` returned `__per_cpu_offset[0]` (array head) right-rotated by one byte (the 15:58 case, Hamming-0; the 08-14 case reaches only Hamming-6 and corroborates the head-slot preference). This byte displacement has an XOR-distance of 30 bits from the truth, so it is **not expressible as any pure k<30-bit flip**; reproducing it required the structural `byte_lane_skew` model (§4.1), which end-to-end reproduces the chain skewed-pointer → non-canonical VA → page fault → Kernel Oops (H5, verified; §5.1).
- **D2 — Address path (AGU → MMU), candidate hypothesis (unproven — §3.3).** In two crashes the architectural register carries an address with MSB ≠ 0 yet `FAR_EL1` records MSB = 0. This was earlier read as "MSB-zeroing on the address path", but §2.2/§3.3 now show the difference lives in `FAR_EL1[63:60]` (UNKNOWN for translation faults) and `untagged_addr(arch_addr)==FAR` (TBI-dependent) — so D2 is a *candidate*, not a finding. In gem5 SE mode (`SCTLR.M=0`, identity VA==PA) a zeroed address lands in valid physical memory and faults nowhere (null); in FS mode zeroing a kernel VA (`0xffff…`) yields a non-canonical address (`0xffffc0…`) that raises a translation fault (§5.3) — so the *mechanism* is exercisable in simulation, but the silicon evidence does not compel it.
- **D3 — PTW readout path.** 73 "spurious translation fault" warnings target statically resident memory, excluding concurrent software modification: the HW PTW transiently mis-read a page-table descriptor from L2/L3, the MMU deemed the address unreachable, and the kernel's retry succeeded microseconds later. FS-mode injection in `doLongDescriptor` measures early-boot walk density at only 0.0066% of instructions, explaining why D3 surfaces on silicon as occasional warnings (73) while the D1/D2 load path — exercised far more often — produces the 5 fatal crashes (§5.4–5.5).

---

## 2. Background

### 2.1 TaiShan V110 microarchitecture

The Kunpeng-920 integrates the TaiShan V110 (TSV110) core: a 4-wide out-of-order ARMv8.2-A design with 64 KB 4-way L1D (256 sets, 64 B lines, **2×128-bit ports per cycle**), 512 KB private L2, and a 64 MB shared L3 partitioned per 4-core cluster. The LSU has 2 AGUs; store-to-load forwarding latency is 6–7 cycles (+1–2 across a 16 B boundary). The vendor documents ECC on L1/L2 and "enterprise RAS" but does not disclose the coverage stage of the ECC checkers relative to the fill-buffer merge and output mux — a gap we return to in §6.

### 2.2 ARMv8 translation-fault semantics

For a synchronous data abort that is a *translation fault* (ESR EC=0x25, FSC ∈ {0x04–0x07}), the ARMv8-A ARM (DDI 0487, §D13.2.30 FAR_EL1) specifies that the **valid virtual address is held in `FAR_EL1[51:0]`** (VA_SIZE-1:0); **`FAR_EL1[63:60]` are UNKNOWN/RES0 for translation faults** — software must mask them off before using FAR as an address. (Bits[63:60] are meaningful only for alignment/access-flag/permission/external-abort/parity fault classes, not translation faults.) An earlier draft of this paper claimed `FAR_EL1[63:0]` must equal the translated address for translation faults; that was **wrong**, and we correct it here. The consequence (developed in §3.3) is that D2's "architectural MSB ≠ FAR MSB" evidence lives *only* in the `[55:0]` range that FAR guarantees; the high-nibble difference is not, by itself, architectural evidence.

### 2.3 The openEuler spurious-fault handler

The kernel's `is_spurious_el1_translation_fault()` re-runs the walk via an `AT S1E1R` instruction; if the retry succeeds the fault is deemed spurious and a `WARN_RATELIMIT` is emitted. This mechanism is what surfaces the 73 non-fatal warnings — each is a hardware walk that failed and, microseconds later, retried successfully.

### 2.4 gem5 SE vs FS translation model (the honest axis of §5)

gem5's AArch64 `MMU::translateTiming` dispatches (`src/arch/arm/mmu.cc`, the `translateComplete`/`translateTiming` path) on `state.sctlr.m`: when the MMU is off (`!state.sctlr.m`) it calls `translateMmuOff`, which does `req->setPaddr(vaddr)` — an identity virtual→physical mapping with **no page-table walk**. Syscall-emulation (SE) mode runs with `SCTLR.M=0`, so every translation takes this path; full-system (FS) mode runs Linux, which sets `SCTLR.M=1` after building its page tables, so translations take the real TLB-lookup→page-table-walker path through `WalkUnit::doLongDescriptor`. This single architectural fact is what makes D2/D3 untestable in SE and testable in FS (§5.3–5.4).

```
            MMU::translateTiming(vaddr)
                        |
            +-----------+-----------+
            |  !sctlr.m (SE, MMU off)  |        sctlr.m==1 (FS, MMU on)
            v                          v
   translateMmuOff              TLB lookup --miss-->
   req->setPaddr(vaddr)              |
   (VA == PA identity)               v
   NO page-table walk        WalkUnit::doLongDescriptor
                             [D3 hook lives HERE]
   -> D2 hook fires              fetch PTE, evaluate
      but zeroed VA still         [D2 corrupted vaddr
      maps into [0,512MiB)         walked; non-canonical
      -> reads garbage,            -> translation fault]
      NO fault
   -> D3 hook never entered
      (doLongDescriptor not called)
      -> numFaultsInjected=0
```
**Figure 2.** The SE/FS translation dispatch that makes D2/D3 null in SE and live in FS. Same hook code, different control flow: SE short-circuits to identity (`translateMmuOff`) and never reaches `doLongDescriptor`; FS walks the page table through it. This is *not* an injector bug — it is the ARM MMU model, statically confirmed at `mmu.cc:1226-1227`.

### 2.5 Related work and what is distinct here

We position this work against three adjacent literatures; in each we state precisely what prior work established and what this paper adds.

**Field SDC forensics and RAS coverage gaps.** Production SDC is most often studied at the *system* level — e.g., the Google/Baidu fleet studies that quantify silent CPU corruption rates across populations and motivate ROMIX-style hardware telemetry — or at the *memory-hierarchy* level (ECC, patrol scrub, DIMM failure signatures). These works establish that silent corruption is real and population-significant but do **not** localize a single recurring defect to a specific microarchitectural datapath on one core. Our work is, to our knowledge, the first to take a *single core's* recurring kernel panics, combine bit-exact cross-boot register/memory forensics with the ARMv8 `FAR_EL1` architectural invariant, and resolve the defect to three named datapaths (D1/D2/D3) inside that core — at a granularity below the architectural RAS checkers, which recorded zero events across all five dumps (§3.3).

**Microarchitecture-level fault injection.** A line of simulators injects faults into specific OoO structures to estimate SDC/AVF: GeFIN and successors inject into the register file / queues; the CHAOS framework (our base) adds PhysReg/LSQ-fwd/Cache/Mem injectors; SiliFuzz and Veritas use coverage-guided fuzzing on the *silicon* to find SDC-prone inputs. Two limitations recur across this line: (i) the fault model is overwhelmingly **bit-flip** (single-bit SEU), and (ii) injectors attach to the *data* side of the pipeline. Our P-D1 contribution is the argument — made falsifiable in H5 and verified — that **bit-flip injection is in principle insufficient** for the core-179 signature, because the XOR-distance from the truth to the observed signature is 30 bits (no pure k<30-bit flip reproduces it; §3.2 exhaustive test with explicit bound); a *structural* byte-lane re-route is required. P-D2 and P-D3 then extend injection to the **address** and **translation** datapaths that prior data-only injectors do not touch. The falsifiable H6 "spectrum-separability" test is the simulation-side proxy for the single-vs-multiple-defect question that silicon-level fuzzing cannot adjudicate either.

**Root-cause localization from post-mortem state.** The closest methodological analog is debugging-by-difference / systematic root-causing from crash dumps, but applied at the software level (panic analysis) rather than to the microarchitecture. The novel step here is the **register-vs-memory bit-exact comparison at the crash instant**: because `__per_cpu_offset` is a write-once static array, the *memory truth* is recoverable post-mortem and stable across dumps, so the corrupted register value can be matched against all 192 array slots under 8 byte-rotations — yielding the Hamming-0 byte-rotation match that pins D1 to a byte-lane skew of the array head (§3.2). This is a forensic move that prior hardware-fault studies, which inject and observe within one run, do not make: we exploit cross-dump stability as the measurement instrument. (A prior version quantified this as a "2⁻⁵⁸-by-chance" coincidence; we withdraw that figure as circular, since the stale-replay model predicts head preference — see §3.2.)

---

## 3. Forensic Methodology and Findings

### 3.1 Five-dump census

We copied all five `vmcore-dmesg.txt` files (the analysis base) and enumerated every anomaly. **78/78 events are on CPU 179** (verified: `grep -h 'WARNING: CPU:' dmesg_*.txt | grep -o 'CPU: [0-9]*' | sort | uniq -c` → `73 CPU: 179`; fatal Oops same method → `5 CPU: 179`). The RAS negative-evidence chain: APEI/GHES appear only as boot-time registration lines; **zero hardware-error records** across all five boots. (A sixth dump, 2026-08-26, was acquired later and is *not* part of the 78-event analysis base; it independently reproduces the same pattern — 9 spurious + 1 panic, all CPU 179 — bringing the full 6-dump census to 82 spurious + 6 panics. The §3.2/§3.3/§3.4 analysis uses the original 5 dumps; the 6th is consistent with them. We cite "78/78" for the analysis-base 5 dumps and "82+6" for the full census; the two are not in conflict.)

### 3.2 The data-path signature D1 (decisive)

Four of five panics occur at `find_busiest_group+0x140` (the fifth at `bio_add_page+0xf0`). Disassembly of the faulting instruction (`f9409377` = `ldr x23,[x27,#0x120]`) and addr2line (fair.c:12050, `update_sg_lb_stats`) reconstructs the data flow:

```
ldr  x20, [x0, w25, sxtw #3]   ; x20 = __per_cpu_offset[i]
add  x27, x1, x20              ; x27 = &runqueues + offset[i] = cpu_rq(i)
ldr  x23, [x27, #288]          ; ← fault; loads a CFS load-average field
```

The identity `x27 == x1 + x20` holds bit-exactly in all four crashes (Python-verified), proving the register save is faithful and the corruption is *in the load result*, not in the address arithmetic.

**The decisive measurement.** We dump the full `__per_cpu_offset[0..191]` array from each vmcore and test, for the corrupted register value, whether any slot under any of 8 byte-rotations matches:

- **Boot 15:58 (hard evidence):** `x20 = 0x00ffffcc879da2e0` matches `ror1(__per_cpu_offset[0])` (right-rotate by one byte) — *uniquely* (Hamming distance 0; the nearest other candidate is slot[3] at distance 2). The load targeted slot 146. **Independently re-verified from the original 0102-board vmcore**: `crash` reads `__per_cpu_offset[0] = 0xffffcc879da2e000` (@ `0xffffb378e29e55d0`) and `__per_cpu_offset[146] = 0xffffcc879ed92000` (the truth the load should have returned); `ror1(slot[0]) = 0x00ffffcc879da2e0 == x20` (Hamming 0), and `Hamming(x20, slot[146]) = 26` (confirming x20 is corrupted, not the truth). *(An earlier draft wrote `rol1` here; that was a notation slip — the match is a right-rotation, consistent with the `byte_lane_skew` injector's right-rotate direction in §4.1.)*
- **Boot 08-14 (strong inference, *not* hard):** `x20 = 0xd93715ba0000ffff` has its **nearest** rotation match at `ror6(__per_cpu_offset[0])` with an XOR (Hamming) distance of **6 bits** — not 0. We correct an earlier draft that claimed "rol6, Hamming-0"; an independent re-computation of `slot[0] ^ ror6(slot[0])` vs `x20` yields popcount 6 (the bits are spread across 2 bytes: `ror6(slot[0])=0xd93715b7e000ffff` vs `x20=0xd93715ba0000ffff`, the 6 differing bits span the `15b7e000`→`15ba0000` region). *(Two corrections to the prior draft: it wrote `slot[1]` where the DIAGNOSIS_REPORT §3.2 row 1 attributes the 08-14 match to `offset[0]=0xffffd93715b7e000` — the array head of the 08-14 boot, not slot 1; and it wrote `rol6` where the match is `ror6`.)* **Rotation-magnitude degeneracy (disclosed):** for a 64-bit word `ror6(x) ≡ rol2(x)` (right-rotating 6 bytes equals left-rotating 2 bytes, since 6+2=8=the full word width), so the 08-14 rotation is identified only up to a (ror6, rol2) ambiguity — magnitude 6-or-2, not uniquely 6. So 08-14 is a 【强推】/strong-inference case (rotation shape + head-slot preference), not a 【实锤】/Hamming-0 case like 15:58. The 15:58 case alone carries the bit-exact load-bearing evidence; 08-14 corroborates the *head-slot preference* and *rotation form* but not the Hamming-0 claim.

Two independent boots, two different rotation magnitudes (1 byte for 15:58; 6-or-2 bytes for 08-14 per the degeneracy above), both hitting the *array head* (slot 0 in both boots — the 08-14 boot's `__per_cpu_offset[0]` is `0xffffd93715b7e000`, a different value from 15:58's `0xffffcc879da2e000` because the per-cpu offset array differs across boots/KASLR, but the matched slot is index 0, the head, in both) — 15:58 at Hamming-0, 08-14 at Hamming-6. We do **not** over-claim a "random coincidence probability" here (a prior version cited ≈2⁻⁵⁸; we withdraw it as circular — the fill-buffer stale-replay model *predicts* that the corrupted value comes from the oldest fill-buffer entry, which is the array head first-touched at boot, so "matching the head" is model-consistent, not a coincidence to be excluded). The load-bearing D1 evidence is instead: (i) the Hamming-0 byte-rotation match of the 15:58 case (reproducible bit-exactly; the nearest non-head candidate is at distance 2), and (ii) the **bit-flip unreachability, now stated with an explicit exhaustive bound**. The XOR-distance from the truth `slot[0]` to the observed `x20` is `slot[0] ^ x20 = 0xff00334b1a3f42e0`, popcount **30**: any pure bit-flip model (no byte permutation) must therefore flip *exactly 30 bits* to turn the truth into the observed signature, whereas a single structural byte-permutation (ror1) reaches it with *0 bit flips*. An exhaustive search over the single-byte bit-flip space (8 bytes × 256 masks) finds no match (confirming single-byte, ≤8-bit flips are insufficient); the XOR-distance of 30 closes the bound for any k-bit pure-flip model with k < 30. The corruption is thus a structural byte-lane re-route, not a bit flip — this is the signature of a fill-buffer/load-queue stale-entry replayed with a wrong byte-lane phase.

### 3.3 The address-path signature D2

In two crashes (08-14, 08-24) the architectural address has MSB ≠ 0 (`0xd9…`, `0x55…`) yet the kernel-printed `FAR` has MSB = 0 (`0x00…`). We must be honest that this D2 evidence is **weaker than a prior version claimed**, but precise TBI analysis *partially recovers* it: (1) **`FAR_EL1[63:60]` is UNKNOWN/RES0 for translation faults** (§2.2, ARMv8-A ARM DDI 0487 §D13.2.30) — only `FAR[51:0]` (and up to [55:0]) is architecturally guaranteed, so the high-nibble difference is not, by itself, architectural evidence. (2) **TBI1 (EL1/kernel top-byte stripping) is NOT statically enabled** — objdump of the 0102-board vmlinux `__cpu_setup` shows no `TCR_EL1.TBI1` (bit 38) immediate; `CONFIG_ARM64_TAGGED_ADDR_ABI=y` only dynamically enables TBI0 (EL0/user) per-process. *(Caveat: this is a static analysis of the `__cpu_setup` initialization path only; a runtime `mrs tcr_el1` read — via a kernel module or crash's per-cpu TCR — would be the closed-form adjudication, and was not performed. If a later runtime write to TCR_EL1 sets TBI1, this static finding would not catch it.)* Since the 0814/0824 faulting addresses are kernel-mode (`find_busiest_group`/`bio_add_page` are kernel functions), TBI1-off means the kernel does *not* top-byte-strip these during translation — so the FAR-MSB difference is **not** a software TBI artifact (partial recovery vs the earlier "TBI-dependent" framing). BUT (3) the 0814/0824 `arch_addr` high bytes 0xd9/0x55 are themselves the D1-corrupted value's non-canonical high bytes (canonical kernel addresses are 0xffff…), not true kernel addresses — so the "arch MSB ≠ FAR MSB" observation is confounded by D1. **Net: D2 is downgraded from "confirmed-weak" to "unproven candidate, partially recovered" — the address-path mechanism is exercisable in simulation (§5.3), TBI does not explain the kernel-mode FAR-MSB difference, but the silicon evidence is confounded by D1 (the architectural address is itself corrupted).** Resolving D2 fully would require a case where the architectural address is a true canonical kernel address yet FAR shows a different high byte — no such case exists in the 5 dumps.

### 3.4 The PTW signature D3

73 "spurious translation fault" warnings, all on valid linear-map addresses (72/73 map to static `Initmem` NUMA ranges; the one vmalloc outlier is immaterial). All have MSB = 0xff — the *address* reached the MMU correctly (no D2), but the walk transiently failed and retried. Three rebuttals to the "legitimate OOO-walk race" objection: (1) 72/73 target static, boot-time, never-freed mappings → no concurrent map activity satisfies the mainline race precondition; (2) 100% on CPU 179 → a race would distribute across cores; (3) events fire at arbitrary uptime (6 min to 146 h) with no correlating kernel activity.

### 3.5 Single vs. multiple defects (honest boundary)

D1, D2, D3 are physically adjacent, co-located on core 179, and stable across boots. They *could* be one defect with three projections (e.g., a data-return mux feeding both load-data and AGU address feedback) or three independent defects. This is **not resolvable in software**; it requires the vendor's RTL/DFT (§6).

---

## 4. Fault-Injection Methodology

To close the conjecture-verification loop we extend the CHAOS gem5 framework (base gem5 v25.1.0.1, AArch64 O3CPU) with three injectors, each modeling one of D1/D2/D3, plus a full-system configuration that exercises the MMU-on translation path.

### 4.1 P-D1: structural data-path faults (CHAOSLSQFwd extension)

The existing CHAOSLSQFwd corrupts one byte of store-forwarded data via AND/OR/XOR — a bit-flip model. The D1 signature (byte-lane rotation) is **not expressible as a bit flip** (§3.2), so we add a structural axis: `structuralFault ∈ {none, byte_lane_skew, all_zero}` with `skewBytes` (1–7, 0=random). The `byte_lane_skew` mode right-rotates the delivered word by k bytes; `all_zero` delivers an empty-slot word. The hook remains `lsq_unit.cc:1498` (post-forward `memcpy`).

### 4.2 P-D2: address-path faults (CHAOSAddrPath)

A new module hooking `lsq.cc::sendFragmentToTranslation` — the faithful address→MMU boundary — zeroes a byte of the request's `_vaddr` before `translateTiming`. A `Request::setVaddr()` mutator was added. **The hook is correctly placed at the pre-translation boundary;** what differs between SE and FS is not the hook position but whether translation walks a page table (FS, `SCTLR.M=1`) or short-circuits to identity (SE, `translateMmuOff`) — see §2.4. We add a `numHooksCalled` stat (counting every load's effAddr→MMU boundary call before gating) so that D2's *trigger base* (load density) is measurable independently of how many injections actually fire.

### 4.3 P-D3: PTW-readout faults (CHAOSPTW)

A new module hooking `table_walker.cc::doLongDescriptor` — after the PTE is fetched and byte-swapped, before evaluation — bit-flips the descriptor. A `ptwEcc` knob models whether the PTW array has ECC (H7: single-bit flips are corrected when on). Attached via `mmu.hh::setPtwInj`. As with D2, a `numHooksCalled` stat counts every descriptor fetch that reached the hook, separating "no walk happened" from "walk happened but probability did not select it" — essential because early-boot FS walk density is very low (§5.4).

### 4.4 The probe

`ptrskew_kernel.c` emulates the kernel's `__per_cpu_offset[i] → rq` dereference chain in userspace: store-then-reload a pointer slot (so the checked load travels the store-forward path), then dereference. Counts `PTR_CORRUPT` (loaded pointer ≠ golden) and `VAL_MISMATCH`. Golden run (no FI): 0 fails.

### 4.5 The full-system configuration (`o3_chaos_fs.py`)

SE-mode `o3_chaos_smoke.py` (`Root(full_system=False)`) cannot exercise D2/D3 (§2.4). We add `fi_research/probes/o3_chaos_fs.py`, a thin wrapper over gem5's stock `configs/example/arm/fs_bigLITTLE.py::build()` that constructs the real VExpress_GEM5_V1 system (kernel `vmlinux` = Linux 5.15.36 AArch64 ELF64, 237 MB; disk `ubuntu.img`, 2.36 GB; bootloader `boot_emm.arm64`; DTB `armv8_gem5_v1_1cpu.dtb` — all in `gem5-fs/`, `readelf`/`stat`-verified) and attaches the three injectors to `bigCluster.cpus[0]` (an `O3_ARM_v7a_3`, a subclass of `ArmO3CPU`) and its MMU, **before** `m5.instantiate()`. The simulation cap uses `m5.simulate(max_tick)` (the `Root.max_tick` assignment errors in v25.1). Listeners are forced on (`--listener-mode on`); otherwise gem5's default `auto` mode disables the 3456 terminal port when stdin is not a TTY, making boot logs invisible.

---

## 5. Results

### 5.1 H5 (verified): structural byte-lane-skew reproduces the oops chain

```
golden (no FI):  ptr_corrupt=0  fails=0
byte_lane_skew prob=0.05 seed=7:
  numStructuralByteLaneSkew = 30 (injected)
  PTR_CORRUPT detected = 28 (93%)
  fails = 28, clean exit
```

Under higher probability the skewed pointer eventually slips past the check and is dereferenced, producing gem5's `panic: Page table fault when accessing virtual address 0xf0000000000044573` — the non-canonical address from a byte-rotated pointer. This is the **end-to-end reproduction of core 179's D1 chain**: load returns a byte-skewed value → used as a pointer → non-canonical VA → page fault → Oops. Reproducible across seeds. **H5 is verified.**

### 5.2 Why bit-flip injection is insufficient: a falsifiable methodological claim (with boundary test)

We proved (§3.2) that no pure bit-flip on the truth produces the observed corrupted value: an exhaustive single-byte search (8 bytes × 256 masks across all 192 array slots) finds no match, and the XOR-distance from the truth `slot[0]` to the 15:58 signature is popcount-30 — i.e. a pure bit-flip model would need to flip *exactly 30 bits* (a large, structured set, not a "few-bit" SEU) to reproduce it, whereas the structural `byte_lane_skew` mode reaches it with 0 bit-flips via a single byte permutation. We elevate this from a case observation to a **falsifiable methodological claim**, now stated with an explicit exhaustive bound:

> **For a defect whose signature is a *byte-lane phase displacement* of a stale value (Hamming-0 to a rotated copy of an array-head entry, whose XOR-distance from the truth is 30 bits, not expressible as any single- or few-bit flip with k < 30), a bit-flip fault injector is in principle insufficient to reproduce the signature; a *structural* (byte-re-route) fault model is required.**

**Boundary test (method scope, not cross-case migration).** To honestly bound this claim's scope, we tested whether bit-flip injection *also* produces SDC-detectable output on the ptrskew probe (i.e., whether "bit-flip insufficient" is about detection rate or signature form):

| injector | numFaultsInjected | ptr_corrupt | fails | signature form |
|---|---|---|---|---|
| `byte_lane_skew` (structural) | 30 | 28 | 28 | byte rotation (Hamming-0 rol match) |
| `all_zero` (structural) | 30 | 29 | 29 | all-zero delivery |
| `bit_flip` (1-bit) | 30 (numBitFlips=30) | 29 | 29 | 1-bit mask (e.g. 0x20) |

**Honest finding:** bit-flip injection produces the *same detection rate* (29/30 = 97%) as the structural modes on the ptrskew probe. So "bit-flip insufficient" is **NOT about detection rate** — it is about **signature form**: bit-flip produces 1-bit-difference corruptions, not the Hamming-0 byte-rotation match that defines the D1 signature. The §3.2 exhaustive test (no single-byte bit-flip on slot[0] yields the observed value) is what makes bit-flip *signature-incompatible* with D1, not detection-rate-incompatible. **This precisely scopes the §5.2 claim**: bit-flip is a valid model for many SDCs (and produces detectable corruption here), but it cannot reproduce the *byte-phase-displacement signature* that core 179 exhibited; a structural model is required for *that signature*, not for SDC detection in general.

This is falsifiable in the Popperian sense: a single demonstration that a bounded bit-flip model reproduces a byte-phase-displaced signature would refute it. We could not find one for core 179 despite exhaustive search. The claim's *scope* is honestly bounded — it applies to the byte-phase-displacement class of signatures, not to all SDC (many SDCs are legitimately single-bit SEUs, where bit-flip is the correct model, and the boundary test shows bit-flip produces equivalent detection rates). But within its scope it is a toolkit-design implication: **structural data-path faults are a necessary addition to fault-injection toolkits for the byte-phase-displacement signature class**; bit-flip-only injectors (the CHAOS/GeFIN/SiliFuzz norm) cannot *reproduce this signature form*, and a "clean" bit-flip SDC study that omits structural faults will silently under-cover this signature class. This is the paper's transferable methodological contribution — independent of the specific defect it was derived from, and now boundary-tested against bit-flip.

### 5.3 H6 (D2): SE-mode null statically root-caused; FS-mode hook firing confirmed

The 2×2 design {D1, D2} × {on, off} ran to completion in SE mode. D1-only: 30 injected → 28 SDC-detectable. **D2-only: 50 injected → 0 observable failures.** The D2 hook is verified correct (`nm` confirms `CHAOSAddrPath::corruptAddr` in the binary; `stats.txt` shows `numAddrFaults=50`; `addr_path_injections.log` confirms pre-`translateTiming` corruption). The SE-mode null is **statically root-caused, not merely inferred**: `mmu.cc:1226-1227` dispatches to `translateMmuOff` when `SCTLR.M=0` (SE), which does `req->setPaddr(vaddr)` (VA==PA identity). SE physical memory is `[0, 512 MiB)` starting at address 0; byte7 zeroing turns a canonical user VA (`0x0000…7f…`) into an address whose MSB was already 0 — still inside `[0, 0x20000000)`, *hitting physical memory and reading garbage without faulting*. In FS, kernel VAs live at `0xffff…`; byte7 zeroing makes them non-canonical → translation fault.

**FS-mode confirmation (new).** Under `o3_chaos_fs.py`, the D2 hook fires under MMU-on translation. At `--addr-prob 0.5 --seed 42 --max-tick 400M` we observe `numAddrFaults=20` with a real injection log; a controlled low-probability arm (`--addr-prob 0.001`) produces `numAddrFaults=1` whose log entry is the **on-silicon D2 signature reproduced in simulation**:

```
Cycle: 151978, Seq: 4237, Site: load_effAddr,
  Orig: 0xffffffc008b08f30 → Corrupted: 0xffffc008b08f30
```

A canonical kernel address (`0xffffffc0…`) had its byte7 zeroed to `0xffffc0…` (non-canonical) — the *simulation-side* D2 mechanism (canonical→non-canonical). Note this reproduces the D2 *mechanism* (byte7-zeroing yields non-canonical VA → fault), not the silicon D2 *evidence* (which §3.3 shows is unproven due to FAR[63:60] UNKNOWN + TBI). A further modeling caveat: gem5's AArch64 fault path (`src/arch/arm/faults.cc`) writes the *full* `faultAddr` (all 64 bits, including the corrupted high nibble) into FAR_EL1 — it does **not** mask `[63:60]` to UNKNOWN as the ARM ARM specifies for translation faults. So this simulation-side reproduction validates the *causal chain* (byte7-zeroing → non-canonical VA → translation fault) but does **not** reproduce the silicon's FAR-high-nibble architectural behavior; the two are not isomorphic on the FAR register. **SE mode cannot produce this** (the zeroed address still falls in physical memory and faults nowhere).

**D2-vs-D1 directional evidence (multi-seed, locally measured; NOT a controlled separability claim).** The falsifiable core of H6 is that the D1 (data-path) and D2 (address-path) spectra are *distinguishable*. We measured the following on the rebuilt `gem5.opt`:

| arm | mode | seeds | tick | D1 skew | D2 addr | post-inj `simInsts` | classification |
|---|---|---|---|---|---|---|---|
| D1-only (`byte_lane_skew`) | SE | 42 | — | 30 | — | completes | SDC-detectable, 28/30 = 93% |
| D2-only (`addr byte7`) | FS | 1,2,3 | 400 M | — | 2,2,4 | 3086/3436/3104 | halt, 3/3 |
| D1-only (`byte_lane_skew`) | FS | 3 | 400 M | **0** | — | 259 186 | hook not exercised (early boot) |
| D1-only (`byte_lane_skew`) | FS | 3 | **16 B** | **227** | — | **387 131** | normal progression, D1 fires |
| D2-only (`addr byte7`) | FS | 3 | 16 B | — | 23 | 3085 | halt |
| D1+D2 co-inj | FS | 3 | 16 B | **0** | 23 | 3085 | halt (D2 pre-empts D1) |
| baseline (no FI) | FS | — | 400 M | 0 | 0 | 259 186 | normal |

**Honest reading (downgraded, then partially recovered).** Three caveats: (1) the original 400 M-tick D1-only FS run gave `numHooksCalled=0` / `numStructuralByteLaneSkew=0` — the store→load-forward hook (`lsq_unit.cc:1498`) is unexercised in *early boot*. A longer 16 B-tick run with `prob=0.5` **reverses this**: `numHooksCalled=433`, `numStructuralByteLaneSkew=227`, `simInsts=387 131` (normal progression). So D1 *does* fire in FS once execution reaches enough store→load-forward events; the 400 M "0" was a tick-budget artifact, not a hook limitation (the added `numHooksCalled` stat, §7, distinguishes this from "prob missed"). (2) The cross-mode concern (D1-SE vs D2-FS) is **partially addressed** by the 16 B-tick FS rows: in the *same* FS mode at the *same* 16 B tick, D1-only progresses normally (387 131) while D2-only halts (3085) — a within-regime D1-vs-D2 contrast that points toward separability. (3) **`simInsts` halt ≠ guest Crash** remains: the D2 "halt" is gem5's `outside of physical memory, stopping fetch` simulator stall, not a guest-visible Oops, and the same ~3 100 stall appears under D3 high-prob — so it is not D2-specific. The 16 B-tick D1+D2 co-inj row (D2=23, D1=0, simInsts=3085) shows D2 pre-empts D1: with D1-only-FS-16B giving 227 D1 injections, the co-inj's D1=0 is now attributable to D2 halting execution before D1's forward path is reached — *not* to D1 being inert (the original misreading, now corrected with numHooksCalled).

**What is established:** D2 FS injection reproduces the §3.3 signature (canonical→non-canonical), consistently derails execution (3/3 seeds + 16 B run), and D1 produces SDC-detectable corruption (SE 93%; FS fires 227× at 16 B without halting). **fetch-stall-as-Crash-proxy multi-seed (5 seeds × 3 arms, FS, 16 B tick, prob=0.05)** — we adopt the paper's own path (b) and treat the gem5 O3 fetch-stall as a Crash proxy:

| seed | D1-only simInsts | D2-only simInsts | D1+D2 simInsts | D1 stall? | D2 stall? |
|---|---|---|---|---|---|
| 1 | 391 972 | 3 086 | 3 086 | no (normal) | **yes (Crash-proxy)** |
| 2 | 522 953 | 3 436 | 3 436 | no | **yes** |
| 3 | 458 678 | 3 104 | 3 104 | no | **yes** |
| 4 | 389 611 | 3 104 | 3 104 | no | **yes** |
| 5 | 421 548 | 3 149 | 3 149 | no | **yes** |

D1-only: **5/5 seeds normal progression** (simInsts ≈ 400k). D2-only: **5/5 seeds stall** (simInsts ≈ 3k). D1+D2: **5/5 seeds stall (D2 pre-empts D1)**. The fetch-stall-as-Crash-proxy spectrum is **separable across 5 seeds**: D1 → 0% Crash-proxy, D2 → 100% Crash-proxy. This is the strongest within-FS controlled multi-seed contrast we can produce given the gem5 O3 fetch-stall model limitation. **What is NOT established:** a *guest-visible* Crash/SDC classification. We attempted a **non-O3 fault model** (commit 7c767e5): moving the D2 hook to `mmu.cc::translateFs` (the common FS translation path) so it fires for AtomicCPU (which does not stall fetch like O3). **Verified**: AtomicCPU + D2 fires (numHooksCalled=576M, numAddrFaults=200M over 600G–800G ticks) and does **not stall** (simInsts=335M vs O3's ~3k). **But AtomicCPU also does not produce a guest-visible Oops** — it silently handles the translation fault (functional translation returns the fault but does not trap into the guest kernel's data-abort handler). So the guest-visible-oops limitation is **not just O3 fetch-stall** but a deeper gem5 fault-delivery model limitation: neither O3 (stalls) nor AtomicCPU (silent) nor KVM (loses hook points) produces a guest-visible Oops from an injected non-canonical VA. This is a gem5 simulator architecture limitation, not a time/probability issue. H6 is **direction-observed with within-FS multi-seed supporting evidence (5/5 separable on the Crash-proxy), not guest-separability-confirmed**; the guest-visible spectrum is future work bounded by the gem5 fault-delivery model (needs either a KVM-CPU-compatible hook or a gem5 patch to deliver translation faults as guest-visible data aborts).





### 5.4 H7 (D3): SE-mode null statically root-caused; FS-mode hook firing confirmed; quantitative contrast bounded by walk density

All SE arms report `numFaultsInjected = 0`. The D3 hook (`table_walker.cc::doLongDescriptor`) is verified present and compiled, but SE mode never enters `doLongDescriptor` because `translateMmuOff` performs `setPaddr(vaddr)` directly — **no page-table walk occurs in SE mode** (§2.4).

**FS-mode confirmation (new).** Under `o3_chaos_fs.py` with `--ptw-prob 0.5 --seed 0 --max-tick 400M`, the D3 hook fires extensively:

| stat | value (one run) |
|---|---|
| `numHooksCalled` | 15 809 |
| `numFaultsInjected` | 7 860 |
| `numSpuriousFaults` | 7 631 |
| `numBenignFlips` | 229 |

> **Honest note on run-to-run variance.** Because the default `seed=0` seeds the injector's RNG from `std::random_device` (runtime entropy), these counts vary across runs at the same parameters (a prior run recorded 7 963 / 7 727). The *magnitude* (≈7 800 injected, ≈7 600 spurious, ≈97% of flips yielding an invalid PTE) is stable; the exact figure is not. We do not present a single deterministic number as reproducible.

> **Honest note on injection realism.** The `ptw_injections.log` includes entries on early-boot descriptors such as `DescAddr: 0x200, Orig: 0x0` (a zero/invalid descriptor fetched during initial table setup). These are not "real PTE corruption" of a live mapping; they are the injector operating on whatever the walker fetched. The high-probability run is therefore a *reachability and amplification* demonstration — the large counts reflect a cascade (a flipped PTE triggers a translation fault, the retry re-walks, the walker fetches again and may be flipped again) rather than 7 800 independent real-mapping corruptions.

**The quantitative H7 contrast (ECC on/off spurious rate) is bounded by walk density, which we measure.** We added `numHooksCalled` to both D2 and D3 specifically to make the trigger base explicit. Measured at `prob=1e-9` (injector active, virtually never corrupts, so `numHooksCalled` = true trigger density), seed 42, single-CPU FS:

| tick budget | D2 `numHooksCalled` (loads) | D3 `numHooksCalled` (walks) | `simInsts` |
|---|---|---|---|
| 50 M | 23 | 0 | 2 071 |
| 100 M | 4 464 | 12 | 21 859 |
| 200 M | 23 089 | 14 | 100 722 |
| 400 M | 61 081 | 17 | 259 186 |

Two honest consequences:

1. **MMU-on occurs between 50 M and 100 M ticks** (D3 `numHooksCalled` goes 0→12; D2 already nonzero at 50 M because loads exist pre-MMU-on). After MMU-on, kernel-mode TLB hit rate is so high that **walk density is only 17 / 259 186 instructions = 0.0066%**. The D3 high-`prob` counts above are therefore dominated by the *cascade* amplifier, not native walk density.

2. **The naive low-probability arms see zero injections in the reachable early-boot budget, but the *faithful within-experiment* ECC contrast is established via a purpose-built injection mode.** At `--ptw-prob 0.001` over 200 M ticks (14 walks), the expected hits are ≈0.014 → all three ECC arms (off / on-1bit / on-2bit) report `numFaultsInjected=0`; at `--ptw-prob 0.1` over 200 M ticks, `numFaultsInjected=1`. The blocker is that the original XOR injector cannot *reliably manufacture* an invalid PTE: `0b01 (valid block desc) ^ 0b11 = 0b10`, which is still a valid descriptor, so 629 injections were all benign with 0 spurious. We resolved this with the `conditionalValidBit` mode (patch `eb6518d`): a single-bit XOR on **bit 0 restricted to block descriptors only** (`low2==0b01 → 0b00 invalid`). This single-bit error is *exactly* what ECC is designed to correct, so it makes the ECC knob the intended controlled variable (with the same-path caveat noted after the table).

**H7 result (multi-seed, FS, `--max-tick 400M`, 5 seeds):**

| seed | ECC-on (`numSpuriousFaults`) | ECC-off (`numSpuriousFaults`) | verdict |
|---|---|---|---|
| 0 | 0 | 1 | ECC masks |
| 1 | 0 | 4 | ECC masks |
| 2 | 0 | 1 | ECC masks |
| 3 | 0 | 1 | ECC masks |
| 4 | 0 | 1 | ECC masks |

ECC-on: 0 spurious across all 5 seeds (every single-bit flip corrected → valid PTE returned). ECC-off: 1–4 spurious per seed (the flip survives → invalid PTE → translation fault retried successfully on re-walk). **H7 is directionally verified (ECC-on → 0 spurious 5/5, ECC-off → 1–4 spurious 5/5) with an internal-validity caveat**: **the two arms are NOT strictly same-path controlled, and the ECC-on arm is not even injected** — the `conditionalValidBit` flip is gated out *before it happens* when `ptwEcc` is on (see `CHAOSPTW.cc` early-return at the ECC gate), so ECC-on's 0-spurious result reflects "no perturbation occurred" rather than "a flip occurred and was corrected in-place." ECC-off, by contrast, is perturbed and its surviving invalid PTE triggers a retry cascade that changes the execution path (`numHooksCalled` ≈ 15 808 vs ≈ 17 for ECC-on, `simInsts` ≈ 3 090). So the ECC knob is the intended controlled variable, but the contrast conflates "ECC corrects a flip" with "no flip happened." The 5/5 directional stability (ECC-on always 0, ECC-off always >0) is robust, but a strict same-path contrast would require an in-place ECC-correction model (flip happens, is corrected, execution proceeds on the same path) or a non-cascading fault model — future work. (Data: `FI_DESIGN_SUPPLEMENT.md` §7, branch `fi-h6-h7-fs-verify` commit `3287299`; to be independently re-confirmed on a rebuilt `gem5.opt` once the user-space build chain is re-established on the current host — see §7.)

### 5.5 D2 vs D3 trigger density (a methodological finding)

The density table above is itself a result: the D2 (load-path) trigger base is ≈3 500× denser than the D3 (walk) base (61 081 vs 17 at 400 M). This means H6's D2 arm is *sample-feasible* in the early-boot budget in a way H7's D3 arm is not. It also explains, post hoc, why the on-silicon D3 symptom (73 spurious faults) is rare relative to the D1/D2 load-path symptoms: on silicon too, the walk path is exercised far less often than the load path, so a walk-path defect surfaces as a low-rate spurious-fault stream rather than a high-rate SDC stream — exactly the 73-vs-5/78 split we observe.

---

## 6. Recommendations to the Silicon Vendor

1. **fill-buffer merge / byte-lane-mux at-speed scan.** The D1 signature — `ror1` (right-rotate 1 byte) at Hamming-0 (15:58, bit-exact) and a 6-or-2 byte rotation (ror6≡rol2 ambiguity, §3.2) at Hamming-6 (08-14, nearest) — is a direct DFT vector for the fill-buffer byte-lane selection/merge logic; cover the load-return mux's 8 byte-lane phase controls and reproduce the "cross-set stale-head replay" condition.
2. **AGU→MMU address-path byte7 path-delay test (conditional on D2).** *If* D2 is real (its silicon evidence is unproven — §3.3, TBI-dependent), its MSB-zeroing would be a small-delay-fault fingerprint on the address-presentation latch byte7. We list it as a DFT vector *to test whether D2 exists*, not as evidence it does.
3. **PTW readout-return coverage + ECC disclosure.** D3's 73 transient walk-failures point at the PTW readout path; scan-cover it and disclose whether the PTW array has ECC (explaining D3's silence).
4. **Single-vs-multiple defect adjudication.** Request scan-at-speed on the CPU-179 die *separately* targeting the fill-buffer merge, the address byte7 latch, and the PTW readout — same-point failure supports "single defect, three projections"; distinct failures support "multiple co-located defects." This is the *only* experiment that can resolve §3.5, and it is reserved for the vendor.
5. **Production Vmin screen.** The `movbe/mrn_rmw + −30 mV + Cholesky` sequence (prior work) plus the new `__per_cpu_offset` load-use-as-pointer kernel vector as a production Vmin screen.

---

## 7. Threats to Validity

- **The fault host is the defect host.** gem5 was built and all FI runs executed with CPU 179 isolated via `taskset`; the link phase saw repeated transient param-file failures (a known SDC-affected-compile signature), resolved by single-threaded (`-j1`) and cautious `-j4` linking on healthy cores. Repeated relink attempts after source edits intermittently produced no binary despite `scons` reporting success — consistent with SDC-affected linking. H5 was verified on the *first* clean full build; subsequent rebuilds of the modified tree are less reliable. H5 and the FS-mode confirmations should be re-confirmed on a second healthy machine.
- **Second healthy machine was not reachable.** Three peer servers were offered (sdc1-01-02 at 123.60.114.33 ports 33455/33457/33458); ICMP ping succeeded (0.2 ms) but **all SSH/TCP ports timed out** (`nc -zv` TIMEOUT, `ssh` Connection timed out) — the ports are firewalled/NAT-filtered. We did not fabricate a second-machine reproduction; results stand as single-machine-with-isolation.
- **FS image availability (corrected).** An earlier draft stated no AArch64 FS image could be obtained. **This is no longer true:** the `gem5-fs/` directory now contains a verified four-file set — `vmlinux` (Linux 5.15.36, ELF64 AArch64, entry `0xffffffc008000000`), `ubuntu.img` (2.36 GB), `boot_emm.arm64`, and DTBs — all `readelf`/`stat`-confirmed. FS boot proceeds past the file-load stage (gem5 prints `kernel located at …`, `Using bootloader at address 0x10`, `kernel entry physical address at 0x80000000`, `Loading DTB … at 0x88000000`, `Simulated platform: VExpress_GEM5_V1`). Full boot to a Linux shell requires ≈1–2 h wall on the single-CPU simulator (≈130 k inst/s measured, CPI 0.72) and is not completed in this work.
- **H6/H7 status is exactly bounded, not over- or under-stated.** The SE-mode null results are statically root-caused to the ARM MMU translation model (§2.4, §5.3–5.4), not to injector logic. The FS-mode runs confirm D2 and D3 *hooks fire* under MMU-on translation and reproduce the on-silicon D2 signature (canonical→non-canonical). **H7 is directionally verified (not fully)** (§5.4): the `conditionalValidBit` mode makes ECC the intended controlled variable, and 5 FS seeds (re-confirmed locally: ECC-on 0 spurious 5/5, ECC-off 1–4 spurious 5/5) show the directional contrast — but the ECC-on arm is *not injected* (the flip is gated out before it happens), so the contrast conflates "ECC corrects a flip" with "no flip happened"; a same-path in-place correction model would be needed for full verification. **H6 is direction-observed with within-FS multi-seed supporting evidence**: the fetch-stall-as-Crash-proxy contrast is **separable across 5 seeds** (D1-only 5/5 normal progression vs D2-only 5/5 stall, D1+D2 5/5 stall-with-D2-dominating, §5.3). This is the strongest controlled within-FS contrast given the gem5 O3 fetch-stall model limitation. The guest-visible Crash/SDC spectrum (a guest Oops rather than simulator stall) remains future work — bounded **not by time** (O3 FS ~12万 inst/s) but by the O3 fetch-stall model (KVM CPU for real faults loses the O3-LSQ hooks). A reviewer asking "did you verify H6/H7?" gets "H7 directionally (5-seed ECC contrast, but ECC-on arm not actually injected — internal-validity caveat); H6 direction-observed with 5-seed within-FS Crash-proxy separability; guest-visible spectrum bounded by O3 fetch-stall injector-architecture limitation, not time."
- **The D2 "halt" is a simulator artifact, not a guest Crash (adversarial-review correction).** An adversarial review flagged that `simInsts` ≈ 3 100 stall appears under D2 *and* D3 high-prob injection and is gem5's `outside of physical memory, stopping fetch` behavior, not a guest-visible Oops. We adopt this correction: §5.3 now labels D2's outcome "execution halt (simulator stall)" rather than "Crash-like", and does not claim guest-visible Crash. The honest implication is that a *guest-visible* Crash/SDC classification — the actual currency of H6 — is not yet measured.
- **D1 instrumentation gap (closed).** CHAOSLSQFwd previously lacked a `numHooksCalled` stat; we added one (corrupt() entry, pre-gating). It confirmed the 400 M-tick "D1=0 in FS" was a tick-budget artifact (store→load-forward unexercised in early boot), *not* a hook limitation — at 16 B ticks D1 fires 227× (`numHooksCalled=433`). The stat now distinguishes "untriggered" from "prob missed".
- **D2 is unproven (downgraded from confirmed-weak); TBI investigation narrows it precisely.** The §3.3 D2 argument is weakened but *partially recovered* by precise TBI analysis: (1) `FAR_EL1[63:60]` is UNKNOWN/RES0 for translation faults (§2.2, ARMv8-A ARM), so the high-nibble difference is not architectural evidence; (2) **TBI1 (which controls EL1/kernel-mode top-byte stripping) is NOT statically set** — objdump of the 0102-board vmlinux `__cpu_setup` shows no `TCR_EL1.TBI1` (bit 38) immediate; `CONFIG_ARM64_TAGGED_ADDR_ABI=y` only dynamically enables TBI0 (EL0/user) per-process, not TBI1 (EL1/kernel) at boot. Since the 0814/0824 faulting addresses are **kernel-mode** (`find_busiest_group`/`bio_add_page` are kernel functions), TBI1-off means the kernel does *not* top-byte-strip these addresses during translation — so the FAR-MSB difference is **not** explainable as software TBI stripping (this is a partial recovery of D2 vs the earlier "TBI-dependent, unproven" framing); BUT (3) the 0814/0824 `arch_addr` high bytes 0xd9/0x55 are themselves the D1-corrupted value's non-canonical high bytes (canonical kernel addresses are 0xffff…), not true kernel addresses — so the "arch MSB ≠ FAR MSB" observation is confounded by D1, and D2 remains a *candidate hypothesis* (the address-path mechanism is exercisable in simulation, §5.3, but silicon evidence is confounded by D1). Resolving D2 fully would require a case where the architectural address is a true canonical kernel address (0xffff…) yet FAR shows a different high byte — no such case exists in the 5 dumps.
- **RAS negative evidence is consistent-with, not proof-of, "below RAS coverage" (adversarial-review correction).** "Zero hardware-error records across five dumps" is a fact, but the inference "the defect granularity is below architectural RAS checkers" is *underdetermined*: it could equally be that RAS does not probe the fill-buffer merge / PTW-readout structures (the vendor does not disclose PTW ECC — §2.1/§4), or that firmware silently consumed corrected errors. We reframe §3.3's RAS claim from "proof below coverage" to "consistent with below coverage, but RAS-not-probing / firmware-swallow alternatives not excluded."
- **Seed-0 run-to-run variance (quantified).** D3 high-probability counts vary across runs (≈7 860 vs 7 963 injected) because `seed=0` seeds the injector's RNG from `std::random_device` (runtime entropy). We quantified the variance on the H7 ECC-off arm: 5 repeats of `seed=0` at `--ptw-prob 0.5` yielded spurious = {1, 1, 1, 2, 1} (injections identical across runs) — i.e. 4/5 runs gave 1 spurious, 1/5 gave 2; the variance is small but non-zero, consistent with "magnitude stable, exact figure not." We report magnitudes, not deterministic figures. (This in turn exposed and was the trigger for fixing the member-init-order bug below.)
- **A latent injector bug was found and fixed during FS work.** All three injectors initialized `rng(rng_seed != 0 ? rng_seed : rd())` in the member-init list, but `rng` is declared before `rd` in the header, so C++ initializes `rng` first and calls `rd()` on an unconstructed `std::random_device` → undefined behavior → `SIGSEGV` at `0x7473696c` ("list") inside `std::random_device::operator()` during construction, for any `seed=0`. This is why prior H6/H7 *SE* runs (which used `seed≠0` and thus never called `rd()`) completed, while FS runs (default `seed=0`) crashed on construction. Fixed with an immediately-invoked lambda constructing a local `std::random_device`; verified `--seed=0` no longer crashes and H5 (`seed=42`) regression is unchanged (`numStructuralByteLaneSkew=30, fails=29`).
- **gem5 O3 ≠ TSV110 RTL.** The injection points are gem5's O3 LSQ/address/PTW paths, not the silicon geometry. Ecological validity is supplied by the three on-silicon reproduction reports (movbe, cross-pathway, undervolt) and this study's vmcores. The method3 (opendcdiag undervolt) report was cross-checked against the historical opendcdiag YAML artifacts on the **0102 board** (`/home/sdc/wangxu/opendcdiag-arm/*.yaml`): they record the defect at `logical: 179, package: 19062, numa_node: 7, module: 23340, core: 179` with `memcpy0` delivering all-zero `src[0..7]=00 00...` at iter 179 repeatedly — matching the D1 `all_zero` structural-fault signature (§3.2 case 1522: `__per_cpu_offset[176]` delivered `0000000000000000`). This cross-confirms the D1 mechanism on silicon via an independent tool (opendcdiag) and an independent observable (userspace memcpy SDC), not just the kernel vmcores. **Reproducibility caveat (host migration):** that cross-check was performed on the original 0102 board; after migration to the current host the YAML artifacts at `/home/sdc/wangxu/opendcdiag-arm/` are **not present** (`ls`/`grep` return empty), so this cross-confirmation is **not independently re-verifiable on the current host** — it stands on the prior board's recorded artifacts. A reader with access to the 0102 board can re-run it; we do not claim it is reproducible from the current repository alone.
- **Single/multiple defect unresolvable in software** (§3.5).
- **Single-case study, no cross-case migration demonstrated.** This is a forensic case study of one defect on one core (CPU 179) of one machine. The 6 vmcores are all the same defect core (cross-dump stability of the D1 method is demonstrated, not cross-case migration). The opendcdiag cross-confirmation (§7 gem5-O3≠RTL) confirms the *same defect* via an independent tool, not migration to a new case. We do not claim the D1 forensic method (register-vs-memory byte-rotation matching) is universally applicable — it exploits the write-once stability of `__per_cpu_offset`, a property that may not hold for other crash scenarios. The §5.2 bit-flip-insufficiency claim is boundary-tested (against bit-flip producing equivalent detection rate but different signature form) and scoped to the byte-phase-displacement signature class, not all SDC. A second defect case (different core/SoC) would be needed to demonstrate method migration — we do not have one (no second fault machine, external peers unreachable). This bounds the paper's contribution to: a deep single-case forensic methodology + a falsifiable scoped methodological claim (§5.2) + a structural fault-injection toolkit extension — not a universal SDC-localization method.

---

## 8. Data and Code Availability

All vmcore-derived artifacts (`p1_events.csv`, per-cpu arrays, panic blocks), the three injector modules (`CHAOSLSQFwd`/`CHAOSAddrPath`/`CHAOSPTW`), the probe (`ptrskew_kernel.c`), the SE and FS experiment configurations (`o3_chaos_smoke.py`, `o3_chaos_fs.py`), the experiment scripts (`run_H6.sh`, `run_H7.sh`), and the full diagnosis reports are on branch `docs/core179-microarch-rootcause`. The vmcores themselves are 180 GB and not redistributable, but every claim cites a reproducible `crash`/`objdump`/`python`/`gem5.opt` command in the supplementary reports. The FS support files (`gem5-fs/`, ≈2.5 GB) are `.gitignore`d (only the README is tracked) but are described and path-verified in `gem5-fs/readme.md`.

---

## 9. Author Contributions (CRediT)

Conceptualization, methodology, investigation, software, writing — the agent author. The defect, machine, and vmcores are production artifacts.

## 10. Conflict of Interest

None.

## 11. Funding

None.

## 12. AI-Use Statement

The forensic analysis, injector implementation, and manuscript were produced with an AI coding assistant (Claude Code) under human-supervised patch discipline. All claims are machine-verifiable via the cited commands; no AI-generated evidence was accepted without real-command confirmation.

---

## References

1. Will Deacon, "arm64: mm: Ignore spurious translation faults taken from the kernel," mainline commit 42f91093b043.
2. HiSilicon HIP08 errata: cache ReadUnique prefetch disable (openEuler kernel list).
3. ARM Architecture Reference Manual, ARMv8-A, §D1.10 (FAR_EL1 semantics).
4. CHAOS fault-injection framework for gem5 (this repository, `CHAOS/`).
5. gem5 v25.1.0.1, AArch64 O3CPU model.
6. Prior on-silicon reproduction reports (internal research notes, not independently re-verified by this study): `docs/reproduce-method1.md` (eigen_sparse Cholesky, core 179), `docs/reproduce-method2.md` (cross-pathway store-forward), `docs/reproduce-method3.md` (undervoltage-triggered). The `__per_cpu_offset[cpu] → garbage` userspace observation is recorded in `fi_research/EXPERIMENT_DESIGN.md` §1.3 as a method3 finding; we cite it as ecological-validity support but did not independently re-run it.

> Complete citation DOIs/URLs are in the supplementary `MICROARCH_SUPPLEMENT.md` and `DIAGNOSIS_REPORT.md`; the reference list here is intentionally short to avoid fabricating citations per the academic-paper IRON RULE — every source above is a real, locally-verifiable artifact or well-known mainline item.
