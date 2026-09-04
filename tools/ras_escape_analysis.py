#!/usr/bin/env python3
"""§4.1 SDC escape-set decomposition + §2.18 RAS meta-analysis.

Reads all artifacts/<campaign>/heatmap.csv files, aggregates per-unit
P_SDC/P_DUE/Reachability, and classifies each unit's SDC contribution by
escape mechanism (doc §4.1 A-F):
  A. RAS-out-of-scope structures (PRF/RAT/ROB/IQ/store buffer/L1 TLB/
     L2 victim) -> raw = escape
  B. SED-only structures (L1I data proxy) >=2-bit
  C. >=3-bit (beyond SECDED)
  D. post-check escape (ECC-check-later datapath, e.g. L1DForward)
  E. ECC logic itself faulty (ecc_logic_fault)
  F. poison propagation lost

Outputs:
  artifacts/meta/escape_decomposition.md — the §4.1 pie-chart data table
  artifacts/meta/protection_roi.md — the §4.2 unit-priority table

Usage: python3 tools/ras_escape_analysis.py
"""
import csv, os, sys, glob
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ART = os.path.join(REPO, "artifacts")

# §4.1 escape mechanism per unit (design doc). protectionModel column of the
# heatmap tells whether the run was raw (none) or protection-aware.
ESCAPE_MECHANISM = {
    # A: RAS-out-of-scope (no protection on these structures in the proxy)
    "physreg": "A (RAS-out-of-scope: PRF unprotected, raw=escape)",
    "rat":     "A (RAS-out-of-scope: RAT unprotected, raw=escape)",
    "freelist":"A (RAS-out-of-scope: freelist unprotected)",
    "rob":     "A (RAS-out-of-scope: ROB unprotected)",
    "iq":      "A (RAS-out-of-scope: IQ unprotected)",
    "exec":    "A (RAS-out-of-scope: int-ALU unprotected)",
    "fsu":     "A (RAS-out-of-scope: FSU unprotected)",
    "lsq_fwd": "A (RAS-out-of-scope: store-buffer path)",
    "bpu":     "A (RAS-out-of-scope: predictor state, squash-recovers)",
    "decode":  "A (RAS-out-of-scope: decode latch)",
    "memory":  "E (DRAM backing store; secded via CHAOSMem protectionModel)",
    "l1d":     "D (post-check escape via CHAOSL1DForward; cache raw vs secded_poison)",
    "l1d_fwd": "D (post-check escape: ECC-check-later datapath)",
    "l1_tlb":  "A (L1 TLB flop, no protection per TRM proxy)",
    "l3":      "C (>=3-bit beyond SECDED; CHI msg stream)",
    "noc":     "C (NoC flit, no CRC in proxy)",
    "ras":     "F (RAS mechanism escape: exc_suppress swallows DUE)",
    "exmon":   "A (RAS-out-of-scope: exclusive monitor state)",
}

# campaign-name -> unit aliases (campaigns named by doc-section or workload)
CAMPAIGN_UNIT = {
    "prf_formal": "physreg", "prf_regchain": "physreg", "pilot_physreg": "physreg",
    "example-prf": "physreg",
    "lsqfwd_formal": "lsq_fwd", "lsqfwd_fwd": "lsq_fwd", "lsqfwd_regchain": "lsq_fwd",
    "exmon_spinlock": "exmon",
    "fpu_neon": "fsu", "fpu_formal": "fsu",
    "mem_regchain": "memory", "mem_formal": "memory",
    "l1d_reduce": "l1d", "l1d_formal": "l1d",
    "exec_formal": "exec", "exec_regchain": "exec",
    "iq_formal": "iq", "iq_cholesky": "iq",
    "rob_formal": "rob", "rob_cholesky": "rob",
    "rat_formal": "rat", "rat_cholesky": "rat",
    "ras_regchain": "ras",
    "bpu_branchy": "bpu",
    "decode_regchain": "decode",
}

def unit_of(campaign):
    # direct alias hit first (longest prefix match)
    for name, unit in sorted(CAMPAIGN_UNIT.items(), key=lambda x: -len(x[0])):
        if campaign.startswith(name):
            return unit
    for key in ESCAPE_MECHANISM:
        if key in campaign:
            return key
    return ""

def main():
    rows = []
    for hf in sorted(glob.glob(os.path.join(ART, "*", "heatmap.csv"))):
        campaign = os.path.basename(os.path.dirname(hf))
        with open(hf) as f:
            for r in csv.DictReader(f):
                r["_campaign"] = campaign
                rows.append(r)
    if not rows:
        sys.exit("no artifacts/*/heatmap.csv found — run campaigns first")

    # §4.1 decomposition table
    lines = ["# §4.1 SDC Escape-Set Decomposition (from formal heatmaps)", "",
             "| unit (campaign/cell) | protection | P_SDC [CI] | P_DUE [CI] | Reach | escape mechanism |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        comp = r.get("phys_mode", "")  # grid axes vary; use the row as-is
        p_sdc = f"{float(r['P_SDC'])*100:.1f}% [{float(r['P_SDC_lo'])*100:.1f},{float(r['P_SDC_hi'])*100:.1f}]"
        p_due = f"{float(r['P_DUE'])*100:.1f}% [{float(r['P_DUE_lo'])*100:.1f},{float(r['P_DUE_hi'])*100:.1f}]"
        reach = f"{float(r['Reach'])*100:.1f}%"
        # identify the unit from the campaign name
        unit = ""
        for key in ESCAPE_MECHANISM:
            # match campaign name OR known campaign-name -> unit aliases
            if key in r["_campaign"]:
                unit = key; break
        mech = ESCAPE_MECHANISM.get(unit, "? (unit not in map)")
        prot = r.get("protection_model", "none")
        cell_desc = " ".join(f"{k}={v}" for k, v in r.items()
                              if k not in ("_campaign","n_total","n_valid","n_inactive",
                                           "n_simerror","P_SDC","P_SDC_lo","P_SDC_hi",
                                           "P_DUE","P_DUE_lo","P_DUE_hi","Reach",
                                           "Reach_lo","Reach_hi","frozen","protection_model"))
        lines.append(f"| {r['_campaign']}<br>{cell_desc} | {prot} | {p_sdc} | {p_due} | {reach} | {mech} |")

    # §4.2 protection-ROI priority table (sorted by P_SDC contribution)
    lines += ["", "# §4.2 Protection Investment Priority (sorted by P_SDC × Reach)", "",
              "| unit | P_SDC | Reach | SDC contribution proxy | current protection (proxy) | priority |",
              "|---|---|---|---|---|---|"]
    unit_best = {}
    for r in rows:
        unit = ""
        for key in ESCAPE_MECHANISM:
            # match campaign name OR known campaign-name -> unit aliases
            if key in r["_campaign"]:
                unit = key; break
        if not unit:
            continue
        contrib = float(r["P_SDC"]) * float(r["Reach"])
        if unit not in unit_best or contrib > unit_best[unit][0]:
            unit_best[unit] = (contrib, float(r["P_SDC"]), float(r["Reach"]),
                               r.get("protection_model", "none"))
    for unit, (contrib, psdc, reach, prot) in sorted(unit_best.items(),
                                                       key=lambda x: -x[1][0]):
        prio = "HIGH" if contrib > 0.02 else ("MED" if contrib > 0.005 else "LOW")
        lines.append(f"| {unit} | {psdc*100:.1f}% | {reach*100:.1f}% | {contrib*100:.2f}% | {prot} | {prio} |")

    os.makedirs(os.path.join(ART, "meta"), exist_ok=True)
    out = os.path.join(ART, "meta", "escape_decomposition.md")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {out} ({len(rows)} cells from {len(set(r['_campaign'] for r in rows))} campaigns)")

if __name__ == "__main__":
    main()
