# Formal MMU Verdict: M04-F0-W12-S01-R02

| Field | Value |
|---|---|
| sample_run_id | M04-F0-W12-S01-R02 |
| model | M04 |
| workload | W12 |
| context | R02 |
| target_va | 275012124672 |
| target_mode | Read |
| fault_id | 1 |
| activation_event_id | 631 |
| consumption_event_id | 633 |
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

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M04-F0-W12-S01-R02/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M04-F0-W12-S01-R02/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M04-F0-W12-S01-R02/Run_Log/board.terminal`
- wrong-value proof: ['resident entry dtb:82:3602 pfn 0x83559 -> 0x8353c; 20007 entry-lifetime consumer(s)', 'committed access to target VA 4008000000 carried injected PA 0x8353c000 (carrier events 636,637,638,639, commit events 706,729,762,775)']
- terminal expected by model: True (allowed: ACTIVATED_MASKED, CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, SDC, SQUASHED)

## Oracle evidence

```json
{
  "basis": "target sentinel vs decoy sentinel",
  "context": "R02",
  "golden": 125,
  "line": "W12_RESULT ctx=R02 target_va=0x4008000000 target_pfn=0x83559 decoy_pfn=0x8353c observed=0x51 sentinel=0x7d decoy_sentinel=0x51 branch=0 mode=auto decoy_pfn_arg=0x0 decoy_arg_match=0 pagemap=ok pfn_ok=1/1 result=FAIL",
  "observed": 81,
  "workload_result": "FAIL",
  "wrong": 81
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
