#!/usr/bin/env python3
"""test_lsu_hook_tlb.py — [MDSPEC][H2] TLB 翻译统一事件钩子契约测试。

规格（表 9 缺失钩子列，39 RunID 共文）：
"在 src/arch/arm/tlb.cc 与 table_walker.cc 增加 translate/walk/refill 节点"

SE 实证约束（CHAOS/gem5/src/arch/arm/tlb.cc:173 注释）：SE 经 translateSe
翻译、**从不进入 TLB::lookup**；LSQ 的翻译漏斗是
arch/arm/mmu.cc::MMU::translateTiming（SE/FS 共用，lsq.cc
sendFragmentToTranslation 直接调用）。故 H2 的 translate 节点挂
mmu.cc::translateTiming（SE 立即可验证，pilot A01-F0-W3 是 SE 负载）；
tlb.cc lookup 与 table_walker.cc walk/refill 节点属 FS 路径。

[R4-5.9] T08（walk/fill 配对）落地后，tlb_walk/tlb_refill 已注册（L2），
配对键 = walk_id；本测试从"未注册 = 诚实缺席"改为"已注册 + 配对契约"。
C++ 端（TableWalker::walk / CHAOSArmTLB::maybeDropWalkFill）为
COMPILE-UNVERIFIED（本 worktree 禁止 build），此处只钉契约面。

契约：
- kind=tlb_translate → L2（VA→PA 翻译请求离开 LSQ 后进入 MMU 漏斗）
- 必录字段：fault_id, dyn_inst_seq, va, request_id（pa 在入口未定，留空
  诚实；PA 物化由 resp 节点与 lsq_sendfrag→resp 链覆盖）
- kind=tlb_walk/tlb_refill → L2；必录包含 walk_id（配对键）
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

    print("[4] [R4-5.9] T08 walk/fill 配对节点注册（FS 轨道落地）")
    # R4-5.9：tlb_walk（walk 发出，TableWalker::walk）与 tlb_refill（该
    # walk 的 refill 完成）注册为 L2，配对键 = walk_id（两节点同值）。
    check("tlb_walk -> L2", P.KIND_LAYER.get("tlb_walk") == "L2",
          str(P.KIND_LAYER.get("tlb_walk")))
    check("tlb_refill -> L2", P.KIND_LAYER.get("tlb_refill") == "L2",
          str(P.KIND_LAYER.get("tlb_refill")))
    wreq = P.REQUIRED_FIELDS.get("tlb_walk")
    check("tlb_walk requires walk_id + va + seq/request_id + corr",
          wreq is not None
          and all(f in wreq for f in ("fault_id", "corr", "walk_id", "va",
                                      "dyn_inst_seq", "request_id")),
          str(wreq))
    rreq = P.REQUIRED_FIELDS.get("tlb_refill")
    check("tlb_refill requires walk_id + va + field + corr",
          rreq is not None
          and all(f in rreq for f in ("fault_id", "corr", "walk_id", "va",
                                      "field")),
          str(rreq))

    print("[5] [R4-5.9] T08-a 丢失配对契约（同一 walk_id 的双节点）")
    walk = P.parse_line(
        "PROP-EVT: kind=tlb_walk fault_id=7 corr=origin walk_id=101 "
        "va=ffffffc009483000 dyn_inst_seq=302 request_id=302")
    refill = P.parse_line(
        "PROP-EVT: kind=tlb_refill fault_id=7 corr=origin walk_id=101 "
        "va=ffffffc009483000 field=lost outcome=lost")
    check("complete tlb_walk validates",
          walk is not None and P.validate_event(walk) == [],
          str(P.validate_event(walk) if walk else "None"))
    check("complete tlb_refill (lost) validates",
          refill is not None and P.validate_event(refill) == [],
          str(P.validate_event(refill) if refill else "None"))
    check("pairing key equal on both nodes (walk_id)",
          walk is not None and refill is not None
          and walk["walk_id"] == refill["walk_id"] == "101")
    check("both nodes carry the same fault_id (chain binding)",
          walk is not None and refill is not None
          and walk["fault_id"] == refill["fault_id"] == "7")
    check("tlb_walk/tlb_refill reach L2 in a chain",
          P.provable_to([walk, refill])["provable_to"] == "L2",
          str(P.provable_to([walk, refill])))
    bad_walk = P.parse_line("PROP-EVT: kind=tlb_walk fault_id=7 corr=origin "
                            "va=1000 dyn_inst_seq=1 request_id=1")
    check("tlb_walk missing walk_id flagged",
          len(P.validate_event(bad_walk)) == 1,
          str(P.validate_event(bad_walk)))
    bad_refill = P.parse_line("PROP-EVT: kind=tlb_refill fault_id=7 "
                              "corr=origin va=1000 field=lost")
    check("tlb_refill missing walk_id flagged",
          len(P.validate_event(bad_refill)) == 1,
          str(P.validate_event(bad_refill)))

    print("[5] [R4-4] tlb_pfn seq-PRIMARY 关联契约（2026-10-20 裁决）")
    # R4-4：MMU::getTE 向 TLB 发布在飞翻译的 Request 身份 → tlb_pfn 链
    # SEQ-PRIMARY 注册。dyn_inst_seq/request_id 必录（"0"=未盖戳）；
    # corr 标注注册臂但空值合法（req_seq=0 且 PA 页未变 → 无关联面，
    # 链诚实止于本事件）。
    req = P.REQUIRED_FIELDS.get("tlb_pfn")
    check("tlb_pfn requires dyn_inst_seq + request_id (seq-primary)",
          req is not None and "dyn_inst_seq" in req and "request_id" in req,
          str(req))
    check("tlb_pfn keeps pfn/pa state fields",
          req is not None and all(f in req for f in
                                 ("va", "before", "after", "field",
                                  "state_before", "state_after")))
    check("tlb_pfn corr NOT required (empty = honest no-surface)",
          req is not None and "corr" not in req)
    good = P.parse_line(
        "PROP-EVT: kind=tlb_pfn fault_id=1 corr=seq_primary "
        "dyn_inst_seq=302 request_id=302 va=ffffffc009483fa8 "
        "pa=81d75fa8 before=81d75 after=100000000081d75 field=bit_flip "
        "state_before=81d75fa8 state_after=81d75fa8")
    check("complete seq_primary tlb_pfn validates",
          good is not None and P.validate_event(good) == [])
    unstamped = P.parse_line(
        "PROP-EVT: kind=tlb_pfn fault_id=2 corr= dyn_inst_seq=0 "
        "request_id=0 va=ffff7000 pa=7000 before=ff after=7f "
        "field=bit_flip state_before=7000 state_after=7000")
    check("unstamped seq ('0') + empty corr validates (fallback-only or "
          "chain-stops-at-TLB)", unstamped is not None
          and P.validate_event(unstamped) == [])
    bad = P.parse_line(
        "PROP-EVT: kind=tlb_pfn fault_id=3 va=1000 before=ff after=7f "
        "field=bit_flip state_before=1000 state_after=7000")
    errs = P.validate_event(bad)
    check("missing dyn_inst_seq/request_id flagged",
          len(errs) == 2, str(errs))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
