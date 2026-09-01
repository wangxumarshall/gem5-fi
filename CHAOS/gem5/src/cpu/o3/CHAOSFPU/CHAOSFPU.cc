#include "cpu/o3/CHAOSFPU/CHAOSFPU.hh"
#include "params/CHAOSFPU.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/rob.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "base/trace.hh"
#include "debug/CHAOSFPU.hh"
#include <iostream>
#include <fstream>

namespace gem5
{
    CHAOSFPU::CHAOSFPU(const CHAOSFPUParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fault_mask(p.faultMask),
          num_bits_to_change(p.bitsToChange),
          bit_seg(stringToBitSeg(p.bitSegment)),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          semantic_role(p.semanticRole),
          rng([this]() {
              std::random_device local_rd;
              return rng_seed != 0 ? std::mt19937(rng_seed) : std::mt19937(local_rd());
          }()),
          inter_fault_cycles_dist(probability),
          log_stream(nullptr),
          attackEvent([this] { this->attackCheck(); }, name()),
          stats(nullptr)
    {
        if (!cpu) throw std::runtime_error(
            "CHAOSFPU: cpu not O3CPU. O3-only (needs robAccess).");
        if (probability > 0.0f) {
            log_stream = simout.create("fpu_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSFPU: Could not open log file");
            stats = std::make_unique<Stats>(this);
        }
    }

    void CHAOSFPU::startup() {
        if (!probability) return;
        scheduleAttackEvent(first_clock + Cycles(inter_fault_cycles_dist(rng)));
    }
    CHAOSFPU::~CHAOSFPU() {}

    CHAOSFPU::BitSeg CHAOSFPU::stringToBitSeg(const std::string &s) {
        if (s == "low")  return BitSeg::Low;   // [0:11]
        if (s == "mid")  return BitSeg::Mid;   // [12:47]
        if (s == "high") return BitSeg::High;  // [48:63]
        return BitSeg::All;
    }

    void CHAOSFPU::scheduleAttackEvent(Cycles delay) {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void CHAOSFPU::attackCheck() {
        if (!probability) return;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *tc = cpu->getContext(tid);
            if (!tc || tc->status() == ThreadContext::Halted) continue;
            processFault(tid);
        }
        if (max_faults == 0 || faults_injected_count < max_faults) {
            unsigned next = inter_fault_cycles_dist(rng);
            Cycles nc = cpu->curCycle() + Cycles(next);
            if (last_clock == Cycles(0) || nc <= last_clock)
                scheduleAttackEvent(Cycles(next));
        }
    }

    uint64_t CHAOSFPU::genMask() {
        if (fault_mask) return fault_mask;
        int lo, hi;
        switch (bit_seg) {
            case BitSeg::Low:  lo=0;  hi=11; break;
            case BitSeg::Mid:  lo=12; hi=47; break;
            case BitSeg::High: lo=48; hi=63; break;
            default:           lo=0;  hi=63; break;
        }
        std::uniform_int_distribution<int> bd(lo, hi);
        uint64_t m = 0;
        for (int i = 0; i < num_bits_to_change; ++i) m |= (1ULL << bd(rng));
        return m;
    }

    void CHAOSFPU::processFault(ThreadID tid) {
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        const o3::DynInstPtr &head = cpu->robAccess().readHeadInst(tid);
        if (!head) { stats->numSkippedNonFp++; return; }

        // Negative control: only integer instructions (method1 'int path intact')
        if (!head->isFloating()) {
            stats->numSkippedNonFp++;
            return;
        }
        if (head->getFault() != NoFault) { stats->numSkippedNonFp++; return; }

        uint64_t mask = genMask();
        if (mask == 0) return;
        // Corrupt the front instResult (writeback data path) via DynInst method.
        bool ok = head->corruptResultRegVal(mask);
        if (!ok) { stats->numSkippedNonFp++; return; }
        stats->numFpResultCorrupted++;
        stats->numFaultsInjected++;
        ++faults_injected_count;
        writeLog(tid, mask, 0, 63);
    }

    void CHAOSFPU::writeLog(ThreadID tid, uint64_t mask, int, int) {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Thread: " << tid
            << ", Site: fp_writeback_result"
            << ", Mask: 0x" << std::hex << mask << std::dec
            << (!semantic_role.empty() ? ", SemanticRole: " + semantic_role : "")
            << std::endl;
    }

    CHAOSFPU::Stats::Stats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total Exec faults injected"),
          ADD_STAT(numFpResultCorrupted, statistics::units::Count::get(),
                   "Integer writeback results corrupted (data-path)"),
          ADD_STAT(numSkippedNonFp, statistics::units::Count::get(),
                   "Skipped (ROB empty / non-int / no result / faulting)")
    {}
} // namespace gem5
