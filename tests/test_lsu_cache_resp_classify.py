#!/usr/bin/env python3
"""test_lsu_cache_resp_classify.py — [0202-T02F2-MSHR] 响应分类契约测试驱动。

做三件事：
  1. 从**权威源** `CHAOS/gem5/src/mem/packet.cc` 的 commandTable 解析各 command 的
     flags（真实生产数据，不是日志字符串）；
  2. 用这些 flags 编译并运行 `tests/chaos_cache_resp_test.cc`（standalone，不链接
     gem5），钉死 BaseCache::recvTimingResp 的响应分类规格；
  3. 红线守卫：`assert(mshr)` 与 `setBadAddress` 不得被删除/绕过，且不得出现
     「无 MSHR 就静默返回」这类吞响应的写法。

根因（实测，2026-10-27）：UC 写走 write buffer 不分配 MSHR；其 BadAddressError 响应
的 flags 只有 {IsResponse,IsError}（**不含 IsWrite**），于是 `pkt->isWrite()` 为假、
跳过 handleUncacheableWriteResp、落到 `assert(mshr)` ⇒ SIGABRT。

用法：python3 tests/test_lsu_cache_resp_classify.py   （退出码 0=全 PASS）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKET_CC = ROOT / "CHAOS/gem5/src/mem/packet.cc"
BASE_CC = ROOT / "CHAOS/gem5/src/mem/cache/base.cc"
HARNESS = ROOT / "tests/chaos_cache_resp_test.cc"

FAILED = []


def check(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name
          + (("  :: " + str(detail)) if detail and not ok else ""))
    if not ok:
        FAILED.append(name)


def parse_flags(src, cmd):
    """从 commandTable 行里取某 command 的 flag 集合（真实生产数据）。

    行形如：  { {IsWrite, IsResponse}, InvalidCmd, "WriteResp" },
    """
    m = re.search(r"\{\s*\{([^}]*)\}\s*,\s*\w+\s*,\s*\"%s\"\s*\}" % re.escape(cmd), src)
    if not m:
        return None
    return {f.strip() for f in m.group(1).split(",") if f.strip()}


def main():
    src = PACKET_CC.read_text(errors="replace")

    print("[1] commandTable 真实 flags（CHAOS/gem5/src/mem/packet.cc）")
    CMDS = ["WriteResp", "ReadResp", "ReadError", "BadAddressError", "WriteError"]
    flags = {}
    for c in CMDS:
        f = parse_flags(src, c)
        flags[c] = f
        check(f"找到 {c} 且含 IsResponse", f is not None and "IsResponse" in f, f)
    if any(v is None for v in flags.values()):
        print(f"\nFAILED ({len(FAILED)}): {FAILED}")
        return 1
    # 根因事实：BadAddressError 丢 IsWrite、带 IsError
    check("BadAddressError 不含 IsWrite（根因事实）", "IsWrite" not in flags["BadAddressError"])
    check("BadAddressError 含 IsError", "IsError" in flags["BadAddressError"])
    check("WriteResp 含 IsWrite（对照：正常写响应不丢）", "IsWrite" in flags["WriteResp"])
    check("ReadError 含 IsError 且不含 IsWrite", "IsError" in flags["ReadError"]
          and "IsWrite" not in flags["ReadError"])
    check("WriteError 含 IsWrite（error 也可能保留写位）", "IsWrite" in flags["WriteError"])

    print("[2] 编译并运行 standalone harness（真实 flags 经 -D 注入）")
    defs = []
    for c in CMDS:
        up = re.sub(r"[^A-Za-z0-9]", "", c).upper()
        defs.append(f"-DCMD_{up}_ISWRITE={1 if 'IsWrite' in flags[c] else 0}")
        defs.append(f"-DCMD_{up}_ISERROR={1 if 'IsError' in flags[c] else 0}")
    with tempfile.TemporaryDirectory(prefix="respcls_") as td:
        exe = Path(td) / "h"
        cmd = ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
               "-I", str(ROOT / "CHAOS/gem5/src"), *defs,
               str(HARNESS), "-o", str(exe)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        check("harness 编译干净（-Wall -Wextra -Werror）", r.returncode == 0,
              (r.stderr or "")[-800:])
        if r.returncode != 0:
            print(f"\nFAILED ({len(FAILED)}): {FAILED}")
            return 1
        rr = subprocess.run([str(exe)], capture_output=True, text=True)
        tail = (rr.stdout or "").strip().splitlines()
        for line in tail:
            print("      " + line)
        check("harness 运行 rc==0 且 ALL PASS",
              rr.returncode == 0 and tail and tail[-1] == "ALL PASS",
              f"rc={rr.returncode} last={tail[-1] if tail else '<empty>'}")

    print("[3] 红线守卫（不得删断言 / 不得吞响应）")
    b = BASE_CC.read_text(errors="replace")
    check("base.cc 仍保留 assert(mshr)", "assert(mshr)" in b)
    check("未把 assert(mshr) 注释掉",
          not re.search(r"//\s*assert\(mshr\)", b))
    check("未出现「无 MSHR 即静默返回」的兜底写法",
          not re.search(r"if\s*\(\s*!?\s*mshr\s*\)\s*\{?\s*return", b)
          and "if (!mshr) return" not in b)
    check("packet.cc 仍定义 BadAddressError", '"BadAddressError"' in src)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
