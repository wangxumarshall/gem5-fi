# Terminal Semantic Classification

Original frozen distribution: `{"SDC": 31, "SQUASHED": 4, "DETECTED_CONTAINED": 5}`.

## M03

- M03-F0-W11-S01-R01: Terminal=SQUASHED, Propagation=PARTIAL, Trace=COMPLETE, Primary=SQUASHED, Secondary=SQUASH_BEFORE_ARCH_UPDATE. No `exception_delivery` / `fault_result_propagated`; squash-only. Detection status=SQUASHED_BEFORE_COMMIT, masking=NOT_MASKED_SQUASHED.
- M03-F0-W11-S01-R02: Terminal=SQUASHED, Propagation=PARTIAL, Trace=COMPLETE, Primary=SQUASHED, Secondary=SQUASH_BEFORE_ARCH_UPDATE. No `exception_delivery` / `fault_result_propagated`; squash-only. Detection status=SQUASHED_BEFORE_COMMIT, masking=NOT_MASKED_SQUASHED.
- M03-F0-W11-S01-R03: Terminal=SQUASHED, Propagation=PARTIAL, Trace=COMPLETE, Primary=SQUASHED, Secondary=SQUASH_BEFORE_ARCH_UPDATE. No `exception_delivery` / `fault_result_propagated`; squash-only. Detection status=SQUASHED_BEFORE_COMMIT, masking=NOT_MASKED_SQUASHED.
- M03-F0-W11-S01-R04: Terminal=SQUASHED, Propagation=PARTIAL, Trace=COMPLETE, Primary=SQUASHED, Secondary=SQUASH_BEFORE_ARCH_UPDATE. No `exception_delivery` / `fault_result_propagated`; squash-only. Detection status=SQUASHED_BEFORE_COMMIT, masking=NOT_MASKED_SQUASHED.
- M03-F0-W11-S01-R05: Terminal=SDC, Propagation=FULL, Trace=COMPLETE, Primary=WRONG_CODE_PAGE_EXECUTION, Secondary=WRONG_TRANSLATION. No `exception_delivery` / `fault_result_propagated`; squash-only. Detection status=NOT_DETECTED, masking=NOT_MASKED.

## M06

- M06-F0-W10-S01-R01: Terminal=DETECTED_CONTAINED, Primary=DETECTED_CONTAINED, Secondary=TRANSLATION_FAULT_DETECTED_AND_CONTAINED, Detection=DETECTED_AND_CONTAINED, Masking=CONTAINED_BY_EXCEPTION_DELIVERY; exception evidence=True.
- M06-F0-W10-S01-R02: Terminal=DETECTED_CONTAINED, Primary=DETECTED_CONTAINED, Secondary=TRANSLATION_FAULT_DETECTED_AND_CONTAINED, Detection=DETECTED_AND_CONTAINED, Masking=CONTAINED_BY_EXCEPTION_DELIVERY; exception evidence=True.
- M06-F0-W10-S01-R03: Terminal=DETECTED_CONTAINED, Primary=DETECTED_CONTAINED, Secondary=TRANSLATION_FAULT_DETECTED_AND_CONTAINED, Detection=DETECTED_AND_CONTAINED, Masking=CONTAINED_BY_EXCEPTION_DELIVERY; exception evidence=True.
- M06-F0-W10-S01-R04: Terminal=DETECTED_CONTAINED, Primary=DETECTED_CONTAINED, Secondary=TRANSLATION_FAULT_DETECTED_AND_CONTAINED, Detection=DETECTED_AND_CONTAINED, Masking=CONTAINED_BY_EXCEPTION_DELIVERY; exception evidence=True.
- M06-F0-W10-S01-R05: Terminal=DETECTED_CONTAINED, Primary=DETECTED_CONTAINED, Secondary=TRANSLATION_FAULT_DETECTED_AND_CONTAINED, Detection=DETECTED_AND_CONTAINED, Masking=CONTAINED_BY_EXCEPTION_DELIVERY; exception evidence=True.

## M07

- M07-F0-W14-S01-R01: Terminal=SDC, Primary=UNAUTHORIZED_WRITE, Secondary=PERMISSION_BYPASS+DATA_INTEGRITY_SIDE_EFFECT. 
- M07-F0-W14-S01-R02: Terminal=SDC, Primary=UNAUTHORIZED_WRITE, Secondary=PERMISSION_BYPASS+DATA_INTEGRITY_SIDE_EFFECT. NO_PERMISSION_EVAL_JOINED_TO_ACTIVATION_TRANSLATION_ID_7; nearest same-VA deny is event 345 on translation_id=5 (tick delta -2331), not associated by the frozen validator; permission_before=false is recorded by mmu_fault_activate
- M07-F0-W14-S01-R03: Terminal=SDC, Primary=UNAUTHORIZED_READ, Secondary=PERMISSION_BYPASS. 
- M07-F0-W14-S01-R04: Terminal=SDC, Primary=UNAUTHORIZED_EXECUTION, Secondary=PERMISSION_BYPASS. 
- M07-F0-W14-S01-R05: Terminal=SDC, Primary=UNAUTHORIZED_EXECUTION, Secondary=PERMISSION_BYPASS. 

## Invariant

Original `TerminalState` and `OracleResult` are unchanged; v2 labels are a separate versioned semantic dimension.
