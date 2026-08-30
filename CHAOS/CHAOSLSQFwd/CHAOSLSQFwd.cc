#include "cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh"
#include "params/CHAOSLSQFwd.hh"

#include <iostream>
#include <fstream>

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
          fault_mask(std::bitset<64>(p.faultMask)),
          mask_width(p.maskWidth),
          structural_fault_enum(stringToStructuralFault(p.structuralFault)),
          skew_bytes(p.skewBytes),
          num_bits_to_change(p.bitsToChange),
          byte_offset(p.byteOffset),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          rng(rng_seed != 0 ? rng_seed : rd()),
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
            case FaultType::Random: return "random";  // G7: clear -Wswitch
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
            case StructuralFault::None:         return "none";  // G7: clear -Wswitch
        }
        return "none";
    }

    // S1-5 (P-D1): apply a *structural* (whole-word) fault to the delivered
    // data. Unlike the bit-level FaultType path (multi-byte AND/OR/XOR), these
    // re-route the entire delivered word:
    //   ByteLaneSkew: rotate the byte array right by k bytes — models the D1
    //     signature where core 179 delivered rol_k(stale array-head content)
    //     (15:58: rol1; 0814: rol6). Bit-exact against crash values
    //     (MICROARCH_SUPPLEMENT §2.2). A right-rotation by k delivers, for byte
    //     lane n, the content of lane (n+k) mod size — a fill-buffer byte-lane
    //     mux selecting the wrong phase.
    //   AllZero: deliver an all-zero word — models the D1 "empty/invalid slot"
    //     state (15:42: __per_cpu_offset[176] delivered 0).
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
                // Right-rotate the byte array by k (byte lane n gets data[(n+k)%size]).
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
        if (write_log) {
            *(log_stream->stream())
                << "Cycle: " << cpu->curCycle()
                << ", CPU: " << cpu->name()
                << ", Site: store->load_forward"
                << ", StructuralFault: " << structuralFaultToString(structural_fault_enum)
                << ", Vaddr: 0x" << std::hex << vaddr << std::dec
                << ", FwdSize: " << size
                << std::endl;
        }
        DPRINTF(LSQUnit, "CHAOSLSQFwd: structural %s on forwarded data "
                "(vaddr=%#x size=%u)\n",
                structuralFaultToString(structural_fault_enum), vaddr, size);
    }

    uint64_t
    CHAOSLSQFwd::generateRandomMask(int bits_to_change)
    {
        // D2: 64-bit mask (was 8-bit). For maskWidth=1 the caller truncates
        // to the low 8 bits (legacy single-byte behavior); for maskWidth>1
        // the mask spans the whole little-endian window.
        uint64_t mask = 0;
        // Bit positions span [0, mask_width*8 - 1] so the random flip can
        // land in any byte of the window (not just byte 0).
        int bit_span = mask_width * 8;
        if (bit_span > 64) bit_span = 64;  // paranoia
        std::uniform_int_distribution<int> bitDist(0, bit_span - 1);
        while (bits_to_change-- > 0) mask |= (1ULL << bitDist(rng));
        return mask;
    }

    void
    CHAOSLSQFwd::writeLog(const char *type, unsigned size, Addr vaddr,
                          int byte_off, uint64_t mask, int width)
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
            << ", MaskWidth: " << width
            << ", Mask: 0x" << std::hex << mask << std::dec
            << std::endl;
    }

    void
    CHAOSLSQFwd::corrupt(uint8_t *data, unsigned size, Addr vaddr)
    {
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

        // S1-5 (P-D1): structural (whole-word) faults take precedence over
        // the D2 per-byte bit-fault path when configured. They cannot be
        // expressed as a bit flip (verified bit-exact vs core 179 crashes),
        // so they are a separate axis.
        if (structural_fault_enum != StructuralFault::None) {
            applyStructuralFault(data, size, vaddr);
            return;
        }

        // Choose byte to corrupt (low byte of the masked window).
        int off = byte_offset;
        if (off < 0) {
            std::uniform_int_distribution<int> bdist(0, (int)size - 1);
            off = bdist(rng);
        }
        if (off >= (int)size) off = (int)size - 1;

        // D2: maskWidth consecutive bytes (little-endian) starting at `off`.
        // Clamp the window to the forwarded buffer so we never run off the
        // end. maskWidth=1 + mask low 8 bits == legacy single-byte behavior.
        int width = mask_width;
        if (width < 1) width = 1;
        if (width > 8) width = 8;
        if (off + width > (int)size) width = (int)size - off;
        if (width < 1) width = 1;  // paranoia

        uint64_t mask = fault_mask.any()
            ? fault_mask.to_ullong()
            : generateRandomMask(num_bits_to_change);
        // Truncate the mask to the active window width.
        uint64_t width_mask = (width >= 8) ? mask : (mask & ((1ULL << (8*width)) - 1));

        FaultType chosen = fault_type_enum;
        if (fault_type_enum == FaultType::Random) {
            int idx = random_fault_distribution(rng);
            chosen = static_cast<FaultType>(idx);
        }

        // Read the window as a little-endian uint64, apply the mask, write
        // back only the active bytes (same RMW pattern as CHAOSPhysReg vec).
        uint64_t win_val = 0;
        for (int b = 0; b < width; ++b)
            win_val |= ((uint64_t)data[off + b]) << (8 * b);

        switch (chosen) {
            case FaultType::StuckAtZero:
                win_val &= ~width_mask;
                stats->numStuckAtZero++;
                break;
            case FaultType::StuckAtOne:
                win_val |= width_mask;
                stats->numStuckAtOne++;
                break;
            case FaultType::BitFlip:
                win_val ^= width_mask;
                stats->numBitFlips++;
                break;
            default: break;
        }

        for (int b = 0; b < width; ++b)
            data[off + b] = (uint8_t)((win_val >> (8 * b)) & 0xff);

        stats->numFaultsInjected++;
        ++faults_injected_count;
        writeLog(faultTypeToString(chosen), size, vaddr, off, width_mask, width);
        DPRINTF(LSQUnit, "CHAOSLSQFwd: corrupted forwarded bytes [%d+%d) "
                "(vaddr=%#x mask=%#llx type=%s)\n", off, width, vaddr,
                (unsigned long long)width_mask, faultTypeToString(chosen));
    }

    CHAOSLSQFwd::CHAOSLSQFwdStats::CHAOSLSQFwdStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total forwarded-data faults injected"),
          ADD_STAT(numBitFlips, statistics::units::Count::get(),
                   "Bit-flip faults on forwarded data"),
          ADD_STAT(numStuckAtZero, statistics::units::Count::get(),
                   "Stuck-at-0 faults on forwarded data"),
          ADD_STAT(numStuckAtOne, statistics::units::Count::get(),
                   "Stuck-at-1 faults on forwarded data"),
          ADD_STAT(numStructuralByteLaneSkew, statistics::units::Count::get(),
                   "S1-5 P-D1 byte_lane_skew faults (core179 D1 rol signature)"),
          ADD_STAT(numStructuralAllZero, statistics::units::Count::get(),
                   "S1-5 P-D1 all_zero faults (core179 D1 empty-slot signature)")
    {}

} // namespace gem5
