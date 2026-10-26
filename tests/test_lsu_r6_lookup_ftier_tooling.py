#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-FIXTOOLS] armtlb lookup-mode F-tier 工具侧 + 运行时能力证明。

C++ `6ec7c5aa`（origin/r6-fixcpp）已把真实 lookup-tier 触发落到
CHAOSArmTLB::lookupTierMounted / lookupTierAllowsInjection（F0 legacy；
F1-F6 经 chaos_lsu_trigger.hh 既有语义；固定 seed=7 实测 F0=几何跳步、
F2 首触发 96722 且间隔∈[50k,150k)、F6=index 0，三者互异）。工具侧必须：

  ① 让 T02-F2/T04-F2/T04-F6 传**真实** `--tlb_lsu_tier F2/F6`（六格两两命令不同）；
  ② F0 保持 legacy（无 `--tlb_lsu_tier`，`--tlb_max_faults 1`）——逐字节不变；
  ③ 未知档位（F7/off）**响亮 BLOCKED**，绝不静默退回 F0；
  ④ F1-F6 **不因工具允许就默认可信**：运行时必须由新二进制打印
     CHAOS_LSU_TIER_CAP 启动标记（requested/effective/lookup_tier_enabled），
     campaign 核对 effective==requested 且 enabled=1；
  ⑤ 旧二进制（无标记）/不一致/禁用 ⇒ **响亮拒绝**，绝不产出静默退化数据。

用法：python3 tests/test_lsu_r6_lookup_ftier_tooling.py   （exit 0 = 全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _cell(model, freq, runid, wl="TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页）"):
    row = [""] * 12
    row[LC.COL_RUNID] = runid
    row[LC.COL_MODEL] = model
    row[LC.COL_UNIT] = "L1d-TLB"
    row[LC.COL_FREQ] = freq
    row[LC.COL_WORKLOAD] = wl
    return row


def _flags(model, freq, rid):
    return LC.resolve_cell(_cell(model, freq, rid))[0]


SIX = [("T01", "F0"), ("T02", "F0"), ("T02", "F2"),
       ("T04", "F0"), ("T04", "F2"), ("T04", "F6")]
SIX_RUNIDS = [f"{m}-{f}-W4" for m, f in SIX]


def main():
    print("[1] 六格两两命令不同（缺陷：曾坍缩成 3 个条件）")
    res = {rid: _flags(m, f, rid) for (m, f), rid in zip(SIX, SIX_RUNIDS)}
    norms = [None if res[r] is None else tuple(res[r]) for r in SIX_RUNIDS]
    runnable = [n for n in norms if n is not None]
    check("六格全部 runnable 且两两命令互异",
          len(runnable) == 6 and len(set(runnable)) == 6,
          f"norms={norms}")

    print("[2] F2/F6 传真实 --tlb_lsu_tier <F>（值等于请求档位）")
    for rid, want in (("T02-F2-W4", "F2"), ("T04-F2-W4", "F2"),
                      ("T04-F6-W4", "F6")):
        fl = res[rid] or []
        i = fl.index("--tlb_lsu_tier") if "--tlb_lsu_tier" in fl else -1
        check(f"{rid} 带 --tlb_lsu_tier {want}", i >= 0 and fl[i + 1] == want,
              str(fl[-6:]))

    print("[3] F0 保持 legacy（无 --tlb_lsu_tier；--tlb_max_faults 1）")
    for rid in ("T01-F0-W4", "T02-F0-W4", "T04-F0-W4"):
        fl = res[rid] or []
        i = fl.index("--tlb_max_faults") if "--tlb_max_faults" in fl else -1
        check(f"{rid} F0 = --tlb_max_faults 1 且无 --tlb_lsu_tier",
              i >= 0 and fl[i + 1] == "1" and "--tlb_lsu_tier" not in fl,
              str(fl))

    print("[4] F2/F6 命令 != 同模型 F0 命令（非静默改档）")
    for rid, f0 in (("T02-F2-W4", "T02-F0-W4"), ("T04-F2-W4", "T04-F0-W4"),
                    ("T04-F6-W4", "T04-F0-W4")):
        check(f"{rid} != {f0}", tuple(res[rid]) != tuple(res[f0]),
              f"{res[rid][-4:]} vs {res[f0][-4:]}")

    print("[5] F1-F6 lookup 档位在解析层可表达（不再 TIER-UNIMPL）")
    for rid, m, f in (("T02-F2-W4", "T02", "F2"), ("T04-F6-W4", "T04", "F6"),
                      ("T01-F1-W4", "T01", "F1"), ("T03-F5-W4", "T03", "F5")):
        fl, _g, why = LC.resolve_cell(_cell(m, f, rid))
        check(f"{rid} runnable（不落 armtlb-lookup-tier-unimplemented）",
              fl is not None and "armtlb-lookup-tier-unimplemented" not in (why or ""),
              str(why))

    print("[6] 未知档位（F7/off）响亮 BLOCKED（绝不退回 F0）")
    for rid, m, f in (("T04-F7-W4", "T04", "F7"), ("T02-off-W4", "T02", "off")):
        fl, _g, why = LC.resolve_cell(_cell(m, f, rid))
        check(f"{rid} BLOCKED 且理由点名 lookup-tier-unimplemented",
              fl is None and "armtlb-lookup-tier-unimplemented" in (why or ""),
              str(why)[:80])

    print("[7] 运行时能力标记：present+一致 ⇒ ok")
    ok_txt = "info: CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1"
    g = LC.lookup_tier_capability_gate("F2", ok_txt)
    check("F2 一致标记 ⇒ ok（effective==requested, enabled=1）", g["ok"],
          str(g))
    check("解析出 requested/effective/enabled 三字段",
          g["marker"]["requested"] == "F2" and g["effective"] == "F2"
          and g["enabled"] == "1", str(g["marker"]))

    print("[8] 旧二进制（无标记）⇒ 响亮拒绝")
    g = LC.lookup_tier_capability_gate("F2", "gem5 simulated 1234567 ticks\n")
    check("无标记 ⇒ ok=False 且理由点名 capability-missing",
          not g["ok"] and "capability-missing" in g["reason"], str(g))

    print("[9] requested≠effective ⇒ 拒绝；enabled=0 ⇒ 拒绝；缺字段 ⇒ 拒绝")
    g = LC.lookup_tier_capability_gate(
        "F2", "CHAOS_LSU_TIER_CAP: requested=F2 effective=F0 lookup_tier_enabled=1")
    check("effective=F0≠requested=F2 ⇒ 拒绝（不得静默退化）",
          not g["ok"] and "capability-mismatch" in g["reason"], str(g))
    g = LC.lookup_tier_capability_gate(
        "F6", "CHAOS_LSU_TIER_CAP: requested=F6 effective=F6 lookup_tier_enabled=0")
    check("lookup_tier_enabled=0 ⇒ 拒绝",
          not g["ok"] and "capability-disabled" in g["reason"], str(g))
    g = LC.lookup_tier_capability_gate(
        "F6", "CHAOS_LSU_TIER_CAP: requested=F6 effective=F6")
    check("标记缺 lookup_tier_enabled ⇒ 拒绝",
          not g["ok"] and "capability-malformed" in g["reason"], str(g))

    print("[10] F0 lookup 无需能力标记（legacy，不触碰）")
    check("ARMTLB_LOOKUP_LEGACY_TIERS == {F0}", LC.ARMTLB_LOOKUP_LEGACY_TIERS
          == frozenset({"F0"}))
    check("ARMTLB_LOOKUP_TIERED_TIERS == {F1..F6}",
          LC.ARMTLB_LOOKUP_TIERED_TIERS
          == frozenset({"F1", "F2", "F3", "F4", "F5", "F6"}))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
