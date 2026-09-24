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
        // W5.4 (D32-D35): the done/completed (CanCommit) status bit,
        // hooked at Commit::markCompletedInsts (commit.cc).
        if (s == "done_early") return Mode::DoneEarly;
        if (s == "done_early_event") return Mode::DoneEarlyEvent;
        if (s == "done_delay") return Mode::DoneDelay;
        if (s == "done_delay_event") return Mode::DoneDelayEvent;
        // W5.6 (D40): whole-record stale read at the insert site.
        if (s == "rob_stale_read") return Mode::RobStaleRead;
        // W5.6 (D36-D39): oldphys_* mount through --rob_mode but live in
        // CHAOSRenameMap (ooo_proxy routes them); CHAOSROB stays INERT —
        // never fall back to entry_bitflip for a mode it does not own.
        if (s == "oldphys_bitflip" || s == "oldphys_bitflip2"
                || s == "oldphys_swap_active" || s == "oldphys_stuck")
            return Mode::OldphysInert;
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
            case Mode::DoneEarly: return "done_early";
            case Mode::DoneEarlyEvent: return "done_early_event";
            case Mode::DoneDelay: return "done_delay";
            case Mode::DoneDelayEvent: return "done_delay_event";
            case Mode::RobStaleRead: return "rob_stale_read";
            case Mode::OldphysInert: return "oldphys_inert";
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
        // W5.6 D40 rob_stale_read: (a) capture EVERY retireHead departure
        // into the bounded ring (the "previous occupant" pool — at full
        // occupancy the head departure frees exactly the slot the tail is
        // about to write; retireHead is the commit path, so every captured
        // record is an "早已提交" fully-processed record, exactly the D40
        // population); (b) when the entry whose record was staled reaches
        // commit, emit the STALE_RECORD_COMMITTED evidence line — commit
        // read the OLD record's PC/dest-ids, the "commit 阶段读到已经
        // 提交过的旧记录" proof.
        if (fi_mode == Mode::RobStaleRead) {
            if (stale_read_armed && !stale_read_committed_logged
                    && head_inst->seqNum == stale_read_new_sn) {
                stale_read_committed_logged = true;
                if (write_log && log_stream) {
                    Addr pc = head_inst->pcState()
                                    .as<ArmISA::PCState>().pc();
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rob_retireHead, mode=rob_stale_read"
                        << ", STALE_RECORD_COMMITTED: commit read the"
                        << " previous occupant's record at new sn="
                        << stale_read_new_sn
                        << ", read_pc=0x" << std::hex << pc << std::dec
                        << " (== stale_pc 0x" << std::hex << stale_read_stale_pc
                        << std::dec << ", old record sn=" << stale_read_old_sn
                        << "; the new inst's true pc was 0x" << std::hex
                        << stale_read_true_pc << std::dec << ")"
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
            }
            // keep the departed DynInst alive + readable (record source)
            stale_departed.push_back(head_inst);
            if (stale_departed.size() > 128)  // ROB capacity bound
                stale_departed.pop_front();
        }

        // W5.2 stuck read-back (D27/D31 "该 ROB 项在整个存活期间是否被
        // 反复读取到同一个错误值" persistence evidence): when the ARMED
        // entry leaves the ROB, read its field back and verify the stuck
        // bit is still at the forced polarity. One line per armed entry.
        if ((fi_mode == Mode::PcStuck || fi_mode == Mode::DestIdStuck)
                && stuck_armed && !stuck_readback_done)
            checkStuckReadback(head_inst);

        if (fi_mode == Mode::DoneEarly || fi_mode == Mode::DoneEarlyEvent
                || fi_mode == Mode::DoneDelay || fi_mode == Mode::DoneDelayEvent
                || fi_mode == Mode::RobStaleRead
                || fi_mode == Mode::OldphysInert)
            return false;  // done-bit modes live on the markCompletedInsts
                           // hook; rob_stale_read on the insert hook;
                           // oldphys_* live in CHAOSRenameMap — all no-ops
                           // at the retireHead site.

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

        // W5.4 done-bit modes: no insert-site action (they hook
        // Commit::markCompletedInsts). W5.6 oldphys_* live in
        // CHAOSRenameMap (mounted via --rob_mode; this object is inert).
        if (fi_mode == Mode::DoneEarly || fi_mode == Mode::DoneEarlyEvent
                || fi_mode == Mode::DoneDelay || fi_mode == Mode::DoneDelayEvent
                || fi_mode == Mode::OldphysInert)
            return false;

        // W5.6 D40 rob_stale_read: the insert-site whole-record stale
        // overwrite (before the generic gates — it has its own gates).
        if (fi_mode == Mode::RobStaleRead)
            return maybeStaleReadEntry(tid, inst);

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

    bool
    CHAOSROB::robAbove80Pct(o3::CPU *o3cpu, ThreadID tid)
    {
        // D33/D35 event gate: "ROB 占用超过 80%（约 102/128 项）" — the
        // design fixes the threshold at 80% of the thread's ROB capacity.
        // Integer 4/5 compare (countInsts*5 > maxEntries*4).
        o3::ROB &rob = o3cpu->o3ROB();
        unsigned max_e = rob.getMaxEntries(tid);
        if (max_e == 0) return false;
        return (uint64_t)rob.countInsts(tid) * 5 > (uint64_t)max_e * 4;
    }

    bool
    CHAOSROB::doneBitExcluded(const o3::DynInstPtr &inst, bool early)
    {
        // Shared exclusion list for the done-bit family.
        //
        // done_delay: the self-healing classes are excluded — barriers /
        // non-speculative / store-conditionals / strictly-ordered loads go
        // through commitHead's nonSpecSeqNum re-execution path, whose
        // completion arrives through fromIEW a SECOND time, so skipping
        // the first setCanCommit would not be the "never marked done"
        // model (it would silently self-heal).
        //
        // done_early additionally excludes stores/atomics (committing a
        // store that never executed breaks the SQ writeback ordering the
        // IEW store-drain path relies on) and control transfers (a branch
        // committed before it resolves interacts with the mispredict
        // squash machinery) — v1 keeps plain ALU ops and plain loads,
        // the stale-PRF-value population of spike A. Honest scoping: an
        // explicitly narrowed fault domain, extendable at W8 if the
        // branch/store families are needed.
        if (inst->isNonSpeculative() || inst->isStoreConditional()
                || inst->isReadBarrier() || inst->isWriteBarrier()
                || (inst->isLoad() && inst->strictlyOrdered()))
            return true;
        if (!early) return false;          // delay keeps stores/branches
        if (inst->isStore() || inst->isAtomic() || inst->isControl())
            return true;
        return false;
    }

    bool
    CHAOSROB::maybeDelayDoneBit(const o3::DynInstPtr &inst)
    {
        // W5.4 D34 done_delay / D35 done_delay_event (ooo 04-design-matrix
        // R35/R36, done位·延迟置位). The setCanCommit in
        // Commit::markCompletedInsts (commit.cc) is the ONLY regular site
        // that ever sets the done bit; fromIEW carries each completion for
        // exactly one cycle, so a skip here is permanent — the entry sits
        // in the ROB with done=0 forever, the in-order commit head blocks,
        // the ROB fills and the machine wedges (design expectation:
        // Timeout-dominant, the free-list-leak resource-exhaustion
        // family; the ROB-occupancy curve is the early-warning signal).
        if (fi_mode != Mode::DoneDelay && fi_mode != Mode::DoneDelayEvent)
            return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;
        if (!inWindow()) return false;
        ThreadID tid = inst->threadNumber;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        // self-healing classes: see doneBitExcluded
        if (doneBitExcluded(inst, /*early=*/false)) return false;

        bool above80 = robAbove80Pct(o3cpu, tid);
        if (fi_mode == Mode::DoneDelayEvent && !above80) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // The write silently fails: done stays 0 for this entry.
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: commit_markCompletedInsts, mode="
                << modeToString(fi_mode)
                << ", tid=" << (int)tid
                << ", sn=" << inst->seqNum
                << ", pc=0x" << std::hex
                << inst->pcState().as<ArmISA::PCState>().pc() << std::dec
                << ", setCanCommit SKIPPED (done stays 0 — fromIEW is"
                   " one-shot, this entry never becomes committable)"
                << ", rob_occupancy=" << o3cpu->o3ROB().countInsts(tid)
                   << "/" << o3cpu->o3ROB().getMaxEntries(tid)
                << (fi_mode == Mode::DoneDelayEvent
                        ? above80 ? ", rob_above_80pct=1" : ""
                        : "")
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSROB::maybeEarlyDoneBit()
    {
        // W5.4 D32 done_early / D33 done_early_event (ooo 04-design-matrix
        // R33/R34, done位·提前置位): mark a NOT-yet-executed ROB-resident
        // entry done AHEAD of its real completion. setCanCommit alone
        // would panic at commitHead (commit.cc:1128-1134 asserts an
        // un-executed head must be non-speculative/barrier/...) — the
        // paired setExecuted() is what makes the early commit flow
        // through, and the architectural value the committed dest
        // physRegFile cell carries is then its PREVIOUS OCCUPANT's
        // residue (spike A) — the "合法但结果错" silent-SDC path the
        // design expects to dominate this cell. The instruction's real
        // execution still happens later (IQ issue is untouched); its
        // late writeback may or may not race the consumers that already
        // read the stale cell — timing-dependent SDC, honestly reported.
        if (fi_mode != Mode::DoneEarly && fi_mode != Mode::DoneEarlyEvent)
            return;
        if (!cpu || probability <= 0.0f) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        if (!inWindow()) return;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return;

        bool any_above80 = false;
        o3::ROB &rob = o3cpu->o3ROB();
        // collect candidates across threads: ROB-resident, done still
        // clear, execution NOT finished, not in the excluded classes.
        std::vector<o3::DynInstPtr> cands;
        ThreadID hit_tid = 0;
        for (ThreadID t = 0; t < cpu->numThreads; t++) {
            bool above80 = robAbove80Pct(o3cpu, t);
            any_above80 = any_above80 || above80;
            if (fi_mode == Mode::DoneEarlyEvent && !above80) continue;
            for (int d = 0; ; d++) {
                o3::DynInstPtr ri = rob.getEntryAtDistance(t, d);
                if (!ri) break;  // past tail / empty
                if (ri->readyToCommit() || ri->isSquashed()) continue;
                if (ri->isExecuted()) continue;  // model: not yet finished
                // MUST have passed the IEW dispatch point: an inst still
                // in the rename->IEW skid buffer (IQ-full backpressure)
                // hits iew.cc:1064's assert(!inst->isExecuted()) when it
                // is finally dispatched into the IQ. isInIQ() = IQ-
                // resident; isIssued() = issued/in-flight (both clear of
                // the dispatch assert). Directed-run verified: without
                // this guard tick-795795 aborted on exactly that assert.
                if (!ri->isInIQ() && !ri->isIssued()) continue;
                if (doneBitExcluded(ri, /*early=*/true)) continue;
                cands.push_back(ri);
            }
        }
        if (fi_mode == Mode::DoneEarlyEvent && !any_above80) return;
        if (cands.empty()) return;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return;

        o3::DynInstPtr target = cands[(int)(rng() % (unsigned)cands.size())];
        hit_tid = target->threadNumber;
        Addr tpc = target->pcState().as<ArmISA::PCState>().pc();
        // The forced early done: BOTH status bits (the assert bypass).
        target->setExecuted();
        target->setCanCommit();
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: commit_markCompletedInsts, mode="
                << modeToString(fi_mode)
                << ", tid=" << (int)hit_tid
                << ", target_sn=" << target->seqNum
                << ", target_pc=0x" << std::hex << tpc << std::dec
                << ", forced done=1 AND executed=1 (setExecuted bypasses"
                   " the commit.cc:1128 un-executed-head assert)"
                << ", dest_phys=";
            bool first = true;
            for (int i = 0; i < (int)target->numDestRegs(); i++) {
                PhysRegIdPtr d = target->renamedDestIdx(i);
                if (!d) continue;
                if (!first) *(log_stream->stream()) << ",";
                *(log_stream->stream()) << d->index();
                first = false;
            }
            *(log_stream->stream())
                << " (PRF cells still hold the previous occupant's value"
                   " — silent-SDC potential, spike A)"
                << ", rob_occupancy=" << rob.countInsts(hit_tid)
                   << "/" << rob.getMaxEntries(hit_tid)
                << ", candidates=" << cands.size()
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
    }

    bool
    CHAOSROB::maybeStaleReadEntry(ThreadID tid, const o3::DynInstPtr &inst)
    {
        // W5.6 D40 rob_stale_read (ooo 04-design-matrix R41, ROB项整体·
        // 读到旧数据, 错位拼接): at the instant the ROB slot is written by
        // a newly dispatched instruction, that write silently fails — the
        // slot retains the PREVIOUS occupant's complete record and commit
        // later reads it ("已经被正确处理过的合法数据，不触发任何依赖
        // 检查失败" — the mechanism designed to bypass the TC'23-style
        // dependency check without constructing a swap target).
        //
        // gem5 realization (honest approximation, documented): gem5's ROB
        // is a std::list<DynInstPtr> — there is no physical slot array
        // whose cells could retain old data. The entry IS the DynInst, so
        // "the slot keeps the old record" is realized by overwriting the
        // new entry's RECORD fields (pcState, flattened dest ids, renamed
        // dest ids, prev dest ids) with the previous occupant's values at
        // insert time — the same maybeCorruptEntry mutation pattern the
        // D25-D31 modes use. Identity (seqNum/status/IQ-LSQ membership)
        // stays the new instruction's, so the entry commits exactly once,
        // with the OLD record's contents: the commit-map setEntry loop
        // re-applies the previous occupant's (arch, phys) pairs (stale
        // rollback) and the new instruction's own mapping never lands.
        // The "previous occupant" = the most recently retired instruction
        // with a matching dest count (at full occupancy the head departure
        // frees exactly the slot the tail writes; the record-shape match
        // keeps the copy total, no truncation).
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;
        if (!inWindow()) return false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // previous occupant: newest departure with the same dest count
        // (bounded scan of the ring; the ring only holds committed,
        // fully-processed records — the D40 population).
        static thread_local uint64_t skip_logs = 0;
        o3::DynInstPtr old;
        for (auto it = stale_departed.rbegin(); it != stale_departed.rend();
                ++it) {
            if ((*it)->seqNum == inst->seqNum) continue;
            if ((*it)->numDestRegs() == inst->numDestRegs()) { old = *it; break; }
        }
        if (!old) {
            if (write_log && skip_logs < 32) {
                ++skip_logs;
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_insert, mode=rob_stale_read"
                    << ", tid=" << (int)tid
                    << ", sn=" << inst->seqNum
                    << " — no departed record with matching dest count"
                       " in the ring (skipped, no injection)"
                    << ", skip_log: " << skip_logs
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return false;
        }

        // The write silently fails: restore the old record's fields.
        Addr true_pc = inst->pcState().as<ArmISA::PCState>().pc();
        ArmISA::PCState old_ns =
            old->pcState().as<ArmISA::PCState>();
        inst->pcState(old_ns);
        for (int i = 0; i < (int)inst->numDestRegs(); i++) {
            inst->flattenedDestIdx(i, old->flattenedDestIdx(i));
            inst->renameDestReg(i, old->renamedDestIdx(i),
                                old->prevDestIdx(i));
        }
        stale_read_armed = true;
        stale_read_committed_logged = false;
        stale_read_new_sn = inst->seqNum;
        stale_read_true_pc = true_pc;
        stale_read_stale_pc = old_ns.pc();
        stale_read_old_sn = old->seqNum;
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: rob_insert, mode=rob_stale_read"
                << ", tid=" << (int)tid
                << ", new_sn=" << inst->seqNum
                << ", true_pc=0x" << std::hex << true_pc << std::dec
                << " (this entry's record write SILENTLY FAILED)"
                << ", stale_record_sn=" << old->seqNum
                << ", stale_pc=0x" << std::hex << stale_read_stale_pc
                << std::dec
                << ", stale_dests=";
            bool first = true;
            for (int i = 0; i < (int)old->numDestRegs(); i++) {
                PhysRegIdPtr d = old->renamedDestIdx(i);
                if (!d) continue;
                if (!first) *(log_stream->stream()) << ",";
                *(log_stream->stream()) << d->index();
                first = false;
            }
            *(log_stream->stream())
                << " (previous occupant's record retained; commit reads it"
                   " — STALE_RECORD_COMMITTED line at retire)"
                << ", rob_occupancy=" << o3cpu->o3ROB().countInsts(tid)
                   << "/" << o3cpu->o3ROB().getMaxEntries(tid)
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
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
        // W5.4 done-bit family (D32-D35): the same injector also hooks
        // Commit::markCompletedInsts (the setCanCommit site — the ONLY
        // regular place the done bit is ever set). The commit-side
        // pointer follows the §2.18 CHAOSRAS pattern (setChaosRAS).
        o3cpu->o3Commit().setChaosROB(this);
    }

} // namespace gem5
