#include <stdio.h>
#include <stdint.h>
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
    uint64_t acc = 0x1234;
    for (int i = 0; i < 10000; i++) { acc = acc * 7 + i * 3 + 1; }
    cs ^= acc; cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs);
    return 0;
}
