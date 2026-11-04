# R6-P-UNIT — partial closeout (2026-11-04)

**Status: PARTIAL — 5 F0 RunIDs × 3 seeds certified as PARTIAL_SUBMODEL; 18
of the 23 P-F0/F5 RunIDs are blocked/not certifiable. The full P unit (53
RunIDs across F0–F6) is not complete and is not claimed complete.**

## Completed

- 5 RunIDs, 15 seeds, checker `admitted=True` / `certified=True`:
  `P01-F0-W8`, `P02-F0-W8`, `P02-F0-W10`, `P05-F0-W8`, `P05-F0-W10`.
- All seeds: gzip EOF, stats non-zero, exit 0, not truncated; oracle Masked;
  terminal full or detected_contained at L5.
- Per-seed docs: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`.
- F0 span census and per-pair span routing fixed (P03/P05-W8 eligible=7 would
  otherwise silently inject zero under the old span=50).
- No-fault goldens W2/W6/W8/W9/W10 match the authoritative registry.

## Not completed (exact reasons)

- **F5 trigger accounting defect (P02-F5-W8/W10, P08-F5-W8/W10):** the injector
  log and prop stream show one real injection with a full L5 chain, while the
  trigger summary reports `fires=131/417 outcomes_recorded=0 injected=0` and the
  campaign records `activated=0`. Seed2/3 were not run. This is an implementation
  accounting/permanent-mode defect, not an oracle result.
- **F0 chain not closed:** P01-F0-W2 (`L5_then_unknown`), P03-F0-W8/W9
  (`L4_then_unknown`; P03-b cross-page also absent), P06-F0-W6
  (`L0_then_unknown`), P06-F0-W8 (zero injection due to span/warmup fit).
- **Model substitution avoided:** P04 (mapped to P05 drop/dup), P07/P09 (mapped
  to classic CHAOSCache tag/dirty) are not the authoritative prefetch models and
  were not run.
- **Asset:** P09-F0-W13 requires PARSEC, absent in this repository.

## Partial-submodel boundaries

P01: stride bitflip only (PC tag missing). P02: confidence only
(degree/distance/throttle missing). P05: drop/dup only (delay/cancel missing).
P03/P06 as above. No full-model P claim is made.

## Evidence and verification

- Campaign evidence: `runs/lsu/r6_p_unit/campaign_seed1_20261104`,
  `runs/lsu/r6_p_unit/campaign_seed23_20261104`; census under
  `runs/lsu/r6_p_unit/census`; goldens under `runs/lsu/r6_p_unit/golden`.
- Binary `c6cccf5b…` (reused from O worktree; P code inherited from base);
  source/tool head `f5055a99`.
- The F0 EARLY_BIAS alarms are retained and adjudicated against the measured
  golden eligible counts; the faults can extend/shorten the downstream stream
  (±1–few events). Alarms on equality (e.g. eligible == span) are the trigger's
  conservative warning, not a missing injection.
