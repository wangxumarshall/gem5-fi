# Formal MMU Verdict: TEST-M08-R03

| Field | Value |
|---|---|
| sample_run_id |  |
| model | M08 |
| workload | W10 |
| context | R03 |
| target_va | 274896781312 |
| target_mode | Read |
| fault_id | 1 |
| activation_event_id | 4421 |
| consumption_event_id | 4422 |
| ActivationStatus | ACTIVATED |
| FaultConsumptionStatus | CONSUMED |
| PropagationStatus | PARTIAL |
| TraceCompleteness | PARTIAL |
| TerminalState | TRACE_INCOMPLETE |
| OracleResult | PASS |
| RecordIntegrity | PASS |

## Missing causal edges / kinds

- `missing_kind:commit`
- `missing_kind:memory_response`
- `missing_kind:rf_writeback`

## Evidence

- trace: `runs/TEST-M08-R03/Trace/prop_evt.txt.gz`
- golden: `runs/TEST-M08-R03/Run_Log/golden_output.txt`
- terminal: `runs/TEST-M08-R03/Run_Log/board.terminal`
- wrong-value proof: ['request PA 0x83480000 -> 0x83481000 with TLB pfn unchanged (0x83480); consumer 4422 carries new PA']
- terminal expected by model: False (allowed: ACTIVATED_MASKED, ARCH_STATE_CORRUPTION, CRASH, HANG/TIMEOUT, SDC, SQUASHED)

## Oracle evidence

```json
{
  "basis": "W10 target sentinel vs neighbor sentinel",
  "context": "R03",
  "golden": 125,
  "line": "W10_RESULT ctx=R03 pages=4096 alias=0x4002000000 target=0x4001200000 target_pfn=0x83480 neighbor_pfn=0x83481 pa=0x83480000 pa_neigh=0x83481000 new_pfn_xor1=0x83481 pte_present=1 pfn_match=1 page_size=KernelPageSize:        4 kB,MMUPageSize:           4 kB sentinel=0x7d neighbor_sentinel=0x51 observed=0x7d branch=1 vec0=0x00 result=PASS",
  "observed": 125,
  "workload_result": "PASS",
  "wrong": 81
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
