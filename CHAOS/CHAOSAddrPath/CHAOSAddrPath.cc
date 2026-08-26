#include "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"
#include "params/CHAOSAddrPath.hh"
#include "cpu/o3/cpu.hh"
#include "debug/LSQUnit.hh"
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
          rng(rng_seed != 0 ? rng_seed : rd()),
          log_stream(nullptr),
          stats(nullptr)
    {
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSAddrPath: cpu is not an O3CPU. O3-only (hooks LSQ).");
        }
        if (probability > 0.0f) {
            log_stream = simout.create("addr_path_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSAddrPath: Could not open log file");
            stats = std::make_unique<Stats>(this);
            cpu->addrPath = this;  // register self on the CPU
        }
    }

    CHAOSAddrPath::~CHAOSAddrPath() {}

    void
    CHAOSAddrPath::writeLog(uint64_t seq, Addr orig, Addr corrupted)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
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
        Cycles cur = cpu->curCycle();
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
          ADD_STAT(numAddrFaults, statistics::units::Count::get(),
                   "Total address-path faults injected (D2)")
    {}

} // namespace gem5
