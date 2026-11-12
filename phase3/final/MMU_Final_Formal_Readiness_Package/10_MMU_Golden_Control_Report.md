# MMU Golden Control Report

Every formal sample needs a separately executed no-fault control.  A faulted run's own output is never a golden.

## Per model/context control

| Model | Context | Control path | Line present | Independent | Detail |
|---|---|---|---|---|---|
| M01 | R01 | `runs/TEST-F1-CTRL-W9/Run_Log/golden_output.txt` | YES | YES | canonical W9 all-ASID control |
| M01 | R02 | `runs/TEST-F1-CTRL-W9/Run_Log/golden_output.txt` | YES | YES | canonical W9 all-ASID control |
| M01 | R03 | `runs/TEST-F1-CTRL-W9/Run_Log/golden_output.txt` | YES | YES | canonical W9 all-ASID control |
| M01 | R04 | `runs/TEST-F1-CTRL-W9/Run_Log/golden_output.txt` | YES | YES | canonical W9 all-ASID control |
| M01 | R05 | `runs/TEST-F1-CTRL-W9/Run_Log/golden_output.txt` | YES | YES | canonical W9 all-ASID control |
| M02 | R01 | `runs/TEST-F1-CTRL-W10-R01/Run_Log/golden_output.txt` | YES | YES | independent no-fault R01 control runs/TEST-F1-CTRL-W10-R01 |
| M02 | R02 | `runs/TEST-F1-CTRL-W10-R02/Run_Log/golden_output.txt` | YES | YES | independent no-fault R02 control runs/TEST-F1-CTRL-W10-R02 |
| M02 | R03 | `runs/TEST-F1-CTRL-W10-R03/Run_Log/golden_output.txt` | YES | YES | independent no-fault R03 control runs/TEST-F1-CTRL-W10-R03 |
| M02 | R04 | `runs/TEST-F1-CTRL-W10-R04/Run_Log/golden_output.txt` | YES | YES | independent no-fault R04 control runs/TEST-F1-CTRL-W10-R04 |
| M02 | R05 | `runs/TEST-F1-CTRL-W10-R05/Run_Log/golden_output.txt` | YES | YES | independent no-fault R05 control runs/TEST-F1-CTRL-W10-R05 |
| M03 | R01 | `runs/TEST-F1-CTRL-W11-R01/Run_Log/golden_output.txt` | YES | YES | independent no-fault R01 control runs/TEST-F1-CTRL-W11-R01 |
| M03 | R02 | `runs/TEST-F1-CTRL-W11-R02/Run_Log/golden_output.txt` | YES | YES | independent no-fault R02 control runs/TEST-F1-CTRL-W11-R02 |
| M03 | R03 | `runs/TEST-F1-CTRL-W11-R03/Run_Log/golden_output.txt` | YES | YES | independent no-fault R03 control runs/TEST-F1-CTRL-W11-R03 |
| M03 | R04 | `runs/TEST-F1-CTRL-W11-R04/Run_Log/golden_output.txt` | YES | YES | independent no-fault R04 control runs/TEST-F1-CTRL-W11-R04 |
| M03 | R05 | `runs/TEST-F1-CTRL-W11-R05/Run_Log/golden_output.txt` | YES | YES | independent no-fault R05 control runs/TEST-F1-CTRL-W11-R05 |
| M04 | R01 | `runs/TEST-F1-CTRL-W12-R01/Run_Log/golden_output.txt` | YES | YES | independent no-fault R01 control runs/TEST-F1-CTRL-W12-R01 |
| M04 | R02 | `runs/TEST-F1-CTRL-W12-R02/Run_Log/golden_output.txt` | YES | YES | independent no-fault R02 control runs/TEST-F1-CTRL-W12-R02 |
| M04 | R03 | `runs/TEST-F1-CTRL-W12-R03/Run_Log/golden_output.txt` | YES | YES | independent no-fault R03 control runs/TEST-F1-CTRL-W12-R03 |
| M04 | R04 | `runs/TEST-F1-CTRL-W12-R04/Run_Log/golden_output.txt` | YES | YES | independent no-fault R04 control runs/TEST-F1-CTRL-W12-R04 |
| M04 | R05 | `runs/TEST-F1-CTRL-W12-R05/Run_Log/golden_output.txt` | YES | YES | independent no-fault R05 control runs/TEST-F1-CTRL-W12-R05 |
| M05 | R01 | `runs/TEST-F1-CTRL-W13-R01/Run_Log/golden_output.txt` | YES | YES | independent no-fault R01 control runs/TEST-F1-CTRL-W13-R01 |
| M05 | R02 | `runs/TEST-F1-CTRL-W13-R02/Run_Log/golden_output.txt` | YES | YES | independent no-fault R02 control runs/TEST-F1-CTRL-W13-R02 |
| M05 | R03 | `runs/TEST-F1-CTRL-W13-R03/Run_Log/golden_output.txt` | YES | YES | independent no-fault R03 control runs/TEST-F1-CTRL-W13-R03 |
| M05 | R04 | `runs/TEST-F1-CTRL-W13-R04/Run_Log/golden_output.txt` | YES | YES | independent no-fault R04 control runs/TEST-F1-CTRL-W13-R04 |
| M05 | R05 | `runs/TEST-F1-CTRL-W13-R05/Run_Log/golden_output.txt` | YES | YES | independent no-fault R05 control runs/TEST-F1-CTRL-W13-R05 |
| M06 | R01 | `runs/TEST-F1-CTRL-W10-R01/Run_Log/golden_output.txt` | YES | YES | independent no-fault R01 control runs/TEST-F1-CTRL-W10-R01 |
| M06 | R02 | `runs/TEST-F1-CTRL-W10S-COLD/Run_Log/board.terminal` | YES | YES | independent no-fault R02 control runs/TEST-F1-CTRL-W10S-COLD |
| M06 | R03 | `runs/TEST-F1-CTRL-W10-R03/Run_Log/golden_output.txt` | YES | YES | independent no-fault R03 control runs/TEST-F1-CTRL-W10-R03 |
| M06 | R04 | `runs/TEST-F1-CTRL-W10-R04/Run_Log/golden_output.txt` | YES | YES | independent no-fault R04 control runs/TEST-F1-CTRL-W10-R04 |
| M06 | R05 | `runs/TEST-F1-CTRL-W10-R05/Run_Log/golden_output.txt` | YES | YES | independent no-fault R05 control runs/TEST-F1-CTRL-W10-R05 |
| M07 | R01 | `runs/TEST-F1-CTRL2-W14-R01/Run_Log/golden_output.txt` | YES | YES | independent no-fault R01 control runs/TEST-F1-CTRL2-W14-R01 |
| M07 | R02 | `runs/TEST-F1-CTRL2-W14-R02/Run_Log/golden_output.txt` | YES | YES | independent no-fault R02 control runs/TEST-F1-CTRL2-W14-R02 |
| M07 | R03 | `runs/TEST-F1-CTRL2-W14-R03/Run_Log/golden_output.txt` | YES | YES | independent no-fault R03 control runs/TEST-F1-CTRL2-W14-R03 |
| M07 | R04 | `runs/TEST-F1-CTRL2-W14-R04/Run_Log/golden_output.txt` | YES | YES | independent no-fault R04 control runs/TEST-F1-CTRL2-W14-R04 |
| M07 | R05 | `runs/TEST-F1-CTRL2-W14-R05/Run_Log/golden_output.txt` | YES | YES | independent no-fault R05 control runs/TEST-F1-CTRL2-W14-R05 |
| M08 | R01 | `runs/TEST-F1-CTRL-W10-R01/Run_Log/golden_output.txt` | YES | YES | independent no-fault R01 control runs/TEST-F1-CTRL-W10-R01 |
| M08 | R02 | `runs/TEST-F1-CTRL-W10-R02/Run_Log/golden_output.txt` | YES | YES | independent no-fault R02 control runs/TEST-F1-CTRL-W10-R02 |
| M08 | R03 | `runs/TEST-F1-CTRL-W10-R03/Run_Log/golden_output.txt` | YES | YES | independent no-fault R03 control runs/TEST-F1-CTRL-W10-R03 |
| M08 | R04 | `runs/TEST-F1-CTRL-W10-R04/Run_Log/golden_output.txt` | YES | YES | independent no-fault R04 control runs/TEST-F1-CTRL-W10-R04 |
| M08 | R05 | `runs/TEST-F1-CTRL-W10S-WARM/Run_Log/board.terminal` | YES | YES | independent no-fault R05 control runs/TEST-F1-CTRL-W10S-WARM |

## M02 W10 target PFN map

Source: `/home/sdc/gem5-fi-mmu-impl-v2/phase3/formal/w10_pfn_map.json` (phase3/formal/w10_pfn_map.json: 5/5 contexts)

| Context | target_pfn | Source run | SHA256 |
|---|---|---|---|
| R01 | `0x834b2` | TEST-F1-CTRL-W10-R01 | `0c129fccb17eab0c` |
| R02 | `0x834b2` | TEST-F1-CTRL-W10-R02 | `66a42431eb599efc` |
| R03 | `0x834b2` | TEST-F1-CTRL-W10-R03 | `b4e023e6425474a4` |
| R04 | `0x834b2` | TEST-F1-CTRL-W10-R04 | `99fbdd1c31630232` |
| R05 | `0x834b2` | TEST-F1-CTRL-W10-R05 | `3c52e535dac71ddd` |

The legacy `--ctx all` W10 control is rejected: it reports target PFN `0x83480` / sentinel `0x7d`, while the final scoped control `TEST-F1-CTRL-W10-R02` reports target PFN `0x834b2`, neighbour `0x834b3` and sentinel `0x63`. The earlier scoped control `TEST-ENV-CTRL-W10` reported `0x834b6`; it predates the final EPAN checkpoint and is superseded. No reference to `0x83480` or `0x834b6` is used as a run parameter.
