/* P-D1 / H5 probe: load-use-as-pointer kernel mirroring core 179's
 * __per_cpu_offset[i] -> rq dereference failure chain (MICROARCH_SUPPLEMENT §2.2).
 *
 * Architecture of the failure (from the vmcore forensics):
 *   1. a load of a "per-cpu offset array" element returns a STALE value from
 *      the array HEAD, byte-lane-skewed (rol_k(slot[0])); truth is intact.
 *   2. that skewed value is added to a base pointer -> bogus pointer.
 *   3. dereferencing the bogus pointer -> translation fault (kernel: Oops).
 *
 * This probe emulates steps 1-3 in user space: it keeps an array of pointers
 * (analog of __per_cpu_offset[]) and dereferences the loaded entry. Under
 * CHAOSLSQFwd structuralFault=byte_lane_skew, the loaded pointer is a byte-
 * rotated form of the array-head entry. We detect SDC by comparing the
 * dereferenced value against the expected (golden) value, and we detect
 * pointer corruption by checking the loaded pointer is canonical & in-range.
 *
 * Pure libc, no main deps; static link for gem5 SE mode. Exits 0 on pass,
 * 1 on SDC, 2 on setup error. The "fails" counter separates:
 *   - PTR_CORRUPT: loaded pointer itself is wrong (the D1 signature)
 *   - VAL_MISMATCH: dereferenced value mismatches golden
 *
 * Note: under byte_lane_skew the loaded pointer will usually be non-canonical
 * (bits shifted), so PTR_CORRUPT fires and the deref is skipped (mimicking
 * the kernel Oops rather than SIGSEGV-ing the sim).
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define NPTR 256          /* analog of __per_cpu_offset[0..191] */
#define TARGET_IDX 146    /* the slot the kernel crashed loading (15:58) */

static uint64_t rng_state = 0x123456789abcdef0ULL;
static inline uint64_t xorshift64(void) {
    uint64_t x = rng_state;
    x ^= x << 13; x ^= x >> 7; x ^= x << 17;
    rng_state = x; return x;
}

/* Each "pointer slot" points to a 64-bit target whose golden value we know. */
int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 1000;
    uint64_t *slots = (uint64_t*)malloc(NPTR * sizeof(uint64_t)); /* ptr array */
    uint64_t *targets = (uint64_t*)malloc(NPTR * sizeof(uint64_t)); /* pointees */
    if (!slots || !targets) return 2;

    /* init: each slot[j] = &targets[j]; each target[j] = golden(j). */
    for (int j = 0; j < NPTR; j++) {
        targets[j] = 0x1000ULL * (j + 1);     /* golden: distinct per slot */
        slots[j] = (uint64_t)&targets[j];
    }

    long ptr_corrupt = 0, val_mismatch = 0;
    for (long it = 0; it < iters; it++) {
        if ((it & 63) == 0) { rng_state = 0x9E3779B97F4A7C15ULL * (it + 1); }
        /* Method2-style store-then-reload so the checked load travels the
         * store->load FORWARDING path (the CHAOSLSQFwd injection site). The
         * kernel's __per_cpu_offset is .data (no pending store), but the
         * D1 *defect* sits on the load-return path that store-forwarding also
         * uses; method2/v3 localized the defect precisely on this path. So to
         * exercise the injector we store-then-reload the slot under test. */
        slots[TARGET_IDX] = (uint64_t)&targets[TARGET_IDX];  /* (re)store truth */
        volatile uint64_t loaded = slots[TARGET_IDX];          /* reload = forward */
        uint64_t p = loaded;

        /* PTR_CORRUPT detection: the loaded pointer should equal slots[TARGET_IDX].
         * A byte-lane skew makes it differ from every valid slot. */
        if (p != (uint64_t)&targets[TARGET_IDX]) {
            ptr_corrupt++;
            if (ptr_corrupt <= 8) {
                fprintf(stderr, "PTR_CORRUPT it=%ld loaded=%016lx truth=%016lx xor=%016lx\n",
                        it, loaded, (uint64_t)&targets[TARGET_IDX],
                        loaded ^ (uint64_t)&targets[TARGET_IDX]);
            }
            continue;  /* skip deref — would SIGSEGV/Oops, as the kernel did */
        }

        /* deref (analog of rq = *(ptr+base)). */
        uint64_t got = *(uint64_t*)p;
        if (got != targets[TARGET_IDX]) {
            val_mismatch++;
            if (val_mismatch <= 8)
                fprintf(stderr, "VAL_MISMATCH it=%ld got=%016lx golden=%016lx\n",
                        it, got, targets[TARGET_IDX]);
        }
    }

    long fails = ptr_corrupt + val_mismatch;
    printf("iters=%ld ptr_corrupt=%ld val_mismatch=%ld fails=%ld\n",
           iters, ptr_corrupt, val_mismatch, fails);
    free(slots); free(targets);
    return fails ? 1 : 0;
}
