#!/usr/bin/env python3
"""Collect the MMU formal campaign into the final dataset.

Reads only completed run directories under attempt_A01 plus the frozen
authority CSV.  Never launches gem5 and never rewrites run evidence.
Unobserved fields are marked NOT_EMITTED rather than invented.
"""
import csv
import gzip
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict

REPO = "/home/sdc/gem5-fi-mmu-impl-v2"
CAMP = os.path.join(REPO, "runs", "MMU_FORMAL_CAMPAIGN_20261113")
OUTROOT = os.path.join(CAMP, "attempt_A01")
AUTH_CSV = os.path.join(
    REPO, "phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2",
    "MMU_40_Sample_Matrix.csv")
ANALYSIS = os.path.join(CAMP, "analysis")
sys.path.insert(0, os.path.join(REPO, "tools"))

KV = re.compile(r"(\w+)=([^\s]*)")


def parse_trace(path):
    """Use the frozen v3 parser so numeric fields are typed, exactly as the
    validator does; fall back to raw key=value only if unavailable."""
    try:
        import mmu_trace_validate_v3 as v3
        events = []
        with v3.open_maybe_gz(path) as fh:
            for line in fh:
                ev = v3.parse_line(line)
                if ev is None:
                    continue
                try:
                    ev["event_id"] = int(ev.get("event_id", ""))
                except (TypeError, ValueError):
                    continue
                events.append(ev)
        events.sort(key=lambda e: e["event_id"])
        return events
    except Exception:
        events = []
        with gzip.open(path, "rt", errors="replace") as fh:
            for line in fh:
                if not line.startswith("PROP-EVT:"):
                    continue
                events.append(dict(KV.findall(line)))
        return events


def load_authority():
    with open(AUTH_CSV, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def f(ev, key, default=""):
    return ev.get(key, default) or ""


def chain_record(ev):
    """Spec field mapping; missing binary fields are explicit."""
    rec = OrderedDict()
    rec["EventID"] = f(ev, "event_id", "NOT_EMITTED")
    rec["ParentEventID"] = f(ev, "parent_event_id", "ROOT")
    rec["FaultID"] = f(ev, "fault_id", "0")
    rec["Kind"] = f(ev, "kind")
    rec["TranslationID"] = f(ev, "translation_id", "NOT_EMITTED")
    rec["LookupID"] = f(ev, "lookup_id", "NOT_EMITTED")
    rec["WalkID"] = f(ev, "walk_id", "NOT_EMITTED")
    rec["EntryID"] = f(ev, "entry_index", "NOT_EMITTED")
    rec["EntryGeneration"] = f(ev, "entry_generation", "NOT_EMITTED")
    rec["DynamicInstSeqNum"] = f(ev, "dyn_inst_seq", "NOT_EMITTED")
    rec["ExecutionAttemptID"] = f(ev, "execution_attempt_id", "NOT_EMITTED")
    rec["UniqueRequestID"] = f(ev, "unique_request_id",
                                f(ev, "request_id", "NOT_EMITTED"))
    rec["ResponseID"] = f(ev, "response_id", "NOT_EMITTED")
    rec["VA"] = f(ev, "va", "NOT_EMITTED")
    rec["PA"] = f(ev, "pa", "NOT_EMITTED")
    rec["CommitSeq"] = f(ev, "commit_seq", "NOT_EMITTED")
    rec["SquashStatus"] = "SQUASH" if f(ev, "kind") == "squash" else ""
    rec["TerminalState"] = ""
    rec["Tick"] = f(ev, "tick")
    rec["Field"] = f(ev, "field")
    rec["Before"] = f(ev, "before")
    rec["After"] = f(ev, "after")
    rec["StateBefore"] = f(ev, "state_before")
    rec["StateAfter"] = f(ev, "state_after")
    rec["Outcome"] = f(ev, "outcome")
    rec["Contained"] = f(ev, "contained")
    mapped = {"event_id", "parent_event_id", "fault_id", "kind",
              "translation_id", "lookup_id", "walk_id", "entry_index",
              "entry_generation", "dyn_inst_seq", "execution_attempt_id",
              "unique_request_id", "request_id", "response_id", "va", "pa",
              "commit_seq", "tick", "field", "before", "after",
              "state_before", "state_after", "outcome", "contained",
              "run_id", "sample_run_id"}
    rec["ExtraFields"] = {k: v for k, v in ev.items()
                          if v not in ("", None) and k not in mapped}
    return rec


def _eid(ev):
    v = ev.get("event_id")
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def build_chain(events, verdict):
    act = verdict.get("activation_event_id", "")
    cons = verdict.get("consumption_event_id", "")
    try:
        act = int(act)
    except (TypeError, ValueError):
        act = None
    try:
        cons = int(cons)
    except (TypeError, ValueError):
        cons = None
    by_id = {_eid(e): e for e in events}
    relevant_tids = set()
    for eid in (act, cons):
        e = by_id.get(eid)
        if e:
            t = f(e, "translation_id")
            if t not in ("", "0", 0):
                relevant_tids.add(str(t))
    fault_rows = [e for e in events
                  if f(e, "fault_id", "0") not in ("", "0", 0)]
    # Bounded causal window: activation -> first terminal after consumption.
    # Long-lived entry reuse is summarised by first/last-per-kind below rather
    # than emitting tens of thousands of identical rows.
    terminal_kinds = {"commit", "squash", "exception_delivery", "chain_end",
                      "arch_translation_fault", "translation_fault"}
    anchor = max(x for x in (act, cons) if x) if (act or cons) else -1
    end = None
    for e in events:
        if (_eid(e) or -1) > anchor and f(e, "kind") in terminal_kinds:
            end = _eid(e)
            break
    start = act if act is not None else (
        min((_eid(e) for e in fault_rows), default=-1))
    stop = end if end is not None else start
    keep = {_eid(e) for e in events
            if start <= (_eid(e) or -1) <= stop}
    by_kind = defaultdict(list)
    for e in fault_rows:
        by_kind[f(e, "kind")].append(_eid(e))
    for ids in by_kind.values():
        keep.add(ids[0])
        keep.add(ids[-1])
    keep.update(x for x in (act, cons) if x)
    for e in events:
        if f(e, "translation_id") in relevant_tids:
            keep.add(_eid(e))
    children = defaultdict(list)
    by_id_all = {_eid(e): e for e in events}
    for e in events:
        par = f(e, "parent_event_id")
        try:
            par = int(par)
        except (TypeError, ValueError):
            continue
        children[par].append(_eid(e))
    for x in (act, cons):
        keep.update(children.get(x, ()))
    for eid in list(keep):
        cur = eid
        seen = set()
        while cur in by_id_all and cur not in seen:
            seen.add(cur)
            par = f(by_id_all[cur], "parent_event_id")
            try:
                par = int(par)
            except (TypeError, ValueError):
                break
            if par == cur:
                break
            keep.add(par)
            cur = par
    rows = sorted((e for e in events if _eid(e) in keep),
                  key=lambda e: int(f(e, "event_id", "0") or 0))
    return rows, act, cons, relevant_tids


def control_zero_proof(manifest):
    path = (manifest.get("control_run") or "")
    ctl = os.path.dirname(os.path.dirname(path)) if path else ""
    proof = OrderedDict()
    proof["control_oracle_path"] = path
    proof["control_run_dir"] = ctl
    proof["exists"] = bool(ctl and os.path.isdir(ctl))
    if not ctl or not os.path.isdir(ctl):
        proof["status"] = "MISSING"
        return proof
    cmd_path = os.path.join(ctl, "Run_Log", "command.txt")
    cfg_path = os.path.join(ctl, "Config", "config.ini")
    exit_path = os.path.join(ctl, "Run_Log", "gem5_exit_code.txt")
    proof["command_sha256_path"] = cmd_path
    cmd = open(cmd_path, errors="replace").read() if os.path.exists(cmd_path) else ""
    proof["fault_flags_in_command"] = sorted(
        set(re.findall(r"--mmu_fault_model[^\s]*|--mmu_fault_enable[^\s]*",
                       cmd)))
    model = ""
    enable = ""
    if os.path.exists(cfg_path):
        insec = False
        for line in open(cfg_path, errors="replace"):
            s = line.strip()
            if s == "[board.chaos_propagation]":
                insec = True
                continue
            if insec and s.startswith("["):
                break
            if insec and s.startswith("mmuFaultModel="):
                model = s.split("=", 1)[1]
            if insec and s.startswith("mmuFaultEnable="):
                enable = s.split("=", 1)[1]
    proof["config_mmuFaultEnable"] = enable
    proof["config_mmuFaultModel"] = model
    proof["gem5_exit_code"] = (open(exit_path).read().strip()
                               if os.path.exists(exit_path) else "MISSING")
    proof["injection_applied_count"] = 0 if model == "" else "UNEXPECTED_NONZERO_MODEL"
    proof["basis"] = ("executed config has mmuFaultEnable=%s but an EMPTY "
                      "mmuFaultModel; CHAOSPropagation.cc arms only when "
                      "mmu_fault_enable && !mmu_fault_model.empty() (line 92)"
                      % enable)
    proof["status"] = ("ZERO_PROVEN"
                       if model == "" and proof["gem5_exit_code"] == "0"
                       else "CONTROL_INVALID")
    return proof


STRICT_CONTEXTS = {("M03", "R05"), ("M04", "R05"), ("M05", "R05"),
                   ("M07", "R04"), ("M07", "R05")}


def strict_chain(model, context, events, target_va, mode, oracle_line):
    if (model, context) not in STRICT_CONTEXTS:
        return None
    try:
        if isinstance(target_va, str):
            target_va = int(target_va, 0)
        import mmu_evidence_chain as ec
        return ec.evaluate(model, context, events, target_va, mode, oracle_line)
    except Exception as exc:  # reported, never hidden
        return {"error": repr(exc)}


def main():
    os.makedirs(ANALYSIS, exist_ok=True)
    rows = load_authority()
    samples = []
    missing = []
    for row in rows:
        sid = row["SampleRunID"]
        attempt = "A01"
        rdir = os.path.join(OUTROOT, sid)
        for att, root in (("A01", OUTROOT),
                          ("A02", os.path.join(CAMP, "attempt_A02"))):
            cand = os.path.join(root, sid)
            if (os.path.exists(os.path.join(cand, "sample_manifest.json")) and
                    os.path.exists(os.path.join(cand, "Validation",
                                                "verdict.json"))):
                attempt, rdir = att, cand
                break
        rec = OrderedDict()
        rec.update({
            "SampleRunID": sid, "ModelID": row["ModelID"],
            "ContextID": row["ContextID"], "WorkloadID": row["WorkloadID"],
            "CampaignID": "MMU-FORMAL-20261113",
            "AttemptID": attempt, "Role": "Fault",
            "TargetVA": row.get("TargetVAExact") or row.get("TargetVA", ""),
            "AccessMode": row.get("AccessMode", ""),
            "InjectionConfig": "curve-F0 deterministic",
            "Seed": row.get("Seed", ""), "SeedPolicy": row.get("SeedPolicy", ""),
        })
        man_p = os.path.join(rdir, "sample_manifest.json")
        ver_p = os.path.join(rdir, "Validation", "verdict.json")
        tr_p = os.path.join(rdir, "Trace", "prop_evt.txt.gz")
        rec["RunDir"] = rdir
        rec["RunStatus"] = "MISSING_OUTPUT"
        if not (os.path.exists(man_p) and os.path.exists(ver_p)):
            missing.append(sid)
            rec["FaultID"] = ""
            rec["ActivationStatus"] = "NOT_RUN"
            rec["PropagationStatus"] = "NOT_RUN"
            rec["TerminalState"] = "NOT_RUN"
            rec["TraceCompleteness"] = "NOT_RUN"
            rec["OracleResult"] = "NOT_RUN"
            rec["GoldenOutput"] = ""
            rec["FaultOutput"] = ""
            rec["ChainEventCount"] = 0
            rec["EventCount"] = 0
            rec["ControlZeroProof"] = {}
            rec["StrictChain"] = None
            samples.append(rec)
            continue
        man = json.load(open(man_p))
        ver = json.load(open(ver_p))
        events = parse_trace(tr_p) if os.path.exists(tr_p) else []
        chain_rows, act, cons, tids = build_chain(events, ver)
        obs_p = os.path.join(rdir, "Run_Log", "observed_output.txt")
        obs = open(obs_p, errors="replace").read() if os.path.exists(obs_p) else ""
        oracle_line = ver.get("OracleEvidence", {}).get("line", "")
        rec.update({
            "RunStatus": ("COMPLETED" if man.get("gem5_exit_code") == 0
                          else "FAILED"),
            "FaultID": ver.get("fault_id", ""),
            "ActivationStatus": ver.get("ActivationStatus", ""),
            "FaultConsumptionStatus": ver.get("FaultConsumptionStatus", ""),
            "PropagationStatus": ver.get("PropagationStatus", ""),
            "TraceCompleteness": ver.get("TraceCompleteness", ""),
            "TerminalState": ver.get("TerminalState", ""),
            "OracleResult": ver.get("OracleResult", ""),
            "RecordIntegrity": ver.get("RecordIntegrity", ""),
            "GoldenOutput": oracle_line,
            "FaultOutput": next((l for l in obs.splitlines()
                                 if ("ctx=%s" % row["ContextID"]) in l), ""),
            "BinarySHA256": man.get("gem5_sha256", ""),
            "ConfigSHA256": "",
            "WorkloadSHA256": man.get("workload_sha256", ""),
            "ControlOracle": man.get("control_oracle", {}),
            "ControlRun": man.get("control_run", ""),
            "StartedUTC": man.get("started_at_utc", ""),
            "FinishedUTC": man.get("finished_at_utc", ""),
            "Gem5ExitCode": man.get("gem5_exit_code"),
            "TimedOut": man.get("timed_out"),
            "ActivationEventID": act,
            "ConsumptionEventID": cons,
            "TranslationIDs": sorted(tids),
            "EventCount": len(events),
            "ChainEventCount": len(chain_rows),
            "MissingKinds": ver.get("Details", {}).get("missing_kinds", []),
            "WrongValueProof": ver.get("Details", {}).get("wrong_value_basis", []),
            "ControlZeroProof": control_zero_proof(man),
        })
        cfg = os.path.join(rdir, "Config", "config.ini")
        import hashlib
        rec["ConfigSHA256"] = (hashlib.sha256(open(cfg, "rb").read()).hexdigest()
                               if os.path.exists(cfg) else "")
        rec["StrictChain"] = (
            (ver.get("Details") or {}).get("strict_evidence_chain") or
            strict_chain(row["ModelID"], row["ContextID"], events,
                         rec["TargetVA"], row["AccessMode"], obs))
        # structured chain artifact
        cdir = os.path.join(ANALYSIS, "propagation_chains")
        os.makedirs(cdir, exist_ok=True)
        chain = OrderedDict()
        chain["SampleRunID"] = sid
        chain["ModelID"] = row["ModelID"]
        chain["ContextID"] = row["ContextID"]
        chain["FaultActivation"] = {
            "ActivationEventID": act,
            "ConsumptionEventID": cons,
            "TranslationIDs": sorted(tids),
            "ActivationStatus": rec["ActivationStatus"],
            "ConsumptionStatus": rec["FaultConsumptionStatus"],
        }
        chain["TerminalState"] = rec["TerminalState"]
        chain["Oracle"] = ver.get("OracleEvidence", {})
        chain["StrictChain"] = rec["StrictChain"]
        chain["DownstreamNotObservedByFrozenBinary"] = [
            "per-instruction IFU fetch response",
            "decode",
            "commit (as an IFU-specific event; generic commit is emitted)",
        ]
        chain["Events"] = [chain_record(e) for e in chain_rows]
        with open(os.path.join(cdir, sid + ".json"), "w") as fh:
            json.dump(chain, fh, indent=1)
        with open(os.path.join(cdir, sid + ".csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(chain_record(events[0]).keys())
                               if events else
                               ["EventID", "ParentEventID", "FaultID", "Kind"])
            w.writeheader()
            for e in chain_rows:
                w.writerow(chain_record(e))
        samples.append(rec)

    with open(os.path.join(ANALYSIS, "samples.json"), "w") as fh:
        json.dump(samples, fh, indent=1)
    cols = list(samples[0].keys()) if samples else []
    with open(os.path.join(ANALYSIS, "samples.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[c for c in cols
                                          if not isinstance(samples[0][c], dict)])
        w.writeheader()
        for r in samples:
            w.writerow({k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
                        for k, v in r.items() if k in w.fieldnames})

    agg = OrderedDict()
    agg["campaign_id"] = "MMU-FORMAL-20261113"
    agg["planned"] = len(rows)
    agg["completed"] = sum(1 for r in samples if r["RunStatus"] == "COMPLETED")
    agg["missing"] = missing
    agg["terminal"] = Counter(r["TerminalState"] for r in samples)
    agg["activation"] = Counter(r["ActivationStatus"] for r in samples)
    agg["propagation"] = Counter(r["PropagationStatus"] for r in samples)
    agg["trace"] = Counter(r["TraceCompleteness"] for r in samples)
    agg["oracle"] = Counter(r["OracleResult"] for r in samples)
    agg["per_model"] = {}
    for m in sorted({r["ModelID"] for r in samples}):
        sub = [r for r in samples if r["ModelID"] == m]
        agg["per_model"][m] = {
            "samples": len(sub),
            "activation": dict(Counter(r["ActivationStatus"] for r in sub)),
            "terminal": dict(Counter(r["TerminalState"] for r in sub)),
            "trace": dict(Counter(r["TraceCompleteness"] for r in sub)),
            "oracle": dict(Counter(r["OracleResult"] for r in sub)),
            "chain_events": {r["SampleRunID"]: r["ChainEventCount"]
                             for r in sub},
        }
    with open(os.path.join(ANALYSIS, "campaign_summary.json"), "w") as fh:
        json.dump(agg, fh, indent=1)
    print(json.dumps(agg, indent=1))


if __name__ == "__main__":
    main()
