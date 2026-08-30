#include "cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh"
#include "params/CHAOSRenameMap.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/o3/rename_map.hh"
#include "cpu/reg_class.hh"
#include "base/trace.hh"
#include "debug/CHAOSRenameMap.hh"

#include <iostream>
#include <fstream>

namespace gem5
{

    CHAOSRenameMap::CHAOSRenameMap(const CHAOSRenameMapParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fi_mode(stringToMode(p.mode)),
          reg_target_class(stringToRegClassSel(p.regTargetClass)),
          target_arch_idx(p.targetArchReg),
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
          periodicCheck([this] { this->checkPermanent(); }, name() + ".periodicCheck"),
          stats(nullptr)
    {
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSRenameMap: cpu is not an O3CPU. O3-only (needs "
                "frontRenameMap). Cast failed.");
        }
        if (probability > 0.0f) {
            log_stream = simout.create("rat_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSRenameMap: Could not open log file");
            }
            stats = std::make_unique<CHAOSRenameMapStats>(this);
        }
    }

    void CHAOSRenameMap::startup()
    {
        if (!probability) return;
        unsigned next_fault_cycle_distance = inter_fault_cycles_dist(rng);
        scheduleAttackEvent(first_clock + Cycles(next_fault_cycle_distance));
        if (fi_mode == Mode::F4FieldStuck) {
            schedule(periodicCheck, cpu->clockEdge(first_clock + Cycles(1)));
        }
    }

    CHAOSRenameMap::~CHAOSRenameMap() {}

    CHAOSRenameMap::Mode
    CHAOSRenameMap::stringToMode(const std::string &s) {
        if (s == "map_bitflip") return Mode::MapBitFlip;
        if (s == "f4_field_stuck") return Mode::F4FieldStuck;
        return Mode::F5Substitute;  // default + "f5_substitute"
    }

    const char*
    CHAOSRenameMap::modeToString(Mode m) {
        switch (m) {
            case Mode::MapBitFlip: return "map_bitflip";
            case Mode::F5Substitute: return "f5_substitute";
            case Mode::F4FieldStuck: return "f4_field_stuck";  // G7: clear -Wswitch
        }
        return "?";
    }

    CHAOSRenameMap::RegClassSel
    CHAOSRenameMap::stringToRegClassSel(const std::string &s) {
        if (s == "floating_point") return RegClassSel::FloatingPoint;
        if (s == "vector") return RegClassSel::Vector;
        return RegClassSel::Integer;
    }

    void
    CHAOSRenameMap::scheduleAttackEvent(Cycles delay)
    {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void
    CHAOSRenameMap::attackCheck()
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
    CHAOSRenameMap::processFault(ThreadID tid)
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

        int arch_idx = target_arch_idx;
        if (arch_idx < 0 || arch_idx >= (int)reg_class->numRegs()) {
            // random arch reg within class
            arch_idx = std::uniform_int_distribution<int>(0, (int)reg_class->numRegs() - 1)(rng);
        }
        gem5::RegId arch_reg(*reg_class, arch_idx);
        const gem5::RegId flat = arch_reg.flatten(*isa);

        // Read current mapping.
        PhysRegIdPtr old_phys = cpu->frontRenameMap()[tid].lookup(flat);
        if (!old_phys) return;  // not mapped yet
        int old_phys_idx = old_phys->index();

        int new_phys_idx = old_phys_idx;
        uint64_t mask = 0;

        if (fi_mode == Mode::MapBitFlip) {
            // Flip a bit of the physRegIdx. Build the mask.
            mask = fault_mask;
            if (mask == 0) {
                // random one bit within a plausible physRegIdx width (<= 64 bits)
                std::uniform_int_distribution<int> bitDist(0, 7);
                mask = 1ULL << bitDist(rng);
            }
            new_phys_idx = old_phys_idx ^ (int)mask;
            // Legality check: new idx must be a valid physReg of this class.
            // PhysRegFile accessor gives the count; reject if out of range.
            size_t n_phys = 0;
            if (reg_target_class == RegClassSel::Integer)
                n_phys = cpu->physRegFile().numIntPhysRegs();
            else if (reg_target_class == RegClassSel::FloatingPoint)
                n_phys = cpu->physRegFile().numFloatPhysRegs();
            else
                n_phys = cpu->physRegFile().numVecPhysRegs();
            if (new_phys_idx < 0 || (size_t)new_phys_idx >= n_phys) {
                // Out of range — would SimulatorError. Reject (legality).
                stats->numLegalityRejects++;
                if (write_log) {
                    *(log_stream->stream())
                        << "Cycle: " << cpu->curCycle()
                        << " map_bitflip REJECT: old_phys=" << old_phys_idx
                        << " mask=0x" << std::hex << mask << std::dec
                        << " -> new_phys=" << new_phys_idx
                        << " out of range (n_phys=" << n_phys << ")\n";
                }
                return;
            }
            // Construct the new physRegId by index (PhysRegFile accessor).
            PhysRegIdPtr new_phys = nullptr;
            if (reg_target_class == RegClassSel::Integer)
                new_phys = cpu->physRegFile().intPhysRegId(new_phys_idx);
            else if (reg_target_class == RegClassSel::FloatingPoint)
                new_phys = cpu->physRegFile().floatPhysRegId(new_phys_idx);
            else
                new_phys = cpu->physRegFile().vecPhysRegId(new_phys_idx);
            if (!new_phys) { stats->numLegalityRejects++; return; }
            cpu->frontRenameMap()[tid].setEntry(flat, new_phys);
            stats->numMapBitFlips++;
        } else if (fi_mode == Mode::F5Substitute) {
            // method1 history residue: point this arch reg at ANOTHER currently-
            // allocated physReg (steal a donor's mapping). Enumerate other arch
            // regs of the same class, pick one whose lookup is non-null and
            // != old_phys.
            int donor_arch = -1;
            PhysRegIdPtr donor_phys = nullptr;
            int n_arch = reg_class->numRegs();
            // try up to n_arch random donors
            for (int tries = 0; tries < n_arch; ++tries) {
                int cand = std::uniform_int_distribution<int>(0, n_arch - 1)(rng);
                if (cand == arch_idx) continue;
                gem5::RegId cand_reg(*reg_class, cand);
                const gem5::RegId cand_flat = cand_reg.flatten(*isa);
                PhysRegIdPtr pp = cpu->frontRenameMap()[tid].lookup(cand_flat);
                if (pp && pp->index() != old_phys_idx) {
                    donor_arch = cand;
                    donor_phys = pp;
                    break;
                }
            }
            if (!donor_phys) {
                // No suitable donor — reject (legality, no residue possible now).
                stats->numLegalityRejects++;
                if (write_log) {
                    *(log_stream->stream())
                        << "Cycle: " << cpu->curCycle()
                        << " f5_substitute REJECT: no donor arch reg with a "
                        << "live mapping != self (arch=" << arch_idx << ")\n";
                }
                return;
            }
            new_phys_idx = donor_phys->index();
            // setEntry: point arch_reg at donor's physReg (double-occupancy =
            // method1 history residue — reads of arch_reg now return donor's value).
            cpu->frontRenameMap()[tid].setEntry(flat, donor_phys);
            stats->numF5Substitutes++;
            if (write_log) {
                *(log_stream->stream())
                    << "Cycle: " << cpu->curCycle()
                    << " f5_substitute: ArchReg[" << arch_idx << "] -> "
                    << "PhysReg[" << new_phys_idx << "] (stolen from donor arch "
                    << donor_arch << ", was PhysReg[" << old_phys_idx << "])\n";
            }
        } else if (fi_mode == Mode::F4FieldStuck) {
            // Persistently pin arch_reg to a wrong physReg. Arm a stuck mapping
            // that checkPermanent re-applies after subsequent rewrites.
            // For the initial application, substitute a donor (same as F5) then
            // record it as stuck.
            int n_arch = reg_class->numRegs();
            int donor_arch = -1;
            PhysRegIdPtr donor_phys = nullptr;
            for (int tries = 0; tries < n_arch; ++tries) {
                int cand = std::uniform_int_distribution<int>(0, n_arch - 1)(rng);
                if (cand == arch_idx) continue;
                gem5::RegId cand_reg(*reg_class, cand);
                const gem5::RegId cand_flat = cand_reg.flatten(*isa);
                PhysRegIdPtr pp = cpu->frontRenameMap()[tid].lookup(cand_flat);
                if (pp && pp->index() != old_phys_idx) {
                    donor_arch = cand;
                    donor_phys = pp;
                    break;
                }
            }
            if (!donor_phys) { stats->numLegalityRejects++; return; }
            new_phys_idx = donor_phys->index();
            cpu->frontRenameMap()[tid].setEntry(flat, donor_phys);
            stuck_mappings[{tid, arch_idx}] = {arch_idx, new_phys_idx};
            stats->numF4FieldStuck++;
            if (write_log) {
                *(log_stream->stream())
                    << "Cycle: " << cpu->curCycle()
                    << " f4_field_stuck: ArchReg[" << arch_idx << "] pinned to "
                    << "PhysReg[" << new_phys_idx << "] (donor arch " << donor_arch
                    << ", was " << old_phys_idx << ")\n";
            }
        }

        stats->numFaultsInjected++;
        ++faults_injected_count;
        writeLog(modeToString(fi_mode), tid, arch_idx, old_phys_idx,
                 new_phys_idx, mask);
    }

    void
    CHAOSRenameMap::checkPermanent()
    {
        // Re-apply f4_field_stuck mappings (survive subsequent rewrites — G2).
        gem5::BaseISA *isa = cpu->getContext(0) ? cpu->getContext(0)->getIsaPtr() : nullptr;
        if (!isa) {
            schedule(periodicCheck, cpu->clockEdge(cpu->curCycle() + Cycles(100000)));
            return;
        }
        const auto &reg_classes = isa->regClasses();
        gem5::RegClassType target_class = gem5::IntRegClass;
        if (reg_target_class == RegClassSel::FloatingPoint)
            target_class = gem5::FloatRegClass;
        else if (reg_target_class == RegClassSel::Vector)
            target_class = gem5::VecRegClass;
        const gem5::RegClass *reg_class = reg_classes[target_class];
        if (!reg_class) {
            schedule(periodicCheck, cpu->clockEdge(cpu->curCycle() + Cycles(100000)));
            return;
        }
        for (auto &kv : stuck_mappings) {
            ThreadID tid = kv.first.first;
            int arch_idx = kv.first.second;
            int stuck_phys_idx = kv.second.phys_idx;
            if ((size_t)arch_idx >= reg_class->numRegs()) continue;
            gem5::RegId arch_reg(*reg_class, arch_idx);
            const gem5::RegId flat = arch_reg.flatten(*isa);
            // Re-fetch the stuck physRegId by index (the map entry may have been
            // overwritten by a legitimate rename; re-pin it).
            PhysRegIdPtr stuck_phys = nullptr;
            if (reg_target_class == RegClassSel::Integer)
                stuck_phys = cpu->physRegFile().intPhysRegId(stuck_phys_idx);
            else if (reg_target_class == RegClassSel::FloatingPoint)
                stuck_phys = cpu->physRegFile().floatPhysRegId(stuck_phys_idx);
            else
                stuck_phys = cpu->physRegFile().vecPhysRegId(stuck_phys_idx);
            if (stuck_phys) {
                cpu->frontRenameMap()[tid].setEntry(flat, stuck_phys);
            }
        }
        schedule(periodicCheck, cpu->clockEdge(cpu->curCycle() + Cycles(100000)));
    }

    void
    CHAOSRenameMap::writeLog(const std::string &type, ThreadID tid,
                             int arch_idx, int old_phys, int new_phys,
                             uint64_t mask)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Thread: " << tid
            << ", Site: rat_front_rename_map"
            << ", Mode: " << type
            << ", ArchReg: " << arch_idx
            << ", old_phys: " << old_phys
            << ", new_phys: " << new_phys
            << ", Mask: 0x" << std::hex << mask << std::dec
            << (!semantic_role.empty() ? ", SemanticRole: " + semantic_role : "")
            << std::endl;
    }

    CHAOSRenameMap::CHAOSRenameMapStats::CHAOSRenameMapStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total RAT faults injected"),
          ADD_STAT(numMapBitFlips, statistics::units::Count::get(),
                   "map_bitflip faults (physRegIdx bit flip)"),
          ADD_STAT(numF5Substitutes, statistics::units::Count::get(),
                   "f5_substitute faults (method1 history residue)"),
          ADD_STAT(numF4FieldStuck, statistics::units::Count::get(),
                   "f4_field_stuck persistent mappings"),
          ADD_STAT(numLegalityRejects, statistics::units::Count::get(),
                   "injection attempts rejected by legality (free/invalid/out-of-range)")
    {}

} // namespace gem5
