from m5.params import *
from m5.SimObject import SimObject

class CHAOSDecode(SimObject):
    type = 'CHAOSDecode'
    cxx_class = 'gem5::CHAOSDecode'
    cxx_header = "cpu/o3/CHAOSDecode/CHAOSDecode.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.14 decode-unit fault injector. Hooks rename.cc:1137 AFTER
    # flattenedDestIdx is set (per-INST, NOT shared staticInst — safe).
    # dest_reg_sub (F5): replace the dest arch reg index with another legal
    #   integer reg 0-30 (zhang-guan-li-dai on the DEST, not the mapping).
    # HONEST: srcRegIdx/imm/opClass are NOT done — srcRegIdx reads shared
    #   staticInst (unsafe to mutate); imm/opClass need StaticInst clone.
    #   dest_reg_sub is the safe per-inst subset (the _flatDestIdx array is
    #   per-DynInst).
    #
    # W6 D01-D07 (ooo 04-design-matrix R2-R8 Int Decode): encoding-level
    # corruption at the FETCH decode output — hooks fetch.cc right after
    # dec_ptr->decode(), flips bits of the raw 32-bit A64 encoding and
    # re-decodes via ArmISA::Decoder::decodeChaos (cache-bypassing), then
    # replaces the fetch loop's LOCAL staticInst. AArch64 non-macroop only
    # (Thumb/macroop excluded). Log line carries orig_enc/new_enc/bits/
    # mnemonics — the encoding diff is recomputable (orig ^ (1<<b) == new).
    #   opcode_bitflip  (D01): 1 random bit of the opcode region
    #                            {31,30,29,28-24,21}; may land legal or
    #                            illegal (illegal -> Unknown -> SIGILL,
    #                            the expected Crash baseline).
    #   opcode_bitflip2 (D02): 2 distinct random bits, same region.
    #   opcode_swap     (D03): swap to a format-compatible LEGAL opcode
    #                            (ADD<->SUB, AND<->ORR, EOR<->EON,
    #                            MOVZ<->MOVN, LDR<->STR, ...; GNU-as
    #                            verified table) — bypasses the illegal-
    #                            encoding defense by construction.
    #   reg_bitflip     (D04): 1 bit of the reg-number positions
    #                            Rd[4:0]/Rn[9:5]/Rm[20:16]; verified
    #                            semantic: mnemonic unchanged AND a reg
    #                            operand index actually moved.
    #   reg_bitflip2    (D05): 2 distinct bits, same positions/predicate.
    #   imm_bitflip     (D06): 1 bit of the immediate region [21:10]
    #                            (imm12/immr+imms/imm6); verified semantic:
    #                            mnemonic unchanged AND reg operands
    #                            unchanged (value-only change).
    #   imm_bitflip2    (D07): 2 distinct bits, same region/predicate.
    # W6 batch 2 (D08-D10, ooo 04-design-matrix R9-R11), same fetch-decode
    # re-decode-and-replace mechanism:
    #   sign_ext_bit    (D08): flip EXACTLY the format-located sign/top bit
    #                            of the immediate's encoding (per-format
    #                            GNU-as-verified table); the re-decode's
    #                            own sign extension consumes the flip.
    #   imm_subfield_shift (D09): transpose two equal-width named subfields
    #                            of the immediate encoding (imms<->immr,
    #                            immlo<->immhi[1:0], hw<->imm16[15:14],
    #                            sh<->imm12[11:10]); single-field formats
    #                            honestly skipped WITH a log line.
    #   crack_ctrl      (D10, exploratory): on macroop (cracked) LDP/STP
    #                            decodes flip the addressing-mode field
    #                            enc[24:23] within {post,offset,pre} —
    #                            ±1 µop (spurious/lost writeback µop) or
    #                            composition swap, µop counts logged;
    #                            non-macroop honestly skipped (blocker).
    # W7 batch 1 (D56-D61, ooo 04-design-matrix R57-R62 FP/SIMD Decode),
    # same fetch-decode re-decode-and-replace engine, gated by fpOnly
    # (opClass in scalar Float* ∪ SimdFloat* — the CHAOSFPU.cc:88-98
    # isFpOpClass scope; integer SIMD is out of scope for W7.1,
    # documented honesty limitation):
    #   fp_opcode_bitflip  (D56): 1 random bit of the FP/SIMD opcode
    #                            region enc[23:10]; may land legal or
    #                            illegal (illegal -> SIGILL, the expected
    #                            Crash baseline).
    #   fp_opcode_bitflip2 (D57): 2 distinct random bits, same region.
    #   fp_opcode_swap     (D58, legal_domain_sub 换值): format-compatible
    #                            LEGAL FP pair (FADD<->FSUB, FMUL<->FDIV,
    #                            FMAX<->FMIN, FMAXNM<->FMINNM,
    #                            FMADD<->FMSUB, FNMADD<->FNMSUB,
    #                            FCMP<->FCMPE + the SIMD mirrors
    #                            FADD/FMAX/FMAXNM/FMLA/FCMEQ/FMUL/FABS
    #                            pairs; GNU-as closed-loop verified table).
    #   fp_reg_bitflip     (D59): 1 bit of the V-register-number positions
    #                            Vd[4:0]/Vn[9:5]/Vm[20:16] — the W6
    #                            reg_bitflip machinery unchanged (kRegBits
    #                            already covers the FP formats); verified
    #                            semantic: mnemonic unchanged AND a reg
    #                            operand index actually moved.
    #   fp_reg_bitflip2    (D60): 2 distinct bits, same positions.
    #   fp_route_bit       (D61): flip 1 bit of the top-level A64
    #                            instruction-class field enc[28:24] such
    #                            that the re-decode's opClass DIFFERS from
    #                            the original — the honest approximation
    #                            of the int-vs-FP/SIMD dispatch-queue
    #                            routing bit (gem5 has no separate route
    #                            latch; opClass selects the FUPool
    #                            capability, observable = FU/latency
    #                            effect); no effective bit -> honest skip.
    mode = Param.String("dest_reg_sub",
        "dest_reg_sub | opcode_bitflip | opcode_bitflip2 | opcode_swap | "
        "reg_bitflip | reg_bitflip2 | imm_bitflip | imm_bitflip2 | "
        "sign_ext_bit | imm_subfield_shift | crack_ctrl | "
        "fp_opcode_bitflip | fp_opcode_bitflip2 | fp_opcode_swap | "
        "fp_reg_bitflip | fp_reg_bitflip2 | fp_route_bit")
    probability = Param.Float(1.0, "per-decode injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
