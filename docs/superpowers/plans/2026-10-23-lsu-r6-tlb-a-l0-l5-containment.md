# R6-TLB (Lane A) — L0 inj before/after + real L5 detection + explicit containment

Date: 2026-10-23
Branch: `r6-tlb-hooks` (worktree `.claude/worktrees/r6-tlb-hooks`)
Owner files (only): `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/*`, `CHAOS/gem5/src/arch/arm/mmu.cc`,
`CHAOS/gem5/src/cpu/o3/CHAOSPropagation/*`, `tests/test_lsu_hook_tlb_observation.py`.
`tools/**` is NOT owned by this lane.

## Evidence (real, linear parent DAG)
`runs/lsu/r6_tlb_pilot2/T04-F0-W4/seed1/prop_evt.txt.gz`:
- `kind=inj ... field=pfn_to_mapped_page before= after=`  ← GAP-1 (L0 records no before/after)
- `kind=errant_commit ... detection_layer= contained= outcome= corr=taint_prop dyn_inst_seq=391` ← GAP-2
- `kind=chain_end ... detection_layer=None contained=0 outcome=errant_commit_seen corr=none`

## Binding rulings
- L5 evidence = the REAL detection event (`errant_commit`), never a lifecycle `chain_end` alone.
- No `Unknown` at any layer: a contained chain must close with explicit `containment_layer` +
  `containment_reason` and its later layers justified N/A(contained).
- `Masked` (= corruption absorbed, effective PA unchanged) must record its containment layer+reason.

## Gap list A1–A10 (from the lane brief) and their disposition

| # | Gap | Disposition |
|---|-----|-------------|
| A1 | L0 `inj` has EMPTY before/after | **CLOSED** (unit 1) |
| A2 | L5 unlabeled (`errant_commit` empty; `chain_end` alone) | **CLOSED** (unit 1) |
| A3 | L3 cache events lack `request_id`/`dyn_inst_seq`/set/way/cache_line | **BLOCKED** — emit sites are `src/mem/cache/{cache.cc,base.cc}` (not owned by this lane) |
| A4 | `taint_reg` EMPTY before/after | **CLOSED** (unit 2) |
| A5 | L1 coverage: only 1 `tlb_lookup` with full fields; `way=-1` | **PARTIAL/BLOCKED** — post-lookup emission for non-injected fault-correlated lookups needs the ArmTLB post-lookup hook to fire per access (see below) |
| A6 | `parent_event_id == event_id-1` for every event (linear, not a DAG) | **CLOSED (consumer edges)** (unit 2) |
| A7 | store chains have NO L4 (taint gated to loads) | **NOT DONE** — see remaining work |
| A8 | store L5 is a stub (`run_end`/None/0) | **CLOSED** as part of unit 1 (per-chain errant/containment reporting replaced the hardcoded stub) |
| A9 | `lq_read` carries no `request_id` | **BLOCKED** — emit site is `src/cpu/o3/lsq_unit.cc` (not owned by this lane) |
| A10 | squashed load silently emits nothing | **CLOSED** (unit 2) |

## Units (one commit each)

### Unit 1 — `[LSU][MDSPEC][R6-TLB]` L0 inj before/after + real L5 detection + explicit containment (A1/A2/A8)
- [x] Test (RED first): `[R6-A]`..`[R6-C]` checks in `tests/test_lsu_hook_tlb_observation.py` →
      10 FAIL quoted (`inj #1 carries an explicit before/after`, `errant_commit names its
      detection layer`, `contained chains close chain_end with a real detection layer`, ...).
- [x] `CHAOSPropagation.hh`: `PROP_EVT_EXT_FIELDS` (`containment_layer`, `containment_reason`),
      `errant_ptags`, `containment_ptags`.
- [x] `registerTlbFault`: inj detail carries `old_addr`/`new_addr` (lifted → before/after).
- [x] `registerTlbStateFault` / `registerTlbWalkPair`: inj carries explicit `before`/`after`.
- [x] `noteTlbTranslationResult`: `containment_layer`/`containment_reason` when contained;
      reason rides `field`, fault rides `outcome` (registered fields only).
- [x] `errant_commit` detail carries `detection_layer=L5;outcome=errant_commit`.
- [x] `chain_end` reports per-chain errant/containment; never invents a layer.
- [x] GREEN: "ALL PASS" (test prints ALL PASS).
- [x] Build: `scons -j16 build/ARM/gem5.opt` → binary 11:46, 0 warnings from owned files.
- [x] Smoke pilot `T02-F0-W4` → `runs/lsu/r6_tlb_H_T02-F0-W4/seed1`; quoted inj/errant_commit/chain_end.
- [x] Regression: tlb / t08_pairing / t05_state / t08_walk / prop_fields → ALL PASS.
- [x] Commit `7d562b71` + pushed to `origin/r6-tlb-hooks`.

### Unit 2 — `[LSU][MDSPEC][R6-TLB]` L4 taint evidence + DAG parent edges + squash containment (A4/A6/A10)
- [x] Test (RED first): `[R6-D]` checks → 6 FAIL quoted.
- [x] `taint_reg` detail lifts `old_addr=clean;new_addr=tainted` → before/after.
- [x] `TaintEntry::src_event`: consumer nodes name the taint-establishing event as
      `parent_event_id` (real DAG fan-out, not `event_id-1`).
- [x] Squashed-load branch emits `squash_masked` (detection_layer=L4, outcome=masked,
      containment_layer/reason) and records `containment_ptags[ptag]`.
- [x] GREEN / build / pilot / regression / commit — see commit message.

### Unit 3 — store L4/L5 (A7) — NOT DONE in this pass
Remaining work (not attempted, budget): in `noteMemResponse`, a store whose response matches a
registered fault (`!wb_to_reg && inst->isStore()`) should emit an L4 node and record the store's
seq in a `tainted_store_seqs` set; `noteCommit` should then treat a committing tainted store as the
`errant_commit` (trigger=faulting_store_commit) so A8's per-chain L5 reporting also covers stores.

## Remaining blockers (loud, with the exact unowned fix site)
- **A3** `src/mem/cache/cache.cc:194,240` and `src/mem/cache/base.cc:462,553,1849-1865`: the cache
  events pass only `fault_id`/`corr`/`va`/`pa`; adding `request_id`/`dyn_inst_seq`/set/way/
  `cache_line` must be done AT THE EMITTER (the `Packet`/`CacheBlk` with that identity lives there,
  not in the tracer). Lane-owned by another lane.
- **A9** `src/cpu/o3/lsq_unit.cc:1574`: `lq_read` has the `RequestPtr` in hand
  (`load_entry.getRequest()` → `getReqInstSeqNum()`); the tracer cannot reconstruct it.
- **A5** the 29 non-injected `tlb_translate` nodes come from `mmu.cc:1334` at translation ENTRY
  (pre-lookup, so entry/way/PA are honestly empty). Emitting a post-lookup `tlb_lookup` per
  fault-correlated access requires the ArmTLB lookup result at that point; the tracer-side
  `noteTlbTranslationResult` already closes the injected lookup but cannot be called for every
  access without a per-lookup hook. `way=-1` on the T02 `tlb_lookup` is the injector's own
  `candidate_way` for a selected-entry bit flip (no candidate way exists by construction).
