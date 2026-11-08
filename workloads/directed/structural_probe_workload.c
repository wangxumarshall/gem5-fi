/* Structural activation probes for AutoµSens structure mapping.
 *
 * Each mode executes one AArch64 instruction kind inside an m5 work-item
 * window, so RF/L1/FU counters can be attributed to that instruction after
 * subtracting the empty-loop baseline. Prologue, verification and output stay
 * outside the measured window.
 *
 * Usage: structural_probe_workload <mode> <iterations>
 *
 * Every mode prints "stream=<mode> ... status=PASS|FAIL". FAIL (exit 1) means
 * the probe stream did not compute what the C reference says it must; a probe
 * that silently mis-executes would poison the structure map.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gem5/m5ops.h>

#if !defined(__aarch64__)
#error "structural probes require AArch64"
#endif

/* 16 groups of 4 instructions per loop iteration. */
#define GROUPS_PER_ITER 16
#define OPS_PER_GROUP 4

/* One hot line: load probes hit the same line, store probes dirty it. */
static uint64_t data[64] __attribute__((aligned(64))) = {
    [0] = 0x0123456789abcdefULL,
};

static volatile uint64_t *const hot = data;

/* The four-instruction group repeats the same op, so the group semantics are
 * simply "apply OP four times in program order" and the reference mirrors it
 * without modelling scheduling. */
#define RUN_STREAM(INSTR, SETUP)                                             \
    __asm__ volatile(                                                        \
        SETUP                                                               \
        "1:\n\t"                                                            \
        ".rept " STR(GROUPS_PER_ITER) "\n\t"                                \
        INSTR "\n\t" INSTR "\n\t" INSTR "\n\t" INSTR "\n\t"                 \
        ".endr\n\t"                                                         \
        "subs %[n], %[n], #1\n\t"                                           \
        "b.ne 1b\n\t"                                                       \
        "mov %[v], x8\n\t"                                                  \
        : [n] "+r"(count), [v] "=r"(value)                                   \
        : [buf] "r"(buffer)                                                  \
        : "x8", "x10", "x12", "cc", "memory")

#define STR_(x) #x
#define STR(x) STR_(x)

enum probe_mode {
    PROBE_BASELINE,
    PROBE_ADD,
    PROBE_SUB,
    PROBE_AND,
    PROBE_ORR,
    PROBE_EOR,
    PROBE_MUL,
    PROBE_MADD,
    PROBE_UDIV,
    PROBE_LDR,
    PROBE_STR,
    PROBE_LDXR,
    PROBE_COUNT,
};

static const char *
mode_name(enum probe_mode mode)
{
    static const char *const names[PROBE_COUNT] = {
        "baseline", "add", "sub", "and", "orr", "eor",
        "mul", "madd", "udiv", "ldr", "str", "ldxr",
    };
    return names[mode];
}

static int
parse_mode(const char *name, enum probe_mode *mode)
{
    for (int i = 0; i < PROBE_COUNT; ++i) {
        if (strcmp(name, mode_name((enum probe_mode)i)) == 0) {
            *mode = (enum probe_mode)i;
            return 0;
        }
    }
    return -1;
}

/* Reference for the four sequential applications of the ALU op per group.
 * x12 supplies the second operand; x10 supplies the addend for madd. */
static uint64_t
ref_alu(enum probe_mode mode, uint64_t groups, uint64_t x8, uint64_t x12,
        uint64_t x10)
{
    for (uint64_t group = 0; group < groups; ++group) {
        for (int op = 0; op < OPS_PER_GROUP; ++op) {
            switch (mode) {
              case PROBE_ADD: x8 += x12; break;
              case PROBE_SUB: x8 -= x12; break;
              case PROBE_AND: x8 &= x12; break;
              case PROBE_ORR: x8 |= x12; break;
              case PROBE_EOR: x8 ^= x12; break;
              case PROBE_MUL: x8 *= x12; break;
              case PROBE_MADD: x8 = x8 * x12 + x10; break;
              case PROBE_UDIV: x8 /= x12; break;
              default: return 0;
            }
        }
    }
    return x8;
}

/* Per-mode operand setup. The value kept in x8 is the reference input.
 * Setup strings must be literals: the asm volatile body is string-encoded at
 * compile time. */
#define ASM_SETUP_1        "mov x8, #1\n\t"
#define ASM_SETUP_ADD      "mov x8, #1\n\tmov x12, #3\n\t"
#define ASM_SETUP_SUB      "mov x8, #1\n\tmov x12, #3\n\t"
#define ASM_SETUP_AND      "mov x8, #0xff\n\tmov x12, #0x0f\n\t"
#define ASM_SETUP_ORR      "mov x8, #0xf0\n\tmov x12, #0x0f\n\t"
#define ASM_SETUP_EOR      "mov x8, #0xff\n\tmov x12, #0x0f\n\t"
#define ASM_SETUP_MUL      "mov x8, #3\n\tmov x12, #3\n\t"
#define ASM_SETUP_MADD     "mov x8, #3\n\tmov x12, #3\n\tmov x10, #5\n\t"
#define ASM_SETUP_UDIV     "mov x8, #0x100\n\tmov x12, #2\n\t"

struct operand_setup
{
    uint64_t x8;
    uint64_t x12;
    uint64_t x10;
};

static const struct operand_setup setups[PROBE_COUNT] = {
    [PROBE_BASELINE] = {1, 1, 1},
    [PROBE_ADD] = {1, 3, 1},
    [PROBE_SUB] = {1, 3, 1},
    [PROBE_AND] = {0xff, 0x0f, 1},
    [PROBE_ORR] = {0xf0, 0x0f, 1},
    [PROBE_EOR] = {0xff, 0x0f, 1},
    [PROBE_MUL] = {3, 3, 1},
    [PROBE_MADD] = {3, 3, 5},
    [PROBE_UDIV] = {0x100, 2, 1},
    [PROBE_LDR] = {1, 1, 1},
    [PROBE_STR] = {1, 1, 1},
    [PROBE_LDXR] = {1, 1, 1},
};

int
main(int argc, char **argv)
{
    if (argc != 3)
        return 2;
    enum probe_mode mode;
    if (parse_mode(argv[1], &mode) != 0)
        return 2;
    const uint64_t iterations = strtoull(argv[2], NULL, 0);
    if (!iterations || iterations > 1000000)
        return 2;
    const struct operand_setup *setup = &setups[mode];
    uint64_t *buffer = data;
    uint64_t count = iterations, value = 0;
    const uint64_t groups = GROUPS_PER_ITER * iterations;

    m5_work_begin(7, 0);
    switch (mode) {
      case PROBE_BASELINE:
        RUN_STREAM("nop", ASM_SETUP_1);
        break;
      case PROBE_ADD:
        RUN_STREAM("add x8, x8, x12", ASM_SETUP_ADD);
        break;
      case PROBE_SUB:
        RUN_STREAM("sub x8, x8, x12", ASM_SETUP_SUB);
        break;
      case PROBE_AND:
        RUN_STREAM("and x8, x8, x12", ASM_SETUP_AND);
        break;
      case PROBE_ORR:
        RUN_STREAM("orr x8, x8, x12", ASM_SETUP_ORR);
        break;
      case PROBE_EOR:
        RUN_STREAM("eor x8, x8, x12", ASM_SETUP_EOR);
        break;
      case PROBE_MUL:
        RUN_STREAM("mul x8, x8, x12", ASM_SETUP_MUL);
        break;
      case PROBE_MADD:
        RUN_STREAM("madd x8, x8, x12, x10", ASM_SETUP_MADD);
        break;
      case PROBE_UDIV:
        RUN_STREAM("udiv x8, x8, x12", ASM_SETUP_UDIV);
        break;
      case PROBE_LDR:
        RUN_STREAM("ldr x8, [%[buf]]", ASM_SETUP_1);
        break;
      case PROBE_STR:
        RUN_STREAM("str x8, [%[buf]]", ASM_SETUP_1);
        break;
      case PROBE_LDXR:
        RUN_STREAM("ldxr x8, [%[buf]]", ASM_SETUP_1);
        break;
      default:
        return 2;
    }
    m5_work_end(7, 0);

    int pass = 1;
    switch (mode) {
      case PROBE_BASELINE:
        /* nop leaves x8 at its setup value; nothing else may change. */
        pass = value == setup->x8;
        break;
      case PROBE_LDR:
        pass = value == *hot;
        break;
      case PROBE_LDXR:
        pass = value == *hot;
        break;
      case PROBE_STR:
        /* Every store wrote the setup value of x8 to data[0]. */
        pass = *hot == setup->x8;
        break;
      default:
        pass = value == ref_alu(mode, groups, setup->x8, setup->x12,
                                setup->x10);
        break;
    }
    printf("stream=%s iterations=%llu groups=%llu result=%llu status=%s\n",
           argv[1], (unsigned long long)iterations,
           (unsigned long long)groups, (unsigned long long)value,
           pass ? "PASS" : "FAIL");
    return pass ? 0 : 1;
}
