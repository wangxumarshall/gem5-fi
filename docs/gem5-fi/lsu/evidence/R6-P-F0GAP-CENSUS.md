# R6-P F0-gap census — exact absolute command (2026-11-04)

**Why re-census:** the P06 span table was measured with a *relative* `--cmd
workloads/directed/<wl>` census, while the campaign runs the guest with an
**absolute** `--cmd /.../workloads/directed/<wl>`. In gem5 SE the argv[0]
string is part of the initial stack image; it shifts stack/cache placement
and is timing-visible. The same lesson is already recorded for
`LSQFWD_F0_SPAN` in `tools/lsu_campaign.py`. The old P06 values (W6=56,
W8=32) are therefore *not* the formal eligible stream.

**Binary:** `runs/lsu/r6_p_unit/binaries/gem5.opt-8a2778d4`
(sha256 `8a2778d4d32644dbb02355ee90a95b3107b56af31723811f663da8940d283204`,
source head `3f0a5589`).

**Census command (both workloads; span=1e9 so the F0 draw can never land):**

```bash
CHAOS/gem5/build/ARM/gem5.opt \
  --outdir=/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/census_abs_20261104/P06_<wl> \
  configs/se/lsu_proxy.py \
  --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-p-unit-20261104/workloads/directed/<wl> \
  --cpu O3 --chaos_prefetch --prefetch_mode p06_as_demand \
  --prefetch_lsu_tier F0 --prefetch_warmup_events 1 \
  --prefetch_span_events 1000000000 --prefetch_max_faults 1 \
  --prefetch_rng_seed 1 \
  --chaos_propagation --prop_run_id P06-SPAN-<wl> --prop_sample_run_id s1
```

**Quoted teardown (real output):**

```
P06_prefetch_stride (W8):
CHAOS_LSU_TRIGGER: injector=CHAOSPrefetch tier=F0 attempted=28 eligible=28 injected=0 first_eligible_tick=724570 last_eligible_tick=107877385 fires=n/a no_effect=n/a (activated=W3-L0-layer)
CHAOS_LSU_TRIGGER_ALARM: injector=CHAOSPrefetch mode=SPAN_UNREACHABLE attempted=28 eligible=28 injected=0 draw_next_fire=735756413 span=1000000000 warmup=1 (F0 draw never landed inside the observed eligible stream; no injection though the hook fired)
golden hash: 629727c0ad9ca8ef

P06_cache_dirtyevict (W6):
CHAOS_LSU_TRIGGER: injector=CHAOSPrefetch tier=F0 attempted=50 eligible=50 injected=0 first_eligible_tick=838915 last_eligible_tick=58170035 fires=n/a no_effect=n/a (activated=W3-L0-layer)
CHAOS_LSU_TRIGGER_ALARM: injector=CHAOSPrefetch mode=SPAN_UNREACHABLE attempted=50 eligible=50 injected=0 draw_next_fire=735756413 span=1000000000 warmup=1 (F0 draw never landed inside the observed eligible stream; no injection though the hook fired)
```

**Frozen selection rule (pre-registered):**

- Definition: eligible = the mounted cache's prefetch-owned fills that pass
  the `setPrefetched` gate's legal-candidate test (`from_pref && !from_core
  && blk`), measured with the campaign's exact absolute command.
- `warmup = 1`; `span = N` where `N` is the measured eligible count.
- Then `next_fire = 1 + lcg(seed) % N ∈ [1, N]`: every eligible event is hit
  with probability `1/N` and the draw is guaranteed to land (`next_fire ≤ N`).
- Frozen values: `P06/cache_dirtyevict = 50`, `P06/prefetch_stride = 28`.
- No further span changes are allowed after the seed runs start; any change
  requires a new pre-registered census and a new evidence directory.

**Why the old W8 failed:** formal seed1 used span=32 and drew
`next_fire=29`, but the absolute-command stream has only 28 eligible events
→ `attempted=28 eligible=28 injected=0` + `SPAN_UNREACHABLE`. The old
relative census had 32 eligible, which is a different experiment.

**W6 effect:** the old span=56 is larger than the 50-event stream; seed1
happened to draw 13 and fired, but other seeds can draw >50 and miss. The
correct guaranteed window is 50.

---

## F0-gap batch result (2026-11-04, new binary)

**Binary:** `runs/lsu/r6_p_unit/binaries/gem5.opt-9dafb090`
(sha256 `9dafb09011cda80cdb295397ed55b97660c4998dc2742654d78ec2dabef269c3`,
source commit `d3f7471ba93349e04b8a893ed52ebab9fe2c0d73`, incremental build
log `r6o-logs/p_f0gap_build.log`/`_build2`/`_build3`, zero new errors).
Evidence: `runs/lsu/r6_p_unit/campaign_f0gap_20261104` (seed1) and
`campaign_f0gap_seed23_20261104` (seeds 2/3).

### Fixes applied

1. **Escape-first path selection** (`tools/lsu_chain_check.py`): among
   equal-length maximal L0→L5 prefixes, the real `errant_commit` lane wins
   over an earlier `squash_masked` lane. P01-F0-W2's old
   `provable_to_L5_then_unknown` was an analyzer selection artifact.
2. **Prefetch-request lineage bridge** (`CHAOSPropagation` + `cache.cc` +
   `base.cc` + checker): the first prefetch-side event of the fault carries
   `pf_request_id`; a later demand `cache_access`/`mshr_fill` on the same
   registered line is joined by one `request_fork` bridge whose
   `old_request_id` is the pfid and `new_request_id` the demand request.
   The checker accepts a pfid source only for family `pf` when the source
   event has no CPU request id; every other bridge clause still applies.
3. **Campaign drift removed** (`tools/lsu_campaign.py`): the campaign's
   local linear path scan was stale and disagreed with the authoritative
   checker on P01-W2; it now delegates to `lsu_chain_check`'s implementation.
4. **Exact-command census** (above): P06 W6=50, W8=28.

### Results (per seed, quoted from `chain_report.json`)

| RunID | seed1 | seed2 | seed3 | verdict |
|---|---|---|---|---|
| P01-F0-W2 | full / admitted | full / admitted | detected_contained / admitted | **3/3 certified** |
| P03-F0-W8 | full / admitted | detected_contained / admitted | full / admitted | **3/3 certified** |
| P03-F0-W9 | L4_then_unknown / not admitted | — | — | local block |
| P06-F0-W6 | full / not admitted (`cache_access_faked_l1`) | — | — | local block |
| P06-F0-W8 | L2_then_unknown / not admitted | — | — | local block |

All six certified seeds: gzip EOF, stats non-empty (1768/1771 lines for the
seed1 pair), `exit_code=0`, not truncated, oracle Masked, `admitted=True` /
`certified=True`. The EARLY_BIAS trigger alarms are retained and adjudicated
against the measured no-fault eligible counts (P01 W2=142; P03 W8=7).

### Local-block reasons (no admission relaxation)

- **P03-W9**: the only errant_commit is on a different line (`0x80080`) with
  no lineage bridge from the faulted prefetch (`0x7fcc0`); the checker refuses
  cross-branch stitching. The other branch's L5 is not borrowed.
- **P06-W6**: the demand hit on the marked line is real and now linked (full
  chain), but admission is blocked only by `cache_access_faked_l1` (pf-family
  L1 must be the unit observation; P06-a's fill classification has no separate
  unit-side L1 event and the P06 contract forbids a new kind). Admission was
  not loosened.
- **P06-W8**: injection is fixed (attempted=13, injected=1), but the demand
  access precedes the prefetch fill, so no forward pf source exists; the chain
  remains L2 and is also blocked by the same pf-L1 rule.

The old failed evidence under `campaign_seed1_20261104/` is retained; only
these five RunIDs are superseded by the new batch.

### Supersession note (2026-11-04, schema-v2 batch)

The P06-F0-W6/W8 rows in the table above describe the F0-gap batch
(`9dafb090`): at that point the pf-family L1 gate still rejected the chain
and W8 remained at L2.  The **P06 schema-v2 batch** (`4f3db315`, source
`05793493`) supersedes those two rows: both RunIDs are now 3/3
admitted/certified. See `R6-P-P06-SCHEMA2-EVIDENCE.md`. The P03-W9 row is
unchanged and remains a local block.
