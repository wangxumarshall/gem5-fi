#!/usr/bin/env python3
"""test_lsu_campaign_propagation.py — [MDSPEC][H0] campaign 全量传播接入契约。

用户指令（2026-10-20 第二轮）：CHAOSPropagation 必须由**正式 campaign 入口**
对每个样本自动挂载并传递 run_id/sample_run_id（此前只有手工直驱 lsu_proxy
才有 PROP-EVT 流，正式入口产不出传播证据）。

钉死三件事：
  1. 每样本命令行含 --chaos_propagation / --prop_run_id <RunID> /
     --prop_sample_run_id s<seed>（SE 与 FS 两支）；
  2. 二进制解析遵 LSU_GEM5_BIN → repo-root build/ARM/gem5.opt，二者皆缺
     **响亮 SystemExit**（不得静默跑错/跑空二进制）；
  3. 端到端：run_single_cell 实际组装的命令里带齐上述三项（不是"函数存在
     但没被调用"）。

用法：python3 tests/test_lsu_campaign_propagation.py   （退出码 0=全 PASS）
"""
import sys
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


def _cell(runid, model, unit, freq, workload):
    row = [""] * 12
    row[LC.COL_RUNID] = runid
    row[LC.COL_MODEL] = model
    row[LC.COL_UNIT] = unit
    row[LC.COL_FREQ] = freq
    row[LC.COL_WORKLOAD] = workload
    return row


def main():
    print("[1] propagation_flags 形状")
    f = LC.propagation_flags("A01-F0-W3", 3)
    check("flags 完整", f == ["--chaos_propagation", "--prop_run_id",
                              "A01-F0-W3", "--prop_sample_run_id", "s3"],
          str(f))

    print("[2] 二进制解析（LSU_GEM5_BIN 优先 + 缺则响亮失败）")
    real = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
    if real.exists():
        got = LC.resolve_g5({"LSU_GEM5_BIN": str(real)})
        check("env 覆盖生效", got == real, str(got))
    try:
        LC.resolve_g5({"LSU_GEM5_BIN": "/nonexistent/gem5.opt"})
        check("缺二进制必须 SystemExit", False, "没抛异常")
    except SystemExit:
        check("缺二进制必须 SystemExit", True)
    # worktree 里 repo-root build/ 不存在 → 默认路径也必须响亮失败
    if not (ROOT / "build/ARM/gem5.opt").exists():
        try:
            LC.resolve_g5({})
            check("默认路径缺失也 SystemExit", False, "没抛异常")
        except SystemExit:
            check("默认路径缺失也 SystemExit", True)

    print("[3] 端到端：run_single_cell 组装的命令带齐传播标志")
    if not real.exists():
        check("端到端（需已构建二进制）", False, "未找到 " + str(real))
    else:
        import os
        os.environ["LSU_GEM5_BIN"] = str(real)
        captured = {}

        def fake_run(cmd, **kw):
            captured["cmd"] = cmd

            class P:
                returncode = 0
                stdout = "FINAL 728e604ffcec539d\n"
                stderr = ""
            return P()

        orig = LC.subprocess.run
        LC.subprocess.run = fake_run
        orig_classify = LC.classify_run
        LC.classify_run = lambda *a, **k: {"outcome": "Masked",
                                          "activated": 1, "classes": {}}
        try:
            args = types.SimpleNamespace(
                phase="trial", timeout=60, fs_checkpoint=None,
                fs_timeout=60)
            cell = _cell("A01-F0-W3", "A01", "AGU", "F0",
                         "AGU-AddrModes AArch64 寻址模式探针")
            out = ROOT / "runs/lsu/_test_prop_assembly/seed1"
            LC.run_single_cell(cell, args, 7, out)
        finally:
            LC.subprocess.run = orig
            LC.classify_run = orig_classify
            os.environ.pop("LSU_GEM5_BIN", None)

        cmd = captured.get("cmd")
        check("命令已组装", cmd is not None, "subprocess.run 未被调用")
        if cmd:
            check("含 --chaos_propagation", "--chaos_propagation" in cmd,
                  str(cmd))
            i = cmd.index("--prop_run_id") if "--prop_run_id" in cmd else -1
            check("--prop_run_id = RunID",
                  i >= 0 and cmd[i + 1] == "A01-F0-W3", str(cmd))
            j = (cmd.index("--prop_sample_run_id")
                 if "--prop_sample_run_id" in cmd else -1)
            check("--prop_sample_run_id = s<seed>",
                  j >= 0 and cmd[j + 1] == "s7", str(cmd))
            check("二进制取自 LSU_GEM5_BIN", str(real) in cmd, str(cmd[:2]))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
