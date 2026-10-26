#include "arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh"
#include "arch/arm/CHAOSArmTLB/chaos_tlb_pfn.hh"  // [R6-FIXC] T04 candidate rule
#include "arch/arm/CHAOSArmTLB/chaos_tlb_stuck.hh"  // [R6-F5-NOEFFECT] F5 latch
#include "cpu/o3/chaos_lsu_tier_cap.hh"  // [MDSPEC][R6-FIXCPP] tier-cap marker
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
            // [R6-F5-NOEFFECT] F5 的每次发射都必须被回报（见
            // chaos_lsu_trigger.hh 的 require_outcome_accounting）：onEligible()
            // 对 F5 只计 fires，真注入由 lookup 侧的 noteOutcome() 记账，漏报
            // 会在 summary 里亮成 F5_UNREPORTED_OUTCOME。
            if (lsuTrigger->tier == ChaOSLsuTier::F5)
                lsuTrigger->require_outcome_accounting = true;
        }
        // [R6-F5-NOEFFECT] Keep the raw --tlb_lsu_tier spelling for the
        // exit-time CHAOS_LSU_NOEFFECT summary (see .hh).
        lsu_tier_string = p.lsuTier;
        // [MDSPEC][R6-FIXCPP] Runtime lookup-tier capability marker: printed
        // ONCE at startup so the campaign's lookup_tier_capability_gate can
        // PROVE this run really mounted the requested tier on the lookup path
        // (rather than needing to trust the flag name). `mounted` is the
        // trigger's real tier (-1 = no trigger object: the legacy F0 path);
        // the marker never claims enabled=1 unless a real non-F0 gate is
        // mounted. F0/`off` still prints (requested=F0 effective=F0
        // lookup_tier_enabled=0) so the legacy path is equally auditable.
        {
            const int mounted = lsuTrigger
                ? static_cast<int>(lsuTrigger->tier) : -1;
            const auto cap = chaos_lsu_tier_cap::resolve(p.lsuTier, mounted);
            printf("%s\n", chaos_lsu_tier_cap::marker(cap).c_str());
            // Crash durability (the trace stream's Z_SYNC_FLUSH discipline,
            // applied to the capability proof): an aborted run must still
            // carry the marker, otherwise the campaign would refuse the
            // sample as `capability-missing` for the WRONG reason.
            fflush(stdout);
        }
        // walk_pairing is the only mode that needs the event-normalized
        // trigger; refuse loudly instead of silently injecting nothing
        // (L04/S10 discipline — a mode that needs a tier must not run
        // without one).
        if (isWalkFamily(fault_type_enum) && !lsuTrigger) {
            panic("CHAOSArmTLB: the walk/refill family (walk_pairing / "
                  "walk_fill_dup / walk_done_early / walk_stale_result) "
                  "requires --tlb_lsu_tier (the event-normalized trigger that "
                  "selects which walk is affected). See R4-5.9 / R4-10 reports.");
        }
        if (isWalkFamily(fault_type_enum) && !walker) {
            panic("CHAOSArmTLB: the walk/refill family requires walker= "
                  "(the ArmTableWalker to attach to). See R4-5.9 / R4-10 "
                  "reports.");
        }
        if (walker) {
            walker->setChaosTLB(this);
        }
        if (lsuTrigger) {
            registerExitCallback([this]() {
                if (lsuTrigger)
                    lsuTrigger->summary("CHAOSArmTLB");
                printNoEffectSummary();      // [R6-F5-NOEFFECT]
            });
        } else {
            // [R6-F0FUNNEL 2026-10-25] F0 / no tier mounted: no
            // ChaOSLsuTrigger exists, so nothing printed the authoritative L0
            // funnel and the campaign could only record attempted=None for
            // every F0 armtlb cell. Print the SAME line from the passive
            // counters. Observation only — registering a callback changes no
            // injection decision, RNG draw or skip/cap arithmetic.
            registerExitCallback([this]() { printLegacyFunnelSummary(); });
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

    // [MDSPEC][R6-FIXCPP/B] lookup-mode F-tier. See CHAOSArmTLB.hh for the
    // full ruling; the semantics are chaos_lsu_trigger.hh's (event-normalized,
    // no frequency invented here).
    bool
    CHAOSArmTLB::lookupTierMounted() const
    {
        return lsuTrigger && lsuTrigger->tier != ChaOSLsuTier::F0;
    }

    // [R6-F0FUNNEL 2026-10-25] F0-legacy authoritative funnel summary.
    // Same line/format the tier path prints (ChaOSLsuTrigger::summary) and the
    // campaign's own regexes accept — so an F0 sample now carries a real
    // attempted/eligible source instead of None. injected is the REAL
    // faults_injected_count (the same counter the fault budget tests), never a
    // mirrored copy. Nothing here is read by any injection decision.
    void
    CHAOSArmTLB::printLegacyFunnelSummary() const
    {
        printf("CHAOS_LSU_TRIGGER: injector=%s tier=F%d attempted=%lu "
               "eligible=%lu injected=%lu first_eligible_tick=%lu "
               "last_eligible_tick=%lu (activated=W3-L0-layer)\n",
               "CHAOSArmTLB", static_cast<int>(ChaOSLsuTier::F0),
               (unsigned long)legacy_attempted,
               (unsigned long)legacy_eligible,
               (unsigned long)faults_injected_count,
               (unsigned long)legacy_first_eligible_tick,
               (unsigned long)legacy_last_eligible_tick);
        // Crash durability: keep the marker in the same flushed window the
        // tier path uses, so an aborted run still carries it.
        fflush(stdout);
    }

    // [R6-F5-NOEFFECT] lookup 侧 no_effect 聚合摘要（任务书要求的最小字段集：
    // attempted / eligible / fires / effective_injected / no_effect /
    // first_tick / last_tick / requested+effective tier）。只打印聚合，绝不
    // 逐事件 —— 与 CHAOS_LSU_TRIGGER 同一 stdout 窗口、同样 flush，供
    // Task 10/12/17 的四方一致性合同复用。
    void
    CHAOSArmTLB::printNoEffectSummary() const
    {
        if (!lsuTrigger) return;
        // Same resolve() the startup CHAOS_LSU_TIER_CAP marker uses: requested
        // = the raw --tlb_lsu_tier spelling, effective = the mounted tier. The
        // two agree for a healthy run and disagree loudly for a stale/wrong
        // mount (the campaign's capability gate already refuses those).
        const auto cap = chaos_lsu_tier_cap::resolve(lsu_tier_string,
                                                     static_cast<int>(lsuTrigger->tier));
        printf("CHAOS_LSU_NOEFFECT: injector=CHAOSArmTLB tier=F%d "
               "requested=%s effective=%s attempted=%lu eligible=%lu "
               "fires=%lu effective_injected=%lu no_effect=%lu "
               "first_no_effect_tick=%lu last_no_effect_tick=%lu\n",
               static_cast<int>(lsuTrigger->tier),
               cap.requested.c_str(), cap.effective.c_str(),
               (unsigned long)lsuTrigger->attempted,
               (unsigned long)lsuTrigger->eligible,
               (unsigned long)lsuTrigger->fires,
               (unsigned long)lookup_effective,
               (unsigned long)lookup_no_effect,
               (unsigned long)lookup_no_effect_first_tick,
               (unsigned long)lookup_no_effect_last_tick);
        fflush(stdout);
    }

    // [R6-F6APP] The funnel ATTEMPT half of the lookup-tier poll. One TLB-hit
    // lookup books one attempted, unconditionally: the hook really ran. The
    // one-shot reachability/budget notice is emitted here (at the first
    // lookup of a tiered run), so the proof line lands in
    // armtlb_injections.log even when no candidate ever appears.
    void
    CHAOSArmTLB::lookupTierBookAttempt()
    {
        lsuTrigger->onAttempt();
        if (!tier_lookup_notice) {
            tier_lookup_notice = true;
            if (write_log && log_stream) {
                *(log_stream->stream())
                    << "Tick: " << curTick()
                    << ", Site: arm_tlb_lookup_tier"
                    << ", FaultType: " << faultTypeToString(fault_type_enum)
                    << " (lookup path now polls lsuTrigger; tier=F"
                    << static_cast<int>(lsuTrigger->tier)
                    << "; a tiered run does NOT consume --tlb_max_faults="
                    << max_faults << " — the tier is the frequency model)"
                    << std::endl;
            }
        }
    }

    // [R6-F6APP] The tier's inject-now decision for one ELIGIBLE lookup.
    // Callers must have established model applicability first (for
    // pfn_to_mapped_page that means a non-empty legal-candidate scan): this
    // is the only place a tier consumes its fire opportunity — F6 sets
    // `spent`, F1-F4 advance `next_fire` — so it must never be reached by a
    // lookup the model cannot act on. F0 is NOT tiered (the legacy gates run
    // unchanged, so F0 stays byte-equivalent to the pre-R6 tree).
    bool
    CHAOSArmTLB::lookupTierFires(bool is_hit)
    {
        if (lsuTrigger->tier == ChaOSLsuTier::F6) {
            // The F6 event source for the lookup path IS a TLB hit
            // (09 §2.1 map): a miss never consumes the arm.
            return is_hit ? lsuTrigger->onF6Event(false) : false;
        }
        return lsuTrigger->onEligible();
    }

    // [R6-F6APP] Read-only candidate scan (see the header). Deterministic
    // entryTable() order; the legality test is the shared predicate
    // chaos_tlb::isSelectablePfnTarget (chaos_tlb_pfn.hh).
    void
    CHAOSArmTLB::collectPfnCandidates(
        const ArmISA::TlbEntry *entry,
        std::vector<std::pair<const ArmISA::TlbEntry *, int>> &out) const
    {
        out.clear();
        if (!tlb || !entry) return;
        const auto &tbl = tlb->entryTable();
        chaos_tlb::PfnCandidateView hit_view{};
        hit_view.valid = entry->valid;
        hit_view.pfn = entry->pfn;
        hit_view.page_size_bits = entry->N;
        hit_view.is_hit_entry = false;
        int table_idx = 0;
        for (auto it = tbl.begin(); it != tbl.end(); ++it) {
            chaos_tlb::PfnCandidateView cand{};
            cand.valid = it->valid;
            cand.pfn = it->pfn;
            cand.page_size_bits = it->N;
            cand.is_hit_entry = (&(*it) == entry);
            if (chaos_tlb::isSelectablePfnTarget(hit_view, cand))
                out.emplace_back(&(*it), table_idx);
            ++table_idx;
        }
    }

    CHAOSArmTLB::FaultType
    CHAOSArmTLB::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        if (s == "stuck_at_one") return FaultType::StuckAtOne;
        if (s == "pfn_to_mapped_page") return FaultType::PfnToMappedPage;
        // [R4-5.9] T08: FS walk/fill pairing (T08-a lost walk).
        if (s == "walk_pairing") return FaultType::WalkPairing;
        // [R4-10-T08-b/c/d] walk/refill pairing sub-models.
        if (s == "walk_fill_dup") return FaultType::WalkDuplicate;
        if (s == "walk_done_early") return FaultType::WalkEarlyDone;
        if (s == "walk_stale_result") return FaultType::WalkStaleResult;
        // [R4-10-T05] entry identity / lifecycle state.
        if (s == "valid_clear") return FaultType::ValidClear;
        if (s == "valid_set") return FaultType::ValidSet;
        if (s == "global_flip") return FaultType::GlobalFlip;
        if (s == "asid_subst") return FaultType::AsidSubst;
        // [R4-10-T06] access-attribute legal substitution.
        if (s == "perm_subst") return FaultType::PermSubst;
        if (s == "memtype_subst") return FaultType::MemTypeSubst;
        if (s == "pagesize_subst") return FaultType::PageSizeSubst;
        // [R4-10-T07] CAM compare / way select.
        if (s == "false_hit") return FaultType::FalseHit;
        if (s == "double_hit") return FaultType::DoubleHit;
        if (s == "wrong_way") return FaultType::WrongWay;
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
            case FaultType::WalkDuplicate: return "walk_fill_dup";   // T08-b
            case FaultType::WalkEarlyDone: return "walk_done_early"; // T08-c
            case FaultType::WalkStaleResult: return "walk_stale_result"; // T08-d
            case FaultType::ValidClear: return "valid_clear";    // [R4-10-T05]
            case FaultType::ValidSet: return "valid_set";
            case FaultType::GlobalFlip: return "global_flip";
            case FaultType::AsidSubst: return "asid_subst";
            case FaultType::PermSubst: return "perm_subst";      // [R4-10-T06]
            case FaultType::MemTypeSubst: return "memtype_subst";
            case FaultType::PageSizeSubst: return "pagesize_subst";
            case FaultType::FalseHit: return "false_hit";        // [R4-10-T07]
            case FaultType::DoubleHit: return "double_hit";
            case FaultType::WrongWay: return "wrong_way";
            case FaultType::Random: return "random";  // G7: clear -Wswitch
        }
        return "random";
    }

    // [MDSPEC][R4-5.9] T08-a walk/fill 丢失. See the header for the full
    // ruling. The walk-issue point (ArmISA::TableWalker::walk) IS the eligible
    // event stream for this model (spec trigger column: "DTLB miss并启动
    // walk"), so the funnel accounting is onAttempt at entry + the tier
    // decision on the same event (F6 rides onF6Event(false) — the attempt
    // is already booked here, matching the CHAOSCache mshr_merge precedent).
    bool
    CHAOSArmTLB::maybeDropWalkFill(uint64_t walk_id, Addr va, uint64_t req_seq,
                                   uint64_t walk_start_tick, unsigned level)
    {
        // [R4-10] all four walk-family sub-models share this issue-point
        // funnel (the walk-issue stream is the eligible stream for the whole
        // family): T08-a DROPS the walk here; T08-b/c/d arm a refill-side
        // action applied in maybeCorruptWalkRefill.
        if (!isWalkFamily(fault_type_enum)) return false;
        if (!lsuTrigger) return false;
        lsuTrigger->onAttempt();
        // [MDSPEC][R4-6-T08] One-shot reachability probe. The R4-5.9 pilot
        // could not tell "the walk hook was never reached" from "the hook
        // was reached but the fault budget had already been spent by the
        // lookup-hit path"; this line settles it in the SAME artifact the
        // judge reads (armtlb_injections.log), and — unlike the exit-
        // callback summary — it survives a timeout-killed sim. One line per
        // run, T08-only: every other fault type is byte-equivalent.
        if (!walk_pairing_probe_notice) {
            walk_pairing_probe_notice = true;
            if (write_log && log_stream) {
                *(log_stream->stream())
                    << "Tick: " << curTick()
                    << ", Site: arm_tlb_walk_issue_probe"
                    << ", walk_id: " << walk_id
                    << ", VA: 0x" << std::hex << va << std::dec
                    << ", FaultType: walk_pairing (walk-issue hook REACHED: "
                       "TableWalker::walk -> maybeDropWalkFill)"
                    << std::endl;
            }
        }
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

        // [R4-10] T08-b/c/d: the walk is NOT dropped here — arm the refill
        // action and let maybeCorruptWalkRefill apply it at the refill
        // completion point (the pairing node pair is emitted there, with the
        // sub-model's field/outcome). walk_stale_result needs a PREVIOUS
        // completed walk; on the very first walk it is an honest no-op (no
        // budget consumed, one-shot notice).
        if (fault_type_enum != FaultType::WalkPairing) {
            if (fault_type_enum == FaultType::WalkStaleResult &&
                !have_last_walk) {
                if (write_log && log_stream && !stale_no_previous_notice) {
                    stale_no_previous_notice = true;
                    *(log_stream->stream())
                        << "Tick: " << curTick()
                        << ", Site: arm_tlb_walk_stale_no_previous"
                        << ", walk_id: " << walk_id
                        << ", FaultType: walk_stale_result (no previously "
                           "completed walk yet — honest no-op)"
                        << std::endl;
                }
                return false;   // do NOT consume the fault budget
            }
            ++faults_injected_count;
            stats->numFaultsInjected++;
            pending_walk_id = walk_id;
            if (write_log && log_stream) {
                *(log_stream->stream())
                    << "Tick: " << curTick()
                    << ", Site: arm_tlb_walk_refill_armed"
                    << ", walk_id: " << walk_id
                    << ", VA: 0x" << std::hex << va << std::dec
                    << ", FaultType: " << faultTypeToString(fault_type_enum)
                    << std::endl;
            }
            return false;   // the walk proceeds; the refill hook fires
        }

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

        // [MDSPEC][R4-6-T08] walk_pairing is a WALK-ISSUE-ONLY model.
        // -----------------------------------------------------------------
        // R4-5.9 pilot root cause (measured, runs/lsu/r4_t59_pilot): with
        // faultType=walk_pairing + probability=1.0 + maxFaults=1, THIS hook
        // — not the walk hook — consumed the single fault. `chosen` became
        // WalkPairing, the switch below hit `default: break` (no pfn
        // mutation), the budget was spent, and the log line read
        //   Site: arm_tlb_lookup_hit, old_pfn == new_pfn, FaultType: walk_pairing
        // (the exact evidence in §5.9.6). TableWalker::walk's
        // maybeDropWalkFill then always saw faults_injected_count >=
        // max_faults and never dropped a walk, so no tlb_walk/tlb_refill
        // pair was ever emitted.
        //
        // The lookup-hit path is NOT an eligible event for this model (the
        // model's trigger column is "DTLB miss并启动walk" — the walk-issue
        // stream), so skip it here BEFORE any budget/RNG/events_to_skip
        // consumption and say so once, loudly, instead of injecting a
        // no-op that silently eats the walk's fault budget. Every other
        // fault type is byte-equivalent to the pre-R4-6 tree.
        if (fault_type_enum == FaultType::WalkPairing) {
            if (write_log && log_stream && !walk_pairing_lookup_notice) {
                walk_pairing_lookup_notice = true;
                *(log_stream->stream())
                    << "Tick: " << curTick()
                    << ", Site: arm_tlb_lookup_hit_skipped"
                    << ", VA: 0x" << std::hex << va << std::dec
                    << ", FaultType: walk_pairing (T08 walk-issue-only: NOT "
                       "consumed at lookup-hit; see maybeDropWalkFill)"
                    << std::endl;
            }
            return;
        }

        // [MDSPEC][R4-10-T07] The CAM/way-select models (false_hit /
        // double_hit / wrong_way) are owned by maybeCorruptLookup, which is
        // the only hook that sees the MISS case and can REPLACE the returned
        // entry pointer. Skipping here for the same reason walk_pairing is
        // skipped above: the single fault budget must not be spent on an
        // ineligible site. Every other fault type is byte-equivalent.
        if (isCamFault(fault_type_enum)) return;

        // TLB has no direct curCycle(); use curTick() vs the clock domain.
        // The first/last clock window is checked via curTick (tick-based,
        // approximate — a TLB SimObject has access to its own clock).
        // For simplicity we check the fault cap + probability only; the
        // clock window is advisory (the tlb SimObject's schedule isn't
        // easily reachable here without more plumbing).
        // [MDSPEC][R6-FIXCPP/B] F-tier gate. A mounted non-F0 tier IS the
        // frequency model for the lookup path (event-normalized, one
        // eligible event per TLB-hit lookup) and replaces the legacy
        // chain (--tlb_max_faults / --tlb_probability / the seed-varied
        // eligible-event skip) — the latter would silently cap every tier
        // back to a single F0 shot, which is exactly the R6-FTIER defect.
        // F0 / no tier mounted: legacy path, byte-equivalent to pre-R6.
        //
        // [R6-F6APP] Model applicability is part of ELIGIBILITY. The pfn
        // substitution model can only act on a hit that has a legal
        // substitute, so for it the read-only candidate scan runs BEFORE the
        // tier is polled (no RNG, no TLB write, no state change): a hit with
        // an empty candidate set books the funnel ATTEMPT and returns — it
        // never books eligible/injected and never consumes a tier's fire
        // opportunity (F6's one shot, an F1-F4 interval slot). Without this,
        // F6 spent its shot on the first TLB hit of the restored checkpoint
        // (T04-F6-W4 seed1: trigger injected=1, numFaultsInjected=0).
        std::vector<std::pair<const ArmISA::TlbEntry *, int>> pfn_candidates;
        bool pfn_scanned = false;
        if (lookupTierMounted()) {
            lookupTierBookAttempt();      // attempted, for every TLB hit
            if (fault_type_enum == FaultType::PfnToMappedPage) {
                collectPfnCandidates(entry, pfn_candidates);
                pfn_scanned = true;
                if (chaos_tlb::pfnHookAction(pfn_candidates.size())
                        == chaos_tlb::PfnHookAction::AttemptOnly)
                    return;               // honest no-op, nothing else consumed
            }
            if (!lookupTierFires(/*is_hit=*/true)) return;
        } else {
            // [R6-F0FUNNEL 2026-10-25] PASSIVE observation, legacy F0 path.
            // One attempted per F0 lookup-hook call that reaches the legacy
            // chain (walk/CAM models returned above, so nothing is double
            // counted across hooks). Increment only — no draw, no branch.
            // [R6-F6APP] BYTE-EQUIVALENT: the legacy path does NOT consult
            // the applicability gate — its gate order (attempted -> fault
            // cap -> probability draw -> eligible -> skip budget) is the
            // pre-R6 sequence verbatim.
            ++legacy_attempted;

            if (max_faults != 0 && faults_injected_count >= max_faults) return;

            // Probability gate: per-lookup Bernoulli.
            std::uniform_real_distribution<float> probDist(0.0f, 1.0f);
            if (probDist(rng) > probability) return;

            // [R6-F0FUNNEL] Eligible = past the entry + fault-cap + probability
            // gates, BEFORE the skip budget is consumed — the same junction
            // the tier path's onEligible() counts at. Observation only: the
            // counters are written after every gate has already decided, so
            // the skip/cap/RNG arithmetic below is untouched.
            ++legacy_eligible;
            if (legacy_eligible == 1)
                legacy_first_eligible_tick = curTick();
            legacy_last_eligible_tick = curTick();

            // Sampling-bias fix (see .hh): consume the skip budget on ELIGIBLE
            // events (past the entry + probability gates) before the first
            // fault, so distinct seeds inject at distinct lookup sites.
            if (events_to_skip > 0) { --events_to_skip; return; }
        }

        FaultType chosen = fault_type_enum;
        if (fault_type_enum == FaultType::Random) {
            int idx = random_fault_distribution(rng);
            chosen = static_cast<FaultType>(idx);
        }

        // [MDSPEC][R4-10-T05/T06] entry-state / access-attribute faults act
        // on a field of the hit entry that is NOT the pfn (valid/global/asid,
        // or a legal AP/memory-type/page-size substitute from another live
        // entry). They do not use the pfn mask and bypass applyProtection
        // (which models pfn-parity), so they are dispatched here. An honest
        // no-op (no legal candidate) registers and counts nothing.
        if (isEntryStateFault(chosen) || isAttrSubstFault(chosen)) {
            applyEntryFieldFault(entry, chosen, va, req_seq, req_size);
            // [R6-F5-NOEFFECT] F5 的 outcome 记账目前只覆盖 pfn 改写模型。
            // 若某次 F5 运行选了 entry-state/attr 模型，必须响亮说明"本格未
            // 计入 no_effect 记账"，绝不静默当作已覆盖。
            if (lookupTierMounted() && lsuTrigger->tier == ChaOSLsuTier::F5)
                printf("CHAOS_LSU_TRIGGER_ALARM: injector=CHAOSArmTLB "
                       "mode=F5_NONPFN_MODEL fault_type=%s (F5 outcome "
                       "accounting covers pfn-mutating models only; this run's "
                       "fires are not fully accounted)\n",
                       faultTypeToString(chosen));
            return;
        }

        // §2.10 F5 pfn_to_mapped_page (Phase 4.4): substitute the hit
        // entry's pfn with the pfn of ANOTHER mapped entry in the same TLB
        // (legal-domain substitution — the wrong-PA access lands on a LIVE
        // page, so no BadAddressError; silent wrong-data read instead).
        // FS-only by construction (the hook fires under the MMU).
        if (chosen == FaultType::PfnToMappedPage) {
            if (!tlb) return;
            // [R6-F6APP] Tiered runs already scanned read-only, before the
            // tier was polled (and are guaranteed non-empty here); the legacy
            // F0 path scans now, at exactly the pre-R6 point in the sequence,
            // so its RNG stream and injection site are byte-identical.
            //
            // [R6-FIXC] The legality test is the shared predicate
            // chaos_tlb::isSelectablePfnTarget (chaos_tlb_pfn.hh): it requires
            // the candidate to be a LIVE (valid) mapping of the SAME page size
            // and a DIFFERENT, non-zero physical frame. The pre-R6 filter
            // (`!= entry && pfn != entry->pfn`) never checked `valid`, so
            // stale/invalid slots holding pfn == 0 dominated the set and every
            // seed produced new_pfn == 0x0 -> PA 0xfa8 -> guest level-0
            // translation fault -> kernel Oops ("wrong page + crash"), not the
            // spec §2.10 F5 silent wrong-LIVE-page read.
            std::vector<std::pair<const ArmISA::TlbEntry *, int>> candidates;
            if (pfn_scanned) {
                candidates.swap(pfn_candidates);
            } else {
                collectPfnCandidates(entry, candidates);
            }
            if (candidates.empty()) return;  // no legal substitute (honest no-op)
            Addr old_pfn = entry->pfn;
            // [R4-4] gem5's own PA arithmetic, before/after the mutation —
            // captures the 64-bit wrap that leaves high pfn bits inert.
            const Addr old_pa = entry->pAddr(va);
            const int entry_way = entryIndex(entry);
            const std::string entry_before = snapshotEntry(entry, old_pa);
            // [R6-FIXC] Deterministic, reproducible pick (same rngSeed -> same
            // draw sequence -> same index; see selectPfnCandidateIndex).
            const auto &candidate = candidates[
                chaos_tlb::selectPfnCandidateIndex(candidates.size(), rng())];
            entry->pfn = candidate.first->pfn;
            const int candidate_way = candidate.second;
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
            const Addr new_pa = entry->pAddr(va);
            registerTrace(va, old_pfn, entry->pfn, old_pa, new_pa,
                          entry->size + 1, "pfn_to_mapped_page",
                          req_seq, req_size, entry_way, candidate_way, 0,
                          entry_before, snapshotEntry(entry, new_pa));
            return;
        }

        // [R6-F5-NOEFFECT] Only the pfn-MUTATING stuck models use the mask
        // path. WalkPairing (returned at the top), the entry-state/attr
        // family (returned just above) and pfn_to_mapped_page (returned just
        // above) never reach here, so `chosen` is one of the three below when
        // Random's draw is resolved — {BitFlip, StuckAtZero, StuckAtOne}.
        const bool pfn_model = (chosen == FaultType::StuckAtZero
                             || chosen == FaultType::StuckAtOne
                             || chosen == FaultType::BitFlip);
        if (!pfn_model) return;

        // [R6-F5-NOEFFECT] F5 是**永久**卡死：规范 07:60 要求"warm-up 后固定
        // 一个物理 bit…之后每次读出/写入都施加同一掩码直到运行结束"。在这里
        // latch 抽取值即实现了"永久"；修复前每次 lookup 重抽，实测
        // armtlb_injections.log 每行 Mask 都不同，并把命中条目的 pfn 逐位
        // 摧毁到 0（0x81d75→0x81d74→0x81c74→…→0x0）。
        const bool permanent =
            lookupTierMounted() && lsuTrigger->tier == ChaOSLsuTier::F5;

        uint64_t mask;
        if (fault_mask) {
            mask = fault_mask;               // 显式掩码优先（且同样被 latch）
        } else if (permanent) {
            mask = chaos_tlb::latchStuckMask(0, f5_stuck_mask,
                        generateRandomMask(num_bits_to_change));
        } else {
            // F0-F4/F6/legacy：保持既有"每次发射重抽掩码"的行为不变
            // （transient 模型每发一次抽一次是原语义，不在本修复范围内）。
            mask = generateRandomMask(num_bits_to_change);
        }
        if (mask == 0) {
            // 抽不到位 = 这一次没有写任何东西；F5 是一次发射，必须回报。
            if (permanent) lsuTrigger->noteOutcome(false);
            return;
        }

        chaos_tlb::StuckKind sk;
        switch (chosen) {
            case FaultType::StuckAtZero: sk = chaos_tlb::StuckKind::StuckAtZero; break;
            case FaultType::StuckAtOne:  sk = chaos_tlb::StuckKind::StuckAtOne;  break;
            case FaultType::BitFlip:     sk = chaos_tlb::StuckKind::BitFlip;     break;
            // [MDSPEC][R4-6-T08] Structurally unreachable: WalkPairing was
            // returned at the top of maybeCorrupt, and Random's draw support
            // is {BitFlip, StuckAtZero, StuckAtOne}. Kept as an explicit loud
            // no-op so a future edit cannot silently fall back to mutating
            // the lookup entry with a non-mask model.
            default: return;
        }

        Addr old_pfn = entry->pfn;
        // [R4-4] gem5 自身的 PA 运算，在改写前后各取一次 —— 捕捉 64 位回绕
        // 导致高位 pfn 失效的情形。
        const Addr old_pa = entry->pAddr(va);
        const int entry_way = entryIndex(entry);
        const std::string entry_before = snapshotEntry(entry, old_pa);

        entry->pfn = chaos_tlb::applyStuckMask(mask, old_pfn, sk).new_pfn;

        // §1.2 注入后保护（N1 TRM Table 9-1 PROXY）。在条目返回 MMU **之前**
        // 运行 —— 1-bit parity_interleaved 检测会把 clean pfn 还原（Corrected）。
        // 因此"是否 effective"必须在它**之后**判定。
        applyProtection(entry, mask, old_pfn, chosen);

        const bool effective = (entry->pfn != old_pfn);
        if (permanent) lsuTrigger->noteOutcome(effective);

        // [R6-F5-NOEFFECT] no_effect：卡死值本来就等于正确值（07:60
        // "若某次事件的正确值本来就等于卡死值，该次不增加 activated"）。
        // 不建 fault identity、不建 ptag、不注册传播链、不写注入日志、
        // 不计 stats、不发 CHAOS_DETECT / prop_evt —— 只进聚合。
        //
        // 只对 permanent(F5) 生效：F0-F4/F6 的每一次发射都照旧计数/写日志/
        // 建 ptag（既有行为逐字保留），否则一次"掩码未改变 pfn"的 transient
        // 发射会让 trigger.injected 与 stats/log 三方对不上，把 F1-F4 的
        // armtlb_count_sources 一致性检查打红。
        if (permanent && !effective) {
            ++lookup_no_effect;
            if (lookup_no_effect_first_tick == 0)
                lookup_no_effect_first_tick = curTick();
            lookup_no_effect_last_tick = curTick();
            return;
        }

        switch (chosen) {
            case FaultType::StuckAtZero: stats->numStuckAtZero++; break;
            case FaultType::StuckAtOne:  stats->numStuckAtOne++;  break;
            case FaultType::BitFlip:     stats->numBitFlips++;    break;
            default: break;
        }
        if (effective) ++lookup_effective;
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
                << ", effective: 1" << std::endl;
        }
        const Addr new_pa = entry->pAddr(va);
        registerTrace(va, old_pfn, entry->pfn, old_pa, new_pa,
                      entry->size + 1, faultTypeToString(chosen),
                      req_seq, req_size, entry_way,
                      /*candidate_way=*/-1, /*walk_id=*/0,
                      entry_before, snapshotEntry(entry, new_pa));
    }

    // [MDSPEC][R4-10-T08-b/c/d] walk/refill pairing sub-models. Called at the
    // refill completion point (WalkUnit::insertTableEntry) once per COMPLETED
    // walk, BEFORE mmu->insert. Applies the sub-model armed at the issue point
    // (pending_walk_id) and emits the tlb_walk/tlb_refill node pair with the
    // sub-model's field + outcome. Also maintains the last-completed-walk
    // record consumed by walk_stale_result (captured BEFORE any mutation, so
    // a stale substitution always uses the NATURAL previous result).
    bool
    CHAOSArmTLB::maybeCorruptWalkRefill(uint64_t walk_id, Addr va,
                                        uint64_t req_seq,
                                        uint64_t walk_start_tick,
                                        unsigned level, ArmISA::TlbEntry *te)
    {
        bool duplicate = false;
        // Natural result of THIS walk (pre-mutation) — the record a later
        // stale fault draws from.
        const Addr this_pfn = te ? te->pfn : 0;
        const Addr this_vpn = te ? te->vpn : 0;

        if (isWalkFamily(fault_type_enum) && pending_walk_id != 0 &&
            pending_walk_id == walk_id &&
            fault_type_enum != FaultType::WalkPairing) {
            pending_walk_id = 0;   // one-shot arm
            const char *mode = faultTypeToString(fault_type_enum);
            // T08-c reports the completion (done) at the walk's ISSUE tick
            // (the "done too early" handshake fault); the data payload stays
            // correct (spec T08: timing-only, data must remain valid).
            const uint64_t refill_tick =
                (fault_type_enum == FaultType::WalkEarlyDone)
                    ? walk_start_tick
                    : (uint64_t)curTick();

            if (fault_type_enum == FaultType::WalkStaleResult) {
                if (te && have_last_walk) {
                    const Addr old_pfn = te->pfn;
                    // Write the PREVIOUS walk's translation into the current
                    // entry (the "old walk result written into the current
                    // slot" fault). The tag/size stay this walk's — only the
                    // translation payload is stale.
                    te->pfn = last_walk_pfn;
                    if (write_log && log_stream) {
                        *(log_stream->stream())
                            << "Tick: " << curTick()
                            << ", Site: arm_tlb_walk_refill_stale"
                            << ", walk_id: " << walk_id
                            << ", VA: 0x" << std::hex << va
                            << ", old_pfn: 0x" << old_pfn
                            << ", stale_pfn: 0x" << te->pfn
                            << ", FaultType: walk_stale_result" << std::dec
                            << std::endl;
                    }
                    CHAOSPropagation *tr = CHAOSPropagation::instance();
                    if (tr) {
                        tr->registerTlbWalkPair(walk_id, va, req_seq,
                                                walk_start_tick, refill_tick,
                                                level, /*fill_lost=*/false,
                                                mode);
                    }
                    stats->numFaultsInjected++;
                }
                // else: honest no-op (should not happen — the issue point
                // already refused when there was no previous walk).
            } else {
                // T08-b (duplicated refill) / T08-c (done too early).
                duplicate = (fault_type_enum == FaultType::WalkDuplicate);
                CHAOSPropagation *tr = CHAOSPropagation::instance();
                if (tr) {
                    tr->registerTlbWalkPair(walk_id, va, req_seq,
                                            walk_start_tick, refill_tick,
                                            level, /*fill_lost=*/false, mode);
                }
                if (write_log && log_stream) {
                    *(log_stream->stream())
                        << "Tick: " << curTick()
                        << ", Site: arm_tlb_walk_refill"
                        << ", walk_id: " << walk_id
                        << ", VA: 0x" << std::hex << va << std::dec
                        << ", FaultType: " << mode
                        << std::endl;
                }
                stats->numFaultsInjected++;
            }
        }

        // Maintain the last-completed-walk record (natural values).
        if (te) {
            last_walk_pfn = this_pfn;
            last_walk_vpn = this_vpn;
            have_last_walk = true;
        }
        return duplicate;
    }

    // [MDSPEC][R4-10-T05/T06] entry-state / attribute substitution. Mutates
    // ONE field of the hit entry (spec: 一次只改一种状态 / 一个字段) and
    // registers the L2 tlb_state node. Legal-domain discipline (spec T06:
    // "从当前运行中选择另一个满足…约束的合法值"): substitutes are taken from
    // ANOTHER live (valid) entry of the same TLB, never a random bit string.
    // Returns true when applied; false = honest no-op (no candidate), in
    // which case nothing is registered and no budget is consumed beyond the
    // trigger draw the caller already made.
    bool
    CHAOSArmTLB::applyEntryFieldFault(ArmISA::TlbEntry *entry, FaultType ft,
                                      Addr va, uint64_t req_seq,
                                      uint64_t req_size)
    {
        if (!entry) return false;
        const char *field = faultTypeToString(ft);
        std::string before, after;
        const Addr old_pa = entry->pAddr(va);
        const int entry_way = entryIndex(entry);
        const std::string state_before = snapshotEntry(entry, old_pa);
        int candidate_way = -1;

        switch (ft) {
          case FaultType::ValidClear:
            before = entry->valid ? "1" : "0";
            entry->valid = false;
            after = "0";
            break;
          case FaultType::ValidSet:
            before = entry->valid ? "1" : "0";
            entry->valid = true;
            after = "1";
            break;
          case FaultType::GlobalFlip:
            before = entry->global ? "1" : "0";
            entry->global = !entry->global;
            after = entry->global ? "1" : "0";
            break;
          case FaultType::AsidSubst: {
            if (!tlb) return false;
            bool found = false; uint16_t cand = 0;
            const auto &tbl = tlb->entryTable();
            int idx = 0;
            for (auto it = tbl.begin(); it != tbl.end(); ++it, ++idx) {
                if (&(*it) == entry) continue;
                if (it->valid && it->asid != entry->asid) {
                    cand = it->asid; candidate_way = idx;
                    found = true; break;
                }
            }
            if (!found) return false;   // no other active ASID: honest no-op
            before = std::to_string(entry->asid);
            entry->asid = cand;
            after = std::to_string(cand);
            break;
          }
          case FaultType::PermSubst: {
            if (!tlb) return false;
            bool found = false; uint8_t cand = 0;
            const auto &tbl = tlb->entryTable();
            int idx = 0;
            for (auto it = tbl.begin(); it != tbl.end(); ++it, ++idx) {
                if (&(*it) == entry) continue;
                if (it->valid && it->ap != entry->ap) {
                    cand = it->ap; candidate_way = idx;
                    found = true; break;
                }
            }
            if (!found) return false;
            before = std::to_string(static_cast<unsigned>(entry->ap));
            entry->ap = cand;
            after = std::to_string(static_cast<unsigned>(cand));
            break;
          }
          case FaultType::MemTypeSubst: {
            if (!tlb) return false;
            bool found = false; uint8_t cand = 0;
            const auto &tbl = tlb->entryTable();
            int idx = 0;
            for (auto it = tbl.begin(); it != tbl.end(); ++it, ++idx) {
                if (&(*it) == entry) continue;
                if (it->valid &&
                    static_cast<uint8_t>(it->mtype) !=
                        static_cast<uint8_t>(entry->mtype)) {
                    cand = static_cast<uint8_t>(it->mtype);
                    candidate_way = idx; found = true; break;
                }
            }
            if (!found) return false;
            before = std::to_string(static_cast<unsigned>(entry->mtype));
            entry->mtype =
                static_cast<ArmISA::TlbEntry::MemoryType>(cand);
            after = std::to_string(static_cast<unsigned>(entry->mtype));
            break;
          }
          case FaultType::PageSizeSubst: {
            if (!tlb) return false;
            bool found = false; uint8_t n = 0; ArmISA::GrainSize tg =
                ArmISA::Grain4KB;
            const auto &tbl = tlb->entryTable();
            int idx = 0;
            for (auto it = tbl.begin(); it != tbl.end(); ++it, ++idx) {
                if (&(*it) == entry) continue;
                if (it->valid && it->N != entry->N) {
                    n = it->N; tg = it->tg; candidate_way = idx;
                    found = true; break;
                }
            }
            if (!found) return false;
            before = std::to_string(entry->N);
            entry->N = n;
            // PPN unchanged (spec T06-c): only the page-size encoding moves.
            entry->size = (n >= 64) ? ~(Addr)0 : ((Addr(1) << n) - 1);
            entry->tg = tg;
            after = std::to_string(n);
            break;
          }
          default:
            return false;
        }

        stats->numStateFaults++;
        ++faults_injected_count;
        if (write_log && log_stream) {
            *(log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: arm_tlb_lookup_hit"
                << ", VA: 0x" << std::hex << va << std::dec
                << ", old_" << field << ": " << before
                << ", new_" << field << ": " << after
                << ", FaultType: " << field
                << std::endl;
        }
        CHAOSPropagation *tr = CHAOSPropagation::instance();
        if (tr) {
            const Addr new_pa = entry->pAddr(va);
            const std::string state_after = snapshotEntry(entry, new_pa);
            tr->registerTlbStateFault(req_seq, va, req_size, field,
                                      before, after, old_pa, new_pa,
                                      entry_way, candidate_way, 0,
                                      state_before, state_after);
        }
        return true;
    }

    // [MDSPEC][R4-10-T07] CAM-compare / way-select models. Called from
    // TLB::lookup for BOTH outcomes (miss/hit). false_hit fabricates a hit on
    // a miss; wrong_way returns another valid way's entry; double_hit observes
    // a fabricated double match. None of them writes entry contents (spec
    // T07: "不直接改表项内容"), so no TLB insert happens inside the lookup
    // iteration (which would invalidate the returned pointer). Honest no-op
    // when the model's premise is unreachable (no other valid entry / no
    // second match).
    ArmISA::TlbEntry *
    CHAOSArmTLB::maybeCorruptLookup(ArmISA::TlbEntry *entry, Addr va,
                                    uint64_t req_seq, uint64_t req_size)
    {
        if (!isCamFault(fault_type_enum)) return entry;
        if (probability <= 0.0f) return entry;
        // [MDSPEC][R6-FIXCPP/B] same F-tier gate as maybeCorrupt. The CAM
        // family's eligible stream is the lookup itself (false_hit's premise
        // IS a miss / T07's trigger is the CAM compare), so for non-F6 tiers
        // both outcomes count; the F6 arm consumes only a real TLB hit
        // (is_hit = entry != nullptr), matching the 09 §2.1 TlbHit source.
        if (lookupTierMounted()) {
            // [R6-F6APP] The CAM family's eligible stream is the lookup
            // itself, and false_hit's premise IS a miss: the model has no
            // separate applicability scan, so attempt and fire are the two
            // adjacent halves here (unchanged semantics for this family).
            lookupTierBookAttempt();
            if (!lookupTierFires(/*is_hit=*/entry != nullptr)) return entry;
        } else {
            if (max_faults != 0 && faults_injected_count >= max_faults)
                return entry;
            std::uniform_real_distribution<float> probDist(0.0f, 1.0f);
            if (probDist(rng) > probability) return entry;
            if (events_to_skip > 0) { --events_to_skip; return entry; }
        }
        if (!tlb) return entry;

        const auto &tbl = tlb->entryTable();
        const char *field = faultTypeToString(fault_type_enum);
        std::string before, after;
        ArmISA::TlbEntry *ret = entry;
        const Addr old_pa = entry ? entry->pAddr(va) : 0;
        const int entry_way = entryIndex(entry);
        const std::string state_before = snapshotEntry(entry, old_pa);

        switch (fault_type_enum) {
          case FaultType::FalseHit: {
            if (entry) return entry;   // only the MISS arm fabricates a hit
            ArmISA::TlbEntry *cand = nullptr;
            for (auto it = tbl.begin(); it != tbl.end(); ++it) {
                if (it->valid) {
                    cand = const_cast<ArmISA::TlbEntry *>(&(*it)); break;
                }
            }
            if (!cand) return entry;   // nothing to fabricate from: no-op
            before = "miss"; after = "hit";
            ret = cand;
            break;
          }
          case FaultType::DoubleHit: {
            if (!entry) return entry;   // needs a first hit to double
            unsigned matches = 1;
            for (auto it = tbl.begin(); it != tbl.end(); ++it) {
                if (&(*it) == entry) continue;
                if (it->valid && it->vpn == entry->vpn) ++matches;
            }
            // No second match exists → the premise is unreachable on this
            // platform; honest no-op rather than a fabricated popcount.
            if (matches < 2) return entry;
            before = "1"; after = std::to_string(matches);
            break;
          }
          case FaultType::WrongWay: {
            if (!entry) return entry;
            ArmISA::TlbEntry *cand = nullptr;
            for (auto it = tbl.begin(); it != tbl.end(); ++it) {
                if (&(*it) == entry) continue;
                if (it->valid) {
                    cand = const_cast<ArmISA::TlbEntry *>(&(*it)); break;
                }
            }
            if (!cand) return entry;   // no other way: honest no-op
            before = "issued_way"; after = "wrong_way";
            ret = cand;
            break;
          }
          default:
            return entry;
        }

        stats->numStateFaults++;
        ++faults_injected_count;
        if (write_log && log_stream) {
            *(log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: arm_tlb_lookup"
                << ", VA: 0x" << std::hex << va << std::dec
                << ", CAM: " << before << " -> " << after
                << ", FaultType: " << field
                << std::endl;
        }
        CHAOSPropagation *tr = CHAOSPropagation::instance();
        if (tr) {
            const Addr new_pa = ret ? ret->pAddr(va) : 0;
            const int candidate_way = entryIndex(ret);
            const std::string state_after = snapshotEntry(ret, new_pa);
            tr->registerTlbStateFault(req_seq, va, req_size, field,
                                      before, after, old_pa, new_pa,
                                      entry_way, candidate_way, 0,
                                      state_before, state_after);
        }
        return ret;
    }

    int
    CHAOSArmTLB::entryIndex(const ArmISA::TlbEntry *entry) const
    {
        if (!tlb || !entry)
            return -1;
        int entry_way = 0;
        const auto &tbl = tlb->entryTable();
        for (auto it = tbl.begin(); it != tbl.end(); ++it, ++entry_way) {
            if (&(*it) == entry)
                return entry_way;
        }
        return -1;
    }

    std::string
    CHAOSArmTLB::snapshotEntry(const ArmISA::TlbEntry *entry, Addr pa) const
    {
        if (!entry)
            return "entry=none";
        std::ostringstream out;
        out << "vpn=" << std::hex << entry->vpn
            << ";asid=" << std::dec << entry->asid
            << ";valid=" << (entry->valid ? 1 : 0)
            << ";global=" << (entry->global ? 1 : 0)
            << ";pfn=" << std::hex << entry->pfn
            << ";ap=" << std::dec << static_cast<unsigned>(entry->ap)
            << ";mtype=" << static_cast<unsigned>(entry->mtype)
            << ";page_size=" << std::hex << (entry->size + 1)
            << ";pa=" << pa;
        return out.str();
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
                               uint64_t req_size, int entry_way,
                               int candidate_way, uint64_t walk_id,
                               const std::string &entry_before,
                               const std::string &entry_after)
    {
        CHAOSPropagation *tr = CHAOSPropagation::instance();
        if (!tr)
            return;
        tr->registerTlbFault(req_seq, va, req_size, old_pfn, new_pfn,
                             old_pa, new_pa, pa_span, mode, entry_way,
                             candidate_way, walk_id, entry_before,
                             entry_after);
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
                   "TLB pfn stuck-at-one faults"),
          ADD_STAT(numStateFaults, statistics::units::Count::get(),
                   "TLB entry-state/attribute/CAM faults (T05/T06/T07)")
    {}

} // namespace gem5
