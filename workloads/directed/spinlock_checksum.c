#include <stdio.h>
#include <stdint.h>
static uint64_t cs = 0xcbf29ce484222325ULL;
static inline int try_lock(volatile uint32_t *lock) {
    uint32_t tmp, old;
    __asm__ volatile (
        "ldaxr %w0, [%2]\n"
        "cbnz %w0, 2f\n"
        "stxr %w1, %w3, [%2]\n"
        "b 3f\n"
        "2: mov %w1, #1\n"
        "3:\n"
        : "=&r"(old), "=&r"(tmp)
        : "r"(lock), "r"(1)
        : "memory");
    return (tmp == 0) ? 0 : 1;
}
int main(void) {
    volatile uint32_t lock = 0;
    int acquires = 0, fails = 0;
    for (int i = 0; i < 100; i++) {
        int retries = 0;
        while (try_lock(&lock) != 0 && retries < 5) { fails++; retries++; lock = 0; }
        if (retries < 5) { acquires++; lock = 0; }
    }
    cs ^= (uint64_t)acquires; cs *= 0x100000001b3ULL;
    cs ^= (uint64_t)fails; cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs);
    return 0;
}
