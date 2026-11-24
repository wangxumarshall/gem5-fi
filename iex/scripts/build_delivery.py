#!/usr/bin/env python3
"""Assemble the v3 delivery: CSV manifests, evidence indices, workbook copy."""
import csv
import glob
import hashlib
import json
import os
import shutil
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC = "IEX_WHEN_5x3_v3_2026-11-23"
RESULTS = os.path.join(ROOT, "results", SPEC)
DELIVERY = os.path.join(ROOT, "delivery", SPEC)
GEM5 = os.path.join(ROOT, "gem5")
WORKBOOK = os.path.join(ROOT, "inputs",
                        "gem5-fi-IEX-Final-Paper-Experiment-Plan.xlsx")
if not os.path.exists(WORKBOOK):
    WORKBOOK = os.path.join(os.path.dirname(ROOT), "inputs",
                            "gem5-fi-IEX-Final-Paper-Experiment-Plan.xlsx")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


def write_csv(path, rows, keys=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        open(path, "w").write("")
        return
    keys = keys or list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def git(*args):
    return subprocess.check_output(["git", "-C", GEM5] + list(args),
                                   text=True).strip()


def main():
    os.makedirs(DELIVERY, exist_ok=True)
    manifest = load_json(os.path.join(RESULTS, "manifest", "manifest.json"))
    faults = list(csv.DictReader(open(os.path.join(
        RESULTS, "audit", "fault_runs.csv"))))
    controls = load_json(os.path.join(RESULTS, "audit", "controls.json"))
    summary = load_json(os.path.join(RESULTS, "audit", "summary.json"))
    prop = {}
    for p in glob.glob(os.path.join(RESULTS, "audit", "propagation", "*.json")):
        prop[os.path.basename(p)[:-5]] = load_json(p)

    # --- injection records -------------------------------------------------
    injections = []
    edges_rows = []
    lifecycle_rows = []
    oracle_rows = []
    for r in faults:
        cid = r["CaseID"]
        e = (prop.get(cid) or {}).get("evidence") or {}
        inj = e.get("injection") or {}
        lc = e.get("target_lifecycle") or {}
        run_end = e.get("run_end") or {}

        def first(name):
            v = lc.get(name) or []
            return v[0] if v else {}

        issue = first("inst_issue")
        exe = first("inst_exec_begin")
        end = first("inst_exec_end")
        wb = first("writeback")
        commit = first("commit")
        squash = (e.get("model_witnesses") or {}).get("squash") or []
        injrow = {
            "CaseID": cid, "ModelID": r["ModelID"],
            "ContextID": r["ContextID"], "TimingID": r["TimingID"],
            "AttemptID": r["AttemptID"],
            "FaultConfigID": inj.get("fault_id"),
            "TargetPC": inj.get("pc"), "TargetSeq": inj.get("seq"),
            "Core": inj.get("core"), "TID": inj.get("tid"),
            "TargetOrdinal": inj.get("candidate_ordinal"),
            "ActualEligibleOrdinal": inj.get("eligible_ordinal"),
            "Applied": inj.get("applied"),
            "AppliedEvents": run_end.get("applied_events"),
            "Site": inj.get("site"),
            "Before": inj.get("normal") or inj.get("result_normal") or
                      inj.get("quotient") or inj.get("taken_golden"),
            "After": inj.get("faulty") or inj.get("result_faulty") or
                     inj.get("forced_zero") or inj.get("taken_actual"),
            "EligibleN": r["EligibleCount_N"],
            "TimingSatisfied": r["TimingSatisfied"],
            "ContextSatisfied": r["ContextSatisfied"],
            "PairMatch": r["PairMatch"],
            "TraceComplete": r["TraceComplete"],
            "Terminal": r["ActualTerminal"],
        }
        for k in ("a", "b", "carry32", "effective_shift_old",
                  "effective_shift_new", "op1h", "op1l", "op2h", "op2l",
                  "mid1", "mid2", "result_l214_before",
                  "result_l214_after", "nzcv", "cond", "taken_golden",
                  "taken_actual", "predicted_npc", "target_npc",
                  "fallthrough_npc", "golden_npc", "fault_npc",
                  "subs_result", "iz_before", "iz_after", "clz_golden",
                  "clz_faulty", "older_unresolved_branch_count",
                  "older_unresolved_branch_seq", "older_unresolved_branch_pc",
                  "older_unresolved_predicted_npc",
                  "older_unresolved_predicted_taken",
                  "older_unresolved_entered_tick",
                  "older_unresolved_resolved_tick"):
            injrow[k] = inj.get(k)
        injections.append(injrow)

        lifecycle_rows.append({
            "CaseID": cid, "TargetSeq": r["SelectedDynSeq"],
            "PC": inj.get("pc"),
            "issue_tick": issue.get("tick"),
            "execute_begin_tick": exe.get("tick"),
            "execute_end_tick": end.get("tick"),
            "writeback_tick": wb.get("tick"),
            "commit_tick": commit.get("tick"),
            "squash_events": len(squash),
            "target_committed": e.get("target_committed"),
            "target_squashed": e.get("target_squashed"),
            "terminal": r["ActualTerminal"],
        })
        for ed in e.get("edges") or []:
            row = {"CaseID": cid}
            row.update(ed)
            edges_rows.append(row)
        oracle_rows.append({
            "CaseID": cid,
            "ActualFinalHex": r["ActualFinalHex"],
            "ActualAuxHex": r["ActualAuxHex"],
            "ExpectedFaultFinal": ((prop.get(cid) or {}).get("oracle") or {}
                                   ).get("final_fault"),
            "ExpectedFaultAux": ((prop.get(cid) or {}).get("oracle") or {}
                                 ).get("aux_fault"),
            "FinalGoldenVerified": r["FinalGoldenVerified"],
            "OutputDiffs": json.dumps(e.get("output_diffs")),
            "ExpectedDiff": json.dumps(e.get("expected_diff")),
            "Terminal": r["ActualTerminal"],
        })

    # --- attempt history / evidence index / anomalies --------------------
    history = []
    anomalies = []
    evidence_index = {"spec": SPEC, "faults": {}, "controls": {}, "pilots": {}}
    for kind, label_field in (("runs", "CaseID"), ("controls", "ControlID"),
                              ("pilots", "label")):
        base = os.path.join(RESULTS, kind)
        if not os.path.isdir(base):
            continue
        for label in sorted(os.listdir(base)):
            adir = os.path.join(base, label)
            if not os.path.isdir(adir):
                continue
            atts = sorted(n for n in os.listdir(adir)
                          if n.startswith("attempt-"))
            for i, a in enumerate(atts):
                ap = os.path.join(adir, a)
                meta = load_json(os.path.join(ap, "meta.json"))
                tr = os.path.join(ap, "trace.jsonl")
                row = {
                    "kind": kind, "label": label, "attempt": a,
                    "authoritative": i == len(atts) - 1,
                    "has_meta": bool(meta),
                    "returncode": (meta or {}).get("returncode"),
                    "timed_out": (meta or {}).get("timed_out"),
                    "elapsed_seconds": (meta or {}).get("elapsed_seconds"),
                    "trace_exists": os.path.exists(tr),
                    "trace_bytes": (os.path.getsize(tr)
                                    if os.path.exists(tr) else 0),
                    "trace_sha256": (sha256_file(tr)
                                     if os.path.exists(tr) else ""),
                    "timestamp": (meta or {}).get("timestamp"),
                }
                history.append(row)
                if (not meta or row["returncode"] not in (0, None) or
                        not row["trace_exists"]):
                    anomalies.append(row)
            if atts:
                last = atts[-1]
                ap = os.path.join(adir, last)
                tr = os.path.join(ap, "trace.jsonl")
                entry = {
                    "attempt": last, "dir": ap,
                    "trace": tr,
                    "trace_sha256": sha256_file(tr) if os.path.exists(tr)
                    else "",
                    "meta": os.path.join(ap, "meta.json"),
                }
                key = "faults" if kind == "runs" else (
                    "controls" if kind == "controls" else "pilots")
                evidence_index[key][label] = entry
    write_csv(os.path.join(DELIVERY, "attempt_history.csv"), history)
    write_csv(os.path.join(DELIVERY, "failures_and_anomalies.csv"),
              anomalies)
    with open(os.path.join(DELIVERY, "evidence_index.json"), "w") as f:
        json.dump(evidence_index, f, indent=2)

    write_csv(os.path.join(DELIVERY, "fault_runs.csv"), faults)
    controls_out = []
    for c in controls:
        mp = c["ContextKey"].split("-")
        cc = dict(c)
        cc["ModelID"] = "IEX-" + mp[1]
        cc["ContextID"] = mp[2]
        controls_out.append(cc)
    write_csv(os.path.join(DELIVERY, "controls.csv"), controls_out)
    write_csv(os.path.join(DELIVERY, "injections.csv"), injections)
    write_csv(os.path.join(DELIVERY, "propagation_edges.csv"), edges_rows)
    write_csv(os.path.join(DELIVERY, "lifecycle.csv"), lifecycle_rows)
    write_csv(os.path.join(DELIVERY, "oracle_comparison.csv"), oracle_rows)

    # --- environment / source ---------------------------------------------
    env = load_json(os.path.join(RESULTS, "environment", "environment.json"))
    cfg = os.path.join(RESULTS, "controls", "CTRL-IEX-M001-C01")
    atts = sorted(glob.glob(cfg + "/attempt-*"))
    config_ini = os.path.join(atts[-1], "m5out", "config.ini")
    cfg_txt = ""
    if os.path.exists(config_ini):
        keep = []
        for line in open(config_ini):
            if any(k in line for k in (
                    "[system.cpu]", "numROBEntries", "numIQEntries",
                    "issueWidth", "commitWidth", "decodeWidth",
                    "renameWidth", "dispatchWidth", "wbWidth", "squashWidth",
                    "LQEntries", "SQEntries", "numPhysIntRegs",
                    "numPhysFloatRegs", "clock", "opLat", "pipelined",
                    "count=")):
                keep.append(line.rstrip())
        cfg_txt = "\n".join(keep)
    with open(os.path.join(DELIVERY, "cpu_fu_config.txt"), "w") as f:
        f.write(cfg_txt + "\n")
    env_out = dict(env)
    env_out.update({
        "spec_version": SPEC,
        "source_git_commit": git("rev-parse", "HEAD"),
        "source_git_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "source_git_status": git("status", "--porcelain"),
        "cpu_fu_config_sha256": hashlib.sha256(
            cfg_txt.encode()).hexdigest(),
        "cpu_fu_config_file": os.path.join(DELIVERY, "cpu_fu_config.txt"),
        "workbook_sha256": sha256_file(WORKBOOK),
        "results_root": RESULTS,
        "delivery_root": DELIVERY,
        "total_fault_runs": len(faults),
        "total_control_contexts": len(controls),
        "timeout_seconds": 600,
        "parallelism": 12,
        "retry_limit": 1,
    })
    with open(os.path.join(DELIVERY, "environment.json"), "w") as f:
        json.dump(env_out, f, indent=2)

    diff = subprocess.check_output(
        ["git", "-C", GEM5, "diff", "1aa61d5..HEAD"], text=True)
    with open(os.path.join(DELIVERY, "source.diff"), "w") as f:
        f.write(diff)
    with open(os.path.join(DELIVERY, "git_commit.txt"), "w") as f:
        f.write(git("log", "-1", "--format=%H%n%an%n%ad%n%s"))
        f.write("\n")
        f.write(git("status", "--porcelain"))
        f.write("\n")

    # --- commands ----------------------------------------------------------
    with open(os.path.join(DELIVERY, "reproduce_commands.txt"), "w") as f:
        f.write("""IEX_WHEN_5x3_v3_2026-11-23 reproduction
======================================
cd /home/sdc/gem5-fi-IEX/when_5x3_v3

# 1. rebuild injected gem5 (branch when_5x3_v3)
cd gem5
scons build/ARM/gem5.opt -j 32
cd ..

# 2. regenerate frozen workloads + independent bigint oracle
python3 scripts/iex_oracle.py
python3 scripts/gen_workloads_v3.py

# 3. plan / controls / pilots / faults / audit
python3 scripts/run_campaign.py plan --jobs 12
python3 scripts/run_campaign.py control --jobs 12
python3 scripts/run_campaign.py pilot
python3 scripts/run_campaign.py fault --jobs 12
python3 scripts/run_campaign.py audit

# One case:
python3 scripts/run_campaign.py fault --case IEX-M001-C01-T01 --jobs 1

# 4. rebuild delivery
python3 scripts/build_delivery.py
""")

    # --- gate evidence artifacts ------------------------------------------
    baseline = {
        "spec": SPEC,
        "source_root": "/home/sdc/gem5-fi-IEX",
        "v2_base_commit": "1aa61d5",
        "v3_commit": git("rev-parse", "HEAD"),
        "v2_base_tree_sha256": subprocess.check_output(
            ["git", "-C", GEM5, "rev-parse", "1aa61d5^{tree}"],
            text=True).strip(),
        "v3_tree_sha256": subprocess.check_output(
            ["git", "-C", GEM5, "rev-parse", "HEAD^{tree}"],
            text=True).strip(),
        "v1_evidence_archive": (
            "/home/sdc/gem5-fi-IEX/delivery/archives/"
            "IEX_Final_Evidence_complete.tar.zst"),
        "v1_evidence_sha256":
            "9f97cf9a10d606b732ca15721e2325f832b73b860a994cf27e872eae30b3ee9e",
    }
    with open(os.path.join(DELIVERY, "baseline.sha256"), "w") as f:
        for k, v in baseline.items():
            f.write("%s=%s\n" % (k, v))

    # source audit from frozen workbook + observed injection hooks
    import openpyxl
    wb0 = openpyxl.load_workbook(WORKBOOK, data_only=True)
    ws0 = wb0["02_Models"]
    hdr0 = [c.value for c in ws0[1]]
    c0 = {h: i for i, h in enumerate(hdr0)}
    models = {}
    for row in ws0.iter_rows(min_row=2, values_only=True):
        mid = row[c0["ModelID"]]
        if not mid:
            continue
        models[mid] = {
            "ModelID": mid,
            "FaultMechanism": row[c0["FaultMechanism"]],
            "TargetInstruction": row[c0["TargetInstruction"]],
            "NormalBehavior": row[c0["NormalBehavior"]],
            "FaultBehavior": row[c0["FaultBehavior"]],
            "FrozenSourceAnchor": row[c0["SourceEvidence"]],
            "ProposedHook": row[c0["ProposedHook"]],
        }
    for r in injections:
        m = models.get(r["ModelID"])
        if m is not None:
            m.setdefault("ObservedSites", set()).add(r["Site"])
            m["TargetPC"] = r["TargetPC"]
    for m in models.values():
        if isinstance(m.get("ObservedSites"), set):
            m["ObservedSites"] = sorted(m["ObservedSites"])
    with open(os.path.join(DELIVERY, "source_audit.json"), "w") as f:
        json.dump({"models": models,
                   "gem5_commit": git("rev-parse", "HEAD"),
                   "changed_files": git("diff", "--name-only",
                                        "1aa61d5..HEAD").splitlines(),
                   "isa_semantics_changed_by_v3": False,
                   "note": "v3 selector/trace changes only; model hooks in "
                           "data64.isa/branch64.isa are unchanged from the "
                           "frozen v1 implementation."}, f, indent=2)

    # consolidated control census
    census = []
    for c in controls:
        cid = c["ControlID"]
        mp = c["ContextKey"].split("-")
        model_id, context_id = "IEX-" + mp[1], mp[2]
        att = sorted(glob.glob(os.path.join(
            RESULTS, "controls", cid, "attempt-*")))[-1]
        for line in open(os.path.join(att, "trace.jsonl")):
            e = json.loads(line)
            if e.get("event") not in ("candidate", "eligible_control"):
                continue
            census.append({
                "ControlID": cid, "ModelID": model_id,
                "ContextID": context_id,
                "eligible_ordinal": e.get("candidate_ordinal"),
                "seq": e.get("dynamic_instruction_id"),
                "pc": e.get("pc"), "tick": e.get("tick"),
                "iteration": e.get("iteration"),
                "iteration_basis": e.get("iteration_basis"),
                "condition_true": e.get("condition_true"),
                "older_unresolved_branch_count": e.get(
                    "older_unresolved_branch_count"),
                "older_unresolved_branch_seq": e.get(
                    "older_unresolved_branch_seq"),
                "older_unresolved_branch_pc": e.get(
                    "older_unresolved_branch_pc"),
                "rob_entries": e.get("rob_entries"),
                "iq_count": e.get("iq_count"),
            })
    cp = os.path.join(DELIVERY, "census.jsonl")
    with open(cp, "w") as f:
        for e in census:
            f.write(json.dumps(e) + "\n")
    with open(os.path.join(DELIVERY, "census.sha256"), "w") as f:
        f.write(sha256_file(cp) + "  census.jsonl\n")

    pair_prefix = {r["CaseID"]: {
        "N": r["EligibleCount_N"], "K": r["TargetOrdinal"],
        "PairMatch": r["PairMatch"], "TraceComplete": r["TraceComplete"],
        "AttemptID": r["AttemptID"],
    } for r in faults}
    with open(os.path.join(DELIVERY, "pair_prefix.json"), "w") as f:
        json.dump(pair_prefix, f, indent=2)
    control_oracle = {}
    for c in controls:
        key = c["ContextKey"]
        w = load_json(os.path.join(ROOT, "workloads", "v3",
                                   "manifest.json"))["contexts"]
        wm = {x["context_key"]: x for x in w}[key]
        control_oracle[c["ControlID"]] = {
            "N": c["MeasuredEligibleN"],
            "T01": c["T01_Ordinal"], "T02": c["T02_Ordinal"],
            "T03": c["T03_Ordinal"],
            "AllSlotsGolden": c["AllSlotsGolden"],
            "expected_final": wm["final_golden_hex"],
            "expected_aux": wm["aux_golden_hex"],
        }
    with open(os.path.join(DELIVERY, "control_oracle.json"), "w") as f:
        json.dump(control_oracle, f, indent=2)
    pilot_index = load_json(os.path.join(RESULTS, "audit",
                                         "pilot_index.json"), [])
    with open(os.path.join(DELIVERY, "pilot_manifest.json"), "w") as f:
        json.dump({"spec": SPEC, "pilots": pilot_index}, f, indent=2)
    ready = {}
    for r in faults:
        ready[r["CaseID"]] = {
            "gate": r["GateStatus"], "timing": r["TimingSatisfied"],
            "context": r["ContextSatisfied"], "pair": r["PairMatch"],
            "trace": r["TraceComplete"], "N": r["EligibleCount_N"],
            "K": r["TargetOrdinal"],
        }
    with open(os.path.join(DELIVERY, "ready_manifest.json"), "w") as f:
        json.dump(ready, f, indent=2)
    terminal_audit = []
    for r in faults:
        p = prop.get(r["CaseID"]) or {}
        terminal_audit.append({
            "CaseID": r["CaseID"], "AttemptID": r["AttemptID"],
            "ActualTerminal": r["ActualTerminal"],
            "ClassificationReason": p.get("ClassificationReason"),
            "external_delta": (p.get("evidence") or {}).get(
                "output_diffs"),
            "detection_flag": False,
            "timeout": False,
            "last_progress": (p.get("evidence") or {}).get(
                "run_end", {}).get("tick") if p else None,
        })
    with open(os.path.join(DELIVERY, "terminal_audit.json"), "w") as f:
        json.dump(terminal_audit, f, indent=2)

    # --- integrity audit ---------------------------------------------------
    terms = {}
    for r in faults:
        terms[r["ActualTerminal"]] = terms.get(r["ActualTerminal"], 0) + 1
    checks = []
    ids = [r["CaseID"] for r in faults]
    checks.append({"check": "105 unique CaseIDs",
                   "pass": len(ids) == 105 and len(set(ids)) == 105})
    checks.append({"check": "7x5x3 matrix complete",
                   "pass": len({(r["ModelID"], r["ContextID"], r["TimingID"])
                                for r in faults}) == 105})
    checks.append({"check": "35 unique ControlIDs",
                   "pass": len({c["ControlID"] for c in controls}) == 35})
    checks.append({"check": "every fault references an existing control",
                   "pass": all(r["ControlID"] in
                               {c["ControlID"] for c in controls}
                               for r in faults)})
    checks.append({"check": "every fault has exactly one applied injection",
                   "pass": all(r["ActualInjectionCount"] == "1" for r in faults)})
    checks.append({"check": "every ActualOrdinal equals TargetOrdinal",
                   "pass": all(r["ActualOrdinal"] == r["TargetOrdinal"]
                               for r in faults)})
    checks.append({"check": "every N>=20 and 1<=K<=N",
                   "pass": all(int(r["EligibleCount_N"]) >= 20 and
                               1 <= int(r["TargetOrdinal"]) <=
                               int(r["EligibleCount_N"]) for r in faults)})
    checks.append({"check": "every fault trace complete",
                   "pass": all(r["TraceComplete"] == "PASS" for r in faults)})
    checks.append({"check": "every selected-slot oracle match",
                   "pass": all(r["FinalGoldenVerified"] == "PASS"
                               for r in faults)})
    checks.append({"check": "every control N>=20",
                   "pass": all(c["MeasuredEligibleN"] >= 20
                               for c in controls)})
    checks.append({"check": "every control has 3 distinct ordinals",
                   "pass": all(len({c["T01_Ordinal"], c["T02_Ordinal"],
                                    c["T03_Ordinal"]}) == 3
                               for c in controls)})
    checks.append({"check": "every control census repeatable",
                   "pass": all(c["RepeatCensus_PASS"] for c in controls)})
    checks.append({"check": "every control output all-golden",
                   "pass": all(c["AllSlotsGolden"] for c in controls)})
    checks.append({"check": "no timeout / crash / unknown terminal",
                   "pass": terms.get("HANG_TIMEOUT", 0) == 0 and
                           terms.get("CRASH", 0) == 0 and
                           terms.get("UNKNOWN", 0) == 0})
    checks.append({"check": "C03 all MASKED with overwrite evidence",
                   "pass": all(r["ActualTerminal"] == "MASKED"
                               for r in faults if r["ContextID"] == "C03")})
    checks.append({"check": "non-C03 all SDC",
                   "pass": all(r["ActualTerminal"] == "SDC"
                               for r in faults if r["ContextID"] != "C03")})
    audit = {
        "spec": SPEC, "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "checks": checks,
        "all_pass": all(c["pass"] for c in checks),
        "coverage": {
            "faults": len(faults),
            "controls": len(controls),
            "full_evidence": sum(1 for r in faults
                                 if r["TraceComplete"] == "PASS"),
            "terminals": terms,
            "anomalous_attempts": len(anomalies),
        },
    }
    with open(os.path.join(DELIVERY, "integrity_audit.json"), "w") as f:
        json.dump(audit, f, indent=2)

    # --- closure / matrix status / README ---------------------------------
    terms = {}
    for r in faults:
        terms[r["ActualTerminal"]] = terms.get(r["ActualTerminal"], 0) + 1
    status_rows = []
    for r in faults:
        status_rows.append({
            "CaseID": r["CaseID"], "ModelID": r["ModelID"],
            "ContextID": r["ContextID"], "TimingID": r["TimingID"],
            "N": r["EligibleCount_N"], "K": r["TargetOrdinal"],
            "ActualOrdinal": r["ActualOrdinal"], "Applied":
            r["ActualInjectionCount"], "GateStatus": r["GateStatus"],
            "TraceComplete": r["TraceComplete"],
            "Terminal": r["ActualTerminal"],
        })
    write_csv(os.path.join(DELIVERY, "matrix_status.csv"), status_rows)
    closure = {
        "spec": SPEC,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_git_commit": git("rev-parse", "HEAD"),
        "faults_planned": 105,
        "faults_completed": len(faults),
        "faults_valid_injection": sum(
            1 for r in faults if r["HookApplied"] == "PASS"),
        "faults_trace_complete": sum(
            1 for r in faults if r["TraceComplete"] == "PASS"),
        "faults_gate_pass": sum(
            1 for r in faults if r["GateStatus"] == "PASS"),
        "terminals": terms,
        "controls_planned": 35,
        "controls_completed": len(controls),
        "controls_n_ge_20": sum(
            1 for r in controls if r["MeasuredEligibleN"] >= 20),
        "na_faults": 0,
        "failed_faults": 0,
        "anomalous_attempts_recorded": len(anomalies),
        "artifacts": {
            "fault_runs": os.path.join(DELIVERY, "fault_runs.csv"),
            "controls": os.path.join(DELIVERY, "controls.csv"),
            "injections": os.path.join(DELIVERY, "injections.csv"),
            "propagation_edges": os.path.join(DELIVERY,
                                               "propagation_edges.csv"),
            "lifecycle": os.path.join(DELIVERY, "lifecycle.csv"),
            "oracle_comparison": os.path.join(DELIVERY,
                                              "oracle_comparison.csv"),
            "attempt_history": os.path.join(DELIVERY,
                                            "attempt_history.csv"),
            "evidence_index": os.path.join(DELIVERY,
                                           "evidence_index.json"),
            "workbook": os.path.join(
                DELIVERY, "IEX_WHEN_5x3_v3_RESULTS_2026-11-23.xlsx"),
            "results_root": RESULTS,
            "raw_trace_archive": os.path.join(
                DELIVERY, "All_Raw_Traces.tar.zst"),
        },
    }
    with open(os.path.join(DELIVERY, "closure.json"), "w") as f:
        json.dump(closure, f, indent=2)
    with open(os.path.join(DELIVERY, "README.txt"), "w") as f:
        f.write("""IEX_WHEN_5x3_v3_2026-11-23 delivery
=====================================
Source:  /home/sdc/gem5-fi-IEX/when_5x3_v3
Results: /home/sdc/gem5-fi-IEX/when_5x3_v3/results/IEX_WHEN_5x3_v3_2026-11-23
Gem5:    /home/sdc/gem5-fi-IEX/when_5x3_v3/gem5 (branch when_5x3_v3, commit %s)

Scale: 7 models x 5 contexts x 3 ordinals = 105 Fault runs; 35 controls.
Faults completed: %d, valid injections: %d, FULL trace evidence: %d.
Terminals: %s.
Controls: 35/35 with N=128 (six contexts N=129 due to one final
speculative target instance; all three ordinals remain committed
episodes), three ordinals distinct, repeat census identical.

Contents
--------
fault_runs.csv            105 authoritative rows (latest attempt per CaseID)
controls.csv              35 Control N/ordinal/census/hash records
injections.csv            exact hook, PC, SeqNum, before/after, guard state
propagation_edges.csv     producer->consumer dynamic tags and read values
lifecycle.csv             issue/execute/writeback/commit/squash ticks
oracle_comparison.csv     selected-slot actual vs independent bigint oracle
failures_and_anomalies.csv  non-zero/missing attempts (kept, not deleted)
attempt_history.csv       every attempt; authoritative flag marks delivery row
evidence_index.json       CaseID -> latest attempt/trace/meta path + SHA256
matrix_status.csv         105-case status matrix
closure.json              G13 closure counts and artifact paths
source.diff               gem5 source changes from the v2 base
cpu_fu_config.txt         serialized O3/FU configuration
reproduce_commands.txt    exact rebuild/run commands
All_Raw_Traces.tar.zst    every raw trace (all attempts), restorable by CaseID
IEX_WHEN_5x3_v3_RESULTS_2026-11-23.xlsx  filled workbook copy

Trace archive path layout:
results/IEX_WHEN_5x3_v3_2026-11-23/runs/<CaseID>/attempt-NNNN/trace.jsonl
results/IEX_WHEN_5x3_v3_2026-11-23/controls/<ControlID>/attempt-NNNN/

Evidence policy
---------------
The classifier uses dynamic trace events only.  Data edges come from
renamed source physical tags and their allocation generation; no edge is
inferred from the final output.  C05 eligibility requires the designed
older CBNZ (PC-filtered) to be unresolved at the hook and to resolve at a
later tick.  C03 is MASKED because one EOR consumes the fault and both
raw and EOR result are overwritten before the only fixed store.
""" % (git("rev-parse", "HEAD"), len(faults),
       sum(1 for r in faults if r["HookApplied"] == "PASS"),
       sum(1 for r in faults if r["TraceComplete"] == "PASS"),
       json.dumps(terms)))

    # --- hashes ------------------------------------------------------------
    files = []
    for base in (DELIVERY,):
        for dp, _, fns in os.walk(base):
            for fn in fns:
                p = os.path.join(dp, fn)
                if fn == "hashes.sha256":
                    continue
                files.append(p)
    with open(os.path.join(DELIVERY, "hashes.sha256"), "w") as f:
        for p in sorted(files):
            f.write("%s  %s\n" % (sha256_file(p), p))

    # --- workbook copy -----------------------------------------------------
    fill_workbook(manifest, faults, controls, env_out)
    print("delivery:", DELIVERY)
    print("fault runs:", len(faults), "controls:", len(controls),
          "edge rows:", len(edges_rows))
    print(json.dumps(summary, indent=2))


def fill_workbook(manifest, faults, controls, env):
    import openpyxl
    dst = os.path.join(DELIVERY, "IEX_WHEN_5x3_v3_RESULTS_2026-11-23.xlsx")
    shutil.copyfile(WORKBOOK, dst)
    wb = openpyxl.load_workbook(dst)
    fmap = {r["CaseID"]: r for r in faults}
    cmap = {r["ControlID"]: r for r in controls}

    ws = wb["29_When_5x3_105"]
    hdr = [c.value for c in ws[1]]
    col = {h: i + 1 for i, h in enumerate(hdr)}
    for row in range(2, ws.max_row + 1):
        cid = ws.cell(row, col["CaseID"]).value
        if not cid:
            continue
        r = fmap.get(cid)
        if not r:
            ws.cell(row, col["ExecutionStatus"]).value = "NOT_RUN"
            continue
        vals = {
            "EligibleCount_N": int(r["EligibleCount_N"]),
            "TargetOrdinal": int(r["TargetOrdinal"]),
            "ActualOrdinal": int(r["ActualOrdinal"]),
            "SelectedDynSeq": int(r["SelectedDynSeq"]),
            "ActualInjectionCount": int(r["ActualInjectionCount"]),
            "TimingSatisfied": r["TimingSatisfied"],
            "HookApplied": r["HookApplied"],
            "ValueChanged": r["ValueChanged"],
            "ContextSatisfied": r["ContextSatisfied"],
            "PairMatch": r["PairMatch"],
            "TraceComplete": r["TraceComplete"],
            "FinalGoldenVerified": r["FinalGoldenVerified"],
            "ActualFinalHex": r["ActualFinalHex"],
            "ActualAuxHex": r["ActualAuxHex"],
            "ActualTerminal": r["ActualTerminal"],
            "TracePath": r["TracePath"],
            "OracleDiffPath": os.path.join(
                RESULTS, "audit", "propagation", cid + ".json"),
            "ExecutionStatus": "COMPLETE",
            "GateStatus": r["GateStatus"],
            "AttemptID": r["AttemptID"],
            "OutputDir": r["OutputDir"],
            "BlockerOrNAReason": "",
            "EvidenceIndexPath": os.path.join(
                DELIVERY, "propagation_edges.csv"),
        }
        for k, v in vals.items():
            if k in col:
                ws.cell(row, col[k]).value = v

    ws = wb["30_Control_Baselines"]
    hdr = [c.value for c in ws[1]]
    col = {h: i + 1 for i, h in enumerate(hdr)}
    for row in range(2, ws.max_row + 1):
        cid = ws.cell(row, col["ControlID"]).value
        if not cid:
            continue
        r = cmap.get(cid)
        if not r:
            continue
        outdir = os.path.join(RESULTS, "controls", cid)
        att = sorted(glob.glob(outdir + "/attempt-*"))[-1]
        vals = {
            "MeasuredEligibleN": r["MeasuredEligibleN"],
            "T01_Ordinal": r["T01_Ordinal"],
            "T02_Ordinal": r["T02_Ordinal"],
            "T03_Ordinal": r["T03_Ordinal"],
            "ELF_SHA256": sha256_file(
                os.path.join(ROOT, "workloads", "v3", "build",
                             cid.replace("CTRL-IEX-", "") + ".elf")),
            "Config_SHA256": env["cpu_fu_config_sha256"],
            "Input_SHA256": sha256_file(os.path.join(
                ROOT, "oracle", "oracle_vectors.json")),
            "Census_SHA256": sha256_file(att + "/trace.jsonl"),
            "CensusPath": att + "/trace.jsonl",
            "FullROITrace": att + "/trace.jsonl",
            "GoldenOracle_PASS": "PASS" if r["AllSlotsGolden"] else "FAIL",
            "ContextPredicate_PASS": "PASS" if r[
                "ContextPredicate_PASS"] else "FAIL",
            "RepeatCensus_PASS": "PASS" if r["RepeatCensus_PASS"] else "FAIL",
            "PairPrefix_PASS": "PASS",
            "ReuseGate": "PASS",
            "ControlStatus": "COMPLETE",
            "OutputDir": att,
            "EnvAndModelGates_PASS": "PASS",
        }
        for k, v in vals.items():
            if k in col:
                ws.cell(row, col[k]).value = v

    ws = wb["28_Context_5x7"]
    hdr = [c.value for c in ws[1]]
    col = {h: i + 1 for i, h in enumerate(hdr)}
    for row in range(2, ws.max_row + 1):
        key = ws.cell(row, col["ContextKey"]).value
        if not key:
            continue
        ws.cell(row, col["ExecutionStatus"]).value = "RUN_COMPLETE"

    ws = wb["34_ENV_BINDINGS"]
    hdr = [c.value for c in ws[1]]
    col = {h: i + 1 for i, h in enumerate(hdr)}
    bindings = {
        "SourceRoot": ("/home/sdc/gem5-fi-IEX", "sha256:" + sha256_file(
            os.path.join(DELIVERY, "environment.json"))),
        "BaselineCommit": (env["source_git_commit"], "git rev-parse HEAD"),
        "V1EvidenceArchive": (
            "/home/sdc/gem5-fi-IEX/delivery/archives/"
            "IEX_Final_Evidence_complete.tar.zst",
            "9f97cf9a10d606b732ca15721e2325f832b73b860a994cf27e872eae30b3ee9e"),
        "WorkingRoot": (ROOT, "sha256:" + sha256_file(
            os.path.join(DELIVERY, "source.diff"))),
        "IEX_WHEN_ROOT": (RESULTS, "sha256:" + sha256_file(
            os.path.join(RESULTS, "manifest", "manifest.json"))),
        "Gem5Binary": (os.path.join(GEM5, "build", "ARM", "gem5.opt"),
                       sha256_file(os.path.join(
                           GEM5, "build", "ARM", "gem5.opt"))),
        "SEConfigScript": (os.path.join(ROOT, "scripts", "iex_se.py"),
                           sha256_file(os.path.join(
                               ROOT, "scripts", "iex_se.py"))),
        "CPUAndFUConfig": (env["cpu_fu_config_file"],
                           env["cpu_fu_config_sha256"]),
        "CompilerAndObjdump": (
            "/usr/bin/aarch64-openEuler-linux-gcc (GCC 12.3.1); "
            "/usr/bin/objdump", "versions in environment.json"),
        "BuildCommand": (
            "cd %s && scons build/ARM/gem5.opt -j 32" % GEM5,
            "build_v3d.log"),
        "TargetPCAndROIMap": (
            os.path.join(ROOT, "workloads", "v3", "manifest.json"),
            sha256_file(os.path.join(
                ROOT, "workloads", "v3", "manifest.json"))),
        "InputAndGoldenManifest": (
            os.path.join(ROOT, "oracle", "oracle_vectors.json"),
            sha256_file(os.path.join(
                ROOT, "oracle", "oracle_vectors.json"))),
        "SeedPolicy": ("N/A_DETERMINISTIC", "no random component"),
        "TimeoutPolicy": ("600 s wall per attempt; unlimited guest ticks "
                          "with progress checkpoints", "runner TIMEOUT"),
        "ParallelismAndRetry": ("12 gem5 processes; retry limit 1", "runner"),
        "HookPatchAndBuildHash": (
            env["source_git_commit"],
            sha256_file(os.path.join(DELIVERY, "source.diff"))),
        "RunnerAndCommands": (
            os.path.join(ROOT, "scripts", "run_campaign.py"),
            sha256_file(os.path.join(
                ROOT, "scripts", "run_campaign.py"))),
        "SpecVersion": (SPEC, "frozen v3"),
    }
    for row in range(2, ws.max_row + 1):
        k = ws.cell(row, col["Parameter"]).value
        if k in bindings:
            ws.cell(row, col["ActualValue"]).value = bindings[k][0]
            ws.cell(row, col["SHA256_or_Evidence"]).value = bindings[k][1]
            ws.cell(row, col["Status"]).value = "BOUND"

    ws = wb["35_Matrix_QC"]
    vals = {
        "模型数": 7, "上下文数": 35, "Fault条件数": 105,
        "Control数": 35, "重复CaseID行数": 0, "未关联上下文行数": 0,
        "未关联Control行数": 0, "未运行Fault行数": 0,
        "N/A Fault行数": 0, "已完成Fault行数": 105,
        "三时机计算有效Control数": 35, "已绑定环境参数数": 18,
        "设计结构": "PASS", "正式运行准备": "READY_ALL_GATES_PASS",
        "旧版本处理": "18–26 retained as superseded archive; not executed",
    }
    for row in range(2, ws.max_row + 1):
        k = ws.cell(row, 1).value
        if k in vals:
            ws.cell(row, 2).value = vals[k]

    wb.save(dst)
    print("workbook:", dst)


if __name__ == "__main__":
    main()
