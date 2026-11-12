# MMU causal slice — M03/R05

| Field | Value |
|---|---|
| sample_run_id | `M03-F0-W11-S01-R05` |
| run_id | `TEST-F1-M03-R05` |
| model | `M03` |
| context | `R05` |
| workload | `W11` |
| target_va | `0x4005000000` |
| target_mode | `Execute` |
| fault_id | `1` |
| trace_sha256 | `2c834f9d84c030979d5fea3185c7e781904ba3718f09c803922f32920aae31b5` |
| activation_basis | `M03_FALSE_HIT_ACTIVATION` |
| consumption_basis | `TLB_ENTRY_IDENTITY_253:51` |
| strict_chain_ok | `True` |

## Verdict

| ActivationStatus | `ACTIVATED` |
| FaultConsumptionStatus | `CONSUMED` |
| PropagationStatus | `FULL` |
| TraceCompleteness | `COMPLETE` |
| TerminalState | `SDC` |
| OracleResult | `FAIL` |

## Identity join

- `candidate_entry` = `(253, 51)`
- `candidate_asid` = `236`
- `requester_asid` = `238`
- `candidate_pa` = `0x83543000`
- `lookup_entry` = `(253, 51)`
- `lookup_id` = `42991437`
- `lookup_asid` = `238`
- `lookup_pa` = `83543000`
- `result_entry` = `(253, 51)`
- `result_pa` = `83543000`

## Join note

The activation names candidate_entry/generation (253, 51) from ASID 236; the fault-tagged tlb_lookup_hit, the later translation_result and the lsu_request(mode=Execute) all carry the same entry identity and the candidate PA. The requester ASID (238) differs from the candidate ASID, so the fetch consumed a foreign-context translation.

## Causal chain (logical order)

| Step | EventID | Kind | VA | PA | Translation | Entry | Decision |
|---|---|---|---|---|---|---|---|
| 1 | 294 | mmu_fault_activate | 4005000000 |  | 6 | l2_shared:: |  |
| 2 | 295 | tlb_lookup_hit | 4005000000 | 83543000 | 6 | l2_shared:253:51 |  |
| 3 | 296 | tlb_entry_insert | 4005000000 |  | 6 | itb:189:688 |  |
| 4 | 297 | permission_eval | 4005000000 |  | 6 | :: | grant |
| 5 | 298 | translation_result | 4005000000 | 83543000 | 6 | :253:51 |  |
| 6 | 299 | lsu_request | 4005000000 | 83543000 | 6 | :: |  |

## Events present in the raw trace (ascending EventID)

| EventID | Kind |
|---|---|
| 294 | mmu_fault_activate |
| 295 | tlb_lookup_hit |
| 296 | tlb_entry_insert |
| 297 | permission_eval |
| 298 | translation_result |
| 299 | lsu_request |

## Guest oracle

```
W11_INFO ctx=R05 stage=parent_a_ready pid=317 va=0x4005000000 handshake=ready_rewarm fork_b=now
W11_INFO ctx=R05 stage=a_ready pid=318 va=0x4005000000 handshake=ready_rewarm initial_warm=1
W11_INFO ctx=R05 stage=b_setup_complete pid=319 va=0x4005000000 handshake=ready_rewarm target_untouched=1
W11_INFO ctx=R05 stage=a_b_ready pid=318 va=0x4005000000 handshake=ready_rewarm b_setup_ok=1
W11_INFO ctx=R05 stage=a_rewarmed pid=318 va=0x4005000000 handshake=ready_rewarm rewarm=64 flush=mprotect
W11_INFO ctx=R05 stage=b_rewarmed pid=319 va=0x4005000000 handshake=ready_rewarm target_access=immediate
W11_INFO ctx=R05 stage=a_released pid=318 va=0x4005000000 handshake=ready_rewarm exit=0
W11_RESULT ctx=R05 va=0x4005000000 pid_a=318 pid_b=319 pfn_a=0x83543 pfn_b=0x83542 pagemap=ok marker_a=0xa5 marker_b=0x5a observed=0xa5 branch=0 stage=0 b_signal=0 asid_source=trace pin_cpu=cpu0 handshake=ready_rewarm expect=0x5a result=FAIL
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

The exact PROP-EVT lines are in `causal_slice.prop_evt.txt`; every event id above is present in `M03-F0-W11-S01-R05`.
