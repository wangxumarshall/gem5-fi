/* sve_ffr_pr305_dual.c — dual-channel extraction of the PR #305
 * review-fix FFR validation (branch fix/ci-40596064101, round-1 commits
 * 25372613 [svcntp_b8 full-bit count] / 89f21715 [window comment] /
 * 10f2bd93 [re-loop sampling]; round-2 commits 2dae11da [always-inline
 * window helper] / acb55504 [split diagnosis] / faulting-LDFF1 golden)
 * for CHAOS/gem5 SE-O3.
 *
 * Phase 1 (golden, section-4 shape): SETFFR -> LDFF1(mapped) -> RDFFR
 *   -> svcntp_b8(svptrue_b8(), ffr) == 8*vl + readback memcmp — the
 *   patched one-shot check, expressions mirrored verbatim from
 *   tests/cpu/arm64/sve512_pred_ops_arm.cpp.
 * Phase 2 (golden, re-loop shape): 20000 iterations of the same
 *   capture window — the round-1 sustained-sampling shape.
 * Phase 3 (poison negative control, no WRFFR needed — gem5 may not
 *   model it): flip ONE NON-FIRST FFR bit (bit 3, inside f64 element
 *   0's slice; first bits are 0,8,16,..) of the captured predicate via
 *   predicate EOR with (whilelt_b8(0,4) ^ whilelt_b8(0,3)). The OLD
 *   b64 count must stay == vl (the blind spot the review proved) and
 *   the NEW b8 count must drop to 8*vl-1 (detection).
 * Phase 4 (golden, round-2 faulting face): the production page-pair
 *   construction — mmap 2 pages, fill the page-1 tail with the test's
 *   src pattern ((j%4)-1.5), punch out page 2 with munmap (NOT
 *   mprotect(PROT_NONE): gem5 SE maps mprotect to ignoreFunc, the hole
 *   must fault identically on hardware and here), then the three faces
 *   per the patched test: M mapped (== 8*vl), F fault-at-element-1
 *   (== 8, data prefix src[vl-1] + zero tail), A accumulation (mapped
 *   LDFF1 without SETFFR, FFR must stay at 8 — captured back-to-back
 *   with F, no call in between, exactly as the test orders them).
 * Phase 5 (golden, faulting re-loop shape): 2000 iterations of the
 *   F+A pair (gem5 SE suppressed faults are far costlier than on
 *   hardware; 2k suffices for per-tier semantic determinism — the
 *   sustained-stress duty belongs to the real test on hardware).
 * Phase 6 (poison, stuck-at-1 negative control): flip ONE TAIL bit
 *   (bit 9, inside element 1's slice — expected-0 territory) of the
 *   F-face captured predicate. The partial-clear count must see 9 !=
 *   8 (detection); the round-1 all-mapped-only test never sampled a
 *   partially-cleared FFR at all, so this bit state was invisible to
 *   it by construction — the round-2 review #12 blind spot.
 *
 * Output: one 16-hex checksum line (fnv1a over the captured counts and
 * readbacks) + SDCSHIELD_FAILS=N (N = unexpected outcomes).
 */
#include <arm_sve.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define RELOOP_ITERS 20000
#define FAULT_RELOOP_ITERS 2000

static uint64_t fnv1a(uint64_t h, const void *p, size_t n)
{
    const uint8_t *b = p;
    for (size_t i = 0; i < n; ++i) { h ^= b[i]; h *= 1099511628211ULL; }
    return h;
}

/* the patched test's single always-inline capture window, PrimeFFR
 * variant included verbatim in shape (setffr?/ldff1/rdffr/cntp_b8/st1) */
static long capture(const double *from, double *to, int prime)
{
    if (prime) svsetffr();
    svfloat64_t v = svldff1_f64(svptrue_b64(), from);
    svbool_t ffr = svrdffr();
    long bits = svcntp_b8(svptrue_b8(), ffr);
    svst1_f64(svptrue_b64(), to, v);
    return bits;
}

int main(void)
{
    const long vl = svcntd();               /* f64 lanes */
    const long total_bits = 8 * vl;         /* FFR bits = VL bytes */
    const svbool_t all_b64 = svptrue_b64();
    const svbool_t all_b8 = svptrue_b8();
    double mem[16];
    long fails = 0;
    uint64_t h = 1469598103934665603ULL;

    for (long i = 0; i < vl; ++i) mem[i] = (double)(i % 4) - 1.5;

    /* ---- Phase 1: one-shot section-4 shape (round-1 patched check) ---- */
    {
        svsetffr();
        svfloat64_t v = svldff1_f64(all_b64, mem);
        svbool_t ffr = svrdffr();
        const long ffr_bits = svcntp_b8(all_b8, ffr);
        double back[16];
        svst1_f64(all_b64, back, v);
        if (ffr_bits != total_bits) { fails++; }
        if (memcmp(back, mem, (size_t)vl * 8) != 0) { fails++; }
        h = fnv1a(h, &ffr_bits, sizeof ffr_bits);
        h = fnv1a(h, back, (size_t)vl * 8);
        printf("phase1: ffr_bits=%ld expected=%ld readback=%s\n",
               ffr_bits, total_bits,
               memcmp(back, mem, (size_t)vl * 8) == 0 ? "clean" : "MISMATCH");
    }

    /* ---- Phase 2: re-loop sustained sampling (round-1 shape) ---- */
    {
        long bad = -1;
        for (long it = 0; it < RELOOP_ITERS; ++it) {
            svsetffr();
            svfloat64_t v = svldff1_f64(all_b64, mem);
            svbool_t ffr = svrdffr();
            const long ffr_bits = svcntp_b8(all_b8, ffr);
            double back[16];
            svst1_f64(all_b64, back, v);
            if (ffr_bits != total_bits ||
                memcmp(back, mem, (size_t)vl * 8) != 0) { bad = it; break; }
        }
        if (bad >= 0) { fails++; }
        h = fnv1a(h, &bad, sizeof bad);
        printf("phase2: %ld iterations, %s\n", (long)RELOOP_ITERS,
               bad < 0 ? "all clean" : "FAILED");
    }

    /* ---- Phase 3: poison — one NON-FIRST FFR bit flipped ---- */
    {
        svsetffr();
        (void)svldff1_f64(all_b64, mem);
        svbool_t ffr = svrdffr();
        svbool_t w4 = svwhilelt_b8((uint64_t)0, (uint64_t)4);
        svbool_t w3 = svwhilelt_b8((uint64_t)0, (uint64_t)3);
        svbool_t hole = sveor_b_z(all_b8, w4, w3);          /* bit 3 only */
        svbool_t corrupt = sveor_b_z(all_b8, ffr, hole);
        const long old_cnt = svcntp_b64(all_b64, corrupt);
        const long new_cnt = svcntp_b8(all_b8, corrupt);
        /* old check blind (== vl) AND new check detects (< total) */
        if (!(old_cnt == vl && new_cnt == total_bits - 1)) fails++;
        h = fnv1a(h, &old_cnt, sizeof old_cnt);
        h = fnv1a(h, &new_cnt, sizeof new_cnt);
        printf("phase3: poison bit3: old cntp_b64=%ld (==vl %ld? %s) "
               "new cntp_b8=%ld (==%ld? %s)\n",
               old_cnt, vl, old_cnt == vl ? "blind as reviewed" : "NO",
               new_cnt, total_bits - 1,
               new_cnt == total_bits - 1 ? "detected" : "NO");
    }

    /* ---- Phase 4: round-2 faulting face (production page pair) ---- */
    {
        const long ps = sysconf(_SC_PAGESIZE);
        char *base = mmap(0, 2 * (size_t)ps, PROT_READ | PROT_WRITE,
                          MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (base == (char *)-1) { printf("phase4: mmap FAILED\n"); return 2; }
        if (munmap(base + ps, (size_t)ps) != 0) {
            printf("phase4: munmap hole FAILED\n"); return 2;
        }
        char *hole = base + ps;
        /* the patched test's init fill: src pattern at the page-1 tail */
        double *pg_mapped = (double *)(hole - (size_t)vl * 8);
        for (long i = 0; i < vl; ++i) pg_mapped[i] = (double)(i % 4) - 1.5;
        const double *pg_fault_k1 = (const double *)(hole - 8);

        /* M: mapped, all-ones golden */
        double mback[16];
        const long m_bits = capture(pg_mapped, mback, 1);
        int m_ok = m_bits == total_bits &&
                   memcmp(mback, pg_mapped, (size_t)vl * 8) == 0;
        if (!m_ok) fails++;

        /* F then A back-to-back, no call between (the patched test's
         * ordering: the partially-cleared FFR is live state) */
        double fback[16], aback[16];
        const long f_bits = capture(pg_fault_k1, fback, 1);
        const long a_bits = capture(pg_mapped, aback, 0);
        double fexp[16];
        fexp[0] = (double)((vl - 1) % 4) - 1.5;
        for (long i = 1; i < vl; ++i) fexp[i] = 0.0;
        int f_ok = f_bits == 8 && memcmp(fback, fexp, (size_t)vl * 8) == 0;
        int a_ok = a_bits == 8;
        if (!f_ok || !a_ok) fails++;
        h = fnv1a(h, &m_bits, sizeof m_bits);
        h = fnv1a(h, &f_bits, sizeof f_bits);
        h = fnv1a(h, &a_bits, sizeof a_bits);
        h = fnv1a(h, fback, (size_t)vl * 8);
        h = fnv1a(h, aback, (size_t)vl * 8);
        printf("phase4: pagesize=%ld M=%ld(exp %ld,%s) F=%ld(exp 8,%s data %s) "
               "A=%ld(exp 8,%s)\n", ps,
               m_bits, total_bits, m_bits == total_bits ? "OK" : "FAIL",
               f_bits, f_ok ? "OK" : "FAIL",
               memcmp(fback, fexp, (size_t)vl * 8) == 0 ? "OK" : "FAIL",
               a_bits, a_ok ? "OK" : "FAIL");

        /* ---- Phase 5: faulting re-loop (F+A pair, 2k iterations) ---- */
        {
            long bad = -1;
            for (long it = 0; it < FAULT_RELOOP_ITERS; ++it) {
                const long fb = capture(pg_fault_k1, fback, 1);
                const long ab = capture(pg_mapped, aback, 0);
                if (fb != 8 || ab != 8 ||
                    memcmp(fback, fexp, (size_t)vl * 8) != 0) { bad = it; break; }
            }
            if (bad >= 0) { fails++; }
            h = fnv1a(h, &bad, sizeof bad);
            printf("phase5: %ld faulting iterations, %s\n",
                   (long)FAULT_RELOOP_ITERS, bad < 0 ? "all clean" : "FAILED");
        }

        /* ---- Phase 6: poison — stuck-at-1 in the faulted tail ---- */
        {
            svsetffr();
            (void)svldff1_f64(all_b64, pg_fault_k1);
            svbool_t ffr = svrdffr();
            /* bit 9 = element 1's slice, non-first bit, expected-0 tail */
            svbool_t w10 = svwhilelt_b8((uint64_t)0, (uint64_t)10);
            svbool_t w9 = svwhilelt_b8((uint64_t)0, (uint64_t)9);
            svbool_t hole9 = sveor_b_z(all_b8, w10, w9);     /* bit 9 only */
            svbool_t stuck = sveor_b_z(all_b8, ffr, hole9);  /* emulate s@1 */
            const long clean_cnt = svcntp_b8(all_b8, ffr);
            const long stuck_cnt = svcntp_b8(all_b8, stuck);
            /* clean face == 8 AND the stuck-at-1 bit pushes it to 9: the
             * partial-clear assertion detects what the round-1 mapped-only
             * sampling could never even express */
            if (!(clean_cnt == 8 && stuck_cnt == 9)) fails++;
            h = fnv1a(h, &clean_cnt, sizeof clean_cnt);
            h = fnv1a(h, &stuck_cnt, sizeof stuck_cnt);
            printf("phase6: poison tail bit9: clean=%ld (==8? %s) "
                   "stuck=%ld (==9 detected? %s)\n",
                   clean_cnt, clean_cnt == 8 ? "Y" : "NO",
                   stuck_cnt, stuck_cnt == 9 ? "Y" : "NO");
        }
    }

    /* restore FFR to all-ones before exit */
    svsetffr();

    printf("%016llx\n", (unsigned long long)h);
    printf("SDCSHIELD_FAILS=%ld vl=%ld total_ffr_bits=%ld\n",
           fails, vl, total_bits);
    return fails ? 1 : 0;
}
