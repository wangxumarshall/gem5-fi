#include "cpu/o3/CHAOSFPU/CHAOSFPU.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst, opClass, isFloating
#include "cpu/op_class.hh"       // FloatAddOp/FloatMultOp/FloatMultAccOp/SimdFloat*
#include "cpu/inst_res.hh"       // InstResult::corruptBlob
#include "debug/CHAOSFPU.hh"
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
        }
    }

    CHAOSFPU::~CHAOSFPU() {}

    bool
    CHAOSFPU::inWindow() {
        Tick now = curTick();
        Tick f = first_clock * 1000;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * 1000) return false;
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
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        OpClass oc = dyn_inst->opClass();
        if (!isFpOpClass(oc)) return false;
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
    }

} // namespace gem5
