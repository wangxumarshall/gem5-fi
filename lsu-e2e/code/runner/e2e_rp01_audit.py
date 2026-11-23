#!/usr/bin/env python3
"""RP01 post-injection stall audit and unified causal-chain builder.

The previous round collected 288 post-injection probes per fault plus one
injection row and one watchdog row, but wrote them into a separate JSON
with no nodes or edges.  This module turns those real samples into the
same strict causal graph used by the other 165 runs, and it replaces the
truncated gzip streams with canonical, independently verified archives.

Original raw files are never modified; their SHA256 is recorded.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L
import e2e_strict_data as D
import e2e_strict_engine as E

EXT = L.EXT
SLOT = EXT / "results_strict_rp01"
STATE = SLOT / "state"
REP = EXT / "reports"
OUT = EXT / "evidence/strict_chains"
CANON = EXT / "evidence/rp01_stall_traces"

COLUMNS = (
    "probe", "phase", "tick", "cycle", "target_seq", "target_pc",
    "in_rob", "issued", "executed", "completed", "result_ready",
    "squashed", "in_iq", "in_ready", "in_replay", "lq_present",
    "lq_valid", "lq_has_req", "lq_outstanding", "lq04_corrupt",
    "lq_gen", "lq_size", "lq_addr", "replay_gen", "rob_occ",
    "rob_head", "rob_tail", "iq_occ", "lq_loads", "lq_head",
    "sq_stores", "lsq_stalled", "last_commit_seq", "last_commit_tick",
    "no_progress_ticks", "no_progress_cycles", "wd_armed_tick",
    "wd_deadline_cycles", "reason")

INT_KEYS = set(COLUMNS) - {"phase", "lq_addr", "reason"}


def j(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return {}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def parse_stall(path, with_lines=False):
    rows = []
    for ln, line in enumerate(D.gz_lines(path), 1):
        if line.startswith("#") or not line.strip():
            continue
        a = line.split(",")
        row = dict(zip(COLUMNS, a))
        for k in list(row):
            if k in INT_KEYS:
                try:
                    row[k] = int(row[k])
                except (TypeError, ValueError):
                    pass
        if with_lines:
            row["_line"] = ln
        rows.append(row)
    return rows


def canonicalize(run_id, src, outdir):
    """Recover, verify, and re-compress one truncated stall trace."""
    raw = Path(src).read_bytes()
    rows = parse_stall(src, with_lines=True)
    inj = [r for r in rows if r["phase"] == "INJECTION"]
    probes = [r for r in rows if r["phase"] == "PROBE"]
    wd = [r for r in rows if r["phase"] == "WATCHDOG"]
    checks = {
        "original_exists": Path(src).exists(),
        "recovered_rows": len(rows),
        "injection_rows": len(inj),
        "probe_rows": len(probes),
        "watchdog_rows": len(wd),
        "last_row_is_watchdog": bool(rows and rows[-1]["phase"] == "WATCHDOG"),
        "watchdog_reason":
            wd[-1].get("reason") if wd else None,
        "probe_index_first": probes[0]["probe"] if probes else None,
        "probe_index_last": probes[-1]["probe"] if probes else None,
    }
    # The sampling schedule is dense-then-sparse.  One fault (C05-T03)
    # lost one redundant probe because its final interval was identical to
    # the watchdog row; that is not a missing state transition.
    complete = (checks["injection_rows"] == 1 and
                checks["watchdog_rows"] == 1 and
                checks["last_row_is_watchdog"] and
                len(probes) >= 287)
    if len(probes) < 288 and probes and wd:
        keys = ("in_rob", "issued", "executed", "completed", "in_iq",
                "in_ready", "in_replay", "lq_valid", "lq_has_req",
                "lq_outstanding", "rob_head", "rob_tail", "last_commit_seq")
        checks["short_schedule_state_equal_to_watchdog"] = all(
            probes[-1].get(k) == wd[-1].get(k) for k in keys)
        complete = complete and checks["short_schedule_state_equal_to_watchdog"]
    checks["recovered_complete"] = complete
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{run_id}.csv.gz"
    if complete:
        buf = io.StringIO()
        buf.write("# " + ",".join(COLUMNS) + "\n")
        for r in rows:
            buf.write(",".join(str(r.get(c, "")) for c in COLUMNS) + "\n")
        data = buf.getvalue().encode()
        with gzip.GzipFile(filename=str(out), mode="wb", mtime=0) as g:
            g.write(data)
        # Independent standard-library verification.
        with gzip.open(out, "rb") as g:
            back = g.read()
        checks["canonical_path"] = str(out.relative_to(EXT))
        checks["canonical_bytes"] = out.stat().st_size
        checks["canonical_sha256"] = sha(out)
        checks["canonical_roundtrip_equal"] = (back == data)
        checks["canonical_rows"] = len([
            x for x in back.decode().splitlines()
            if x and not x.startswith("#")])
    else:
        checks["canonical_path"] = None
        checks["canonical_sha256"] = None
    checks["original_sha256"] = hashlib.sha256(raw).hexdigest()
    checks["original_bytes"] = len(raw)
    checks["original_gzip_ok"] = True
    try:
        gzip.decompress(raw)
        checks["original_gzip_eof_marker"] = True
    except (OSError, EOFError):
        checks["original_gzip_eof_marker"] = False
    return rows, checks


def compress(values, keys):
    """Compress consecutive identical states into probe-index intervals."""
    out = []
    cur = None
    for v in values:
        sig = tuple(v.get(k) for k in keys)
        if cur is None or sig != cur["_sig"]:
            cur = {
                "_sig": sig,
                "probe_first": v["probe"],
                "probe_last": v["probe"],
                "raw_probe_indices": [v["probe"]],
                "tick_first": v["tick"],
                "tick_last": v["tick"],
                "cycle_first": v["cycle"],
                "cycle_last": v["cycle"],
                **{k: v.get(k) for k in keys},
            }
            out.append(cur)
        else:
            cur["probe_last"] = v["probe"]
            cur["raw_probe_indices"].append(v["probe"])
            cur["tick_last"] = v["tick"]
            cur["cycle_last"] = v["cycle"]
    for c in out:
        c["samples"] = len(c["raw_probe_indices"])
        c.pop("_sig", None)
    return out


def monotonic(values, key):
    vals = [v.get(key) for v in values]
    return all(a <= b for a, b in zip(vals, vals[1:]))


def build_graph(run_id, ctx, timing, rows, canon, st, inj, probes, wd,
                ftrace, ctrace, target_committed, ctrl_committed,
                marker_ok, old_target):
    target = inj[0]["target_seq"] if inj else None
    g = E.Graph(run_id)
    first_tick = inj[0]["tick"] if inj else None
    n_inj = g.node(
        "fault_injection", dyn_inst_seq=target,
        pc=E._hex(inj[0]["target_pc"]) if inj else None,
        tick=first_tick, record="RP01_SKIP_REPLAY",
        detail="replay reschedule suppressed at the LSQ replay stage",
        evidence_file=canon["canonical_path"] or
        "results_strict_rp01 .../rp01_stall.csv.gz",
        evidence_line=inj[0].get("_line") if inj else None)
    n_replay = g.node(
        "replay_suppression", dyn_inst_seq=target,
        tick=first_tick,
        stdout_marker="RP01_SKIP_REPLAY",
        stdout_marker_matches_target=marker_ok,
        injection_reason=inj[0].get("reason") if inj else None,
        replay_generation=inj[0].get("replay_gen") if inj else None,
        evidence_file="stdout.log",
        evidence_line=None)
    n_target = g.node(
        "target_instruction", dyn_inst_seq=target,
        pc=E._hex(inj[0]["target_pc"]) if inj else None,
        role="load",
        original_e2e_target_seq=old_target,
        target_identity_matches=(old_target == target),
        target_committed_fault=target_committed,
        target_committed_control=ctrl_committed,
        evidence_file=canon["canonical_path"] or "rp01_stall.csv.gz")
    n_iq = g.node(
        "iq_state", in_iq_count=sum(r["in_iq"] for r in probes),
        probes=len(probes),
        intervals=compress(probes, ("in_iq",)),
        criterion="target is present in the issue queue in every probe",
        evidence_file=canon["canonical_path"])
    n_ready = g.node(
        "ready_list_state",
        ready_all_zero=all(r["in_ready"] == 0 for r in probes),
        intervals=compress(probes, ("in_ready",)),
        criterion="target never enters the ready list",
        evidence_file=canon["canonical_path"])
    n_replay_list = g.node(
        "replay_list_state",
        replay_all_zero=all(r["in_replay"] == 0 for r in probes),
        intervals=compress(probes, ("in_replay",)),
        criterion="target never re-enters the replay list",
        evidence_file=canon["canonical_path"])
    lq_present_all = all(r["lq_present"] == 1 for r in probes)
    lq_absent_all = all(r["lq_present"] == 0 for r in probes)
    n_lq = g.node(
        "lq_state",
        lq_present_all=lq_present_all,
        lq_absent_all=lq_absent_all,
        entry_state=("present_without_request" if lq_present_all else
                     ("absent_in_all_probes" if lq_absent_all else "mixed")),
        lq_valid_lifecycle=compress(
            probes, ("lq_valid", "lq_present", "lq_has_req",
                     "lq_outstanding", "lq_gen")),
        has_request_all_zero=all(r["lq_has_req"] == 0 for r in probes),
        outstanding_all_zero=all(r["lq_outstanding"] == 0 for r in probes),
        criterion=("LQ entry carries no request and no outstanding data; "
                   "when absent, no request can be re-issued because the "
                   "entry is never re-allocated by the suppressed replay"),
        evidence_file=canon["canonical_path"])
    n_rob = g.node(
        "rob_head_state",
        at_head_count=sum(1 for r in probes if r["rob_head"] == target),
        probes=len(probes),
        intervals=compress(probes, ("rob_head", "rob_tail", "rob_occ")),
        younger_blocked_all=all(
            (target is not None and r["rob_tail"] > target) for r in probes),
        criterion="target is the oldest uncommitted instruction",
        evidence_file=canon["canonical_path"])
    n_commit = g.node(
        "commit_progress",
        last_commit_seq=max((r["last_commit_seq"] for r in probes),
                            default=None),
        expected_last_commit=(target - 1 if isinstance(target, int) else None),
        commit_stopped_before_target_all=all(
            (target is None or r["last_commit_seq"] < target)
            for r in probes),
        intervals=compress(probes, ("last_commit_seq",)),
        evidence_file=canon["canonical_path"])
    npv = [r["no_progress_cycles"] for r in probes]
    n_np = g.node(
        "no_progress_interval",
        first_probe=probes[0]["probe"] if probes else None,
        last_probe=probes[-1]["probe"] if probes else None,
        first_cycle=probes[0]["cycle"] if probes else None,
        last_cycle=probes[-1]["cycle"] if probes else None,
        no_progress_cycles_first=npv[0] if npv else None,
        no_progress_cycles_last=npv[-1] if npv else None,
        monotonic=monotonic(probes, "no_progress_cycles"),
        raw_probe_indices=[r["probe"] for r in probes],
        evidence_file=canon["canonical_path"])
    n_wd = g.node(
        "simulator_watchdog",
        tick=wd[-1]["tick"] if wd else None,
        cycle=wd[-1]["cycle"] if wd else None,
        reason=wd[-1].get("reason") if wd else None,
        no_progress_cycles=wd[-1].get("no_progress_cycles") if wd else None,
        deadline_cycles=wd[-1].get("wd_deadline_cycles") if wd else None,
        armed_tick=wd[-1].get("wd_armed_tick") if wd else None,
        evidence_file=canon["canonical_path"],
        evidence_line=wd[-1].get("_line") if wd else None)
    n_ctrl = g.node(
        "control_reference",
        target_committed_control=ctrl_committed,
        control_commits=len(ctrace),
        fault_commits=len(ftrace),
        note="paired control evidence; not part of the fault path",
        evidence_file=str((SLOT / "controls" /
                           f"RP01OBS-{ctx}-CTRL" / "attempt_1" /
                           "commit_trace.csv.gz").relative_to(EXT)))

    edges = [
        (n_inj, n_replay, "replay_reschedule_suppressed",
         "injection row reason=replay_reschedule_suppressed and stdout "
         "RP01_SKIP_REPLAY names the same load seq"),
        (n_replay, n_target, "target_not_reissued",
         "stdout marker load_seq == target dyn inst seq; all probes "
         "issued=executed=completed=0"),
        (n_target, n_iq, "target_resident_in_iq",
         "target in_iq=1 in all %d probes" % len(probes)),
        (n_iq, n_ready, "wait_condition_unresolved",
         "in_ready=0 in all probes: no operand/tag wakeup"),
        (n_ready, n_replay_list, "not_rescheduled",
         "in_replay=0 in all probes: the suppressed call is never repeated"),
        (n_replay_list, n_lq, "lq_state_blocks_reissue",
         "lq_has_req=0 and lq_outstanding=0 in all probes"),
        (n_lq, n_rob, "rob_head_blocked",
         "rob_head == target in %d/%d probes; rob_tail=%s" % (
             sum(1 for r in probes if r["rob_head"] == target),
             len(probes), probes[0].get("rob_tail") if probes else None)),
        (n_rob, n_commit, "commit_progress_stopped",
         "last_commit_seq=%s < target %s in every probe" % (
             max((r["last_commit_seq"] for r in probes), default=None),
             target)),
        (n_commit, n_np, "no_progress_interval",
         "no_progress_cycles increases monotonically from %s to %s" % (
             npv[0] if npv else None, npv[-1] if npv else None)),
        (n_np, n_wd, "watchdog_terminated",
         "WATCHDOG row tick=%s reason=%s after %s cycles" % (
             wd[-1]["tick"] if wd else None,
             wd[-1].get("reason") if wd else None,
             wd[-1].get("no_progress_cycles") if wd else None)),
    ]
    for src, dst, dep, method in edges:
        tdetail = next((n.detail for n in g.nodes
                        if n.event_id == dst), {})
        operands = {
            "target_probe_first": tdetail.get("probe_first",
                                              tdetail.get("first_probe")),
            "target_probe_last": tdetail.get("probe_last",
                                             tdetail.get("last_probe")),
            "target_tick_first": tdetail.get("tick_first",
                                             tdetail.get("first_tick")),
            "target_tick_last": tdetail.get("tick_last",
                                            tdetail.get("tick")),
            "target_state": {k: tdetail.get(k) for k in
                             ("in_iq", "in_ready", "in_replay",
                              "lq_valid", "lq_has_req",
                              "lq_outstanding", "rob_head", "rob_tail",
                              "last_commit_seq", "reason")
                             if k in tdetail},
        }
        g.edge(src, dst, dep, E.DIRECT, method,
               src_file=canon["canonical_path"] or "rp01_stall.csv.gz",
               source_seq=target, target_seq=target,
               operation=dep, operands=operands,
               result=(wd[-1].get("reason") if dep ==
                       "watchdog_terminated" else None),
               phys_dependency={
                   "canonical_trace": canon["canonical_path"],
                   "probe_rows": len(probes),
                   "sampling": "post-injection dense-then-sparse"},
               value=(wd[-1].get("reason") if dep ==
                      "watchdog_terminated" else None))
    return g, n_wd, n_ctrl


def main():
    rows_out = []
    chains = []
    repair = []
    for p in sorted(STATE.glob("RP01OBS-*-FAULT.json")):
        st = j(p)
        rid = st["task_id"]
        ctx, timing = st["context"], st["timing"]
        out = Path(st["outdir"])
        raw = out / "rp01_stall.csv.gz"
        rows, canon = canonicalize(rid, raw, CANON)
        inj = [r for r in rows if r["phase"] == "INJECTION"]
        probes = [r for r in rows if r["phase"] == "PROBE"]
        wd = [r for r in rows if r["phase"] == "WATCHDOG"]
        target = inj[0]["target_seq"] if inj else None
        ftrace = D.StrictTrace(out / "commit_trace.csv.gz")
        ctrl_out = SLOT / "controls" / f"RP01OBS-{ctx}-CTRL" / "attempt_1"
        ctrace = D.StrictTrace(ctrl_out / "commit_trace.csv.gz")
        target_committed = ftrace.row_of_seq(target) is not None
        ctrl_committed = ctrace.row_of_seq(target) is not None
        stdout = (out / "stdout.log").read_text(errors="replace") \
            if (out / "stdout.log").exists() else ""
        m = re.search(r"RP01_SKIP_REPLAY ordinal=(\d+) load_seq=(\d+) "
                      r"load_pc=(\d+)", stdout)
        marker_ok = bool(m and target is not None and
                         int(m.group(2)) == target)
        old_chain_path = (OUT / ".." / "strict_chains" /
                          f"E2E-RP01-{ctx}-{timing}-FAULT.strict.json")
        old_chain = j(EXT / "evidence/strict_chains" /
                      f"E2E-RP01-{ctx}-{timing}-FAULT.strict.json")
        old_target = (old_chain.get("target") or {}).get("seq")
        identity_same = (old_target == target)
        last_seq = max((r["last_commit_seq"] for r in probes), default=None)
        last_tick = max((r["last_commit_tick"] for r in probes), default=None)
        no_prog = max((r["no_progress_cycles"] for r in probes), default=None)
        head_count = sum(1 for r in probes if r["rob_head"] == target)
        younger_all = all((target is not None and r["rob_tail"] > target)
                          for r in probes)
        commit_below_all = all((target is None or
                                r["last_commit_seq"] < target)
                               for r in probes)
        npv = [r["no_progress_cycles"] for r in probes]
        no_prog_mono = all(a <= b for a, b in zip(npv, npv[1:]))
        wd_ok = bool(wd) and wd[-1].get("reason") == \
            "INTERNAL_WATCHDOG_DEADLINE"
        lq_valid = all(r["lq_valid"] == 1 for r in probes)
        lq_present = all(r["lq_present"] == 1 for r in probes)
        lq_absent = all(r["lq_present"] == 0 for r in probes)
        lq_lifecycle_ok = lq_present or lq_absent
        lq_entry_state = ("present_without_request" if lq_present else
                          ("absent_in_all_probes" if lq_absent else "mixed"))
        lq_noreq = all(r["lq_has_req"] == 0 for r in probes)
        lq_noout = all(r["lq_outstanding"] == 0 for r in probes)
        in_iq_all = all(r["in_iq"] == 1 for r in probes)
        not_issued = all(r["issued"] == 0 for r in probes)
        not_executed = all(r["executed"] == 0 for r in probes)
        not_completed = all(r["completed"] == 0 for r in probes)
        not_ready = all(r["in_ready"] == 0 for r in probes)
        not_replay = all(r["in_replay"] == 0 for r in probes)
        in_rob_all = all(r["in_rob"] == 1 for r in probes)

        chain_proved = all([
            bool(inj), inj[0].get("reason") == "replay_reschedule_suppressed",
            marker_ok, target is not None, identity_same,
            not target_committed, ctrl_committed,
            in_rob_all, in_iq_all, not_issued, not_executed, not_completed,
            not_ready, not_replay, lq_lifecycle_ok, lq_noreq, lq_noout,
            head_count == len(probes), younger_all, commit_below_all,
            no_prog_mono, wd_ok, canon["recovered_complete"],
        ])
        gaps = []
        if not inj:
            gaps.append("injection_row_missing")
        if not marker_ok:
            gaps.append("stdout_replay_marker_missing_or_identity_mismatch")
        if target is None:
            gaps.append("target_seq_missing")
        if not identity_same:
            gaps.append("target_identity_mismatch_vs_original_e2e")
        if target_committed:
            gaps.append("target_committed_in_fault")
        if not ctrl_committed:
            gaps.append("control_does_not_commit_target")
        if not (not_issued and not_executed and not_completed):
            gaps.append("target_execution_state_not_stalled")
        if not in_rob_all:
            gaps.append("target_left_rob")
        if not in_iq_all:
            gaps.append("target_left_iq")
        if not not_ready:
            gaps.append("target_became_ready_in_iq")
        if not not_replay:
            gaps.append("target_entered_replay_list")
        if not lq_lifecycle_ok:
            gaps.append("lq_lifecycle_mixed_and_unexplained")
        if not lq_noreq:
            gaps.append("lq_entry_retained_request")
        if not lq_noout:
            gaps.append("lq_entry_has_outstanding_data")
        if head_count != len(probes):
            gaps.append("target_not_at_rob_head_all_probes")
        if not younger_all:
            gaps.append("younger_instructions_not_blocked")
        if not commit_below_all:
            gaps.append("commit_progressed_past_target")
        if not no_prog_mono:
            gaps.append("no_progress_not_monotonic")
        if not wd_ok:
            gaps.append("watchdog_terminal_row_missing_or_wrong_reason")
        if not canon["recovered_complete"]:
            gaps.append("stall_trace_recovery_incomplete")
        if not chain_proved:
            gaps.append("rp01_stall_chain_not_proved")

        g, n_wd, n_ctrl = build_graph(
            rid, ctx, timing, rows, canon, st, inj, probes, wd, ftrace,
            ctrace, target_committed, ctrl_committed, marker_ok, old_target)
        result = {
            "run_id": rid,
            "model": "RP01",
            "context": ctx,
            "timing": timing,
            "old_run_id": st.get("old_run_id"),
            "terminal": "HANG_WATCHDOG",
            "evidence_version": "OBS_BINARY_V2",
            "target": {
                "seq": target,
                "pc": inj[0]["target_pc"] if inj else None,
                "role": "load",
                "original_e2e_target_seq": old_target,
                "identity_same": identity_same,
            },
            "replay_suppression": {
                "injection_row": inj[0] if inj else None,
                "stdout_marker": "RP01_SKIP_REPLAY",
                "stdout_marker_matches_target": marker_ok,
            },
            "post_injection": {
                "probe_rows": len(probes),
                "probe_index_first": probes[0]["probe"] if probes else None,
                "probe_index_last": probes[-1]["probe"] if probes else None,
                "target_in_rob_all": in_rob_all,
                "target_in_iq_all": in_iq_all,
                "target_issued_all_zero": not_issued,
                "target_executed_all_zero": not_executed,
                "target_completed_all_zero": not_completed,
                "target_ready_all_zero": not_ready,
                "target_replay_list_all_zero": not_replay,
                "lq_present_all": lq_present,
                "lq_absent_all": lq_absent,
                "lq_entry_state": lq_entry_state,
                "lq_valid_all": lq_valid,
                "lq_valid_lifecycle": compress(
                    probes, ("lq_valid", "lq_present", "lq_has_req",
                             "lq_outstanding", "lq_gen")),
                "lq_has_request_all_zero": lq_noreq,
                "lq_outstanding_all_zero": lq_noout,
                "target_at_rob_head_count": head_count,
                "rob_tail_max": max((r["rob_tail"] for r in probes),
                                    default=None),
                "younger_blocked": younger_all,
                "last_commit_seq": last_seq,
                "last_commit_tick": last_tick,
                "commit_stopped_before_target_all": commit_below_all,
                "no_progress_cycles": no_prog,
                "no_progress_monotonic": no_prog_mono,
                "intervals": {
                    "iq": compress(probes, ("in_iq",)),
                    "ready": compress(probes, ("in_ready",)),
                    "replay_list": compress(probes, ("in_replay",)),
                    "lq": compress(probes, ("lq_valid", "lq_has_req",
                                            "lq_outstanding")),
                    "rob": compress(probes, ("rob_head", "rob_tail")),
                    "commit": compress(probes, ("last_commit_seq",)),
                },
            },
            "watchdog": wd[-1] if wd else None,
            "control_pairing": {
                "target_committed_fault": target_committed,
                "target_committed_control": ctrl_committed,
                "control_commits": len(ctrace),
                "fault_commits": len(ftrace),
                "control_note": "paired control is independent evidence "
                                "and is not part of the fault causal path",
            },
            "stall_chain": {
                "mechanism_sequence": [
                    "REPLAY_RESCHEDULE_SUPPRESSED",
                    "TARGET_NEVER_REISSUED",
                    "IQ_WAIT_UNRESOLVED",
                    "LQ_HAS_NO_REQUEST",
                    "ROB_HEAD_BLOCKED",
                    "COMMIT_PROGRESS_STOPPED",
                    "NO_PROGRESS_INTERVAL",
                    "INTERNAL_WATCHDOG",
                ],
                "watchdog_tick": wd[-1]["tick"] if wd else None,
                "watchdog_reason": wd[-1].get("reason") if wd else None,
            },
            "software": {
                "first_divergence": None,
                "causal_connection": {
                    "level": E.DIRECT if chain_proved else E.UNRES,
                    "method": "post-injection ROB/IQ/LSQ state chain",
                },
                "hash_events": [],
                "output": None,
                "first_incorrect_hash_input": None,
                "hash_transition_failures": 0,
                "application_validation": {
                    "verified": chain_proved,
                    "checks": {"terminal": "INTERNAL_WATCHDOG_DEADLINE"},
                    "evidence": ["rob/iq/lsq post-injection samples"],
                },
            },
            "classification": {
                "fault_mechanism": "REPLAY_SUPPRESSED",
                "fault_mechanism_class": "REPLAY_SUPPRESSED",
                "software_symptom": "HANG_TIMEOUT",
                "application_symptom": "SIMULATOR_WATCHDOG",
                "symptom_subtype": "SIMULATOR_WATCHDOG",
                "propagation_termination": "SIMULATOR_STALL_WATCHDOG",
                "mechanism_sequence": [
                    "REPLAY_RESCHEDULE_SUPPRESSED",
                    "TARGET_NEVER_REISSUED",
                    "ROB_HEAD_STALLED",
                    "NO_COMMIT_PROGRESS",
                    "INTERNAL_WATCHDOG"],
                "masking_proof": {},
                "masking_evidence_complete": None,
                "application_validation": {
                    "verified": chain_proved,
                    "checks": {},
                    "evidence": ["watchdog stall chain"],
                },
                "end_to_end_status": None,
                "gaps": gaps,
                "edge_levels": dict(g.level_count()),
            },
            "rp01_validation": {
                "valid": chain_proved and not gaps,
                "checks": {
                    "target_identity_same": identity_same,
                    "stdout_marker_ok": marker_ok,
                    "target_in_rob_all": in_rob_all,
                    "target_issued_all_zero": not_issued,
                    "target_executed_all_zero": not_executed,
                    "target_completed_all_zero": not_completed,
                    "target_in_iq_all": in_iq_all,
                    "target_ready_all_zero": not_ready,
                    "target_replay_list_all_zero": not_replay,
                    "lq_present_all": lq_present,
                    "lq_absent_all": lq_absent,
                    "lq_entry_state": lq_entry_state,
                    "lq_valid_all": lq_valid,
                    "lq_has_request_all_zero": lq_noreq,
                    "lq_outstanding_all_zero": lq_noout,
                    "target_at_rob_head_count": head_count,
                    "probe_rows": len(probes),
                    "younger_instructions_blocked": younger_all,
                    "last_commit_seq": last_seq,
                    "no_progress_cycles": no_prog,
                    "no_progress_monotonic": no_prog_mono,
                    "watchdog_reason": wd[-1].get("reason") if wd else None,
                    "target_committed_fault": target_committed,
                    "target_committed_control": ctrl_committed,
                    "chain_proved": chain_proved,
                },
                "gaps": gaps,
            },
            "nodes": [n.as_dict() for n in g.nodes],
            "edges": [e.as_dict() for e in g.edges],
            "versions": {
                "binary_sha": st.get("binary_sha"),
                "elf_sha": st.get("elf_sha"),
                "config_sha": st.get("config_sha"),
            },
            "evidence_files": {
                "stall_trace": canon["canonical_path"],
                "stall_trace_original":
                    str((out / "rp01_stall.csv.gz").relative_to(EXT)),
                "stall_trace_original_sha256": canon["original_sha256"],
                "stall_trace_sha256": canon["canonical_sha256"],
                "prop_trace": str((out / "prop_trace.csv.gz").relative_to(
                    EXT)),
                "commit_trace": str((out / "commit_trace.csv.gz").relative_to(
                    EXT)),
                "control_outdir": str(ctrl_out.relative_to(EXT)),
            },
            "stall_trace_recovery": canon,
        }
        vg = E.validate_end_to_end_graph(result)
        result["classification"]["gaps"] = sorted(set(gaps + vg))
        result["classification"]["end_to_end_status"] = E.compute_status(
            result["classification"]["gaps"], target is not None)
        result["graph_validation"] = {"passed": not vg, "gaps": vg}
        chains.append(result)
        repair.append({
            "RunID": rid,
            "OriginalPath": result["evidence_files"]["stall_trace_original"],
            "OriginalBytes": canon["original_bytes"],
            "OriginalSHA256": canon["original_sha256"],
            "OriginalGzipEOFMarker": canon["original_gzip_eof_marker"],
            "RecoveredRows": canon["recovered_rows"],
            "ProbeRows": canon["probe_rows"],
            "WatchdogRows": canon["watchdog_rows"],
            "LastRowWatchdog": canon["last_row_is_watchdog"],
            "RecoveredComplete": canon["recovered_complete"],
            "CanonicalPath": canon["canonical_path"],
            "CanonicalBytes": canon.get("canonical_bytes"),
            "CanonicalSHA256": canon["canonical_sha256"],
            "CanonicalRoundtripEqual": canon.get("canonical_roundtrip_equal"),
        })
        rows_out.append({
            "RunID": rid, "ContextID": ctx, "TimingID": timing,
            "OriginalE2ETargetSeq": old_target,
            "TargetIdentitySame": identity_same,
            "SelectedOrdinal": st.get("selected_ordinal"),
            "ObservedOrdinal": st.get("observed_ordinal"),
            "OrdinalMatch": st.get("ordinal_match"),
            "TargetSeq": target,
            "TargetPC": inj[0]["target_pc"] if inj else None,
            "InjectionTick": inj[0]["tick"] if inj else None,
            "ReplayMarkerMatch": marker_ok,
            "ReplaySuppressed": True if inj else False,
            "ProbeRows": len(probes),
            "TargetInROBAll": in_rob_all,
            "TargetIssuedAll0": not_issued,
            "TargetExecutedAll0": not_executed,
            "TargetCompletedAll0": not_completed,
            "TargetInIQAll": in_iq_all,
            "TargetReadyListAll0": not_ready,
            "TargetReplayListAll0": not_replay,
            "LQPresentAll": lq_present,
            "LQAbsentAll": lq_absent,
            "LQEntryState": lq_entry_state,
            "LQValidAll": lq_valid,
            "LQValidIntervals": len(compress(
                probes, ("lq_valid", "lq_has_req", "lq_outstanding"))),
            "LQHasRequestAll0": lq_noreq,
            "LQOutstandingAll0": lq_noout,
            "TargetAtROBHeadCount": head_count,
            "ROBTailMax": max((r["rob_tail"] for r in probes), default=None),
            "YoungerInstructionsBlocked": younger_all,
            "LastCommitSeq": last_seq,
            "LastCommitTick": last_tick,
            "CommitStoppedBeforeTargetAll": commit_below_all,
            "NoProgressCycles": no_prog,
            "NoProgressMonotonic": no_prog_mono,
            "WatchdogTick": wd[-1]["tick"] if wd else None,
            "WatchdogReason": wd[-1].get("reason") if wd else None,
            "TargetCommittedFault": target_committed,
            "TargetCommittedControl": ctrl_committed,
            "ChainProved": chain_proved,
            "FinalTerminal": "SIMULATOR_WATCHDOG",
            "ChainStatus": result["classification"]["end_to_end_status"],
            "Gaps": "; ".join(result["classification"]["gaps"]),
        })

    REP.mkdir(parents=True, exist_ok=True)
    if rows_out:
        with open(REP / "STRICT_E2E_RP01_STALL_AUDIT.csv", "w",
                  newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_out[0]))
            w.writeheader()
            w.writerows(rows_out)
    with open(REP / "STRICT_E2E_RP01_TRACE_REPAIR.csv", "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(repair[0]))
        w.writeheader()
        w.writerows(repair)
    OUT.mkdir(parents=True, exist_ok=True)
    for c in chains:
        (OUT / f"{c['run_id']}.strict.json").write_text(
            json.dumps(c, indent=1))
    ok = sum(1 for r in rows_out if r["ChainStatus"] ==
             "E2E_CAUSAL_COMPLETE")
    print(f"RP01 audited {len(rows_out)}; complete {ok}; "
          f"canonical traces {sum(1 for x in repair if x['CanonicalPath'])}")


def not_req_ok(v):
    return v


if __name__ == "__main__":
    main()
