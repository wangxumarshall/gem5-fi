from m5.params import *
from m5.SimObject import SimObject

# CHAOSPropagation — [LSU][OBS-L3] real L3 propagation-chain tracer for LSU
# non-PRF faults (central correction directive 2026-10-13). READ-ONLY for
# architectural/µarch state: it observes the injector call path, the LSQ
# request/response path and the commit stream, and writes one CSV node per
# propagation event into prop_trace.csv.gz (pinned v1 format — see
# CHAOSPropagation.hh). NOT an injector: attaching it must leave the
# workload FINAL checksum byte-identical (CHAOSMicroSnap/CHAOSCommitTrace
# hard-gate precedent). Consumed by tools/lsu_l3_propagation.py
# (COVERED_FAMILIES = addrpath + cache; lsqfwd/prefetch/exmod stay
# unsupported, honestly).
class CHAOSPropagation(SimObject):
    type = 'CHAOSPropagation'
    cxx_class = 'gem5::CHAOSPropagation'
    cxx_header = "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    traceFile = Param.String("prop_trace.csv.gz",
        "propagation trace output (relative to --outdir; .gz = auto gzip)")
    writeLog = Param.Bool(True,
        "write the propagation trace (false = attached but inert)")
    addrExpiryTicks = Param.Unsigned(20000000,
        "registry entry lifetime in ticks (0 = never expire); bounds "
        "address-reuse misattribution (lazy sweep on insert/lookup)")
