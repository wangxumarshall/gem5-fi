# CHAOSFUPerm — functional-unit permanent fault injector, execution-level
# (harp plan Task 5.2; L1 of the two-level FU fault model).
#
# Models the paper's permanent FU fault (ISCA'24 §II-E: "permanent fault
# model at the gate level ... stuck-at-0 or stuck-at-1 simulated to the end
# of execution") at the microarchitectural execution level: every result
# produced by an instruction of the target OpClass is corrupted by a fixed
# bit mask, for the entire run. This is the writeback-path analog of a
# stuck gate whose error persists across every use.
#
# The gate-level netlist refinement (L2, plan Tasks 5.3/5.4) builds on this
# object's protocol: same mount, same classification, finer fault locus.
from m5.params import *
from m5.SimObject import SimObject


class CHAOSFUPerm(SimObject):
    type = "CHAOSFUPerm"
    cxx_class = "gem5::CHAOSFUPerm"
    cxx_header = "CHAOSFUPerm/CHAOSFUPerm.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # Target OpClass by name (enums::OpClass), e.g. IntAlu, IntMult,
    # FloatAdd, FloatMult, SimdFloatAdd, SimdFloatMultAcc ...
    targetOpClass = Param.String("IntAlu",
        "OpClass whose results are corrupted on EVERY execution "
        "(permanent execution-level fault)")

    # Fixed corruption mask XORed into each result (0 = derive a single
    # random bit from rngSeed at startup — deterministic per seed)
    faultMask = Param.UInt64(0, "Result XOR mask (0 = one random bit from seed)")

    rngSeed = Param.UInt64(0, "Seed for the random bit when faultMask=0")
    firstClock = Param.UInt64(0,
        "Cycle after which the fault is active (0 = from program start). "
        "Set to the ROI begin cycle to fault only the measured region — "
        "permanent faults active during C-library startup corrupt "
        "addresses and crash before any workload instruction (measured).")

    writeLog = Param.Bool(True, "Write fu_perm_injections.log (one line per "
                                "corrupted instruction)")
