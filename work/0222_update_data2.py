#!/usr/bin/env python3
"""W5X3-OBS-0222 part 2: causal DAG + per_condition.json + summary CSVs."""
import csv
import json
import os

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
V3 = os.path.join(ROOT, "exports", "MMU_E2E_V3_FINAL_DELIVERY")
ANALYSIS = os.path.join(ROOT, "analysis")

TERMINAL_STATE = "SQUASHED_BEFORE_MEMORY_ACCESS"

ev = json.load(open(os.path.join(ROOT, "work", "obs0222_evidence.json")))

# Per-sample fixed identity
META = {
    "M07-F0-W14-W5X3-C02-T01": {
        "tid": 4, "seq": 24118302, "asid": 236, "va": "400d200000",
        "pa": "83496000", "trace": "runs/W5X3_OBS/M07-F0-W14-W5X3-OBS-C02-T01/Trace/prop_evt.txt.gz",
        "run_id": "M07-F0-W14-W5X3-OBS-C02-T01",
    },
    "M07-F0-W14-W5X3-C02-T02": {
        "tid": 9, "seq": 27030544, "asid": 242, "va": "400d200000",
        "pa": "83474000", "trace": "runs/W5X3_OBS/M07-F0-W14-W5X3-OBS-C02-T02/Trace/prop_evt.txt.gz",
        "run_id": "M07-F0-W14-W5X3-OBS-C02-T02",
    },
}

def ev_by(sid, kind):
    return next(e for e in ev[sid]["chain"] if e["kind"] == kind)


def load_csv(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(p, rows):
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# ============================================================
# 1. causal_nodes.csv + causal_edges.csv  (replace T01/T02)
# ============================================================
nodes = load_csv(os.path.join(V3, "causal_nodes.csv"))
edges = load_csv(os.path.join(V3, "causal_edges.csv"))

NODE_KINDS = ["mmu_fault_activate", "translation_result", "lsu_request",
              "translation_response_received", "squash_translation_decision",
              "squash_translation_invoked", "translation_request_discarded",
              "cache_dispatch_decision"]

def new_nodes(sid):
    m = META[sid]
    out = []
    for k in NODE_KINDS:
        e = ev_by(sid, k)
        mode = "Read" if k in ("mmu_fault_activate", "lsu_request") else ""
        pa = ("0x" + m["pa"]) if k in ("translation_result", "lsu_request",
                "translation_response_received", "squash_translation_decision",
                "squash_translation_invoked", "translation_request_discarded",
                "cache_dispatch_decision") else ""
        out.append({
            "SampleRunID": sid, "EventID": str(e["event_id"]),
            "Tick": str(e["tick"]), "EventType": k,
            "TranslationID": str(m["tid"]), "RequestID": str(m["seq"]),
            "DynamicInstructionID": str(m["seq"]), "VA": m["va"],
            "PA": pa, "Mode": mode, "FaultID": str(e["fault_id"]),
            "EvidenceFile": m["trace"], "EvidenceLine": str(e["line"]),
        })
    return out

def new_edges(sid):
    m = META[sid]
    out = []
    for i in range(len(NODE_KINDS) - 1):
        s = ev_by(sid, NODE_KINDS[i])
        t = ev_by(sid, NODE_KINDS[i + 1])
        out.append({
            "SampleRunID": sid, "SourceEventID": str(s["event_id"]),
            "TargetEventID": str(t["event_id"]), "SourceTick": str(s["tick"]),
            "TargetTick": str(t["tick"]), "SourceEventType": NODE_KINDS[i],
            "TargetEventType": NODE_KINDS[i + 1], "LinkType": "parent_event_id",
            "LinkKey": str(s["event_id"]), "ParentEventID": str(s["event_id"]),
            "TranslationID": str(m["tid"]), "RequestID": str(m["seq"]),
            "DynamicInstructionID": str(m["seq"]), "EvidenceFile": m["trace"],
            "EvidenceLine": str(t["line"]), "EvidenceStatus": "observed",
            "Confidence": "high",
        })
    return out

for sid in META:
    nodes = [n for n in nodes if n["SampleRunID"] != sid]
    edges = [e for e in edges if e["SampleRunID"] != sid]
    nodes += new_nodes(sid)
    edges += new_edges(sid)
nodes.sort(key=lambda r: (r["SampleRunID"], int(r["EventID"])))
edges.sort(key=lambda r: (r["SampleRunID"], int(r["SourceEventID"])))
write_csv(os.path.join(V3, "causal_nodes.csv"), nodes)
write_csv(os.path.join(V3, "causal_edges.csv"), edges)
print("causal_nodes/edges updated: nodes=%d edges=%d" % (len(nodes), len(edges)))

# ============================================================
# 2. per_condition.json  (surgical Chain update)
# ============================================================
pc = json.load(open(os.path.join(ANALYSIS, "per_condition.json")))
pc_v3 = os.path.join(V3, "per_condition.json")

def hexaddr(v):
    return "0x" + v

for sid, m in META.items():
    e = ev[sid]
    a = ev_by(sid, "mmu_fault_activate")
    t = ev_by(sid, "translation_result")
    q = ev_by(sid, "lsu_request")
    rsp = ev_by(sid, "translation_response_received")
    dec = ev_by(sid, "squash_translation_decision")
    inv = ev_by(sid, "squash_translation_invoked")
    disc = ev_by(sid, "translation_request_discarded")
    cdd = ev_by(sid, "cache_dispatch_decision")

    for row in pc:
        if row.get("NewSampleRunID") != sid:
            continue
        chain = row["Chain"]
        # top-level classification
        row["Completeness"] = "FULL"
        row["ArchitectureComplete"] = True
        row["TerminalState"] = TERMINAL_STATE
        row["EvidencePath"] = "runs/W5X3_OBS/%s" % m["run_id"]
        row["Reason"] = ("fault activated (permission false->true), translation NoFault, "
                         "LSU request issued; translation response received by LSQ, squash "
                         "decision=discard_due_to_prior_squash, squashTranslation() invoked, "
                         "request discarded (prior_squash_before_translation_completion), cache "
                         "dispatch blocked by squash -> complete chain; no SDC (guest SIGSEGV "
                         "is architectural, not the faulted instruction)")

        # terminal
        chain["terminal"] = {
            "corr": "none", "dyn_inst_seq": m["seq"], "event_id": disc["event_id"],
            "fault_id": 1, "kind": "translation_request_discarded",
            "request_id": m["seq"], "tick": disc["tick"],
            "translation_id": m["tid"], "va": "0x" + m["va"],
            "terminal_reason": "prior_squash_before_translation_completion",
        }
        # response + commit_squash stages
        chain["response"] = {
            "corr": "none", "dyn_inst_seq": m["seq"], "event_id": rsp["event_id"],
            "fault_id": 1, "kind": "translation_response_received",
            "pa": hexaddr(m["pa"]), "request_id": m["seq"], "tick": rsp["tick"],
            "translation_id": m["tid"], "va": "0x" + m["va"],
        }
        chain["writeback"] = None
        chain["consumer"] = None
        chain["stages"]["response"] = chain["response"]
        chain["stages"]["commit_squash"] = {
            "corr": "none", "dyn_inst_seq": m["seq"], "event_id": disc["event_id"],
            "fault_id": 1, "kind": "translation_request_discarded",
            "request_id": m["seq"], "tick": disc["tick"],
            "translation_id": m["tid"], "va": "0x" + m["va"],
        }
        # edges: keep activation->translation->request, add the new 4
        base_edges = [
            {"basis": "parent_event_id", "confidence": "high",
             "source": a["event_id"], "source_kind": "mmu_fault_activate",
             "target": t["event_id"], "target_kind": "translation_result",
             "type": "parent_child"},
            {"basis": "parent_event_id", "confidence": "high",
             "source": t["event_id"], "source_kind": "translation_result",
             "target": q["event_id"], "target_kind": "lsu_request",
             "type": "parent_child"},
        ]
        new_edge_kinds = [
            ("lsu_request", "translation_response_received"),
            ("translation_response_received", "squash_translation_decision"),
            ("squash_translation_decision", "squash_translation_invoked"),
            ("squash_translation_invoked", "translation_request_discarded"),
            ("translation_request_discarded", "cache_dispatch_decision"),
        ]
        for sk, tk in new_edge_kinds:
            se = ev_by(sid, sk); te = ev_by(sid, tk)
            base_edges.append({"basis": "parent_event_id", "confidence": "high",
                               "source": se["event_id"], "source_kind": sk,
                               "target": te["event_id"], "target_kind": tk,
                               "type": "parent_child"})
        chain["edges"] = base_edges
        # branches terminal
        chain["branches"] = [{
            "commits": False, "consume_event_id": None, "consume_kind": None,
            "dyn_inst_seq": m["seq"], "mode": "Read", "origin_dyn_inst_seq": None,
            "pa": hexaddr(m["pa"]), "reuse_ordinal": None, "squashed": True,
            "terminal_event_id": disc["event_id"],
            "terminal_kind": "translation_request_discarded",
            "terminal_tick": disc["tick"], "translation_id": m["tid"],
            "va": "0x" + m["va"],
        }]
        chain["effect_branch_index"] = 0
        chain["effect_terminal_kind"] = "translation_request_discarded"
        # completeness
        chain["completeness"] = {
            "architecture_complete": True, "boundary": [], "edges_explicit": True,
            "effect_commits": False, "effect_terminal_kind": "translation_request_discarded",
            "not_applicable": ["mutation", "writeback", "consumer"],
            "terminal_observed": True, "unobserved": [],
        }
        chain["not_applicable"] = ["mutation", "writeback", "consumer"]
        chain["unobserved"] = []
        chain["boundary"] = []
        # summary: keep mmu_fault_summary but refine terminal note
        chain["summary"]["masked_reason"] = "request_issued_not_completed_at_roi_end"
        chain["notes"] = [
            "M07 carries its mutation inside the activation row (permission_before=false -> permission_after=true)",
            "runtime-proven squash-discard terminal: translation_response_received -> "
            "squash_translation_decision(discard_due_to_prior_squash) -> squash_translation_"
            "invoked -> translation_request_discarded(prior_squash_before_translation_"
            "completion) -> cache_dispatch_decision(cache_dispatch_blocked_by_squash)",
            "guest SIGSEGV is architectural (execute-only denial), NOT the faulted "
            "instruction (fault one-shot consumed on the squashed load)",
        ]
        # TerminalStateDetail
        row["TerminalStateDetail"] = {
            "activation_basis": "parent_event_id(%d)" % a["parent"],
            "activation_kind": "mmu_fault_activate", "consumed_lineage": False,
            "exception_delivered": 0, "faulted_event_count": len(e["chain"]),
            "has_any_commit": False, "has_consumer": False, "has_request": True,
            "has_response": True, "has_translation": True, "has_writeback": False,
            "masked_reason": "request_issued_not_completed_at_roi_end",
            "not_applicable": ["mutation", "writeback", "consumer"],
            "summary_outcome": "activated_not_consumed",
            "terminal_kind": "translation_request_discarded",
            "terminal_reason": "prior_squash_before_translation_completion",
            "unobserved": [],
        }
        # Stages (top-level summary)
        row["Stages"] = {
            "activation": {"event_id": a["event_id"], "kind": "mmu_fault_activate",
                           "tick": a["tick"]},
            "translation": {"event_id": t["event_id"], "kind": "translation_result",
                            "tick": t["tick"]},
            "request": {"event_id": q["event_id"], "kind": "lsu_request",
                        "tick": q["tick"]},
            "response": {"event_id": rsp["event_id"],
                         "kind": "translation_response_received", "tick": rsp["tick"]},
            "commit_squash": {"event_id": disc["event_id"],
                              "kind": "translation_request_discarded", "tick": disc["tick"]},
        }

json.dump(pc, open(os.path.join(ANALYSIS, "per_condition.json"), "w"), indent=2)
# mirror to V3 (copy)
import shutil
shutil.copy2(os.path.join(ANALYSIS, "per_condition.json"), pc_v3)
print("per_condition.json updated (analysis + V3)")

# ============================================================
# 3. completeness.csv / summary_by_model.csv / per_model_completeness.csv
# ============================================================
comp = load_csv(os.path.join(V3, "completeness.csv"))
for sid in META:
    for r in comp:
        if r["SampleRunID"] == sid:
            r["TerminalState"] = TERMINAL_STATE
            r["ArchitectureComplete"] = "True"
            r["Completeness"] = "FULL"
write_csv(os.path.join(V3, "completeness.csv"), comp)
# also update analysis copy if present
if os.path.isfile(os.path.join(ANALYSIS, "completeness.csv")):
    write_csv(os.path.join(ANALYSIS, "completeness.csv"), comp)

# summary_by_model.csv: replace REQUEST_PENDING_AT_ROI_END column with SQUASHED
sbm = load_csv(os.path.join(V3, "summary_by_model.csv"))
for r in sbm:
    if r["ModelID"] == "M07":
        r["REQUEST_PENDING_AT_ROI_END"] = "0"
    r["SQUASHED_BEFORE_MEMORY_ACCESS"] = ("2" if r["ModelID"] == "M07" else "0")
write_csv(os.path.join(V3, "summary_by_model.csv"), sbm)

pmc = load_csv(os.path.join(V3, "per_model_completeness.csv"))
for r in pmc:
    if r["ModelID"] == "M07":
        r["FULL"] = "15"
        r["PARTIAL"] = "0"
write_csv(os.path.join(V3, "per_model_completeness.csv"), pmc)
print("completeness/summary/per_model CSVs updated")

print("part 2 done")
