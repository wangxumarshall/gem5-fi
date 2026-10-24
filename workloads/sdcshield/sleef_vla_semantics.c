/* sleef_vla_semantics.c — SLEEF-on-gem5 fidelity probe for the
 * sleef_vla_dual 16-run matrix (PR #286 sleef_sve true-VLA validation).
 *
 * Motivation (honesty requirement on the matrix): the vendored SLEEF SVE
 * code contains vector-immediate MOVs (MOVI bitmask forms like
 * `mov z.d, #0x8000000000000000` and FMOV FP forms like `fmov z.d, #1.5`),
 * and gem5 has a KNOWN deviation F3 (sve_sme_semantics P2: `mov z.d, #1`
 * vector-immediate writes read back as 0). The dual kernel's two channels
 * (same-kernel golden recompute + cross-tier checksum) are both blind to a
 * DETERMINISTIC corruption — both passes and all four tiers would be
 * identically wrong (the documented in-run dual-channel blind-spot class).
 * This probe closes that hole with two checks, run at each VL tier:
 *
 *   S1  F3 applicability, per encoding class, at THIS tier: direct
 *       readback of the exact MOVI/FMOV shapes SLEEF emits (sign mask
 *       0x8000000000000000, inf mask 0x7ff0000000000000, fmov #1.5,
 *       byte-zero over a nonzero prestate, and the original P2 `#1`).
 *   S2  vector-vs-scalar math calibration: the dual kernel's fixed-mode
 *       input construction (position-deterministic u53 + domain edges in
 *       the first 8 slots), full svcntd()/svcntw()-stepped whilelt loops —
 *       then every lane compared against the SCALAR SLEEF u10/u35
 *       functions (pure NEON-free C, no SVE mov-imm on their path). Both
 *       implementations of a family target the same accuracy bound
 *       (u10: 1.0 ulp, u35: 3.5 ulp), so a healthy lane differs by at
 *       most a few ulp; an F3-corrupted lane (lost sign/inf mask or lost
 *       coefficient) is off by ~2^52 ulp. Gate: u10 <= 16 ulp, u35 <= 64
 *       ulp (8-9x margin over the worst legitimate diff); the printed
 *       worst-ulp value is the real evidence.
 *
 * Build: make sleef_vla_semantics (same vendored-SLEEF paths as the dual)
 * Run:   gem5.opt configs/se/arm_chaos.py --cmd <bin> --sve_vl 4
 */
#include <arm_sve.h>
#include <sleef.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define NELEMS 1028   /* same as the dual kernel */
#define N_EDGE 8      /* leading edge-value slots per domain */

static unsigned g_fails = 0;

/* ---------------- S1: F3 applicability, per encoding ---------------- */

static uint64_t rd_u64_of(const double *p)
{
    uint64_t v;
    memcpy(&v, p, sizeof(v));
    return v;
}

static void probe_f3(void)
{
    double buf[34] = {0};   /* svcntd() <= 16 */
    int ok;

    /* MOVI sign mask — the exact SLEEF sin/cos form */
    asm volatile(
        "mov z4.d, %a0\n"
        "ptrue p1.d\n"
        "st1d z4.d, p1, [%1]\n"
        :: "i"(0x8000000000000000), "r"(buf) : "z4", "p1", "memory");
    ok = rd_u64_of(buf) == 0x8000000000000000ULL;
    printf("S1 movi sign-mask   %-7s lane0=%016llx\n",
           ok ? "PASS" : "DEVIATION", (unsigned long long)rd_u64_of(buf));
    g_fails += !ok;

    /* MOVI inf mask — the exp/exp2 family form */
    asm volatile(
        "mov z4.d, %a0\n"
        "ptrue p1.d\n"
        "st1d z4.d, p1, [%1]\n"
        :: "i"(0x7ff0000000000000), "r"(buf) : "z4", "p1", "memory");
    ok = rd_u64_of(buf) == 0x7ff0000000000000ULL;
    printf("S1 movi inf-mask    %-7s lane0=%016llx\n",
           ok ? "PASS" : "DEVIATION", (unsigned long long)rd_u64_of(buf));
    g_fails += !ok;

    /* FMOV FP immediate — the coefficient form */
    asm volatile(
        "fmov z4.d, #1.5000000000000000\n"
        "ptrue p1.d\n"
        "st1d z4.d, p1, [%0]\n"
        :: "r"(buf) : "z4", "p1", "memory");
    ok = rd_u64_of(buf) == 0x3ff8000000000000ULL; /* 1.5 */
    printf("S1 fmov #1.5        %-7s lane0=%016llx\n",
           ok ? "PASS" : "DEVIATION", (unsigned long long)rd_u64_of(buf));
    g_fails += !ok;

    /* byte-zero MOVI over a NONZERO prestate (0 readback is ambiguous —
     * only the prestate surviving proves the write was lost) */
    asm volatile(
        "fmov z4.d, #1.5000000000000000\n"
        "mov z4.b, #0\n"
        "ptrue p1.d\n"
        "st1d z4.d, p1, [%0]\n"
        :: "r"(buf) : "z4", "p1", "memory");
    ok = rd_u64_of(buf) == 0;
    printf("S1 movi z.b,#0      %-7s lane0=%016llx\n",
           ok ? "PASS" : "DEVIATION", (unsigned long long)rd_u64_of(buf));
    g_fails += !ok;

    /* the original P2 form (mov z.d, #1) — re-checked at THIS tier */
    asm volatile(
        "mov z4.d, #1\n"
        "ptrue p1.d\n"
        "st1d z4.d, p1, [%0]\n"
        :: "r"(buf) : "z4", "p1", "memory");
    ok = rd_u64_of(buf) == 1;
    printf("S1 movi #1 (P2)     %-7s lane0=%016llx\n",
           ok ? "PASS" : "DEVIATION", (unsigned long long)rd_u64_of(buf));
    g_fails += !ok;
}

/* ---------------- S2: vector-vs-scalar calibration ---------------- */

static double xd_trig[NELEMS], xd_exp[NELEMS], xd_log[NELEMS];
static float  xf_trig[NELEMS], xf_exp[NELEMS], xf_log[NELEMS];
static double od[NELEMS];
static float  of[NELEMS];

/* position-deterministic u53 — the dual kernel's fixed-mode form */
static double uniform01_pos(int i)
{
    uint64_t h = (uint64_t)i + 0x9E3779B97F4A7C15ULL;
    h ^= h >> 30; h *= 0xBF58476D1CE4E5B9ULL;
    h ^= h >> 27; h *= 0x94D049BB133111EBULL;
    h ^= h >> 31;
    return (double)(h >> 11) / 9007199254740992.0;
}

static double ulp_d(double x)
{
    double a = x < 0 ? -x : x;
    if (a <= 5e-324)
        return 5e-324;
    return nextafter(a, __builtin_inf()) - a;
}
static float ulp_f(float x)
{
    float a = x < 0 ? -x : x;
    if (a <= 1e-45f)
        return 1e-45f;
    return nextafterf(a, __builtin_inff()) - a;
}

static void check_d(const char *name, const double *out, const double *in,
                    double (*scalar)(double), double gate_ulp)
{
    double worst = 0.0;
    unsigned bad = 0;
    for (int i = 0; i < NELEMS; ++i) {
        const double s = scalar(in[i]);
        const double r = (out[i] == s) ? 0.0
                          : (out[i] - s < 0 ? s - out[i] : out[i] - s)
                            / ulp_d(s);
        if (r > worst)
            worst = r;
        if (r > gate_ulp) {
            if (bad == 0)
                fprintf(stderr,
                        "%s @%d: vec=%a sca=%a (%.1f ulp)\n",
                        name, i, out[i], s, r);
            ++bad;
        }
    }
    printf("S2 %-17s worst=%8.2f ulp  %s\n", name, worst,
           bad ? "DEVIATION" : "PASS");
    g_fails += bad;
}
static void check_f(const char *name, const float *out, const float *in,
                    float (*scalar)(float), float gate_ulp)
{
    float worst = 0.0f;
    unsigned bad = 0;
    for (int i = 0; i < NELEMS; ++i) {
        const float s = scalar(in[i]);
        const float r = (out[i] == s) ? 0.0f
                          : (out[i] - s < 0 ? s - out[i] : out[i] - s)
                            / ulp_f(s);
        if (r > worst)
            worst = r;
        if (r > gate_ulp) {
            if (bad == 0)
                fprintf(stderr,
                        "%s @%d: vec=%a sca=%a (%.1f ulp)\n",
                        name, i, (double)out[i], (double)s, (double)r);
            ++bad;
        }
    }
    printf("S2 %-17s worst=%8.2f ulp  %s\n", name, (double)worst,
           bad ? "DEVIATION" : "PASS");
    g_fails += bad;
}

int main(void)
{
    const uint64_t vl_bytes = svcntb();
    if (vl_bytes < 16 || vl_bytes > 128) {
        fprintf(stderr, "unsupported VL %llu bytes\n",
                (unsigned long long)vl_bytes);
        return 3;
    }
    fprintf(stderr, "sleef_vla_semantics: nelems=%d vl_bytes=%llu "
            "svcntd=%u svcntw=%u\n", NELEMS,
            (unsigned long long)vl_bytes,
            (unsigned)svcntd(), (unsigned)svcntw());

    probe_f3();

    /* inputs: dual-kernel fixed-mode fill + edge values up front */
    for (int i = 0; i < NELEMS; ++i)
        xd_trig[i] = (uniform01_pos(i) * 2.0 - 1.0) * 3.141592653589793;
    for (int i = 0; i < NELEMS; ++i)
        xd_exp[i] = (uniform01_pos(i) * 2.0 - 1.0) * 20.0;
    for (int i = 0; i < NELEMS; ++i)
        xd_log[i] = (uniform01_pos(i) + 1.0e-300) * 1.0e10;
    for (int i = 0; i < NELEMS; ++i) {
        float u = (float)uniform01_pos(i);
        xf_trig[i] = (u * 2.0f - 1.0f) * 3.14159265f;
    }
    for (int i = 0; i < NELEMS; ++i) {
        float u = (float)uniform01_pos(i);
        xf_exp[i] = (u * 2.0f - 1.0f) * 20.0f;
    }
    for (int i = 0; i < NELEMS; ++i) {
        float u = (float)uniform01_pos(i);
        xf_log[i] = (u + 1.0e-30f) * 1.0e10f;
    }
    /* domain edges (incl. the negative side where the sign masks matter) */
    {
        const double e_trig[N_EDGE] = { -3.141592653589793, -1.5707963267948966,
                                        -1.0, -1e-10, 1e-10, 1.0,
                                        1.5707963267948966, 3.14159265358979 };
        const double e_exp[N_EDGE] = { -19.999999999999996, -1.0, -1e-10, 0.0,
                                       1e-10, 1.0, 10.0, 19.999999999999996 };
        const double e_log[N_EDGE] = { 1e-290, 1e-100, 1e-10, 1e-2,
                                       1.0, 2.0, 1e5, 1e10 };
        const float ef_trig[N_EDGE] = { -3.14159265f, -1.5707963f, -1.0f,
                                        -1e-10f, 1e-10f, 1.0f, 1.5707963f,
                                        3.1415925f };
        const float ef_exp[N_EDGE] = { -20.0f, -1.0f, -1e-10f, 0.0f,
                                       1e-10f, 1.0f, 10.0f, 20.0f };
        const float ef_log[N_EDGE] = { 1e-20f, 1e-10f, 1e-2f, 1.0f,
                                       2.0f, 1e3f, 1e6f, 1e10f };
        memcpy(xd_trig, e_trig, sizeof(e_trig));
        memcpy(xd_exp, e_exp, sizeof(e_exp));
        memcpy(xd_log, e_log, sizeof(e_log));
        memcpy(xf_trig, ef_trig, sizeof(ef_trig));
        memcpy(xf_exp, ef_exp, sizeof(ef_exp));
        memcpy(xf_log, ef_log, sizeof(ef_log));
    }

    /* the dual kernel's own loop shapes, family by family */
    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_sindx_u10sve(svld1_f64(pg, &xd_trig[i])));
    }
    check_d("sin  d u10 vs sca", od, xd_trig, Sleef_sin_u10, 16.0);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_cosdx_u10sve(svld1_f64(pg, &xd_trig[i])));
    }
    check_d("cos  d u10 vs sca", od, xd_trig, Sleef_cos_u10, 16.0);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_expdx_u10sve(svld1_f64(pg, &xd_exp[i])));
    }
    check_d("exp  d u10 vs sca", od, xd_exp, Sleef_exp_u10, 16.0);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_logdx_u10sve(svld1_f64(pg, &xd_log[i])));
    }
    check_d("log  d u10 vs sca", od, xd_log, Sleef_log_u10, 16.0);

    for (int i = 0; i < NELEMS; i += (int)svcntw()) {
        const svbool_t pgf = svwhilelt_b32((uint64_t)i, (uint64_t)NELEMS);
        svst1_f32(pgf, &of[i],
                  Sleef_sinfx_u10sve(svld1_f32(pgf, &xf_trig[i])));
    }
    check_f("sin  f u10 vs sca", of, xf_trig, Sleef_sinf_u10, 16.0f);

    for (int i = 0; i < NELEMS; i += (int)svcntw()) {
        const svbool_t pgf = svwhilelt_b32((uint64_t)i, (uint64_t)NELEMS);
        svst1_f32(pgf, &of[i],
                  Sleef_cosfx_u10sve(svld1_f32(pgf, &xf_trig[i])));
    }
    check_f("cos  f u10 vs sca", of, xf_trig, Sleef_cosf_u10, 16.0f);

    for (int i = 0; i < NELEMS; i += (int)svcntw()) {
        const svbool_t pgf = svwhilelt_b32((uint64_t)i, (uint64_t)NELEMS);
        svst1_f32(pgf, &of[i],
                  Sleef_expfx_u10sve(svld1_f32(pgf, &xf_exp[i])));
    }
    check_f("exp  f u10 vs sca", of, xf_exp, Sleef_expf_u10, 16.0f);

    for (int i = 0; i < NELEMS; i += (int)svcntw()) {
        const svbool_t pgf = svwhilelt_b32((uint64_t)i, (uint64_t)NELEMS);
        svst1_f32(pgf, &of[i],
                  Sleef_logfx_u10sve(svld1_f32(pgf, &xf_log[i])));
    }
    check_f("log  f u10 vs sca", of, xf_log, Sleef_logf_u10, 16.0f);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_sindx_u35sve(svld1_f64(pg, &xd_trig[i])));
    }
    check_d("sin  d u35 vs sca", od, xd_trig, Sleef_sin_u35, 64.0);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_cosdx_u35sve(svld1_f64(pg, &xd_trig[i])));
    }
    check_d("cos  d u35 vs sca", od, xd_trig, Sleef_cos_u35, 64.0);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_logdx_u35sve(svld1_f64(pg, &xd_log[i])));
    }
    check_d("log  d u35 vs sca", od, xd_log, Sleef_log_u35, 64.0);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_exp2dx_u35sve(svld1_f64(pg, &xd_exp[i])));
    }
    check_d("exp2 d u35 vs sca", od, xd_exp, Sleef_exp2_u35, 64.0);

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    return g_fails ? 1 : 0;
}
