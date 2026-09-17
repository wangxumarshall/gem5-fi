# CHAOSGateFU — synthetic gate-level netlist FU fault injector (harp plan
# Task 5.3; L2 of the two-level FU fault model, the paper's gate-level
# stuck-at protocol).
#
# The paper injects stuck-at-0/1 at GATES of the functional units (GeFIN's
# gate-level FU extension). gem5 has no RTL; we synthesize the datapath of
# the target FU as an injectable netlist (honest boundary: a synthetic
# structural model, not real RTL — documented in docs/harpocrates):
#   IntAdd : 64-bit Kogge-Stone adder
#   IntMult: 64x64 shift-add array multiplier (the adder stages reuse the
#            Kogge-Stone cell structure)
# Every result of the target OpClass is recomputed through the netlist
# with the injected stuck-at applied; a mismatch vs the architectural
# value propagates to the writeback (the fault effect).
from m5.params import *
from m5.SimObject import SimObject


class CHAOSGateFU(SimObject):
    type = "CHAOSGateFU"
    cxx_class = "gem5::CHAOSGateFU"
    cxx_header = "CHAOSGateFU/CHAOSGateFU.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    targetOpClass = Param.String("IntMult",
        "OpClass whose results are recomputed through the netlist: "
        "IntAlu (Kogge-Stone adder) or IntMult (shift-add array)")

    # Stuck-at site: gate index in the netlist (see gate count in stats).
    # -1 = no fault (equivalence-check mode). Polarity selects the value
    # the gate output is forced to.
    targetGate = Param.Int(-1, "Gate index to stick (-1 = none)")
    stuckPolarity = Param.Int(1, "Stuck value: 0 or 1")

    firstClock = Param.UInt64(0,
        "Cycle after which the fault is active (0 = from start; set to "
        "ROI begin like CHAOSFUPerm)")

    rngSeed = Param.UInt64(0, "Seed for the random bit when targetGate<0 "
                             "is not used; reserved")

    writeLog = Param.Bool(True, "Write gatefu_injections.log")
