#!/usr/bin/env python3
"""test_lsu_hook_a07.py — [MDSPEC][R4-5.8] A07 AGU clean-ready/握手模式契约测试.

落地模板（mode_unimpl_plan.md §逐项落地模板）第 4 步：A07（6 RunID，
阻塞短语 "R4: no clean hook"）的注入端（IEW::executeInsts isMemRef 分支
= AGU clean-ready/握手点 + CHAOSAddrPath agu_ready_mode=a07b_ready_delay
有界 ready 延迟 + aguResumeEvent 延迟拍再入）、观测端（inj corr=origin
+ before/after = ready tick 前/后（时序故障的被故障值，C12 交付 tick 对
先例）+ 既有 lsq_push/lsq_sendfrag/tlb_translate/lq_read/resp/
lq_complete/taint_reg 链 kind——A07 不新增 kind；EA 晚绑定：延迟指令 EA
进入 LSQ 时绑真实地址区间，下游按 seq+overlap 入链）、路由（lsu_proxy
choices+互斥校验 → MODEL_FLAGS A07 → ADDRPATH_F0_SPAN 跨度表（本会话
禁止跑 census，A07 两对条目**故意缺席** → A07-F0 loud refusal；A07 保持
MODEL_BLOCKED：compile-unverified + 无 pilot，集成侧 build+census+pilot
通过后才删——C11/C12/L04 纪律））与 L0 注入行契约逐项钉死。

用法：python3 tests/test_lsu_hook_a07.py   （退出码 0=全 PASS）
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
    print("[1] 观测端契约：A07 链复用既有 kind（无新 kind）+ 必录字段")
    chain_kinds = ["inj", "lsq_push", "lsq_sendfrag", "tlb_translate",
                   "lq_read", "resp", "lq_complete", "taint_reg",
                   "consumer", "errant_commit", "chain_end"]
    for k in chain_kinds:
        check(f"{k} 在 KIND_LAYER 注册", k in P.KIND_LAYER,
              str(P.KIND_LAYER.get(k)))
    check("inj 必录字段 = fault_id+corr（R4-4-review-I1）",
          P.REQUIRED_FIELDS.get("inj") == ["fault_id", "corr"],
          str(P.REQUIRED_FIELDS.get("inj")))
    check("A07 无新 kind（inj 的 field=agu_ready_delay 是值不是 kind；"
          "KIND_LAYER 无 agu_ready_delay 事件 kind）",
          "agu_ready_delay" not in P.KIND_LAYER,
          str(P.KIND_LAYER.get("agu_ready_delay")))
    check("lsq_push 必录字段含 corr（A07 入链臂标注）",
          "corr" in P.REQUIRED_FIELDS.get("lsq_push", []),
          str(P.REQUIRED_FIELDS.get("lsq_push")))

    # 合成 A07-b 负载链（真实发射顺序）：inj(ready 延迟, corr=origin,
    # before/after=ready tick 前/后, dyn_inst_seq=被延迟指令) → lsq_push
    # (EA/size/flags 进入 LSQRequest——在**延迟后**的 tick, L1,
    # corr=seq_primary, seq+overlap 晚绑定入链) → lsq_sendfrag/
    # tlb_translate(L2) → lq_read(L3) → resp/lq_complete(延迟后响应,
    # L3) → taint_reg(L4) → consumer/errant_commit(taint_prop) →
    # chain_end。数据载荷保持正确（时序故障，spec 03 A07）——oracle 预期
    # Masked 类结局由真机 pilot 裁决（本会话禁止运行，不虚构）。
    T0, T1 = 5920530, 5920915   # delay=1 CPU cycle @385 ticks/cycle
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=%d dyn_inst_seq=3998 "
        "before=%d after=%d field=agu_ready_delay corr=origin" % (T0, T0, T1),
        "PROP-EVT: kind=lsq_push fault_id=1 event_id=1 tick=%d "
        "dyn_inst_seq=3998 pc=402b18 opcode=ldr lq_idx=657 sq_idx=-1 "
        "va=4903e8 field=load corr=seq_primary" % T1,
        "PROP-EVT: kind=lsq_sendfrag fault_id=1 event_id=2 tick=%d "
        "dyn_inst_seq=3998 pc=402b18 opcode=ldr request_id=3998 va=4903e8 "
        "corr=seq_primary" % T1,
        "PROP-EVT: kind=tlb_translate fault_id=1 event_id=3 tick=%d "
        "dyn_inst_seq=3998 va=4903e8 request_id=3998 corr=seq_primary" % T1,
        "PROP-EVT: kind=lq_read fault_id=1 event_id=4 tick=%d "
        "dyn_inst_seq=3998 lq_idx=657 va=4903e8 corr=seq_primary" % T1,
        "PROP-EVT: kind=resp fault_id=1 event_id=5 tick=%d dyn_inst_seq=3998 "
        "corr=seq_primary" % (T1 + 770),
        "PROP-EVT: kind=lq_complete fault_id=1 event_id=6 tick=%d "
        "dyn_inst_seq=3998 lq_idx=657 va=4903e8 pa=7503e8 request_id=3998 "
        "corr=seq_primary" % (T1 + 770),
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=7 tick=%d "
        "dyn_inst_seq=3998 phys_reg=212 arch_reg=5 corr=seq_primary"
        % (T1 + 771),
        "PROP-EVT: kind=consumer fault_id=1 event_id=8 tick=%d "
        "dyn_inst_seq=4012 phys_reg=212 arch_reg=5 corr=taint_prop"
        % (T1 + 1540),
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=9 tick=%d "
        "dyn_inst_seq=4012 corr=taint_prop" % (T1 + 1541),
        "PROP-EVT: kind=chain_end fault_id=1 event_id=10 tick=90000000 "
        "outcome=Masked detection_layer=software contained=0 corr=none",
    ]]
    check("合成 A07 链 11 事件全部可解析", len(chain) == 11
          and all(e is not None for e in chain))
    # 每事件过家族契约（REQUIRED_FIELDS 非空）
    verrs = []
    for e in chain:
        verrs += P.validate_event(e)
    check("合成链逐事件过 validate_event（必录字段）", not verrs, str(verrs))
    # R4-4-review-I1：链上每事件 corr 必须非空
    no_corr = [e["kind"] for e in chain if not e.get("corr")]
    check("链上每事件 corr 非空（关联来源显式）", not no_corr, str(no_corr))
    # A07 特有：时序对在案——inj.before/after = ready tick 前/后，且被
    # 延迟指令的 lsq_push 落在延迟后窗口（>= inj.after）
    inj = chain[0]
    push = next(e for e in chain if e["kind"] == "lsq_push")
    check("inj before/after = ready tick 前/后（时序对在案）",
          int(inj["before"]) < int(inj["after"]),
          f"before={inj['before']} after={inj['after']}")
    check("inj.after - inj.before = 有界延迟（1 CPU cycle @385 ticks）",
          int(inj["after"]) - int(inj["before"]) == 385,
          str(int(inj["after"]) - int(inj["before"])))
    check("lsq_push.tick 落在延迟后窗口（>= inj.after）",
          int(push["tick"]) >= int(inj["after"]),
          f"push.tick={push['tick']} inj.after={inj['after']}")
    check("被延迟指令身份贯穿（inj.dyn_inst_seq == lsq_push.dyn_inst_seq）",
          inj["dyn_inst_seq"] == push["dyn_inst_seq"] == "3998")
    v = CC.check_chain(chain, oracle_outcome="Masked")
    f1 = v["faults"]["1"]
    check("A07 链 L0→L4 全边 proven → full（chain_end 在案）",
          f1["terminal"] == "full", f1["terminal"])
    check("A07 链 provable_to=L5",
          f1["provable_to"] == "L5", str(f1["provable_to"]))

    print("[2] L0 注入行契约（addrpath_injections.log 实际格式）")
    inj_line = ("Tick: %d, Site: iew_memRef_AGU_ready, "
                "mode=a07b_ready_delay, dyn_inst_seq=3998, "
                "ready_tick=%d, delayed_tick=%d, delay_cycles=1, "
                "isLoad=1, isStore=0, faults_injected: 1" % (T0, T0, T1))
    fun_line = "FUNNEL: attempted=2582 eligible=1307 injected=1"
    l0 = OBS.parse_l0(
        "CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=2582 "
        "eligible=1307 injected=1",
        inj_line + "\n" + fun_line)
    check("无 L0 violation（注入行可解析）", not l0["violations"],
          str(l0["violations"]))
    check("漏斗四元组从 stdout 解析",
          (l0["attempted"], l0["eligible"], l0["injected"]) ==
          (2582, 1307, 1),
          str((l0["attempted"], l0["eligible"], l0["injected"])))
    check("注入明细 mode=a07b_ready_delay（Site=ready 点）",
          len(l0["injections"]) == 1
          and l0["injections"][0]["mode"] == "a07b_ready_delay",
          str(l0["injections"]))

    print("[3] 注入端源码契约（触发纪律 + 端到端接线 + ready 点）")
    iew_cc = src("CHAOS/gem5/src/cpu/o3/iew.cc")
    iew_hh = src("CHAOS/gem5/src/cpu/o3/iew.hh")
    cpu_hh = src("CHAOS/gem5/src/cpu/o3/cpu.hh")
    ap_cc = src("CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc")
    ap_hh = src("CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh")
    ap_py = src("CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.py")
    lsq_cc = src("CHAOS/gem5/src/cpu/o3/lsq.cc")
    prop_hh = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.hh")
    prop_cc = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.cc")
    trig_hh = src("CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh")

    # ready/handshake 点选择：IEW::executeInsts 的 isMemRef 分支（调度器
    # 把就绪访存指令交给 LSQ 算地址——AGU=其中的 initiateAcc）
    memref_region = iew_cc[iew_cc.index('if (inst->isMemRef()) {'):]
    memref_region = memref_region[:memref_region.index("if (inst->isAtomic())")]
    check("钩子在 isMemRef 分支顶部、atomic/load/store 分派之前",
          "chaosAguReady->maybeDelayAguReady(inst)" in memref_region,
          "")
    check("钩子返回 true 时 continue（跳过本拍正常执行路径）",
          "maybeDelayAguReady(inst)) {\n                continue;" in iew_cc,
          "")
    check("iew.hh 公有声明 chaosAguResumeInst（注入器从外部再入）",
          "void chaosAguResumeInst(const DynInstPtr &inst);" in iew_hh,
          "")
    resume_fn = iew_cc[iew_cc.index("IEW::chaosAguResumeInst"):]
    resume_fn = resume_fn[:resume_fn.index("\n}\n")]
    # resume 逐字镜像 executeInsts 的 memRef 分支
    check("resume 镜像：squash 处理（setExecuted+setCanCommit）",
          "inst->isSquashed()" in resume_fn
          and "setCanCommit()" in resume_fn, "")
    check("resume 镜像：load/store 分派 + 翻译延迟 deferMemInst",
          "ldstQueue.executeLoad(inst)" in resume_fn
          and "ldstQueue.executeStore(inst)" in resume_fn
          and "instQueue.deferMemInst(inst);" in resume_fn, "")
    check("resume 镜像：store fault/谓词簿记（setExecuted+instToCommit）",
          "instToCommit(inst);" in resume_fn
          and "readPredicate()" in resume_fn, "")
    check("resume 收尾：updateExeInstStats + activityThisCycle",
          "updateExeInstStats(inst);" in resume_fn
          and "activityThisCycle();" in resume_fn, "")
    # CPU 侧访问器
    check("cpu.hh chaosAguReady 访问器（setChaosAguReady）",
          "CHAOSAddrPath *chaosAguReady = nullptr;" in cpu_hh
          and "void setChaosAguReady(CHAOSAddrPath *p)" in cpu_hh, "")

    # 注入器：ctor 大声拒绝（tier=off / pre_mode 互斥 / delay<1 / 未知模式）
    ctor = ap_cc[:ap_cc.index("if (p.lsuTier != \"off\") {")]
    check("A07 模式拒绝 lsuTier=off（LSU-trigger-native，大声失败）",
          'if (p.lsuTier == "off")' in ctor and "panic" in ctor, "")
    check("A07 与 PRE 族互斥（一 run 一钩子，W1-⑦）",
          'if (pre_mode != "off")' in ctor and "panic" in ctor, "")
    check("A07 拒绝 delay_cycles<1（零延迟=无故障）",
          "agu_ready_delay_cycles < 1" in ctor and "panic" in ctor, "")
    check("A07 拒绝未知 agu_ready_mode（choices 外大声 panic）",
          'agu_ready_mode != "a07b_ready_delay"' in ctor
          and "panic" in ctor, "")

    # 触发纪律：onAttempt 单次 + op-class 门在触发决定之前 + F6 无双计 +
    # 无手搓概率
    hook_fn = ap_cc[ap_cc.index("CHAOSAddrPath::maybeDelayAguReady"):]
    hook_fn = hook_fn[:hook_fn.index("CHAOSAddrPath::resumeDeferredAgu")]
    check("触发语义走 ChaOSLsuTrigger（onAttempt 单次 + onEligible）",
          hook_fn.count("lsuTrigger->onAttempt();") == 1
          and "lsuTrigger->onEligible()" in hook_fn, "")
    check("op-class 门在触发决定之前（F-049：plain load/store；atomic/"
          "prefetch 不 eligible）",
          hook_fn.index("lsuTrigger->onAttempt();")
          < hook_fn.index("inst->isAtomic()")
          < hook_fn.index("lsuTrigger->onEligible()"), "")
    check("F6 事件门 onF6Event(false)（本调用 attempt 已计，无双计——"
          "R4-5.1-review-I1 形态）",
          "lsuTrigger->onF6Event(false);" in hook_fn, "")
    check("ready 钩子无手搓概率检查",
          "uniform_real_distribution" not in hook_fn
          and "uniform_int_distribution" not in hook_fn, "")
    check("单槽守卫（resume 未决时结构性拒绝第二次 fire，C12 纪律）",
          "aguResumeEvent.scheduled()" in hook_fn, "")
    check("延迟 = CPU clockEdge(delay_cycles)（未来沿）",
          "clockEdge(Cycles(agu_ready_delay_cycles))" in hook_fn, "")
    check("fire 时 stash 指令 + schedule resume 事件",
          "aguPendingInst = inst;" in hook_fn
          and "schedule(aguResumeEvent, delayed_tick);" in hook_fn, "")
    check("注册 registerAguReadyFault（inj 节点，seq=被延迟指令）",
          "registerAguReadyFault(" in hook_fn, "")
    check("activated 不在 fire 时计（Injected-not-activated 可区分——"
          "read-back 在 resume）",
          "++l0_funnel.activated" not in hook_fn, "")

    resume_thunk = ap_cc[ap_cc.index("CHAOSAddrPath::resumeDeferredAgu"):]
    resume_thunk = resume_thunk[:resume_thunk.index(
        "CHAOSAddrPath::notifyFunnelAtInjection")]
    check("resume：先清槽再再入（单槽不被重入覆盖）",
          resume_thunk.index("aguPendingInst = nullptr;")
          < resume_thunk.index("chaosAguResumeInst(inst)"), "")
    check("resume：activated 真实 read-back（再入即消费）",
          "agu_activated = true;" in resume_thunk
          and "++l0_funnel.activated;" in resume_thunk, "")
    check("resume：经 o3IEW() 再入 IEW 公有方法",
          "o3IEW().chaosAguResumeInst(inst);" in resume_thunk, "")

    # PRE 钩子 = EA 观测点（晚绑定），非注入
    pre_fn = ap_cc[ap_cc.index("CHAOSAddrPath::maybeCorruptPre"):]
    pre_fn = pre_fn[:pre_fn.index("if (probability <= 0.0f)")]
    check("A07 路径 PRE 钩子不注入不计数（早退于概率/触发逻辑之前）",
          "if (agu_ready_mode != \"off\")" in pre_fn
          and "bindAguFaultAddr" in pre_fn
          and "onAttempt" not in pre_fn, "")
    check("晚绑定按 seq 门（只有被延迟指令自己的 pushRequest 绑定）",
          "dyn_inst_seq == agu_fault_seq" in pre_fn, "")

    # startup：ready 钩子注册 + PRE 指针仅作观测点 + POST 不注册 +
    # F6 thunk 不接管 W1 四源
    startup = ap_cc[ap_cc.index("CHAOSAddrPath::startup"):]
    check("startup：A07 注册 chaosAguReady + PRE 观测点指针",
          "o3cpu->setChaosAguReady(this);" in startup
          and startup.index("if (agu_ready_mode != \"off\")")
          < startup.index("o3cpu->setChaosAguReady(this);"), "")
    check("startup：A07 的 F6 不注册 W1 四源 thunk（EIGHTH 源直调 "
          "onF6Event）",
          ('lsuTrigger->tier == ChaOSLsuTier::F6\n'
           '                && agu_ready_mode == "off"') in startup, "")
    check("startup：A07 的 F6MODE 行不打印（thunk 轨道从未运行）",
          ('lsuTrigger->tier == ChaOSLsuTier::F6\n'
           '                        && agu_ready_mode == "off"') in startup,
          "")
    check("退出回调：CHAOS_AGU_READY 行（addr_bound/activated/declines）",
          "CHAOS_AGU_READY: mode=%s delay_cycles=%lu" in ap_cc, "")

    # CHAOSPropagation：注册 API + inj 时序对 + 晚绑定条目
    check("CHAOSPropagation 提供 registerAguReadyFault + bindAguFaultAddr",
          "registerAguReadyFault" in prop_hh
          and "CHAOSPropagation::registerAguReadyFault" in prop_cc
          and "bindAguFaultAddr" in prop_hh
          and "CHAOSPropagation::bindAguFaultAddr" in prop_cc, "")
    reg = prop_cc[prop_cc.index("CHAOSPropagation::registerAguReadyFault"):]
    reg = reg[:reg.index("CHAOSPropagation::bindAguFaultAddr")]
    check("inj before/after = ready tick 前/后（时序对入统一流，C12 先例）",
          '";before=" << ready_tick' in reg
          and '";after=" << delayed_tick' in reg, "")
    check("注册时不建注册表条目（EA 尚不存在——晚绑定设计）",
          "addr_registry" not in reg, "")
    bind = prop_cc[prop_cc.index("CHAOSPropagation::bindAguFaultAddr"):]
    bind = bind[:bind.index("\n    }\n")]
    check("晚绑定 = seq-bound addr_registry 条目（seq 主臂，精确区间）",
          "e.dyn_seq = dyn_seq;" in bind
          and "addr_registry[addr] = e;" in bind, "")
    check("lsq.cc PRE 调用点传 inst->seqNum（晚绑定的 seq 面）",
          "maybeCorruptPre(addr, size, isLoad,\n"
          "                                                      flags, "
          "inst->seqNum)" in lsq_cc, "")
    check("第八 F6 事件源（AGU clean-ready）已在 trigger 头文件登记",
          "EIGHTH source" in trig_hh and "a07b_ready_delay" in trig_hh, "")
    check("CHAOSAddrPath.py 参数面（aguReadyMode + aguReadyDelayCycles）",
          "aguReadyMode" in ap_py and "aguReadyDelayCycles" in ap_py, "")

    print("[4] 路由契约（lsu_proxy → MODEL_FLAGS → F0 跨度表 → 保持阻塞）")
    proxy = src("configs/se/lsu_proxy.py")
    check("lsu_proxy --agu_ready_mode choices 含 a07b_ready_delay",
          '--agu_ready_mode' in proxy
          and '"a07b_ready_delay"' in proxy, "")
    check("lsu_proxy 挂载传递 aguReadyMode/aguReadyDelayCycles",
          "aguReadyMode=args.agu_ready_mode" in proxy
          and "aguReadyDelayCycles=args.agu_ready_delay_cycles" in proxy, "")
    check("lsu_proxy config-time 校验（tier=off / pre 互斥 / delay<1）",
          proxy.count("p.error(") >= 3, "")
    check("MODEL_FLAGS 注册 A07（addrpath 家族，显式 delay=1）",
          LC.MODEL_FLAGS.get("A07") ==
          ("addrpath", ["--agu_ready_mode", "a07b_ready_delay",
                        "--agu_ready_delay_cycles", "1"]),
          str(LC.MODEL_FLAGS.get("A07")))
    check("A07 已从 MODEL_BLOCKED 删除（实测可跑后才允许——集成侧 "
          "build + census + pilot 全过，C11/C12/L04 纪律）",
          "A07" not in LC.MODEL_BLOCKED,
          str(LC.MODEL_BLOCKED.get("A07"))[:120])
    check("旧阻塞短语已退役（'R4: no clean hook' 不再是 A07 的理由）",
          LC.MODEL_BLOCKED.get("A07") != "deferred(R4: no clean hook)", "")
    check("ADDRPATH_F0_SPAN 含两个实测条目（集成侧 census："
          "agu_addrmodes=2795 / sq_forward=2579）",
          LC.ADDRPATH_F0_SPAN.get(("A07", "agu_addrmodes")) == 2795
          and LC.ADDRPATH_F0_SPAN.get(("A07", "sq_forward")) == 2579,
          str(LC.ADDRPATH_F0_SPAN))
    check("A07 F0 tier flags：实测对 = warmup=1 + span=实测流长（真 "
          "F0-uniform）；未实测 workload 仍 loud None",
          LC._addrpath_tier_flags("A07", "F0", "agu_addrmodes") ==
          ["--addrpath_lsu_tier", "F0", "--addrpath_warmup_events", "1",
           "--addrpath_span_events", "2795"]
          and LC._addrpath_tier_flags("A07", "F0", "sq_forward") ==
          ["--addrpath_lsu_tier", "F0", "--addrpath_warmup_events", "1",
           "--addrpath_span_events", "2579"]
          and LC._addrpath_tier_flags("A07", "F0", "sqlite_like") is None,
          str(LC._addrpath_tier_flags("A07", "F0", "agu_addrmodes")))
    check("A07 非 F0 tier flags 可解析（F4/F6 惯例形 + F6 门禁 flag）",
          LC._addrpath_tier_flags("A07", "F4", "agu_addrmodes") ==
          ["--addrpath_lsu_tier", "F4", "--addrpath_warmup_events", "0",
           "--addrpath_span_events", "1000"]
          and LC._addrpath_tier_flags("A07", "F6", "sq_forward") ==
          ["--addrpath_lsu_tier", "F6", "--addrpath_warmup_events", "0",
           "--addrpath_span_events", "1000", "--addrpath_f6_mode",
           "early_stress"], "")
    check("既有 addrpath 模型 tier flags 逐字节不变（R4-2 §2.4 parked 项）",
          LC._addrpath_tier_flags("A01", "F0", "sq_forward") ==
          ["--addrpath_lsu_tier", "F0", "--addrpath_warmup_events", "0",
           "--addrpath_span_events", "1000"]
          and LC._addrpath_tier_flags("S04", "F6", "sq_forward") ==
          ["--addrpath_lsu_tier", "F6", "--addrpath_warmup_events", "0",
           "--addrpath_span_events", "1000", "--addrpath_f6_mode",
           "early_stress"], "")
    # loud refusal 路径在解阻塞后依然有效：未实测 workload 对仍被拒
    check("A07 F0 未实测 workload 对仍 loud None（F0-span-unmeasured "
          "拒绝路径未因解阻塞而失效）",
          LC._addrpath_tier_flags("A07", "F0", "sqlite_like") is None, "")

    print("[5] 矩阵解析：6 个 A07 RunID 全部 runnable（集成后真机可跑）")
    header, cells = LC.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    a07 = [c for c in cells if c[LC.COL_MODEL].strip() == "A07"]
    check("A07 cell 数 = 6", len(a07) == 6, str(len(a07)))
    all_runnable = True
    for c in a07:
        runid = c[LC.COL_RUNID].strip()
        flags, golden, note = LC.resolve_cell(c)
        if flags is None:
            all_runnable = False
            print(f"    {runid}: note={str(note)[:100]}")
    check("6 RunID 全部解析为 runnable（MODEL_BLOCKED 条目已删；campaign "
          "--dry-run 实测 runnable=6）", all_runnable, "")

    print("[6] SPEC_IMPL_LANDED 登记（集成后：真机证据在册）")
    rim = src("tools/lsu_runid_map.py")
    check('SPEC_IMPL_LANDED 含 "A07" 条目', '"A07": "implemented(' in rim, "")
    check("A07 条目声明 COMPILE-VERIFIED（集成侧已构建；不再有 "
          "COMPILE-UNVERIFIED 字样）",
          "COMPILE-VERIFIED" in rim and "COMPILE-UNVERIFIED" not in rim, "")
    check("A07 条目 pending 列逐一点名（A07-a 旧EA / A07-c 丢失）",
          "A07-a" in rim and "stale latched EA" in rim
          and "A07-c" in rim and "ready loss" in rim, "")
    check("A07 条目记录实测 census 跨度对（2795 / 2579）",
          "2795" in rim and "2579" in rim, "")
    check("A07 条目记录真机 pilot 证据（F0/F6 已注入 + F4 honest zero）",
          "A07-F6-W3" in rim and "honest zero" in rim, "")

    print()
    if FAILED:
        print(f"FAILED: {len(FAILED)} -> {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
