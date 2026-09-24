#include "cpu/o3/CHAOSROB/CHAOSROB.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/rob.hh"           // ROB
#include "cpu/o3/regfile.hh"       // PhysRegFile, intPhysRegId
#include "cpu/o3/dyn_inst.hh"      // DynInst, getFault, status
#include "cpu/reg_class.hh"        // IntRegClass
#include "arch/arm/pcstate.hh"     // ArmISA::PCState (pc(Addr) field setter)
#include "debug/CHAOSROB.hh"
#include "params/CHAOSROB.hh"

namespace gem5
{

    CHAOSROB::CHAOSROB(const CHAOSROBParams &p)
        : SimObject(p),
          cpu(p.cpu),
          fi_mode(stringToMode(p.mode)),
          field(stringToField(p.field)),
          distance_from_head(p.distanceFromHead),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          fault_mask(p.faultMask),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("rob_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSROB: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
    }

    CHAOSROB::~CHAOSROB() {}

    CHAOSROB::Mode
    CHAOSROB::stringToMode(const std::string &s) {
        if (s == "entry_bitflip") return Mode::EntryBitflip;
        if (s == "exc_suppress") return Mode::ExcSuppress;
        // W5.1-W5.3 (ooo 04-design-matrix D25-D31, Int Dispatch/ROB)
        if (s == "pc_bitflip") return Mode::PcBitflip;
        if (s == "pc_bitflip2") return Mode::PcBitflip2;
        if (s == "pc_stuck") return Mode::PcStuck;
        if (s == "destid_bitflip") return Mode::DestIdBitflip;
        if (s == "destid_bitflip2") return Mode::DestIdBitflip2;
        if (s == "destid_swap_active") return Mode::DestIdSwapActive;
        if (s == "destid_stuck") return Mode::DestIdStuck;
        return Mode::EntryBitflip;
    }

    const char*
    CHAOSROB::modeToString(CHAOSROB::Mode m) {
        switch (m) {
            case Mode::EntryBitflip: return "entry_bitflip";
            case Mode::ExcSuppress: return "exc_suppress";
            case Mode::PcBitflip: return "pc_bitflip";
            case Mode::PcBitflip2: return "pc_bitflip2";
            case Mode::PcStuck: return "pc_stuck";
            case Mode::DestIdBitflip: return "destid_bitflip";
            case Mode::DestIdBitflip2: return "destid_bitflip2";
            case Mode::DestIdSwapActive: return "destid_swap_active";
            case Mode::DestIdStuck: return "destid_stuck";
        }
        return "entry_bitflip";
    }

    CHAOSROB::Field
    CHAOSROB::stringToField(const std::string &s) {
        if (s == "result") return Field::Result;
        if (s == "done") return Field::Done;
        if (s == "exc_status") return Field::ExcStatus;
        if (s == "dest_phys") return Field::DestPhys;
        if (s == "spec") return Field::Spec;
        return Field::ExcStatus;
    }

    bool
    CHAOSROB::inWindow() {
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
    CHAOSROB::collectIntDestSlots(const o3::DynInstPtr &inst,
                                  std::vector<int> &slots)
    {
        // Int Dispatch/ROB unit scope (W5): the dest-id field = the INTEGER
        // dest physReg identifiers of the entry. FP/vector dests belong to
        // the W7 FP unit. Returns the number of int-class dest slots.
        slots.clear();
        for (int i = 0; i < (int)inst->numDestRegs(); i++) {
            PhysRegIdPtr d = inst->renamedDestIdx(i);
            if (!d) continue;
            if (d->classValue() != IntRegClass) continue;
            slots.push_back(i);
        }
        return (int)slots.size();
    }

    int
    CHAOSROB::collectRobActiveDests(int cur_idx, uint64_t self_sn,
                                    o3::CPU *o3cpu, ThreadID tid,
                                    std::vector<RobDestCand> &cands)
    {
        // W5.2 D30 destid_swap_active: the swap pool = int dest physRegs of
        // instructions currently ROB-resident (in flight). Each such physReg
        // is by construction allocated and in use (grabbed from the freelist
        // at rename, freed only after its owner commits and the next definer
        // retires) — a swap onto it is LEGAL-domain and bypasses the
        // random-flip luck of D28/D29 (the W4.2a collectRobActiveDests
        // precedent in CHAOSRenameMap.cc, reused at the ROB-insert site).
        // The inserting inst itself is excluded (self_sn): swapping an
        // entry's own dest for its own dest is a no-op. Read-only walk
        // head->tail via getEntryAtDistance; called from ROB::insertInst
        // AFTER the new entry is linked (the list is complete and stable).
        cands.clear();
        o3::ROB &rob = o3cpu->o3ROB();
        for (int d = 0; ; d++) {
            o3::DynInstPtr ri = rob.getEntryAtDistance(tid, d);
            if (!ri) break;  // past tail / empty
            if (ri->seqNum == self_sn) continue;
            for (int i = 0; i < (int)ri->numDestRegs(); i++) {
                PhysRegIdPtr dest = ri->renamedDestIdx(i);
                if (!dest) continue;
                if (dest->classValue() != IntRegClass) continue;
                int pidx = dest->index();
                if (pidx == cur_idx) continue;  // must differ from current
                cands.push_back({pidx, d, ri->seqNum});
            }
        }
        return (int)cands.size();
    }

    bool
    CHAOSROB::maybeCorrupt(ThreadID tid, o3::DynInstPtr &head_inst)
    {
        // W5.2 stuck read-back (D27/D31 "该 ROB 项在整个存活期间是否被
        // 反复读取到同一个错误值" persistence evidence): when the ARMED
        // entry leaves the ROB, read its field back and verify the stuck
        // bit is still at the forced polarity. One line per armed entry.
        if ((fi_mode == Mode::PcStuck || fi_mode == Mode::DestIdStuck)
                && stuck_armed && !stuck_readback_done)
            checkStuckReadback(head_inst);

        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        if (fi_mode == Mode::ExcSuppress) {
            // §2.3 exc_suppress: clear the head's fault -> a pending
            // SError/DUE is silently swallowed (DUE->SDC conversion).
            Fault &fref = head_inst->getFault();
            Fault old = fref;
            fref = NoFault;
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_retireHead, mode=exc_suppress, tid=" << (int)tid
                    << ", head_sn=" << head_inst->seqNum
                    << ", cleared_fault=" << (old ? "yes" : "none")
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        } else if (fi_mode == Mode::EntryBitflip) {
            // §2.3 entry_bitflip: flip a field of the entry at distance D
            // from head. exc_status/done: toggle CanCommit (clear => the
            // instruction can't commit -> stall/Crash; set => re-enable).
            int D = distance_from_head;
            if (D < 0) D = (int)(rng() % 4);
            o3::DynInstPtr target = o3cpu->o3ROB().getEntryAtDistance(tid, D);
            if (!target) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rob_retireHead, mode=entry_bitflip"
                        << " — NO entry at D=" << D << " (skipped)." << std::endl;
                }
                return false;
            }
            // toggle CanCommit on the target (the done/exc_status proxy).
            if (target->readyToCommit()) target->clearCanCommit();
            else                          target->setCanCommit();
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_retireHead, mode=entry_bitflip"
                    << ", field=" << (field == Field::ExcStatus ? "exc_status" : "done")
                    << ", tid=" << (int)tid << ", D=" << D
                    << ", target_sn=" << target->seqNum
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }
        return false;
    }

    // spec_leak (method1 speculative-state-leak) is DEFERRED — needs the
    // squash path edit (don't roll back a wrong-path µop's phys-reg write).
    // §2.3 patch 2.

    bool
    CHAOSROB::maybeCorruptEntry(ThreadID tid, const o3::DynInstPtr &inst)
    {
        // W5.1-W5.3 (ooo 04-design-matrix D25-D31, Int Dispatch/ROB), the
        // ROB-entry WRITE path: ROB::insertInst calls this right after the
        // entry is linked, i.e. the fault is in the entry's field as the
        // entry is written into the ROB (the TC'23 "random bit of a ROB
        // entry" site, field-level refined: pcState pc / int dest physReg
        // id). The pre-existing rob.cc:254 retireHead hook is post-commit
        // (too late for in-flight PC/dest-id corruption) — the Field enum
        // of the legacy entry_bitflip mode is log strings only.
        //
        // Expected outcomes (design matrix): D25/D26/D28/D29 are the TC'23
        // reproduction cells — random PC / dest-id flips are expected to be
        // intercepted by the IQ dependency graph (IQ wakes dependents on
        // renamedDestIdx at completion, inst_queue.cc:1151; scoreboard
        // busy/clear on dispatch/writeback) -> Crash/Hang with SDC~=0%.
        // That IS the M2-gate expectation, recorded honestly. D30
        // swap_active is the designed bypass (legal in-use id).
        if (fi_mode == Mode::EntryBitflip || fi_mode == Mode::ExcSuppress)
            return false;  // legacy modes live on the retireHead site only

        // F5 stuck modes: arming is the counted fault; the application is
        // the write-path mask on the armed entry (f5_rat_stuck precedent —
        // dispatch before the generic gates so the mask is ungated by
        // max_faults/probability once armed).
        if (fi_mode == Mode::PcStuck || fi_mode == Mode::DestIdStuck)
            return maybeStuckEntryWrite(tid, inst);

        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        // bounded skip logging (prob<1 unlimited-fault campaigns would
        // otherwise emit a skip line per ineligible insert)
        static thread_local uint64_t skip_logs = 0;

        if (fi_mode == Mode::PcBitflip || fi_mode == Mode::PcBitflip2) {
            // D25 (R26, PC字段·单比特翻转) / D26 (R27, 双比特翻转): flip
            // 1 / 2 distinct random bits of the entry's PC field (the
            // pcState pc address; ~48-bit address space per the design
            // note). Field-exact: only _pc changes (ArmISA::PCState::pc()
            // setter; flags/npc untouched). Downstream readers of a
            // ROB-resident entry's PC: branch execute (target computed
            // from the entry's own pcState) and commit.cc:990
            // set(pc[tid], head_inst->pcState()).
            const int pc_nbits = 48;
            ArmISA::PCState ns = inst->pcState().as<ArmISA::PCState>();
            Addr old_pc = ns.pc();
            int b1 = -1, b2 = -1;
            if (fi_mode == Mode::PcBitflip) {
                b1 = fault_mask
                    ? (int)__builtin_ctzll(fault_mask) % pc_nbits
                    : (int)(rng() % (unsigned)pc_nbits);
            } else {
                if (__builtin_popcountll(fault_mask) >= 2) {
                    // directed control: the two lowest set bits
                    b1 = __builtin_ctzll(fault_mask);
                    uint64_t rest = fault_mask & ~(1ULL << b1);
                    b2 = __builtin_ctzll(rest);
                } else {
                    // uniform random DISTINCT pair (order-statistics trick)
                    b1 = (int)(rng() % (unsigned)pc_nbits);
                    b2 = (int)(rng() % (unsigned)(pc_nbits - 1));
                    if (b2 >= b1) b2++;
                }
                if (b1 == b2 || b1 >= pc_nbits || b2 >= pc_nbits) return false;
            }
            Addr xor_mask = (1ULL << b1)
                | (fi_mode == Mode::PcBitflip2 ? (1ULL << b2) : 0);
            Addr new_pc = old_pc ^ xor_mask;
            ns.pc(new_pc);
            inst->pcState(ns);
            int hamming = __builtin_popcountll(old_pc ^ new_pc);
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_insert, mode=" << modeToString(fi_mode)
                    << ", tid=" << (int)tid
                    << ", sn=" << inst->seqNum
                    << ", old_pc=0x" << std::hex << old_pc
                    << ", new_pc=0x" << new_pc << std::dec
                    << ", bits=(" << b1;
                if (fi_mode == Mode::PcBitflip2)
                    *(log_stream->stream()) << "," << b2;
                *(log_stream->stream()) << ")"
                    << ", hamming=" << hamming
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }

        if (fi_mode == Mode::DestIdBitflip || fi_mode == Mode::DestIdBitflip2
                || fi_mode == Mode::DestIdSwapActive) {
            // D28 (R29, 寄存器标识符·单比特) / D29 (R30, 双比特) / D30
            // (R31, 换值): corrupt ONE integer dest physReg identifier of
            // the entry being written. The flip lands after the IQ insert
            // (renameToIEWDelay=1 < renameToROBDelay=2) but before
            // completion/writeback, so the IQ wake (inst_queue.cc:1151)
            // and the scoreboard clear / result write see the WRONG id
            // while the dependency lists were built on the TRUE one — the
            // gem5 manifestation of the TC'23 dependency-check intercept.
            std::vector<int> slots;
            int n = collectIntDestSlots(inst, slots);
            if (n == 0) {
                // The field does not exist on this entry (branch/store have
                // no int dest) — honest skip, nothing to flip.
                if (write_log && skip_logs < 32) {
                    ++skip_logs;
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rob_insert, mode=" << modeToString(fi_mode)
                        << ", tid=" << (int)tid
                        << ", sn=" << inst->seqNum
                        << " — entry has no int dest (skipped, no field)"
                        << ", skip_log: " << skip_logs
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                return false;
            }
            int slot = slots[(int)(rng() % (unsigned)n)];
            PhysRegIdPtr cur = inst->renamedDestIdx(slot);
            int cur_idx = cur->index();
            int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();
            if (num_phys <= 1) return false;

            int new_idx = -1;
            int log_b1 = -1, log_b2 = -1;
            int log_rob_dist = -1;
            uint64_t log_chosen_sn = 0;
            std::vector<RobDestCand> rob_cands;

            if (fi_mode == Mode::DestIdBitflip) {
                // 1-bit flip of the physReg index. On the C3 north-star
                // (num_phys=128=2^7) every bit of the 7-bit index field
                // flips within [0,128) — hamming exactly 1, always.
                int nbits = 0; int tmp = num_phys;
                while (tmp > 1) { nbits++; tmp >>= 1; }
                if (nbits < 1) nbits = 1;
                int bit = fault_mask
                    ? (int)__builtin_ctzll(fault_mask) % nbits
                    : (int)(rng() % (unsigned)nbits);
                int flipped = cur_idx ^ (1 << bit);
                if (flipped < 0 || flipped >= num_phys) {
                    // non-power-of-2 pool: honest skip, no clamp (a clamped
                    // id would not be the 1-bit-flip fault model)
                    if (write_log && skip_logs < 32) {
                        ++skip_logs;
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Site: rob_insert, mode=destid_bitflip"
                            << ", tid=" << (int)tid
                            << ", sn=" << inst->seqNum
                            << ", old_phys=" << cur_idx
                            << " — flipped idx " << flipped << " out of [0,"
                            << num_phys << ") (skipped, no clamp)"
                            << ", skip_log: " << skip_logs
                            << ", faults_injected: " << faults_injected_count
                            << std::endl;
                    }
                    return false;
                }
                new_idx = flipped;
                log_b1 = bit;
            } else if (fi_mode == Mode::DestIdBitflip2) {
                // 2 distinct random bits of the physReg index (D29: the
                // narrow-field twin of D26 — on 128 physRegs any 2-bit flip
                // stays in range and changes the value, hamming exactly 2).
                int nbits = 0; int tmp = num_phys;
                while (tmp > 1) { nbits++; tmp >>= 1; }
                if (nbits < 2) return false;
                int b1 = 0, b2 = 0;
                if (__builtin_popcountll(fault_mask) >= 2) {
                    b1 = __builtin_ctzll(fault_mask);
                    uint64_t rest = fault_mask & ~(1ULL << b1);
                    b2 = __builtin_ctzll(rest);
                } else {
                    b1 = (int)(rng() % (unsigned)nbits);
                    b2 = (int)(rng() % (unsigned)(nbits - 1));
                    if (b2 >= b1) b2++;
                }
                if (b1 == b2 || b1 >= nbits || b2 >= nbits) return false;
                int flipped = cur_idx ^ (1 << b1) ^ (1 << b2);
                if (flipped < 0 || flipped >= num_phys) {
                    if (write_log && skip_logs < 32) {
                        ++skip_logs;
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Site: rob_insert, mode=destid_bitflip2"
                            << ", tid=" << (int)tid
                            << ", sn=" << inst->seqNum
                            << ", old_phys=" << cur_idx
                            << " — flipped idx " << flipped << " out of [0,"
                            << num_phys << ") (skipped, no clamp)"
                            << ", skip_log: " << skip_logs
                            << ", faults_injected: " << faults_injected_count
                            << std::endl;
                    }
                    return false;
                }
                new_idx = flipped;
                log_b1 = b1; log_b2 = b2;
            } else {
                // D30 swap_active: replace the dest id with the int dest
                // physReg of ANOTHER in-flight (ROB-resident) instruction —
                // legal-domain by construction, designed to bypass the
                // dependency check (the D13 swap_to_active mechanism at the
                // ROB layer).
                int nc = collectRobActiveDests(cur_idx, inst->seqNum,
                                               o3cpu, tid, rob_cands);
                if (nc == 0) {
                    if (write_log && skip_logs < 32) {
                        ++skip_logs;
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Site: rob_insert, mode=destid_swap_active"
                            << ", tid=" << (int)tid
                            << ", sn=" << inst->seqNum
                            << ", old_phys=" << cur_idx
                            << " — ROB has no active int dest candidate"
                            << " != cur (skipped, no injection)"
                            << ", skip_log: " << skip_logs
                            << ", faults_injected: " << faults_injected_count
                            << std::endl;
                    }
                    return false;
                }
                int pick = (int)(rng() % (unsigned)nc);
                new_idx = rob_cands[pick].phys_idx;
                log_rob_dist = rob_cands[pick].dist;
                log_chosen_sn = rob_cands[pick].sn;
            }

            if (new_idx < 0 || new_idx == cur_idx || new_idx >= num_phys)
                return false;

            // Apply: re-point the entry's dest id at the corrupted physReg
            // (a real physRegId object from the regfile — legal domain, no
            // UB; the CHAOSRenameMap setEntry pattern).
            inst->renamedDestIdx(slot,
                o3cpu->physRegFile().intPhysRegId(new_idx));
            faults_injected_count++;
            if (write_log) {
                if (fi_mode == Mode::DestIdSwapActive) {
                    // plan-mandated evidence line: the swap + "(active,
                    // rob_dist=D)" + chosen_sn + the full ROB-active int
                    // dest pool (phys@dist, head->tail order) so
                    // "new_phys ∈ ROB active set" is verifiable from the
                    // log alone (the W4.2a D13 log format, ROB site).
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rob_insert, mode=destid_swap_active"
                        << ", tid=" << (int)tid
                        << ", sn=" << inst->seqNum
                        << ", dest_slot=" << slot
                        << ", old_phys=" << cur_idx
                        << ", new_phys=" << new_idx << "(active, rob_dist="
                        << log_rob_dist << ")"
                        << ", chosen_sn=" << log_chosen_sn
                        << ", rob_active_dests=[";
                    for (size_t i = 0; i < rob_cands.size(); i++) {
                        if (i) *(log_stream->stream()) << " ";
                        *(log_stream->stream()) << rob_cands[i].phys_idx
                            << "@" << rob_cands[i].dist;
                    }
                    *(log_stream->stream()) << "]"
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                } else {
                    // D28/D29 plan-mandated evidence line: old/new phys idx
                    // + the flipped bit(s) (verifiable: popcount(old^new)
                    // == 1/2 and old ^ (1<<b1) [^ (1<<b2)] == new).
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rob_insert, mode=" << modeToString(fi_mode)
                        << ", tid=" << (int)tid
                        << ", sn=" << inst->seqNum
                        << ", dest_slot=" << slot
                        << ", old_phys=" << cur_idx
                        << ", new_phys=" << new_idx
                        << ", bits=(" << log_b1;
                    if (fi_mode == Mode::DestIdBitflip2)
                        *(log_stream->stream()) << "," << log_b2;
                    *(log_stream->stream()) << ")"
                        << ", hamming="
                        << __builtin_popcountll((uint64_t)cur_idx
                                                ^ (uint64_t)new_idx)
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
            }
            return true;
        }
        return false;
    }

    bool
    CHAOSROB::maybeStuckEntryWrite(ThreadID tid, const o3::DynInstPtr &inst)
    {
        // W5.2 D27 (R28, PC字段·卡死) / D31 (R32, 寄存器标识符·卡死), F5:
        // ONE stuck-at bit in ONE ROB entry's field, armed at the first
        // in-window eligible entry-write (the f5_rat_stuck arming pattern:
        // probability/max_faults gate the FAULT'S CREATION only — F5 is
        // permanent from existence). The write-path mask applies at the
        // armed entry's write (ROB::insertInst — the single write of that
        // entry's PC/destId field: gem5 never rewrites a ROB-resident
        // entry's pcState or renamedDestIdx after insert, so persistence =
        // value permanence, verified by the retire-time read-back in
        // checkStuckReadback). Polarity semantics differ from the bitflip
        // modes: the bit is FORCED to 0/1 (a stuck cell does not XOR — if
        // the written value already carries the polarity the stored value
        // is unchanged, the fault is present but value-masked).
        if (!cpu || probability <= 0.0f) return false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        // For destid_stuck the arming event must be an entry that actually
        // HAS the field (an int dest) — the cell lives in the dest-id field.
        std::vector<int> slots;
        int n_int_dests = 0;
        if (fi_mode == Mode::DestIdStuck) {
            n_int_dests = collectIntDestSlots(inst, slots);
            if (n_int_dests == 0) return false;  // no field on this entry
        }

        if (!stuck_armed) {
            // Arming: D27/D31 "运行开始（首个注入窗口到达时）随机选一个
            // 比特位置，永久固定为 0 或 1" — one bit, polarity 50/50
            // (faultMask's lowest set bit is the directed bit override).
            if (max_faults != 0 && faults_injected_count >= max_faults)
                return false;
            if (!inWindow()) return false;
            std::uniform_real_distribution<float> pd(0.0f, 1.0f);
            if (pd(rng) > probability) return false;

            if (fi_mode == Mode::PcStuck) {
                const int pc_nbits = 48;
                stuck_bit = fault_mask
                    ? (int)__builtin_ctzll(fault_mask) % pc_nbits
                    : (int)(rng() % (unsigned)pc_nbits);
            } else {
                int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();
                int nbits = 0; int tmp = num_phys;
                while (tmp > 1) { nbits++; tmp >>= 1; }
                if (nbits < 1) nbits = 1;
                stuck_bit = fault_mask
                    ? (int)__builtin_ctzll(fault_mask) % nbits
                    : (int)(rng() % (unsigned)nbits);
            }
            stuck_polarity = (int)(rng() % 2);
            stuck_sn = inst->seqNum;
            stuck_armed = true;
            stuck_readback_done = false;
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_insert, mode=" << modeToString(fi_mode)
                    << ", ARMED, tid=" << (int)tid
                    << ", sn=" << stuck_sn
                    << ", bit=" << stuck_bit
                    << ", polarity=" << stuck_polarity
                    << (stuck_polarity ? " (stuck_at_one)" : " (stuck_at_zero)")
                    << ", write_path=rob_insert (single write per entry;"
                    << " gem5 never rewrites a ROB-resident entry's field"
                    << " post-insert — persistence = value permanence,"
                    << " readback at retire)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            // fall through: mask THIS entry write now
        }

        // Applications after arming are passive and ungated (F5): only the
        // ARMED entry's write is masked (one ROB entry = one stuck cell,
        // the design's "该 ROB 项存活期间持续带着这个缺陷").
        if (inst->seqNum != stuck_sn) return false;

        stuck_exposures++;
        if (fi_mode == Mode::PcStuck) {
            ArmISA::PCState ns = inst->pcState().as<ArmISA::PCState>();
            Addr old_pc = ns.pc();
            Addr masked = stuck_polarity
                ? (old_pc | (1ULL << stuck_bit))
                : (old_pc & ~(1ULL << stuck_bit));
            if (masked == old_pc) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rob_insert, mode=pc_stuck"
                        << ", tid=" << (int)tid
                        << ", sn=" << inst->seqNum
                        << ", write_pc=0x" << std::hex << old_pc << std::dec
                        << ", stored_pc=0x" << std::hex << masked << std::dec
                        << " (bit " << stuck_bit << " already at "
                        << stuck_polarity << ", no observable change)"
                        << ", exposure: " << stuck_exposures
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                return true;
            }
            ns.pc(masked);
            inst->pcState(ns);
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_insert, mode=pc_stuck"
                    << ", tid=" << (int)tid
                    << ", sn=" << inst->seqNum
                    << ", write_pc=0x" << std::hex << old_pc
                    << ", stored_pc=0x" << masked << std::dec
                    << ", bit=" << stuck_bit << " forced to " << stuck_polarity
                    << ", hamming="
                    << __builtin_popcountll(old_pc ^ masked)
                    << ", exposure: " << stuck_exposures
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }

        // DestIdStuck: mask ONE int dest slot of the armed entry (the
        // arming entry's first/random slot; multi-int-dest insts are rare
        // on AArch64).
        if (n_int_dests == 0) return false;  // armed entry has no field
        if (stuck_dest_slot < 0)
            stuck_dest_slot = slots[(int)(rng() % (unsigned)n_int_dests)];
        // the armed entry's slot count is fixed; re-derive safely
        if (stuck_dest_slot >= (int)inst->numDestRegs()) return false;
        PhysRegIdPtr cur = inst->renamedDestIdx(stuck_dest_slot);
        if (!cur || cur->classValue() != IntRegClass) return false;
        int written = cur->index();
        int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();
        int masked = stuck_polarity
            ? (written | (1 << stuck_bit))
            : (written & ~(1 << stuck_bit));
        if (masked == written) {
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_insert, mode=destid_stuck"
                    << ", tid=" << (int)tid
                    << ", sn=" << inst->seqNum
                    << ", dest_slot=" << stuck_dest_slot
                    << ", write_phys=" << written
                    << ", stored_phys=" << masked
                    << " (bit " << stuck_bit << " already at "
                    << stuck_polarity << ", no observable change)"
                    << ", exposure: " << stuck_exposures
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
                    << ", Site: rob_insert, mode=destid_stuck"
                    << ", tid=" << (int)tid
                    << ", sn=" << inst->seqNum
                    << ", write_phys=" << written
                    << " — forced idx " << masked << " out of [0,"
                    << num_phys << ") (skipped this write, no clamp)"
                    << ", exposure: " << stuck_exposures
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return false;
        }
        inst->renamedDestIdx(stuck_dest_slot,
            o3cpu->physRegFile().intPhysRegId(masked));
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: rob_insert, mode=destid_stuck"
                << ", tid=" << (int)tid
                << ", sn=" << inst->seqNum
                << ", dest_slot=" << stuck_dest_slot
                << ", write_phys=" << written
                << ", stored_phys=" << masked
                << ", bit=" << stuck_bit << " forced to " << stuck_polarity
                << ", hamming="
                << __builtin_popcountll((uint64_t)written ^ (uint64_t)masked)
                << ", exposure: " << stuck_exposures
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSROB::checkStuckReadback(const o3::DynInstPtr &head_inst)
    {
        // Fires when the ARMED entry leaves the ROB (retireHead sees every
        // exit, including squashed retires). Reads the field back: the
        // "整个存活期间持续带着缺陷 / 被反复读取到同一个错误值"
        // evidence. If the bit is NOT at the polarity (the field was
        // rewritten by something), that is logged honestly too.
        if (head_inst->seqNum != stuck_sn) return;
        stuck_readback_done = true;
        if (fi_mode == Mode::PcStuck) {
            Addr pc = head_inst->pcState().as<ArmISA::PCState>().pc();
            int bitval = (int)((pc >> stuck_bit) & 1ULL);
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_retireHead_readback, mode=pc_stuck"
                    << ", sn=" << stuck_sn
                    << ", readback_pc=0x" << std::hex << pc << std::dec
                    << ", bit=" << stuck_bit
                    << " read=" << bitval
                    << ", polarity=" << stuck_polarity
                    << (bitval == stuck_polarity
                            ? " (STILL STUCK at retire — defect persisted"
                              " the entry's whole ROB lifetime)"
                            : " (bit NOT at polarity — field was rewritten)")
                    << ", exposures: " << stuck_exposures
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return;
        }
        // DestIdStuck
        if (stuck_dest_slot < 0
                || stuck_dest_slot >= (int)head_inst->numDestRegs()) {
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_retireHead_readback, mode=destid_stuck"
                    << ", sn=" << stuck_sn
                    << " — no int dest slot recorded (no field to read back)"
                    << ", exposures: " << stuck_exposures
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return;
        }
        PhysRegIdPtr d = head_inst->renamedDestIdx(stuck_dest_slot);
        if (!d || d->classValue() != IntRegClass) {
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_retireHead_readback, mode=destid_stuck"
                    << ", sn=" << stuck_sn
                    << " — dest slot no longer an int reg (cannot read back)"
                    << ", exposures: " << stuck_exposures
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return;
        }
        int idx = d->index();
        int bitval = (idx >> stuck_bit) & 1;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: rob_retireHead_readback, mode=destid_stuck"
                << ", sn=" << stuck_sn
                << ", readback_phys=" << idx
                << ", bit=" << stuck_bit
                << " read=" << bitval
                << ", polarity=" << stuck_polarity
                << (bitval == stuck_polarity
                        ? " (STILL STUCK at retire — defect persisted the"
                          " entry's whole ROB lifetime)"
                        : " (bit NOT at polarity — field was rewritten)")
                << ", exposures: " << stuck_exposures
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
    }

    void
    CHAOSROB::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSROB: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        o3cpu->o3ROB().setChaosROB(this);
    }

} // namespace gem5
