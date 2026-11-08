/* AArch64 input width and FU utilization streams, isolated by m5 markers. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <gem5/m5ops.h>

#if !defined(__aarch64__)
#error "IBR directed workload requires AArch64"
#endif

#define RUN_STREAM(OP, WIDTH, PADDING) \
    __asm__ volatile( \
        "mov x8, #1\n\t" "mov x9, #1\n\t" \
        "mov x10, #1\n\t" "mov x11, #1\n\t" \
        "mov x12, #1\n\t" "mov x13, #1\n\t" \
        "1:\n\t" \
        ".rept 16\n\t" \
        OP " " WIDTH "8, " WIDTH "8, " WIDTH "12\n\t" \
        OP " " WIDTH "9, " WIDTH "9, " WIDTH "13\n\t" \
        OP " " WIDTH "10, " WIDTH "10, " WIDTH "12\n\t" \
        OP " " WIDTH "11, " WIDTH "11, " WIDTH "13\n\t" \
        PADDING \
        ".endr\n\t" \
        "subs %[n], %[n], #1\n\t" "b.ne 1b\n\t" \
        "mov %[v], x8\n\t" \
        : [n] "+r" (count), [v] "=r" (value) \
        : : "x8", "x9", "x10", "x11", "x12", "x13", "cc")

int main(int argc, char **argv)
{
    if (argc != 3 && argc != 4)
        return 2;
    const int no_markers = argc == 4 && strcmp(argv[3], "no-markers") == 0;
    const int mismatched_end =
        argc == 4 && strcmp(argv[3], "mismatched-end") == 0;
    if (argc == 4 && !no_markers && !mismatched_end)
        return 2;
    const uint64_t iterations = strtoull(argv[2], NULL, 0);
    if (!iterations || iterations > 1000000)
        return 2;
    int mode = -1;
    const char *names[] = {"alu64", "alu32", "mul64", "mul32", "div64",
                           "sparse"};
    for (int i = 0; i < 6; ++i)
        if (strcmp(argv[1], names[i]) == 0)
            mode = i;
    if (mode < 0)
        return 2;
    uint64_t count = iterations, value = 0;
    if (!no_markers)
        m5_work_begin(7, 0);
    if (mismatched_end)
        m5_work_end(99, 0);
    switch (mode) {
      case 0: RUN_STREAM("add", "x", ""); break;
      case 1: RUN_STREAM("add", "w", ""); break;
      case 2: RUN_STREAM("mul", "x", ""); break;
      case 3: RUN_STREAM("mul", "w", ""); break;
      case 4: RUN_STREAM("udiv", "x", ""); break;
      case 5: RUN_STREAM("add", "x", ".rept 8\n\tnop\n\t.endr\n\t"); break;
    }
    if (!no_markers)
        m5_work_end(7, 0);
    const uint64_t expected = mode < 2 || mode == 5 ? 1 + 16 * iterations : 1;
    printf("stream=%s iterations=%llu result=%llu expected=%llu status=%s\n",
           argv[1], (unsigned long long)iterations,
           (unsigned long long)value, (unsigned long long)expected,
           value == expected ? "PASS" : "FAIL");
    return value == expected ? 0 : 1;
}
