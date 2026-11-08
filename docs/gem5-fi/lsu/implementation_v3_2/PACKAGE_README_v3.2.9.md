# LSU v3.2.9 package — SP05 implementation, SQ03 probe, FW05 closure

Branch `lsu-platform-v3.2.9`, base v3.2.8 `d5c15309`; final binary SHA
`d6e60863bb63f85398b5aaa35539c0c6c3fdf582e3d969aace27611d5db97b90`.
No 60-sample formal run; ConfigFrozen NO for all 60.

## A_SP05
Definition freeze, source audit, C++ hook sources, git diff, unit test,
build logs, safety/watchdog report, five pilot directories with raw
trace_v31.jsonl, evidence CSV.

## B_SQ03
Original five pilots retained (metadata/logs/prop traces; the 188 MB JSONL
originals stay in the v3.2.8 package — see ORIGINAL_TRACE_NOTICE), propagation
analysis over the originals, the independent SQ03_Propagation_Probe workload
(P00 control / P01 fault) with traces, and the conclusion report. HANG risk
analysis remains in the v3.2.8 safety audit (included).

## C_FW05
Full workload archive (exact binary `0cf40509…`), fixed standalone
run_pilot.sh, SHA256SUMS, strict matched baselines (off/on on the final
binary), golden, Excel v3.2.4, original SDC retention note.

## D_Global
12-model matrix, authoritative Excel v3.2.4, 60_SAMPLE_MATRIX.csv, git
branch/HEAD/status/diff, final binary SHA, full test log, final report,
open issues, package SHA256SUMS.

## Verify
```bash
sha256sum -c SHA256SUMS
sha256sum A_SP05/pilots/SP05-R01/trace_v31.jsonl   # matches SHA256SUMS
GEM5_ROOT=<repo> C_FW05/archive/run_pilot.sh /tmp/fw05out 1025137124 1
```
