# LSU E2E causal propagation — executive report

* Generated: 2026-11-17 18:17:10
* Runs: **180 faults** + **60 controls** (independent E2E campaign)
* End-to-end status: **180 E2E_CAUSAL_COMPLETE / 0 PARTIAL / 0 UNRESOLVED**

## Software symptoms

* `WRONG_OUTPUT`: **108**
* `NO_VISIBLE_ERROR`: **57**
* `HANG_TIMEOUT`: **15**

## Symptom subtypes

* `WRONG_ADDRESS_EFFECT`: **24**
* `N/A`: **57**
* `WRONG_MEMORY_CONTENT`: **27**
* `STALE_DATA_USED`: **47**
* `WRONG_NUMERIC_VALUE`: **10**
* `SIMULATOR_WATCHDOG`: **15**

## Propagation termination

* `COMMITTED_AND_PROPAGATED`: **108**
* `MASKED_BY_OVERWRITE`: **22**
* `MASKED_BY_VALUE_CONVERGENCE`: **35**
* `STALLED`: **15**

## Per model

| Model | WRONG_OUTPUT | NO_VISIBLE_ERROR | HANG_TIMEOUT |
|---|---:|---:|---:|
| A01 | 12 | 3 | 0 |
| A03 | 12 | 3 | 0 |
| DA04 | 13 | 2 | 0 |
| FW02 | 12 | 3 | 0 |
| FW05 | 12 | 3 | 0 |
| LP01 | 10 | 5 | 0 |
| LQ04 | 0 | 15 | 0 |
| MD04 | 12 | 3 | 0 |
| RP01 | 0 | 0 | 15 |
| SP05 | 11 | 4 | 0 |
| SQ01 | 14 | 1 | 0 |
| SQ03 | 0 | 15 | 0 |

## Per context

| Context | WRONG_OUTPUT | NO_VISIBLE_ERROR | HANG_TIMEOUT |
|---|---:|---:|---:|
| C01 | 27 | 6 | 3 |
| C02 | 27 | 6 | 3 |
| C03 | 5 | 28 | 3 |
| C04 | 24 | 9 | 3 |
| C05 | 25 | 8 | 3 |

## Per timing

| Timing | WRONG_OUTPUT | NO_VISIBLE_ERROR | HANG_TIMEOUT |
|---|---:|---:|---:|
| T01 | 37 | 18 | 5 |
| T02 | 36 | 19 | 5 |
| T03 | 35 | 20 | 5 |

## Answers to the ten required questions

1. **Complete chains:** 180/180 have a continuous, cited path from the injection to a software endpoint (or a proved masking/squash/stall termination).
2. **98 old checksum mismatches:** the new campaign measured 108 WRONG_OUTPUT runs. Breakdown: STALE_DATA_USED 47, WRONG_MEMORY_CONTENT 27, WRONG_ADDRESS_EFFECT 24, WRONG_NUMERIC_VALUE 10. Each has a first divergent application load/store with fault and control values.
3. **No-visible-error runs:** 57; mechanisms: MASKED_BY_VALUE_CONVERGENCE 35, MASKED_BY_OVERWRITE 22. No run is labelled 'masked' without a cited overwrite/reload or unchanged-data witness.
4. **Squash:** the new timed stream produced 0 target squashes. The six frozen squash cells were re-run under the new marker stream and every target now commits: FW02/C05/T01 -> SDC, FW05/C05/T01,T02,T03 -> SDC, LP01/C05/T02 -> masked convergence, LQ04/C05/T03 -> masked convergence. This is a dynamic-stream difference, not a re-interpretation of the frozen squash evidence; the classifier still reports SQUASHED_BEFORE_COMMIT if a target is squashed.
5. **RP01:** all 15 runs have a complete stall chain: replay-skip ledger, target absent from the committed stream while the paired control commits it, last progress point, silent-tick interval and the CHAOS_RP01 watchdog terminal.
6. **Application crash:** none. All SE runs either completed with exit 0 or were terminated by the in-simulator watchdog. A synthetic assertion was not added; doing so would change the terminal state.
7. **Kernel panic:** not observed. No FS fault run was used to replace the 180 SE samples. FS assets (Linux 5.15.36 kernel, Ubuntu disk, DTB, bootloader) exist on 0101; a bounded O3 FS boot instantiated the platform and reached 0.012 simulated seconds of kernel boot in 15 wall-clock minutes but not userspace. The FS config does not mount the 12 frozen LSU LSQ models, so no FS fault semantic parity or panic claim is made (see E2E_FS_Symptom_Report.md).
8. **Context/Timing effect:** see the per-context/per-timing tables and the Where/When comparison; C03 suppresses propagation by overwrite, C05 changes the timing stream and C04 adds dependency depth. T01/T02/T03 only move the selected eligible event.
9. **Remaining gaps:** none for the 180 SE runs under the stated observability boundary; the boundary itself (marker observers, commit-trace tail truncation for watchdog runs, no natural SE application crash, no FS kernel panic) is documented in E2E_Regression_and_Validation.md.
10. **Conclusion:** within SE observation the reconstruction meets the new per-run evidence criteria; the FS panic dimension is not claimed.

## Historical protection

* Frozen 240-run results, traces, Excel, 12 Where models and the frozen tag/commit were not modified.
* New runs use `E2E-*` RunIDs and map 1:1 to the old `*-WHEN-*` IDs.
* No GitHub/remote write was performed.
