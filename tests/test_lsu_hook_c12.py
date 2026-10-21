#!/usr/bin/env python3
"""test_lsu_hook_c12.py — [MDSPEC][R4-5.2] C12 fill 时序偏移模式契约测试.

落地模板（mode_unimpl_plan.md §逐项落地模板）第 4 步：C12（6 RunID，
阻塞短语 "consumer-side: fill-timing event source only"）的注入端模式
（targetField=mshr_fill_timing + BaseCache::recvTimingResp 顶部 fill 推迟
钩子）、观测端（inj corr=origin + 既有 mshr_fill/cache_fill/mshr_free/
resp/taint_reg 链 kind——C12 不新增 kind；inj 的 before/after = 故障值
即 fill 交付 tick 的前/后）、路由（lsu_proxy choices → MODEL_FLAGS →
CACHE_F0_SPAN 实测跨度（C12 自有流：L1D read fill，与 C11 merge 流分开
实测）→ 从 MODEL_BLOCKED 删除）与 L0 注入行契约逐项钉死。

用法：python3 tests/test_lsu_hook_c12.py   （退出码 0=全 PASS）
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
    print("[1] 观测端契约：C12 链复用既有 kind（无新 kind）+ 必录字段")
    chain_kinds = ["inj", "cache_access", "mshr_fill", "cache_fill",
                   "mshr_free", "resp", "lq_complete", "taint_reg",
                   "consumer", "errant_commit", "chain_end"]
    for k in chain_kinds:
        check(f"{k} 在 KIND_LAYER 注册", k in P.KIND_LAYER,
              str(P.KIND_LAYER.get(k)))
    check("inj 必录字段 = fault_id+corr（R4-4-review-I1）",
          P.REQUIRED_FIELDS.get("inj") == ["fault_id", "corr"],
          str(P.REQUIRED_FIELDS.get("inj")))
    check("mshr_fill 必录字段含 corr（C12 入链臂标注）",
          "corr" in P.REQUIRED_FIELDS.get("mshr_fill", []),
          str(P.REQUIRED_FIELDS.get("mshr_fill")))
    check("C12 无新 kind（inj/mshr_fill/cache_fill 复用，KIND_LAYER 无 "
          "mshr_fill_timing 事件 kind）",
          "mshr_fill_timing" not in P.KIND_LAYER,
          str(P.KIND_LAYER.get("mshr_fill_timing")))

    # 合成 C12 链（真实发射顺序）：inj(fill 响应到达并推迟, corr=origin,
    # before/after=交付 tick 前/后) → cache_access(推迟窗口内/后的重访,
    # L1) → mshr_fill/cache_fill/mshr_free(全部在偏移后的 tick, L2) →
    # resp/lq_complete/taint_reg(同 tick 响应交付, L3/L4) → errant_commit
    # (taint_prop) → consumer → chain_end。
    chain = [P.parse_line(l) for l in [
        # inj：addr 列 = 被推迟 fill 的行；before/after = 故障值（交付
        # tick）前/后（时序故障的被故障值就是交付时间）
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=42946750 va=79280 "
        "before=42946750 after=42960750 cache_line=79280 "
        "field=mshr_fill_timing corr=origin",
        "PROP-EVT: kind=cache_access fault_id=1 event_id=1 tick=42947000 "
        "va=79280 pa=79280 corr=addr_fallback",
        "PROP-EVT: kind=mshr_fill fault_id=1 event_id=2 tick=42960750 "
        "cache_line=79280 mshr_id=1 fill_id=1 corr=addr_fallback "
        "state_after=filled",
        "PROP-EVT: kind=cache_fill fault_id=1 event_id=3 tick=42960750 "
        "pa=79280 cache_line=79280 fill_id=1 corr=addr_fallback",
        "PROP-EVT: kind=mshr_free fault_id=1 event_id=4 tick=42960750 "
        "cache_line=79280 mshr_id=1 corr=addr_fallback "
        "state_after=mshr_freed",
        "PROP-EVT: kind=resp fault_id=1 event_id=5 tick=42961520 "
        "dyn_inst_seq=42 request_id=42 corr=addr_fallback",
        "PROP-EVT: kind=lq_complete fault_id=1 event_id=6 tick=42961520 "
        "dyn_inst_seq=42 lq_idx=3 va=79280 pa=79280 request_id=42 "
        "corr=addr_fallback",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=7 tick=42961521 "
        "dyn_inst_seq=42 phys_reg=5 arch_reg=5 corr=addr_fallback",
        "PROP-EVT: kind=consumer fault_id=1 event_id=8 tick=42963000 "
        "dyn_inst_seq=50 phys_reg=5 arch_reg=5 corr=taint_prop",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=9 tick=42963100 "
        "dyn_inst_seq=50 corr=taint_prop",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=10 tick=90000000 "
        "outcome=Masked corr=none",
    ]]
    check("合成 C12 链 11 事件全部可解析", len(chain) == 11
          and all(e is not None for e in chain))
    # R4-4-review-I1：链上每事件 corr 必须非空（显式标注关联来源）
    no_corr = [e["kind"] for e in chain if not e.get("corr")]
    check("链上每事件 corr 非空（关联来源显式）", not no_corr, str(no_corr))
    # C12 特有：时序偏移在流上可读——inj.before/after = 交付 tick 前/后，
    # 且 mshr_fill 的 tick 落在偏移后的窗口（>= inj.after 才算"推迟交付"）
    inj = chain[0]
    fill = next(e for e in chain if e["kind"] == "mshr_fill")
    check("inj before/after = fill 交付 tick 前/后（时序对在案）",
          int(inj["before"]) < int(inj["after"]),
          f"before={inj['before']} after={inj['after']}")
    check("mshr_fill.tick 落在偏移后窗口（>= inj.after）",
          int(fill["tick"]) >= int(inj["after"]),
          f"fill.tick={fill['tick']} inj.after={inj['after']}")
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("C12 链 L0→L4 全边 proven → full",
          f1["terminal"] == "full", f1["terminal"])
    check("C12 链 provable_to=L5（chain_end 在案）",
          f1["provable_to"] == "L5", str(f1["provable_to"]))

    print("[2] L0 注入行契约（cache_injections.log 实际格式）")
    inj_line = ("Tick: 42946750, Cache Block Addr: 496256, "
                "Field: mshr_fill_timing (C12 fill deferred 100 cycles), "
                "arrival_tick=42946750, deferred_tick=42960750, "
                "faults_injected: 1")
    fun_line = "FUNNEL: attempted=10879 eligible=3405 injected=1"
    l0 = OBS.parse_l0(
        "CHAOS_LSU_TRIGGER: injector=CHAOSCache tier=F0 attempted=10879 "
        "eligible=3405 injected=1",
        inj_line + "\n" + fun_line)
    check("无 L0 violation（注入行可解析）", not l0["violations"],
          str(l0["violations"]))
    check("漏斗四元组从 stdout 解析",
          (l0["attempted"], l0["eligible"], l0["injected"]) ==
          (10879, 3405, 1),
          str((l0["attempted"], l0["eligible"], l0["injected"])))
    check("注入明细 mode=field:mshr_fill_timing…",
          len(l0["injections"]) == 1
          and l0["injections"][0]["mode"].startswith(
              "field:mshr_fill_timing"),
          str(l0["injections"]))

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
    check("base.hh 声明 chaosFillTimingHook + chaosResumeDeferredResp",
          "chaosFillTimingHook" in bhh
          and "chaosResumeDeferredResp(PacketPtr pkt);" in bhh)
    check("base.cc 定义 + recvTimingResp 顶部咨询 chaosFillTimingHook",
          "CHAOSCache *BaseCache::chaosFillTimingHook = nullptr;" in bcc
          and "chaosFillTimingHook->maybeDeferFillTiming(this, pkt)" in bcc)
    # 顺序契约：钩子必须在 popSenderState 之前（MSHR sender state 未弹，
    # 推迟期间 MSHR 保持 outstanding、后续同 line 请求继续合并）
    resp_region = bcc[bcc.index("BaseCache::recvTimingResp(PacketPtr pkt)"):]
    resp_region = resp_region[:resp_region.index("popSenderState()")]
    check("钩子调用先于 popSenderState（MSHR 保持 outstanding）",
          "maybeDeferFillTiming" in resp_region)
    check("chaosResumeDeferredResp 转发到（受保护的）recvTimingResp",
          "void\nBaseCache::chaosResumeDeferredResp(PacketPtr pkt)\n{\n"
          "    recvTimingResp(pkt);\n}" in bcc)
    check("CHAOSCache.hh 声明 maybeDeferFillTiming + resumeDeferredFill",
          "maybeDeferFillTiming(BaseCache" in chh
          and "resumeDeferredFill();" in chh)
    check("CHAOSPropagation 提供 registerFillTimingFault",
          "registerFillTimingFault" in prop_hh and
          "CHAOSPropagation::registerFillTimingFault" in prop_cc)
    # inj 节点时序对：before/after = 交付 tick 前/后（流上可见）
    reg = prop_cc[prop_cc.index(
        "CHAOSPropagation::registerFillTimingFault"):]
    reg = reg[:reg.index("\n    }")]
    check("inj before/after = 交付 tick 前/后（时序对入统一流）",
          '";before=" << arrival_tick' in reg
          and '";after=" << deferred_tick' in reg)
    check("整行入 blk 注册表（延迟 fill 事件按重叠入链）",
          "blk_registry[b.byte_begin] = b;" in reg)
    ctor = chk[:chk.index("CHAOSCache::CHAOSCacheStats")]
    check("fill_timing 模式拒绝 lsuTier=off（大声失败，不静默）",
          'p.lsuTier == "off"' in ctor and "panic" in ctor)
    check("fill_timing 模式拒绝 lsuFillDelayCycles=0（零偏移=无故障）",
          "p.lsuFillDelayCycles == 0" in ctor and "panic" in ctor)
    check("hook 模式禁用 legacy 周期攻击（lsu_hook_mode 门）",
          "const bool lsu_hook_mode" in ctor
          and "if (!lsu_hook_mode)" in ctor)
    check("legacy cache 路径回归不变（victim/merge 钩子未动）",
          "chaosVictimHook = this" in chk
          and "BaseCache::chaosMergeHook = this" in chk)
    fill_fn = chk[chk.index("CHAOSCache::maybeDeferFillTiming"):]
    fill_fn = fill_fn[:fill_fn.index("\n    }")]
    check("触发语义走 ChaOSLsuTrigger（onAttempt/onEligible/onF6Event）",
          "onAttempt()" in fill_fn and "onEligible()" in fill_fn
          and "onF6Event(false)" in fill_fn)
    # [MDSPEC][R4-5.1-review-I1] F6 funnel 无双计（C11 修复形态复用）：
    # fill 钩子的 attempt 流 = onAttempt 每次调用恰一次；F6 事件门
    # onF6Event(false) 不得再计 attempted。
    check("F6 事件门不重复计 attempted（onF6Event(false)，review-I1）",
          "lsuTrigger->onF6Event(false);" in fill_fn
          and fill_fn.count("lsuTrigger->onAttempt();") == 1)
    check("fill 函数无手搓概率检查",
          "uniform_real_distribution" not in fill_fn
          and "uniform_int_distribution" not in fill_fn)
    # 资格门镜像 is_fill：非错误 READ + 非 forward MSHR
    check("资格门镜像 is_fill（read+非错误+非 forward MSHR）",
          "pkt->isRead()" in fill_fn and "pkt->isError()" in fill_fn
          and "mshr->isForward" in fill_fn)
    # 再入防护：推迟槽指针守卫（tier/maxFaults 无关，F5+unlimited 不环）
    check("再入防护（pkt == fillPendingPkt 直接处理）",
          "pkt == fillPendingPkt" in fill_fn)
    check("单槽守卫（槽占用时结构性拒绝第二份推迟）",
          "if (fillPendingPkt) return false;" in fill_fn)
    check("偏移 = 挂载缓存 clockEdge(fill_delay_cycles)（未来沿）",
          "clockEdge(Cycles(fill_delay_cycles))" in fill_fn
          and "when <= curTick()" in fill_fn)
    resume_fn = chk[chk.index("CHAOSCache::resumeDeferredFill"):]
    resume_fn = resume_fn[:resume_fn.index("\n    }")]
    check("resume 经 BaseCache 公共跳板再入 recvTimingResp",
          "chaosResumeDeferredResp(pkt)" in resume_fn
          and "fillPendingPkt = nullptr;" in resume_fn)
    trig_hh = src("CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh")
    check("第六 F6 事件源（L1D miss fill）已在 trigger 头文件登记",
          "SIXTH source" in trig_hh and "miss fill" in trig_hh
          and "mshr_fill_timing" in trig_hh)
    check("CHAOSCache.py 参数面（lsuFillDelayCycles + targetField 文档）",
          "lsuFillDelayCycles" in cpy and "mshr_fill_timing" in cpy)

    print("[4] 路由契约（lsu_proxy → MODEL_FLAGS → F0 跨度 → 解阻塞）")
    proxy = src("configs/se/lsu_proxy.py")
    check("lsu_proxy --l1d_target_field 含 mshr_fill_timing",
          '"mshr_fill_timing"' in proxy)
    check("lsu_proxy 挂载传递 lsuTier/Warmup/Span/FillDelayCycles",
          "lsuTier=args.l1d_lsu_tier" in proxy
          and "lsuWarmupEvents=args.l1d_warmup_events" in proxy
          and "lsuSpanEvents=args.l1d_span_events" in proxy
          and "lsuFillDelayCycles=args.l1d_fill_delay_cycles" in proxy)
    check("MODEL_FLAGS 注册 C12（显式 fill delay=100）",
          LC.MODEL_FLAGS.get("C12") ==
          ("cache", ["--l1d_target_field", "mshr_fill_timing",
                     "--l1d_fill_delay_cycles", "100"]),
          str(LC.MODEL_FLAGS.get("C12")))
    check("C12 已从 MODEL_BLOCKED 删除（实测可跑后才允许）",
          "C12" not in LC.MODEL_BLOCKED)
    check("后续模型未误解锁（C14/C15 仍 BLOCKED；L04 已于 R4-5.3、"
          "S10 已于 R4-5.7 落地解锁）",
          all(m in LC.MODEL_BLOCKED
              for m in ("C14", "C15")) and "S10" not in LC.MODEL_BLOCKED)
    for pair in (("C12", "cache_dirtyevict"), ("C12", "stream_chase"),
                 ("C12", "cache_mshr_refetch")):
        check(f"CACHE_F0_SPAN 实测条目 {pair}",
              isinstance(LC.CACHE_F0_SPAN.get(pair), int)
              and LC.CACHE_F0_SPAN[pair] > 0,
              str(LC.CACHE_F0_SPAN.get(pair)))
    check("C12 F0 tier flags 用实测跨度（warmup=1）",
          LC._cache_tier_flags("C12", "F0", "cache_dirtyevict") ==
          ["--l1d_lsu_tier", "F0", "--l1d_warmup_events", "1",
           "--l1d_span_events",
           str(LC.CACHE_F0_SPAN[("C12", "cache_dirtyevict")])],
          str(LC._cache_tier_flags("C12", "F0", "cache_dirtyevict")))
    check("未实测 (C12, workload) F0 拒绝（loud None）",
          LC._cache_tier_flags("C12", "F0", "sq_forward") is None)
    check("legacy cache 模型 tier flags 逐字节不变（[]）",
          LC._cache_tier_flags("C01", "F0", "cache_dirtyevict") == []
          and LC._cache_tier_flags("C09", "F2", "stream_chase") == [])
    check("C11 tier flags 不受 C12 落地影响（逐字节不变）",
          LC._cache_tier_flags("C11", "F0", "cache_dirtyevict") ==
          ["--l1d_lsu_tier", "F0", "--l1d_warmup_events", "1",
           "--l1d_span_events",
           str(LC.CACHE_F0_SPAN[("C11", "cache_dirtyevict")])])

    print("[5] 矩阵解析：6 个 C12 RunID 全部 runnable")
    header, cells = LC.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    c12 = [c for c in cells if c[LC.COL_MODEL].strip() == "C12"]
    check("C12 cell 数 = 6", len(c12) == 6, str(len(c12)))
    for c in c12:
        runid = c[LC.COL_RUNID].strip()
        flags, golden, note = LC.resolve_cell(c)
        ok = (flags is not None and golden
              and "--l1d_target_field" in flags
              and flags[flags.index("--l1d_target_field") + 1] ==
              "mshr_fill_timing"
              and "--l1d_fill_delay_cycles" in flags
              and "--l1d_lsu_tier" in flags)
        check(f"{runid} 解析为 mshr_fill_timing 运行配置", ok,
              f"flags={flags} note={note}")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
