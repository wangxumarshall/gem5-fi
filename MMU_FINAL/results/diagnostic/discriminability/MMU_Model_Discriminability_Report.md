# Cross-Model Discriminability (model-ID-free)

This is not a trained classifier and no accuracy is claimed. Ground-truth model IDs are used only to group the evaluation.

## Blind feature distributions

| Feature | M02 | M04 | M08 | M01 | M03 | M06 | M07 |
|---|---|---|---|---|---|---|---|
| ObservedPathClass | PTW_WALK:5 | PTW_WALK:1,RESIDENT_HIT:4 | OTHER:1,PTW_WALK:4 | MAINTENANCE_THEN_REUSE:5 | PERMISSION_DENIED_SQUASHED:4,PERMISSION_GRANTED_EXECUTE:1 | EXCEPTION_DETECTION:5 | OTHER:1,PERMISSION_DENIED_CONSUMED:1,PTW_WALK:3 |
| ObservedMaintenanceEvents | True:5 | False:4,True:1 | False:5 | True:5 | False:4,True:1 | False:5 | True:5 |
| ObservedPTW | True:5 | False:4,True:1 | False:1,True:4 | False:5 | False:5 | True:5 | False:2,True:3 |
| ObservedPermissionResults | grant:5 | grant:5 | :1,grant:4 | grant:5 | deny:4,grant:1 | :5 | :1,deny:4 |
| ObservedSquash | False:5 | False:1,True:4 | False:5 | False:1,True:4 | False:1,True:4 | True:5 | False:5 |
| ObservedExceptionDelivery | False:5 | False:5 | False:5 | False:5 | False:5 | True:5 | False:5 |
| ObservedConsumerKind | lsu_request:5 | lsu_request:5 | lsu_request:5 | lsu_request:5 | lsu_request:1,squash:4 | exception_delivery:5 | lsu_request:5 |
| GuestValueMismatch_SW | True:5 | True:5 | True:5 | True:5 | False:4,True:1 | False:5 | False:5 |
| GuestUnexpectedSuccess_SW | False:5 | False:5 | False:5 | False:5 | False:5 | False:5 | True:5 |

## Pair conclusions

### M02/M04/M08

- Observable feature set: ObservedPTW, ObservedPartialEntry, ObservedTLBHits, ObservedConsumerKind, GuestValueMismatch_SW
- Distinguishing evidence: M02 has PTW; M04 has resident TLB hit in some contexts; M08 has final request PA corruption (simulator-only).
- Ambiguous cases: Blinded observation cannot separate M02/M04/M08 reliably: all show PTW and/or resident-hit signals and the same wrong-value symptom. M04 vs M08 is not separable without internal entry/request-PA instrumentation.
- Required additional observability: Simulator-assisted: refill-PFN event, entry lineage, request-PA delta. Production: page-table/PMU evidence not proven.

### M01/M03

- Observable feature set: ObservedMaintenanceEvents, ObservedTLBHits, ObservedPermissionResults, ObservedSquash, GuestValueMismatch_SW
- Distinguishing evidence: M01 shows maintenance events followed by reuse; M03 shows permission-eval categories (deny+squash or grant+execute).
- Ambiguous cases: If only the final wrong value is available, both are ambiguous. The observation must include maintenance history and permission/squash events.
- Required additional observability: Simulator-assisted: TLBI match/suppression, candidate ASID. Production: TLB maintenance history + ASID correlation may be indirectly testable but is not proven.

### M06/M07

- Observable feature set: ObservedExceptionDelivery, ObservedPermissionResults, ObservedSquash, GuestSignal_SW, GuestValueMismatch_SW, GuestUnexpectedSuccess_SW
- Distinguishing evidence: M06 has exception delivery/containment; M07 has permission denial followed by a successful consumer or unexpected success.
- Ambiguous cases: If exception delivery is not observed, M06 vs M07 can be ambiguous; guest unexpected-success is a software-visible separator when present.
- Required additional observability: Simulator-assisted: fault_state_consumed / exception class. Production: SIGSEGV/ESR and policy test are available, but exact internal cause is not.

## Boundaries

- M04 vs M08 is not separable from the blinded observation set; both can present resident TLB hit + wrong value. Simulator-assisted entry/request-PA evidence is needed.
- M02 vs M04/M08 cannot be separated by final software symptom alone; PTW presence helps only if the trace is available.
- M01 vs M03 require maintenance/ASID/permission/squash observations; final wrong value alone is ambiguous.
- M06 vs M07 is separable when exception delivery or unexpected-success is visible.
- No claim is made about generalization to new faults or workloads; the dataset has 40 contexts.
