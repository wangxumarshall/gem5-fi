#include "cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh"

#include <bitset>
#include <cmath>

#include "cpu/o3/cpu.hh"          // o3::CPU (full def)
#include "cpu/o3/regfile.hh"       // PhysRegFile, intPhysRegId etc.
#include "cpu/o3/free_list.hh"     // UnifiedFreeList::isFree
#include "cpu/o3/rob.hh"           // o3::ROB::getEntryAtDistance (D13 walk)
#include "cpu/o3/dyn_inst.hh"      // o3::DynInst: numDestRegs/renamedDestIdx/seqNum
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
            // spec_leak sampling-bias fix: skip a geometric(0.1) number of
            // eligible squash-rollbacks before the first suppressed one.
            std::geometric_distribution<uint64_t> skip_dist(0.1);
            events_to_skip = skip_dist(rng);
        }
        // SELF-ATTACH happens in startup() (the rename map is constructed
        // before the CPU hierarchy is fully wired; dynamic_cast there).
    }

    CHAOSRenameMap::~CHAOSRenameMap() {}

    CHAOSRenameMap::Mode
    CHAOSRenameMap::stringToMode(const std::string &s) {
        if (s == "map_bitflip") return Mode::MapBitflip;
        if (s == "map_bitflip2") return Mode::MapBitflip2;
        if (s == "swap_to_active") return Mode::SwapToActive;
        if (s == "f5_substitute") return Mode::F5Substitute;
        if (s == "f4_field_stuck") return Mode::F4FieldStuck;
        if (s == "spec_leak") return Mode::SpecLeak;
        if (s == "f5_rat_stuck") return Mode::F5RatStuck;
        if (s == "stale_read") return Mode::StaleRead;
        if (s == "swap_mispred_event") return Mode::SwapMispredEvent;
        if (s == "hb_bitflip") return Mode::HbBitflip;
        if (s == "hb_bitflip2") return Mode::HbBitflip2;
        // W5.6 (ooo 04-design-matrix D36-D39, Int Dispatch/ROB
        // old-physical-register field) — mounted via --rob_mode, routed
        // by ooo_proxy to THIS injector (gem5's old-phys lives in the
        // rename historyBuffer checkpoint, the W4 N1 finding).
        if (s == "oldphys_bitflip") return Mode::OldphysBitflip;
        if (s == "oldphys_bitflip2") return Mode::OldphysBitflip2;
        if (s == "oldphys_swap_active") return Mode::OldphysSwapActive;
        if (s == "oldphys_stuck") return Mode::OldphysStuck;
        return Mode::MapBitflip;
    }

    const char*
    CHAOSRenameMap::modeToString(CHAOSRenameMap::Mode m) {
        switch (m) {
            case Mode::MapBitflip: return "map_bitflip";
            case Mode::MapBitflip2: return "map_bitflip2";
            case Mode::SwapToActive: return "swap_to_active";
            case Mode::F5Substitute: return "f5_substitute";
            case Mode::F4FieldStuck: return "f4_field_stuck";
            case Mode::SpecLeak: return "spec_leak";
            case Mode::F5RatStuck: return "f5_rat_stuck";
            case Mode::StaleRead: return "stale_read";
            case Mode::SwapMispredEvent: return "swap_mispred_event";
            case Mode::HbBitflip: return "hb_bitflip";
            case Mode::HbBitflip2: return "hb_bitflip2";
            case Mode::OldphysBitflip: return "oldphys_bitflip";
            case Mode::OldphysBitflip2: return "oldphys_bitflip2";
            case Mode::OldphysSwapActive: return "oldphys_swap_active";
            case Mode::OldphysStuck: return "oldphys_stuck";
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

    int
    CHAOSRenameMap::collectRobActiveDests(int cur_idx, o3::CPU *o3cpu,
                                          ThreadID tid,
                                          std::vector<RobCand> &cands) {
        // W4.2a D13 (04-design-matrix R14): the swap pool = dest physRegs of
        // instructions currently in flight (ROB-resident). Each such physReg
        // is by construction allocated and in use (it was grabbed from the
        // freelist at rename and is only freed after its owner commits AND
        // the next definer of that arch reg retires) — a mapping swap onto
        // it is LEGAL-domain and by design bypasses the "random flip landed
        // on a free/dead reg" luck of D12. Walk head->tail via
        // getEntryAtDistance (the CHAOSROB.cc pattern; ROB=128 so the
        // O(n^2) re-walk is bounded and only runs on injection attempts
        // that passed every gate). Read-only — safe from Rename::doSquash
        // (rename stage; the ROB list is not mutated re-entrantly).
        cands.clear();
        o3::ROB &rob = o3cpu->o3ROB();
        for (int d = 0; ; d++) {
            o3::DynInstPtr inst = rob.getEntryAtDistance(tid, d);
            if (!inst) break;  // past tail / empty
            for (int i = 0; i < (int)inst->numDestRegs(); i++) {
                PhysRegIdPtr dest = inst->renamedDestIdx(i);
                if (!dest) continue;
                if (dest->classValue() != IntRegClass) continue;
                int pidx = dest->index();
                if (pidx == cur_idx) continue;  // must differ from current
                cands.push_back({pidx, d, inst->seqNum});
            }
        }
        return (int)cands.size();
    }

    bool
    CHAOSRenameMap::maybeCorrupt(ThreadID tid, const RegId &arch_reg,
                                  PhysRegIdPtr &phys_reg)
    {
        // W4.3 D15 f5_rat_stuck: permanent write-path mask. Dispatch BEFORE
        // the generic gates below: once armed, applications are exposures of
        // the ONE permanent fault — max_faults/probability must NOT gate
        // them (F5 = permanent from existence; the gates live only in the
        // arming path inside maybeStuckWrite). This call site covers the
        // squash-rollback restore writes (UnifiedRenameMap::setEntry); the
        // normal rename writes go through maybeFaultRename below.
        if (fi_mode == Mode::F5RatStuck)
            return maybeStuckWrite(tid, arch_reg, phys_reg,
                                   "setEntry_restore");
        // W4 final D14 swap_mispred_event (ooo 04-design-matrix R15,
        // RAT映射字段·换值·误预测事件触发): the swap model of D13
        // swap_to_active, but eligible ONLY while a BRANCH-MISPREDICTION
        // squash-restore is in flight (the context is armed by
        // notifySquashSignal around Rename::squash — the doSquash restore
        // setEntry calls land inside it; traps / order violations /
        // squashAfter carry mispredictInst==NULL and never arm it). Outside
        // that window this mode is a strict no-op.
        if (fi_mode == Mode::SwapMispredEvent && !(sq_active && sq_mispredict))
            return false;
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
        // W4.1 D12 map_bitflip2: the two flipped index bits (for the log
        // line's bits=(b1,b2) — the hamming-distance-2 evidence).
        int log_b1 = -1, log_b2 = -1;
        // W4.2a D13 swap_to_active: chosen candidate + the full ROB-active
        // pool (for the log line's "(active, rob_dist=D)" evidence).
        int log_rob_dist = -1;
        uint64_t log_chosen_sn = 0;
        std::vector<RobCand> rob_cands;

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
        } else if (fi_mode == Mode::MapBitflip2) {
            // W4.1 D12 (04-design-matrix R13): flip TWO distinct random bits
            // of the physReg index at the same site as map_bitflip. On the
            // C3 north-star config (128 int physRegs = 2^7) the 7-bit index
            // field is fully covered: any 2-bit flip stays in [0,128) and
            // always changes the value (b1 != b2 => XOR != 0), so the
            // hamming distance between old and new phys idx is EXACTLY 2.
            // On a non-power-of-2 num_phys the flip can land out of range —
            // honest skip with log (NO clamp: a clamped remap would not be
            // the 2-bit-flip fault model).
            int nbits = 0; int tmp = num_phys; while (tmp > 1) { nbits++; tmp >>= 1; }
            if (nbits < 2) return false;  // index field too small for 2 bits
            int b1 = 0, b2 = 0;
            if (__builtin_popcountll(fault_mask) >= 2) {
                // directed control: the two lowest set bits of fault_mask
                b1 = __builtin_ctzll(fault_mask);
                uint64_t rest = fault_mask & ~(1ULL << b1);
                b2 = __builtin_ctzll(rest);
            } else {
                // uniform random DISTINCT pair: b1 uniform, b2 uniform over
                // the remaining nbits-1 slots (order-statistics trick)
                b1 = (int)(rng() % (unsigned)nbits);
                b2 = (int)(rng() % (unsigned)(nbits - 1));
                if (b2 >= b1) b2++;
            }
            if (b1 == b2 || b1 >= nbits || b2 >= nbits) return false;
            int flipped = cur_idx ^ (1 << b1) ^ (1 << b2);
            if (flipped < 0 || flipped >= num_phys) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rename_setEntry, mode=map_bitflip2, "
                        << "tid=" << (int)tid
                        << ", arch=X" << arch_idx << ", old_phys=" << cur_idx
                        << ", bits=(" << b1 << "," << b2 << ")"
                        << " — flipped idx " << flipped << " out of [0,"
                        << num_phys << ") (skipped, no clamp)"
                        << std::endl;
                }
                return false;
            }
            new_idx = flipped;
            log_b1 = b1; log_b2 = b2;
        } else if (fi_mode == Mode::SwapToActive || fi_mode == Mode::SwapMispredEvent) {
            // W4.2a D13 (04-design-matrix R14, 换值·固定间隔) / W4 final
            // D14 (R15, 误预测事件触发): force the arch reg's mapping to
            // the dest physReg of ANOTHER in-flight instruction — "从 ROB
            // 里随机挑一个活跃物理寄存器号写入". The new mapping is legal
            // (allocated + in use), so it is designed to bypass the
            // dependency-check luck D12 relies on. ROB empty / no candidate
            // != cur -> honest skip, logged.
            int n = collectRobActiveDests(cur_idx, o3cpu, tid, rob_cands);
            if (n == 0) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rename_setEntry, mode="
                        << modeToString(fi_mode) << ", "
                        << "tid=" << (int)tid
                        << ", arch=X" << arch_idx << ", old_phys=" << cur_idx
                        << " — ROB has no active int dest candidate != cur "
                        << "(skipped, no injection)" << std::endl;
                }
                return false;
            }
            int pick = (int)(rng() % (unsigned)n);
            new_idx = rob_cands[pick].phys_idx;
            log_rob_dist = rob_cands[pick].dist;
            log_chosen_sn = rob_cands[pick].sn;
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
            if (fi_mode == Mode::MapBitflip2) {
                // W4.1 D12 plan-mandated evidence line: old/new phys idx +
                // the two flipped bits (verifiable: popcount(old^new)==2 and
                // old ^ (1<<b1) ^ (1<<b2) == new).
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rename_setEntry, mode=map_bitflip2"
                    << ", tid=" << (int)tid
                    << ", arch=X" << arch_idx
                    << ", old_phys=" << cur_idx
                    << ", new_phys=" << new_idx
                    << ", bits=(" << log_b1 << "," << log_b2 << ")"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            } else if (fi_mode == Mode::SwapToActive
                       || fi_mode == Mode::SwapMispredEvent) {
                // W4.2a D13 / W4 final D14 plan-mandated evidence line: the
                // swap + "(active, rob_dist=D)" + the FULL ROB-active dest
                // pool so "new_phys ∈ ROB active set" is verifiable from the
                // log alone (pool printed as phys@dist in ROB head->tail
                // order). D14 additionally carries the misprediction-restore
                // context (squash cause + the mispredicted branch's seqNum)
                // — the "触发时刻=误预测恢复瞬间" evidence. The Site label
                // stays "rename_setEntry" for D13 (byte-identical to the
                // batch-1 log format); D14 tags the restore site.
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: "
                    << (fi_mode == Mode::SwapMispredEvent
                            ? "rename_setEntry_restore" : "rename_setEntry")
                    << ", mode=" << modeToString(fi_mode)
                    << ", tid=" << (int)tid
                    << ", arch=X" << arch_idx
                    << ", old_phys=" << cur_idx
                    << ", new_phys=" << new_idx << "(active, rob_dist="
                    << log_rob_dist << ")"
                    << ", chosen_sn=" << log_chosen_sn;
                if (fi_mode == Mode::SwapMispredEvent) {
                    *(log_stream->stream())
                        << ", trigger=branch_misprediction_restore"
                        << ", mispred_squash_sn=" << sq_sn;
                }
                *(log_stream->stream()) << ", rob_active_dests=[";
                for (size_t i = 0; i < rob_cands.size(); i++) {
                    if (i) *(log_stream->stream()) << " ";
                    *(log_stream->stream()) << rob_cands[i].phys_idx
                        << "@" << rob_cands[i].dist;
                }
                *(log_stream->stream()) << "]"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            } else {
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
        }
        return true;
    }

    // CHAOSRenameMap needs the cpu pointer set after construction. Override
    bool
    CHAOSRenameMap::maybeSuppressRollback(ThreadID tid, const RegId &arch_reg,
                                          PhysRegIdPtr new_phys,
                                          PhysRegIdPtr prev_phys)
    {
        // §2.3 spec_leak: suppress ONE history-buffer rollback during squash.
        // Only active in SpecLeak mode (other modes never touch this path —
        // zero regression for all existing campaigns).
        if (fi_mode != Mode::SpecLeak) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (new_phys == prev_phys) return false;  // non-renamed (misc/XZR): skip

        // int class only (same discipline as maybeCorrupt)
        if (arch_reg.classValue() != IntRegClass) return false;
        int arch_idx = arch_reg.index();
        if (arch_idx > 30) return false;  // XZR / banked

        // directed target or random within 0..30
        int target = target_arch_reg;
        if (target < 0) target = (int)(rng() % 31);
        if (arch_idx != target) return false;

        // sampling-bias fix (Phase 3.0 family): skip a geometric(0.1) number
        // of ELIGIBLE rollbacks so maxFaults=1 lands on a seed-dependent event
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (events_to_skip > 0) { --events_to_skip; return false; }
        if (pd(rng) > probability) return false;

        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: rename_doSquash, mode=spec_leak, tid=" << (int)tid
                << ", arch_reg=X" << arch_idx
                << ", kept_new_phys_idx=" << (new_phys ? new_phys->index() : -1)
                << ", suppressed_prev_phys_idx=" << (prev_phys ? prev_phys->index() : -1)
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    bool
    CHAOSRenameMap::maybeStuckWrite(ThreadID tid, const RegId &arch_reg,
                                    PhysRegIdPtr &phys_reg, const char *site)
    {
        // W4.3 D15 (04-design-matrix R16, RAT映射字段·卡死, F5): a stuck-at
        // cell in ONE FRONT-map RAT entry — every write to the entry stores
        // the value with ONE physReg-index bit forced to a fixed polarity.
        // Arming (the fault's creation, the ONLY faults_injected_count
        // increment) happens at the first in-window eligible write event;
        // applications after that are passive and ungated by max_faults /
        // probability (F5 = permanent from existence). Scope note: the fault
        // lives in the rename-stage (front) RAT — the commitRenameMap copy
        // has no injector attached and is never masked.
        if (!cpu || probability <= 0.0f) return false;
        if (arch_reg.classValue() != IntRegClass) return false;
        int arch_idx = arch_reg.index();
        if (arch_idx > 30) return false;  // XZR / banked slots

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;
        int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();

        if (!f5s_armed) {
            // Arming: D15 "运行开始（首个注入窗口到达时）随机选一个 RAT
            // 表项的一个比特位" — one entry, one bit, polarity 50/50
            // (directed targetArchReg overrides the entry choice).
            if (max_faults != 0 && faults_injected_count >= max_faults)
                return false;
            if (!inWindow()) return false;
            std::uniform_real_distribution<float> pd(0.0f, 1.0f);
            if (pd(rng) > probability) return false;

            int target = target_arch_reg;
            if (target < 0) target = (int)(rng() % 31);  // 0..30
            int nbits = 0; int tmp = num_phys;
            while (tmp > 1) { nbits++; tmp >>= 1; }
            if (nbits < 1) nbits = 1;
            f5s_arch_reg = target;
            f5s_bit = (int)(rng() % (unsigned)nbits);
            f5s_polarity = (int)(rng() % 2);
            f5s_armed = true;
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: " << site << ", mode=f5_rat_stuck, ARMED"
                    << ", tid=" << (int)tid
                    << ", arch=X" << f5s_arch_reg
                    << ", bit=" << f5s_bit
                    << ", polarity=" << f5s_polarity
                    << (f5s_polarity ? " (stuck_at_one)" : " (stuck_at_zero)")
                    << ", num_phys=" << num_phys
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            // fall through: if THIS write targets the armed entry, mask it now
        }
        if (f5s_arch_reg != arch_idx) return false;

        // Apply the write-path mask (the G2 regfile.hh:360 pattern): force
        // the bit on the value being written to the entry.
        int written = phys_reg->index();
        int masked = f5s_polarity ? (written | (1 << f5s_bit))
                                  : (written & ~(1 << f5s_bit));
        f5s_exposures++;
        if (masked == written) {
            // The written value already carries the forced polarity — a
            // stuck cell does not change it. Log the exposure (persistence
            // evidence); phys_reg unchanged, caller stores it (no-op).
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: " << site << ", mode=f5_rat_stuck"
                    << ", tid=" << (int)tid
                    << ", arch=X" << arch_idx
                    << ", write_phys=" << written
                    << ", stored_phys=" << masked
                    << " (bit " << f5s_bit << " already at " << f5s_polarity
                    << ", no observable change)"
                    << ", exposure: " << f5s_exposures
                    << std::endl;
            }
            return true;
        }
        if (masked < 0 || masked >= num_phys) {
            // Non-power-of-2 numPhys: forcing the bit can leave the valid
            // index range. Honest skip, no clamp (a clamped value would not
            // be the stuck-at fault); THIS write stores unmasked.
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: " << site << ", mode=f5_rat_stuck"
                    << ", tid=" << (int)tid
                    << ", arch=X" << arch_idx
                    << ", write_phys=" << written
                    << " — forced idx " << masked << " out of [0,"
                    << num_phys << ") (skipped this write, no clamp)"
                    << ", exposure: " << f5s_exposures
                    << std::endl;
            }
            return false;
        }
        phys_reg = o3cpu->physRegFile().intPhysRegId(masked);
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: " << site << ", mode=f5_rat_stuck"
                << ", tid=" << (int)tid
                << ", arch=X" << arch_idx
                << ", write_phys=" << written
                << ", stored_phys=" << masked
                << ", bit=" << f5s_bit << " forced to " << f5s_polarity
                << ", exposure: " << f5s_exposures
                << std::endl;
        }
        return true;
    }

    bool
    CHAOSRenameMap::maybeFaultRename(ThreadID tid, const RegId &arch_reg,
                                     PhysRegIdPtr prev_phys,
                                     PhysRegIdPtr &entry_phys)
    {
        // W4.3 D15: the NORMAL rename write (SimpleRenameMap::rename,
        // rename_map.cc — "map[idx] = renamed_reg") bypasses setEntry, so the
        // pre-existing setEntry pre-store hook cannot mask it. This post-
        // write hook re-masks the entry: maybeStuckWrite mutates entry_phys
        // to the masked value and the caller re-stores it. Every other mode
        // returns false here (zero regression on the rename path).
        if (fi_mode == Mode::F5RatStuck)
            return maybeStuckWrite(tid, arch_reg, entry_phys, "rename_write");

        if (fi_mode == Mode::StaleRead) {
            // W4.4 D16 (04-design-matrix R17, RAT映射字段·读到旧数据,
            // event = 该表项即将被下一次重命名写入覆盖的瞬间): make THAT
            // ONE rename write silently fail — the entry keeps the previous
            // occupant's still-legal mapping until the next rename updates
            // it normally. NOT a value swap (D13 swap_to_active) and NOT a
            // stuck bit (D15 f5_rat_stuck): "本该发生的更新没有真正发生".
            // The renaming instruction KEEPS its freshly allocated physReg as
            // dest (the getReg pop already happened inside
            // SimpleRenameMap::rename and its freelist accounting stands);
            // only the stored entry is rolled back, so downstream readers of
            // this arch reg read the OLD phys -> stale but legal data (the
            // model's "读到旧数据"). Fires on the RENAME write path ONLY —
            // the squash-restore setEntry path is not a rename overwrite and
            // maybeCorrupt has no StaleRead dispatch (falls through to
            // return false there).
            if (!cpu || probability <= 0.0f) return false;
            if (max_faults != 0 && faults_injected_count >= max_faults)
                return false;
            if (!inWindow()) return false;
            if (arch_reg.classValue() != IntRegClass) return false;
            int arch_idx = arch_reg.index();
            if (arch_idx > 30) return false;  // XZR / banked

            int target = target_arch_reg;
            if (target < 0) target = (int)(rng() % 31);  // 0..30
            if (arch_idx != target) return false;

            std::uniform_real_distribution<float> pd(0.0f, 1.0f);
            if (pd(rng) > probability) return false;

            int attempted = entry_phys->index();
            int kept = prev_phys->index();
            // The write silently fails once: the entry keeps the old mapping.
            entry_phys = prev_phys;
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rename_write, mode=stale_read"
                    << ", tid=" << (int)tid
                    << ", arch=X" << arch_idx
                    << ", attempted_phys=" << attempted
                    << " (write silently failed, not stored)"
                    << ", kept_phys=" << kept
                    << " (previous mapping retained)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }
        return false;
    }

    void
    CHAOSRenameMap::notifySquashSignal(bool mispredict, ThreadID tid,
                                       InstSeqNum sn)
    {
        // W4 final D14: context arm — called by Rename::checkSignalsAndUpdate
        // immediately BEFORE squash() (which runs doSquash, and therefore all
        // the restore setEntry writes, to completion before returning).
        // mispredict == commitInfo.mispredictInst != NULL (commit.cc:840 is
        // the ONLY setter for the mispredict path; squashAll/trap/order-
        // violation paths leave it NULL) — so sq_mispredict==true means
        // "this restore window was caused by a branch misprediction".
        // Signal logging is bounded: only while the D14 fault is still
        // unspent (maxFaults gate), so a maxFaults=1 directed run logs at
        // most the squashes that precede the first injection.
        sq_active = true;
        sq_mispredict = mispredict;
        sq_sn = sn;
        if (fi_mode == Mode::SwapMispredEvent && write_log && log_stream
            && !(max_faults != 0 && faults_injected_count >= max_faults)
            && cpu && probability > 0.0f) {
            ++sq_signals_logged;
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: rename_squash_signal, mode=swap_mispred_event"
                << ", tid=" << (int)tid
                << ", cause=" << (mispredict ? "branch_mispred" : "other")
                << ", squash_sn=" << sn
                << ", signal: " << sq_signals_logged
                << std::endl;
        }
    }

    void
    CHAOSRenameMap::clearSquashSignal()
    {
        // W4 final D14: context disarm — called right after squash()
        // returns (rename.cc). Outside the window the mode is a no-op again.
        sq_active = false;
        sq_mispredict = false;
    }

    bool
    CHAOSRenameMap::maybeCorruptHistory(ThreadID tid, InstSeqNum sn,
                                        const RegId &arch_reg,
                                        PhysRegIdPtr &new_phys,
                                        PhysRegIdPtr &prev_phys)
    {
        // W4 final D23 (hb_bitflip, 1 bit) / D24 (hb_bitflip2, 2 distinct
        // random bits), ooo 04-design-matrix R24/R25 重命名检查点·单/双比
        // 特翻转. Mechanism (verified N1): gem5 has NO separate RAT-checkpoint
        // array — the recovery checkpoint IS the historyBuffer entry
        // RenameHistory{instSeqNum, archReg, newPhysReg, prevPhysReg}
        // (rename.hh:301), created at Rename::renameDestRegs (push_front,
        // rename.cc) and consumed by doSquash (mispred restore) or
        // removeFromHistory (commit release). The injection flips bit(s) of
        // ONE field's physReg index at CREATION; the instruction itself
        // keeps its TRUE dest (rename.cc feeds inst->renameDestReg from the
        // untouched rename_result — only the checkpoint copy is corrupted),
        // so the fault is DORMANT until the checkpoint is consumed:
        //   - prevPhysReg flip -> doSquash restores the WRONG phys into the
        //     RAT / removeFromHistory frees the WRONG phys (duplicate free);
        //   - newPhysReg flip  -> doSquash queues the WRONG phys for the
        //     post-squash free (leaking the true one / double-freeing).
        if (fi_mode != Mode::HbBitflip && fi_mode != Mode::HbBitflip2) {
            // W5.6 D36-D39 oldphys family: same push_front site, same
            // dormancy/consumption model, but the corrupted field is
            // ALWAYS the old-phys (prevPhysReg) — the design's "ROB的旧
            // 物理寄存器字段（squash 回滚要用）". Dispatch to its own
            // implementation (gates mirror hb's).
            if (fi_mode == Mode::OldphysBitflip
                    || fi_mode == Mode::OldphysBitflip2
                    || fi_mode == Mode::OldphysSwapActive
                    || fi_mode == Mode::OldphysStuck)
                return maybeCorruptOldphys(tid, sn, arch_reg,
                                            new_phys, prev_phys);
            return false;
        }
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;
        if (!inWindow()) return false;
        if (arch_reg.classValue() != IntRegClass) return false;
        int arch_idx = arch_reg.index();
        if (arch_idx > 30) return false;  // XZR / banked slots
        // Only REAL renames: misc/zero regs carry new==prev and are never
        // restored/freed by the consumers (the newPhysReg != prevPhysReg
        // guard at both consumption sites) — a flip there would be dead.
        if (new_phys == prev_phys) return false;

        // directed target or random within 0..30 (the W4.4 flat-index
        // discipline: target compares the FLATTENED int-reg index).
        int target = target_arch_reg;
        if (target < 0) target = (int)(rng() % 31);  // 0..30
        if (arch_idx != target) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;
        int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();

        // pick the field to corrupt: 50/50 newPhysReg / prevPhysReg
        bool flip_new = ((int)(rng() % 2)) == 0;

        // pick the bit(s): faultMask with enough set bits = directed control
        // (lowest set bits); otherwise uniform random distinct bits over the
        // index field. Out-of-range flip = honest skip (NO clamp — a clamped
        // value would not be the bit-flip fault model; map_bitflip2 policy).
        int nbits = 0; int tmp = num_phys;
        while (tmp > 1) { nbits++; tmp >>= 1; }
        int b1 = -1, b2 = -1;
        int need = (fi_mode == Mode::HbBitflip) ? 1 : 2;
        if (nbits < need) return false;  // index field too small
        if ((int)__builtin_popcountll(fault_mask) >= need) {
            b1 = __builtin_ctzll(fault_mask);
            if (need == 2) {
                uint64_t rest = fault_mask & ~(1ULL << b1);
                b2 = __builtin_ctzll(rest);
            }
        } else if (fi_mode == Mode::HbBitflip) {
            b1 = (int)(rng() % (unsigned)nbits);
        } else {
            b1 = (int)(rng() % (unsigned)nbits);
            b2 = (int)(rng() % (unsigned)(nbits - 1));
            if (b2 >= b1) b2++;
        }
        if (need == 2 && (b1 == b2 || b1 >= nbits || b2 >= nbits))
            return false;

        PhysRegIdPtr &field = flip_new ? new_phys : prev_phys;
        int cur_idx = field->index();
        int flipped = cur_idx ^ (1 << b1) ^ (need == 2 ? (1 << b2) : 0);
        if (flipped < 0 || flipped >= num_phys) {
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rename_history_push_front, mode="
                    << modeToString(fi_mode)
                    << ", tid=" << (int)tid
                    << ", sn=" << sn
                    << ", arch=X" << arch_idx
                    << ", field=" << (flip_new ? "newPhysReg" : "prevPhysReg")
                    << ", true_phys=" << cur_idx
                    << ", bits=(" << b1;
                if (need == 2) *(log_stream->stream()) << "," << b2;
                *(log_stream->stream())
                    << ") — flipped idx " << flipped << " out of [0,"
                    << num_phys << ") (skipped, no clamp)" << std::endl;
            }
            return false;
        }

        // Apply: re-point the checkpoint's field at the flipped physReg.
        // The caller (rename.cc renameDestRegs) builds the RenameHistory
        // from these by-ref values while feeding the instruction the TRUE
        // dest — the checkpoint diverges from the machine state silently.
        field = o3cpu->physRegFile().intPhysRegId(flipped);
        faults_injected_count++;

        // Arm the one-shot consumption watch (the evidence that the WRONG
        // phys was actually restored/freed at consumption time).
        hb_watch_armed = true;
        hb_watch_sn = sn;
        hb_watch_arch_idx = arch_idx;
        hb_watch_is_new_field = flip_new ? 1 : 0;
        hb_watch_orig_idx = cur_idx;
        hb_watch_corrupt_idx = flipped;

        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: rename_history_push_front, mode="
                << modeToString(fi_mode)
                << ", tid=" << (int)tid
                << ", sn=" << sn
                << ", arch=X" << arch_idx
                << ", field=" << (flip_new ? "newPhysReg" : "prevPhysReg")
                << ", true_phys=" << cur_idx
                << ", checkpoint_phys=" << flipped
                << ", bits=(" << b1;
            if (need == 2) *(log_stream->stream()) << "," << b2;
            *(log_stream->stream())
                << ")"
                << ", dormant_until_consumed (doSquash restore or "
                "removeFromHistory release)"
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    bool
    CHAOSRenameMap::maybeCorruptOldphys(ThreadID tid, InstSeqNum sn,
                                        const RegId &arch_reg,
                                        PhysRegIdPtr &new_phys,
                                        PhysRegIdPtr &prev_phys)
    {
        // W5.6 (ooo 04-design-matrix D36-D39, Int Dispatch/ROB, ROB的旧
        // 物理寄存器字段): the entry's old-phys — the value a squash
        // rollback restores into the RAT and a commit release frees. In
        // gem5 that value is the rename historyBuffer checkpoint's
        // prevPhysReg (W4 N1 mechanism finding), created HERE at
        // renameDestRegs push_front and consumed by doSquash
        // (setEntry(archReg, prevPhysReg) + freeingInProgress of newPhysReg)
        // or removeFromHistory (freeList->addReg(prevPhysReg)). The
        // corruption at creation is DORMANT — the design's "平时注入无
        // 效果（该字段只在 squash 路径上被读取）... 潜伏期最长" — and
        // the consumption watch (notifyHistoryConsumed) logs the moment
        // the WRONG phys is actually restored/freed.
        //
        // Deviation note (honest, documented): the design rows' trigger
        // reads "commit 阶段处理异常/分支误预测导致的 squash 时触发";
        // the gem5 realization injects at the checkpoint's CREATION (the
        // W4 hb_bitflip mount point — the checkpoint does not exist as a
        // writable structure at squash time; doSquash consumes and erases
        // in one pass). The "squash-event" semantics survive as the
        // dormancy-until-squash-consumption model, and the fixed-interval
        // vs event-hit-rate question (D36's stated purpose: 检验「按事件
        // 触发」是否比固定间隔更有效) becomes measurable through the
        // consumed-vs-injected ratio in the logs.
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults
                && !(fi_mode == Mode::OldphysStuck && ops_armed))
            return false;  // stuck: maxFaults gates only the ARMING
        // F5 discipline (the f5_rat_stuck precedent): the window gates the
        // fault's CREATION (arming / one-shot injection) only — a stuck
        // defect's write-path applications are permanent-from-existence and
        // must keep applying after the window closes.
        if (!(fi_mode == Mode::OldphysStuck && ops_armed) && !inWindow())
            return false;
        if (arch_reg.classValue() != IntRegClass) return false;
        int arch_idx = arch_reg.index();
        if (arch_idx > 30) return false;  // XZR / banked slots
        // Only REAL renames: misc/zero regs carry new==prev and both
        // consumers skip them — a corrupted old-phys there would be dead.
        if (new_phys == prev_phys) return false;

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;
        int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();
        int nbits = 0; int tmp = num_phys;
        while (tmp > 1) { nbits++; tmp >>= 1; }
        if (nbits < 1) nbits = 1;

        int cur_idx = prev_phys->index();

        // ---- D39 oldphys_stuck (F5): permanent write-path mask on the
        // old-phys FIELD cell. Arming = the counted fault (probability/
        // maxFaults/inWindow gate ONLY this); every later eligible push's
        // prevPhysReg write is masked — passive, ungated (F5 = permanent
        // from existence, the f5_rat_stuck/pc_stuck arming pattern).
        // targetArchReg is deliberately IGNORED here: the defect is the
        // shared field cell ("随机选一个比特位置" — no 表项 selection in
        // the D39 text, in contrast to f5_rat_stuck's "随机选一个 RAT
        // 表项"), so the mask applies to every int-class real rename.
        if (fi_mode == Mode::OldphysStuck) {
            if (!ops_armed) {
                std::uniform_real_distribution<float> pd(0.0f, 1.0f);
                if (pd(rng) > probability) return false;
                ops_bit = fault_mask
                    ? (int)__builtin_ctzll(fault_mask) % nbits
                    : (int)(rng() % (unsigned)nbits);
                ops_polarity = (int)(rng() % 2);
                ops_armed = true;
                faults_injected_count++;
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rename_history_push_front, mode="
                           "oldphys_stuck, ARMED"
                        << ", tid=" << (int)tid
                        << ", sn=" << sn
                        << ", bit=" << ops_bit
                        << ", polarity=" << ops_polarity
                        << (ops_polarity ? " (stuck_at_one)" :
                                           " (stuck_at_zero)")
                        << ", scope=old-phys FIELD cell (every int-class"
                           " prevPhysReg write masked; shared-cell reading"
                           " of D39 \"持久缺陷+多次 squash 反复命中\")"
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                // fall through: mask THIS write now
            }
            ops_exposures++;
            int masked = ops_polarity
                ? (cur_idx | (1 << ops_bit))
                : (cur_idx & ~(1 << ops_bit));
            if (masked == cur_idx) {
                // written value already carries the polarity — the stuck
                // cell does not change it (present but value-masked)
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rename_history_push_front, mode="
                           "oldphys_stuck"
                        << ", tid=" << (int)tid
                        << ", sn=" << sn
                        << ", arch=X" << arch_idx
                        << ", write_oldphys=" << cur_idx
                        << ", stored_oldphys=" << masked
                        << " (bit " << ops_bit << " already at "
                        << ops_polarity << ", no observable change)"
                        << ", exposure: " << ops_exposures
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                return true;
            }
            if (masked < 0 || masked >= num_phys) {
                // non-power-of-2 pool: forcing the bit can leave the valid
                // index range — honest skip, THIS write stores unmasked.
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rename_history_push_front, mode="
                           "oldphys_stuck"
                        << ", tid=" << (int)tid
                        << ", sn=" << sn
                        << ", write_oldphys=" << cur_idx
                        << " — forced idx " << masked << " out of [0,"
                        << num_phys << ") (skipped this write, no clamp)"
                        << ", exposure: " << ops_exposures
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                return false;
            }
            prev_phys = o3cpu->physRegFile().intPhysRegId(masked);
            ops_masked_count++;
            ops_masked_sns.insert(sn);  // multi-consumption watch key
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rename_history_push_front, mode="
                       "oldphys_stuck"
                    << ", tid=" << (int)tid
                    << ", sn=" << sn
                    << ", arch=X" << arch_idx
                    << ", write_oldphys=" << cur_idx
                    << ", stored_oldphys=" << masked
                    << ", bit=" << ops_bit << " forced to " << ops_polarity
                    << ", exposure: " << ops_exposures
                    << ", masked_writes: " << ops_masked_count
                    << ", dormant_until_consumed (doSquash restore or"
                       " removeFromHistory release)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }

        // ---- D36/D37/D38 one-shot modes: directed target or random 0..30
        // (the W4.4 flat-index discipline), probability-gated.
        int target = target_arch_reg;
        if (target < 0) target = (int)(rng() % 31);  // 0..30
        if (arch_idx != target) return false;
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        int new_idx = -1;
        int log_b1 = -1, log_b2 = -1;
        int log_rob_dist = -1;
        uint64_t log_chosen_sn = 0;
        std::vector<RobCand> rob_cands;

        if (fi_mode == Mode::OldphysBitflip
                || fi_mode == Mode::OldphysBitflip2) {
            // D36 (R37, 单比特) / D37 (R38, 双比特): flip 1 / 2 distinct
            // bits of the old-phys index. faultMask with enough set bits =
            // directed control (lowest set bits); else uniform random
            // distinct bits. Out-of-range = honest skip, NO clamp.
            int need = (fi_mode == Mode::OldphysBitflip) ? 1 : 2;
            if (nbits < need) return false;
            int b1 = -1, b2 = -1;
            if ((int)__builtin_popcountll(fault_mask) >= need) {
                b1 = __builtin_ctzll(fault_mask);
                if (need == 2) {
                    uint64_t rest = fault_mask & ~(1ULL << b1);
                    b2 = __builtin_ctzll(rest);
                }
            } else if (need == 1) {
                b1 = (int)(rng() % (unsigned)nbits);
            } else {
                b1 = (int)(rng() % (unsigned)nbits);
                b2 = (int)(rng() % (unsigned)(nbits - 1));
                if (b2 >= b1) b2++;
            }
            if (need == 2 && (b1 == b2 || b1 >= nbits || b2 >= nbits))
                return false;
            int flipped = cur_idx ^ (1 << b1)
                ^ (need == 2 ? (1 << b2) : 0);
            if (flipped < 0 || flipped >= num_phys) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rename_history_push_front, mode="
                        << modeToString(fi_mode)
                        << ", tid=" << (int)tid
                        << ", sn=" << sn
                        << ", arch=X" << arch_idx
                        << ", field=prevPhysReg"
                        << ", true_oldphys=" << cur_idx
                        << ", bits=(" << b1;
                    if (need == 2) *(log_stream->stream()) << "," << b2;
                    *(log_stream->stream())
                        << ") — flipped idx " << flipped << " out of [0,"
                        << num_phys << ") (skipped, no clamp)" << std::endl;
                }
                return false;
            }
            new_idx = flipped;
            log_b1 = b1; log_b2 = b2;
        } else {
            // D38 (R39, 换值): replace the old-phys with the dest physReg
            // of ANOTHER in-flight (ROB-resident) instruction — legal
            // domain by construction (the D13 swap_to_active / D30
            // destid_swap_active pattern, old-phys flavor). The squash
            // restore then re-maps the arch reg onto a physReg that is
            // still in use by another instruction — the designed
            // "squash 会错误释放/覆盖一个正在用的寄存器" SDC path.
            int nc = collectRobActiveDests(cur_idx, o3cpu, tid, rob_cands);
            // additionally exclude the entry's own new dest: restoring
            // new_phys would be a degenerate self-referential no-op.
            int new_idx_own = new_phys->index();
            int n_ok = 0;
            for (int i = 0; i < nc; i++) {
                if (rob_cands[i].phys_idx == new_idx_own) continue;
                rob_cands[n_ok++] = rob_cands[i];
            }
            if (n_ok == 0) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rename_history_push_front, mode="
                           "oldphys_swap_active"
                        << ", tid=" << (int)tid
                        << ", sn=" << sn
                        << ", arch=X" << arch_idx
                        << ", true_oldphys=" << cur_idx
                        << " — ROB has no active int dest candidate"
                           " != cur/new (skipped, no injection)"
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                return false;
            }
            int pick = (int)(rng() % (unsigned)n_ok);
            new_idx = rob_cands[pick].phys_idx;
            log_rob_dist = rob_cands[pick].dist;
            log_chosen_sn = rob_cands[pick].sn;
        }

        if (new_idx < 0 || new_idx == cur_idx || new_idx >= num_phys)
            return false;

        // Apply: the checkpoint's old-phys field points at the corrupted
        // physReg; the instruction's OWN renameDestReg(., new, prev) is
        // fed from the untouched rename_result (rename.cc) — only the
        // checkpoint diverges, dormant until consumption.
        prev_phys = o3cpu->physRegFile().intPhysRegId(new_idx);
        faults_injected_count++;

        // one-shot consumption watch (the W4 hb_bitflip evidence reuse:
        // logs doSquash/removeFromHistory consuming the WRONG phys).
        hb_watch_armed = true;
        hb_watch_sn = sn;
        hb_watch_arch_idx = arch_idx;
        hb_watch_is_new_field = 0;       // old-phys = prevPhysReg field
        hb_watch_orig_idx = cur_idx;
        hb_watch_corrupt_idx = new_idx;

        if (write_log) {
            if (fi_mode == Mode::OldphysSwapActive) {
                // the D13/D30 evidence format: swap + "(active,
                // rob_dist=D)" + chosen_sn + the full ROB-active pool.
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rename_history_push_front, mode="
                       "oldphys_swap_active"
                    << ", tid=" << (int)tid
                    << ", sn=" << sn
                    << ", arch=X" << arch_idx
                    << ", field=prevPhysReg"
                    << ", true_oldphys=" << cur_idx
                    << ", checkpoint_oldphys=" << new_idx
                    << "(active, rob_dist=" << log_rob_dist << ")"
                    << ", chosen_sn=" << log_chosen_sn
                    << ", rob_active_dests=[";
                for (size_t i = 0; i < rob_cands.size(); i++) {
                    if (i) *(log_stream->stream()) << " ";
                    *(log_stream->stream()) << rob_cands[i].phys_idx
                        << "@" << rob_cands[i].dist;
                }
                *(log_stream->stream()) << "]"
                    << ", dormant_until_consumed (doSquash restore or"
                       " removeFromHistory release)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            } else {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rename_history_push_front, mode="
                    << modeToString(fi_mode)
                    << ", tid=" << (int)tid
                    << ", sn=" << sn
                    << ", arch=X" << arch_idx
                    << ", field=prevPhysReg"
                    << ", true_oldphys=" << cur_idx
                    << ", checkpoint_oldphys=" << new_idx
                    << ", bits=(" << log_b1;
                if (fi_mode == Mode::OldphysBitflip2)
                    *(log_stream->stream()) << "," << log_b2;
                *(log_stream->stream())
                    << ")"
                    << ", dormant_until_consumed (doSquash restore or"
                       " removeFromHistory release)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
        }
        return true;
    }

    void
    CHAOSRenameMap::notifyHistoryConsumed(ThreadID tid, InstSeqNum sn,
                                          const RegId &arch_reg,
                                          PhysRegIdPtr new_phys,
                                          PhysRegIdPtr prev_phys,
                                          const char *site)
    {
        // W4 final D23/D24 consumption watch: READ-ONLY. Fired from
        // Rename::doSquash (site="rename_doSquash") and
        // Rename::removeFromHistory (site="rename_removeFromHistory") for
        // every history entry they process; logs the end of the dormancy
        // window when the corrupted checkpoint is the one being consumed.
        //
        // W5.6 D39 oldphys_stuck: the repeatable-defect multi-consumption
        // watch — EVERY entry whose old-phys the stuck mask actually
        // changed is in ops_masked_sns; each consumption logs the "same
        // error mode recurring across squashes" evidence line (the
        // design's 累积效应 metric). The one-shot hb watch below is never
        // armed in stuck mode.
        if (fi_mode == Mode::OldphysStuck && ops_armed) {
            auto it = ops_masked_sns.find(sn);
            if (it != ops_masked_sns.end()) {
                ops_masked_sns.erase(it);
                if (write_log && log_stream) {
                    int consumed_idx = prev_phys ? prev_phys->index() : -1;
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: " << site << ", mode=oldphys_stuck"
                        << ", OLDPHYS_STUCK_CONSUMED: checkpoint sn=" << sn
                        << ", tid=" << (int)tid
                        << ", arch=X"
                        << (arch_reg.classValue() == IntRegClass
                                ? std::to_string(arch_reg.index()) : "?")
                        << ", consumed_oldphys=" << consumed_idx
                        << ", bit=" << ops_bit << " polarity=" << ops_polarity
                        << " (MASKED value restored/freed — repeatable"
                           " defect, masked-consumption #"
                        << (ops_masked_count - ops_masked_sns.size())
                        << " of " << ops_masked_count << ")"
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
            }
            return;
        }
        if (!hb_watch_armed || sn != hb_watch_sn) return;
        hb_watch_armed = false;
        if (!write_log || !log_stream) return;
        int consumed_idx = hb_watch_is_new_field
            ? (new_phys ? new_phys->index() : -1)
            : (prev_phys ? prev_phys->index() : -1);
        *(log_stream->stream()) << "Tick: " << curTick()
            << ", Site: " << site << ", mode=" << modeToString(fi_mode)
            << ", tid=" << (int)tid
            << ", HISTORY_CONSUMED: checkpoint sn=" << sn
            << ", arch=X" << hb_watch_arch_idx
            << ", corrupted_field="
            << (hb_watch_is_new_field ? "newPhysReg" : "prevPhysReg")
            << ", true_phys=" << hb_watch_orig_idx
            << ", consumed_phys=" << consumed_idx
            << (consumed_idx == hb_watch_corrupt_idx
                ? " (the WRONG phys was restored/freed — dormancy ended)"
                : " (MISMATCH vs armed corruption — consumed value differs)")
            << ", faults_injected: " << faults_injected_count
            << std::endl;
    }

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
