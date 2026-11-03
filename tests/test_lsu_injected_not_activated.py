#!/usr/bin/env python3
"""Strict `injected_not_activated` terminal — denial + acceptance controls.

The five C04/C05 seed1 samples were really injected but the corrupted line
was never consumed again; the chain honestly stops at L0. This terminal is
ONLY for that case and must not relax any other L0-only / truncated /
evidence-missing stream.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import lsu_chain_check as C  # noqa: E402

SHA = "a" * 64


def ev(**kw):
    d = {"run_id": "C04-F0-W6", "sample_run_id": "s1", "fault_id": "1",
         "event_id": "", "parent_event_id": "", "tick": "", "cycle": "",
         "kind": "", "corr": "", "evidence_status": "observed"}
    d.update({k: ("" if v is None else str(v)) for k, v in kw.items()})
    return d


def l0(**kw):
    base = dict(event_id="851", tick="1851000", kind="inj", corr="origin",
                va="74cc0", cache_line="74cc0", field="tag",
                detection_layer="", contained="", outcome="")
    base.update(kw)
    return ev(**base)


def chain_end(**kw):
    base = dict(event_id="854", parent_event_id="851", tick="58399880",
                kind="chain_end", corr="none", detection_layer="",
                contained="0", outcome="run_end")
    base.update(kw)
    return ev(**base)


def facts(**kw):
    f = dict(oracle_outcome="Masked", exit_code=0, truncated=False,
             stats={"simTicks": "58399880",
                    "board.chaos_l1d.numFaultsInjected": "1"},
             inj_rows=1, binary_sha256=SHA,
             binary_source_head="f0233ef1",
             analysis_tool_head="a7d30f07",
             consumer_summary_accounting={"conservation": "n/a"})
    f.update(kw)
    return f


def verdict(events, **kw):
    return C.injected_not_activated_verdict(events, **facts(**kw))


def test_strict_case_is_accepted():
    r = verdict([l0(), chain_end()])
    assert r["ok"] is True, r["reasons"]
    assert r["terminal"] == "injected_not_activated"
    assert r["provable_to"] == "L0"
    assert r["subkind"] == "not_consumed"


def test_truncated_stream_rejected():
    r = verdict([l0(), chain_end()], truncated=True)
    assert r["ok"] is False
    assert any("truncated" in x for x in r["reasons"])


def test_empty_stats_rejected():
    r = verdict([l0(), chain_end()], stats={})
    assert r["ok"] is False
    assert any("stats" in x for x in r["reasons"])


def test_missing_simticks_rejected():
    r = verdict([l0(), chain_end()],
                stats={"board.chaos_l1d.numFaultsInjected": "1"})
    assert r["ok"] is False
    assert any("simTicks" in x for x in r["reasons"])


def test_injection_count_mismatch_rejected():
    r = verdict([l0(), chain_end()], inj_rows=2)
    assert r["ok"] is False
    assert any("injection" in x or "count" in x for x in r["reasons"])


def test_downstream_access_on_same_line_rejected():
    down = ev(event_id="900", parent_event_id="851", tick="2000000",
              kind="cache_access", corr="addr_fallback", va="74cc0",
              cache_line="74cc0")
    r = verdict([l0(), down, chain_end()])
    assert r["ok"] is False
    assert any("downstream" in x for x in r["reasons"])


def test_unknown_downstream_event_rejected():
    down = ev(event_id="901", parent_event_id="851", tick="2000000",
              kind="mystery_kind", corr="addr_fallback")
    r = verdict([l0(), down, chain_end()])
    assert r["ok"] is False
    assert any("unknown" in x or "downstream" in x for x in r["reasons"])


def test_chain_end_cannot_be_l5():
    bad = chain_end(detection_layer="L5", contained="1",
                    outcome="errant_commit_seen")
    r = verdict([l0(), bad])
    assert r["ok"] is False
    assert any("chain_end" in x for x in r["reasons"])


def test_errant_commit_rejected():
    err = ev(event_id="900", parent_event_id="851", tick="2000000",
             kind="errant_commit", corr="taint_prop",
             detection_layer="L5", contained="0", outcome="errant_commit")
    r = verdict([l0(), err, chain_end()])
    assert r["ok"] is False


def test_plain_l0_only_without_facts_is_not_relaxed():
    # No stats / no injection count / no binary identity: the old open
    # terminal must remain un-admitted.
    r = C.injected_not_activated_verdict([l0(), chain_end()])
    assert r["ok"] is False
    v = C.check_chain([l0(), chain_end()], oracle_outcome="Masked")
    assert v["faults"]["1"]["provable_to"] == "L0"
    assert v["faults"]["1"]["terminal"] != "full"


def test_full_and_contained_terminals_unchanged():
    full = [
        ev(event_id="0", tick="100", kind="inj", corr="origin", va="8cf40"),
        ev(event_id="1", parent_event_id="0", tick="200", kind="cache_access",
           corr="addr_fallback", va="8cf40", dyn_inst_seq="7"),
        ev(event_id="2", parent_event_id="1", tick="300", kind="cache_return",
           corr="addr_fallback", dyn_inst_seq="7"),
        ev(event_id="3", parent_event_id="2", tick="400", kind="resp",
           corr="addr_fallback", dyn_inst_seq="7"),
        ev(event_id="4", parent_event_id="3", tick="500", kind="taint_reg",
           corr="addr_fallback", dyn_inst_seq="7"),
        ev(event_id="5", parent_event_id="4", tick="600", kind="errant_commit",
           corr="taint_prop", dyn_inst_seq="7", detection_layer="L5",
           contained="0", outcome="errant_commit"),
        ev(event_id="6", parent_event_id="5", tick="700", kind="chain_end",
           corr="none"),
    ]
    v = C.check_chain(full, oracle_outcome="SDC")
    assert v["faults"]["1"]["terminal"] == "full"
    assert v["faults"]["1"]["provable_to"] == "L5"

    contained = [
        ev(event_id="0", tick="100", kind="inj", corr="origin", va="8cf40"),
        ev(event_id="1", parent_event_id="0", tick="200", kind="cache_access",
           corr="addr_fallback", va="8cf40", dyn_inst_seq="7"),
        ev(event_id="2", parent_event_id="1", tick="300", kind="cache_return",
           corr="addr_fallback", dyn_inst_seq="7"),
        ev(event_id="3", parent_event_id="2", tick="400", kind="resp",
           corr="addr_fallback", dyn_inst_seq="7"),
        ev(event_id="4", parent_event_id="3", tick="500", kind="squash_masked",
           corr="seq_primary", detection_layer="L4", contained="1",
           outcome="masked", containment_reason="squash_replay"),
    ]
    v = C.check_chain(contained, oracle_outcome="Masked")
    assert v["faults"]["1"]["terminal"] == "detected_contained"
