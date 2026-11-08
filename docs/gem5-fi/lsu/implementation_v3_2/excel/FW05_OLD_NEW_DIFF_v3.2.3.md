# FW05 old/new configuration diff (v3.2.2 → v3.2.3)

| Field | v3.2.2 | v3.2.3 | Reason |
|---|---|---|---|
| WorkloadName | W8 alignment | fw05_forward | Original W8 alignment cannot reliably trigger the target forwarding fault; the new workload was validated by five pilots. |
| WorkloadPath | `workloads/alignment` | `workloads/fw05_forward` | Same. |
| BinarySHA256 (workload SHA) | `89ff937a...` (alignment) | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` | Archive binary SHA, identical to all five v3.2.7 pilot manifests. |
| Oracle | `3f89eab79392ce69` (alignment) | `67afad307642983e` | fw05_forward golden; host and gem5 agree. |
| TargetFunction | `CHAOSLSQFwd::maybeSubstituteSource` (old hook name in the text) | `LSQUnit::read` / `CHAOSLSQFwd::maybeSubstituteFW05` | Actual v3.2.7 hook. |
| TargetField | `store_it._idx / alt_src` | true_src vs alt_src store data | Wrong-source selection, not multi-store splicing. |
| NormalValue | true_src = youngest matching store | true_src=youngest matching store | Unchanged semantics. |
| FaultValue | copy alt_src=older store data | alt_src=older full-cover store | Eligibility is now strict (full cover, different bytes). |
| FaultAction | (implicit copy) | SUBSTITUTE_ONE_WRONG_SOURCE | Names the action; no data splice. |
| PilotStatus | NOT_RUN | PILOT_RUN_ACCEPTED; R01 SQUASHED, R02–R05 SDC | Five actual pilots. |

## History retained

- The v3.2.2 workbook, its W8 alignment rows and the five v3.2.7 pilots/traces
  are untouched.
- The v3.2.7 pilots used a pilot-only `fw05_forward` override; v3.2.3 makes
  that workload the formal one, so no override is needed for future runs.
- The model is wrong-source selection only. It is **not** a multi-store
  partial-data splice, and must not be described as one.
