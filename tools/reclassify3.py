#!/usr/bin/env python3
"""SDC process-reclassification (three-class framework), 2026-09-11.

Re-aggregates every completed campaign (runs/<campaign>/c*/results.jsonl) into
the three-class framework:
  C1 无影响 (no impact)                = Masked / N_valid
  C2 过程中被检出 (detected in-flight) = (Corrected + DetectedContained) / N_valid
  C3 未检出但有问题 (undetected, bad)  = (SDC + Crash + Hang) / N_valid
     3a silent-wrong  = SDC / N_valid
     3b crash-exposed = Crash / N_valid
     3c hang-exposed  = Hang / N_valid
Tool artifacts (SimulatorError) excluded from C1/C2/C3; reported separately:
  validity = N_valid / (N_total - N_inactive);  artifact_rate = 1 - validity
N_valid = N_total - N_inactive - N_simulator_error (existing definition, unchanged).

Every cell key = (unit, fault_model, sub-mode axes, workload golden_id, protection,
platform). All numbers traceable to runs/<campaign>/c*/results.jsonl (the campaign
column records the source)."""
import json, os, sys, glob, yaml
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
RUNS = os.path.join(REPO, "runs")

# campaign -> unit (uses ras_escape_analysis's mapping + extensions)
CAMP_UNIT = {
    "prf_formal_cholesky": "physreg", "prf_regchain_pilot": "physreg",
    "prf_bitseg_pilot": "physreg", "prf_bitseg_boundary": "physreg",
    "prf_abiclass_pilot": "physreg", "prf_ptrchase_pilot": "physreg",
    "prf_ptrchase_phys_pilot": "physreg", "pilot_physreg_x3": "physreg",
    "prf_h2_window_pilot": "physreg", "prf_h2_trigger_scan": "physreg",
    "prf_h2_trigger_scan_80k": "physreg", "p15_h2_repro": "physreg", "p15_h2_fc_scan": "physreg",
    "pwf_v12_prf_x3_formal": "physreg",
    "rat_formal_cholesky": "rat", "rat_cholesky_pilot": "rat",
    "rat_f5_formal_cholesky": "rat",
    "freelist_formal_cholesky": "freelist",
    "rob_formal_cholesky": "rob", "rob_cholesky_pilot": "rob",
    "iq_formal_cholesky": "iq", "iq_cholesky_pilot": "iq",
    "iq_f5f6_pilot": "iq", "iq_f5_formal_madd": "iq",
    "iq_f6_phase_curve": "iq", "iq_f6_phase_curve_cholesky": "iq",
    "exec_formal_cholesky": "exec", "exec_formal_regchain": "exec",
    "exec_regchain_pilot": "exec",
    "fpu_formal_gemm": "fsu", "fpu_formal_neon": "fsu", "fpu_neon_pilot": "fsu",
    "lsqfwd_formal_fwd": "lsq_fwd", "lsqfwd_fwd_pilot": "lsq_fwd",
    "lsqfwd_regchain_pilot": "lsq_fwd",
    "fwdsrc_formal_fwd": "lsq_fwd",
    "fwdphase_curve_1": "lsq_fwd", "fwdphase_curve_2": "lsq_fwd",
    "fwdphase_curve_4": "lsq_fwd", "fwdphase_curve_8": "lsq_fwd",
    "l1d_formal_reduce": "l1d", "l1d_formal_reduce_secded": "l1d",
    "l1d_reduce_pilot": "l1d",
    "l1dfwd_formal_reduce": "l1d_fwd",
    "l1i_formal_loop": "l1i",
    "l2_formal_reduce": "l2",
    "mem_formal_cholesky": "memory", "mem_regchain_pilot": "memory",
    "addrmap_formal_fwd": "memory",
    "decode_formal": "decode", "decode_regchain_pilot": "decode",
    "bpu_formal": "bpu", "bpu_formal_regchain": "bpu",
    "bpu_branchy_pilot": "bpu",
    "ras_formal_cholesky": "ras", "ras_regchain_pilot": "ras",
    "exmon_formal_spinlock": "exmon", "exmon_spinlock_pilot": "exmon",
    "specleak_branchy_pilot": "rat", "specleak_formal_branchy": "rat",
    "specleak_formal_x19": "rat",
    "tlbf5_pilot": "l1_tlb", "tlbf5_formal_fs": "l1_tlb",
    "sysreg_f5_pilot": "sysreg",
    "ptw_h7_pilot_fs": "ptw",
    # v1.1+ rounds
    "p81_campaign_smoke": "l1d_fwd", "p82_legacy_smoke": "fsu",
    "p82_uniform_smoke": "fsu", "p84_recurring_smoke": "fsu",
    "pwf_v11_fpu_pilot": "fsu", "pwf_v11_fpu_modes_pilot": "fsu",
    "pwf_v11_fpu_fmaw_rec_pilot": "fsu", "pwf_v11_fpu_recurring_pilot": "fsu",
    "pwf_v11_fpu_svd_formal": "fsu",
    "pwf_v11_rob_specleak_pilot": "rat", "pwf_v11_rob_specleak_formal": "rat",
    "pwf_v11_rob_specleak_depth": "rat",
    "pwf_v11_l2_pilot": "l2", "pwf_v11_l2_formal": "l2",
    "pwf_v11_l2_size_sweep": "l2",
    "pwf_v11_dram_pilot": "memory", "pwf_v11_dram_formal": "memory",
    "pwf_v11_dram_addrmap_pilot": "memory",
    "p12_setB_fpu": "fsu", "p12_setB_specleak": "rat",
    "p12_setB_l2": "l2", "p12_setB_dram": "memory",
    "p17_repro_fpu_svd": "fsu", "p17_repro_specleak": "rat",
    "p17_repro_l2": "l2",
    "pwf_v12_exec_pilot": "exec", "pwf_v12_exec_chol_pilot": "exec",
    "pwf_v12_exec_formal": "exec", "pwf_v12_exec_chol_formal": "exec",
    "pwf_v12_exec_c2_formal": "exec",
    "pwf_v12_iq_pilot": "iq", "pwf_v12_iq_omit_pilot": "iq",
    "pwf_v12_iq_formal": "iq",
    "pwf_v12_l2_arms_pilot": "l2", "pwf_v12_l2_arms_formal": "l2",
    "pwf_v12_l2_victim_pilot": "l2",
    "pwf_v12_dram_ecc_pilot": "memory",
    "pwf_v12_dram_ecclogic_pilot": "memory",
    "pwf_v13_dram_ecclogic_formal": "memory",
    "pwf_v12_l1i_fields_pilot": "l1i", "pwf_v13_l1i_formal": "l1i",
    "pwf_v12_bpu_target_pilot": "bpu", "pwf_v12_bpu_ras_pilot": "bpu",
    "pwf_v13_bpu_formal": "bpu",
    "pwf_v12_specleak_x10_formal": "rat",
    "pwf_v12_specleak_x10_c2_formal": "rat",
    "pwf_v13_fpu_svd_c2_formal": "fsu",
    "pwf_v13_dram_c2_formal": "memory",
    "pwf_v13_exec_c2_formal": "exec",
    "pwf_v13_exec_chol_formal": "exec",
    "pwf_v13_l3_paired_pilot": "l3",
    "pwf_v13_lane_pilot": "physreg",
}

CLASSES = ("Masked", "SDC", "Crash", "Hang", "Inactive", "SimulatorError",
           "Corrected", "DetectedContained")

def cell_axes(m):
    """Extract the sub-mode / platform axes from a manifest dict."""
    f = m.get("fault", {})
    t = m.get("target", {})
    ax = []
    fm = f.get("fpu_mode") or {}
    if fm.get("bitseg"): ax.append(f"bitseg={fm['bitseg']}")
    if fm.get("fma_weighted"): ax.append("fma_weighted")
    if fm.get("recurring_stuck"): ax.append("recurring")
    if fm.get("rounding_sub"): ax.append("rounding_sub")
    if fm.get("f3_dependent"): ax.append("f3")
    if fm.get("fpsr_suppress"): ax.append("fpsr")
    em = f.get("exec_mode") or {}
    if em.get("bitseg"): ax.append(f"exec_bitseg={em['bitseg']}")
    if em.get("recurring_stuck"): ax.append("exec_recurring")
    if f.get("l1i_field"): ax.append(f"l1i_field={f['l1i_field']}")
    if f.get("target_field"): ax.append(f"field={f['target_field']}")
    if f.get("victim_fault"): ax.append("victim")
    if f.get("paired"): ax.append("paired")
    if f.get("ecc_logic_fault"): ax.append("ecc_logic_fault")
    if f.get("addr_window"): ax.append("addrwin")
    if t.get("index") is not None: ax.append(f"idx={t['index']}")
    return ",".join(ax)

def main():
    rows = []
    campaigns = sorted(set(os.path.basename(p) for p in
                           glob.glob(os.path.join(RUNS, "*", "c*", "results.jsonl"))
                           for p in [os.path.dirname(os.path.dirname(p))])
    ) if False else sorted({os.path.relpath(os.path.dirname(os.path.dirname(p)), RUNS)
              for p in glob.glob(os.path.join(RUNS, "*", "c*", "results.jsonl"))})
    for camp in campaigns:
        unit = CAMP_UNIT.get(camp)
        if unit is None:
            print(f"WARN unmapped campaign: {camp}", file=sys.stderr)
            unit = "?" + camp
        for cdir in sorted(glob.glob(os.path.join(RUNS, camp, "c*"))):
            rj = os.path.join(cdir, "results.jsonl")
            if not os.path.exists(rj): continue
            # read one manifest for cell-level axes
            mans = sorted(glob.glob(os.path.join(cdir, "*.yaml")))
            ax, model, gid, prot, plat = "", "?", "?", "none", "?"
            if mans:
                m = yaml.safe_load(open(mans[0]))
                model = m["fault"]["model"]
                gid = m.get("oracle", {}).get("golden_id", "?")
                prot = m["fault"].get("protection_model", "none")
                plat = m.get("platform", {}).get("config_family", "?")
                # ptw ecc arm
                if unit == "ptw" or camp == "ptw_h7_pilot_fs":
                    pass  # ptw campaigns ran outside runner (shell scripts) — no manifests
                ax = cell_axes(m)
            counts = defaultdict(int)
            for line in open(rj):
                r = json.loads(line)
                cls = r["classification"]
                # v1.4 reclassification fix: exit in {1,2} + faults=0 = gem5 python config
                # error (e.g. the madd_chain vs madd_chain_kernel binary-name bug that
                # invalidated iq_f5f6_pilot / iq_f5_formal_madd / iq_f6_phase_curve) — the
                # 2026-09-04-era classifier labeled these Crash; they are SimulatorError.
                if (cls == "Crash" and r.get("exit") in (1, 2)
                        and (r.get("faults_injected") or 0) == 0):
                    cls = "SimulatorError"
                counts[cls] += 1
            n_total = sum(counts.values())
            rows.append(dict(campaign=camp, cell=os.path.basename(cdir), unit=unit,
                             model=model, axes=ax, workload=gid, prot=prot, plat=plat,
                             n_total=n_total, **{c: counts.get(c, 0) for c in CLASSES}))
    out = os.path.join(REPO, "artifacts", "meta", "reclass3_cells.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rows, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"{len(rows)} cells from {len(campaigns)} campaigns -> {out}")

if __name__ == "__main__":
    main()
