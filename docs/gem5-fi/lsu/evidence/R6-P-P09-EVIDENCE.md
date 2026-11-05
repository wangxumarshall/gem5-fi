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
  **not** cited as evidence; `c6953bba` is the final diagnostic binary.
  On 2026-11-05 the non-evidence intermediates (`24f0b5c0`, `f696c48f`,
  `587ea8c3`, `9cb528d9`) were removed during the 0101 disk cleanup; their
  sha256 identities are retained in `R6P_UNIT_STATE.json` and the cleanup
  manifest `DISK-CLEANUP-20261105.md`. No evidence stream references them.

---

## P09-c dirty premature clear — implementation and diagnostic (2026-11-05)

**Status: IMPLEMENTED / RUNTIME-VERIFIED DIAGNOSTIC / NOT A RUNID.**
The authoritative B0 W6/W8 coverage block is unchanged (the eligible
stream is the same: a prefetch allocation must evict a dirty victim; 1 MiB
B0 L2 has zero such events), so P09-F0-W6/W8 still cannot be certified.
This submodel is proven end-to-end on the same explicitly non-B0
L2=16KiB diagnostic control as P09-a.

### Distinct faulted field (not a relabel of P09-a)

Both submodels target the prefetch-caused dirty victim, but a different
field is faulted and a different real state transition is applied:

| | P09-a writeback loss | P09-c dirty premature clear |
|---|---|---|
| faulted field | writeback request | the victim's dirty state |
| real operation | request is created, then destroyed (packet suppressed) | `DirtyBit` cleared **before** the eviction decision |
| eviction packet | none (dirty_evict_writeback suppressed) | `CleanEvict` (no writeback request is ever generated) |
| unit-side L1 event | `pf_wb` (pending → lost) | `pf_dirty` (dirty → clean) |
| `cache_evict` | `dirty_evict_writeback`, `writeback_suppressed` | `clean_evict`, `dirty_premature_clear` |
| writebacks stat | not incremented | not incremented (different code path) |

The eviction gate now returns a `VictimAction` (`None` / `DropWriteback` /
`ClearDirty`) and `Cache::evictBlock` applies the real operation; the
packet decision then sees the post-fault state. This is a real storage
semantic, not a log-only change.

### P09-b (done early) — local model block, not implemented

The authoritative P09-b is "提前报告 writeback done". This platform has
no such completion handshake at the authoritative site:

- `BaseCache::writebackBlk` creates a `WritebackDirty` packet and clears
  the block's `WritableBit`/`DirtyBit` at **creation** (base.cc:2214–2224);
  the L1D has no "pending writeback completion" state for that line — the
  line is invalidated immediately (`invalidateBlock`).
- The only completion notion is the lower-level write-buffer acceptance
  (`WriteQueue` deallocation), which is internal buffer bookkeeping, not a
  reportable transaction outcome; forcing an early free would corrupt the
  queue rather than model an acknowledged-but-not-committed write.
- The other state that could carry "done" is the dirty state, and clearing
  it early is exactly P09-c.

Therefore P09-b is recorded as **MODEL_NOT_EXPRESSIBLE_AT_SITE** rather
than implemented as a relabel of P09-c. No log-only or counter-only
approximation is used.

### Binary / command / control

- Binary: `CHAOS/gem5/build/ARM/gem5.opt`, sha256
  `c8b0e25f4f2fff41afef5843bddd63884040f6f033997c9a4daeb4896d2ced64`,
  source `31bbc94b` + this patch; build exit 0, zero warnings
  (`/tmp/p09c_build.log`).
- Exact command (fault), same shape as the P09-a diagnostic:
  `--chaos_prefetch --prefetch_mode p09_dirty_clear --prefetch_lsu_tier F0
  --prefetch_warmup_events 1 --prefetch_span_events 378
  --prefetch_max_faults 1 --prefetch_rng_seed 1 --chaos_propagation
  --prop_run_id P09C-DIAG-W6-L2_16KiB --prop_sample_run_id s1
  --l2_size 16KiB`.
- Control: identical, `--prefetch_span_events 1000000000` (never fires),
  output golden.

### Real event chain

Fault run `p09c_diag_l2small_fault_20261105/P09C-DIAG-W6-L2_16KiB/seed1`:

```
Site: P09_dirty_clear Tick: 49447090 pf_addr=0x7e740 dirty victim set=13 way=4 dirty state cleared before eviction (no writeback request generated)
pf_dirty  set=13 way=4 field=dirty_state before=dirty after=clean state_after=dirty_premature_clear  (tick 49447090)
cache_evict set=13 way=4 field=clean_evict state_after=dirty_premature_clear                       (tick 49447090)
```

Then: same-line demand miss/re-read, `taint_reg` (tick 53006030), real
`errant_commit` (pc=0x400620, commit_seq=81337, detection_layer=L5, tick
53006800); chain checker `full`/L5; workload output
`8e64d8d4427c2169` vs control `062e5124df3667f9` — a real SDC in this
non-B0 diagnostic. The only `cache_writeback` of the line is at tick
62665295 (the stale re-fill, after the errant commit). The trigger
`attempted=175 eligible=167 injected=1`; gzip intact, stats 1822 lines,
exit 0, no truncation. The control's no-fault census (fills=4576,
pure_pref_fills=634, pref_evictions=595, dirty=378) reproduces the
previously frozen diagnostic shape and the B0 golden.

### Honest boundary

- P09-c is a non-B0 diagnostic control, **not a RunID/seed**; its oracle
  is n/a. It does not change the B0 coverage block for P09-F0-W6/W8.
- P09-b is a recorded model block, not a silent approximation.
- The authoritative P09 RunIDs remain NOT certified.
