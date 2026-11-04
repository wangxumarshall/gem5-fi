#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_full_audit.py — recompute every authoritative FSU seed with the current
tools and classify the result into four mutually exclusive categories.

For each seed on disk:

* suite seed (``suite_manifest.json`` present): ``fsu_suite_audit.audit_seed``
  recomputes the frozen plan binding, every component chain/audit and the
  element oracle.  Each component is classified independently.
* non-suite seed (``AUTHORITATIVE`` pointer, no suite manifest):
  ``fsu_seed_audit.audit_attempt`` plus a fresh
  ``fsu_chain_check.check_stream`` on the raw PROP-EVT stream.

Categories
----------
``current_verified``
    The current tool recomputed the seed/component from raw evidence and it
    passed.
``legacy_report_only``
    A stored report exists but no current recomputation was possible (for
    example the raw stream is gone).  The stored value is echoed, never
    counted as verified.
``current_verification_failed``
    The current tool recomputed and found a real failure (hash drift, audit
    failure, uncertified chain, ...).
``missing_evidence``
    Required evidence is absent, so the current tool cannot decide.  This is
    never upgraded to a pass.

The report is a derived artifact.  No seed directory is modified.  Provenance
(raw config/manifest SHA-256, tool git SHA, verification time) is recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_chain_check as C  # noqa: E402
import fsu_seed_audit as A  # noqa: E402
import fsu_suite_audit as U  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "fsu-full-audit/v1"
TOOL_VERSION = "fsu_full_audit/v1"
CATEGORIES = (
    "current_verified",
    "legacy_report_only",
    "current_verification_failed",
    "missing_evidence",
)


def _sha(path: Path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except OSError as e:
        return None, f"missing/unreadable: {e}"
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _stored_audit(attempt: Path) -> dict:
    data, err = _load(attempt / "audit.json")
    if err:
        return {"present": False, "ok": None, "certified": None,
                "path": str(attempt / "audit.json"), "error": err}
    return {
        "present": True,
        "ok": data.get("ok"),
        "certified": data.get("certified"),
        "path": str(attempt / "audit.json"),
        "sha256": _sha(attempt / "audit.json"),
    }


def _legacy_or_missing(detail: dict, attempt: Path, reason: str) -> dict:
    """No current recomputation is possible; a stored report is echo-only."""
    stored = _stored_audit(attempt) if attempt.is_dir() else {
        "present": False, "ok": None, "certified": None,
        "path": str(attempt / "audit.json")}
    detail["stored_audit"] = stored
    if stored.get("present") and stored.get("ok") is not None:
        detail["category"] = "legacy_report_only"
        detail["reason"] = ("stored report only (not counted): " + reason)
    else:
        detail["category"] = "missing_evidence"
        detail["reason"] = reason
    return detail


def audit_non_suite_seed(seed_dir: Path, run_id: str) -> dict:
    pointer = seed_dir / "AUTHORITATIVE"
    detail = {
        "kind": "non_suite_seed",
        "seed_dir": str(seed_dir),
        "run_id": run_id,
        "seed": seed_dir.name,
        "category": None,
        "reason": None,
        "attempt": None,
        "recomputed_audit_ok": None,
        "recomputed_chain_certified": None,
        "stored_audit": None,
        "evidence_sha256": {},
    }
    if not pointer.exists():
        detail["category"] = "missing_evidence"
        detail["reason"] = "AUTHORITATIVE pointer missing"
        return detail
    attempt = Path(pointer.read_text(encoding="utf-8").strip())
    if not attempt.is_absolute():
        # Historical pointers use either a repo-root-relative path or a
        # seed-relative path.  Resolve the repo-root form first, and never
        # silently concatenate both.
        root_relative = ROOT / attempt
        attempt = root_relative if root_relative.exists() else seed_dir / attempt
    detail["attempt"] = str(attempt)
    if not attempt.is_dir():
        return _legacy_or_missing(
            detail, attempt, f"attempt directory missing: {attempt}")
    for rel in ("manifest.json", "chain_report.json", "inject/prop_evt.txt.gz"):
        if not (attempt / rel).exists():
            detail["evidence_sha256"][rel] = None
            return _legacy_or_missing(
                detail, attempt, f"required evidence missing: {rel}")
        detail["evidence_sha256"][rel] = _sha(attempt / rel)
    detail["stored_audit"] = _stored_audit(attempt)

    manifest, err = _load(attempt / "manifest.json")
    if err:
        return _legacy_or_missing(detail, attempt, f"manifest.json {err}")
    report, err = _load(attempt / "chain_report.json")
    if err:
        return _legacy_or_missing(
            detail, attempt, f"chain_report.json {err}")

    detail["oracle"] = (report.get("oracle") or {}).get("category")
    detail["oracle_reason"] = (report.get("oracle") or {}).get("reason")
    detail["terminal"] = None
    for _fid, fault in sorted((report.get("chain") or {}).get(
            "faults", {}).items()):
        if fault.get("admitted"):
            detail["terminal"] = fault.get("terminal")
            break

    try:
        audit = A.audit_attempt(attempt)
        detail["recomputed_audit_ok"] = audit.get("ok") is True
        detail["audit_failures"] = list(audit.get("failures", []))[:12]
    except Exception as e:  # noqa: BLE001
        audit = {"ok": False, "failures": [f"{type(e).__name__}: {e}"]}
        detail["recomputed_audit_ok"] = False
        detail["audit_failures"] = audit["failures"]

    try:
        chain = C.check_stream(
            attempt / "inject/prop_evt.txt.gz",
            run_id=manifest.get("run_id"),
            sample_run_id=manifest.get("sample_run_id"))
        detail["recomputed_chain_certified"] = chain.get("certified") is True
        detail["chain_violations"] = list(chain.get("violations", []))[:12]
        detail["chain_faults"] = sorted(chain.get("faults", {}))
    except Exception as e:  # noqa: BLE001
        detail["recomputed_chain_certified"] = False
        detail["chain_violations"] = [f"{type(e).__name__}: {e}"]
        chain = {}

    ok = (detail["recomputed_audit_ok"]
          and detail["recomputed_chain_certified"])
    detail["category"] = "current_verified" if ok else \
        "current_verification_failed"
    if not ok:
        detail["reason"] = "recomputed audit/chain not certified"
    return detail


def audit_suite_seed(seed_dir: Path, run_id: str) -> dict:
    detail = {
        "kind": "suite_seed",
        "seed_dir": str(seed_dir),
        "run_id": run_id,
        "seed": seed_dir.name,
        "category": None,
        "reason": None,
        "components": [],
        "component_categories": {},
        "legacy_audit_v2": None,
    }
    try:
        report = U.audit_seed(seed_dir)
    except Exception as e:  # noqa: BLE001
        # The current tool could not run at all.  If a stored report exists,
        # echo it as legacy-only; never upgrade it to verified.
        stored = ((seed_dir / "audit_v2.json").exists()
                  or (seed_dir / "audit.json").exists())
        detail["category"] = ("legacy_report_only" if stored
                              else "current_verification_failed")
        detail["reason"] = f"current audit raised {type(e).__name__}: {e}"
        return detail
    detail["suite_id"] = report.get("suite_id")
    detail["suite_seed"] = report.get("suite_seed")
    detail["suite_hash"] = report.get("suite_hash")
    detail["suite_hash_declared"] = report.get("suite_hash_declared")
    detail["seed_plan_schema"] = report.get("seed_plan_schema")
    detail["suite_certified"] = report.get("suite_certified")
    detail["violations"] = report.get("violations", [])
    detail["missing_evidence"] = report.get("missing_evidence", [])
    detail["category"] = report.get("recompute_status")
    if detail["category"] not in CATEGORIES:
        detail["category"] = "current_verification_failed"

    v2_path = seed_dir / "audit_v2.json"
    if v2_path.exists():
        v2, err = _load(v2_path)
        detail["legacy_audit_v2"] = {
            "present": True,
            "schema_version": (v2 or {}).get("schema_version"),
            "suite_certified": (v2 or {}).get("suite_certified"),
            "tool_version": (v2 or {}).get("tool_version"),
            "sha256": _sha(v2_path),
            "error": err,
        }

    counts = {c: 0 for c in CATEGORIES}
    for comp in report.get("components", []):
        if comp.get("missing_evidence"):
            cat = "missing_evidence"
        elif comp.get("violations"):
            cat = "current_verification_failed"
        elif (comp.get("execution_complete") and comp.get("evidence_valid")
              and comp.get("audit_ok") and comp.get("certified")
              and comp.get("recomputed_audit_ok")
              and comp.get("recomputed_certified")
              and comp.get("component_status") == "admitted"):
            cat = "current_verified"
        else:
            cat = "current_verification_failed"
        counts[cat] += 1
        detail["components"].append({
            "program_id": comp.get("program_id"),
            "program_index": comp.get("program_index"),
            "category": cat,
            "oracle_category": comp.get("oracle_category"),
            "chain_terminal": comp.get("chain_terminal"),
            "plan_binding_key": comp.get("plan_binding_key"),
            "plan_binding_ok": comp.get("plan_binding_ok"),
            "manifest_sha256": comp.get("manifest_sha256"),
            "evidence_sha256": comp.get("evidence_sha256"),
            "violations": comp.get("violations", []),
            "missing_evidence": comp.get("missing_evidence", []),
        })
    detail["component_categories"] = counts
    return detail


def discover(out_root: Path):
    suite_seeds, non_suite = [], []
    for run_dir in sorted(p for p in out_root.iterdir() if p.is_dir()):
        for seed_dir in sorted(run_dir.glob("seed*")):
            if not seed_dir.is_dir():
                continue
            if (seed_dir / "suite_manifest.json").exists():
                suite_seeds.append((seed_dir, run_dir.name))
            elif (seed_dir / "AUTHORITATIVE").exists():
                non_suite.append((seed_dir, run_dir.name))
    return suite_seeds, non_suite


def summarize(suite_details, non_suite_details) -> dict:
    summary = {
        "suite_seeds": {c: 0 for c in CATEGORIES},
        "components": {c: 0 for c in CATEGORIES},
        "non_suite_seeds": {c: 0 for c in CATEGORIES},
        "authoritative_seeds": {c: 0 for c in CATEGORIES},
    }
    for d in suite_details:
        summary["suite_seeds"][d["category"]] += 1
        for cat, n in d.get("component_categories", {}).items():
            summary["components"][cat] += n
    for d in non_suite_details:
        summary["non_suite_seeds"][d["category"]] += 1
    for key in ("suite_seeds", "non_suite_seeds"):
        for cat in CATEGORIES:
            summary["authoritative_seeds"][cat] += summary[key][cat]
    summary["suite_seeds"]["total"] = len(suite_details)
    summary["non_suite_seeds"]["total"] = len(non_suite_details)
    summary["authoritative_seeds"]["total"] = (
        len(suite_details) + len(non_suite_details))
    summary["components"]["total"] = sum(
        len(d.get("components", [])) for d in suite_details)
    return summary


def build(out_root: Path, only: str = "all") -> dict:
    suite_seeds, non_suite = discover(out_root)
    if only == "non-suite":
        suite_seeds = []
    elif only == "suite":
        non_suite = []
    suite_details = []
    for i, (seed_dir, rid) in enumerate(suite_seeds, 1):
        detail = audit_suite_seed(seed_dir, rid)
        print(f"[full-audit] suite {i}/{len(suite_seeds)} {rid}/"
              f"{seed_dir.name}: {detail['category']}", file=sys.stderr,
              flush=True)
        suite_details.append(detail)
    non_suite_details = []
    for i, (seed_dir, rid) in enumerate(non_suite, 1):
        detail = audit_non_suite_seed(seed_dir, rid)
        print(f"[full-audit] seed {i}/{len(non_suite)} {rid}/"
              f"{seed_dir.name}: {detail['category']}", file=sys.stderr,
              flush=True)
        non_suite_details.append(detail)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "scope": only,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tool_git_sha": _git_sha(),
        "tool_script_sha256": _sha(Path(__file__)),
        "out_root": str(out_root),
        "inputs": {
            "suite_configs": sorted(
                str(p.relative_to(ROOT)) for p in
                (ROOT / "configs/fsu/suites").glob("*.json")),
            "suite_configs_sha256": {
                str(p.relative_to(ROOT)): _sha(p) for p in
                (ROOT / "configs/fsu/suites").glob("*.json")},
        },
        "summary": summarize(suite_details, non_suite_details),
        "suite_seeds": suite_details,
        "non_suite_seeds": non_suite_details,
    }


def _write(report: dict, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)
                      + "\n", encoding="utf-8")


def render_markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# FSU 当前工具全量复审",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- tool_git_sha: `{report['tool_git_sha']}`",
        f"- schema_version: `{report['schema_version']}`",
        "",
        "| 范围 | total | current_verified | legacy_report_only | "
        "current_verification_failed | missing_evidence |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, label in (("suite_seeds", "suite seed"),
                       ("components", "component"),
                       ("non_suite_seeds", "非 suite 权威 seed"),
                       ("authoritative_seeds", "权威 seed 合计")):
        row = s[key]
        lines.append(
            f"| {label} | {row.get('total', 0)} | "
            f"{row['current_verified']} | {row['legacy_report_only']} | "
            f"{row['current_verification_failed']} | "
            f"{row['missing_evidence']} |")
    failures = [d for d in report["suite_seeds"]
                if d["category"] != "current_verified"]
    failures += [d for d in report["non_suite_seeds"]
                 if d["category"] != "current_verified"]
    lines += ["", "## 未通过/缺证据明细", ""]
    if not failures:
        lines.append("无。")
    for d in failures:
        lines.append(f"### {d['run_id']}/{d['seed']} — {d['category']}")
        if d.get("reason"):
            lines.append(f"- reason: {d['reason']}")
        for v in d.get("violations", [])[:10]:
            lines.append(f"- {v}")
        for m in d.get("missing_evidence", [])[:10]:
            lines.append(f"- missing_evidence: {m}")
        for c in d.get("components", []):
            if c["category"] != "current_verified":
                lines.append(f"- component {c['program_id']}: "
                             f"{c['category']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Recompute every authoritative FSU seed with the current "
                    "tools and classify the result.")
    ap.add_argument("--out-root", default=str(ROOT / "runs/fsu"))
    ap.add_argument("--out", default=str(
        ROOT / "docs/gem5-fi/fsu/audit/CURRENT-AUDIT.json"))
    ap.add_argument("--markdown", default=str(
        ROOT / "docs/gem5-fi/fsu/audit/CURRENT-AUDIT.md"))
    ap.add_argument("--only", choices=("all", "suite", "non-suite"),
                    default="all")
    args = ap.parse_args(argv)
    report = build(Path(args.out_root), only=args.only)
    _write(report, Path(args.out))
    Path(args.markdown).parent.mkdir(parents=True, exist_ok=True)
    Path(args.markdown).write_text(render_markdown(report), encoding="utf-8")
    s = report["summary"]
    print(json.dumps({"summary": s, "out": args.out,
                      "markdown": args.markdown}, ensure_ascii=False,
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
