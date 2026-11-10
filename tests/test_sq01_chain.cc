// test_sq01_chain.cc — host test for the SQ01 (LSU v3.2.12 task 11)
// store-data chain rules in
// CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/sq01_rules.hh.
//
// Build/run:
//   g++ -O2 -std=c++17 -I CHAOS/gem5/src tests/test_sq01_chain.cc -o /tmp/t
//   /tmp/t   -> SQ01_CHAIN_OK
//
// The brief's step-1 asserts, verbatim:
//   - data_after != data_before                     (the divergence)
//   - mem_write_hash == hash(data_after)            (drain carried it)
//   - reload_data_hash == mem_write_hash            (reload read it)
//   - consumer_hash == reload_data_hash             (verified consumer edge)
//   - STORE_COMMITTED_LANE_NOT_READ when no reload exists.

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>

#include "cpu/o3/CHAOSLSQFwd/sq01_rules.hh"

using namespace gem5::chaos_sq01;

int
main()
{
    // Build the SQ entry the way LSQUnit::write + maybeCorruptStoreData do:
    // byte0 bit3 (0x08) flips after the store data was copied in.
    uint8_t sq_entry[8] = {0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc};
    const uint8_t data_before = sq_entry[0];
    sq_entry[0] = (uint8_t)(sq_entry[0] ^ 0x08);
    const uint8_t data_after = sq_entry[0];

    assert(data_after != data_before);              // the divergence is real
    assert(data_after == (uint8_t)(data_before ^ 0x08));

    // The drain hash is the FNV-1a-64 of the post-flip store bytes —
    // the same hash CHAOSPropagation::noteStoreWriteback computes over the
    // SQ entry data that leaves for the cache.
    const uint64_t drain_fnv = fnv1a64(sq_entry, 8);
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%llx",
                  (unsigned long long)drain_fnv);
    const std::string mem_write_hash(buf);
    assert(hashValue(mem_write_hash) == drain_fnv);

    // ---- complete chain: every hop hash-equal ----------------------------
    Sq01Chain full;
    full.data_before = data_before;
    full.data_after = data_after;
    full.mem_write_hash = mem_write_hash;
    full.reload_seq = 900;               // a younger reload bound to the chain
    full.reload_data_hash = mem_write_hash;
    full.consumer_hash = mem_write_hash;
    assert(grade(full) == ChainVerdict::COMPLETE_CHAIN);
    assert(std::string(verdictName(grade(full))) == "COMPLETE_CHAIN");

    // ---- no reload: the honest terminal -----------------------------------
    Sq01Chain no_reload = full;
    no_reload.reload_seq = 0;
    no_reload.reload_data_hash.clear();
    no_reload.consumer_hash.clear();
    assert(grade(no_reload) == ChainVerdict::STORE_COMMITTED_LANE_NOT_READ);
    assert(std::string(verdictName(grade(no_reload)))
           == "STORE_COMMITTED_LANE_NOT_READ");

    // ---- reload bound but never consumed ----------------------------------
    Sq01Chain unconsumed = full;
    unconsumed.consumer_hash.clear();
    assert(grade(unconsumed) == ChainVerdict::PARTIAL_RELOAD_NOT_CONSUMED);

    // ---- reload read different bytes: never claim the chain ---------------
    Sq01Chain mismatch = full;
    mismatch.reload_data_hash = "1234567890abcdef";
    assert(grade(mismatch) == ChainVerdict::PARTIAL_HASH_MISMATCH);
    Sq01Chain consumer_mismatch = full;
    consumer_mismatch.consumer_hash = "1234567890abcdef";
    assert(grade(consumer_mismatch) == ChainVerdict::PARTIAL_HASH_MISMATCH);

    // ---- the corrupted byte never left the SQ ------------------------------
    Sq01Chain no_drain = full;
    no_drain.mem_write_hash.clear();
    assert(grade(no_drain) == ChainVerdict::PARTIAL_NO_DRAIN);

    // ---- a bound hop with an absent hash is an unverified edge (§3) --------
    Sq01Chain absent = full;
    absent.reload_data_hash = "null";
    assert(grade(absent) == ChainVerdict::PARTIAL_HASH_ABSENT);

    // ---- the fault did not change the lane ---------------------------------
    Sq01Chain nodiv;
    nodiv.data_before = 0x55;
    nodiv.data_after = 0x55;
    assert(grade(nodiv) == ChainVerdict::NO_DATA_DIVERGENCE);

    std::printf("SQ01_CHAIN_OK\n");
    return 0;
}
