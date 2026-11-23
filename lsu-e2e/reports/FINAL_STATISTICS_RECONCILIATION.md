# FINAL statistics reconciliation

Every statistic is regenerated from the 180 frozen chain JSONs.
Expected baseline is the strict R1 classification; no label was changed to fit it.

| Check | Expected | Actual | Status |
|---|---|---|---|
| WRONG_OUTPUT | 108 | 108 | PASS |
| NO_VISIBLE_ERROR | 37 | 37 | PASS |
| INTERMEDIATE_VALUE_DIVERGENCE | 20 | 20 | PASS |
| HANG_TIMEOUT (software) / SIMULATOR_WATCHDOG (application) | 15 | 15 / 15 | PASS |
| Total edges | 712998 | 712998 | PASS |
| Masking-silent runs | 57 | 57 | PASS |
| RP01 watchdog | 15 | 15 | PASS |
| Reconciliation rows | 6812 | 6812 | PASS |

Termination counts: `{"ACTIVATED_NO_DATA_CORRUPTION": 34, "COMMITTED_AND_PROPAGATED": 108, "MASKED_BY_NON_CONSUMPTION": 3, "MASKED_BY_OVERWRITE": 18, "MASKED_BY_VALUE_CONVERGENCE": 2, "SIMULATOR_STALL_WATCHDOG": 15}`.

Application symptom counts: `{"INTERMEDIATE_VALUE_DIVERGENCE": 20, "NO_VISIBLE_ERROR": 37, "SIMULATOR_WATCHDOG": 15, "STALE_DATA_USED": 47, "WRONG_ADDRESS_EFFECT": 24, "WRONG_MEMORY_CONTENT": 27, "WRONG_NUMERIC_VALUE": 10}`.

Overall: **PASS**.
