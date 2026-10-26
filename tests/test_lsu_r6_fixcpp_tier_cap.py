#!/usr/bin/env python3
"""[MDSPEC][R6-FIXCPP/T1] lookup-tier 运行时能力标记（不跑仿真）。

工具侧契约（FIX-TOOLS `ea17e3c9`，冻结，不在本 worktree）：
  `tools/lsu_campaign.py` 的 `lookup_tier_capability_gate(requested, text)` 只认
  启动标记 `CHAOS_LSU_TIER_CAP: requested=<F0..F6|off> effective=<F0..F6|off>
  lookup_tier_enabled=<0|1>`，且要求 effective==requested==请求值 且 enabled==1；
  缺标记（旧二进制）/缺字段/不一致/禁用 ⇒ 一律 blocked=True, admitted=False。

本套件钉 C++ 半边（本 lane 交付）：
  [1] 真编译 + 真运行独立单测（tests/chaos_lsu_tier_cap_test.cc）——标记行逐字钉死；
  [2] 打印样例（F0 / F2 / F6）在本套件内用**冻结契约的本地镜像** `_gate()` 复核
      （F1-F6 ⇒ ok；F0 ⇒ 不该被 F2/F6 门采信）；
  [3] 防漂移守卫：CHAOSArmTLB.cc 真调用共享标记函数 chaos_lsu_tier_cap::marker，
      且 mounted tier 取自真实 lsuTrigger->tier（不谎报 enabled）。

用法：python3 tests/test_lsu_r6_fixcpp_tier_cap.py   （exit 0 = 全 PASS）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHAOS/gem5/src"
HARNESS = ROOT / "tests/chaos_lsu_tier_cap_test.cc"
ARM_CC = ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc"
CAP_HH = ROOT / "CHAOS/gem5/src/cpu/o3/chaos_lsu_tier_cap.hh"

failed = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + ("" if cond or not detail else f"  [{detail}]"))
    if not cond:
        failed.append(name)


def _gate(requested, text):
    """Frozen-contract mirror of lookup_tier_capability_gate (returns ok, reason).

    Same semantics as tools/lsu_campaign.py ea17e3c9: a marker line must be
    present with all three fields; effective == requested; enabled == 1 (or one
    of the truthy spellings); and the marker's own requested field must be empty
    or equal to the requested value.
    """
    rec = None
    for ln in (text or "").splitlines():
        i = ln.find("CHAOS_LSU_TIER_CAP:")
        if i < 0:
            continue
        rec = {}
        for tok in ln[i + len("CHAOS_LSU_TIER_CAP:"):].strip().split():
            k, sep, v = tok.partition("=")
            if sep:
                rec[k] = v
        break
    if rec is None:
        return False, "capability-missing"
    for f in ("requested", "effective", "lookup_tier_enabled"):
        if f not in rec or not rec[f].strip():
            return False, "capability-malformed"
    if rec["lookup_tier_enabled"] not in ("1", "true", "True", "yes"):
        return False, "capability-disabled"
    if rec["effective"] != requested:
        return False, "capability-mismatch"
    if rec["requested"] not in ("", requested):
        return False, "capability-mismatch"
    return True, ""


def main():
    print("[1] 真编译 + 真运行独立单测（标记行逐字钉死）")
    out = ""
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "tier_cap_test"
        cc = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             f"-I{SRC}", str(HARNESS), "-o", str(exe)],
            capture_output=True, text=True, cwd=str(ROOT))
        ok = cc.returncode == 0
        check("harness compiles clean (-Wall -Wextra -Werror)", ok,
              (cc.stderr or "").strip()[:200])
        if ok:
            r = subprocess.run([str(exe)], capture_output=True, text=True)
            out = r.stdout or ""
            print(out.rstrip())
            check("harness ALL PASS", r.returncode == 0 and "ALL PASS" in out,
                  out.strip()[-200:])
        else:
            print("  (harness did not build; behavioral checks skipped)")

    print("[2] 打印样例用冻结契约的本地镜像复核（F0 与 F2/F6）")
    by_req = {}
    for m in re.finditer(r"(requested=\S+) (effective=\S+) "
                         r"(lookup_tier_enabled=\S+)", out):
        req = m.group(1).split("=", 1)[1]
        by_req[req] = f"CHAOS_LSU_TIER_CAP: {m.group(1)} {m.group(2)} {m.group(3)}"
    check("见到 F0 打印样例", "F0" in by_req, str(sorted(by_req)))
    check("见到 F2 打印样例", "F2" in by_req, str(sorted(by_req)))
    check("见到 F6 打印样例", "F6" in by_req, str(sorted(by_req)))
    if "F2" in by_req:
        g = _gate("F2", by_req["F2"])
        check("F2 通过 F2 门（effective==requested, enabled=1）", g[0], f"{by_req['F2']} -> {g[1]}")
    if "F6" in by_req:
        g = _gate("F6", by_req["F6"])
        check("F6 通过 F6 门", g[0], f"{by_req['F6']} -> {g[1]}")
    if "F0" in by_req:
        g0 = _gate("F0", by_req["F0"])
        check("F0 行 enabled=0（legacy 不谎报）",
              "lookup_tier_enabled=0" in by_req["F0"], by_req["F0"])
        check("F0 行不得被 F2 门采信（否则静默退化）",
              _gate("F2", by_req["F0"])[0] is False, by_req["F0"])

    print("[3] 防漂移守卫：CHAOSArmTLB.cc 真调用共享标记函数")
    arm = ARM_CC.read_text(encoding="utf-8")
    check("CHAOSArmTLB.cc include chaos_lsu_tier_cap.hh",
          "chaos_lsu_tier_cap.hh" in arm)
    check("CHAOSArmTLB.cc 调用 chaos_lsu_tier_cap::marker",
          "chaos_lsu_tier_cap::marker(" in arm
          and "chaos_lsu_tier_cap::resolve(" in arm)
    check("mounted tier 取自真实 lsuTrigger->tier（不硬编码谎报）",
          "lsuTrigger->tier" in arm
          and re.search(r"const int mounted\s*=\s*lsuTrigger", arm) is not None)
    cap = CAP_HH.read_text(encoding="utf-8")
    check("共享头是唯一标记定义（依赖无关，只 include <string>）",
          "CHAOS_LSU_TIER_CAP: requested=" in cap
          and set(re.findall(r"#include\s*(<[^>]+>)", cap)) == {"<string>"})
    check("enabled 只由非 F0 触发决定（mounted_tier > 0）",
          "c.enabled = (mounted_tier > 0);" in cap)

    print()
    if failed:
        print(f"FAILURES: {failed}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
