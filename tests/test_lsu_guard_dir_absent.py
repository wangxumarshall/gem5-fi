#!/usr/bin/env python3
"""test_lsu_guard_dir_absent.py — R6-GUARD：GUARD_DIR 缺失不得 TypeError。

缺陷实测（lane L15-v2 报告，2026-10-23）：`LSU_GUARD_DIR` 指向不存在的路径时
`gate` 抛 TypeError（不是可读的阻断理由）：

    File "tools/lsu_guard.py", line 294, in _disk_guard_reason
        floor = max(DISK_MIN_FREE_GIB, DISK_MIN_FREE_PCT * total_gib)
    TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'

根因：snapshot() 在 GUARD_DIR 不存在时把 disk_free_gib/disk_total_gib 置 None
（`if os.path.isdir(GUARD_DIR) else None`），而 _disk_guard_reason 在 None 检查
之前就先算了 `DISK_MIN_FREE_PCT * total_gib`。L15-v2 只能靠 `mkdir` + 导出绕过。

本套件要求：① gate 在不存在的嵌套 GUARD_DIR 下不得 Traceback、且把目录建出；
② _disk_guard_reason(None, None) 返回可读理由字符串而非抛异常。

用法：python3 tests/test_lsu_guard_dir_absent.py   （退出码 0=全 PASS）
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD = HERE.parent / "tools" / "lsu_guard.py"


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name, "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    # 顶层临时目录存在，但嵌套 guard 子目录**不存在**
    base = tempfile.mkdtemp(prefix="guard_absent_")
    absent = os.path.join(base, "runs", "lsu", "guard")
    check("precondition_dir_absent", not os.path.isdir(absent), absent)

    # ---- 1) gate 在缺失 GUARD_DIR 下：无 Traceback，目录被创建 ----
    r = subprocess.run([sys.executable, str(GUARD), "gate"],
                       capture_output=True, text=True,
                       env={**os.environ, "LSU_GUARD_DIR": absent})
    combined = (r.stdout or "") + (r.stderr or "")
    check("gate_no_typeerror",
          "TypeError" not in combined and "Traceback" not in combined,
          combined.strip().splitlines()[-1] if combined.strip() else "<no output>")
    check("gate_dir_created", os.path.isdir(absent), absent)
    check("gate_rc_bool", r.returncode in (0, 1),
          f"rc={r.returncode} stderr={r.stderr!r}")

    # ---- 2) _disk_guard_reason(None, None)：可读理由，不抛异常 ----
    sys.path.insert(0, str(GUARD.parent))
    os.environ["LSU_GUARD_DIR"] = absent
    import lsu_guard as G  # noqa: E402
    try:
        reason = G._disk_guard_reason(None, None)
        check("disk_reason_none_is_str", isinstance(reason, str) and reason != "",
              repr(reason))
    except Exception as exc:  # noqa: BLE001  （TDD：任何异常都是失败）
        check("disk_reason_none_is_str", False, f"raised {type(exc).__name__}: {exc}")

    # ---- 3) status/run 路径同样不得 Traceback（同一 snapshot 入口） ----
    r2 = subprocess.run([sys.executable, str(GUARD), "status"],
                        capture_output=True, text=True,
                        env={**os.environ, "LSU_GUARD_DIR": os.path.join(base, "b2")})
    c2 = (r2.stdout or "") + (r2.stderr or "")
    check("status_no_traceback",
          "Traceback" not in c2 and r2.returncode == 0, c2[-200:])

    shutil.rmtree(base, ignore_errors=True)
    print()
    if fails:
        print(f"FAILURES: {fails}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
