#!/usr/bin/env python3
"""Extract one fault chain (and its explicit ancestors/descendants) as JSONL.

Usage: mmu_chain_slice.py --trace prop_evt.txt.gz --ptag 1 [--tid 15] \
           --out chain.jsonl
No event is invented: each output line is one parsed PROP-EVT event.
"""
import argparse
import gzip
import json
import sys


def load(path):
    op = gzip.open if open(path, "rb").read(2) == b"\x1f\x8b" else open
    events = []
    with op(path, "rt", errors="replace") as fh:
        for line in fh:
            if not line.startswith("PROP-EVT:"):
                continue
            d = {}
            for tok in line[len("PROP-EVT:"):].split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    d[k] = v
            try:
                d["event_id"] = int(d.get("event_id", ""))
            except ValueError:
                continue
            events.append(d)
    return events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--ptag", type=int, required=True)
    ap.add_argument("--tid", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    events = load(args.trace)
    by_id = {e["event_id"]: e for e in events}
    sel = {}
    for e in events:
        if e.get("fault_id") == str(args.ptag):
            sel[e["event_id"]] = e
        elif args.tid and e.get("translation_id") == args.tid:
            sel[e["event_id"]] = e
    if args.tid:
        seqs = {e.get("dyn_inst_seq") for e in list(sel.values())
                if e.get("dyn_inst_seq", "") not in ("", "0")}
        for e in events:
            if e.get("kind") in ("rf_writeback", "commit", "squash",
                                 "consumer") and \
                    e.get("dyn_inst_seq", "") in seqs:
                sel[e["event_id"]] = e
    changed = True
    while changed:
        changed = False
        for eid in list(sel):
            p = sel[eid].get("parent_event_id", "")
            if p and int(p) in by_id and int(p) not in sel:
                sel[int(p)] = by_id[int(p)]
                changed = True
    out = sorted(sel.values(), key=lambda e: (int(e.get("tick", "0")),
                                               e["event_id"]))
    with open(args.out, "w") as fh:
        for e in out:
            fh.write(json.dumps(e, sort_keys=True) + "\n")
    print("wrote %d events to %s" % (len(out), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
