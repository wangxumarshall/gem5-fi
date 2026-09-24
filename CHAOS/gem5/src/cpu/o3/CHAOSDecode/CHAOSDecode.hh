#ifndef __CPU_O3_CHAOS_DECODE_HH__
#define __CPU_O3_CHAOS_DECODE_HH__

#include <random>
#include <string>
#include <vector>

#include "params/CHAOSDecode.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/reg_class.hh"
#include "cpu/static_inst_fwd.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class DynInst; } }
namespace gem5 { class InstDecoder; }
// W6 batch 2 (D08-D10) helper signatures (definitions in CHAOSDecode.cc,
// which includes arch/arm/decoder.hh for the full types). NOTE: the EMI is
// passed as its raw uint64_t storage — ArmISA::ExtMachInst is a BitUnion
// TYPEDEF (EndBitUnion), NOT a struct tag, so it cannot be forward-declared
// here; BitUnionOperators provides the implicit uint64_t conversion both
// ways (bitunion.hh:267/274), and each helper rebuilds the full EMI via
// `ExtMachInst emi; emi = emi_raw;` (the proven batch-1 assignment path).
namespace gem5 { namespace ArmISA { class Decoder; } }

namespace gem5
{

class CHAOSDecode : public SimObject
{
  public:
    CHAOSDecode(const CHAOSDecodeParams &p);
    ~CHAOSDecode();

    void startup() override;  // self-attach to CPU.chaosDecode

    // Called from rename.cc AFTER inst->flattenedDestIdx(dest_idx,
    // flat_dest_regid) is set. May MUTATE flat_dest_regid's index to another
    // legal 0-30 integer reg (dest_reg_sub F5). Per-inst (safe, _flatDestIdx
    // is per-DynInst, not shared staticInst). Returns true if injected.
    // LEGACY §2.14 mode only — the W6 encoding modes never enter here.
    bool maybeCorrupt(int dest_idx, RegId &flat_dest_regid,
                      const o3::DynInst *inst);

    // W6 (D01-D07, ooo 04-design-matrix R2-R8 Int Decode): called from
    // fetch.cc right after `staticInst = dec_ptr->decode(this_pc)` and
    // BEFORE the isMacroop() branch. Extracts the 8-byte ExtMachInst from
    // the decoded StaticInst (ArmStaticInst::asBytes), corrupts the low 32
    // encoding bits per the mode, re-decodes via
    // ArmISA::Decoder::decodeChaos (cache-bypassing) and RETURNS the
    // replacement StaticInstPtr (nullptr = no injection — fetch keeps the
    // original). The caller only rebinds its LOCAL staticInst variable, so
    // the fetch loop's macroop/pcOffset bookkeeping downstream applies to
    // the replacement naturally.
    StaticInstPtr maybeCorruptEncoding(StaticInstPtr orig,
                                       InstDecoder *dec, Addr pc);

  private:
    BaseCPU *cpu;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;
    // Sampling-bias fix (findings.md Phase 2.2/3.0, same as CHAOSL1DForward
    // 7387649): skip a geometric(p=0.1) number of eligible events before
    // the first injection, so maxFaults=1 lands on a seed-dependent event
    // instead of always the first eligible one (same dynamic instruction
    // every rep on a deterministic stream).
    uint64_t events_to_skip = 0;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();

    // ---- W6 encoding-corruption modes (D01-D07) ----
    enum class Mode { DestRegSub,            // legacy §2.14 (rename hook)
                      OpcodeBitflip,         // D01 opcode field, 1 bit
                      OpcodeBitflip2,        // D02 opcode field, 2 bits
                      OpcodeSwap,            // D03 opcode 换值 (legal pair)
                      RegBitflip,            // D04 reg-number field, 1 bit
                      RegBitflip2,           // D05 reg-number field, 2 bits
                      ImmBitflip,            // D06 immediate field, 1 bit
                      ImmBitflip2,           // D07 immediate field, 2 bits
                      // ---- W6 batch 2 (D08-D10) ----
                      SignExtBit,            // D08 sign-extension bit of the
                                             // format-located immediate
                      ImmSubfieldShift,      // D09 immediate subfield
                                             // mis-assembly (transposed)
                      CrackCtrl,             // D10 macroop crack-control
                                             // (addressing-mode µop-stream
                                             // perturbation on LDP/STP)
                      // ---- W7 batch 1 (D56-D61, ooo 04-design-matrix
                      // R57-R62 FP/SIMD Decode) ----
                      FpOpcodeBitflip,       // D56 FP opcode field, 1 bit
                      FpOpcodeBitflip2,      // D57 FP opcode field, 2 bits
                      FpOpcodeSwap,          // D58 FP opcode 换值 (legal
                                             // operand-format-compatible
                                             // FP pair table)
                      FpRegBitflip,          // D59 V-reg-number field, 1 bit
                      FpRegBitflip2,         // D60 V-reg-number field, 2 bits
                      FpRouteBit };          // D61 instruction-route bit
                                             // (opClass-change predicate)
    Mode fi_mode = Mode::DestRegSub;
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m) const;

    // Candidate positional bit sets (plan 2026-09-24 W6; the log line
    // carries the actual flipped bits so every injection is recomputable
    // from orig_enc ^ (1<<bit) == new_enc):
    //   opcode bits: the high opcode region of the A64 encoding
    //                (sf/op/S + the 28-24 opcode group + bit 21).
    //   reg bits:    A64 fixed register-number positions Rd[4:0],
    //                Rn[9:5], Rm[20:16].
    //   imm bits:    the contiguous immediate region [21:10] (imm12 /
    //                immr+imms / imm6), the dominant imm window for
    //                data-processing and load/store formats.
    static constexpr uint32_t kOpcodeBits[] = {31, 30, 29, 28, 27, 26,
                                               25, 24, 21};
    static constexpr uint32_t kRegBits[]    = {0, 1, 2, 3, 4,
                                               5, 6, 7, 8, 9,
                                               16, 17, 18, 19, 20};
    static constexpr uint32_t kImmBits[]    = {10, 11, 12, 13, 14,
                                               15, 16, 17, 18, 19,
                                               20, 21};

    // D03 opcode 换值: format-compatible legal-opcode swap table. Every
    // rule was verified against real GNU-as encodings (see the W6 plan
    // verification record): (mask, match, xor_bits, rule_name). First
    // match wins; no match = the instruction is not eligible for D03.
    struct SwapRule { uint32_t mask; uint32_t match; uint32_t xor_bits;
                      const char *name; };
    static const SwapRule kSwapRules[];
    static const SwapRule *matchSwapRule(uint32_t enc);

    // ---- W7 batch 1 (D56-D61, ooo 04-design-matrix R57-R62 FP/SIMD
    // Decode). Same fetch-decode asBytes/decodeChaos engine as W6 —
    // architecture-agnostic (findings.md W7 spike item 1). The W7 addition
    // is a per-mode fpOnly eligibility gate plus FP-specific bit sets. ----
    //
    // fpOnly scope (DOCUMENTED DESIGN DECISION, per the W7 plan): an
    // instruction is FP-eligible iff StaticInst::opClass() is a scalar
    // Float* or SIMD SimdFloat* class — the exact isFpOpClass set of
    // CHAOSFPU.cc:88-98. Integer SIMD (SimdAdd/SimdMul/... on V regs) is
    // OUT of scope for W7.1: it is not in the 04 "FP/SIMD" FP-opclass
    // reading and its opClass routing belongs to the Int Decode unit
    // (D04/D05). Honest limitation, not a silent gap.
    static bool isFpOpClass(OpClass oc);

    // Candidate positional bit sets. kFpOpcodeBits: the FP/SIMD opcode
    // region enc[23:10] (spike-verified: for the A64 FP formats this window
    // covers ftype/size[23:22], the fixed-1 bit21, Rm[20:16] and the
    // op[15:10] field — the operation-discriminating bits of the scalar
    // single-data-pass / fused / SIMD 3-same formats). NOTE the deliberate
    // overlap with Rm: like W6's kImmBits, the log line carries the actual
    // bit so every injection stays recomputable (orig ^ (1<<b) == new).
    static constexpr uint32_t kFpOpcodeBits[] = {
        23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10 };
    // D61 route candidates: the top-level A64 instruction-class field
    // bits[28:24] (x1110/x1111 = FP/ASIMD vs the integer data-proc /
    // load-store / branch groups) — the bits the "integer vs FP/SIMD
    // dispatch queue" routing decision reads. Single bit only (the 04
    // matrix: 该字段本身为单比特控制位，无多比特版本).
    static constexpr uint32_t kFpRouteBits[] = { 24, 25, 26, 27, 28 };

    // D58 FP opcode 换值: format-compatible legal FP-opcode swap table.
    // Every (mask, match, xor_bits) row was CLOSED-LOOP verified against
    // real GNU-as encodings on this aarch64 host (2026-09-24 W7 record,
    // /tmp/w71/verify_rules.py): for every real member encoding of the
    // pair across ALL lane variants (S/D/H, .2s/.4s/.2d) and register
    // combinations, (enc & mask) == match AND enc^xor re-disassembles to
    // the partner mnemonic with an IDENTICAL register operand list; a
    // 46-instruction negative corpus (fmov/fsqrt/fmulx/fabd/fcmgt/facge/
    // frint/fccmp/fcsel/scvtf/by-element/FP16-3-same/fcvtl/fcvtn) matches
    // NO rule. Scalar rows (top byte 0x1E/0x1F):
    //   fadd d0,d1,d2 = 0x1e622820 <-> fsub = 0x1e623820  (xor bit12)
    //   fmul d0,d1,d2 = 0x1e620820 <-> fdiv = 0x1e621820  (xor bit12)
    //   fmax d0,d1,d2 = 0x1e624820 <-> fmin = 0x1e625820  (xor bit12)
    //   fmaxnm         = 0x1e626820 <-> fminnm = 0x1e627820 (xor bit12)
    //   fmadd d0..d3   = 0x1f420c20 <-> fmsub  = 0x1f428c20 (xor bit15=O2;
    //                   bit21=O1 pinned — Ra[14:10] is a REGISTER, left free)
    //   fnmadd         = 0x1f620c20 <-> fnmsub  = 0x1f628c20 (xor bit15)
    //   fcmp d0,d1     = 0x1e612000 <-> fcmpe   = 0x1e612010 (xor bit4 = E
    //                   flag; the fcmp #0.0 forms 0x1e602008/0x1e602018
    //                   share the rule — opcode2[3:0] free)
    // Vector rows (3-same, bits[28:24]=01110, bit21=1; 2-reg-misc for
    // fabs/fneg):
    //   fadd v0.2d     = 0x4e62d420 <-> fsub v  = 0x4ee2d420 (xor bit23=U;
    //                   bit29 pinned 0 excludes FABD 0x6ea2d420)
    //   fmax v0.2d     = 0x4e62f420 <-> fmin v  = 0x4ee2f420 (xor bit23)
    //   fmaxnm v0.2d   = 0x4e62c420 <-> fminnm v= 0x4ee2c420 (xor bit23)
    //   fmla v0.2d     = 0x4e62cc20 <-> fmls v  = 0x4ea2cc20 (xor bit23)
    //   fcmeq v0.2d    = 0x4e62e420 <-> fcmge v = 0x6e62e420 (xor bit29;
    //                   bit23 pinned 0 excludes FCMGT 0x6ee2e420)
    //   fmul v0.2d     = 0x6e62dc20 <-> fdiv v  = 0x6e62fc20 (xor bit13;
    //                   bit29 pinned 1 excludes FMULX 0x4e22dc20)
    //   fabs v0.4s     = 0x4ea0f820 <-> fneg v  = 0x6ea0f820 (xor bit29;
    //                   Rm pinned 00000 excludes the FRINT/FSQRT family)
    static const SwapRule kFpSwapRules[];
    static const SwapRule *matchFpSwapRule(uint32_t enc);

    // ---- W6 batch 2 (D08/D09/D10, ooo 04-design-matrix R9-R11) ----
    //
    // D08 sign_ext_bit: per-instruction-format location of the immediate's
    // TOP encoded bit (the bit the decoder's sign-extension logic reads for
    // sext formats — imm9/imm19/imm26/adrp immhi — and the immediate's
    // magnitude MSB for unsigned formats per the plan: imm12 bit11,
    // immr+imms 顶位). NOT a random bit: exactly this one bit is flipped.
    // Every (mask, match, sign_bit) row was verified against real GNU-as
    // encodings on this aarch64 host (2026-09-24, /tmp/w6b2/fmt.s):
    //   add x0,x1,#1     = 0x91000420 (group 100010 imm, imm12[21:10])
    //   and/orr/eor/ands = 0x92400c20/0xb2400c20/0xd2400c20/0xf2400c20
    //                      (N[22] immr[15:10] imms[20:16]; top = bit 20)
    //   ldr x0,[x1,#8]   = 0xf9400420 / str = 0xf9000420 (imm12[21:10])
    //   ldur x0,[x1,#-8] = 0xf85f8020 / stur = 0xf81f8020 (imm9[20:12],
    //                      true sign bit = bit 20)
    //   b.eq = 0x540001c0 (imm19[23:5]) / cbz = 0xb40001a0 / cbnz = 0xb5000180
    //   tbz  = 0x36180160 / tbnz = 0x37180140 (imm14[18:5], bit 18)
    //   b    = 0x14000009 / bl = 0x94000008 (imm26[25:0], bit 25)
    //   adr  = 0x100000e0 / adrp = 0x90000000 (immhi[23:5]+immlo[30:29];
    //                      21-bit imm's sign = immhi MSB = bit 23)
    //   ldr x0,lit       = 0x580000a0 (imm19[23:5])
    //   movz/movn/movk   = 0xd2824680/0x92824680/0xf2a24680 (imm16[20:5])
    struct SignImmFormat { uint32_t mask; uint32_t match;
                           uint8_t sign_bit, fhi, flo; const char *name; };
    static const SignImmFormat kSignImmFormats[];

    // D09 imm_subfield_shift: formats whose immediate is assembled from
    // MULTIPLE NAMED encoding subfields. The fault transposes two
    // equal-width subfields (the fragments of the value are placed at the
    // wrong bit positions — 04: "该放到 imm[19:16] 位置的子字段被错误地
    // 拼到了 imm[15:12] 的位置"). Field A bits [hi_a:lo_a] swap with field
    // B bits [hi_b:lo_b] (equal width by construction):
    //   logical imm  (and/orr/eor/ands imm, "immr/imms 类"):
    //        imms[20:16] <-> immr[15:10]   (verified: and x0,x1,#0xf =
    //        0x92400c20 -> N=1, imms=0, immr=3)
    //   adr/adrp     ("拆装类"): immhi[1:0] (enc 6:5) <-> immlo (enc 30:29)
    //        (verified: adr x0,.+28 = 0x100000e0 -> immhi=7, immlo=0)
    //   movz/movn/movk ("移位类"): hw[22:21] <-> imm16[15:14] (enc 20:19)
    //        (verified: movk x0,#0x1234,lsl#16 = 0xf2a24680 -> hw=1,
    //        imm16=0x1234)
    //   add/sub imm12+sh ("移位类"): sh[23:22] <-> imm12[11:10] (enc 21:20)
    //        (verified: adds x0,x1,#1,lsl#12 = 0xb1400420 -> sh=1, imm12=1)
    // Formats with a single contiguous immediate (ldr/str imm12, ldur imm9,
    // b/imm26, b.cond/imm19, ldr-lit) are honestly skipped WITH a log line
    // (no multi-named-subfield structure to mis-assemble).
    struct SubfieldFormat { uint32_t mask; uint32_t match;
                            uint8_t hi_a, lo_a, hi_b, lo_b;
                            const char *name; };
    static const SubfieldFormat kSubfieldFormats[];

    // D10 crack_ctrl (exploratory): gem5 v25 A64 "cracking" = decoding to a
    // macroop (PairMemOp LdpStp for LDP/STP/LDPSW, macromem.hh:473;
    // fetch.cc walks curMacroop->fetchMicroop(upc), upc 0-based, last µop
    // flagged IsLastMicroop). There is NO runtime crack-latch bit — the
    // decision is baked into the static ISA decode table — so the fault is
    // modeled at the encoding level by flipping the pair-op addressing-mode
    // field enc[24:23] (type: 00 ldnp/stnp, 01 post, 10 offset, 11 pre;
    // aarch64.isa:1670-1685) on an instruction that decoded to a MACROOP:
    //   offset(10) -> pre(11): +1 µop, a spurious writeback µop appears
    //               ("不该拆的指令被拆": Rn clobbered)
    //   pre(11) -> offset(10): -1 µop, the writeback µop is lost
    //               ("该拆的指令不拆": stale base pointer)
    //   post(01) <-> offset(10): composition swap (writeback µop vs
    //               addr-generation µop), count unchanged
    // µop counts are measured at injection time by a bounded
    // fetchMicroop/isLastMicroop walk and logged (the 04 metric:
    // "µop 数量与无故障基线的偏差"). BLOCKER (recorded, not silently
    // dropped): force-cracking a NON-macroop instruction (e.g. plain LDR,
    // which gem5 decodes as one single-µop StaticInst) has no encoding-
    // level control — no flippable bit changes macroop-ness — and
    // synthesizing a truncated macroop is blocked by shared cached µop
    // objects (no clone API; mutating their flags corrupts the ISA cache).
    // Non-macroop instructions in crack_ctrl mode get an honest skip log.
    static uint32_t countMicroops(const StaticInst *mop);

    // The three D08-D10 injection helpers (called after the shared
    // window/skip/probability gates; each does its own format eligibility,
    // re-decode, semantic predicate, fault counting and logging, and
    // returns the replacement StaticInstPtr or nullptr for an honest skip).
    StaticInstPtr injectSignExtBit(uint64_t emi_raw, uint32_t enc,
                                   StaticInstPtr orig,
                                   const std::string &orig_name,
                                   ArmISA::Decoder *arm_dec, Addr pc);
    StaticInstPtr injectImmSubfieldShift(uint64_t emi_raw, uint32_t enc,
                                         StaticInstPtr orig,
                                         const std::string &orig_name,
                                         ArmISA::Decoder *arm_dec, Addr pc);
    StaticInstPtr injectCrackCtrl(uint64_t emi_raw, uint32_t enc,
                                  StaticInstPtr orig,
                                  const std::string &orig_name,
                                  ArmISA::Decoder *arm_dec, Addr pc);

    // ---- W7 batch 1 (D56-D61) injection helpers ----
    // D61 fp_route_bit: flip exactly one bit of the top-level A64
    // instruction-class field enc[28:24] such that the re-decode yields a
    // REAL (non-"unknown") instruction whose opClass DIFFERS from the
    // original — the honest gem5 approximation of the int-vs-FP/SIMD
    // dispatch-queue routing bit (gem5 has no separate route latch; the
    // opClass is what selects the FUPool capability, inst_queue.cc:184-192
    // — the observable effect is the FU/latency change). Uniform over the
    // effective single bits (W6 effective()-scan discipline); no effective
    // bit = honest skip log. The int->FP mis-judgment direction is NOT
    // reachable: the fpOnly gate restricts D61 to FP-classified
    // instructions (documented honesty limitation).
    StaticInstPtr injectFpRouteBit(uint64_t emi_raw, uint32_t enc,
                                   StaticInstPtr orig,
                                   const std::string &orig_name,
                                   ArmISA::Decoder *arm_dec, Addr pc);

    // Reg-operand fingerprint (classValue<<16 | index per operand, dests
    // then srcs) for the semantic verification of reg/imm flips:
    //   reg mode: mnemonic unchanged AND fingerprint differs
    //             (a register NUMBER actually moved — not an opcode flip)
    //   imm mode: mnemonic unchanged AND fingerprint identical
    //             (a value-only change — some immediate/constant moved)
    static void captureRegs(const StaticInst *si, std::vector<uint32_t> &out);
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_DECODE_HH__
