#!/usr/bin/env python3
"""
P6: SDC bit-flip position spectrum analyzer.

Input: a list of XOR masks (golden ^ actual) + the precision of the corrupted
value. Output: per-field (sign / exponent / mantissa) flip counts and shares,
popcount (flip-bit-count) distribution, and the path-dependent regularity
signature that reproduce-method2 v3 §6 established for the core-179 SDC defect
(mantissa-concentrated 85-93%, sign-immune 0-1, path-dependent count: tight
store->reload & GEMM -> multi-bit; iterative SVD -> single-bit).

This is the analysis-side counterpart to CHAOSPhysReg's read-trace closure:
the closure answers "did the fault propagate?" (Benign/Masked/SDC/Crash); this
answers "what does the corruption look like?" (bit-position signature). Together
they form the two-axis characterization needed for H3/H4 in EXPERIMENT_DESIGN.

Usage:
  python3 bit_spectrum.py --precision float  < masks.txt
  python3 bit_spectrum.py --precision double masks.txt
  python3 bit_spectrum.py --precision float --inline 0x0001F1F0 0x7FE873E6 ...

Fields (IEEE 754):
  float32 : 1 sign | 8 exponent | 23 mantissa   (bits 31 / 30-23 / 22-0)
  double64: 1 sign | 11 exponent | 52 mantissa  (bits 63 / 62-52 / 51-0)
"""
import argparse
import sys
from pathlib import Path

# IEEE 754 field layouts: (sign_hi, sign_lo, exp_hi, exp_lo, man_hi, man_lo)
# bit ranges inclusive, numbered from LSB (0) up.
LAYOUTS = {
    "float":  dict(sign=(31,31), exp=(30,23), man=(22,0),  width=32),
    "double": dict(sign=(63,63), exp=(62,52), man=(51,0), width=64),
}

def popcount(x):
    return bin(x).count("1")

def field_bits(mask, hi, lo):
    """Count set bits in mask within [lo,hi] inclusive."""
    full = (1 << (hi - lo + 1)) - 1
    return bin((mask >> lo) & full).count("1")

def parse_masks(args):
    masks = []
    if args.inline:
        for tok in args.inline:
            masks.append(int(tok, 0))
    else:
        src = args.input if isinstance(args.input, str) else sys.stdin
        for line in src:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # accept "0x...." or bare hex/dec, optionally "golden=.. actual=.. xor=0x.."
            tok = line.split()[-1] if "xor" in line.lower() else line.split()[0]
            try:
                masks.append(int(tok, 0))
            except ValueError:
                pass
    return masks

def analyze(masks, precision):
    if precision not in LAYOUTS:
        sys.exit(f"unknown precision {precision}; use float|double")
    L = LAYOUTS[precision]
    w = L["width"]
    n = len(masks)
    if n == 0:
        print("no masks parsed"); return
    tot_sign = tot_exp = tot_man = tot_bits = 0
    popcounts = []
    field_counts = {"sign":0, "exp":0, "man":0}  # samples touching each field
    for m in masks:
        m &= (1 << w) - 1
        pc = popcount(m)
        popcounts.append(pc)
        s = field_bits(m, *L["sign"])
        e = field_bits(m, *L["exp"])
        mn = field_bits(m, *L["man"])
        tot_sign += s; tot_exp += e; tot_man += mn; tot_bits += pc
        if s: field_counts["sign"] += 1
        if e: field_counts["exp"] += 1
        if mn: field_counts["man"] += 1
    print(f"=== bit-spectrum ({precision}, {n} samples, {tot_bits} flipped bits) ===")
    print(f"  sign      : {tot_sign:5d}  ({100*tot_sign/tot_bits:5.1f}%)  samples touching sign: {field_counts['sign']}")
    print(f"  exponent  : {tot_exp:5d}  ({100*tot_exp/tot_bits:5.1f}%)  samples touching exp:  {field_counts['exp']}")
    print(f"  mantissa  : {tot_man:5d}  ({100*tot_man/tot_bits:5.1f}%)  samples touching man:  {field_counts['man']}")
    popcounts.sort()
    med = popcounts[n//2]
    print(f"  popcount  : min={popcounts[0]} median={med} max={popcounts[-1]}")
    single = sum(1 for p in popcounts if p == 1)
    multi  = sum(1 for p in popcounts if p >= 4)
    print(f"  regularity: single-bit samples={single}/{n}  multi-bit(>=4)={multi}/{n}")
    # Signature check vs method2 v3 §6
    man_share = 100*tot_man/tot_bits
    sign_share = 100*tot_sign/tot_bits
    print(f"  signature: mantissa {man_share:.0f}% (method2 expects 85-93%), "
          f"sign {sign_share:.0f}% (expects 0-1%)")
    if man_share >= 80 and sign_share <= 5:
        print("  => MATCHES method2 v3 §6 data-path-corruption signature")
    else:
        print("  => does NOT match method2 signature (different corruption site or SEU)")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--precision", required=True, choices=["float","double"])
    ap.add_argument("--input", default=None, help="file of xor masks (default stdin)")
    ap.add_argument("--inline", nargs="+", default=None, help="masks on cmdline, e.g. --inline 0x0001F1F0 0x7FE873E6")
    args = ap.parse_args()
    if args.input:
        with open(args.input) as f:
            args.input = f
    masks = parse_masks(args)
    analyze(masks, args.precision)

if __name__ == "__main__":
    main()
