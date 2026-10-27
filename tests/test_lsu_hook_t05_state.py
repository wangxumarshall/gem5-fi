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

    print("[6] R6-PROPAGATION-V3：T05/T06/T07 已移出 MODEL_BLOCKED（模式在冻结二进制中）")
    for model in ("T05", "T06", "T07"):
        check(f"{model} is NOT in MODEL_BLOCKED",
              model not in LC.MODEL_BLOCKED,
              repr(LC.MODEL_BLOCKED.get(model)))
        check(f"{model} stays routed in MODEL_FLAGS",
              model in LC.MODEL_FLAGS,
              str(LC.MODEL_FLAGS.get(model)))

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

    print("[8] [R6-V4-STATECOUNT] 注入日志写入点必须同时递增统计计数")
    # 真缺陷（实测 T05-F0-W4 / T06-F0-W4 seed1）：applyEntryFieldFault() 写了
    # 注入日志、递增了 numStateFaults 与 faults_injected_count（funnel 因此
    # 报 injected=1），却**漏掉** stats->numFaultsInjected++，于是 stats.txt=0，
    # campaign 三源交叉核对判 count_contradiction=true。
    body = cc.split("CHAOSArmTLB::applyEntryFieldFault", 1)
    check("applyEntryFieldFault definition present", len(body) == 2)
    body = body[1].split("// [MDSPEC][R4-10-T07] CAM-compare", 1)[0]
    check("applyEntryFieldFault increments numStateFaults",
          "stats->numStateFaults++" in body)
    check("applyEntryFieldFault increments faults_injected_count",
          "++faults_injected_count" in body)
    check("applyEntryFieldFault increments numFaultsInjected",
          "stats->numFaultsInjected++" in body,
          "missing stats->numFaultsInjected++ (stats/log contradiction)")
    # 一般不变式（带具名豁免）：写注入日志的函数必须在**本函数内**或
    # **具名他处**递增 numFaultsInjected。豁免只有三条，且各写明理由：
    #   CHAOSArmTLB(ctor)      — 只写档位/能力诊断，不是注入；
    #   lookupTierBookAttempt  — `arm_tlb_lookup_tier` 诊断行；
    #   maybeCorruptWalkRefill — T08-b/c/d 的一次性故障在 arm 点已计数
    #                            （见下方 [9] 的“不重复计数”契约）。
    # 其他任何写日志却不计数的函数（尤其 T07 的 maybeCorruptLookup）都
    # 必须响亮失败，不得被静默放过。
    import re as _re
    EXEMPT = {"CHAOSArmTLB", "lookupTierBookAttempt", "maybeCorruptWalkRefill"}
    marks = list(_re.finditer(r"CHAOSArmTLB::(\w+)\s*\(", cc))
    offenders = []
    scanned = 0
    for i, m in enumerate(marks):
        seg = cc[m.start(): marks[i + 1].start() if i + 1 < len(marks) else len(cc)]
        if "log_stream->stream()" in seg:
            scanned += 1
            if "numFaultsInjected++" not in seg and m.group(1) not in EXEMPT:
                offenders.append(m.group(1))
    check("至少扫描到一个写注入日志的函数体", scanned > 0, str(scanned))
    check("每个写注入日志的函数都在本处或具名他处计数", not offenders,
          str(offenders))

    print("[9] [R6-V4-STATECOUNT] T08-b/c/d 一次性故障只计一次（arm 计数，refill 不再加）")
    arm_seg = cc.split("if (fault_type_enum != FaultType::WalkPairing) {", 1)
    check("arm 分支存在", len(arm_seg) == 2)
    # 尾部标记用 “the walk proceeds” 那条 return（其前的 return 是
    # stale-no-previous 的诚实 no-op 分支，尚未计数）。
    arm_body = arm_seg[1].split("return false;   // the walk proceeds", 1)[0]
    check("arm 点递增 numFaultsInjected",
          "stats->numFaultsInjected++" in arm_body)
    check("arm 点消耗 fault budget", "++faults_injected_count" in arm_body)
    refill = cc.split("CHAOSArmTLB::maybeCorruptWalkRefill", 1)
    check("maybeCorruptWalkRefill 存在", len(refill) == 2)
    refill_body = refill[1].split("// Maintain the last-completed-walk record",
                                 1)[0]
    check("refill 分支不再重复递增 numFaultsInjected",
          "stats->numFaultsInjected++" not in refill_body,
          "double count: arm already counted this one fault")

    print("[10] [R6-V4-T07CHAIN] 状态/CAM 故障在 PA 真重定向时打开关联臂")
    prop = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc")
    seg = prop.split("CHAOSPropagation::registerTlbStateFault", 1)
    check("registerTlbStateFault 存在", len(seg) == 2)
    body = seg[1].split("CHAOSPropagation::registerTlbWalkPair", 1)[0]
    check("状态故障走共享判据 tlbRegistrationArms",
          "chaos_chain::tlbRegistrationArms" in body)
    check("按 pa_changed 判定（PA 未变则不开臂）",
          "pa_changed" in body and "new_page != old_page" in body)
    check("seq 主臂登记 addr_registry", "addr_registry[va]" in body)
    check("PA 页回退臂登记 blk_registry", "blk_registry[new_page]" in body)
    check("PA 中立时不开臂（arms.seq_primary / addr_fallback 双门）",
          "if (arms.seq_primary)" in body and "if (arms.addr_fallback)" in body)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
