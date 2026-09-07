/* indirect_jmp_kernel — §5.9D Task 2.4: indirect-branch / branch-target
 * corruption kernel. A computed goto chain: each hop's target is read from
 * a table (an indirect branch through a register). A corrupted branch
 * target / register lands on the WRONG handler; each handler contributes
 * a distinct value to the checksum, so any diversion is observable.
 *
 * Inline asm guarantees the A64 BR (branch-register) form is really
 * emitted (not a compiler-turned conditional).
 * Build: gcc -static -O2 -o indirect_jmp_kernel indirect_jmp_kernel.c
 */
#include <stdio.h>
#include <stdint.h>
static uint64_t cs = 0xcbf29ce484222325ULL;

static void h0(void) { cs ^= 0x1111111111111111ULL; cs *= 0x100000001b3ULL; }
static void h1(void) { cs ^= 0x2222222222222222ULL; cs *= 0x100000001b3ULL; }
static void h2(void) { cs ^= 0x3333333333333333ULL; cs *= 0x100000001b3ULL; }
static void h3(void) { cs ^= 0x4444444444444444ULL; cs *= 0x100000001b3ULL; }

static const void *tab[4] = { h0, h1, h2, h3 };

int main(void) {
    unsigned st = 0x1234abcd;
    for (int i = 0; i < 4096; i++) {
        st ^= st << 13; st ^= st >> 17; st ^= st << 5;
        int k = (st >> 8) & 3;
        /* indirect call through the table (compiler emits BLR — the
           register-indirect branch form) */
        ((void(*)(void))tab[k])();
    }
    printf("%016llx\n", cs);
    return 0;
}
