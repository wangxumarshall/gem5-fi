// mmu_w10s.c — ARM64 userland MMU-PTW Store variant (W10 successor, M08/M06-R02).
//
// W10 (read side) is left untouched.  This workload reuses W10's layout:
// a large file-backed buffer is populated through an alias, pagemap finds a
// pair of 4 KiB pages whose PFNs differ by XOR 1, and the target page is
// mapped at a runtime-selected VA with MAP_POPULATE so its leaf PTE exists
// before the first user access.
//
// Formal variants (Excel WorkloadID stays W10):
//   M06 R02  W10S-COLD-STORE  --cold --target-va 0x4001100000
//   M08 R05  W10S-WARM-STORE  --warm --target-va 0x4001400000
//
// Layout / VA design relation:
//   target VA   --target-va    (default 0x4001400000) -> target page, 0x7D
//   neighbor VA = target VA + W10S_NEIGH_DELTA (0x200000, 2 MiB, page
//                 aligned, documented constant; never equal to target)
//                              -> neighbor page (PFN == target_pfn ^ 1), 0x51
//   buffer VA   --buffer-va    (default 0x4002000000) -> base of the
//                              file-backed allocation used to discover the
//                              XOR1 PFN pair.  It must not overlap target or
//                              neighbor.
//
// The workload performs one real 8-bit store of 0xAB to the target VA and a
// DSB SY, then reads back through (a) the target VA and (b) the neighbor-page
// alias.
//
// Modes (--warm default / --cold):
//   --warm : the target VA is read warm_iters times first, so the store is a
//            target-relevant DTLB hit.  M08 (store redirect) should make the
//            neighbor alias read 0xAB while the target stays 0x7D.
//   --cold : no user access to the target VA before the store; the target
//            mmap (MAP_POPULATE, so the leaf PTE exists) is issued as the
//            last libc call before the STRB, and every printf is emitted
//            after the store.  The store is therefore the first translation
//            of the target VA and triggers a cold write walk.  M06 R02 (EL0
//            write, clear leaf valid bit) can therefore be targeted.  This
//            ordering matters: a gem5 O3 wrong-path strlen from the old
//            pre-store printf used to translate the VA, fill the TLB and
//            make the store a hit (see M06_R02_COLD_FINDING.md).
//
// No-fault golden (both modes):
//   target_observed=0xab  neighbor_alias_observed=0x51  store_fault=0
//   result=PASS
//
// Output order: W10S_ALLOC, then the store and DSB, then W10S_STORE (which
// still reports the pre-store captures target_before/neighbor_before), then
// W10S_RESULT.
//
// M08 redirect signature: target_observed=0x7d neighbor_alias_observed=0xab.
// A SIGSEGV/SIGBUS during the store/readback (e.g. M06 translation fault) is
// caught with sigsetjmp/siglongjmp so the result line is still printed:
//   store_fault=11 fault_phase=store  m06_write_fault_signature=1
//
// Pagemap PFNs are only readable by root/CAP_SYS_ADMIN.  Without them the
// workload reports pagemap=unavailable and result=BLOCKED; it never claims a
// verified XOR1 pair it could not observe.
//
// Build: gcc -O2 -static -march=armv8-a+simd -o mmu_w10s mmu_w10s.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <setjmp.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <unistd.h>

#define PAGE 4096UL
#define PAGES_DEFAULT 4096UL           /* W10 formal sample page count */
#define PAGES_MAX 65536UL              /* 256 MiB hard cap */

/* Defaults are macros so tools/mmu_formal_preflight.py can discover them. */
#define W10S_TARGET_VA 0x4001400000UL  /* M08 R05 default */
#define W10S_BUF_VA    0x4002000000UL
#define W10S_NEIGH_DELTA 0x200000UL    /* neighbor = target + 2 MiB */

#define TARGET_SENTINEL 0x7D
#define NEIGH_SENTINEL  0x51
#define STORE_MARKER    0xAB
#define WARM_ITERS      128            /* real target-relevant DTLB warm-up */

static volatile uint64_t sink;
static int pm_fd = -1;

static sigjmp_buf fault_jb;
static volatile sig_atomic_t g_fault_phase;
static volatile sig_atomic_t g_fault_sig;
static volatile uintptr_t g_fault_addr;

enum { FP_NONE = 0, FP_STORE = 1, FP_READ_TARGET = 2, FP_READ_NEIGH = 3 };

static const char *
fault_phase_name(int p)
{
    switch (p) {
    case FP_STORE: return "store";
    case FP_READ_TARGET: return "read_target";
    case FP_READ_NEIGH: return "read_neighbor_alias";
    default: return "none";
    }
}

static void
segv_handler(int sig, siginfo_t *si, void *uc)
{
    (void)uc;
    g_fault_sig = sig;
    g_fault_addr = (uintptr_t)si->si_addr;
    siglongjmp(fault_jb, 1);
}

static void
install_fault_handler(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = segv_handler;
    sa.sa_flags = SA_SIGINFO | SA_NODEFER;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGSEGV, &sa, NULL);
    sigaction(SIGBUS, &sa, NULL);
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

static int
read_pagemap_block(uintptr_t base_va, size_t pages, uint64_t *out)
{
    if (pm_fd < 0)
        pm_fd = open("/proc/self/pagemap", O_RDONLY);
    if (pm_fd < 0)
        return -1;
    off_t off = (off_t)((base_va >> 12) * 8);
    size_t bytes = pages * sizeof(uint64_t);
    ssize_t n = pread(pm_fd, out, bytes, off);
    return n == (ssize_t)bytes ? 0 : -1;
}

typedef struct {
    uint64_t pfn;
    uint32_t idx;
} PfnIdx;

static int
cmp_pfn(const void *a, const void *b)
{
    const PfnIdx *x = a, *y = b;
    if (x->pfn < y->pfn) return -1;
    if (x->pfn > y->pfn) return 1;
    return 0;
}

static int
ranges_overlap(uintptr_t a, size_t alen, uintptr_t b, size_t blen)
{
    return a < b + blen && b < a + alen;
}

static const char *
pagemap_status(int ok)
{
    return ok ? "ok" : "unavailable";
}

int
main(int argc, char **argv)
{
    const char *volatile mode = "warm";
    volatile size_t pages_req = PAGES_DEFAULT;
    volatile size_t max_pages = PAGES_MAX;
    volatile uintptr_t target_va = W10S_TARGET_VA;
    volatile uintptr_t buffer_va = W10S_BUF_VA;
    volatile int selftest_store_fault = 0;
    const char *file_dir = "/tmp";

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--warm"))
            mode = "warm";
        else if (!strcmp(argv[i], "--cold"))
            mode = "cold";
        else if (!strcmp(argv[i], "--pages") && i + 1 < argc)
            pages_req = strtoul(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--max-pages") && i + 1 < argc)
            max_pages = strtoul(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--target-va") && i + 1 < argc)
            target_va = (uintptr_t)strtoull(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--buffer-va") && i + 1 < argc)
            buffer_va = (uintptr_t)strtoull(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--file-dir") && i + 1 < argc)
            file_dir = argv[++i];
        else if (!strcmp(argv[i], "--ctx") && i + 1 < argc) {
            /* Alias for harness compatibility: R02 = EL0 write = cold walk,
             * R05 = warm store arm. */
            mode = !strcmp(argv[++i], "R02") ? "cold" : "warm";
        } else if (!strcmp(argv[i], "--selftest-store-fault")) {
            /* Native verification only: mprotect the target page just before
             * the store to prove the SIGSEGV capture emits the result line.
             * Never used by formal gem5 samples. */
            selftest_store_fault = 1;
        } else {
            fprintf(stderr, "usage: %s [--warm|--cold|--ctx R02|R05]"
                    " [--target-va 0x...] [--buffer-va 0x...]"
                    " [--file-dir DIR] [--pages N] [--max-pages N]"
                    " [--selftest-store-fault]\n", argv[0]);
            return 2;
        }
    }
    if (max_pages < 1 || max_pages > PAGES_MAX) {
        fprintf(stderr, "W10S_FATAL bad --max-pages %zu (1..%lu)\n",
                max_pages, (unsigned long)PAGES_MAX);
        return 2;
    }
    if (pages_req < 1 || pages_req > max_pages) {
        fprintf(stderr, "W10S_FATAL bad --pages %zu (1..%zu)\n",
                pages_req, max_pages);
        return 2;
    }
    if ((target_va & (PAGE - 1)) != 0) {
        fprintf(stderr, "W10S_FATAL --target-va 0x%" PRIxPTR
                " not 4 KiB aligned\n", target_va);
        return 2;
    }
    if ((buffer_va & (PAGE - 1)) != 0) {
        fprintf(stderr, "W10S_FATAL --buffer-va 0x%" PRIxPTR
                " not 4 KiB aligned\n", buffer_va);
        return 2;
    }

    /* Documented design relation: neighbor = target + W10S_NEIGH_DELTA. */
    uintptr_t neighbor_va = target_va + W10S_NEIGH_DELTA;
    if (neighbor_va <= target_va) {
        fprintf(stderr, "W10S_FATAL neighbor VA overflow\n");
        return 2;
    }

    /* The buffer may expand to PAGES_MAX, so reserve/validate that extent
     * against target and neighbor up front.  The neighbor alias maps the
     * neighbor page at neighbor_va, so the two single-page ranges cover the
     * complete set of distinct VAs this program uses. */
    size_t buf_reserve = max_pages * PAGE;
    if (target_va == buffer_va || neighbor_va == buffer_va ||
        ranges_overlap(buffer_va, buf_reserve, target_va, PAGE) ||
        ranges_overlap(buffer_va, buf_reserve, neighbor_va, PAGE) ||
        ranges_overlap(target_va, PAGE, neighbor_va, PAGE)) {
        fprintf(stderr, "W10S_FATAL VA overlap: target=0x%" PRIxPTR
                " neighbor=0x%" PRIxPTR " buffer=0x%" PRIxPTR
                " buffer_extent=0x%zx\n", target_va, neighbor_va, buffer_va,
                buf_reserve);
        return 2;
    }

    int cold = !strcmp(mode, "cold");

    /* Per-process file: parallel host runs must not share a backing file. */
    char path[256];
    int pn = snprintf(path, sizeof(path), "%s/mmu_w10s_pages.%ld.bin",
                      file_dir, (long)getpid());
    if (pn < 0 || (size_t)pn >= sizeof(path)) {
        fprintf(stderr, "W10S_FATAL --file-dir too long\n");
        return 2;
    }
    unlink(path);
    int fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0600);
    if (fd < 0) {
        perror("open");
        return 2;
    }
    unlink(path);   /* anonymous: disappears even if the run is killed */

    volatile uint8_t *buf = MAP_FAILED;
    size_t pages = pages_req;
    size_t total = pages * PAGE;
    int attempts = 0;
    int found = 0;
    int pm_available = 0;   /* pagemap PFNs were readable */
    int pm_unavailable = 0; /* pagemap present but PFNs hidden/zero */
    uint32_t nvalid = 0, npresent = 0;
    uint32_t tgt = 0, neigh = 0;
    uint64_t pfn_t = 0, pfn_n = 0;
    uint64_t *ents = NULL;
    PfnIdx *arr = NULL;

    size_t prev_total = 0;

    for (;;) {
        attempts++;
        total = pages * PAGE;
        if (ftruncate(fd, (off_t)total) != 0) {
            perror("ftruncate");
            return 2;
        }
        if (buf != MAP_FAILED && prev_total)
            munmap((void *)buf, prev_total);

        buf = mmap((void *)buffer_va, total, PROT_READ | PROT_WRITE,
                   MAP_SHARED | MAP_FIXED_NOREPLACE | MAP_POPULATE, fd, 0);
        if (buf == MAP_FAILED) {
            fprintf(stderr, "W10S_FATAL buffer mmap va=0x%" PRIxPTR
                    " len=%zu errno=%d (%s)\n", buffer_va, total, errno,
                    strerror(errno));
            return 2;
        }
        prev_total = total;
        madvise((void *)buf, total, MADV_NOHUGEPAGE);

        for (size_t i = 0; i < pages; i++)
            memset((void *)(buf + i * PAGE), (uint8_t)(0x5A ^ (i & 0xFF)),
                   PAGE);
        msync((void *)buf, total, MS_ASYNC);

        if (!ents)
            ents = calloc(PAGES_MAX, sizeof(*ents));
        if (!arr)
            arr = calloc(PAGES_MAX, sizeof(*arr));
        if (!ents || !arr) {
            perror("calloc");
            return 2;
        }

        if (read_pagemap_block((uintptr_t)buf, pages, ents) != 0) {
            pm_unavailable = 1;
            printf("W10S_ALLOC attempt=%d pages=%zu valid_pages=0 "
                   "pagemap=unavailable pair=UNAVAILABLE\n", attempts, pages);
            fflush(stdout);
            break;
        }
        pm_available = 1;
        nvalid = 0;
        npresent = 0;
        for (size_t i = 0; i < pages; i++) {
            int present = (int)((ents[i] >> 63) & 1);
            uint64_t pfn = ents[i] & ((1ULL << 55) - 1);
            if (present)
                npresent++;
            if (present && pfn) {
                arr[nvalid].pfn = pfn;
                arr[nvalid].idx = (uint32_t)i;
                nvalid++;
            }
        }
        qsort(arr, nvalid, sizeof(*arr), cmp_pfn);

        found = 0;
        for (uint32_t i = 0; i + 1 < nvalid; i++) {
            if ((arr[i].pfn ^ 1ULL) == arr[i + 1].pfn) {
                tgt = arr[i].idx;
                neigh = arr[i + 1].idx;
                pfn_t = arr[i].pfn;
                pfn_n = arr[i + 1].pfn;
                found = 1;
                break;
            }
        }

        /* PFNs zeroed with present PTEs (unprivileged pagemap) can never
         * yield a pair; report that honestly instead of expanding. */
        if (!found && npresent > 0 && nvalid == 0) {
            pm_unavailable = 1;
            pm_available = 0;
            printf("W10S_ALLOC attempt=%d pages=%zu present_pages=%u "
                   "valid_pages=0 pagemap=unavailable pair=UNAVAILABLE\n",
                   attempts, pages, npresent);
            fflush(stdout);
            break;
        }

        printf("W10S_ALLOC attempt=%d pages=%zu present_pages=%u "
               "valid_pages=%u pair=%s\n", attempts, pages, npresent,
               nvalid, found ? "FOUND" : "NOT_FOUND");
        fflush(stdout);
        if (found)
            break;
        if (pages >= max_pages)
            break;
        volatile size_t next = pages * 2;
        if (next > max_pages)
            next = max_pages;
        pages = next;
    }

    if (!found) {
        printf("W10S_RESULT mode=%s target_va=0x%" PRIxPTR
               " neighbor_va=0x%" PRIxPTR " buffer_va=0x%" PRIxPTR
               " pages_requested=%zu max_pages=%zu pages=%zu attempts=%d"
               " pfn_xor1_pair=%s valid_pages=%u pagemap=%s"
               " pfn_ok=0/0 result=BLOCKED\n",
               mode, target_va, neighbor_va, buffer_va, pages_req, max_pages,
               pages, attempts, pm_unavailable ? "UNAVAILABLE" : "NOT_FOUND",
               nvalid, pagemap_status(pm_available));
        fflush(stdout);
        free(ents);
        free(arr);
        if (buf != MAP_FAILED)
            munmap((void *)buf, total);
        close(fd);
        return 3;
    }
    free(ents);
    free(arr);

    /* Attach the requested sentinels through the buffer alias. */
    memset((void *)(buf + (uint64_t)tgt * PAGE), TARGET_SENTINEL, PAGE);
    memset((void *)(buf + (uint64_t)neigh * PAGE), NEIGH_SENTINEL, PAGE);
    msync((void *)buf, total, MS_SYNC);

    /* The neighbor is a distinct VA and is never the target page, so its
     * alias may be mapped and read before the target mapping exists. */
    volatile uint8_t *neigh_alias = mmap((void *)neighbor_va, PAGE,
                                         PROT_READ | PROT_WRITE,
                                         MAP_SHARED | MAP_FIXED_NOREPLACE |
                                         MAP_POPULATE, fd,
                                         (off_t)neigh * PAGE);
    if (neigh_alias == MAP_FAILED) {
        fprintf(stderr, "W10S_FATAL neighbor alias mmap neighbor=0x%" PRIxPTR
                " errno=%d (%s)\n", neighbor_va, errno, strerror(errno));
        return 2;
    }
    madvise((void *)neigh_alias, PAGE, MADV_NOHUGEPAGE);

    /* Warm mode needs the target mapped before its warm-up reads.  Cold
     * mode defers the target mmap to the last statement before the store
     * (inside the fault-capture block below), so that nothing executed in
     * between can create any translation of the target VA. */
    volatile uint8_t *volatile target = MAP_FAILED;
    if (!cold) {
        target = mmap((void *)target_va, PAGE, PROT_READ | PROT_WRITE,
                      MAP_SHARED | MAP_FIXED_NOREPLACE | MAP_POPULATE, fd,
                      (off_t)tgt * PAGE);
        if (target == MAP_FAILED) {
            fprintf(stderr, "W10S_FATAL target mmap target=0x%" PRIxPTR
                    " errno=%d (%s)\n", target_va, errno, strerror(errno));
            return 2;
        }
        madvise((void *)target, PAGE, MADV_NOHUGEPAGE);
    }

    /* Capture pre-store state through the buffer alias and the neighbor
     * alias only; the target VA stays untouched in cold mode.  The values
     * are printed after the store (see below) so that no printf-family or
     * strlen-path libc code runs before the store. */
    uint8_t tgt_pre = buf[(uint64_t)tgt * PAGE];
    uint8_t neigh_pre = neigh_alias[0];

    if (!cold) {
        /* Warm the target VA: the store becomes a target-relevant DTLB hit. */
        for (int i = 0; i < WARM_ITERS; i++)
            sink += target[0];
    }

    volatile uint8_t target_obs = 0, neigh_obs = 0;
    volatile int fault_sig = 0;
    volatile int fault_phase = FP_NONE;
    volatile uintptr_t fault_addr = 0;

    if (sigsetjmp(fault_jb, 1) == 0) {
        install_fault_handler();
        if (cold) {
            /* M06 R02 cold store.  MAP_POPULATE installs the leaf PTE (so
             * the walk decodes a valid L3 Page descriptor) without a user
             * TLB entry.  From this mmap to the STRB below the code path
             * contains no libc call at all: a gem5 O3 wrong-path strlen
             * (printf path) on this VA previously filled the TLB before
             * the store, so the store hit the TLB and never walked. */
            target = mmap((void *)target_va, PAGE, PROT_READ | PROT_WRITE,
                          MAP_SHARED | MAP_FIXED_NOREPLACE | MAP_POPULATE,
                          fd, (off_t)tgt * PAGE);
            if (target == MAP_FAILED) {
                fprintf(stderr, "W10S_FATAL target mmap target=0x%" PRIxPTR
                        " errno=%d (%s)\n", target_va, errno,
                        strerror(errno));
                return 2;
            }
        }
        if (selftest_store_fault &&
            mprotect((void *)target, PAGE, PROT_NONE) != 0) {
            fprintf(stderr, "W10S_FATAL selftest mprotect errno=%d (%s)\n",
                    errno, strerror(errno));
            return 2;
        }
        g_fault_phase = FP_STORE;
        __asm__ __volatile__("dsb sy" ::: "memory");
        target[0] = STORE_MARKER;              /* real 8-bit STRB */
        __asm__ __volatile__("dsb sy" ::: "memory");

        g_fault_phase = FP_READ_TARGET;
        target_obs = target[0];
        __asm__ __volatile__("dmb ld" ::: "memory");

        g_fault_phase = FP_READ_NEIGH;
        neigh_obs = neigh_alias[0];
        g_fault_phase = FP_NONE;
    } else {
        fault_sig = (int)g_fault_sig;
        fault_phase = (int)g_fault_phase;
        fault_addr = g_fault_addr;
    }

    /* Cold-mode belt-and-braces: mark the target VMA non-hugepage.  It is
     * done after the store (a file-backed MAP_SHARED mapping is never
     * khugepaged) because any libc call before the store is a wrong-path
     * strlen hazard on this exact VA. */
    if (cold && target != MAP_FAILED)
        madvise((void *)target, PAGE, MADV_NOHUGEPAGE);

    int pres_t = 0, pfn_t_ok = 0, pres_n = 0, pfn_n_ok = 0;
    uint64_t pfn_target_now = read_pagemap((uintptr_t)target, &pres_t,
                                           &pfn_t_ok);
    uint64_t pfn_neigh_now = read_pagemap((uintptr_t)neigh_alias, &pres_n,
                                          &pfn_n_ok);

    printf("W10S_STORE mode=%s target_va=0x%" PRIxPTR
           " neighbor_va=0x%" PRIxPTR " buffer_va=0x%" PRIxPTR
           " max_pages=%zu pages=%zu attempts=%d"
           " target_pfn=0x%" PRIx64 " neighbor_pfn=0x%" PRIx64
           " pair_xor1=%d target_before=0x%02x neighbor_before=0x%02x"
           " warm_iters=%d walk=%s\n",
           mode, target_va, neighbor_va, buffer_va, max_pages, pages, attempts,
           pfn_t, pfn_n, (int)((pfn_t ^ 1ULL) == pfn_n), tgt_pre, neigh_pre,
           cold ? 0 : WARM_ITERS, cold ? "cold_write" : "warm_hit");
    fflush(stdout);

    int pass = (fault_sig == 0) &&
               (target_obs == STORE_MARKER) &&
               (neigh_obs == NEIGH_SENTINEL);
    int m08_sig = (fault_sig == 0) &&
                  (neigh_obs == STORE_MARKER) &&
                  (target_obs == TARGET_SENTINEL);
    int m06_sig = cold && (fault_sig != 0) && (fault_phase == FP_STORE);

    printf("W10S_RESULT mode=%s target_va=0x%" PRIxPTR
           " neighbor_va=0x%" PRIxPTR
           " neighbor_alias_va=0x%" PRIxPTR
           " buffer_va=0x%" PRIxPTR
           " pages_requested=%zu max_pages=%zu pages=%zu attempts=%d"
           " target_pfn=0x%" PRIx64 " neighbor_pfn=0x%" PRIx64
           " pair_xor1=%d stored=0x%02x"
           " target_before=0x%02x target_after=0x%02x"
           " neighbor_before=0x%02x neighbor_after=0x%02x"
           " target_observed=0x%02x neighbor_alias_observed=0x%02x"
           " store_fault=%d fault_phase=%s fault_addr=0x%" PRIxPTR
           " pagemap=%s pfn_ok=%d/%d pfn_match=%d"
           " walk=%s warm_iters=%d"
           " m08_redirect_signature=%d m06_write_fault_signature=%d"
           " selftest_store_fault=%d result=%s\n",
           mode, target_va, neighbor_va, neighbor_va, buffer_va,
           pages_req, max_pages, pages, attempts, pfn_t, pfn_n,
           (int)((pfn_t ^ 1ULL) == pfn_n), STORE_MARKER,
           tgt_pre, (unsigned)target_obs,
           neigh_pre, (unsigned)neigh_obs,
           (unsigned)target_obs, (unsigned)neigh_obs,
           (int)fault_sig, fault_phase_name((int)fault_phase),
           (uintptr_t)fault_addr,
           pagemap_status(pm_available), pfn_t_ok, pfn_n_ok,
           (int)((pfn_target_now == pfn_t) && (pfn_neigh_now == pfn_n)),
           cold ? "cold_write" : "warm_hit", cold ? 0 : WARM_ITERS,
           m08_sig, m06_sig, (int)selftest_store_fault,
           pass ? "PASS" : "FAIL");
    fflush(stdout);

    close(fd);
    return pass ? 0 : 1;
}
