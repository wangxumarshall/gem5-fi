# LSU v3.3.3 — Control Zero Proof Rules (formal)

A control run proves zero injection **only** when the evidence says so. Missing
or unparsable evidence is never interpreted as zero.

## Strict tri-state

`InjectionCount` is classified by `tools/lsu_v333_control_proof.py:
classify_injection_count(value) -> (state, reason)`:

| Input | ControlInjected | Reason |
|---|---|---|
| `None` / column absent | `UNKNOWN` | `MISSING` |
| `""` / whitespace | `UNKNOWN` | `EMPTY` |
| canonical integer `0` (or `+0`/`-0`) | `NO` | `ZERO` |
| positive integer | `YES` | `POSITIVE` |
| negative integer | `INVALID` | `NEGATIVE` |
| `1.0`, `0x0`, `nan`, `abc`, bool, list | `UNKNOWN` | `UNPARSEABLE` |

Ordering matters: missing is checked before empty; only `^[+-]?\d+$` is
accepted; nothing defaults to `0`.

## Separate counters

`InjectionAttemptCount` and `InjectionAppliedCount` are emitted as separate
columns next to `InjectionCount`. A control may attempt injections and apply
zero; both facts remain visible.

## Proof classes (unchanged)

`INJECTOR_ABSENT`, `MOUNTED_BUT_DISABLED`, `MOUNTED_BUT_SUPPRESSED`, and
`CONTROL_PROOF_INCOMPLETE`. A mounted control whose trace cannot corroborate a
zero is not upgraded to PASS. Any observed applied injection `> 0` is `FAIL`.

## Campaign-level rule

If any of the 60 controls yields `UNKNOWN` or `INVALID`, the control-audit
emitter exits nonzero and `04_final_reports.sh` refuses to write a passing
Control Validation. There is no default `NO`.
