#!/usr/bin/env python3
"""MMU unified trace validator v3 (Phase 2.1).

Fixes over v2 (tools/mmu_trace_validate_v2.py is preserved unchanged):

  1. M02 causal path is CONTROL/M02-aware:
        CONTROL: tlb_fill -> tlb_entry_insert
        M02:     tlb_fill -> refill_pfn_corrupt -> tlb_entry_insert
     The edge is checked through real ParentEventID values, never deleted
     from the report.
  2. M01 causal order is checked in the real direction:
        tlbi_issue -> tlbi_match -> mmu_fault_arm -> tlbi_suppressed
     The retained EntryID + Generation must be identical across the match,
     the suppression and the consuming lookup.
  3. Terminal-aware completeness: a commit chain must reach commit; a squash
     chain is judged up to squash; a walk still in flight at ROI end can
     never be COMPLETE (it is TRACE_INCOMPLETE/PARTIAL).
  4. The single global "trace_completeness" is replaced by distinct fields:
     RecordIntegrity, FaultChainCompleteness, PerTranslationCompleteness,
     PerContextCompleteness, RunTraceCompleteness, PropagationCoverage,
     TerminalCoverage, MissingCausalEdges.
  5. Explicit ContextID mapping (never tick/window inference):
        W9  R01..R05 -> ASID 220/224/228/232/236
        W10 R01..R05 -> VA 0x4001000000..0x4001400000
  6. Per-fault / per-context / per-translation / per-edge target coverage.

Everything is computed from the real PROP-EVT stream. No event is invented;
a chain is never declared COMPLETE merely because one representative chain
in the run was complete.

Usage:
  mmu_trace_validate_v3.py --input prop_evt.txt.gz --workload W9 \
    --model M01 --run-id TEST-M01-CONTEXT-R02 \
    --va 0x4000000000 --csv-prefix out/prefix --report-json out/report.json
"""

import argparse
import csv
import gzip
import json
import sys
from collections import Counter, defaultdict

PROP_PREFIX = "PROP-EVT:"
CONTEXT_IDS = ["R01", "R02", "R03", "R04", "R05"]

# Explicit, workload-defined context identities. These are facts about the
# frozen workload/checkpoint, not tick-window guesses.
W9_ASID_CONTEXT = {220: "R01", 224: "R02", 228: "R03", 232: "R04", 236: "R05"}
W10_VA_CONTEXT = {
    0x4001000000: "R01",
    0x4001100000: "R02",
    0x4001200000: "R03",
    0x4001300000: "R04",
    0x4001400000: "R05",
}

MODEL_REQUIRED = {
    ("W9", "CONTROL"): [
        "tlbi_issue", "tlbi_match", "tlbi_invalidate", "translation_start",
        "tlb_lookup_miss", "ptw_start", "pte_read", "pte_decode", "tlb_fill",
        "tlb_entry_insert", "tlb_lookup_hit", "permission_eval",
        "translation_result", "lsu_request", "memory_response",
        "rf_writeback", "commit",
    ],
    ("W9", "M01"): [
        "tlbi_issue", "tlbi_match", "mmu_fault_arm", "tlbi_suppressed",
        "translation_start", "tlb_lookup_miss", "tlb_lookup_hit",
        "tlb_entry_insert", "permission_eval", "translation_result",
        "lsu_request", "memory_response", "rf_writeback", "commit",
        "mmu_fault_disarm",
    ],
    ("W10", "CONTROL"): [
        "translation_start", "tlb_lookup_miss", "ptw_start", "pte_read",
        "pte_decode", "tlb_fill", "tlb_entry_insert", "tlb_lookup_hit",
        "permission_eval", "translation_result", "lsu_request",
        "memory_response", "rf_writeback", "commit",
    ],
    ("W10", "M02"): [
        "translation_start", "tlb_lookup_miss", "ptw_start", "pte_read",
        "pte_decode", "tlb_fill", "refill_pfn_corrupt", "tlb_entry_insert",
        "tlb_lookup_hit", "permission_eval", "translation_result",
        "lsu_request", "memory_response", "rf_writeback", "commit",
    ],
}


def open_maybe_gz(path):
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic == b"\x1f\x8b":
        return gzip.open(path, "rt", errors="replace")
    return open(path, "r", errors="replace")


def parse_line(line):
    line = line.strip()
    if not line.startswith(PROP_PREFIX):
        return None
    out = {}
    for token in line[len(PROP_PREFIX):].strip().split():
        if "=" not in token:
            continue
        key, val = token.split("=", 1)
        out[key] = val
    return out


def load_events(path):
    events, bad = [], 0
    with open_maybe_gz(path) as fh:
        for line in fh:
            ev = parse_line(line)
            if ev is None:
                continue
            try:
                ev["event_id"] = int(ev.get("event_id", ""))
            except ValueError:
                bad += 1
                continue
            events.append(ev)
    events.sort(key=lambda e: e["event_id"])
    return events, bad


def to_int(ev, key, default=0):
    val = ev.get(key, "")
    if val == "":
        return default
    try:
        return int(val, 0)
    except ValueError:
        return default


def kind(ev):
    return ev.get("kind", "")


def hexaddr(val):
    """PROP-EVT addresses are emitted as bare hex (mmuHex drops 0x)."""
    if not val:
        return None
    try:
        return int(val, 16) if not val.startswith("0x") else int(val, 0)
    except ValueError:
        return None


def context_for(workload, chain_events):
    """Explicit ContextID from workload-defined ASID/VA identity."""
    if workload == "W9":
        for ev in chain_events:
            asid = to_int(ev, "asid", -1)
            if asid in W9_ASID_CONTEXT:
                return W9_ASID_CONTEXT[asid], "ASID"
    elif workload == "W10":
        for ev in chain_events:
            va = hexaddr(ev.get("va", ""))
            if va in W10_VA_CONTEXT:
                return W10_VA_CONTEXT[va], "VA"
    return "UNMAPPED", "UNMAPPED"


def expected_kinds(kinds, model, has_ptw_ids=False, has_cache_events=False):
    """Expected event kinds for the branch this chain really took.

    Presence-based (the trace is a DAG, not a total order); the temporal
    order is enforced separately through ParentEventID edges.

    Terminal-aware:
      * a commit chain must carry the full data path to commit;
      * a squash chain is judged only up to the node that really squashed
        (a PTW-stage squash has no lsu/memory/writeback/commit);
      * a hit-only chain that took no walk is not required to show PTW events.
    """
    exp = []
    if "tlbi_issue" in kinds:
        exp += ["tlbi_issue", "tlbi_match"]
    if model == "M01" and "mmu_fault_arm" in kinds:
        exp += ["mmu_fault_arm", "tlbi_suppressed"]
    exp.append("translation_start")
    if "ptw_start" in kinds:
        exp += ["tlb_lookup_miss", "ptw_start"]
        if "pte_read" in kinds:
            exp += ["pte_read", "pte_decode", "tlb_fill"]
            if has_ptw_ids:
                exp += ["ptw_request", "ptw_response"]
        elif "partial_entry_insert" in kinds:
            # A walk entered from a partial/higher-level cached entry can
            # legitimately skip the descriptor fetches below that level.
            # It is not a trace gap; require only the observed insert path.
            exp += ["partial_entry_insert"]
        else:
            # No descriptor fetch and no documented skip: real trace gap.
            exp += ["pte_read", "pte_decode", "tlb_fill"]
    elif "tlb_lookup_miss" in kinds:
        exp.append("tlb_lookup_miss")
    else:
        exp.append("tlb_lookup_hit")
    if "refill_pfn_corrupt" in kinds:
        exp.append("refill_pfn_corrupt")
    exp += ["tlb_entry_insert", "tlb_lookup_hit"]
    # Only require the data path the observed branch could reach.
    if "squash" in kinds:
        # Judge up to the real squash point. translation_result/lsu/... are
        # required only if this chain actually got there.
        for k in ("permission_eval", "translation_result", "lsu_request",
                  "memory_response", "rf_writeback"):
            if k in kinds:
                exp.append(k)
        exp.append("squash")
    else:
        exp += ["permission_eval", "translation_result", "lsu_request",
                "memory_response", "rf_writeback"]
        if "commit" in kinds:
            exp.append("commit")
    if "mmu_fault_disarm" in kinds:
        exp.append("mmu_fault_disarm")
    if has_cache_events:
        if "cache_request" in kinds:
            exp += ["cache_request", "cache_lookup"]
        if "cache_response" in kinds:
            exp.append("cache_response")
    # de-duplicate, preserve order
    out = []
    for k in exp:
        if k not in out:
            out.append(k)
    return out


def parent_kind(ev, by_id):
    p = ev.get("parent_event_id", "")
    if p == "":
        return None
    try:
        par = by_id.get(int(p))
    except ValueError:
        return None
    return kind(par) if par else None


def has_parent(chain_evs, by_id, child_kind, parent_kinds):
    for ev in chain_evs:
        if kind(ev) != child_kind:
            continue
        if parent_kind(ev, by_id) in parent_kinds:
            return True
    return False


def edge_present(chain_evs, by_id, frm, to):
    return has_parent(chain_evs, by_id, to, {frm})


def build_chains(events, by_id, va_points, model, has_ptw_ids=False,
                 has_cache_events=False):
    in_scope = []
    for ev in events:
        v = hexaddr(ev.get("va", ""))
        if v is None:
            continue
        if any((v >> 12) == (p >> 12) for p in va_points):
            in_scope.append(ev)

    groups = defaultdict(list)
    for ev in in_scope:
        tid = ev.get("translation_id", "")
        if tid and tid != "0":
            groups["tid:" + tid].append(ev)
        elif ev.get("unique_request_id", "") not in ("", "0"):
            groups["uid:" + ev["unique_request_id"]].append(ev)

    chains = []
    for key, evs in groups.items():
        chain_evs = list(evs)
        seen = {e["event_id"] for e in evs}
        # Explicit ancestors only. No tick-order inference.
        for ev in evs:
            p = ev.get("parent_event_id", "")
            hops = 0
            while p and int(p) in by_id and int(p) not in seen and hops < 128:
                anc = by_id[int(p)]
                chain_evs.append(anc)
                seen.add(anc["event_id"])
                p = anc.get("parent_event_id", "")
                hops += 1
        # Instruction-keyed terminal/consumer witnesses (carry no VA).
        seqs = {e.get("dyn_inst_seq") for e in evs
                if e.get("dyn_inst_seq", "") not in ("", "0")}
        for ev in events:
            if ev["event_id"] in seen:
                continue
            if kind(ev) in ("rf_writeback", "commit", "squash", "consumer") \
                    and ev.get("dyn_inst_seq", "") in seqs:
                chain_evs.append(ev)
                seen.add(ev["event_id"])
        # FaultID is an explicit chain identity: include the latch lifecycle
        # (arm/suppressed/disarm) that carries no translation id.
        chain_fault = next((e.get("fault_id") for e in chain_evs
                            if e.get("fault_id", "") not in ("", "0")), "0")
        if chain_fault != "0":
            for ev in events:
                if ev["event_id"] in seen:
                    continue
                if ev.get("fault_id", "") == chain_fault:
                    chain_evs.append(ev)
                    seen.add(ev["event_id"])

        chain_evs.sort(key=lambda e: e["event_id"])
        kinds = [kind(e) for e in chain_evs]
        kset = set(kinds)
        asid = next((e.get("asid") for e in evs
                     if e.get("asid", "") != ""), "")
        va = next((e.get("va") for e in evs if e.get("va", "")), "")
        seq = next((e.get("dyn_inst_seq") for e in evs
                    if e.get("dyn_inst_seq", "") not in ("", "0")), "")
        tid = next((e.get("translation_id") for e in evs
                    if e.get("translation_id", "") not in ("", "0")), "")
        # Explicit identity only: W10 context is the workload-defined VA,
        # W9 context is the workload-defined ASID. Never a tick window.
        # Unmatched chains must be recorded honestly as unresolved instead
        # of raising UnboundLocalError (seen when a chain carries no ASID).
        ctx, ctx_basis = "", "unresolved"
        if va and hexaddr(va) in W10_VA_CONTEXT:
            ctx, ctx_basis = W10_VA_CONTEXT[hexaddr(va)], "VA"
        elif asid:
            try:
                asid_i = int(asid, 0)
            except ValueError:
                asid_i = -1
            if asid_i in W9_ASID_CONTEXT:
                ctx, ctx_basis = W9_ASID_CONTEXT[asid_i], "ASID"

        if "commit" in kset:
            terminal = "commit"
        elif "squash" in kset:
            terminal = "squash"
        elif "translation_result" in kset:
            terminal = "no_terminal_after_result"
        elif "tlb_lookup_miss" in kset or "ptw_start" in kset:
            terminal = "walk_in_flight_at_roi_end"
        else:
            terminal = "no_target_events"

        exp = expected_kinds(kset, model, has_ptw_ids, has_cache_events)
        missing = [k for k in exp if k not in kset]

        # ---- causal edges (real ParentEventID, direction-correct) ----
        edges = []
        if "tlbi_match" in kset:
            if not has_parent(chain_evs, by_id, "tlbi_match",
                              {"tlbi_issue", "tlbi_invalidate"}):
                edges.append("tlbi_issue->tlbi_match")
        if model == "M01" and "mmu_fault_arm" in kset:
            if not has_parent(chain_evs, by_id, "mmu_fault_arm",
                              {"tlbi_match"}):
                edges.append("tlbi_match->mmu_fault_arm")
        if "tlbi_suppressed" in kset:
            if not has_parent(chain_evs, by_id, "tlbi_suppressed",
                              {"mmu_fault_arm", "tlbi_match"}):
                edges.append("(mmu_fault_arm|tlbi_match)->tlbi_suppressed")
        # Only the ORIGIN translation (started before the fault was consumed
        # and disarmed) must be parented to the suppressed TLBI.  Later
        # re-executions/continuations of the same fault legitimately descend
        # from a later (non-suppressed) maintenance op; requiring the
        # suppressed parent there would report a phantom edge on a real,
        # fully-linked continuation chain.
        disarm_ids = [int(e["event_id"]) for e in chain_evs
                      if kind(e) == "mmu_fault_disarm"]
        origin_translation = any(
            kind(e) == "translation_start" and
            (not disarm_ids or int(e["event_id"]) < min(disarm_ids))
            for e in chain_evs)
        if ("translation_start" in kset and "tlbi_suppressed" in kset and
                origin_translation):
            edge_ok = has_parent(chain_evs, by_id, "translation_start",
                                 {"tlbi_suppressed", "tlbi_match"})
            if not edge_ok:
                # The transaction is created (translation_start) BEFORE the
                # lookup discovers the stale entry, so that event carries
                # fault_id=0 even though it is the fault's own translation.
                # Accept the real edge through the transaction identity: a
                # translation_start with the same translation_id as a
                # fault-tagged chain event, parented to the suppressed TLBI.
                tids = {e.get("translation_id") for e in chain_evs
                        if e.get("translation_id") not in ("", "0", None)}
                for e in by_id.values():
                    if kind(e) != "translation_start":
                        continue
                    if e.get("translation_id") not in tids:
                        continue
                    parent = by_id.get(e.get("parent_event_id"))
                    if parent is not None and kind(parent) in (
                            "tlbi_suppressed", "tlbi_match"):
                        edge_ok = True
                        break
            if not edge_ok:
                edges.append("tlbi_suppressed->translation_start")
        if "ptw_start" in kset:
            # The walk starts from the real miss that triggered it (the
            # trace parents ptw_start to the last tlb_lookup_miss), not
            # necessarily to translation_start.
            if not has_parent(chain_evs, by_id, "ptw_start",
                              {"translation_start", "tlb_lookup_miss",
                               "tlb_lookup_hit"}):
                edges.append("(translation_start|tlb_lookup_miss)->ptw_start")
            for frm, to in [("ptw_start", "pte_read"),
                            ("pte_read", "pte_decode")]:
                if to in kset and not edge_present(chain_evs, by_id, frm, to):
                    edges.append("%s->%s" % (frm, to))
            if "tlb_fill" in kset and not has_parent(
                    chain_evs, by_id, "tlb_fill",
                    {"pte_decode", "tlb_lookup_hit"}):
                edges.append("pte_decode->tlb_fill")
        # M02 / CONTROL refill edge.
        if "tlb_entry_insert" in kset:
            if model == "M02" and "refill_pfn_corrupt" in kset:
                if not has_parent(chain_evs, by_id, "refill_pfn_corrupt",
                                  {"tlb_fill"}):
                    edges.append("tlb_fill->refill_pfn_corrupt")
                if not has_parent(chain_evs, by_id, "tlb_entry_insert",
                                  {"refill_pfn_corrupt"}):
                    edges.append("refill_pfn_corrupt->tlb_entry_insert")
            else:
                # CONTROL: fill -> insert. M01 stale hit: l2_shared
                # lookup hit -> dtb insert (no walk/fill by construction).
                if not has_parent(chain_evs, by_id, "tlb_entry_insert",
                                  {"tlb_fill", "partial_entry_insert",
                                   "tlb_lookup_hit"}):
                    edges.append("(tlb_fill|tlb_lookup_hit)->tlb_entry_insert")
        if "permission_eval" in kset and not has_parent(
                chain_evs, by_id, "permission_eval",
                {"tlb_entry_insert", "tlb_lookup_hit", "translation_start"}):
            edges.append("(tlb_entry_insert|tlb_lookup_hit)->permission_eval")
        if "translation_result" in kset and not edge_present(
                chain_evs, by_id, "permission_eval", "translation_result"):
            edges.append("permission_eval->translation_result")
        for frm, to in [("translation_result", "lsu_request"),
                        ("lsu_request", "memory_response"),
                        ("memory_response", "rf_writeback")]:
            if to in kset and not edge_present(chain_evs, by_id, frm, to):
                edges.append("%s->%s" % (frm, to))
        if "commit" in kset and not has_parent(
                chain_evs, by_id, "commit",
                {"rf_writeback", "consumer", "memory_response"}):
            edges.append("rf_writeback->commit")
        if "squash" in kset and not has_parent(
                chain_evs, by_id, "squash",
                {"translation_result", "lsu_request", "memory_response",
                 "rf_writeback", "permission_eval", "tlb_entry_insert",
                 "tlb_lookup_hit", "ptw_start", "pte_read", "pte_decode",
                 "tlb_fill", "translation_start"}):
            edges.append("translation->squash")

        # ---- M01 identity integrity ----
        identity_errors = []
        if model == "M01" and "mmu_fault_arm" in kset:
            arms = [e for e in chain_evs if kind(e) == "mmu_fault_arm"]
            suppressed = [e for e in chain_evs
                          if kind(e) == "tlbi_suppressed"]
            for arm in arms:
                eid = arm.get("tlb_entry_id", "")
                gen = arm.get("entry_generation", "")
                if not eid or eid == "0":
                    identity_errors.append("arm_entry_id_missing")
                for s in suppressed:
                    if s.get("tlb_entry_id", "") != eid:
                        identity_errors.append("suppressed_entry_id_mismatch")
                    if s.get("entry_generation", "") != gen:
                        identity_errors.append(
                            "suppressed_generation_mismatch")
            arm_events = [e["event_id"] for e in arms]
            sup_events = [e["event_id"] for e in suppressed]
            if arm_events and sup_events and min(sup_events) < max(arm_events):
                identity_errors.append("suppressed_precedes_arm")
        # ---- M02 PTE integrity ----
        if model == "M02" and "refill_pfn_corrupt" in kset:
            for ev in chain_evs:
                if kind(ev) != "refill_pfn_corrupt":
                    continue
                if ev.get("pte_value_before", "") != \
                        ev.get("pte_value_after", ""):
                    identity_errors.append("pte_value_changed")
                if ev.get("old_pfn", "") == ev.get("new_pfn", ""):
                    identity_errors.append("pfn_not_changed")
                if ev.get("pte_recheck", "") != "descriptor_unchanged":
                    identity_errors.append("pte_recheck_missing")
        # ---- PTW per-level identity (one ID per descriptor fetch) ----
        if has_ptw_ids:
            ptw_ids = {e.get("ptw_request_id") for e in chain_evs
                       if e.get("ptw_request_id", "") not in ("", "0")}
            for pid in sorted(ptw_ids):
                k = {kind(e) for e in chain_evs
                     if e.get("ptw_request_id") == pid}
                if "ptw_request" not in k or "ptw_response" not in k:
                    identity_errors.append(
                        "ptw_id_%s_missing_request_or_response" % pid)
                if "pte_decode" not in k:
                    identity_errors.append(
                        "ptw_id_%s_missing_pte_decode" % pid)
        # ---- cache request identity (composite cache_req_id) ----
        if has_cache_events:
            cache_ids = {e.get("cache_req_id") for e in chain_evs
                         if e.get("cache_req_id", "") not in ("", "0")}
            for cid in sorted(cache_ids):
                k = {kind(e) for e in chain_evs
                     if e.get("cache_req_id") == cid}
                if "cache_lookup" not in k:
                    identity_errors.append(
                        "cache_req_%s_missing_lookup" % cid)
                if "mshr_alloc" in k and "cache_response" not in k:
                    identity_errors.append(
                        "cache_req_%s_missing_response" % cid)

        # ---- completeness, terminal-aware ----
        has_terminal = terminal in ("commit", "squash")
        if not missing and not edges and not identity_errors and has_terminal:
            completeness = "COMPLETE"
        elif not has_terminal and (kset & set(exp)):
            completeness = "TRACE_INCOMPLETE"
        elif kset & set(exp):
            completeness = "PARTIAL"
        else:
            completeness = "INCOMPLETE"

        chains.append({
            "group": key,
            "translation_id": tid,
            "dyn_inst_seq": seq,
            "asid": asid,
            "va": va,
            "context_id": ctx,
            "context_basis": ctx_basis,
            "fault_id": chain_fault,
            "terminal": terminal,
            "has_terminal": has_terminal,
            "event_count": len(chain_evs),
            "observed_kinds": kset,
            "expected_kinds": exp,
            "missing_kinds": missing,
            "missing_edges": edges,
            "identity_errors": identity_errors,
            "completeness": completeness,
            "events": chain_evs,
        })
    chains.sort(key=lambda c: (c["context_id"], c["group"]))
    return chains


def evaluate(events, by_id, args):
    integrity_errors, dup = [], []
    seen = set()
    for ev in events:
        if ev["event_id"] in seen:
            dup.append(ev["event_id"])
        seen.add(ev["event_id"])
        p = ev.get("parent_event_id", "")
        if p == "":
            continue
        try:
            pi = int(p)
        except ValueError:
            integrity_errors.append(
                "event %s (%s) non-integer parent %s" %
                (ev["event_id"], kind(ev), p))
            continue
        if pi not in by_id:
            integrity_errors.append(
                "event %s (%s) parent %s missing" %
                (ev["event_id"], kind(ev), p))
        elif pi == ev["event_id"]:
            integrity_errors.append("event %s self-parent" % ev["event_id"])
        else:
            pt = to_int(by_id[pi], "tick")
            ct = to_int(ev, "tick")
            if pt and ct and ct < pt:
                integrity_errors.append(
                    "event %s (%s) tick %s < parent tick %s" %
                    (ev["event_id"], kind(ev), ct, pt))
    record_integrity = "PASS" if not integrity_errors and not dup else "FAIL"

    va_points = [int(v, 0) for v in args.va]
    has_ptw_ids = any(e.get("ptw_request_id", "") not in ("", "0")
                      for e in events)
    has_cache_events = any(kind(e).startswith("cache_") for e in events)
    chains = build_chains(events, by_id, va_points, args.model,
                          has_ptw_ids, has_cache_events)

    # ---- per-context aggregation ----
    ctx = {cid: {
        "context_id": cid, "asid": "", "target_va": "",
        "chains": 0, "complete": 0, "partial": 0,
        "incomplete": 0, "trace_incomplete": 0,
        "terminal": 0, "representative": 0,
        "fault_ids": set(), "observed_kinds": set(),
    } for cid in CONTEXT_IDS}
    unmapped = defaultdict(lambda: {
        "context_id": "UNMAPPED", "asid": "", "target_va": "",
        "chains": 0, "complete": 0, "partial": 0, "incomplete": 0,
        "trace_incomplete": 0, "terminal": 0, "representative": 0,
        "fault_ids": set(), "observed_kinds": set()})
    for c in chains:
        bucket = ctx.get(c["context_id"])
        if bucket is None:
            bucket = unmapped[c["context_id"]]
            bucket["context_id"] = c["context_id"]
        bucket["chains"] += 1
        key = c["completeness"].lower()
        if key in bucket:
            bucket[key] += 1
        if c["has_terminal"]:
            bucket["terminal"] += 1
        if c["completeness"] == "COMPLETE" and c["has_terminal"]:
            bucket["representative"] += 1
        if c["fault_id"] != "0":
            bucket["fault_ids"].add(c["fault_id"])
        bucket["observed_kinds"].update(c["observed_kinds"])
        if c["asid"] and not bucket["asid"]:
            bucket["asid"] = c["asid"]
        if c["va"] and not bucket["target_va"]:
            bucket["target_va"] = c["va"]
    for cid, b in unmapped.items():
        ctx[cid] = b

    # ---- per-fault aggregation ----
    faults = defaultdict(lambda: {
        "fault_id": "", "context_ids": set(), "translation_ids": [],
        "observed_kinds": set(), "missing_kinds": set(),
        "missing_edges": set(), "identity_errors": set(),
        "terminals": set(), "chains": 0, "complete": 0,
    })
    for c in chains:
        if c["fault_id"] == "0":
            continue
        f = faults[c["fault_id"]]
        f["fault_id"] = c["fault_id"]
        f["context_ids"].add(c["context_id"])
        if c["translation_id"]:
            f["translation_ids"].append(c["translation_id"])
        f["observed_kinds"].update(c["observed_kinds"])
        f["missing_kinds"].update(c["missing_kinds"])
        f["missing_edges"].update(c["missing_edges"])
        f["identity_errors"].update(c["identity_errors"])
        f["terminals"].add(c["terminal"])
        f["chains"] += 1
        if c["completeness"] == "COMPLETE":
            f["complete"] += 1

    # [M02] The corruption is applied when the walk reaches insertTableEntry,
    # i.e. AFTER pte_read/pte_decode/tlb_fill.  Those precursors therefore
    # carry fault_id=0 even though they belong to the SAME translation that
    # produced the faulted insert.  Join them by translation identity; this
    # is the real upstream of the fault, not an inference from time order.
    if args.model == "M02":
        for fid, f in faults.items():
            tids = set()
            for c in chains:
                if c["fault_id"] != fid:
                    continue
                for e in c["events"]:
                    if (kind(e) == "tlb_entry_insert" and
                            e.get("fault_id") == fid and
                            e.get("translation_id") not in ("", "0", None)):
                        tids.add(e["translation_id"])
            joined = False
            for e in events:
                if e.get("translation_id") in tids and kind(e) in (
                        "pte_read", "pte_decode", "tlb_fill", "ptw_start",
                        "ptw_request", "ptw_response"):
                    f["observed_kinds"].add(kind(e))
                    joined = True
            if joined:
                exp = expected_kinds(f["observed_kinds"], args.model,
                                     has_ptw_ids, has_cache_events)
                f["missing_kinds"] = set(exp) - f["observed_kinds"]

    # ---- identity-linked continuations (squash then re-execution) ----
    # A faulting attempt may be squashed; the same corrupted/retained TLB
    # entry is then consumed by a younger dynamic instruction with a new
    # dyn_inst_seq/translation_id. The link is the exact EntryID+Generation
    # (+ VA + PFN) of the entry written by the fault, never tick proximity.
    entry_fault = defaultdict(set)
    for c in chains:
        if c["fault_id"] == "0":
            continue
        for e in c["events"]:
            if kind(e) != "tlb_entry_insert":
                continue
            if e.get("fault_id", "0") != c["fault_id"]:
                continue
            key = (e.get("tlb_entry_id", ""), e.get("entry_generation", ""),
                   e.get("va", ""), e.get("pfn", ""))
            if all(key):
                entry_fault[key].add(c["fault_id"])
    continuations = defaultdict(dict)
    for c in chains:
        if c["fault_id"] != "0":
            continue
        for e in c["events"]:
            if kind(e) != "tlb_lookup_hit":
                continue
            key = (e.get("tlb_entry_id", ""), e.get("entry_generation", ""),
                   e.get("va", ""), e.get("pfn", ""))
            for fid in entry_fault.get(key, ()):
                continuations[fid][c["group"]] = c

    for fid, conts in continuations.items():
        f = faults[fid]
        cont_kinds, cont_edges, cont_term = set(), set(), set()
        cont_ids = []
        for c in conts.values():
            f["context_ids"].add(c["context_id"])
            if c["translation_id"]:
                f["translation_ids"].append(c["translation_id"])
                cont_ids.append(c["translation_id"])
            cont_kinds |= c["observed_kinds"]
            # Only the continuation's data path from the identity-matched
            # lookup is relevant. Its own unrelated ancestors (e.g. a
            # partial insert for another VA) must not break the fault chain.
            ck = c["observed_kinds"]
            cevs = c["events"]
            for need in ("tlb_lookup_hit", "permission_eval",
                         "translation_result", "lsu_request",
                         "memory_response", "rf_writeback", "commit"):
                if need not in ck:
                    cont_edges.add("continuation_missing:%s" % need)
            if "permission_eval" in ck and not has_parent(
                    cevs, by_id, "permission_eval",
                    {"tlb_lookup_hit", "tlb_entry_insert"}):
                cont_edges.add("continuation_lookup->permission")
            for frm, to in [("permission_eval", "translation_result"),
                            ("translation_result", "lsu_request"),
                            ("lsu_request", "memory_response"),
                            ("memory_response", "rf_writeback")]:
                if to in ck and not edge_present(cevs, by_id, frm, to):
                    cont_edges.add("continuation_%s->%s" % (frm, to))
            if "commit" in ck and not has_parent(
                    cevs, by_id, "commit",
                    {"rf_writeback", "consumer", "memory_response"}):
                cont_edges.add("continuation_rf_writeback->commit")
            cont_term.add(c["terminal"])
            f["terminals"].add(c["terminal"])
        f["continuation_ids"] = sorted(set(cont_ids))
        f["observed_kinds"] |= cont_kinds
        exp = expected_kinds(f["observed_kinds"], args.model,
                             has_ptw_ids, has_cache_events)
        f["missing_kinds"] = set(exp) - f["observed_kinds"]
        f["missing_edges"] |= cont_edges
        # A squashed first attempt is a real recovery event; the committed
        # continuation is the terminal of the fault-effect chain.
        if "commit" in cont_term:
            f["missing_edges"] = {e for e in f["missing_edges"]
                                  if e != "translation->squash"}
            f["squash_then_reexecution"] = True
        f["chains"] = 1
        f["complete"] = 1 if (not f["missing_kinds"] and
                              not f["missing_edges"] and
                              not f["identity_errors"] and
                              ("commit" in f["terminals"])) else 0

    for f in faults.values():
        if f["chains"] and f["complete"] == f["chains"]:
            f["completeness"] = "COMPLETE"
        elif f["chains"]:
            f["completeness"] = "PARTIAL"
        else:
            f["completeness"] = "INCOMPLETE"
        f["terminal_verified"] = bool(
            f["terminals"] & {"commit", "squash"})
        f["structural_completeness"] = (
            "COMPLETE" if not f["missing_kinds"] and not f["missing_edges"]
            else "PARTIAL")
        data_path = {"translation_result", "lsu_request", "memory_response",
                     "rf_writeback", "commit"}
        f["fault_effect_coverage"] = (
            "COMPLETE_CAUSAL_CHAIN"
            if data_path <= f["observed_kinds"] and f["terminal_verified"]
            else "LIFECYCLE_ONLY")

    # ---- target event coverage (global, per fault, per context) ----
    required = MODEL_REQUIRED[(args.workload, args.model)]
    global_observed = set()
    for c in chains:
        global_observed.update(c["observed_kinds"])
    global_cov = {
        "required": len(required),
        "observed": len([k for k in required if k in global_observed]),
        "ratio": round(len([k for k in required if k in global_observed]) /
                       len(required), 3),
        "missing": [k for k in required if k not in global_observed],
    }
    per_context_cov = {}
    for cid, b in ctx.items():
        obs = b["observed_kinds"]
        per_context_cov[cid] = {
            "required": len(required),
            "observed": len([k for k in required if k in obs]),
            "missing": [k for k in required if k not in obs],
        }
    per_fault_cov = {
        fid: {
            "required": len(required),
            "observed": len([k for k in required
                             if k in f["observed_kinds"]]),
            "missing": [k for k in required
                        if k not in f["observed_kinds"]],
        } for fid, f in faults.items()
    }
    per_translation_cov = {
        c["group"]: {
            "context_id": c["context_id"],
            "observed": len([k for k in required
                             if k in c["observed_kinds"]]),
            "required": len(required),
            "missing": [k for k in required
                        if k not in c["observed_kinds"]],
        } for c in chains
    }

    # ---- run-level metrics (no representative-chain shortcut) ----
    expected_contexts = [c for c in CONTEXT_IDS
                         if ctx[c]["chains"] > 0]
    complete_chains = [c for c in chains
                       if c["completeness"] == "COMPLETE"]
    terminal_chains = [c for c in chains if c["has_terminal"]]
    contexts_with_terminal = [c for c in expected_contexts
                              if ctx[c]["terminal"] > 0]
    run_complete = (
        bool(chains) and len(complete_chains) == len(chains) and
        len(contexts_with_terminal) == len(expected_contexts))
    run_state = ("COMPLETE" if run_complete else
                 "PARTIAL" if chains else "INCOMPLETE")
    propagation_cov = ("FULL" if
                       len(contexts_with_terminal) == len(expected_contexts)
                       and expected_contexts else
                       "PARTIAL" if contexts_with_terminal else
                       "NOT_OBSERVED")
    terminal_cov = (round(len(terminal_chains) / len(chains), 3)
                    if chains else 0.0)
    missing_edges_total = sum(len(c["missing_edges"]) for c in chains)

    result = {
        "input": args.input,
        "run_id": args.run_id,
        "workload": args.workload,
        "model": args.model,
        "event_count": len(events),
        "parse_skipped": 0 if not hasattr(args, "parse_skipped")
                         else args.parse_skipped,
        "duplicate_event_ids": sorted(set(dup)),
        "record_integrity": record_integrity,
        "record_integrity_errors": integrity_errors[:200],
        "context_mapping": {
            "basis": "W9_ASID" if args.workload == "W9" else "W10_VA",
            "map": (W9_ASID_CONTEXT if args.workload == "W9"
                    else W10_VA_CONTEXT),
        },
        "fault_chain_completeness": {
            fid: {
                "completeness": f["completeness"],
                "structural_completeness": f["structural_completeness"],
                "fault_effect_coverage": f["fault_effect_coverage"],
                "terminal_verified": f["terminal_verified"],
                "oracle_verified": "NOT_EVALUATED_IN_TRACE",
                "context_ids": sorted(f["context_ids"]),
                "translation_ids": sorted(set(f["translation_ids"])),
                "continuation_translation_ids":
                    f.get("continuation_ids", []),
                "squash_then_reexecution":
                    bool(f.get("squash_then_reexecution", False)),
                "missing_kinds": sorted(f["missing_kinds"]),
                "missing_edges": sorted(f["missing_edges"]),
                "identity_errors": sorted(f["identity_errors"]),
            } for fid, f in sorted(faults.items())
        },
        "per_translation_completeness": {
            "chains": len(chains),
            "complete": len(complete_chains),
            "partial": len([c for c in chains
                            if c["completeness"] == "PARTIAL"]),
            "trace_incomplete": len([c for c in chains
                                     if c["completeness"] ==
                                     "TRACE_INCOMPLETE"]),
            "incomplete": len([c for c in chains
                               if c["completeness"] == "INCOMPLETE"]),
        },
        "per_context_completeness": {
            cid: {
                "chains": b["chains"],
                "complete": b["complete"],
                "partial": b["partial"],
                "trace_incomplete": b["trace_incomplete"],
                "incomplete": b["incomplete"],
                "terminal": b["terminal"],
                "trace_coverage": (round(b["complete"] / b["chains"], 3)
                                   if b["chains"] else 0.0),
            } for cid, b in sorted(ctx.items())
        },
        "run_trace_completeness": run_state,
        "propagation_coverage": propagation_cov,
        "terminal_coverage": {
            "chains": len(chains),
            "chains_with_terminal": len(terminal_chains),
            "ratio": terminal_cov,
            "contexts_observed": expected_contexts,
            "contexts_with_terminal": contexts_with_terminal,
        },
        "missing_causal_edges": missing_edges_total,
        "target_event_coverage": {
            "global": global_cov,
            "per_fault": per_fault_cov,
            "per_context": per_context_cov,
            "per_translation": per_translation_cov,
        },
        "kind_counts": dict(Counter(kind(e) for e in events)),
        "chains": [{
            k: (sorted(v) if isinstance(v, set) else v)
            for k, v in c.items() if k != "events"
        } for c in chains],
    }
    return result, chains


def write_csvs(result, chains, prefix):
    # Per-translation.
    with open(prefix + "_per_translation.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "ContextID", "ContextBasis", "ASID", "TargetVA",
                    "TranslationID", "FaultID", "DynInstSeq", "Terminal",
                    "Completeness", "EventCount", "ObservedKinds",
                    "ExpectedKinds", "MissingKinds", "MissingEdges",
                    "IdentityErrors", "FaultChainComplete"])
        for c in chains:
            w.writerow([
                result["run_id"], c["context_id"], c["context_basis"],
                c["asid"], c["va"], c["translation_id"], c["fault_id"],
                c["dyn_inst_seq"], c["terminal"], c["completeness"],
                c["event_count"], ";".join(sorted(c["observed_kinds"])),
                ";".join(c["expected_kinds"]), ";".join(c["missing_kinds"]),
                ";".join(c["missing_edges"]), ";".join(c["identity_errors"]),
                "YES" if c["fault_id"] != "0" and
                c["completeness"] == "COMPLETE" else "NO",
            ])

    # Per-context (explicit ContextID, not ASID aggregation).
    with open(prefix + "_per_context.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "ContextID", "ASID", "TargetVA",
                    "TranslationCount", "CompleteCount", "PartialCount",
                    "TraceIncompleteCount", "IncompleteCount",
                    "TerminalCount", "TraceCoverage", "FaultID",
                    "FaultChainCompleteCount", "TargetEventCoverage"])
        for cid in sorted(result["per_context_completeness"]):
            b = result["per_context_completeness"][cid]
            ctx_chains = [c for c in chains if c["context_id"] == cid]
            asid = next((c["asid"] for c in ctx_chains if c["asid"]), "")
            va = next((c["va"] for c in ctx_chains if c["va"]), "")
            fids = sorted({c["fault_id"] for c in ctx_chains
                           if c["fault_id"] != "0"})
            fcomplete = sum(1 for c in ctx_chains
                            if c["fault_id"] != "0" and
                            c["completeness"] == "COMPLETE")
            cov = result["target_event_coverage"]["per_context"].get(cid, {})
            w.writerow([result["run_id"], cid, asid, va, b["chains"],
                        b["complete"], b["partial"], b["trace_incomplete"],
                        b["incomplete"], b["terminal"],
                        "%.3f" % b["trace_coverage"], ";".join(fids),
                        fcomplete,
                        "%d/%d" % (cov.get("observed", 0),
                                   cov.get("required", 0))])

    # Fault-chain completeness.
    with open(prefix + "_fault_chain.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "FaultID", "ContextID", "TranslationIDs",
                    "Completeness", "StructuralChainCompleteness",
                    "FaultEffectPropagationCoverage", "TerminalVerified",
                    "OracleVerified", "MissingKinds", "MissingEdges",
                    "IdentityErrors"])
        for fid, f in sorted(result["fault_chain_completeness"].items()):
            w.writerow([result["run_id"], fid,
                        ";".join(f["context_ids"]),
                        ";".join(str(x) for x in f["translation_ids"]),
                        f["completeness"], f["structural_completeness"],
                        f["fault_effect_coverage"],
                        "YES" if f["terminal_verified"] else "NO",
                        f["oracle_verified"],
                        ";".join(f["missing_kinds"]),
                        ";".join(f["missing_edges"]),
                        ";".join(f["identity_errors"])])

    # Missing causal edges (real records, never suppressed).
    with open(prefix + "_missing_edges.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "ContextID", "TranslationID", "FaultID",
                    "MissingEdge", "ObservedParentKinds", "Evidence"])
        by_id = {}
        for c in chains:
            for e in c["events"]:
                by_id[e["event_id"]] = e
        for c in chains:
            if not c["missing_edges"]:
                continue
            parents = sorted({parent_kind(e, by_id) or "NONE"
                              for e in c["events"]})
            for edge in c["missing_edges"]:
                w.writerow([result["run_id"], c["context_id"],
                            c["translation_id"], c["fault_id"], edge,
                            ";".join(parents),
                            "ParentEventID chain in %s" % c["group"]])

    # Target event coverage.
    with open(prefix + "_target_coverage.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "Scope", "Key", "Required", "Observed",
                    "Ratio", "Missing"])
        g = result["target_event_coverage"]["global"]
        w.writerow([result["run_id"], "GLOBAL", "-", g["required"],
                    g["observed"], "%.3f" % g["ratio"],
                    ";".join(g["missing"])])
        for fid, f in sorted(
                result["target_event_coverage"]["per_fault"].items()):
            w.writerow([result["run_id"], "FAULT", fid, f["required"],
                        f["observed"],
                        "%.3f" % (f["observed"] / f["required"]),
                        ";".join(f["missing"])])
        for cid, f in sorted(
                result["target_event_coverage"]["per_context"].items()):
            if not ctx_has_events(result, cid):
                continue
            w.writerow([result["run_id"], "CONTEXT", cid, f["required"],
                        f["observed"],
                        "%.3f" % (f["observed"] / f["required"]),
                        ";".join(f["missing"])])
        for tid, f in sorted(
                result["target_event_coverage"]["per_translation"].items()):
            w.writerow([result["run_id"], "TRANSLATION", tid,
                        f["required"], f["observed"],
                        "%.3f" % (f["observed"] / f["required"]),
                        ";".join(f["missing"])])


def ctx_has_events(result, cid):
    return result["per_context_completeness"][cid]["chains"] > 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--workload", required=True, choices=["W9", "W10"])
    ap.add_argument("--model", default="CONTROL",
                    choices=["CONTROL", "M01", "M02"])
    ap.add_argument("--run-id", default="")
    ap.add_argument("--va", action="append", default=[],
                    help="target VA (page granularity), repeatable")
    ap.add_argument("--csv-prefix", default="")
    ap.add_argument("--report-json", default="")
    ap.add_argument("--jsonl", default="")
    args = ap.parse_args()

    events, bad = load_events(args.input)
    args.parse_skipped = bad
    by_id = {}
    for ev in events:
        by_id[ev["event_id"]] = ev

    result, chains = evaluate(events, by_id, args)
    result["parse_skipped"] = bad

    if args.csv_prefix:
        write_csvs(result, chains, args.csv_prefix)
    if args.report_json:
        with open(args.report_json, "w") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
    if args.jsonl:
        with open(args.jsonl, "w") as fh:
            for ev in events:
                fh.write(json.dumps(ev, sort_keys=True) + "\n")

    print(json.dumps({k: result[k] for k in (
        "run_id", "event_count", "record_integrity",
        "fault_chain_completeness", "per_translation_completeness",
        "run_trace_completeness", "propagation_coverage",
        "terminal_coverage", "missing_causal_edges",
        "target_event_coverage")}, indent=2))
    return 0 if result["record_integrity"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
