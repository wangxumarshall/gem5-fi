#!/usr/bin/env python3
"""test_lsu_hook_t05_state.py — [MDSPEC][R4-10] T05/T06/T07 契约测试.

覆盖三个此前 MODE-UNIMPL 的 TLB 子模型族（FS-only, CHAOSArmTLB）：

  T05 表项身份/生命周期状态：valid清零/伪置位、global翻转、ASID替换
  T06 访问属性合法替换（PPN不变）：AP权限 / memory type / page size
  T07 CAM比较/way选择：false hit / double hit / wrong-way

观测端：新增 kind `tlb_state`（L2），载荷 = field + state_before/state_after
（被改字段文本 before/after；不像 tlb_pfn 那样以 before/after pfn 为载荷，
因为这三个模型的故障面不是 pfn）。corr 与 tlb_pfn 同约定：空值合法
（无关联面 = req_seq 未盖戳，链诚实止于本事件）。

C++ 端（CHAOSArmTLB::maybeCorrupt / maybeCorruptLookup /
applyEntryFieldFault，tlb.cc 的 T07 钩子）为 COMPILE-UNVERIFIED
（本 worktree 禁止 build），此处只钉观测端契约 + 路由 + 源码落点。

用法：python3 tests/test_lsu_hook_t05_state.py   （退出码 0=全 PASS）
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


def main():
    print("[1] 观测端契约：tlb_state 注册为 L2 + 必录字段")
    check("tlb_state -> L2", P.KIND_LAYER.get("tlb_state") == "L2",
          str(P.KIND_LAYER.get("tlb_state")))
    req = P.REQUIRED_FIELDS.get("tlb_state")
    check("tlb_state required = fault_id/dyn_inst_seq/request_id/va/field/"
          "state_before/state_after",
          req is not None
          and all(f in req for f in ("fault_id", "dyn_inst_seq", "request_id",
                                     "va", "field", "state_before",
                                     "state_after")),
          str(req))
    check("tlb_state corr NOT required (empty = honest no-surface)",
          req is not None and "corr" not in req)
    check("tlb_state does NOT reuse tlb_pfn's before/after pfn payload",
          req is not None and "before" not in req and "after" not in req)

    print("[2] tlb_state 行校验（good / bad）")
    good = P.parse_line(
        "PROP-EVT: kind=tlb_state fault_id=5 corr=seq_primary "
        "dyn_inst_seq=302 request_id=302 va=ffffffc009483fa8 "
        "field=valid_clear state_before=1 state_after=0")
    check("complete seq_primary tlb_state validates",
          good is not None and P.validate_event(good) == [],
          str(P.validate_event(good) if good else "None"))
    unstamped = P.parse_line(
        "PROP-EVT: kind=tlb_state fault_id=6 corr= dyn_inst_seq=0 "
        "request_id=0 va=ffff7000 field=global_flip state_before=1 "
        "state_after=0")
    check("unstamped (corr empty) tlb_state validates",
          unstamped is not None and P.validate_event(unstamped) == [],
          str(P.validate_event(unstamped) if unstamped else "None"))
    bad = P.parse_line(
        "PROP-EVT: kind=tlb_state fault_id=7 va=1000 field=asid_subst")
    errs = P.validate_event(bad)
    check("missing dyn_inst_seq/request_id/state_before/state_after flagged",
          len(errs) == 4, str(errs))

    print("[3] 链推进：inj → tlb_state 可达 L2")
    chain = [P.parse_line("PROP-EVT: kind=inj fault_id=5 corr=origin"),
             P.parse_line("PROP-EVT: kind=tlb_state fault_id=5 "
                          "corr=seq_primary dyn_inst_seq=302 request_id=302 "
                          "va=ffffffc009483fa8 field=valid_clear "
                          "state_before=1 state_after=0")]
    v = P.provable_to(chain)
    check("inj→tlb_state reaches L2 (no fabrication of higher layers)",
          v["provable_to"] == "L2", str(v))

    print("[4] 每子模型的 field 文本契约（T05/T06/T07 共 10 个子模型）")
    submodels = {
        "T05": ["valid_clear", "valid_set", "global_flip", "asid_subst"],
        "T06": ["perm_subst", "memtype_subst", "pagesize_subst"],
        "T07": ["false_hit", "double_hit", "wrong_way"],
    }
    for model, fields in submodels.items():
        for f in fields:
            line = P.parse_line(
                f"PROP-EVT: kind=tlb_state fault_id=9 corr=seq_primary "
                f"dyn_inst_seq=1 request_id=1 va=1000 field={f} "
                f"state_before=a state_after=b")
            check(f"{model} field={f} validates as tlb_state",
                  line is not None and P.validate_event(line) == [],
                  str(P.validate_event(line) if line else "None"))

    print("[5] 路由（campaign MODEL_FLAGS）：T05/T06/T07 归属 armtlb 家族")
    for model, want in (("T05", "valid_clear"), ("T06", "perm_subst"),
                        ("T07", "false_hit")):
        fam, extra = LC.MODEL_FLAGS.get(model, (None, None))
        check(f"{model} -> armtlb family", fam == "armtlb", str(fam))
        check(f"{model} default sub-model = {want}",
              extra is not None and extra == ["--tlb_fault_type", want],
              str(extra))
    check("ARMTLB_MODELS contains T05/T06/T07",
          {"T05", "T06", "T07"} <= LC.ARMTLB_MODELS, str(LC.ARMTLB_MODELS))

    print("[6] 阻塞理由已诚实改写（landed / compile-unverified）")
    for model in ("T05", "T06", "T07"):
        r = LC.MODEL_BLOCKED.get(model, "")
        check(f"{model} block reason mentions LANDED + COMPILE-UNVERIFIED",
              "LANDED" in r and "COMPILE-UNVERIFIED" in r, repr(r))
        check(f"{model} block reason no longer says 'mode unimplemented'",
              "mode unimplemented" not in r, repr(r))

    print("[7] C++ 落点（源码 grep：注入器 + 钩子 + 配置 choices）")
    cc = src("CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc")
    hh = src("CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh")
    for s in ("valid_clear", "valid_set", "global_flip", "asid_subst",
              "perm_subst", "memtype_subst", "pagesize_subst",
              "false_hit", "double_hit", "wrong_way"):
        check(f"CHAOSArmTLB.cc maps '{s}'", f'"{s}"' in cc)
    check("CHaosArmTLB.hh declares applyEntryFieldFault",
          "applyEntryFieldFault" in hh)
    check("CHAOSArmTLB.cc defines maybeCorruptLookup",
          "maybeCorruptLookup" in src(
              "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc"))
    check("tlb.cc calls maybeCorruptLookup",
          "maybeCorruptLookup" in src("CHAOS/gem5/src/arch/arm/tlb.cc"))
    cfg = src("configs/se/arm_chaos_fs.py")
    for s in ("valid_clear", "asid_subst", "perm_subst", "pagesize_subst",
              "false_hit", "wrong_way"):
        check(f"arm_chaos_fs.py --tlb_fault_type accepts '{s}'",
              f'"{s}"' in cfg)
    check("CHaosPropagation declares registerTlbStateFault",
          "registerTlbStateFault" in src(
              "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"))
    check("CHAOSPropagation defines registerTlbStateFault",
          "registerTlbStateFault" in src(
              "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc"))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
