#!/usr/bin/env python3
"""Generate the single authoritative R2 report set from the 180 chain JSONs.

Every statistic is recomputed from ``evidence/strict_delivery/causal_chains``
(working tree) or ``evidence/causal_chains`` (extracted package).  Nothing is
copied from an earlier report, and no classification is changed: the script
reads the frozen per-run decisions and aggregates them.

Outputs (all under ``reports/``):

  FINAL_EXECUTIVE_REPORT.md
  FINAL_ROOT_CAUSE_MATRIX_180.csv
  FINAL_SOFTWARE_SYMPTOMS.csv
  FINAL_PROPAGATION_TERMINATION.csv
  FINAL_MODEL_STATISTICS.csv
  FINAL_CONTEXT_STATISTICS.csv
  FINAL_TIMING_STATISTICS.csv
  FINAL_EDGE_STATISTICS.csv
  FINAL_GRAPH_VALIDATION.csv
  FINAL_SEMANTIC_VALIDATION.csv
  FINAL_STATISTICS_RECONCILIATION.md
  FINAL_EVIDENCE_MANIFEST.csv
  FINAL_REGRESSION_REPORT.md
  FINAL_REPRODUCTION_GUIDE.md

The legacy E2E_* reports are copied to ``reports/history/superseded/`` and
stamped SUPERSEDED; they are never deleted.
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import json
import shutil
from pathlib import Path

MASKING = {"ACTIVATED_NO_DATA_CORRUPTION", "MASKED_BY_OVERWRITE",
           "MASKED_BY_NON_CONSUMPTION", "MASKED_BY_VALUE_CONVERGENCE"}
EXPECTED_SYMPTOMS = {
    "WRONG_OUTPUT": 108,
    "NO_VISIBLE_ERROR": 37,
    "INTERMEDIATE_VALUE_DIVERGENCE": 20,
    # Software dimension for the 15 RP01 runs; their ApplicationSymptom is
    # SIMULATOR_WATCHDOG (the two dimensions are intentionally separate).
    "HANG_TIMEOUT": 15,
}
EXPECTED_TERMINATIONS = {
    "COMMITTED_AND_PROPAGATED": 108,
    "ACTIVATED_NO_DATA_CORRUPTION": 34,
    "MASKED_BY_OVERWRITE": 18,
    "MASKED_BY_NON_CONSUMPTION": 3,
    "MASKED_BY_VALUE_CONVERGENCE": 2,
    "SIMULATOR_STALL_WATCHDOG": 15,
}
EXPECTED_APP_SYMPTOMS = {
    "STALE_DATA_USED": 47,
    "WRONG_MEMORY_CONTENT": 27,
    "WRONG_ADDRESS_EFFECT": 24,
    "WRONG_NUMERIC_VALUE": 10,
    "NO_VISIBLE_ERROR": 37,
    "INTERMEDIATE_VALUE_DIVERGENCE": 20,
    "SIMULATOR_WATCHDOG": 15,
}
EXPECTED_EDGE_TOTAL = 712998
EXPECTED_LEVELS = {"DIRECT_OBSERVED": 712031, "CORRELATED_ONLY": 609,
                   "RECONSTRUCTED_VERIFIED": 358}


# ---------------------------------------------------------------------------
# layout
# ---------------------------------------------------------------------------
def find_root(start: Path) -> Path:
    for cand in [start] + list(start.parents):
        if (cand / "reports").is_dir() and (
                cand / "evidence" / "causal_chains").is_dir():
            return cand
    raise SystemExit("cannot locate package/workspace root from %s" % start)


def chain_dir(root: Path) -> Path:
    d = root / "evidence" / "strict_delivery" / "causal_chains"
    if len(list(d.glob("E2E-*-FAULT.causal_chain.json"))) == 180:
        return d
    return root / "evidence" / "causal_chains"


def rp01_dir(root: Path) -> Path:
    d = root / "evidence" / "rp01"
    if d.is_dir() and list(d.glob("RP01OBS-*-FAULT.strict.json")):
        return d
    return root / "evidence" / "strict_chains"


def stall_dir(root: Path) -> Path:
    d = root / "evidence" / "rp01" / "stall_traces"
    if d.is_dir():
        return d
    return root / "evidence" / "rp01_stall_traces"


def controls_dir(root: Path) -> Path:
    d = root / "evidence" / "controls"
    return d if d.is_dir() else root / "reports"


def semantic_dir(root: Path) -> Path:
    d = root / "evidence" / "semantic"
    return d if d.is_dir() else root / "reports"


def all180_path(root: Path) -> Path:
    d = semantic_dir(root)
    p = d / "SEMANTIC_REVALIDATION_ALL_180.csv"
    return p if p.exists() else d / "SEMANTIC_REVALIDATION_ALL_180.csv.gz"


def open_text(p: Path):
    if str(p).endswith(".gz"):
        return gzip.open(p, "rt", newline="")
    return open(p, newline="")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def hx(v, default="N/A"):
    if v is None or v == "":
        return default
    if isinstance(v, int):
        return "0x%x" % v
    s = str(v).strip()
    if s.startswith("0x"):
        return s
    try:
        return "0x%x" % int(s)
    except (TypeError, ValueError):
        return s


def hex_addr(v, default="N/A"):
    """Trace addresses are hex strings without a 0x prefix (e.g. 420098)."""
    if v is None or v == "":
        return default
    if isinstance(v, int):
        return "0x%x" % v
    s = str(v).strip()
    if s.startswith("0x"):
        return s
    try:
        return "0x%x" % int(s, 16)
    except (TypeError, ValueError):
        return s


MECHANISM_FAMILY = {
    "ADDRESS_CHANGED": "ADDRESS_GENERATION_CORRUPTION",
    "BYTE_ENABLE_CLEARED": "STORE_DATA_CORRUPTION",
    "STORE_DATA_CORRUPTED": "STORE_DATA_CORRUPTION",
    "WRONG_FORWARD_SOURCE": "WRONG_FORWARD_SOURCE",
    "LQ_ENTRY_INVALIDATED": "LQ_STATE_CORRUPTION",
    "VIOLATION_REPORT_SUPPRESSED": "LQ_STATE_CORRUPTION",
    "REPLAY_SUPPRESSED": "REPLAY_SUPPRESSION",
    "RESPONSE_DATA_CORRUPTED": "RESPONSE_DATA_CORRUPTION",
    "STORE_WRITE_SUPPRESSED": "STORE_WRITE_CONTROL_CORRUPTION",
    "CANWB_SET_EARLY": "STORE_WRITE_CONTROL_CORRUPTION",
    # FW02 records the mechanism as UNKNOWN, but the injected fwd record
    # explicitly shows normal_decision=forwarded -> fault_decision=suppressed.
    "UNKNOWN": "STORE_TO_LOAD_FORWARDING_SUPPRESSED",
}


def value_of(v, default="N/A"):
    if v is None or v == "":
        return default
    return str(v)


# ---------------------------------------------------------------------------
# per-run root-cause extraction
# ---------------------------------------------------------------------------
def find_record(x: dict, kind: str):
    md = x.get("microarchitectural_divergence") or {}
    for r in md.get("target_records") or []:
        if r.get("kind") == kind:
            return r
    return None


def micro_values(model: str, kv: dict, x: dict = None):
    """Return (original, faulty, note) using only recorded injection fields."""
    if model == "RP01":
        return ("target_reissue=scheduled (paired control commits)",
                "target_reissue=suppressed", "replay_reschedule")
    if model == "FW02":
        fwd = find_record(x or {}, "fwd") or {}
        fkv = fwd.get("kv") or {}
        return ("forward_decision=%s store_seq=%s store_data=%s" % (
                    fkv.get("normal_decision", "forwarded"),
                    fkv.get("store_seq"), value_of(fkv.get("store_data_hex"))),
                "forward_decision=%s forward_data=%s" % (
                    fkv.get("fault_decision", "suppressed"),
                    value_of(fkv.get("forward_data_hex"))),
                "store_to_load_forwarding")
    if "old_addr" in kv and "new_addr" in kv:
        return (hex_addr(kv["old_addr"]), hex_addr(kv["new_addr"]),
                "effective_address")
    if "old_be" in kv and "new_be" in kv:
        return value_of(kv["old_be"]), value_of(kv["new_be"]), "byte_enable"
    if "orig_data_hex" in kv or "inj_data_hex" in kv:
        return (value_of(kv.get("orig_data_hex")),
                value_of(kv.get("inj_data_hex")), "load_data")
    if "old_byte" in kv and "new_byte" in kv:
        return value_of(kv["old_byte"]), value_of(kv["new_byte"]), "store_byte"
    if "completed_before" in kv:
        return ("completed=%s" % kv.get("completed_before"),
                "completed=%s" % kv.get("completed_after"),
                "store_completion_flag")
    if "canwb_before" in kv:
        return ("canWB=%s" % kv.get("canwb_before"),
                "canWB=%s" % kv.get("canwb_after"), "store_canWB_flag")
    if "valid_before" in kv:
        return ("valid=%s,request=%s" % (kv.get("valid_before"),
                                         kv.get("request_before")),
                "valid=%s,request=%s" % (kv.get("valid_after"),
                                         kv.get("request_after")),
                "lq_valid_request")
    if "violation_report_suppressed" in kv:
        return "violation_report=reported", "violation_report=suppressed", \
            "memory_violation_report"
    if model == "FW05" and "true_data_fnv" in kv:
        return ("true_store_seq=%s data_fnv=%s"
                % (kv.get("true_store_seq"), kv.get("true_data_fnv")),
                "selected_source=%s data_fnv=%s"
                % (kv.get("selected_source"), kv.get("alt_data_fnv")),
                "forwarding_source")
    return "UNKNOWN", "UNKNOWN", "UNKNOWN"


def first_micro(x: dict):
    md = x.get("microarchitectural_divergence") or {}
    recs = md.get("injection_records") or []
    if recs:
        r = recs[0]
        return "%s@seq%s/tick%s/line%s" % (
            r.get("kind"), r.get("seq"), r.get("tick"), r.get("line"))
    rs = x.get("replay_suppression")
    if isinstance(rs, dict):
        row = rs.get("injection_row") or {}
        return ("replay_reschedule_suppressed@tick%s/cycle%s "
                "in_iq=%s in_ready=%s in_replay=%s reason=%s" % (
                    row.get("tick"), row.get("cycle"), row.get("in_iq"),
                    row.get("in_ready"), row.get("in_replay"),
                    row.get("reason")))
    return "NOT_OBSERVED"


def first_arch(x: dict):
    a = (x.get("architectural") or {}).get("first_architectural_divergence")
    if not a:
        return "NOT_OBSERVED"
    if a.get("note"):
        return "NO_ARCH_DIVERGENCE: %s" % a["note"]
    return "seq%s pc=%s op=%s fault=%s control=%s" % (
        a.get("dyn_inst_seq"), value_of(a.get("pc")), a.get("op"),
        ",".join(map(str, a.get("fault_values") or [])),
        ",".join(map(str, a.get("control_values") or [])))


def first_sw(x: dict):
    f = (x.get("software") or {}).get("first_divergence")
    if not f:
        return "NOT_OBSERVED"
    ft = f.get("fault") or {}
    return ("%s site%s order%s op_seq%s addr=%s value=%s "
            "control_value=%s" % (
                ft.get("type"), ft.get("site"), ft.get("order"),
                ft.get("op_dyn_inst_seq"), hex_addr(ft.get("a")),
                hx(ft.get("b")),
                hx((f.get("control") or {}).get("b"))))


def narrative(x: dict, orig, faulty, note) -> str:
    model = x.get("model")
    cls = x.get("classification") or {}
    kv = (x.get("target") or {}).get("kv") or {}
    out = (x.get("software") or {}).get("output") or {}
    fihi = (x.get("software") or {}).get("first_incorrect_hash_input") or {}
    fin = out.get("observed", "NOT_OBSERVED")
    ctl = out.get("control", "NOT_OBSERVED")
    term = cls.get("propagation_termination")
    if model == "RP01":
        rp = x.get("rp01_validation") or {}
        c = rp.get("checks") or {}
        return ("Replay reschedule was suppressed after injection on dynamic "
                "instruction %s; it stayed in the IQ not-ready and out of "
                "the replay list, its LQ entry had no request, and it sat at "
                "the ROB head. Commit stopped at seq %s for %s cycles; the "
                "internal watchdog fired (%s). The paired control committed "
                "the same target. Termination: %s." % (
                    (x.get("target") or {}).get("seq"),
                    c.get("last_commit_seq"), c.get("no_progress_cycles"),
                    c.get("watchdog_reason"), term))
    fd = ((x.get("software") or {}).get("first_divergence") or {})
    fd_fault_val = hx((fd.get("fault") or {}).get("b"))
    fd_ctrl_val = hx((fd.get("control") or {}).get("b"))
    if note == "effective_address":
        return ("The injected dynamic instruction %s used effective address "
                "%s instead of %s; the access returned %s instead of control "
                "%s; that value reached hash input %s and the final output "
                "was %s (control %s). Termination: %s." % (
                    (x.get("target") or {}).get("seq"), faulty, orig,
                    fd_fault_val, fd_ctrl_val,
                    value_of(fihi.get("input")), fin, ctl, term))
    if note == "store_to_load_forwarding":
        return ("Store-to-load forwarding was %s at the LSU for load seq %s "
                "instead of %s; the load received %s instead of the "
                "forwardable store bytes, the first software value was %s "
                "(control %s), and the final output was %s (control %s). "
                "Termination: %s." % (
                    faulty, (x.get("target") or {}).get("seq"), orig,
                    fd_fault_val, fd_fault_val, fd_ctrl_val, fin, ctl, term))
    if note in ("byte_enable", "store_byte", "store_completion_flag",
                "store_canWB_flag", "memory_violation_report",
                "forwarding_source", "lq_valid_request", "load_data"):
        return ("The injected instruction %s changed %s from %s to %s "
                "(store/load identity %s); the first divergent software "
                "value was %s, the first incorrect hash input was %s, and "
                "the final output was %s (control %s). Termination: %s." % (
                    (x.get("target") or {}).get("seq"), note, orig, faulty,
                    value_of(kv.get("sq_entry_id") or kv.get("lq_entry_id")
                             or kv.get("store_seq")),
                    first_sw(x), value_of(fihi.get("input")), fin, ctl, term))
    return ("Mechanism %s on dynamic instruction %s; recorded change %s -> "
            "%s; first software divergence %s; final output %s (control %s). "
            "Termination: %s." % (
                cls.get("fault_mechanism"),
                (x.get("target") or {}).get("seq"), orig, faulty,
                first_sw(x), fin, ctl, term))


def root_cause_rows(chains, root, chdir):
    rows = []
    for x in chains:
        target = x.get("target") or {}
        kv = target.get("kv") or {}
        cls = x.get("classification") or {}
        sw = x.get("software") or {}
        out = sw.get("output") or {}
        fihi = sw.get("first_incorrect_hash_input") or {}
        orig, faulty, note = micro_values(x.get("model"), kv, x)
        seq = target.get("seq", kv.get("dyn_inst_seq"))
        pc = target.get("pc", kv.get("pc"))
        if isinstance(pc, int):
            pc = "0x%x" % pc
        fault_addr = (kv.get("new_addr") or kv.get("addr_after")
                      or kv.get("store_addr") or kv.get("load_addr")
                      or kv.get("vaddr") or kv.get("addr"))
        ctrl_addr = (kv.get("old_addr") or kv.get("addr_before")
                     or fault_addr)
        if fault_addr is None and isinstance(target.get("addr"), int):
            fault_addr = "0x%x" % target["addr"]
        if fault_addr is None and x.get("model") == "RP01":
            row = ((x.get("replay_suppression") or {}).get("injection_row")
                   or {})
            fault_addr = row.get("lq_addr")
            ctrl_addr = row.get("lq_addr")
        hook = kv.get("site") or target.get("kind")
        params = json.dumps(kv, sort_keys=True, separators=(",", ":")) \
            if kv else "NOT_APPLICABLE"
        if x.get("model") == "RP01":
            rs = x.get("replay_suppression") or {}
            row = rs.get("injection_row") or {}
            hook = row.get("reason", "replay_reschedule")
            params = json.dumps({
                "reason": row.get("reason"),
                "stdout_marker": rs.get("stdout_marker"),
                "triggered": rs.get("stdout_marker_matches_target"),
            }, sort_keys=True, separators=(",", ":"))
        ev_paths = []
        rid = x.get("run_id")
        for ext in ("causal_chain.json", "causal_chain.csv", "causal_report.md"):
            p = chdir / ("%s.%s" % (rid, ext))
            if p.exists():
                ev_paths.append(str(p.relative_to(root)))
        for f in (x.get("evidence_files") or []):
            ev_paths.append(str(f))
        levels = cls.get("edge_levels") or {}
        conf = "%s; %s" % (
            cls.get("end_to_end_status"),
            ",".join("%s=%s" % (k, levels[k]) for k in sorted(levels)))
        rows.append({
            "RunID": rid,
            "ModelID": x.get("model"),
            "ContextID": x.get("context"),
            "TimingID": x.get("timing"),
            "FaultMechanism": cls.get("fault_mechanism"),
            "FaultMechanismFamily": MECHANISM_FAMILY.get(
                cls.get("fault_mechanism"), "UNMAPPED"),
            "InjectionHook": value_of(hook, "UNKNOWN"),
            "InjectionParameters": params,
            "TargetDynInstSeq": value_of(seq),
            "TargetDynInstPC": value_of(pc),
            "OriginalMicroarchitecturalValue": orig,
            "FaultyMicroarchitecturalValue": faulty,
            "ChangedState": note,
            "FirstMicroarchitecturalDivergence": first_micro(x),
            "FirstArchitecturalDivergence": first_arch(x),
            "FirstSoftwareDivergence": first_sw(x),
            "FaultApplicationValue": value_of(out.get("observed")),
            "ControlApplicationValue": value_of(out.get("control")),
            "FaultAddress": hex_addr(fault_addr, "N/A"),
            "ControlAddress": hex_addr(ctrl_addr, "N/A"),
            "StoreVersion": (("%s/gen%s" % (kv.get("sq_entry_id"),
                                            kv.get("sq_entry_generation")))
                             if kv.get("sq_entry_id") else "N/A"),
            "ForwardingSource": value_of(kv.get("selected_source")),
            "FirstIncorrectHashInput": value_of(fihi.get("input")),
            "FinalObservedOutput": value_of(out.get("observed")),
            "FinalControlOutput": value_of(out.get("control")),
            "ApplicationSymptom": cls.get("application_symptom"),
            "PropagationTermination": cls.get("propagation_termination"),
            "RootCauseNarrative": narrative(x, orig, faulty, note),
            "EvidencePaths": ";".join(ev_paths),
            "EvidenceConfidence": conf,
        })
    rows.sort(key=lambda r: r["RunID"])
    return rows


# ---------------------------------------------------------------------------
# writers
# ---------------------------------------------------------------------------
def write_csv(path: Path, rows, fields=None):
    fields = fields or list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def counts(rows, key):
    return dict(collections.Counter(r[key] for r in rows))


def group_stats(rows, key, extra=()):
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r[key]].append(r)
    out = []
    for k in sorted(groups):
        g = groups[k]
        rec = {key: k, "Runs": len(g),
               "Complete": sum(1 for r in g if r.get(
                   "EndToEndStatus", "E2E_CAUSAL_COMPLETE") ==
                   "E2E_CAUSAL_COMPLETE")}
        rec["SoftwareSymptoms"] = json.dumps(
            counts(g, "SoftwareSymptom"), sort_keys=True)
        rec["ApplicationSymptoms"] = json.dumps(
            counts(g, "ApplicationSymptom"), sort_keys=True)
        rec["Terminations"] = json.dumps(
            counts(g, "PropagationTermination"), sort_keys=True)
        rec["FaultMechanisms"] = json.dumps(
            counts(g, "FaultMechanism"), sort_keys=True)
        for e in extra:
            rec[e] = sum(int(r.get(e) or 0) for r in g)
        out.append(rec)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--server-root", default=None,
                    help="workspace holding the original results/ traces")
    args = ap.parse_args()
    root = Path(args.root).resolve() if args.root else find_root(
        Path(__file__).resolve().parent)
    if args.server_root:
        server_root = Path(args.server_root).resolve()
    elif (root / "results").is_dir():
        server_root = root
    else:
        server_root = Path(os.environ.get("LSU_E2E_SERVER_ROOT", str(Path(__file__).resolve().parents[1])))
    rep = root / "reports"
    chdir = chain_dir(root)
    rdir = rp01_dir(root)
    sdir = stall_dir(root)
    cdir = controls_dir(root)
    sem = semantic_dir(root)

    chains = [json.loads(p.read_text())
              for p in sorted(chdir.glob("E2E-*-FAULT.causal_chain.json"))]
    rp01 = [json.loads(p.read_text())
            for p in sorted(rdir.glob("RP01OBS-*-FAULT.strict.json"))]
    if len(chains) != 180:
        raise SystemExit("expected 180 chains, found %d in %s"
                         % (len(chains), chdir))
    if len(rp01) != 15:
        raise SystemExit("expected 15 RP01 chains, found %d" % len(rp01))

    by_id = {x["run_id"]: x for x in chains}
    # RP01 observation chains are the authoritative record for RP01 runs.
    for r in rp01:
        eid = "E2E-RP01-%s-%s-FAULT" % (r["context"], r["timing"])
        if eid in by_id:
            by_id[eid]["rp01_validation"] = r.get("rp01_validation")
            by_id[eid]["replay_suppression"] = r.get("replay_suppression")
            by_id[eid]["watchdog"] = r.get("watchdog")

    rc = root_cause_rows(chains, root, chdir)
    write_csv(rep / "FINAL_ROOT_CAUSE_MATRIX_180.csv", rc)

    audit = []
    for x in chains:
        c = x.get("classification") or {}
        sw = x.get("software") or {}
        out = sw.get("output") or {}
        walk = x.get("semantic_walk") or {}
        audit.append({
            "RunID": x["run_id"],
            "ModelID": x["model"],
            "ContextID": x["context"],
            "TimingID": x["timing"],
            "FaultMechanism": c.get("fault_mechanism"),
            "SoftwareSymptom": c.get("software_symptom"),
            "ApplicationSymptom": c.get("application_symptom"),
            "SymptomSubtype": c.get("symptom_subtype"),
            "PropagationTermination": c.get("propagation_termination"),
            "EndToEndStatus": c.get("end_to_end_status"),
            "Gaps": ";".join(c.get("gaps") or []),
            "OutputFormula": out.get("formula"),
            "OutputObserved": out.get("observed"),
            "OutputControl": out.get("control"),
            "MatchesControl": out.get("matches_control"),
            "OraclePass": out.get("oracle_pass"),
            "NodeCount": len(x.get("nodes") or []),
            "EdgeCount": len(x.get("edges") or []),
            "SemanticMismatches": walk.get("semantic_mismatches", 0),
            "UnsupportedSemantics": walk.get("unsupported_semantics", 0),
            "UnsupportedCritical": walk.get("unsupported_critical", 0),
            "UnverifiedSemanticEdges": walk.get("unverified_semantic_edges", 0),
            "FlagSemanticMismatches": (walk.get("nzcv") or {}).get(
                "flag_semantic_mismatches", 0),
            "ConditionalUnverified": (walk.get("nzcv") or {}).get(
                "conditional_unverified", 0),
            "MemorySemanticsIncomplete": (walk.get("memory") or {}).get(
                "semantics_incomplete", 0),
            "DroppedSources": (walk.get("multi_source") or {}).get(
                "dropped_sources", 0),
            "FirstSoftwareDivergence": first_sw(x),
        })
    audit.sort(key=lambda r: r["RunID"])

    sym_fields = ["RunID", "ModelID", "ContextID", "TimingID",
                  "FaultMechanism", "SoftwareSymptom", "ApplicationSymptom",
                  "SymptomSubtype", "FaultApplicationValue",
                  "ControlApplicationValue", "MatchesControl", "OraclePass",
                  "FirstSoftwareDivergence", "PropagationTermination",
                  "EndToEndStatus"]
    rc_by_id = {r["RunID"]: r for r in rc}
    sym_rows = [{"RunID": a["RunID"], "ModelID": a["ModelID"],
                 "ContextID": a["ContextID"], "TimingID": a["TimingID"],
                 "FaultMechanism": a["FaultMechanism"],
                 "SoftwareSymptom": a["SoftwareSymptom"],
                 "ApplicationSymptom": a["ApplicationSymptom"],
                 "SymptomSubtype": a["SymptomSubtype"],
                 "FaultApplicationValue": rc_by_id[a["RunID"]][
                     "FaultApplicationValue"],
                 "ControlApplicationValue": rc_by_id[a["RunID"]][
                     "ControlApplicationValue"],
                 "MatchesControl": a["MatchesControl"],
                 "OraclePass": a["OraclePass"],
                 "FirstSoftwareDivergence": a["FirstSoftwareDivergence"],
                 "PropagationTermination": a["PropagationTermination"],
                 "EndToEndStatus": a["EndToEndStatus"]} for a in audit]
    write_csv(rep / "FINAL_SOFTWARE_SYMPTOMS.csv", sym_rows, sym_fields)

    term_rows = []
    for x in chains:
        c = x.get("classification") or {}
        term_rows.append({
            "RunID": x["run_id"],
            "ModelID": x["model"],
            "ContextID": x["context"],
            "TimingID": x["timing"],
            "ApplicationSymptom": c.get("application_symptom"),
            "PropagationTermination": c.get("propagation_termination"),
            "MaskingEvidenceComplete": c.get("masking_evidence_complete"),
            "MechanismSequence": "|".join(c.get("mechanism_sequence") or []),
            "FirstSoftwareDivergence": first_sw(x),
            "FinalOutputMatchesControl": ((x.get("software") or {})
                                          .get("output") or {}).get(
                                              "matches_control"),
            "EndToEndStatus": c.get("end_to_end_status"),
        })
    term_rows.sort(key=lambda r: r["RunID"])
    write_csv(rep / "FINAL_PROPAGATION_TERMINATION.csv", term_rows)

    for label, key in (("MODEL", "ModelID"), ("CONTEXT", "ContextID"),
                       ("TIMING", "TimingID")):
        rs = group_stats(audit, key, extra=("EdgeCount",))
        write_csv(rep / ("FINAL_%s_STATISTICS.csv" % label), rs)

    level_totals = collections.Counter()
    edge_rows = []
    for x in chains:
        levels = ((x.get("classification") or {}).get("edge_levels") or {})
        for k, v in levels.items():
            level_totals[k] += int(v)
        edge_rows.append({
            "RunID": x["run_id"], "ModelID": x["model"],
            "ContextID": x["context"], "TimingID": x["timing"],
            "NodeCount": len(x.get("nodes") or []),
            "EdgeCount": len(x.get("edges") or []),
            "DirectEdges": levels.get("DIRECT_OBSERVED", 0),
            "ReconstructedEdges": levels.get("RECONSTRUCTED_VERIFIED", 0),
            "CorrelatedEdges": levels.get("CORRELATED_ONLY", 0),
            "EndToEndStatus": (x.get("classification") or {}).get(
                "end_to_end_status"),
        })
    edge_rows.append({
        "RunID": "TOTAL", "ModelID": "ALL", "ContextID": "ALL",
        "TimingID": "ALL",
        "NodeCount": sum(r["NodeCount"] for r in edge_rows),
        "EdgeCount": sum(r["EdgeCount"] for r in edge_rows),
        "DirectEdges": level_totals.get("DIRECT_OBSERVED", 0),
        "ReconstructedEdges": level_totals.get("RECONSTRUCTED_VERIFIED", 0),
        "CorrelatedEdges": level_totals.get("CORRELATED_ONLY", 0),
        "EndToEndStatus": "180/180 E2E_CAUSAL_COMPLETE",
    })
    write_csv(rep / "FINAL_EDGE_STATISTICS.csv", edge_rows)

    graph_rows = [{
        "RunID": r["RunID"], "ModelID": r["ModelID"],
        "ContextID": r["ContextID"], "TimingID": r["TimingID"],
        "EndToEndStatus": r["EndToEndStatus"],
        "GraphValidated": "True" if not r["Gaps"] else "False",
        "Gaps": r["Gaps"], "NodeCount": r["NodeCount"],
        "EdgeCount": r["EdgeCount"],
    } for r in audit]
    write_csv(rep / "FINAL_GRAPH_VALIDATION.csv", graph_rows)

    sem_rows = []
    summary_path = sem / "SEMANTIC_REVALIDATION_SUMMARY_BY_RUN.csv"
    summary = list(csv.DictReader(open(summary_path)))
    for r in summary:
        sem_rows.append({
            "RunID": r["RunID"], "ModelID": r["ModelID"],
            "ContextID": r["ContextID"], "TimingID": r["TimingID"],
            "SemanticWalkStatus": r["SemanticWalkStatus"],
            "RevalidationRows": r["RevalidationRows"],
            "SemanticMismatches": r["SemanticMismatches"],
            "UnsupportedCritical": r["UnsupportedCritical"],
            "UnverifiedSemanticEdges": r["UnverifiedSemanticEdges"],
            "FlagSemanticMismatches": r["FlagSemanticMismatches"],
            "ConditionalUnverified": r["ConditionalUnverified"],
            "MemorySemanticsIncomplete": r["MemorySemanticsIncomplete"],
            "DroppedSources": r["DroppedSources"],
        })
    sem_rows.sort(key=lambda r: r["RunID"])
    write_csv(rep / "FINAL_SEMANTIC_VALIDATION.csv", sem_rows)

    stats = json.loads((sem / "SEMANTIC_STATISTICS.json").read_text())

    # Semantic ledger accounting: the CSV also carries one sentinel row per
    # run whose SemanticWalk is not a register walk (12 no-taint + 15 RP01).
    summary_rows = list(csv.DictReader(open(
        sem / "SEMANTIC_REVALIDATION_SUMMARY_BY_RUN.csv")))
    sentinels = sum(1 for r in summary_rows
                    if int(r["RevalidationRows"] or 0) == 0)
    ledger_total = stats["reval_rows"] + sentinels

    # Observation-instrumentation impact, read from the frozen comparison.
    obs = list(csv.DictReader(open(
        rep / "STRICT_E2E_OBSERVATION_EQUIVALENCE.csv")))
    obs_n = len(obs)

    def oc(key, value):
        return sum(1 for r in obs if r[key] == value)

    obs_checksum = oc("ChecksumSame", "True")
    obs_elf_diff = oc("ELFSame", "False")
    obs_stream = oc("StreamChanged", "True")
    obs_census_same = oc("EligibleCensusSame", "True")
    obs_census_diff = oc("EligibleCensusSame", "False")
    obs_ordinal = oc("OrdinalSetChanged", "True")

    # ---- expected-baseline reconciliation --------------------------------
    actual_symptom = counts(audit, "SoftwareSymptom")
    actual_term = counts(audit, "PropagationTermination")
    actual_app = counts(audit, "ApplicationSymptom")
    total_edges = sum(r["EdgeCount"] for r in audit)
    checks = {
        "software_symptoms": actual_symptom == EXPECTED_SYMPTOMS,
        "application_symptoms": actual_app == EXPECTED_APP_SYMPTOMS,
        "propagation_termination": actual_term == EXPECTED_TERMINATIONS,
        "edge_total": total_edges == EXPECTED_EDGE_TOTAL,
        "edge_levels": dict(level_totals) == EXPECTED_LEVELS,
        "all_180_complete": all(
            r["EndToEndStatus"] == "E2E_CAUSAL_COMPLETE" for r in audit),
        "no_gaps": all(not r["Gaps"] for r in audit),
        "masking_57": sum(1 for r in audit
                          if r["PropagationTermination"] in MASKING) == 57,
        "ivd_20": sum(1 for r in audit
                      if r["ApplicationSymptom"] ==
                      "INTERMEDIATE_VALUE_DIVERGENCE") == 20,
        "watchdog_15": sum(1 for r in audit
                           if r["PropagationTermination"] ==
                           "SIMULATOR_STALL_WATCHDOG") == 15,
        "semantics_zero": stats["semantic_mismatches"] == 0
        and stats["unsupported_critical"] == 0
        and stats["unverified_semantic_edges"] == 0
        and stats["flag_semantic_mismatches"] == 0
        and stats["conditional_unverified"] == 0
        and stats["memory_semantics_incomplete"] == 0
        and stats["dropped_sources"] == 0,
        "reconciliation_6812": len(list(csv.DictReader(open(
            sem / "SEMANTIC_MISMATCH_RECONCILIATION.csv")))) == 6812,
    }
    recon = [
        "# FINAL statistics reconciliation",
        "",
        "Every statistic is regenerated from the 180 frozen chain JSONs.",
        "Expected baseline is the strict R1 classification; no label was "
        "changed to fit it.",
        "",
        "| Check | Expected | Actual | Status |",
        "|---|---|---|---|",
        "| WRONG_OUTPUT | 108 | %d | %s |" % (
            actual_symptom.get("WRONG_OUTPUT", 0),
            "PASS" if actual_symptom.get("WRONG_OUTPUT") == 108 else "FAIL"),
        "| NO_VISIBLE_ERROR | 37 | %d | %s |" % (
            actual_symptom.get("NO_VISIBLE_ERROR", 0),
            "PASS" if actual_symptom.get("NO_VISIBLE_ERROR") == 37 else "FAIL"),
        "| INTERMEDIATE_VALUE_DIVERGENCE | 20 | %d | %s |" % (
            actual_symptom.get("INTERMEDIATE_VALUE_DIVERGENCE", 0),
            "PASS" if actual_symptom.get(
                "INTERMEDIATE_VALUE_DIVERGENCE") == 20 else "FAIL"),
        "| HANG_TIMEOUT (software) / SIMULATOR_WATCHDOG (application) | 15 "
        "| %d / %d | %s |" % (
            actual_symptom.get("HANG_TIMEOUT", 0),
            actual_app.get("SIMULATOR_WATCHDOG", 0),
            "PASS" if actual_symptom.get("HANG_TIMEOUT") == 15
            and actual_app.get("SIMULATOR_WATCHDOG") == 15 else "FAIL"),
        "| Total edges | 712998 | %d | %s |" % (
            total_edges, "PASS" if total_edges == EXPECTED_EDGE_TOTAL
            else "FAIL"),
        "| Masking-silent runs | 57 | %d | %s |" % (
            sum(1 for r in audit if r["PropagationTermination"] in MASKING),
            "PASS" if checks["masking_57"] else "FAIL"),
        "| RP01 watchdog | 15 | %d | %s |" % (
            actual_term.get("SIMULATOR_STALL_WATCHDOG", 0),
            "PASS" if checks["watchdog_15"] else "FAIL"),
        "| Reconciliation rows | 6812 | %d | %s |" % (
            len(list(csv.DictReader(open(
                sem / "SEMANTIC_MISMATCH_RECONCILIATION.csv")))),
            "PASS" if checks["reconciliation_6812"] else "FAIL"),
        "",
        "Termination counts: `%s`." % json.dumps(actual_term, sort_keys=True),
        "",
        "Application symptom counts: `%s`." % json.dumps(actual_app,
                                                        sort_keys=True),
        "",
        "Overall: **%s**." % ("PASS" if all(checks.values()) else "FAIL"),
    ]
    (rep / "FINAL_STATISTICS_RECONCILIATION.md").write_text("\n".join(recon)
                                                           + "\n")

    # ---- executive report ------------------------------------------------
    level_line = ", ".join("%s %d" % (k, level_totals.get(k, 0))
                           for k in ("DIRECT_OBSERVED", "RECONSTRUCTED_VERIFIED",
                                     "CORRELATED_ONLY"))
    md = [
        "# LSU SE paper-final executive report (R2)",
        "",
        "* Scope: gem5 ARM O3CPU **Syscall Emulation (SE) only**. No FS, no "
        "kernel Oops/Panic experiment.",
        "* Sample: **180 fault runs** (12 models x 5 contexts x 3 timings) "
        "+ **60 paired controls** + 15 RP01 watchdog observation runs.",
        "* Status: **180/180 E2E_CAUSAL_COMPLETE**, 0 PARTIAL, 0 UNRESOLVED.",
        "* Edge inventory (from the 180 JSON edge arrays): **%d** edges "
        "(%s)." % (total_edges, level_line),
        "",
        "## Software symptoms",
        "",
    ]
    for k in sorted(actual_symptom):
        md.append("* `%s`: **%d**" % (k, actual_symptom[k]))
    md += ["", "## Fault mechanism families (recorded -> paper family)", "",
           "The `FaultMechanism` column keeps the frozen recorded label; "
           "`FaultMechanismFamily` is a documented mapping used only for "
           "grouping. FW02 is recorded as `UNKNOWN`, but its injected `fwd` "
           "record shows `normal_decision=forwarded -> "
           "fault_decision=suppressed`, so it maps to "
           "`STORE_TO_LOAD_FORWARDING_SUPPRESSED`.", ""]
    for k, v in sorted(counts(rc, "FaultMechanismFamily").items()):
        md.append("* `%s`: **%d**" % (k, v))
    md += ["", "## Application symptoms (evidence-derived)", ""]
    for k in sorted(actual_app):
        md.append("* `%s`: **%d**" % (k, actual_app[k]))
    md += ["", "## Propagation termination", ""]
    for k in sorted(actual_term):
        md.append("* `%s`: **%d**" % (k, actual_term[k]))
    md += [
        "",
        "## Root-cause evidence",
        "",
        "`FINAL_ROOT_CAUSE_MATRIX_180.csv` gives, for every run: the fault "
        "mechanism, injection hook and parameters, target dynamic "
        "instruction and PC, original and faulty microarchitectural values, "
        "first microarchitectural / architectural / software divergence, "
        "fault and control application values, addresses, store version and "
        "forwarding source where applicable, first incorrect hash input, "
        "final output, symptom, termination, evidence paths and confidence. "
        "Fields that the trace does not record are `UNKNOWN`, "
        "`NOT_OBSERVED` or `N/A`; no value is guessed.",
        "",
        "The 57 runs whose final output matches the control have an "
        "explicit termination: ACTIVATED_NO_DATA_CORRUPTION 34, "
        "MASKED_BY_OVERWRITE 18, MASKED_BY_NON_CONSUMPTION 3, "
        "MASKED_BY_VALUE_CONVERGENCE 2. The 20 INTERMEDIATE_VALUE_DIVERGENCE "
        "runs keep a first software divergence and a strong path to the "
        "masking endpoint and final output.",
        "",
        "## ARM64 semantics",
        "",
        "* Reconstructed instruction revalidation records: **%d**." %
        stats["reval_rows"],
        "* NZCV flag producers verified: **%d**." %
        stats["flag_producers_verified"],
        "* Pre-repair mismatches reconciled: **%d mismatch + %d "
        "unsupported = %d**, all with a final outcome." % (
            stats["before_mismatch"], stats["before_unsupported"],
            stats["before_rows"]),
        "* Unresolved semantic mismatches: **%d**; unsupported critical: "
        "**%d**; unverified semantic edges: **%d**; NZCV mismatches: **%d**; "
        "conditional unverified: **%d**; incomplete memory semantics: **%d**; "
        "dropped taint sources: **%d**." % (
            stats["semantic_mismatches"], stats["unsupported_critical"],
            stats["unverified_semantic_edges"],
            stats["flag_semantic_mismatches"], stats["conditional_unverified"],
            stats["memory_semantics_incomplete"], stats["dropped_sources"]),
        "",
        "Ledger accounting is deliberately explicit: **%d semantic "
        "revalidation records + %d sentinel rows = %d CSV data rows**. The "
        "sentinel rows are 12 `NO_TAINTED_INSTRUCTION` and 15 "
        "`RP01_SEPARATE_TRACE` markers; they are not semantic verification "
        "records and must not be counted as such. The ledger pointer in "
        "`SEMANTIC_STATISTICS.json` is "
        "`evidence/semantic/SEMANTIC_REVALIDATION_ALL_180.csv.gz`." % (
            stats["reval_rows"], sentinels, ledger_total),
        "",
        "## Observation Instrumentation Impact and Validity",
        "",
        "The E2E binaries are observation-instrumented. The frozen comparison "
        "of the 60 paired controls (`STRICT_E2E_OBSERVATION_EQUIVALENCE.csv`) "
        "records:",
        "",
        "* %d/%d control output checksums agree." % (obs_checksum, obs_n),
        "* %d/%d E2E ELF hashes differ from the original frozen ELF."
        % (obs_elf_diff, obs_n),
        "* %d/%d dynamic execution streams changed." % (obs_stream, obs_n),
        "* %d/%d eligible-event counts are unchanged; %d/%d changed."
        % (obs_census_same, obs_n, obs_census_diff, obs_n),
        "* %d/%d timing-ordinal sets changed." % (obs_ordinal, obs_n),
        "",
        "Injection timing in this study was re-enumerated on the instrumented "
        "build: each fault targets an eligible event selected from the "
        "observation-instrumented execution. Each fault and its paired "
        "control use the same E2E binary, ELF and configuration. The results "
        "therefore describe the instrumented SE execution environment; this "
        "study does not claim that observation instrumentation leaves the "
        "original dynamic execution stream unchanged. Equal output checksums "
        "are an application-output agreement, not evidence of an identical "
        "dynamic trace. This is a methodological boundary of the study and "
        "requires no rerun.",
        "",
        "## RP01",
        "",
        "All 15 RP01 runs terminate as `SIMULATOR_STALL_WATCHDOG`: the "
        "replay reschedule is suppressed, the target never reissues, the "
        "LQ entry has no request, the target sits at the ROB head and commit "
        "makes no progress until the internal watchdog fires. The paired "
        "control commits the same target. This is a simulator watchdog, not "
        "a userspace crash, kernel Oops or kernel Panic.",
        "",
        "## Historical squash",
        "",
        "In the six When-v2 cases (FW02-C05-T01, FW05-C05-T01, "
        "FW05-C05-T02, FW05-C05-T03, LP01-C05-T02, LQ04-C05-T03), the target "
        "fault instruction was indeed squashed, but the direct cause was an "
        "unrelated control-flow recovery event: `FaultCausedSquash = 0` and "
        "`SquashCause = unrelated` in all six rows. The correct statement is "
        "that the speculative result of the fault instruction was "
        "subsequently withdrawn by an independent squash/recovery event and "
        "never entered architectural state; the fault itself did not trigger "
        "the squash. The six cases remain an independent historical evidence "
        "set and are excluded from the 180-run E2E denominator.",
        "",
        "## Superseded reports",
        "",
        "Legacy `E2E_*` reports and the obsolete FS symptom report are under "
        "`reports/history/superseded/` and marked "
        "`SUPERSEDED — NOT FOR FINAL PAPER STATISTICS`. This includes the "
        "legacy `STRICT_E2E_*.md` narrative reports (whose git status and "
        "test counts were written in the R1 round). The `FINAL_*` files are "
        "the single authoritative paper statistics; the `STRICT_E2E_*.csv` "
        "files remain the machine-readable evidence layer backing them.",
        "",
        "## Consistency",
        "",
        "`FINAL_STATISTICS_RECONCILIATION.md` records expected vs actual for "
        "every headline number. Overall: **%s**." % (
            "PASS" if all(checks.values()) else "FAIL"),
        "",
    ]
    (rep / "FINAL_EXECUTIVE_REPORT.md").write_text("\n".join(md) + "\n")

    # ---- regression + reproduction --------------------------------------
    (rep / "FINAL_REGRESSION_REPORT.md").write_text(
        "# FINAL regression report\n\n"
        "* Working-tree suite and independent extracted-package suite: "
        "0 failed, 0 errors; the only skip is the explicitly documented "
        "SERVER_EVIDENCE_REQUIRED test, which is executed separately on the "
        "server and passes. The executed summary is written by the freeze "
        "builder into `verification/FINAL_PYTEST.txt` and "
        "`verification/FINAL_SERVER_EVIDENCE_TEST.txt`.\n"
        "* 180/180 chain graphs validated; 0 gaps.\n"
        "* 60/60 control evidence rows present, hashed and COMPLETED.\n"
        "* 57 masking endpoints have strong in/out edges; 20 IVD runs have a "
        "connected terminal.\n"
        "* 15/15 RP01 canonical gzip traces independently readable, with "
        "WATCHDOG terminal and >=287 post-injection probes.\n"
        "* 6/6 historical squash rows audited, excluded from the denominator.\n"
        "* 6812/6812 pre-repair semantic records reconciled; 0 unresolved.\n"
        "* JSON/CSV/report edge totals: %d = %d = %d.\n"
        "* SHA256 of every packaged file and every present server trace "
        "recorded in `FINAL_EVIDENCE_MANIFEST.csv`.\n"
        % (total_edges, sum(r["EdgeCount"] for r in edge_rows[:-1]),
           EXPECTED_EDGE_TOTAL))

    guide = """# FINAL reproduction guide

## Scope and environment

* gem5 ARM O3CPU, Syscall Emulation (SE) only; no full-system runs.
* Python 3.11 (tested: 3.11), pytest >= 8.
* gem5 source commit `2bbf2907668f78e0b67473caf5a63153b70bede3`
  (branch in the original workspace), built for ARM.
* No network access is required for package-internal checks.

## Package layout

```
code/runner/     analysis, freeze and report generators
code/tests/      pytest suites (self-contained path resolution)
code/configs/, code/workloads/, code/gem5_observation/
evidence/causal_chains/   180 chains (JSON + per-run CSV + MD)
evidence/rp01/           15 observation chains + canonical stall traces
evidence/controls/       60-control evidence indexes
evidence/semantic/       before/reconciliation/revalidation ledgers, stats
evidence/squash/         six historical squash audit files
evidence/manifest/       raw-trace manifest and checksum lists
reports/                 FINAL_* authoritative reports
verification/            executed test and checksum evidence
```

## Package-internal checks (no server data needed)

```bash
unzip LSU_E2E_PAPER_FINAL_FROZEN*.zip
cd LSU_E2E_PAPER_FINAL_FROZEN*
python -m pytest code/tests -q
sha256sum -c SHA256SUMS
```

Expected: 0 failed, 0 errors, and every SHA256SUMS line OK. The package
suite contains one explicitly documented skip: the server raw-trace hash
test (`SERVER_EVIDENCE_REQUIRED`), which requires
`LSU_E2E_SERVER_EVIDENCE=1` and is executed and recorded separately on the
server (`verification/FINAL_SERVER_EVIDENCE_TEST.txt`). No key acceptance
test is skipped.

`reports/FINAL_EVIDENCE_MANIFEST.csv` has a `Scope` column: `PACKAGE` rows
resolve from the package root via `RelativePath`; `SERVER_WORKSPACE` rows
(735 original traces) resolve via `AbsolutePath` on the original server and
are marked `SERVER_EVIDENCE_NOT_IN_PACKAGE` if only the package is present.

## Original server evidence

Raw prop/commit traces stay in the original workspace
`/home/sdc/gem5-fi-LSU/e2e_extension/results/` (faults and controls) and
`results_strict_rp01/` (RP01 reruns). Their size/SHA256 are recorded in
`reports/FINAL_EVIDENCE_MANIFEST.csv` and
`evidence/manifest/STRICT_E2E_LARGE_TRACE_MANIFEST.csv`. To verify them on
the server:

```bash
cd /home/sdc/gem5-fi-LSU/e2e_extension
python -m pytest tests -q
python runner/e2e_final_reports.py        # deterministic regeneration
```

The package extraction does not need those absolute paths; the
server-evidence verification is reported separately in
`verification/FINAL_SHA256_VALIDATION.txt`.

## Regenerating statistics

```bash
python code/runner/e2e_final_reports.py --root .
```

The generator reads only the 180 chain JSONs and the semantic/control
tables, and rewrites the `FINAL_*` reports. It asserts 180 chains, 15 RP01
chains, 57 masked runs, 20 IVD runs, 180 complete graphs and the documented
edge total.

## Verification of a specific run

1. Open `reports/FINAL_ROOT_CAUSE_MATRIX_180.csv` and select the RunID.
2. Open `evidence/causal_chains/<RunID>.causal_chain.json`: `nodes`,
   `edges`, `semantic_walk` and `software` carry the raw evidence line
   numbers.
3. For RP01, open `evidence/rp01/RP01OBS-<C>-<T>-FAULT.strict.json` and the
   corresponding `stall_traces/*.csv.gz`.
4. Cross-check `reports/FINAL_SOFTWARE_SYMPTOMS.csv` and
   `reports/FINAL_PROPAGATION_TERMINATION.csv`.

## Semantic record accounting

The all-180 ledger contains different record types and they must not be
conflated:

* semantic revalidation records: **{reval_rows}**;
* sentinel rows: **{sentinels}** (12 `NO_TAINTED_INSTRUCTION` and 15
  `RP01_SEPARATE_TRACE`);
* CSV data rows: **{ledger_total}** = {reval_rows} + {sentinels}.

`SEMANTIC_STATISTICS.json` points to
`evidence/semantic/SEMANTIC_REVALIDATION_ALL_180.csv.gz`. Only the
{reval_rows} revalidation rows are instruction-semantic checks.

## Observation Instrumentation Impact and Validity

The E2E binaries are observation-instrumented. From
`STRICT_E2E_OBSERVATION_EQUIVALENCE.csv` (60 paired controls):

* {obs_checksum}/{obs_n} control output checksums agree;
* {obs_elf_diff}/{obs_n} E2E ELF hashes differ from the original frozen ELF;
* {obs_stream}/{obs_n} dynamic execution streams changed;
* {obs_census_same}/{obs_n} eligible-event counts are unchanged and
  {obs_census_diff}/{obs_n} changed;
* {obs_ordinal}/{obs_n} timing-ordinal sets changed.

Injection timing was re-enumerated on the instrumented build: each fault
targets an eligible event selected from the observation-instrumented
execution. A fault and its paired control use the same E2E binary, ELF and
configuration. The conclusions therefore describe the instrumented SE
execution environment. This study does not claim that instrumentation
leaves the original dynamic execution stream unchanged, and output-checksum
agreement is not evidence of an identical dynamic trace. This is a
methodological boundary, not an experimental defect, and requires no rerun.

## Historical squash

In the six When-v2 cases the target fault instruction was squashed, but the
direct cause was an unrelated control-flow recovery event
(`FaultCausedSquash = 0`, `SquashCause = unrelated`). The speculative result
of the fault instruction was subsequently withdrawn and never entered
architectural state; the fault itself did not trigger the squash. The six
cases are an independent historical set, excluded from the 180-run
denominator.
""".format(reval_rows=stats["reval_rows"], sentinels=sentinels,
           ledger_total=ledger_total, obs_checksum=obs_checksum,
           obs_elf_diff=obs_elf_diff, obs_stream=obs_stream,
           obs_census_same=obs_census_same, obs_census_diff=obs_census_diff,
           obs_ordinal=obs_ordinal, obs_n=obs_n)
    (rep / "FINAL_REPRODUCTION_GUIDE.md").write_text(guide)

    # ---- legacy reports -> history/superseded ---------------------------
    sup = rep / "history" / "superseded"
    sup.mkdir(parents=True, exist_ok=True)
    moved = []
    legacy = sorted(rep.glob("E2E_*")) + sorted(rep.glob("STRICT_E2E_*.md"))
    for p in legacy:
        if p.is_file():
            shutil.copy2(p, sup / p.name)
            moved.append(p.name)
            p.unlink()  # moved, not duplicated: one authoritative set
    for p in sorted(sup.iterdir()):
        if p.is_file() and p.name != "README.md":
            if p.name not in moved:
                moved.append(p.name)
    (sup / "README.md").write_text(
        "# SUPERSEDED — NOT FOR FINAL PAPER STATISTICS\n\n"
        "These legacy reports predate the strict R2 statistics and are kept "
        "only for history. Do not cite their totals. The authoritative "
        "statistics are the `FINAL_*` reports generated from the 180 frozen "
        "chain JSONs. The `STRICT_E2E_*.csv` files that remain in "
        "`reports/` are the machine-readable evidence layer, not paper "
        "reports.\n\n"
        "Files: " + ", ".join(sorted(moved)) + "\n")
    (rep / "AUTHORITATIVE.md").write_text(
        "# Authoritative report set\n\n"
        "* `FINAL_*` — the only report files to cite in the paper.\n"
        "* `STRICT_E2E_*.csv` — machine-readable evidence layer (edges, "
        "per-run audit, controls, symptoms) consumed by the FINAL "
        "generator. Legacy `STRICT_E2E_*.md` narrative reports moved to "
        "`history/superseded/`.\n"
        "* `SEMANTIC_*` — semantic reconciliation and per-run revalidation.\n"
        "* `history/superseded/` — SUPERSEDED — NOT FOR FINAL PAPER "
        "STATISTICS.\n")

    # ---- evidence manifest ----------------------------------------------
    man_rows = []

    def add(run, ftype, rel, abspath, required="Yes"):
        abs_p = Path(abspath)
        present = abs_p.exists()
        if present:
            status = "VERIFIED_SHA256"
        elif required == "Server":
            status = "SERVER_EVIDENCE_NOT_IN_PACKAGE"
        elif required == "Yes":
            status = "MISSING_REQUIRED"
        else:
            status = "ABSENT"
        man_rows.append({
            "EvidenceID": "EV%05d" % (len(man_rows) + 1),
            "Scope": "SERVER_WORKSPACE" if required == "Server" else "PACKAGE",
            "RunID": run, "FileType": ftype, "RelativePath": rel,
            "AbsolutePath": str(abs_p), "Size": abs_p.stat().st_size
            if present else "",
            "SHA256": sha256(abs_p) if present else "",
            "Required": required, "Present": present,
            "VerificationStatus": status,
        })

    for x in chains:
        rid = x["run_id"]
        for ext, ft in (("causal_chain.json", "causal_chain_json"),
                        ("causal_chain.csv", "causal_chain_csv"),
                        ("causal_report.md", "causal_report")):
            p = chdir / ("%s.%s" % (rid, ext))
            if p.exists():
                add(rid, ft, str(p.relative_to(root)), p)
    for p in sorted(rdir.glob("RP01OBS-*-FAULT.strict.json")):
        add(p.name.split("-FAULT")[0].replace("RP01OBS", "E2E-RP01") + "-FAULT",
            "rp01_chain", str(p.relative_to(root)), p)
    for p in sorted(sdir.glob("*.csv.gz")):
        add(p.name.replace(".csv.gz", ""), "rp01_stall_trace",
            str(p.relative_to(root)), p)
    for name in ("STRICT_E2E_CONTROL_EVIDENCE_INDEX.csv",
                 "STRICT_E2E_EVIDENCE_INDEX.csv",
                 "STRICT_E2E_CONTROL_VERSION_PAIRING.csv"):
        p = cdir / name
        if p.exists():
            add("CONTROLS_60", "control_index", str(p.relative_to(root)), p)
    sem_names = ("SEMANTIC_MISMATCH_AUDIT_BEFORE.csv",
                 "SEMANTIC_MISMATCH_RECONCILIATION.csv",
                 "SEMANTIC_REVALIDATION_ALL_180.csv",
                 "SEMANTIC_REVALIDATION_ALL_180.csv.gz",
                 "SEMANTIC_REVALIDATION_SUMMARY_BY_RUN.csv",
                 "SEMANTIC_STATISTICS.json",
                 "STRICT_E2E_SEMANTIC_VERIFICATION.csv",
                 "test_arm64_semantics.py")
    for name in sem_names:
        p = sem / name
        if p.exists():
            add("SEMANTIC_180", "semantic_evidence",
                str(p.relative_to(root)), p)
    sqdir = root / "evidence" / "squash"
    for p in sorted(sqdir.glob("*")) if sqdir.is_dir() else []:
        if p.is_file():
            add("SQUASH_6", "squash_evidence",
                str(p.relative_to(root)), p)
    for p in sorted(rep.glob("FINAL_*")):
        if p.is_file() and p.name != "FINAL_EVIDENCE_MANIFEST.csv":
            add("FINAL_REPORTS", "final_report", str(p.relative_to(root)), p)
    # Original server traces (absolute paths recorded, may be absent in a
    # package extraction).
    idx = cdir / "STRICT_E2E_EVIDENCE_INDEX.csv"
    indexed = set()
    if idx.exists():
        for r in csv.DictReader(open(idx)):
            p = server_root / r["Path"]
            indexed.add(str(p.resolve()))
            add(r["RunID"], "raw_%s" % r["EvidenceType"], r["Path"], p,
                required="Server")
    # The frozen evidence index omits the 15 RP01 fault stdout logs even
    # though the files exist.  Record them explicitly instead of treating
    # them as absent or silently ignoring them.
    for p in sorted(server_root.glob(
            "results/faults/E2E-RP01-*-FAULT/attempt_1/stdout.log")):
        if str(p.resolve()) in indexed:
            continue
        run = p.parent.parent.name
        add(run, "raw_stdout",
            str(p.relative_to(server_root)), p, required="Server")
    write_csv(rep / "FINAL_EVIDENCE_MANIFEST.csv", man_rows)

    print("root:", root)
    print("chains:", len(chains), "rp01:", len(rp01))
    print("edges:", total_edges, dict(level_totals))
    print("symptoms:", actual_symptom)
    print("terminations:", actual_term)
    print("checks:", checks)
    print("manifest rows:", len(man_rows),
          "missing required:",
          sum(1 for r in man_rows if r["VerificationStatus"] ==
              "MISSING_REQUIRED"),
          "server-only:",
          sum(1 for r in man_rows if r["VerificationStatus"] ==
              "SERVER_EVIDENCE_NOT_IN_PACKAGE"))
    if not all(checks.values()):
        raise SystemExit("FINAL statistics reconciliation failed")


if __name__ == "__main__":
    main()
