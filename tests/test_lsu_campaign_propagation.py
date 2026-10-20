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

    print("[4] FS 路径：armtlb 单元的命令构造同样带传播标志")
    if not real.exists():
        check("FS 命令构造（需已构建二进制）", False, "未找到 " + str(real))
    else:
        import os
        os.environ["LSU_GEM5_BIN"] = str(real)
        captured = {}

        def fake_run_fs(cmd, **kw):
            captured["cmd"] = cmd

            class P:
                returncode = 0
                stdout = ""
                stderr = ""
            return P()

        orig = LC.subprocess.run
        LC.subprocess.run = fake_run_fs
        # asset guard is exercised by the real FS smoke; here we only assert
        # the command shape (the worktree has no gem5-fs submodule).
        orig_assets = LC.require_fs_assets
        LC.require_fs_assets = lambda: None
        orig_fs = LC.classify_fs_run
        LC.classify_fs_run = lambda *a, **k: {"outcome": "Timeout",
                                             "injected": 0, "activated": 0}
        try:
            args = types.SimpleNamespace(
                phase="trial", timeout=60, fs_checkpoint="/tmp/fake_cpt",
                fs_timeout=60)
            cell = _cell("T01-F0-W4", "T01", "L1d-TLB", "F0",
                         "TLB-AliasPerm 地址翻译探针")
            out = ROOT / "runs/lsu/_test_prop_assembly_fs/seed1"
            LC.run_single_cell(cell, args, 5, out)
        finally:
            LC.subprocess.run = orig
            LC.classify_fs_run = orig_fs
            LC.require_fs_assets = orig_assets
            os.environ.pop("LSU_GEM5_BIN", None)
        cmd = captured.get("cmd") or []
        check("FS 命令已组装", bool(cmd), "subprocess.run 未被调用")
        check("FS 命令用 fs 配置", any("fs" in str(c) for c in cmd[:4]), str(cmd[:3]))
        check("FS 含 --chaos_propagation", "--chaos_propagation" in cmd, str(cmd))
        i = cmd.index("--prop_run_id") if "--prop_run_id" in cmd else -1
        check("FS --prop_run_id = RunID",
              i >= 0 and cmd[i + 1] == "T01-F0-W4", str(cmd))
        j = (cmd.index("--prop_sample_run_id")
             if "--prop_sample_run_id" in cmd else -1)
        check("FS --prop_sample_run_id = s<seed>",
              j >= 0 and cmd[j + 1] == "s5", str(cmd))

    print("[5] chain_report：oracle join + truncated 保留（含无 chain_end）")
    import gzip
    import json as _json
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        # 一条真实形状的流：tlb_fault(contained 空) + 无 chain_end（中止样本）
        body = (
            "# prop-evt v1: header\n"
            "PROP-EVT: kind=inj run_id=X sample_run_id=s1 fault_id=1 "
            "event_id=0 tick=10\n"
            "PROP-EVT: kind=addr_form run_id=X sample_run_id=s1 fault_id=1 "
            "event_id=1 tick=10\n"
            "PROP-EVT: kind=tlb_fault run_id=X sample_run_id=s1 fault_id=1 "
            "event_id=2 tick=13 detection_layer=Hardware contained= "
            "outcome=GenericPageTableFault\n"
        )
        # A well-formed gz is NOT truncated; the abort shape is a stream
        # that was Z_SYNC_FLUSH-ed but never finished (no trailer). Build
        # exactly that, or the assertion tests nothing.
        import zlib
        co = zlib.compressobj(9, zlib.DEFLATED, 16 + 15)   # gzip wrapper
        (d / "prop_evt.txt.gz").write_bytes(
            co.compress(body.encode()) + co.flush(zlib.Z_SYNC_FLUSH))
        rep = LC.write_chain_report(d, "A01-F0-W3", 1,
                                    {"outcome": "Crash"}, exit_code=134)
        check("stream_present", rep["stream_present"] is True, str(rep))
        check("事件前缀被保留（无 chain_end 也计入）", rep["event_count"] == 3,
              str(rep["event_count"]))
        check("truncated 标记（gz 无 trailer）", rep["truncated"] is True,
              str(rep["truncated"]))
        check("oracle join → crash_translation_blocked",
              rep["terminal"] == "crash_translation_blocked", str(rep["terminal"]))
        check("provable_to / beyond 一致",
              rep["provable_to"] == "L2" and rep["beyond"] == "",
              f'{rep["provable_to"]} / {rep["beyond"]!r}')
        check("chain_report.json 落盘",
              (d / "chain_report.json").exists(), "文件不存在")
        # 无流：诚实记录 absent，不伪造判定
        rep2 = LC.write_chain_report(d / "non", "X-F0-W1", 2,
                                     {"outcome": "Masked"})
        check("无流 → stream_present=False 且无 terminal",
              rep2["stream_present"] is False and rep2["terminal"] is None,
              str(rep2))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
