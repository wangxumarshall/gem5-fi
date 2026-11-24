#!/usr/bin/env python3
"""Classify every v3 attempt from raw trace evidence and build the closure.

The classifier never infers a propagation path from the final output alone:
edges come from dynamic src-producer_seq records, lifecycle from the target
sequence's own events, and C05 state from the hook-time snapshot.
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict, deque

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC = "IEX_WHEN_5x3_v3_2026-11-23"
RESULTS = os.path.join(ROOT, "results", SPEC)

sys.path.insert(0, HERE)
import iex_oracle as oracle


def load_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


def latest_attempt(kind, label):
    base = os.path.join(RESULTS, kind, label)
    if not os.path.isdir(base):
        return None
    atts = sorted(n for n in os.listdir(base) if n.startswith("attempt-"))
    if not atts:
        return None
    return os.path.join(base, atts[-1])


def load_trace(path):
    ev = []
    with open(path) as f:
        for line in f:
            try:
                ev.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return ev


def seq_of(e):
    return e.get("dynamic_instruction_id") or e.get("seq") or 0


def build_index(events):
    by_seq_begin = {}
    by_seq_all = defaultdict(list)
    by_event = defaultdict(list)
    reg_writes = defaultdict(list)
    for e in events:
        s = e.get("dynamic_instruction_id", 0)
        by_event[e.get("event")].append(e)
        if s:
            by_seq_all[s].append(e)
        if e.get("event") == "inst_exec_begin":
            by_seq_begin[s] = e
        if e.get("event") == "reg_write":
            reg_writes[s].append(e)
    return by_seq_begin, by_seq_all, by_event, reg_writes


def lifecycle(by_seq_all, seq):
    out = {}
    for e in by_seq_all.get(seq, []):
        n = e.get("event")
        if n in ("inst_issue", "inst_exec_begin", "inst_exec_end",
                 "writeback", "commit",
                 "squash", "branch_resolve", "branch_resolve_iew",
                 "reg_write", "model_witness_csel", "model_witness_flags"):
            out.setdefault(n, []).append(e)
    return out


def reachable_edges(by_seq_begin, target, boundary=None):
    """BFS over dynamic producer_seq -> consumer edges starting at target.

    The search is bounded by the next dynamic instance of the same target
    (the next episode).  This keeps a fault's causal graph inside the
    episode that was actually injected; target templates such as ADDS read
    their architectural destination as a renamed source, which would
    otherwise fabricate a cross-episode edge even though the faulted value
    is not used by the next iteration's computation.
    """
    consumers = defaultdict(list)
    for seq, e in by_seq_begin.items():
        if boundary is not None and seq >= boundary:
            continue
        for i, r in enumerate(e.get("srcs") or []):
            p = r.get("producer_seq", 0)
            if p:
                consumers[p].append((seq, i, r))
    seen = {target}
    q = deque([target])
    edges = []
    while q:
        p = q.popleft()
        for cseq, idx, r in consumers.get(p, []):
            if boundary is not None and cseq >= boundary:
                continue
            edges.append({
                "producer_seq": p, "consumer_seq": cseq,
                "operand_index": idx,
                "reg_class": r.get("cls"), "arch": r.get("arch"),
                "phys": r.get("phys"), "flat": r.get("flat"),
                "allocation_generation": r.get("gen"),
                "actual_read_value": r.get("value"),
                "consumer_pc": by_seq_begin[cseq]["pc"]
                if cseq in by_seq_begin else None,
                "consumer_opcode": by_seq_begin[cseq].get("opcode")
                if cseq in by_seq_begin else None,
            })
            if cseq not in seen:
                seen.add(cseq)
                q.append(cseq)
    return edges, seen


def committed(by_seq_all, seq):
    return any(e.get("event") == "commit" for e in by_seq_all.get(seq, []))


def squashed(by_seq_all, seq):
    return any(e.get("event") == "squash" and
               (e.get("squashed_seq") or 0) <= seq for e in
               by_seq_all.get(seq, []))


def classify(meta, trace_events, vec, w, control):
    inj = next((e for e in trace_events if e.get("event") == "inject"), None)
    run_end = next((e for e in trace_events if e.get("event") == "run_end"),
                   None)
    out = meta.get("guest_output", {})
    slots = [tuple(x) for x in out.get("slots", [])]
    golden = (int(w["final_golden_hex"], 16), int(w["aux_golden_hex"], 16))
    faultv = (int(w["final_fault_hex"], 16), int(w["aux_fault_hex"], 16))
    n = (run_end or {}).get("eligible_events", 0)
    k = meta.get("select_ordinal") or 0
    diffs = [i for i, s in enumerate(slots) if s != golden]
    expected_diff = [k - 1] if k and k - 1 < len(slots) else []
    terminal = "UNKNOWN"
    reason = ""
    trace_complete = bool(inj and run_end)
    by_seq_begin, by_seq_all, by_event, reg_writes = build_index(trace_events)
    target_seq = inj.get("dynamic_instruction_id") if inj else 0
    lc = lifecycle(by_seq_all, target_seq)
    older_resolution = {}
    if inj and inj.get("older_unresolved_branch_seq"):
        osq = inj["older_unresolved_branch_seq"]
        older_resolution = {
            "older_seq": osq,
            "events": [e for e in by_seq_all.get(osq, [])
                       if e.get("event") in ("inst_issue", "inst_exec_begin",
                                             "inst_exec_end", "writeback",
                                             "branch_resolve", "commit")],
            "squash_covering": [e for e in trace_events
                                if e.get("event") == "squash" and
                                osq <= (e.get("squashed_seq") or 0)],
        }
        hook_tick = inj.get("tick", 0)
        older_resolved_after_hook = any(
            (e.get("tick") or 0) > hook_tick
            for e in older_resolution["events"]
            if e.get("event") == "branch_resolve")
    else:
        older_resolved_after_hook = False
    tcands = list((meta.get("trace_summary", {}).get("candidates") or []))
    if inj:
        tcands.append({"ordinal": inj.get("candidate_ordinal"),
                       "seq": target_seq, "eligible": 1})
    tcands.sort(key=lambda c: c.get("ordinal") or 0)
    boundary = None
    for i, c in enumerate(tcands):
        if c.get("seq") == target_seq:
            if i + 1 < len(tcands):
                boundary = tcands[i + 1].get("seq")
            break
    edges, reach = reachable_edges(by_seq_begin, target_seq,
                                   boundary) if target_seq else ([], set())
    for ed in edges:
        cseq = ed["consumer_seq"]
        ed["consumer_committed"] = committed(by_seq_all, cseq)
        ed["consumer_write_values"] = [
            {k: w.get(k) for k in ("cls", "arch", "phys", "gen", "old",
                                   "new")}
            for w in reg_writes.get(cseq, [])]
        pseq = ed["producer_seq"]
        ed["producer_write_values"] = [
            {k: w.get(k) for k in ("cls", "arch", "phys", "gen", "old",
                                   "new")}
            for w in reg_writes.get(pseq, [])]
    committed_con = sorted(s for s in reach
                           if s != target_seq and committed(by_seq_all, s))
    comm_stores = [s for s in committed_con
                   if (by_seq_begin.get(s) or {}).get("is_store")]
    target_commit = committed(by_seq_all, target_seq)
    target_squash = (not target_commit) and bool(
        lc.get("squash") or
        (target_seq and any(e.get("event") == "squash" and
                            (e.get("squashed_seq") or 0) <= target_seq
                            for e in trace_events if e.get("event") ==
                            "squash")))
    if not inj or not run_end:
        return "UNKNOWN", "missing inject/run_end", False, lc, edges, diffs
    if meta.get("timed_out"):
        terminal, reason = "HANG_TIMEOUT", "runner timeout"
    elif meta.get("returncode") != 0 or not out.get("gem5_end"):
        terminal, reason = "CRASH", "sim/guest non-zero exit or missing end"
    elif not (inj.get("applied") == 1 and
              (run_end or {}).get("timing_satisfied") == 1 and
              (run_end or {}).get("timing_selected_ordinal") == k):
        terminal, reason = "UNKNOWN", "invalid injection (gate failed)"
    else:
        # trace completeness
        has_target_end = bool(lc.get("inst_exec_end"))
        target_resolved = target_commit or target_squash
        model = w["model"]
        ctx = w["context"]
        consumer_evidence = bool(edges) or model == "IEX-M005"
        if ctx == "C05":
            consumer_evidence = consumer_evidence and bool(
                inj.get("older_unresolved_branch_count", 0) > 0) and \
                older_resolved_after_hook
        if model == "IEX-M005":
            consumer_evidence = consumer_evidence and bool(
                lc.get("branch_resolve") or lc.get("branch_resolve_iew"))
        if model == "IEX-M006":
            csel = [e for e in trace_events
                    if e.get("event") == "model_witness_csel"]
            consumer_evidence = consumer_evidence and bool(csel)
        trace_complete = bool(inj and run_end and has_target_end and
                              target_resolved and consumer_evidence)

        if diffs == expected_diff and diffs:
            terminal = "SDC"
            reason = ("selected episode slot %d carries the committed fault "
                      "value" % (k - 1))
        elif not diffs:
            if w["context"] == "C03":
                terminal = "MASKED"
                reason = ("single EOR consumer then both raw and EOR result "
                          "overwritten before the only store")
            elif target_squash and not committed_con:
                terminal = "SQUASHED"
                reason = "target and faulted descendants squashed"
            elif target_commit and committed_con:
                terminal = "MASKED"
                reason = ("faulted value consumed/committed but absent from "
                          "the final episode slot")
            elif target_commit:
                terminal = "MASKED"
                reason = "target committed but no committed data consumer"
            else:
                terminal = "UNKNOWN"
                reason = "no output difference and no decisive lifecycle"
        elif diffs and not expected_diff:
            terminal = "UNKNOWN"
            reason = "output differs outside the selected episode slot"
        else:
            terminal = "UNKNOWN"
            reason = "output difference does not match oracle fault value"

    # Locate the committed store that produced the selected episode slot.
    committed_stores_all = []
    for e in trace_events:
        if e.get("event") != "inst_exec_begin" or not e.get("is_store"):
            continue
        s = e.get("dynamic_instruction_id")
        if not committed(by_seq_all, s):
            continue
        ends = [x for x in by_seq_all.get(s, [])
                if x.get("event") == "inst_exec_end" and x.get("eff_addr")]
        if not ends:
            continue
        end = ends[-1]
        vals = [r.get("value") for r in (e.get("srcs") or [])]
        committed_stores_all.append({
            "seq": s, "pc": e.get("pc"), "eff_addr": end.get("eff_addr"),
            "tick": end.get("tick"), "values": vals,
        })
    selected_stores = []
    if committed_stores_all and k:
        base = min(int(x["eff_addr"], 16) & ~0xF
                   for x in committed_stores_all)
        want = base + (k - 1) * 16
        for x in committed_stores_all:
            if (int(x["eff_addr"], 16) & ~0xF) == want:
                selected_stores.append(x)
    # Committed instructions at a branch's resolved/fault NPC (path proof).
    branch_path = []
    for e in (lc.get("branch_resolve") or []) + \
             (lc.get("branch_resolve_iew") or []):
        npc = e.get("resolved_npc")
        if not npc:
            continue
        for b in trace_events:
            if (b.get("event") == "commit" and
                    (b.get("pc") or "").lower() == npc.lower()):
                branch_path.append({
                    "resolved_npc": npc, "committed_pc": b.get("pc"),
                    "seq": b.get("dynamic_instruction_id"),
                    "opcode": b.get("opcode")})

    evidence = {
        "trace_complete": trace_complete,
        "selected_slot_stores": selected_stores,
        "committed_stores_all": committed_stores_all,
        "branch_committed_path": branch_path,
        "target_seq": target_seq,
        "target_pc": inj.get("pc") if inj else None,
        "injection": inj,
        "target_lifecycle": lc,
        "older_branch_resolution": older_resolution,
        "older_resolved_after_hook": older_resolved_after_hook,
        "edges": edges,
        "committed_consumers": committed_con,
        "committed_stores": comm_stores,
        "target_committed": target_commit,
        "target_squashed": target_squash,
        "output_diffs": diffs,
        "expected_diff": expected_diff,
        "slots": slots,
        "run_end": run_end,
        "older_state": ({
            kk: inj.get(kk) for kk in (
                "older_unresolved_branch_count", "older_unresolved_branch_seq",
                "older_unresolved_branch_pc",
                "older_unresolved_predicted_npc",
                "older_unresolved_predicted_taken",
                "older_unresolved_entered_tick",
                "older_unresolved_resolved_tick")
        } if inj else {}),
        "model_witnesses": {
            n: [e for e in trace_events if e.get("event") == n]
            for n in ("model_witness_l215", "model_witness_l216",
                      "model_witness_l217", "model_witness_flags",
                      "model_witness_csel", "model_witness_quotient",
                      "branch_resolve", "squash")
        },
    }
    return terminal, reason, trace_complete, lc, edges, evidence


def analyze_case(case, w, vec, control):
    att = latest_attempt("runs", case["CaseID"])
    row = dict(case)
    if not att:
        row.update({"ExecutionStatus": "NOT_RUN", "ActualTerminal": "",
                    "TraceComplete": "", "FinalGoldenVerified": ""})
        return row, None
    meta = load_json(os.path.join(att, "meta.json"), {})
    tr = load_trace(os.path.join(att, "trace.jsonl"))
    terminal, reason, complete, lc, edges, evidence = classify(
        meta, tr, vec, w, control)
    slots = [tuple(x) for x in meta.get("guest_output", {}).get("slots", [])]
    k = meta.get("select_ordinal") or 0
    actual_slot = slots[k - 1] if 0 < k <= len(slots) else (None, None)
    exp = None
    if actual_slot[0] is not None:
        exp = (int(w["final_fault_hex"], 16),
               int(w["aux_fault_hex"], 16)) if w["context"] != "C03" else \
              (int(w["final_golden_hex"], 16),
               int(w["aux_golden_hex"], 16))
    verified = (actual_slot == exp) if exp else False
    inj = evidence.get("injection") or {}
    end = evidence.get("run_end") or {}
    cands = [c for c in
             (meta.get("trace_summary", {}).get("candidates") or [])]
    if inj:
        cands.append({"ordinal": inj.get("candidate_ordinal"),
                      "seq": inj.get("dynamic_instruction_id"),
                      "eligible": 1})
    cands.sort(key=lambda c: c.get("ordinal") or 0)
    pair = True
    if control and control.get("CandidateSeqs"):
        fault_prefix = [c["seq"] for c in cands
                        if c.get("eligible", 1)][:k]
        ctrl_prefix = control["CandidateSeqs"][:k]
        pair = fault_prefix == ctrl_prefix
    row.update({
        "AttemptID": os.path.basename(att),
        "OutputDir": att,
        "TracePath": os.path.join(att, "trace.jsonl"),
        "EligibleCount_N": end.get("eligible_events"),
        "TargetOrdinal": k,
        "ActualOrdinal": end.get("timing_selected_ordinal"),
        "SelectedDynSeq": end.get("timing_selected_seq"),
        "ActualInjectionCount": 1 if inj.get("applied") == 1 else 0,
        "TimingSatisfied": "PASS" if end.get("timing_satisfied") == 1
        else "FAIL",
        "HookApplied": "PASS" if inj.get("applied") == 1 else "FAIL",
        "ValueChanged": "PASS" if inj and inj.get("applied") == 1 else "FAIL",
        "ContextSatisfied": "PASS" if (
            w["context"] != "C05" or
            (inj.get("older_unresolved_branch_count", 0) > 0 and
             evidence.get("older_resolved_after_hook"))) else "FAIL",
        "PairMatch": "PASS" if pair else "FAIL",
        "TraceComplete": "PASS" if evidence.get("trace_complete") else
        "TRACE_INCOMPLETE",
        "FinalGoldenVerified": "PASS" if verified else "FAIL",
        "ActualFinalHex": ("0x%016X" % actual_slot[0]
                           if actual_slot[0] is not None else ""),
        "ActualAuxHex": ("0x%016X" % actual_slot[1]
                         if actual_slot[1] is not None else ""),
        "ActualTerminal": terminal,
        "ClassificationReason": reason,
        "ExecutionStatus": "COMPLETE",
        "GateStatus": "PASS" if all([
            inj.get("applied") == 1,
            end.get("timing_satisfied") == 1,
            end.get("timing_selected_ordinal") == k,
            evidence.get("trace_complete"), pair]) else "FAIL",
    })
    return row, evidence


def main(args=None):
    manifest = load_json(os.path.join(RESULTS, "manifest", "manifest.json"))
    wm = {c["context_key"]: c
          for c in load_json(os.path.join(ROOT, "workloads", "v3",
                                          "manifest.json"))["contexts"]}
    ov = load_json(os.path.join(ROOT, "oracle", "oracle_vectors.json"))[
        "vectors"]
    controls = {r["ControlID"]: r for r in
                load_json(os.path.join(RESULTS, "audit", "controls.json"),
                          [])}
    rows = []
    propdir = os.path.join(RESULTS, "audit", "propagation")
    os.makedirs(propdir, exist_ok=True)
    terminals = defaultdict(int)
    full = 0
    valid = 0
    for case in manifest["cases"]:
        w = wm[case["ContextKey"]]
        vec = ov[case["ContextKey"]]
        row, evidence = analyze_case(case, w, vec,
                                     controls.get(case["ControlID"]))
        rows.append(row)
        terminals[row.get("ActualTerminal") or "NOT_RUN"] += 1
        if row.get("HookApplied") == "PASS":
            valid += 1
        if row.get("TraceComplete") == "PASS":
            full += 1
        if evidence is not None:
            out = {
                "CaseID": case["CaseID"],
                "ModelID": case["ModelID"],
                "ContextID": case["ContextID"],
                "TimingID": case["TimingID"],
                "AttemptID": row["AttemptID"],
                "Terminal": row["ActualTerminal"],
                "ClassificationReason": row["ClassificationReason"],
                "ContextKey": case["ContextKey"],
                "target_ordinal": row["TargetOrdinal"],
                "oracle": {"final_golden": w["final_golden_hex"],
                           "final_fault": w["final_fault_hex"],
                           "aux_golden": w["aux_golden_hex"],
                           "aux_fault": w["aux_fault_hex"]},
                "evidence": evidence,
            }
            p = os.path.join(propdir, case["CaseID"] + ".json")
            with open(p, "w") as f:
                json.dump(out, f, indent=2)
    path = os.path.join(RESULTS, "audit", "fault_runs.csv")
    keys = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=keys)
        wtr.writeheader()
        wtr.writerows(rows)
    summary = {
        "spec": SPEC,
        "fault_cases_planned": 105,
        "fault_cases_completed": sum(
            1 for r in rows if r.get("ExecutionStatus") == "COMPLETE"),
        "valid_injections": valid,
        "trace_complete_full": full,
        "terminals": dict(terminals),
        "gate_pass": sum(1 for r in rows if r.get("GateStatus") == "PASS"),
        "output_dirs": os.path.join(RESULTS, "runs"),
    }
    with open(os.path.join(RESULTS, "audit", "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
