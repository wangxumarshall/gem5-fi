# MMU causal slice — M04/R05

| Field | Value |
|---|---|
| sample_run_id | `M04-F0-W12-S01-R05` |
| run_id | `TEST-F1-M04-R05` |
| model | `M04` |
| context | `R05` |
| workload | `W12` |
| target_va | `0x4008000000` |
| target_mode | `Execute` |
| fault_id | `1` |
| trace_sha256 | `b0571f235d1b67f79e943279fc74198f7ee748871e0fff37387d027b026d8316` |
| activation_basis | `M04_ENTRY_PFN_SUBSTITUTION` |
| consumption_basis | `ENTRY_LIFETIME_ITB_173:540 consumed by translation_result and lsu_request` |
| strict_chain_ok | `True` |

## Verdict

| ActivationStatus | `ACTIVATED` |
| FaultConsumptionStatus | `CONSUMED` |
| PropagationStatus | `FULL` |
| TraceCompleteness | `COMPLETE` |
| TerminalState | `SDC` |
| OracleResult | `FAIL` |

## Identity join

- `mutated_entry` = `(173, 540)`
- `mutated_instance` = `itb`
- `old_pa` = `0x83559000`
- `new_pa` = `0x8353c000`
- `lineage_event` = `482`
- `lineage_state` = `alias_mutated`
- `consumer_entry` = `(173, 540)`
- `consumer_pa` = `8353c000`
- `consumer_translation_id` = `16`

## Join note

The activation mutates resident entry (instance=itb, entry=173, generation=540) and records old_pa=0x83559000 -> new_pa=0x8353c000. The later translation_result names the SAME entry identity and emits new_pa; the lsu_request(mode=Execute) carries that PA. The C++ fault_entry_consume counter is 0 for this synthetic IFU transaction, so the proof is the entry lifetime identity, not the counter.

## Causal chain (logical order)

| Step | EventID | Kind | VA | PA | Translation | Entry | Decision |
|---|---|---|---|---|---|---|---|
| 1 | 481 | mmu_fault_activate | 4008000000 |  | 0 | itb:173:540 |  |
| 2 | 482 | tlb_entry_lineage | 0x4008000000 |  |  | l2_shared:652:25 |  |
| 3 | 484 | translation_result | 4008000000 | 8353c000 | 16 | :173:540 |  |
| 4 | 485 | lsu_request | 4008000000 | 8353c000 | 16 | :: |  |

## Events present in the raw trace (ascending EventID)

| EventID | Kind |
|---|---|
| 481 | mmu_fault_activate |
| 482 | tlb_entry_lineage |
| 484 | translation_result |
| 485 | lsu_request |

## Guest oracle

```
W12_RESULT ctx=R05 target_va=0x4008000000 target_pfn=0x83559 decoy_pfn=0x8353c observed=0x51 sentinel=0x7d decoy_sentinel=0x51 branch=0 mode=auto decoy_pfn_arg=0x0 decoy_arg_match=0 pagemap=ok pfn_ok=1/1 result=FAIL
```

## Instrumentation boundary (honest)

- `ifu_fetch_request_event`: lsu_request(mode=Execute)
- `ifu_fetch_response`: NOT_EMITTED_BY_FROZEN_BINARY
- `per_instruction_decode_execute`: NOT_EMITTED_BY_FROZEN_BINARY
- `per_instruction_commit_for_synthetic_ifu`: NOT_EMITTED
- `execution_terminal_evidence`: guest oracle marker tied to the fetched PA/code page
- `binary_sha256`: b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185

## Missing kinds / guards

- missing_kinds: `[]`
- guards: `[]`

The exact PROP-EVT lines are in `causal_slice.prop_evt.txt`; every event id above is present in `M04-F0-W12-S01-R05`.
