from m5.params import *
from m5.SimObject import SimObject

class CHAOSPTW(SimObject):
    type = 'CHAOSPTW'
    cxx_class = 'gem5::CHAOSPTW'
    cxx_header = "arch/arm/CHAOSPTW/CHAOSPTW.hh"

    walker = Param.ArmWalkUnit(NULL, "Target ArmWalkUnit (FS-only)")

    # §2.10 page-table-walker fault injector. Hooks WalkUnit::doLongDescriptor
    # — bit-flips the fetched PTE (longDesc.data) pre-eval. HONEST: FS-only
    # (SE走translateMmuOff, doLongDescriptor never called in SE, doc §0.3).
    # ptwEcc knob models H7 (ECC-on spurious≈0 / off spurious>0).
    mode = Param.String("single_bit_xor",
        "single_bit_xor: XOR a single bit of the PTE | clear_valid: clear the "
        "PTE valid bit (conditionalValidBit, H7)")
    probability = Param.Float(1.0, "per-descriptor injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    faultMask = Param.UInt64(0, "bitmask for the PTE XOR (0 = random single bit)")
    ptwEcc = Param.Bool(True, "H7: ECC-on (spurious≈0) / off (spurious>0)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
