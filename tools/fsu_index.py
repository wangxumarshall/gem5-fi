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

import fsu_scope as S

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNIDS = ROOT / "docs/gem5-fi/fsu/runids.json"
DEFAULT_OUT = ROOT / "runs/fsu"
DEFAULT_MATRIX = ROOT / "docs/gem5-fi/fsu/IMPLEMENTATION_MATRIX.json"


def _load_runids(path: Path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data.get("runids", data if isinstance(data, list) else [])
    return [x["RunID"] for x in items]


def _suite_seed_state(seed_dir: Path):
    """A W5 suite seed counts as exactly ONE seed, never as 5 components."""
    import fsu_suite as S
    try:
        st = S.suite_seed_state(seed_dir)
    except Exception as e:  # malformed suite evidence must not inflate counts
        return {"state": "invalid", "suite": True,
                "reason": f"suite state error: {e}"}
    state = st.get("state", "invalid")
    return {
        "state": state,
        "suite": True,
        "suite_id": st.get("suite_id"),
        "suite_hash": st.get("suite_hash"),
        "suite_seed": st.get("suite_seed"),
        "component_runs": st.get("component_runs", 0),
        "component_certified": st.get("component_certified", 0),
        "audit_ok": st.get("suite_audit_ok", False),
        "components": st.get("components", []),
        "reason": st.get("reason"),
    }


def _w6_suite_seed_state(seed_dir: Path):
    """A W6 (SVD/FFT/sparse) suite seed counts as exactly ONE seed."""
    try:
        sm = json.loads((seed_dir / "suite_manifest.json").read_text(
            encoding="utf-8"))
        rep = json.loads((seed_dir / "suite_report.json").read_text(
            encoding="utf-8"))
        audit = json.loads((seed_dir / "audit.json").read_text(
            encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"state": "invalid", "suite": True,
                "reason": f"W6 suite state error: {e}"}
    comps = sm.get("components") or []
    ok = (audit.get("ok") is True
          and rep.get("suite_admitted") is True
          and int(rep.get("component_run_count", 0)) == 3
          and len(comps) == 3
          and all(c.get("ok") is True for c in comps)
          and (seed_dir / "AUTHORITATIVE").exists())
    return {
        "state": "admitted" if ok else "invalid",
        "suite": True,
        "suite_id": sm.get("suite_id"),
        "suite_hash": sm.get("suite_hash"),
        "suite_seed": sm.get("suite_seed"),
        "component_runs": len(comps),
        "component_certified": sum(1 for c in comps
                                   if c.get("component_certified") is True),
        "audit_ok": audit.get("ok") is True,
        "components": comps,
        "reason": None if ok else "W6 suite audit/report/authoritative "
                                  "not all admitted",
    }


def _v2_suite_state(seed_dir: Path, sm: dict):
    """Unified suite audit v2 (if present) is the counting gate."""
    try:
        v2 = json.loads((seed_dir / "audit_v2.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"state": "invalid", "suite": True,
                "reason": f"audit_v2 unreadable: {e}"}
    ok = (v2.get("schema_version", "").startswith("fsu-suite-audit/")
          and v2.get("suite_certified") is True
          and int(v2.get("formal_seed_contribution", 0)) == 1
          and (seed_dir / "AUTHORITATIVE").exists())
    return {
        "state": "admitted" if ok else "invalid",
        "suite": True,
        "suite_id": v2.get("suite_id") or sm.get("suite_id"),
        "suite_hash": v2.get("suite_hash") or sm.get("suite_hash"),
        "suite_seed": v2.get("suite_seed", sm.get("suite_seed")),
        "component_runs": int(v2.get("component_count", 0)),
        "component_certified": int(v2.get("component_count", 0)) if ok else 0,
        "audit_ok": v2.get("suite_certified") is True,
        "components": v2.get("components", []),
        "reason": None if ok else "unified suite audit not certified",
        "audit_v2": True,
    }


def _seed_state(seed_dir: Path):
    # Presence of suite_manifest.json makes this a formal suite seed:
    # its component runs must never enter admitted_seeds_total as N seeds.
    if (seed_dir / "suite_manifest.json").exists():
        try:
            sm = json.loads((seed_dir / "suite_manifest.json").read_text(
                encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            sm = {}
        if (seed_dir / "audit_v2.json").exists():
            return _v2_suite_state(seed_dir, sm)
        if str(sm.get("suite_id", "")).startswith("w6-"):
            return _w6_suite_seed_state(seed_dir)
        return _suite_seed_state(seed_dir)
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


def scan(runids, out_root: Path, matrix_path=None, scope=None):
    complete_root = Path(out_root) / "COMPLETE_PROPAGATION_PATHS"
    cov = _coverage_map(matrix_path)
    scope = scope or S.load_scope()
    rows = []
    for rid in runids:
        base = Path(out_root) / rid
        seeds = {s: _seed_state(base / f"seed{s}") for s in (1, 2, 3)}
        n = sum(1 for s in seeds.values() if s["state"] == "admitted")
        c = cov.get(rid, {"coverage_status": "UNKNOWN",
                          "coverage_reason": "implementation matrix not found"})
        freq = S.frequency_from_runid(rid)
        scope_status = S.scope_status(freq, n, scope)
        scope_class = ("ACTIVE_SCOPE" if S.is_active_freq(freq, scope)
                       else scope_status)
        states = {s["state"] for s in seeds.values()}
        if n == 3:
            completion_state = "COMPLETE"
        elif n > 0:
            completion_state = "PARTIAL"
        elif "failed" in states:
            completion_state = "FAILED"
        elif "invalid" in states:
            completion_state = "INVALID_EVIDENCE"
        elif "incomplete" in states:
            completion_state = "INCOMPLETE"
        else:
            completion_state = "NOT_RUN"
        rows.append({"runid": rid, "frequency": freq,
                     "scope_class": scope_class,
                     "scope_status": scope_status,
                     "completion_state": completion_state,
                     "seeds": seeds, "admitted_seeds": n,
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
        "suite_seed_dirs": sum(
            1 for r in rows for s in r["seeds"].values() if s.get("suite")),
        "suite_seed_admitted": sum(
            1 for r in rows for s in r["seeds"].values()
            if s.get("suite") and s.get("state") == "admitted"),
        "component_runs_in_admitted_suites": sum(
            int(s.get("component_runs", 0)) for r in rows
            for s in r["seeds"].values()
            if s.get("suite") and s.get("state") == "admitted"),
        "component_faults_note": (
            "component runs/faults are reported separately and never added "
            "to admitted_seeds_total"),
        "target_seeds": len(runids) * 3,
        "seed_completion_counts": {},
        "coverage_status_counts": {},
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "complete_root": str(complete_root),
    }
    from collections import Counter
    summary["seed_completion_counts"] = dict(Counter(r["seed_completion"] for r in rows))
    summary["coverage_status_counts"] = dict(Counter(r["coverage_status"] for r in rows))
    active_rows = [r for r in rows if S.is_active_freq(r["frequency"], scope)]
    scope_summary = {
        "policy_version": scope["policy_version"],
        "decision_date": scope["decision_date"],
        "active_frequencies": scope["active_frequencies"],
        "deferred_frequencies": scope["deferred_frequencies"],
        "active_runids": len(active_rows),
        "active_seed_target": len(active_rows) * 3,
        "active_admitted_seeds": sum(r["admitted_seeds"] for r in active_rows),
        "active_complete_runids": sum(1 for r in active_rows
                                      if r["admitted_seeds"] == 3),
        "deferred_by_user_runids": sum(
            1 for r in rows if r["scope_status"] == "DEFERRED_BY_USER"),
        "historical_complete_out_of_scope_runids": sum(
            1 for r in rows
            if r["scope_status"] == "HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE"),
        "historical_complete_out_of_scope_seeds": sum(
            r["admitted_seeds"] for r in rows
            if r["scope_status"].startswith("HISTORICAL_COMPLETE")),
        "scope_status_counts": dict(Counter(r["scope_status"] for r in rows)),
        "note": "F1-F4 are DEFERRED_BY_USER; historical completed seeds are "
                "HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE, never failures.",
    }
    return rows, summary, scope_summary


def write_index(runids, out_root: Path, runids_path: Path, matrix_path=None):
    rows, summary, scope_summary = scan(runids, out_root, matrix_path)
    summary["active_scope"] = scope_summary
    cr = Path(out_root) / "COMPLETE_PROPAGATION_PATHS"
    cr.mkdir(parents=True, exist_ok=True)
    (cr / "INDEX.json").write_text(
        json.dumps({"summary": summary, "runids": rows},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# FSU 三 seed 完成度索引", "",
             f"> 生成时间：{summary['generated_at']}；RunID 清单：`{runids_path}`。",
             "",
             "## 历史全量视图（source registry）", "",
             f"- 总 RunID：**{summary['total_runids']}**",
             f"- 目标 seed：**{summary['target_seeds']}**",
             f"- 已完成合格 seed：**{summary['admitted_seeds_total']}**",
             f"- suite seed（5 component run 只计 1 seed）："
             f"目录 {summary['suite_seed_dirs']}，admitted "
             f"{summary['suite_seed_admitted']}，"
             f"component run {summary['component_runs_in_admitted_suites']}"
             "（不进入 seed 总数）",
             f"- COMPLETE_3_OF_3：**{summary['complete_3_of_3']}**",
             "- seed_completion："
             + "、".join(f"{k} {v}" for k, v in sorted(summary['seed_completion_counts'].items())),
             "- coverage_status："
             + "、".join(f"{k} {v}" for k, v in sorted(summary['coverage_status_counts'].items())),
             f"- 1/3：{summary['with_1_of_3']}；2/3：{summary['with_2_of_3']}；"
             f"0/3：{summary['with_0_of_3']}", "",
             "## 当前活跃范围视图（F0/F5）", "",
             f"- active_frequencies：{scope_summary['active_frequencies']}",
             f"- 活跃 RunID：**{scope_summary['active_runids']}**；"
             f"目标 seed：**{scope_summary['active_seed_target']}**",
             f"- 活跃范围已完成 seed：**{scope_summary['active_admitted_seeds']}**；"
             f"3/3 RunID：**{scope_summary['active_complete_runids']}**",
             f"- DEFERRED_BY_USER RunID：{scope_summary['deferred_by_user_runids']}",
             f"- HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE RunID："
             f"{scope_summary['historical_complete_out_of_scope_runids']}"
             f"（seed {scope_summary['historical_complete_out_of_scope_seeds']}）",
             "",
             "> F1–F4 是 DEFERRED_BY_USER，不是失败、缺失或删除；"
             "历史完成项不追溯改标。", "",
             "| RunID | seed1 | seed2 | seed3 | seed_completion | coverage_status | 状态 | frequency | scope_class | completion_state |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        cells = []
        for s in (1, 2, 3):
            st = r["seeds"][s]["state"]
            cells.append({"admitted": "✅", "failed": "❌",
                          "incomplete": "…", "pending": "—",
                          "invalid": "!"}.get(st, st))
        lines.append(f"| {r['runid']} | " + " | ".join(cells) +
                     f" | {r['seed_completion']} | {r['coverage_status']} | "
                     f"{r['status']} | {r['frequency']} | "
                     f"{r['scope_class']} | {r['completion_state']} |")
    (cr / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    readme = ["# FSU 完整传播链（COMPLETE_PROPAGATION_PATHS）", "",
              "目录规则：`<RunID>/<RunID>-seed<N>.md`（仅 admitted seed 复制到此）。",
              "",
              f"- 生成时间：{summary['generated_at']}",
              f"- 总 RunID：{summary['total_runids']}；目标 seed：{summary['target_seeds']}",
              f"- 已完成合格 seed：{summary['admitted_seeds_total']}",
              f"- suite seed（component run 不计 seed）：admitted "
              f"{summary['suite_seed_admitted']}，component run "
              f"{summary['component_runs_in_admitted_suites']}",
              f"- COMPLETE_3_OF_3：{summary['complete_3_of_3']}",
              f"- 活跃范围（{'/'.join(scope_summary['active_frequencies'])}）："
              f"{scope_summary['active_admitted_seeds']}/"
              f"{scope_summary['active_seed_target']} seed，"
              f"{scope_summary['active_complete_runids']}/"
              f"{scope_summary['active_runids']} RunID 3/3；"
              f"DEFERRED_BY_USER {scope_summary['deferred_by_user_runids']} RunID",
              "- seed_completion 与 coverage_status 独立：3/3 只表示三个真实 seed，"
              "不代表模型覆盖完整。",
              "- 历史全量视图（173/519）与活跃范围视图（80/240）分别记录；"
              "F1–F4 不是失败。",
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
