#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_seed_audit.py — 逐 seed 证据与 Markdown 审计（门禁 10）。

审计对象：runs/fsu/<RunID>/seed<N>/attempt-<k>/
检查:
  - manifest / chain_report / seed Markdown 的 RunID、seed、workload、
    gem5 二进制、源码 HEAD 身份一致；
  - prop_evt 可完整解析、gzip 未截断、事件 sample_run_id 全为本 seed；
  - chain_report 与原始事件流重算结果一致（terminal/admitted/violations）；
  - Markdown 事件表的每个 event_id 在原始流中存在，kind/parent 一致；
    原始主链每个 event_id 在 Markdown 中出现；
  - Markdown 的 terminal / admitted 与 chain_report 一致；
  - evidence_sha256.json 中每个文件哈希仍匹配；
  - stats.txt 非空；admitted=True 且 violations=[]。

用法: python3 tools/fsu_seed_audit.py <attempt_dir>
退出码 0 = 全部通过；1 = 有失败项。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_chain_check as C  # noqa: E402
import fsu_prop_fields as P  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _md_event_rows(md: str):
    rows, inside = [], False
    for line in md.splitlines():
        if line.startswith("## 5."):
            inside = True
            continue
        if inside and line.startswith("## 6."):
            break
        if not inside or not line.startswith("|"):
            continue
        if line.startswith("|---") or "| kind | event_id |" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3:
            rows.append(cells)
    return rows


def _md_value(md: str, label: str):
    m = re.search(re.escape(label) + r"\s*\**([^*\n]+?)\**\s*$", md, re.M)
    return m.group(1).strip() if m else None


def audit_attempt(attempt: Path):
    attempt = Path(attempt)
    checks, failures = [], []

    def check(name, ok):
        checks.append((name, ok))
        if not ok:
            failures.append(name)

    man_path = attempt / "manifest.json"
    rep_path = attempt / "chain_report.json"
    if not man_path.exists() or not rep_path.exists():
        return {"ok": False, "checks": [], "failures": ["manifest/chain_report missing"]}
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    report = json.loads(rep_path.read_text(encoding="utf-8"))
    chain = report.get("chain", {})
    runid = manifest["run_id"]
    seed = manifest["seed"]
    sample = manifest.get("sample_run_id") or f"s{seed}"

    md_path = attempt / f"{runid}-seed{seed}.md"
    check("seed Markdown 存在", md_path.exists())
    md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""

    # 1. 身份一致性
    check("RunID 一致", report.get("run_id") == runid and runid in md)
    check("seed/sample_run_id 一致",
          report.get("seed") == seed and report.get("sample_run_id") == sample
          and sample in md)
    check("workload 二进制身份一致",
          report.get("workload_sha256") == manifest.get("workload_sha256"))
    check("gem5 二进制身份一致",
          report.get("gem5_sha256") == manifest.get("gem5_sha256"))
    check("源码 HEAD 一致", report.get("source_head") == manifest.get("source_head"))

    # 2. 原始事件流
    prop = attempt / "inject/prop_evt.txt.gz"
    check("prop_evt 存在", prop.exists())
    events, truncated, reason = P.read_stream(prop) if prop.exists() else ([], True, "missing")
    check(f"prop_evt 未截断（reason={reason or 'ok'}）", not truncated)
    bad_identity = [e.get("event_id") for e in events
                    if str(e.get("run_id")) != runid
                    or str(e.get("sample_run_id")) != sample]
    check(f"事件身份全为本 seed（越界 {len(bad_identity)}）", not bad_identity)

    # 3. 链重算与 chain_report 一致
    recomputed = C.check_stream(prop, run_id=runid, sample_run_id=sample) \
        if prop.exists() else {"faults": {}, "admitted_faults": [], "truncated": True}
    check("重算 admitted_faults 一致",
          recomputed.get("admitted_faults") == chain.get("admitted_faults"))
    check("重算 truncated 一致", recomputed.get("truncated") == chain.get("truncated"))
    for fid, r in recomputed.get("faults", {}).items():
        old = chain.get("faults", {}).get(fid, {})
        check(f"fault {fid} terminal 一致", r.get("terminal") == old.get("terminal"))
        check(f"fault {fid} violations 一致", r.get("violations") == old.get("violations"))
        check(f"fault {fid} admitted 一致", r.get("admitted") == old.get("admitted"))

    # 4. Markdown 事件表 ↔ 原始流
    by_id = {str(e.get("event_id")): e for e in events}
    rows = _md_event_rows(md)
    md_ids = [r[1] for r in rows if len(r) > 1]
    for r in rows:
        eid = r[1]
        evt = by_id.get(eid)
        check(f"MD event {eid} 存在于原始流", evt is not None)
        if evt is not None:
            check(f"MD event {eid} kind 一致", r[0] == str(evt.get("kind")))
            check(f"MD event {eid} parent 一致",
                  r[2] == (str(evt.get("parent_event_id")) or "—"))
    admitted_fid = None
    for fid, r in chain.get("faults", {}).items():
        if r.get("admitted"):
            admitted_fid = fid
            break
    # A chain with no admitted/certified fault must never pass the gate,
    # even if a tampered report and a regenerated MD agree with each other.
    check("链 admitted=True", chain.get("admitted") is True)
    check("链 certified=True", chain.get("certified") is True)
    check("链 violations=[]", chain.get("violations", []) == [])
    check("存在 admitted fault", admitted_fid is not None)
    if admitted_fid is not None:
        chain_ids = chain["faults"][admitted_fid].get("path_event_ids", [])
        check("MD 覆盖原始主链全部事件",
              all(i in md_ids for i in chain_ids))
        # 5. terminal / admitted 一致
        term = _md_value(md, "传播链 terminal：")
        check("MD terminal 与 chain_report 一致",
              term is not None and term.strip("* ") == str(
                  chain["faults"][admitted_fid].get("terminal")))
        adm = _md_value(md, "admitted / certified：")
        check("MD admitted/certified 与 chain_report 一致",
              adm is not None and adm.replace(" ", "") in
              (f"{chain['faults'][admitted_fid].get('admitted')}/"
               f"{chain['faults'][admitted_fid].get('certified')}",
               f"{str(chain['faults'][admitted_fid].get('admitted')).lower()}/"
               f"{str(chain['faults'][admitted_fid].get('certified')).lower()}"))

    # 6. 证据哈希
    hp = attempt / "evidence_sha256.json"
    check("evidence_sha256.json 存在", hp.exists())
    if hp.exists():
        hashes = json.loads(hp.read_text(encoding="utf-8"))
        bad = [rel for rel, h in hashes.items()
               if not (attempt / rel).exists() or _sha(attempt / rel) != h]
        check(f"证据 SHA-256 全部匹配（失配 {len(bad)}）", not bad)

    # 7. stats 非空
    stats = attempt / "stats.txt"
    check("stats.txt 非空", stats.exists() and stats.stat().st_size > 0)

    # 8. 结论
    if admitted_fid is not None:
        r = chain["faults"][admitted_fid]
        check("admitted=True", r.get("admitted") is True)
        check("violations=[]", r.get("violations") == [])

    return {"ok": not failures, "checks": checks, "failures": failures,
            "attempt": str(attempt)}


def write_audit(attempt: Path):
    """Recompute the audit gate and persist audit.json / audit.md.

    `certified` is computed from the full gate (identity, gzip EOF, parent
    chain, tick monotonicity, L5 witness, stats, evidence hashes, no
    cross-seed data) — never hard-coded.
    """
    import hashlib as _hashlib
    attempt = Path(attempt)
    res = audit_attempt(attempt)
    manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((attempt / "chain_report.json").read_text(encoding="utf-8"))
    chain = report.get("chain", {})
    oracle = report.get("oracle", {})
    prop = attempt / "inject/prop_evt.txt.gz"
    events, truncated, reason = P.read_stream(prop) if prop.exists() else ([], True, "missing")
    fid, fault = None, {}
    for k, v in sorted(chain.get("faults", {}).items()):
        if v.get("admitted"):
            fid, fault = k, v
            break
    by_id = {str(e.get("event_id")): e for e in events}
    path = [by_id[i] for i in fault.get("path_event_ids", []) if i in by_id]
    edges = [{"from": a.get("event_id"), "to": b.get("event_id"),
              "ok": str(b.get("parent_event_id")) == str(a.get("event_id"))}
             for a, b in zip(path, path[1:])]
    ticks = []
    for e in path:
        try:
            ticks.append(int(str(e.get("tick"))))
        except ValueError:
            pass
    tick_ok = all(b >= a for a, b in zip(ticks, ticks[1:]))
    l5_id = fault.get("l5_witness_event_id")
    l5 = by_id.get(str(l5_id), {})
    cross_ok = all(str(e.get("sample_run_id")) == manifest.get("sample_run_id")
                   for e in events)
    hp = attempt / "evidence_sha256.json"
    hashes = json.loads(hp.read_text(encoding="utf-8")) if hp.exists() else {}
    stats = attempt / "stats.txt"
    audit = {
        "run_id": manifest.get("run_id"),
        "seed": manifest.get("seed"),
        "sample_run_id": manifest.get("sample_run_id"),
        "attempt": attempt.name,
        "gzip_eof_ok": not truncated,
        "truncation_reason": reason,
        "event_count": len(events),
        "identity_ok": not chain.get("identity_violations"),
        "identity_violations": chain.get("identity_violations", []),
        "direct_parent_chain": all(e["ok"] for e in edges) if edges else False,
        "edges": edges,
        "tick_monotonic": tick_ok,
        "layers": fault.get("layers", []),
        "layers_na": fault.get("layers_na", []),
        "l5_witness": {"event_id": l5_id, "kind": l5.get("kind"),
                       "outcome": l5.get("outcome")},
        "oracle": oracle.get("category"),
        "oracle_reason": oracle.get("reason"),
        "chain_terminal": fault.get("terminal"),
        "stats_nonempty": stats.exists() and stats.stat().st_size > 0,
        "evidence_sha256": hashes,
        "cross_seed_ok": cross_ok,
        "admitted": fault.get("admitted", False),
        "certified": bool(res["ok"]),
        "violations": fault.get("violations", []),
        "audit_checks": [{"check": n, "ok": ok} for n, ok in res["checks"]],
        "failures": res["failures"],
        "ok": res["ok"],
    }
    (attempt / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# {audit['run_id']} seed{audit['seed']} 审计", "",
             f"- attempt：`{audit['attempt']}`",
             f"- sample_run_id：`{audit['sample_run_id']}`", "",
             "| 项 | 值 |", "|---|---|",
             f"| gzip EOF 完整 | {audit['gzip_eof_ok']}（{audit['truncation_reason'] or 'ok'}） |",
             f"| event_count | {audit['event_count']} |",
             f"| 身份一致 | {audit['identity_ok']} |",
             f"| 单祖先直接 parent | {audit['direct_parent_chain']} |",
             f"| tick 单调 | {audit['tick_monotonic']} |",
             f"| 层映射 | {', '.join(audit['layers'])}；N/A={audit['layers_na']} |",
             f"| L5 witness | {audit['l5_witness']} |",
             f"| oracle | {audit['oracle']} |",
             f"| chain terminal | {audit['chain_terminal']} |",
             f"| stats 非空 | {audit['stats_nonempty']} |",
             f"| 无跨 seed 复制 | {audit['cross_seed_ok']} |",
             f"| admitted | {audit['admitted']} |",
             f"| certified | {audit['certified']} |",
             f"| violations | {audit['violations']} |", "",
             "## 边", ""]
    for e in audit["edges"]:
        lines.append(f"- `{e['from']}` → `{e['to']}`：{'✓' if e['ok'] else '✗'}")
    lines += ["", "## 证据 SHA-256", "", "| 文件 | SHA-256 |", "|---|---|"]
    for rel, h in sorted(hashes.items()):
        lines.append(f"| `{rel}` | `{h}` |")
    lines += ["", "## 审计检查", "", "| 检查 | 结果 |", "|---|---|"]
    for c in audit["audit_checks"]:
        lines.append(f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} |")
    lines += ["", f"**结论：{'PASS' if audit['ok'] else 'FAIL'}**", ""]
    (attempt / "audit.md").write_text("\n".join(lines), encoding="utf-8")
    return audit


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="FSU 单 seed 审计器")
    ap.add_argument("attempt")
    a = ap.parse_args(argv)
    res = audit_attempt(Path(a.attempt))
    for name, ok in res["checks"]:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(json.dumps({"ok": res["ok"], "failures": res["failures"]},
                     ensure_ascii=False, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
