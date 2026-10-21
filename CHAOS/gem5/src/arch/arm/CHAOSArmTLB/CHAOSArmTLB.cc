#include "arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh"
#include "params/CHAOSArmTLB.hh"
#include "arch/arm/tlb.hh"
#include "arch/arm/pagetable.hh"
#include "arch/arm/table_walker.hh"   // [R4-5.9] T08 walker self-attach
#include "base/output.hh"
#include <sstream>
#include "sim/sim_exit.hh"            // [R4-5.9] registerExitCallback
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // [MDSPEC][H2-FS]

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
        // [MDSPEC][R4-5.9] T08 walk/fill pairing wiring. walker is set from
        // the optional Param (FS configs pass walker=<ArmTableWalker>);
        // nullptr keeps every existing T01-T04/T10/TLB cell byte-equivalent.
        walker = p.walker;
        if (p.lsuTier != "off") {
            auto tier = ChaOSLsuTier::F0;
            if (p.lsuTier == "F1") tier = ChaOSLsuTier::F1;
            else if (p.lsuTier == "F2") tier = ChaOSLsuTier::F2;
            else if (p.lsuTier == "F3") tier = ChaOSLsuTier::F3;
            else if (p.lsuTier == "F4") tier = ChaOSLsuTier::F4;
            else if (p.lsuTier == "F5") tier = ChaOSLsuTier::F5;
            else if (p.lsuTier == "F6") tier = ChaOSLsuTier::F6;
            lsuTrigger = std::make_unique<ChaOSLsuTrigger>(
                tier, rng_seed ? rng_seed : 1,
                p.lsuWarmupEvents, p.lsuSpanEvents);
        }
        // walk_pairing is the only mode that needs the event-normalized
        // trigger; refuse loudly instead of silently injecting nothing
        // (L04/S10 discipline — a mode that needs a tier must not run
        // without one).
        if (fault_type_enum == FaultType::WalkPairing && !lsuTrigger) {
            panic("CHAOSArmTLB: faultType=walk_pairing requires "
                  "--tlb_lsu_tier (the event-normalized trigger that "
                  "selects which walk is dropped). See R4-5.9 report.");
        }
        if (fault_type_enum == FaultType::WalkPairing && !walker) {
            panic("CHAOSArmTLB: faultType=walk_pairing requires walker= "
                  "(the ArmTableWalker to attach to). See R4-5.9 report.");
        }
        if (walker) {
            walker->setChaosTLB(this);
        }
        if (lsuTrigger) {
            registerExitCallback([this]() {
                if (lsuTrigger)
                    lsuTrigger->summary("CHAOSArmTLB");
            });
        }
        if (probability > 0.0f) {
            log_stream = simout.create("armtlb_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSArmTLB: Could not open log file");
            }
            stats = std::make_unique<CHAOSArmTLBStats>(this);
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            // Sampling-bias fix (9th member of the geometric-skip family,
            // see CHAOSArmTLB.hh): skip a seed-dependent number of eligible
            // events so maxFaults=1 lands on a VARIED lookup, not the
            // deterministic first post-window hit.
            std::geometric_distribution<uint64_t> skip_dist(0.1);
            events_to_skip = skip_dist(rng);
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
        // [R4-5.9] T08: FS walk/fill pairing (T08-a lost walk).
        if (s == "walk_pairing") return FaultType::WalkPairing;
        return FaultType::Random;
    }

    const char*
    CHAOSArmTLB::faultTypeToString(CHAOSArmTLB::FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
            case FaultType::PfnToMappedPage: return "pfn_to_mapped_page";
            case FaultType::WalkPairing: return "walk_pairing";  // [R4-5.9]
            case FaultType::Random: return "random";  // G7: clear -Wswitch
        }
        return "random";
    }

    // [MDSPEC][R4-5.9] T08-a walk/fill 丢失. See the header for the full
    // ruling. The walk-issue point (TableWalker::walk) IS the eligible
    // event stream for this model (spec trigger column: "DTLB miss并启动
    // walk"), so the funnel accounting is onAttempt at entry + the tier
    // decision on the same event (F6 rides onF6Event(false) — the attempt
    // is already booked here, matching the CHAOSCache mshr_merge precedent).
    bool
    CHAOSArmTLB::maybeDropWalkFill(uint64_t walk_id, Addr va, uint64_t req_seq,
                                   uint64_t walk_start_tick, unsigned level)
    {
        if (fault_type_enum != FaultType::WalkPairing) return false;
        if (!lsuTrigger) return false;
        lsuTrigger->onAttempt();
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;
        // Per-walk Bernoulli gate (parity with maybeCorrupt's probability
        // semantics). Only consulted when probability > 0 (default 0 =
        // inert, so the campaign's T-cells keep their existing behaviour
        // unless T08 explicitly arms this mode).
        if (probability > 0.0f) {
            std::uniform_real_distribution<float> probDist(0.0f, 1.0f);
            if (probDist(rng) > probability) return false;
        }
        const bool fire = (lsuTrigger->tier == ChaOSLsuTier::F6)
                              ? lsuTrigger->onF6Event(false)
                              : lsuTrigger->onEligible();
        if (!fire) return false;

        ++faults_injected_count;
        stats->numFaultsInjected++;
        // Emit the walk/fill node PAIR (pairing key = walk_id). T08-a is
        // the lost-refill arm: fill_lost=true ⇒ the tlb_refill node is
        // recorded explicitly as field=lost / outcome=lost rather than
        // fabricating a completed refill (honest absence).
        CHAOSPropagation *tr = CHAOSPropagation::instance();
        if (tr) {
            tr->registerTlbWalkPair(walk_id, va, req_seq, walk_start_tick,
                                    curTick(), level, /*fill_lost=*/true,
                                    "walk_pairing");
        }
        if (write_log && log_stream) {
            *(log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: arm_tlb_walk_issue_drop"
                << ", walk_id: " << walk_id
                << ", VA: 0x" << std::hex << va
                << ", FaultType: walk_pairing (T08-a lost walk/fill)"
                << std::dec << std::endl;
        }
        return true;
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
    CHAOSArmTLB::maybeCorrupt(ArmISA::TlbEntry *entry, Addr va,
                              uint64_t req_seq, uint64_t req_size)
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

        // Sampling-bias fix (see .hh): consume the skip budget on ELIGIBLE
        // events (past the entry + probability gates) before the first
        // fault, so distinct seeds inject at distinct lookup sites.
        if (events_to_skip > 0) { --events_to_skip; return; }

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
            // [R4-4] gem5's own PA arithmetic, before/after the mutation —
            // captures the 64-bit wrap that leaves high pfn bits inert.
            const Addr old_pa = entry->pAddr(va);
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
            registerTrace(va, old_pfn, entry->pfn, old_pa, entry->pAddr(va),
                          entry->size + 1, "pfn_to_mapped_page",
                          req_seq, req_size);
            return;
        }

        uint64_t mask = fault_mask ? fault_mask : generateRandomMask(
            num_bits_to_change);
        if (mask == 0) return;

        Addr old_pfn = entry->pfn;
        // [R4-4] gem5's own PA arithmetic, before/after the mutation —
        // captures the 64-bit wrap that leaves high pfn bits inert.
        const Addr old_pa = entry->pAddr(va);
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
        registerTrace(va, old_pfn, entry->pfn, old_pa, entry->pAddr(va),
                      entry->size + 1, faultTypeToString(chosen),
                      req_seq, req_size);
    }

    // [MDSPEC][R4-4] register a TLB-entry fault with the propagation tracer
    // — SEQ-PRIMARY correlation (replaces the pre-R4-4 address-only
    // registration; user ruling 2026-10-20: address-only correlation may
    // survive only as a labeled fallback).
    //
    // Pre-R4-4 defect (measured, runs/lsu/r4_fs/T01-F0-W4/seed1): the chain
    // was registered VA-PAGE-scoped in the faulted-byte registry, so every
    // later request whose VA fell in the same 4 KiB page joined by address
    // overlap — 105 DISTINCT dyn_inst_seqs' events (lsq_push/mem_req/
    // lsq_sendfrag/tlb_translate/resp/consumer) merged into one TLB fault
    // chain, none identifiable as the request whose translation consumed
    // the corrupted entry (that request's own tlb_translate had already
    // fired before the injection — the join was provably NOT the fault
    // consumer). The drawn mask (pfn bit 56) also wraps out of the 64-bit
    // PA, so the PA was UNCHANGED and every "downstream" cache/resp/
    // taint_reg/errant_commit join was fabricated from unrelated correct
    // traffic on the unchanged page.
    //
    // The injection site (TLB::lookup) still has no Request in the gem5
    // core signature, but MMU::getTE — the only lookup caller that owns
    // the RequestPtr — now publishes the in-flight request's seq/size on
    // the TLB (chaosLookupReqSeq/Size, [R4-4]), which this hook consumes:
    //   * PRIMARY  — addr-registry entry [va, va+span) bound to req_seq,
    //                so the request's own later seq-keyed events join by
    //                SEQ (correlateRequestBySeq / correlateRequest's
    //                seq arm); same registration shape as R4-1's
    //                registerLSQForwardFault.
    //   * FALLBACK — the WRONG physical page in the faulted-byte registry
    //                for the seq-less cache-side sites, ONLY when the
    //                corrupted pfn actually redirects the PA (old/new PA
    //                page differ). A pfn bit at/above the PA width wraps
    //                out of the Addr and changes nothing — then nothing is
    //                registered downstream and the chain honestly ends at
    //                the TLB layer (no fabricated cache/resp joins).
    //   * req_seq == 0 (table-walker / functional lookups — no Request
    //     identity published): no primary arm; the PA fallback (when the
    //     PA changed) survives, labeled addr_fallback.
    void
    CHAOSArmTLB::registerTrace(Addr va, Addr old_pfn, Addr new_pfn,
                               Addr old_pa, Addr new_pa, Addr pa_span,
                               const char *mode, uint64_t req_seq,
                               uint64_t req_size)
    {
        CHAOSPropagation *tr = CHAOSPropagation::instance();
        if (!tr)
            return;
        tr->registerTlbFault(req_seq, va, req_size, old_pfn, new_pfn,
                             old_pa, new_pa, pa_span, mode);
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
