#!/usr/bin/env python3
"""Identity-based MMU fault propagation-chain reconstruction.

Replaces the stage-order heuristic in campaign/finalize.py with a causal
reconstruction rooted at the real fault activation.  Every edge is justified
by an explicit correlation field or persistent-state identity, never by
"same kind" or "happens after activation" alone.

Correlation evidence used (in priority order):
  parent_event_id          -- direct causal parent in the same pipeline
  source_event_id          -- cross-request state lineage (fault_entry_* -> insert)
  origin_event_id          -- origin event of a faulted state
  translation_id           -- translation transaction (nonzero only)
  request_id               -- LSU/cache request identity (nonzero only)
  walk_id                  -- page-table walk identity
  entry identity           -- (tlb_instance, tlb_entry_id, entry_generation)
                              or (tlb_entry_id, entry_generation) where one
                              side has no instance
  retained entry identity  -- retained_entry_(id/generation) vs entry fields
  dyn_inst_seq / origin_dyn_inst_seq -- dynamic instruction lineage
  co-temporal key          -- (tick, va, mode, stage, regime, security) for the
                              fetch path where the activation carries
                              translation_id=0 (mmu.cc refuses seq==0)

The tracer already tags every event it decided to be causally downstream of
the fault with the same `fault_id`.  We treat that tag as a *candidate* set,
then require an explicit basis for each edge; where no explicit basis exists
the edge is recorded as UNKNOWN rather than invented.

Streaming: the raw fault traces are large (a single M04 ROI can exceed 1 GB
uncompressed).  `build_chain_from_path` therefore does a single pass that
only fully parses fault-tagged (`fault_id=1`) events plus a small tail used
to recover the activation's parent and the co-temporal permission_eval.
"""

import gzip

# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------

ACTIVATION_KINDS = {"mmu_fault_activate", "mmu_fault_arm",
                    "refill_pfn_corrupt"}
SUMMARY_KINDS = {"mmu_fault_summary", "chain_end"}

INT_KEYS = {
    "event_id", "tick", "cycle", "fault_id", "parent_event_id",
    "source_event_id", "origin_event_id", "translation_id", "request_id",
    "lookup_id", "walk_id", "tlbi_id", "tlb_entry_id", "entry_generation",
    "asid", "vmid", "dyn_inst_seq", "origin_dyn_inst_seq", "page_size_n",
    "ptw_request_id", "ptw_response_id", "cache_req_id", "mshr_id",
    "fill_id", "pf_request_id", "eligible_ordinal", "consumed",
    "state_consumed", "result_propagated", "exception_delivered",
    "faulting_inst_squashed", "fault_arm_event_id", "fault_disarm_event_id",
    "consumption_event_id", "match_event_id", "lookup_event_id",
    "entry_insert_event_id", "activation_event_id", "result_event_id",
    "response_event_id", "writeback_event_id", "commit_event_id",
    "origin_squash_event_id", "fault_state_consumed_event_id",
    "fault_result_propagated_event_id", "exception_delivery_event_id",
    "retained_entry_id", "retained_entry_generation", "first_tlbi_id",
    "suppress_count", "reuse_ordinal", "faulting_inst_squash_event_id",
    "is_fetch", "is_write", "isv", "commit_seq", "response_id",
    "consumer_of",
}

HEX_KEYS = {
    "va", "pa", "pfn", "old_pfn", "new_pfn", "old_pa", "new_pa",
    "candidate_pa", "candidate_pfn", "pte_address",
    "next_table_pa_before", "next_table_pa_after", "result_pa",
    "decoy_pfn", "decoy_pa", "decoy_vpn", "decoy_table_base",
    "request_pa_before", "request_pa_after",
}


def _dec(s):
    try:
        return int(s, 10)
    except (ValueError, TypeError):
        return None


def _hex(s):
    if s in (None, ""):
        return None
    try:
        return int(s, 16) if not str(s).lower().startswith("0x") else int(s, 0)
    except ValueError:
        return None


def parse_raw(line):
    line = line.strip()
    if not line.startswith("PROP-EVT:"):
        return None
    out = {}
    for token in line[len("PROP-EVT:"):].split():
        if "=" not in token:
            continue
        k, v = token.split("=", 1)
        out[k] = v
    return out


def _type(ev):
    for k in INT_KEYS:
        if k in ev:
            ev[k] = _dec(ev[k])
    for k in HEX_KEYS:
        if k in ev:
            ev[k] = _hex(ev[k])
    return ev


def parse_line(line):
    ev = parse_raw(line)
    return _type(ev) if ev is not None else None


def load_events(path):
    events = []
    opener = gzip.open if str(path).endswith(".gz") else open
    try:
        with opener(path, "rt", errors="replace") as fh:
            for line in fh:
                ev = parse_line(line)
                if ev is not None:
                    events.append(ev)
    except (OSError, EOFError):
        pass
    return events


# ---------------------------------------------------------------------------
# streaming collection (single pass, memory-light)
# ---------------------------------------------------------------------------

def collect(path):
    """Single-pass collector returning
    (act, fevs, mmu_summary, ctx_pool, parent_ev).

    ctx_pool holds fully-parsed events near the activation: the raw tail that
    precedes it (for the parent / co-temporal permission_eval) and a short
    window of ~64 events that follow it (for the fetch-path
    translation_result / lsu_request that the tracer cannot tag with the
    fault id because the activation carries translation_id=0)."""
    act = None
    fid = None
    fevs = []
    mmu_summary = None
    chain_end = None
    ctx_pool = []
    parent_ev = None
    tail = []          # raw lines before the activation
    post_window = 0

    opener = gzip.open if str(path).endswith(".gz") else open
    try:
        with opener(path, "rt", errors="replace") as fh:
            for line in fh:
                if not line.startswith("PROP-EVT:"):
                    continue
                if act is None:
                    tail.append(line)
                    if len(tail) > 256:
                        tail.pop(0)
                    if "fault_id=1 " not in line:
                        continue
                    ev = parse_line(line)
                    if ev is None:
                        continue
                    k = ev.get("kind")
                    if k in ACTIVATION_KINDS and ev.get("fault_id"):
                        act = ev
                        fid = ev.get("fault_id")
                        post_window = 64
                        tail_evs = [e for e in (parse_line(l) for l in tail)
                                    if e is not None]
                        ctx_pool.extend(tail_evs)
                        ap = ev.get("parent_event_id")
                        if ap is not None:
                            parent_ev = next((e for e in tail_evs
                                              if e.get("event_id") == ap), None)
                    if ev.get("fault_id") == fid:
                        fevs.append(ev)
                        if k == "mmu_fault_summary" and mmu_summary is None:
                            mmu_summary = ev
                        elif k == "chain_end" and chain_end is None:
                            chain_end = ev
                else:
                    # after activation: collect the short fetch-recovery window
                    if post_window > 0:
                        ev = parse_line(line)
                        if ev is not None:
                            ctx_pool.append(ev)
                        post_window -= 1
                    if "fault_id=1 " in line:
                        ev = parse_line(line)
                        if ev is not None and ev.get("fault_id") == fid:
                            fevs.append(ev)
                            if ev.get("kind") == "mmu_fault_summary" and \
                                    mmu_summary is None:
                                mmu_summary = ev
                            elif ev.get("kind") == "chain_end" and \
                                    chain_end is None:
                                chain_end = ev
    except (OSError, EOFError):
        pass
    return act, fevs, mmu_summary or chain_end, ctx_pool, parent_ev


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def kind(e):
    return e.get("kind", "")


def _entry_key(e):
    iid = e.get("tlb_entry_id")
    gen = e.get("entry_generation")
    if iid is None or gen is None:
        return None
    return (iid, gen)


def _entry_full(e):
    iid = e.get("tlb_entry_id")
    gen = e.get("entry_generation")
    inst = e.get("tlb_instance", "")
    if iid is None or gen is None:
        return None
    return (inst, iid, gen)


def _retained_key(e):
    iid = e.get("retained_entry_id")
    gen = e.get("retained_entry_generation")
    if iid is None or gen is None:
        return None
    return (iid, gen)


def tid(e):
    v = e.get("translation_id")
    return v if v else 0


def rid(e):
    v = e.get("request_id")
    return v if v else 0


def wid(e):
    v = e.get("walk_id")
    return v if v else 0


MUTATION_KINDS = {
    "M01": {"tlbi_suppressed", "mmu_fault_disarm"},
    "M02": {"tlb_entry_insert"},
    "M03": {"tlb_lookup_hit", "tlb_entry_insert"},
    "M04": {"tlb_entry_lineage"},
    "M05": {"partial_entry_insert", "tlb_entry_insert"},
    "M06": {"pte_decode"},
    "M07": set(),
    "M08": set(),
}

CONSUME_ANCHOR_KINDS = {
    "fault_entry_consume", "fault_entry_reuse",
    "fault_state_consumed", "fault_result_propagated",
}


# ---------------------------------------------------------------------------
# edge basis
# ---------------------------------------------------------------------------


def _parent(e):
    p = e.get("parent_event_id")
    return p if p else None


def edge_basis(source, target):
    ts = source.get("event_id")
    tt = target.get("event_id")
    if ts is None or tt is None or ts >= tt:
        return None

    if _parent(target) == ts:
        return ("parent_child", "parent_event_id", "high")

    if target.get("source_event_id") == ts:
        return ("state_source", "source_event_id", "high")
    if target.get("origin_event_id") == ts:
        return ("state_source", "origin_event_id", "high")

    t_s, t_t = tid(source), tid(target)
    if t_t and t_s == t_t:
        return ("transaction", "translation_id", "high")

    r_s, r_t = rid(source), rid(target)
    if r_t and r_s == r_t:
        return ("transaction", "request_id", "high")

    w_s, w_t = wid(source), wid(target)
    if w_t and w_s == w_t:
        return ("transaction", "walk_id", "medium")

    ef_s, ef_t = _entry_full(source), _entry_full(target)
    if ef_s is not None and ef_s == ef_t:
        return ("state_source", "entry_identity", "high")
    k_s, k_t = _entry_key(source), _entry_key(target)
    if k_s is not None and k_s == k_t:
        # instance-less match: only if at least one side has no instance
        if ef_s is None or ef_t is None or ef_s[0] == "" or ef_t[0] == "":
            return ("state_source", "entry_identity", "medium")

    rk_s = _retained_key(source)
    if rk_s is not None and rk_s == _entry_key(target):
        return ("state_source", "retained_entry", "medium")
    k_s = _entry_key(source)
    rk_t = _retained_key(target)
    if k_s is not None and k_s == rk_t:
        return ("state_source", "retained_entry", "medium")

    if (source.get("origin_dyn_inst_seq") is not None and
            source.get("origin_dyn_inst_seq") == target.get("dyn_inst_seq") and
            source.get("dyn_inst_seq") != target.get("dyn_inst_seq")):
        return ("state_source", "dyn_lineage", "medium")

    # [W5X3-OBS-0202c] M05 partial-entry -> poisoned-DTB-entry propagation.
    # The corrupted partial entry (partial_entry_insert) causes fault-tagged
    # walks that fill a COMPLETE DTB entry (tlb_entry_insert) with the decoy
    # PA; that DTB entry is then consumed by later warm hits. Both events are
    # fault-tagged with the SAME fault_id (the single-fault chain id), which
    # is a real correlation identity — never a tick/VA-only join.
    if (source.get("fault_id") is not None and
            source.get("fault_id") == target.get("fault_id") and
            source.get("fault_id") not in ("", "0") and
            kind(source) == "partial_entry_insert" and
            kind(target) == "tlb_entry_insert"):
        return ("state_source", "fault_entry_lineage", "medium")

    return None


def cotemporal_key(e):
    return (e.get("tick"), e.get("va"), e.get("mode"), e.get("stage", ""),
            e.get("regime", ""), e.get("security_state", ""))


def find_cotemporal_permission_eval(events, act):
    pool = [e for e in events
            if kind(e) == "permission_eval" and
            e.get("event_id") is not None and
            e.get("event_id") < act.get("event_id") and
            e.get("tick") == act.get("tick") and
            e.get("va") == act.get("va")]
    exact = [e for e in pool
             if e.get("mode") == act.get("mode") and
             e.get("stage", "") == act.get("stage", "") and
             e.get("regime", "") == act.get("regime", "") and
             e.get("security_state", "") == act.get("security_state", "")]
    return exact, pool


# ---------------------------------------------------------------------------
# reconstruction
# ---------------------------------------------------------------------------


def _ev(e):
    if not e:
        return None
    keys = ("event_id", "tick", "fault_id", "mode", "asid", "vmid",
            "va", "pa", "pfn", "dyn_inst_seq", "origin_dyn_inst_seq",
            "translation_id", "request_id", "walk_id", "tlb_instance",
            "tlb_entry_id", "entry_generation", "outcome", "corr",
            "permission_result", "permission_before", "permission_after",
            "old_pfn", "new_pfn", "old_pa", "new_pa",
            "candidate_asid", "candidate_pa", "descriptor_before",
            "descriptor_after", "exception_class", "exception_delivered",
            "state_consumed", "result_propagated", "consumed",
            "faulting_inst_squashed", "is_fetch", "masked_reason",
            "consumer_of", "commit_seq", "phys_reg")
    out = {"kind": e.get("kind", "")}
    for k in keys:
        v = e.get(k)
        if v is not None and v != "":
            out[k] = hex(v) if (k in HEX_KEYS and isinstance(v, int)) else v
    # `consumer_of` and the writeback physical register are carried in the
    # `field` attribute of the consumer / rf_writeback events.
    f = e.get("field", "")
    if f and f.startswith("consumer_of="):
        try:
            out["consumer_of"] = int(f.split("=", 1)[1], 10)
        except ValueError:
            out["consumer_of"] = f.split("=", 1)[1]
    elif f:
        out["reg_field"] = f
    return out


def _add_edge(out, src, dst):
    if src is None or dst is None:
        return
    if src.get("event_id") == dst.get("event_id"):
        return
    basis = edge_basis(src, dst)
    if basis is None:
        out["edges"].append({
            "type": "unknown", "basis": "UNKNOWN", "confidence": "none",
            "source": src.get("event_id"), "target": dst.get("event_id"),
            "source_kind": kind(src), "target_kind": kind(dst)})
    else:
        out["edges"].append({
            "type": basis[0], "basis": basis[1], "confidence": basis[2],
            "source": src.get("event_id"), "target": dst.get("event_id"),
            "source_kind": kind(src), "target_kind": kind(dst)})


# ---------------------------------------------------------------------------
# multi-branch reconstruction (DAG)
# ---------------------------------------------------------------------------

# All architecture stages a *complete* data-path propagation would exhibit.
# `mutation` / `translation` / `request` / `response` / `consumer` /
# `commit_squash` are the compressed nodes the acceptance machinery reasons
# about; a stage is "expected" unless it is declared not-applicable below.
ALL_STAGES = ("mutation", "translation", "request", "response",
              "writeback", "consumer", "commit_squash")


def build_branches(fevs):
    """Split the fault-tagged event stream into consumer branches keyed by
    nonzero translation_id.  Each branch is one fault-effect transaction
    (origin or a later reuse of the same faulted state).

    The consume/reuse anchors (`fault_entry_consume` / `fault_entry_reuse`)
    carry translation_id=0 in the tracer (they are emitted between the lookup
    and the page-table-walk start), so they are associated to their branch via
    their `parent_event_id` (the tlb_lookup_hit that carries the transaction
    id) or, failing that, by matching `request_id`."""
    by_id = {e.get("event_id"): e for e in fevs
             if e.get("event_id") is not None}
    by_tid = {}
    order = []
    for e in fevs:
        t = tid(e)
        if not t:
            continue
        if t not in by_tid:
            by_tid[t] = []
            order.append(t)
        by_tid[t].append(e)
    # associate zero-translation_id downstream events to their branch: the
    # consume/reuse anchors (fault_entry_consume / fault_entry_reuse) and the
    # data-consumer pair (`consumer` + the consumer's own `commit`).  The
    # `consumer` event carries translation_id=0 and is emitted when a committed
    # dynamic instruction reads the physical register a fault-tagged Load
    # wrote; its parent_event_id is that Load's rf_writeback, so parent
    # association binds it to the producer's branch.
    _assoc_kinds = set(CONSUME_ANCHOR_KINDS) | {"consumer", "commit"}
    for e in fevs:
        if kind(e) not in _assoc_kinds or tid(e):
            continue
        parent = by_id.get(e.get("parent_event_id"))
        t = tid(parent) if parent else 0
        if not t:
            for bt in order:
                if any(rid(x) == rid(e) and rid(e) for x in by_tid[bt]):
                    t = bt
                    break
        if t:
            by_tid.setdefault(t, []).append(e)
    branches = []
    for t in order:
        evs = sorted(by_tid[t], key=lambda e: (e.get("event_id") or 0))
        anchor = next((e for e in evs
                       if kind(e) in CONSUME_ANCHOR_KINDS), None)
        tr = next((e for e in evs if kind(e) == "translation_result"), None)
        req = next((e for e in evs if kind(e) == "lsu_request"), None)
        # The architecture "response" is the final data response that precedes
        # rf_writeback.  For a read that is `memory_response` (carries data_fnv);
        # `cache_response` is the intermediate L2->MSHR acknowledgement that is
        # emitted earlier and must NOT be reported as the data response.  For an
        # instruction-side fetch it is `ifu_response`.  For a store/atomic (no
        # memory_response) only `cache_response` remains.
        resp = next((e for e in evs if kind(e) == "memory_response"), None)
        if resp is None:
            resp = next((e for e in evs if kind(e) == "ifu_response"), None)
        if resp is None:
            resp = next((e for e in evs if kind(e) == "cache_response"), None)
        # rf_writeback is the Load's own register writeback; the `consumer`
        # event is the separate downstream instruction that reads that register
        # (kind=consumer, field=consumer_of=<producer dyn_inst_seq>).  On the
        # fetch path the consumer is the ifu_decode event instead.
        wb = next((e for e in evs if kind(e) == "rf_writeback"), None)
        cons = next((e for e in evs if kind(e) == "consumer"), None)
        if cons is None:
            cons = next((e for e in evs if kind(e) == "ifu_decode"), None)
        # The terminal commit is the DATA CONSUMER's own retirement (matching
        # dyn_inst_seq), never the producer Load's commit which is a sibling of
        # the consumer under the same rf_writeback parent.
        term = None
        if cons is not None and cons.get("dyn_inst_seq") is not None:
            term = next((e for e in evs if kind(e) == "commit" and
                         e.get("dyn_inst_seq") == cons.get("dyn_inst_seq")),
                        None)
        if term is None:
            term = next((e for e in evs if kind(e) == "commit"), None)
        if term is None:
            term = next((e for e in evs if kind(e) == "squash"), None)
        if term is None:
            term = next((e for e in reversed(evs)
                         if kind(e) == "lsu_request"), None)
        if term is None:
            term = next((e for e in reversed(evs)
                         if kind(e) == "translation_result"), None)
        head = tr or req or evs[0]
        insert_keys = {(e.get("tlb_entry_id"), e.get("entry_generation"))
                       for e in evs
                       if kind(e) == "tlb_entry_insert" and
                       e.get("tlb_entry_id") is not None and
                       e.get("entry_generation") is not None}
        hit_keys = {(e.get("tlb_entry_id"), e.get("entry_generation"))
                    for e in evs
                    if kind(e) == "tlb_lookup_hit" and
                    e.get("tlb_entry_id") is not None and
                    e.get("entry_generation") is not None}
        branches.append({
            "translation_id": t,
            "consume_kind": kind(anchor) if anchor else None,
            "consume_event_id": anchor.get("event_id") if anchor else None,
            "reuse_ordinal": anchor.get("reuse_ordinal") if anchor else None,
            "origin_dyn_inst_seq": anchor.get("origin_dyn_inst_seq")
            if anchor else None,
            "dyn_inst_seq": head.get("dyn_inst_seq"),
            "va": head.get("va"),
            "pa": head.get("pa"),
            "mode": (req or tr or {}).get("mode"),
            "terminal": term,
            "terminal_kind": kind(term) if term else None,
            "terminal_event_id": term.get("event_id") if term else None,
            "terminal_tick": term.get("tick") if term else None,
            "commits": bool(term and kind(term) == "commit"),
            "squashed": bool(term and kind(term) == "squash"),
            "insert_keys": insert_keys,
            "hit_keys": hit_keys,
            "stages": {"translation": tr, "request": req, "response": resp,
                       "writeback": wb, "consumer": cons, "terminal": term},
        })
    return branches


def select_effect_branch(branches, summary):
    """Pick the branch whose translation is the fault's architectural effect.

    Prefer the tracer's own summary anchors (`result_event_id` first, then the
    faulted entry identity), then the first committing branch, then the first
    branch."""
    if not branches:
        return None
    if summary is not None:
        rid = summary.get("result_event_id")
        if rid is not None:
            for i, b in enumerate(branches):
                if any(e.get("event_id") == rid
                       for e in (b["stages"].get("translation"),
                                 b["stages"].get("request")) if e):
                    return i
            for i, b in enumerate(branches):
                if b["terminal_event_id"] == rid:
                    return i
        eid = summary.get("tlb_entry_id")
        gen = summary.get("entry_generation")
        if eid is not None and gen is not None:
            key = (eid, gen)
            for i, b in enumerate(branches):
                if key in b["insert_keys"]:
                    return i
            for i, b in enumerate(branches):
                if key in b["hit_keys"]:
                    return i
    for i, b in enumerate(branches):
        if b["commits"]:
            return i
    return 0


def resolve_terminal(branch, summary):
    """Return (raw_terminal_event, terminal_kind) for a branch, applying the
    tracer's own `faulting_inst_squashed` signal: a squash that the tracer
    does not consider architecturally final (a replay / wrong-path artifact
    that does not stop the completed walk) is *not* the terminal — the effect
    still reached the LSU request."""
    if branch is None:
        return None, None
    term = branch["terminal"]
    tkind = branch["terminal_kind"]
    transient = (tkind == "squash" and summary is not None and
                 summary.get("faulting_inst_squashed") == 0)
    if transient:
        st = branch["stages"]
        if st.get("request") is not None:
            return st["request"], "lsu_request"
        if st.get("translation") is not None:
            return st["translation"], "translation_result"
    return term, tkind


def mutation_handoff(mut_raw, fevs, anchor=None):
    """Return the explicit state-transfer events that bridge a mutation to the
    entry a later consumer reuses.

    M01 suppresses a TLBI so the retained L2 entry (retained_entry_id /
    generation) stays valid; on the first hit the entry is disarmed and its
    stale PA is cached into a *new* DTB entry (tlb_entry_insert).  The later
    consumers reuse that DTB entry, not the retained entry, so a direct
    mutation -> consume edge has no common identity.  This helper recovers the
    two bridge events:
        disarming hit   -- tlb_lookup_hit whose (entry_id, generation) equals
                           the mutation's retained entry
        dtb insert      -- tlb_entry_insert whose parent is that hit
    giving mutation -> hit (retained_entry) -> insert (parent) -> reuse
    (entry_identity) — all explicit.

    M05 substitutes a partial L2 walk-cache entry; the faulted walk then fills
    a *new* complete DTB entry (tlb_entry_insert) whose decoy PA the later
    warm-hit consumers reuse.  The consumer's source_event_id names that DTB
    insert, and the insert shares the mutation's translation_id, so the bridge
    is mutation -> insert (translation_id) -> reuse (source_event_id)."""
    rk = _retained_key(mut_raw)
    if rk is not None:
        hit = next((e for e in fevs if kind(e) == "tlb_lookup_hit" and
                    _entry_key(e) == rk), None)
        if hit is None:
            return []
        insert = next((e for e in fevs if kind(e) == "tlb_entry_insert" and
                       _parent(e) == hit.get("event_id")), None)
        if insert is None:
            return []
        return [hit, insert]
    if kind(mut_raw) == "partial_entry_insert" and anchor is not None:
        seid = anchor.get("source_event_id")
        if seid is None:
            return []
        insert = next((e for e in fevs if e.get("event_id") == seid), None)
        if insert is None:
            return []
        # [W5X3-OBS-0202c] Recover the FULL partial-entry -> poisoned-DTB-entry
        # state transfer, not just the insert.  The corrupted partial entry is
        # later reused (fault_entry_reuse with source_event_id == mutation),
        # which restarts a page-table walk (ptw_start) that reads the decoy
        # next-table base (pte_read -> ptw_request -> ptw_response -> pte_decode)
        # and fills a complete DTB entry (tlb_fill -> tlb_entry_insert).  All of
        # these are fault-tagged and joined by request_id / walk_id / parent.
        chain = []
        ridv = insert.get("request_id")
        # the PTW walk that filled this complete entry
        ptw = next((e for e in fevs
                    if kind(e) == "ptw_start" and
                    e.get("request_id") == ridv), None)
        if ptw is not None:
            wid = ptw.get("walk_id")
            chain = [e for e in fevs
                     if (e.get("walk_id") == wid) or
                     e.get("event_id") == insert.get("event_id")]
        # the partial-entry reuse that restarted this walk
        reuse = next((e for e in fevs
                      if kind(e) == "fault_entry_reuse" and
                      e.get("source_event_id") == mut_raw.get("event_id") and
                      e.get("request_id") == ridv), None)
        if reuse is not None:
            chain.append(reuse)
        # de-duplicate and order by event_id
        chain = sorted({e.get("event_id"): e for e in chain if e}.values(),
                       key=lambda e: e.get("event_id") or 0)
        return chain
    return []


def branch_summary(b):
    """Compact, traceable per-branch record (translation_id + terminal + the
    effect PA).  Full stage detail for the *effect* branch is carried by the
    single-chain fields; this list only records the fan-out structure so the
    per_condition.json stays bounded for the ~1000-consumer M01 traces."""
    return {
        "translation_id": b["translation_id"],
        "consume_kind": b["consume_kind"],
        "consume_event_id": b["consume_event_id"],
        "reuse_ordinal": b["reuse_ordinal"],
        "origin_dyn_inst_seq": b["origin_dyn_inst_seq"],
        "dyn_inst_seq": b["dyn_inst_seq"],
        "va": hex(b["va"]) if isinstance(b["va"], int) else b["va"],
        "pa": hex(b["pa"]) if isinstance(b["pa"], int) else b["pa"],
        "mode": b["mode"],
        "terminal_kind": b["terminal_kind"],
        "terminal_event_id": b["terminal_event_id"],
        "terminal_tick": b["terminal_tick"],
        "commits": b["commits"],
        "squashed": b["squashed"],
    }


def expected_stages(model, act, term_kind, masked_reason=None):
    """Return (not_applicable, boundary) for the architecture-completeness
    dimension.

    * not_applicable — a stage this model's propagation shape does not have
      (structural absence, e.g. M06 detection has no LSU request; a store has
      no rf_writeback; a squashed instruction writes back nothing).
    * boundary — a stage that *does* exist architecturally but that the frozen
      binary does not emit (NOT_EMITTED_BY_FROZEN_BINARY), e.g. the
      per-instruction IFU response/commit of an instruction-side fetch.

    Both are declared rather than silently completed; only a `boundary` (or a
    raw ``unobserved`` gap) makes ``architecture_complete`` false."""
    na = set()
    boundary = set()
    mode = (act or {}).get("mode", "")
    if model == "M06":
        # detection path: no LSU data request / writeback / consumer
        na |= {"translation", "request", "response", "writeback", "consumer"}
    if model in ("M07", "M08"):
        # mutation is carried inside the activation row
        na.add("mutation")
        # a store (Write) commits directly with no rf_writeback/data consumer;
        # an atomic RMW still has BOTH (the trace shows rf_writeback + consumer)
        if mode == "Write":
            na |= {"writeback", "consumer"}
    # instruction-side fetch: the IFU consumes the fetched line (ifu_decode)
    # with no per-instruction register rf_writeback, so `writeback` is
    # structurally absent
    if mode == "Execute":
        na.add("writeback")
    if mode == "Execute" and term_kind == "lsu_request":
        # instruction-side fetch that reached ONLY the Execute lsu_request:
        # the frozen binary did not emit per-instruction IFU
        # response/decode/commit. With the 0202c IFU instrumentation a faulted
        # fetch that DID reach the IFU pipeline terminates on commit/squash and
        # these stages are directly observed, so this boundary only remains for
        # the honest fallback where no IFU event fired.
        boundary |= {"response", "consumer", "commit_squash"}
    if term_kind == "squash":
        # a truly squashed consumer writes back nothing
        na |= {"writeback", "consumer"}
    if term_kind == "mmu_fault_unconsumed":
        # natural endpoint: the fault armed but no later access consumed it —
        # the downstream data-path stages do not apply, not "missing"
        na |= {"translation", "request", "response", "writeback", "consumer",
               "commit_squash"}
    if (term_kind == "lsu_request" and
            masked_reason == "request_issued_not_completed_at_roi_end"):
        # [W5X3-FIX] The request was issued but NEVER completed before the ROI
        # boundary.  response / writeback / consumer / commit_squash are NOT
        # structurally absent (the request would have produced them had it
        # completed); they are missing because the ROI cut the request off.
        # Record them as an explicit ROI-boundary so the sample is PARTIAL
        # (architecture), never a silent FULL or a structural N/A.
        boundary |= {"response", "writeback", "consumer", "commit_squash"}
    return sorted(na), sorted(boundary)


def assemble(act, fevs, summary, ctx_pool, parent_ev, model):
    out = {
        "root": _ev(act), "fault_id": None, "summary": None,
        "activation_trigger": None, "activation_basis": "",
        "mutation": None, "consume": None, "terminal": None,
        "translation": None, "request": None, "response": None,
        "consumer": None, "stages": {}, "edges": [], "unobserved": [],
        "not_applicable": [], "boundary": [], "notes": [],
        "faulted_event_count": 0, "cotemporal": None,
        "has_any_commit": False, "branches": [], "effect_branch_index": None,
        "completeness": {},
    }
    if act is None:
        out["unobserved"].append("activation")
        out["completeness"] = {
            "edges_explicit": True, "terminal_observed": False,
            "architecture_complete": False, "unobserved": ["activation"],
            "not_applicable": [],
        }
        return out

    fid = act.get("fault_id")
    out["fault_id"] = fid
    out["faulted_event_count"] = len(fevs)
    out["summary"] = _ev(summary)
    # any fault-tagged committing consumer (an architectural commit, regardless
    # of which transaction), used to distinguish masked vs squashed outcomes
    out["has_any_commit"] = any(kind(e) == "commit" and tid(e) for e in fevs)

    if parent_ev is not None:
        out["activation_trigger"] = _ev(parent_ev)
        out["activation_basis"] = "parent_event_id(%s)" % parent_ev.get(
            "event_id")

    mut_raw = None
    muts = MUTATION_KINDS.get(model, set())
    for e in fevs:
        if kind(e) in muts and (e.get("event_id") or 0) >= (act.get("event_id") or 0):
            mut_raw = e
            out["mutation"] = _ev(e)
            _add_edge(out, act, e)
            break

    # --- M07 fetch co-temporal join
    pe_raw = None
    if model == "M07" and act.get("mode") == "Execute" and not tid(act):
        exact, pool = find_cotemporal_permission_eval(ctx_pool, act)
        out["cotemporal"] = {
            "candidate_count": len(pool), "exact_match_count": len(exact),
            "permission_eval_event_id":
                exact[0].get("event_id") if exact else None,
        }
        if len(exact) == 1:
            pe_raw = exact[0]
            out["edges"].append({
                "type": "control", "basis": "cotemporal_key",
                "confidence": "high",
                "source": pe_raw.get("event_id"),
                "target": act.get("event_id"),
                "source_kind": kind(pe_raw), "target_kind": kind(act)})

    # --- multi-branch reconstruction: every consumer transaction (origin +
    # cross-dynamic reuses) is a branch of the same faulted state.
    branches = build_branches(fevs)
    eff_idx = select_effect_branch(branches, summary)
    eff = branches[eff_idx] if eff_idx is not None else None
    out["effect_branch_index"] = eff_idx
    out["branches"] = [branch_summary(b) for b in branches]
    if len(branches) > 1:
        out["notes"].append(
            "%d consumer branches of the same faulted state (translation_id "
            "fan-out); effect branch = %s" % (
                len(branches),
                eff.get("translation_id") if eff else None))

    # --- terminal selection on the effect branch, overridden by the tracer's
    # own `faulting_inst_squashed` signal so a transient (replay/wrong-path)
    # squash is never reported as the terminal of an SDC.
    term_raw, term_kind = resolve_terminal(eff, summary)
    tr = req = resp = wb = cons = None
    anchor = None
    if eff is not None:
        st = eff["stages"]
        tr, req, resp, wb, cons = (st["translation"], st["request"],
                                   st["response"], st.get("writeback"),
                                   st["consumer"])
        if eff.get("consume_event_id") is not None:
            anchor = next((e for e in fevs
                           if e.get("event_id") == eff["consume_event_id"]),
                          None)
    if term_raw is None and model == "M06":
        term_raw = next((e for e in fevs
                         if kind(e) == "exception_delivery"), None) or \
            next((e for e in fevs if kind(e) == "fault_result_propagated"), None)
        term_kind = kind(term_raw) if term_raw else None
    if term_raw is None:
        # natural unconsumed endpoint: the tracer emits an explicit witness
        # that the fault armed but no later access consumed it before the ROI
        # ended.  This is a real observed terminal, not a missing stage.
        term_raw = next((e for e in fevs
                         if kind(e) == "mmu_fault_unconsumed"), None)
    if term_raw is None:
        term_raw = next((e for e in fevs if kind(e) == "commit" and tid(e)),
                        None)
    if term_raw is None:
        term_raw = next((e for e in fevs if kind(e) == "squash"), None)
    if term_raw is None:
        term_raw = next((e for e in reversed(fevs)
                         if kind(e) == "lsu_request" and
                         e.get("mode") == "Execute"), None)
    if term_raw is not None:
        term_kind = kind(term_raw)

    out["consume"] = _ev(anchor)

    # M07 fetch downstream (fault_id=0): recover from the ctx_pool window via
    # the joined permission_eval's translation_id.
    if (tr is None and req is None) and pe_raw is not None:
        t2 = tid(pe_raw)
        for e in ctx_pool:
            if (e.get("event_id") or 0) <= (act.get("event_id") or 0):
                continue
            if kind(e) == "translation_result" and tid(e) == t2 and tr is None:
                tr = e
            if kind(e) == "lsu_request" and tid(e) == t2 and \
                    e.get("mode") == "Execute" and req is None:
                req = e
        if tr is not None:
            out["edges"].append({
                "type": "transaction", "basis": "translation_id",
                "confidence": "high",
                "source": pe_raw.get("event_id"),
                "target": tr.get("event_id"),
                "source_kind": kind(pe_raw), "target_kind": kind(tr)})

    if term_raw is not None and kind(term_raw) == "lsu_request":
        req = term_raw
    # fetch boundary: when the only effect recovered is the Execute lsu_request
    # (activation carries translation_id=0 and no branch exists), that request
    # is the observed terminal; the per-instruction IFU commit is NOT_EMITTED.
    if term_raw is None and req is not None and kind(req) == "lsu_request":
        term_raw = req
        term_kind = "lsu_request"
        out["notes"].append(
            "fetch boundary: the Execute lsu_request is the last observed "
            "effect stage; per-instruction IFU commit is "
            "NOT_EMITTED_BY_FROZEN_BINARY")

    out["translation"] = _ev(tr)
    out["request"] = _ev(req)
    out["response"] = _ev(resp)
    out["writeback"] = _ev(wb)
    out["consumer"] = _ev(cons)
    out["terminal"] = _ev(term_raw) if term_raw is not None else None

    # --- primary-path edges (temporally ordered, distinct)
    raw = {e.get("event_id"): e for e in fevs}
    if parent_ev is not None:
        raw[parent_ev.get("event_id")] = parent_ev
    if pe_raw is not None:
        raw[pe_raw.get("event_id")] = pe_raw

    ordered = ["root", "mutation", "consume", "translation", "request",
               "response", "writeback", "consumer", "terminal"]
    # retained-entry -> DTB-entry state hand-off (M01): insert the disarming
    # hit + DTB insert between mutation and consume so the cross-branch edge is
    # never left UNKNOWN when the trace carries the explicit bridge.
    handoff = mutation_handoff(mut_raw, fevs, anchor) \
        if mut_raw is not None else []
    out["state_transfer"] = [_ev(h) for h in handoff]
    evs = []
    seen_evids = set()
    for name in ordered:
        v = out.get(name)
        if not v:
            continue
        eid = v.get("event_id")
        if eid is None or eid in seen_evids:
            continue
        seen_evids.add(eid)
        evs.append(v)
    for h in handoff:
        eid = h.get("event_id")
        if eid is not None and eid not in seen_evids:
            seen_evids.add(eid)
            evs.append(_ev(h))
    evs.sort(key=lambda e: e.get("event_id") or 0)
    for i in range(len(evs) - 1):
        a, b = evs[i], evs[i + 1]
        if (a is out["root"] and not tid(raw.get(a.get("event_id"), a)) and
                out.get("cotemporal")):
            out["notes"].append(
                "activation carries translation_id=0; downstream transaction "
                "is joined via a co-temporal permission_eval, not a direct "
                "activation edge")
            continue
        ra = raw.get(a.get("event_id"), a)
        rb = raw.get(b.get("event_id"), b)
        already = any(x.get("source") == a.get("event_id") and
                      x.get("target") == b.get("event_id")
                      for x in out["edges"])
        if not already:
            _add_edge(out, ra, rb)

    # --- compressed stages.  `commit_squash` is only claimed when the terminal
    # really is an architectural commit/squash/detection — a fetch-boundary
    # lsu_request terminal must not be reported as the commit stage.
    TERMINAL_AS_COMMIT = {"commit", "squash", "exception_delivery",
                          "fault_result_propagated"}
    stages = {}
    for name in ("activation", "mutation", "translation", "request",
                 "response", "writeback", "consumer", "commit_squash"):
        src = {"activation": "root", "commit_squash": "terminal"}.get(name, name)
        v = out.get(src)
        if name == "commit_squash" and term_kind not in TERMINAL_AS_COMMIT:
            v = None
        if v:
            stages[name] = v
    out["stages"] = stages

    # --- declared not-applicable vs NOT_EMITTED boundary vs honest gap,
    # feeding the four-dimensional completeness record.
    masked_reason = (summary or {}).get("masked_reason")
    na, boundary = expected_stages(model, act, term_kind, masked_reason)
    out["not_applicable"] = na
    out["boundary"] = boundary
    if model == "M06":
        out["notes"].append(
            "M06 detection path: no LSU data request is expected; the "
            "architectural effect is the TranslationLL / exception delivery")
    if model in ("M07", "M08"):
        out["notes"].append(
            "%s carries its mutation inside the activation row "
            "(permission_before/after or request PA flip)" % model)
    if act.get("mode") == "Execute":
        out["notes"].append(
            "instruction-side (Execute) context: the frozen binary emits the "
            "MMU translation up to the Execute lsu_request; per-instruction "
            "IFU response/decode/commit are NOT_EMITTED_BY_FROZEN_BINARY")
    if term_kind == "lsu_request" and not act.get("mode") == "Execute":
        out["notes"].append(
            "effect reached the LSU request but no committing consumer is "
            "fault-tagged in the trace (committing read NOT_OBSERVED; "
            "terminal is the observed request, not a claimed commit)")

    for s in ALL_STAGES:
        if s not in stages and s not in na and s not in boundary:
            out["unobserved"].append(s)

    out["completeness"] = {
        "edges_explicit": not any(e.get("basis") == "UNKNOWN"
                                  for e in out["edges"]),
        "terminal_observed": term_raw is not None,
        # complete architecture propagation = every expected stage observed
        # with no declared NOT_EMITTED boundary and no raw gap
        "architecture_complete": (not out["unobserved"] and not boundary),
        "unobserved": list(out["unobserved"]),
        "not_applicable": list(na),
        "boundary": list(boundary),
        "effect_commits": bool(eff and eff["commits"]),
        "effect_terminal_kind": term_kind,
    }
    return out


def build_chain_from_path(path, model):
    act, fevs, summary, ctx_pool, parent_ev = collect(path)
    return assemble(act, fevs, summary, ctx_pool, parent_ev, model)


def build_chain(events, model):
    """Standalone / in-memory variant (full event list already loaded)."""
    act = None
    for e in events:
        if kind(e) in ACTIVATION_KINDS and e.get("fault_id"):
            act = e
            break
    if act is None:
        return assemble(None, [], None, [], None, model)
    fid = act.get("fault_id")
    fevs = [e for e in events if e.get("fault_id") == fid]
    summary = None
    for e in fevs:
        if kind(e) == "mmu_fault_summary":
            summary = e
            break
    if summary is None:
        for e in fevs:
            if kind(e) == "chain_end":
                summary = e
                break
    ap = act.get("parent_event_id")
    parent_ev = None
    if ap is not None:
        for e in events:
            if e.get("event_id") == ap:
                parent_ev = e
                break
    return assemble(act, fevs, summary, events, parent_ev, model)


def build_stage_map(chain):
    out = {}
    for name, ev in (chain.get("stages") or {}).items():
        if ev:
            out[name] = {
                "event_id": ev.get("event_id", ""),
                "tick": ev.get("tick", ""),
                "kind": ev.get("kind", ""),
            }
    return out


if __name__ == "__main__":
    import json
    import sys
    path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "M01"
    print(json.dumps(build_chain_from_path(path, model), indent=1, default=str))
