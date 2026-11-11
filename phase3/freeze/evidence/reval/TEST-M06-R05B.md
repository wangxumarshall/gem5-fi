# Formal MMU Verdict: TEST-M06-R05B

| Field | Value |
|---|---|
| sample_run_id |  |
| model | M06 |
| workload | W10 |
| context | R05 |
| target_va | 274898878464 |
| target_mode | Read |
| fault_id | 1 |
| activation_event_id | 4511 |
| consumption_event_id | 4512 |
| ActivationStatus | ACTIVATED |
| FaultConsumptionStatus | CONSUMED |
| PropagationStatus | PARTIAL |
| TraceCompleteness | COMPLETE |
| TerminalState | DETECTED_CONTAINED |
| OracleResult | PASS_EXPECTED_DETECTION |
| RecordIntegrity | PASS |

## Missing causal edges / kinds

- none

## Evidence

- trace: `runs/TEST-M06-R05B/Trace/prop_evt.txt.gz`
- golden: `runs/TEST-M06-R05B/Run_Log/golden_output.txt`
- terminal: `runs/TEST-M06-R05B/Run_Log/board.terminal`
- wrong-value proof: ['L3 descriptor bit0 cleared (0x60000083480fc3 -> 0x60000083480fc2) and decoded Invalid; Translation Fault path']
- terminal expected by model: True (allowed: CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, INJECTION_NOT_ACTIVATED, TRACE_INCOMPLETE)

## Oracle evidence

```json
{
  "basis": "W10 target sentinel vs neighbor sentinel",
  "context": "R05",
  "golden": 125,
  "line": "W10_RESULT ctx=R05 pages=4096 alias=0x4002000000 target=0x4001400000 target_pfn=0x83480 neighbor_pfn=0x83481 pa=0x83480000 pa_neigh=0x83481000 new_pfn_xor1=0x83481 pte_present=1 pfn_match=1 page_size=KernelPageSize:        4 kB,MMUPageSize:           4 kB sentinel=0x7d neighbor_sentinel=0x51 observed=0x7d branch=0 vec0=0x7e result=PASS",
  "observed": 125,
  "workload_result": "PASS",
  "wrong": 81
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
- M06 is an exception model: no LSU request or normal commit is required; a Translation Fault is the expected terminal.
