// [LSU][V3.2.12][A01] host unit test for cpu/o3/CHAOSAddrPath/a01_coords.hh
// (plan Task 7 Step 2). Pure-header test — no gem5 build, plain g++:
//   g++ -O2 -std=c++17 -I CHAOS/gem5/src tests/test_addrpath_a01_coords.cc
//       -o /tmp/test_a01 && /tmp/test_a01
// Expected output: A01_COORDS_OK
//
// Asserts the frozen coordinate rules (LSU_Propagation_Acceptance_Standard_
// v3.2.12.md, plan Task 7 Step 2):
//   - bit-3 flip: actual_ea == golden_ea ^ (1<<3), bit == 3, xor_delta != 0
//   - no-op (masked) event: xor_delta == 0 and affected == 0
// plus the record contract: request_va == the corrupted EA, fault_va is the
// literal NOT_APPLICABLE until a fault is raised, and the detail strings use
// the CHAOSPropagation k=v;k=v dialect with NO commas (a comma would corrupt
// the CSV trace, whose detail column is the last field).

#include <cstdio>
#include <cstring>
#include <string>

#include "cpu/o3/CHAOSAddrPath/a01_coords.hh"

using namespace gem5::chaos_a01;

static int failures = 0;

static void
check(bool ok, const char *what)
{
    if (!ok) {
        std::printf("FAIL: %s\n", what);
        ++failures;
    }
}

static bool
contains(const std::string &s, const char *needle)
{
    return s.find(needle) != std::string::npos;
}

int
main()
{
    // ---- bit-3 flip (the a01_bit3_load pilot math) -----------------------
    {
        // The REAL v3.2.2 A01-R01 direction, per the on-disk
        // pilots_v3_2_2/A01-R01/addrpath_injections.log: "old_addr=0x7ffffefda0,
        // new_addr=0x7ffffefda8" — golden (old) has bit 3 clear, the corrupted
        // actual (new) has bit 3 set. (The continuation audit caught the earlier
        // test labeling the inverted pair as this run; both directions are
        // valid bit-3 flips, but the provenance values must match the run.)
        const uint64_t golden = 0x7ffffefda0ULL;   // v3.2.2 R01 golden EA
        const EACoords c = eaCoordsForFlip(1, 4242, kPcUnknown, golden, 3, 8);

        check(c.actual_ea == (golden ^ (1ULL << 3)),
              "bit-3 flip: actual == golden ^ (1<<3)");
        check(c.actual_ea == 0x7ffffefda8ULL,
              "bit-3 flip: 0x...da0 ^ 0x8 == 0x...da8");
        check(c.bit == 3, "bit-3 flip: bit == 3");
        check(c.xor_delta != 0, "bit-3 flip: xor_delta != 0");
        check(c.xor_delta == 0x8ULL, "bit-3 flip: xor_delta == 1<<3");
        check(affectedBits(c.xor_delta) == 1, "bit-3 flip: affected == 1");
        check(singleBitIndex(c.xor_delta) == 3, "bit-3 flip: single bit idx");
        check(c.request_va == c.actual_ea,
              "request VA == corrupted EA at formation");
        check(!c.fault_raised, "no fault raised at formation");
        check(c.golden_ea == golden, "golden preserved");
        check(c.access_size == 8, "access size carried");
        check(c.fault_id == 1 && c.dyn_inst_seq == 4242,
              "fault_id / dyn_inst_seq carried");
        check(c.pc == kPcUnknown, "pc sentinel carried (never fabricated)");

        const std::string d = eaDetail(c);
        check(contains(d, ";fault_va=NOT_APPLICABLE"),
              "detail: fault_va=NOT_APPLICABLE when none raised");
        check(contains(d, ";bit=3;"), "detail: bit=3");
        check(contains(d, ";golden_ea=7ffffefda0;"),
              "detail: golden_ea bare hex");
        check(contains(d, ";actual_ea=7ffffefda8;"),
              "detail: actual_ea bare hex");
        check(contains(d, ";xor_delta=8;"), "detail: xor_delta bare hex");
        check(d.find(',') == std::string::npos,
              "detail: NO commas (CSV last column)");
        check(contains(d, ";access_size=8;") && contains(d, ";affected=1;"),
              "detail: access_size / affected decimal");
    }

    // ---- fault-VA completion (sink-side recordFaultVA) --------------------
    {
        EACoords c = eaCoordsForFlip(2, 77, kPcUnknown, 0x1000, 3, 4);
        recordFaultVA(c, 0x1008);
        check(c.fault_raised && c.fault_va == 0x1008,
              "recordFaultVA sets the raised fault VA");
        const std::string d = eaDetail(c);
        check(contains(d, ";fault_va=1008"),
              "detail: fault_va hex once raised");
        check(!contains(d, "NOT_APPLICABLE"),
              "detail: no NOT_APPLICABLE once the fault VA is known");
    }

    // ---- no-op / masked event ----------------------------------------------
    {
        const EACoords c = eaCoordsNoop(3, 88, kPcUnknown, 0x2000, 4);
        check(c.actual_ea == c.golden_ea, "no-op: actual == golden");
        check(c.xor_delta == 0, "no-op: xor_delta == 0");
        check(affectedBits(c.xor_delta) == 0, "no-op: affected == 0");
        check(c.bit == kNoBit, "no-op: no single-bit identity");
        const std::string d = eaDetail(c);
        check(contains(d, ";bit=NOT_APPLICABLE;"),
              "no-op detail: bit=NOT_APPLICABLE");
        check(contains(d, ";fault_va=NOT_APPLICABLE"),
              "no-op detail: fault_va=NOT_APPLICABLE");
    }

    // ---- pure math invariants ----------------------------------------------
    {
        check(applyBitFlip(0xa8, 3) == 0xa0, "applyBitFlip byte math");
        check(applyBitFlip(applyBitFlip(0xa8, 3), 3) == 0xa8,
              "XOR flip is its own inverse");
        check(singleBitIndex(0) == kNoBit, "zero delta has no bit");
        check(singleBitIndex(0x11) == kNoBit, "two-bit delta has no bit");
        check(singleBitIndex(1ULL << 47) == 47, "high band bit index");
        check(affectedBits(0x11) == 2, "affectedBits counts set bits");

        const EACoords p = eaCoordsFromPair(4, 99, kPcUnknown, 0xf0, 0xf8, 2);
        check(p.bit == 3 && p.xor_delta == 8,
              "eaCoordsFromPair derives the bit from the delta");
        const EACoords q = eaCoordsFromPair(5, 100, kPcUnknown, 0xf0, 0xf0, 2);
        check(q.bit == kNoBit && q.xor_delta == 0,
              "eaCoordsFromPair: identical pair is a no-op");
    }

    // ---- a01_consumed record ------------------------------------------------
    {
        Consumed k;
        k.dyn_inst_seq = 4242;
        k.consumer_seq = 4299;
        k.consumer_kind = ConsumerKind::RegisterSource;
        k.input_hash = 0x123456789abcdef0ULL;
        const std::string d = consumedDetail(k);
        check(contains(d, "dyn_inst_seq=4242"), "consumed: dyn_inst_seq");
        check(contains(d, "consumer_seq=4299"), "consumed: consumer_seq");
        check(contains(d, "consumer_kind=register_source"),
              "consumed: consumer_kind name");
        check(contains(d, "input_hash=123456789abcdef0"),
              "consumed: input_hash bare hex");
        check(d.find(',') == std::string::npos, "consumed: NO commas");
        check(std::strcmp(consumerKindName(ConsumerKind::Unknown),
                          "unknown") == 0,
              "consumer kind name fallback");
    }

    if (failures != 0) {
        std::printf("test_addrpath_a01_coords: %d failure(s)\n", failures);
        return 1;
    }
    std::printf("A01_COORDS_OK\n");
    return 0;
}
