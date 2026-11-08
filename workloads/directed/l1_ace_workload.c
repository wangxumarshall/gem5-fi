/* Directed L1 cache ACE streams. Initialization and output are outside the
 * measured m5 work-item region. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gem5/m5ops.h>

#define HOT_WORDS (32 * 1024 / sizeof(uint64_t))
#define STREAM_WORDS (8 * 1024 * 1024 / sizeof(uint64_t))
#define CACHE_WORDS (64 * 1024 / sizeof(uint64_t))
#define CONFLICT_LINES 32
#define DATA_MULTIPLIER 0x9e3779b97f4a7c15ULL

static uint64_t data[STREAM_WORDS] __attribute__((aligned(64)));
static volatile uint64_t sink;

static uint64_t
read_reuse(uint64_t iterations)
{
    uint64_t result = 0;
    for (uint64_t pass = 0; pass < iterations; ++pass) {
        for (size_t index = 0; index < HOT_WORDS; ++index)
            result += *(volatile uint64_t *)&data[index];
    }
    return result;
}

static uint64_t
stream_read(uint64_t iterations)
{
    uint64_t result = 0;
    for (uint64_t pass = 0; pass < iterations; ++pass) {
        for (size_t index = 0; index < STREAM_WORDS; ++index)
            result += *(volatile uint64_t *)&data[index];
    }
    return result;
}

static uint64_t
dead_writes(uint64_t iterations)
{
    for (uint64_t pass = 0; pass < iterations; ++pass) {
        for (size_t index = 0; index < STREAM_WORDS; ++index)
            *(volatile uint64_t *)&data[index] = pass + index;
    }
    return iterations;
}

static uint64_t
set_pressure(uint64_t iterations)
{
    uint64_t result = 0;
    for (uint64_t pass = 0; pass < iterations; ++pass) {
        for (size_t line = 0; line < CONFLICT_LINES; ++line) {
            const size_t index = line * CACHE_WORDS;
            result += *(volatile uint64_t *)&data[index];
        }
    }
    return result;
}

static uint64_t
sum_indices(uint64_t count)
{
    if ((count & 1) == 0)
        return (count / 2) * (count - 1);
    return count * ((count - 1) / 2);
}

static uint64_t
expected_result(const char *stream, uint64_t iterations)
{
    if (strcmp(stream, "reuse") == 0)
        return iterations * DATA_MULTIPLIER * sum_indices(HOT_WORDS);
    if (strcmp(stream, "stream") == 0)
        return iterations * DATA_MULTIPLIER * sum_indices(STREAM_WORDS);
    if (strcmp(stream, "pressure") == 0) {
        return iterations * DATA_MULTIPLIER * CACHE_WORDS *
               sum_indices(CONFLICT_LINES);
    }
    return iterations;
}

int
main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr,
                "usage: %s reuse|dead|pressure|stream iterations\n", argv[0]);
        return 2;
    }

    const uint64_t iterations = strtoull(argv[2], NULL, 0);
    for (size_t index = 0; index < STREAM_WORDS; ++index)
        data[index] = index * DATA_MULTIPLIER;

    uint64_t result;
    m5_work_begin(11, 0);
    if (strcmp(argv[1], "reuse") == 0) {
        result = read_reuse(iterations);
    } else if (strcmp(argv[1], "stream") == 0) {
        result = stream_read(iterations);
    } else if (strcmp(argv[1], "dead") == 0) {
        result = dead_writes(iterations);
    } else if (strcmp(argv[1], "pressure") == 0) {
        result = set_pressure(iterations);
    } else {
        m5_work_end(11, 0);
        fprintf(stderr, "unknown stream: %s\n", argv[1]);
        return 2;
    }
    m5_work_end(11, 0);

    const uint64_t expected = expected_result(argv[1], iterations);
    sink = result;
    printf("stream=%s iterations=%llu result=%016llx expected=%016llx "
           "status=%s\n",
           argv[1], (unsigned long long)iterations,
           (unsigned long long)result, (unsigned long long)expected,
           result == expected ? "PASS" : "FAIL");
    return result == expected ? 0 : 1;
}
