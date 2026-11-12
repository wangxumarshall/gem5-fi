// mmu_w14.c — ARM64 userland MMU-Permission-Guard workload (M07 baseline).
//
// One process owns a shared 4 KiB backing page through a read-write alias.
// For every context a child process maps a restricted alias over the SAME
// backing page, attempts one EL0 access, and reports the outcome through a
// pipe.  The child is forked so a SIGSEGV cannot kill the run.
//
//   R01 EL0 store through PROT_READ alias          (expect SIGSEGV, no change)
//   R02 EL0 atomic RMW (LDADDAL, LSE AMO) through PROT_READ alias
//   R03 EL0 LOAD through a PROT_EXEC-only (execute-only, EPAN) mapping:
//       with EPAN the kernel installs PAGE_EXECONLY, a VALID leaf descriptor
//       with AP[2:1]=10 (EL0 read/write denied, EL1 read-only) and UXN=0.
//       The load is denied by the AP permission check, NOT by an invalid
//       descriptor.  NOTE: the kernel gates this on the runtime capability
//       ARM64_HAS_EPAN (ID_AA64MMFR1_EL1.PAN >= 3).  Without it the VMA keeps
//       PAGE_READONLY_EXEC (AP[2:1]=11) and an EL0 load succeeds; the pilot
//       must therefore gate R03 on the trace pte_decode AP field.
//   R04 EL0 execute from XN mapping (PROT_READ only) of a JIT code page
//   R05 EL0 indirect-branch fetch into a VALID XN page (PROT_READ only):
//       the target comes from a runtime table and is entered with `br xN`,
//       so the EL0 instruction fetch is denied by UXN=1, NOT by an invalid
//       descriptor and NOT by PROT_NONE.
//
// No-fault golden: every context faults (SIGSEGV).  M07 inverts one grant
// decision, so an injected run has the access complete instead: R01/R02 then
// change the shared page, visible through the parent's RW alias
// (shared_changed=1); R03 reads the sentinel byte; R04/R05 execute JIT code
// and return their (distinct) markers.
//
// PASS means the NO-FAULT expectation (fault/denial) held.  An injected
// success therefore shows result=FAIL plus injected_success=1.
//
// A permission decision and a translation fault both surface as SIGSEGV, and
// Linux can report SEGV_ACCERR for either when the VMA itself lacks the
// access right (the old PROT_NONE realization did exactly that).  Therefore
// this workload additionally emits pagemap_present (the leaf PTE is valid)
// and fault_class, and the authoritative discriminator is the gem5 trace:
// pte_decode must show descriptor_type=Page with AP=00 (R03) or UXN=1 (R05).
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
/* R05 uses its own code blob at a distinct page offset so the two execute
 * contexts never share a consumer/return path even though they both map the
 * same file-backed page through different VAs. */
#define R05_CODE_OFF 0x180UL
#define INIT_U64   0x1122334455667788ULL
#define STORE_BYTE 0xC1
#define CODE_MARK 0xC7
#define R05_CODE_MARK 0x5A
#define SENTINEL_BYTE 0x88
#define EXPECT_STORE_U64 0x11223344556677C1ULL
#define EXPECT_ATOMIC_U64 0x1122334455667789ULL

#define W14_MAGIC 0x57313431u   /* "W141" */
#define MSG_FAULT 2
#define MSG_DONE  1

enum {
    PH_STORE = 1,
    PH_ATOMIC,
    PH_READ_EXECONLY,
    PH_EXEC_XN,
    PH_FETCH_XN_INDIRECT,
};

static const char *
phase_name(int phase)
{
    switch (phase) {
    case PH_STORE: return "store_ro";
    case PH_ATOMIC: return "atomic_rmw_ro";
    case PH_READ_EXECONLY: return "read_exec_only";
    case PH_EXEC_XN: return "exec_xn";
    case PH_FETCH_XN_INDIRECT: return "fetch_xn_indirect";
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
    int32_t  pte_present; /* -1 = n/a, 0 = absent, 1 = valid leaf PTE */
    int32_t  pad2;
};

static int g_outfd = -1;
static volatile sig_atomic_t g_phase = 0;
static volatile sig_atomic_t g_pte_present = -1;

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
        [PH_READ_EXECONLY] = "W14_FAULT phase=read_exec_only signal=SIGSEGV\n",
        [PH_EXEC_XN] = "W14_FAULT phase=exec_xn signal=SIGSEGV\n",
        [PH_FETCH_XN_INDIRECT] =
            "W14_FAULT phase=fetch_xn_indirect signal=SIGSEGV\n",
    };
    int ph = (int)g_phase;
    if (ph >= PH_STORE && ph <= PH_FETCH_XN_INDIRECT)
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
    m.pte_present = (int)g_pte_present;
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

/* R05's target is read from this table at run time.  Keeping it in writable
 * .bss and reading through a volatile index prevents the compiler from
 * constant-folding the address into a direct branch/call immediate. */
static uint64_t g_r05_target_table[2];

/* Enter `target` with an explicit indirect branch.  Unlike R04's
 * `fn()` function-pointer call (BLR), this uses a literal `br xN` and sets LR
 * to a local return label itself; the target instruction stream is therefore
 * reached only through the indirect-branch path. */
static int
indirect_branch_marker(uint64_t target)
{
    uint64_t result = 0;
    __asm__ __volatile__(
        "adr x9, 1f\n\t"
        "mov x30, x9\n\t"
        "br  %[tgt]\n\t"
        "1:\n\t"
        "mov %[res], x0\n\t"
        : [res] "=&r"(result)
        : [tgt] "r"(target)
        : "x0", "x9", "x30", "memory");
    return (int)(unsigned)result;
}

/* Present bit of the process's own leaf PTE.  This lets the workload itself
 * state whether the target VA has a VALID descriptor (permission fault path)
 * or an absent/invalid one (translation fault path).  Returns -1 (n/a) if
 * /proc/self/pagemap is unavailable. */
static int
pagemap_present(uintptr_t va)
{
    int fd = open("/proc/self/pagemap", O_RDONLY);
    if (fd < 0)
        return -1;
    uint64_t entry = 0;
    ssize_t n = pread(fd, &entry, sizeof(entry),
                      (off_t)((va >> 12) * sizeof(entry)));
    close(fd);
    if (n != (ssize_t)sizeof(entry))
        return -1;
    return (int)((entry >> 63) & 1);
}

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
    /* R05: distinct consumer code page entry, distinct marker. */
    uint32_t *c5 = (uint32_t *)(buf + R05_CODE_OFF);
    c5[0] = movz_w0(R05_CODE_MARK);
    c5[1] = INSN_RET;
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
    const char *prot_name = "PROT_READ";
    const char *access_name = "";
    if (!strcmp(ctx, "R01") || !strcmp(ctx, "R02")) {
        phase = PH_STORE;
        if (!strcmp(ctx, "R02"))
            phase = PH_ATOMIC;
        va = W14_RO_VA;
        prot = PROT_READ;
        access_name = phase == PH_STORE ? "store" : "atomic_rmw";
    } else if (!strcmp(ctx, "R03")) {
        /* Execute-only user mapping (CONFIG_ARM64_EPAN + runtime
         * ARM64_HAS_EPAN): valid PAGE_EXECONLY descriptor, AP[2:1]=10,
         * UXN=0.  An EL0 load must be denied by AP, not by an invalid/absent
         * descriptor.  Without the runtime EPAN capability Linux keeps
         * PAGE_READONLY_EXEC and the load succeeds -- the trace PTE is the
         * gate, not the VMA's --xp flag. */
        phase = PH_READ_EXECONLY;
        va = W14_NONE_VA;
        prot = PROT_EXEC;
        prot_name = "PROT_EXEC";
        access_name = "load";
    } else if (!strcmp(ctx, "R04")) {
        phase = PH_EXEC_XN;
        va = W14_XN_VA;
        prot = PROT_READ;
        access_name = "execute";
    } else if (!strcmp(ctx, "R05")) {
        /* Valid read-only (XN, UXN=1) page reached only through a runtime
         * table + explicit `br xN`.  Distinct VA, code blob, consumer and
         * marker from R04. */
        phase = PH_FETCH_XN_INDIRECT;
        va = W14_NONE_CODE_VA;
        prot = PROT_READ;
        access_name = "indirect_fetch";
    } else {
        _exit(2);
    }
    g_phase = phase;

    printf("W14_CHILD ctx=%s pid=%d phase=%s alias_va=0x%" PRIxPTR
           " prot=%s access=%s\n", ctx, (int)getpid(), phase_name(phase),
           va, prot_name, access_name);
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
        m.pte_present = -1;
        write_full(outfd, &m, sizeof(m));
        _exit(3);
    }

    /* Fault the leaf PTE in for real while the alias is still writable.
     * MAP_POPULATE does not install a PTE for a PROT_NONE VMA, and the gem5
     * guest leaves such a mapping with a literally zero L1 descriptor, which
     * would take a TRANSLATION fault before any permission decision.
     * mprotect() below then rewrites the permission bits (AP=00 for R03's
     * execute-only mapping, UXN=1 for R05's read-only mapping) while keeping
     * the leaf VALID + AF. */
    {
        volatile uint8_t touch = *(volatile uint8_t *)p;
        (void)touch;
    }

    if (phase == PH_EXEC_XN || phase == PH_FETCH_XN_INDIRECT) {
        /* Clean the caches while the page is still writable/executable-
         * agnostic.  mprotect() follows; the R04 call / R05 indirect branch
         * after it is the first instruction access under the restricted
         * PTE. */
        __builtin___clear_cache((char *)p + CODE_OFF,
                                (char *)p + CODE_OFF + 64);
        if (phase == PH_FETCH_XN_INDIRECT)
            __builtin___clear_cache((char *)p + R05_CODE_OFF,
                                    (char *)p + R05_CODE_OFF + 64);
        __asm__ __volatile__("isb" ::: "memory");
    }

    if (phase == PH_FETCH_XN_INDIRECT) {
        /* Compute the branch target at run time from a writable table.  This
         * happens before mprotect; the value is reloaded after it so the
         * transfer itself is a genuine table load + `br xN`. */
        g_r05_target_table[0] = 0;
        g_r05_target_table[1] = (uint64_t)(uintptr_t)((char *)p + R05_CODE_OFF);
        printf("W14_INFO ctx=R05 stage=target_computed target=0x%" PRIx64
               " source=table index=1\n", g_r05_target_table[1]);
        fflush(stdout);
    }

    /* Diagnostic witnesses are printed BEFORE mprotect.  Printing after it
     * would place the critical access in the shadow of a write() syscall:
     * the load/branch is fetched speculatively, squashed at the syscall
     * boundary, and the one-shot would be spent on a dead instruction (the
     * architectural retry then faults after the fault was consumed).
     * Keeping every syscall before mprotect makes the restricted access the
     * first post-syscall, architectural translation. */
    int pm_present = pagemap_present(va);
    g_pte_present = pm_present;
    if (phase == PH_READ_EXECONLY) {
        printf("W14_INFO ctx=R03 stage=mapping prot=PROT_EXEC access=load"
               " pte_present=%d\n", pm_present);
        fflush(stdout);
    }
    if (phase == PH_FETCH_XN_INDIRECT) {
        printf("W14_INFO ctx=R05 stage=indirect_branch insn=br target=0x%"
               PRIx64 " lr=local_label\n", g_r05_target_table[1]);
        fflush(stdout);
    }

    if (mprotect(p, PAGE, prot) != 0) {
        struct fmsg m;
        memset(&m, 0, sizeof(m));
        m.magic = W14_MAGIC;
        m.kind = MSG_DONE;
        m.phase = phase;
        m.pid = getpid();
        m.code = -errno;
        m.pte_present = -1;
        write_full(outfd, &m, sizeof(m));
        _exit(3);
    }

    /* Workload-side validity witness: a VALID leaf PTE means the MMU will
     * reach the AP/XN permission decision, whereas present=0 means the access
     * would take a TRANSLATION fault (the old PROT_NONE realization).  This
     * is diagnostic only; the trace pte_decode is authoritative.  It was
     * printed before mprotect so the restricted access is not speculated in
     * the shadow of a syscall. */
    uint64_t observed = 0;
    if (phase == PH_STORE) {
        *(volatile uint8_t *)p = STORE_BYTE;
        observed = *(volatile uint64_t *)(uintptr_t)W14_RW_VA;
    } else if (phase == PH_ATOMIC) {
        atomic_rmw((volatile uint64_t *)p);
        observed = *(volatile uint64_t *)(uintptr_t)W14_RW_VA;
    } else if (phase == PH_READ_EXECONLY) {
        /* The first access to the target VA after mprotect(PROT_EXEC): an
         * EL0 load that AP=00 must deny. */
        observed = *(volatile uint8_t *)p;
    } else if (phase == PH_EXEC_XN) {
        /* R04 (frozen): execute from a PROT_READ (XN) page via a function
         * pointer call (BLR). */
        volatile fn_t fn = (fn_t)((char *)p + CODE_OFF);
        observed = (uint64_t)(unsigned)fn();
    } else {
        /* R05: reload the target from the runtime table and enter it with a
         * literal indirect branch.  The `br` is the first instruction access
         * to this VA after mprotect(PROT_READ); UXN=1 must deny the fetch. */
        volatile uint64_t idx = 1;
        uint64_t target = ((volatile uint64_t *)g_r05_target_table)[idx];
        observed = (uint64_t)(unsigned)indirect_branch_marker(target);
        printf("W14_INFO ctx=R05 stage=executed marker=0x%" PRIx64 "\n",
               observed);
        fflush(stdout);
    }

    struct fmsg m;
    memset(&m, 0, sizeof(m));
    m.magic = W14_MAGIC;
    m.kind = MSG_DONE;
    m.phase = phase;
    m.pid = getpid();
    m.observed = observed;
    m.pte_present = pm_present;
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

    /* No-fault golden: the access must fault with a PERMISSION decision
     * (SEGV_ACCERR); a translation fault would report SEGV_MAPERR.  For
     * R01/R02 the shared backing page must also remain unchanged. */
    /* The in-child SIGSEGV handler converts the fault into _exit(70), so the
     * pipe message is authoritative for the delivered signal. */
    int effective_sig = got_fault ? m.signo : sig;
    int fault_code_ok = !got_fault ||
                        (m.signo == SIGSEGV && m.code == SEGV_ACCERR);
    int pass = (got_fault && m.signo == SIGSEGV && m.code == SEGV_ACCERR) ||
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

    uint64_t expected;
    switch (phase) {
    case PH_STORE:            expected = EXPECT_STORE_U64;  break;
    case PH_ATOMIC:           expected = EXPECT_ATOMIC_U64; break;
    case PH_READ_EXECONLY:    expected = SENTINEL_BYTE;     break;
    case PH_EXEC_XN:          expected = CODE_MARK;         break;
    case PH_FETCH_XN_INDIRECT: expected = R05_CODE_MARK;     break;
    default:                  expected = 0;                 break;
    }
    const char *fault_class = "none";
    if (got_fault)
        fault_class = m.code == SEGV_ACCERR ? "permission" :
                      m.code == SEGV_MAPERR ? "translation" : "other";
    int value_ok = got_done && observed == expected;

    printf("W14_RESULT ctx=%s signal=%d phase=%s observed=0x%" PRIx64
           " observed_kind=%s si_code=%d fault_addr=0x%" PRIx64
           " fault_class=%s fault_code_ok=%d pte_present=%d"
           " shared_before=0x%" PRIx64 " shared_after=0x%" PRIx64
           " shared_changed=%d injected_success=%d expected=0x%" PRIx64
           " value_ok=%d msg=%s result=%s\n",
           ctx, effective_sig, pname, observed, obs_kind,
           got_fault ? m.code : -1, got_fault ? m.addr : 0,
           fault_class, fault_code_ok, m.pte_present,
           (uint64_t)INIT_U64, shared_after, shared_changed, injected,
           expected, value_ok,
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
