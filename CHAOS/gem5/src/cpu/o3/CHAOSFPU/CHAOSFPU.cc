#include "cpu/o3/CHAOSFPU/CHAOSFPU.hh"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <sstream>

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst, opClass, isFloating
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // FSU_PROP stream
#include "arch/arm/insts/static_inst.hh"  // ArmStaticInst::encoding()
#include "cpu/op_class.hh"       // FloatAddOp/FloatMultOp/FloatMultAccOp/SimdFloat*
#include "cpu/inst_res.hh"       // InstResult::corruptBlob
#include "cpu/o3/chaos_event_sample.hh"  // v1.1 Phase 8.2 uniform sampling
#include "debug/CHAOSFPU.hh"
#include "sim/sim_exit.hh"
#include "params/CHAOSFPU.hh"

namespace gem5
{

    // [FSU][FP06] Defined with the other filter helpers below; declared here
    // because the constructor validates the params before that block.
    static bool opClassFromName(const std::string &name, OpClass &out);
    static bool regClassFromName(const std::string &name, int &out);

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
          prf_wb_hook(p.prfWbHook),
          bitseg(p.bitseg),
          precision(p.precision),
          precision_bits(64),
          lane_width((int)p.laneWidth),
          lane_offset((int)p.laneOffset),
          decode_guard(p.decodeGuard),
          fma_weighted(p.fmaWeighted),
          recurring_stuck(p.recurringStuck),
          rounding_sub(p.roundingSub),
          f3_dependent(p.f3Dependent),
          exp_lo(p.expLo),
          exp_hi(p.expHi),
          fpsr_suppress(p.fpsrSuppress),
          permanent_stuck(p.permanentStuck),
          stuck_polarity(p.stuckPolarity),
          f5_warmup(p.f5Warmup),
          f5_sample_limit(p.f5SampleLimit),
          f5_keep_first_last_n(p.f5KeepFirstLastN),
          fsu_model(p.fsuModel),
          fsu_freq(p.fsuFreq),
          fsu_load(p.fsuLoad),
          fsu_submodel(p.fsuSubmodel),
          fsu_eligible_total(p.fsuEligibleTotal),
          rate_warmup(p.rateWarmup),
          rate_divisor(p.fsuRateDivisor),
          jitter_pct(p.fsuJitterPct)
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

        // [FSU][D2] Parse + validate F1/F2/F3 ordinals. The driver
        // (tools/fsu_rate_ordinals.py) is the single generator; the C++ side
        // only consumes the explicit list, so there is no second sampler to
        // drift from the manifest.
        if (!p.rateOrdinals.empty()) {
            std::stringstream ss(p.rateOrdinals);
            std::string tok;
            while (std::getline(ss, tok, ',')) {
                if (tok.empty())
                    panic("CHAOSFPU: empty rate-ordinal token in '%s'\n",
                          p.rateOrdinals.c_str());
                char *end = nullptr;
                unsigned long long v = std::strtoull(tok.c_str(), &end, 10);
                if (end == tok.c_str() || *end != '\0')
                    panic("CHAOSFPU: bad rate ordinal '%s'\n", tok.c_str());
                rate_ordinals.push_back((uint64_t)v);
            }
        }
        rate_mode = !rate_ordinals.empty();
        if (rate_mode) {
            const bool known_freq = fsu_freq == "F1" || fsu_freq == "F2" ||
                                    fsu_freq == "F3";
            if (!known_freq)
                panic("CHAOSFPU: rate ordinals require F1/F2/F3 freq, got "
                      "'%s'\n", fsu_freq.c_str());
            const uint64_t expected = fsu_freq == "F1" ? 1000000ULL :
                                      fsu_freq == "F2" ? 100000ULL :
                                      10000ULL;
            if (rate_divisor != expected)
                panic("CHAOSFPU: %s requires rate_divisor=%llu, got %llu\n",
                      fsu_freq.c_str(), (unsigned long long)expected,
                      (unsigned long long)rate_divisor);
            if (jitter_pct >= 100)
                panic("CHAOSFPU: jitter_pct must be < 100, got %llu\n",
                      (unsigned long long)jitter_pct);
            if (fsu_eligible_total == 0)
                panic("CHAOSFPU: rate mode requires --fsu_eligible_total "
                      "(countOnly census)\n");
            if (probability != 1.0f)
                panic("CHAOSFPU: rate mode requires probability=1.0 "
                      "(ordinals define the exact injection events)\n");
            // These modes can skip a matched ordinal (fpsr/f3) or bypass
            // noteFaultApplied (rounding), which would silently break the
            // rate contract. Reject loudly instead.
            if (fpsr_suppress || f3_dependent || rounding_sub ||
                recurring_stuck)
                panic("CHAOSFPU: rate mode is incompatible with "
                      "fpsr_suppress/f3_dependent/rounding_sub/"
                      "recurring_stuck\n");
            for (size_t i = 0; i < rate_ordinals.size(); ++i) {
                if (i == 0 && rate_ordinals[i] <= rate_warmup)
                    panic("CHAOSFPU: first ordinal %llu <= warmup %llu\n",
                          (unsigned long long)rate_ordinals[i],
                          (unsigned long long)rate_warmup);
                if (i > 0 && rate_ordinals[i] <= rate_ordinals[i - 1])
                    panic("CHAOSFPU: ordinals not strictly increasing at "
                          "index %zu\n", i);
                if (rate_ordinals[i] > fsu_eligible_total)
                    panic("CHAOSFPU: ordinal %llu > eligible_total %llu\n",
                          (unsigned long long)rate_ordinals[i],
                          (unsigned long long)fsu_eligible_total);
            }
            max_faults = rate_ordinals.size();
            events_to_skip = 0;
            fixed_skip_mode = true;
        } else {
            // A bare F1/F2/F3 label without ordinals is exactly the
            // forbidden "change the tag only" case. countOnly is exempt: it
            // measures the stream before ordinals can exist.
            if (!count_only && (fsu_freq == "F1" || fsu_freq == "F2" ||
                                fsu_freq == "F3"))
                panic("CHAOSFPU: %s requires --fpu_rate_ordinals; changing "
                      "--fsu_freq alone is not rate semantics\n",
                      fsu_freq.c_str());
            if (rate_divisor != 0 || jitter_pct != 0)
                panic("CHAOSFPU: rate_divisor/jitter without ordinals\n");
        }
        if (probability <= 0.0f &&
            (!p.rateOrdinals.empty() || p.fsuRateDivisor != 0))
            panic("CHAOSFPU: rate mode requires probability > 0\n");

        // [FSU][D3] Precision + lane geometry. Every configuration mistake is
        // rejected here (fail closed) instead of silently injecting into the
        // wrong bits.
        std::string ferr;
        if (!chaos_fsu::parsePrecision(precision, precision_bits))
            panic("CHAOSFPU: unknown precision '%s' (expected fp64|fp32)\n",
                  precision.c_str());
        if (!chaos_fsu::laneGeometryValid(lane_width, lane_offset, ferr))
            panic("CHAOSFPU: %s\n", ferr.c_str());
        if (!bitseg.empty()) {
            const auto fr = chaos_fsu::fieldRange(bitseg, precision_bits);
            if (!fr.valid)
                panic("CHAOSFPU: unknown bitseg '%s' for precision '%s'\n",
                      bitseg.c_str(), precision.c_str());
            if (fr.hi >= lane_width)
                panic("CHAOSFPU: field '%s' range [%d,%d] does not fit "
                      "lane_width %d\n", bitseg.c_str(), fr.lo, fr.hi,
                      lane_width);
        }
        if (fault_mask &&
            !chaos_fsu::validateExplicitMask(fault_mask, lane_width,
                                             lane_offset, ferr))
            panic("CHAOSFPU: %s\n", ferr.c_str());
        if (precision_bits > lane_width)
            panic("CHAOSFPU: precision %s requires lane_width >= %d "
                  "(got %d)\n", precision.c_str(), precision_bits,
                  lane_width);
        // [FSU][FR07-HOOK v2] The pre-PRF-write hook is a distinct, explicit
        // mode. It must not silently coexist with modes that bypass the
        // writeback path or mint multiple faults.
        if (prf_wb_hook) {
            // countOnly is allowed: the census run must measure the same
            // eligible stream, and maybeArm() returns false in that mode.
            if (permanent_stuck || rate_mode || recurring_stuck ||
                fma_weighted || rounding_sub || f3_dependent || fpsr_suppress)
                panic("CHAOSFPU: prfWbHook is incompatible with "
                      "permanent_stuck/rate/recurringStuck/fmaWeighted/"
                      "roundingSub/f3Dependent/fpsrSuppress\n");
            if (!fault_mask)
                panic("CHAOSFPU: prfWbHook requires an explicit faultMask\n");
            std::string hferr;
            if (!chaos_fsu::buildExplicitMask(fault_mask, lane_width,
                                              lane_offset, hook_mi, hferr))
                panic("CHAOSFPU: prfWbHook mask: %s\n", hferr.c_str());
            hook_mi_ok = true;
        }
        // Ambiguous mode combinations would make the emitted `field`
        // disagree with the actual mask. Reject them instead of guessing.
        if (!bitseg.empty() && (fault_mask || recurring_stuck ||
                                fma_weighted || rounding_sub))
            panic("CHAOSFPU: bitseg cannot be combined with explicit "
                  "fault_mask/recurring_stuck/fma_weighted/rounding_sub\n");
        // These legacy modes are FP64 low-lane proxies; refuse to label
        // them as FP32/lane-aware evidence.
        if (rounding_sub && (precision != "fp64" || lane_width != 64 ||
                             lane_offset != 0))
            panic("CHAOSFPU: rounding_sub is FP64/lane64/offset0 only\n");
        if (f3_dependent && (precision != "fp64" || lane_width != 64 ||
                             lane_offset != 0))
            panic("CHAOSFPU: f3_dependent is FP64/lane64/offset0 only\n");

        // [FSU][FP06] Explicit opClass / regClass filters. Unknown names are
        // a configuration error, never silently ignored (fail closed).
        if (!p.opClasses.empty()) {
            std::stringstream ss(p.opClasses);
            std::string tok;
            while (std::getline(ss, tok, ',')) {
                if (tok.empty())
                    panic("CHAOSFPU: empty opClasses token in '%s'\n",
                          p.opClasses.c_str());
                OpClass oc;
                if (!opClassFromName(tok, oc))
                    panic("CHAOSFPU: unknown opClasses name '%s'\n",
                          tok.c_str());
                if (std::find(op_class_allow.begin(), op_class_allow.end(),
                              (int)oc) == op_class_allow.end())
                    op_class_allow.push_back((int)oc);
            }
            if (op_class_allow.empty())
                panic("CHAOSFPU: opClasses parsed to an empty allowlist\n");
        }
        if (!regClassFromName(p.regClass, required_reg_class))
            panic("CHAOSFPU: unknown regClass '%s' (expected any|vec|float|"
                  "vec_elem or empty)\n", p.regClass.c_str());
        // opClasses and regClass are orthogonal: scalar FP opClasses may use
        // the VecReg storage class on AArch64, so a cross product is valid.

        // [FSU][F5] Permanent stuck-at (one install, many exposures).
        // Fail closed on every ambiguous configuration: this mode MUST NOT
        // be a relabeled rate/random mode, and it MUST NOT fall back to XOR
        // (a stuck cell forces a polarity; it never flips).
        if (permanent_stuck) {
            if (!count_only && fsu_freq != "F5")
                panic("CHAOSFPU: permanentStuck requires --fsu_freq F5, "
                      "got '%s'\n", fsu_freq.c_str());
            if (probability != 1.0f)
                panic("CHAOSFPU: permanentStuck requires probability=1.0 "
                      "(every eligible event after warm-up is an exposure)\n");
            if (fault_mask == 0)
                panic("CHAOSFPU: permanentStuck requires an explicit "
                      "fixed faultMask (one fixed mask for the whole run)\n");
            if (stuck_polarity < -1 || stuck_polarity > 1)
                panic("CHAOSFPU: stuckPolarity must be -1 (draw once), 0 "
                      "(SA0) or 1 (SA1), got %d\n", stuck_polarity);
            if (max_faults > 1)
                panic("CHAOSFPU: permanentStuck installs exactly one fault; "
                      "maxFaults must be 0 or 1, got %llu\n",
                      (unsigned long long)max_faults);
            if (rate_mode || recurring_stuck || rounding_sub ||
                f3_dependent || fpsr_suppress || fma_weighted)
                panic("CHAOSFPU: permanentStuck is incompatible with "
                      "rate/recurring_stuck/rounding_sub/f3_dependent/"
                      "fpsr_suppress/fma_weighted\n");
            if (!bitseg.empty())
                panic("CHAOSFPU: permanentStuck uses the explicit faultMask; "
                      "bitseg is not allowed\n");
            if (p.eventsToSkip != ~0ULL)
                panic("CHAOSFPU: permanentStuck uses f5Warmup, not "
                      "eventsToSkip\n");
            // Bounded evidence: mandatory first/first-activated events plus
            // the first/last sample budget must stay well below the
            // authoritative PROP-EVT cap (200000) so a run can never be
            // silently truncated by EVENT_CAP. The arithmetic lives in the
            // pure header helper (unit-tested on the host) so the runtime
            // panic and the offline audit cannot drift.
            const auto budget = chaos_fsu::f5ResolveSampleBudget(
                f5_sample_limit, f5_keep_first_last_n);
            if (!budget.within_cap)
                panic("CHAOSFPU: permanentStuck sample budget %llu exceeds "
                      "the auditable PROP-EVT budget (%llu of %llu)\n",
                      (unsigned long long)budget.total_with_mandatory,
                      (unsigned long long)chaos_fsu::F5_AUDITABLE_BUDGET,
                      (unsigned long long)chaos_fsu::F5_EVENT_CAP);
            f5_keep_first = budget.keep_first;
            f5_keep_last = budget.keep_last;
        } else {
            if (stuck_polarity != -1)
                panic("CHAOSFPU: stuckPolarity requires permanentStuck\n");
            if (f5_warmup != 0 || f5_sample_limit != 0 ||
                f5_keep_first_last_n != 0)
                panic("CHAOSFPU: f5Warmup/f5SampleLimit/f5KeepFirstLastN "
                      "require permanentStuck\n");
        }
        // A bare F5 tag without permanentStuck is exactly the forbidden
        // "change the tag only" case (countOnly is exempt: it measures the
        // stream before the mode is armed).
        if (!count_only && fsu_freq == "F5" && !permanent_stuck)
            panic("CHAOSFPU: --fsu_freq F5 requires permanentStuck; changing "
                  "the tag alone is not permanent-stuck semantics\n");
    }

    CHAOSFPU::~CHAOSFPU()
    {
        // v1.1 Phase 8.2 countOnlyMode: the driver's dry-run learns
        // N_eligible from this line (campaign.py parses the log).
        if (count_only && log_stream && log_stream->stream())
            dumpCensus(*(log_stream->stream()));
    }

    void
    CHAOSFPU::dumpCensus(std::ostream &os) const
    {
        os << "CHAOS_ELIGIBLE_COUNT=" << eligible_count << "\n";
        // [FSU][FP06] Per-opClass / per-regClass eligible counts. Only the
        // FILTERED stream is counted: a name outside the allowlist can never
        // appear, and the counts must sum to CHAOS_ELIGIBLE_COUNT.
        for (const auto &kv : eligible_opclass_counts)
            os << "CHAOS_ELIGIBLE_OPCLASS " << kv.first << "=" << kv.second
               << "\n";
        for (const auto &kv : eligible_regclass_counts)
            os << "CHAOS_ELIGIBLE_REGCLASS " << kv.first << "=" << kv.second
               << "\n";
        // [FSU][FP08] Early-return proxy accounting. `attempted` is every
        // eligible event reaching the mode; `applied` is a real modeled
        // effect; `suppressed` is the fpsr placeholder (arch FPSR is not
        // modeled in SE). Conservation is checked by the gate.
        if (fpsr_suppress) {
            os << "CHAOS_FPSR_ATTEMPTED=" << fpsr_attempted << "\n";
            os << "CHAOS_FPSR_APPLIED=" << fpsr_applied << "\n";
            os << "CHAOS_FPSR_SUPPRESSED=" << suppressed_count << "\n";
            os << "CHAOS_FPSR_REASON=fpsr_not_architecturally_modeled\n";
        }
        if (rounding_sub) {
            os << "CHAOS_ROUNDING_ATTEMPTED=" << rounding_attempted << "\n";
            os << "CHAOS_ROUNDING_APPLIED=" << rounding_applied << "\n";
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

    static bool isSimdOpClass(OpClass oc) {
        return oc == SimdFloatAddOp || oc == SimdFloatAluOp ||
               oc == SimdFloatCmpOp || oc == SimdFloatCvtOp ||
               oc == SimdFloatMultOp || oc == SimdFloatMultAccOp ||
               oc == SimdFloatDivOp || oc == SimdFloatSqrtOp ||
               oc == SimdFloatMiscOp;
    }

    // [FSU][FP06] The ONLY opClass names accepted by --fpu_op_classes. This
    // is exactly the injector's FP-domain (scalar Float* + SIMD FP).
    struct OpClassName { const char *name; OpClass oc; };
    static const OpClassName kOpClassNames[] = {
        {"FloatAdd", FloatAddOp},
        {"FloatCmp", FloatCmpOp},
        {"FloatCvt", FloatCvtOp},
        {"FloatMult", FloatMultOp},
        {"FloatMultAcc", FloatMultAccOp},
        {"FloatDiv", FloatDivOp},
        {"FloatMisc", FloatMiscOp},
        {"FloatSqrt", FloatSqrtOp},
        {"SimdFloatAdd", SimdFloatAddOp},
        {"SimdFloatAlu", SimdFloatAluOp},
        {"SimdFloatCmp", SimdFloatCmpOp},
        {"SimdFloatCvt", SimdFloatCvtOp},
        {"SimdFloatMult", SimdFloatMultOp},
        {"SimdFloatMultAcc", SimdFloatMultAccOp},
        {"SimdFloatDiv", SimdFloatDivOp},
        {"SimdFloatSqrt", SimdFloatSqrtOp},
        {"SimdFloatMisc", SimdFloatMiscOp},
    };

    static bool opClassFromName(const std::string &name, OpClass &out) {
        for (const auto &e : kOpClassNames) {
            if (name == e.name) {
                out = e.oc;
                return true;
            }
        }
        return false;
    }

    static const char *opClassName(OpClass oc) {
        for (const auto &e : kOpClassNames) {
            if (oc == e.oc)
                return e.name;
        }
        return "unknown";
    }

    static bool regClassFromName(const std::string &name, int &out) {
        if (name.empty() || name == "any") { out = -1; return true; }
        if (name == "vec")      { out = (int)VecRegClass;    return true; }
        if (name == "float")    { out = (int)FloatRegClass;  return true; }
        if (name == "vec_elem") { out = (int)VecElemClass;   return true; }
        return false;
    }

    static const char *regClassName(int cls) {
        if (cls == VecRegClass) return "vec";
        if (cls == VecElemClass) return "vec_elem";
        if (cls == FloatRegClass) return "float";
        return "unknown";
    }

    static std::string precisionName(int bits) {
        if (bits == 32) return "fp32";
        if (bits == 64) return "fp64";
        if (bits == 16) return "fp16";
        return "none";
    }

    static chaos_fsu::FpFamily familyOf(OpClass oc) {
        switch (oc) {
          case FloatAddOp: case FloatCmpOp: case FloatMultOp:
          case FloatMultAccOp: case FloatDivOp: case FloatMiscOp:
          case FloatSqrtOp:
            return chaos_fsu::FpFamily::ScalarFloat;
          case FloatCvtOp:
            return chaos_fsu::FpFamily::Cvt;
          case SimdFloatAluOp: case SimdFloatCmpOp: case SimdFloatCvtOp:
          case SimdFloatMultOp: case SimdFloatMultAccOp: case SimdFloatDivOp:
          case SimdFloatSqrtOp: case SimdFloatMiscOp:
          case SimdFloatAddOp:
            if (oc == SimdFloatCvtOp)
                return chaos_fsu::FpFamily::Cvt;
            return chaos_fsu::FpFamily::SimdFloat;
          default:
            return chaos_fsu::FpFamily::Other;
        }
    }

    // Decode the REAL dynamic AArch64 instruction. Returns false when the
    // encoding is not available or not reliably classifiable; callers must
    // fail closed when decode_guard is enabled.
    static bool decodeInstInfo(o3::DynInst *inst,
                               chaos_fsu::DecodedFp &dec, uint32_t &enc)
    {
        dec = chaos_fsu::DecodedFp();
        enc = 0;
        if (!inst || !inst->staticInst) {
            dec.reason = "no-static-inst";
            return false;
        }
        auto *asi = dynamic_cast<const ArmISA::ArmStaticInst *>(
            inst->staticInst.get());
        if (!asi) {
            dec.reason = "not-arm-static-inst";
            return false;
        }
        enc = asi->encoding();
        dec = chaos_fsu::decodedPrecision(enc, familyOf(inst->opClass()));
        return dec.reliable;
    }

    bool
    CHAOSFPU::maybeCorrupt(o3::DynInst *dyn_inst)
    {
        // [FSU][FR07-HOOK v2] In hook mode the decision/arming happened
        // before execute; this call only commits the shadow WB data (with the
        // mask applied) to the PRF and emits the L0 evidence.
        // countOnly is the census pass: it must use the legacy eligible
        // stream (maybeArm() is inert there), so only the injection run
        // finalizes the shadow WB.
        if (prf_wb_hook && !count_only) return finalizeWb(dyn_inst);
        if (!cpu || probability <= 0.0f) return false;
        // [FSU][F5] maxFaults bounds INSTALLATIONS, not exposures: after the
        // single install every eligible event is an exposure of the same
        // fault and must still be forced.
        if (!permanent_stuck && !count_only && max_faults != 0 &&
            faults_injected_count >= max_faults)
            return false;
        if (!inWindow()) return false;
        OpClass oc = dyn_inst->opClass();
        if (!isFpOpClass(oc)) return false;
        // [FSU][FP06] Explicit opClass allowlist. Empty = legacy (every FP
        // opClass accepted). A non-matching candidate is not eligible and is
        // not counted anywhere (the census counts only the filtered stream).
        if (!op_class_allow.empty() &&
            std::find(op_class_allow.begin(), op_class_allow.end(),
                      (int)oc) == op_class_allow.end())
            return false;

        // v1.1 Phase 9 patch 1a-0: with the PRF-dest rewrite the corruptible
        // stream is 'inst has an FP/vector destination register' — checkable
        // directly from the dest-reg list (no InstResult involved).
        // [FSU][FP06] `regClass` restricts the TARGET dest class. The target
        // is the first FP/vector dest whose class matches the filter (the
        // injection loop below applies the same rule, so eligibility and
        // injection can never pick different registers).
        int target_class = -1;
        for (int i = 0; i < dyn_inst->numDestRegs(); i++) {
            PhysRegIdPtr d = dyn_inst->renamedDestIdx(i);
            if (d && !d->is(InvalidRegClass) &&
                (d->classValue() == VecRegClass ||
                 d->classValue() == FloatRegClass ||
                 d->classValue() == VecElemClass) &&
                regClassMatches((int)d->classValue())) {
                target_class = (int)d->classValue();
                break;
            }
        }
        const bool has_fp_dest = target_class >= 0;

        // A non-zero lane offset only makes sense for a SIMD instruction;
        // scalar FP results use lane 0 (AArch64 scalar FP is stored in a
        // VecReg container whose upper lanes are zero padding). Keep the
        // countOnly and injection streams on the SAME predicate.
        // [FSU][D3] Decode the REAL instruction. The guard only changes the
        // eligible stream when explicitly enabled; otherwise the decoded
        // facts are still recorded so a mismatch is visible, never silent.
        const bool want_decode = decode_guard || !fsu_model.empty();
        chaos_fsu::DecodedFp dec;
        uint32_t dec_enc = 0;
        bool dec_ok = true, dec_pm = false, dec_lm = false;
        if (want_decode) {
            dec_ok = decodeInstInfo(dyn_inst, dec, dec_enc);
            if (dec_ok) {
                dec_pm = dec.precision_bits == precision_bits;
                if (dec.kind == chaos_fsu::FpKind::ScalarVfp) {
                    dec_lm = lane_offset == 0 &&
                        (lane_width == dec.element_width ||
                         (dec.element_width == 32 && lane_width == 64));
                } else if (dec.kind == chaos_fsu::FpKind::NeonVector) {
                    dec_lm = lane_width == dec.element_width &&
                             lane_offset >= 0 && lane_offset < dec.lanes;
                }
                ++decode_kind_counts[chaos_fsu::fpKindName(dec.kind)];
            } else {
                ++decode_kind_counts["unreliable"];
            }
            const bool matched = dec_ok && dec_pm && dec_lm;
            if (has_fp_dest && !matched) {
                ++decode_reject_count;
                const std::string why = !dec_ok
                    ? std::string("undecoded:") + dec.reason
                    : (!dec_pm ? "precision_mismatch" : "lane_mismatch");
                ++decode_reject_reasons[why];
                if (decode_reject_count <= 16 && log_stream &&
                    log_stream->stream()) {
                    std::ostringstream os;
                    os << "Tick: " << curTick()
                       << ", Site: dyn_inst_execute, sn=" << dyn_inst->seqNum
                       << ", pc=0x" << std::hex
                       << dyn_inst->pcState().instAddr() << std::dec
                       << ", decode_reject=" << why
                       << ", enc=0x" << std::hex << dec_enc << std::dec
                       << ", decoded_kind="
                       << chaos_fsu::fpKindName(dec.kind)
                       << ", decoded_precision="
                       << precisionName(dec.precision_bits)
                       << ", decoded_width=" << dec.element_width
                       << ", decoded_lanes=" << dec.lanes
                       << ", manifest_precision=" << precision
                       << ", manifest_lane_width=" << lane_width
                       << ", manifest_lane_offset=" << lane_offset
                       << std::endl;
                    *(log_stream->stream()) << os.str();
                }
            }
            if (decode_guard)
                dec_ok = matched;
        }

        const bool lane_mode = lane_offset != 0;
        const bool eligible = has_fp_dest && dec_ok &&
                              (!lane_mode || isSimdOpClass(oc));

        // v1.1 Phase 8.2 countOnlyMode: count only CORRUPTIBLE eligible
        // events (no FP/vector dest = can never take the fault); never
        // corrupt. The counted stream is identical to the stream the
        // fixed-skip draw indexes into.
        if (count_only) {
            if (eligible) {
                ++eligible_count;
                ++eligible_opclass_counts[opClassName(oc)];
                ++eligible_regclass_counts[regClassName(target_class)];
            }
            return false;
        }

        // [FSU][F5] Permanent stuck-at: warm-up counts eligible events; the
        // first eligible event AFTER the warm-up installs the fault, and
        // every later eligible event is an exposure. No probability, no
        // skip, no new fault_id.
        if (permanent_stuck) {
            if (!eligible) return false;
            ++eligible_ordinal;
            if (eligible_ordinal <= f5_warmup) return false;
            injected_eligible_ordinal = eligible_ordinal;
        } else if (rate_mode) {
            if (!eligible) return false;
            ++eligible_ordinal;
            if (next_rate_index >= rate_ordinals.size())
                return false;   // max_faults already enforced above
            const uint64_t target = rate_ordinals[next_rate_index];
            if (eligible_ordinal < target)
                return false;
            if (eligible_ordinal > target)
                panic("CHAOSFPU: rate ordinal %llu missed (eligible now "
                      "%llu)\n", (unsigned long long)target,
                      (unsigned long long)eligible_ordinal);
            const uint64_t prev = next_rate_index == 0
                ? rate_warmup : rate_ordinals[next_rate_index - 1];
            current_interval = target - prev;
            current_ordinal_index = next_rate_index;
            injected_eligible_ordinal = target;
        } else {
            // v1.1 Phase 8.2 fixed-skip mode: consume the skip ONLY on
            // corruptible events so skip indexes the same stream countOnly
            // counted. Legacy geometric mode keeps the old consume-on-
            // eligible behavior (byte-identical replays for existing
            // campaigns).
            if (fixed_skip_mode && !eligible) return false;

            // Sampling-bias fix (findings.md Phase 3.0): skip the first N
            // eligible events (N ~ geometric(0.1) from the seed) so the
            // single fault lands on a seed-dependent event.
            if (events_to_skip > 0) {
                --events_to_skip;
                return false;
            }

            std::uniform_real_distribution<float> pd(0.0f, 1.0f);
            if (pd(rng) > probability) return false;
        }

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
        // v1.1 Phase 9 mode 6 — fpsr_suppress (E3 placeholder): the arch
        // FPSR is only observable via an MRS read, which SE kernels never
        // take — count the suppressed-flag events honestly and corrupt
        // nothing. (A real arm would need an MRS-consuming kernel.)
        if (fpsr_suppress) {
            // [FSU][FP08] Honest proxy accounting: there is no architectural
            // FPSR write in SE kernels, so "applied" means the modeled flag
            // was cleared. The counts are emitted at exit and the event says
            // exactly that; this path never mints a certified fault.
            ++fpsr_attempted;
            ++suppressed_count;
            ++fpsr_applied;
            std::vector<std::pair<std::string, std::string>> kv = {
                {"field", "fpsr_suppress"},
                {"attempted", "1"},
                {"applied", "1"},
                {"suppressed", "1"},
                {"reason", "fpsr_not_architecturally_modeled"},
                {"injection_site", "fpsr_suppress_proxy"},
                {"hook_version", "1"},
                {"dyn_inst_seq", std::to_string(dyn_inst->seqNum)},
                {"op_class", opClassName(oc)},
            };
            emitFsu("suppress", 0, ~0ULL, kv);
            return false;
        }

        // v1.1 Phase 9 mode 4 — rounding_sub: one-ULP nudge to the
        // OPPOSITE neighbor of the rounded result (E3 proxy for a flipped
        // FPCR RMODE changing one rounding decision). Applies to the first
        // FP/vector dest.
        if (rounding_sub) {
            ++rounding_attempted;
            bool okr = false;
            PhysRegIdPtr rdest = nullptr;
            uint64_t rbits = 0, robits = 0;
            auto *o3cpur = dynamic_cast<o3::CPU *>(cpu);
            if (o3cpur) {
              for (int i = 0; i < dyn_inst->numDestRegs() && !okr; i++) {
                PhysRegIdPtr dest = dyn_inst->renamedDestIdx(i);
                if (!dest || dest->is(InvalidRegClass)) continue;
                if (dest->classValue() != VecRegClass) continue;
                void *vp = o3cpur->getWritableReg(dest,
                                                  dyn_inst->threadNumber);
                if (!vp) continue;
                uint64_t bits; std::memcpy(&bits, vp, 8);
                double d; std::memcpy(&d, vp, 8);
                if (!std::isfinite(d)) continue;
                double other = (bits & 1)
                    ? std::nextafter(d, -std::numeric_limits<double>::infinity())
                    : std::nextafter(d,  std::numeric_limits<double>::infinity());
                uint64_t obits; std::memcpy(&obits, &other, 8);
                std::memcpy(vp, &obits, 8);
                okr = true;
                rdest = dest;
                rbits = bits;
                robits = obits;
              }
            }
            if (okr) {
                ++rounding_applied;
                faults_injected_count++;
                // [FSU][FP08] Connect the early-return path to the real L0/L1
                // events so the proxy has an auditable chain boundary. It is
                // labelled as a one-ULP rounding proxy, never as a hardware
                // RMODE fault.
                FaultInfo fi;
                fi.reg_class = (int)VecRegClass;
                fi.reg_index = (int)rdest->index();
                fi.before = rbits;
                fi.after = robits;
                fi.mask = rbits ^ robits;
                fi.precision_bits = precision_bits;
                fi.lane_width = lane_width;
                fi.lane_offset = lane_offset;
                fi.full_before_lo = rbits;
                fi.full_after_lo = robits;
                fi.is_vec = true;
                fi.field = "rounding_sub";
                fi.op_class = opClassName(oc);
                fi.injection_site = "rounding_sub_one_ulp_proxy";
                fi.hook_version = "1";
                fi.producer_sn = dyn_inst->seqNum;
                noteFaultApplied(dyn_inst, fi);
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: dyn_inst_execute, opClass=" << (int)oc
                        << ", sn=" << dyn_inst->seqNum
                        << ", mode=rounding_sub, faults_injected: "
                        << faults_injected_count << std::endl;
                }
            }
            return okr;
        }

        // [FSU][D3] Build a lane-relative mask and its absolute 128-bit
        // position. The field table is selected by precision; lane geometry
        // and field fit were already validated in the constructor.
        chaos_fsu::MaskInfo mi;
        std::string ferr;
        const bool field_mode = !bitseg.empty();
        int field_lo = -1, field_hi = -1;

        auto mask_fail = [&](const std::string &why) {
            panic("CHAOSFPU: %s\n", why.c_str());
        };

        if (permanent_stuck) {
            // The explicit faultMask is the one permanent mask. It is
            // validated once in the constructor and reused verbatim.
            if (!chaos_fsu::buildExplicitMask(fault_mask, lane_width,
                                              lane_offset, mi, ferr))
                mask_fail(ferr);
        } else if (recurring_stuck) {
            // v1.1 Phase 9 mode 3 — the SAME fixed mask every event: the
            // directed --fault_mask if given, else drawn once from the
            // uniform pick and reused for the whole run.
            if (!recurring_mask_drawn) {
                recurring_mask = fault_mask ? fault_mask
                    : (1ULL << (rng() % (unsigned)lane_width));
                recurring_mask_drawn = true;
            }
            if (!chaos_fsu::buildExplicitMask(recurring_mask, lane_width,
                                              lane_offset, mi, ferr))
                mask_fail(ferr);
        } else if (fault_mask) {
            if (!chaos_fsu::buildExplicitMask(fault_mask, lane_width,
                                              lane_offset, mi, ferr))
                mask_fail(ferr);
        } else if (fma_weighted) {
            // v1.1 Phase 9 mode 2 — fma_intermediate (E3 behavioral
            // proxy, plan fallback (b)): draw the field from method3's
            // matched distribution (mant 85% / exp 10% / sign 5%), then
            // the bit uniformly within the field. Field ranges are
            // precision-aware (FP32: mant 23 bits, exp 8 bits).
            unsigned f = (unsigned)(rng() % 100);
            if (f < 85) {
                field_lo = 0;
                field_hi = precision_bits == 64 ? 51 : 22;
            } else if (f < 95) {
                field_lo = precision_bits == 64 ? 52 : 23;
                field_hi = precision_bits == 64 ? 62 : 30;
            } else {
                field_lo = field_hi = precision_bits - 1;
            }
            if (field_hi >= lane_width)
                mask_fail("fma_intermediate field does not fit lane_width");
            const int bit = field_lo +
                (int)(rng() % (unsigned)(field_hi - field_lo + 1));
            if (!chaos_fsu::buildSingleBitMask(lane_width, lane_offset, bit,
                                               mi, ferr))
                mask_fail(ferr);
        } else if (field_mode) {
            const auto fr = chaos_fsu::fieldRange(bitseg, precision_bits);
            field_lo = fr.lo;
            field_hi = fr.hi;
            const int bit = fr.lo +
                (int)(rng() % (unsigned)(fr.hi - fr.lo + 1));
            if (!chaos_fsu::buildFieldMask(bitseg, precision_bits, lane_width,
                                           lane_offset, bit, mi, ferr))
                mask_fail(ferr);
        } else {
            const int bit = (int)(rng() % (unsigned)lane_width);
            if (!chaos_fsu::buildSingleBitMask(lane_width, lane_offset, bit,
                                               mi, ferr))
                mask_fail(ferr);
        }

        // [FSU][F5] The polarity is fixed at installation. If the user did
        // not pin it, draw it ONCE here from the seeded RNG and never draw
        // again; every later exposure reuses f5_polarity.
        int f5_pol = f5_polarity;
        if (permanent_stuck && !f5_armed) {
            f5_pol = stuck_polarity >= 0 ? stuck_polarity
                                         : (int)(rng() % 2);
        }

        FaultInfo info;
        info.mask = mi.lane_mask;
        info.precision_bits = precision_bits;
        info.lane_width = lane_width;
        info.lane_offset = lane_offset;
        info.bit_in_lane = mi.bit_in_lane;
        info.abs_bit = mi.abs_bit;
        info.field_lo = field_lo;
        info.field_hi = field_hi;
        info.abs_lo = mi.abs_lo;
        info.abs_hi = mi.abs_hi;
        info.instruction_bits = dec_enc;
        info.op_class = opClassName(oc);
        if (want_decode) {
            info.decoded_kind = chaos_fsu::fpKindName(dec.kind);
            info.decoded_precision_bits = dec.precision_bits;
            info.decoded_element_width = dec.element_width;
            info.decoded_lanes = dec.lanes;
            info.decoded_reliable = dec.reliable;
            info.precision_match = dec_pm;
            info.lane_match = dec_lm;
        }
        if (permanent_stuck) {
            // A SINGLE-bit mask that fits one IEEE754 field is named by
            // that field; a multi-bit mask (FP06-c fixed mantissa) stays
            // "permanent_stuck" and is expressed by `fixed_mask`. The seed
            // audit validates a named field against fault_mask == 1<<bit,
            // so the label must never disagree with a multi-bit mask.
            info.field = "permanent_stuck";
            if (mi.lane_mask) {
                info.field_lo = __builtin_ctzll(mi.lane_mask);
                info.field_hi = 63 - __builtin_clzll(mi.lane_mask);
            }
            if (__builtin_popcountll(mi.lane_mask) == 1) {
                static const char *const segs[] = {
                    "sign", "exp_hi", "exp_lo",
                    "mant_hi", "mant_mid", "mant_lo"
                };
                for (const char *seg : segs) {
                    const auto r = chaos_fsu::fieldRange(
                        seg, precision_bits);
                    if (!r.valid || r.hi >= lane_width)
                        continue;
                    uint64_t fm = 0;
                    for (int b = r.lo; b <= r.hi; ++b)
                        fm |= ((uint64_t)1 << b);
                    if ((mi.lane_mask & ~fm) == 0) {
                        info.field = seg;
                        // The SINGLE-bit mask lies inside this named IEEE
                        // field. field_lo/hi describe the FIELD's full
                        // range (the audit validates the name against this
                        // range); bit_in_lane + fault_mask still describe
                        // the exact targeted bit.
                        info.field_lo = r.lo;
                        info.field_hi = r.hi;
                        break;
                    }
                }
            }
        } else {
            info.field = field_mode ? bitseg :
                (recurring_stuck ? "recurring_result_stuck" :
                 fma_weighted ? "fma_intermediate" :
                 rounding_sub ? "rounding_sub" : "uniform");
        }

        bool ok = false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu)
            panic("CHAOSFPU: cpu is not an O3CPU\n");
        if (o3cpu->physRegFile().vecRegBytes() < 16)
            panic("CHAOSFPU: vector register storage is %zu bytes, need "
                  ">=16 for a 128-bit lane inject\n",
                  o3cpu->physRegFile().vecRegBytes());
        // v1.1 Phase 9 mode 5 — f3_data_dependent gate: corrupt only when
        // the first FP/vector dest's biased exponent is inside
        // [exp_lo, exp_hi] (the --fpu_operand_range proxy; the trigger
        // VALUE pattern needs the operands, which are gone post-execute —
        // the result exponent is the honest post-hoc proxy).
        if (f3_dependent && (exp_lo >= 0 || exp_hi >= 0)) {
            int dexp = -1;
            for (int i = 0; i < dyn_inst->numDestRegs() && dexp < 0; i++) {
                PhysRegIdPtr dest = dyn_inst->renamedDestIdx(i);
                if (!dest || dest->is(InvalidRegClass)) continue;
                if (dest->classValue() != VecRegClass) continue;
                void *vp = o3cpu->getWritableReg(dest,
                                                 dyn_inst->threadNumber);
                if (!vp) continue;
                uint64_t bits; std::memcpy(&bits, vp, 8);
                dexp = (int)((bits >> 52) & 0x7ff);
            }
            if (dexp < 0) return false;
            if (exp_lo >= 0 && dexp < exp_lo) return false;
            if (exp_hi >= 0 && dexp > exp_hi) return false;
        }
        for (int i = 0; i < dyn_inst->numDestRegs() && !ok; i++) {
            PhysRegIdPtr dest = dyn_inst->renamedDestIdx(i);
            if (!dest || dest->is(InvalidRegClass)) continue;
            // [FSU][FP06] Same regClass predicate as eligibility.
            if (!regClassMatches((int)dest->classValue())) continue;
            switch (dest->classValue()) {
              case VecRegClass: {
                // Full 128-bit vector register: read/write only the selected
                // lane. All other lanes stay byte-identical.
                void *vp = o3cpu->getWritableReg(dest,
                                                 dyn_inst->threadNumber);
                if (!vp) break;
                unsigned char before[16], after[16];
                std::memcpy(before, vp, 16);
                std::memcpy(after, vp, 16);
                const int lane_bytes = lane_width / 8;
                const int base = lane_offset * lane_bytes;
                uint64_t lane_before = 0, lane_after = 0;
                std::memcpy(&lane_before, before + base, lane_bytes);
                // [FSU][F5] Stuck-at forces a polarity (SA0: &~mask,
                // SA1: |mask); it is NOT XOR. Non-target bits and all other
                // lanes stay byte-identical.
                lane_after = permanent_stuck
                    ? chaos_fsu::applyStuck(lane_before, mi.lane_mask, f5_pol)
                    : lane_before ^ mi.lane_mask;
                std::memcpy(after + base, &lane_after, lane_bytes);
                std::memcpy(vp, after, 16);
                std::memcpy(&info.full_before_lo, before, 8);
                std::memcpy(&info.full_before_hi, before + 8, 8);
                std::memcpy(&info.full_after_lo, after, 8);
                std::memcpy(&info.full_after_hi, after + 8, 8);
                info.before = lane_before;
                info.after = lane_after;
                info.reg_class = (int)dest->classValue();
                info.reg_index = dest->index();
                info.is_vec = true;
                ok = true;
                break;
              }
              case FloatRegClass:
              case VecElemClass: {
                // Scalar FP register / vector element: scalar storage has no
                // lane offset; lane_width 32 preserves the upper 32 bits.
                if (lane_offset != 0)
                    panic("CHAOSFPU: scalar dest requires lane_offset=0 "
                          "(got %d)\n", lane_offset);
                if (lane_width != 32 && lane_width != 64)
                    panic("CHAOSFPU: scalar dest requires lane_width 32 or "
                          "64 (got %d)\n", lane_width);
                RegVal v = o3cpu->getReg(dest, dyn_inst->threadNumber);
                const uint64_t width_mask =
                    chaos_fsu::laneMaskForWidth(lane_width);
                const uint64_t oldv = (uint64_t)v;
                const uint64_t lane_before = oldv & width_mask;
                const uint64_t lane_after = permanent_stuck
                    ? chaos_fsu::applyStuck(lane_before, mi.lane_mask, f5_pol)
                    : lane_before ^ mi.lane_mask;
                const uint64_t newv =
                    (oldv & ~width_mask) | lane_after;
                o3cpu->setReg(dest, (RegVal)newv, dyn_inst->threadNumber);
                info.before = lane_before;
                info.after = lane_after;
                info.full_before_lo = oldv;
                info.full_after_lo = newv;
                info.reg_class = (int)dest->classValue();
                info.reg_index = dest->index();
                info.is_vec = false;
                ok = true;
                break;
              }
              default:
                break;  // int/cond/misc dests are CHAOSExec's scope
            }
        }
        if (!ok) {
            // [FSU][F5] A matched post-warmup eligible event with no writable
            // FP/vector destination cannot carry an exposure. Count it
            // explicitly instead of letting it silently disappear from the
            // eligible accounting (post_install_eligible =
            // exposures_total + eligible_without_writable_dest).
            if (permanent_stuck && eligible_ordinal > f5_warmup)
                ++f5_eligible_without_writable_dest;
            if (rate_mode)
                panic("CHAOSFPU: rate ordinal %llu matched but no writable "
                      "FP/vector dest (fault not applied)\n",
                      (unsigned long long)injected_eligible_ordinal);
            return false;  // no FP/vector dest register on this inst
        }
        if (permanent_stuck) {
            // Install once (fixed fault_id/mask/polarity); every event after
            // that is an exposure of the SAME fault. noteFaultApplied is
            // deliberately NOT called per exposure: that would mint a new
            // fault_id for every event and turn one permanent defect into
            // thousands of independent faults.
            if (!f5_armed) {
                f5_fixed_mask = mi.lane_mask;
                f5_polarity = f5_pol;
            }
            notePermanentExposure(dyn_inst, info);
        } else {
            faults_injected_count++;
            noteFaultApplied(dyn_inst, info);
        }
        if (rate_mode) ++next_rate_index;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: dyn_inst_execute, opClass=" << (int)oc
                << ", sn=" << dyn_inst->seqNum
                << (bitseg.empty() ? std::string() : ", bitseg=" + bitseg)
                << (fma_weighted ? ", mode=fma_intermediate" : "")
                << (recurring_stuck ? ", mode=recurring_result_stuck" : "")
                << (permanent_stuck
                    ? ", mode=permanent_stuck, polarity=" +
                      std::to_string(f5_polarity) +
                      ", exposure=" + std::to_string(f5_exposures_total) +
                      ", activated_exposures=" +
                      std::to_string(f5_activated_total)
                    : std::string())
                << ", precision=" << precision
                << ", lane_width=" << lane_width
                << ", lane_offset=" << lane_offset
                << (want_decode
                    ? ", decoded_kind=" +
                      std::string(chaos_fsu::fpKindName(dec.kind))
                    : std::string())
                << (want_decode
                    ? std::string(", precision_match=") +
                      (dec_pm ? "1" : "0") + ", lane_match=" +
                      (dec_lm ? "1" : "0")
                    : std::string())
                << ", mask=0x" << std::hex << mi.lane_mask << std::dec
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    // ------------------------------------------------------------------
    // [FSU][FR07-HOOK v2] Real PRF writeback-data boundary.
    // ------------------------------------------------------------------

    bool
    CHAOSFPU::wbDestMatches(PhysRegIdPtr phys_reg, ThreadID tid) const
    {
        return wb.valid && phys_reg &&
               (int)phys_reg->classValue() == wb.reg_class &&
               (int)phys_reg->index() == wb.reg_index && tid == wb.tid;
    }

    void
    CHAOSFPU::cancelPendingArm()
    {
        wb = WbPending();
    }

    bool
    CHAOSFPU::maybeArm(o3::DynInst *dyn_inst)
    {
        if (!prf_wb_hook || !dyn_inst || !cpu) return false;
        if (wb.valid) cancelPendingArm();
        if (!hook_mi_ok)
            panic("CHAOSFPU: prfWbHook armed without a validated mask\n");
        if (permanent_stuck || count_only || rate_mode || recurring_stuck ||
            fma_weighted || rounding_sub || f3_dependent || fpsr_suppress)
            return false;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;
        if (!inWindow()) return false;
        // Predicated-off instructions must not install a writeback fault.
        if (!dyn_inst->readPredicate()) return false;

        const OpClass oc = dyn_inst->opClass();
        if (!isFpOpClass(oc)) return false;
        if (!op_class_allow.empty() &&
            std::find(op_class_allow.begin(), op_class_allow.end(),
                      (int)oc) == op_class_allow.end())
            return false;

        // First FP/vector destination matching the configured reg class:
        // exactly the same target the legacy path picks.
        int target = -1;
        int target_class = -1;
        for (int i = 0; i < dyn_inst->numDestRegs(); i++) {
            PhysRegIdPtr d = dyn_inst->renamedDestIdx(i);
            if (d && !d->is(InvalidRegClass) &&
                (d->classValue() == VecRegClass ||
                 d->classValue() == FloatRegClass ||
                 d->classValue() == VecElemClass) &&
                regClassMatches((int)d->classValue())) {
                target = i;
                target_class = (int)d->classValue();
                break;
            }
        }
        if (target < 0) return false;

        chaos_fsu::DecodedFp dec;
        uint32_t dec_enc = 0;
        bool dec_ok = true, dec_pm = false, dec_lm = false;
        const bool want_decode = decode_guard || !fsu_model.empty();
        if (want_decode) {
            dec_ok = false;
            auto *asi = dynamic_cast<const ArmISA::ArmStaticInst *>(
                dyn_inst->staticInst.get());
            if (asi) {
                dec_enc = asi->encoding();
                dec = chaos_fsu::decodedPrecision(dec_enc,
                                                  familyOf(dyn_inst->opClass()));
                dec_ok = dec.reliable;
            }
            if (dec_ok) {
                dec_pm = dec.precision_bits == precision_bits;
                if (dec.kind == chaos_fsu::FpKind::ScalarVfp) {
                    dec_lm = lane_offset == 0 &&
                        (lane_width == dec.element_width ||
                         (dec.element_width == 32 && lane_width == 64));
                } else if (dec.kind == chaos_fsu::FpKind::NeonVector) {
                    dec_lm = lane_width == dec.element_width &&
                             lane_offset >= 0 && lane_offset < dec.lanes;
                }
            }
            if (decode_guard) dec_ok = dec_ok && dec_pm && dec_lm;
        }
        const bool lane_mode = lane_offset != 0;
        const bool eligible = target >= 0 && dec_ok &&
                              (!lane_mode || isSimdOpClass(oc));
        if (!eligible) return false;

        // Same fixed-skip / probability selection as the legacy path, so the
        // injected dynamic event is the pre-registered one.
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) panic("CHAOSFPU: cpu is not an O3CPU\n");
        if (o3cpu->physRegFile().vecRegBytes() < 16)
            panic("CHAOSFPU: vector register storage is %zu bytes, need "
                  ">=16 for the PRF-WB hook\n",
                  o3cpu->physRegFile().vecRegBytes());

        PhysRegIdPtr dest = dyn_inst->renamedDestIdx(target);
        wb = WbPending();
        wb.valid = true;
        wb.seq = dyn_inst->seqNum;
        wb.tid = dyn_inst->threadNumber;
        wb.dest_operand = target;
        wb.reg_class = target_class;
        wb.reg_index = (int)dest->index();
        wb.lane_mask = hook_mi.lane_mask;
        wb.lane_width = lane_width;
        wb.lane_offset = lane_offset;
        wb.bit_in_lane = hook_mi.bit_in_lane;
        wb.abs_bit = hook_mi.abs_bit;
        wb.abs_lo = hook_mi.abs_lo;
        wb.abs_hi = hook_mi.abs_hi;
        wb.field_lo = hook_mi.lane_mask
            ? __builtin_ctzll(hook_mi.lane_mask) : -1;
        wb.field_hi = hook_mi.lane_mask
            ? 63 - __builtin_clzll(hook_mi.lane_mask) : -1;
        wb.enc = dec_enc;
        wb.op_class = opClassName(oc);
        wb.decoded_kind = chaos_fsu::fpKindName(dec.kind);
        wb.decoded_precision_bits = dec.precision_bits;
        wb.decoded_element_width = dec.element_width;
        wb.decoded_lanes = dec.lanes;
        wb.decoded_reliable = dec.reliable;
        wb.precision_match = dec_pm;
        wb.lane_match = dec_lm;
        wb.arm_tick = curTick();
        if (target_class == VecRegClass) {
            wb.vec_bytes = (int)o3cpu->physRegFile().vecRegBytes();
            if (wb.vec_bytes <= 0 ||
                wb.vec_bytes > WbPending::MAX_VEC_BYTES)
                panic("CHAOSFPU: vector register storage is %d bytes, "
                      "PRF-WB shadow supports <= %d\n", wb.vec_bytes,
                      WbPending::MAX_VEC_BYTES);
            // Snapshot the destination cell: the ISA will write the FU
            // result into the shadow, never into the PRF.
            o3cpu->getReg(dest, wb.shadow, dyn_inst->threadNumber);
        } else {
            RegVal v = o3cpu->getReg(dest, dyn_inst->threadNumber);
            std::memcpy(wb.shadow, &v, sizeof(v));
        }
        return true;
    }

    bool
    CHAOSFPU::shadowForWrite(PhysRegIdPtr phys_reg, ThreadID tid, void **out)
    {
        if (!wb.valid || !wbDestMatches(phys_reg, tid)) return false;
        if (wb.reg_class != VecRegClass) return false;
        wb.shadow_used = true;
        *out = (void *)wb.shadow;
        return true;
    }

    bool
    CHAOSFPU::interceptScalarWrite(PhysRegIdPtr phys_reg, ThreadID tid,
                                   RegVal *val)
    {
        if (!wb.valid || !wbDestMatches(phys_reg, tid)) return false;
        if (wb.reg_class != FloatRegClass && wb.reg_class != VecElemClass)
            return false;
        const uint64_t width_mask = chaos_fsu::laneMaskForWidth(wb.lane_width);
        const uint64_t oldv = (uint64_t)*val;
        const uint64_t lane_before = oldv & width_mask;
        const uint64_t lane_after = lane_before ^ wb.lane_mask;
        const uint64_t newv = (oldv & ~width_mask) | lane_after;
        *val = (RegVal)newv;
        if (!wb.prf_written) {
            wb.before_lane = lane_before;
            wb.after_lane = lane_after;
            wb.before_lo = oldv;
            wb.before_hi = 0;
            wb.after_lo = newv;
            wb.after_hi = 0;
            wb.prf_written = true;
        }
        return true;
    }

    bool
    CHAOSFPU::interceptVectorWrite(PhysRegIdPtr phys_reg, ThreadID tid,
                                   const void *val)
    {
        if (!wb.valid || !wbDestMatches(phys_reg, tid)) return false;
        if (wb.reg_class != VecRegClass || !val) return false;
        // The ISA's FU result lands in the shadow WB buffer; the PRF write is
        // deferred to finalizeWb(), where the mask is applied first.
        std::memcpy(wb.shadow, val, (size_t)wb.vec_bytes);
        wb.shadow_used = true;
        return true;
    }

    bool
    CHAOSFPU::finalizeWb(o3::DynInst *dyn_inst)
    {
        if (!wb.valid || !dyn_inst || wb.seq != dyn_inst->seqNum)
            return false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        PhysRegIdPtr dest = dyn_inst->renamedDestIdx(wb.dest_operand);
        if (!o3cpu || !dest ||
            (int)dest->classValue() != wb.reg_class ||
            (int)dest->index() != wb.reg_index) {
            cancelPendingArm();
            return false;
        }

        if (wb.shadow_used) {
            unsigned char after[WbPending::MAX_VEC_BYTES] = {};
            std::memcpy(after, wb.shadow, (size_t)wb.vec_bytes);
            const int lane_bytes = wb.lane_width / 8;
            const int base = wb.lane_offset * lane_bytes;
            uint64_t lane_before = 0;
            std::memcpy(&lane_before, wb.shadow + base, lane_bytes);
            const uint64_t lane_after = lane_before ^ wb.lane_mask;
            std::memcpy(after + base, &lane_after, lane_bytes);
            // This is the actual PRF writeback of the FU result, with the
            // fault applied to the writeback data. No unmasked value is ever
            // stored in the PRF.
            if (wb.reg_class == VecRegClass)
                o3cpu->physRegFile().setReg(dest, (const void *)after);
            else
                panic("CHAOSFPU: PRF-WB shadow on a non-vector class\n");
            std::memcpy(&wb.before_lo, wb.shadow, 8);
            std::memcpy(&wb.before_hi, wb.shadow + 8, 8);
            std::memcpy(&wb.after_lo, after, 8);
            std::memcpy(&wb.after_hi, after + 8, 8);
            wb.before_lane = lane_before;
            wb.after_lane = lane_after;
            wb.prf_written = true;
        }

        if (!wb.prf_written) {
            // No real destination write happened (predicated off or the ISA
            // did not write). This event cannot carry a fault; do not count.
            cancelPendingArm();
            return false;
        }

        FaultInfo fi;
        fi.reg_class = wb.reg_class;
        fi.reg_index = wb.reg_index;
        fi.before = wb.before_lane;
        fi.after = wb.after_lane;
        fi.mask = wb.lane_mask;
        fi.precision_bits = precision_bits;
        fi.lane_width = wb.lane_width;
        fi.lane_offset = wb.lane_offset;
        fi.bit_in_lane = wb.bit_in_lane;
        fi.abs_bit = wb.abs_bit;
        fi.field_lo = wb.field_lo;
        fi.field_hi = wb.field_hi;
        fi.abs_lo = wb.abs_lo;
        fi.abs_hi = wb.abs_hi;
        fi.full_before_lo = wb.before_lo;
        fi.full_before_hi = wb.before_hi;
        fi.full_after_lo = wb.after_lo;
        fi.full_after_hi = wb.after_hi;
        fi.instruction_bits = wb.enc;
        fi.decoded_kind = wb.decoded_kind;
        fi.decoded_precision_bits = wb.decoded_precision_bits;
        fi.decoded_element_width = wb.decoded_element_width;
        fi.decoded_lanes = wb.decoded_lanes;
        fi.decoded_reliable = wb.decoded_reliable;
        fi.precision_match = wb.precision_match;
        fi.lane_match = wb.lane_match;
        fi.is_vec = (wb.reg_class == VecRegClass);
        fi.field = "uniform";
        fi.op_class = wb.op_class;
        fi.injection_site = "prf_wb_data";
        fi.hook_version = "2";
        fi.producer_sn = dyn_inst->seqNum;
        fi.dest_operand = wb.dest_operand;
        fi.arm_tick = wb.arm_tick;
        noteFaultApplied(dyn_inst, fi);
        const uint64_t l0 = faulted_regs.empty()
            ? 0 : faulted_regs.back().l0_id;
        const uint64_t fid = faulted_regs.empty()
            ? 0 : faulted_regs.back().fault_id;
        wb_wakeup_valid = true;
        wb_wakeup_woken = false;
        wb_wakeup_seq = dyn_inst->seqNum;
        wb_wakeup_fid = fid;
        wb_wakeup_l0 = l0;
        wb_wakeup_class = wb.reg_class;
        wb_wakeup_reg = wb.reg_index;
        ++faults_injected_count;
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: prf_wb_data, hook_version=2"
                << ", opClass=" << wb.op_class
                << ", sn=" << dyn_inst->seqNum
                << ", phys_reg=" << wb.reg_index
                << ", mask=0x" << std::hex << wb.lane_mask << std::dec
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        cancelPendingArm();
        return true;
    }

    void
    CHAOSFPU::noteProducerWakeup(o3::DynInst *dyn_inst, int dependents)
    {
        if (!dyn_inst || !wb_wakeup_valid ||
            wb_wakeup_seq != dyn_inst->seqNum)
            return;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"producer_seq", std::to_string(dyn_inst->seqNum)},
            {"dyn_inst_seq", std::to_string(dyn_inst->seqNum)},
            {"wakeup_tick", std::to_string(curTick())},
            {"wakeup_dependents", std::to_string(dependents)},
            {"injection_site", "prf_wb_data"},
            {"hook_version", "2"},
        };
        kv.push_back({"reg_class", regClassName(wb_wakeup_class)});
        kv.push_back({"phys_reg", std::to_string(wb_wakeup_reg)});
        emitFsu("wakeup", wb_wakeup_fid, wb_wakeup_l0, kv);
        // Keep the record alive: a wakeup can be followed by a squash (the
        // instruction wrote back but never committed). noteSquash() must be
        // able to cancel it; noteCommit() clears it on the commit path.
        wb_wakeup_woken = true;
    }

    void
    CHAOSFPU::noteSquash(o3::DynInst *dyn_inst)
    {
        if (!dyn_inst || !wb_wakeup_valid ||
            wb_wakeup_seq != dyn_inst->seqNum)
            return;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"producer_seq", std::to_string(dyn_inst->seqNum)},
            {"dyn_inst_seq", std::to_string(dyn_inst->seqNum)},
            {"squash_tick", std::to_string(curTick())},
            {"injection_site", "prf_wb_data"},
            {"hook_version", "2"},
            {"outcome", wb_wakeup_woken
                ? "squashed_after_wakeup" : "squashed_before_wakeup"},
            {"wakeup_pending", wb_wakeup_woken ? "0" : "1"},
        };
        kv.push_back({"reg_class", regClassName(wb_wakeup_class)});
        kv.push_back({"phys_reg", std::to_string(wb_wakeup_reg)});
        // Retire the taint: this producer never reaches architectural state.
        for (auto &f : faulted_regs) {
            if (f.producer_sn == dyn_inst->seqNum)
                f.squashed = true;
        }
        // `squash` is a lifecycle/containment event, not an L0-L5 layer.
        emitFsu("squash", wb_wakeup_fid, wb_wakeup_l0, kv);
        wb_wakeup_valid = false;
    }

    // Sentinel: event_id 0 is valid; do not use 0 to mean "no parent".
    static constexpr uint64_t FSU_NO_PARENT = ~0ULL;

    std::string
    CHAOSFPU::hex64(uint64_t v)
    {
        char buf[32];
        std::snprintf(buf, sizeof(buf), "0x%016llx",
                      (unsigned long long)v);
        return std::string(buf);
    }

    std::string
    CHAOSFPU::hexWidth(uint64_t v, int bits)
    {
        const int digits = bits / 4;
        char buf[40];
        std::snprintf(buf, sizeof(buf), "0x%0*llx", digits,
                      (unsigned long long)v);
        return std::string(buf);
    }

    std::string
    CHAOSFPU::hex128(uint64_t lo, uint64_t hi)
    {
        char buf[40];
        std::snprintf(buf, sizeof(buf), "0x%016llx%016llx",
                      (unsigned long long)hi, (unsigned long long)lo);
        return std::string(buf);
    }

    std::string
    CHAOSFPU::hash64(uint64_t v)
    {
        // FNV-1a over the 8 value bytes (evidence only; not a crypto hash).
        uint64_t h = 1469598103934665603ULL;
        for (int i = 0; i < 8; i++) {
            h ^= (v >> (8 * i)) & 0xffULL;
            h *= 1099511628211ULL;
        }
        return hex64(h);
    }

    uint64_t
    CHAOSFPU::emitFsu(const char *kind, uint64_t fault_id, uint64_t parent,
                      std::vector<std::pair<std::string, std::string>> kv)
    {
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu || !o3cpu->chaosPropagation)
            return 0;
        kv.push_back({"fault_id", std::to_string(fault_id)});
        if (parent != FSU_NO_PARENT)
            kv.push_back({"parent_event_id", std::to_string(parent)});
        if (!fsu_model.empty())
            kv.push_back({"model_id", fsu_model});
        if (!fsu_submodel.empty())
            kv.push_back({"submodel", fsu_submodel});
        if (!fsu_freq.empty())
            kv.push_back({"freq", fsu_freq});
        if (!fsu_load.empty())
            kv.push_back({"load_id", fsu_load});
        // PROP-EVT is space-delimited: no spaces in values.
        kv.push_back({"unit", "FSU_Pipe"});
        // fault_installed is the F5 L0 root, exactly like fault_applied is
        // the F0-F4 root: it opens the chain (no join happened yet).
        kv.push_back({"corr", (std::string(kind) == "fault_applied" ||
                               std::string(kind) == "fault_installed")
                              ? "origin" : "fsu_taint"});
        return o3cpu->chaosPropagation->notePropEvt(kind, kv);
    }

    void
    CHAOSFPU::noteFaultApplied(o3::DynInst *inst, const FaultInfo &fi)
    {
        if (!inst || fi.reg_class < 0 || fi.reg_index < 0)
            return;
        const uint64_t fid = next_fault_id++;
        int fl = fi.field_lo, fh = fi.field_hi;
        if (fl < 0 && fi.mask) {
            fl = __builtin_ctzll(fi.mask);
            fh = 63 - __builtin_clzll(fi.mask);
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"dyn_inst_seq", std::to_string(inst->seqNum)},
            {"pc", hex64(inst->pcState().instAddr())},
            {"opcode", inst->staticInst ? inst->staticInst->getName() : ""},
            {"phys_reg", std::to_string(fi.reg_index)},
            {"reg_class", regClassName(fi.reg_class)},
            {"field", fi.field},
            {"precision", precision},
            {"fault_mask", hex64(fi.mask)},
            {"bit_indices", std::to_string(fi.abs_bit)},
            {"bit_in_lane", std::to_string(fi.bit_in_lane)},
            {"lane_width", std::to_string(fi.lane_width)},
            {"lane_offset", std::to_string(fi.lane_offset)},
            {"lane_mask", hex128(fi.abs_lo, fi.abs_hi)},
            {"before", hexWidth(fi.before, fi.lane_width)},
            {"after", hexWidth(fi.after, fi.lane_width)},
            {"full_before", hex128(fi.full_before_lo, fi.full_before_hi)},
            {"full_after", hex128(fi.full_after_lo, fi.full_after_hi)},
            {"before_hash", hash64(fi.before)},
            {"after_hash", hash64(fi.after)},
            {"value_hash", hash64(fi.after)},
            {"attempted", "1"},
            {"activated", ""},
            {"thread_id", std::to_string((int)inst->threadNumber)},
        };
        // [FSU][FR07-HOOK v2] Self-describing injection-site provenance.
        if (!fi.injection_site.empty()) {
            kv.push_back({"injection_site", fi.injection_site});
            kv.push_back({"hook_version", fi.hook_version});
            kv.push_back({"producer_seq", std::to_string(fi.producer_sn)});
            kv.push_back({"dest_operand", std::to_string(fi.dest_operand)});
            kv.push_back({"arm_tick", std::to_string(fi.arm_tick)});
            kv.push_back({"writeback_tick", std::to_string(curTick())});
            kv.push_back({"wakeup_pending", "1"});
        }
        if (fl >= 0)
            kv.push_back({"field_lo", std::to_string(fl)});
        if (fh >= 0)
            kv.push_back({"field_hi", std::to_string(fh)});
        if (fi.instruction_bits || !fi.decoded_kind.empty()) {
            kv.push_back({"instruction_bits",
                          hexWidth(fi.instruction_bits, 32)});
            kv.push_back({"decoded_kind", fi.decoded_kind});
            kv.push_back({"decoded_precision",
                          precisionName(fi.decoded_precision_bits)});
            kv.push_back({"decoded_reg_class",
                          regClassName(fi.reg_class)});
            kv.push_back({"decoded_element_width",
                          std::to_string(fi.decoded_element_width)});
            kv.push_back({"decoded_lanes",
                          std::to_string(fi.decoded_lanes)});
            kv.push_back({"decoded_reliable",
                          fi.decoded_reliable ? "1" : "0"});
            kv.push_back({"manifest_precision", precision});
            kv.push_back({"manifest_lane_width",
                          std::to_string(lane_width)});
            kv.push_back({"manifest_lane_offset",
                          std::to_string(lane_offset)});
            kv.push_back({"precision_match",
                          fi.precision_match ? "1" : "0"});
            kv.push_back({"lane_match", fi.lane_match ? "1" : "0"});
        }
        if (fsu_eligible_total)
            kv.push_back({"eligible_total",
                          std::to_string(fsu_eligible_total)});
        if (rate_mode) {
            // [FSU][D2] Per-fault rate provenance. These fields make the
            // event self-describing: a reader can verify the ordinal is the
            // declared cumulative interval and that the run really used F3
            // (etc.), not merely a relabeled F0.
            kv.push_back({"eligible_ordinal",
                          std::to_string(injected_eligible_ordinal)});
            kv.push_back({"eligible_total",
                          std::to_string(fsu_eligible_total)});
            kv.push_back({"rate_divisor",
                          std::to_string(rate_divisor)});
            kv.push_back({"jitter_pct", std::to_string(jitter_pct)});
            kv.push_back({"interval", std::to_string(current_interval)});
            kv.push_back({"ordinal_index",
                          std::to_string(current_ordinal_index)});
            kv.push_back({"ordinal_generator",
                          "splitmix64-mod-uniform-interval"});
            kv.push_back({"ordinal_generator_version", "1"});
            kv.push_back({"ordinal_seed", std::to_string(rng_seed)});
        }
        const uint64_t l0 = emitFsu("fault_applied", fid, FSU_NO_PARENT, kv);
        const uint64_t l1 = emitFsu("carrier_state", fid, l0, kv);
        FaultedReg fr;
        fr.fault_id = fid;
        fr.l0_id = l0;
        fr.l1_id = l1;
        fr.producer_sn = inst->seqNum;
        fr.tick = curTick();
        fr.tid = (int)inst->threadNumber;
        fr.reg_class = fi.reg_class;
        fr.reg_index = fi.reg_index;
        fr.before = fi.before;
        fr.after = fi.after;
        fr.mask = fi.mask;
        fr.field = fi.field;
        fr.precision_bits = fi.precision_bits;
        fr.lane_width = fi.lane_width;
        fr.lane_offset = fi.lane_offset;
        fr.bit_in_lane = fi.bit_in_lane;
        fr.abs_bit = fi.abs_bit;
        fr.field_lo = fi.field_lo;
        fr.field_hi = fi.field_hi;
        fr.abs_lo = fi.abs_lo;
        fr.abs_hi = fi.abs_hi;
        fr.full_before_lo = fi.full_before_lo;
        fr.full_before_hi = fi.full_before_hi;
        fr.full_after_lo = fi.full_after_lo;
        fr.full_after_hi = fi.full_after_hi;
        fr.instruction_bits = fi.instruction_bits;
        fr.decoded_kind = fi.decoded_kind;
        fr.decoded_precision_bits = fi.decoded_precision_bits;
        fr.decoded_element_width = fi.decoded_element_width;
        fr.decoded_lanes = fi.decoded_lanes;
        fr.decoded_reliable = fi.decoded_reliable;
        fr.precision_match = fi.precision_match;
        fr.lane_match = fi.lane_match;
        fr.is_vec = fi.is_vec;
        fr.consumed = false;
        fr.op_class = fi.op_class;
        faulted_regs.push_back(fr);
    }

    // ------------------------------------------------------------------
    // [FSU][F5] Permanent stuck-at: one install, many exposures.
    // ------------------------------------------------------------------

    std::string
    CHAOSFPU::f5PolicyString() const
    {
        // PROP-EVT is space-delimited: keep this value free of spaces.
        return "bounded_first_last(limit=" + std::to_string(f5_sample_limit) +
               ",first=" + std::to_string(f5_keep_first) +
               ",last=" + std::to_string(f5_keep_last) + ")";
    }

    void
    CHAOSFPU::appendF5Accounting(
        std::vector<std::pair<std::string, std::string>> &kv,
        bool install_snapshot) const
    {
        // `eligible_ordinal` is the run's ground-truth count of matched
        // eligible events. The installation event is exposure #1, so the
        // post-warmup window is [warmup_skipped + 1 .. eligible_seen_total]
        // and every event in it is either an exposure or a matched event
        // with no writable destination.
        const uint64_t seen = eligible_ordinal;
        const uint64_t post = install_snapshot
            ? 1 + f5_eligible_without_writable_dest
            : f5_exposures_total + f5_eligible_without_writable_dest;
        kv.push_back({"eligible_seen_total", std::to_string(seen)});
        kv.push_back({"warmup_configured", std::to_string(f5_warmup)});
        kv.push_back({"warmup_eligible_skipped",
                      std::to_string(f5_warmup_eligible_skipped)});
        kv.push_back({"install_eligible_ordinal",
                      std::to_string(f5_install_eligible_ordinal)});
        kv.push_back({"install_is_exposure", "1"});
        kv.push_back({"post_install_eligible", std::to_string(post)});
        kv.push_back({"eligible_without_writable_dest",
                      std::to_string(f5_eligible_without_writable_dest)});
        // The pre-registered census is a REFERENCE, not a required equality:
        // a fault-run eligible total may legitimately differ from it (the
        // census was measured on a possibly different/earlier stream). Only
        // the delta arithmetic is authoritative.
        if (fsu_eligible_total) {
            kv.push_back({"selected_eligible_total",
                          std::to_string(fsu_eligible_total)});
            const long long delta =
                (long long)seen - (long long)fsu_eligible_total;
            kv.push_back({"eligible_delta_vs_census",
                          std::to_string(delta)});
            kv.push_back({"census_reference", "pre_registered_countOnly"});
        }
    }

    bool
    CHAOSFPU::markF5Sample(uint64_t exposure_id)
    {
        // insert() is the single source of truth for "already sampled": the
        // first / tail / first-activated policies may select the same
        // exposure, but it is emitted and counted exactly once.
        if (!f5_sampled_exposure_ids.insert(exposure_id).second)
            return false;
        ++f5_exposures_sampled;
        return true;
    }

    void
    CHAOSFPU::noteF5CellActivation(const FaultInfo &fi, uint64_t exposure_id)
    {
        // Bounded per-(reg_class, phys_index) accumulation. The key is the
        // physical cell identity, not the fault_id: a consumer reading that
        // cell can be affected by several activated exposures of the same
        // permanent fault.
        const std::pair<int, int> key(fi.reg_class, fi.reg_index);
        auto it = f5_cell_sources.find(key);
        if (it == f5_cell_sources.end()) {
            if (f5_cell_sources.size() >= F5_MAX_CELL_SOURCES) {
                // Bounded map: never grow without limit. The overflow is
                // reported on chain_end; it is never silent.
                ++f5_cell_sources_overflow;
                return;
            }
            F5CellSourceSummary s;
            s.merged_activated = 1;
            s.first_exposure_id = exposure_id;
            s.last_exposure_id = exposure_id;
            f5_cell_sources.emplace(key, s);
            return;
        }
        ++it->second.merged_activated;
        it->second.last_exposure_id = exposure_id;
    }

    std::vector<std::pair<std::string, std::string>>
    CHAOSFPU::buildF5Kv(o3::DynInst *inst, const FaultInfo &fi) const
    {
        int fl = fi.field_lo, fh = fi.field_hi;
        if (fl < 0 && fi.mask) {
            fl = __builtin_ctzll(fi.mask);
            fh = 63 - __builtin_clzll(fi.mask);
        }
        // `fi.field` was refined once in maybeCorrupt (single-bit mask that
        // fits one IEEE754 field -> that field's name; otherwise
        // "permanent_stuck"), so every event of the chain -- including the
        // L2-L5 consumer events -- carries the SAME field label.
        const std::string &fld = fi.field;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"dyn_inst_seq", std::to_string(inst->seqNum)},
            {"pc", hex64(inst->pcState().instAddr())},
            {"opcode", inst->staticInst ? inst->staticInst->getName() : ""},
            {"phys_reg", std::to_string(fi.reg_index)},
            {"reg_class", regClassName(fi.reg_class)},
            {"op_class", fi.op_class},
            {"field", fld},
            {"precision", precision},
            {"fault_mask", hex64(fi.mask)},
            {"fixed_mask", hex64(fi.mask)},
            {"stuck_polarity", std::to_string(f5_polarity)},
            {"bit_indices", std::to_string(fi.abs_bit)},
            {"bit_in_lane", std::to_string(fi.bit_in_lane)},
            {"lane_width", std::to_string(fi.lane_width)},
            {"lane_offset", std::to_string(fi.lane_offset)},
            {"lane_mask", hex128(fi.abs_lo, fi.abs_hi)},
            {"before", hexWidth(fi.before, fi.lane_width)},
            {"after", hexWidth(fi.after, fi.lane_width)},
            {"full_before", hex128(fi.full_before_lo, fi.full_before_hi)},
            {"full_after", hex128(fi.full_after_lo, fi.full_after_hi)},
            {"before_hash", hash64(fi.before)},
            {"after_hash", hash64(fi.after)},
            {"value_hash", hash64(fi.after)},
            {"attempted", "1"},
            {"thread_id", std::to_string((int)inst->threadNumber)},
            {"first_eligible_sn", std::to_string(f5_first_eligible_sn)},
            {"sample_policy", f5PolicyString()},
        };
        if (fl >= 0)
            kv.push_back({"field_lo", std::to_string(fl)});
        if (fh >= 0)
            kv.push_back({"field_hi", std::to_string(fh)});
        if (f5_install_event)
            kv.push_back({"install_event", std::to_string(f5_install_event)});
        if (fi.instruction_bits || !fi.decoded_kind.empty()) {
            kv.push_back({"instruction_bits",
                          hexWidth(fi.instruction_bits, 32)});
            kv.push_back({"decoded_kind", fi.decoded_kind});
            kv.push_back({"decoded_precision",
                          precisionName(fi.decoded_precision_bits)});
            kv.push_back({"decoded_reg_class",
                          regClassName(fi.reg_class)});
            kv.push_back({"decoded_element_width",
                          std::to_string(fi.decoded_element_width)});
            kv.push_back({"decoded_lanes",
                          std::to_string(fi.decoded_lanes)});
            kv.push_back({"decoded_reliable",
                          fi.decoded_reliable ? "1" : "0"});
            kv.push_back({"manifest_precision", precision});
            kv.push_back({"manifest_lane_width",
                          std::to_string(lane_width)});
            kv.push_back({"manifest_lane_offset",
                          std::to_string(lane_offset)});
            kv.push_back({"precision_match",
                          fi.precision_match ? "1" : "0"});
            kv.push_back({"lane_match", fi.lane_match ? "1" : "0"});
        }
        if (fsu_eligible_total)
            kv.push_back({"eligible_total",
                          std::to_string(fsu_eligible_total)});
        return kv;
    }

    static void
    f5SetKv(std::vector<std::pair<std::string, std::string>> &kv,
            const std::string &key, const std::string &value)
    {
        for (auto &p : kv) {
            if (p.first == key) {
                p.second = value;
                return;
            }
        }
        kv.push_back({key, value});
    }

    uint64_t
    CHAOSFPU::emitF5Exposure(
        const std::vector<std::pair<std::string, std::string>> &kv,
        uint64_t parent)
    {
        const uint64_t eid = emitFsu("exposure", f5_fault_id, parent, kv);
        if (eid)
            f5_last_event_id = eid;
        return eid;
    }

    void
    CHAOSFPU::registerF5Taint(o3::DynInst *inst, const FaultInfo &fi,
                              uint64_t parent_event)
    {
        if (f5_taint_registered)
            return;
        FaultedReg fr;
        fr.fault_id = f5_fault_id;
        fr.l0_id = f5_install_event;
        // The first ACTIVATED exposure is the direct L1 parent of the real
        // L2-L5 impact chain: install -> carrier -> exposure -> operand_read
        // -> execute -> prf_writeback -> commit.
        fr.l1_id = parent_event ? parent_event : f5_carrier_event;
        fr.producer_sn = inst->seqNum;
        fr.tick = curTick();
        fr.tid = (int)inst->threadNumber;
        fr.reg_class = fi.reg_class;
        fr.reg_index = fi.reg_index;
        fr.before = fi.before;
        fr.after = fi.after;
        fr.mask = fi.mask;
        fr.field = fi.field;
        fr.precision_bits = fi.precision_bits;
        fr.lane_width = fi.lane_width;
        fr.lane_offset = fi.lane_offset;
        fr.bit_in_lane = fi.bit_in_lane;
        fr.abs_bit = fi.abs_bit;
        fr.field_lo = fi.field_lo;
        fr.field_hi = fi.field_hi;
        fr.abs_lo = fi.abs_lo;
        fr.abs_hi = fi.abs_hi;
        fr.full_before_lo = fi.full_before_lo;
        fr.full_before_hi = fi.full_before_hi;
        fr.full_after_lo = fi.full_after_lo;
        fr.full_after_hi = fi.full_after_hi;
        fr.instruction_bits = fi.instruction_bits;
        fr.decoded_kind = fi.decoded_kind;
        fr.decoded_precision_bits = fi.decoded_precision_bits;
        fr.decoded_element_width = fi.decoded_element_width;
        fr.decoded_lanes = fi.decoded_lanes;
        fr.decoded_reliable = fi.decoded_reliable;
        fr.precision_match = fi.precision_match;
        fr.lane_match = fi.lane_match;
        fr.is_vec = fi.is_vec;
        fr.consumed = false;
        fr.op_class = fi.op_class;
        fr.f5 = true;
        faulted_regs.push_back(fr);
        f5_taint_registered = true;
    }

    void
    CHAOSFPU::notePermanentExposure(o3::DynInst *inst, const FaultInfo &fi)
    {
        if (!inst || fi.reg_class < 0 || fi.reg_index < 0)
            return;

        const bool install = !f5_armed;
        if (install) {
            // ONE installation per run: one fault_id, one mask, one
            // polarity. The install event is the L0 root; carrier_state is
            // L1. No later event increments next_fault_id.
            f5_fault_id = next_fault_id++;
            f5_first_eligible_sn = inst->seqNum;
            f5_op_class = fi.op_class;
            f5_reg_class = regClassName(fi.reg_class);
            ++faults_injected_count;
            // The installation event is the first post-warmup eligible
            // event and exposure #1. Record its ordinal and the number of
            // warm-up eligible events that were skipped, then emit the full
            // eligible accounting on the L0 root (and L1 carrier).
            f5_install_eligible_ordinal = eligible_ordinal;
            f5_warmup_eligible_skipped = chaos_fsu::f5WarmupEligibleSkipped(
                f5_warmup, eligible_ordinal, true);
            auto kv = buildF5Kv(inst, fi);
            appendF5Accounting(kv, true);
            f5_install_event = emitFsu("fault_installed", f5_fault_id,
                                       FSU_NO_PARENT, kv);
            f5_last_event_id = f5_install_event;
            auto ckv = kv;
            if (f5_install_event)
                f5SetKv(ckv, "install_event",
                        std::to_string(f5_install_event));
            f5_carrier_event = emitFsu(
                "carrier_state", f5_fault_id,
                f5_install_event ? f5_install_event : FSU_NO_PARENT, ckv);
            if (f5_carrier_event)
                f5_last_event_id = f5_carrier_event;
            f5_terminal_parent = f5_carrier_event
                ? f5_carrier_event : f5_install_event;
            f5_armed = true;
            // Register the terminal flush on the tracer itself (not as a
            // global exit callback): it runs after the tracer's chain_end
            // markers and before the gzip stream is closed, regardless of
            // SimObject construction order.
            if (!f5_flush_registered) {
                auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
                if (o3cpu && o3cpu->chaosPropagation) {
                    o3cpu->chaosPropagation->registerExitFlush(
                        [this]() { flushF5Samples(); emitF5ChainEnd(); });
                    f5_flush_registered = true;
                }
            }
        }

        // Every eligible event after installation is an exposure: re-apply
        // the SAME polarity and classify activation from the CORRECT value
        // (the value before the forced write). No new fault is created.
        ++f5_exposures_total;
        const bool activated = chaos_fsu::stuckActivated(
            fi.before, fi.mask, f5_polarity);
        if (activated) {
            ++f5_activated_total;
            // [FSU][F5] Accumulate per-physical-cell activated-exposure
            // sources for the eventual consumer. This is NOT sampling:
            // every activated exposure is counted, whether or not its
            // exposure event reaches the bounded sample stream. The map is
            // erased when the cell is consumed (noteConsumerExecute).
            noteF5CellActivation(fi, f5_exposures_total);
        }
        const bool first_activated = activated && !f5_first_activated_done;
        if (first_activated) {
            f5_first_activated_done = true;
            f5_first_activated_sn = inst->seqNum;
            f5_first_activated_tick = curTick();
        }
        f5_last_exposure_sn = inst->seqNum;

        auto ekv = buildF5Kv(inst, fi);
        // Every exposure names the ONE installation root, including the
        // ordinary prefix samples emitted during the run. The gate/audit
        // contract requires this field on every exposure, not only on the
        // commit/chain_end summary.
        ekv.push_back({"install_event", std::to_string(f5_install_event)});
        ekv.push_back({"exposure_id", std::to_string(f5_exposures_total)});
        ekv.push_back({"exposure_count", std::to_string(f5_exposures_total)});
        ekv.push_back({"activated_exposure_count",
                       std::to_string(f5_activated_total)});
        ekv.push_back({"activated", activated ? "1" : "0"});
        ekv.push_back({"first_activated_sn",
                       f5_first_activated_sn
                           ? std::to_string(f5_first_activated_sn)
                           : std::string()});
        ekv.push_back({"last_exposure_sn",
                       std::to_string(f5_last_exposure_sn)});
        ekv.push_back({"affected_sn",
                       activated ? std::to_string(inst->seqNum)
                                 : std::string()});
        ekv.push_back({"correct_before",
                       hexWidth(fi.before, fi.lane_width)});
        ekv.push_back({"stuck_after",
                       hexWidth(fi.after, fi.lane_width)});
        ekv.push_back({"exposures_total",
                       std::to_string(f5_exposures_total)});

        const bool first_exposure = (f5_exposures_total == 1);
        enum { F5_DROP, F5_EMIT_NOW, F5_KEEP_TAIL } action = F5_DROP;
        if (first_exposure || first_activated) {
            action = F5_EMIT_NOW;
        } else if (f5_ordinary_emitted < f5_keep_first) {
            action = F5_EMIT_NOW;
            ++f5_ordinary_emitted;
        } else if (f5_keep_last > 0) {
            action = F5_KEEP_TAIL;
        }

        if (action == F5_EMIT_NOW) {
            // Every sample is keyed by exposure_id: the first / tail /
            // first-activated policies may overlap, but an exposure can
            // never be counted or emitted twice. markF5Sample() owns the
            // single increment of f5_exposures_sampled.
            if (markF5Sample(f5_exposures_total)) {
                const uint64_t sampled = f5_exposures_sampled;
                const uint64_t dropped = f5_exposures_total > sampled
                    ? f5_exposures_total - sampled : 0;
                f5SetKv(ekv, "exposures_sampled", std::to_string(sampled));
                f5SetKv(ekv, "exposures_dropped", std::to_string(dropped));
                const uint64_t parent = f5_carrier_event
                    ? f5_carrier_event : f5_install_event;
                const uint64_t eid = emitF5Exposure(ekv, parent);
                if (first_activated) {
                    if (eid)
                        f5_terminal_parent = eid;
                    registerF5Taint(inst, fi,
                                    eid ? eid : (f5_carrier_event
                                                 ? f5_carrier_event
                                                 : f5_install_event));
                }
            }
        } else if (action == F5_KEEP_TAIL) {
            // Bounded tail sample: emitted by the tracer's exit hook. Its
            // counters are rewritten at flush time (sampled events may
            // still grow afterwards) and the authoritative totals live on
            // chain_end. The exposure_id travels with the sample so the
            // flush uses the SAME deduplication key.
            f5SetKv(ekv, "exposures_sampled",
                    std::to_string(f5_exposures_sampled + 1));
            f5SetKv(ekv, "exposures_dropped",
                    std::to_string(f5_exposures_total >
                                   f5_exposures_sampled + 1
                                       ? f5_exposures_total -
                                         (f5_exposures_sampled + 1)
                                       : 0));
            F5Sample sample;
            sample.exposure_id = f5_exposures_total;
            sample.kv = std::move(ekv);
            f5_last_samples.push_back(std::move(sample));
            while (f5_last_samples.size() > (size_t)f5_keep_last)
                f5_last_samples.pop_front();
        }
    }

    void
    CHAOSFPU::flushF5Samples()
    {
        const uint64_t parent = f5_carrier_event
            ? f5_carrier_event : f5_install_event;
        while (!f5_last_samples.empty()) {
            F5Sample sample = std::move(f5_last_samples.front());
            f5_last_samples.pop_front();
            // Same exposure_id key as the in-run samples: a tail sample can
            // never double-count an exposure that was already emitted.
            if (!markF5Sample(sample.exposure_id))
                continue;
            const uint64_t sampled = f5_exposures_sampled;
            // These events were queued during the run; at flush time the
            // authoritative total is known. Rewrite the TOTAL as well as
            // sampled/dropped so every exposure satisfies the conservation
            // identity total == sampled + dropped (a stale per-event total
            // would make the tail samples internally inconsistent).
            const uint64_t dropped = f5_exposures_total > sampled
                ? f5_exposures_total - sampled : 0;
            f5SetKv(sample.kv, "exposures_total",
                    std::to_string(f5_exposures_total));
            f5SetKv(sample.kv, "activated_exposure_count",
                    std::to_string(f5_activated_total));
            f5SetKv(sample.kv, "exposures_sampled", std::to_string(sampled));
            f5SetKv(sample.kv, "exposures_dropped", std::to_string(dropped));
            emitF5Exposure(sample.kv, parent);
        }
    }

    void
    CHAOSFPU::emitF5ChainEnd()
    {
        if (!f5_armed)
            return;
        f5_exposures_dropped = f5_exposures_total > f5_exposures_sampled
            ? f5_exposures_total - f5_exposures_sampled : 0;
        const char *terminal = f5_commit_seen
            ? "committed"
            : (f5_activated_total ? "exposed_unconsumed" : "not_activated");
        std::vector<std::pair<std::string, std::string>> kv = {
            {"install_event", std::to_string(f5_install_event)},
            {"stuck_polarity", std::to_string(f5_polarity)},
            {"fixed_mask", hex64(f5_fixed_mask)},
            {"op_class", f5_op_class},
            {"reg_class", f5_reg_class},
            {"first_eligible_sn", std::to_string(f5_first_eligible_sn)},
            {"exposure_count", std::to_string(f5_exposures_total)},
            {"activated_exposure_count",
             std::to_string(f5_activated_total)},
            {"first_activated_sn",
             f5_first_activated_sn
                 ? std::to_string(f5_first_activated_sn) : std::string()},
            {"last_exposure_sn", std::to_string(f5_last_exposure_sn)},
            {"affected_sn",
             f5_first_impact_sn
                 ? std::to_string(f5_first_impact_sn)
                 : (f5_first_activated_sn
                        ? std::to_string(f5_first_activated_sn)
                        : std::string())},
            {"first_impact_latency",
             f5_commit_seen ? std::to_string(f5_first_impact_latency)
                            : std::string()},
            {"sample_policy", f5PolicyString()},
            {"exposures_total", std::to_string(f5_exposures_total)},
            {"exposures_sampled", std::to_string(f5_exposures_sampled)},
            {"exposures_dropped", std::to_string(f5_exposures_dropped)},
            {"terminal", terminal},
            {"outcome", terminal},
            {"activated", f5_activated_total ? "1" : "0"},
            // [FSU][F5] Sampling is OBSERVATION ONLY: the fault is applied
            // to every eligible event regardless of how many observations
            // fit in the bounded sample stream. These flags make that
            // explicit on the terminal record.
            {"applied_to_all_exposures", "1"},
            {"sampled_is_observation_only", "1"},
            {"sampled_unique", std::to_string(f5_exposures_sampled)},
            {"omitted", std::to_string(f5_exposures_dropped)},
            // Lifecycle terminus only: no detection_layer, never an L5
            // witness. The real L5 is the commit event of the first
            // activated exposure's chain.
        };
        appendF5Accounting(kv, false);
        kv.push_back({"cell_sources_overflow",
                      std::to_string(f5_cell_sources_overflow)});
        emitFsu("chain_end", f5_fault_id,
                f5_terminal_parent ? f5_terminal_parent
                                   : (f5_carrier_event
                                          ? f5_carrier_event
                                          : f5_install_event),
                kv);
    }

    void
    CHAOSFPU::noteConsumerExecute(o3::DynInst *inst)
    {
        if (!inst || faulted_regs.empty())
            return;
        if (tainted_consumers.count(inst->seqNum))
            return;
        for (auto &f : faulted_regs) {
            if (f.consumed || f.squashed)
                continue;
            for (int i = 0; i < inst->numSrcRegs(); i++) {
                PhysRegIdPtr reg = inst->renamedSrcIdx(i);
                if (!reg || reg->is(InvalidRegClass))
                    continue;
                if ((int)reg->classValue() != f.reg_class ||
                    reg->index() != f.reg_index ||
                    (int)inst->threadNumber != f.tid)
                    continue;
                f.consumed = true;
                std::vector<std::pair<std::string, std::string>> kv = {
                    {"producer_seq", std::to_string(f.producer_sn)},
                    {"consumer_seq", std::to_string(inst->seqNum)},
                    {"dyn_inst_seq", std::to_string(inst->seqNum)},
                    {"src_slot", std::to_string(i)},
                    {"phys_reg", std::to_string(f.reg_index)},
                    {"reg_class", regClassName(f.reg_class)},
                    {"instruction_bits", hexWidth(f.instruction_bits, 32)},
                    {"decoded_kind", f.decoded_kind},
                    {"decoded_precision",
                     precisionName(f.decoded_precision_bits)},
                    {"decoded_element_width",
                     std::to_string(f.decoded_element_width)},
                    {"decoded_lanes", std::to_string(f.decoded_lanes)},
                    {"decoded_reliable", f.decoded_reliable ? "1" : "0"},
                    {"manifest_precision", precision},
                    {"manifest_lane_width", std::to_string(lane_width)},
                    {"manifest_lane_offset", std::to_string(lane_offset)},
                    {"precision_match", f.precision_match ? "1" : "0"},
                    {"lane_match", f.lane_match ? "1" : "0"},
                    {"pc", hex64(inst->pcState().instAddr())},
                    {"opcode", inst->staticInst
                                   ? inst->staticInst->getName() : ""},
                    {"activated", "1"},
                    {"value_hash", hash64(f.after)},
                    {"field", f.field},
                    {"precision", precision},
                    {"lane_width", std::to_string(f.lane_width)},
                    {"lane_offset", std::to_string(f.lane_offset)},
                    {"bit_indices", std::to_string(f.abs_bit)},
                    {"bit_in_lane", std::to_string(f.bit_in_lane)},
                    {"fault_mask", hex64(f.mask)},
                    {"lane_mask", hex128(f.abs_lo, f.abs_hi)},
                    {"thread_id", std::to_string((int)inst->threadNumber)},
                };
                if (f.field_lo >= 0)
                    kv.push_back({"field_lo", std::to_string(f.field_lo)});
                if (f.field_hi >= 0)
                    kv.push_back({"field_hi", std::to_string(f.field_hi)});
                if (f.f5) {
                    // Keep every link of the one permanent fault's chain
                    // self-describing, not just the install/exposure.
                    kv.push_back({"install_event",
                                  std::to_string(f5_install_event)});
                    // reg_class is already present in the operand_read kv;
                    // only op_class needs to be added here.
                    kv.push_back({"op_class", f.op_class});
                    kv.push_back({"stuck_polarity",
                                  std::to_string(f5_polarity)});
                    kv.push_back({"fixed_mask", hex64(f5_fixed_mask)});
                    kv.push_back({"first_eligible_sn",
                                  std::to_string(f5_first_eligible_sn)});
                    kv.push_back({"first_activated_sn",
                                  f5_first_activated_sn
                                      ? std::to_string(f5_first_activated_sn)
                                      : std::string()});
                    // [FSU][F5] A consumer reading this physical cell may be
                    // affected by several activated exposures of the same
                    // permanent fault. Do NOT silently keep only the first
                    // source, and do NOT expand every source: carry the
                    // merged count plus a bounded first:last exposure-id
                    // range. sources_expanded=1 is the one source whose real
                    // L2-L5 chain this event belongs to; the rest are
                    // counted as unexpanded.
                    auto cs = f5_cell_sources.find(
                        std::make_pair(f.reg_class, f.reg_index));
                    if (cs != f5_cell_sources.end()) {
                        const uint64_t merged = cs->second.merged_activated;
                        const auto summary =
                            chaos_fsu::f5SourceSummary(merged);
                        kv.push_back({"merged_activated_exposures",
                                      std::to_string(merged)});
                        kv.push_back({"observed_exposure_ids",
                                      std::to_string(
                                          cs->second.first_exposure_id) + ":" +
                                      std::to_string(
                                          cs->second.last_exposure_id)});
                        kv.push_back({"sources_expanded",
                                      std::to_string(summary.expanded)});
                        kv.push_back({"sources_unexpanded",
                                      std::to_string(summary.unexpanded)});
                        kv.push_back({"observation_scope",
                                      "first_activated_chain"});
                        // Consumed: the summary belongs to THIS consumer.
                        f5_cell_sources.erase(cs);
                    }
                }
                const uint64_t l2 = emitFsu("operand_read", f.fault_id,
                                            f.l1_id, kv);
                TaintedConsumer tc;
                tc.fault_id = f.fault_id;
                tc.l2_id = l2;
                tc.consumer_sn = inst->seqNum;
                tc.field = f.field;
                tc.precision_bits = f.precision_bits;
                tc.lane_width = f.lane_width;
                tc.lane_offset = f.lane_offset;
                tc.bit_in_lane = f.bit_in_lane;
                tc.abs_bit = f.abs_bit;
                tc.field_lo = f.field_lo;
                tc.field_hi = f.field_hi;
                tc.abs_lo = f.abs_lo;
                tc.abs_hi = f.abs_hi;
                tc.instruction_bits = f.instruction_bits;
                tc.decoded_kind = f.decoded_kind;
                tc.decoded_precision_bits = f.decoded_precision_bits;
                tc.decoded_element_width = f.decoded_element_width;
                tc.decoded_lanes = f.decoded_lanes;
                tc.decoded_reliable = f.decoded_reliable;
                tc.precision_match = f.precision_match;
                tc.lane_match = f.lane_match;
                tc.op_class = f.op_class;
                tc.reg_class = regClassName(f.reg_class);
                tc.is_store = inst->isStore();
                if (!tc.is_store && isFpOpClass(inst->opClass())) {
                    tc.l3_id = emitFsu("execute", f.fault_id, l2, kv);
                    tc.has_l3 = true;
                    tc.l4_id = emitFsu("prf_writeback", f.fault_id,
                                       tc.l3_id, kv);
                    tc.has_l4 = true;
                }
                tainted_consumers[inst->seqNum] = tc;
                return;
            }
        }
    }

    void
    CHAOSFPU::noteCommit(ThreadID tid, o3::DynInst *inst)
    {
        if (!inst)
            return;
        // [FR07-HOOK v2] The injected producer committed: it can no longer
        // be squashed, so its pending wakeup record is retired here.
        if (wb_wakeup_valid && wb_wakeup_seq == inst->seqNum)
            wb_wakeup_valid = false;
        auto it = tainted_consumers.find(inst->seqNum);
        if (it == tainted_consumers.end() || it->second.committed)
            return;
        TaintedConsumer &tc = it->second;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"consumer_seq", std::to_string(inst->seqNum)},
            {"dyn_inst_seq", std::to_string(inst->seqNum)},
            {"commit_seq", std::to_string(inst->seqNum)},
            {"thread_id", std::to_string((int)tid)},
            {"pc", hex64(inst->pcState().instAddr())},
            {"opcode", inst->staticInst ? inst->staticInst->getName() : ""},
            {"field", tc.field},
            {"precision", precision},
            {"lane_width", std::to_string(tc.lane_width)},
            {"lane_offset", std::to_string(tc.lane_offset)},
            {"bit_indices", std::to_string(tc.abs_bit)},
            {"bit_in_lane", std::to_string(tc.bit_in_lane)},
            {"lane_mask", hex128(tc.abs_lo, tc.abs_hi)},
            {"instruction_bits", hexWidth(tc.instruction_bits, 32)},
            {"decoded_kind", tc.decoded_kind},
            {"decoded_precision", precisionName(tc.decoded_precision_bits)},
            {"decoded_element_width", std::to_string(tc.decoded_element_width)},
            {"decoded_lanes", std::to_string(tc.decoded_lanes)},
            {"decoded_reliable", tc.decoded_reliable ? "1" : "0"},
            {"manifest_precision", precision},
            {"manifest_lane_width", std::to_string(lane_width)},
            {"manifest_lane_offset", std::to_string(lane_offset)},
            {"precision_match", tc.precision_match ? "1" : "0"},
            {"lane_match", tc.lane_match ? "1" : "0"},
        };
        if (tc.field_lo >= 0)
            kv.push_back({"field_lo", std::to_string(tc.field_lo)});
        if (tc.field_hi >= 0)
            kv.push_back({"field_hi", std::to_string(tc.field_hi)});
        // [FSU][F5] The commit of the first activated exposure's consumer
        // is the FIRST REAL IMPACT. Record its latency from activation and
        // carry the permanent-fault identity onto the L5 witness.
        if (permanent_stuck && f5_armed && tc.fault_id == f5_fault_id) {
            kv.push_back({"op_class", tc.op_class});
            kv.push_back({"reg_class", tc.reg_class});
            f5_commit_seen = true;
            f5_first_impact_sn = inst->seqNum;
            f5_first_impact_tick = curTick();
            f5_first_impact_latency =
                (f5_first_activated_tick &&
                 curTick() >= f5_first_activated_tick)
                    ? (uint64_t)(curTick() - f5_first_activated_tick)
                    : 0;
            kv.push_back({"install_event",
                          std::to_string(f5_install_event)});
            kv.push_back({"stuck_polarity",
                          std::to_string(f5_polarity)});
            kv.push_back({"fixed_mask", hex64(f5_fixed_mask)});
            kv.push_back({"first_eligible_sn",
                          std::to_string(f5_first_eligible_sn)});
            kv.push_back({"first_activated_sn",
                          f5_first_activated_sn
                              ? std::to_string(f5_first_activated_sn)
                              : std::string()});
            kv.push_back({"affected_sn",
                          std::to_string(f5_first_impact_sn)});
            kv.push_back({"first_impact_latency",
                          std::to_string(f5_first_impact_latency)});
            kv.push_back({"exposure_count",
                          std::to_string(f5_exposures_total)});
            kv.push_back({"activated_exposure_count",
                          std::to_string(f5_activated_total)});
            kv.push_back({"last_exposure_sn",
                          std::to_string(f5_last_exposure_sn)});
            kv.push_back({"sample_policy", f5PolicyString()});
            kv.push_back({"exposures_total",
                          std::to_string(f5_exposures_total)});
            kv.push_back({"exposures_sampled",
                          std::to_string(f5_exposures_sampled)});
            kv.push_back({"exposures_dropped",
                          std::to_string(f5_exposures_total >
                                         f5_exposures_sampled
                                             ? f5_exposures_total -
                                               f5_exposures_sampled
                                             : 0)});
        }
        if (!tc.has_l4) {
            kv.push_back({"outcome", "arch_side_effect"});
            tc.l4_id = emitFsu("consumer", tc.fault_id, tc.l2_id, kv);
            tc.has_l4 = true;
        }
        kv.push_back({"detection_layer", "L5"});
        kv.push_back({"outcome", "errant_commit"});
        kv.push_back({"contained", "0"});
        const uint64_t commit_eid = emitFsu("commit", tc.fault_id,
                                            tc.l4_id, kv);
        if (commit_eid && permanent_stuck && f5_armed &&
            tc.fault_id == f5_fault_id)
            f5_terminal_parent = commit_eid;
        tc.committed = true;
    }

    void
    CHAOSFPU::noteNotActivated()
    {
        for (auto &f : faulted_regs) {
            if (f.consumed || f.squashed)
                continue;
            // [FSU][F5] A permanent fault's terminal is the F5 chain_end
            // (exposures_total/activated_exposure_count/terminal). A
            // generic not_activated event here would contradict a nonzero
            // activated_exposure_count and falsely say the value never
            // changed.
            if (f.f5)
                continue;
            std::vector<std::pair<std::string, std::string>> kv = {
                {"producer_seq", std::to_string(f.producer_sn)},
                {"phys_reg", std::to_string(f.reg_index)},
                {"reg_class", regClassName(f.reg_class)},
                {"instruction_bits", hexWidth(f.instruction_bits, 32)},
                {"decoded_kind", f.decoded_kind},
                {"decoded_precision",
                 precisionName(f.decoded_precision_bits)},
                {"decoded_element_width",
                 std::to_string(f.decoded_element_width)},
                {"decoded_lanes", std::to_string(f.decoded_lanes)},
                {"decoded_reliable", f.decoded_reliable ? "1" : "0"},
                {"manifest_precision", precision},
                {"manifest_lane_width", std::to_string(lane_width)},
                {"manifest_lane_offset", std::to_string(lane_offset)},
                {"precision_match", f.precision_match ? "1" : "0"},
                {"lane_match", f.lane_match ? "1" : "0"},
                {"field", f.field},
                {"precision", precision},
                {"lane_width", std::to_string(f.lane_width)},
                {"lane_offset", std::to_string(f.lane_offset)},
                {"bit_indices", std::to_string(f.abs_bit)},
                {"bit_in_lane", std::to_string(f.bit_in_lane)},
                {"fault_mask", hex64(f.mask)},
                {"lane_mask", hex128(f.abs_lo, f.abs_hi)},
                {"activated", "0"},
                {"value_hash", hash64(f.after)},
            };
            emitFsu("not_activated", f.fault_id, f.l1_id, kv);
        }
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
                    dumpCensus(*(log_stream->stream()));
            });
        }
        // [FSU][FP08] The early-return proxy counters must be visible in the
        // injection pass too, not only in the countOnly census.
        if (fpsr_suppress || rounding_sub) {
            registerExitCallback([this]() {
                if (!log_stream || !log_stream->stream())
                    return;
                std::ostream &os = *(log_stream->stream());
                if (fpsr_suppress) {
                    os << "CHAOS_FPSR_ATTEMPTED=" << fpsr_attempted << "\n";
                    os << "CHAOS_FPSR_APPLIED=" << fpsr_applied << "\n";
                    os << "CHAOS_FPSR_SUPPRESSED=" << suppressed_count << "\n";
                    os << "CHAOS_FPSR_REASON=fpsr_not_architecturally_modeled\n";
                }
                if (rounding_sub) {
                    os << "CHAOS_ROUNDING_ATTEMPTED=" << rounding_attempted
                       << "\n";
                    os << "CHAOS_ROUNDING_APPLIED=" << rounding_applied
                       << "\n";
                }
            });
        }
        // [FSU][D3] Honest decode-rejection accounting. A mismatch rejects
        // the candidate (no ordinal consumption); it never fabricates an
        // injection or a chain event.
        registerExitCallback([this]() {
            if (!log_stream || !log_stream->stream())
                return;
            if (decode_reject_count || !decode_kind_counts.empty()) {
                std::ostream &os = *(log_stream->stream());
                os << "CHAOS_DECODE_REJECTS=" << decode_reject_count
                   << "\n";
                for (const auto &kv : decode_reject_reasons)
                    os << "CHAOS_DECODE_REJECT_REASON " << kv.first
                       << "=" << kv.second << "\n";
                for (const auto &kv : decode_kind_counts)
                    os << "CHAOS_DECODE_KIND " << kv.first
                       << "=" << kv.second << "\n";
            }
        });
        // [FSU] Explicit not_activated terminal for faults never consumed.
        // The chain checker maps this to terminal=not_activated (never
        // inferred from a missing event).
        registerExitCallback([this]() { noteNotActivated(); });
        // [FSU][F5] The terminal chain_end is NOT registered as a global exit
        // callback: callback order is construction-order dependent and the
        // propagation tracer may close its event stream first. The flush hook
        // is registered on the tracer at installation time (see
        // notePermanentExposure), so it always runs before gzclose.
        if (rate_mode) {
            // Honest end-of-run rate accounting: the driver must see every
            // declared ordinal actually injected. A shortfall is loud.
            registerExitCallback([this]() {
                const size_t total = rate_ordinals.size();
                std::ostream *os = (log_stream && log_stream->stream())
                    ? log_stream->stream() : nullptr;
                if (next_rate_index < total) {
                    warn("CHAOSFPU: rate ordinals unreached: %zu/%zu "
                         "injected\n", next_rate_index, total);
                    if (os)
                        *os << "CHAOS_RATE_UNREACHED=" << (total - next_rate_index)
                            << " injected=" << next_rate_index
                            << " ordinals=" << total << std::endl;
                } else if (os) {
                    *os << "CHAOS_RATE_COMPLETE=" << total << std::endl;
                }
            });
        }
    }

} // namespace gem5
