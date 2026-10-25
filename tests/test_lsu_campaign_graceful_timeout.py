#!/usr/bin/env python3
"""[R6-GRACEEXIT] 超时退出必须先优雅收口（消除证据截断）——升级顺序契约。

真实根因（只读实证，2026-10-25）：
  `tools/lsu_campaign.py:run_gem5` 在 `subprocess.TimeoutExpired` 上**直接**
  对进程组发 SIGTERM，10 s 后 SIGKILL。gem5 **只为 SIGINT 装了处理器**
  （`src/sim/init_signals.cc:initSigInt` → `simulate.cc:195` → `exitNowHandler`
  → `async_exit` → `exitSimLoop("user interrupt received")`），SIGTERM/SIGKILL
  走默认动作 ⇒ 进程立即死亡 ⇒ **不写 stats.txt、prop_evt gzip 无 EOF、退出
  回调（CHAOS_LSU_TRIGGER 摘要）不运行** ⇒ `detect_evidence_truncation` 判截断
  ⇒ `admitted/certified=False`。实测证据：`runs/lsu/r6_c8_T04-F6-W4_s1`
  （stats.txt 0 字节、gzip 无 EOF、outcome=Timeout、EVIDENCE-TRUNCATED）。

本测试用**假子进程**（无 gem5、秒级）钉死升级顺序与事实回传：
  [1] 到点先发 SIGINT（子进程记录到的是 SIGINT，不是 SIGTERM/SIGKILL）；
  [2] SIGINT 后自行退出 ⇒ graceful=True、signal=None、exit_code=0；
  [3] 忽略 SIGINT、只认 SIGTERM ⇒ graceful=False、signal=SIGTERM；
  [4] 忽略 SIGINT/SIGTERM、只认 SIGKILL ⇒ graceful=False、signal=SIGKILL；
  [5] 未到预算即正常结束 ⇒ timed_out=False、graceful=False、signal=None；
  [6] 三种升级路径都必须被 REAP（不留孤儿）且 stdout 完整回收。

用法：python3 tests/test_lsu_campaign_graceful_timeout.py   （退出码 0=全 PASS）
"""
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

failed = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + ("" if cond or not detail else f"  [{detail}]"))
    if not cond:
        failed.append(name)


# 假子进程：把**实际收到的信号**写进 record 文件，然后按 mode 决定：
#   graceful — 处理 SIGINT，正常退出（gem5 的 finalize 形状：exit 0）
#   sigterm  — 忽略 SIGINT，死于默认的 SIGTERM（须被升级到 SIGTERM 才结束）
#   sigkill  — 忽略 SIGINT 与 SIGTERM，只死于 SIGKILL（须升到 SIGKILL）
CHILD = r'''
import os, signal, sys, time
mode, rec = sys.argv[1], sys.argv[2]
def note(sig):
    with open(rec, "a") as f:
        f.write(signal.Signals(sig).name + "\n")
if mode == "graceful":
    def on_int(sig, frm):
        note(sig)
        sys.stdout.write("graceful finalize\n"); sys.stdout.flush()
        sys.exit(0)
    signal.signal(signal.SIGINT, on_int)
else:
    # no SIGINT handler: the SIGINT request must NOT be what ends this child
    signal.signal(signal.SIGINT, lambda s, f: note(s))
    if mode == "sigkill":
        signal.signal(signal.SIGTERM, lambda s, f: note(s))
print("child up", flush=True)
while True:
    time.sleep(0.05)
'''


def run_child(mode, timeout=1, sigint_grace=3, grace=3):
    """Run the fake child through the REAL run_gem5 escalation path."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        script = td / "child.py"
        script.write_text(CHILD)
        rec = td / "rec.txt"
        r = LC.run_gem5([sys.executable, str(script), mode, str(rec)],
                        timeout, td / "out.txt", td / "err.txt",
                        sigint_grace=sigint_grace, grace=grace)
        seen = rec.read_text().split() if rec.exists() else []
        return r, seen


def main():
    print("[1] 到点先发 SIGINT：子进程记录到的是 SIGINT（不是 SIGTERM/SIGKILL）")
    r_grace, seen_grace = run_child("graceful")
    check("child recorded exactly SIGINT first",
          seen_grace[:1] == ["SIGINT"], str(seen_grace))
    check("SIGINT was actually sent (sigint_sent flag)", bool(r_grace.get("sigint_sent")),
          repr(r_grace.get("sigint_sent")))

    print("[2] SIGINT 后自行退出 ⇒ graceful=True / signal=None / exit_code=0")
    check("timed_out is True (the budget really was exhausted)", r_grace["timed_out"])
    check("graceful is True", r_grace.get("graceful") is True,
          repr(r_grace.get("graceful")))
    check("no signal killed it (signal is None)", r_grace.get("signal") is None,
          repr(r_grace.get("signal")))
    check("exit_code is 0 (gem5-style clean finalize)", r_grace.get("exit_code") == 0,
          repr(r_grace.get("exit_code")))
    check("stdout was captured (finalize output survives)",
          "graceful finalize" in (r_grace.get("stdout") or ""))

    print("[3] SIGINT 不奏效时才升级 SIGTERM（graceful=False）")
    r_term, seen_term = run_child("sigterm")
    # the child records SIGINT (its handler notes it) and is then killed by
    # SIGTERM's DEFAULT action, so SIGTERM is not recordable — the escalation
    # signal below is what proves it was sent.
    check("child saw SIGINT first (the escalation came after, not instead)",
          seen_term[:1] == ["SIGINT"], str(seen_term))
    check("timed_out is True", r_term["timed_out"])
    check("graceful is False", r_term.get("graceful") is False,
          repr(r_term.get("graceful")))
    check("escalation_signal is SIGTERM (15)",
          r_term.get("escalation_signal") == int(signal.SIGTERM),
          repr(r_term.get("escalation_signal")))
    check("signal (what terminated it) is SIGTERM (15)",
          r_term.get("signal") == int(signal.SIGTERM),
          repr(r_term.get("signal")))
    check("exit_code is -15", r_term.get("exit_code") == -int(signal.SIGTERM),
          repr(r_term.get("exit_code")))

    print("[4] 忽略 SIGINT/SIGTERM 才升级 SIGKILL（仍须被 reap）")
    r_kill, seen_kill = run_child("sigkill", sigint_grace=1, grace=1)
    check("child saw SIGINT then SIGTERM before dying on SIGKILL",
          seen_kill[:2] == ["SIGINT", "SIGTERM"], str(seen_kill))
    check("timed_out is True", r_kill["timed_out"])
    check("graceful is False", r_kill.get("graceful") is False,
          repr(r_kill.get("graceful")))
    check("escalation_signal is SIGKILL (9)",
          r_kill.get("escalation_signal") == int(signal.SIGKILL),
          repr(r_kill.get("escalation_signal")))
    check("signal (what terminated it) is SIGKILL (9)",
          r_kill.get("signal") == int(signal.SIGKILL),
          repr(r_kill.get("signal")))
    check("exit_code is -9", r_kill.get("exit_code") == -int(signal.SIGKILL),
          repr(r_kill.get("exit_code")))

    print("[5] 预算内正常结束：不得进入任何升级路径")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        out = td / "out.txt"
        r_ok = LC.run_gem5([sys.executable, "-c",
                            "print('done')"], 30, out, td / "err.txt",
                           sigint_grace=3, grace=3)
    check("timed_out is False", r_ok["timed_out"] is False)
    check("graceful is False (not a timeout at all)",
          r_ok.get("graceful") is False, repr(r_ok.get("graceful")))
    check("signal is None", r_ok.get("signal") is None)
    check("exit_code is 0", r_ok.get("exit_code") == 0, repr(r_ok.get("exit_code")))
    check("stdout captured", "done" in (r_ok.get("stdout") or ""))

    print("[6] 三种升级路径都必须被 REAP（无孤儿、无僵尸、stdout 回收）")
    for tag, r in (("graceful", r_grace), ("sigterm", r_term), ("sigkill", r_kill)):
        check(f"{tag}: pid recorded", isinstance(r.get("pid"), int) and r["pid"] > 0)
        check(f"{tag}: returncode settled (not None)", r.get("exit_code") is not None)
        try:
            import os
            os.kill(r["pid"], 0)
            alive = True
        except (ProcessLookupError, PermissionError):
            alive = False
        check(f"{tag}: child is gone (reaped, no orphan)", not alive)

    print("[7] 未知异常退出仍然响亮（不得静默当成正常/干净）")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # 非超时的异常退出：gem5 被信号杀死（如 SIGSEGV → -11）且无 oracle 行。
        r_crash = LC.classify_fs_run(td, "", -11)
        check("abnormal exit (killed by signal) -> Crash/guest_or_unknown",
              r_crash.get("outcome") == "Crash"
              and r_crash.get("crash_kind") == "guest_or_unknown",
              repr(r_crash.get("outcome")) + "/" + repr(r_crash.get("crash_kind")))
        # exit 0 但没有 oracle 行：诚实 Unclassified（不是 Masked，也不是通过）。
        r_uncl = LC.classify_fs_run(td, "", 0)
        check("clean exit without the oracle line -> Unclassified (honest)",
              r_uncl.get("outcome") == "Unclassified",
              repr(r_uncl.get("outcome")))
        # 受控 KERNEL PANIC 标记行仍按 Crash/kernel_panic 分类（不回归）。
        r_panic = LC.classify_fs_run(
            td, "[arm_chaos_fs] KERNEL PANIC under fault — exiting "
                "(classify: Crash/DUE per fs_mode)\n", 0)
        check("controlled KERNEL PANIC marker still Crash/kernel_panic",
              r_panic.get("outcome") == "Crash"
              and r_panic.get("crash_kind") == "kernel_panic",
              repr(r_panic.get("outcome")) + "/"
              + repr(r_panic.get("crash_kind")))

    print()
    if failed:
        print("FAILED (%d): %s" % (len(failed), ", ".join(failed)))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
