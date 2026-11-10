#include "cpu/o3/fu_ibr.hh"

#include <algorithm>
#include <set>

#include "config/use_arm_isa.hh"
#if USE_ARM_ISA
#include "arch/arm/insts/static_inst.hh"
#endif
#include "base/logging.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/fu_pool.hh"
#include "cpu/o3/inst_queue.hh"
#include "params/BaseO3CPU.hh"

namespace gem5 { namespace o3 {

namespace {
#if USE_ARM_ISA
/** Scalar FP width from the AArch64 type field (bits 23:22). */
unsigned
scalarFpWidth(uint32_t word)
{
    const uint32_t type_bits = (word >> 22) & 0x3;
    if (type_bits == 0)
        return 32; // S
    if (type_bits == 3)
        return 16; // H
    return 64;     // D (and the default for unrecognised scalar forms)
}
#endif
} // anonymous namespace

FUIbrTracker::FUIbrTracker(CPU *_cpu, const BaseO3CPUParams &params)
    : cpu(_cpu), enabled(params.fuIbr), useWorkItems(params.fuIbrUseWorkItems),
      workId(params.fuIbrWorkItemId), startCycle(params.fuIbrStartCycle),
      endCycle(params.fuIbrEndCycle), stats(*this, _cpu)
{
#if !USE_ARM_ISA
    fatal_if(enabled, "fuIbr requires an ARM ISA build");
#endif
    fatal_if(enabled && !useWorkItems && endCycle && endCycle <= startCycle,
             "fuIbrEndCycle must be greater than fuIbrStartCycle");
    // Shared pools must contribute their physical units only once.
    std::set<FUPool *> seen;
    const std::array<OpClass, numClasses> classes = {
        enums::IntAlu, enums::IntMult, enums::IntDiv,
        enums::FloatAdd, enums::FloatMult, enums::FloatDiv};
    for (auto *iq : params.instQueues) {
        auto *pool = iq->fuPool();
        if (!seen.insert(pool).second)
            continue;
        for (unsigned i = 0; i < classes.size(); ++i)
            unitCounts[i] += pool->capableUnitCount(classes[i]);
    }
    resetCycle = currentCycle();
}

uint64_t FUIbrTracker::currentCycle() const
{ return static_cast<uint64_t>(cpu->curCycle()); }

bool FUIbrTracker::selected(uint64_t id) const
{ return workId < 0 || static_cast<uint64_t>(workId) == id; }

uint64_t FUIbrTracker::measuredCycles() const
{
    if (!enabled || (useWorkItems && !started))
        return 0;
    const uint64_t start = useWorkItems ? windowStart :
        std::max(startCycle, resetCycle);
    const uint64_t end = useWorkItems ?
        (complete ? windowEnd : currentCycle()) :
        (endCycle ? std::min(endCycle, currentCycle()) : currentCycle());
    return end > start ? end - start : 0;
}

void FUIbrTracker::recordIssue(const StaticInstPtr &inst)
{
    if (!enabled)
        return;
    const uint64_t cycle = currentCycle();
    if (useWorkItems ? !active :
        (cycle < std::max(startCycle, resetCycle) ||
         (endCycle && cycle >= endCycle)))
        return;
#if USE_ARM_ISA
    if (sampleCycle != cycle) {
        sampleCycle = cycle;
        cycleInputBits.fill(0);
        cycleIssuedOps.fill(0);
        cycleExcluded = 0;
    }
    const auto *arm = dynamic_cast<const ArmISA::ArmStaticInst *>(inst.get());
    const uint64_t emi = inst->getEMI();
    const ArmISA::ExtMachInst encoding(emi);
    const uint32_t word = static_cast<uint32_t>(emi);
    int index = -1;
    unsigned width = 64;
    if (arm && encoding.aarch64 && !inst->isControl()) {
        if (inst->opClass() == enums::IntAlu) {
            // Binary add/sub and logical operations, register or immediate,
            // including MOVZ/MOVK/MOVN aliases and shifted/extended forms.
            const uint32_t kind = word & 0x1f000000;
            if (kind == 0x11000000 || kind == 0x12000000 ||
                kind == 0x0b000000 || kind == 0x0a000000) {
                index = 0;
                width = arm->getIntWidth();
            }
        } else if (inst->opClass() == enums::IntMult &&
                   (word & 0x1fe00000) == 0x1b000000) {
            // Same-width MADD/MSUB, including MUL/MNEG aliases with Ra=ZR.
            index = 1;
            width = arm->getIntWidth();
        } else if (inst->opClass() == enums::IntDiv) {
            index = 2;
            width = arm->getIntWidth();
        } else if (inst->opClass() == enums::FloatAdd) {
            // Scalar FADD/FSUB; SIMD uses SimdFloatAdd and stays excluded.
            index = 3;
            width = scalarFpWidth(word);
        } else if (inst->opClass() == enums::FloatMult) {
            // Scalar FMUL/FNMUL; SIMD uses SimdFloatMult.
            index = 4;
            width = scalarFpWidth(word);
        } else if (inst->opClass() == enums::FloatDiv) {
            // Scalar FDIV; SIMD uses SimdFloatDiv.
            index = 5;
            width = scalarFpWidth(word);
        }
    }
    if (index < 0) {
        ++excluded;
        ++cycleExcluded;
        return;
    }
    inputBits[index] += ports[index] * width;
    ++issuedOps[index];
    cycleInputBits[index] += ports[index] * width;
    ++cycleIssuedOps[index];
#endif
}

void FUIbrTracker::workItemBegin(uint64_t id)
{
    if (!enabled || !useWorkItems || started || !selected(id))
        return;
    started = active = true;
    activeWorkId = id;
    windowStart = currentCycle();
    ++begins;
}

void FUIbrTracker::workItemEnd(uint64_t id)
{
    if (!enabled || !useWorkItems || !active || id != activeWorkId)
        return;
    active = false;
    complete = true;
    windowEnd = currentCycle();
    if (sampleCycle == windowEnd) {
        for (unsigned i = 0; i < inputBits.size(); ++i) {
            inputBits[i] -= cycleInputBits[i];
            issuedOps[i] -= cycleIssuedOps[i];
        }
        excluded -= cycleExcluded;
    }
    ++ends;
}

void FUIbrTracker::resetTracking()
{
    inputBits.fill(0);
    issuedOps.fill(0);
    cycleInputBits.fill(0);
    cycleIssuedOps.fill(0);
    cycleExcluded = 0;
    sampleCycle = currentCycle();
    excluded = ends = 0;
    resetCycle = currentCycle();
    started = useWorkItems && active;
    complete = false;
    if (!started)
        activeWorkId = 0;
    windowStart = started ? resetCycle : 0;
    windowEnd = 0;
    begins = started ? 1 : 0;
}

FUIbrTracker::Stats::Stats(FUIbrTracker &t, CPU *cpu)
    : statistics::Group(cpu, "fuIbr"), tracker(t),
      ADD_STAT(inputBits, statistics::units::Count::get(),
               "Effective input bits sampled at FU issue"),
      ADD_STAT(issuedOps, statistics::units::Count::get(),
               "Supported operations actually issued, including wrong path"),
      ADD_STAT(unitCount, statistics::units::Count::get(),
               "Physical units supporting this operation class"),
      ADD_STAT(maxInputBits, statistics::units::Count::get(),
               "Units * input ports * 64 bits * measured cycles"),
      ADD_STAT(ibrRatio, statistics::units::Ratio::get(),
               "Input bits divided by theoretical maximum input bits"),
      ADD_STAT(measuredCycles, statistics::units::Cycle::get(),
               "Cycles in the selected IBR measurement window"),
      ADD_STAT(windowBegins, statistics::units::Count::get(),
               "Selected work-item windows started"),
      ADD_STAT(windowEnds, statistics::units::Count::get(),
               "Selected work-item windows completed"),
      ADD_STAT(excludedOps, statistics::units::Count::get(),
               "FU issues outside the supported AArch64 arithmetic subset")
{
    for (auto *v : {&inputBits, &issuedOps, &unitCount, &maxInputBits,
                    &ibrRatio}) {
        v->init(numClasses);
        v->subname(0, "intAlu").subname(1, "intMult").subname(2, "intDiv")
            .subname(3, "fpAdd").subname(4, "fpMult").subname(5, "fpDiv");
    }
    ibrRatio.precision(8);
    measuredCycles.functor([this]() { return tracker.measuredCycles(); });
    windowBegins.functor([this]() { return tracker.begins; });
    windowEnds.functor([this]() { return tracker.ends; });
    excludedOps.functor([this]() { return tracker.excluded; });
}

void FUIbrTracker::Stats::preDumpStats()
{
    statistics::Group::preDumpStats();
    for (unsigned i = 0; i < numClasses; ++i) {
        const double maximum = static_cast<double>(tracker.unitCounts[i]) *
            ports[i] * 64 * tracker.measuredCycles();
        inputBits[i] = tracker.inputBits[i];
        issuedOps[i] = tracker.issuedOps[i];
        unitCount[i] = tracker.unitCounts[i];
        maxInputBits[i] = maximum;
        ibrRatio[i] = maximum ? tracker.inputBits[i] / maximum : 0;
    }
}

void FUIbrTracker::Stats::resetStats()
{
    tracker.resetTracking();
    statistics::Group::resetStats();
}
} } // namespace gem5::o3
