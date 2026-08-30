# CHAOSRenameMap — RAT (rename map) fault injector for O3CPU (plan §5.2, S1-2).
#
# method1 (Cholesky x[0]) core hypothesis: "映射张冠李戴/历史残留" — an arch
# reg's mapping is swapped to ANOTHER currently-allocated physReg, so a
# later read of the arch reg returns the value of a DIFFERENT live variable
# (history residue signature, popcount 21-32 bit multi-bit aliasing, not a
# single-bit SEU). This is the F5 (legal-domain substitute) fault model on
# the RAT, which a register-only injector (CHAOSPhysReg corrupts a cell)
# cannot reproduce — it corrupts the MAPPING decision layer.
#
# Three modes:
#   map_bitflip    : flip a bit of the map entry's physRegIdx (may point to
#                    a free/invalid slot —合法性校验 rejects if out of range)
#   f5_substitute  : point an arch reg at ANOTHER currently-allocated physReg
#                    (stolen from a different arch reg's mapping) — method1
#                    history residue. Legality: target must be int-class and
#                    currently mapped (not free).
#   f4_field_stuck : persistently pin an arch reg to a (wrong) physReg across
#                    subsequent rewrites (G2 write-path style, via periodicCheck)
#
# O3-only: dynamic_cast to O3CPU to reach frontRenameMap(). Self-attach is
# NOT used (RAT is not a SimObject) — the injector holds a cpu pointer and
# drives faults from its own attackEvent, same pattern as CHAOSPhysReg.

from m5.params import *
from m5.SimObject import SimObject


class CHAOSRenameMap(SimObject):
    type = "CHAOSRenameMap"
    cxx_class = "gem5::CHAOSRenameMap"
    cxx_header = "cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0,
        "Per-interval injection probability (use 1.0 with maxFaults=1).")
    mode = Param.String("f5_substitute",
        "map_bitflip: flip a bit of physRegIdx in the map entry | "
        "f5_substitute: point arch reg at another live physReg (method1) | "
        "f4_field_stuck: persistently pin a wrong mapping")
    targetArchReg = Param.Int(-1,
        "Target architectural register (-1 = random across int class). "
        "method1 points at long-lived accumulators (X19-X28 callee-saved).")
    regTargetClass = Param.String("integer",
        "Register class: 'integer' | 'floating_point' | 'vector'. "
        "Default integer (method1 is GPR residue).")
    faultMask = Param.UInt64(0,
        "map_bitflip bit mask (0 = random one bit within physRegIdx width).")
    bitsToChange = Param.Int(1, "Bits to flip when faultMask=0 (map_bitflip).")
    firstClock = Param.UInt64(0, "First clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1 for single-fault.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device). Nonzero = reproducible.")
    writeLog = Param.Bool(True, "Write rat_injections.log")
    semanticRole = Param.String("",
        "ABI role label for campaign heatmap (callee_saved/accum/etc). Metadata.")
