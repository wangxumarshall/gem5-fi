#!/usr/bin/env python3
"""[MDSPEC][R6-FIXCPP/A] TLB 故障链「注册门控 + 含住撤销」契约。

缺陷（实测 T01-F0-W4/seed1，契约钉子 tests/test_lsu_r6_contained_chain_contract.py）：
注入翻转 pfn bit 56，`pfn<<12` 在 64 位 Addr 里回绕 ⇒ **有效 PA 未变**
（0x81d75fa8 == 0x81d75fa8），注入点自判 `pa_changed=0`；但
`registerTlbFault` 的 **seq-primary 归属臂对任何 `req_seq != 0` 无条件注册**
（CHAOSPropagation.cc），于是**同一请求**后续的干净事件（sq_execute ->
sq_writeback -> resp -> taint_reg）仍按 seq 并入本链 —— 一条链同时断言
"L2 已含住（effective_pa_unchanged）"与"已传播到 L4"，checker（裁决 D，保持
严格）以 `time_reversed_edge` 响亮拒绝。

本套件钉住修复的两半（共享决策源 CHAOSPropagation/chaos_tlb_chain.hh）：
  ① **注册门控**：`pa_changed == 0` 的请求**根本不进入下游归属**（无 seq 臂、
     无 addr_fallback 臂），该请求后续干净事件无法再挂到该 fault ancestry；
  ② **含住撤销**：翻译在 L2 收口（含住）时**撤销**该链已开的归属臂，防残留
     映射（含 blocked 翻译：PA 可能已变，但翻译根本不发生）。
  ③ 真实转发（pa_changed=1）行为**不变**：seq 臂照旧、传播继续（不得过度修复）。

三部分证据：
  [1] 真编译 + 真运行独立 C++ 单测（tests/chaos_tlb_chain_containment_test.cc）；
  [2] 防漂移守卫：CHAOSPropagation.cc 必须真正调用同一决策函数（否则谓词形同虚设）；
  [3] 修复目标形状在同一严格 checker 下准入（option-2 含住），现状形状仍被拒。

用法：python3 tests/test_lsu_r6_tlb_chain_containment.py   （退出码 0=全 PASS）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHAOS/gem5/src"
HARNESS = ROOT / "tests/chaos_tlb_chain_containment_test.cc"
HDR = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/chaos_tlb_chain.hh"
PROP_CC = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc"
PROP_HH = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"
CONTRACT = ROOT / "tests/test_lsu_r6_contained_chain_contract.py"

failed = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + ("" if cond or not detail else f"  [{detail}]"))
    if not cond:
        failed.append(name)


def main():
    print("[1] 独立 C++ 单测：真实编译 + 真实运行（注册门控 + 含住撤销）")
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "tlb_chain_test"
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
                  (r.stdout or "").strip()[-160:])
        else:
            print("  (harness did not build; behavioral checks skipped)")

    print("[2] 防漂移守卫：CHAOSPropagation 必须真正调用同一决策函数")
    prop = PROP_CC.read_text(encoding="utf-8")
    hh = PROP_HH.read_text(encoding="utf-8")
    check("CHAOSPropagation.cc includes chaos_tlb_chain.hh",
          "CHAOSPropagation/chaos_tlb_chain.hh" in prop)
    check("registerTlbFault gates on chaos_chain::tlbRegistrationArms",
          "chaos_chain::tlbRegistrationArms(" in prop)
    check("noteTlbTranslationResult uses chaos_chain::translationContained",
          "chaos_chain::translationContained(" in prop)
    check("containment revokes the chain's arms (revokeChainArms called)",
          "revokeChainArms(" in prop and "revokeChainArms =" not in prop)
    check("revokeChainArms declared on the class", "revokeChainArms" in hh)
    # 旧缺陷形状不得复活：seq-primary 归属臂不得再对 req_seq 单独无条件开。
    check("no unconditional `if (req_seq)` seq-primary registration remains",
          not re.search(r"// PRIMARY \(seq-bound\).*?\n\s*if \(req_seq\) \{",
                        prop, re.S),
          "seq-primary arm must be gated by the pa_changed verdict")

    print("[3] 修复目标形状在同一严格 checker 下准入（现状形状仍被拒）")
    r = subprocess.run([sys.executable, str(CONTRACT)],
                       capture_output=True, text=True, cwd=str(ROOT))
    check("77c318f9 含住链发射契约测试仍全绿（不得放宽 checker）",
          r.returncode == 0 and "ALL PASS" in (r.stdout or ""),
          (r.stdout or "").strip()[-200:])

    print()
    if failed:
        print(f"FAILURES: {failed}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
