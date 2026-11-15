# Formal MMU Verdict: M04-F0-W12-S01-R05

| Field | Value |
|---|---|
| sample_run_id | M04-F0-W12-S01-R05 |
| model | M04 |
| workload | W12 |
| context | R05 |
| target_va | 275012124672 |
| target_mode | Execute |
| fault_id | 1 |
| activation_event_id | 481 |
| consumption_event_id | 485 |
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

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M04-F0-W12-S01-R05/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M04-F0-W12-S01-R05/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M04-F0-W12-S01-R05/Run_Log/board.terminal`
- wrong-value proof: ['resident entry itb:173:540 pfn 0x83559 -> 0x8353c; 0 entry-lifetime consumer(s)']
- terminal expected by model: True (allowed: ACTIVATED_MASKED, CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, SDC, SQUASHED)

## Oracle evidence

```json
{
  "basis": "target sentinel vs decoy sentinel",
  "context": "R05",
  "golden": 125,
  "line": "W12_RESULT ctx=R05 target_va=0x4008000000 target_pfn=0x83559 decoy_pfn=0x8353c observed=0x51 sentinel=0x7d decoy_sentinel=0x51 branch=0 mode=auto decoy_pfn_arg=0x0 decoy_arg_match=0 pagemap=ok pfn_ok=1/1 result=FAIL",
  "observed": 81,
  "workload_result": "FAIL",
  "wrong": 81
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
