from m5.params import *
from m5.SimObject import SimObject

# CHAOSMicroSnap — W2.4 read-only L1 µarchitecture shadow snapshot sampler.
# NOT an injector: never writes architectural/µarch state, never schedules
# events, prints nothing to stdout — the workload FINAL checksum must be
# byte-identical with it attached (hard gate, CHAOSProbe/CHAOSCommitTrace
# precedent). Emits one pinned-format CSV row every snapEvery committed
# instructions (occupancies + ROB head/tail + the FRONT rename map per class
# as FNV-1a-64 hash + full compact table) into the run --outdir; consumed by
# tools/micro_diff.py, which aligns a no-fault reference run against a faulted
# run by snap_seq and reports RAT divergence / occupancy deviation / IPC
# deviation series (L1 shadow compare, docs/gem5-fi/ooo 01-observation-points).
class CHAOSMicroSnap(SimObject):
    type = 'CHAOSMicroSnap'
    cxx_class = 'gem5::CHAOSMicroSnap'
    cxx_header = "cpu/o3/CHAOSMicroSnap/CHAOSMicroSnap.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    snapEvery = Param.Unsigned(1000,
        "take one snapshot every N committed instructions (0 clamped to 1)")
    traceFile = Param.String("micro_snap.csv.gz",
        "snapshot CSV output (relative to --outdir; .gz = auto gzip)")
    writeLog = Param.Bool(True,
        "write the snapshot CSV rows (false = attached but writes nothing)")
