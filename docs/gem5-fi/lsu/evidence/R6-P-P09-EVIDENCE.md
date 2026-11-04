# R6-P-P09 — prefetch-caused dirty-writeback loss (P09-a)

**Status: IMPLEMENTED / RUNTIME-VERIFIED DIAGNOSTIC / NOT A RUNID.**
The authoritative B0 W6/W8 runs have **zero eligible events** (prefetch fills
exist but none evicts a victim), so P09-F0-W6/W8 remain BLOCKED by workload
coverage. The model is nevertheless proven end-to-end on an explicitly
non-authoritative L2=16KiB diagnostic control (real writeback suppression →
stale re-read → taint → errant commit / SDC).

## 1. Authoritative model

Sheet 03 P09: the victim selection, dirty-victim writeback request, and
completion handshake **caused by a prefetch allocation**. P09-a = the
writeback request is lost. The victim tag/data are unchanged; the prefetch
transaction and victim line must be recorded. Substitution with a classic
cache `dirty` fault is forbidden (and has been removed from `MODEL_FLAGS`).

## 2. Fill-time pure-prefetch marker (the known gap)

`from_pref` is only computed in `Cache::serviceMSHRTargets`, which runs
**after** `handleFill` (and therefore after the victim eviction). The model
therefore classifies the fill at the real fill point from the MSHR's own
target sources:

- new `MSHR::hasTargetFrom(Source)` scans both `targets` and
  `deferredTargets`;
- `BaseCache::recvTimingResp` sets `chaosFillFromPrefetch` iff the filling
  MSHR has a `FromPrefetcher` target and **no** `FromCPU` / `FromSnoop`
  target (a demand-merged fill is deliberately not marked);
- the marker is cleared immediately after `handleFill`, so an eviction in
  any other fill can never inherit a stale marker;
- `Cache::evictBlock` consults the P09 hook only while that marker is true.
  For a dirty victim the hook may suppress the writeback packet: the line
  is invalidated **without** any writeback.

Attempted is every victim eviction during a pure-prefetch fill; eligible is
a **dirty** victim (clean-victim evictions are Injected-not-activated).

## 3. B0 result — real zero-eligible (not a model absence)

Binary `runs/lsu/r6_p_unit/binaries/gem5.opt-c6953bba`, sha256
`c6953bba69f7c97634d02c5be8e67629de05017d14708e87cb90cc866a26b0bc`,
source head `88c1d697` + this patch. Evidence
`runs/lsu/r6_p_unit/census_p09_20261104_v4/`.

| W | fills | pure-prefetch fills | prefetch evictions | dirty |
|---|---|---|---|---|
| W6 cache_dirtyevict | 3489 | 50 | **0** | **0** |
| W8 prefetch_stride | 17913 | 28 | **0** | **0** |

Trigger: `attempted=0 eligible=0 injected=0` on both. So the 1 MiB B0 L2
absorbs/clips every pure-prefetch fill (no victim allocation), and the
authoritative P09-F0-W6/W8 RunIDs cannot be exercised by this workload
configuration. This is a workload-coverage block, recorded as such; no
substitution probe is used.

## 4. Non-authoritative diagnostic control (L2 = 16KiB)

To verify the model itself fires and produces the intended effect, the L2
capacity was reduced via the diagnostic-only `--l2_size` knob (default
1 MiB = B0; the run prints a non-B0 warning). This control is **not a
RunID**, contributes no seed/RunID count, and its oracle is **n/a**
(direct run, no campaign classification).

No-fault census (`p09_diag_l2small_20261104b/16KiB`):
`fills=4576 pure_pref_fills=634 pref_evictions=595 dirty_pref_evictions=378`.
Frozen `warmup=1, span=378`; output hash `062e5124df3667f9` (the B0 W6
golden, so the smaller L2 did not change the no-fault result).

Fault run (`p09_diag_l2small_fault_20261104/P09-DIAG-W6-L2_16KiB/seed1`):

```
CHAOS_LSU_TRIGGER: ... attempted=175 eligible=167 injected=1 ...
Site: P09_wb_loss Tick: 49447090 pf_addr=0x7e740 dirty victim set=13 way=4 writeback request dropped
```

Real event chain (same `fault_id=1`, same line `0x7e740`):

1. `pf_wb` (unit-side L1): `field=wb_request before=pending after=lost`,
   `state_after=writeback_suppressed`, `set=13 way=4` (tick 49447090).
2. `cache_evict`: `field=dirty_evict_writeback`,
   `state_after=writeback_suppressed` (same tick). No `cache_writeback`
   packet exists at this eviction.
3. Demand re-read of the same line misses (`cache_access` + `pf_demand`,
   tick 52951745) and re-fills `0x7e740` from the stale backing data.
4. `taint_reg` (tick 53006030) and a real `errant_commit` at
   `pc=0x400620, dyn_inst_seq=90383, commit_seq=81337` (tick 53006800,
   `detection_layer=L5`).
5. Chain checker: fault 1 `terminal=full`, `provable_to=L5`,
   path `0 -> 1 -> 7 -> 34 -> 36 -> 40`.
6. Workload output hash `8e64d8d4427c2169` vs no-fault
   `062e5124df3667f9` — a real SDC in this diagnostic control.

A later `cache_writeback` of `0x7e740` appears at tick 62665295, i.e.
**after** the stale re-fill and the errant commit; it writes back the stale
copy, not the original dirty value. It is not a counterexample to the loss
at 49447090.

`gzip -t` passes for both streams, `stats.txt` is 1822 lines, exit 0, no
truncation.

## 5. Honest boundary

- The B0 authoritative RunIDs are **not** certified and are not claimed as
  SDC: zero eligible events at 1 MiB L2.
- The diagnostic control is non-B0 and is not a RunID/seed; its oracle is
  n/a. It proves the fault semantics and the end-to-end loss path, not a
  B0 result.
- P09-b (done-early) and P09-c (dirty premature clear) are not implemented.
- P09-F0-W13 (PARSEC) remains BLOCKED_ASSET.
- Intermediate binaries `24f0b5c0` (generation-site fall-through spent the
  fault budget) and `f696c48f` (early-return fix, no eligible found) are
  retained but are **not** cited as evidence; `c6953bba` is the final
  diagnostic binary.
