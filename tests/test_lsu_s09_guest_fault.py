#!/usr/bin/env python3
"""S09/S03：LSQFwd 真实注入后必须 arm 受控 guest SEGV 终局。

根因（2026-10-30 实证，R6-S-REPAIR2）：S09-F0-W5 seed2 已有完整 L0→L5
（errant_commit，650 事件），但故障后下游野指针触发 GenericPageTableFault
时 `chaos::guestSegvArmed()` 仍为 false（只有 CHAOSAddrPath 会 arm），
gem5 panic/abort → gzip 无 EOF、stats.txt 0 字节、exit=-6 → 整条真实链
因证据截断被拒。

本测试钉死：
  1. 共享 header 提供 `noteChaosInjection()`（只 arm，不登记 VA）；
  2. LSQFwd 的每个真实注入汇点都调用它；
  3. faults.cc 先尝试 guest 处理，再检查 armed（无注入基线仍 panic）；
  4. 负向：count_only / 未注入路径不得 arm（源码级合同）。

用法：python3 tests/test_lsu_s09_guest_fault.py   退出码 0=全 PASS。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def src(path):
    return (ROOT / path).read_text(encoding="utf-8")


def body(text, signature, end_markers=("\n    }\n", "\n    bool\n",
                                      "\n    o3::DynInstPtr\n")):
    """Return the function body starting at `signature` up to the next end."""
    i = text.find(signature)
    if i < 0:
        return ""
    best = len(text)
    for m in end_markers:
        j = text.find(m, i + len(signature))
        if j >= 0:
            best = min(best, j)
    return text[i:best]


def main():
    h = src("CHAOS/gem5/src/base/chaos_guest_fault.hh")
    cc = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc")
    faults = src("CHAOS/gem5/src/sim/faults.cc")

    print("[1] shared header: arm-only injection hook")
    check("header exposes noteChaosInjection()",
          "noteChaosInjection()" in h)
    i = h.find("noteChaosInjection()")
    j = h.find("}", i) if i >= 0 else -1
    hb = h[i:j + 1] if i >= 0 and j >= 0 else ""
    check("it flips guestSegvArmed()", "guestSegvArmed() = true" in hb, hb[:200])
    check("it does not register a VA (no injectedGuestVas insert)",
          "injectedGuestVas" not in hb and "vas.insert" not in hb, hb[:200])

    print("[2] LSQFwd arms on every real injection sink")
    check("LSQFwd includes the guest-fault registry",
          '#include "base/chaos_guest_fault.hh"' in cc)
    sites = {
        "writeLog (S01/S02/S03/S09 data path)":
            body(cc, "CHAOSLSQFwd::writeLog"),
        "maybeSubstituteSource (S08 wrong source)":
            body(cc, "CHAOSLSQFwd::maybeSubstituteSource"),
        "violationCorrupt (L03)":
            body(cc, "CHAOSLSQFwd::violationCorrupt"),
        "maybeSwapResponseTarget (L04)":
            body(cc, "CHAOSLSQFwd::maybeSwapResponseTarget"),
        "s10SsidSubstCb (S10 SSIT)":
            body(cc, "CHAOSLSQFwd::s10SsidSubstCb(Addr store_pc"),
    }
    for name, b in sites.items():
        check(f"{name} calls chaos::noteChaosInjection()",
              "chaos::noteChaosInjection()" in b, b[:160])
    check("no arm in the pure attempt/eligibility path",
          "chaos::noteChaosInjection()" not in body(
              cc, "CHAOSLSQFwd::s10ViolationCb"))

    print("[3] faults.cc keeps real guest handling first and baseline panic")
    check("page-table fault handles via fixupFault first",
          faults.index("fixupFault") < faults.index("guestSegvArmed()"))
    check("unarmed baseline still panics",
          "panic_if(!handled" in faults)
    check("armed path exits via exitSimLoop with SIGSEGV",
          'exitSimLoop("chaos_guest_segv", 128 + SIGSEGV)' in faults)

    print("[4] terminal event stays conditional on the registered range")
    check("noteArchTranslationFault receives the exact-match flag",
          "noteArchTranslationFault(vaddr, exact)" in faults)
    check("downstream wild-pointer faults stay unattributed",
          "exact ? \"injected\" : \"downstream-unmapped\"" in faults)

    print(f"FAILED: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
