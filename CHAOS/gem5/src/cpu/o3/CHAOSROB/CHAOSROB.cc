#include "cpu/o3/CHAOSROB/CHAOSROB.hh"
#include "params/CHAOSROB.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/rob.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/o3/dyn_inst_ptr.hh"  // DynInstPtr
#include "base/trace.hh"
#include "debug/CHAOSROB.hh"

#include <iostream>
#include <fstream>

namespace gem5
{

    CHAOSROB::CHAOSROB(const CHAOSROBParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fi_mode(stringToMode(p.mode)),
          distance_from_head(p.distanceFromHead),
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
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSROB: cpu is not an O3CPU. O3-only (needs cpu->rob). "
                "Cast failed.");
        }
        if (probability > 0.0f) {
            log_stream = simout.create("rob_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSROB: Could not open log file");
            }
            stats = std::make_unique<CHAOSROBStats>(this);
            // S6-4 spec_leak: register on Rename so doSquash can reach us.
            cpu->renameAccess().setChaosRob(this);
        }
    }

    void CHAOSROB::startup()
    {
        if (!probability) return;
        // S6-4: spec_leak is driven by the Rename::doSquash hook (event-
        // driven), NOT by attackEvent polling — do not schedule the attack
        // event in that mode (prob=1.0 would otherwise poll every cycle).
        if (fi_mode == Mode::SpecLeak) return;
        unsigned next_fault_cycle_distance = inter_fault_cycles_dist(rng);
        scheduleAttackEvent(first_clock + Cycles(next_fault_cycle_distance));
    }

    CHAOSROB::~CHAOSROB() {}

    CHAOSROB::Mode
    CHAOSROB::stringToMode(const std::string &s) {
        if (s == "exc_suppress") return Mode::ExcSuppress;
        if (s == "spec_leak") return Mode::SpecLeak;  // deferred (needs squash hook)
        return Mode::EntryBitFlip;  // default + "entry_bitflip"
    }

    const char*
    CHAOSROB::modeToString(Mode m) {
        switch (m) {
            case Mode::EntryBitFlip: return "entry_bitflip";
            case Mode::ExcSuppress: return "exc_suppress";
            case Mode::SpecLeak:     return "spec_leak";  // G7: clear -Wswitch
        }
        return "?";
    }

    void
    CHAOSROB::scheduleAttackEvent(Cycles delay)
    {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void
    CHAOSROB::attackCheck()
    {
        if (!probability) return;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *thread_context = cpu->getContext(tid);
            if (!thread_context || thread_context->status() == ThreadContext::Halted)
                continue;
            processFault(tid);
        }
        if (max_faults == 0 || faults_injected_count < max_faults) {
            unsigned next = inter_fault_cycles_dist(rng);
            Cycles next_cycle = cpu->curCycle() + Cycles(next);
            if (last_clock == Cycles(0) || next_cycle <= last_clock)
                scheduleAttackEvent(Cycles(next));
        }
    }

    void
    CHAOSROB::processFault(ThreadID tid)
    {
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        // Get the ROB head (about-to-commit) DynInst. distance_from_head>0
        // would walk the ROB list, but the public API only exposes head/tail;
        // we use head (the most commit-relevant entry). DynInstPtr is in o3.
        const o3::DynInstPtr &head = cpu->robAccess().readHeadInst(tid);
        if (!head) {
            stats->numLegalityRejects++;
            return;  // ROB empty
        }

        uint64_t seq = head->seqNum;
        bool had_fault = (head->getFault() != NoFault);

        if (fi_mode == Mode::EntryBitFlip) {
            // Flip a bit of the head DynInst's seqNum. seqNum is public
            // (dyn_inst.hh:124). A corrupted seqNum breaks re-ordering
            // comparisons -> may mis-commit or trigger an exception.
            uint64_t mask = fault_mask;
            if (mask == 0) {
                std::uniform_int_distribution<int> bitDist(0, 15);
                mask = 1ULL << bitDist(rng);
            }
            uint64_t old_seq = seq;
            head->seqNum = seq ^ mask;
            stats->numEntryBitFlips++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            writeLog("entry_bitflip", tid, old_seq, old_seq, head->seqNum,
                     had_fault, false);
        } else if (fi_mode == Mode::ExcSuppress) {
            // Clear the head DynInst's fault if it has one (DUE -> SDC: the
            // trap that should signal a loud error is silenced). getFault()&
            // returns a mutable ref (dyn_inst.hh:506).
            if (!had_fault) {
                // No fault to suppress — reject (legality). exc_suppress only
                // applies to a faulting instruction.
                stats->numLegalityRejects++;
                if (write_log) {
                    *(log_stream->stream())
                        << "Cycle: " << cpu->curCycle()
                        << " exc_suppress REJECT: ROB head seq=" << seq
                        << " has no fault (NoFault) — nothing to suppress\n";
                }
                return;
            }
            Fault &fref = head->getFault();
            fref = NoFault;  // clear the fault -> commit proceeds -> SDC
            stats->numExcSuppress++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            writeLog("exc_suppress", tid, seq, seq, seq, true, true);
        } else if (fi_mode == Mode::SpecLeak) {
            // spec_leak is now driven by Rename::doSquash's maybeDelayFree
            // hook (constructor registered us on Rename). Nothing to do
            // here — the attackEvent only services entry_bitflip/exc_suppress.
            return;
        }
    }

    bool
    CHAOSROB::maybeDelayFree(const PhysRegIdPtr &reg)
    {
        if (fi_mode != Mode::SpecLeak) return false;
        if (probability <= 0.0f) return false;
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return false;
        if (last_clock != Cycles(0) && cur > last_clock) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return false;

        // Skip the freelist return: the wrong-path dest physReg leaks.
        stats->numSpecLeak++;
        stats->numFaultsInjected++;
        ++faults_injected_count;
        if (write_log) {
            *(log_stream->stream())
                << "Cycle: " << cpu->curCycle()
                << ", CPU: " << cpu->name()
                << ", Site: rename_doSquash_freelist_skip"
                << ", Mode: spec_leak"
                << ", PhysReg: " << reg->index()
                << std::endl;
        }
        return true;
    }

    void
    CHAOSROB::writeLog(const std::string &type, ThreadID tid,
                       uint64_t seq, uint64_t old_seq, uint64_t new_seq,
                       bool had_fault, bool cleared_fault)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Thread: " << tid
            << ", Site: rob_head"
            << ", Mode: " << type
            << ", Seq: " << seq
            << (type == "entry_bitflip" ?
                (std::string(", old_seq: ") + std::to_string(old_seq) +
                 ", new_seq: " + std::to_string(new_seq)) : "")
            << ", had_fault: " << (had_fault ? 1 : 0)
            << ", cleared_fault: " << (cleared_fault ? 1 : 0)
            << (!semantic_role.empty() ? ", SemanticRole: " + semantic_role : "")
            << std::endl;
    }

    CHAOSROB::CHAOSROBStats::CHAOSROBStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total ROB faults injected"),
          ADD_STAT(numEntryBitFlips, statistics::units::Count::get(),
                   "entry_bitflip faults (seqNum bit flip on ROB head)"),
          ADD_STAT(numExcSuppress, statistics::units::Count::get(),
                   "exc_suppress faults (fault cleared -> DUE-to-SDC)"),
          ADD_STAT(numSpecLeak, statistics::units::Count::get(),
                   "spec_leak faults (deferred, needs squash hook)"),
          ADD_STAT(numLegalityRejects, statistics::units::Count::get(),
                   "injection attempts rejected (ROB empty / no fault / spec_leak)")
    {}

} // namespace gem5
