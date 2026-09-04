#include <stdio.h>
#include <stdint.h>
static uint64_t cs = 0xcbf29ce484222325ULL;
uint32_t crc32_simple(uint32_t crc, const uint8_t *buf, int len) {
    for (int i = 0; i < len; i++) { crc ^= buf[i]; for (int b=0;b<8;b++) crc = (crc>>1) ^ (0xEDB88320 & -(crc&1)); }
    return crc;
}
int main(void) {
    uint8_t buf[256];
    for (int i = 0; i < 256; i++) buf[i] = i;
    uint32_t crc = 0xFFFFFFFF;
    uint64_t sum = 0;
    for (int r = 0; r < 10; r++) { crc = crc32_simple(crc, buf, 256); sum += crc; }
    cs ^= sum; cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs);
    return 0;
}
