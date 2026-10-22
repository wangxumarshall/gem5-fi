#!/usr/bin/env python3
"""test_lsu_hook_s10.py — [MDSPEC][R4-5.7] S10 StoreSet SSIT-ID 换值契约测试.

落地模板（mode_unimpl_plan.md §逐项落地模板）第 4 步：S10（6 RunID，阻塞
短语 "consumer-side: StoreSet SSID corruption event source only"——W5
commit 7af6eed4 只放了 count-only chaosLsuF6Observe 事件源）的注入端模式
（--lsqfwd_s10 + store_set.cc StoreSet::violation 新 SSID 赋值臂的
chaosS10SsidSubst 钩子——表7 实施细则"不生成任意随机位串，而是从当前运行
中选择另一个…合法值"：候选=SSIT 现存有效条目的 SSID、排除真值；load 条目
拿替换值、store 条目保留真 SSID，训练对被拆开 + load 假并入目标集合）、
观测端（新 kind ssit_consult(L1)——checkInst 咨询腐蚀条目，
before/after=反事实/实际预测 producing-store seq；ssit_violation(L2)——
腐蚀 PC 上的 ordering violation 检出，表9 L2 档字面点名"violation/replay"；
corr 刻意不列入必录——pf_train 先例类：注入器自有 PC 键匹配、非
correlate* join，CORR_VALUES 5 值词汇表（test_lsu_prop_fields §6 钉死）
无 PC 键 join 标记）、路由（lsu_proxy flag → MODEL_FLAGS → LSQFWD_F0_SPAN
**实测条目** sq_forward/3 + gap_bfs/4（R4-8-S10 census，F0 cell 靠它可跑）→
MODEL_BLOCKED 已删除；F2 两格由 LSQFWD_INTERVAL_UNREACHABLE 逐格响亮拒绝）
与 L0 注入行契约（old_ssid/new_ssid 对 _INJ_RE 可解析）逐项钉死。

链形态（结构性，与 L04/T01-postfix 同类）：故障发生在预测器状态（PC 键），
无 addr/seq correlate 面——链成员为注入器自产事件（inj → ssit_consult →
ssit_violation → chain_end）；L2 之后（L3 cache/访存）无 S10 链事件 →
L2→L3 missing，terminal=provable_to_L2_then_unknown（beyond=Unknown，
绝不推断 Masked）。本测试把该诚实形态钉死。

诚实前置：本模式的 C++ 由隔离 no-build worktree 落地——compile-unverified，
census/pilot/逐边链证据均为集成侧步骤（R4-5.7-report.md 清单）；本测试钉
死的是源码级契约与路由行为，不声称真机证据。

用法：python3 tests/test_lsu_hook_s10.py   （退出码 0=全 PASS）
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
import lsu_runid_map as RM       # noqa: E402

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
    print("[1] 观测端契约：S10 新 kind ssit_consult/ssit_violation + 必录字段")
    check("ssit_consult 在 KIND_LAYER 注册为 L1",
          P.KIND_LAYER.get("ssit_consult") == "L1",
          str(P.KIND_LAYER.get("ssit_consult")))
    check("ssit_violation 在 KIND_LAYER 注册为 L2（表9 L2 档字面点名 "
          "violation/replay）",
          P.KIND_LAYER.get("ssit_violation") == "L2",
          str(P.KIND_LAYER.get("ssit_violation")))
    check("ssit_consult 必录字段 = fault_id/pc/field/before/after/entry_index",
          P.REQUIRED_FIELDS.get("ssit_consult") ==
          ["fault_id", "pc", "field", "before", "after", "entry_index"],
          str(P.REQUIRED_FIELDS.get("ssit_consult")))
    check("ssit_violation 必录字段 = fault_id/pc/field/state_before",
          P.REQUIRED_FIELDS.get("ssit_violation") ==
          ["fault_id", "pc", "field", "state_before"],
          str(P.REQUIRED_FIELDS.get("ssit_violation")))
    for f in (P.REQUIRED_FIELDS.get("ssit_consult", [])
              + P.REQUIRED_FIELDS.get("ssit_violation", [])):
        check(f"必录字段 {f} 已在 PROP_EVT_FIELDS 注册表（零新增字段）",
              f in P.PROP_EVT_FIELDS, f)
    # pf_train 先例类（注入器自有 PC 键匹配，非 correlate* join）：
    # corr 不列入必录。CORR_VALUES 5 值词汇表被 test_lsu_prop_fields §6
    # 钉死，无 PC 键 join 标记——扩展词汇表会破坏既有契约，此为已裁决的
    # 诚实缺席（登记于 R4-5.7 报告，供集成侧评审）。
    check("corr 刻意不列入 S10 kind 必录（pf_train 先例类，非 correlate* "
          "join——登记过的诚实缺席）",
          "corr" not in P.REQUIRED_FIELDS.get("ssit_consult", [])
          and "corr" not in P.REQUIRED_FIELDS.get("ssit_violation", []))
    check("lsu_prop_fields.py 登记 S10 corr 缺席裁决（pf_train 先例注释）",
          "pf_train 先例" in src("tools/lsu_prop_fields.py"))

    print("[2] 合成 S10 链：inj → ssit_consult → ssit_violation → chain_end")
    # 真实发射顺序（load PC=0x4448a4，真 SSID=37 → 替换 SSID=512）：
    #   inj(L0)    — 训练点换值，before/after = 真/替换 SSID，field=ssid；
    #   consult(L1)— 下一个该 PC 的 load 入 IQ 咨询预测：反事实 dep=9901
    #                （真 SSID 的 LFST 槽）、实际 dep=0（替换 SSID 无在飞
    #                store——漏预测），entry_index=512（实际命中 SSID）；
    #   violation(L2) — 该 load 提前执行后与老 store 冲突：violation 检出
    #                （漏预测的具体化），state_before=512（violation 时刻
    #                仍映射的替换 SSID）；
    #   chain_end(L5) — 退出回调。
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=12631850 "
        "pc=4448a4 before=37 after=512 field=ssid corr=origin",
        "PROP-EVT: kind=ssit_consult fault_id=1 event_id=1 tick=12680000 "
        "pc=4448a4 field=pred_dep before=9901 after=0 entry_index=512",
        "PROP-EVT: kind=ssit_violation fault_id=1 event_id=2 tick=12712250 "
        "pc=4448a4 field=dep_miss_violation state_before=512",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=3 tick=19000000 "
        "detection_layer=None contained=0 outcome=run_end corr=none",
    ]]
    check("合成 S10 链 4 事件全部可解析", len(chain) == 4
          and all(e is not None for e in chain))
    check("链上每事件过 validate_event（必录字段齐备）",
          not [e for e in chain if P.validate_event(e)],
          str([P.validate_event(e) for e in chain if P.validate_event(e)]))
    check("缺 pc 的 consult 行被拒（不得静默入流）",
          bool(P.validate_event({"kind": "ssit_consult",
                                 "fault_id": "1", "field": "pred_dep",
                                 "before": "1", "after": "0",
                                 "entry_index": "2"})))
    check("缺 state_before 的 violation 行被拒",
          bool(P.validate_event({"kind": "ssit_violation",
                                 "fault_id": "1", "pc": "4448a4",
                                 "field": "dep_miss_violation"})))
    v = CC.check_chain(chain, oracle_outcome="Masked")
    f1 = v["faults"]["1"]
    check("L0→L1 proven（inj → ssit_consult，witness fault_id）",
          f1["edges"]["L0->L1"] == "proven", str(f1["edges"].get("L0->L1")))
    check("L1→L2 proven（consult → violation）",
          f1["edges"]["L1->L2"] == "proven", str(f1["edges"].get("L1->L2")))
    check("L2→L3 missing（预测器故障无 L3 链事件——缺事件只报 Unknown）",
          f1["edges"]["L2->L3"] == "missing",
          str(f1["edges"].get("L2->L3")))
    check("terminal = provable_to_L2_then_unknown（绝不推断 Masked）",
          f1["terminal"] == "provable_to_L2_then_unknown",
          str(f1["terminal"]))
    check("beyond = Unknown", f1["beyond"] == "Unknown", str(f1["beyond"]))
    # 只有 inj + chain_end（注入的 PC 从未被咨询）——诚实 Injected-not-
    # activated 形态：链止于 L0。
    v2 = CC.check_chain([chain[0], chain[3]])
    f2 = v2["faults"]["1"]
    check("未被消费的注入：terminal = provable_to_L0_then_unknown",
          f2["terminal"] == "provable_to_L0_then_unknown",
          str(f2["terminal"]))

    print("[3] L0 注入行契约（lsu_obs_core._INJ_RE 可解析）")
    inj_line = ("Tick: 12631850, Site: StoreSet_violation_ssid_assign, "
                "mode=ssid_subst (S10-a SSIT-ID 换值), old_ssid=37, "
                "new_ssid=512, store_pc=0x444470, load_pc=0x4448a4, "
                "ssid_candidates=6, faults_injected: 1")
    m = OBS._INJ_RE.search(inj_line)
    check("注入行过 _INJ_RE（Tick/Site/mode + old_ssid/new_ssid 对）",
          m is not None and m.group(1) == "12631850"
          and m.group(2) == "StoreSet_violation_ssid_assign"
          and m.group(4) == "ssid" and m.group(5) == "37"
          and m.group(6) == "ssid" and m.group(7) == "512"
          and m.group(8) == "1",
          str(m.groups() if m else None))
    viol_line = ("Tick: 12712250, Site: StoreSet_violation_retrain, "
                 "mode=ssit_violation (S10 dep-miss manifestation), "
                 "load_pc=0x4448a4, load_ssid_now=512, faults_injected: 1")
    m2 = OBS._INJ_RE.search(viol_line)
    check("violation 观测行过 _INJ_RE（无 old/new 对也可解析）",
          m2 is not None and m2.group(8) == "1",
          str(m2.groups() if m2 else None))

    print("[4] 源码级契约：注入端（store_set.cc + CHAOSLSQFwd.cc）")
    ss = src("CHAOS/gem5/src/cpu/o3/store_set.cc")
    hh = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh")
    cc = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc")
    trig = src("CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh")
    prop_hh = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh")
    prop_cc = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc")

    check("store_set.cc 顶部钩子（violation 顶部 = attempt 流 + "
          "ssit_violation 观测）",
          "chaosS10Violation(store_PC, load_PC," in ss)
    check("store_set.cc 赋值臂钩子（chaosS10SsidSubst + 候选惰性扫描）",
          "chaosS10SsidSubst(store_PC, load_PC, new_set," in ss
          and "e.isValid()" in ss and "getSSID()" in ss)
    check("load 条目拿替换值（ld_entry->setSSID(load_ssid)）",
          "ld_entry->setSSID(load_ssid);" in ss)
    check("store 条目保留真 SSID（st_entry->setSSID(new_set)——训练对被"
          "拆开）",
          "st_entry->setSSID(new_set);" in ss)
    check("checkInst 消费观测钩子（chaosS10CorruptedPc + chaosS10Consult + "
          "counterfactual）",
          "chaosS10CorruptedPc(PC, &true_ssid)" in ss
          and "chaosS10Consult(PC, (uint64_t)inst_SSID" in ss
          and "counter_dep" in ss)
    check("W5 的 chaosLsuF6Observe(SqForward) 计数保留（拆它会改变已落地 "
          "F6 cell 的事件供给——历史并注如实登记）",
          "chaosLsuF6Observe(ChaOSLsuEvent::SqForward);" in ss)
    check("替换值不随机翻位（表7 实施细则：候选来自当前运行的合法值——"
          "S10 路径无 SSID XOR）",
          "XOR the new SSID" not in ss)

    check("CHAOSLSQFwd.cc cap 先于 onAttempt（C11 惯例：封顶后计数冻结）",
          "s10_active->max_faults != 0" in cc
          and cc.index("s10_active->max_faults != 0")
          < cc.index("s10_active->lsuTrigger->onAttempt()"))
    check("F6 事件门不重复计 attempted（onF6Event(false)，"
          "R4-5.1-review-I1 记账）",
          "s10_active->lsuTrigger->onF6Event(false)" in cc)
    check("触发语义走 ChaOSLsuTrigger（onEligible/onF6Event，无手搓概率）",
          "s10_active->lsuTrigger->onEligible()" in cc)
    # The .cc mentions the cb names twice (ctor registration
    # "&CHAOSLSQFwd::s10SsidSubstCb" and the definition) — anchor on the
    # DEFINITION signature (qualified name + parameter list).
    s10_subst_body = cc[
        cc.index("CHAOSLSQFwd::s10SsidSubstCb(Addr store_pc, Addr load_pc,"):
        cc.index("CHAOSLSQFwd::s10CorruptedPcCb(Addr pc,")]
    check("候选集排除真值且去重（合法值域）",
          "s != true_ssid" in s10_subst_body
          and "cands.begin(), cands.end(), s" in s10_subst_body)
    check("无候选则不 eligible（返回 false，不注入）",
          "cands.empty()" in s10_subst_body)
    check("目标从候选均匀抽取（seeded mt19937，非随机位串）",
          "rng() % cands.size()" in s10_subst_body)
    check("corrupt() 在 s10_mode 下旁路（hook split，L03/L04 纪律）",
          "if (s10_mode) return;" in cc)
    check("s10 模式拒绝 lsuTier=off（大声失败，不静默）",
          "--lsqfwd_s10 (S10 StoreSet SSIT-ID 换值 " in cc
          and "requires --lsqfwd_lsu_tier" in cc)
    check("s10 模式拒绝 probability=0 挂载（日志流/退出回调路径在标准"
          "挂载内）",
          "requires the standard mount" in cc)
    check("ctor 注册 chaosS10* 全局（单消费者，chaosMergeHook 先例）",
          "chaosS10Violation = &CHAOSLSQFwd::s10ViolationCb;" in cc)
    check("dtor 注销 chaosS10* 全局（只清指向自己的）",
          "chaosS10Violation = nullptr;" in cc)
    check("activated = 消费口径（consult/violation 读取腐蚀条目，非注入"
          "同义反复）",
          "s10_mode ? s10_activated_count" in cc)
    check("violation 观测先于 cap（机械链证据，L04 half-2 纪律）",
          cc.index("ssit_violation") < cc.index("s10_active->max_faults != 0"))

    print("[5] 源码级契约：观测注册端 + F6 事件源裁决")
    check("CHAOSPropagation 提供 registerStoreSetFault（.hh 声明）",
          "registerStoreSetFault(Addr store_pc, Addr load_pc," in prop_hh)
    reg_body = prop_cc[prop_cc.index("CHAOSPropagation::registerStoreSetFault"):]
    reg_body = reg_body[:reg_body.index("\n    }\n") + 1]
    check("inj 节点 corr=origin（链开启注册）", "CORR_ORIGIN" in reg_body)
    check("inj before/after = 真/替换 SSID（old_addr/new_addr 抬升）",
          ";old_addr=\" << true_ssid" in reg_body
          and ";new_addr=\" << new_ssid" in reg_body)
    check("pc 抬升到统一 pc 字段（腐蚀 load PC = 链键）",
          ";pc=\" << std::hex << load_pc" in reg_body)
    check("零下游 correlate 注册（无 addr_registry/blk_registry 写入——"
          "PC 键预测器状态无 addr/seq 面，pf_train 先例）",
          "addr_registry" not in reg_body and "blk_registry" not in reg_body)
    check("ssit_consult 发射字段含 before/after/entry_index（反事实/实际"
          "预测）",
          "{\"before\", std::to_string(counterfactual_dep)}" in cc
          and "{\"after\", std::to_string(actual_dep)}" in cc
          and "{\"entry_index\", std::to_string(actual_ssid)}" in cc)
    check("EIGHTH F6 事件源（StoreSet SSID 赋值训练事件）已在 trigger 头"
          "登记",
          "EIGHTH source" in trig and "StoreSet::violation's new-SSID arm"
          in trig)
    check("trigger 头登记 SqForward 计数并注（W5 7af6eed4 历史保留）",
          "HISTORICAL CONFLATION" in trig)

    print("[6] 路由契约：lsu_proxy flag → MODEL_FLAGS → span 表 → "
          "MODEL_BLOCKED")
    proxy = src("configs/se/lsu_proxy.py")
    injpy = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py")
    check("CHAOSLSQFwd.py 参数面 s10Mode", "s10Mode = Param.Bool" in injpy)
    check("lsu_proxy --lsqfwd_s10 flag + s10Mode 透传",
          '"--lsqfwd_s10"' in proxy and "s10Mode=args.lsqfwd_s10" in proxy)
    check("MODEL_FLAGS 注册 S10（lsqfwd 家族 + --lsqfwd_s10）",
          LC.MODEL_FLAGS.get("S10") == ("lsqfwd", ["--lsqfwd_s10"]),
          str(LC.MODEL_FLAGS.get("S10")))
    # [MDSPEC][R4-8-S10] the R4-5.7b platform-defect block was LIFTED by
    # the §R4-6-S10 platform fix + this round's census: S10 is no longer in
    # MODEL_BLOCKED. The honest state is now PER-TIER (see the matrix
    # section below), not a blanket model block.
    check("S10 已从 MODEL_BLOCKED 删除（平台缺陷已修并真机验证，"
          "§R4-6-S10；F0/F2 改由逐格门禁把关）",
          "S10" not in LC.MODEL_BLOCKED,
          str(LC.MODEL_BLOCKED.get("S10"))[:120])
    check("LSQFWD_F0_SPAN 有 S10 实测条目（本轮 census：sq_forward/3、"
          "gap_bfs/4——R4-8-S10）",
          LC.LSQFWD_F0_SPAN.get(("S10", "sq_forward")) == 3
          and LC.LSQFWD_F0_SPAN.get(("S10", "gap_bfs")) == 4,
          str({k: v for k, v in LC.LSQFWD_F0_SPAN.items() if k[0] == "S10"}))
    check("LSQFWD_INTERVAL_UNREACHABLE 登记 S10-F2 两格（F2 下界 50000 "
          ">> 实测流长，响亮拒绝而非静默零）",
          ("S10", "F2", "sq_forward") in LC.LSQFWD_INTERVAL_UNREACHABLE
          and ("S10", "F2", "gap_bfs") in LC.LSQFWD_INTERVAL_UNREACHABLE)
    check("LSU_INTERVAL_EVENTS 与 trigger 头 intervalEvents() 一致"
          "（F1/F2/F3/F4 = 1e6/1e5/1e4/1e5）",
          LC.LSU_INTERVAL_EVENTS == {"F1": 1000000, "F2": 100000,
                                     "F3": 10000, "F4": 100000},
          str(LC.LSU_INTERVAL_EVENTS))

    print("[7] 矩阵解析：S10 的 6 cell（F0/F5 runnable；F2 逐格响亮拒绝）")
    header, cells = LC.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    s10 = [c for c in cells if c[LC.COL_MODEL].strip() == "S10"]
    check("S10 cell 数 = 6", len(s10) == 6, str(len(s10)))
    runids = {c[LC.COL_RUNID].strip() for c in s10}
    check("S10 RunID 集合 = 任务书 6 项",
          runids == {"S10-F0-W5", "S10-F0-W9", "S10-F2-W5", "S10-F2-W9",
                     "S10-F5-W5", "S10-F5-W9"}, str(sorted(runids)))
    # Expected per-cell state after R4-8-S10 (measured, not asserted blind):
    expect = {
        "S10-F0-W5": ("runnable", 3), "S10-F0-W9": ("runnable", 4),
        "S10-F5-W5": ("runnable", None), "S10-F5-W9": ("runnable", None),
        "S10-F2-W5": ("blocked", "interval-tier-unreachable"),
        "S10-F2-W9": ("blocked", "interval-tier-unreachable"),
    }
    for c in s10:
        runid = c[LC.COL_RUNID].strip()
        tier = c[LC.COL_FREQ].strip()
        flags, golden, note = LC.resolve_cell(c)
        want, extra = expect[runid]
        if want == "runnable":
            ok = flags is not None and note is not None
            if extra is not None:
                # F0: the measured span must be the F0 window (warmup=1).
                ok = ok and "--lsqfwd_span_events" in flags and \
                    flags[flags.index("--lsqfwd_span_events") + 1] == str(extra)
            check(f"{runid} runnable（tier={tier}，实测门禁通过）", ok,
                  f"flags={flags}")
        else:
            ok = (flags is None and note is not None and extra in note)
            check(f"{runid} loud blocked（tier={tier}，理由="
                  f"{extra}，绝不静默 runnable）", ok, f"note={str(note)[:90]}")

    print("[8] SPEC_IMPL_LANDED 登记契约（源码钉；JSON 再生成为集成侧步骤）")
    rm_src = src("tools/lsu_runid_map.py")
    check("SPEC_IMPL_LANDED 源码含 S10 条目",
          '"S10": "implemented(ssid_subst=S10-a' in rm_src)
    for pending in ("S10-b LFST", "S10-c store-set valid loss"):
        check(f"pending 子模型点名：{pending}", pending in rm_src)
    check("登记已改写为集成侧实测定论（真机负结果，不冒充已实证）",
          "evidence: REAL RUNS, NEGATIVE" in rm_src
          and "platform-defect" in rm_src.split('"S10"')[1][:2400])

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
