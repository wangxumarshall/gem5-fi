// test_fw02_decision.cc — host test for the FW02 (LSU v3.2.12 task 9)
// decision-record and squash-causality rules in
// CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/fw02_rules.hh.
//
// Build/run (same invocation as the other rule host tests):
//   g++ -O2 -std=c++17 -I CHAOS/gem5/src tests/test_fw02_decision.cc -o /tmp/t
//   /tmp/t   -> FW02_DECISION_OK

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>

#include "cpu/o3/CHAOSLSQFwd/fw02_rules.hh"

using namespace gem5::chaos_fw02;

int
main()
{
    // ---- decision-record mapping: what fw02_decision must report --------
    // A full-coverage pair always forwards in the fault-free run; the fault
    // can only suppress that one forward (the load then takes the memory
    // path, memory_path=1).
    assert(std::string(normalDecision()) == "forwarded");
    assert(std::string(faultDecision(true)) == "suppressed");
    assert(std::string(faultDecision(false)) == "none");

    // ---- hashValue: the absent sentinels are never real (§3) ------------
    assert(hashValue("") == 0);
    assert(hashValue("null") == 0);
    assert(hashValue("None") == 0);
    assert(hashValue("0") == 0);
    assert(hashValue("deadbeef") == 0xdeadbeefULL);
    assert(hashValue("0x1") == 0x1ULL);   // tolerates a 0x prefix

    // ---- completeChain (task-9 brief step 1): resp == wb == consumer ----
    const std::string h1 = "c8c89a9aee4c1c0f";
    const std::string h2 = "1e2f2a9a6a0d0af1";
    assert(completeChain(h1, h1, h1));
    assert(!completeChain(h1, h1, h2));       // consumer input hash differs
    assert(!completeChain(h1, h2, h2));        // writeback hash differs
    assert(!completeChain("", h1, h1));        // absent response hash
    assert(!completeChain(h1, "null", h1));   // absent writeback hash
    assert(!completeChain(h1, h1, "0"));       // absent consumer hash
    assert(!completeChain(h1, h1, ""));         // absent consumer hash

    // ---- maskedWithEvidence: correct data is MASKED only with the chain -
    assert(maskedWithEvidence(h1, h1, h1, h1));   // memory returned the
                                                  // forwardable bytes AND
                                                  // the chain holds
    assert(!maskedWithEvidence(h1, h2, h1, h1));   // data differs: not MASKED
    assert(!maskedWithEvidence(h1, h1, h2, h2));   // chain broken
    assert(!maskedWithEvidence("", h1, h1, h1));   // no forwardable hash
    assert(!maskedWithEvidence(h1, "", h1, h1));   // no response hash
    assert(!maskedWithEvidence(h1, h1, "", h1));   // no writeback hash
    assert(!maskedWithEvidence(h1, h1, h1, ""));   // no consumer hash

    // ---- squash causality (standard §5 / T2) -----------------------------
    // Recorded squash boundary IS the faulting instruction: proven.
    assert(classifySquash(50, 100, 100) == SquashCause::FaultCaused);
    // Recorded boundary is a DIFFERENT instruction: proven unrelated, even
    // when the faulting instruction is one of the squash victims.
    assert(classifySquash(100, 90, 100) == SquashCause::Unrelated);
    assert(classifySquash(50, 60, 100) == SquashCause::Unrelated);
    // Boundary NOT recorded (pre-wiring default): the faulting instruction
    // itself being squashed stays causality-unproven (PARTIAL, never a
    // proven SQUASHED verdict) — the v3.2.11 MD04/FW02 R01/R05 case.
    assert(classifySquash(100, 0, 100) == SquashCause::FaultVictimUnproven);
    // Any other squashed instruction without a recorded boundary.
    assert(classifySquash(50, 0, 100) == SquashCause::Unrelated);
    // No fault identity at all.
    assert(classifySquash(50, 60, 0) == SquashCause::Unrelated);

    assert(std::string(squashCauseName(SquashCause::FaultCaused))
           == "fault_caused");
    assert(std::string(squashCauseName(SquashCause::FaultVictimUnproven))
           == "fault_victim_unproven");
    assert(std::string(squashCauseName(SquashCause::Unrelated))
           == "unrelated");

    std::printf("FW02_DECISION_OK\n");
    return 0;
}
