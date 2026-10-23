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
import os
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
        # [R6-GATE-D1] L5 证据 = 真实检测事件：非生命周期 kind 且携带
        # detection_layer + outcome + 链关联 corr（此处 errant_commit 由离线
        # reclass join 富化：错误提交已确认 + 检测/结局载荷）。生命周期
        # chain_end 不再充当 L5。
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=9 tick=31 "
        "detection_layer=Software outcome=SDC contained=0 corr=taint_prop",
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
        # 显式检测事件（L5 证据）只认"真实检测事件"（D1）：本例验证
        # "缺席不猜测"——无真实检测事件时绝不判 detected_contained。
    ])
    v3 = CC.check_chain(contained)
    f3 = v3["faults"]["3"]
    check("无显式检测事件 → 不判 contained（缺席不猜测）",
          f3["terminal"] != "detected_contained", f3["terminal"])
    check("L5 证据由 _explicit_l5 严格定义（生命周期 chain_end 恒 False）",
          CC._LIFECYCLE_KINDS == {"chain_end"}
          and CC._explicit_l5(P.parse_line(
              "PROP-EVT: kind=chain_end fault_id=3 outcome=SDC "
              "detection_layer=Software contained=0 corr=none")) is False)

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
        # [R6-GATE-D1] L5 见证 = 富化检测事件（dl+outcome+链关联 corr）
        "PROP-EVT: kind=errant_commit fault_id=30 event_id=7 tick=7 "
        "detection_layer=Software outcome=SDC contained=0 corr=taint_prop",
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

    print("[12] R6-GATE hard-admission gate（activated 样本 READY 判定的硬门）")
    # 门禁：activated 样本仅当 (1) family-specific 完整 L0→L5 链，或
    # (2) 显式 containment（含层级+理由+逐层指标）且后续层全 N/A(contained)
    # 才 admitted；六类禁用情形一律响亮拒绝。
    def adm(events, **kw):
        bundle = {"run_id": kw.pop("run_id", "G1"), "activated": 1,
                  "events": events}
        bundle.update(kw)
        return CC.check_admission(bundle)

    # (a) 正常完整链 → admitted（对照，证明门禁不是无条件拒绝）
    good = adm(full_chain)
    check("full 链 admitted=True（对照组）", good["admitted"] is True,
          str(good["violations"]))
    check("full 链 path=full_chain", good["path"] == "full_chain",
          str(good.get("path")))

    # (b) activated 样本含 Unknown → 拒绝
    unk = _evts([
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=1",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 tick=2",
        "PROP-EVT: kind=resp fault_id=1 event_id=2 tick=3 "
        "evidence_status=unknown",
    ])
    r = adm(unk, run_id="U1")
    check("Unknown activated 样本被拒（unknown_in_activated_chain）",
          r["admitted"] is False and "unknown_in_activated_chain" in " ".join(
              r["violations"]), str(r["violations"]))

    # (c) TLB 族用 cache_access 冒充 L1 → 拒绝
    tlb_fake = _evts([
        "PROP-EVT: kind=inj run_id=T02-F0-W4 fault_id=1 event_id=0 "
        "parent_event_id= tick=1",
        "PROP-EVT: kind=cache_access run_id=T02-F0-W4 fault_id=1 event_id=1 "
        "parent_event_id=0 tick=2 va=1000 pa=2000",
        "PROP-EVT: kind=resp run_id=T02-F0-W4 fault_id=1 event_id=2 "
        "parent_event_id=1 tick=3 dyn_inst_seq=7",
    ])
    r = adm(tlb_fake, run_id="T02-F0-W4")
    check("TLB L1 被 cache_access 冒充被拒",
          r["admitted"] is False and "tlb_l1_faked_by_cache_access"
          in " ".join(r["violations"]), str(r["violations"]))

    # (d) 跨分支拼接（两分支各自补出一条“完整”链）→ 拒绝
    branch = _evts([
        "PROP-EVT: kind=inj fault_id=1 event_id=0 parent_event_id= tick=1",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 parent_event_id=0 "
        "tick=2",
        "PROP-EVT: kind=mem_req fault_id=1 event_id=2 parent_event_id=1 tick=3",
        # branch B starts at L3; pairwise joining would splice A and B into a
        # spurious full chain, but no single DAG ancestry holds both.
        "PROP-EVT: kind=resp fault_id=1 event_id=3 parent_event_id=0 tick=4",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=4 "
        "parent_event_id=3 tick=5",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=5 parent_event_id=4 "
        "tick=6 outcome=SDC detection_layer=Software contained=0",
    ])
    r = adm(branch, run_id="B1")
    check("跨分支拼接被拒（cross_branch_edge）",
          r["admitted"] is False and "cross_branch_edge"
          in " ".join(r["violations"]), str(r["violations"]))

    # (e) 跨请求拼接（相邻层见证 request_id 不同）→ 拒绝
    xreq = _evts([
        "PROP-EVT: kind=inj fault_id=1 event_id=0 parent_event_id= tick=1",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 parent_event_id=0 "
        "tick=2 request_id=7",
        "PROP-EVT: kind=mem_req fault_id=1 event_id=2 parent_event_id=1 "
        "tick=3 request_id=99",
    ])
    r = adm(xreq, run_id="X1")
    check("跨请求拼接被拒（cross_request_edge）",
          r["admitted"] is False and "cross_request_edge"
          in " ".join(r["violations"]), str(r["violations"]))

    # (f) 时间倒挂拼接（深层层见证 tick 早于浅层）→ 拒绝
    trev = _evts([
        "PROP-EVT: kind=inj fault_id=1 event_id=0 parent_event_id= tick=10",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 parent_event_id=0 "
        "tick=20",
        "PROP-EVT: kind=mem_req fault_id=1 event_id=2 parent_event_id=1 "
        "tick=5",
        "PROP-EVT: kind=resp fault_id=1 event_id=3 parent_event_id=1 tick=5",
    ])
    r = adm(trev, run_id="TR1")
    check("时间倒挂拼接被拒（time_reversed_edge）",
          r["admitted"] is False and "time_reversed_edge"
          in " ".join(r["violations"]), str(r["violations"]))

    # (g) 仅凭 activated / RC=0 / chain_end → 拒绝（三条各自点名）
    crutch = _evts([
        "PROP-EVT: kind=inj fault_id=1 event_id=0 parent_event_id= tick=1",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=1 parent_event_id=0 "
        "tick=2 outcome=run_end detection_layer=None contained=0",
    ])
    r = adm(crutch, run_id="C1", rc=0)
    joined = " ".join(r["violations"])
    check("READY-by-activated-only 被拒",
          r["admitted"] is False and "ready_by_activated_only" in joined,
          joined)
    check("READY-by-RC0 被拒", "ready_by_rc0" in joined, joined)
    check("READY-by-chain_end-only 被拒", "ready_by_chain_end_only" in joined,
          joined)

    # (h) 缺逐层必录指标 → 响亮拒绝（L2 见证缺 event_id）
    missm = _evts([
        "PROP-EVT: kind=inj fault_id=1 event_id=0 parent_event_id= tick=1",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 parent_event_id=0 "
        "tick=2",
        "PROP-EVT: kind=mem_req fault_id=1 parent_event_id=1 tick=3",
        "PROP-EVT: kind=resp fault_id=1 event_id=3 parent_event_id=2 tick=4",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=4 parent_event_id=3 "
        "tick=5",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=5 "
        "parent_event_id=4 tick=6",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=6 parent_event_id=5 "
        "tick=7 outcome=SDC detection_layer=Software contained=0",
    ])
    r = adm(missm, run_id="M1")
    check("缺逐层必录指标被拒（missing_mandatory_metric）",
          r["admitted"] is False and "missing_mandatory_metric"
          in " ".join(r["violations"]), str(r["violations"]))

    # (i) 显式 containment 路径（option 2）→ admitted，后续层 N/A(contained)
    cont = _evts([
        "PROP-EVT: kind=inj fault_id=1 event_id=0 parent_event_id= tick=1",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 parent_event_id=0 "
        "tick=2",
        "PROP-EVT: kind=tlb_fault fault_id=1 event_id=2 parent_event_id=1 "
        "tick=3 detection_layer=Hardware contained=1 "
        "outcome=GenericPageTableFault",
    ])
    r = adm(cont, run_id="CT1", containment={
        "layer": "L2", "reason": "翻译阶段 Hardware 检测并含住",
        "metrics": {"L2": {"faults": 1}}, "na_layers": ["L3", "L4", "L5"]})
    check("containment 路径 admitted=True", r["admitted"] is True,
          str(r["violations"]))
    check("containment path=contained", r["path"] == "contained",
          str(r.get("path")))

    # (j) containment 但后续层未全 N/A(contained) → 拒绝
    r = adm(cont, run_id="CT2", containment={
        "layer": "L2", "reason": "翻译阶段 Hardware 检测并含住",
        "metrics": {"L2": {"faults": 1}}, "na_layers": ["L3"]})
    check("containment 后续层未全 N/A 被拒（contained_without_later_na）",
          r["admitted"] is False and "contained_without_later_na"
          in " ".join(r["violations"]), str(r["violations"]))

    print()
    print("[13] D1/D5：L5 证据必须是真实检测事件（chain_end 生命周期标记绝不充当 L5）")
    # [R6-GATE-D1] 规格：L5（检测/结局）只能由**真实检测事件**证明——非生命周期
    # kind 且同时携带 detection_layer + outcome + 链关联 corr（在故障祖先上）。
    # chain_end 是退出回调的生命周期标记（corr=none），结构性不能占任何层级，
    # 故 ready_by_chain_end_only 由构造堵死（不再是"仅文案"）。
    t04_lifecycle = _evts([
        "PROP-EVT: kind=inj fault_id=1 event_id=0 parent_event_id= tick=1",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 parent_event_id=0 tick=2",
        "PROP-EVT: kind=mem_req fault_id=1 event_id=2 parent_event_id=1 tick=3",
        "PROP-EVT: kind=resp fault_id=1 event_id=3 parent_event_id=2 tick=4",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=4 parent_event_id=3 tick=5",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=5 parent_event_id=4 "
        "tick=6 corr=taint_prop",
        # 真实 T04/T02 形状：chain_end outcome=errant_commit_seen、dl=None、corr=none
        "PROP-EVT: kind=chain_end fault_id=1 event_id=6 parent_event_id=5 "
        "tick=7 outcome=errant_commit_seen detection_layer=None contained=0 "
        "corr=none",
    ])
    f43 = CC.check_chain(t04_lifecycle)["faults"]["1"]
    check("chain_end 生命周期标记不证明 L4->L5",
          f43["edges"]["L4->L5"] == "missing", str(f43["edges"]))
    check("T04 形状终局非 full（止于 L4 Unknown）",
          f43["terminal"] == "provable_to_L4_then_unknown", f43["terminal"])
    check("T04 形状 beyond=Unknown", f43["beyond"] == "Unknown")
    # 富化检测事件（同一 errant_commit 由 reclass join 补齐检测载荷）才证明 L5
    check("_explicit_l5 拒绝生命周期 chain_end 载荷",
          CC._explicit_l5(P.parse_line(
              "PROP-EVT: kind=chain_end fault_id=1 outcome=SDC "
              "detection_layer=Software contained=0 corr=none")) is False)
    check("_explicit_l5 接受带链关联 corr 的检测载荷",
          CC._explicit_l5(P.parse_line(
              "PROP-EVT: kind=errant_commit fault_id=1 outcome=SDC "
              "detection_layer=Software contained=0 corr=taint_prop")) is True)
    miss_corr = P.parse_line(
        "PROP-EVT: kind=errant_commit fault_id=1 outcome=SDC "
        "detection_layer=Software contained=0 corr=none")
    check("_explicit_l5 要求链关联 corr（corr=none 不算）",
          CC._explicit_l5(miss_corr) is False)

    # 真实流回归（D5）：T04 真样本绝不判 full / 绝不 admitted
    t04 = Path(os.environ.get(
        "LSU_R6_T04_EVT",
        "/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_pilot2/T04-F0-W4/seed1/"
        "prop_evt.txt.gz"))
    if t04.is_file():
        ev04, _t = P.read_events(t04)
        v04 = CC.check_chain(ev04)["faults"]["1"]
        check("真实 T04 终局非 full", v04["terminal"] != "full",
              v04["terminal"])
        check("真实 T04 止于 L4（provable_to=L4）",
              v04["provable_to"] == "L4", str(v04["provable_to"]))
        a04 = CC.check_admission({"run_id": "T04-F0-W4", "activated": 1,
                                  "events": ev04, "rc": 0})
        check("真实 T04 不得 admitted（D5）", a04["admitted"] is False,
              str(a04["violations"]))
    else:
        print("  SKIP 真实 T04 流不在（合成例已覆盖）")

    print("[14] D3：跨请求拼接必须在**整条所选祖先**上被抓（不只层代表）")
    # 真实 T04：相邻 resp 对 id=47(req=304) → id=48(req=310) 直接父子同挂
    # 一个 fault_id，却落在同一层（L3）而只保留一个代表 —— 旧口径漏判。
    if t04.is_file():
        ev14, _t = P.read_events(t04)
        r14 = CC.check_admission({"run_id": "T04-F0-W4", "activated": 1,
                                  "events": ev14, "rc": 0})
        joined = " ".join(r14["violations"])
        check("真实 T04 相邻跨请求对被抓（cross_request_edge）",
              "cross_request_edge" in joined, joined[:160])
        # 祖先上确有多处相邻 request_id 不一致（不是空报）
        by_id = {e.get("event_id"): e for e in ev14}
        fam = CC._family_of([e for e in ev14 if e.get("fault_id") == "1"])
        ch = [e for e in ev14 if e.get("fault_id") == "1"]
        path14 = CC._best_ordered_path(ch, fam)
        brk = CC._ancestry_request_breaks(ch, fam, path14)
        check("T04 祖先跨请求对计数 >0（真实证据）", len(brk) > 0, str(len(brk)))
        ex = [(a.get("kind"), a.get("request_id"), b.get("kind"),
               b.get("request_id")) for a, b in brk[:2]]
        check("T04 首例形如 resp 304→310（D3 点名证据）",
              any(x[0] == "resp" and x[2] == "resp" and x[1] != x[3]
                  for x in ex), str(ex))
    else:
        print("  SKIP 真实 T04 流不在（合成例已覆盖）")

    print("[15] D4：cache_access 不得冒充非 cache 族的 L1（且 cache 族 L1 必须是 lookup）")
    # 族由 RunID 前缀判定（T=tlb/L=Load Queue/S=Store Queue/C=L1d-Cache/
    # A=AGU/P=prefetch/O=atomic）——非 cache 族的 L1 观察点不是 cache 结构事件。
    lq_fake = _evts([
        "PROP-EVT: kind=inj run_id=L04-F0-W5 fault_id=1 event_id=0 "
        "parent_event_id= tick=1 corr=origin",
        "PROP-EVT: kind=cache_access run_id=L04-F0-W5 fault_id=1 event_id=1 "
        "parent_event_id=0 tick=2 va=1000 pa=2000 corr=origin",
        "PROP-EVT: kind=cache_return run_id=L04-F0-W5 fault_id=1 event_id=2 "
        "parent_event_id=1 tick=3 pa=2000 field=miss corr=origin",
        "PROP-EVT: kind=resp run_id=L04-F0-W5 fault_id=1 event_id=3 "
        "parent_event_id=2 tick=4 dyn_inst_seq=7 corr=seq_primary",
    ])
    r = adm(lq_fake, run_id="L04-F0-W5")
    check("LQ 族 cache_access 冒充 L1 被拒（cache_access_faked_l1）",
          r["admitted"] is False and "cache_access_faked_l1"
          in " ".join(r["violations"]), str(r["violations"]))
    check("LQ 族判定为 family=lq（非 generic）", r["family"] == "lq",
          str(r.get("family")))
    # cache 族 L1 必须是 cache_access（lookup）
    cache_l1_wrong = _evts([
        "PROP-EVT: kind=inj run_id=C01-F0-W6 fault_id=1 event_id=0 "
        "parent_event_id= tick=1 corr=origin",
        "PROP-EVT: kind=lsq_push run_id=C01-F0-W6 fault_id=1 event_id=1 "
        "parent_event_id=0 tick=2 dyn_inst_seq=7 pc=4000 opcode=ldr "
        "lq_idx=1 va=1000 corr=origin",
        "PROP-EVT: kind=cache_return run_id=C01-F0-W6 fault_id=1 event_id=2 "
        "parent_event_id=1 tick=3 pa=2000 field=miss corr=origin",
    ])
    r = adm(cache_l1_wrong, run_id="C01-F0-W6")
    check("cache 族 L1 非 cache_access 被拒（cache_l1_missing）",
          r["admitted"] is False and "cache_l1_missing"
          in " ".join(r["violations"]), str(r["violations"]))
    # 对照组：cache 族以 cache_access 作 L1 → 不触发这两个 guard
    cache_ok = _evts([
        "PROP-EVT: kind=inj run_id=C99-F0-W6 fault_id=1 event_id=0 "
        "parent_event_id= tick=1 corr=origin",
        "PROP-EVT: kind=cache_access run_id=C99-F0-W6 fault_id=1 event_id=1 "
        "parent_event_id=0 tick=2 va=1000 pa=2000 corr=origin",
        "PROP-EVT: kind=cache_return run_id=C99-F0-W6 fault_id=1 event_id=2 "
        "parent_event_id=1 tick=3 pa=2000 field=miss corr=origin",
        "PROP-EVT: kind=resp run_id=C99-F0-W6 fault_id=1 event_id=3 "
        "parent_event_id=2 tick=4 dyn_inst_seq=7 corr=seq_primary",
    ])
    r = adm(cache_ok, run_id="C99-F0-W6")
    joined = " ".join(r["violations"])
    check("cache 族以 cache_access 作 L1 不误报（对照组）",
          "cache_access_faked_l1" not in joined
          and "cache_l1_missing" not in joined, joined[:160])
    check("两个 D4 规则名登记在 GATE_VIOLATIONS",
          {"cache_access_faked_l1", "cache_l1_missing"}
          <= set(CC.GATE_VIOLATIONS))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
