#!/usr/bin/env python3
"""lsu_next_batch.py — 下一批 RunID 提案生成器（OBS T7，report-only）。

用户指令 2026-10-12（阶段二前置）：从 Excel/清单 + manifest 能力检查产出
"明确、唯一、未完成"的 RunID 清单；存在 injector gap 或能力阻塞的项
**跳过并记录原因**，绝不伪造。本工具不启动任何实验。

准入链（与 lsu_unit_pilot.eligible 同口径，no drift）：
  1. 模型映射：MODEL_BLOCKED（缺口）/ APPROX_MODELS（DR-002 近似）→ 跳过
  2. 家族：armtlb FS-only → 跳过；载体缺失（MiBench/SPEC/PARSEC/SQLite）→ 跳过
  3. 完成度：AGU 31 冻结 RunID（formal 在跑/未完）→ 跳过（不重复认领）
  4. 能力标注：W1 载体 → needs_phaseB_window（Phase A 只能 l0l5，不入
     初始 6 槽分配）；短流 checklist 载体 → full 链可用

输出：runs/lsu/obs/next_batch_proposal_<date>.json + .md（交中央）。
"""
import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_runner as LR
import lsu_campaign as LC
import lsu_unit_pilot as UP

MT = Path("/home/sdc/gem5-fi-ding")
OBS_ROOT = MT / "runs/lsu/obs"
FREEZE = MT / "docs/gem5-fi/lsu/evidence/P4/p4_freeze_agu_formal_20261012.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit-prefix", default=None,
                    help="限制单元前缀（A=AGU/T=L1d-TLB/L=Load Queue；缺省全量）")
    ap.add_argument("--max-candidates", type=int, default=12)
    args = ap.parse_args()

    frozen = set()
    if FREEZE.exists():
        d = json.loads(FREEZE.read_text(encoding="utf-8"))
        for carrier, rlist in d.get("runids", {}).items():
            if isinstance(rlist, list):
                frozen.update(r[:-3] if r.endswith("(K)") else r
                              for r in rlist)

    candidates, skipped = [], []
    for item_id, run_id, fields in LR.parse_items():
        model, freq, wtag = (run_id.split("-") + ["?", "?"])[:3]
        if args.unit_prefix and not model.startswith(args.unit_prefix):
            continue
        if run_id in frozen:
            skipped.append({"runid": run_id, "item": item_id,
                            "reason": "P4 冻结 31 RunID 之一（formal 在跑，不重复认领）"})
            continue
        ok, reason = UP.eligible(item_id, run_id, fields)
        if not ok:
            skipped.append({"runid": run_id, "item": item_id,
                            "reason": f"准入 BLOCKED: {reason}"})
            continue
        # 载体与能力标注（eligible 通过 → 有 SE golden 二进制）
        wl_text = fields.get("负载", "") + " " + fields.get("负载/oracle", "")
        wl_binary = next((b for k, b in LC.WL_BINARY.items() if k in wl_text),
                         None)
        is_w1 = bool(wl_binary and str(wl_binary).endswith("w1_all"))
        candidates.append({
            "runid": run_id, "item": item_id,
            "model": model, "freq": freq, "workload_tag": f"W{wtag}",
            "unit": fields.get("单元", "n/a"),
            "carrier": f"se:{wl_binary}",
            "obs_capability": ("needs_phaseB_window(l0l5_only)"
                               if is_w1 else "full_chain_ready"),
            "golden": LC.GOLDENS.get(wl_binary),
            "est_duration_class": "long(7.4h golden)" if is_w1 else "short(≤61s golden)",
            "initial_assignment_eligible": not is_w1,
        })
    candidates.sort(key=lambda c: (c["unit"], c["runid"]))

    out = {
        "generated": time.strftime("%F %T"),
        "report_only": True,
        "note": ("阶段二前置提案：未获中央 PASS 不启动；W1 载体 RunID 因 "
                 "Phase A 无激活窗口不入初始分配（记录原因跳过，不伪造）"),
        "frozen_31_excluded": len(frozen),
        "candidates": candidates[:args.max_candidates],
        "candidates_total": len(candidates),
        "candidates_short_carrier": sum(1 for c in candidates
                                        if c["initial_assignment_eligible"]),
        "skipped": skipped,
    }
    OBS_ROOT.mkdir(parents=True, exist_ok=True)
    outj = OBS_ROOT / f"next_batch_proposal_{time.strftime('%Y%m%d')}.json"
    outj.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    md = [f"# 下一批 RunID 提案（report-only）— {out['generated']}", "",
          f"- 冻结排除（P4 在跑）：{len(frozen)} 个 RunID",
          f"- 候选总数：{len(candidates)}（短流全链可用 "
          f"{out['candidates_short_carrier']}）",
          f"- 跳过（含原因）：{len(skipped)} 项", "", "## 候选（前 "
          f"{min(args.max_candidates, len(candidates))}）", ""]
    for c in out["candidates"]:
        md.append(f"- **{c['runid']}** ({c['item']}, {c['unit']}, {c['carrier']},"
                  f" {c['freq']}) — {c['obs_capability']}, {c['est_duration_class']}")
    md += ["", "## 跳过清单（原因记录，不伪造执行）", ""]
    for s in skipped:
        md.append(f"- {s['runid']} ({s['item']}): {s['reason'][:90]}")
    (OBS_ROOT / f"next_batch_proposal_{time.strftime('%Y%m%d')}.md").write_text(
        "\n".join(md) + "\n")
    print(f"proposal → {outj}")
    print(f"candidates={len(candidates)} short_chain_ready="
          f"{out['candidates_short_carrier']} skipped={len(skipped)}")
    for c in out["candidates"][:6]:
        print(f"  {c['runid']} {c['item']} {c['carrier']} {c['obs_capability']}")
    return 0


if __name__ == "__main__":
    main()
