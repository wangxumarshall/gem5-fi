#!/usr/bin/env python3
"""escape_decomp.py — SDC escape-set decomposition (plan §8.1 / task S5-2).

Attributes every SDC (and SDC-class) outcome across the formal campaigns to
one of the six escape mechanisms (§8.1 A–F), producing the paper's escape
decomposition table. Honest: mechanisms without data (D post-check escape
via CHAOSL1DForward formal, E ECC-logic fault, F poison-loss) are reported
as "no data".

Usage:
  python3 tools/escape_decomp.py --l1d artifacts/l1d-ecc \
      --campaigns artifacts/prf-formal artifacts/m1-formal-num [...] \
      [--out docs/paper/tables/t6-escape-decomp.md]
"""
import argparse, csv, os, glob

# Units whose protection baseline is "none" (N1 TRM Table 9-1 proxy §2.3):
# RAS 范围外结构 — a raw fault IS the escape (mechanism A). Campaign dir
# names carry the unit (prf-formal → prf; m1-formal-num → rat; h2-window →
# prf; lsq-matrix → lsq_fwd).
UNPROTECTED_UNITS = {"prf", "rat", "freelist", "rob", "iq", "lsq_fwd",
                     "l1_tlb", "l2_tlb", "exec", "fsu", "mem", "l1d", "l2"}

# campaign-dir → unit overrides for names that don't start with the unit.
SOURCE_UNIT_OVERRIDES = {"m1-formal-num": "rat", "m1-formal-both": "rat",
                         "h2-window": "prf"}

def unit_from_source(src):
    """Infer the unit from a campaign/source name (longest prefix match)."""
    if src in SOURCE_UNIT_OVERRIDES:
        return SOURCE_UNIT_OVERRIDES[src]
    for u in sorted(UNPROTECTED_UNITS, key=len, reverse=True):
        if src.startswith(u):
            return u
    return src

def classify_escape_mechanism(unit, protection, bits, classification):
    """Map one outcome to §8.1 mechanism A–F, or 'None' (not an escape)."""
    if classification not in ("SDC", "Latent"):
        return "None"          # Corrected/DetectedContained/Crash/Hang/Masked: contained or DUE
    if protection == "sed" and bits >= 2:
        return "B"             # SED-only ≥2-bit silent
    if protection == "secded" and bits >= 3:
        return "C"             # beyond SECDED
    if protection in ("secded", "secded_poison") and bits == 2:
        return "None"          # 2-bit under SECDED: contained, not escape
    if protection == "none":
        # Accept either a bare unit name or a campaign/source name (the
        # latter is normalized via unit_from_source).
        return "A" if unit_from_source(unit) in UNPROTECTED_UNITS else "None"
    return "None"

def decompose(l1d_dir=None, campaigns=None):
    """Tally SDC-class outcomes by mechanism.

    l1d_dir: dir of per-rep csv files (schema tag,protection,bits,classification,faults).
    campaigns: list of campaign dirs each holding cells.csv (aggregate rows).
    Returns {mech: {count, share, sources}} for A–F (0-count mechanisms kept)."""
    mechs = {}
    def add(m, src):
        if m == "None":
            return
        e = mechs.setdefault(m, {"count": 0, "sources": set()})
        e["count"] += 1
        e["sources"].add(src)
    if l1d_dir and os.path.isdir(l1d_dir):
        for path in sorted(glob.glob(os.path.join(l1d_dir, "*.csv"))):
            src = os.path.basename(path).replace(".csv", "")
            with open(path) as f:
                for row in csv.DictReader(f):
                    add(classify_escape_mechanism(
                            "l1d", row.get("protection", "none"),
                            int(row.get("bits", 1) or 1),
                            row.get("classification", "")), src)
    for camp in (campaigns or []):
        path = os.path.join(camp, "cells.csv")
        if not os.path.exists(path):
            continue
        src = os.path.basename(os.path.normpath(camp))
        unit = unit_from_source(src)
        with open(path) as f:
            for row in csv.DictReader(f):
                n = int(row.get("SDC", 0) or 0) + int(row.get("Latent", 0) or 0)
                for _ in range(n):
                    add(classify_escape_mechanism(
                            unit, "none", 1, "SDC"), src)
    out = {}
    total = sum(e["count"] for e in mechs.values())
    for m in ("A", "B", "C", "D", "E", "F"):
        e = mechs.get(m)
        cnt = e["count"] if e else 0
        out[m] = {"count": cnt,
                  "share": (cnt / total if total else 0.0),
                  "sources": ",".join(sorted(e["sources"])) if e else ""}
    return out

MECH_DESC = {
    "A": "RAS 范围外结构 raw escape（PRF/RAT/ROB/IQ/LSQ-fwd/TLB none）",
    "B": "SED-only ≥2-bit 静默",
    "C": "≥3-bit 超 SECDED",
    "D": "post-check escape（ECC 后数据通路）",
    "E": "ECC 逻辑自身故障（漏检/误纠）",
    "F": "毒化传播丢失",
}

def render_markdown(dec):
    lines = ["# SDC 逃逸集合分解（§8.1 机理 A–F）", "",
             "| 机理 | SDC 事件数 | 占比 | 数据源 |",
             "|---|---|---|---|"]
    for m in "ABCDEF":
        e = dec[m]
        if e["count"] == 0:
            lines.append(f"| {m} | no data | — | {MECH_DESC[m]} |")
        else:
            lines.append(f"| {m} | {e['count']} | {e['share']:.1%} | {e['sources']} |")
    lines += ["", "> All counts are gem5-proxy conditional outcomes, NOT FIT.",
              "> D/E/F 无 formal 数据（CHAOSL1DForward/CHAOSRAS 未跑 formal）——如实标注 no data。"]
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l1d", default="artifacts/l1d-ecc")
    ap.add_argument("--campaigns", nargs="*", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    dec = decompose(l1d_dir=a.l1d, campaigns=a.campaigns)
    md = render_markdown(dec)
    print(md)
    if a.out:
        with open(a.out, "w") as f:
            f.write(md + "\n")

if __name__ == "__main__":
    main()
