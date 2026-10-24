# R6-FTIER — armtlb lookup-mode F-tier contract (2026-10-24)

## Goal

Fix the R6-FTIER defect: the six first-wave RunIDs (`T01-F0-W4`, `T02-F0-W4`,
`T02-F2-W4`, `T04-F0-W4`, `T04-F2-W4`, `T04-F6-W4`) collapsed to **three
independent experimental conditions** because the `armtlb` (lookup-mode TLB)
family never carried the cell's F column into its run parameters.

Deliverable: each RunID either carries a tier the landed injector really
consumes, or is **loudly BLOCKED** — never silently re-labelled F0.

## Step 1 — confirmed spec semantics (no guessing)

Source of truth, quoted verbatim:

- `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md` §5 (sheet 5), lines 144-150:
  - `F0 | 单次瞬态 | 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样`
  - `F2 | 中频事件归一化 | 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动`
  - `F6 | 确定性事件触发 | 首次出现指定事件时注入一次，如 TLB hit、SQ forward、dirty eviction、CAS 成功`
- `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh` (header comment) restates the
  same LSU event-normalized tiers (`intervalEvents`: F1=1e6 / F2=1e5 / F3=1e4).
- `artifacts/lsu-trial/07-expanded-matrix-backfilled.csv`: T01 {F0,F1,F2},
  T02 {F0,F2}, T04 {F0,F2,F6}; the F definition text per row is the sheet-5 text.
- `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-03-位置x模型矩阵.md`: the
  `适用频率` column carries the same tier sets; the sub-model column carries the
  *adjacency/field* variants (T02-a/b, T04-a) — the tier is NOT a sub-model.

## Step 2 — root cause (three layers, all verified in source)

1. `tools/lsu_campaign.py` `resolve_cell` (armtlb branch) appended
   `--tlb_lsu_tier` **only** `if any(w in extra for w in WALK_FAULT_TYPES)`
   — a walk-only gate. `FAMILY_TIER_FLAGS` had **no** `armtlb` key (the branch
   builds its flags inline). So the F column was dropped for T01/T02/T04/T10.
2. Deeper: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc` — the
   lookup-hit path (`maybeCorrupt` / `maybeCorruptLookup`, both called from
   `TLB::lookup` in `arch/arm/tlb.cc:171-184`) **never references `lsuTrigger`**.
   `lsuTrigger` appears only in (a) the constructor and (b) `maybeDropWalkFill`
   (the T08 walk-issue path). Every other injector family polls its trigger at
   its hook. ⇒ For lookup modes, `--tlb_lsu_tier` would be a no-op flag: wiring
   it alone would change the command string while the physics stayed identical —
   the exact "six RunIDs = three conditions" defect, merely disguised.
3. Existing pinned tests encode the current contract: `tests/test_lsu_hook_t08_walk.py`
   ("T01 lookup 模式不带 tier/warmup/span（逐字节不变）") and
   `tests/test_lsu_fs_infra.py` [5] (all 12 T-cell W4 rows resolve runnable).

## Step 3 — the honest contract implemented

For the `armtlb` **lookup** modes (every fault type except `WALK_FAULT_TYPES`):

- **F0 → runnable** — the landed legacy chain (`--tlb_max_faults 1` +
  `--tlb_probability 1.0` + the seed-varied eligible-event skip) implements
  F0's semantics ("一次运行只注入 1 次；warm-up 后在 eligible event 中抽样").
- **F1/F2/F3/F4/F5/F6 → BLOCKED** with a loud reason naming the C++ fact
  (no interval / burst / fixed-mask-permanent / first-event knob is consumed on
  the lookup path). Not re-labelled F0.

Walk modes (T08 family) keep the existing tier wiring (unchanged).

## Tasks (one commit per task)

- [x] **T1** — RED: `tests/test_lsu_ftier_armtlb_lookup.py` (new) pinning:
      ① the six RunIDs no longer produce identical runnable commands;
      ② every emitted armtlb flag is a real option of `configs/se/arm_chaos_fs.py`;
      ③ F0/F2/F6 no longer silently degrade; ④ unexpressible tiers are BLOCKED.
      Run it → real FAIL (current code returns 6 identical runnable commands).
- [x] **T2** — GREEN: implement `ARMTLB_LOOKUP_TIERS`,
      `_armtlb_lookup_tier_block_reason`, and the `resolve_cell` tier gate.
      Re-run T1 → real PASS.
- [x] **T3** — update the in-lane contract test `tests/test_lsu_fs_infra.py` [5]
      (its 12-row runnable assertion now pins F0-only runnable + the new
      block reason); also updated the three census tests that pinned the old
      runnable set (`test_lsu_runid_map`, `test_lsu_w11_spec_residual`,
      `test_lsu_ready_contract_category`, `test_lsu_r6_reconcile_realroot`) +
      a new named ledger category `TIER-UNIMPL` in tools/lsu_ready_contract.py. Re-run → PASS.
- [x] **T4** — whole-suite run: `python3 tools/lsu_test_runner.py` →
      NEW FAIL = 0. Baseline `FAIL=12 PASS=49 ENV=4 SKIP=1 suites=66`; after
      `FAIL=12 PASS=50 ENV=4 SKIP=1 suites=67` (the +1 suite = the new test).
      The 12 FAIL names are byte-identical to the baseline set.
- [x] **T5** — commit `[LSU][MDSPEC][R6-FTIER] …` + push branch `r6-ftier`.

## Verification commands

```
python3 tests/test_lsu_ftier_armtlb_lookup.py
python3 tests/test_lsu_fs_infra.py
python3 tests/test_lsu_hook_t08_walk.py
python3 tools/lsu_test_runner.py --json /tmp/r6ftier_after.json
```

## Out of scope / blocked on other lanes

Making T02-F2 / T04-F2 / T04-F6 genuinely runnable requires the **C++**
change (Lane 3): `CHAOSArmTLB::maybeCorrupt` / `maybeCorruptLookup` must poll
`lsuTrigger` like every other family's hook. This plan only makes the campaign
honest; no C++ (.cc/.hh) and no `tools/lsu_chain_check.py` file is touched
(Lane 2 / Lane 3 own them).
