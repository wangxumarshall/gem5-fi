/* workloads/litmus/litmus_sb.c — W7 litmus: Store-Buffering (SB).
 *
 *   P0: x=1 ; dmb ish ; r0=y
 *   P1: y=1 ; dmb ish ; r1=x
 *   禁出现结果: r0==0 && r1==0
 *
 * 两条 dmb ish 使弱结果在 ARM 架构模型下非法，所以"禁出现结果"计数必须为
 * 0；非 0 = 硬件可见违例（或注入导致的可见违例）。读/写 0 的偷懒实现会
 * 让本测试变成恒真的空测试 —— 见 litmus_common.h 文件头第 4 条。
 */
#include "litmus_common.h"

struct sb_sh {
    volatile unsigned long x, y, r0, r1;
    volatile unsigned long go;
    volatile unsigned long done0, done1;
};

int main(void)
{
    long ncpu = litmus_ncpus();
    struct sb_sh *s = mmap(NULL, sizeof *s, PROT_READ | PROT_WRITE,
                           MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (s == MAP_FAILED) { perror("mmap"); return 2; }

    printf("LITMUS sb nproc=%ld rounds=%d\n", ncpu, LITMUS_ROUNDS);
    fflush(stdout);
    if (ncpu < 2) {
        /* 不是"跳过"，而是明确报错：单核跑 litmus 没有得到任何东西。 */
        printf("LITMUS sb ABORT: nproc=%ld < 2 — this litmus needs two "
               "runnable CPUs\n", ncpu);
        return 4;
    }

    pid_t p0 = fork();
    if (p0 == 0) {
        if (litmus_pin(0) != 0) { perror("pin cpu0"); _exit(3); }
        for (unsigned long r = 1; r <= (unsigned long)LITMUS_ROUNDS; ++r) {
            while (__atomic_load_n(&s->go, __ATOMIC_ACQUIRE) != r) { }
            s->x = 1;
            litmus_dmb();
            s->r0 = s->y;
            __atomic_store_n(&s->done0, r, __ATOMIC_RELEASE);
        }
        _exit(0);
    }

    pid_t p1 = fork();
    if (p1 == 0) {
        if (litmus_pin(1) != 0) { perror("pin cpu1"); _exit(3); }
        for (unsigned long r = 1; r <= (unsigned long)LITMUS_ROUNDS; ++r) {
            while (__atomic_load_n(&s->go, __ATOMIC_ACQUIRE) != r) { }
            s->y = 1;
            litmus_dmb();
            s->r1 = s->x;
            __atomic_store_n(&s->done1, r, __ATOMIC_RELEASE);
        }
        _exit(0);
    }

    if (p0 < 0 || p1 < 0) { perror("fork"); return 2; }

    unsigned long long n00 = 0, n01 = 0, n10 = 0, n11 = 0;
    for (unsigned long r = 1; r <= (unsigned long)LITMUS_ROUNDS; ++r) {
        s->x = 0; s->y = 0; s->r0 = 0; s->r1 = 0;
        litmus_dmb();
        __atomic_store_n(&s->go, r, __ATOMIC_RELEASE);
        while (__atomic_load_n(&s->done0, __ATOMIC_ACQUIRE) != r) { }
        while (__atomic_load_n(&s->done1, __ATOMIC_ACQUIRE) != r) { }
        litmus_dmb();
        unsigned long a = s->r0, b = s->r1;
        if (a == 0 && b == 0) ++n00;
        else if (a == 0 && b == 1) ++n01;
        else if (a == 1 && b == 0) ++n10;
        else if (a == 1 && b == 1) ++n11;
        else { printf("LITMUS sb BAD r0=%lu r1=%lu at round %lu\n", a, b, r); return 5; }
    }

    printf("LITMUS sb hist r0r1: 00=%llu 01=%llu 10=%llu 11=%llu "
           "forbidden(00)=%llu\n", n00, n01, n10, n11, n00);
    fflush(stdout);

    int w0 = 0, w1 = 0;
    waitpid(p0, &w0, 0);
    waitpid(p1, &w1, 0);
    litmus_final("sb", n00, (unsigned long long)LITMUS_ROUNDS);
    printf("LITMUS sb children status p0=%d p1=%d\n", w0, w1);
    return (w0 == 0 && w1 == 0) ? 0 : 6;
}
