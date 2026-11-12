#!/usr/bin/env python3
"""Build the M01/M02 propagation-chain report from a real trace + oracle.

Every check is derived from an actual PROP-EVT event (evidence_event_id) or
from the real guest stdout line (board.terminal). Nothing is assumed: a
missing evidence link is reported as a failed check, never as success.
"""

import argparse
import gzip
import json
import sys
from collections import defaultdict


def open_maybe_gz(path):
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic == b"\x1f\x8b":
        return gzip.open(path, "rt", errors="replace")
    return open(path, "r", errors="replace")


def load_trace(path):
    events = []
    with open_maybe_gz(path) as fh:
        for line in fh:
            if not line.startswith("PROP-EVT:"):
                continue
            d = {}
            for tok in line[len("PROP-EVT:"):].split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    d[k] = v
            try:
                d["event_id"] = int(d.get("event_id", ""))
                d["tick"] = int(d.get("tick", "0"))
            except ValueError:
                continue
            events.append(d)
    return events


def fnv1a64(byte):
    h = 14695981039346656037
    h ^= byte
    h = (h * 1099511628211) & ((1 << 64) - 1)
    return "%016x" % h


def parse_oracle(path):
    results = {}
    try:
        with open(path, "r", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("W9_RESULT") or line.startswith("W10_RESULT"):
                    parts = line.split()
                    d = {"_line": line}
                    for p in parts[1:]:
                        if "=" in p:
                            k, v = p.split("=", 1)
                            d[k] = v
                    key = d.get("ctx", "?")
                    results[key] = d
    except FileNotFoundError:
        pass
    return results


def to_int(ev, key, default=0, hexa=False):
    v = ev.get(key, "")
    if v == "":
        return default
    try:
        # Trace address fields are bare lowercase hex without 0x.
        return int(v, 16) if hexa else int(v, 0)
    except ValueError:
        try:
            return int(v, 16)
        except ValueError:
            return default


def find(events, **kw):
    out = []
    for e in events:
        if all(e.get(k, "") == v for k, v in kw.items()):
            out.append(e)
    return out


def one(events, **kw):
    r = find(events, **kw)
    return r[0] if r else None


def ev_summary(e):
    keys = ("kind", "event_id", "parent_event_id", "tick", "dyn_inst_seq",
            "translation_id", "unique_request_id", "walk_id", "lookup_id",
            "tlbi_id", "tlb_instance", "tlb_entry_id", "entry_generation",
            "entry_generation_after", "va", "pa", "pfn", "page_size_n",
            "asid", "vmid", "regime", "security_state", "fault_id",
            "fault_model", "old_pfn", "new_pfn", "old_pa", "new_pa",
            "pte_value_before", "pte_value_after", "data_fnv",
            "response_id", "commit_seq", "outcome", "suppress_count",
            "field")
    return {k: e.get(k, "") for k in keys if e.get(k, "") != ""}


def chain_events(events, ptag, tid):
    """Fault-tagged events + the translation chain + explicit ancestors."""
    by_id = {e["event_id"]: e for e in events}
    sel = {}
    for e in events:
        if e.get("fault_id") == str(ptag):
            sel[e["event_id"]] = e
        elif tid and e.get("translation_id") == str(tid):
            sel[e["event_id"]] = e
        elif str(ptag) != "0" and e.get("fault_id") == str(ptag):
            sel[e["event_id"]] = e
    if tid:
        seqs = {e.get("dyn_inst_seq") for e in list(sel.values())
                if e.get("dyn_inst_seq", "") not in ("", "0")}
        for e in events:
            if e.get("kind") in ("rf_writeback", "commit", "squash",
                                 "consumer") and \
                    e.get("dyn_inst_seq", "") in seqs:
                sel[e["event_id"]] = e
    # Explicit ancestors of every selected event.
    changed = True
    while changed:
        changed = False
        for eid in list(sel):
            p = sel[eid].get("parent_event_id", "")
            if p and int(p) in by_id and int(p) not in sel:
                sel[int(p)] = by_id[int(p)]
                changed = True
    return sorted(sel.values(), key=lambda e: (e["tick"], e["event_id"]))


def check(cond, evidence, detail=""):
    return {"pass": bool(cond),
            "evidence_event_id": evidence.get("event_id") if evidence else None,
            "detail": detail}


def classify_m01(checks, oracle_r01, fault_present, squashed):
    if not fault_present:
        if checks.get("target_entry_present", {}).get("pass"):
            return "INJECTION_NOT_ACTIVATED", "armed but no consumption evidence"
        return "NO_ELIGIBLE_EVENT", "no fault arm event"
    if squashed and not checks["commit"]["pass"]:
        return "SQUASHED", "fault-carrying instruction squashed"
    if checks["stale_consumed"]["pass"] and checks["old_pa_result"]["pass"] \
            and checks["old_data"]["pass"]:
        obs = oracle_r01.get("observed", "")
        if obs.lower() in ("0xaa", "aa"):
            return "SDC", "software observed the stale marker 0xAA"
        return "ARCH_STATE_CORRUPTION", \
            "stale translation propagated but oracle did not expose 0xAA"
    if fault_present and not checks["stale_consumed"]["pass"]:
        return "INJECTION_NOT_ACTIVATED", \
            "retained entry was never consumed by a translation"
    return "TRACE_INCOMPLETE", "terminal evidence link missing"


def classify_m02(checks, oracle_r01, fault_present, squashed):
    if not fault_present:
        return "NO_ELIGIBLE_EVENT", "no refill_pfn_corrupt activation"
    if squashed and not checks["commit"]["pass"]:
        return "SQUASHED", "fault-carrying load squashed"
    if checks["consumed"]["pass"] and checks["wrong_pa_result"]["pass"] \
            and checks["wrong_data"]["pass"]:
        obs = oracle_r01.get("observed", "")
        if obs.lower() in ("0x51", "51"):
            return "SDC", "software observed the neighbor sentinel 0x51"
        return "ARCH_STATE_CORRUPTION", \
            "corrupted PA propagated but oracle did not expose 0x51"
    if not checks["consumed"]["pass"]:
        return "INJECTION_NOT_ACTIVATED", \
            "corrupted entry was never consumed by a later lookup"
    return "TRACE_INCOMPLETE", "terminal evidence link missing"


def build_m01(events, oracle):
    arms = [e for e in events if e.get("kind") == "mmu_fault_arm"
            and e.get("fault_model") == "M01"]
    ptag = int(arms[0]["fault_id"]) if arms else 0
    arm = arms[0] if arms else None
    suppressed = [e for e in events if e.get("kind") == "tlbi_suppressed"
                  and e.get("fault_id") == str(ptag)]
    l2hits = [e for e in events if e.get("kind") == "tlb_lookup_hit"
              and e.get("tlb_instance") == "l2_shared"
              and e.get("fault_id") == str(ptag)]
    l2hit = l2hits[0] if l2hits else None
    tid = l2hit.get("translation_id") if l2hit else None
    evs = chain_events(events, ptag, tid) if ptag else []

    dtb_miss = next((e for e in evs if e.get("kind") == "tlb_lookup_miss"
                     and e.get("tlb_instance") == "dtb"), None)
    dtb_ins = next((e for e in evs if e.get("kind") == "tlb_entry_insert"
                    and e.get("tlb_instance") == "dtb"), None)
    res = next((e for e in evs if e.get("kind") == "translation_result"),
               None)
    lsu = next((e for e in evs if e.get("kind") == "lsu_request"), None)
    resp = next((e for e in evs if e.get("kind") == "memory_response"), None)
    wb = next((e for e in evs if e.get("kind") == "rf_writeback"), None)
    commit = next((e for e in evs if e.get("kind") == "commit"), None)
    squash = next((e for e in evs if e.get("kind") == "squash"), None)
    disarm = next((e for e in evs if e.get("kind") == "mmu_fault_disarm"),
                  None)

    retained_id = arm.get("retained_entry_id") if arm else None
    retained_gen = arm.get("retained_entry_generation") if arm else None
    stale_pfn = to_int(l2hit, "pfn", hexa=True) if l2hit else 0
    stale_pa = to_int(res, "pa", hexa=True) if res else 0
    # Generation must not move for the retained lifetime. Later contexts can
    # reuse the same slot, so the check is scoped to the maintenance window
    # (arm tick .. consumption tick), not the whole ROI.
    consume_tick = l2hit["tick"] if l2hit else 0
    invalidated_same = [e for e in events if e.get("kind") == "tlbi_invalidate"
                        and e.get("tlb_entry_id") == retained_id
                        and (not consume_tick or e["tick"] <= consume_tick)
                        and int(e.get("entry_generation", "-99")) >=
                        int(retained_gen or -1)]
    checks = {
        "target_entry_present": check(
            bool(arm) and retained_id not in (None, "", "0") and
            l2hit is not None and l2hit.get("tlb_entry_id") == retained_id,
            l2hit, "l2_shared hit carries the armed EntryID"),
        "invalidation_suppressed": check(
            bool(suppressed) and suppressed[0].get("outcome") == "suppressed",
            suppressed[0] if suppressed else None,
            "matching TLBI emitted tlbi_suppressed"),
        "identity_retained": check(
            bool(l2hit) and l2hit.get("entry_generation") == retained_gen,
            l2hit, "consuming lookup EntryGeneration equals arm generation"),
        "generation_unchanged": check(
            not invalidated_same, arm,
            "no tlbi_invalidate for the retained EntryID at/after arm gen"),
        "dtlb_normal_miss": check(dtb_miss is not None, dtb_miss,
                                  "post-maintenance DTLB lookup is a real miss"),
        "dtlb_refilled": check(dtb_ins is not None and
                               dtb_ins.get("pfn") == (l2hit or {}).get("pfn"),
                               dtb_ins, "DTLB refilled from the stale L2 entry"),
        "stale_consumed": check(bool(l2hit), l2hit,
                                "l2_shared hit on the retained entry"),
        "old_pa_result": check(
            stale_pa != 0 and to_int(res, "pfn", hexa=True) == stale_pfn,
            res, "translation_result PA comes from the stale PFN"),
        "old_pa_lsu": check(
            to_int(lsu, "pa", hexa=True) == stale_pa and stale_pa != 0, lsu,
            "LSU request carries the old PA"),
        "old_pa_response": check(
            to_int(resp, "pa", hexa=True) == stale_pa and stale_pa != 0, resp,
            "memory response returns on the old PA"),
        "old_data": check(
            (resp or {}).get("data_fnv") == fnv1a64(0xAA), resp,
            "response data is the old marker 0xAA (FNV-1a-64)"),
        "writeback": check(wb is not None, wb, "register writeback observed"),
        "commit": check(commit is not None, commit, "load committed"),
        "disarm": check(disarm is not None or
                        (arm and not l2hit), disarm,
                        "latch disarmed on first consumption"),
    }
    terminal, reason = classify_m01(checks, oracle, bool(arm),
                                    squash is not None)
    return {
        "model": "M01", "fault_id": ptag, "translation_id": tid,
        "arm_event": ev_summary(arm) if arm else None,
        "retained_entry_id": retained_id,
        "retained_entry_generation": retained_gen,
        "suppressed_tlbis": [ev_summary(e) for e in suppressed],
        "stale_pfn": hex(stale_pfn) if stale_pfn else None,
        "stale_pa": hex(stale_pa) if stale_pa else None,
        "checks": checks,
        "terminal_state": terminal, "terminal_reason": reason,
        "oracle": oracle,
        "chain": [ev_summary(e) for e in evs],
    }


def build_m02(events, oracle):
    acts = [e for e in events if e.get("kind") == "refill_pfn_corrupt"
            and e.get("fault_model") == "M02"]
    act = acts[0] if acts else None
    ptag = int(act["fault_id"]) if act else 0
    tid = act.get("translation_id") if act else None
    evs = chain_events(events, ptag, tid) if ptag else []

    inserts = [e for e in evs if e.get("kind") == "tlb_entry_insert"]
    hit = next((e for e in evs if e.get("kind") == "tlb_lookup_hit"
                and e.get("fault_id") == str(ptag)), None)
    res = next((e for e in evs if e.get("kind") == "translation_result"),
               None)
    lsu = next((e for e in evs if e.get("kind") == "lsu_request"), None)
    resp = next((e for e in evs if e.get("kind") == "memory_response"), None)
    wb = next((e for e in evs if e.get("kind") == "rf_writeback"), None)
    commit = next((e for e in evs if e.get("kind") == "commit"), None)
    squash = next((e for e in evs if e.get("kind") == "squash"), None)
    new_pfn = to_int(act, "new_pfn", hexa=True) if act else 0
    new_pa = to_int(act, "new_pa", hexa=True) if act else 0

    checks = {
        "ptw_started": check(
            any(e.get("kind") == "ptw_start" for e in evs), act,
            "real Stage-1 data walk observed"),
        "pte_unchanged": check(
            bool(act) and act.get("pte_value_before") ==
            act.get("pte_value_after") and
            act.get("pte_value_before") not in (None, "", "0"), act,
            "descriptor value before/after the hook is identical"),
        "pfn_corrupted": check(
            bool(act) and act.get("old_pfn") != act.get("new_pfn"), act,
            "refill payload PFN changed"),
        "entry_inserted": check(
            any(e.get("pfn") == act.get("new_pfn") for e in inserts)
            if act else False,
            next((e for e in inserts
                  if act and e.get("pfn") == act.get("new_pfn")), None),
            "corrupted PFN written into the TLB"),
        "consumed": check(hit is not None and
                          hit.get("pfn") == act.get("new_pfn"),
                          hit, "later lookup hits the corrupted entry"),
        "wrong_pa_result": check(
            to_int(res, "pa", hexa=True) == new_pa and new_pa != 0, res,
            "translation_result PA is the corrupted PA"),
        "wrong_pa_lsu": check(
            to_int(lsu, "pa", hexa=True) == new_pa and new_pa != 0, lsu,
            "LSU request carries the corrupted PA"),
        "wrong_pa_response": check(
            to_int(resp, "pa", hexa=True) == new_pa and new_pa != 0, resp,
            "response returns on the corrupted PA"),
        "wrong_data": check(
            (resp or {}).get("data_fnv") == fnv1a64(0x51), resp,
            "response data is the neighbor sentinel 0x51 (FNV-1a-64)"),
        "writeback": check(wb is not None, wb, "register writeback observed"),
        "commit": check(commit is not None, commit, "load committed"),
    }
    terminal, reason = classify_m02(checks, oracle, bool(act),
                                    squash is not None)
    return {
        "model": "M02", "fault_id": ptag, "translation_id": tid,
        "activation_event": ev_summary(act) if act else None,
        "old_pfn": act.get("old_pfn") if act else None,
        "new_pfn": act.get("new_pfn") if act else None,
        "old_pa": act.get("old_pa") if act else None,
        "new_pa": act.get("new_pa") if act else None,
        "entry_inserts": [ev_summary(e) for e in inserts],
        "checks": checks,
        "terminal_state": terminal, "terminal_reason": reason,
        "oracle": oracle,
        "chain": [ev_summary(e) for e in evs],
    }


def render_md(rep):
    lines = ["# %s Propagation Report" % rep["model"], ""]
    lines.append("- FaultID: `%s`" % rep["fault_id"])
    lines.append("- TranslationID: `%s`" % rep["translation_id"])
    if rep["model"] == "M01":
        lines.append("- Retained EntryID/Generation: `%s` / `%s`" %
                     (rep["retained_entry_id"],
                      rep["retained_entry_generation"]))
        lines.append("- Stale PFN/PA: `%s` / `%s`" %
                     (rep["stale_pfn"], rep["stale_pa"]))
        lines.append("- Suppressed TLBI ops: %d" %
                     len(rep["suppressed_tlbis"]))
    else:
        lines.append("- Refill PFN: `%s` -> `%s`" %
                     (rep["old_pfn"], rep["new_pfn"]))
        lines.append("- Refill PA: `%s` -> `%s`" %
                     (rep["old_pa"], rep["new_pa"]))
    lines.append("- TerminalState: **%s** (%s)" %
                 (rep["terminal_state"], rep["terminal_reason"]))
    lines.append("")
    lines.append("## Acceptance checks")
    lines.append("")
    lines.append("| Check | Result | Evidence event |")
    lines.append("|---|---|---|")
    for name, c in rep["checks"].items():
        lines.append("| %s | %s | %s |" %
                     (name, "PASS" if c["pass"] else "FAIL",
                      c["evidence_event_id"]))
    lines.append("")
    lines.append("## Oracle")
    lines.append("")
    o = rep.get("oracle") or {}
    lines.append("```")
    lines.append(o.get("_line", "n/a"))
    lines.append("```")
    lines.append("")
    lines.append("## Chain (%d events)" % len(rep["chain"]))
    lines.append("")
    lines.append("| tick | event_id | parent | kind | inst | tid | detail |")
    lines.append("|---|---|---|---|---|---|---|")
    for e in rep["chain"]:
        detail = []
        for k in ("tlb_instance", "tlb_entry_id", "entry_generation",
                  "va", "pa", "pfn", "page_size_n", "asid", "old_pfn",
                  "new_pfn", "data_fnv", "commit_seq", "suppress_count"):
            if e.get(k):
                detail.append("%s=%s" % (k, e[k]))
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" %
                     (e.get("tick", ""), e.get("event_id", ""),
                      e.get("parent_event_id", ""), e.get("kind", ""),
                      e.get("dyn_inst_seq", ""), e.get("translation_id", ""),
                      " ".join(detail)))
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=["M01", "M02"])
    ap.add_argument("--trace", required=True)
    ap.add_argument("--terminal", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    events = load_trace(args.trace)
    oracle = parse_oracle(args.terminal)
    r01 = oracle.get("R01", {})
    rep = build_m01(events, r01) if args.model == "M01" else \
        build_m02(events, r01)
    with open(args.out_json, "w") as fh:
        json.dump(rep, fh, indent=2, sort_keys=True)
    with open(args.out_md, "w") as fh:
        fh.write(render_md(rep))
    print(json.dumps({
        "model": rep["model"], "fault_id": rep["fault_id"],
        "terminal_state": rep["terminal_state"],
        "checks_passed": sum(1 for c in rep["checks"].values() if c["pass"]),
        "checks_total": len(rep["checks"]),
        "failed": [k for k, c in rep["checks"].items() if not c["pass"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
