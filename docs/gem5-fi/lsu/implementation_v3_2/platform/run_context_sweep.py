#!/usr/bin/env python3
"""Run the full A01/A03/FW02 R01-R05 context sweep.

Every one of the 15 contexts gets an entry in ``context_sweep_summary.json``.
A context that fails is recorded as a failure with its reason; it is never
dropped because it did not accept. The sweep calls :mod:`run_pilot` once per
context so each directory remains a self-contained pilot (manifest, command,
logs, CSV and Trace v3.1 JSONL).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parent
MODELS = ("A01", "A03", "FW02")
CONTEXTS = (1, 2, 3, 4, 5)


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _entry(model: str, context: int, outdir: Path, returncode: int,
           stdout: str, stderr: str) -> dict:
    meta = _read_json(outdir / "pilot_meta.json") or {}
    classification = meta.get("classification") or {}
    trace = meta.get("trace") or {}
    completeness = trace.get("completeness") or {}
    accepted = bool(meta.get("accepted"))
    reason = classification.get("terminal_state_reason")
    if not accepted and not reason:
        if meta:
            reason = "NOT_ACCEPTED"
        elif "Traceback" in stderr:
            reason = "RUNNER_EXCEPTION"
        else:
            reason = "NO_PILOT_META"
    return {
        "model": model,
        "context": f"R{context:02d}",
        "pilot_id": f"PILOT-{model}-R{context:02d}",
        "seed": meta.get("seed"),
        "event_ordinal": context,
        "accepted": accepted,
        "injection": meta.get("injection") or {},
        "injection_count": meta.get("injection_count"),
        "run_status": classification.get("run_status"),
        "activation": classification.get("fault_activation_status"),
        "terminal": classification.get("terminal_state"),
        "terminal_reason": reason,
        "record_integrity": classification.get("record_integrity"),
        "propagation_coverage": classification.get("propagation_coverage"),
        "oracle": classification.get("oracle_outcome"),
        "trace_completeness": classification.get("trace_completeness"),
        "trace_counts": {
            "events": completeness.get("events"),
            "edges": completeness.get("edges"),
            "injections": completeness.get("injections"),
            "activations": completeness.get("activations"),
        },
        "crash_evidence": meta.get("crash_evidence"),
        "exit_code": meta.get("exit_code", returncode),
        "runner_returncode": returncode,
        "failure_detail": (None if accepted else
                           (reason or "") + ": " + (stderr.strip().splitlines()[-1]
                                                     if stderr.strip() else "")),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--models", nargs="+", default=list(MODELS), choices=MODELS)
    ap.add_argument("--contexts", nargs="+", type=int, default=list(CONTEXTS),
                    choices=CONTEXTS)
    args = ap.parse_args(argv)

    root = args.outdir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for model in args.models:
        for context in args.contexts:
            pilot_id = f"PILOT-{model}-R{context:02d}"
            outdir = root / f"{model}-R{context:02d}"
            cmd = [sys.executable, str(PLATFORM / "run_pilot.py"),
                   "--model", model, "--context-index", str(context),
                   "--pilot-id", pilot_id, "--outdir", str(outdir)]
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=1800)
            (outdir / "sweep_runner.log").write_text(
                proc.stdout + proc.stderr, encoding="utf-8")
            entry = _entry(model, context, outdir, proc.returncode,
                           proc.stdout, proc.stderr)
            entries.append(entry)
            print(f"{pilot_id}: accepted={entry['accepted']} "
                  f"terminal={entry['terminal']} "
                  f"injected={(entry['injection'] or {}).get('injected')} "
                  f"reason={entry['terminal_reason']}")

    summary = {
        "schema_version": "lsu-context-sweep-v3.2.2",
        "contexts_expected": len(args.models) * len(args.contexts),
        "contexts_recorded": len(entries),
        "accepted": sum(1 for e in entries if e["accepted"]),
        "failed": [e["pilot_id"] for e in entries if not e["accepted"]],
        "entries": entries,
    }
    (root / "context_sweep_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SUMMARY contexts={summary['contexts_recorded']} "
          f"accepted={summary['accepted']} failed={len(summary['failed'])}")
    return 0 if summary["contexts_recorded"] == summary["contexts_expected"] else 1


if __name__ == "__main__":
    sys.exit(main())
