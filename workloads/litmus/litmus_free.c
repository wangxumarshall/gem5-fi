/* workloads/litmus/litmus_free.c — W7 Atomic-Litmus 多核载体的 **freestanding**
 * 变体（R4-9-FSMC-A）。
 *
 * 为什么另起一个文件（R4-9-FSMC-A 的根因决定）：
 *   规格 §07 把 10 个 A 组 RunID（O01/O02/O03 × W7）钉在 Atomic-Litmus 上。
 *   R4-8-FSMC 已经做出多核 FS 平台（2 核 Ruby/CHI）与仓库本地 litmus，但
 *   **载荷投放臂卡死**：把 3 个 642 KB 的 libc 静态 ELF 以 base64 heredoc
 *   内嵌进 rcS，guest 侧 `sh` + `base64 -d` 在观测窗内解不出来（三臂终态
 *   一致；压缩臂同样卡住）。R4-8-FSMC §3.2 给出的修法有两条，其中一条是
 *   "把 litmus 改成 -nostdlib 手写 syscall 的版本（约 3 KB）"。本文件就是
 *   那一条，并且把三个测试合进一个 ELF（一次 exec 而不是三次），把投放量
 *   从 ~1.9 MB（base64 后 2.6 MB）压到 ~4 KB 量级。
 *
 * 设计约束（每条都有理由）：
 *
 *  1. **零 libc、零 libgcc。** `-nostdlib -static -no-pie -ffreestanding
 *     -fno-stack-protector`。所以：自己做 syscall、自己做整数→十进制/十六
 *     进制格式化、不调用 memcpy/memset（结构体一律用指针读写，避免编译器
 *     生成 memcpy 调用）、不做 64 位除法（除数是常量 10 时 GCC 用乘移位，
 *     不会拉进 __udivdi3）。理由是"小"和"确定"：没有动态装载器、没有
 *     locale、没有任何隐藏依赖，ELF 只有 .text/.rodata 几页。
 *
 *  2. **fork 用裸 clone(220)，不用 pthread。** litmus7/herd7 的标准做法就是
 *     "两个独立进程 + 共享 mmap"（进程一定能被调度到两个 CPU 上）。子进程栈
 *     由 mmap 显式提供（musl 的做法），不依赖内核对 newsp==0 的约定；子进程
 *     入口走 asm trampoline（见下面 litmus_clone_tramp），因为 arm64 的
 *     clone 子进程是从 svc 之后继续执行、x0==0，需要一个显式的跳转点。
 *
 *  3. **每个测试只 fork 一次，轮次用世代计数器同步。** gem5 FS 下 fork/exec
 *     走整条内核路径，很贵（仓库既有记录：m2_ptrchase.rcS 的 2000 次 fork
 *     实测 ≈20s/次 → ~12h）。所以 3 个测试 = 3 次 clone，之后全是共享内存
 *     握手。父进程同时承担 P0 角色（不做第三个"纯控制器"进程），fork 数
 *     再减半。
 *
 *  4. **oracle = 禁出现结果计数，必须为 0。** 与 litmus_common.h 同一口径，
 *     但每一步都插了 dmb ish（既是编译器屏障也是 ARM DMB ISH），使弱结果在
 *     ARM 架构模型下非法：
 *       SB  : P0 {x=1; dmb; r0=y}  P1 {y=1; dmb; r1=x}      禁 r0==0 && r1==0
 *       MP  : P0 {x=1; dmb; flag=1} P1 {有界等 flag; dmb; r1=x}
 *             禁 flag==1 && r1==0；**有界自旋**，超时单独计数（timeout），
 *             因为无一致性平台上"永远读不到 flag"本身就是诊断结论，把它
 *             变成挂死会毁掉整个 payload 的可观测性（R4-8-FSMC §3.2 的教训）。
 *       ATOM: 两核各 N 次 ldxr/stxr 自增同一变量   禁 final != 2N
 *
 *  5. **FINAL=<16hex> 只折叠"禁出现计数 + 轮次"，不折叠结果分布。** SB 的
 *     直方图本身非确定（弱序下不同调度给不同直方图），把分布当 golden 是
 *     错的；折叠计数才是"同一台机器上恒定"的量。3 个测试各自打印 oracle 行，
 *     整个二进制最后只打一行 FINAL，供 tools/classify.py 的 _CHECKSUM_RE 取。
 *
 * 用法：见 Makefile 的 `free` / `payload_free` / `smoke_free` 目标。
 * 退出码：0 = 三个测试都跑完且父/子进程都正常退出（**不**代表 0 违例——
 * 违例数在 oracle 行与 FINAL 里，由分类器判）。
 */
typedef unsigned long u64;
typedef long i64;
typedef unsigned int u32;

/* ---- 常量 -------------------------------------------------------------- */
#define SYS_write 64
#define SYS_exit 93
#define SYS_clone 220
#define SYS_sched_setaffinity 122
#define SYS_sched_getaffinity 123
#define SYS_mmap 222
#define SYS_wait4 260

#define PROT_RW 3
#define MAP_SHARED_ANON 0x21   /* MAP_SHARED(1) | MAP_ANONYMOUS(0x20) */
#define MAP_PRIV_ANON 0x22     /* MAP_PRIVATE(2) | MAP_ANONYMOUS(0x20) */

#define SIGCHLD 17

#ifndef LITMUS_FREE_SB_ROUNDS
#define LITMUS_FREE_SB_ROUNDS 64
#endif
#ifndef LITMUS_FREE_MP_ROUNDS
#define LITMUS_FREE_MP_ROUNDS 64
#endif
#ifndef LITMUS_FREE_MP_SPIN
#define LITMUS_FREE_MP_SPIN 50000
#endif
#ifndef LITMUS_FREE_ATOM_ROUNDS
#define LITMUS_FREE_ATOM_ROUNDS 32
#endif
#ifndef LITMUS_FREE_ATOM_INCR
#define LITMUS_FREE_ATOM_INCR 4
#endif

/* ---- syscall ----------------------------------------------------------- */
static long sys6(long n, long a, long b, long c, long d, long e, long f)
{
    register long x8 __asm__("x8") = n;
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = d;
    register long x4 __asm__("x4") = e;
    register long x5 __asm__("x5") = f;
    __asm__ volatile("svc #0"
                     : "+r"(x0)
                     : "r"(x8), "r"(x1), "r"(x2), "r"(x3), "r"(x4), "r"(x5)
                     : "memory", "cc");
    return x0;
}

static void sys_exit(int code) { sys6(SYS_exit, code, 0, 0, 0, 0, 0); }
static void sys_write(const char *p, long n)
{
    sys6(SYS_write, 1, (long)p, n, 0, 0, 0);
}

static void *os_mmap(long len, int flags)
{
    long r = sys6(SYS_mmap, 0, len, PROT_RW, flags, -1, 0);
    if (r < 0 && r > -4096)
        return 0;
    return (void *)r;
}

/* ---- 输出（无 libc 的极简格式化）-------------------------------------- */
/* ★ 这三个全局**故意给非零初值**：零初值会落进 .bss，而 .bss 会生成一个
 * FileSiz==0 的 PT_LOAD 段。仓库里能跑的 nostdlib 先例（sysreg_churn，见
 * configs/fs/sysreg_churn.rcS 内嵌的 ELF）**只有 1 个 LOAD 段、FileSiz ==
 * MemSiz**（无 .bss）。R4-9-FSMC-A 实测：带零长 .bss 段的版本在 gem5 2 核
 * Ruby/O3 guest 里**一进 _start 就 SIGSEGV（exit=139）**，而同一条码在宿主
 * aarch64 上正常——所以这是 guest 侧 ELF 装载对零长段的处理问题，不是本程序
 * 的逻辑问题。非零初值把数据挪进 .data（有文件字节支撑），再配 -Wl,-N
 * （text+data 合并进同一个可写 LOAD）就得到与先例同形的单段 ELF。
 * 真正的初值在 _start 里显式设置，这里的初值只是"非零"占位。 */
static char obuf[1024] = {1};
static int opos = -1;
static int olines = -1;

static void o_flush(void)
{
    if (opos > 0) {
        sys_write(obuf, opos);
        opos = 0;
        ++olines;
    }
}

static void o_c(char c)
{
    if (opos >= 1000)
        o_flush();
    obuf[opos++] = c;
}

static void o_s(const char *s)
{
    while (*s)
        o_c(*s++);
}

static void o_u64(u64 v)
{
    char t[24];
    int i = 0;
    if (v == 0) { o_c('0'); return; }
    while (v) { t[i++] = (char)('0' + (int)(v % 10)); v /= 10; }
    while (i > 0) o_c(t[--i]);
}

static void o_i64(i64 v)
{
    if (v < 0) { o_c('-'); o_u64((u64)(-v)); }
    else o_u64((u64)v);
}

static void o_hex16(u64 v)
{
    static const char H[] = "0123456789abcdef";
    for (int sh = 60; sh >= 0; sh -= 4)
        o_c(H[(v >> sh) & 0xf]);
}

/* ---- CPU 数（sched_getaffinity，不依赖 /proc 与 util-linux）----------- */
/* len 必须 >= cpumask_size()：实测宿主（128 核 → 16 字节）在 len=8 时直接
   EINVAL（见 R4-9-FSMC-A 报告的宿主对照实验）。取 16 = 128 位，恰好覆盖
   宿主的 nr_cpu_ids=128；guest（2 核 → cpumask_size=8）会按 min(len,
   cpumask_size) 截断，同样接受。 */
#define AFFINITY_LEN 16
static long ncpus(void)
{
    u64 mask[2];
    mask[0] = 0;
    mask[1] = 0;
    long r = sys6(SYS_sched_getaffinity, 0, AFFINITY_LEN, (long)mask, 0, 0, 0);
    if (r < 0)
        return -1;
    long n = 0;
    for (int i = 0; i < 64; ++i)
        if ((mask[0] >> i) & 1UL)
            ++n;
    for (int i = 0; i < 64; ++i)
        if ((mask[1] >> i) & 1UL)
            ++n;
    return n;
}

static int pin(int cpu)
{
    u64 mask[2];
    mask[0] = (cpu < 64) ? (1UL << cpu) : 0UL;
    mask[1] = (cpu >= 64 && cpu < 128) ? (1UL << (cpu - 64)) : 0UL;
    long r = sys6(SYS_sched_setaffinity, 0, AFFINITY_LEN, (long)mask, 0, 0, 0);
    return r == 0 ? 0 : (int)r;
}

/* ---- 内存序 ----------------------------------------------------------- */
static void dmb_ish(void) { __asm__ volatile("dmb ish" ::: "memory"); }

/* ---- fork：裸 clone + asm trampoline ---------------------------------- */
__asm__(
".text\n"
".global litmus_clone_tramp\n"
".type litmus_clone_tramp, %function\n"
"litmus_clone_tramp:\n"          /* x0=fn, x1=child_stack_top, x2=arg */
"  stp x0, x2, [x1, #-16]!\n"    /* 在子栈上放 fn/arg，x1 -> 新栈顶 */
"  mov x0, #17\n"                /* flags = SIGCHLD（fork 语义） */
"  mov x3, xzr\n"                /* parent_tid */
"  mov x4, xzr\n"                /* child_tid  */
"  mov x5, xzr\n"                /* tls        */
"  mov x8, #220\n"
"  svc #0\n"
"  cbnz x0, 1f\n"                 /* 父：返回 pid */
"  ldp x1, x0, [sp], #16\n"      /* 子：x1=fn, x0=arg */
"  br x1\n"
"1:\n"
"  ret\n"
".size litmus_clone_tramp, .-litmus_clone_tramp\n"
);
extern long litmus_clone_tramp(void (*fn)(void *), void *stack_top, void *arg);

#define CHILD_STACK_SIZE 65536

static i64 lf_fork(void (*fn)(void *), void *arg)
{
    void *stk = os_mmap(CHILD_STACK_SIZE, MAP_PRIV_ANON);
    if (!stk)
        return -1;
    /* mmap 返回页对齐；栈顶再对齐到 16（arm64 ABI）*/
    u64 top = ((u64)stk + CHILD_STACK_SIZE) & ~15UL;
    return litmus_clone_tramp(fn, (void *)top, arg);
}

static void lf_wait(i64 pid, int *st)
{
    if (pid > 0)
        sys6(SYS_wait4, pid, (long)st, 0, 0, 0, 0);
}

/* ---- 共享内存 --------------------------------------------------------- */
struct sb_sh {
    volatile u64 x, y, r0, r1;
    volatile u64 arr0, arr1;   /* 对称到达栅栏：两侧都必须先到，才同时放行 */
    volatile u64 done0, done1;
};
struct mp_sh {
    volatile u64 x, flag, r1;
    volatile u64 go;
    volatile u64 done0, done1, timeout1;
};
struct at_sh {
    volatile u64 ctr;
    volatile u64 arr0, arr1;   /* 同上：让 ldxr/stxr 竞争真正是双向的 */
    volatile u64 done0, done1;
    volatile u64 tries0, tries1;
};

/* ---- 测试 A：Store Buffering ------------------------------------------ */
static void sb_child(void *p)
{
    struct sb_sh *s = (struct sb_sh *)p;
    if (pin(1) != 0)
        sys_exit(3);
    for (u64 r = 1; r <= (u64)LITMUS_FREE_SB_ROUNDS; ++r) {
        while (s->done0 != r - 1) { }   /* 上一轮父侧已读完，才允许进入本轮 */
        dmb_ish();
        s->arr1 = r;                     /* 对称到达栅栏 */
        dmb_ish();
        while (s->arr0 != r) { }
        dmb_ish();
        s->y = 1;
        dmb_ish();
        s->r1 = s->x;
        dmb_ish();
        s->done1 = r;
    }
    sys_exit(0);
}

static u64 run_sb(long ncpu)
{
    struct sb_sh *s = (struct sb_sh *)os_mmap(sizeof *s, MAP_SHARED_ANON);
    u64 n00 = 0, n01 = 0, n10 = 0, n11 = 0, bad = 0;
    int st = 0;

    o_s("LITMUS free sb nproc="); o_u64((u64)ncpu);
    o_s(" rounds="); o_u64((u64)LITMUS_FREE_SB_ROUNDS); o_c('\n');
    o_flush();
    if (!s) { o_s("LITMUS free sb ABORT mmap\n"); o_flush(); return 1; }
    if (pin(0) != 0) { o_s("LITMUS free sb ABORT pin0\n"); o_flush(); return 1; }

    i64 p1 = lf_fork(sb_child, s);
    if (p1 <= 0) { o_s("LITMUS free sb ABORT fork\n"); o_flush(); return 1; }

    for (u64 r = 1; r <= (u64)LITMUS_FREE_SB_ROUNDS; ++r) {
        s->x = 0; s->y = 0; s->r0 = 0; s->r1 = 0;
        dmb_ish();
        s->arr0 = r;                     /* 对称到达栅栏：两侧同时放行 */
        dmb_ish();
        while (s->arr1 != r) { }
        dmb_ish();
        /* P0 */
        s->x = 1;
        dmb_ish();
        s->r0 = s->y;
        dmb_ish();
        s->done0 = r;
        while (s->done1 != r) { }
        dmb_ish();
        u64 a = s->r0, b = s->r1;
        if (a == 0 && b == 0) ++n00;
        else if (a == 0 && b == 1) ++n01;
        else if (a == 1 && b == 0) ++n10;
        else if (a == 1 && b == 1) ++n11;
        else ++bad;
    }
    lf_wait(p1, &st);

    o_s("LITMUS free sb hist r0r1: 00="); o_u64(n00);
    o_s(" 01="); o_u64(n01);
    o_s(" 10="); o_u64(n10);
    o_s(" 11="); o_u64(n11);
    o_s(" forbidden(00)="); o_u64(n00);
    o_s(" bad="); o_u64(bad);
    o_s(" child_status="); o_i64(st);
    o_c('\n');
    o_flush();
    return n00 + bad;
}

/* ---- 测试 B：Message Passing ----------------------------------------- */
static void mp_child(void *p)
{
    struct mp_sh *s = (struct mp_sh *)p;
    if (pin(1) != 0)
        sys_exit(3);
    for (u64 r = 1; r <= (u64)LITMUS_FREE_MP_ROUNDS; ++r) {
        while (s->go != r) { }
        dmb_ish();
        long seen = 0;
        for (long i = 0; i < LITMUS_FREE_MP_SPIN; ++i)
            if (s->flag != 0) { seen = 1; break; }
        if (!seen)
            s->timeout1 = r;
        dmb_ish();
        s->r1 = s->x;
        dmb_ish();
        s->done1 = r;
    }
    sys_exit(0);
}

static u64 g_mp_tmo = 1;   /* 非零初值 ⇒ .data，见 obuf 上方说明 */

static u64 run_mp(long ncpu)
{
    struct mp_sh *s = (struct mp_sh *)os_mmap(sizeof *s, MAP_SHARED_ANON);
    u64 viol = 0, tmo = 0;
    int st = 0;

    o_s("LITMUS free mp nproc="); o_u64((u64)ncpu);
    o_s(" rounds="); o_u64((u64)LITMUS_FREE_MP_ROUNDS);
    o_s(" spin="); o_u64((u64)LITMUS_FREE_MP_SPIN); o_c('\n');
    o_flush();
    if (!s) { o_s("LITMUS free mp ABORT mmap\n"); o_flush(); return 1; }
    if (pin(0) != 0) { o_s("LITMUS free mp ABORT pin0\n"); o_flush(); return 1; }

    i64 p1 = lf_fork(mp_child, s);
    if (p1 <= 0) { o_s("LITMUS free mp ABORT fork\n"); o_flush(); return 1; }

    for (u64 r = 1; r <= (u64)LITMUS_FREE_MP_ROUNDS; ++r) {
        s->x = 0; s->flag = 0; s->r1 = 0; s->timeout1 = 0;
        dmb_ish();
        s->go = r;
        dmb_ish();
        /* P0 */
        s->x = 1;
        dmb_ish();
        s->flag = 1;
        dmb_ish();
        s->done0 = r;
        while (s->done1 != r) { }
        dmb_ish();
        if (s->timeout1 == r) ++tmo;
        else if (s->r1 == 0) ++viol;
    }
    lf_wait(p1, &st);
    g_mp_tmo = tmo;

    o_s("LITMUS free mp flag1_x0_violations="); o_u64(viol);
    o_s(" timeouts="); o_u64(tmo);
    o_s(" child_status="); o_i64(st);
    o_c('\n');
    o_flush();
    return viol;
}

/* ---- 测试 C：LDXR/STXR 原子性（CAS counter）------------------------- */
static void at_child(void *p)
{
    struct at_sh *s = (struct at_sh *)p;
    if (pin(1) != 0)
        sys_exit(3);
    u64 tries = 0;
    for (u64 r = 1; r <= (u64)LITMUS_FREE_ATOM_ROUNDS; ++r) {
        while (s->done0 != r - 1) { }   /* 上一轮父侧已收尾 */
        dmb_ish();
        s->arr1 = r;                     /* 对称到达栅栏 */
        dmb_ish();
        while (s->arr0 != r) { }
        dmb_ish();
        for (int i = 0; i < LITMUS_FREE_ATOM_INCR; ++i) {
            u64 tmp; u32 st;
            do {
                __asm__ volatile("ldxr %0, [%1]" : "=r"(tmp) : "r"(&s->ctr));
                tmp += 1;
                __asm__ volatile("stxr %w0, %1, [%2]"
                                 : "=&r"(st) : "r"(tmp), "r"(&s->ctr));
                ++tries;
            } while (st != 0);
        }
        s->tries1 = tries;
        dmb_ish();
        s->done1 = r;
    }
    sys_exit(0);
}

static u64 run_atom(long ncpu)
{
    struct at_sh *s = (struct at_sh *)os_mmap(sizeof *s, MAP_SHARED_ANON);
    u64 viol = 0;
    int st = 0;
    const u64 expect = 2UL * (u64)LITMUS_FREE_ATOM_INCR;

    o_s("LITMUS free atomic nproc="); o_u64((u64)ncpu);
    o_s(" rounds="); o_u64((u64)LITMUS_FREE_ATOM_ROUNDS);
    o_s(" incr_per_core="); o_u64((u64)LITMUS_FREE_ATOM_INCR); o_c('\n');
    o_flush();
    if (!s) { o_s("LITMUS free atomic ABORT mmap\n"); o_flush(); return 1; }
    if (pin(0) != 0) { o_s("LITMUS free atomic ABORT pin0\n"); o_flush(); return 1; }

    i64 p1 = lf_fork(at_child, s);
    if (p1 <= 0) { o_s("LITMUS free atomic ABORT fork\n"); o_flush(); return 1; }

    u64 tries0 = 0;
    for (u64 r = 1; r <= (u64)LITMUS_FREE_ATOM_ROUNDS; ++r) {
        s->ctr = 0;
        dmb_ish();
        s->arr0 = r;                     /* 对称到达栅栏：两侧同时放行 */
        dmb_ish();
        while (s->arr1 != r) { }
        dmb_ish();
        for (int i = 0; i < LITMUS_FREE_ATOM_INCR; ++i) {
            u64 tmp; u32 stx;
            do {
                __asm__ volatile("ldxr %0, [%1]" : "=r"(tmp) : "r"(&s->ctr));
                tmp += 1;
                __asm__ volatile("stxr %w0, %1, [%2]"
                                 : "=&r"(stx) : "r"(tmp), "r"(&s->ctr));
                ++tries0;
            } while (stx != 0);
        }
        s->tries0 = tries0;
        dmb_ish();
        s->done0 = r;
        while (s->done1 != r) { }
        dmb_ish();
        if (s->ctr != expect)
            ++viol;
    }
    lf_wait(p1, &st);

    o_s("LITMUS free atomic ctr_expect="); o_u64(expect);
    o_s(" violations="); o_u64(viol);
    o_s(" tries cpu0="); o_u64(s->tries0);
    o_s(" cpu1="); o_u64(s->tries1);
    o_s(" min="); o_u64((u64)LITMUS_FREE_ATOM_INCR);
    o_s(" child_status="); o_i64(st);
    o_c('\n');
    o_flush();
    return viol;
}

/* ---- FINAL：只折叠"禁出现计数 + 轮次"（见文件头第 5 条）------------- */
static u64 fnv(u64 acc, u64 v)
{
    acc ^= v;
    acc *= 0x100000001b3UL;
    return acc;
}

static u64 final_hash(u64 sb, u64 mp, u64 mp_tmo, u64 at)
{
    u64 acc = 0x9c3b7af1d52e4806UL;
    const char *tag = "litmus_free";
    for (const char *c = tag; *c; ++c)
        acc = fnv(acc, (u64)(unsigned char)*c);
    acc = fnv(acc, sb);
    acc = fnv(acc, mp);
    acc = fnv(acc, mp_tmo);
    acc = fnv(acc, at);
    acc = fnv(acc, (u64)LITMUS_FREE_SB_ROUNDS);
    acc = fnv(acc, (u64)LITMUS_FREE_MP_ROUNDS);
    acc = fnv(acc, (u64)LITMUS_FREE_ATOM_ROUNDS);
    acc = fnv(acc, (u64)LITMUS_FREE_ATOM_INCR);
    return acc;
}

/* ---- 入口 ------------------------------------------------------------- */
void _start(void);

void _start(void)
{
    opos = 0;
    olines = 0;
    g_mp_tmo = 0;
    long ncpu = ncpus();

    o_s("LITMUS free begin nproc="); o_u64((u64)ncpu); o_c('\n');
    o_flush();
    if (ncpu < 2) {
        o_s("LITMUS free ABORT nproc<2 — this litmus needs two runnable "
            "CPUs\n");
        o_flush();
        sys_exit(4);
    }

    u64 sb = run_sb(ncpu);
    u64 mp = run_mp(ncpu);
    u64 at = run_atom(ncpu);

    o_s("FINAL="); o_hex16(final_hash(sb, mp, g_mp_tmo, at)); o_c('\n');
    o_s("LITMUS free end\n");
    o_flush();
    sys_exit(0);
}
