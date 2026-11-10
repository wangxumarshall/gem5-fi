#include "cpu/o3/rf_ace.hh"

#include <algorithm>

#include "config/use_arm_isa.hh"
#if USE_ARM_ISA
#include "arch/arm/insts/static_inst.hh"
#endif
#include "base/logging.hh"
#include "cpu/o3/cpu.hh"

namespace gem5
{

namespace o3
{

RFAceTracker::RFAceTracker(
        CPU *_cpu, bool enable, bool use_work_items, int64_t work_item_id,
        uint64_t start_cycle, uint64_t end_cycle, bool bit_granularity,
        unsigned reg_width_bits, unsigned num_int_phys_regs,
        unsigned num_vec_phys_regs)
    : cpu(_cpu), trackingEnabled(enable), useWorkItems(use_work_items),
      targetWorkItemId(work_item_id), configuredStartCycle(start_cycle),
      configuredEndCycle(end_cycle), bitGranularity(bit_granularity),
      registerWidthBits(reg_width_bits),
      numIntPhysRegs(num_int_phys_regs),
      numVecPhysRegs(num_vec_phys_regs),
      regStates(num_int_phys_regs + num_vec_phys_regs), stats(*this, _cpu)
{
    fatal_if(trackingEnabled && registerWidthBits == 0,
            "%s: rfAceRegWidthBits must be greater than zero", cpu->name());
    fatal_if(trackingEnabled && registerWidthBits > 64,
            "%s: rfAceRegWidthBits must not exceed 64", cpu->name());
#if !USE_ARM_ISA
    fatal_if(trackingEnabled && bitGranularity,
            "%s: bit-granularity RF ACE requires an ARM ISA build",
            cpu->name());
#endif
    fatal_if(trackingEnabled && !useWorkItems && configuredEndCycle != 0 &&
             configuredEndCycle <= configuredStartCycle,
            "%s: rfAceEndCycle must be greater than rfAceStartCycle",
            cpu->name());
    resetCycle = currentCycle();
}

uint64_t
RFAceTracker::currentCycle() const
{
    return static_cast<uint64_t>(cpu->curCycle());
}

bool
RFAceTracker::selectedWorkItem(uint64_t work_id) const
{
    return targetWorkItemId < 0 ||
           static_cast<uint64_t>(targetWorkItemId) == work_id;
}

uint64_t
RFAceTracker::currentWindowStart() const
{
    if (useWorkItems)
        return workWindowStart;
    return std::max(configuredStartCycle, resetCycle);
}

bool
RFAceTracker::windowActive(uint64_t cycle) const
{
    if (!trackingEnabled)
        return false;
    if (useWorkItems)
        return workWindowActive;

    const uint64_t start = currentWindowStart();
    return cycle >= start &&
           (configuredEndCycle == 0 || cycle < configuredEndCycle);
}

bool
RFAceTracker::trackedRegister(PhysRegIdPtr reg, bool &vector,
                              unsigned &slot_index) const
{
    if (reg->is(IntRegClass) && reg->index() < numIntPhysRegs) {
        vector = false;
        slot_index = reg->index();
        return true;
    }
    if (reg->is(VecRegClass) && reg->index() < numVecPhysRegs) {
        vector = true;
        slot_index = numIntPhysRegs + reg->index();
        return true;
    }
    return false;
}

unsigned
RFAceTracker::widthFor(bool vector) const
{
    return vector ? vecWidthBits : registerWidthBits;
}

uint64_t
RFAceTracker::fullMaskFor(bool vector) const
{
    const unsigned width = widthFor(vector);
    return width == 64 ? ~uint64_t(0) : (uint64_t(1) << width) - 1;
}

void
RFAceTracker::recordRead(
        PhysRegIdPtr reg, ThreadID tid, InstSeqNum seq_num,
        const StaticInst *inst, int src_index)
{
    recordEvent(EventType::Read, reg, tid, seq_num, inst, src_index);
}

void
RFAceTracker::recordWrite(
        PhysRegIdPtr reg, ThreadID tid, InstSeqNum seq_num,
        const StaticInst *inst)
{
    recordEvent(EventType::Write, reg, tid, seq_num, inst);
}

uint64_t
RFAceTracker::accessMask(EventType type, const StaticInst *inst,
                         int src_index, bool vector) const
{
    if (!bitGranularity || type == EventType::Write || !inst)
        return fullMaskFor(vector);

#if USE_ARM_ISA
    const auto *arm = dynamic_cast<const ArmISA::ArmStaticInst *>(inst);
    const ArmISA::ExtMachInst encoding(inst->getEMI());
    if (vector) {
        if (!arm || !encoding.aarch64 || inst->isMemRef())
            return fullMaskFor(true);
        // Scalar FP uses type bits 23:22: 00=S(32), 01=D(64), 11=H(16).
        // Vector/SIMD writes and memory operations use the tracked 64-bit
        // lane by default instead of inventing 128-bit coverage.
        const uint32_t word = static_cast<uint32_t>(inst->getEMI());
        const uint32_t type_bits = (word >> 22) & 0x3;
        unsigned width = vecWidthBits;
        if (type_bits == 0)
            width = 32;
        else if (type_bits == 3)
            width = 16;
        return width == 64 ? ~uint64_t(0) :
            (uint64_t(1) << width) - 1;
    }
    if (arm && encoding.aarch64 && !inst->isMemRef() && src_index >= 0) {
        const unsigned width = std::min<unsigned>(
            arm->getIntSrcWidth(src_index), registerWidthBits);
        return width == 64 ? ~uint64_t(0) :
            (uint64_t(1) << width) - 1;
    }
#endif
    return fullMaskFor(vector);
}

void
RFAceTracker::recordEvent(
        EventType type, PhysRegIdPtr reg, ThreadID tid, InstSeqNum seq_num,
        const StaticInst *inst, int src_index)
{
    if (!trackingEnabled || !reg)
        return;

    bool vector = false;
    unsigned slot_index = 0;
    if (!trackedRegister(reg, vector, slot_index))
        return;

    const uint64_t cycle = currentCycle();
    if (!windowActive(cycle))
        return;
    if (inst && inst->isPseudo())
        return;
    if (useWorkItems && tid == markerThread && seq_num <= beginSeqNum)
        return;

    pendingInstructions[{tid, seq_num}].events.push_back(
        {type, slot_index, cycle, currentWindowStart(),
         accessMask(type, inst, src_index, vector), vector});
}

void
RFAceTracker::applyEvent(const Event &event)
{
    RegState &state = regStates[event.regIndex];
    const unsigned width = widthFor(event.vector);

    if (event.type == EventType::Write) {
        if (state.liveMask & event.mask) {
            endLifetime(state, event.mask, event.vector);
            if (event.vector)
                ++vecOverwriteDrops;
            else
                ++overwriteDrops;
        }
        const uint64_t write_cycle = std::max(event.cycle, event.windowStart);
        for (unsigned bit = 0; bit < width; ++bit) {
            const uint64_t bit_mask = uint64_t(1) << bit;
            if (event.mask & bit_mask) {
                state.writeCycles[bit] = write_cycle;
                state.lastReadCycles[bit] = 0;
            }
        }
        state.liveMask |= event.mask;
        state.readMask &= ~event.mask;
        if (event.vector)
            ++vecTrackedWrites;
        else
            ++trackedWrites;
        return;
    }

    if (state.liveMask == 0) {
        // A live-in integer value was produced before the ROI. Its in-window
        // ACE lifetime starts at the ROI boundary, not at an unknown earlier
        // time. Vector/FP values are not given this live-in treatment: the
        // ROI's vector baseline is not observable per-bit here (and a freed
        // register re-read would otherwise double-count). A vector read only
        // contributes after an in-ROI write, which the FP templates perform.
        if (event.vector)
            return;
        state.liveMask = fullMaskFor(event.vector);
        for (unsigned bit = 0; bit < width; ++bit)
            state.writeCycles[bit] = event.windowStart;
    }
    const uint64_t effective_mask = event.mask & state.liveMask;
    state.readMask |= effective_mask;
    for (unsigned bit = 0; bit < width; ++bit) {
        if (effective_mask & (uint64_t(1) << bit)) {
            state.lastReadCycles[bit] = std::max(
                state.lastReadCycles[bit], event.cycle);
        }
    }
    if (event.vector)
        ++vecTrackedReads;
    else
        ++trackedReads;
}

void
RFAceTracker::commitInstruction(ThreadID tid, InstSeqNum seq_num)
{
    if (!trackingEnabled)
        return;

    auto it = pendingInstructions.find({tid, seq_num});
    if (it == pendingInstructions.end())
        return;

    for (const auto &event : it->second.events)
        applyEvent(event);
    pendingInstructions.erase(it);
}

void
RFAceTracker::squashInstruction(ThreadID tid, InstSeqNum seq_num)
{
    if (!trackingEnabled)
        return;

    auto it = pendingInstructions.find({tid, seq_num});
    if (it == pendingInstructions.end())
        return;

    for (const auto &event : it->second.events) {
        if (event.type != EventType::Write)
            continue;
        if (event.vector)
            ++vecSquashDiscards;
        else
            ++squashDiscards;
    }
    pendingInstructions.erase(it);
}

void
RFAceTracker::squashYounger(ThreadID tid, InstSeqNum squash_seq_num)
{
    if (!trackingEnabled)
        return;

    auto it = pendingInstructions.upper_bound({tid, squash_seq_num});
    while (it != pendingInstructions.end() && it->first.first == tid) {
        for (const auto &event : it->second.events) {
            if (event.type != EventType::Write)
                continue;
            if (event.vector)
                ++vecSquashDiscards;
            else
                ++squashDiscards;
        }
        it = pendingInstructions.erase(it);
    }
}

void
RFAceTracker::endLifetime(RegState &state, uint64_t mask, bool vector)
{
    const uint64_t effective_mask = mask & state.liveMask & state.readMask;
    for (unsigned bit = 0; bit < widthFor(vector); ++bit) {
        if (!(effective_mask & (uint64_t(1) << bit)))
            continue;
        const uint64_t cycles = state.lastReadCycles[bit] -
            state.writeCycles[bit];
        if (vector) {
            finalizedVecAceBitCycles += cycles;
        } else {
            finalizedAceBitCycles += cycles;
            if (bit < 32)
                finalizedAceBitCyclesLow32 += cycles;
            else
                finalizedAceBitCyclesHigh32 += cycles;
        }
    }
    state.liveMask &= ~mask;
    state.readMask &= ~mask;
}

void
RFAceTracker::freeRegister(PhysRegIdPtr reg)
{
    if (!trackingEnabled || !reg)
        return;

    bool vector = false;
    unsigned slot_index = 0;
    if (!trackedRegister(reg, vector, slot_index))
        return;

    RegState &state = regStates[slot_index];
    if (state.liveMask == 0)
        return;
    endLifetime(state, fullMaskFor(vector), vector);
    if (vector)
        ++vecOverwriteDrops;
    else
        ++overwriteDrops;
}

void
RFAceTracker::workItemBegin(uint64_t work_id, ThreadID tid,
                            InstSeqNum seq_num)
{
    if (!trackingEnabled || !useWorkItems || workWindowStarted ||
        !selectedWorkItem(work_id)) {
        return;
    }

    workWindowStarted = true;
    workWindowActive = true;
    activeWorkItemId = work_id;
    markerThread = tid;
    beginSeqNum = seq_num;
    workWindowStart = currentCycle();
    ++windowBegins;
}

void
RFAceTracker::workItemEnd(uint64_t work_id, ThreadID tid,
                          InstSeqNum seq_num)
{
    if (!trackingEnabled || !useWorkItems || !workWindowActive ||
        work_id != activeWorkItemId) {
        return;
    }

    workWindowEnd = currentCycle();

    // The non-speculative marker executes at the ROB head: older instructions
    // in this thread have committed. Pending younger accesses belong to code
    // after the marker, even if they executed before it.
    auto pending = pendingInstructions.lower_bound({tid, seq_num});
    while (pending != pendingInstructions.end() && pending->first.first == tid)
        pending = pendingInstructions.erase(pending);

    // The work-end pseudo instruction obtains its arguments before invoking
    // this callback. Remove accesses from that exclusive boundary cycle so
    // the marker itself is not part of the measured test body.
    for (auto &entry : pendingInstructions) {
        auto &events = entry.second.events;
        events.erase(
            std::remove_if(events.begin(), events.end(),
                [this](const Event &event) {
                    return event.cycle >= workWindowEnd;
                }),
            events.end());
    }
    workWindowActive = false;
    workWindowComplete = true;
    ++windowEnds;
}

void
RFAceTracker::resetTracking()
{
    // The default m5_work_begin behavior resets all gem5 statistics after
    // The CPU marker hook has notified this tracker. Preserve that
    // newly opened ROI across the reset, but make the reset cycle its exact
    // accounting boundary.  Explicit resets in the middle of an ROI follow
    // the same standard gem5 semantics: prior samples are discarded and the
    // active measurement continues from the reset point.
    const bool preserve_work_window = useWorkItems && workWindowActive;
    const uint64_t new_start = currentCycle();

    pendingInstructions.clear();
    std::fill(regStates.begin(), regStates.end(), RegState{});
    finalizedAceBitCycles = 0;
    finalizedAceBitCyclesLow32 = 0;
    finalizedAceBitCyclesHigh32 = 0;
    finalizedVecAceBitCycles = 0;
    trackedReads = 0;
    trackedWrites = 0;
    vecTrackedReads = 0;
    vecTrackedWrites = 0;
    overwriteDrops = 0;
    vecOverwriteDrops = 0;
    squashDiscards = 0;
    vecSquashDiscards = 0;
    windowBegins = 0;
    windowEnds = 0;
    resetCycle = new_start;
    workWindowStarted = preserve_work_window;
    workWindowActive = preserve_work_window;
    workWindowComplete = false;
    if (!preserve_work_window)
        activeWorkItemId = 0;
    workWindowStart = preserve_work_window ? new_start : 0;
    workWindowEnd = 0;
    if (preserve_work_window)
        windowBegins = 1;
}

uint64_t
RFAceTracker::liveBitCycles(uint64_t mask, bool vector) const
{
    uint64_t cycles = 0;
    const unsigned start = vector ? numIntPhysRegs : 0;
    const unsigned end = vector ? numIntPhysRegs + numVecPhysRegs
                                : numIntPhysRegs;
    const unsigned width = widthFor(vector);
    for (unsigned index = start; index < end; ++index) {
        const RegState &state = regStates[index];
        const uint64_t effective_mask = mask & state.liveMask & state.readMask;
        for (unsigned bit = 0; bit < width; ++bit) {
            if (effective_mask & (uint64_t(1) << bit)) {
                cycles += state.lastReadCycles[bit] - state.writeCycles[bit];
            }
        }
    }
    return cycles;
}

uint64_t
RFAceTracker::aceRegCycles() const
{
    return registerWidthBits == 0 ? 0 : aceBitCycles() / registerWidthBits;
}

uint64_t
RFAceTracker::aceBitCycles() const
{
    return finalizedAceBitCycles + liveBitCycles(fullMaskFor(false), false);
}

uint64_t
RFAceTracker::aceBitCyclesLow32() const
{
    return finalizedAceBitCyclesLow32 +
        liveBitCycles(fullMaskFor(false) & 0xffffffffULL, false);
}

uint64_t
RFAceTracker::aceBitCyclesHigh32() const
{
    return finalizedAceBitCyclesHigh32 +
        liveBitCycles(fullMaskFor(false) & 0xffffffff00000000ULL, false);
}

uint64_t
RFAceTracker::vecAceRegCycles() const
{
    return vecWidthBits == 0 ? 0 : vecAceBitCycles() / vecWidthBits;
}

uint64_t
RFAceTracker::vecAceBitCycles() const
{
    return finalizedVecAceBitCycles + liveBitCycles(fullMaskFor(true), true);
}

uint64_t
RFAceTracker::measuredCycles() const
{
    if (!trackingEnabled)
        return 0;

    const uint64_t now = currentCycle();
    if (useWorkItems) {
        if (!workWindowStarted)
            return 0;
        const uint64_t end = workWindowComplete ? workWindowEnd : now;
        return end >= workWindowStart ? end - workWindowStart : 0;
    }

    const uint64_t start = currentWindowStart();
    const uint64_t end = configuredEndCycle == 0 ?
        now : std::min(now, configuredEndCycle);
    return end >= start ? end - start : 0;
}

double
RFAceTracker::aceRatio() const
{
    const uint64_t cycles = measuredCycles();
    if (cycles == 0 || numIntPhysRegs == 0 || registerWidthBits == 0)
        return 0.0;

    const long double denominator =
        static_cast<long double>(numIntPhysRegs) * registerWidthBits * cycles;
    return static_cast<double>(aceBitCycles() / denominator);
}

double
RFAceTracker::vecAceRatio() const
{
    const uint64_t cycles = measuredCycles();
    if (cycles == 0 || numVecPhysRegs == 0 || vecWidthBits == 0)
        return 0.0;

    const long double denominator =
        static_cast<long double>(numVecPhysRegs) * vecWidthBits * cycles;
    return static_cast<double>(vecAceBitCycles() / denominator);
}

RFAceTracker::Stats::Stats(RFAceTracker &_tracker, CPU *_cpu)
    : statistics::Group(_cpu, "rfAce"), tracker(_tracker),
      ADD_STAT(intAceRegCycles, statistics::units::Cycle::get(),
               "ACE register-entry cycles in the integer physical register "
               "file"),
      ADD_STAT(intAceBitCycles, statistics::units::Count::get(),
               "ACE bit-cycles at the selected integer granularity"),
      ADD_STAT(intAceBitCyclesLow32, statistics::units::Count::get(),
               "ACE bit-cycles in integer-register bits 0 through 31"),
      ADD_STAT(intAceBitCyclesHigh32, statistics::units::Count::get(),
               "ACE bit-cycles in integer-register bits 32 through 63"),
      ADD_STAT(intAceRatio, statistics::units::Ratio::get(),
               "Integer physical register file ACE coverage ratio"),
      ADD_STAT(bitGranularity, statistics::units::Count::get(),
               "One when per-bit access masks are enabled"),
      ADD_STAT(intTrackedWrites, statistics::units::Count::get(),
               "Committed integer physical register writes in the window"),
      ADD_STAT(intTrackedReads, statistics::units::Count::get(),
               "Committed integer physical register reads in the window"),
      ADD_STAT(intSquashDiscards, statistics::units::Count::get(),
               "Wrong-path integer destination writes discarded"),
      ADD_STAT(intOverwriteDrops, statistics::units::Count::get(),
               "Tracked integer values ended by free, reuse, or overwrite"),
      ADD_STAT(vecAceRegCycles, statistics::units::Cycle::get(),
               "ACE register-entry cycles in the vector/FP physical register "
               "file (64-bit lane)"),
      ADD_STAT(vecAceBitCycles, statistics::units::Count::get(),
               "ACE bit-cycles in the vector/FP physical register file"),
      ADD_STAT(vecAceRatio, statistics::units::Ratio::get(),
               "Vector/FP physical register file ACE coverage ratio"),
      ADD_STAT(vecTrackedWrites, statistics::units::Count::get(),
               "Committed vector/FP physical register writes in the window"),
      ADD_STAT(vecTrackedReads, statistics::units::Count::get(),
               "Committed vector/FP physical register reads in the window"),
      ADD_STAT(vecSquashDiscards, statistics::units::Count::get(),
               "Wrong-path vector/FP destination writes discarded"),
      ADD_STAT(vecOverwriteDrops, statistics::units::Count::get(),
               "Tracked vector/FP values ended by free, reuse, or overwrite"),
      ADD_STAT(measuredCycles, statistics::units::Cycle::get(),
               "Cycles in the selected RF ACE measurement window"),
      ADD_STAT(windowBegins, statistics::units::Count::get(),
               "Selected work-item windows started"),
      ADD_STAT(windowEnds, statistics::units::Count::get(),
               "Selected work-item windows completed")
{
    intAceRegCycles.functor([this]() { return tracker.aceRegCycles(); });
    intAceBitCycles.functor([this]() { return tracker.aceBitCycles(); });
    intAceBitCyclesLow32.functor(
        [this]() { return tracker.aceBitCyclesLow32(); });
    intAceBitCyclesHigh32.functor(
        [this]() { return tracker.aceBitCyclesHigh32(); });
    intAceRatio.functor([this]() { return tracker.aceRatio(); }).precision(8);
    bitGranularity.functor([this]() { return tracker.bitGranularity ? 1 : 0; });
    intTrackedWrites.functor([this]() { return tracker.trackedWrites; });
    intTrackedReads.functor([this]() { return tracker.trackedReads; });
    intSquashDiscards.functor([this]() { return tracker.squashDiscards; });
    intOverwriteDrops.functor([this]() { return tracker.overwriteDrops; });
    vecAceRegCycles.functor([this]() { return tracker.vecAceRegCycles(); });
    vecAceBitCycles.functor([this]() { return tracker.vecAceBitCycles(); });
    vecAceRatio.functor([this]() { return tracker.vecAceRatio(); }).precision(8);
    vecTrackedWrites.functor([this]() { return tracker.vecTrackedWrites; });
    vecTrackedReads.functor([this]() { return tracker.vecTrackedReads; });
    vecSquashDiscards.functor([this]() { return tracker.vecSquashDiscards; });
    vecOverwriteDrops.functor([this]() { return tracker.vecOverwriteDrops; });
    measuredCycles.functor([this]() { return tracker.measuredCycles(); });
    windowBegins.functor([this]() { return tracker.windowBegins; });
    windowEnds.functor([this]() { return tracker.windowEnds; });
}

void
RFAceTracker::Stats::resetStats()
{
    tracker.resetTracking();
    statistics::Group::resetStats();
}

} // namespace o3
} // namespace gem5
