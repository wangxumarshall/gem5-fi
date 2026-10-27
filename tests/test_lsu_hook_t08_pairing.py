#!/usr/bin/env python3
"""test_lsu_hook_t08_pairing.py — [MDSPEC][R4-10] T08-b/c/d walk/refill 配对契约.

T08 的四个子模型（spec 07 T08 行）：
  T08-a walk_pairing       walk/fill 丢失   -> refill field=lost / outcome=lost
  T08-b walk_fill_dup      walk/fill 重复   -> outcome=duplicated
  T08-c walk_done_early    done 过早        -> outcome=early_done（数据正确）
  T08-d walk_stale_result  旧 walk 结果写入 -> outcome=stale

四者都经 issue 点（TableWalker::walk → maybeDropWalkFill）的同一 tier 门选中；
T08-a 在 issue 点丢弃 walk，T08-b/c/d 在 refill 完成点
（WalkUnit::insertTableEntry → maybeCorruptWalkRefill）施加。配对键 = walk_id；
两节点同 fault_id；refill 的 field/outcome 逐子模型自描述。

C++ 端为 COMPILE-UNVERIFIED（本 worktree 禁止 build），此处钉观测端契约 + 路由
+ 源码落点。

用法：python3 tests/test_lsu_hook_t08_pairing.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P      # noqa: E402
import lsu_campaign as LC        # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def src(path):
    return (ROOT / path).read_text(encoding="utf-8")


# (faultType, refill field, refill outcome)
SUBMODELS = [("walk_pairing", "lost", "lost"),
             ("walk_fill_dup", "walk_fill_dup", "duplicated"),
             ("walk_done_early", "walk_done_early", "early_done"),
             ("walk_stale_result", "walk_stale_result", "stale")]


def main():
    print("[1] 配对节点契约：tlb_walk / tlb_refill 层级 + 必录字段")
    check("tlb_walk -> L2", P.KIND_LAYER.get("tlb_walk") == "L2")
    check("tlb_refill -> L2", P.KIND_LAYER.get("tlb_refill") == "L2")
    wreq = P.REQUIRED_FIELDS.get("tlb_walk", [])
    check("tlb_walk requires walk_id + va + seq/request_id + corr",
          all(f in wreq for f in ("fault_id", "corr", "walk_id", "va",
                                  "dyn_inst_seq", "request_id")), str(wreq))
    rreq = P.REQUIRED_FIELDS.get("tlb_refill", [])
    check("tlb_refill requires walk_id + va + field + corr",
          all(f in rreq for f in ("fault_id", "corr", "walk_id", "va",
                                  "field")), str(rreq))

    print("[2] [R4-10] 四子模型的 field/outcome 自描述契约（逐项校验）")
    for ft, field, outcome in SUBMODELS:
        walk = P.parse_line(
            f"PROP-EVT: kind=tlb_walk fault_id=7 corr=origin walk_id=101 "
            f"va=ffffffc009483000 dyn_inst_seq=302 request_id=302")
        refill = P.parse_line(
            f"PROP-EVT: kind=tlb_refill fault_id=7 corr=origin walk_id=101 "
            f"va=ffffffc009483000 field={field} outcome={outcome}")
        check(f"{ft}: tlb_walk validates",
              walk is not None and P.validate_event(walk) == [],
              str(P.validate_event(walk) if walk else "None"))
        check(f"{ft}: tlb_refill (field={field}/outcome={outcome}) validates",
              refill is not None and P.validate_event(refill) == [],
              str(P.validate_event(refill) if refill else "None"))
        check(f"{ft}: pairing key equal (walk_id)",
              walk is not None and refill is not None
              and walk["walk_id"] == refill["walk_id"] == "101")
        check(f"{ft}: same fault_id binds the pair",
              walk is not None and refill is not None
              and walk["fault_id"] == refill["fault_id"] == "7")
        check(f"{ft}: pair reaches L2",
              P.provable_to([walk, refill])["provable_to"] == "L2")

    print("[3] T08-a lost arm stays field=lost/outcome=lost (unchanged)")
    refill_lost = P.parse_line(
        "PROP-EVT: kind=tlb_refill fault_id=1 corr=origin walk_id=703 "
        "va=ffffffc00801e240 field=lost outcome=lost")
    check("lost refill validates", refill_lost is not None
          and P.validate_event(refill_lost) == [])

    print("[4] 路由：walk 家族共 4 个 faultType + tier 追加条件")
    check("campaign WALK_FAULT_TYPES = the 4 sub-models",
          set(LC.WALK_FAULT_TYPES) == {ft for ft, _f, _o in SUBMODELS},
          str(LC.WALK_FAULT_TYPES))
    check("T08 defaults to the T08-a arm (walk_pairing)",
          LC.MODEL_FLAGS["T08"][1] == ["--tlb_fault_type", "walk_pairing"],
          str(LC.MODEL_FLAGS["T08"]))
    # [R6-PROPAGATION-V3] T08 left MODEL_BLOCKED; the narrower
    # partial-submodel gate still names T08-b/c/d explicitly.
    check("T08 partial gate names the landed T08-b/c/d sub-models",
          "T08" not in LC.MODEL_BLOCKED
          and "walk_fill_dup" in LC.T08_PARTIAL_REASON
          and "walk_done_early" in LC.T08_PARTIAL_REASON
          and "walk_stale_result" in LC.T08_PARTIAL_REASON,
          LC.T08_PARTIAL_REASON[:120])

    print("[5] C++ 落点（源码 grep）")
    cc = src("CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc")
    hh = src("CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh")
    tw = src("CHAOS/gem5/src/arch/arm/table_walker.cc")
    for s in ("walk_fill_dup", "walk_done_early", "walk_stale_result"):
        check(f"CHAOSArmTLB.cc maps '{s}'", f'"{s}"' in cc)
    check("CHAOSArmTLB.cc defines maybeCorruptWalkRefill",
          "maybeCorruptWalkRefill" in cc)
    check("CHAOSArmTLB.hh declares maybeCorruptWalkRefill",
          "maybeCorruptWalkRefill" in hh)
    check("table_walker.cc calls maybeCorruptWalkRefill at the refill point",
          "maybeCorruptWalkRefill" in tw)
    check("table_walker.cc performs the duplicated insert (T08-b)",
          "chaos_dup_refill" in tw)
    prop = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc")
    for o in ("duplicated", "early_done", "stale"):
        check(f"CHAOSPropagation.cc labels outcome '{o}'", f'"{o}"' in prop)
    cfg = src("configs/se/arm_chaos_fs.py")
    for s in ("walk_fill_dup", "walk_done_early", "walk_stale_result"):
        check(f"arm_chaos_fs.py --tlb_fault_type accepts '{s}'",
              f'"{s}"' in cfg)
    check("arm_chaos_fs.py defines WALK_FAULT_TYPES (pre-flight family gate)",
          "WALK_FAULT_TYPES" in cfg)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
