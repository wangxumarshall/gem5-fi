# Fault Consumption Semantics Report

Semantics are separated into FaultInjected, FaultActivated, FaultStateConsumed and DownstreamArchitecturalConsumption. `ExplicitFaultStateConsumedEventObserved` is only the literal `fault_state_consumed` event; it does not replace FaultStateConsumed.

## Counts

| Metric | Value |
|---|---|
| samples | 40 |
| fault_injected | 40 |
| fault_activated | 40 |
| fault_state_consumed | 40 |
| explicit_fault_state_consumed_event | 5 |
| downstream_architectural_consumption | 36 |
| architectural_data_corruption | 28 |
| terminal distribution | {"SDC": 31, "SQUASHED": 4, "DETECTED_CONTAINED": 5} |
| propagation distribution | {"FULL": 36, "PARTIAL": 4} |

## Per-model consumption evidence

| Model | Consumed | Downstream | Explicit literal event |
|---|---|---|---|
| M01 | 5/5 | 5/5 | 0/5 |
| M02 | 5/5 | 5/5 | 0/5 |
| M03 | 5/5 | 1/5 | 0/5 |
| M04 | 5/5 | 5/5 | 0/5 |
| M05 | 5/5 | 5/5 | 0/5 |
| M06 | 5/5 | 5/5 | 5/5 |
| M07 | 5/5 | 5/5 | 0/5 |
| M08 | 5/5 | 5/5 | 0/5 |

## Important distinctions

- **M03 R01-R04**: FaultStateConsumed=true (the false-ASID hit is used by translation), but DownstreamArchitecturalConsumption=false because the result is squashed before architectural update. Terminal SQUASHED / Propagation PARTIAL / Trace COMPLETE.
- **M06 R01-R05**: the literal `fault_state_consumed` event is present (5/5), but consumption is also proven by `pte_decode` and the Translation-Fault path. This is detection/containment, not generic masking.
- **M07 R02**: permission denial is recorded by `mmu_fault_activate(permission_before=false)`; no permission_eval with the same TranslationID is joined. This limitation remains.
- For M01/M02/M04/M05/M08, the consumption event is the model-specific TLB hit / request / translation result shown in the table; `fault_state_consumed` is not emitted.

## Verdict comparison

The recomputed counts match the frozen formal verdicts: FaultActivated=40, FaultStateConsumed=40, Propagation FULL=36/PARTIAL=4, Terminal SDC=31/SQUASHED=4/DETECTED_CONTAINED=5. No event was synthesized.
