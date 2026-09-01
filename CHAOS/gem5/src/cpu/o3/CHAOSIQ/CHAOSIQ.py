# CHAOSIQ — issue-queue fault injector for O3CPU (plan §5.5, S8-1).
#
# method3 / core179 IQ dimension: "错源唤醒 + 相位竞态" —
#   src_ready_bitflip: flip a source-ready bit of an in-flight DynInst
#                      (false wake / missed wake -> wrong source value)
#   tag_sub (F5): substitute a srcReg tag with another physReg's
#                  (wrong-source dispatch — models F5 on the IQ tag field)
#   wake_phase (F6): +/-N cycle wake offset (deferred — needs IQ timing hook)
#   wake_omit (F6): omit a wake (deferred — same)
#
# O3-only. Self-driven attackEvent (IQ is not a SimObject). Reaches the ROB
# head DynInst via cpu->robAccess() (same as CHAOSROB) — the public IQ list
# is not iterable, so we operate on the about-to-commit DynInst's src fields
# as the observable IQ-state proxy.

from m5.params import *
from m5.SimObject import SimObject


class CHAOSIQ(SimObject):
    type = "CHAOSIQ"
    cxx_class = "gem5::CHAOSIQ"
    cxx_header = "cpu/o3/CHAOSIQ/CHAOSIQ.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0, "Per-interval injection probability (use 1.0 with maxFaults=1).")
    mode = Param.String("src_ready_bitflip",
        "src_ready_bitflip: flip a src-ready bit of the ROB-head DynInst | "
        "tag_sub: substitute a src tag with another physReg (F5) | "
        "wake_phase: F6 phase offset (deferred) | "
        "wake_omit: F6 omit a wake (deferred)")
    targetSrcIdx = Param.Int(-1, "Target source index (-1 = random within numSrcs).")
    faultMask = Param.UInt64(0, "src_ready_bitflip mask (0 = random one bit).")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0.")
    firstClock = Param.UInt64(0, "First clock cycle eligible")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device).")
    writeLog = Param.Bool(True, "Write iq_injections.log")
    semanticRole = Param.String("", "ABI role label. Metadata only.")
