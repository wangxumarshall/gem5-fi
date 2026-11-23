# LSU E2E strict causal evidence — executive report

* Generated: 2026-11-18 18:00:46
* Sample: **180 fault runs** (12 models x 5 contexts x 3 timings) plus 60 paired controls.
* Strict status: **180 COMPLETE / 0 PARTIAL / 0 UNRESOLVED**
* This is not a node-existence check: only DIRECT_OBSERVED and RECONSTRUCTED_VERIFIED edges may carry a complete chain.

## What was actually repaired in this round

* Reconstructed hash state streams per accumulator from the HASH marker slots and renamed physical-register def/use.  A temporal neighbour is never a predecessor: the target before-operand must resolve to the exact committed instruction instance that produced the source after-operand.
* Replaced the unconditional `final_checksum` edge with a verified OUTPUT expression.  Every marker is recomputed from its real instruction; SQ-family runs are verified as `s ^ path` with two independent streams (C05) or a real counter operand (C01-C03).  All 165 non-RP01 outputs are verified.
* Gave every masking termination a real node with a strong incoming mechanism edge and an edge to the correct application output.  The 20 INTERMEDIATE_VALUE_DIVERGENCE runs have a connected first-divergence -> masking -> output path.
* Classified `ApplicationSymptom` from observed software values (actual address changes, injected response bytes, store-version bytes, byte-enable lanes, alternate store sources, complete non-consumption scans).  The model id/origin alone never selects a symptom; unproved cases are `WRONG_OUTPUT_UNSPECIFIED`.
* Built unified RP01 graphs from the post-injection ROB/IQ/LQ/commit samples, made `chain_proved` part of the status, and replaced the truncated gzip streams with canonical traces.
* The software hash transition is verified with the real `when_fnv` semantics, but connectivity now comes from def/use.
* Edge statistics have one source: the per-run JSON edge arrays. All CSVs and report totals are generated from them; the RP01 synthetic +90 discrepancy is gone.
* Memory is reconstructed byte-by-byte from committed stores and every computable load is checked against it (load match rate recorded per run); this is the basis of memory version/overwrite edges.
* Added a read-only RP01 post-injection stall trace and rebuilt a separate observation binary; the 15 RP01 faults and their 5 controls were re-run because the original traces had no post-injection state.
* The six historical squash cells are preserved as a separate, verified version; they are not merged into the 180 E2E sample.

## Software symptoms (strict, data-derived)

* `WRONG_OUTPUT`: **108**
* `NO_VISIBLE_ERROR`: **37**
* `INTERMEDIATE_VALUE_DIVERGENCE`: **20**
* `HANG_TIMEOUT`: **15**

## ApplicationSymptom (evidence-derived)

* `STALE_DATA_USED`: **47**
* `NO_VISIBLE_ERROR`: **37**
* `WRONG_MEMORY_CONTENT`: **27**
* `WRONG_ADDRESS_EFFECT`: **24**
* `INTERMEDIATE_VALUE_DIVERGENCE`: **20**
* `SIMULATOR_WATCHDOG`: **15**
* `WRONG_NUMERIC_VALUE`: **10**

## Propagation termination

* `COMMITTED_AND_PROPAGATED`: **108**
* `ACTIVATED_NO_DATA_CORRUPTION`: **34**
* `MASKED_BY_OVERWRITE`: **18**
* `SIMULATOR_STALL_WATCHDOG`: **15**
* `MASKED_BY_NON_CONSUMPTION`: **3**
* `MASKED_BY_VALUE_CONVERGENCE`: **2**

## Edge evidence inventory (all runs)

* `DIRECT_OBSERVED`: **712031** edges
* `CORRELATED_ONLY`: **609** edges
* `RECONSTRUCTED_VERIFIED`: **358** edges

## ARM64 semantic verification

* Reconstructed instruction checks: **1141566**
* Unresolved semantic mismatches: **0**
* Unsupported critical instructions: **0**
* Unverified taint edges: **0**
* Flag producers verified against real CC registers: **490710**
* NZCV mismatches: **0**
* Conditional instructions with unverified NZCV: **0**
* STP/LDP pair checks: **8**
* Incomplete memory semantics: **0**
* Dropped multi-source taint inputs: **0**
* Every pre-repair mismatch is reconciled in `SEMANTIC_MISMATCH_RECONCILIATION.csv`; the complete per-instruction ledger is `SEMANTIC_REVALIDATION_ALL_180.csv`.


## Answers to the ten required questions

1. **Verifiable application computation chains in the 108 checksum-mismatch runs:** every WRONG_OUTPUT chain in this report has a first divergent application event, a verified consumer path from the injected dynamic instruction, a first incorrect hash input and a verified final checksum. The per-run CSV and JSON name each object and value.
2. **Concrete wrong data/operation per WRONG_OUTPUT run:** `STRICT_E2E_SOFTWARE_SYMPTOMS.csv` reports the first divergent type/site/dynamic instruction, fault vs control value, and the first hash input. `STRICT_E2E_CAUSAL_EDGES.csv` carries every verified edge with its method and raw file/line.
3. **The 57 runs whose final checksum matches:** 20 have a committed intermediate software value divergence; 37 have none. The observed termination mechanisms are ACTIVATED_NO_DATA_CORRUPTION 34, MASKED_BY_OVERWRITE 18, MASKED_BY_NON_CONSUMPTION 3, and MASKED_BY_VALUE_CONVERGENCE 2. The exact witness is in `STRICT_E2E_MASKING_AUDIT.csv`.
4. **RP01 post-injection ROB/IQ/LSQ collection:** yes. `STRICT_E2E_RP01_STALL_AUDIT.csv` has 287-288 post-injection probes per run (dense then sparse), plus the WATCHDOG row, with target issued/executed/completed, IQ/ready/replay membership, LQ entry state/request/outstanding, ROB head/tail/occupancy, last commit and no-progress duration. The one 287-probe run lost only a redundant sample whose state equals the watchdog row.
5. **Can RP01 watchdog be explained by real dependencies and pipeline progress:** yes for all 15: the suppressed replay call leaves the target in the IQ (not ready) and out of the replay list; its LQ entry has no request, it sits at the ROB head, and commit stops at the immediately preceding sequence number for ~19.8M cycles until the internal watchdog fires. The paired control commits the same target and continues. The observation re-run's target dynamic-instruction identity matches the original E2E target in 15/15 runs and its controls reproduce the original eligible census. This is a simulator-internal watchdog, not an application crash.
6. **Six historical squashes:** all six pass the frozen identity/boundary/hash checks; the target squash cause remains "unrelated" (the fault did not cause the squash). The new E2E stream changes the target dynamic instruction, so the new runs are reported as a separate version, not as a reproduction of the old trace.
7. **Did the software markers change the dynamic stream:** the ELFs and all target sequences differ (expected, the binaries are instrumented). The eligible census is identical in 33/60 controls and differs in 27/60, with large C05 differences in A01/A03/LP01. No old ordinal was reused; every control, prepass and ordinal was re-run. See `STRICT_E2E_OBSERVATION_EQUIVALENCE.csv` and `STRICT_E2E_TARGET_IDENTITY_COMPARISON.csv`.
8. **Direct vs reconstructed edges:** the counts above split DIRECT_OBSERVED (renamed phys-reg def/use, payload->register, explicit tracer prop_edge, recorded memory version) from RECONSTRUCTED_VERIFIED (committed operands + real ARM64 semantics recomputed and matched). CORRELATED_ONLY edges are exported but never used to close a chain.
9. **Strict COMPLETE count:** 180/180. The remaining status counts are 0 PARTIAL and 0 UNRESOLVED.
10. **Remaining gaps:** every non-empty gap is listed per run in `STRICT_E2E_GAP_MATRIX.csv`; no gap is hidden by a count. The only evidence-version split is RP01 (observation binary v2) versus the other 165 runs (original binary v1); both are recorded with their own binary/ELF/config hashes.

## Honest limitations

* The marker observers change the dynamic instruction stream. They do not execute loads/stores, but they change speculation/scheduling. The census comparison quantifies this; it is not claimed to be non-invasive.
* The 15 RP01 complete chains use the observation binary v2. The fault semantics are unchanged (only read-only accessors and sampling were added), and the controls reproduce the original eligible counts, but the binary hash differs by construction.
* The six frozen squash cells are not part of the 180 E2E denominator. The new E2E workload does not reproduce those squashes because the dynamic stream changed; that is a finding, not a silent substitution.
* No FS kernel panic or natural SE application crash is claimed. RP01 terminates by the simulator's internal watchdog.

## Final verdict

`LSU_E2E_PAPER_FINAL_READY`

