#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-NEXT6] campaign 单-seed 选择（--seed-start）。

背景（实测）：`run_cell_adaptive` 的 seed 枚举历史上是严格 `1..N`
（`seed += 1` → `<outdir>/<runid>/seed{N}`）。要为每个 (RunID,seed) 产出
**一个独立权威目录、且不累计重跑低号 seed**，就必须能单独跑某个 seed。
`--max-seeds-per-cell 3` 那种累计写法会在新目录里把 seed1、seed2 再算一遍
（上一批 `r6_c9_*_s2` 目录含 seed1+seed2、`_s3` 含 seed1+seed2+seed3 ——
`cell_results.json: seed_batches=N`），本轮明令禁止。

钉死：
  1. `--seed-start 2 --max-seeds-per-cell 1` → 只跑 seed2（目录只有 seed2；
     不出现 seed1/seed3）；
  2. 该 seed2 传给 run_single_cell 的 seed 号 == 累计运行(seed-start 1, cap 2)
     的 seed2 的 seed 号（共随机数按构造不变：seed 号即 RNG 抽点源）；
  3. 默认（无 --seed-start）与历史行为逐字一致：cap=1 → 仅 seed1，
     stop_reason=="seed-cap(1)"；cap=2 → seed1,seed2，stop_reason=="seed-cap(2)"；
  4. 非默认起点 stop_reason 记为 `seed-cap(<cap>@<start>)`，响亮可辨。

用法：python3 tests/test_lsu_campaign_seed_start.py   （退出码 0=全 PASS）
"""
import json
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _cell(runid="A01-F0-W3"):
    cell = [""] * 12
    cell[LC.COL_RUNID] = runid
    cell[LC.COL_MODEL] = "A01"
    cell[LC.COL_UNIT] = "U"
    cell[LC.COL_FREQ] = "F0"
    return cell


def _args(**kw):
    base = dict(phase="trial", trial_target=10 ** 9, screening_target=1,
                main_target=1, max_seeds_per_cell=1, wilson_stop_hw=0.02,
                timeout=300, fs_timeout=2700)
    base.update(kw)
    return types.SimpleNamespace(**base)


def _run(tmp, args, ret=None):
    """Run one cell with a fake run_single_cell that records the seed numbers
    actually exercised and materialises each seed's outdir (mirroring the real
    runner, which writes into <outroot>/<runid>/seed{N}/). Returns
    (cell_results dict, recorded seeds list)."""
    ret = ret or {"outcome": "Masked", "activated": 0, "attempted": 0,
                  "timeout_seconds": 300, "chain_report": None}
    seen = []
    original = LC.run_single_cell

    def fake(c, a, s, o):
        seen.append(s)
        Path(o).mkdir(parents=True, exist_ok=True)
        return dict(ret)

    LC.run_single_cell = fake
    try:
        runid, _line = LC.run_cell_adaptive(_cell(), args, Path(tmp))
    finally:
        LC.run_single_cell = original
    res = json.loads((Path(tmp) / runid / "cell_results.json").read_text())
    return res, seen


def main():
    print("[1] --seed-start 2 --max-seeds-per-cell 1 → 只跑 seed2，独立目录")
    with tempfile.TemporaryDirectory() as td:
        res, seen = _run(td, _args(seed_start=2, max_seeds_per_cell=1))
        dirs = sorted(p.name for p in (Path(td) / "A01-F0-W3").glob("seed*"))
        check("run_single_cell 只被调用一次", seen == [2], str(seen))
        check("目录恰为 ['seed2']", dirs == ["seed2"], str(dirs))
        check("n_runs == 1", res.get("n_runs") == 1, str(res.get("n_runs")))
        # seed_batches 是 seed 高水位（最后一个 seed 号），不是计数 ——
        # 单跑 seed2 时高水位=2 而 n_runs=1（旧累计写法下二者恒相等，
        # 故此处正是区分"独立单跑"与"累计重跑"的判据）。
        check("seed_batches == 2（高水位=2，非计数）",
              res.get("seed_batches") == 2, str(res.get("seed_batches")))
        check("stop_reason == 'seed-cap(1@2)'",
              res.get("stop_reason") == "seed-cap(1@2)", str(res.get("stop_reason")))

    print("[2] --seed-start 3 --max-seeds-per-cell 1 → 只跑 seed3")
    with tempfile.TemporaryDirectory() as td:
        res, seen = _run(td, _args(seed_start=3, max_seeds_per_cell=1))
        dirs = sorted(p.name for p in (Path(td) / "A01-F0-W3").glob("seed*"))
        check("run_single_cell 只被调用一次且 seed==3", seen == [3], str(seen))
        check("目录恰为 ['seed3']", dirs == ["seed3"], str(dirs))

    print("[3] 共随机数不变：单跑 seed2 与累计跑(cap=2) 的 seed2 同号")
    with tempfile.TemporaryDirectory() as td_a:
        _res_a, seen_a = _run(td_a, _args(seed_start=2, max_seeds_per_cell=1))
    with tempfile.TemporaryDirectory() as td_b:
        _res_b, seen_b = _run(td_b, _args(seed_start=1, max_seeds_per_cell=2))
    check("累计运行 seed 序列 == [1,2]", seen_b == [1, 2], str(seen_b))
    check("单跑 seed2 的 seed 号 == 累计运行的最后一个 seed 号",
          seen_a == [seen_b[-1]] == [2], f"{seen_a} vs {seen_b}")

    print("[4] 默认（无 seed_start）与历史行为逐字一致")
    # 4a: cap=1 → 仅 seed1, stop_reason 'seed-cap(1)'
    with tempfile.TemporaryDirectory() as td:
        args = _args(max_seeds_per_cell=1)          # no seed_start attr
        res, seen = _run(td, args)
        check("cap=1 默认只跑 seed1", seen == [1], str(seen))
        check("stop_reason == 'seed-cap(1)'（不带 @）",
              res.get("stop_reason") == "seed-cap(1)", str(res.get("stop_reason")))
    # 4b: cap=2 → seed1,seed2, stop_reason 'seed-cap(2)'
    with tempfile.TemporaryDirectory() as td:
        args = _args(max_seeds_per_cell=2)
        res, seen = _run(td, args)
        dirs = sorted(p.name for p in (Path(td) / "A01-F0-W3").glob("seed*"))
        check("cap=2 默认跑 seed1,seed2", seen == [1, 2], str(seen))
        check("默认目录 == ['seed1','seed2']", dirs == ["seed1", "seed2"], str(dirs))
        check("stop_reason == 'seed-cap(2)'",
              res.get("stop_reason") == "seed-cap(2)", str(res.get("stop_reason")))
    # 4c: seed_start=1 显式 == 默认
    with tempfile.TemporaryDirectory() as td:
        args = _args(seed_start=1, max_seeds_per_cell=2)
        res, seen = _run(td, args)
        check("seed_start=1 显式 == 默认（seed1,seed2 + 'seed-cap(2)'）",
              seen == [1, 2] and res.get("stop_reason") == "seed-cap(2)",
              f"{seen} {res.get('stop_reason')}")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
