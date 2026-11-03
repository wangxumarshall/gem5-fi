#ifndef __CPU_O3_CHAOS_DECODED_FP_HH__
#define __CPU_O3_CHAOS_DECODED_FP_HH__

// Pure AArch64 FP instruction decoder used by the FSU result injector.
//
// It depends only on <cstdint>, so tests/test_chaos_fsu_decoded_fp_cpp.py can
// compile and run it with the host compiler without a gem5 build.
//
// The decoder answers, from the real 32-bit encoding of a dynamic instruction:
//   - scalar VFP vs NEON vector vs unsupported (FP16/SVE/FCVT/by-element...)
//   - FP32 vs FP64
//   - element width and lane count for NEON vectors
// Anything it cannot prove is marked reliable=false and the caller MUST fail
// closed (do not inject, do not count eligible).
//
// Notes (verified with GNU as/objdump, see tests):
//   * Scalar VFP: (enc & 0xFE000000) == 0x1E000000; type bits [23:22]:
//       00 = FP32 (S), 01 = FP64 (D), 11 = FP16 (H, unsupported),
//       10 = reserved/unknown.
//   * FCVT/int-convert uses the same scalar top but the type bit describes
//     the source/destination mix, not the result precision -> unsupported.
//   * NEON FP vectors: bits [28:24] == 0b01110. Element width is bit22
//     (NOT size[23:22]); bit23 can be an operation selector (e.g. FMINNM
//     v.4s has size=10 but is still 32-bit). Q=bit30 selects 128/64-bit.
//   * By-element/indexed [28:24]=0b01111, AdvSIMD scalar (top 0x5E/0x7E),
//     FCADD/FCMLA, FP16, FMLAL/FMLSL and SVE/SME are unsupported.

#include <cstdint>

namespace gem5
{
namespace chaos_fsu
{

enum class FpFamily : uint8_t
{
    Other,
    ScalarFloat,
    Cvt,
    SimdFloat,
};

enum class FpKind : uint8_t
{
    NonFp,
    Unknown,
    ScalarVfp,
    NeonVector,
    NeonScalar,
    SveSme,
    Fp16Scalar,
    Fp16Neon,
    Mixed,
    Cvt,
};

struct DecodedFp
{
    FpKind kind = FpKind::Unknown;
    int precision_bits = 0;   // 0 / 16 / 32 / 64
    int element_width = 0;    // 0 / 16 / 32 / 64
    int lanes = 0;            // 0 / 1 / 2 / 4 / 8 / 16
    bool reliable = false;
    const char *reason = "unknown";
};

inline const char *
fpKindName(FpKind kind)
{
    switch (kind) {
      case FpKind::NonFp: return "non_fp";
      case FpKind::Unknown: return "unknown";
      case FpKind::ScalarVfp: return "scalar_vfp";
      case FpKind::NeonVector: return "neon_vector";
      case FpKind::NeonScalar: return "neon_scalar";
      case FpKind::SveSme: return "sve_sme";
      case FpKind::Fp16Scalar: return "fp16_scalar";
      case FpKind::Fp16Neon: return "fp16_neon";
      case FpKind::Mixed: return "mixed";
      case FpKind::Cvt: return "cvt";
      default: return "unknown";
    }
}

inline DecodedFp
decodedPrecision(uint32_t enc, FpFamily fam)
{
    auto fail = [](FpKind kind, const char *why) {
        DecodedFp d;
        d.kind = kind;
        d.reliable = false;
        d.reason = why;
        return d;
    };

    if (fam == FpFamily::Other)
        return fail(FpKind::NonFp, "opclass");
    if (fam == FpFamily::Cvt)
        return fail(FpKind::Cvt, "fcvt/int-convert");

    if (fam == FpFamily::ScalarFloat) {
        if ((enc & 0xFE000000U) != 0x1E000000U)
            return fail(FpKind::NonFp, "scalar-not-vfp-top");
        const unsigned type = (enc >> 22) & 3U;
        DecodedFp d;
        d.kind = FpKind::ScalarVfp;
        d.lanes = 1;
        if (type == 0) {
            d.precision_bits = d.element_width = 32;
            d.reliable = true;
            d.reason = "scalar-type00";
            return d;
        }
        if (type == 1) {
            d.precision_bits = d.element_width = 64;
            d.reliable = true;
            d.reason = "scalar-type01";
            return d;
        }
        if (type == 3)
            return fail(FpKind::Fp16Scalar, "scalar-type11-fp16");
        return fail(FpKind::Unknown, "scalar-type10");
    }

    // SIMD FP family. SVE/SME dispatch is bit27==0 in AArch64.
    if (((enc >> 27) & 1U) == 0)
        return fail(FpKind::SveSme, "sve-sme-bit27=0");

    const unsigned m2824 = (enc >> 24) & 0x1FU;
    const bool q = (enc >> 30) & 1U;
    const bool u = (enc >> 29) & 1U;
    const bool bit21 = (enc >> 21) & 1U;
    const bool bit22 = (enc >> 22) & 1U;
    const bool bit10 = (enc >> 10) & 1U;

    if (m2824 == 0x0F)
        return fail(FpKind::Mixed, "indexed/by-element/modimm/shift");
    if (m2824 != 0x0E)
        return fail(FpKind::NeonScalar, "advsimd-scalar/other");

    // FP16 3-same: bit22=1, bit21=0, [15:14]==00, bit10=1.
    if (!bit21 && bit22 && ((enc >> 14) & 3U) == 0 && bit10)
        return fail(FpKind::Fp16Neon, "fp16-3same");
    // FP16 2-reg-misc: bit21=1, [20:19]==11.
    if (bit21 && ((enc >> 19) & 3U) == 3)
        return fail(FpKind::Fp16Neon, "fp16-2misc");

    auto vector = [&](const char *why) {
        if (bit22 && !q)
            return fail(FpKind::Unknown, "1d-invalid");
        const int w = bit22 ? 64 : 32;
        DecodedFp d;
        d.kind = FpKind::NeonVector;
        d.precision_bits = w;
        d.element_width = w;
        d.lanes = (q ? 128 : 64) / w;
        d.reliable = true;
        d.reason = why;
        return d;
    };

    // 3-same FP (FADD/FMUL/FMLA/FDIV/FMIN/...).
    if (bit21 && bit10) {
        const unsigned op = (enc >> 11) & 0x1FU;
        if (op < 0x18 || op > 0x1F)
            return fail(FpKind::Unknown, "3same-non-fp-opcode");
        if ((op == 0x19 && u) || (op == 0x1D && !u))
            return fail(FpKind::Mixed, "fmlal/fmlsl");
        return vector("neon-3same");
    }
    // 2-reg-misc FP (FABS/FNEG/FSQRT/FRECPE/...); Cvt already excluded.
    if (bit21 && !bit10 && ((enc >> 17) & 3U) == 0)
        return vector("neon-2misc");

    // FCADD/FCMLA and other 3-reg-extension shapes.
    return fail(FpKind::Unknown, "neon-other");
}

} // namespace chaos_fsu
} // namespace gem5

#endif // __CPU_O3_CHAOS_DECODED_FP_HH__
