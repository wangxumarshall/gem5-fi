# CHAOSRAS — RAS-mechanism-escape injector for O3CPU (plan §5.11/S5-2, P1).
#
# Models the RAS-ESCAPE mechanism: a faulting instruction's exception is
# SILENTLY COMMITTED (the ERR* record that should log the error to the RAS
# subsystem is suppressed) — the DUE that hardware should have reported
# becomes an unreported SDC. This is the meta-analysis arm of §8.1 escape
# decomposition (mechanism E-adjacent: the protection/reporting logic
# itself fails), distinct from CHAOSROB::exc_suppress which models the ROB
# entry-level fault bit; CHAOSRAS hooks the COMMIT path (commitHead) and
# logs the suppression as a RAS record miss.
#
# O3-only. Self-driven attackEvent (same pattern as CHAOSROB/CHAOSPhysReg):
# polls the ROB head; when the head is FAULTING, with probability p the
# fault is cleared AND a "RAS-record-suppressed" log entry is written
# (the observable: the SDC event leaves NO RAS record behind).
from m5.params import *
from m5.SimObject import SimObject


class CHAOSRAS(SimObject):
    type = "CHAOSRAS"
    cxx_class = "gem5::CHAOSRAS"
    cxx_header = "cpu/o3/CHAOSRAS/CHAOSRAS.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0,
        "Per-poll suppression probability (use 1.0 with maxFaults=1).")
    firstClock = Param.UInt64(0, "First clock cycle eligible for suppression")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max suppressions (0 = unlimited). Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device).")
    writeLog = Param.Bool(True, "Write ras_injections.log")
    semanticRole = Param.String("",
        "ABI role label for campaign heatmap. Metadata only.")
