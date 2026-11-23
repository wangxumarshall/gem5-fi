# R2 supplemental revision 1

This archive is a documentation-and-archive revision of
`LSU_E2E_PAPER_FINAL_FROZEN_R2`. No gem5 experiment was rerun, no
fault model or matrix was changed, and no causal-chain result was
modified.

Changes relative to R2:

* `SEMANTIC_STATISTICS.json` ledger pointer corrected to
  `evidence/semantic/SEMANTIC_REVALIDATION_ALL_180.csv.gz`; every
  statistic is unchanged (1,141,566 revalidation records, 27
  sentinel rows, 1,141,593 CSV data rows).
* Added `Observation Instrumentation Impact and Validity` to the
  Executive Report and Reproduction Guide (60/60 output agreement,
  60/60 ELF differences, 60/60 stream changes, 33/60 unchanged and
  27/60 changed eligible counts, 26/60 changed ordinal sets).
* Clarified the six historical squash cases: the target was
  squashed by an unrelated control-flow recovery event
  (`FaultCausedSquash=0`, `SquashCause=unrelated`); the fault did not
  trigger the squash.
* Added the independent 735-file trace backup and its manifest.

All historical tags, including R1 and R2, are unchanged.
