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

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
