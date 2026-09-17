/*
 * CHAOSFUPerm — FU permanent fault injector, execution level (Task 5.2).
 * See CHAOSFUPerm.hh for the mount contract.
 */
#include "CHAOSFUPerm/CHAOSFUPerm.hh"
#include "params/CHAOSFUPerm.hh"
#include "cpu/o3/cpu.hh"
#include "enums/OpClass.hh"
#include "base/trace.hh"

#include <iostream>

namespace gem5
{

CHAOSFUPerm *CHAOSFUPerm::instance = nullptr;
bool fu_perm_enabled = false;

// Mask oracle for cpu/o3/dyn_inst.hh setRegOperand: returns the XOR mask
// for this op class, 0 if none. Hot path: one compare when disabled.
uint64_t
fu_perm_mask_for(int op_class)
{
    if (!CHAOSFUPerm::instance)
        return 0;
    CHAOSFUPerm *self = CHAOSFUPerm::instance;
    if (op_class != self->target_opclass)
        return 0;
    if (self->cpu->curCycle() < Cycles(self->first_clock))
        return 0;
    self->stats.numMatchedOpClass++;
    if (self->write_log && self->log_stream && self->log_stream->stream()
        && self->corrupt_count < 32) {
        *(self->log_stream->stream())
            << "Cycle: " << self->cpu->curCycle()
            << ", OpClass: " << enums::OpClassStrings[self->target_opclass]
            << ", Mask: 0x" << std::hex << self->fault_mask << std::dec
            << std::endl;
    }
    self->corrupt_count++;
    self->stats.numCorrupted++;
    return self->fault_mask;
}

CHAOSFUPerm::CHAOSFUPerm(const CHAOSFUPermParams &p)
    : SimObject(p),
      cpu(dynamic_cast<o3::CPU *>(p.cpu)),
      write_log(p.writeLog),
      stats(this)
{
    if (!cpu)
        throw std::runtime_error(
            "CHAOSFUPerm: cpu is not an O3CPU — O3-only (writeback hook)");

    // OpClass name -> enums value.
    const std::string &n = p.targetOpClass;
    target_opclass = -1;
    for (int i = 0; i < enums::Num_OpClass; i++) {
        if (enums::OpClassStrings[i] == n) {
            target_opclass = i;
            break;
        }
    }
    if (target_opclass < 0)
        throw std::runtime_error(
            "CHAOSFUPerm: unknown targetOpClass '" + n + "'");

    first_clock = p.firstClock;
    // faultMask=0 → derive one random bit from rngSeed (deterministic).
    fault_mask = p.faultMask;
    if (fault_mask == 0) {
        uint64_t seed = p.rngSeed ? p.rngSeed : 1;
        fault_mask = 1ULL << (seed % 64);
    }

    if (instance)
        warn("CHAOSFUPerm: multiple instances; last one wins\n");
    instance = this;
    fu_perm_enabled = true;

    if (write_log) {
        log_stream = simout.create("fu_perm_injections.log", false, true);
        if (!log_stream || !log_stream->stream())
            panic("CHAOSFUPerm: could not open fu_perm_injections.log");
    }
}

CHAOSFUPerm::~CHAOSFUPerm()
{
    if (instance == this) {
        instance = nullptr;
        fu_perm_enabled = false;
    }
}

CHAOSFUPerm::Stats::Stats(statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(numCorrupted, statistics::units::Count::get(),
               "Results corrupted by the permanent FU fault"),
      ADD_STAT(numMatchedOpClass, statistics::units::Count::get(),
               "Instructions of the target OpClass reaching writeback")
{
}

} // namespace gem5
