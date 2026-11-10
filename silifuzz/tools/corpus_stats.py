#!/usr/bin/env python3
"""Corpus statistics for the reproduction report."""

from __future__ import annotations

import collections
import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import sfsnapshot as sf  # noqa: E402


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else "work/corpus"
    out = sys.argv[2] if len(sys.argv) > 2 else "evidence/corpus-stats.json"
    files = sorted(glob.glob(os.path.join(root, "**", "*.sfs"), recursive=True))
    sources = collections.Counter()
    signals = collections.Counter()
    mappings = collections.Counter()
    code_bytes = []
    attempts = collections.Counter()
    total_bytes = 0
    signals_by_source = collections.defaultdict(collections.Counter)

    for path in files:
        total_bytes += os.path.getsize(path)
        s = sf.load(path)
        src = "unknown"
        try:
            src = json.loads(s.meta).get("source", "unknown")
        except json.JSONDecodeError:
            pass
        sources[src] += 1
        mappings[len(s.mappings)] += 1
        attempts[json.loads(s.meta).get("attempts", 0) if s.meta else 0] += 1
        code_bytes.append(len(s.mappings[0].data))
        if s.end_states:
            sig = s.end_states[0].signal
            signals[sig] += 1
            signals_by_source[src][sig] += 1

    def pct(values, p):
        if not values:
            return 0
        values = sorted(values)
        return values[min(len(values) - 1, int(len(values) * p))]

    stats = {
        "corpus": root,
        "snapshots": len(files),
        "bytes": total_bytes,
        "bytes_per_snapshot": total_bytes / len(files) if files else 0,
        "sources": dict(sources),
        "signals": {str(k): v for k, v in signals.items()},
        "signals_by_source": {k: {str(a): b for a, b in v.items()}
                              for k, v in signals_by_source.items()},
        "mappings": {str(k): v for k, v in mappings.items()},
        "attempts": {str(k): v for k, v in attempts.items()},
        "code_bytes": {
            "min": min(code_bytes) if code_bytes else 0,
            "p50": pct(code_bytes, 0.5),
            "p90": pct(code_bytes, 0.9),
            "max": max(code_bytes) if code_bytes else 0,
            "mean": statistics.mean(code_bytes) if code_bytes else 0,
        },
    }
    with open(out, "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
