#include <cassert>
#include <cstdint>
#include <cstdio>

#include "cpu/o3/CHAOSLSQFwd/sq03_rules.hh"

using namespace gem5::chaos_sq03;

int
main()
{
    assert(shouldSetCanWB(100, 100, 0, 1));
    assert(!shouldSetCanWB(99, 100, 0, 1));
    assert(!shouldSetCanWB(100, 100, 1, 1));
    assert(!shouldSetCanWB(100, 0, 0, 1));   // 0 = no target
    // max_faults==0 must be clamped to one injection, not unlimited.
    assert(!shouldSetCanWB(100, 100, 1, 0));
    assert(shouldSetCanWB(100, 100, 0, 0));
    std::printf("SQ03 canWB rules: PASS\n");
    return 0;
}
