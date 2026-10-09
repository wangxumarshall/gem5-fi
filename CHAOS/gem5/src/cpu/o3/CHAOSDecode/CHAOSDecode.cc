#include "cpu/o3/CHAOSDecode/CHAOSDecode.hh"

#include <cstring>

#include "arch/arm/decoder.hh"
#include "arch/arm/types.hh"
#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst
#include "cpu/op_class.hh"        // FloatAddOp/... + enums::OpClassStrings
#include "cpu/static_inst.hh"     // StaticInst operand/name accessors
#include "debug/CHAOSDecode.hh"
#include "params/CHAOSDecode.hh"

namespace gem5
{

    // ---- D03 opcode 换值: format-compatible legal-opcode swap table ----
    // Every (mask, match, xor_bits) was verified against real GNU-as
    // encodings on this aarch64 host (2026-09-24 W6 plan record):
    //   add x0,x1,x2  = 0x8b020020  <-> sub  = 0xcb020020  (xor bit 30)
    //   add x0,x1,#1  = 0x91000420  <-> sub  = 0xd1000420  (xor bit 30)
    //   add x1,w2,sxtw= 0x8b22c020 <-> sub  = 0xcb22c020   (xor bit 30)
    //   and x0,x1,x2  = 0x8a020020  <-> orr  = 0xaa020020  (xor bit 29)
    //   bic           = 0x8a220020  <-> orn  = 0xaa220020  (xor bit 29)
    //   eor           = 0xca020020  <-> ands = 0xea020020  (xor bit 29)
    //   eon           = 0xca220020  <-> bics = 0xea220020  (xor bit 29)
    //   and x0,x1,#0xf= 0x92400c20  <-> orr imm = 0xb2400c20(xor bit 29)
    //   movz x0,#1    = 0xd2800020  <-> movn = 0x92800020  (xor bit 30)
    //   ldr x0,[x1,#8]= 0xf9400420  <-> str  = 0xf9000420  (xor bit 22)
    // Group masks pin exactly the A64 opcode-group bits so the xor always
    // lands on a LEGAL, operand-format-compatible opcode (the whole point
    // of D03: bypass the "illegal encoding -> crash" defense).
    // add_sub_imm:  bits[28:23]==100010 (ADD/SUB/ADDS/SUBS imm, op free)
    // add_sub_reg:  bits[28:24]==01011  (ADD/SUB shifted+extended reg)
    // logical_reg:  bits[28:24]==01010  (AND/ORR, BIC/ORN, EOR/ANDS,
    //                                    EON/BICS — all 4 pairs legal)
    // and/orr imm:  bits[30:23] pin opc 00/01 in group 100100 (opc 10 is
    //                                    unallocated; ANDS(11) excluded)
    // movn/movz:    bits[30:23] pin opc 00/10 in group 100101 (MOVK opc 11
    //                                    excluded — its bit-30 image 01 is
    //                                    unallocated)
    // str/ldr:      bits[28:22] pin opc 00/01 in group 11100x01 unsigned
    //                                    imm (LDRSW opc 10 excluded — its
    //                                    bit-22 image 11 is PRFM, a
    //                                    different operand semantic)
    const CHAOSDecode::SwapRule CHAOSDecode::kSwapRules[] = {
        {0x1FC00000u, 0x11000000u, 0x40000000u, "add_sub_imm"},
        {0x1F000000u, 0x0B000000u, 0x40000000u, "add_sub_reg"},
        {0x1F000000u, 0x0A000000u, 0x20000000u, "logical_reg"},
        {0x7FC00000u, 0x12000000u, 0x20000000u, "and_imm"},
        {0x7FC00000u, 0x32000000u, 0x20000000u, "orr_imm"},
        {0x7FC00000u, 0x12800000u, 0x40000000u, "movn_movz"},
        {0x7FC00000u, 0x52800000u, 0x40000000u, "movz_movn"},
        {0x1FC00000u, 0x19000000u, 0x00400000u, "str_ldr"},
        {0x1FC00000u, 0x19400000u, 0x00400000u, "ldr_str"},
    };

    const CHAOSDecode::SwapRule *
    CHAOSDecode::matchSwapRule(uint32_t enc)
    {
        for (const SwapRule &r : kSwapRules)
            if ((enc & r.mask) == r.match)
                return &r;
        return nullptr;
    }

    // ---- W7 batch 1 (D56-D61, ooo 04-design-matrix R57-R62 FP/SIMD
    // Decode) ----
    //
    // fpOnly eligibility: the DOCUMENTED W7 scope — all scalar Float* plus
    // all SIMD SimdFloat* opClasses (identical set to CHAOSFPU.cc:88-98
    // isFpOpClass). Integer SIMD (SimdAdd/SimdMult/... over V registers) is
    // deliberately OUT of scope (Int Decode unit D04/D05 owns its opClass
    // routing); this is an honesty limitation, not a silent gap.
    bool
    CHAOSDecode::isFpOpClass(OpClass oc)
    {
        return oc == FloatAddOp || oc == FloatCmpOp || oc == FloatCvtOp ||
               oc == FloatMultOp || oc == FloatMultAccOp || oc == FloatDivOp ||
               oc == FloatMiscOp || oc == FloatSqrtOp ||
               oc == SimdFloatAddOp || oc == SimdFloatAluOp ||
               oc == SimdFloatCmpOp || oc == SimdFloatCvtOp ||
               oc == SimdFloatMultOp || oc == SimdFloatMultAccOp ||
               oc == SimdFloatDivOp || oc == SimdFloatSqrtOp ||
               oc == SimdFloatMiscOp;
    }

    // D58 FP opcode 换值 table — closed-loop verified (see .hh block
    // comment for the per-row derivations and the negative-corpus record).
    // Masks pin the scalar top byte (0x1E/0x1F) or the SIMD 3-same/2-reg
    // group bits plus the family's shared opcode bits and the
    // family-excluding discriminants (FABD/FCMGT/FMULX/FRINT neighbors),
    // so the xor always lands on the partner operand-format-compatible
    // opcode. First match wins.
    const CHAOSDecode::SwapRule CHAOSDecode::kFpSwapRules[] = {
        // scalar single-data-pass (op[15:10], bit12 = add/sub|mul/div|
        // max/min|maxnm/minnm discriminant; ftype[23:22] free)
        {0xFF20EC00u, 0x1E202800u, 0x00001000u, "s_fadd_fsub"},
        {0xFF20EC00u, 0x1E200800u, 0x00001000u, "s_fmul_fdiv"},
        {0xFF20EC00u, 0x1E204800u, 0x00001000u, "s_fmax_fmin"},
        {0xFF20EC00u, 0x1E206800u, 0x00001000u, "s_fmaxnm_fminnm"},
        // scalar fused (bit21=O1 pinned selects the neg-accumulate pair,
        // bit15=O2 is the xor; Ra[14:10]/Rm/Rn/Rd/ftype all free)
        {0xFF200000u, 0x1F000000u, 0x00008000u, "s_fmadd_fmsub"},
        {0xFF200000u, 0x1F200000u, 0x00008000u, "s_fnmadd_fnmsub"},
        // scalar compare (op=001000 pinned; bit4 = E flag; the #0.0 forms
        // share the rule — opcode2[3:0]/Rm free)
        {0xFF20FC00u, 0x1E202000u, 0x00000010u, "s_fcmp_fcmpe"},
        // SIMD 3-same (bit31=0, bits[28:24]=01110, bit21=1, bit29 pinned
        // per family; bit23 = the add/sub-class xor; Q[30]/size[22] free)
        {0xBF20FC00u, 0x0E20D400u, 0x00800000u, "v_fadd_fsub"},
        {0xBF20FC00u, 0x0E20F400u, 0x00800000u, "v_fmax_fmin"},
        {0xBF20FC00u, 0x0E20C400u, 0x00800000u, "v_fmaxnm_fminnm"},
        {0xBF20FC00u, 0x0E20CC00u, 0x00800000u, "v_fmla_fmls"},
        // fcmeq<->fcmge: bit29 xor, bit23 pinned 0 (excludes FCMGT)
        {0x9FA0FC00u, 0x0E20E400u, 0x20000000u, "v_fcmeq_fcmge"},
        // fmul<->fdiv: op common bits 11?111 pinned, bit13 xor, bit29=1
        // pinned (excludes FMULX), bit23=0 pinned
        {0xBFA0DC00u, 0x2E20DC00u, 0x00002000u, "v_fmul_fdiv"},
        // SIMD 2-reg-misc fabs<->fneg: op=111110, bits[23:22]=10, Rm=00000
        // pinned (excludes FRINT/FSQRT), bit29 = U xor
        {0x9FFFFC00u, 0x0EA0F800u, 0x20000000u, "v_fabs_fneg"},
    };

    const CHAOSDecode::SwapRule *
    CHAOSDecode::matchFpSwapRule(uint32_t enc)
    {
        for (const SwapRule &r : kFpSwapRules)
            if ((enc & r.mask) == r.match)
                return &r;
        return nullptr;
    }

    // ---- W6 batch 2 tables (D08/D09/D10, ooo 04-design-matrix R9-R11) ----
    // Every row below was verified against real GNU-as encodings on this
    // aarch64 host (2026-09-24 W6 batch 2 record, /tmp/w6b2/fmt.s + objdump
    // output quoted in CHAOSDecode.hh). See the .hh block comments for the
    // per-row derivation and the field maps.

    // D08 sign_ext_bit: (mask, match) pins the format; sign_bit is the
    // immediate's top ENCODED bit to flip (exactly this bit, never random);
    // [fhi:flo] documents the immediate field for the log line.
    const CHAOSDecode::SignImmFormat CHAOSDecode::kSignImmFormats[] = {
        // add/sub imm12: add x0,x1,#1=0x91000420 adds..lsl#12=0xb1400420
        {0x1FC00000u, 0x11000000u, 21, 21, 10, "add_sub_imm12"},
        // logical imm (N immr imms): and=0x92400c20 orr=0xb2400c20
        // eor=0xd2400c20 ands=0xf2400c20 -> imms[20:16] top = bit 20
        {0x7FC00000u, 0x12000000u, 20, 20, 16, "and_imm"},
        {0x7FC00000u, 0x32000000u, 20, 20, 16, "orr_imm"},
        {0x7FC00000u, 0x52000000u, 20, 20, 16, "eor_imm"},
        {0x7FC00000u, 0x72000000u, 20, 20, 16, "ands_imm"},
        // ldr/str unsigned imm12: ldr x0,[x1,#8]=0xf9400420 str=0xf9000420
        {0x1FC00000u, 0x19000000u, 21, 21, 10, "str_imm12"},
        {0x1FC00000u, 0x19400000u, 21, 21, 10, "ldr_imm12"},
        // ldur/stur imm9 (TRUE sign extension): ldur x0,[x1,#-8]=0xf85f8020
        // stur=0xf81f8020 -> imm9[20:12], sign bit = bit 20
        {0x3FE00C00u, 0x38000000u, 20, 20, 12, "stur_imm9"},
        {0x3FE00C00u, 0x38400000u, 20, 20, 12, "ldur_imm9"},
        // b.cond imm19: b.eq=0x540001c0 (cond bits[15:12] free)
        {0xFF000010u, 0x54000000u, 23, 23, 5, "bcond_imm19"},
        // cbz/cbnz imm19: cbz=0xb40001a0 cbnz=0xb5000180
        {0x7F000000u, 0x34000000u, 23, 23, 5, "cbz_imm19"},
        {0x7F000000u, 0x35000000u, 23, 23, 5, "cbnz_imm19"},
        // tbz/tbnz imm14: tbz=0x36180160 tbnz=0x37180140
        {0x7F000000u, 0x36000000u, 18, 18, 5, "tbz_imm14"},
        {0x7F000000u, 0x37000000u, 18, 18, 5, "tbnz_imm14"},
        // b/bl imm26: b=0x14000009 bl=0x94000008
        {0x7C000000u, 0x14000000u, 25, 25, 0, "b_imm26"},
        {0x7C000000u, 0x94000000u, 25, 25, 0, "bl_imm26"},
        // adr/adrp (immhi[23:5] + immlo[30:29]): adr x0,.+28=0x100000e0
        // adrp=0x90000000 -> 21-bit immediate's MSB = immhi top = bit 23
        {0x9F000000u, 0x10000000u, 23, 23, 5, "adr_imm21"},
        {0x9F000000u, 0x90000000u, 23, 23, 5, "adrp_imm21"},
        // ldr literal imm19: ldr x0,lit=0x580000a0
        {0xFF000000u, 0x58000000u, 23, 23, 5, "ldr_lit_imm19"},
        // movz/movn/movk imm16: movz=0xd2824680 movn=0x92824680
        // movk lsl#16=0xf2a24680 movz w=0x52800020 (sf free)
        {0x7F800000u, 0x52800000u, 20, 20, 5, "movz_imm16"},
        {0x7F800000u, 0x92800000u, 20, 20, 5, "movn_imm16"},
        {0x7F800000u, 0xF2800000u, 20, 20, 5, "movk_imm16"},
    };

    // D09 imm_subfield_shift: (mask, match) pins the format; the equal-width
    // subfields [hi_a:lo_a] and [hi_b:lo_b] are TRANSPOSED in the encoding
    // (each fragment re-assembled at the other's bit position).
    const CHAOSDecode::SubfieldFormat CHAOSDecode::kSubfieldFormats[] = {
        // and x0,x1,#0xf = 0x92400c20 (N=1 imms=0 immr=3): imms <-> immr
        {0x7FC00000u, 0x12000000u, 20, 16, 15, 10, "logical_imm"},
        {0x7FC00000u, 0x32000000u, 20, 16, 15, 10, "logical_imm"},
        {0x7FC00000u, 0x52000000u, 20, 16, 15, 10, "logical_imm"},
        {0x7FC00000u, 0x72000000u, 20, 16, 15, 10, "logical_imm"},
        // adr x0,.+28 = 0x100000e0 (immhi=7 immlo=0): immhi[1:0](enc 6:5)
        // <-> immlo(enc 30:29); adrp = 0x90000000
        {0x9F000000u, 0x10000000u, 30, 29, 6, 5, "adr_immlo_immhi"},
        {0x9F000000u, 0x90000000u, 30, 29, 6, 5, "adrp_immlo_immhi"},
        // movz/movn/movk (hw[22:21] <-> imm16[15:14] at enc 20:19):
        // movk x0,#0x1234,lsl#16 = 0xf2a24680 (hw=1 imm16=0x1234)
        {0x7F800000u, 0x52800000u, 22, 21, 20, 19, "mov_wide"},
        {0x7F800000u, 0x92800000u, 22, 21, 20, 19, "mov_wide"},
        {0x7F800000u, 0xF2800000u, 22, 21, 20, 19, "mov_wide"},
        // add/sub imm12+sh (sh[23:22] <-> imm12[11:10] at enc 21:20):
        // adds x0,x1,#1,lsl#12 = 0xb1400420 (sh=1 imm12=1)
        {0x1FC00000u, 0x11000000u, 23, 22, 21, 20, "add_sub_sh_imm12"},
    };

    // D10 crack_ctrl: bounded microop counter. Walks fetchMicroop(k) until
    // IsLastMicroop (ARM macroop ctors flag the final uop, e.g. PairMemOp
    // macromem.cc:362-363); the 16-step bound guarantees the
    // fetchMicroop(microPC < numMicroops) assert can never be reached even
    // for a pathological unflagged macroop (honest floor of 16).
    uint32_t
    CHAOSDecode::countMicroops(const StaticInst *mop)
    {
        for (uint32_t k = 0; k < 16; k++) {
            StaticInstPtr u = mop->fetchMicroop(k);
            if (!u || u->isLastMicroop())
                return k + 1;
        }
        return 16;
    }

    CHAOSDecode::Mode
    CHAOSDecode::stringToMode(const std::string &s)
    {
        if (s == "dest_reg_sub")   return Mode::DestRegSub;
        if (s == "opcode_bitflip")  return Mode::OpcodeBitflip;
        if (s == "opcode_bitflip2") return Mode::OpcodeBitflip2;
        if (s == "opcode_swap")     return Mode::OpcodeSwap;
        if (s == "reg_bitflip")     return Mode::RegBitflip;
        if (s == "reg_bitflip2")    return Mode::RegBitflip2;
        if (s == "imm_bitflip")     return Mode::ImmBitflip;
        if (s == "imm_bitflip2")    return Mode::ImmBitflip2;
        if (s == "sign_ext_bit")    return Mode::SignExtBit;
        if (s == "imm_subfield_shift") return Mode::ImmSubfieldShift;
        if (s == "crack_ctrl")      return Mode::CrackCtrl;
        if (s == "fp_opcode_bitflip")  return Mode::FpOpcodeBitflip;
        if (s == "fp_opcode_bitflip2") return Mode::FpOpcodeBitflip2;
        if (s == "fp_opcode_swap")     return Mode::FpOpcodeSwap;
        if (s == "fp_reg_bitflip")     return Mode::FpRegBitflip;
        if (s == "fp_reg_bitflip2")    return Mode::FpRegBitflip2;
        if (s == "fp_route_bit")       return Mode::FpRouteBit;
        panic("CHAOSDecode: unknown mode '%s'\n", s);
    }

    const char *
    CHAOSDecode::modeToString(Mode m) const
    {
        switch (m) {
          case Mode::DestRegSub:    return "dest_reg_sub";
          case Mode::OpcodeBitflip: return "opcode_bitflip";
          case Mode::OpcodeBitflip2:return "opcode_bitflip2";
          case Mode::OpcodeSwap:    return "opcode_swap";
          case Mode::RegBitflip:    return "reg_bitflip";
          case Mode::RegBitflip2:   return "reg_bitflip2";
          case Mode::ImmBitflip:    return "imm_bitflip";
          case Mode::ImmBitflip2:   return "imm_bitflip2";
          case Mode::SignExtBit:    return "sign_ext_bit";
          case Mode::ImmSubfieldShift: return "imm_subfield_shift";
          case Mode::CrackCtrl:     return "crack_ctrl";
          case Mode::FpOpcodeBitflip:  return "fp_opcode_bitflip";
          case Mode::FpOpcodeBitflip2: return "fp_opcode_bitflip2";
          case Mode::FpOpcodeSwap:     return "fp_opcode_swap";
          case Mode::FpRegBitflip:     return "fp_reg_bitflip";
          case Mode::FpRegBitflip2:    return "fp_reg_bitflip2";
          case Mode::FpRouteBit:       return "fp_route_bit";
        }
        return "?";
    }

    void
    CHAOSDecode::captureRegs(const StaticInst *si, std::vector<uint32_t> &out)
    {
        out.clear();
        out.reserve(si->numDestRegs() + si->numSrcRegs());
        for (int i = 0; i < int(si->numDestRegs()); i++) {
            const RegId &r = si->destRegIdx(i);
            out.push_back((uint32_t(r.classValue()) << 16) | r.index());
        }
        for (int i = 0; i < int(si->numSrcRegs()); i++) {
            const RegId &r = si->srcRegIdx(i);
            out.push_back((uint32_t(r.classValue()) << 16) | r.index());
        }
    }

    CHAOSDecode::CHAOSDecode(const CHAOSDecodeParams &p)
        : SimObject(p),
          cpu(p.cpu),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          fi_mode(stringToMode(p.mode))
    {
        if (probability > 0.0f) {
            log_stream = simout.create("decode_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSDecode: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        // Sampling-bias fix (findings.md Phase 2.2/3.0): skip a
        // geometric(p=0.1) number of eligible events before the first
        // injection so maxFaults=1 lands on a seed-dependent event.
        std::geometric_distribution<uint64_t> skip_dist(0.1);
        events_to_skip = skip_dist(rng);
        }
    }

    CHAOSDecode::~CHAOSDecode() {}

    bool
    CHAOSDecode::inWindow() {
        // Frequency-correct: use the CPU's actual clock period for the
        // cycles->ticks conversion (C0 2GHz=500t/cyc, C2-KP 2.6GHz~385t/cyc).
        // The old *1000 assumed 1GHz and never opened the window on C2.
        if (!cpu) return false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;
        Tick now = curTick();
        Tick period = o3cpu->clockPeriod();
        Tick f = first_clock * period;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * period) return false;
        return true;
    }

    bool
    CHAOSDecode::maybeCorrupt(int dest_idx, RegId &flat_dest_regid,
                              const o3::DynInst *inst)
    {
        // Mode guard (W6 batch 2 bug fix, found by the crack_ctrl seed
        // scan): the rename-site §2.14 injection belongs to DestRegSub
        // ONLY. Without this guard every W6 encoding mode (D01-D10) raced
        // the legacy rename hook for the shared max_faults budget, so a
        // decode-mode run could mis-inject dest_reg_sub and the outcome
        // would be mis-attributed to the selected decode fault model.
        if (fi_mode != Mode::DestRegSub) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        // only integer class dest regs (aarch64 X0-X30 = index 0-30)
        if (flat_dest_regid.classValue() != IntRegClass) return false;

        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible events (N ~ geometric(0.1) from the seed) so the
        // single fault lands on a seed-dependent event.
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }


        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // §2.14 dest_reg_sub F5: replace the dest arch reg index with another
        // legal 0-30 integer reg (per-inst, safe — _flatDestIdx is per-DynInst,
        // not the shared staticInst). The commit path will write the result
        // to the WRONG arch reg (commit.cc:1264 reads flattenedDestIdx).
        RegIndex old_idx = flat_dest_regid.index();
        RegIndex new_idx;
        do { new_idx = rng() % 31; } while (new_idx == old_idx);  // 0..30, != old
        flat_dest_regid.setIndex(new_idx);  // mutate the by-ref reg id

        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: rename_flattenDest, mode=dest_reg_sub"
                << ", dest_idx=" << dest_idx
                << ", sn=" << inst->seqNum
                << ", old_dest_reg=" << old_idx
                << ", new_dest_reg=" << new_idx
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    // ---- W6 D01-D07: decode-output encoding corruption (fetch.cc hook) ----

    StaticInstPtr
    CHAOSDecode::maybeCorruptEncoding(StaticInstPtr orig, InstDecoder *dec,
                                      Addr pc)
    {
        // Idle path: detached / disabled / legacy §2.14 mode (its hook is
        // in rename.cc, not here) — zero work, zero regression.
        if (!cpu || probability <= 0.0f) return nullptr;
        if (fi_mode == Mode::DestRegSub) return nullptr;
        if (!orig) return nullptr;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return nullptr;
        if (!inWindow()) return nullptr;

        // Pull the full 8-byte ExtMachInst back out of the decoded
        // StaticInst (ArmStaticInst::asBytes -> simpleAsBytes(machInst);
        // htole is identity on this little-endian aarch64 host). Bits
        // [31:0] are the real encoding (instBits), [63:32] the decoder
        // metadata the original decode ran with (sveLen/fpscr/itstate...),
        // which the re-decode must see unchanged.
        uint8_t buf[8];
        const size_t n = orig->asBytes(buf, sizeof(buf));
        if (n != sizeof(ArmISA::ExtMachInst) || n != 8) return nullptr;
        uint64_t raw = 0;
        std::memcpy(&raw, buf, 8);
        ArmISA::ExtMachInst emi;
        emi = raw;

        // Plan risk list: Thumb excluded (candidate bit maps are A64
        // positions; Thumb is 2/4-byte mixed), non-AArch64 excluded, and
        // macroop decodes excluded (their microop stream comes through
        // fetchMicroop, not this hook). isMicroop() is belt-and-braces:
        // dec_ptr->decode() only ever returns top-level instructions.
        // D10 crack_ctrl is the ONE exception: its eligible population IS
        // the macroop decodes (gem5-cracked LDP/STP — see .hh spike note),
        // so for that mode the macroop exclusion is inverted.
        if (emi.thumb || !emi.aarch64) return nullptr;
        if (orig->isMicroop()) return nullptr;
        if (orig->isMacroop() && fi_mode != Mode::CrackCtrl) return nullptr;

        auto *arm_dec = dynamic_cast<ArmISA::Decoder *>(dec);
        if (!arm_dec) return nullptr;

        const uint32_t enc = emi.instBits;
        // W7: fp_reg_bitflip/fp_reg_bitflip2 ride the W6 reg machinery
        // (kRegBits already covers Vd/Vn/Vm = enc[4:0]/[9:5]/[20:16] for the
        // FP/SIMD formats) — ZERO selection-side changes, only the fpOnly
        // gate upstream differs.
        const bool is_reg_mode = (fi_mode == Mode::RegBitflip ||
                                  fi_mode == Mode::RegBitflip2 ||
                                  fi_mode == Mode::FpRegBitflip ||
                                  fi_mode == Mode::FpRegBitflip2);
        const bool is_imm_mode = (fi_mode == Mode::ImmBitflip ||
                                  fi_mode == Mode::ImmBitflip2);
        // W7 batch 1 (D56-D61): all six FP modes gate on fpOnly (see
        // isFpOpClass for the documented scope).
        const bool is_fp_mode = (fi_mode == Mode::FpOpcodeBitflip ||
                                 fi_mode == Mode::FpOpcodeBitflip2 ||
                                 fi_mode == Mode::FpOpcodeSwap ||
                                 fi_mode == Mode::FpRegBitflip ||
                                 fi_mode == Mode::FpRegBitflip2 ||
                                 fi_mode == Mode::FpRouteBit);

        // ---- cheap per-mode eligibility (before skip/probability) ----
        const SwapRule *rule = nullptr;
        if (is_fp_mode && !isFpOpClass(orig->opClass())) {
            // fpOnly gate: the W7.1 eligible population is FP-classified
            // instructions only (scalar Float* / SIMD SimdFloat*).
            return nullptr;
        }
        if (fi_mode == Mode::OpcodeSwap) {
            rule = matchSwapRule(enc);
            if (!rule) return nullptr;     // not a swappable opcode
        } else if (fi_mode == Mode::FpOpcodeSwap) {
            // D58: the operand-format-compatible FP pair table (the W6
            // kSwapRules are all-integer — FP encodings match none).
            rule = matchFpSwapRule(enc);
            if (!rule) return nullptr;     // not a swappable FP opcode
        } else if (is_reg_mode || is_imm_mode) {
            // Necessary condition for a reg flip: the instruction actually
            // has register operands. (The full semantic check below is the
            // real filter; this only keeps the common no-operand cases
            // from paying the scan.)
            if (orig->numSrcRegs() == 0 && orig->numDestRegs() == 0)
                return nullptr;
        }

        // ---- sampling: geometric skip, then probability draw ----
        if (events_to_skip > 0) { --events_to_skip; return nullptr; }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return nullptr;

        // ---- W6 batch 2 (D08-D10) dispatch ----
        // Structured immediate / crack models. These run their own format
        // eligibility AFTER the gates — a deliberate deviation from the
        // D01-D07 cheap-eligibility ordering, because the plan REQUIRES an
        // honest skip log for ineligible formats ("无子字段格式诚实跳过
        // +日志"), which is only reachable past the gates. The skip log
        // volume stays bounded by the probability draw.
        if (fi_mode == Mode::SignExtBit)
            return injectSignExtBit(emi, enc, orig, orig->getName(),
                                    arm_dec, pc);
        if (fi_mode == Mode::ImmSubfieldShift)
            return injectImmSubfieldShift(emi, enc, orig, orig->getName(),
                                          arm_dec, pc);
        if (fi_mode == Mode::CrackCtrl)
            return injectCrackCtrl(emi, enc, orig, orig->getName(),
                                   arm_dec, pc);
        // ---- W7 batch 1 (D56-D61): D61 runs its own effective-bit scan
        // past the gates (an honest skip log requires reaching here; no
        // effective route bit = wasted draw, same D08-D10 discipline).
        if (fi_mode == Mode::FpRouteBit)
            return injectFpRouteBit(emi, enc, orig, orig->getName(),
                                    arm_dec, pc);

        // ---- bit selection ----
        // Semantic predicate for reg/imm flips (see .hh): the candidate
        // re-decode must keep the mnemonic, and
        //   reg mode: the register-operand fingerprint must MOVE
        //             (a register NUMBER changed — not an opcode bit)
        //   imm mode: the fingerprint must be UNCHANGED
        //             (a value-only change: immediate/constant bits)
        const std::string orig_name = orig->getName();
        std::vector<uint32_t> fp0;
        if (is_reg_mode || is_imm_mode)
            captureRegs(orig.get(), fp0);
        auto effective = [&](uint32_t xor_mask) -> bool {
            ArmISA::ExtMachInst t = emi;
            t.instBits = enc ^ xor_mask;
            StaticInstPtr c = arm_dec->decodeChaos(t);
            if (!c) return false;
            if (c->getName() != orig_name) return false;
            std::vector<uint32_t> fpc;
            captureRegs(c.get(), fpc);
            return is_reg_mode ? (fpc != fp0) : (fpc == fp0);
        };

        uint32_t bit_a = 32, bit_b = 32;    // 32 = unset
        if (fi_mode == Mode::OpcodeBitflip ||
            fi_mode == Mode::OpcodeBitflip2) {
            // No verification by design: flipping an opcode-region bit may
            // land on another LEGAL opcode (possible SDC) or on an illegal
            // encoding (Unknown/DecoderFault -> SIGILL Crash). Both
            // outcomes are the fault model (D01/D02 baseline: "random
            // opcode flips almost never produce SDC").
            constexpr size_t nb = sizeof(kOpcodeBits) / sizeof(kOpcodeBits[0]);
            bit_a = kOpcodeBits[rng() % nb];
            if (fi_mode == Mode::OpcodeBitflip2) {
                do { bit_b = kOpcodeBits[rng() % nb]; } while (bit_b == bit_a);
            }
        } else if (fi_mode == Mode::FpOpcodeBitflip ||
                   fi_mode == Mode::FpOpcodeBitflip2) {
            // D56/D57: same no-verification-by-design as D01/D02, but the
            // candidate bits are the FP/SIMD opcode region enc[23:10]
            // (spike-verified window; see .hh). The fpOnly gate upstream
            // already restricted the population to FP-class instructions.
            constexpr size_t nb =
                sizeof(kFpOpcodeBits) / sizeof(kFpOpcodeBits[0]);
            bit_a = kFpOpcodeBits[rng() % nb];
            if (fi_mode == Mode::FpOpcodeBitflip2) {
                do { bit_b = kFpOpcodeBits[rng() % nb]; } while (bit_b == bit_a);
            }
        } else if (fi_mode == Mode::OpcodeSwap) {
            // Single verified opcode bit by construction (see kSwapRules).
            bit_a = __builtin_ctz(rule->xor_bits);
        } else if (fi_mode == Mode::FpOpcodeSwap) {
            // D58: single verified opcode bit by construction — every
            // kFpSwapRules xor_bits is a verified single-bit power of two
            // (closed-loop host check, .hh record).
            bit_a = __builtin_ctz(rule->xor_bits);
        } else if (is_reg_mode || is_imm_mode) {
            const uint32_t *cand;
            size_t ncand;
            if (is_reg_mode) {
                cand = kRegBits;
                ncand = sizeof(kRegBits) / sizeof(kRegBits[0]);
            } else {
                cand = kImmBits;
                ncand = sizeof(kImmBits) / sizeof(kImmBits[0]);
            }
            const bool two_bits = (fi_mode == Mode::RegBitflip2 ||
                                   fi_mode == Mode::ImmBitflip2 ||
                                   fi_mode == Mode::FpRegBitflip2);
            if (!two_bits) {
                // Single-bit: scan the positional candidates once, keep
                // the EFFECTIVE ones (semantic predicate above), pick
                // uniformly among them — exactly uniform over effective
                // bits, deterministic under the seed.
                std::vector<uint32_t> eff;
                for (size_t i = 0; i < ncand; i++)
                    if (effective(1u << cand[i]))
                        eff.push_back(cand[i]);
                if (eff.empty())
                    return nullptr;   // honest wasted draw, no fault count
                bit_a = eff[rng() % eff.size()];
            } else {
                // Double-bit: rejection sampling over distinct positional
                // pairs (uniform over accepted pairs; bounded at 16 tries
                // so a pathological format gives an honest wasted draw
                // instead of a scan storm).
                for (int tries = 0; tries < 16 && bit_b == 32; tries++) {
                    uint32_t b1 = cand[rng() % ncand];
                    uint32_t b2;
                    do { b2 = cand[rng() % ncand]; } while (b2 == b1);
                    if (effective((1u << b1) | (1u << b2))) {
                        bit_a = b1;
                        bit_b = b2;
                    }
                }
                if (bit_b == 32)
                    return nullptr;   // honest wasted draw, no fault count
            }
        }

        // ---- apply the flip, re-decode, replace ----
        const uint32_t flip_mask =
            (1u << bit_a) | (bit_b != 32 ? (1u << bit_b) : 0u);
        ArmISA::ExtMachInst new_emi = emi;
        new_emi.instBits = enc ^ flip_mask;
        StaticInstPtr repl = arm_dec->decodeChaos(new_emi);
        if (!repl) return nullptr;

        faults_injected_count++;
        if (write_log) {
            // Encoding diff is recomputable: orig_enc ^ (1<<b1 [^ 1<<b2])
            // == new_enc. regs_moved carries the semantic verification
            // verdict for reg/imm modes (reg: 1 = a register number
            // moved; imm: 0 = value-only change).
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: fetch_decode, mode=" << modeToString(fi_mode)
                << ", pc=0x" << std::hex << pc << std::dec
                << ", orig_enc=0x" << std::hex << enc << std::dec
                << ", new_enc=0x" << std::hex << new_emi.instBits << std::dec
                << ", bits=[" << bit_a
                << (bit_b != 32 ? "," : "")
                << (bit_b != 32 ? std::to_string(bit_b) : "") << "]"
                << ", orig_mnemonic=" << orig_name
                << ", new_mnemonic=" << repl->getName();
            if (fi_mode == Mode::OpcodeSwap ||
                fi_mode == Mode::FpOpcodeSwap)
                *(log_stream->stream()) << ", swap_rule=" << rule->name;
            if (is_reg_mode || is_imm_mode)
                *(log_stream->stream())
                    << ", regs_moved=" << (is_reg_mode ? 1 : 0);
            *(log_stream->stream())
                << ", macroop_new=" << (repl->isMacroop() ? 1 : 0)
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return repl;
    }

    // ---- W6 batch 2 (D08-D10) injection helpers ----
    // Shared skip-log prefix: "site fetch_decode + honest-skip" lines are
    // bounded by the probability draw and carry the reason + mnemonic so a
    // reviewer can see WHY a draw was not injectable.

    // D08 sign_ext_bit: flip EXACTLY the format-located sign/top bit of the
    // immediate's encoding, then re-decode (the decoder's own sext logic
    // consumes the flipped bit — no value-level patch needed).
    StaticInstPtr
    CHAOSDecode::injectSignExtBit(uint64_t emi_raw, uint32_t enc,
                                  StaticInstPtr orig,
                                  const std::string &orig_name,
                                  ArmISA::Decoder *arm_dec, Addr pc)
    {
        ArmISA::ExtMachInst emi;
        emi = emi_raw;   // rebuild the full EMI (high 32 bits = decode ctx)
        const SignImmFormat *fmt = nullptr;
        for (const SignImmFormat &f : kSignImmFormats)
            if ((enc & f.mask) == f.match) { fmt = &f; break; }
        if (!fmt) {
            // honest skip: no immediate whose sign/top bit this model targets
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=sign_ext_bit"
                    << ", event=honest_skip"
                    << ", reason=no_locatable_immediate_format"
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }

        ArmISA::ExtMachInst new_emi = emi;
        new_emi.instBits = enc ^ (1u << fmt->sign_bit);
        StaticInstPtr repl = arm_dec->decodeChaos(new_emi);

        // Semantic predicate (value-only change, the imm_bitflip
        // discipline): same mnemonic AND same reg operands. Rejection
        // (e.g. a logical-imm pattern that re-decodes as Unknown) is an
        // honest skip, not a fault.
        bool ok = false;
        if (repl) {
            std::vector<uint32_t> fp0, fp1;
            captureRegs(orig.get(), fp0);
            captureRegs(repl.get(), fp1);
            ok = (repl->getName() == orig_name) && (fp1 == fp0);
        }
        if (!ok) {
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=sign_ext_bit"
                    << ", event=honest_skip"
                    << ", reason=predicate_fail_mnemonic_changed"
                    << ", format=" << fmt->name
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }

        faults_injected_count++;
        if (write_log)
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: fetch_decode, mode=sign_ext_bit"
                << ", pc=0x" << std::hex << pc << std::dec
                << ", format=" << fmt->name
                << ", imm_field=[" << int(fmt->fhi) << ":" << int(fmt->flo)
                << "]"
                << ", sign_bit=" << int(fmt->sign_bit)
                << ", orig_enc=0x" << std::hex << enc << std::dec
                << ", new_enc=0x" << std::hex << new_emi.instBits << std::dec
                << ", orig_mnemonic=" << orig_name
                << ", new_mnemonic=" << repl->getName()
                << ", regs_moved=0"
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        return repl;
    }

    // D09 imm_subfield_shift: transpose two equal-width named subfields of
    // the immediate's encoding (the fragments of the value assembled at the
    // wrong bit positions), then re-decode. Formats without a multi-named-
    // subfield immediate are honestly skipped WITH a log line.
    StaticInstPtr
    CHAOSDecode::injectImmSubfieldShift(uint64_t emi_raw, uint32_t enc,
                                        StaticInstPtr orig,
                                        const std::string &orig_name,
                                        ArmISA::Decoder *arm_dec, Addr pc)
    {
        ArmISA::ExtMachInst emi;
        emi = emi_raw;   // rebuild the full EMI (high 32 bits = decode ctx)
        const SubfieldFormat *fmt = nullptr;
        for (const SubfieldFormat &f : kSubfieldFormats)
            if ((enc & f.mask) == f.match) { fmt = &f; break; }
        if (!fmt) {
            // honest skip + log: name the KNOWN immediate format when there
            // is one (single contiguous field — nothing to transpose).
            const char *imm_name = "none";
            for (const SignImmFormat &f : kSignImmFormats)
                if ((enc & f.mask) == f.match) { imm_name = f.name; break; }
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=imm_subfield_shift"
                    << ", event=honest_skip"
                    << ", reason=no_multi_named_subfield_structure"
                    << ", imm_format=" << imm_name
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }

        // Transpose the two equal-width subfields A=[hi_a:lo_a],
        // B=[hi_b:lo_b]: each fragment lands at the other's position.
        const uint32_t width = fmt->hi_a - fmt->lo_a + 1;
        const uint32_t mask_a = ((1u << width) - 1) << fmt->lo_a;
        const uint32_t mask_b = ((1u << width) - 1) << fmt->lo_b;
        const uint32_t val_a = (enc & mask_a) >> fmt->lo_a;
        const uint32_t val_b = (enc & mask_b) >> fmt->lo_b;
        ArmISA::ExtMachInst new_emi = emi;
        new_emi.instBits = (enc & ~(mask_a | mask_b))
                         | (val_a << fmt->lo_b) | (val_b << fmt->lo_a);

        if (new_emi.instBits == enc) {
            // transposition is the identity (fields held equal values)
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=imm_subfield_shift"
                    << ", event=honest_skip"
                    << ", reason=subfield_transpose_is_identity"
                    << ", format=" << fmt->name
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }

        StaticInstPtr repl = arm_dec->decodeChaos(new_emi);
        // Semantic predicate (value-only change, the imm_bitflip
        // discipline): same mnemonic AND same reg operands.
        bool ok = false;
        if (repl) {
            std::vector<uint32_t> fp0, fp1;
            captureRegs(orig.get(), fp0);
            captureRegs(repl.get(), fp1);
            ok = (repl->getName() == orig_name) && (fp1 == fp0);
        }
        if (!ok) {
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=imm_subfield_shift"
                    << ", event=honest_skip"
                    << ", reason=predicate_fail_mnemonic_changed"
                    << ", format=" << fmt->name
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", new_enc=0x" << std::hex << new_emi.instBits
                    << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }

        faults_injected_count++;
        if (write_log)
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: fetch_decode, mode=imm_subfield_shift"
                << ", pc=0x" << std::hex << pc << std::dec
                << ", format=" << fmt->name
                << ", subfields=A[" << int(fmt->hi_a) << ":"
                << int(fmt->lo_a) << "]<->B[" << int(fmt->hi_b) << ":"
                << int(fmt->lo_b) << "]"
                << ", field_a=" << val_a << ", field_b=" << val_b
                << ", orig_enc=0x" << std::hex << enc << std::dec
                << ", new_enc=0x" << std::hex << new_emi.instBits << std::dec
                << ", orig_mnemonic=" << orig_name
                << ", new_mnemonic=" << repl->getName()
                << ", regs_moved=0"
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        return repl;
    }

    // D10 crack_ctrl (exploratory): on an instruction that gem5 DECODED AS
    // A MACROOP (cracked), flip the pair-op addressing-mode field
    // enc[24:23] within {post=01, offset=10, pre=11} (never into 00 =
    // noAlloc ldnp/stnp — that changes the mnemonic). The re-decoded pair
    // op carries a different µop stream (writeback µop lost / spurious
    // writeback µop / composition swap); µop counts are measured and
    // logged. Non-macroop instructions are honestly skipped (the
    // force-crack-of-a-plain-instruction arm is a recorded blocker — see
    // the .hh spike note).
    StaticInstPtr
    CHAOSDecode::injectCrackCtrl(uint64_t emi_raw, uint32_t enc,
                                 StaticInstPtr orig,
                                 const std::string &orig_name,
                                 ArmISA::Decoder *arm_dec, Addr pc)
    {
        ArmISA::ExtMachInst emi;
        emi = emi_raw;   // rebuild the full EMI (high 32 bits = decode ctx)
        if (!orig->isMacroop()) {
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=crack_ctrl"
                    << ", event=honest_skip"
                    << ", reason=not_a_macroop_decode"
                    << " (force-crack of a plain instruction has no"
                    << " encoding-level control - recorded blocker)"
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }

        const uint32_t type = (enc >> 23) & 3;
        static const char *kTypeNames[4] =
            {"noalloc", "post", "offset", "pre"};
        if (type == 0) {
            // ldnp/stnp: every flip lands on a different mnemonic — skip.
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=crack_ctrl"
                    << ", event=honest_skip"
                    << ", reason=noalloc_pair_op_mnemonic_would_change"
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }

        // pick the target addressing mode uniformly among the two
        // non-noAlloc alternatives (seed-deterministic)
        uint32_t cand[2], ncand = 0;
        for (uint32_t t = 1; t <= 3; t++)
            if (t != type) cand[ncand++] = t;
        const uint32_t new_type = cand[rng() % ncand];

        ArmISA::ExtMachInst new_emi = emi;
        new_emi.instBits = (enc & ~0x01800000u) | (new_type << 23);
        StaticInstPtr repl = arm_dec->decodeChaos(new_emi);

        // Predicate: still the SAME cracked pair-op (macroop + mnemonic).
        if (!repl || !repl->isMacroop() || repl->getName() != orig_name) {
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=crack_ctrl"
                    << ", event=honest_skip"
                    << ", reason=predicate_fail_not_same_macroop"
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", new_enc=0x" << std::hex << new_emi.instBits
                    << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }

        // Measured µop counts (the 04 metric: µop-count deviation vs the
        // fault-free baseline). delta<0 = crack suppressed (writeback µop
        // lost, "该拆的指令不拆"); delta>0 = extra µop (spurious writeback,
        // "不该拆的指令被拆"); delta==0 = composition swap (post<->offset).
        const uint32_t uops_orig = countMicroops(orig.get());
        const uint32_t uops_new = countMicroops(repl.get());
        const int32_t delta = int32_t(uops_new) - int32_t(uops_orig);
        const char *arm =
            delta < 0 ? "crack_suppressed" :
            delta > 0 ? "crack_forced_extra_uop" : "composition_swap";

        faults_injected_count++;
        if (write_log)
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: fetch_decode, mode=crack_ctrl"
                << ", pc=0x" << std::hex << pc << std::dec
                << ", orig_enc=0x" << std::hex << enc << std::dec
                << ", new_enc=0x" << std::hex << new_emi.instBits << std::dec
                << ", addr_mode=" << kTypeNames[type] << "->"
                << kTypeNames[new_type]
                << ", uops_orig=" << uops_orig
                << ", uops_new=" << uops_new
                << ", uops_delta=" << delta
                << ", arm=" << arm
                << ", orig_mnemonic=" << orig_name
                << ", new_mnemonic=" << repl->getName()
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        return repl;
    }

    // ---- W7 batch 1 (D56-D61) injection helper ----
    // D61 fp_route_bit: scan the top-level A64 instruction-class bits
    // enc[28:24] for a single-bit flip whose re-decode yields a REAL
    // (non-"unknown") instruction with a DIFFERENT opClass (the honest
    // gem5 approximation of the int-vs-FP/SIMD queue routing bit: gem5
    // routes by opClass -> FUPool capability, so the observable effect of
    // the mis-route is the FU/latency change). Uniform over the effective
    // bits; no effective bit = honest skip (wasted draw, no fault count).
    StaticInstPtr
    CHAOSDecode::injectFpRouteBit(uint64_t emi_raw, uint32_t enc,
                                  StaticInstPtr orig,
                                  const std::string &orig_name,
                                  ArmISA::Decoder *arm_dec, Addr pc)
    {
        ArmISA::ExtMachInst emi;
        emi = emi_raw;   // rebuild the full EMI (high 32 bits = decode ctx)

        const OpClass orig_oc = orig->opClass();
        // Effective-bit scan (the W6 reg_bitflip discipline): keep the
        // candidates whose flip re-decodes to a legal instruction routed
        // to a DIFFERENT opClass. Illegal flips (re-decode "unknown" —
        // gem5's illegal-decode StaticInst, misc.isa:849 mnemonic
        // "unknown") are NOT route changes and are excluded.
        std::vector<uint32_t> eff;
        for (uint32_t b : kFpRouteBits) {
            ArmISA::ExtMachInst t = emi;
            t.instBits = enc ^ (1u << b);
            StaticInstPtr c = arm_dec->decodeChaos(t);
            if (!c) continue;
            if (c->getName() == "unknown") continue;
            if (c->opClass() == orig_oc) continue;
            eff.push_back(b);
        }
        if (eff.empty()) {
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=fp_route_bit"
                    << ", event=honest_skip"
                    << ", reason=no_effective_route_bit"
                    << " (no single class-field bit re-decodes to a legal"
                    << " instruction with a different opClass)"
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }
        const uint32_t bit = eff[rng() % eff.size()];

        ArmISA::ExtMachInst new_emi = emi;
        new_emi.instBits = enc ^ (1u << bit);
        StaticInstPtr repl = arm_dec->decodeChaos(new_emi);
        if (!repl || repl->getName() == "unknown" ||
            repl->opClass() == orig_oc) {
            // Defensive re-check (decodeChaos is deterministic, so this
            // cannot diverge from the scan — belt and braces).
            if (write_log)
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: fetch_decode, mode=fp_route_bit"
                    << ", event=honest_skip"
                    << ", reason=predicate_fail_opclass_unchanged"
                    << ", pc=0x" << std::hex << pc << std::dec
                    << ", orig_enc=0x" << std::hex << enc << std::dec
                    << ", new_enc=0x" << std::hex << new_emi.instBits
                    << std::dec
                    << ", orig_mnemonic=" << orig_name
                    << std::endl;
            return nullptr;
        }

        faults_injected_count++;
        if (write_log) {
            // opclass_old/new names from the generated enums::OpClassStrings
            // table (base build artifact enums/OpClass.cc); the observable
            // route effect = the FU/latency change implied by the pair.
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: fetch_decode, mode=fp_route_bit"
                << ", pc=0x" << std::hex << pc << std::dec
                << ", orig_enc=0x" << std::hex << enc << std::dec
                << ", new_enc=0x" << std::hex << new_emi.instBits << std::dec
                << ", bits=[" << bit << "]"
                << ", opclass_old="
                << enums::OpClassStrings[static_cast<int>(orig_oc)]
                << ", opclass_new="
                << enums::OpClassStrings[static_cast<int>(repl->opClass())]
                << ", orig_mnemonic=" << orig_name
                << ", new_mnemonic=" << repl->getName()
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return repl;
    }

    void
    CHAOSDecode::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSDecode: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        o3cpu->setChaosDecode(this);
    }

} // namespace gem5
