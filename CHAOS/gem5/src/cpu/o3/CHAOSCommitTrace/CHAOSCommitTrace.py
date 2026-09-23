from m5.params import *
from m5.SimObject import SimObject

# CHAOSCommitTrace — W2.1 read-only L2 commit-per-instruction trace.
# NOT an injector: never writes architectural/µarch state and never schedules
# events — the workload FINAL checksum must be byte-identical with it
# attached (hard gate, CHAOSProbe precedent). Writes ONE CSV line per
# committed instruction, pinned format (consumed by tools/commit_diff.py):
#   seq,tid,tick,pc,op,ndest[,class,arch,phys,val]*
# (seq = self-held global commit counter from 0; pc = hex, no prefix;
#  val = 16 hex digits — scalar RegVal zero-padded, vector blob FNV-1a-64.)
# Unlike CHAOSProbe this needs the commit.cc hook (commitHead, after the
# commit-renameMap setEntry loop = the POST-INJECTION RAT), reached via the
# CHAOSRAS-style setter attached at startup().
class CHAOSCommitTrace(SimObject):
    type = 'CHAOSCommitTrace'
    cxx_class = 'gem5::CHAOSCommitTrace'
    cxx_header = "cpu/o3/CHAOSCommitTrace/CHAOSCommitTrace.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    traceFile = Param.String("commit_trace.csv.gz",
        "per-commit CSV trace output (relative to the run --outdir; "
        "a .gz suffix is gzip-compressed automatically)")
    writeLog = Param.Bool(True,
        "write the trace lines (False = attach but write nothing)")
