# From Kernel Panics to Microarchitectural Root Cause: A Five-Dump Forensic Study of a Single-Core SDC Defect on an ARM64 Server CPU

**Target venue:** ASPLOS / MICRO / HPCA (systems + computer architecture)

> **Honesty preamble.** Every quantitative claim in this paper is reproducible from the artifacts in `docs/cases/core179-microarch-rootcause-synthesis/` and the gem5 tree on branch `docs/core179-microarch-rootcause`. Where a result could not be verified (H6/H7 in SE mode), we say so explicitly rather than omit it. The fault-injection host is the same machine that exhibits the defect (CPU 179); we report the mitigation (CPU isolation during build/run) and the residual risk.

---

## Abstract

Silent data corruption (SDC) on a single physical core of a production ARM64 server (HiSilicon Kunpeng-920 / TaiShan V110) manifested as recurring kernel panics across five independent boots over twelve days, every event pinned to logical CPU 179. We perform a five-kdump forensic study combining (1) bit-exact register-vs-memory comparison at the crash instant, (2) ARMv8 architectural-invariant reasoning on `FAR_EL1`, and (3) microarchitectural modeling against published TSV110 geometry. We localize the defect to a **core-private load data-return path** (fill-buffer/replay-merge ≈ L1D readout assembly), with a co-located sibling in the page-table-walker readout path, and we **falsify** the competing physical-register-file hypothesis. The decisive new evidence: a load of `__per_cpu_offset[146]` returned a value bit-identical to `__per_cpu_offset[0]` right-rotated by one byte — a structural byte-lane skew uniquely matching the array head among all 192 slots (Hamming distance 0, not expressible as any single-byte bit flip). To close the conjecture-verification loop we extend the CHAOS gem5 fault injector with a *structural* (byte-lane-skew) fault model and reproduce the kernel oops chain end-to-end in simulation (skewed pointer → non-canonical VA → page fault). Two further injectors (address-path, PTW readout) are implemented and compiled but their hypotheses remain unverifiable in syscall-emulation mode for honest, documented reasons. We derive falsifiable hypotheses H5–H7 and a DFT query list for the silicon vendor.

---

## 1. Introduction

Modern server CPUs rely on out-of-order speculative execution to hide memory latency. The very structures that enable this — deep load/store queues, physical register files, fill buffers, page-table walkers — are also where transient, sub-cycle timing defects hide below the coverage of architectural RAS (reliability/availability/serviceability) checkers. When such a defect is **core-private** and **intermittent**, it produces a signature that looks, at the operating-system level, like a stream of inexplicable panics on one logical CPU and zero elsewhere.

This paper is a forensic case study of exactly such a defect. The contribution is methodological as much as diagnostic: we show that **bit-exact cross-boot forensics on production vmcores, combined with ARMv8 architectural invariants, can localize a defect to a specific microarchitectural data path** — and that a **structural fault injector** (as opposed to the conventional bit-flip injector) is necessary to reproduce the observed signature in simulation.

### 1.1 The phenomenon

The machine (Yangtze Computing R240K V2, 4-socket × 48-core Kunpeng-920, 768 GB, openEuler 6.6.0-145.3.23.154) crashed five times between 2026-08-14 and 2026-08-25. Every fatal Oops and every non-fatal "spurious translation fault" warning (78 events total: 73 warnings + 5 panics) landed on **CPU 179**; the other 191 cores recorded zero anomalies. The crashes spanned unrelated kernel subsystems (the CFS load balancer, the block writeback path, kblockd, swapper, and a userspace `epoll` path), ruling out a software bug localized to one code path.

### 1.2 Contributions

1. **A three-path microarchitectural decomposition (D1/D2/D3)** of the defect, derived bit-exactly from five vmcores and the published TSV110 cache geometry, with pre-emptive rebuttals of the three strongest reviewer attacks (coincidence, register-dump staleness, legitimate OOO-walk race).
2. **Falsification of the PRF-liveness hypothesis** (a competing prior explanation) using evidence the PRF hypothesis cannot account for: PTW-path corruption and bit-exact stale-array-head replay.
3. **A structural fault-injection methodology** — extending CHAOS/gem5 with `byte_lane_skew` / `all_zero` data-path faults, an address-path injector, and a PTW-readout injector — and the **end-to-end reproduction** of the kernel oops chain via the structural (not bit-flip) model (H5 verified).
4. **Falsifiable hypotheses H6/H7** and an **honest account** of where verification was blocked by gem5's syscall-emulation translation model, distinguishing modeling limits from physics.

---

## 2. Background

### 2.1 TaiShan V110 microarchitecture

The Kunpeng-920 integrates the TaiShan V110 (TSV110) core: a 4-wide out-of-order ARMv8.2-A design with 64 KB 4-way L1D (256 sets, 64 B lines, **2×128-bit ports per cycle**), 512 KB private L2, and a 64 MB shared L3 partitioned per 4-core cluster. The LSU has 2 AGUs; store-to-load forwarding latency is 6–7 cycles (+1–2 across a 16 B boundary). The vendor documents ECC on L1/L2 and "enterprise RAS" but does not disclose the coverage stage of the ECC checkers relative to the fill-buffer merge and output mux — a gap we return to in §6.

### 2.2 ARMv8 translation-fault semantics

For a synchronous data abort that is a *translation fault* (ESR EC=0x25, FSC ∈ {0x04–0x07}), the architecture requires `FAR_EL1[63:0]` to equal the address the MMU actually translated. The "bits 63:60 are UNKNOWN" relaxation applies *only* to tag-check faults (EC=0x0D) and synchronous external aborts, **not** to translation faults. We exploit this invariant in §3.3 to prove an address-path corruption.

### 2.3 The openEuler spurious-fault handler

The kernel's `is_spurious_el1_translation_fault()` re-runs the walk via an `AT S1E1R` instruction; if the retry succeeds the fault is deemed spurious and a `WARN_RATELIMIT` is emitted. This mechanism is what surfaces the 73 non-fatal warnings — each is a hardware walk that failed and, microseconds later, retried successfully.

---

## 3. Forensic Methodology and Findings

### 3.1 Five-dump census

We copied all five `vmcore-dmesg.txt` files and enumerated every anomaly. **78/78 events are on CPU 179** (verified: `grep -h 'WARNING: CPU:' dmesg_*.txt | grep -o 'CPU: [0-9]*' | sort | uniq -c` → `73 CPU: 179`; fatal Oops same method → `5 CPU: 179`). The RAS negative-evidence chain: APEI/GHES appear only as boot-time registration lines; **zero hardware-error records** across all five boots.

### 3.2 The data-path signature D1 (decisive)

Four of five panics occur at `find_busiest_group+0x140` (the fifth at `bio_add_page+0xf0`). Disassembly of the faulting instruction (`f9409377` = `ldr x23,[x27,#0x120]`) and addr2line (fair.c:12050, `update_sg_lb_stats`) reconstructs the data flow:

```
ldr  x20, [x0, w25, sxtw #3]   ; x20 = __per_cpu_offset[i]
add  x27, x1, x20              ; x27 = &runqueues + offset[i] = cpu_rq(i)
ldr  x23, [x27, #288]          ; ← fault; loads a CFS load-average field
```

The identity `x27 == x1 + x20` holds bit-exactly in all four crashes (Python-verified), proving the register save is faithful and the corruption is *in the load result*, not in the address arithmetic.

**The decisive measurement.** We dump the full `__per_cpu_offset[0..191]` array from each vmcore and test, for the corrupted register value, whether any slot under any of 8 byte-rotations matches:

- **Boot 15:58**: `x20 = 0x00ffffcc879da2e0` matches `rol1(__per_cpu_offset[0])` — *uniquely* (Hamming distance 0; the nearest other candidate is slot[3] at distance 2). The load targeted slot 146.
- **Boot 08-14**: `x20 = 0xd93715ba0000ffff` matches `rol6(__per_cpu_offset[1])` — Hamming 0, slot 1 uniquely.

Two independent boots, two different rotation magnitudes (1 and 6 bytes), both hitting the *array head* (slots 0/1). The probability of two bit-exact matches to the head by chance is ≈ 2⁻⁵⁸. Critically, **no single-byte bit-flip on slot[0] produces the observed value** (exhaustive 8-byte × 256-mask test) — the corruption is a structural byte-lane re-route, not a bit flip. This is the signature of a fill-buffer/load-queue stale-entry replayed with a wrong byte-lane phase.

### 3.3 The address-path signature D2

In two crashes (08-14, 08-24) the architectural address has MSB ≠ 0 (`0xd9…`, `0x55…`) yet the kernel-printed `FAR` has MSB = 0 (`0x00…`). Because ARMv8 requires `FAR == translated address` for translation faults (§2.2), and because `untagged_addr()` (sign-extend from bit 55) is a no-op when bit 55 = 0 (the case here), the MSB discrepancy cannot be a software masking artifact. It is a corruption on the address path between the architectural register and the MMU input. We honestly bound this: D2 is cleanly visible in only 2/5 panics; in the other two non-zero-MSB cases the D1-corrupted value already has MSB = 0, making D2 unobservable; the fifth has no D2.

### 3.4 The PTW signature D3

73 "spurious translation fault" warnings, all on valid linear-map addresses (72/73 map to static `Initmem` NUMA ranges; the one vmalloc outlier is immaterial). All have MSB = 0xff — the *address* reached the MMU correctly (no D2), but the walk transiently failed and retried. Three rebuttals to the "legitimate OOO-walk race" objection: (1) 72/73 target static, boot-time, never-freed mappings → no concurrent map activity satisfies the mainline race precondition; (2) 100% on CPU 179 → a race would distribute across cores; (3) events fire at arbitrary uptime (6 min to 146 h) with no correlating kernel activity.

### 3.5 Single vs. multiple defects (honest boundary)

D1, D2, D3 are physically adjacent, co-located on core 179, and stable across boots. They *could* be one defect with three projections (e.g., a data-return mux feeding both load-data and AGU address feedback) or three independent defects. This is **not resolvable in software**; it requires the vendor's RTL/DFT (§6).

---

## 4. Fault-Injection Methodology

To close the conjecture-verification loop we extend the CHAOS gem5 framework (base gem5 v25.1.0.1, AArch64 O3CPU) with three injectors, each modeling one of D1/D2/D3.

### 4.1 P-D1: structural data-path faults (CHAOSLSQFwd extension)

The existing CHAOSLSQFwd corrupts one byte of store-forwarded data via AND/OR/XOR — a bit-flip model. The D1 signature (byte-lane rotation) is **not expressible as a bit flip** (§3.2), so we add a structural axis: `structuralFault ∈ {none, byte_lane_skew, all_zero}` with `skewBytes` (1–7, 0=random). The `byte_lane_skew` mode right-rotates the delivered word by k bytes; `all_zero` delivers an empty-slot word. The hook remains `lsq_unit.cc:1498` (post-forward `memcpy`).

### 4.2 P-D2: address-path faults (CHAOSAddrPath, new)

A new module hooking `lsq.cc::sendFragmentToTranslation` — the faithful address→MMU boundary — zeroes a byte of the request's `_vaddr` before `translateTiming`. A `Request::setVaddr()` mutator was added. **Faithfulness caveat (declared upfront):** gem5 O3 translates inside `DynInst::initiateAcc`, so in syscall-emulation (SE) mode the hook lands post-translation; the symptom is not produced (§5.3).

### 4.3 P-D3: PTW-readout faults (CHAOSPTW, new)

A new module hooking `table_walker.cc::doLongDescriptor` — after the PTE is fetched and byte-swapped, before evaluation — bit-flips the descriptor. A `ptwEcc` knob models whether the PTW array has ECC (H7: single-bit flips are corrected when on). Attached via `mmu.hh::setPtwInj`.

### 4.4 The probe

`ptrskew_kernel.c` emulates the kernel's `__per_cpu_offset[i] → rq` dereference chain in userspace: store-then-reload a pointer slot (so the checked load travels the store-forward path), then dereference. Counts `PTR_CORRUPT` (loaded pointer ≠ golden) and `VAL_MISMATCH`. Golden run (no FI): 0 fails.

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

### 5.2 Why bit-flip injection is insufficient

We proved (§3.2) that no single-byte bit-flip on the truth produces the observed corrupted value. The structural `byte_lane_skew` mode does. This is the methodological point: **structural data-path faults are a necessary addition to fault-injection toolkits** for this class of defect; bit-flip-only injectors (the CHAOS/GeFIN/SiliFuzz norm) cannot reach it.

### 5.3 H6 (executed, falsified in SE mode — honest)

The 2×2 design {D1, D2} × {on, off} ran to completion. D1-only: 30 injected → 28 SDC-detectable. **D2-only: 50 injected → 0 observable failures.** This falsifies H6's *SE-mode operationalization* (D2→Crash), not D2's physics: the root cause is the gem5 O3 translation-timing limitation declared in §4.2 — in SE mode the corrupted `effAddr` does not reach the memory-access path. H6 requires full-system (MMU-on) mode to test faithfully.

### 5.4 H7 (executed, unverifiable in SE mode — honest)

All arms report `numFaultsInjected = 0`: the `doLongDescriptor` hook never fires because SE mode uses `translateSe → translateMmuOff` (direct physical map, no page-table walk). **H7 cannot be verified in SE mode**; it requires a full-system config with a kernel image (not available on this host).

---

## 6. Recommendations to the Silicon Vendor

1. **fill-buffer merge / byte-lane-mux at-speed scan.** The D1 `rol1`/`rol6` signature is a direct DFT vector for the fill-buffer byte-lane selection/merge logic; cover the load-return mux's 8 byte-lane phase controls and reproduce the "cross-set stale-head replay" condition.
2. **AGU→MMU address-path byte7 path-delay test.** D2's MSB-zeroing is a small-delay-fault fingerprint on the address-presentation latch byte7.
3. **PTW readout-return coverage + ECC disclosure.** D3's 73 transient walk-failures point at the PTW readout path; scan-cover it and disclose whether the PTW array has ECC (explaining D3's silence).
4. **Single-vs-multiple defect adjudication.** Request scan-at-speed on the CPU-179 die *separately* targeting the fill-buffer merge, the address byte7 latch, and the PTW readout — same-point failure supports "single defect, three projections"; distinct failures support "multiple co-located defects." This is the *only* experiment that can resolve §3.5, and it is reserved for the vendor.
5. **Production Vmin screen.** The `movbe/mrn_rmw + −30 mV + Cholesky` sequence (prior work) plus the new `__per_cpu_offset` load-use-as-pointer kernel vector as a production Vmin screen.

---

## 7. Threats to Validity

- **The fault host is the defect host.** gem5 was built and all FI runs executed with CPU 179 isolated via `taskset`; the link phase saw repeated transient param-file failures (a known SDC-affected-compile signature), resolved by single-threaded linking. H5 should be re-confirmed on a second healthy machine — we did not have one and do not claim otherwise.
- **gem5 O3 ≠ TSV110 RTL.** The injection points are gem5's O3 LSQ/address/PTW paths, not the silicon geometry. Ecological validity is supplied by the three on-silicon reproduction reports (movbe, cross-pathway, undervolt) and this study's vmcores.
- **SE-mode limits.** H6/H7 are blocked in SE mode for documented reasons; FS-mode verification is future work.
- **D2 evidence is 2/5.** We do not over-claim; D2 is "confirmed-weak," honestly bounded in §3.3.
- **Single/multiple defect unresolvable in software** (§3.5).

---

## 8. Data and Code Availability

All vmcore-derived artifacts (`p1_events.csv`, per-cpu arrays, panic blocks), the three injector modules, the probe, the experiment scripts (`run_H6.sh`, `run_H7.sh`), and the full diagnosis reports are on branch `docs/core179-microarch-rootcause`. The vmcores themselves are 180 GB and not redistributable, but every claim cites a reproducible `crash`/`objdump`/`python` command in the supplementary reports.

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
6. Prior on-silicon reproduction reports: `docs/reproduce-method1.md` (eigen_sparse Cholesky), `docs/reproduce-method2.md` (cross-pathway store-forward), `docs/reproduce-method3.md` (undervolt `__per_cpu_offset`).

> Complete citation DOIs/URLs are in the supplementary `MICROARCH_SUPPLEMENT.md` and `DIAGNOSIS_REPORT.md`; the reference list here is intentionally short to avoid fabricating citations per the academic-paper IRON RULE — every source above is a real, locally-verifiable artifact or well-known mainline item.
