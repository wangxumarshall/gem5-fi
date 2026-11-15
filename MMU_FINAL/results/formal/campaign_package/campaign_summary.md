# MMU Final Formal Campaign — Results Summary

Campaign: `MMU-FORMAL-20261113`  
Binary: `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`

| Metric | Value |
|---|---|
| status | FORMAL_CAMPAIGN_COMPLETE_WITH_LIMITATIONS |
| planned_samples | 40 |
| started_samples | 40 |
| completed_samples | 40 |
| valid_injection_evidence | 40 |
| fault_state_consumed | 40 |
| full_propagation | 36 |
| chain_complete | 40 |
| legal_terminal | 40 |
| unfinished_samples | 0 |
| control_runs_referenced | 28 |
| control_zero_proven | 28 |

## TerminalState distribution

| Terminal | Count |
|---|---|
| DETECTED_CONTAINED | 5 |
| SDC | 31 |
| SQUASHED | 4 |

## Per-model

| Model | Mechanism | n | Terminal | Activation | Trace | Propagation |
|---|---|---:|---|---|---|---|
| M01 | L2/Unified TLB invalidation suppression | 5 | {'SDC': 5} | {'ACTIVATED': 5} | {'COMPLETE': 5} | {'FULL': 5} |
| M02 | PTW refill PFN corruption | 5 | {'SDC': 5} | {'ACTIVATED': 5} | {'COMPLETE': 5} | {'FULL': 5} |
| M03 | ASID tag-match false positive | 5 | {'SQUASHED': 4, 'SDC': 1} | {'ACTIVATED': 5} | {'COMPLETE': 5} | {'PARTIAL': 4, 'FULL': 1} |
| M04 | Resident TLB PFN substitution | 5 | {'SDC': 5} | {'ACTIVATED': 5} | {'COMPLETE': 5} | {'FULL': 5} |
| M05 | L2 partial walk-cache pointer substitution | 5 | {'SDC': 5} | {'ACTIVATED': 5} | {'COMPLETE': 5} | {'FULL': 5} |
| M06 | PTW leaf descriptor valid-bit corruption | 5 | {'DETECTED_CONTAINED': 5} | {'ACTIVATED': 5} | {'COMPLETE': 5} | {'FULL': 5} |
| M07 | Permission grant decision inversion | 5 | {'SDC': 5} | {'ACTIVATED': 5} | {'COMPLETE': 5} | {'FULL': 5} |
| M08 | Final PA materialization corruption | 5 | {'SDC': 5} | {'ACTIVATED': 5} | {'COMPLETE': 5} | {'FULL': 5} |

## Sample matrix

| # | SampleRunID | Model | Ctx | Activation | Propagation | Terminal | Trace | Oracle |
|---:|---|---|---|---|---|---|---|---|
| 1 | `M01-F0-W9-S01-R01` | M01 | R01 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 2 | `M01-F0-W9-S01-R02` | M01 | R02 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 3 | `M01-F0-W9-S01-R03` | M01 | R03 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 4 | `M01-F0-W9-S01-R04` | M01 | R04 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 5 | `M01-F0-W9-S01-R05` | M01 | R05 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 6 | `M02-F0-W10-S01-R01` | M02 | R01 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 7 | `M02-F0-W10-S01-R02` | M02 | R02 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 8 | `M02-F0-W10-S01-R03` | M02 | R03 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 9 | `M02-F0-W10-S01-R04` | M02 | R04 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 10 | `M02-F0-W10-S01-R05` | M02 | R05 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 11 | `M03-F0-W11-S01-R01` | M03 | R01 | ACTIVATED | PARTIAL | SQUASHED | COMPLETE | PASS |
| 12 | `M03-F0-W11-S01-R02` | M03 | R02 | ACTIVATED | PARTIAL | SQUASHED | COMPLETE | PASS |
| 13 | `M03-F0-W11-S01-R03` | M03 | R03 | ACTIVATED | PARTIAL | SQUASHED | COMPLETE | PASS |
| 14 | `M03-F0-W11-S01-R04` | M03 | R04 | ACTIVATED | PARTIAL | SQUASHED | COMPLETE | PASS |
| 15 | `M03-F0-W11-S01-R05` | M03 | R05 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 16 | `M04-F0-W12-S01-R01` | M04 | R01 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 17 | `M04-F0-W12-S01-R02` | M04 | R02 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 18 | `M04-F0-W12-S01-R03` | M04 | R03 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 19 | `M04-F0-W12-S01-R04` | M04 | R04 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 20 | `M04-F0-W12-S01-R05` | M04 | R05 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 21 | `M05-F0-W13-S01-R01` | M05 | R01 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 22 | `M05-F0-W13-S01-R02` | M05 | R02 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 23 | `M05-F0-W13-S01-R03` | M05 | R03 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 24 | `M05-F0-W13-S01-R04` | M05 | R04 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 25 | `M05-F0-W13-S01-R05` | M05 | R05 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 26 | `M06-F0-W10-S01-R01` | M06 | R01 | ACTIVATED | FULL | DETECTED_CONTAINED | COMPLETE | PASS_EXPECTED_DETECTION |
| 27 | `M06-F0-W10-S01-R02` | M06 | R02 | ACTIVATED | FULL | DETECTED_CONTAINED | COMPLETE | PASS_EXPECTED_DETECTION |
| 28 | `M06-F0-W10-S01-R03` | M06 | R03 | ACTIVATED | FULL | DETECTED_CONTAINED | COMPLETE | PASS_EXPECTED_DETECTION |
| 29 | `M06-F0-W10-S01-R04` | M06 | R04 | ACTIVATED | FULL | DETECTED_CONTAINED | COMPLETE | PASS_EXPECTED_DETECTION |
| 30 | `M06-F0-W10-S01-R05` | M06 | R05 | ACTIVATED | FULL | DETECTED_CONTAINED | COMPLETE | PASS_EXPECTED_DETECTION |
| 31 | `M07-F0-W14-S01-R01` | M07 | R01 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 32 | `M07-F0-W14-S01-R02` | M07 | R02 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 33 | `M07-F0-W14-S01-R03` | M07 | R03 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 34 | `M07-F0-W14-S01-R04` | M07 | R04 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 35 | `M07-F0-W14-S01-R05` | M07 | R05 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 36 | `M08-F0-W10-S01-R01` | M08 | R01 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 37 | `M08-F0-W10-S01-R02` | M08 | R02 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 38 | `M08-F0-W10-S01-R03` | M08 | R03 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 39 | `M08-F0-W10-S01-R04` | M08 | R04 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |
| 40 | `M08-F0-W10-S01-R05` | M08 | R05 | ACTIVATED | FULL | SDC | COMPLETE | FAIL |

## Control Zero Proof

| Control run | mmuFaultModel | exit | InjectionAppliedCount | Status |
|---|---|---|---|---|
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W9` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W10-R01` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W10-R02` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W10-R03` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W10-R04` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W10-R05` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W11-R01` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W11-R02` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W11-R03` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W11-R04` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W11-R05` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W12-R01` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W12-R02` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W12-R03` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W12-R04` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W12-R05` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W13-R01` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W13-R02` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W13-R03` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W13-R04` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W13-R05` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W10S-COLD` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL2-W14-R01` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL2-W14-R02` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL2-W14-R03` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL2-W14-R04` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL2-W14-R05` | `` | 0 | 0 | ZERO_PROVEN |
| `/home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-F1-CTRL-W10S-WARM` | `` | 0 | 0 | ZERO_PROVEN |

## Documented limitations

- 4 sample(s) end SQUASHED with PARTIAL downstream propagation by design (the faulted translation is squashed before a data-side consumer); their raw trace is COMPLETE.
- The frozen binary does not emit per-instruction IFU fetch-response, decode, or IFU-specific commit events; instruction-side samples use MMU translation/permission -> Execute Request -> Guest Oracle and mark the unobserved nodes NOT_EMITTED_BY_FROZEN_BINARY.
- Two samples were re-run under AttemptID A02 after an external process kill; original A01 partial attempts are preserved.

## Failures / incomplete

- No unfinished or trace-incomplete sample.
- Legitimate SQUASHED terminals: `M03-F0-W11-S01-R01`, `M03-F0-W11-S01-R02`, `M03-F0-W11-S01-R03`, `M03-F0-W11-S01-R04`
