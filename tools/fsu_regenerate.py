#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_regenerate.py — 从原始证据重建派生证据（不修改原始证据）。

重建: chain_report.json（含 top-level admitted/certified/violations）、
seed Markdown、evidence_sha256.json、audit.json/audit.md，并复制权威
Markdown 到 COMPLETE_PROPAGATION_PATHS。原始 prop_evt/stats/run.out/
run.err/注入日志只读；重建前后哈希必须一致，否则响亮失败。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_chain_check as C  # noqa: E402
import fsu_seed_audit  # noqa: E402
import fsu_seed_doc  # noqa: E402
import fsu_seed_runner as R  # noqa: E402

RAW_FILES = [
    "inject/prop_evt.txt.gz", "stats.txt", "run.out", "run.err",
    "inject/fpu_injections.log", "inject/stats.txt",
    "census/fpu_injections.log", "census/stats.txt",
    "census.out", "census.err",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _raw_hashes(attempt: Path):
    return {rel: _sha(attempt / rel) for rel in RAW_FILES
            if (attempt / rel).exists()}


def regenerate(attempt: Path, out_root: Path):
    attempt = Path(attempt)
    out_root = Path(out_root)
    before = _raw_hashes(attempt)
    manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    old = json.loads((attempt / "chain_report.json").read_text(encoding="utf-8"))
    oracle = json.loads((attempt / "oracle.json").read_text(encoding="utf-8")) \
        if (attempt / "oracle.json").exists() else old.get("oracle", {})
    prop = attempt / "inject/prop_evt.txt.gz"
    run_id = manifest["run_id"]
    seed = manifest["seed"]
    sample = manifest.get("sample_run_id") or f"s{seed}"
    chain = C.check_stream(prop, run_id=run_id, sample_run_id=sample) \
        if prop.exists() else {
            "path": str(prop), "event_count": 0, "truncated": True,
            "truncation_reason": "missing prop_evt", "identity_violations": [],
            "faults": {}, "admitted_faults": [], "admitted": False,
            "certified": False, "violations": ["missing_prop_evt"]}
    stats = attempt / "stats.txt"
    report = {
        **old,
        "run_id": run_id,
        "seed": seed,
        "sample_run_id": sample,
        "oracle": oracle,
        "chain": chain,
        "admitted": chain.get("admitted"),
        "certified": chain.get("certified"),
        "violations": chain.get("violations", []),
        "stats_nonempty": stats.exists() and stats.stat().st_size > 0,
        "prop_evt_exists": prop.exists(),
    }
    (attempt / "chain_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = fsu_seed_doc.write_doc(attempt, manifest, report)
    R.write_hashes(attempt)
    audit = fsu_seed_audit.write_audit(attempt)
    dst = (out_root / "COMPLETE_PROPAGATION_PATHS" / run_id /
           f"{run_id}-seed{seed}.md")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(md, dst)
    after = _raw_hashes(attempt)
    if before != after:
        raise SystemExit(f"[ABORT] raw evidence changed in {attempt}: "
                         f"{ {k: (before.get(k), after.get(k)) for k in set(before) | set(after) if before.get(k) != after.get(k)} }")
    return {"attempt": str(attempt), "admitted": chain.get("admitted"),
            "certified": chain.get("certified"),
            "audit_ok": audit.get("ok"),
            "audit_certified": audit.get("certified"),
            "md": str(md), "raw_files_unchanged": True}


def main(argv=None):
    ap = argparse.ArgumentParser(description="FSU 派生证据重建")
    ap.add_argument("--attempt", action="append", required=True)
    ap.add_argument("--out-root", default=str(R.DEFAULT_OUT))
    a = ap.parse_args(argv)
    out = []
    for p in a.attempt:
        out.append(regenerate(Path(p), Path(a.out_root)))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if all(x["audit_ok"] for x in out) else 1


if __name__ == "__main__":
    sys.exit(main())
