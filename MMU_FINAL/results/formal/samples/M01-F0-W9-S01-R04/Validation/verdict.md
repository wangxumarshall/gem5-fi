# Formal MMU Verdict: M01-F0-W9-S01-R04

| Field | Value |
|---|---|
| sample_run_id | M01-F0-W9-S01-R04 |
| model | M01 |
| workload | W9 |
| context | R04 |
| target_va | 274877906944 |
| target_mode | Read |
| fault_id | 1 |
| activation_event_id | 1100 |
| consumption_event_id | 1109 |
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

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M01-F0-W9-S01-R04/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M01-F0-W9-S01-R04/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M01-F0-W9-S01-R04/Run_Log/board.terminal`
- wrong-value proof: ['l2_shared entry 946:24 survived 2 matching TLBI(s), was consumed by lookup event 1109, then disarmed']
- terminal expected by model: True (allowed: ACTIVATED_MASKED, CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, SDC, SQUASHED)

## Oracle evidence

```json
{
  "basis": "W9 PA2 marker vs PA1 stale marker",
  "context": "R04",
  "golden": 85,
  "line": "W9_RESULT ctx=R04 va=0x4000000000 pa1=0x83466000 pa2=0x8346e000 pte_present=1/1 pagemap=ok old_marker=0xaa new_marker=0x55 observed=0xaa old_alias=0xaa branch=0 vec0=0x00 result=FAIL",
  "observed": 170,
  "workload_result": "FAIL",
  "wrong": 170
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
