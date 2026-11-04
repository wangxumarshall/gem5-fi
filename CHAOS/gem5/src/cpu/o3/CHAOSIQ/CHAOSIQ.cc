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
        // W7.4 (D86-D91): the register-class scope — "int" keeps the W5
        // Int-IQ modes byte-identical; "vec" extends the same modes to the
        // FP/SIMD queue (VecRegClass rename domain). Unknown values are a
        // config error (loud, never a silent int fallback).
        if (p.targetClass == "int") {
            target_reg_class = IntRegClass;
        } else if (p.targetClass == "vec") {
            target_reg_class = VecRegClass;
        } else {
            panic("CHAOSIQ: unknown targetClass '%s' (int|vec)\n",
                  p.targetClass);
        }
        fp_only = p.fpOnly;
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
        // Both dropping modes hook here: wake_omit drops the broadcast
        // outright; wake_phase drops it now and re-issues it later. FQ08-c:
        // wake_phase is owned by CHAOSIQ (see shouldDelayWake) so the caller's
        // unsafe o3::DelayedWakeEvent is never scheduled.
        const bool wake_omit = (fi_mode == Mode::WakeOmit);
        const bool wake_phase = (fi_mode == Mode::WakePhase);
        if (!wake_omit && !wake_phase) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!completed_inst) return false;
        // A delayed wake being re-issued must not fire a NEW injection.
        if (replaying_delayed_wake) return false;
        // W7.4 D86 fpOnly: restrict eligibility to FP/SIMD completed
        // instructions (the "FP/SIMD 队列版" scoping) — placed BEFORE the
        // skip counter / RNG draw so non-FP events stay invisible to the
        // sampling discipline.
        if (fp_only && !isFpOpClass(completed_inst->opClass())) return false;
        // F6 wake_phase: delay only; advance = wake in the past = no-op
        // (documented E3 proxy limit).
        if (wake_phase && phase_offset <= 0) return false;

        iq_counts.eligible++;
        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible wakeup events (N ~ geometric(0.1) from the seed).
        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        iq_counts.attempted++;

        if (wake_phase) {
            // FQ08-c: schedule CHAOSIQ's generation-checked delayed wake
            // instead of letting the caller schedule o3::DelayedWakeEvent.
            auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
            if (!o3cpu) return false;
            const chaos_iq_lifecycle::WakeStamp stamp =
                snapshotWakeStamp(o3cpu, completed_inst);
            cpu->schedule(new DelayedWake(this, completed_inst, stamp),
                          curTick() + (Tick)phase_offset * cpu->clockPeriod());
            dw_counts.scheduled++;
            iq_counts.applied++;
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: iq_wakeDependents, mode=wake_phase"
                    << ", tid=" << (int)tid
                    << ", completed_sn=" << completed_inst->seqNum
                    << ", phase_offset=+" << phase_offset
                    << ", delayed_event=scheduled (CHAOSIQ-owned, identity+"
                       "generation checked at fire)";
                if (fp_only)
                    *(log_stream->stream()) << ", fp_only=1, op_class="
                        << enums::OpClassStrings[
                            static_cast<int>(completed_inst->opClass())];
                *(log_stream->stream())
                    << ", eligible=" << iq_counts.eligible
                    << ", attempted=" << iq_counts.attempted
                    << ", applied=" << iq_counts.applied
                    << ", activated=" << iq_counts.activated
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;  // caller skips the broadcast; the event replays it
        }

        // §2.5 wake_omit (F6): drop this wakeup broadcast. Dependents of the
        // completed inst stay not-ready (one missed wake) — models method3
        // timing-race phase shift / dropped-wake fault.
        iq_counts.applied++;
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode=wake_omit, tid=" << (int)tid
                << ", completed_sn=" << completed_inst->seqNum
                << ", phase_offset=" << phase_offset;
            if (fp_only)
                *(log_stream->stream()) << ", fp_only=1, op_class="
                    << enums::OpClassStrings[
                        static_cast<int>(completed_inst->opClass())];
            *(log_stream->stream())
                << ", eligible=" << iq_counts.eligible
                << ", attempted=" << iq_counts.attempted
                << ", applied=" << iq_counts.applied
                << ", activated=" << iq_counts.activated
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;  // caller skips the wakeup broadcast
    }

    bool
    CHAOSIQ::shouldWrongSourceWake(ThreadID tid,
                                   const o3::DynInstPtr &completed_inst)
    {
        // §2.5 F5 src_ready_bitflip (FQ08-b): ATTEMPT gate only.
        //
        // The old implementation incremented faults_injected_count and wrote
        // the injection log HERE, before any victim existed: when the
        // completed inst had no dependent (or all were ineligible) the run
        // reported an injection that never happened and the max_faults budget
        // was consumed. The fault is now applied by noteTagWake() on a real
        // dependent that the caller is really waking; this gate only records
        // the attempt. Returning false also disables the caller's legacy
        // "pop a random different chain" surgery, which had no way to report
        // whether a victim was found.
        if (fi_mode != Mode::SrcReadyBitflip) return false;

        // A new producer wake invalidates an attempt that never found a
        // victim on a previous wake (counted as attempted + no_victim; the
        // fault budget was never consumed).
        chaos_iq_lifecycle::abortPendingAttempt(ws_attempt, iq_counts);

        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!completed_inst) return false;
        if (replaying_delayed_wake) return false;
        // W7.4 D86 fpOnly (see shouldOmitWake): the trigger wake is
        // restricted to FP/SIMD producers.
        if (fp_only && !isFpOpClass(completed_inst->opClass())) return false;

        iq_counts.eligible++;
        // sampling-bias fix: skip on eligible completed-inst events
        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) { --events_to_skip; return false; }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // Gate hit = ATTEMPT. No applied/activated count, no budget use.
        chaos_iq_lifecycle::beginAttempt(ws_attempt, completed_inst->seqNum,
                                         (unsigned)tid, curTick());
        iq_counts.attempted++;
        return false;
    }

    bool
    CHAOSIQ::shouldDelayWake(ThreadID tid, const o3::DynInstPtr &completed_inst)
    {
        // §2.5 F6 wake_phase — FQ08-c: permanently closed.
        //
        // Returning true here makes InstructionQueue schedule its
        // o3::DelayedWakeEvent, which (a) holds only a DynInstPtr and no
        // identity/generation stamp and (b) calls iq->wakeDependents(inst)
        // unconditionally, where `assert(!completed_inst->isSquashed())`
        // aborts on a producer squashed inside the delay window and a freed/
        // reallocated destination register would wake the NEW occupant's
        // dependents. CHAOSIQ now owns the delayed wake (shouldOmitWake ->
        // DelayedWake), so this legacy gate must never fire.
        (void)tid;
        (void)completed_inst;
        return false;
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
        iq_counts.eligible++;
        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) { --events_to_skip; return false; }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;
        return true;
    }

    // W7.4 class helpers (D86-D91): the tag-index domain and the
    // PhysRegId factory of the target register class. int = the W5
    // [0, numIntPhysRegs) domain / intPhysRegId; vec = [0,
    // numVecPhysRegs) / vecPhysRegId (regfile.hh:172-177).
    int
    CHAOSIQ::numTargetPhysRegs(o3::CPU *o3cpu)
    {
        return (int)(target_reg_class == IntRegClass
            ? o3cpu->physRegFile().numIntPhysRegs()
            : o3cpu->physRegFile().numVecPhysRegs());
    }

    PhysRegIdPtr
    CHAOSIQ::targetPhysRegId(o3::CPU *o3cpu, int idx)
    {
        return target_reg_class == IntRegClass
            ? o3cpu->physRegFile().intPhysRegId(idx)
            : o3cpu->physRegFile().vecPhysRegId(idx);
    }

    const char *
    CHAOSIQ::targetClassName()
    {
        return target_reg_class == IntRegClass ? "int" : "vec";
    }

    // W7.4 D86: the FP/SIMD opClass filter (Float* ∪ SimdFloat*, the
    // CHAOSFPU §2.6 isFpOpClass convention) — integer SIMD stays out of
    // the fpOnly scoping (documented, same caliber as W7.1's fpOnly).
    bool
    CHAOSIQ::isFpOpClass(OpClass oc)
    {
        return oc == FloatAddOp || oc == FloatCmpOp || oc == FloatCvtOp ||
               oc == FloatMultOp || oc == FloatMultAccOp || oc == FloatDivOp ||
               oc == FloatMiscOp || oc == FloatSqrtOp ||
               oc == SimdFloatAddOp || oc == SimdFloatAluOp ||
               oc == SimdFloatCmpOp || oc == SimdFloatCvtOp ||
               oc == SimdFloatMultOp || oc == SimdFloatMultAccOp ||
               oc == SimdFloatDivOp || oc == SimdFloatSqrtOp ||
               oc == SimdFloatMiscOp;
    }

    int
    CHAOSIQ::collectSrcSlots(const o3::DynInstPtr &inst,
                             std::vector<int> &slots)
    {
        // W5.10-11 Int-IQ scope / W7.4 FP-SIMD twin: the tag/ready fields
        // live on the TARGET-class source slots — IntRegClass ("int", the
        // W5 population) or VecRegClass ("vec" — scalar FP, FP SIMD AND
        // integer SIMD sources all rename onto VecRegClass on AArch64, so
        // the one vec class is the whole FP/SIMD queue population).
        slots.clear();
        for (int i = 0; i < (int)inst->numSrcRegs(); i++) {
            PhysRegIdPtr s = inst->renamedSrcIdx(i);
            if (!s) continue;
            if (s->classValue() != target_reg_class) continue;
            slots.push_back(i);
        }
        return (int)slots.size();
    }

    bool
    CHAOSIQ::maybeCorruptTag(ThreadID tid, const o3::DynInstPtr &inst)
    {
        // W5.11 D50-D54 (ooo 04-design-matrix R51-R55) / W7.4 D87-D91
        // (R88-R92, the FP/SIMD twins): corrupt ONE target-class source
        // TAG of the IQ entry as it is written (the hook sits in
        // InstructionQueue::insert BEFORE addToDependents, so the
        // dependency graph, the scoreboard check and the issue-time
        // operand read — DynInst::getRegOperand reads renamedSrcIdx,
        // dyn_inst.hh — all follow the corrupted tag: the entry WAITS FOR
        // and READS the wrong physreg, the faithful CAM-tag-mismatch
        // realization; no IQ-internal surgery needed). targetClass=vec
        // scopes the population to VecRegClass source tags (the FP/SIMD
        // queue: scalar FP + FP SIMD + integer SIMD, all renamed onto
        // VecRegClass) with the [0, numVecPhysRegs) tag domain.
        if (fi_mode != Mode::TagSwap && fi_mode != Mode::TagBitflip
                && fi_mode != Mode::TagBitflip2 && fi_mode != Mode::TagStuck
                && fi_mode != Mode::TagStaleRead)
            return false;
        if (!cpu) return false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;
        // W5.10-11 Int-IQ scope / W7.4 FP-SIMD twin (D87-91): "int" keeps
        // the W5 population gate (FP/vector entries are NOT this unit's
        // population); "vec" scopes by the SLOT CLASS below instead — the
        // FP/SIMD queue population is exactly "has a VecRegClass source
        // tag" (scalar FP, FP SIMD and integer SIMD all rename onto
        // VecRegClass), so an entry with no vec-class src slot is
        // honestly skipped (no field), whatever its instruction class.
        if (target_reg_class == IntRegClass
                && (inst->isFloating() || inst->isVector()))
            return false;

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
                int n = collectSrcSlots(inst, slots);
                if (n == 0) return false;   // arm on an entry WITH the field
                if (!gateEligible()) return false;
                int num_phys = numTargetPhysRegs(o3cpu);
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
                        << ", class=" << targetClassName()
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
                if (!cur || cur->classValue() != target_reg_class)
                    return false;
                int written = cur->index();
                int num_phys = numTargetPhysRegs(o3cpu);
                int masked = tag_stuck_polarity
                    ? (written | (1 << tag_stuck_bit))
                    : (written & ~(1 << tag_stuck_bit));
                if (masked == written) {
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Site: iq_insert, mode=tag_stuck"
                            << ", tid=" << (int)tid
                            << ", sn=" << inst->seqNum
                            << ", class=" << targetClassName()
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
                            << ", class=" << targetClassName()
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
                    targetPhysRegId(o3cpu, masked));
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: iq_insert, mode=tag_stuck"
                        << ", tid=" << (int)tid
                        << ", sn=" << inst->seqNum
                        << ", class=" << targetClassName()
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
        int n = collectSrcSlots(inst, slots);
        if (n == 0) {
            if (write_log && skip_logs < 32) {
                ++skip_logs;
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: iq_insert, tid=" << (int)tid
                    << ", sn=" << inst->seqNum
                    << " — entry has no " << targetClassName()
                    << " src tag (skipped, no field)"
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
        int num_phys = numTargetPhysRegs(o3cpu);
        if (num_phys <= 1) return false;

        if (fi_mode == Mode::TagStaleRead) {
            // D54 (R55) / D91 (R92): at the slot-overwrite instant the tag
            // write silently FAILS — the slot retains the PREVIOUS
            // occupant's tag; the entry waits for / reads a long-retired,
            // unrelated physreg ("旧 tag 大概率仍指向一个存在的、有
            // 真实数据的物理寄存器"). HONEST APPROXIMATION: gem5's IQ has
            // no slot array — the previous occupant = the newest
            // issue-time departure (noteIqDeparture ring) with a
            // TARGET-class tag at the SAME slot index.
            // ROBUSTNESS (W7.4 fix, found by the nbody directed run):
            // DynInst's _srcIdx entries are POINTERS into array storage
            // that gem5 RECYCLES through the inst pool — a departed
            // micro-op's tag storage can be overwritten while our ring
            // still holds the DynInst ref (observed: a scanned "vec tag"
            // of index 60128 on the 48-entry vec pool; aliasing it gave a
            // dangling pointer and a PhysRegFile::getReg panic). Guards:
            // (1) the candidate index must lie in the legal [0, num_phys)
            // target domain — a garbage/dangling read is honestly skipped;
            // (2) the injected id is RECONSTRUCTED from the regfile's
            // permanent id table (targetPhysRegId) — never aliased from
            // the departed inst's recyclable pointer storage.
            int stale_idx = -1;
            uint64_t prev_sn = 0;
            for (auto it = tag_departed.rbegin();
                    it != tag_departed.rend(); ++it) {
                if ((*it)->seqNum == inst->seqNum) continue;
                if (slot >= (int)(*it)->numSrcRegs()) continue;
                PhysRegIdPtr s = (*it)->renamedSrcIdx(slot);
                if (!s || s->classValue() != target_reg_class) continue;
                int cand = s->index();
                if (cand < 0 || cand >= num_phys) continue;  // garbage tag
                stale_idx = cand;
                prev_sn = (*it)->seqNum;
                break;
            }
            if (stale_idx < 0 || stale_idx == cur_idx) {
                if (write_log && skip_logs < 32) {
                    ++skip_logs;
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: iq_insert, mode=tag_stale_read"
                        << ", tid=" << (int)tid
                        << ", sn=" << inst->seqNum
                        << ", class=" << targetClassName()
                        << ", src_slot=" << slot
                        << ", true_tag=" << cur_idx
                        << " — no departed occupant with a legal "
                        << targetClassName() << " tag at"
                           " this slot in the ring (skipped, no injection)"
                        << ", skip_log: " << skip_logs
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                return false;
            }
            inst->renameSrcReg(slot, targetPhysRegId(o3cpu, stale_idx));
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: iq_insert, mode=tag_stale_read"
                    << ", tid=" << (int)tid
                    << ", sn=" << inst->seqNum
                    << ", class=" << targetClassName()
                    << ", src_slot=" << slot
                    << ", true_tag=" << cur_idx
                    << " (this slot's tag write SILENTLY FAILED)"
                    << ", stale_tag=" << stale_idx
                    << ", previous_occupant_sn=" << prev_sn
                    << ", approx=prev_issue_departure_same_slot (gem5 IQ"
                       " has no slot array — previous occupant = newest"
                       " issue-time departure with a "
                    << targetClassName() << " tag at the same"
                       " slot index, the D40 stale_departure pattern;"
                       " id reconstructed from the regfile table)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }

        int new_idx = -1;
        int log_b1 = -1, log_b2 = -1;
        if (fi_mode == Mode::TagSwap) {
            // D50 (R51) / D87 (R88): 换值 — the waiting tag becomes
            // ANOTHER physreg number of the target class (random legal
            // id, the RAT-A setEntry semantics). The new tag may be
            // in-flight (wrong producer wait) or already-written
            // (immediate stale read) — both the designed behaviors.
            do {
                new_idx = (int)(rng() % (unsigned)num_phys);
            } while (new_idx == cur_idx);
        } else {
            // D51/D52 / D88/D89: 1 / 2 distinct random bits of the
            // target-class tag index (the destid_bitflip domain policy:
            // bits of the tag field, out-of-range = honest skip, never
            // clamped).
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
                        << ", class=" << targetClassName()
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

        inst->renameSrcReg(slot, targetPhysRegId(o3cpu, new_idx));
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_insert, mode="
                << (fi_mode == Mode::TagSwap ? "tag_swap"
                    : fi_mode == Mode::TagBitflip ? "tag_bitflip"
                    : "tag_bitflip2")
                << ", tid=" << (int)tid
                << ", sn=" << inst->seqNum
                << ", class=" << targetClassName()
                << ", tag_domain=[0," << num_phys << ")"
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
        // W5.10 D47 (ooo 04-design-matrix R48, ready位·提前置位) / W7.4
        // D86 (R87, the FP/SIMD twin): force ONE not-yet-ready
        // TARGET-class source slot's ready bit at IQ entry — the entry
        // lies about its operand availability. The hook sits BEFORE
        // addToDependents: the per-slot bit keeps the entry OFF that
        // slot's dependency chain (no later wake can re-mark it — the
        // scheduleReadyInsts assert(iq) double-issue artifact is
        // impossible), while the incremented counter lets a
        // last-unready-slot entry reach the normal addIfReady at the end
        // of insert() THIS cycle — it issues and reads the physreg BEFORE
        // the producer's writeback lands (stale-PRF-value silent-SDC
        // family, same value source as the verified done_early /
        // src_ready_bitflip modes). D86's vec scope: the ready bit of a
        // VecRegClass source slot (scalar FP / SIMD operands).
        if (fi_mode != Mode::ReadyEarly) return;
        if (!cpu) return;
        // W5 Int-IQ population gate / W7.4 vec twin (see maybeCorruptTag:
        // "vec" scopes by slot class — the FP/SIMD queue population).
        if (target_reg_class == IntRegClass
                && (inst->isFloating() || inst->isVector()))
            return;

        std::vector<int> slots;
        int n = collectSrcSlots(inst, slots);
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
                << ", class=" << targetClassName()
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
        // FQ08-b: the injected wrong-source write marks a slot ready but the
        // victim stays in that source's dependency chain (CHAOSIQ cannot pop
        // it without touching dependGraph). When that source's producer later
        // completes, this callback suppresses the duplicate genuine mark
        // exactly once, restoring the "one mark per source" invariant and
        // preventing a second push onto the ready list after issue.
        if (fi_mode == Mode::SrcReadyBitflip) {
            if (!ws_duplicate.tracked || !dep_inst) return false;
            const bool suppress = chaos_iq_lifecycle::suppressDuplicateWake(
                ws_duplicate, dep_inst->seqNum,
                (unsigned)dep_inst->threadNumber, (uint64_t)producer_flat);
            if (suppress && write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: iq_wakeDependents, mode=src_ready_bitflip"
                    << ", duplicate genuine wake suppressed"
                    << ", victim_sn=" << dep_inst->seqNum
                    << ", corrupt_chain_flat=" << (unsigned)producer_flat
                    << " (the source was already marked ready by the"
                       " injected wrong-source write)"
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return suppress;
        }

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
        // FQ08-b: src_ready_bitflip victim hook. The caller invokes this for
        // every dependent it is about to wake, before markSrcRegReady().
        if (fi_mode == Mode::SrcReadyBitflip) {
            maybeApplyWrongSourceWake(dep_inst, chain_flat);
            return;
        }

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
    CHAOSIQ::maybeApplyWrongSourceWake(const o3::DynInstPtr &dep_inst,
                                       RegIndex chain_flat)
    {
        // FQ08-b: apply the wrong-source ready write to a REAL victim.
        //
        // The victim is the dependent the caller is currently waking: it is
        // a live IQ resident (the caller's loop owns it), so a successful
        // write is genuine evidence. The fault is the "wrong source" part:
        // ONE OTHER unready source slot of the same target register class is
        // marked ready by this wake, so the victim can issue before that
        // slot's producer has written (stale operand / lying ready counter).
        //
        // If this dependent is not eligible (squashed, fully ready, or its
        // only unready target-class slot is the chain being woken — i.e. the
        // wake is not "wrong" at all), the attempt stays pending and a later
        // dependent may still be the victim. If the whole wake ends without
        // one, shouldWrongSourceWake() drops it as no_victim at the next
        // producer wake: no applied/activated count, no budget use.
        if (!ws_attempt.pending || !dep_inst) return;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return;

        chaos_iq_lifecycle::VictimView view;
        view.squashed = dep_inst->isSquashed();
        view.issued = dep_inst->isIssued();
        view.ready_regs = dep_inst->readyRegs;
        view.num_src_regs = (unsigned)dep_inst->numSrcRegs();
        for (int i = 0; i < (int)dep_inst->numSrcRegs(); i++) {
            PhysRegIdPtr src = dep_inst->renamedSrcIdx(i);
            if (!src || src->classValue() != target_reg_class) continue;
            // An always-ready register is not part of the dependency graph;
            // marking it ready is not a wrong-source fault.
            if (src->isAlwaysReady()) continue;
            view.slot.push_back((unsigned)i);
            view.flat.push_back((uint64_t)src->flatIndex());
            view.unready.push_back(dep_inst->readySrcIdx(i) ? 0 : 1);
        }

        const int slot = chaos_iq_lifecycle::chooseWrongSlot(
            view, (uint64_t)chain_flat);
        if (slot < 0) return;   // no victim on this dependent

        PhysRegIdPtr src = dep_inst->renamedSrcIdx(slot);
        const int src_idx = src->index();
        const uint32_t src_gen = o3cpu->physRegFile().generationOf(src);
        const bool issueable_before = dep_inst->readyToIssue();
        const unsigned ready_before = (unsigned)dep_inst->readyRegs;

        dep_inst->markSrcRegReady((RegIndex)slot);

        const bool issueable_after = dep_inst->readyToIssue();
        const chaos_iq_lifecycle::ApplyOutcome outcome =
            chaos_iq_lifecycle::noteApplied(iq_counts, issueable_before,
                                            issueable_after);
        faults_injected_count++;
        ws_attempt.pending = false;
        chaos_iq_lifecycle::recordDuplicateWake(
            ws_duplicate, dep_inst->seqNum,
            (unsigned)dep_inst->threadNumber, (uint64_t)src->flatIndex());

        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode=src_ready_bitflip"
                << ", APPLIED wrong-source ready bit"
                << ", tid=" << (int)dep_inst->threadNumber
                << ", victim_sn=" << dep_inst->seqNum
                << ", victim_pc=0x" << std::hex
                << dep_inst->pcState().as<ArmISA::PCState>().pc() << std::dec
                << ", victim_op_class="
                << enums::OpClassStrings[
                       static_cast<int>(dep_inst->opClass())]
                << ", class=" << targetClassName()
                << ", victim_src_slot=" << slot
                << ", victim_src_phys=" << src_idx
                << ", victim_src_class=" << src->className()
                << ", victim_src_flat=" << (unsigned)src->flatIndex()
                << ", victim_src_generation=" << src_gen
                << ", wrong_of_chain_flat=" << (unsigned)chain_flat
                << ", producer_sn=" << ws_attempt.producer_sn
                << ", producer_tid=" << ws_attempt.producer_tid
                << ", producer_wake_tick=" << ws_attempt.tick
                << ", ready_regs " << ready_before << " -> "
                << (unsigned)dep_inst->readyRegs << " / "
                << (unsigned)dep_inst->numSrcRegs()
                << (outcome.activated
                        ? " (activated: the wrong-source write alone made"
                          " the victim issueable — stale operand path)"
                        : " (applied: wrong ready bit set, one wake short)")
                << ", eligible=" << iq_counts.eligible
                << ", attempted=" << iq_counts.attempted
                << ", applied=" << iq_counts.applied
                << ", activated=" << iq_counts.activated
                << ", no_victim=" << iq_counts.no_victim
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
    }

    const char *
    CHAOSIQ::modeName()
    {
        switch (fi_mode) {
          case Mode::WakeOmit: return "wake_omit";
          case Mode::SrcReadyBitflip: return "src_ready_bitflip";
          case Mode::WakePhase: return "wake_phase";
          case Mode::ReadyEarly: return "ready_early";
          case Mode::ReadyNever: return "ready_never";
          case Mode::ReadyNeverEvent: return "ready_never_event";
          case Mode::TagSwap: return "tag_swap";
          case Mode::TagBitflip: return "tag_bitflip";
          case Mode::TagBitflip2: return "tag_bitflip2";
          case Mode::TagStuck: return "tag_stuck";
          case Mode::TagStaleRead: return "tag_stale_read";
          case Mode::DispatchMisroute: return "dispatch_misroute";
        }
        return "unknown";
    }

    void
    CHAOSIQ::dumpIqCounts()
    {
        // Observable FQ08 accounting. The trailing "faults_injected: <n>" is
        // the explicit count both tools/runner.py and
        // tools/fsu_seed_runner.py use for the injection log, so this summary
        // line must keep that form (it is the authoritative final value).
        if (!write_log || !log_stream || !log_stream->stream()) return;
        *(log_stream->stream())
            << "CHAOS_IQ_COUNTS mode=" << modeName()
            << ", eligible=" << iq_counts.eligible
            << ", attempted=" << iq_counts.attempted
            << ", applied=" << iq_counts.applied
            << ", activated=" << iq_counts.activated
            << ", no_victim=" << iq_counts.no_victim
            << ", pending_attempt=" << (ws_attempt.pending ? 1 : 0)
            << ", delayed_scheduled=" << dw_counts.scheduled
            << ", delayed_fired=" << dw_counts.fired
            << ", delayed_ignored_no_inst=" << dw_counts.ignored_no_inst
            << ", delayed_ignored_identity=" << dw_counts.ignored_identity
            << ", delayed_ignored_squashed=" << dw_counts.ignored_squashed
            << ", delayed_ignored_generation=" << dw_counts.ignored_generation
            << ", faults_injected: " << faults_injected_count
            << std::endl;
    }

    chaos_iq_lifecycle::WakeStamp
    CHAOSIQ::snapshotWakeStamp(o3::CPU *o3cpu, const o3::DynInstPtr &inst)
    {
        // FQ08-c: value snapshot at schedule time. The event stores this and
        // the refcounted DynInstPtr; the stamps let process() detect a freed/
        // reallocated destination physical register (generation bump) before
        // touching the dependency graph.
        chaos_iq_lifecycle::WakeStamp stamp;
        stamp.seq_num = inst->seqNum;
        stamp.tid = (unsigned)inst->threadNumber;
        for (int i = 0; i < (int)inst->numDestRegs(); i++) {
            PhysRegIdPtr dest = inst->renamedDestIdx(i);
            chaos_iq_lifecycle::DestStamp ds;
            if (dest) {
                ds.flat = (uint64_t)dest->flatIndex();
                ds.generation = o3cpu->physRegFile().generationOf(dest);
            }
            stamp.dests.push_back(ds);
        }
        return stamp;
    }

    void
    CHAOSIQ::noteDelayedWakeIgnored(
        chaos_iq_lifecycle::WakeDecision decision,
        const o3::DynInstPtr &inst)
    {
        // FQ08-c: a delayed wake hit a dead/absent/reallocated producer and
        // was safely skipped. Every log line keeps the "faults_injected: <n>"
        // suffix so log parsers never count it as a second injection.
        if (!write_log || !log_stream || !log_stream->stream()) return;
        *(log_stream->stream())
            << "Tick: " << curTick()
            << ", Site: iq_delayed_wake, mode=wake_phase"
            << ", IGNORED reason="
            << chaos_iq_lifecycle::wakeDecisionName(decision)
            << ", completed_sn=" << (inst ? inst->seqNum : 0)
            << ", completed_tid=" << (inst ? (int)inst->threadNumber : -1)
            << ", delayed_fired=" << dw_counts.fired
            << ", delayed_ignored_squashed=" << dw_counts.ignored_squashed
            << ", delayed_ignored_generation=" << dw_counts.ignored_generation
            << ", delayed_ignored_identity=" << dw_counts.ignored_identity
            << ", faults_injected: " << faults_injected_count
            << std::endl;
    }

    CHAOSIQ::DelayedWake::DelayedWake(
        CHAOSIQ *_injector, const o3::DynInstPtr &_inst,
        const chaos_iq_lifecycle::WakeStamp &_stamp)
        : Event(Default_Pri, AutoDelete), injector(_injector), inst(_inst),
          stamp(_stamp)
    {
    }

    void
    CHAOSIQ::DelayedWake::process()
    {
        auto *o3cpu = dynamic_cast<o3::CPU *>(injector->cpu);
        if (!o3cpu) return;

        chaos_iq_lifecycle::WakeObserved now;
        now.has_inst = (inst.get() != nullptr);
        if (inst) {
            now.seq_num = inst->seqNum;
            now.tid = (unsigned)inst->threadNumber;
            now.squashed = inst->isSquashed();
            for (int i = 0; i < (int)inst->numDestRegs(); i++) {
                PhysRegIdPtr dest = inst->renamedDestIdx(i);
                chaos_iq_lifecycle::DestStamp ds;
                if (dest) {
                    ds.flat = (uint64_t)dest->flatIndex();
                    ds.generation =
                        o3cpu->physRegFile().generationOf(dest);
                }
                now.dests.push_back(ds);
            }
        }

        const chaos_iq_lifecycle::WakeDecision decision =
            chaos_iq_lifecycle::classifyWake(stamp, now);
        chaos_iq_lifecycle::noteWakeDecision(injector->dw_counts, decision);

        if (decision != chaos_iq_lifecycle::WakeDecision::Fire) {
            injector->noteDelayedWakeIgnored(decision, inst);
            return;
        }

        // The producer is still the same, unsquashed object and still owns
        // every destination physical register: the delayed broadcast is safe.
        injector->iq_counts.activated++;
        injector->replaying_delayed_wake = true;
        o3cpu->o3IEW().instQueue.wakeDependents(inst);
        injector->replaying_delayed_wake = false;

        if (injector->write_log && injector->log_stream
                && injector->log_stream->stream()) {
            *(injector->log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: iq_delayed_wake, mode=wake_phase"
                << ", FIRED delayed wake (producer live, generation stable)"
                << ", completed_sn=" << inst->seqNum
                << ", completed_tid=" << (int)inst->threadNumber
                << ", delayed_fired=" << injector->dw_counts.fired
                << ", eligible=" << injector->iq_counts.eligible
                << ", attempted=" << injector->iq_counts.attempted
                << ", applied=" << injector->iq_counts.applied
                << ", activated=" << injector->iq_counts.activated
                << ", faults_injected: " << injector->faults_injected_count
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
        // FQ08-b/c: observable accounting summary at exit (eligible /
        // attempted / applied / activated are separate). Emitted for every
        // logging run so a "0 injections" outcome is explicit, never a
        // silent zero.
        if (write_log) {
            registerExitCallback([this]() { dumpIqCounts(); });
        }
    }

} // namespace gem5
