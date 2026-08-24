#include "cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh"
#include "params/CHAOSPhysReg.hh"

#include <iostream>
#include <fstream>
#include <vector>
#include <random>
#include <bitset>

#include "base/output.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/regfile.hh"
#include "cpu/o3/rename_map.hh"
#include "arch/generic/isa.hh"

namespace gem5
{

    CHAOSPhysReg::CHAOSPhysReg(const CHAOSPhysRegParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          fi_mode(stringToMode(p.injectionMode)),
          target_phys_idx(p.targetPhysRegIdx),
          target_arch_idx(p.targetArchRegIdx),
          probability(p.probability),
          num_bits_to_change(p.bitsToChange),
          fault_type_enum(stringToFaultType(p.faultType)),
          fault_mask(std::bitset<32>(p.faultMask)),
          bit_flip_prob(0.9),
          stuck_at_zero_prob(0.05),
          stuck_at_one_prob(0.05),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          attackEvent([this] { this->attackCheck(); }, name()),
          periodicCheck([this] { this->checkPermanent(); }, name() + ".periodicCheck"),
          readTraceEvent([this] { this->readTraceCheck(); }, name() + ".readTrace"),
          stats(nullptr)
    {
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSPhysReg: cpu is not an O3CPU. CHAOSPhysReg only supports "
                "O3CPU (it needs regFile/renameMap). Cast failed.");
        }
        if (probability > 0.0) {
            log_stream = simout.create("fault_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSPhysReg: Could not open log file");
            }
            stats = std::make_unique<CHAOSPhysRegStats>(this);
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            if (num_bits_to_change == -1) {
                std::uniform_int_distribution<int> dist(1, 32);
                num_bits_to_change = dist(rng);
            }
            inter_fault_cycles_dist = std::geometric_distribution<unsigned>(probability);
            unsigned next_fault_cycle_distance = inter_fault_cycles_dist(rng);
            scheduleAttackEvent(first_clock + Cycles(next_fault_cycle_distance));
            scheduleCheckPermanentFault(first_clock + Cycles(1));
        }
    }

    CHAOSPhysReg::CHAOSPhysRegStats::CHAOSPhysRegStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total number of faults injected"),
          ADD_STAT(numBitFlips, statistics::units::Count::get(),
                   "Number of bit flip faults injected"),
          ADD_STAT(numStuckAtZero, statistics::units::Count::get(),
                   "Number of stuck-at-0 faults injected"),
          ADD_STAT(numStuckAtOne, statistics::units::Count::get(),
                   "Number of stuck-at-1 faults injected"),
          ADD_STAT(numPermanentFaults, statistics::units::Count::get(),
                   "Total number of permanent faults injected")
    {}

    CHAOSPhysReg::~CHAOSPhysReg() {}

    CHAOSPhysReg::FaultType
    CHAOSPhysReg::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        else if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        else if (s == "stuck_at_one") return FaultType::StuckAtOne;
        return FaultType::Random;
    }

    const char*
    CHAOSPhysReg::faultTypeToString(CHAOSPhysReg::FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
        }
        return "random";
    }

    CHAOSPhysReg::Mode
    CHAOSPhysReg::stringToMode(const std::string &s) {
        if (s == "arch_commit") return Mode::ArchCommit;
        else if (s == "arch_frontend") return Mode::ArchFrontend;
        return Mode::Phys;
    }

    void
    CHAOSPhysReg::scheduleAttackEvent(Cycles delay)
    {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void
    CHAOSPhysReg::unscheduleAttackEvent()
    {
        if (attackEvent.scheduled()) attackEvent.squash();
        if (periodicCheck.scheduled()) periodicCheck.squash();
        // NOTE: readTraceEvent is intentionally NOT squashed here — it must
        // keep counting reads of the injected phys slot until the workload
        // ends (all threads halt). It is squashed only from readTraceCheck
        // when the workload has halted.
    }

    void
    CHAOSPhysReg::scheduleCheckPermanentFault(Cycles delay)
    {
        if (!periodicCheck.scheduled())
            schedule(periodicCheck, cpu->clockEdge(delay));
    }

    int
    CHAOSPhysReg::generateRandomMask(std::mt19937 &gen, int bits_to_change, int len)
    {
        int mask = 0;
        std::uniform_int_distribution<int> bitDist(0, len - 1);
        while (bits_to_change-- > 0) mask |= (1 << bitDist(gen));
        return mask;
    }

    // Core: resolve a target PHYSICAL register id according to the fi_mode,
    // then read-modify-write it directly in the physical register file.
    // This is the key difference from CHAOSReg (which wrote the commitRenameMap
    // phys reg via ThreadContext::setReg — a backdoor that doesn't propagate
    // to in-flight instructions on O3).
    void
    CHAOSPhysReg::processFault(ThreadID tid)
    {
        // 1. Resolve target physical register id.
        PhysRegIdPtr phys_reg = nullptr;
        int chosen_phys_idx = -1;     // for logging
        int chosen_arch_idx = -1;     // for logging (arch modes)

        if (fi_mode == Mode::Phys) {
            // Inject by physical register index. A real defective cell has no
            // notion of architectural registers; whoever is allocated to this
            // slot gets hit. This is the ITC'23/GeFIN abstraction.
            int n = cpu->physRegFile().numIntPhysRegs();
            if (n <= 0) return;
            chosen_phys_idx = (target_phys_idx >= 0)
                ? target_phys_idx
                : std::uniform_int_distribution<>(0, n - 1)(rng);
            if (chosen_phys_idx >= n) return;
            phys_reg = cpu->physRegFile().intPhysRegId(chosen_phys_idx);

            // Liveness probe: is this physical slot currently FREE (inactive)
            // or ALLOCATED (active)? Correct criterion per project notes: a phys
            // reg NOT in the free list is allocated — it may be held as a source
            // by in-flight renamed-but-unexecuted instructions even if no rename
            // map entry currently maps it (older version superseded but not yet
            // released). So "not free" = active = may be read. (The earlier
            // "rename map reverse-walk" criterion was too narrow and mislabeled
            // some live slots as dead, producing the dead-slot SDC anomaly.)
            bool is_free = cpu->physFreeList().isFree(
                gem5::IntRegClass, phys_reg);
            free_list_size_at_inject = cpu->physFreeList().numFreeRegs(
                gem5::IntRegClass);
            if (!is_free) {
                // active — also record which arch reg (if any) maps to it now,
                // for diagnostics (walk rename map; best-effort, not the
                // liveness source of truth).
                gem5::ThreadContext *tc = cpu->getContext(tid);
                if (tc) {
                    gem5::BaseISA *isa = tc->getIsaPtr();
                    if (isa) {
                        const auto &rc = isa->regClasses();
                        const gem5::RegClass *ic = rc[gem5::IntRegClass];
                        int na = ic ? ic->numRegs() : 0;
                        int cap = na < 31 ? na : 31;  // X0-X30
                        for (int a = 0; a < cap; a++) {
                            gem5::RegId ar(*ic, a);
                            const gem5::RegId flat = ar.flatten(*isa);
                            PhysRegIdPtr pm = cpu->frontRenameMap()[tid].lookup(flat);
                            if (pm && pm->index() == chosen_phys_idx) {
                                chosen_arch_idx = a;
                                break;
                            }
                        }
                    }
                }
            } else {
                chosen_arch_idx = -2;  // sentinel: free/inactive
            }
        } else {
            // arch_frontend: renameMap.lookup      (in-flight mapping)
            // arch_commit:   commitRenameMap.lookup (committed mapping = CHAOSReg)
            gem5::ThreadContext *thread_context = cpu->getContext(tid);
            if (!thread_context) return;
            gem5::BaseISA *isa = thread_context->getIsaPtr();
            if (!isa) return;
            const auto &reg_classes = isa->regClasses();
            const gem5::RegClass *reg_class = reg_classes[gem5::IntRegClass];
            if (!reg_class || reg_class->numRegs() == 0) return;
            int arch_idx = target_arch_idx;
            if (arch_idx < 0 || arch_idx >= reg_class->numRegs()) return;
            chosen_arch_idx = arch_idx;
            gem5::RegId arch_reg(*reg_class, arch_idx);
            // flatten to match the per-class rename map's indexing
            const gem5::RegId flat = arch_reg.flatten(*isa);
            if (fi_mode == Mode::ArchFrontend)
                phys_reg = cpu->frontRenameMap()[tid].lookup(flat);
            else // ArchCommit
                phys_reg = cpu->commitRenameMapAccess()[tid].lookup(flat);
            if (!phys_reg) return;
            chosen_phys_idx = phys_reg->index();
        }

        if (!phys_reg) return;

        // 2. Read current physical reg value, apply fault, write back.
        gem5::RegVal reg_val = cpu->physRegFile().getReg(phys_reg);

        int mask = fault_mask.any()
            ? fault_mask.to_ulong()
            : generateRandomMask(rng, num_bits_to_change, sizeof(reg_val) << 3);

        FaultType chosen = fault_type_enum;
        if (fault_type_enum == FaultType::Random) {
            int idx = random_fault_distribution(rng);
            chosen = static_cast<FaultType>(idx);
        }

        switch (chosen) {
            case FaultType::StuckAtZero:
                reg_val &= ~mask;
                stats->numStuckAtZero++;
                stats->numPermanentFaults++;
                permanent_faults[{tid, chosen_phys_idx}] = {chosen, mask, true};
                break;
            case FaultType::StuckAtOne:
                reg_val |= mask;
                stats->numStuckAtOne++;
                stats->numPermanentFaults++;
                permanent_faults[{tid, chosen_phys_idx}] = {chosen, mask, true};
                break;
            case FaultType::BitFlip:
                reg_val ^= mask;
                stats->numBitFlips++;
                break;
            default: break;
        }

        cpu->physRegFile().setReg(phys_reg, reg_val);
        stats->numFaultsInjected++;
        ++faults_injected_count;

        // Start read-tracing this phys slot until workload end, to measure
        // whether the injected cell is actually read after injection.
        // (Closure check: SDC|read>0 should be similar for layer2 & layer3,
        //  SDC|read==0 should be ~0.) The readTraceEvent reschedules itself
        // every 1000 cycles until all threads halt, then writes the final
        // read count to the log.
        traced_phys_idx = chosen_phys_idx;
        reads_before_overwrite = 0;
        trace_overwritten = false;
        overwrite_recorded = false;
        overwritten_at_cycle = 0;
        cpu->physRegFile().setReadTraceTarget(chosen_phys_idx);
        if (!readTraceEvent.scheduled()) {
            schedule(readTraceEvent, cpu->clockEdge(Cycles(100000)));
        }

        if (write_log) {
            *(log_stream->stream())
                << "Cycle: " << cpu->curCycle()
                << ", CPU: " << cpu->name()
                << ", Thread: " << tid
                << ", Mode: " << (fi_mode == Mode::Phys ? "phys"
                              : fi_mode == Mode::ArchFrontend ? "arch_frontend"
                              : "arch_commit")
                << ", PhysReg[" << chosen_phys_idx << "]"
                << (fi_mode == Mode::Phys
                    ? (chosen_arch_idx == -2
                       ? " (Inactive/free slot)"
                       : (chosen_arch_idx >= 0
                          ? " (Active, mapped from ArchReg[" + std::to_string(chosen_arch_idx) + "])"
                          : " (Active, held by in-flight inst, no current rename-map entry)"))
                    : (chosen_arch_idx >= 0
                       ? " (<= ArchReg[" + std::to_string(chosen_arch_idx) + "])"
                       : ""))
                << ", FaultType: " << faultTypeToString(chosen)
                << ", Mask: " << std::bitset<32>(mask)
                << ", FreeListSize: " << free_list_size_at_inject
                << std::endl;
        }
    }

    void
    CHAOSPhysReg::attackCheck()
    {
        if (!probability) return;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *thread_context = cpu->getContext(tid);
            if (!thread_context || thread_context->status() == ThreadContext::Halted)
                continue;
            processFault(tid);
        }
        // maxFaults cap (mirrors CHAOSReg)
        if (max_faults != 0 && faults_injected_count >= max_faults) {
            unscheduleAttackEvent();
            return;
        }
        bool any_active = false;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *thread_context = cpu->getContext(tid);
            if (thread_context && thread_context->status() != ThreadContext::Halted) {
                any_active = true; break;
            }
        }
        if (any_active) {
            Cycles next = Cycles(inter_fault_cycles_dist(rng));
            if (last_clock == 0 || (next + cpu->curCycle()) <= last_clock)
                scheduleAttackEvent(next);
        } else {
            unscheduleAttackEvent();
        }
    }

    void
    CHAOSPhysReg::checkPermanent()
    {
        // NOTE: periodic re-apply is the WRONG stuck mechanism (see project
        // notes). The correct one is a write-path mask hook in
        // PhysRegFile::setReg. This periodic re-apply is kept only as a
        // fallback for the 'arch_*' modes' compatibility and will NOT make
        // stuck faults truly permanent on O3 for the same reason CHAOSReg's
        // didn't propagate (commits vs in-flight). Phys-fi_mode stuck also needs
        // the write-path mask to be correct.
        for (auto &entry : permanent_faults) {
            if (!entry.second.update) continue;
            ThreadID tid = entry.first.first;
            int phys_idx = entry.first.second;
            if (phys_idx < 0 || phys_idx >= cpu->physRegFile().numIntPhysRegs()) continue;
            PhysRegIdPtr phys_reg = cpu->physRegFile().intPhysRegId(phys_idx);
            try {
                gem5::RegVal v = cpu->physRegFile().getReg(phys_reg);
                switch (entry.second.fault_type) {
                    case FaultType::StuckAtZero: v &= ~entry.second.mask; break;
                    case FaultType::StuckAtOne:  v |= entry.second.mask; break;
                    default: break;
                }
                cpu->physRegFile().setReg(phys_reg, v);
                entry.second.update = false; // (kept for compatibility; TODO remove + write-path mask)
            } catch (...) {}
            scheduleCheckPermanentFault(Cycles(1));
        }
    }

    void
    CHAOSPhysReg::readTraceCheck()
    {
        // Poll the PhysRegFile's read counter for the INJECTED VALUE.
        // Counting stops once the slot is written (injected value destroyed),
        // so reads_before_overwrite = # reads of the injected value specifically.
        reads_before_overwrite = cpu->physRegFile().getReadsBeforeOverwrite();
        // Capture the cycle at the moment the value is overwritten (once).
        if (cpu->physRegFile().isTraceOverwritten() && !overwrite_recorded) {
            overwritten_at_cycle = cpu->curCycle();
            overwrite_recorded = true;
        }
        if (write_log) {
            *(log_stream->stream())
                << "ReadTracePoll: cycle " << cpu->curCycle()
                << " PhysReg[" << traced_phys_idx
                << "] reads_before_overwrite=" << reads_before_overwrite
                << " overwritten=" << (overwrite_recorded ? 1 : 0)
                << (overwrite_recorded ? (" at_cycle=" + std::to_string(overwritten_at_cycle)) : "")
                << std::endl;
        }
        bool any_active = false;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *thread_context = cpu->getContext(tid);
            if (thread_context && thread_context->status() != ThreadContext::Halted) {
                any_active = true; break;
            }
        }
        if (any_active) {
            schedule(readTraceEvent, cpu->clockEdge(Cycles(100000)));
        } else {
            if (write_log) {
                *(log_stream->stream())
                    << "ReadTraceFinal: PhysReg[" << traced_phys_idx
                    << "] reads_before_overwrite=" << reads_before_overwrite
                    << " overwritten=" << (overwrite_recorded ? 1 : 0)
                    << (overwrite_recorded ? (" at_cycle=" + std::to_string(overwritten_at_cycle)) : "")
                    << " (workload halted)"
                    << std::endl;
            }
            cpu->physRegFile().clearReadTraceTarget();
            traced_phys_idx = -1;
        }
    }

} // namespace gem5
