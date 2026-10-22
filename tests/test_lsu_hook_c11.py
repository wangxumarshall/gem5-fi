#!/usr/bin/env python3
"""test_lsu_hook_c11.py — [MDSPEC][R4-5.1] C11 MSHR merge corruption 契约测试.

落地模板（mode_unimpl_plan.md §逐项落地模板）第 4 步：C11（8 RunID，
阻塞短语 "consumer-side: MSHR merge event source only"）的注入端模式
（targetField=mshr_merge + BaseCache::handleTimingReqMiss 合并钩子）、
观测端（inj corr=origin + 既有 mshr_* / resp / taint_reg 链 kind——
C11 不新增 kind，注入节点经 writeNode 双发自动携带 before/after/
cache_line/corr）、路由（lsu_proxy choices → MODEL_FLAGS → CACHE_F0_SPAN
实测跨度 → 从 MODEL_BLOCKED 删除）与 L0 注入行契约逐项钉死。

用法：python3 tests/test_lsu_hook_c11.py   （退出码 0=全 PASS）
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
    print("[1] 观测端契约：C11 链复用既有 kind（无新 kind）+ 必录字段")
    chain_kinds = ["inj", "cache_access", "mshr_merge", "mshr_fill",
                   "mshr_free", "cache_fill", "resp", "lq_complete",
                   "taint_reg", "consumer", "errant_commit", "chain_end"]
    for k in chain_kinds:
        check(f"{k} 在 KIND_LAYER 注册", k in P.KIND_LAYER,
              str(P.KIND_LAYER.get(k)))
    check("inj 必录字段 = fault_id+corr（R4-4-review-I1）",
          P.REQUIRED_FIELDS.get("inj") == ["fault_id", "corr"],
          str(P.REQUIRED_FIELDS.get("inj")))
    check("mshr_merge 必录字段含 corr（C11 入链臂标注）",
          "corr" in P.REQUIRED_FIELDS.get("mshr_merge", []),
          str(P.REQUIRED_FIELDS.get("mshr_merge")))

    # 合成 C11 链（真实发射顺序）：inj(合并点注册, corr=origin) →
    # mshr_merge(同 tick, addr_fallback) → cache_access(后续重访) →
    # mshr_fill/cache_fill/mshr_free → resp/lq_complete(损坏地址响应) →
    # taint_reg → errant_commit → chain_end。
    chain = [P.parse_line(l) for l in [
        # inj：addr 列 = 损坏后目标地址；before/after=old/new_addr 提升
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=100 va=76e18 "
        "before=76e10 after=76e18 cache_line=76e00 field=mshr_merge "
        "corr=origin",
        "PROP-EVT: kind=mshr_merge fault_id=1 event_id=1 tick=100 "
        "cache_line=76e00 mshr_id=1 corr=addr_fallback "
        "state_after=merged_into_mshr",
        "PROP-EVT: kind=cache_access fault_id=1 event_id=2 tick=200 "
        "va=76e18 pa=76e18 corr=addr_fallback",
        "PROP-EVT: kind=mshr_fill fault_id=1 event_id=3 tick=300 "
        "cache_line=76e00 mshr_id=1 fill_id=1 corr=addr_fallback",
        "PROP-EVT: kind=cache_fill fault_id=1 event_id=4 tick=300 "
        "pa=76e00 cache_line=76e00 fill_id=1 corr=addr_fallback",
        "PROP-EVT: kind=mshr_free fault_id=1 event_id=5 tick=300 "
        "cache_line=76e00 mshr_id=1 corr=addr_fallback state_after=mshr_freed",
        "PROP-EVT: kind=resp fault_id=1 event_id=6 tick=310 dyn_inst_seq=42 "
        "request_id=42 corr=addr_fallback",
        "PROP-EVT: kind=lq_complete fault_id=1 event_id=7 tick=310 "
        "dyn_inst_seq=42 lq_idx=3 va=76e10 pa=76e18 request_id=42 "
        "corr=addr_fallback",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=8 tick=311 "
        "dyn_inst_seq=42 phys_reg=5 corr=addr_fallback",
        "PROP-EVT: kind=consumer fault_id=1 event_id=9 tick=400 "
        "dyn_inst_seq=50 corr=taint_prop",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=10 tick=401 "
        "dyn_inst_seq=50 corr=taint_prop",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=11 tick=900 "
        "outcome=SDC corr=none",
    ]]
    check("合成 C11 链 12 事件全部可解析", len(chain) == 12
          and all(e is not None for e in chain))
    # R4-4-review-I1：链上每事件 corr 必须非空（显式标注关联来源）
    no_corr = [e["kind"] for e in chain if not e.get("corr")]
    check("链上每事件 corr 非空（关联来源显式）", not no_corr, str(no_corr))
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("C11 链 L0→L4 全边 proven → full",
          f1["terminal"] == "full", f1["terminal"])
    # 链含 chain_end（L5）→ provable_to=L5；L4→L5 边以 chain_end 收口
    check("C11 链 provable_to=L5（chain_end 在案）",
          f1["provable_to"] == "L5", str(f1["provable_to"]))

    print("[2] L0 注入行契约（cache_injections.log 实际格式）")
    inj_line = ("Tick: 47052775, Cache Block Addr: 485376, "
                "Field: mshr_merge (C11 target addr bit_flip bit 3), "
                "old_addr=0x76e10, new_addr=0x76e18, faults_injected: 1")
    fun_line = "FUNNEL: attempted=10879 eligible=3421 injected=1"
    l0 = OBS.parse_l0(
        "CHAOS_LSU_TRIGGER: injector=CHAOSCache tier=F0 attempted=10879 "
        "eligible=3421 injected=1",
        inj_line + "\n" + fun_line)
    check("无 L0 violation（注入行可解析）", not l0["violations"],
          str(l0["violations"]))
    check("漏斗四元组从 stdout 解析",
          (l0["attempted"], l0["eligible"], l0["injected"]) ==
          (10879, 3421, 1),
          str((l0["attempted"], l0["eligible"], l0["injected"])))
    check("注入明细 mode=field:mshr_merge…",
          len(l0["injections"]) == 1
          and l0["injections"][0]["mode"].startswith("field:mshr_merge"),
          str(l0["injections"]))

    print("[3] 注入端源码契约（触发纪律 + 端到端接线）")
    bhh = src("CHAOS/gem5/src/mem/cache/base.hh")
    bcc = src("CHAOS/gem5/src/mem/cache/base.cc")
    chk = src("CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.cc")
    chh = src("CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.hh")
    prop_hh = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.hh")
    prop_cc = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.cc")
    check("base.hh 声明 chaosMergeHook", "chaosMergeHook" in bhh)
    check("base.cc 定义 + 合并分支咨询 chaosMergeHook",
          "CHAOSCache *BaseCache::chaosMergeHook = nullptr;" in bcc
          and "chaosMergeHook->maybeCorruptMergeTarget(this, pkt)" in bcc)
    # 顺序契约：钩子必须在 allocateTarget 之前（翻位后的地址才进入合并）
    merge_region = bcc[bcc.index("coalescing MSHR for"):bcc.index(
        "mshr->allocateTarget(pkt, forward_time")]
    check("钩子调用先于 allocateTarget（损坏地址真正入链）",
          "maybeCorruptMergeTarget" in merge_region)
    check("CHAOSCache.hh 声明 maybeCorruptMergeTarget",
          "maybeCorruptMergeTarget(BaseCache" in chh)
    check("CHAOSPropagation 提供 registerMshrMergeFault",
          "registerMshrMergeFault" in prop_hh and
          "CHAOSPropagation::registerMshrMergeFault" in prop_cc)
    check("合并模式拒绝 lsuTier=off（大声失败，不静默）",
          'p.lsuTier == "off"' in chk and "panic" in chk)
    merge_fn = chk[chk.index("CHAOSCache::maybeCorruptMergeTarget"):]
    merge_fn = merge_fn[:merge_fn.index("\n    }")]
    check("触发语义走 ChaOSLsuTrigger（onAttempt/onEligible/onF6Event）",
          "onAttempt()" in merge_fn and "onEligible()" in merge_fn
          and "onF6Event(false)" in merge_fn)
    # [MDSPEC][R4-5.1-review-I1] F6 funnel 无双计：merge 钩子的 attempt 流
    # = onAttempt 每次调用恰一次；F6 事件门 onF6Event(false) 不得再计
    # attempted（W1 thunk 站点保持默认 true——事件通知处无 onAttempt）。
    check("F6 事件门不重复计 attempted（onF6Event(false)，review-I1）",
          "lsuTrigger->onF6Event(false);" in merge_fn
          and merge_fn.count("lsuTrigger->onAttempt();") == 1)
    trig_hh = src("CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh")
    check("trigger 头文件 onF6Event(book_attempt=true) 双调用形态契约",
          "onF6Event(bool book_attempt = true)" in trig_hh
          and "if (book_attempt) ++attempted;" in trig_hh)
    check("第五 F6 事件源（MSHR merge）已在 trigger 头文件登记",
          "FIFTH source" in trig_hh and "MSHR merge" in trig_hh
          and "onF6Event(false)" in trig_hh)
    check("F6 触发条件=首个过资格门的 merge（非『于每次 merge』）",
          "FIRST merge that passes the eligibility gate" in merge_fn)
    check("合并函数无手搓概率检查",
          "uniform_real_distribution" not in merge_fn
          and "probability" not in merge_fn)
    # 位数域契约：对齐保持（bit >= log2(size)）+ 块内偏移界
    check("翻位限制在块偏移域（对齐+界内，P4-FIX-GEOM 类）",
          "while ((1u << lo) < size)" in merge_fn
          and "while ((1u << hi) < blk_sz)" in merge_fn)
    ctor = chk[:chk.index("CHAOSCache::CHAOSCacheStats")]
    # [MDSPEC][R4-5.2] C12 落地把门变量从 merge_mode 泛化为 lsu_hook_mode
    # （= merge_mode || fill_timing_mode）：merge 模式仍禁用 legacy 周期
    # 攻击（lsu_hook_mode 包含 merge_mode），C12 fill_timing 同门。
    check("合并模式禁用 legacy 周期攻击（不注入无关数据故障）",
          'const bool merge_mode = (target_field == "mshr_merge")' in ctor
          and "lsu_hook_mode = merge_mode || fill_timing_mode" in ctor
          and "if (!lsu_hook_mode)" in ctor)
    check("legacy cache 路径回归不变（victim 钩子未动）",
          "chaosVictimHook = this" in chk)

    print("[4] 路由契约（lsu_proxy → MODEL_FLAGS → F0 跨度 → 解阻塞）")
    proxy = src("configs/se/lsu_proxy.py")
    check("lsu_proxy --l1d_target_field 含 mshr_merge",
          '"mshr_merge"' in proxy)
    check("lsu_proxy 挂载传递 lsuTier/Warmup/Span",
          "lsuTier=args.l1d_lsu_tier" in proxy
          and "lsuWarmupEvents=args.l1d_warmup_events" in proxy
          and "lsuSpanEvents=args.l1d_span_events" in proxy)
    check("MODEL_FLAGS 注册 C11",
          LC.MODEL_FLAGS.get("C11") ==
          ("cache", ["--l1d_target_field", "mshr_merge"]),
          str(LC.MODEL_FLAGS.get("C11")))
    check("C11 已从 MODEL_BLOCKED 删除（实测可跑后才允许）",
          "C11" not in LC.MODEL_BLOCKED)
    # [MDSPEC][R4-5.2] C12 已按同一模板落地并实测（targetField=
    # mshr_fill_timing，见 test_lsu_hook_c12.py）；[R4-5.3] L04 已按同一
    # 模板落地并实测（--lsqfwd_l04 配对点交换，见 test_lsu_hook_l04.py）；
    # [R4-5.7] S10 已按同一模板落地（--lsqfwd_s10 StoreSet SSIT-ID 换值，
    # 见 test_lsu_hook_s10.py——compile-unverified，census/pilot 归集成侧）
    # ——三者不再列入"未解锁"钉；C14/C15 仍未实现，必须保持 BLOCKED。
    # [MDSPEC][R4-5.7b→R4-8-S10] S10 亦已落地并按**逐格**门禁接管：平台缺陷
    # 修好后（§R4-6-S10，真机 eligible>0）本轮实测两条 spec 载体的 eligible
    # 流（sq_forward 3 / gap_bfs 4）——F0 由 LSQFWD_F0_SPAN 门禁、F5 已激活、
    # F2 由 LSQFWD_INTERVAL_UNREACHABLE 逐格响亮拒绝，故 S10 不再列入
    # "未解锁"钉（此前断言 "S10 in MODEL_BLOCKED" 已随 R4-8-S10 失效）。
    check("后续模型未误解锁（C14/C15 亦已解锁；S10 已于 R4-8-S10 "
          "逐格门禁接管）",
          "C14" not in LC.MODEL_BLOCKED and "C15" not in LC.MODEL_BLOCKED
          and "S10" not in LC.MODEL_BLOCKED
          and ("S10", "F2", "sq_forward") in LC.LSQFWD_INTERVAL_UNREACHABLE)
    for pair in (("C11", "cache_dirtyevict"), ("C11", "stream_chase"),
                 ("C11", "cache_mshr_refetch")):
        check(f"CACHE_F0_SPAN 实测条目 {pair}",
              isinstance(LC.CACHE_F0_SPAN.get(pair), int)
              and LC.CACHE_F0_SPAN[pair] > 0,
              str(LC.CACHE_F0_SPAN.get(pair)))
    check("C11 F0 tier flags 用实测跨度（warmup=1）",
          LC._cache_tier_flags("C11", "F0", "cache_dirtyevict") ==
          ["--l1d_lsu_tier", "F0", "--l1d_warmup_events", "1",
           "--l1d_span_events",
           str(LC.CACHE_F0_SPAN[("C11", "cache_dirtyevict")])],
          str(LC._cache_tier_flags("C11", "F0", "cache_dirtyevict")))
    check("未实测 (C11, workload) F0 拒绝（loud None）",
          LC._cache_tier_flags("C11", "F0", "sq_forward") is None)
    check("legacy cache 模型 tier flags 逐字节不变（[]）",
          LC._cache_tier_flags("C01", "F0", "cache_dirtyevict") == []
          and LC._cache_tier_flags("C09", "F2", "stream_chase") == [])

    print("[5] 矩阵解析：8 个 C11 RunID 全部 runnable")
    header, cells = LC.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    c11 = [c for c in cells if c[LC.COL_MODEL].strip() == "C11"]
    check("C11 cell 数 = 8", len(c11) == 8, str(len(c11)))
    for c in c11:
        runid = c[LC.COL_RUNID].strip()
        flags, golden, note = LC.resolve_cell(c)
        ok = (flags is not None and golden
              and "--l1d_target_field" in flags
              and flags[flags.index("--l1d_target_field") + 1] ==
              "mshr_merge"
              and "--l1d_lsu_tier" in flags)
        check(f"{runid} 解析为 mshr_merge 运行配置", ok,
              f"flags={flags} note={note}")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
