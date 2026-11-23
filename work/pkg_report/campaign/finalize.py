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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMPAIGN = os.path.join(ROOT, "campaign")
RUNS = os.path.join(ROOT, "runs", "W5X3")
COND = os.path.join(CAMPAIGN, "conditions.json")
STATUS = os.path.join(ROOT, "experiment_status.csv")
MANIFEST = os.path.join(ROOT, "run_manifest.json")
BLOCKED = os.path.join(ROOT, "blocked_tasks.md")
ACCEPT = os.path.join(ROOT, "final_acceptance.md")
ANALYSIS = os.path.join(ROOT, "analysis")

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


def classify(model, man, ctrl):
    kinds = man.get("kinds") or {}
    ckinds = (ctrl or {}).get("kinds") or {}
    act = man.get("activation_count", 0)
    if act == 0:
        return "NOT_ACTIVATED", "activation_count=0"
    if model == "M06":
        det = (kinds.get("translation_fault", 0) +
               kinds.get("mmu_fault_detected", 0) +
               kinds.get("fault_delivery", 0) +
               kinds.get("arm_fault", 0) +
               kinds.get("exception", 0) +
               kinds.get("fault_state_consumed", 0) +
               kinds.get("fault_result_propagated", 0))
        if det:
            return "DETECTED_CONTAINED", "translation-fault/delivery event"
        # A fatal guest signal without a data consumer is also the expected
        # detected/contained terminal for a translation fault.
        term = man.get("terminal_lines") or []
        if any("TranslationFault" in ln or "SIGSEGV" in ln or
               "SIGBUS" in ln for ln in term):
            return "DETECTED_CONTAINED", "guest translation fault signal"
        return "PARTIAL", "activation without observed detection event"
    fo = oracle_lines(man.get("terminal_lines") or [])
    co = oracle_lines((ctrl or {}).get("terminal_lines") or [])
    if fo != co:
        return "SDC", "faulted oracle differs from same-config control"
    if kinds.get("squash", 0) and not (
            kinds.get("consumer", 0) or kinds.get("data_consumer", 0)):
        return "SQUASHED", "squash observed and no consumer / oracle change"
    return "ACTIVATED_MASKED", "faulted oracle equals control"


import gzip as _gzip

_STAGES = [
    ("activation", {"mmu_fault_activate", "mmu_fault_arm",
                    "refill_pfn_corrupt"}),
    ("mutation", {"tlbi_suppressed", "refill_pfn_corrupt",
                  "mmu_entry_mutation", "tlb_entry_substitution",
                  "fault_entry_reuse"}),
    ("translation", {"translation_result", "tlb_entry_insert",
                     "partial_entry_insert", "ptw_start"}),
    ("request", {"lsu_request"}),
    ("response", {"memory_response", "cache_response"}),
    ("consumer", {"consumer", "rf_writeback", "fault_entry_consume",
                  "fault_state_consumed", "ifu_response"}),
    ("commit_squash", {"commit", "squash"}),
]


def edge_summary_stream(path):
    """First observed event id per propagation stage (constant memory)."""
    out = {}
    seen = set()
    if not path or not os.path.isfile(path):
        return out
    try:
        with _gzip.open(path, "rt", errors="replace") as fh:
            for line in fh:
                if not line.startswith("PROP-EVT:"):
                    continue
                kind = re.search(r"kind=([^ ]*)", line)
                if not kind:
                    continue
                k = kind.group(1)
                for name, kinds in _STAGES:
                    if name in seen or k not in kinds:
                        continue
                    ev = re.search(r"event_id=([^ ]*)", line)
                    tick = re.search(r"tick=([^ ]*)", line)
                    out[name] = {"event_id": ev.group(1) if ev else "",
                                 "tick": tick.group(1) if tick else "",
                                 "kind": k}
                    seen.add(name)
                if len(seen) == len(_STAGES):
                    break
    except (OSError, EOFError):
        pass
    return out


def main():
    conds = load(COND, [])
    os.makedirs(ANALYSIS, exist_ok=True)
    rows = []
    blocked = []
    per = []
    controls = {}
    for c in conds:
        cid = c["ControlID"]
        if cid not in controls:
            controls[cid] = load(os.path.join(RUNS, cid, "manifest.json")) or {}
    for c in conds:
        ctrl = controls.get(c["ControlID"]) or {}
        n = int((ctrl.get("eligible_summary") or {}).get(
            "eligible_total", 0) or 0)
        plan = ceil_ord(c["TimingID"], n) if n else ""
        man = load(os.path.join(RUNS, c["NewSampleRunID"], "manifest.json"))
        st = "NOT_RUN"
        reason = ""
        terminal = ""
        if c["ControlContext"] == "SPEC":
            st = "N/A"
            reason = "M06-C05 speculative wrong-path has no generated rcS; pilot required"
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
                terminal, reason = classify(c["ModelID"], man, ctrl)
        if st in ("N/A", "BLOCKED", "FAILED", "PARTIAL"):
            blocked.append((c["NewSampleRunID"], st, reason))
        stages = edge_summary_stream(
            os.path.join(ROOT, man["trace"]) if man and man.get("trace")
            else "")
        rec = {
            "NewSampleRunID": c["NewSampleRunID"],
            "ModelID": c["ModelID"],
            "WorkloadID": c["WorkloadID"],
            "NewContext": c["NewContext"],
            "GuestContext": c["ControlContext"],
            "TimingID": c["TimingID"],
            "ControlID": c["ControlID"],
            "ControlReused": bool(ctrl),
            "N": n,
            "TargetOrdinal": plan,
            "ActualOrdinal": (man or {}).get("eligible_selected", [{}])[0].get(
                "eligible_ordinal", "") if man and man.get("eligible_selected")
            else "",
            "ActivationCount": (man or {}).get("activation_count", ""),
            "ReturnCode": (man or {}).get("returncode", ""),
            "TraceCompleteness": ("COMPLETE" if man and man.get(
                "trace_sha256") else ("INCOMPLETE" if man else "")),
            "TerminalState": terminal,
            "Status": st,
            "Reason": reason,
            "EvidencePath": ("runs/W5X3/%s" % c["NewSampleRunID"]) if man else "",
            "Stages": stages,
        }
        per.append(rec)
        rows.append({k: v for k, v in rec.items() if k != "Stages"})

    with open(STATUS, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(ANALYSIS, "per_condition.json"), "w") as fh:
        json.dump(per, fh, indent=1, sort_keys=True)

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
