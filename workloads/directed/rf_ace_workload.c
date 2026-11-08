/* Directed RF ACE streams. The m5 work item excludes argument parsing and
 * output from the measured region. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gem5/m5ops.h>

static volatile uint64_t branch_condition = 1;
static volatile uint64_t sink;

static uint64_t
dependency_chain(uint64_t iterations)
{
    uint64_t value = 0x123456789abcdef0ULL;
    for (uint64_t i = 0; i < iterations; ++i) {
#if defined(__aarch64__)
        const uint64_t mask = 0x5a5a;
        const uint64_t multiplier = 3;
        __asm__ volatile(
            "add %x[v], %x[v], #17\n\t"
            "ror %x[v], %x[v], #57\n\t"
            "eor %x[v], %x[v], %x[mask]\n\t"
            "mul %x[v], %x[v], %x[multiplier]\n\t"
            : [v] "+r" (value)
            : [mask] "r" (mask), [multiplier] "r" (multiplier)
            : "cc");
#elif defined(__x86_64__)
        __asm__ volatile(
            "addq $17, %[v]\n\t"
            "rolq $7, %[v]\n\t"
            "xorq $0x5a5a, %[v]\n\t"
            "imulq $3, %[v], %[v]\n\t"
            : [v] "+r" (value)
            :
            : "cc");
#else
#error "RF ACE directed workload supports AArch64 and x86-64"
#endif
    }
    return value;
}

static uint64_t
dead_writes(uint64_t iterations)
{
    for (uint64_t i = 0; i < iterations; ++i) {
#if defined(__aarch64__)
        __asm__ volatile(
            "mov x8, #1\n\t"
            "mov x9, #2\n\t"
            "mov x10, #3\n\t"
            "mov x11, #4\n\t"
            :
            :
            : "x8", "x9", "x10", "x11");
#else
        __asm__ volatile(
            "movq $1, %%r8\n\t"
            "movq $2, %%r9\n\t"
            "movq $3, %%r10\n\t"
            "movq $4, %%r11\n\t"
            :
            :
            : "r8", "r9", "r10", "r11");
#endif
    }
    return iterations;
}

static uint64_t
register_pressure(uint64_t iterations)
{
    for (uint64_t i = 0; i < iterations; ++i) {
#if defined(__aarch64__)
        __asm__ volatile(
            "mov x8, #1\n\t"
            "mov x9, #2\n\t"
            "mov x10, #3\n\t"
            "mov x11, #4\n\t"
            "mov x12, #5\n\t"
            "mov x13, #6\n\t"
            "mov x14, #7\n\t"
            "mov x15, #8\n\t"
            :
            :
            : "x8", "x9", "x10", "x11", "x12", "x13", "x14", "x15");
#else
        __asm__ volatile(
            "movq $1, %%r8\n\t"
            "movq $2, %%r9\n\t"
            "movq $3, %%r10\n\t"
            "movq $4, %%r11\n\t"
            "movq $5, %%r12\n\t"
            "movq $6, %%r13\n\t"
            "movq $7, %%r14\n\t"
            "movq $8, %%r15\n\t"
            :
            :
            : "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15");
#endif
    }
    return iterations;
}

static uint64_t
operand_width_32(uint64_t iterations)
{
    uint32_t value = 0x12345678U;
    const uint32_t delta = 0x10203U;
    const uint32_t mask = 0x5a5aU;
    for (uint64_t i = 0; i < iterations; ++i) {
#if defined(__aarch64__)
        __asm__ volatile(
            "add %w[v], %w[v], %w[delta]\n\t"
            "eor %w[v], %w[v], %w[mask]\n\t"
            "ror %w[v], %w[v], #25\n\t"
            : [v] "+r" (value)
            : [delta] "r" (delta), [mask] "r" (mask)
            : "cc");
#elif defined(__x86_64__)
        __asm__ volatile(
            "addl %[delta], %[v]\n\t"
            "xorl %[mask], %[v]\n\t"
            "roll $7, %[v]\n\t"
            : [v] "+r" (value)
            : [delta] "r" (delta), [mask] "r" (mask)
            : "cc");
#endif
    }
    return value;
}

static uint64_t
operand_width_64(uint64_t iterations)
{
    uint64_t value = 0x12345678ULL;
    const uint64_t delta = 0x10203ULL;
    const uint64_t mask = 0x5a5aULL;
    for (uint64_t i = 0; i < iterations; ++i) {
#if defined(__aarch64__)
        __asm__ volatile(
            "add %x[v], %x[v], %x[delta]\n\t"
            "eor %x[v], %x[v], %x[mask]\n\t"
            "ror %x[v], %x[v], #57\n\t"
            : [v] "+r" (value)
            : [delta] "r" (delta), [mask] "r" (mask)
            : "cc");
#elif defined(__x86_64__)
        __asm__ volatile(
            "addq %[delta], %[v]\n\t"
            "xorq %[mask], %[v]\n\t"
            "rolq $7, %[v]\n\t"
            : [v] "+r" (value)
            : [delta] "r" (delta), [mask] "r" (mask)
            : "cc");
#endif
    }
    return value;
}

static uint64_t
squashed_writes(uint64_t iterations)
{
    uint64_t result = 0;
    for (uint64_t i = 0; i < iterations; ++i) {
        /* Train not-taken, then delay the actual taken-branch resolution.
         * Independent fall-through writes can execute before the branch
         * resolves and must subsequently be discarded by RF ACE. */
        branch_condition = 0;
        for (unsigned train = 0; train < 8; ++train) {
            if (branch_condition)
                result += train;
        }
        branch_condition = 1;
#if defined(__aarch64__)
        __asm__ volatile(
            "ldr x0, [%[condition]]\n\t"
            "mov x1, #1\n\t"
            ".rept 8\n\t"
            "udiv x0, x0, x1\n\t"
            ".endr\n\t"
            "cbnz x0, 1f\n\t"
            ".rept 48\n\t"
            "add x8, x8, #1\n\t"
            "add x9, x9, #3\n\t"
            "eor x10, x10, x8\n\t"
            "ror x11, x11, #63\n\t"
            ".endr\n\t"
            "1:\n\t"
            :
            : [condition] "r" (&branch_condition)
            : "x0", "x1", "x8", "x9", "x10", "x11", "cc", "memory");
#else
        __asm__ volatile("clflush (%0)" : : "r" (&branch_condition) : "memory");
        __asm__ volatile("mfence" : : : "memory");
        __asm__ volatile(
            "movq (%[condition]), %%rax\n\t"
            "testq %%rax, %%rax\n\t"
            "jnz 1f\n\t"
            ".rept 48\n\t"
            "addq $1, %%r8\n\t"
            "addq $3, %%r9\n\t"
            "xorq %%r8, %%r10\n\t"
            "rolq $1, %%r11\n\t"
            ".endr\n\t"
            "1:\n\t"
            :
            : [condition] "r" (&branch_condition)
            : "rax", "r8", "r9", "r10", "r11", "cc", "memory");
#endif
        result += branch_condition;
    }
    return result;
}

static uint64_t
rotate_left(uint64_t value, unsigned shift)
{
    return (value << shift) | (value >> (64 - shift));
}

static uint32_t
rotate_left_32(uint32_t value, unsigned shift)
{
    return (value << shift) | (value >> (32 - shift));
}

static uint64_t
expected_result(const char *stream, uint64_t iterations)
{
    if (strcmp(stream, "chain") == 0) {
        uint64_t value = 0x123456789abcdef0ULL;
        for (uint64_t i = 0; i < iterations; ++i) {
            value += 17;
            value = rotate_left(value, 7);
            value ^= 0x5a5a;
            value *= 3;
        }
        return value;
    }
    if (strcmp(stream, "width32") == 0) {
        uint32_t value = 0x12345678U;
        for (uint64_t i = 0; i < iterations; ++i) {
            value += 0x10203U;
            value ^= 0x5a5aU;
            value = rotate_left_32(value, 7);
        }
        return value;
    }
    if (strcmp(stream, "width64") == 0) {
        uint64_t value = 0x12345678ULL;
        for (uint64_t i = 0; i < iterations; ++i) {
            value += 0x10203ULL;
            value ^= 0x5a5aULL;
            value = rotate_left(value, 7);
        }
        return value;
    }
    return iterations;
}

int
main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s chain|dead|pressure|squash|width32|"
                "width64 iterations\n", argv[0]);
        return 2;
    }

    const uint64_t iterations = strtoull(argv[2], NULL, 0);
    uint64_t result = 0;

    m5_work_begin(7, 0);
    if (strcmp(argv[1], "chain") == 0) {
        result = dependency_chain(iterations);
    } else if (strcmp(argv[1], "dead") == 0) {
        result = dead_writes(iterations);
    } else if (strcmp(argv[1], "pressure") == 0) {
        result = register_pressure(iterations);
    } else if (strcmp(argv[1], "width32") == 0) {
        result = operand_width_32(iterations);
    } else if (strcmp(argv[1], "width64") == 0) {
        result = operand_width_64(iterations);
    } else if (strcmp(argv[1], "squash") == 0) {
        result = squashed_writes(iterations);
    } else {
        m5_work_end(7, 0);
        fprintf(stderr, "unknown stream: %s\n", argv[1]);
        return 2;
    }
    m5_work_end(7, 0);

    const uint64_t expected = expected_result(argv[1], iterations);
    sink = result;
    printf("stream=%s iterations=%llu result=%016llx expected=%016llx "
           "status=%s\n",
           argv[1], (unsigned long long)iterations,
           (unsigned long long)result, (unsigned long long)expected,
           result == expected ? "PASS" : "FAIL");
    return result == expected ? 0 : 1;
}
