#include "arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh"
#include "params/CHAOSArmTLB.hh"
#include "arch/arm/tlb.hh"
#include "arch/arm/pagetable.hh"
#include "base/output.hh"

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
          protection_model(p.protectionModel),
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
            if (tlb) tlb->chaosTLB = this;
        }
    }

    CHAOSArmTLB::~CHAOSArmTLB() {}

    CHAOSArmTLB::FaultType
    CHAOSArmTLB::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        if (s == "stuck_at_one") return FaultType::StuckAtOne;
        if (s == "pfn_to_mapped_page") return FaultType::PfnToMappedPage;
        return FaultType::Random;
    }

    const char*
    CHAOSArmTLB::faultTypeToString(CHAOSArmTLB::FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
            case FaultType::PfnToMappedPage: return "pfn_to_mapped_page";
            case FaultType::Random: return "random";  // G7: clear -Wswitch
        }
        return "random";
    }

    // §1.2 protection-aware (N1 TRM Table 9-1 PROXY). L1 TLB = 'none' (raw
    // escape, default); L2 TLB/walk cache = 'parity_interleaved' (1-bit
    // detect -> contained). "none" (default) = raw, zero regression.
    CHAOSArmTLB::ProtectionOutcome
    CHAOSArmTLB::stringToProtectionModel(const std::string &s) {
        if (s == "parity_interleaved") return ProtectionOutcome::Corrected;
        return ProtectionOutcome::Raw;  // "none" / unknown -> raw
    }

    const char*
    CHAOSArmTLB::protectionOutcomeToString(CHAOSArmTLB::ProtectionOutcome o) {
        switch (o) {
            case ProtectionOutcome::Raw: return "Raw";
            case ProtectionOutcome::Corrected: return "Corrected";
            case ProtectionOutcome::SilentEscape: return "SilentEscape";
        }
        return "Raw";
    }

    // §1.2 post-injection protection. Acts on entry->pfn AFTER the bit
    // mutation, BEFORE the entry is returned to the MMU (so an undo restores
    // the clean pfn before translation uses it -> no wrong-PA access).
    //   none                -> Raw (leave = escape). Default, zero regression.
    //   parity_interleaved  -> 1-bit: undo entry->pfn = old_pfn (Corrected;
    //                          real L2-TLB parity HW invalidates+re-walks, this
    //                          restores the pfn to model the same observable
    //                          outcome re-entrancy-safely from inside the
    //                          lookup hot-path; E3); >=2-bit: SilentEscape.
    CHAOSArmTLB::ProtectionOutcome
    CHAOSArmTLB::applyProtection(ArmISA::TlbEntry *entry, uint64_t mask,
                                 Addr old_pfn, FaultType ft)
    {
        // popcount of the 64-bit mask = bits this fault flips (§1.2 "1-bit/2-bit").
        int bits = __builtin_popcountll(mask);
        ProtectionOutcome outcome = ProtectionOutcome::Raw;
        (void)ft;

        if (protection_model == "none") {
            outcome = ProtectionOutcome::Raw;  // leave = escape (default)
        } else if (protection_model == "parity_interleaved") {
            if (bits == 1 && entry) {
                // 1-bit: restore the clean pfn before the MMU uses the entry
                // (Corrected / DetectedContained-equivalent). Re-entrancy-safe:
                // no _flushMva (private + complex sig + walk re-entry risk).
                entry->pfn = old_pfn;
                outcome = ProtectionOutcome::Corrected;
            } else {
                outcome = ProtectionOutcome::SilentEscape;  // >=2-bit silent
            }
        } else {
            outcome = ProtectionOutcome::Raw;  // unknown model -> raw
        }

        if (write_log) {
            *(log_stream->stream()) << "    protection: model=" << protection_model
                << " bits=" << bits << " -> " << protectionOutcomeToString(outcome)
                << std::endl;
        }
        return outcome;
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
        // TLB has no direct curCycle(); use curTick() vs the clock domain.
        // The first/last clock window is checked via curTick (tick-based,
        // approximate — a TLB SimObject has access to its own clock).
        // For simplicity we check the fault cap + probability only; the
        // clock window is advisory (the tlb SimObject's schedule isn't
        // easily reachable here without more plumbing).
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        // Probability gate: per-lookup Bernoulli.
        std::uniform_real_distribution<float> probDist(0.0f, 1.0f);
        if (probDist(rng) > probability) return;

        FaultType chosen = fault_type_enum;
        if (fault_type_enum == FaultType::Random) {
            int idx = random_fault_distribution(rng);
            chosen = static_cast<FaultType>(idx);
        }

        // §2.10 F5 pfn_to_mapped_page (Phase 4.4): substitute the hit
        // entry's pfn with the pfn of ANOTHER mapped entry in the same TLB
        // (legal-domain substitution — the wrong-PA access lands on a LIVE
        // page, so no BadAddressError; silent wrong-data read instead).
        // FS-only by construction (the hook fires under the MMU).
        if (chosen == FaultType::PfnToMappedPage) {
            if (!tlb) return;
            // collect candidate pfns from the other entries
            std::vector<Addr> candidates;
            const auto &tbl = tlb->entryTable();
            for (auto it = tbl.begin(); it != tbl.end(); ++it) {
                if (&(*it) != entry && it->pfn != entry->pfn)
                    candidates.push_back(it->pfn);
            }
            if (candidates.empty()) return;  // no legal substitute (honest no-op)
            Addr old_pfn = entry->pfn;
            entry->pfn = candidates[rng() % candidates.size()];
            stats->numFaultsInjected++;
            ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream())
                    << "Tick: " << curTick()
                    << ", Site: arm_tlb_lookup_hit"
                    << ", VA: 0x" << std::hex << va
                    << ", old_pfn: 0x" << old_pfn
                    << ", new_pfn: 0x" << entry->pfn
                    << ", FaultType: pfn_to_mapped_page"
                    << ", candidates: " << std::dec << candidates.size()
                    << std::endl;
            }
            return;
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

        // §1.2 post-injection protection (N1 TRM Table 9-1 PROXY). Runs
        // BEFORE the entry is returned to the MMU — a 1-bit parity_interleaved
        // detection RESTORES the clean pfn (Corrected) so translation proceeds
        // without a wrong-PA access. Default protection_model="none" = Raw
        // (no-op, zero regression — the §0.1 FS TLB DUE anchor reproduces).
        applyProtection(entry, mask, old_pfn, chosen);

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
