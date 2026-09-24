#!/usr/bin/env python3
"""fanout.py -- W2.6 L3 fanout counter (OoO north star, software-layer
propagation; docs/gem5-fi/ooo/01-observation-points.md L3, plan Task 6).

North-star question: after a physical register is polluted, how many
subsequent instructions read it?

Data source: the W2.1 commit trace (one line per committed instruction,
pinned format `seq,tid,tick,pc,op,ndest[,class,arch,phys,val]*` -- only DEST
registers are recorded; SOURCE-side reads are NOT in the trace).

HONEST metric (this tool's documented contract):
  - liveness window = the number of committed instructions strictly between
    one write to phys P (P appearing as a dest) and the NEXT overwrite of P
    (P appearing as a dest again):  window = seq_next - seq_write - 1.
    Neither the writing nor the overwriting instruction is counted. The last
    write of the trace has no successor -- an OPEN (censored) window that is
    counted separately and excluded from the window statistics.
  - val_changes = the number of consecutive write pairs to P whose 16-hex
    val differs.
  - CAVEAT (pinned in every JSON output): source reads are invisible in the
    commit trace, so the liveness window is an UPPER-BOUND PROXY for the
    true consumer-read fanout, not a read count.

Known trace quirks honored (W2.1 execution notes): XZR/WZR dests print the
gem5 sentinel class=-1/phys=65535 (asking for 65535 measures the whole
zero-register family); MiscReg dests do not read the PRF (their val column
is recorded as zero); lines are per committed DynInst INCLUDING microcode
ops (309387 rows vs simInsts 308057 on the smoke kernel), so windows are in
committed-rows, not simInsts.

Usage:
  python3 tools/fanout.py --trace commit_trace.csv.gz --phys 80 \\
      [--json OUT.json] [--window 0]

  --window W (default 0 = uncapped): also report fanout_capped, every window
  truncated at min(window, W) -- a bounded fanout proxy comparable across
  runs -- plus how many windows hit the cap.

Exit codes: 0 = analysis done (INCLUDING n_writes=0: the phys id simply
never appears as a dest -- an honest finding, not an error); 2 = the trace
is missing, malformed, or unreadable (a truncated gzip stream from a Crash
rep is NOT an error: the readable prefix is analyzed and "truncated": true
is recorded, mirroring tools/micro_diff.py's rescue path).

stdlib only.
"""

import argparse
import gzip
import json
import os
import statistics
import sys

TRACE_FORMAT = "seq,tid,tick,pc,op,ndest[,class,arch,phys,val]*"
CAVEAT = ("source-side reads are not recorded in the commit trace; the "
          "liveness window (committed instructions before the next "
          "overwrite of the same phys id) is an UPPER-BOUND proxy for the "
          "number of consumer reads, not a read count")
# report the full per-write window list only up to this many closed windows
WINDOWS_INLINE_MAX = 100


def die(msg):
    print("fanout.py: ERROR: %s" % msg, file=sys.stderr)
    sys.exit(2)


def open_trace(path):
    """Open the trace as text, gzip by magic (W2.1 writes .csv.gz via
    simout.create; plain text accepted for synthetic tests)."""
    try:
        with open(path, "rb") as f:
            magic = f.read(2)
    except OSError as e:
        die("cannot read trace %s: %s" % (path, e))
    if magic == b"\x1f\x8b":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "rt", encoding="utf-8", errors="replace")


def parse_dest_quads(cols, path, lineno):
    """Yield (class, arch, phys, val_int) for each dest quad of one trace
    line. Strict contract check (W2.1 pinned format): exactly
    6 + 4*ndest columns, val exactly 16 hex chars."""
    try:
        ndest = int(cols[5])
        seq = int(cols[0])
    except ValueError:
        die("%s:%d: bad ndest/seq (format: %s): %r"
            % (path, lineno, TRACE_FORMAT, ",".join(cols)))
    if ndest < 0 or len(cols) != 6 + 4 * ndest:
        die("%s:%d: column count %d != 6 + 4*ndest(%d) (format: %s)"
            % (path, lineno, len(cols), ndest, TRACE_FORMAT))
    quads = []
    for i in range(ndest):
        b = 6 + 4 * i
        cls_s, arch_s, phys_s, val_s = cols[b], cols[b + 1], cols[b + 2], cols[b + 3]
        try:
            cls = int(cls_s)   # -1 = gem5 XZR/WZR sentinel (W2.1 note)
            arch = int(arch_s)
            phys = int(phys_s)
        except ValueError:
            die("%s:%d: bad dest quad %d (class/arch/phys not ints): %r"
                % (path, lineno, i, ",".join(cols[b:b + 4])))
        if len(val_s) != 16:
            die("%s:%d: dest quad %d val %r is not 16 hex chars"
                % (path, lineno, i, val_s))
        try:
            val = int(val_s, 16)
        except ValueError:
            die("%s:%d: dest quad %d val %r is not hex"
                % (path, lineno, i, val_s))
        quads.append((cls, arch, phys, val))
    return seq, quads


def collect_writes(path, phys_id):
    """Stream the trace, collecting (seq, arch, class, val) for every dest
    quad whose phys == phys_id. Returns (writes, truncated, n_lines).

    A truncated gzip stream (Crash rep: gem5 aborts before the stream is
    finalized) raises EOFError/BadGzipFile mid-iteration -- the readable
    prefix is kept and truncated=True is returned (honest partial evidence,
    micro_diff.py precedent)."""
    writes = []
    n_lines = 0
    truncated = False
    fh = open_trace(path)
    try:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            n_lines += 1
            seq, quads = parse_dest_quads(line.split(","), path, lineno)
            for (cls, arch, phys, val) in quads:
                if phys == phys_id:
                    writes.append((seq, arch, cls, val))
    except (EOFError, gzip.BadGzipFile, OSError) as e:
        truncated = True
        print("fanout.py: note: trace stream ended early (%s: %s) -- "
              "analyzing the readable prefix (%d lines) and marking "
              "truncated=true" % (path, e, n_lines), file=sys.stderr)
    finally:
        fh.close()
    return writes, truncated, n_lines


def mean_med_min_max(xs):
    """Honest summary over a non-empty list; None for an empty one."""
    if not xs:
        return None
    return {"mean": round(statistics.mean(xs), 2),
            "median": statistics.median(xs),
            "min": min(xs), "max": max(xs)}


def analyze(path, phys_id, window_cap):
    writes, truncated, n_lines = collect_writes(path, phys_id)
    seqs = [w[0] for w in writes]
    # closed windows: consecutive write pairs; open: the last write has no
    # successor in the trace (censored -- excluded from the statistics)
    windows = [seqs[i + 1] - seqs[i] - 1 for i in range(len(seqs) - 1)]
    val_changes = sum(1 for i in range(len(writes) - 1)
                      if writes[i][3] != writes[i + 1][3])
    arch_counts, class_counts = {}, {}
    for (_, arch, cls, _) in writes:
        arch_counts[str(arch)] = arch_counts.get(str(arch), 0) + 1
        class_counts[str(cls)] = class_counts.get(str(cls), 0) + 1

    out = {
        "tool": "fanout",
        "trace": os.path.abspath(path),
        "phys": phys_id,
        "trace_lines": n_lines,
        "truncated": truncated,
        "n_writes": len(writes),
        "n_closed_windows": len(windows),
        "n_open_windows": 1 if writes else 0,
        "first_write_seq": seqs[0] if seqs else None,
        "last_write_seq": seqs[-1] if seqs else None,
        "liveness": mean_med_min_max(windows),
        "val_changes": val_changes,
        "arch_counts": arch_counts,
        "class_counts": class_counts,
        "window_cap": window_cap if window_cap > 0 else None,
        "fanout_capped": None,
        "caveat": CAVEAT,
    }
    if window_cap > 0 and windows:
        capped = [min(w, window_cap) for w in windows]
        out["fanout_capped"] = {
            "liveness": mean_med_min_max(capped),
            "n_windows_hitting_cap": sum(1 for w in windows if w >= window_cap),
        }
    if len(windows) <= WINDOWS_INLINE_MAX:
        out["windows"] = windows
    else:
        out["windows_omitted"] = len(windows)
    if not writes:
        out["note"] = ("phys id %d never appears as a dest in the trace -- "
                       "zero fanout evidence (wrong id, or the register is "
                       "never written)" % phys_id)
    if phys_id == 65535:
        out["note"] = ("phys 65535 is the gem5 XZR/WZR sentinel (class=-1): "
                       "this measures the whole zero-register dest family")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="W2.6 L3 fanout: liveness windows of one physical "
                    "register id in a W2.1 commit trace (upper-bound proxy "
                    "for consumer reads -- source reads are not traced).")
    ap.add_argument("--trace", required=True, metavar="TRACE.csv.gz",
                    help="W2.1 commit trace (gzip by magic, or plain text)")
    ap.add_argument("--phys", required=True, type=int, metavar="ID",
                    help="physical register id to track (as recorded in "
                         "dest quads; 65535 = the XZR/WZR sentinel family)")
    ap.add_argument("--json", metavar="OUT",
                    help="also write the full result as JSON to this path")
    ap.add_argument("--window", type=int, default=0, metavar="W",
                    help="cap each liveness window at W committed "
                         "instructions and report fanout_capped (bounded "
                         "proxy); 0 (default) = uncapped")
    args = ap.parse_args(argv)

    if args.phys < 0:
        die("--phys must be a non-negative integer")
    if args.window < 0:
        die("--window must be >= 0")
    if not os.path.exists(args.trace):
        die("trace not found: %s" % args.trace)

    out = analyze(args.trace, args.phys, args.window)

    print("fanout: trace=%s phys=%d" % (out["trace"], args.phys))
    print("  trace_lines=%d truncated=%s" % (out["trace_lines"],
                                             out["truncated"]))
    print("  writes=%d closed_windows=%d open_windows=%d"
          % (out["n_writes"], out["n_closed_windows"], out["n_open_windows"]))
    if out["liveness"] is not None:
        lv = out["liveness"]
        print("  liveness (committed instrs before next overwrite): "
              "mean=%.2f median=%s min=%d max=%d"
              % (lv["mean"], lv["median"], lv["min"], lv["max"]))
    else:
        print("  liveness: n/a (no closed window)")
    print("  val_changes=%d arch_counts=%s class_counts=%s"
          % (out["val_changes"], out["arch_counts"], out["class_counts"]))
    if out["fanout_capped"] is not None:
        fc = out["fanout_capped"]["liveness"]
        print("  fanout_capped (cap=%d): mean=%.2f median=%s "
              "windows_hitting_cap=%d"
              % (out["window_cap"], fc["mean"], fc["median"],
                 out["fanout_capped"]["n_windows_hitting_cap"]))
    if "note" in out:
        print("  note: %s" % out["note"])
    print("  caveat: %s" % CAVEAT)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=2)
            f.write("\n")
        print("wrote %s" % args.json, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
