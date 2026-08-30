# CHAOSFreeList — freelist fault injector for O3CPU (plan §5.2, S1-3).
#
# method1 (Cholesky x[0]) companion to CHAOSRenameMap: "活寄存器被误标空闲/
# 历史残留" — a physReg still mapped in the RAT is wrongly added to the free
# list, so the next rename allocates it to ANOTHER arch reg (double-occupancy);
# the old owner's in-flight reads then return the NEW owner's value (history
# residue signature). Distinct from CHAOSRenameMap (which swaps the MAPPING):
# CHAOSFreeList corrupts the ALLOCATION state (the free list), which the RAT
# injector can't reach.
#
# Two modes:
#   mark_free  : add a currently-LIVE physReg to the free list (it will be
#                re-allocated to a new arch reg on the next getReg — double
#                occupancy = method1 residue). Legality: target must be int-class
#                and currently NOT free (isFree==false, i.e. allocated).
#   pop_wrong  : same as mark_free but immediately consume the wrongly-added
#                slot via getReg (forces the double-allocation at inject time).
#
# O3-only: dynamic_cast to O3CPU to reach physFreeList(). Self-driven
# attackEvent (freelist is not a SimObject), same pattern as CHAOSPhysReg/
# CHAOSRenameMap.

from m5.params import *
from m5.SimObject import SimObject


class CHAOSFreeList(SimObject):
    type = "CHAOSFreeList"
    cxx_class = "gem5::CHAOSFreeList"
    cxx_header = "cpu/o3/CHAOSFreeList/CHAOSFreeList.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0,
        "Per-interval injection probability (use 1.0 with maxFaults=1).")
    mode = Param.String("mark_free",
        "mark_free: add a live physReg to the free list (method1 residue) | "
        "pop_wrong: mark_free + immediate getReg (force double-allocation)")
    targetPhysReg = Param.Int(-1,
        "Target physReg index (-1 = random across int class). method1 targets "
        "long-lived accumulators; combine with CHAOSRenameMap for full residue.")
    regTargetClass = Param.String("integer",
        "Register class: 'integer' | 'floating_point' | 'vector'. "
        "Default integer (method1 is GPR residue).")
    firstClock = Param.UInt64(0, "First clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1 for single-fault.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device). Nonzero = reproducible.")
    writeLog = Param.Bool(True, "Write freelist_injections.log")
    semanticRole = Param.String("",
        "ABI role label for campaign heatmap. Metadata only.")
