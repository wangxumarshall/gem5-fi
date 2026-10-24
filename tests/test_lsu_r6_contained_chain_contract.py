#!/usr/bin/env python3
"""test_lsu_r6_contained_chain_contract.py — [MDSPEC][R6-DIAG] 含住链的
发射契约（T01-F0-W4 / time_reversed_edge 根因的契约钉子）。

实测根因（Lane DIAG-EMIT，只读诊断，证据见 runs/lsu/r6_p1_T01-F0-W4/
T01-F0-W4/seed1/prop_evt.txt.gz）：
  * 注入把 TLB 表项 pfn 的高位 bit（bit 56）翻转 → `pfn<<12` 在 64 位 Addr
    里回绕，**有效 PA 未变**（0x81d75fa8 == 0x81d75fa8）→ 注入点自身即判
    `pa_changed=0`（CHAOSArmTLB.cc:926-929 注释与 registerTlbFault 实现）。
  * 但 `registerTlbFault` 的 **seq-primary 归属臂**对 `req_seq != 0` **无条件**
    注册（CHAOSPropagation.cc:1410-1419），于是同一条 store 请求（dyn_seq
    相同）的后续**普通干净事件**（sq_execute→resp→taint_reg）仍按 seq 并
    入本故障链 —— 该流同时断言"L2 已含住（effective_pa_unchanged）"与
    "已传播到 L4"。
  * checker 把携带 detection_layer/outcome/corr 的 L2 检测事件提升为 L5
    （`_layer_of` → `_explicit_l5`），再要求 tick(L5 见证) ≥ tick(L4 见证)：
    237950940537 < 237950942203 ⇒ `time_reversed_edge`；同时
    `containment_from_events` 因"更深层仍有见证"返回 None ⇒ 不准入。

本测试钉死两条契约（不依赖 gem5，纯离线）：
  (A) **现状形状**（含住 + 后续仍有本链见证）必须被**响亮拒绝**——
      checker 保持严格（用户裁决 D：不得放宽该拒绝）；发射器**不得**
      产出这种自相矛盾的流。
  (B) **修复目标形状**（含住的翻译在 L2 收口 ⇒ 该请求后续事件不再并入本
      链）必须在同一严格 checker 下**准入**（option-2：containment.layer=L2，
      后续层 L3/L4/L5 全 N/A），且物理顺序真实（parent.tick ≤ child.tick，
      同 tick 允许）。

用法：python3 tests/test_lsu_r6_contained_chain_contract.py（rc=0 全 PASS）
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


# --------------------------------------------------------------- real stream
# 逐字取自 T01-F0-W4 seed1 的真实事件（tick/字段原样，未改写）。
_L2_DETECT = (
    "PROP-EVT: kind=tlb_translate_result fault_id=1 event_id=3 "
    "parent_event_id=2 tick=237950940537 request_id=301 dyn_inst_seq=301 "
    "va=ffffffc009483fa8 pa=81d75fa8 field=effective_pa_unchanged "
    "detection_layer=L2 contained=1 outcome=NoFault "
    "containment_layer=L2 containment_reason=effective_pa_unchanged "
    "corr=seq_primary")
_HEAD = [
    "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=237950940537 "
    "request_id=301 corr=origin",
    "PROP-EVT: kind=tlb_lookup fault_id=1 event_id=1 parent_event_id=0 "
    "tick=237950940537 request_id=301 dyn_inst_seq=301 "
    "field=post_lookup state_before=pfn=81d75 state_after=pfn=100000000081d75 "
    "corr=seq_primary",
    "PROP-EVT: kind=tlb_pfn fault_id=1 event_id=2 parent_event_id=1 "
    "tick=237950940537 request_id=301 dyn_inst_seq=301 va=ffffffc009483fa8 "
    "pa=81d75fa8 before=81d75 after=100000000081d75 corr=seq_primary",
    _L2_DETECT,
]
# 该请求的后续"干净"事件（同 dyn_seq/request_id）。现状发射器把它们并入本链。
_LATER_WITNESSES = [
    "PROP-EVT: kind=sq_execute fault_id=1 event_id=4 parent_event_id=3 "
    "tick=237950940537 request_id=301 dyn_inst_seq=301 corr=seq_primary",
    "PROP-EVT: kind=sq_writeback fault_id=1 event_id=5 parent_event_id=4 "
    "tick=237950941869 request_id=301 dyn_inst_seq=301 corr=seq_primary",
    "PROP-EVT: kind=resp fault_id=1 event_id=6 parent_event_id=5 "
    "tick=237950942203 request_id=301 dyn_inst_seq=301 corr=seq_primary",
    "PROP-EVT: kind=taint_reg fault_id=1 event_id=7 parent_event_id=6 "
    "tick=237950942203 request_id=301 dyn_inst_seq=301 "
    "before=clean after=tainted corr=seq_primary",
]
# 收口标记由退出回调发射，parent 取该分支（ptag, request）链游标的最后事件：
# 现状形状里链上最后一个事件是 ev8(sq_complete)；修复目标形状里链止于 L2
# 检测事件 ev3 —— 两者都用真实游标语义（不得为通过门禁伪造顺序）。
_CHAIN_END = (
    "PROP-EVT: kind=chain_end fault_id=1 event_id=9 parent_event_id=8 "
    "tick=314515193310 detection_layer=L2 contained=1 "
    "outcome=detected_contained containment_layer=L2 "
    "containment_reason=effective_pa_unchanged corr=none")
_CHAIN_END_CLOSED = _CHAIN_END.replace("parent_event_id=8", "parent_event_id=3")


def _parse(lines):
    return [e for e in (P.parse_line(x) for x in lines) if e]


def _admit(events, run_id):
    cont = CC.containment_from_events(events, run_id, truncated=False)
    bundle = {"run_id": run_id, "activated": 1, "events": events, "rc": 0,
              "oracle_outcome": "Masked"}
    if cont:
        bundle["containment"] = cont
    return CC.check_admission(bundle), cont


def main():
    print("[A] 现状形状：含住 + 后续本链见证（T01-F0-W4 seed1 实录）")
    as_emitted = _parse(_HEAD + _LATER_WITNESSES + [_CHAIN_END])
    res_a, cont_a = _admit(as_emitted, "T01-F0-W4-seed1-asis")
    check("现状形状不得准入（admitted=False）", res_a["admitted"] is False,
          f"admitted={res_a['admitted']}")
    check("现状形状响亮给出 time_reversed_edge（checker 保持严格，裁决 D）",
          any(v.startswith("time_reversed_edge") for v in res_a["violations"]),
          res_a["violations"][:1])
    check("现状形状拿不出 containment 束（更深层仍有见证）", cont_a is None)
    check("现状形状 L2 检测事件被提升为 L5 见证（根因机理）",
          CC._layer_of(_parse([_L2_DETECT])[0], "tlb") == "L5")

    print("[B] 修复目标形状：含住的翻译在 L2 收口，后续事件不并入本链")
    fixed = _parse(_HEAD + [_CHAIN_END_CLOSED])
    res_b, cont_b = _admit(fixed, "T01-F0-W4-seed1-fixed")
    check("修复目标形状准入（admitted=True）", res_b["admitted"] is True,
          f"admitted={res_b['admitted']} viol={res_b['violations'][:1]}")
    check("准入路径 = 显式含住（option-2）", res_b["path"] == "contained",
          f"path={res_b['path']}")
    check("终局 = detected_contained", res_b["terminal"] == "detected_contained",
          res_b["terminal"])
    check("含住层 = L2 且后续层 L3/L4/L5 全 N/A",
          bool(cont_b) and cont_b["layer"] == "L2"
          and cont_b["na_layers"] == ["L3", "L4", "L5"],
          cont_b)
    check("无 time_reversed_edge", not any(
        v.startswith("time_reversed_edge") for v in res_b["violations"]))

    print("[C] 物理顺序真实性（parent.tick ≤ child.tick；同 tick 允许）")
    by_id = {e["event_id"]: e for e in fixed}
    bad = [(e["event_id"], e["parent_event_id"])
           for e in fixed if e.get("parent_event_id")
           and int(by_id[e["parent_event_id"]]["tick"]) > int(e["tick"])]
    check("修复目标形状无父子倒挂", not bad, bad)
    check("同 tick 父子被允许（PASS 依据：inj→tlb_lookup 同 tick）",
          int(by_id["0"]["tick"]) == int(by_id["1"]["tick"]))

    if FAILED:
        print(f"FAILURES: {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
