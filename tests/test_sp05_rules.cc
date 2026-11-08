#include <cassert>
#include <cstdio>
#include "cpu/o3/CHAOSLSQFwd/sp05_rules.hh"
using namespace gem5::chaos_sp05;
int main() {
    assert(shouldComplete(7, 9, 7, 9, 0, 1));
    assert(!shouldComplete(7, 9, 7, 9, 1, 1));
    assert(!shouldComplete(8, 9, 7, 9, 0, 1));
    assert(!shouldComplete(7, 8, 7, 9, 0, 1));
    assert(!shouldComplete(7, 9, 0, 0, 0, 1));   // no target
    assert(!shouldComplete(7, 9, 7, 9, 1, 0));   // clamp 0 -> 1
    // v3.2.9: ordinal target selection for the premature-completion hook.
    assert(shouldSelect(2, 2));
    assert(!shouldSelect(2, 0));       // ordinal 0 = not selected
    assert(!shouldSelect(1, 2));       // not yet
    assert(!shouldSelect(2, 1));       // wrong ordinal
    std::printf("SP05 completion rules: PASS\n");
    return 0;
}
