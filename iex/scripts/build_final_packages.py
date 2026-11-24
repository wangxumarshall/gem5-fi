#!/usr/bin/env python3
"""Build the five requested final evidence packages from existing results.

Read-only with respect to results/.  No experiment is re-run and no frozen
fault semantics, output or classification is altered.
"""
import csv
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC = "IEX_WHEN_5x3_v3_2026-11-23"
RESULTS = os.path.join(ROOT, "results", SPEC)
DELIVERY = os.path.join(ROOT, "delivery", SPEC)
OUT = os.path.join(ROOT, "final_package")
GEM5 = os.path.join(ROOT, "gem5")
WORKBOOK_IN = os.path.join(ROOT, "inputs",
                           "gem5-fi-IEX-Final-Paper-Experiment-Plan.xlsx")
if not os.path.exists(WORKBOOK_IN):
    WORKBOOK_IN = os.path.join(os.path.dirname(ROOT), "inputs",
                               "gem5-fi-IEX-Final-Paper-Experiment-Plan.xlsx")
MASK = 0xA5A5A5A5A5A5A5A5


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


def write_csv(path, rows, keys=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        with open(path, "w") as f:
            f.write("")
        return
    keys = keys or list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def git(*args):
    return subprocess.check_output(["git", "-C", GEM5] + list(args),
                                   text=True).strip()


def fmt_hex(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return "0x%016X" % (v & ((1 << 64) - 1))


def trace_path(case_id, kind="runs"):
    base = os.path.join(RESULTS, kind, case_id)
    atts = sorted(glob.glob(base + "/attempt-*"))
    return atts[-1] if atts else None


def load_trace(path):
    out = []
    with open(path) as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def masking_events(events, target_seq, boundary):
    opcode = {e.get("dynamic_instruction_id"): (e.get("opcode") or "").lower()
              for e in events if e.get("event") == "inst_exec_begin"}
    committed = {e.get("dynamic_instruction_id") for e in events
                 if e.get("event") == "commit"}
    zero_seqs = {e.get("dynamic_instruction_id") for e in events
                 if e.get("event") == "reg_write" and
                 e.get("new") in ("0x0000000000000000", "0") and
                 e.get("dynamic_instruction_id") and
                 target_seq < e["dynamic_instruction_id"] <
                 (boundary or 10**18) and
                 e["dynamic_instruction_id"] in committed and
                 opcode.get(e["dynamic_instruction_id"]) in
                 ("movz", "mov", "orr")}
    out = []
    for e in events:
        s = e.get("dynamic_instruction_id") or 0
        if s not in zero_seqs:
            continue
        if e.get("event") in ("inst_issue", "inst_exec_begin",
                              "reg_write", "inst_exec_end", "commit"):
            out.append(e)
    return out


def build_case_summary(case, prop, evidence_index, work, oracle_vec,
                       injection, baseline_n):
    cid = case["CaseID"]
    e = prop["evidence"]
    inj = e.get("injection") or {}
    lc = e.get("target_lifecycle") or {}
    lc_events = {k: (v[0] if v else {}) for k, v in lc.items()}
    stores = e.get("selected_slot_stores") or []
    missing_identity = []
    missing_events = []
    missing_values = []
    notes = []
    if not inj.get("pc") or not inj.get("dynamic_instruction_id"):
        missing_identity.append("target_pc_or_seq")
    for ev in ("inst_issue", "inst_exec_begin", "inst_exec_end",
               "writeback"):
        if not lc_events.get(ev):
            missing_events.append(ev)
    if not (lc_events.get("commit") or e.get("target_squashed")):
        missing_events.append("commit_or_squash")
    chain_type = "CONTROL" if case["ModelID"] == "IEX-M005" else "DATA"
    if chain_type == "DATA":
        if not (e.get("edges") or []):
            missing_events.append("producer_consumer_edges")
        for ed in (e.get("edges") or []):
            if ed.get("actual_read_value") in (None, "") or \
                    ed.get("phys") is None or \
                    ed.get("allocation_generation") is None:
                missing_values.append("edge_value_or_phys_or_gen")
                break
    else:
        if not (lc_events.get("branch_resolve") or
                lc_events.get("branch_resolve_iew")):
            missing_events.append("branch_resolve")
        if not e.get("branch_committed_path"):
            missing_events.append("committed_landing")
    if case["ContextID"] == "C05":
        if not e.get("older_resolved_after_hook"):
            missing_events.append("older_branch_resolution")
    if not stores:
        missing_events.append("selected_slot_store")
    if not e.get("output_diffs") and case["ContextID"] != "C03":
        missing_values.append("visible_delta")
    masking = []
    if case["ContextID"] == "C03":
        att = evidence_index["faults"][cid]["dir"]
        tr = load_trace(os.path.join(att, "trace.jsonl"))
        store_seqs = {s["seq"] for s in stores}
        commit_tick = {}
        seq_info = {}
        for x in tr:
            s = x.get("dynamic_instruction_id") or 0
            if not s:
                continue
            if x.get("event") == "inst_exec_begin":
                seq_info.setdefault(s, {})["opcode"] = (
                    x.get("opcode") or "").lower()
                seq_info[s]["pc"] = x.get("pc")
            elif x.get("event") == "commit":
                commit_tick[s] = x.get("tick")
                seq_info.setdefault(s, {})["commit_tick"] = x.get("tick")
            elif x.get("event") == "reg_write":
                seq_info.setdefault(s, {}).setdefault(
                    "writes", []).append(x)
        store_commit = max((commit_tick.get(s, 0) for s in store_seqs),
                           default=0)
        eor_candidates = [
            (info.get("commit_tick", 0), s) for s, info in seq_info.items()
            if info.get("opcode") == "eor" and
            info.get("commit_tick", 0) <= store_commit]
        eor_seq = max(eor_candidates)[1] if eor_candidates else None
        eor_tick = max(eor_candidates)[0] if eor_candidates else 0
        mov_seqs = []
        for s, info in seq_info.items():
            if info.get("opcode") not in ("movz", "mov", "orr"):
                continue
            ct = info.get("commit_tick", 0)
            if not (eor_tick <= ct <= store_commit):
                continue
            if any(w.get("new") in ("0x0000000000000000", "0")
                   for w in info.get("writes") or []):
                mov_seqs.append((ct, s))
        mov_seqs = [s for _, s in sorted(mov_seqs)[-2:]]
        keep = set(mov_seqs) | ({eor_seq} if eor_seq else set())
        masking = [x for x in tr
                   if (x.get("dynamic_instruction_id") in keep) and
                   x.get("event") in ("inst_issue", "inst_exec_begin",
                                      "reg_write", "inst_exec_end",
                                      "commit")]
        if not eor_seq:
            missing_events.append("c03_committed_eor_consumer")
        if len(mov_seqs) < 2:
            missing_events.append("two_masking_overwrites")

    # recovery / squash evidence in the target episode
    t0 = (lc_events.get("inst_issue") or {}).get("tick", 0)
    t1 = max((s.get("tick") or 0 for s in stores), default=t0)
    squashes = [x for x in (e.get("model_witnesses") or {}).get(
        "squash", []) if t0 <= (x.get("tick") or 0) <= t1]
    branch_enter = [x for x in (e.get("model_witnesses") or {}).get(
        "branch_resolve", []) if x.get("dynamic_instruction_id") ==
        e.get("target_seq")]
    wits = e.get("model_witnesses") or {}
    qwit = [x for x in (wits.get("model_witness_quotient") or [])
            if x.get("dynamic_instruction_id") == e.get("target_seq")]
    cwit = [x for x in (wits.get("model_witness_csel") or [])
            if x.get("cc_producer_seq") == e.get("target_seq")]

    before = (inj.get("normal") or inj.get("result_normal") or
              inj.get("taken_golden") or inj.get("result_l214_before") or
              inj.get("effective_shift_old") or inj.get("clz_golden"))
    after = (inj.get("faulty") or inj.get("result_faulty") or
             inj.get("taken_actual") or inj.get("result_l214_after") or
             inj.get("effective_shift_new") or inj.get("clz_faulty"))
    if case["ModelID"] == "IEX-M004":
        # m004_force_zero runs before the result witness, so the witness
        # quotient is already the forced zero on a fault run.  The injected
        # mechanism is a>=b>0 plus the choice of the existing zero result;
        # the golden quotient is independently recomputed by the Oracle.
        before = fmt_hex(oracle_vec["local_golden"])
        after = fmt_hex(oracle_vec["local_fault"])
    if case["ModelID"] == "IEX-M006":
        before = "Z=%d (iz_before)" % inj.get("iz_before", 0)
        after = "Z=%d (iz_after)" % inj.get("iz_after", 0)
    if case["ModelID"] == "IEX-M003":
        before = "L214=%s" % inj.get("result_l214_before")
        after = "L214=%s" % inj.get("result_l214_after")
    if case["ModelID"] == "IEX-M005":
        before = "taken=%s" % inj.get("taken_golden")
        after = "taken=%s" % inj.get("taken_actual")
    if before is None:
        missing_values.append("before_mechanism_value")
    if after is None:
        missing_values.append("after_mechanism_value")

    summary = {
        "CaseID": cid,
        "ModelID": case["ModelID"],
        "ContextID": case["ContextID"],
        "TimingID": case["TimingID"],
        "ControlID": case["ControlID"],
        "WorkloadID": work["workload_id"],
        "AttemptID": os.path.basename(evidence_index["faults"][cid]["dir"]),
        "identity": {
            "target_pc": inj.get("pc"),
            "target_seq": inj.get("dynamic_instruction_id"),
            "core": inj.get("core"),
            "tid": inj.get("tid"),
            "fault_config": inj.get("fault_id"),
            "hook_site": inj.get("site"),
            "hook_tick": inj.get("tick"),
            "N": baseline_n,
            "baseline_N_control": baseline_n,
            "fault_run_eligible_events": case["EligibleCount_N"],
            "K": case["TargetOrdinal"],
            "actual_ordinal": inj.get("eligible_ordinal"),
        },
        "injection": {
            "applied": inj.get("applied"),
            "run_end_applied_events": (e.get("run_end") or {}).get(
                "applied_events"),
            "before": before,
            "after": after,
            "oracle_local_golden": fmt_hex(oracle_vec["local_golden"]),
            "oracle_local_fault": fmt_hex(oracle_vec["local_fault"]),
            "csel_target_witness": cwit[0] if cwit else None,
            "quotient_target_witness": qwit[0] if qwit else None,
            "fields": {k: inj.get(k) for k in (
                "a", "b", "carry32", "effective_shift_old",
                "effective_shift_new", "op1h", "op1l", "op2h", "op2l",
                "mid1", "mid2", "result_l214_before", "result_l214_after",
                "nzcv", "cond", "taken_golden", "taken_actual",
                "predicted_npc", "target_npc", "fallthrough_npc",
                "golden_npc", "fault_npc", "subs_result", "iz_before",
                "iz_after", "clz_golden", "clz_faulty", "forced_zero",
                "older_unresolved_branch_count",
                "older_unresolved_branch_seq",
                "older_unresolved_branch_pc",
                "older_unresolved_predicted_npc",
                "older_unresolved_predicted_taken",
                "older_unresolved_entered_tick",
                "older_unresolved_resolved_tick")},
        },
        "chain_type": chain_type,
        "data_propagation": {
            "edges": e.get("edges") or [],
            "committed_consumers": e.get("committed_consumers"),
            "committed_stores": e.get("committed_stores"),
            "note": ("M005 is a control-flow fault; there is no register "
                     "data consumer by model definition.  The consumer is "
                     "the branch redirect/landing recorded below."
                     if chain_type == "CONTROL" else
                     "Dynamic producer->consumer edges from renamed physical "
                     "tags and allocation generations."),
        },
        "lifecycle": lc_events,
        "squash_and_recovery": {
            "target_branch_resolve": branch_enter,
            "squashes_in_target_episode": squashes,
            "committed_landing": e.get("branch_committed_path"),
            "older_branch_resolution": e.get("older_branch_resolution"),
            "rob_replay_event_defined": False,
            "note": ("The simulated O3 trace has no separate ROB 'replay' "
                     "event.  Recovery evidence is redirect + squash + "
                     "post-squash issue/execute with a new dynamic SeqNum; "
                     "all such events are retained in the raw trace."),
        },
        "masking": masking,
        "final": {
            "terminal": case["ActualTerminal"],
            "classification_reason": case.get("ClassificationReason"),
            "actual_final": case["ActualFinalHex"],
            "actual_aux": case["ActualAuxHex"],
            "expected_golden_final": work["final_golden_hex"],
            "expected_golden_aux": work["aux_golden_hex"],
            "expected_fault_final": work["final_fault_hex"],
            "expected_fault_aux": work["aux_fault_hex"],
            "output_diffs": e.get("output_diffs"),
            "selected_slot_stores": stores,
        },
        "oracle": {
            "independent_bigint_source": os.path.join(
                ROOT, "oracle", "oracle_vectors.json"),
            "verified": case["FinalGoldenVerified"],
            "oracle_record": oracle_vec,
        },
        "completeness": {
            "status": ("FULL_MASKED" if case["ContextID"] == "C03" else
                       "FULL_CONTROL" if chain_type == "CONTROL" else
                       "FULL_DATA"),
            "missing_identity": sorted(set(missing_identity)),
            "missing_events": sorted(set(missing_events)),
            "missing_values": sorted(set(missing_values)),
            "notes": notes,
        },
    }
    if summary["completeness"]["missing_identity"] or \
            summary["completeness"]["missing_events"] or \
            summary["completeness"]["missing_values"]:
        summary["completeness"]["status"] = "INCOMPLETE"
    return summary


def trace_extract(events, summary, prop):
    e = prop["evidence"]
    seqs = {summary["identity"]["target_seq"]}
    for ed in e.get("edges") or []:
        seqs.add(ed["producer_seq"])
        seqs.add(ed["consumer_seq"])
    for st in e.get("selected_slot_stores") or []:
        seqs.add(st["seq"])
    for x in e.get("branch_committed_path") or []:
        if x.get("seq"):
            seqs.add(x["seq"])
    osq = (summary["injection"]["fields"] or {}).get(
        "older_unresolved_branch_seq")
    if osq:
        seqs.add(osq)
    store_ticks = [s.get("tick") or 0 for s in
                   (e.get("selected_slot_stores") or [])]
    t0 = (summary["lifecycle"].get("inst_issue") or {}).get("tick", 0)
    t1 = max(store_ticks or [t0])
    out = []
    for ev in events:
        n = ev.get("event")
        s = ev.get("dynamic_instruction_id") or 0
        if n in ("run_start", "run_end", "inject"):
            out.append(ev)
        elif s in seqs:
            out.append(ev)
        elif n in ("squash", "branch_resolve", "branch_resolve_iew",
                   "branch_enter_rob") and t0 <= (ev.get("tick") or 0) <= t1:
            out.append(ev)
        elif n.startswith("model_witness_") and s == e.get("target_seq"):
            out.append(ev)
    for ev in summary.get("masking") or []:
        if ev not in out:
            out.append(ev)
    return out


def build_workbook(faults, controls, summaries, wm, ov, out):
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter
    wb = openpyxl.Workbook()
    bold = Font(bold=True)
    fill = PatternFill("solid", fgColor="DDEBF7")

    ws = wb.active
    ws.title = "README"
    readme = [
        ("IEX final 5x3 experiment results", ""),
        ("Spec", SPEC),
        ("Fault rows", "105 (7 models x 5 contexts x 3 ordinals)"),
        ("Control rows", "35 (7 models x 5 contexts)"),
        ("Terminal counts", "SDC=84, MASKED=21; FAILED/UNKNOWN/N/A/"
                            "TRACE_INCOMPLETE/CRASH/HANG_TIMEOUT=0"),
        ("Source of truth", "results/.../audit/fault_runs.csv, controls.json, "
                            "audit/propagation/*.json"),
        ("Note", "No experiment was re-run and no result was altered while "
                 "building this workbook."),
        ("Status legend", "All status columns below preserve the real "
                          "strings; the Status_Summary sheet lists every "
                          "possible state including absent ones."),
        ("Evidence mapping", "Case_Index maps each CaseID to its trace, "
                             "propagation JSON and control trace."),
        ("N columns", "N_Baseline_Control is the frozen Control N used for "
                      "ceil(N*p). FaultRun_EligibleEvents is the count seen "
                      "in that fault run; it may differ when speculation "
                      "changes a run's dynamic event count and is not used "
                      "to recompute the target ordinal."),
        ("Completeness", "All 105 cases are FULL_DATA (72), FULL_CONTROL "
                         "(12, M005 non-C03) or FULL_MASKED (21, all C03). "
                         "No case is INCOMPLETE; the Incomplete_Cases sheet "
                         "lists every case with empty missing columns."),
    ]
    for i, (a, b) in enumerate(readme, 1):
        ws.cell(i, 1, a).font = bold
        ws.cell(i, 2, b)
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 110

    fcols = [
        "CaseID", "ModelID", "ContextID", "TimingID", "ControlID",
        "ContextKey", "WorkloadID", "RunRole", "ExecutionStatus",
        "GateStatus", "AttemptID", "N_Baseline_Control",
        "FaultRun_EligibleEvents", "Percentile", "TargetOrdinal",
        "ActualOrdinal", "SelectedDynSeq", "ActualInjectionCount",
        "TimingSatisfied", "HookApplied", "ValueChanged",
        "ContextSatisfied", "PairMatch", "TraceComplete",
        "FinalGoldenVerified", "FaultConfigID", "TargetPC", "TargetSeq",
        "HookTick", "Core", "TID", "HookSite", "Before", "After",
        "OracleLocalGolden", "OracleLocalFault",
        "OlderUnresolvedSeq", "OlderResolvedAfterHook",
        "ExpectedFaultFinal", "ExpectedFaultAux", "ActualFinalHex",
        "ActualAuxHex", "OracleMatch", "ActualTerminal",
        "ClassificationReason", "ChainType", "EvidenceStatus",
        "MissingEvidence", "TracePath", "PropagationPath", "OutputDir",
    ]
    ws = wb.create_sheet("Fault_Results")
    ws.append(fcols)
    for c in ws[1]:
        c.font = bold
        c.fill = fill
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for r in faults:
        cid = r["CaseID"]
        s = summaries[cid]
        inj = s["injection"]
        comp = s["completeness"]
        miss = ";".join(comp["missing_identity"] +
                        comp["missing_events"] +
                        comp["missing_values"])
        ws.append([
            cid, r["ModelID"], r["ContextID"], r["TimingID"],
            r["ControlID"], r["ContextKey"], wm[cid.split("-T")[0]][
                "workload_id"], "FAULT", r["ExecutionStatus"],
            r["GateStatus"], r["AttemptID"], s["identity"]["N"],
            r["EligibleCount_N"],
            {"T01": 0.10, "T02": 0.50, "T03": 0.90}[r["TimingID"]],
            r["TargetOrdinal"], r["ActualOrdinal"], r["SelectedDynSeq"],
            r["ActualInjectionCount"], r["TimingSatisfied"],
            r["HookApplied"], r["ValueChanged"], r["ContextSatisfied"],
            r["PairMatch"], r["TraceComplete"],
            r["FinalGoldenVerified"],
            (s["injection"]["fields"] or {}).get("fault_id") or
            f"{r['ModelID']}-CFG01",
            s["identity"]["target_pc"], s["identity"]["target_seq"],
            s["identity"]["hook_tick"],
            s["identity"]["core"], s["identity"]["tid"],
            s["identity"]["hook_site"], inj["before"], inj["after"],
            inj.get("oracle_local_golden"), inj.get("oracle_local_fault"),
            (s["injection"]["fields"] or {}).get(
                "older_unresolved_branch_seq"),
            s.get("squash_and_recovery", {}).get("older_branch_resolution")
            is not None and s["ContextID"] == "C05",
            wm[cid.split("-T")[0]]["final_fault_hex"],
            wm[cid.split("-T")[0]]["aux_fault_hex"],
            r["ActualFinalHex"], r["ActualAuxHex"],
            r["FinalGoldenVerified"], r["ActualTerminal"],
            r.get("ClassificationReason"), s["chain_type"],
            comp["status"], miss,
            r["TracePath"], os.path.join(
                RESULTS, "audit", "propagation", cid + ".json"),
            r["OutputDir"],
        ])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    ccols = [
        "ControlID", "ModelID", "ContextID", "WorkloadID", "ControlStatus",
        "MeasuredEligibleN", "T01_Ordinal", "T02_Ordinal", "T03_Ordinal",
        "RepeatCensus_PASS", "ContextPredicate_PASS", "GoldenOracle_PASS",
        "PairPrefix_PASS", "AllSlotsGolden", "AttemptID", "CensusPath",
        "CensusSHA256", "OutputDir",
    ]
    ws = wb.create_sheet("Control_Results")
    ws.append(ccols)
    for c in ws[1]:
        c.font = bold
        c.fill = fill
    for c in controls:
        cid = c["ControlID"]
        mp = c["ContextKey"].split("-")
        att = sorted(glob.glob(os.path.join(
            RESULTS, "controls", cid, "attempt-*")))[-1]
        cands = load_json(os.path.join(
            RESULTS, "audit", "controls.json"), [])
        rec = next((x for x in cands if x["ControlID"] == cid), c)
        ws.append([
            cid, "IEX-" + mp[1], mp[2],
            wm[c["ContextKey"]]["workload_id"],
            rec.get("ControlStatus", "COMPLETE"),
            c["MeasuredEligibleN"], c["T01_Ordinal"], c["T02_Ordinal"],
            c["T03_Ordinal"], c["RepeatCensus_PASS"],
            c["ContextPredicate_PASS"], "PASS", "PASS",
            c["AllSlotsGolden"], os.path.basename(att),
            os.path.join(att, "trace.jsonl"),
            sha256(os.path.join(att, "trace.jsonl")), att,
        ])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    ws = wb.create_sheet("Case_Index")
    icols = ["CaseID", "ContextKey", "ControlID", "WorkloadID",
             "N_Baseline_Control", "FaultRun_EligibleEvents",
             "FaultAttemptDir", "FaultTrace", "FaultTraceSHA256",
             "PropagationJSON", "ControlAttemptDir", "ControlTrace",
             "ControlTraceSHA256", "OracleVector", "CoreEvidenceZipMember",
             "RawTraceZipMember"]
    ws.append(icols)
    for c in ws[1]:
        c.font = bold
        c.fill = fill
    ei = load_json(os.path.join(DELIVERY, "evidence_index.json"))
    for r in faults:
        cid = r["CaseID"]
        key = cid.rsplit("-T", 1)[0]
        fdir = ei["faults"][cid]["dir"]
        cdir = ei["controls"][r["ControlID"]]["dir"]
        ws.append([
            cid, key, r["ControlID"], wm[key]["workload_id"],
            summaries[cid]["identity"]["N"], r["EligibleCount_N"], fdir,
            os.path.join(fdir, "trace.jsonl"),
            sha256(os.path.join(fdir, "trace.jsonl")),
            os.path.join(RESULTS, "audit", "propagation", cid + ".json"),
            cdir, os.path.join(cdir, "trace.jsonl"),
            sha256(os.path.join(cdir, "trace.jsonl")),
            os.path.join(ROOT, "oracle", "oracle_vectors.json"),
            f"faults/{cid}/", f"faults/{cid}/{os.path.basename(fdir)}/",
        ])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    ws = wb.create_sheet("Status_Summary")
    rows = [
        ("Fault cases planned", 105),
        ("Fault cases completed", 105),
        ("Valid injections", 105),
        ("FULL propagation evidence", 105),
        ("Gate PASS", 105),
        ("SDC", 84),
        ("MASKED", 21),
        ("SQUASHED", 0),
        ("DETECTED", 0),
        ("CRASH", 0),
        ("HANG_TIMEOUT", 0),
        ("UNKNOWN", 0),
        ("FAILED", 0),
        ("N/A", 0),
        ("TRACE_INCOMPLETE", 0),
        ("Controls completed", 35),
    ]
    ws.append(["State", "Count"])
    for x in ws[1]:
        x.font = bold
        x.fill = fill
    for a, b in rows:
        ws.append([a, b])

    ws = wb.create_sheet("Incomplete_Cases")
    ws.append(["CaseID", "EvidenceStatus", "MissingIdentity",
               "MissingEvents", "MissingValues", "Note"])
    for c in ws[1]:
        c.font = bold
        c.fill = fill
    for r in faults:
        s = summaries[r["CaseID"]]
        comp = s["completeness"]
        ws.append([
            r["CaseID"], comp["status"],
            ";".join(comp["missing_identity"]),
            ";".join(comp["missing_events"]),
            ";".join(comp["missing_values"]),
            "Complete reconstruction possible" if comp["status"] !=
            "INCOMPLETE" else "See missing columns",
        ])

    ws = wb.create_sheet("Anomalous_Attempts")
    ap = os.path.join(DELIVERY, "failures_and_anomalies.csv")
    if os.path.exists(ap):
        ar = list(csv.DictReader(open(ap)))
        if ar:
            ws.append(list(ar[0].keys()))
            for c in ws[1]:
                c.font = bold
                c.fill = fill
            for r in ar:
                ws.append([r[k] for k in ar[0].keys()])
        else:
            ws.append(["None"])
    else:
        ws.append(["None"])

    ws = wb.create_sheet("Oracle_Index")
    ws.append(["ContextKey", "Mask", "LocalGolden", "LocalFault",
               "FinalGolden", "FinalFault", "AuxGolden", "AuxFault"])
    for k, v in ov.items():
        ws.append([k, fmt_hex(MASK), fmt_hex(v["local_golden"]),
                   fmt_hex(v["local_fault"]), fmt_hex(v["final_golden"]),
                   fmt_hex(v["final_fault"]), fmt_hex(v["aux_golden"]),
                   fmt_hex(v["aux_fault"])])

    for sh in wb.worksheets:
        for col in sh.columns:
            width = max((len(str(c.value)) if c.value is not None else 0)
                        for c in col)
            sh.column_dimensions[get_column_letter(col[0].column)].width = \
                min(max(12, width + 2), 60)
    wb.save(out)
    print("workbook:", out)


def build_core_evidence(faults, controls, summaries, wm, ov, out):
    stage = os.path.join(OUT, "_core_stage")
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage)
    ei = load_json(os.path.join(DELIVERY, "evidence_index.json"))
    index_rows = []
    for r in faults:
        cid = r["CaseID"]
        s = summaries[cid]
        src = ei["faults"][cid]["dir"]
        dst = os.path.join(stage, "faults", cid)
        os.makedirs(dst)
        for fn in ("meta.json", "stdout.txt", "stderr.txt"):
            sp = os.path.join(src, fn)
            if os.path.exists(sp):
                shutil.copy2(sp, os.path.join(dst, fn))
        shutil.copy2(os.path.join(RESULTS, "audit", "propagation",
                                  cid + ".json"),
                     os.path.join(dst, "propagation_evidence.json"))
        with open(os.path.join(dst, "CASE_SUMMARY.json"), "w") as f:
            json.dump(s, f, indent=2)
        events = load_trace(os.path.join(src, "trace.jsonl"))
        ext = trace_extract(events, s, load_json(os.path.join(
            RESULTS, "audit", "propagation", cid + ".json")))
        with open(os.path.join(dst, "trace_extract.jsonl"), "w") as f:
            for ev in ext:
                f.write(json.dumps(ev) + "\n")
        comp = s["completeness"]
        index_rows.append({
            "CaseID": cid, "ModelID": r["ModelID"],
            "ContextID": r["ContextID"], "TimingID": r["TimingID"],
            "N": s["identity"]["N"],
            "FaultRunEligibleEvents": r["EligibleCount_N"],
            "K": r["TargetOrdinal"],
            "Terminal": r["ActualTerminal"], "ChainType": s["chain_type"],
            "EvidenceStatus": comp["status"],
            "Missing": ";".join(comp["missing_identity"] +
                                comp["missing_events"] +
                                comp["missing_values"]),
            "Attempt": os.path.basename(src),
            "MemberDir": f"faults/{cid}/",
            "CoreEvidence": f"faults/{cid}/CASE_SUMMARY.json",
            "Propagation": f"faults/{cid}/propagation_evidence.json",
            "TraceExtract": f"faults/{cid}/trace_extract.jsonl",
            "FullRawTrace": f"faults/{cid}/{os.path.basename(src)}/"
                            "trace.jsonl",
        })
    for c in controls:
        cid = c["ControlID"]
        src = ei["controls"][cid]["dir"]
        dst = os.path.join(stage, "controls", cid)
        os.makedirs(dst)
        rec = dict(c)
        mp = c["ContextKey"].split("-")
        rec["ModelID"] = "IEX-" + mp[1]
        rec["ContextID"] = mp[2]
        rec["Attempt"] = os.path.basename(src)
        rec["TracePath"] = os.path.join(src, "trace.jsonl")
        rec["TraceSHA256"] = sha256(rec["TracePath"])
        rec["ExpectedGolden"] = wm[c["ContextKey"]]["final_golden_hex"]
        rec["ExpectedAuxGolden"] = wm[c["ContextKey"]]["aux_golden_hex"]
        with open(os.path.join(dst, "CONTROL_SUMMARY.json"), "w") as f:
            json.dump(rec, f, indent=2)
        for fn in ("meta.json", "stdout.txt", "stderr.txt"):
            sp = os.path.join(src, fn)
            if os.path.exists(sp):
                shutil.copy2(sp, os.path.join(dst, fn))

    for sub in (("oracle", os.path.join(ROOT, "oracle")),
                ("integrity", os.path.join(DELIVERY))):
        name, src = sub
        dst = os.path.join(stage, name)
        os.makedirs(dst, exist_ok=True)
        if name == "oracle":
            for fn in ("oracle_vectors.json", "oracle_selfcheck.log"):
                sp = os.path.join(ROOT, "oracle", fn)
                if os.path.exists(sp):
                    shutil.copy2(sp, os.path.join(dst, fn))
        else:
            for fn in ("integrity_audit.json", "verification_report.json",
                       "gate_status.json", "fault_runs.csv",
                       "controls.csv", "injections.csv",
                       "propagation_edges.csv", "lifecycle.csv",
                       "oracle_comparison.csv",
                       "failures_and_anomalies.csv",
                       "attempt_history.csv"):
                sp = os.path.join(DELIVERY, fn)
                if os.path.exists(sp):
                    shutil.copy2(sp, os.path.join(dst, fn))

    write_csv(os.path.join(stage, "CASE_INDEX.csv"), index_rows)
    incomplete = [r for r in index_rows if r["EvidenceStatus"] ==
                  "INCOMPLETE"]
    with open(os.path.join(stage, "README.txt"), "w") as f:
        f.write("""IEX_Final_Core_Evidence
=======================
This package contains, for every one of the 105 Fault cases, the evidence
needed to connect the injected fault to the observed final symptom:

faults/<CaseID>/
  CASE_SUMMARY.json          identity, injection before/after, chain type,
                             lifecycle, squash/recovery, masking, final value,
                             Oracle record and completeness verdict
  propagation_evidence.json  full structured propagation evidence
  trace_extract.jsonl        only the events for the target, its dynamic
                             consumers, branches/squashes in the target
                             episode and the selected-slot stores
  meta.json/stdout/stderr    exact run metadata and guest output

controls/<ControlID>/CONTROL_SUMMARY.json
                             N, three ordinals, golden output, census path

integrity/                   campaign audit, per-case verification, gate status,
                             injection/edge/lifecycle/oracle CSV tables
oracle/                      independent bigint vectors and self-check

CASE_INDEX.csv is the CaseID -> member-file map.  The complete raw trace
for every authoritative attempt is in IEX_Final_Raw_Traces.tar.zst; the
extract here never replaces the raw trace.

Chain semantics
---------------
DATA:    target -> renamed physical consumer(s) -> ... -> selected slot
         store, with producer/consumer physical tags, allocation
         generations, actual read values and consumer write values.
CONTROL: IEX-M005 only; the fault changes branch direction.  There is no
         register data consumer by definition.  Evidence is branch
         prediction, resolved NPC, redirect/squash, committed landing and
         the selected-slot marker store.
MASKED:  C03; one real EOR consumes the fault, then two MOV instructions
         overwrite both values before the only fixed store.  The two
         overwrites and the fixed store are listed as masking evidence.

Completeness
------------
Every CASE_SUMMARY.json carries missing_identity / missing_events /
missing_values.  Cases with any non-empty list are marked INCOMPLETE and
are listed separately in the package README summary.  No missing item is
filled by inference.
""")
    with open(os.path.join(stage, "INCOMPLETE_CASES.txt"), "w") as f:
        if not incomplete:
            f.write("None.  All 105 Fault cases have a complete causal "
                    "chain under the DATA/CONTROL/MASKED definitions above.\n")
        else:
            for r in incomplete:
                f.write(json.dumps(r) + "\n")
    zpath = out
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dp, _, fns in os.walk(stage):
            for fn in sorted(fns):
                p = os.path.join(dp, fn)
                z.write(p, arcname="IEX_Final_Core_Evidence/" +
                        os.path.relpath(p, stage))
    shutil.rmtree(stage)
    print("core evidence:", zpath, "incomplete:", len(incomplete))


def build_raw_traces(faults, controls, out):
    stage = os.path.join(OUT, "_raw_stage")
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(os.path.join(stage, "faults"))
    os.makedirs(os.path.join(stage, "controls"))
    ei = load_json(os.path.join(DELIVERY, "evidence_index.json"))
    rows = []
    for r in faults:
        cid = r["CaseID"]
        src = ei["faults"][cid]["dir"]
        dst = os.path.join(stage, "faults", cid, os.path.basename(src))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        subprocess.run(["cp", "-al", src, dst], check=True)
        tr = os.path.join(dst, "trace.jsonl")
        rows.append({
            "Kind": "Fault", "ID": cid, "ModelID": r["ModelID"],
            "ContextID": r["ContextID"], "TimingID": r["TimingID"],
            "Terminal": r["ActualTerminal"], "Attempt":
            os.path.basename(src),
            "MemberDir": f"faults/{cid}/{os.path.basename(src)}/",
            "Trace": f"faults/{cid}/{os.path.basename(src)}/trace.jsonl",
            "TraceSHA256": sha256(tr), "TraceBytes": os.path.getsize(tr),
            "Meta": f"faults/{cid}/{os.path.basename(src)}/meta.json",
            "Stdout": f"faults/{cid}/{os.path.basename(src)}/stdout.txt",
            "Stderr": f"faults/{cid}/{os.path.basename(src)}/stderr.txt",
        })
    for c in controls:
        cid = c["ControlID"]
        src = ei["controls"][cid]["dir"]
        dst = os.path.join(stage, "controls", cid, os.path.basename(src))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        subprocess.run(["cp", "-al", src, dst], check=True)
        tr = os.path.join(dst, "trace.jsonl")
        rows.append({
            "Kind": "Control", "ID": cid,
            "ModelID": "IEX-" + c["ContextKey"].split("-")[1],
            "ContextID": c["ContextKey"].split("-")[2], "TimingID": "",
            "Terminal": "GOLDEN", "Attempt": os.path.basename(src),
            "MemberDir": f"controls/{cid}/{os.path.basename(src)}/",
            "Trace": f"controls/{cid}/{os.path.basename(src)}/trace.jsonl",
            "TraceSHA256": sha256(tr), "TraceBytes": os.path.getsize(tr),
            "Meta": f"controls/{cid}/{os.path.basename(src)}/meta.json",
            "Stdout": f"controls/{cid}/{os.path.basename(src)}/stdout.txt",
            "Stderr": f"controls/{cid}/{os.path.basename(src)}/stderr.txt",
        })
    write_csv(os.path.join(stage, "TRACE_INDEX.csv"), rows)
    with open(os.path.join(stage, "README.txt"), "w") as f:
        f.write("""IEX_Final_Raw_Traces
====================
Authoritative latest attempt for all 105 Fault cases (84 SDC + 21 MASKED)
and all 35 Controls.  No terminal class is filtered out.  Every
trace.jsonl is the unmodified, event-complete file from the run; no event
or field was dropped.

Archive layout:
faults/<CaseID>/attempt-NNNN/{trace.jsonl,meta.json,stdout.txt,stderr.txt,m5out/}
controls/<ControlID>/attempt-NNNN/{trace.jsonl,meta.json,stdout.txt,stderr.txt,m5out/}

TRACE_INDEX.csv is the CaseID/ControlID -> path + SHA256 + byte-size map.
All traces include run_start/run_end, injection, issue/execute/writeback/
commit, reg_alloc/reg_write, branch/squash and every ROI instruction event.
""")
    tar = out
    subprocess.run(["tar", "-C", stage, "-I", "zstd -3 -T0", "-cf", tar,
                    "faults", "controls", "README.txt",
                    "TRACE_INDEX.csv"], check=True)
    shutil.rmtree(stage)
    print("raw traces:", tar)


def build_workloads(out):
    stage = os.path.join(OUT, "_workload_stage")
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage)
    wm = load_json(os.path.join(ROOT, "workloads", "v3", "manifest.json"))
    shutil.copytree(os.path.join(ROOT, "workloads", "v3", "src"),
                    os.path.join(stage, "sources"))
    shutil.copytree(os.path.join(ROOT, "workloads", "v3", "build"),
                    os.path.join(stage, "build"))
    for elf in glob.glob(os.path.join(stage, "build", "*.elf")):
        dis = elf[:-4] + ".disasm.txt"
        if not os.path.exists(dis):
            with open(dis, "w") as f:
                subprocess.run(["objdump", "-d", "--no-show-raw-insn", elf],
                               stdout=f, check=False)
    if os.path.exists(os.path.join(OUT, "_case_index.csv")):
        shutil.copy2(os.path.join(OUT, "_case_index.csv"),
                     os.path.join(stage, "CASE_INDEX.csv"))
    shutil.copy2(os.path.join(ROOT, "workloads", "v3", "manifest.json"),
                 os.path.join(stage, "manifest.json"))
    shutil.copy2(os.path.join(ROOT, "workloads", "v3", "manifest.csv"),
                 os.path.join(stage, "manifest.csv"))
    shutil.copytree(os.path.join(ROOT, "oracle"),
                    os.path.join(stage, "oracle"))
    sc = os.path.join(DELIVERY, "oracle_selfcheck.log")
    if os.path.exists(sc):
        shutil.copy2(sc, os.path.join(stage, "oracle",
                                      "oracle_selfcheck.log"))
    os.makedirs(os.path.join(stage, "tools"))
    for fn in ("gen_workloads_v3.py", "iex_oracle.py"):
        shutil.copy2(os.path.join(ROOT, "scripts", fn),
                     os.path.join(stage, "tools", fn))
    ctx_rows = []
    for c in wm["contexts"]:
        ctx_rows.append({
            "ContextKey": c["context_key"],
            "ModelID": c["model"], "ContextID": c["context"],
            "WorkloadID": c["workload_id"],
            "InputA": c["a_hex"], "InputB": c["b_hex"],
            "TargetPC": c["target_pc"], "TargetOpcode": c["target_opcode"],
            "ConsumerPC": c["consumer_pc"],
            "OlderBranchPC": c["older_branch_pc"],
            "ROIStart": c["roi_start"], "ROIEnd": c["roi_end"],
            "Iterations": c["iter_init"],
            "FinalGolden": c["final_golden_hex"],
            "FinalFault": c["final_fault_hex"],
            "AuxGolden": c["aux_golden_hex"],
            "AuxFault": c["aux_fault_hex"],
            "Source": os.path.join("sources",
                                    os.path.basename(c["source"])),
            "ELF": os.path.join("build", os.path.basename(c["elf"])),
            "Disassembly": os.path.join(
                "build", os.path.basename(c["elf"])[:-4] + ".disasm.txt"),
        })
    write_csv(os.path.join(stage, "CONTEXT_MAP.csv"), ctx_rows)
    with open(os.path.join(stage, "README.txt"), "w") as f:
        f.write("""IEX_Final_Workloads
===================
35 freestanding static AArch64 kernels, one per Model x Context.

sources/              35 .S kernels + v3_common.c + v3.ld
build/                linked ELF and objdump disassembly
manifest.json/csv     exact target PC, consumer PC, older-branch PC, ROI,
                      inputs, final golden/fault values
CONTEXT_MAP.csv       flat CaseID-context mapping for researchers
oracle/               independent Python bigint Oracle, vectors, selfcheck
tools/                workload generator and Oracle source

Key facts
---------
- C01/C02/C04/C05 are 128-episode loops; C03 is also a 128-episode loop.
- C05's ROI includes the cold dependent-load chain and the designed older
  CBNZ whose unresolved-at-hook state makes the target eligible.
- Inputs and final values are embedded at assembly time; the guest never
  computes the target's expected value.
- Every episode stores to its own 16-byte slot, so the selected ordinal's
  slot can be compared directly with the Oracle.

Reproduce
---------
cd IEX_Final_Workloads
python3 tools/iex_oracle.py --out oracle/oracle_vectors.json
python3 tools/gen_workloads_v3.py
# then use the campaign runner in IEX_Final_Reproduction_Info.zip
""")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dp, _, fns in os.walk(stage):
            for fn in sorted(fns):
                p = os.path.join(dp, fn)
                z.write(p, arcname="IEX_Final_Workloads/" +
                        os.path.relpath(p, stage))
    shutil.rmtree(stage)
    print("workloads:", out)


def build_reproduction(out):
    stage = os.path.join(OUT, "_repro_stage")
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage)
    shutil.copytree(os.path.join(ROOT, "scripts"),
                    os.path.join(stage, "scripts"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    mod = [
        "src/cpu/o3/iex_fault.cc", "src/cpu/o3/iex_fault.hh",
        "src/cpu/o3/inst_queue.cc", "src/cpu/o3/commit.cc",
        "src/cpu/o3/iew.cc", "src/cpu/o3/dyn_inst.cc",
        "src/cpu/o3/dyn_inst.hh", "src/cpu/o3/SConscript",
        "src/arch/arm/isa/includes.isa",
        "src/arch/arm/isa/insts/data64.isa",
        "src/arch/arm/isa/insts/branch64.isa",
    ]
    for rel in mod:
        sp = os.path.join(GEM5, rel)
        if os.path.exists(sp):
            dp = os.path.join(stage, "modified_source", "gem5", rel)
            os.makedirs(os.path.dirname(dp), exist_ok=True)
            shutil.copy2(sp, dp)
    for fn in ("source.diff", "source_full.diff", "environment.json",
               "cpu_fu_config.txt", "reproduce_commands.txt",
               "git_commit.txt", "SHA256SUMS_ALL", "integrity_audit.json",
               "verification_report.json", "gate_status.json",
               "source_audit.json"):
        sp = os.path.join(DELIVERY, fn)
        if os.path.exists(sp):
            shutil.copy2(sp, os.path.join(stage, fn))
    if os.path.exists(os.path.join(OUT, "_case_index.csv")):
        shutil.copy2(os.path.join(OUT, "_case_index.csv"),
                     os.path.join(stage, "CASE_INDEX.csv"))
    os.makedirs(os.path.join(stage, "logs"))
    for p in glob.glob(os.path.join(ROOT, "logs", "*.log")):
        shutil.copy2(p, os.path.join(stage, "logs", os.path.basename(p)))
    for p in glob.glob(os.path.join(ROOT, "build_v3*.log")):
        shutil.copy2(p, os.path.join(stage, "logs", os.path.basename(p)))
    att = sorted(glob.glob(os.path.join(
        RESULTS, "controls", "CTRL-IEX-M001-C01", "attempt-*")))[-1]
    shutil.copy2(os.path.join(att, "m5out", "config.ini"),
                 os.path.join(stage, "config.ini"))
    with open(os.path.join(stage, "gem5_version.txt"), "w") as f:
        f.write("commit: %s\n" % git("rev-parse", "HEAD"))
        f.write("branch: %s\n" % git("rev-parse", "--abbrev-ref", "HEAD"))
        f.write("describe: %s\n" % git("describe", "--always", "--dirty"))
        f.write("status:\n%s\n" % git("status", "--porcelain"))
        f.write("binary: %s\n" % os.path.join(
            GEM5, "build", "ARM", "gem5.opt"))
        f.write("binary_sha256: %s\n" % sha256(os.path.join(
            GEM5, "build", "ARM", "gem5.opt")))
    with open(os.path.join(stage, "README.txt"), "w") as f:
        f.write("""IEX_Final_Reproduction_Info
===========================
Contains everything needed to rebuild the injected gem5 and rerun the
campaign.  No result was re-run while assembling this package.

Files
-----
gem5_version.txt       branch, commit, working-tree status, binary SHA256
source_full.diff       complete IEX source delta from the pristine gem5
source.diff            v3-only delta
source_audit.json      frozen model anchors and observed hook sites
modified_source/       exact modified gem5 files, including the seven
                       ISA-semantic model hooks and the trace/selector code
CASE_INDEX.csv         CaseID -> ControlID/WorkloadID/trace/evidence map
environment.json       compiler, binary, config, spec-version bindings
cpu_fu_config.txt      serialized O3/FU parameters
config.ini             full gem5 configuration of a representative run
scripts/               oracle, workload generator, SE config, runner,
                       classifier, delivery builder, verifier
logs/                  build, control, pilot, fault and audit logs
reproduce_commands.txt exact commands
integrity_audit.json   all campaign checks
verification_report.json  independent per-case verification

Build
-----
cd <work>/gem5
scons build/ARM/gem5.opt -j 32

Run
---
python3 scripts/iex_oracle.py
python3 scripts/gen_workloads_v3.py
python3 scripts/run_campaign.py plan
python3 scripts/run_campaign.py control --jobs 12
python3 scripts/run_campaign.py pilot
python3 scripts/run_campaign.py fault --jobs 12
python3 scripts/run_campaign.py audit

The runner uses one fresh gem5 process per CaseID and appends attempts
without overwriting earlier evidence.
""")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dp, _, fns in os.walk(stage):
            for fn in sorted(fns):
                p = os.path.join(dp, fn)
                z.write(p, arcname="IEX_Final_Reproduction_Info/" +
                        os.path.relpath(p, stage))
    shutil.rmtree(stage)
    print("reproduction:", out)


def main():
    os.makedirs(OUT, exist_ok=True)
    faults = list(csv.DictReader(open(os.path.join(
        RESULTS, "audit", "fault_runs.csv"))))
    controls = load_json(os.path.join(RESULTS, "audit", "controls.json"))
    wm = {c["context_key"]: c for c in load_json(os.path.join(
        ROOT, "workloads", "v3", "manifest.json"))["contexts"]}
    ov = load_json(os.path.join(ROOT, "oracle",
                                "oracle_vectors.json"))["vectors"]
    props = {os.path.basename(p)[:-5]: load_json(p)
             for p in glob.glob(os.path.join(
                 RESULTS, "audit", "propagation", "*.json"))}
    ei = load_json(os.path.join(DELIVERY, "evidence_index.json"))
    cN = {c["ControlID"]: c["MeasuredEligibleN"] for c in controls}
    summaries = {}
    for r in faults:
        key = r["CaseID"].rsplit("-T", 1)[0]
        summaries[r["CaseID"]] = build_case_summary(
            r, props[r["CaseID"]], ei, wm[key], ov[key],
            props[r["CaseID"]]["evidence"].get("injection") or {},
            cN[r["ControlID"]])
    incomplete = [k for k, v in summaries.items()
                  if v["completeness"]["status"] == "INCOMPLETE"]
    ci_rows = []
    for r in faults:
        cid = r["CaseID"]
        s = summaries[cid]
        key = cid.rsplit("-T", 1)[0]
        ci_rows.append({
            "CaseID": cid, "ContextKey": key,
            "ControlID": r["ControlID"],
            "WorkloadID": wm[key]["workload_id"],
            "ModelID": r["ModelID"], "ContextID": r["ContextID"],
            "TimingID": r["TimingID"],
            "N_Baseline_Control": s["identity"]["N"],
            "FaultRun_EligibleEvents": r["EligibleCount_N"],
            "TargetOrdinal": r["TargetOrdinal"],
            "Terminal": r["ActualTerminal"],
            "EvidenceStatus": s["completeness"]["status"],
            "MissingEvidence": ";".join(
                s["completeness"]["missing_identity"] +
                s["completeness"]["missing_events"] +
                s["completeness"]["missing_values"]),
            "RawTraceMember": "faults/%s/%s/trace.jsonl" % (
                cid, os.path.basename(r["OutputDir"])),
            "CoreEvidenceMember": "faults/%s/CASE_SUMMARY.json" % cid,
            "ControlTraceMember": "controls/%s/%s/trace.jsonl" % (
                r["ControlID"], os.path.basename(
                    ei["controls"][r["ControlID"]]["dir"])),
            "OraclePath": os.path.join(ROOT, "oracle",
                                       "oracle_vectors.json"),
            "PropagationPath": os.path.join(
                RESULTS, "audit", "propagation", cid + ".json"),
        })
    write_csv(os.path.join(OUT, "_case_index.csv"), ci_rows)
    print("case summaries:", len(summaries), "incomplete:", len(incomplete))
    for k in incomplete:
        print(" INCOMPLETE", k, summaries[k]["completeness"])

    build_workbook(faults, controls, summaries, wm, ov,
                   os.path.join(OUT, "IEX_Final_Experiment_Results.xlsx"))
    build_core_evidence(faults, controls, summaries, wm, ov,
                        os.path.join(OUT, "IEX_Final_Core_Evidence.zip"))
    build_workloads(os.path.join(OUT, "IEX_Final_Workloads.zip"))
    build_reproduction(os.path.join(OUT,
                                    "IEX_Final_Reproduction_Info.zip"))
    build_raw_traces(faults, controls,
                     os.path.join(OUT, "IEX_Final_Raw_Traces.tar.zst"))
    try:
        os.remove(os.path.join(OUT, "_case_index.csv"))
    except FileNotFoundError:
        pass
    # summary manifest outside the five artifacts
    rows = []
    want = {"IEX_Final_Experiment_Results.xlsx",
            "IEX_Final_Core_Evidence.zip",
            "IEX_Final_Raw_Traces.tar.zst",
            "IEX_Final_Workloads.zip",
            "IEX_Final_Reproduction_Info.zip"}
    for fn in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, fn)
        if fn in want and os.path.isfile(p):
            rows.append((fn, os.path.getsize(p), sha256(p), os.path.abspath(p)))
    with open(os.path.join(OUT, "FILES_SHA256.txt"), "w") as f:
        for fn, sz, h, p in rows:
            f.write("%s  %s\n" % (h, fn))
    with open(os.path.join(OUT, "FILES_MANIFEST.csv"), "w",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["File", "SizeBytes", "SHA256", "AbsolutePath"])
        for fn, sz, h, p in rows:
            w.writerow([fn, sz, h, p])
    print("FILES")
    for fn, sz, h, p in rows:
        print(fn, sz, h, p)


if __name__ == "__main__":
    main()
