/* sve_ffr_pr305_dual.c — dual-channel extraction of the PR #305
 * review-fix FFR validation (branch fix/ci-40596064101, commits
 * 25372613 [svcntp_b8 full-bit count] / 89f21715 [window comment] /
 * 10f2bd93 [re-loop sampling]) for CHAOS/gem5 SE-O3.
 *
 * Phase 1 (golden, section-4 shape): SETFFR -> LDFF1(mapped) -> RDFFR
 *   -> svcntp_b8(svptrue_b8(), ffr) == 8*vl + readback memcmp — the
 *   patched one-shot check, expressions mirrored verbatim from
 *   tests/cpu/arm64/sve512_pred_ops_arm.cpp.
 * Phase 2 (golden, re-loop shape): 200000 iterations of the same
 *   capture window — the patch-3 sustained-sampling shape.
 * Phase 3 (poison negative control, no WRFFR needed — gem5 may not
 *   model it): flip ONE NON-FIRST FFR bit (bit 3, inside f64 element
 *   0's slice; first bits are 0,8,16,..) of the captured predicate via
 *   predicate EOR with (whilelt_b8(0,4) ^ whilelt_b8(0,3)). The OLD
 *   b64 count must stay == vl (the blind spot the review proved) and
 *   the NEW b8 count must drop to 8*vl-1 (detection) — at this tier.
 *
 * Output: one 16-hex checksum line (fnv1a over the captured counts and
 * readback) + SDCSHIELD_FAILS=N (N = unexpected outcomes).
 */
#include <arm_sve.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define RELOOP_ITERS 20000

static uint64_t fnv1a(uint64_t h, const void *p, size_t n)
{
    const uint8_t *b = p;
    for (size_t i = 0; i < n; ++i) { h ^= b[i]; h *= 1099511628211ULL; }
    return h;
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

    for (long i = 0; i < vl; ++i) mem[i] = (double)i - 0.5;

    /* ---- Phase 1: one-shot section-4 shape (patched check) ---- */
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

    /* ---- Phase 2: re-loop sustained sampling (patch-3 shape) ---- */
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

    /* restore FFR to all-ones before exit */
    svsetffr();

    printf("%016llx\n", (unsigned long long)h);
    printf("SDCSHIELD_FAILS=%ld vl=%ld total_ffr_bits=%ld\n",
           fails, vl, total_bits);
    return fails ? 1 : 0;
}
