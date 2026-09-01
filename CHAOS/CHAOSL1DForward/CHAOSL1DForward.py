# CHAOSL1DForward — post-check escape (PCE) injector (plan §5.8, §3.1 PCE).
from m5.params import *
from m5.SimObject import SimObject

class CHAOSL1DForward(SimObject):
    type = "CHAOSL1DForward"
    cxx_class = "gem5::CHAOSL1DForward"
    cxx_header = "cpu/o3/CHAOSL1DForward/CHAOSL1DForward.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0, "Per-interval injection probability.")
    faultMask = Param.UInt64(0, "Result XOR mask (0 = random bit).")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0.")
    firstClock = Param.UInt64(0, "First clock cycle eligible")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device).")
    writeLog = Param.Bool(True, "Write l1d_fwd_injections.log")
    semanticRole = Param.String("", "ABI role label. Metadata only.")
