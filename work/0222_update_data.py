#!/usr/bin/env python3
"""W5X3-OBS-0222: update M07-C02-T01/T02 classification + deliverables.

Both samples now have runtime proof of the FULL fault->terminal chain:
  mmu_fault_activate -> translation_result(NoFault) -> lsu_request ->
  translation_response_received -> squash_translation_decision(discard) ->
  squash_translation_invoked -> translation_request_discarded ->
  cache_dispatch_decision(blocked_by_squash)

Terminal = SQUASHED_BEFORE_MEMORY_ACCESS; Completeness = FULL.

This script extracts evidence directly from the new traces (no transcription),
updates the derived data files, and writes the per-sample propagation reports.
It does NOT touch the 118 other samples or the historical raw traces.
"""
import csv
import gzip
import json
import os
import re
import hashlib

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
V3 = os.path.join(ROOT, "exports", "MMU_E2E_V3_FINAL_DELIVERY")
ANALYSIS = os.path.join(ROOT, "analysis")
OBS = os.path.join(ROOT, "runs", "W5X3_OBS")

NEW_BUILD = "ce80a9c983b31f77c9b4a6626012505fd3484d5c00df5b9399a9d6975ab2b73d"
TERMINAL_STATE = "SQUASHED_BEFORE_MEMORY_ACCESS"

SAMPLES = [
    {
        "sid": "M07-F0-W14-W5X3-C02-T01",
        "run_id": "M07-F0-W14-W5X3-OBS-C02-T01",
        "seq": 24118302,
        "trace": os.path.join(OBS, "M07-F0-W14-W5X3-OBS-C02-T01",
                             "Trace", "prop_evt.txt.gz"),
        "control_run": "CTRL-OBS-M07-C02",
        "control_trace": os.path.join(OBS, "CTRL-OBS-M07-C02",
                                      "Trace", "prop_evt.txt.gz"),
        "ordinal": 1,
    },
    {
        "sid": "M07-F0-W14-W5X3-C02-T02",
        "run_id": "M07-F0-W14-W5X3-OBS-C02-T02",
        "seq": 27030544,
        "trace": os.path.join(OBS, "M07-F0-W14-W5X3-OBS-C02-T02",
                             "Trace", "prop_evt.txt.gz"),
        "control_run": "CTRL-OBS-M07-C02",
        "control_trace": os.path.join(OBS, "CTRL-OBS-M07-C02",
                                      "Trace", "prop_evt.txt.gz"),
        "ordinal": 3,
    },
]

KINDS = ("translation_start", "squash", "mmu_fault_activate",
         "translation_result", "lsu_request", "translation_response_received",
         "squash_translation_decision", "squash_translation_invoked",
         "translation_request_discarded", "cache_dispatch_decision")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def extract_chain(trace_path, seq):
    """Return ordered list of key events for the faulted dyn-inst seq."""
    evs = []
    with gzip.open(trace_path, "rt", errors="replace") as fh:
        for ln, line in enumerate(fh, 1):
            if "dyn_inst_seq=%d " % seq not in line:
                continue
            d = dict(re.findall(r"([a-z_]+)=([^ ]*)", line))
            k = d.get("kind", "")
            if k in KINDS:
                evs.append({
                    "line": ln,
                    "kind": k,
                    "event_id": int(d.get("event_id", 0)),
                    "parent": int(d.get("parent_event_id") or 0),
                    "tick": int(d.get("tick") or 0),
                    "tid": int(d.get("translation_id") or 0),
                    "fault_id": int(d.get("fault_id") or 0),
                    "va": d.get("va", ""),
                    "pa": d.get("pa", ""),
                    "mode": d.get("mode", ""),
                    "fault_status": d.get("fault_status", ""),
                    "decision": d.get("decision", ""),
                    "released": d.get("released", ""),
                    "terminal_reason": d.get("terminal_reason", ""),
                    "dispatch_decision": d.get("dispatch_decision", ""),
                    "asid": int(d.get("asid") or 0),
                })
    # dedupe by event_id (some events may match multiple greps)
    seen = set()
    uniq = []
    for e in evs:
        if e["event_id"] in seen:
            continue
        seen.add(e["event_id"])
        uniq.append(e)
    return sorted(uniq, key=lambda e: e["event_id"])


def load_csv(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main():
    for S in SAMPLES:
        chain = extract_chain(S["trace"], S["seq"])
        S["chain"] = chain
        S["trace_sha256"] = sha256(S["trace"])
        S["control_trace_sha256"] = sha256(S["control_trace"])
        act = next(e for e in chain if e["kind"] == "mmu_fault_activate")
        tr = next(e for e in chain if e["kind"] == "translation_result")
        lsu = next(e for e in chain if e["kind"] == "lsu_request")
        resp = next(e for e in chain if e["kind"] == "translation_response_received")
        dec = next(e for e in chain if e["kind"] == "squash_translation_decision")
        inv = next(e for e in chain if e["kind"] == "squash_translation_invoked")
        disc = next(e for e in chain if e["kind"] == "translation_request_discarded")
        cdd = next(e for e in chain if e["kind"] == "cache_dispatch_decision")
        S["act"] = act; S["tr"] = tr; S["lsu"] = lsu; S["resp"] = resp
        S["dec"] = dec; S["inv"] = inv; S["disc"] = disc; S["cdd"] = cdd

    # sanity assertions
    for S in SAMPLES:
        assert S["act"]["fault_id"] == 1, S["sid"]
        assert S["tr"]["fault_status"] == "NoFault", S["sid"]
        assert S["dec"]["decision"] == "discard_due_to_prior_squash", S["sid"]
        assert S["disc"]["terminal_reason"] == "prior_squash_before_translation_completion", S["sid"]
        assert S["cdd"]["dispatch_decision"] == "cache_dispatch_blocked_by_squash", S["sid"]
        assert S["lsu"]["parent"] == S["tr"]["event_id"]
        assert S["resp"]["parent"] == S["lsu"]["event_id"]
        assert S["dec"]["parent"] == S["resp"]["event_id"]
        assert S["inv"]["parent"] == S["dec"]["event_id"]
        assert S["disc"]["parent"] == S["inv"]["event_id"]
        assert S["cdd"]["parent"] == S["disc"]["event_id"]

    # Persist evidence for report generation + later steps
    with open(os.path.join(ROOT, "work", "obs0222_evidence.json"), "w") as fh:
        json.dump({S["sid"]: {"chain": S["chain"],
                              "trace_sha256": S["trace_sha256"],
                              "control_trace_sha256": S["control_trace_sha256"]}
                   for S in SAMPLES}, fh, indent=2, sort_keys=True)

    # ---- 1. experiment_status.csv ----
    es = load_csv(os.path.join(ROOT, "experiment_status.csv"))
    for S in SAMPLES:
        for r in es:
            if r["NewSampleRunID"] == S["sid"]:
                r["Completeness"] = "FULL"
                r["ArchitectureComplete"] = "True"
                r["TerminalState"] = TERMINAL_STATE
                r["Reason"] = ("fault activated (permission false->true), translation "
                               "returned NoFault, LSU issued request; translation response "
                               "received by LSQ, squash decision=discard_due_to_prior_squash, "
                               "squashTranslation() invoked, request discarded "
                               "(prior_squash_before_translation_completion), cache dispatch "
                               "blocked by squash -> complete fault-to-terminal chain (no SDC; "
                               "guest SIGSEGV is architectural, not the faulted instruction)")
                r["EvidencePath"] = "runs/W5X3_OBS/%s" % S["run_id"]
    write_csv(os.path.join(ROOT, "experiment_status.csv"),
              list(es[0].keys()), es)

    # ---- 2. terminal_symptoms.csv ----
    ts = load_csv(os.path.join(V3, "terminal_symptoms.csv"))
    for S in SAMPLES:
        for r in ts:
            if r["SampleRunID"] == S["sid"]:
                r["MicroarchTerminal"] = TERMINAL_STATE
                r["ArchStateImpact"] = ("翻译结果 NoFault 返回给 LSQ；因指令已在页表游走期间被 "
                                        "squash，翻译被 squashTranslation() 丢弃（TranslationSquashed，"
                                        "LSQ entry 已释放 -> self-destruct），请求未进入 Cache")
                r["SoftwareSymptom"] = ("请求在进入 Cache 前被丢弃（squash before memory access）；"
                                        "无 memory response / writeback / commit / 异常投递；"
                                        "Guest SIGSEGV 为架构拒绝（execute-only），非故障指令所致")
                r["TerminalEventID"] = str(S["disc"]["event_id"])
                r["TerminalEventKind"] = "translation_request_discarded"
                r["EvidenceSufficiency"] = "FULL"
    write_csv(os.path.join(V3, "terminal_symptoms.csv"),
              list(ts[0].keys()), ts)

    # ---- 3. propagation_chains.csv ----
    pc = load_csv(os.path.join(V3, "propagation_chains.csv"))
    for S in SAMPLES:
        a, t, q, rsp, dc = S["act"], S["tr"], S["lsu"], S["resp"], S["disc"]
        path = ("activation:%d(mmu_fault_activate)@%d -> translation:%d(translation_result)@%d"
                " -> request:%d(lsu_request)@%d -> response:%d(translation_response_received)@%d"
                " -> commit_squash:%d(translation_request_discarded)@%d" %
                (a["event_id"], a["tick"], t["event_id"], t["tick"], q["event_id"],
                 q["tick"], rsp["event_id"], rsp["tick"], dc["event_id"], dc["tick"]))
        for r in pc:
            if r["SampleRunID"] == S["sid"]:
                r["TerminalState"] = TERMINAL_STATE
                r["activation"] = "%d(mmu_fault_activate)@%d" % (a["event_id"], a["tick"])
                r["translation"] = "%d(translation_result)@%d" % (t["event_id"], t["tick"])
                r["request"] = "%d(lsu_request)@%d" % (q["event_id"], q["tick"])
                r["response"] = "%d(translation_response_received)@%d" % (rsp["event_id"], rsp["tick"])
                r["writeback"] = ""
                r["consumer"] = ""
                r["commit_squash"] = "%d(translation_request_discarded)@%d" % (dc["event_id"], dc["tick"])
                r["Path"] = path
                r["Unobserved"] = ""
                r["NotApplicable"] = "mutation,writeback,consumer"
                r["Boundary"] = ""
                r["Completeness"] = "FULL"
    write_csv(os.path.join(V3, "propagation_chains.csv"),
              list(pc[0].keys()), pc)

    # ---- 4. authoritative_trace_index.csv ----
    ati = load_csv(os.path.join(V3, "authoritative_trace_index.csv"))
    for S in SAMPLES:
        for r in ati:
            if r["SampleRunID"] == S["sid"]:
                r["ActualRunID"] = S["run_id"]
                r["RunKind"] = "obs0222"
                r["TracePath"] = "runs/W5X3_OBS/%s/Trace/prop_evt.txt.gz" % S["run_id"]
                r["TraceSHA256"] = S["trace_sha256"]
                r["BuildHash"] = NEW_BUILD
                r["ControlRunID"] = S["control_run"]
                r["ActivationEventID"] = str(S["act"]["event_id"])
                r["AnalyzedFileVersion"] = r["TracePath"]
    write_csv(os.path.join(V3, "authoritative_trace_index.csv"),
              list(ati[0].keys()), ati)

    # ---- 5. control_map.json ----
    cm = json.load(open(os.path.join(ANALYSIS, "control_map.json")))
    for S in SAMPLES:
        for e in cm:
            if e["SampleRunID"] == S["sid"]:
                e["FaultBuildHash"] = NEW_BUILD
                e["FaultTraceSHA256"] = S["trace_sha256"]
                e["ControlBuildHash"] = NEW_BUILD
                e["ControlRunID"] = S["control_run"]
                e["ControlTraceSHA256"] = S["control_trace_sha256"]
                e["BuildMatches"] = True
    json.dump(cm, open(os.path.join(ANALYSIS, "control_map.json"), "w"),
              indent=2, sort_keys=True)

    # ---- 6. partial23_repair_comparison.csv ----
    pr = load_csv(os.path.join(V3, "partial23_repair_comparison.csv"))
    for S in SAMPLES:
        for r in pr:
            if r["SampleRunID"] == S["sid"]:
                r["FinalCompleteness"] = "FULL"
                r["PreviousMissingStages"] = ("response / writeback / consumer / commit "
                                              "(previously: ROI ended at lsu_request)")
                r["NewlyObservedStages"] = ("translation_response_received + squash_translation_"
                                            "decision + squash_translation_invoked + "
                                            "translation_request_discarded + cache_dispatch_"
                                            "decision -> SQUASHED_BEFORE_MEMORY_ACCESS")
                r["InstrumentationAdded"] = "LSQ translation-lifecycle observation (mmuNoteLsqTranslationFinish)"
                r["RerunPerformed"] = "True"
                r["NewRunID"] = S["run_id"]
                r["NewBuildHash"] = NEW_BUILD
                r["NewTracePath"] = "runs/W5X3_OBS/%s/Trace/prop_evt.txt.gz" % S["run_id"]
                r["NewTraceSHA256"] = S["trace_sha256"]
                r["NewlyEstablishedCausalEdges"] = "parent_event_id(translation_response_received->squash_translation_decision->squash_translation_invoked->translation_request_discarded->cache_dispatch_decision)"
                r["FinalTerminalEvent"] = "%d(translation_request_discarded)" % S["disc"]["event_id"]
                r["FinalSoftwareSymptom"] = ("请求在进入 Cache 前被丢弃（squash before memory access）；"
                                             "无 memory response / writeback / commit；Guest SIGSEGV "
                                             "为架构拒绝，非故障指令所致")
                r["RemainingMissingStages"] = "none"
                r["RepairConclusion"] = ("运行时证明完整 fault->squash-discard 链，升级为 FULL "
                                         "(SQUASHED_BEFORE_MEMORY_ACCESS)")
    write_csv(os.path.join(V3, "partial23_repair_comparison.csv"),
              list(pr[0].keys()), pr)

    print("data files updated for", [S["sid"] for S in SAMPLES])
    print("T01 terminal event:", SAMPLES[0]["disc"]["event_id"],
          "T02 terminal event:", SAMPLES[1]["disc"]["event_id"])


if __name__ == "__main__":
    main()
