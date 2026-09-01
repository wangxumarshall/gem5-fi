#include "cpu/o3/CHAOSL1DForward/CHAOSL1DForward.hh"
#include "params/CHAOSL1DForward.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/rob.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "base/trace.hh"
#include "debug/CHAOSL1DForward.hh"
#include <iostream>
#include <fstream>

namespace gem5
{
    CHAOSL1DForward::CHAOSL1DForward(const CHAOSL1DForwardParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fault_mask(p.faultMask),
          num_bits_to_change(p.bitsToChange),
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
            "CHAOSL1DForward: cpu not O3CPU. O3-only (needs robAccess).");
        if (probability > 0.0f) {
            log_stream = simout.create("l1d_fwd_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSL1DForward: Could not open log file");
            stats = std::make_unique<Stats>(this);
        }
    }

    void CHAOSL1DForward::startup() {
        if (!probability) return;
        scheduleAttackEvent(first_clock + Cycles(inter_fault_cycles_dist(rng)));
    }
    CHAOSL1DForward::~CHAOSL1DForward() {}

    void CHAOSL1DForward::scheduleAttackEvent(Cycles delay) {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void CHAOSL1DForward::attackCheck() {
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

    uint64_t CHAOSL1DForward::genMask() {
        if (fault_mask) return fault_mask;
        std::uniform_int_distribution<int> bd(0, 63);
        uint64_t m = 0;
        for (int i = 0; i < num_bits_to_change; ++i) m |= (1ULL << bd(rng));
        return m;
    }

    void CHAOSL1DForward::processFault(ThreadID tid) {
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        const o3::DynInstPtr &head = cpu->robAccess().readHeadInst(tid);
        if (!head) { stats->numSkippedNonLoad++; return; }

        // PCE: only loads — the data path between cache return and PhysReg
        // writeback (post-ECC-check). Distinct from CHAOSLSQFwd (store→load
        // forwarding) and CHAOSCache (cache data byte): this corrupts the
        // load RESULT after ECC passed, modeling the inevitable escape.
        if (!head->isLoad()) {
            stats->numSkippedNonLoad++;
            return;
        }
        if (head->getFault() != NoFault) { stats->numSkippedNonLoad++; return; }

        uint64_t mask = genMask();
        if (mask == 0) return;
        bool ok = head->corruptResultRegVal(mask);
        if (!ok) { stats->numSkippedNonLoad++; return; }
        stats->numLoadResultCorrupted++;
        stats->numFaultsInjected++;
        ++faults_injected_count;
        writeLog(tid, mask);
    }

    void CHAOSL1DForward::writeLog(ThreadID tid, uint64_t mask) {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Thread: " << tid
            << ", Site: l1d_post_check_escape"
            << ", Mask: 0x" << std::hex << mask << std::dec
            << (!semantic_role.empty() ? ", SemanticRole: " + semantic_role : "")
            << std::endl;
    }

    CHAOSL1DForward::Stats::Stats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total PCE faults injected"),
          ADD_STAT(numLoadResultCorrupted, statistics::units::Count::get(),
                   "Load results corrupted (post-check escape, post-ECC)"),
          ADD_STAT(numSkippedNonLoad, statistics::units::Count::get(),
                   "Skipped (ROB empty / non-load / no result / faulting)")
    {}
} // namespace gem5
