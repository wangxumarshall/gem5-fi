#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A4] A01 translation-fault squash 真实终局（窄白名单）契约。

事实（真实 A01-F1-W3 seed2 / A01-F2-W3 seed2 流，Lane C 字段级核对）：
inj(va 493170→49b170) → addr_form → mem_req → lsq_sendfrag → tlb_translate →
tlb_fault(Hardware, contained 空) → squash_discarded(L4, contained=1,
outcome=contained, state_before=load_queue_uncommitted) → chain_end。
翻译 fault 的请求**从未进入下游**，L3 见证结构性缺席；旧通用前缀规则因此
误拒。白名单按 Lane C 的严格字段契约接纳：

  A. 全 run_id=A01、family=agu、唯一 fault、唯一 squash、唯一 chain_end 且
     位于流末并带合法生命周期字段；
  B. squash 字段精确（contained/outcome/dl/containment_layer/reason/corr/
     field/state_before/evidence_status）；
  C. ancestry 严格等于 7 事件序列；dyn/request/va 全等且非空；inj 确有改值；
     tlb_fault=Hardware 且 contained≠1；
  D. tick 非降、squash>fault、end>squash；squash 之后无任何非 chain_end
     事件；链内禁 arch/consumer/taint/errant/L3 族；
  E. oracle=Masked 且 rc=0（必要条件），errant_commit 逃逸优先。
其余（仅 oracle=Masked、仅 chain_end、truncated、request/corr/va 不匹配、
非 A01、store squash、oracle=SDC/Crash、更深观测）一律拒绝。

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
VA = "49b170"
OLD_VA = "493170"


def evt(**kw):
    base = dict(run_id="A01-F1-W3", sample_run_id="s2", fault_id="1",
                parent_event_id="", tick="1", detection_layer="",
                contained="", outcome="", corr="", field="", request_id="",
                dyn_inst_seq="", va="", before="", after="",
                state_before="")
    base.update(kw)
    line = "PROP-EVT: " + " ".join(f"{k}={v}" for k, v in base.items())
    return P.parse_line(line)


def a01_chain(squash_kw=None, extra_after=None, extra_anc=None):
    """The REAL A01-F1-W3 seed2 chain shape (no L3 witness)."""
    t = "1336019300"
    ev = [
        evt(kind="inj", event_id="0", tick=t, corr="origin",
            dyn_inst_seq=REQ, va=OLD_VA, before=OLD_VA, after=VA),
        evt(kind="addr_form", event_id="1", parent_event_id="0", tick=t,
            corr="origin", dyn_inst_seq=REQ, va=VA, field="va"),
        evt(kind="mem_req", event_id="2", parent_event_id="1", tick=t,
            corr="seq_primary", request_id=REQ, dyn_inst_seq=REQ, va=VA),
        evt(kind="lsq_sendfrag", event_id="3", parent_event_id="2", tick=t,
            corr="seq_primary", request_id=REQ, dyn_inst_seq=REQ, va=VA),
        evt(kind="tlb_translate", event_id="4", parent_event_id="3", tick=t,
            corr="seq_primary", request_id=REQ, dyn_inst_seq=REQ, va=VA,
            detection_layer="L2", outcome="miss"),
        evt(kind="tlb_fault", event_id="5", parent_event_id="4", tick=t,
            corr="seq_primary", request_id=REQ, dyn_inst_seq=REQ, va=VA,
            detection_layer="Hardware",
            outcome="Generic_page_table_fault"),
    ]
    if extra_anc:
        ev.extend(extra_anc)
    kw = dict(event_id="6", parent_event_id="5", tick="1336029695",
              detection_layer="L4", contained="1", outcome="contained",
              corr="seq_primary", request_id=REQ, dyn_inst_seq=REQ,
              field="load", state_before="load_queue_uncommitted",
              containment_layer="L4", containment_reason="squash_discarded")
    if squash_kw:
        kw.update(squash_kw)
    ev.append(evt(kind="squash_discarded", **kw))
    if extra_after:
        ev.extend(extra_after)
    ev.append(evt(kind="chain_end", event_id="99",
                  parent_event_id=ev[-1].get("event_id", ""),
                  tick="1813259525", outcome="run_end", contained="0",
                  corr="none"))
    return ev


def bundle(events, oracle="Masked", rc=0, truncated=False):
    return {
        "run_id": "A01-F1-W3", "activated": 1, "events": events,
        "rc": rc, "oracle_outcome": oracle,
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
    res = C.check_admission(bundle(a01_chain()))
    assert res["admitted"] is True, res
    assert res["path"] == "contained", res
    assert res["violations"] == [], res["violations"]


# ------------------------------------------------------- oracle / rc gates
def test_oracle_masked_alone_is_not_containment():
    ev = [e for e in a01_chain() if e.get("kind") != "squash_discarded"]
    ev[-1] = dict(ev[-1], parent_event_id=ev[-2].get("event_id", ""))
    b = bundle(ev)
    assert b["containment"] is None
    res = C.check_admission(b)
    assert res["admitted"] is False
    assert any(v.startswith("no_closed_chain_and_no_containment")
               for v in res["violations"]), res["violations"]


def test_oracle_sdc_refused():
    res = C.check_admission(bundle(a01_chain(), oracle="SDC"))
    assert res["admitted"] is False, res
    assert any(v.startswith("a01_squash_oracle_not_masked")
               for v in res["violations"]), res["violations"]


def test_oracle_crash_refused():
    res = C.check_admission(bundle(a01_chain(), oracle="Crash"))
    assert res["admitted"] is False, res
    assert any(v.startswith("a01_squash_oracle_not_masked")
               for v in res["violations"]), res["violations"]


def test_rc_nonzero_refused():
    res = C.check_admission(bundle(a01_chain(), rc=1))
    assert res["admitted"] is False, res
    assert any(v.startswith("a01_squash_requires_rc0")
               for v in res["violations"]), res["violations"]


# ------------------------------------------------- stream / ancestry gates
def test_chain_end_cannot_be_the_containment_witness():
    ev = [e for e in a01_chain() if e.get("kind") != "squash_discarded"]
    ev[-1] = dict(ev[-1], contained="1", detection_layer="L4",
                  outcome="contained", corr="seq_primary")
    assert C.containment_from_events(ev, "A01-F1-W3") is None


def test_chain_end_mutated_lifecycle_fields_refused():
    ev = a01_chain()
    ev[-1] = dict(ev[-1], corr="seq_primary", outcome="arch_exception",
                  contained="1", detection_layer="L4")
    assert C.containment_from_events(ev, "A01-F1-W3") is None


def test_duplicate_chain_end_refused():
    ev = a01_chain()
    dup = evt(kind="chain_end", event_id="100",
              parent_event_id=ev[-1].get("event_id", ""), tick="1813259526",
              outcome="run_end", contained="0", corr="none")
    assert C.containment_from_events(ev + [dup], "A01-F1-W3") is None


def test_truncated_stream_still_refused():
    assert C.containment_from_events(a01_chain(), "A01-F1-W3",
                                     truncated=True) is None


def test_request_mismatch_refused():
    assert C.containment_from_events(
        a01_chain(squash_kw={"request_id": "999999"}), "A01-F1-W3") is None


def test_tlb_fault_request_mismatch_refused():
    ev = a01_chain()
    for e in ev:
        if e.get("kind") == "tlb_fault":
            e["request_id"] = "999999"
    assert C.containment_from_events(ev, "A01-F1-W3") is None


def test_tlb_translate_request_mismatch_refused():
    ev = a01_chain()
    for e in ev:
        if e.get("kind") == "tlb_translate":
            e["request_id"] = "999999"
    assert C.containment_from_events(ev, "A01-F1-W3") is None


def test_va_mismatch_refused():
    ev = a01_chain()
    for e in ev:
        if e.get("kind") == "tlb_fault":
            e["va"] = "49b171"
    assert C.containment_from_events(ev, "A01-F1-W3") is None


def test_no_actual_va_change_refused():
    ev = a01_chain()
    for e in ev:
        if e.get("kind") == "inj":
            e["after"] = OLD_VA
    assert C.containment_from_events(ev, "A01-F1-W3") is None


def test_empty_dyn_seq_refused():
    ev = a01_chain()
    for e in ev:
        if e.get("kind") == "mem_req":
            e["dyn_inst_seq"] = ""
    assert C.containment_from_events(ev, "A01-F1-W3") is None


def test_dyn_inst_seq_mismatch_refused():
    assert C.containment_from_events(
        a01_chain(squash_kw={"dyn_inst_seq": "898989"}),
        "A01-F1-W3") is None


def test_corr_none_refused():
    assert C.containment_from_events(
        a01_chain(squash_kw={"corr": "none"}), "A01-F1-W3") is None


def test_missing_parent_event_refused():
    assert C.containment_from_events(
        a01_chain(squash_kw={"parent_event_id": ""}), "A01-F1-W3") is None


def test_time_reversed_squash_refused():
    assert C.containment_from_events(
        a01_chain(squash_kw={"tick": "1336019299"}), "A01-F1-W3") is None


def test_deeper_real_observation_after_squash_refused():
    deeper = [evt(kind="consumer", event_id="7", parent_event_id="6",
                  tick="1336100000", corr="taint_prop", request_id=REQ,
                  dyn_inst_seq=REQ, detection_layer="L4",
                  outcome="consumed")]
    assert C.containment_from_events(a01_chain(extra_after=deeper),
                                     "A01-F1-W3") is None


def test_same_tick_deeper_observation_refused():
    deeper = [evt(kind="consumer", event_id="7", parent_event_id="6",
                  tick="1336029695", corr="taint_prop", request_id=REQ,
                  dyn_inst_seq=REQ, detection_layer="L4",
                  outcome="consumed")]
    assert C.containment_from_events(a01_chain(extra_after=deeper),
                                     "A01-F1-W3") is None


def test_delivered_arch_fault_sibling_refused_by_whitelist():
    # A delivered architectural translation fault is a real terminal in its
    # OWN right (existing generic rule, used by A01 seed1/s3). The A01 squash
    # whitelist must NOT treat the squash as the terminal in such a stream
    # (Lane C G7): assert the whitelist predicate itself refuses.
    arch = evt(kind="arch_translation_fault", event_id="7",
               parent_event_id="5", tick="1336020000", corr="seq_primary",
               request_id=REQ, dyn_inst_seq=REQ, detection_layer="L2",
               contained="1", outcome="arch_exception")
    ev = a01_chain(extra_anc=[arch])
    sq = next(e for e in ev if e.get("kind") == "squash_discarded")
    assert C._a01_translation_squash_witness(ev, sq, "agu") is False


def test_store_not_retired_in_chain_refused():
    snr = evt(kind="store_not_retired", event_id="7", parent_event_id="5",
              tick="1336020000", corr="taint_prop", request_id=REQ,
              dyn_inst_seq=REQ, detection_layer="L4", contained="1",
              outcome="contained")
    assert C.containment_from_events(a01_chain(extra_anc=[snr]),
                                     "A01-F1-W3") is None


def test_non_a01_run_is_not_whitelisted():
    ev = a01_chain()
    for e in ev:
        e["run_id"] = "A05-F1-W3"
    assert C.containment_from_events(ev, "A05-F1-W3") is None


def test_missing_containment_reason_refused():
    assert C.containment_from_events(
        a01_chain(squash_kw={"containment_reason": ""}),
        "A01-F1-W3") is None


def test_store_squash_refused():
    assert C.containment_from_events(
        a01_chain(squash_kw={"field": "store",
                             "state_before": "store_queue_uncommitted"}),
        "A01-F1-W3") is None


def test_squash_without_tlb_fault_refused():
    ev = [e for e in a01_chain() if e.get("kind") != "tlb_fault"]
    for e in ev:
        if e.get("kind") == "squash_discarded":
            e["parent_event_id"] = "4"
    assert C.containment_from_events(ev, "A01-F1-W3") is None


def test_extra_ancestry_event_refused():
    extra = evt(kind="taint_reg", event_id="9", parent_event_id="5",
                tick="1336020000", corr="taint_prop", request_id=REQ,
                dyn_inst_seq=REQ, detection_layer="L4",
                outcome="tainted")
    # relink squash to the extra event
    ev = a01_chain(extra_anc=[extra])
    for e in ev:
        if e.get("kind") == "squash_discarded":
            e["parent_event_id"] = "9"
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
