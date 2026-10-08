#!/usr/bin/env python3
"""test_ooo_guard_f025.py — F-025 guard_pid 竞态移植的 TDD 测试（P1 U1b）。

背景（LSU 轨同源缺陷，6d1662ee 已修）：cmd_run spawn 后锁内 pid 被覆盖为
子进程 pid；子进程正常退出 → release 之间存在 0-60s 窗口，其间 pid 是死
pid——若 gate/acquire/clear-stale 用 pid 判活，正常收尾中的槽被误判"陈旧
槽" → GATE BLOCKED / ACQUIRE REFUSED → fail-fast 自终止。

夹具：
  A {guard_pid: 死pid, pid: 死pid}        老格式/真泄漏     → 判陈旧
  B {guard_pid: 本进程pid, pid: 死pid}    新格式收尾窗口     → 不判陈旧
  C {pid: 本进程pid}（无 guard_pid）       纯老格式回退语义

断言（全部针对隔离 OOO_GUARD_DIR，不依赖机器全局状态）：
  1) _lock_owner_pid 回退语义（guard_pid 优先，老格式回退 pid，缺省 -1）
  2) _slot_holders 用 guard_pid 判活：B 槽 live=True
  3) B 槽在场时 acquire 不误报陈旧（应成功入相邻槽）
  4) A 槽在场时 acquire REFUSED（真陈旧，显式处置语义）
  5) _release 确认字段：B 槽 confirm=guard_pid 成功、confirm=子 pid REFUSED
  6) clear-stale 双字段接受（A 槽 guard_pid 或 pid 任一）+ B 槽存活 REFUSED

运行：python3 tools/tests/test_ooo_guard_f025.py（退出码 0=PASS）。
"""
import json
import os
import shutil
import sys

TEST_GUARD_DIR = "/tmp/ooo-guard-f025-test"
DEAD_A, DEAD_B = 999001, 999002  # 假死 pid（断言确不存在）

os.environ["OOO_GUARD_DIR"] = TEST_GUARD_DIR
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import ooo_guard as G  # noqa: E402  (GUARD_DIR 在 import 时读环境)

ME = os.getpid()
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print("%s %s%s" % ("PASS" if cond else "FAIL", name, (" | " + detail) if detail else ""))


def craft(slot, lock):
    with open(G._lock_path("experiment", slot), "w") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2)


def fresh_dir():
    shutil.rmtree(TEST_GUARD_DIR, ignore_errors=True)
    os.makedirs(TEST_GUARD_DIR, exist_ok=True)


def main():
    for p in (DEAD_A, DEAD_B):
        assert not os.path.exists(f"/proc/{p}"), f"夹具 pid {p} 意外存活"

    # 1) _lock_owner_pid 回退语义
    fresh_dir()
    check("T1a owner=guard_pid（B 新格式）", G._lock_owner_pid({"guard_pid": ME, "pid": DEAD_A}) == ME)
    check("T1b owner=guard_pid（A 真泄漏）", G._lock_owner_pid({"guard_pid": DEAD_A, "pid": DEAD_B}) == DEAD_A)
    check("T1c 老格式回退 pid（C）", G._lock_owner_pid({"pid": ME}) == ME)
    check("T1d 空锁回退 -1", G._lock_owner_pid({}) == -1)

    # 2) _slot_holders 判活走 guard_pid：B 槽 live
    fresh_dir()
    craft(0, {"guard_pid": ME, "pid": DEAD_A, "desc": "f025-window", "task_type": "experiment"})
    holders = {h[0]: h for h in G._slot_holders()}
    check("T2 B 槽 holder=guard_pid 且 live", holders[0][1] == ME and holders[0][3] is True,
          "holders[0]=%r" % (holders.get(0),))

    # 3) B 槽在场：acquire 不误报陈旧，应成功入槽 1
    lock, reason = G._try_acquire("experiment", "t3")
    check("T3 B 槽在场 acquire 成功（不误报陈旧）", lock is not None and lock.get("slot") == 1,
          "lock=%s reason=%s" % (lock and lock.get("slot"), reason))
    G._release("experiment", 1, confirm_pid=ME)

    # 4) A 槽（真泄漏）在场：acquire REFUSED 且报陈旧
    fresh_dir()
    craft(0, {"guard_pid": DEAD_A, "pid": DEAD_B, "desc": "real-leak", "task_type": "experiment"})
    lock, reason = G._try_acquire("experiment", "t4")
    check("T4 A 真泄漏 acquire REFUSED+陈旧", lock is None and "陈旧" in reason and str(DEAD_A) in reason,
          "reason=%s" % reason)

    # 5) _release 确认字段：confirm=guard_pid 成功 / confirm=子 pid REFUSED
    fresh_dir()
    craft(2, {"guard_pid": ME, "pid": DEAD_A, "desc": "t5", "task_type": "experiment"})
    ok, msg, _ = G._release("experiment", 2, confirm_pid=ME)
    check("T5a release confirm=guard_pid 成功", ok and not os.path.exists(G._lock_path("experiment", 2)), "msg=%s" % msg)
    craft(2, {"guard_pid": ME, "pid": DEAD_A, "desc": "t5", "task_type": "experiment"})
    ok, msg, _ = G._release("experiment", 2, confirm_pid=DEAD_A)
    check("T5b release confirm=子pid REFUSED", (not ok) and "不符" in msg, "msg=%s" % msg)

    # 6) clear-stale：A 槽双字段任一接受；B 槽存活 REFUSED
    fresh_dir()
    craft(3, {"guard_pid": DEAD_A, "pid": DEAD_B, "desc": "t6", "task_type": "experiment"})
    argv = sys.argv
    for confirm in (DEAD_A, DEAD_B):
        fresh_dir()
        craft(3, {"guard_pid": DEAD_A, "pid": DEAD_B, "desc": "t6", "task_type": "experiment"})
        sys.argv = ["ooo_guard.py", "clear-stale", "--type", "experiment",
                    "--confirm-dead-pid", str(confirm)]
        try:
            rc = G.main()
        except SystemExit as e:  # main() 内部 sys.exit
            rc = e.code
        sys.argv = argv
        check("T6%c clear-stale 接受 %s（guard_pid/pid 任一）" % ("ab"[confirm == DEAD_B], confirm),
              rc == 0 and not os.path.exists(G._lock_path("experiment", 3)), "rc=%s" % rc)
    fresh_dir()
    craft(3, {"guard_pid": ME, "pid": DEAD_A, "desc": "t6c", "task_type": "experiment"})
    sys.argv = ["ooo_guard.py", "clear-stale", "--type", "experiment",
                "--confirm-dead-pid", str(DEAD_A)]
    try:
        rc = G.main()
    except SystemExit as e:
        rc = e.code
    sys.argv = argv
    check("T6c B 槽 guard 存活 clear-stale REFUSED", rc == 2 and os.path.exists(G._lock_path("experiment", 3)),
          "rc=%s" % rc)

    shutil.rmtree(TEST_GUARD_DIR, ignore_errors=True)
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print("SELFTEST %s (%d checks, %d failed)" % ("PASS" if n_fail == 0 else "FAIL", len(RESULTS), n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
