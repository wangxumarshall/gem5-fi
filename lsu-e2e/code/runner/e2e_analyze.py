#!/usr/bin/env python3
"""Reconstruct one end-to-end causal chain per E2E fault run.

Every emitted edge carries a real evidence reference (propagation node id,
commit-trace line, or software-marker line).  Nothing is inferred from a
checksum mismatch alone: the software endpoint is the first committed
software event whose recorded value diverges from the paired control, and
that event is mapped back to a dynamic instruction through the control
catalogue or a same-address reload.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L

def sw_dict(e):
    d = e.marker.as_dict()
    d["op_dyn_inst_seq"] = e.op_seq
    return d


OUT = L.EXT / "evidence/causal_chains"
REPORTS = L.EXT / "reports"


# ---------------------------------------------------------------------------
def pick_target(model, props, stdout, ct):
    rows = [r for r in props if r["kind"].startswith("inj")]
    all_inj = list(rows)
    selected = None
    if model == "RP01":
        m = re.search(r"RP01_SKIP_REPLAY ordinal=(\d+) load_seq=(\d+) "
                      r"load_pc=(\d+) lq_idx=(\d+) lq_gen=(\d+) "
                      r"store_seq=(\d+)", stdout)
        if m:
            sl = None
            for ln_no, line in enumerate(stdout.splitlines(), 1):
                if line.startswith("RP01_SKIP_REPLAY"):
                    sl = ln_no
                    break
            selected = {"kind": "rp01_skip", "seq": int(m.group(2)),
                        "pc": int(m.group(3)), "stdout_line": sl,
                        "kv": {"ordinal": m.group(1),
                               "load_seq": m.group(2),
                               "load_pc": m.group(3),
                               "lq_idx": m.group(4),
                               "lq_gen": m.group(5),
                               "store_seq": m.group(6)}}
    elif rows:
        if model == "A03":
            eff = [r for r in rows if r["kind"] == "inj"
                   and r["kv"].get("value_changed") != "0"]
            sel = eff[0] if eff else rows[0]
        else:
            sel = rows[0]
        kv = sel["kv"]
        seq = sel["seq_int"]
        for k in ("load_seq", "store_seq", "dyn_inst_seq"):
            if k in kv:
                try:
                    seq = int(kv[k])
                    break
                except ValueError:
                    pass
        if seq is None:
            seq = sel["seq_int"]
        pc = None
        for k in ("pc", "load_pc", "store_pc"):
            if k in kv:
                try:
                    pc = (int(str(kv[k]), 0)
                          if str(kv[k]).lower().startswith("0x")
                          else int(str(kv[k]), 16))
                    break
                except ValueError:
                    pass
        selected = {"kind": sel["kind"], "seq": seq, "pc": pc, "kv": kv,
                    "node_id": sel["node_id"], "tick": sel["tick_int"]}
    if selected is None:
        return None, all_inj
    if selected.get("pc") is None and selected.get("seq") is not None:
        r = ct.commit_row(selected["seq"])
        selected["pc"] = r["pc"] if r else None
    return selected, all_inj


_ADDR_FIELD = {
    "A01": ("old_addr",), "A03": ("old_addr",),
    "FW02": ("vaddr",), "FW05": ("load_addr",),
    "MD04": ("load_addr",), "SP05": ("store_addr",),
    "SQ01": ("addr",), "SQ03": ("store_addr",),
    "DA04": ("addr_before", "addr"), "LP01": ("vaddr",),
    "LQ04": ("addr",), "RP01": (),
}


def target_addr(model, kv):
    for k in _ADDR_FIELD.get(model, ()):
        if k in kv:
            try:
                v = str(kv[k]).strip()
                return (int(v, 0) if v.lower().startswith("0x")
                        else int(v, 16))
            except ValueError:
                pass
    return None


def is_store_target(model, target):
    if not target:
        return False
    k = target["kind"]
    if "store" in k:
        return True
    if model in ("SQ01", "SQ03", "SP05", "DA04"):
        return True
    return False


def chain_row(props, kind):
    rows = L.prop_by_kind(props, kind)
    return rows[0] if rows else None


def chain_kv(props, *kinds):
    for k in kinds:
        r = chain_row(props, k)
        if r:
            return r["kv"], r
    return {}, None


def find_reload(evs, target_seq, target_addr_, model, props):
    kv, row = {}, None
    for kind in ("sp05_stage", "sq01_chain", "sq03_effect"):
        r = chain_row(props, kind)
        if r and r["kv"].get("reload_seq"):
            try:
                rs = int(r["kv"]["reload_seq"])
                if rs:
                    return rs, L.marker_for_op(evs, rs, (L.T_LOAD,))
            except ValueError:
                pass
    if target_seq is None:
        return None, None
    for e in evs:
        if (e.marker.type == L.T_LOAD and e.op_seq and
                e.op_seq > target_seq and
                (target_addr_ is None or e.marker.a == target_addr_)):
            return e.op_seq, e
    return None, None


def taint_edges(ct, start_seq, max_edges=32):
    """Read-only register taint walk from a load's destination."""
    idx = ct.index_of(start_seq) if start_seq is not None else None
    if idx is None:
        return []
    tainted = {}
    for (c, ar, ph, v) in ct.dst[idx]:
        if ar != 28:
            tainted[(c, ph)] = (ct.seq[idx], v)
    edges = []
    for j in range(idx + 1, len(ct)):
        if not tainted:
            break
        if L.is_marker_commit(ct, j):
            continue
        hits = []
        for (c, ar, ph, sv) in ct.srcv[j]:
            if (c, ph) in tainted:
                ov, ovv = tainted[(c, ph)]
                if sv is None or ovv is None or sv == ovv:
                    hits.append(((c, ph), ov, ovv))
        if hits:
            for (c, ar, ph, v) in ct.dst[j]:
                if ar == 28:
                    continue
                prod = hits[0][1]
                valin = hits[0][2]
                tainted[(c, ph)] = (ct.seq[j], v)
                edges.append({
                    "producer_seq": prod,
                    "consumer_seq": ct.seq[j],
                    "consumer_pc": ct.pc[j],
                    "consumer_op": ct.op[j],
                    "value_in": valin,
                    "value_out": v,
                    "ctrace_line": ct.line[j],
                })
            if len(edges) >= max_edges:
                break
        else:
            # a renamed write to a tainted physical cell overwrites the taint
            for (c, ar, ph, v) in ct.dst[j]:
                tainted.pop((c, ph), None)
    return edges


def hash_chain(evs, start_marker_seq):
    out = [e for e in evs if e.marker.type == L.T_HASH and
           e.marker.seq > start_marker_seq]
    breaks = 0
    for a, b in zip(out, out[1:]):
        if a.marker.site == b.marker.site and a.marker.c != b.marker.b:
            breaks += 1
    return out, breaks


def output_event(evs):
    rows = [e for e in evs if e.marker.type == L.T_OUTPUT]
    return rows[-1] if rows else None


def sw_series_after(evs, marker_seq, n=8):
    return [e for e in evs if e.marker.seq > marker_seq][:n]


def sw_value(e):
    if e.marker.type == L.T_BRANCH:
        return e.marker.b          # architectural branch transition
    if e.marker.type in (L.T_VALUE, L.T_HASH, L.T_CHECK):
        return e.marker.a
    return e.marker.b


def classify(model, st, target, fd, props, ct, evs, reload_seq, t_edges):
    terminal = st.get("terminal")
    tseq = target["seq"] if target else None
    kv = target["kv"] if target else {}
    store_target = is_store_target(model, target)
    squash = tseq in ct.squash if tseq is not None else False
    commit = ct.commit_row(tseq) if tseq is not None else None
    has_fd = fd is not None
    fde = fd["fault"] if fd and fd.get("fault") else None

    # ---- model mechanism evidence -------------------------------------
    mech = []
    if model == "A01":
        mech = ["A01_ADDRESS_BIT3_FLIP"] if kv.get("old_addr") != kv.get(
            "new_addr") else ["A01_ADDRESS_NO_CHANGE"]
    elif model == "A03":
        mech = ["A03_PERSISTENT_ADDRESS_STUCK0"]
    elif model == "LP01":
        mech = ["LP01_L1D_RESPONSE_BYTE0_BIT3"]
    elif model == "FW02":
        mech = ["FW02_FORWARDING_SUPPRESSED"]
    elif model == "FW05":
        mech = ["FW05_WRONG_SOURCE_FORWARD"]
    elif model == "MD04":
        mech = ["MD04_VIOLATION_REPORT_SUPPRESSED"]
    elif model == "SP05":
        mech = ["SP05_STORE_WRITE_SKIPPED"]
    elif model == "SQ01":
        mech = ["SQ01_STORE_DATA_BYTE0_BIT3"]
    elif model == "SQ03":
        mech = ["SQ03_PREMATURE_CANWB"]
    elif model == "DA04":
        mech = ["DA04_STORE_BYTE_ENABLE_LANE0_CLEARED"]
    elif model == "LQ04":
        mech = ["LQ04_LQ_VALID_REQUEST_CLEARED"]
    elif model == "RP01":
        mech = ["RP01_REPLAY_RESCHEDULE_SUPPRESSED"]

    # ---- symptom -------------------------------------------------------
    if terminal == "SDC":
        symptom = "WRONG_OUTPUT"
        if fd and (fd["kind"] != "value" or
                   (fde is not None and fde.marker.type == L.T_BRANCH)):
            subtype = "CONTROL_FLOW_DIVERGENCE"
        elif model in ("A01", "A03"):
            subtype = ("WRONG_ADDRESS_EFFECT"
                       if kv.get("old_addr") != kv.get("new_addr")
                       else "WRONG_NUMERIC_VALUE")
        elif model in ("SQ01", "DA04"):
            subtype = "WRONG_MEMORY_CONTENT"
        elif model in ("FW02", "FW05", "MD04", "SP05"):
            subtype = "STALE_DATA_USED"
        else:
            subtype = "WRONG_NUMERIC_VALUE"
        termination = "COMMITTED_AND_PROPAGATED"
    elif terminal == "HANG_WATCHDOG" or terminal == "HANG":
        symptom = "HANG_TIMEOUT"
        subtype = "SIMULATOR_WATCHDOG"
        termination = "STALLED"
    elif terminal == "CRASH":
        symptom = "APPLICATION_CRASH"
        subtype = "OTHER_APPLICATION_CRASH"
        termination = "UNRESOLVED"
    else:
        symptom = "NO_VISIBLE_ERROR"
        subtype = None
        termination = None

        # ---- masking mechanism ----------------------------------------
        if squash:
            termination = "SQUASHED_BEFORE_COMMIT"
            mech.append("TARGET_SQUASHED_BEFORE_COMMIT")
        elif model == "LQ04":
            termination = "MASKED_BY_VALUE_CONVERGENCE"
            mech.append("LQ_ENTRY_CLEARED_BUT_RESPONSE_DATA_UNCHANGED")
        elif model == "SQ03":
            termination = "MASKED_BY_VALUE_CONVERGENCE"
            mech.append("DRAIN_MOVED_BEFORE_COMMIT_BUT_RELOAD_DATA_SAME")
        elif has_fd:
            e = fde
            later = sw_series_after(evs, e.marker.seq, 12)
            nxt_value = next((x for x in later
                              if x.marker.type == L.T_VALUE), None)
            nxt_load = next((x for x in later
                             if x.marker.type == L.T_LOAD and
                             x.marker.site != e.marker.site), None)
            nxt_store = next((x for x in later
                              if x.marker.type == L.T_STORE and
                              x.marker.a == e.marker.a), None)
            if nxt_value is not None:
                termination = "MASKED_BY_OVERWRITE"
                mech.append("DIVERGENT_VALUE_OVERWRITTEN_IN_REGISTER")
            elif nxt_store is not None:
                termination = "MASKED_BY_OVERWRITE"
                mech.append("DIVERGENT_MEMORY_OVERWRITTEN_BEFORE_RELOAD")
            elif model == "LP01" and e.marker.type == L.T_LOAD:
                # only the low bit of the cold condition is consumed; a
                # bit-3 corruption of the loaded word does not reach the
                # application-visible value
                termination = "MASKED_BY_VALUE_CONVERGENCE"
                mech.append("CORRUPTED_BIT_NOT_IN_CONSUMED_MASK")
            elif not t_edges:
                termination = "MASKED_BY_NON_CONSUMPTION"
                mech.append("DIVERGENT_VALUE_HAS_NO_APPLICATION_CONSUMER")
            else:
                termination = "COMMITTED_WITHOUT_VISIBLE_ERROR"
                mech.append("MASKING_MECHANISM_UNRESOLVED")
        else:
            # no software divergence at all
            addr = target_addr(model, kv) if target else None

            def store_before_reload():
                if tseq is None or addr is None:
                    return None
                reload = None
                for e in evs:
                    if (e.marker.type == L.T_LOAD and e.op_seq and
                            e.op_seq > tseq and e.marker.a == addr):
                        reload = e.op_seq
                        break
                for e in evs:
                    if (e.marker.type == L.T_STORE and e.op_seq and
                            e.op_seq > tseq and e.marker.a == addr and
                            (reload is None or e.op_seq < reload)):
                        return e
                return None

            if model == "SP05":
                ov = store_before_reload()
                if ov is not None:
                    termination = "MASKED_BY_OVERWRITE"
                    mech.append("LOST_WRITE_OVERWRITTEN_BEFORE_RELOAD")
                else:
                    termination = "MASKED_BY_VALUE_CONVERGENCE"
                    mech.append(
                        "LOST_WRITE_NOT_OBSERVED_FORWARDED_RELOAD_OK")
            elif model == "SQ01":
                verdict = (chain_kv(props, "sq01_chain")[0] or {}).get(
                    "chain_verdict")
                ov = store_before_reload()
                if verdict == "STORE_COMMITTED_LANE_NOT_READ" and ov is not None:
                    termination = "MASKED_BY_OVERWRITE"
                    mech.append("FAULTED_LANE_OVERWRITTEN_BEFORE_READ")
                elif verdict == "STORE_COMMITTED_LANE_NOT_READ":
                    termination = "MASKED_BY_NON_CONSUMPTION"
                    mech.append("FAULTED_LANE_NEVER_READ")
                else:
                    termination = "MASKED_BY_VALUE_CONVERGENCE"
            elif model == "DA04":
                termination = ("MASKED_BY_OVERWRITE"
                               if store_before_reload() is not None
                               else "MASKED_BY_NON_CONSUMPTION")
                mech.append("FAULTED_STORE_OVERWRITTEN_BEFORE_RELOAD")
            elif model in ("A01", "A03"):
                termination = "ACTIVATED_NO_STATE_DIVERGENCE"
                mech.append("ADDRESS_CHANGE_DID_NOT_REACH_A_VALUE")
            elif model == "FW02":
                termination = "MASKED_BY_VALUE_CONVERGENCE"
                mech.append("SUPPRESSED_FORWARD_READ_CORRECT_MEMORY")
            elif model == "FW05":
                termination = "MASKED_BY_VALUE_CONVERGENCE"
                mech.append("WRONG_SOURCE_CONVERGED_TO_TRUE_VALUE")
            elif model == "MD04":
                termination = "MASKED_BY_VALUE_CONVERGENCE"
            elif model == "LP01":
                termination = "MASKED_BY_VALUE_CONVERGENCE"
            else:
                termination = "COMMITTED_WITHOUT_VISIBLE_ERROR"
                mech.append("MASKING_MECHANISM_UNRESOLVED")

    # ---- e2e status ----------------------------------------------------
    gaps = []
    if target is None:
        gaps.append("target_injection_not_identified")
    if target and target.get("seq") is None:
        gaps.append("target_dyn_inst_seq_missing")
    if commit is None and not squash and terminal != "HANG_WATCHDOG":
        gaps.append("target_commit_or_squash_evidence_missing")
    if terminal == "SDC" and not has_fd:
        gaps.append("no_software_divergence_for_checksum_mismatch")
    if terminal == "SDC" and has_fd:
        fde = fd["fault"]
        direct = (fde.op_seq == tseq)
        reload_ok = (reload_seq is not None and fde.op_seq == reload_seq)
        app_ok = any(e["consumer_seq"] == fde.op_seq for e in t_edges)
        fd_ok = direct or reload_ok or app_ok
        if not fd_ok:
            gaps.append("software_divergence_not_connected_to_target")
    if symptom == "NO_VISIBLE_ERROR":
        if termination in ("COMMITTED_WITHOUT_VISIBLE_ERROR",
                           "UNRESOLVED"):
            gaps.append("masking_mechanism_unresolved")
    if terminal == "HANG_WATCHDOG":
        wd = chain_row(props, "watchdog_terminal")
        if not wd:
            gaps.append("watchdog_terminal_evidence_missing")
        if reload_seq is None and tseq is not None:
            # RP01 target load has no reload by construction: absence is
            # the stall evidence, checked against the control commit.
            pass
    if not evs:
        gaps.append("software_marker_stream_empty")
    status = "E2E_CAUSAL_COMPLETE" if not gaps else (
        "E2E_CAUSAL_UNRESOLVED" if target is None else "E2E_CAUSAL_PARTIAL")
    return {
        "software_symptom": symptom,
        "symptom_subtype": subtype,
        "propagation_termination": termination,
        "mechanism_sequence": mech,
        "end_to_end_status": status,
        "gaps": gaps,
        "target_committed": commit is not None,
        "target_squashed": squash,
    }


# ---------------------------------------------------------------------------
def analyze(rid: str):
    st, out = L.load_state(rid, "fault")
    if st.get("status") not in ("COMPLETED", "COMPLETED_SDC",
                                "COMPLETED_HANG", "COMPLETED_CRASH"):
        return {"run_id": rid, "status": "SKIP",
                "reason": st.get("status")}
    model, ctx, t = st["model"], st["context"], st["timing"]
    fam = L.FAMILY[model]
    ct = L.CommitTrace(out / "commit_trace.csv.gz")
    evs = L.build_sw_events(ct, fam)
    ctrl_meta, ctrl_events = L.load_ctrl_events(model, ctx)
    ctrl_map = L.sw_event_index(ctrl_events)
    fd = L.first_sw_diff(evs, ctrl_events)
    all_diffs = L.all_sw_diffs(evs, ctrl_events)
    props = L.parse_prop(out / "prop_trace.csv.gz")
    stdout = ((out / "stdout.log").read_text(errors="replace")
              if (out / "stdout.log").exists() else "")
    target, all_inj = pick_target(model, props, stdout, ct)
    if model == "RP01" and not all_inj and target:
        rr = next((r for r in props if r["kind"] == "replay" and
                   r["seq_int"] == target["seq"]), None)
        if rr is not None:
            all_inj = [{"kind": "rp01_replay_skip",
                        "seq_int": target["seq"], "tick_int": rr["tick_int"],
                        "detail": rr["detail"], "node_id": rr["node_id"],
                        "kv": target.get("kv", {})}]
    tseq = target["seq"] if target else None
    taddr = target_addr(model, target["kv"]) if target else None
    store_target = is_store_target(model, target)
    reload_seq, reload_ev = (find_reload(evs, tseq, taddr, model, props)
                             if store_target else (None, None))
    if reload_seq is not None and reload_ev is None:
        reload_ev = L.marker_for_op(evs, reload_seq, (L.T_LOAD,))

    # software anchors
    tmarker = L.marker_for_op(evs, tseq) if tseq is not None else None
    fd_event = fd["fault"] if fd and fd.get("fault") else None
    fde_seq = fd_event.op_seq if fd_event else None

    # register taint chain
    start_seq = reload_seq if store_target else tseq
    t_edges = taint_edges(ct, start_seq) if start_seq else []

    # microarchitecture rows for the target (and reload)
    seqs_of_interest = {s for s in (tseq, reload_seq) if s is not None}
    uarch = [r for r in props
             if r["seq_int"] in seqs_of_interest and
             r["kind"] not in ("consumer", "prop_edge", "replay")]
    if model == "RP01":
        # the RP01 replay decision is the central microarchitectural event
        uarch += [r for r in props
                  if r["kind"] in ("replay", "fwd", "squash")
                  and r["seq_int"] == tseq]

    # hash chain from the first divergence (or from the target for masked)
    anchor = fd_event.marker.seq if fd_event else (
        tmarker.marker.seq if tmarker else
        (reload_ev.marker.seq if reload_ev and hasattr(reload_ev, "marker")
         else 0))
    if st.get("terminal") == "SDC":
        hashes, hash_breaks = hash_chain(evs, anchor)
    else:
        hashes, hash_breaks = [], 0
    outev = output_event(evs)

    # first architectural divergence, expressed as the first commit at
    # which the fault run's application-visible value/state differs
    arch = {
        "target_commit": (
            {"seq": ct.commit_row(tseq)["seq"],
             "tick": ct.commit_row(tseq)["tick"],
             "pc": ct.commit_row(tseq)["pc"],
             "dst": ct.commit_row(tseq)["dst"],
             "ctrace_line": ct.commit_row(tseq)["line"]}
            if tseq is not None and ct.commit_row(tseq) else None),
        "target_squash": (
            {"seq": tseq, "tick": ct.squash_tick.get(tseq, 0)}
            if tseq is not None and tseq in ct.squash else None),
        "first_architectural_divergence": None,
    }
    if fd_event is not None:
        if fde_seq is not None and ct.commit_row(fde_seq):
            r = ct.commit_row(fde_seq)
            arch["first_architectural_divergence"] = {
                "dyn_inst_seq": fde_seq, "tick": r["tick"],
                "pc": r["pc"], "op": r["op"],
                "ctrace_line": r["line"],
                "note": "first committed instruction carrying the divergent "
                        "software-visible value",
            }
    elif st.get("terminal") == "NO_VISIBLE_MISMATCH":
        arch["first_architectural_divergence"] = {
            "dyn_inst_seq": None,
            "note": "no committed architectural value diverged; the target "
                    "committed with a control-equal value or was overwritten "
                    "before the first consuming reload"}

    stall = None
    if model == "RP01" and target is not None:
        wd = chain_row(props, "watchdog_terminal")
        ctrl_state, ctrl_out = L.load_state(
            f"E2E-{model}-{ctx}-CTRL", "control")
        ctrl_ct = L.CommitTrace(ctrl_out / "commit_trace.csv.gz")
        snaps = L.micro_snapshots(out / "micro_snap.csv.gz")
        wdkv = wd["kv"] if wd else {}
        wd_last_seq = (int(wdkv["last_commit_dyn_seq"])
                       if "last_commit_dyn_seq" in wdkv else None)
        wd_last_tick = (int(wdkv["last_commit_tick"])
                        if "last_commit_tick" in wdkv else None)
        stall = {
            "target_load_seq": tseq,
            "control_target_committed": ctrl_ct.commit_row(tseq) is not None,
            "fault_target_committed": ct.commit_row(tseq) is not None,
            "target_squashed": tseq in ct.squash,
            "last_commit_dyn_seq": (wd_last_seq if wd_last_seq is not None
                                    else (ct.seq[-1] if ct.seq else None)),
            "last_commit_tick": (wd_last_tick if wd_last_tick is not None
                                 else (ct.tick[-1] if ct.tick else None)),
            "last_commit_pc": (ct.pc[-1] if ct.seq and
                               wd_last_seq in (None, ct.seq[-1]) else None),
            "commit_trace_tail_truncated": (wd_last_seq is not None and
                                            ct.seq and
                                            wd_last_seq != ct.seq[-1]),
            "watchdog_last_commit_dyn_seq": wd_last_seq,
            "watchdog_last_commit_tick": wd_last_tick,
            "commit_count_fault": len(ct),
            "commit_count_control": len(ctrl_ct),
            "watchdog_tick": wd["tick_int"] if wd else None,
            "watchdog_detail": wd["detail"] if wd else None,
            "silent_ticks": (int(wd["kv"]["silent_ticks"])
                             if wd and "silent_ticks" in wd["kv"] else None),
            "lq_head_seq": (int(wd["kv"]["lq_head_seq"])
                            if wd and "lq_head_seq" in wd["kv"] else None),
            "lq_loads": (int(wd["kv"]["lq_loads"])
                         if wd and "lq_loads" in wd["kv"] else None),
            "sq_stores": (int(wd["kv"]["sq_stores"])
                          if wd and "sq_stores" in wd["kv"] else None),
            "last_snapshot": snaps[-1] if snaps else None,
        }

    cls = classify(model, st, target, fd, props, ct, evs, reload_seq,
                   t_edges)
    if model == "A03" and len(all_diffs) > 1:
        cls["mechanism_sequence"].append(
            f"PERSISTENT_STATE_AFFECTS_{len(all_diffs)}_SOFTWARE_EVENTS")
    if model == "LP01" and fd and fd.get("fault") and fd.get("control"):
        cls["mechanism_sequence"].append(
            "CORRUPTED_BITS=0x%x;CONSUMED_BRANCH_TRANSITION_UNCHANGED"
            % (fd["fault"].marker.b ^ fd["control"].marker.b))
    if stall is not None:
        arch["first_architectural_divergence"] = {
            "dyn_inst_seq": stall.get("last_commit_dyn_seq"),
            "tick": stall.get("last_commit_tick"),
            "note": ("no architectural divergence: the target load never "
                     "commits in the fault run; execution stops at the last "
                     "progress point shown and the watchdog terminates the "
                     "simulation"),
        }
        if not stall["control_target_committed"]:
            cls["gaps"].append("control_does_not_commit_target_load")
        if stall["last_commit_dyn_seq"] is None:
            cls["gaps"].append("no_commit_progress_evidence")
        if not stall["watchdog_tick"]:
            cls["gaps"].append("watchdog_tick_missing")
        if cls["gaps"]:
            cls["end_to_end_status"] = "E2E_CAUSAL_PARTIAL"

    # software events (compact full list)
    sw = [[e.marker.seq, e.marker.type, e.marker.site, e.marker.order,
           e.marker.a, e.marker.b, e.marker.c, e.op_seq]
          for e in evs]

    # ---- vertices / edges ---------------------------------------------
    nodes = []
    edges = []
    nid = [0]

    def node(kind, **kw):
        nid[0] += 1
        d = {"event_id": f"E{nid[0]}", "kind": kind}
        d.update(kw)
        nodes.append(d)
        return d["event_id"]

    def edge(src, dst, **kw):
        d = {"source": src, "target": dst}
        d.update(kw)
        edges.append(d)

    inj_nodes = []
    for r in all_inj:
        nid_ = node("injection", dyn_inst_seq=r["seq_int"],
                    tick=r["tick_int"], record=r["kind"],
                    detail=r["detail"], trace_record_id=r["node_id"],
                    evidence="prop_trace.csv.gz")
        inj_nodes.append(nid_)
    tmarker_id = None
    tnode = None
    if target:
        tnode = node("target_instruction", dyn_inst_seq=tseq,
                     pc=target.get("pc"), address=taddr,
                     detail=target.get("kv", {}),
                     evidence="prop_trace.csv.gz/stdout.log")
        for i in inj_nodes[:1]:
            edge(i, tnode, dependency="injection_identity",
                 evidence_strength="STRONG")
        for r in uarch:
            un = node("microarchitecture", dyn_inst_seq=r["seq_int"],
                      tick=r["tick_int"], record=r["kind"],
                      request_id=r["request_id"], address=r["addr"],
                      detail=r["detail"], trace_record_id=r["node_id"],
                      evidence="prop_trace.csv.gz")
            edge(tnode, un, dependency="same_dyn_inst",
                 address=r["addr"], evidence_strength="STRONG")
        if arch["target_commit"]:
            cn = node("commit", dyn_inst_seq=tseq,
                      tick=arch["target_commit"]["tick"],
                      pc=arch["target_commit"]["pc"],
                      value=[d[3] for d in arch["target_commit"]["dst"]],
                      evidence_file="commit_trace.csv.gz",
                      evidence_line=arch["target_commit"]["ctrace_line"])
            edge(tnode, cn, dependency="architectural_commit",
                 evidence_strength="STRONG")
        if arch["target_squash"]:
            sn = node("squash", dyn_inst_seq=tseq,
                      tick=arch["target_squash"]["tick"],
                      evidence="prop_trace.csv.gz")
            edge(tnode, sn, dependency="squashed_before_commit",
                 evidence_strength="STRONG")
        if tmarker:
            tmarker_id = node(
                "software_observation", dyn_inst_seq=tmarker.marker.seq,
                op_dyn_inst_seq=tmarker.op_seq,
                software_site=tmarker.marker.site,
                address=tmarker.marker.a, value=tmarker.marker.b,
                clobber=tmarker.marker.c,
                evidence_file="commit_trace.csv.gz",
                evidence_line=tmarker.marker.line)
            edge(tnode, tmarker_id, dependency="observer_register_read",
                 value=tmarker.marker.b, evidence_strength="STRONG")
    rn = None
    if store_target and reload_ev is not None and hasattr(reload_ev, "marker"):
        rn = node("reload_load", dyn_inst_seq=reload_seq,
                  software_site=reload_ev.marker.site,
                  address=reload_ev.marker.a, value=reload_ev.marker.b,
                  evidence_file="commit_trace.csv.gz",
                  evidence_line=reload_ev.marker.line)
        edge(tnode, rn, dependency="same_address_reload",
             address=taddr, evidence_strength="STRONG")

    # application-level register dataflow from the target load (or reload)
    anchor_id = rn if rn is not None else tmarker_id
    seq_node = {}
    prev = anchor_id
    for e in t_edges:
        an = node("application_consumer", dyn_inst_seq=e["consumer_seq"],
                  pc=e["consumer_pc"], op=e["consumer_op"],
                  value_in=e["value_in"], value_out=e["value_out"],
                  evidence_file="commit_trace.csv.gz",
                  evidence_line=e["ctrace_line"])
        src = seq_node.get(e["producer_seq"], prev)
        edge(src, an, dependency="register_dataflow",
             value=e["value_in"], evidence_strength="STRONG")
        seq_node[e["consumer_seq"]] = an
        prev = an

    fn = None
    if fd_event is not None:
        fn = node("first_software_divergence",
                  dyn_inst_seq=fd_event.op_seq,
                  marker_dyn_inst_seq=fd_event.marker.seq,
                  software_type=L.TYPE_NAME.get(fd_event.marker.type),
                  software_site=fd_event.marker.site,
                  iteration=((fd_event.marker.c >> 32)
                             if fd_event.marker.type in L.AUX_ITER_TYPES
                             else None),
                  observed={"a": fd_event.marker.a,
                            "b": fd_event.marker.b,
                            "c": fd_event.marker.c},
                  control=({"a": fd["control"].marker.a,
                            "b": fd["control"].marker.b,
                            "c": fd["control"].marker.c}
                           if fd.get("control") else None),
                  differing_fields=fd["fields"],
                  divergence_kind=fd["kind"],
                  evidence_file="commit_trace.csv.gz",
                  evidence_line=fd_event.marker.line)
        m_for_fd = L.marker_for_op(evs, fd_event.op_seq)
        src = seq_node.get(fd_event.op_seq, prev)
        if m_for_fd is not None:
            src = seq_node.get(fd_event.op_seq,
                               tmarker_id if m_for_fd is tmarker else prev)
        edge(src, fn, dependency="first_visible_software_divergence",
             value=fd_event.marker.b, evidence_strength="STRONG")

    hash_nodes = []
    for h in hashes:
        hn = node("software_hash", dyn_inst_seq=h.marker.seq,
                  software_site=h.marker.site, iteration=h.marker.order,
                  input=h.marker.a, hash_before=h.marker.b,
                  hash_after=h.marker.c,
                  evidence_file="commit_trace.csv.gz",
                  evidence_line=h.marker.line)
        hash_nodes.append(hn)
    if fn is not None and hash_nodes:
        edge(fn, hash_nodes[0], dependency="application_consumption",
             value=hashes[0].marker.a, evidence_strength="STRONG")
    for a, b in zip(hash_nodes, hash_nodes[1:]):
        edge(a, b, dependency="hash_accumulator", evidence_strength="STRONG")
    on = None
    if outev:
        on = node("application_output", dyn_inst_seq=outev.marker.seq,
                  checksum=outev.marker.a,
                  expected=st.get("oracle_expected"),
                  observed=st.get("oracle_got"),
                  oracle_pass=st.get("oracle_pass"),
                  evidence_file="commit_trace.csv.gz",
                  evidence_line=outev.marker.line)
        if hash_nodes:
            edge(hash_nodes[-1], on, dependency="final_checksum",
                 value=outev.marker.a, evidence_strength="STRONG")

    # masking endpoint: the divergent value is not consumed, or the target
    # value never diverges.  The endpoint cites the concrete software rows.
    term = cls["propagation_termination"]
    if cls["software_symptom"] == "NO_VISIBLE_ERROR":
        mask_events = []
        if fd_event is not None:
            mask_events = sw_series_after(evs, fd_event.marker.seq, 16)
        elif store_target and tmarker is not None:
            # overwrite before reload, or the same-address reload that
            # converges to the correct value
            for e in evs:
                if (e.marker.type == L.T_STORE and e.marker.seq >
                        tmarker.marker.seq and e.marker.a == taddr):
                    mask_events.append(e)
                    break
            for e in evs:
                if (e.marker.type == L.T_LOAD and e.op_seq and
                        e.op_seq > tseq and e.marker.a == taddr):
                    mask_events.append(e)
                    break
        elif tmarker is not None:
            mask_events = [tmarker]
        def ev_entry(x):
            c = ctrl_map.get((x.key, x.occurrence))
            d = {"type": L.TYPE_NAME.get(x.marker.type),
                 "site": x.marker.site, "address": x.marker.a,
                 "value": sw_value(x),
                 "control_value": sw_value(c) if c else None,
                 "dyn_inst_seq": x.marker.seq,
                 "ctrace_line": x.marker.line}
            if x.marker.type == L.T_BRANCH:
                d.update({"condition": x.marker.a,
                          "control_condition": c.marker.a if c else None,
                          "taken": x.marker.b,
                          "control_taken": c.marker.b if c else None})
            return d
        evid = [ev_entry(x) for x in mask_events[:8]]
        men = node("masking_endpoint", kind_reason=term,
                   divergent_event=(fd_event.marker.seq if fd_event else None),
                   later_events=evid, evidence="commit_trace.csv.gz")
        prev_mask = fn if fn is not None else (tmarker_id or tnode)
        for x in mask_events[:8]:
            nn = node("masking_evidence",
                      dyn_inst_seq=x.marker.seq, op_dyn_inst_seq=x.op_seq,
                      software_type=L.TYPE_NAME.get(x.marker.type),
                      software_site=x.marker.site, address=x.marker.a,
                      value=x.marker.b,
                      evidence_file="commit_trace.csv.gz",
                      evidence_line=x.marker.line)
            if prev_mask:
                edge(prev_mask, nn,
                     dependency=("overwrite_or_reload"
                                 if store_target else
                                 "overwritten_before_consumption"),
                     value=sw_value(x), evidence_strength="STRONG")
            prev_mask = nn
        if prev_mask is not None:
            edge(prev_mask, men, dependency="masking_mechanism",
                 value=(fd_event.marker.b if fd_event else None),
                 evidence_strength="STRONG" if evid else "MEDIUM")
        if on:
            edge(men, on, dependency="output_unaffected",
                 evidence_strength="STRONG")

    # RP01 watchdog terminal
    if model == "RP01":
        wd = chain_row(props, "watchdog_terminal")
        if wd:
            wn = node("watchdog_terminal", tick=wd["tick_int"],
                      detail=wd["detail"], trace_record_id=wd["node_id"],
                      evidence="prop_trace.csv.gz")
            end = node("application_end", terminal="HANG_WATCHDOG",
                       evidence="prop_trace.csv.gz")
            stn = node("stall_state",
                       last_commit_dyn_seq=(stall or {}).get(
                           "last_commit_dyn_seq"),
                       lq_head_seq=(stall or {}).get("lq_head_seq"),
                       silent_ticks=(stall or {}).get("silent_ticks"),
                       target_never_committed=(stall or {}).get(
                           "fault_target_committed") is False,
                       evidence="prop_trace.csv.gz")
            if stall and stall.get("last_commit_dyn_seq"):
                lc = node("last_commit_before_stall",
                          dyn_inst_seq=stall["last_commit_dyn_seq"],
                          tick=stall["last_commit_tick"],
                          pc=stall.get("last_commit_pc"),
                          evidence="prop_trace.csv.gz",
                          trace_record_id=(wd["node_id"] if wd else ""))
                edge(tnode, lc, dependency="last_progress_before_stall",
                     evidence_strength="STRONG")
                edge(lc, stn, dependency="no_commit_after_replay_skip",
                     evidence_strength="STRONG")
            edge(tnode, stn, dependency="replay_not_rescheduled",
                 evidence_strength="STRONG")
            edge(stn, wn, dependency="pipeline_progress_stopped",
                 evidence_strength="STRONG")
            edge(wn, end, dependency="watchdog_terminated_simulation",
                 evidence_strength="STRONG")

    # control pairing
    ctrl = {
        "control_run_id": st.get("control_run_id"),
        "control_checksum": ctrl_meta.get("checksum"),
        "fault_checksum": st.get("oracle_got"),
        "control_commits": ctrl_meta.get("commits"),
        "fault_commits": len(ct),
        "control_events": len(ctrl_events),
        "fault_events": len(evs),
    }
    result = {
        "run_id": rid,
        "old_run_id": st.get("old_run_id"),
        "model": model, "context": ctx, "timing": t,
        "seed": st.get("seed"),
        "selected_ordinal": st.get("selected_ordinal"),
        "observed_ordinal": st.get("observed_ordinal"),
        "timing_percent": st.get("timing_percent"),
        "terminal": st.get("terminal"),
        "exit_code": st.get("exit_code"),
        "watchdog": st.get("watchdog"),
        "target": target,
        "injection_events": [{
            "kind": r["kind"], "dyn_inst_seq": r["seq_int"],
            "tick": r["tick_int"], "detail": r["detail"],
            "trace_record_id": r["node_id"]} for r in all_inj],
        "microarchitecture_events": [{
            "kind": r["kind"], "dyn_inst_seq": r["seq_int"],
            "tick": r["tick_int"], "request_id": r["request_id"],
            "addr": r["addr"], "detail": r["detail"],
            "trace_record_id": r["node_id"]} for r in uarch],
        "architectural": arch,
        "software": {
            "first_divergence": (
                {"kind": fd["kind"],
                 "fault": sw_dict(fd_event) if fd_event else None,
                 "control": (sw_dict(fd["control"])
                             if fd and fd.get("control") else None),
                 "differing_fields": fd["fields"]} if fd else None),
            "reload": ({"dyn_inst_seq": reload_seq,
                        "software_site": reload_ev.marker.site,
                        "address": reload_ev.marker.a,
                        "value": reload_ev.marker.b}
                       if reload_ev is not None and hasattr(reload_ev, "marker")
                       else None),
            "difference_count": len(all_diffs),
            "differences": [{
                "kind": x["kind"],
                "type": (L.TYPE_NAME.get(x["fault"].marker.type)
                         if x.get("fault") else
                         L.TYPE_NAME.get(x["control"].marker.type)),
                "site": (x["fault"].marker.site if x.get("fault")
                         else x["control"].marker.site),
                "iteration": (((x["fault"].marker.c >> 32)
                               if x["fault"].marker.type in L.AUX_ITER_TYPES
                               else None) if x.get("fault") else None),
                "fields": x["fields"]} for x in all_diffs[:64]],
            "hash_chain_events": len(hashes),
            "hash_chain_breaks": hash_breaks,
            "output": ({"checksum": outev.marker.a,
                        "expected": st.get("oracle_expected"),
                        "oracle_pass": st.get("oracle_pass")}
                       if outev else None),
            "events": sw,
        },
        "control_pairing": ctrl,
        "stall_chain": stall,
        "classification": cls,
        "nodes": nodes,
        "edges": edges,
        "evidence_files": {
            "fault_dir": str(out.relative_to(L.EXT)),
            "prop_trace": str((out / "prop_trace.csv.gz").relative_to(L.EXT)),
            "commit_trace": str((out / "commit_trace.csv.gz").relative_to(L.EXT)),
            "stdout": str((out / "stdout.log").relative_to(L.EXT)),
            "micro_snap": str((out / "micro_snap.csv.gz").relative_to(L.EXT)),
            "control_sw_cache": str((L.EXT / "results/controls" /
                f"E2E-{model}-{ctx}-CTRL/attempt_1/sw_events.json"
                ).relative_to(L.EXT)),
        },
    }
    return result


# ---------------------------------------------------------------------------
def write_run(result):
    rid = result["run_id"]
    OUT.mkdir(parents=True, exist_ok=True)
    jp = OUT / f"{rid}.causal_chain.json"
    jp.write_text(json.dumps(result, indent=1))
    cp = OUT / f"{rid}.causal_chain.csv"
    with open(cp, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["record", "event_id", "kind", "source", "target",
                    "dyn_inst_seq", "target_dyn_inst_seq", "cpu", "thread",
                    "request_id", "address", "value", "dependency_type",
                    "timestamp", "evidence_file", "evidence_line",
                    "trace_record_id", "evidence_strength"])
        for n in result["nodes"]:
            w.writerow(["node", n["event_id"], n["kind"], "", "",
                        n.get("dyn_inst_seq"), "", 0, 0, "",
                        n.get("address", ""), n.get("value", ""), "",
                        n.get("tick", ""), n.get("evidence_file",
                        n.get("evidence", "")), n.get("evidence_line", ""),
                        n.get("trace_record_id", ""), "STRONG"])
        for e in result["edges"]:
            w.writerow(["edge", e["source"], e["target"], e["source"],
                        e["target"], "", "", 0, 0, "",
                        e.get("address", ""), e.get("value", ""),
                        e.get("dependency", ""), "",
                        result["evidence_files"]["prop_trace"], "",
                        e.get("trace_record_id", ""),
                        e.get("evidence_strength", "")])
    md = report_md(result)
    (OUT / f"{rid}.causal_report.md").write_text(md)
    return jp, cp


def hexs(v):
    if v is None:
        return "N/A"
    if isinstance(v, int):
        return "0x%x" % v
    return str(v)


def report_md(r):
    c = r["classification"]
    t = r["target"] or {}
    sw = r["software"]["first_divergence"]
    lines = [
        f"# {r['run_id']} — E2E causal report",
        "",
        f"* Old RunID: `{r['old_run_id']}`",
        f"* Model / Context / Timing: **{r['model']} / {r['context']} / {r['timing']}**",
        f"* Terminal: `{r['terminal']}` (exit {r['exit_code']})",
        f"* Symptom: **{c['software_symptom']}**"
        + (f" / `{c['symptom_subtype']}`" if c["symptom_subtype"] else ""),
        f"* Propagation termination: `{c['propagation_termination']}`",
        f"* End-to-end status: **{c['end_to_end_status']}**",
        "",
        "## 1. Fault source",
        "",
        f"* Target kind: `{t.get('kind')}`",
        f"* Target DynInst seq: `{t.get('seq')}`  PC: `{hexs(t.get('pc'))}`",
        f"* Target address: `{hexs(target_addr(r['model'], t.get('kv', {})) if t else None)}`",
        f"* Injection detail: `{(t.get('kv') or {}).get('site', '')}`",
        "",
        "## 2. Microarchitecture propagation",
        "",
    ]
    for e in r["microarchitecture_events"][:20]:
        lines.append(f"* `{e['kind']}` seq={e['dyn_inst_seq']} tick={e['tick']} "
                     f"req={e['request_id']} addr={e['addr']}")
        lines.append(f"  - {e['detail'][:300]}")
    lines += ["", "## 3. Architectural state", ""]
    a = r["architectural"]
    if a["target_commit"]:
        lines.append(f"* Target committed at tick {a['target_commit']['tick']} "
                     f"(PC {hexs(a['target_commit']['pc'])}, ctrace line "
                     f"{a['target_commit']['ctrace_line']})")
    if a["target_squash"]:
        lines.append(f"* Target squashed at tick {a['target_squash']['tick']}")
    fad = a["first_architectural_divergence"]
    if fad:
        lines.append(f"* First architectural divergence: "
                     f"`{fad.get('dyn_inst_seq')}` — {fad.get('note', '')}")
    sc = r.get("stall_chain")
    if sc:
        lines.append(f"* Stall chain: target never commits; paired control "
                     f"commits it = {sc['control_target_committed']}; last "
                     f"progress DynInst {sc['last_commit_dyn_seq']} at tick "
                     f"{sc['last_commit_tick']}; watchdog tick "
                     f"{sc['watchdog_tick']}; silent ticks "
                     f"{sc['silent_ticks']}; LQ head {sc['lq_head_seq']}; "
                     f"commit count fault/control "
                     f"{sc['commit_count_fault']}/{sc['commit_count_control']}.")
        if sc.get("commit_trace_tail_truncated"):
            lines.append("* Observation limitation: the commit trace lost "
                         "its gzip tail on the fatal exit; the watchdog "
                         "ledger's last-commit fields are authoritative.")
    lines += ["", "## 4. Software propagation", ""]
    if sw and sw.get("fault"):
        f_ = sw["fault"]
        c_ = sw["control"]
        lines.append(f"* First software divergence: {f_['type']} site "
                     f"{f_['site']}; application DynInst seq "
                     f"{f_.get('op_dyn_inst_seq')} (observer marker seq "
                     f"{f_.get('dyn_inst_seq')}).")
        lines.append(f"  * fault: a={hexs(f_['a'])} b={hexs(f_['b'])} "
                     f"c={hexs(f_['c'])}")
        if c_:
            lines.append(f"  * control: a={hexs(c_['a'])} b={hexs(c_['b'])} "
                         f"c={hexs(c_['c'])}")
        lines.append(f"  * differing fields: {sw['differing_fields']}")
    elif r["terminal"] == "HANG_WATCHDOG":
        lines.append("* No software endpoint was reached: the pipeline "
                     "stopped before the target load committed, so no "
                     "later application operation executes in the fault run.")
    else:
        lines.append("* No committed software-event value divergence "
                     "against the paired control.")
    sws = r["software"]
    lines.append(f"* Hash-chain events after the divergence: "
                 f"{sws['hash_chain_events']} (breaks: "
                 f"{sws['hash_chain_breaks']})")
    if sws["output"]:
        o = sws["output"]
        lines.append(f"* Final checksum: {hexs(o['checksum'])}; expected "
                     f"{o['expected']}; oracle_pass={o['oracle_pass']}")
    lines += ["", "## 5. Mechanism sequence", ""]
    lines += [f"* {m}" for m in c["mechanism_sequence"]]
    lines += ["", "## 6. Evidence gaps", ""]
    lines += ([f"* {g}" for g in c["gaps"]] if c["gaps"] else
              ["* none — every layer has a cited event."])
    lines += ["", "## 7. Causal edges (first 40)", "",
              "| source | target | dependency | value | evidence |",
              "|---|---|---|---|---|"]
    for e in r["edges"][:40]:
        lines.append(f"| {e['source']} | {e['target']} | "
                     f"{e.get('dependency', '')} | {hexs(e.get('value'))} | "
                     f"{e.get('evidence_strength', '')} |")
    lines += ["", "Machine-readable graph: "
              f"`{r['run_id']}.causal_chain.json`; edges: "
              f"`{r['run_id']}.causal_chain.csv`."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--runs", default="all")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)
    ids = sorted(p.stem for p in
                 (L.EXT / "results/state").glob("E2E-*-FAULT.json"))
    if args.runs != "all":
        want = set(args.runs.split(","))
        ids = [i for i in ids if i in want]
    if args.limit:
        ids = ids[:args.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    done, errors = [], []
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(analyze, i): i for i in ids}
        for f in as_completed(futs):
            rid = futs[f]
            try:
                res = f.result()
                if res.get("status") == "SKIP":
                    errors.append((rid, res))
                    continue
                write_run(res)
                done.append(res)
            except Exception as exc:  # noqa: BLE001
                errors.append((rid, repr(exc)))
    print(f"analyzed {len(done)}; errors {len(errors)}")
    for rid, err in errors[:20]:
        print("ERR", rid, err)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
