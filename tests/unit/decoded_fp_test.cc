// Host-side unit test for cpu/o3/CHAOSFPU/decoded_fp.hh.
// Compiled and run by tests/test_chaos_fsu_decoded_fp_cpp.py.

#include <cstdio>

#include "cpu/o3/CHAOSFPU/decoded_fp.hh"

using namespace gem5::chaos_fsu;

static int failures = 0;

#define CHECK(cond) do {                                                    \
    if (!(cond)) {                                                          \
        std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        ++failures;                                                         \
    }                                                                       \
} while (0)

struct Vec {
    const char *asm_;
    uint32_t enc;
    FpFamily fam;
    FpKind kind;
    int precision;
    int width;
    int lanes;
    bool reliable;
};

static const Vec V[] = {
    {"fadd s0,s1,s2",      0x1E222820, FpFamily::ScalarFloat, FpKind::ScalarVfp, 32, 32, 1, true},
    {"fmul s0,s1,s2",      0x1E220820, FpFamily::ScalarFloat, FpKind::ScalarVfp, 32, 32, 1, true},
    {"fdiv s0,s1,s2",      0x1E221820, FpFamily::ScalarFloat, FpKind::ScalarVfp, 32, 32, 1, true},
    {"fsqrt s0,s1",        0x1E21C020, FpFamily::ScalarFloat, FpKind::ScalarVfp, 32, 32, 1, true},
    {"fmadd s0,s1,s2,s3",  0x1F020C20, FpFamily::ScalarFloat, FpKind::ScalarVfp, 32, 32, 1, true},
    {"fadd d0,d1,d2",      0x1E622820, FpFamily::ScalarFloat, FpKind::ScalarVfp, 64, 64, 1, true},
    {"fmul d0,d1,d2",      0x1E620820, FpFamily::ScalarFloat, FpKind::ScalarVfp, 64, 64, 1, true},
    {"fdiv d0,d1,d2",      0x1E621820, FpFamily::ScalarFloat, FpKind::ScalarVfp, 64, 64, 1, true},
    {"fsqrt d0,d1",        0x1E61C020, FpFamily::ScalarFloat, FpKind::ScalarVfp, 64, 64, 1, true},
    {"fmadd d0,d1,d2,d3",  0x1F420C20, FpFamily::ScalarFloat, FpKind::ScalarVfp, 64, 64, 1, true},
    {"fadd v0.4s",         0x4E22D420, FpFamily::SimdFloat, FpKind::NeonVector, 32, 32, 4, true},
    {"fadd v0.2s",         0x0E22D420, FpFamily::SimdFloat, FpKind::NeonVector, 32, 32, 2, true},
    {"fmla v0.4s",         0x4E22CC20, FpFamily::SimdFloat, FpKind::NeonVector, 32, 32, 4, true},
    {"fmul v0.4s",         0x6E22DC20, FpFamily::SimdFloat, FpKind::NeonVector, 32, 32, 4, true},
    {"fdiv v0.4s",         0x6E22FC20, FpFamily::SimdFloat, FpKind::NeonVector, 32, 32, 4, true},
    {"fsqrt v0.4s",        0x6EA1F820, FpFamily::SimdFloat, FpKind::NeonVector, 32, 32, 4, true},
    {"fadd v0.2d",         0x4E62D420, FpFamily::SimdFloat, FpKind::NeonVector, 64, 64, 2, true},
    {"fmla v0.2d",         0x4E62CC20, FpFamily::SimdFloat, FpKind::NeonVector, 64, 64, 2, true},
    {"fmul v0.2d",         0x6E62DC20, FpFamily::SimdFloat, FpKind::NeonVector, 64, 64, 2, true},
    {"fdiv v0.2d",         0x6E62FC20, FpFamily::SimdFloat, FpKind::NeonVector, 64, 64, 2, true},
    {"fsqrt v0.2d",        0x6EE1F820, FpFamily::SimdFloat, FpKind::NeonVector, 64, 64, 2, true},
    {"fminnm v0.4s",       0x4EA2C420, FpFamily::SimdFloat, FpKind::NeonVector, 32, 32, 4, true},
    {"fadd h0,h1,h2",      0x1EE22820, FpFamily::ScalarFloat, FpKind::Fp16Scalar, 0, 0, 0, false},
    {"fadd v0.8h",         0x4E421420, FpFamily::SimdFloat, FpKind::Fp16Neon, 0, 0, 0, false},
    {"fcvt s0,d0",         0x1E624000, FpFamily::Cvt, FpKind::Cvt, 0, 0, 0, false},
    {"fcvt d0,s0",         0x1E22C000, FpFamily::Cvt, FpKind::Cvt, 0, 0, 0, false},
    {"scvtf s0,w1",        0x1E220020, FpFamily::Cvt, FpKind::Cvt, 0, 0, 0, false},
    {"scvtf d0,x1",        0x9E620020, FpFamily::Cvt, FpKind::Cvt, 0, 0, 0, false},
    {"fcvtzs w0,s1",       0x1E380020, FpFamily::Cvt, FpKind::Cvt, 0, 0, 0, false},
    {"fmlal v0.4s",        0x4E22EC20, FpFamily::SimdFloat, FpKind::Mixed, 0, 0, 0, false},
    {"fmla v0.4s,v2.s[0]", 0x4F821020, FpFamily::SimdFloat, FpKind::Mixed, 0, 0, 0, false},
    {"fmla v0.2d,v2.d[0]", 0x4FC21020, FpFamily::SimdFloat, FpKind::Mixed, 0, 0, 0, false},
    {"fmul v0.4s,v2.s[0]", 0x4F829020, FpFamily::SimdFloat, FpKind::Mixed, 0, 0, 0, false},
    {"fadd z0.s",          0x65820020, FpFamily::SimdFloat, FpKind::SveSme, 0, 0, 0, false},
    {"fadd z0.d",          0x65C20020, FpFamily::SimdFloat, FpKind::SveSme, 0, 0, 0, false},
    {"add x0,x1,x2",       0x8B020020, FpFamily::Other, FpKind::NonFp, 0, 0, 0, false},
    {"add v0.4s",          0x4EA28420, FpFamily::Other, FpKind::NonFp, 0, 0, 0, false},
    {"faddp s0,v1.2s",     0x7E30D820, FpFamily::SimdFloat, FpKind::NeonScalar, 0, 0, 0, false},
    {"fmla s0,s1,v2.s[0]", 0x5F821020, FpFamily::SimdFloat, FpKind::NeonScalar, 0, 0, 0, false},
};

int
main()
{
    for (const auto &v : V) {
        const DecodedFp d = decodedPrecision(v.enc, v.fam);
        if (d.kind != v.kind || d.precision_bits != v.precision ||
            d.element_width != v.width || d.lanes != v.lanes ||
            d.reliable != v.reliable) {
            std::fprintf(stderr,
                "FAIL %-22s enc=0x%08x kind=%s prec=%d w=%d lanes=%d rel=%d "
                "expected kind=%s prec=%d w=%d lanes=%d rel=%d (%s)\n",
                v.asm_, v.enc, fpKindName(d.kind), d.precision_bits,
                d.element_width, d.lanes, (int)d.reliable,
                fpKindName(v.kind), v.precision, v.width, v.lanes,
                (int)v.reliable, d.reason);
            ++failures;
        }
    }
    if (failures) {
        std::fprintf(stderr, "%d failure(s)\n", failures);
        return 1;
    }
    std::printf("decoded_fp: %zu vectors passed\n", sizeof(V) / sizeof(V[0]));
    return 0;
}
