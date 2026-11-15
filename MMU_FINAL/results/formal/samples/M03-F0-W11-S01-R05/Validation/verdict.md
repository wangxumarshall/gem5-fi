# Formal MMU Verdict: M03-F0-W11-S01-R05

| Field | Value |
|---|---|
| sample_run_id | M03-F0-W11-S01-R05 |
| model | M03 |
| workload | W11 |
| context | R05 |
| target_va | 274961793024 |
| target_mode | Execute |
| fault_id | 1 |
| activation_event_id | 294 |
| consumption_event_id | 299 |
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

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M03-F0-W11-S01-R05/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M03-F0-W11-S01-R05/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M03-F0-W11-S01-R05/Run_Log/board.terminal`
- wrong-value proof: ['real candidate entry 253 with ASID 236 != requester ASID 238']
- terminal expected by model: True (allowed: ACTIVATED_MASKED, CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, SDC, SQUASHED)

## Oracle evidence

```json
{
  "basis": "W11 process-B marker vs process-A marker",
  "context": "R05",
  "golden": 90,
  "line": "W11_RESULT ctx=R05 va=0x4005000000 pid_a=318 pid_b=319 pfn_a=0x83543 pfn_b=0x83542 pagemap=ok marker_a=0xa5 marker_b=0x5a observed=0xa5 branch=0 stage=0 b_signal=0 asid_source=trace pin_cpu=cpu0 handshake=ready_rewarm expect=0x5a result=FAIL",
  "observed": 165,
  "workload_result": "FAIL",
  "wrong": 165
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
