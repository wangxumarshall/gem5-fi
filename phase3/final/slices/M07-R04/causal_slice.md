# MMU causal slice — M07/R04

| Field | Value |
|---|---|
| sample_run_id | `M07-F0-W14-S01-R04` |
| run_id | `TEST-F1-M07-R04` |
| model | `M07` |
| context | `R04` |
| workload | `W14` |
| target_va | `0x400d400100` |
| target_mode | `Execute` |
| fault_id | `1` |
| trace_sha256 | `17ea0a97447714e410fa13785b2b8c237d78630a65d52d958c396c60e1c2ec2d` |
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

- `permission_eval_event` = `353`
- `permission_eval_result` = `deny`
- `permission_eval_tick` = `260302309128`
- `translation_id` = `7`

## Join note

The activation row carries translation_id=0 on the fetch path because the C++ hook runs for an instruction-fetch Request with no instruction sequence number (mmu.cc:742-791; mmuBeginTxn refuses seq==0). The join to translation 7 is a co-temporal key match: the permission_eval at the same tick/cycle, VA, mode, stage, regime and security state records the real deny decision, and that same transaction owns the translation_result and the lsu_request(mode=Execute). It is never inferred from event order.

## Causal chain (logical order)

| Step | EventID | Kind | VA | PA | Translation | Entry | Decision |
|---|---|---|---|---|---|---|---|
| 1 | 353 | permission_eval | 400d400100 |  | 7 | :: | deny |
| 2 | 354 | mmu_fault_activate | 400d400100 |  | 0 | :: |  |
| 3 | 355 | translation_result | 400d400100 | 8353d100 | 7 | :946:20 |  |
| 4 | 356 | lsu_request | 400d400100 | 8353d100 | 7 | :: |  |

## Events present in the raw trace (ascending EventID)

| EventID | Kind |
|---|---|
| 353 | permission_eval |
| 354 | mmu_fault_activate |
| 355 | translation_result |
| 356 | lsu_request |

## Guest oracle

```
W14_RESULT ctx=R04 signal=0 phase=exec_xn observed=0xc7 observed_kind=value si_code=-1 fault_addr=0x0 fault_class=none fault_code_ok=1 pte_present=1 shared_before=0x1122334455667788 shared_after=0x1122334455667788 shared_changed=0 injected_success=1 expected=0xc7 value_ok=1 msg=done result=FAIL
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

The exact PROP-EVT lines are in `causal_slice.prop_evt.txt`; every event id above is present in `M07-F0-W14-S01-R04`.
