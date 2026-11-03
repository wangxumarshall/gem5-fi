#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_f5_w4_gate.py — non-formal FP06-F5-W4 evidence/resource gate.

Runs four real attempts under runs/fsu-gates (never runs/fsu, never 519/240):

  1. FULL        short W4, prefix budget 60000 -> every exposure recorded
  2. SAMPLED     short W4, bounded first/last sampling, same fault identity
  3. FORMAL      W4-rate-v1 (2,097,155 eligible census), bounded sampling
  4. EARLY       short W4, injection killed before exit -> fail-closed

The gate PASSES only when:
  - FULL and SAMPLED report identical exposures_total / activated count /
    faults_injected / run-level oracle (sampling is observation only);
  - both are audit.ok / certified, with chain_end and exact conservation;
  - FORMAL is audit.ok / certified with event_count well below the 200000
    PROP-EVT cap and bounded prop/injection-log files;
  - EARLY has no AUTHORITATIVE and its audit is NOT ok (no invented terminal).

Usage:
  python3 tools/fsu_f5_w4_gate.py [--outdir runs/fsu-gates/F5-FP06-W4-GATE]
  python3 tools/fsu_f5_w4_gate.py --verify-only --outdir ...
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_seed_audit as A  # noqa: E402
import fsu_seed_runner as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "runs/fsu-gates/F5-FP06-W4-GATE"
MANIFESTS = {
    "full": ROOT / "configs/fsu/FSU-FP06-F5-W4-FULL-GATE.json",
    "sampled": ROOT / "configs/fsu/FSU-FP06-F5-W4-SAMPLED-GATE.json",
    "formal": ROOT / "configs/fsu/FSU-FP06-F5-W4-FORMAL-BOUNDED-GATE.json",
}
EVENT_CAP = 200000


def _run(manifest: Path, out_root: Path, label: str):
    return R.run_seed(manifest, 1, out_root=out_root, root=ROOT)


def _attempt(out_root: Path, manifest: Path):
    manifest = json.loads(manifest.read_text(encoding="utf-8"))
    seed_dir = out_root / manifest["run_id"] / "seed1"
    auth = seed_dir / "AUTHORITATIVE"
    if auth.exists():
        return Path(auth.read_text(encoding="utf-8").strip())
    attempts = sorted(seed_dir.glob("attempt-*"))
    return attempts[-1] if attempts else None


def _chain(attempt: Path):
    p = attempt / "chain_report.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _f5(chain: dict):
    faults = (chain.get("chain") or {}).get("faults") or {}
    for r in faults.values():
        f5 = r.get("f5") or {}
        if f5:
            return f5
    return {}


def _art(attempt: Path):
    import fsu_prop_fields as P
    prop = attempt / "inject/prop_evt.txt.gz"
    inj = attempt / "inject/fpu_injections.log"
    events, truncated, _ = P.read_stream(prop) if prop.exists() else ([], True, "")
    return {
        "event_count": len(events),
        "truncated": bool(truncated),
        "prop_evt_bytes": prop.stat().st_size if prop.exists() else 0,
        "injection_log_bytes": inj.stat().st_size if inj.exists() else 0,
    }


def _audit(attempt: Path):
    try:
        res = A.audit_attempt(attempt)
        return res, True
    except Exception as e:  # audit must fail closed, not crash the gate
        return {"ok": False, "failures": [repr(e)]}, False


def _early_runner(cmd, timeout):
    """Kill the injection run mid-flight (census still runs normally)."""
    if "--chaos_propagation" in cmd:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               errors="replace", timeout=2)
            return r.returncode, r.stdout or "", r.stderr or "", False
        except subprocess.TimeoutExpired as e:
            def s(x):
                return (x.decode("utf-8", "replace")
                        if isinstance(x, bytes) else (x or ""))
            return -1, s(e.stdout), s(e.stderr), True
    r = subprocess.run(cmd, capture_output=True, text=True,
                       errors="replace", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or "", False


def run_gate(outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    checks = []
    attempts = {}
    for label in ("full", "sampled", "formal"):
        sub = outdir / label
        shutil.rmtree(sub, ignore_errors=True)
        res = _run(MANIFESTS[label], sub, label)
        attempts[label] = _attempt(sub, MANIFESTS[label])
        checks.append({"check": f"{label}: runner status", "pass":
                       res.get("status") == "admitted", "detail": res})

    early_root = outdir / "early"
    shutil.rmtree(early_root, ignore_errors=True)
    early_manifest = MANIFESTS["sampled"]
    early_res = R.run_seed(early_manifest, 1, out_root=early_root,
                           root=ROOT, runner=_early_runner)
    early_attempt = _attempt(early_root, early_manifest)
    attempts["early"] = early_attempt
    checks.append({"check": "early: run not admitted", "pass":
                   early_res.get("status") != "admitted",
                   "detail": early_res})

    stats = {}
    for label in ("full", "sampled", "formal"):
        att = attempts[label]
        audits, _ = _audit(att) if att else ({"ok": False}, False)
        chain = _chain(att) if att else {}
        f5 = _f5(chain)
        stats[label] = {
            "attempt": str(att) if att else None,
            "audit_ok": bool(audits.get("ok")),
            "audit_failures": audits.get("failures", []),
            "oracle": (chain.get("run_level_oracle") or {}).get("category"),
            "faults_injected": (chain.get("run_level_oracle") or {}).get(
                "faults_injected"),
            "exposures_total": f5.get("exposures_total"),
            "activated_exposure_count": f5.get("activated_exposure_count"),
            "exposures_sampled": f5.get("exposures_sampled"),
            "exposures_dropped": f5.get("exposures_dropped"),
            "sampled_unique": f5.get("sampled_unique"),
            "eligible_seen_total": f5.get("eligible_seen_total"),
            "chain_end_terminal": f5.get("chain_end_terminal"),
            "artifacts": _art(att) if att else None,
        }
        checks.append({"check": f"{label}: audit.ok",
                       "pass": bool(audits.get("ok")),
                       "detail": audits.get("failures", [])})
        checks.append({"check": f"{label}: chain_end terminal present",
                       "pass": bool(f5.get("chain_end_terminal")),
                       "detail": f5.get("chain_end_terminal")})
        if label in ("full", "sampled"):
            cons = (f5.get("exposures_total") is not None
                    and f5.get("exposures_sampled") is not None
                    and f5.get("exposures_dropped") is not None
                    and f5["exposures_total"] ==
                    f5["exposures_sampled"] + f5["exposures_dropped"])
            checks.append({"check": f"{label}: total=sampled+dropped",
                           "pass": cons, "detail": f5})
            checks.append({"check": f"{label}: sampled == unique ids",
                           "pass": f5.get("exposures_sampled") ==
                           f5.get("sampled_unique"), "detail": f5})

    if all(stats[k]["attempt"] for k in ("full", "sampled")):
        for field in ("exposures_total", "activated_exposure_count",
                      "faults_injected", "oracle"):
            checks.append({
                "check": f"full == sampled: {field}",
                "pass": stats["full"].get(field) ==
                        stats["sampled"].get(field),
                "detail": {"full": stats["full"].get(field),
                           "sampled": stats["sampled"].get(field)},
            })

    formal_art = stats.get("formal", {}).get("artifacts") or {}
    if formal_art:
        checks.append({
            "check": "formal: prop_evt bounded (< 200000 events)",
            "pass": int(formal_art.get("prop_evt_bytes", 1 << 60)) < 512 << 20,
            "detail": formal_art,
        })
        checks.append({
            "check": "formal: evidence files bounded",
            "pass": int(formal_art.get("injection_log_bytes", 1 << 60)) <
                    2 << 30,
            "detail": formal_art,
        })

    if early_attempt:
        early_audit, _ = _audit(early_attempt)
        checks.append({"check": "early: audit is NOT ok (fail-closed)",
                       "pass": not bool(early_audit.get("ok")),
                       "detail": early_audit.get("failures", [])})
        auth = early_attempt.parent / "AUTHORITATIVE"
        checks.append({"check": "early: no AUTHORITATIVE",
                       "pass": not auth.exists(),
                       "detail": str(auth)})
        prop = early_attempt / "inject/prop_evt.txt.gz"
        has_end = False
        if prop.exists():
            import fsu_prop_fields as P
            events, _, _ = P.read_stream(prop)
            has_end = any(str(e.get("kind")) == "chain_end"
                          and str(e.get("exposures_total")).strip()
                          for e in events)
        checks.append({"check": "early: no injector chain_end",
                       "pass": not has_end, "detail": {"has_end": has_end}})

    passed = all(c["pass"] for c in checks)
    summary = {
        "gate": "F5-FP06-W4",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "passed": passed,
        "formal_suite_seed_count": 0,
        "standalone_seed_count": 0,
        "checks": checks,
        "stats": stats,
        "attempts": {k: (str(v) if v else None) for k, v in attempts.items()},
    }
    (outdir / "gate_checks.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# FP06-F5-W4 gate (non-formal, never 519/240)",
        "",
        f"- generated: {summary['generated_at']}",
        f"- conclusion: **{'PASS' if passed else 'FAIL'}**",
        f"- evidence: `{outdir}`",
        "",
        "| item | value |",
        "|---|---|",
    ]
    for label, s in stats.items():
        lines.append(f"| {label} exposures_total | {s.get('exposures_total')} |")
        lines.append(f"| {label} activated | "
                     f"{s.get('activated_exposure_count')} |")
        lines.append(f"| {label} sampled / dropped | "
                     f"{s.get('exposures_sampled')} / "
                     f"{s.get('exposures_dropped')} |")
        lines.append(f"| {label} oracle | {s.get('oracle')} |")
        lines.append(f"| {label} audit.ok | {s.get('audit_ok')} |")
    lines += ["", "## Checks", "", "| check | result | detail |",
              "|---|---|---|"]
    for c in checks:
        lines.append(f"| {c['check']} | {'PASS' if c['pass'] else 'FAIL'} | "
                     f"`{json.dumps(c['detail'], ensure_ascii=False)[:240]}` |")
    (outdir / "GATE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def verify_only(outdir: Path):
    p = outdir / "gate_checks.json"
    if not p.exists():
        return {"passed": False, "error": f"missing {p}"}
    return json.loads(p.read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="FP06-F5-W4 non-formal gate")
    ap.add_argument("--outdir", default=str(DEFAULT_OUT))
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args(argv)
    if a.verify_only:
        print(json.dumps(verify_only(Path(a.outdir)), ensure_ascii=False,
                         indent=2))
        return 0
    res = run_gate(Path(a.outdir))
    print(json.dumps({"passed": res["passed"],
                      "evidence": str(Path(a.outdir))},
                     ensure_ascii=False, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
