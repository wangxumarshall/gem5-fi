# M07 Permission Grant Inversion - Terminal Semantics Audit

Sources: `sample_manifest.json`, `Validation/verdict.json`, the frozen `analysis/propagation_chains/M07-*.json` (event IDs verified against the raw `prop_evt.txt.gz`; zero join mismatches), the faulted `Run_Log/observed_output.txt` and the independent `TEST-F1-CTRL2-W14-R0x` control transcripts.

## Per-sample evidence

| Ctx | Mode | Phase | Faulted signal | Observed | Expected | value_ok | shared_changed | Control | Permission eval | Manifestation |
|---|---|---|---|---|---|---|---|---|---|---|
| R01 | Write | store_ro | 0 | 0x11223344556677c1 | 0x11223344556677c1 | 1 | 1 | signal=11 permission | deny (joined 343) | **UNAUTHORIZED_WRITE** |
| R02 | Atomic | atomic_rmw_ro | 0 | 0x1122334455667789 | 0x1122334455667789 | 1 | 1 | signal=11 permission | none joined; nearest 345/tid5 | **UNAUTHORIZED_WRITE** |
| R03 | Read | read_exec_only | 0 | 0x88 | 0x88 | 1 | 0 | signal=11 permission | deny (joined 332) | **UNAUTHORIZED_READ** |
| R04 | Execute | exec_xn | 0 | 0xc7 | 0xc7 | 1 | 0 | signal=11 permission | deny (joined 353) | **UNAUTHORIZED_EXECUTION** |
| R05 | Execute | fetch_xn_indirect | 0 | 0x5a | 0x5a | 1 | 0 | signal=11 permission | deny (joined 331) | **UNAUTHORIZED_EXECUTION** |

## Event-level proof

- **R01**: `permission_eval` deny event(s) 343 -> `mmu_fault_activate` 344 (permission_before=false, permission_after=true, fault_site=mmu_checkPermissions64) -> `translation_result` 345 at PA 8353d000 -> `lsu_request` 346 (mode=Write). StrictChain ok=None, join basis=direct activation/translation id.
- **R02**: `permission_eval` deny event(s) none joined (nearest 345/tid5) -> `mmu_fault_activate` 350 (permission_before=false, permission_after=true, fault_site=mmu_checkPermissions64) -> `translation_result` 351 at PA 8353d000 -> `lsu_request` 352 (mode=Write). StrictChain ok=None, join basis=direct activation/translation id.
  *Note*: no permission_eval is joined to the activation translation_id=7; nearest same-VA deny is event 345 (translation_id=5, mode=Write, tick delta -2331), which the frozen validator does not associate; the activation records permission_before=false and the control shows SIGSEGV permission fault.
- **R03**: `permission_eval` deny event(s) 332 -> `mmu_fault_activate` 333 (permission_before=false, permission_after=true, fault_site=mmu_checkPermissions64) -> `translation_result` 334 at PA 8353d000 -> `lsu_request` 335 (mode=Read). StrictChain ok=None, join basis=direct activation/translation id.
- **R04**: `permission_eval` deny event(s) 353 -> `mmu_fault_activate` 354 (permission_before=false, permission_after=true, fault_site=mmu_checkPermissions64) -> `translation_result` 355 at PA 8353d100 -> `lsu_request` 356 (mode=Execute). StrictChain ok=True, join basis=COTEMPORAL_PERMISSION_EVAL_KEY_MATCH.
- **R05**: `permission_eval` deny event(s) 331 -> `mmu_fault_activate` 332 (permission_before=false, permission_after=true, fault_site=mmu_checkPermissions64) -> `translation_result` 333 at PA 8353d180 -> `lsu_request` 334 (mode=Execute). StrictChain ok=True, join basis=COTEMPORAL_PERMISSION_EVAL_KEY_MATCH.

## Classification

* **R01, R02 = UNAUTHORIZED_WRITE** (+ PERMISSION_BYPASS, + DATA_INTEGRITY_SIDE_EFFECT). The store/atomic on a read-only page completes with no exception and mutates the shared page (`shared_changed=1`); the independent control receives SIGSEGV + permission fault and leaves it unchanged.
* **R03 = UNAUTHORIZED_READ** (+ PERMISSION_BYPASS). EL0 reads the PAGE_EXECONLY page (`observed=0x88`, `value_ok=1`); the control faults with SIGSEGV + permission fault.
* **R04, R05 = UNAUTHORIZED_EXECUTION** (+ PERMISSION_BYPASS). Code is fetched/executed from an XN mapping and the marker is returned (0xc7 / 0x5a); the control faults with SIGSEGV + permission fault. R05 is an indirect-branch fetch (`stage=indirect_branch insn=br` then `stage=executed marker=0x5a`).

## OracleResult=FAIL is not the manifestation

In every M07 sample `value_ok=1` and `injected_success=1`; the observed value equals the expected value. There is **no WRONG_DATA_VALUE** in M07. `OracleResult=FAIL` means the workload detected that an operation which must be denied instead succeeded. `PermissionPolicyViolation=true` in all five; `ArchitecturalStateCorruption` applies only as the memory-mutation side effect of R01/R02, not as the primary label. The original `TerminalState=SDC` is preserved; `ManifestationType` is an added diagnostic dimension, not an overwrite.

## Evidence limitation (R04/R05)

The instruction-fetch activation row carries `translation_id=0` and `dyn_inst_seq=0` because the C++ hook runs for a fetch Request with no sequence number. The formal `Details.observed_kinds` therefore lists only activation/summary/permission_eval for R04/R05; the downstream `translation_result` and `lsu_request` carry `fault_id=0`. The frozen strict chain supplies a co-temporal join (`exact_key_match_count=1`, `exact_key_deny_match_count=1`, `execute_request_match_count=1`); the join is never inferred from event order. This is a method limitation, not a missing propagation.

## SDC semantic audit (all 31 samples)

| Sample | Model | Terminal | Value mismatch | Permission bypass | Manifestation | Audit |
|---|---|---|---|---|---|---|
| M01-F0-W9-S01-R01 | M01 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M01-F0-W9-S01-R02 | M01 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M01-F0-W9-S01-R03 | M01 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M01-F0-W9-S01-R04 | M01 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M01-F0-W9-S01-R05 | M01 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M02-F0-W10-S01-R01 | M02 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M02-F0-W10-S01-R02 | M02 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M02-F0-W10-S01-R03 | M02 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M02-F0-W10-S01-R04 | M02 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M02-F0-W10-S01-R05 | M02 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M03-F0-W11-S01-R05 | M03 | SDC | True | False | WRONG_CODE_PAGE_EXECUTION | CONFIRMED_SDC |
| M04-F0-W12-S01-R01 | M04 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M04-F0-W12-S01-R02 | M04 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M04-F0-W12-S01-R03 | M04 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M04-F0-W12-S01-R04 | M04 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M04-F0-W12-S01-R05 | M04 | SDC | True | False | WRONG_CODE_PAGE_EXECUTION | CONFIRMED_SDC |
| M05-F0-W13-S01-R01 | M05 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M05-F0-W13-S01-R02 | M05 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M05-F0-W13-S01-R03 | M05 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M05-F0-W13-S01-R04 | M05 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M05-F0-W13-S01-R05 | M05 | SDC | True | False | WRONG_CODE_PAGE_EXECUTION | CONFIRMED_SDC |
| M07-F0-W14-S01-R01 | M07 | SDC | False | True | UNAUTHORIZED_WRITE | CONFIRMED_SDC |
| M07-F0-W14-S01-R02 | M07 | SDC | False | True | UNAUTHORIZED_WRITE | CONFIRMED_SDC |
| M07-F0-W14-S01-R03 | M07 | SDC | False | True | UNAUTHORIZED_READ | CONFIRMED_SDC |
| M07-F0-W14-S01-R04 | M07 | SDC | False | True | UNAUTHORIZED_EXECUTION | CONFIRMED_SDC |
| M07-F0-W14-S01-R05 | M07 | SDC | False | True | UNAUTHORIZED_EXECUTION | CONFIRMED_SDC |
| M08-F0-W10-S01-R01 | M08 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M08-F0-W10-S01-R02 | M08 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M08-F0-W10-S01-R03 | M08 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M08-F0-W10-S01-R04 | M08 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |
| M08-F0-W10-S01-R05 | M08 | SDC | True | False | WRONG_DATA_VALUE | CONFIRMED_SDC |

**31 SDC samples audited**: {'CONFIRMED_SDC': 31}. Primary manifestation distribution: {'WRONG_DATA_VALUE': 23, 'WRONG_CODE_PAGE_EXECUTION': 3, 'UNAUTHORIZED_WRITE': 2, 'UNAUTHORIZED_READ': 1, 'UNAUTHORIZED_EXECUTION': 2}.

No sample was reclassified as a different TerminalState. The audit confirms each SDC by a software-visible oracle difference (wrong data value or permission-policy bypass), a control difference, trace completeness and `wrong_value_proven`. OracleResult=FAIL alone was never used as the criterion.
