#include <cassert>
#include <cstdio>
#include <vector>

#include "cpu/o3/CHAOSLSQFwd/da04_byte_enable.hh"

using namespace gem5::chaos_da04;

int
main()
{
    std::vector<bool> all(4, true);
    assert(eligible(4, all));
    assert(maskOf(all) == 0xF);

    assert(clearLane0(all));
    assert(maskOf(all) == 0xE);
    assert(!all[0] && all[1] && all[2] && all[3]);

    // Idempotent: a second application changes nothing.
    assert(!clearLane0(all));
    assert(!eligible(4, all));   // already faulted is not eligible

    // Only size==4, only all-ones.
    std::vector<bool> two(2, true);
    assert(!eligible(2, two));
    std::vector<bool> partial{true, false, true, true};
    assert(!eligible(4, partial));
    std::vector<bool> eight(8, true);
    assert(!eligible(8, eight));

    std::printf("DA04 byte-enable unit test: PASS\n");
    return 0;
}
