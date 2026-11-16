# CHAOSPrefetch — LSU W8 P-series prefetcher injector (09 §3 W8).
#
# Injects into the L2 StridePrefetcher (B0 baseline object, 02 r19). The
# injector hooks the TAIL of Stride::calculatePrefetch via the
# single-consumer registry Stride::chaosPrefetchHook (same pattern as
# BaseCache::chaosVictimHook) — one injector per run by grid construction.
#
# Modes (03-design-matrix P rows, fault semantics verbatim):
#   p01_stride_bitflip     P01: training-entry stride 1-bit XOR
#   p02_confidence_corrupt P02: confidence clear (reset) / fake-set
#                          (saturate), 50/50 per injection
#   p03_addr_subst         P03: generated prefetch address -> another legal
#                          aligned line in the SAME 4KiB page (negative
#                          control: prefetch errors must NOT change arch
#                          results; SDC => injector polluted the fill path)
#   p05_drop_dup           P05: drop / duplicate one generated prefetch,
#                          50/50 (also the P04 queue-family approximation —
#                          a missing/extra generation is the observable
#                          queue-content effect; documented approximation)
#   p08_stride_stuck       P08: stride stuck-at-0, re-applied on every
#                          eligible event (F5 nature; tier decides)
#
# HONEST BOUNDARY (not in this injector, routed/documented elsewhere):
#   P06 (mark prefetch as demand / wrong permissions)  — no clean hook, deferred
#   P07 (fill way/tag mismatch)  — cache-side, CHAOSCache tag-field approximation
#   P09 (prefetch-caused dirty-eviction writeback loss) — cache-side,
#        CHAOSCache dirty/victim approximation
from m5.params import *
from m5.SimObject import SimObject

class CHAOSPrefetch(SimObject):
    type = 'CHAOSPrefetch'
    cxx_class = 'gem5::CHAOSPrefetch'
    cxx_header = "mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.hh"

    mode = Param.String("p01_stride_bitflip",
        "p01_stride_bitflip | p02_confidence_corrupt | p03_addr_subst | "
        "p05_drop_dup | p08_stride_stuck (LSU 03 P-rows)")

    # LSU W2 trigger tier (docs/gem5-fi/lsu/05 r2-r8). This injector is
    # LSU-track-native: a tier is REQUIRED (no legacy cycle-window path —
    # unlike CHAOSAddrPath which keeps one for the KP track).
    lsuTier = Param.String("F0",
        "F0 | F1 | F2 | F3 | F4 | F5 | F6 (LSU event-normalized tier)")
    lsuWarmupEvents = Param.UInt64(0,
        "eligible events skipped before arming (LSU tiers)")
    lsuSpanEvents = Param.UInt64(1000,
        "F0 uniform window size in eligible events")
    lsuF6Event = Param.String("dirty_eviction",
        "F6 event: tlb_hit (FS-only) | sq_forward | dirty_eviction | "
        "cas_success")

    maxFaults = Param.UInt64(1, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    lineSize = Param.Addr(64,
        "cache line size for P03 same-page line arithmetic (must match the "
        "prefetcher's host cache)")
    writeLog = Param.Bool(True, "Write prefetch_injections.log")
