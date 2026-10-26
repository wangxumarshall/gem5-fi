# R6 c9 evidence de-duplication — one authoritative copy per (RunID, seed)

Source: `runs/lsu/r6_c9_<RunID>_s<N>/<RunID>/cell_results.json` (main checkout).
`--max-seeds-per-cell N` is CUMULATIVE (seed1..N): `_s1` holds seed1, `_s2` holds seed1+seed2, `_s3` holds seed1+seed2+seed3.
Each `(RunID, seed)` has exactly ONE authoritative copy below; the other directories are EXCLUDED duplicates —
superseded re-runs, never counted as extra samples, never deleted (finding A1).

**Re-verified 2026-10-26 after Task 11b** (guarded `squash_masked` contain-by-squash fix in
`tools/lsu_chain_check.py` + `tools/lsu_prop_fields.py`). All 16 distinct `(RunID, seed)` pairs are now
`certified=True` + `admitted=True`; none truncated; no forced timeout counted as a pass.

| RunID | seed | authoritative dir | certified | admitted | terminal | provable_to | graceful | outcome | excluded duplicate DIRS |
|---|---|---|---|---|---|---|---|---|---|
| T01-F0-W4 | 1 | `r6_c9_T01-F0-W4_s3` | True | True | `detected_contained` | L2 | None | Masked | r6_c9_T01-F0-W4_s1, r6_c9_T01-F0-W4_s2 |
| T01-F0-W4 | 2 | `r6_c9_T01-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T01-F0-W4_s1, r6_c9_T01-F0-W4_s2 |
| T01-F0-W4 | 3 | `r6_c9_T01-F0-W4_s3` | True | True | `detected_contained` | L2 | None | Masked | r6_c9_T01-F0-W4_s1, r6_c9_T01-F0-W4_s2 |
| T02-F0-W4 | 1 | `r6_c9_T02-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T02-F0-W4_s1, r6_c9_T02-F0-W4_s2 |
| T02-F0-W4 | 2 | `r6_c9_T02-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T02-F0-W4_s1, r6_c9_T02-F0-W4_s2 |
| T02-F0-W4 | 3 | `r6_c9_T02-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T02-F0-W4_s1, r6_c9_T02-F0-W4_s2 |
| T02-F2-W4 | 1 | `r6_c9_T02-F2-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T02-F2-W4_s1, r6_c9_T02-F2-W4_s2 |
| T02-F2-W4 | 2 | `r6_c9_T02-F2-W4_s3` | True | True | `detected_contained` | L5 | None | Crash | r6_c9_T02-F2-W4_s1, r6_c9_T02-F2-W4_s2 |
| T02-F2-W4 | 3 | `r6_c9_T02-F2-W4_s3` | True | True | `full` | L5 | True | Timeout | r6_c9_T02-F2-W4_s1, r6_c9_T02-F2-W4_s2 |
| T04-F0-W4 | 1 | `r6_c9_T04-F0-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T04-F0-W4_s1, r6_c9_T04-F0-W4_s2 |
| T04-F0-W4 | 2 | `r6_c9_T04-F0-W4_s3` | True | True | `full` | L5 | True | Timeout | r6_c9_T04-F0-W4_s1, r6_c9_T04-F0-W4_s2 |
| T04-F0-W4 | 3 | `r6_c9_T04-F0-W4_s3` | True | True | `full` | L5 | True | Timeout | r6_c9_T04-F0-W4_s1, r6_c9_T04-F0-W4_s2 |
| T04-F2-W4 | 1 | `r6_c9_T04-F2-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T04-F2-W4_s1, r6_c9_T04-F2-W4_s2 |
| T04-F2-W4 | 2 | `r6_c9_T04-F2-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T04-F2-W4_s1, r6_c9_T04-F2-W4_s2 |
| T04-F2-W4 | 3 | `r6_c9_T04-F2-W4_s3` | True | True | `full` | L5 | None | Crash | r6_c9_T04-F2-W4_s1, r6_c9_T04-F2-W4_s2 |
| T04-F6-W4 | 1 | `r6_c9_T04-F6-W4_s1` | True | True | `full` | L5 | None | Timeout | — |

**Distinct (RunID, seed) pairs certified + admitted: 16/16**

**NOT admitted: — (none)**

A3 re-check (unchanged): `T04-F0-W4` seed2 re-run in `_s3` is `graceful=True, gem5_exit=0, terminal=full,
provable_to=L5, admitted=True` — the earlier non-graceful `_s2` copy is superseded and excluded. No forced
timeout is counted as a pass.

## Old → new verdict diff (Task 11b offline regrade — no gem5 re-run)

Old = the classifier at `HEAD b13966aa`; new = the Task 11b candidate. Both ran over the same raw
`prop_evt.txt.gz` bytes in the same directories (streams untouched). Only the classification changed.

| RunID | seed | field | old | new | why |
|---|---|---|---|---|---|
| **T02-F2-W4** | **2** | `terminal` | `provable_to_L5_then_unknown` | **`detected_contained`** | the chain's L0→L5 closing witness is a `squash_masked` containment event (`detection_layer=L4 contained=1 outcome=masked corr=addr_fallback containment_reason=squash_replay`); that kind was absent from both observation-layer maps, so `_event_has_prefix` rejected it and the `detected_contained` / `squash_replay_masked` / `containment_from_events` closure paths were structurally dead for it |
| **T02-F2-W4** | **2** | `admitted` | `False` | **`True`** | same — the explicit containment bundle (`layer=L4`, `na_layers=['L5']`) is now derived from a **closed, untruncated** stream |
| **T02-F2-W4** | **2** | `certified` | `False` | **`True`** | `certified = admitted ∧ ¬truncated` |
| T02-F2-W4 | 3 | (cause only) | — | — | `terminal`/`admitted` UNCHANGED (`full`/`True`); only the *containment bundle* of the event-count-max fault newly materialises (`None` → `{L4, ['L5']}`). It cannot affect admission: the chain already admits via `full` |
| T04-F2-W4 | 2 | (cause only) | — | — | idem — `full`/`True` unchanged, only the containment bundle appears |

No sample's terminal was downgraded; no sample other than `T02-F2-W4` seed2 changed its `admitted`
verdict, and the four uncounted duplicates in the two columns above behave identically to their
authoritative copies. The full-corpus regrade (all 144 readable `prop_evt.txt.gz` under `runs/lsu`,
6 of them too large to hold in memory probed instead for the one necessary condition) is recorded in
`.superpowers/sdd/2026-10-25-lsu-r6-frequency-policy/task-11b-report.md`.
