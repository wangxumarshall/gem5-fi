#!/usr/bin/env python3
"""test_lsu_campaign_count_contradiction.py — [LSU][MDSPEC][R6-FIXD] 计数矛盾
绝不被静默成一个"率"。

真缺陷（实测）：`run_cell_adaptive` 末
    act_rate = (activated / attempted) if attempted else 0.0
`attempted=0` 而 `activated=3` 时打印 `activation_rate=0.0` —— 分母为 0 的
比值被伪装成"0 激活率"，掩盖了 attempted/activated 计数本身互相矛盾这一事实
（activated 不可能超过 attempted）。同理 `sdc_rate` 在 activated=0 时报静默 0.0。

钉死：
  1. attempted>0 → activation_rate = activated/attempted（正常比值）；
  2. attempted==0 且 activated==0 → 0.0（真零，非矛盾）；
  3. attempted==0 且 activated>0 → activation_rate is None + count_contradiction
     True + 响亮 note（绝不打印 0.0）；
  4. activated==0 时 sdc_rate 不再静默 0.0（None + note）。

用法：python3 tests/test_lsu_campaign_count_contradiction.py   （退出码 0=全 PASS）
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


def _args():
    return types.SimpleNamespace(
        phase="trial", trial_target=1, screening_target=1, main_target=1,
        max_seeds_per_cell=1, wilson_stop_hw=0.02, timeout=300, fs_timeout=2700)


def _run(tmp, ret):
    args = _args()
    original = LC.run_single_cell
    LC.run_single_cell = lambda c, a, s, o: dict(ret)
    try:
        runid, line = LC.run_cell_adaptive(_cell(), args, Path(tmp))
    finally:
        LC.run_single_cell = original
    res = json.loads((Path(tmp) / runid / "cell_results.json").read_text())
    return res, line


def main():
    print("[1] 矛盾：attempted=0 而 activated=3 —— 不得报 0.0")
    with tempfile.TemporaryDirectory() as td:
        res, line = _run(td, {"outcome": "SDC", "activated": 3, "attempted": 0,
                              "timeout_seconds": 300, "chain_report": None})
        check("activation_rate is None",
              res.get("activation_rate") is None, str(res.get("activation_rate")))
        check("count_contradiction is True",
              res.get("count_contradiction") is True,
              str(res.get("count_contradiction")))
        check("activation_rate_note 非空",
              bool(res.get("activation_rate_note")), str(res.get("activation_rate_note")))
        check("控制台行不谎报 activation_rate=0.0",
              "activation_rate=0.0" not in line, line)

    print("[2] 正常比值：attempted=10, activated=3 → 0.3")
    with tempfile.TemporaryDirectory() as td:
        res, _ = _run(td, {"outcome": "SDC", "activated": 3, "attempted": 10,
                           "timeout_seconds": 300, "chain_report": None})
        check("activation_rate == 0.3",
              res.get("activation_rate") == 0.3, str(res.get("activation_rate")))
        check("无 count_contradiction 标记",
              not res.get("count_contradiction"), str(res.get("count_contradiction")))

    print("[3] 真零：attempted=0 且 activated=0 → 0.0（不是矛盾）")
    with tempfile.TemporaryDirectory() as td:
        res, _ = _run(td, {"outcome": "Blocked", "activated": 0, "attempted": 0,
                           "timeout_seconds": 300, "chain_report": None})
        check("activation_rate == 0.0",
              res.get("activation_rate") == 0.0, str(res.get("activation_rate")))
        check("无 count_contradiction 标记",
              not res.get("count_contradiction"), str(res.get("count_contradiction")))
        check("activated=0 → sdc_rate 为 None（不静默 0.0）",
              res.get("sdc_rate") is None, str(res.get("sdc_rate")))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
