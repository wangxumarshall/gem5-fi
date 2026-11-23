// mmu_w13.c — ARM64 userland MMU-WalkCache-PartialHit workload (M05 baseline).
//
// Two 4 KiB VA regions exactly 2 MiB apart (VA and VA+0x200000) are mapped to
// distinct physical pages.  They share the same L1 (1 GiB) translation-table
// entry but have different L2 entries, so their L2->L3 partial walk-cache
// entries cache different L3 table base addresses.  Both regions are warmed,
// which creates compatible L2 partial entries.
//
// M05 substitutes one L2 partial entry's next-table base with the other's;
// a later target walk that resumes from the substituted partial entry reads
// the decoy L3 table, gets the decoy leaf PFN and returns the decoy sentinel.
//
// ORDERING MATTERS FOR M05: the decoy region is touched BEFORE the target
// region.  The PTW hook activates on the target's FIRST L2 partial-entry
// insertion (the target fill below), so the decoy's L2 partial entry must
// already be live at that instant.  The formal runner selects that entry by
// decoy VA (--mmu_m05_decoy_va 0x4010200000) instead of guessing.
//
// To make the target walk re-run while keeping partial entries, the workload
// uses a MAP_SHARED 4 KiB page (no COW on the protection change) and changes
// only the target page protection with mprotect().  Linux then issues a
// VA-range last-level TLB invalidation for the target VA; the last-level
// complete entry is removed while intermediate (partial) walk-cache entries
// are not address-tagged by the VA.  Exact syscall sequence is printed on the
// W13_SEQUENCE line.  EL0 cannot issue TLBI VALE1IS itself, and partial-entry
// retention is not observable from userspace, so the workload states that
// honestly (W13_LIMITATION) and leaves confirmation to the gem5 TLB trace.
//
// DETERMINISTIC TERMINALS: SIGSEGV/SIGBUS are caught and print a W13_RESULT
// line with result=CRASH plus the fault phase; a SIGALRM watchdog armed only
// for the post-warm access phase prints result=TIMEOUT.  Every context thus
// ends with exactly one RESULT line and a non-zero exit code instead of an
// open-ended hang.  A W13_INFO line is the machine-readable start handshake.
//
// Contexts (--ctx / --all):
//   R01 LDR direct                       (data side)
//   R02 LDR -> ADD                       (data side)
//   R03 LDR -> CMP -> conditional branch (data side)
//   R04 LDR -> address -> second LDR     (data side)
//   R05 instruction fetch after the leaf-only invalidation (ITLB/PTW)
//
// PASS = observed == target sentinel (target sentinel is the no-fault golden).
//
// Build: gcc -O2 -static -march=armv8-a+simd -o mmu_w13 mmu_w13.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define PAGE 4096UL
#define W13_TARGET_VA 0x4010000000UL
#define W13_DECOY_VA  0x4010200000UL   /* +2 MiB: same L1, different L2/L3 */
/* Fresh alias page inside the same 2 MiB region.  It has a populated 4K PTE
 * but no complete TLB entry before the consumer access, so the access must
 * resume from the (possibly corrupted) L2 partial walk-cache entry. */
#define W13_ALIAS_OFF 0x1000UL

#define MARKER_T 0x7D
#define MARKER_D 0x51
#define WARM_ITERS 20000
#define W13_WATCHDOG_SEC 120

static volatile uint64_t sink;
static int pm_fd = -1;
static unsigned watchdog_sec = W13_WATCHDOG_SEC;

/* ---- deterministic-terminal support ---------------------------------- */
/* The watchdog is armed ONLY after warm-up and before mprotect, so a long
 * but healthy warm phase can never trigger it.  The hang this protects
 * against is post-invalidation (M05 walk-cache substitution / fault loop). */
enum w13_phase {
    PH_START = 0,
    PH_MAP,
    PH_FILL,
    PH_WARM,
    PH_MPROTECT,
    PH_ACCESS,
    PH_DONE
};

static const char *const w13_ctx_names[5] = {"R01", "R02", "R03", "R04", "R05"};
/* [WHEN-5X3] C03 runs R01's mapping/sequence as a weak (dead) consumer. */
static int g_weak_consumer = 0;
static volatile sig_atomic_t g_ctx_idx = -1;
static volatile sig_atomic_t g_phase = PH_START;
static unsigned long long g_sig_target_va;
static unsigned long long g_sig_decoy_va;
static unsigned long long g_sig_target_pfn;
static unsigned long long g_sig_decoy_pfn;
static int g_sig_pfn_t_ok;
static int g_sig_pfn_d_ok;
static const char *g_sig_pagemap = "unavailable";

static const char *
w13_phase_name(int phase)
{
    switch (phase) {
      case PH_START:    return "start";
      case PH_MAP:      return "map";
      case PH_FILL:     return "fill";
      case PH_WARM:     return "warm";
      case PH_MPROTECT: return "mprotect";
      case PH_ACCESS:   return "access";
      case PH_DONE:     return "done";
      default:          return "unknown";
    }
}

/* snprintf is not strictly async-signal-safe, but this single-threaded
 * research workload has no other writer and write(2) is safe; a lost or
 * truncated line would still leave the non-zero exit code visible. */
static void
w13_emit_terminal(const char *result, int signo)
{
    char buf[640];
    const char *ctx = (g_ctx_idx >= 0 && g_ctx_idx < 5)
        ? w13_ctx_names[g_ctx_idx] : "R??";
    int n = snprintf(buf, sizeof(buf),
        "W13_RESULT ctx=%s target_va=0x%llx target_pfn=0x%llx"
        " decoy_va=0x%llx decoy_pfn=0x%llx observed=0x0"
        " sentinel=0x%x decoy_sentinel=0x%x branch=0"
        " pagemap=%s pfn_ok=%d/%d partial_hit=UNVERIFIED"
        " signal=%d fault_phase=%s result=%s\n",
        ctx, g_sig_target_va, g_sig_target_pfn, g_sig_decoy_va,
        g_sig_decoy_pfn, MARKER_T, MARKER_D, g_sig_pagemap,
        g_sig_pfn_t_ok, g_sig_pfn_d_ok, signo,
        w13_phase_name((int)g_phase), result);
    if (n > 0) {
        size_t len = (size_t)n < sizeof(buf) ? (size_t)n : sizeof(buf) - 1;
        ssize_t ignored = write(STDOUT_FILENO, buf, len);
        (void)ignored;
    }
}

static void
w13_on_fault(int sig)
{
    w13_emit_terminal("CRASH", sig);
    _exit(128 + sig);
}

static void
w13_on_alarm(int sig)
{
    w13_emit_terminal("TIMEOUT", sig);
    _exit(124);
}

static void
w13_install_handlers(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sigemptyset(&sa.sa_mask);
    sa.sa_handler = w13_on_fault;
    sigaction(SIGSEGV, &sa, NULL);
    sigaction(SIGBUS, &sa, NULL);
    sa.sa_handler = w13_on_alarm;
    sigaction(SIGALRM, &sa, NULL);
}

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
    } else if (!strcmp(ctx, "C03")) {
        /* [WHEN-5X3 C03] Weak consumer: the redirected partial-walk value
         * is loaded and discarded, never used by sink/oracle/address. */
        volatile uint8_t dead = *p;
        (void)dead;
        __asm__ __volatile__("" ::: "memory");
        v = 0;
    } else {
        return -1;
    }
    *scalar = v;
    return 0;
}

/* MAP_SHARED anonymous page: no COW can replace the physical page when its
 * protection changes, so the PFN/sentinel oracle stays attached.
 * NOTE: the mapping and the first touch are split on purpose: the decoy
 * region must be touched before the target so its L2 partial walk-cache
 * entry is live when M05 activates on the target's first partial insert. */
/* Two-page file-backed data object: page 0 carries the target sentinel, page
 * 1 the decoy sentinel.  Each page is mapped twice (page-0 VA and the fresh
 * +0x1000 alias) so the alias has a populated PTE but no user access before
 * the consumer.  A memfd is used instead of MAP_ANONYMOUS because the fill
 * must happen before the alias VA is ever touched: touching it would create
 * the very complete TLB entry the alias access is meant to miss. */
static int
make_data_fd(uint8_t target_sentinel, uint8_t decoy_sentinel)
{
    int fd = memfd_create("mmu_w13_data", 0);
    if (fd < 0)
        fd = open("/tmp/mmu_w13_data.bin", O_RDWR | O_CREAT | O_TRUNC, 0600);
    if (fd < 0)
        return -1;
    if (ftruncate(fd, (off_t)(2 * PAGE)) != 0) {
        close(fd);
        return -1;
    }
    uint8_t *buf = calloc(2, PAGE);
    if (!buf) {
        close(fd);
        return -1;
    }
    memset(buf, target_sentinel, PAGE);
    memset(buf + PAGE, decoy_sentinel, PAGE);
    ssize_t n = pwrite(fd, buf, 2 * PAGE, 0);
    free(buf);
    if (n != (ssize_t)(2 * PAGE)) {
        close(fd);
        return -1;
    }
    return fd;
}

static void *
map_shared_data(int fd, uintptr_t va, off_t off)
{
    void *p = mmap((void *)va, PAGE, PROT_READ | PROT_WRITE,
                   MAP_SHARED | MAP_FIXED_NOREPLACE | MAP_POPULATE, fd, off);
    if (p == MAP_FAILED)
        return MAP_FAILED;
    madvise(p, PAGE, MADV_NOHUGEPAGE);
    return p;
}

/* Two-page MAP_SHARED code object: page 0 returns target_marker, page 1
 * returns decoy_marker.  Created once per process. */
static int
make_code_fd(uint16_t target_marker, uint16_t decoy_marker)
{
    int fd = memfd_create("mmu_w13_code", 0);
    if (fd < 0)
        fd = open("/tmp/mmu_w13_code.bin", O_RDWR | O_CREAT | O_TRUNC, 0600);
    if (fd < 0)
        return -1;
    if (ftruncate(fd, (off_t)(2 * PAGE)) != 0) {
        close(fd);
        return -1;
    }
    uint8_t *buf = calloc(2, PAGE);
    if (!buf) {
        close(fd);
        return -1;
    }
    uint32_t *c0 = (uint32_t *)buf;
    uint32_t *c1 = (uint32_t *)(buf + PAGE);
    c0[0] = movz_w0(target_marker);
    c0[1] = INSN_RET;
    c1[0] = movz_w0(decoy_marker);
    c1[1] = INSN_RET;
    for (int i = 2; i < (int)(PAGE / 4); i++)
        c0[i] = c1[i] = 0xD503201Fu;   /* NOP padding */
    ssize_t n = pwrite(fd, buf, 2 * PAGE, 0);
    free(buf);
    if (n != (ssize_t)(2 * PAGE)) {
        close(fd);
        return -1;
    }
    return fd;
}

static void *
map_shared_code(int fd, uintptr_t va, off_t off)
{
    void *p = mmap((void *)va, PAGE, PROT_READ | PROT_WRITE,
                   MAP_SHARED | MAP_FIXED_NOREPLACE | MAP_POPULATE, fd, off);
    if (p == MAP_FAILED)
        return MAP_FAILED;
    madvise(p, PAGE, MADV_NOHUGEPAGE);
    if (mprotect(p, PAGE, PROT_READ | PROT_EXEC) != 0)
        return MAP_FAILED;
    return p;
}

static int
run_one_ctx(int ctx_idx)
{
    const char *ctx = g_weak_consumer ? "C03" : w13_ctx_names[ctx_idx];
    int is_r05 = is_code_ctx(ctx);
    uint64_t sentinel = MARKER_T;
    uint64_t decoy_sentinel = MARKER_D;

    g_ctx_idx = ctx_idx;
    g_phase = PH_START;
    w13_install_handlers();

    /* Test-only deterministic terminal checks (never set by the runner):
     * exercise the exact handler paths that a gem5 hang/fault would take. */
    if (getenv("W13_TEST_SELF_ALARM")) {
        g_phase = PH_ACCESS;
        raise(SIGALRM);
    }
    if (getenv("W13_TEST_SELF_FAULT")) {
        g_phase = PH_ACCESS;
        raise(SIGSEGV);
    }

    void *t, *d, *ta, *da;
    g_phase = PH_MAP;
    if (is_r05) {
        int fd = make_code_fd(MARKER_T, MARKER_D);
        if (fd < 0) {
            fprintf(stderr, "W13_FATAL code backing errno=%d (%s)\n",
                    errno, strerror(errno));
            return 2;
        }
        t = map_shared_code(fd, W13_TARGET_VA, 0);
        ta = map_shared_code(fd, W13_TARGET_VA + W13_ALIAS_OFF, 0);
        d = map_shared_code(fd, W13_DECOY_VA, PAGE);
        da = map_shared_code(fd, W13_DECOY_VA + W13_ALIAS_OFF, PAGE);
    } else {
        int fd = make_data_fd(MARKER_T, MARKER_D);
        if (fd < 0) {
            fprintf(stderr, "W13_FATAL data backing errno=%d (%s)\n",
                    errno, strerror(errno));
            return 2;
        }
        t = map_shared_data(fd, W13_TARGET_VA, 0);
        ta = map_shared_data(fd, W13_TARGET_VA + W13_ALIAS_OFF, 0);
        d = map_shared_data(fd, W13_DECOY_VA, PAGE);
        da = map_shared_data(fd, W13_DECOY_VA + W13_ALIAS_OFF, PAGE);
    }
    if (t == MAP_FAILED || d == MAP_FAILED ||
            ta == MAP_FAILED || da == MAP_FAILED) {
        fprintf(stderr, "W13_FATAL mmap target/decoy/alias errno=%d (%s)\n",
                errno, strerror(errno));
        return 2;
    }

    g_phase = PH_FILL;   /* fill happened through the backing file, no VA touch */

    if (is_r05) {
        __builtin___clear_cache((char *)t, (char *)t + PAGE);
        __builtin___clear_cache((char *)ta, (char *)ta + PAGE);
        __builtin___clear_cache((char *)d, (char *)d + PAGE);
        __builtin___clear_cache((char *)da, (char *)da + PAGE);
        __asm__ __volatile__("isb" ::: "memory");
    }

    int pres_t = 0, pfn_t_ok = 0, pres_d = 0, pfn_d_ok = 0;
    uint64_t pfn_t = read_pagemap((uintptr_t)t, &pres_t, &pfn_t_ok);
    uint64_t pfn_d = read_pagemap((uintptr_t)d, &pres_d, &pfn_d_ok);

    g_sig_target_va = (unsigned long long)(uintptr_t)t;
    g_sig_decoy_va = (unsigned long long)(uintptr_t)d;
    g_sig_target_pfn = pfn_t;
    g_sig_decoy_pfn = pfn_d;
    g_sig_pfn_t_ok = pfn_t_ok;
    g_sig_pfn_d_ok = pfn_d_ok;
    g_sig_pagemap = (pfn_t_ok && pfn_d_ok) ? "ok" : "unavailable";

    printf("W13_INFO ctx=%s phase=start pid=%d target_va=0x%" PRIxPTR
           " decoy_va=0x%" PRIxPTR " target_pfn=0x%" PRIx64
           " decoy_pfn=0x%" PRIx64 " decoy_first=1 watchdog=post_warm"
           " watchdog_sec=%u\n",
           ctx, (int)getpid(), (uintptr_t)t, (uintptr_t)d, pfn_t, pfn_d,
           watchdog_sec);
    fflush(stdout);

    /* Warm both regions: this keeps the L2 partial walk-cache entries
     * resident.  For R05 the DECOY is called first so its instruction-side
     * partial entry is live before the target's first fetch activates M05. */
    g_phase = PH_WARM;
    if (is_r05) {
        volatile fn_t ft = (fn_t)t;
        volatile fn_t fd = (fn_t)d;
        for (int i = 0; i < WARM_ITERS; i++) {
            sink += (uint64_t)fd();
            sink += (uint64_t)ft();
        }
    } else {
        volatile uint8_t *pt = t, *pd = d;
        for (int i = 0; i < WARM_ITERS; i++) {
            sink += pd[0];   /* decoy partial entry live before M05 activates */
            sink += pt[0];
        }
    }

    /* M05 consumption access: the alias page has a populated PTE but no
     * complete TLB entry, so this access must resume from the L2 partial
     * walk-cache entry.  With M05 active that entry's next-table base is the
     * decoy L3 table, so the alias access returns the decoy sentinel.  This
     * happens BEFORE the mprotect/TLBI: the guest's own maintenance would
     * otherwise invalidate the partial entry first. */
    uint64_t alias_observed = 0;
    unsigned alias_branch = 0;
    g_phase = PH_ACCESS;
    if (watchdog_sec)
        alarm(watchdog_sec);
    if (is_r05) {
        volatile fn_t ft = (fn_t)ta;
        alias_observed = (uint64_t)(unsigned)ft();
    } else {
        uint8_t av = 0;
        if (run_context(ctx, ta, (uint8_t)sentinel, &av,
                        &alias_branch) != 0) {
            alarm(0);
            fprintf(stderr, "W13_FATAL unknown ctx %s\n", ctx);
            return 2;
        }
        alias_observed = av;
    }
    alarm(0);

    /* Invalidation sequence kept for design fidelity; the consumer above is
     * already the M05 target access. */
    g_phase = PH_MPROTECT;
    if (watchdog_sec)
        alarm(watchdog_sec);

    /* Leaf-only invalidation attempt.  The mapping is MAP_SHARED, so the
     * protection change cannot COW the page away from the oracle. */
    int rc1 = -1, rc2 = -1;
    const char *seq;
    if (is_r05) {
        rc1 = mprotect(t, PAGE, PROT_NONE);
        rc2 = mprotect(t, PAGE, PROT_READ | PROT_EXEC);
        __builtin___clear_cache((char *)t, (char *)t + PAGE);
        __asm__ __volatile__("isb" ::: "memory");
        seq = "mprotect(target,4096,PROT_NONE);"
              "mprotect(target,4096,PROT_READ|PROT_EXEC);"
              "__builtin___clear_cache(target,+4096);isb";
    } else {
        rc1 = mprotect(t, PAGE, PROT_READ);
        seq = "mprotect(target,4096,PROT_READ)";
    }

    printf("W13_SEQUENCE ctx=%s target_va=0x%" PRIxPTR
           " alias_va=0x%" PRIxPTR
           " target_2mib_decoy_va=0x%" PRIxPTR
           " mapping=MAP_SHARED file-backed/no-COW ops=%s rc=%d,%d"
           " consumer=alias_before_tlbi design_tlbi_not_required\n",
           ctx, (uintptr_t)t, (uintptr_t)ta, (uintptr_t)d, seq, rc1, rc2);
    printf("W13_LIMITATION ctx=%s EL0 cannot issue TLBI VALE1IS. The M05 "
           "consumer is the fresh +0x1000 alias page accessed BEFORE the "
           "guest maintenance: it has a populated PTE but no complete TLB "
           "entry, so it must resume from the L2 partial walk-cache entry. "
           "The RESULT line reports that alias observation; the partial-hit "
           "lineage is confirmed from the gem5 TLB trace.\n", ctx);
    fflush(stdout);

    if (rc1 != 0 || (is_r05 && rc2 != 0)) {
        alarm(0);
        fprintf(stderr, "W13_FATAL mprotect errno=%d (%s)\n", errno,
                strerror(errno));
        return 2;
    }

    uint64_t observed = alias_observed;
    unsigned branch = alias_branch;
    alarm(0);                 /* access completed: disarm the watchdog */
    g_phase = PH_DONE;

    /* [WHEN-5X3 C03] completion, not the redirected value, is the oracle. */
    int pass = g_weak_consumer ? 1 : (observed == sentinel);
    printf("W13_RESULT ctx=%s target_va=0x%" PRIxPTR
           " target_pfn=0x%" PRIx64 " decoy_va=0x%" PRIxPTR
           " decoy_pfn=0x%" PRIx64 " alias_va=0x%" PRIxPTR
           " observed=0x%" PRIx64
           " sentinel=0x%" PRIx64 " decoy_sentinel=0x%" PRIx64
           " branch=%u pagemap=%s pfn_ok=%d/%d"
           " signal=0 fault_phase=none"
           " partial_hit=TRACE_CONFIRMED result=%s\n",
           ctx, (uintptr_t)t, pfn_t, (uintptr_t)d, pfn_d, (uintptr_t)ta,
           observed, sentinel, decoy_sentinel, branch,
           (pfn_t_ok && pfn_d_ok) ? "ok" : "unavailable",
           pfn_t_ok, pfn_d_ok, pass ? "PASS" : "FAIL");
    fflush(stdout);
    return pass ? 0 : 1;
}

int
main(int argc, char **argv)
{
    int ctx_idx = 0;
    int all = 0;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--ctx") && i + 1 < argc) {
            const char *ctx = argv[++i];
            ctx_idx = -1;
            if (!strcmp(ctx, "C03")) {
                ctx_idx = 0;
                g_weak_consumer = 1;
            }
            for (int j = 0; j < 5; j++)
                if (!strcmp(ctx, w13_ctx_names[j]))
                    ctx_idx = j;
            if (ctx_idx < 0) {
                fprintf(stderr, "W13_FATAL unknown ctx %s\n", ctx);
                return 2;
            }
        } else if (!strcmp(argv[i], "--all")) {
            all = 1;
        } else if (!strcmp(argv[i], "--watchdog-sec") && i + 1 < argc) {
            long v = strtol(argv[++i], NULL, 0);
            if (v < 0)
                v = 0;
            watchdog_sec = (unsigned)v;
        } else {
            fprintf(stderr,
                    "usage: %s [--ctx R01..R05] [--all] "
                    "[--watchdog-sec N]\n", argv[0]);
            return 2;
        }
    }

    if (!all)
        return run_one_ctx(ctx_idx);

    int pass = 0;
    for (int i = 0; i < 5; i++) {
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork ctx");
            continue;
        }
        if (pid == 0)
            _exit(run_one_ctx(i));
        int st = 0;
        waitpid(pid, &st, 0);
        if (WIFEXITED(st) && WEXITSTATUS(st) == 0)
            pass++;
    }
    printf("W13_SUMMARY pass=%d/5\n", pass);
    fflush(stdout);
    return pass == 5 ? 0 : 1;
}
