# Canonical edge-count reconciliation

* Canonical source: the `edges` array of each per-run `causal_chain.json` / `*.strict.json`.
* `STRICT_E2E_EDGE_COUNTS_PER_RUN.csv` is generated from that source; every global number is the sum of those rows.
* `STRICT_E2E_CAUSAL_EDGES.csv` is generated from the same arrays in one pass.

## Totals

| Quantity | Value |
|---|---:|
| Runs | 180 |
| COMPLETE runs | 180 |
| JSON edges (sum of per-run) | 712998 |
| CSV edge rows | 712998 |
| Difference | 0 |
| DIRECT_OBSERVED | 712031 |
| RECONSTRUCTED_VERIFIED | 358 |
| CORRELATED_ONLY | 609 |
| UNRESOLVED | 0 |

## Edge-level definitions

* `DIRECT_OBSERVED` — the trace records the hardware relation itself: renamed physical-register def/use, payload-to-register writeback, explicit propagation row, or a recorded memory version.
* `RECONSTRUCTED_VERIFIED` — the relation is rebuilt from committed instructions with actual operand values and real ARM64 semantics, and the recomputation matches the recorded result.
* `CORRELATED_ONLY` — only ordering/association exists.  It is exported for transparency and is forbidden on a COMPLETE path.
* `UNRESOLVED` — a required relation could not be proven; any run containing one on a key path is not COMPLETE.

## Structural checks

* Duplicate/missing edge IDs or dangling node references: **0**
  * none

* JSON/CSV difference is zero: **True**
