#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reclassify a preserved real experiment outcome that an older runner marked
as `.failed` before the real-outcome distinction existed.

Only the tool marker is changed; raw evidence (manifest, prop stream, oracle,
chain report, stats) is never touched. An attempt qualifies only when its
stored chain report has a real terminal and the stream is intact.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_chain_check as C  # noqa: E402

REAL_TERMINALS = {"not_consumed", "exposed_unconsumed", "free_realloc",
                  "squashed", "overwritten"}


def reclassify(attempt: Path) -> dict:
    failed = attempt / ".failed"
    if not failed.exists():
        return {"attempt": str(attempt), "changed": False,
                "reason": "no .failed marker"}
    report_path = attempt / "chain_report.json"
    manifest_path = attempt / "manifest.json"
    prop = attempt / "inject/prop_evt.txt.gz"
    if not (report_path.exists() and manifest_path.exists() and prop.exists()):
        return {"attempt": str(attempt), "changed": False,
                "reason": "chain_report/manifest/prop_evt missing"}
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored_chain = report.get("chain") or {}
    # Recompute with the CURRENT chain tool; the stored terminal may predate
    # the real-outcome distinction. Raw evidence is only read.
    try:
        chain = C.check_stream(
            prop, run_id=manifest.get("run_id"),
            sample_run_id=manifest.get("sample_run_id") or
            f"s{manifest.get('seed')}")
    except Exception as e:  # noqa: BLE001
        return {"attempt": str(attempt), "changed": False,
                "reason": f"chain recompute failed: {e}"}
    terminals = {r.get("terminal") for r in (chain.get("faults") or {}).values()}
    oracle = (report.get("oracle") or {}).get("category")
    if chain.get("truncated"):
        return {"attempt": str(attempt), "changed": False,
                "reason": "stream truncated"}
    if oracle in ("SimulatorError", "Inactive", "Timeout"):
        return {"attempt": str(attempt), "changed": False,
                "reason": f"oracle={oracle}"}
    real = sorted(t for t in terminals if t in REAL_TERMINALS)
    if not real:
        return {"attempt": str(attempt), "changed": False,
                "reason": f"no real terminal: {sorted(t for t in terminals if t)}"}
    note = (f"reclassified from .failed: oracle={oracle} "
            f"terminals={real}\n"
            f"original marker: {failed.read_text(encoding='utf-8').strip()}\n")
    (attempt / ".real_outcome").write_text(note, encoding="utf-8")
    failed.rename(attempt / ".failed.historical")
    return {"attempt": str(attempt), "changed": True, "terminals": real,
            "oracle": oracle}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("attempts", nargs="+")
    a = ap.parse_args(argv)
    out = []
    for raw in a.attempts:
        p = Path(raw)
        candidates = [p] if p.name.startswith("attempt-") else \
            sorted(x for x in p.glob("attempt-*") if x.is_dir())
        for attempt in candidates:
            out.append(reclassify(attempt))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
