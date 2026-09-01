from m5.params import *
from m5.SimObject import SimObject

class CHAOSCHI(SimObject):
    type = 'CHAOSCHI'
    cxx_class = 'gem5::CHAOSCHI'
    cxx_header = "mem/ruby/CHAOSCHI/CHAOSCHI.hh"

    # §2.9 L3/LLC + HHA coherence directory fault injector. Hooks
    # MessageBuffer::dequeue (the CHI directory/response message flow).
    # Modes:
    #   msg_delay (F6): delay a message's enqueue time (it arrives later ->
    #     propagation latency corruption; the doc's '传播时延' product).
    #   msg_drop (F6): drop a message entirely (lost response -> coherency
    #     violation, readers read stale values).
    #   payload_bitflip: corrupt the Ruby Message data bytes (needs
    #     functionalWrite, E3 proxy — deferred).
    # NOTE: Ruby-only — stdlib SE classic-cache doesn't use Ruby/CHI.
    # Needs a Ruby config (configs/se/ruby_chaos.py, deferred) to run.
    mode = Param.String("msg_delay",
        "msg_delay (F6) | msg_drop (F6) | payload_bitflip (deferred)")
    probability = Param.Float(1.0, "per-dequeue injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
