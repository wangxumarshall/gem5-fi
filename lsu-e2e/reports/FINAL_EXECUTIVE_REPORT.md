# LSU SE paper-final executive report (R2)

* Scope: gem5 ARM O3CPU **Syscall Emulation (SE) only**. No FS, no kernel Oops/Panic experiment.
* Sample: **180 fault runs** (12 models x 5 contexts x 3 timings) + **60 paired controls** + 15 RP01 watchdog observation runs.
* Status: **180/180 E2E_CAUSAL_COMPLETE**, 0 PARTIAL, 0 UNRESOLVED.
* Edge inventory (from the 180 JSON edge arrays): **712998** edges (DIRECT_OBSERVED 712031, RECONSTRUCTED_VERIFIED 358, CORRELATED_ONLY 609).

## Software symptoms

* `HANG_TIMEOUT`: **15**
* `INTERMEDIATE_VALUE_DIVERGENCE`: **20**
* `NO_VISIBLE_ERROR`: **37**
* `WRONG_OUTPUT`: **108**

## Fault mechanism families (recorded -> paper family)

The `FaultMechanism` column keeps the frozen recorded label; `FaultMechanismFamily` is a documented mapping used only for grouping. FW02 is recorded as `UNKNOWN`, but its injected `fwd` record shows `normal_decision=forwarded -> fault_decision=suppressed`, so it maps to `STORE_TO_LOAD_FORWARDING_SUPPRESSED`.

* `ADDRESS_GENERATION_CORRUPTION`: **30**
* `LQ_STATE_CORRUPTION`: **30**
* `REPLAY_SUPPRESSION`: **15**
* `RESPONSE_DATA_CORRUPTION`: **15**
* `STORE_DATA_CORRUPTION`: **30**
* `STORE_TO_LOAD_FORWARDING_SUPPRESSED`: **15**
* `STORE_WRITE_CONTROL_CORRUPTION`: **30**
* `WRONG_FORWARD_SOURCE`: **15**

## Application symptoms (evidence-derived)

* `INTERMEDIATE_VALUE_DIVERGENCE`: **20**
* `NO_VISIBLE_ERROR`: **37**
* `SIMULATOR_WATCHDOG`: **15**
* `STALE_DATA_USED`: **47**
* `WRONG_ADDRESS_EFFECT`: **24**
* `WRONG_MEMORY_CONTENT`: **27**
* `WRONG_NUMERIC_VALUE`: **10**

## Propagation termination

* `ACTIVATED_NO_DATA_CORRUPTION`: **34**
* `COMMITTED_AND_PROPAGATED`: **108**
* `MASKED_BY_NON_CONSUMPTION`: **3**
* `MASKED_BY_OVERWRITE`: **18**
* `MASKED_BY_VALUE_CONVERGENCE`: **2**
* `SIMULATOR_STALL_WATCHDOG`: **15**

## Root-cause evidence

`FINAL_ROOT_CAUSE_MATRIX_180.csv` gives, for every run: the fault mechanism, injection hook and parameters, target dynamic instruction and PC, original and faulty microarchitectural values, first microarchitectural / architectural / software divergence, fault and control application values, addresses, store version and forwarding source where applicable, first incorrect hash input, final output, symptom, termination, evidence paths and confidence. Fields that the trace does not record are `UNKNOWN`, `NOT_OBSERVED` or `N/A`; no value is guessed.

The 57 runs whose final output matches the control have an explicit termination: ACTIVATED_NO_DATA_CORRUPTION 34, MASKED_BY_OVERWRITE 18, MASKED_BY_NON_CONSUMPTION 3, MASKED_BY_VALUE_CONVERGENCE 2. The 20 INTERMEDIATE_VALUE_DIVERGENCE runs keep a first software divergence and a strong path to the masking endpoint and final output.

## ARM64 semantics

* Reconstructed instruction revalidation records: **1141566**.
* NZCV flag producers verified: **490710**.
* Pre-repair mismatches reconciled: **6808 mismatch + 4 unsupported = 6812**, all with a final outcome.
* Unresolved semantic mismatches: **0**; unsupported critical: **0**; unverified semantic edges: **0**; NZCV mismatches: **0**; conditional unverified: **0**; incomplete memory semantics: **0**; dropped taint sources: **0**.

Ledger accounting is deliberately explicit: **1141566 semantic revalidation records + 27 sentinel rows = 1141593 CSV data rows**. The sentinel rows are 12 `NO_TAINTED_INSTRUCTION` and 15 `RP01_SEPARATE_TRACE` markers; they are not semantic verification records and must not be counted as such. The ledger pointer in `SEMANTIC_STATISTICS.json` is `evidence/semantic/SEMANTIC_REVALIDATION_ALL_180.csv.gz`.

## Observation Instrumentation Impact and Validity

The E2E binaries are observation-instrumented. The frozen comparison of the 60 paired controls (`STRICT_E2E_OBSERVATION_EQUIVALENCE.csv`) records:

* 60/60 control output checksums agree.
* 60/60 E2E ELF hashes differ from the original frozen ELF.
* 60/60 dynamic execution streams changed.
* 33/60 eligible-event counts are unchanged; 27/60 changed.
* 26/60 timing-ordinal sets changed.

Injection timing in this study was re-enumerated on the instrumented build: each fault targets an eligible event selected from the observation-instrumented execution. Each fault and its paired control use the same E2E binary, ELF and configuration. The results therefore describe the instrumented SE execution environment; this study does not claim that observation instrumentation leaves the original dynamic execution stream unchanged. Equal output checksums are an application-output agreement, not evidence of an identical dynamic trace. This is a methodological boundary of the study and requires no rerun.

## RP01

All 15 RP01 runs terminate as `SIMULATOR_STALL_WATCHDOG`: the replay reschedule is suppressed, the target never reissues, the LQ entry has no request, the target sits at the ROB head and commit makes no progress until the internal watchdog fires. The paired control commits the same target. This is a simulator watchdog, not a userspace crash, kernel Oops or kernel Panic.

## Historical squash

In the six When-v2 cases (FW02-C05-T01, FW05-C05-T01, FW05-C05-T02, FW05-C05-T03, LP01-C05-T02, LQ04-C05-T03), the target fault instruction was indeed squashed, but the direct cause was an unrelated control-flow recovery event: `FaultCausedSquash = 0` and `SquashCause = unrelated` in all six rows. The correct statement is that the speculative result of the fault instruction was subsequently withdrawn by an independent squash/recovery event and never entered architectural state; the fault itself did not trigger the squash. The six cases remain an independent historical evidence set and are excluded from the 180-run E2E denominator.

## Superseded reports

Legacy `E2E_*` reports and the obsolete FS symptom report are under `reports/history/superseded/` and marked `SUPERSEDED — NOT FOR FINAL PAPER STATISTICS`. This includes the legacy `STRICT_E2E_*.md` narrative reports (whose git status and test counts were written in the R1 round). The `FINAL_*` files are the single authoritative paper statistics; the `STRICT_E2E_*.csv` files remain the machine-readable evidence layer backing them.

## Consistency

`FINAL_STATISTICS_RECONCILIATION.md` records expected vs actual for every headline number. Overall: **PASS**.

