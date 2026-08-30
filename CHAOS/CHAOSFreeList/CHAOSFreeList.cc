#include "cpu/o3/CHAOSFreeList/CHAOSFreeList.hh"
#include "params/CHAOSFreeList.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/free_list.hh"
#include "cpu/o3/rename_map.hh"
#include "cpu/reg_class.hh"
#include "base/trace.hh"
#include "debug/CHAOSFreeList.hh"

#include <iostream>
#include <fstream>

namespace gem5
{

    CHAOSFreeList::CHAOSFreeList(const CHAOSFreeListParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fi_mode(stringToMode(p.mode)),
          reg_target_class(stringToRegClassSel(p.regTargetClass)),
          target_phys_idx(p.targetPhysReg),
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
                "CHAOSFreeList: cpu is not an O3CPU. O3-only (needs "
                "physFreeList). Cast failed.");
        }
        if (probability > 0.0f) {
            log_stream = simout.create("freelist_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSFreeList: Could not open log file");
            }
            stats = std::make_unique<CHAOSFreeListStats>(this);
        }
    }

    void CHAOSFreeList::startup()
    {
        if (!probability) return;
        unsigned next_fault_cycle_distance = inter_fault_cycles_dist(rng);
        scheduleAttackEvent(first_clock + Cycles(next_fault_cycle_distance));
    }

    CHAOSFreeList::~CHAOSFreeList() {}

    CHAOSFreeList::Mode
    CHAOSFreeList::stringToMode(const std::string &s) {
        if (s == "pop_wrong") return Mode::PopWrong;
        return Mode::MarkFree;  // default + "mark_free"
    }

    const char*
    CHAOSFreeList::modeToString(Mode m) {
        switch (m) {
            case Mode::MarkFree: return "mark_free";
            case Mode::PopWrong: return "pop_wrong";  // G7: clear -Wswitch
        }
        return "?";
    }

    CHAOSFreeList::RegClassSel
    CHAOSFreeList::stringToRegClassSel(const std::string &s) {
        if (s == "floating_point") return RegClassSel::FloatingPoint;
        if (s == "vector") return RegClassSel::Vector;
        return RegClassSel::Integer;
    }

    void
    CHAOSFreeList::scheduleAttackEvent(Cycles delay)
    {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void
    CHAOSFreeList::attackCheck()
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
    CHAOSFreeList::processFault(ThreadID tid)
    {
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        gem5::ThreadContext *thread_context = cpu->getContext(tid);
        if (!thread_context) return;
        gem5::BaseISA *isa = thread_context->getIsaPtr();
        if (!isa) return;

        const auto &reg_classes = isa->regClasses();
        gem5::RegClassType target_class = gem5::IntRegClass;
        if (reg_target_class == RegClassSel::FloatingPoint)
            target_class = gem5::FloatRegClass;
        else if (reg_target_class == RegClassSel::Vector)
            target_class = gem5::VecRegClass;
        const gem5::RegClass *reg_class = reg_classes[target_class];
        if (!reg_class || reg_class->numRegs() == 0) return;

        // Choose a physReg target. If directed, use target_phys_idx; else
        // scan the RAT for a currently-LIVE (mapped) physReg.
        int phys_idx = target_phys_idx;
        int donor_arch = -1;
        PhysRegIdPtr target_phys = nullptr;

        if (phys_idx >= 0) {
            // directed: fetch the physRegId by index
            if (reg_target_class == RegClassSel::Integer)
                target_phys = cpu->physRegFile().intPhysRegId(phys_idx);
            else if (reg_target_class == RegClassSel::FloatingPoint)
                target_phys = cpu->physRegFile().floatPhysRegId(phys_idx);
            else
                target_phys = cpu->physRegFile().vecPhysRegId(phys_idx);
        } else {
            // scan RAT: find an arch reg whose lookup physReg is LIVE
            // (isFree==false). This is the method1 residue target.
            int n_arch = reg_class->numRegs();
            for (int tries = 0; tries < n_arch; ++tries) {
                int cand = std::uniform_int_distribution<int>(0, n_arch - 1)(rng);
                gem5::RegId cand_reg(*reg_class, cand);
                const gem5::RegId cand_flat = cand_reg.flatten(*isa);
                PhysRegIdPtr pp = cpu->frontRenameMap()[tid].lookup(cand_flat);
                if (pp) {
                    // is it LIVE (not free)?
                    if (!cpu->physFreeList().isFree(target_class, pp)) {
                        phys_idx = pp->index();
                        target_phys = pp;
                        donor_arch = cand;
                        break;
                    }
                }
            }
        }
        if (!target_phys) {
            stats->numLegalityRejects++;
            return;
        }

        // Legality: target must be LIVE (not already free). Adding an already-
        // free reg is a no-op (no residue). Reject if free.
        if (cpu->physFreeList().isFree(target_class, target_phys)) {
            stats->numLegalityRejects++;
            if (write_log) {
                *(log_stream->stream())
                    << "Cycle: " << cpu->curCycle()
                    << " mark_free REJECT: PhysReg[" << phys_idx
                    << "] is already free (not live) — no residue possible\n";
            }
            return;
        }

        // mark_free: add the live physReg to the free list. The next rename
        // getReg() will allocate it to a NEW arch reg -> double-occupancy ->
        // the old owner's in-flight reads return the new owner's value
        // (method1 history residue).
        cpu->physFreeList().addReg(target_phys);
        stats->numMarkFree++;

        if (fi_mode == Mode::PopWrong) {
            // Immediately consume the wrongly-added slot via getReg, forcing
            // the double-allocation at inject time. The returned physReg is
            // the one we just (wrongly) marked free.
            if (cpu->physFreeList().numFreeRegs(target_class) > 0) {
                PhysRegIdPtr popped = cpu->physFreeList().getReg(target_class);
                stats->numPopWrong++;
                if (write_log) {
                    *(log_stream->stream())
                        << "Cycle: " << cpu->curCycle()
                        << " pop_wrong: getReg returned PhysReg["
                        << (popped ? popped->index() : -1)
                        << "] (double-allocated)\n";
                }
            }
        }

        stats->numFaultsInjected++;
        ++faults_injected_count;
        writeLog(modeToString(fi_mode), tid, phys_idx, donor_arch,
                 std::string("live physReg added to free list (method1 residue)"));
    }

    void
    CHAOSFreeList::writeLog(const std::string &type, ThreadID tid,
                            int phys_idx, int donor_arch,
                            const std::string &detail)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Thread: " << tid
            << ", Site: phys_free_list"
            << ", Mode: " << type
            << ", PhysReg: " << phys_idx
            << ", donor_arch: " << donor_arch
            << ", " << detail
            << (!semantic_role.empty() ? ", SemanticRole: " + semantic_role : "")
            << std::endl;
    }

    CHAOSFreeList::CHAOSFreeListStats::CHAOSFreeListStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total freelist faults injected"),
          ADD_STAT(numMarkFree, statistics::units::Count::get(),
                   "mark_free faults (live physReg added to free list)"),
          ADD_STAT(numPopWrong, statistics::units::Count::get(),
                   "pop_wrong faults (immediate double-allocation)"),
          ADD_STAT(numLegalityRejects, statistics::units::Count::get(),
                   "injection attempts rejected by legality (target was free)")
    {}

} // namespace gem5
