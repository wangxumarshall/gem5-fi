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
    # v1.1 Phase 9-12 campaigns (the corrected-artifact round).
    "pwf_v11_fpu_pilot": "fsu", "pwf_v11_fpu_modes_pilot": "fsu",
    "pwf_v11_fpu_fmaw_rec_pilot": "fsu", "pwf_v11_fpu_recurring_pilot": "fsu",
    "p12_setB_fpu": "fsu",
    "pwf_v11_rob_specleak_pilot": "rat",   # spec_leak lives in CHAOSRenameMap
    "p12_setB_specleak": "rat",
    "pwf_v11_l2_pilot": "l2", "p12_setB_l2": "l2",
    "pwf_v11_dram_pilot": "memory", "p12_setB_dram": "memory",
    # v1.2/v1.3 rounds.
    "pwf_v11_fpu_svd_formal": "fsu",
    "pwf_v11_rob_specleak_formal": "rat", "pwf_v11_rob_specleak_depth": "rat",
    "pwf_v11_l2_formal": "l2", "pwf_v11_dram_formal": "memory",
    "pwf_v11_dram_addrmap_pilot": "memory",
    "pwf_v11_l2_size_sweep": "l2",
    "pwf_v12_exec_pilot": "exec", "pwf_v12_exec_chol_pilot": "exec",
    "pwf_v12_exec_formal": "exec",
    "pwf_v12_exec_chol_formal": "exec", "pwf_v12_exec_c2_formal": "exec",
    "pwf_v12_iq_pilot": "iq", "pwf_v12_iq_omit_pilot": "iq",
    "pwf_v12_iq_formal": "iq",
    "pwf_v12_l2_arms_pilot": "l2", "pwf_v12_l2_arms_formal": "l2",
    "pwf_v12_l2_victim_pilot": "l2",
    "pwf_v12_dram_ecc_pilot": "memory", "pwf_v12_dram_ecclogic_pilot": "memory",
    "pwf_v13_dram_ecclogic_formal": "memory",
    "pwf_v12_l1i_fields_pilot": "l1i", "pwf_v13_l1i_formal": "l1i",
    "pwf_v12_bpu_target_pilot": "bpu", "pwf_v12_bpu_ras_pilot": "bpu",
    "pwf_v13_bpu_formal": "bpu",
    "pwf_v12_prf_x3_formal": "physreg",
    "pwf_v12_specleak_x10_formal": "rat", "pwf_v12_specleak_x10_c2_formal": "rat",
    "p15_h2_repro": "physreg",
    "p17_repro_fpu_svd": "fsu", "p17_repro_specleak": "rat", "p17_repro_l2": "l2",
    "pwf_v13_fpu_svd_c2_formal": "fsu", "pwf_v13_dram_c2_formal": "memory",
    "mem_regchain": "memory", "mem_formal": "memory",
    "l1d_reduce": "l1d", "l1d_formal": "l1d",
    "exec_formal": "exec", "exec_regchain": "exec",
    "iq_formal": "iq", "iq_cholesky": "iq",
    "iq_f5": "iq", "iq_f6": "iq", "iq_f5f6": "iq",
    "rob_formal": "rob", "rob_cholesky": "rob",
    "rat_formal": "rat", "rat_cholesky": "rat",
    "rat_f5": "rat",
    "freelist_formal": "freelist",
    "specleak": "rat",          # §2.3 spec_leak lives in the rename rollback path
    "fwdsrc": "lsq_fwd",        # §2.4 fwd_source_sub (F5 wrong-source forward)
    "addrmap": "memory",        # §2.17 addr_map_sub (F5 displaced write)
    "exmon_formal": "exmon",
    "prf_h2": "physreg", "prf_bitseg": "physreg", "prf_abiclass": "physreg",
    "ras_regchain": "ras", "ras_formal": "ras",
    "bpu_branchy": "bpu", "bpu_formal": "bpu",
    "decode_regchain": "decode", "decode_formal": "decode",
    "l1dfwd": "l1d_fwd",
    "fpu_formal_gemm": "fsu",
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

# §4.2 weight(unit) — occupancy-based (Phase 6.1). Single source: a no-injection
# C2/cholesky golden run's stats.txt (artifacts/meta/occupancy_cholesky_C2.stats).
# Weights are RELATIVE structure-occupancy proxies per unit, normalized to
# sum=1 over the units in the table. E3-honest: gem5 classic-config occupancy
# stats differ per workload; this weights the C2/cholesky family (the biggest
# formal cluster). Units without a measurable occupancy proxy get the mean.
OCCUPANCY_STATS = os.path.join(ART, "meta", "occupancy_cholesky_C2.stats")

def _stat(stats_path, pattern):
    """First matching 'name  value' line's value as float, or None."""
    try:
        with open(stats_path) as f:
            for line in f:
                if pattern in line and not line.strip().startswith("#"):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            return float(parts[1])
                        except ValueError:
                            continue
    except OSError:
        pass
    return None

def _stat_pct(stats_path, pattern):
    """The '%'-column value (parts[2], e.g. '44.17%') of the first matching
    stats row, as a 0..1 fraction. gem5 distribution rows are
    '<name> <count> <pct>% <cumulative>% # ...' — the count is in CYCLES,
    the pct column is the comparable fraction."""
    try:
        with open(stats_path) as f:
            for line in f:
                if pattern in line and "%" in line:
                    parts = line.split()
                    for tok in parts[1:4]:
                        if tok.endswith("%"):
                            try:
                                return float(tok[:-1]) / 100.0
                            except ValueError:
                                continue
    except OSError:
        pass
    return None

def weight_table():
    """unit -> relative occupancy weight (sums to 1 over measured units)."""
    raw = {
        # L1D/L1I/L2: average tag occupancy (fraction of ways occupied)
        "l1d": _stat(OCCUPANCY_STATS, "l1d-cache-0.tags.avgOccs::total"),
        "l1i": _stat(OCCUPANCY_STATS, "l1i-cache-0.tags.avgOccs::total"),
        "l2":  _stat(OCCUPANCY_STATS, "l2-cache-0.tags.avgOccs::total"),
        # rename (RAT/freelist live in rename's pipeline activity):
        # share of cycles rename is Running (mapping writes happening).
        # NOTE the stats row is '<name> <count> <pct>%' — _stat's parts[1]
        # is the COUNT; use the percentage column via _stat_pct (a 0..100
        # fraction-of-cycles figure, comparable with avgOccs 0..1).
        "rat": _stat_pct(OCCUPANCY_STATS, "rename.status::Running"),
        "freelist": _stat_pct(OCCUPANCY_STATS, "rename.status::Running"),
        # ROB: commit utilization — committedInsts / cycles (per-cycle occupancy
        # of the ROB's in-flight window; width-normalized to a <=1 fraction)
        # handled below with two stats
        "rob": None,
        # IQ: full-event proxy is an event count, not occupancy; use rename
        # running as the dispatch-into-IQ activity proxy
        "iq": _stat_pct(OCCUPANCY_STATS, "rename.status::Running"),
        # LSQ: the same dispatch proxy (loads/stores pass rename into LSQ)
        "lsq_fwd": _stat_pct(OCCUPANCY_STATS, "rename.status::Running"),
        # exec/fsu: commit-mix of the class (fraction of committed insts)
        "exec": None,  # filled from committedInstType below
        "fsu":  None,
        # PRF: live-physreg fraction proxied by the in-flight window
        # occupancy (filled after the ROB calc below)
        "physreg": None,
        # l1d_fwd (the fill->PRF datapath): L1D tag occupancy proxies the
        # forwarding-relevant state flowing through it
        "l1d_fwd": _stat(OCCUPANCY_STATS, "l1d-cache-0.tags.avgOccs::total"),
    }
    # ROB: committedInsts per cycle / commit width (4) as window-occupancy proxy
    ci = _stat(OCCUPANCY_STATS, "commit.committedInsts")
    # total cycles: rename status percentages denominator — use commit's
    # committedInsts over (Running+Idle+Squashing+Blocked+Unblocking cycles)
    cyc = None
    try:
        vals = []
        with open(OCCUPANCY_STATS) as f:
            for line in f:
                if "rename.status::" in line:
                    vals.append(float(line.split()[1]))
        cyc = sum(vals) if vals else None
    except Exception:
        pass
    if ci is not None and cyc:
        raw["rob"] = min(1.0, ci / cyc / 4.0)
        raw["physreg"] = raw["rob"]  # in-flight window = live-physreg proxy
    # exec/fsu: committed-mix fractions
    tot = _stat(OCCUPANCY_STATS, "commit.committedInstType_0::IntAlu")
    # use the % column is unreliable; approximate from the IntAlu/FloatAdd lines
    ia = _stat(OCCUPANCY_STATS, "commit.committedInstType_0::IntAlu")
    fa = _stat(OCCUPANCY_STATS, "commit.committedInstType_0::FloatAdd")
    if ia is not None:
        raw["exec"] = min(1.0, ia / ci) if ci else None
    if fa is not None and ci:
        raw["fsu"] = min(1.0, fa / ci)
    # unmeasurable units: l1d_fwd (a datapath, not storage), l1_tlb/exmon/
    # bpu/decode/ras/memory — leave None, get the mean of measured ones
    measured = {k: v for k, v in raw.items() if v is not None}
    if not measured:
        return {}
    mean_v = sum(measured.values()) / len(measured)
    for k, v in raw.items():
        if v is None:
            raw[k] = mean_v
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}

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
        # identify the unit from the campaign name (aliases first, then
        # direct key match — unit_of() centralizes this)
        unit = unit_of(r["_campaign"])
        mech = ESCAPE_MECHANISM.get(unit, "? (unit not in map)")
        prot = r.get("protection_model", "none")
        cell_desc = " ".join(f"{k}={v}" for k, v in r.items()
                              if k not in ("_campaign","n_total","n_valid","n_inactive",
                                           "n_simerror","P_SDC","P_SDC_lo","P_SDC_hi",
                                           "P_DUE","P_DUE_lo","P_DUE_hi","Reach",
                                           "Reach_lo","Reach_hi","frozen","protection_model"))
        lines.append(f"| {r['_campaign']}<br>{cell_desc} | {prot} | {p_sdc} | {p_due} | {reach} | {mech} |")

    # §4.2 protection-ROI priority table (sorted by P_SDC contribution)
    weights = weight_table()
    wsrc = "occupancy_cholesky_C2.stats" if weights else "UNAVAILABLE (raw table)"
    lines += ["", f"# §4.2 Protection Investment Priority (P_SDC x Reach, occupancy-weighted; weights: {wsrc})", "",
              "| unit | P_SDC | Reach | SDC contribution | occupancy weight | weighted priority | current protection (proxy) | priority |",
              "|---|---|---|---|---|---|---|---|"]
    # formal-first selection: prefer n>=300 (formal scale) rows; fall back
    # to smaller grids/pilots only for units with no formal cell. Without
    # this, a 5-rep pilot's 100% (CI [35,100]) outranks the n=384 formal's
    # 97.7%/3.9% — the Phase 6.1 audit caught the physreg 100% artifact.
    unit_best = {}
    for r in rows:
        unit = unit_of(r["_campaign"])
        if not unit:
            continue
        n = int(r.get("n_valid", 0) or 0)
        contrib = float(r["P_SDC"]) * float(r["Reach"])
        is_formal = n >= 300
        cur = unit_best.get(unit)
        if cur is None:
            unit_best[unit] = (contrib, float(r["P_SDC"]), float(r["Reach"]),
                               r.get("protection_model", "none"), is_formal)
        else:
            cur_formal = cur[4]
            if (is_formal and not cur_formal) or (is_formal == cur_formal
                                                  and contrib > cur[0]):
                unit_best[unit] = (contrib, float(r["P_SDC"]),
                                   float(r["Reach"]),
                                   r.get("protection_model", "none"),
                                   is_formal)
    for unit, (contrib, psdc, reach, prot, is_f) in sorted(unit_best.items(),
                                                            key=lambda x: -x[1][0]):
        w = weights.get(unit, 0.0)
        weighted = contrib * w
        prio = "HIGH" if weighted > 0.01 else ("MED" if weighted > 0.002 else "LOW")
        lines.append(f"| {unit} | {psdc*100:.1f}% | {reach*100:.1f}% | "
                     f"{contrib*100:.2f}% | {w*100:.1f}% | {weighted*100:.2f}% | "
                     f"{prot} | {prio} |")

    os.makedirs(os.path.join(ART, "meta"), exist_ok=True)
    out = os.path.join(ART, "meta", "escape_decomposition.md")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {out} ({len(rows)} cells from {len(set(r['_campaign'] for r in rows))} campaigns)")

if __name__ == "__main__":
    main()
