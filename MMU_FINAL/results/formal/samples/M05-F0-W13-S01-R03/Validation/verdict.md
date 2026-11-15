# Formal MMU Verdict: M05-F0-W13-S01-R03

| Field | Value |
|---|---|
| sample_run_id | M05-F0-W13-S01-R03 |
| model | M05 |
| workload | W13 |
| context | R03 |
| target_va | 275146342400 |
| target_mode | Read |
| fault_id | 1 |
| activation_event_id | 233 |
| consumption_event_id | 236 |
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

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M05-F0-W13-S01-R03/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M05-F0-W13-S01-R03/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M05-F0-W13-S01-R03/Run_Log/board.terminal`
- wrong-value proof: ['L2 partial next-table base 0x81d28000 -> 0x81ce7000; later partial hit event 244; resumed walk read decoy PTE at event 356']
- terminal expected by model: True (allowed: ACTIVATED_MASKED, CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, SDC, SQUASHED)

## Oracle evidence

```json
{
  "basis": "target sentinel vs decoy sentinel",
  "context": "R03",
  "golden": 125,
  "line": "W13_RESULT ctx=R03 target_va=0x4010000000 target_pfn=0x83575 decoy_va=0x4010200000 decoy_pfn=0x83544 alias_va=0x4010001000 observed=0x51 sentinel=0x7d decoy_sentinel=0x51 branch=2 pagemap=ok pfn_ok=1/1 signal=0 fault_phase=none partial_hit=TRACE_CONFIRMED result=FAIL",
  "observed": 81,
  "workload_result": "FAIL",
  "wrong": 81
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
