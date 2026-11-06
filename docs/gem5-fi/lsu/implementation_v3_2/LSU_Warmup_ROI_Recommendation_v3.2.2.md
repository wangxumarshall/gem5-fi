# LSU v3.2.2 — W1–W8 Warm-up / ROI Recommendation

**Status:** `NEEDS_RESEARCHER_CONFIRMATION` for every row. This document only
recommends; it does not modify the 60 SampleRunIDs, RunIDs, SubTaskIDs or seeds
in the frozen workbook. The formal Excel must not be updated until the
researcher confirms these boundaries.

**Evidence base:** measured fault-free baselines in `baselines/<workload>/`
(v3.2.1 binary `b233a4cb…`, stats SHA in each `run_meta.json`) and the W1–W8
sources in `workloads/`. Event counts below are source-derived eligible-event
budgets, not yet measured by a phase-instrumented build.

**Why not 0 / full:** the static SE binaries spend most of their dynamic
instructions in libc startup and in the workload's initialization loop. A
`WarmUp=0` formal sample would inject into libc or the initializer (no steady
state), and `ROI=full workload` would let the final checksum/verification loop
consume the fault before the modeled region ends. Both are explicitly rejected.

## Recommended table

| W | Workload | Init phase | Warm-up end condition | ROI start event | ROI end condition | R01–R05 ordinal origin | Injection-allowed range |
|---|---|---|---|---|---|---|---|
| W1 | `agu_addrmodes` | 64-element `array` init stores + first touch of the 4 KiB page | last store of the init loop (EA in the workload data page) | first load in addressing phase 1 (`base+imm`) | last load of the final `output[i]` reload loop | first eligible load of phase 1 | phase 1 start … final reload end |
| W2 | `lq_lifetime` | 4096-element `a[]` init + `guard` memset | last init store to `a[]` | first `a[idx]` load of the 64-iteration loop | last guard-load of the verification loop (or the last loop load if the guard loop is excluded) | first loop load | loop start … loop end |
| W3 | `sq_drain` | first 8192-iteration region-A store loop | last store of the 8192-iteration loop | first store of the second (4096-iteration) drain loop | last store of that loop, before `fnv1a` | first store of the second loop | second loop start … end |
| W4 | `sq_forward` | phase 1 full-overlap store→load pairs (32) | last phase-1 load | first phase-2 partial-overlap load | last load of the `memset`+bulk-load phase (phase 7) | first phase-2 load | phase 2 start … phase 7 end |
| W5 | `load_response` | 2048-element `a[]` init | last init store | first load of the 128-iteration loop | last loop load, before checksum | first loop load | loop start … loop end |
| W6 | `store_path` | region A (4096 byte stores) | last region-A store | first region-B unaligned 16-bit store | last store of the final same-width byte update | first region-B store | region B start … final update end |
| W7 | `replay_dependency` | 1024-element `a[]` init | last init store | first store of the 256-iteration store+load loop | last loop load | first loop store | loop start … loop end (contains the 5 partial-forward replays) |
| W8 | `alignment` | first 64 unaligned 4-byte writes (page touch) | 64th write | 65th unaligned write | last read of the read-back loop, before the final byte-update loop | first write after the page touch | write #65 … read-back end |

## Suggested ordinal placement inside the ROI

Use the R01–R05 contexts as five positions **inside** the ROI, not five events
from the ROI start. Recommended quantiles of the eligible-event budget:
R01 = 10 %, R02 = 30 %, R03 = 50 %, R04 = 70 %, R05 = 90 %. This keeps the
same seed/RunID/SubTaskID and only changes the EventOrdinal value that the
frozen workbook already carries per context.

## Measured totals (fault-free baselines)

| Workload | simInsts | executed loads | executed stores |
|---|---:|---:|---:|
| agu_addrmodes | 6,757 | 1,477 | 1,325 |
| lq_lifetime | 53,289 | 5,930 | 5,588 |
| sq_drain | 432,794 | 67,174 | 31,200 |
| sq_forward | 6,178 | 1,277 | 1,309 |
| load_response | 102,309 | 18,284 | 3,530 |
| store_path | 211,908 | 35,444 | 10,717 |
| replay_dependency | 54,967 | 10,086 | 2,764 |
| alignment | 36,125 | 6,750 | 3,151 |

The executed-load/store totals include libc startup; they are not eligible-event
counts. The recommended boundaries above are therefore expressed as program
phases and must be converted to event counts with a phase-instrumented run
before they can be frozen in the workbook.

## Open questions for the researcher

1. Are libc-startup accesses inside or outside the ROI? (Recommendation: outside;
   warm-up ends at the first workload-data-page access.)
2. For W2, is the guard-verification loop part of the ROI or the oracle region?
   (Recommendation: oracle region, excluded from the ROI.)
3. For W5, should the final checksum read-back be excluded? (Recommendation: yes,
   same as the W1 final reload.)
4. Confirm the five ordinal quantiles (10/30/50/70/90 %) or supply exact
   EventOrdinal values per RunID.
