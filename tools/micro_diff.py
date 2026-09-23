#!/usr/bin/env python3
"""micro_diff.py — W2.4 L1 µarchitecture shadow-snapshot differ.

Aligns two CHAOSMicroSnap CSV snapshots (a no-fault reference run vs a
faulted run) by snap_seq and reports, as per-snap series:

  * RAT divergence item counts per class (int/fp/vec) — arch entries whose
    mapped phys register differs between the two runs' FRONT rename maps
    (the L1 signal: a CHAOSRenameMap map_bitflip/f5_substitute corruption,
    or any rename-flow divergence, shows up here).
  * occupancy deviations (rob/iq/freelist x3): run - ref per snap.
  * IPC deviation per snap interval, derived from commit_seq/tick:
    ipc_k = (commit_seq[k]-commit_seq[k-1]) / (tick[k]-tick[k-1]) with a
    virtual origin (0,0); dev_pct = (ipc_run - ipc_ref)/ipc_ref * 100.
  * the "hidden sample" marker: micro_diff does NOT know the architectural
    outcome (that is the W2.1/W2.2 layer's verdict), so it only exports
    max_ipc_dev_pct and the count of intervals whose |IPC deviation| exceeds
    --ipc-hide-pct (default 50). A Masked/SDC verdict combined with a large
    max_ipc_dev_pct is the "silent but slow" hidden-sample case — W2.3's
    results merge is responsible for that join, not this tool.

Pinned input format (produced by CHAOSMicroSnap.cc — do not change one side
without the other). One leading '#' comment line; then per snapshot:

  snap_seq,commit_seq,tick,rob_occ,iq_occ,fl_int,fl_fp,fl_vec,
  rob_head,rob_tail,rat_int_hash,rat_fp_hash,rat_vec_hash,
  rat_int_table,rat_fp_table,rat_vec_table

  rat_<c>_table is "arch:phys;arch:phys;..." over the whole class table
  (';' between entries so the CSV split(',') keeps exactly 16 columns).

Usage:
  python3 tools/micro_diff.py --ref A.csv.gz --run B.csv.gz \
      [--json OUT.json] [--ipc-hide-pct 50] [--self-test]

stdlib only. Exit codes: 0 = diff computed (divergence or not);
1 = usage/parse error (malformed snapshot file, bad args).
"""

import argparse
import gzip
import json
import os
import sys
import tempfile

VERSION = "micro_diff v1 (W2.4)"

# Pinned column contract (16 columns; rat tables last three).
COLUMNS = [
    "snap_seq", "commit_seq", "tick",
    "rob_occ", "iq_occ", "fl_int", "fl_fp", "fl_vec",
    "rob_head", "rob_tail",
    "rat_int_hash", "rat_fp_hash", "rat_vec_hash",
    "rat_int_table", "rat_fp_table", "rat_vec_table",
]
NCOL = len(COLUMNS)
OCC_FIELDS = ["rob_occ", "iq_occ", "fl_int", "fl_fp", "fl_vec"]
RAT_CLASSES = ["int", "fp", "vec"]


class ParseError(Exception):
    pass


def _open_maybe_gzip(path):
    """Open path as gzip (by magic) or plain text. Returns a text file."""
    with open(path, "rb") as f:
        magic = f.read(2)
    if magic == b"\x1f\x8b":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def _to_uint(s, what, path, lineno):
    if not s.isdigit():
        raise ParseError(
            f"{path}:{lineno}: {what} field {s!r} is not a non-negative "
            f"integer")
    return int(s)


def parse_table(s, what, path, lineno):
    """Parse '0:5;1:6;...' into {arch:int -> phys:int}."""
    out = {}
    if s == "":
        return out
    for item in s.split(";"):
        arch, sep, phys = item.partition(":")
        if not sep or not arch.isdigit() or not phys.isdigit():
            raise ParseError(
                f"{path}:{lineno}: malformed {what} table entry {item!r} "
                f"(expected 'arch:phys')")
        a, p = int(arch), int(phys)
        if a in out:
            raise ParseError(
                f"{path}:{lineno}: duplicate arch index {a} in {what} table")
        out[a] = p
    return out


def load_snaps(path):
    """Load one snapshot CSV into a list of dicts (validated).

    Returns (snaps, truncated). A gzip stream missing its trailer — what a
    crashed run leaves behind: CHAOSMicroSnap flushes every row with
    Z_SYNC_FLUSH, but SIGABRT skips the gzclose trailer — surfaces as
    EOFError when the reader tries to pass the end, and the decompressed
    tail may additionally end mid-line (a torn row: fewer than 16 columns).
    Line-wise iteration delivers every complete row before the raise (a
    bulk read(1<<20) does NOT: it raises before returning the partial
    buffer — measured on the real crashed-run artifact). Trailing text
    without a newline is by construction a torn final row (the writer
    always ends rows with '\\n'), so it is dropped and flagged. The
    complete-row prefix is salvaged and `truncated` reports the crash
    honestly instead of discarding the pre-crash divergence series.
    """
    lines = []
    truncated = False
    with _open_maybe_gzip(path) as f:
        try:
            for raw in f:
                lines.append(raw)
        except (EOFError, OSError):
            truncated = True
    text = "".join(lines)
    if text and not text.endswith("\n"):
        # Torn final row (crash mid-write): drop it.
        truncated = True
        text = text[:text.rfind("\n") + 1]

    snaps = []
    prev_snap = None
    prev_commit = None
    prev_tick = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")
        if line == "":
            continue
        if line.startswith("#"):
            continue
        fields = line.split(",")
        if len(fields) != NCOL:
            raise ParseError(
                f"{path}:{lineno}: expected {NCOL} columns, got "
                f"{len(fields)}: {line[:120]}...")
        rec = {}
        for name, val in zip(COLUMNS, fields):
            if name.endswith("_table"):
                continue
            rec[name] = _to_uint(val, name, path, lineno)
        for cls in RAT_CLASSES:
            rec[f"rat_{cls}_table"] = parse_table(
                fields[COLUMNS.index(f"rat_{cls}_table")],
                f"rat_{cls}", path, lineno)
        # series sanity: snap_seq must be strictly increasing; commit_seq
        # and tick strictly increasing.
        if prev_snap is not None:
            if rec["snap_seq"] <= prev_snap:
                raise ParseError(
                    f"{path}:{lineno}: snap_seq {rec['snap_seq']} not"
                    f" strictly increasing (prev {prev_snap})")
            if rec["commit_seq"] <= prev_commit:
                raise ParseError(
                    f"{path}:{lineno}: commit_seq {rec['commit_seq']} not "
                    f"strictly increasing (prev {prev_commit})")
            if rec["tick"] <= prev_tick:
                raise ParseError(
                    f"{path}:{lineno}: tick {rec['tick']} not strictly "
                    f"increasing (prev {prev_tick})")
        prev_snap = rec["snap_seq"]
        prev_commit = rec["commit_seq"]
        prev_tick = rec["tick"]
        snaps.append(rec)
    return snaps, truncated


def rat_div(ref_map, run_map):
    """Count arch entries whose phys mapping differs (union of keys)."""
    div = 0
    for a in set(ref_map) | set(run_map):
        if ref_map.get(a) != run_map.get(a):
            div += 1
    return div


def tables_equal_hash_equal(ref, run, cls):
    """Consistency check: equal tables MUST have equal hashes (they are a
    pure function of the table). A mismatch means format drift or a hash
    bug — refuse to silently trust either."""
    teq = ref[f"rat_{cls}_table"] == run[f"rat_{cls}_table"]
    heq = ref[f"rat_{cls}_hash"] == run[f"rat_{cls}_hash"]
    return teq, heq


def interval_ipc(snaps):
    """Per-snap interval IPC: d(commit_seq)/d(tick) with virtual origin
    (0,0) for the first snap. Returns a list of floats (insts per tick)."""
    out = []
    pc, pt = 0, 0
    for r in snaps:
        dc = r["commit_seq"] - pc
        dt = r["tick"] - pt
        out.append((dc, dt))
        pc, pt = r["commit_seq"], r["tick"]
    return out


def diff(ref_path, run_path, ipc_hide_pct):
    ref, ref_trunc = load_snaps(ref_path)
    run, run_trunc = load_snaps(run_path)

    ref_by = {r["snap_seq"]: r for r in ref}
    run_by = {r["snap_seq"]: r for r in run}
    common = sorted(set(ref_by) & set(run_by))

    res = {
        "tool": VERSION,
        "ref": ref_path,
        "run": run_path,
        "ipc_hide_pct": ipc_hide_pct,
        "ref_truncated": ref_trunc,
        "run_truncated": run_trunc,
        "snaps_ref": len(ref),
        "snaps_run": len(run),
        "snaps_aligned": len(common),
        "snaps_ref_only": len(ref) - len(common),
        "snaps_run_only": len(run) - len(common),
        "hash_table_consistent": True,
        # series (aligned snaps, in snap_seq order)
        "snap_seq_series": common,
        "rat_div_series": {c: [] for c in RAT_CLASSES},
        "occ_dev_series": {f: [] for f in OCC_FIELDS},
        "ipc_dev_pct_series": [],
        # summaries, filled below
        "rat_div_first_snap": None,
        "rat_div_first_snap_by_class": {c: None for c in RAT_CLASSES},
        "rat_div_max_by_class": {c: 0 for c in RAT_CLASSES},
        "rat_div_last_snap_by_class": {c: None for c in RAT_CLASSES},
        "rat_div_nonzero_snaps_by_class": {c: 0 for c in RAT_CLASSES},
        "rat_div_final_by_class": {c: 0 for c in RAT_CLASSES},
        "occ_dev_first_snap": None,
        "occ_dev_max_by_field": {f: 0 for f in OCC_FIELDS},
        "ipc_dev_first_snap": None,
        "max_ipc_dev_pct": 0.0,
        "ipc_hidden_intervals": 0,
        "ipc_invalid_intervals": 0,
        "no_divergence": True,
    }

    for s in common:
        r0, r1 = ref_by[s], run_by[s]
        # Same-period guard: CHAOSMicroSnap emits snap k at exactly
        # (k+1)*snapEvery commits in BOTH runs (the self-held counter counts
        # commits 1:1 regardless of faults), so a commit_seq mismatch at an
        # aligned snap_seq can only mean ref and run were sampled with
        # DIFFERENT snapEvery values — aligning those is meaningless. Refuse
        # loudly instead of emitting a garbage diff (protects the W2.3 merge
        # from mixing files).
        if r0["commit_seq"] != r1["commit_seq"]:
            raise ParseError(
                f"ref and run disagree on commit_seq at snap {s} "
                f"({r0['commit_seq']} vs {r1['commit_seq']}) — the two "
                f"snapshot files were taken with different snapEvery "
                f"periods; aligning them is meaningless")
        any_div = False
        for cls in RAT_CLASSES:
            d = rat_div(r0[f"rat_{cls}_table"], r1[f"rat_{cls}_table"])
            res["rat_div_series"][cls].append(d)
            if d > 0:
                any_div = True
                if res["rat_div_first_snap_by_class"][cls] is None:
                    res["rat_div_first_snap_by_class"][cls] = s
                res["rat_div_last_snap_by_class"][cls] = s
                res["rat_div_nonzero_snaps_by_class"][cls] += 1
            if d > res["rat_div_max_by_class"][cls]:
                res["rat_div_max_by_class"][cls] = d
            res["rat_div_final_by_class"][cls] = d
            # hash/table consistency contract
            teq, heq = tables_equal_hash_equal(r0, r1, cls)
            if teq and not heq:
                res["hash_table_consistent"] = False
        for f in OCC_FIELDS:
            d = r1[f] - r0[f]
            res["occ_dev_series"][f].append(d)
            if d != 0:
                any_div = True
                if res["occ_dev_first_snap"] is None:
                    res["occ_dev_first_snap"] = s
            if abs(d) > abs(res["occ_dev_max_by_field"][f]):
                res["occ_dev_max_by_field"][f] = d
        if any_div and res["rat_div_first_snap"] is None:
            res["rat_div_first_snap"] = s
        if any_div:
            res["no_divergence"] = False

    # IPC deviation per interval (aligned snaps only).
    ref_iv = interval_ipc([ref_by[s] for s in common])
    run_iv = interval_ipc([run_by[s] for s in common])
    for s, (r_iv, u_iv) in zip(common, zip(ref_iv, run_iv)):
        (rdc, rdt), (udc, udt) = r_iv, u_iv
        if rdt == 0 or udt == 0 or rdc == 0 or udc == 0:
            res["ipc_dev_pct_series"].append(None)
            res["ipc_invalid_intervals"] += 1
            continue
        ipc_r = rdc / rdt
        ipc_u = udc / udt
        dev = (ipc_u - ipc_r) / ipc_r * 100.0
        res["ipc_dev_pct_series"].append(dev)
        if dev != 0.0:
            if res["ipc_dev_first_snap"] is None:
                res["ipc_dev_first_snap"] = s
            res["no_divergence"] = False
        if abs(dev) > res["max_ipc_dev_pct"]:
            res["max_ipc_dev_pct"] = abs(dev)
        if abs(dev) > ipc_hide_pct:
            res["ipc_hidden_intervals"] += 1
    return res


def print_summary(res, out=sys.stdout):
    w = out.write
    w(f"{res['tool']}\n")
    w(f"ref={res['ref']} snaps={res['snaps_ref']}"
      f" truncated={str(res['ref_truncated']).lower()}\n")
    w(f"run={res['run']} snaps={res['snaps_run']}"
      f" truncated={str(res['run_truncated']).lower()}\n")
    w(f"aligned={res['snaps_aligned']} "
      f"ref_only={res['snaps_ref_only']} run_only={res['snaps_run_only']}\n")
    w(f"hash_table_consistent={res['hash_table_consistent']}\n")
    verdict = "no_divergence" if res["no_divergence"] else "DIVERGENCE"
    w(f"verdict={verdict}\n")
    for cls in RAT_CLASSES:
        w(f"rat_{cls}_div: max={res['rat_div_max_by_class'][cls]} "
          f"first_snap={res['rat_div_first_snap_by_class'][cls]} "
          f"last_snap={res['rat_div_last_snap_by_class'][cls]} "
          f"nonzero_snaps={res['rat_div_nonzero_snaps_by_class'][cls]} "
          f"final={res['rat_div_final_by_class'][cls]}\n")
    for f in OCC_FIELDS:
        w(f"occ_dev_{f}: max={res['occ_dev_max_by_field'][f]}\n")
    w(f"occ_dev_first_snap={res['occ_dev_first_snap']}\n")
    w(f"ipc_dev_first_snap={res['ipc_dev_first_snap']}\n")
    w(f"max_ipc_dev_pct={res['max_ipc_dev_pct']:.4f}\n")
    w(f"ipc_hidden_intervals(>{res['ipc_hide_pct']}%)="
      f"{res['ipc_hidden_intervals']}\n")
    w(f"ipc_invalid_intervals={res['ipc_invalid_intervals']}\n")
    w(f"rat_div_first_snap={res['rat_div_first_snap']}\n")


# ---------------------------------------------------------------------------
# --self-test: synthetic snapshot pairs (the W2.4 verification d cases).
# ---------------------------------------------------------------------------

def _synth_row(snap_seq, commit_seq, tick, rob=10, iq=8, fi=100, ff=150,
               fv=40, rh=1000, rt=1100, int_tbl=None, fp_tbl=None,
               vec_tbl=None, ih=0, fh=0, vh=0):
    int_tbl = int_tbl if int_tbl is not None else {0: 5, 1: 6, 2: 7, 3: 8}
    fp_tbl = fp_tbl if fp_tbl is not None else {0: 105, 1: 106}
    vec_tbl = vec_tbl if vec_tbl is not None else {0: 205, 1: 206}

    def tbl(d):
        return ";".join(f"{a}:{p}" for a, p in sorted(d.items()))

    # Recompute the exact FNV variant CHAOSMicroSnap.cc uses so synthetic
    # files exercise hash/table consistency the same way real ones do.
    def fnv(d):
        h = 14695981039346656037
        for a, p in sorted(d.items()):
            h = ((h ^ a) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
            h = ((h ^ p) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return h

    return ",".join(str(x) for x in [
        snap_seq, commit_seq, tick, rob, iq, fi, ff, fv, rh, rt,
        ih if ih else fnv(int_tbl), fh if fh else fnv(fp_tbl),
        vh if vh else fnv(vec_tbl),
        tbl(int_tbl), tbl(fp_tbl), tbl(vec_tbl)])


def _write_snap(path, rows, header=True):
    with gzip.open(path, "wt") as f:
        if header:
            f.write("# micro_snap v1: " + ",".join(COLUMNS) + "\n")
        for r in rows:
            f.write(r + "\n")


def self_test():
    """Build synthetic pairs in a temp dir, assert on diff() results."""
    tmp = tempfile.mkdtemp(prefix="micro_diff_selftest_")
    ok = 0

    def path(name):
        return os.path.join(tmp, name)

    def base_rows(tick0=1000, dtick=500, n=5, **kw):
        return [_synth_row(i, (i + 1) * 1000, tick0 + i * dtick, **kw)
                for i in range(n)]

    # Case 1: identical pair -> no divergence.
    rows = base_rows()
    _write_snap(path("A.csv.gz"), rows)
    _write_snap(path("A2.csv.gz"), rows)
    r = diff(path("A.csv.gz"), path("A2.csv.gz"), 50.0)
    assert r["no_divergence"], "identical pair must be no_divergence"
    assert r["snaps_aligned"] == 5
    assert all(v == 0 for v in r["rat_div_max_by_class"].values())
    assert r["max_ipc_dev_pct"] == 0.0 and r["ipc_hidden_intervals"] == 0
    assert r["hash_table_consistent"]
    ok += 1

    # Case 2: same file as both ref and run (self-comparison) -> zero.
    r = diff(path("A.csv.gz"), path("A.csv.gz"), 50.0)
    assert r["no_divergence"]
    ok += 1

    # Case 3: RAT divergence in int class at snaps 2..3 (heals at 4).
    ref_rows = base_rows()
    run_rows = base_rows()
    div_tbl = {0: 5, 1: 6, 2: 9, 3: 8}   # arch 2: 7 -> 9
    run_rows[2] = _synth_row(2, 3000, 2000, int_tbl=div_tbl)
    run_rows[3] = _synth_row(3, 4000, 2500, int_tbl=div_tbl)
    _write_snap(path("B.csv.gz"), run_rows)
    r = diff(path("A.csv.gz"), path("B.csv.gz"), 50.0)
    assert not r["no_divergence"]
    assert r["rat_div_series"]["int"] == [0, 0, 1, 1, 0], r["rat_div_series"]
    assert r["rat_div_series"]["fp"] == [0] * 5
    assert r["rat_div_series"]["vec"] == [0] * 5
    assert r["rat_div_first_snap_by_class"]["int"] == 2
    assert r["rat_div_last_snap_by_class"]["int"] == 3
    assert r["rat_div_max_by_class"]["int"] == 1
    assert r["rat_div_final_by_class"]["int"] == 0  # healed (overwritten)
    assert r["rat_div_first_snap"] == 2
    ok += 1

    # Case 4: occupancy deviation (rob +10, fl_int -7 from snap 3 on).
    run_rows = base_rows()
    for i in (3, 4):
        run_rows[i] = _synth_row(i, (i + 1) * 1000, 1000 + i * 500,
                                 rob=20, fi=93)
    _write_snap(path("C.csv.gz"), run_rows)
    r = diff(path("A.csv.gz"), path("C.csv.gz"), 50.0)
    assert not r["no_divergence"]
    assert r["occ_dev_series"]["rob_occ"] == [0, 0, 0, 10, 10]
    assert r["occ_dev_series"]["fl_int"] == [0, 0, 0, -7, -7]
    assert r["occ_dev_max_by_field"]["rob_occ"] == 10
    assert r["occ_dev_max_by_field"]["fl_int"] == -7
    assert r["occ_dev_first_snap"] == 3
    assert all(v == 0 for k, v in r["rat_div_max_by_class"].items())
    ok += 1

    # Case 5: IPC deviation — both files' snap 0 lands at tick 1000 (interval
    # 0 identical), then the run's tick step doubles => intervals 1..4 have
    # run IPC = ref/2 => dev -50% each. The hide threshold is exclusive (>),
    # so exactly 50.0 does NOT count as hidden; 49.0 catches all 4.
    run_rows = base_rows(dtick=1000)
    _write_snap(path("D.csv.gz"), run_rows)
    r = diff(path("A.csv.gz"), path("D.csv.gz"), 50.0)
    assert not r["no_divergence"]
    assert r["ipc_dev_first_snap"] == 1
    assert abs(r["max_ipc_dev_pct"] - 50.0) < 1e-9
    assert r["ipc_hidden_intervals"] == 0  # exactly 50% is not > 50%
    ok += 1
    r = diff(path("A.csv.gz"), path("D.csv.gz"), 49.0)
    assert r["ipc_hidden_intervals"] == 4
    ok += 1

    # Case 6: length mismatch (run stops early) -> run_only counted.
    _write_snap(path("E.csv.gz"), base_rows()[:3])
    r = diff(path("A.csv.gz"), path("E.csv.gz"), 50.0)
    assert r["snaps_aligned"] == 3 and r["snaps_run_only"] == 0
    assert r["snaps_ref_only"] == 2
    ok += 1

    # Case 7: hash/table consistency violation is flagged (equal tables but
    # a wrong hash on one side -> format drift must not pass silently).
    run_rows = base_rows()
    run_rows[2] = _synth_row(2, 3000, 2000, ih=0xDEADBEEF)
    _write_snap(path("F.csv.gz"), run_rows)
    r = diff(path("A.csv.gz"), path("F.csv.gz"), 50.0)
    assert not r["hash_table_consistent"]
    ok += 1

    # Case 8: malformed table entry -> ParseError.
    bad = [",".join(["0", "1000", "1000", "1", "1", "1", "1", "1", "1",
                     "1", "1", "1", "1", "0:5:9", "0:105", "0:205"])]
    _write_snap(path("G.csv.gz"), bad)
    try:
        diff(path("A.csv.gz"), path("G.csv.gz"), 50.0)
        raise AssertionError("malformed table must raise ParseError")
    except ParseError:
        ok += 1

    # Case 9: truncated gzip (a crashed run's snapshot: rows flushed with
    # Z_SYNC_FLUSH, gzip trailer missing). Cut the byte tail of a valid
    # file; the salvage must keep the complete-row prefix, flag truncated,
    # and diff must still work on the salvaged prefix.
    with open(path("H.csv.gz"), "wb") as f:
        with gzip.open(path("A.csv.gz"), "rb") as src:
            blob = src.read()
        f.write(blob[:len(blob) // 2])   # cut mid-stream
    snaps, trunc = load_snaps(path("H.csv.gz"))
    assert trunc and 0 < len(snaps) < 5, (trunc, len(snaps))
    r = diff(path("A.csv.gz"), path("H.csv.gz"), 50.0)
    assert r["run_truncated"] and not r["ref_truncated"]
    assert r["snaps_aligned"] == len(snaps)
    assert r["snaps_ref_only"] == 5 - len(snaps)
    ok += 1

    # Case 10: cross-period guard — a run sampled at a different snapEvery
    # must be REFUSED, not silently mis-diffed (A is every-1000; I is
    # every-500, so snap 1 means commit 1000 in ref but 1500 in run).
    _write_snap(path("I.csv.gz"),
                [_synth_row(0, 500, 500), _synth_row(1, 1500, 1000),
                 _synth_row(2, 2500, 1500)])
    try:
        diff(path("A.csv.gz"), path("I.csv.gz"), 50.0)
        raise AssertionError("cross-period diff must raise ParseError")
    except ParseError:
        ok += 1

    # 11 checks over 10 synthetic cases (case 5 checked at two thresholds).
    assert ok == 11, f"self-test bookkeeping: expected 11 checks, ran {ok}"
    print("micro_diff self-test: 11/11 checks (10 synthetic cases) PASS")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="W2.4 L1 µarch shadow-snapshot differ (micro_snap.csv.gz)")
    ap.add_argument("--ref", help="reference (no-fault) snapshot CSV(.gz)")
    ap.add_argument("--run", help="faulted-run snapshot CSV(.gz)")
    ap.add_argument("--json", help="optional output JSON path (full series)")
    ap.add_argument("--ipc-hide-pct", type=float, default=50.0,
                    help="hidden-sample IPC deviation threshold in percent "
                         "(interval counts when |dev| > this; default 50)")
    ap.add_argument("--self-test", action="store_true",
                    help="run the synthetic-pair self-test and exit")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.ref or not args.run:
        ap.error("--ref and --run are required (or use --self-test)")

    try:
        res = diff(args.ref, args.run, args.ipc_hide_pct)
    except ParseError as e:
        print(f"micro_diff: PARSE ERROR: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"micro_diff: IO ERROR: {e}", file=sys.stderr)
        return 1

    print_summary(res)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, indent=1)
        print(f"json written: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
