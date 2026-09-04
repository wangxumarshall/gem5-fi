/* spinlock_kernel — §2.4 CHAOSExMon 验证 kernel.
 *
 * 用 inline asm 执行 LDXR/STXR 自旋锁自检：尝试 acquire 一个 lock
 * (LDXR + STXR 循环)，统计 acquire 成功/失败次数。在无注入时，
 * STXR 应总是成功（单核无竞争）；CHAOSExMon stxr_force_fail 注入后
 * 应出现 STXR 失败（lock 获取失败次数增加）。输出 16-hex checksum。
 *
 * Build: gcc -static -O0 -o spinlock_kernel spinlock_kernel.c
 * (用 -O0 防 inline asm 被优化掉)
 */
#include <stdio.h>
#include <stdint.h>

static inline int ldaxr_stxr_acquire(volatile uint32_t *lock, uint32_t *old) {
    uint32_t tmp;
    __asm__ volatile (
        "1: ldaxr %w0, [%2]\n"       /* LDXR (acquire) old value */
        "   cbnz  %w0, 2f\n"         /* if nonzero, lock held, fail */
        "   stxr  %w1, %w3, [%2]\n"   /* STXR: try store 1 (acquire) */
        "   cbnz  %w1, 1b\n"         /* if STXR failed (rare in single-core),
                                       retry */
        "   b 3f\n"
        "2: mov %w1, #1\n"           /* mark as fail (lock held) */
        "3:\n"
        : "=&r"(*old), "=&r"(tmp)
        : "r"(lock), "r"(1)
        : "memory");
    return (tmp == 0) ? 0 : 1;  /* 0 = acquired, 1 = failed */
}

int main(void) {
    volatile uint32_t lock = 0;
    int acquires = 0, fails = 0;
    uint32_t old;
    for (int i = 0; i < 100; i++) {
        /* limit retries to 10 to avoid infinite spin under ExMon injection */
        int retries = 0;
        int result;
        while ((result = ldaxr_stxr_acquire(&lock, &old)) != 0 && retries < 10) {
            fails++;
            retries++;
            lock = 0;  /* reset lock (under injection, STXR may fail spuriously) */
        }
        if (result == 0) {
            acquires++;
            lock = 0;  /* release */
        }
    }
    /* FNV-1a checksum of acquires + fails */
    uint64_t cs = 0xcbf29ce484222325ULL;
    cs ^= (uint64_t)acquires; cs *= 0x100000001b3ULL;
    cs ^= (uint64_t)fails; cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs);
    fprintf(stderr, "acquires=%d fails=%d\n", acquires, fails);
    return 0;
}
