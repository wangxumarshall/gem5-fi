# FW05 configuration — Excel v3.2.3 (frozen)

Authority: `gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx`,
sheet `5.60个样本执行矩阵`, `3.最终12模型矩阵`, `4.源码Hook审计`,
`15.FW05配置冻结`.

| Field | Final value | Excel location |
|---|---|---|
| FaultModelID | FW05 | sample col 5 |
| FaultModelName | Wrong-Source Store-to-Load Forwarding | 15.FW05配置冻结 |
| TargetUnit | FWD | 15.FW05配置冻结 |
| TargetSubunit | Store-to-Load Forwarding Source Selection | 15.FW05配置冻结 |
| TargetFunction | `LSQUnit::read` / `CHAOSLSQFwd::maybeSubstituteFW05` | FaultLocation (6) |
| TargetField | true_src vs alt_src store data | TargetField (7) |
| FaultAction | SUBSTITUTE_ONE_WRONG_SOURCE | 15.FW05配置冻结 |
| WorkloadName | fw05_forward | 15.FW05配置冻结 |
| WorkloadPath | `<worktree>/.../workloads/fw05_forward` | WorkloadPath (19) |
| WorkloadSHA256 | 0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf | BinarySHA256 (20) |
| Oracle | 67afad307642983e | Oracle (22) |
| PilotStatus | R01 SQUASHED/PASS; R02–R05 SDC/FAIL; all accepted | ExecutionStatus (33), TerminalState_v31 (41) |

## Important scope note

Only the FW05 model-specific configuration is frozen. `ConfigFrozen` remains
`NO` for all 60 rows because global Warm-up and ROI are still researcher
decisions. This is not a full 60-sample formal freeze.

## Identity preservation

The five FW05 SampleRunID / RunID / SubTaskID / Seed values are unchanged
(asserted by `tests/test_lsu_v323_workbook.py`). The other 55 sample rows
and the 11 other models are cell-identical.
