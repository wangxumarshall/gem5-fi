#include "cpu/o3/CHAOSIQ/CHAOSIQ.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/inst_queue.hh"   // InstructionQueue
#include "sim/core.hh"
#include "cpu/o3/dyn_inst.hh"     // DynInst
#include "cpu/o3/regfile.hh"      // PhysRegFile, intPhysRegId (W5.10-11)
#include "cpu/reg_class.hh"       // IntRegClass (W5.10-11)
#include "arch/arm/pcstate.hh"    // ArmISA::PCState (W5.10-11 log lines)
#include "debug/CHAOSIQ.hh"
#include "sim/sim_exit.hh"
#include "params/CHAOSIQ.hh"

namespace gem5
{

    CHAOSIQ::CHAOSIQ(const CHAOSIQParams &p)
        : SimObject(p),
          cpu(p.cpu),
          fi_mode(stringToMode(p.mode)),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          phase_offset(p.phaseOffset),
          fault_mask(p.faultMask),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("iq_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSIQ: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            // v1.1 Phase 8.2: fixed uniform skip (driver-provided,
            // chaos_event_sample.hh) overrides the legacy geometric(0.1)
            // draw; UINT64_MAX sentinel keeps legacy behavior.
            if (p.eventsToSkip != ~0ULL)
                events_to_skip = p.eventsToSkip;
            else {
                std::geometric_distribution<uint64_t> skip_dist(0.1);
                events_to_skip = skip_dist(rng);
            }
            count_only = p.countOnly;
        }
    }

    CHAOSIQ::~CHAOSIQ()
    {
        // v1.1 Phase 8.2 countOnlyMode: the driver's dry-run learns
        // N_eligible from this line (campaign.py parses the log).
        if (count_only && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT=" << eligible_count
                << std::endl;
        }
    }

    CHAOSIQ::Mode
    CHAOSIQ::stringToMode(const std::string &s) {
        if (s == "src_ready_bitflip") return Mode::SrcReadyBitflip;
        if (s == "wake_phase") return Mode::WakePhase;
        // W5.10-W5.12 (ooo 04-design-matrix D47-D55, Int Dispatch/ROB):
        // the Int-IQ entry's ready bit (D47-D49), its source-tag field
        // (D50-D54) and the dispatch-port FU-class misroute (D55).
        if (s == "ready_early") return Mode::ReadyEarly;
        if (s == "ready_never") return Mode::ReadyNever;
        if (s == "ready_never_event") return Mode::ReadyNeverEvent;
        if (s == "tag_swap") return Mode::TagSwap;
        if (s == "tag_bitflip") return Mode::TagBitflip;
        if (s == "tag_bitflip2") return Mode::TagBitflip2;
        if (s == "tag_stuck") return Mode::TagStuck;
        if (s == "tag_stale_read") return Mode::TagStaleRead;
        if (s == "dispatch_misroute") return Mode::DispatchMisroute;
        return Mode::WakeOmit;  // default / unknown
    }

    bool
    CHAOSIQ::inWindow() {
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

    bool
    CHAOSIQ::shouldOmitWake(ThreadID tid, const o3::DynInstPtr &completed_inst)
    {
        if (fi_mode != Mode::WakeOmit) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible wakeup events (N ~ geometric(0.1) from the seed).
        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // §2.5 wake_omit (F6): drop this wakeup broadcast. Dependents of the
        // completed inst stay not-ready (one missed wake) — models method3
        // timing-race phase shift / dropped-wake fault.
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode=wake_omit, tid=" << (int)tid
                << ", completed_sn=" << completed_inst->seqNum
                << ", phase_offset=" << phase_offset
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;  // caller skips the wakeup broadcast
    }

    bool
    CHAOSIQ::shouldWrongSourceWake(ThreadID tid,
                                   const o3::DynInstPtr &completed_inst)
    {
        // §2.5 F5 src_ready_bitflip: gate ONLY. The dependency-graph surgery
        // (pop a not-ready dependent from a different chain, markSrcRegReady,
        // addIfReady) lives in InstructionQueue::wakeDependents — it owns
        // dependGraph/addIfReady/scoreboard and we don't want to expose them.
        if (fi_mode != Mode::SrcReadyBitflip) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!completed_inst) return false;

        // sampling-bias fix: skip on eligible completed-inst events
        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) { --events_to_skip; return false; }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode=src_ready_bitflip"
                << ", tid=" << (int)tid
                << ", completed_sn=" << completed_inst->seqNum
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    bool
    CHAOSIQ::shouldDelayWake(ThreadID tid, const o3::DynInstPtr &completed_inst)
    {
        // §2.5 F6 wake_phase: gate. The caller (InstructionQueue) skips this
        // broadcast now and re-issues it after |phase_offset| cycles via its
        // own scheduled event. phase_offset <= 0 is a config error for this
        // mode (advance = wake in the past = no-op; documented E3 limit).
        if (fi_mode != Mode::WakePhase) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (phase_offset <= 0) return false;  // delay only; advance not modeled
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!completed_inst) return false;

        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) { --events_to_skip; return false; }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode=wake_phase"
                << ", tid=" << (int)tid
                << ", completed_sn=" << completed_inst->seqNum
                << ", phase_offset=+" << phase_offset
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    // ------------------------------------------------------------------
    // W5.10-W5.12 (ooo 04-design-matrix D47-D55, Int Dispatch/ROB)

    bool
    CHAOSIQ::gateEligible()
    {
        // Shared per-event gate for the W5 insert/wake/issue-site hooks:
        // window + max_faults + the events_to_skip sampling discipline +
        // the probability draw (the existing CHAOSIQ house style).
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;
        if (!inWindow()) return false;
        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) { --events_to_skip; return false; }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;
        return true;
    }

    int
    CHAOSIQ::collectIntSrcSlots(const o3::DynInstPtr &inst,
                                std::vector<int> &slots)
    {
        // Int-IQ scope (W5.10-11): the tag/ready fields live on INT-class
        // source slots; FP/vector sources belong to the W7 FP units.
        slots.clear();
        for (int i = 0; i < (int)inst->numSrcRegs(); i++) {
            PhysRegIdPtr s = inst->renamedSrcIdx(i);
            if (!s) continue;
            if (s->classValue() != IntRegClass) continue;
            slots.push_back(i);
        }
        return (int)slots.size();
    }

    bool
    CHAOSIQ::maybeCorruptTag(ThreadID tid, const o3::DynInstPtr &inst)
    {
        // W5.11 D50-D54 (ooo 04-design-matrix R51-R55): corrupt ONE
        // int-class source TAG of the IQ entry as it is written (the hook
        // sits in InstructionQueue::insert BEFORE addToDependents, so the
        // dependency graph, the scoreboard check and the issue-time
        // operand read — DynInst::getRegOperand reads renamedSrcIdx,
        // dyn_inst.hh — all follow the corrupted tag: the entry WAITS FOR
        // and READS the wrong physreg, the faithful CAM-tag-mismatch
        // realization; no IQ-internal surgery needed).
        if (fi_mode != Mode::TagSwap && fi_mode != Mode::TagBitflip
                && fi_mode != Mode::TagBitflip2 && fi_mode != Mode::TagStuck
                && fi_mode != Mode::TagStaleRead)
            return false;
        if (!cpu) return false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;
        // Int-IQ scope: FP/vector entries are not this unit's population.
        if (inst->isFloating() || inst->isVector()) return false;

        // bounded skip logging (an IQ insert fires per inst — a per-skip
        // line would flood the log)
        static thread_local uint64_t skip_logs = 0;

        // F5 tag_stuck: arming is the counted fault; the write-path mask
        // applies at the ARMED entry's single tag write (gem5 never
        // rewrites renamedSrcIdx while the entry is IQ-resident —
        // persistence = value permanence; noteTagWake logs the
        // wrong-chain consumption evidence).
        if (fi_mode == Mode::TagStuck) {
            if (!tag_stuck_armed) {
                std::vector<int> slots;
                int n = collectIntSrcSlots(inst, slots);
                if (n == 0) return false;   // arm on an entry WITH the field
                if (!gateEligible()) return false;
                int num_phys =
                    (int)o3cpu->physRegFile().numIntPhysRegs();
                int nbits = 0; int tmp = num_phys;
                while (tmp > 1) { nbits++; tmp >>= 1; }
                if (nbits < 1) nbits = 1;
                tag_stuck_bit = fault_mask
                    ? (int)__builtin_ctzll(fault_mask) % nbits
                    : (int)(rng() % (unsigned)nbits);
                tag_stuck_polarity = (int)(rng() % 2);
                tag_stuck_slot = slots[(int)(rng() % (unsigned)n)];
                tag_stuck_sn = inst->seqNum;
                tag_stuck_armed = true;
                tag_stuck_wakes = 0;
                faults_injected_count++;
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: iq_insert, mode=tag_stuck, ARMED"
                        << ", tid=" << (int)tid
                        << ", sn=" << tag_stuck_sn
                        << ", src_slot=" << tag_stuck_slot
                        << ", bit=" << tag_stuck_bit
                        << ", polarity=" << tag_stuck_polarity
                        << (tag_stuck_polarity ? " (stuck_at_one)"
                                               : " (stuck_at_zero)")
                        << ", write_path=iq_insert (the single write of an"
                           " entry's tag field — gem5 never rewrites"
                           " renamedSrcIdx while IQ-resident; persistence ="
                           " value permanence, wrong-chain consumption"
                           " logged at wake)"
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                // fall through: mask THIS entry's tag write now.
            }
            // The ARMED entry's single tag write gets the mask (for the
            // just-armed entry this IS that write; every later insert is
            // a different entry — no cell, no action).
            {
                if (inst->seqNum != tag_stuck_sn) return false;
                if (tag_stuck_slot >= (int)inst->numSrcRegs())
                    return false;
                PhysRegIdPtr cur = inst->renamedSrcIdx(tag_stuck_slot);
                if (!cur || cur->classValue() != IntRegClass)
                    return false;
                int written = cur->index();
                int num_phys =
                    (int)o3cpu->physRegFile().numIntPhysRegs();
                int masked = tag_stuck_polarity
                    ? (written | (1 << tag_stuck_bit))
                    : (written & ~(1 << tag_stuck_bit));
                if (masked == written) {
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Site: iq_insert, mode=tag_stuck"
                            << ", tid=" << (int)tid
                            << ", sn=" << inst->seqNum
                            << ", src_slot=" << tag_stuck_slot
                            << ", write_tag=" << written
                            << ", stored_tag=" << masked
                            << " (bit " << tag_stuck_bit << " already at "
                            << tag_stuck_polarity
                            << ", no observable change)"
                            << ", faults_injected: "
                            << faults_injected_count << std::endl;
                    }
                    return true;
                }
                if (masked < 0 || masked >= num_phys) {
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Site: iq_insert, mode=tag_stuck"
                            << ", tid=" << (int)tid
                            << ", sn=" << inst->seqNum
                            << ", src_slot=" << tag_stuck_slot
                            << ", write_tag=" << written
                            << " — forced idx " << masked << " out of [0,"
                            << num_phys << ") (skipped this write, no clamp)"
                            << ", faults_injected: "
                            << faults_injected_count << std::endl;
                    }
                    return false;
                }
                inst->renameSrcReg(tag_stuck_slot,
                    o3cpu->physRegFile().intPhysRegId(masked));
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: iq_insert, mode=tag_stuck"
                        << ", tid=" << (int)tid
                        << ", sn=" << inst->seqNum
                        << ", src_slot=" << tag_stuck_slot
                        << ", write_tag=" << written
                        << ", stored_tag=" << masked
                        << ", bit=" << tag_stuck_bit << " forced to "
                        << tag_stuck_polarity
                        << ", hamming="
                        << __builtin_popcountll((uint64_t)written
                                                ^ (uint64_t)masked)
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                return true;
            }
        }

        std::vector<int> slots;
        int n = collectIntSrcSlots(inst, slots);
        if (n == 0) {
            if (write_log && skip_logs < 32) {
                ++skip_logs;
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: iq_insert, tid=" << (int)tid
                    << ", sn=" << inst->seqNum
                    << " — entry has no int src tag (skipped, no field)"
                    << ", skip_log: " << skip_logs
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return false;
        }
        if (!gateEligible()) return false;

        int slot = slots[(int)(rng() % (unsigned)n)];
        PhysRegIdPtr cur = inst->renamedSrcIdx(slot);
        int cur_idx = cur->index();
        int num_phys = (int)o3cpu->physRegFile().numIntPhysRegs();
        if (num_phys <= 1) return false;

        if (fi_mode == Mode::TagStaleRead) {
            // D54 (R55): at the slot-overwrite instant the tag write
            // silently FAILS — the slot retains the PREVIOUS occupant's
            // tag; the entry waits for / reads a long-retired, unrelated
            // physreg ("旧 tag 大概率仍指向一个存在的、有真实数据的
            // 物理寄存器"). HONEST APPROXIMATION: gem5's IQ has no slot
            // array — the previous occupant = the newest issue-time
            // departure (noteIqDeparture ring) with an int-class tag at
            // the SAME slot index.
            PhysRegIdPtr stale_tag;
            uint64_t prev_sn = 0;
            for (auto it = tag_departed.rbegin();
                    it != tag_departed.rend(); ++it) {
                if ((*it)->seqNum == inst->seqNum) continue;
                if (slot >= (int)(*it)->numSrcRegs()) continue;
                PhysRegIdPtr s = (*it)->renamedSrcIdx(slot);
                if (!s || s->classValue() != IntRegClass) continue;
                stale_tag = s;
                prev_sn = (*it)->seqNum;
                break;
            }
            if (!stale_tag || stale_tag->index() == cur_idx) {
                if (write_log && skip_logs < 32) {
                    ++skip_logs;
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: iq_insert, mode=tag_stale_read"
                        << ", tid=" << (int)tid
                        << ", sn=" << inst->seqNum
                        << ", src_slot=" << slot
                        << ", true_tag=" << cur_idx
                        << " — no departed occupant with an int tag at"
                           " this slot in the ring (skipped, no injection)"
                        << ", skip_log: " << skip_logs
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                return false;
            }
            inst->renameSrcReg(slot, stale_tag);
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: iq_insert, mode=tag_stale_read"
                    << ", tid=" << (int)tid
                    << ", sn=" << inst->seqNum
                    << ", src_slot=" << slot
                    << ", true_tag=" << cur_idx
                    << " (this slot's tag write SILENTLY FAILED)"
                    << ", stale_tag=" << stale_tag->index()
                    << ", previous_occupant_sn=" << prev_sn
                    << ", approx=prev_issue_departure_same_slot (gem5 IQ"
                       " has no slot array — previous occupant = newest"
                       " issue-time departure with an int tag at the same"
                       " slot index, the D40 stale_departure pattern)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }

        int new_idx = -1;
        int log_b1 = -1, log_b2 = -1;
        if (fi_mode == Mode::TagSwap) {
            // D50 (R51): 换值 — the waiting tag becomes ANOTHER int
            // physreg number (random legal id, the RAT-A setEntry
            // semantics). The new tag may be in-flight (wrong producer
            // wait) or already-written (immediate stale read) — both the
            // designed behaviors.
            do {
                new_idx = (int)(rng() % (unsigned)num_phys);
            } while (new_idx == cur_idx);
        } else {
            // D51/D52: 1 / 2 distinct random bits of the int tag index
            // (the destid_bitflip domain policy: bits of the INT tag
            // field, out-of-range = honest skip, never clamped).
            int nbits = 0; int tmp = num_phys;
            while (tmp > 1) { nbits++; tmp >>= 1; }
            if (nbits < 1) nbits = 1;
            if (fi_mode == Mode::TagBitflip) {
                int bit = fault_mask
                    ? (int)__builtin_ctzll(fault_mask) % nbits
                    : (int)(rng() % (unsigned)nbits);
                new_idx = cur_idx ^ (1 << bit);
                log_b1 = bit;
            } else {
                if (nbits < 2) return false;
                int b1 = 0, b2 = 0;
                if (__builtin_popcountll(fault_mask) >= 2) {
                    b1 = (int)__builtin_ctzll(fault_mask);
                    uint64_t rest = fault_mask & ~(1ULL << b1);
                    b2 = (int)__builtin_ctzll(rest);
                } else {
                    b1 = (int)(rng() % (unsigned)nbits);
                    b2 = (int)(rng() % (unsigned)(nbits - 1));
                    if (b2 >= b1) b2++;
                }
                if (b1 == b2 || b1 >= nbits || b2 >= nbits) return false;
                new_idx = cur_idx ^ (1 << b1) ^ (1 << b2);
                log_b1 = b1; log_b2 = b2;
            }
            if (new_idx < 0 || new_idx >= num_phys) {
                if (write_log && skip_logs < 32) {
                    ++skip_logs;
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: iq_insert, mode="
                        << (fi_mode == Mode::TagBitflip
                                ? "tag_bitflip" : "tag_bitflip2")
                        << ", tid=" << (int)tid
                        << ", sn=" << inst->seqNum
                        << ", old_tag=" << cur_idx
                        << " — flipped idx " << new_idx << " out of [0,"
                        << num_phys << ") (skipped, no clamp)"
                        << ", skip_log: " << skip_logs
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                return false;
            }
        }
        if (new_idx < 0 || new_idx == cur_idx || new_idx >= num_phys)
            return false;

        inst->renameSrcReg(slot,
            o3cpu->physRegFile().intPhysRegId(new_idx));
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_insert, mode="
                << (fi_mode == Mode::TagSwap ? "tag_swap"
                    : fi_mode == Mode::TagBitflip ? "tag_bitflip"
                    : "tag_bitflip2")
                << ", tid=" << (int)tid
                << ", sn=" << inst->seqNum
                << ", src_slot=" << slot
                << ", old_tag=" << cur_idx
                << ", new_tag=" << new_idx;
            if (fi_mode == Mode::TagBitflip || fi_mode == Mode::TagBitflip2) {
                *(log_stream->stream()) << ", bits=(" << log_b1;
                if (fi_mode == Mode::TagBitflip2)
                    *(log_stream->stream()) << "," << log_b2;
                *(log_stream->stream()) << ")"
                    << ", hamming="
                    << __builtin_popcountll((uint64_t)cur_idx
                                            ^ (uint64_t)new_idx);
            }
            *(log_stream->stream())
                << " (dependency wait AND operand read both follow the"
                   " corrupted tag — getRegOperand reads renamedSrcIdx)"
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSIQ::maybeReadyEarly(ThreadID tid, const o3::DynInstPtr &inst)
    {
        // W5.10 D47 (ooo 04-design-matrix R48, ready位·提前置位): force
        // ONE not-yet-ready int-class source slot's ready bit at IQ entry
        // — the entry lies about its operand availability. The hook sits
        // BEFORE addToDependents: the per-slot bit keeps the entry OFF
        // that slot's dependency chain (no later wake can re-mark it —
        // the scheduleReadyInsts assert(iq) double-issue artifact is
        // impossible), while the incremented counter lets a
        // last-unready-slot entry reach the normal addIfReady at the end
        // of insert() THIS cycle — it issues and reads the physreg BEFORE
        // the producer's writeback lands (stale-PRF-value silent-SDC
        // family, same value source as the verified done_early /
        // src_ready_bitflip modes).
        if (fi_mode != Mode::ReadyEarly) return;
        if (!cpu) return;
        if (inst->isFloating() || inst->isVector()) return;

        std::vector<int> slots;
        int n = collectIntSrcSlots(inst, slots);
        if (n == 0) return;
        // only slots that are NOT ready yet (the lie has content)
        std::vector<int> unready;
        for (int i = 0; i < n; i++)
            if (!inst->readySrcIdx(slots[i])) unready.push_back(slots[i]);
        if (unready.empty()) return;   // fully ready already — nothing to lie about
        if (!gateEligible()) return;

        int slot = unready[(int)(rng() % (unsigned)unready.size())];
        int src_phys = inst->renamedSrcIdx(slot)->index();
        int old_ready = (int)inst->readyRegs;
        inst->markSrcRegReady(slot);   // per-slot bit + counter (+CanIssue)
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_insert, mode=ready_early"
                << ", tid=" << (int)tid
                << ", sn=" << inst->seqNum
                << ", pc=0x" << std::hex
                << inst->pcState().as<ArmISA::PCState>().pc() << std::dec
                << ", src_slot=" << slot
                << ", src_phys=" << src_phys
                << ", ready_regs " << old_ready << " -> "
                << (int)inst->readyRegs << " / "
                << (int)inst->numSrcRegs()
                << (inst->readyToIssue()
                        ? " (entry became issueable NOW — it will read the"
                          " physreg cell BEFORE the producer's writeback:"
                          " stale value, the 状态位撒谎 silent-SDC path)"
                        : " (one wake short — will issue one wake EARLY)")
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
    }

    bool
    CHAOSIQ::shouldSuppressReadyMark(const o3::DynInstPtr &dep_inst,
                                     RegIndex producer_flat,
                                     unsigned iq_used, unsigned iq_cap)
    {
        // W5.10 D48/D49 (R49/R50, ready位·永不置位): the operand IS ready
        // (its producer completed — this wake carries the value's
        // availability) but the ready bit never sets: SUPPRESS this
        // markSrcRegReady. The pop already consumed the entry's only wake
        // for that slot, so the entry's readyRegs can never reach
        // numSrcRegs — it sits in the IQ forever, the in-order ROB head
        // blocks on it, the ROB/IQ fill (resource-exhaustion Timeout,
        // the free-list-leak family). D49 fires only when the IQ is
        // >80% full (iq_used*5 > iq_cap*4, the "约 51/64 项" gate).
        if (fi_mode != Mode::ReadyNever && fi_mode != Mode::ReadyNeverEvent)
            return false;
        if (!dep_inst || dep_inst->isSquashed()) return false;
        if (dep_inst->isFloating() || dep_inst->isVector()) return false;
        if (fi_mode == Mode::ReadyNeverEvent) {
            if (iq_cap == 0) return false;
            if (!((uint64_t)iq_used * 5 > (uint64_t)iq_cap * 4))
                return false;
        }
        if (!gateEligible()) return false;

        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode="
                << (fi_mode == Mode::ReadyNever
                        ? "ready_never" : "ready_never_event")
                << ", tid=" << (int)dep_inst->threadNumber
                << ", sn=" << dep_inst->seqNum
                << ", pc=0x" << std::hex
                << dep_inst->pcState().as<ArmISA::PCState>().pc()
                << std::dec
                << ", producer_flat=" << (unsigned)producer_flat
                << ", markSrcRegReady SUPPRESSED (ready_regs stays "
                << (int)dep_inst->readyRegs << " / "
                << (int)dep_inst->numSrcRegs()
                << " — the wake was consumed; this entry is permanently"
                   " never-ready: it wedges the IQ/ROB -> Timeout)"
                << ", iq_occupancy=" << iq_used << "/" << iq_cap
                << (fi_mode == Mode::ReadyNeverEvent
                        ? " (event gate IQ>80% satisfied)" : "")
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSIQ::noteTagWake(const o3::DynInstPtr &dep_inst,
                         RegIndex chain_flat)
    {
        // D53 tag_stuck persistence evidence: the ARMED entry was woken
        // through a chain — its corrupted tag actually matched a
        // producer's broadcast ("该 IQ 项占用期间是否反复触发同一种
        // tag 匹配偏差"). Zero cost unless tag_stuck is armed.
        if (fi_mode != Mode::TagStuck || !tag_stuck_armed) return;
        if (!dep_inst || dep_inst->seqNum != tag_stuck_sn) return;
        tag_stuck_wakes++;
        if (write_log && tag_stuck_wakes <= 10) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode=tag_stuck"
                << ", STUCK_TAG_CONSUMED: armed entry sn=" << tag_stuck_sn
                << " woken via chain flat=" << (unsigned)chain_flat
                << " (the corrupted tag matched a producer broadcast)"
                << ", wrong_chain_wakes: " << tag_stuck_wakes
                << (tag_stuck_wakes == 10 ? " (logging capped)" : "")
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
    }

    void
    CHAOSIQ::noteIqDeparture(const o3::DynInstPtr &inst)
    {
        // D54 previous-occupant ring: record issue-time IQ departures
        // (the non-mem clearInIQ site). Only maintained in tag_stale_read
        // runs — zero cost otherwise.
        if (fi_mode != Mode::TagStaleRead) return;
        tag_departed.push_back(inst);
        if (tag_departed.size() > 64)   // IQ capacity bound
            tag_departed.pop_front();
    }

    void
    CHAOSIQ::maybeMisrouteFU(const o3::DynInstPtr &issuing_inst,
                             OpClass &fu_class)
    {
        // W5.12 D55 (ooo 04-design-matrix R56, 分发端口选择逻辑·状态
        // 翻转): swap the FU-selection class between IntAlu and IntMult
        // (the design's binary ALU-vs-MDU judgment — 3 ALU + 1 MDU).
        // HONEST SCOPE (spike C, findings.md): the FU index only drives
        // latency / port / pipelining accounting — the executed VALUE
        // comes from inst->execute() (the StaticInst vtable, no FU
        // parameter) — so the misroute is a wrong-port / wrong-latency
        // effect with a CORRECT value. A semantically incompatible
        // target (the design's int-vs-float crash branch) has no gem5
        // realization: getUnit(FloatAdd) would happily hand out an FP
        // FU and the int op would still execute correctly, so that
        // branch is honestly NOT modeled (faking a NoCapableFU would be
        // inventing a crash gem5 cannot produce).
        if (fi_mode != Mode::DispatchMisroute) return;
        if (fu_class != IntAluOp && fu_class != IntMultOp) return;
        if (!gateEligible()) return;

        OpClass true_class = fu_class;
        fu_class = (true_class == IntAluOp) ? IntMultOp : IntAluOp;
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_scheduleReadyInsts, mode=dispatch_misroute"
                << ", tid=" << (int)issuing_inst->threadNumber
                << ", sn=" << issuing_inst->seqNum
                << ", pc=0x" << std::hex
                << issuing_inst->pcState().as<ArmISA::PCState>().pc()
                << std::dec
                << ", true_fu_class="
                << (true_class == IntAluOp ? "IntAlu" : "IntMult")
                << ", routed_fu_class="
                << (fu_class == IntAluOp ? "IntAlu" : "IntMult")
                << " (wrong port + wrong latency for this µop; the VALUE"
                   " is still computed correctly — spike C: gem5's FU pick"
                   " is latency/port accounting only, 探索性近似口径)"
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
    }

    void
    CHAOSIQ::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSIQ: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        // SELF-ATTACH: IEW.instQueue.chaosIQ = this.
        o3cpu->o3IEW().instQueue.setChaosIQ(this);
        // v1.1 Phase 8.2: print CHAOS_ELIGIBLE_COUNT at sim exit (the
        // destructor may not run before gem5's exit path tears everything
        // down; the exit callback always fires).
        if (count_only) {
            registerExitCallback([this]() {
                if (log_stream && log_stream->stream())
                    *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT="
                        << eligible_count << std::endl;
            });
        }
    }

} // namespace gem5
