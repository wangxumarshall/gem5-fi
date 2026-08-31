# CHAOSROB — ROB (reorder buffer) fault injector for O3CPU (plan §5.3, S1-4).
#
# method1 (Cholesky x[0]) ROB dimension: "投机流状态泄漏 + 异常位静默" —
# (1) exc_suppress: a faulting DynInst's `fault` is cleared -> DUE turns
#     into SDC (the trap that should signal a loud error is silenced).
# (2) entry_bitflip: flip a bit of a ROB-entry DynInst's seqNum (re-ordering
#     corruption; may mis-commit or trigger an exception).
# (3) spec_leak: on squash, the wrong-path μop's PRF write is retained ->
#     architectural state leak (method1's 4x numeric-vs-compute signature).
#     spec_leak needs a squash hook (deferred — needs lsq_unit/squash plumbing).
#
# O3-only: dynamic_cast to O3CPU to reach cpu->rob. Self-driven attackEvent
# (ROB is not a SimObject), same pattern as CHAOSPhysReg/CHAOSRenameMap.

from m5.params import *
from m5.SimObject import SimObject


class CHAOSROB(SimObject):
    type = "CHAOSROB"
    cxx_class = "gem5::CHAOSROB"
    cxx_header = "cpu/o3/CHAOSROB/CHAOSROB.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0,
        "Per-interval injection probability (use 1.0 with maxFaults=1).")
    mode = Param.String("entry_bitflip",
        "entry_bitflip: flip a bit of the ROB-head DynInst's seqNum | "
        "exc_suppress: clear a faulting DynInst's fault -> DUE-to-SDC | "
        "spec_leak: retain wrong-path PRF write on squash (needs squash hook, deferred)")
    distanceFromHead = Param.Int(0,
        "Distance from ROB head (0=head=about-to-commit; >0=older in-flight). "
        "entry_bitflip targets readHeadInst+distance (clamped to ROB size).")
    faultMask = Param.UInt64(0,
        "entry_bitflip seqNum bit mask (0 = random one bit).")
    bitsToChange = Param.Int(1, "Bits to flip when faultMask=0 (entry_bitflip).")
    firstClock = Param.UInt64(0, "First clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1 for single-fault.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device). Nonzero = reproducible.")
    writeLog = Param.Bool(True, "Write rob_injections.log")
    semanticRole = Param.String("",
        "ABI role label for campaign heatmap. Metadata only.")
