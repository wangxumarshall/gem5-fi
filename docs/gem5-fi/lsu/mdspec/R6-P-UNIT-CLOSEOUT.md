# R6-P-UNIT — partial closeout (2026-11-04)

**Status: PARTIAL — 11 RunIDs × 3 seeds (33 seeds) certified as
PARTIAL_SUBMODEL: 7 F0 + 4 F5. 12 of the 23 P-F0/F5 RunIDs remain
blocked/not certifiable. The full P unit (53 RunIDs across F0–F6) is not
complete and is not claimed complete.**

## Completed

- 11 RunIDs, 33 seeds, checker `admitted=True` / `certified=True`.
- F0 (7): `P01-F0-W8`, `P02-F0-W8`, `P02-F0-W10`, `P05-F0-W8`,
  `P05-F0-W10`, plus the F0-gap batch `P01-F0-W2` and `P03-F0-W8`.
- F5 permanent (4): `P02-F5-W8`, `P02-F5-W10`, `P08-F5-W8`, `P08-F5-W10`.
- F0-gap batch (2 RunIDs / 6 seeds): binary `9dafb090…`, source `d3f7471b`.
  P01-W2 uses escape-first path selection; P03-W8 uses the `pf_request_id`
  lineage bridge. Both keep the PARTIAL_SUBMODEL boundaries (P01-b stride
  only; P03-a same-page only).
  F5 was repaired in C++ + campaign: `--prefetch_max_faults 0`, per-fire
  `noteOutcome(effective)`, effective-only fault registration, `pf_train` on
  every effective fire. New frozen binary
  `binaries/gem5.opt-8a2778d4` (sha256 `8a2778d4…`); all 12 F5 seeds are
  full/L5, no truncation, `fires == injected + no_effect`.
- All seeds: gzip EOF, stats non-zero, exit 0, not truncated; oracle Masked;
  terminal full or detected_contained at L5.
- Per-seed docs: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`.
- F0 span census and per-pair span routing fixed (P03/P05-W8 eligible=7 would
  otherwise silently inject zero under the old span=50).
- No-fault goldens W2/W6/W8/W9/W10 match the authoritative registry.

## Not completed (exact reasons)

- **F0 local blocks (3 RunIDs):** `P03-F0-W9` (the only errant_commit is on a
  different line and has no lineage bridge from the faulted prefetch; the
  cross-branch L5 is not borrowed), `P06-F0-W6` (observation fixed: the real
  demand hit is linked and the chain is `full`; admission is blocked only by
  `cache_access_faked_l1` — the pf-family L1 must be the unit observation and
  the P06 contract forbids a new kind), `P06-F0-W8` (injection fixed by the
  exact-command census; the demand precedes the prefetch fill, so the chain
  remains L2). No admission rule was loosened and no unknown was rewritten as
  contained.
- **P04-a implemented (pilot only):** the queue-valid model now uses a real
  shadow valid bit and a real `Queued::getPacket` skip (no P05 drop/dup
  substitution). P04-F0-W2/W8 seed1 pilot: `P04_queue_valid` injection, L0
  inj → L1 `pf_train(queue valid→invalid)` → L2 `pf_queue(queue_valid 1→0)` →
  L2 `invalid_skipped`, terminal `provable_to_L2_then_unknown`, oracle Masked,
  not admitted (a skipped prefetch has no architectural data effect). P04-b
  pointer and P04-c entry-selection remain unimplemented.
- **Model substitution avoided:** P07/P09 (mapped to classic CHAOSCache
  tag/dirty) are not the authoritative prefetch models and were not run.
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

## F0-gap supersession policy (2026-11-04 takeover)

The five F0 gap RunIDs (`P01-F0-W2`, `P03-F0-W8`, `P03-F0-W9`, `P06-F0-W6`,
`P06-F0-W8`) keep their original failed evidence under
`campaign_seed1_20261104/`. New runs go to `campaign_f0gap_20261104/` (seed1)
and `campaign_f0gap_seed23_20261104/` (seeds 2/3), on the new F0-gap binary.
Only those five RunIDs are superseded; the 9 already-certified RunIDs and all
F5 evidence are untouched. No older evidence file is deleted or rewritten.
