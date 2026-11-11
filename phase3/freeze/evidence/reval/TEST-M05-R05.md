# Formal MMU Verdict: TEST-M05-R05

| Field | Value |
|---|---|
| sample_run_id |  |
| model | M05 |
| workload | W13 |
| context | R05 |
| target_va | 275146342400 |
| target_mode | Execute |
| fault_id | 1 |
| activation_event_id | 194 |
| consumption_event_id | 0 |
| ActivationStatus | ACTIVATED |
| FaultConsumptionStatus | NOT_CONSUMED |
| PropagationStatus | PARTIAL |
| TraceCompleteness | PARTIAL |
| TerminalState | TRACE_INCOMPLETE |
| OracleResult | PASS |
| RecordIntegrity | PASS |

## Missing causal edges / kinds

- `missing_kind:commit`
- `missing_kind:lsu_request`
- `missing_kind:memory_response`
- `missing_kind:partial_entry_insert`
- `missing_kind:translation_result`

## Evidence

- trace: `runs/TEST-M05-R05/Trace/prop_evt.txt.gz`
- golden: `runs/TEST-M05-R05/Run_Log/observed_output.txt`
- terminal: `runs/TEST-M05-R05/Run_Log/board.terminal`
- wrong-value proof: ['corrupted partial base 0x81c1f000 had no later partial hit; a level-2 partial entry was invalidated at event 203 (guest containment)']
- terminal expected by model: False (allowed: ACTIVATED_MASKED, CRASH, DETECTED_CONTAINED, HANG/TIMEOUT, SDC, SQUASHED)

## Oracle evidence

```json
{
  "basis": "target sentinel vs decoy sentinel",
  "context": "R05",
  "golden": 125,
  "line": "W13_RESULT ctx=R05 target_va=0x4010000000 target_pfn=0x83546 decoy_va=0x4010200000 decoy_pfn=0x83545 observed=0x7d sentinel=0x7d decoy_sentinel=0x51 branch=0 pagemap=ok pfn_ok=1/1 signal=0 fault_phase=none partial_hit=UNVERIFIED result=PASS",
  "observed": 125,
  "workload_result": "PASS",
  "wrong": 81
}
```

## Interpretation rules

- COMPLETE requires all model-required kinds, real ParentEventID edges, record integrity and a terminal.
- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is deleted and unrelated events are never merged.
