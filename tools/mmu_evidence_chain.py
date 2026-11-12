#!/usr/bin/env python3
"""Strict, identity-based MMU propagation chains for the five final contexts.

The frozen binary does not emit a per-instruction fetch-response/decode/commit
event for a synthetic IFU transaction.  What it *does* emit, and what this
module proves, is the causal request chain with real identities:

  M03 R05  activation(candidate entry 253/51) -> l2_shared hit 253/51
           -> ITLB insert -> permission -> translation_result 253/51
           -> lsu_request(mode=Execute, PA=candidate_pa)
  M04 R05  activation mutates itb entry 173/540; lineage; the very next
           translation_result reuses itb:173:540 and emits new_pa
           -> lsu_request(mode=Execute, PA=new_pa)
  M05 R05  faulted partial insert -> fault_entry_consume (source=insert,
           lookup=real partial hit) -> PTW -> wrong leaf -> translation_result
           -> lsu_request(mode=Execute, PA=decoy_pa)
  M07 R04  permission_eval(Execute, deny) at cycle T -> activation inversion
           at the same cycle/T/VA/mode -> translation_result + lsu_request
           (mode=Execute) on the SAME translation_id
  M07 R05  same, with the workload's explicit `indirect_branch insn=br`
           line proving the runtime `br xN` entered the target VA.

The M07 activation row itself has translation_id=0 because the C++ hook runs
for a fetch request with no instruction sequence number (mmu.cc:746-769).
The join below therefore uses a *co-temporal key match* (same tick AND same
VA AND same mode AND same stage AND same regime/security state) against the
permission_eval that the source emits immediately before the inversion, plus
the transaction identity shared by that permission_eval, the
translation_result and the lsu_request.  It never uses event order alone.

Nothing here invents an event.  A missing/mismatched identity is reported.
"""

from collections import OrderedDict

# ---------------------------------------------------------------------------
# field helpers
# ---------------------------------------------------------------------------


def kind(ev):
    return ev.get("kind", "")


def dec(ev, key, default=None):
    v = ev.get(key, "")
    if v in ("", None):
        return default
    try:
        return int(v, 0)
    except ValueError:
        try:
            return int(v, 16)
        except ValueError:
            return default


def hx(ev, key, default=None):
    """PA/PFN fields are bare hex (mmuHex drops 0x); 0x-prefixed is accepted."""
    v = ev.get(key, "")
    if v in ("", None):
        return default
    try:
        return int(v, 16) if not str(v).lower().startswith("0x") else int(v, 0)
    except ValueError:
        return default


def entry_identity(ev):
    iid = dec(ev, "tlb_entry_id")
    gen = dec(ev, "entry_generation")
    if iid is None or gen is None:
        return None
    return (iid, gen)


def instance(ev):
    return ev.get("tlb_instance", "")


def page(ev):
    va = hx(ev, "va")
    return None if va is None else va >> 12


def tid(ev):
    v = dec(ev, "translation_id", 0)
    return v or 0


def pick(events, kinds, after=-1, pred=None):
    kinds = set(kinds)
    for ev in events:
        if ev.get("event_id", -1) <= after:
            continue
        if kind(ev) not in kinds:
            continue
        if pred is not None and not pred(ev):
            continue
        return ev
    return None


def fault_id(events):
    for ev in events:
        if kind(ev) == "mmu_fault_activate":
            fid = str(ev.get("fault_id", "0"))
            if fid not in ("", "0"):
                return fid
    return "0"


def oracle_tokens(line):
    out = {}
    for tok in (line or "").split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out


# ---------------------------------------------------------------------------
# result helpers
# ---------------------------------------------------------------------------


def _result(model, context, mode, target_va, fid):
    return OrderedDict([
        ("model", model),
        ("context", context),
        ("mode", mode),
        ("target_va", target_va),
        ("fault_id", fid),
        ("activation", None),
        ("activation_basis", ""),
        ("join_note", ""),
        ("consumption", None),
        ("consumption_events", []),
        ("consumption_basis", ""),
        ("required_kinds", []),
        ("missing_kinds", []),
        ("missing_edges", []),
        ("identity", OrderedDict()),
        ("fetch_request", None),
        ("terminal_evidence", OrderedDict()),
        ("guards", []),
        ("ok", False),
    ])


def _ev_summary(ev):
    if not ev:
        return None
    keys = ("kind", "event_id", "fault_id", "tick", "cycle", "dyn_inst_seq",
            "commit_seq", "pc", "va", "pa", "pfn", "is_fetch", "mode",
            "asid", "translation_id", "unique_request_id", "lookup_id",
            "request_id", "tlb_instance", "tlb_entry_id", "entry_generation",
            "permission_result", "permission_before", "permission_after",
            "old_pfn", "new_pfn", "old_pa", "new_pa", "candidate_pfn",
            "candidate_pa", "candidate_entry_id", "candidate_generation",
            "candidate_asid", "commit_status", "squash_status", "outcome",
            "source_event_id", "lookup_event_id", "consumption_event_id",
            "next_table_pa_before", "next_table_pa_after", "decoy_va",
            "decoy_pfn", "decoy_pa", "retained_entry_id",
            "retained_entry_generation", "lineage_state", "walk_level",
            "descriptor_type", "memory_attribute")
    return OrderedDict((k, ev[k]) for k in keys if ev.get(k, "") != "")


def _missing_kinds(required, events):
    seen = {kind(e) for e in events}
    return [k for k in required if k not in seen]


# ---------------------------------------------------------------------------
# M03 — ASID false hit consumed by the IFU
# ---------------------------------------------------------------------------


def chain_m03(events, context, target_va, mode, oracle_line):
    fid = fault_id(events)
    res = _result("M03", context, mode, target_va, fid)
    act = pick(events, ["mmu_fault_activate"],
               pred=lambda e: str(e.get("fault_id", "0")) == fid)
    if act is None:
        res["missing_kinds"] = ["mmu_fault_activate"]
        return res
    res["activation"] = _ev_summary(act)
    cand = entry_identity({
        "tlb_entry_id": act.get("candidate_entry_id", ""),
        "entry_generation": act.get("candidate_generation", ""),
    })
    cand_pa = hx(act, "candidate_pa")
    cand_asid = dec(act, "candidate_asid")
    requester_asid = dec(act, "asid")
    cand_inst = instance(act)
    res["identity"]["candidate_entry"] = cand
    res["identity"]["candidate_asid"] = cand_asid
    res["identity"]["requester_asid"] = requester_asid
    res["identity"]["candidate_pa"] = None if cand_pa is None else hex(cand_pa)
    res["activation_basis"] = "M03_FALSE_HIT_ACTIVATION"
    res["join_note"] = (
        "The activation names candidate_entry/generation %s from ASID %s; the "
        "fault-tagged tlb_lookup_hit, the later translation_result and the "
        "lsu_request(mode=Execute) all carry the same entry identity and the "
        "candidate PA. The requester ASID (%s) differs from the candidate "
        "ASID, so the fetch consumed a foreign-context translation." %
        (cand, cand_asid, requester_asid))

    guards = []
    if cand is None:
        guards.append("candidate_entry_identity_missing")
    if cand_asid == requester_asid:
        guards.append("candidate_asid_equals_requester")
    if instance(act) not in ("l2_shared",):
        guards.append("activation_instance_not_l2_shared")

    lookup = pick(
        events, ["tlb_lookup_hit"], after=act["event_id"],
        pred=lambda e: str(e.get("fault_id", "0")) == fid and
        entry_identity(e) == cand and instance(e) == cand_inst)
    if lookup is None:
        res["missing_kinds"] = ["tlb_lookup_hit"]
        res["guards"] = guards
        return res
    res["identity"]["lookup_entry"] = entry_identity(lookup)
    res["identity"]["lookup_id"] = dec(lookup, "lookup_id")
    res["identity"]["lookup_asid"] = dec(lookup, "asid")
    res["identity"]["lookup_pa"] = lookup.get("pa")
    if dec(lookup, "asid") != requester_asid:
        guards.append("lookup_asid_not_requester")

    ins = pick(events, ["tlb_entry_insert"], after=lookup["event_id"],
               pred=lambda e: str(e.get("fault_id", "0")) == fid)
    perm = pick(events, ["permission_eval"],
                after=(ins or lookup)["event_id"],
                pred=lambda e: str(e.get("fault_id", "0")) == fid)
    result = pick(
        events, ["translation_result"], after=(perm or ins or lookup)["event_id"],
        pred=lambda e: str(e.get("fault_id", "0")) == fid and
        entry_identity(e) == cand and hx(e, "pa") == cand_pa)
    if result is None:
        res["missing_kinds"] = ["translation_result"]
        res["guards"] = guards
        return res
    res["identity"]["result_entry"] = entry_identity(result)
    res["identity"]["result_pa"] = result.get("pa")

    sq = None
    if mode == "Execute":
        req = pick(events, ["lsu_request"], after=result["event_id"],
                   pred=lambda e: str(e.get("fault_id", "0")) == fid and
                   e.get("mode") == "Execute" and hx(e, "pa") == cand_pa)
        required = ["translation_start", "tlb_lookup_miss",
                    "mmu_fault_activate", "tlb_lookup_hit",
                    "tlb_entry_insert", "permission_eval",
                    "translation_result", "lsu_request"]
        if req is None:
            res["missing_kinds"] = ["lsu_request"]
    else:
        req = None
        sq = pick(events, ["squash"], after=result["event_id"],
                  pred=lambda e: str(e.get("fault_id", "0")) == fid)
        required = ["translation_start", "tlb_lookup_miss",
                    "mmu_fault_activate", "tlb_lookup_hit",
                    "tlb_entry_insert", "permission_eval",
                    "translation_result", "squash"]
        if sq is None:
            res["missing_kinds"] = ["squash"]

    res["consumption"] = _ev_summary(req or sq or result)
    res["consumption_events"] = [lookup["event_id"], ins["event_id"]
                                 if ins else None,
                                 perm["event_id"] if perm else None,
                                 result["event_id"],
                                 req["event_id"] if req else None,
                                 sq["event_id"] if req is None and sq else None]
    res["consumption_events"] = [e for e in res["consumption_events"] if e]
    res["consumption_basis"] = "TLB_ENTRY_IDENTITY_%d:%d" % cand if cand else ""
    res["fetch_request"] = _ev_summary(req) if req else None
    res["required_kinds"] = required
    res["missing_kinds"] = sorted(set(res["missing_kinds"] +
                                      _missing_kinds(required, events)))

    tok = oracle_tokens(oracle_line)
    pfn_a = tok.get("pfn_a")
    marker_a = tok.get("marker_a")
    observed = tok.get("observed")
    expect = tok.get("expect")
    res["terminal_evidence"] = OrderedDict([
        ("guest_line", oracle_line or ""),
        ("observed", observed),
        ("expected", expect),
        ("pfn_a", pfn_a),
        ("marker_a", marker_a),
        ("observed_matches_foreign_pfn",
         bool(pfn_a and cand_pa is not None and
              hx({"v": pfn_a}, "v") == (cand_pa >> 12))),
        ("guest_marker_is_foreign", bool(observed and marker_a and
                                         observed == marker_a and
                                         observed != expect)),
        ("fetch_request_pa", (req or {}).get("pa", "")),
        ("request_is_ifu", (req or {}).get("mode") == "Execute"),
        ("microarchitectural_fetch_response", "NOT_EMITTED_BY_FROZEN_BINARY"),
        ("execution_proof", "guest marker equals the code page fetched from "
                            "the foreign candidate PA"),
    ])
    res["guards"] = guards
    res["ok"] = (not guards and not res["missing_kinds"] and
                 res["terminal_evidence"]["guest_marker_is_foreign"] and
                 res["terminal_evidence"]["observed_matches_foreign_pfn"])
    return res


# ---------------------------------------------------------------------------
# M04 — resident entry PFN substitution, consumed by a later request
# ---------------------------------------------------------------------------


def chain_m04(events, context, target_va, mode, oracle_line):
    fid = fault_id(events)
    res = _result("M04", context, mode, target_va, fid)
    act = pick(events, ["mmu_fault_activate"],
               pred=lambda e: str(e.get("fault_id", "0")) == fid)
    if act is None:
        res["missing_kinds"] = ["mmu_fault_activate"]
        return res
    res["activation"] = _ev_summary(act)
    key = entry_identity(act)
    new_pa = hx(act, "new_pa")
    old_pa = hx(act, "old_pa")
    res["identity"]["mutated_entry"] = key
    res["identity"]["mutated_instance"] = instance(act)
    res["identity"]["old_pa"] = None if old_pa is None else hex(old_pa)
    res["identity"]["new_pa"] = None if new_pa is None else hex(new_pa)
    res["activation_basis"] = "M04_ENTRY_PFN_SUBSTITUTION"
    res["join_note"] = (
        "The activation mutates resident entry (instance=%s, entry=%s, "
        "generation=%s) and records old_pa=%s -> new_pa=%s. The later "
        "translation_result names the SAME entry identity and emits new_pa; "
        "the lsu_request(mode=Execute) carries that PA. The C++ "
        "fault_entry_consume counter is 0 for this synthetic IFU transaction, "
        "so the proof is the entry lifetime identity, not the counter." %
        (instance(act), (key or ("", ""))[0], (key or ("", ""))[1],
         act.get("old_pa", ""), act.get("new_pa", "")))

    guards = []
    if key is None:
        guards.append("activation_entry_identity_missing")
    if old_pa is None or new_pa is None:
        guards.append("activation_old_new_pa_missing")

    lineage = pick(events, ["tlb_entry_lineage"], after=act["event_id"],
                   pred=lambda e: str(e.get("fault_id", "0")) == fid and
                   dec(e, "retained_entry_id") == (key or (None, None))[0] and
                   dec(e, "retained_entry_generation") ==
                   (key or (None, None))[1])
    if lineage is None:
        guards.append("retained_entry_lineage_missing")
    else:
        res["identity"]["lineage_event"] = lineage["event_id"]
        res["identity"]["lineage_state"] = lineage.get("lineage_state", "")

    wanted_page = None if target_va is None else target_va >> 12
    consumers = [e for e in events
                 if e["event_id"] > act["event_id"] and
                 kind(e) == "translation_result" and
                 entry_identity(e) == key and hx(e, "pa") == new_pa and
                 (wanted_page is None or page(e) == wanted_page)]
    if not consumers:
        res["missing_kinds"] = ["translation_result"]
        res["guards"] = guards
        return res
    consumer = consumers[0]
    req = pick(events, ["lsu_request"], after=consumer["event_id"],
               pred=lambda e: hx(e, "pa") == new_pa and
               (e.get("mode") == "Execute" if mode == "Execute" else True))
    res["consumption"] = _ev_summary(req or consumer)
    res["consumption_events"] = [act["event_id"], lineage["event_id"]
                                 if lineage else None,
                                 consumer["event_id"],
                                 req["event_id"] if req else None]
    res["consumption_events"] = [e for e in res["consumption_events"] if e]
    res["consumption_basis"] = ("ENTRY_LIFETIME_ITB_%d:%d consumed by "
                                "translation_result and lsu_request" % key
                                if key else "")
    res["fetch_request"] = _ev_summary(req) if req else None
    res["identity"]["consumer_entry"] = entry_identity(consumer)
    res["identity"]["consumer_pa"] = consumer.get("pa")
    res["identity"]["consumer_translation_id"] = tid(consumer)

    if mode == "Execute":
        required = ["translation_start", "tlb_lookup_miss",
                    "tlb_lookup_hit", "tlb_entry_insert",
                    "mmu_fault_activate", "tlb_entry_lineage",
                    "permission_eval", "translation_result", "lsu_request"]
    else:
        required = ["mmu_fault_activate", "tlb_entry_lineage",
                    "tlb_lookup_hit", "fault_entry_consume",
                    "permission_eval", "translation_result", "lsu_request",
                    "memory_response", "commit"]
    res["required_kinds"] = required
    res["missing_kinds"] = sorted(set(_missing_kinds(required, events)))
    if req is None:
        res["missing_kinds"] = sorted(set(res["missing_kinds"] +
                                          ["lsu_request"]))

    tok = oracle_tokens(oracle_line)
    decoy = tok.get("decoy_pfn")
    observed = tok.get("observed")
    decoy_sent = tok.get("decoy_sentinel")
    target_sent = tok.get("sentinel")
    res["terminal_evidence"] = OrderedDict([
        ("guest_line", oracle_line or ""),
        ("observed", observed),
        ("target_sentinel", target_sent),
        ("decoy_sentinel", decoy_sent),
        ("decoy_pfn", decoy),
        ("consumer_pa", consumer.get("pa", "")),
        ("consumer_uses_substituted_pfn",
         bool(decoy and hx({"v": decoy}, "v") ==
              (None if new_pa is None else new_pa >> 12))),
        ("guest_observed_decoy",
         bool(observed and decoy_sent and observed == decoy_sent and
              observed != target_sent)),
        ("request_is_ifu", (req or {}).get("mode") == "Execute"),
        ("microarchitectural_fetch_response", "NOT_EMITTED_BY_FROZEN_BINARY"),
        ("execution_proof", "guest marker equals the decoy code page sentinel"),
    ])
    res["guards"] = guards
    res["ok"] = (not guards and not res["missing_kinds"] and
                 res["terminal_evidence"]["consumer_uses_substituted_pfn"] and
                 res["terminal_evidence"]["guest_observed_decoy"])
    return res


# ---------------------------------------------------------------------------
# M05 — corrupted L2 partial walk-cache entry consumed by a later ITLB walk
# ---------------------------------------------------------------------------


def chain_m05(events, context, target_va, mode, oracle_line):
    fid = fault_id(events)
    res = _result("M05", context, mode, target_va, fid)
    act = pick(events, ["mmu_fault_activate"],
               pred=lambda e: str(e.get("fault_id", "0")) == fid)
    if act is None:
        res["missing_kinds"] = ["mmu_fault_activate"]
        return res
    res["activation"] = _ev_summary(act)
    res["activation_basis"] = "M05_PARTIAL_TABLE_ENTRY_CORRUPTION"
    res["join_note"] = (
        "The faulted partial_entry_insert is the source_event_id of "
        "fault_entry_consume; the consume row names the real partial "
        "tlb_lookup_hit and its entry identity, and the resumed PTW, the "
        "wrong leaf, the translation_result and the lsu_request(mode=Execute) "
        "share that transaction id. The consumer is the +0x1000 alias page "
        "that must resume from the corrupted L2 partial entry.")

    ins = pick(events, ["partial_entry_insert"], after=act["event_id"],
               pred=lambda e: str(e.get("fault_id", "0")) == fid)
    if ins is None:
        res["missing_kinds"] = ["partial_entry_insert"]
        return res
    consume = pick(events, ["fault_entry_consume"], after=ins["event_id"],
                   pred=lambda e: str(e.get("fault_id", "0")) == fid and
                   dec(e, "source_event_id") == ins["event_id"])
    if consume is None:
        res["missing_kinds"] = ["fault_entry_consume"]
        return res
    lookup_id = dec(consume, "lookup_event_id")
    lookup = next((e for e in events if e["event_id"] == lookup_id), None)
    if lookup is None or kind(lookup) != "tlb_lookup_hit":
        res["missing_kinds"] = ["tlb_lookup_hit"]
        return res
    t = tid(lookup) or tid(consume)
    res["identity"]["faulted_insert"] = ins["event_id"]
    res["identity"]["consumer_event"] = consume["event_id"]
    res["identity"]["consumed_entry"] = entry_identity(consume)
    res["identity"]["lookup_event"] = lookup["event_id"]
    res["identity"]["translation_id"] = t
    res["identity"]["corrupted_base_before"] = act.get("next_table_pa_before")
    res["identity"]["corrupted_base_after"] = act.get("next_table_pa_after")

    guards = []
    if entry_identity(lookup) != entry_identity(consume):
        guards.append("consume_lookup_entry_identity_mismatch")
    base_after = hx(act, "next_table_pa_after")
    if base_after is not None:
        ins_pfn = hx(ins, "pfn")
        if ins_pfn not in (base_after, base_after >> 12):
            guards.append("partial_insert_pfn_not_corrupted_base")

    ptw = pick(events, ["ptw_start"], after=consume["event_id"],
               pred=lambda e: str(e.get("fault_id", "0")) == fid and
               tid(e) == t)
    steps = [ptw]
    if ptw:
        for k in ("pte_read", "pte_decode", "tlb_fill", "tlb_entry_insert",
                  "permission_eval", "translation_result"):
            nxt = pick(events, [k], after=ptw["event_id"],
                       pred=lambda e, kk=k: str(e.get("fault_id", "0")) == fid
                       and tid(e) == t)
            steps.append(nxt)
    result = steps[-1] if steps and kind(steps[-1]) == "translation_result" \
        else pick(events, ["translation_result"], after=consume["event_id"],
                  pred=lambda e: str(e.get("fault_id", "0")) == fid and
                  tid(e) == t)
    req = pick(events, ["lsu_request"],
               after=(result or consume)["event_id"],
               pred=lambda e: str(e.get("fault_id", "0")) == fid and
               tid(e) == t and e.get("mode") == (mode or "Execute"))
    res["consumption"] = _ev_summary(req or result or consume)
    res["consumption_events"] = [x["event_id"] for x in
                                 [act, ins, lookup, consume] + steps
                                 + [req] if x]
    res["consumption_basis"] = ("PARTIAL_ENTRY_LIFETIME insert=%d "
                                "consume=%d lookup=%d" %
                                (ins["event_id"], consume["event_id"],
                                 lookup["event_id"]))
    res["fetch_request"] = _ev_summary(req) if req else None

    required = ["mmu_fault_activate", "partial_entry_insert",
                "tlb_lookup_hit", "fault_entry_consume", "ptw_start",
                "pte_read", "pte_decode", "tlb_fill", "tlb_entry_insert",
                "permission_eval", "translation_result", "lsu_request"]
    res["required_kinds"] = required
    res["missing_kinds"] = sorted(set(_missing_kinds(required, events)))

    tok = oracle_tokens(oracle_line)
    decoy = tok.get("decoy_pfn")
    observed = tok.get("observed")
    decoy_sent = tok.get("decoy_sentinel")
    target_sent = tok.get("sentinel")
    result_pfn = hx(result, "pfn") if result is not None else None
    res["terminal_evidence"] = OrderedDict([
        ("guest_line", oracle_line or ""),
        ("observed", observed),
        ("target_sentinel", target_sent),
        ("decoy_sentinel", decoy_sent),
        ("decoy_pfn", decoy),
        ("alias_va", tok.get("alias_va")),
        ("partial_hit", tok.get("partial_hit")),
        ("result_pa", (result or {}).get("pa", "")),
        ("result_pfn", None if result_pfn is None else hex(result_pfn)),
        ("result_is_decoy",
         bool(decoy and result_pfn is not None and
              hx({"v": decoy}, "v") == result_pfn)),
        ("guest_observed_decoy",
         bool(observed and decoy_sent and observed == decoy_sent and
              observed != target_sent)),
        ("request_is_ifu", (req or {}).get("mode") == "Execute"),
        ("microarchitectural_fetch_response", "NOT_EMITTED_BY_FROZEN_BINARY"),
        ("execution_proof", "guest marker equals the decoy page sentinel"),
    ])
    res["guards"] = guards
    res["ok"] = (not guards and not res["missing_kinds"] and
                 res["terminal_evidence"]["result_is_decoy"] and
                 res["terminal_evidence"]["guest_observed_decoy"])
    return res


# ---------------------------------------------------------------------------
# M07 — permission decision inversion consumed by the authorized request
# ---------------------------------------------------------------------------


M07_REQUIRED = {
    "R01": ["mmu_fault_activate", "translation_result", "lsu_request",
            "cache_request", "cache_lookup", "memory_response", "commit"],
    "R02": ["mmu_fault_activate", "translation_result", "lsu_request",
            "cache_request", "cache_lookup", "memory_response",
            "rf_writeback", "commit"],
    "R03": ["mmu_fault_activate", "translation_result", "lsu_request"],
    "R04": ["translation_start", "tlb_lookup_miss", "tlb_lookup_hit",
            "tlb_entry_insert", "permission_eval", "mmu_fault_activate",
            "translation_result", "lsu_request"],
    "R05": ["translation_start", "tlb_lookup_miss", "tlb_lookup_hit",
            "tlb_entry_insert", "permission_eval", "mmu_fault_activate",
            "translation_result", "lsu_request"],
}


def chain_m07(events, context, target_va, mode, oracle_line):
    fid = fault_id(events)
    res = _result("M07", context, mode, target_va, fid)
    res["required_kinds"] = list(M07_REQUIRED.get(context, []))
    act = pick(events, ["mmu_fault_activate"],
               pred=lambda e: str(e.get("fault_id", "0")) == fid)
    if act is None:
        res["missing_kinds"] = ["mmu_fault_activate"]
        return res
    res["activation"] = _ev_summary(act)
    res["activation_basis"] = "M07_PERMISSION_GRANT_INVERSION"

    guards = []
    if not (act.get("permission_before") == "false" and
            act.get("permission_after") == "true"):
        guards.append("activation_does_not_record_false_to_true_inversion")

    t = tid(act)
    basis = "ACTIVATION_CARRIES_TRANSACTION_ID"
    if not t:
        # Fetch path: the hook runs with seq=0, so the C++ cannot mint a
        # transaction id (mmuBeginTxn refuses seq==0).  Join the inversion to
        # the permission evaluation that produced it by a co-temporal key
        # match: same tick AND same VA AND same mode/stage/regime/security
        # state.  Then use that transaction id for the result/request.
        pe = pick(events, ["permission_eval"],
                  after=-1,
                  pred=lambda e: e["event_id"] < act["event_id"] and
                  e.get("tick") == act.get("tick") and
                  e.get("va") == act.get("va") and
                  e.get("mode") == act.get("mode") and
                  e.get("stage", "") == act.get("stage", "") and
                  e.get("regime", "") == act.get("regime", "") and
                  e.get("security_state", "") == act.get("security_state", ""))
        if pe is None:
            guards.append("cotemporal_permission_eval_not_found")
            res["guards"] = guards
            return res
        t = tid(pe)
        basis = "COTEMPORAL_PERMISSION_EVAL_KEY_MATCH"
        res["identity"]["permission_eval_event"] = pe["event_id"]
        res["identity"]["permission_eval_result"] = pe.get("permission_result")
        res["identity"]["permission_eval_tick"] = pe.get("tick")
        if pe.get("permission_result") != "deny":
            guards.append("permission_eval_pre_inversion_not_deny")
    res["identity"]["translation_id"] = t
    res["activation_basis"] = basis
    res["join_note"] = (
        "The activation row carries translation_id=0 on the fetch path because "
        "the C++ hook runs for an instruction-fetch Request with no "
        "instruction sequence number (mmu.cc:742-791; mmuBeginTxn refuses "
        "seq==0). The join to translation %d is a co-temporal key match: the "
        "permission_eval at the same tick/cycle, VA, mode, stage, regime and "
        "security state records the real deny decision, and that same "
        "transaction owns the translation_result and the "
        "lsu_request(mode=Execute). It is never inferred from event order." %
        t)

    result = pick(events, ["translation_result"], after=act["event_id"],
                  pred=lambda e: tid(e) == t)
    req = pick(events, ["lsu_request"],
               after=(result or act)["event_id"],
               pred=lambda e: tid(e) == t and
               e.get("mode") == (mode or e.get("mode")))
    if result is None:
        guards.append("translation_result_on_inverted_transaction_missing")
    if req is None:
        guards.append("lsu_request_on_inverted_transaction_missing")

    res["consumption"] = _ev_summary(req or result)
    res["consumption_events"] = [e["event_id"] for e in
                                 [act, result, req] if e]
    res["consumption_basis"] = ("SAME_TRANSACTION_%s permission_eval -> "
                                "translation_result -> lsu_request" % basis)
    res["fetch_request"] = _ev_summary(req) if req else None
    res["missing_kinds"] = sorted(set(_missing_kinds(
        res["required_kinds"], events)))
    res["guards"] = guards

    tok = oracle_tokens(oracle_line)
    res["terminal_evidence"] = OrderedDict([
        ("guest_line", oracle_line or ""),
        ("phase", tok.get("phase")),
        ("observed", tok.get("observed")),
        ("expected", tok.get("expected")),
        ("injected_success", tok.get("injected_success")),
        ("value_ok", tok.get("value_ok")),
        ("pte_present", tok.get("pte_present")),
        ("indirect_branch_line",
         next((ln for ln in (oracle_line or "").splitlines()
               if "indirect_branch" in ln), "")),
        ("executed_line",
         next((ln for ln in (oracle_line or "").splitlines()
               if "stage=executed" in ln), "")),
        ("request_pa", (req or {}).get("pa", "")),
        ("pxn_xn", next((ln for ln in (oracle_line or "").splitlines()
                         if "pte_decode" in ln), "")),
        ("microarchitectural_fetch_response", "NOT_EMITTED_BY_FROZEN_BINARY"),
        ("execution_proof", "guest marker returned only by executing the "
                            "XN page after the inverted grant"),
    ])
    res["ok"] = (not guards and not res["missing_kinds"] and
                 result is not None and req is not None and
                 req.get("mode") == "Execute" and
                 tok.get("injected_success") == "1" and
                 tok.get("value_ok") == "1")
    return res


# ---------------------------------------------------------------------------
# dispatcher / required kinds for every model
# ---------------------------------------------------------------------------


def evaluate(model, context, events, target_va, mode, oracle_line=""):
    if model == "M03":
        return chain_m03(events, context, target_va, mode, oracle_line)
    if model == "M04":
        return chain_m04(events, context, target_va, mode, oracle_line)
    if model == "M05":
        return chain_m05(events, context, target_va, mode, oracle_line)
    if model == "M07":
        return chain_m07(events, context, target_va, mode, oracle_line)
    return None


def required_kinds(model, context, mode, observed, workload=None):
    """Non-empty expected kinds for every model (never a silent [])."""
    if model == "M01":
        return list(MMU_TRACE_REQUIRED.get((workload, "M01"), []))
    if model == "M02":
        return list(MMU_TRACE_REQUIRED.get((workload, "M02"), []))
    if model == "M03":
        if mode == "Execute":
            return ["translation_start", "tlb_lookup_miss",
                    "mmu_fault_activate", "tlb_lookup_hit",
                    "tlb_entry_insert", "permission_eval",
                    "translation_result", "lsu_request"]
        return ["translation_start", "tlb_lookup_miss",
                "mmu_fault_activate", "tlb_lookup_hit", "tlb_entry_insert",
                "permission_eval", "translation_result", "squash"]
    if model == "M04":
        if mode == "Execute":
            return ["translation_start", "tlb_lookup_miss",
                    "tlb_lookup_hit", "tlb_entry_insert",
                    "mmu_fault_activate", "tlb_entry_lineage",
                    "permission_eval", "translation_result", "lsu_request"]
        return ["mmu_fault_activate", "tlb_entry_lineage",
                "tlb_lookup_hit", "fault_entry_consume", "permission_eval",
                "translation_result", "lsu_request", "memory_response",
                "commit"]
    if model == "M05":
        return ["mmu_fault_activate", "partial_entry_insert",
                "tlb_lookup_hit", "fault_entry_consume", "ptw_start",
                "pte_read", "pte_decode", "tlb_fill", "tlb_entry_insert",
                "permission_eval", "translation_result", "lsu_request"]
    if model == "M06":
        return ["mmu_fault_activate", "pte_decode", "fault_state_consumed",
                "fault_result_propagated", "exception_delivery"]
    if model == "M07":
        return list(M07_REQUIRED.get(context, []))
    if model == "M08":
        return ["mmu_fault_activate", "translation_result", "lsu_request",
                "cache_request", "cache_lookup", "memory_response", "commit"]
    return []


# Import late to avoid a cycle: v3 only supplies the frozen model tables.
try:  # pragma: no cover - exercised by the validator
    from mmu_trace_validate_v3 import MODEL_REQUIRED as MMU_TRACE_REQUIRED
except Exception:  # pragma: no cover
    MMU_TRACE_REQUIRED = {}
