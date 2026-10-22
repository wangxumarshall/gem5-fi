#!/usr/bin/env python3
"""[MDSPEC][R4-9-FSMC] O04/O05/O06/O07/O09 契约测试（C 组 15 格）.

落地模板（mode_unimpl_plan.md §逐项落地模板）逐项钉死：
  1. 观测端契约：新 kind rmw_data/rmw_result/rmw_order (L1/L1/L2) +
     barrier_done/order_tag (L2) + 必录字段；合成链过 chain_check。
  2. 注入端源码契约（结构性断言，真实可跑）：钩子存在、注册点存在、
     RMW 钩子在 `pkt->isAtomicOp()` 门内（LSE 路径，不是 LLSC cmpAndSwap）、
     屏障钩子在 MemDepUnit 的插入/释放两端、hook-split 关闭 SQ-forward 数据面。
  3. 路由契约：MODEL_FLAGS 的 family/extra 精确匹配（端到端接线）。
  4. 响亮拒斥不变式：MODEL_BLOCKED 五项在案；F0 未实测流长 -> 拒斥（None）；
     真实 RunID 在 workload 阻塞解除前**任何情况下**都不得 resolve 成可跑。

用法：python3 tests/test_lsu_hook_o0x.py   （退出码 0 = 全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P      # noqa: E402
import lsu_chain_check as CC     # noqa: E402
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


def cell(runid, model, freq, workload):
    """Synthetic matrix row (only the columns resolve_cell reads)."""
    row = [""] * 12
    row[LC.COL_RUNID] = runid
    row[LC.COL_MODEL] = model
    row[LC.COL_FREQ] = freq
    row[LC.COL_WORKLOAD] = workload
    return row


def main():
    print("[1] 观测端契约：新 kind + 层级 + 必录字段")
    for k, layer in (("rmw_data", "L1"), ("rmw_result", "L1"),
                     ("rmw_order", "L2"), ("barrier_done", "L2"),
                     ("order_tag", "L2")):
        check(f"{k} 在 KIND_LAYER 注册且层级 {layer}",
              P.KIND_LAYER.get(k) == layer, str(P.KIND_LAYER.get(k)))
    check("rmw_data 必录字段（fault_id/corr/cache_line/field/before/after）",
          P.REQUIRED_FIELDS.get("rmw_data") ==
          ["fault_id", "corr", "cache_line", "field", "before", "after"],
          str(P.REQUIRED_FIELDS.get("rmw_data")))
    check("rmw_order 必录 state_before/state_after（完成面）",
          P.REQUIRED_FIELDS.get("rmw_order") ==
          ["fault_id", "corr", "cache_line", "field",
           "state_before", "state_after"],
          str(P.REQUIRED_FIELDS.get("rmw_order")))
    check("barrier_done / order_tag 必录 corr+field+state 对",
          P.REQUIRED_FIELDS.get("barrier_done") ==
          ["fault_id", "corr", "field", "state_before", "state_after"]
          and P.REQUIRED_FIELDS.get("order_tag") ==
          ["fault_id", "corr", "field", "state_before", "state_after"],
          str(P.REQUIRED_FIELDS.get("barrier_done")))
    check("既有 kind 未被本轮改动（inj/atomic_op/exmon_* 仍在）",
          all(k in P.KIND_LAYER for k in
              ("inj", "atomic_op", "exmon_monitor", "exmon_rmw", "exmon_stxr",
               "cache_access", "resp", "taint_reg", "chain_end")))

    # 合成 O05 链（真实发射顺序，键结构与 C14 链同形以保证逐边可证）：
    #   inj(origin) → rmw_result(L1 值面) → cache_access(L1) →
    #   rmw_order(L2 完成面, lost: committed→dropped) → resp(L3) →
    #   taint_reg(L4) → errant_commit → chain_end(L5)。
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=42946750 "
        "va=79280 cache_line=79280 field=rmw_order corr=origin",
        "PROP-EVT: kind=rmw_result fault_id=1 event_id=1 tick=42946755 "
        "cache_line=79280 field=rmw_latch before=4096 after=4097 "
        "corr=origin",
        "PROP-EVT: kind=cache_access fault_id=1 event_id=2 tick=42946760 "
        "va=79280 pa=79280 cache_line=79280 corr=addr_fallback",
        "PROP-EVT: kind=rmw_order fault_id=1 event_id=3 tick=42946770 "
        "cache_line=79280 field=lost state_before=committed "
        "state_after=dropped corr=origin",
        "PROP-EVT: kind=resp fault_id=1 event_id=4 tick=42961520 "
        "dyn_inst_seq=42 request_id=42 corr=addr_fallback",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=5 tick=42961521 "
        "dyn_inst_seq=42 phys_reg=5 arch_reg=5 corr=addr_fallback",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=6 tick=42963100 "
        "dyn_inst_seq=42 corr=taint_prop",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=7 tick=90000000 "
        "outcome=SDC detection_layer=none contained=0 corr=none",
    ]]
    check("合成 O05 链 8 事件全部可解析",
          len(chain) == 8 and all(e is not None for e in chain))
    no_corr = [e["kind"] for e in chain if not e.get("corr")]
    check("链上每事件 corr 非空（关联来源显式）", not no_corr, str(no_corr))
    rr = next(e for e in chain if e["kind"] == "rmw_result")
    check("rmw_result before/after = 值对（4096->4097）",
          rr["before"] == "4096" and rr["after"] == "4097",
          f"{rr['before']}->{rr['after']}")
    ro = next(e for e in chain if e["kind"] == "rmw_order")
    check("rmw_order state_before/after = committed->dropped（lost 子模型）",
          ro["state_before"] == "committed"
          and ro["state_after"] == "dropped",
          f"{ro['state_before']}->{ro['state_after']}")
    check("每事件过 validate_event（无缺键）",
          all(not P.validate_event(e) for e in chain),
          str([P.validate_event(e) for e in chain]))
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("O05 链逐边可证（L0->L1->L2->L3->L4->L5 全 proven）",
          all(f1["edges"][e] == "proven" for e in
              ("L0->L1", "L1->L2", "L2->L3", "L3->L4", "L4->L5")),
          str({k: vv for k, vv in f1["edges"].items()
               if not k.endswith("witness")}))
    check("O05 链 provable_to=L5（chain_end 在案）",
          f1["provable_to"] == "L5", str(f1["provable_to"]))
    # O09 的节点面止于 L1（返回锁存器）：只有 L1 节点在场时链诚实截断在
    # L1（不臆造 L2）；这是该模型的层位事实，不是缺件。
    o09 = [e for e in chain if e["kind"] != "rmw_order"]
    v2 = CC.check_chain(o09)
    check("去掉 rmw_order 后链在 L1 截断（L2 节点确为该子模型特有）",
          v2["faults"]["1"]["provable_to"] in ("L0", "L1"),
          str(v2["faults"]["1"]["provable_to"]))
    check("去掉 rmw_result（L1 值面节点）后链在 L0/L1 更早截断",
          CC.check_chain([e for e in chain
                          if e["kind"] not in ("rmw_result",
                                               "rmw_order")])
          ["faults"]["1"]["provable_to"] in ("L0", "L1"))

    print("[2] 注入端源码契约（结构性断言，真实可跑）")
    bhh = src("CHAOS/gem5/src/mem/cache/base.hh")
    bcc = src("CHAOS/gem5/src/mem/cache/base.cc")
    chk = src("CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.cc")
    chh = src("CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.hh")
    bhook = src("CHAOS/gem5/src/cpu/o3/chaos_barrier_hook.hh")
    mdcc = src("CHAOS/gem5/src/cpu/o3/mem_dep_unit.cc")
    lfh = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh")
    lfcc = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc")

    check("base.hh 声明 chaosRmwHook + chaosRmwCommit",
          "chaosRmwHook" in bhh and "chaosRmwCommit" in bhh)
    check("base.cc 定义 chaosRmwHook = nullptr",
          "CHAOSCache *BaseCache::chaosRmwHook = nullptr;" in bcc)
    check("base.cc 在同一 SwapReq 提交点调用 chaosRmwCommit",
          "chaosRmwCommit(pkt, blk_data);" in bcc)
    check("RMW 钩子位于 isAtomicOp 门内（LSE 路径，非 LLSC cmpAndSwap）",
          "if (pkt->isAtomicOp())" in bcc.split("chaosRmwCommit(pkt, blk_data)")[0]
          .rsplit("// Check RMW operations first", 1)[-1])
    check("CHAOSCache 实现 maybeCorruptRmw + 以 pkt->isAtomicOp() 复核",
          "CHAOSCache::maybeCorruptRmw" in chk and "pkt->isAtomicOp()" in chk)
    check("CHAOSCache 三种 RMW 规则齐备（swap_oldnew/result_old/lost/dup）",
          all(r in chk for r in ('"swap_oldnew"', '"result_old"', '"lost"',
                                 '"dup"')))
    check("CHAOSCache 模式/规则不匹配响亮 panic（半指定模型不被静默运行）",
          "is inconsistent with" in chk and "lsuRmwRule" in chh)
    check("CHAOSCache legacy 周期攻击在 rmw 模式关闭（lsu_hook_mode）",
          "rmw_mode;" in chk and "if (!lsu_hook_mode)" in chk)

    check("屏障注册表 header 存在且全 nullptr 默认（零回归）",
          "chaosBarrierInsertHook" in bhook and
          "chaosBarrierReleaseHook" in bhook and "= nullptr" in bhook)
    check("mem_dep_unit.cc 在 insertBarrierSN 顶部调用插入钩子",
          "chaosBarrierInsertHook &&" in mdcc and "NOT tracked" in mdcc)
    check("mem_dep_unit.cc 在 completeInst 释放点调用释放钩子且保留原路径",
          "chaosBarrierReleaseHook &&" in mdcc and "baction == 1" in mdcc
          and "assert(hasStoreBarrier());" in mdcc)
    check("CHAOSLSQFwd 声明 O06/O07 钩子 + 单消费者 barrier_active",
          "maybeCorruptBarrierInsert" in lfh
          and "maybeCorruptBarrierRelease" in lfh
          and "orderTagSubstitute" in lfh and "barrier_active" in lfh)
    check("CHAOSLSQFwd O06/O07 自注册（S10 先例）且需 lsuTier",
          "chaosBarrierInsertHook = &CHAOSLSQFwd::barrierInsertCb;" in lfcc
          and "--lsqfwd_o06/--lsqfwd_o07 require" in lfcc)
    check("CHAOSLSQFwd hook-split：O06/O07 下 SQ-forward 数据面关闭",
          "if (o06_mode || o07_mode) return;" in lfcc)
    check("O07 替换值只取另一个活 SN（不伪造），无候选则诚实跳过",
          "orderTagSubstitute" in lfcc and "return *it;" in lfcc
          and "if (other == 0)" in lfcc)

    print("[3] 路由契约（端到端接线，精确匹配）")
    check("MODEL_FLAGS['O04'] = cache/rmw_mux/swap_oldnew",
          LC.MODEL_FLAGS.get("O04") ==
          ("cache", ["--l1d_target_field", "rmw_mux",
                     "--l1d_rmw_rule", "swap_oldnew"]),
          str(LC.MODEL_FLAGS.get("O04")))
    check("MODEL_FLAGS['O09'] = cache/rmw_latch/result_old",
          LC.MODEL_FLAGS.get("O09") ==
          ("cache", ["--l1d_target_field", "rmw_latch",
                     "--l1d_rmw_rule", "result_old"]),
          str(LC.MODEL_FLAGS.get("O09")))
    check("MODEL_FLAGS['O05'] = cache/rmw_order/lost",
          LC.MODEL_FLAGS.get("O05") ==
          ("cache", ["--l1d_target_field", "rmw_order",
                     "--l1d_rmw_rule", "lost"]),
          str(LC.MODEL_FLAGS.get("O05")))
    check("MODEL_FLAGS['O06'] = lsqfwd/o06/early",
          LC.MODEL_FLAGS.get("O06") ==
          ("lsqfwd", ["--lsqfwd_o06", "--lsqfwd_o06_done", "early"]),
          str(LC.MODEL_FLAGS.get("O06")))
    check("MODEL_FLAGS['O07'] = lsqfwd/o07",
          LC.MODEL_FLAGS.get("O07") == ("lsqfwd", ["--lsqfwd_o07"]),
          str(LC.MODEL_FLAGS.get("O07")))
    check("FAMILY_MOUNT/FAMILY_SEED 覆盖两个 family",
          "cache" in LC.FAMILY_MOUNT and "lsqfwd" in LC.FAMILY_MOUNT
          and LC.FAMILY_SEED["cache"] == "--l1d_rng_seed"
          and LC.FAMILY_SEED["lsqfwd"] == "--rng_seed")
    prx = src("configs/se/lsu_proxy.py")
    check("lsu_proxy 暴露 RMW targetField 三值与 --l1d_rmw_rule",
          all(t in prx for t in ('"rmw_mux", "rmw_latch", "rmw_order"',
                                 "--l1d_rmw_rule"))
          or all(t in prx for t in ('"rmw_mux"', '"rmw_latch"',
                                    '"rmw_order"', "--l1d_rmw_rule")))
    check("lsu_proxy 暴露 --lsqfwd_o06 / --lsqfwd_o06_done / --lsqfwd_o07",
          all(t in prx for t in ("--lsqfwd_o06", "--lsqfwd_o06_done",
                                 "--lsqfwd_o07")))
    check("lsu_proxy 把 lsuRmwRule / o06Mode / o07Mode 传给 SimObject",
          "lsuRmwRule=args.l1d_rmw_rule" in prx
          and "o06Mode=args.lsqfwd_o06" in prx
          and "o07Mode=args.lsqfwd_o07" in prx)
    lfpy = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py")
    cpy = src("CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.py")
    check("SimObject .py 声明对应参数（参数面完整）",
          "o06Mode = Param.Bool" in lfpy and "o07Mode = Param.Bool" in lfpy
          and "o06BarrierDone = Param.String" in lfpy
          and "lsuRmwRule = Param.String" in cpy)

    print("[4] 响亮拒斥不变式（不得静默解锁）")
    for m in ("O04", "O05", "O06", "O07", "O09"):
        check(f"MODEL_BLOCKED['{m}'] 在案（无真机证据不得解锁）",
              m in LC.MODEL_BLOCKED, "missing")
    for m in ("O04", "O09"):
        check(f"MODEL_BLOCKED['{m}'] 记为 deferred(RMW…)",
              LC.MODEL_BLOCKED[m].startswith("deferred(RMW"),
              LC.MODEL_BLOCKED[m][:40])
    for m in ("O05", "O06", "O07"):
        check(f"MODEL_BLOCKED['{m}'] 保留 multicore-fs 前缀（triage 分桶）",
              "multicore" in LC.MODEL_BLOCKED[m],
              LC.MODEL_BLOCKED[m][:60])
    # F0 未实测流长必须拒斥（R4-1-review-I2：不得复用别的流的数）
    check("O04 F0 未实测流长 -> 拒斥（None）",
          LC._cache_tier_flags("O04", "F0", "lse_rmw") is None)
    check("O09 F0 未实测流长 -> 拒斥（None）",
          LC._cache_tier_flags("O09", "F0", "lse_rmw") is None)
    check("O06 F0 未实测流长 -> 拒斥（None）",
          LC._lsqfwd_tier_flags("O06", "F0", "barrier_probe") is None)
    check("O07 F0 未实测流长 -> 拒斥（None）",
          LC._lsqfwd_tier_flags("O07", "F0", "barrier_probe") is None)
    check("F2 档仍给出 tier 参数（非 F0 不受 span 契约约束）",
          LC._cache_tier_flags("O04", "F2", "lse_rmw") ==
          ["--l1d_lsu_tier", "F2", "--l1d_warmup_events", "0",
           "--l1d_span_events", "1000"],
          str(LC._cache_tier_flags("O04", "F2", "lse_rmw")))

    # 真实 RunID：15 格在 Atomic-Litmus 负载阻塞下永远不得 resolve 成可跑
    rows = {
        "O04-F0-W7": ("O04", "F0", "Atomic-Litmus 并发探针"),
        "O04-F2-W7": ("O04", "F2", "Atomic-Litmus 并发探针"),
        "O04-F6-W7": ("O04", "F6", "Atomic-Litmus 并发探针"),
        "O05-F0-W7": ("O05", "F0", "Atomic-Litmus 并发探针"),
        "O05-F4-W7": ("O05", "F4", "Atomic-Litmus 并发探针"),
        "O05-F6-W7": ("O05", "F6", "Atomic-Litmus 并发探针"),
        "O06-F0-W7": ("O06", "F0", "Atomic-Litmus 并发探针"),
        "O06-F4-W7": ("O06", "F4", "Atomic-Litmus 并发探针"),
        "O06-F6-W7": ("O06", "F6", "Atomic-Litmus 并发探针"),
        "O07-F0-W7": ("O07", "F0", "Atomic-Litmus 并发探针"),
        "O07-F2-W7": ("O07", "F2", "Atomic-Litmus 并发探针"),
        "O07-F6-W7": ("O07", "F6", "Atomic-Litmus 并发探针"),
        "O09-F0-W7": ("O09", "F0", "Atomic-Litmus 并发探针"),
        "O09-F1-W7": ("O09", "F1", "Atomic-Litmus 并发探针"),
        "O09-F2-W7": ("O09", "F2", "Atomic-Litmus 并发探针"),
    }
    unlocked = []
    for rid, (m, f, wl) in rows.items():
        for allow in (False, True):
            flags, golden, reason = LC.resolve_cell(cell(rid, m, f, wl),
                                                    allow_blocked=allow)
            if flags is not None:
                unlocked.append(f"{rid}(allow_blocked={allow})")
            elif not reason:
                unlocked.append(f"{rid}(allow_blocked={allow}):EMPTY-REASON")
    check("15 格在任何 allow_blocked 取值下都不得 resolve 成可跑（无静默解锁）",
          not unlocked, str(unlocked))

    print()
    if FAILED:
        print(f"FAILED {len(FAILED)}: {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
