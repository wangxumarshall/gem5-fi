#!/usr/bin/env python3
"""Negative/positive tests for the authorized O-F5 Timeout/livelock acceptance.

The tool is a SEPARATE acceptance axis; these tests pin that it rejects:
  * truncated evidence,
  * a Timeout with no causal evidence,
  * an unconsumed/pending fault,
  * a successful STXR after injection,
  * chain_end not at the observation boundary,
  * non-Timeout outcomes (no generic auto-certification).
"""
import gzip
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "lsu_o_f5_livelock_accept.py")
REAL_DIR = "/home/sdc/gem5-fi-ding/runs/lsu/r6_o_unit/f5_diag_20261103_r2"


def _ev(fid, kind, eid, tick, **kw):
    fields = {"kind": kind, "run_id": "O02-F5-W7", "sample_run_id": "s1",
              "fault_id": str(fid), "event_id": str(eid), "tick": str(tick),
              "core_id": "0"}
    fields.update({k: str(v) for k, v in kw.items()})
    return "PROP-EVT: " + " ".join(f"{k}={v}" for k, v in fields.items())


def make_case(tmp, *, outcome="timeout", truncate=False, pending=False,
              success_after=False, bad_end=False, guest_final=False,
              both_cores=True, analysis_capped=False, n=4):
    diag = os.path.join(tmp, "diag")
    cell = os.path.join(diag, "O02-F5-W7")
    seed = os.path.join(cell, "seed1")
    os.makedirs(seed, exist_ok=True)
    inj_ticks = [1000 + i * 6000 for i in range(n)]
    fail_ticks = [t + 100 for t in inj_ticks]
    final = fail_ticks[-1] + 100
    lines = []
    faults = {}
    eid = 0
    for i in range(n):
        fid = i + 1
        lines.append(_ev(fid, "inj", eid, inj_ticks[i], before="835e4000",
                         after="835e4040", corr="origin")); eid += 1
        lines.append(_ev(fid, "addr_form", eid, inj_ticks[i], parent_event_id=eid - 1,
                         before="835e4000", after="835e4040", corr="origin")); eid += 1
        lines.append(_ev(fid, "exmon_monitor", eid, inj_ticks[i], parent_event_id=eid - 1,
                         field="o02_monitor_state_fake", before="835e4000",
                         after="835e4040", state_before="1", state_after="1")); eid += 1
        if pending and i == n - 1:
            faults[str(fid)] = {"terminal": "provable_to_L1_then_unknown",
                                "provable_to": "L1", "edges": {}, "event_count": 4}
        else:
            lines.append(_ev(fid, "exmon_rmw", eid, fail_ticks[i], parent_event_id=eid - 1,
                             field="reservation_compare", state_before="reserved",
                             state_after="mismatch_fail")); eid += 1
            st = "success" if (success_after and i == n - 1) else "fail_retry"
            lines.append(_ev(fid, "exmon_stxr", eid, fail_ticks[i], parent_event_id=eid - 1,
                             field="stxr_consume", state_before="reserved", state_after=st,
                             detection_layer="L3", contained="1",
                             outcome="corrupted_monitor_blocks_sc", corr="addr_fallback")); eid += 1
            faults[str(fid)] = {"terminal": "detected_contained", "provable_to": "L2",
                                "edges": {}, "event_count": 5}
        end_tick = final + (1 if (bad_end and i == 0) else 0)
        lines.append(_ev(fid, "chain_end", eid, end_tick, parent_event_id=eid - 1,
                         contained="0", outcome="run_end", corr="none")); eid += 1
    with gzip.open(os.path.join(seed, "prop_evt.txt.gz"), "wt") as f:
        f.write("\n".join(lines) + "\n")
    if truncate:
        p = os.path.join(seed, "prop_evt.txt.gz")
        data = open(p, "rb").read()
        open(p, "wb").write(data[: len(data) // 2])
    with gzip.open(os.path.join(seed, "prop_trace.csv.gz"), "wt") as f:
        f.write("")
    with open(os.path.join(seed, "stats.txt"), "w") as f:
        f.write(f"simTicks 2200000000\nsimInsts 59000000\nfinalTick {final}\n")
        if both_cores:
            f.write("board.processor.cores0.core.instsIssued 49000000\n")
            f.write("board.processor.cores1.core.instsIssued 18000000\n")
        else:
            f.write("board.processor.cores0.core.instsIssued 49000000\n")
    term = "LITMUS free atomic nproc=2 rounds=8 incr_per_core=2\n"
    if guest_final:
        term += "FINAL=6b39e7aaa74b663f\nLITMUS free end\n"
    open(os.path.join(seed, "board.terminal"), "w").write(term)
    open(os.path.join(seed, "run.err"), "w").write(
        "TIMEOUT triggered=True graceful=True signal=None exit=0 "
        "(budget 1200s exhausted; child finalized on SIGINT — evidence complete)\n")
    open(os.path.join(seed, "exmon_injections.log"), "w").write(
        "".join(f"Tick: {t}, faults_injected: {i+1}\n" for i, t in enumerate(inj_ticks)))
    classes = {"Masked": 0, "Detected/Contained": 0, "SDC": 0, "Crash": 0, "Timeout": 0}
    if outcome == "timeout":
        classes["Timeout"] = n
    else:
        classes[outcome] = n
    json.dump({"runid": "O02-F5-W7", "activated": n, "classes": classes},
              open(os.path.join(cell, "cell_results.json"), "w"))
    report = {"oracle_outcome": classes.get("Timeout") and "Timeout" or outcome,
              "truncated": False, "evidence_truncated": False, "event_count": eid,
              "admitted": True, "certified": True,
              "terminal": "detected_contained", "provable_to": "L2",
              "faults": faults}
    if analysis_capped:
        # Raw gzip is complete; only the analyzer capped at EVENT_CAP=200000.
        report.update({"truncated": True, "evidence_truncated": True,
                       "event_count": 200000,
                       "truncation_reason": "prop_evt prop_evt.txt.gz incomplete "
                                            "gzip stream (EOF before the end-of-"
                                            "stream marker; run killed mid-write)"})
    json.dump(report, open(os.path.join(seed, "chain_report.json"), "w"))
    open(os.path.join(diag, "started_at_epoch"), "w").write("1000")
    open(os.path.join(diag, "ended_at_epoch"), "w").write("1100")
    return diag


def run_tool(diag):
    out = os.path.join(diag, "acceptance.json")
    cp = subprocess.run(
        [sys.executable, TOOL, "--diag-dir", diag, "--run-id", "O02-F5-W7",
         "--seed", "1", "--out-json", out, "--golden-ticks-per-sec", "10000000",
         "--min-injections", "2", "--min-failures", "2"],
        capture_output=True, text=True, timeout=60)
    return cp.returncode, json.load(open(out)) if os.path.exists(out) else None


def test_valid_timeout_livelock_accepted():
    with tempfile.TemporaryDirectory() as tmp:
        rc, res = run_tool(make_case(tmp))
    assert rc == 0
    assert res["axes"]["experiment_acceptance"] == "AUTHORIZED_TIMEOUT_LIVELOCK"
    assert res["axes"]["run_outcome"] == "Timeout"
    assert res["axes"]["diagnosis"] == "guest_livelock"
    assert res["axes"]["chain_admission"]["contained_detected"] == 4
    assert res["promoted_to_pass"] is False
    assert res["generic_admission_unchanged"] is True


def test_analysis_capped_with_complete_raw_accepted_and_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        rc, res = run_tool(make_case(tmp, analysis_capped=True))
    assert rc == 0
    assert res["axes"]["evidence_integrity"] == "COMPLETE_RAW_ANALYSIS_CAPPED"
    assert res["axes"]["experiment_acceptance"] == "AUTHORIZED_TIMEOUT_LIVELOCK"
    assert res["evidence"]["analysis_capped"] is True
    assert res["axes"]["chain_admission"]["source"] == "recomputed_full_stream"
    assert res["axes"]["chain_admission"]["contained_detected"] == 4


def test_truncated_stream_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        rc, res = run_tool(make_case(tmp, truncate=True))
    assert rc == 1
    assert res["axes"]["evidence_integrity"] == "INCOMPLETE"
    assert res["axes"]["experiment_acceptance"] == "NOT_ACCEPTED"


def test_timeout_without_causal_evidence_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        rc, res = run_tool(make_case(tmp, guest_final=True, success_after=True))
    assert rc == 1
    assert "causal_evidence_insufficient" in res["reasons"]
    assert "guest_reached_final" in res["reasons"]
    assert "successful_stxr_after_injection" in res["reasons"]


def test_pending_unconsumed_fault_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        rc, res = run_tool(make_case(tmp, pending=True))
    assert rc == 1
    assert "unconsumed_fault_pending" in res["reasons"]
    assert res["counts"]["unconsumed_pending"] == 1


def test_chain_end_not_at_boundary_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        rc, res = run_tool(make_case(tmp, bad_end=True))
    assert rc == 1
    assert "chain_end_not_at_boundary" in res["reasons"]


def test_non_timeout_not_auto_certified():
    with tempfile.TemporaryDirectory() as tmp:
        rc, res = run_tool(make_case(tmp, outcome="Masked"))
    assert rc == 1
    assert res["axes"]["run_outcome"] != "Timeout"
    assert res["axes"]["experiment_acceptance"] == "NOT_ACCEPTED"


def test_real_seed1_accepted():
    if not os.path.isdir(REAL_DIR):
        import pytest
        pytest.skip("real seed1 diagnostic dir absent")
    out = os.path.join(tempfile.mkdtemp(), "acceptance.json")
    cp = subprocess.run(
        [sys.executable, TOOL, "--diag-dir", REAL_DIR, "--run-id", "O02-F5-W7",
         "--seed", "1", "--out-json", out], capture_output=True, text=True, timeout=120)
    res = json.load(open(out))
    assert cp.returncode == 0, res["reasons"]
    assert res["axes"]["experiment_acceptance"] == "AUTHORIZED_TIMEOUT_LIVELOCK"
    # 1010 injections, 1008 consumed, 2 squash-discarded, 0 pending
    assert res["counts"]["injections"] == 1010
    assert res["counts"]["consumed"] == 1008
    assert res["counts"]["successes_after_injection"] == 0
    assert res["counts"]["unconsumed_pending"] == 0
    assert res["axes"]["chain_admission"]["contained_detected"] == 1008
    assert res["axes"]["chain_admission"]["unresolved"] == 2
