#!/usr/bin/env python3
"""test_lsu_campaign_timeout.py — [LSU][R6-CAMPAIGN] FS timeout 预算契约。

背景（2026-10-23）：FS gem5 在 checkpoint 上的运行远超其被赋予的 timeout，
被中途杀掉。已知良好预算是 2700 s（被赋予 --fs-timeout 2700 的运行干净结束、
留下完整流 + stats.txt）。此前默认 1800 会静默把诸多 FS run 判成 Timeout。

钉死：
  1. FS 默认 --fs-timeout == 2700（不静默降低）；
  2. **生效** timeout 可见：per-seed 条目与 cell 结果都带 timeout_seconds，
     cell 控制台行打印 FS/SE 预算。

用法：python3 tests/test_lsu_campaign_timeout.py   （退出码 0=全 PASS）
"""
import json
import re
import subprocess
import sys
import tempfile
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


def main():
    print("[1] FS 默认 timeout = 2700（已知良好预算，不静默降低）")
    check("模块常量 FS_TIMEOUT_DEFAULT 存在",
          getattr(LC, "FS_TIMEOUT_DEFAULT", None) == 2700,
          str(getattr(LC, "FS_TIMEOUT_DEFAULT", "MISSING")))
    check("build_parser 存在", hasattr(LC, "build_parser"),
          "lsu_campaign.build_parser 缺失")
    defaults = LC.build_parser().parse_args(["--matrix", "dummy"])
    check("parser --fs-timeout 默认 2700", defaults.fs_timeout == 2700,
          str(defaults.fs_timeout))
    check("parser --timeout 默认 300", defaults.timeout == 300,
          str(defaults.timeout))
    helptext = subprocess.run(
        ["python3", str(ROOT / "tools/lsu_campaign.py"), "--help"],
        capture_output=True, text=True).stdout
    flat = re.sub(r"\s+", " ", helptext)     # argparse wraps "(default: N)"
    check("--help 里 --fs-timeout default: 2700",
          "default: 2700" in flat, flat[-200:] if
          "default: 2700" not in flat else "")
    check("--help `-h` 仍可用（help 非空）", "usage" in helptext.lower(),
          helptext[:80])

    print("[2] 生效 timeout 可见（per-seed 条目 + cell 结果 + 控制台行）")
    import types
    with tempfile.TemporaryDirectory() as td:
        cell = [""] * 12
        cell[LC.COL_RUNID] = "T01-F0-W4"
        cell[LC.COL_MODEL] = "T01"
        cell[LC.COL_UNIT] = "L1d-TLB"
        cell[LC.COL_FREQ] = "F0"
        args = types.SimpleNamespace(
            phase="trial", trial_target=1, screening_target=1, main_target=1,
            max_seeds_per_cell=1, wilson_stop_hw=0.02, timeout=300,
            fs_timeout=2700)
        original = LC.run_single_cell
        LC.run_single_cell = lambda c, a, s, o: {
            "outcome": "Masked", "activated": 1,
            "timeout_seconds": a.fs_timeout, "chain_report": None}
        try:
            runid, line = LC.run_cell_adaptive(cell, args, Path(td))
        finally:
            LC.run_single_cell = original
        res = json.loads((Path(td) / runid / "cell_results.json").read_text())
        entry = res["runs"][0]
        check("per-seed 条目带 timeout_seconds=2700",
              entry.get("timeout_seconds") == 2700, str(entry.get("timeout_seconds")))
        check("cell 结果带 timeout_budget（FS/SE）",
              isinstance(res.get("timeout_budget"), dict)
              and res["timeout_budget"].get("fs_timeout") == 2700
              and res["timeout_budget"].get("se_timeout") == 300,
              str(res.get("timeout_budget")))
        check("控制台行打印生效预算（含 2700）", "2700" in line, line)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
