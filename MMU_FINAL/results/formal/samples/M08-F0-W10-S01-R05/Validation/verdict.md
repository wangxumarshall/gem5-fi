# Formal MMU Verdict: M08-F0-W10-S01-R05

| Field | Value |
|---|---|
| sample_run_id | M08-F0-W10-S01-R05 |
| model | M08 |
| workload | W10S |
| context | R05 |
| target_va | 274898878464 |
| target_mode | Write |
| fault_id | 1 |
| activation_event_id | 8630 |
| consumption_event_id | 8631 |
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

- trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M08-F0-W10-S01-R05/Trace/prop_evt.txt.gz`
- golden: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M08-F0-W10-S01-R05/Run_Log/observed_output.txt`
- terminal: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M08-F0-W10-S01-R05/Run_Log/board.terminal`
- wrong-value proof: ['request PA 0x8352c000 -> 0x8352d000 with TLB pfn unchanged (0x8352c); consumer 8631 carries new PA']
- terminal expected by model: True (allowed: ACTIVATED_MASKED, ARCH_STATE_CORRUPTION, CRASH, HANG/TIMEOUT, SDC, SQUASHED)

## Oracle evidence

```json
{
  "basis": "W10S store-redirect / write-fault signature",
  "context": "R05",
  "line": "W10S_RESULT mode=warm target_va=0x4001400000 neighbor_va=0x4001600000 neighbor_alias_va=0x4001600000 buffer_va=0x4002000000 pages_requested=4096 max_pages=65536 pages=4096 attempts=1 target_pfn=0x8352c neighbor_pfn=0x8352d pair_xor1=1 stored=0xab target_before=0x7d target_after=0x7d neighbor_before=0x51 neighbor_after=0xab target_observed=0x7d neighbor_alias_observed=0xab store_fault=0 fault_phase=none fault_addr=0x0 pagemap=ok pfn_ok=1/1 pfn_match=1 walk=warm_hit warm_iters=128 m08_redirect_signature=1 m06_write_fault_signature=0 selftest_store_fault=0 result=FAIL",
  "m06_write_fault_signature": 0,
  "m08_redirect_signature": 1,
  "neighbor_alias_observed": 171,
  "neighbor_before": 81,
  "store_fault": 0,
  "target_before": 125,
  "target_observed": 125,
  "workload_result": "FAIL"
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
