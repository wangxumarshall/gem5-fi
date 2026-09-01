#include "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"
#include "params/CHAOSAddrPath.hh"
#include "cpu/o3/cpu.hh"
#include "arch/arm/mmu.hh"  // for setAddrInj (non-O3 translateTiming hook)
#include "debug/LSQUnit.hh"
#include <iostream>
#include <fstream>

namespace gem5
{

    CHAOSAddrPath::CHAOSAddrPath(const CHAOSAddrPathParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          mmu(dynamic_cast<ArmISA::MMU *>(p.mmu)),
          probability(p.probability),
          byte_offset(p.byteOffset),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          rng(rng_seed != 0 ? rng_seed : [](){ std::random_device r; return r(); }()),
          log_stream(nullptr),
          stats(nullptr)
    {
        if (!cpu) {
            // Non-O3 path (e.g. AtomicCPU): cpu dynamic_cast<o3::CPU*> returns
            // nullptr. This is now allowed — the MMU non-O3 hook (setAddrInj)
            // carries the injection. Only warn if no mmu either (then inert).
            if (!mmu) {
                warn("CHAOSAddrPath: neither O3 cpu nor mmu attached; injector inert.");
            } else {
                inform("CHAOSAddrPath: non-O3 mode (mmu translateTiming hook only).");
            }
        }
        // non-O3 path: if mmu is provided, register self at the MMU's
        // translateTiming boundary (fires for AtomicCPU/Minor, not just O3).
        // This is the path used for H6 guest-visible-oops experiments (O3 stalls
        // fetch on non-canonical VAs; AtomicCPU raises a guest translation fault).
        if (mmu) {
            mmu->setAddrInj(this);
            inform("CHAOSAddrPath: setAddrInj called on mmu=%s", mmu->name());
        } else {
            warn("CHAOSAddrPath: mmu is NULL, non-O3 hook will not fire");
        }
        if (probability > 0.0f) {
            log_stream = simout.create("addr_path_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSAddrPath: Could not open log file");
            stats = std::make_unique<Stats>(this);
            if (cpu) cpu->addrPath = this;  // O3 LSQ path (only if O3 cpu)
        }
    }

    CHAOSAddrPath::~CHAOSAddrPath() {}

    void
    CHAOSAddrPath::writeLog(uint64_t seq, Addr orig, Addr corrupted)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << (cpu ? cpu->curCycle() : Cycles(curTick() >> 0))
            << ", CPU: " << (cpu ? cpu->name() : std::string("(non-O3 mmu path)"))
            << ", Seq: " << seq
            << ", Site: load_effAddr"
            << ", Orig: 0x" << std::hex << orig << std::dec
            << ", Corrupted: 0x" << std::hex << corrupted << std::dec
            << std::endl;
    }

    bool
    CHAOSAddrPath::corruptAddr(Addr *addr, uint64_t seq)
    {
        if (probability <= 0.0f) return false;
        // Count every call to the hook (every load's effAddr->MMU boundary)
        // before prob/first-clock gating. Mirrors CHAOSPTW::numHooksCalled:
        // distinguishes "load happened" from "load happened but prob missed" —
        // essential to size H6's D2 arm (load density vs PTW walk density).
        stats->numHooksCalled++;
        // Clock source: O3 cpu->curCycle() for O3; fall back to curTick() for
        // the non-O3 (AtomicCPU) path where cpu is NULL. Note the raw-tick
        // fallback has the same scale issue as CHAOSPTW (first_clock vs raw tick),
        // but all H6 experiments use first_clock=0 (gating inert) or a large
        // first_clock set in tick units for the AtomicCPU bash-after path.
        Cycles cur = cpu ? cpu->curCycle() : Cycles(curTick() >> 0);
        if (cur < first_clock) return false;
        if (last_clock != Cycles(0) && cur > last_clock) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;

        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return false;

        int off = byte_offset;
        if (off < 0) {
            std::uniform_int_distribution<int> bd(0, 7);
            off = bd(rng);
        }
        if (off < 0 || off > 7) off = 7;

        Addr orig = *addr;
        // Zero byte `off` (MSB-first ordering: byte 7 = bits 56..63).
        Addr mask = ~((Addr)0xFF << (off * 8));
        *addr = *addr & mask;

        stats->numAddrFaults++;
        ++faults_injected_count;
        writeLog(seq, orig, *addr);
        DPRINTF(LSQUnit, "CHAOSAddrPath: zeroed byte %d of effAddr "
                "(seq=%lli %s->%s)\n", off, seq, orig, *addr);
        return true;
    }

    CHAOSAddrPath::Stats::Stats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numHooksCalled, statistics::units::Count::get(),
                   "Times the addr-path hook was called (D2; every load's "
                   "effAddr->MMU boundary while injector active, before gating)"),
          ADD_STAT(numAddrFaults, statistics::units::Count::get(),
                   "Total address-path faults injected (D2)")
    {}

} // namespace gem5
