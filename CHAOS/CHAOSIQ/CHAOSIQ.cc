#include "cpu/o3/CHAOSIQ/CHAOSIQ.hh"
#include "params/CHAOSIQ.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/rob.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "base/trace.hh"
#include "debug/CHAOSIQ.hh"

#include <iostream>
#include <fstream>

namespace gem5
{

    CHAOSIQ::CHAOSIQ(const CHAOSIQParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fi_mode(stringToMode(p.mode)),
          target_src_idx(p.targetSrcIdx),
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
                "CHAOSIQ: cpu is not an O3CPU. O3-only (needs cpu->robAccess).");
        }
        if (probability > 0.0f) {
            log_stream = simout.create("iq_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSIQ: Could not open log file");
            }
            stats = std::make_unique<CHAOSIQStats>(this);
        }
    }

    void CHAOSIQ::startup()
    {
        if (!probability) return;
        unsigned next_fault_cycle_distance = inter_fault_cycles_dist(rng);
        scheduleAttackEvent(first_clock + Cycles(next_fault_cycle_distance));
    }

    CHAOSIQ::~CHAOSIQ() {}

    CHAOSIQ::Mode
    CHAOSIQ::stringToMode(const std::string &s) {
        if (s == "tag_sub")     return Mode::TagSub;
        if (s == "wake_phase")  return Mode::WakePhase;   // deferred
        if (s == "wake_omit")   return Mode::WakeOmit;     // deferred
        return Mode::SrcReadyBitFlip;  // default + "src_ready_bitflip"
    }

    const char*
    CHAOSIQ::modeToString(Mode m) {
        switch (m) {
            case Mode::SrcReadyBitFlip: return "src_ready_bitflip";
            case Mode::TagSub:          return "tag_sub";
            case Mode::WakePhase:       return "wake_phase";   // G7
            case Mode::WakeOmit:        return "wake_omit";    // G7
        }
        return "?";
    }

    void
    CHAOSIQ::scheduleAttackEvent(Cycles delay)
    {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void
    CHAOSIQ::attackCheck()
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
    CHAOSIQ::processFault(ThreadID tid)
    {
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        // Reach the ROB-head DynInst (the public IQ list is not iterable;
        // the about-to-commit DynInst is the observable IQ-state proxy).
        const o3::DynInstPtr &head = cpu->robAccess().readHeadInst(tid);
        if (!head) {
            stats->numLegalityRejects++;
            return;
        }
        size_t nsrcs = head->numSrcs();
        if (nsrcs == 0) {
            stats->numLegalityRejects++;
            return;
        }

        int src_idx = target_src_idx;
        if (src_idx < 0 || src_idx >= (int)nsrcs) {
            src_idx = std::uniform_int_distribution<int>(0, (int)nsrcs - 1)(rng);
        }

        if (fi_mode == Mode::SrcReadyBitFlip) {
            // Flip the source-ready bit (false wake / missed wake). This is
            // a single-bit toggle, not a mask — ready is 1 bit per src.
            bool old_ready = head->readySrcIdx(src_idx);
            head->readySrcIdx(src_idx, !old_ready);
            stats->numSrcReadyBitFlips++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            writeLog("src_ready_bitflip", tid, src_idx, old_ready, !old_ready, 1);
        } else if (fi_mode == Mode::TagSub) {
            // F5: substitute the src tag with another physReg's. srcRegIdx(idx)
            // returns a const ref; _srcIdx[idx] = phys_reg_id is the setter
            // (dyn_inst.hh:301). We substitute with a random valid physRegId
            // from the int class (legality: same class).
            // For now, just swap src tags between two sources of the same inst
            // (a safe in-range substitute that doesn't need a physReg lookup).
            if (nsrcs < 2) {
                stats->numLegalityRejects++;
                return;  // need >=2 srcs to swap
            }
            int other = (src_idx + 1) % nsrcs;
            PhysRegIdPtr a = head->renamedSrcIdx(src_idx);
            PhysRegIdPtr b = head->renamedSrcIdx(other);
            head->renamedSrcIdx(src_idx, b);
            head->renamedSrcIdx(other, a);
            stats->numTagSub++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            writeLog("tag_sub", tid, src_idx, false, false, 0);
        } else {
            // WakePhase / WakeOmit: deferred (need IQ timing hook).
            stats->numLegalityRejects++;
            if (write_log) {
                *(log_stream->stream())
                    << "Cycle: " << cpu->curCycle()
                    << " wake_phase/wake_omit: NOT IMPLEMENTED (needs IQ timing hook)\n";
            }
        }
    }

    void
    CHAOSIQ::writeLog(const std::string &type, ThreadID tid,
                      int src_idx, bool old_ready, bool new_ready, uint64_t mask)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Thread: " << tid
            << ", Site: iq_rob_head_proxy"
            << ", Mode: " << type
            << ", SrcIdx: " << src_idx
            << (type == "src_ready_bitflip" ?
                (std::string(", old_ready: ") + (old_ready?"1":"0") +
                 ", new_ready: " + (new_ready?"1":"0")) : "")
            << (!semantic_role.empty() ? ", SemanticRole: " + semantic_role : "")
            << std::endl;
    }

    CHAOSIQ::CHAOSIQStats::CHAOSIQStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total IQ faults injected"),
          ADD_STAT(numSrcReadyBitFlips, statistics::units::Count::get(),
                   "src_ready_bitflip faults (src-ready bit toggle)"),
          ADD_STAT(numTagSub, statistics::units::Count::get(),
                   "tag_sub faults (F5 src tag substitute)"),
          ADD_STAT(numLegalityRejects, statistics::units::Count::get(),
                   "injection attempts rejected (ROB empty / no srcs / deferred)")
    {}

} // namespace gem5
