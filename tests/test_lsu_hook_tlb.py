#!/usr/bin/env python3
"""test_lsu_hook_tlb.py — [MDSPEC][H2] TLB 翻译统一事件钩子契约测试。

规格（表 9 缺失钩子列，39 RunID 共文）：
"在 src/arch/arm/tlb.cc 与 table_walker.cc 增加 translate/walk/refill 节点"

SE 实证约束（CHAOS/gem5/src/arch/arm/tlb.cc:173 注释）：SE 经 translateSe
翻译、**从不进入 TLB::lookup**；LSQ 的翻译漏斗是
arch/arm/mmu.cc::MMU::translateTiming（SE/FS 共用，lsq.cc
sendFragmentToTranslation 直接调用）。故 H2 的 translate 节点挂
mmu.cc::translateTiming（SE 立即可验证，pilot A01-F0-W3 是 SE 负载）；
tlb.cc lookup 与 table_walker.cc walk/refill 节点属 FS 路径——推迟到
FS TLB 轨道（W4 TLB-AliasPerm 负载本就 BLOCKED），不静默跳过。

契约：
- kind=tlb_translate → L2（VA→PA 翻译请求离开 LSQ 后进入 MMU 漏斗）
- 必录字段：fault_id, dyn_inst_seq, va, request_id（pa 在入口未定，留空
  诚实；PA 物化由 resp 节点与 lsq_sendfrag→resp 链覆盖）
- 发射端只对 fault-correlated 请求发射（规格 11 传播流语义）。

用法：python3 tests/test_lsu_hook_tlb.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def main():
    print("[1] H2 kind→层级与必录字段注册")
    check("tlb_translate -> L2", P.KIND_LAYER.get("tlb_translate") == "L2",
          str(P.KIND_LAYER.get("tlb_translate")))
    req = P.REQUIRED_FIELDS.get("tlb_translate")
    check("tlb_translate required fields",
          req is not None
          and all(f in req for f in ("fault_id", "dyn_inst_seq", "va",
                                     "request_id")))

    print("[2] 契约行校验")
    good = P.parse_line(
        "PROP-EVT: kind=tlb_translate fault_id=1 dyn_inst_seq=42 "
        "request_id=42 va=1ffff70 pa=")
    check("complete tlb_translate validates (pa empty = honest pending)",
          good is not None and P.validate_event(good) == [])
    bad = P.parse_line("PROP-EVT: kind=tlb_translate fault_id=1")
    errs = P.validate_event(bad)
    check("missing dyn_inst_seq/va/request_id flagged",
          len(errs) == 3, str(errs))

    print("[3] 链推进与层级语义")
    chain = [P.parse_line("PROP-EVT: kind=inj fault_id=1 event_id=0"),
             P.parse_line("PROP-EVT: kind=addr_form fault_id=1 event_id=1"),
             P.parse_line("PROP-EVT: kind=lsq_push fault_id=1 event_id=2"),
             P.parse_line("PROP-EVT: kind=tlb_translate fault_id=1 "
                          "event_id=3 dyn_inst_seq=42 request_id=42 va=1ffff70"),
             P.parse_line("PROP-EVT: kind=resp fault_id=1 event_id=4")]
    v = P.provable_to(chain)
    check("inj→addr_form→lsq_push→tlb_translate→resp reaches L3",
          v["provable_to"] == "L3", str(v))

    print("[4] FS 路径推迟如实记录（不静默）")
    # tlb_walk / tlb_refill 尚未注册 = FS 轨道未实现的诚实状态；
    # 注册它们是 FS TLB 轨道任务（W4 解锁后）的义务。
    check("tlb_walk/tlb_refill NOT yet registered (honest fs-pending)",
          "tlb_walk" not in P.KIND_LAYER
          and "tlb_refill" not in P.KIND_LAYER)
    evt = P.parse_line("PROP-EVT: kind=tlb_walk fault_id=1")
    check("unregistered kind rejected by validate_event",
          len(P.validate_event(evt)) >= 1)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
