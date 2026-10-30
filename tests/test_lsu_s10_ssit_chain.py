#!/usr/bin/env python3
"""S10 SSIT 真实传播层级契约（R6-S-REPAIR2 2026-10-30）。

证据事实（r6_s_unit_r3 S10 四格 seed1）：
  inj(L0, SSID 156→485) → ssit_consult(L1) → chain_end；
  consult 的 counterfactual=actual=0（别名 SSID 的 LFST 槽为空，预测未改变）。
真实终局不是伪造 L2–L5，而是“污染状态被读取但依赖预测不变”的 detected
containment。

本测试把用户工作令 §七 的层级钉死：
  L0 inj / L1 ssit_corrupt（SSIT 字段被污染）/
  L2 ssit_consult（读取污染状态）/
  L3 ssit_dep_effective（错误依赖决策生效）/
  L4 ssit_violation（真实 violation/replay 后果）/
  L1/L2 containment：no-effect / epoch-clear（未影响决策即结束）。
另覆盖：一源多 consumer（fan-out）、无关 PC 不继承、缺 corr/parent 拒绝、
effective 之后不得再声称 L2 含住。

用法：python3 tests/test_lsu_s10_ssit_chain.py   退出码 0=全 PASS。
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
        "tick": str(tick), "cycle": "0", "corr": "origin",
        "pc": "401098", "field": "", "detection_layer": "", "contained": "",
        "outcome": "", "before": "", "after": "", "entry_index": "",
        "state_before": "", "va": "", "pa": "", "dyn_inst_seq": "",
        "store_dyn_inst_seq": "", "request_id": "", "phys_reg": "",
        "arch_reg": "",
    }
    d.update({k: str(v) for k, v in kw.items()})
    return d


def base():
    return [
        ev("inj", 0, None, 100, field="ssid", before=156, after=485),
        ev("ssit_corrupt", 1, 0, 100, field="ssid", before=156, after=485,
           entry_index=485),
    ]


def consult(eid, parent, tick, before=0, after=0, corr="origin"):
    return ev("ssit_consult", eid, parent, tick, field="pred_dep",
              before=before, after=after, entry_index=485, corr=corr)


def no_effect(eid, parent, tick, before=0, after=0, corr="origin"):
    return ev("ssit_no_effect", eid, parent, tick, field="pred_dep",
              before=before, after=after, entry_index=485, corr=corr,
              detection_layer="L2", contained="1", outcome="contained",
              containment_layer="L2",
              containment_reason="ssit_consult_prediction_unchanged")


def chain_end(eid, parent, tick):
    # chain_end's required-field contract includes detection_layer; the
    # lifecycle marker still never counts as L5 evidence (_explicit_l5
    # excludes lifecycle kinds regardless of this value).
    return ev("chain_end", eid, parent, tick, detection_layer="L5",
              contained="0", outcome="run_end", corr="none")


def admit(events, oracle="Masked", rc=0):
    return CC.check_admission({
        "run_id": "S10-F0-W5", "activated": 1, "events": events, "rc": rc,
        "oracle_outcome": oracle,
        "containment": CC.containment_from_events(events, "S10-F0-W5"),
        "truncated": False,
    })


def main():
    print("[1] layer contract: real semantics, not legacy names")
    want = {
        "ssit_corrupt": "L1", "ssit_consult": "L2",
        "ssit_dep_effective": "L3", "ssit_violation": "L4",
        "ssit_no_effect": "L2", "ssit_epoch_clear": "L1",
    }
    for kind, layer in want.items():
        check(f"{kind} is {layer}", P.KIND_LAYER.get(kind) == layer,
              P.KIND_LAYER.get(kind))
    for kind in want:
        check(f"{kind} has a required-field contract",
              kind in P.REQUIRED_FIELDS, kind)

    print("[2] no-effect containment (the four measured cells' real path)")
    evs = base() + [consult(2, 1, 200), no_effect(3, 2, 200),
                    chain_end(4, 3, 1000)]
    for e in evs:
        check(f"event {e['event_id']} validates", not P.validate_event(e),
              P.validate_event(e))
    f = CC.check_chain(evs, oracle_outcome="Masked")["faults"]["1"]
    check("terminal detected_contained", f["terminal"] == "detected_contained",
          f["terminal"])
    check("provable_to L2", f["provable_to"] == "L2", f["provable_to"])
    cont = CC.containment_from_events(evs, "S10-F0-W5")
    check("containment layer L2", cont and cont["layer"] == "L2", cont)
    check("later layers N/A", cont and cont["na_layers"] == ["L3", "L4", "L5"],
          cont and cont["na_layers"])
    r = admit(evs)
    check("admission accepts the real containment", r["admitted"] is True,
          (r["admitted"], r["violations"]))

    print("[3] wrong dependency effective -> L3, not a premature L2 terminal")
    evs = base() + [consult(2, 1, 200, before=9901, after=0),
                    ev("ssit_dep_effective", 3, 2, 210, field="pred_dep",
                       before=9901, after=0, entry_index=485),
                    chain_end(4, 3, 1000)]
    f = CC.check_chain(evs, oracle_outcome="SDC")["faults"]["1"]
    check("L3 effective is provable", f["provable_to"] == "L3",
          f["provable_to"])
    check("no containment claimed without a real consequence",
          CC.containment_from_events(evs, "S10-F0-W5") is None)
    check("not admitted at L3", admit(evs, oracle="SDC", rc=1)["admitted"] is False)

    print("[4] real violation/replay containment at L4")
    evs = base() + [consult(2, 1, 200, before=9901, after=0),
                    ev("ssit_dep_effective", 3, 2, 210, field="pred_dep",
                       before=9901, after=0, entry_index=485),
                    ev("ssit_violation", 4, 3, 300, field="dep_miss_violation",
                       state_before=485, detection_layer="L4", contained="1",
                       outcome="contained", containment_layer="L4",
                       containment_reason="mem_order_violation_replay"),
                    chain_end(5, 4, 1000)]
    cont = CC.containment_from_events(evs, "S10-F0-W5")
    check("L4 violation containment layer L4", cont and cont["layer"] == "L4",
          cont)
    check("na_layers L5 only", cont and cont["na_layers"] == ["L5"],
          cont and cont["na_layers"])
    check("admitted via L4 containment", admit(evs)["admitted"] is True)

    print("[5] overwrite-before-use / epoch clear containment")
    evs = base() + [ev("ssit_epoch_clear", 2, 1, 500, field="ssid_cleared",
                       state_before=485, detection_layer="L1", contained="1",
                       outcome="contained", containment_layer="L1",
                       containment_reason="epoch_clear_before_use"),
                    chain_end(3, 2, 1000)]
    cont = CC.containment_from_events(evs, "S10-F0-W5")
    check("clear containment layer L1", cont and cont["layer"] == "L1", cont)
    check("clear na_layers L2-L5",
          cont and cont["na_layers"] == ["L2", "L3", "L4", "L5"],
          cont and cont["na_layers"])
    check("clear admitted", admit(evs)["admitted"] is True)

    print("[6] fan-out: one corrupted entry, several real consults")
    evs = base() + [consult(2, 1, 200), no_effect(3, 2, 200),
                    consult(4, 3, 300), consult(5, 4, 400),
                    chain_end(6, 5, 1000)]
    cont = CC.containment_from_events(evs, "S10-F0-W5")
    check("fan-out keeps the L2 containment", cont and cont["layer"] == "L2",
          cont)
    check("fan-out admits", admit(evs)["admitted"] is True)
    # A later effective use must invalidate the earlier no-effect claim.
    evs_bad = evs[:-1] + [
        ev("ssit_dep_effective", 6, 5, 410, field="pred_dep",
           before=9901, after=0, entry_index=485),
        chain_end(7, 6, 1000)]
    check("later effective use disqualifies the L2 containment",
          CC.containment_from_events(evs_bad, "S10-F0-W5") is None)

    print("[7] negatives: missing corr / parent / unrelated PC")
    bad_corr = base() + [consult(2, 1, 200),
                         no_effect(3, 2, 200, corr="")]
    check("no-effect without corr is not evidence",
          CC.containment_from_events(bad_corr, "S10-F0-W5") is None)
    orphan = base() + [consult(2, None, 200), no_effect(3, 2, 200)]
    f = CC.check_chain(orphan, oracle_outcome="Masked")["faults"]["1"]
    check("orphan consult cannot prove L1->L2",
          f["edges"].get("L1->L2") == "missing", f["edges"].get("L1->L2"))
    # A consult on an unrelated PC belongs to a DIFFERENT fault_id (the
    # injector's s10_entries lookup is keyed by the corrupted load PC). It
    # must never inherit fault 1's L0/L1 prefix or containment.
    unrelated = base() + [
        consult(2, 1, 150), no_effect(3, 2, 150),
        ev("ssit_consult", 4, None, 200, fault_id="2", pc="deadbeef",
           field="pred_dep", before=0, after=0, entry_index=999),
        ev("ssit_no_effect", 5, 4, 200, fault_id="2", pc="deadbeef",
           field="pred_dep", before=0, after=0, entry_index=999,
           detection_layer="L2", contained="1", outcome="contained",
           containment_layer="L2", containment_reason="x"),
        chain_end(6, 3, 1000)]
    recs = CC.check_chain(unrelated, oracle_outcome="Masked")["faults"]
    check("unrelated PC is a separate fault with no L0 prefix",
          recs["2"]["terminal"] != "detected_contained"
          and recs["2"]["provable_to"] != "L2",
          (recs["2"]["terminal"], recs["2"]["provable_to"]))
    check("fault 1 keeps its own real containment",
          recs["1"]["terminal"] == "detected_contained",
          recs["1"]["terminal"])

    print("[8] C++ source contract")
    ss = (ROOT / "CHAOS/gem5/src/cpu/o3/store_set.cc").read_text()
    lh = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh").read_text()
    lc = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc").read_text()
    check("StoreSet::issued consults a real S10 issued hook",
          "chaosS10Issued" in ss and "chaosS10Issued(" in ss)
    check("issued hook runs for loads too (before the is_store early return)",
          ss.find("chaosS10Issued(") < ss.find("if (!is_store)"))
    check("StoreSet::clear reports the epoch boundary",
          "chaosS10Clear" in ss and "chaosS10Clear(" in ss)
    check("LSQFwd header declares the issued/clear callbacks",
          "s10IssuedCb" in lh and "s10ClearCb" in lh
          and "chaosS10Issued" in lh and "chaosS10Clear" in lh)
    for kind in ("ssit_corrupt", "ssit_consult", "ssit_dep_effective",
                 "ssit_violation", "ssit_no_effect", "ssit_epoch_clear"):
        check(f"LSQFwd emits {kind}", kind in lc)

    print(f"FAILED: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
