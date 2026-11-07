# v3.2.4 pilot trace storage

DA04 traces are 20–35 MB each and are committed in `DA04-R0*/trace_v31.jsonl`.
FW02 traces are ~6 MB and committed.

SQ01 traces are 189 MB each, above the GitHub 100 MB limit. They are kept on
disk and in `LSU_v3.2.4_DA04_Implementation_Package.zip`, with sha256
sidecars committed next to them (`trace_v31.jsonl.sha256`). Do not `git add`
the SQ01 `trace_v31.jsonl` files.

| Pilot | sha256 |
|---|---|
| SQ01-R01 | `c8aad1bba0dbcdaae4add24e5b5cd240111fd2856a81b096a450fe447a0706e1` |
| SQ01-R02 | see `SQ01-R02/trace_v31.jsonl.sha256` |
| SQ01-R03 | see `SQ01-R03/trace_v31.jsonl.sha256` |
| SQ01-R04 | see `SQ01-R04/trace_v31.jsonl.sha256` |
| SQ01-R05 | see `SQ01-R05/trace_v31.jsonl.sha256` |
