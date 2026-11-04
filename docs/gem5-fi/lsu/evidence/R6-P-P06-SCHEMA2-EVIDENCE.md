# R6-P-P06 — monitoring schema v2 (`pf_class`) and 3/3 certification

**Status: P06-F0-W6 / P06-F0-W8 CERTIFIED 3/3 as PARTIAL_SUBMODEL
(P06-a fill classification only).**

## 1. The contract conflict (original text and purpose)

The old contract was an **internal monitoring-schema** rule, not a fault
semantics rule:

- `tests/test_lsu_hook_p06.py` asserted
  `"pf_fill_class" not in P.KIND_LAYER` ("P06 无新 kind"), i.e. the P06
  classification pair was carried only by the `inj` event's `before/after`.
- `tools/lsu_chain_check.py`'s `cache_access_faked_l1` gate requires the
  pf-family L1 to be the **unit's own observation point**, not a cache
  structural event.
- With no unit-side L1 event, the real demand consumer on the marked line
  (a `cache_access`) was the only L1 candidate and the gate correctly
  rejected it.

The fault semantics themselves (one prefetch-owned fill classified
`prefetch -> demand`) were never in conflict with the experiment.

## 2. Resolution: versioned schema revision, not admission loosening

Monitoring schema v2 adds a **real unit-side L1 observation event** at the
fill-classification gate:

- kind `pf_class` (layer L1), fields `fault_id`, `pf_request_id`, `corr`,
  `va`, `field=pf_fill_class`, `before=prefetch`, `after=demand`.
- emitted in `CHAOSPrefetch::maybeMarkFillAsDemand`, immediately after the
  inj registration and the prefetch-request-id allocation (the same real
  fill gate; no fabricated retroactive event).
- the `inj` event still carries the classification pair; the fault model,
  trigger, and cap are unchanged.
- the L1 gate is **not** weakened: `cache_access` remains in
  `_FORCED_L1_KINDS` and is still rejected as pf-family L1 (negative test
  added).
- the `pf_class` event is also the first prefetch-side `pf_request_id`
  source, so the existing lineage bridge connects the real demand consumer.
  This resolves the W8 ordering issue: `pf_class` is emitted at the fill
  gate (t=15592500), before the demand access (t=15982891), so the bridge is
  time-forward even though the prefetch fill completes later.

## 3. Binary / evidence

- Binary: `runs/lsu/r6_p_unit/binaries/gem5.opt-4f3db315`
  (sha256 `4f3db315686908ca9bb290a5c3e15426a52562c696594c4c2a415dd8e45caa2a`,
  source `05793493`).
- Evidence: `runs/lsu/r6_p_unit/campaign_p06_schema2_20261104` (seed1),
  `campaign_p06_schema2_seed23_20261104` (seeds 2/3).
- Exact-command census: P06 W6=50, W8=28 (unchanged from the F0-gap batch).

## 4. Results (all 6 seeds admitted/certified, oracle Masked)

| RunID | seed1 | seed2 | seed3 |
|---|---|---|---|
| P06-F0-W6 | full | full | full |
| P06-F0-W8 | detected_contained | detected_contained | full |

W6 seed1: injection `line=0x76c40`, chain `0 -> 1 -> 65 -> 67 -> 69 -> 97`,
L5 = `errant_commit@t20082370`. W8 seed1: injection `line=0x76c40`, chain
`0 -> 1 -> 10 -> 48 -> 49 -> 69`, L5 = real `store_not_retired@t108107230`
(detected_contained). Seeds 2/3 use different lines/injection ticks
(seed diversity), gzip EOF, stats 1764/1765 lines, exit_code 0, not
truncated.

## 5. Honest boundary

- P06-a only; P06-b/c/d (dirty/ownership/allocate fill permissions) remain
  unimplemented.
- The schema-v2 kind is an observation addition; it does not change the
  experiment fault value, the trigger, or the admission gate. A negative
  test proves that removing `pf_class` makes the same chain fail with
  `cache_access_faked_l1`.
