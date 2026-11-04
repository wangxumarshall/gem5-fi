# R6-P-P07 — prefetch-response fill tag/way mispair (P07-b)

**Status: IMPLEMENTED / SEED1 PILOT / NOT CERTIFIED.**
The authoritative B0 W6/W8 runs have a real eligible stream (W6=2, W8=5
pure-prefetch fills with a distinct same-set partner). The seed1 pilots
show the real tag exchange and subsequent demand misses, but the workload
output hashes stay at the golden values, so **no SDC is claimed**; seeds
2/3 were not run.

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
