#include "cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh"

#include <bitset>
#include <cmath>

#include "cpu/o3/cpu.hh"          // o3::CPU (full def)
#include "cpu/o3/regfile.hh"       // PhysRegFile, intPhysRegId etc.
#include "cpu/o3/free_list.hh"     // UnifiedFreeList::isFree
#include "cpu/reg_class.hh"       // RegId, IntRegClass
#include "arch/arm/regs/int.hh"   // ARM IntRegClass + numRegs
#include "debug/CHAOSRenameMap.hh"
#include "params/CHAOSRenameMap.hh"

namespace gem5
{

    CHAOSRenameMap::CHAOSRenameMap(const CHAOSRenameMapParams &p)
        : SimObject(p),
          cpu(p.cpu),
          fi_mode(stringToMode(p.mode)),
          target_arch_reg(p.targetArchReg),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          fault_mask(p.faultMask),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("rename_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSRenameMap: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
        // SELF-ATTACH happens in startup() (the rename map is constructed
        // before the CPU hierarchy is fully wired; dynamic_cast there).
    }

    CHAOSRenameMap::~CHAOSRenameMap() {}

    CHAOSRenameMap::Mode
    CHAOSRenameMap::stringToMode(const std::string &s) {
        if (s == "map_bitflip") return Mode::MapBitflip;
        if (s == "f5_substitute") return Mode::F5Substitute;
        if (s == "f4_field_stuck") return Mode::F4FieldStuck;
        return Mode::MapBitflip;
    }

    const char*
    CHAOSRenameMap::modeToString(CHAOSRenameMap::Mode m) {
        switch (m) {
            case Mode::MapBitflip: return "map_bitflip";
            case Mode::F5Substitute: return "f5_substitute";
            case Mode::F4FieldStuck: return "f4_field_stuck";
        }
        return "map_bitflip";
    }

    bool
    CHAOSRenameMap::inWindow() {
        // Use the CPU's actual clock period for the cycles->ticks conversion
        // (frequency-correct across configs: C0 2GHz=500t/cyc, C2-KP
        // 2.6GHz~385t/cyc). The old *1000 assumed 1GHz and silently never
        // opened the window on faster clocks. first/last_clock are CPU CYCLES.
        if (!cpu) return false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;
        Tick now = curTick();
        Tick period = o3cpu->clockPeriod();
        Tick f = first_clock * period;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * period) return false;
        return true;
    }

    int
    CHAOSRenameMap::pickAllocatedPhysReg(int class_value, int cur_idx,
                                         int num_phys, o3::CPU *o3cpu) {
        // Sample a candidate physReg of the same class that is NOT free
        // (= currently allocated = alive), validating via UnifiedFreeList::isFree.
        // K retries; return -1 if no valid candidate (honest: no injection).
        const int K = 16;
        for (int t = 0; t < K; t++) {
            int cand = (int)(rng() % (unsigned)num_phys);
            if (cand == cur_idx) continue;
            // build a PhysRegIdPtr for the candidate to query isFree
            PhysRegIdPtr cand_reg = nullptr;
            if (class_value == IntRegClass)
                cand_reg = o3cpu->physRegFile().intPhysRegId(cand);
            else if (class_value == FloatRegClass)
                cand_reg = o3cpu->physRegFile().floatPhysRegId(cand);
            else
                continue;  // only int/float for now
            if (!o3cpu->physFreeList().isFree((RegClassType)class_value, cand_reg)) {
                return cand;  // allocated = valid substitute target
            }
        }
        return -1;  // no valid candidate
    }

    bool
    CHAOSRenameMap::maybeCorrupt(ThreadID tid, const RegId &arch_reg,
                                  PhysRegIdPtr &phys_reg)
    {
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;

        // dynamic_cast to O3CPU once per call (physRegFile/physFreeList are
        // o3::CPU members, not BaseCPU). Cheap: maybeCorrupt fires at most once
        // per setEntry within the injection window.
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        // Only inject on the integer class (aarch64 X0-X30) — the method1
        // long-lived accumulator target. FP/vector RAT is structurally similar
        // but out of scope for this first patch (one class, single-thread SE).
        int class_value = arch_reg.classValue();
        if (class_value != IntRegClass) return false;

        int arch_idx = arch_reg.index();
        // aarch64 XZR (idx 31) and banked slots: skip (the CHAOSReg discipline).
        if (arch_idx > 30) return false;

        // target selection: directed or random within 0..30
        int target = target_arch_reg;
        if (target < 0) {
            target = (int)(rng() % 31);  // 0..30
        }
        if (arch_idx != target) return false;  // only inject on the chosen arch reg

        // probability gate
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        int cur_idx = phys_reg->index();
        int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();
        if (num_phys <= 1) return false;

        int new_idx = -1;

        if (fi_mode == Mode::MapBitflip) {
            // 1-bit remap: XOR a bit of the physReg index, realized as pointing
            // the entry at a DIFFERENT valid physReg (the method1 张冠李戴
            // semantics; §2.2 map_bitflip). Pick a random bit in
            // [0, ceil(log2(num_phys))) and XOR.
            int nbits = 0; int tmp = num_phys; while (tmp > 1) { nbits++; tmp >>= 1; }
            if (nbits < 1) nbits = 1;
            int bit = fault_mask ? (int)__builtin_ctzll(fault_mask) % nbits
                                 : (int)(rng() % (unsigned)nbits);
            new_idx = cur_idx ^ (1 << bit);
            if (new_idx < 0 || new_idx >= num_phys) {
                // bit flip landed out of range — clamp to a random valid idx
                new_idx = (int)(rng() % (unsigned)num_phys);
            }
            if (new_idx == cur_idx) return false;
        } else if (fi_mode == Mode::F5Substitute) {
            // §2.2 F5: point at another CURRENTLY-ALLOCATED physReg (not free).
            // The §2.2 guard: substitute target MUST be a legal physReg number
            // AND currently allocated, else skip (no UB). pickAllocatedPhysReg
            // validates via isFree; returns -1 if no candidate (honest no-op).
            new_idx = pickAllocatedPhysReg(class_value, cur_idx, num_phys, o3cpu);
            if (new_idx < 0) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rename_setEntry, mode=f5_substitute, "
                        << "arch_reg=int[" << arch_idx << "] cur_phys=" << cur_idx
                        << " — NO valid allocated substitute target (skipped, "
                        << "no UB). tid=" << (int)tid << std::endl;
                }
                return false;
            }
        } else if (fi_mode == Mode::F4FieldStuck) {
            // Pin ONE arch_reg's entry to a wrong physReg permanently. On the
            // first injection for this arch_reg, pick a wrong phys_idx; every
            // subsequent setEntry on it re-points to that wrong idx.
            if (!f4_armed || f4_arch_reg != arch_idx) {
                f4_arch_reg = arch_idx;
                f4_wrong_phys_idx = (int)(rng() % (unsigned)num_phys);
                if (f4_wrong_phys_idx == cur_idx)
                    f4_wrong_phys_idx = (cur_idx + 1) % num_phys;
                f4_armed = true;
            }
            new_idx = f4_wrong_phys_idx;
        }

        if (new_idx < 0 || new_idx == cur_idx) return false;
        if (new_idx >= num_phys) return false;

        // Apply: re-point the map entry at the new physReg. We mutate the
        // by-reference phys_reg so UnifiedRenameMap::setEntry stores the
        // corrupted mapping. (This is a LEGAL-domain remap — the entry points
        // at a real physReg object; no UB. §2.2 f5/mark_free legal-domain.)
        PhysRegIdPtr new_reg = o3cpu->physRegFile().intPhysRegId(new_idx);
        phys_reg = new_reg;
        faults_injected_count++;

        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: rename_setEntry, mode=" << modeToString(fi_mode)
                << ", tid=" << (int)tid
                << ", arch_reg=int[" << arch_idx << "]"
                << ", old_phys_idx=" << cur_idx
                << ", new_phys_idx=" << new_idx
                << ", FaultType: " << modeToString(fi_mode)
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    // CHAOSRenameMap needs the cpu pointer set after construction. Override
    // startup() to dynamic_cast and self-attach (the rename map is constructed
    // before the CPU SimObject hierarchy is fully wired, so do it at startup).
    void
    CHAOSRenameMap::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSRenameMap: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        // SELF-ATTACH: thread 0's frontRenameMap.chaosRenameMap = this.
        // PerThreadUnifiedRenameMap = std::array<UnifiedRenameMap, MaxThreads>.
        if (!o3cpu->frontRenameMap().empty()) {
            o3cpu->frontRenameMap()[0].setChaosRenameMap(this);
        }
    }

} // namespace gem5
