// mmu_w12.c — ARM64 userland MMU-TLB-Resident-PFN workload (M04 baseline).
//
// One process maps a target 4 KiB page and a decoy 4 KiB page (distinct
// sentinels), populates both PTEs and warms both TLB entries.  The target
// access is therefore a real DTLB hit; M04 substitutes the resident target
// PFN with the decoy PFN, so a baseline target load must read the target
// sentinel while an injected one reads the decoy sentinel.
//
// Contexts (--ctx / --all):
//   R01 LDR direct                       (DTLB hit)
//   R02 LDR -> ADD                       (DTLB hit)
//   R03 LDR -> CMP -> conditional branch (DTLB hit)
//   R04 LDR -> address -> second LDR     (DTLB hit)
//   R05 ITLB: a target JIT code page and a decoy JIT code page return
//       different values; both ITLB entries are warmed, then target is called.
//
// --decoy-pfn <hex> lets the run script pin the decoy PFN observed in a
// control run.  0 (default) means auto mode: the PFN of the second mapping.
// The workload always reports the actual decoy-mapping PFN and whether the
// supplied candidate matched it.
//
// Pagemap PFNs require CAP_SYS_ADMIN (root in the gem5 FS).
//
// PASS = observed == target sentinel.
//
// Build: gcc -O2 -static -march=armv8-a+simd -o mmu_w12 mmu_w12.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define PAGE 4096UL
#define W12_TARGET_VA 0x4008000000UL
#define W12_DECOY_VA  0x400A000000UL

#define MARKER_T 0x7D
#define MARKER_D 0x51
#define WARM_ITERS 20000

static volatile uint64_t sink;
static int pm_fd = -1;

static uint64_t
read_pagemap(uintptr_t va, int *present, int *pfn_ok)
{
    uint64_t entry = 0;
    *present = 0;
    *pfn_ok = 0;
    if (pm_fd < 0)
        pm_fd = open("/proc/self/pagemap", O_RDONLY);
    if (pm_fd < 0)
        return 0;
    off_t off = (off_t)((va >> 12) * 8);
    if (pread(pm_fd, &entry, sizeof(entry), off) != sizeof(entry)) {
        *present = -1;
        return 0;
    }
    *present = (int)((entry >> 63) & 1);
    uint64_t pfn = entry & ((1ULL << 55) - 1);
    *pfn_ok = (*present && pfn != 0);
    return pfn;
}

static uint32_t
movz_w0(uint16_t imm)
{
    return 0x52800000u | ((uint32_t)imm << 5);   /* MOVZ W0, #imm16 */
}

#define INSN_RET 0xD65F03C0u

typedef int (*fn_t)(void);

static int
is_code_ctx(const char *ctx)
{
    return !strcmp(ctx, "R05");
}

static int
run_context(const char *ctx, volatile uint8_t *p, uint8_t expect,
            uint8_t *scalar, unsigned *branch)
{
    uint8_t v = 0;
    *branch = 0;
    *scalar = 0;

    if (!strcmp(ctx, "R01")) {
        v = *p;
        sink = v;
    } else if (!strcmp(ctx, "R02")) {
        v = *p;
        sink = (uint64_t)v + 0x11;
    } else if (!strcmp(ctx, "R03")) {
        v = *p;
        if (v == expect) {
            *branch = 1;
            sink = 0x100;
        } else {
            *branch = 2;
            sink = 0x200;
        }
    } else if (!strcmp(ctx, "R04")) {
        v = *p;
        volatile uint8_t *q = p + (v & 0x0F);
        uint8_t w = *q;
        sink = w;
        v = w;
    } else {
        return -1;
    }
    *scalar = v;
    return 0;
}

static int
run_one_ctx(const char *ctx, uint64_t decoy_arg)
{
    int is_r05 = is_code_ctx(ctx);
    uint64_t sentinel = is_r05 ? MARKER_T : MARKER_T;
    uint64_t decoy_sentinel = is_r05 ? MARKER_D : MARKER_D;

    int prot = PROT_READ | PROT_WRITE;
    void *t = mmap((void *)W12_TARGET_VA, PAGE, prot,
                   MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE |
                   MAP_POPULATE, -1, 0);
    void *d = mmap((void *)W12_DECOY_VA, PAGE, prot,
                   MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE |
                   MAP_POPULATE, -1, 0);
    if (t == MAP_FAILED || d == MAP_FAILED) {
        fprintf(stderr, "W12_FATAL mmap target/decoy errno=%d (%s)\n",
                errno, strerror(errno));
        return 2;
    }
    madvise(t, PAGE, MADV_NOHUGEPAGE);
    madvise(d, PAGE, MADV_NOHUGEPAGE);

    if (is_r05) {
        uint32_t *ct = (uint32_t *)t;
        uint32_t *cd = (uint32_t *)d;
        ct[0] = movz_w0(MARKER_T);
        ct[1] = INSN_RET;
        cd[0] = movz_w0(MARKER_D);
        cd[1] = INSN_RET;
        for (int i = 2; i < (int)(PAGE / 4); i++)
            ct[i] = cd[i] = 0xD503201Fu;   /* NOP padding */
        if (mprotect(t, PAGE, PROT_READ | PROT_EXEC) != 0 ||
            mprotect(d, PAGE, PROT_READ | PROT_EXEC) != 0) {
            fprintf(stderr, "W12_FATAL mprotect RX errno=%d (%s)\n",
                    errno, strerror(errno));
            return 2;
        }
        __builtin___clear_cache((char *)t, (char *)t + PAGE);
        __builtin___clear_cache((char *)d, (char *)d + PAGE);
        __asm__ __volatile__("isb" ::: "memory");
    } else {
        memset(t, MARKER_T, PAGE);
        memset(d, MARKER_D, PAGE);
    }

    int pres_t = 0, pfn_t_ok = 0, pres_d = 0, pfn_d_ok = 0;
    uint64_t pfn_t = read_pagemap((uintptr_t)t, &pres_t, &pfn_t_ok);
    uint64_t pfn_d = read_pagemap((uintptr_t)d, &pres_d, &pfn_d_ok);

    if (!strcmp(ctx, "C03")) {
        /* [WHEN-5X3 C03] Weak consumer. Warm both entries once (the target
         * miss is not eligible), then perform >=3 real target hits whose
         * values are discarded. No value feeds sink or the oracle. */
        volatile uint8_t *pt = t, *pd = d;
        for (int i = 0; i < 4; i++) {
            volatile uint8_t dead_d = pd[0];
            volatile uint8_t dead_t = pt[0];
            (void)dead_d;
            (void)dead_t;
        }
        for (int i = 0; i < 3; i++) {
            volatile uint8_t dead = pt[0];
            (void)dead;
            __asm__ __volatile__("" ::: "memory");
        }
        int pass = (pfn_t_ok && pfn_d_ok);
        printf("W12_RESULT ctx=C03 target_va=0x%" PRIxPTR
               " target_pfn=0x%" PRIx64 " decoy_pfn=0x%" PRIx64
               " observed=0x0 sentinel=0x%" PRIx64
               " decoy_sentinel=0x%" PRIx64 " branch=0"
               " mode=weak_consumer decoy_pfn_arg=0x%" PRIx64
               " decoy_arg_match=%d pagemap=%s pfn_ok=%d/%d result=%s\n",
               (uintptr_t)t, pfn_t, pfn_d, sentinel, decoy_sentinel,
               decoy_arg, (decoy_arg != 0 && decoy_arg == pfn_d),
               (pfn_t_ok && pfn_d_ok) ? "ok" : "unavailable",
               pfn_t_ok, pfn_d_ok, pass ? "PASS" : "FAIL");
        fflush(stdout);
        return pass ? 0 : 1;
    }

    /* Warm both translations: the M04 target event is a real TLB hit. */
    if (is_r05) {
        volatile fn_t ft = (fn_t)t;
        volatile fn_t fd = (fn_t)d;
        for (int i = 0; i < WARM_ITERS; i++) {
            sink += (uint64_t)ft();
            sink += (uint64_t)fd();
        }
    } else {
        volatile uint8_t *pt = t, *pd = d;
        for (int i = 0; i < WARM_ITERS; i++) {
            sink += pt[0];
            sink += pd[0];
        }
    }

    uint64_t observed = 0;
    unsigned branch = 0;
    if (is_r05) {
        volatile fn_t ft = (fn_t)t;
        observed = (uint64_t)(unsigned)ft();
    } else {
        uint8_t v = 0;
        if (run_context(ctx, t, (uint8_t)sentinel, &v, &branch) != 0) {
            fprintf(stderr, "W12_FATAL unknown ctx %s\n", ctx);
            return 2;
        }
        observed = v;
    }

    int pass = (observed == sentinel);
    int arg_match = (decoy_arg != 0 && decoy_arg == pfn_d);
    printf("W12_RESULT ctx=%s target_va=0x%" PRIxPTR
           " target_pfn=0x%" PRIx64 " decoy_pfn=0x%" PRIx64
           " observed=0x%" PRIx64 " sentinel=0x%" PRIx64
           " decoy_sentinel=0x%" PRIx64 " branch=%u"
           " mode=%s decoy_pfn_arg=0x%" PRIx64 " decoy_arg_match=%d"
           " pagemap=%s pfn_ok=%d/%d result=%s\n",
           ctx, (uintptr_t)t, pfn_t, pfn_d, observed, sentinel,
           decoy_sentinel, branch,
           decoy_arg ? "explicit" : "auto", decoy_arg, arg_match,
           (pfn_t_ok && pfn_d_ok) ? "ok" : "unavailable",
           pfn_t_ok, pfn_d_ok, pass ? "PASS" : "FAIL");
    fflush(stdout);
    return pass ? 0 : 1;
}

int
main(int argc, char **argv)
{
    const char *ctx = "R01";
    int all = 0;
    uint64_t decoy_arg = 0;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--ctx") && i + 1 < argc)
            ctx = argv[++i];
        else if (!strcmp(argv[i], "--all"))
            all = 1;
        else if (!strcmp(argv[i], "--decoy-pfn") && i + 1 < argc)
            decoy_arg = strtoull(argv[++i], NULL, 0);
        else {
            fprintf(stderr, "usage: %s [--ctx R01..R05] [--all]"
                    " [--decoy-pfn <hex>]\n", argv[0]);
            return 2;
        }
    }

    static const char *ctxs[5] = {"R01", "R02", "R03", "R04", "R05"};
    int valid = !strcmp(ctx, "C03");
    for (int i = 0; i < 5; i++)
        if (!strcmp(ctx, ctxs[i]))
            valid = 1;
    if (!all && !valid) {
        fprintf(stderr, "W12_FATAL unknown ctx %s\n", ctx);
        return 2;
    }

    if (!all)
        return run_one_ctx(ctx, decoy_arg);

    /* --all: one process per context. */
    int pass = 0;
    for (int i = 0; i < 5; i++) {
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork ctx");
            continue;
        }
        if (pid == 0)
            _exit(run_one_ctx(ctxs[i], decoy_arg));
        int st = 0;
        waitpid(pid, &st, 0);
        if (WIFEXITED(st) && WEXITSTATUS(st) == 0)
            pass++;
    }
    printf("W12_SUMMARY pass=%d/5\n", pass);
    fflush(stdout);
    return pass == 5 ? 0 : 1;
}
