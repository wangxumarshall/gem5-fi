# R6-P-P07 — prefetch-response fill tag/way mispair (P07-b)

**Status: P07-F0-W6 CERTIFIED 3/3 as PARTIAL_SUBMODEL (P07-b only);
P07-F0-W8 remains an unadmitted L1 diagnostic.**
Formal campaign `campaign_p07_formal_v2_20261104` (binary
`gem5.opt-91c0e030`, sha256
`91c0e030bade715e13a6f1b227a5652e810ddefcd7f198e9319282849a6aa818`):
all three W6 seeds `admitted=True`, `certified=True`, oracle `Masked`,
terminal `full`/L5, 268 events, no truncation, gzip/stats/exit OK.
W6 has only 2 eligible fills, so seeds 1/3 sample the first
(tick 34086360) and seed 2 the second (34091365) — two distinct injection
points by pigeonhole, each an independent RNG draw. W8 (eligible=5) still
has no downstream consumer and stays `provable_to_L1_then_unknown`,
not admitted. No SDC is claimed: the W6 guest output hash remains the
golden `062e5124df3667f9`, and the real `errant_commit` is a tainted
commit whose value did not change the final output.

## 1. Model

Sheet 03 P07: the prefetch response's fill tag / target way / valid / data
write pairing. P07-b = the tag is written to the wrong way. Implementation
at the REAL fill point (`BaseCache::handleFill`), gated by the same
fill-time pure-prefetch marker as P09 (`FromPrefetcher` and no
`FromCPU`/`FromSnoop`; cleared immediately after the fill):

- enumerate the filled block's set with `BaseTags::getNumWays` +
  `findBlockBySetAndWay` (no hardcoded geometry);
- require a distinct, valid, same-secure partner (tag differs);
- on trigger consent, exchange the two blocks' **tags** via
  `TaggedEntry::chaosSetTag`; data stays in its own way. This is the exact
  tag/data mispair of P07-b, not a classic cache-tag approximation.
- unit-side L1 kind `pf_tag` (schema v1): set/way, both line addresses,
  `field=fill_way_tag`, `state_after=tag_mispair`. Both lines are
  registered for downstream correlation.
- the old `P07 -> l1d_target_field=tag` campaign routing is removed.

## 2. B0 census (binary `gem5.opt-ebd61101`, sha256
`ebd611014b74afbfcba2d125dea5d8591ffdc75c07ce41fc7840cce446457934`)

| W | attempted | eligible |
|---|---|---|
| W6 cache_dirtyevict | 2 | 2 |
| W8 prefetch_stride | 5 | 5 |

Evidence `runs/lsu/r6_p_unit/census_p07_20261104/`. Frozen `warmup=1`;
seed1 spans W6=2, W8=5. `runs/lsu/r6_p_unit/campaign_p07_20261104/`.

## 3. Seed1 real behavior

W6 (`P07-F0-W6`, tick 34086360):

```
Site: P07_fill_tag_mispair ... pf_addr=0x7ec00 fill set=944 way=1
      -> partner set=944 way=0 (tags swapped; data stays in its way)
PROP-EVT kind=pf_tag va=7ec00 set=944 way=1 entry_index=0
      field=fill_way_tag before=7ec00 after=8ec00 state_after=tag_mispair
```

After the swap, demands to `0x7ec00` (`cache_access`/`pf_demand`) miss and
refill from memory; the chain checker reports `terminal=full`,
`provable_to=L5` via address-correlation bridges. **The workload output
hash is `062e5124df3667f9`, identical to the no-fault golden**, so this is
not an output-visible SDC; the direct run has no campaign oracle (n/a).

W8 (`P07-F0-W8`, tick 107338770): fill `0x76740` set=413 way=1, partner
`0x86740` way=0, same `pf_tag`; no downstream demand on either line was
observed, terminal `provable_to_L1_then_unknown`; output hash
`629727c0ad9ca8ef` = golden.

Both seeds: gzip EOF, stats non-zero, exit 0. Chain terminal is quoted
exactly; no L5/SDC is invented.

## 4. Honest boundary

- Seed1 only; seeds 2/3 not run, no certification, no RunID/seed count.
- W6's checker L5 is a real correlation to an errant commit, but the
  output is unchanged; this is recorded as terminal `full` **without** an
  SDC claim, and the direct-run oracle is n/a.
- P07-a (data written to the wrong way) and P07-c (old tag/valid) are not
  implemented.
- B0 W6/W8 did not produce an output-visible error in these seeds; a
  larger/bounded seed sweep would be the next step if certification is
  pursued.

---

## P07-a data written to the wrong way — implementation and seed1 pilot (2026-11-05)

**Status: IMPLEMENTED / BEHAVIOR-VERIFIED PILOT / NOT CERTIFIED.**
The landed arm is P07-a (response data written to a different way). P07-b
(tag mispair) is unchanged and certified for W6; P07-c (old tag/valid) is
not implemented this pass.

### Model

At the SAME real pure-prefetch fill gate as P07-b, the fill block and a
distinct valid same-set partner (same secure bit, different tag) exchange
their **data arrays** (`blk->data` ↔ `partner->data`); the **tags stay in
their own ways**. The response bytes therefore land under the partner's
tag while the fill way keeps the partner's old bytes. This is the
authoritative P07-a "把 data 写入 way A、tag 写入 way B" composition — the
spec's legal "exchange" rule, with every input fragment preserved and only
the composition/way changed. It is not a tag fault (P07-b) and not a
generic cache-tag substitution.

The fill hook now returns `FillMispair` (`None` / `Tags` / `Data`) so one
fill books exactly one attempt: `maybeMispairFill` is the single attempt
stream for both P07-b and P07-a.

### Binary / census / evidence

- Binary: `CHAOS/gem5/build/ARM/gem5.opt`, sha256
  `0f21b4c4a86c51effb7dca135485f278dcb3496cf288b2bcd0eab6fd0c4fddc0`,
  source `4b701bd4` + this patch; build exit 0, zero warnings
  (`/tmp/p07a_build.log`).
- No-fault census (same mode mounted, warm-up 1, span 1e9): the eligible
  stream is unchanged from the P07-b census — W6 attempted=2 eligible=2,
  W8 attempted=5 eligible=5; controls reproduce both goldens
  (`062e5124df3667f9`, `629727c0ad9ca8ef`) with `injected=0`.
- Pilot (span 2 / 5, seed 1): `campaign_p07a_20261105`.

### Real behavior (seed1)

```
W6: Site: P07_data_wrong_way Tick: 34086360 pf_addr=0x7ec00 fill set=944 way=1 -> partner set=944 way=0 (data arrays swapped; tags stay in their way)
W8: Site: P07_data_wrong_way Tick: 107338770 pf_addr=0x76740 fill set=413 way=1 -> partner set=413 way=0 (data arrays swapped; tags stay in their way)
```

Propagation: `pf_data` (`field=fill_data_way`, before=fill way, after=
partner way, `state_after=data_wrong_way`, both lines registered under
the same fault). W6 chain reaches a real `errant_commit` (`pc=0x400620`,
`commit_seq=81793`, tick 45204775, detection_layer=L5) — checker terminal
`full`/L5 — but the workload output hash stays golden
`062e5124df3667f9`, so **no SDC is claimed** (the tainted commit has no
output effect). W8: fill 0x76740↔0x86740, no downstream demand observed;
terminal `provable_to_L1_then_unknown`, output golden
`629727c0ad9ca8ef`.

### Honesty boundary

- Pilot only (seed 1); seeds 2/3 not run; NOT certified.
- W6's L5 is a real tainted commit, not an output change; the oracle is
  Masked and no SDC claim is made.
- W8 has no downstream consumer; terminal L1 is recorded as-is.
- P07-c (old tag/valid) remains unimplemented; the classic cache-tag
  routing stays removed.

### P07-F0-W8 coverage probe (2026-11-05)

The P07-F0-W8 RunID is not admitted because the faulted fill has no later
demand. To distinguish a sampling artifact from a workload-coverage block,
seeds 2 and 3 were run with the certified P07-b arm (warm-up 1, span 5):

```
seed2: Site: P07_fill_tag_mispair Tick: 107338770 pf_addr=0x76740 set=413 way=1 -> partner way=0
seed3: Site: P07_fill_tag_mispair Tick: 107333380 pf_addr=0x767c0 set=415 way=1 -> partner way=0
```

Both terminate `provable_to_L1_then_unknown` (seed1: same terminal at
0x76740). Three distinct activation points, no downstream consumer on any
of them — the W8 block is a real workload-consumption block, not a
seed-sampling artifact. Evidence: `campaign_p07_w8probe_20261105`. No L5
was borrowed from another branch.
