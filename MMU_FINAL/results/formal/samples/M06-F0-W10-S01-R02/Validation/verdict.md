# Formal MMU Verdict: M06-F0-W10-S01-R02

| Field | Value |
|---|---|
| sample_run_id | M06-F0-W10-S01-R02 |
| model | M06 |
| workload | W10S |
| context | R02 |
| target_va | 274895732736 |
| target_mode | Write |
| fault_id | 1 |
| activation_event_id | 8517 |
| consumption_event_id | 8518 |
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

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M06-F0-W10-S01-R02/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M06-F0-W10-S01-R02/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M06-F0-W10-S01-R02/Run_Log/board.terminal`
- wrong-value proof: ['L3 descriptor bit0 cleared (0x6000008352cfc3 -> 0x6000008352cfc2) and decoded Invalid; Translation Fault path']
- terminal expected by model: True (allowed: CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, INJECTION_NOT_ACTIVATED, TRACE_INCOMPLETE)

## Oracle evidence

```json
{
  "basis": "W10S store-redirect / write-fault signature",
  "context": "R02",
  "line": "W10S_RESULT mode=cold target_va=0x4001100000 neighbor_va=0x4001300000 neighbor_alias_va=0x4001300000 buffer_va=0x4002000000 pages_requested=4096 max_pages=65536 pages=4096 attempts=1 target_pfn=0x8352c neighbor_pfn=0x8352d pair_xor1=1 stored=0xab target_before=0x7d target_after=0xab neighbor_before=0x51 neighbor_after=0x51 target_observed=0xab neighbor_alias_observed=0x51 store_fault=0 fault_phase=none fault_addr=0x0 pagemap=ok pfn_ok=1/1 pfn_match=1 walk=cold_write warm_iters=0 m08_redirect_signature=0 m06_write_fault_signature=0 selftest_store_fault=0 result=PASS",
  "m06_write_fault_signature": 0,
  "m08_redirect_signature": 0,
  "neighbor_alias_observed": 81,
  "neighbor_before": 81,
  "store_fault": 0,
  "target_before": 125,
  "target_observed": 171,
  "workload_result": "PASS"
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
- M06 is an exception model: no LSU request or normal commit is required; a Translation Fault is the expected terminal.
