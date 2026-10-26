/* workloads/litmus/litmus_atomic.c — W7 litmus: LDXR/STXR atomicity (CAS counter).
 *
 *   P0 (cpu0): N 次 { ldxr; add 1; stxr }  重试直到成功
 *   P1 (cpu1): N 次 { ldxr; add 1; stxr }  重试直到成功
 *   禁出现结果: 最终计数 != 2N（丢失更新 = 原子性被破坏 = SDC）
 *
 * 为什么这条测试是 O01/O02/O03 的判别载体（规格 §6 W7 明列
 * "LDXR/STXR 竞争 / CAS counter"）：
 *   * O01 腐蚀 exclusive monitor 的保留地址、O02 腐蚀 monitor 的
 *     valid/version/granule —— 都会让**本不应失败的 STXR 失败**，
 *     被重试环吸收 => 数据面不变，只有重试次数上升 => Masked（不是伪 SDC）。
 *   * 反过来，若 STXR 在保留已失效时**错误地成功**（O03 状态码翻转、
 *     O01/O02 的另一种取值），就会造成丢失更新 => 最终计数 < 2N => SDC。
 *   所以本测试同时给出两个可观测量：数据面（禁出现结果）与重试面（tries）。
 *   只报数据面的实现会把"重试吸收"错判成"没发生故障"，所以 tries 必须报。
 */
#include "litmus_common.h"

#ifndef LITMUS_ATOM_INCR
#define LITMUS_ATOM_INCR 8      /* 每轮每核的自增次数（gem5 FS 预算） */
#endif
#ifndef LITMUS_ATOM_ROUNDS
#define LITMUS_ATOM_ROUNDS 400  /* fork 一次，循环 AR 轮 —— 见 common 头第 2 条 */
#endif

struct atom_sh {
    volatile unsigned long ctr;
    volatile unsigned long go;
    volatile unsigned long done0, done1;
    volatile unsigned long tries0, tries1;
};

int main(void)
{
    long ncpu = litmus_ncpus();
    struct atom_sh *s = mmap(NULL, sizeof *s, PROT_READ | PROT_WRITE,
                             MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (s == MAP_FAILED) { perror("mmap"); return 2; }

    printf("LITMUS atomic nproc=%ld rounds=%d incr_per_core=%d\n",
           ncpu, LITMUS_ATOM_ROUNDS, LITMUS_ATOM_INCR);
    fflush(stdout);
    if (ncpu < 2) {
        printf("LITMUS atomic ABORT: nproc=%ld < 2 — this litmus needs two "
               "runnable CPUs\n", ncpu);
        return 4;
    }

    /* 子进程 0/1 共享同一段循环体；pin/cpu/写回槽位由参数区分。 */
    pid_t p0 = fork();
    if (p0 == 0) {
        if (litmus_pin(0) != 0) { perror("pin cpu0"); _exit(3); }
        unsigned long long tries = 0;
        for (unsigned long r = 1; r <= (unsigned long)LITMUS_ATOM_ROUNDS; ++r) {
            while (__atomic_load_n(&s->go, __ATOMIC_ACQUIRE) != r) { }
            for (int i = 0; i < LITMUS_ATOM_INCR; ++i) {
                unsigned long tmp;
                unsigned int st;
                do {
                    __asm__ volatile("ldxr %0, [%1]" : "=r"(tmp) : "r"(&s->ctr));
                    tmp += 1;
                    __asm__ volatile("stxr %w0, %1, [%2]"
                                     : "=&r"(st) : "r"(tmp), "r"(&s->ctr));
                    ++tries;
                } while (st != 0);
            }
            __atomic_store_n(&s->tries0, tries, __ATOMIC_RELEASE);
            __atomic_store_n(&s->done0, r, __ATOMIC_RELEASE);
        }
        _exit(0);
    }

    pid_t p1 = fork();
    if (p1 == 0) {
        if (litmus_pin(1) != 0) { perror("pin cpu1"); _exit(3); }
        unsigned long long tries = 0;
        for (unsigned long r = 1; r <= (unsigned long)LITMUS_ATOM_ROUNDS; ++r) {
            while (__atomic_load_n(&s->go, __ATOMIC_ACQUIRE) != r) { }
            for (int i = 0; i < LITMUS_ATOM_INCR; ++i) {
                unsigned long tmp;
                unsigned int st;
                do {
                    __asm__ volatile("ldxr %0, [%1]" : "=r"(tmp) : "r"(&s->ctr));
                    tmp += 1;
                    __asm__ volatile("stxr %w0, %1, [%2]"
                                     : "=&r"(st) : "r"(tmp), "r"(&s->ctr));
                    ++tries;
                } while (st != 0);
            }
            __atomic_store_n(&s->tries1, tries, __ATOMIC_RELEASE);
            __atomic_store_n(&s->done1, r, __ATOMIC_RELEASE);
        }
        _exit(0);
    }

    if (p0 < 0 || p1 < 0) { perror("fork"); return 2; }

    const unsigned long expect = 2UL * LITMUS_ATOM_INCR;
    unsigned long long viol = 0;
    for (unsigned long r = 1; r <= (unsigned long)LITMUS_ATOM_ROUNDS; ++r) {
        s->ctr = 0;
        litmus_dmb();
        __atomic_store_n(&s->go, r, __ATOMIC_RELEASE);
        while (__atomic_load_n(&s->done0, __ATOMIC_ACQUIRE) != r) { }
        while (__atomic_load_n(&s->done1, __ATOMIC_ACQUIRE) != r) { }
        litmus_dmb();
        if (s->ctr != expect) ++viol;
    }

    unsigned long long t0 = s->tries0, t1 = s->tries1;
    long ncpu_after = litmus_ncpus();
    printf("LITMUS atomic ctr_expect=%lu violations=%llu tries cpu0=%llu "
           "cpu1=%llu (min=%d) nproc_after=%ld\n",
           expect, viol, t0, t1, LITMUS_ATOM_INCR, ncpu_after);
    fflush(stdout);

    int w0 = 0, w1 = 0;
    waitpid(p0, &w0, 0);
    waitpid(p1, &w1, 0);
    litmus_final("atomic", viol, (unsigned long long)LITMUS_ATOM_ROUNDS);
    printf("LITMUS atomic children status p0=%d p1=%d\n", w0, w1);
    return (w0 == 0 && w1 == 0) ? 0 : 6;
}
