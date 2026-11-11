// mmu_w14.c — ARM64 userland MMU-Permission-Guard workload (M07 baseline).
//
// One process owns a shared 4 KiB backing page through a read-write alias.
// For every context a child process maps a restricted alias over the SAME
// backing page, attempts one EL0 access, and reports the outcome through a
// pipe.  The child is forked so a SIGSEGV cannot kill the run.
//
//   R01 EL0 store through PROT_READ alias          (expect SIGSEGV, no change)
//   R02 EL0 atomic RMW (LDADDAL, LSE AMO) through PROT_READ alias
//   R03 EL0 read through PROT_NONE mapping
//   R04 EL0 execute from XN mapping (PROT_READ only) of a JIT code page
//   R05 EL0 fetch from PROT_NONE mapping of a JIT code page
//
// No-fault golden: every context faults (SIGSEGV).  M07 inverts one grant
// decision, so an injected run has the access complete instead: R01/R02 then
// change the shared page, visible through the parent's RW alias
// (shared_changed=1); R03 reads the sentinel; R04/R05 execute the JIT code
// and return its marker.
//
// PASS means the NO-FAULT expectation (fault/denial) held.  An injected
// success therefore shows result=FAIL plus injected_success=1.
//
// Build: gcc -O2 -static -march=armv8-a+simd -o mmu_w14 mmu_w14.c
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
#define W14_RW_VA        0x400C000000UL
#define W14_RO_VA        0x400D000000UL
#define W14_NONE_VA      0x400D200000UL
#define W14_XN_VA        0x400D400000UL
#define W14_NONE_CODE_VA 0x400D600000UL

#define CODE_OFF   0x100UL
#define INIT_U64   0x1122334455667788ULL
#define STORE_BYTE 0xC1
#define CODE_MARK 0xC7

#define W14_MAGIC 0x57313431u   /* "W141" */
#define MSG_FAULT 2
#define MSG_DONE  1

enum {
    PH_STORE = 1,
    PH_ATOMIC,
    PH_READ_NONE,
    PH_EXEC_XN,
    PH_FETCH_NONE,
};

static const char *
phase_name(int phase)
{
    switch (phase) {
    case PH_STORE: return "store_ro";
    case PH_ATOMIC: return "atomic_rmw_ro";
    case PH_READ_NONE: return "read_prot_none";
    case PH_EXEC_XN: return "exec_xn";
    case PH_FETCH_NONE: return "fetch_prot_none";
    default: return "unknown";
    }
}

struct fmsg {
    uint32_t magic;
    int32_t  kind;      /* MSG_FAULT or MSG_DONE */
    int32_t  signo;
    int32_t  code;      /* si_code */
    int32_t  phase;
    int32_t  pad;
    int64_t  pid;
    uint64_t addr;      /* si_addr (fault) or observed value (done) */
    uint64_t observed;
};

static int g_outfd = -1;
static volatile sig_atomic_t g_phase = 0;

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

static void
segv_handler(int sig, siginfo_t *si, void *uc)
{
    (void)uc;
    static const char *const lines[] = {
        [PH_STORE] = "W14_FAULT phase=store_ro signal=SIGSEGV\n",
        [PH_ATOMIC] = "W14_FAULT phase=atomic_rmw_ro signal=SIGSEGV\n",
        [PH_READ_NONE] = "W14_FAULT phase=read_prot_none signal=SIGSEGV\n",
        [PH_EXEC_XN] = "W14_FAULT phase=exec_xn signal=SIGSEGV\n",
        [PH_FETCH_NONE] = "W14_FAULT phase=fetch_prot_none signal=SIGSEGV\n",
    };
    int ph = (int)g_phase;
    if (ph >= PH_STORE && ph <= PH_FETCH_NONE)
        write_full(2, lines[ph], strlen(lines[ph]));

    struct fmsg m;
    memset(&m, 0, sizeof(m));
    m.magic = W14_MAGIC;
    m.kind = MSG_FAULT;
    m.signo = sig;
    m.code = si->si_code;
    m.phase = ph;
    m.pid = getpid();
    m.addr = (uint64_t)(uintptr_t)si->si_addr;
    write_full(g_outfd, &m, sizeof(m));
    _exit(70);
}

/* A true single-instruction atomic RMW (ARMv8.1 LSE LDADDAL).  Unlike an
 * LDXR/STXR pair (whose STXR is a plain Mode=Write access that hits the TLB
 * entry the LDXR just filled, so it never opens an MMU trace transaction),
 * the AMO is one memory request with Request::isAtomic() set: its first
 * access to the target VA is a TLB miss and its permission decision is the
 * model's "Atomic" class. */
static int
atomic_rmw(volatile uint64_t *p)
{
    uint64_t old;
    __asm__ __volatile__(
        ".arch_extension lse\n"
        "ldaddal %1, %0, [%2]\n"
        : "=&r"(old)
        : "r"(1ULL), "r"(p)
        : "memory");
    return 0;   /* LDADD never fails; the returned old value is not needed */
}

static uint32_t
movz_w0(uint16_t imm)
{
    return 0x52800000u | ((uint32_t)imm << 5);   /* MOVZ W0, #imm16 */
}

#define INSN_RET 0xD65F03C0u

typedef int (*fn_t)(void);

static int
make_backing(void)
{
    int fd = memfd_create("mmu_w14_shared", 0);
    if (fd < 0)
        fd = open("/tmp/mmu_w14_shared.bin", O_RDWR | O_CREAT | O_TRUNC, 0600);
    if (fd < 0)
        return -1;
    if (ftruncate(fd, (off_t)PAGE) != 0)
        return -1;
    uint8_t *buf = calloc(1, PAGE);
    if (!buf)
        return -1;
    *(uint64_t *)buf = INIT_U64;
    uint32_t *c = (uint32_t *)(buf + CODE_OFF);
    c[0] = movz_w0(CODE_MARK);
    c[1] = INSN_RET;
    ssize_t n = pwrite(fd, buf, PAGE, 0);
    free(buf);
    if (n != (ssize_t)PAGE)
        return -1;
    return fd;
}

static void
child_run(const char *ctx, int fd, int outfd)
{
    g_outfd = outfd;

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = segv_handler;
    sa.sa_flags = SA_SIGINFO;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGSEGV, &sa, NULL);

    int phase = 0;
    uintptr_t va = 0;
    int prot = PROT_READ;
    if (!strcmp(ctx, "R01") || !strcmp(ctx, "R02")) {
        phase = PH_STORE;
        if (!strcmp(ctx, "R02"))
            phase = PH_ATOMIC;
        va = W14_RO_VA;
        prot = PROT_READ;
    } else if (!strcmp(ctx, "R03")) {
        phase = PH_READ_NONE;
        va = W14_NONE_VA;
        prot = PROT_NONE;
    } else if (!strcmp(ctx, "R04")) {
        phase = PH_EXEC_XN;
        va = W14_XN_VA;
        prot = PROT_READ;
    } else if (!strcmp(ctx, "R05")) {
        phase = PH_FETCH_NONE;
        va = W14_NONE_CODE_VA;
        prot = PROT_READ;
    } else {
        _exit(2);
    }
    g_phase = phase;

    printf("W14_CHILD ctx=%s pid=%d phase=%s alias_va=0x%" PRIxPTR
           " prot=%s access=%s\n", ctx, (int)getpid(), phase_name(phase),
           va, prot == PROT_NONE ? "PROT_NONE" : "PROT_READ",
           phase == PH_STORE ? "store" :
           phase == PH_ATOMIC ? "atomic_rmw" :
           phase == PH_READ_NONE ? "load" :
           phase == PH_EXEC_XN ? "execute" : "fetch");
    fflush(stdout);

    void *p = mmap((void *)va, PAGE, PROT_READ | PROT_WRITE,
                   MAP_SHARED | MAP_FIXED_NOREPLACE | MAP_POPULATE, fd, 0);
    if (p == MAP_FAILED) {
        struct fmsg m;
        memset(&m, 0, sizeof(m));
        m.magic = W14_MAGIC;
        m.kind = MSG_DONE;
        m.phase = phase;
        m.pid = getpid();
        m.code = -errno;
        write_full(outfd, &m, sizeof(m));
        _exit(3);
    }

    /* Fault the leaf PTE in for real.  MAP_POPULATE does not install a PTE
     * for a PROT_NONE VMA, and the gem5 guest has been observed to leave
     * such a mapping with a literally zero L1 descriptor, so the access
     * would take a TRANSLATION fault before any permission decision.  The
     * read-only touch below guarantees a valid leaf PTE; mprotect() then
     * restricts it while keeping the PTE present (PTE_VALID + AF, AP set by
     * the new prot), which is what M07 needs. */
    {
        volatile uint8_t touch = *(volatile uint8_t *)p;
        (void)touch;
    }

    if (phase == PH_EXEC_XN || phase == PH_FETCH_NONE) {
        /* Clean the caches while the page is still accessible.  R05 makes
         * the page PROT_NONE only after this, so its instruction fetch is
         * the first access under the restricted PTE. */
        __builtin___clear_cache((char *)p + CODE_OFF,
                                (char *)p + CODE_OFF + 64);
        __asm__ __volatile__("isb" ::: "memory");
    }

    if (mprotect(p, PAGE, prot) != 0) {
        struct fmsg m;
        memset(&m, 0, sizeof(m));
        m.magic = W14_MAGIC;
        m.kind = MSG_DONE;
        m.phase = phase;
        m.pid = getpid();
        m.code = -errno;
        write_full(outfd, &m, sizeof(m));
        _exit(3);
    }

    uint64_t observed = 0;
    if (phase == PH_STORE) {
        *(volatile uint8_t *)p = STORE_BYTE;
        observed = *(volatile uint64_t *)(uintptr_t)W14_RW_VA;
    } else if (phase == PH_ATOMIC) {
        atomic_rmw((volatile uint64_t *)p);
        observed = *(volatile uint64_t *)(uintptr_t)W14_RW_VA;
    } else if (phase == PH_READ_NONE) {
        observed = *(volatile uint8_t *)p;
    } else {
        /* PH_EXEC_XN: execute from a PROT_READ (XN) page.
         * PH_FETCH_NONE: fetch from the now PROT_NONE page. */
        volatile fn_t fn = (fn_t)((char *)p + CODE_OFF);
        observed = (uint64_t)(unsigned)fn();
    }

    struct fmsg m;
    memset(&m, 0, sizeof(m));
    m.magic = W14_MAGIC;
    m.kind = MSG_DONE;
    m.phase = phase;
    m.pid = getpid();
    m.observed = observed;
    write_full(outfd, &m, sizeof(m));
    _exit(0);
}

static int
run_one_ctx(const char *ctx, int fd, volatile uint64_t *rw)
{
    /* Reset the shared sentinel so an injected store is unambiguous. */
    *rw = INIT_U64;
    __sync_synchronize();

    int pfd[2];
    if (pipe(pfd) != 0) {
        perror("pipe");
        return 2;
    }

    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 2;
    }
    if (pid == 0) {
        close(pfd[0]);
        child_run(ctx, fd, pfd[1]);
    }
    close(pfd[1]);

    struct fmsg m;
    memset(&m, 0, sizeof(m));
    int got = read_full(pfd[0], &m, sizeof(m));
    close(pfd[0]);

    int status = 0;
    waitpid(pid, &status, 0);

    int signaled = WIFSIGNALED(status);
    int sig = signaled ? WTERMSIG(status) : 0;
    int got_fault = (got == 0 && m.magic == W14_MAGIC && m.kind == MSG_FAULT);
    int got_done = (got == 0 && m.magic == W14_MAGIC && m.kind == MSG_DONE);

    uint64_t shared_after = *rw;
    int shared_changed = (shared_after != INIT_U64);

    int phase = got_fault || got_done || got == 0 ? m.phase : 0;
    const char *pname = phase_name(phase ? phase : 0);

    /* No-fault golden: the access must fault and, for R01/R02, the shared
     * backing page must remain unchanged. */
    /* The in-child SIGSEGV handler converts the fault into _exit(70), so the
     * pipe message is authoritative for the delivered signal. */
    int effective_sig = got_fault ? m.signo : sig;
    int pass = (got_fault && m.signo == SIGSEGV) ||
               (got != 0 && signaled && sig == SIGSEGV);
    pass = pass && !shared_changed;
    int injected = got_done;

    uint64_t observed;
    const char *obs_kind;
    if (got_fault) {
        observed = (uint64_t)(unsigned)m.code;
        obs_kind = "si_code";
    } else if (got_done) {
        observed = m.observed;
        obs_kind = "value";
    } else {
        observed = 0;
        obs_kind = "none";
    }

    printf("W14_RESULT ctx=%s signal=%d phase=%s observed=0x%" PRIx64
           " observed_kind=%s si_code=%d fault_addr=0x%" PRIx64
           " shared_before=0x%" PRIx64 " shared_after=0x%" PRIx64
           " shared_changed=%d injected_success=%d msg=%s"
           " result=%s\n",
           ctx, effective_sig, pname, observed, obs_kind,
           got_fault ? m.code : -1, got_fault ? m.addr : 0,
           (uint64_t)INIT_U64, shared_after, shared_changed, injected,
           got_fault ? "fault" : got_done ? "done" : "none",
           pass ? "PASS" : "FAIL");
    fflush(stdout);
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
        fprintf(stderr, "W14_FATAL unknown ctx %s\n", ctx);
        return 2;
    }

    int fd = make_backing();
    if (fd < 0) {
        fprintf(stderr, "W14_FATAL cannot create backing: %s\n",
                strerror(errno));
        return 2;
    }
    volatile uint64_t *rw = mmap((void *)W14_RW_VA, PAGE,
                                 PROT_READ | PROT_WRITE,
                                 MAP_SHARED | MAP_FIXED_NOREPLACE |
                                 MAP_POPULATE, fd, 0);
    if (rw == MAP_FAILED) {
        fprintf(stderr, "W14_FATAL RW alias mmap: %s\n", strerror(errno));
        return 2;
    }

    if (!all) {
        int rc = run_one_ctx(ctx, fd, rw);
        return rc;
    }

    int pass = 0;
    for (int i = 0; i < 5; i++) {
        /* run_one_ctx forks the faulting child; an extra fork isolates each
         * context's parent-side bookkeeping as well. */
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork ctx");
            continue;
        }
        if (pid == 0)
            _exit(run_one_ctx(ctxs[i], fd, rw));
        int st = 0;
        waitpid(pid, &st, 0);
        if (WIFEXITED(st) && WEXITSTATUS(st) == 0)
            pass++;
    }
    printf("W14_SUMMARY pass=%d/5\n", pass);
    fflush(stdout);
    return pass == 5 ? 0 : 1;
}
