#!/usr/bin/env python3
"""Backfill W8.2/W8.3/W8.5 event_coverage counting densities.

Reads the per-binary event_density.py JSONs (2 no-fault probe reps each)
and replaces every `_TODO_density` placeholder stanza in the three
preparation yamls with the measured `density:` value. Zero-density cells
KEEP the placeholder (campaign.py's loud exit-1 semantics — never fabricate
a count) and are reported as blocked.

Event-column mapping (north star 02-doc six families; 05-expanded-matrix
事件触发条件 -> event_density.py column):
  D14/D23/D24 误预测恢复/检查点窗口     -> branch_mispred (commit.branchMispredicts)
  D16/D66/D71 RAT表项被覆盖的瞬间       -> rat_writes (rename.renamedOperands = dest renames)
  D18  空闲表剩余≤8                     -> flIntLe8 (probe, threshold==injector 8)
  D75  向量池干涸(≤0)                   -> flVecLe0 (probe run with --probe_fl_vec_le 0)
  D33/D35/D85 ROB占用>80%               -> robOver80 (probe, gate==injector 5*occ>4*cap)
  D36-D39 commit阶段squash              -> squash (commit.commitSquashedInsts)
  D40  ROB槽位被新分派写入覆盖          -> renamed_insts (rename.renamedInsts)
  D49  IQ占用>80%                       -> iqOver80 (probe, gate==injector)
  D54/D91 IQ槽位被新µop写入覆盖         -> renamed_insts
"""
import json
import os
import re
import subprocess
import sys

REPO = "/home/sdc/gem5-fi"
D = os.path.join(REPO, "artifacts/ooo_w8_density")

# binary short name -> workload path
BIN = {
    "branch_mispred": "branch_mispred/branch_mispred",
    "coremark": "coremark/coremark",
    "crc32": "embench/crc32/crc32",
    "matmult_int": "embench/matmult-int/matmult-int",
    "md5sum": "embench/md5sum/md5sum",
    "minver": "embench/minver/minver",
    "nbody": "embench/nbody/nbody",
    "wikisort": "embench/wikisort/wikisort",
    "dep_chain": "dep_chain/dep_chain",
    "dep_chain_vec": "dep_chain/dep_chain_vec",
    "rob_fill": "rob_fill/rob_fill",
    "rob_fill_fp": "rob_fill/rob_fill_fp",
    "gap": "gap/gap",
    "gemm": "polybench/gemm/gemm",
    "lu": "polybench/lu/lu",
    "cholesky": "polybench/cholesky/cholesky",
    "jacobi2d": "polybench/jacobi-2d/jacobi-2d",
    "jpeg_wl": "libjpeg/jpeg_wl",
}

# campaign_id -> (event column, binary short name)
# NOTE dep_chain_vec D75 uses the le0 probe runs (flVecLe0, parsed from raw
# stdout because event_density.py's PROBE_KEYS hardcodes flVecLe6).
CELLS = {
    # ---- w82 Int Rename ----
    "ooo_w82_d14_rat_branch_mispred":  ("branch_mispred", "branch_mispred"),
    "ooo_w82_d16_rat_coremark":        ("rat_writes", "coremark"),
    "ooo_w82_d16_rat_emb_crc32":       ("rat_writes", "crc32"),
    "ooo_w82_d16_rat_emb_matmult":     ("rat_writes", "matmult_int"),
    "ooo_w82_d16_rat_emb_md5sum":      ("rat_writes", "md5sum"),
    "ooo_w82_d16_rat_emb_minver":      ("rat_writes", "minver"),
    "ooo_w82_d16_rat_emb_nbody":       ("rat_writes", "nbody"),
    "ooo_w82_d16_rat_emb_wikisort":    ("rat_writes", "wikisort"),
    "ooo_w82_d18_freelist_dep_chain":  ("flIntLe8", "dep_chain"),
    "ooo_w82_d23_rat_branch_mispred":  ("branch_mispred", "branch_mispred"),
    "ooo_w82_d24_rat_branch_mispred":  ("branch_mispred", "branch_mispred"),
    # ---- w83 Int Dispatch/ROB/IQ ----
    "ooo_w83_d33_rob_rob_fill":        ("robOver80", "rob_fill"),
    "ooo_w83_d35_rob_rob_fill":        ("robOver80", "rob_fill"),
    "ooo_w83_d36_rob_gap":             ("squash", "gap"),
    "ooo_w83_d37_rob_gap":             ("squash", "gap"),
    "ooo_w83_d38_rob_gap":             ("squash", "gap"),
    "ooo_w83_d39_rob_gap":             ("squash", "gap"),
    "ooo_w83_d40_rob_coremark":        ("renamed_insts", "coremark"),
    "ooo_w83_d40_rob_emb_crc32":       ("renamed_insts", "crc32"),
    "ooo_w83_d40_rob_emb_matmult":     ("renamed_insts", "matmult_int"),
    "ooo_w83_d40_rob_emb_md5sum":      ("renamed_insts", "md5sum"),
    "ooo_w83_d40_rob_emb_minver":      ("renamed_insts", "minver"),
    "ooo_w83_d40_rob_emb_nbody":       ("renamed_insts", "nbody"),
    "ooo_w83_d40_rob_emb_wikisort":    ("renamed_insts", "wikisort"),
    "ooo_w83_d49_iq_rob_fill":         ("iqOver80", "rob_fill"),
    "ooo_w83_d54_iq_coremark":         ("renamed_insts", "coremark"),
    "ooo_w83_d54_iq_emb_crc32":        ("renamed_insts", "crc32"),
    "ooo_w83_d54_iq_emb_matmult":      ("renamed_insts", "matmult_int"),
    "ooo_w83_d54_iq_emb_md5sum":       ("renamed_insts", "md5sum"),
    "ooo_w83_d54_iq_emb_minver":       ("renamed_insts", "minver"),
    "ooo_w83_d54_iq_emb_nbody":        ("renamed_insts", "nbody"),
    "ooo_w83_d54_iq_emb_wikisort":     ("renamed_insts", "wikisort"),
    # ---- w85 FP/SIMD ----
    "ooo_w85_d66_rat_emb_nbody":       ("rat_writes", "nbody"),
    "ooo_w85_d66_rat_emb_minver":      ("rat_writes", "minver"),
    "ooo_w85_d71_rat_pb_gemm":         ("rat_writes", "gemm"),
    "ooo_w85_d71_rat_pb_lu":           ("rat_writes", "lu"),
    "ooo_w85_d71_rat_pb_cholesky":     ("rat_writes", "cholesky"),
    "ooo_w85_d71_rat_pb_jacobi2d":     ("rat_writes", "jacobi2d"),
    "ooo_w85_d71_rat_jpeg":            ("rat_writes", "jpeg_wl"),
    "ooo_w85_d75_freelist_dep_chain_vec": ("flVecLe0", "dep_chain_vec_le0"),
    "ooo_w85_d85_rob_rob_fill_fp":     ("robOver80", "rob_fill_fp"),
    "ooo_w85_d91_iq_pb_gemm":          ("renamed_insts", "gemm"),
    "ooo_w85_d91_iq_pb_lu":            ("renamed_insts", "lu"),
    "ooo_w85_d91_iq_pb_cholesky":      ("renamed_insts", "cholesky"),
    "ooo_w85_d91_iq_pb_jacobi2d":      ("renamed_insts", "jacobi2d"),
    "ooo_w85_d91_iq_jpeg":             ("renamed_insts", "jpeg_wl"),
}

YAMLS = [
    "campaigns/ooo-w82-int-rename.yaml",
    "campaigns/ooo-w83-int-dispatch-rob.yaml",
    "campaigns/ooo-w85-fpsimd.yaml",
]


def run_event_density(b):
    """Produce <b>.json via tools/event_density.py over the 2 reps."""
    out_json = os.path.join(D, b + ".json")
    runs = [os.path.join(D, b + "_r1"), os.path.join(D, b + "_r2")]
    stdouts = [r + ".out" for r in runs]
    for p in runs:
        if not os.path.isfile(os.path.join(p, "stats.txt")):
            sys.exit("missing stats.txt for %s" % p)
    cmd = [sys.executable, os.path.join(REPO, "tools/event_density.py"),
           "--runs"] + runs + ["--stdout"] + stdouts + ["--json", out_json]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("event_density.py failed for %s:\n%s\n%s" %
                 (b, r.stdout, r.stderr))
    with open(out_json) as f:
        data = json.load(f)
    return data, r.stdout


def parse_le0():
    """flVecLe0 counts from the raw CHAOS_PROBE lines of the le0 runs."""
    vals = []
    for rep in ("r1", "r2"):
        path = os.path.join(D, "dep_chain_vec_le0_" + rep + ".out")
        with open(path) as f:
            hits = [ln for ln in f if "CHAOS_PROBE" in ln]
        if len(hits) != 1:
            sys.exit("%s: expected exactly one CHAOS_PROBE line, got %d"
                     % (path, len(hits)))
        m = re.search(r"flVecLe0=(\d+)", hits[0])
        if not m:
            sys.exit("%s: no flVecLe0= in CHAOS_PROBE line" % path)
        vals.append(int(m.group(1)))
    return vals


def fmt_density(vals):
    """Mean density; int when the reps agree exactly (deterministic)."""
    if vals[0] == vals[1]:
        return str(vals[0]), vals[0] == vals[1]
    mean = sum(vals) / 2.0
    s = ("%d" % mean) if float(mean).is_integer() else ("%.1f" % mean)
    return s, False


def main():
    # 1) per-binary event_density.py products
    means = {}
    determinism = {}
    for b in BIN:
        data, _ = run_event_density(b)
        means[b] = data["aggregate"]["mean"]
        # determinism check: compare per-run values for every column
        runs = data["runs"]
        cols = list(runs[0]["stats"].keys())
        diffs = [c for c in cols if runs[0]["stats"][c] != runs[1]["stats"][c]]
        p0, p1 = runs[0]["probe"], runs[1]["probe"]
        if p0 and p1:
            diffs += ["probe:" + k for k in p0
                      if p0[k] != p1.get(k)]
        determinism[b] = diffs
    # 2) D75 le0 counts (raw parse)
    le0_vals = parse_le0()

    # 3) resolve per-cell density values
    cell_density = {}
    cell_blocked = {}
    for cid, (col, b) in CELLS.items():
        if col == "flVecLe0":
            vals = le0_vals
        else:
            if col not in means[b]:
                sys.exit("column %s missing for %s" % (col, b))
            runs_json = json.load(open(os.path.join(D, b + ".json")))["runs"]
            if col in ("robOver80", "iqOver80", "flIntLe8", "flFloatLe12",
                       "flVecLe6"):
                vals = [r["probe"][col] for r in runs_json]
            else:
                vals = [r["stats"][col] for r in runs_json]
        s, det = fmt_density(vals)
        if float(vals[0]) <= 0 and float(vals[1]) <= 0:
            cell_blocked[cid] = (col, b, vals)
        else:
            cell_density[cid] = (s, col, b, det, vals)

    # 4) rewrite the yamls (text-level: replace the 3-line _TODO_density
    #    scalar with density + provenance comment)
    todo_re = re.compile(
        r"    _TODO_density: 'W8\.1 后核实[^\n]*\n"
        r"      \(or density_table\+event\)\.[^\n]*\n"
        r"      fabricate a count\.'\n")
    report = {"filled": {}, "blocked": {}, "kept_todo": []}
    for rel in YAMLS:
        path = os.path.join(REPO, rel)
        with open(path) as f:
            text = f.read()
        # walk stanzas: current campaign_id
        out_lines = []
        cur_cid = None
        lines = text.split("\n")
        i = 0
        n_filled = 0
        while i < len(lines):
            ln = lines[i]
            m = re.match(r"- campaign_id: (\S+)", ln)
            if m:
                cur_cid = m.group(1)
            if "_TODO_density:" in ln:
                # consume the 3-line scalar
                j = i
                while not lines[j].rstrip().endswith(".'"):
                    j += 1
                if cur_cid in cell_density:
                    s, col, b, det, vals = cell_density[cur_cid]
                    det_note = ("r1==r2 exact" if det
                                else "r1=%s r2=%s mean" % (vals[0], vals[1]))
                    out_lines.append(
                        "    # density: events/run, no-fault probe baseline "
                        "(event=%s @ %s, %s);" % (col, b, det_note))
                    out_lines.append(
                        "    # provenance: artifacts/ooo_w8_density/%s.json "
                        "(tools/event_density.py, 2 reps)" % b)
                    out_lines.append("    density: %s" % s)
                    report["filled"][cur_cid] = s
                    n_filled += 1
                else:
                    col, b, vals = cell_blocked[cur_cid]
                    out_lines.append(
                        "    # DENSITY MEASURED ZERO (event=%s @ %s: r1=%s "
                        "r2=%s) — event coverage UNREACHABLE on this binary;"
                        " keep the loud placeholder until a probe workload "
                        "or re-scope lands (02-doc: 换自设探针负载, not "
                        "brute-force)." % (col, b, vals[0], vals[1]))
                    out_lines.append(lines[i:j + 1][0])
                    for k in range(i + 1, j + 1):
                        out_lines.append(lines[k])
                    report["kept_todo"].append((cur_cid, col, b, vals))
                i = j + 1
                continue
            out_lines.append(ln)
            i += 1
        with open(path, "w") as f:
            f.write("\n".join(out_lines))
        print("%s: filled %d stanzas" % (rel, n_filled))

    # 5) determinism anomalies
    for b, diffs in determinism.items():
        if diffs:
            print("DETERMINISM-ANOMALY %s: %s" % (b, diffs))
    print("filled=%d blocked=%d" % (len(report["filled"]),
                                    len(report["kept_todo"])))
    with open(os.path.join(D, "backfill_result.json"), "w") as f:
        json.dump({"filled": report["filled"],
                   "blocked": [list(x) for x in report["kept_todo"]]},
                  f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
