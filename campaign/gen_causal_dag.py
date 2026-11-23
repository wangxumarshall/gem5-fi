#!/usr/bin/env python3
"""Generate causal_nodes.csv / causal_edges.csv / causal_branches.csv with full
per-edge correlation fields (tick, translation_id, request_id, dyn_inst_seq,
evidence file + line).  Reads the existing chain DAG from per_condition.json +
chain_branches.csv and enriches each edge by joining the source/target event
against the sample's raw trace (event_id -> line / fields).  No experiment
changes; correlation IDs are read from the trace verbatim, never invented.
"""
import csv
import gzip
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELIVERY = os.path.join(ROOT, "exports", "MMU_E2E_V3_FINAL_DELIVERY")
ANALYSIS = os.path.join(ROOT, "analysis")
RUNS = os.path.join(ROOT, "runs", "W5X3")
RETRY = os.path.join(ROOT, "runs", "W5X3_RETRY")
RETRY2 = os.path.join(ROOT, "runs", "W5X3_RETRY2")


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


def read_csv(p):
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


r2 = load(os.path.join(ANALYSIS, "retry2_map.json"), {})
r1 = load(os.path.join(ANALYSIS, "retry_map.json"), {})
per = {p["NewSampleRunID"]: p for p in
       load(os.path.join(ANALYSIS, "per_condition.json"), [])}
branches_csv = read_csv(os.path.join(ANALYSIS, "chain_branches.csv"))
# group branches by sample
branches_by_sid = {}
for b in branches_csv:
    branches_by_sid.setdefault(b["SampleRunID"], []).append(b)


def trace_path_for(sid):
    if sid in r2:
        return os.path.join(RETRY2, r2[sid], "Trace", "prop_evt.txt.gz")
    if sid in r1:
        return os.path.join(RETRY, r1[sid], "Trace", "prop_evt.txt.gz")
    return os.path.join(RUNS, sid, "Trace", "prop_evt.txt.gz")


def index_trace(sid, needed_ids):
    """event_id -> (dict, line_no) for ONLY the event ids the chain references.
    A full index would balloon (M04 traces hold ~235k events); the chain's
    edges reference at most a few dozen, so a single filtered pass is bounded."""
    path = trace_path_for(sid)
    idx = {}
    if not os.path.isfile(path) or not needed_ids:
        return idx, path
    import re as _re
    # cheap scan: pull event_id first, full regex-parse only on a needed id
    eid_re = _re.compile(r"event_id=(\d+)")
    with gzip.open(path, "rt", errors="replace") as fh:
        line_no = 0
        for line in fh:
            line_no += 1
            if not line.startswith("PROP-EVT:"):
                continue
            m = eid_re.search(line)
            if m is None:
                continue
            eid = int(m.group(1))
            if eid not in needed_ids:
                continue
            ev = dict(_re.findall(r"(\w+)=([^ ]*)", line))
            idx[eid] = (ev, line_no)
            if len(idx) >= len(needed_ids):
                break
    return idx, path


def main():
    node_rows = []
    edge_rows = []
    seen_nodes = set()
    n_edge = 0

    for sid, p in sorted(per.items()):
        ch = p.get("Chain") or {}
        edges = ch.get("edges", [])
        if not edges:
            continue
        # bounded: only index the event ids this chain's edges reference
        needed = set()
        for e in edges:
            if e.get("source") is not None:
                needed.add(int(e["source"]))
            if e.get("target") is not None:
                needed.add(int(e["target"]))
        idx, path = index_trace(sid, needed)
        if not idx:
            continue
        relpath = os.path.relpath(path, ROOT)
        for e in edges:
            src = e.get("source")
            tgt = e.get("target")
            if src is None or tgt is None:
                continue
            s = idx.get(int(src))
            t = idx.get(int(tgt))
            if not s or not t:
                continue
            sev, sln = s
            tev, tln = t
            basis = e.get("basis", "")
            # LinkKey = the correlation value that actually links them
            link_key = ""
            if basis == "parent_event_id":
                link_key = tev.get("parent_event_id", "")
            elif basis in ("translation_id", "request_id", "walk_id",
                           "source_event_id", "origin_event_id",
                           "entry_identity", "retained_entry",
                           "dyn_lineage", "fault_entry_lineage"):
                # prefer the target's field for the link identity
                link_key = tev.get(basis, "") or sev.get(basis, "")
            # correlation IDs from the target event (fall back to source)
            def g(d, k):
                v = d.get(k)
                return v if v not in ("", None) else sev.get(k, "")
            tid = g(tev, "translation_id")
            rid = g(tev, "request_id")
            dseq = g(tev, "dyn_inst_seq")
            parent = tev.get("parent_event_id", "")

            edge_rows.append({
                "SampleRunID": sid,
                "SourceEventID": src,
                "TargetEventID": tgt,
                "SourceTick": sev.get("tick", ""),
                "TargetTick": tev.get("tick", ""),
                "SourceEventType": e.get("source_kind", ""),
                "TargetEventType": e.get("target_kind", ""),
                "LinkType": basis,
                "LinkKey": link_key,
                "ParentEventID": parent,
                "TranslationID": tid,
                "RequestID": rid,
                "DynamicInstructionID": dseq,
                "EvidenceFile": relpath,
                "EvidenceLine": tln,
                "EvidenceStatus": "observed",
                "Confidence": e.get("confidence", ""),
            })
            n_edge += 1
            # collect distinct nodes
            for (ev, ln, eid) in ((sev, sln, src), (tev, tln, tgt)):
                key = (sid, str(eid))
                if key in seen_nodes:
                    continue
                seen_nodes.add(key)
                node_rows.append({
                    "SampleRunID": sid,
                    "EventID": eid,
                    "Tick": ev.get("tick", ""),
                    "EventType": ev.get("kind", ""),
                    "TranslationID": ev.get("translation_id", ""),
                    "RequestID": ev.get("request_id", ""),
                    "DynamicInstructionID": ev.get("dyn_inst_seq", ""),
                    "VA": ev.get("va", ""),
                    "PA": ev.get("pa", ""),
                    "Mode": ev.get("mode", ""),
                    "FaultID": ev.get("fault_id", ""),
                    "EvidenceFile": relpath,
                    "EvidenceLine": ln,
                })

    node_cols = ["SampleRunID", "EventID", "Tick", "EventType",
                 "TranslationID", "RequestID", "DynamicInstructionID",
                 "VA", "PA", "Mode", "FaultID", "EvidenceFile",
                 "EvidenceLine"]
    with open(os.path.join(DELIVERY, "causal_nodes.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=node_cols)
        w.writeheader()
        w.writerows(node_rows)

    edge_cols = ["SampleRunID", "SourceEventID", "TargetEventID",
                 "SourceTick", "TargetTick", "SourceEventType",
                 "TargetEventType", "LinkType", "LinkKey", "ParentEventID",
                 "TranslationID", "RequestID", "DynamicInstructionID",
                 "EvidenceFile", "EvidenceLine", "EvidenceStatus",
                 "Confidence"]
    with open(os.path.join(DELIVERY, "causal_edges.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=edge_cols)
        w.writeheader()
        w.writerows(edge_rows)

    # causal_branches.csv = chain_branches.csv (already carries the full
    # multi-branch DAG fields) with SampleRunID key
    bcols = ["SampleRunID", "ModelID", "Timing", "BranchIndex",
             "TranslationID", "ConsumeKind", "ConsumeEventID",
             "ReuseOrdinal", "VA", "PA", "TerminalKind", "TerminalEventID",
             "TerminalTick", "Commits", "Squashed"]
    with open(os.path.join(DELIVERY, "causal_branches.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=bcols)
        w.writeheader()
        for b in branches_csv:
            w.writerow({k: b.get(k, "") for k in bcols})

    print("causal_nodes.csv:", len(node_rows), "nodes")
    print("causal_edges.csv:", len(edge_rows), "edges")
    print("causal_branches.csv:", len(branches_csv), "branches")


if __name__ == "__main__":
    main()
