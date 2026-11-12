#!/usr/bin/env python3
"""Validate the unified MMU propagation trace (CHAOSPropagation PROP-EVT).

The native stream is `prop_evt.txt.gz` (one `PROP-EVT: k=v ...` line per
event, the existing CHAOSPropagation format).  This tool never invents
events: it parses the actual stream, converts it 1:1 to JSONL on request,
reconstructs the explicit ParentEventID graph, and reports TraceIntegrity,
TraceCompleteness and PropagationCoverage independently of the terminal
state.

Usage:
  mmu_trace_validate.py --input m5out/prop_evt.txt.gz --workload W10 \
      --jsonl trace.jsonl --report-json report.json --report-md report.md
"""

import argparse
import gzip
import json
import os
import sys
from collections import Counter, defaultdict

PROP_PREFIX = "PROP-EVT:"


def open_maybe_gz(path):
    """Open a gzip or plain text file; truncated gzip (aborted run) is OK."""
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
    # Values are whitespace-free by construction (the emitter never writes
    # spaces into a value); split on whitespace and then on the first '='.
    for token in body.split():
        if "=" not in token:
            continue
        key, val = token.split("=", 1)
        out[key] = val
    return out


def load_events(path):
    events = []
    bad = 0
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


def event_kind(ev):
    return ev.get("kind", "")


def expected_chain(workload):
    """Expected observable kinds for the workload's target chain."""
    if workload == "W9":
        return [
            "tlbi_issue", "tlbi_match", "tlbi_invalidate",
            "translation_start", "tlb_lookup_miss", "tlb_lookup_hit",
            "ptw_start", "pte_read", "pte_decode", "tlb_fill",
            "tlb_entry_insert", "permission_eval", "translation_result",
            "lsu_request", "memory_response", "rf_writeback", "commit",
        ]
    if workload == "W10":
        return [
            "translation_start", "tlb_lookup_miss", "ptw_start",
            "pte_read", "pte_decode", "tlb_fill", "tlb_entry_insert",
            "tlb_lookup_hit", "permission_eval", "translation_result",
            "lsu_request", "memory_response", "rf_writeback", "commit",
        ]
    return []


def validate(events, workload, va_prefixes):
    by_id = {}
    duplicate_ids = []
    for ev in events:
        eid = ev["event_id"]
        if eid in by_id:
            duplicate_ids.append(eid)
        by_id[eid] = ev

    integrity_errors = []
    for ev in events:
        parent = ev.get("parent_event_id", "")
        if parent == "":
            continue
        if int(parent) not in by_id:
            integrity_errors.append(
                "event %s (%s) parent %s missing" %
                (ev["event_id"], event_kind(ev), parent))
            continue
        if int(parent) == ev["event_id"]:
            integrity_errors.append(
                "event %s (%s) self-parent" %
                (ev["event_id"], event_kind(ev)))
            continue
        pt = to_int(by_id[int(parent)], "tick")
        ct = to_int(ev, "tick")
        if pt and ct and ct < pt:
            integrity_errors.append(
                "event %s (%s) tick %s < parent tick %s" %
                (ev["event_id"], event_kind(ev), ct, pt))

    # Select target translations by VA prefix.
    def in_scope(ev):
        if not va_prefixes:
            return True
        va = ev.get("va", "")
        if not va:
            return False
        try:
            v = int(va, 16) if not va.startswith("0x") else int(va, 0)
        except ValueError:
            return False
        # A prefix selects the 4 KiB page it names (the workload target VAs
        # are page-aligned). Exact 4 KiB granularity avoids pulling in the
        # unrelated pages that share the upper address bits.
        return any((v >> 12) == (int(p, 16) >> 12) for p in va_prefixes)

    # Group by translation_id (fall back to unique_request_id).
    groups = defaultdict(list)
    for ev in events:
        if not in_scope(ev):
            continue
        tid = ev.get("translation_id", "")
        if tid and tid != "0":
            groups["tid:" + tid].append(ev)
        elif ev.get("unique_request_id", "") not in ("", "0"):
            groups["uid:" + ev["unique_request_id"]].append(ev)

    exp = expected_chain(workload)

    # Chain quality per target translation. The chain includes every REAL
    # ancestor reachable through ParentEventID (e.g. the TLBI issue/match/
    # invalidate that caused the miss) — the graph is reconstructed from
    # explicit edges, never from tick adjacency.
    chains = []
    for key, evs in sorted(groups.items(),
                            key=lambda kv: min(to_int(e, "tick") for e in kv[1])):
        base_kinds = [event_kind(e) for e in evs]
        # Keep only groups that reached at least a translation/result event.
        if not any(k in base_kinds for k in ("translation_start",
                                             "translation_result",
                                             "tlb_lookup_hit",
                                             "tlb_lookup_miss")):
            continue
        chain_evs = list(evs)
        seen = {e["event_id"] for e in evs}
        # Ancestors: explicit ParentEventID edges only.
        for e in evs:
            p = e.get("parent_event_id", "")
            hops = 0
            while p and int(p) in by_id and int(p) not in seen and hops < 64:
                a = by_id[int(p)]
                chain_evs.append(a)
                seen.add(a["event_id"])
                p = a.get("parent_event_id", "")
                hops += 1
        # Instruction-keyed descendants: writeback/commit/squash carry no
        # virtual address, so they are joined by their real dyn_inst_seq
        # (the instruction identity the translation belongs to). This is an
        # explicit identity join, not a tick-order guess.
        target_seqs = {e.get("dyn_inst_seq") for e in evs
                       if e.get("dyn_inst_seq", "") not in ("", "0")}
        for e in events:
            if e["event_id"] in seen:
                continue
            if (event_kind(e) in ("rf_writeback", "commit", "squash")
                    and e.get("dyn_inst_seq", "") in target_seqs):
                chain_evs.append(e)
                seen.add(e["event_id"])
        kinds = [event_kind(e) for e in chain_evs]
        chain = {
            "group": key,
            "dyn_inst_seq": next((e.get("dyn_inst_seq") for e in evs
                                  if e.get("dyn_inst_seq", "") not in
                                  ("", "0")), ""),
            "unique_request_id": next((e.get("unique_request_id") for e in evs
                                       if e.get("unique_request_id", "") not in
                                       ("", "0")), ""),
            "translation_id": next((e.get("translation_id") for e in evs
                                    if e.get("translation_id", "") not in
                                    ("", "0")), ""),
            "walk_id": next((e.get("walk_id") for e in evs
                             if e.get("walk_id", "") not in ("", "0")), ""),
            "event_count": len(chain_evs),
            "kinds": kinds,
            "event_ids": [e["event_id"] for e in chain_evs],
            "first_tick": min(to_int(e, "tick") for e in chain_evs),
            "last_tick": max(to_int(e, "tick") for e in chain_evs),
            "full": bool(exp) and all(k in kinds for k in exp),
        }
        parent_ok = True
        for e in evs:
            p = e.get("parent_event_id", "")
            if p != "" and int(p) not in by_id:
                parent_ok = False
        chain["parent_linked"] = parent_ok
        chain["prefix_observed"] = True
        chains.append(chain)

    # Workload expected-chain coverage: a chain is COMPLETE only when at
    # least one target chain contains the whole expected sequence; the union
    # is reported separately so a partial warm-up chain cannot masquerade as
    # a complete propagation chain.
    observed_union = set()
    for c in chains:
        observed_union.update(c["kinds"])
    present = [k for k in exp if k in observed_union]
    missing = [k for k in exp if k not in observed_union]
    full_chains = [c for c in chains if c["full"]]

    if full_chains:
        completeness = "COMPLETE"
        coverage = "FULL"
    elif not chains:
        completeness = "INCOMPLETE"
        coverage = "NOT_OBSERVED"
    elif present:
        completeness = "PARTIAL"
        coverage = "PARTIAL"
    else:
        completeness = "PARTIAL"
        coverage = "NOT_OBSERVED"

    # A chain that lacks an explicit parent link is not complete.
    if chains and not all(c["parent_linked"] for c in chains):
        if completeness == "COMPLETE":
            completeness = "PARTIAL"

    integrity = "PASS" if not integrity_errors and not duplicate_ids else "FAIL"

    return {
        "event_count": len(events),
        "duplicate_event_ids": sorted(set(duplicate_ids)),
        "integrity_errors": integrity_errors[:200],
        "trace_integrity": integrity,
        "trace_completeness": completeness,
        "propagation_coverage": coverage,
        "expected_kinds": exp,
        "observed_kinds": sorted(observed_union),
        "missing_kinds": missing,
        "target_chain_count": len(chains),
        "full_chain_count": len(full_chains),
        "target_chains": chains,
        "kind_counts": dict(Counter(event_kind(e) for e in events)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--workload", default="", choices=["", "W9", "W10"])
    ap.add_argument("--va-prefix", action="append", default=[],
                    help="32-bit VA prefix, e.g. 0x40000000 (repeatable)")
    ap.add_argument("--jsonl", default="")
    ap.add_argument("--report-json", default="")
    ap.add_argument("--report-md", default="")
    args = ap.parse_args()

    events, bad = load_events(args.input)
    result = validate(events, args.workload, args.va_prefix)
    result["parse_skipped"] = bad

    if args.jsonl:
        with open(args.jsonl, "w") as out:
            for ev in events:
                out.write(json.dumps(ev, sort_keys=True) + "\n")

    if args.report_json:
        with open(args.report_json, "w") as out:
            json.dump(result, out, indent=2, sort_keys=True)

    if args.report_md:
        with open(args.report_md, "w") as out:
            out.write("# MMU Trace Validation Report\n\n")
            out.write("**Input:** `%s`  \n" % args.input)
            out.write("**Workload:** `%s`  \n" % (args.workload or "n/a"))
            out.write("**Events parsed:** %d (skipped: %d)\n\n" %
                      (len(events), bad))
            out.write("| Quality field | Value |\n|---|---|\n")
            out.write("| TraceIntegrity | %s |\n" % result["trace_integrity"])
            out.write("| TraceCompleteness | %s |\n" %
                      result["trace_completeness"])
            out.write("| PropagationCoverage | %s |\n" %
                      result["propagation_coverage"])
            out.write("| Target chains | %d |\n" %
                      result["target_chain_count"])
            out.write("| Fully complete target chains | %d |\n\n" %
                      result["full_chain_count"])
            out.write("## Expected vs observed kinds\n\n")
            out.write("Expected: %s\n\n" % ", ".join(result["expected_kinds"]))
            out.write("Observed: %s\n\n" % ", ".join(result["observed_kinds"]))
            out.write("Missing: %s\n\n" % (", ".join(result["missing_kinds"])
                                           or "none"))
            out.write("## Target chains\n\n")
            for c in result["target_chains"]:
                out.write("- `%s` seq=%s uid=%s tid=%s walk=%s events=%d "
                          "parent_linked=%s full=%s\n  - kinds: %s\n" %
                          (c["group"], c["dyn_inst_seq"],
                           c["unique_request_id"], c["translation_id"],
                           c["walk_id"], c["event_count"],
                           c["parent_linked"], c["full"],
                           ", ".join(c["kinds"])))

    print(json.dumps({k: result[k] for k in
                      ("event_count", "trace_integrity",
                       "trace_completeness", "propagation_coverage",
                       "target_chain_count", "missing_kinds")}, indent=2))
    return 0 if result["trace_integrity"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
