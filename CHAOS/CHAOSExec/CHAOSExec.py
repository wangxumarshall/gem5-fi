# CHAOSExec — integer execution unit fault injector (plan §5.10, S8-3).
# Negative control: P_SDC(Int) << P_SDC(FSU/forwarding) — confirms method1
# "integer path intact" + Veritas (integer adders SDC << FSU).
# Hooks the writeback result (DynInst::corruptResultRegVal) on integer
# instructions, flipping bits of the just-produced result before PhysReg write.
from m5.params import *
from m5.SimObject import SimObject

class CHAOSExec(SimObject):
    type = "CHAOSExec"
    cxx_class = "gem5::CHAOSExec"
    cxx_header = "cpu/o3/CHAOSExec/CHAOSExec.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0, "Per-interval injection probability.")
    faultMask = Param.UInt64(0, "Result XOR mask (0 = random bit 0-63).")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0.")
    bitSegment = Param.String("all",
        "Bit segment stratification: all | low[0:11] | mid[12:47] | high[48:63]. "
        "Confirm method1 'int path intact' — P_SDC(Int) << P_SDC(FSU).")
    firstClock = Param.UInt64(0, "First clock cycle eligible")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device).")
    writeLog = Param.Bool(True, "Write exec_injections.log")
    semanticRole = Param.String("", "ABI role label. Metadata only.")
