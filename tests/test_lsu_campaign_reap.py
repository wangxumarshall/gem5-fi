#!/usr/bin/env python3
"""test_lsu_campaign_reap.py — [LSU][R6-CAMPAIGN] timeout 后真正 kill+reap 子进程。

背景（2026-10-23）：FS 运行超时被弃时，必须真正 kill **并** reap gem5 子进程，
不留孤儿占用 checkpoint/outdir，并记录退出码/信号（此前 subprocess.run 的
TimeoutExpired 路径不落盘信号，kill 后语义不可审计）。

钉死：
  1. run_gem5() 超时时对**进程组**发 SIGTERM，grace 内不退则 SIGKILL；
  2. 进程确实被 reap（pid 不再存在）；exit_code / signal 被记录；
  3. 非超时路径正常返回 exit_code/stdout；
  4. run_single_cell 的 FS 超时分支把 timeout_signal 折进结果（可审计）。

用法：python3 tests/test_lsu_campaign_reap.py   （退出码 0=全 PASS）
"""
import json
import signal
import subprocess
import sys
import tempfile
import time
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


def _alive(pid):
    try:
        import os
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def main():
    print("[1] run_gem5 形状")
    check("run_gem5 存在", hasattr(LC, "run_gem5"),
          "lsu_campaign.run_gem5 缺失")
    if not hasattr(LC, "run_gem5"):
        print("\nFAILED (1): ['run_gem5 存在']")
        return 1

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        print("[2] 非超时：正常返回 exit_code/stdout")
        r = LC.run_gem5([sys.executable, "-c", "print('hello')"], 30,
                        td / "o.txt", td / "e.txt")
        check("timed_out=False", r["timed_out"] is False, str(r))
        check("exit_code=0", r["exit_code"] == 0, str(r.get("exit_code")))
        check("stdout 落盘", (td / "o.txt").read_text().strip() == "hello",
              (td / "o.txt").read_text())

        print("[3] 超时 + 服从 SIGTERM：SIGTERM 回收并 reap")
        r = LC.run_gem5([sys.executable, "-c",
                         "import time; time.sleep(30)"], 1,
                        td / "o2.txt", td / "e2.txt")
        check("timed_out=True", r["timed_out"] is True, str(r))
        check("signal=SIGTERM", r["signal"] == int(signal.SIGTERM), str(r))
        check("exit_code=-15（被 SIGTERM 杀）", r["exit_code"] == -15,
              str(r.get("exit_code")))
        check("子进程已 reap（pid 不存在）", not _alive(r["pid"]), str(r["pid"]))

        print("[4] 超时 + 忽略 SIGTERM：升级 SIGKILL 并 reap")
        r = LC.run_gem5([sys.executable, "-c",
                         "import signal,time; "
                         "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                         "time.sleep(60)"], 1,
                        td / "o3.txt", td / "e3.txt", grace=0.3)
        check("timed_out=True", r["timed_out"] is True, str(r))
        check("signal=SIGKILL（升级）", r["signal"] == int(signal.SIGKILL),
              str(r))
        check("exit_code=-9", r["exit_code"] == -9, str(r.get("exit_code")))
        check("顽固子进程已 reap", not _alive(r["pid"]), str(r["pid"]))

    print("[5] run_single_cell FS 超时分支折入 timeout_signal")
    captured = {}

    def fake_run_gem5(cmd, timeout, out_file, err_file, **kw):
        captured["timeout"] = timeout
        Path(out_file).write_text("")
        Path(err_file).write_text("TIMEOUT")
        return {"timed_out": True, "exit_code": -9, "signal": int(signal.SIGKILL),
                "stdout": "", "stderr": "TIMEOUT", "pid": 12345}

    import os
    # resolve_g5 needs an existing binary path; the Popen is faked below, so a
    # dummy existing file suffices (a worktree has no repo-root build/).
    os.environ["LSU_GEM5_BIN"] = sys.executable
    orig_rg = LC.run_gem5
    orig_assets = LC.require_fs_assets
    LC.run_gem5 = fake_run_gem5
    LC.require_fs_assets = lambda: None
    try:
        cell = [""] * 12
        cell[LC.COL_RUNID] = "T01-F0-W4"
        cell[LC.COL_MODEL] = "T01"
        cell[LC.COL_UNIT] = "L1d-TLB"
        cell[LC.COL_FREQ] = "F0"
        args = types.SimpleNamespace(phase="trial", timeout=300, fs_timeout=2700,
                                     fs_checkpoint="/tmp/fake_cpt")
        out = ROOT / "runs/lsu/_test_reap/seed1"
        res = LC.run_single_cell(cell, args, 1, out)
    finally:
        LC.run_gem5 = orig_rg
        LC.require_fs_assets = orig_assets
    check("FS 超时 outcome=Timeout", res.get("outcome") == "Timeout", str(res))
    check("传入了 FS 生效 budget(=2700)", captured.get("timeout") == 2700,
          str(captured.get("timeout")))
    check("结果记录 timeout_signal=SIGKILL",
          res.get("timeout_signal") == int(signal.SIGKILL), str(res))
    check("结果记录 timeout_exit_code=-9", res.get("timeout_exit_code") == -9,
          str(res))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
