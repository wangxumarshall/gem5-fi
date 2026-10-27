#!/usr/bin/env python3
"""[MDSPEC][R4-6-T08] T08 walk-issue 路由契约测试（真 walk 是否可能发生）。

R4-5.9 pilot 的实测失败（round4_findings.md §5.9.6）：
  Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8,
  old_pfn: 0x81d75, new_pfn: 0x81d75, FaultType: walk_pairing, Mask: 0x4000000
即 faultType=walk_pairing 被 TLB **lookup-hit 路径抢先消费**（old_pfn == new_pfn
= 未变异），maxFaults=1 的预算在那一刻用光 → TableWalker::walk 的
maybeDropWalkFill 恒 false → 整跑没有 tlb_walk/tlb_refill。

本测试钉住修复后的三条不变量（可执行断言优先，源码断言补足 C++ 面）：
  [A] maybeCorrupt 对 WalkPairing 在**任何预算/RNG/events_to_skip 消耗之前**
      就 return（顺序断言，不是"存在"断言），且有一次性诊断行（不静默）；
      switch 里另有显式 `case WalkPairing: return;`。
  [B] walker 接线存在且唯一：config 传 walker=<cpu0.mmu.walker>、ctor
      walker->setChaosTLB(this)、table_walker.cc 在 walk 发出点查 chaosTLB；
      ArmMMU 只有 1 个 TableWalker 实例；TLB 无 serialize（restore 后 TLB 冷
      → 必然产生真 walk）。
  [C] 配置/campaign 面：walk_pairing 缺 injector 或缺 tier 时 Python 侧早失败；
      campaign 解析出的 T08 flags 带 pin 住的 F0 窗；--allow-blocked-models
      能跑通被 MODEL_BLOCKED 的 cell 且不改 block 语义。
  [D] 注入落点判据字符串存在：arm_tlb_walk_issue_probe / arm_tlb_walk_issue_drop，
      且不再有 lookup-hit 上的 walk_pairing 变异路径。

C++ 为 COMPILE-UNVERIFIED（本 worktree 禁 build）；[A][B] 是源码级顺序断言，
真正的判据只能由主 agent 的真机 FS run 给出（见 R4-6-T08 报告）。

用法：python3 tests/test_lsu_hook_t08_walk.py   （退出码 0 = 全 PASS）
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as lc                          # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def _cell(model, freq, workload, run_id):
    n = max(lc.COL_RUNID, lc.COL_MODEL, lc.COL_FREQ, lc.COL_WORKLOAD) + 1
    c = [""] * n
    c[lc.COL_RUNID] = run_id
    c[lc.COL_MODEL] = model
    c[lc.COL_FREQ] = freq
    c[lc.COL_WORKLOAD] = workload
    return c


def _body(src, start_marker, end_marker):
    """Slice one function body out of a .cc file (after the marker)."""
    i = src.index(start_marker)
    j = src.index(end_marker, i)
    return src[i:j]


def main():
    tlb_cc = (ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc").read_text()
    tlb_hh = (ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh").read_text()
    fs_py = (ROOT / "configs/se/arm_chaos_fs.py").read_text()
    tw_cc = (ROOT / "CHAOS/gem5/src/arch/arm/table_walker.cc").read_text()
    tw_hh = (ROOT / "CHAOS/gem5/src/arch/arm/table_walker.hh").read_text()
    mmu_py = (ROOT / "CHAOS/gem5/src/arch/arm/ArmMMU.py").read_text()
    mmu_cc = (ROOT / "CHAOS/gem5/src/arch/arm/mmu.cc").read_text()
    tlb_hh_arm = (ROOT / "CHAOS/gem5/src/arch/arm/tlb.hh").read_text()
    sample_hh = (ROOT / "CHAOS/gem5/src/cpu/o3/chaos_event_sample.hh").read_text()

    print("[A] maybeCorrupt：WalkPairing 不再在 lookup-hit 被消费（顺序断言）")
    mc = _body(tlb_cc, "CHAOSArmTLB::maybeCorrupt(", "CHAOSArmTLB::registerTrace(")
    i_guard = mc.find("fault_type_enum == FaultType::WalkPairing")
    check("maybeCorrupt 有 WalkPairing 早退守卫", i_guard != -1)
    # 顺序：守卫必须早于任何预算/RNG/理论事件消耗点。
    for probe in ("max_faults != 0 && faults_injected_count",
                  "events_to_skip > 0",
                  "random_fault_distribution(",
                  "switch (chosen)"):
        j = mc.find(probe)
        check(f"WalkPairing 守卫早于 `{probe}`", i_guard != -1 and j != -1
              and i_guard < j, f"guard@{i_guard} probe@{j}")
    # 守卫块本身（到 return; 为止）不得动预算/RNG/events_to_skip —— 否则
    # lookup-hit 仍会替 walk 花掉 maxFaults 或推进 F0 抽签。
    guard_block = mc[i_guard:mc.index("// TLB has no direct curCycle()", i_guard)]
    check("守卫块内不消耗预算/抽签（无 ++faults_injected_count / events_to_skip）",
          "++faults_injected_count" not in guard_block
          and "events_to_skip" not in guard_block
          and "rng" not in guard_block, guard_block[-160:].replace("\n", " "))
    check("lookup-hit 下打印一次性诊断行（不静默）",
          "arm_tlb_lookup_hit_skipped" in mc and "walk_pairing_lookup_notice" in mc)
    # The current tree implements the unreachable arm as a loud `default:
    # return;` with a comment naming WalkPairing (an explicit
    # `case FaultType::WalkPairing: return;` is also acceptable).
    check("switch 内显式 no-op 守卫（不可达响亮返回）",
          re.search(r"case FaultType::WalkPairing:\s*(?://[^\n]*\n\s*)*return;", mc)
          is not None
          or re.search(r"//[^\n]*WalkPairing[^\n]*\n(?:\s*//[^\n]*\n)*\s*default: return;", mc)
          is not None)

    print("[A2] 其它 fault type 逐字节不受影响（守卫/T08-only 探针）")
    i_other = mc.find("// TLB has no direct curCycle(); use curTick()")
    check("bit_flip/stuck/pfn_to_mapped_page 路径仍在守卫之后原样存在",
          i_other != -1
          and all(k in mc[i_other:] for k in
                  ("case FaultType::StuckAtZero:", "case FaultType::StuckAtOne:",
                   "case FaultType::BitFlip:", "FaultType::PfnToMappedPage")))
    dw = _body(tlb_cc, "CHAOSArmTLB::maybeDropWalkFill(", "\n    // §1.2 protection-aware")
    # [R4-10] the gate widened from WalkPairing to the whole walk/refill
    # family (isWalkFamily) so T08-b/c/d share the issue-point funnel; the
    # INTENT is unchanged — a non-walk mode returns before onAttempt().
    check("maybeDropWalkFill 首行是 walk 家族门（其它 mode 立即返回 false）",
          dw.index("isWalkFamily(fault_type_enum)")
          < dw.index("lsuTrigger->onAttempt()"))
    check("walk 发出点探针行存在（wiring 证明，且 T08-only）",
          "arm_tlb_walk_issue_probe" in dw and "walk_pairing_probe_notice" in dw)
    check("drop 落点判据字符串保持 arm_tlb_walk_issue_drop",
          "arm_tlb_walk_issue_drop" in dw)
    check("hh 声明两个一次性标志（T08-only 诊断）",
          "walk_pairing_lookup_notice" in tlb_hh and "walk_pairing_probe_notice" in tlb_hh)

    print("[B] walker 接线（config + 自挂 + 唯一实例 + TLB 冷启动）")
    # [R4-6.0] the kwarg is now assembled into _tlb_kwargs and injected only
    # for walk_pairing: passing walker=None for the lookup modes made gem5's
    # param conversion call Class(None) -> TypeError, killing EVERY FS run at
    # instantiate time (see round4_findings §R4-6.0).
    # [R4-10] the walker kwarg is now gated on the walk FAMILY
    # (WALK_FAULT_TYPES), so T08-b/c/d also get the walker; the lookup modes
    # still never pass walker= (the R4-6.0 None-param crash stays fixed).
    check("FS config 在 walk 家族下把 walker=cpu0.mmu.walker 交给 CHAOSArmTLB",
          "if args.tlb_fault_type in WALK_FAULT_TYPES:" in fs_py
          and '_tlb_kwargs["walker"] = cpu0.mmu.walker' in fs_py)
    _kw = (fs_py.split("_tlb_kwargs = dict(")[1].split("if args.tlb_fault_type")[0]
           if "_tlb_kwargs = dict(" in fs_py else "")
    check("其余 fault type 不设 walker 参数（不得传 None）",
          "_tlb_kwargs = dict(" in fs_py and "walker" not in _kw)
    check("ctor 自挂 walker->setChaosTLB(this)",
          "walker->setChaosTLB(this)" in tlb_cc)
    check("table_walker 在 walk 发出点查 chaosTLB->maybeDropWalkFill",
          "if (chaosTLB)" in tw_cc and "maybeDropWalkFill(" in tw_cc)
    check("walk_id 在 WalkerState 构造时赋值（配对键）",
          "++chaosNextWalkId" in tw_cc and "chaosWalkId" in tw_hh)
    check("ArmMMU 只声明一个 walker（Param.ArmTableWalker）",
          mmu_py.count("walker = Param.ArmTableWalker(") == 1)
    check("itb/dtb/stage2 共用同一 walker 实例（钩子不会漏侧）",
          "getDTBPtr()->setTableWalker(walker)" in mmu_cc
          and "itbStage2->setTableWalker(walker)" in mmu_cc)
    check("mmu.cc 的 D 侧 walk 调用点就是 TableWalker::walk 本体",
          "walker->walk(req, tc," in mmu_cc)
    check("ARM TLB 不序列化（restore 后 TLB 冷 -> 必然真 walk）",
          "serialize" not in tlb_hh_arm and "class TLB : public BaseTLB" in tlb_hh_arm)

    print("[C] 配置/campaign 面：早失败 + T08 flags + blocked opt-in")
    # [R4-10] the refusal block is now gated on the walk FAMILY
    # (WALK_FAULT_TYPES) so the T08-b/c/d sub-models get the same早失败.
    i_val = fs_py.index("if args.tlb_fault_type in WALK_FAULT_TYPES:")
    check("config 有 walk 家族早失败块（chaos_armtlb + tier）",
          "--chaos_armtlb" in fs_py[i_val:i_val + 1600]
          and 'args.tlb_lsu_tier == "off"' in fs_py[i_val:i_val + 1600])
    check("早失败在 SimObject 构造之前（ctor panic 之前就退）",
          i_val < fs_py.index("arm_tlb = CHAOSArmTLB("))

    wl = "TLB-AliasPerm 地址翻译探针"
    # [R6-PROPAGATION-V3] T08-F0-W4 is the explicit T08-a canary; W9 is a
    # hard workload gap (never tlb_probe).
    c = _cell("T08", "F0", wl, "T08-F0-W4")
    blocked = lc.resolve_cell(c)
    check("T08-F0-W4 default -> blocked PARTIAL reason",
          blocked[0] is None and "PARTIAL_SUBMODEL_PROVEN" in (blocked[2] or ""),
          str(blocked))
    flags, golden, carrier = lc.resolve_cell(c, t08a_canary=True)
    check("explicit --t08a-canary resolves FS flags", flags is not None)
    for need in ("--tlb_fault_type", "walk_pairing", "--tlb_lsu_tier", "F0",
                 "--tlb_lsu_warmup_events", str(lc.ARMTLB_T08_WARMUP_EVENTS),
                 "--tlb_lsu_span_events", str(lc.ARMTLB_T08_SPAN_EVENTS),
                 "--chaos_armtlb"):
        check(f"T08-a canary flags 含 {need}", need in flags, str(flags[-10:]))
    check("T08 走 tlb_probe 载体 + host golden",
          carrier == "fs:tlb_probe" and golden == lc.TLB_PROBE_GOLDEN)
    c4 = _cell("T08", "F4", wl, "T08-F4-W4")
    f4 = lc.resolve_cell(c4, t08a_canary=True)[0]
    check("F4 canary 同样带 tier（F4 而非 F0）",
          f4 is not None and "--tlb_lsu_tier" in f4 and "F4" in f4,
          str(f4[-8:] if f4 else f4))
    c6 = _cell("T08", "F6", wl, "T08-F6-W4")
    f6 = lc.resolve_cell(c6, t08a_canary=True)[0]
    check("F6 is not a canary (canary is W4 F0/F4 seed1 only)", f6 is None)
    for w9 in ("T08-F0-W9", "T08-F4-W9"):
        got = lc.resolve_cell(_cell("T08", w9.split("-")[1], "GAP/Graph500",
                                    w9), allow_blocked=True,
                              t08a_canary=True)
        check(f"{w9} hard BLOCKED_WORKLOAD_GAP", got[0] is None
              and got[2].startswith("BLOCKED_WORKLOAD_GAP"), str(got))
    t01 = lc.resolve_cell(_cell("T01", "F0", wl, "T01-F0-W4"))
    check("T01 lookup 模式不带 tier/warmup/span（逐字节不变）",
          t01[0] is not None and "--tlb_lsu_tier" not in t01[0]
          and "--tlb_lsu_span_events" not in t01[0])
    check("T08 is NOT in MODEL_BLOCKED (narrow RunID gate instead)",
          "T08" not in lc.MODEL_BLOCKED)

    print("[C2] F0 抽签可预测（用 chaos_event_sample.hh 的真实 LCG 常量复算）")
    m = re.search(r"return x \* (\d+)ULL \+ (\d+)ULL;", sample_hh)
    check("从 chaos_event_sample.hh 解析出 LCG 常量", m is not None)
    a, cc = int(m.group(1)), int(m.group(2))
    mask64 = (1 << 64) - 1

    def lcg(x):
        return (x * a + cc) & mask64

    for seed, want in ((1, 412), (2, 417), (3, 806)):
        got = lcg(seed) % lc.ARMTLB_T08_SPAN_EVENTS + lc.ARMTLB_T08_WARMUP_EVENTS
        check(f"seed {seed} -> F0 落点 walk#{got}", got == want,
              f"computed={got} documented={want}")
    check("F4 首发落点在 5e4..1.5e5 量级（预算风险需真机确认）",
          50000 <= (50000 + lcg(1) % 100000) <= 150000)

    print("[D] 判据字符串（主 agent 真机 FS run 的 grep 目标）")
    check("probe 行格式含 Tick/Site/walk_id/VA",
          all(k in dw for k in ("Tick: ", "Site: arm_tlb_walk_issue_probe",
                                "walk_id: ", "VA: 0x")))
    check("drop 行格式保持 Tick/Site/walk_id/VA（R4-5.9 判据不变）",
          all(k in dw for k in ("Site: arm_tlb_walk_issue_drop", "walk_id: ",
                                "VA: 0x")))
    check("lookup-hit 诊断行含 Site: arm_tlb_lookup_hit_skipped",
          "Site: arm_tlb_lookup_hit_skipped" in mc)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
