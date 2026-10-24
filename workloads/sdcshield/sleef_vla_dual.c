/* sleef_vla_dual.c — all-VL Phase 2 P5 kernel: validates that the
 * vendored SLEEF 3.9.0 VLA SVE functions (Sleef_*dx_u10sve / u35sve)
 * produce byte-identical results at every SVE tier for a fixed input —
 * the cross-tier identity judgment for migrating tests/cpu/sleef/
 * sleef_sve.cpp off the -msve-vector-bits=128 lock (the historical
 * "256 compile regression" is most plausibly experiment contamination;
 * this kernel settles the VLA path at all four tiers).
 *
 * Judgment structure:
 *   - within-run: the function set is computed TWICE over the same
 *     input and byte-compared (determinism);
 *   - cross-tier: with the fixed input the output checksum MUST be
 *     identical across 128/256/512/1024-bit (sin/cos/exp/log are pure
 *     per-lane functions; any tier dependence is a real defect) — the
 *     16-run matrix compares the four fixed-mode checksums;
 *   - absolute correctness is SLEEF's own tested property (u10 scalar
 *     refs are tolerance-based, NOT byte-exact — do not cross-compare).
 *
 * Build dependency: the vendored SLEEF static library (gitignored):
 *   /home/sdc/wangxu/code-review/sdcshield-sve/third-party/sleef/install/
 * The library is pure VLA machine code (disassembly-verified: cntd/cntp/
 * rdvl, no ptrue_pat fixed-width patterns).
 *
 * Channels: A = two-pass byte-exact compare; B = FNV-1a over all output
 *           words (the cross-tier oracle).
 * argv: [fixed|random] [seed]; exit 0 / 1 (fails) / 3 (unsupported VL).
 * Run:   gem5.opt configs/se/arm_chaos.py --cpu O3 --cmd \
 *          workloads/sdcshield/sleef_vla_dual --sve_vl 4 \
 *          --workload_args "fixed 1"
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <arm_sve.h>
#include <sleef.h>

#define NELEMS 1024
#define LMAX   16

static uint32_t xs_state;
static uint32_t xs32(void)
{
    xs_state ^= xs_state << 13;
    xs_state ^= xs_state >> 17;
    xs_state ^= xs_state << 5;
    return xs_state;
}

static unsigned g_fails = 0;
static uint64_t fnv = 1469598103934665603ULL;
static void fnv_bits(const void *p, size_t n)
{
    const unsigned char *b = p;
    for (size_t i = 0; i < n; ++i) {
        fnv ^= b[i];
        fnv *= 1099511628211ULL;
    }
}

/* One pass over the input through the six SLEEF VLA function groups,
   mirroring the test's loop shape (svcnt stepping + whilelt tail). */
static void compute_all(const double *x, double *out, size_t n)
{
    const svbool_t pg64 = svptrue_b64();
    for (size_t i = 0; i < n; i += (size_t)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)n);
        const svfloat64_t v = svld1_f64(pg, x + i);
        /* out layout: [function][element] — six function slots */
        svst1_f64(pg, out + 0 * n + i, Sleef_sindx_u10sve(v));
        svst1_f64(pg, out + 1 * n + i, Sleef_cosdx_u10sve(v));
        svst1_f64(pg, out + 2 * n + i, Sleef_expdx_u10sve(v));
        svst1_f64(pg, out + 3 * n + i, Sleef_logdx_u10sve(v));
        svst1_f64(pg, out + 4 * n + i, Sleef_exp2dx_u10sve(v));
        svst1_f64(pg, out + 5 * n + i, Sleef_sindx_u35sve(v));
    }
    (void)pg64;
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "fixed";
    const uint32_t seed = (argc > 2) ? (uint32_t)strtoul(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    xs_state = seed ? seed : 1;

    const int lanes = (int)svcntd();
    if (lanes < 2 || lanes > LMAX) {
        fprintf(stderr, "unsupported VL (f64 lanes %d)\n", lanes);
        return 3;
    }

    /* Input domain: the test's band (|x| <= 2 for sin/cos; positive
       (0.5, 2) for exp/log/exp2 to stay well-conditioned). */
    static double x[NELEMS];
    for (int i = 0; i < NELEMS; ++i) {
        if (randomize) {
            double f = (double)(xs32() >> 8) / (double)(1u << 24);
            x[i] = 0.5 + 1.5 * f;
        } else {
            x[i] = 0.5 + 1.5 * ((i % 199) / 199.0);
        }
    }

    static double out_a[6 * NELEMS], out_b[6 * NELEMS];
    compute_all(x, out_a, NELEMS);
    compute_all(x, out_b, NELEMS);

    /* Channel A: two-pass determinism, byte-exact. */
    if (memcmp(out_a, out_b, sizeof(out_a)) != 0) {
        for (int i = 0; i < 6 * NELEMS; ++i)
            if (out_a[i] != out_b[i]) {
                fprintf(stderr, "nondeterministic @%d %.17g vs %.17g\n",
                        i, out_a[i], out_b[i]);
                break;
            }
        ++g_fails;
    }

    /* Channel B: FNV over the first-pass outputs — the cross-tier
       oracle (fixed mode MUST give the same checksum at every tier). */
    fnv_bits(out_a, sizeof(out_a));

    printf("mode=sleef_vla lanes=%d nelems=%d FAILS=%u\n",
           lanes, NELEMS, g_fails);
    printf("SDCSHIELD_FAILS=%u\n%016llx\n",
           g_fails, (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
