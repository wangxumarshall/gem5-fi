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

## Units (one commit each)

### Unit 1 — `[LSU][MDSPEC][R6-TLB]` L0 inj records its before/after + registry for containment
- [ ] Test (RED first): extend `tests/test_lsu_hook_tlb_observation.py` with `[R6-C]` checks →
      run, quote real FAIL.
- [ ] `CHAOSPropagation.hh`: register `containment_layer`, `containment_reason` in
      `PROP_EVT_FIELDS`; add `containment_ptags` member.
- [ ] `registerTlbFault`: inj detail carries `old_addr`/`new_addr` (lifted → before/after).
- [ ] `registerTlbStateFault` / `registerTlbWalkPair`: inj carries explicit `before`/`after`.
- [ ] `noteTlbTranslationResult` + lost-walk L2 node: emit `containment_layer`/`containment_reason`
      when contained; record in `containment_ptags`.
- [ ] `errant_commit` writeNode detail carries `detection_layer=L5;outcome=errant_commit`
      (corr stays `taint_prop`, the chain join).
- [ ] `chain_end` exit callback: report per-chain containment (`detection_layer`/`contained`/
      `containment_layer`/`containment_reason`) so a contained chain is a CLOSED terminal.
- [ ] GREEN: quote real ALL PASS.
- [ ] Build: `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` (wait if another scons runs).
- [ ] Smoke pilot `T02-F0-W4` → `runs/lsu/r6_tlb_A_T02-F0-W4`; quote inj/errant_commit/chain_end.
- [ ] Regression: `tests/test_lsu_hook_tlb.py`, `tests/test_lsu_hook_t08_pairing.py`.
- [ ] Commit + `git push -u origin r6-tlb-hooks`; write `docs/gem5-fi/lsu/mdspec/R6-TLB-A-report.md`
      and copy summary to `runs/lsu/r6_reports/L1.md`.
