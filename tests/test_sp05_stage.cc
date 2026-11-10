// test_sp05_stage.cc — host test for the SP05 (LSU v3.2.12 task 13)
// pipeline-stage vs memory-visibility grading in
// CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/sp05_rules.hh.
//
// Build/run (same invocation as the other rule host tests):
//   g++ -O2 -std=c++17 -Wall -Wextra -I CHAOS/gem5/src
//       tests/test_sp05_stage.cc -o /tmp/t
//   /tmp/t   -> SP05_STAGE_OK
//
// The brief's step-2 asserts, verbatim:
//   - a premature completion with correct data must classify MASKED with
//     MaskingMechanism=DATA_WRITTEN_CORRECTLY
//   - a visibility change with a reload consumer must produce a data chain.
// Plus data_correct's tri-state and every other StageOutcome.

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>

#include "cpu/o3/CHAOSLSQFwd/sp05_rules.hh"

using namespace gem5::chaos_sp05;

int
main()
{
    // ---- hashValue: the absent sentinels are never real (§3) ------------
    assert(hashValue("") == 0);
    assert(hashValue("null") == 0);
    assert(hashValue("None") == 0);
    assert(hashValue("0") == 0);
    assert(hashValue("deadbeef") == 0xdeadbeefULL);

    // The three stages the trace separates for an SP05 store — commit is
    // NOT visibility, both ticks are recorded (brief step 1):
    //   the target is selected at commitStores (commit_tick) and completed
    //   prematurely inside writebackStores (completion_tick ==
    //   writeback_tick), which skips the cache write (drain_tick stays 0).
    Sp05Stage st;
    st.commit_tick = 1000;       // architectural commit
    st.writeback_tick = 1200;    // writebackStores processed the entry
    st.completion_tick = 1200;   // premature completeStore (send skipped)
    st.drain_tick = 0;           // the cache write never happened
    assert(writeSkipped(st));    // the definitive SP05 fact: write is lost
    assert(st.commit_tick != 0 && st.drain_tick == 0);

    // ---- premature completion, correct data: MASKED / --------------------
    // ---- MaskingMechanism=DATA_WRITTEN_CORRECTLY --------------------------
    // A reload bound to the chain read exactly the store's intended bytes
    // (e.g. the line already held them / a same-value writer covered the
    // dropped write), so the lost write is unobservable in the loaded
    // value: data_correct=1.
    Sp05Stage masked = st;
    masked.reload_seq = 900;
    masked.store_data_hash = "c8c89a9aee4c1c0f";
    masked.reload_data_hash = masked.store_data_hash;
    assert(stageVerdict(masked)
           == StageOutcome::MASKED_DATA_WRITTEN_CORRECTLY);
    assert(std::string(stageOutcomeName(stageVerdict(masked))) == "MASKED");
    assert(std::string(maskingMechanism(stageVerdict(masked)))
           == "DATA_WRITTEN_CORRECTLY");
    assert(std::string(dataCorrect(masked)) == "1");
    assert(writeSkipped(masked));   // masked WITH the write still skipped

    // ---- visibility change with a reload consumer: the data chain ---------
    // The dropped write left the old bytes in the line and the reload read
    // them: the loaded value visibly diverged from the store's intent —
    // data_correct=0, never MASKED.
    Sp05Stage chain = st;
    chain.reload_seq = 900;
    chain.store_data_hash = "c8c89a9aee4c1c0f";
    chain.reload_data_hash = "1e2f2a9a6a0d0af1";
    assert(stageVerdict(chain) == StageOutcome::CHAIN_VISIBILITY_LOST);
    assert(std::string(stageOutcomeName(stageVerdict(chain)))
           == "CHAIN_VISIBILITY_LOST");
    assert(std::string(maskingMechanism(stageVerdict(chain)))
           == "NOT_APPLICABLE");
    assert(std::string(dataCorrect(chain)) == "0");

    // ---- skipped write, no reload: honestly unobservable ------------------
    // The write is lost but no load ever read the lane: the frozen
    // SP05_Source_Audit_v3.2.9 §5 "unobservable" case; data_correct stays
    // unknown ("null"), never claimed as either correct or a chain.
    Sp05Stage noreload = st;
    assert(stageVerdict(noreload) == StageOutcome::NO_RELOAD_OBSERVED);
    assert(std::string(stageOutcomeName(stageVerdict(noreload)))
           == "NO_RELOAD_OBSERVED");
    assert(std::string(dataCorrect(noreload)) == "null");

    // ---- a bound hop with an absent hash: unverified, never a chain (§3) --
    Sp05Stage unver_store = chain;
    unver_store.store_data_hash = "null";   // store bytes hash not recorded
    assert(stageVerdict(unver_store) == StageOutcome::RELOAD_UNVERIFIABLE);
    assert(std::string(dataCorrect(unver_store)) == "null");
    Sp05Stage unver_reload = chain;
    unver_reload.reload_data_hash.clear();  // reload response hash absent
    assert(stageVerdict(unver_reload) == StageOutcome::RELOAD_UNVERIFIABLE);
    assert(std::string(stageOutcomeName(stageVerdict(unver_reload)))
           == "RELOAD_UNVERIFIABLE");
    assert(std::string(dataCorrect(unver_reload)) == "null");

    // ---- a normal completion is not an SP05 record: writeSkipped keys on
    // completion-without-drain only, and the stage ticks stay separated
    // (commit != completion != visibility).
    Sp05Stage normal = masked;
    normal.drain_tick = 1300;    // the cache write happened after completion
    assert(!writeSkipped(normal));
    assert(normal.commit_tick < normal.completion_tick
           && normal.completion_tick < normal.drain_tick);
    // With the write drained, a matching reload still reads correct data.
    assert(stageVerdict(normal)
           == StageOutcome::MASKED_DATA_WRITTEN_CORRECTLY);

    std::printf("SP05_STAGE_OK\n");
    return 0;
}
