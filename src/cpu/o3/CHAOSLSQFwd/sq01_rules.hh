#ifndef __CPU_O3_SQ01_RULES_HH__
#define __CPU_O3_SQ01_RULES_HH__

// SQ01 (LSU v3.2.3 sq01_bit3) pure store-data chain rules — v3.2.12
// propagation-closure round (task 11). Host-testable by construction
// (tests/test_sq01_chain.cc, plain g++ -std=c++17; same self-contained
// pattern as fw05_rules.hh / lq04_rules.hh).
//
// SQ01 flips byte0 bit3 (0x08) of a store's SQ entry after LSQUnit::write()
// copied the store data in, before forwarding/writeback can consume it. The
// chain under test (task-11 brief):
//   SQ entry byte0   data_before -> data_after   (the divergence)
//   -> drain         mem_write_hash == hash of the post-flip store data
//   -> reload        reload_data_hash == mem_write_hash
//   -> consumer      consumer_hash == reload_data_hash
// With no reload ever bound, the honest terminal is
// STORE_COMMITTED_LANE_NOT_READ: the store committed (and its lane drained)
// but no load ever read the faulted byte.

#include <cstdint>
#include <cstdlib>
#include <string>

namespace gem5
{
namespace chaos_sq01
{

// FNV-1a 64 — identical constants to CHAOSPropagation::fnv1a64, so host-side
// hashes match simulator-side hashes byte for byte.
inline uint64_t
fnv1a64(const uint8_t *p, unsigned n)
{
    uint64_t h = 14695981039346656037ULL;  // FNV-1a 64 offset basis
    for (unsigned i = 0; i < n; ++i) {
        h ^= p[i];
        h *= 1099511628211ULL;             // FNV-1a 64 prime
    }
    return h;
}

// Absent-sentinel rule shared with chaos_fw02 / chaos_sp05 (standard §3):
// empty / "null" / "None" / "0" are ABSENT hashes, never real ones.
inline uint64_t
hashValue(const std::string &h)
{
    if (h.empty() || h == "null" || h == "None" || h == "0")
        return 0;
    return std::strtoull(h.c_str(), nullptr, 16);
}

enum class ChainVerdict
{
    COMPLETE_CHAIN,                 // diverged byte drained, reloaded and
                                    // consumed — every hop hash-equal
    STORE_COMMITTED_LANE_NOT_READ,  // store committed+drained, no reload
    PARTIAL_NO_DRAIN,               // corrupted byte never left the SQ
    PARTIAL_HASH_ABSENT,            // a bound hop's hash is absent — the
                                    // edge is unverified, never a chain
    PARTIAL_RELOAD_NOT_CONSUMED,    // reload bound, no verified consumer edge
    PARTIAL_HASH_MISMATCH,          // a hop hash differs — investigate,
                                    // never claim the chain
    NO_DATA_DIVERGENCE              // data_after == data_before
};

struct Sq01Chain
{
    uint8_t data_before = 0;       // SQ entry byte0 at injection
    uint8_t data_after = 0;        // after the bit3 flip
    std::string mem_write_hash;    // drained store data hash ("" = no drain)
    uint64_t reload_seq = 0;       // 0 = no reload bound to the chain
    std::string reload_data_hash;  // reload response data hash
    std::string consumer_hash;     // verified consumer input hash
};

inline ChainVerdict
grade(const Sq01Chain &c)
{
    if (c.data_after == c.data_before)
        return ChainVerdict::NO_DATA_DIVERGENCE;
    if (hashValue(c.mem_write_hash) == 0)
        return ChainVerdict::PARTIAL_NO_DRAIN;
    if (c.reload_seq == 0)
        return ChainVerdict::STORE_COMMITTED_LANE_NOT_READ;
    if (hashValue(c.reload_data_hash) == 0)
        return ChainVerdict::PARTIAL_HASH_ABSENT;
    if (hashValue(c.reload_data_hash) != hashValue(c.mem_write_hash))
        return ChainVerdict::PARTIAL_HASH_MISMATCH;
    if (hashValue(c.consumer_hash) == 0)
        return ChainVerdict::PARTIAL_RELOAD_NOT_CONSUMED;
    if (hashValue(c.consumer_hash) != hashValue(c.reload_data_hash))
        return ChainVerdict::PARTIAL_HASH_MISMATCH;
    return ChainVerdict::COMPLETE_CHAIN;
}

inline const char *
verdictName(ChainVerdict v)
{
    switch (v) {
      case ChainVerdict::COMPLETE_CHAIN:
          return "COMPLETE_CHAIN";
      case ChainVerdict::STORE_COMMITTED_LANE_NOT_READ:
          return "STORE_COMMITTED_LANE_NOT_READ";
      case ChainVerdict::PARTIAL_NO_DRAIN:
          return "PARTIAL_NO_DRAIN";
      case ChainVerdict::PARTIAL_HASH_ABSENT:
          return "PARTIAL_HASH_ABSENT";
      case ChainVerdict::PARTIAL_RELOAD_NOT_CONSUMED:
          return "PARTIAL_RELOAD_NOT_CONSUMED";
      case ChainVerdict::PARTIAL_HASH_MISMATCH:
          return "PARTIAL_HASH_MISMATCH";
      case ChainVerdict::NO_DATA_DIVERGENCE:
          return "NO_DATA_DIVERGENCE";
    }
    return "NO_DATA_DIVERGENCE";
}

} // namespace chaos_sq01
} // namespace gem5

#endif // __CPU_O3_SQ01_RULES_HH__
