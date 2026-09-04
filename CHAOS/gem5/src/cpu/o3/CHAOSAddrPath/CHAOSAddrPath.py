from m5.params import *
from m5.SimObject import SimObject

class CHAOSAddrPath(SimObject):
    type = 'CHAOSAddrPath'
    cxx_class = 'gem5::CHAOSAddrPath'
    cxx_header = "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.4 AGU address-path fault injector. Hooks LSQ::LSQRequest::
    # sendFragmentToTranslation BEFORE translateTiming — corrupts the
    # request vaddr (byte7 zero = canonical->non-canonical kernel address,
    # or low-bit flip). HONEST: SE-inert (SE physical memory from 0, 512MiB
    # — byte7 zero still lands in range, no fault). FS-only effective.
    mode = Param.String("byte7_zero",
        "byte7_zero: clear vaddr byte7 (canonical->non-canonical) | "
        "low_bit_flip: XOR a low bit of vaddr")
    probability = Param.Float(1.0, "per-sendFragment injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
