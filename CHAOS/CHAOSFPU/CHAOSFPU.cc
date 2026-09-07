#include "cpu/o3/CHAOSFPU/CHAOSFPU.hh"
#include "params/CHAOSFPU.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/rob.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "base/trace.hh"
#include "debug/CHAOSFPU.hh"
#include <iostream>
#include <fstream>

namespace gem5
{
    CHAOSFPU::CHAOSFPU(const CHAOSFPUParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fault_mask(p.faultMask),
          num_bits_to_change(p.bitsToChange),
          bit_seg(stringToBitSeg(p.bitSegment)),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          semantic_role(p.semanticRole),
          rng([this]() {
              std::random_device local_rd;
              return rng_seed != 0 ? std::mt19937(rng_seed) : std::mt19937(local_rd());
          }()),
          inter_fault_cycles_dist(probability),
          log_stream(nullptr),
          attackEvent([this] { this->attackCheck(); }, name()),
          stats(nullptr)
    {
        if (!cpu) throw std::runtime_error(
            "CHAOSFPU: cpu not O3CPU. O3-only (needs robAccess).");
        if (probability > 0.0f) {
            log_stream = simout.create("fpu_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSFPU: Could not open log file");
            stats = std::make_unique<Stats>(this);
            // v2 writeback-path hook: self-attach on the CPU so
            // DynInst::setRegOperand can reach us (same pattern as
            // lsqFwd/addrPath).
            cpu->setChaosFPUHook(this);
        }
    }

    void CHAOSFPU::startup() {
        if (!probability) return;
        // v1 ROB-head sampling only as a fallback; the primary v2 hook is
        // event-driven from setRegOperand (no attackEvent needed when the
        // writeback hook is armed). Keep the event for the legacy path so
        // old manifests (events_to_skip semantics) still behave, but it
        // will usually be redundant.
        scheduleAttackEvent(first_clock + Cycles(inter_fault_cycles_dist(rng)));
    }
    CHAOSFPU::~CHAOSFPU() {}

    // §5.6 v2 writeback-path hook: corrupt the FP result BEFORE it reaches
    // the PhysReg + result queue. This is the true FSU data-path point.
    void
    CHAOSFPU::maybeCorruptWriteback(const PhysRegIdPtr &reg, RegVal &val)
    {
        // FP filter: scalar FP (FloatRegClass) or SIMD FP (VecRegClass).
        const RegClassType cls = reg->classValue();
        if (cls != FloatRegClass && cls != VecRegClass) return;
        // Time window ([firstClock, lastClock] CPU-cycle domain, same as
        // the v1 attackEvent).
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return;
        if (last_clock != Cycles(0) && cur > last_clock) return;
        // G5 fault cap.
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        // Per-write Bernoulli draw.
        std::uniform_real_distribution<float> d(0.0f, 1.0f);
        if (d(rng) >= probability) return;

        uint64_t mask = genMask();
        if (mask == 0) return;
        RegVal old = val;
        val ^= mask;
        stats->numFpResultCorrupted++;
        stats->numFaultsInjected++;
        ++faults_injected_count;
        logCorruption("fp_writeback_result (v2 setRegOperand hook)",
                      reg, cls, old, val, mask);
    }

    // Blob overload: same gates; XOR the mask into the first 8 bytes of
    // the blob in place (vector lanes are little-endian packed).
    void
    CHAOSFPU::maybeCorruptWritebackBlob(const PhysRegIdPtr &reg,
                                        const void *val)
    {
        const RegClassType cls = reg->classValue();
        if (cls != FloatRegClass && cls != VecRegClass) return;
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return;
        if (last_clock != Cycles(0) && cur > last_clock) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        std::uniform_real_distribution<float> d(0.0f, 1.0f);
        if (d(rng) >= probability) return;

        uint64_t mask = genMask();
        if (mask == 0) return;
        uint8_t *bytes = const_cast<uint8_t*>(
            static_cast<const uint8_t*>(val));
        uint64_t old; __builtin_memcpy(&old, bytes, 8);
        uint64_t neu = old ^ mask;
        __builtin_memcpy(bytes, &neu, 8);
        stats->numFpResultCorrupted++;
        stats->numFaultsInjected++;
        ++faults_injected_count;
        logCorruption("fp_writeback_result (v2 setRegOperand blob hook)",
                      reg, cls, old, neu, mask);
    }

    // §5.6 source-read hook (scalar RegVal overload).
    void
    CHAOSFPU::maybeCorruptRead(const PhysRegIdPtr &reg, RegVal &val)
    {
        const RegClassType cls = reg->classValue();
        if (cls != FloatRegClass && cls != VecRegClass) return;
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return;
        if (last_clock != Cycles(0) && cur > last_clock) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        std::uniform_real_distribution<float> d(0.0f, 1.0f);
        if (d(rng) >= probability) return;

        uint64_t mask = genMask();
        if (mask == 0) return;
        RegVal old = val;
        val ^= mask;
        stats->numFpResultCorrupted++;
        stats->numFaultsInjected++;
        ++faults_injected_count;
        logCorruption("fp_source_read (v3 getRegOperand hook)", reg, cls,
                      old, val, mask);
    }

    // §5.6 source-read hook (blob overload — vector FP sources).
    void
    CHAOSFPU::maybeCorruptReadBlob(const PhysRegIdPtr &reg, void *val)
    {
        const RegClassType cls = reg->classValue();
        if (cls != FloatRegClass && cls != VecRegClass) return;
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return;
        if (last_clock != Cycles(0) && cur > last_clock) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        std::uniform_real_distribution<float> d(0.0f, 1.0f);
        if (d(rng) >= probability) return;

        uint64_t mask = genMask();
        if (mask == 0) return;
        uint8_t *bytes = static_cast<uint8_t*>(val);
        uint64_t old; __builtin_memcpy(&old, bytes, 8);
        uint64_t neu = old ^ mask;
        __builtin_memcpy(bytes, &neu, 8);
        stats->numFpResultCorrupted++;
        stats->numFaultsInjected++;
        ++faults_injected_count;
        logCorruption("fp_source_read (v3 getRegOperand blob hook)", reg,
                      cls, old, neu, mask);
    }

    // shared corruption logger for the v2/v3 hooks
    void
    CHAOSFPU::logCorruption(const char *site, const PhysRegIdPtr &reg,
                            RegClassType cls, uint64_t old, uint64_t neu,
                            uint64_t mask)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Site: " << site
            << ", PhysReg[" << reg->index() << "]"
            << ", Class: " << (cls == FloatRegClass ? "fp" : "vec")
            << ", Old: 0x" << std::hex << old
            << ", New: 0x" << std::hex << neu
            << ", Mask: 0x" << mask << std::dec
            << (!semantic_role.empty()
                ? ", SemanticRole: " + semantic_role : "")
            << std::endl;
    }

    CHAOSFPU::BitSeg CHAOSFPU::stringToBitSeg(const std::string &s) {
        if (s == "low")  return BitSeg::Low;   // [0:11]
        if (s == "mid")  return BitSeg::Mid;   // [12:47]
        if (s == "high") return BitSeg::High;  // [48:63]
        // §5.6D IEEE754 semantic segments (double layout: sign 63, exp
        // 62-52, mantissa 51-0) — the config's --fpu_bit_segment choices.
        if (s == "sign")    return BitSeg::Sign;     // [63]
        if (s == "exp")     return BitSeg::Exp;      // [62:52]
        if (s == "mantissa") return BitSeg::Mantissa; // [51:0]
        return BitSeg::All;
    }

    void CHAOSFPU::scheduleAttackEvent(Cycles delay) {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void CHAOSFPU::attackCheck() {
        if (!probability) return;
        uint64_t before = faults_injected_count;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *tc = cpu->getContext(tid);
            if (!tc || tc->status() == ThreadContext::Halted) continue;
            processFault(tid);
        }
        if (max_faults == 0 || faults_injected_count < max_faults) {
            // method1-formal fix (same as CHAOSRenameMap): when an attempt
            // was SKIPPED (head not a FP inst — e.g. the loop's loads/
            // stores), geometric(1.0) yields a 0-cycle interval -> poll
            // every cycle forever (observed: gemm_kernel + probability=1.0
            // hung the sim with zero injections, only numSkippedNonFp
            // growing). Enforce a minimum +1-cycle backoff on skip.
            unsigned next = inter_fault_cycles_dist(rng);
            if (faults_injected_count == before)  // no fault landed this try
                next = std::max(next, (unsigned)1);
            Cycles nc = cpu->curCycle() + Cycles(next);
            if (last_clock == Cycles(0) || nc <= last_clock)
                scheduleAttackEvent(Cycles(next));
        }
    }

    uint64_t CHAOSFPU::genMask() {
        if (fault_mask) return fault_mask;
        int lo, hi;
        switch (bit_seg) {
            case BitSeg::Low:  lo=0;  hi=11; break;
            case BitSeg::Mid:  lo=12; hi=47; break;
            case BitSeg::High: lo=48; hi=63; break;
            // §5.6D IEEE754 double segments (bit_spectrum.py-compatible)
            case BitSeg::Sign:    lo=63; hi=63; break;
            case BitSeg::Exp:     lo=52; hi=62; break;
            case BitSeg::Mantissa: lo=0; hi=51; break;
            default:           lo=0;  hi=63; break;
        }
        std::uniform_int_distribution<int> bd(lo, hi);
        uint64_t m = 0;
        for (int i = 0; i < num_bits_to_change; ++i) m |= (1ULL << bd(rng));
        return m;
    }

    void CHAOSFPU::processFault(ThreadID tid) {
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        const o3::DynInstPtr &head = cpu->robAccess().readHeadInst(tid);
        if (!head) { stats->numSkippedNonFp++; return; }

        // FP detection via DEST REGISTER CLASS, not isFloating(): the ARM
        // ISA never sets the IsFloating static-inst flag (only x86/riscv/
        // sparc operands.isa do) — observed on gemm_kernel: 144k head
        // samples, 0 hits, because isFloating() is ALWAYS false on ARM.
        // A scalar FP inst writes FloatRegClass; SIMD FP (FMLA/FMUL v*)
        // writes VecRegClass. Both are the FSU data path.
        bool is_fp = false;
        for (size_t i = 0; i < head->numDestRegs(); ++i) {
            PhysRegIdPtr dest = head->renamedDestIdx(i);
            if (!dest) continue;
            const RegClassType cls = dest->classValue();
            if (cls == FloatRegClass || cls == VecRegClass) {
                is_fp = true; break;
            }
        }
        if (!is_fp) {
            stats->numSkippedNonFp++;
            return;
        }
        if (head->getFault() != NoFault) { stats->numSkippedNonFp++; return; }

        uint64_t mask = genMask();
        if (mask == 0) return;
        // Corrupt the front instResult (writeback data path) via DynInst method.
        bool ok = head->corruptResultRegVal(mask);
        if (!ok) { stats->numResultPopped++; return; }  // FP but result already popped (writeback done)
        stats->numFpResultCorrupted++;
        stats->numFaultsInjected++;
        ++faults_injected_count;
        writeLog(tid, mask, 0, 63);
    }

    void CHAOSFPU::writeLog(ThreadID tid, uint64_t mask, int, int) {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Thread: " << tid
            << ", Site: fp_writeback_result"
            << ", Mask: 0x" << std::hex << mask << std::dec
            << (!semantic_role.empty() ? ", SemanticRole: " + semantic_role : "")
            << std::endl;
    }

    CHAOSFPU::Stats::Stats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total Exec faults injected"),
          ADD_STAT(numFpResultCorrupted, statistics::units::Count::get(),
                   "Integer writeback results corrupted (data-path)"),
          ADD_STAT(numSkippedNonFp, statistics::units::Count::get(),
                   "Skipped (ROB empty / non-int / no result / faulting)"),
          ADD_STAT(numResultPopped, statistics::units::Count::get(),
                   "FP head reached but instResult already popped (writeback done — too late to corrupt)")
    {}
} // namespace gem5
