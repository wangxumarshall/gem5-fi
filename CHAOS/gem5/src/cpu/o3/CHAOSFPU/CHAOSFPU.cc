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
          write_log(p.writeLog),
          bitseg(p.bitseg)
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

        // v1.1 Phase 9 patch 1a-0: with the PRF-dest rewrite the corruptible
        // stream is 'inst has an FP/vector destination register' — checkable
        // directly from the dest-reg list (no InstResult involved).
        bool has_fp_dest = false;
        for (int i = 0; i < dyn_inst->numDestRegs(); i++) {
            PhysRegIdPtr d = dyn_inst->renamedDestIdx(i);
            if (d && !d->is(InvalidRegClass) &&
                (d->classValue() == VecRegClass ||
                 d->classValue() == FloatRegClass ||
                 d->classValue() == VecElemClass)) {
                has_fp_dest = true;
                break;
            }
        }

        // v1.1 Phase 8.2 countOnlyMode: count only CORRUPTIBLE eligible
        // events (no FP/vector dest = can never take the fault); never
        // corrupt. The counted stream is identical to the stream the
        // fixed-skip draw indexes into.
        if (count_only) {
            if (has_fp_dest) ++eligible_count;
            return false;
        }

        // v1.1 Phase 8.2 fixed-skip mode: consume the skip ONLY on
        // corruptible events so skip indexes the same stream countOnly
        // counted. Legacy geometric mode keeps the old consume-on-eligible
        // behavior (byte-identical replays for existing campaigns).
        if (fixed_skip_mode && !has_fp_dest) return false;

        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible events (N ~ geometric(0.1) from the seed) so the
        // single fault lands on a seed-dependent event.
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // v1.1 Phase 9 patch 1a-0 — PRF-DEST REWRITE. The old path XORed
        // the DynInst::instResult queue, whose ONLY consumer is the checker
        // CPU (checker=Null in every CHAOS config) — FP/SIMD results reach
        // the PRF via getWritableRegOperand (a direct PRF pointer used
        // DURING staticInst->execute()) and never touch instResult, so the
        // fault was architecturally INVISIBLE (Phase 8.1/8.2 root-cause:
        // 6637 opClass-eligible events on cholesky, only 32 with any
        // InstResult, zero effect on the checksum).
        // Now: XOR the physical destination register's PRF storage directly,
        // post-execute (the value is already written there). VecRegClass
        // (all AArch64 FP/SIMD registers) via the writable PRF pointer;
        // scalar classes via getReg/setReg.
        // v1.1 Phase 9 patch 1a mode 1 — bitseg: pick the flip bit ONLY
        // inside the requested IEEE754 double field. Field map (FP64):
        //   sign=bit63 | exp=62..52 (exp_hi=62..58, exp_lo=57..52) |
        //   mant=51..0 (mant_hi=51..35, mant_mid=34..18, mant_lo=17..0)
        // A uniform whole-register pick hits the 52-bit mantissa 81% of
        // the time — method3's field shows 85-93% AFTER workload filtering;
        // bitseg isolates the field experimentally (the campaign stratifies
        // over the six segments).
        RegVal mask;
        if (fault_mask) {
            mask = fault_mask;
        } else if (!bitseg.empty()) {
            int lo = -1, hi = -1;
            if      (bitseg == "sign")    { lo = 63; hi = 63; }
            else if (bitseg == "exp_hi")  { lo = 58; hi = 62; }
            else if (bitseg == "exp_lo")  { lo = 52; hi = 57; }
            else if (bitseg == "mant_hi") { lo = 35; hi = 51; }
            else if (bitseg == "mant_mid"){ lo = 18; hi = 34; }
            else if (bitseg == "mant_lo") { lo = 0;  hi = 17; }
            if (lo < 0)
                panic("CHAOSFPU: unknown bitseg '%s'\n", bitseg.c_str());
            int bit = lo + (int)(rng() % (unsigned)(hi - lo + 1));
            mask = (1ULL << bit);
        } else {
            mask = (1ULL << (rng() % 64));
        }
        bool ok = false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        for (int i = 0; i < dyn_inst->numDestRegs() && !ok; i++) {
            PhysRegIdPtr dest = dyn_inst->renamedDestIdx(i);
            if (!dest || dest->is(InvalidRegClass)) continue;
            switch (dest->classValue()) {
              case VecRegClass: {
                // XOR the low 8 bytes of the vector register's PRF blob.
                void *vp = o3cpu->getWritableReg(dest, dyn_inst->threadNumber);
                if (!vp) break;
                uint64_t *q = reinterpret_cast<uint64_t*>(vp);
                *q ^= (uint64_t)mask;
                ok = true;
                break;
              }
              case FloatRegClass:
              case VecElemClass: {
                RegVal v = o3cpu->getReg(dest, dyn_inst->threadNumber);
                o3cpu->setReg(dest, v ^ mask, dyn_inst->threadNumber);
                ok = true;
                break;
              }
              default:
                break;  // int/cond/misc dests are CHAOSExec's scope
            }
        }
        if (!ok) return false;  // no FP/vector dest register on this inst
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: dyn_inst_execute, opClass=" << (int)oc
                << ", sn=" << dyn_inst->seqNum
                << (bitseg.empty() ? std::string() : ", bitseg=" + bitseg)
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
