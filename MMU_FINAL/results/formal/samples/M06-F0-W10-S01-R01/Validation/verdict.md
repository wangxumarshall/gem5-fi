# Formal MMU Verdict: M06-F0-W10-S01-R01

| Field | Value |
|---|---|
| sample_run_id | M06-F0-W10-S01-R01 |
| model | M06 |
| workload | W10 |
| context | R01 |
| target_va | 274894684160 |
| target_mode | Read |
| fault_id | 1 |
| activation_event_id | 4422 |
| consumption_event_id | 4423 |
| ActivationStatus | ACTIVATED |
| FaultConsumptionStatus | CONSUMED |
| PropagationStatus | FULL |
| TraceCompleteness | COMPLETE |
| TerminalState | DETECTED_CONTAINED |
| OracleResult | PASS_EXPECTED_DETECTION |
| RecordIntegrity | PASS |

## Missing causal edges / kinds

- none

## Evidence

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M06-F0-W10-S01-R01/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M06-F0-W10-S01-R01/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M06-F0-W10-S01-R01/Run_Log/board.terminal`
- wrong-value proof: ['L3 descriptor bit0 cleared (0x600000834b2fc3 -> 0x600000834b2fc2) and decoded Invalid; Translation Fault path']
- terminal expected by model: True (allowed: CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, INJECTION_NOT_ACTIVATED, TRACE_INCOMPLETE)

## Oracle evidence

```json
{
  "basis": "W10 target sentinel vs neighbor sentinel",
  "context": "R01",
  "golden": 99,
  "line": "W10_RESULT ctx=R01 pages=4096 alias=0x4002000000 target=0x4001000000 target_pfn=0x834b2 neighbor_pfn=0x834b3 pa=0x834b2000 pa_neigh=0x834b3000 new_pfn_xor1=0x834b3 pte_present=1 pfn_match=1 page_size=KernelPageSize:        4 kB,MMUPageSize:           4 kB sentinel=0x63 neighbor_sentinel=0x60 observed=0x63 branch=0 vec0=0x00 result=PASS",
  "observed": 99,
  "workload_result": "PASS",
  "wrong": 96
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
- M06 is an exception model: no LSU request or normal commit is required; a Translation Fault is the expected terminal.
