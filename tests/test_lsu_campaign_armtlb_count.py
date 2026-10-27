#!/usr/bin/env python3
"""test_lsu_campaign_armtlb_count.py — [R6-FIXCOUNT] armtlb 注入计数只数
**已应用**的注入，并对三源交叉核对。

真缺陷（实测，T02-F2-W4/seed1）：seed1/armtlb_injections.log 共两行带
"Site: "，其中
    第 1 行 = `Site: arm_tlb_lookup_tier`  —— F1-F6 的**档位/频率模型诊断**
              （"a tiered run does NOT consume --tlb_max_faults=1 — the tier
               is the frequency model"），启动时写一次，**不是注入**；
    第 2 行 = `Site: arm_tlb_lookup_hit, VA: ..., old_pfn: ..., new_pfn: ...`
              —— 唯一真实注入。
旧 `count_armtlb_injections` 只排除 probe / hit_skipped，于是把 tier 诊断
也算进去 → activated=2（真值 1）；而 T02-F0-W4 无 tier 行 → 计数本就正确=1。
F1-F6 全部受影响，F0 不受影响。

钉死：
  1. tier 诊断行 + 1 条真实 hit → activated=1；
  2. 真实 lookup_hit 缺应用字段（VA/old_pfn/new_pfn）→ 不计入，并计 malformed；
  3. 三源（注入日志 / CHAOS_LSU_TRIGGER.injected / stats.numFaultsInjected）
     可用值必须一致；不一致 → contradiction=True（响亮，不静默选一个）；
  4. 回归：T07 `arm_tlb_lookup`(false_hit) 与 T08 `arm_tlb_walk_issue_drop`
     仍计为注入；`arm_tlb_walk_issue_probe` / `arm_tlb_lookup_hit_skipped`
     仍不计；
  5. `classify_fs_run` 在真实 T02-F2 形状上得 activated=1（F0 形状不变）。

用法：python3 tests/test_lsu_campaign_armtlb_count.py   （退出码 0=全 PASS）
"""
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []

# ---- 逐字取自 runs/lsu/r6_c5_T02-F2-W4/T02-F2-W4/seed1/armtlb_injections.log
TIER_LINE = (
    "Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: bit_flip "
    "(lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT "
    "consume --tlb_max_faults=1 — the tier is the frequency model)")
HIT_LINE = (
    "Tick: 238085259417, Site: arm_tlb_lookup_hit, VA: 0xffffff8001362708, "
    "old_pfn: 0x81362, new_pfn: 0x800400000081362, FaultType: bit_flip, "
    "Mask: 0x800400000000000")
# ---- 逐字取自其他既有 RunID 的注入日志（回归用）
T07_LOOKUP_LINE = (
    "Tick: 237950351460, Site: arm_tlb_lookup, VA: 0xffffff807fbce090, "
    "CAM: miss -> hit, FaultType: false_hit")
T08_PROBE_LINE = (
    "Tick: 237949797348, Site: arm_tlb_walk_issue_probe, walk_id: 1, "
    "VA: 0x40b4c0, FaultType: walk_pairing (walk-issue hook REACHED)")
T08_DROP_LINE = (
    "Tick: 238044463587, Site: arm_tlb_walk_issue_drop, walk_id: 703, "
    "VA: 0xffffffc00801e240, FaultType: walk_pairing (T08-a lost walk/fill)")
HIT_SKIPPED_LINE = (
    "Tick: 237950233578, Site: arm_tlb_lookup_hit_skipped, "
    "FaultType: bit_flip (walk-issue-only model did NOT consume the hit)")

# ---- 逐字取自 runs/lsu/r6_v3_{T05,T06}-F0-W4_s1/*/seed1/armtlb_injections.log
# [R6-V4-STATECOUNT] T05/T06/T07 走 applyEntryFieldFault()：真实注入写的是
# `old_<field>: … new_<field>: …`（valid_clear / perm_subst），**不是** pfn 对。
# 旧 `armtlb_line_applied` 只认 old_pfn/new_pfn，于是把这些真实注入判成
# malformed → log=0 → activated=0，与 trigger/stats 形成假矛盾。
T05_VALID_CLEAR_LINE = (
    "Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8, "
    "old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear")
T06_PERM_SUBST_LINE = (
    "Tick: 237951188955, Site: arm_tlb_lookup_hit, VA: 0xffffffc008a16868, "
    "old_perm_subst: 2, new_perm_subst: 0, FaultType: perm_subst")
# 看起来像状态行但两半都不成立：既无 pfn 对，也无 old_/new_ 配对 → 仍应 malformed。
HIT_NO_EFFECT_LINE = (
    "Tick: 238085259417, Site: arm_tlb_lookup_hit, VA: 0x1234, "
    "FaultType: valid_clear")

TRIGGER_1 = ("CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F2 attempted=110149 "
             "eligible=110149 injected=1 first_eligible_tick=1 "
             "last_eligible_tick=2 (activated=W3-L0-layer)")
STATS_1 = ("board.chaos_armtlb.numFaultsInjected                1"
           "                       # Total TLB-entry faults injected (Count)\n")


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _outdir(log_lines, trigger=TRIGGER_1, stats=STATS_1):
    d = Path(tempfile.mkdtemp(prefix="armtlb-count-"))
    if log_lines is not None:
        (d / "armtlb_injections.log").write_text("\n".join(log_lines) + "\n")
    if stats is not None:
        (d / "stats.txt").write_text(stats)
    return d, (trigger or "")


def main():
    print("[1] tier 诊断行 + 1 条真实 hit → 日志计数 = 1")
    d, trig = _outdir([TIER_LINE, HIT_LINE])
    n = LC.count_armtlb_injections(d / "armtlb_injections.log")
    check("count == 1（tier 行不计）", n == 1, str(n))

    print("[2] 三源一致（log=1 / trigger=1 / stats=1）→ 无 contradiction")
    src = LC.armtlb_count_sources(d, trig)
    check("log == 1", src["log"] == 1, str(src["log"]))
    check("trigger == 1", src["trigger"] == 1, str(src["trigger"]))
    check("stats == 1", src["stats"] == 1, str(src["stats"]))
    check("contradiction is False", src["contradiction"] is False, src["detail"])
    check("attempted == 110149", src["attempted"] == 110149, str(src["attempted"]))
    check("eligible == 110149", src["eligible"] == 110149, str(src["eligible"]))

    print("[3] 真实 lookup_hit 缺应用字段 → 不计入 + malformed=1")
    bad_hit = ("Tick: 238085259417, Site: arm_tlb_lookup_hit, VA: 0x1234, "
               "FaultType: bit_flip, Mask: 0x8")
    d2, _ = _outdir([bad_hit])
    check("count == 0（缺 old_pfn/new_pfn）",
          LC.count_armtlb_injections(d2 / "armtlb_injections.log") == 0)
    s2 = LC.armtlb_count_sources(d2, "")
    check("malformed_hit_lines == 1", s2["malformed_hit_lines"] == 1,
          str(s2["malformed_hit_lines"]))

    print("[4] 三源不一致 → contradiction=True（响亮，不静默选一个）")
    d3, _ = _outdir([TIER_LINE, HIT_LINE], trigger=TRIGGER_1,
                    stats="board.chaos_armtlb.numFaultsInjected 7\n")
    s3 = LC.armtlb_count_sources(d3, TRIGGER_1)
    check("contradiction is True", s3["contradiction"] is True, s3["detail"])
    check("detail 点名三源", all(k in s3["detail"] for k in
                                ("log=", "trigger=", "stats=")), s3["detail"])
    # trigger 与 log 不一致（stats 缺席，只有可用两源）
    d3b, _ = _outdir([TIER_LINE, HIT_LINE],
                     trigger=TRIGGER_1.replace("injected=1", "injected=9"),
                     stats=None)
    s3b = LC.armtlb_count_sources(d3b, TRIGGER_1.replace("injected=1",
                                                         "injected=9"))
    check("两源不一致也响亮", s3b["contradiction"] is True, s3b["detail"])

    print("[5] 回归：其他 ARM TLB 站点的计数语义不变")
    d5, _ = _outdir([T07_LOOKUP_LINE, T08_PROBE_LINE, T08_DROP_LINE,
                     HIT_SKIPPED_LINE], trigger=None, stats=None)
    n5 = LC.count_armtlb_injections(d5 / "armtlb_injections.log")
    check("T07 lookup(false_hit) + T08 walk_issue_drop 计 2"
          "（probe/hit_skipped 不计）", n5 == 2, str(n5))

    print("[6] classify_fs_run：真实 T02-F2 形状 → activated=1（F0 形状不变）")
    d6, trig6 = _outdir(
        [TIER_LINE, HIT_LINE],
        trigger=(TRIGGER_1 + "\n[arm_chaos_fs] KERNEL PANIC under fault "
                            "— exiting (classify: Crash/DUE per fs_mode)\n"))
    v = LC.classify_fs_run(d6, trig6, 0)
    check("activated == 1", v.get("activated") == 1, str(v.get("activated")))
    check("injected == 1", v.get("injected") == 1, str(v.get("injected")))
    check("count_contradiction False",
          v.get("count_contradiction") is False, str(v.get("count_contradiction")))
    d6f, trig6f = _outdir([HIT_LINE], trigger=TRIGGER_1.replace("tier=F2",
                                                                "tier=F0"))
    vf = LC.classify_fs_run(d6f, trig6f, 0)
    check("F0 形状仍 activated == 1", vf.get("activated") == 1,
          str(vf.get("activated")))

    print("[7] [R6-V4-STATECOUNT] T05/T06 状态/属性替换行计为已应用注入")
    d7, trig7 = _outdir([T05_VALID_CLEAR_LINE],
                        trigger=TRIGGER_1.replace("tier=F2", "tier=F0"),
                        stats=STATS_1)
    check("T05 valid_clear 行 applied",
          LC.armtlb_line_applied(T05_VALID_CLEAR_LINE) is True)
    check("T05 count == 1",
          LC.count_armtlb_injections(d7 / "armtlb_injections.log") == 1,
          str(LC.count_armtlb_injections(d7 / "armtlb_injections.log")))
    s7 = LC.armtlb_count_sources(d7, TRIGGER_1.replace("tier=F2", "tier=F0"))
    check("T05 log=1 / trigger=1 / stats=1 → 无 contradiction",
          (s7["log"], s7["trigger"], s7["stats"]) == (1, 1, 1) and
          s7["contradiction"] is False, s7["detail"])
    check("T05 malformed_hit_lines == 0", s7["malformed_hit_lines"] == 0,
          str(s7["malformed_hit_lines"]))

    d7b, _ = _outdir([T06_PERM_SUBST_LINE],
                     trigger=TRIGGER_1.replace("tier=F2", "tier=F0"),
                     stats=STATS_1)
    s7b = LC.armtlb_count_sources(d7b, TRIGGER_1.replace("tier=F2", "tier=F0"))
    check("T06 perm_subst 行 applied",
          LC.armtlb_line_applied(T06_PERM_SUBST_LINE) is True)
    check("T06 三源一致 → 无 contradiction",
          s7b["contradiction"] is False and s7b["log"] == 1, s7b["detail"])

    # 放宽必须精确：既无 pfn 对也无 old_/new_ 配对的 hit 行仍是 malformed。
    check("无效果字段的 hit 行仍 applied=False",
          LC.armtlb_line_applied(HIT_NO_EFFECT_LINE) is False)
    d7c, _ = _outdir([HIT_NO_EFFECT_LINE], trigger=TRIGGER_1, stats=STATS_1)
    s7c = LC.armtlb_count_sources(d7c, TRIGGER_1)
    check("无效果字段的 hit 行 malformed=1 且 log=0",
          s7c["log"] == 0 and s7c["malformed_hit_lines"] == 1, s7c["detail"])
    # 诊断站点即使用 old_/new_ 形状也不得被计入。
    skipped_state = ("Tick: 1, Site: arm_tlb_lookup_hit_skipped, VA: 0x1, "
                     "old_valid_clear: 1, new_valid_clear: 0, "
                     "FaultType: valid_clear")
    check("hit_skipped + 状态字段仍不计",
          LC.armtlb_line_applied(skipped_state) is False)

    print("[8] [R6-V4-STATECOUNT] classify_fs_run：真实 T05 形状 → activated=1")
    v8 = LC.classify_fs_run(d7, TRIGGER_1.replace("tier=F2", "tier=F0"), 0)
    check("T05 形状 activated == 1", v8.get("activated") == 1,
          str(v8.get("activated")))
    check("T05 形状 count_contradiction False",
          v8.get("count_contradiction") is False,
          str(v8.get("count_contradiction")))

    print("[9] [R6-V4-STATECOUNT] T08-b/c/d armed+refill 记一次应用注入")
    # 形状取自 CHAOSArmTLB.cc:414-422（armed，握手）与 :893-902 / :924-932
    # （refill，真正应用）。一次故障写两行，但只应计一次。
    T08B_ARMED = ("Tick: 238044000000, Site: arm_tlb_walk_refill_armed, "
                  "walk_id: 703, VA: 0xffffffc00801e240, "
                  "FaultType: walk_fill_dup")
    T08B_REFILL = ("Tick: 238044463587, Site: arm_tlb_walk_refill, "
                   "walk_id: 703, VA: 0xffffffc00801e240, "
                   "FaultType: walk_fill_dup")
    T08D_STALE = ("Tick: 238044463587, Site: arm_tlb_walk_refill_stale, "
                  "walk_id: 703, VA: 0xffffffc00801e240, "
                  "old_pfn: 0x81d75, stale_pfn: 0x80a16, "
                  "FaultType: walk_stale_result")
    d9, t9 = _outdir([T08B_ARMED, T08B_REFILL],
                     trigger=TRIGGER_1.replace("tier=F2", "tier=F0"),
                     stats=STATS_1)
    s9 = LC.armtlb_count_sources(d9, TRIGGER_1.replace("tier=F2", "tier=F0"))
    check("armed+refill → log=1", s9["log"] == 1, str(s9["log"]))
    check("armed+refill 三源一致 → 无 contradiction",
          s9["contradiction"] is False, s9["detail"])
    check("armed 行本身 applied=False",
          LC.armtlb_line_applied(T08B_ARMED) is False)
    check("refill 行 applied=True",
          LC.armtlb_line_applied(T08B_REFILL) is True)
    check("stale refill 行 applied=True",
          LC.armtlb_line_applied(T08D_STALE) is True)
    d9b, _ = _outdir([T08B_ARMED], trigger=TRIGGER_1.replace("tier=F2",
                                                             "tier=F0"),
                     stats=STATS_1)
    s9b = LC.armtlb_count_sources(d9b, TRIGGER_1.replace("tier=F2", "tier=F0"))
    check("只有 armed（walk 未到 refill）→ log=0 且如实报矛盾",
          s9b["log"] == 0 and s9b["contradiction"] is True, s9b["detail"])

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
