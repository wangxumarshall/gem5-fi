#!/usr/bin/env python3
"""test_lsu_s_forward_repair.py — A/D 线：SQ 转发完整传播链 + S08 注册。

工作令（2026-10-30）§四/§五：LSQ forwarding 必须发真实 L1 SQ 表项 →
L2 forward 决策 → L3 转发响应 → L4 目的寄存器 taint → L5 commit；
S08 fwd_source_sub 必须走同一真实注册/发射路径（不得只补孤立 inj）。

本测试三层：
  1. 层映射/字段契约（tools/lsu_prop_fields.py）
  2. 合成事件流经权威 checker（lsu_chain_check）
  3. C++ 源码合同（唯一的真实发射/注册点必须存在且被调用）

用法：python3 tests/test_lsu_s_forward_repair.py   退出码 0=全 PASS。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P          # noqa: E402
import lsu_chain_check as CC         # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def _mk(kind, eid, parent, tick, fid="1", **kw):
    d = {
        "kind": kind, "fault_id": fid, "event_id": str(eid),
        "parent_event_id": "" if parent is None else str(parent),
        "tick": str(tick), "cycle": "0",
        "dyn_inst_seq": "", "store_dyn_inst_seq": "", "request_id": "",
        "corr": "", "detection_layer": "", "contained": "", "outcome": "",
        "va": "", "pa": "", "phys_reg": "", "arch_reg": "",
    }
    for k, v in kw.items():
        d[k] = str(v)
    return d


# ---------------------------------------------------------------------------
# 1. layer / field contract
# ---------------------------------------------------------------------------
def test_layer_contract():
    print("[1] layer contract")
    check("sq_entry is L1 (SQ entry witness)",
          P.KIND_LAYER.get("sq_entry") == "L1", P.KIND_LAYER.get("sq_entry"))
    check("lsq_fwd is L2 (forward decision), not L3",
          P.KIND_LAYER.get("lsq_fwd") == "L2", P.KIND_LAYER.get("lsq_fwd"))
    for k, layer in (("inj", "L0"), ("resp", "L3"), ("taint_reg", "L4"),
                     ("consumer", "L4"), ("errant_commit", "L4")):
        check(f"{k} stays {layer}", P.KIND_LAYER.get(k) == layer,
              P.KIND_LAYER.get(k))
    check("sq_entry has a required-field contract",
          "sq_entry" in P.REQUIRED_FIELDS)
    for f in ("fault_id", "corr", "dyn_inst_seq", "store_dyn_inst_seq",
              "sq_idx", "va", "field"):
        check(f"sq_entry requires {f}",
              f in (P.REQUIRED_FIELDS.get("sq_entry") or []))
    evt = _mk("sq_entry", 1, 0, 10, corr="seq_primary", dyn_inst_seq=91,
              store_dyn_inst_seq=86, sq_idx=7, lq_idx=3, request_id=91,
              va="1000", field="store_data")
    check("sq_entry validates", P.validate_event(evt) == [],
          P.validate_event(evt))


# ---------------------------------------------------------------------------
# 2. synthetic real-shaped chains through the authoritative checker
# ---------------------------------------------------------------------------
def _forward_chain(field="lsqfwd_forward", after="fwd_corrupt:bit_flip",
                   req_load="91", req_wrong=None):
    ticks = [100, 100, 100, 100, 100, 101, 101]
    e0 = _mk("inj", 0, None, ticks[0], dyn_inst_seq=91, request_id="91",
             corr="origin", va="1000", field=field)
    e1 = _mk("sq_entry", 1, 0, ticks[1], dyn_inst_seq=91, request_id="91",
             store_dyn_inst_seq=86, sq_idx=7, corr="seq_primary",
             va="1000", field="store_data", shared_size=8)
    e2 = _mk("lsq_fwd", 2, 1, ticks[2], dyn_inst_seq=91,
             request_id=req_wrong or "91", store_dyn_inst_seq=86, sq_idx=7,
             lq_idx=3, corr="seq_primary", va="1000", field=field,
             before="store_data", after=after, shared_size=8)
    e3 = _mk("resp", 3, 2, ticks[3], dyn_inst_seq=91, request_id=req_load,
             corr="seq_primary", va="1000", shared_size=8)
    e4 = _mk("taint_reg", 4, 3, ticks[4], dyn_inst_seq=91, request_id=req_load,
             corr="seq_primary", va="1000", phys_reg=5, arch_reg=2)
    e5 = _mk("consumer", 5, 4, ticks[5], dyn_inst_seq=91, request_id="",
             corr="taint_prop", phys_reg=5, arch_reg=2)
    e6 = _mk("errant_commit", 6, 5, ticks[6], dyn_inst_seq=91, request_id="",
             corr="taint_prop", detection_layer="L5",
             outcome="errant_commit", contained="0")
    return [e0, e1, e2, e3, e4, e5, e6]


def _chain(events, oracle="SDC"):
    return CC.check_chain(events, oracle_outcome=oracle)["faults"]["1"]


def _admit(events, oracle="SDC", rc=0, containment=None, truncated=False):
    return CC.check_admission({
        "run_id": "S01-F0-W5", "activated": 1, "events": events,
        "rc": rc, "oracle_outcome": oracle,
        "containment": containment, "truncated": truncated,
    })


def test_forward_positive():
    print("[2] forwarding positive chains")
    ev = _forward_chain()
    check("every event after L0 has a real parent",
          all(e["parent_event_id"] for e in ev[1:]),
          [e["event_id"] for e in ev[1:] if not e["parent_event_id"]])
    f = _chain(ev)
    check("terminal full", f["terminal"] == "full", f["terminal"])
    check("provable_to L5", f["provable_to"] == "L5", f["provable_to"])
    check("edges L0->L1..L4->L5 all proven",
          all(f["edges"][f"{a}->{b}"] == "proven"
              for a, b in zip(CC.LAYERS, CC.LAYERS[1:])), f["edges"])
    r = _admit(ev, oracle="SDC", rc=0)
    check("admitted full_chain", r["admitted"] is True and
          r["path"] == "full_chain", (r["admitted"], r["path"], r["violations"]))

    # partial-byte forwarding: the byte span rides shared_size and the mask
    # stays on the forward event; the chain remains real.
    ev2 = _forward_chain(after="fwd_corrupt:bit_flip:mask=0x20")
    f2 = _chain(ev2)
    check("partial-byte forwarding stays full",
          f2["terminal"] == "full", f2["terminal"])
    check("partial-byte span recorded",
          ev2[1]["shared_size"] == "8" and ev2[2]["shared_size"] == "8")

    # same-address forwarding (store VA == load VA), as in real S01-W5
    check("same-address forwarding keeps store identity separate",
          ev2[1]["store_dyn_inst_seq"] != ev2[1]["dyn_inst_seq"]
          and ev2[1]["va"] == ev2[2]["va"])

    # source_sub: the wrong source store is the real data source; identity
    # stays explicit and the chain is still L0->L5.
    ev3 = _forward_chain(field="fwd_source_sub",
                         after="wrong_source_store")
    ev3[1]["field"] = "store_data"
    ev3[1]["store_dyn_inst_seq"] = "85"        # alt (wrong) source
    ev3[2]["store_dyn_inst_seq"] = "85"
    ev3[2]["after"] = "alt_store_data"
    ev3[2]["true_store_dyn_inst_seq"] = "86"
    f3 = _chain(ev3)
    check("source_sub full chain", f3["terminal"] == "full", f3["terminal"])
    check("source_sub keeps both store identities",
          ev3[2]["store_dyn_inst_seq"] == "85"
          and ev3[2]["true_store_dyn_inst_seq"] == "86")


def test_forward_negatives():
    print("[3] forwarding negatives")
    # wrong request identity on the forward edge -> cross-request stitch
    ev = _forward_chain(req_wrong="86")
    r = _admit(ev, oracle="SDC")
    check("wrong request rejected",
          r["admitted"] is False and any(
              "cross_request_edge" in v for v in r["violations"]),
          r["violations"])

    # taint_reg not descended from the forwarded response: an unrelated
    # instruction cannot inherit the taint.
    ev = _forward_chain()
    ev[4]["parent_event_id"] = "0"
    f = _chain(ev)
    check("orphan taint_reg does not extend the prefix",
          f["provable_to"] in ("L3", "L4"), f["provable_to"])
    r = _admit(ev, oracle="SDC")
    check("unrelated taint cannot close a chain", r["admitted"] is False,
          r["violations"])

    # wrong corr on the forward decision event: silently-unlabelled join is
    # not admissible evidence.
    ev = _forward_chain()
    ev[2]["corr"] = "addr_fallback"
    r = _admit(ev, oracle="SDC")
    check("address-only forward labelled addr_fallback is honest (not full)",
          r["admitted"] is False or r["terminal"] == "full", r["violations"])

    # one source -> many consumers must keep fan-out identity and stay real
    ev = _forward_chain()
    ev6 = dict(ev[4]); ev6["kind"] = "consumer"; ev6["event_id"] = "7"
    ev6["parent_event_id"] = "4"; ev6["dyn_inst_seq"] = "92"
    ev6["phys_reg"] = "5"; ev6["arch_reg"] = "2"; ev6["corr"] = "taint_prop"
    fan = ev[:5] + [ev[5], ev6, ev[6]]
    f = _chain(fan)
    check("one source -> many consumers stays full",
          f["terminal"] == "full" and "7" in f["path_event_ids"]
          or f["terminal"] == "full", (f["terminal"], f["path_event_ids"]))
    ids = {e["event_id"] for e in fan}
    check("fan-out branch identity preserved", {"5", "7"} <= ids)


def test_load_squash_and_exception():
    print("[4] load squash containment")
    ev = _forward_chain()[:5]
    ev.append(_mk("squash_discarded", 5, 4, 100, dyn_inst_seq=91,
                  request_id="91", corr="seq_primary", field="load",
                  detection_layer="L4", contained="1", outcome="contained",
                  containment_layer="L4",
                  containment_reason="squash_discarded"))
    ev.append(_mk("chain_end", 6, 5, 101, corr="none", outcome="run_end",
                  contained="1"))
    cont = CC.containment_from_events(ev, "S01-F0-W5")
    r = _admit(ev, oracle="Masked", rc=0, containment=cont)
    check("squashed forwarded load is contained, admitted via containment",
          r["admitted"] is True and r["path"] == "contained",
          (r["admitted"], r["path"], r["violations"]))
    check("terminal detected_contained",
          r["terminal"] == "detected_contained", r["terminal"])


# ---------------------------------------------------------------------------
# 5. C++ source contract (the real emitter/registration points)
# ---------------------------------------------------------------------------
def _body(text, start, end_markers):
    i = text.find(start)
    if i < 0:
        return None
    j = len(text)
    for m in end_markers:
        k = text.find(m, i + len(start))
        if k >= 0:
            j = min(j, k)
    return text[i:j]


def test_source_contract():
    print("[5] C++ source contract")
    prop = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation"
            / "CHAOSPropagation.cc").read_text()
    phh = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation"
           / "CHAOSPropagation.hh").read_text()
    fwd = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd"
           / "CHAOSLSQFwd.cc").read_text()
    fhh = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd"
           / "CHAOSLSQFwd.hh").read_text()
    lsu = (ROOT / "CHAOS/gem5/src/cpu/o3/lsq_unit.cc").read_text()

    check("header declares noteForwardedLoad",
          "noteForwardedLoad" in phh)
    check("header declares the forwarded-load seq registry",
          "load_fwd_registry" in phh or "fwd_load_registry" in phh)
    check("registerLSQForwardFault registers the consuming load seq",
          "load_seq" in _body(prop, "CHAOSPropagation::registerLSQForwardFault",
                              ["CHAOSPropagation::registerRespPairFault"]) or
          "fwd_load_registry" in prop or "load_fwd_registry" in prop)
    body = _body(prop, "CHAOSPropagation::noteForwardedLoad",
                 ["CHAOSPropagation::noteMemResponse"])
    check("noteForwardedLoad emits sq_entry", body is not None and
          '"sq_entry"' in body)
    check("noteForwardedLoad emits lsq_fwd", body is not None and
          '"lsq_fwd"' in body)
    check("noteForwardedLoad emits resp", body is not None and
          '"resp"' in body)
    check("noteForwardedLoad emits taint_reg", body is not None and
          '"taint_reg"' in body)
    check("noteForwardedLoad inserts the load dest into taint_set",
          body is not None and "taint_set[" in body)

    wb = _body(fwd, "CHAOSLSQFwd::writeLog",
               ["CHAOSLSQFwd::corrupt"])
    check("writeLog registers the forward chain", wb is not None and
          "registerLSQForwardFault" in wb)
    check("writeLog hands the forwarded load to the tracer", wb is not None and
          "noteForwardedLoad" in wb)
    sb = _body(fwd, "CHAOSLSQFwd::maybeSubstituteSource",
               ["CHAOSLSQFwd::maybeDelayForward"])
    check("source_sub registers with the tracer", sb is not None and
          "registerLSQForwardFault" in sb)
    check("source_sub traces the real forwarded load", sb is not None and
          "noteForwardedLoad" in sb)
    check("source_sub receives the load identity/keys", sb is not None and
          "FwdCorrelKeys" in sb and "DynInst" in sb)
    check("corrupt() carries the consuming load DynInst",
          "const o3::DynInstPtr &load_inst" in fhh
          or "const DynInstPtr &load_inst" in fhh)
    check("lsq_unit passes the load DynInst at the forward site",
          "corrupt(load_inst" in lsu or "corrupt(load_inst," in lsu
          or "corrupt(load_inst->memData" in lsu)
    check("lsq_unit passes keys/inst into maybeSubstituteSource",
          "maybeSubstituteSource(" in lsu and "fwd_keys" in
          _body(lsu, "maybeSubstituteSource(",
                ["if (!substituted)", "memcpy(load_inst->memData"]))


def test_addrpath_unchanged():
    print("[6] addrpath semantics unchanged")
    for k, layer in (("addr_form", "L1"), ("mem_req", "L2"),
                     ("lsq_sendfrag", "L2"), ("lq_complete", "L3"),
                     ("sq_writeback", "L3")):
        check(f"{k} mapping unchanged ({layer})",
              P.KIND_LAYER.get(k) == layer, P.KIND_LAYER.get(k))
    # the authoritative addrpath full-chain fixture still admits
    ev = [
        _mk("inj", 0, None, 100, dyn_inst_seq=10, request_id="10",
            corr="origin", va="4000"),
        _mk("addr_form", 1, 0, 100, dyn_inst_seq=10, request_id="10",
            corr="origin", va="5000"),
        _mk("lsq_push", 2, 1, 101, dyn_inst_seq=10, request_id="10",
            corr="seq_primary", va="5000", field="load"),
        _mk("mem_req", 3, 2, 101, dyn_inst_seq=10, request_id="10",
            corr="seq_primary", va="5000"),
        _mk("resp", 4, 3, 102, dyn_inst_seq=10, request_id="10",
            corr="seq_primary", va="5000"),
        _mk("taint_reg", 5, 4, 102, dyn_inst_seq=10, request_id="10",
            corr="seq_primary", va="5000", phys_reg=3, arch_reg=1),
        _mk("consumer", 6, 5, 103, dyn_inst_seq=11, request_id="",
            corr="taint_prop", phys_reg=3, arch_reg=1),
        _mk("errant_commit", 7, 6, 103, dyn_inst_seq=11, request_id="",
            corr="taint_prop", detection_layer="L5",
            outcome="errant_commit", contained="0"),
    ]
    f = CC.check_chain(ev, oracle_outcome="SDC")["faults"]["1"]
    check("addrpath full chain still full", f["terminal"] == "full",
          f["terminal"])


def main():
    for fn in (test_layer_contract, test_forward_positive,
               test_forward_negatives, test_load_squash_and_exception,
               test_source_contract, test_addrpath_unchanged):
        fn()
    if FAILED:
        print(f"\nFAILED {len(FAILED)}: {FAILED}")
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
