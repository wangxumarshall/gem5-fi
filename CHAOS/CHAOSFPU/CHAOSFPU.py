# CHAOSFPU — FP/FSU writeback-path fault injector (plan §5.6, S8-2).
from m5.params import *
from m5.SimObject import SimObject

class CHAOSFPU(SimObject):
    type = "CHAOSFPU"
    cxx_class = "gem5::CHAOSFPU"
    cxx_header = "cpu/o3/CHAOSFPU/CHAOSFPU.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0, "Per-interval injection probability.")
    faultMask = Param.UInt64(0, "Result XOR mask (0 = random bit).")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0.")
    bitSegment = Param.String("all",
        "IEEE754 segment: all | sign | exp | mantissa. method3 mantissa 85-93%.")
    firstClock = Param.UInt64(0, "First clock cycle eligible")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device).")
    writeLog = Param.Bool(True, "Write fpu_injections.log")
    semanticRole = Param.String("", "ABI role label. Metadata only.")
