#!/usr/bin/env python3
"""ooo_observe — L0-L5 observation-chain composer for OOO FI runs (U10).

Reads one gem5 outdir and composes the observation record the P1 campaign
needs, layer by layer:

  L0  injection evidence      *_injections.log (runner-known names):
                              CHAOS_L0_FUNNEL lines (pinned counter format,
                              chaos_l0.hh), CHAOS_L0 read-back hit lines,
                              and the legacy `faults_injected: N` lines.
  L1  occupancy/IPC drift     micro_snap.csv.gz vs ref  (micro_diff)
  L2  RAT divergence          micro_snap.csv.gz vs ref  (micro_diff)
  L3  commit-stream classes   commit_trace.csv.gz vs ref (commit_diff)
  L4  first erroneous commit  commit_diff first_divergence (首检)
  L5  final outcome verdict   classify.classify_run + exit.rc

Design invariants:
  - One-way imports: ooo_observe -> classify/commit_diff/micro_diff. classify
    never imports ooo_observe (no cycle).
  - Verdict requires exit.rc: a run without exit.rc gets verdict=None
    (honest refusal) — never guessed from simout alone.
  - faults fed to classify_run use the strictest live evidence:
    funnel activated > l0 hit > legacy injected > 0, source recorded.
  - Abort legitimacy (chaos_l0.hh): Crash/Hang/SimulatorError with absent
    L0 evidence is NOT a conservation violation — abort paths run no exit
    callbacks (CHAOSPhysReg.cc l0Final()).
  - L1-L4 are reference-gated: without --ref-outdir they stay None.

CLI:
  python3 tools/ooo_observe.py OUTDIR [--golden HEX] [--ref-outdir DIR]
      [--oracle-kind K] [--oracle-tol N] [--timed-out] [--json]

Exit code: 0 when the observation completed (a conservation violation is
data, not tool failure); 2 on tool error (missing outdir etc.).
"""
import argparse
import gzip
import json
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from classify import (classify_run, check_conservation,
                      check_verdict_l0_consistency, extract_checksum)

# The injector-log names runner.py scans (tools/runner.py ~line 1483).
# Keep in sync — a log name not in this list is silently ignored by BOTH
# the runner and the observer, which is exactly the half-routed trap the
# repo discipline forbids.
KNOWN_LOG_NAMES = (
    "fault_injections.log", "main_mem_injections.log",
    "cache_injections.log", "rename_injections.log",
    "freelist_injections.log", "rob_injections.log",
    "iq_injections.log", "exec_injections.log",
    "fpu_injections.log", "l1d_fwd_injections.log",
    "bpu_injections.log", "addrpath_injections.log",
    "decode_injections.log", "ras_injections.log",
    "exmon_injections.log", "ptw_injections.log",
    "noc_injections.log", "chi_injections.log",
    "lsq_fwd_injections.log", "armtlb_injections.log",
    "sysreg_injections.log",
)

# chaos_l0.hh pinned formats:
#   CHAOS_L0_FUNNEL: <injector> attempted=N eligible=N injected=N activated=N
#   CHAOS_L0: <injector> target=<k> reads=<n> overwritten=<0|1> at=<cycle> hit=<0|1>
# legacy (CHAOSMem G5 evidence): faults_injected: N
RE_FUNNEL = re.compile(
    r"^CHAOS_L0_FUNNEL:\s+(\S+)\s+attempted=(\d+)\s+eligible=(\d+)"
    r"\s+injected=(\d+)\s+activated=(\d+)")
RE_L0 = re.compile(
    r"^CHAOS_L0:\s+(\S+)\s+target=\d+\s+reads=(\d+)\s+overwritten=[01]"
    r"\s+at=(\d+)\s+hit=([01])")
RE_LEGACY = re.compile(r"faults_injected:\s+(\d+)")


def _read_text(path):
    """Read a text file, transparently handling gzip (magic 1f 8b)."""
    with open(path, "rb") as f:
        head = f.read(2)
    if head == b"\x1f\x8b":
        with gzip.open(path, "rt", errors="replace") as f:
            return f.read()
    return Path(path).read_text(errors="replace")


def _blank_inj():
    return {"attempted": None, "eligible": None, "injected": None,
            "activated": None, "hit": 0, "legacy_injected": 0}


def collect_l0(outdir):
    """Scan the runner-known injection logs in outdir; return the L0 record.

    Counters accumulate across lines (an injector may append more than one
    funnel line across a run). Per-injector funnel counters stay None until
    a funnel line is seen (None = unknown, not zero — check_conservation
    skips unknowns). Legacy `faults_injected:` lines carry no injector name,
    so they are kept as a grand total only.
    """
    outdir = Path(outdir)
    injectors = {}
    totals = {"attempted": 0, "eligible": 0, "injected": 0, "activated": 0}
    legacy_injected_total = 0
    l0_hit_total = 0
    has_funnel = has_l0line = has_legacy = False
    logs_scanned = []
    for name in KNOWN_LOG_NAMES:
        p = outdir / name
        if not p.is_file():
            continue
        logs_scanned.append(name)
        for line in _read_text(p).splitlines():
            m = RE_FUNNEL.match(line)
            if m:
                has_funnel = True
                rec = injectors.setdefault(m.group(1), _blank_inj())
                for key, idx in (("attempted", 2), ("eligible", 3),
                                 ("injected", 4), ("activated", 5)):
                    n = int(m.group(idx))
                    rec[key] = n if rec[key] is None else rec[key] + n
                    totals[key] += n
                continue
            m = RE_L0.match(line)
            if m:
                has_l0line = True
                rec = injectors.setdefault(m.group(1), _blank_inj())
                hit = int(m.group(4))
                rec["hit"] += hit
                l0_hit_total += hit
                continue
            m = RE_LEGACY.search(line)
            if m:
                has_legacy = True
                legacy_injected_total += int(m.group(1))
    if has_funnel:
        evidence = "funnel"
    elif has_l0line:
        evidence = "l0"
    elif has_legacy:
        evidence = "legacy"
    else:
        evidence = "absent"
    # Strictest-live-evidence precedence for the classifier feed.
    if has_funnel:
        faults, source = totals["activated"], "funnel_activated"
    elif has_l0line:
        faults, source = l0_hit_total, "l0_hit"
    elif has_legacy:
        faults, source = legacy_injected_total, "legacy_injected"
    else:
        faults, source = 0, "none"
    return {
        "evidence": evidence,
        "injectors": injectors,
        "totals": totals,
        "l0_hit_total": l0_hit_total,
        "legacy_injected_total": legacy_injected_total,
        "faults_for_classify": faults,
        "faults_source": source,
        "logs_scanned": logs_scanned,
    }


def _compose_ref_layers(obs, outdir, ref_outdir, tick_tol, ipc_hide_pct):
    """L1-L4 need a no-fault reference outdir; both sides must have the
    matching artifact or the layer stays None (recorded, never guessed)."""
    ct_run = outdir / "commit_trace.csv.gz"
    ct_ref = ref_outdir / "commit_trace.csv.gz"
    if ct_run.is_file() and ct_ref.is_file():
        import commit_diff
        cres = commit_diff.compare(str(ct_ref), str(ct_run), tick_tol)
        aux = cres.get("aux") or {}
        obs["L4"] = cres.get("first_divergence")
        obs["L3"] = {
            "commit_verdict": cres.get("verdict"),
            "primary_class": cres.get("primary_class"),
            "primary_class_zh": cres.get("primary_class_zh"),
            "latency_seq": cres.get("latency_seq"),
            "divergence_counts": cres.get("divergence_counts"),
            "total_divergence_points": cres.get("total_divergence_points"),
            "ref_truncated": cres.get("ref_truncated"),
            "run_truncated": cres.get("run_truncated"),
            "tick_max_drift": aux.get("max_tick_drift"),
            "first_tick_over_tol_seq": aux.get("first_tick_over_tol_seq"),
        }
    ms_run = outdir / "micro_snap.csv.gz"
    ms_ref = ref_outdir / "micro_snap.csv.gz"
    if ms_run.is_file() and ms_ref.is_file():
        import micro_diff
        mres = micro_diff.diff(str(ms_ref), str(ms_run), ipc_hide_pct)
        obs["L1"] = {
            "no_divergence": mres.get("no_divergence"),
            "occ_dev_first_snap": mres.get("occ_dev_first_snap"),
            "ipc_dev_first_snap": mres.get("ipc_dev_first_snap"),
            "ipc_hide_pct": mres.get("ipc_hide_pct"),
        }
        obs["L2"] = {
            "rat_div_first_snap": mres.get("rat_div_first_snap"),
            "rat_div_first_snap_by_class": mres.get("rat_div_first_snap_by_class"),
            "hash_table_consistent": mres.get("hash_table_consistent"),
        }


def observe_run(outdir, golden=None, ref_outdir=None, oracle_kind="exact_hash",
                oracle_tol=0, timed_out=False, tick_tol=0, ipc_hide_pct=50.0):
    """Compose the full L0-L5 observation record for one outdir.

    Returns a dict (JSON-safe): outdir/returncode/checksum/golden/timed_out,
    L0 (collect_l0), L5 {verdict, reason, simfail}, L1-L4 (None without a
    ref), conservation_ok, violations. verdict is None when exit.rc is
    missing — honest refusal, the reason names it.
    """
    outdir = Path(outdir)
    l0 = collect_l0(outdir)
    simout = _read_text(outdir / "simout") if (outdir / "simout").is_file() else ""
    simerr = _read_text(outdir / "simerr") if (outdir / "simerr").is_file() else ""
    rc = None
    rc_path = outdir / "exit.rc"
    if rc_path.is_file():
        try:
            rc = int(rc_path.read_text().strip())
        except ValueError:
            rc = None
    checksum = extract_checksum(simout)
    verdict = reason = None
    if rc is None:
        reason = "no exit.rc in outdir — verdict refused (honest unknown)"
    else:
        verdict, reason = classify_run(
            simout, simerr, rc, l0["faults_for_classify"], golden,
            timed_out=timed_out, oracle_kind=oracle_kind, oracle_tol=oracle_tol)
    obs = {
        "outdir": str(outdir),
        "returncode": rc,
        "checksum": checksum,
        "golden": golden,
        "timed_out": timed_out,
        "L0": l0,
        "L5": {"verdict": verdict, "reason": reason,
               "simfail": verdict == "SimulatorError"},
        "L1": None, "L2": None, "L3": None, "L4": None,
    }
    ok1, viol1 = check_conservation(l0)
    ok2, viol2 = check_verdict_l0_consistency(verdict, l0, checksum, golden)
    obs["conservation_ok"] = bool(ok1 and ok2)
    obs["violations"] = viol1 + viol2
    if ref_outdir is not None:
        _compose_ref_layers(obs, outdir, Path(ref_outdir), tick_tol, ipc_hide_pct)
    return obs


def classify_ooo_run(outdir, golden=None, **kw):
    """Convenience wrapper: observe_run with the classification emphasis
    (the U10 fixture entry point)."""
    return observe_run(outdir, golden=golden, **kw)


def _report(obs):
    """Compact human-readable report (the JSON form carries everything)."""
    t = obs["L0"]["totals"]
    print("outdir: %s" % obs["outdir"])
    print("rc=%s checksum=%s golden=%s timed_out=%s"
          % (obs["returncode"], obs["checksum"] or "-", obs["golden"] or "-",
             obs["timed_out"]))
    print("L0 evidence=%s logs=[%s] attempted=%d eligible=%d injected=%d "
          "activated=%d faults_source=%s"
          % (obs["L0"]["evidence"], ",".join(obs["L0"]["logs_scanned"]),
             t["attempted"], t["eligible"], t["injected"], t["activated"],
             obs["L0"]["faults_source"]))
    for name in sorted(obs["L0"]["injectors"]):
        c = obs["L0"]["injectors"][name]
        print("L0   %s attempted=%s eligible=%s injected=%s activated=%s hit=%d"
              % (name, c["attempted"], c["eligible"], c["injected"],
                 c["activated"], c["hit"]))
    for layer in ("L1", "L2", "L3"):
        if obs[layer] is not None:
            print("%s: %s" % (layer, obs[layer]))
    if obs["L4"] is not None:
        fd = obs["L4"]
        print("L4 first_divergence: seq=%s class=%s level=%s detail=%s"
              % (fd.get("seq"), fd.get("class"), fd.get("level"), fd.get("detail")))
    l5 = obs["L5"]
    print("L5 verdict=%s simfail=%s" % (l5["verdict"], l5["simfail"]))
    print("L5 reason: %s" % l5["reason"])
    if obs["violations"]:
        for v in obs["violations"]:
            print("VIOLATION: %s" % v)
        print("conservation: BROKEN (%d)" % len(obs["violations"]))
    else:
        print("conservation: OK")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Compose the L0-L5 observation record for one gem5 outdir.")
    ap.add_argument("outdir", help="gem5 output directory")
    ap.add_argument("--golden", default=None,
                    help="expected 16-hex FINAL checksum of the no-fault run")
    ap.add_argument("--ref-outdir", default=None,
                    help="no-fault reference outdir (gates L1-L4)")
    ap.add_argument("--oracle-kind", default="exact_hash",
                    choices=["exact_hash", "array_hash", "per_element_diff",
                             "fp_ulp"])
    ap.add_argument("--oracle-tol", type=int, default=0)
    ap.add_argument("--timed-out", action="store_true",
                    help="the run hit its time limit (Hang semantics)")
    ap.add_argument("--tick-tol", type=int, default=0,
                    help="commit_diff tick tolerance (default 0)")
    ap.add_argument("--ipc-hide-pct", type=float, default=50.0,
                    help="micro_diff IPC noise gate (default 50.0)")
    ap.add_argument("--json", action="store_true",
                    help="print the full record as JSON")
    args = ap.parse_args(argv)
    d = Path(args.outdir)
    if not d.is_dir():
        print("ooo_observe: outdir not found: %s" % d, file=sys.stderr)
        return 2
    obs = observe_run(d, golden=args.golden, ref_outdir=args.ref_outdir,
                      oracle_kind=args.oracle_kind, oracle_tol=args.oracle_tol,
                      timed_out=args.timed_out, tick_tol=args.tick_tol,
                      ipc_hide_pct=args.ipc_hide_pct)
    if args.json:
        print(json.dumps(obs, ensure_ascii=False, indent=2, default=str))
    else:
        _report(obs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
