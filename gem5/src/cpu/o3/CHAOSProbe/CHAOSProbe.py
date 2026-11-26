from m5.params import *
from m5.SimObject import SimObject

# CHAOSProbe — W0.3a read-only OoO occupancy/threshold event probe.
# NOT an injector: never writes architectural/µarch state (reg_chain golden
# checksum must be unchanged with it attached). Samples every sampleEvery
# cycles and prints ONE `CHAOS_PROBE samples=... robOver80=... flIntLe8=...`
# stdout line at end of sim (field names embed the actual thresholds below;
# the defaults reproduce the plan interface verbatim). tools/event_density.py
# (W0.3b) parses that line.
class CHAOSProbe(SimObject):
    type = 'CHAOSProbe'
    cxx_class = 'gem5::CHAOSProbe'
    cxx_header = "cpu/o3/CHAOSProbe/CHAOSProbe.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    sampleEvery = Param.Unsigned(1, "sample every N CPU cycles (0 clamped to 1)")
    robThresholdPct = Param.Unsigned(80,
        "ROB over-occupancy threshold in percent (occupancy > pct% counts)")
    iqThresholdPct = Param.Unsigned(80,
        "IQ over-occupancy threshold in percent (occupancy > pct% counts)")
    flIntLe = Param.Unsigned(8,
        "int PRF freelist low-watermark (remaining <= N counts)")
    flFloatLe = Param.Unsigned(12,
        "float PRF freelist low-watermark (remaining <= N counts)")
    flVecLe = Param.Unsigned(6,
        "vec PRF freelist low-watermark (remaining <= N counts)")
    writeLog = Param.Bool(True,
        "also persist the summary line to chaos_probe.log (stdout always gets it)")
