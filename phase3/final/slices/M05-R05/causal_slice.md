# MMU causal slice — M05/R05

| Field | Value |
|---|---|
| sample_run_id | `M05-F0-W13-S01-R05` |
| run_id | `TEST-F1-M05-R05` |
| model | `M05` |
| context | `R05` |
| workload | `W13` |
| target_va | `0x4010000000` |
| target_mode | `Execute` |
| fault_id | `1` |
| trace_sha256 | `50755bafa235f7c28aba00b7067e08378543e3318783a16cd0de20d78baafc9f` |
| activation_basis | `M05_PARTIAL_TABLE_ENTRY_CORRUPTION` |
| consumption_basis | `PARTIAL_ENTRY_LIFETIME insert=230 consume=245 lookup=244` |
| strict_chain_ok | `True` |

## Verdict

| ActivationStatus | `ACTIVATED` |
| FaultConsumptionStatus | `CONSUMED` |
| PropagationStatus | `FULL` |
| TraceCompleteness | `COMPLETE` |
| TerminalState | `SDC` |
| OracleResult | `FAIL` |

## Identity join

- `faulted_insert` = `230`
- `consumer_event` = `245`
- `consumed_entry` = `(699, 52)`
- `lookup_event` = `244`
- `translation_id` = `3`
- `corrupted_base_before` = `0x81d28000`
- `corrupted_base_after` = `0x81ce7000`

## Join note

The faulted partial_entry_insert is the source_event_id of fault_entry_consume; the consume row names the real partial tlb_lookup_hit and its entry identity, and the resumed PTW, the wrong leaf, the translation_result and the lsu_request(mode=Execute) share that transaction id. The consumer is the +0x1000 alias page that must resume from the corrupted L2 partial entry.

## Causal chain (logical order)

| Step | EventID | Kind | VA | PA | Translation | Entry | Decision |
|---|---|---|---|---|---|---|---|
| 1 | 229 | mmu_fault_activate | 4010000000 |  | 2 | :: |  |
| 2 | 230 | partial_entry_insert | 4010000000 |  | 2 | :: |  |
| 3 | 244 | tlb_lookup_hit | 4010001000 | 1039ce00000000 | 3 | l2_shared:699:52 |  |
| 4 | 245 | fault_entry_consume | 4010001000 |  |  | l2_shared:699:52 |  |
| 5 | 246 | ptw_start | 4010001000 |  | 3 | :: |  |
| 6 | 247 | pte_read | 4010001000 |  | 3 | :: |  |
| 7 | 250 | pte_decode | 4010001000 |  | 3 | :: |  |
| 8 | 251 | tlb_fill | 4010001000 |  | 3 | :: |  |
| 9 | 252 | tlb_entry_insert | 4010001000 |  | 3 | itb:94:830 |  |
| 10 | 254 | permission_eval | 4010001000 |  | 3 | :: | grant |
| 11 | 255 | translation_result | 4010001000 | 83544000 | 3 | :94:830 |  |
| 12 | 256 | lsu_request | 4010001000 | 83544000 | 3 | :: |  |

## Events present in the raw trace (ascending EventID)

| EventID | Kind |
|---|---|
| 229 | mmu_fault_activate |
| 230 | partial_entry_insert |
| 244 | tlb_lookup_hit |
| 245 | fault_entry_consume |
| 246 | ptw_start |
| 247 | pte_read |
| 250 | pte_decode |
| 251 | tlb_fill |
| 252 | tlb_entry_insert |
| 254 | permission_eval |
| 255 | translation_result |
| 256 | lsu_request |

## Guest oracle

```
W13_INFO ctx=R05 phase=start pid=317 target_va=0x4010000000 decoy_va=0x4010200000 target_pfn=0x83575 decoy_pfn=0x83544 decoy_first=1 watchdog=post_warm watchdog_sec=120
W13_LIMITATION ctx=R05 EL0 cannot issue TLBI VALE1IS. The M05 consumer is the fresh +0x1000 alias page accessed BEFORE the guest maintenance: it has a populated PTE but no complete TLB entry, so it must resume from the L2 partial walk-cache entry. The RESULT line reports that alias observation; the partial-hit lineage is confirmed from the gem5 TLB trace.
W13_RESULT ctx=R05 target_va=0x4010000000 target_pfn=0x83575 decoy_va=0x4010200000 decoy_pfn=0x83544 alias_va=0x4010001000 observed=0x51 sentinel=0x7d decoy_sentinel=0x51 branch=0 pagemap=ok pfn_ok=1/1 signal=0 fault_phase=none partial_hit=TRACE_CONFIRMED result=FAIL
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

The exact PROP-EVT lines are in `causal_slice.prop_evt.txt`; every event id above is present in `M05-F0-W13-S01-R05`.
