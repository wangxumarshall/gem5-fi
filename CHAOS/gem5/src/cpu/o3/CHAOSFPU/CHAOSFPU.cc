#include "cpu/o3/CHAOSFPU/CHAOSFPU.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst, opClass, isFloating
#include "cpu/op_class.hh"       // FloatAddOp/FloatMultOp/FloatMultAccOp/SimdFloat*
#include "cpu/inst_res.hh"       // InstResult::corruptBlob
#include "cpu/o3/chaos_event_sample.hh"  // v1.1 Phase 8.2 uniform sampling
#include "debug/CHAOSFPU.hh"
#include "sim/sim_exit.hh"
#include "params/CHAOSFPU.hh"

namespace gem5
{

    CHAOSFPU::CHAOSFPU(const CHAOSFPUParams &p)
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
            log_stream = simout.create("fpu_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSFPU: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        // v1.1 Phase 8.2: a FIXED skip (from the driver's uniform
        // chaosPickSkip) overrides the legacy geometric draw. Sentinel
        // UINT64_MAX (param default) keeps the old behavior so every
        // existing campaign/manifest replays unchanged.
        if (p.eventsToSkip != ~0ULL) {
            fixed_skip_mode = true;
            events_to_skip = p.eventsToSkip;
        } else {
            // Sampling-bias fix (findings.md Phase 2.2/3.0): skip a
            // geometric(p=0.1) number of eligible events before the first
            // injection so maxFaults=1 lands on a seed-dependent event.
            std::geometric_distribution<uint64_t> skip_dist(0.1);
            events_to_skip = skip_dist(rng);
        }
        count_only = p.countOnly;
        }
    }

    CHAOSFPU::~CHAOSFPU()
    {
        // v1.1 Phase 8.2 countOnlyMode: the driver's dry-run learns
        // N_eligible from this line (campaign.py parses the log).
        if (count_only && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT=" << eligible_count
                << std::endl;
        }
    }

    bool
    CHAOSFPU::inWindow() {
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

    static bool isFpOpClass(OpClass oc) {
        // §2.6 FSU opClass filter: all scalar Float* + SIMD FP.
        return oc == FloatAddOp || oc == FloatCmpOp || oc == FloatCvtOp ||
               oc == FloatMultOp || oc == FloatMultAccOp || oc == FloatDivOp ||
               oc == FloatMiscOp || oc == FloatSqrtOp ||
               oc == SimdFloatAddOp || oc == SimdFloatAluOp || oc == SimdFloatCmpOp ||
               oc == SimdFloatCvtOp || oc == SimdFloatMultOp || oc == SimdFloatMultAccOp ||
               oc == SimdFloatDivOp || oc == SimdFloatSqrtOp || oc == SimdFloatMiscOp;
    }

    bool
    CHAOSFPU::maybeCorrupt(o3::DynInst *dyn_inst)
    {
        if (!cpu || probability <= 0.0f) return false;
        if (!count_only && max_faults != 0 && faults_injected_count >= max_faults)
            return false;
        if (!inWindow()) return false;
        OpClass oc = dyn_inst->opClass();
        if (!isFpOpClass(oc)) return false;

        // v1.1 Phase 8.2 countOnlyMode: count only CORRUPTIBLE eligible
        // events (an empty/invalid InstResult can never take the fault);
        // never corrupt. This makes the counted stream identical to the
        // stream the fixed-skip draw indexes into.
        if (count_only) {
            if (dyn_inst->hasCorruptibleResult()) ++eligible_count;
            return false;
        }

        // v1.1 Phase 8.2 fixed-skip mode: consume the skip ONLY on
        // corruptible events so skip indexes the same stream countOnly
        // counted. Legacy geometric mode keeps the old consume-on-eligible
        // behavior (byte-identical replays for existing campaigns).
        if (fixed_skip_mode && !dyn_inst->hasCorruptibleResult()) return false;

        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible events (N ~ geometric(0.1) from the seed) so the
        // single fault lands on a seed-dependent event.
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // Corrupt the FP result: try blob path first (vector/FP stored as
        // blob), then scalar RegVal path (FP64 may be stored as a uint64
        // scalar — AArch64 FP registers are regBytes()=8, scalar).
        RegVal mask = fault_mask ? fault_mask : (1ULL << (rng() % 64));
        bool ok = dyn_inst->corruptFrontResultBlob((uint64_t)mask);
        if (!ok) ok = dyn_inst->corruptFrontResult(mask);  // scalar path
        if (!ok) return false;  // no recorded result (RecordResult flag off)
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
    CHAOSFPU::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSFPU: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
                o3cpu->setChaosFPU(this);
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
