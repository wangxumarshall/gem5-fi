#!/usr/bin/env python3
"""test_lsu_campaign_fs_trigger.py — [R6-FIXTRIGGER] FS 分类路径接入权威漏斗
摘要（CHAOS_LSU_TRIGGER），且**缺失时绝不默认 0**。

缺陷（实测，T02-F2-W4/seed1）：`classify_fs_run` **从不解析** stdout 的
    CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F2 attempted=110149
                       eligible=110149 injected=1 ...
（同仓库 `tools/lsu_l5_classify.py:60`、`tools/lsu_obs_core.py:177` 都有该
正则，唯独 FS 路径没有），于是 `attempted/eligible` 恒为 None；单格汇总
`attempted += int(r.get("attempted", 0) or 0)` 把 None **静默转成 0** →
`attempted=0` 而 `activated>0` → `count_contradiction=true` +
`conservation=VIOLATION`。而在同一份证据里 stdout 明明白白写着 attempted=
110149 —— 真实数据流断裂，不是数据缺失。

钉死：
  1. 本格（T02-F2 形状）解析出 attempted=110149 / eligible=110149 / injected=1；
  2. 缺失权威摘要（无 TRIGGER 且注入日志无 FUNNEL）→ attempted 记 None 且
     funnel_missing=True，**绝不默认 0**；
  3. abort 样本回退：注入日志 FUNNEL 行（取最后一行=终态）；
  4. 整格集成（三缺陷叠加的真实形状）→
     attempted=110149 / activated=1 / Crash=1 / conservation=OK /
     count_contradiction=False。

用法：python3 tests/test_lsu_campaign_fs_trigger.py   （退出码 0=全 PASS）
"""
import json
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []

# 逐字取自 runs/lsu/r6_c5_T02-F2-W4/T02-F2-W4/seed1/
TRIGGER_LINE = (
    "CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F2 attempted=110149 "
    "eligible=110149 injected=1 first_eligible_tick=237950233578 "
    "last_eligible_tick=238090618719 (activated=W3-L0-layer)")
PANIC_LINE = ("[arm_chaos_fs] KERNEL PANIC under fault — exiting "
              "(classify: Crash/DUE per fs_mode)")
TIER_LINE = (
    "Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: bit_flip "
    "(lookup tier; the tier is the frequency model)")
HIT_LINE = (
    "Tick: 238085259417, Site: arm_tlb_lookup_hit, VA: 0xffffff8001362708, "
    "old_pfn: 0x81362, new_pfn: 0x800400000081362, FaultType: bit_flip, "
    "Mask: 0x800400000000000")
STATS_1 = ("board.chaos_armtlb.numFaultsInjected                1"
           "                       # Total TLB-entry faults injected (Count)\n")
FUNNEL_LINE = "FUNNEL: attempted=110149 eligible=110149 injected=1"


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _mk(log_lines, stats=STATS_1):
    d = Path(tempfile.mkdtemp(prefix="fs-trigger-"))
    if log_lines is not None:
        (d / "armtlb_injections.log").write_text("\n".join(log_lines) + "\n")
    if stats is not None:
        (d / "stats.txt").write_text(stats)
    return d


def _cell(runid="T02-F2-W4"):
    cell = [""] * 12
    cell[LC.COL_RUNID] = runid
    cell[LC.COL_MODEL] = "T02"
    cell[LC.COL_UNIT] = "L1d-TLB"
    cell[LC.COL_FREQ] = "F2"
    return cell


def _args(**kw):
    base = dict(phase="trial", trial_target=1, screening_target=1,
                main_target=1, max_seeds_per_cell=1, wilson_stop_hw=0.02,
                timeout=300, fs_timeout=5400)
    base.update(kw)
    return types.SimpleNamespace(**base)


def main():
    print("[1] 本格：TRIGGER 摘要进结果（attempted=110149 / eligible=110149）")
    d = _mk([TIER_LINE, HIT_LINE])
    v = LC.classify_fs_run(d, TRIGGER_LINE + "\n" + PANIC_LINE + "\n", 0)
    check("attempted == 110149", v.get("attempted") == 110149,
          str(v.get("attempted")))
    check("eligible == 110149", v.get("eligible") == 110149,
          str(v.get("eligible")))
    check("injected == 1", v.get("injected") == 1, str(v.get("injected")))
    check("funnel_missing is False", v.get("funnel_missing") is False,
          str(v.get("funnel_missing")))
    check("funnel_source 记为 stdout",
          v.get("funnel_source") == "stdout:CHAOS_LSU_TRIGGER",
          str(v.get("funnel_source")))

    print("[2] 缺失权威摘要（无 TRIGGER、无 FUNNEL）→ None + funnel_missing，非 0")
    d2 = _mk([HIT_LINE])
    v2 = LC.classify_fs_run(d2, PANIC_LINE + "\n", 0)
    check("attempted is None（绝不默认 0）", v2.get("attempted") is None,
          repr(v2.get("attempted")))
    check("funnel_missing is True", v2.get("funnel_missing") is True,
          str(v2.get("funnel_missing")))

    print("[3] abort 样本回退：注入日志 FUNNEL 行（取最后一行=终态）")
    d3 = _mk([FUNNEL_LINE.replace("injected=1", "injected=0"),
              HIT_LINE.split("\n")[0], FUNNEL_LINE])
    v3 = LC.classify_fs_run(d3, PANIC_LINE + "\n", 0)
    check("attempted == 110149（来自 FUNNEL）", v3.get("attempted") == 110149,
          str(v3.get("attempted")))
    check("funnel_source 记为 injections.log",
          str(v3.get("funnel_source", "")).startswith("injections.log:FUNNEL"),
          str(v3.get("funnel_source")))

    print("[4] 整格集成（三缺陷叠加的真实形状）→ 单格结论逐项达标")
    d4 = _mk([TIER_LINE, HIT_LINE])
    verdict = LC.classify_fs_run(d4, TRIGGER_LINE + "\n" + PANIC_LINE + "\n", 0)
    args = _args()

    def _fake_run_single_cell(c, a, s, o):
        r = dict(verdict)
        r["timeout_seconds"] = a.fs_timeout
        r["chain_report"] = None
        return r

    orig = LC.run_single_cell
    LC.run_single_cell = _fake_run_single_cell
    try:
        with tempfile.TemporaryDirectory() as td:
            runid, line = LC.run_cell_adaptive(_cell(), args, Path(td))
            res = json.loads((Path(td) / runid / "cell_results.json")
                             .read_text())
    finally:
        LC.run_single_cell = orig
    check("cell attempted == 110149", res.get("attempted") == 110149,
          str(res.get("attempted")))
    check("cell activated == 1", res.get("activated") == 1,
          str(res.get("activated")))
    check("cell classes.Crash == 1", res["classes"]["Crash"] == 1,
          str(res["classes"]))
    check("cell conservation == OK", res.get("conservation") == "OK",
          str(res.get("conservation")))
    check("cell count_contradiction is False",
          res.get("count_contradiction") is False,
          str(res.get("count_contradiction")))
    check("控制台行报 attempted=110149", "attempted=110149" in line, line)

    print("[5] 整格集成：样本缺漏斗 → cell attempted=None + 响亮矛盾，非 0")
    verdict5 = dict(verdict, attempted=None, eligible=None,
                    funnel_missing=True, funnel_source=None)
    LC.run_single_cell = lambda c, a, s, o: dict(verdict5,
                                                 timeout_seconds=a.fs_timeout,
                                                 chain_report=None)
    try:
        with tempfile.TemporaryDirectory() as td:
            runid5, line5 = LC.run_cell_adaptive(_cell(), _args(), Path(td))
            res5 = json.loads((Path(td) / runid5 / "cell_results.json")
                              .read_text())
    finally:
        LC.run_single_cell = orig
    check("cell attempted is None（非 0）", res5.get("attempted") is None,
          repr(res5.get("attempted")))
    check("cell count_contradiction is True",
          res5.get("count_contradiction") is True,
          str(res5.get("count_contradiction")))
    check("conversion 未把 None 伪装成 0", "attempted=0 " not in line5, line5)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
