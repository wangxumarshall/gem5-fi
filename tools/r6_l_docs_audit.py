#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-L-UNIT] Independent audit of the 42 L propagation docs.

Checks, per doc, against THAT seed's own raw evidence only:
  * identity/name ownership;
  * every evidence-row SHA-256;
  * every event-order line exists in the seed's prop_evt with matching
    kind/tick, and its parent exists and does not post-date it;
  * terminal/provable_to/admitted/certified match chain_report.json;
  * no broken relative Markdown links;
  * the doc set is exactly 42 seeds / 14 RunIDs.

Writes a JSON report and exits non-zero on any mismatch.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import lsu_prop_fields as PF  # noqa: E402

DOCS_DEFAULT = "/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"
PREFIXES = ("L01", "L02", "L03")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def docs(root):
    out = []
    for pref in PREFIXES:
        out += sorted(Path(root).glob(f"{pref}-*/*-seed*.md"))
    return out


def audit_one(p):
    problems = []
    text = p.read_text()
    m = re.search(r"RunID `([^`]+)` / seed `(\d+)`", text)
    if not m:
        return ["identity line missing"], None
    rid, seed = m.group(1), int(m.group(2))
    if p.parent.name != rid or p.name != f"{rid}-seed{seed}.md":
        problems.append("doc name/identity mismatch")
    for _key, path, sha in re.findall(
            r"\| (prop_evt|stats|run_out|inj_log|manifest) \| "
            r"`([^`]+)` \| `([0-9a-f]{64})` \|", text):
        if not os.path.isfile(path):
            problems.append(f"evidence missing {path}")
        elif sha256(path) != sha:
            problems.append(f"evidence SHA mismatch {path}")
    m = re.search(r"\| prop_evt \| `([^`]+)` \|", text)
    if not m:
        return problems + ["prop_evt row missing"], (rid, seed)
    pe = Path(m.group(1))
    events, truncated, _s, _i = PF.read_stream(str(pe))
    byid = {str(e.get("event_id")): e for e in events}
    if truncated:
        problems.append("truncated stream")
    for eid, parent, tick, kind in re.findall(
            r"`event_id=(\d+)` parent=`([^`]*)` tick=`(\d+)` kind=`([^`]+)`",
            text):
        e = byid.get(eid)
        if e is None:
            problems.append(f"event {eid} not in own stream")
            continue
        if str(e.get("kind")) != kind or int(e.get("tick")) != int(tick):
            problems.append(f"event {eid} kind/tick mismatch")
        if parent.strip() not in ("", "—"):
            pev = byid.get(parent)
            if pev is None:
                problems.append(f"parent {parent} not in own stream")
            elif int(pev.get("tick")) > int(e.get("tick")):
                problems.append(f"parent {parent} tick after child {eid}")
    sr = pe.parent / "chain_report.json"
    if not os.path.isfile(sr):
        problems.append("chain_report missing")
    else:
        rep = json.load(open(sr))
        for token in (f"terminal `{rep.get('terminal')}`",
                      f"provable_to `{rep.get('provable_to')}`",
                      f"admitted `{rep.get('admitted')}`",
                      f"certified `{rep.get('certified')}`"):
            if token not in text:
                problems.append(f"verdict token missing: {token}")
    for link in re.findall(r"\]\(([^)]+)\)", text):
        if link.startswith(("http://", "https://", "#")):
            continue
        if not (p.parent / link).exists():
            problems.append(f"broken link {link}")
    return problems, (rid, seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=DOCS_DEFAULT)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    ds = docs(args.docs)
    problems = {}
    seeds = []
    for p in ds:
        probs, ident = audit_one(p)
        if probs:
            problems[str(p)] = probs
        if ident:
            seeds.append(list(ident))
    runids = sorted({r for r, _ in seeds})
    report = {
        "docs_root": args.docs,
        "docs": len(ds),
        "run_ids": len(runids),
        "runid_list": runids,
        "broken_or_mismatched_docs": len(problems),
        "problems": problems,
        "ok": len(ds) == 42 and len(runids) == 14 and not problems,
    }
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: report[k] for k in
                      ("docs", "run_ids", "broken_or_mismatched_docs", "ok")},
                     ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
