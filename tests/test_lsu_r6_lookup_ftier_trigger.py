#!/usr/bin/env python3
"""[MDSPEC][R6-FIXCPP/B] armtlb lookup 路径 F 档位：真实 polling + 触发序列。

缺陷（R6-FTIER，实测 2026-10-24）：campaign 的 ARMTLB_LOOKUP_TIERS 把 lookup
模式的 F1-F6 全部显式 BLOCKED，理由**点名 C++ 事实**：「lookup 命中路径
（TLB::lookup -> maybeCorrupt / maybeCorruptLookup）**从不 poll lsuTrigger**，
只有 walk 路径 poll；Making them runnable needs a C++ change to CHAOSArmTLB
(out of this lane)」。即这六格在**物理上无法表达**，只能 F0。

本套件钉住 C++ 侧的修复与证据：
  [1] 真编译 + 真运行独立 C++ 单测（tests/chaos_armtlb_lookup_ftier_test.cc）：
      **固定 seed 的触发序列** —— F0（legacy 单次瞬态）/ F2（均值 10 万
      eligible events、±50% 抖动）/ F6（首个事件一次）三者触发位置**互不相同
      且可复现**；
  [2] 防漂移守卫：lookup 两个 hook 都必须真正 poll（lookupTierAllowsInjection
      调用 onEligible/onF6Event），F0 仍走 legacy（不因新增 polling 改变 F0）；
  [3] 频率不是新发明的：tier 间隔取自 chaos_lsu_trigger.hh（F2 = 100,000
      eligible events，与 05 r2-r8 / 方案 §5 sheet-5 一致）。

**注意（诚实）**：campaign/ready_contract 的 `ARMTLB_LOOKUP_TIERS = {"F0"}` 是
**冻结的 tools/**，本 lane 不得修改 —— 因此「T02-F2 不再 TIER-UNIMPL」这半边
（工具侧解锁）**不在本 lane 边界内**，已按停点规则上报；本套件只钉 C++ 半边的
真实性与可复现性，不声称工具侧已解锁。

用法：python3 tests/test_lsu_r6_lookup_ftier_trigger.py   （退出码 0=全 PASS）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHAOS/gem5/src"
HARNESS = ROOT / "tests/chaos_armtlb_lookup_ftier_test.cc"
ARM_CC = ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc"
TRIGGER_HH = ROOT / "CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh"

failed = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + ("" if cond or not detail else f"  [{detail}]"))
    if not cond:
        failed.append(name)


def main():
    print("[1] 固定 seed 触发序列：真编译 + 真运行（F0/F2/F6 位置不同且可复现）")
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "tlb_ftier_test"
        cc = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             f"-I{SRC}", str(HARNESS), "-o", str(exe)],
            capture_output=True, text=True, cwd=str(ROOT))
        ok = cc.returncode == 0
        check("harness compiles clean (-Wall -Wextra -Werror)", ok,
              (cc.stderr or "").strip()[:200])
        if ok:
            r = subprocess.run([str(exe)], capture_output=True, text=True)
            print((r.stdout or "").rstrip())
            check("harness ALL PASS", r.returncode == 0
                  and "ALL PASS" in (r.stdout or ""),
                  (r.stdout or "").strip()[-200:])
        else:
            print("  (harness did not build; behavioral checks skipped)")

    print("[2] 防漂移守卫：lookup 的**两个** hook 都真正 poll tier")
    arm = ARM_CC.read_text(encoding="utf-8")
    check("CHAOSArmTLB.cc 定义 lookupTierMounted / lookupTierAllowsInjection",
          "CHAOSArmTLB::lookupTierMounted()" in arm
          and "CHAOSArmTLB::lookupTierAllowsInjection(" in arm)
    check("lookupTierAllowsInjection 读 tier（onEligible / onF6Event）",
          "lsuTrigger->onEligible()" in arm
          and "lsuTrigger->onF6Event(false)" in arm)
    # maybeCorrupt 与 maybeCorruptLookup 都必须调用该 gate（每个 lookup 恰好
    # 一次 → 单一 eligible 流，不重复计数）。
    n_gate = len(re.findall(r"lookupTierAllowsInjection\(", arm))
    check("两个 lookup hook 各有一处 gate 调用（+定义 1 处 = 3）",
          n_gate == 3, f"n={n_gate}")
    check("F0 仍走 legacy（maxFaults/probability/events_to_skip 仍在）",
          "faults_injected_count >= max_faults" in arm
          and "events_to_skip > 0" in arm)
    check("legacy 分支被 lookupTierMounted() 门控（F0 不受影响）",
          "if (lookupTierMounted()) {" in arm)
    # 旧缺陷形状不得复活：lookup 路径不得只靠 legacy（无 tier 调用）。
    check("lookup 路径不再完全无视 tier",
          "lookupTierAllowsInjection" in arm)

    print("[3] 频率取自 chaos_lsu_trigger.hh（不自行发明）")
    trig = TRIGGER_HH.read_text(encoding="utf-8")
    check("F2 = 100,000 eligible events（05 r2-r8）",
          re.search(r"F2: return\s+100000;", trig) is not None)
    check("±50% 抖动由 scheduleNext 实现（U[iv/2, 3iv/2)）",
          "next_fire = from + iv / 2 + rng % iv;" in trig)
    check("F6 = 事件触发（onF6Event），非间隔",
          "onF6Event" in trig and "F6 fires on the event" in trig)

    print()
    if failed:
        print(f"FAILURES: {failed}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
