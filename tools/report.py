#!/usr/bin/env python3
"""Cross-campaign report generator (plan §9.1 table producer).

Merges multiple campaign cells.csv files, aggregates SDC/n_valid by a unit
column (target_arch / semantic_role / fault_model / ...), computes Wilson
95% CI per group, and emits a paper-ready Markdown table + CSV.

Usage:
  python3 tools/report.py --inputs artifacts/a/cells.csv artifacts/b/cells.csv \
      --unit-col target_arch [--out artifacts/report]
"""
import argparse, csv, math, os, sys

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0, 0.0)
    p = k / n
    if k == 0: return (0.0, 0.0, min(1.0, 3.0 / n))
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0.0, c-h), p, min(1.0, c+h))

def merge_campaigns(paths, unit_col="target_arch"):
    agg = {}
    for path in paths:
        with open(path) as f:
            for row in csv.DictReader(f):
                unit = row.get(unit_col) or row.get("fault_model") or "?"
                a = agg.setdefault(unit, {"sdc": 0, "n_valid": 0, "hang": 0,
                                          "crash": 0, "masked": 0,
                                          "inactive": 0, "files": set()})
                a["sdc"] += int(row["SDC"])
                a["n_valid"] += int(row["n_valid"])
                for k in ("hang","crash","masked","inactive"):
                    col = {"hang":"Hang","crash":"Crash","masked":"Masked",
                           "inactive":"Inactive"}[k]
                    a[k] += int(row.get(col, 0))
                a["files"].add(os.path.basename(os.path.dirname(path)))
    rows = []
    for unit, a in sorted(agg.items(), key=lambda kv: -kv[1]["sdc"]):
        lo, p, hi = wilson(a["sdc"], a["n_valid"])
        rows.append({"unit": unit, "sdc": a["sdc"], "n_valid": a["n_valid"],
                     "p": p, "lo": lo, "hi": hi, "hang": a["hang"],
                     "crash": a["crash"], "masked": a["masked"],
                     "sources": ",".join(sorted(a["files"]))})
    return rows

def render_markdown(rows):
    out = ["# Cross-campaign SDC report", "",
           "| unit | SDC/n_valid | P_SDC | Wilson 95% CI | Hang | Crash | Masked | sources |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['unit']} | {r['sdc']}/{r['n_valid']} | "
                   f"{r['p']:.3f} | [{r['lo']:.3f},{r['hi']:.3f}] | "
                   f"{r['hang']} | {r['crash']} | {r['masked']} | {r['sources']} |")
    out.append("")
    out.append("> All P_SDC are gem5-proxy conditional probabilities, NOT "
               "product FIT. Wilson 95% CI.")
    return "\n".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--unit-col", default="target_arch")
    ap.add_argument("--out", default=None, help="output prefix (.md + .csv)")
    a = ap.parse_args()
    rows = merge_campaigns(a.inputs, unit_col=a.unit_col)
    md = render_markdown(rows)
    print(md)
    if a.out:
        with open(a.out + ".md", "w") as f: f.write(md)
        if rows:
            with open(a.out + ".csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    main()
