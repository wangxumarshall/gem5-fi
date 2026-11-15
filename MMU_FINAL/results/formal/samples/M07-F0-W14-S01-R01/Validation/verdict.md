# Formal MMU Verdict: M07-F0-W14-S01-R01

| Field | Value |
|---|---|
| sample_run_id | M07-F0-W14-S01-R01 |
| model | M07 |
| workload | W14 |
| context | R01 |
| target_va | 275096010752 |
| target_mode | Write |
| fault_id | 1 |
| activation_event_id | 344 |
| consumption_event_id | 345 |
| ActivationStatus | ACTIVATED |
| FaultConsumptionStatus | CONSUMED |
| PropagationStatus | FULL |
| TraceCompleteness | COMPLETE |
| TerminalState | SDC |
| OracleResult | FAIL |
| RecordIntegrity | PASS |

## Missing causal edges / kinds

- none

## Evidence

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M07-F0-W14-S01-R01/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M07-F0-W14-S01-R01/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M07-F0-W14-S01-R01/Run_Log/board.terminal`
- wrong-value proof: ['permission grant false -> true']
- terminal expected by model: True (allowed: ACTIVATED_MASKED, ARCH_STATE_CORRUPTION, CRASH, DETECTED_CONTAINED, SDC, TRACE_INCOMPLETE)

## Oracle evidence

```json
{
  "basis": "W14 permission guard (shared_changed / injected_success)",
  "context": "R01",
  "golden": null,
  "injected_success": 1,
  "line": "W14_RESULT ctx=R01 signal=0 phase=store_ro observed=0x11223344556677c1 observed_kind=value si_code=-1 fault_addr=0x0 fault_class=none fault_code_ok=1 pte_present=1 shared_before=0x1122334455667788 shared_after=0x11223344556677c1 shared_changed=1 injected_success=1 expected=0x11223344556677c1 value_ok=1 msg=done result=FAIL",
  "observed": 1234605616436508609,
  "shared_changed": 1,
  "workload_result": "FAIL",
  "wrong": null
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
