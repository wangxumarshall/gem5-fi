# 40-Sample Final Audit

Frozen campaign `MMU-FORMAL-20261113`. Read-only audit; no original artifact was modified.

## Sources cross-checked

- `MMU_Final_Formal_Campaign_Results.xlsx` sheet `40_Sample_Matrix`
- `40_Sample_Matrix_Completed.csv`
- `analysis/samples.csv` and `analysis/samples.json`
- each `attempt_*/<SampleRunID>/sample_manifest.json`
- each `Validation/verdict.json`
- each `logs/<SampleRunID>.result.json`
- design-time `authority/MMU_40_Sample_Matrix.csv`
- each `SHA256/SHA256SUMS.txt` and the campaign evidence index
- per-sample YAML: **n/a** (no per-sample YAML exists); the authority YAML `/home/sdc/gem5-fi-mmu-impl-v2/phase3/freeze/authority/MMU_Formal_Config.yaml` is design-time only

## Field agreement (40 samples)

| Field | AGREE | AGREE_VARIANT | DIFF | MISSING |
|---|---|---|---|---|
| SampleRunID | 40 | 0 | 0 | 0 |
| ModelID | 40 | 0 | 0 | 0 |
| ContextID | 40 | 0 | 0 | 0 |
| WorkloadID | 38 | 2 | 0 | 0 |
| AttemptID | 40 | 0 | 0 | 0 |
| FaultID | 40 | 0 | 0 | 0 |
| InjectionStatus | 40 | 0 | 0 | 0 |
| FaultConsumptionStatus | 40 | 0 | 0 | 0 |
| PropagationStatus | 40 | 0 | 0 | 0 |
| TerminalState | 40 | 0 | 0 | 0 |
| OracleResult | 40 | 0 | 0 | 0 |
| TraceCompleteness | 40 | 0 | 0 | 0 |
| RecordIntegrity | 40 | 0 | 0 | 0 |
| BinarySHA256 | 40 | 0 | 0 | 0 |
| ConfigSHA256 | 40 | 0 | 0 | 0 |
| WorkloadSHA256 | 40 | 0 | 0 | 0 |

The only non-plain-AGREE field is `WorkloadID` on the two W10S samples: the authoritative matrix/manifest ID stays `W10`; `verdict.workload` records the internal run workload `W10S` (`W10S-COLD-STORE`, `W10S-WARM-STORE`). This is the documented variant encoding, not a conflicting identity.

## Reconstructed campaign statistics

| Metric | Recomputed | Reported |
|---|---|---|
| planned | 40 | 40 |
| completed | 40 | 40 |
| valid injection | 40 | 40 |
| fault state consumed | 40 | 40 |
| FULL propagation | 36 | 36 |
| legal PARTIAL/SQUASHED | 4 | 4 |
| COMPLETE trace | 40 | 40 |
| terminal distribution | {"SDC": 31, "SQUASHED": 4, "DETECTED_CONTAINED": 5} | {"SDC": 31, "SQUASHED": 4, "DETECTED_CONTAINED": 5} |

Recomputed totals match the reported summary: **True**.

## Integrity checks

- SHA256SUMS entries recomputed: **798**, verified **798**, mismatches **0**, missing **0** (disk.img hashed once and all 40 recorded values are identical `bb8727...`).
- Evidence-index rows failing existence/hash: **0**.
- Frozen binary `CHAOS/gem5/build/ARM/gem5.opt` actual SHA256 `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185` equals every sample `BinarySHA256`.
- Every `verdict.event_count` equals the raw trace event count; zero chain-join mismatches in the 40 traces.

## Anomalies

- **INFO** `M06-F0-W10-S01-R02`: authoritative WorkloadID W10; verdict records internal run workload W10S (variant W10S-COLD-STORE)
- **INFO** `M06-F0-W10-S01-R02`: top-level rcS.scoped absent (variant rcS layout)
- **INFO** `M08-F0-W10-S01-R05`: authoritative WorkloadID W10; verdict records internal run workload W10S (variant W10S-WARM-STORE)
- **INFO** `M08-F0-W10-S01-R05`: top-level rcS.scoped absent (variant rcS layout)

## Per-sample result

| Sample | Model | Ctx | Workload | Attempt | Propagation | Terminal | Oracle | Trace | Integrity | Audit |
|---|---|---|---|---|---|---|---|---|---|---|
| M01-F0-W9-S01-R01 | M01 | R01 | W9 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M01-F0-W9-S01-R02 | M01 | R02 | W9 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M01-F0-W9-S01-R03 | M01 | R03 | W9 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M01-F0-W9-S01-R04 | M01 | R04 | W9 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M01-F0-W9-S01-R05 | M01 | R05 | W9 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M02-F0-W10-S01-R01 | M02 | R01 | W10 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M02-F0-W10-S01-R02 | M02 | R02 | W10 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M02-F0-W10-S01-R03 | M02 | R03 | W10 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M02-F0-W10-S01-R04 | M02 | R04 | W10 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M02-F0-W10-S01-R05 | M02 | R05 | W10 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M03-F0-W11-S01-R01 | M03 | R01 | W11 | A01 | PARTIAL | SQUASHED | PASS | COMPLETE | PASS | PASS |
| M03-F0-W11-S01-R02 | M03 | R02 | W11 | A01 | PARTIAL | SQUASHED | PASS | COMPLETE | PASS | PASS |
| M03-F0-W11-S01-R03 | M03 | R03 | W11 | A01 | PARTIAL | SQUASHED | PASS | COMPLETE | PASS | PASS |
| M03-F0-W11-S01-R04 | M03 | R04 | W11 | A01 | PARTIAL | SQUASHED | PASS | COMPLETE | PASS | PASS |
| M03-F0-W11-S01-R05 | M03 | R05 | W11 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M04-F0-W12-S01-R01 | M04 | R01 | W12 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M04-F0-W12-S01-R02 | M04 | R02 | W12 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M04-F0-W12-S01-R03 | M04 | R03 | W12 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M04-F0-W12-S01-R04 | M04 | R04 | W12 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M04-F0-W12-S01-R05 | M04 | R05 | W12 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M05-F0-W13-S01-R01 | M05 | R01 | W13 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M05-F0-W13-S01-R02 | M05 | R02 | W13 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M05-F0-W13-S01-R03 | M05 | R03 | W13 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M05-F0-W13-S01-R04 | M05 | R04 | W13 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M05-F0-W13-S01-R05 | M05 | R05 | W13 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M06-F0-W10-S01-R01 | M06 | R01 | W10 | A01 | FULL | DETECTED_CONTAINED | PASS_EXPECTED_DETECTION | COMPLETE | PASS | PASS |
| M06-F0-W10-S01-R02 | M06 | R02 | W10 | A01 | FULL | DETECTED_CONTAINED | PASS_EXPECTED_DETECTION | COMPLETE | PASS | PASS |
| M06-F0-W10-S01-R03 | M06 | R03 | W10 | A01 | FULL | DETECTED_CONTAINED | PASS_EXPECTED_DETECTION | COMPLETE | PASS | PASS |
| M06-F0-W10-S01-R04 | M06 | R04 | W10 | A02 | FULL | DETECTED_CONTAINED | PASS_EXPECTED_DETECTION | COMPLETE | PASS | PASS |
| M06-F0-W10-S01-R05 | M06 | R05 | W10 | A01 | FULL | DETECTED_CONTAINED | PASS_EXPECTED_DETECTION | COMPLETE | PASS | PASS |
| M07-F0-W14-S01-R01 | M07 | R01 | W14 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M07-F0-W14-S01-R02 | M07 | R02 | W14 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M07-F0-W14-S01-R03 | M07 | R03 | W14 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M07-F0-W14-S01-R04 | M07 | R04 | W14 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M07-F0-W14-S01-R05 | M07 | R05 | W14 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M08-F0-W10-S01-R01 | M08 | R01 | W10 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M08-F0-W10-S01-R02 | M08 | R02 | W10 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M08-F0-W10-S01-R03 | M08 | R03 | W10 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M08-F0-W10-S01-R04 | M08 | R04 | W10 | A02 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |
| M08-F0-W10-S01-R05 | M08 | R05 | W10 | A01 | FULL | SDC | FAIL | COMPLETE | PASS | PASS |

## Verdict

`SAMPLE_AUDIT = PASS` — 40/40 unique SampleRunIDs, 5 per model, R01-R05 per model, zero field conflicts beyond the documented W10S variant encoding, zero SHA256 mismatches, zero event-count mismatches, zero blocking anomalies.
