#include "cpu/o3/CHAOSFreeList/CHAOSFreeList.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/regfile.hh"       // PhysRegFile, intPhysRegId
#include "cpu/o3/free_list.hh"     // UnifiedFreeList, isFree, addReg
#include "cpu/reg_class.hh"       // IntRegClass
#include "debug/CHAOSFreeList.hh"
#include "params/CHAOSFreeList.hh"

namespace gem5
{

    CHAOSFreeList::CHAOSFreeList(const CHAOSFreeListParams &p)
        : SimObject(p),
          cpu(p.cpu),
          fi_mode(stringToMode(p.mode)),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("freelist_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSFreeList: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
    }

    CHAOSFreeList::~CHAOSFreeList() {}

    CHAOSFreeList::Mode
    CHAOSFreeList::stringToMode(const std::string &s) {
        if (s == "mark_free") return Mode::MarkFree;
        if (s == "pop_wrong") return Mode::PopWrong;
        return Mode::MarkFree;
    }

    const char*
    CHAOSFreeList::modeToString(CHAOSFreeList::Mode m) {
        switch (m) {
            case Mode::MarkFree: return "mark_free";
            case Mode::PopWrong: return "pop_wrong";
        }
        return "mark_free";
    }

    bool
    CHAOSFreeList::inWindow() {
        // Frequency-correct: use the CPU's actual clock period for the
        // cycles->ticks conversion (C0 2GHz=500t/cyc, C2-KP 2.6GHz~385t/cyc).
        // The old *1000 assumed 1GHz and never opened the window on C2.
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
    CHAOSFreeList::pickAllocatedPhysReg(int class_value, int num_phys,
                                        o3::CPU *o3cpu) {
        // §2.2 mark_free: pick a physReg of the class that is NOT free
        // (= allocated = alive), so re-adding it to the free list causes
        // history residue (two arch regs sharing one physReg). Validates via
        // UnifiedFreeList::isFree (the §2.2 guard).
        const int K = 16;
        for (int t = 0; t < K; t++) {
            int cand = (int)(rng() % (unsigned)num_phys);
            PhysRegIdPtr cand_reg = nullptr;
            if (class_value == IntRegClass)
                cand_reg = o3cpu->physRegFile().intPhysRegId(cand);
            else if (class_value == FloatRegClass)
                cand_reg = o3cpu->physRegFile().floatPhysRegId(cand);
            else
                continue;
            if (!o3cpu->physFreeList().isFree((RegClassType)class_value, cand_reg)) {
                return cand;  // allocated = valid mark_free target
            }
        }
        return -1;
    }

    bool
    CHAOSFreeList::maybeCorrupt(int class_value, PhysRegIdPtr &popped)
    {
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        // only int class for now (method1 long-lived accumulator target)
        if (class_value != IntRegClass) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();
        if (num_phys <= 1) return false;

        if (fi_mode == Mode::PopWrong) {
            // Return a different-but-LEGAL physReg id (same class, in range).
            // The caller (rename) stores it as the dest -> wrong mapping.
            int cur_idx = popped->index();
            int new_idx = (int)(rng() % (unsigned)num_phys);
            if (new_idx == cur_idx) new_idx = (cur_idx + 1) % num_phys;
            popped = o3cpu->physRegFile().intPhysRegId(new_idx);
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: freelist_getReg, mode=pop_wrong, class=int"
                    << ", true_front_idx=" << cur_idx
                    << ", returned_idx=" << new_idx
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        } else if (fi_mode == Mode::MarkFree) {
            // RE-ADD a currently-ALLOCATED physReg to the free list -> it gets
            // re-handed-out later while still held as a source by an in-flight
            // inst -> two arch regs share one physReg -> history residue
            // (method1 '其它计算数据覆盖 x[0]').
            int target = pickAllocatedPhysReg(class_value, num_phys, o3cpu);
            if (target < 0) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: freelist_getReg, mode=mark_free, class=int"
                        << " — NO valid allocated target (skipped, no UB)."
                        << std::endl;
                }
                return false;
            }
            PhysRegIdPtr target_reg = o3cpu->physRegFile().intPhysRegId(target);
            o3cpu->physFreeList().addReg(target_reg);  // re-add allocated
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: freelist_getReg, mode=mark_free, class=int"
                    << ", readded_allocated_idx=" << target
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }
        return false;
    }

    void
    CHAOSFreeList::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSFreeList: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        // SELF-ATTACH: set the UnifiedFreeList's chaosFreeList pointer.
        o3cpu->physFreeList().setChaosFreeList(this);
    }

} // namespace gem5
