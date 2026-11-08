# SQ03 original-trace propagation analysis (v3.2.9)

Tool: `tools/analyze_sq03_propagation.py`; data:
`evidence_v3_2_9/SQ03_propagation_v328.csv`. The five v3.2.8 pilots and
their traces are unchanged.

## Distinct moments (fault traces)

| Pilot | seq | `_canWB`/injection | `store_writeback` node | actual `store_mem_write` | commit | completion |
|---|---:|---:|---:|---:|---:|---:|
| R01 | 18 | 140910 | 140910 | 198275 | 149380 | 199045 |
| R02 | 19 | 141295 | 150150 | 203665 | 149380 | 205205 |
| R03 | 23 | 141680 | 150150 | 203665 | 149380 | 205206 |
| R04 | 24 | 142065 | 150150 | 203665 | 149380 | 205207 |
| R05 | 28 | 142450 | 150150 | 203665 | 149765 | 205208 |

The `store_writeback` node is emitted at the writeback decision/permission
point (for R01 it coincides with the injected `_canWB` tick); it is **not**
the cache update. The actual cache write is `store_mem_write`, 49,775–57,365
ticks later. Completion follows the cache write.

## Baseline comparison

The five v3.2.8 baselines (`evidence_v3_2_8/SQ03_baselines/`) were run
without the full store_writeback/store_mem_write nodes; they carry
`sq_lifecycle` only (e.g. R01 target `free/complete` at 204435). They cannot
be used to claim a cache-write delta, and this document does not. The matched
fault/no-fault visibility experiment is the `SQ03_Propagation_Probe`
(`SQ03_Probe_Report_v3.2.9.md`).

## What the traces do and do not show

- Injection succeeded: `canWB` 0→1, `storesToWB` 0→1, one injection each.
- Early permission is real, but the store's cache update still happens at its
  normal later tick; permission is not visibility.
- Later loads to the target address: 0; consumer instructions: 0. The four
  `consumer_inst_seq`-bearing records are propagation-edge bookkeeping, not
  consumers (the completeness summary reports `consumer_instructions=0`).
- No application-level SDC (all five oracle PASS).

Conclusion: the v3.2.8 fault moved the writeback-permission event, not the
observed data. Whether any data-flow consequence exists at all is tested by
the probe.
