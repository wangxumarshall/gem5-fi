# MD04 configuration — Excel v3.2.2 (frozen)

Authority: `gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.2.xlsx`,
sheets `5.60个样本执行矩阵`, `3.最终12模型矩阵`, `4.源码Hook审计`,
`14.MD04配置冻结`; definition: `MD04_Definition_Freeze_v3.2.7.md`.

| Field | Final value | Excel column |
|---|---|---|
| FaultModelID | MD04 | 5.60!FaultModelID |
| FaultModelName | Store-to-Load Violation Suppression | 14 (freeze sheet) |
| TargetUnit | LSQ | 14 (freeze sheet) |
| TargetSubunit | Violation Detection | 14 (freeze sheet) |
| TargetFunction | `LSQUnit::checkViolations` | FaultLocation (6) |
| TargetField | M5PanicFault return path | TargetField (7) |
| NormalValue | ALLOW_M5PANICFAULT_RETURN | NormalValue (9) |
| FaultValue | SKIP_M5PANICFAULT_RETURN_ONCE | FaultValue (10) |
| FaultAction | SUPPRESS_ONE_VIOLATION_REPORT | 14 (freeze sheet) |
| TriggerCondition | Eligible Store-to-Younger-Load violation | EligibleEventCondition (15) |
| StoreSize | 8 bytes | TargetInstruction (14) + condition (15) |
| InjectionCount | 1 | FaultDuration (13) |
| AddressModification | NONE | v3.2_ConfigProvenance (43) + trace flags |
| SizeModification | NONE | v3.2_ConfigProvenance (43) + trace flags |
| DataModification | NONE | v3.2_ConfigProvenance (43) + trace flags |

No new duplicate columns were added to the 43-column sample matrix. The
three "Modification" fields are carried in the provenance cell and are
emitted as `address_modified=0;size_modified=0;data_modified=0` on every
injection event.

## Identity preservation

- The five MD04 SampleRunID / RunID / SubTaskID / Seed values are unchanged
  (asserted by `tests/test_lsu_v322_workbook.py`).
- The other 55 sample rows and the 11 other model rows are unchanged.
- `60_SAMPLE_MATRIX.csv` is a verbatim mirror of sheet 5 (43 columns ×
  60 rows).
