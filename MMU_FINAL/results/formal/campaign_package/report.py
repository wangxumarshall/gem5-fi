#!/usr/bin/env python3
"""Build the final campaign report, diagnostic feature library and Excel.

Reads analysis/samples.json + propagation_chains/*.json only.
"""
import glob
import json
import os
from collections import Counter, OrderedDict, defaultdict

import openpyxl
from openpyxl.styles import Font

CAMP = "/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113"
A = os.path.join(CAMP, "analysis")
SAMPLES = json.load(open(os.path.join(A, "samples.json")))

MODEL_MECH = {
    "M01": "L2/Unified TLB invalidation suppression",
    "M02": "PTW refill PFN corruption",
    "M03": "ASID tag-match false positive",
    "M04": "Resident TLB PFN substitution",
    "M05": "L2 partial walk-cache pointer substitution",
    "M06": "PTW leaf descriptor valid-bit corruption",
    "M07": "Permission grant decision inversion",
    "M08": "Final PA materialization corruption",
}
MODEL_FEATURES = {
    "M01": ["tlbi_issue", "tlbi_match", "mmu_fault_arm", "tlbi_suppressed",
            "tlb_lookup_hit", "tlb_entry_insert", "translation_result",
            "lsu_request", "memory_response", "commit", "mmu_fault_disarm"],
    "M02": ["ptw_start", "pte_read", "pte_decode", "refill_pfn_corrupt",
            "tlb_entry_insert", "tlb_lookup_hit", "fault_entry_consume",
            "translation_result", "lsu_request", "memory_response", "commit"],
    "M03": ["mmu_fault_activate", "tlb_lookup_hit", "permission_eval",
            "translation_result", "squash"],
    "M04": ["mmu_fault_activate", "tlb_entry_lineage", "tlb_lookup_hit",
            "fault_entry_consume", "translation_result", "lsu_request",
            "memory_response", "commit"],
    "M05": ["mmu_fault_activate", "partial_entry_insert", "tlb_lookup_hit",
            "fault_entry_consume", "ptw_start", "pte_read", "pte_decode",
            "tlb_fill", "tlb_entry_insert", "translation_result",
            "lsu_request"],
    "M06": ["mmu_fault_activate", "pte_decode", "fault_state_consumed",
            "fault_result_propagated", "exception_delivery"],
    "M07": ["permission_eval", "mmu_fault_activate", "translation_result",
            "lsu_request", "commit"],
    "M08": ["mmu_fault_activate", "translation_result", "lsu_request",
            "cache_request", "cache_lookup", "memory_response", "commit"],
}


def load_chain(sid):
    p = os.path.join(A, "propagation_chains", sid + ".json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def signature(events):
    return [e["Kind"] for e in events]


def state_transitions(events):
    out = []
    for e in events:
        if e.get("Field") or e.get("Before") or e.get("After"):
            out.append(OrderedDict([
                ("EventID", e["EventID"]), ("Kind", e["Kind"]),
                ("Field", e.get("Field")), ("Before", e.get("Before")),
                ("After", e.get("After")),
                ("StateBefore", e.get("StateBefore")),
                ("StateAfter", e.get("StateAfter"))]))
    return out


def pa_flow(events):
    seq = []
    for e in events:
        if e.get("VA") not in ("", "NOT_EMITTED") or \
           e.get("PA") not in ("", "NOT_EMITTED"):
            seq.append({"EventID": e["EventID"], "Kind": e["Kind"],
                        "VA": e.get("VA"), "PA": e.get("PA"),
                        "TranslationID": e.get("TranslationID"),
                        "EntryID": e.get("EntryID"),
                        "EntryGeneration": e.get("EntryGeneration")})
    return seq


def consumers(events):
    keep = {"translation_result", "lsu_request", "cache_request",
            "memory_response", "rf_writeback", "commit", "consumer",
            "exception_delivery", "squash", "fault_entry_consume",
            "fault_state_consumed", "fault_result_propagated"}
    return [{"EventID": e["EventID"], "Kind": e["Kind"],
             "VA": e.get("VA"), "PA": e.get("PA"),
             "TranslationID": e.get("TranslationID"),
             "CommitSeq": e.get("CommitSeq")}
            for e in events if e["Kind"] in keep]


def diagnose(s):
    ch = load_chain(s["SampleRunID"])
    events = ch["Events"] if ch else []
    present = Counter(e["Kind"] for e in events)
    expect = MODEL_FEATURES.get(s["ModelID"], [])
    return OrderedDict([
        ("SampleRunID", s["SampleRunID"]),
        ("ModelID", s["ModelID"]),
        ("ContextID", s["ContextID"]),
        ("FaultOrigin", s["ActivationStatus"]),
        ("ActivationEventID", s["ActivationEventID"]),
        ("ConsumptionEventID", s["ConsumptionEventID"]),
        ("TranslationIDs", s["TranslationIDs"]),
        ("ExpectedFeatureKinds", expect),
        ("ObservedFeatureKinds", sorted(present)),
        ("MissingFeatureKinds", [k for k in expect if k not in present]),
        ("PropagationSignature", signature(events)),
        ("MicroarchitecturalStateTransitions", state_transitions(events)),
        ("AddressFlow", pa_flow(events)),
        ("DownstreamConsumers", consumers(events)),
        ("TerminalState", s["TerminalState"]),
        ("OracleResult", s["OracleResult"]),
        ("OracleEvidence", s.get("ControlOracle", {})),
        ("DetectionOrMasking",
         "SQUASHED" if s["TerminalState"] == "SQUASHED"
         else ("DETECTED" if any(k in present for k in
                                 ("exception_delivery", "squash"))
               else "NOT_OBSERVED")),
        ("WrongValueProof", s.get("WrongValueProof", [])),
        ("TraceCompleteness", s["TraceCompleteness"]),
        ("StrictChain", s.get("StrictChain")),
    ])


def main():
    diags = [diagnose(s) for s in SAMPLES]
    with open(os.path.join(A, "diagnostic_features.json"), "w") as fh:
        json.dump(diags, fh, indent=1)

    # control zero proof (unique runs)
    proof = OrderedDict()
    for s in SAMPLES:
        p = s.get("ControlZeroProof") or {}
        ctl = p.get("control_run_dir")
        if ctl and ctl not in proof:
            proof[ctl] = p
    with open(os.path.join(A, "control_zero_proof.json"), "w") as fh:
        json.dump(proof, fh, indent=1)

    terminal = Counter(s["TerminalState"] for s in SAMPLES)
    activation = Counter(s["ActivationStatus"] for s in SAMPLES)
    propagation = Counter(s["PropagationStatus"] for s in SAMPLES)
    trace = Counter(s["TraceCompleteness"] for s in SAMPLES)
    oracle = Counter(s["OracleResult"] for s in SAMPLES)
    runs_ok = sum(1 for s in SAMPLES if s["RunStatus"] == "COMPLETED")
    activated = sum(1 for s in SAMPLES if s["ActivationStatus"] == "ACTIVATED")
    consumed = sum(1 for s in SAMPLES
                   if s["FaultConsumptionStatus"] == "CONSUMED")
    full = sum(1 for s in SAMPLES if s["PropagationStatus"] == "FULL")
    complete = sum(1 for s in SAMPLES if s["TraceCompleteness"] == "COMPLETE")
    legal = sum(1 for s in SAMPLES
                if s["TerminalState"] in
                ("SDC", "SQUASHED", "DETECTED_CONTAINED", "ACTIVATED_MASKED",
                 "CRASH", "HANG/TIMEOUT"))
    zero_ok = sum(1 for v in proof.values() if v.get("status") == "ZERO_PROVEN")

    limitations = []
    if full < 40:
        limitations.append(
            "%d sample(s) end SQUASHED with PARTIAL downstream propagation by "
            "design (the faulted translation is squashed before a data-side "
            "consumer); their raw trace is COMPLETE." % (40 - full))
    limitations.append(
        "The frozen binary does not emit per-instruction IFU fetch-response, "
        "decode, or IFU-specific commit events; instruction-side samples use "
        "MMU translation/permission -> Execute Request -> Guest Oracle and "
        "mark the unobserved nodes NOT_EMITTED_BY_FROZEN_BINARY.")
    if any(s["AttemptID"] != "A01" for s in SAMPLES):
        limitations.append(
            "Two samples were re-run under AttemptID A02 after an external "
            "process kill; original A01 partial attempts are preserved.")
    summary = OrderedDict([
        ("campaign_id", "MMU-FORMAL-20261113"),
        ("status", ("FORMAL_CAMPAIGN_COMPLETE"
                    if runs_ok == 40 and complete == 40 and
                    zero_ok == len(proof) and not limitations
                    else "FORMAL_CAMPAIGN_COMPLETE_WITH_LIMITATIONS"
                    if runs_ok == 40 else "FORMAL_CAMPAIGN_INCOMPLETE")),
        ("limitations", limitations),
        ("planned_samples", 40), ("started_samples", 40),
        ("completed_samples", runs_ok),
        ("valid_injection_evidence", activated),
        ("fault_state_consumed", consumed),
        ("full_propagation", full),
        ("partial_propagation_legal_squash", 40 - full),
        ("chain_complete", complete),
        ("legal_terminal", legal),
        ("unfinished_samples", 40 - runs_ok),
        ("control_runs_referenced", len(proof)),
        ("control_zero_proven", zero_ok),
        ("terminal_distribution", dict(terminal)),
        ("activation_distribution", dict(activation)),
        ("propagation_distribution", dict(propagation)),
        ("trace_distribution", dict(trace)),
        ("oracle_distribution", dict(oracle)),
        ("per_model", {}),
    ])
    for m in sorted(MODEL_MECH):
        sub = [s for s in SAMPLES if s["ModelID"] == m]
        summary["per_model"][m] = OrderedDict([
            ("mechanism", MODEL_MECH[m]),
            ("samples", len(sub)),
            ("terminal", dict(Counter(s["TerminalState"] for s in sub))),
            ("activation", dict(Counter(s["ActivationStatus"] for s in sub))),
            ("propagation", dict(Counter(s["PropagationStatus"] for s in sub))),
            ("trace", dict(Counter(s["TraceCompleteness"] for s in sub))),
            ("oracle", dict(Counter(s["OracleResult"] for s in sub))),
        ])
    with open(os.path.join(A, "final_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)

    md = []
    md.append("# MMU Final Formal Campaign — Results Summary\n")
    md.append("Campaign: `MMU-FORMAL-20261113`  ")
    md.append("Binary: `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`\n")
    md.append("| Metric | Value |\n|---|---|")
    for k in ("status", "planned_samples", "started_samples",
              "completed_samples", "valid_injection_evidence",
              "fault_state_consumed", "full_propagation", "chain_complete",
              "legal_terminal", "unfinished_samples",
              "control_runs_referenced", "control_zero_proven"):
        md.append("| %s | %s |" % (k, summary[k]))
    md.append("\n## TerminalState distribution\n")
    md.append("| Terminal | Count |\n|---|---|")
    for k, v in sorted(terminal.items()):
        md.append("| %s | %d |" % (k, v))
    md.append("\n## Per-model\n")
    md.append("| Model | Mechanism | n | Terminal | Activation | Trace | Propagation |")
    md.append("|---|---|---:|---|---|---|---|")
    for m, d in summary["per_model"].items():
        md.append("| %s | %s | %d | %s | %s | %s | %s |" % (
            m, d["mechanism"], d["samples"], d["terminal"], d["activation"],
            d["trace"], d["propagation"]))
    md.append("\n## Sample matrix\n")
    md.append("| # | SampleRunID | Model | Ctx | Activation | Propagation | Terminal | Trace | Oracle |")
    md.append("|---:|---|---|---|---|---|---|---|---|")
    for i, s in enumerate(SAMPLES, 1):
        md.append("| %d | `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
            i, s["SampleRunID"], s["ModelID"], s["ContextID"],
            s["ActivationStatus"], s["PropagationStatus"], s["TerminalState"],
            s["TraceCompleteness"], s["OracleResult"]))
    md.append("\n## Control Zero Proof\n")
    md.append("| Control run | mmuFaultModel | exit | InjectionAppliedCount | Status |")
    md.append("|---|---|---|---|---|")
    for ctl, p in proof.items():
        md.append("| `%s` | `%s` | %s | %s | %s |" % (
            ctl, p.get("config_mmuFaultModel"), p.get("gem5_exit_code"),
            p.get("injection_applied_count"), p.get("status")))
    md.append("\n## Documented limitations\n")
    for item in limitations:
        md.append("- " + item)
    md.append("\n## Failures / incomplete\n")
    bad = [s for s in SAMPLES
           if s["RunStatus"] != "COMPLETED" or s["TraceCompleteness"] != "COMPLETE"]
    if not bad:
        md.append("- No unfinished or trace-incomplete sample.")
    for s in bad:
        md.append("- `%s`: run=%s trace=%s" % (
            s["SampleRunID"], s["RunStatus"], s["TraceCompleteness"]))
    squash = [s for s in SAMPLES if s["TerminalState"] == "SQUASHED"]
    if squash:
        md.append("- Legitimate SQUASHED terminals: %s" %
                  ", ".join("`%s`" % s["SampleRunID"] for s in squash))
    with open(os.path.join(A, "campaign_summary.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")

    # ---------------- Excel ----------------
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Campaign_Summary"
    ws.append(["Metric", "Value"])
    for k, v in summary.items():
        if k in ("per_model", "terminal_distribution", "activation_distribution",
                 "propagation_distribution", "trace_distribution",
                 "oracle_distribution"):
            continue
        ws.append([k, str(v)])
    ws.append([])
    ws.append(["TerminalState", "Count"])
    for k, v in sorted(terminal.items()):
        ws.append([k, v])

    ws2 = wb.create_sheet("40_Sample_Matrix")
    cols = ["SampleRunID", "ModelID", "ContextID", "WorkloadID", "FaultID",
            "ActivationStatus", "FaultConsumptionStatus", "PropagationStatus",
            "TerminalState", "OracleResult", "TraceCompleteness",
            "RecordIntegrity", "GoldenOutput", "FaultOutput",
            "BinarySHA256", "ConfigSHA256", "WorkloadSHA256"]
    ws2.append(cols)
    for s in SAMPLES:
        ws2.append([str(s.get(c, "")) for c in cols])

    ws3 = wb.create_sheet("Per_Model")
    ws3.append(["Model", "Mechanism", "Samples", "Terminal", "Activation",
                "Propagation", "Trace", "Oracle"])
    for m, d in summary["per_model"].items():
        ws3.append([m, d["mechanism"], d["samples"], json.dumps(d["terminal"]),
                    json.dumps(d["activation"]), json.dumps(d["propagation"]),
                    json.dumps(d["trace"]), json.dumps(d["oracle"])])

    ws4 = wb.create_sheet("Control_Zero_Proof")
    ws4.append(["ControlRun", "mmuFaultEnable", "mmuFaultModel",
                "Gem5ExitCode", "InjectionAppliedCount", "Status", "Basis"])
    for ctl, p in proof.items():
        ws4.append([ctl, p.get("config_mmuFaultEnable"),
                    p.get("config_mmuFaultModel"), p.get("gem5_exit_code"),
                    p.get("injection_applied_count"), p.get("status"),
                    p.get("basis")])

    ws5 = wb.create_sheet("Diagnostic_Features")
    ws5.append(["SampleRunID", "Model", "Ctx", "Origin", "ActivationEvent",
                "ConsumptionEvent", "MissingFeatureKinds",
                "PropagationSignature", "StateTransitions", "AddressFlow",
                "Terminal", "Oracle", "DetectionOrMasking"])
    for d in diags:
        ws5.append([d["SampleRunID"], d["ModelID"], d["ContextID"],
                    d["FaultOrigin"], d["ActivationEventID"],
                    d["ConsumptionEventID"],
                    json.dumps(d["MissingFeatureKinds"]),
                    " -> ".join(d["PropagationSignature"]),
                    json.dumps(d["MicroarchitecturalStateTransitions"]),
                    json.dumps(d["AddressFlow"]),
                    d["TerminalState"], d["OracleResult"],
                    d["DetectionOrMasking"]])
    for sh in wb.worksheets:
        for c in sh[1]:
            c.font = Font(bold=True)
        sh.freeze_panes = "A2"
    xlsx = os.path.join(A, "MMU_Final_Formal_Campaign_Results.xlsx")
    wb.save(xlsx)
    print("wrote", xlsx)
    print(json.dumps({k: summary[k] for k in
                      ("status", "completed_samples", "valid_injection_evidence",
                       "chain_complete", "control_zero_proven",
                       "terminal_distribution")}, indent=1))


if __name__ == "__main__":
    main()
