// test_sq03_effect.cc — host test for the SQ03 (LSU v3.2.12 task 12)
// state-fault downstream-effect grading in
// CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/sq03_rules.hh.
//
// Build/run (same invocation as the other rule host tests):
//   g++ -O2 -std=c++17 -Wall -Wextra -I CHAOS/gem5/src
//       tests/test_sq03_effect.cc -o /tmp/t
//   /tmp/t   -> SQ03_EFFECT_OK
//
// The brief's step-2 asserts, verbatim:
//   - a state change with no downstream difference yields LIFECYCLE_ONLY
//     with reason=NO_DOWNSTREAM_EFFECT
//   - a state change that moves the drain/visibility yields a chain.
// Plus every other EffectOutcome / reason branch, the resource-release
// observable (resource_reuse_tick) and the absent-hash sentinels (§3).

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>

#include "cpu/o3/CHAOSLSQFwd/sq03_rules.hh"

using namespace gem5::chaos_sq03;

int
main()
{
    // ---- hashValue: the absent sentinels are never real (§3) ------------
    assert(hashValue("") == 0);
    assert(hashValue("null") == 0);
    assert(hashValue("None") == 0);
    assert(hashValue("0") == 0);
    assert(hashValue("deadbeef") == 0xdeadbeefULL);
    assert(hashValue("0x1") == 0x1ULL);   // tolerates a 0x prefix

    // The injected record the trace produces for a premature canWB
    // (noteSQ03Injection): the flag was false before the executeStore hook
    // and true after it.
    Sq03Effect inj;
    inj.canwb_before = false;
    inj.canwb_after = true;
    assert(stateChanged(inj));

    // ---- no downstream difference: LIFECYCLE_ONLY / NO_DOWNSTREAM_EFFECT --
    // The store still drained AFTER its architectural commit (the order the
    // fault-free run shows too) and no reload ever bound to the chain: the
    // field change is real but nothing downstream differed.
    Sq03Effect quiet = inj;
    quiet.writeback_tick = 4000;   // writebackStores processed the entry
    quiet.drain_tick = 5000;       // cache write applied...
    quiet.commit_tick = 3000;      // ...after the architectural commit
    assert(!visibleBeforeCommit(quiet));
    assert(!phantomDrain(quiet));
    assert(!resourceReused(quiet));
    assert(effectVerdict(quiet)
           == EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT);
    assert(std::string(effectOutcomeName(effectVerdict(quiet)))
           == "LIFECYCLE_ONLY");
    assert(std::string(effectReason(effectVerdict(quiet)))
           == "NO_DOWNSTREAM_EFFECT");
    assert(std::string(lifecycleReason(quiet)) == "NO_DOWNSTREAM_EFFECT");

    // The empty tail is the same honest verdict: nothing at all was
    // observed downstream of the premature _canWB.
    Sq03Effect bare = inj;   // every tick/hash still 0 / empty
    assert(effectVerdict(bare)
           == EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT);
    assert(std::string(lifecycleReason(bare)) == "NO_DOWNSTREAM_EFFECT");

    // ---- drain/visibility moved + reload consumer: the chain -------------
    // canWB set early in executeStore lets writebackStores pick the store
    // up and apply its cache write BEFORE commit; a reload bound to the
    // chain with a real response hash verifies the consumer edge.
    Sq03Effect moved = inj;
    moved.writeback_tick = 2000;
    moved.drain_tick = 2100;       // cache write applied BEFORE commit
    moved.commit_tick = 3000;
    moved.reload_seq = 900;
    moved.reload_data_hash = "c8c89a9aee4c1c0f";
    assert(visibleBeforeCommit(moved));
    assert(effectVerdict(moved) == EffectOutcome::CHAIN_VISIBILITY_MOVED);
    assert(std::string(effectOutcomeName(effectVerdict(moved)))
           == "CHAIN_VISIBILITY_MOVED");
    assert(std::string(effectReason(effectVerdict(moved)))
           == "DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER");

    // ---- drain moved but NO reload consumer: honest LIFECYCLE_ONLY -------
    // The visibility moved, but without a verified reload edge the chain is
    // unproven — never recorded as propagation (brief step 4).
    Sq03Effect moved_no_reload = moved;
    moved_no_reload.reload_seq = 0;
    moved_no_reload.reload_data_hash.clear();
    assert(visibleBeforeCommit(moved_no_reload));
    assert(effectVerdict(moved_no_reload)
           == EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT);

    // ---- reload bound but its hash absent: unverified edge (§3) ----------
    Sq03Effect absent = moved;
    absent.reload_data_hash = "null";
    assert(effectVerdict(absent)
           == EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT);

    // ---- reload bound but drain AFTER commit: the bytes the reload read
    // were architecturally visible anyway — no visibility moved, no chain.
    Sq03Effect late = quiet;
    late.reload_seq = 900;
    late.reload_data_hash = "c8c89a9aee4c1c0f";
    assert(effectVerdict(late)
           == EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT);

    // ---- phantom store: drained, never committed ---------------------------
    // lsq_unit.cc squash() stops at canWB-marked entries ("Instructions
    // marked as can WB are already committed"), so the premature canWB
    // defeats the squash guard: a squashed store whose bytes reached memory.
    Sq03Effect phantom = inj;
    phantom.drain_tick = 2100;
    phantom.commit_tick = 0;
    assert(phantomDrain(phantom));
    assert(effectVerdict(phantom) == EffectOutcome::CHAIN_PHANTOM_STORE);
    assert(std::string(effectReason(effectVerdict(phantom)))
           == "DRAINED_WITHOUT_COMMIT");

    // ---- resource reuse only: LIFECYCLE_ONLY with the refined reason ------
    // The SQ slot was recycled for a later store (the resource-release path
    // responding), but no visibility moved and no reload consumed the
    // chain. A slot is reused in the fault-free run too, so reuse alone is
    // never propagation — it is recorded with its own source-proved reason.
    Sq03Effect reused = quiet;
    reused.resource_reuse_tick = 6000;
    assert(resourceReused(reused));
    assert(effectVerdict(reused)
           == EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT);
    assert(std::string(lifecycleReason(reused)) == "RESOURCE_REUSE_ONLY");
    // Resource reuse never upgrades a chain case to anything else either.
    Sq03Effect reused_chain = moved;
    reused_chain.resource_reuse_tick = 6000;
    assert(effectVerdict(reused_chain)
           == EffectOutcome::CHAIN_VISIBILITY_MOVED);

    // ---- no state change: no fault, no effect ------------------------------
    Sq03Effect nofault;
    nofault.canwb_before = true;   // canWB already set (normal commitStores)
    nofault.canwb_after = true;
    assert(!stateChanged(nofault));
    assert(effectVerdict(nofault)
           == EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT);
    assert(std::string(lifecycleReason(nofault)) == "NO_DOWNSTREAM_EFFECT");

    std::printf("SQ03_EFFECT_OK\n");
    return 0;
}
