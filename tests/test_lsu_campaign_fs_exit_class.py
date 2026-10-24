#!/usr/bin/env python3
"""test_lsu_campaign_fs_exit_class.py — [R6-FIXEXIT2] 受控 KERNEL PANIC/OOPS
退出必须被**精确**识别为 Crash。

真缺陷（实测，T02-F2-W4/seed1）：gem5 在 F2 档位下打出受控标记
    [arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)
（configs/se/arm_chaos_fs.py:533-535 的 _kernel_panic_exit；`—` = U+2014）。
`classify_fs_run` 只认旧口径（terminal 含 "Oops" / stdout 含
"Kernel oops in guest"），既未识别该 PANIC 行、也未识别同族 OOPS 行
（configs/se/arm_chaos_fs.py:522-525），于是把一次**合法的受控 Crash**
误判成 Unclassified → classes 全零 → conservation VIOLATION。

钉死（不引入任何宽泛 "panic"/"Oops" 子串匹配）：
  1. 两种配置前缀（[arm_chaos_fs] / [lsu_multicore_fs]）的受控 PANIC 行
     + exit_code=0 → outcome=Crash, crash_kind=kernel_panic；
  2. 两种前缀的受控 OOPS 行 → outcome=Crash, crash_kind=kernel_oops；
  3. 普通日志里出现 "panic" 单词但**没有**受控标记行 → 仍 Unclassified
     （绝不因字样判 Crash）；
  4. 干净退出、无 oracle 行、无标记 → 仍 Unclassified。

用法：python3 tests/test_lsu_campaign_fs_exit_class.py   （退出码 0=全 PASS）
"""
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []

# 受控标记的权威文本（逐字取自 configs/se/arm_chaos_fs.py:522-535 与
# configs/fs/lsu_multicore_fs.py:293-302；破折号是 U+2014 EM DASH）。
FS_PANIC = ("[arm_chaos_fs] KERNEL PANIC under fault — exiting "
            "(classify: Crash/DUE per fs_mode)")
FS_OOPS = ("[arm_chaos_fs] KERNEL OOPS under fault — exiting "
           "(classify: Crash/DUE per fs_mode)")
MC_PANIC = ("[lsu_multicore_fs] KERNEL PANIC under fault — exiting "
            "(classify: Crash/DUE per fs_mode)")
MC_OOPS = ("[lsu_multicore_fs] KERNEL OOPS under fault — exiting "
           "(classify: Crash/DUE per fs_mode)")


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _fs_run(stdout, exit_code=0, log_lines=()):
    """classify_fs_run 在一个临时 outdir 上跑，返回 verdict。"""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        if log_lines:
            (d / "armtlb_injections.log").write_text("\n".join(log_lines) + "\n")
        return LC.classify_fs_run(d, stdout, exit_code)


def _fsmc_run(stdout, exit_code=0):
    with tempfile.TemporaryDirectory() as td:
        return LC.classify_fsmc_run(Path(td), stdout, exit_code)


def main():
    print("[1] 受控 PANIC（arm_chaos_fs）+ exit 0 → Crash/kernel_panic")
    r = _fs_run("gem5 ...\n" + FS_PANIC + "\n", 0)
    check("outcome == Crash", r.get("outcome") == "Crash", str(r.get("outcome")))
    check("crash_kind == kernel_panic",
          r.get("crash_kind") == "kernel_panic", str(r.get("crash_kind")))

    print("[2] 受控 OOPS（arm_chaos_fs）→ Crash/kernel_oops")
    r = _fs_run(FS_OOPS + "\n", 0)
    check("outcome == Crash", r.get("outcome") == "Crash", str(r.get("outcome")))
    check("crash_kind == kernel_oops",
          r.get("crash_kind") == "kernel_oops", str(r.get("crash_kind")))

    print("[3] 受控 PANIC（lsu_multicore_fs，走 classify_fsmc_run）"
          " → Crash/kernel_panic")
    r = _fsmc_run(MC_PANIC + "\n", 0)
    check("outcome == Crash", r.get("outcome") == "Crash", str(r.get("outcome")))
    check("crash_kind == kernel_panic",
          r.get("crash_kind") == "kernel_panic", str(r.get("crash_kind")))

    print("[4] 受控 OOPS（lsu_multicore_fs）→ Crash/kernel_oops")
    r = _fsmc_run(MC_OOPS + "\n", 0)
    check("outcome == Crash", r.get("outcome") == "Crash", str(r.get("outcome")))
    check("crash_kind == kernel_oops",
          r.get("crash_kind") == "kernel_oops", str(r.get("crash_kind")))

    print("[5] 普通日志含 panic 字样但无受控标记 → 仍 Unclassified")
    r = _fs_run("this run mentions a kernel panic in passing\n", 0)
    check("outcome == Unclassified",
          r.get("outcome") == "Unclassified", str(r.get("outcome")))
    check("未设 crash_kind", "crash_kind" not in r, str(r.get("crash_kind")))
    r = _fsmc_run("kernel panic: not a controlled marker\n", 0)
    check("fsmc: outcome == Unclassified",
          r.get("outcome") == "Unclassified", str(r.get("outcome")))

    print("[6] 干净退出、无 oracle、无标记 → 仍 Unclassified")
    r = _fs_run("all good\n", 0)
    check("outcome == Unclassified",
          r.get("outcome") == "Unclassified", str(r.get("outcome")))

    print("[7] 受控标记行必须整行锚定：前缀相同的普通行不误判")
    # 缺尾注 / 尾注被改写的行不是受控标记 → 不判 Crash
    r = _fs_run("[arm_chaos_fs] KERNEL PANIC under fault — exiting\n", 0)
    check("缺尾注的行不判 Crash（整行锚定）",
          r.get("outcome") == "Unclassified", str(r.get("outcome")))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
