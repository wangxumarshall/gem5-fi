# R6-P Unit — coverage and evidence audit (2026-11-05, takeover #2)

Scope: the 23 authoritative P-F0/P-F5 RunIDs (the round runs only F0/F5;
the full P matrix has 53 RunIDs across F0-F6). Every status below is read
from the evidence directories, not copied from an older ledger. Non-B0
diagnostics are listed separately and never counted as RunIDs or seeds.

## Counts (computed, not copied)

- Authoritative F0/F5 scope: **23 RunIDs** (10 F0 P01/P02/P03/P05/P06/P07 +
  F5 P02/P04/P08/P09 as listed in the matrix).
- RunID-level certified 3/3: **14 RunIDs**, **42 seeds**, all
  `PARTIAL_SUBMODEL`.
- Submodel-level certifications: **15** — the 14 RunIDs plus P07-a on
  `P07-F0-W6` (P07-b is the RunID's primary submodel; P07-a is a second
  certified submodel on the same RunID).
- Non-B0 diagnostics (not RunIDs, oracle n/a): **3** — P09-a, P09-c, P07-c.
- Behavior-verified pilots (not certified): P04-b, P04-c (F0), P04-a/b/c
  F0 pilots; P04-F5 fixed-slot v2 (2 RunIDs, 6 deterministic reps).
- Remaining RunIDs not certified: **9** (table below).
- Full P unit (53 RunIDs) is **not** complete; F1/F2/F3/F4/F6 were not run
  and are not claimed.

## Per-RunID status

| RunID | submodel(s) | implemented | behavior-verified | certified 3/3 | seeds | workload coverage | model expressible | asset | status |
|---|---|---|---|---|---|---|---|---|---|
| P01-F0-W2 | P01-b stride bitflip | yes | yes | yes | 3 | W2 ok | P01-a PC tag absent | ok | CERTIFIED PARTIAL |
| P01-F0-W8 | P01-b stride bitflip | yes | yes | yes | 3 | W8 ok | P01-a absent | ok | CERTIFIED PARTIAL |
| P02-F0-W8 | P02-a confidence | yes | yes | yes | 3 | W8 ok | degree/distance/throttle absent | ok | CERTIFIED PARTIAL |
| P02-F0-W10 | P02-a confidence | yes | yes | yes | 3 | W10 ok | same | ok | CERTIFIED PARTIAL |
| P02-F5-W8 | P02-a confidence (F5) | yes | yes | yes | 3 | W8 ok | same | ok | CERTIFIED PARTIAL |
| P02-F5-W10 | P02-a confidence (F5) | yes | yes | yes | 3 | W10 ok | same | ok | CERTIFIED PARTIAL |
| P03-F0-W8 | P03-a same-page substitution | yes | yes | yes | 3 | W8 ok | P03-b cross-page absent | ok | CERTIFIED PARTIAL |
| P03-F0-W9 | P03-a same-page substitution | yes | yes | no | 0 | W9 ok | P03-b absent; L5 on another line, no bridge | ok | LOCAL BLOCK (L4_then_unknown) |
| P04-F0-W2 | P04-a/b/c | yes | yes (pilots) | no | 0 | W2 ok | all three F0 submodels | ok | PILOT (L2_then_unknown) |
| P04-F0-W8 | P04-a/b/c | yes | yes (pilots) | no | 0 | W8 ok | all three F0 submodels | ok | PILOT (L2_then_unknown) |
| P04-F5-W2 | P04-a fixed-slot permanent | yes | yes (v2) | no | 0 (3 det. reps) | W2 ok | F5 arm = P04-a only | ok | DIAGNOSTIC (L2, Masked) |
| P04-F5-W8 | P04-a fixed-slot permanent | yes | yes (v2) | no | 0 (3 det. reps) | W8 ok | same | ok | DIAGNOSTIC (L2, Masked) |
| P05-F0-W8 | P05-a/b drop/dup | yes | yes | yes | 3 | W8 ok | delay/cancel absent | ok | CERTIFIED PARTIAL |
| P05-F0-W10 | P05-a/b drop/dup | yes | yes | yes | 3 | W10 ok | delay/cancel absent | ok | CERTIFIED PARTIAL |
| P06-F0-W6 | P06-a fill classification | yes | yes | yes | 3 | W6 ok | P06-b/c/d absent | ok | CERTIFIED PARTIAL |
| P06-F0-W8 | P06-a fill classification | yes | yes | yes | 3 | W8 ok | P06-b/c/d absent | ok | CERTIFIED PARTIAL |
| P07-F0-W6 | P07-b tag mispair; P07-a data wrong way | yes | yes | yes (both submodels) | 3 + 3 submodel | W6 ok | P07-c implemented, coverage-blocked | ok | CERTIFIED PARTIAL (15th submodel) |
| P07-F0-W8 | P07-a/b | yes | yes (probe) | no | 0 | W8: no downstream demand | P07-c implemented | ok | COVERAGE BLOCK (L1_then_unknown) |
| P08-F5-W8 | P08-a stride stuck-at-0 | yes | yes | yes | 3 | W8 ok | stuck-at-1 / entry-never-invalidate absent | ok | CERTIFIED PARTIAL |
| P08-F5-W10 | P08-a stride stuck-at-0 | yes | yes | yes | 3 | W10 ok | same | ok | CERTIFIED PARTIAL |
| P09-F0-W6 | P09-a writeback loss; P09-c dirty clear | yes | non-B0 only | no | 0 | B0: zero prefetch-caused evictions | P09-b not expressible | ok | WORKLOAD COVERAGE BLOCK |
| P09-F0-W8 | P09-a/P09-c | yes | non-B0 only | no | 0 | B0: zero prefetch-caused evictions | same | ok | WORKLOAD COVERAGE BLOCK |
| P09-F0-W13 | P09-a/P09-c | yes | no | no | 0 | PARSEC absent | same | PARSEC missing | BLOCKED ASSET |

## Submodel coverage

| model | implemented submodels | missing / blocked |
|---|---|---|
| P01 | P01-b stride bitflip | P01-a PC-tag bitflip |
| P02 | P02-a confidence clear/fake | degree, distance, throttle |
| P03 | P03-a same-page substitution | P03-b cross-page |
| P04 | P04-a queue valid, P04-b tail pointer, P04-c entry selection; F5 fixed-slot on P04-a | no F5 arm for P04-b/c |
| P05 | P05-a drop, P05-b dup | delay, cancel-loss |
| P06 | P06-a fill classification | P06-b/c/d fill permissions |
| P07 | P07-a data wrong way, P07-b tag mispair (both certified on W6); P07-c old tag/valid implemented | P07-c B0 coverage block (no valid victim) |
| P08 | P08-a stride stuck-at-0 | stuck-at-1, entry-never-invalidate |
| P09 | P09-a writeback loss, P09-c dirty premature clear | P09-b MODEL_NOT_EXPRESSIBLE_AT_SITE; W13 asset |

## Diagnostics (non-RunID, oracle n/a)

| diagnostic | binary (frozen) | fault / control output | raw origin | chain | audit |
|---|---|---|---|---|---|
| P09-a writeback loss | `c6953bba…` | `8e64d8d4427c2169` / `062e5124df3667f9` | `pf_wb` | full/L5 | PASS |
| P09-c dirty clear | `5b26240c…` (v2) | `8e64d8d4427c2169` / `062e5124df3667f9` | `pf_dirty` | full/L5 | PASS (original binary not frozen; v2 authoritative) |
| P07-c stale tag | `5b26240c…` | `fcecec2dd089d871` / `062e5124df3667f9` | `pf_stale_tag` | full/L5 | PASS |
| P04-b tail pointer | `f52461b5…` | n/a | behavior log | L2 | behavior-verified pilot |
| P04-c entry selection | `a0d0e8af…` | n/a | behavior log | L2 | behavior-verified pilot |

See `evidence/R6-P-DIAGNOSTIC-AUDIT.md` for the exact commands, SHAs, and
the P09-c provenance gap.

## Document reconciliation

Corrected in this takeover:

- The P07 evidence and CENSUS/CLOSEOUT/INDEX no longer say P07-a is
  unimplemented; P07-a is certified 3/3 as a submodel on `P07-F0-W6`
  (`a7ebdbbd`).
- P07-c is described as implemented but B0 coverage-blocked (all
  pure-prefetch fills land in invalid ways), not “not implemented”.
- P09-c is described as implemented and audited; P09-b remains
  MODEL_NOT_EXPRESSIBLE_AT_SITE.
- P04-F5's whole-queue field is labelled SUPERSEDED; the fixed-slot v2 is
  the authoritative evidence (commit `a00ab5c7`, binary `b2bf0cd3…`), and
  the old run is retained.
- `R6-STATUS-TABLE.md` P rows are **stale** (they say NOT_RUN and were
  generated from a root that did not include `runs/lsu/r6_p_unit`). It is a
  generated historical table; the authoritative P status is this audit and
  `R6-P-UNIT-CENSUS.md`. Do not cite its P rows as current evidence.
- No document claims F1/F2/F3/F4/F6 P coverage; the 53-RunID full unit is
  not complete.

## Remaining blocks (unchanged unless new evidence appears)

1. `P03-F0-W9`: L4 terminal; the only errant commit is on another line with
   no lineage bridge; P03-b cross-page absent. Local block.
2. `P07-F0-W8`: no downstream consumer; three eligible fills all terminal
   L1. Real workload-coverage block.
3. `P09-F0-W6/W8`: B0 1 MiB L2 has pure-prefetch fills but zero
   prefetch-caused evictions. Coverage block; non-B0 diagnostics do not
   convert it.
4. `P09-F0-W13`: PARSEC assets absent. BLOCKED_ASSET.
5. `P09-b`: model not expressible at the authoritative writeback site.
6. P04 F0 pilots and P04-F5 v2 remain performance-only / L2-Masked, not
   certified; P04-b/c have no F5 arm.
