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
 * Phase 7 (golden, round-3 combined window + bitmap): the two round-3
 *   changes mirrored — (a) faulting+accumulation captures inside ONE
 *   combined unit capture_pair (cross-capture zero-call discipline),
 *   (b) FFR verified BIT-FOR-BIT on a materialized byte image (byte i
 *   = 1 iff FFR bit i set; svsel + st1b inside the window) against
 *   golden bitmaps m_gold (all ones) / f_gold (8 ones then zeros),
 *   counts kept as diagnostics only. FAULT_RELOOP_ITERS iterations of
 *   [mapped face + pair], the patched re-loop shape (no straight-line
 *   one-shot: GCC 12 CSEs svrdffr across SETFFR/LDFF1/calls, so the
 *   captures are noinline functions — a call boundary is the only
 *   reliable CSE killer; the loop's first iteration is the one-shot).
 *   Measured boundary: the acc-face DATA is hashed but NOT asserted —
 *   hardware (Kunpeng 920) loads all predicate-active elements
 *   regardless of prior FFR state (FFR is a pure output; even FFR=0
 *   loads fully), gem5 SE models the FFR as an implicit per-element
 *   input mask (sve_mem.isa: GpOp_x[i] && firstFaultReg[...]) and
 *   zeroes FFR-clear elements. Both agree the mapped load leaves the
 *   FFR untouched — which is the assertion the patched test makes.
 * Phase 8 (poison, round-3 #17 blind spot): complementary count-
 *   conserving double flip of the F-face predicate — bit 1 (expected-1,
 *   element 0's slice) drops, bit 9 (expected-0, element 1's slice)
 *   rises. popcount stays exactly 8 (the OLD count check is blind —
 *   the review's exact scenario) while the image memcmp detects.
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

/* round-3 capture: additionally materializes the FFR predicate into a
 * byte image (byte i = 1 iff FFR bit i set) — the patched test's
 * bit-for-bit verification input; expressions mirror the round-3
 * ffr_ldff1_capture (count demoted to diagnostic). The leading asm is
 * the same zero-instruction compiler barrier the round-3 test carries:
 * GCC 12 neither models svldff1/svsetffr FFR effects nor kills rdffr
 * values at calls (measured), so without it a later capture's rdffr can
 * be CSE'd into an earlier capture's stale spill (observed: phase7 M
 * face reloading phase6's partial-clear value). */
static __attribute__((noinline)) long
capture_img(const double *from, double *to, int prime,
                          uint8_t *ffr_image)
{
    __asm__ volatile ("" : : : "memory");
    if (prime) svsetffr();
    svfloat64_t v = svldff1_f64(svptrue_b64(), from);
    svbool_t ffr = svrdffr();
    long bits = svcntp_b8(svptrue_b8(), ffr);
    svst1_f64(svptrue_b64(), to, v);
    svst1_s8(svptrue_b8(), (int8_t *)ffr_image,
             svsel(ffr, svdup_n_s8(1), svdup_n_s8(0)));
    return bits;
}

/* round-3 combined unit: the faulting and accumulation captures as ONE
 * function so the between-captures zero-call discipline is structural —
 * mirrors the patched test's ffr_fault_acc_capture (always-inline there;
 * plain here: gem5 SE has no libc/syscall in this path to clobber FFR) */
static __attribute__((noinline)) void
capture_pair(const double *fault_from, double *fault_to,
                           uint8_t *fault_img, const double *acc_from,
                           double *acc_to, uint8_t *acc_img,
                           long *fb, long *ab)
{
    *fb = capture_img(fault_from, fault_to, 1, fault_img);
    *ab = capture_img(acc_from, acc_to, 0, acc_img);
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
        /* round-3 bitmap goldens (shared by Phase 7/8): one byte per FFR
         * bit; m_gold all-ones (mapped face), f_gold 8 ones then zeros
         * (faulting AND accumulation faces) */
        uint8_t m_gold[128], f_gold[128];
        for (long i = 0; i < total_bits; ++i) {
            m_gold[i] = 1;
            f_gold[i] = (i < 8) ? 1 : 0;
        }
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

        /* ---- Phase 6: poison — stuck-at-1 in the faulted tail ----
         * GCC 12 (measured, 12.3.1) does NOT model svldff1's FFR side
         * effect: when the loaded data is dead (buffer never read), the
         * st1d is DSE'd, the ldff1 follows it out, and rdffr then reads
         * the all-ones FFR left by SETFFR — the fault silently never
         * happens in the generated code (minimal repro: setffr;
         * (void)ldff1; rdffr -> ldff1d absent). Every capture's data
         * buffer is therefore memcmp'd (the data golden is part of the
         * face anyway) and the poison base predicate is rebuilt from
         * the OBSERVABLE image bytes — svcmpne(image, 0) restores
         * exactly the predicate the image materialized, bit for bit. */
        {
            double pback6[16];
            uint8_t p6_img[128];
            (void)capture_img(pg_fault_k1, pback6, 1, p6_img);
            if (memcmp(pback6, fexp, (size_t)vl * 8) != 0) fails++;
            svbool_t ffr = svcmpne_n_s8(all_b8,
                                        svld1_s8(all_b8,
                                                 (int8_t *)p6_img), 0);
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

        /* ---- Phase 7: round-3 combined window + bitmap goldens ----
         * No straight-line one-shot ahead of the loop: GCC 12 CSEs
         * svrdffr values across SETFFR/LDFF1 and even calls (measured —
         * see the capture_img comment), so a one-shot M face placed here
         * read Phase 6's stale partial-clear value and false-FAILED;
         * the loop boundary is the only reliable CSE killer and the
         * FIRST loop iteration runs the identical one-shot checks. */
        {
            uint8_t m_img[128], f_img[128], a_img[128];
            double mback[16], fback2[16], aback2[16];
            long mb = -1, fb2 = -1, ab2 = -1, bad = -1;
            int why = -1;
            for (long it = 0; it < FAULT_RELOOP_ITERS; ++it) {
                mb = capture_img(pg_mapped, mback, 1, m_img);
                capture_pair(pg_fault_k1, fback2, f_img, pg_mapped, aback2,
                             a_img, &fb2, &ab2);
                if (memcmp(m_img, m_gold, (size_t)total_bits) != 0) { why = 0; }
                else if (memcmp(mback, pg_mapped, (size_t)vl * 8) != 0) { why = 1; }
                else if (memcmp(f_img, f_gold, (size_t)total_bits) != 0) { why = 2; }
                else if (memcmp(fback2, fexp, (size_t)vl * 8) != 0) { why = 3; }
                else if (memcmp(a_img, f_gold, (size_t)total_bits) != 0) { why = 4; }
                if (why >= 0) { bad = it; break; }
                /* acc-face DATA: hashed, not asserted — the patched test
                 * does not check it either, because the two executions
                 * of record DISAGREE here (measured 2026-10-30):
                 * hardware (Kunpeng 920) loads all predicate-active
                 * elements regardless of prior FFR state (FFR is a pure
                 * output — even FFR=0 loads fully), while gem5 SE models
                 * the FFR as an implicit per-element input mask
                 * (sve_mem.isa fautlingLoadmemAccCode: GpOp_x[i] &&
                 * firstFaultReg[...]) and zeroes FFR-clear elements.
                 * Both agree the mapped load leaves the FFR untouched,
                 * which is the face's assertion. The hash still pins the
                 * acc LDFF1 against DSE. */
                h = fnv1a(h, aback2, (size_t)vl * 8);
            }
            if (bad >= 0) fails++;
            h = fnv1a(h, &bad, sizeof bad);
            h = fnv1a(h, &mb, sizeof mb);
            h = fnv1a(h, &fb2, sizeof fb2);
            h = fnv1a(h, &ab2, sizeof ab2);
            printf("phase7: %ld combined iterations (M/F/A bitmaps+data), "
                   "%s (last counts %ld/%ld/%ld diag%s%s)\n",
                   (long)FAULT_RELOOP_ITERS, bad < 0 ? "all clean" : "FAILED",
                   mb, fb2, ab2, bad < 0 ? "" : ", failed check ",
                   bad < 0 ? "" : (why == 0 ? "m_img" : why == 1 ? "mback" :
                                   why == 4 ? "a_img" : "?"));
        }

        /* ---- Phase 8: poison — count-CONSERVING complementary double
         * flip (round-3 review #17's exact blind spot): bit 1 (expected
         * 1, element 0's slice) drops, bit 9 (expected 0, element 1's
         * slice) rises. The OLD count check sees 8 == 8 and passes; the
         * round-3 image memcmp must detect. ---- */
        {
            double fback3[16];
            uint8_t p_img[128], c_img[128];
            /* base predicate rebuilt from the observable image, data
             * buffer memcmp'd to pin the ldff1 (see the Phase 6 comment
             * for the GCC 12 DCE/DSE mechanism) */
            (void)capture_img(pg_fault_k1, fback3, 1, p_img);
            if (memcmp(fback3, fexp, (size_t)vl * 8) != 0) fails++;
            svbool_t ffr = svcmpne_n_s8(all_b8,
                                        svld1_s8(all_b8,
                                                 (int8_t *)p_img), 0);
            /* bit 1 = whilelt(0,2) ^ whilelt(0,1); bit 9 = w(0,10)^w(0,9) */
            svbool_t w2 = svwhilelt_b8((uint64_t)0, (uint64_t)2);
            svbool_t w1 = svwhilelt_b8((uint64_t)0, (uint64_t)1);
            svbool_t w10 = svwhilelt_b8((uint64_t)0, (uint64_t)10);
            svbool_t w9 = svwhilelt_b8((uint64_t)0, (uint64_t)9);
            svbool_t flip = svorr_b_z(all_b8,
                                      sveor_b_z(all_b8, w2, w1),
                                      sveor_b_z(all_b8, w10, w9));
            svbool_t corrupt = sveor_b_z(all_b8, ffr, flip);
            const long clean_cnt = svcntp_b8(all_b8, ffr);
            const long corrupt_cnt = svcntp_b8(all_b8, corrupt);
            svst1_s8(all_b8, (int8_t *)c_img,
                     svsel(corrupt, svdup_n_s8(1), svdup_n_s8(0)));
            /* clean face must equal f_gold; corrupt count must CONSERVE
             * (== 8, old check blind) while the image must DIFFER */
            int clean_ok = memcmp(p_img, f_gold, (size_t)total_bits) == 0;
            int old_blind = (corrupt_cnt == 8);
            int new_detects = memcmp(c_img, f_gold, (size_t)total_bits) != 0;
            if (!(clean_ok && old_blind && new_detects)) fails++;
            h = fnv1a(h, &clean_cnt, sizeof clean_cnt);
            h = fnv1a(h, &corrupt_cnt, sizeof corrupt_cnt);
            h = fnv1a(h, c_img, (size_t)total_bits);
            printf("phase8: poison bits{1,9}: clean_img=%s corrupt_cnt=%ld "
                   "(==8 conserved/old blind? %s) corrupt_img_differs=%s\n",
                   clean_ok ? "OK" : "FAIL", corrupt_cnt,
                   old_blind ? "Y" : "NO", new_detects ? "Y" : "NO");
        }
    }

    /* restore FFR to all-ones before exit */
    svsetffr();

    printf("%016llx\n", (unsigned long long)h);
    printf("SDCSHIELD_FAILS=%ld vl=%ld total_ffr_bits=%ld\n",
           fails, vl, total_bits);
    return fails ? 1 : 0;
}
