#include "cpu/o3/CHAOSExec/CHAOSExec.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst, opClass, isInteger, popResult, pushResult
#include "cpu/op_class.hh"       // IntAluOp/IntMultOp/IntDivOp
#include "cpu/inst_res.hh"       // InstResult::corrupt
#include "debug/CHAOSExec.hh"
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
        }
    }

    CHAOSExec::~CHAOSExec() {}

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
    }

} // namespace gem5
