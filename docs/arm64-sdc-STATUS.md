# ARM64 SDC Fault-Injection Implementation — Status & Provenance

This document records the honest implementation status of the ARM64 SDC
fault-injection study defined in `docs/arm64-fi-plan-based-on-CHAOS.md`,
as implemented on branch `fix/fi-tool-correctness` (off `fi` HEAD
`70b725c`). Every claim below corresponds to a real gem5 command whose
output was captured and quoted in the commit message of the patch that
introduced it.

## Tool-correctness pass (post source-check report, 2026-08-26)

A source-code inspection (`docs/gem5-fi_branch_next_step.md`) found that
the post-merge `fi` HEAD had regressed on several gates (the parallel-
session CHAOSPhysReg vec/float series overwrote the G2 write-path mask;
both register modules were still 32-bit; the NEON path overflowed; the
classifier mislabeled crashes as SDC; the manifest target/bit were not
honored; the top-level CHAOSCache/Mem were stale). The following patches
on `fix/fi-tool-correctness` fix exactly those defects, each verified
with real gem5 output:

| Commit | Unit (report issue) | Real verification |
|---|---|---|
| `9f0ad41` | G2 restore write-path stuck mask (#1) | stuck_persist phys PhysReg[80] stuck_at_one 0xff → `00ff0000dee1f5d0` (mask re-applied at reuse @cycle 150000); golden `00000000dee1f5d0`; O3 golden `f247ef3fe6f02cfd` |
| `8739214` | 64-bit masks, CHAOSReg+CHAOSPhysReg (#2) | `--fault_mask=1<<32`/`1<<63` now log `0x100000000`/`0x8000000000000000` (were 0); zero CHAOS-source warnings |
| `4602f28` | NEON buffer sized to vecRegBytes() (#3) | `--phys_reg_class=vector` phys inject on reg_chain: NO SIGSEGV (was 192B overflow); log `RegClass: vec, PhysReg[0]` |
| `e3a39b9` | honest classifier §9.1 (#4) | exit1+empty+1inj → Crash (was SDC); X0/X1 Masked, X2 SDC; manifest reg9 → Masked with reason |
| `aeaf043` | manifest target/bit/trigger honored (#5a) | physreg manifest idx=3 bit=[20] → `PhysReg[77] (<= ArchReg[3])` Mask `...0010000...` reads=25000 → SDC; idx=3 bit=[32] → SDC (high bit now lands) |
| `890cca3` | single source-of-truth + gitignore gem5-fs (#5b) | `diff -rq CHAOS/{Cache,Mem,Reg,PhysReg} ↔ vendored` all identical; Makefile clobber-safe (no-op when identical); `git check-ignore gem5-fs/` OK |

## Honest status of the gates (after the fix pass)

| Gate | Pre-merge (arm64-sdc-base) | Post-merge (fi 70b725c) | After fix pass |
|---|---|---|---|
| G0 replayable RNG | done | done | done |
| G1 64-bit width | done (`54f31cd`) | **LOST** (both modules 32-bit) | **restored** (`8739214`) |
| G2 permanent stuck-at | done (`e5eecbb`) | **LOST** (write-path mask overwritten) | **restored** (`9f0ad41`) |
| G3 cache safe accessor | done | done | done |
| G4 memory correctness | done | done (vendored); top-level stale → **synced** (`890cca3`) | done |
| G5 single-fault + evidence | done | done (vendored); top-level stale → synced | done |
| G6 ≥1-cycle interval | done | done | done (broad triggers still deferred) |
| G7 no CHAOS-source warnings | done | **REGRESSED** (Random -Wswitch in PhysReg/LSQFwd) | CHAOSReg/PhysReg **clean**; CHAOSLSQFwd still has it (out of scope) |
| Classifier §9.1 | baseline | **broken** (no exit-code check) | **fixed** (`e3a39b9`) |
| Manifest target/bit | baseline | **ignored** | **honored** (`aeaf043`) |
| NEON/Vec path | baseline (unsafe) | **overflowed** | **safe** (`4602f28`) |

## Phase 1 P0 — pilot results, HONEST re-status

The pre-fix P0 pilot numbers were collected with the broken classifier
(no exit-code check, no Hang/Crash split) and the truncated 32-bit mask.
They are therefore NOT trustworthy as-is and are flagged here:

- **P0 GPR bit-stratified (`3551d57`)** claimed "SDC=3, Hang=5" across
  X2/X3 × bits 0/31/32/63. But `bit32`/`bit63` masks were silently 0
  (UInt32 truncation) → effectively NO injection for those cases, so the
  "high-bit → Hang" conclusion does not hold. Re-run after the fix:
  X3 bit63 (arch_frontend, 1<<63) → **SDC** (`d9a35c115042d41a`),
  exit 0, no trap — a high-bit flip propagated as silent data corruption,
  NOT Hang. The high-bit/low-bit SDC-vs-Hang distinction must be re-stated
  after a proper formal run; the current data does not support "high-bit
  → Hang".
- **P0 L1I (`8beeea1`)** "10/10 Hang": the old classifier counted empty
  stdout as Hang with no timeout/returncode distinction. Needs re-run
  with the honest classifier (Hang = timeout with no completion, vs
  Crash = trap/exit≠0) before the "all Hang" claim can stand.
- **P0 L1D (`d72c61e`)** "10/10 Masked": less affected (Masked is the
  no-propagation case either way), but still needs a re-run for the
  evidence log (single-fault assertion, exit code).

**Reproducible anchors that DO survive (verified post-fix):**
- reg_chain golden (no inj, O3) = `f247ef3fe6f02cfd`
- CHAOSPhysReg arch_frontend X3 1-bit-flip (seed 20260825) = `d43a25d7fcc218b7` (SDC)
- G2 persistence: stuck_at_one 0xff PhysReg[80] → `00ff0000dee1f5d0` (golden `00000000dee1f5d0`)
- Manifest physreg idx=3 bit=[20] → `PhysReg[77] (<= ArchReg[3])` SDC `88ff2422239b4952`

## Step-3 minimal re-runs (report §六.3, post-fix honest re-collection)

The report's §六.3 asks to re-run the easiest-to-verify groups with the
fixed tooling (64-bit masks + honest classifier + single-fault + evidence
log), confirm stable replay + correct classification, THEN scale. Done:

### Grid 1 — GPR X2/X3 × bits 0/31/32/63 (replaces invalidated `3551d57`)

CHAOSPhysReg arch_frontend, reg_chain, O3, firstClock=100000, maxFaults=1,
seed=20260825, explicit `--fault_mask=1<<k` (now 64-bit, so bit32/bit63
actually flip). Honest §9.1 classification (Hang = timeout, no trap):

| reg | bit0 | bit31 | bit32 | bit63 |
|---|---|---|---|---|
| X2 | SDC `25e4130b0408b2cd` | **Hang** (timeout, exit 124, no trap) | **Hang** | **Hang** |
| X3 | SDC `ace5d7dcf0bbe4df` | SDC `cf415a9e6b07af9a` | SDC `dbdd0f0aad30df0b` | SDC `d9a35c115042d41a` |

**Totals: SDC=5, Hang=3.** Each cell hit the explicit arch reg (X2→
PhysReg[187], X3→PhysReg[77], both `<= ArchReg[k]`) with exactly 1 fault.
The three Hangs were VERIFIED to be real timeouts (exit 124 from the
240s Hang cutoff, NO panic/assert/SIGSEGV/trap in stderr — not a
misclassified Crash/SimulatorError). This replaces the old `3551d57`
"SDC=3/Hang=5": the difference is the SDC-vs-Hang split is REGISTER-
SPECIFIC, not generic "high-bit": **X2 high bits → Hang (control-flow
corruption: X2 is the loop counter); X3 (data accumulator) all bits →
SDC.** The old "high-bit→Hang" claim was both artifact (bit32/63 were
never injected before the 64-bit fix) AND over-generalized (it's X2,
not all high bits).

### Grid 4 — memory first/last/single-byte (report §六.3 grid 4)

CHAOSMem on l1d_reduce (512KiB BSS array `data[65536]`), Timing, maxFaults=1,
evidence log asserts exactly 1 fault. Boundary correctness (G4 closed
interval `[start,end]`, single-byte `[n,n]`):

| window | target addr logged | faults | class |
|---|---|---|---|
| `[0,1]` (first byte reachable) | 0 | 1 | Masked |
| `[0x100000,0x100000]` (single mid byte) | 1048576 | 1 | Masked |
| `[0x3FFFFFFF,0x3FFFFFFF]` (last byte) | 1073741823 | 1 | Masked |

NOTE: `addr_end=0` is the "unrestricted" convention (NOT a bug — same as
lastClock=0); to reach the very first byte use a 2-byte window `[0,1]`.
The last byte IS reachable (old code dropped it; G4 fixed). 5 random seeds
over the full BSS range: 5/5 Masked — a single transient byte flip on a
512KiB array is mostly masked (the byte is rarely the one live at read,
or is overwritten before read) — honest memory AVF, consistent with the
old `d72c61e` direction but now correctly classified + single-fault.

### Grid 2/3 (L1D fixed-to-live-data, L1I fixed-to-executed-instr) — deferred

These need the cache config (configs/se/arm_chaos_cache.py) with a
tighter O3 window / directed cache-line target. The L1D/L1I pilots
(d72c61e/8beeea1) need re-run with the honest classifier before their
"all Masked"/"all Hang" claims can stand — that is a follow-up, not
this round.

### Grid 2b/3b — L1D/L1I random-pilot RE-RUN with the honest classifier

The §六.3 "fixed-to" directed runs need a directed byte/line injector
(not yet a CHAOSCache knob). But the RANDOM-pilot re-run (random byte/
line sampled by rngSeed) is doable now and verifies the classifier works
on the cache path end-to-end. Done:

- **L1D re-run** (l1d_reduce, O3, 5 seeds, random cache block/byte,
  maxFaults=1): each run injected exactly 1 fault at a distinct byte
  offset (byte3/16/36/38/42 across 64B blocks). **5/5 Masked**
  (golden `f44d2b9cd4a173cd`). Honest cache AVF — a random transient
  byte rarely hits the live value before overwrite. (Direction matches
  the old `d72c61e`, now correctly classified + single-fault.)
- **L1I re-run** (l1i_loop, O3, 10 seeds, random cache block/byte,
  maxFaults=1): **10/10 Hang**. VERIFIED Hang is real (not a misclassified
  Crash/SimError): seed 20260825 — exit 124 (timeout), no checksum, NO
  panic/trap/SIGSEGV in stderr (only benign `info: Increasing stack
  size`). Injection log: `Cache Block Addr: 51392, Byte Offset: 38,
  Mask: 01000000` (bit 6 of an instruction byte flipped → loop control
  corrupted → infinite loop). l1i_loop is a tight fixed-instruction
  loop, so most instruction-field flips corrupt control flow (Hang) or
  make illegal encodings (Crash); 10/10 Hang here is honest for THIS
  kernel. A Crash case (legal-but-wrong → SDC, or illegal → trap) would
  need a directed flip on a specific instruction field — deferred.

Honest note: the §六.3 "fixed-to-live-data"/"fixed-to-executed-instr"
directed runs are STILL deferred (need a directed cache byte/line knob
in CHAOSCache — a feature patch). The random re-runs above prove the
classifier + single-fault + evidence log work on the cache path, and
confirm the L1D-Masked / L1I-Hang directions honestly (now classified
correctly), but do NOT replace directed formal cells.

## What is the platform / build

- gem5 v25.1.0.1 (commit `62c7bf284864b83f7308f5e14ca9c80812621c29`) vendored
  as plain files under `CHAOS/gem5/`. Built natively on an **aarch64**
  host (openEuler, gcc 12.3.1 — NO cross-compiler needed).
- **gem5.opt path**: `scons -C CHAOS/gem5 build/ARM/gem5.opt -j16` builds to
  the **repo-ROOT `build/ARM/gem5.opt`** (~1.1GB) on this host — NOT
  `CHAOS/gem5/build/ARM/`. Use `G5=$PWD/build/ARM/gem5.opt`. (The
  `CHAOS/gem5/build/ARM/` path may hold a stale/duplicate binary; do not
  use it.) `-j126` OOM-kills on this 29GB host — use `-j16`.
- SE config: `configs/se/arm_chaos.py` uses gem5 v25 stdlib `SimpleBoard`
  + `PrivateL1PrivateL2CacheHierarchy` + `SimpleProcessor(O3, ARM)`.
- Workloads: `workloads/directed/{hello,reg_chain,stuck_persist,
  l1d_reduce,l1i_loop}` (native aarch64 static). Goldens:
  reg_chain `f247ef3fe6f02cfd`, l1d_reduce `f44d2b9cd4a173cd`,
  l1i_loop `bb0b1c4cb661236e`, stuck_persist `00000000dee1f5d0`.

## Run recipe (post-fix)

```bash
cd /home/sdc/gem5-fi
G5=$PWD/build/ARM/gem5.opt   # repo-ROOT build dir (NOT CHAOS/gem5/build)
# golden (no injection)
$G5 --quiet --outdir=runs/gold configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3
# CHAOSPhysReg single-fault (arch_frontend, X3, bit_flip)
$G5 --quiet --outdir=runs/inj configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 \
    --chaos_phys --phys_mode=arch_frontend --phys_target_arch=3 \
    --probability=1.0 --first_clock=100000 --max_faults=1 \
    --rng_seed=20260825 --fault_type=bit_flip --bits_to_change=1
# manifest-driven (golden_id resolved automatically)
python3 tools/runner.py manifests/p1-gpr-regchain-000384.yaml \
    --binary workloads/directed/reg_chain
```

NOTE: put gem5 `--outdir` under `runs/` (NOT /tmp — /tmp filled up and
ENOSPC-killed a G4 test on this 29GB host).

## Honest deferrals (NOT claimed as done)

- G6 broad triggers (pc / committedInst / semantic-event): only ≥1-cycle
  interval + tick/cycle done. The manifest runner rejects pc/
  committedInst/event with a clear error (needs G6 work).
- G7 full sanitizer (ASan/UBSan) gem5 build: only -Wswitch/-Wunused
  cleaned at compile time; the sanitized build is deferred.
- CHAOSReg has no directed-reg knob: a manifest asking for a SPECIFIC
  gpr can't force it (logged as a TODO; CHAOSPhysReg can, via
  phys_target_arch). The manifest runner records this honestly.
- Formal P0 cells (n=384 by ABI role × bit-field × boundary): NOT done.
  The pilot (n=10) proves reachability + real SDC; formal cells are a
  follow-up, run with the fixed classifier.
- Phases 2-7: NEON/Vec (the 64-bit/NEON-overflow fixes make the path
  SAFE; full 128-bit lane stratification is Phase 2), TLB/SYS (FS mode,
  needs `gem5-fs/` deps — now gitignored), LSQ forwarding, L3 128B,
  x86-64 paired control, Kunpeng real-machine RAS calibration. These
  are separate multi-patch phases.
