#include "cpu/o3/CHAOSFPU/CHAOSFPU.hh"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <sstream>

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst, opClass, isFloating
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // FSU_PROP stream
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
          bitseg(p.bitseg),
          fma_weighted(p.fmaWeighted),
          recurring_stuck(p.recurringStuck),
          rounding_sub(p.roundingSub),
          f3_dependent(p.f3Dependent),
          exp_lo(p.expLo),
          exp_hi(p.expHi),
          fpsr_suppress(p.fpsrSuppress),
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

        // [FSU][D2] F1/F2/F3: exact eligible-ordinal match. The ordinal
        // stream is the same `has_fp_dest` stream countOnly measured; no
        // probability draw, no geometric skip, no second sampler.
        if (rate_mode) {
            if (!has_fp_dest) return false;
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
            ++suppressed_count;
            return false;
        }

        // v1.1 Phase 9 mode 4 — rounding_sub: one-ULP nudge to the
        // OPPOSITE neighbor of the rounded result (E3 proxy for a flipped
        // FPCR RMODE changing one rounding decision). Applies to the first
        // FP/vector dest.
        if (rounding_sub) {
            bool okr = false;
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
              }
            }
            if (okr) {
                faults_injected_count++;
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

        RegVal mask;
        if (recurring_stuck) {
            // v1.1 Phase 9 mode 3 — the SAME fixed mask every event: the
            // directed --fault_mask if given, else drawn once from the
            // uniform pick and reused for the whole run.
            if (!recurring_mask_drawn) {
                recurring_mask = fault_mask ? fault_mask
                                            : (1ULL << (rng() % 64));
                recurring_mask_drawn = true;
            }
            mask = recurring_mask;
        } else if (fault_mask) {
            mask = fault_mask;
        } else if (fma_weighted) {
            // v1.1 Phase 9 mode 2 — fma_intermediate (E3 behavioral
            // proxy, plan fallback (b)): draw the field from method3's
            // matched distribution (mant 85% / exp 10% / sign 5%), then
            // the bit uniformly within the field. Implemented as the
            // mant_* / exp_* / sign bitseg ranges.
            int lo, hi;
            unsigned field = (unsigned)(rng() % 100);
            if (field < 85)      { lo = 0;  hi = 51; }  // mantissa (52 bits)
            else if (field < 95) { lo = 52; hi = 62; }  // exponent (11 bits)
            else                 { lo = 63; hi = 63; }  // sign
            int bit = lo + (int)(rng() % (unsigned)(hi - lo + 1));
            mask = (1ULL << bit);
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
        int fault_cls = -1, fault_idx = -1;
        uint64_t oldv = 0, newv = 0;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
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
            switch (dest->classValue()) {
              case VecRegClass: {
                // XOR the low 8 bytes of the vector register's PRF blob.
                void *vp = o3cpu->getWritableReg(dest, dyn_inst->threadNumber);
                if (!vp) break;
                std::memcpy(&oldv, vp, 8);
                uint64_t *q = reinterpret_cast<uint64_t*>(vp);
                *q ^= (uint64_t)mask;
                std::memcpy(&newv, vp, 8);
                fault_cls = (int)dest->classValue();
                fault_idx = dest->index();
                ok = true;
                break;
              }
              case FloatRegClass:
              case VecElemClass: {
                RegVal v = o3cpu->getReg(dest, dyn_inst->threadNumber);
                oldv = (uint64_t)v;
                newv = (uint64_t)(v ^ mask);
                o3cpu->setReg(dest, v ^ mask, dyn_inst->threadNumber);
                fault_cls = (int)dest->classValue();
                fault_idx = dest->index();
                ok = true;
                break;
              }
              default:
                break;  // int/cond/misc dests are CHAOSExec's scope
            }
        }
        if (!ok) {
            if (rate_mode)
                panic("CHAOSFPU: rate ordinal %llu matched but no writable "
                      "FP/vector dest (fault not applied)\n",
                      (unsigned long long)injected_eligible_ordinal);
            return false;  // no FP/vector dest register on this inst
        }
        faults_injected_count++;
        noteFaultApplied(dyn_inst, fault_cls, fault_idx, oldv, newv, mask);
        if (rate_mode) ++next_rate_index;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: dyn_inst_execute, opClass=" << (int)oc
                << ", sn=" << dyn_inst->seqNum
                << (bitseg.empty() ? std::string() : ", bitseg=" + bitseg)
                << (fma_weighted ? ", mode=fma_intermediate" : "")
                << (recurring_stuck ? ", mode=recurring_result_stuck" : "")
                << ", mask=0x" << std::hex << mask << std::dec
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
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
        kv.push_back({"corr", std::string(kind) == "fault_applied"
                              ? "origin" : "fsu_taint"});
        return o3cpu->chaosPropagation->notePropEvt(kind, kv);
    }

    void
    CHAOSFPU::noteFaultApplied(o3::DynInst *inst, int reg_class,
                               int reg_index, uint64_t oldv, uint64_t newv,
                               uint64_t mask)
    {
        if (!inst || reg_class < 0 || reg_index < 0)
            return;
        const uint64_t fid = next_fault_id++;
        const std::string field = !bitseg.empty() ? bitseg :
            (recurring_stuck ? "recurring_result_stuck" :
             fma_weighted ? "fma_intermediate" :
             rounding_sub ? "rounding_sub" : "uniform");
        const int bit = mask ? __builtin_ctzll(mask) : -1;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"dyn_inst_seq", std::to_string(inst->seqNum)},
            {"pc", hex64(inst->pcState().instAddr())},
            {"opcode", inst->staticInst ? inst->staticInst->getName() : ""},
            {"phys_reg", std::to_string(reg_index)},
            {"field", field},
            {"fault_mask", hex64(mask)},
            {"bit_indices", bit >= 0 ? std::to_string(bit) : ""},
            {"lane_width", "64"},
            {"lane_offset", "0"},
            {"before", hex64(oldv)},
            {"after", hex64(newv)},
            {"before_hash", hash64(oldv)},
            {"after_hash", hash64(newv)},
            {"value_hash", hash64(newv)},
            {"attempted", "1"},
            {"activated", ""},
            {"thread_id", std::to_string((int)inst->threadNumber)},
        };
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
        faulted_regs.push_back({fid, l0, l1, inst->seqNum, curTick(),
                                (int)inst->threadNumber, reg_class, reg_index,
                                oldv, newv, mask, field, false});
    }

    void
    CHAOSFPU::noteConsumerExecute(o3::DynInst *inst)
    {
        if (!inst || faulted_regs.empty())
            return;
        if (tainted_consumers.count(inst->seqNum))
            return;
        for (auto &f : faulted_regs) {
            if (f.consumed)
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
                    {"pc", hex64(inst->pcState().instAddr())},
                    {"opcode", inst->staticInst
                                   ? inst->staticInst->getName() : ""},
                    {"activated", "1"},
                    {"value_hash", hash64(f.after)},
                    {"field", f.field},
                    {"thread_id", std::to_string((int)inst->threadNumber)},
                };
                const uint64_t l2 = emitFsu("operand_read", f.fault_id,
                                            f.l1_id, kv);
                TaintedConsumer tc;
                tc.fault_id = f.fault_id;
                tc.l2_id = l2;
                tc.consumer_sn = inst->seqNum;
                tc.field = f.field;
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
        };
        if (!tc.has_l4) {
            kv.push_back({"outcome", "arch_side_effect"});
            tc.l4_id = emitFsu("consumer", tc.fault_id, tc.l2_id, kv);
            tc.has_l4 = true;
        }
        kv.push_back({"detection_layer", "L5"});
        kv.push_back({"outcome", "errant_commit"});
        kv.push_back({"contained", "0"});
        emitFsu("commit", tc.fault_id, tc.l4_id, kv);
        tc.committed = true;
    }

    void
    CHAOSFPU::noteNotActivated()
    {
        for (auto &f : faulted_regs) {
            if (f.consumed)
                continue;
            std::vector<std::pair<std::string, std::string>> kv = {
                {"producer_seq", std::to_string(f.producer_sn)},
                {"phys_reg", std::to_string(f.reg_index)},
                {"field", f.field},
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
                    *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT="
                        << eligible_count << std::endl;
            });
        }
        // [FSU] Explicit not_activated terminal for faults never consumed.
        // The chain checker maps this to terminal=not_activated (never
        // inferred from a missing event).
        registerExitCallback([this]() { noteNotActivated(); });
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
