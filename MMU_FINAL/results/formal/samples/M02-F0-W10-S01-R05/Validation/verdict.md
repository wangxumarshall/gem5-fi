# Formal MMU Verdict: M02-F0-W10-S01-R05

| Field | Value |
|---|---|
| sample_run_id | M02-F0-W10-S01-R05 |
| model | M02 |
| workload | W10 |
| context | R05 |
| target_va | 274898878464 |
| target_mode | Read |
| fault_id | 1 |
| activation_event_id | 4442 |
| consumption_event_id | 4445 |
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

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M02-F0-W10-S01-R05/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M02-F0-W10-S01-R05/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M02-F0-W10-S01-R05/Run_Log/board.terminal`
- wrong-value proof: ['M02 faulted insert dtb:72:14240 consumed by lookup 4445', 'M02 faulted insert dtb:72:14240 consumed by lookup 4451']
- terminal expected by model: True (allowed: ACTIVATED_MASKED, CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, SDC, SQUASHED)

## Oracle evidence

```json
{
  "basis": "W10 target sentinel vs neighbor sentinel",
  "context": "R05",
  "golden": 99,
  "line": "W10_RESULT ctx=R05 pages=4096 alias=0x4002000000 target=0x4001400000 target_pfn=0x834b2 neighbor_pfn=0x834b3 pa=0x834b2000 pa_neigh=0x834b3000 new_pfn_xor1=0x834b3 pte_present=1 pfn_match=1 page_size=KernelPageSize:        4 kB,MMUPageSize:           4 kB sentinel=0x63 neighbor_sentinel=0x60 observed=0x60 branch=0 vec0=0x61 result=FAIL",
  "observed": 96,
  "workload_result": "FAIL",
  "wrong": 96
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
