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
