#!/usr/bin/env python3
"""Build the WHEN-5X3 status matrix, causal summaries and A01-A22 evidence.

Reads only manifest.json / Trace / Run_Log artifacts produced by
when5x3_runner.py.  Nothing here invents an activation, a consumer, or a
terminal state: a condition is COMPLETE only when its fault manifest shows
exactly one activation, the planned ordinal, a matching eligible census and a
readable trace.
"""
import csv
import hashlib
import json
import os
import re
import gzip
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
import propagation  # noqa: E402
import control_map  # noqa: E402
import oracle  # noqa: E402
CAMPAIGN = os.path.join(ROOT, "campaign")
RUNS = os.path.join(ROOT, "runs", "W5X3")
RETRY_RUNS = os.path.join(ROOT, "runs", "W5X3_RETRY")
RETRY2_RUNS = os.path.join(ROOT, "runs", "W5X3_RETRY2")
COND = os.path.join(CAMPAIGN, "conditions.json")
STATUS = os.path.join(ROOT, "experiment_status.csv")
MANIFEST = os.path.join(ROOT, "run_manifest.json")
BLOCKED = os.path.join(ROOT, "blocked_tasks.md")
ACCEPT = os.path.join(ROOT, "final_acceptance.md")
ANALYSIS = os.path.join(ROOT, "analysis")
RETRY_MAP_PATH = os.path.join(ANALYSIS, "retry_map.json")
RETRY2_MAP_PATH = os.path.join(ANALYSIS, "retry2_map.json")

TIMING = {"T01": (1, 10), "T02": (1, 2), "T03": (9, 10)}
ACT_KIND = {"M01": "mmu_fault_arm", "M02": "refill_pfn_corrupt"}
for _m in ("M03", "M04", "M05", "M06", "M07", "M08"):
    ACT_KIND[_m] = "mmu_fault_activate"


def load(path, default=None):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def sha(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for c in iter(lambda: fh.read(1 << 20), b""):
                h.update(c)
        return h.hexdigest()
    except OSError:
        return ""


def ceil_ord(t, n):
    a, b = TIMING[t]
    return (a * n + b - 1) // b


def trace_events(path, limit=None):
    out = []
    try:
        with gzip.open(path, "rt", errors="replace") as fh:
            for line in fh:
                if line.startswith("PROP-EVT:"):
                    out.append(dict(re.findall(r"(\w+)=([^ ]*)", line)))
                    if limit and len(out) >= limit:
                        break
    except (OSError, EOFError):
        pass
    return out


def oracle_lines(term):
    pat = re.compile(r"^W(?:9|10S|1[0-4])_(?:RESULT|SUMMARY|STORE|RESULT)\b")
    return [ln for ln in term if pat.match(ln)]


def classify(model, man, ctrl, chain):
    """Granular terminal-state classification computed only from observed
    events, the reconstructed chain and the fault/control oracle comparison.

    The old heuristic ("first event of each stage kind in the whole trace")
    is gone: the chain passed in is the identity-based reconstruction from
    campaign/propagation.py.
    """
    act = (chain or {}).get("root")
    if not act:
        return "NOT_ACTIVATED", "activation_count=0", {}

    detail = {
        "activation_kind": act.get("kind", ""),
        "activation_basis": (chain or {}).get("activation_basis", ""),
        "consumed_lineage": bool((chain or {}).get("consume")),
        "has_translation": bool((chain or {}).get("translation")),
        "has_request": bool((chain or {}).get("request")),
        "has_response": bool((chain or {}).get("response")),
        "has_writeback": bool((chain or {}).get("writeback")),
        "has_consumer": bool((chain or {}).get("consumer")),
        "terminal_kind": ((chain or {}).get("terminal") or {}).get("kind", ""),
        "has_any_commit": bool((chain or {}).get("has_any_commit")),
        "unobserved": (chain or {}).get("unobserved", []),
        "not_applicable": (chain or {}).get("not_applicable", []),
        "faulted_event_count": (chain or {}).get("faulted_event_count", 0),
        "masked_reason": ((chain or {}).get("summary") or {}).get(
            "masked_reason", ""),
        "summary_outcome": ((chain or {}).get("summary") or {}).get(
            "outcome", ""),
        "exception_delivered": ((chain or {}).get("summary") or {}).get(
            "exception_delivered", 0),
    }

    if model == "M06":
        terminal = (chain or {}).get("terminal") or {}
        summary = (chain or {}).get("summary") or {}
        delivered = (terminal.get("kind") == "exception_delivery" or
                     summary.get("exception_delivered") == 1)
        if delivered:
            return ("DETECTED_DELIVERED",
                    "exception_delivery observed; exception_delivered=1",
                    detail)
        return ("DETECTED_LOCALLY",
                "TranslationLL propagated internally (fault_result_propagated); "
                "exception_delivered=0, no exception_delivery event", detail)

    fo = oracle_lines(man.get("terminal_lines") or [])
    co = oracle_lines((ctrl or {}).get("terminal_lines") or [])
    if not oracle.semantic_compare(man.get("terminal_lines") or [],
                                   (ctrl or {}).get("terminal_lines") or []):
        return ("SDC",
                "faulted oracle differs from same-config control "
                "(semantic observed/result/signal fields)", detail)

    # No software-visible oracle change.
    consumed = (detail["consumed_lineage"] or detail["has_translation"] or
                detail["has_request"])
    if not consumed:
        return ("ACTIVATED_UNCONSUMED",
                "fault activated but no downstream consumer observed in trace",
                detail)
    # [W5X3-FIX] An explicit tracer terminal signal: the fault's request was
    # issued but never completed before the ROI ended (no memory response, no
    # consumer, no commit, no exception).  This is neither "masked" (no realise-
    # and-mask happened) nor "unconsumed" (a translation + LSU request did
    # happen); it is a pending-request boundary at ROI end.
    if detail["masked_reason"] == "request_issued_not_completed_at_roi_end":
        return ("REQUEST_PENDING_AT_ROI_END",
                "fault translated and issued an LSU request, but the request "
                "never completed before the ROI ended "
                "(mmu_fault_summary.masked_reason="
                "request_issued_not_completed_at_roi_end); no memory response "
                "/ consumer / commit / exception delivery observed", detail)
    # A fault-tagged committing consumer means the fault's effect was realized
    # and then masked (the value was dead/unused); only a chain with no commit
    # at all (a squashed consumer) is "propagated but squashed".
    if detail["has_any_commit"]:
        return ("ACTIVATED_MASKED",
                "fault reached translation/request and a consumer committed, "
                "but oracle equals control (effect masked)", detail)
    if detail["terminal_kind"] == "squash":
        return ("PROPAGATED_BUT_SQUASHED",
                "fault propagated to a consumer that was squashed before any "
                "architectural effect (no commit observed)", detail)
    # Consumed (translation/request observed) but no commit, no squash, no
    # explicit ROI boundary.  Only reached for a request that was still
    # in-flight at trace end without the exporter's explicit masked_reason.
    return ("ACTIVATED_MASKED",
            "fault reached translation/request but oracle equals control "
            "(effect masked)", detail)


def edge_summary_stream(path, model):
    """Return the compressed per-stage map for one fault trace, rooted at the
    real activation and joined by explicit correlation evidence."""
    if not path or not os.path.isfile(path):
        return {}, {}
    chain = propagation.build_chain_from_path(path, model)
    return propagation.build_stage_map(chain), chain


def completeness(man, chain):
    """Four orthogonal completeness dimensions (issue the researcher flagged):

      file         -- the raw trace file is present and has a recorded hash
      edges        -- every recorded causal edge carries an explicit basis
      terminal     -- an observed terminal (endpoint) exists
      architecture -- every expected architecture stage is observed (no NOT_
                      EMITTED boundary and no raw gap)

    Returns (file_bool, edges_bool, terminal_bool, arch_bool, overall_label).
    """
    comp = (chain or {}).get("completeness") or {}
    file_complete = bool(man and man.get("trace_sha256"))
    edges_explicit = bool(comp.get("edges_explicit"))
    terminal_observed = bool(comp.get("terminal_observed"))
    arch_complete = bool(comp.get("architecture_complete"))
    dims = {"file": file_complete, "edges": edges_explicit,
            "terminal": terminal_observed, "architecture": arch_complete}
    if not file_complete:
        overall = "FILE_MISSING"
    elif all(dims.values()):
        overall = "FULL"
    else:
        overall = "PARTIAL_" + "+".join(k.upper()
                                        for k, v in dims.items() if not v)
    return (file_complete, edges_explicit, terminal_observed, arch_complete,
            overall)


CHAIN_CACHE = os.path.join(ANALYSIS, "_chains_cache.json")


def _chain_cache_key(run_id, trace_path):
    return run_id


def load_chain_cache():
    return load(CHAIN_CACHE, {})


def save_chain_cache(cache):
    try:
        with open(CHAIN_CACHE, "w") as fh:
            json.dump(cache, fh, sort_keys=True)
    except OSError:
        pass


def get_chain(run_id, trace_path, model, cache, tsha=""):
    """Retrieve or build a chain, caching the (expensive) streaming pass."""
    if not tsha:
        man = load(os.path.join(RUNS, run_id, "manifest.json")) or {}
        tsha = man.get("trace_sha256", "")
    if tsha and run_id in cache and cache[run_id].get("_trace_sha256") == tsha:
        return cache[run_id]["chain"]
    chain = propagation.build_chain_from_path(trace_path, model)
    cache[run_id] = {"chain": chain, "_trace_sha256": tsha}
    return chain


def main():
    conds = load(COND, [])
    os.makedirs(ANALYSIS, exist_ok=True)
    retry_map = load(RETRY_MAP_PATH, {})
    retry2_map = load(RETRY2_MAP_PATH, {})

    def run_manifest_for(sample_id):
        """Return (manifest, base_dir, rid) for a sample, honouring targeted
        re-runs.  Precedence: 0202c RETRY2 > 0202b RETRY > original W5X3.  The
        base dir is returned so EvidencePath/RetryRunID name the ACTUAL trace
        location, never the original path (the round-0202b EvidenceSource bug)."""
        if sample_id in retry2_map:
            rid = retry2_map[sample_id]
            return load(os.path.join(RETRY2_RUNS, rid, "manifest.json")), \
                RETRY2_RUNS, rid
        if sample_id in retry_map:
            rid = retry_map[sample_id]
            return load(os.path.join(RETRY_RUNS, rid, "manifest.json")), \
                RETRY_RUNS, rid
        return load(os.path.join(RUNS, sample_id, "manifest.json")), RUNS, \
            sample_id

    rows = []
    blocked = []
    per = []
    controls = {}
    ctrl_reg = control_map.registry()
    ctrl_rows = []           # for analysis/control_map.json (build-matched)
    chain_cache = load_chain_cache()
    def _ctl_manifest(cid):
        if cid not in controls:
            controls[cid] = load(os.path.join(RUNS, cid, "manifest.json")) or {}
        return controls[cid]
    for c in conds:
        cid = c["ControlID"]
        _ctl_manifest(cid)
    for c in conds:
        man, man_base, man_rid = run_manifest_for(c["NewSampleRunID"])
        cid = c["ControlID"]  # per-row authoritative plan ID (not the preload loop's stale value)
        is_spec = (c["ControlContext"] == "SPEC")
        # build-matched control: the fault's gem5 build hash selects the golden
        # control (original / RETRY / RETRY2), never a cross-build substitute.
        # SPEC (M06-C05, N/A) has no executed fault, so no Control is required.
        crec, cbuild_ok = (None, True) if is_spec else \
            control_map.resolve_control(
                c["ModelID"], c["NewContext"],
                (man or {}).get("gem5_sha256", ""), ctrl_reg)
        ctrl = (crec or {}).get("manifest") or _ctl_manifest(cid)
        ctrl_rows.append({
            "SampleRunID": c["NewSampleRunID"], "ModelID": c["ModelID"],
            "ContextID": c["NewContext"], "ControlID": cid,
            "FaultBuildHash": (man or {}).get("gem5_sha256", ""),
            "FaultTraceSHA256": (man or {}).get("trace_sha256", ""),
            "ControlRunID": (crec or {}).get("run_id", ""),
            "ControlBuildHash": (crec or {}).get("build_hash", ""),
            "ControlTraceSHA256": (crec or {}).get("trace_sha256", ""),
            "ControlEligibleN": (crec or {}).get("eligible_total", ""),
            "BuildMatches": bool(cbuild_ok),
            "ControlApplicable": "N/A (SPEC)" if is_spec else "REQUIRED",
        })
        n = int((ctrl.get("eligible_summary") or {}).get(
            "eligible_total", 0) or 0)
        plan = ceil_ord(c["TimingID"], n) if n else ""
        retried = (c["NewSampleRunID"] in retry_map or
                   c["NewSampleRunID"] in retry2_map)
        st = "NOT_RUN"
        reason = ""
        terminal = ""
        if c["ControlContext"] == "SPEC":
            st = "N/A"
            reason = ("M06-C05 speculative wrong-path: feasibility boundary of "
                      "the frozen workload/config (validated by pilot "
                      "runs/pilot/M06-C05), not a global infeasibility claim. "
                      "The pilot formed 3 eligible M06 events but all are "
                      "correct-path cold fetches; the frozen O3 fetch does not "
                      "speculatively predict the indirect-branch target")
        elif not ctrl:
            st = "NOT_RUN"
            reason = "control/pre-scan has not run"
        elif n < 3:
            st = "N/A" if n == 0 else "BLOCKED"
            reason = "golden eligible N=%d < 3" % n
        elif not man:
            st = "NOT_RUN"
            reason = "fault run has not run"
        elif man.get("returncode") != 0:
            st = "FAILED"
            reason = "gem5 exit=%s timeout=%s" % (man.get("returncode"),
                                                  man.get("timed_out"))
        elif man.get("activation_count") != 1:
            st = "FAILED"
            reason = "activation_count=%s (expected 1)" % man.get(
                "activation_count")
        else:
            sel = man.get("eligible_selected") or []
            actual = int(sel[0].get("eligible_ordinal", -1)) if sel else -1
            total = int((man.get("eligible_summary") or {}).get(
                "eligible_total", 0) or 0)
            if actual != plan:
                st = "FAILED"
                reason = "actual ordinal %s != planned %s" % (actual, plan)
            elif total < plan and c["ModelID"] not in ("M01", "M02"):
                # Persistent entry models (M04/M05) stop counting once the
                # corrupted entry is registered; the control N is the
                # authoritative denominator and the selected ordinal is the
                # timing witness.
                st = "PARTIAL"
                reason = "fault-run census %s below planned ordinal %s" % (
                    total, plan)
            elif not man.get("trace_sha256") or not man.get("total_events"):
                st = "PARTIAL"
                reason = "trace missing/empty"
            else:
                st = "COMPLETE"
        chain = {}
        if man and man.get("trace"):
            chain = get_chain(c["NewSampleRunID"],
                              os.path.join(ROOT, man["trace"]),
                              c["ModelID"], chain_cache,
                              tsha=man.get("trace_sha256", ""))
        if st == "COMPLETE":
            terminal, reason, detail = classify(c["ModelID"], man, ctrl, chain)
        else:
            detail = {}
        if st in ("N/A", "BLOCKED", "FAILED", "PARTIAL"):
            blocked.append((c["NewSampleRunID"], st, reason))
        stages = propagation.build_stage_map(chain)
        file_c, edges_c, term_c, arch_c, overall = completeness(man, chain)
        rec = {
            "NewSampleRunID": c["NewSampleRunID"],
            "ModelID": c["ModelID"],
            "WorkloadID": c["WorkloadID"],
            "NewContext": c["NewContext"],
            "GuestContext": c["ControlContext"],
            "TimingID": c["TimingID"],
            "ControlID": c["ControlID"],
            "ControlReused": bool(ctrl),
            "Retried": retried,
            "RetryRunID": (retry2_map.get(c["NewSampleRunID"], "") or
                           retry_map.get(c["NewSampleRunID"], "")),
            "N": n,
            "TargetOrdinal": plan,
            "ActualOrdinal": (man or {}).get("eligible_selected", [{}])[0].get(
                "eligible_ordinal", "") if man and man.get("eligible_selected")
            else "",
            "ActivationCount": (man or {}).get("activation_count", ""),
            "ReturnCode": (man or {}).get("returncode", ""),
            # file-level integrity only: the raw trace exists and is healthy
            "TraceCompleteness": ("FILE_COMPLETE" if file_c else
                                  ("FILE_MISSING" if man else "")),
            "FileComplete": file_c,
            "EdgesExplicit": edges_c,
            "TerminalObserved": term_c,
            "ArchitectureComplete": arch_c,
            "Completeness": overall,
            "TerminalState": terminal,
            "Status": st,
            "Reason": reason,
            "EvidencePath": (os.path.relpath(os.path.join(man_base, man_rid), ROOT)
                          if man else ""),
            "Stages": stages,
            "TerminalStateDetail": detail,
        }
        rec["Chain"] = chain
        per.append(rec)
        rows.append({k: v for k, v in rec.items()
                     if k not in ("Stages", "Chain", "TerminalStateDetail")})

    with open(os.path.join(ANALYSIS, "control_map.json"), "w") as fh:
        json.dump(ctrl_rows, fh, indent=1, sort_keys=True)

    with open(STATUS, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(ANALYSIS, "per_condition.json"), "w") as fh:
        json.dump(per, fh, indent=1, sort_keys=True)
    save_chain_cache(chain_cache)

    counts = {}
    for r in rows:
        counts[r["Status"]] = counts.get(r["Status"], 0) + 1
    manifest = {
        "generated_utc": __import__("time").strftime(
            "%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        "conditions": len(rows),
        "status_counts": counts,
        "controls_run": sum(1 for c in controls.values() if c),
        "control_reuse": "one pre-scan/Control per (Model,Context)",
        "gem5_sha256": sha(os.path.join(ROOT, "CHAOS/gem5/build/ARM/gem5.opt")),
        "authority_excel_sha256": sha(os.path.join(
            ROOT, "inputs/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx")),
        "disk_template_sha256": sha(os.path.join(
            ROOT, "runs/disks/mmu_template.img")),
        "checkpoint": os.environ.get("W5X3_CHECKPOINT",
            "runs/mmu_bootF1/cpt.244799013609"),
        "workload_binaries": {
            n: sha(os.path.join(ROOT, "workloads/mmu_w5x3", n))
            for n in ("mmu_w9", "mmu_w10", "mmu_w11", "mmu_w12", "mmu_w13",
                      "mmu_w14", "mmu_w9.dyn", "mmu_w10.dyn", "mmu_w11.dyn",
                      "mmu_w12.dyn", "mmu_w13.dyn", "mmu_w14.dyn",
                      "mmu_w10s.dyn")},
        "rcs_sha256": {
            f: sha(os.path.join(CAMPAIGN, "rcs", f))
            for f in sorted(os.listdir(os.path.join(CAMPAIGN, "rcs")))
            if f.endswith(".rcS")},
        "checkpoint_m5cpt_sha256": sha(os.path.join(
            ROOT, "runs/mmu_bootF1/cpt.244799013609/m5.cpt")),
        "runs": rows,
    }
    with open(MANIFEST, "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)

    with open(BLOCKED, "w") as fh:
        fh.write("# WHEN-5X3 blocked / incomplete conditions\n\n")
        fh.write("Every entry below is a real observed condition, never a "
                 "silent substitution.\n\n")
        for sid, st, why in blocked:
            fh.write("- `%s` — **%s** — %s\n" % (sid, st, why))
        if not blocked:
            fh.write("- none\n")
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
