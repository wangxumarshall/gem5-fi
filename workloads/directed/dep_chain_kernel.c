/* dep_chain_kernel — §2.5 D: tight dependency chain (wakeup-select pressure).
 * Build: gcc -static -O2 -o dep_chain_kernel dep_chain_kernel.c
 */
#include <stdio.h>
#include <stdint.h>
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
    uint64_t a = 0x1234567890abcdefULL;
    for (int i = 0; i < 10000; i++) { a = a * 6364136223846793005ULL + 1442695040888963407ULL; }
    cs ^= a; cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs);
    return 0;
}
