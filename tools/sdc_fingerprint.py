#!/usr/bin/env python3
"""sdc_fingerprint.py — SDC bit-spectrum fingerprint library CLI (§7.7/§8.3).

build: unit name -> {sign_exp_share, mantissa_share, popcount_median}
       from a list of XOR masks (golden^actual).
lookup: a field xor value -> Top-K candidate units ranked by field-share
       similarity (diagnosis feedback: spectrum -> suspect unit).

Field classification is IEEE754 double (sign=bit63, exponent=62-52,
mantissa=51-0), matching fi_research/bit_spectrum.py's FIELD_LAYOUTS for
"double"; inlined here (15 lines) because bit_spectrum exposes analyze()
(whole-report) rather than a per-mask field classifier.

Usage:
  python3 tools/sdc_fingerprint.py build lib.json lsq_fwd:masks.txt ...
  python3 tools/sdc_fingerprint.py lookup lib.json 0x00000100 --top 3
"""
import argparse, json, sys, os

# IEEE754 double64 field bits (mirror of bit_spectrum.py FIELD_LAYOUTS)
_SIGN, _EXP_HI, _EXP_LO, _MAN_HI, _MAN_LO = 63, 62, 52, 51, 0

def _field_counts(mask):
    """Classify one 64-bit XOR mask into (sign, exponent, mantissa) counts."""
    sign = 1 if (mask >> _SIGN) & 1 else 0
    exp = bin((mask >> _EXP_LO) & ((1 << (_EXP_HI - _EXP_LO + 1)) - 1)).count("1")
    man = bin(mask & ((1 << (_MAN_HI - _MAN_LO + 1)) - 1)).count("1")
    return sign, exp, man

def build_library(unit_masks):
    lib = {}
    for unit, masks in unit_masks.items():
        sign = exp = man = 0
        pcs = []
        for m in masks:
            s, e, x = _field_counts(m)
            sign += s; exp += e; man += x
            pcs.append(bin(m).count("1"))
        total = sign + exp + man or 1
        pcs.sort()
        lib[unit] = {
            "sign_exp_share": round((sign + exp) / total, 4),
            "mantissa_share": round(man / total, 4),
            "popcount_median": pcs[len(pcs)//2] if pcs else 0,
            "n": len(masks)}
    return lib

def lookup(lib, xor_value):
    """Rank units by how closely the observed field mix matches each unit's
    fingerprint mix. Returns [(unit, similarity)] sorted descending."""
    s, e, m = _field_counts(xor_value)
    tot = s + e + m or 1
    v_man_share = m / tot
    scores = []
    for unit, fp in lib.items():
        # similarity: 1 - |share difference| (1.0 = exact field-mix match)
        sim = 1 - abs(fp["mantissa_share"] - v_man_share)
        scores.append((unit, round(sim, 4)))
    return sorted(scores, key=lambda x: -x[1])

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("out")
    b.add_argument("units", nargs="+", help="unit:masks_file ... (one hex/line)")
    l = sub.add_parser("lookup")
    l.add_argument("lib")
    l.add_argument("xor", type=lambda x: int(x, 0))
    l.add_argument("--top", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "build":
        um = {}
        for spec in a.units:
            unit, path = spec.split(":", 1)
            with open(path) as f:
                um[unit] = [int(line.strip(), 0) for line in f if line.strip()]
        with open(a.out, "w") as f:
            json.dump(build_library(um), f, indent=2)
        print(f"library -> {a.out} ({len(um)} units)")
    else:
        with open(a.lib) as f:
            lib = json.load(f)
        for unit, s in lookup(lib, a.xor)[:a.top]:
            print(f"{unit}: similarity={s}")

if __name__ == "__main__":
    main()
