#include "cpu/o3/CHAOSRAS/CHAOSRAS.hh"
#include "params/CHAOSRAS.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/rob.hh"
#include "cpu/o3/dyn_inst.hh"
#include "base/trace.hh"
#include "debug/CHAOSRAS.hh"

#include <iostream>
#include <fstream>

namespace gem5
{

    CHAOSRAS::CHAOSRAS(const CHAOSRASParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
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
            "CHAOSRAS: cpu is not an O3CPU. O3-only (needs robAccess).");
        if (probability > 0.0f) {
            log_stream = simout.create("ras_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSRAS: Could not open log file");
            stats = std::make_unique<CHAOSRASStats>(this);
        }
    }

    void
    CHAOSRAS::startup()
    {
        if (!probability) return;
        scheduleAttackEvent(first_clock + Cycles(inter_fault_cycles_dist(rng)));
    }
    CHAOSRAS::~CHAOSRAS() {}

    void
    CHAOSRAS::scheduleAttackEvent(Cycles delay)
    {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void
    CHAOSRAS::attackCheck()
    {
        if (!probability) return;
        uint64_t before = faults_injected_count;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *tc = cpu->getContext(tid);
            if (!tc || tc->status() == ThreadContext::Halted) continue;
            processFault(tid);
        }
        if (max_faults == 0 || faults_injected_count < max_faults) {
            // min +1-cycle backoff on no-op polls (same fix as CHAOSFPU/
            // CHAOSRenameMap: geometric(1.0)=0-interval polls otherwise).
            unsigned next = inter_fault_cycles_dist(rng);
            if (faults_injected_count == before)
                next = std::max(next, (unsigned)1);
            Cycles nc = cpu->curCycle() + Cycles(next);
            if (last_clock == Cycles(0) || nc <= last_clock)
                scheduleAttackEvent(Cycles(next));
        }
    }

    void
    CHAOSRAS::processFault(ThreadID tid)
    {
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        const o3::DynInstPtr &head = cpu->robAccess().readHeadInst(tid);
        if (!head) { stats->numSkippedNoFault++; return; }

        // Only a FAULTING head is eligible: the RAS-escape mechanism
        // suppresses the error REPORT of an actual error. A clean head has
        // nothing to suppress (honest skip).
        if (head->getFault() == NoFault) {
            stats->numSkippedNoFault++;
            return;
        }
        // SE syscalls present as "Supervisor Call" faults at the commit
        // head BEFORE any program-level fault; suppressing one breaks the
        // syscall path itself (observed: every seed hit SVC first, the
        // workload then core-dumped on the BROKEN syscall, not the target
        // DABT). Real RAS ERR* records concern hardware error reports
        // (data/instruction aborts, SError) — not the syscall mechanism.
        const std::string fname = head->getFault()->name();
        if (fname == "Supervisor Call" || fname == "System Call") {
            stats->numSkippedNoFault++;
            return;
        }
        // Time window.
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return;
        if (last_clock != Cycles(0) && cur > last_clock) return;

        // Probability gate (per-eligible-head Bernoulli).
        std::uniform_real_distribution<float> d(0.0f, 1.0f);
        if (d(rng) >= probability) return;

        // SUPPRESS: clear the fault (the ERR* record is never written —
        // the DUE becomes an unreported SDC) and log the record miss.
        uint64_t seq = head->seqNum;
        Fault &fref = head->getFault();
        fref = NoFault;
        stats->numFaultsInjected++;
        stats->numRasRecordMisses++;
        ++faults_injected_count;
        if (write_log) {
            *(log_stream->stream())
                << "Cycle: " << cur
                << ", CPU: " << cpu->name()
                << ", Thread: " << tid
                << ", Site: commit_head_ras_record"
                << ", Mode: ras_escape (ERR* record suppressed)"
                << ", Seq: " << seq
                << ", SuppressedFault: " << fname
                << (!semantic_role.empty()
                    ? ", SemanticRole: " + semantic_role : "")
                << std::endl;
        }
    }

    CHAOSRAS::CHAOSRASStats::CHAOSRASStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total RAS-record suppressions applied"),
          ADD_STAT(numRasRecordMisses, statistics::units::Count::get(),
                   "DUE events that became unreported (RAS record misses)"),
          ADD_STAT(numSkippedNoFault, statistics::units::Count::get(),
                   "Polls skipped (ROB empty / head not faulting)")
    {}
} // namespace gem5
