# MMU causal slice — M07/R05

| Field | Value |
|---|---|
| sample_run_id | `M07-F0-W14-S01-R05` |
| run_id | `TEST-F1-M07-R05` |
| model | `M07` |
| context | `R05` |
| workload | `W14` |
| target_va | `0x400d600180` |
| target_mode | `Execute` |
| fault_id | `1` |
| trace_sha256 | `c598b9d08643997f4aa2e8fa8c9a232eceb53909396d81aa326e9de560f5a931` |
| activation_basis | `COTEMPORAL_PERMISSION_EVAL_KEY_MATCH` |
| consumption_basis | `SAME_TRANSACTION_COTEMPORAL_PERMISSION_EVAL_KEY_MATCH permission_eval -> translation_result -> lsu_request` |
| strict_chain_ok | `True` |

## Verdict

| ActivationStatus | `ACTIVATED` |
| FaultConsumptionStatus | `CONSUMED` |
| PropagationStatus | `FULL` |
| TraceCompleteness | `COMPLETE` |
| TerminalState | `SDC` |
| OracleResult | `FAIL` |

## Identity join

- `permission_eval_event` = `331`
- `permission_eval_result` = `deny`
- `permission_eval_tick` = `260385494193`
- `translation_id` = `5`

## Join note

The activation row carries translation_id=0 on the fetch path because the C++ hook runs for an instruction-fetch Request with no instruction sequence number (mmu.cc:742-791; mmuBeginTxn refuses seq==0). The join to translation 5 is a co-temporal key match: the permission_eval at the same tick/cycle, VA, mode, stage, regime and security state records the real deny decision, and that same transaction owns the translation_result and the lsu_request(mode=Execute). It is never inferred from event order.

## Causal chain (logical order)

| Step | EventID | Kind | VA | PA | Translation | Entry | Decision |
|---|---|---|---|---|---|---|---|
| 1 | 331 | permission_eval | 400d600180 |  | 5 | :: | deny |
| 2 | 332 | mmu_fault_activate | 400d600180 |  | 0 | :: |  |
| 3 | 333 | translation_result | 400d600180 | 8353d180 | 5 | :78:377 |  |
| 4 | 334 | lsu_request | 400d600180 | 8353d180 | 5 | :: |  |

## Events present in the raw trace (ascending EventID)

| EventID | Kind |
|---|---|
| 331 | permission_eval |
| 332 | mmu_fault_activate |
| 333 | translation_result |
| 334 | lsu_request |

## Guest oracle

```
W14_INFO ctx=R05 stage=target_computed target=0x400d600180 source=table index=1
W14_INFO ctx=R05 stage=indirect_branch insn=br target=0x400d600180 lr=local_label
W14_INFO ctx=R05 stage=executed marker=0x5a
W14_RESULT ctx=R05 signal=0 phase=fetch_xn_indirect observed=0x5a observed_kind=value si_code=-1 fault_addr=0x0 fault_class=none fault_code_ok=1 pte_present=1 shared_before=0x1122334455667788 shared_after=0x1122334455667788 shared_changed=0 injected_success=1 expected=0x5a value_ok=1 msg=done result=FAIL
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

The exact PROP-EVT lines are in `causal_slice.prop_evt.txt`; every event id above is present in `M07-F0-W14-S01-R05`.
