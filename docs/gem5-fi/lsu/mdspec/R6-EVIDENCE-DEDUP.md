# R6 c9 evidence de-duplication — one authoritative copy per (RunID, seed)

Source: `runs/lsu/r6_c9_<RunID>_s<N>/<RunID>/cell_results.json` (main checkout).
`--max-seeds-per-cell N` is CUMULATIVE (seed1..N): `_s1` holds seed1, `_s2` holds seed1+seed2, `_s3` holds seed1+seed2+seed3.
Each `(RunID, seed)` has exactly ONE authoritative copy below; the other directories are EXCLUDED duplicates —
superseded re-runs, never counted as extra samples, never deleted (finding A1).

| RunID | seed | authoritative dir | certified | admitted | terminal | provable_to | graceful | outcome | excluded duplicate DIRS |
|---|---|---|---|---|---|---|---|---|---|
| T01-F0-W4 | 1 | `r6_c9_T01-F0-W4_s3` | True | True | `detected_contained` | L2 | None | Masked | r6_c9_T01-F0-W4_s1, r6_c9_T01-F0-W4_s2 |
| T01-F0-W4 | 2 | `r6_c9_T01-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T01-F0-W4_s1, r6_c9_T01-F0-W4_s2 |
| T01-F0-W4 | 3 | `r6_c9_T01-F0-W4_s3` | True | True | `detected_contained` | L2 | None | Masked | r6_c9_T01-F0-W4_s1, r6_c9_T01-F0-W4_s2 |
| T02-F0-W4 | 1 | `r6_c9_T02-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T02-F0-W4_s1, r6_c9_T02-F0-W4_s2 |
| T02-F0-W4 | 2 | `r6_c9_T02-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T02-F0-W4_s1, r6_c9_T02-F0-W4_s2 |
| T02-F0-W4 | 3 | `r6_c9_T02-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T02-F0-W4_s1, r6_c9_T02-F0-W4_s2 |
| T02-F2-W4 | 1 | `r6_c9_T02-F2-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T02-F2-W4_s1, r6_c9_T02-F2-W4_s2 |
| T02-F2-W4 | 2 | `r6_c9_T02-F2-W4_s3` | False | False | `provable_to_L5_then_unknown` | L5 | None | Crash | r6_c9_T02-F2-W4_s1, r6_c9_T02-F2-W4_s2 |
| T02-F2-W4 | 3 | `r6_c9_T02-F2-W4_s3` | True | True | `full` | L5 | True | Timeout | r6_c9_T02-F2-W4_s1, r6_c9_T02-F2-W4_s2 |
| T04-F0-W4 | 1 | `r6_c9_T04-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T04-F0-W4_s1, r6_c9_T04-F0-W4_s2 |
| T04-F0-W4 | 2 | `r6_c9_T04-F0-W4_s3` | True | True | `full` | L5 | True | Timeout | r6_c9_T04-F0-W4_s1, r6_c9_T04-F0-W4_s2 |
| T04-F0-W4 | 3 | `r6_c9_T04-F0-W4_s3` | True | True | `full` | L5 | True | Timeout | r6_c9_T04-F0-W4_s1, r6_c9_T04-F0-W4_s2 |
| T04-F2-W4 | 1 | `r6_c9_T04-F2-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T04-F2-W4_s1, r6_c9_T04-F2-W4_s2 |
| T04-F2-W4 | 2 | `r6_c9_T04-F2-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T04-F2-W4_s1, r6_c9_T04-F2-W4_s2 |
| T04-F2-W4 | 3 | `r6_c9_T04-F2-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T04-F2-W4_s1, r6_c9_T04-F2-W4_s2 |
| T04-F6-W4 | 1 | `r6_c9_T04-F6-W4_s1` | True | True | `full` | L5 | None | Timeout | — |

**Distinct (RunID, seed) pairs certified + admitted: 15/16**

**NOT admitted: [('T02-F2-W4', 2, 'provable_to_L5_then_unknown')]**

`T02-F2-W4` seed2 is NOT admitted in BOTH independent runs (`_s2` and `_s3`):
`certified=False, admitted=False, terminal=provable_to_L5_then_unknown`, violations include `no_closed_chain_and_no_containment`.
That is a deterministic experimental outcome (no closed L0→L5 chain and no explicit containment), not a flake.

A3 re-check: `T04-F0-W4` seed2 re-run in `_s3` is `graceful=True, gem5_exit=0, terminal=full, provable_to=L5, admitted=True` —
the earlier non-graceful `_s2` copy is superseded and excluded. A3 resolved PASS; no forced-timeout counted as a pass.
