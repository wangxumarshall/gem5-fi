# Strict E2E regression and validation

## Executed gates (real output)

* Causal-edge negative/positive tests: `........................................................................ [ 87%]
..........                                                               [100%]
82 passed in 174.39s (0:02:54)` (exit 0).
* 12 Where models unchanged: the model list is exactly `A01, A03, DA04, FW02, FW05, LP01, LQ04, MD04, RP01, SP05, SQ01, SQ03`; the fault-rule headers were not edited (only read-only accessors, sampling and report code were added).
* 180 fault raw evidence: every chain references its original `prop_trace.csv.gz`/`commit_trace.csv.gz` and records the line/record id; SHA256s are in `STRICT_E2E_EVIDENCE_INDEX.csv`.
* Controls: **60/60 COMPLETED**, zero injections, oracle pass.
* Timing ordinal matches: **180/180**.
* SDC hash transitions verified: **108/108**.
* SDC runs with a first incorrect hash input: **108/108**.
* SDC runs with a strong (direct/reconstructed) software edge: **108/108**.
* Strict complete: **180/180**.
* Frozen artifact hashes: 2dc7b7534754420eef891aadb2fb78e4aef4265ab571e15313cb26fbb95af668  LSU_When_v2_Final_Results.zip; 95338a94998f10cdded29d323ce1963d54eaf15077c638762bd144b18011e340  LSU_When_v2_Evidence_Hardening_Final.zip; 9c18e496a07ecfd00d268bb7163f38075c6ef2f1e02817142eb2b2af67ca1529  LSU_When_v2_FINAL_CLOSURE.zip; 78e546a814d4a4cc2e96948aa26e4f451578cfdabfa2cb3d6fc7164ec2fc44c3  inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx
* E2E code commit: `e4405a6391098437b3f2646d74173685ee94af89`; gem5 source commit: `2bbf2907668f78e0b67473caf5a63153b70bede3` (local only, no push).

## Observation equivalence

* The instrumented ELFs differ from the frozen ones in all 60 controls. The eligible census is identical in 33/60 and differs in 27/60. The old ordinal was never reused; each control/prepass/fault pair was re-run under its own binary.
* For RP01, the observation binary's controls reproduce the original eligible counts (5/5) and the original selected ordinals; the faults are still the same semantic skip event.

## Honest limits

* The marker instructions are ALU-only but change scheduling; the census delta is reported, not denied.
* `CORRELATED_ONLY` edges are exported for transparency and are never used to close a complete chain.
* The residual gaps (if any) are enumerated in the gap matrix.

