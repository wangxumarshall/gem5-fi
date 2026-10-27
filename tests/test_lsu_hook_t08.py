#!/usr/bin/env python3
"""[MDSPEC][R4-5.9] T08 walk/fill pairing 契约测试。

规格（03 位置×模型矩阵 T08 行 / 07 展开执行矩阵 T08 行 / 09 逐 RunID 传播监控
T08 行 / 10 源码监控映射 T08 行）：
  实现"页表遍历 walk/fill 的事件配对"：绑定一条明确的 transaction ID
  （walk_id），记录 walk 发出 / refill 完成的 tick，丢失/重复/过早完成
  分成独立子模型。本单元落地 T08-a（walk/fill 丢失）：
  - 注入端：CHAOSArmTLB faultType=walk_pairing；walk 在发出点
    （TableWalker::walk）被丢弃 → 请求 translation 永不完成（Timeout 通道）。
    事件归一化触发 = lsuTier（F0/F4/F6，walk-issue 流）。
  - 观测端：tlb_walk(L2) / tlb_refill(L2) 两节点，共享 walk_id（配对键）
    + fault_id（链绑定）；T08-a 时 refill 以 field=lost/outcome=lost 显式
    登记（诚实缺席，不伪造一次完成的 refill）。
  - 路由：MODEL_FLAGS["T08"] 存在；MODEL_BLOCKED["T08"] 保持诚实短语
    （compile-unverified + FS-only，未获真机证据前不解除——不伪装完成）。

本测试只钉 Python 契约面 + 源码级钩子存在性；C++ 为 COMPILE-UNVERIFIED
（本 worktree 禁止 build）。

用法：python3 tests/test_lsu_hook_t08.py   （退出码 0 = 全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P       # noqa: E402
import lsu_campaign as lc         # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def _cell(model, freq, workload, run_id):
    n = max(lc.COL_RUNID, lc.COL_MODEL, lc.COL_FREQ, lc.COL_WORKLOAD) + 1
    c = [""] * n
    c[lc.COL_RUNID] = run_id
    c[lc.COL_MODEL] = model
    c[lc.COL_FREQ] = freq
    c[lc.COL_WORKLOAD] = workload
    return c


def main():
    print("[1] 观测端：walk/fill 配对节点注册与必录字段")
    check("tlb_walk -> L2", P.KIND_LAYER.get("tlb_walk") == "L2")
    check("tlb_refill -> L2", P.KIND_LAYER.get("tlb_refill") == "L2")
    wreq = P.REQUIRED_FIELDS.get("tlb_walk", [])
    rreq = P.REQUIRED_FIELDS.get("tlb_refill", [])
    check("tlb_walk requires walk_id (pairing key)", "walk_id" in wreq)
    check("tlb_refill requires walk_id (pairing key)", "walk_id" in rreq)
    check("tlb_refill requires field (lost vs refilled)", "field" in rreq)

    print("[2] 配对链路：同一 walk_id / 同一 fault_id 的两节点可证")
    pair = [P.parse_line(
                "PROP-EVT: kind=tlb_walk fault_id=9 corr=origin walk_id=55 "
                "va=ffffffc009483000 dyn_inst_seq=302 request_id=302 field=walk_pairing"),
            P.parse_line(
                "PROP-EVT: kind=tlb_refill fault_id=9 corr=origin walk_id=55 "
                "va=ffffffc009483000 field=lost outcome=lost")]
    check("both nodes validate", all(P.validate_event(e) == [] for e in pair),
          str([P.validate_event(e) for e in pair]))
    check("pair shares walk_id and fault_id",
          pair[0]["walk_id"] == pair[1]["walk_id"]
          and pair[0]["fault_id"] == pair[1]["fault_id"])
    check("pair reaches L2 (provable_to)", P.provable_to(pair)["provable_to"] == "L2",
          str(P.provable_to(pair)))
    check("beyond is Unknown (no fabrication of higher layers)",
          P.provable_to(pair)["beyond"] == "Unknown")

    print("[3] 路由：MODEL_FLAGS 落地 / T08-a 显式 canary（整模型仍 PARTIAL）")
    check("MODEL_FLAGS['T08'] is armtlb walk_pairing",
          lc.MODEL_FLAGS.get("T08") == ("armtlb", ["--tlb_fault_type", "walk_pairing"]),
          str(lc.MODEL_FLAGS.get("T08")))
    # [R6-PROPAGATION-V3] T08 left MODEL_BLOCKED (the generic bypass would
    # have unlocked W9 and T08-b/c/d).  The narrower gate is in resolve_cell:
    # only T08-F0/F4-W4 + explicit --t08a-canary, trial only.
    check("T08 is NOT in MODEL_BLOCKED (narrower RunID gate instead)",
          "T08" not in lc.MODEL_BLOCKED)
    blk = lc.T08_PARTIAL_REASON
    check("partial reason names T08-a and pending b/c/d",
          "PARTIAL_SUBMODEL_PROVEN" in blk and "T08-a" in blk
          and "T08-b" in blk and "T08-c" in blk and "T08-d" in blk, blk)
    wl = "TLB-AliasPerm 地址翻译探针"
    r = lc.resolve_cell(_cell("T08", "F0", wl, "T08-F0-W4"))
    check("resolve_cell(T08-F0-W4) default -> blocked PARTIAL reason",
          r[0] is None and "PARTIAL_SUBMODEL_PROVEN" in (r[2] or ""), str(r))
    rc = lc.resolve_cell(_cell("T08", "F0", wl, "T08-F0-W4"),
                         t08a_canary=True)
    check("explicit T08-a canary resolves to walk_pairing flags",
          rc[0] is not None and "walk_pairing" in rc[0]
          and rc[1] == lc.TLB_PROBE_GOLDEN, str(rc))
    rw9 = lc.resolve_cell(_cell("T08", "F0", "GAP/Graph500 子集",
                                "T08-F0-W9"), t08a_canary=True,
                          allow_blocked=True)
    check("T08-F0-W9 stays hard BLOCKED_WORKLOAD_GAP",
          rw9[0] is None and rw9[2].startswith("BLOCKED_WORKLOAD_GAP"),
          str(rw9))
    r2 = lc.resolve_cell(_cell("T01", "F0", wl, "T01-F0-W4"))
    check("T01 lookup mode unchanged (ar mtlb FS flags, no walk path)",
          r2[1] == lc.TLB_PROBE_GOLDEN and "--tlb_fault_type" in r2[0]
          and "walk_pairing" not in r2[0], str(r2[0][-4:]))

    print("[4] 源码级钩子存在性（COMPILE-UNVERIFIED，仅钉存在）")
    tw = (ROOT / "CHAOS/gem5/src/arch/arm/table_walker.cc").read_text()
    check("TableWalker::walk consults maybeDropWalkFill",
          "maybeDropWalkFill" in tw and "chaosTLB" in tw)
    check("walk_id assigned at WalkerState construction",
          "chaosWalkId" in tw and "++chaosNextWalkId" in tw)
    hh = (ROOT / "CHAOS/gem5/src/arch/arm/table_walker.hh").read_text()
    check("WalkerState carries chaosWalkId/chaosWalkStartTick",
          "chaosWalkId" in hh and "chaosWalkStartTick" in hh)
    tlb = (ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc").read_text()
    check("CHAOSArmTLB parses faultType walk_pairing -> WalkPairing",
          'if (s == "walk_pairing") return FaultType::WalkPairing;' in tlb)
    check("CHAOSArmTLB emits the pair via registerTlbWalkPair",
          "registerTlbWalkPair" in tlb)
    # [R4-10] the ctor guards now cover the whole walk/refill family (four
    # sub-models); the loud-refusal INTENT is unchanged, only the literal.
    check("CHAOSArmTLB panics loudly when a walk-family mode lacks tier/walker",
          tlb.count("panic(") >= 2 and "requires" in tlb
          and "walk/refill family" in tlb)
    prop = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc").read_text()
    check("registerTlbWalkPair emits tlb_walk + tlb_refill with shared walk_id",
          'notePropEvt("tlb_walk"' in prop and 'notePropEvt("tlb_refill"' in prop
          and '"walk_id"' in prop)

    print("[5] SPEC_IMPL_LANDED 登记（诚实：显式真机证据 + 证据债）")
    rm = (ROOT / "tools/lsu_runid_map.py").read_text()
    i = rm.find('"T08":')
    # [LSU][MDSPEC][R4-8-SPEC] window widened: the entry now also carries the
    # measured real-run evidence paragraph (was ~0.7 KB, now ~1.9 KB).
    seg = rm[i:i + 3500]
    check("SPEC_IMPL_LANDED carries a T08 entry",
          i != -1 and "walk_pairing" in seg)
    check("entry names the landed sub-model (T08-a) and pending b/c/d",
          "T08-a" in seg and "T08-b" in seg and "T08-c" in seg and "T08-d" in seg)
    # [LSU][MDSPEC][R4-8-SPEC] evidence upgraded from "NONE yet" to the
    # measured runs; the debt is now the *pending* b/c/d coverage.
    check("entry carries the measured real-run evidence + pending debt",
          "evidence: REAL RUNS" in seg and "7d52bc1392a10055" in seg
          and "STILL PENDING" in seg)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
