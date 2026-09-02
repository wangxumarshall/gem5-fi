/* S3-7 (plan §5.4B): exclusive-monitor verification kernel.
 * LDXR/STXR pair where the SC success flag IS checked (unlike
 * fwd_7case's ldxr case which ignores it):
 *   - clear_reservation (LDXR reservation dropped): SC must fail; if the
 *     kernel still observes success (sc==0) OR the value chain breaks,
 *     the monitor is corrupted -> fails++ (Detected).
 *   - stale_reservation (SC false-success): the store goes through
 *     without a valid reservation — the golden accounting (which models
 *     the architectural contract: value committed iff SC succeeded)
 *     diverges -> fails++ (SDC-direction: lost update).
 * Deterministic: single-threaded SE, one LDXR/STXR pair per iteration.
 * Output: "iters=%ld fails=%ld variant=exmon\n" (fail_count oracle).
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define N 1024

static uint32_t rng_state = 0x5A5A1234u;
static inline uint32_t xorshift32(void){uint32_t x=rng_state;x^=x<<13;x^=x>>17;x^=x<<5;rng_state=x;return x;}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 2000;
    uint64_t *buf = aligned_alloc(64, N * sizeof(uint64_t));
    if (!buf) return 2;
    for (int i = 0; i < N; i++) buf[i] = ((uint64_t)xorshift32() << 32) | xorshift32();

    long fails = 0;
    long sc_success = 0, sc_fail = 0;
    uint64_t committed_sum = 0, golden_sum = 0;

    for (long it = 0; it < iters; it++) {
        int i = (int)(it % N);
        uint64_t golden_val = (uint64_t)it + 1;   /* what a successful SC writes */
        uint64_t got = 0; uint32_t sc = 1;
        __asm__ volatile(
            "ldxr %0, [%2]\n"
            "add %0, %0, #0\n"        /* keep got = loaded value */
            "stxr %w1, %3, [%2]\n"    /* try to store golden_val */
            : "=&r"(got), "=&r"(sc)
            : "r"(&buf[i]), "r"(golden_val)
            : "memory");
        if (sc == 0) {
            /* SC succeeded (architecturally: reservation was valid) */
            sc_success++;
            committed_sum += golden_val;
        } else {
            /* SC failed (reservation lost) — buf unchanged */
            sc_fail++;
            committed_sum += buf[i];  /* value that IS in memory now */
        }
        golden_sum += (golden_val);   /* golden: every iteration's SC
                                         succeeds on a healthy monitor */
    }
    /* On a healthy monitor every SC succeeds: committed_sum == golden_sum
     * and sc_fail == 0. A corrupted monitor diverges. */
    if (sc_fail != 0 || committed_sum != golden_sum) {
        fails++;
        fprintf(stderr, "SDC@monitor sc_success=%ld sc_fail=%ld "
                "committed=%016lx golden=%016lx xor=%016lx\n",
                sc_success, sc_fail, committed_sum, golden_sum,
                committed_sum ^ golden_sum);
    }
    printf("iters=%ld fails=%ld variant=exmon sc_ok=%ld sc_fail=%ld\n",
           iters, fails, sc_success, sc_fail);
    return fails ? 1 : 0;
}
