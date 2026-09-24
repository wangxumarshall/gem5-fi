#!/usr/bin/env python3
"""W3.3 backfill tool (OoO north star, docs/gem5-fi/ooo/06-implementation-plan.md
§4 W3.3 + §9): aggregate campaign artifacts back into the 7 result columns of
docs/gem5-fi/ooo/05-expanded-matrix.csv (E001-E226 experiment cells).

WHAT IT READS
  --campaign DIR [DIR ...]
    A campaign directory in one of two layouts (auto-detected):
      (a) root layout:  DIR/runs/<cid>/cNNNN/results.jsonl
                        DIR/artifacts/<cid>/heatmap.csv       (cross-check)
      (b) campaign dir: DIR IS runs/<cid> (contains cNNNN/results.jsonl);
                         the heatmap is looked up at ../artifacts/<cid>/.
    Per rep it reads runs/<cid>/cNNNN/results.jsonl lines:
      - classification   (six SE classes: SimulatorError/Inactive/Crash/Hang/
                          SDC/Masked; the three protection classes
                          Corrected/DetectedContained/Latent are counted but
                          map to no rate column -- reported, never hidden)
      - l2 block         (commit_diff five-class result: verdict /
                          primary_class / latency_seq -- in either the direct
                          L2RESULT shape or the W2.3 replay-wrapper shape
                          {.., commit_diff: {...}})
      - l3 block         (fanout.py result; 污染扇出数 = liveness.mean, the
                          committed-instructions window between rewrites of
                          the polluted phys reg -- an UPPER-BOUND proxy for
                          consumer reads, source reads are not traced)
      - stats block      (runner --stats summary; mean IPC is reported per
                          cell, the matrix has no IPC column)
    Per rep it also reads the rep's manifest (the yaml named in the record's
    "manifest" field, same directory) for the D/E mapping.

EXPERIMENT-CELL MAPPING (which E row a rep belongs to)
  Primary source: the manifest's schema-v3 `ooo` extension block (06-plan
  decision A6 -- additive on top of the arm-chaos-fi/v1 manifests that
  tools/campaign.py's manifest_for_cell writes today):
      ooo:
        design_unit_id:      D11            # D01-D91
        experiment_cell_id:  E041           # E001-E226 (authoritative)
        frequency_tier:      F0             # F0|F1|F2|事件触发|F5
        counting_basis:      运行计数        # 运行计数|事件覆盖计数
        phase:               formal         # pilot|formal
  NOTE (honest deviation, 2026-09-24): campaign.py at HEAD does NOT yet write
  this block (W3.1/W3.2 land it). Legacy/toy campaigns are therefore mapped
  ONLY through an explicit --cell-map <cid>[/<cNNNN>]=<E-id> supplied by the
  operator -- the mapping is declared, printed in the report, and never
  guessed. When the block exists, its fields are cross-checked against the
  matrix row (design_unit_id must equal; frequency_tier lenient-matched; and
  counting_basis must equal) -- a mismatch excludes the rep as a wiring bug.

BACKFILL DISCIPLINE (06-plan §9, hard rules)
  - pilot reps NEVER enter the result columns (ooo.phase == "pilot").
  - reps with unknown/missing phase enter only under --allow-unphased.
  - a cell is backfilled only when it has data AND its counting basis is met:
      运行计数   row: n_valid >= --min-n-valid   (default 2000, §1.3)
      事件覆盖计数 row: covered events (sum of faults_injected over included
                    reps) >= --min-events (default 2000) -- the coverage
                    count is recorded in the report.
    n_valid follows tools/wilson.py §1.4: n_total - n_inactive - n_simerror.
  - non-qualifying cells are left EMPTY and listed in the report.
  - cells already carrying values are skipped unless --force.
  - percentages are conditional on n_valid and carry Wilson 95% CI in-cell
    ("p [lo,hi]"); 仿真器断言崩溃占比% is the SimulatorError share of
    n_total (L4 split: simulator assertion crash is NOT an architectural
    outcome, so its denominator is all reps). 潜伏期 = median latency_seq
    (commit sequence number); 污染扇出数 = mean liveness.mean across reps.
    Latency/fanout stay empty when the L2/L3 passes have not produced
    evidence (W8.7 fills them in the second pass) -- n/a, never 0.

USAGE
  python3 tools/backfill_expanded_matrix.py \
      --campaign runs/ooo_d11_f0_coremark \
      --matrix docs/gem5-fi/ooo/05-expanded-matrix.csv --dry-run
  python3 tools/backfill_expanded_matrix.py --campaign . \
      --cell-map w23-toy-smoke-prf/c0000=E001 \
      --allow-unphased --min-n-valid 1 --dry-run

The matrix file is UTF-8 (no BOM) with CRLF line terminators; every byte
outside the 7 result columns is preserved (atomic replace via tempfile +
os.replace). Exit code 1 = bad input (missing dirs, unparseable matrix,
bad --cell-map); an honest "nothing qualified" outcome is exit 0.
"""
import argparse
import csv
import io
import json
import os
import re
import statistics
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from wilson import wilson_ci, ALL_CLASSES  # noqa: E402  (repo's single Wilson impl)

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip install pyyaml  (needed to read per-rep manifests)")

DEFAULT_MATRIX = os.path.join(REPO, "docs", "gem5-fi", "ooo",
                              "05-expanded-matrix.csv")

# The 7 result columns of 05-expanded-matrix.csv (header order, by name).
RESULT_COL_NAMES = [
    "SDC%", "Crash%", "Timeout%", "Masked%", "仿真器断言崩溃占比%",
    "潜伏期（commit序号）", "污染扇出数",
]

# Six classes that occur on the SE OoO track (wilson.py ALL_CLASSES keeps the
# full nine; the protection classes are handled separately below).
SE_CLASSES = ("SimulatorError", "Inactive", "Crash", "Hang", "SDC", "Masked")
PROTECTION_CLASSES = ("Corrected", "DetectedContained", "Latent")

# ooo-block keys this tool understands (06-plan A6 spelling; a couple of
# tolerant aliases are accepted because the block is not yet frozen in
# campaign.py at the time this tool was written).
OOO_KEYS = ("design_unit_id", "experiment_cell_id", "frequency_tier",
            "counting_basis", "phase", "workload")

CELL_DIR_RE = re.compile(r"c\d{4}$")
MAX_UNMAPPED_LISTED = 10  # report stays bounded on a repo-root scan


def die(msg):
    print("[backfill] ERROR: %s" % msg, file=sys.stderr)
    sys.exit(1)


def note(msg):
    print("[backfill] %s" % msg)


# ------------------------------------------------------------------ discovery

def iter_cell_dirs(runs_dir):
    """Campaign cell dirs (cNNNN) under one runs/<cid> dir that actually hold
    a results.jsonl. Sorted by cell ordinal."""
    out = []
    try:
        names = sorted(os.listdir(runs_dir))
    except OSError:
        return out
    for name in names:
        d = os.path.join(runs_dir, name)
        if (CELL_DIR_RE.match(name) and os.path.isdir(d)
                and os.path.isfile(os.path.join(d, "results.jsonl"))):
            out.append(d)
    return out


def discover_campaigns(paths):
    """Resolve --campaign DIR entries to campaign dicts
    {cid, runs_dir, artifacts_dir}. Two layouts (see module docstring)."""
    out, seen = [], set()
    for p in paths:
        ap = os.path.abspath(p)
        if not os.path.isdir(ap):
            die("campaign dir not found: %s" % p)
        runs_root = os.path.join(ap, "runs")
        arts_root = os.path.join(ap, "artifacts")
        if os.path.isdir(runs_root) and os.path.isdir(arts_root):
            found = 0
            for cid in sorted(os.listdir(runs_root)):
                rd = os.path.join(runs_root, cid)
                if not os.path.isdir(rd) or not iter_cell_dirs(rd):
                    continue
                key = os.path.normpath(rd)
                if key in seen:
                    continue
                seen.add(key)
                ad = os.path.join(arts_root, cid)
                out.append({"cid": cid, "runs_dir": rd,
                            "artifacts_dir": ad if os.path.isdir(ad) else None})
                found += 1
            if found == 0:
                die("no campaigns under %s (runs/*/c*/results.jsonl empty)" % ap)
        elif iter_cell_dirs(ap):
            # ap IS a runs/<cid> directory; campaign.py puts the artifacts at
            # <root>/artifacts/<cid> where <root> is the PARENT of runs/
            cid = os.path.basename(os.path.normpath(ap))
            ad = os.path.join(os.path.dirname(os.path.dirname(ap)),
                              "artifacts", cid)
            key = os.path.normpath(ap)
            if key in seen:
                continue
            seen.add(key)
            out.append({"cid": cid, "runs_dir": ap,
                        "artifacts_dir": ad if os.path.isdir(ad) else None})
        else:
            die("not a campaign dir (neither runs/+artifacts/ subdirs nor "
                "c*/results.jsonl inside): %s" % ap)
    if not out:
        die("no campaigns discovered from: %s" % ", ".join(paths))
    return out


# ------------------------------------------------------------------- manifests

def read_ooo_block(manifest_path):
    """The manifest's ooo extension block (A6) as a dict; {} when absent,
    {"_error": ...} when unreadable. Tolerates flat top-level spellings.

    Performance: a repo-root scan touches tens of thousands of legacy v1
    manifests that predate the ooo block. A cheap TEXT prefilter skips the
    yaml parse whenever none of the ooo-block key spellings occur in the
    file -- those keys could not survive yaml parsing into the dict, so {}
    is the exact result the full parse would have produced (not an
    approximation). NOTE: "workload" is deliberately NOT a marker (every v1
    manifest has a workload: block, so it would never skip); the markers are
    the spellings that do not occur in v1/v2 manifests."""
    MARKERS = ("ooo:", "design_unit_id:", "experiment_cell_id:",
               "frequency_tier:", "counting_basis:", "phase:")
    try:
        with open(manifest_path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        return {"_error": "manifest unreadable: %s" % e}
    if not any(m in text for m in MARKERS):
        return {}
    try:
        man = yaml.safe_load(text)
    except yaml.YAMLError as e:
        return {"_error": "manifest unreadable: %s" % e}
    if not isinstance(man, dict):
        return {}
    blk = man.get("ooo")
    if isinstance(blk, dict):
        return {str(k): v for k, v in blk.items()}
    # schema not frozen yet: accept the same keys flat at top level
    return {k: man[k] for k in OOO_KEYS if k in man}


# ------------------------------------------------------------------- results

def read_results(cell_dir):
    """Parse one cNNNN/results.jsonl. Returns (records, n_bad_lines); a bad
    JSON line is counted (never silently dropped) and skipped."""
    recs, bad = [], 0
    with open(os.path.join(cell_dir, "results.jsonl"),
              encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                bad += 1
                continue
            if isinstance(rec, dict):
                recs.append(rec)
            else:
                bad += 1
    return recs, bad


def extract_l2(rec):
    """The commit_diff dict of a rep's l2 block, or None. Handles both the
    direct shape (runner --ctrace-ref: {verdict, primary_class, latency_seq})
    and the W2.3 campaign replay wrapper (commit_diff nested inside)."""
    l2 = rec.get("l2")
    if not isinstance(l2, dict):
        return None
    cd = l2.get("commit_diff")
    if isinstance(cd, dict):
        return cd
    if "verdict" in l2 or "l2_error" in l2:
        return l2
    return None


def extract_fanout(rec):
    """Per-rep contamination fanout = l3.liveness.mean (fanout.py; upper-bound
    proxy). None when the rep has no usable l3 evidence."""
    l3 = rec.get("l3")
    if not isinstance(l3, dict) or "l3_error" in l3:
        return None
    liv = l3.get("liveness")
    if isinstance(liv, dict):
        v = liv.get("mean")
        if isinstance(v, (int, float)):
            return float(v)
    return None


# --------------------------------------------------------------------- matrix

def load_matrix(path):
    """Read 05-expanded-matrix.csv. Returns (header, rows, ridx) where rows
    are plain lists (mutable) and ridx maps ID -> row index."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            raw = f.read()
    except OSError as e:
        die("matrix unreadable: %s (%s)" % (path, e))
    rdr = csv.reader(io.StringIO(raw))
    table = [r for r in rdr if r]
    if len(table) < 2:
        die("matrix has no data rows: %s" % path)
    header, rows = table[0], table[1:]
    need = ["ID", "设计单元ID", "适用频率", "负载", "计数基准"] + RESULT_COL_NAMES
    missing = [c for c in need if c not in header]
    if missing:
        die("matrix header missing expected columns %s: %s" % (missing, path))
    ridx = {}
    for i, r in enumerate(rows):
        ridx[r[header.index("ID")]] = i
    if len(ridx) != len(rows):
        die("matrix ID column has duplicates: %s" % path)
    return header, rows, ridx


def freq_row_matches(tier, row_freq):
    """Lenient 适用频率 match: the matrix carries annotated F1 variants
    ("F1（持续到运行结束）") and event rows ("—（不适用固定间隔）")."""
    tier = str(tier).strip()
    row_freq = str(row_freq).strip()
    if not tier or not row_freq:
        return False
    if tier == row_freq:
        return True
    if tier in ("事件触发", "事件触发条件", "event"):
        return "事件触发" in row_freq or "不适用固定间隔" in row_freq
    return row_freq.startswith(tier)


# ---------------------------------------------------------------- aggregation

def new_agg(e_id):
    return {
        "e_id": e_id, "sources": [],          # (cid, cell, map_source) per rep
        "counts": {c: 0 for c in ALL_CLASSES},
        "unknown_classes": {},                # raw string -> n (bucketed as SimulatorError)
        "n_total": 0, "n_inactive": 0, "n_simerror": 0, "n_valid": 0,
        "latencies": [], "fanouts": [], "ipcs": [],
        "coverage": 0,                        # sum faults_injected (included reps)
        "l2_verdicts": {}, "l2_primary": {}, "n_l2": 0,
    }


def bump(counter, key):
    counter[str(key)] = counter.get(str(key), 0) + 1


def resolve_e_id(ooo, cid, cell, cell_map, header, rows):
    """E-id for one rep: ooo block -> --cell-map -> D x F unique lookup.
    Returns (e_id or None, source, why_not)."""
    e_id = ooo.get("experiment_cell_id")
    if e_id:
        return str(e_id), "ooo-block", None
    if (cid, cell) in cell_map:
        return cell_map[(cid, cell)], "cell-map", None
    if cid in cell_map:
        return cell_map[cid], "cell-map(campaign)", None
    d = ooo.get("design_unit_id")
    tier = ooo.get("frequency_tier")
    if d and tier:
        hi = header.index("设计单元ID")
        hf = header.index("适用频率")
        hl = header.index("负载")
        cands = [r for r in rows if r[hi] == str(d) and freq_row_matches(tier, r[hf])]
        wl = ooo.get("workload")
        if wl:
            cands = [r for r in cands if r[hl] == str(wl)] or cands
        if len(cands) == 1:
            return cands[0][header.index("ID")], "DxF-unique", None
        if len(cands) > 1:
            return None, None, ("ambiguous D x F: %s x %s matches %d matrix "
                                "rows %s (workload not in manifest -- pass "
                                "--cell-map or experiment_cell_id)"
                                % (d, tier, len(cands),
                                   [c[header.index("ID")] for c in cands[:6]]))
        return None, None, ("D x F %s x %s matches no matrix row" % (d, tier))
    return None, None, ("no ooo block in manifest and no --cell-map for "
                        "%s/%s" % (cid, cell))


def consistency_ok(e_id, ooo, header, row):
    """Cross-check the ooo block against its matrix row. Only fields PRESENT
    in the block are checked (legacy manifests declare nothing)."""
    probs = []
    if ooo.get("design_unit_id") and row[header.index("设计单元ID")] != str(ooo["design_unit_id"]):
        probs.append("design_unit_id %s != row %s" % (ooo["design_unit_id"],
                                                      row[header.index("设计单元ID")]))
    if ooo.get("frequency_tier") and not freq_row_matches(ooo["frequency_tier"],
                                                          row[header.index("适用频率")]):
        probs.append("frequency_tier %s !~ row %s" % (ooo["frequency_tier"],
                                                      row[header.index("适用频率")]))
    if (ooo.get("counting_basis")
            and row[header.index("计数基准")] != str(ooo["counting_basis"])):
        probs.append("counting_basis %s != row %s" % (ooo["counting_basis"],
                                                      row[header.index("计数基准")]))
    return probs


def process_campaign_cell(camp, cell_dir, ctx):
    """Read one cNNNN dir; classify/map/include its reps. Returns a dict with
    all-reps counts (for the heatmap cross-check) and updates ctx['aggs']."""
    cid, cell = camp["cid"], os.path.basename(cell_dir)
    recs, n_bad = read_results(cell_dir)
    out = {
        "cid": cid, "cell": cell, "n_reps": len(recs), "n_bad": n_bad,
        "all_counts": {c: 0 for c in ALL_CLASSES},
    }
    unmapped_reps = {}   # why -> rep count (one report line per reason)
    for rec in recs:
        cls = rec.get("classification")
        if cls in out["all_counts"]:
            out["all_counts"][cls] += 1
        else:
            # campaign.py's counter convention: unknown class -> SimulatorError
            out["all_counts"]["SimulatorError"] += 1
            out.setdefault("unknown_raw", {})[str(cls)] = \
                out.get("unknown_raw", {}).get(str(cls), 0) + 1

        mname = rec.get("manifest")
        mpath = os.path.join(cell_dir, str(mname)) if mname else None
        ooo = read_ooo_block(mpath) if (mpath and os.path.isfile(mpath)) else {}

        # ---- phase gate (backfill discipline, hard rules) ----
        phase = str(ooo.get("phase") or "").strip().lower() or None
        if phase == "pilot":
            ctx["n_pilot"] += 1
            continue
        if phase not in ("formal",):
            if not ctx["allow_unphased"]:
                ctx["n_unphased"] += 1
                continue
            phase = "unknown(allowed)"

        # ---- E-cell resolution ----
        e_id, src, why_not = resolve_e_id(ooo, cid, cell, ctx["cell_map"],
                                          ctx["header"], ctx["rows"])
        if e_id is None:
            unmapped_reps[why_not] = unmapped_reps.get(why_not, 0) + 1
            continue
        if e_id not in ctx["ridx"]:
            why = "E-id %s not in matrix" % e_id
            unmapped_reps[why] = unmapped_reps.get(why, 0) + 1
            continue
        row = ctx["rows"][ctx["ridx"][e_id]]
        probs = consistency_ok(e_id, ooo, ctx["header"], row)
        if probs:
            ctx["n_consistency"] += 1
            ctx["consistency_issues"].append((cid, cell, e_id, "; ".join(probs)))
            continue

        # ---- dedup (same manifest counted once even if dirs overlap) ----
        key = (cid, cell, str(mname))
        if key in ctx["seen"]:
            ctx["n_dup"] += 1
            continue
        ctx["seen"].add(key)

        agg = ctx["aggs"].setdefault(e_id, new_agg(e_id))
        agg["sources"].append((cid, cell, src))

        if cls in agg["counts"]:
            agg["counts"][cls] += 1
        else:
            agg["counts"]["SimulatorError"] += 1
            bump(agg["unknown_classes"], cls)
        fi = rec.get("faults_injected")
        if isinstance(fi, int) and fi > 0:
            agg["coverage"] += fi

        cd = extract_l2(rec)
        if cd is not None:
            agg["n_l2"] += 1
            bump(agg["l2_verdicts"], cd.get("verdict"))
            bump(agg["l2_primary"], cd.get("primary_class"))
            ls = cd.get("latency_seq")
            if isinstance(ls, int):
                agg["latencies"].append(ls)
        fo = extract_fanout(rec)
        if fo is not None:
            agg["fanouts"].append(fo)
        st = rec.get("stats")
        if isinstance(st, dict) and isinstance(st.get("ipc"), (int, float)):
            agg["ipcs"].append(float(st["ipc"]))
    for why, n in unmapped_reps.items():
        ctx["unmapped"].append((cid, cell, why, n))
    return out


def finalize_agg(agg):
    """Derived denominators (wilson.py §1.4)."""
    for c in ALL_CLASSES:
        agg["counts"].setdefault(c, 0)
    agg["n_total"] = sum(agg["counts"][c] for c in ALL_CLASSES)
    agg["n_inactive"] = agg["counts"]["Inactive"]
    agg["n_simerror"] = agg["counts"]["SimulatorError"]
    agg["n_valid"] = agg["n_total"] - agg["n_inactive"] - agg["n_simerror"]
    return agg


def pct_ci(k, n):
    """'p [lo,hi]' in percent with Wilson 95% CI; '' when n<=0 (no claim)."""
    if n <= 0:
        return ""
    lo, hi, phat = wilson_ci(k, n)
    return "%.2f [%.2f,%.2f]" % (phat * 100.0, lo * 100.0, hi * 100.0)


def result_values(agg):
    """The 7 result-column strings for one E-cell aggregate."""
    c, n_valid, n_total = agg["counts"], agg["n_valid"], agg["n_total"]
    vals = [
        pct_ci(c["SDC"], n_valid),
        pct_ci(c["Crash"], n_valid),
        pct_ci(c["Hang"], n_valid),
        pct_ci(c["Masked"], n_valid),
        pct_ci(agg["n_simerror"], n_total),
    ]
    if agg["latencies"]:
        vals.append("%g" % statistics.median(agg["latencies"]))
    else:
        vals.append("")
    if agg["fanouts"]:
        vals.append("%.2f" % statistics.mean(agg["fanouts"]))
    else:
        vals.append("")
    return vals


# ----------------------------------------------------------- heatmap crosscheck

def heatmap_crosscheck(camp, cell_infos, note_lines):
    """Compare this tool's all-reps aggregation against campaign.py's own
    heatmap.csv (rows are in cell-ordinal order == cNNNN order). Informational
    WARN on mismatch -- the heatmap can be stale after a resumed campaign."""
    hm = os.path.join(camp["artifacts_dir"] or "", "heatmap.csv")
    if not camp["artifacts_dir"] or not os.path.isfile(hm):
        note_lines.append("  %s: no heatmap.csv (cross-check skipped)"
                          % camp["cid"])
        return
    try:
        with open(hm, encoding="utf-8-sig", newline="") as f:
            table = [r for r in csv.reader(f) if r]
    except OSError as e:
        note_lines.append("  %s: heatmap unreadable (%s)" % (camp["cid"], e))
        return
    if len(table) < 2:
        note_lines.append("  %s: heatmap empty" % camp["cid"])
        return
    hdr, hrows = table[0], table[1:]
    try:
        col = {name: hdr.index(name) for name in
               ("n_total", "n_valid", "P_SDC", "P_DUE")}
    except ValueError:
        note_lines.append("  %s: heatmap lacks expected columns (skipped)"
                          % camp["cid"])
        return
    ok = mism = 0
    for i, info in enumerate(cell_infos):
        if i >= len(hrows):
            note_lines.append("  %s/%s: no heatmap row (cNNNN beyond heatmap)"
                              % (camp["cid"], info["cell"]))
            continue
        hr = hrows[i]
        mine = info["all_counts"]
        my_total = sum(mine[c] for c in ALL_CLASSES)
        my_valid = (my_total - mine["Inactive"] - mine["SimulatorError"])
        my_sdc = mine["SDC"] / my_valid if my_valid else 0.0
        my_due = ((mine["Crash"] + mine["Hang"]) / my_valid) if my_valid else 0.0
        diffs = []
        # heatmap rates are printed with %.4f (4-decimal rounding), so the
        # legitimate diff is up to 5e-5; tolerate 1e-4 to stay clear of the
        # float boundary (a real 0.0312-vs-0.03125 case tripped 5e-5 exactly).
        if int(hr[col["n_total"]]) != my_total:
            diffs.append("n_total %s != %d" % (hr[col["n_total"]], my_total))
        if int(hr[col["n_valid"]]) != my_valid:
            diffs.append("n_valid %s != %d" % (hr[col["n_valid"]], my_valid))
        if abs(float(hr[col["P_SDC"]]) - my_sdc) > 1e-4:
            diffs.append("P_SDC %s != %.4f" % (hr[col["P_SDC"]], my_sdc))
        if abs(float(hr[col["P_DUE"]]) - my_due) > 1e-4:
            diffs.append("P_DUE %s != %.4f" % (hr[col["P_DUE"]], my_due))
        if diffs:
            mism += 1
            note_lines.append("  %s/%s: MISMATCH %s"
                              % (camp["cid"], info["cell"], "; ".join(diffs)))
        else:
            ok += 1
    note_lines.append("  %s: %d/%d cell(s) consistent with heatmap.csv"
                      % (camp["cid"], ok, ok + mism))


# ---------------------------------------------------------------------- main

def parse_cell_map(entries, ridx):
    """--cell-map 'cid=E001' or 'cid/cNNNN=E001' (repeatable) -> two dicts."""
    exact, whole, used = {}, {}, {}
    for ent in entries or []:
        m = re.fullmatch(r"([^=;\s]+)=([Ee]\d{3})", ent.strip())
        if not m:
            die("--cell-map entry malformed (want cid[/cNNNN]=E001): %r" % ent)
        key, e = m.group(1), "E" + m.group(2)[1:]
        if e not in ridx:
            die("--cell-map E-id %s not in matrix (from %r)" % (e, ent))
        if key in used and used[key] != e:
            die("--cell-map conflicting entries for %s: %s vs %s"
                % (key, used[key], e))
        used[key] = e
        if "/" in key:
            cid, cell = key.split("/", 1)
            exact[(cid, cell)] = e
        else:
            whole[key] = e
    return {**whole, **exact}  # exact keys are tuples, whole are strings


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="W3.3: backfill 05-expanded-matrix.csv result columns "
                    "from campaign artifacts (E/D aggregation + Wilson CI).",
        epilog="Examples:\n"
               "  %(prog)s --campaign runs/ooo_x --dry-run\n"
               "  %(prog)s --campaign . --cell-map w23-toy/c0000=E001 "
               "--allow-unphased --min-n-valid 1 --dry-run\n",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign", nargs="+", required=True, metavar="DIR",
                    help="campaign dir(s): either a root containing runs/ + "
                         "artifacts/, or a runs/<cid> directory itself")
    ap.add_argument("--matrix", default=DEFAULT_MATRIX,
                    help="05-expanded-matrix.csv (default: %(default)s)")
    ap.add_argument("--cell-map", action="append", default=[],
                    metavar="CID[/cNNNN]=E-id",
                    help="explicit experiment-cell mapping for campaigns "
                         "whose manifests predate the ooo block (repeatable)")
    ap.add_argument("--min-n-valid", type=int, default=2000,
                    help="run-count qualification bar (default 2000, north "
                         "star 1.3; lower it explicitly for toy/pilot data)")
    ap.add_argument("--min-events", type=int, default=2000,
                    help="event-coverage qualification bar (default 2000)")
    ap.add_argument("--allow-unphased", action="store_true",
                    help="admit reps whose manifests carry no phase field "
                         "(legacy/toy campaigns; reported as unknown)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite result cells that already hold values "
                         "(default: skip and report)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the cells and values that would be written; "
                         "do not touch the matrix file")
    args = ap.parse_args(argv)

    header, rows, ridx = load_matrix(args.matrix)
    h_res = [header.index(c) for c in RESULT_COL_NAMES]
    h_id, h_du, h_freq, h_load, h_basis = (header.index("ID"),
                                           header.index("设计单元ID"),
                                           header.index("适用频率"),
                                           header.index("负载"),
                                           header.index("计数基准"))
    n_filled_now = sum(1 for r in rows if any(r[i].strip() for i in h_res))
    cell_map = parse_cell_map(args.cell_map, ridx)

    camps = discover_campaigns(args.campaign)
    note("matrix: %s (%d rows, %d result cells currently filled)"
         % (args.matrix, len(rows), n_filled_now))
    note("campaign dirs scanned: %d -> %d campaign(s): %s"
         % (len(args.campaign), len(camps), ", ".join(c["cid"] for c in camps)))
    if cell_map:
        note("explicit cell-map: %s" % args.cell_map)

    ctx = {"header": header, "rows": rows, "ridx": ridx, "cell_map": cell_map,
           "aggs": {}, "seen": set(), "unmapped": [], "n_pilot": 0,
           "n_unphased": 0, "n_consistency": 0, "n_dup": 0,
           "consistency_issues": [], "allow_unphased": args.allow_unphased}
    hm_notes = []
    n_rep_total = 0
    for camp in camps:
        cell_dirs = iter_cell_dirs(camp["runs_dir"])
        infos = [process_campaign_cell(camp, cd, ctx) for cd in cell_dirs]
        n_rep_total += sum(i["n_reps"] for i in infos)
        note("campaign %s: %d cell(s), %d rep(s); heatmap: %s"
             % (camp["cid"], len(infos), sum(i["n_reps"] for i in infos),
                os.path.join("artifacts", camp["cid"], "heatmap.csv")
                if camp["artifacts_dir"] else "MISSING"))
        for i in infos:
            if i["n_bad"]:
                hm_notes.append("  %s/%s: %d unparseable results.jsonl "
                                "line(s) skipped (counted, not silent)"
                                % (camp["cid"], i["cell"], i["n_bad"]))
            raw = i.get("unknown_raw")
            if raw:
                hm_notes.append("  %s/%s: unknown classification value(s) %s "
                                "bucketed as SimulatorError (campaign.py "
                                "counter convention)"
                                % (camp["cid"], i["cell"], raw))
        heatmap_crosscheck(camp, infos, hm_notes)

    note("reps read: %d | included: %d | pilot-excluded: %d | "
         "unphased-excluded: %d | consistency-excluded: %d | duplicate: %d"
         % (n_rep_total, len(ctx["seen"]), ctx["n_pilot"], ctx["n_unphased"],
            ctx["n_consistency"], ctx["n_dup"]))
    if not ctx["aggs"]:
        note("no reps mapped to experiment cells -- nothing to aggregate.")

    # ---------------- per-cell report + qualification ----------------
    cell_reports = []   # {e_id, agg, basis, why, ok}
    n_qualified = 0
    for e_id in sorted(ctx["aggs"]):
        agg = finalize_agg(ctx["aggs"][e_id])
        row = rows[ridx[e_id]]
        basis = row[h_basis]
        if basis == "事件覆盖计数":
            ok = agg["coverage"] >= args.min_events and agg["n_valid"] >= 1
            why = ("coverage=%d event(s)%s" %
                   (agg["coverage"],
                    "" if ok else " < min-events=%d" % args.min_events))
        else:
            ok = agg["n_valid"] >= args.min_n_valid
            why = ("n_valid=%d%s" %
                   (agg["n_valid"],
                    "" if ok else " < min-n-valid=%d" % args.min_n_valid))
        cell_reports.append({"e_id": e_id, "agg": agg, "basis": basis,
                             "why": why, "ok": ok})
        if ok:
            n_qualified += 1

    note("qualification: %d/%d cell(s) meet the counting basis "
         "(min-n-valid=%d, min-events=%d)"
         % (n_qualified, len(cell_reports), args.min_n_valid, args.min_events))
    note("=== experiment cells with data (%d) ===" % len(cell_reports))
    for rep in sorted(cell_reports, key=lambda r: (not r["ok"], r["e_id"])):
        e_id, agg, basis, why, ok = (rep["e_id"], rep["agg"], rep["basis"],
                                     rep["why"], rep["ok"])
        row = rows[ridx[e_id]]
        srcs = {}
        for (cid, cell, src) in agg["sources"]:
            srcs[src] = srcs.get(src, 0) + 1
        note("%s (%s | %s | %s | %s | %s) map-source: %s" %
             (e_id, row[h_du], row[h_freq], row[h_load], basis,
              row[header.index("建议样本量")],
              ", ".join("%s x%d" % kv for kv in sorted(srcs.items()))))
        note("    n_total=%d n_valid=%d inactive=%d simerror=%d | "
             "coverage=%d event(s) | l2=%d rep(s) l3=%d rep(s)"
             % (agg["n_total"], agg["n_valid"], agg["n_inactive"],
                agg["n_simerror"], agg["coverage"],
                agg["n_l2"], len(agg["fanouts"])))
        vals = result_values(agg)
        names = ["SDC%", "Crash%", "Timeout%(Hang)", "Masked%",
                 "仿真器断言崩溃占比%(of n_total)"]
        for name, v, k, n in zip(
                names, vals[:5],
                ["SDC", "Crash", "Hang", "Masked", "SimulatorError"],
                [agg["n_valid"], agg["n_valid"], agg["n_valid"],
                 agg["n_valid"], agg["n_total"]]):
            cnt = (agg["counts"][k] if k != "SimulatorError"
                   else agg["n_simerror"])
            note("    %-28s = %s   (%s/%s)" % (name, v or "n/a", cnt, n))
        note("    %-28s = %s" % ("潜伏期（commit序号）median",
                                 vals[5] or "n/a"))
        note("    %-28s = %s" % ("污染扇出数 mean", vals[6] or "n/a"))
        if agg["ipcs"]:
            note("    mean IPC (stats blocks): %.6f over %d rep(s)"
                 % (statistics.mean(agg["ipcs"]), len(agg["ipcs"])))
        if agg["l2_verdicts"]:
            note("    L2 verdicts: %s | primary_class: %s"
                 % (agg["l2_verdicts"], agg["l2_primary"]))
        prot = {c: agg["counts"][c] for c in PROTECTION_CLASSES
                if agg["counts"][c]}
        if prot:
            note("    NOTE: protection classes counted in n_valid but no "
                 "rate column: %s" % prot)
        if agg["unknown_classes"]:
            note("    NOTE: unknown classifications bucketed as "
                 "SimulatorError: %s" % agg["unknown_classes"])
        if basis == "事件覆盖计数":
            note("    event-coverage cell: coverage=%d event(s) (bar %d)"
                 % (agg["coverage"], args.min_events))
        note("    status: %s -- %s"
             % ("WOULD BACKFILL" if ok
                else "LEFT EMPTY (not qualified)", why))

    # ---------------- unmapped / issues ----------------
    if ctx["unmapped"]:
        n_unmapped_reps = sum(u[3] for u in ctx["unmapped"])
        note("=== unmapped campaign cells: %d (%d rep(s); no E resolution; "
             "showing up to %d) ===" % (len(ctx["unmapped"]), n_unmapped_reps,
                                        MAX_UNMAPPED_LISTED))
        for (cid, cell, why, n) in ctx["unmapped"][:MAX_UNMAPPED_LISTED]:
            note("  %s/%s (%d rep(s)): %s" % (cid, cell, n, why))
        if len(ctx["unmapped"]) > MAX_UNMAPPED_LISTED:
            note("  ... and %d more campaign cell(s)"
                 % (len(ctx["unmapped"]) - MAX_UNMAPPED_LISTED))
    if ctx["consistency_issues"]:
        note("=== manifest-vs-matrix consistency exclusions (%d) ==="
             % len(ctx["consistency_issues"]))
        for (cid, cell, e_id, prob) in ctx["consistency_issues"][:MAX_UNMAPPED_LISTED]:
            note("  %s/%s -> %s: %s" % (cid, cell, e_id, prob))
    if hm_notes:
        note("=== heatmap cross-check (campaign.py aggregation vs this tool) ===")
        for ln in hm_notes:
            note(ln)

    # ---------------- write / dry-run ----------------
    writable = []
    for rep in cell_reports:
        if not rep["ok"]:
            continue
        e_id, agg = rep["e_id"], rep["agg"]
        row = rows[ridx[e_id]]
        already = any(row[i].strip() for i in h_res)
        if already and not args.force:
            note("SKIP %s: result cells already filled (use --force to "
                 "overwrite)" % e_id)
            continue
        writable.append((e_id, result_values(agg)))

    if not writable:
        note("0 cell(s) qualify for writing -- matrix %s"
             % ("NOT modified (dry-run)" if args.dry_run else "unchanged"))
        return 0

    note("=== %s: %d cell(s) %s the matrix ==="
         % ("DRY-RUN (would write)" if args.dry_run else "writing",
            len(writable), "into" if not args.dry_run else "into"))
    for e_id, vals in writable:
        note("  %s: %s" % (e_id, " | ".join(
            "%s=%s" % (n, v if v else "(empty)") for n, v in
            zip(RESULT_COL_NAMES, vals))))
    if args.dry_run:
        note("DRY-RUN: %s NOT modified" % args.matrix)
        return 0

    for e_id, vals in writable:
        row = rows[ridx[e_id]]
        for i, v in zip(h_res, vals):
            row[i] = v
    # utf-8 (no BOM) + CRLF: byte-identical outside the filled cells
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\r\n").writerows([header] + rows)
    d = os.path.dirname(os.path.abspath(args.matrix))
    fd, tmp = tempfile.mkstemp(prefix=".backfill_", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(buf.getvalue())
        os.replace(tmp, args.matrix)
    except OSError as e:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        die("failed to write matrix: %s" % e)
    n_filled_after = sum(1 for r in rows if any(r[i].strip() for i in h_res))
    note("wrote %d cell(s) to %s (result cells filled: %d -> %d; "
         "everything outside the 7 result columns preserved)"
         % (len(writable), args.matrix, n_filled_now, n_filled_after))
    return 0


if __name__ == "__main__":
    sys.exit(main())
