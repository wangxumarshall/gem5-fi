#include "cpu/o3/CHAOSExec/CHAOSExec.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst, opClass, isInteger, popResult, pushResult
#include "cpu/op_class.hh"       // IntAluOp/IntMultOp/IntDivOp
#include "cpu/inst_res.hh"       // InstResult::corrupt
#include "debug/CHAOSExec.hh"
#include "sim/sim_exit.hh"
#include "params/CHAOSExec.hh"

namespace gem5
{

    CHAOSExec::CHAOSExec(const CHAOSExecParams &p)
        : SimObject(p),
          cpu(p.cpu),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          fault_mask(p.faultMask),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          bitseg(p.bitseg),
          recurring_stuck(p.recurringStuck),
          f3_dependent(p.f3Dependent),
          val_lo(p.valLo),
          val_hi(p.valHi)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("exec_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSExec: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            // v1.1 Phase 8.2: fixed uniform skip (driver-provided,
            // chaos_event_sample.hh) overrides the legacy geometric(0.1)
            // draw; UINT64_MAX sentinel keeps legacy behavior.
            if (p.eventsToSkip != ~0ULL) {
                fixed_skip_mode = true;
                events_to_skip = p.eventsToSkip;
            } else {
                std::geometric_distribution<uint64_t> skip_dist(0.1);
                events_to_skip = skip_dist(rng);
            }
            count_only = p.countOnly;
        }
    }

    CHAOSExec::~CHAOSExec()
    {
        // v1.1 Phase 8.2 countOnlyMode: the driver's dry-run learns
        // N_eligible from this line (campaign.py parses the log).
        if (count_only && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT=" << eligible_count
                << std::endl;
        }
    }

    bool
    CHAOSExec::inWindow() {
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
    CHAOSExec::maybeCorrupt(o3::DynInst *dyn_inst)
    {
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;

        // §2.12 opClass filter: integer ALU / multiply / divide only.
        OpClass oc = dyn_inst->opClass();
        if (oc != IntAluOp && oc != IntMultOp && oc != IntDivOp) return false;

        // v1.2 Phase 13: with the PRF-dest rewrite the corruptible stream
        // is 'inst has an INT destination register' — checkable directly
        // from the dest-reg list (no InstResult involved, same as the FPU
        // patch bfa9c4f).
        bool has_int_dest = false;
        for (int i = 0; i < dyn_inst->numDestRegs(); i++) {
            PhysRegIdPtr d = dyn_inst->renamedDestIdx(i);
            if (d && !d->is(InvalidRegClass) &&
                d->classValue() == IntRegClass) {
                has_int_dest = true;
                break;
            }
        }
        // v1.1 Phase 8.2 countOnlyMode: count only CORRUPTIBLE eligible
        // events; never corrupt (same stream the fixed-skip indexes).
        if (count_only) {
            if (has_int_dest) ++eligible_count;
            return false;
        }
        // v1.1 Phase 8.2 fixed-skip: consume skip only on corruptible
        // events (same stream as countOnly). Legacy geometric keeps the
        // old consume-on-eligible behavior.
        if (fixed_skip_mode && !has_int_dest)
            return false;
        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible events (N ~ geometric(0.1) from the seed, or the FIXED
        // uniform skip from chaos_event_sample.hh) so the single fault
        // lands on a seed-dependent event.
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }


        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // v1.2 Phase 13 — PRF-DEST REWRITE (same root cause as the FPU
        // patch bfa9c4f): the old corruptFrontResult XORed the
        // DynInst::instResult queue whose ONLY consumer is the checker CPU
        // (checker=Null in every CHAOS config); integer results reach the
        // PRF via setRegOperand -> cpu->setReg -> regFile during
        // staticInst->execute() and never touch instResult — the fault was
        // architecturally invisible (the first-round Exec 'all Masked'
        // artifact, same as FPU). Now: XOR the physical INT destination
        // register's PRF value directly, post-execute.
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        bool ok = false;
        RegVal mask = 0;   // hoisted: the log line below reads it
        for (int i = 0; i < dyn_inst->numDestRegs() && !ok; i++) {
            PhysRegIdPtr dest = dyn_inst->renamedDestIdx(i);
            if (!dest || dest->is(InvalidRegClass)) continue;
            if (dest->classValue() != IntRegClass) continue;
            RegVal v = o3cpu->getReg(dest, dyn_inst->threadNumber);
            // v1.2 Phase 13 mode 4 — f3_data_dependent: gate on the result
            // value window (post-hoc operand proxy).
            if (f3_dependent && (val_lo != 0 || val_hi != 0)) {
                if (v < val_lo || v > val_hi) { ok = false; continue; }
            }
            // v1.2 Phase 13 modes 2/3 — bitseg (byte/nibble position) and
            // recurring (same fixed mask every event).
            if (recurring_stuck) {
                if (!recurring_mask_drawn) {
                    recurring_mask = fault_mask ? fault_mask
                                                : (1ULL << (rng() % 64));
                    recurring_mask_drawn = true;
                }
                mask = recurring_mask;
            } else if (fault_mask) {
                mask = fault_mask;
            } else if (!bitseg.empty()) {
                int lo = -1, hi = -1;
                if (bitseg == "byte0")      { lo = 0;  hi = 7; }
                else if (bitseg == "byte1") { lo = 8;  hi = 15; }
                else if (bitseg == "byte2") { lo = 16; hi = 23; }
                else if (bitseg == "byte3") { lo = 24; hi = 31; }
                else if (bitseg == "byte4") { lo = 32; hi = 39; }
                else if (bitseg == "byte5") { lo = 40; hi = 47; }
                else if (bitseg == "byte6") { lo = 48; hi = 55; }
                else if (bitseg == "byte7") { lo = 56; hi = 63; }
                else if (bitseg == "nibble"){ lo = 0;  hi = 3; }
                if (lo < 0)
                    panic("CHAOSExec: unknown bitseg '%s'\n",
                          bitseg.c_str());
                int bit = lo + (int)(rng() % (unsigned)(hi - lo + 1));
                mask = (1ULL << bit);
            } else {
                mask = (1ULL << (rng() % 64));
            }
            o3cpu->setReg(dest, v ^ mask, dyn_inst->threadNumber);
            ok = true;
        }
        if (!ok) return false;  // no INT dest on this inst (or f3-gated out)
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: dyn_inst_execute, opClass=" << (int)oc
                << ", sn=" << dyn_inst->seqNum
                << (bitseg.empty() ? std::string() : ", bitseg=" + bitseg)
                << (recurring_stuck ? ", mode=recurring_result_stuck" : "")
                << (f3_dependent ? ", mode=f3_data_dependent" : "")
                << ", mask=0x" << std::hex << mask << std::dec
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSExec::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSExec: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
                o3cpu->setChaosExec(this);
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
