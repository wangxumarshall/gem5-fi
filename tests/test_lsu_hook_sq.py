#!/usr/bin/env python3
"""test_lsu_hook_sq.py — [MDSPEC][H3] SQ 生命周期钩子契约测试。

规格（表 9 缺失钩子列，63 RunID）：
"src/cpu/o3/lsq_unit.cc insertStore/executeStore/checkViolations/
writebackStores/commit-drain — SQ 逐事件 + state_before/after"

契约：
- kind=sq_execute（L3）: executeStore 入口——fault_id/dyn_inst_seq/sq_idx/
  va/state_before（=issued）
- kind=sq_complete（L3）: completeStore（store 排放完成，SQ entry 释放）
  ——fault_id/dyn_inst_seq/sq_idx/va/state_after（=completed）
- 关联：correlateRequestBySeq（dyn-seq）；va 取注册表 base
- insertStore 在 dispatch 期早于注入注册（结构性缺席，同 H7 lq_insert
  裁决）；checkViolations 路径由 CHAOSLSQFwd 既有 violationCorrupt 承载。

用法：python3 tests/test_lsu_hook_sq.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P  # noqa: E402

FAILED = []


def src(path):
    return (ROOT / path).read_text(encoding="utf-8")


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def main():
    print("[1] H3 kind→层级与必录字段注册")
    check("sq_execute -> L3", P.KIND_LAYER.get("sq_execute") == "L3",
          str(P.KIND_LAYER.get("sq_execute")))
    check("sq_complete -> L3", P.KIND_LAYER.get("sq_complete") == "L3",
          str(P.KIND_LAYER.get("sq_complete")))
    req_e = P.REQUIRED_FIELDS.get("sq_execute")
    req_c = P.REQUIRED_FIELDS.get("sq_complete")
    check("sq_execute required fields",
          req_e is not None
          and all(f in req_e for f in ("fault_id", "dyn_inst_seq", "sq_idx",
                                       "va", "state_before")))
    check("sq_complete required fields",
          req_c is not None
          and all(f in req_c for f in ("fault_id", "dyn_inst_seq", "sq_idx",
                                       "va", "state_after")))

    print("[2] 契约行校验")
    good_e = P.parse_line(
        "PROP-EVT: kind=sq_execute fault_id=1 dyn_inst_seq=133 sq_idx=22 "
        "va=7fbff state_before=issued corr=seq_primary")
    check("complete sq_execute validates",
          good_e is not None and P.validate_event(good_e) == [])
    good_c = P.parse_line(
        "PROP-EVT: kind=sq_complete fault_id=1 dyn_inst_seq=133 sq_idx=22 "
        "va=7fbff state_after=completed corr=seq_primary")
    check("complete sq_complete validates",
          good_c is not None and P.validate_event(good_c) == [])
    bad = P.parse_line("PROP-EVT: kind=sq_execute fault_id=1 dyn_inst_seq=1")
    errs = P.validate_event(bad)
    check("missing sq_idx/va/state_before/corr flagged", len(errs) == 4,
          str(errs))

    print("[3] store 链推进（a04 全链含 sq 对）")
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=10",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 tick=10",
        "PROP-EVT: kind=lsq_push fault_id=1 event_id=2 tick=11 "
        "dyn_inst_seq=133",
        "PROP-EVT: kind=lsq_sendfrag fault_id=1 event_id=3 tick=12 "
        "dyn_inst_seq=133",
        "PROP-EVT: kind=sq_execute fault_id=1 event_id=4 tick=15 "
        "dyn_inst_seq=133 sq_idx=22 va=7fbff state_before=issued",
        "PROP-EVT: kind=sq_complete fault_id=1 event_id=5 tick=30 "
        "dyn_inst_seq=133 sq_idx=22 va=7fbff state_after=completed",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=6 tick=40",
    ]]
    import lsu_chain_check as CC  # noqa: E402（tools/ 已在 sys.path）
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("store 链 L0→L4 全边 proven → full（含 sq_execute/complete）",
          f1["terminal"] == "full",
          f"{f1['terminal']} edges={ {k: v2 for k, v2 in f1['edges'].items() if not k.endswith('_witness')} }")

    print("[4] A7 store 链抵达 L4/L5（store 无 wb_to_reg，旧路径止于 L3）")
    # 真实证据 runs/lsu/r6_sq_S04-F0-W5：11 事件、无 taint_reg/consumer/
    # errant_commit，verdict=provable_to_L3_then_unknown。store 的架构物化
    # 就是它的 commit（错误内存副作用），故 store 链必须也能到 L4/L5。
    store_chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=10 dyn_inst_seq=4001",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 tick=10 "
        "dyn_inst_seq=4001",
        "PROP-EVT: kind=lsq_push fault_id=1 event_id=2 tick=11 "
        "dyn_inst_seq=4001 sq_idx=338 va=490250",
        "PROP-EVT: kind=lsq_sendfrag fault_id=1 event_id=3 tick=12 "
        "dyn_inst_seq=4001 request_id=4001 va=490250",
        "PROP-EVT: kind=sq_execute fault_id=1 event_id=4 tick=15 "
        "dyn_inst_seq=4001 sq_idx=338 va=490250 state_before=issued",
        "PROP-EVT: kind=sq_complete fault_id=1 event_id=5 tick=30 "
        "dyn_inst_seq=4001 sq_idx=338 va=490250 state_after=completed",
        # A7 新增的两条 store L4/L5 事件：
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=6 tick=31 "
        "dyn_inst_seq=4001 corr=seq_primary field=store_data",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=7 tick=40 "
        "dyn_inst_seq=4001 detection_layer=L5 contained=0 "
        "outcome=errant_commit corr=taint_prop",
        # 逃逸链：无 containment，contained=0（否则 checker 按 L5 显式
        # contained 判 detected_contained 而非 full）。
        "PROP-EVT: kind=chain_end fault_id=1 event_id=8 tick=99 "
        "fault_id=1 detection_layer=L5 contained=0 "
        "outcome=errant_commit_seen corr=none",
    ]]
    sv = CC.check_chain(store_chain)
    sf = sv["faults"]["1"]
    check("store 链 L3→L4 proven（sq_complete → taint_reg）",
          sf["edges"]["L3->L4"] == "proven", str(sf["edges"].get("L3->L4")))
    check("store 链 L4→L5 proven（errant_commit → chain_end）",
          sf["edges"]["L4->L5"] == "proven", str(sf["edges"].get("L4->L5")))
    check("store 链 terminal=full（不再止于 L3）", sf["terminal"] == "full",
          sf["terminal"])

    # 源码契约：store 响应污染 + 提交即错误路径（A7）
    prop_cc = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.cc")
    prop_hh = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.hh")
    check("noteMemResponse 对 store 响应发 taint_reg（!wb_to_reg && isStore）",
          "!wb_to_reg && inst->isStore()" in prop_cc)
    check("store 污染按 dyn seq 记入 store_taint（新成员）",
          "store_taint[" in prop_cc and "store_taint;" in prop_hh)
    check("noteCommit 认 store 自污染 → errant_commit",
          "self_store_taint" in prop_cc
          and "faulting_store_commit" in prop_cc)
    check("errant_commit 绑定链（errant_ptags）不受 store 路径破坏",
          "errant_ptags.insert(ptag);" in prop_cc)
    # 未 retirement 的故障 store（响应后遭 squash/replay 丢弃）在退出回调记
    # containment，链闭合为 detected_contained（S04-F0-W5 实测：注入 store
    # sn:4001 从不提交、同 PC 重放实例提交，oracle 干净）。
    check("退出回调把未退休的故障 store 记为 containment",
          "store_discarded_not_retired" in prop_cc
          and "containment_ptags[p] = {\"L4\"," in prop_cc)

    print("[5] A9 lq_read 携带 request_id（L2→L3 请求连续性）")
    lu = src("CHAOS/gem5/src/cpu/o3/lsq_unit.cc")
    lq_read = lu[lu.index("// [MDSPEC][H7] unified lq_read event"):]
    lq_read = lq_read[:lq_read.index('notePropEvt("lq_read"')
                      + lq_read[lq_read.index('notePropEvt("lq_read"'):]
                                .index("});")]
    check("lq_read 写 request_id",
          '{"request_id"' in lq_read, lq_read[-200:])
    check("lq_read request_id 来自 Request 盖戳 seq（或 load seq 兜底）",
          "getReqInstSeqNum" in lq_read, lq_read[-200:])

    print("[6] oracle crash/abort 字段契约（L18 §需要发射器车道的字段契约）")
    # (1) 崩溃/abort 路径须写出 detection_layer/contained/outcome，且 L5 结局
    #     join 需要 fault_id/commit_seq/pc/dyn_inst_seq。
    ce = prop_cc[prop_cc.index('notePropEvt("chain_end"'):]
    ce = ce[:ce.index("});")]
    for f in ("fault_id", "commit_seq", "pc", "dyn_inst_seq",
              "detection_layer", "contained", "outcome"):
        check(f"chain_end 写 {f}", f'{{"{f}"' in ce, ce[:160])
    # (2) 检测事件 errant_commit 自带 contained（逃逸=0）。
    check("errant_commit 写 contained=0（逃逸语义）",
          '";contained=0"' in prop_cc)
    # (3) 硬件检测器 stdout 信号行（G7 唯一输入）。
    check("发射 CHAOS_DETECT stdout 信号行",
          "CHAOS_DETECT: layer=" in prop_cc
          and "ptag=" in prop_cc and "reason=" in prop_cc)
    check("CHAOS_DETECT 在检测/containment 路径都发射",
          "emitDetectSignal" in prop_cc
          and prop_hh.count("emitDetectSignal") >= 1)
    # 量刑：4 值层词汇表（Hardware RAS / OS / Application / None）
    check("CHAOS_DETECT layer 用四值词汇表（Hardware RAS / None 用例）",
          '"Hardware RAS"' in prop_cc and '"None"' in prop_cc)

    print("[7] [R6-FIXA] 发射器父边按请求域（不是单一 ptag 游标）")
    # 根因：emitPropEvt 原先以 `ptag_last_event[ptag]` 单游标作 parent_event_id，
    # 使 addr_fallback 广播直接产生跨请求父子边（T04-F0-W4 实测 59 处断裂）。
    # 修复后父边按 (fault, request) 取：事件挂到**自身请求**的上一事件；未盖戳
    # 生命周期事件归属链的 owner 请求。检查器门禁未放宽（见
    # test_lsu_campaign_propagation.py §6）。
    check("emitPropEvt 用请求域游标 ptag_branch_last",
          "ptag_branch_last" in prop_cc, prop_cc[:80])
    check("记录 owner 请求 ptag_owner_request",
          "ptag_owner_request" in prop_cc)
    check("hh 声明请求域游标成员",
          "ptag_owner_request" in prop_hh and "ptag_branch_last" in prop_hh)
    # 旧的单一 ptag 游标不得再作为 parent 来源（只允许留在退出回调枚举链）。
    _s = prop_cc.index("CHAOSPropagation::emitPropEvt(")
    _e = prop_cc.index("CHAOSPropagation::notePropEvt(", _s)
    emit = prop_cc[_s:_e]
    check("emitPropEvt 不再用 ptag_last_event 作 parent",
          "ptag_last_event.find" not in emit
          and "{ptag, branch_key}" in emit,
          "ptag_last_event.find" in emit)

    print("[8] [R6-FIXA2] 显式 lineage bridge（request_fork）发射契约")
    # 用户裁决：兄弟子链「无父生根、不进祖先路径」不可接受。新请求首事件必须
    # 经显式 bridge 接到**真实污染来源事件**；无来源/无共享对象则不造桥。
    check("hh 声明 bridge 契约（id 空间 + 发射器）",
          "BRIDGE_ID_BASE" in prop_hh and "emitLineageBridge" in prop_hh
          and "ptag_bridge_event" in prop_hh)
    check("hh 声明 bridge 家族字段（old/new request + source/dest + 共享对象）",
          all(k in prop_hh for k in
              ("old_request_id", "new_request_id", "source_event_id",
               "dest_event_id", "bridge_layer", "shared_addr", "shared_size")))
    check("emitPropEvt 发射 bridge 并让目标事件挂到 bridge 下",
          "emitLineageBridge(kind, ptag, branch_key," in prop_cc
          and 'fields["parent_event_id"] = std::to_string(bridge_id)' in prop_cc)
    # 不得无源造桥：来源事件 / 共享对象二者缺一即返回 0（不建边）。
    elb = prop_cc[prop_cc.index("CHAOSPropagation::emitLineageBridge("):]
    elb = elb[:elb.index("prefetch request id")]
    check("无真实来源事件 → 不造桥",
          "no source -> no bridge" in elb, elb[-160:])
    check("无共享污染对象 → 不造桥",
          "no verifiable object -> no bridge" in elb, elb[-160:])
    check("bridge 记录来源事件父边 + 目标首事件 + 稳定 corr identity",
          'b["parent_event_id"] = std::to_string(sit->second)' in elb
          and 'b["dest_event_id"] = std::to_string(dest_event_id)' in elb
          and 'b["bridge_layer"]' in elb and 'b["bridge_reason"]' in elb)
    check("bridge 记录被共享的坏对象区间（可核验）",
          'b["shared_addr"]' in elb and 'b["shared_size"]' in elb
          and "blk_registry" in elb)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
