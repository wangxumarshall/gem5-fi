#ifndef __CPU_O3_FW02_RULES_HH__
#define __CPU_O3_FW02_RULES_HH__

// FW02 (LSU v3.2 F6 f6_fw02) pure decision / squash-causality rules —
// v3.2.12 propagation-closure round (task 9). Host-testable by construction:
// no gem5 includes, no simulator state; tests/test_fw02_decision.cc compiles
// this header with plain g++ -std=c++17 (same self-contained-header pattern
// as fw05_rules.hh / da04_byte_enable.hh / lq04_rules.hh).
//
// FW02 = conditional false miss: at the FullAddrRangeCoverage forwarding
// decision point (LSQUnit::read, the store-scan loop) the one-shot trigger
// suppresses ONE real older-store / younger-load match, so the load falls
// through to the normal memory access path (decision=suppressed,
// memory_path=1). No forwarded byte is mutated.

#include <cstdint>
#include <cstdlib>
#include <string>

namespace gem5
{
namespace chaos_fw02
{

// Trace hashes are hex strings; the absent sentinels (empty / "null" /
// "None" / "0") are NOT real hashes (acceptance standard v3.2.12 §3 — an
// absent hash can neither establish continuity nor fabricate a divergence
// nor verify an edge). FNV-1a-64 values are never 0, so 0 safely marks
// "absent" after parsing.
inline uint64_t
hashValue(const std::string &h)
{
    if (h.empty() || h == "null" || h == "None" || h == "0")
        return 0;
    return std::strtoull(h.c_str(), nullptr, 16);
}

// fw02_decision record mapping (task-9 brief interface): what the fault-free
// pipeline would have decided vs. what the faulted pipeline decided for the
// same full-coverage older-store / younger-load pair. A full-coverage match
// always forwards in the fault-free run; the fault's only possible decision
// change is suppressing that forward.
inline const char *
normalDecision()
{
    return "forwarded";
}

inline const char *
faultDecision(bool suppressed)
{
    return suppressed ? "suppressed" : "none";
}

// Data-comparison rule (task-9 brief step 1): the chain is complete when the
// load's writeback hash equals the memory response hash and the consumer
// input hash equals it. Every hash must be real (§3).
inline bool
completeChain(const std::string &resp_hash, const std::string &wb_hash,
              const std::string &consumer_hash)
{
    const uint64_t r = hashValue(resp_hash);
    const uint64_t w = hashValue(wb_hash);
    const uint64_t c = hashValue(consumer_hash);
    if (r == 0 || w == 0 || c == 0)
        return false;
    return w == r && c == w;
}

// MASKED verdict for a suppressed forward (task-9 brief step 1): a
// correct-data outcome is MASKED only with the complete-chain evidence. Data
// is correct when the memory path returned exactly the bytes the suppressed
// forward would have delivered (response hash == forwardable store hash).
inline bool
maskedWithEvidence(const std::string &store_hash,
                   const std::string &resp_hash,
                   const std::string &wb_hash,
                   const std::string &consumer_hash)
{
    const uint64_t s = hashValue(store_hash);
    const uint64_t r = hashValue(resp_hash);
    if (s == 0 || r == 0 || r != s)
        return false;
    return completeChain(resp_hash, wb_hash, consumer_hash);
}

// Squash causality (task-9 brief; standard §5 / tightening T2): a squash
// terminal is fault-caused only when the squash boundary — triggering_seq,
// the argument of LSQUnit::squash(squashed_num), which frees everything
// younger than it — IS the faulting instruction. A RECORDED boundary that is
// not the faulting instruction proves the squash unrelated (it has its own,
// non-fault cause — an older branch miss, say — even when the faulting
// instruction is one of the victims). Only an UNRECORDED boundary
// (triggering_seq == 0, the pre-wiring default) leaves the honest unproven
// state for the faulting instruction itself: causality-PARTIAL, never a
// proven SQUASHED.
enum class SquashCause
{
    FaultCaused,          // triggering_seq == fault_seq: proven fault-caused
    FaultVictimUnproven,  // the faulting inst itself was squashed, boundary
                          // not recorded -> causality unproven (PARTIAL)
    Unrelated             // recorded non-fault boundary, or no identity tie
};

inline SquashCause
classifySquash(uint64_t dyn_inst_seq, uint64_t triggering_seq,
               uint64_t fault_seq)
{
    if (fault_seq == 0)
        return SquashCause::Unrelated;
    if (triggering_seq != 0) {
        // The boundary is recorded: it names the cause outright.
        return triggering_seq == fault_seq
            ? SquashCause::FaultCaused : SquashCause::Unrelated;
    }
    // Boundary not recorded: unproven for the faulting instruction itself.
    return dyn_inst_seq == fault_seq
        ? SquashCause::FaultVictimUnproven : SquashCause::Unrelated;
}

inline const char *
squashCauseName(SquashCause c)
{
    switch (c) {
      case SquashCause::FaultCaused:         return "fault_caused";
      case SquashCause::FaultVictimUnproven: return "fault_victim_unproven";
      case SquashCause::Unrelated:           return "unrelated";
    }
    return "unrelated";
}

} // namespace chaos_fw02
} // namespace gem5

#endif // __CPU_O3_FW02_RULES_HH__
