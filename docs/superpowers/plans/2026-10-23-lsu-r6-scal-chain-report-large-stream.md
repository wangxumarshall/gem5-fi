# L30 — chain-report post-processing is superlinear in event count (R6-SCAL)

Worktree: `.claude/worktrees/r6-scal` (branch `r6-scal`, base `lsu-mdspec-20261019`).
Owner scope: `tools/lsu_campaign.py`, `tools/lsu_l3_propagation.py`,
`tests/test_lsu_campaign*.py`, `runs/lsu/r6_reports/L30.md`.
Explicitly NOT owned: `tools/lsu_chain_check.py`, `tools/lsu_ready_contract.py`, any C++.

## Goal

A multicore FS pilot stream (`runs/lsu/r6_mc_O01-F0-W7/O01-F0-W7/seed1/prop_evt.txt.gz`,
222,057 events, 221,768 of them `kind=consumer`, one `fault_id`) leaves
`write_chain_report` burning CPU for tens of minutes without ever writing
`cell_results.json`. Make that stream produce its chain report in well under a
minute on this host **without changing the chain verdict, layer mapping,
conservation or truncation flags for any stream that already completes**.

## Measured facts (reproduction, this host, 2026-10-23)

* stream: 222,056 parsed events, `truncated=False`, kinds
  `{consumer: 221768, exmon_rmw: 97, exmon_stxr: 97, taint_reg: 34, resp: 28,
  lq_complete: 27, inj: 1, addr_form: 1}`, all `fault_id=1`.
* `lsu_prop_fields.read_events` → 5.2 s. `detect_evidence_truncation` reads the
  stream a **second** time.
* `lsu_chain_check.check_chain` scaling (prefixes of the real stream):
  n=1000 → 1.19 s, n=2000 → 7.31 s, n=4000 → 30.9 s (quadratic+).
* cProfile at n=2000: `check_chain` 16.30 s total, of which
  `_edges_for`/`_best_ordered_path` = 16.27 s (99.8%); inside it
  `_ordered_prefix` 9.48 s + `_ancestry` 6.48 s + `dict.get` 5.59 s.
  Root cause: `_best_ordered_path` calls `_ancestry` + `_ordered_prefix` **once
  per event**; the consumer chain has mean ancestry depth ~100 and grows with
  the index → O(n · depth) = Θ(n²).

## Fix (why it lives in `lsu_campaign.py`)

`_best_ordered_path` is in `lsu_chain_check.py`, which this lane may not edit.
The fix therefore substitutes a **semantics-identical, linear-time** replacement
for that one function while `write_chain_report` calls `check_chain`, so every
other decision step (fault grouping, family inference, edge/layer mapping,
terminal rules) still runs the shipped implementation verbatim.

Key property exploited (greedy-state propagation):
`_ordered_prefix` is a forward greedy scan, so for `ancestry(child) =
ancestry(parent) + [child]` its result is `step(state(parent), child)` where
`state = (next-layer-index, last_tick, selected)`. A single memoised pass over
the parent DAG therefore yields `_ordered_prefix(_ancestry(e))` for every `e`
in O(1) amortised, instead of O(depth); the winner is still the **first** event
in original list order attaining the maximum, so ties break identically.
Cyclic parent graphs fall back to the shipped `_best_ordered_path`.

## Tasks (one commit each)

- [x] **Task 1 — linear-time chain-report path + regression test.**
  Files: `tools/lsu_campaign.py` (new `_linear_best_ordered_path`,
  `_check_chain_linear`; `write_chain_report` uses it),
  `tests/test_lsu_campaign_large_stream.py` (new).
  Verification:
  1. TDD FAIL first: the new test times out / asserts the bound and fails on
     the unpatched `write_chain_report` (quote real output).
  2. TDD PASS after the fix (quote real output).
  3. Equivalence: `chain_report.json` for
     `runs/lsu/r6_tlb_pilot2/T04-F0-W4/seed1` byte-identical before vs after
     (`diff -u` empty, quote it). Same for every other real stream under
     `runs/lsu/**/prop_evt.txt.gz`.
  4. Large stream: full `write_chain_report` on a copy of
     `r6_mc_O01-F0-W7/O01-F0-W7/seed1` completes < 60 s with an unchanged
     verdict shape.
  5. Regression: `python3 tools/lsu_test_runner.py` → no NEW FAIL vs the
     recorded baseline.
  Commit: `[LSU][MDSPEC][R6-SCAL] chain_report 线性化：```
  _best_ordered_path` 逐事件祖先遍历改贪心状态传播（222k 事件流 27min→秒级）
  ```

- [x] **Task 2 — L30 evidence report** (`runs/lsu/r6_reports/L30.md`, `runs/` is
  git-ignored ⇒ evidence file, not a commit).

## Result (2026-10-23)

* Real flow (222,056 events, single linear consumer chain depth(i)=i+1,
  Σdepth=2.47e10, leaves=1): unpatched `write_chain_report` killed by
  `timeout 1200` with **no chain_report.json**; fixed = **WALL 14.2 s /
  CPU 14.2 s**, terminal=full, provable_to=L5.
* cProfile(2k events): `_best_ordered_path` 16.27 s of 16.30 s (99.8%).
* Equivalence: T04-F0-W4/seed1 before-vs-after `diff` **empty**
  (byte-identical); 47 real streams × 2 families = 88 path comparisons and
  full-verdict JSON equality: **0 mismatch**.
* Test: TDD FAIL `FAILED (1): ['线性实现已就位']` → `ALL PASS` (222,007-event
  synthetic shape: shipped >200 s, fixed 8.9 s).
* Suite: PASS 36→37, FAIL 14→14 — **no NEW FAIL**.

## Baseline (recorded before any change, for NEW-FAIL comparison)

`tools/lsu_test_runner.py`: suites=56 ENV=5 FAIL=14 PASS=36 SKIP=1.
FAIL: `pytest::collect`, `tests/test_lsu_campaign_propagation.py`,
`tests/test_lsu_coverage_matrix.py`, `hook_a07`, `hook_c11`, `hook_c12`,
`hook_c14`, `hook_c15`, `hook_cpf`, `hook_l04`, `hook_o0x`, `hook_p06`,
`hook_s10`, `hook_sq`. ENV: `geom_distribution`, `l3_propagation`,
`obs_driver_cli`, `obs_driver_workers`, `slot_release_latency`.
(`coverage_matrix` and `r6_golden_control` are being fixed by other lanes.)
