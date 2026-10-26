/* workloads/litmus/litmus_common.h — W7 Atomic-Litmus 多核载体共享骨架。
 *
 * 用途（R4-8-FSMC）：MDSPEC §07 把 35 个 RunID 钉在 W7(Atomic-Litmus)/
 * W13(PARSEC) 上，理由是 "litmus needs multi-core FS"。本目录提供**仓库本地、
 * 自造、可复现**的 litmus 测试，替代规格里"公开 litmus"的外部二进制依赖
 * （规格 §6 W7 原文："公开 litmus + 自设"，自设是规格明示允许的）。
 *
 * 设计约束（每条都有理由，不要随手改）：
 *
 *  1. **fork + MAP_SHARED，不用 pthread。** litmus7/herd7 的标准做法就是
 *     "两个独立进程 + 共享 mmap"，因为进程一定可被 Linux 调度到两个 CPU 上。
 *     glibc 静态链接 + fork 在 aarch64 上是稳的。
 *
 *  2. **只用一次 fork，轮次用世代计数器同步。** gem5 FS 下每次 fork 都要跑
 *     整条 clone/exec 内核路径（m2_ptrchase.rcS 的 2000 次 fork 实测约 20s/
 *     次 → ~12h）。所以：fork 一次，子进程循环 R 轮，父进程每轮改 go 世代。
 *
 *  3. **CPU 亲缘用 sched_setaffinity，不依赖 guest 里的 taskset。** 静态镜像
 *     里不保证有 util-linux；syscall 直接从 libc 走。
 *
 *  4. **oracle = 禁出现结果计数，必须为 0。** 规格 §6 W7 原文判定是
 *     "每轮检查禁出现结果"。三个测试各自插入了 dmb ish / ldxr-stxr，
 *     使得弱结果在 ARM 架构模型下也**非法**，所以 0 是唯一正确期望值：
 *       SB  : P0 {x=1; dmb; r0=y}  P1 {y=1; dmb; r1=x}  禁 r0==0 && r1==0
 *       MP  : P0 {x=1; dmb; flag=1} P1 {wait flag; dmb; r1=x} 禁 flag==1 && r1==0
 *       ATOM: 两核各 N 次 ldxr/stxr 自增同一变量        禁 final != 2N
 *     出现非 0 即硬件/注入导致的可见违例（对 SDC 分类即"wrong data"）。
 *
 *  5. **输出既有人读的 oracle 行，也有 FINAL=<16hex>。** FINAL 沿用
 *     workloads/ 的既有约定（tools/classify.py 的 _CHECKSUM_RE），这里取
 *     **违例计数与轮次的 fnv1a 折叠**：无故障时恒为定值（0 违例的哈希），
 *     因此可以直接当 golden 用。注意：litmus 的**结果分布**本身不是确定的
 *     （弱序下不同调度给不同直方图），所以哈希**只覆盖违例计数**，不覆盖
 *     分布 —— 覆盖分布会把一个合法非确定量当 golden，那是错的。
 */
#ifndef LITMUS_COMMON_H
#define LITMUS_COMMON_H

#define _GNU_SOURCE
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>

#ifndef LITMUS_ROUNDS
#define LITMUS_ROUNDS 2000
#endif

/* 全屏障：既是编译器屏障也是 ARM DMB ISH。规格 W7 的 MP/SB 要"禁出现结果"
   就靠它把弱结果变成非法；同时它也是 O06（DMB/DSB barrier 完成）模型的
   观测量。 */
static inline void litmus_dmb(void) { __asm__ volatile("dmb ish" ::: "memory"); }

/* 绑核：返回 0 成功。cpu 由 sched_getaffinity 的可选集决定；越界则由内核
   返回 EINVAL —— 我们打印出来而不是静默忽略。 */
static inline int litmus_pin(int cpu) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    return sched_setaffinity(0, sizeof(set), &set);
}

static inline unsigned long long litmus_fnv(unsigned long long acc,
                                           unsigned long long v) {
    acc ^= v;
    acc *= 0x100000001b3ULL;
    return acc;
}

/* FINAL=<16hex>：只有 **测试标识**、违例计数与轮次进哈希（见文件头第 5 条）。
   测试标识必须进哈希：否则两个不同的 litmus 在"0 违例 + 同轮次"下会给出
   同一个 FINAL（SB 与 MP 就是这种情况），golden 就不再是载体指纹。 */
static inline void litmus_final(const char *tag, unsigned long long forbidden,
                               unsigned long long rounds) {
    unsigned long long acc = 0x9c3b7af1d52e4806ULL;
    for (const char *c = tag; *c; ++c)
        acc = litmus_fnv(acc, (unsigned char)*c);
    acc = litmus_fnv(acc, forbidden);
    acc = litmus_fnv(acc, rounds);
    printf("FINAL=%016llx\n", acc);
    fflush(stdout);
}

/* CPU 数：直接从内核拿，作为"guest 真是 SMP"的现场证据（不是断言）。 */
static inline long litmus_ncpus(void) { return sysconf(_SC_NPROCESSORS_ONLN); }

#endif /* LITMUS_COMMON_H */
