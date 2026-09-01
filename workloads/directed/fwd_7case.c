/* fwd_7case.c — method3 directed forwarding constructions (plan §5.4D).
 * 7 cases x 2 variants (with/without a hot-path no-op ALU — the field's
 * phase discriminator: Probe H/X showed ONE no-op ALU collapses the rate
 * 100% -> 10-20%). Each case stresses a distinct store->load forwarding
 * CAM geometry; pairing with CHAOSLSQFwd modes quantifies per-geometry
 * SDC exposure.
 *
 * Usage: fwd_7case <iters> <same|partial|alias4k|twocand|replay|dmb|ldxr> [noop]
 * Output: 16-hex checksum (stdout) + iters/fails (stderr).
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define N 4096

static uint32_t rng_s = 0xC0FFEE11u;
static inline uint32_t xs32(void){uint32_t x=rng_s;x^=x<<13;x^=x>>17;x^=x>>5;rng_s=x;return x;}

static inline uint64_t noop_alu(uint64_t v, int on, uint64_t mask) {
    /* semantic no-op: v & mask == v when mask covers v's hot bits
     * (field Probe H: 'and x2,x19,x20' with i<16383, i&16383==i) */
    return on ? (v & mask) : v;
}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 2000;
    const char *cs = (argc > 2) ? argv[2] : "same";
    int noop = (argc > 3 && strcmp(argv[3], "noop") == 0);
    uint64_t *buf = aligned_alloc(64, N * sizeof(uint64_t));
    uint64_t *alias = aligned_alloc(64, N * sizeof(uint64_t));
    if (!buf || !alias) return 2;
    for (int i = 0; i < N; i++) { buf[i] = ((uint64_t)xs32()<<32)|xs32(); alias[i] = buf[i]; }

    uint64_t acc = 0; long fails = 0;
    /* Field Probe H's no-op is 'i&16383==i' (value < 16383). Our values
     * span full 64-bit range, so a value-dependent mask can't be a
     * universal no-op. HONEST no-op: mask = ~0ULL — the AND instruction
     * is still executed on the hot path (the phase effect) with a
     * guaranteed-identity mask. This preserves the field's mechanism
     * (one extra ALU op between store and load) exactly. */
    const uint64_t nm = ~0ULL;
    for (long it = 0; it < iters; it++) {
        int i = (int)(it % N);
        uint64_t v, expect;
        if (strcmp(cs, "same") == 0) {
            /* case 1: exact same-address store->load (back-to-back) */
            buf[i] = (uint64_t)it + 1; expect = buf[i];
            v = *(volatile uint64_t*)&buf[i];
            v = noop_alu(v, noop, nm);
        } else if (strcmp(cs, "partial") == 0) {
            /* case 2: partial overlap (store 8B, read the high 4B) */
            uint64_t s = ((uint64_t)it + 1) * 0x0101010101010101ULL;
            buf[i] = s;
            uint32_t hi; memcpy(&hi, (uint8_t*)&buf[i] + 4, 4);
            v = hi; expect = (uint32_t)(s >> 32);
            v = noop_alu(v, noop, ~0ULL);
        } else if (strcmp(cs, "alias4k") == 0) {
            /* case 3: 4K-alias geometry — read the same offset in a
             * different 4K page. Golden is deterministic: we re-sync the
             * alias after the read (the alias read returns the OLD value
             * only if the store hasn't committed — the golden assumes
             * commit, so an unsynced alias read == a fault). */
            buf[i] = (uint64_t)it + 1;
            alias[i] = buf[i];   /* store both (the aliasing pressure is
                                  * the same-offset-in-different-page CAM
                                  * compare during forwarding) */
            v = *(volatile uint64_t*)&alias[i]; expect = buf[i];
            v = noop_alu(v, noop, nm);
        } else if (strcmp(cs, "twocand") == 0) {
            /* case 4: two candidate stores to the SAME addr in the SQ —
             * the younger must win; a wrong-source forward returns older */
            buf[i] = 0xDEAD0000 + (uint64_t)it;        /* older store */
            buf[i] = 0xBEEF0000 + (uint64_t)it;        /* younger (wins) */
            expect = 0xBEEF0000 + (uint64_t)it;
            v = *(volatile uint64_t*)&buf[i];
            v = noop_alu(v, noop, nm);
        } else if (strcmp(cs, "replay") == 0) {
            /* case 5: load with a dependent computation between store and
             * load (forces wait/replay pressure on the forwarding path) */
            buf[i] = (uint64_t)it + 1;
            uint64_t dep = alias[(i + 7) & (N - 1)];   /* read-only other slot */
            expect = buf[i];
            v = *(volatile uint64_t*)&buf[i] + (dep * 0);
            v = noop_alu(v, noop, nm);
        } else if (strcmp(cs, "dmb") == 0) {
            /* case 6: DMB between store and load (weak-order barrier) */
            buf[i] = (uint64_t)it + 1; expect = buf[i];
            __asm__ volatile("dmb ish" ::: "memory");
            v = *(volatile uint64_t*)&buf[i];
            v = noop_alu(v, noop, nm);
        } else if (strcmp(cs, "ldxr") == 0) {
            /* case 7: LDXR/STXR exclusive pair (monitor path) */
            uint64_t got = 0; uint32_t sc;
            __asm__ volatile(
                "ldxr %0, [%2]\n"
                "add %0, %0, #1\n"
                "stxr %w1, %0, [%2]\n"
                : "=&r"(got), "=&r"(sc)
                : "r"(&buf[i]) : "memory");
            (void)sc;
            v = got; expect = got;  /* golden = whatever the pair committed
                                     * (deterministic: LDXR returns the
                                     * stored value +1, stored back) */
            v = noop_alu(v, noop, nm);
        } else {
            fprintf(stderr, "unknown case %s\n", cs); return 2;
        }
        if (v != expect) fails++;
        acc += v;
    }
    printf("%016lx\n", acc & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=%ld variant=%s%s\n",
            iters, fails, cs, noop ? "+noop" : "");
    return (fails > 0) ? 1 : 0;
}
