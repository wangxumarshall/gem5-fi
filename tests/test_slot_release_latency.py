#!/usr/bin/env python3
"""test_slot_release_latency.py — guard 槽位释放延迟测试（中央指令 2026-10-13 附加项）。

问题：monitor() 的 time.sleep(interval) 整段睡眠——目标进程退出后，守卫要等
剩余睡眠（最长 --interval=60s）才出循环、wait/reap 并释放锁。旧批次实测
gem5 子进程退出后接近 60 秒槽位才可用。

修复（OBS-SLOT-RELEASE）：资源采样保持 --interval 节拍，目标存活改为
POLL_TARGET_S(=2s) 快轮询——目标退出后 ≤2×POLL_TARGET_S 内释放。

本测试跑真实 guard 子进程（隔离 LSU_GUARD_DIR，/home 文件系——F3：/tmp
tmpfs 过不了磁盘红线门禁），测端到端墙钟：`guard run -- sleep 3 --interval 60`
应在 ~3s(目标) + ≤2s(轮询) + 开销 内完成并释放锁，断言 < 15s（修复前 ~63s）。
同时断言资源日志行数 ≤2（60s 节拍未被快轮询破坏）。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

WT = Path(__file__).resolve().parent.parent
GUARD = WT / "tools" / "lsu_guard.py"


def main():
    # 隔离 guard 目录必须落 /home（worktree 内）——磁盘红线门禁
    tmp = Path(tempfile.mkdtemp(prefix="slotrel_", dir=str(WT)))
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name, "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    try:
        env = {**os.environ, "LSU_GUARD_DIR": str(tmp)}
        t0 = time.time()
        r = subprocess.run(
            [sys.executable, str(GUARD), "run", "--type", "experiment",
             "--desc", "slotrel-test", "--log", str(tmp / "rsrc.log"),
             "--interval", "60", "--max-seconds", "300", "--",
             "/bin/sleep", "3"],
            capture_output=True, text=True, env=env, timeout=120)
        wall = time.time() - t0
        print(f"guard run 墙钟 = {wall:.1f}s（目标 sleep 3s + 轮询/开销）")
        check("guard_run_success",
              r.returncode == 0 and '"action": "run-finish"' in r.stdout,
              r.stdout[-200:] + r.stderr[-200:])
        check("slot_released_within_15s", wall < 15.0,
              f"墙钟 {wall:.1f}s ≥ 15s（修复前行为 ~63s：sleep(60) 整段等待）")
        nlines = len([l for l in (tmp / "rsrc.log").read_text().splitlines()
                      if l.strip()])
        check("resource_log_cadence_preserved", nlines <= 2,
              f"资源日志 {nlines} 行（应保持 60s 节拍，非 2s 刷屏）")
        st = subprocess.run(
            [sys.executable, str(GUARD), "status"],
            capture_output=True, text=True, env=env, timeout=30)
        held = sum(1 for v in json.loads(st.stdout)["experiment_slots"].values()
                   if v and not v.get("corrupt"))
        check("lock_fully_released", held == 0, f"slots_held={held}")
        print(f"\nFAILURES: {fails if fails else '无'}")
        return 1 if fails else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
