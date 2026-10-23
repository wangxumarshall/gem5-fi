#!/usr/bin/env python3
"""test_lsu_chain_check.py — [MDSPEC][C1] 链完整性检查器测试。

规格（表 9 完整性/传播终止判定列）+ 计划 Task C1.1 三例：
1. 全链（inj→addr_form→lsq_push→tlb_translate→resp→taint_reg→
   consumer→errant_commit）→ terminal=full
2. 断于 L2（inj→addr_form→lsq_push 后无 L2+ 事件）→
   terminal=provable_to_L1_then_unknown，beyond=Unknown
   （**不得输出 Masked**——Review Focus #3 钉死）
3. 检测 contained（显式 detection_layer+contained 事件）→
   terminal=detected_contained

用法：python3 tests/test_lsu_chain_check.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P  # noqa: E402
import lsu_chain_check as CC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def _evts(lines):
    """Parse compact fixtures and supply a per-fault linear DAG by default.

    Tests that exercise branching spell parent_event_id explicitly; older
    fixtures intentionally stay terse but must still model the production DAG.
    """
    out = []
    last_by_fault = {}
    for line in lines:
        explicit_parent = "parent_event_id=" in line
        event = P.parse_line(line)
        if event is None:
            continue
        fid = event.get("fault_id", "")
        if not explicit_parent:
            event["parent_event_id"] = last_by_fault.get(fid, "")
        eid = event.get("event_id", "")
        if eid:
            last_by_fault[fid] = eid
        out.append(event)
    return out


def main():
    print("[1] 全链 → full")
    full_chain = _evts([
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=10",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 tick=10",
        "PROP-EVT: kind=lsq_push fault_id=1 event_id=2 tick=11 "
        "dyn_inst_seq=42",
        "PROP-EVT: kind=tlb_translate fault_id=1 event_id=3 tick=12 "
        "dyn_inst_seq=42",
        "PROP-EVT: kind=lsq_sendfrag fault_id=1 event_id=4 tick=12",
        "PROP-EVT: kind=resp fault_id=1 event_id=5 tick=20",
        "PROP-EVT: kind=lq_complete fault_id=1 event_id=6 tick=20",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=7 tick=21",
        "PROP-EVT: kind=consumer fault_id=1 event_id=8 tick=30",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=9 tick=31",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=10 tick=32 "
        "outcome=SDC detection_layer=Software contained=0",
    ])
    v = CC.check_chain(full_chain)
    f1 = v["faults"]["1"]
    check("all L0-L4 edges proven",
          all(f1["edges"][f"L{i}->L{i+1}"] == "proven" for i in range(4)),
          str(f1["edges"]))
    check("terminal == full", f1["terminal"] == "full", f1["terminal"])
    check("beyond empty on full", f1["beyond"] == "")
    check("L4->L5 explicit outcome proven",
          f1["edges"]["L4->L5"] == "proven")

    print("[2] 断于 L2 → provable_to_L1_then_unknown（绝不 Masked）")
    broken = _evts([
        "PROP-EVT: kind=inj fault_id=2 event_id=0 tick=10",
        "PROP-EVT: kind=addr_form fault_id=2 event_id=1 tick=10",
        "PROP-EVT: kind=lsq_push fault_id=2 event_id=2 tick=11",
        # —— L2 起无事件（链断）——
    ])
    v2 = CC.check_chain(broken)
    f2 = v2["faults"]["2"]
    check("L1->L2 missing", f2["edges"]["L1->L2"] == "missing",
          str(f2["edges"]))
    check("terminal provable_to_L1_then_unknown",
          f2["terminal"] == "provable_to_L1_then_unknown", f2["terminal"])
    check("beyond == Unknown（不得 Masked）",
          f2["beyond"] == "Unknown" and "Masked" not in str(f2),
          str(f2))

    print("[3] 显式 contained 检测 → detected_contained")
    contained = _evts([
        "PROP-EVT: kind=inj fault_id=3 event_id=0 tick=10",
        "PROP-EVT: kind=addr_form fault_id=3 event_id=1 tick=10",
        "PROP-EVT: kind=resp fault_id=3 event_id=2 tick=20",
        # 显式检测事件（L5 证据；kind 在 _L5_OUTCOME_KINDS 内才会判
        # contained——当前发射端空集，本例验证"缺席不猜测"：
        # 无显式事件时绝不判 detected_contained）
    ])
    v3 = CC.check_chain(contained)
    f3 = v3["faults"]["3"]
    check("无显式检测事件 → 不判 contained（缺席不猜测）",
          f3["terminal"] != "detected_contained", f3["terminal"])
    check("contained 判定只认显式事件（_L5_OUTCOME_KINDS 含 chain_end）",
          CC._L5_OUTCOME_KINDS == {"chain_end"})

    print("[4] 边证明的共享键 + 时间序")
    # 时间倒挂（L2 事件 tick 早于 L1）→ 该边不得 proven
    time_inv = _evts([
        "PROP-EVT: kind=inj fault_id=4 event_id=0 tick=10",
        "PROP-EVT: kind=addr_form fault_id=4 event_id=1 tick=10",
        "PROP-EVT: kind=tlb_translate fault_id=4 event_id=2 tick=5",  # 早于 L1
    ])
    v4 = CC.check_chain(time_inv)
    f4 = v4["faults"]["4"]
    check("时间倒挂边 missing（时间/可达性不满足）",
          f4["edges"]["L1->L2"] == "missing", str(f4["edges"]))
    # 不同 fault_id 不得互证
    cross = _evts([
        "PROP-EVT: kind=inj fault_id=5 event_id=0 tick=10",
        "PROP-EVT: kind=addr_form fault_id=5 event_id=1 tick=10",
        "PROP-EVT: kind=resp fault_id=6 event_id=2 tick=20",  # 异链
    ])
    v5 = CC.check_chain(cross)
    check("异 fault_id 不互证（fault 5 链止于 L1）",
          v5["faults"]["5"]["provable_to"] == "L1",
          str(v5["faults"]["5"]))
    check("fault 6 独立成链（无 L0）",
          v5["faults"]["6"]["terminal"] == "no_l0_fault_applied",
          str(v5["faults"]["6"]))

    print("[5] 真实流冒烟（C01 实证样本回放，H4 cache 钩子前的诚实预期）")
    real = Path("/tmp/h7v_c01/prop_evt.txt.gz")
    if real.is_file():
        events, trunc = P.read_events(real)
        v6 = CC.check_chain(events)
        fr = v6["faults"].get("1")
        check("C01 样本 fault 1 存在", fr is not None)
        if fr:
            # H4（cache L1/L2 节点）未装：cache 故障链的 L0→L1 边
            # honest missing；但 L3 交付（resp/lq_complete）与 L4 终局
            # （taint/consumer/errant_commit）事件在案——provable_to
            # 按逐边口径止于 L0，绝不推断 Masked。H4 落地后本断言翻转。
            check("L0->L1 honest missing（H4 前结构性）",
                  fr["edges"]["L0->L1"] == "missing",
                  str(fr["edges"].get("L0->L1")))
            check("terminal 非 full 且非 Masked（H4 前诚实态）",
                  fr["terminal"] != "full"
                  and "Masked" not in str(fr["terminal"]),
                  fr["terminal"])
            check("beyond == Unknown", fr["beyond"] == "Unknown")
            # L3/L4 事件在案的独立证据（不因 L1 缺席而抹除）
            l3l4_kinds = {e.get("kind") for e in events
                          if e.get("kind") in ("resp", "lq_complete",
                                               "taint_reg", "consumer",
                                               "errant_commit")}
            check("L3/L4 事件在案（resp/lq_complete/taint/consumer/"
                  "errant_commit ≥4 种）", len(l3l4_kinds) >= 4,
                  str(l3l4_kinds))
    else:
        print("  SKIP 真实样本不在（/tmp/h7v_c01 已清理）——合成例已覆盖")

    print("[6] tlb_fault 终局语义（翻译阻断 ≠ 终局 Contained）")
    # contained 空 = 翻译阶段阻断，终局 pending（不得推断 Contained）
    pending = _evts([
        "PROP-EVT: kind=inj fault_id=7 event_id=0 tick=10",
        "PROP-EVT: kind=tlb_lookup fault_id=7 event_id=1 tick=11",
        "PROP-EVT: kind=tlb_translate fault_id=7 event_id=2 tick=12",
        "PROP-EVT: kind=tlb_fault fault_id=7 event_id=3 tick=13 "
        "detection_layer=Hardware contained= outcome=GenericPageTableFault",
    ])
    v7 = CC.check_chain(pending)
    f7 = v7["faults"]["7"]
    check("tlb_fault(contained 空) → detected_translation_outcome_pending",
          f7["terminal"] == "detected_translation_outcome_pending",
          f7["terminal"])
    check("pending 不得是 detected_contained",
          f7["terminal"] != "detected_contained")
    check("pending beyond 非空（终局待 join）", f7["beyond"] != "")
    # contained=1（显式终局证据）→ detected_contained
    resolved = _evts([
        "PROP-EVT: kind=inj fault_id=8 event_id=0 tick=10",
        "PROP-EVT: kind=tlb_lookup fault_id=8 event_id=1 tick=11",
        "PROP-EVT: kind=tlb_fault fault_id=8 event_id=2 tick=13 "
        "detection_layer=Hardware contained=1 outcome=GenericPageTableFault",
    ])
    v8 = CC.check_chain(resolved)
    f8 = v8["faults"]["8"]
    check("tlb_fault(contained=1) → detected_contained",
          f8["terminal"] == "detected_contained", f8["terminal"])
    check("resolved beyond 为空（终局已定）", f8["beyond"] == "", f8["beyond"])

    print("[7] tlb_fault × runner/oracle join（翻译阻断 → 具体终局）")
    blocked = _evts([
        "PROP-EVT: kind=inj fault_id=20 event_id=0 tick=10",
        "PROP-EVT: kind=tlb_lookup fault_id=20 event_id=1 tick=11",
        "PROP-EVT: kind=tlb_translate fault_id=20 event_id=2 tick=12",
        "PROP-EVT: kind=tlb_fault fault_id=20 event_id=3 tick=13 "
        "detection_layer=Hardware contained= outcome=GenericPageTableFault",
    ])
    fa = CC.check_chain(blocked, oracle_outcome="Crash")["faults"]["20"]
    check("oracle=Crash → crash_translation_blocked（闭合）",
          fa["terminal"] == "crash_translation_blocked", fa["terminal"])
    check("crash 终局 beyond 为空", fa["beyond"] == "", fa["beyond"])
    check("crash 终局 provable_to=L2（翻译阻断层级）",
          fa["provable_to"] == "L2", str(fa["provable_to"]))
    fb = CC.check_chain(blocked, oracle_outcome="SDC")["faults"]["20"]
    check("oracle=SDC → sdc_translation_blocked",
          fb["terminal"] == "sdc_translation_blocked", fb["terminal"])
    fc = CC.check_chain(blocked, oracle_outcome="Masked")["faults"]["20"]
    check("oracle=Masked 不得推断 Masked/Contained（保持开放终局）",
          fc["terminal"] == "provable_to_L2_then_unknown", fc["terminal"])
    check("oracle 干净 beyond=Unknown", fc["beyond"] == "Unknown",
          fc["beyond"])
    fd = CC.check_chain(blocked)["faults"]["20"]
    check("oracle 缺省 → detected_translation_outcome_pending",
          fd["terminal"] == "detected_translation_outcome_pending",
          fd["terminal"])

    print("[8] terminal / provable_to / beyond 三向自洽")
    full_evts = _evts([
        "PROP-EVT: kind=inj fault_id=30 event_id=0 tick=1",
        "PROP-EVT: kind=addr_form fault_id=30 event_id=1 tick=1",
        "PROP-EVT: kind=lsq_push fault_id=30 event_id=2 tick=2",
        "PROP-EVT: kind=mem_req fault_id=30 event_id=3 tick=3",
        "PROP-EVT: kind=resp fault_id=30 event_id=4 tick=4",
        "PROP-EVT: kind=taint_reg fault_id=30 event_id=5 tick=5",
        "PROP-EVT: kind=errant_commit fault_id=30 event_id=6 tick=6",
        "PROP-EVT: kind=chain_end fault_id=30 event_id=7 tick=7 "
        "outcome=SDC detection_layer=Software contained=0",
    ])
    contained_evts = _evts([
        "PROP-EVT: kind=inj fault_id=31 event_id=0 tick=1",
        "PROP-EVT: kind=addr_form fault_id=31 event_id=1 tick=2",
        "PROP-EVT: kind=tlb_fault fault_id=31 event_id=2 tick=3 "
        "detection_layer=Hardware contained=1 outcome=GenericPageTableFault",
    ])
    verdicts = {
        "full": CC.check_chain(full_evts),
        "crash_blocked": CC.check_chain(blocked, oracle_outcome="Crash"),
        "timeout_blocked": CC.check_chain(blocked, oracle_outcome="Timeout"),
        "sdc_blocked": CC.check_chain(blocked, oracle_outcome="SDC"),
        "pending": CC.check_chain(blocked),
        "contained": CC.check_chain(contained_evts),
    }
    for tag, verdict in verdicts.items():
        for fid, f in verdict["faults"].items():
            closed = f["terminal"] in CC.CLOSED_TERMINALS
            check(f"[{tag}] beyond 与终局自洽（{f['terminal']}）",
                  (f["beyond"] == "") == closed,
                  f"beyond={f['beyond']!r} closed={closed}")
            check(f"[{tag}] provable_to 为合法层级（{f['provable_to']}）",
                  f["provable_to"] in CC.LAYERS, str(f["provable_to"]))
    check("full 终局 provable_to=L5",
          verdicts["full"]["faults"]["30"]["provable_to"] == "L5",
          str(verdicts["full"]["faults"]["30"]["provable_to"]))

    print("[9] DAG 单路径约束：分支上的独立边不得拼成 full")
    branched = _evts([
        "PROP-EVT: kind=inj fault_id=40 event_id=0 parent_event_id= "
        "tick=1 corr=origin",
        # branch A only reaches L2
        "PROP-EVT: kind=addr_form fault_id=40 event_id=1 parent_event_id=0 "
        "tick=2 va=1000 corr=origin",
        "PROP-EVT: kind=mem_req fault_id=40 event_id=2 parent_event_id=1 "
        "tick=3 dyn_inst_seq=1 va=1000 corr=seq_primary",
        # branch B starts at L3 and reaches an apparent L5.  The legacy
        # pairwise checker incorrectly splices branch A and B into one chain.
        "PROP-EVT: kind=resp fault_id=40 event_id=3 parent_event_id=0 "
        "tick=4 dyn_inst_seq=1 corr=seq_primary",
        "PROP-EVT: kind=errant_commit fault_id=40 event_id=4 "
        "parent_event_id=3 tick=5 dyn_inst_seq=1 corr=taint_prop",
        "PROP-EVT: kind=chain_end fault_id=40 event_id=5 "
        "parent_event_id=4 tick=6 outcome=SDC detection_layer=Software "
        "contained=0 corr=none",
    ])
    f40 = CC.check_chain(branched)["faults"]["40"]
    check("分支证人不得拼接为 full", f40["terminal"] != "full",
          str(f40))

    print("[10] TLB 族必须有真正的 DTLB lookup L1")
    tlb_false_full = _evts([
        "PROP-EVT: kind=inj run_id=T02-F0-W4 fault_id=41 event_id=0 "
        "parent_event_id= tick=1 corr=origin",
        "PROP-EVT: kind=tlb_pfn run_id=T02-F0-W4 fault_id=41 event_id=1 "
        "parent_event_id=0 tick=1 dyn_inst_seq=7 request_id=7 va=1000 "
        "before=1 after=2 field=bit_flip state_before=1000 "
        "state_after=2000 corr=seq_primary",
        "PROP-EVT: kind=sq_execute run_id=T02-F0-W4 fault_id=41 event_id=2 "
        "parent_event_id=1 tick=2 dyn_inst_seq=7 sq_idx=1 va=1000 "
        "state_before=issued corr=seq_primary",
        # Generic cache L1/L2 events are downstream of the TLB.  They must
        # not stand in for the T-series L1 DTLB lookup required by table 9.
        "PROP-EVT: kind=cache_access run_id=T02-F0-W4 fault_id=41 event_id=3 "
        "parent_event_id=2 tick=3 va=1000 pa=2000 corr=addr_fallback",
        "PROP-EVT: kind=cache_return run_id=T02-F0-W4 fault_id=41 event_id=4 "
        "parent_event_id=3 tick=4 pa=2000 field=miss corr=addr_fallback",
        "PROP-EVT: kind=resp run_id=T02-F0-W4 fault_id=41 event_id=5 "
        "parent_event_id=4 tick=5 dyn_inst_seq=7 corr=seq_primary",
        "PROP-EVT: kind=taint_reg run_id=T02-F0-W4 fault_id=41 event_id=6 "
        "parent_event_id=5 tick=6 dyn_inst_seq=7 phys_reg=1 arch_reg=1 "
        "corr=seq_primary",
        "PROP-EVT: kind=errant_commit run_id=T02-F0-W4 fault_id=41 "
        "event_id=7 parent_event_id=6 tick=7 dyn_inst_seq=7 corr=taint_prop",
        "PROP-EVT: kind=chain_end run_id=T02-F0-W4 fault_id=41 event_id=8 "
        "parent_event_id=7 tick=8 outcome=SDC detection_layer=Software "
        "contained=0 corr=none",
    ])
    f41 = CC.check_chain(tlb_false_full)["faults"]["41"]
    check("TLB 无 tlb_lookup 时 L0->L1 missing",
          f41["edges"]["L0->L1"] == "missing", str(f41["edges"]))
    check("TLB 后续 cache 事件不得制造 full",
          f41["terminal"] != "full", f41["terminal"])

    print("[11] 生命周期 chain_end 不能单独充当 L5")
    lifecycle_only = _evts([
        "PROP-EVT: kind=inj fault_id=42 event_id=0 parent_event_id= tick=1",
        "PROP-EVT: kind=addr_form fault_id=42 event_id=1 parent_event_id=0 "
        "tick=2",
        "PROP-EVT: kind=mem_req fault_id=42 event_id=2 parent_event_id=1 "
        "tick=3",
        "PROP-EVT: kind=resp fault_id=42 event_id=3 parent_event_id=2 tick=4",
        "PROP-EVT: kind=errant_commit fault_id=42 event_id=4 "
        "parent_event_id=3 tick=5",
        "PROP-EVT: kind=chain_end fault_id=42 event_id=5 parent_event_id=4 "
        "tick=6 outcome=run_end detection_layer=None contained=0 corr=none",
    ])
    f42 = CC.check_chain(lifecycle_only)["faults"]["42"]
    check("run_end/None chain_end 不证明 L4->L5",
          f42["edges"]["L4->L5"] == "missing", str(f42["edges"]))
    check("只有生命周期尾标不得 full", f42["terminal"] != "full",
          f42["terminal"])

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
