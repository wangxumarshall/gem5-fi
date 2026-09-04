#include <stdio.h>
#include <stdint.h>
#include <string.h>
static uint64_t cs = 0xcbf29ce484222325ULL;
struct S { uint8_t a; uint16_t b; uint32_t c; uint64_t d; };
int main(void) {
    struct S s[64];
    for (int i = 0; i < 64; i++) { s[i].a=i; s[i].b=i*3; s[i].c=i*7; s[i].d=i*13ULL; }
    uint64_t sum = 0;
    for (int i = 0; i < 64; i++) { sum ^= s[i].a; sum += s[i].b; sum ^= s[i].c; sum += s[i].d; }
    cs ^= sum; cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs);
    return 0;
}
