// mmu_w10.c — ARM64 userland MMU-PTW-ColdWalk workload (baseline only).
//
// A file-backed buffer is initialised through an alias mapping.  Pagemap is
// used to find a target physical page whose PFN XOR 1 is another page of the
// same buffer.  A second fixed VA is mapped to the target file page with
// MAP_POPULATE (PTE present) but is NOT loaded.  The first user load of the
// target VA must therefore be a DTLB miss whose hardware walk succeeds on an
// existing 4 KiB leaf PTE.  The baseline must read the target sentinel.
//
// new_pfn = old_pfn XOR 1 is the later M02 target; this program only records
// the pair and reads the correct sentinel.  No fault is injected.
//
// Contexts: R01 LDR, R02 LDR->ADD, R03 LDR->CMP->branch, R04 LDR->addr->LDR,
//           R05 NEON load->vector ADD.
//
// Build: gcc -O2 -static -march=armv8-a+simd -o mmu_w10 mmu_w10.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#if defined(__aarch64__)
#include <arm_neon.h>
#endif

#define PAGE 4096UL
#define PAGES_DEFAULT 32768UL          /* 128 MiB */
#define PAGES_MAX 65536UL              /* 256 MiB */
#define W10_TARGET 0x4001000000UL      /* target VA, inside 39-bit user VA */
#define W10_ALIAS  0x4002000000UL      /* alias used to initialise the buffer */
#define DRAM_BASE  0x80000000UL
#define DRAM_END   0x100000000UL

static volatile uint64_t sink;
static int pm_fd = -1;

static uint64_t
read_pagemap(uintptr_t va, int *present)
{
    uint64_t entry = 0;
    *present = 0;
    if (pm_fd < 0)
        return 0;
    off_t off = (off_t)((va >> 12) * 8);
    if (pread(pm_fd, &entry, sizeof(entry), off) != sizeof(entry))
        return 0;
    *present = (entry >> 63) & 1;
    return entry & ((1ULL << 55) - 1);
}

typedef struct {
    uint64_t pfn;
    uint32_t idx;
} PfnIdx;

// Read a contiguous run of pagemap entries with ONE pread.  The alias VA is
// contiguous, so 4096 pages cost one syscall instead of 4096.
static int
read_pagemap_block(uintptr_t base_va, size_t pages, uint64_t *out)
{
    if (pm_fd < 0)
        return -1;
    off_t off = (off_t)((base_va >> 12) * 8);
    size_t bytes = pages * sizeof(uint64_t);
    ssize_t n = pread(pm_fd, out, bytes, off);
    return n == (ssize_t)bytes ? 0 : -1;
}

static int
cmp_pfn(const void *a, const void *b)
{
    const PfnIdx *x = a, *y = b;
    if (x->pfn < y->pfn) return -1;
    if (x->pfn > y->pfn) return 1;
    return 0;
}

static void
fill_buffer(volatile uint8_t *alias, size_t pages)
{
    for (size_t i = 0; i < pages; i++) {
        uint8_t v = (uint8_t)(0x5A ^ (i & 0xFF));
        memset((void *)(alias + (uint64_t)i * PAGE), v, PAGE);
    }
}

static int
read_smaps_page_size(uintptr_t va, char *out, size_t outlen)
{
    FILE *f = fopen("/proc/self/smaps", "r");
    if (!f)
        return -1;
    char line[512];
    int in_range = 0;
    out[0] = '\0';
    while (fgets(line, sizeof(line), f)) {
        unsigned long start, end;
        if (sscanf(line, "%lx-%lx", &start, &end) == 2) {
            in_range = (va >= start && va < end);
            continue;
        }
        if (in_range && (!strncmp(line, "KernelPageSize:", 15) ||
                         !strncmp(line, "MMUPageSize:", 12))) {
            size_t n = strlen(line);
            while (n && (line[n - 1] == '\n' || line[n - 1] == ' '))
                line[--n] = '\0';
            if (strlen(out) + n + 2 < outlen) {
                if (out[0]) strncat(out, ",", outlen - strlen(out) - 1);
                strncat(out, line, outlen - strlen(out) - 1);
            }
        }
    }
    fclose(f);
    return out[0] ? 0 : -1;
}

/* Per-context target VA constants.  The target load MUST use its OWN
 * compile-time VA, not the pointer computed for the selected context: the
 * strcmp dispatch chain is only resolved in commit, so O3 executes the
 * target load of an EARLIER context block on the wrong path before the
 * branch resolves.  When every block dereferenced the same live pointer
 * (measured on TEST-M08-R02C/R03B/R04B) that wrong-path load performed the
 * cold walk first, filled the TLB of the context under test, and the
 * architecturally correct load then hit the TLB; the one-shot M08 fault
 * landed on a squashed request and was never consumed.  With a distinct
 * constant per context, a wrong-path block touches a VA that is not mapped
 * in a scoped run, so the selected context's VA is still cold when its own
 * load executes.  main() maps exactly W10_CTX_VA(idx) for the selected
 * context, and run_context() verifies the pointer matches. */
#define W10_VA_STRIDE 0x100000UL
#define W10_CTX_VA(i) (W10_TARGET + (uintptr_t)(i) * W10_VA_STRIDE)

static int ctx_index(const char *ctx);

static int
run_context(const char *ctx, volatile uint8_t *p, uint8_t expect, uint8_t *scalar,
            unsigned *branch, unsigned *vec0)
{
    uint8_t v = 0;
    *branch = 0;
    *vec0 = 0;

    const int idx = ctx_index(ctx);
    if (idx < 0) {
        fprintf(stderr, "unknown ctx %s\n", ctx);
        return -1;
    }
    if (p != (volatile uint8_t *)W10_CTX_VA(idx)) {
        fprintf(stderr, "W10_FATAL ctx=%s mapped pointer %p != constant VA "
                "0x%" PRIxPTR "\n", ctx, (const void *)p,
                (uintptr_t)W10_CTX_VA(idx));
        return -1;
    }

    if (!strcmp(ctx, "C03")) {
        /* [WHEN-5X3 C03] Real cold/warm translation whose loaded value is
         * intentionally discarded: no sink, no branch, no later address. */
        volatile uint8_t dead = *(volatile uint8_t *)W10_CTX_VA(idx);
        (void)dead;
        __asm__ __volatile__("" ::: "memory");
        *scalar = 0;
        return 0;
    } else if (idx == 0) {
        v = *(volatile uint8_t *)W10_CTX_VA(0);
        sink = v;
    } else if (idx == 1) {
        v = *(volatile uint8_t *)W10_CTX_VA(1);
        sink = (uint64_t)v + 0x11;
    } else if (idx == 2) {
        v = *(volatile uint8_t *)W10_CTX_VA(2);
        if (v == expect) {
            *branch = 1;
            sink = 0x100;
        } else {
            *branch = 2;
            sink = 0x200;
        }
        __asm__ __volatile__("" ::: "memory");
    } else if (idx == 3) {
        volatile uint8_t *tp = (volatile uint8_t *)W10_CTX_VA(3);
        v = *tp;
        volatile uint8_t *q = tp + (v & 0x0F);
        uint8_t w = *q;
        sink = w;
    } else {
#if defined(__aarch64__)
        uint8x16_t vec = vld1q_u8((const uint8_t *)W10_CTX_VA(4));
        vec = vaddq_u8(vec, vdupq_n_u8(1));
        *vec0 = vgetq_lane_u8(vec, 0);
        sink = *vec0;
        v = *(volatile uint8_t *)W10_CTX_VA(4);
#else
        v = *(volatile uint8_t *)W10_CTX_VA(4);
        sink = v;
#endif
    }
    *scalar = v;
    return 0;
}

/* R0x -> fixed VA index.  Previously `--ctx R02` still used loop index 0,
 * so a scoped run always touched R01's VA while labelling the output R02;
 * the formal per-context runner relies on the scoped VA being real. */
static int
ctx_index(const char *ctx)
{
    if (!strcmp(ctx, "R01")) return 0;
    if (!strcmp(ctx, "R02")) return 1;
    if (!strcmp(ctx, "R03")) return 2;
    if (!strcmp(ctx, "R04")) return 3;
    if (!strcmp(ctx, "R05")) return 4;
    /* [WHEN-5X3 C03] Weak consumer: R01's fixed VA, value discarded. */
    if (!strcmp(ctx, "C03")) return 0;
    return -1;
}

int
main(int argc, char **argv)
{
    const char *ctx = "R01";
    size_t pages = PAGES_DEFAULT;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--ctx") && i + 1 < argc)
            ctx = argv[++i];
        else if (!strcmp(argv[i], "--pages") && i + 1 < argc)
            pages = strtoul(argv[++i], NULL, 0);
    }
    if (pages < 1024 || pages > PAGES_MAX) {
        fprintf(stderr, "W10_FATAL bad --pages %zu\n", pages);
        return 2;
    }
    size_t total = pages * PAGE;

    pm_fd = open("/proc/self/pagemap", O_RDONLY);
    if (pm_fd < 0) {
        perror("pagemap");
        return 2;
    }

    struct rlimit rl;
    getrlimit(RLIMIT_MEMLOCK, &rl);

    const char *path = "/tmp/mmu_w10_pages.bin";
    int fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0600);
    if (fd < 0) {
        perror("open");
        return 2;
    }
    if (ftruncate(fd, (off_t)total) != 0) {
        perror("ftruncate");
        return 2;
    }

    volatile uint8_t *alias = mmap((void *)W10_ALIAS, total,
                                   PROT_READ | PROT_WRITE,
                                   MAP_SHARED | MAP_FIXED_NOREPLACE |
                                   MAP_POPULATE, fd, 0);
    if (alias == MAP_FAILED) {
        fprintf(stderr, "W10_FATAL alias mmap errno=%d (%s)\n", errno,
                strerror(errno));
        return 2;
    }
    madvise((void *)alias, total, MADV_NOHUGEPAGE);
    fprintf(stderr, "W10_INFO fill start pages=%zu\n", pages);
    fill_buffer(alias, pages);
    msync((void *)alias, total, MS_ASYNC);

    int mlock_rc = mlock((void *)alias, total);
    fprintf(stderr, "W10_INFO pages=%zu mlock=%s rlim_cur=%llu\n", pages,
            mlock_rc == 0 ? "ok" : "fail",
            (unsigned long long)rl.rlim_cur);

    PfnIdx *arr = calloc(pages, sizeof(*arr));
    uint64_t *ents = calloc(pages, sizeof(*ents));
    if (!arr || !ents) {
        perror("calloc");
        return 2;
    }
    fprintf(stderr, "W10_INFO pagemap block read start pages=%zu\n", pages);
    if (read_pagemap_block((uintptr_t)alias, pages, ents) != 0) {
        fprintf(stderr, "W10_FATAL pagemap block read failed: %s\n",
                strerror(errno));
        return 2;
    }
    uint32_t nvalid = 0;
    for (size_t i = 0; i < pages; i++) {
        int present = (ents[i] >> 63) & 1;
        uint64_t pfn = ents[i] & ((1ULL << 55) - 1);
        if (present && pfn) {
            arr[nvalid].pfn = pfn;
            arr[nvalid].idx = (uint32_t)i;
            nvalid++;
        }
    }
    free(ents);
    qsort(arr, nvalid, sizeof(*arr), cmp_pfn);

    int found = 0;
    uint32_t tgt = 0, neigh = 0;
    uint64_t pfn_tgt = 0, pfn_neigh = 0;
    for (uint32_t i = 0; i + 1 < nvalid; i++) {
        if ((arr[i].pfn ^ 1ULL) == arr[i + 1].pfn) {
            tgt = arr[i].idx;
            neigh = arr[i + 1].idx;
            pfn_tgt = arr[i].pfn;
            pfn_neigh = arr[i + 1].pfn;
            found = 1;
            break;
        }
    }
    if (!found) {
        printf("W10_RESULT ctx=%s pages=%zu pfn_xor1_pair=NOT_FOUND "
               "valid_pages=%u result=BLOCKED\n", ctx, pages, nvalid);
        fflush(stdout);
        return 3;
    }

    uint8_t sentinel = alias[(uint64_t)tgt * PAGE];
    uint8_t neigh_sentinel = alias[(uint64_t)neigh * PAGE];
    uint64_t pa_tgt = pfn_tgt << 12;
    uint64_t pa_neigh = pfn_neigh << 12;
    int pa_dram = (pa_tgt >= DRAM_BASE && pa_tgt < DRAM_END &&
                   pa_neigh >= DRAM_BASE && pa_neigh < DRAM_END);

    static const char *all_ctx[5] = {"R01", "R02", "R03", "R04", "R05"};
    int run_all = !strcmp(ctx, "all");
    int nctx = run_all ? 5 : 1;
    int all_ok = 1;
    const int forced_idx = run_all ? -1 : ctx_index(ctx);
    if (!run_all && forced_idx < 0) {
        fprintf(stderr, "W10_FATAL unknown ctx %s\n", ctx);
        return 2;
    }

    for (int ci = 0; ci < nctx; ci++) {
        const char *cctx = run_all ? all_ctx[ci] : ctx;
        const int va_idx = run_all ? ci : forced_idx;
        uintptr_t target_va = W10_TARGET + (uintptr_t)va_idx * 0x100000UL;

        volatile uint8_t *target = mmap((void *)target_va, PAGE, PROT_READ,
                                        MAP_SHARED | MAP_FIXED_NOREPLACE |
                                        MAP_POPULATE, fd,
                                        (off_t)tgt * PAGE);
        if (target == MAP_FAILED) {
            fprintf(stderr, "W10_FATAL target mmap va=0x%" PRIxPTR
                    " errno=%d (%s)\n", target_va, errno, strerror(errno));
            return 2;
        }
        madvise((void *)target, PAGE, MADV_NOHUGEPAGE);

        int pres_target = 0;
        uint64_t pfn_target_now = read_pagemap((uintptr_t)target,
                                               &pres_target);
        char pgsz[256];
        int pgsz_rc = read_smaps_page_size((uintptr_t)target, pgsz,
                                           sizeof(pgsz));
        if (pgsz_rc != 0)
            snprintf(pgsz, sizeof(pgsz), "UNKNOWN");

        uint8_t observed = 0;
        unsigned branch = 0, vec0 = 0;
        if (run_context(cctx, target, sentinel, &observed, &branch, &vec0) != 0)
            return 2;

        int page_4k = (strstr(pgsz, "KernelPageSize:        4 kB") != NULL) ||
                      (strstr(pgsz, "KernelPageSize: 4 kB") != NULL);
        int ok;
        if (!strcmp(cctx, "C03")) {
            /* Weak consumer: the VALUE is not an oracle. The baseline only
             * proves the mapping/translation completed. */
            ok = (sentinel != neigh_sentinel) && pres_target && pa_dram &&
                 page_4k && (pfn_target_now == pfn_tgt);
        } else {
            ok = (observed == sentinel) && (sentinel != neigh_sentinel) &&
                 pres_target && pa_dram && page_4k &&
                 (pfn_target_now == pfn_tgt);
        }
        all_ok = all_ok && ok;

        printf("W10_RESULT ctx=%s pages=%zu alias=0x%" PRIxPTR
               " target=0x%" PRIxPTR
               " target_pfn=0x%" PRIx64 " neighbor_pfn=0x%" PRIx64
               " pa=0x%" PRIx64 " pa_neigh=0x%" PRIx64
               " new_pfn_xor1=0x%" PRIx64 " pte_present=%d pfn_match=%d"
               " page_size=%s sentinel=0x%02x neighbor_sentinel=0x%02x"
               " observed=0x%02x branch=%u vec0=0x%02x result=%s\n",
               cctx, pages, (uintptr_t)alias, target_va, pfn_tgt, pfn_neigh,
               pa_tgt, pa_neigh, (uint64_t)(pfn_tgt ^ 1ULL), pres_target,
               (pfn_target_now == pfn_tgt), pgsz, sentinel, neigh_sentinel,
               observed, branch, vec0, ok ? "PASS" : "FAIL");
        fflush(stdout);

        if (run_all)
            munmap((void *)target, PAGE);
    }

    close(fd);
    if (pm_fd >= 0) close(pm_fd);
    return all_ok ? 0 : 1;
}
