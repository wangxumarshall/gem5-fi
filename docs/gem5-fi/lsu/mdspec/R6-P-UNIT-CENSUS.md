# R6-P Unit — F0/F5 capability census and measured results (2026-11-04)

Unit: **P — Data Prefetcher (P01–P09)**. Authoritative matrix: 53 P RunIDs across
F0–F6. This round runs **only the 23 P-F0/P-F5 RunIDs**, matching the O-round
scope; F1/F2/F3/F4/F6 are not run and not claimed.

Platform: SE `configs/se/lsu_proxy.py`, B0 baseline, O3. Binary reused from the
O worktree (P worktree has no build): `.../r6-o-unit-20261103/CHAOS/gem5/build/ARM/gem5.opt`,
sha256 `c6cccf5b490823d216d01bd2449031aef2d892c88cec5cd291c852bbe86ca87b`;
source/tool head `f5055a99`.

## No-fault goldens (all match `runid_map.json`)

| W | binary | golden |
|---|---|---|
| W2 | beebs_kernels | `a10b9827edd8a9fb` |
| W6 | cache_dirtyevict | `062e5124df3667f9` |
| W8 | prefetch_stride | `629727c0ad9ca8ef` |
| W9 | gap_bfs | `030921682b3731f2` |
| W10 | stream_chase | `50ab96a7fe8f6ec2` |

## F0 span census (binary c6cccf5b; span=1e9, no fire)

| model | workload | eligible N |
|---|---|---|
| P01 | W2 | 142 |
| P01 | W8 | 133 |
| P02 | W8 | 133 |
| P02 | W10 | 417 |
| P03 | W8 | 7 |
| P03 | W9 | 62 |
| P05 | W8 | 7 |
| P05 | W10 | 291 |
| P06 | W6 | 56 (warmup=1) |
| P06 | W8 | 32 (warmup=1) |

`_prefetch_tier_flags` now uses this per-pair table for all P F0 models and
returns `None` (loud BLOCKED) for an unmeasured pair. The old fixed span=50
would have injected **zero** on P03/P05-W8 (eligible=7).

## Capability ledger (23 F0/F5 RunIDs)

### Certified 3/3 — PARTIAL_SUBMODEL (9 F0 RunIDs × 3 seeds)

| RunID | landed arm | seed1/2/3 terminal | oracle |
|---|---|---|---|
| P01-F0-W8 | P01-b stride bitflip | full / full / full (L5) | Masked |
| P02-F0-W8 | P02-a confidence clear/fake | full / full / full (L5) | Masked |
| P02-F0-W10 | P02-a confidence | detected_contained / full / full (L5) | Masked |
| P05-F0-W8 | P05-a/b drop/dup | full / detected_contained / full (L5) | Masked |
| P05-F0-W10 | P05-a/b drop/dup | detected_contained ×3 (L5) | Masked |
| P01-F0-W2 | P01-b stride bitflip | full / full / detected_contained (L5) | Masked |
| P03-F0-W8 | P03-a same-page substitution | full / detected_contained / full (L5) | Masked |
| P06-F0-W6 | P06-a fill classification | full / full / full (L5) | Masked |
| P06-F0-W8 | P06-a fill classification | detected_contained / detected_contained / full (L5) | Masked |

The P01/P03 rows are the F0-gap batch (`campaign_f0gap_20261104` +
`campaign_f0gap_seed23_20261104`, binary `9dafb090…`, source `d3f7471b`).
P01-W2 uses escape-first path selection (the real `errant_commit` lane
outranks the earlier squash lane); P03-W8 uses the `pf_request_id` lineage
bridge to connect the substituted prefetch request to its real demand fill.

The P06 rows are the **schema-v2 batch** (`campaign_p06_schema2_20261104` +
`campaign_p06_schema2_seed23_20261104`, binary `4f3db315…`, source
`05793493`). Monitoring schema v2 adds the unit-side L1 observation kind
`pf_class` at the REAL fill-classification gate; the fault semantics are
unchanged and `cache_access` remains forbidden as pf-family L1.

All 15 seeds: checker admitted/certified, gzip EOF, stats non-zero, exit 0,
not truncated. Docs: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/`.

**Partial boundaries** (not full-model claims):
- P01: P01-a PC-tag bitflip NOT implemented.
- P02: degree/distance/throttle NOT implemented.
- P05: delay / cancel-loss NOT implemented.

### F0 measured but not certifiable

| RunID | result | exact local block |
|---|---|---|
| P03-F0-W9 | Masked, `provable_to_L4_then_unknown`, admitted=False | The only `errant_commit` is on a different line (`0x80080`) and has no lineage bridge from the faulted prefetch (`0x7fcc0`); the checker correctly refuses cross-branch stitching. Do not borrow that L5. P03-b cross-page is still absent. |

P06-F0-W6/W8 are **no longer blocked**: the schema-v2 unit-side `pf_class`
L1 (above) satisfies the pf-family L1 gate without weakening it, and the
`pf_request_id` lineage bridge connects the real demand consumer (including
W8, whose demand precedes the prefetch fill: `pf_class` is emitted at the
fill gate and is time-forward). W8's seeds 1/2 terminate in
`detected_contained` via a real `store_not_retired` containment event.

### F5 fixed and certified 3/3 — PARTIAL_SUBMODEL (4 RunIDs × 3 seeds)

| RunID | fires / injected / no_effect | seed1/2/3 terminal | oracle |
|---|---|---|---|
| P02-F5-W8 | 128/64/64, 139/74/65, 130/65/65 | full ×3 (L5) | Masked |
| P02-F5-W10 | 446/313/133, 445/312/133, 437/270/167 | full ×3 (L5) | Masked |
| P08-F5-W8 | 131/7/124, 131/7/124, 131/7/124 | full ×3 (L5) | Masked |
| P08-F5-W10 | 417/291/126, 417/291/126, 417/291/126 | full ×3 (L5) | Masked |

All 12 seeds: checker `admitted=True` / `certified=True`, full L5, gzip EOF,
stats non-zero, exit 0, no truncation, `fires == injected + no_effect` on every
sample.

Root-cause and fix (C++ + campaign):
1. Campaign F5 did not override `--prefetch_max_faults` to 0 (FAMILY_MOUNT set
   1) → the injector stopped after the first write while the trigger kept
   firing. Fixed in `_prefetch_tier_flags` (F5 appends `--prefetch_max_faults 0`).
2. The injector never called `trigger.noteOutcome`, so `injected`/`no_effect`
   stayed 0. It now reports every fire, with `effective` computed from the
   real state change (P02 SatCounter before/after; P08 stride != 0; others by
   mutation).
3. Fault/inj registration happened **before** the effectiveness test, so
   idempotent fires left L0-only records (P08: 133 fires, 7 effective, 130
   fault ids) and some chains borrowed `cache_access` as L1. Registration now
   happens only for effective fires.
4. F5 now emits `pf_train` on every effective fire (same fault_id), so every
   chain has the prefetcher's own L1 witness instead of `cache_access`.
5. Built and froze a new binary: `runs/lsu/r6_p_unit/binaries/gem5.opt-8a2778d4`,
   sha256 `8a2778d4d32644dbb02355ee90a95b3107b56af31723811f663da8940d283204`
   (build log `r6o-logs/p_build_f5d.log`, no new warnings). No-fault golden W8
   re-checked: `629727c0ad9ca8ef`. The old `c6cccf5b` binary remains valid for
   the 15 previously certified F0 seeds (different evidence generation).

### Model not faithful / assets missing

| RunID | blocker |
|---|---|
| P04-F0/F5-W2/W8 (4) | **P04-a queue-valid and P04-c entry-selection implemented** (faithful shadow valid bit + real `Queued::getPacket` skip; real `std::iter_swap` of two live entries with the correct head retained). P04-c is behavior-verified on binary `a0d0e8af…`: W2/W8 show the wrong entry issued first and the displaced head issued late, exactly reversing the no-fault control order, with both entries issued once (no drop/dup). Both pilots remain `provable_to_L2_then_unknown`, performance-only, NOT certified. **P04-b pointer NOT implemented**; P04-F5 not run; the old P04→P05 drop/dup routing is removed. |
| P07-F0-W6/W8 (2) | campaign maps to classic CHAOSCache `l1d_target_field=tag`; prefetch response fill way/tag hook not implemented — not run |
| P09-F0-W6/W8 (2) | campaign maps to `l1d_target_field=dirty`; prefetch-caused dirty-eviction writeback loss/done-early/clear not implemented — not run |
| P09-F0-W13 (1) | PARSEC assets absent (plus model approximation above) — BLOCKED_ASSET |

## Honest totals

- P F0/F5 scope: 23 RunIDs.
- Certified 3/3 (partial-submodel): **13 RunIDs / 39 seeds** = 9 F0 + 4 F5.
- F0 local block: 1 RunID (P03-W9 cross-branch L5 not bridged). It is not
  written up as contained or SDC.
- Model partial / not implemented: P04-a queue-valid is now implemented and
  piloted (P04-F0-W2/W8 seed1, L0→L2, performance-only, not certified);
  P04-b/c remain unimplemented. P07 F0 fill-way/tag and P09 F0
  dirty-writeback remain not implemented; P09-W13 asset missing.
- The authoritative P unit has **53** RunIDs across F0–F6; this round completed
  only the above subset. No claim of full P-unit completion.

## Binary identity ledger (2026-11-04 takeover)

Per-batch identity is explicit; an old evidence stream is never rewritten as a
new-binary product.

| batch | binary | sha256 | source head | evidence |
|---|---|---|---|---|
| F0 certified (15 seeds) | O-worktree build | `c6cccf5b490823d216d01bd2449031aef2d892c88cec5cd291c852bbe86ca87b` | `f5055a99` | `campaign_seed1_20261104`, `campaign_seed23_20261104` |
| F5 certified (12 seeds) | `runs/lsu/r6_p_unit/binaries/gem5.opt-8a2778d4` | `8a2778d4d32644dbb02355ee90a95b3107b56af31723811f663da8940d283204` | `3f0a5589` | `campaign_f5_seed1_v2`, `campaign_f5_seed23_v2`, `campaign_f5_seed3_v2` |
| F0-gap (6 seeds) | `runs/lsu/r6_p_unit/binaries/gem5.opt-9dafb090` | `9dafb09011cda80cdb295397ed55b97660c4998dc2742654d78ec2dabef269c3` | `d3f7471b` | `campaign_f0gap_20261104`, `campaign_f0gap_seed23_20261104` |
| P06 schema v2 (6 seeds) | `runs/lsu/r6_p_unit/binaries/gem5.opt-4f3db315` | `4f3db315686908ca9bb290a5c3e15426a52562c696594c4c2a415dd8e45caa2a` | `05793493` | `campaign_p06_schema2_20261104`, `campaign_p06_schema2_seed23_20261104` |
| P04-a pilot (2 seeds) | `runs/lsu/r6_p_unit/binaries/gem5.opt-d97276d9` | `d97276d90b1c3e9dcfdba840d0d980796b5654703b3cec207fb2f85c916f7333` | `d9be2743` | `campaign_p04_20261104` (not certified) |
| P04-c pilot (2 seeds) | `runs/lsu/r6_p_unit/binaries/gem5.opt-0cb5073d` | `0cb5073d8d7faec2425ef9f1ffc4fe03a18c70cc6f5416c894b0bda58d477396` | `53561cba` | `campaign_p04c_20261104` (not certified) |
| P04-c behavior verification (2 pilots + 2 controls) | `runs/lsu/r6_p_unit/binaries/gem5.opt-a0d0e8af` | `a0d0e8af9d2242dd6250c24f48bdecf396e4bcc6c220dbbc6e331b65f49cd687` | `5d6399d8` + P04-c observation patch | `campaign_p04c_behavior_20261104` (not certified) |
| intermediate (NOT final) | `runs/lsu/r6_p_unit/binaries/gem5.opt-587ea8c3` | `587ea8c34db022edddb10828463621270d27c45944514f0234c65f30d3c5ad6d` | `3f0a5589` | none; never cited as evidence |

The takeover worktree's `CHAOS/gem5/build/ARM/gem5.opt` currently hashes to
`8a2778d4…` (the frozen F5 binary), so the build tree is at `3f0a5589` and the
F0-gap fixes can be built incrementally. The new F0-gap binary is recorded in
`docs/gem5-fi/lsu/evidence/R6-P-F0GAP-CENSUS.md` once built.
