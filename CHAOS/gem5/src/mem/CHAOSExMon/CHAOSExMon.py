from m5.params import *
from m5.SimObject import SimObject


class CHAOSExMon(SimObject):
    """S3-7 (plan §5.4B): exclusive-monitor (LL/SC reservation) injector.

    Hooks CacheBlk::lockList (the gem5 SE-with-caches model of the ARM
    local exclusive monitor; the AbstractMemory::lockedAddrList path is
    no-cache-only):
      - clear_reservation: after a load-linked (LDXR) registers its
        reservation, silently DROP it — every subsequent store-conditional
        (STXR) fails (chronic SC failure mode).
      - stale_reservation: when a write to a monitored address should ERASE
        other contexts' reservations, keep one alive — the victim's STXR
        succeeds without a valid reservation (silent lost-update race ->
        SDC direction: two writers both believe they won).

    Gates: firstClock/lastClock window, maxFaults (G5 single-fault),
    rngSeed (G0 replayable), writeLog evidence log.
    """

    type = "CHAOSExMon"
    cxx_class = "gem5::CHAOSExMon"
    cxx_header = "mem/CHAOSExMon/CHAOSExMon.hh"

    probability = Param.Float(1.0, "Per-reservation-event probability of injection")
    mode = Param.String("stale_reservation",
        "clear_reservation: drop a just-registered LDXR reservation | "
        "stale_reservation: keep a reservation alive when a conflicting "
        "write should have erased it (SC false-success race)")
    firstClock = Param.UInt64(0, "Earliest injectable cycle (0 = now)")
    lastClock = Param.UInt64(0, "Latest injectable cycle (0 = no limit)")
    maxFaults = Param.UInt64(1, "Max injections (0 = unlimited; G5 default 1)")
    rngSeed = Param.UInt64(20260825, "RNG seed (G0 replayable)")
    writeLog = Param.Bool(True, "Write exmon_injections.log evidence log")
