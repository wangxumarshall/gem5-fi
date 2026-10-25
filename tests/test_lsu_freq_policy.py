#!/usr/bin/env python3
"""Frequency-policy overlay contract test."""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import lsu_freq_policy as P

fails = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))
    if not cond: fails.append(name)

def test_policy_covers_all_runids():
    pol = P.load_policy()
    ids = {e["run_id"] for e in pol["entries"]}
    rm = json.loads((REPO/"docs/gem5-fi/lsu/mdspec/runid_map.json").read_text("utf-8"))
    check("policy_covers_325", len(rm["entries"]) == 325 and all(e["run_id"] in ids for e in rm["entries"]))
    check("f6_is_64", sum(1 for e in pol["entries"] if e["frequency"]=="F6" and not e.get("legacy")) == 64)

def main():
    test_policy_covers_all_runids()
    print(f"\n{'ALL PASS' if not fails else 'FAILED (%d): %s' % (len(fails), fails)}")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
