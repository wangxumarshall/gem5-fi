# CHAOSPhysReg — physical-register-file fault injector for O3CPU.
#
# Three injection abstractions (selectable via injectionMode):
#   'arch_commit'  : commitRenameMap.lookup(archReg) -> setReg
#                    (= original CHAOSReg behavior; FAILS on O3 — kept for
#                     comparison only, to quantify the artifact)
#   'arch_frontend': renameMap.lookup(archReg) -> setReg
#                    (corrected ARCH injection; targets the phys reg that
#                     in-flight instructions will read)
#   'phys'         : inject by PHYSICAL register index, regardless of which
#                    arch reg currently maps to it. This is what ITC'23 /
#                    GeFIN do; the only abstraction benchmarkable against
#                    them. A real defective cell doesn't know arch regs.
#
# O3-only: dynamic_cast<BaseCPU*, O3CPU*> to reach regFile/renameMap.
#
# This file mirrors CHAOSReg.py's parameter set and adds the mode/target knobs.

from m5.params import *
from m5.SimObject import SimObject


class CHAOSPhysReg(SimObject):
    type = "CHAOSPhysReg"
    cxx_class = "gem5::CHAOSPhysReg"
    cxx_header = "cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # --- injection abstraction (the point of this object) ---
    injectionMode = Param.String(
        "phys",
        "Injection abstraction: 'phys' (by phys index, = ITC'23/GeFIN), "
        "'arch_frontend' (renameMap.lookup = in-flight arch), "
        "'arch_commit' (commitRenameMap.lookup = original CHAOSReg, "
        "fails on O3, kept for comparison)")

    # --- target selection (per mode) ---
    targetPhysRegIdx = Param.Int(
        -1, "Physical register index to inject (phys mode). -1 = random "
        "across the selected register class.")
    targetArchRegIdx = Param.Int(
        0, "Architectural register index (arch_frontend / arch_commit modes). "
        "On aarch64 X0-X30 = 0-30 (31 = Zero, excluded); for floating_point "
        "class this indexes the FP arch reg file (V0-V31 = 0-31 on aarch64).")
    regTargetClass = Param.String(
        "integer", "Register class to target: 'integer' | 'floating_point' | "
        "'vector' | 'both' (phys mode: random pick across the three classes; "
        "arch modes: selects the rename map). 'vector' targets VecRegClass "
        "(whole SVE/NEON vectors — the actual AArch64 FMA/byte-swap hot path).")

    # --- vec lane stratification (Phase 2 item 1: NEON 128-bit lane FI) ---
    vecLaneWidth = Param.Int(32,
        "Vec lane width in BITS (8/16/32/64). The fault mask is applied to "
        "ONE lane of this width within the target VecRegClass phys reg. "
        "Default 32 = the 4x32-bit ASIMD lane granularity (kunpeng 920 "
        "baseline = 128-bit ASIMD, NOT SVE). 64 = 2x64-bit; 16 = 8x16-bit.")
    vecLaneOffset = Param.Int(-1,
        "Directed: which lane (0-indexed) to corrupt within the VecRegClass "
        "phys reg, e.g. lane 0 = the low vecLaneWidth bits. -1 = random "
        "lane across the vector width (default). Used with regTargetClass="
        "'vector' to stratify NEON per-lane SDC (plan §7.4 BM-NEON).")

    # --- fault model (mirrors CHAOSReg) ---
    probability = Param.Float(1.0, "Per-interval injection probability "
        "(use 1.0 with maxFaults=1 so the single injection lands at firstClock)")
    bitsToChange = Param.Int(1, "Number of bits to change (used when faultMask=0)")
    faultMask = Param.UInt64(0, "64-bit bitmask; 0 = randomly generated "
        "(bitsToChange bits). Covers the full AArch64 64-bit width — the old "
        "UInt32 silently truncated bit>=32 (1<<32 / 1<<63 became 0), so the "
        "G1 bit-stratified X2/X3 bit32/bit63 cases were never injected.")
    faultType = Param.String("bit_flip",
        "bit_flip | stuck_at_zero | stuck_at_one | random")

    # --- timing (lastClock fixed 0 = unrestricted, per project discipline) ---
    firstClock = Param.UInt64(0, "First clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted). DO NOT use as "
        "a window: small nonzero values cause silent zero-injection "
        "(see CHAOSReg.cc). Use maxFaults for count control.")

    # --- campaign control (patched-in, mirrors CHAOSReg) ---
    maxFaults = Param.UInt64(0, "Max faults to inject; 0 = unlimited. Use 1 "
        "for single-injection campaigns.")
    rngSeed = Param.UInt64(0, "RNG seed (std::mt19937). 0 = random_device "
        "(non-reproducible). Nonzero = fixed for reproducible register/mask.")

    writeLog = Param.Bool(True, "Write a fault_injections.log file")
