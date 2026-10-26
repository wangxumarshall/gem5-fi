#!/usr/bin/env python3
"""test_lsu_multifault_admission.py — [0202-T02F2] 多 fault 样本的保守准入口径。

规则（用户 2026-10-27）：一个运行里**每个实际 activated fault** 都必须独立形成
（a）连续 parent-event 的完整 L0→L5，或（b）真实、非 lifecycle、字段完整的提前
containment。**任一 activated fault 未闭合 ⇒ 整个样本不 admitted**。禁止改成
"任选一条通过即可"，禁止跨 fault / 跨 sibling branch 拼链，禁止 `chain_end` 充当
terminal。

本套件同时钉死"三个选择器一致"：`evaluate_sample` 的顶层 terminal 与准入排序同源
（已证有序路径最长），`containment_from_events` 在多 fault 且未指明 fault_id 时
**返回 None**（拒绝静默重选）。

用法：python3 tests/test_lsu_multifault_admission.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P        # noqa: E402
import lsu_chain_check as CC       # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("  PASS " if cond else "  FAIL ") + name
          + (("  :: " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def _p(*lines):
    return [P.parse_line(l) for l in lines]


def l0_l4(rid, fid, base, tick0=1):
    """inj → tlb_lookup → tlb_pfn → lq_read → taint_reg（L0→L4，连续父链）。"""
    b = base
    return _p(
        f"PROP-EVT: kind=inj run_id={rid} fault_id={fid} event_id={b} "
        f"parent_event_id= tick={tick0} corr=origin",
        f"PROP-EVT: kind=tlb_lookup run_id={rid} fault_id={fid} event_id={b+1} "
        f"parent_event_id={b} tick={tick0+1} dyn_inst_seq=7 request_id=7 va=1000 "
        f"entry_index=1 field=post_lookup state_before=x state_after=y corr=origin",
        f"PROP-EVT: kind=tlb_pfn run_id={rid} fault_id={fid} event_id={b+2} "
        f"parent_event_id={b+1} tick={tick0+2} dyn_inst_seq=7 request_id=7 va=1000 "
        f"pa=2000 corr=origin",
        f"PROP-EVT: kind=lq_read run_id={rid} fault_id={fid} event_id={b+3} "
        f"parent_event_id={b+2} tick={tick0+3} dyn_inst_seq=7 request_id=7 va=1000 "
        f"pa=2000 corr=origin",
        f"PROP-EVT: kind=taint_reg run_id={rid} fault_id={fid} event_id={b+4} "
        f"parent_event_id={b+3} tick={tick0+4} dyn_inst_seq=7 request_id=7 corr=origin")


def to_l5(rid, fid, base, tick0=6):
    return _p(
        f"PROP-EVT: kind=errant_commit run_id={rid} fault_id={fid} event_id={base} "
        f"parent_event_id={base-1} tick={tick0} dyn_inst_seq=7 request_id=7 "
        f"detection_layer=L5 outcome=errant_commit contained=0 corr=taint_prop")


def squash(rid, fid, base, tick0=7):
    return _p(
        f"PROP-EVT: kind=squash_masked run_id={rid} fault_id={fid} event_id={base} "
        f"parent_event_id={base-1} tick={tick0} dyn_inst_seq=7 request_id=7 va=1000 "
        f"pa=2000 field=squashed_load outcome=masked detection_layer=L4 contained=1 "
        f"containment_layer=L4 containment_reason=squash_replay corr=addr_fallback")


def chain_end(rid, fid, base, tick0=99, outcome="run_end", det="None", contained=0):
    return _p(
        f"PROP-EVT: kind=chain_end run_id={rid} fault_id={fid} event_id={base} "
        f"parent_event_id={base-2} tick={tick0} outcome={outcome} "
        f"detection_layer={det} contained={contained} corr=none")


def adm(rid, evts, **kw):
    return CC.check_admission({"run_id": rid, "activated": kw.pop("activated", 1),
                               "events": evts, "rc": kw.pop("rc", 0), **kw})


def main():
    rid = "T90-F2-W4"

    print("[1] 两个 fault 均完整 L0→L5 ⇒ 样本 PASS")
    f1 = l0_l4(rid, 1, 0) + to_l5(rid, 1, 5) + chain_end(rid, 1, 6)
    f2 = l0_l4(rid, 2, 100, tick0=20) + to_l5(rid, 2, 105, tick0=26) + chain_end(rid, 2, 106)
    r = adm(rid, f1 + f2)
    check("admitted=True", r["admitted"] is True, r)
    check("path=full_chain", r["path"] == "full_chain", r["path"])
    check("terminal=full", r["terminal"] == "full", r["terminal"])

    print("[2] 一个完整 + 一个真实 squash containment ⇒ 样本 PASS")
    f3 = l0_l4(rid, 2, 100, tick0=20) + squash(rid, 2, 105, tick0=26) + \
        chain_end(rid, 2, 106, outcome="detected_contained", det="L4", contained=1)
    r = adm(rid, f1 + f3)
    check("admitted=True", r["admitted"] is True, r)
    ev = CC.evaluate_sample(f1 + f3, rid)
    check("fault 2 contained=True", ev["per_fault"]["2"]["contained"] is True,
          ev["per_fault"]["2"])
    check("fault 2 admission=True", ev["per_fault"]["2"]["admission"] is True)

    print("[3] 一个完整 + 一个 L4 unknown ⇒ 样本 FAIL")
    f4 = l0_l4(rid, 2, 100, tick0=20) + chain_end(rid, 2, 105)
    r = adm(rid, f1 + f4)
    check("admitted=False", r["admitted"] is False, r)
    ev = CC.evaluate_sample(f1 + f4, rid)
    check("fault 1 仍独立闭合", ev["per_fault"]["1"]["admission"] is True)
    check("fault 2 未闭合（provable_to L4）",
          ev["per_fault"]["2"]["admission"] is False
          and ev["per_fault"]["2"]["provable_to"] == "L4", ev["per_fault"]["2"])
    check("all_activated_faults_closed=False", ev["all_activated_faults_closed"] is False)

    print("[4] 一个完整 + 另一个只有 chain_end 型 containment ⇒ 样本 FAIL")
    f5 = l0_l4(rid, 2, 100, tick0=20) + \
        chain_end(rid, 2, 105, outcome="detected_contained", det="L4", contained=1)
    r = adm(rid, f1 + f5)
    check("admitted=False（生命周期 chain_end 不作检测/含住证据）",
          r["admitted"] is False, r)
    ev = CC.evaluate_sample(f1 + f5, rid)
    check("fault 2 contained=False", ev["per_fault"]["2"]["contained"] is False,
          ev["per_fault"]["2"]["containment"])
    check("fault 2 terminal 非 detected_contained（chain_end 不算）",
          ev["per_fault"]["2"]["terminal"] != "detected_contained",
          ev["per_fault"]["2"]["terminal"])

    print("[5] 同一 fault 内 L4 与 errant_commit 为 sibling branches ⇒ 不得拼接")
    br = l0_l4(rid, 1, 0)
    sib = _p(
        f"PROP-EVT: kind=errant_commit run_id={rid} fault_id=1 event_id=5 "
        f"parent_event_id=3 tick=6 dyn_inst_seq=7 request_id=7 detection_layer=L5 "
        f"outcome=errant_commit contained=0 corr=taint_prop")
    # event 4 = taint_reg(parent 3) 与 event 5 = errant_commit(parent 3) 同父不同枝
    r = adm(rid, br + sib + chain_end(rid, 1, 6))
    check("admitted=False（无单一路径覆盖 L4→L5）", r["admitted"] is False, r)
    check("terminal != full", r["terminal"] != "full", r["terminal"])

    print("[6] 不同 fault 的 L4/L5：不得互相补链")
    g1 = l0_l4(rid, 1, 0) + to_l5(rid, 1, 5) + chain_end(rid, 1, 6)
    g2 = l0_l4(rid, 2, 100, tick0=20) + chain_end(rid, 2, 105)
    ev = CC.evaluate_sample(g1 + g2, rid)
    check("fault 2 terminal 不因 fault 1 的 L5 而变 full",
          ev["per_fault"]["2"]["terminal"] != "full", ev["per_fault"]["2"]["terminal"])
    check("fault 2 的 ancestry 只含自己的 inj（fault_id=2）",
          any(a["event_id"] == "100" for a in ev["per_fault"]["2"]["selected_ancestry"]),
          ev["per_fault"]["2"]["selected_ancestry"][:2])
    check("样本 admitted=False", ev["admitted"] is False)

    print("[7] 单 fault 旧行为不回归")
    r = adm(rid, f1)
    check("单 fault full ⇒ admitted=True/path=full_chain",
          r["admitted"] is True and r["path"] == "full_chain", r)
    r2 = adm(rid, l0_l4(rid, 1, 0) + chain_end(rid, 1, 5))
    check("单 fault L4-only ⇒ admitted=False", r2["admitted"] is False, r2)

    print("[8] containment_from_events 在多 fault 且未指明 fault_id 时拒绝静默重选")
    check("fault_id=None + 2 faults ⇒ None",
          CC.containment_from_events(f1 + f3, rid) is None)
    c2 = CC.containment_from_events(f1 + f3, rid, fault_id="2")
    check("fault_id='2' ⇒ 该 fault 的含住束", isinstance(c2, dict)
          and c2.get("layer") == "L4", c2)
    check("单 fault + fault_id=None ⇒ 仍派生（旧行为不变）",
          CC.containment_from_events(f3, rid) is not None)

    print("[9] per-fault evaluator 字段齐备")
    ev = CC.evaluate_sample(f1 + f3, rid)
    need = {"fault_id", "activated", "selected_ancestry", "terminal", "provable_to",
            "contained", "containment", "admission", "violations"}
    for fid, f in ev["per_fault"].items():
        check(f"fault {fid} 字段齐备", need.issubset(set(f)), sorted(set(f)))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
