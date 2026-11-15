#!/usr/bin/env python3
"""Phase-3 terminal-aware MMU validator for M01-M08.

The PROP-EVT parser is NOT duplicated: this tool imports
tools/mmu_trace_validate_v4.py (which imports v3) and reuses its parser,
event model, parent-edge helpers and (for M01/M02) its chain evaluator and
M02 entry-lineage audit.

For every run it emits the formal verdict fields:

    ActivationStatus, FaultConsumptionStatus, PropagationStatus,
    TraceCompleteness, MissingCausalEdges, TerminalState, OracleResult,
    fault_id, activation_event_id, consumption_event_id

Model-specific execution realities are honoured, never papered over:

  * M06 is an exception path: a Translation Fault is the expected terminal;
    no LSU request and no normal commit are required.  The local descriptor
    clear (bit0 1 -> 0) and the Invalid decode are the causal evidence.
    DETECTED_CONTAINED additionally requires real delivery evidence
    (`exception_delivery`, or summary exception_delivered=1 with
    result_propagated=1); a consumed descriptor squashed before delivery is
    SQUASHED/TRACE_INCOMPLETE, never DETECTED_CONTAINED.
  * M03 consumes a fabricated hit: the lookup event must be a hit bound to a
    real entry identity (candidate_entry_id / generation) whose ASID differs
    from the requester's ASID.
  * M04/M05 are persistent entry faults: the faulted entry lifetime is keyed
    by (tlb_instance, entry_id, generation); later hits of that exact lifetime
    are the consumption/reuse witnesses.
  * M08 changes only the outgoing Request PA: TLB entry/pfn must stay equal
    while the request PA differs.

Missing evidence is always reported (missing kinds and missing parent edges).
Unknown facts yield NOT_OBSERVED / PARTIAL; no rule is deleted and no unrelated
events are merged to claim COMPLETE.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mmu_trace_validate_v4 as v4
import mmu_evidence_chain as evidence_chain

v3 = v4.v3

ACTIVATION_KINDS = {
    "M01": ["mmu_fault_arm"],
    "M02": ["refill_pfn_corrupt"],
    "M03": ["mmu_fault_activate"],
    "M04": ["mmu_fault_activate"],
    "M05": ["mmu_fault_activate"],
    "M06": ["mmu_fault_activate"],
    "M07": ["mmu_fault_activate"],
    "M08": ["mmu_fault_activate"],
}

CONSUME_KINDS = {
    "M01": ["tlb_lookup_hit", "fault_entry_consume", "fault_entry_reuse"],
    "M02": ["fault_entry_consume", "fault_entry_reuse", "tlb_lookup_hit",
            "translation_result", "lsu_request"],
    "M03": ["tlb_lookup_hit", "translation_result", "lsu_request"],
    "M04": ["tlb_lookup_hit", "fault_entry_consume", "fault_entry_reuse",
            "translation_result", "lsu_request"],
    "M05": ["tlb_lookup_hit", "fault_entry_consume", "fault_entry_reuse",
            "ptw_start", "pte_read", "translation_result", "lsu_request"],
    "M06": ["pte_decode", "arch_translation_fault", "translation_fault"],
    "M07": ["translation_result", "lsu_request"],
    "M08": ["translation_result", "lsu_request"],
}

# The five instruction-side contexts whose propagation must be proven by an
# explicit identity join, not by temporal adjacency or an activation row.
STRICT_CONTEXTS = {
    ("M03", "R05"), ("M04", "R05"), ("M05", "R05"),
    ("M07", "R04"), ("M07", "R05"),
}

RESPONSE_KINDS = {"cache_response", "memory_response"}
EXCEPTION_KINDS = {"arch_translation_fault", "translation_fault",
                   "exception_delivery"}
CONTAIN_KINDS = {"request_suppressed", "store_lost_contained"}
SQUASH_KINDS = {"squash", "squash_discarded", "squash_masked"}
SHELTER_KINDS = EXCEPTION_KINDS | CONTAIN_KINDS

# Expected terminal sets from worksheet 07 (ExpectedTerminalStates).  They are
# recorded for consistency reporting, never used to rewrite the observed
# terminal.
EXPECTED_TERMINALS = {
    "M01": {"SDC", "ACTIVATED_MASKED", "SQUASHED", "DETECTED_CONTAINED",
            "CRASH", "HANG/TIMEOUT"},
    "M02": {"SDC", "ACTIVATED_MASKED", "SQUASHED", "DETECTED_CONTAINED",
            "CRASH", "HANG/TIMEOUT"},
    "M03": {"SDC", "ACTIVATED_MASKED", "SQUASHED", "DETECTED_CONTAINED",
            "CRASH", "HANG/TIMEOUT"},
    "M04": {"SDC", "ACTIVATED_MASKED", "SQUASHED", "DETECTED_CONTAINED",
            "CRASH", "HANG/TIMEOUT"},
    "M05": {"SDC", "ACTIVATED_MASKED", "SQUASHED", "DETECTED_CONTAINED",
            "CRASH", "HANG/TIMEOUT"},
    "M06": {"DETECTED_CONTAINED", "CRASH", "INJECTION_NOT_ACTIVATED",
            "HANG/TIMEOUT", "TRACE_INCOMPLETE"},
    "M07": {"SDC", "ARCH_STATE_CORRUPTION", "DETECTED_CONTAINED", "CRASH",
            "ACTIVATED_MASKED", "TRACE_INCOMPLETE"},
    "M08": {"SDC", "ARCH_STATE_CORRUPTION", "ACTIVATED_MASKED", "SQUASHED",
            "CRASH", "HANG/TIMEOUT"},
}


# ---------------------------------------------------------------------------
# Run layout / input resolution
# ---------------------------------------------------------------------------


def find_run_paths(run_dir):
    def first(*rels):
        for rel in rels:
            path = os.path.join(run_dir, rel)
            if os.path.isfile(path):
                return path
        return None

    return {
        "trace": first("Trace/prop_evt.txt.gz", "run/prop_evt.txt.gz",
                       "prop_evt.txt.gz"),
        "terminal": first("Run_Log/board.terminal", "run/board.terminal",
                          "board.terminal"),
        # The faulted run's own terminal observation.  `golden_output.txt`
        # is accepted only for historical runs; new runs write
        # `observed_output.txt` (an independent control golden is separate).
        "golden": first("Run_Log/observed_output.txt", "observed_output.txt",
                        "Run_Log/golden_output.txt", "golden_output.txt"),
        "manifest": first("sample_manifest.json"),
        "command": first("Run_Log/command.txt", "command.txt"),
        "exit_code": first("Run_Log/gem5_exit_code.txt"),
    }


def load_manifest(path):
    if path and os.path.isfile(path):
        try:
            with open(path) as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}
    return {}


def _manifest_value(manifest, *keys, default=None):
    for key in keys:
        if manifest.get(key) not in (None, ""):
            return manifest[key]
    return default


def _eint(ev, key, default=0, hexa=False):
    value = ev.get(key, "")
    if value in ("", None):
        return default
    try:
        return int(value, 16) if hexa else int(value, 0)
    except ValueError:
        try:
            return int(value, 16)
        except ValueError:
            return default


def _kind(ev):
    return v3.kind(ev)


def _fault_events(events, fid):
    return [e for e in events if e.get("fault_id", "0") == str(fid)]


def _first(evs, kinds, after_id=0):
    kinds = set(kinds)
    for ev in sorted(evs, key=lambda e: e["event_id"]):
        if ev["event_id"] <= after_id:
            continue
        if _kind(ev) in kinds:
            return ev
    return None


def _edge(evs, by_id, child, parents):
    return v3.has_parent(evs, by_id, child, set(parents))


def scope_events(events, model, workload, context, target_va):
    """Select the events belonging to this sample's context.

    A workload rcS can execute all five contexts in one run.  The fault chain
    must be selected by explicit identity, never by "first fault in the
    file":
      * W9/M01: the context is the workload-defined ASID (220/224/.../236);
      * W10/W12/W13/W14: each context has a distinct target VA;
      * W11/M03 R01-R04 share one VA; the model is one-shot, so at most one
        activation can exist.  More than one activation at the same VA is
        reported as ambiguous instead of silently merged.
    Explicit ancestors of the selected events are retained for the parent
    graph.
    """
    if target_va is None:
        return events, "no_target_va", False
    # Page-level identity (an instruction fetch may be at page_base + offset;
    # the model targets the 4 KiB page, and v3 uses the same page test).
    target_page = target_va >> 12
    matched = []
    for e in events:
        va = _eint(e, "va", -1, hexa=True)
        if va >= 0 and (va >> 12) == target_page:
            matched.append(e)
    asid = None
    if workload == "W9" or model == "M01":
        asid = {v: k for k, v in v3.W9_ASID_CONTEXT.items()}.get(context)
        if asid is not None:
            matched = [e for e in matched
                       if e.get("asid", "") in ("", str(asid))]
    if not matched:
        return events, "target_va_unmatched_fallback_all", False

    ids = {e["event_id"] for e in matched}
    tids = {e.get("translation_id") for e in matched
            if e.get("translation_id", "") not in ("", "0")}
    seqs = {e.get("dyn_inst_seq") for e in matched
            if e.get("dyn_inst_seq", "") not in ("", "0")}
    for e in events:
        if tids and e.get("translation_id", "") in tids:
            ids.add(e["event_id"])
        if seqs and e.get("dyn_inst_seq", "") in seqs:
            ids.add(e["event_id"])
    # Run-level honest summaries are context-independent evidence.
    for e in events:
        if _kind(e) in ("mmu_fault_unactivated", "mmu_fault_summary"):
            ids.add(e["event_id"])
    # Explicit ancestor closure (parent_event_id only).
    by_all = {e["event_id"]: e for e in events}
    stack = list(ids)
    while stack:
        eid = stack.pop()
        parent = by_all[eid].get("parent_event_id", "")
        try:
            pid = int(parent)
        except (TypeError, ValueError):
            continue
        if pid in by_all and pid not in ids:
            ids.add(pid)
            stack.append(pid)
    scoped = sorted((e for e in events if e["event_id"] in ids),
                    key=lambda e: e["event_id"])
    act_kinds = set(ACTIVATION_KINDS.get(model, []))
    activations = [e for e in scoped if _kind(e) in act_kinds and
                   e.get("fault_id", "0") not in ("", "0")]
    ambiguous = len({e.get("fault_id") for e in activations}) > 1
    basis = "va+asid/tid/seq" if asid is not None else "va/tid/seq"
    return scoped, basis, ambiguous


def load_events_tolerant(path):
    """Reuse the v3 parser but survive a live/truncated gzip stream.

    A run may still be writing prop_evt.txt.gz; the events read before the
    truncation are real and are kept, and the read error is reported honestly
    (it forces TRACE_INCOMPLETE).
    """
    events, bad, error = [], 0, ""
    try:
        with v3.open_maybe_gz(path) as fh:
            for line in fh:
                ev = v3.parse_line(line)
                if ev is None:
                    continue
                try:
                    ev["event_id"] = int(ev.get("event_id", ""))
                except (TypeError, ValueError):
                    bad += 1
                    continue
                events.append(ev)
    except (EOFError, OSError) as exc:
        error = "%s: %s" % (type(exc).__name__, exc)
    events.sort(key=lambda e: e["event_id"])
    return events, bad, error


# ---------------------------------------------------------------------------
# Trace integrity
# ---------------------------------------------------------------------------


def record_integrity(events, by_id):
    dup, errors = [], []
    seen = set()
    for ev in events:
        if ev["event_id"] in seen:
            dup.append(ev["event_id"])
        seen.add(ev["event_id"])
        parent = ev.get("parent_event_id", "")
        # "" / "0" both mean "no parent" (root event); PROP-EVT roots are
        # emitted with either spelling depending on the emitter.
        if parent in ("", "0"):
            continue
        try:
            pid = int(parent)
        except ValueError:
            errors.append("event %s (%s) non-integer parent %s" %
                          (ev["event_id"], _kind(ev), parent))
            continue
        if pid not in by_id:
            errors.append("event %s (%s) parent %s missing" %
                          (ev["event_id"], _kind(ev), parent))
        elif pid == ev["event_id"]:
            errors.append("event %s self-parent" % ev["event_id"])
        else:
            pt = _eint(by_id[pid], "tick")
            ct = _eint(ev, "tick")
            if pt and ct and ct < pt:
                errors.append("event %s (%s) tick %s < parent tick %s" %
                              (ev["event_id"], _kind(ev), ct, pt))
    return {
        "status": "PASS" if not errors and not dup else "FAIL",
        "errors": errors[:100],
        "duplicate_event_ids": sorted(set(dup)),
    }


# ---------------------------------------------------------------------------
# Fault / activation / consumption selection
# ---------------------------------------------------------------------------


def select_fault(events, model):
    candidates = []
    act_kinds = set(ACTIVATION_KINDS.get(model, ["mmu_fault_activate"]))
    for ev in events:
        fid = ev.get("fault_id", "0")
        if fid in ("", "0"):
            continue
        if _kind(ev) in act_kinds:
            candidates.append((ev["event_id"], str(fid), ev))
    if candidates:
        candidates.sort(key=lambda x: x[0])
        activation = candidates[0][2]
        return candidates[0][1], activation

    # No activation kind: fall back to the fault id with the most events.
    counts = {}
    first_event = {}
    for ev in events:
        fid = ev.get("fault_id", "0")
        if fid in ("", "0"):
            continue
        counts[fid] = counts.get(fid, 0) + 1
        first_event.setdefault(fid, ev)
    if not counts:
        return "0", None
    fid = sorted(counts, key=lambda k: (-counts[k], first_event[k]["event_id"]))[0]
    return fid, first_event[fid]


def select_consumption(events, by_id, model, fid, activation):
    if str(fid) in ("", "0"):
        return None, "no_fault"
    evs = _fault_events(events, fid)
    after = activation["event_id"] if activation else 0
    consume = _first(evs, CONSUME_KINDS.get(model, []), after)
    if consume is not None:
        return consume, "explicit_consumer"
    # No model is allowed to claim consumption at activation.  M03/M04/M07
    # (and M08) must name a later event that reads the faulted state; the
    # five instruction-side contexts are additionally checked by
    # mmu_evidence_chain's identity joins.  A missing consumer is reported.
    if model == "M06" and activation is not None:
        pte = _first(_fault_events(events, fid), ["pte_decode"], after)
        if pte is not None:
            return pte, "faulted_descriptor_decode"
        return activation, "exception_path_activation"
    return None, "no_consumer"


# ---------------------------------------------------------------------------
# Model profiles / required evidence
# ---------------------------------------------------------------------------


def _path_required(model, observed, mode, terminal):
    """Expected causal kinds for the branch this run really took.

    Empty list means the model requires no normal LSU data path (M06).  The
    list is never reduced to what was observed: absent kinds are reported as
    missing_kind:<k> by the caller.
    """
    if model == "M06":
        return ["pte_decode"]
    if model in ("M03", "M04") and mode == "Execute":
        # The ITLB false hit / resident-PFN hit is consumed by the IFU; there
        # is no data-side LSU chain.
        return ["tlb_lookup_hit"]
    if model == "M07" and mode == "Execute":
        # An execute permission inversion is consumed by the IFU; there is no
        # data-side LSU chain.  The activation itself carries the real
        # pre/post grant decision.
        return []
    if model == "M05" and mode == "Execute":
        # The corrupted partial walk-cache entry is consumed by an ITLB miss:
        # insert -> later partial hit -> wrong translation -> instruction
        # fetch request.  There is no data-side cache_response/commit row for
        # the fetch itself (the fetched instruction commits under its own
        # dynamic sequence, not the synthetic fetch transaction), so requiring
        # those kinds here would demand an event the IFU path cannot emit.
        # The guest oracle plus the wrong fetch PA prove the propagation.
        return ["partial_entry_insert", "tlb_lookup_hit",
                "translation_result", "lsu_request"]

    req = []
    if model == "M03":
        req += ["tlb_lookup_hit"]
    elif model == "M04":
        req += ["tlb_lookup_hit"]
    elif model == "M05":
        req += ["partial_entry_insert"]
        if "tlb_lookup_hit" in observed or "fault_entry_consume" in observed:
            req += ["tlb_lookup_hit"]
    elif model == "M07":
        req += ["permission_eval"]
    elif model in ("M01", "M02"):
        return []

    if terminal in ("exception", "contained"):
        # The architectural exception/containment is the terminal; the data
        # path is genuinely absent.
        return req + ["translation_result"] if "translation_result" in observed \
            else req
    if terminal == "squash":
        return req + (["translation_result"] if "translation_result" in observed
                      else []) + ["squash"]

    req += ["translation_result", "lsu_request"]
    req += ["memory_response"] if "memory_response" in observed else \
        ["cache_response"] if "cache_response" in observed else \
        ["memory_response"]
    if mode in ("Read", "Atomic"):
        req += ["rf_writeback"]
    req += ["commit"]
    return req


def _edge_checks(observed_events, by_id, required, model, terminal):
    """ParentEventID checks for the required transitions that are observed.

    Missing kinds are NOT turned into edge errors here (they are reported as
    missing kinds); only a present child without the expected parent edge is
    an edge error.
    """
    missing = []
    kinds = {_kind(e) for e in observed_events}
    present = [k for k in required if k in kinds]

    # Every post-activation evidence event must have a real in-fault parent
    # (never a dangling root and never a self-parent).
    for ev in observed_events:
        k = _kind(ev)
        if k in ("mmu_fault_arm", "mmu_fault_activate", "refill_pfn_corrupt",
                 "translation_start"):
            # translation_start is the ROOT of its transaction by
            # construction (it is emitted when the transaction is created,
            # before any lookup/activation exists to be its parent).  Its
            # causality is carried by translation_id, and every downstream
            # event in the chain is still parent-checked below.
            continue
        parent = ev.get("parent_event_id", "")
        if parent in ("", "0"):
            missing.append("orphan:%s" % k)

    if "translation_result" in kinds and "lsu_request" in kinds:
        if not _edge(observed_events, by_id, "lsu_request",
                     {"translation_result"}):
            missing.append("translation_result->lsu_request")
    if "lsu_request" in kinds:
        if not _edge(observed_events, by_id, "lsu_request",
                     {"translation_result", "permission_eval",
                      "tlb_lookup_hit"}):
            missing.append("(translation_result|lookup)->lsu_request")
    if kinds & RESPONSE_KINDS:
        child = "memory_response" if "memory_response" in kinds \
            else "cache_response"
        if not _edge(observed_events, by_id, child,
                     {"lsu_request", "cache_request", "cache_lookup",
                      "mshr_alloc"}):
            missing.append("lsu_request->%s" % child)
    if "rf_writeback" in kinds:
        if not _edge(observed_events, by_id, "rf_writeback",
                     {"memory_response", "cache_response", "rf_writeback"}):
            missing.append("response->rf_writeback")
    if "commit" in kinds:
        if not _edge(observed_events, by_id, "commit",
                     {"rf_writeback", "consumer", "memory_response",
                      "translation_result", "lsu_request"}):
            missing.append("rf_writeback->commit")
    if "pte_decode" in kinds:
        if not _edge(observed_events, by_id, "pte_decode",
                     {"ptw_start", "pte_read", "translation_start",
                      "mmu_fault_activate"}):
            missing.append("ptw_start->pte_decode")
    if "fault_state_consumed" in kinds:
        if not _edge(observed_events, by_id, "fault_state_consumed",
                     {"pte_decode", "mmu_fault_activate"}):
            missing.append("pte_decode->fault_state_consumed")
    if "fault_result_propagated" in kinds:
        if not _edge(observed_events, by_id, "fault_result_propagated",
                     {"fault_state_consumed", "pte_decode",
                      "mmu_fault_activate"}):
            missing.append("fault_state_consumed->fault_result_propagated")
    if "exception_delivery" in kinds:
        if not _edge(observed_events, by_id, "exception_delivery",
                     {"fault_result_propagated", "pte_decode",
                      "translation_result", "fault_state_consumed",
                      "mmu_fault_activate"}):
            missing.append("fault_result_propagated->exception_delivery")
    elif kinds & EXCEPTION_KINDS:
        child = "arch_translation_fault" if "arch_translation_fault" in kinds \
            else "translation_fault"
        if not _edge(observed_events, by_id, child,
                     {"pte_decode", "translation_start", "pte_read",
                      "mmu_fault_activate", "lsu_request",
                      "translation_result"}):
            missing.append("pte_decode->%s" % child)
    if terminal == "squash" and "squash" in kinds:
        if not _edge(observed_events, by_id, "squash",
                     {"translation_result", "lsu_request", "memory_response",
                      "rf_writeback", "permission_eval", "tlb_lookup_hit",
                      "pte_decode", "translation_start", "cache_request",
                      "cache_lookup", "mshr_alloc", "cache_response"}):
            missing.append("translation->squash")
    return sorted(set(missing))


# ---------------------------------------------------------------------------
# Model-specific causal proofs
# ---------------------------------------------------------------------------


def _cross_dynamic_wrong_commit(events, activation):
    """Final-consumer rule for persistent entry faults (M04/M05/M08).

    A refill/promotion can deliver the wrong PA to an instruction whose trace
    row is not tagged with the one-shot fault_id (the entry lineage changed).
    The target VA mapping to the injected decoy PA is itself impossible by
    construction, so a committed access to `activation.va` carrying
    `activation.new_pa` is causally fault-derived.  Returns (proven, basis).
    """
    if not activation:
        return False, ""
    target_va = activation.get("va", "")
    new_pa = _eint(activation, "new_pa", -1, hexa=True)
    aid = activation.get("event_id", 0)
    if not target_va or new_pa < 0:
        return False, ""
    carriers = []
    for ev in events:
        if ev.get("event_id", 0) <= aid:
            continue
        if ev.get("va", "") != target_va:
            continue
        # PROP-EVT pa fields are unprefixed HEX ("pa=83557000"), while the
        # golden rows use 0x-prefixed values.  _hexval() tries base 0 first
        # and therefore mis-reads an all-digit hex PA as decimal; parse the
        # trace field as base 16 unconditionally.
        raw_pa = ev.get("pa", "")
        try:
            ev_pa = int(raw_pa, 16) if raw_pa else -1
        except ValueError:
            ev_pa = -1
        if ev_pa != new_pa:
            continue
        if _kind(ev) not in ("translation_result", "lsu_request",
                             "cache_request", "cache_lookup", "mshr_alloc",
                             "memory_response", "rf_writeback", "consumer"):
            continue
        carriers.append(ev)
    if not carriers:
        return False, ""
    carrier_seqs = {e.get("dyn_inst_seq", "") for e in carriers if
                    e.get("dyn_inst_seq")}
    commits = [e for e in events
               if e.get("event_id", 0) > aid and
               _kind(e) in ("commit", "consumer") and
               e.get("commit_status") == "committed" and
               (e.get("dyn_inst_seq", "") in carrier_seqs or not carrier_seqs)]
    if not commits:
        return False, ""
    return True, ("committed access to target VA %s carried injected PA "
                  "0x%x (carrier events %s, commit events %s)" %
                  (target_va, new_pa,
                   ",".join(str(e["event_id"]) for e in carriers[:4]),
                   ",".join(str(e["event_id"]) for e in commits[:4])))


def prove_wrong_value(model, events, activation, consumption, lineage_rows,
                      v3_result):
    """Return (proven, basis, contradictions).  No proof -> False."""
    fid = activation.get("fault_id", "0") if activation else "0"
    evs = _fault_events(events, fid) if fid != "0" else []
    basis, contradictions = [], []

    if model == "M01":
        for row in lineage_rows:
            if str(row.get("fault_id")) != str(fid):
                continue
            if row.get("errors"):
                contradictions.extend(row["errors"])
                continue
            if row.get("cross_dynamic") or row.get("downstream", {}).get(
                    "commit") or row.get("downstream", {}).get("squash"):
                return True, ["M01 stale l2_shared entry consumed by a real "
                              "lookup with matching entry identity"], []
        # M01 does not emit fault_entry_consume; its witnesses are the arm,
        # the suppressed matching TLBI(s), the consuming l2_shared hit and
        # the disarm, all keyed by the SAME entry id + generation.
        if activation is not None:
            eid = activation.get("tlb_entry_id", "")
            gen = activation.get("entry_generation", "")
            if eid and eid != "0":
                suppressed = [e for e in evs
                              if _kind(e) == "tlbi_suppressed" and
                              e.get("tlb_entry_id") == eid and
                              e.get("entry_generation") == gen]
                lookups = [e for e in evs
                           if _kind(e) == "tlb_lookup_hit" and
                           e.get("tlb_entry_id") == eid and
                           e.get("entry_generation") == gen and
                           e["event_id"] > activation["event_id"]]
                disarm = [e for e in evs
                          if _kind(e) == "mmu_fault_disarm" and
                          e.get("tlb_entry_id") == eid]
                if suppressed and lookups and disarm:
                    return True, [
                        "l2_shared entry %s:%s survived %d matching TLBI(s), "
                        "was consumed by lookup event %s, then disarmed" %
                        (eid, gen, len(suppressed), lookups[0]["event_id"])], []
        return False, ["no identity-verified stale l2_shared consumption"], []

    if model == "M02":
        for row in lineage_rows:
            if str(row.get("fault_id")) != str(fid):
                continue
            if row.get("errors"):
                contradictions.extend(row["errors"])
            else:
                basis.append("M02 faulted insert %s:%s:%s consumed by "
                             "lookup %s" % (row.get("tlb_instance"),
                                            row.get("tlb_entry_id"),
                                            row.get("entry_generation"),
                                            row.get("lookup_event_id")))
        return bool(basis), basis, sorted(set(contradictions))

    if activation is None:
        return False, ["no activation event"], []

    if model == "M03":
        cand_asid = _eint(activation, "candidate_asid", -1)
        req_asid = _eint(activation, "asid", -2)
        entry_id = activation.get("candidate_entry_id", "")
        if activation.get("lookup_outcome") == "false_hit" and \
                entry_id not in ("", "0") and cand_asid >= 0 and \
                req_asid >= 0 and cand_asid != req_asid:
            return True, ["real candidate entry %s with ASID %d != requester "
                          "ASID %d" % (entry_id, cand_asid, req_asid)], []
        return False, ["false-hit identity/ASID facts absent"], []

    if model == "M04":
        old_pfn = _eint(activation, "old_pfn", -1, hexa=True)
        new_pfn = _eint(activation, "new_pfn", -1, hexa=True)
        if old_pfn >= 0 and new_pfn >= 0 and old_pfn != new_pfn:
            entry = "%s:%s:%s" % (activation.get("tlb_instance", ""),
                                  activation.get("tlb_entry_id", ""),
                                  activation.get("entry_generation", ""))
            consumes = [e for e in evs
                        if _kind(e) in ("fault_entry_consume",
                                        "fault_entry_reuse")]
            basis = ["resident entry %s pfn 0x%x -> 0x%x; %d "
                     "entry-lifetime consumer(s)" %
                     (entry, old_pfn, new_pfn, len(consumes))]
            cross, cross_basis = _cross_dynamic_wrong_commit(events,
                                                            activation)
            if cross:
                basis.append(cross_basis)
            return True, basis, []
        return False, ["resident old_pfn/new_pfn facts absent"], []

    if model == "M05":
        before = _eint(activation, "next_table_pa_before", -1, hexa=True)
        after = _eint(activation, "next_table_pa_after", -1, hexa=True)
        if before < 0 or after < 0 or before == after:
            return False, ["partial next-table before/after facts absent"], []
        aid = activation["event_id"]
        # The consumer must be a LATER PARTIAL hit whose pfn is the corrupted
        # next-table base.  A clean complete hit is not a consumer (the old
        # rule accepted any lookup hit and produced a false positive).
        hits = [e for e in events
                if _kind(e) == "tlb_lookup_hit" and
                str(e.get("entry_partial", "")) == "1" and
                _eint(e, "pfn", -1, hexa=True) == after and
                e["event_id"] > aid]
        if not hits:
            # Look for the honest containment fact: the corrupted entry was
            # invalidated before any partial hit (e.g. the guest's mprotect
            # range TLBI), so the fault never propagated.
            invalidated = [e for e in events
                           if _kind(e) in ("tlbi_invalidate", "tlbi_match")
                           and _eint(e, "page_size_n", -1) == 21 and
                           e["event_id"] > aid]
            note = ("corrupted partial base 0x%x had no later partial hit"
                    % after)
            if invalidated:
                note += ("; a level-2 partial entry was invalidated at event "
                         "%s (guest containment)" % invalidated[0]["event_id"])
            return False, [note], []
        hit = hits[0]
        # The resumed walk must read the decoy L3 table (same 4K page as the
        # substituted base), not the original next-table page.
        reads = [e for e in events
                 if _kind(e) in ("pte_read", "pte_decode") and
                 e["event_id"] > hit["event_id"] and
                 _eint(e, "pte_address", -1, hexa=True) >= 0 and
                 (_eint(e, "pte_address", -1, hexa=True) >> 12) ==
                 (after >> 12)]
        if not reads:
            return False, ["partial hit on 0x%x but the resumed walk did not "
                           "read the decoy L3 table" % after], []
        return True, ["L2 partial next-table base 0x%x -> 0x%x; later partial "
                      "hit event %s; resumed walk read decoy PTE at event %s" %
                      (before, after, hit["event_id"], reads[0]["event_id"])], []

    if model == "M06":
        before = _eint(activation, "descriptor_before", -1, hexa=True)
        after = _eint(activation, "descriptor_after", -1, hexa=True)
        pte = _first(evs, ["pte_decode"], activation["event_id"])
        if before >= 0 and after >= 0 and (before & 1) == 1 and \
                (after & 1) == 0 and pte is not None and \
                pte.get("descriptor_type", "") == "Invalid":
            for pte_key in ("pte_value_before", "pte_value_after"):
                pass
            return True, ["L3 descriptor bit0 cleared (0x%x -> 0x%x) and "
                          "decoded Invalid; Translation Fault path" %
                          (before, after)], []
        return False, ["descriptor clear / Invalid decode facts absent"], []

    if model == "M07":
        pb = activation.get("permission_before", "")
        pa = activation.get("permission_after", "")
        if pb == "false" and pa == "true":
            return True, ["permission grant false -> true"], []
        return False, ["permission inversion facts absent"], []

    if model == "M08":
        old_pa = _eint(activation, "old_pa", -1, hexa=True)
        new_pa = _eint(activation, "new_pa", -1, hexa=True)
        old_pfn = _eint(activation, "old_pfn", -1, hexa=True)
        new_pfn = _eint(activation, "new_pfn", -1, hexa=True)
        if old_pa >= 0 and new_pa >= 0 and old_pa != new_pa and \
                old_pfn == new_pfn:
            hit = None
            for ev in sorted(evs, key=lambda e: e["event_id"]):
                if ev["event_id"] <= activation["event_id"]:
                    continue
                if _eint(ev, "pa", -1, hexa=True) == new_pa:
                    hit = ev
                    break
            return bool(hit), (["request PA 0x%x -> 0x%x with TLB pfn "
                               "unchanged (0x%x); consumer %s carries new PA" %
                               (old_pa, new_pa, old_pfn, hit["event_id"])]
                              if hit else
                              ["request PA changed but no consumer carries "
                               "the new PA"]), []
        return False, ["request PA / TLB pfn facts absent"], []

    return False, ["no model-specific proof"], []


# ---------------------------------------------------------------------------
# Golden oracle
# ---------------------------------------------------------------------------


def parse_golden(path):
    rows = []
    if not path or not os.path.isfile(path):
        return rows
    pat = re.compile(r"^W(?:9|10S|1[0-4])_(?:RESULT|INFO|LIMITATION)\b")
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not pat.match(line):
                continue
            d = {"_line": line}
            for key, value in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)",
                                         line):
                d[key] = value
            rows.append(d)
    return rows


def _pick_golden(rows, context):
    if not rows:
        return None
    # RESULT rows are the oracle; INFO/LIMITATION rows are diagnostics.
    result_rows = [r for r in rows if "_RESULT" in r.get("_line", "")]
    for row in result_rows:
        if row.get("ctx") == context:
            return row
    for row in rows:
        if row.get("ctx") == context:
            return row
    return rows[0] if len(rows) == 1 else None


def _hexval(row, key):
    if not row or key not in row:
        return None
    try:
        return int(row[key], 0)
    except ValueError:
        try:
            return int(row[key], 16)
        except ValueError:
            return None


def evaluate_oracle(model, workload, context, golden_rows, proof,
                    terminal_state):
    """Return (OracleResult, evidence dict).

    PASS  = the oracle observed the no-fault golden value (fault masked or
            not architecturally exposed).
    FAIL  = the oracle exposed the wrong value/state, but only when the trace
            proves the injected fault was consumed; otherwise NOT_OBSERVED.
    PASS_EXPECTED_DETECTION / PASS_EXPECTED_CRASH are M06-specific: the model
            oracle expects a detected exception, not a data value.
    """
    row = _pick_golden(golden_rows, context)
    # W10S store variant: the oracle is the workload's own redirect/fault
    # signature, not a read sentinel.
    if row is not None and ("m08_redirect_signature" in row or
                            "m06_write_fault_signature" in row):
        sig8 = _eint(row, "m08_redirect_signature", 0)
        sig6 = _eint(row, "m06_write_fault_signature", 0)
        fault = _eint(row, "store_fault", 0)
        ev = {
            "context": row.get("ctx", context),
            "line": row.get("_line", ""),
            "target_observed": _hexval(row, "target_observed"),
            "neighbor_alias_observed": _hexval(row,
                                               "neighbor_alias_observed"),
            "target_before": _hexval(row, "target_before"),
            "neighbor_before": _hexval(row, "neighbor_before"),
            "store_fault": fault,
            "m08_redirect_signature": sig8,
            "m06_write_fault_signature": sig6,
            "workload_result": row.get("result", ""),
            "basis": "W10S store-redirect / write-fault signature",
        }
        if model == "M08" and sig8 == 1:
            return "FAIL", ev
        if model == "M06" and (fault != 0 or sig6 == 1):
            return ("PASS_EXPECTED_CRASH" if fault != 0
                    else "PASS_EXPECTED_DETECTION"), ev
        if model == "M08":
            return "PASS", ev
        return ("PASS_EXPECTED_DETECTION"
                if terminal_state == "DETECTED_CONTAINED" else "PASS"), ev
    if row is None:
        if model == "M06":
            if terminal_state == "DETECTED_CONTAINED":
                return "PASS_EXPECTED_DETECTION", {
                    "basis": "translation fault detected/contained; no data "
                             "oracle line required"}
            if terminal_state == "CRASH":
                return "PASS_EXPECTED_CRASH", {
                    "basis": "guest crash is an expected M06 terminal"}
        return "NOT_OBSERVED", {"basis": "no golden output line for context"}

    result = row.get("result", "").upper()
    observed = _hexval(row, "observed")
    golden = None
    wrong = None
    if model == "M01":
        golden = _hexval(row, "new_marker")
        wrong = _hexval(row, "old_marker")
        label = "W9 PA2 marker vs PA1 stale marker"
    elif model in ("M02", "M06", "M08"):
        golden = _hexval(row, "sentinel")
        wrong = _hexval(row, "neighbor_sentinel")
        label = "W10 target sentinel vs neighbor sentinel"
    elif model == "M03":
        golden = _hexval(row, "marker_b")
        wrong = _hexval(row, "marker_a")
        label = "W11 process-B marker vs process-A marker"
    elif model in ("M04", "M05"):
        golden = _hexval(row, "sentinel")
        wrong = _hexval(row, "decoy_sentinel")
        label = "target sentinel vs decoy sentinel"
    elif model == "M07":
        golden = None
        wrong = None
        label = "W14 permission guard (shared_changed / injected_success)"
    else:
        label = "generic result"

    evidence = {
        "context": row.get("ctx", context),
        "line": row.get("_line", ""),
        "observed": observed,
        "golden": golden,
        "wrong": wrong,
        "workload_result": result,
        "basis": label,
    }

    if model == "M06":
        # M06 is an exception model.  A surviving workload reading the
        # correct sentinel is a masked/contained observation; a missing line
        # is handled above by the trace terminal.
        if terminal_state == "DETECTED_CONTAINED":
            return "PASS_EXPECTED_DETECTION", evidence
        if terminal_state == "CRASH":
            return "PASS_EXPECTED_CRASH", evidence
        if result == "PASS":
            return "PASS", evidence
        return "NOT_OBSERVED", evidence

    if model == "M07":
        injected = _eint(row, "injected_success", -1)
        changed = _eint(row, "shared_changed", -1)
        evidence.update({"injected_success": injected,
                         "shared_changed": changed})
        if (injected == 1 or changed == 1) and proof:
            return "FAIL", evidence
        if result == "PASS":
            return "PASS", evidence
        return "NOT_OBSERVED", evidence

    if observed is not None and golden is not None and observed == golden:
        return "PASS", evidence
    if observed is not None and wrong is not None and observed == wrong:
        return ("FAIL" if proof else "NOT_OBSERVED"), evidence
    if result == "PASS":
        return "PASS", evidence
    if result == "FAIL":
        return ("FAIL" if proof else "NOT_OBSERVED"), evidence
    return "NOT_OBSERVED", evidence


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_control_oracle(model, workload, context, control_run,
                            golden_rows):
    """Compare the faulted observation against an independent no-fault run.

    A control path may be a run directory or a golden/observed file.  The
    returned `diff` is the only meaningful SDC basis; the faulted run's own
    `observed_output.txt` is never used as its own control.
    """
    if not control_run:
        return {"present": False, "basis": "no independent control supplied"}
    path = control_run
    if os.path.isdir(path):
        for rel in ("Run_Log/observed_output.txt",
                    "Run_Log/golden_output.txt",
                    "observed_output.txt", "golden_output.txt"):
            cand = os.path.join(path, rel)
            if os.path.isfile(cand):
                path = cand
                break
    if not os.path.isfile(path):
        return {"present": False,
                "basis": "control path not found: %s" % control_run}
    rows = parse_golden(path)
    row = _pick_golden(rows, context)
    if row is None:
        return {"present": False,
                "basis": "control has no %s line for %s" % (workload, context)}
    fault_row = _pick_golden(golden_rows, context)
    ctrl_obs = _hexval(row, "observed")
    if ctrl_obs is None:
        ctrl_obs = _hexval(row, "target_observed")
    fault_obs = None
    if fault_row:
        fault_obs = _hexval(fault_row, "observed")
        if fault_obs is None:
            fault_obs = _hexval(fault_row, "target_observed")
    sentinel = _hexval(row, "sentinel")
    if sentinel is None:
        sentinel = _hexval(row, "target_before")
    # None means "not comparable"; only a real equality is a contradiction.
    diff = None
    if ctrl_obs is not None and fault_obs is not None:
        diff = ctrl_obs != fault_obs
    return {
        "present": True,
        "path": path,
        "sha256": _sha256_file(path),
        "control_observed": ctrl_obs,
        "faulted_observed": fault_obs,
        "expected_sentinel": sentinel,
        "diff": diff,
        "line": row.get("_line", ""),
        "basis": ("faulted observation differs from the independent control"
                  if diff else
                  "faulted observation equals the independent control"),
    }


def evaluate_run(events, by_id, parse_skipped, model, workload, context,
                 target_va, target_mode, run_id, golden_path, terminal_path,
                 manifest, trace_error="", control_run=None):
    integrity = record_integrity(events, by_id)
    scoped, scope_basis, scope_ambiguous = scope_events(
        events, model, workload, context, target_va)
    by_scoped = {e["event_id"]: e for e in scoped}
    fid, activation = select_fault(scoped, model)
    activation_id = activation["event_id"] if activation else 0
    activation_kind = _kind(activation) if activation else ""
    consumption, consumption_basis = select_consumption(
        scoped, by_scoped, model, fid, activation)
    consumption_id = consumption["event_id"] if consumption else 0
    consumption_kind = _kind(consumption) if consumption else ""

    fault_evs = _fault_events(scoped, fid) if fid != "0" else []
    observed = {_kind(e) for e in fault_evs}

    # M06 exception association: the architecture fault may carry ptag 0 (the
    # legacy address registry owns a different id).  Only same-VA, same-seq,
    # after-activation events are associated, and only as terminal evidence.
    associated = []
    if model == "M06" and activation is not None:
        va = activation.get("va", "")
        seq = activation.get("dyn_inst_seq", "")
        for ev in scoped:
            if ev["event_id"] <= activation_id:
                continue
            if _kind(ev) not in (EXCEPTION_KINDS | CONTAIN_KINDS |
                                 {"commit", "squash", "squash_discarded"}):
                continue
            if va and ev.get("va", "") == va or \
                    (seq and ev.get("dyn_inst_seq", "") == seq):
                associated.append(ev)
        observed |= {_kind(e) for e in associated}
    if model == "M07" and activation is not None:
        # mmuNotePermission observes the REAL deny decision BEFORE M07
        # activates, so that permission_eval event carries fault_id=0.  It is
        # the same translation txn as the activation; associate it explicitly
        # by translation_id (never by tick proximity).
        tid = activation.get("translation_id", "")
        seq = activation.get("dyn_inst_seq", "")
        va = activation.get("va", "")
        for ev in scoped:
            if _kind(ev) != "permission_eval":
                continue
            same_txn = (tid and ev.get("translation_id", "") == tid) or \
                (seq and ev.get("dyn_inst_seq", "") == seq and
                 (not va or ev.get("va", "") == va))
            if same_txn:
                associated.append(ev)
        observed |= {_kind(e) for e in associated}

    # M03/M04 Execute: the ITLB fetch carries no Request dyn-inst sequence,
    # so the fault-tagged lookup row may not exist even though the fetch DID
    # consume the substituted entry.  The injected PA is known from the
    # activation (old_pa -> new_pa); a post-activation translation_result or
    # lsu_request for the same VA carrying exactly that PA is the IFU
    # consumption witness.  Identity (VA + injected PA), never time order.
    ifu_carrier_ids = []
    if model in ("M03", "M04") and activation is not None and \
            (target_mode or "") == "Execute":
        va = activation.get("va", "")
        new_pa = _eint(activation, "new_pa", -1, hexa=True)
        for ev in scoped:
            if ev["event_id"] <= activation_id:
                continue
            if _kind(ev) not in ("translation_result", "lsu_request"):
                continue
            if va and ev.get("va", "") != va:
                continue
            raw_pa = ev.get("pa", "")
            try:
                ev_pa = int(raw_pa, 16) if raw_pa else -1
            except ValueError:
                ev_pa = -1
            if new_pa >= 0 and ev_pa == new_pa:
                associated.append(ev)
                ifu_carrier_ids.append(ev["event_id"])
        observed |= {_kind(e) for e in associated}

    # ---- v3/v4 chain evaluation for M01/M02 ------------------------------
    v3_result = None
    lineage_rows = []
    v3_completeness = None
    v3_missing_kinds = []
    v3_missing_edges = []
    if model in ("M01", "M02") and workload in ("W9", "W10"):
        if target_va is not None:
            va_points = [target_va]
        elif workload == "W9":
            va_points = [0x4000000000]
        elif context in v3.W10_VA_CONTEXT:
            va_points = [v3.W10_VA_CONTEXT[context]]
        else:
            va_points = sorted(v3.W10_VA_CONTEXT)
        va_args = [hex(v) for v in va_points]
        args = SimpleNamespace(input="", workload=workload, model=model,
                               run_id=run_id, va=va_args, parse_skipped=0)
        v3_result, chains = v3.evaluate(scoped, by_scoped, args)
        lineage, lineage_rows = v4.audit_lineage(scoped)
        if model == "M02":
            req = list(v3.MODEL_REQUIRED[("W10", "M02")])
            if "fault_entry_consume" not in req:
                v3.MODEL_REQUIRED[("W10", "M02")] = req + [
                    "fault_entry_consume"]
            v4.refine_m02(v3_result, scoped, lineage, lineage_rows)
        fc = v3_result.get("fault_chain_completeness", {}).get(str(fid))
        if fc:
            v3_completeness = fc.get("completeness")
            v3_missing_kinds = list(fc.get("missing_kinds") or [])
            v3_missing_edges = list(fc.get("missing_edges") or [])

    proof, proof_basis, contradictions = prove_wrong_value(
        model, scoped, activation, consumption, lineage_rows, v3_result)

    # ---- terminal --------------------------------------------------------
    # An architectural exception/containment is the terminal even if a later
    # replay commits; a squash is terminal only when nothing committed.
    terminal = "none"
    if observed & EXCEPTION_KINDS:
        terminal = "exception"
    elif observed & CONTAIN_KINDS:
        terminal = "contained"
    elif observed & SQUASH_KINDS and "commit" not in observed:
        terminal = "squash"
    elif "commit" in observed:
        terminal = "commit"
    elif observed & SQUASH_KINDS:
        terminal = "squash"

    # ---- strict identity chains (the five instruction-side contexts) ------
    spec_mode = target_mode or ""
    strict = None
    strict_guards = []
    if (model, context) in STRICT_CONTEXTS:
        oracle_text = ""
        if golden_path and os.path.isfile(golden_path):
            oracle_text = open(golden_path, "r", errors="replace").read()
        strict = evidence_chain.evaluate(
            model, context, events, target_va, spec_mode, oracle_text)

    if strict is not None:
        required = list(strict.get("required_kinds") or [])
        missing_kinds = list(strict.get("missing_kinds") or [])
        missing_edges = list(strict.get("missing_edges") or [])
        strict_guards = list(strict.get("guards") or [])
        # The strict chain names the real consuming request.  Never fall back
        # to the activation event as a consumption witness.
        sc = strict.get("consumption") or {}
        cid = sc.get("event_id")
        consumption = next((e for e in events if e["event_id"] == cid), None)
        consumption_id = cid or 0
        consumption_kind = _kind(consumption) if consumption else ""
        consumption_basis = "strict_identity_chain"
        if strict.get("consumption_basis"):
            consumption_basis += ":" + strict["consumption_basis"]
        live_evs = fault_evs + [e for e in associated if e not in fault_evs]
    else:
        required = _path_required(model, observed, spec_mode, terminal)
        if not required:
            required = evidence_chain.required_kinds(
                model, context, spec_mode, observed, workload)
        missing_kinds = [k for k in required if k not in observed]
        # M04/M05 consumption is an either/or witness.
        if model == "M04" and "tlb_lookup_hit" in missing_kinds and \
                ({"fault_entry_consume", "fault_entry_reuse"} & observed):
            missing_kinds.remove("tlb_lookup_hit")
        if model == "M05" and "tlb_lookup_hit" in missing_kinds and \
                ({"fault_entry_consume", "fault_entry_reuse"} & observed):
            missing_kinds.remove("tlb_lookup_hit")
        # M03/M04 Execute: an IFU fetch that returned the injected PA is the
        # consumption witness even when the lookup row is untagged.
        if model in ("M03", "M04") and ifu_carrier_ids and \
                "tlb_lookup_hit" in missing_kinds:
            missing_kinds.remove("tlb_lookup_hit")
        # M07: the activation row records the real pre/post grant decision
        # when the separate permission_eval row is absent.
        m07_activation_witness = bool(
            model == "M07" and activation is not None and
            activation.get("permission_before") == "false" and
            activation.get("permission_after") == "true")
        if m07_activation_witness and "permission_eval" in missing_kinds:
            missing_kinds.remove("permission_eval")

        live_evs = fault_evs + [e for e in associated if e not in fault_evs]
        missing_edges = _edge_checks(live_evs, by_id, required, model, terminal)
        if model in ("M01", "M02"):
            missing_edges = v3_missing_edges
            missing_kinds = v3_missing_kinds

    missing = ["missing_kind:%s" % k for k in sorted(set(missing_kinds))]
    missing += missing_edges
    missing += ["identity:%s" % g for g in sorted(set(strict_guards))]
    missing += ["lineage:%s" % c for c in sorted(set(contradictions))]
    missing = sorted(set(missing))

    # ---- status ----------------------------------------------------------
    unactivated = [e for e in scoped
                   if _kind(e) == "mmu_fault_unactivated"]
    if activation is None:
        if unactivated:
            reason = unactivated[0].get("fault_reason", "")
            if "no_eligible" in reason:
                activation_status = "NO_ELIGIBLE_EVENT"
            else:
                activation_status = "NOT_ACTIVATED"
        else:
            activation_status = "NOT_OBSERVED"
    else:
        activation_status = "ACTIVATED"

    if consumption is not None:
        consumption_status = "CONSUMED"
        # M05: a clean complete hit / clean pte_read is not consumption of
        # the corrupted partial entry.  The proof carries the real partial
        # hit on the substituted base.
        if model == "M05" and not proof:
            consumption_status = "NOT_CONSUMED"
    elif activation_status == "ACTIVATED":
        summary = next((e for e in scoped
                        if _kind(e) == "mmu_fault_summary"), None)
        if summary is not None and summary.get("consumed") == "0":
            consumption_status = "NOT_CONSUMED"
        elif terminal != "none":
            consumption_status = "NOT_CONSUMED"
        else:
            consumption_status = "NOT_OBSERVED"
    else:
        consumption_status = "NOT_OBSERVED"
    if strict is not None:
        consumption_status = "CONSUMED" if strict.get("ok") else \
            "NOT_CONSUMED"

    # Propagation means reaching architectural state.  A squash is a real
    # terminal for the trace but NOT architectural propagation.
    if activation_status == "ACTIVATED" and not missing and \
            terminal in ("commit", "exception", "contained"):
        propagation = "FULL"
    elif activation_status == "ACTIVATED" and (observed or associated):
        propagation = "PARTIAL"
    else:
        propagation = "NOT_OBSERVED"
    # M05: a clean complete hit/commit is not fault propagation.  FULL is
    # claimed only when the corrupted partial base was really consumed.
    if model == "M05" and not proof:
        propagation = "PARTIAL" if (observed or associated) else \
            "NOT_OBSERVED"

    golden_rows = parse_golden(golden_path)
    target_golden = _pick_golden(golden_rows, context)
    timed_out = bool(manifest.get("timed_out"))
    crash_text = ""
    if terminal_path and os.path.isfile(terminal_path):
        crash_text = open(terminal_path, "r", errors="replace").read()
    # Crash text is only attributed when the target context produced no
    # golden line of its own; otherwise a crash from another context in the
    # same guest log could be merged into this fault.
    crash_evidence = bool(
        target_golden is None and re.search(
            r"(Kernel panic|BUG:|Oops|Segmentation fault|SIGSEGV|"
            r"Unhandled fault|Unable to handle kernel|W14_FAULT)", crash_text))

    summary_evt = next((e for e in scoped
                        if _kind(e) == "mmu_fault_summary"), None) or {}
    m06_state_consumed = summary_evt.get("state_consumed")
    m06_result_prop = summary_evt.get("result_propagated")
    m06_exc_deliv = summary_evt.get("exception_delivered")

    # M06 containment is an ARCHITECTURAL claim: the hardware must have
    # generated the translation fault AND delivered it to an architectural
    # consumer.  Proof is either a real `exception_delivery` event, or the
    # C++ summary recording exception_delivered=1 together with
    # result_propagated=1 (the summary is emitted from the delivery hook).
    # A consumed descriptor whose fault result never reached a delivery point
    # -- e.g. a squash of the faulting instruction with no architectural
    # consumer -- is not containment and must not be reported as
    # DETECTED_CONTAINED.
    m06_exc_event = any(_kind(e) == "exception_delivery"
                        for e in live_evs)
    m06_delivery_proof = bool(m06_exc_event) or (
        m06_exc_deliv == "1" and m06_result_prop == "1")
    m06_consumed = (m06_state_consumed == "1" or
                    "fault_state_consumed" in observed)

    if timed_out:
        terminal_state = "HANG/TIMEOUT"
    elif activation_status in ("NOT_ACTIVATED", "NO_ELIGIBLE_EVENT"):
        terminal_state = activation_status
    elif model == "M06" and m06_consumed and m06_delivery_proof:
        # The Translation Fault was architecturally delivered; the wrong
        # state never committed.
        terminal_state = "DETECTED_CONTAINED"
    elif model == "M06" and m06_consumed and m06_result_prop == "1":
        # Fault generated from a consumed descriptor, but no architectural
        # delivery was observed.  A squash without an architectural consumer
        # is SQUASHED; otherwise the terminal is simply not in the trace.
        terminal_state = ("SQUASHED" if (observed & SQUASH_KINDS or
                                         terminal == "squash")
                          else "TRACE_INCOMPLETE")
    elif model == "M06" and m06_consumed and m06_result_prop == "0":
        # The descriptor was consumed by decode but the fault never reached
        # the exception path (walk replayed).  Not a terminal.
        terminal_state = "TRACE_INCOMPLETE"
    elif terminal == "exception":
        exc = next((e for e in live_evs if _kind(e) in EXCEPTION_KINDS), None)
        contained = False
        if exc is not None:
            contained = (exc.get("contained") == "1" or
                         exc.get("delivered") == "1" or
                         exc.get("exception_delivered") == "1")
        terminal_state = "DETECTED_CONTAINED" if contained else "CRASH"
    elif terminal == "contained":
        terminal_state = "DETECTED_CONTAINED"
    elif terminal == "squash":
        terminal_state = "SQUASHED"
    elif terminal == "commit":
        # Filled after oracle evaluation.
        terminal_state = "COMMITTED_PENDING_ORACLE"
    elif crash_evidence:
        terminal_state = "CRASH"
    else:
        terminal_state = "TRACE_INCOMPLETE"

    oracle_result, oracle_evidence = evaluate_oracle(
        model, workload, context, golden_rows, proof, terminal_state)
    if strict is not None:
        # The strict identity chain is the propagation witness.  FULL requires
        # both the joined chain and an oracle diff; a chain that is not
        # complete can never be FULL.
        if strict.get("ok") and oracle_result == "FAIL":
            propagation = "FULL"
        elif strict.get("ok"):
            propagation = "PARTIAL"
        else:
            propagation = ("PARTIAL" if (observed or associated)
                           else "NOT_OBSERVED")
    if str(fid) == "0" and activation_status in ("NOT_ACTIVATED",
                                                 "NO_ELIGIBLE_EVENT"):
        # No injected fault exists, so the golden comparison is moot.  Do not
        # report PASS: that would be mistaken for a passed injection sample.
        oracle_result = "NOT_OBSERVED"
        oracle_evidence = dict(oracle_evidence)
        oracle_evidence["basis"] = ("no injected fault activated; oracle "
                                    "comparison not applicable")

    # Final-consumer override: a persistent entry fault may reach a committed
    # instruction whose row is not fault-tagged after a refill/lineage change.
    # If the committed access carried the injected PA and the oracle differs,
    # the terminal is SDC, not SQUASHED (the origin squash is not terminal).
    if model in ("M04", "M05", "M08") and \
            terminal_state in ("SQUASHED", "TRACE_INCOMPLETE") and \
            oracle_result == "FAIL" and proof:
        terminal_state = "SDC"
        propagation = "FULL"
    # M07 execute: the IFU consumed the inverted grant; a real JIT-code
    # observation (oracle diff) is the architectural corruption.
    if model == "M07" and activation_status == "ACTIVATED" and \
            oracle_result == "FAIL" and proof:
        terminal_state = "SDC"
        propagation = "FULL"
    # M03 execute: the ITLB false hit executed the foreign code page.
    if model == "M03" and (target_mode or "") == "Execute" and \
            activation_status == "ACTIVATED" and oracle_result == "FAIL" and \
            proof:
        terminal_state = "SDC"
        propagation = "FULL"

    if terminal_state == "COMMITTED_PENDING_ORACLE":
        if oracle_result == "FAIL" and proof:
            terminal_state = "SDC"
        elif oracle_result == "FAIL":
            # Oracle diff without a causal trace proof can never be SDC.
            terminal_state = "TRACE_INCOMPLETE"
        elif oracle_result in ("PASS", "PASS_EXPECTED_DETECTION"):
            terminal_state = ("ACTIVATED_MASKED" if consumption is not None
                              else "TRACE_INCOMPLETE")
        elif proof:
            terminal_state = "ARCH_STATE_CORRUPTION"
        else:
            terminal_state = "TRACE_INCOMPLETE"
    if terminal_state == "COMMITTED_PENDING_ORACLE":
        terminal_state = "TRACE_INCOMPLETE"

    # ---- trace completeness ---------------------------------------------
    if v3_completeness in ("COMPLETE", "PARTIAL", "INCOMPLETE"):
        trace_completeness = v3_completeness
        if missing_kinds or missing_edges:
            trace_completeness = "PARTIAL"
    elif activation_status != "ACTIVATED":
        trace_completeness = "NOT_OBSERVED"
    # NOTE: the former blanket "Execute => COMPLETE" shortcut was removed:
    # it hid real missing kinds (e.g. M03 R05 had no tlb_lookup_hit and no
    # consumer/commit yet still reported COMPLETE).  Execute runs now fall
    # through to the same real-evidence rules as every other mode.
    elif model == "M06" and activation_status == "ACTIVATED" and \
            m06_state_consumed == "1":
        trace_completeness = "COMPLETE"
    elif not missing and terminal in ("commit", "squash", "exception",
                                      "contained"):
        # Trace completeness is about knowing what happened, not about the
        # fault reaching architectural state (that is PropagationStatus).
        trace_completeness = "COMPLETE"
    elif not missing and propagation == "FULL":
        trace_completeness = "COMPLETE"
    elif observed or associated:
        trace_completeness = "PARTIAL"
    else:
        trace_completeness = "INCOMPLETE"
    if strict is not None:
        # Completeness is defined by the real, identity-joined event set of
        # this context; a guard failure is never COMPLETE.
        if strict.get("ok") and not missing:
            trace_completeness = "COMPLETE"
        elif strict.get("ok"):
            trace_completeness = "PARTIAL"
        else:
            trace_completeness = "TRACE_INCOMPLETE"
    if integrity["status"] == "FAIL":
        # A broken parent graph can never be claimed COMPLETE.
        if trace_completeness == "COMPLETE":
            trace_completeness = "TRACE_INCOMPLETE"
        missing = sorted(set(missing + ["record_integrity:%s" % e
                                        for e in integrity["errors"][:5]]))
    if trace_error:
        trace_completeness = "TRACE_INCOMPLETE"
        missing = sorted(set(missing + ["trace_read_error:%s" % trace_error]))

    # Independent control oracle (optional CLI input).  The faulted run's own
    # output is NOT a golden; the comparison is only meaningful against a
    # separately executed no-fault run.
    control = evaluate_control_oracle(model, workload, context,
                                      control_run, golden_rows)
    if control.get("present") and control.get("diff") is False and \
            oracle_result == "FAIL":
        oracle_result = "CONTRADICTION"
        details_contradiction = (
            "observed value equals the independent control golden while the "
            "trace claims SDC")
    else:
        details_contradiction = ""

    last_evt = scoped[-1] if scoped else {}
    deadline_evidence = {
        "last_event_id": last_evt.get("event_id", ""),
        "last_event_kind": _kind(last_evt),
        "last_tick": last_evt.get("tick", ""),
        "timed_out": timed_out,
        "deadline_sec": manifest.get("timeout_sec", ""),
    }

    expected_terminals = EXPECTED_TERMINALS.get(model, set())
    details = {
        "scope_basis": scope_basis,
        "scope_event_count": len(scoped),
        "scope_ambiguous_multi_fault": scope_ambiguous,
        "expected_terminals": sorted(expected_terminals),
        "terminal_expected_by_model":
            terminal_state in expected_terminals
            if expected_terminals else None,
        "activation_kind": activation_kind,
        "consumption_kind": consumption_kind,
        "consumption_basis": consumption_basis,
        "observed_kinds": sorted(observed),
        "required_kinds": required,
        "missing_kinds": sorted(set(missing_kinds)),
        "associated_event_ids": [e["event_id"] for e in associated],
        "wrong_value_proven": proof,
        "wrong_value_basis": proof_basis,
        "contradictions": sorted(set(contradictions)),
        "record_integrity": integrity,
        "v3_v4_result": {
            "run_trace_completeness":
                (v3_result or {}).get("run_trace_completeness"),
            "fault_chain_completeness":
                (v3_result or {}).get("fault_chain_completeness", {}).get(
                    str(fid)),
            "lineage": (v3_result or {}).get("phase2_2_lineage_audit"),
        } if v3_result else None,
        "oracle": oracle_evidence,
        "control_oracle": control,
        "control_oracle_contradiction": details_contradiction,
        "deadline_evidence": deadline_evidence,
        "m06_separation": {
            "state_consumed": m06_state_consumed,
            "result_propagated": m06_result_prop,
            "exception_delivered": m06_exc_deliv,
        } if model == "M06" else None,
        "ifu_lookup_identity_join": ifu_carrier_ids,
        "strict_evidence_chain": strict,
        "fault_activation_basis":
            (strict or {}).get("activation_basis") or activation_kind,
        "fault_consumption_basis": consumption_basis,
        "terminal_evidence_basis":
            ("STRICT_IDENTITY_CHAIN_PLUS_GUEST_ORACLE"
             if strict is not None and strict.get("ok")
             else "TRACE_PLUS_GUEST_ORACLE"),
        "terminal_text_crash_evidence": crash_evidence,
        "timed_out": timed_out,
    }
    return {
        "run_id": run_id,
        "sample_run_id": manifest.get("sample_run_id", ""),
        "model": model,
        "workload": workload,
        "context": context,
        "target_va": target_va,
        "target_mode": target_mode,
        "fault_id": str(fid),
        "activation_event_id": activation_id,
        "consumption_event_id": consumption_id,
        "ActivationStatus": activation_status,
        "FaultConsumptionStatus": consumption_status,
        "PropagationStatus": propagation,
        "TraceCompleteness": trace_completeness,
        # Explicit separation required by the 2026-11-12 review:
        # activation != consumption != propagation completeness != terminal.
        "FaultActivated": activation_status,
        "FaultStateConsumed": consumption_status,
        "PropagationComplete": propagation,
        "MissingCausalEdges": missing,
        "TerminalState": terminal_state,
        "OracleResult": oracle_result,
        "OracleEvidence": oracle_evidence,
        "RecordIntegrity": integrity["status"],
        "Details": details,
    }


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


def write_md(path, result, inputs):
    lines = []
    lines.append("# Formal MMU Verdict: %s\n" % result.get("run_id", "?"))
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    for key in ("sample_run_id", "model", "workload", "context",
                "target_va", "target_mode", "fault_id",
                "activation_event_id", "consumption_event_id",
                "ActivationStatus", "FaultConsumptionStatus",
                "PropagationStatus", "TraceCompleteness", "TerminalState",
                "OracleResult", "RecordIntegrity"):
        lines.append("| %s | %s |" % (key, result.get(key, "")))
    lines.append("")
    lines.append("## Missing causal edges / kinds\n")
    if result["MissingCausalEdges"]:
        for item in result["MissingCausalEdges"]:
            lines.append("- `%s`" % item)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Evidence\n")
    lines.append("- trace: `%s`" % (inputs.get("trace") or "-"))
    lines.append("- golden: `%s`" % (inputs.get("golden") or "-"))
    lines.append("- terminal: `%s`" % (inputs.get("terminal") or "-"))
    lines.append("- wrong-value proof: %s" %
                 (result["Details"].get("wrong_value_basis") or "-"))
    lines.append("- terminal expected by model: %s (allowed: %s)" % (
        result["Details"].get("terminal_expected_by_model"),
        ", ".join(result["Details"].get("expected_terminals") or [])))
    if result["Details"].get("contradictions"):
        lines.append("- contradictions: %s" %
                     result["Details"]["contradictions"])
    lines.append("")
    lines.append("## Oracle evidence\n")
    lines.append("```json")
    lines.append(json.dumps(result.get("OracleEvidence", {}),
                            indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("## Interpretation rules\n")
    lines.append("- COMPLETE requires all model-required kinds, real "
                 "ParentEventID edges, record integrity and a terminal.")
    lines.append("- Unknown facts are NOT_OBSERVED/PARTIAL; no rule is "
                 "deleted and unrelated events are never merged.")
    if result["model"] == "M06":
        lines.append("- M06 is an exception model: no LSU request or normal "
                     "commit is required; a Translation Fault is the "
                     "expected terminal.")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Terminal-aware formal validator for MMU M01-M08")
    ap.add_argument("--run-dir")
    ap.add_argument("--input", help="prop_evt.txt[.gz]")
    ap.add_argument("--golden", help="faulted observation file "
                                     "(observed_output.txt)")
    ap.add_argument("--control-run",
                    help="independent no-fault control run dir or golden "
                         "file; required to substantiate an SDC oracle diff")
    ap.add_argument("--terminal", help="board.terminal")
    ap.add_argument("--manifest")
    ap.add_argument("--model", choices=sorted(ACTIVATION_KINDS))
    ap.add_argument("--workload")
    ap.add_argument("--context", default="")
    ap.add_argument("--target-va", default=None)
    ap.add_argument("--target-mode", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--report-json")
    ap.add_argument("--report-md")
    args = ap.parse_args(argv)

    paths = find_run_paths(args.run_dir) if args.run_dir else {}
    trace = args.input or paths.get("trace")
    if not trace or not os.path.isfile(trace):
        print("VALIDATOR ERROR: no PROP-EVT trace (use --input or --run-dir)",
              file=sys.stderr)
        return 2
    manifest = load_manifest(args.manifest or paths.get("manifest"))
    model = args.model or _manifest_value(manifest, "model")
    workload = args.workload or _manifest_value(manifest, "workload")
    context = args.context or _manifest_value(manifest, "context", default="")
    if not model:
        print("VALIDATOR ERROR: --model is required", file=sys.stderr)
        return 2
    if model not in ACTIVATION_KINDS:
        print("VALIDATOR ERROR: unsupported model %s" % model,
              file=sys.stderr)
        return 2
    target_va = args.target_va
    if target_va is None:
        target_va = _manifest_value(manifest, "target_va")
    if isinstance(target_va, str) and target_va:
        target_va = int(target_va, 0)
    target_mode = args.target_mode or _manifest_value(
        manifest, "target_mode", default="")
    run_id = args.run_id or _manifest_value(
        manifest, "run_id", "sample_run_id", default="")
    golden = args.golden or paths.get("golden")
    terminal = args.terminal or paths.get("terminal")

    events, bad, trace_error = load_events_tolerant(trace)
    by_id = {e["event_id"]: e for e in events}
    result = evaluate_run(
        events, by_id, bad, model, workload or "", context or "",
        target_va, target_mode or "", run_id, golden, terminal, manifest,
        trace_error=trace_error, control_run=args.control_run)
    result["trace"] = trace
    result["golden_output"] = golden
    result["terminal"] = terminal
    result["parse_skipped"] = bad
    result["trace_read_error"] = trace_error
    result["event_count"] = len(events)
    result["validator"] = "mmu_formal_validate"

    inputs = {"trace": trace, "golden": golden, "terminal": terminal}
    if args.report_json:
        with open(args.report_json, "w") as fh:
            json.dump(result, fh, indent=2, sort_keys=True, default=str)
    if args.report_md:
        write_md(args.report_md, result, inputs)

    print(json.dumps({k: result[k] for k in (
        "run_id", "model", "workload", "context", "fault_id",
        "activation_event_id", "consumption_event_id", "ActivationStatus",
        "FaultConsumptionStatus", "PropagationStatus", "TraceCompleteness",
        "TerminalState", "OracleResult", "MissingCausalEdges",
        "RecordIntegrity")}, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
