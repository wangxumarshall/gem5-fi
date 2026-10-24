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
   mirroring the test's loop shape (svcnt stepping + whilelt tail).
   The function set is the test's REAL call set (12 functions: f64 u10
   sin/cos/exp/log, f64 u35 sin/cos/exp2/log, f32 u10 sin/cos/exp/log —
   adversarial-review Minor-4: the first matrix ran a mismatched set
   incl. an exp2dx_u10 the test never calls). */
static void compute_all(const double *x, double *out, float *out32,
                         const float *xf_trig, const float *xf_exp,
                         const float *xf_log, size_t n)
{
    for (size_t i = 0; i < n; i += (size_t)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)n);
        const svfloat64_t v = svld1_f64(pg, x + i);
        /* out layout: [function][element] — eight f64 slots */
        svst1_f64(pg, out + 0 * n + i, Sleef_sindx_u10sve(v));
        svst1_f64(pg, out + 1 * n + i, Sleef_cosdx_u10sve(v));
        svst1_f64(pg, out + 2 * n + i, Sleef_expdx_u10sve(v));
        svst1_f64(pg, out + 3 * n + i, Sleef_logdx_u10sve(v));
        svst1_f64(pg, out + 4 * n + i, Sleef_sindx_u35sve(v));
        svst1_f64(pg, out + 5 * n + i, Sleef_cosdx_u35sve(v));
        svst1_f64(pg, out + 6 * n + i, Sleef_exp2dx_u35sve(v));
        svst1_f64(pg, out + 7 * n + i, Sleef_logdx_u35sve(v));
    }
    for (size_t i = 0; i < n; i += (size_t)svcntw()) {
        const svbool_t pg = svwhilelt_b32((uint64_t)i, (uint64_t)n);
        /* out32 layout: [function][element] — four f32 slots, each fed
           from the test's own domain-specific input array */
        svst1_f32(pg, out32 + 0 * n + i,
                  Sleef_sinfx_u10sve(svld1_f32(pg, xf_trig + i)));
        svst1_f32(pg, out32 + 1 * n + i,
                  Sleef_cosfx_u10sve(svld1_f32(pg, xf_trig + i)));
        svst1_f32(pg, out32 + 2 * n + i,
                  Sleef_expfx_u10sve(svld1_f32(pg, xf_exp + i)));
        svst1_f32(pg, out32 + 3 * n + i,
                  Sleef_logfx_u10sve(svld1_f32(pg, xf_log + i)));
    }
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

    /* Input domains mirror the TEST's real domains (sleef_sve.cpp):
       f64 band (0.5, 2); f32 trig [-pi, pi] / exp [-20, 20) / log
       positive — the first matrix fed the f32 set with reinterpreted
       double bits (out-of-domain garbage); cosfx then diverged at the
       128-bit tier, which the oracle flagged. */
    static double x[NELEMS];
    static float xf_trig[NELEMS], xf_exp[NELEMS], xf_log[NELEMS];
    for (int i = 0; i < NELEMS; ++i) {
        double f01, u;
        if (randomize) {
            f01 = (double)(xs32() >> 8) / (double)(1u << 24);
            u = (float)(xs32() >> 8) / (float)(1u << 24);
        } else {
            f01 = ((i % 199) / 199.0);
            u = (float)((i % 173) / 173.0);
        }
        x[i] = 0.5 + 1.5 * f01;
        xf_trig[i] = (u * 2.0f - 1.0f) * 3.14159265f;
        xf_exp[i] = (u * 2.0f - 1.0f) * 20.0f;
        xf_log[i] = (u + 1.0e-30f) * 1.0e10f;
    }

    static double out_a[8 * NELEMS], out_b[8 * NELEMS];
    static float out32_a[4 * NELEMS], out32_b[4 * NELEMS];
    compute_all(x, out_a, out32_a, xf_trig, xf_exp, xf_log, NELEMS);
    compute_all(x, out_b, out32_b, xf_trig, xf_exp, xf_log, NELEMS);

    /* Channel A: two-pass determinism, byte-exact (f64 + f32 sets). */
    if (memcmp(out_a, out_b, sizeof(out_a)) != 0 ||
        memcmp(out32_a, out32_b, sizeof(out32_a)) != 0) {
        for (int i = 0; i < 8 * NELEMS; ++i)
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
    fnv_bits(out32_a, sizeof(out32_a));

    printf("mode=sleef_vla lanes=%d nelems=%d FAILS=%u\n",
           lanes, NELEMS, g_fails);
    printf("SDCSHIELD_FAILS=%u\n%016llx\n",
           g_fails, (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
