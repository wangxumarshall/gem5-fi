# ARM64 SDC Fault-Injection Implementation — Status & Provenance

This document records the honest implementation status of the ARM64 SDC
fault-injection study defined in `docs/arm64-fi-plan-based-on-CHAOS.md`,
as implemented on branch `arm64-sdc-base` (off `fi`). Every claim below
corresponds to a real gem5 command whose output was captured and quoted
in the commit message of the patch that introduced it.

## What is DONE (verified, committed, pushed)

All work is one-patch-per-unit (CLAUDE.md patch discipline), each verified
with REAL commands before commit (build clean + functional + regression).

| Commit | Unit | Real verification |
|---|---|---|
| `95bb6ac` | Patch 0a — clean base | `scons build/ARM/gem5.opt -j16` → "scons: done building targets."; source==binary (CHAOSPhysReg/CHAOSRAT correctly MISSING); reg_chain golden `f247ef3fe6f02cfd` on O3 |
| `f2a20bf` | Patch 0b — CHAOSPhysReg + o3 hooks (restored from main `6585f7a`) | 3 modes (phys/arch_frontend/arch_commit) work; phys idx 50 → Inactive; arch_frontend reg9 → PhysReg[106] injects; read-trace |
| `3b8c33c` | G0 — reproducible RNG | 20/20 field-identical replay (seed=20260825 → reg[9] bit 20 every run) |
| `54f31cd` | G1 — width-aware masks | bit 0/31/32/63 all injectable (64-bit mask, no signed-shift UB); XZR(integer[31]) → Inactive |
| `e5eecbb` | G2 — permanent stuck-at | PhysRegFile::setReg write-path mask; stuck persists across rename reuse+overwrite (PhysReg[80] reused → `00ff` prefix, mask re-applied) |
| `ea6b192` | G3 — cache safe interface | unsafe `static_cast<CacheAccessor*>` removed; supported public `Cache::getTags()` accessor |
| `9870e9f` | G4 — memory correctness | CHAOSMem weights fixed ({bf,bf,so}→{bf,sz,so}); 20-run dist 11bf/9sz/0so≈0.5/0.5/0.0; last byte/single-byte interval reachable |
| `d44982f` | G5 — single-fault + evidence log | CHAOSMem/CHAOSCache maxFaults added (was uncapped, logged 52M injections in 1 tick); now exactly 1; log has old/new/mask/width/seed/count |
| `4e8045f` | G6 — ≥1-cycle interval | geometric dist clamped ≥1 (was degenerate same-tick re-fire at p=1.0); distinct ticks now 1000 apart |
| `e01c9f1` | G7 — no CHAOS-source warnings | `-Wswitch` Random case added; CHAOSReg/Cache/Mem compile warning-clean under -Wall/-Wextra/-Wundef |
| `a9d4130` | Patch 9 — manifest runner | schemas/manifest.schema.json + manifests/*.yaml + tools/runner.py; end-to-end: classified reg[9] flip as Masked, G5 asserted |
| `8cbf7b6` | P0 BM-GPR pilot — FIRST REAL SDC | arch_frontend scan X0-X9, n=10: **X2 SDC `bcd3c78e2ed7de1b`, X3 SDC `d43a25d7fcc218b7`**; 2/10=20% pilot (no CI at n=10) |

Phase 1 §8.3 golden stability: 5× no-injection reg_chain → 1 unique checksum
`f247ef3fe6f02cfd` (stable; cell eligible for campaign).

## What is the platform / build

- gem5 v25.1.0.1 (commit `62c7bf284864b83f7308f5e14ca9c80812621c29`) vendored
  as plain files under `CHAOS/gem5/`. Built natively on an **aarch64**
  host (openEuler, gcc 12.3.1 — NO cross-compiler needed; `gcc -static`
  produces AArch64 ELF directly).
- gem5.opt: `CHAOS/gem5/build/ARM/gem5.opt` (build with `-j16`; `-j126`
  OOM-kills on this 29 GB host — see memory gem5-build-j126-oom-29gb).
- SE config: `configs/se/arm_chaos.py` uses gem5 v25 stdlib `SimpleBoard`
  + `PrivateL1PrivateL2CacheHierarchy` + `SimpleProcessor(O3, ARM)`.
  CHAOSReg/CHAOSPhysReg attach to the cpu; CHAOSMem to `memory.mem_ctrl[0].dram`.
- Workloads: `workloads/directed/{hello,reg_chain,stuck_persist}` (native
  aarch64 static). reg_chain golden = `f247ef3fe6f02cfd`.

## Honest deferrals (NOT claimed as done)

Per the plan's phased structure, these are follow-up patches, not this phase:
- G6 broad triggers: pc / committedInst / semantic-event (need deep O3 hooks
  beyond the firstClock trigger). Done: ≥1-cycle interval + tick/cycle.
- G7 full sanitizer (ASan/UBSan) build + explicit SimulatorError classifier
  at the per-run level (the classifier exists in the runner; sanitized gem5
  rebuild is heavy and deferred). Done: warning-clean CHAOS compilation.
- L1I/L1D cache functional end-to-end: the stdlib `SimpleBoard` does not
  expose its L1D Cache SimObject for pre-instantiate CHAOSCache attachment
  (the cache SimObjects are created lazily inside `Simulator` and are not
  reachable from the hierarchy's `_root` CacheNode tree before instantiate).
  An explicit `ArmSystem()+ArmTimingSimpleCPU` config with classic L1D
  ALSO fails on gem5 v25: the MMU `release_se` param does not resolve
  (`Error in unproxying param 'release_se' of system.cpu.mmu`) — the stdlib
  `SimpleBoard` resolves this implicitly for the CPUs it creates, but that
  implicit release-wiring is not reproducible in a hand-written explicit
  config without reverse-engineering the stdlib CPU factory. The G3 supported
  accessor (`Cache::getTags()`) is correct and compiles; a directed cache
  test config is blocked on this stdlib/ARM-release interaction and is the
  first deliverable of a dedicated cache-integration patch. The GPR/mem
  paths (which use stdlib SimpleBoard directly) are NOT affected and work.
- Formal P0 cells: per-cell n=384 (GPR by ABI role × bit-field [0:11]/
  [12:47]/[48:63] × bit 31/32/63 boundary), golden 5×, raw/no-protection.
  Done: the pilot (n=10) proving reachability + real SDC.
- Phases 2-7: NEON/Vec (needs VecRegContainer path, not RegVal), TLB/SYS,
  LSQ forwarding (CHAOSLSQFwd exists on origin/docs/core179-microarch-rootcause),
  L3 128B paired-sector proxy, x86-64 paired control, Kunpeng real-machine
  RAS calibration. These are separate multi-patch phases.

## Run recipe

```bash
cd /home/sdc/gem5-fi
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
# golden (no injection)
$G5 --quiet --outdir=runs/gold configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3
# CHAOSPhysReg single-fault (arch_frontend, X3, bit_flip)
$G5 --quiet --outdir=runs/inj configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 \
    --chaos_phys --phys_mode=arch_frontend --phys_target_arch=3 \
    --probability=1.0 --first_clock=100000 --max_faults=1 \
    --rng_seed=20260825 --fault_type=bit_flip --bits_to_change=1
# manifest-driven
python3 tools/runner.py manifests/p1-gpr-regchain-000384.yaml \
    --golden-checksum f247ef3fe6f02cfd --binary workloads/directed/reg_chain
```
NOTE: put gem5 `--outdir` under `runs/` (NOT /tmp — /tmp filled up and
ENOSPC-killed a G4 test on this 29 GB host).
