// mmu_w11.c — ARM64 userland MMU-ASID-Context-Conflict workload (M03 baseline).
//
// Two concurrent processes, A and B, are pinned to CPU 0.  Both map the SAME
// fixed virtual address but to DIFFERENT physical pages:
//
//   process A: fixed VA -> page A (marker 0xA5); maps, warms, signals ready,
//              then waits for B to finish its setup.  When B is ready, A
//              forces a fresh full-page-table lookup for the VA and re-warms
//              it, so A's COMPLETE translation is the MRU l2_shared entry.
//              A stays alive until the parent releases it (distinct ASID);
//   process B: same fixed VA -> page B (marker 0x5A), performs ALL setup
//              (mmap/MAP_POPULATE, madvise, pagemap read, R05 cache maintenance)
//              WITHOUT touching the target VA, announces READY to A, blocks
//              until A reports REWARMED, and only then performs the single
//              target access.  B has never touched the VA in user mode, so its
//              own-ASID lookup is a normal MISS; only an injected ASID
//              false-match can select A's non-global entry and return marker A.
//
// A/B residency handshake (why it exists):
//   The M03 implementation needs a COMPLETE foreign-ASID entry resident in
//   l2_shared at B's target lookup.  In the plain W11 control, B's startup
//   (fork/exec of the child, page-table setup, cache maintenance) drives
//   enough untraced replacement to evict A's complete l2_shared entry before B
//   ever performs its lookup.  The handshake moves A's final warm to AFTER
//   B's setup and immediately before B's access, so A's entry is the newest
//   (MRU) complete entry at the lookup.
//
//   A plain repeat of the warm loop would be insufficient: once A's L1 dtb/itb
//   entry exists, every further load/execute is an L1 HIT and the l2_shared
//   entry's replacement order is never touched.  A therefore issues
//   mprotect(PROT_NONE) + mprotect(original) on its own VMA, which makes the
//   kernel execute a VA-based stage-1 TLBI (VAAE1IS: by VA, all ASID) that
//   removes the VA from BOTH the L1 TLB and l2_shared; the subsequent warm
//   then takes the full lookup path and inserts a fresh COMPLETE entry into
//   l2_shared as the MRU entry.  mprotect only changes A's own VMA, never B's.
//
// Contexts (selected with --ctx / --all):
//   R01 LDR direct                       (DTLB)
//   R02 LDR -> ADD                       (DTLB)
//   R03 LDR -> CMP -> conditional branch (DTLB)
//   R04 pointer load -> second LDR       (DTLB; A/B pointer values differ and
//       select different sentinel sub-pages so a wrong first load propagates)
//   R05 instruction fetch at the same code VA, different code bytes in A and
//       B (ITLB).  code_A returns marker A, code_B returns marker B.
//
// The backing pages live in a memfd (fallback /tmp file), prepared by the
// parent before fork, so B can map its page with MAP_POPULATE without ever
// touching the fixed VA in user mode.  This keeps B's target lookup a real
// TLB miss.
//
// ASIDs are not visible from EL0; they must be read from the gem5 trace.
// This workload prints both PIDs, both pagemap PFNs, the observed value in B
// and #PFN validity (pagemap PFNs are only readable with CAP_SYS_ADMIN,
// which root has in the gem5 FS).  Each handshake stage emits one W11_INFO
// line so the terminal ordering is visible.
//
// PASS means B observed its own marker (0x5A / code_B).
//
// Build: gcc -O2 -static -march=armv8-a+simd -o mmu_w11 mmu_w11.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define PAGE 4096UL
#define W11_DATA_VA 0x4004000000UL   /* data target VA, shared by A and B     */
#define W11_CODE_VA 0x4005000000UL   /* R05 code target VA                    */
#define W11_SENT_VA 0x4006000000UL   /* R04 two-page sentinel region          */

#define MARKER_A 0xA5
#define MARKER_B 0x5A
#define MAGIC   0x57313131u          /* "W111" */
#define HS_MAGIC 0x48533131u         /* "HS11" handshake message */

/* Initial per-process warm; small on purpose (the handshake, not the warm
 * length, is what keeps A's entry resident).  Re-warm is a fresh full-path
 * lookup performed after B's setup is complete. */
#define WARM_ITERS   512
#define REWARM_ITERS 64

/* Handshake stages. */
#define HS_A_READY   1   /* A -> parent: mapping + initial warm complete   */
#define HS_B_READY   2   /* B -> A:       B setup complete, no VA touched  */
#define HS_A_REWARMED 3  /* A -> B:       target entry re-warmed           */

static volatile uint64_t sink;
static int pm_fd = -1;

struct msg {
    uint32_t magic;
    int32_t  ok;
    int64_t  pid;
    uint64_t pfn;
    uint64_t observed;
    uint64_t branch;
    int64_t  stage;      /* 0 = access completed; negative = setup error     */
    int32_t  pagemap_ok;
    int32_t  pad;
};

struct hs {
    uint32_t magic;
    int32_t  stage;
    int64_t  pid;
    uint64_t aux;
};

static void
write_full(int fd, const void *buf, size_t len)
{
    const char *p = buf;
    while (len) {
        ssize_t n = write(fd, p, len);
        if (n <= 0) {
            if (n < 0 && errno == EINTR)
                continue;
            return;
        }
        p += n;
        len -= (size_t)n;
    }
}

static int
read_full(int fd, void *buf, size_t len)
{
    char *p = buf;
    while (len) {
        ssize_t n = read(fd, p, len);
        if (n < 0 && errno == EINTR)
            continue;
        if (n <= 0)
            return -1;
        p += n;
        len -= (size_t)n;
    }
    return 0;
}

static int
pin_cpu0(void)
{
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(0, &set);
    return sched_setaffinity(0, sizeof(set), &set);
}

static uint64_t
read_pagemap(uintptr_t va, int *present, int *pfn_ok)
{
    uint64_t entry = 0;
    *present = 0;
    *pfn_ok = 0;
    /* /proc/self/pagemap is bound to the process that opened it.  Every
     * process (parent and both children) must open its own. */
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

static int
make_backing(uint8_t *pages, size_t npages)
{
    int fd = memfd_create("mmu_w11_pages", 0);
    if (fd < 0)
        fd = open("/tmp/mmu_w11_pages.bin", O_RDWR | O_CREAT | O_TRUNC, 0600);
    if (fd < 0)
        return -1;
    if (ftruncate(fd, (off_t)(npages * PAGE)) != 0) {
        close(fd);
        return -1;
    }
    if (pwrite(fd, pages, npages * PAGE, 0) != (ssize_t)(npages * PAGE)) {
        close(fd);
        return -1;
    }
    return fd;
}

static uint32_t
movz_w0(uint16_t imm)
{
    /* MOVZ W0, #imm16 */
    return 0x52800000u | ((uint32_t)imm << 5);
}

#define INSN_RET 0xD65F03C0u

typedef int (*fn_t)(void);

static int
run_context(const char *ctx, volatile uint8_t *p, uint8_t *scalar,
            unsigned *branch)
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
        if (v == MARKER_B) {
            *branch = 1;
            sink = 0x100;
        } else {
            *branch = 2;
            sink = 0x200;
        }
    } else if (!strcmp(ctx, "R04")) {
        /* p[0..7] is a pointer to a sentinel sub-page (page A -> sentinel 0,
         * page B -> sentinel 1).  A wrong (foreign-ASID) first load therefore
         * selects marker A, not marker B. */
        uint64_t q = *(volatile uint64_t *)p;
        v = *(volatile uint8_t *)(uintptr_t)q;
        sink = v;
    } else {
        return -1;
    }
    *scalar = v;
    return 0;
}

static int
is_code_ctx(const char *ctx)
{
    return !strcmp(ctx, "R05");
}

/* One warm pass over the target page.  R05 executes the code page (ITLB),
 * every other context performs data loads (DTLB). */
static void
warm_target(const char *ctx, volatile void *p, int iters, const char *stage)
{
    if (is_code_ctx(ctx)) {
        __builtin___clear_cache((char *)p, (char *)p + PAGE);
        __asm__ __volatile__("isb" ::: "memory");
        volatile fn_t fn = (fn_t)p;
        for (int i = 0; i < iters; i++)
            sink += (uint64_t)fn();
    } else {
        volatile uint8_t *q = p;
        for (int i = 0; i < iters; i++)
            sink += q[0];
    }
    (void)stage;
}

static void
info(const char *ctx, const char *stage, uint64_t va, const char *detail)
{
    printf("W11_INFO ctx=%s stage=%s pid=%d va=0x%" PRIx64
           " handshake=ready_rewarm%s%s\n",
           ctx, stage, (int)getpid(), (uint64_t)va,
           detail && *detail ? " " : "", detail ? detail : "");
    fflush(stdout);
}

/* Fill the four backing pages for a context. */
static void
prepare_pages(const char *ctx, uint8_t *pg)
{
    memset(pg, MARKER_A, 4 * PAGE);                 /* page0: A                */
    memset(pg + PAGE, MARKER_B, 3 * PAGE);          /* page1: B; S1: B         */
    memset(pg + 2 * PAGE, MARKER_A, PAGE);          /* S0: A                   */
    memset(pg + 3 * PAGE, MARKER_B, PAGE);          /* S1: B                   */

    if (is_code_ctx(ctx)) {
        memset(pg, 0, 2 * PAGE);
        uint32_t *ca = (uint32_t *)pg;
        uint32_t *cb = (uint32_t *)(pg + PAGE);
        ca[0] = movz_w0(MARKER_A);
        ca[1] = INSN_RET;
        cb[0] = movz_w0(MARKER_B);
        cb[1] = INSN_RET;
    } else if (!strcmp(ctx, "R04")) {
        memset(pg, MARKER_A, PAGE);
        memset(pg + PAGE, MARKER_B, PAGE);
        *(volatile uint64_t *)pg = (uint64_t)W11_SENT_VA;
        *(volatile uint64_t *)(pg + PAGE) = (uint64_t)W11_SENT_VA + PAGE;
    }
}

/* Worker A: map backing page 0 at the fixed VA, warm, report ready, wait for
 * B's setup, then force a fresh full lookup + re-warm and tell B.  A stays
 * alive until the parent releases it. */
static void
child_a(const char *ctx, int fd, uintptr_t va, int ready_wr, int bready_rd,
        int rewarm_wr, int hold_rd)
{
    struct msg m;
    memset(&m, 0, sizeof(m));
    m.magic = MAGIC;
    m.pid = getpid();
    m.stage = -1;

    signal(SIGPIPE, SIG_IGN);

    if (pin_cpu0() != 0)
        fprintf(stderr, "W11_WARN A pid=%d taskset(cpu0) failed: %s\n",
                (int)getpid(), strerror(errno));

    int prot = PROT_READ | (is_code_ctx(ctx) ? PROT_EXEC : 0);
    void *p = mmap((void *)va, PAGE, prot,
                   MAP_SHARED | MAP_FIXED_NOREPLACE | MAP_POPULATE, fd, 0);
    if (p == MAP_FAILED) {
        m.ok = 0;
        write_full(ready_wr, &m, sizeof(m));
        close(ready_wr);
        _exit(3);
    }
    madvise(p, PAGE, MADV_NOHUGEPAGE);

    /* Initial warm: establishes A's translation in L1 and l2_shared. */
    warm_target(ctx, p, WARM_ITERS, "initial");

    int present = 0, pfn_ok = 0;
    m.pfn = read_pagemap(va, &present, &pfn_ok);
    m.pagemap_ok = pfn_ok;
    m.ok = 1;
    m.stage = 0;
    write_full(ready_wr, &m, sizeof(m));
    close(ready_wr);
    info(ctx, "a_ready", (uint64_t)va, "initial_warm=1");

    /* Wait until B has finished ALL of its setup. */
    struct hs h;
    memset(&h, 0, sizeof(h));
    if (read_full(bready_rd, &h, sizeof(h)) != 0 ||
        h.magic != HS_MAGIC || h.stage != HS_B_READY) {
        info(ctx, "a_b_ready_missing", (uint64_t)va, "handshake_broken=1");
        char c;
        while (read(hold_rd, &c, 1) < 0 && errno == EINTR)
            ;
        _exit(0);
    }
    close(bready_rd);
    if (!h.aux) {
        /* B reported a setup failure: nothing to re-warm. */
        info(ctx, "a_b_ready", (uint64_t)va, "b_setup_ok=0");
        char c;
        while (read(hold_rd, &c, 1) < 0 && errno == EINTR)
            ;
        _exit(0);
    }
    info(ctx, "a_b_ready", (uint64_t)va, "b_setup_ok=1");

    /* Force BOTH the L1 entry and the l2_shared entry for this VA to be
     * dropped, so the re-warm below is a genuine full lookup that inserts a
     * fresh COMPLETE entry as the MRU l2_shared entry.  A plain warm after an
     * L1 hit would leave l2_shared untouched.  mprotect affects A's VMA only.
     * The kernel performs the VA-based stage-1 TLBI (all-ASID) on each call. */
    if (mprotect(p, PAGE, PROT_NONE) != 0)
        fprintf(stderr, "W11_WARN A pid=%d mprotect(PROT_NONE) failed: %s\n",
                (int)getpid(), strerror(errno));
    if (mprotect(p, PAGE, prot) != 0)
        fprintf(stderr, "W11_WARN A pid=%d mprotect(restore) failed: %s\n",
                (int)getpid(), strerror(errno));

    warm_target(ctx, p, REWARM_ITERS, "rewarm");
    info(ctx, "a_rewarmed", (uint64_t)va, "rewarm=64 flush=mprotect");

    memset(&h, 0, sizeof(h));
    h.magic = HS_MAGIC;
    h.stage = HS_A_REWARMED;
    h.pid = getpid();
    write_full(rewarm_wr, &h, sizeof(h));
    close(rewarm_wr);

    /* Stay alive while B performs the target access. */
    char c;
    while (read(hold_rd, &c, 1) < 0 && errno == EINTR)
        ;
    info(ctx, "a_released", (uint64_t)va, "exit=0");
    _exit(0);
}

/* Worker B: map backing page 1 at the same fixed VA, finish ALL setup without
 * touching the target VA, tell A, wait for REWARMED, then do the one access. */
static void
child_b(const char *ctx, int fd, uintptr_t va, int bready_wr, int rewarm_rd,
        int res_fd)
{
    struct msg m;
    memset(&m, 0, sizeof(m));
    m.magic = MAGIC;
    m.pid = getpid();
    m.stage = -1;

    signal(SIGPIPE, SIG_IGN);

    if (pin_cpu0() != 0)
        fprintf(stderr, "W11_WARN B pid=%d taskset(cpu0) failed: %s\n",
                (int)getpid(), strerror(errno));

    int prot = PROT_READ | (is_code_ctx(ctx) ? PROT_EXEC : 0);
    void *p = mmap((void *)va, PAGE, prot,
                   MAP_SHARED | MAP_FIXED_NOREPLACE | MAP_POPULATE, fd,
                   (off_t)PAGE);
    if (p == MAP_FAILED) {
        struct hs h = { HS_MAGIC, HS_B_READY, getpid(), 0 };
        write_full(bready_wr, &h, sizeof(h));
        close(bready_wr);
        m.stage = -10;
        write_full(res_fd, &m, sizeof(m));
        _exit(3);
    }
    madvise(p, PAGE, MADV_NOHUGEPAGE);

    if (!strcmp(ctx, "R04")) {
        void *s = mmap((void *)W11_SENT_VA, 2 * PAGE, PROT_READ,
                       MAP_SHARED | MAP_FIXED_NOREPLACE | MAP_POPULATE, fd,
                       (off_t)(2 * PAGE));
        if (s == MAP_FAILED) {
            struct hs h = { HS_MAGIC, HS_B_READY, getpid(), 0 };
            write_full(bready_wr, &h, sizeof(h));
            close(bready_wr);
            m.stage = -11;
            write_full(res_fd, &m, sizeof(m));
            _exit(3);
        }
        madvise(s, 2 * PAGE, MADV_NOHUGEPAGE);
    }

    if (is_code_ctx(ctx)) {
        /* Drop any stale instruction bytes for this VA from B's I-cache.
         * This does not populate the ITLB. */
        __builtin___clear_cache((char *)p, (char *)p + PAGE);
        __asm__ __volatile__("isb" ::: "memory");
    }

    int present = 0, pfn_ok = 0;
    m.pfn = read_pagemap(va, &present, &pfn_ok);
    m.pagemap_ok = pfn_ok;

    /* ALL setup is complete and the target VA has not been touched in user
     * mode.  Announce it, then block until A has re-warmed the entry. */
    info(ctx, "b_setup_complete", (uint64_t)va, "target_untouched=1");
    struct hs h = { HS_MAGIC, HS_B_READY, getpid(), 1 };
    write_full(bready_wr, &h, sizeof(h));
    close(bready_wr);

    memset(&h, 0, sizeof(h));
    if (read_full(rewarm_rd, &h, sizeof(h)) != 0 ||
        h.magic != HS_MAGIC || h.stage != HS_A_REWARMED) {
        close(rewarm_rd);
        m.stage = -13;
        write_full(res_fd, &m, sizeof(m));
        _exit(4);
    }
    close(rewarm_rd);
    info(ctx, "b_rewarmed", (uint64_t)va, "target_access=immediate");

    /* Pipe read is a syscall barrier: access the VA immediately, no sleeps. */
    uint8_t v = 0;
    unsigned branch = 0;
    if (is_code_ctx(ctx)) {
        volatile fn_t fn = (fn_t)p;
        m.observed = (uint64_t)(unsigned)fn();
        m.branch = 0;
        m.stage = 0;
    } else if (run_context(ctx, p, &v, &branch) != 0) {
        m.stage = -12;
    } else {
        m.observed = v;
        m.branch = branch;
        m.stage = 0;
    }

    write_full(res_fd, &m, sizeof(m));
    _exit(m.stage == 0 ? 0 : 4);
}

static int
run_one_ctx(const char *ctx)
{
    int is_r05 = is_code_ctx(ctx);
    uintptr_t va = is_r05 ? W11_CODE_VA : W11_DATA_VA;

    /* Each process opens its own pagemap lazily in read_pagemap(). */

    uint8_t *pages = malloc(4 * PAGE);
    if (!pages) {
        perror("malloc");
        return 2;
    }
    prepare_pages(ctx, pages);

    int fd = make_backing(pages, 4);
    free(pages);
    if (fd < 0) {
        fprintf(stderr, "W11_FATAL cannot create backing store: %s\n",
                strerror(errno));
        return 2;
    }

    /* ready:  A -> parent (mapped + initial warm done)
     * bready: B -> A      (B setup complete)
     * rewarm: A -> B      (A re-warmed the target entry)
     * hold:   parent -> A (release A after B's result)
     * res:    B -> parent (target access result) */
    int ready_p[2], bready_p[2], rewarm_p[2], hold_p[2], res_p[2];
    if (pipe(ready_p) || pipe(bready_p) || pipe(rewarm_p) ||
        pipe(hold_p) || pipe(res_p)) {
        perror("pipe");
        close(fd);
        return 2;
    }

    pid_t a = fork();
    if (a < 0) {
        perror("fork A");
        close(fd);
        return 2;
    }
    if (a == 0) {
        close(ready_p[0]);
        close(bready_p[1]);
        close(rewarm_p[0]);
        close(hold_p[1]);
        close(res_p[0]);
        close(res_p[1]);
        child_a(ctx, fd, va, ready_p[1], bready_p[0], rewarm_p[1], hold_p[0]);
    }
    close(ready_p[1]);
    /* Parent keeps only the endpoints it needs; A owns the other side. */
    close(bready_p[0]);
    close(rewarm_p[1]);
    close(hold_p[0]);

    struct msg ma;
    memset(&ma, 0, sizeof(ma));
    if (read_full(ready_p[0], &ma, sizeof(ma)) != 0 ||
        ma.magic != MAGIC || !ma.ok) {
        fprintf(stderr, "W11_FATAL A setup failed for ctx=%s\n", ctx);
        close(ready_p[0]);
        close(bready_p[1]);
        close(rewarm_p[0]);
        close(hold_p[1]);
        close(res_p[0]);
        close(res_p[1]);
        waitpid(a, NULL, 0);
        close(fd);
        if (pm_fd >= 0) close(pm_fd);
        return 2;
    }
    close(ready_p[0]);
    info(ctx, "parent_a_ready", (uint64_t)va, "fork_b=now");

    /* A is mapped/ready; only now fork B. */
    pid_t b = fork();
    if (b < 0) {
        perror("fork B");
        close(bready_p[1]);
        close(rewarm_p[0]);
        close(hold_p[1]);
        close(res_p[0]);
        close(res_p[1]);
        waitpid(a, NULL, 0);
        return 2;
    }
    if (b == 0) {
        close(ready_p[0]);
        close(hold_p[0]);
        close(hold_p[1]);
        close(res_p[0]);
        close(bready_p[0]);
        close(rewarm_p[1]);
        child_b(ctx, fd, va, bready_p[1], rewarm_p[0], res_p[1]);
    }
    /* Parent copies of B<->A endpoints must be closed. */
    close(bready_p[1]);
    close(rewarm_p[0]);
    close(res_p[1]);

    struct msg mb;
    memset(&mb, 0, sizeof(mb));
    int got = read_full(res_p[0], &mb, sizeof(mb));
    close(res_p[0]);

    int status = 0;
    waitpid(b, &status, 0);

    /* Release A. */
    write_full(hold_p[1], "x", 1);
    close(hold_p[1]);
    waitpid(a, NULL, 0);

    if (got != 0 || mb.magic != MAGIC) {
        memset(&mb, 0, sizeof(mb));
        mb.magic = MAGIC;
        mb.stage = -100;
    }

    int signaled = WIFSIGNALED(status);
    int sig = signaled ? WTERMSIG(status) : 0;

    uint64_t expect = (uint64_t)MARKER_B;
    int pass = (mb.stage == 0) && !signaled && (mb.observed == expect);

    printf("W11_RESULT ctx=%s va=0x%" PRIxPTR
           " pid_a=%d pid_b=%d pfn_a=0x%" PRIx64 " pfn_b=0x%" PRIx64
           " pagemap=%s marker_a=0x%02x marker_b=0x%02x"
           " observed=0x%" PRIx64 " branch=%" PRIu64
           " stage=%" PRId64 " b_signal=%d asid_source=trace pin_cpu=cpu0"
           " handshake=ready_rewarm"
           " expect=0x%" PRIx64 " result=%s\n",
           ctx, va, (int)ma.pid, (int)mb.pid, ma.pfn, mb.pfn,
           (ma.pagemap_ok && mb.pagemap_ok) ? "ok" : "unavailable",
           MARKER_A, MARKER_B, mb.observed, mb.branch, mb.stage, sig,
           expect, pass ? "PASS" : "FAIL");
    fflush(stdout);

    close(fd);
    if (pm_fd >= 0) {
        close(pm_fd);
        pm_fd = -1;
    }
    return pass ? 0 : 1;
}

int
main(int argc, char **argv)
{
    const char *ctx = "R01";
    int all = 0;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--ctx") && i + 1 < argc)
            ctx = argv[++i];
        else if (!strcmp(argv[i], "--all"))
            all = 1;
        else {
            fprintf(stderr, "usage: %s [--ctx R01..R05] [--all]\n", argv[0]);
            return 2;
        }
    }

    static const char *ctxs[5] = {"R01", "R02", "R03", "R04", "R05"};
    int valid = 0;
    for (int i = 0; i < 5; i++)
        if (!strcmp(ctx, ctxs[i]))
            valid = 1;
    if (!all && !valid) {
        fprintf(stderr, "W11_FATAL unknown ctx %s\n", ctx);
        return 2;
    }

    if (!all)
        return run_one_ctx(ctx);

    /* --all: one process per context so a faulting context cannot take down
     * the rest of the run. */
    int pass = 0;
    for (int i = 0; i < 5; i++) {
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork ctx");
            continue;
        }
        if (pid == 0)
            _exit(run_one_ctx(ctxs[i]));
        int st = 0;
        waitpid(pid, &st, 0);
        if (WIFEXITED(st) && WEXITSTATUS(st) == 0)
            pass++;
    }
    printf("W11_SUMMARY pass=%d/5\n", pass);
    fflush(stdout);
    return pass == 5 ? 0 : 1;
}
