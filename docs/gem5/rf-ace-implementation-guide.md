# RF ACE Metric Implementation Guide

Purpose: implement Register File ACE lifetime coverage in gem5 O3/CHAOS to reproduce the Harpocrates RF ACE metric. ACE is a hardware coverage/fitness proxy, not the final SFI detection rate.

Target metric:

```text
ACE_RF = sum(ACE bit cycles) / (num_physical_regs * reg_width_bits * measured_cycles)
```

ACE meaning: if a transient bit flip in an RF bit during a cycle can affect architecturally correct execution, that bit-cycle is ACE. Otherwise it is un-ACE.

## Paper Constraints

1. ACE is for bit-array/storage structures: register files, caches, queues, and similar arrays.
2. ACE lifetime requires time. Track whether each bit is ACE or un-ACE across cycles.
3. For RF, the practical ACE interval is the producer-written value lifetime until consumer reads:
   - write-to-read interval counts as ACE.
   - read-to-read interval can also count when the same value has multiple consumers.
   - a value never read before overwrite/free is un-ACE.
4. Squashed wrong-path producer or consumer effects must not increase ACE.
5. Overwritten, freed, or never-read values are un-ACE.
6. ACE coverage is an upper-bound-like proxy for detection capability. Do not report it as SDC detection rate.
7. Measure only the target test body. Exclude init, warmup, wrapper, signature, and output code through a gem5 work item, magic op, or explicit tick/instruction window.

## Phase 1: Register-Granularity RF ACE

Goal: implement a stable low-intrusion approximation. Track one state per physical register entry, not one state per bit.

Start with integer physical registers only:

```text
target = IntRegClass
default_reg_width_bits = 64
```

### State

Per physical register:

```cpp
struct RFAceRegState {
    bool valid;              // phys reg currently holds a tracked value
    bool committedPath;      // value is not known to be wrong-path/squashed
    Tick lastEventTick;      // latest write/read event
    unsigned widthBits;      // effective value width, usually 32 or 64
};
```

Global counters:

```cpp
uint64_t rfAceBitCycles;
uint64_t rfTrackedReads;
uint64_t rfTrackedWrites;
uint64_t rfOverwriteDrops;
uint64_t rfSquashDiscards;
Tick rfWindowStart;
Tick rfWindowEnd;
```

### Event: Physical Register Write

Hook where an instruction result writes a destination physical register.

```text
onPhysRegWrite(phys_reg, width_bits, inst)
```

Rules:

1. Ignore if outside the measurement window.
2. If the phys reg already has a valid tracked value, end the old lifetime as overwrite/drop. Do not add ACE cycles.
3. Initialize the new state:
   - `valid = true`
   - `committedPath = !inst->isSquashed()`
   - `lastEventTick = curTick`
   - `widthBits = effective_width_bits`
4. Increment `rfTrackedWrites`.

### Event: Source Register Read

Hook where a source physical register is read for execution.

```text
onPhysRegRead(phys_reg, width_bits, inst)
```

Rules:

1. Ignore if outside the measurement window.
2. Ignore if the consumer instruction is squashed or architecturally inactive.
3. If the state is valid and on the committed path:

```text
delta = curTick - lastEventTick
rfAceBitCycles += delta * min(width_bits, state.widthBits)
state.lastEventTick = curTick
rfTrackedReads++
```

4. Keep the state valid after a read so read-to-read intervals from multiple consumers can count.

### Event: Free, Reuse, or Overwrite

Hook where a physical register is returned to the free list or overwritten by a new value.

```text
onPhysRegFreeOrOverwrite(phys_reg)
```

Rules:

1. Clear `valid`.
2. Do not add ACE cycles.
3. Increment `rfOverwriteDrops` or a more specific drop counter.

### Event: Squash

Hook where wrong-path instructions are squashed.

```text
onSquash(inst)
```

Rules:

1. For each destination physical register produced by the squashed instruction, clear the tracked state if it is still valid.
2. Do not add ACE cycles.
3. Increment `rfSquashDiscards`.

### Phase 1 Ratio

```text
measured_cycles = rfWindowEnd - rfWindowStart
denominator = num_target_phys_regs * default_reg_width_bits * measured_cycles
rfAceRatio = rfAceBitCycles / denominator
```

### Phase 1 Validation

Use directed workloads:

1. Long dependency chain should raise RF ACE.
2. Dead writes should lower RF ACE.
3. Wrong-path/squashed instructions should not raise RF ACE.
4. Higher register pressure without actual consumption should not create artificial ACE.

## Phase 2: Bit-Level RF ACE

Goal: match the paper's per-bit RF ACE lifetime semantics more closely. Support 32-bit vs 64-bit GPR behavior, partial writes, vector lanes, predicate masks, and inactive lanes.

Current implementation status: AArch64 integer GPR W/X masks are implemented
behind `--rf_ace_granularity=bit`; `whole` retains Phase 1 behavior. Vector,
predicate, and operand-specific memory masks remain future extensions.

Prefer mask aggregation first. Avoid creating heavy per-bit objects unless needed.

### State

For GPRs:

```cpp
struct RFAceBitState {
    uint64_t liveMask;          // bits currently holding tracked value
    Tick lastEventTick[64];     // exact per-bit event time
};
```

For vector/predicate registers, use lane or byte masks:

```text
byte mask for SIMD
lane mask for vector registers
predicate mask for SVE/VecPred
```

### Event: Bit-Masked Write

```text
onPhysRegWrite(phys_reg, write_mask, inst)
```

Rules:

1. `write_mask` must describe bits actually defined by the write.
2. Bits overwritten by `write_mask` end their old lifetime without adding ACE.
3. For each bit in `write_mask`:
   - mark live
   - set `lastEventTick[bit] = curTick`
4. Respect ISA semantics:
   - AArch64 32-bit `W` writes zero-extend to `X`, so high 32 bits are defined too.
   - Partial vector lane writes only define active lanes.
   - Predicated inactive lanes are not effective writes.

### Event: Bit-Masked Read

```text
onPhysRegRead(phys_reg, read_mask, inst)
```

Rules:

1. `effective_mask = read_mask & liveMask`.
2. For each bit in `effective_mask`:

```text
rfAceBitCycles += curTick - lastEventTick[bit]
lastEventTick[bit] = curTick
```

3. Predicated inactive lanes are not effective reads.
4. Zero registers and constant sources do not count as RF ACE.

### Event: Bit-Masked Free, Overwrite, or Squash

Rules:

1. Clear affected live bits.
2. Do not add ACE cycles.
3. For squashed producers, discard the produced destination mask.

### Phase 2 Ratio

```text
rfAceRatio =
    sum(per-bit ACE cycles)
    / (num_target_phys_regs * reg_width_bits * measured_cycles)
```

Recommended extra stats:

```text
rfAceRatioInt
rfAceRatioFp
rfAceRatioVec
rfAceBitCyclesLow32
rfAceBitCyclesHigh32
```

## Implementation Boundaries

Do not:

1. Mix ROB, IQ, or LSQ lifetimes into RF ACE.
2. Treat committed architectural-register observation as a physical RF read.
3. Count init, wrapper, output, or signature code in the target window.
4. Mix fault injection detection rate with ACE coverage.
5. Claim Phase 1 is bit-accurate.

## Required Stats

At minimum, emit:

```text
system.cpu.rfAce.intAceBitCycles
system.cpu.rfAce.intAceRatio
system.cpu.rfAce.intTrackedWrites
system.cpu.rfAce.intTrackedReads
system.cpu.rfAce.intSquashDiscards
system.cpu.rfAce.intOverwriteDrops
system.cpu.rfAce.measuredCycles
```

## Completion Criteria

Phase 1 is complete when:

1. `stats.txt` reports integer RF ACE ratio.
2. Long dependency-chain workloads score higher than dead-write workloads.
3. Squashed paths do not significantly increase ACE.
4. The measurement window is controllable.

Phase 2 is complete when:

1. 32-bit and 64-bit GPR masks are correct.
2. Partial writes/reads do not inflate ACE as full-register accesses.
3. Bit-level or mask-level results preserve Phase 1 trends and explain them with finer detail.
4. The metric can rank programs as Harpocrates-style fitness for RF coverage.
