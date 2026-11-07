#include <cassert>
#include <cstdint>
#include <cstdio>

#include "cpu/o3/CHAOSL1DForward/lp01_bytewise.hh"

using namespace gem5::chaos_lp01;

int
main()
{
    uint8_t buf[4] = {0, 0, 0, 0};
    xorMask(buf, 4, 0x1122334455667788ULL);
    assert(buf[0] == 0x88);
    assert(buf[1] == 0x77);
    assert(buf[2] == 0x66);
    assert(buf[3] == 0x55);

    uint8_t one[1] = {0xAA};
    xorMask(one, 1, 0xFF);
    assert(one[0] == 0x55);

    // 7-byte payload: only the first 7 bytes are touched (no 8-byte store).
    uint8_t seven[7] = {0};
    xorMask(seven, 7, 0x00000000000000FFULL);
    assert(seven[0] == 0xFF);
    for (int i = 1; i < 7; ++i)
        assert(seven[i] == 0x00);

    // 16-byte payload: the mask repeats every 8 bytes, identical to the old
    // two-uint64-word behaviour.
    uint8_t sixteen[16] = {0};
    xorMask(sixteen, 16, 0x0102030405060708ULL);
    assert(sixteen[0] == 0x08 && sixteen[8] == 0x08);
    assert(sixteen[7] == 0x01 && sixteen[15] == 0x01);

    std::printf("LP01 byte-wise corruption unit test: PASS\n");
    return 0;
}
