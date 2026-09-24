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
                      ImmBitflip2 };         // D07 immediate field, 2 bits
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
