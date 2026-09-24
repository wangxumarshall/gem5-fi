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
    mode = Param.String("dest_reg_sub",
        "dest_reg_sub | opcode_bitflip | opcode_bitflip2 | opcode_swap | "
        "reg_bitflip | reg_bitflip2 | imm_bitflip | imm_bitflip2")
    probability = Param.Float(1.0, "per-decode injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
