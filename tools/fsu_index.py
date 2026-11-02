#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_index.py — FSU 三 seed 完成度索引（README/INDEX.md/INDEX.json）。

只读取 runs/fsu 下的 AUTHORITATIVE 与 chain_report.json；不运行 gem5。
每个 RunID 的 seed1..3 独立统计，3/3 才标 COMPLETE_3_OF_3。
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNIDS = ROOT / "docs/gem5-fi/fsu/runids.json"
DEFAULT_OUT = ROOT / "runs/fsu"
DEFAULT_MATRIX = ROOT / "docs/gem5-fi/fsu/IMPLEMENTATION_MATRIX.json"


def _load_runids(path: Path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data.get("runids", data if isinstance(data, list) else [])
    return [x["RunID"] for x in items]


def _seed_state(seed_dir: Path):
    auth = seed_dir / "AUTHORITATIVE"
    if auth.exists():
        attempt = Path(auth.read_text(encoding="utf-8").strip())
        rep = attempt / "chain_report.json"
        if rep.exists():
            r = json.loads(rep.read_text(encoding="utf-8"))
            chain = r.get("chain", {})
            # A seed is only counted when its independent audit passed; an
            # AUTHORITATIVE pointer alone must not inflate completion.
            audit_path = attempt / "audit.json"
            audit_ok = False
            if audit_path.exists():
                try:
                    audit_ok = json.loads(
                        audit_path.read_text(encoding="utf-8")).get("ok") is True
                except (OSError, json.JSONDecodeError):
                    audit_ok = False
            terminal = None
            for fid, f in sorted(chain.get("faults", {}).items()):
                if f.get("admitted"):
                    terminal = f.get("terminal")
                    break
            return {"state": "admitted" if audit_ok else "invalid",
                    "attempt": str(attempt),
                    "oracle": r.get("oracle", {}).get("category"),
                    "terminal": terminal,
                    "audit_ok": audit_ok,
                    "admitted_faults": chain.get("admitted_faults", [])}
        return {"state": "invalid", "attempt": str(attempt)}
    attempts = sorted(seed_dir.glob("attempt-*")) if seed_dir.exists() else []
    failed = [a for a in attempts if (a / ".failed").exists()]
    if failed:
        return {"state": "failed", "attempts": [str(a) for a in attempts]}
    if attempts:
        return {"state": "incomplete", "attempts": [str(a) for a in attempts]}
    return {"state": "pending"}


def _coverage_map(matrix_path):
    if not matrix_path or not Path(matrix_path).exists():
        return {}
    data = json.loads(Path(matrix_path).read_text(encoding="utf-8"))
    return {r["runid"]: {"coverage_status": r.get("coverage_status", "UNKNOWN"),
                         "coverage_reason": r.get("coverage_reason", "")}
            for r in data.get("runids", data.get("runids", []))}


def scan(runids, out_root: Path, matrix_path=None):
    complete_root = Path(out_root) / "COMPLETE_PROPAGATION_PATHS"
    cov = _coverage_map(matrix_path)
    rows = []
    for rid in runids:
        base = Path(out_root) / rid
        seeds = {s: _seed_state(base / f"seed{s}") for s in (1, 2, 3)}
        n = sum(1 for s in seeds.values() if s["state"] == "admitted")
        c = cov.get(rid, {"coverage_status": "UNKNOWN",
                          "coverage_reason": "implementation matrix not found"})
        rows.append({"runid": rid, "seeds": seeds, "admitted_seeds": n,
                     "seed_completion": f"{n}/3",
                     "coverage_status": c["coverage_status"],
                     "coverage_reason": c["coverage_reason"],
                     "status": ("COMPLETE_3_OF_3" if n == 3 else
                                f"PARTIAL_{n}_OF_3" if n else
                                ("FAILED" if any(s["state"] == "failed"
                                                 for s in seeds.values())
                                 else "PENDING"))})
    summary = {
        "total_runids": len(runids),
        "complete_3_of_3": sum(1 for r in rows if r["admitted_seeds"] == 3),
        "with_1_of_3": sum(1 for r in rows if r["admitted_seeds"] == 1),
        "with_2_of_3": sum(1 for r in rows if r["admitted_seeds"] == 2),
        "with_0_of_3": sum(1 for r in rows if r["admitted_seeds"] == 0),
        "admitted_seeds_total": sum(r["admitted_seeds"] for r in rows),
        "target_seeds": len(runids) * 3,
        "seed_completion_counts": {},
        "coverage_status_counts": {},
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "complete_root": str(complete_root),
    }
    from collections import Counter
    summary["seed_completion_counts"] = dict(Counter(r["seed_completion"] for r in rows))
    summary["coverage_status_counts"] = dict(Counter(r["coverage_status"] for r in rows))
    return rows, summary


def write_index(runids, out_root: Path, runids_path: Path, matrix_path=None):
    rows, summary = scan(runids, out_root, matrix_path)
    cr = Path(out_root) / "COMPLETE_PROPAGATION_PATHS"
    cr.mkdir(parents=True, exist_ok=True)
    (cr / "INDEX.json").write_text(
        json.dumps({"summary": summary, "runids": rows},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# FSU 三 seed 完成度索引", "",
             f"> 生成时间：{summary['generated_at']}；RunID 清单：`{runids_path}`。",
             "",
             f"- 总 RunID：**{summary['total_runids']}**",
             f"- 目标 seed：**{summary['target_seeds']}**",
             f"- 已完成合格 seed：**{summary['admitted_seeds_total']}**",
             f"- COMPLETE_3_OF_3：**{summary['complete_3_of_3']}**",
             "- seed_completion："
             + "、".join(f"{k} {v}" for k, v in sorted(summary['seed_completion_counts'].items())),
             "- coverage_status："
             + "、".join(f"{k} {v}" for k, v in sorted(summary['coverage_status_counts'].items())),
             f"- 1/3：{summary['with_1_of_3']}；2/3：{summary['with_2_of_3']}；"
             f"0/3：{summary['with_0_of_3']}", "",
             "| RunID | seed1 | seed2 | seed3 | seed_completion | coverage_status | 状态 |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        cells = []
        for s in (1, 2, 3):
            st = r["seeds"][s]["state"]
            cells.append({"admitted": "✅", "failed": "❌",
                          "incomplete": "…", "pending": "—",
                          "invalid": "!"}.get(st, st))
        lines.append(f"| {r['runid']} | " + " | ".join(cells) +
                     f" | {r['seed_completion']} | {r['coverage_status']} | {r['status']} |")
    (cr / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    readme = ["# FSU 完整传播链（COMPLETE_PROPAGATION_PATHS）", "",
              "目录规则：`<RunID>/<RunID>-seed<N>.md`（仅 admitted seed 复制到此）。",
              "",
              f"- 生成时间：{summary['generated_at']}",
              f"- 总 RunID：{summary['total_runids']}；目标 seed：{summary['target_seeds']}",
              f"- 已完成合格 seed：{summary['admitted_seeds_total']}",
              f"- COMPLETE_3_OF_3：{summary['complete_3_of_3']}",
              "- seed_completion 与 coverage_status 独立：3/3 只表示三个真实 seed，"
              "不代表模型覆盖完整。",
              "", "详细状态见 `INDEX.md` / `INDEX.json`。", ""]
    (cr / "README.md").write_text("\n".join(readme), encoding="utf-8")
    return summary, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="FSU 三 seed 完成度索引")
    ap.add_argument("--runids-json", default=str(DEFAULT_RUNIDS))
    ap.add_argument("--out-root", default=str(DEFAULT_OUT))
    ap.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    a = ap.parse_args(argv)
    runids = _load_runids(Path(a.runids_json))
    summary, _ = write_index(runids, Path(a.out_root),
                             Path(a.runids_json), Path(a.matrix))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
