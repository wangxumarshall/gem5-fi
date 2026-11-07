#!/usr/bin/env python3
"""Re-adjudicate existing v3.2.1/v3.2.3 pilot traces with the v3.2.4
chain-scoped terminal rules. Read-only: the old traces and pilot_meta files
are never modified. Prints a Markdown table (old -> new verdict)."""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parent
sys.path.insert(0, str(PLATFORM))

from terminal_rules import adjudicate  # noqa: E402
from trace_validator import read_records  # noqa: E402

IMPL = PLATFORM.parent


def trace_for(d: Path) -> Path | None:
    for name in ("trace_v31.jsonl", "trace_v31.jsonl.gz"):
        p = d / name
        if p.exists():
            return p
    return None


def main() -> int:
    metas = []
    for pattern in ("pilots_v3_2_1/*/pilot_meta.json",
                    "pilots_v3_2_3/sweep/*/pilot_meta.json",
                    "pilots_v3_2_2/*/pilot_meta.json"):
        metas.extend(glob.glob(str(IMPL / pattern)))
    print("# LSU v3.2.4 — FW02 / existing-pilot terminal re-adjudication")
    print()
    print("Read-only pass over stored traces; `new` uses `terminal_rules.adjudicate`.")
    print()
    print("| Pilot | Model | Old terminal | New terminal | Reason | Oracle |")
    print("|---|---|---|---|---|---|")
    changed = []
    for mp in sorted(metas):
        m = json.load(open(mp))
        d = Path(mp).parent
        trace = trace_for(d)
        if trace is None:
            continue
        old = m.get("classification", {}).get("terminal_state")
        oracle = m.get("classification", {}).get("oracle_outcome")
        if oracle is None:
            oracle = "PASS" if m.get("oracle_pass") else "FAIL"
        try:
            events = [r for r in read_records(trace)
                      if r.get("record_type") == "event"]
        except Exception as exc:  # noqa: BLE001
            print(f"| {d.name} | {m.get('model')} | {old} | ERROR | {exc} | {oracle} |")
            continue
        new, reason = adjudicate(
            events, model=m.get("model", ""), observed_terminal=old or "MASKED",
            oracle_pass=(oracle == "PASS"), trace_complete=True)
        print(f"| {d.name} | {m.get('model')} | {old} | {new} | {reason} | {oracle} |")
        if new != old:
            changed.append((d.name, old, new, reason))
    print()
    print("## Changed verdicts")
    print()
    if not changed:
        print("None.")
    for name, old, new, reason in changed:
        print(f"- `{name}`: {old} -> **{new}** ({reason})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
