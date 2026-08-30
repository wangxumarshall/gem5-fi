#include "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"
#include "params/CHAOSAddrPath.hh"
#include "cpu/o3/cpu.hh"
#include "debug/LSQUnit.hh"
#include "base/trace.hh"
#include "sim/core.hh"  // curTick() (D1-style tick window)

#include <iostream>
#include <fstream>

namespace gem5
{

    CHAOSAddrPath::CHAOSAddrPath(const CHAOSAddrPathParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          byte_offset(p.byteOffset),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          // rng via lambda: construct random_device in a local, not via member
          // declaration order (rng is declared before rd in the header). This
          // avoids the UB crash on rng_seed==0 that hit sibling injectors.
          rng([this]() {
              std::random_device local_rd;
              return rng_seed != 0 ? std::mt19937(rng_seed) : std::mt19937(local_rd());
          }()),
          log_stream(nullptr),
          stats(nullptr)
    {
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSAddrPath: cpu is not an O3CPU. O3-only (hooks LSQ "
                "sendFragmentToTranslation). Cast failed.");
        }
        if (probability > 0.0f) {
            log_stream = simout.create("addr_path_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSAddrPath: Could not open log file");
            }
            stats = std::make_unique<Stats>(this);
            // SELF-ATTACH: register on the CPU so lsq.cc can reach this
            // injector via cpu->addrPath. cpu is constructed first (passed
            // as a Param). Safe: lsq only reads addrPath during execute(),
            // long after SimObject construction.
            cpu->addrPath = this;
        } else {
            if (!cpu->addrPath) {
                inform("CHAOSAddrPath: probability==0, not self-attaching "
                       "(no address-path injection).\n");
            }
        }
    }

    void
    CHAOSAddrPath::startup()
    {
        // D1-style: snapshot firstClock/lastClock as SIM TICKS (curTick domain).
        // The LSQ is not a ClockedObject and can't reach curCycle(); ticks are
        // the only reachable time base. last_clock==0 means unrestricted.
        first_tick = (Tick)first_clock;
        last_tick = (last_clock == Cycles(0)) ? (Tick)0 : (Tick)last_clock;
    }

    CHAOSAddrPath::~CHAOSAddrPath() {}

    void
    CHAOSAddrPath::writeLog(uint64_t seq, Addr orig, Addr corrupted)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Tick: " << curTick()
            << ", Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Seq: " << seq
            << ", Site: load_effAddr_pre_translate"
            << ", Orig: 0x" << std::hex << orig
            << ", Corrupted: 0x" << corrupted << std::dec
            << std::endl;
    }

    bool
    CHAOSAddrPath::corruptAddr(Addr *addr, uint64_t seq)
    {
        if (probability <= 0.0f) return false;
        // D1-style tick window (NOT cpu->curCycle — LSQ isn't a ClockedObject).
        Tick now = curTick();
        if (now < first_tick) return false;
        if (last_tick != 0 && now > last_tick) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;

        // Probability gate: per-load Bernoulli. >= for consistency (D5).
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
        // This reproduces core 179's D2 (arch MSB d9 -> MMU saw 00).
        Addr mask = ~((Addr)0xFF << (off * 8));
        *addr = *addr & mask;

        stats->numAddrFaults++;
        ++faults_injected_count;
        writeLog(seq, orig, *addr);
        DPRINTF(LSQUnit, "CHAOSAddrPath: zeroed byte %d of effAddr "
                "(seq=%lli 0x%llx->0x%llx)\n", off, seq,
                (unsigned long long)orig, (unsigned long long)*addr);
        return true;
    }

    CHAOSAddrPath::Stats::Stats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numAddrFaults, statistics::units::Count::get(),
                   "Total address-path faults injected (D2)")
    {}

} // namespace gem5
