# R6-P-UNIT — partial closeout (2026-11-04)

**Status: PARTIAL — 14 RunIDs × 3 seeds (42 seeds) certified as
PARTIAL_SUBMODEL: 10 F0 + 4 F5. 9 of the 23 P-F0/F5 RunIDs remain
blocked/not certifiable. The full P unit (53 RunIDs across F0–F6) is not
complete and is not claimed complete.**

## Completed

- 14 RunIDs, 42 seeds, checker `admitted=True` / `certified=True`.
  - `P07-F0-W6` (new, PARTIAL_SUBMODEL P07-b): formal campaign 3/3, oracle
    Masked, full L5, output hash golden (no SDC claim). W6 has 2 eligible
    events; seeds 1/3 sample the first and seed 2 the second. P07-F0-W8
    remains an unadmitted L1 diagnostic.
- F0 (9): `P01-F0-W8`, `P02-F0-W8`, `P02-F0-W10`, `P05-F0-W8`,
  `P05-F0-W10`, the F0-gap batch `P01-F0-W2` / `P03-F0-W8`, and the
  schema-v2 batch `P06-F0-W6` / `P06-F0-W8`.
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

- **F0 local block (1 RunID):** `P03-F0-W9` — the only errant_commit is on a
  different line and has no lineage bridge from the faulted prefetch; the
  cross-branch L5 is not borrowed.
- **P06 schema v2 (resolved):** `P06-F0-W6` / `P06-F0-W8` now certify 3/3.
  The old "P06 adds no kind" rule was an internal monitoring-schema
  limitation; schema v2 adds the unit-side L1 kind `pf_class` at the REAL
  fill-classification gate. Fault semantics are unchanged and the L1 gate is
  NOT weakened (`cache_access` remains forbidden as pf-family L1). W8's
  demand-before-fill ordering is handled by the `pf_class` event (emitted at
  the fill gate, time-forward) plus the `pf_request_id` lineage bridge; W8
  seeds 1/2 contain via a real `store_not_retired` event.
- No admission rule was loosened and no unknown was rewritten as contained.
- **P04-a / P04-c implemented (pilot only):** P04-a uses a real shadow valid
  bit and a real `Queued::getPacket` skip (no P05 drop/dup substitution).
  P04-c swaps the second live queue entry into the head and retains the
  correct head (`std::iter_swap`; no erase/duplicate). Behavior-verified on
  binary `a0d0e8af…`: W2/W8 select `head=0x77980/0x76980`,
  `second=0x77b40/0x76b40`; the wrong entry is issued first and the correct
  head is issued late at the next tick, exactly reversing the no-fault
  control order; both issue once. **P04-b pointer implemented** as a
  one-shot tail-pointer -1 insertion (new entry inserted before the tail;
  no erase/duplicate) and behavior-verified on binary `f52461b5…`:
  W2/W8 arm with `tail=0x77ec0/0x76ec0`, `insert=0x77580/0x76580`,
  `size=4`; the inserted entry issues before the former tail, while
  no-fault controls issue tail-first; both entries issue once. All P04
  pilots terminate `provable_to_L2_then_unknown`, oracle Masked, not
  admitted (no architectural data effect observed). Seeds 2/3 were not run
  for the F0 pilots.
- **P04-F5 permanent queue-valid stuck implemented (3 seeds, NOT
  certified):** F5 latches ONE physical fault identity at the first
  eligible event after warm-up and keeps the queue valid field stuck at
  invalid to the end of the run (no recovery). Every live entry is
  invalidated and every later ready-queue entry is born invalid; each
  birth/skip is a propagation instance of the same `fault_id`. Binary
  `chaos build` sha256 `cb98fbb5…`, source `f502fd19` + patch. W2/W8,
  seeds 1/2/3: `attempted=143/131 eligible=1 injected=1 fires=1
  no_effect=0`, latch tick 148525300/107286025 with 4 live entries,
  terminal `provable_to_L2_then_unknown`, admitted False, oracle Masked,
  output hashes exactly the goldens. No-fault controls (warm-up 1e9,
  no latch) reproduce both goldens. The three seeds are deterministic
  replications (F5 has no span draw), not independent samples. P04-b/c
  have no F5 arm. Evidence: `campaign_p04f5_20261105`,
  `campaign_p04f5_seed23_20261105`; details in
  `evidence/R6-P-P04-EVIDENCE.md`.
- **P09-a implemented (diagnostic, not a RunID):** the prefetch-caused
  dirty-writeback loss is modelled at the REAL eviction gate. A fill-time
  marker (`chaosFillFromPrefetch`) is set only when the MSHR has a
  `FromPrefetcher` target and no `FromCPU`/`FromSnoop` target, and is
  cleared immediately after `handleFill` (no stale marker); the victim's
  writeback packet is then suppressed. B0 W6/W8 have **zero eligible
  events** (prefetch fills exist — W6=50, W8=28 — but none evicts), so
  P09-F0-W6/W8 remain blocked by workload coverage. A non-authoritative
  L2=16KiB diagnostic control proves the path end-to-end: writeback
  suppressed (`pf_wb`, `cache_evict` suppressed), same-line demand miss
  re-fills stale data, `taint_reg` and a real `errant_commit` (L5, chain
  full), output hash differs from the no-fault golden. That control is not
  a RunID/seed and its oracle is n/a. **P09-c implemented (runtime-
  verified diagnostic, not a RunID):** the victim's dirty state is cleared
  before the eviction decision, so the eviction is a CleanEvict and no
  writeback request is generated (`pf_dirty` dirty→clean +
  `cache_evict` clean_evict/dirty_premature_clear) — a distinct faulted
  field from P09-a. Same non-B0 L2=16KiB measurement: real stale re-read →
  taint → `errant_commit` L5 (chain full), output `8e64d8d4427c2169` vs
  control golden `062e5124df3667f9`; binary `c8b0e25f…`. **P09-b is not
  expressible at the authoritative site** in classic gem5 (writeback is
  fire-and-forget: `writebackBlk` clears dirty at creation, the line is
  invalidated immediately, and there is no completion ack; the only
  "done" states are internal buffer acceptance or the dirty state, the
  latter being exactly P09-c). It is recorded as a local model block, not
  implemented as a relabel.
- **P07-b implemented (seed1 pilot, not a certified RunID):** at the REAL
  pure-prefetch fill gate, the fill block and a distinct valid same-set
  partner exchange **tags** (data stays in its own way). B0 census W6=2 /
  W8=5 eligible. Seed1 W6 fill 0x7ec00↔0x8ec00: real `pf_tag`, subsequent
  demand misses, checker terminal `full`/L5, but the output hash remains
  the golden `062e5124df3667f9` — recorded without an SDC claim (oracle
  n/a). W8 fill 0x76740↔0x86740: no downstream demand, terminal L1,
  output golden. Seeds 2/3 not run; P07-a/c not implemented.
- **Model substitution avoided:** the old classic CHAOSCache `tag`/`dirty`
  routing for P07/P09 is removed.
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
