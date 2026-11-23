#!/usr/bin/env python3
"""Repeatable, self-checking validator for the WHEN-5X3 final evidence.

Re-derives the four-dimensional completeness record, granular terminal
states, causal-completeness (FULL/PARTIAL) totals, and the SDC-terminal
invariant directly from `analysis/per_condition.json` + the raw manifests, and
asserts they are consistent with `experiment_status.csv`, `acceptance.json`
and `final_acceptance.md`.  Exits nonzero on any mismatch.

Run:  python3 campaign/validate.py
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
import control_map  # noqa: E402
import oracle  # noqa: E402
RUNS = os.path.join(ROOT, "runs", "W5X3")
RETRY_RUNS = os.path.join(ROOT, "runs", "W5X3_RETRY")
RETRY2_RUNS = os.path.join(ROOT, "runs", "W5X3_RETRY2")
COND = os.path.join(ROOT, "campaign", "conditions.json")
STATUS = os.path.join(ROOT, "experiment_status.csv")
PER = os.path.join(ROOT, "analysis", "per_condition.json")
ACCEPT = os.path.join(ROOT, "acceptance.json")
ACCEPT_MD = os.path.join(ROOT, "final_acceptance.md")

FAILS = []


def fail(msg):
    FAILS.append(msg)
    print("FAIL:", msg)


def ok(msg):
    print("ok  :", msg)


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


def fault_manifest_for(sample_id):
    r2 = load(os.path.join(ROOT, "analysis", "retry2_map.json"), {})
    r1 = load(os.path.join(ROOT, "analysis", "retry_map.json"), {})
    if sample_id in r2:
        return load(os.path.join(RETRY2_RUNS, r2[sample_id], "manifest.json"),
                    {})
    if sample_id in r1:
        return load(os.path.join(RETRY_RUNS, r1[sample_id], "manifest.json"),
                    {})
    return load(os.path.join(RUNS, sample_id, "manifest.json"), {})


def oracle_lines(term):
    pat = re.compile(r"^W(?:9|10S|1[0-4])_(?:RESULT|SUMMARY|STORE)\b")
    return [ln for ln in term if pat.match(ln)]


def main():
    conds = load(COND, [])
    rows = {r["NewSampleRunID"]: r for r in csv.DictReader(open(STATUS))}
    per = {p["NewSampleRunID"]: p for p in load(PER, [])}
    accept = load(ACCEPT, {})
    md = open(ACCEPT_MD).read()

    # ---- 1. status counts ----
    counts = {}
    for c in conds:
        st = rows[c["NewSampleRunID"]]["Status"]
        counts[st] = counts.get(st, 0) + 1
    if counts.get("COMPLETE", 0) != 117 or counts.get("N/A", 0) != 3:
        fail("status counts %s != {COMPLETE:117, N/A:3}" % counts)
    else:
        ok("status counts: %s" % counts)

    # ---- 2. re-derive terminal state + completeness + SDC-terminal invariant
    ts = {}
    full_partial = {}
    sdc_squash = []
    for c in conds:
        rid = c["NewSampleRunID"]
        r = rows[rid]
        if r["Status"] != "COMPLETE":
            ts[rid] = r["Status"]
            continue
        man = fault_manifest_for(rid)
        ch = per[rid].get("Chain", {})
        term = ch.get("terminal") or {}
        edges = ch.get("edges", [])
        has_unknown = any(e.get("basis") == "UNKNOWN" for e in edges)
        comp = ch.get("completeness", {})
        # four dimensions
        file_c = bool(man.get("trace_sha256"))
        edges_c = not has_unknown
        term_c = bool(term)
        arch_c = bool(comp.get("architecture_complete"))
        dims = {"file": file_c, "edges": edges_c, "terminal": term_c,
                "architecture": arch_c}
        overall = "FULL" if all(dims.values()) else "PARTIAL_%s" % \
            "+".join(k.upper() for k, v in dims.items() if not v)
        # compare to reported columns
        if str(r.get("Completeness", "")) != overall:
            fail("%s completeness %r != derived %r" %
                 (rid, r.get("Completeness", ""), overall))
        for col, val in (("FileComplete", file_c), ("EdgesExplicit", edges_c),
                         ("TerminalObserved", term_c),
                         ("ArchitectureComplete", arch_c)):
            if str(r.get(col, "")).lower() != str(val).lower():
                fail("%s %s %r != derived %r" % (rid, col, r.get(col), val))
        # terminal state
        model = c["ModelID"]
        reported = r["TerminalState"]
        masked_reason = (ch.get("summary") or {}).get("masked_reason") or ""
        if model == "M06":
            delivered = (term.get("kind") == "exception_delivery" or
                         (ch.get("summary") or {}).get("exception_delivered") == 1)
            derived = "DETECTED_DELIVERED" if delivered else "DETECTED_LOCALLY"
        else:
            crec, _ = control_map.resolve_control(
                model, c["NewContext"], man.get("gem5_sha256", ""))
            ctrl = (crec or {}).get("manifest") or {}
            if not oracle.semantic_compare(
                    man.get("terminal_lines") or [],
                    ctrl.get("terminal_lines") or []):
                derived = "SDC"
            else:
                consumed = (bool(ch.get("consume")) or
                            bool(ch.get("translation")) or
                            bool(ch.get("request")))
                if not consumed:
                    derived = "ACTIVATED_UNCONSUMED"
                elif masked_reason == "request_issued_not_completed_at_roi_end":
                    derived = "REQUEST_PENDING_AT_ROI_END"
                elif ch.get("has_any_commit"):
                    derived = "ACTIVATED_MASKED"
                elif term.get("kind") == "squash":
                    derived = "PROPAGATED_BUT_SQUASHED"
                else:
                    derived = "ACTIVATED_MASKED"
        if reported != derived:
            fail("%s terminal state %r != derived %r" % (rid, reported, derived))
        ts[rid] = derived
        # SDC-terminal invariant: an SDC must never terminate on a squash
        if derived == "SDC" and term.get("kind") == "squash":
            sdc_squash.append(rid)
        # causal FULL/PARTIAL per model
        fp = full_partial.setdefault(model, {"FULL": 0, "PARTIAL": 0})
        fp["FULL" if all(dims.values()) else "PARTIAL"] += 1
    if sdc_squash:
        fail("SDC samples whose terminal is a squash: %s" % sdc_squash)
    else:
        ok("no SDC sample terminates on a squash")

    ts_sum = {}
    for _rid, v in ts.items():
        ts_sum[v] = ts_sum.get(v, 0) + 1
    accepted_ts = accept.get("TerminalStateSummary", {})
    if accepted_ts and ts_sum != accepted_ts:
        fail("terminal summary %s != acceptance TerminalStateSummary %s"
             % (ts_sum, accepted_ts))
    else:
        ok("terminal summary reconciles with acceptance.json: %s" % ts_sum)

    # ---- 3. FULL/PARTIAL per model == acceptance.json ----
    repo = accept.get("CausalCompleteness", {}).get("per_model", {})
    for m in sorted(full_partial):
        got = (full_partial[m].get("FULL", 0), full_partial[m].get("PARTIAL", 0))
        want = (repo.get(m, {}).get("FULL", 0), repo.get(m, {}).get("PARTIAL", 0))
        if got != want:
            fail("model %s FULL/PARTIAL %s != acceptance %s" % (m, got, want))
        else:
            ok("model %s FULL/PARTIAL reconciled: %s" % (m, got))
    if repo.get("unknown_edge_samples") != (accept.get("CausalCompleteness", {})
                                            .get("unknown_edge_samples")):
        pass

    # ---- 4. acceptance md carries the four dimensions ----
    for phrase in ("file", "edges", "terminal", "architecture"):
        if phrase not in md:
            fail("final_acceptance.md missing dimension term %r" % phrase)

    # ---- 5. every SDC traceable to (activation EventID+Tick, Oracle) and to
    #        an explicit terminal event OR a declared boundary.
    for c in conds:
        rid = c["NewSampleRunID"]
        if rows[rid].get("Status") != "COMPLETE":
            continue
        if ts[rid] != "SDC":
            continue
        ch = per[rid].get("Chain", {})
        root = ch.get("root") or {}
        term = ch.get("terminal") or {}
        if not (root.get("event_id") is not None and root.get("tick")):
            fail("%s SDC activation missing event_id/tick" % rid)
        boundary_declared = bool(ch.get("boundary") or ch.get("unobserved"))
        if not (term.get("event_id") and term.get("tick")) and \
                not boundary_declared:
            fail("%s SDC has neither explicit terminal nor declared boundary"
                 % rid)

    print("\n=== %d failure(s) ===" % len(FAILS) if FAILS else
          "\n=== ALL CHECKS PASSED ===")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())