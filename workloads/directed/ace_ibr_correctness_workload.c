/* Regressions for cache atomics and mixed-width integer RF operands. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <gem5/m5ops.h>

#if !defined(__aarch64__)
#error "This workload requires AArch64"
#endif

static uint64_t data __attribute__((aligned(64))) = 123;

#define LOOP(OP) \
    __asm__ volatile("mov x9, #4096\n1:\n" OP \
                     "subs x9, x9, #1\nb.ne 1b\nmov %0, x10\n" \
                     : "=&r"(result) : "r"(&data) \
                     : "x9", "x10", "x11", "x12", "x13", "cc", "memory")

#define MULTIPLY_LOOP(OP) \
    LOOP("mov x11, #2\nmov x12, #3\nmov x13, #5\n" OP)

int
main(int argc, char **argv)
{
    const char *names[] = {"ldr", "ldxr", "llsc", "failedsc", "swp",
                           "mixed", "wide", "boundary", "casfail", "cassame"};
    int mode = -1;
    if (argc != 2)
        return 2;
    for (int i = 0; i < 10; ++i)
        if (strcmp(argv[1], names[i]) == 0)
            mode = i;
    if (mode < 0)
        return 2;
    uint64_t result = 0;
    m5_work_begin(7, 123);
    switch (mode) {
      case 0: LOOP("ldr x10, [%1]\n"); break;
      case 1: LOOP("ldxr x10, [%1]\n"); break;
      case 2:
        LOOP("2: ldxr x10, [%1]\nadd x10, x10, #1\n"
             "stxr w11, x10, [%1]\ncbnz w11, 2b\n");
        break;
      case 3:
        LOOP("clrex\nmov x10, #1\nstxr w11, x10, [%1]\n"
             "mov x10, x11\n");
        break;
      case 4: LOOP("mov x12, #1\nswp x12, x10, [%1]\n"); break;
      case 5:
        MULTIPLY_LOOP("smaddl x10, w11, w12, x13\n"); break;
      case 6:
        MULTIPLY_LOOP("madd x10, x11, x12, x13\n"); break;
      case 7:
        // Keep an independent younger chain issuing while the work-end
        // marker waits for the older chain to retire at the ROB head.
        __asm__ volatile(
            "mov x0, #7\nmov x1, #123\nmov x10, #0\nmov x11, #0\n"
            ".rept 64\nadd x10, x10, #1\n.endr\n"
            ".balign 64\n"
            ".inst 0xff5b0110\n" // AArch64 m5_work_end
            ".rept 128\nadd x11, x11, #1\n.endr\nmov %0, x11\n"
            : "=r"(result) : : "x0", "x1", "x10", "x11", "memory");
        break;
      case 8:
        LOOP("mov x10, #0\nmov x12, #1\ncas x10, x12, [%1]\n");
        break;
      case 9:
        LOOP("mov x10, #123\nmov x12, #123\ncas x10, x12, [%1]\n");
        break;
    }
    if (mode != 7)
        m5_work_end(7, 123);
    const uint64_t expected = mode < 2 ? 123 : mode == 2 ? 4219 :
                              mode < 5 ? 1 : mode < 7 ? 11 : mode == 7 ? 128 : 123;
    printf("mode=%s result=%lu expected=%lu status=%s\n", argv[1], result,
           expected, result == expected ? "PASS" : "FAIL");
    return result != expected;
}
