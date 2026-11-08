# MD04 old/new definition diff (v3.2.1 → v3.2.2)

| Field | v3.2.1 (superseded) | v3.2.2 (frozen) | Why |
|---|---|---|---|
| FaultLocation | Violation检测：checkViolations | LSQ违规检测：LSQUnit::checkViolations | Names the exact function; no behavior change. |
| TargetField | `possibleLoadViolation` | M5PanicFault return path | `possibleLoadViolation(true)` is the load/load snoop flag at `lsq_unit.cc:642`, consumed by the snoop path; W7's store→younger-load detection is the `M5PanicFault` return in the store branch (`lsq_unit.cc:676-679`). |
| NormalValue | 检测到alias后possibleLoadViolation=true | ALLOW_M5PANICFAULT_RETURN | The real normal behavior is returning M5PanicFault, not setting a flag. |
| FaultValue | 跳过一次置位 | SKIP_M5PANICFAULT_RETURN_ONCE | Suppress exactly one real violation report. |
| FaultAction | (implicit flag skip) | SUPPRESS_ONE_VIOLATION_REPORT | Distinguishes report suppression from data/address faults. |
| TriggerCondition | 真实同地址alias | StoreSize=8; LoadSize>=8; YoungerLoad; real byte overlap + gem5 shifted-range predicate | Researcher-confirmed MD04-ELIG-v1: 8-byte store, LDP-16 covering included, 4-byte excluded, different addresses excluded. |
| StoreSize | unspecified | 8 bytes | Older store must be an 8-byte store. |
| InjectionCount | F6 single (implicit) | 1 | One selected dynamic violation event per sample. |
| AddressModification | unspecified | NONE | Report-only fault. |
| SizeModification | unspecified | NONE | Report-only fault. |
| DataModification | unspecified | NONE | Report-only fault. |

## Consequences

- The old exact-start-address rule missed a real eligible pair: the 16-byte
  load 69297 / store 69294 at `0x...fb00` (real overlap with the load's upper
  half, same gem5 violation predicate). It is now eligible ordinal 5.
- Consequently the historical R05 target (71660/71652) is now eligible
  ordinal 6. R05 is marked `HISTORICAL_NONCONFORMING (ordinal drift)` and
  the frozen R05 run uses ordinal 5 (69297/69294). R01–R04 keep their
  ordinals 1–4.
- The old workbook never carried `TargetPairID`, store size/address or the
  injection request id; v3.2.2/v3.2.7 traces do.
