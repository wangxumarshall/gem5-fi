# MMU Final Repeatability Campaign Report

Planned 10; completed 10; valid 10.

| Status | Value |
|---|---|
| `MMU_REPEATABILITY_CAMPAIGN` | `COMPLETE` |
| `MMU_REPEATABILITY_EVIDENCE` | `VALIDATED` |
| `MMU_FINAL_EXPERIMENTAL_FREEZE` | `READY` |
| `FORMAL_DATA_INTEGRITY` | `PASS` |

## Consistency

- Activation: `{"MATCH": 10}`
- Propagation: `{"MATCH": 10}`
- Terminal: `{"MATCH": 10}`
- Mismatch: 0; Unresolved: 0; Simulator failures: 0

| RepeatRunID | Formal Terminal | Repeat Terminal | Activation | Propagation | Terminal |
|---|---|---|---|---|---|
| REP-FINAL-MMU-M01-R01-01 | SDC | SDC | MATCH | MATCH | MATCH |
| REP-FINAL-MMU-M02-R02-01 | SDC | SDC | MATCH | MATCH | MATCH |
| REP-FINAL-MMU-M03-R01-01 | SQUASHED | SQUASHED | MATCH | MATCH | MATCH |
| REP-FINAL-MMU-M03-R05-01 | SDC | SDC | MATCH | MATCH | MATCH |
| REP-FINAL-MMU-M04-R05-01 | SDC | SDC | MATCH | MATCH | MATCH |
| REP-FINAL-MMU-M05-R05-01 | SDC | SDC | MATCH | MATCH | MATCH |
| REP-FINAL-MMU-M06-R02-01 | DETECTED_CONTAINED | DETECTED_CONTAINED | MATCH | MATCH | MATCH |
| REP-FINAL-MMU-M07-R01-01 | SDC | SDC | MATCH | MATCH | MATCH |
| REP-FINAL-MMU-M07-R05-01 | SDC | SDC | MATCH | MATCH | MATCH |
| REP-FINAL-MMU-M08-R01-01 | SDC | SDC | MATCH | MATCH | MATCH |

## Boundaries

- Two observations per context only; no statistical or cross-workload generalization is claimed.
- No independent repeat control was authorized; the approved formal shared controls remain the baseline.
- Simulator-only TLB/PTW/PFN internals remain simulator-only or UNKNOWN for production.
- No per-instruction IFU fetch/decode/commit event was fabricated.
