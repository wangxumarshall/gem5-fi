# Research Limitations

These are research-observability boundaries, not hidden engineering failures.

1. The blinded observation set cannot separate M04 vs M08; both can present resident-hit + wrong value. Entry lineage/request-PA are simulator-only.
2. M02/M04/M08 share the final wrong-value symptom; trace events are required for more than a generic "wrong data" diagnosis.
3. M01/M03 final wrong value alone is ambiguous; TLB maintenance history, ASID relation and squash/permission evidence are needed.
4. Production availability of TLB entry ID/generation, modified PFN, PTW partial entries and permission-grant internals is UNKNOWN; no real-hardware interface is proven here.
5. M03 R01-R04 are SQUASHED/PARTIAL/COMPLETE; they are not detected exceptions.
6. M06 R01-R05 are DETECTED_CONTAINED, not generic MASKED; the exception is delivered and the guest value is correct.
7. M07 R02 has no permission_eval joined to the activation TranslationID; nearest same-VA deny is event 345 / tid 5.
8. Per-instruction IFU fetch/decode/commit nodes are not emitted by the frozen binary; they are not fabricated.
9. No classifier is trained and no accuracy or cross-workload generalization is claimed.
10. The 10 repeatability runs are prepared but not executed.
