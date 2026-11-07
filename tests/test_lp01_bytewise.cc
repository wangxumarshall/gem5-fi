#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>

#include "cpu/o3/CHAOSL1DForward/lp01_bytewise.hh"

using namespace gem5::chaos_lp01;

static void
checkSize(unsigned n)
{
    std::vector<uint8_t> buf(n, 0xA5);
    const std::vector<uint8_t> before = buf;
    assert(corruptByte0(buf.data(), n, 0x8));
    assert(buf[0] == (uint8_t)(before[0] ^ 0x08));
    for (unsigned i = 1; i < n; ++i)
        assert(buf[i] == before[i]);
}

int
main()
{
    // Model matrix: exactly byte 0 changes, for every size.
    for (unsigned n : {1u, 4u, 7u, 8u, 9u, 12u, 16u})
        checkSize(n);

    // Size 0 is a no-op and must not touch memory.
    uint8_t zero[1] = {0xAA};
    assert(!corruptByte0(zero, 0, 0x08));
    assert(zero[0] == 0xAA);

    // mask 0 is a no-op.
    uint8_t m0[8] = {0};
    assert(!corruptByte0(m0, 8, 0));
    for (uint8_t b : m0)
        assert(b == 0);

    // A mask with no byte-0 bit is outside the LP01 lane (review fix: do not
    // silently discard random bits 8..63).
    uint8_t hi[8] = {0};
    assert(!corruptByte0(hi, 8, 0x100));
    for (uint8_t b : hi)
        assert(b == 0);

    // Only the low byte of the mask is in the modeled lane.
    uint8_t wide[4] = {0, 0, 0, 0};
    assert(corruptByte0(wide, 4, 0x1122334455667708ULL));
    assert(wide[0] == 0x08 && wide[1] == 0 && wide[2] == 0 && wide[3] == 0);

    // Ordinal helper: skip 0 -> ordinal 1; skip 4 -> ordinal 5.
    assert(eligibleOrdinal(0, 0) == 1);
    assert(eligibleOrdinal(4, 0) == 5);

    std::printf("LP01 byte-0 payload matrix (0/1/4/7/8/9/12/16): PASS\n");
    return 0;
}
