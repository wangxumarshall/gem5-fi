# A01 8-byte eligible-stream census (v3.3.3 correction, ledger L-A12)

**Binary:** `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
**Command:**
```
build/ARM/gem5.opt --outdir=audit_v3_3_3/census/A01_8B \
  configs/se/lsu_proxy.py --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/agu_addrmodes \
  --cpu O3 --variant B0 --probability 1.0 --chaos_addrpath \
  --agu_pre_mode a01_bit3_load --addrpath_lsu_tier F0 --addrpath_max_faults 0 \
  --addrpath_warmup_events 0 --addrpath_span_events 1000 \
  --addrpath_rng_seed 2108120075 --addrpath_count_only
```

**Result:** `CHAOS_LSU_TRIGGER: attempted=2775 eligible=817 injected=0`.
The `addrpath_injections.log` contains 817 `CHAOS_ELIGIBLE` lines, all `size=8`
(the A01 filter excludes the 16-byte vector load and all non-8-byte loads).

**Main-loop window:** ordinals `585–713`, N=`129`; every event in the span has a
PC in `main` (`0x400538..0x400748`), no interleaved non-main events. The first
main event is `585 (0x400578, seq 12488, ea 0x493020)`; the last is
`713 (0x4006d0, seq 15043, ea 0x493100)`.

**Percentiles (`start + ceil(p*N) − 1`):**

| Context | p | Ordinal | PC | size | EA |
|---|---:|---:|---|---:|---|
| R01 | 0.10 | 597 | `0x400578` | 8 | `0x493020` |
| R02 | 0.30 | 623 | `0x4005e0` | 8 | `0x4930f0` |
| R03 | 0.50 | 649 | `0x4006d0` | 8 | `0x493200` |
| R04 | 0.70 | 675 | `0x4006d0` | 8 | `0x4932d0` |
| R05 | 0.90 | 701 | `0x4006d0` | 8 | `0x4933a0` |

**Correction smoke (R03, ordinal 649):** injection=1, `a01_ea_discarded`=0,
`register_writeback`=1, `commit`=1, `errant_commit`=1, `a01_consumed`=1,
272 `consumer_commit` events; oracle FAIL, terminal `SDC`; control injection=0,
oracle PASS, golden `728e604ffcec539d`.

The earlier all-load window `1040–1222 (N=183)` is superseded for A01 only;
A03 remains size-agnostic and keeps its `1040–1222 (N=183)` re-census.
