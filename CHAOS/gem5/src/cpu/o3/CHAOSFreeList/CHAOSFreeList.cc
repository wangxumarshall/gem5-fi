#include "cpu/o3/CHAOSFreeList/CHAOSFreeList.hh"

#include <string>

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/regfile.hh"       // PhysRegFile, intPhysRegId
#include "cpu/o3/free_list.hh"     // UnifiedFreeList, isFree, addReg
#include "cpu/reg_class.hh"       // IntRegClass
#include "debug/CHAOSFreeList.hh"
#include "params/CHAOSFreeList.hh"
#include "sim/sim_exit.hh"        // registerExitCallback (W4 final D19/D22
                                   // end-of-run free-pool summary)

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
          write_log(p.writeLog),
          event_threshold(p.eventThreshold)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("freelist_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSFreeList: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            // W4 final D19/D22: end-of-run free-pool summary (final counts
            // evidence; the CHAOSPhysReg.cc:77 exit-callback pattern).
            registerExitCallback([this]() { this->finalSummary(); });
        }
    }

    CHAOSFreeList::~CHAOSFreeList() {}

    CHAOSFreeList::Mode
    CHAOSFreeList::stringToMode(const std::string &s) {
        if (s == "mark_free") return Mode::MarkFree;
        if (s == "pop_wrong") return Mode::PopWrong;
        if (s == "mark_free_event") return Mode::MarkFreeEvent;
        if (s == "drop_release") return Mode::DropRelease;
        if (s == "head_bitflip") return Mode::HeadBitflip;
        if (s == "head_bitflip2") return Mode::HeadBitflip2;
        if (s == "head_stuck") return Mode::HeadStuck;
        return Mode::MarkFree;
    }

    const char*
    CHAOSFreeList::modeToString(CHAOSFreeList::Mode m) {
        switch (m) {
            case Mode::MarkFree: return "mark_free";
            case Mode::PopWrong: return "pop_wrong";
            case Mode::MarkFreeEvent: return "mark_free_event";
            case Mode::DropRelease: return "drop_release";
            case Mode::HeadBitflip: return "head_bitflip";
            case Mode::HeadBitflip2: return "head_bitflip2";
            case Mode::HeadStuck: return "head_stuck";
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
        // W4 final D19/D22 have their OWN entry points (UnifiedFreeList::
        // addReg drop / SimpleFreeList::getReg stuck) — never touch this
        // post-pop path (early return BEFORE any gate/RNG use so their
        // determinism is unaffected).
        if (fi_mode == Mode::DropRelease || fi_mode == Mode::HeadStuck)
            return false;
        // W4.5 D17/D18 evidence watcher: after a mark_free(_event) injection
        // re-adds an ALLOCATED idx to the free list, watch for that idx
        // being popped again — the SECOND allocation = the duplicate the
        // model is designed to create ("两条指令共享同一物理寄存器").
        // Read-only, no fault counting; deliberately BEFORE the gates below
        // so it still fires after maxFaults is spent (the watch is only ever
        // set after a real injection, so log_stream exists). One observation
        // per injected duplicate.
        if (dup_watch_idx >= 0 && popped
            && class_value == IntRegClass
            && (int)popped->index() == dup_watch_idx) {
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: freelist_getReg, mode="
                    << modeToString(fi_mode) << ", class=int"
                    << ", DUPLICATE_ALLOCATION: idx " << dup_watch_idx
                    << " re-handed-out (second allocation; first holder "
                    << "still owns it)" << std::endl;
            }
            dup_watch_idx = -1;
        }
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
        } else if (fi_mode == Mode::HeadBitflip
                   || fi_mode == Mode::HeadBitflip2) {
            // W4 final D20 head_bitflip (ooo 04-design-matrix R21, 空闲表
            // 头/尾指针·单比特翻转) / D21 head_bitflip2 (R22, 双比特翻转,
            // F0) — HONEST APPROXIMATION (spike B conclusion: gem5
            // SimpleFreeList is a std::queue with NO explicit head/tail
            // pointer registers): the pop_wrong-style proxy where the
            // popped-front idx has 1 (D20) / 2 distinct random (D21) bits
            // flipped — the id HANDED OUT is what a corrupted head read
            // would have returned. The true front is still consumed (the
            // skipped entries leak), and the flipped-to id may be currently
            // ALLOCATED (immediate duplicate allocation) or still IN THE
            // FREE QUEUE (future duplicate) — the two D20 observables
            // ("重复分配 vs 分配到未初始化项" mixture). Out-of-range flip =
            // honest skip, never clamped (the map_bitflip2 policy).
            int cur_idx = popped->index();
            int nbits = 0; int tmp = num_phys;
            while (tmp > 1) { nbits++; tmp >>= 1; }
            int need = (fi_mode == Mode::HeadBitflip) ? 1 : 2;
            if (nbits < need) return false;
            int b1 = (int)(rng() % (unsigned)nbits);
            int b2 = -1;
            if (need == 2) {
                b2 = (int)(rng() % (unsigned)(nbits - 1));
                if (b2 >= b1) b2++;
                if (b1 == b2 || b2 >= nbits) return false;
            }
            int flipped = cur_idx ^ (1 << b1) ^ (need == 2 ? (1 << b2) : 0);
            if (flipped < 0 || flipped >= num_phys) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: freelist_getReg, mode="
                        << modeToString(fi_mode) << ", class=int"
                        << ", true_front_idx=" << cur_idx
                        << ", bits=(" << b1;
                    if (need == 2)
                        *(log_stream->stream()) << "," << b2;
                    *(log_stream->stream())
                        << ") — flipped idx " << flipped << " out of [0,"
                        << num_phys << ") (skipped, no clamp)" << std::endl;
                }
                return false;
            }
            PhysRegIdPtr flipped_reg =
                o3cpu->physRegFile().intPhysRegId(flipped);
            // post-pop liveness of the flipped-to target: isFree scans the
            // queue (the contains() helper) — false = allocated elsewhere.
            bool target_in_queue = o3cpu->physFreeList().isFree(
                IntRegClass, flipped_reg);
            popped = flipped_reg;
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: freelist_getReg, mode="
                    << modeToString(fi_mode) << ", class=int"
                    << ", true_front_idx=" << cur_idx
                    << " (popped-and-consumed: entries below the corrupted "
                    "head read leak)"
                    << ", returned_idx=" << flipped
                    << ", bits=(" << b1;
                if (need == 2)
                    *(log_stream->stream()) << "," << b2;
                *(log_stream->stream())
                    << ")"
                    << ", target_status="
                    << (target_in_queue
                            ? "in_free_queue(future duplicate hand-out)"
                            : "allocated(immediate duplicate allocation)")
                    << ", approx=head_ptr_bitflip_on_queue_front (std::queue "
                       "has no explicit pointer — 近似口径)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        } else if (fi_mode == Mode::MarkFree || fi_mode == Mode::MarkFreeEvent) {
            // D17 (04-design-matrix R18, 固定间隔) = MarkFree: re-add a
            // currently-ALLOCATED physReg to the free list -> it gets
            // re-handed-out later while still held -> two arch regs share
            // one physReg -> WAW / history residue. D18 (R19, 事件触发) =
            // MarkFreeEvent: the SAME action, eligible only when the INT
            // free-list remaining count is at/below event_threshold
            // (checked POST-POP — this hook fires after the pop, so the
            // count is the "空闲表剩余" at the getReg moment).
            unsigned nfree = 0;
            if (fi_mode == Mode::MarkFreeEvent) {
                nfree = o3cpu->physFreeList().numFreeRegs(IntRegClass);
                if ((uint64_t)nfree > event_threshold) return false;
            }
            int target = pickAllocatedPhysReg(class_value, num_phys, o3cpu);
            if (target < 0) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: freelist_getReg, mode="
                        << modeToString(fi_mode) << ", class=int"
                        << " — NO valid allocated target (skipped, no UB)."
                        << std::endl;
                }
                return false;
            }
            PhysRegIdPtr target_reg = o3cpu->physRegFile().intPhysRegId(target);
            o3cpu->physFreeList().addReg(target_reg);  // re-add allocated
            dup_watch_idx = target;  // W4.5: watch for the second allocation
            faults_injected_count++;
            if (write_log) {
                if (fi_mode == Mode::MarkFreeEvent) {
                    // D18 evidence line: the trigger-time remaining count
                    // (must be <= threshold) + the re-added idx.
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: freelist_getReg, mode=mark_free_event"
                        << ", class=int"
                        << ", num_free_int_after_pop=" << nfree
                        << " (threshold=" << event_threshold << ")"
                        << ", popped_idx=" << popped->index()
                        << ", readded_allocated_idx=" << target
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                } else {
                    // D17: legacy mark_free line format kept byte-identical.
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: freelist_getReg, mode=mark_free, class=int"
                        << ", readded_allocated_idx=" << target
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
            }
            return true;
        }
        return false;
    }

    bool
    CHAOSFreeList::maybeDropRelease(int class_value, PhysRegIdPtr freed_reg)
    {
        // W4 final D19 (ooo 04-design-matrix R20, 空闲表·丢失释放, F1
        // "一次性触发持续影响"): a release event that should have happened
        // does not — the physReg is NOT pushed back onto the free list. One
        // suppression is a permanent leak: the int pool shrinks by one for
        // the rest of the run. The hook site (UnifiedFreeList::addReg)
        // covers BOTH runtime release paths — rename.cc removeFromHistory
        // (commit-time old-mapping release) and the freeingInProgress drain
        // (post-squash wrong-path release); the construction-time init path
        // is safe because chaosFreeList is still nullptr while
        // PhysRegFile::initFreeList runs (the injector self-attaches at
        // startup()).
        if (fi_mode != Mode::DropRelease) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;
        if (!inWindow()) return false;
        if (class_value != IntRegClass) return false;  // int pool only

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        unsigned before = o3cpu->physFreeList().numFreeRegs(IntRegClass);
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: freelist_addReg, mode=drop_release, class=int"
                << ", suppressed_release_idx=" << freed_reg->index()
                << ", num_free_int_at_drop=" << before
                << " (release suppressed — queue stays at " << before
                << "; a normal release would make it " << (before + 1)
                << "; the pool is permanently -1 for the rest of the run)"
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;  // caller MUST skip the push
    }

    bool
    CHAOSFreeList::maybeStuckHead(int class_value, PhysRegIdPtr &front_reg)
    {
        // W4 final D22 (ooo 04-design-matrix R23, 空闲表头/尾指针·卡死,
        // F5) — HONEST APPROXIMATION (spike B: gem5 SimpleFreeList is a
        // std::queue with NO explicit head/tail pointer registers): the
        // pre-approved "反复返回同项不真正 pop（头卡死）" proxy. Arming
        // (the fault's creation, the ONLY faults_injected_count increment)
        // at the first in-window eligible getReg: the stuck id = the
        // then-front idx with ONE random bit forced to a random polarity
        // (the 04-matrix "选指针寄存器的一个比特位置，永久固定为 0/1"
        // flavor); if forcing leaves the valid range the RAW front idx is
        // frozen instead (logged). From then on EVERY getReg returns that
        // SAME id and the queue NEVER advances — a permanent fixed-pattern
        // deviation (持续重复分配; the true queue entries are unreachable).
        if (fi_mode != Mode::HeadStuck) return false;
        if (class_value != IntRegClass) return false;  // int pool only
        if (!cpu || probability <= 0.0f) return false;

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        if (!hs_armed) {
            // F5 arming: max_faults/probability/window gate the CREATION
            // only (the f5_rat_stuck arming pattern); applications after
            // arming are exposures of the ONE permanent fault.
            if (max_faults != 0 && faults_injected_count >= max_faults)
                return false;
            if (!inWindow()) return false;
            std::uniform_real_distribution<float> pd(0.0f, 1.0f);
            if (pd(rng) > probability) return false;

            int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();
            int front_idx = front_reg->index();
            int nbits = 0; int tmp = num_phys;
            while (tmp > 1) { nbits++; tmp >>= 1; }
            if (nbits < 1) nbits = 1;
            hs_bit = (int)(rng() % (unsigned)nbits);
            hs_polarity = (int)(rng() % 2);
            int stuck = hs_polarity ? (front_idx | (1 << hs_bit))
                                    : (front_idx & ~(1 << hs_bit));
            if (stuck < 0 || stuck >= num_phys) {
                // forcing the bit leaves the valid index range — freeze the
                // RAW front instead (the head stuck before any deviation);
                // logged honestly.
                stuck = front_idx;
                hs_bit = -1;
            }
            hs_stuck_idx = stuck;
            hs_armed = true;
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: freelist_getReg, mode=head_stuck, ARMED"
                    << ", class=int"
                    << ", frozen_front_idx=" << front_idx
                    << ", stuck_idx=" << hs_stuck_idx;
                if (hs_bit >= 0) {
                    *(log_stream->stream()) << ", forced_bit=" << hs_bit
                        << ", polarity=" << hs_polarity
                        << (hs_polarity ? " (stuck_at_one)" :
                                          " (stuck_at_zero)");
                } else {
                    *(log_stream->stream())
                        << " (bit force out of range — raw freeze)";
                }
                *(log_stream->stream())
                    << ", approx=head_ptr_stuck_no_pop (std::queue has no "
                       "explicit pointer — 近似口径)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            // fall through: THIS getReg is the first exposure
        }

        // Application (F5: NOT re-gated by max_faults/probability): hand
        // out the stuck id WITHOUT popping. Exposure logging is capped at
        // the first 10 (the fixed-pattern evidence); the total count lands
        // in the exit summary.
        hs_exposures++;
        int true_front = front_reg->index();
        front_reg = o3cpu->physRegFile().intPhysRegId(hs_stuck_idx);
        if (write_log && hs_exposures <= 10) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: freelist_getReg, mode=head_stuck, class=int"
                << ", true_front_idx=" << true_front
                << ", returned_idx=" << hs_stuck_idx
                << " (same item every time — head never advances, no pop)"
                << ", deviation=" << (hs_stuck_idx - true_front)
                << ", exposure: " << hs_exposures
                << (hs_exposures == 10 ? " (logging capped; total in exit "
                   "summary)" : "")
                << std::endl;
        }
        return true;  // caller MUST NOT pop
    }

    void
    CHAOSFreeList::finalSummary()
    {
        // W4 final D19/D22 end-of-run evidence: final free-pool sizes (the
        // D19 permanent -1 shrink is provable by comparing an injected run
        // against a zero-injection control with the same seed and an
        // unreachable window) + the D22 total exposure count.
        if (!write_log || !log_stream || !cpu) return;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return;
        *(log_stream->stream()) << "Tick: " << curTick()
            << ", Site: exit_summary, mode=" << modeToString(fi_mode)
            << ", faults_injected: " << faults_injected_count
            << ", final_free_int="
            << o3cpu->physFreeList().numFreeRegs(IntRegClass)
            << ", final_free_float="
            << o3cpu->physFreeList().numFreeRegs(FloatRegClass)
            << ", head_stuck_exposures=" << hs_exposures
            << std::endl;
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
