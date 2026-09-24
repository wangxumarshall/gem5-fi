#include "cpu/o3/CHAOSDecode/CHAOSDecode.hh"

#include <cstring>

#include "arch/arm/decoder.hh"
#include "arch/arm/types.hh"
#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst
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
        if (emi.thumb || !emi.aarch64) return nullptr;
        if (orig->isMacroop() || orig->isMicroop()) return nullptr;

        auto *arm_dec = dynamic_cast<ArmISA::Decoder *>(dec);
        if (!arm_dec) return nullptr;

        const uint32_t enc = emi.instBits;
        const bool is_reg_mode = (fi_mode == Mode::RegBitflip ||
                                  fi_mode == Mode::RegBitflip2);
        const bool is_imm_mode = (fi_mode == Mode::ImmBitflip ||
                                  fi_mode == Mode::ImmBitflip2);

        // ---- cheap per-mode eligibility (before skip/probability) ----
        const SwapRule *rule = nullptr;
        if (fi_mode == Mode::OpcodeSwap) {
            rule = matchSwapRule(enc);
            if (!rule) return nullptr;     // not a swappable opcode
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
        } else if (fi_mode == Mode::OpcodeSwap) {
            // Single verified opcode bit by construction (see kSwapRules).
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
                                   fi_mode == Mode::ImmBitflip2);
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
            if (fi_mode == Mode::OpcodeSwap)
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
