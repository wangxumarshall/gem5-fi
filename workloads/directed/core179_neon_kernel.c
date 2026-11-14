/* Standalone re-implementation of the OpenDCDiag core-179 trigger loop.
 *
 * Source of truth: 179core-docs/test.c (sandstone test
 * ``neon_rot_ldr_at_top_rowmajor``).  That file cannot be compiled outside
 * OpenDCDiag (it needs sandstone.h / TEST_LOOP / memset_random), so this
 * workload reproduces its *inner loop* instruction structure for gem5
 * measurement:
 *
 *   per element: 3 x 128-bit NEON loads (scratch, srcA, srcB)
 *                rotating 128-bit ALU op (add / eor / and / orr, by i % 4)
 *                2 x 128-bit NEON stores (temp, dst)
 *   per sweep:   alternate ascending / descending index order
 *                optional full-buffer comparison of dst against golden
 *
 * The comparison pass replaces libc memcmp with an explicit 64-bit scan so
 * the run does not depend on the host glibc's SVE/NEON dispatch.  It reads
 * the same 16 KiB of dst data, which is what matters for L1D traffic.
 *
 * Arguments: <elements> <sweeps> <check 0|1>
 * Status line: kernel=core179-neon ... status=DONE
 *
 * This is a measurement harness, not a functional replacement for the
 * OpenDCDiag test: it does not reproduce the test framework's warm-up,
 * thread pinning, or failing-seed search.
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include <arm_neon.h>
#include <gem5/m5ops.h>

#if !defined(__aarch64__)
#error "core179 kernel requires AArch64"
#endif

#define DEFAULT_ELEMENTS 1024
#define DEFAULT_SWEEPS 8

static inline uint64x2_t
load_vec(const void *addr)
{
    uint64x2_t result;
    __asm__ volatile("ldr %q0, [%1]" : "=w"(result) : "r"(addr) : "memory");
    return result;
}

static inline void
store_vec(void *addr, uint64x2_t value)
{
    __asm__ volatile("str %q0, [%1]" : : "w"(value), "r"(addr) : "memory");
}

static uint64_t rng_state = 0x0123456789abcdefULL;

static uint64_t
xorshift64(void)
{
    uint64_t x = rng_state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    rng_state = x;
    return x;
}

static void
fill(uint64x2_t *buffer, int count)
{
    for (int i = 0; i < count; ++i)
        buffer[i] = vdupq_n_u64(xorshift64());
}

static uint64x2_t
rotate_op(uint64x2_t a, uint64x2_t b, int index)
{
    switch (index & 3) {
      case 0: return vaddq_u64(a, b);
      case 1: return veorq_u64(a, b);
      case 2: return vandq_u64(a, b);
      default: return vorrq_u64(a, b);
    }
}

int
main(int argc, char **argv)
{
    const int count = argc > 1 ? atoi(argv[1]) : DEFAULT_ELEMENTS;
    const int sweeps = argc > 2 ? atoi(argv[2]) : DEFAULT_SWEEPS;
    const int check = argc > 3 ? atoi(argv[3]) : 1;

    if (count <= 0 || count % 4 != 0 || sweeps <= 0 || sweeps > 4096)
        return 2;

    const size_t bytes = (size_t)count * sizeof(uint64x2_t);
    uint64x2_t *src_a = aligned_alloc(64, bytes);
    uint64x2_t *src_b = aligned_alloc(64, bytes);
    uint64x2_t *scratch = aligned_alloc(64, bytes);
    uint64x2_t *expected = aligned_alloc(64, bytes);
    uint64x2_t *temp = aligned_alloc(64, bytes);
    uint64x2_t *dst = aligned_alloc(64, bytes);

    if (!src_a || !src_b || !scratch || !expected || !temp || !dst)
        return 3;

    fill(src_a, count);
    fill(src_b, count);
    fill(scratch, count);

    for (int i = 0; i < count; ++i)
        expected[i] = rotate_op(src_a[i], src_b[i], i);

    uint64_t sweep = 0;
    int mismatches = 0;

    m5_work_begin(7, 0);
    for (sweep = 0; sweep < (uint64_t)sweeps; ++sweep) {
        const int ascending = (sweep & 1) == 0;
        for (int n = 0; n < count; ++n) {
            const int i = ascending ? n : (count - 1 - n);

            uint64x2_t unused = load_vec(&scratch[i]);
            (void)unused;

            uint64x2_t a = load_vec(&src_a[i]);
            uint64x2_t b = load_vec(&src_b[i]);
            uint64x2_t res = rotate_op(a, b, i);

            store_vec(&temp[i], res);
            store_vec(&dst[i], res);
        }

        if (check) {
            const uint64_t *got = (const uint64_t *)dst;
            const uint64_t *want = (const uint64_t *)expected;
            for (int i = 0; i < count * 2; ++i) {
                if (got[i] != want[i]) {
                    ++mismatches;
                    break;
                }
            }
        }
    }
    m5_work_end(7, 0);

    printf("kernel=core179-neon elements=%d sweeps=%d check=%d "
           "mismatches=%d status=%s\n", count, sweeps, check, mismatches,
           mismatches == 0 ? "DONE" : "FAIL");

    free(src_a);
    free(src_b);
    free(scratch);
    free(expected);
    free(temp);
    free(dst);
    return mismatches == 0 ? 0 : 1;
}
