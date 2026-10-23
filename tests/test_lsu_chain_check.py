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
    # [L34 合并] 原集成分支断言「contained 判定只认显式事件（_L5_OUTCOME_KINDS
    # 含 chain_end）」——其口径已被 D1 规格**反演**（chain_end 永不充当 L5）。
    # 该断言不可原样保留（保留即断言一条已被禁止的语义），故此处以**更强**的
    # 形式保留其"只认显式事件、绝不猜测"的意图：旧常量必须已结构性移除，
    # 且链末只有生命周期标记时绝不判 full / detected_contained。
    check("contained 判定只认显式真实检测事件（旧 _L5_OUTCOME_KINDS 口径已废，"
          "chain_end 恒不占 L5）",
          not hasattr(CC, "_L5_OUTCOME_KINDS")
          and CC._explicit_l5(P.parse_line(
              "PROP-EVT: kind=chain_end fault_id=3 outcome=SDC "
              "detection_layer=Software contained=1")) is False)

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
        # [R6-FIXB] 含住准入须以**完整收口**的流为前提（正常退出 ⇒ chain_end）。
        "PROP-EVT: kind=chain_end fault_id=1 event_id=3 parent_event_id=2 "
        "tick=4 outcome=run_end detection_layer=None contained=0 corr=none",
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

    print("[16] D2：containment 束由显式证据推导（含住主张须真成立）")
    cont_ok = _evts([
        "PROP-EVT: kind=inj run_id=T77-F0-W4 fault_id=1 event_id=0 "
        "parent_event_id= tick=1 corr=origin",
        "PROP-EVT: kind=tlb_lookup run_id=T77-F0-W4 fault_id=1 event_id=1 "
        "parent_event_id=0 tick=2 dyn_inst_seq=7 request_id=7 va=1000 "
        "entry_index=1 field=post_lookup state_before=x state_after=y "
        "corr=origin",
        "PROP-EVT: kind=tlb_translate_result run_id=T77-F0-W4 fault_id=1 "
        "event_id=2 parent_event_id=1 tick=3 dyn_inst_seq=7 request_id=7 "
        "va=1000 pa=2000 field=walk_refill_lost detection_layer=L2 "
        "contained=1 outcome=translation_blocked corr=origin",
        # [R6-FIXB] 含住主张须建立在**完整收口**的流上：正常退出的样本由
        # 退出回调发射生命周期 chain_end（abort 样本没有）——故合法含住夹具
        # 必须收口，否则与截断流不可区分（见 [18]）。
        "PROP-EVT: kind=chain_end run_id=T77-F0-W4 fault_id=1 event_id=3 "
        "parent_event_id=2 tick=4 outcome=run_end detection_layer=None "
        "contained=0 corr=none",
    ])
    b = CC.containment_from_events(cont_ok, "T77-F0-W4")
    check("显式含住证据 → 束合法（layer=L2 / na_layers=L3,L4,L5）",
          bool(b) and b["layer"] == "L2"
          and b["na_layers"] == ["L3", "L4", "L5"], str(b))
    r = CC.check_admission({"run_id": "T77-F0-W4", "activated": 1,
                            "events": cont_ok, "rc": 0, "containment": b})
    check("显式含住 → admitted=True", r["admitted"] is True,
          str(r["violations"]))
    # 含住之后仍有更深层见证 ⇒ 传播未止 ⇒ 主张不成立（束为 None）
    cont_deep = _evts([
        "PROP-EVT: kind=inj run_id=T78-F0-W4 fault_id=1 event_id=0 "
        "parent_event_id= tick=1 corr=origin",
        "PROP-EVT: kind=tlb_lookup run_id=T78-F0-W4 fault_id=1 event_id=1 "
        "parent_event_id=0 tick=2 dyn_inst_seq=7 request_id=7 va=1000 "
        "entry_index=1 field=post_lookup state_before=x state_after=y "
        "corr=origin",
        "PROP-EVT: kind=tlb_translate_result run_id=T78-F0-W4 fault_id=1 "
        "event_id=2 parent_event_id=1 tick=3 dyn_inst_seq=7 request_id=7 "
        "va=1000 pa=2000 field=walk_refill_lost detection_layer=L2 "
        "contained=1 outcome=translation_blocked corr=origin",
        # 更深的见证（L3 交付）⇒ 故障并未止于 L2
        "PROP-EVT: kind=resp run_id=T78-F0-W4 fault_id=1 event_id=3 "
        "parent_event_id=2 tick=4 dyn_inst_seq=7 request_id=7 "
        "corr=seq_primary",
    ])
    check("含住层之后仍有见证 → 主张不成立（束=None）",
          CC.containment_from_events(cont_deep, "T78-F0-W4") is None)
    check("无证据 → containment_from_events 返回 None（不猜测）",
          CC.containment_from_events(
              _evts(["PROP-EVT: kind=inj fault_id=1 event_id=0 tick=1"]),
              "N1") is None)

    print()
    print("[17] R6-FIXB：chain_end 生命周期标记不得充当 L5 / 不得制造 containment")
    # [R6-FIXB] 净新语义收口：**两处**曾把生命周期链条目 chain_end 当成真实 L5——
    #   (i)  containment_from_events 只查 detection_layer+outcome+contained，
    #        chain_end（退出回调，corr=none）于是被采信为含住见证；
    #   (ii) _terminal 的 "explicit contained" 扫描读**原始** contained，
    #        吃掉 chain_end 自带的 contained=1，把已有真实检测事件的链
    #        从 full 拉低成 detected_contained。
    # chain_end 是**生命周期标记**（C++ CHAOSPropagation.cc 退出回调；
    # corr=none 无关联语义），其存在与否只表示"流是否正常收口"，
    # 绝不表示检测/含住。
    # (a) chain_end-only（富化载荷 contained=1 + detection_layer=L5），链上无
    #     任何真实检测事件 → 不得 full、不得判含住、不得准入。
    c17a = _evts([
        "PROP-EVT: kind=inj run_id=X00-F0-W0 fault_id=1 event_id=0 tick=1",
        "PROP-EVT: kind=addr_form run_id=X00-F0-W0 fault_id=1 event_id=1 tick=2",
        "PROP-EVT: kind=mem_req run_id=X00-F0-W0 fault_id=1 event_id=2 tick=3",
        "PROP-EVT: kind=resp run_id=X00-F0-W0 fault_id=1 event_id=3 tick=4",
        "PROP-EVT: kind=taint_reg run_id=X00-F0-W0 fault_id=1 event_id=4 tick=5",
        "PROP-EVT: kind=errant_commit run_id=X00-F0-W0 fault_id=1 event_id=5 "
        "tick=6",
        # 真实 T04/T02 形状：chain_end 带 dl=L5 + contained=1 + outcome
        "PROP-EVT: kind=chain_end run_id=X00-F0-W0 fault_id=1 event_id=6 "
        "tick=7 detection_layer=L5 contained=1 outcome=errant_commit_seen "
        "corr=none",
    ])
    f17a = CC.check_chain(c17a)["faults"]["1"]
    check("chain_end 富化载荷不占 L5（L4->L5 missing）",
          f17a["edges"]["L4->L5"] == "missing", str(f17a["edges"]))
    check("chain_end-only 不得 full", f17a["terminal"] != "full",
          f17a["terminal"])
    check("chain_end-only 诚实止于 L4（provable_to_L4_then_unknown）",
          f17a["terminal"] == "provable_to_L4_then_unknown", f17a["terminal"])
    b17a = CC.containment_from_events(c17a, "X00-F0-W0")
    check("chain_end 不得制造含住束（束=None）", b17a is None, str(b17a))
    r17a = adm(c17a, run_id="X00-F0-W0", containment=b17a)
    check("chain_end-only 不准入", r17a["admitted"] is False,
          str(r17a["violations"]))

    # (b) 真实检测事件（富化 errant_commit）+ chain_end 自带 contained=1：
    #     P6 决定性形状 —— 结论必须由真实检测事件给出（full），
    #     chain_end 不得把它拉低成 detected_contained。
    c17b = _evts([
        "PROP-EVT: kind=inj run_id=X01-F0-W0 fault_id=1 event_id=0 tick=1",
        "PROP-EVT: kind=addr_form run_id=X01-F0-W0 fault_id=1 event_id=1 tick=2",
        "PROP-EVT: kind=mem_req run_id=X01-F0-W0 fault_id=1 event_id=2 tick=3",
        "PROP-EVT: kind=resp run_id=X01-F0-W0 fault_id=1 event_id=3 tick=4",
        "PROP-EVT: kind=taint_reg run_id=X01-F0-W0 fault_id=1 event_id=4 tick=5",
        "PROP-EVT: kind=errant_commit run_id=X01-F0-W0 fault_id=1 event_id=5 "
        "tick=6 detection_layer=L5 outcome=errant_commit contained=0 "
        "corr=taint_prop",
        "PROP-EVT: kind=chain_end run_id=X01-F0-W0 fault_id=1 event_id=6 "
        "tick=7 detection_layer=L5 contained=1 outcome=errant_commit_seen "
        "corr=none",
    ])
    f17b = CC.check_chain(c17b)["faults"]["1"]
    check("真实检测事件 + chain_end 自带 contained=1 ⇒ 仍判 full（不被拉低）",
          f17b["terminal"] == "full", f17b["terminal"])
    check("含住束不得由 chain_end 制造（真实事件 contained=0）",
          CC.containment_from_events(c17b, "X01-F0-W0") is None)
    r17b = adm(c17b, run_id="X01-F0-W0",
               containment=CC.containment_from_events(c17b, "X01-F0-W0"))
    check("真实检测事件驱动的 full 仍准入（不过度收紧，对照组）",
          r17b["admitted"] is True, str(r17b["violations"]))
    check("full 链 path=full_chain", r17b["path"] == "full_chain",
          str(r17b.get("path")))

    # (c) P6 真流决定性证据（Lane B 归因引用）：删/不删 chain_end 结论必须相同。
    p6 = Path(os.environ.get(
        "LSU_R6_P6_EVT",
        "/home/sdc/gem5-fi-ding/runs/lsu/r6_p1_T01-F0-W4/T01-F0-W4/seed2/"
        "prop_evt.txt.gz"))
    if p6.is_file():
        ev6, _t6 = P.read_events(p6)
        t6_with = CC.check_chain(ev6)["faults"]["1"]["terminal"]
        t6_without = CC.check_chain(
            [e for e in ev6 if e.get("kind") != "chain_end"]
        )["faults"]["1"]["terminal"]
        print(f"  INFO P6 带 chain_end={t6_with} / 删除后={t6_without}")
        check("P6：chain_end 的存在不改变结论（不被拉低）",
              t6_with == t6_without, f"{t6_with} vs {t6_without}")
        check("P6：真实 errant_commit 检测事件驱动的终局为 full",
              t6_with == "full", t6_with)
        check("P6：chain_end 不得制造含住束",
              CC.containment_from_events(ev6, "T01-F0-W4") is None)
    else:
        print("  SKIP P6 真流不在（合成例已覆盖）")

    print("[18] R6-FIXB：截断 / 未收口流不得因 containment 被准入（缺陷 #5）")
    t08p = Path(os.environ.get(
        "LSU_R6_T08_EVT",
        "/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_C_T08-F0-W4/T08-F0-W4/seed1/"
        "prop_evt.txt.gz"))
    if t08p.is_file():
        ev08, tr08 = P.read_events(t08p)
        check("T08 真流确为截断（gzip EOF，truncated=True）", tr08 is True)
        check("截断流不得推出含住束（束=None）",
              CC.containment_from_events(ev08, "T08-F0-W4") is None)
        r08 = adm(ev08, run_id="T08-F0-W4",
                  containment=CC.containment_from_events(ev08, "T08-F0-W4"))
        j08 = " ".join(r08["violations"])
        check("截断流不得因 containment 被准入", r08["admitted"] is False, j08)
        check("截断流不准入须响亮给因（点名未收口/截断）",
              "containment_on_unclosed_stream" in j08, j08[:200])
    else:
        print("  SKIP 真实 T08 流不在（合成例已覆盖）")
    check("R6-FIXB 规则名登记在 GATE_VIOLATIONS",
          {"containment_on_unclosed_stream", "containment_on_truncated_stream"}
          <= set(CC.GATE_VIOLATIONS), str(CC.GATE_VIOLATIONS))

    # 显式截断信号（bundle）——调用方已判定截断时，一律不得含住准入。
    closed_like = _evts([
        "PROP-EVT: kind=inj run_id=T77-F0-W4 fault_id=1 event_id=0 tick=1",
        "PROP-EVT: kind=tlb_lookup run_id=T77-F0-W4 fault_id=1 event_id=1 "
        "tick=2 dyn_inst_seq=7 request_id=7 va=1000 entry_index=1 "
        "field=post_lookup state_before=x state_after=y",
        "PROP-EVT: kind=tlb_translate_result run_id=T77-F0-W4 fault_id=1 "
        "event_id=2 tick=3 dyn_inst_seq=7 request_id=7 va=1000 pa=2000 "
        "field=walk_refill_lost detection_layer=L2 contained=1 "
        "outcome=translation_blocked corr=origin",
        "PROP-EVT: kind=chain_end run_id=T77-F0-W4 fault_id=1 event_id=3 "
        "tick=4 outcome=run_end detection_layer=None contained=0 corr=none",
    ])
    b_ok = CC.containment_from_events(closed_like, "T77-F0-W4")
    check("已收口的合法含住证据 → 束合法（layer=L2 / na=L3,L4,L5）",
          bool(b_ok) and b_ok["layer"] == "L2"
          and b_ok["na_layers"] == ["L3", "L4", "L5"], str(b_ok))
    r_ok = adm(closed_like, run_id="T77-F0-W4", containment=b_ok)
    check("已收口的合法含住 → 仍 admitted=True（反证不过度收紧）",
          r_ok["admitted"] is True, str(r_ok["violations"]))
    r_tr = adm(closed_like, run_id="T77-F0-W4", containment=b_ok,
               truncated=True)
    check("同一证据但显式 truncated=True ⇒ 拒绝含住准入",
          r_tr["admitted"] is False, str(r_tr["violations"]))
    check("显式截断响亮点名 containment_on_truncated_stream",
          "containment_on_truncated_stream" in " ".join(r_tr["violations"]),
          str(r_tr["violations"]))
    check("显式 truncated 亦不得推出含住束",
          CC.containment_from_events(closed_like, "T77-F0-W4",
                                     truncated=True) is None)
    # 未收口（无 chain_end）→ 含住主张不可证（同一含住检测事件）
    unclosed = [e for e in closed_like if e.get("kind") != "chain_end"]
    b_un = CC.containment_from_events(unclosed, "T77-F0-W4")
    check("未收口（缺 chain_end）→ 含住束=None（含住是对缺席的断言）",
          b_un is None, str(b_un))
    r_un = adm(unclosed, run_id="T77-F0-W4", containment=b_un)
    check("未收口 ⇒ 不准入 + 响亮点名 containment_on_unclosed_stream",
          r_un["admitted"] is False
          and "containment_on_unclosed_stream" in " ".join(r_un["violations"]),
          str(r_un["violations"]))

    print()
    print("[19] [R6-ABREC] 合法 lineage bridge 不得绕过 B 的终局门禁"
          "（bridge 白名单 ≠ 放宽 L5/收口）")
    # 本 lane 收口 A2 的 bridge 白名单与 B 的终局语义：bridge 只豁免
    # cross_request_edge（跨请求身份），**绝不**制造 L5、绝不豁免截断/未收口
    # 的含住准入。下面用**完整可核验 bridge**（与 A2 test [6] 同形）证明：
    # 合法 bridge 在场时，(a) chain_end 伪 L5 仍被判非 full 且不准入；
    # (b) 截断流仍被响亮拒绝——且两例都**不是**因 cross_request_edge。
    RUN19 = "T04-F0-W4"

    def _L19(kind, **kw):
        parts = [f"kind={kind}", f"run_id={RUN19}"]
        parts += [f"{k}={v}" for k, v in kw.items()]
        return P.parse_line("PROP-EVT: " + " ".join(parts))

    owner19 = [
        _L19("inj", fault_id=1, event_id=0, tick=10, request_id=301,
             va="ffffffc009483fa8", corr="origin"),
        _L19("tlb_lookup", fault_id=1, event_id=1, parent_event_id=0, tick=11,
             request_id=301, corr="seq_primary", dyn_inst_seq=301,
             field="post_lookup", state_before="valid", state_after="valid"),
        _L19("tlb_pfn", fault_id=1, event_id=2, parent_event_id=1, tick=12,
             request_id=301, corr="seq_primary", va="ffffffc009483fa8",
             before="81d75", after="0", pa="fa8"),
        _L19("tlb_translate_result", fault_id=1, event_id=3, parent_event_id=2,
             tick=13, request_id=301, corr="seq_primary", outcome="NoFault",
             contained="0"),
        _L19("lsq_push", fault_id=1, event_id=4, parent_event_id=3, tick=14,
             corr="seq_primary"),
        _L19("cache_access", fault_id=1, event_id=5, parent_event_id=4,
             tick=15, request_id=301, corr="addr_fallback", pa="fa8",
             va="ffffffc009483fa8"),
        _L19("mshr_alloc", fault_id=1, event_id=6, parent_event_id=5, tick=16,
             request_id=301, corr="addr_fallback", cache_line="fa8"),
    ]
    bridge19 = _L19(
        "request_fork", fault_id=1, event_id=7, parent_event_id=6, tick=17,
        request_id=301, corr="addr_fallback", old_request_id=301,
        new_request_id=303, source_event_id=6, dest_event_id=8,
        bridge_layer="L3", bridge_reason="addr_fallback_broadcast",
        shared_addr="0", shared_size="1000")
    branch19 = [
        _L19("cache_access", fault_id=1, event_id=8, parent_event_id=7,
             tick=18, request_id=303, corr="addr_fallback", pa="fe0",
             va="ffffffc009483fe0"),
        _L19("resp", fault_id=1, event_id=9, parent_event_id=8, tick=19,
             request_id=303, corr="addr_fallback", pa="fe0",
             va="ffffffc009483fe0"),
        _L19("taint_reg", fault_id=1, event_id=10, parent_event_id=9, tick=20,
             request_id=303, corr="addr_fallback"),
    ]
    # 对照组：真实检测事件（errant_commit 富化 L5）—— 合法 bridge 应 admitted。
    real_l5 = _L19("errant_commit", fault_id=1, event_id=11,
                   parent_event_id=10, tick=21, request_id=303,
                   corr="addr_fallback", detection_layer="L5", contained="0",
                   outcome="errant_commit")
    end19 = _L19("chain_end", fault_id=1, event_id=12, parent_event_id=11,
                 tick=22, corr="none", detection_layer="L5", contained="1",
                 outcome="errant_commit_seen")
    r_ctrl = adm(owner19 + [bridge19] + branch19 + [real_l5, end19],
                 run_id=RUN19)
    j_ctrl = " ".join(r_ctrl["violations"])
    check("(19 对照) 合法 bridge + 真实 L5 事件 ⇒ admitted=True",
          r_ctrl["admitted"] is True, j_ctrl)
    check("(19 对照) 合法 bridge 本身不触发 invalid_lineage_bridge/"
          "cross_request_edge",
          "invalid_lineage_bridge" not in j_ctrl
          and "cross_request_edge" not in j_ctrl, j_ctrl)

    # (a) bridge 合法，但把真实 L5 换成 chain_end 伪 L5（无真实检测事件）。
    pseudo_end = _L19("chain_end", fault_id=1, event_id=11,
                      parent_event_id=10, tick=21, corr="none",
                      detection_layer="L5", contained="1",
                      outcome="errant_commit_seen")
    r_a = adm(owner19 + [bridge19] + branch19 + [pseudo_end], run_id=RUN19)
    j_a = " ".join(r_a["violations"])
    f_a = CC.check_chain(owner19 + [bridge19] + branch19 + [pseudo_end])
    check("(19a) 合法 bridge + chain_end 伪 L5 ⇒ 不得 full",
          f_a["faults"]["1"]["terminal"] != "full",
          f_a["faults"]["1"]["terminal"])
    check("(19a) 合法 bridge + chain_end 伪 L5 ⇒ 不准入",
          r_a["admitted"] is False, j_a)
    check("(19a) 该拒绝**不是**因 cross_request_edge（bridge 有效）",
          "cross_request_edge" not in j_a
          and "invalid_lineage_bridge" not in j_a, j_a)

    # (b) bridge 合法，但流被显式标记截断 + 含住主张 ⇒ 仍不得准入。
    cont_l2 = _L19("tlb_translate_result", fault_id=1, event_id=3,
                   parent_event_id=2, tick=13, request_id=301,
                   corr="seq_primary", outcome="translation_blocked",
                   detection_layer="L2", contained="1")
    # 用 owner19 前缀（把事件 3 换成显式含住检测）+ bridge + B 分支，合成
    # 一条止于 L2 含住、后续经 bridge 跨请求的流；调用方显式 truncated=True。
    chain_b = ([e for e in owner19 if e["event_id"] != "3"] + [cont_l2,
               bridge19] + branch19)
    r_b = adm(chain_b, run_id=RUN19, truncated=True, containment={
        "layer": "L2", "reason": "翻译阶段 Hardware 检测并含住",
        "metrics": {"L2": {"faults": 1}}, "na_layers": ["L3", "L4", "L5"]})
    j_b = " ".join(r_b["violations"])
    check("(19b) 合法 bridge + 显式截断 ⇒ 不准入",
          r_b["admitted"] is False, j_b)
    check("(19b) 合法 bridge + 显式截断 ⇒ 响亮 containment_on_truncated_stream",
          "containment_on_truncated_stream" in j_b, j_b)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
