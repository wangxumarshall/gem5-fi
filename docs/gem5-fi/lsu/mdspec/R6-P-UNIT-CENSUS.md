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

### Certified 3/3 — PARTIAL_SUBMODEL (5 RunIDs × 3 seeds)

| RunID | landed arm | seed1/2/3 terminal | oracle |
|---|---|---|---|
| P01-F0-W8 | P01-b stride bitflip | full / full / full (L5) | Masked |
| P02-F0-W8 | P02-a confidence clear/fake | full / full / full (L5) | Masked |
| P02-F0-W10 | P02-a confidence | detected_contained / full / full (L5) | Masked |
| P05-F0-W8 | P05-a/b drop/dup | full / detected_contained / full (L5) | Masked |
| P05-F0-W10 | P05-a/b drop/dup | detected_contained ×3 (L5) | Masked |

All 15 seeds: checker admitted/certified, gzip EOF, stats non-zero, exit 0,
not truncated. Docs: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/`.

**Partial boundaries** (not full-model claims):
- P01: P01-a PC-tag bitflip NOT implemented.
- P02: degree/distance/throttle NOT implemented.
- P05: delay / cancel-loss NOT implemented.

### F0 measured but not certifiable

| RunID | result | blocker |
|---|---|---|
| P01-F0-W2 | Masked, `provable_to_L5_then_unknown`, admitted=False | chain has no closed L5 detection/containment; needs chain-model repair |
| P03-F0-W8 | Masked, L4 unknown, admitted=False | P03-a same-page substitution; cross-page P03-b missing; chain stops at L4 |
| P03-F0-W9 | Masked, L4 unknown, admitted=False | same; P03-b missing |
| P06-F0-W6 | Masked, `provable_to_L0_then_unknown`, admitted=False | P06-a fill-class marking produced no L1.. chain (needs chain-model repair) |
| P06-F0-W8 | zero events | span=32/warmup=1 draw 29 but formal stream observed 28 eligible — no fire; needs P06 span/warmup re-fit |

### F5 measured — trigger accounting defect

| RunID | observed | blocker |
|---|---|---|
| P02-F5-W8 / W10 | injector log 1 line, prop stream 1 inj + full L5 chain | trigger summary `fires=131/417 outcomes_recorded=0 injected=0`; campaign `activated=0`. F5 permanent accounting/per-event outcome is incomplete. Seed2/3 not run. |
| P08-F5-W8 / W10 | same shape (stride stuck; full L5) | same F5 accounting defect |

The chain is real (checker full/L5), but the trigger/activation accounting is
not, so these cells are **not accepted** and not counted complete.

### Model not faithful / assets missing

| RunID | blocker |
|---|---|
| P04-F0/F5-W2/W8 (4) | campaign maps P04 to `p05_drop_dup`; queue valid/pointer/select model not implemented — fault-model substitution, not run |
| P07-F0-W6/W8 (2) | campaign maps to classic CHAOSCache `l1d_target_field=tag`; prefetch response fill way/tag hook not implemented — not run |
| P09-F0-W6/W8 (2) | campaign maps to `l1d_target_field=dirty`; prefetch-caused dirty-eviction writeback loss/done-early/clear not implemented — not run |
| P09-F0-W13 (1) | PARSEC assets absent (plus model approximation above) — BLOCKED_ASSET |

## Honest totals

- P F0/F5 scope: 23 RunIDs.
- Full 3/3 certified (partial-submodel): **5 RunIDs / 15 seeds**.
- F0 measured but not certifiable: 5 RunIDs.
- F5 accounting defect: 4 RunIDs.
- Model/asset blocked: 9 RunIDs.
- The authoritative P unit has **53** RunIDs across F0–F6; this round completed
  only the above subset. No claim of full P-unit completion.
