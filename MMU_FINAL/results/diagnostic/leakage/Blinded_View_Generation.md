# Blinded Diagnostic View Generation

`blind_features.derive_blind(events, guest, access_mode, target_va)` has **no ground-truth parameter**. It filters injector-only event kinds and derives path classes only from non-injector microarchitectural events.

## Guarantees

- No `FaultModelID`, `FaultOrigin`, `InjectionLocation`, `TraceFaultSite` or `FaultField` input.
- `SampleRunID` is replaced by `OpaqueSampleID` (S001..S040); the mapping is in the Ground Truth view only.
- Injector-only kinds (`mmu_fault_*`, `refill_pfn_corrupt`, `tlbi_suppressed`, `tlb_entry_lineage`, `fault_state_consumed`, `fault_result_propagated`, `fault_entry_*`, `chain_end`) are removed before deriving observations.
- `ObservedPathClass` is deliberately ambiguous where the remaining events are ambiguous (e.g. `RESIDENT_HIT` covers M04/M08; `PERMISSION_DENIED_SQUASHED` covers M03 R01-R04).
- `TerminalState`, `OracleResult` and `ManifestationType` are not in the blinded input; guest symptoms are software-visible observations, not origin labels.

## Leakage finding

The old `UpstreamPathClass_SIM` used `InjectionLocation.TraceFaultSite` and was effectively a model label. It is retained only in the legacy addendum and marked `LeakageRisk=HIGH`, `AllowedInBlindView=NO`.

No classifier is trained and no accuracy is claimed.
