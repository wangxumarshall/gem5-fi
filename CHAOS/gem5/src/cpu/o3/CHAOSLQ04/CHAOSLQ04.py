# CHAOSLQ04 — Load-Queue entry lifetime fault injector for O3CPU
# (LSU v3.2.10 LQ04).
#
# At the end of a successful LSQUnit::executeLoad (a live LQ entry whose
# request has just been issued), the selected entry's `valid` and `request`
# fields are moved into the LSQEntry side channel (corruptLifetime); the
# boundary restore (commit/squash) puts them back before clear(). Data,
# address and size are untouched — this is a structural lifetime fault.
#
# Selection is ordinal-driven and deterministic (F0, lq04_rules.hh): the
# eventOrdinal-th eligible Load (valid entry, owns its request, not
# squashed, not executed; prefetches excluded) is the one target, and the
# target is identified by its LQ entry identity (index + generation) so a
# replayed load is never injected twice.
#
# O3-only: self-attaches at startup() (cpu->chaosLQ04 = this); the
# lsq_unit.cc executeLoad tail calls maybeSelect (Task 6).
from m5.params import *
from m5.SimObject import SimObject


class CHAOSLQ04(SimObject):
    type = "CHAOSLQ04"
    cxx_class = "gem5::CHAOSLQ04"
    cxx_header = "cpu/o3/CHAOSLQ04/CHAOSLQ04.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    probability = Param.Float(1.0,
        "LQ04: global mount probability; <= 0 disables the ordinal "
        "injection and the watchdog (L-A06 control gate). Default 1.0 keeps "
        "the ordinal-only behavior when the flag is not wired.")
    eventOrdinal = Param.UInt64(0,
        "LQ04: 1-based eligible Load ordinal to select (0 = disabled). "
        "The Nth eligible load's LQ entry is the injection target.")
    maxFaults = Param.UInt64(1,
        "LQ04: maximum injections (0 clamps to 1)")
    countOnly = Param.Bool(False,
        "LQ04: count-only dry-run — count eligible loads, log up to "
        "probeFirstN probe lines and print CHAOS_LQ04_ELIGIBLE_COUNT at "
        "exit; never inject.")
    probeFirstN = Param.UInt64(0,
        "LQ04: log the first N eligible loads as "
        "CHAOS_LQ04_ELIGIBLE_PROBE lines (0 = none). Bounded logging for "
        "anchor verification in count-only and probe mode.")
    watchdogCycles = Param.UInt64(500000000,
        "LQ04: in-simulator watchdog in CPU cycles (0 = disabled); on "
        "expiry logs CHAOS_LQ04_WATCHDOG_EXPIRED and exits the simulation "
        "with code 1 (a stuck run must not classify as MASKED)")
    rngSeed = Param.UInt64(0,
        "LQ04: RNG seed recorded for reproducibility (the ordinal-driven "
        "F0 model draws no random numbers)")
    writeLog = Param.Bool(True, "write lq04_injections.log")
