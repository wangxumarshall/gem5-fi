/* workloads/litmus/litmus_mp.c — W7 litmus: Message-Passing (MP).
 *
 *   P0: x=1 ; dmb ish ; flag=1
 *   P1: while (flag==0) ; dmb ish ; r1=x
 *   禁出现结果: 看见 flag==1 却读到 x==0
 *
 * 这条测试是**跨核可见性**的判别式：只有在真一致性（Ruby/CHI）下 P1 才可能
 * 看到 flag；在无一致性的 classic 多核内存系统上 P1 会永远读不到 flag，
 * 于是本测试表现为 Timeout —— 这正是"classic 多核不可用于 litmus"的
 * 现场证据（见 R4-8-FSMC 报告）。所以本测试天然区分两种平台。
 *
 * O06（DMB/DSB barrier 完成）模型的观测点也在这里：barrier 提前/丢失完成
 * 会让 r1==0 的违例出现率上升。
 */
#include "litmus_common.h"

struct mp_sh {
    volatile unsigned long x, flag, r1, r0;
    volatile unsigned long go;
    volatile unsigned long done0, done1;
};

int main(void)
{
    long ncpu = litmus_ncpus();
    struct mp_sh *s = mmap(NULL, sizeof *s, PROT_READ | PROT_WRITE,
                           MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (s == MAP_FAILED) { perror("mmap"); return 2; }

    printf("LITMUS mp nproc=%ld rounds=%d\n", ncpu, LITMUS_ROUNDS);
    fflush(stdout);
    if (ncpu < 2) {
        printf("LITMUS mp ABORT: nproc=%ld < 2 — this litmus needs two "
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
            s->flag = 1;
            __atomic_store_n(&s->done0, r, __ATOMIC_RELEASE);
        }
        _exit(0);
    }

    pid_t p1 = fork();
    if (p1 == 0) {
        if (litmus_pin(1) != 0) { perror("pin cpu1"); _exit(3); }
        for (unsigned long r = 1; r <= (unsigned long)LITMUS_ROUNDS; ++r) {
            while (__atomic_load_n(&s->go, __ATOMIC_ACQUIRE) != r) { }
            while (s->flag == 0) { }       /* spin until P0 publishes */
            litmus_dmb();
            s->r1 = s->x;
            __atomic_store_n(&s->done1, r, __ATOMIC_RELEASE);
        }
        _exit(0);
    }

    if (p0 < 0 || p1 < 0) { perror("fork"); return 2; }

    unsigned long long viol = 0, ok = 0;
    for (unsigned long r = 1; r <= (unsigned long)LITMUS_ROUNDS; ++r) {
        s->x = 0; s->flag = 0; s->r1 = 0;
        litmus_dmb();
        __atomic_store_n(&s->go, r, __ATOMIC_RELEASE);
        while (__atomic_load_n(&s->done0, __ATOMIC_ACQUIRE) != r) { }
        while (__atomic_load_n(&s->done1, __ATOMIC_ACQUIRE) != r) { }
        litmus_dmb();
        if (s->r1 == 0) ++viol; else ++ok;
    }

    printf("LITMUS mp hist: saw_flag_x0(forbidden)=%llu saw_flag_x1=%llu\n",
           viol, ok);
    fflush(stdout);

    int w0 = 0, w1 = 0;
    waitpid(p0, &w0, 0);
    waitpid(p1, &w1, 0);
    litmus_final("mp", viol, (unsigned long long)LITMUS_ROUNDS);
    printf("LITMUS mp children status p0=%d p1=%d\n", w0, w1);
    return (w0 == 0 && w1 == 0) ? 0 : 6;
}
