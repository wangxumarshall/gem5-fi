from m5.params import *
from m5.SimObject import SimObject

class CHAOSMem(SimObject):
    type = 'CHAOSMem'
    cxx_class = 'gem5::CHAOSMem'
    cxx_header = "mem/CHAOSMem/CHAOSMem.hh"

    mem = Param.AbstractMemory(NULL, "Main memory pointer.")
    probability = Param.Float(0.0, "Probability (between 0 and 1) of processing cache fault injection")
    bitsToChange = Param.Int(-1, "Number of bits to change in the target cache packet during fault injection (from 0 to 8)")
    firstClock = Param.UInt64(0, "Clock cycle after which the cache fault injector is enabled (default 0)")
    lastClock = Param.UInt64(0, "Clock cycle after which the cache fault injector is disabled (default last clock cycle)")
    faultType = Param.String("random", "Type of alteration to be performed")
    faultMask = Param.String("0", "Bit mask to be applied to the target cache packet value")
    tickToClockRatio = Param.Int(1000, "Ratio between tick and clock cycle (tick/cycle)")
    bitFlipProb = Param.Float(0.9, "Probability (between 0 and 1) of injecting a bit flip fault on 'random' fault type")
    stuckAtZeroProb = Param.Float(0.05, "Probability (between 0 and 1) of injecting a stuck-at-zero fault on 'random' fault type")
    stuckAtOneProb = Param.Float(0.05, "Probability (between 0 and 1) of injecting a stuck-at-one flip fault on 'random' fault type")
    cyclesPermamentFaultCheck = Param.Int(1, "Number of cycles between each periodic check for permanent faults.")
    addr_start = Param.Addr(0, "Start address of the memory-mapped range (default: 0)")
    addr_end = Param.Addr(0, "End address of the memory-mapped range (default: 0, full memory length)")
    rngSeed = Param.UInt64(0, "Seed for the injection RNG (std::mt19937). 0 = seed from std::random_device (original, NON-reproducible behavior). Nonzero = fixed seed for reproducible address/byte/mask selection.")
    maxFaults = Param.UInt64(0, "G5: maximum number of faults to inject; 0 = unlimited (original). Use 1 for single-fault campaigns. Without this the original CHAOSMem keeps re-injecting forever (observed: maxFaults=1 still logged 5 injections in one tick).")
    protectionModel = Param.String("none",
        "§1.2 protection-aware modeling layer (N1 TRM Table 9-1 PROXY), "
        "DRAM = 'secded' (Huawei DDR ECC). Post-injection, keyed on "
        "popcount(mask) (bits this fault flips): 'none' (default = raw upper "
        "bound, leave = escape, zero regression); 'secded' (1-bit -> undo the "
        "byte write = Corrected; 2-bit -> poison-log + leave = Latent (no "
        "real poison bit in AbstractMemory backing store, E3 proxy); >=3-bit "
        "-> SilentEscape). Runs before the write-back so undo restores the "
        "original byte (== golden). Does NOT convert to product FIT.")
    writeLog = Param.Bool(True, "Write a log file")
    # §2.17 ECC-logic fault: model the SECDED *check/correct logic itself*
    # being faulty (not the data). 'none' (default = backing-byte injection,
    # orig); 'ecc_logic_fault' = build an in-CHAOSMem SECDED codec over an
    # 8-byte data word + 1-byte ECC syndrome, then inject a fault into the
    # *syndrome bits* (not the data) -> mis-correction / missed-detection
    # (a 1-bit data error gets miscorrected to a DIFFERENT value; a 2-bit
    # error is declared 'no error'). Models §2.17 'ECC logic itself unreliable'.
    # NOTE: §2.17 addr_map_sub needs DRAM coordinate mapping (E3, NOT here).
    # §2.17 addr_map_sub (F5, Phase 4.6): displaced WRITE — read 8 bytes at
    # the target address, write them at ANOTHER legal address (wrong DRAM
    # coordinate, bypasses cache tags). E3 proxy (no real DRAM geometry).
    addrMapSub = Param.Bool(False,
        "§2.17 F5: if true, attackMemory performs a displaced write (read at "
        "target, write at another legal address) instead of a byte flip.")
    eccLogicFault = Param.Bool(False,
        "§2.17: if true, the fault is applied to the in-CHAOSMem SECDED "
        "syndrome (ECC-logic fault), not the data byte. Models mis-correction "
        "/ missed-detection. Default false = backing-byte injection (orig).")