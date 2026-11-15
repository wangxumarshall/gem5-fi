# Formal MMU Verdict: M07-F0-W14-S01-R04

| Field | Value |
|---|---|
| sample_run_id | M07-F0-W14-S01-R04 |
| model | M07 |
| workload | W14 |
| context | R04 |
| target_va | 275100205312 |
| target_mode | Execute |
| fault_id | 1 |
| activation_event_id | 354 |
| consumption_event_id | 356 |
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

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M07-F0-W14-S01-R04/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M07-F0-W14-S01-R04/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M07-F0-W14-S01-R04/Run_Log/board.terminal`
- wrong-value proof: ['permission grant false -> true']
- terminal expected by model: True (allowed: ACTIVATED_MASKED, ARCH_STATE_CORRUPTION, CRASH, DETECTED_CONTAINED, SDC, TRACE_INCOMPLETE)

## Oracle evidence

```json
{
  "basis": "W14 permission guard (shared_changed / injected_success)",
  "context": "R04",
  "golden": null,
  "injected_success": 1,
  "line": "W14_RESULT ctx=R04 signal=0 phase=exec_xn observed=0xc7 observed_kind=value si_code=-1 fault_addr=0x0 fault_class=none fault_code_ok=1 pte_present=1 shared_before=0x1122334455667788 shared_after=0x1122334455667788 shared_changed=0 injected_success=1 expected=0xc7 value_ok=1 msg=done result=FAIL",
  "observed": 199,
  "shared_changed": 0,
  "workload_result": "FAIL",
  "wrong": null
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
