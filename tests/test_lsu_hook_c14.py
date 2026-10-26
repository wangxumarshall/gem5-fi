#!/usr/bin/env python3
"""[MDSPEC][R4-5.5] C14-a MSHR busy/occupied stuck-at-1 契约测试.

落地模板（mode_unimpl_plan.md §逐项落地模板）第 4 步：C14（2 RunID，
阻塞短语 "consumer-side: MSHR busy event source only"，子模型 C14-a）的
注入端模式（targetField=mshr_busy_leak + BaseCache::recvTimingResp 的 MSHR
释放点钩子——同意后**跳过 deallocate**）、观测端（新 kind mshr_busy(L2) +
既有 mshr_* 链；inj corr=origin，before/after=占用对）、路由
（lsu_proxy choices → MODEL_FLAGS → CACHE_F0_SPAN 故意缺席 + census 命令）
与 L0 注入行契约逐项钉死。

用法：python3 tests/test_lsu_hook_c14.py   （退出码 0=全 PASS）
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
    print("[1] 观测端契约：新 kind mshr_busy(L2) + 必录字段")
    check("mshr_busy 在 KIND_LAYER 注册且层级 L2",
          P.KIND_LAYER.get("mshr_busy") == "L2",
          str(P.KIND_LAYER.get("mshr_busy")))
    req = P.REQUIRED_FIELDS.get("mshr_busy", [])
    check("mshr_busy 必录字段（fault_id/corr/mshr_id/entry_index/"
          "cache_line/field/state_before/state_after）",
          req == ["fault_id", "corr", "mshr_id", "entry_index",
                  "cache_line", "field", "state_before", "state_after"],
          str(req))
    check("既有 C-链 kind 未被改动（mshr_alloc/merge/fill/free 仍在）",
          all(k in P.KIND_LAYER for k in
              ("inj", "mshr_alloc", "mshr_merge", "mshr_fill", "mshr_free",
               "cache_access", "resp", "taint_reg", "chain_end")))
    check("inj 必录字段 = fault_id+corr（R4-4-review-I1 未变）",
          P.REQUIRED_FIELDS.get("inj") == ["fault_id", "corr"],
          str(P.REQUIRED_FIELDS.get("inj")))

    # 合成 C14 链（真实发射顺序）：inj(释放点捕获，corr=origin,
    # before/after=占用对) → mshr_busy(卡死状态, L2) → 后续重访同 line 的
    # mshr_alloc（被卡死的表项令同 line 请求无响应 → 诚实 Unknown）→
    # chain_end。此外给出一个"恢复"形态：卡死槽位令队列满 → CPU 阻塞 →
    # 最终 Timeout（chain_end outcome=Timeout）。
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=42946750 va=79280 "
        "before=5 after=6 cache_line=79280 field=mshr_busy_leak corr=origin",
        "PROP-EVT: kind=cache_access fault_id=1 event_id=1 tick=42946760 "
        "va=79280 pa=79280 corr=addr_fallback",
        "PROP-EVT: kind=mshr_busy fault_id=1 event_id=2 tick=42946770 "
        "cache_line=79280 mshr_id=7 entry_index=7 field=busy "
        "state_before=should_release state_after=stuck_busy corr=origin",
        "PROP-EVT: kind=resp fault_id=1 event_id=3 tick=42961520 "
        "dyn_inst_seq=42 request_id=42 corr=addr_fallback",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=4 tick=42961521 "
        "dyn_inst_seq=42 phys_reg=5 arch_reg=5 corr=addr_fallback",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=5 tick=42963100 "
        "dyn_inst_seq=42 corr=taint_prop",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=6 tick=90000000 "
        "outcome=Timeout detection_layer=none contained=0 corr=none",
    ]]
    check("合成 C14 链 7 事件全部可解析", len(chain) == 7
          and all(e is not None for e in chain))
    no_corr = [e["kind"] for e in chain if not e.get("corr")]
    check("链上每事件 corr 非空（关联来源显式）", not no_corr, str(no_corr))
    inj = chain[0]
    check("inj before/after = 占用对（correct vs stuck，before<after）",
          int(inj["before"]) == 5 and int(inj["after"]) == 6,
          f"before={inj['before']} after={inj['after']}")
    busy = next(e for e in chain if e["kind"] == "mshr_busy")
    check("mshr_busy 事件带 mshr_id/entry_index（槽位身份）",
          busy["mshr_id"] == "7" and busy["entry_index"] == "7",
          f"mshr_id={busy['mshr_id']} entry_index={busy['entry_index']}")
    check("mshr_busy state_before/after = should_release→stuck_busy",
          busy["state_before"] == "should_release"
          and busy["state_after"] == "stuck_busy",
          f"{busy['state_before']}->{busy['state_after']}")
    check("每事件过 validate_event（无缺键）",
          all(not P.validate_event(e) for e in chain),
          str([P.validate_event(e) for e in chain]))
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("C14 链 provable_to=L5（chain_end 在案）",
          f1["provable_to"] == "L5", str(f1["provable_to"]))
    check("C14 链 terminal=full（合成链全边 proven）",
          f1["terminal"] == "full", f1["terminal"])
    # 缺 mshr_busy 节点 → mshr_busy 观察不在场（诚实缺席，不臆造）
    v2 = CC.check_chain([e for e in chain if e["kind"] != "mshr_busy"])
    check("去掉 mshr_busy 节点后链在 L2 前截断（节点确为 C14 特有）",
          v2["faults"]["1"]["provable_to"] in ("L0", "L1"),
          str(v2["faults"]["1"]["provable_to"]))

    print("[2] L0 注入行契约（cache_injections.log 实际格式）")
    inj_line = ("Tick: 42946750, Cache Block Addr: 79280, "
                "Field: mshr_busy_leak (C14-a occupied-stuck-at-1 "
                "release-skipped), in_service_before=5, "
                "in_service_after=6, was_full=0, faults_injected: 1")
    l0 = OBS.parse_l0(
        "CHAOS_LSU_TRIGGER: injector=CHAOSCache tier=F5 attempted=4200 "
        "eligible=1 injected=1",
        inj_line + "\n" +
        "FUNNEL: attempted=4200 eligible=1 injected=1")
    check("无 L0 violation（注入行可解析）", not l0["violations"],
          str(l0["violations"]))
    check("漏斗四元组从 stdout 解析",
          (l0["attempted"], l0["eligible"], l0["injected"]) == (4200, 1, 1),
          str((l0["attempted"], l0["eligible"], l0["injected"])))
    check("注入明细 mode=field:mshr_busy_leak…",
          len(l0["injections"]) == 1
          and l0["injections"][0]["mode"].startswith(
              "field:mshr_busy_leak"),
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
    trig_hh = src("CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh")
    check("base.hh 声明 chaosMshrBusyHook",
          "static class CHAOSCache *chaosMshrBusyHook;" in bhh)
    check("base.cc 定义 chaosMshrBusyHook = nullptr",
          "CHAOSCache *BaseCache::chaosMshrBusyHook = nullptr;" in bcc)
    check("base.cc 在释放点咨询 maybeStickMshrBusy（deallocate 之前）",
          "chaosMshrBusyHook->maybeStickMshrBusy(" in bcc)
    # 顺序契约：leak 判定必须早于 mshrQueue.deallocate(mshr)
    resp_region = bcc[bcc.index("const bool mshr_leaked"):]
    resp_region = resp_region[:resp_region.index("const Tick forward_time")]
    check("leaked 为真时跳过 deallocate（if (!mshr_leaked)）",
          "if (!mshr_leaked) {" in resp_region
          and "mshrQueue.deallocate(mshr);" in resp_region
          and "clearBlocked(Blocked_NoMSHRs);" in resp_region)
    check("CHAOSCache.hh 声明 maybeStickMshrBusy + 单槽成员",
          "maybeStickMshrBusy(BaseCache" in chh
          and "MSHR *mshr_busy_victim = nullptr;" in chh
          and "uint64_t mshr_busy_leaks = 0;" in chh)
    check("CHAOSPropagation 提供 registerMshrBusyFault（声明+定义）",
          "registerMshrBusyFault" in prop_hh and
          "CHAOSPropagation::registerMshrBusyFault" in prop_cc)
    check("inj before/after = 占用对（入统一流）",
          '<< ";before=" << occ_before' in prop_cc
          and '<< ";after=" << occ_after' in prop_cc)
    check("mshr_busy 节点发射（state_before/state_after/field=busy）",
          'notePropEvt("mshr_busy"' in prop_cc
          and '{"state_before", "should_release"}' in prop_cc
          and '{"state_after", "stuck_busy"}' in prop_cc
          and '{"field", "busy"}' in prop_cc)
    check("整行入 blk 注册表（同 line 事件按重叠入链）",
          "blk_registry[b.byte_begin] = b;" in prop_cc)

    ctor = chk[:chk.index("CHAOSCache::CHAOSCacheStats")]
    check("mshr_busy_leak 模式拒绝 lsuTier=off（大声失败，不静默）",
          'mshr_busy_mode' in ctor and 'p.lsuTier == "off"' in ctor
          and "panic" in ctor)
    check("hook 模式禁用 legacy 周期攻击（lsu_hook_mode 门）",
          "const bool lsu_hook_mode" in ctor
          and "if (!lsu_hook_mode)" in ctor)
    check("注册 BaseCache::chaosMshrBusyHook = this",
          "BaseCache::chaosMshrBusyHook = this;" in ctor)
    check("legacy/victim/merge/fill 路径回归不变",
          "chaosVictimHook = this" in chk
          and "BaseCache::chaosMergeHook = this" in chk
          and "BaseCache::chaosFillTimingHook = this" in chk)

    leak_fn = chk[chk.index("CHAOSCache::maybeStickMshrBusy"):]
    leak_fn = leak_fn[:leak_fn.index("\n    }")]
    check("触发语义走 ChaOSLsuTrigger（onAttempt/onEligible/onF6Event）",
          "onAttempt()" in leak_fn and "onEligible()" in leak_fn
          and "onF6Event(false)" in leak_fn)
    check("F6 事件门不重复计 attempted（onF6Event(false)，review-I1）",
          "lsuTrigger->onF6Event(false);" in leak_fn
          and leak_fn.count("lsuTrigger->onAttempt();") == 1)
    check("泄露函数无手搓概率检查",
          "uniform_real_distribution" not in leak_fn
          and "uniform_int_distribution" not in leak_fn)
    check("单槽守卫（已有泄露时结构性拒绝第二次）",
          "if (mshr_busy_victim) return false;" in leak_fn)
    check("G5 maxFaults 上限（faults_injected_count）",
          "max_faults != 0 && faults_injected_count >= max_faults" in leak_fn)
    check("因模式关/挂载缓存/空指针提前返回（zero regression）",
          'if (target_field != "mshr_busy_leak") return false;' in leak_fn
          and "if (cache != targetCache) return false;" in leak_fn
          and "if (!mshr || !lsuTrigger) return false;" in leak_fn)
    check("第九 F6 事件源（MSHR 完成并应释放）已在 trigger 头文件登记",
          "NINTH source" in trig_hh and "mshr_busy_leak" in trig_hh)
    check("CHAOSCache.py 参数面（targetField 文档含 mshr_busy_leak）",
          "mshr_busy_leak" in cpy)

    print("[4] 路由契约（lsu_proxy → MODEL_FLAGS → F0 跨度 → 解阻塞）")
    proxy = src("configs/se/lsu_proxy.py")
    check("lsu_proxy --l1d_target_field 含 mshr_busy_leak",
          '"mshr_busy_leak"' in proxy)
    check("lsu_proxy --l1d_lsu_tier help 点名 C14",
          "C14" in proxy and "mshr_busy_leak" in proxy)
    check("MODEL_FLAGS 注册 C14（mshr_busy_leak）",
          LC.MODEL_FLAGS.get("C14") ==
          ("cache", ["--l1d_target_field", "mshr_busy_leak"]),
          str(LC.MODEL_FLAGS.get("C14")))
    check("C14 已从 MODEL_BLOCKED 删除（实测可跑后才允许，C11/C12/L04 纪律）",
          "C14" not in LC.MODEL_BLOCKED,
          str(LC.MODEL_BLOCKED.get("C14")))
    check("后续模型未误解锁（C11/C12 已解锁；C15 状态由其自身集成裁决）",
          "C11" not in LC.MODEL_BLOCKED
          and "C12" not in LC.MODEL_BLOCKED)
    check("CACHE_F0_SPAN 无 C14 条目（C14 无 F0 cell，故跨度表本就不需要它）",
          ("C14", "cache_dirtyevict") not in LC.CACHE_F0_SPAN
          and ("C14", "stream_chase") not in LC.CACHE_F0_SPAN)
    check("CACHE_F0_SPAN 注释含 C14/C15 census 命令",
          "C14-SPAN-" in src("tools/lsu_campaign.py")
          and "mshr_busy_leak" in src("tools/lsu_campaign.py"))
    check("C14 F5 tier flags（inert span，lsqfwd 约定）",
          LC._cache_tier_flags("C14", "F5", "cache_dirtyevict") ==
          ["--l1d_lsu_tier", "F5", "--l1d_warmup_events", "0",
           "--l1d_span_events", "1000"],
          str(LC._cache_tier_flags("C14", "F5", "cache_dirtyevict")))
    check("C14 无 F0 cell：F0 路径对该模型仍 loud None（拒绝静默复用）",
          LC._cache_tier_flags("C14", "F0", "cache_dirtyevict") is None)
    check("legacy cache 模型 tier flags 逐字节不变（[]）",
          LC._cache_tier_flags("C01", "F0", "cache_dirtyevict") == []
          and LC._cache_tier_flags("C09", "F2", "stream_chase") == [])
    check("C11/C12 tier flags 不受 C14 落地影响（逐字节不变）",
          LC._cache_tier_flags("C11", "F0", "cache_dirtyevict") ==
          ["--l1d_lsu_tier", "F0", "--l1d_warmup_events", "1",
           "--l1d_span_events",
           str(LC.CACHE_F0_SPAN[("C11", "cache_dirtyevict")])]
          and LC._cache_tier_flags("C12", "F0", "stream_chase") ==
          ["--l1d_lsu_tier", "F0", "--l1d_warmup_events", "1",
           "--l1d_span_events",
           str(LC.CACHE_F0_SPAN[("C12", "stream_chase")])])

    print("[5] 矩阵解析：C14 2 RunID 解析为 mshr_busy_leak 运行配置"
          "（已集成解锁）")
    header, cells = LC.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    c14 = [c for c in cells if c[LC.COL_MODEL].strip() == "C14"]
    check("C14 cell 数 = 2", len(c14) == 2, str(len(c14)))
    for c in c14:
        runid = c[LC.COL_RUNID].strip()
        flags, golden, note = LC.resolve_cell(c)
    for c in c14:
        runid = c[LC.COL_RUNID].strip()
        flags, golden, note = LC.resolve_cell(c)
        ok = (flags is not None and golden
              and "--l1d_target_field" in flags
              and flags[flags.index("--l1d_target_field") + 1] ==
              "mshr_busy_leak"
              and "--l1d_lsu_tier" in flags)
        check(f"{runid} 解析为 mshr_busy_leak 运行配置（已集成解锁）", ok,
              f"flags={flags} note={note}")

    print("[6] SPEC_IMPL_LANDED 诚实登记")
    rm = src("tools/lsu_runid_map.py")
    check("SPEC_IMPL_LANDED 含 C14 条目", '"C14": "implemented(' in rm)
    check("C14 条目写明 compile-unverified / 无真机证据",
          "C14" in rm and "compile-unverified" in rm
          and "no census" in rm)

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
