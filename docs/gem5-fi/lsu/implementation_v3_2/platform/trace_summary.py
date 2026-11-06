"""Summarize a Trace v3.1 JSONL file (counts + terminal dimensions)."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from trace_completeness import check_completeness
from trace_validator import read_records


def summarize(path: Path) -> dict:
    records = [r for r in read_records(path) if "__parse_error__" not in r]
    events = [r for r in records if r.get("record_type") == "event"]
    edges = [r for r in records if r.get("record_type") == "propagation_edge"]
    summaries = [r for r in records if r.get("record_type") == "summary"]
    summary = summaries[0] if len(summaries) == 1 else {}
    completeness = check_completeness(path)
    return {
        "trace": str(path),
        "events": len(events),
        "edges": len(edges),
        "event_types": dict(Counter(e.get("event_type") for e in events)),
        "units": dict(Counter(e.get("unit") for e in events)),
        "injection_status": dict(Counter(e.get("injection_status") for e in events)),
        "commit_status": dict(Counter(e.get("commit_status") for e in events)),
        "squash_status": dict(Counter(e.get("squash_status") for e in events)),
        "summary": {
            "run_status": summary.get("run_status"),
            "fault_activation_status": summary.get("fault_activation_status"),
            "terminal_state": summary.get("terminal_state"),
            "trace_completeness": summary.get("trace_completeness"),
        },
        "completeness_check": completeness,
    }


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("usage: trace_summary.py <trace.jsonl[.gz]>", file=sys.stderr)
        return 2
    print(json.dumps(summarize(Path(argv[0])), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
