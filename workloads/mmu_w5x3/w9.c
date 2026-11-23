// mmu_w9.c — ARM64 userland MMU-TLBI-Remap workload (baseline only).
//
// One fixed VA is first mapped to file page 0 (Marker A), warmed in the DTLB,
// then legally remapped with MAP_FIXED|MAP_POPULATE to file page 1 (Marker B).
// The old file page stays in the page cache; a second alias mapping proves it
// is still readable.  After the remap the same VA must read Marker B.
//
// Contexts (selected with --ctx):
//   R01 LDR -> result
//   R02 LDR -> ADD
//   R03 LDR -> CMP -> conditional branch
//   R04 LDR -> address calculation -> second LDR
//   R05 NEON load -> vector ADD
//
// No fault injection, no seed, no SampleRunID.  Build:
//   gcc -O2 -static -march=armv8-a+simd -o mmu_w9 mmu_w9.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#if defined(__aarch64__)
#include <arm_neon.h>
#endif

#define PAGE 4096UL
#define W9_VA 0x4000000000UL          /* 256 GiB, inside 39-bit user VA */
#define W9_ALIAS 0x4003000000UL       /* old-page alias */
#define PAGE0_OFF 0UL
#define PAGE1_OFF 4096UL
#define MARKER_A 0xAA
#define MARKER_B 0x55

static volatile uint64_t sink;
static int pagemap_ok;

static uint64_t
read_pagemap(uintptr_t va, int *present)
{
    uint64_t entry = 0;
    int fd = open("/proc/self/pagemap", O_RDONLY);
    *present = 0;
    if (fd < 0)
        return 0;
    off_t off = (off_t)((va >> 12) * 8);
    if (pread(fd, &entry, sizeof(entry), off) != sizeof(entry)) {
        close(fd);
        return 0;
    }
    close(fd);
    *present = (entry >> 63) & 1;
    return entry & ((1ULL << 55) - 1);
}

static uint64_t
virt_to_pa(uintptr_t va, int *present, int *pfn_ok)
{
    uint64_t pfn = read_pagemap(va, present);
    *pfn_ok = (*present && pfn != 0);
    return *pfn_ok ? (pfn << 12) | (va & (PAGE - 1)) : 0;
}

static void
fill_page(int fd, off_t off, uint8_t marker)
{
    uint8_t *buf = malloc(PAGE);
    if (!buf) {
        perror("malloc");
        exit(2);
    }
    memset(buf, marker, PAGE);
    if (pwrite(fd, buf, PAGE, off) != (ssize_t)PAGE) {
        perror("pwrite");
        exit(2);
    }
    free(buf);
}

static int
run_context(const char *ctx, volatile uint8_t *p, uint8_t expect, uint8_t *scalar,
            unsigned *branch, unsigned *vec0)
{
    uint8_t v = 0;
    *branch = 0;
    *vec0 = 0;

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
        __asm__ __volatile__("" ::: "memory");
    } else if (!strcmp(ctx, "R04")) {
        v = *p;
        volatile uint8_t *q = p + (v & 0x0F);
        uint8_t w = *q;
        sink = w;
    } else if (!strcmp(ctx, "C03")) {
        /* [WHEN-5X3 C03] Weak consumption: the stale translation feeds a
         * real load whose value is intentionally discarded and never
         * reaches sink, an oracle, or a later address. */
        volatile uint8_t dead = *p;
        (void)dead;
        __asm__ __volatile__("" ::: "memory");
        v = 0;
    } else if (!strcmp(ctx, "R05")) {
#if defined(__aarch64__)
        uint8x16_t vec = vld1q_u8((const uint8_t *)p);
        vec = vaddq_u8(vec, vdupq_n_u8(1));
        *vec0 = vgetq_lane_u8(vec, 0);
        sink = *vec0;
        v = *p;   /* scalar oracle read */
#else
        v = *p;
        sink = v;
#endif
    } else {
        fprintf(stderr, "unknown ctx %s\n", ctx);
        return -1;
    }
    *scalar = v;
    return 0;
}

int
main(int argc, char **argv)
{
    const char *ctx = "R01";
    int iterations = 1;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--ctx") && i + 1 < argc)
            ctx = argv[++i];
        else if (!strcmp(argv[i], "--iterations") && i + 1 < argc)
            iterations = atoi(argv[++i]);
    }
    int known = !strcmp(ctx, "C03");
    for (int i = 0; i < 5; i++) {
        static const char *names[5] = {"R01", "R02", "R03", "R04", "R05"};
        if (!strcmp(ctx, names[i]))
            known = 1;
    }
    if (!known || iterations < 1) {
        fprintf(stderr, "W9_FATAL bad ctx/iterations\n");
        return 2;
    }

    const char *path = "/tmp/mmu_w9_pages.bin";
    int fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0600);
    if (fd < 0) {
        perror("open");
        return 2;
    }
    if (ftruncate(fd, 2 * PAGE) != 0) {
        perror("ftruncate");
        return 2;
    }
    fill_page(fd, PAGE0_OFF, MARKER_A);
    fill_page(fd, PAGE1_OFF, MARKER_B);
    fsync(fd);

    /* 1. Map VA -> page 0 at a fixed address. */
    volatile uint8_t *p = mmap((void *)W9_VA, PAGE, PROT_READ | PROT_WRITE,
                               MAP_SHARED | MAP_FIXED_NOREPLACE, fd, PAGE0_OFF);
    if (p == MAP_FAILED) {
        fprintf(stderr, "W9_FATAL mmap page0 VA=0x%" PRIxPTR " errno=%d (%s)\n",
                (uintptr_t)W9_VA, errno, strerror(errno));
        return 2;
    }
    madvise((void *)p, PAGE, MADV_NOHUGEPAGE);

    /* [WHEN-5X3] Each iteration is one independent maintenance epoch:
     * warm the current complete translation, legally remap the same VA
     * (the kernel issues the matching maintenance), then access it. This
     * yields exactly one eligible M01 TLBI event per iteration in the
     * same process / same ASID. */
    int cur_off = PAGE0_OFF;
    int next_off = PAGE1_OFF;
    int passed = 0;
    for (int it = 0; it < iterations; it++) {
        const uint8_t cur_marker = (cur_off == PAGE0_OFF) ? MARKER_A
                                                          : MARKER_B;
        const uint8_t next_marker = (next_off == PAGE0_OFF) ? MARKER_A
                                                            : MARKER_B;
        /* 2. Warm the old DTLB/L2 complete entry. */
        for (int i = 0; i < 1000; i++)
            sink += p[0];

        int pres1 = 0, pfn1 = 0;
        uint64_t pa1 = virt_to_pa((uintptr_t)p, &pres1, &pfn1);

        /* 3. Legal remap, with MAP_POPULATE to establish the new PTE. */
        volatile uint8_t *p2 = mmap((void *)W9_VA, PAGE,
                                    PROT_READ | PROT_WRITE,
                                    MAP_SHARED | MAP_FIXED | MAP_POPULATE, fd,
                                    next_off);
        if (p2 == MAP_FAILED) {
            fprintf(stderr, "W9_FATAL mmap next errno=%d (%s)\n", errno,
                    strerror(errno));
            return 2;
        }
        p = p2;
        madvise((void *)p, PAGE, MADV_NOHUGEPAGE);

        int pres2 = 0, pfn2 = 0;
        uint64_t pa2 = virt_to_pa((uintptr_t)p, &pres2, &pfn2);
        pagemap_ok = (pres1 && pres2 && pfn1 && pfn2);

        /* 4. Keep the old file page valid and prove it is still readable. */
        volatile uint8_t *alias = mmap((void *)W9_ALIAS, PAGE, PROT_READ,
                                       MAP_SHARED | MAP_FIXED, fd, cur_off);
        uint8_t old_alias = 0xFF;
        if (alias != MAP_FAILED) {
            madvise((void *)alias, PAGE, MADV_NOHUGEPAGE);
            old_alias = alias[0];
            munmap((void *)alias, PAGE);
        } else {
            fprintf(stderr, "W9_WARN alias mmap errno=%d (%s)\n", errno,
                    strerror(errno));
        }

        /* 5. Access the same VA after the remap. */
        uint8_t observed = 0;
        unsigned branch = 0, vec0 = 0;
        if (run_context(ctx, p, next_marker, &observed, &branch, &vec0) != 0)
            return 2;

        int ok;
        if (!strcmp(ctx, "C03")) {
            /* Weak consumer: success means the mapping was correct and
             * the dead load completed; the loaded VALUE is not an oracle. */
            ok = pres2 && (old_alias == cur_marker);
        } else {
            ok = (observed == next_marker) &&
                 (old_alias == cur_marker) && pres2;
        }
        passed += ok;
        printf("W9_RESULT ctx=%s iter=%d va=0x%" PRIxPTR " pa1=0x%" PRIx64
               " pa2=0x%" PRIx64 " pte_present=%d/%d pagemap=%s"
               " old_marker=0x%02x new_marker=0x%02x expected=0x%02x"
               " observed=0x%02x old_alias=0x%02x branch=%u vec0=0x%02x"
               " result=%s\n",
               ctx, it, (uintptr_t)p, pa1, pa2, pres1, pres2,
               pagemap_ok ? "ok" : "unavailable", cur_marker, next_marker,
               next_marker, observed, old_alias, branch, vec0,
               ok ? "PASS" : "FAIL");
        fflush(stdout);

        cur_off = next_off;
        next_off = (next_off == PAGE0_OFF) ? PAGE1_OFF : PAGE0_OFF;
    }
    printf("W9_SUMMARY ctx=%s iterations=%d pass=%d/%d\n",
           ctx, iterations, passed, iterations);
    fflush(stdout);
    close(fd);
    return passed == iterations ? 0 : 1;
}
