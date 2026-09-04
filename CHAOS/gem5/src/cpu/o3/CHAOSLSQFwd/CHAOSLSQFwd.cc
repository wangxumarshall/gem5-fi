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
          struct_mode(stringToStructMode(p.structMode)),
          fault_mask(std::bitset<64>(p.faultMask)),
          num_bits_to_change(p.bitsToChange),
          byte_offset(p.byteOffset),
          lane_skew_k(p.laneSkewK),
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
            // Sampling-bias fix (findings.md Phase 2.2, same as
            // CHAOSL1DForward): skip a geometric(p=0.1) number of eligible
            // forwarding events before the first injection, so the single
            // fault (maxFaults=1) lands on a seed-dependent event instead
            // of always the first eligible one (same dynamic store->load
            // pair every rep on a deterministic stream).
            std::geometric_distribution<uint64_t> skip_dist(0.1);
            events_to_skip = skip_dist(rng);
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
            case FaultType::Random: return "random";  // §2.4: clear -Wswitch
        }
        return "random";
    }

    // §2.4 structured fault mode (fi-h6-h7 branch, H5 closed).
    CHAOSLSQFwd::StructMode
    CHAOSLSQFwd::stringToStructMode(const std::string &s) {
        if (s == "byte_lane_skew") return StructMode::ByteLaneSkew;
        if (s == "all_zero") return StructMode::AllZero;
        if (s == "fwd_source_sub") return StructMode::FwdSourceSub;
        return StructMode::ByteFlip;  // default / unknown
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
        // Hot-path short-circuit: no injection configured.
        if (probability <= 0.0f) return;
        // fwd_source_sub injects at the DECISION point (maybeSubstituteSource,
        // called before the memcpy); this post-forward corrupt hook must NOT
        // also fire in that mode (double-injection bug found in Phase 4.2
        // verification: an unlimited-faults run showed bit_flip lines while
        // in fwd_source_sub mode — the old hook was still active).
        if (struct_mode == StructMode::FwdSourceSub) return;
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return;
        if (last_clock != Cycles(0) && cur > last_clock) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        // Sampling-bias fix (findings.md Phase 2.2): skip the first N
        // eligible forwarding events (N ~ geometric(0.1) from the seed) so
        // the single fault lands on a seed-dependent event.
        if (events_to_skip > 0) {
            --events_to_skip;
            return;
        }

        // Bernoulli: does this forwarding event get corrupted?
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return;
        if (size == 0) return;

        // §2.4 structured fault modes (fi-h6-h7 branch, H5 closed):
        if (struct_mode == StructMode::ByteLaneSkew) {
            // Rotate the whole forwarded buffer by k bytes (rol_k) —
            // core179 D1 byte-lane phase signature (method2).
            int k = lane_skew_k % (int)size;
            if (k < 0) k += (int)size;
            if (k != 0) {
                uint8_t tmp[16];
                for (unsigned i = 0; i < size; i++) tmp[i] = data[i];
                for (unsigned i = 0; i < size; i++)
                    data[i] = tmp[(i + k) % size];
            }
            stats->numFaultsInjected++;
            ++faults_injected_count;
            writeLog("byte_lane_skew", size, vaddr, lane_skew_k, 0);
            DPRINTF(LSQUnit, "CHAOSLSQFwd: byte_lane_skew rol %d (vaddr=%#x)\n",
                    lane_skew_k, vaddr);
            return;
        }
        if (struct_mode == StructMode::AllZero) {
            for (unsigned i = 0; i < size; i++) data[i] = 0;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            writeLog("all_zero", size, vaddr, 0, 0);
            DPRINTF(LSQUnit, "CHAOSLSQFwd: all_zero (vaddr=%#x size=%u)\n",
                    vaddr, size);
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

    bool
    CHAOSLSQFwd::maybeSubstituteSource(uint8_t *load_data,
                                       const uint8_t *true_src,
                                       unsigned copy_size,
                                       const uint8_t *alt_src,
                                       unsigned alt_size, Addr vaddr)
    {
        // §2.4 fwd_source_sub (F5): wrong-source store->load forwarding.
        // Only active in FwdSourceSub mode; other modes return false and the
        // caller does its normal memcpy (zero regression).
        if (struct_mode != StructMode::FwdSourceSub) return false;
        if (probability <= 0.0f) return false;
        if (!load_data || !true_src || !alt_src) return false;
        if (copy_size == 0 || alt_size == 0) return false;

        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return false;
        if (last_clock != Cycles(0) && cur > last_clock) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;

        // sampling-bias fix: consume skip only on eligible wrong-source
        // opportunities (an older SQ entry exists with data)
        if (events_to_skip > 0) { --events_to_skip; return false; }

        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return false;

        // Copy the WRONG store's data into the load buffer. If the wrong
        // source is smaller than the load, copy what it has (the tail keeps
        // whatever the caller's buffer held — the mismatch IS the fault).
        unsigned n = copy_size < alt_size ? copy_size : alt_size;
        memcpy(load_data, alt_src, n);
        stats->numFaultsInjected++;
        ++faults_injected_count;
        if (write_log) {
            *(log_stream->stream())
                << "Cycle: " << cpu->curCycle()
                << ", Site: store->load_forward_decision"
                << ", FaultType: fwd_source_sub"
                << ", Vaddr: 0x" << std::hex << vaddr << std::dec
                << ", TrueSrcSize: " << copy_size
                << ", AltSrcSize: " << alt_size
                << ", Copied: " << n
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        DPRINTF(LSQUnit, "CHAOSLSQFwd: fwd_source_sub wrong-source forward "
                "(vaddr=%#x true=%uB alt=%uB)\n", vaddr, copy_size, alt_size);
        return true;
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
                   "Stuck-at-1 faults on forwarded data")
    {}

} // namespace gem5
