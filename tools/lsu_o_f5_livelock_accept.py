#!/usr/bin/env python3
"""Authorized bounded O-F5 Timeout/livelock acceptance — a SEPARATE axis.

This tool does NOT change chain admission (`lsu_chain_check.check_admission`)
and never turns a Timeout into Masked/Crash/contained/PASS.  It records the
2026-11-03 user ruling: a sustained retry/no-progress episode terminated at a
pre-set observation bound is a legitimate experimental result

    run_outcome = Timeout
    diagnosis   = guest_livelock   (only with sufficient causal evidence)

and keeps four axes distinct:

    run_outcome / chain_admission / evidence_integrity / experiment_acceptance

Acceptance is strict and per-sample.  Generic admission is untouched, so no
other Timeout is auto-certified.

Usage:
  python3 tools/lsu_o_f5_livelock_accept.py \
    --diag-dir /home/sdc/gem5-fi-ding/runs/lsu/r6_o_unit/f5_diag_20261103_r2 \
    --run-id O02-F5-W7 --seed 1 --out-json .../acceptance.json

Exit: 0 = AUTHORIZED_TIMEOUT_LIVELOCK, 1 = NOT_ACCEPTED (reasons printed).
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lsu_chain_check as CC  # noqa: E402
import lsu_prop_fields as PF  # noqa: E402

EVENT_RE = re.compile(r"(\w+)=([^\s]*)")
DISPOSAL_KINDS = {"squash_discarded", "squash_masked", "replay", "mask"}
DEFAULT_GOLDEN_TICKS_PER_SEC = 21_130_000.0  # measured no-fault golden rate


def read_events(path):
    """Return (events, truncated). Raises on gzip errors after recording them."""
    events = []
    with gzip.open(path, "rt") as f:
        for line in f:
            if line.startswith("PROP-EVT:"):
                events.append(dict(EVENT_RE.findall(line[9:])))
    return events


def gzip_eof(path):
    try:
        with gzip.open(path, "rt") as f:
            f.read()
        return True, ""
    except Exception as exc:  # noqa: BLE001 - report, never hide
        return False, f"{type(exc).__name__}: {exc}"


def parse_stats(path):
    out = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"^(simTicks|simInsts|finalTick)\s+(\d+)", line)
            if m:
                out[m.group(1)] = int(m.group(2))
            m = re.match(r"^board\.processor\.cores(\d+)\.core\.instsIssued\s+(\d+)", line)
            if m:
                out.setdefault("core_issued", {})[m.group(1)] = int(m.group(2))
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def analyse(seed_dir, cell_results_path, started, ended, golden_ticks_per_sec,
            min_speed_fraction, min_injections, min_failures, max_gap_factor):
    reasons = []
    axes = {}
    evidence = {}

    prop_evt = os.path.join(seed_dir, "prop_evt.txt.gz")
    prop_trace = os.path.join(seed_dir, "prop_trace.csv.gz")
    stats_path = os.path.join(seed_dir, "stats.txt")
    term_path = os.path.join(seed_dir, "board.terminal")
    err_path = os.path.join(seed_dir, "run.err")
    chain_path = os.path.join(seed_dir, "chain_report.json")
    inj_path = os.path.join(seed_dir, "exmon_injections.log")

    # ---- evidence integrity -------------------------------------------------
    ok_evt, evt_err = gzip_eof(prop_evt)
    ok_trace, trace_err = gzip_eof(prop_trace) if os.path.exists(prop_trace) else (True, "absent")
    stats = parse_stats(stats_path) if os.path.exists(stats_path) else {}
    stats_ok = all(stats.get(k, 0) > 0 for k in ("simTicks", "simInsts", "finalTick"))
    err = open(err_path, errors="replace").read() if os.path.exists(err_path) else ""
    timeout_graceful = ("TIMEOUT triggered=True" in err and "graceful=True" in err
                        and "signal=None" in err)
    chain = json.load(open(chain_path)) if os.path.exists(chain_path) else {}
    # [R6-O-F5-CAP 2026-11-03] `lsu_prop_fields.read_stream` keeps at most
    # EVENT_CAP events and sets truncated=True at the cap.  The campaign then
    # labels that as "incomplete gzip stream ... killed mid-write", which is
    # wrong when the raw gzip is complete.  Distinguish the two:
    #   raw gzip complete + chain event_count == EVENT_CAP -> analysis cap only.
    event_cap = getattr(PF, "EVENT_CAP", 200000)
    analysis_capped = (chain.get("truncated") is True and ok_evt
                       and chain.get("event_count") == event_cap)
    raw_ok = ok_evt and ok_trace and stats_ok and timeout_graceful
    chain_ok = (chain.get("truncated") is False) or analysis_capped
    evidence = {
        "prop_evt_gzip_eof": ok_evt, "prop_evt_error": evt_err,
        "prop_trace_gzip_eof": ok_trace, "prop_trace_error": trace_err,
        "stats_present_and_nonzero": stats_ok,
        "run_err_timeout_graceful": timeout_graceful,
        "chain_report_truncated": chain.get("truncated"),
        "chain_report_truncation_reason": chain.get("truncation_reason"),
        "chain_event_count": chain.get("event_count"),
        "analysis_event_cap": event_cap,
        "analysis_capped": analysis_capped,
    }
    if not (raw_ok and chain_ok):
        reasons.append("evidence_integrity_incomplete")
    if not raw_ok:
        integrity = "INCOMPLETE"
    elif analysis_capped:
        integrity = "COMPLETE_RAW_ANALYSIS_CAPPED"
    else:
        integrity = "COMPLETE"
    axes["evidence_integrity"] = integrity

    # ---- run outcome --------------------------------------------------------
    cell = json.load(open(cell_results_path)) if os.path.exists(cell_results_path) else {}
    classes = cell.get("classes", {})
    activated = cell.get("activated") or 0
    timeout_n = classes.get("Timeout", 0)
    other = {k: v for k, v in classes.items() if k != "Timeout" and v}
    run_outcome = "Timeout" if timeout_n > 0 else (cell.get("outcome") or "unknown")
    axes["run_outcome"] = run_outcome
    if not (timeout_n > 0 and not other):
        reasons.append("run_outcome_not_pure_timeout")

    # ---- events -------------------------------------------------------------
    events = read_events(prop_evt) if ok_evt else []
    faults = {}
    for e in events:
        fid = e.get("fault_id", "")
        if fid and fid != "0":
            faults.setdefault(fid, []).append(e)
    injects = [e for e in events if e.get("kind") == "inj"]
    stxrs = [e for e in events if e.get("kind") == "exmon_stxr"]
    rmws = [e for e in events if e.get("kind") == "exmon_rmw"]
    ends = [int(e["tick"]) for e in events if e.get("kind") == "chain_end"]
    final_tick = stats.get("finalTick", 0)

    consumed = []
    discarded = []
    pending = []
    for fid, evs in faults.items():
        kinds = {e.get("kind") for e in evs}
        if "exmon_stxr" in kinds:
            consumed.append(fid)
        elif kinds & DISPOSAL_KINDS:
            discarded.append(fid)
        elif "inj" in kinds:
            pending.append(fid)

    fail_states = [e.get("state_after") for e in stxrs]
    failures = sum(1 for s in fail_states if s in ("fail_retry", "fail"))
    successes = sum(1 for s in fail_states if s in ("success", "match_success"))
    rmw_fail = sum(1 for e in rmws if e.get("state_after") == "mismatch_fail")

    fail_ticks = sorted(int(e["tick"]) for e in stxrs
                        if e.get("state_after") in ("fail_retry", "fail"))
    inj_ticks = sorted(int(e["tick"]) for e in injects)
    timing = {}
    if len(fail_ticks) >= 2 and inj_ticks and final_tick:
        gaps = [b - a for a, b in zip(fail_ticks, fail_ticks[1:])]
        med = sorted(gaps)[len(gaps) // 2]
        span = fail_ticks[-1] - inj_ticks[0]
        window = final_tick - inj_ticks[0]
        timing = {
            "first_injection_tick": inj_ticks[0],
            "first_failure_tick": fail_ticks[0],
            "last_failure_tick": fail_ticks[-1],
            "final_tick": final_tick,
            "failure_span_ticks": span,
            "window_ticks": window,
            "span_fraction": round(span / window, 6) if window > 0 else 0.0,
            "gap_median": med, "gap_max": max(gaps),
            "tail_distance_ticks": final_tick - fail_ticks[-1],
        }

    # ---- guest terminal -----------------------------------------------------
    term = open(term_path, errors="replace").read() if os.path.exists(term_path) else ""
    guest_no_final = ("FINAL=" not in term and "LITMUS free end" not in term
                      and "violations=" not in term)
    reached_atomic = "LITMUS free atomic" in term

    # ---- both cores active / host speed ------------------------------------
    core_issued = stats.get("core_issued", {})
    both_cores = all(core_issued.get(str(i), 0) > 0 for i in (0, 1))
    wall = (ended - started) if (started and ended and ended > started) else 0
    speed = (stats.get("simTicks", 0) / wall) if wall else 0.0
    speed_ok = bool(wall) and speed >= golden_ticks_per_sec * min_speed_fraction

    # ---- causal diagnosis ---------------------------------------------------
    causal = (
        len(injects) >= min_injections
        and failures >= min_failures
        and rmw_fail >= min_failures
        and successes == 0
        and not pending
        and reached_atomic and guest_no_final
        and bool(timing)
        and timing.get("span_fraction", 0.0) >= 0.5
        and timing.get("gap_max", 0) <= max(1, timing.get("gap_median", 1)) * max_gap_factor
        and bool(ends) and all(t == final_tick for t in ends)
        and both_cores and speed_ok
    )
    axes["diagnosis"] = "guest_livelock" if causal else "suspected_livelock"
    if not causal:
        reasons.append("causal_evidence_insufficient")
        if pending:
            reasons.append("unconsumed_fault_pending")
        if successes:
            reasons.append("successful_stxr_after_injection")
        if not both_cores:
            reasons.append("both_cores_not_proven_active")
        if not speed_ok:
            reasons.append("host_speed_not_comparable_to_golden")
        if not guest_no_final:
            reasons.append("guest_reached_final")
        if ends and any(t != final_tick for t in ends):
            reasons.append("chain_end_not_at_boundary")

    # ---- chain accounting (not used to claim full containment) -------------
    # If only the analyzer cap truncated (raw gzip complete), re-derive every
    # fault verdict from the full raw stream with the same authoritative checker.
    chain_source = "capped_report"
    rep_faults = chain.get("faults", {})
    if analysis_capped and ok_evt:
        try:
            full = CC.check_chain(events, oracle_outcome=chain.get("oracle_outcome"))
            rep_faults = full.get("faults", {})
            chain_source = "recomputed_full_stream"
        except Exception as exc:  # noqa: BLE001 - reject loudly, never guess
            reasons.append("chain_recompute_failed")
            evidence["chain_recompute_error"] = f"{type(exc).__name__}: {exc}"
            axes["evidence_integrity"] = "INCOMPLETE"
    terms = {}
    unresolved = []
    for fid, v in rep_faults.items():
        t = v.get("terminal", "unknown")
        terms[t] = terms.get(t, 0) + 1
        if t != "detected_contained":
            unresolved.append({"fault_id": fid, "terminal": t,
                               "provable_to": v.get("provable_to")})
    axes["chain_admission"] = {
        "contained_detected": terms.get("detected_contained", 0),
        "unresolved": len(unresolved),
        "unconsumed_discarded": len(discarded),
        "unconsumed_pending": len(pending),
        "terminal_distribution": terms,
        "source": chain_source,
        "reported_fault_count": len(rep_faults),
        "note": "top-level admitted/certified are reported, not used for full-containment claims",
    }

    accepted = (
        str(axes.get("evidence_integrity", "")).startswith("COMPLETE")
        and run_outcome == "Timeout"
        and axes.get("diagnosis") == "guest_livelock"
        and not pending
    )
    axes["experiment_acceptance"] = ("AUTHORIZED_TIMEOUT_LIVELOCK"
                                     if accepted else "NOT_ACCEPTED")

    return {
        "run_id": None, "seed": None, "diag_dir": seed_dir,
        "axes": axes,
        "evidence": evidence,
        "counts": {
            "injections": len(injects), "consumed": len(consumed),
            "failures": failures, "rmw_mismatch_fail": rmw_fail,
            "successes_after_injection": successes,
            "squash_discarded": len(discarded),
            "unconsumed_pending": len(pending),
            "faults": len(faults), "chain_end_events": len(ends),
            "cell_activated": activated, "cell_timeout": timeout_n,
            "injection_log_lines": sum(1 for _ in open(inj_path)) if os.path.exists(inj_path) else None,
        },
        "unconsumed_discarded_faults": sorted(discarded, key=int)[:50],
        "unconsumed_pending_faults": sorted(pending, key=int)[:50],
        "unresolved_chain_faults": unresolved[:50],
        "timing": timing,
        "golden_comparison": {
            "wall_seconds": wall, "sim_ticks": stats.get("simTicks", 0),
            "ticks_per_sec": round(speed), "golden_ticks_per_sec": golden_ticks_per_sec,
            "speed_fraction": round(speed / golden_ticks_per_sec, 4) if golden_ticks_per_sec else None,
            "core_issued": core_issued, "both_cores_active": both_cores,
        },
        "guest_terminal": {
            "reached_atomic_phase": reached_atomic, "no_final": guest_no_final,
            "tail": term.strip().splitlines()[-1] if term.strip() else "",
        },
        "top_level_chain_flags": {
            "admitted": chain.get("admitted"), "certified": chain.get("certified"),
            "terminal": chain.get("terminal"), "provable_to": chain.get("provable_to"),
        },
        "reasons": reasons,
        "generic_admission_unchanged": True,
        "promoted_to_pass": False,
        "tool": "tools/lsu_o_f5_livelock_accept.py",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--diag-dir", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--out-json", default="")
    ap.add_argument("--golden-ticks-per-sec", type=float, default=DEFAULT_GOLDEN_TICKS_PER_SEC)
    ap.add_argument("--min-speed-fraction", type=float, default=0.70)
    ap.add_argument("--min-injections", type=int, default=50)
    ap.add_argument("--min-failures", type=int, default=50)
    ap.add_argument("--max-gap-factor", type=float, default=20.0)
    a = ap.parse_args()

    cell_dir = os.path.join(a.diag_dir, a.run_id)
    seed_dir = os.path.join(cell_dir, f"seed{a.seed}")
    cell_results = os.path.join(cell_dir, "cell_results.json")
    started = ended = 0
    for name, attr in (("started_at_epoch", "started"), ("ended_at_epoch", "ended")):
        p = os.path.join(a.diag_dir, name)
        if os.path.exists(p):
            val = int(open(p).read().strip() or 0)
            if attr == "started":
                started = val
            else:
                ended = val
    res = analyse(seed_dir, cell_results, started, ended,
                  a.golden_ticks_per_sec, a.min_speed_fraction,
                  a.min_injections, a.min_failures, a.max_gap_factor)
    res["run_id"] = a.run_id
    res["seed"] = a.seed
    res["diag_dir"] = a.diag_dir
    print(json.dumps({"run_id": a.run_id, "seed": a.seed,
                      "axes": res["axes"], "counts": res["counts"],
                      "reasons": res["reasons"]}, ensure_ascii=False))
    if a.out_json:
        os.makedirs(os.path.dirname(a.out_json) or ".", exist_ok=True)
        with open(a.out_json, "w") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    return 0 if res["axes"]["experiment_acceptance"] == "AUTHORIZED_TIMEOUT_LIVELOCK" else 1


if __name__ == "__main__":
    sys.exit(main())
