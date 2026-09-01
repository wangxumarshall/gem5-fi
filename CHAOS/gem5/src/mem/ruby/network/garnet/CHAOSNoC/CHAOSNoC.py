from m5.params import *
from m5.SimObject import SimObject

class CHAOSNoC(SimObject):
    type = 'CHAOSNoC'
    cxx_class = 'gem5::CHAOSNoC'
    cxx_header = "mem/ruby/network/garnet/CHAOSNoC/CHAOSNoC.hh"

    # §2.15 bufferless NoC Mesh fault injector. Hooks NetworkLink::wakeup
    # (the flit transfer point). Modes:
    #   flit_delay (F6): add a random delay to the flit's src_delay (models
    #     deflection/stall — bufferless vs buffered P_SDC comparison).
    #   route_sub (F5): corrupt the RouteInfo dest (flit goes to wrong node).
    #   payload_bitflip: corrupt the flit's msg payload data bytes (raw SDC
    #     if no CRC; needs Ruby Message functionalWrite, E3 proxy here).
    # NOTE: Garnet/Ruby-only — the stdlib SE classic-cache config does NOT use
    # Garnet. Needs a Ruby config (configs/se/ruby_chaos.py, deferred) to run.
    mode = Param.String("flit_delay",
        "flit_delay (F6) | route_sub (F5) | payload_bitflip")
    probability = Param.Float(1.0, "per-flit-transfer injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    faultMask = Param.UInt64(0, "bitmask for payload_bitflip (0=random)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
