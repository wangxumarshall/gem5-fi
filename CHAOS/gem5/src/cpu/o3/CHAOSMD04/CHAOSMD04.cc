#include "cpu/o3/CHAOSMD04/CHAOSMD04.hh"

#include <algorithm>

#include "cpu/o3/CHAOSMD04/md04_rules.hh"
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"
#include "debug/CHAOSMD04.hh"
#include "sim/sim_exit.hh"

namespace gem5
{

CHAOSMD04::CHAOSMD04(const CHAOSMD04Params &p)
    : SimObject(p), cpu(p.cpu), probability(p.probability),
      first_clock(p.firstClock), last_clock(p.lastClock),
      max_faults(p.maxFaults), rng_seed(p.rngSeed),
      event_ordinal(p.eventOrdinal), count_only(p.countOnly),
      write_log(p.writeLog)
{
    if (write_log) {
        log_stream = simout.create("md04_injections.log", false, true);
        if (!log_stream || !log_stream->stream())
            panic("CHAOSMD04: cannot open md04_injections.log");
    }
    if (rng_seed)
        rng.seed(rng_seed);
    else
        rng.seed(rd());
}

CHAOSMD04::~CHAOSMD04()
{
    if (count_only && log_stream && log_stream->stream())
        *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT=" << eligible_count
                                << std::endl;
}

void
CHAOSMD04::startup()
{
    SimObject::startup();
    auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
    if (!o3cpu) {
        warn("CHAOSMD04: cpu is not an O3CPU; injector disabled.\n");
        return;
    }
    o3cpu->setChaosMD04(this);
    registerExitCallback([this]() {
        if (!log_stream || !log_stream->stream())
            return;
        if (count_only)
            *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT="
                                    << eligible_count << std::endl;
        if (faults_injected_count == 0) {
            *(log_stream->stream())
                << "CHAOS_MD04_TARGET_STATUS="
                << ((event_ordinal != 0 && eligible_count < event_ordinal)
                    ? "ORDINAL_NOT_REACHED" : "NOT_TRIGGERED")
                << " eligible_count=" << eligible_count
                << " target_ordinal=" << event_ordinal << std::endl;
        } else {
            *(log_stream->stream())
                << "CHAOS_MD04_TARGET_STATUS=INJECTED count="
                << faults_injected_count << std::endl;
        }
    });
}

bool
CHAOSMD04::maybeSkipViolation(o3::DynInst *ld_inst, o3::DynInst *store_inst,
                              bool load_complete, unsigned dep_check_shift,
                              const RequestPtr &load_req)
{
    (void)load_req;  // consumed by the v3.2.7 trace identity (Task 3)
    // L-A06: mounted-at-p=0 control gate — probability<=0 is a true disable
    // (belt-and-braces even though the config couples md04_probability).
    if (probability <= 0.0f)
        return false;
    if (!cpu || !ld_inst || !store_inst)
        return false;
    if (ld_inst->effAddrValid() && store_inst->effAddrValid())
        DPRINTF(CHAOSMD04, "pair load=%llu addr=%#x size=%u store=%llu "
                "addr=%#x size=%u\n",
                (unsigned long long)ld_inst->seqNum, ld_inst->effAddr,
                ld_inst->effSize, (unsigned long long)store_inst->seqNum,
                store_inst->effAddr, store_inst->effSize);
    if (ld_inst->isSquashed() || !ld_inst->isLoad() || store_inst->isLoad())
        return false;
    if (!ld_inst->effAddrValid() || !store_inst->effAddrValid())
        return false;
    if (ld_inst->seqNum <= store_inst->seqNum)
        return false;   // only a younger load can have passed the store
    if (!chaos_md04::isEligibleViolationPair(
            ld_inst->effAddr, ld_inst->effSize,
            store_inst->effAddr, store_inst->effSize, dep_check_shift))
        return false;

    Cycles cur = cpu->curCycle();
    if (cur < Cycles(first_clock))
        return false;
    if (last_clock != 0 && cur > Cycles(last_clock))
        return false;

    ++eligible_count;
    last_eligible_ordinal = eligible_count;
    if (count_only)
        return false;
    if (!chaos_md04::shouldInject(eligible_count, event_ordinal,
                                  faults_injected_count, max_faults))
        return false;

    std::uniform_real_distribution<float> pd(0.0f, 1.0f);
    if (pd(rng) > probability)
        return false;

    ++faults_injected_count;
    if (log_stream && log_stream->stream()) {
        *(log_stream->stream()) << "Tick: " << curTick()
            << ", Site: checkViolations"
            << ", load_seq=" << ld_inst->seqNum
            << ", store_seq=" << store_inst->seqNum
            << ", addr=0x" << std::hex << ld_inst->effAddr << std::dec
            << ", size=" << ld_inst->effSize
            << ", store_addr=0x" << std::hex << store_inst->effAddr
            << ", store_size=" << std::dec << store_inst->effSize
            << ", load_pc=0x" << std::hex
            << ld_inst->pcState().instAddr()
            << ", store_pc=0x" << store_inst->pcState().instAddr()
            << std::dec
            << ", sq_entry_id=" << (long long)store_inst->sqIdx
            << ", sq_entry_generation=" << store_inst->sqEntryGeneration
            << ", lq_entry_id=" << (long long)ld_inst->lqIdx
            << ", lq_entry_generation=" << ld_inst->lqEntryGeneration
            << ", eligible_ordinal=" << eligible_count
            << ", event_ordinal=" << event_ordinal
            << ", seed=" << rng_seed
            << ", load_complete=" << (load_complete ? 1 : 0)
            << ", address_modified=0, size_modified=0, data_modified=0"
            << ", faults_injected: " << faults_injected_count << std::endl;
    }
    auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
    if (o3cpu && o3cpu->chaosPropagation) {
        o3cpu->chaosPropagation->noteMD04Injection(
            ld_inst, store_inst, load_req, ld_inst->effAddr,
            ld_inst->effSize, eligible_count, event_ordinal, rng_seed,
            load_complete);
    }
    DPRINTF(CHAOSMD04, "suppressed store->load violation load=%llu store=%llu "
            "addr=%#x\n", (unsigned long long)ld_inst->seqNum,
            (unsigned long long)store_inst->seqNum, ld_inst->effAddr);
    return true;
}

} // namespace gem5
