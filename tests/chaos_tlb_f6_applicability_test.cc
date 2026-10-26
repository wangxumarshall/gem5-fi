/*
 * chaos_tlb_f6_applicability_test.cc — [R6-F6APP] standalone unit test for the
 * pfn_to_mapped_page funnel order. NOT part of the gem5 build; compiled:
 *
 *   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
 *       tests/chaos_tlb_f6_applicability_test.cc -o /tmp/tlb_f6app \
 *       && /tmp/tlb_f6app
 *
 * Defect under test (measured 2026-10-25, T04-F6-W4 seed1, binary a9b2c236):
 * CHAOSArmTLB::maybeCorrupt polled the tier BEFORE it scanned for a legal
 * substitute, so F6 consumed its one shot on the very FIRST TLB hit — a hit
 * with no other live same-page-size frame. The trigger reported
 * eligible=1/injected=1 while numFaultsInjected stayed 0 (phantom injection:
 * no injection log line, no prop_evt, count_contradiction=true). F1-F4 had
 * the same shape: onEligible() already incremented eligible and advanced
 * next_fire on a candidate-less lookup.
 *
 * The rule under test: one TLB-hit lookup books the funnel ATTEMPT
 * unconditionally; it is ELIGIBLE only when the read-only candidate scan
 * found >= 1 legal substitute; the tier fires (consuming RNG/state) only for
 * an eligible lookup, and the mutation is applied iff the tier fired.
 */
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include "arch/arm/CHAOSArmTLB/chaos_tlb_pfn.hh"
#include "cpu/o3/chaos_lsu_trigger.hh"

// standalone link shim (same as tests/chaos_armtlb_lookup_ftier_test.cc):
// chaos_lsu_trigger.hh calls curTick(), which dereferences the gem5 TLS
// pointer the event queue maintains. Outside the gem5 build nothing defines
// it — define it here and point it at a static tick in main().
namespace gem5 { namespace Gem5Internal {
__thread Tick *_curTickPtr;
} }
static gem5::Tick standalone_tick = 0;

using gem5::ChaOSLsuTier;
using gem5::ChaOSLsuTrigger;
using gem5::chaos_tlb::PfnCandidateView;
using gem5::chaos_tlb::PfnHookAction;
using gem5::chaos_tlb::isSelectablePfnTarget;
using gem5::chaos_tlb::pfnHookAction;

static int failed = 0;

static void
check(const std::string &name, bool cond, const std::string &detail = "")
{
    if (cond) {
        std::printf("PASS %s\n", name.c_str());
    } else {
        std::printf("FAIL %s%s\n", name.c_str(),
                    detail.empty() ? "" : ("  [" + detail + "]").c_str());
        ++failed;
    }
}

static PfnCandidateView
view(bool valid, uint64_t pfn, uint8_t n = 12, bool is_hit = false)
{
    PfnCandidateView v;
    v.valid = valid;
    v.pfn = pfn;
    v.page_size_bits = n;
    v.is_hit_entry = is_hit;
    return v;
}

// The legal-substitute count for a hit on `hit_idx` in `tbl` — the same
// predicate the injector and the pfn candidate unit test already share.
static std::size_t
countCandidates(const std::vector<PfnCandidateView> &tbl, std::size_t hit_idx)
{
    std::size_t n = 0;
    for (std::size_t i = 0; i < tbl.size(); ++i)
        if (i != hit_idx && isSelectablePfnTarget(tbl[hit_idx], tbl[i])) ++n;
    return n;
}

// One full hook pass over a candidate-count stream, in the order under test.
//   eligibility_gate=false reproduces the PRE-FIX order (the tier is polled
//     for every lookup; the model then honestly no-ops when no candidate
//     exists) — that is the phantom-injection shape.
//   eligibility_gate=true is the FIXED order.
// `fires` = times the tier said "inject now"; `applied` = fires that also had
// a legal candidate (the only ones the model can actually write).
struct Run
{
    uint64_t attempted = 0, eligible = 0, injected = 0;
    std::size_t fires = 0, applied = 0;
    long first_fire = -1, first_applied = -1;
};

static Run
drive(ChaOSLsuTier tier, uint64_t seed, uint64_t warmup, uint64_t span,
      bool eligibility_gate, const std::vector<std::size_t> &cands)
{
    ChaOSLsuTrigger tr(tier, seed, warmup, span);
    Run r;
    for (std::size_t i = 0; i < cands.size(); ++i) {
        tr.onAttempt();                       // (1) every TLB-hit lookup
        if (eligibility_gate &&
            pfnHookAction(cands[i]) == PfnHookAction::AttemptOnly)
            continue;                         // (2) honest no-op, nothing consumed
        const bool fire = (tier == ChaOSLsuTier::F6)
                              ? tr.onF6Event(false)   // (3) the hit IS the event
                              : tr.onEligible();
        if (fire) {
            if (r.first_fire < 0) r.first_fire = (long)i;
            ++r.fires;
            if (cands[i]) {
                if (r.first_applied < 0) r.first_applied = (long)i;
                ++r.applied;
            }
        }
    }
    r.attempted = tr.attempted;
    r.eligible = tr.eligible;
    r.injected = tr.injected;
    return r;
}

// A real mini-TLB: the hit entry, two stale zero-frame slots, and — from
// `epoch` on — a live 4 KiB frame that is a legal substitute. The counts fed
// to drive() come from the SHARED predicate, not from a magic constant.
static std::vector<std::size_t>
candidateStream(std::size_t n, std::size_t epoch)
{
    std::vector<PfnCandidateView> tbl = {
        view(true, 0x81d75, 12, /*is_hit=*/true),  // 0: the hit entry
        view(false, 0),                            // 1: stale slot (pfn 0)
        view(false, 0),                            // 2: stale slot (pfn 0)
    };
    std::vector<std::size_t> counts(n, 0);
    for (std::size_t i = 0; i < n; ++i) {
        if (i == epoch)
            tbl.push_back(view(true, 0x80000, 12));  // a live frame appears
        counts[i] = countCandidates(tbl, 0);
    }
    return counts;
}

int
main()
{
    gem5::Gem5Internal::_curTickPtr = &standalone_tick;

    const std::size_t N = 500000;
    const std::size_t EPOCH = 200000;   // first 200k hits have NO candidate
    const std::vector<std::size_t> cands = candidateStream(N, EPOCH);
    const uint64_t seed = 7;

    std::printf("[0] the synthetic stream really switches candidate supply\n");
    check("no candidate before the epoch", cands.front() == 0);
    check("a legal candidate from the epoch on",
          cands[EPOCH] == 1 && cands[N - 1] == 1);

    std::printf("[1] F6: the one shot is NOT spent on a candidate-less hit\n");
    {
        const Run fixed = drive(ChaOSLsuTier::F6, seed, 0, 0,
                                /*gate=*/true, cands);
        check("F6+gate: every hit books an attempt",
              fixed.attempted == N, std::to_string(fixed.attempted));
        check("F6+gate: eligible == 1 (only the first hit WITH a candidate)",
              fixed.eligible == 1, std::to_string(fixed.eligible));
        check("F6+gate: injected == 1", fixed.injected == 1,
              std::to_string(fixed.injected));
        check("F6+gate: exactly one fire, and it applied",
              fixed.fires == 1 && fixed.applied == 1,
              std::to_string(fixed.fires) + "/" + std::to_string(fixed.applied));
        check("F6+gate: fires at the FIRST candidate-bearing hit (not index 0)",
              fixed.first_fire == (long)EPOCH,
              std::to_string(fixed.first_fire));

        const Run pre = drive(ChaOSLsuTier::F6, seed, 0, 0,
                              /*gate=*/false, cands);
        check("pre-fix order reproduces the phantom: injected=1, applied=0",
              pre.injected == 1 && pre.fires == 1 && pre.applied == 0,
              std::to_string(pre.injected) + "/" + std::to_string(pre.applied));
        check("pre-fix order fires at index 0 (the candidate-less first hit)",
              pre.first_fire == 0, std::to_string(pre.first_fire));
        check("F6+gate has NO phantom (injected == applied)",
              fixed.injected == fixed.applied);
    }

    std::printf("[2] F2: a candidate-less fire is never counted as injected\n");
    {
        const Run fixed = drive(ChaOSLsuTier::F2, seed, 0, 0,
                                /*gate=*/true, cands);
        check("F2+gate: at least one fire", fixed.fires > 0,
              std::to_string(fixed.fires));
        check("F2+gate: every fire had a candidate (no phantom)",
              fixed.applied == fixed.fires,
              std::to_string(fixed.applied) + "/" + std::to_string(fixed.fires));
        check("F2+gate: injected == applied", fixed.injected == fixed.applied,
              std::to_string(fixed.injected) + "/" + std::to_string(fixed.applied));
        check("F2+gate: no fire before the candidate epoch",
              fixed.first_fire >= (long)EPOCH, std::to_string(fixed.first_fire));

        const Run pre = drive(ChaOSLsuTier::F2, seed, 0, 0,
                              /*gate=*/false, cands);
        check("pre-fix F2 fires inside the candidate-less prefix (phantom)",
              pre.first_fire >= 0 && pre.first_fire < (long)EPOCH,
              std::to_string(pre.first_fire));
        check("pre-fix F2: injected > applied (the defect class)",
              pre.injected > pre.applied,
              std::to_string(pre.injected) + " vs " + std::to_string(pre.applied));
    }

    std::printf("[3] F5 (permanent): same gate, every eligible hit applies\n");
    {
        const Run fixed = drive(ChaOSLsuTier::F5, seed, 0, 0,
                                /*gate=*/true, cands);
        check("F5+gate: eligible == the candidate-bearing hits",
              fixed.eligible == N - EPOCH, std::to_string(fixed.eligible));
        check("F5+gate: injected == applied == eligible",
              fixed.injected == fixed.applied && fixed.applied == fixed.eligible,
              std::to_string(fixed.injected) + "/" + std::to_string(fixed.applied));

        const Run pre = drive(ChaOSLsuTier::F5, seed, 0, 0,
                              /*gate=*/false, cands);
        check("pre-fix F5: injected == stream length, applied < injected",
              pre.injected == N && pre.applied == N - EPOCH,
              std::to_string(pre.injected) + "/" + std::to_string(pre.applied));
    }

    std::printf("[4] the gate is a pure read (no state, no RNG)\n");
    {
        // pfnHookAction depends on the count alone and is deterministic.
        check("pfnHookAction(0) == AttemptOnly",
              pfnHookAction(0) == PfnHookAction::AttemptOnly);
        check("pfnHookAction(1) == PollTier",
              pfnHookAction(1) == PfnHookAction::PollTier);
        check("pfnHookAction(31) == PollTier",
              pfnHookAction(31) == PfnHookAction::PollTier);
        // Repeated runs with the same seed are identical (no hidden state).
        const Run a = drive(ChaOSLsuTier::F2, seed, 0, 0, true, cands);
        const Run b = drive(ChaOSLsuTier::F2, seed, 0, 0, true, cands);
        check("reproducible for a fixed seed",
              a.fires == b.fires && a.first_fire == b.first_fire &&
              a.injected == b.injected);
    }

    std::printf("\n");
    if (failed) {
        std::printf("FAILED (%d)\n", failed);
        return 1;
    }
    std::printf("ALL PASS\n");
    return 0;
}
