#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A4/A07-b] ready-delay 生命周期终局的**准入**集成测试。

契约测试（tests/test_lsu_r6a4_a07b_lifecycle.py）钉死事件形状；本文件钉死
checker 的三条收口路径（check_chain 终局 / containment_from_events 束 /
check_admission 准入门）对同一真实生命周期的判定一致，且不因 oracle/退出码/
截断/缺终局/普通 L0-only 链而虚增 READY。

用法：python3 -m pytest tests/test_lsu_r6a4_a07b_admission.py -q
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_chain_check as C  # noqa: E402
import lsu_prop_fields as P  # noqa: E402

BASE = 12606440
CYCLE = 385
SEQ = "9703"


def evt(kind, **kw):
    base = dict(run_id="A07-F0-W3", sample_run_id="s1", fault_id="1",
                event_id="", parent_event_id="", tick="", dyn_inst_seq="",
                request_id="", field="", before="", after="", pc="0x44452c",
                corr="", detection_layer="", contained="", outcome="",
                containment_layer="", containment_reason="", consumed="",
                squashed="", ready_tick="", delayed_tick="", delay_cycles="")
    base.update(kw)
    base["kind"] = kind
    line = "PROP-EVT: " + " ".join(f"{k}={v}" for k, v in base.items())
    return P.parse_line(line)


def chain(terminal="ready_delay_squashed", close=True):
    ready, delayed = BASE, BASE + CYCLE
    ev = [
        evt("inj", event_id="10", tick=ready, dyn_inst_seq=SEQ,
            request_id=SEQ, field="agu_ready_delay", before=ready,
            after=delayed, delay_cycles="1", state_before="ready",
            state_after="delayed", corr="origin"),
        evt("ready_delay_resume", event_id="11", parent_event_id="10",
            tick=delayed, dyn_inst_seq=SEQ, request_id=SEQ,
            field="agu_ready_delay", ready_tick=ready, delayed_tick=delayed,
            delay_cycles="1", consumed="1",
            squashed="1" if terminal != "ready_delay_retired" else "0",
            corr="seq_primary"),
    ]
    if terminal == "ready_delay_retired":
        ev.append(evt(terminal, event_id="12", parent_event_id="11",
                      tick=delayed + 1000, dyn_inst_seq=SEQ, request_id=SEQ,
                      field="agu_ready_delay", ready_tick=ready,
                      delayed_tick=delayed, delay_cycles="1", consumed="1",
                      squashed="0", outcome="retired_after_delay",
                      detection_layer="L5", contained="1",
                      containment_layer="L5",
                      containment_reason="delay_transparent_retire",
                      corr="seq_primary"))
    elif terminal == "ready_delay_squashed":
        ev.append(evt(terminal, event_id="12", parent_event_id="11",
                      tick=delayed, dyn_inst_seq=SEQ, request_id=SEQ,
                      field="agu_ready_delay", ready_tick=ready,
                      delayed_tick=delayed, delay_cycles="1", consumed="1",
                      squashed="1", outcome="contained",
                      detection_layer="L4", contained="1",
                      containment_layer="L4",
                      containment_reason="squash_before_retire",
                      corr="seq_primary"))
    elif terminal == "ready_delay_discarded":
        ev.append(evt(terminal, event_id="12", parent_event_id="11",
                      tick=delayed + 5000, dyn_inst_seq=SEQ, request_id=SEQ,
                      field="agu_ready_delay", ready_tick=ready,
                      delayed_tick=delayed, delay_cycles="1", consumed="1",
                      squashed="1", outcome="discarded_before_retire",
                      detection_layer="L4", contained="1",
                      containment_layer="L4",
                      containment_reason="squash_after_resume_before_retire",
                      corr="seq_primary"))
    if close:
        ev.append(evt("chain_end", event_id="99",
                      parent_event_id=ev[-1].get("event_id", ""),
                      tick=delayed + 9000, outcome="run_end", contained="0",
                      corr="none"))
    return ev


def bundle(events, oracle="Masked", rc=0, truncated=False):
    return {"run_id": "A07-F0-W3", "activated": 1, "events": events,
            "rc": rc, "oracle_outcome": oracle,
            "containment": C.containment_from_events(
                events, "A07-F0-W3", truncated=truncated)}


def test_all_three_terminals_admitted():
    for term in ("ready_delay_retired", "ready_delay_squashed",
                 "ready_delay_discarded"):
        ev = chain(term)
        r = C.check_chain(ev, oracle_outcome="Masked")
        assert r["faults"]["1"]["terminal"] == "detected_contained", (term, r)
        c = C.containment_from_events(ev, "A07-F0-W3")
        assert c is not None, term
        res = C.check_admission(bundle(ev))
        assert res["admitted"] is True, (term, res)
        assert res["path"] == "contained", (term, res)
        assert res["violations"] == [], (term, res["violations"])


def test_retired_bundle_is_l5_squashed_is_l4():
    assert C.containment_from_events(
        chain("ready_delay_retired"), "A07-F0-W3")["layer"] == "L5"
    c = C.containment_from_events(chain("ready_delay_squashed"), "A07-F0-W3")
    assert c["layer"] == "L4" and c["na_layers"] == ["L5"], c


def test_no_terminal_is_not_containment():
    ev = [e for e in chain("ready_delay_squashed") if e.get("kind") not in (
        "ready_delay_squashed",)]
    ev[-1] = dict(ev[-1], parent_event_id=ev[-2].get("event_id", ""))
    b = bundle(ev)
    assert b["containment"] is None
    assert C.check_admission(b)["admitted"] is False


def test_inj_plus_resume_only_stays_unknown():
    ev = [e for e in chain("ready_delay_squashed") if e.get("kind") not in (
        "ready_delay_squashed",)]
    ev[-1] = dict(ev[-1], parent_event_id=ev[-2].get("event_id", ""))
    r = C.check_chain(ev, oracle_outcome="Masked")
    assert r["faults"]["1"]["terminal"] != "detected_contained", r


def test_plain_l0_only_chain_not_released():
    ev = [
        evt("inj", event_id="0", tick="1", corr="origin"),
        evt("addr_form", event_id="1", parent_event_id="0", tick="2",
            corr="origin"),
        evt("chain_end", event_id="2", parent_event_id="1", tick="3",
            outcome="run_end", contained="0", corr="none"),
    ]
    assert C.check_admission(bundle(ev))["admitted"] is False


def test_truncated_stream_refused():
    assert C.containment_from_events(chain("ready_delay_squashed"),
                                     "A07-F0-W3", truncated=True) is None


def test_oracle_sdc_refused():
    res = C.check_admission(bundle(chain("ready_delay_squashed"),
                                   oracle="SDC"))
    assert res["admitted"] is False, res
    assert any(v.startswith("a07_lifecycle_oracle_not_masked")
               for v in res["violations"]), res["violations"]


def test_rc_nonzero_refused():
    res = C.check_admission(bundle(chain("ready_delay_squashed"), rc=1))
    assert res["admitted"] is False, res
    assert any(v.startswith("a07_lifecycle_requires_rc0")
               for v in res["violations"]), res["violations"]


def test_cross_request_refused():
    ev = chain("ready_delay_squashed")
    for e in ev:
        if e.get("kind") == "ready_delay_resume":
            e["dyn_inst_seq"] = "12345"
    assert C.containment_from_events(ev, "A07-F0-W3") is None


def test_terminal_before_resume_refused():
    ev = chain("ready_delay_squashed")
    for e in ev:
        if e.get("kind") == "ready_delay_squashed":
            e["tick"] = str(BASE)
    assert C.containment_from_events(ev, "A07-F0-W3") is None


if __name__ == "__main__":
    import traceback
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except AssertionError as exc:
                failed += 1
                print("FAIL", name, "->", exc)
            except Exception:
                failed += 1
                print("ERROR", name)
                traceback.print_exc()
    print("R6-A4 A07-B ADMISSION:", "ALL PASSED" if not failed
          else f"{failed} FAILURE(S)")
    sys.exit(1 if failed else 0)
