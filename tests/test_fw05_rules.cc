#include <cassert>
#include <cstdint>
#include <cstdio>

#include "cpu/o3/CHAOSLSQFwd/fw05_rules.hh"

using namespace gem5::chaos_fw05;

int
main()
{
    uint8_t t[16] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16};
    uint8_t a[16] = {9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9};

    Candidate tr{100, 0x1000, 16, t};
    Candidate ok{90, 0x1000, 16, a};
    Candidate partial{90, 0x1000, 8, a};       // no multi-store splice
    Candidate shortcov{90, 0x1004, 8, a};      // does not cover load start
    Candidate same{90, 0x1000, 16, t};         // identical data
    Candidate notolder{110, 0x1000, 16, a};    // not older than true source

    unsigned off = 0;
    assert(isEligible(200, 0x1000, 16, tr, ok, off));
    assert(off == 0);
    assert(!isEligible(200, 0x1000, 16, tr, partial, off));
    assert(!isEligible(200, 0x1000, 16, tr, shortcov, off));
    assert(!isEligible(200, 0x1000, 16, tr, same, off));
    assert(!isEligible(200, 0x1000, 16, tr, notolder, off));
    assert(!isEligible(50, 0x1000, 16, tr, ok, off));   // load not younger

    // The alternative store starts 4 bytes before the load and covers the
    // whole load range; the copy is taken at that real offset.
    uint8_t a2[20] = {9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9};
    Candidate before{90, 0x0ffc, 20, a2};
    assert(isEligible(200, 0x1000, 16, tr, before, off));
    assert(off == 4);

    // The true source must itself cover the load range.
    Candidate trueshort{100, 0x1000, 8, t};
    assert(!isEligible(200, 0x1000, 16, trueshort, ok, off));

    std::printf("FW05 wrong-source rules: PASS\n");
    return 0;
}
