# SQ01 trace storage note

The five `SQ01-R0*/trace_v31.jsonl` files are 189 MB each (sq_drain produces
~198k events), above the GitHub 100 MB per-file limit. They are therefore kept
on disk and in `LSU_v3.2.3_Propagation_Closure_Package.zip`, but excluded from
Git. Each directory carries `trace_v31.jsonl.sha256` so the exact bytes can be
verified. The compressed raw `prop_trace.csv.gz`, manifest, meta, logs and
summary remain tracked.
