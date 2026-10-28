#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A4] A01 translation-fault squash 真实终局（白名单）契约。

事实（真实 A01-F1-W3 seed2 流）：注入的 EA 让请求翻译 fault，该请求随后被
LSQ 真实 squash/discard：inj → addr_form → mem_req → lsq_sendfrag →
tlb_translate → tlb_fault(Hardware) → squash_discarded(L4, contained=1,
outcome=contained, request_id≡mem_req) → chain_end。翻译 fault 的请求天然
**没有 L3 见证**（它从未进入下游），旧通用规则要求 L0→L3 前缀 ⇒ 误拒。

本测试钉死**窄白名单**：只有字段齐全、同一 request、ancestry/tick 正确、
流已收口、squash 后无更深真实观测的 A01 流才被接纳；其余（仅 oracle=Masked、
chain_end 冒充、truncated、request/corr 不匹配、跨请求、时间倒挂、非 A01）
一律拒绝。通用门禁不放宽。

用法：python3 -m pytest tests/test_lsu_r6a4_a01_squash_terminal.py -q
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_chain_check as C  # noqa: E402
import lsu_prop_fields as P  # noqa: E402

REQ = "6126737"


def evt(**kw):
    base = dict(run_id="A01-F1-W3", sample_run_id="s2", fault_id="1",
                parent_event_id="", tick="1", detection_layer="",
                contained="", outcome="", corr="", field="", request_id="",
                dyn_inst_seq="")
    base.update(kw)
    line = "PROP-EVT: " + " ".join(f"{k}={v}" for k, v in base.items())
    return P.parse_line(line)


def a01_chain(squash_kw=None, extra_after=None):
    """The REAL A01-F1-W3 seed2 chain shape (no L3 witness)."""
    ev = [
        evt(kind="inj", event_id="0", tick="1336019300", corr="origin"),
        evt(kind="addr_form", event_id="1", parent_event_id="0",
            tick="1336019300", corr="origin", field="va"),
        evt(kind="mem_req", event_id="2", parent_event_id="1",
            tick="1336019300", corr="seq_primary", request_id=REQ,
            dyn_inst_seq=REQ),
        evt(kind="lsq_sendfrag", event_id="3", parent_event_id="2",
            tick="1336019300", corr="seq_primary", request_id=REQ,
            dyn_inst_seq=REQ),
        evt(kind="tlb_translate", event_id="4", parent_event_id="3",
            tick="1336019300", corr="seq_primary", request_id=REQ,
            dyn_inst_seq=REQ, detection_layer="L2", outcome="miss"),
        evt(kind="tlb_fault", event_id="5", parent_event_id="4",
            tick="1336019300", corr="seq_primary", request_id=REQ,
            dyn_inst_seq=REQ, detection_layer="Hardware", outcome="Generic"),
    ]
    kw = dict(event_id="6", parent_event_id="5", tick="1336029695",
              detection_layer="L4", contained="1", outcome="contained",
              corr="seq_primary", request_id=REQ, dyn_inst_seq=REQ,
              field="load", state_before="executing",
              containment_layer="L4", containment_reason="squash_discarded")
    if squash_kw:
        kw.update(squash_kw)
    ev.append(evt(kind="squash_discarded", **kw))
    if extra_after:
        ev.extend(extra_after)
    ev.append(evt(kind="chain_end", event_id="99",
                  parent_event_id=ev[-1].get("event_id", ""),
                  tick="1813259525", outcome="run_end", corr="none"))
    return ev


def bundle(events, oracle="Masked", truncated=False):
    return {
        "run_id": "A01-F1-W3", "activated": 1, "events": events,
        "rc": 0, "oracle_outcome": oracle,
        "containment": C.containment_from_events(
            events, "A01-F1-W3", truncated=truncated),
    }


# ---------------------------------------------------------------- positive
def test_real_chain_terminal_is_detected_contained():
    r = C.check_chain(a01_chain(), oracle_outcome="Masked")
    assert r["faults"]["1"]["terminal"] == "detected_contained", r["faults"]


def test_real_chain_containment_bundle_fields():
    c = C.containment_from_events(a01_chain(), "A01-F1-W3")
    assert c is not None, "real squash must yield a containment bundle"
    assert c["layer"] == "L4", c
    assert c["na_layers"] == ["L5"], c
    assert "squash_discarded" in c["reason"], c
    m = c["metrics"]["L4"]
    assert m["event_id"] == "6" and m["kind"] == "squash_discarded", m


def test_real_chain_admitted_via_contained():
    b = bundle(a01_chain())
    res = C.check_admission(b)
    assert res["admitted"] is True, res
    assert res["path"] == "contained", res
    assert res["violations"] == [], res["violations"]


# ---------------------------------------------------------------- negatives
def test_oracle_masked_alone_is_not_containment():
    # same chain minus the squash: honest L2-then-unknown, NOT admitted.
    ev = [e for e in a01_chain() if e.get("kind") != "squash_discarded"]
    # re-link chain_end to the last real ancestor
    ev[-1] = dict(ev[-1], parent_event_id=ev[-2].get("event_id", ""))
    b = bundle(ev)
    assert b["containment"] is None
    res = C.check_admission(b)
    assert res["admitted"] is False
    assert any(v.startswith("no_closed_chain_and_no_containment")
               for v in res["violations"]), res["violations"]


def test_chain_end_cannot_be_the_containment_witness():
    ev = a01_chain()
    # strip the real squash, keep only chain_end (contained=1) as witness
    ev = [e for e in ev if e.get("kind") != "squash_discarded"]
    ev[-1] = dict(ev[-1], contained="1", detection_layer="L4",
                  outcome="contained", corr="seq_primary")
    assert C.containment_from_events(ev, "A01-F1-W3") is None


def test_truncated_stream_still_refused():
    assert C.containment_from_events(a01_chain(), "A01-F1-W3",
                                     truncated=True) is None


def test_request_mismatch_refused():
    c = C.containment_from_events(
        a01_chain(squash_kw={"request_id": "999999"}), "A01-F1-W3")
    assert c is None, c


def test_dyn_inst_seq_mismatch_refused():
    c = C.containment_from_events(
        a01_chain(squash_kw={"dyn_inst_seq": "898989"}), "A01-F1-W3")
    assert c is None, c


def test_corr_none_refused():
    c = C.containment_from_events(
        a01_chain(squash_kw={"corr": "none"}), "A01-F1-W3")
    assert c is None, c


def test_missing_parent_event_refused():
    c = C.containment_from_events(
        a01_chain(squash_kw={"parent_event_id": ""}), "A01-F1-W3")
    assert c is None, c


def test_time_reversed_squash_refused():
    c = C.containment_from_events(
        a01_chain(squash_kw={"tick": "1336019299"}), "A01-F1-W3")
    assert c is None, c


def test_deeper_real_observation_after_squash_refused():
    # a REAL downstream observation (consumer is L4 in the generic map) after
    # the squash means the request did propagate — containment is not proven.
    deeper = [evt(kind="consumer", event_id="7", parent_event_id="6",
                  tick="1336100000", corr="taint_prop", request_id=REQ,
                  dyn_inst_seq=REQ, detection_layer="L4",
                  outcome="consumed")]
    deeper += [evt(kind="lq_complete", event_id="8", parent_event_id="7",
                   tick="1336200000", corr="seq_primary", request_id=REQ,
                   dyn_inst_seq=REQ, detection_layer="L3",
                   outcome="complete")]
    c = C.containment_from_events(a01_chain(extra_after=deeper), "A01-F1-W3")
    assert c is None, c


def test_non_a01_run_is_not_whitelisted():
    ev = a01_chain()
    for e in ev:
        e["run_id"] = "A05-F1-W3"
    assert C.containment_from_events(ev, "A05-F1-W3") is None


def test_missing_containment_reason_refused():
    c = C.containment_from_events(
        a01_chain(squash_kw={"containment_reason": ""}), "A01-F1-W3")
    assert c is None, c


def test_squash_without_tlb_fault_refused():
    ev = [e for e in a01_chain() if e.get("kind") != "tlb_fault"]
    # relink squash to tlb_translate
    for e in ev:
        if e.get("kind") == "squash_discarded":
            e["parent_event_id"] = "4"
    assert C.containment_from_events(ev, "A01-F1-W3") is None


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
    print("R6-A4 A01 SQUASH TERMINAL:", "ALL PASSED" if not failed
          else f"{failed} FAILURE(S)")
    sys.exit(1 if failed else 0)
