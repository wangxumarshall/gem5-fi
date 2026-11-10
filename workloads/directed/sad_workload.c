/* Directed workload for the O3 Structure Activation Depth (SAD) metric.
 *
 * Each mode executes a known body inside m5_work_begin(7,0)/end. The body
 * deliberately stresses one observable resource class so `--sad` ratios can be
 * compared directionally between modes. Correctness is checked against a C
 * reference; a silently mis-executing mode fails before it can poison a SAD
 * experiment.
 *
 * Usage: sad_workload <nop|rob|lsq|prf> <iterations>
 */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gem5/m5ops.h>

#if !defined(__aarch64__)
#error "sad_workload requires AArch64"
#endif

/* One hot line; lsq mode loads and stores the same line. */
static uint64_t data[64] __attribute__((aligned(64))) = {
    [0] = 0x0123456789abcdefULL,
    [1] = 0xfedcba9876543210ULL,
};

#define BODY_NOP                                                             \
    ".rept 64\n\t"                                                          \
    "nop\n\t"                                                               \
    ".endr\n\t"

#define BODY_ROB                                                             \
    ".rept 64\n\t"                                                          \
    "add x9, x9, #1\n\t"                                                    \
    ".endr\n\t"

#define BODY_LSQ                                                             \
    ".rept 32\n\t"                                                          \
    "ldr x9, [%[buf]]\n\t"                                                  \
    "str x9, [%[buf], #8]\n\t"                                              \
    ".endr\n\t"

/* Independent register writes: alternate destinations, no true dependencies. */
#define BODY_PRF                                                             \
    ".rept 16\n\t"                                                          \
    "add x9, x10, #1\n\t"                                                   \
    "add x11, x10, #2\n\t"                                                  \
    "add x12, x10, #3\n\t"                                                  \
    "add x13, x10, #4\n\t"                                                  \
    ".endr\n\t"

enum sad_mode {
    SAD_NOP,
    SAD_ROB,
    SAD_LSQ,
    SAD_PRF,
    SAD_COUNT,
};

static const char *const mode_names[SAD_COUNT] = {
    "nop", "rob", "lsq", "prf",
};

static int
parse_mode(const char *name)
{
    for (int i = 0; i < SAD_COUNT; ++i) {
        if (strcmp(name, mode_names[i]) == 0)
            return i;
    }
    return -1;
}

int
main(int argc, char **argv)
{
    if (argc != 3 && argc != 4)
        return 2;
    const int mode = parse_mode(argv[1]);
    if (mode < 0)
        return 2;
    const bool no_markers = argc == 4 && strcmp(argv[3], "no-markers") == 0;
    const uint64_t iterations = strtoull(argv[2], NULL, 0);
    if (!iterations || iterations > 1000000)
        return 2;

    uint64_t *buffer = data;
    uint64_t count = iterations, value = 0;
    if (!no_markers)
        m5_work_begin(7, 0);
    switch (mode) {
      case SAD_NOP:
        __asm__ volatile(
            "mov x9, #0\n\t"
            "mov x10, #7\n\t"
            "mov x14, %[n]\n\t"
            "1:\n\t" BODY_NOP
            "subs x14, x14, #1\n\t"
            "b.ne 1b\n\t"
            "mov %[v], x9\n\t"
            : [n] "+r"(count), [v] "=r"(value)
            :
            : "x9", "x10", "x14", "cc", "memory");
        break;
      case SAD_ROB:
        __asm__ volatile(
            "mov x9, #0\n\t"
            "mov x14, %[n]\n\t"
            "1:\n\t" BODY_ROB
            "subs x14, x14, #1\n\t"
            "b.ne 1b\n\t"
            "mov %[v], x9\n\t"
            : [n] "+r"(count), [v] "=r"(value)
            :
            : "x9", "x14", "cc", "memory");
        break;
      case SAD_LSQ:
        __asm__ volatile(
            "mov x9, #0\n\t"
            "mov x14, %[n]\n\t"
            "1:\n\t" BODY_LSQ
            "subs x14, x14, #1\n\t"
            "b.ne 1b\n\t"
            "mov %[v], x9\n\t"
            : [n] "+r"(count), [v] "=r"(value)
            : [buf] "r"(buffer)
            : "x9", "x14", "cc", "memory");
        break;
      case SAD_PRF:
        __asm__ volatile(
            "mov x9, #0\n\t"
            "mov x10, #7\n\t"
            "mov x11, #0\n\t"
            "mov x12, #0\n\t"
            "mov x13, #0\n\t"
            "mov x14, %[n]\n\t"
            "1:\n\t" BODY_PRF
            "subs x14, x14, #1\n\t"
            "b.ne 1b\n\t"
            "add %[v], x9, x11\n\t"
            : [n] "+r"(count), [v] "=r"(value)
            :
            : "x9", "x10", "x11", "x12", "x13", "x14", "cc", "memory");
        break;
      default:
        return 2;
    }
    if (!no_markers)
        m5_work_end(7, 0);

    int pass = 0;
    switch (mode) {
      case SAD_NOP:
        pass = value == 0;
        break;
      case SAD_ROB:
        pass = value == iterations * 64;
        break;
      case SAD_LSQ:
        /* Every iteration reloads data[0]; data[1] receives the same value. */
        pass = value == data[0] && data[1] == data[0];
        break;
      case SAD_PRF:
        /* Every group rewrites the same destinations: x9 = 8, x11 = 9. */
        pass = value == 17;
        break;
      default:
        break;
    }
    printf("sad mode=%s iterations=%llu result=%llu status=%s\n",
           argv[1], (unsigned long long)iterations,
           (unsigned long long)value, pass ? "PASS" : "FAIL");
    return pass ? 0 : 1;
}
