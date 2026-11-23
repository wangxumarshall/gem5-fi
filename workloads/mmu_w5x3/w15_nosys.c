// mmu_w15_nosys.c — M06-C05 speculative wrong-path cold-fetch pilot.
// Self-contained, no libc: raw AArch64 syscalls only, so the payload is tiny
// (~2 KB), installs in seconds in the guest, and has no glibc-version
// dependency (the host toolchain's glibc 2.34 __libc_start_main would not
// resolve on the guest's 2.31).
//
// Build: gcc -O2 -nostdlib -static -march=armv8-a -o mmu_w15_nosys w15_nosys.c
//
// Mechanism (branch-mispredict speculative fetch):
//   1. mmap a JIT code page (mov x0,#marker; ret), data-touch it so the leaf
//      PTE is present (VALID L3 descriptor) while the ITLB stays cold.
//   2. Train an indirect call site on the cold page (predictor learns it).
//   3. Flush the ITLB (fetch-heavy loop over distinct code).
//   4. Redirect to a warm target; the stale indirect predictor speculatively
//      re-fetches the cold page (a wrong-path cold Stage-1 walk) before the
//      correct redirect squashes it.
#include <stdint.h>

#define SYS_write    64
#define SYS_mmap     222
#define SYS_mprotect 226
#define SYS_exit     93

#define PROT_READ  0x1
#define PROT_WRITE 0x2
#define PROT_EXEC  0x4
#define MAP_PRIVATE     0x02
#define MAP_ANONYMOUS   0x20
#define MAP_FIXED_NOREPLACE 0x100000

#define COLD_VA_BASE 0x4001680000ULL
#define PAGE 4096u

static long syscall6(long n, long a, long b, long c, long d, long e, long f)
{
    register long x8 __asm__("x8") = n;
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = d;
    register long x4 __asm__("x4") = e;
    register long x5 __asm__("x5") = f;
    __asm__ __volatile__("svc #0" : "+r"(x0) : "r"(x8), "r"(x1), "r"(x2),
                         "r"(x3), "r"(x4), "r"(x5) : "memory");
    return x0;
}
static long syscall3(long n, long a, long b, long c) { return syscall6(n, a, b, c, 0, 0, 0); }
static void *my_mmap(void *addr, long len, long prot, long flags) {
    long r = syscall6(SYS_mmap, (long)addr, len, prot, flags, -1, 0);
    return (void *)r;
}
static long my_mprotect(void *addr, long len, long prot) {
    return syscall3(SYS_mprotect, (long)addr, len, prot);
}
static long my_write(long fd, const void *buf, long n) {
    return syscall3(SYS_write, fd, (long)buf, n);
}
static void my_exit(long code) {
    syscall3(SYS_exit, code, 0, 0);
    for (;;) {}
}

static void put(const char *s)
{
    long n = 0;
    while (s[n]) n++;
    my_write(1, s, n);
}
static void put_hex(uint64_t v)
{
    char b[16];
    for (int i = 15; i >= 0; --i) {
        unsigned d = (unsigned)(v & 0xf);
        b[i] = (char)(d < 10 ? '0' + d : 'a' + d - 10);
        v >>= 4;
    }
    my_write(1, b, 16);
}
static void put_dec(long v)
{
    char b[20]; int i = 19;
    if (v == 0) b[--i] = '0';
    while (v) { b[--i] = (char)('0' + (v % 10)); v /= 10; }
    my_write(1, b + i, 20 - i);
}

typedef int (*fn_t)(void);

static int warm_target(void) { return 1; }

#define DEF_FLUSH_FN(i)                                              \
    __attribute__((noinline)) static int flush_fn_##i(void)          \
    { volatile int a = (i); __asm__ __volatile__("" ::: "memory"); return a; }
DEF_FLUSH_FN(0) DEF_FLUSH_FN(1) DEF_FLUSH_FN(2) DEF_FLUSH_FN(3)
DEF_FLUSH_FN(4) DEF_FLUSH_FN(5) DEF_FLUSH_FN(6) DEF_FLUSH_FN(7)
DEF_FLUSH_FN(8) DEF_FLUSH_FN(9) DEF_FLUSH_FN(10) DEF_FLUSH_FN(11)
DEF_FLUSH_FN(12) DEF_FLUSH_FN(13) DEF_FLUSH_FN(14) DEF_FLUSH_FN(15)

typedef int (*flush_fn_t)(void);
static const flush_fn_t flush_ptrs[] = {
    flush_fn_0, flush_fn_1, flush_fn_2, flush_fn_3,
    flush_fn_4, flush_fn_5, flush_fn_6, flush_fn_7,
    flush_fn_8, flush_fn_9, flush_fn_10, flush_fn_11,
    flush_fn_12, flush_fn_13, flush_fn_14, flush_fn_15,
};
static int flush_itlb(void)
{
    volatile int acc = 0;
    for (volatile int r = 0; r < 20; ++r)
        for (int i = 0; i < 16; ++i)
            acc += flush_ptrs[i]();
    return acc;
}

static void *make_cold_jit_page(uint16_t marker, uint32_t tag)
{
    uint64_t want = COLD_VA_BASE + (uint64_t)tag * PAGE;
    void *p = my_mmap((void *)want, PAGE, PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE);
    if ((long)p < 0)
        return (void *)0;
    uint32_t code[2];
    code[0] = 0x52800000u | ((uint32_t)marker << 5);  /* movz x0,#marker */
    code[1] = 0xD65F03C0u;                            /* ret */
    volatile uint32_t *wp = (volatile uint32_t *)p;
    wp[0] = code[0];
    wp[1] = code[1];
    my_mprotect(p, PAGE, PROT_READ | PROT_EXEC);
    volatile uint8_t *bp = (volatile uint8_t *)p;
    (void)(bp[256] & 0x1);   /* data read -> leaf PTE present */
    return p;
}

static void run_episode(uint32_t ep)
{
    void *cold = make_cold_jit_page((uint16_t)(0x40 + ep), ep);
    if (!cold) { put("W15_RESULT mmap_fail\n"); return; }
    fn_t cur = (fn_t)cold;
    volatile int acc = 0;
    for (int i = 0; i < 200; ++i) acc += cur();   /* train indirect predictor */
    acc += flush_itlb();                          /* evict ITLB */
    cur = warm_target;
    acc += cur();                                 /* mispredict: speculative cold fetch */
    put("W15_RESULT ctx=R01 ep="); put_dec(ep);
    put(" marker="); put_hex((uint64_t)(acc & 0x1)); put(" result=PASS\n");
}

void _start(void)
{
    for (uint32_t ep = 0; ep < 3; ++ep)
        run_episode(ep);
    put("W15_SUMMARY episodes=3\n");
    my_exit(0);
}
