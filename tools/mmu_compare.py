#!/usr/bin/env python3
"""Compare a control terminal log with a fault terminal log (per context)."""
import argparse
import csv
import sys


def parse(path, prefix):
    out = {}
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith(prefix):
                continue
            d = {"_line": line}
            for p in line.split()[1:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    d[k] = v
            out[d.get("ctx", "?")] = d
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", required=True)
    ap.add_argument("--fault", required=True)
    ap.add_argument("--prefix", required=True, choices=["W9_RESULT", "W10_RESULT"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    c = parse(args.control, args.prefix)
    f = parse(args.fault, args.prefix)
    keys = sorted(set(c) | set(f))
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["context", "control_observed", "fault_observed",
                    "control_result", "fault_result", "control_line",
                    "fault_line", "delta"])
        for k in keys:
            cc = c.get(k, {})
            ff = f.get(k, {})
            co = cc.get("observed", "")
            fo = ff.get("observed", "")
            cr = cc.get("result", "")
            fr = ff.get("result", "")
            delta = "identical" if cc.get("_line") == ff.get("_line") \
                else "observed %s -> %s ; result %s -> %s" % (co, fo, cr, fr)
            w.writerow([k, co, fo, cr, fr, cc.get("_line", ""),
                        ff.get("_line", ""), delta])
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
