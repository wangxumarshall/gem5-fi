#!/usr/bin/env python3
"""test_lsu_hook_p06.py — [MDSPEC][R4-5.4] P06 prefetch-as-demand fill
分类标记模式契约测试.

落地模板（mode_unimpl_plan.md §逐项落地模板）第 4 步：P06（6 RunID，
阻塞短语 "no clean hook: prefetch-as-demand marking"）的注入端模式
（CHAOSPrefetch mode p06_as_demand + maybeMarkFillAsDemand 钩子 @
Cache::serviceMSHRTargets 的 setPrefetched 分类门——gem5 中 demand/
prefetch 分类位的落点）、观测端（inj corr=origin + before/after=
分类对 prefetch->demand + 既有 cache_*/pf_*/resp 链 kind——P06 不新增
kind；blk 注册表整行 + notePrefetchRequest 武装 pf_fill/pf_demand）、
路由（lsu_proxy choices → MODEL_FLAGS → PF_F0_SPAN 跨度表（P06 两条
未实测——本 worktree 禁止跑 pilot，F0 两 cell 大声 BLOCKED）→ 从
MODEL_BLOCKED 删除）与 L0 注入行契约（_INJ_RE 可解析新行格式）逐项
钉死。

与 C11/C12/L04 测试的差异（如实）：本项落地于禁止构建/运行 pilot 的
worktree —— C++ 编译未验证、真机证据 0、PF_F0_SPAN 未实测；本测试钉
死的是源码契约与路由契约，不声称任何运行时行为。

用法：python3 tests/test_lsu_hook_p06.py   （退出码 0=全 PASS）
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
    print("[1] 观测端契约：P06 链复用既有 kind（无新 kind）+ 必录字段")
    chain_kinds = ["inj", "pf_fill", "pf_demand", "cache_access",
                   "mshr_fill", "cache_fill", "mshr_free", "resp",
                   "lq_complete", "taint_reg", "consumer", "errant_commit",
                   "chain_end"]
    for k in chain_kinds:
        check(f"{k} 在 KIND_LAYER 注册", k in P.KIND_LAYER,
              str(P.KIND_LAYER.get(k)))
    check("inj 必录字段 = fault_id+corr（R4-4-review-I1）",
          P.REQUIRED_FIELDS.get("inj") == ["fault_id", "corr"],
          str(P.REQUIRED_FIELDS.get("inj")))
    check("pf_fill/pf_demand 允许 fault_id=0 契约不变（corr 不列必录）",
          "corr" not in P.REQUIRED_FIELDS.get("pf_fill", [])
          and "corr" not in P.REQUIRED_FIELDS.get("pf_demand", []),
          str((P.REQUIRED_FIELDS.get("pf_fill"),
               P.REQUIRED_FIELDS.get("pf_demand"))))
    check("P06 无新 kind（inj/分类值经 before/after 表达，KIND_LAYER 无 "
          "pf_fill_class 事件 kind）",
          "pf_fill_class" not in P.KIND_LAYER,
          str(P.KIND_LAYER.get("pf_fill_class")))

    # 合成 P06 链（真实发射顺序）：inj(fill 分类门击发, corr=origin,
    # before/after=分类对 prefetch->demand——本模型的被故障值) →
    # cache_access(后续重访, L1) → mshr_fill/cache_fill/mshr_free(重取,
    # L2) → pf_fill/pf_demand(标记时分配的 pf_request_id 武装的
    # pf 链节点, L3/L4) → resp/lq_complete/taint_reg(同地址 demand 命中
    # 的 noteMemResponse 缓存臂, L3/L4) → errant_commit(taint_prop) →
    # consumer → chain_end。
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=47008115 va=537536 "
        "before=prefetch after=demand cache_line=537536 "
        "field=pf_fill_class corr=origin",
        "PROP-EVT: kind=cache_access fault_id=1 event_id=1 tick=47010000 "
        "va=537536 pa=537536 corr=addr_fallback",
        "PROP-EVT: kind=mshr_fill fault_id=1 event_id=2 tick=47095000 "
        "cache_line=537536 mshr_id=2 fill_id=4 corr=addr_fallback "
        "state_after=filled",
        "PROP-EVT: kind=cache_fill fault_id=1 event_id=3 tick=47095000 "
        "pa=537536 cache_line=537536 fill_id=4 corr=addr_fallback",
        "PROP-EVT: kind=mshr_free fault_id=1 event_id=4 tick=47095000 "
        "cache_line=537536 mshr_id=2 corr=addr_fallback "
        "state_after=mshr_freed",
        "PROP-EVT: kind=pf_fill fault_id=1 event_id=5 tick=47095000 "
        "pf_request_id=7 pa=537536 cache_line=537536 fill_id=4 "
        "corr=addr_fallback state_after=filled",
        "PROP-EVT: kind=pf_demand fault_id=1 event_id=6 tick=47099500 "
        "pf_request_id=7 dyn_inst_seq=99617 request_id=99617 pa=537536 "
        "field=demand_hit corr=addr_fallback",
        "PROP-EVT: kind=resp fault_id=1 event_id=7 tick=47100000 "
        "dyn_inst_seq=99617 request_id=99617 corr=addr_fallback",
        "PROP-EVT: kind=lq_complete fault_id=1 event_id=8 tick=47100000 "
        "dyn_inst_seq=99617 lq_idx=8051 va=537536 pa=537536 request_id=99617 "
        "corr=addr_fallback",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=9 tick=47100001 "
        "dyn_inst_seq=99617 phys_reg=5 arch_reg=5 corr=addr_fallback",
        "PROP-EVT: kind=consumer fault_id=1 event_id=10 tick=47120000 "
        "dyn_inst_seq=99620 phys_reg=5 arch_reg=5 corr=taint_prop",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=11 tick=47121000 "
        "dyn_inst_seq=99620 corr=taint_prop",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=12 tick=90000000 "
        "outcome=Masked detection_layer=software contained=0 corr=none",
    ]]
    check("合成 P06 链 13 事件全部可解析", len(chain) == 13
          and all(e is not None for e in chain))
    # 逐事件家族契约（REQUIRED_FIELDS 全非空）
    verr = [(e["kind"], f) for e in chain for f in
            P.validate_event(e)]
    check("合成链逐事件 validate_event 无缺字段", not verr, str(verr))
    # R4-4-review-I1：链上每事件 corr 必须非空（pf_fill/pf_demand 的
    # corr 留空是已裁决例外——本合成链两者均带 corr，更严）
    no_corr = [e["kind"] for e in chain if not e.get("corr")]
    check("链上每事件 corr 非空（关联来源显式）", not no_corr, str(no_corr))
    # P06 特有：分类对在流上可读——inj.before/after = 分类值前/后，
    # field 钉死语义（字符串值是 C12 tick 对/L04 seq 对之后的第三种
    # 逐模型被故障值类型）
    inj = chain[0]
    check("inj before/after = 分类对 prefetch->demand（被故障值在案）",
          inj["before"] == "prefetch" and inj["after"] == "demand",
          f"before={inj['before']} after={inj['after']}")
    check("inj field=pf_fill_class（值类型语义钉死）",
          inj["field"] == "pf_fill_class", inj["field"])
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("P06 链 L0→L4 全边 proven → full",
          f1["terminal"] == "full", f1["terminal"])
    check("P06 链 provable_to=L5（chain_end 在案）",
          f1["provable_to"] == "L5", str(f1["provable_to"]))
    check("P06 链 beyond 为空（闭合终局）", f1["beyond"] == "",
          f1["beyond"])

    print("[2] L0 注入行契约（_INJ_RE 可解析的新行格式）")
    inj_line = ("Tick: 47008115, Site: P06_fill_class_mark, "
                "mode=p06_as_demand, old_class=prefetch, new_class=demand, "
                "line=0x833c0, blk_size=64, faults_injected: 1")
    l0 = OBS.parse_l0(
        "CHAOS_LSU_TRIGGER: injector=CHAOSPrefetch tier=F0 attempted=85 "
        "eligible=85 injected=1",
        inj_line)
    check("无 L0 violation（注入行可解析）", not l0["violations"],
          str(l0["violations"]))
    check("漏斗三元组从 stdout 解析",
          (l0["attempted"], l0["eligible"], l0["injected"]) == (85, 85, 1),
          str((l0["attempted"], l0["eligible"], l0["injected"])))
    check("注入明细 mode=p06_as_demand, old/new=prefetch/demand",
          len(l0["injections"]) == 1
          and l0["injections"][0]["mode"] == "p06_as_demand"
          and l0["injections"][0]["old"] == "prefetch"
          and l0["injections"][0]["new"] == "demand",
          str(l0["injections"]))

    print("[3] 注入端源码契约（触发纪律 + 端到端接线）")
    phh = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
              "CHAOSPrefetch.hh")
    pcc = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
              "CHAOSPrefetch.cc")
    ccc = src("CHAOS/gem5/src/mem/cache/cache.cc")
    cpy = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
              "CHAOSPrefetch.py")
    prop_hh = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.hh")
    prop_cc = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.cc")
    check("CHAOSPrefetch.hh 模式枚举含 P06AsDemand + p06_as_demand 映射",
          "P08StrideStuck, P06AsDemand" in phh
          and '"p06_as_demand")          return Mode::P06AsDemand;' in pcc)
    check("CHAOSPrefetch.hh 声明 maybeMarkFillAsDemand + fillMarkHook",
          "maybeMarkFillAsDemand(Addr line, unsigned blk_size," in phh
          and "static CHAOSPrefetch *fillMarkHook;" in phh)
    check("ctor 仅 P06 模式自挂 fillMarkHook（其余运行逐字节不变）",
          "if (fi_mode == Mode::P06AsDemand)\n            fillMarkHook = this;"
          in pcc
          and "if (fillMarkHook == this)\n            fillMarkHook = nullptr;"
          in pcc)
    # P06 的 attempt 流 = fill 钩子：maybeCorrupt 在 P06 模式必须先于
    # onAttempt 返回（双 attempt 流会污染漏斗分母）
    mc = pcc[pcc.index("CHAOSPrefetch::maybeCorrupt"):]
    mc = mc[:mc.index("trigger.onAttempt();")]
    check("maybeCorrupt 在 P06 模式先于 onAttempt 惰性返回（单 attempt 流）",
          "if (fi_mode == Mode::P06AsDemand) return;" in mc)
    mark_fn = pcc[pcc.index("CHAOSPrefetch::maybeMarkFillAsDemand"):]
    mark_fn = mark_fn[:mark_fn.index("\n    }\n\n    void\n"
                                     "    CHAOSPrefetch::logInjection")]
    check("fill 钩子触发语义走 ChaOSLsuTrigger（onAttempt/onEligible）",
          "trigger.onAttempt();" in mark_fn
          and "trigger.onEligible();" in mark_fn)
    # G5 单故障 cap 在 onAttempt 之前（C11 惯例：fire 后 attempted 冻结）
    cap_pos = mark_fn.index("faults_injected >= max_faults")
    att_pos = mark_fn.index("trigger.onAttempt();")
    check("G5 cap 检查先于 onAttempt（C11 惯例，fire 后冻结）",
          cap_pos < att_pos)
    # 资格门：分类位必须"活着"——demand 已并入的 fill 与无 blk 的 fill
    # 不可标（void 值不是合法候选）
    check("资格门拒绝 demand_merged 与无 blk（分类位不活的 void 标记）",
          "if (demand_merged || !blk_valid) return false;" in mark_fn)
    # F6 记账（R4-5.1-review-I1 约束的镜像面）：钩子内走 f6_pending 消费，
    # 不调 onF6Event —— onF6Event 留在 thunk 站点（默认 true 正确）
    check("F6 臂 = f6_pending 消费（P 家族 P01-P08 同形）",
          "go = f6_pending;" in mark_fn and "f6_pending = false;" in mark_fn)
    check("fill 钩子内无 onF6Event 调用（无双计可能；thunk 站点记账）",
          "onF6Event(" not in mark_fn)
    check("fill 钩子无手搓概率检查",
          "uniform_real_distribution" not in mark_fn
          and "uniform_int_distribution" not in mark_fn
          and "rng() %" not in mark_fn)
    check("注册链：registerPfFillClassFault + notePrefetchRequest（pf 链武装）",
          "registerPfFillClassFault(line, blk_size)" in mark_fn
          and "notePrefetchRequest(line, blk_size)" in mark_fn)
    check("注入行 _INJ_RE 契约（Site/mode/old_class/new_class）",
          ", Site: P06_fill_class_mark, mode=p06_as_demand" in mark_fn
          and "old_class=prefetch, new_class=demand" in mark_fn)
    # cache.cc 端到端接线：门位 + 原语义保持
    check("cache.cc include CHAOSPrefetch.hh",
          '#include "mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.hh"'
          in ccc)
    check("cache.cc 分类门咨询 fillMarkHook（from_pref 全量 attempt 面）",
          "from_pref && CHAOSPrefetch::fillMarkHook" in ccc
          and "maybeMarkFillAsDemand(" in ccc
          and "mshr->blkAddr, blkSize, from_core, blk != nullptr" in ccc)
    check("setPrefetched 门保持原条件 + 标记臂（!p06_demand_marked）",
          "from_pref && !p06_demand_marked" in ccc
          and "blk->setPrefetched();" in ccc)
    gate = ccc[ccc.index("bool p06_demand_marked = false;"):]
    gate = gate[:gate.index("blk->setPrefetched();")]
    check("门位在 serviceMSHRTargets（from_pref 分类门原址）",
          "p06_demand_marked" in gate)
    # 传播注册端
    check("CHAOSPropagation 提供 registerPfFillClassFault",
          "registerPfFillClassFault" in prop_hh
          and "CHAOSPropagation::registerPfFillClassFault" in prop_cc)
    reg = prop_cc[prop_cc.index(
        "CHAOSPropagation::registerPfFillClassFault"):]
    reg = reg[:reg.index("\n    }")]
    check("inj before/after = 分类对（字符串被故障值入统一流）",
          '";before=prefetch"' in reg and '";after=demand"' in reg)
    check("field=pf_fill_class + family=prefetch",
          '"family=prefetch;field=pf_fill_class"' in reg)
    check("整行入 blk 注册表（后续事件按重叠入链，addr_fallback 臂）",
          "blk_registry[b.byte_begin] = b;" in reg)
    check("corr=origin（链开启注册）", "CORR_ORIGIN" in reg)
    # CHAOSPrefetch.py 参数面
    check("CHAOSPrefetch.py 文档面（p06_as_demand 模式 + 诚实边界改名）",
          "p06_as_demand" in cpy
          and "P06-b/c/d" in cpy)

    print("[4] 路由契约（lsu_proxy → MODEL_FLAGS → PF_F0_SPAN → 解阻塞）")
    proxy = src("configs/se/lsu_proxy.py")
    check("lsu_proxy --prefetch_mode choices 含 p06_as_demand",
          '"p06_as_demand"' in proxy
          and "p08_stride_stuck" in proxy)
    check("MODEL_FLAGS 注册 P06",
          LC.MODEL_FLAGS.get("P06") ==
          ("prefetch", ["--prefetch_mode", "p06_as_demand"]),
          str(LC.MODEL_FLAGS.get("P06")))
    check("P06 已从 MODEL_BLOCKED 删除",
          "P06" not in LC.MODEL_BLOCKED)
    # [R4-8-INT] 本守卫的原意是"后续模型不得**误解锁**"（撰写时 C14/C15/S10/A06
    # 都还 BLOCKED）。但把这份名单**硬编码为"必须仍 BLOCKED"**会让守卫在合法
    # 推进发生时变成"禁止解锁"——C14/C15 于 R4-5.5/5.6 按 C11/C12/L04 纪律
    # （真机 pilot + 链检查 + 证据重生成）合法解锁后，本行即已 FAIL（**先于本轮**，
    # 见 test_lsu_hook_p06.py 自 R4-5.5 起 rc=1）；本轮 S10 又按同一纪律解锁
    # （activated=3/3 + L0→L1 逐边 proven，见 round4_findings.md §R4-8-S10）。
    # 改为**按证据**断言，既不放过误解锁，也不惩罚合法推进：
    #   * 尚未拿到真机证据的 A06 必须仍在 MODEL_BLOCKED；
    #   * 已解锁的三个必须确实不在表里（其 span 表/路由由各自的 hook 测试钉住）。
    check("后续模型未误解锁（A06 仍 BLOCKED；C14/C15/S10 按纪律解锁）",
          "A06" in LC.MODEL_BLOCKED
          and all(m not in LC.MODEL_BLOCKED for m in ("C14", "C15", "S10")))
    # [R4-5.4 集成] 本文件撰写于隔离 worktree（禁跑 pilot），当时两个 (P06, workload)
    # 跨度**未实测**，故断言"表存在但条目缺席 + loud None"。集成期主 worktree 已用
    # 普查实测（cache_dirtyevict=56、prefetch_stride=32；见 round4_findings.md §R4-5.4），
    # 断言随之翻转为"**已实测**且按对取值 + 逐对生效"，同时保留"未实测对仍 loud 拒绝"
    # 这条**机制**断言（用一个刻意未实测的负载名验证），以免丢失该纪律的回归网。
    check("PF_F0_SPAN 表存在且 P06 两条已实测（集成期普查）",
          isinstance(LC.PF_F0_SPAN, dict)
          and LC.PF_F0_SPAN.get(("P06", "cache_dirtyevict")) == 56
          and LC.PF_F0_SPAN.get(("P06", "prefetch_stride")) == 32,
          str(LC.PF_F0_SPAN))
    check("已实测 (P06, workload) F0 逐对生效（span=实测值, warmup=1）",
          LC._prefetch_tier_flags("P06", "F0", "cache_dirtyevict") ==
          ["--prefetch_lsu_tier", "F0", "--prefetch_warmup_events", "1",
           "--prefetch_span_events", "56"]
          and LC._prefetch_tier_flags("P06", "F0", "prefetch_stride") ==
          ["--prefetch_lsu_tier", "F0", "--prefetch_warmup_events", "1",
           "--prefetch_span_events", "32"],
          str(LC._prefetch_tier_flags("P06", "F0", "cache_dirtyevict")))
    check("未实测 (P06, workload) F0 仍 loud 拒绝（机制未丢）",
          LC._prefetch_tier_flags("P06", "F0", "no_such_workload") is None)
    check("P06 F2/F6 tier flags 解析（legacy 形，span 惰性）",
          LC._prefetch_tier_flags("P06", "F2", "cache_dirtyevict") ==
          ["--prefetch_lsu_tier", "F2", "--prefetch_warmup_events", "0",
           "--prefetch_span_events", "50"]
          and LC._prefetch_tier_flags("P06", "F6", "prefetch_stride") ==
          ["--prefetch_lsu_tier", "F6", "--prefetch_warmup_events", "0",
           "--prefetch_span_events", "50"],
          str(LC._prefetch_tier_flags("P06", "F2", "cache_dirtyevict")))
    check("P01-P08 tier flags 逐字节不变（F0/F2 同旧 lambda）",
          LC._prefetch_tier_flags("P01", "F0", "prefetch_stride") ==
          ["--prefetch_lsu_tier", "F0", "--prefetch_warmup_events", "0",
           "--prefetch_span_events", "50"]
          and LC._prefetch_tier_flags("P08", "F2", "prefetch_stride") ==
          ["--prefetch_lsu_tier", "F2", "--prefetch_warmup_events", "0",
           "--prefetch_span_events", "50"],
          str(LC._prefetch_tier_flags("P01", "F0", "prefetch_stride")))
    check("C11/C12/L04 既有 tier flags 不受影响（跨度表原样）",
          LC._cache_tier_flags("C11", "F0", "cache_dirtyevict") ==
          ["--l1d_lsu_tier", "F0", "--l1d_warmup_events", "1",
           "--l1d_span_events",
           str(LC.CACHE_F0_SPAN[("C11", "cache_dirtyevict")])]
          and LC._lsqfwd_tier_flags("L04", "F0", "sq_forward") ==
          ["--lsqfwd_lsu_tier", "F0", "--lsqfwd_warmup_events", "1",
           "--lsqfwd_span_events", "324"])

    print("[5] 矩阵解析：6 个 P06 RunID（F0 已实测 → 可解析 / F2·F6 可解析）")
    header, cells = LC.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    p06 = [c for c in cells if c[LC.COL_MODEL].strip() == "P06"]
    check("P06 cell 数 = 6", len(p06) == 6, str(len(p06)))
    for c in p06:
        runid = c[LC.COL_RUNID].strip()
        tier = c[LC.COL_FREQ].strip()
        flags, golden, note = LC.resolve_cell(c)
        if tier == "F0":
            # [R4-5.4 集成] 集成期已普查两条跨度，F0 cell 不再阻塞；断言翻转为
            # "解析成功且 span = 该负载的实测值"（值来自 PF_F0_SPAN，非硬编码常量）。
            wl = c[LC.COL_WORKLOAD].strip()
            wl_bin = next((b for k, b in LC.WL_BINARY.items() if k in wl), None)
            want = LC.PF_F0_SPAN.get(("P06", wl_bin))
            # 注意 flags 里 `--prefetch_span_events` **出现两次**（家族基础
            # mount 给 1，tier lambda 给实测跨度）；argparse **last-wins**，
            # 故生效值 = 最后一次出现，必须按 rindex 取（同 C11/C12 的
            # FAMILY_TIER_FLAGS 先例）。
            ok = (flags is not None and golden and want is not None
                  and "--prefetch_lsu_tier" in flags
                  and flags[len(flags) - 1 - flags[::-1].index(
                      "--prefetch_lsu_tier") + 1] == "F0"
                  and flags[len(flags) - 1 - flags[::-1].index(
                      "--prefetch_span_events") + 1] == str(want))
            check(f"{runid} F0 已实测跨度 → 解析运行配置（span={want}）",
                  ok, f"flags={flags} note={note}")
        else:
            ok = (flags is not None and golden
                  and flags[flags.index("--prefetch_mode") + 1] ==
                  "p06_as_demand"
                  and "--prefetch_lsu_tier" in flags
                  and flags[flags.index("--prefetch_lsu_tier") + 1] == tier)
            check(f"{runid} {tier} 解析为 p06_as_demand 运行配置", ok,
                  f"flags={flags} note={note}")

    print("[6] SPEC_IMPL_LANDED 登记（landed/pending 机器可读 + 诚实证据状态）")
    # SPEC_IMPL_LANDED 是 generate_map() 的局部 dict —— 源码 pin（L04 测试
    # 同形）；runid_map.json 的再生成属集成方（本 worktree 不得改产物）。
    # 换行折叠后匹配（字符串跨行拼接不断词）。
    runid_map_py = src("tools/lsu_runid_map.py")
    flat = " ".join(runid_map_py.split())
    # 字符串跨行拼接的引号续行（" ... " " ... "）去引号+再折叠后匹配
    nq = " ".join(flat.replace('"', '').split())
    check("SPEC_IMPL_LANDED P06 落地登记（机器可读 landed/pending，源码 pin）",
          '"P06": "implemented(pf_fill_class=P06-a forward arm' in flat
          and "pending: P06-a " in flat)
    check("未落地子模型逐一点名（反向臂 + P06-b/c/d）",
          all(s in nq for s in
              ("P06-a reverse arm (demand marked prefetch)",
               "P06-b dirty attribute",
               "P06-c ownership attribute",
               "P06-d allocate attribute")),
          "grep tools/lsu_runid_map.py P06 段")
    check("证据状态如实（compile-unverified + 零真机样本 + 跨度未实测）",
          "compile-unverified" in nq
          and "NONE YET" in nq
          and "PF_F0_SPAN" in nq,
          "P06 证据状态段")
    check("C11/C12/L04 登记仍在（不覆盖）",
          all(f'"{m}": "implemented(' in flat
              for m in ("C11", "C12", "L04")))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
