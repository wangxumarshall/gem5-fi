# Control Sharing and Zero-Injection Audit
Sources: `fault_control_pairs.csv`, each sample `Validation/verdict.json` (`Details.control_oracle`), each control `Config/config.ini` and `Run_Log/command.txt`, `analysis/control_zero_proof.json`.
## Result
| Check | Result |
|---|---|
| Fault->control references | 40 |
| Distinct referenced oracles | 28 |
| Oracle SHA256 match | 40/40 |
| Zero-injection proven | 28/28 oracles |
| Workload compatible | 40/40 |
| Context compatible | 40/40 |
| Row-level PASS | 40/40 |

## Why 40 samples use 28 controls

The counting units differ: 40 fault samples reference 28 distinct oracle files; 34 `TEST-F1-CTRL*` run directories exist, of which 6 are duplicate/superseded copies not referenced by this campaign. A shared control is one independent execution whose per-context oracle line is distinct. This is documented and approved in `/home/sdc/gem5-fi-mmu-impl-v2/phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.1/MMU_Control_Inventory_Reconciliation.md` (lines 92,140):

> **CONTROL_INVENTORY_VERDICT = RECONCILED (34 run dirs / 28 referenced oracles /

| Control | Samples | Models | Contexts |
|---|---|---|---|
| `TEST-F1-CTRL-W9` | 5 | M01 | R01,R02,R03,R04,R05 |
| `TEST-F1-CTRL-W10-R01` | 3 | M02,M06,M08 | R01,R01,R01 |
| `TEST-F1-CTRL-W10-R02` | 2 | M02,M08 | R02,R02 |
| `TEST-F1-CTRL-W10-R03` | 3 | M02,M06,M08 | R03,R03,R03 |
| `TEST-F1-CTRL-W10-R04` | 3 | M02,M06,M08 | R04,R04,R04 |
| `TEST-F1-CTRL-W10-R05` | 2 | M02,M06 | R05,R05 |
| `TEST-F1-CTRL-W11-R01` | 1 | M03 | R01 |
| `TEST-F1-CTRL-W11-R02` | 1 | M03 | R02 |
| `TEST-F1-CTRL-W11-R03` | 1 | M03 | R03 |
| `TEST-F1-CTRL-W11-R04` | 1 | M03 | R04 |
| `TEST-F1-CTRL-W11-R05` | 1 | M03 | R05 |
| `TEST-F1-CTRL-W12-R01` | 1 | M04 | R01 |
| `TEST-F1-CTRL-W12-R02` | 1 | M04 | R02 |
| `TEST-F1-CTRL-W12-R03` | 1 | M04 | R03 |
| `TEST-F1-CTRL-W12-R04` | 1 | M04 | R04 |
| `TEST-F1-CTRL-W12-R05` | 1 | M04 | R05 |
| `TEST-F1-CTRL-W13-R01` | 1 | M05 | R01 |
| `TEST-F1-CTRL-W13-R02` | 1 | M05 | R02 |
| `TEST-F1-CTRL-W13-R03` | 1 | M05 | R03 |
| `TEST-F1-CTRL-W13-R04` | 1 | M05 | R04 |
| `TEST-F1-CTRL-W13-R05` | 1 | M05 | R05 |
| `TEST-F1-CTRL-W10S-COLD` | 1 | M06 | R02 |
| `TEST-F1-CTRL2-W14-R01` | 1 | M07 | R01 |
| `TEST-F1-CTRL2-W14-R02` | 1 | M07 | R02 |
| `TEST-F1-CTRL2-W14-R03` | 1 | M07 | R03 |
| `TEST-F1-CTRL2-W14-R04` | 1 | M07 | R04 |
| `TEST-F1-CTRL2-W14-R05` | 1 | M07 | R05 |
| `TEST-F1-CTRL-W10S-WARM` | 1 | M08 | R05 |

Unreferenced control directories (historical duplicates): `TEST-F1-CTRL-W14-R01`, `TEST-F1-CTRL-W14-R02`, `TEST-F1-CTRL-W14-R03`, `TEST-F1-CTRL-W14-R04`, `TEST-F1-CTRL-W14-R05`, `TEST-F1-CTRL-W9T`

## Zero-injection basis

Every control was executed with `mmuFaultEnable=true` but an empty `mmuFaultModel`; `CHAOSPropagation` arms injection only when both are set. `control_zero_proof.json` records `injection_applied_count=0` and gem5 exit 0 for all 28 oracles, and the control `Config/config.ini` / command line were re-read here. No `--mmu_fault_model` flag is present in any control command.

## W10S oracle substitution

The two W10S variant controls (`TEST-F1-CTRL-W10S-COLD`, `TEST-F1-CTRL-W10S-WARM`) use the guest serial transcript (`board.terminal`) as the oracle because their `golden_output.txt` is empty; this is documented in the inventory reconciliation. Both are context-exact by the generated rcS named in their command.

## Verdict

`CONTROL_AUDIT = PASS` — all 40 references, 28 oracles, hash, workload, context and zero-injection checks agree, with the frozen approval evidence above. No control was re-run or modified.
