# R6-EMIT2 — store-chain L4/L5 (A7) + L3 event identity (A3) + lq_read request_id (A9) + oracle crash/abort field contract

Lane L27. worktree `.claude/worktrees/r6-emit2`, branch `r6-emit2`, base `56993c80` (`r6-tlb-hooks`).

Owned files (nothing else may be touched):
- `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{cc,hh}`
- `CHAOS/gem5/src/mem/cache/cache.cc`, `CHAOS/gem5/src/mem/cache/base.cc`
- `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`
- `tests/test_lsu_hook_sq.py`, `tests/test_lsu_hook_l04.py`, `tests/test_lsu_hook_c11.py`, `tests/test_lsu_hook_c12.py`
- `runs/lsu/r6_reports/L27.md`

Method: TDD per gap (extend the owned test → RED quoted → implement → GREEN quoted).
One build (`scons -j16 build/ARM/gem5.opt`), one smoke pilot, then regression.

## Task 1 — A7: store chains reach L4/L5
- [ ] RED: extend `tests/test_lsu_hook_sq.py` with (a) a synthetic store chain
      `inj..sq_complete → taint_reg → errant_commit → chain_end` asserting
      `terminal=="full"`; (b) source pins on `CHAOSPropagation.cc` for the
      store taint path (`inst->isStore()` store branch + `store_taint` +
      `faulting_store_commit`). Quote the real FAIL.
- [ ] GREEN: `CHAOSPropagation.hh` add `std::map<uint64_t, TaintEntry> store_taint;`
      (keyed by the store's dyn seq). `noteMemResponse` emits the L4 `taint_reg`
      for a store response (`!wb_to_reg && inst->isStore()`) and records the
      store taint. `noteCommit` treats a committing tainted store as self-taint
      → `errant_commit` (`trigger=faulting_store_commit`) and binds `errant_ptags`.
- [ ] Verify: `python3 tests/test_lsu_hook_sq.py` PASS.

## Task 2 — A3: L3 cache/memory events carry identity
- [ ] RED: extend `tests/test_lsu_hook_c11.py` with source+contract pins: every
      cache structural emit (`cache_access`,`cache_return`,`mshr_merge`,
      `mshr_alloc`,`mshr_fill`,`cache_fill`,`mshr_free`) writes `dyn_inst_seq`
      and `request_id` from `pkt->req`. Quote the real FAIL.
- [ ] GREEN: `cache.cc` (cache_access ~194, cache_return ~240) and `base.cc`
      (mshr_merge ~462, mshr_alloc ~553, mshr_fill/cache_fill/mshr_free
      ~1849-1865) add `dyn_inst_seq`/`request_id` from
      `pkt->req->hasInstSeqNum() ? getReqInstSeqNum() : 0`.
- [ ] Verify: `python3 tests/test_lsu_hook_c11.py` PASS (and c12 still PASS).

## Task 3 — A9: lq_read request_id
- [ ] RED: add an A9 section to `tests/test_lsu_hook_sq.py` pinning
      `request_id` in the `lq_read` emit at `lsq_unit.cc:1574`. Quote FAIL.
- [ ] GREEN: `lsq_unit.cc` lq_read adds `{"request_id", ...}` (request-stamped
      seq, else `load_inst->seqNum`).
- [ ] Verify: `python3 tests/test_lsu_hook_sq.py` PASS.

## Task 4 — oracle crash/abort field contract
- [ ] RED: add a section to `tests/test_lsu_hook_sq.py` pinning (1) `chain_end`
      writes `fault_id/commit_seq/pc/dyn_inst_seq/detection_layer/contained/outcome`;
      (2) `errant_commit` writes `contained`; (3) a `CHAOS_DETECT:` stdout line is
      emitted on the detection path (`layer`/`contained`/`tick`/`ptag`/`reason`).
      Quote FAIL.
- [ ] GREEN: `CHAOSPropagation.cc` — maintain a tracer commit counter
      (`commit_seq`), remember the errant commit's (pc/seq/commit_seq) per ptag,
      lift them onto `chain_end`; add `contained=0` to the `errant_commit` node;
      add `emitDetectSignal()` printing
      `CHAOS_DETECT: layer=<..> contained=<0|1> tick=<n> ptag=<n> reason=<..>`
      at errant_commit (layer=None contained=0) and at every containment
      recording (layer=Hardware RAS contained=1).
- [ ] Verify: `python3 tests/test_lsu_hook_sq.py` PASS.

## Task 5 — build + smoke pilot + regression
- [ ] `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` (repo-root binary), no new warning.
- [ ] Smoke pilot S04-F0-W5 → `runs/lsu/r6_sq2_S04-F0-W5`; quote the real
      store-path lines proving L4/L5.
- [ ] Regression: `tests/test_lsu_hook_sq.py`, `l04`, `tlb`, `c11`, `c12`.
- [ ] Commits per unit `[LSU][MDSPEC][R6-EMIT2] ...`; `git push -u origin r6-emit2`.
- [ ] Report `runs/lsu/r6_reports/L27.md`.
