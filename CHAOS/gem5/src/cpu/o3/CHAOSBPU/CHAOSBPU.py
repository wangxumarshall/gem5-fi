# CHAOSBPU — branch-predictor fault injector (plan §5.9, S8-4).
# Hooks BAC::predict (bac.cc): AFTER bpu->predict() computes the target,
# substitutes the predicted target with the fall-through address (pc()+4
# for AArch64) — an F5 legal-domain substitute (both are legal PCs; the
# wrong one forces a mispredict -> squash). Study point: does the wrong
# speculative stream LEAK architectural state (P(squash-then-arch==golden)
# should be ~= 1 — BPU is a negative-control surface).
from m5.params import *
from m5.SimObject import SimObject

class CHAOSBPU(SimObject):
    type = "CHAOSBPU"
    cxx_class = "gem5::CHAOSBPU"
    cxx_header = "cpu/o3/CHAOSBPU/CHAOSBPU.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0, "Per-prediction probability of target substitution.")
    mode = Param.String("target_sub",
        "target_sub: replace predicted target with fall-through pc+4 (F5). "
        "direction_flip: invert taken (F1).")
    firstClock = Param.UInt64(0, "First clock cycle eligible")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device).")
    writeLog = Param.Bool(True, "Write bpu_injections.log")
    semanticRole = Param.String("", "ABI role label. Metadata only.")
