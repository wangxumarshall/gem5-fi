from m5.params import *
from m5.SimObject import SimObject

class CHAOSReg(SimObject):
    type = 'CHAOSReg'
    cxx_class = 'gem5::CHAOSReg'
    cxx_header = "CHAOSReg/CHAOSReg.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU")
    probability = Param.Float(0.0, "Probability (between 0 and 1) of injecting faults")
    bitsToChange = Param.Int(-1, "Number of bits to change during fault injection")
    firstClock = Param.UInt64(0, "Clock cycle after which fault injection starts")
    lastClock = Param.UInt64(0, "Clock cycle after which fault injection stops rescheduling. Default 0 means NO upper bound (unrestricted). NOTE: diverges from README which claims default -1 / -1 means unrestricted; here 0 is the unrestricted value. A literal -1 wraps to 0xFFFF...F via uint64 and also reads unrestricted, only by accident. Prefer maxFaults for count control and leave this at 0 to avoid silent zero-injection.")
    maxFaults = Param.UInt64(0, "Maximum number of faults to inject; 0 = unlimited (original behavior)")
    rngSeed = Param.UInt64(0, "Seed for the injection RNG (std::mt19937). 0 = seed from std::random_device (original, NON-reproducible behavior). Nonzero = fixed seed for reproducible injection (register/mask).")
    maxRegIdx = Param.UInt64(0, "Upper bound (exclusive) on the randomly sampled register index within its class. 0 = use full numRegs()-1 (original behavior, which on ARM/aarch64 includes integer[31]=Zero and idx>=32 banked/non-arch slots — a systematic bias). Set to 31 on aarch64 to restrict integer injection to X0-X30 (indices 0..30).")
    targetRegIdx = Param.Int(-1, "G1/report #5: directed architectural reg index (forces the fault onto this specific reg, so the manifest's target.index takes effect). -1 = random sample within [0, maxRegIdx). On aarch64 integer: 0=X0..30=X30.")
    faultType = Param.String("random", "Fault type: bit_flip, stuck_at_zero, stuck_at_one")
    faultMask = Param.UInt64(0, "Bit mask for the fault (64-bit; G1 width-aware)")
    regTargetClass = Param.String("both", "Target register class: integer, floating_point, or both")
    bitFlipProb = Param.Float(0.9, "Probability (between 0 and 1) of injecting a bit flip fault on 'bit_flip' fault type")
    stuckAtZeroProb = Param.Float(0.05, "Probability (between 0 and 1) of injecting a stuck-at-zero fault on 'stuck_at_zero' fault type")
    stuckAtOneProb = Param.Float(0.05, "Probability (between 0 and 1) of injecting a stuck-at-one flip fault on 'stuck_at_one' fault type")
    cyclesPermamentFaultCheck = Param.Int(1, "Number of cycles between each periodic check for permanent faults.")
    PCTarget = Param.Addr(0, "Specific PC value that triggers fault injection")
    writeLog = Param.Bool(True, "Write a log file")