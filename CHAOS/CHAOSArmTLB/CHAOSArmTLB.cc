#include "arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh"
#include "params/CHAOSArmTLB.hh"
#include "arch/arm/tlb.hh"
#include "arch/arm/pagetable.hh"
#include "base/output.hh"
#include "base/trace.hh"
#include "sim/core.hh"  // curTick() + getClockFrequency() (D1 time window)

namespace gem5
{

    CHAOSArmTLB::CHAOSArmTLB(const CHAOSArmTLBParams &p)
        : SimObject(p),
          tlb(p.tlb),
          probability(p.probability),
          fault_type_enum(stringToFaultType(p.faultType)),
          fault_mask(p.faultMask),
          num_bits_to_change(p.bitsToChange),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          stats(nullptr)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("armtlb_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSArmTLB: Could not open log file");
            }
            stats = std::make_unique<CHAOSArmTLBStats>(this);
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            random_fault_distribution = std::discrete_distribution<int>(
                {0.9, 0.05, 0.05});  // bit_flip / stuck0 / stuck1
            // SELF-ATTACH to the target TLB (same pattern as CHAOSLSQFwd:
            // cpu->lsqFwd = this). The TLB's `chaosTLB` field is public; we
            // set it here so TLB::lookup can reach this injector. `tlb` was
            // passed as a Param and is constructed first. Safe because
            // TLB::lookup only reads chaosTLB during translate(), long after
            // SimObject construction. This avoids needing a python binding
            // for setChaosTLB (which has none, like setLSQFwd).
            // D6: warn (not silent) if tlb is NULL — a misconfigured run
            // would otherwise silently inject nothing.
            if (tlb) {
                tlb->chaosTLB = this;
            } else {
                warn("CHAOSArmTLB: tlb param is NULL — SELF-ATTACH failed; "
                     "TLB hook will be inactive.\n");
            }
        }
    }

    void
    CHAOSArmTLB::startup()
    {
        // D1 fix: snapshot the firstClock/lastClock window as sim ticks at
        // startup (the global tick domain is fixed by then). The TLB is not
        // a ClockedObject, so firstClock/lastClock are interpreted as SIM
        // TICKS (curTick domain) — NOT CPU cycles. This removes the prior
        // "advisory only, never checked" gap (D1) and the 1GHz * 1000
        // assumption used by the sibling CHAOSArmSysReg (D4, fixed
        // separately). last_clock==0 means unrestricted (consistent with
        // lastClock==0 elsewhere).
        first_tick = (Tick)first_clock;
        last_tick = (last_clock == Cycles(0)) ? (Tick)0 : (Tick)last_clock;
    }

    CHAOSArmTLB::~CHAOSArmTLB() {}

    CHAOSArmTLB::FaultType
    CHAOSArmTLB::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        if (s == "stuck_at_one") return FaultType::StuckAtOne;
        return FaultType::Random;
    }

    const char*
    CHAOSArmTLB::faultTypeToString(CHAOSArmTLB::FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
            case FaultType::Random: return "random";  // G7: clear -Wswitch
        }
        return "random";
    }

    uint64_t
    CHAOSArmTLB::generateRandomMask(int bits_to_change) {
        uint64_t mask = 0;
        std::uniform_int_distribution<int> bitDist(0, 63);
        while (bits_to_change-- > 0) mask |= (1ULL << bitDist(rng));
        return mask;
    }

    void
    CHAOSArmTLB::maybeCorrupt(ArmISA::TlbEntry *entry, Addr va)
    {
        if (!entry || probability <= 0.0f) return;
        // D1 fix: enforce the [first_tick, last_tick] window (curTick domain).
        // Before this fix the window was "advisory only" and never checked,
        // so injection fired from sim start. last_tick==0 means unrestricted.
        Tick now = curTick();
        if (now < first_tick) return;
        if (last_tick != 0 && now > last_tick) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        // Probability gate: per-lookup Bernoulli. D5: use >= (consistent with
        // CHAOSLSQFwd; was >, which let probDist==probability slip through).
        std::uniform_real_distribution<float> probDist(0.0f, 1.0f);
        if (probDist(rng) >= probability) return;

        FaultType chosen = fault_type_enum;
        if (fault_type_enum == FaultType::Random) {
            int idx = random_fault_distribution(rng);
            chosen = static_cast<FaultType>(idx);
        }

        uint64_t mask = fault_mask ? fault_mask : generateRandomMask(
            num_bits_to_change);
        if (mask == 0) return;

        Addr old_pfn = entry->pfn;
        switch (chosen) {
            case FaultType::StuckAtZero:
                entry->pfn &= ~mask;
                stats->numStuckAtZero++;
                break;
            case FaultType::StuckAtOne:
                entry->pfn |= mask;
                stats->numStuckAtOne++;
                break;
            case FaultType::BitFlip:
                entry->pfn ^= mask;
                stats->numBitFlips++;
                break;
            default: break;
        }
        stats->numFaultsInjected++;
        ++faults_injected_count;

        if (write_log) {
            *(log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: arm_tlb_lookup_hit"
                << ", VA: 0x" << std::hex << va
                << ", old_pfn: 0x" << old_pfn
                << ", new_pfn: 0x" << entry->pfn
                << ", FaultType: " << faultTypeToString(chosen)
                << ", Mask: 0x" << mask << std::dec
                << std::endl;
        }
    }

    CHAOSArmTLB::CHAOSArmTLBStats::CHAOSArmTLBStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total TLB-entry faults injected"),
          ADD_STAT(numBitFlips, statistics::units::Count::get(),
                   "TLB pfn bit-flip faults"),
          ADD_STAT(numStuckAtZero, statistics::units::Count::get(),
                   "TLB pfn stuck-at-zero faults"),
          ADD_STAT(numStuckAtOne, statistics::units::Count::get(),
                   "TLB pfn stuck-at-one faults")
    {}

} // namespace gem5
