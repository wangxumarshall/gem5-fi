#!/usr/bin/env python3
"""S11-F0-W5：lost store 的真实 request-suppressed containment。

实证（r6_s_unit_r3/S11-F0-W5_s1）：PRE hook 把 size 置 0 → `addReq` 的
空 byte-enable 使 `_reqs.size()==0` → 不创建 Request、不启动翻译、
`writebackStores` 直接 `completeStore`。真实链必须显式记录
  L2 request_suppressed（请求形成被抑制）
  L3 store_lost_contained（store 完成但无任何内存事务）
后续 L4/L5 N/A。不得伪造 mem_req/L2 消费者，也不得把空链判 PASS。

用法：python3 tests/test_lsu_s11_store_lost.py   退出码 0=全 PASS。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P   # noqa: E402
import lsu_chain_check as CC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def ev(kind, eid, parent, tick, **kw):
    d = {
        "kind": kind, "fault_id": "1", "event_id": str(eid),
        "parent_event_id": "" if parent is None else str(parent),
        "tick": str(tick), "cycle": "0", "dyn_inst_seq": "4136",
        "va": "4903f8", "corr": "", "field": "", "before": "", "after": "",
        "state_before": "", "state_after": "", "detection_layer": "",
        "contained": "", "outcome": "", "containment_layer": "",
        "containment_reason": "", "sq_idx": "", "pa": "",
        "store_dyn_inst_seq": "", "request_id": "", "phys_reg": "",
        "arch_reg": "",
    }
    d.update({k: str(v) for k, v in kw.items()})
    return d


def chain():
    return [
        ev("inj", 0, None, 100, field="size", before=8, after=0,
           corr="origin"),
        ev("addr_form", 1, 0, 100, field="size", before="4903f8",
           after="4903f8", corr="origin"),
        ev("request_suppressed", 2, 1, 100,
           field="request_suppressed:empty_byte_enable", before=8, after=0,
           state_before="byte_enable_empty", corr="seq_primary"),
        ev("sq_execute", 3, 2, 100, sq_idx=342, state_before="issued",
           corr="seq_primary"),
        ev("sq_complete", 4, 3, 101, sq_idx=342, state_after="completed",
           corr="seq_primary"),
        ev("store_lost_contained", 5, 4, 101,
           field="store_completed_without_mem_request",
           state_after="completed_no_request", detection_layer="L3",
           contained="1", outcome="contained", containment_layer="L3",
           containment_reason="store_lost_before_request_formation",
           corr="seq_primary"),
        ev("chain_end", 6, 5, 200, detection_layer="L5", contained="0",
           outcome="run_end", corr="none"),
    ]


def admit(events, oracle="Masked", rc=0):
    return CC.check_admission({
        "run_id": "S11-F0-W5", "activated": 1, "events": events, "rc": rc,
        "oracle_outcome": oracle,
        "containment": CC.containment_from_events(events, "S11-F0-W5"),
        "truncated": False,
    })


def main():
    print("[1] layer/field contract")
    check("request_suppressed is L2",
          P.KIND_LAYER.get("request_suppressed") == "L2",
          P.KIND_LAYER.get("request_suppressed"))
    check("store_lost_contained is L3",
          P.KIND_LAYER.get("store_lost_contained") == "L3",
          P.KIND_LAYER.get("store_lost_contained"))
    for kind in ("request_suppressed", "store_lost_contained"):
        check(f"{kind} has a required-field contract",
              kind in P.REQUIRED_FIELDS, kind)

    print("[2] real chain: L0 -> L1 -> L2 -> L3 containment")
    evs = chain()
    for e in evs:
        check(f"event {e['event_id']} validates", not P.validate_event(e),
              P.validate_event(e))
    f = CC.check_chain(evs, oracle_outcome="Masked")["faults"]["1"]
    check("terminal detected_contained",
          f["terminal"] == "detected_contained", f["terminal"])
    check("provable_to L3", f["provable_to"] == "L3", f["provable_to"])
    for a, b in (("L0", "L1"), ("L1", "L2"), ("L2", "L3")):
        check(f"{a}->{b} proven", f["edges"][f"{a}->{b}"] == "proven",
              f["edges"])
    cont = CC.containment_from_events(evs, "S11-F0-W5")
    check("containment layer L3", cont and cont["layer"] == "L3", cont)
    check("L4/L5 N/A", cont and cont["na_layers"] == ["L4", "L5"],
          cont and cont["na_layers"])
    r = admit(evs)
    check("admission accepts the real containment", r["admitted"] is True,
          (r["admitted"], r["violations"]))

    print("[3] negatives: no fabricated bridge, no missing corr")
    no_l2 = [evs[0], evs[1], evs[3], evs[4], evs[5], evs[6]]
    check("without request_suppressed the L3 terminal cannot be proven",
          CC.containment_from_events(no_l2, "S11-F0-W5") is None)
    bad_corr = chain()
    bad_corr[5]["corr"] = ""
    check("store_lost_contained without corr is not evidence",
          CC.containment_from_events(bad_corr, "S11-F0-W5") is None)
    check("no mem_req is fabricated anywhere on the chain",
          all(e["kind"] != "mem_req" for e in evs))

    print("[4] C++ source contract")
    lsq = (ROOT / "CHAOS/gem5/src/cpu/o3/lsq.cc").read_text()
    lsu = (ROOT / "CHAOS/gem5/src/cpu/o3/lsq_unit.cc").read_text()
    prop = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
            "CHAOSPropagation.cc").read_text()
    check("lsq.cc emits request_suppressed only on size==0 stores",
          "size == 0 && !pre_byte_enable.empty()" in lsq
          and "noteStoreRequestSuppressed" in lsq)
    check("lsq.cc does not create a Request for the suppressed store",
          "noteStoreRequestSuppressed" in lsq
          and "new Request" not in lsq[lsq.index("noteStoreRequestSuppressed"):
                                       lsq.index("inst->setRequest()")])
    check("lsq_unit.cc emits the L3 containment only for size==0",
          "store_idx->size() == 0" in lsu
          and "noteStoreLostContained" in lsu)
    check("propagation correlates by seq (no fabricated identity)",
          "noteStoreRequestSuppressed" in prop
          and "noteStoreLostContained" in prop
          and "correlateRequestBySeq(dyn_seq" in prop)
    check("containment is emitted once per seq",
          "store_lost_contained.count(dyn_seq)" in prop)

    print(f"FAILED: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
