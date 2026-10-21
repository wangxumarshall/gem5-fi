#!/usr/bin/env python3
"""[MDSPEC][R4-5.6] C15-b MSHR 容量仲裁伪空位（fake free）契约测试.

落地模板（mode_unimpl_plan.md §逐项落地模板）第 4 步：C15（6 MODE-UNIMPL
RunID：F0/F4/F6 × W6/W10；阻塞短语 "consumer-side: MSHR occupancy event
source only"，子模型 C15-a/b/c）的注入端模式
（targetField=mshr_occupancy + BaseCache::chaosMshrOccArbitrate @
allocateMissBuffer 尾部：队列满时清掉 Blocked_NoMSHRs 伪造一个空位）、
观测端（新 kind mshr_arb(L2) + 既有 mshr_* 链；inj corr=origin，
before/after=占用对；真实 activated = noteMshrAllocAttempt 的超额分配读回）、
路由（lsu_proxy choices → MODEL_FLAGS → CACHE_F0_SPAN 故意缺席 + census
命令）与 L0 注入行契约逐项钉死。

用法：python3 tests/test_lsu_hook_c15.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P      # noqa: E402
import lsu_chain_check as CC     # noqa: E402
import lsu_obs_core as OBS       # noqa: E402
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
    print("[1] 观测端契约：新 kind mshr_arb(L2) + 必录字段")
    check("mshr_arb 在 KIND_LAYER 注册且层级 L2",
          P.KIND_LAYER.get("mshr_arb") == "L2",
          str(P.KIND_LAYER.get("mshr_arb")))
    req = P.REQUIRED_FIELDS.get("mshr_arb", [])
    check("mshr_arb 必录字段（fault_id/corr/mshr_id/entry_index/"
          "cache_line/field/state_before/state_after）",
          req == ["fault_id", "corr", "mshr_id", "entry_index",
                  "cache_line", "field", "state_before", "state_after"],
          str(req))
    check("C14 的 mshr_busy 未被改动（前一单元回归）",
          P.REQUIRED_FIELDS.get("mshr_busy") ==
          ["fault_id", "corr", "mshr_id", "entry_index", "cache_line",
           "field", "state_before", "state_after"])
    check("既有 C-链 kind 未被改动",
          all(k in P.KIND_LAYER for k in
              ("inj", "mshr_alloc", "mshr_merge", "mshr_fill", "mshr_free",
               "cache_access", "resp", "taint_reg", "chain_end")))

    # 合成 C15 链（真实发射顺序）：inj(超额分配读回，corr=origin,
    # before/after=占用对) → cache_access(L1) → mshr_arb(仲裁观察, L2) →
    # resp/taint_reg/errant_commit → chain_end。
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=42946750 va=79280 "
        "before=6 after=7 cache_line=79280 field=mshr_occupancy corr=origin",
        "PROP-EVT: kind=cache_access fault_id=1 event_id=1 tick=42946760 "
        "va=79280 pa=79280 corr=addr_fallback",
        "PROP-EVT: kind=mshr_arb fault_id=1 event_id=2 tick=42946770 "
        "cache_line=79280 mshr_id=8 entry_index=7 field=capacity "
        "state_before=full_blocked state_after=over_commit_alloc "
        "corr=origin",
        "PROP-EVT: kind=resp fault_id=1 event_id=3 tick=42961520 "
        "dyn_inst_seq=42 request_id=42 corr=addr_fallback",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=4 tick=42961521 "
        "dyn_inst_seq=42 phys_reg=5 arch_reg=5 corr=addr_fallback",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=5 tick=42963100 "
        "dyn_inst_seq=42 corr=taint_prop",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=6 tick=90000000 "
        "outcome=Timeout detection_layer=none contained=0 corr=none",
    ]]
    check("合成 C15 链 7 事件全部可解析", len(chain) == 7
          and all(e is not None for e in chain))
    no_corr = [e["kind"] for e in chain if not e.get("corr")]
    check("链上每事件 corr 非空（关联来源显式）", not no_corr, str(no_corr))
    inj = chain[0]
    check("inj before/after = 占用对（fire vs over-commit，before<after）",
          int(inj["before"]) == 6 and int(inj["after"]) == 7,
          f"before={inj['before']} after={inj['after']}")
    arb = next(e for e in chain if e["kind"] == "mshr_arb")
    check("mshr_arb field=capacity + state_before/after = 满→超额分配",
          arb["field"] == "capacity"
          and arb["state_before"] == "full_blocked"
          and arb["state_after"] == "over_commit_alloc",
          f"{arb['field']} {arb['state_before']}->{arb['state_after']}")
    check("mshr_arb entry_index = 占用计数（记账观察）",
          arb["entry_index"] == "7", arb["entry_index"])
    check("每事件过 validate_event（无缺键）",
          all(not P.validate_event(e) for e in chain),
          str([P.validate_event(e) for e in chain]))
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("C15 链 provable_to=L5（chain_end 在案）",
          f1["provable_to"] == "L5", str(f1["provable_to"]))
    check("C15 链 terminal=full（合成链全边 proven）",
          f1["terminal"] == "full", f1["terminal"])
    v2 = CC.check_chain([e for e in chain if e["kind"] != "mshr_arb"])
    check("去掉 mshr_arb 节点后链在 L2 前截断（节点确为 C15 特有）",
          v2["faults"]["1"]["provable_to"] in ("L0", "L1"),
          str(v2["faults"]["1"]["provable_to"]))

    print("[2] L0 注入行契约（cache_injections.log 实际格式）")
    fire_line = ("Tick: 42946750, Cache Block Addr: 79280, "
                 "Field: mshr_occupancy (C15-b fake-free at capacity), "
                 "in_service=6, faults_injected: 1")
    mat_line = ("Tick: 42946800, Cache Block Addr: 79344, "
                "Field: mshr_occupancy_materialized (C15-b over-capacity "
                "allocation allowed), occupancy=7, faults_injected: 1")
    l0 = OBS.parse_l0(
        "CHAOS_LSU_TRIGGER: injector=CHAOSCache tier=F6 attempted=31 "
        "eligible=1 injected=1",
        fire_line + "\n" + mat_line + "\n" +
        "FUNNEL: attempted=31 eligible=1 injected=1")
    check("无 L0 violation（两行注入记录均可解析）", not l0["violations"],
          str(l0["violations"]))
    check("漏斗四元组从 stdout 解析",
          (l0["attempted"], l0["eligible"], l0["injected"]) == (31, 1, 1),
          str((l0["attempted"], l0["eligible"], l0["injected"])))
    modes = sorted(i["mode"] for i in l0["injections"])
    check("两条注入明细 = fire 与 materialized",
          len(modes) == 2
          and modes[0].startswith("field:mshr_occupancy ")
          and modes[1].startswith("field:mshr_occupancy_materialized"),
          str(modes))

    print("[3] 注入端源码契约（触发纪律 + 端到端接线）")
    bhh = src("CHAOS/gem5/src/mem/cache/base.hh")
    bcc = src("CHAOS/gem5/src/mem/cache/base.cc")
    chk = src("CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.cc")
    chh = src("CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.hh")
    cpy = src("CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.py")
    prop_hh = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.hh")
    prop_cc = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.cc")
    trig_hh = src("CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh")
    check("base.hh 声明 chaosMshrOccHook + chaosMshrOccArbitrate",
          "static class CHAOSCache *chaosMshrOccHook;" in bhh
          and "void chaosMshrOccArbitrate(PacketPtr pkt, MSHR *mshr);" in bhh)
    check("base.cc 定义 chaosMshrOccHook = nullptr",
          "CHAOSCache *BaseCache::chaosMshrOccHook = nullptr;" in bcc)
    check("allocateMissBuffer 尾部调用 chaosMshrOccArbitrate（内联体）",
          "chaosMshrOccArbitrate(pkt, mshr);" in bhh)
    check("chaosMshrOccArbitrate 定义含 clearBlocked(Blocked_NoMSHRs)",
          "BaseCache::chaosMshrOccArbitrate" in bcc
          and "clearBlocked((BlockedCause)MSHRQueue_MSHRs);" in bcc)
    check("仲裁 helper 先读回（noteMshrAllocAttempt）再 fire",
          bcc.index("noteMshrAllocAttempt(")
          < bcc.index("maybeFakeFreeSlot(this, pkt, mshr,"))
    check("CHAOSCache.hh 声明 maybeFakeFreeSlot + noteMshrAllocAttempt + "
          "单槽/计数成员",
          "maybeFakeFreeSlot(BaseCache" in chh
          and "noteMshrAllocAttempt(BaseCache" in chh
          and "bool mshr_fake_free_armed = false;" in chh
          and "uint64_t mshr_fake_free_fires = 0;" in chh
          and "uint64_t mshr_over_commit = 0;" in chh)
    check("CHAOSPropagation 提供 registerMshrArbFault（声明+定义）",
          "registerMshrArbFault" in prop_hh and
          "CHAOSPropagation::registerMshrArbFault" in prop_cc)
    check("mshr_arb 节点发射（field=capacity + 状态对）",
          'notePropEvt("mshr_arb"' in prop_cc
          and '{"field", "capacity"}' in prop_cc
          and '{"state_before", "full_blocked"}' in prop_cc
          and '{"state_after", "over_commit_alloc"}' in prop_cc)
    check("inj before/after = 占用对入统一流",
          '<< ";before=" << occ_before' in prop_cc
          and '<< ";after=" << occ_after' in prop_cc)
    check("整行入 blk 注册表（同 line 事件按重叠入链）",
          "blk_registry[b.byte_begin] = b;" in prop_cc)

    ctor = chk[:chk.index("CHAOSCache::CHAOSCacheStats")]
    check("mshr_occupancy 模式拒绝 lsuTier=off（大声失败，不静默）",
          "mshr_occ_mode" in ctor and 'p.lsuTier == "off"' in ctor
          and "panic" in ctor)
    check("注册 BaseCache::chaosMshrOccHook = this",
          "BaseCache::chaosMshrOccHook = this;" in ctor)
    check("C14 注册不被 C15 落地破坏（chaosMshrBusyHook = this）",
          "BaseCache::chaosMshrBusyHook = this;" in ctor)
    check("转义链完整（merge/fill/fill-busy 分支保留）",
          "BaseCache::chaosMergeHook = this;" in ctor
          and "BaseCache::chaosFillTimingHook = this;" in ctor)

    fire_fn = chk[chk.index("CHAOSCache::maybeFakeFreeSlot"):]
    fire_fn = fire_fn[:fire_fn.index("\n    }")]
    check("触发语义走 ChaOSLsuTrigger（onAttempt/onEligible/onF6Event）",
          "onAttempt()" in fire_fn and "onEligible()" in fire_fn
          and "onF6Event(false)" in fire_fn)
    check("F6 事件门不重复计 attempted（onF6Event(false)，review-I1）",
          "lsuTrigger->onF6Event(false);" in fire_fn
          and fire_fn.count("lsuTrigger->onAttempt();") == 1)
    check("fire 函数无手搓概率检查",
          "uniform_real_distribution" not in fire_fn
          and "uniform_int_distribution" not in fire_fn)
    check("单槽守卫（已伪造未消费时结构性拒绝）",
          "if (mshr_fake_free_armed) return false;" in fire_fn)
    check("G5 maxFaults 上限",
          "max_faults != 0 && faults_injected_count >= max_faults"
          in fire_fn)
    check("因模式关/挂载缓存提前返回（zero regression）",
          'if (target_field != "mshr_occupancy") return false;' in fire_fn
          and "if (cache != targetCache) return false;" in fire_fn)

    mat_fn = chk[chk.index("CHAOSCache::noteMshrAllocAttempt"):]
    mat_fn = mat_fn[:mat_fn.index("\n    }")]
    check("读回仅在 '仍满' 时计 activated（否则诚实 no-op 清标志）",
          "if (!is_full) {" in mat_fn
          and "mshr_fake_free_armed = false;" in mat_fn
          and "++mshr_over_commit;" in mat_fn)
    check("读回注册 prop 链（registerMshrArbFault）",
          "registerMshrArbFault(" in mat_fn)
    check("第十 F6 事件源（MSHR 容量仲裁）已在 trigger 头文件登记",
          "TENTH source" in trig_hh and "mshr_occupancy" in trig_hh)
    check("CHAOSCache.py 参数面（targetField 文档含 mshr_occupancy）",
          "mshr_occupancy" in cpy)

    print("[4] 路由契约（lsu_proxy → MODEL_FLAGS → F0 跨度 → 解阻塞）")
    proxy = src("configs/se/lsu_proxy.py")
    check("lsu_proxy --l1d_target_field 含 mshr_occupancy",
          '"mshr_occupancy"' in proxy)
    check("lsu_proxy --l1d_lsu_tier help 点名 C15",
          "C15" in proxy and "mshr_occupancy" in proxy)
    check("MODEL_FLAGS 注册 C15（mshr_occupancy）",
          LC.MODEL_FLAGS.get("C15") ==
          ("cache", ["--l1d_target_field", "mshr_occupancy"]),
          str(LC.MODEL_FLAGS.get("C15")))
    check("C15 仍在 MODEL_BLOCKED（compile-unverified，未实测不删）",
          "C15" in LC.MODEL_BLOCKED
          and "compile-unverified" in LC.MODEL_BLOCKED["C15"],
          str(LC.MODEL_BLOCKED.get("C15")))
    check("C14 仍在 MODEL_BLOCKED（前一单元未误解锁）",
          "C14" in LC.MODEL_BLOCKED
          and "compile-unverified" in LC.MODEL_BLOCKED["C14"])
    check("CACHE_F0_SPAN 无 C15 实测条目（故意缺席 = census 未做）",
          ("C15", "cache_dirtyevict") not in LC.CACHE_F0_SPAN
          and ("C15", "stream_chase") not in LC.CACHE_F0_SPAN)
    check("CACHE_F0_SPAN 注释含 C15 census 命令",
          "C15-SPAN-" in src("tools/lsu_campaign.py"))
    check("C15 F4 tier flags（inert span，lsqfwd 约定）",
          LC._cache_tier_flags("C15", "F4", "cache_dirtyevict") ==
          ["--l1d_lsu_tier", "F4", "--l1d_warmup_events", "0",
           "--l1d_span_events", "1000"],
          str(LC._cache_tier_flags("C15", "F4", "cache_dirtyevict")))
    check("C15 F0 未实测 → loud None（拒绝静默复用）",
          LC._cache_tier_flags("C15", "F0", "cache_dirtyevict") is None)
    check("legacy cache 模型 tier flags 逐字节不变（[]）",
          LC._cache_tier_flags("C01", "F0", "cache_dirtyevict") == []
          and LC._cache_tier_flags("C09", "F2", "stream_chase") == [])
    check("C11/C12/C14 tier flags 不受 C15 落地影响（逐字节不变）",
          LC._cache_tier_flags("C11", "F0", "cache_dirtyevict") ==
          ["--l1d_lsu_tier", "F0", "--l1d_warmup_events", "1",
           "--l1d_span_events",
           str(LC.CACHE_F0_SPAN[("C11", "cache_dirtyevict")])]
          and LC._cache_tier_flags("C14", "F5", "cache_dirtyevict") ==
          ["--l1d_lsu_tier", "F5", "--l1d_warmup_events", "0",
           "--l1d_span_events", "1000"])

    print("[5] 矩阵解析：C15 9 cell（6 MODE-UNIMPL + 3 LICENSE）")
    header, cells = LC.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    c15 = [c for c in cells if c[LC.COL_MODEL].strip() == "C15"]
    check("C15 cell 数 = 9", len(c15) == 9, str(len(c15)))
    w11 = [c for c in c15 if c[LC.COL_WORKLOAD].strip().startswith("SPEC")]
    check("其中 3 个为 W11/SPEC（LICENSE 阻塞）", len(w11) == 3, str(len(w11)))
    for c in c15:
        runid = c[LC.COL_RUNID].strip()
        flags, golden, note = LC.resolve_cell(c)
        check(f"{runid} 诚实 BLOCKED（compile-unverified 或 LICENSE）",
              flags is None and ("compile-unverified" in note
                                 or "spec-license" in note), note)
    # 临时 pop MODEL_BLOCKED["C15"] 验证路由本身可解析（try/finally 复原）
    saved = LC.MODEL_BLOCKED.pop("C15")
    try:
        for c in c15:
            runid = c[LC.COL_RUNID].strip()
            freq = c[LC.COL_FREQ].strip()
            flags, golden, note = LC.resolve_cell(c)
            if freq == "F0":
                # F0 cells: span unmeasured -> loud refusal (except W11 which
                # stays LICENSE-blocked by the earlier workload gate)
                if c[LC.COL_WORKLOAD].strip().startswith("SPEC"):
                    ok = flags is None and "spec-license" in note
                else:
                    ok = flags is None and "F0-span-unmeasured" in note
                check(f"{runid} 解锁后 F0 跨度未实测 → loud 拒绝", ok, note)
            elif c[LC.COL_WORKLOAD].strip().startswith("SPEC"):
                check(f"{runid} LICENSE 阻塞不因解锁而消失",
                      flags is None and "spec-license" in note, note)
            else:
                ok = (flags is not None and golden
                      and "--l1d_target_field" in flags
                      and flags[flags.index("--l1d_target_field") + 1] ==
                      "mshr_occupancy"
                      and "--l1d_lsu_tier" in flags)
                check(f"{runid} 解锁后解析为 mshr_occupancy 运行配置", ok,
                      f"flags={flags} note={note}")
    finally:
        LC.MODEL_BLOCKED["C15"] = saved
    check("MODEL_BLOCKED['C15'] 已复原", "C15" in LC.MODEL_BLOCKED)

    print("[6] SPEC_IMPL_LANDED 诚实登记")
    rm = src("tools/lsu_runid_map.py")
    check("SPEC_IMPL_LANDED 含 C15 条目（C15-b 落地 + C15-a/c 未落地）",
          '"C15": "implemented(c15b_fake_free' in rm
          and "C15-a occupancy counter +/-1" in rm
          and "C15-c free-list selects" in rm)
    check("C15 条目写明 compile-unverified / 无真机证据",
          "compile-unverified from the isolated no-build worktree" in rm
          and "no census/pilot/chain evidence" in rm)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
