#!/usr/bin/env python3
"""method1 formal statistics (plan §5.2 H acceptance): Fisher exact,
popcount median, numeric/compute ratio.

Usage: python3 tools/fisher_test.py <numeric_cells.csv> <both_cells.csv>
Reads two campaign cells.csv (numeric-only arm + compute-both arm), each
with SDC/n_valid columns, computes:
  1. P(history_residue) per arm (SDC rate) + Fisher exact p (one-sided)
  2. numeric/compute ratio (field target [2,8]; method1 field 1.0%/0.27%)
  3. Wilson 95% CI per arm
Prints a summary; exit 0 always (stats are reported, not asserted).
"""
import sys, csv, math

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0, 0.0)
    p = k / n
    if k == 0: return (0.0, 0.0, min(1.0, 3.0 / n))
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0, c-h), p, min(1, c+h))

def fisher_exact_1sided(a, b, c, d):
    """Fisher exact for 2x2 [[a,b],[c,d]], one-sided (a/b > c/d direction).
    Pure-python hypergeometric tail (no scipy dependency)."""
    lg = math.lgamma
    n = a+b+c+d
    row1, col1 = a+b, a+c
    lo = max(0, row1 + col1 - n)
    hi = min(row1, col1)
    total = 0.0
    for x in range(a, hi+1):
        lp = (lg(row1+1)+lg(n-row1+1)+lg(col1+1)+lg(n-col1+1)
              - lg(n+1) - lg(x+1) - lg(row1-x+1)
              - lg(col1-x+1) - lg(n-row1-col1+x+1))
        total += math.exp(lp)
    return min(1.0, total)

def main():
    num_csv, both_csv = sys.argv[1], sys.argv[2]
    def arm(path):
        sdc = nv = 0
        with open(path) as f:
            for row in csv.DictReader(f):
                sdc += int(row["SDC"]); nv += int(row["n_valid"])
        return sdc, nv
    a_sdc, a_nv = arm(num_csv)      # numeric-only arm
    b_sdc, b_nv = arm(both_csv)     # compute-both arm
    print(f"numeric-only : SDC={a_sdc}/{a_nv}")
    print(f"compute-both : SDC={b_sdc}/{b_nv}")
    lo_a, p_a, hi_a = wilson(a_sdc, a_nv)
    lo_b, p_b, hi_b = wilson(b_sdc, b_nv)
    print(f"  P_residue numeric={p_a:.4f} [{lo_a:.4f},{hi_a:.4f}]")
    print(f"  P_residue both   ={p_b:.4f} [{lo_b:.4f},{hi_b:.4f}]")
    if a_nv and b_nv:
        ratio = (a_sdc/a_nv) / max(1e-12, b_sdc/b_nv) if b_sdc else float('inf')
        print(f"  numeric/compute ratio = {ratio:.2f}  (field [2,8])")
        p = fisher_exact_1sided(a_sdc, a_nv-a_sdc, b_sdc, b_nv-b_sdc)
        print(f"  Fisher exact (1-sided) p = {p:.4g}  (acceptance p<0.05)")
        verdict = "PASS" if p < 0.05 else "FAIL(insufficient n — see formal n=384)"
        print(f"  H-acceptance P(history_residue)>0 Fisher p<0.05: {verdict}")
    else:
        print("  (insufficient data — run both arms)")

if __name__ == "__main__":
    main()
