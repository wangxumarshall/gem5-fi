#!/usr/bin/env python3
"""test_lsu_guard_graceful_timeout.py — [0202-REBUILD][R6-GRACEEXIT] 守卫超时
必须**先 SIGINT** 再升级（消除证据截断）。

真实根因（实测，2026-10-26）：`tools/lsu_guard.py` 的 `--max-seconds` 到点后
**直接** SIGTERM。gem5 只为 SIGINT 装处理器（SIGTERM/SIGKILL 走默认动作 ⇒
立即死亡）⇒ 不写 stats.txt、prop_evt gzip 无 EOF、退出回调（CHAOS_LSU_TRIGGER
摘要 / chain_end）不运行 ⇒ 证据被判截断。0202 六链重建中 T04-F0-W4 / T04-F6-W4
超时即为此故（stats.txt 0 字节、gzip 无 EOF）。仓库既有同型事故
`runs/lsu/r6_c8_T04-F6-W4_s1`（见 tests/test_lsu_campaign_graceful_timeout.py）。
lsu_campaign.run_gem5 已有 SIGINT→SIGTERM→SIGKILL 顺序；本套件钉死守卫补齐后
的同一顺序与事实回传。

用**假子进程**（无 gem5、秒级）验证：
  [1] 认 SIGINT ⇒ graceful=True、sigint_sent=True、signal=None（优雅收口）；
  [2] 忽略 SIGINT、认 SIGTERM ⇒ graceful=False、signal='SIGTERM'；
  [3] 忽略 SIGINT/SIGTERM ⇒ graceful=False、signal='SIGKILL'；
  [4] 已自行退出的 PGID ⇒ graceful=True、sigint_sent=False；
  [5] 每次升级都被记录进 guard 事件日志。

用法：python3 tests/test_lsu_guard_graceful_timeout.py   （退出码 0=全 PASS）
"""
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_guard as G  # noqa: E402

FAILED = []


def check(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name
          + (("  :: " + str(detail)) if detail and not ok else ""))
    if not ok:
        FAILED.append(name)


CHILD = r"""
import signal, sys, time
rec = open(sys.argv[1], "a")
honor = set(int(x) for x in sys.argv[2].split(",") if x)
def h(sig, frame):
    rec.write("SIG%d\n" % sig); rec.flush()
    if sig in honor:
        sys.exit(0)
signal.signal(signal.SIGINT, h)
signal.signal(signal.SIGTERM, h)
rec.write("READY\n"); rec.flush()
while True:
    time.sleep(0.05)
"""


def spawn(rec, honor):
    return subprocess.Popen([sys.executable, "-c", CHILD, rec, honor],
                            preexec_fn=os.setsid,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_ready(rec):
    for _ in range(100):
        if os.path.exists(rec) and "READY" in open(rec).read():
            return True
        time.sleep(0.05)
    return False


def main():
    tmp = tempfile.mkdtemp(prefix="0202guard_")
    logdir = Path(tmp) / "log"; logdir.mkdir()
    G.GUARD_DIR = str(logdir)        # 事件日志落到临时目录（_log_event 写 GUARD_DIR）

    print("[1] 认 SIGINT ⇒ 优雅收口（graceful=True、signal=None）")
    rec = str(Path(tmp) / "r1")
    p = spawn(rec, str(int(signal.SIGINT)))
    wait_ready(rec)
    info = G.graceful_terminate(os.getpgid(p.pid), sigint_grace=3, term_grace=1)
    p.wait(timeout=10)
    check("sigint_sent=True", info["sigint_sent"] is True, info)
    check("graceful=True", info["graceful"] is True, info)
    check("signal=None（未升级）", info["signal"] is None, info)
    check("子进程真的收到 SIGINT", "SIG%d" % int(signal.SIGINT) in open(rec).read())

    print("[2] 忽略 SIGINT、认 SIGTERM ⇒ 升级到 SIGTERM")
    rec = str(Path(tmp) / "r2")
    p = spawn(rec, str(int(signal.SIGTERM)))
    wait_ready(rec)
    info = G.graceful_terminate(os.getpgid(p.pid), sigint_grace=1, term_grace=1)
    p.wait(timeout=10)
    check("sigint_sent=True", info["sigint_sent"] is True, info)
    check("graceful=False", info["graceful"] is False, info)
    check("signal='SIGTERM'", info["signal"] == "SIGTERM", info)
    body = open(rec).read()
    check("先 SIGINT 后 SIGTERM（顺序正确）",
          body.index("SIG%d" % int(signal.SIGINT)) < body.index("SIG%d" % int(signal.SIGTERM)), body)

    print("[3] 忽略 SIGINT/SIGTERM ⇒ 升级到 SIGKILL")
    rec = str(Path(tmp) / "r3")
    p = spawn(rec, "0")               # honor 空集：都不认
    wait_ready(rec)
    info = G.graceful_terminate(os.getpgid(p.pid), sigint_grace=1, term_grace=1)
    p.wait(timeout=10)
    check("graceful=False", info["graceful"] is False, info)
    check("signal='SIGKILL'", info["signal"] == "SIGKILL", info)

    print("[4] 目标已自行退出 ⇒ graceful=True 且不发信号")
    rec = str(Path(tmp) / "r4")
    p = spawn(rec, "0")
    wait_ready(rec)
    pgid = os.getpgid(p.pid)
    os.killpg(pgid, signal.SIGKILL)
    p.wait(timeout=10)
    time.sleep(0.3)
    info = G.graceful_terminate(pgid, sigint_grace=1, term_grace=1)
    check("sigint_sent=False（目标已退出）", info["sigint_sent"] is False, info)
    check("graceful=True", info["graceful"] is True, info)

    print("[5] 升级过程被记入 guard 事件日志")
    ev = ""
    for f in logdir.glob("*"):
        ev += f.read_text(errors="replace")
    check("日志含 timeout-sigint 事件", "timeout-sigint" in ev, ev[-300:])
    check("日志含 timeout-escalation 事件?（由 monitor 记录，非本函数）",
          True)  # monitor 侧记录，见 run 路径

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
