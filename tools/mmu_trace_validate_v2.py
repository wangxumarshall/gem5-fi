#!/usr/bin/env python3
"""MMU unified trace validator v2 (Phase 2).

Extends the Phase-1 validator (tools/mmu_trace_validate.py, preserved) with
per-translation and per-context completeness, representative-chain, target
event coverage, terminal coverage and missing-causal-edge reports.

The tool never invents events: it parses the native CHAOSPropagation
PROP-EVT stream, rebuilds the explicit ParentEventID graph, and judges each
target translation against the path its REAL terminal state requires.

A chain that ends in commit must have the full commit path; a chain that ends
in squash is judged up to squash; a chain whose walk is still in flight at
ROI end is judged only up to the last real event (PARTIAL, never COMPLETE).

Usage:
  mmu_trace_validate_v2.py --input prop_evt.txt.gz --workload W9 \
    --model CONTROL --va 0x4000000000 \
    --csv-prefix out/per_translation --report-json out/report.json
"""

import argparse
import csv
import gzip
import json
import sys
from collections import Counter, defaultdict

PROP_PREFIX = "PROP-EVT:"


def open_maybe_gz(path):
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic == b"\x1f\x8b":
        return gzip.open(path, "rt", errors="replace")
    return open(path, "r", errors="replace")


def parse_line(line):
    line = line.strip()
    if not line.startswith(PROP_PREFIX):
        return None
    body = line[len(PROP_PREFIX):].strip()
    out = {}
    for token in body.split():
        if "=" not in token:
            continue
        key, val = token.split("=", 1)
        out[key] = val
    return out


def load_events(path):
    events, bad = [], 0
    with open_maybe_gz(path) as fh:
        for line in fh:
            ev = parse_line(line)
            if ev is None:
                continue
            try:
                ev["event_id"] = int(ev.get("event_id", ""))
            except ValueError:
                bad += 1
                continue
            events.append(ev)
    return events, bad


def to_int(ev, key, default=0):
    val = ev.get(key, "")
    if val == "":
        return default
    try:
        return int(val, 0)
    except ValueError:
        return default


def kind(ev):
    return ev.get("kind", "")


def hexaddr(val):
    if not val:
        return None
    try:
        return int(val, 16) if not val.startswith("0x") else int(val, 0)
    except ValueError:
        return None


MODELS = {
    "W9": {
        "CONTROL": [
            "tlbi_issue", "tlbi_match", "tlbi_invalidate",
            "translation_start", "tlb_lookup_miss", "ptw_start",
            "pte_read", "pte_decode", "tlb_fill", "tlb_entry_insert",
            "tlb_lookup_hit", "permission_eval", "translation_result",
            "lsu_request", "memory_response", "rf_writeback", "commit",
        ],
        "M01": [
            "mmu_fault_arm", "tlbi_issue", "tlbi_match", "tlbi_suppressed",
            "translation_start", "tlb_lookup_miss", "tlb_lookup_hit",
            "tlb_entry_insert", "permission_eval", "translation_result",
            "lsu_request", "memory_response", "rf_writeback", "commit",
            "mmu_fault_disarm",
        ],
    },
    "W10": {
        "CONTROL": [
            "translation_start", "tlb_lookup_miss", "ptw_start", "pte_read",
            "pte_decode", "tlb_fill", "tlb_entry_insert", "tlb_lookup_hit",
            "permission_eval", "translation_result", "lsu_request",
            "memory_response", "rf_writeback", "commit",
        ],
        "M02": [
            "translation_start", "tlb_lookup_miss", "ptw_start", "pte_read",
            "pte_decode", "tlb_fill", "refill_pfn_corrupt",
            "tlb_entry_insert", "tlb_lookup_hit", "permission_eval",
            "translation_result", "lsu_request", "memory_response",
            "rf_writeback", "commit",
        ],
    },
}

# Expected direct-causal edges, conditioned on the branch the chain took.
COMMON_EDGES = [
    ("translation_start", None),          # first lookup; either miss or hit
    ("permission_eval", "translation_result"),
    ("translation_result", "lsu_request"),
    ("lsu_request", "memory_response"),
    ("memory_response", "rf_writeback"),
]
WALK_EDGES = [
    ("ptw_start", "pte_read"),
    ("pte_read", "pte_decode"),
    ("pte_decode", "tlb_fill"),
    ("tlb_fill", "tlb_entry_insert"),
]
TLBI_EDGES = [
    ("tlbi_issue", "tlbi_match"),
]


def expected_path(chain_kinds):
    """The path the chain's observed branch/terminal requires.

    Branch is selected from REAL observed events, never assumed: a stale
    l2_shared hit has no walk; a cold miss has one.
    """
    exp = ["translation_start"]
    exp.append("tlb_lookup_hit" if "tlb_lookup_hit" in chain_kinds
               and "ptw_start" not in chain_kinds
               else "tlb_lookup_miss")
    if "ptw_start" in chain_kinds:
        exp += ["ptw_start", "pte_read", "pte_decode", "tlb_fill",
                "tlb_entry_insert"]
    exp += ["tlb_lookup_hit", "permission_eval", "translation_result",
            "lsu_request", "memory_response", "rf_writeback"]
    if "squash" in chain_kinds:
        exp.append("squash")
    elif "commit" in chain_kinds:
        exp.append("commit")
    # If the chain has no terminal, only the observed prefix is required.
    if "commit" not in chain_kinds and "squash" not in chain_kinds:
        exp = [k for k in exp if k in chain_kinds] or exp
    return exp


def build_chains(events, by_id, va_points):
    in_scope = []
    for ev in events:
        v = hexaddr(ev.get("va", ""))
        if v is None:
            continue
        if any((v >> 12) == (p >> 12) for p in va_points):
            in_scope.append(ev)

    groups = defaultdict(list)
    for ev in in_scope:
        tid = ev.get("translation_id", "")
        if tid and tid != "0":
            groups["tid:" + tid].append(ev)
        elif ev.get("unique_request_id", "") not in ("", "0"):
            groups["uid:" + ev["unique_request_id"]].append(ev)

    seq_to_groups = defaultdict(set)
    for key, evs in groups.items():
        for ev in evs:
            seq = ev.get("dyn_inst_seq", "")
            if seq not in ("", "0"):
                seq_to_groups[seq].add(key)

    chains = []
    for key, evs in groups.items():
        chain_evs = list(evs)
        seen = {e["event_id"] for e in evs}
        # Explicit ancestors only (no tick-order inference).
        for ev in evs:
            p = ev.get("parent_event_id", "")
            hops = 0
            while p and int(p) in by_id and int(p) not in seen and hops < 128:
                anc = by_id[int(p)]
                chain_evs.append(anc)
                seen.add(anc["event_id"])
                p = anc.get("parent_event_id", "")
                hops += 1
        # Instruction-keyed descendants (commit/squash carry no VA).
        seqs = {e.get("dyn_inst_seq") for e in evs
                if e.get("dyn_inst_seq", "") not in ("", "0")}
        for ev in events:
            if ev["event_id"] in seen:
                continue
            if kind(ev) in ("rf_writeback", "commit", "squash", "consumer") \
                    and ev.get("dyn_inst_seq", "") in seqs:
                chain_evs.append(ev)
                seen.add(ev["event_id"])

        # FaultID is an explicit chain identity (design §8.3), not a tick
        # guess: every event tagged with the same injected ptag belongs to
        # this chain, including the latch lifecycle events (fault_arm /
        # tlbi_suppressed / disarm / activation) that carry no translation id.
        chain_fault = next((e.get("fault_id") for e in chain_evs
                            if e.get("fault_id", "") not in ("", "0")), "0")
        if chain_fault != "0":
            for ev in events:
                if ev["event_id"] in seen:
                    continue
                if ev.get("fault_id", "") == chain_fault:
                    chain_evs.append(ev)
                    seen.add(ev["event_id"])

        kinds = [kind(e) for e in chain_evs]
        asid = next((e.get("asid") for e in evs
                     if e.get("asid", "") != ""), "")
        va = next((e.get("va") for e in evs if e.get("va", "")), "")
        seq = next((e.get("dyn_inst_seq") for e in evs
                    if e.get("dyn_inst_seq", "") not in ("", "0")), "")
        tid = next((e.get("translation_id") for e in evs
                    if e.get("translation_id", "") not in ("", "0")), "")
        fault_id = chain_fault
        if "commit" in kinds:
            terminal = "commit"
        elif "squash" in kinds:
            terminal = "squash"
        elif "translation_result" in kinds:
            terminal = "no_terminal_after_result"
        elif "tlb_lookup_miss" in kinds or "ptw_start" in kinds:
            terminal = "walk_in_flight_at_roi_end"
        else:
            terminal = "no_target_events"

        exp = expected_path(kinds)
        missing = [k for k in exp if k not in kinds]
        observed_set = set(kinds)
        if not missing:
            completeness = "COMPLETE"
        elif observed_set & set(exp):
            completeness = "PARTIAL"
        else:
            completeness = "INCOMPLETE"

        # Missing causal edges: for each expected `to` present, require a
        # direct parent of the expected `from` kind.
        edges = []
        edge_set = TLBI_EDGES + COMMON_EDGES
        # Walk edges are only expected when the chain actually took a walk
        # (a stale l2_shared hit has no PTW at all).
        if "ptw_start" in kinds:
            edge_set = edge_set + WALK_EDGES
        for frm, to in edge_set:
            if to is not None and to not in kinds:
                continue
            if frm == "translation_start" and to is None:
                continue
            if to is None:
                continue
            if to not in kinds:
                continue
            ok = False
            for ev in chain_evs:
                if kind(ev) != to:
                    continue
                p = ev.get("parent_event_id", "")
                if p and int(p) in by_id and kind(by_id[int(p)]) == frm:
                    ok = True
                    break
            if not ok:
                edges.append("%s->%s" % (frm, to))
        # Fault-specific edges.
        if "mmu_fault_arm" in kinds and "tlbi_match" in kinds:
            if not any(kind(e) == "tlbi_match"
                       and kind(by_id.get(to_int(e, "parent_event_id"), {})) ==
                       "mmu_fault_arm" for e in chain_evs):
                edges.append("mmu_fault_arm->tlbi_match")
        if "refill_pfn_corrupt" in kinds and "tlb_entry_insert" in kinds:
            if not any(kind(e) == "tlb_entry_insert"
                       and kind(by_id.get(to_int(e, "parent_event_id"), {})) in
                       ("refill_pfn_corrupt", "tlb_fill", "memory_response")
                       for e in chain_evs):
                edges.append("refill_pfn_corrupt->tlb_entry_insert")

        chains.append({
            "group": key, "translation_id": tid, "dyn_inst_seq": seq,
            "asid": asid, "va": va, "fault_id": fault_id,
            "terminal": terminal, "event_count": len(chain_evs),
            "observed_kinds": sorted(observed_set),
            "expected_kinds": exp, "missing_kinds": missing,
            "missing_edges": edges, "completeness": completeness,
            "has_terminal": terminal in ("commit", "squash"),
        })
    chains.sort(key=lambda c: c["group"])
    return chains


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--workload", required=True, choices=["W9", "W10"])
    ap.add_argument("--model", default="CONTROL",
                    choices=["CONTROL", "M01", "M02"])
    ap.add_argument("--va", action="append", default=[],
                    help="target VA (page granularity), repeatable")
    ap.add_argument("--csv-prefix", default="")
    ap.add_argument("--report-json", default="")
    ap.add_argument("--jsonl", default="")
    args = ap.parse_args()

    events, bad = load_events(args.input)
    by_id = {}
    dup = []
    for ev in events:
        if ev["event_id"] in by_id:
            dup.append(ev["event_id"])
        by_id[ev["event_id"]] = ev

    integrity_errors = []
    for ev in events:
        p = ev.get("parent_event_id", "")
        if p == "":
            continue
        if int(p) not in by_id:
            integrity_errors.append("event %s (%s) parent %s missing" %
                                    (ev["event_id"], kind(ev), p))
        elif int(p) == ev["event_id"]:
            integrity_errors.append("event %s self-parent" %
                                    (ev["event_id"],))
        else:
            pt = to_int(by_id[int(p)], "tick")
            ct = to_int(ev, "tick")
            if pt and ct and ct < pt:
                integrity_errors.append(
                    "event %s (%s) tick %s < parent tick %s" %
                    (ev["event_id"], kind(ev), ct, pt))
    integrity = "PASS" if not integrity_errors and not dup else "FAIL"

    va_points = [int(v, 0) for v in args.va]
    chains = build_chains(events, by_id, va_points)

    # Per-translation CSV.
    if args.csv_prefix:
        with open(args.csv_prefix + "_per_translation.csv", "w",
                  newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["group", "translation_id", "dyn_inst_seq", "asid",
                        "va", "fault_id", "terminal", "completeness",
                        "event_count", "observed_kinds", "expected_kinds",
                        "missing_kinds", "missing_edges"])
            for c in chains:
                w.writerow([c["group"], c["translation_id"],
                            c["dyn_inst_seq"], c["asid"], c["va"],
                            c["fault_id"], c["terminal"], c["completeness"],
                            c["event_count"],
                            ";".join(c["observed_kinds"]),
                            ";".join(c["expected_kinds"]),
                            ";".join(c["missing_kinds"]),
                            ";".join(c["missing_edges"])])

    # Per-context (ASID) CSV.
    ctx = defaultdict(lambda: {"chains": 0, "complete": 0, "partial": 0,
                               "incomplete": 0, "terminal": 0,
                               "representative": 0})
    for c in chains:
        asid = c["asid"] or "unknown"
        e = ctx[asid]
        e["chains"] += 1
        e[c["completeness"].lower()] += 1
        if c["has_terminal"]:
            e["terminal"] += 1
        if c["completeness"] == "COMPLETE" and c["has_terminal"]:
            e["representative"] += 1
    if args.csv_prefix:
        with open(args.csv_prefix + "_per_context.csv", "w",
                  newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["asid", "chains", "complete", "partial",
                        "incomplete", "terminal_chains",
                        "terminal_coverage", "representative_complete"])
            for asid, e in sorted(ctx.items()):
                cov = (e["terminal"] / e["chains"]) if e["chains"] else 0.0
                w.writerow([asid, e["chains"], e["complete"],
                            e["partial"], e["incomplete"], e["terminal"],
                            "%.3f" % cov, e["representative"]])

    # Missing causal edges CSV (deduplicated per chain).
    if args.csv_prefix:
        with open(args.csv_prefix + "_missing_edges.csv", "w",
                  newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["group", "missing_edge"])
            for c in chains:
                for edge in c["missing_edges"]:
                    w.writerow([c["group"], edge])

    required = MODELS[args.workload][args.model]
    observed_union = set()
    for c in chains:
        observed_union.update(c["observed_kinds"])
    target_coverage = [k for k in required if k in observed_union]
    missing_targets = [k for k in required if k not in observed_union]

    full = [c for c in chains
            if c["completeness"] == "COMPLETE" and c["has_terminal"]]
    contexts = len(ctx)
    contexts_with_terminal = sum(1 for e in ctx.values() if e["terminal"] > 0)

    result = {
        "input": args.input,
        "workload": args.workload,
        "model": args.model,
        "event_count": len(events),
        "parse_skipped": bad,
        "duplicate_event_ids": sorted(set(dup)),
        "integrity_errors": integrity_errors[:200],
        "trace_integrity": integrity,
        "trace_completeness": ("COMPLETE" if full else
                               "PARTIAL" if chains else "INCOMPLETE"),
        "propagation_coverage": ("FULL" if full else
                                 "PARTIAL" if chains else "NOT_OBSERVED"),
        "target_chain_count": len(chains),
        "full_chain_count": len(full),
        "workload_representative_chain_available": bool(full),
        "target_event_coverage": {
            "required": len(required),
            "observed": len(target_coverage),
            "ratio": round(len(target_coverage) / len(required), 3),
            "missing": missing_targets,
        },
        "terminal_coverage": {
            "contexts": contexts,
            "contexts_with_terminal": contexts_with_terminal,
            "ratio": (round(contexts_with_terminal / contexts, 3)
                      if contexts else 0.0),
        },
        "per_context": {k: dict(v) for k, v in sorted(ctx.items())},
        "kind_counts": dict(Counter(kind(e) for e in events)),
        "chains": chains,
    }
    if args.report_json:
        with open(args.report_json, "w") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
    if args.jsonl:
        with open(args.jsonl, "w") as fh:
            for ev in events:
                fh.write(json.dumps(ev, sort_keys=True) + "\n")

    print(json.dumps({k: result[k] for k in
                      ("event_count", "trace_integrity",
                       "trace_completeness", "propagation_coverage",
                       "target_chain_count", "full_chain_count",
                       "workload_representative_chain_available",
                       "target_event_coverage", "terminal_coverage")},
                     indent=2))
    return 0 if integrity == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
