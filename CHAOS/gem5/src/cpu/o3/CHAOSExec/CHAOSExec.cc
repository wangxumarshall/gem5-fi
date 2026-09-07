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
          write_log(p.writeLog)
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

        // v1.1 Phase 8.2 countOnlyMode: count only CORRUPTIBLE eligible
        // events; never corrupt (same stream the fixed-skip indexes).
        if (count_only) {
            if (dyn_inst->hasCorruptibleResult()) ++eligible_count;
            return false;
        }
        // v1.1 Phase 8.2 fixed-skip: consume skip only on corruptible
        // events (same stream as countOnly). Legacy geometric keeps the
        // old consume-on-eligible behavior.
        if (fixed_skip_mode && !dyn_inst->hasCorruptibleResult())
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

        // Corrupt the integer result: pop the front InstResult, XOR a bit,
        // re-push. InstResult::corrupt() flips the RegVal scalar path (no-op
        // for blob/FP/vector — those are §2.6 FSU's scope).
        RegVal mask = fault_mask ? fault_mask : (1ULL << (rng() % 64));
        // DynInst::popResult returns the front; we corrupt it in-place via
        // the new InstResult::corrupt(), then the caller (commit) reads the
        // corrupted value. Since popResult removes from the queue, we use
        // the in-place accessor DynInst::corruptFrontResult() (added below).
        if (!dyn_inst->corruptFrontResult(mask)) {
            // no integer scalar result to corrupt (e.g. store/branch) — no-op
            return false;
        }
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: dyn_inst_execute, opClass=" << (int)oc
                << ", sn=" << dyn_inst->seqNum
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
