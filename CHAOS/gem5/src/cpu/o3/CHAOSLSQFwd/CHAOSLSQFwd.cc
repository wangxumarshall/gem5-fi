#include "cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh"
#include "params/CHAOSLSQFwd.hh"

#include <iostream>
#include <fstream>
#include <vector>
#include <cstring>

#include "base/output.hh"
#include "cpu/o3/cpu.hh"
#include "debug/LSQUnit.hh"

namespace gem5
{

    CHAOSLSQFwd::CHAOSLSQFwd(const CHAOSLSQFwdParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fault_type_enum(stringToFaultType(p.faultType)),
          structural_fault_enum(stringToStructuralFault(p.structuralFault)),
          skew_bytes(p.skewBytes),
          fault_mask(std::bitset<32>(p.faultMask)),
          num_bits_to_change(p.bitsToChange),
          byte_offset(p.byteOffset),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          rng(rng_seed != 0 ? rng_seed : [](){ std::random_device r; return r(); }()),
          log_stream(nullptr),
          stats(nullptr)
    {
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSLSQFwd: cpu is not an O3CPU. CHAOSLSQFwd only supports "
                "O3CPU (it hooks the O3 LSQ store->load forwarding path). "
                "Cast failed.");
        }
        if (probability > 0.0f) {
            log_stream = simout.create("lsq_fwd_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSLSQFwd: Could not open log file");
            }
            stats = std::make_unique<CHAOSLSQFwdStats>(this);
            random_fault_distribution = std::discrete_distribution<int>(
                {0.9, 0.05, 0.05});  // bit_flip / stuck0 / stuck1
            // Register self with the CPU so lsq_unit.cc can reach this
            // injector via cpu->lsqFwd. cpu is guaranteed constructed first
            // (it was passed as a Param). Safe because lsq_unit only reads
            // lsqFwd during execute(), long after SimObject construction.
            cpu->lsqFwd = this;
        }
        if (structural_fault_enum != StructuralFault::None &&
            probability <= 0.0f) {
            // Structural faults need the injector armed (probability>0) to
            // reach the hot path; warn rather than panic so legacy configs
            // that set structuralFault=none still work with probability=0.
            warn("CHAOSLSQFwd: structuralFault set but probability<=0; "
                 "structural path will never fire.");
        }
        if (skew_bytes < 0 || skew_bytes > 7) {
            warn("CHAOSLSQFwd: skewBytes=%d out of [0,7]; 0 means random "
                 "1..7 per event. Clamping.", skew_bytes);
            skew_bytes = 0;
        }
    }

    CHAOSLSQFwd::~CHAOSLSQFwd() {}

    CHAOSLSQFwd::FaultType
    CHAOSLSQFwd::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        else if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        else if (s == "stuck_at_one") return FaultType::StuckAtOne;
        return FaultType::Random;
    }

    const char*
    CHAOSLSQFwd::faultTypeToString(FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
            case FaultType::Random: return "random";
        }
        return "random";
    }

    CHAOSLSQFwd::StructuralFault
    CHAOSLSQFwd::stringToStructuralFault(const std::string &s) {
        if (s == "byte_lane_skew") return StructuralFault::ByteLaneSkew;
        if (s == "all_zero")       return StructuralFault::AllZero;
        return StructuralFault::None;
    }

    const char*
    CHAOSLSQFwd::structuralFaultToString(StructuralFault f) {
        switch (f) {
            case StructuralFault::ByteLaneSkew: return "byte_lane_skew";
            case StructuralFault::AllZero:      return "all_zero";
            case StructuralFault::None:         return "none";
        }
        return "none";
    }

    // P-D1: apply a *structural* (whole-word) fault to the delivered data.
    // Unlike the bit-level FaultType path (one-byte AND/OR/XOR), these re-route
    // the entire delivered word:
    //   ByteLaneSkew: rotate the byte array right by k bytes — models the D1
    //     signature where core 179 delivered rol_k(stale array-head content)
    //     (15:58: rol1; 0814: rol6). A right-rotation by k delivers, for byte
    //     lane n, the content of lane (n+k) mod size — i.e. a fill-buffer
    //     byte-lane mux selecting the wrong phase. Verified bit-exact against
    //     the crash values (MICROARCH_SUPPLEMENT §2.2).
    //   AllZero: deliver an all-zero word — models the D1 "empty/invalid slot"
    //     state (15:42: __per_cpu_offset[176] delivered 0).
    // size is the forwarded size in bytes (typically 8 for a 64-bit GPR load).
    void
    CHAOSLSQFwd::applyStructuralFault(uint8_t *data, unsigned size, Addr vaddr)
    {
        if (size == 0) return;
        switch (structural_fault_enum) {
            case StructuralFault::ByteLaneSkew: {
                int k = skew_bytes;
                if (k == 0) {
                    std::uniform_int_distribution<int> kd(1, 7);
                    k = kd(rng);
                }
                if (k < 1) k = 1;
                if (k >= (int)size) k = (int)size - 1;
                // Right-rotate the byte array by k (byte lane n gets data[n-k]).
                std::vector<uint8_t> tmp(data, data + size);
                for (unsigned n = 0; n < size; n++)
                    data[n] = tmp[(n + k) % size];
                stats->numStructuralByteLaneSkew++;
                break;
            }
            case StructuralFault::AllZero:
                std::memset(data, 0, size);
                stats->numStructuralAllZero++;
                break;
            case StructuralFault::None:
                break;
        }
        stats->numFaultsInjected++;
        ++faults_injected_count;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Site: store->load_forward"
            << ", StructuralFault: " << structuralFaultToString(structural_fault_enum)
            << ", Vaddr: 0x" << std::hex << vaddr << std::dec
            << ", FwdSize: " << size
            << std::endl;
        DPRINTF(LSQUnit, "CHAOSLSQFwd: structural %s on forwarded data "
                "(vaddr=%#x size=%u)\n",
                structuralFaultToString(structural_fault_enum), vaddr, size);
    }

    int
    CHAOSLSQFwd::generateRandomMask(int bits_to_change)
    {
        // 8-bit mask (applied to one byte of the forwarded buffer)
        int mask = 0;
        std::uniform_int_distribution<int> bitDist(0, 7);
        while (bits_to_change-- > 0) mask |= (1 << bitDist(rng));
        return mask;
    }

    void
    CHAOSLSQFwd::writeLog(const char *type, unsigned size, Addr vaddr,
                          int byte_off, int mask)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Site: store->load_forward"
            << ", FaultType: " << type
            << ", Vaddr: 0x" << std::hex << vaddr << std::dec
            << ", FwdSize: " << size
            << ", ByteOffset: " << byte_off
            << ", Mask: " << std::bitset<8>(mask)
            << std::endl;
    }

    void
    CHAOSLSQFwd::corrupt(uint8_t *data, unsigned size, Addr vaddr)
    {
        // numHooksCalled: count EVERY store→load-forward event (i.e. every call
        // to this hook) BEFORE any gating, mirroring CHAOSPTW/CHAOSAddrPath. This
        // distinguishes "forward did not happen (hook not called)" from "forward
        // happened but probability did not select it (numFaultsInjected=0)" —
        // essential to diagnose why D1 gives numStructuralByteLaneSkew=0 in FS
        // early-boot (is the store→load-forward path unexercised, or exercised
        // but not selected?). Prior versions lacked this stat, making D1's FS
        // behavior unattributable (adversarial-review instrumentation gap).
        if (stats) stats->numHooksCalled++;
        // Hot-path short-circuit: no injection configured.
        if (probability <= 0.0f) return;
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return;
        if (last_clock != Cycles(0) && cur > last_clock) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        // Bernoulli: does this forwarding event get corrupted?
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return;
        if (size == 0) return;

        // P-D1: structural (whole-word) faults take precedence over the
        // legacy per-byte bit-fault path when configured. They cannot be
        // expressed as a bit flip (verified), so they are a separate axis.
        if (structural_fault_enum != StructuralFault::None) {
            applyStructuralFault(data, size, vaddr);
            return;
        }

        // Choose byte to corrupt.
        int off = byte_offset;
        if (off < 0) {
            std::uniform_int_distribution<int> bdist(0, (int)size - 1);
            off = bdist(rng);
        }
        if (off >= (int)size) off = (int)size - 1;

        int mask = fault_mask.any()
            ? (int)(fault_mask.to_ulong() & 0xff)
            : generateRandomMask(num_bits_to_change);

        FaultType chosen = fault_type_enum;
        if (fault_type_enum == FaultType::Random) {
            int idx = random_fault_distribution(rng);
            chosen = static_cast<FaultType>(idx);
        }

        switch (chosen) {
            case FaultType::StuckAtZero:
                data[off] &= ~(uint8_t)mask;
                stats->numStuckAtZero++;
                break;
            case FaultType::StuckAtOne:
                data[off] |= (uint8_t)mask;
                stats->numStuckAtOne++;
                break;
            case FaultType::BitFlip:
                data[off] ^= (uint8_t)mask;
                stats->numBitFlips++;
                break;
            default: break;
        }
        stats->numFaultsInjected++;
        ++faults_injected_count;
        writeLog(faultTypeToString(chosen), size, vaddr, off, mask);
        DPRINTF(LSQUnit, "CHAOSLSQFwd: corrupted forwarded byte %d (vaddr=%#x "
                "mask=%#x type=%s)\n", off, vaddr, mask,
                faultTypeToString(chosen));
    }

    CHAOSLSQFwd::CHAOSLSQFwdStats::CHAOSLSQFwdStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numHooksCalled, statistics::units::Count::get(),
                   "Times the store→load-forward hook was called (D1; every "
                   "forwarding event while injector active, before prob/first-"
                   "clock gating)"),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total forwarded-data faults injected"),
          ADD_STAT(numBitFlips, statistics::units::Count::get(),
                   "Bit-flip faults on forwarded data"),
          ADD_STAT(numStuckAtZero, statistics::units::Count::get(),
                   "Stuck-at-0 faults on forwarded data"),
          ADD_STAT(numStuckAtOne, statistics::units::Count::get(),
                   "Stuck-at-1 faults on forwarded data"),
          ADD_STAT(numStructuralByteLaneSkew, statistics::units::Count::get(),
                   "Structural byte-lane-skew faults (P-D1, core-179 D1)"),
          ADD_STAT(numStructuralAllZero, statistics::units::Count::get(),
                   "Structural all-zero deliveries (P-D1, core-179 D1)")
    {}

} // namespace gem5
