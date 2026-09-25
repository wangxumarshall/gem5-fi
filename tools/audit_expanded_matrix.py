#!/usr/bin/env python3
"""W9.1 completeness audit (OoO north star, docs/gem5-fi/ooo/
06-implementation-plan.md §1.2/§9 + W9.1): after the 7 result columns of
docs/gem5-fi/ooo/05-expanded-matrix.csv (E001-E226) are backfilled by
tools/backfill_expanded_matrix.py, this script asserts the matrix is
DELIVERY-COMPLETE. It reads ONLY the matrix CSV (+ the W8.5 alias_map yaml
for the merged-cell accounting) -- it never touches runs/ or artifacts/.

ASSERTION GROUPS (each reported loudly; any hard violation => exit 1)

  G1  non-deferred cells have no empty result values
      deferred = 负载 column contains "SVE" (D78-D82, PolyBench（SVE 向量化版）
      rows -- 06 §1.3 default-deferred, excluded from the 920 口径).  Every
      OTHER row must have all 7 result columns non-empty.  The two honest
      non-value tokens are accepted as NON-empty and reported:
        - "n/a" (case-insensitive, exact token): no denominator / no L2-L3
          evidence -- explicit per the repo honesty convention, never a
          silent zero and never a silent blank;
        - an alias marker (value containing "别名" or "alias", case-blind)
          ONLY on cells in the G4 alias set (merged-row credit).
      Structural precondition: IDs are unique and exactly E001..E226.

  G2  Wilson CI present wherever a proportion value is present
      backfill_expanded_matrix.py writes rates IN-CELL as "p [lo,hi]"
      (pct_ci -> "%.2f [%.2f,%.2f]"), so the CSV has no separate CI
      columns; a rate value that lacks the "[lo,hi]" part is a violation.
      潜伏期 must be numeric ("%g" median) and 污染扇出数 numeric
      ("%.2f" mean) when not n/a / alias-marked.  A matrix with ZERO rate
      values reports the check as vacuous (loud), not as passed.

  G3  n_valid >= --min-n-valid (default 2000, 06 §1.3)
      The matrix carries NO n / n_valid column, so this CANNOT be asserted
      from the CSV alone: the check DOWNGRADES TO A WARNING and documents
      the boundary -- the bar is enforced upstream by backfill (a cell is
      only written when its counting basis is met) and is re-derivable
      from artifacts (results.jsonl per E-id); CSV-vs-artifacts comparison
      is out of scope for this script.  If a future matrix revision adds
      an n/n_valid column, the check turns hard automatically.

  G4  merged/alias cell accounting (W8 plan doc §0 ruling 7; W7.2 merge)
      Reads alias_map from campaigns/ooo-w85-fpsimd.yaml (D62-D66 x
      PolyBench -> D67-D71; D72/D73 x 长依赖链压力核 -> D74/D75; 10 cells
      total: E159 E161 E163 E165 E167 E169 E171 E187 E188 E189).  These
      cells are NOT re-run; they are credited from the covered_by rows.
      Assertions: every alias E-id exists in the matrix and is not
      deferred; every alias cell is non-empty (a real value, "n/a", or an
      explicit alias marker -- never silently blank); every covered_by
      design unit exists in the matrix.  The full E-id -> covered_by table
      is printed for the delivery record.

  G5  pilot data never enters the result columns
      STRUCTURAL BOUNDARY (documented, not re-derived here): the pilot
      exclusion is enforced upstream -- campaign.py writes pilot reps to
      pilot_results.jsonl only and backfill_expanded_matrix.py hard-gates
      on ooo.phase (pilot reps are never admitted, --allow-unphased
      excepted and always reported).  This script cannot distinguish a
      pilot-derived number from a formal one by reading the CSV; that
      audit belongs to the artifacts side (same boundary as G3).

EXIT CODES: 0 = no hard violations (warnings allowed) | 1 = violations |
2 = bad input (unreadable matrix / unreadable alias yaml / bad structure).

USAGE
  python3 tools/audit_expanded_matrix.py                     # audit the real matrix
  python3 tools/audit_expanded_matrix.py --matrix /tmp/f.csv # audit a fixture
  python3 tools/audit_expanded_matrix.py --min-n-valid 2000
"""
import argparse
import csv
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_MATRIX = os.path.join(REPO, "docs", "gem5-fi", "ooo",
                              "05-expanded-matrix.csv")
DEFAULT_ALIAS_YAML = os.path.join(REPO, "campaigns", "ooo-w85-fpsimd.yaml")

# The 7 result columns (exact header names, same list as backfill).
RESULT_COL_NAMES = [
    "SDC%", "Crash%", "Timeout%", "Masked%", "仿真器断言崩溃占比%",
    "潜伏期（commit序号）", "污染扇出数",
]
RATE_COL_NAMES = RESULT_COL_NAMES[:5]
LATENCY_COL, FANOUT_COL = RESULT_COL_NAMES[5], RESULT_COL_NAMES[6]
REQUIRED_COLS = (["ID", "设计单元ID", "适用频率", "负载", "计数基准"]
                 + RESULT_COL_NAMES)

EXPECTED_IDS = ["E%03d" % i for i in range(1, 227)]          # E001..E226
DEFERRED_MARK = "SVE"                                        # in 负载 column
ALIAS_MARK_RE = re.compile(r"别名|alias", re.IGNORECASE)     # in-cell marker
NA_TOKENS = ("n/a", "N/A")
# backfill pct_ci writes "%.2f [%.2f,%.2f]"; accept any fixed-point variant
PCT_CI_RE = re.compile(r"^\d+(?:\.\d+)?\s*\[\d+(?:\.\d+)?,\s*\d+(?:\.\d+)?\]$")
NUM_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")
N_COL_RE = re.compile(r"^n[_ ]?valid$|^n$|^n[_ ]?total$", re.IGNORECASE)
MAX_LISTED = 25          # keep the report bounded, never silent


def die(msg):
    print("[audit] ERROR: %s" % msg, file=sys.stderr)
    sys.exit(2)


def note(msg):
    print("[audit] %s" % msg)


# ------------------------------------------------------------------- inputs

def load_matrix(path):
    """05-expanded-matrix.csv -> (header, rows). Dies on bad structure."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            raw = f.read()
    except OSError as e:
        die("matrix unreadable: %s (%s)" % (path, e))
    table = [r for r in csv.reader(io.StringIO(raw)) if r]
    if len(table) < 2:
        die("matrix has no data rows: %s" % path)
    header, rows = table[0], table[1:]
    missing = [c for c in REQUIRED_COLS if c not in header]
    if missing:
        die("matrix header missing expected columns %s: %s" % (missing, path))
    ids = [r[header.index("ID")] for r in rows]
    if len(set(ids)) != len(ids):
        die("matrix ID column has duplicates: %s" % path)
    return header, rows


def load_alias_map(path):
    """alias_map from the W8.5 umbrella yaml -> list of entries.
    {design_unit_id, workload, covered_by, experiment_cell_ids}."""
    try:
        import yaml
    except ImportError:
        die("pyyaml required to read the alias_map (%s) -- same dependency "
            "as tools/backfill_expanded_matrix.py" % path)
    try:
        with open(path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except OSError as e:
        die("alias yaml unreadable: %s (%s)" % (path, e))
    except Exception as e:  # yaml.YAMLError, but stay stdlib-typed
        die("alias yaml unparseable: %s (%s)" % (path, e))
    amap = (doc or {}).get("alias_map")
    if not isinstance(amap, list) or not amap:
        die("no alias_map list in %s -- cannot run the G4 merged-cell "
            "accounting (the map is the authoritative merged-cell roster)"
            % path)
    out = []
    for ent in amap:
        eids = ent.get("experiment_cell_ids") or []
        if not ent.get("design_unit_id") or not ent.get("covered_by") or not eids:
            die("alias_map entry malformed (needs design_unit_id, covered_by,"
                " experiment_cell_ids): %r" % (ent,))
        out.append({"design_unit_id": str(ent["design_unit_id"]),
                    "workload": str(ent.get("workload", "")),
                    "covered_by": str(ent["covered_by"]),
                    "eids": [str(e) for e in eids]})
    return out


# ------------------------------------------------------------------ helpers

def is_blank(v):
    return v is None or str(v).strip() == ""


def is_na(v):
    return str(v).strip() in NA_TOKENS


def is_alias_marked(v):
    return bool(ALIAS_MARK_RE.search(str(v)))


def classify(row, h, alias_eids):
    """deferred | alias | normal for one matrix row."""
    load = row[h["负载"]]
    if DEFERRED_MARK in load:
        return "deferred"
    if row[h["ID"]] in alias_eids:
        return "alias"
    return "normal"


def fmt_missing(cols):
    return ", ".join(cols) if cols else "-"


# ---------------------------------------------------------------------- G1

def check_g1(header, rows, h, alias_eids):
    """Non-deferred cells: all 7 result columns non-empty. Returns
    (violations, n_na_cells, per-class counts)."""
    ids = [r[h["ID"]] for r in rows]
    viol, na_cells, counts = [], [], {"deferred": 0, "alias": 0, "normal": 0}
    for r in rows:
        cls = classify(r, h, alias_eids)
        counts[cls] += 1
        if cls == "deferred":
            continue
        if cls == "alias":
            continue  # emptiness of alias cells is asserted in G4
        missing = [c for c in RESULT_COL_NAMES if is_blank(r[h[c]])]
        if missing:
            viol.append((r[h["ID"]], missing))
        for c in RESULT_COL_NAMES:  # explicit n/a is legal, but reported
            if is_na(r[h[c]]):
                na_cells.append((r[h["ID"]], c))
    return viol, na_cells, counts


# ---------------------------------------------------------------------- G2

def check_g2(header, rows, h, alias_eids):
    """Rate values carry Wilson CI in-cell; latency/fanout numeric.
    Returns (violations, n_rate_values, vacuous_flag)."""
    viol, n_rate = [], 0
    for r in rows:
        if classify(r, h, alias_eids) == "deferred":
            continue
        e_id = r[h["ID"]]
        for c in RATE_COL_NAMES:
            v = r[h[c]]
            if is_blank(v) or is_na(v) or is_alias_marked(v):
                continue
            n_rate += 1
            if not PCT_CI_RE.match(v.strip()):
                viol.append((e_id, c, v.strip()))
        for c in (LATENCY_COL, FANOUT_COL):
            v = r[h[c]]
            if is_blank(v) or is_na(v) or is_alias_marked(v):
                continue
            if not NUM_RE.match(v.strip()):
                viol.append((e_id, c, v.strip()))
    return viol, n_rate


# ---------------------------------------------------------------------- G4

def check_g4(header, rows, h, alias_entries):
    """Merged-cell accounting. Returns (violations, table_lines, alias_eids,
    covered_missing)."""
    viol, table, alias_eids, covered_missing = [], [], set(), []
    all_ids = {r[h["ID"]] for r in rows}
    all_dus = {r[h["设计单元ID"]] for r in rows}
    for ent in alias_entries:
        for e in ent["eids"]:
            alias_eids.add(e)
            table.append("%s (%s x %s) -> covered_by %s"
                         % (e, ent["design_unit_id"], ent["workload"] or "?",
                            ent["covered_by"]))
        if ent["covered_by"] not in all_dus:
            covered_missing.append(ent["covered_by"])
    # second pass: cell-level assertions need the full alias set first
    for ent in alias_entries:
        for e in ent["eids"]:
            if e not in all_ids:
                viol.append((e, "E-id from alias_map not present in matrix"))
                continue
            row = rows[[r[h["ID"]] for r in rows].index(e)]
            if DEFERRED_MARK in row[h["负载"]]:
                viol.append((e, "alias cell is ALSO SVE-deferred -- "
                                "classification conflict"))
            missing = [c for c in RESULT_COL_NAMES if is_blank(row[h[c]])]
            if missing:
                viol.append((e, "alias cell silently empty in: %s"
                             % fmt_missing(missing)))
    return viol, table, alias_eids, covered_missing


# ---------------------------------------------------------------------- G3

def check_g3(header, rows, h, min_n_valid):
    """n_valid bar. Hard only if an n/n_valid column exists; else warning."""
    n_cols = [c for c in header if N_COL_RE.match(c.strip())]
    if not n_cols:
        return ("warn", "matrix carries no n/n_valid column -- n_valid >= %d "
                "cannot be asserted from the CSV. DOWNGRADED TO WARNING "
                "(documented boundary): the bar is enforced by "
                "tools/backfill_expanded_matrix.py at write time (only "
                "counting-basis-qualified cells are ever written) and is "
                "re-derivable from artifacts/ (per-E-id results.jsonl). "
                "CSV-vs-artifacts comparison is out of scope for this "
                "script." % min_n_valid)
    viol = []
    col = n_cols[0]
    for r in rows:
        if classify(r, h, set()) == "deferred":  # alias set not needed here
            continue
        v = r[h[col]]
        if is_blank(v) or is_na(v):
            continue
        try:
            n = float(v)
        except ValueError:
            viol.append((r[h["ID"]], col, v.strip()))
            continue
        if n < min_n_valid:
            viol.append((r[h["ID"]], col, "%s < %d" % (v.strip(), min_n_valid)))
    return ("hard", viol, col)


# --------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="W9.1: completeness audit of the 7 result columns in "
                    "05-expanded-matrix.csv (226 cells; deferred/alias "
                    "aware; Wilson-CI aware).",
        epilog="Exit codes: 0 pass (warnings allowed) | 1 violations | "
               "2 bad input.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--matrix", default=DEFAULT_MATRIX,
                    help="05-expanded-matrix.csv (default: %(default)s)")
    ap.add_argument("--alias-yaml", default=DEFAULT_ALIAS_YAML,
                    help="umbrella yaml carrying alias_map for the merged-"
                         "cell accounting (default: %(default)s)")
    ap.add_argument("--min-n-valid", type=int, default=2000,
                    help="run-count qualification bar for G3 "
                         "(default: %(default)s; only enforced when the "
                         "matrix has an n/n_valid column)")
    args = ap.parse_args(argv)

    header, rows = load_matrix(args.matrix)
    h = {c: header.index(c) for c in REQUIRED_COLS}
    alias_entries = load_alias_map(args.alias_yaml)

    ids = [r[h["ID"]] for r in rows]
    note("matrix: %s (%d rows, %d result columns audited: %s)"
         % (args.matrix, len(rows), len(RESULT_COL_NAMES),
            ", ".join(RESULT_COL_NAMES)))
    note("alias yaml: %s (%d alias_map entries)" % (args.alias_yaml,
                                                    len(alias_entries)))

    # ---- structural precondition (folded into G1's report) ----
    structural = []
    if ids != EXPECTED_IDS:
        missing = [e for e in EXPECTED_IDS if e not in set(ids)]
        extra = [i for i in ids if i not in set(EXPECTED_IDS)]
        if missing or extra or len(ids) != 226:
            structural.append("ID set != E001..E226 (missing=%s extra=%s "
                              "n=%d)" % (missing or "-", extra or "-",
                                         len(ids)))

    # ---- G4 first: its alias_eids roster feeds G1/G2 exemptions ----
    g4_viol, g4_table, alias_eids, covered_missing = \
        check_g4(header, rows, h, alias_entries)

    # ---- G1 ----
    g1_viol, na_cells, counts = check_g1(header, rows, h, alias_eids)
    note("=== G1 non-deferred cells non-empty ===")
    note("cell classes: normal=%d alias=%d deferred(SVE)=%d (of %d rows)"
         % (counts["normal"], counts["alias"], counts["deferred"], len(rows)))
    if structural:
        for s in structural:
            note("  VIOLATION (structural): %s" % s)
        g1_viol = g1_viol + [("STRUCTURE", [s]) for s in structural]
    if g1_viol:
        note("  VIOLATIONS: %d cell(s) with empty result values "
             "(showing up to %d):" % (len(g1_viol), MAX_LISTED))
        for e_id, missing in g1_viol[:MAX_LISTED]:
            note("    %s: empty -> %s" % (e_id, fmt_missing(missing)))
        if len(g1_viol) > MAX_LISTED:
            note("    ... and %d more cell(s)" % (len(g1_viol) - MAX_LISTED))
    else:
        note("  OK: all %d normal cells have all 7 result columns non-empty"
             % counts["normal"])
    if na_cells:
        note("  NOTE: %d explicit n/a value(s) present (legal, must be "
             "justified at delivery; showing up to %d): %s"
             % (len(na_cells), MAX_LISTED,
                "; ".join("%s/%s" % nc for nc in na_cells[:MAX_LISTED])))

    # ---- G2 ----
    g2_viol, n_rate = check_g2(header, rows, h, alias_eids)
    note("=== G2 Wilson CI present on proportion values ===")
    if n_rate == 0 and not g2_viol:
        note("  VACUOUS: 0 rate values present in the matrix -- nothing to "
            "CI-check (an all-empty matrix is reported here loudly, NOT "
            "silently passed)")
    if g2_viol:
        note("  VIOLATIONS: %d value(s) not in 'p [lo,hi]' / numeric "
             "format (showing up to %d):" % (len(g2_viol), MAX_LISTED))
        for e_id, col, v in g2_viol[:MAX_LISTED]:
            note("    %s / %s: %r" % (e_id, col, v))
        if len(g2_viol) > MAX_LISTED:
            note("    ... and %d more value(s)" % (len(g2_viol) - MAX_LISTED))
    elif n_rate:
        note("  OK: all %d rate value(s) carry in-cell Wilson CI "
             "'p [lo,hi]'; latency/fanout numeric or n/a" % n_rate)

    # ---- G3 ----
    note("=== G3 n_valid >= %d ===" % args.min_n_valid)
    res = check_g3(header, rows, h, args.min_n_valid)
    if res[0] == "warn":
        note("  WARNING (downgraded, documented): %s" % res[1])
    else:
        if res[1]:
            note("  VIOLATIONS via column %r: %d (showing up to %d): %s"
                 % (res[2], len(res[1]), MAX_LISTED, res[1][:MAX_LISTED]))
        else:
            note("  OK: column %r satisfies n >= %d on all non-deferred "
                 "filled cells" % (res[2], args.min_n_valid))

    # ---- G4 ----
    note("=== G4 merged/alias cell accounting ===")
    note("  alias roster (%d cell(s)):" % len(alias_eids))
    for ln in g4_table:
        note("    %s" % ln)
    if covered_missing:
        note("  VIOLATIONS: covered_by design unit(s) absent from matrix: %s"
             % ", ".join(covered_missing))
        g4_viol = g4_viol + [("covered_by", c) for c in covered_missing]
    if g4_viol:
        note("  VIOLATIONS: %d (showing up to %d):" % (len(g4_viol), MAX_LISTED))
        for e_id, why in g4_viol[:MAX_LISTED]:
            note("    %s: %s" % (e_id, why))
        if len(g4_viol) > MAX_LISTED:
            note("    ... and %d more" % (len(g4_viol) - MAX_LISTED))
    else:
        note("  OK: all alias cells present, non-deferred, and non-empty "
            "(value / n/a / explicit alias marker)")

    # ---- G5 ----
    note("=== G5 pilot data never in result columns ===")
    note("  STRUCTURAL BOUNDARY (documented, not re-derived from the CSV): "
         "pilot exclusion is enforced upstream -- campaign.py writes pilot "
         "reps to pilot_results.jsonl only (results.jsonl is formal-only) "
         "and backfill_expanded_matrix.py hard-gates on ooo.phase.  A "
         "CSV-only audit cannot distinguish a pilot-derived number from a "
         "formal one; that check belongs to the artifacts side (same "
         "boundary as G3).  No assertion evaluated here -- by design.")

    # ---- verdict ----
    hard = {"G1": len(g1_viol), "G2": len(g2_viol), "G4": len(g4_viol)}
    note("=== verdict ===")
    note("hard violations: G1=%d G2=%d G4=%d | G3=warning-only "
         "(no n column) | G5=structural boundary" %
         (hard["G1"], hard["G2"], hard["G4"]))
    if any(hard.values()):
        note("AUDIT FAIL: %d violation(s) -- the matrix is NOT delivery-"
             "complete." % sum(hard.values()))
        return 1
    note("AUDIT PASS: matrix is delivery-complete under the documented "
         "boundaries (G3 warning, G5 boundary).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
