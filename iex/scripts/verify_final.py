#!/usr/bin/env python3
"""Independent post-run verification of the v3 evidence set."""
import csv
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC = "IEX_WHEN_5x3_v3_2026-11-23"
RESULTS = os.path.join(ROOT, "results", SPEC)
DELIVERY = os.path.join(ROOT, "delivery", SPEC)


def load_json(p):
    with open(p) as f:
        return json.load(f)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    faults = list(csv.DictReader(open(os.path.join(
        RESULTS, "audit", "fault_runs.csv"))))
    controls = load_json(os.path.join(RESULTS, "audit", "controls.json"))
    failures = []
    ok = 0

    def check(cid, cond, msg):
        if not cond:
            failures.append({"CaseID": cid, "check": msg})

    for r in faults:
        cid = r["CaseID"]
        p = os.path.join(RESULTS, "audit", "propagation", cid + ".json")
        d = load_json(p)
        e = d["evidence"]
        inj = e.get("injection") or {}
        lc = e.get("target_lifecycle") or {}
        k = int(r["TargetOrdinal"])
        n = int(r["EligibleCount_N"])
        check(cid, 1 <= k <= n and n >= 20, "ordinal/N range")
        check(cid, inj.get("applied") == 1, "inject applied=1")
        check(cid, inj.get("candidate_ordinal") == k, "inject ordinal=K")
        check(cid, (e.get("run_end") or {}).get(
            "timing_satisfied") == 1, "timing satisfied")
        for ev in ("inst_issue", "inst_exec_begin", "inst_exec_end",
                   "writeback"):
            check(cid, bool(lc.get(ev)), "lifecycle " + ev)
        check(cid, bool(lc.get("commit")) or e.get("target_squashed"),
              "commit or squash")
        stores = e.get("selected_slot_stores") or []
        check(cid, bool(stores), "selected slot store observed")
        diffs = e.get("output_diffs") or []
        if r["ContextID"] == "C03":
            check(cid, r["ActualTerminal"] == "MASKED", "C03 MASKED")
            check(cid, diffs == [], "C03 no visible delta")
            check(cid, not (e.get("committed_stores") or []),
                  "C03 no reachable committed store")
            eors = [x for x in (e.get("edges") or [])
                    if x.get("consumer_opcode") == "eor"]
            if r["ModelID"] == "IEX-M005":
                check(cid, bool(lc.get("branch_resolve") or
                                lc.get("branch_resolve_iew")),
                      "C03 M005 branch path evidence")
            elif r["ModelID"] == "IEX-M006":
                check(cid, bool(eors), "C03 M006 EOR consumer")
            else:
                check(cid, len(e.get("edges") or []) == 1 and bool(eors),
                      "C03 exactly one EOR consumer")
        else:
            check(cid, r["ActualTerminal"] == "SDC", "non-C03 SDC")
            check(cid, diffs == [k - 1], "delta only selected slot")
            if r["ModelID"] != "IEX-M005":
                check(cid, len(e.get("edges") or []) > 0,
                      "data edge exists")
        if r["ModelID"] == "IEX-M003":
            check(cid, inj.get("result_l214_before") == 1 and
                  inj.get("result_l214_after") == 0,
                  "M003 L214 1->0")
            w = e.get("model_witnesses") or {}
            check(cid, all(w.get(x) for x in (
                "model_witness_l215", "model_witness_l216",
                "model_witness_l217")), "M003 L215-217 witnesses")
        if r["ModelID"] == "IEX-M005":
            check(cid, bool(lc.get("branch_resolve") or
                            lc.get("branch_resolve_iew")),
                  "M005 branch resolved")
            check(cid, bool(e.get("branch_committed_path")),
                  "M005 committed landing")
        if r["ModelID"] == "IEX-M006":
            cc_edges = [x for x in (e.get("edges") or [])
                        if x["producer_seq"] == e["target_seq"] and
                        x["reg_class"] == "condition_code"]
            check(cid, bool(cc_edges), "M006 CC producer->CSEL edge")
            csel = (e.get("model_witnesses") or {}).get(
                "model_witness_csel") or []
            check(cid, any(x.get("cc_producer_seq") == e["target_seq"]
                           for x in csel), "M006 CSEL CC version")
        if r["ContextID"] == "C05":
            os_ = e.get("older_state") or {}
            check(cid, (os_.get("older_unresolved_branch_count") or 0) > 0,
                  "C05 older unresolved at hook")
            check(cid, e.get("older_resolved_after_hook") is True,
                  "C05 older resolves after hook")
            check(cid, (os_.get("older_unresolved_branch_seq") or 0) <
                  e["target_seq"], "C05 older_seq < target_seq")
        if not failures or failures[-1]["CaseID"] != cid:
            ok += 1

    # control-side checks
    for c in controls:
        cid = c["ControlID"]
        check(cid, c["MeasuredEligibleN"] >= 20, "control N>=20")
        check(cid, len({c["T01_Ordinal"], c["T02_Ordinal"],
                        c["T03_Ordinal"]}) == 3, "control ordinals distinct")
        check(cid, c["RepeatCensus_PASS"], "control census repeat")
        check(cid, c["AllSlotsGolden"], "control all slots golden")
        att = sorted(glob.glob(os.path.join(
            RESULTS, "controls", cid, "attempt-*")))[-1]
        check(cid, os.path.exists(os.path.join(att, "trace.jsonl")),
              "control trace exists")

    report = {
        "spec": SPEC,
        "faults_checked": len(faults),
        "controls_checked": len(controls),
        "checks_failed": len(failures),
        "failures": failures,
        "all_pass": len(failures) == 0,
    }
    out = os.path.join(DELIVERY, "verification_report.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({"all_pass": report["all_pass"],
                      "faults": len(faults),
                      "controls": len(controls),
                      "failures": len(failures)}, indent=2))
    if failures:
        print(json.dumps(failures[:20], indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
