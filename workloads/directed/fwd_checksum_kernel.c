#include <stdio.h>
#include <stdint.h>
#include <string.h>
static uint64_t cs = 0xcbf29ce484222325ULL;
static void fold(const void *p, int n) {
    uint64_t v = 0;
    memcpy(&v, p, n > 8 ? 8 : n);
    cs ^= v; cs *= 0x100000001b3ULL;
}
int main(void) {
    double buf[64];
    for (int i = 0; i < 64; i++) {
        double val = (double)(i * 7 + 3) / 2.0;
        buf[i] = val;
        double loaded = buf[i];
        fold(&loaded, sizeof(loaded));
    }
    printf("%016llx\n", cs);
    return 0;
}
