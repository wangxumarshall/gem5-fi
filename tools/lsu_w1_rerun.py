#!/usr/bin/env python3
"""[LSU][W1-RERUN] D-2026-10-09-重跑 campaign driver（载体改指 W1，RunID 不变）。

背景（findings F-041/F-052/F-053/F-054）：
  16 个 300/0 BLOCKED 项中 15 项根因 = 短流载体事件供给不足（531-265K events
  << F1/F2/F4 首发下限）；W1 w1_all 载体权威 census 实测 1.39e9/1.38e9/4.98e8
  eligible，count-only 门禁全过；双代表 n=5 全部真实有效注入。
裁决（task_plan D-2026-10-09-重跑）：
  RunID（模型×频率）不变，载体从短流改指 W1；原 300/0 结果归档为 SE 短流环境
  证据（runs/lsu/pilot/ 原样保留），重跑入本新 campaign（runs/lsu/pilot_w1/）。
范围：15 项（ITEM-289 capability-gap 除外；ITEM-285 撤销隔离不在 16 项内）。

用法：
  python3 tools/lsu_w1_rerun.py --items ITEM-005 ITEM-274 [--phase pilot]
  多实例并行 = 每实例占 1 守卫槽（守卫 4 槽位自然限流）；样本级 resume。

停止规则（pilot 口径）：30 activated 或 300 attempted。
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_runner as LR
import lsu_unit_pilot as UP

W1_TEXT = ("MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、"
           "rijndael、sha、bitcount、edge、smooth）")
ITEMS = ["ITEM-003", "ITEM-004", "ITEM-005", "ITEM-009", "ITEM-015", "ITEM-016",
         "ITEM-020", "ITEM-024", "ITEM-025", "ITEM-036", "ITEM-037", "ITEM-274",
         "ITEM-277", "ITEM-281", "ITEM-287"]
ROOT = LR.REPO / "runs/lsu/pilot_w1"


def summarize(runs):
    """复用 unit_pilot.audit（权威聚合口径）：simulator_assert 单列
    post_activation_simulator_failure、五类只收架构结局、守恒校验——
    与旧波次 result.json 完全同构（本驱动初版误将 simulator_assert 计入
    five_class.Crash，2026-10-12 对账时发现并修正）。"""
    return UP.audit(runs)


def run_item(it, phase):
    udir = ROOT / it
    udir.mkdir(parents=True, exist_ok=True)
    runs = []
    s = 0
    while True:                      # 样本级 resume（F-022 同款）
        v = UP._valid_resumed(udir, it, s)
        if v is None:
            break
        runs.append(v)
        s += 1
    if runs:
        print(f"[{it}] resume: {len(runs)} valid samples reused", flush=True)
    status = "IN_PROGRESS"
    try:
        while (UP._activated_count(runs) < UP.SAMPLES_TARGET
               and len(runs) < UP.ATTEMPTED_CAP):
            m = LR.build_manifest(it, phase, s, carrier_text=W1_TEXT)
            od = udir / f"{it}_s{s}"
            od.mkdir(parents=True, exist_ok=True)
            try:
                v, _ = UP.run_one(m, od, None)
            except UP.GuardFailure as gf:
                # F-023 纪律：基础设施失败不记账，中止本项保现场待查
                print(f"[{it}] s{s}: GUARD_FAILURE {gf}"[:300], flush=True)
                status = "GUARD_FAILURE"
                break
            runs.append(v)
            print(f"[{it}] s{s}: {v.get('outcome')}/{v.get('crash_kind', '-')} "
                  f"inj={v.get('injected')} act={UP._activated_count(runs)}"
                  f"/{UP.SAMPLES_TARGET}", flush=True)
            s += 1
        else:
            status = ("COMPLETE" if UP._activated_count(runs) >= UP.SAMPLES_TARGET
                      else "BLOCKED_ATTEMPT_CAP")
    finally:
        rj = udir / f"{it}_result.json"
        rj.write_text(json.dumps(
            {"item": it, "campaign": "w1_rerun_20261011", "status": status,
             "carrier_override": "MiBench-TC23 -> mibench/bin/w1_all",
             "runid_unchanged": True, "decision": "D-2026-10-09-重跑",
             **summarize(runs), "runs": runs},
            ensure_ascii=False, indent=1))
        print(f"[{it}] => {status} {summarize(runs)}", flush=True)
    return status


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--items", nargs="+", default=ITEMS)
    ap.add_argument("--phase", default="pilot")
    args = ap.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    print(f"W1-RERUN campaign start {time.strftime('%F %T')} items={args.items}",
          flush=True)
    for it in args.items:
        run_item(it, args.phase)
    print(f"W1-RERUN campaign end {time.strftime('%F %T')}", flush=True)


if __name__ == "__main__":
    main()
