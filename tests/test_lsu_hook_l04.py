#!/usr/bin/env python3
"""test_lsu_hook_l04.py — [MDSPEC][R4-5.3] L04 响应配对目标互换契约测试.

落地模板（mode_unimpl_plan.md §逐项落地模板）第 4 步：L04（6 RunID，
阻塞短语 "consumer-side: response-pairing event source only"）的注入端
模式（--lsqfwd_l04 + LSQUnit::completeDataAccess 配对点钩子
maybeSwapResponseTarget——request->instruction() 绑定处，09 sheet 钦定
"L04在response配对点新增可注入且可观测hook"）、观测端（inj corr=origin
+ 既有 resp/lq_complete/taint_reg/consumer/errant_commit/chain_end 链
kind——L04 不新增 kind；inj 的 before/after = 故障值即配对映射
source-seq → target-seq；配对表以两条 seq-bound addr-registry 条目入链
——L04 不注册任何 address-only fallback，比"标注 fallback"最低线更严）、
路由（lsu_proxy flag → MODEL_FLAGS → LSQFWD_F0_SPAN 实测跨度（L04 自有
流：配对点的合格 load 响应）→ 从 MODEL_BLOCKED 删除）与 L0 注入行契约
逐项钉死。

链形态（结构性，与 T01-postfix 同类）：配对点故障发生在 L3（响应交付），
受影响 load 的 L1/L2 请求路径事件（lsq_push/mem_req/lsq_sendfrag）先于
注入存在、不回溯入链——梯子 L0→L1/L1→L2/L2→L3 missing，
L3→L4/L4→L5 proven，terminal=provable_to_L0_then_unknown（beyond=
Unknown，绝不推断 Masked）。本测试把该诚实形态钉死。

用法：python3 tests/test_lsu_hook_l04.py   （退出码 0=全 PASS）
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
    print("[1] 观测端契约：L04 链复用既有 kind（无新 kind）+ 必录字段")
    chain_kinds = ["inj", "resp", "lq_complete", "taint_reg",
                   "consumer", "errant_commit", "chain_end"]
    for k in chain_kinds:
        check(f"{k} 在 KIND_LAYER 注册", k in P.KIND_LAYER,
              str(P.KIND_LAYER.get(k)))
    check("inj 必录字段 = fault_id+corr（R4-4-review-I1）",
          P.REQUIRED_FIELDS.get("inj") == ["fault_id", "corr"],
          str(P.REQUIRED_FIELDS.get("inj")))
    check("resp/lq_complete 必录字段含 corr（L04 入链臂标注）",
          "corr" in P.REQUIRED_FIELDS.get("resp", [])
          and "corr" in P.REQUIRED_FIELDS.get("lq_complete", []),
          str(P.REQUIRED_FIELDS.get("resp")))
    check("L04 无新 kind（resp_pair 是 inj 的 field 值，非事件 kind）",
          "resp_pair" not in P.KIND_LAYER and "resp_pairing" not in P.KIND_LAYER,
          str(P.KIND_LAYER.get("resp_pair")))

    # 合成 L04-b 链（真实发射顺序，src seq=42 / tgt seq=57）：
    #   half 1 — src(42) 的响应交付给 tgt(57)：resp/lq_complete 的
    #            dyn_inst_seq=57（错消费者）、request_id=42（src 的请求
    #            戳——配对错换在流上可读）；
    #   half 2 — tgt(57) 的响应交付给 src(42)：镜像；
    #   然后 taint_reg(双方 dest) → consumer → errant_commit → chain_end。
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=12631850 "
        "dyn_inst_seq=57 request_id=57 va=48fb70 before=42 after=57 "
        "field=resp_pairing corr=origin",
        "PROP-EVT: kind=resp fault_id=1 event_id=1 tick=12631850 "
        "dyn_inst_seq=57 request_id=42 corr=seq_primary",
        "PROP-EVT: kind=lq_complete fault_id=1 event_id=2 tick=12631850 "
        "dyn_inst_seq=57 lq_idx=9 va=48fb70 pa=48fb70 request_id=42 "
        "corr=seq_primary",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=3 tick=12631855 "
        "dyn_inst_seq=57 phys_reg=5 arch_reg=5 corr=seq_primary",
        "PROP-EVT: kind=resp fault_id=1 event_id=4 tick=12660100 "
        "dyn_inst_seq=42 request_id=57 corr=seq_primary",
        "PROP-EVT: kind=lq_complete fault_id=1 event_id=5 tick=12660100 "
        "dyn_inst_seq=42 lq_idx=4 va=496798 pa=496798 request_id=57 "
        "corr=seq_primary",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=6 tick=12660105 "
        "dyn_inst_seq=42 phys_reg=8 arch_reg=8 corr=seq_primary",
        "PROP-EVT: kind=consumer fault_id=1 event_id=7 tick=12690000 "
        "dyn_inst_seq=90 phys_reg=5 arch_reg=5 corr=taint_prop",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=8 tick=12700000 "
        "dyn_inst_seq=57 corr=taint_prop",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=9 tick=19000000 "
        "detection_layer=None contained=0 outcome=run_end corr=none",
    ]]
    check("合成 L04 链 10 事件全部可解析", len(chain) == 10
          and all(e is not None for e in chain))
    # R4-4-review-I1：链上每事件 corr 必须非空（显式标注关联来源）
    no_corr = [e["kind"] for e in chain if not e.get("corr")]
    check("链上每事件 corr 非空（关联来源显式）", not no_corr, str(no_corr))
    # corr 词汇表值（origin/seq_primary/taint_prop/none 均合法）
    bad_corr = [e["kind"] for e in chain
                if e.get("corr") and e["corr"] not in P.CORR_VALUES]
    check("corr 值均在 CORR_VALUES 词汇表内", not bad_corr, str(bad_corr))
    # L04 特有：配对错换在流上可读——inj.before/after = source/target seq
    inj = chain[0]
    check("inj before/after = 配对映射 src-seq → tgt-seq（before≠after）",
          int(inj["before"]) != int(inj["after"]),
          f"before={inj['before']} after={inj['after']}")
    lq1 = next(e for e in chain if e["kind"] == "lq_complete"
               and e["dyn_inst_seq"] == "57")
    lq2 = next(e for e in chain if e["kind"] == "lq_complete"
               and e["dyn_inst_seq"] == "42")
    check("half-1 错换可读：lq_complete(tgt).request_id == inj.before（src 戳）",
          lq1["request_id"] == inj["before"],
          f"lq1.request_id={lq1['request_id']} before={inj['before']}")
    check("half-2 镜像可读：lq_complete(src).request_id == inj.after（tgt 戳）",
          lq2["request_id"] == inj["after"],
          f"lq2.request_id={lq2['request_id']} after={inj['after']}")
    check("inj.dyn_inst_seq = tgt（错消费者，与 resp/lq_complete 同 seq）",
          inj["dyn_inst_seq"] == "57")
    # 每事件过 validate_event（必录字段契约）
    bad_req = []
    for e in chain:
        v = P.validate_event(e)
        if v:
            bad_req.append((e["kind"], v))
    check("合成链逐事件过 validate_event（必录字段齐备）", not bad_req,
          str(bad_req))
    # 梯子（结构性诚实形态）：
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("L3→L4 proven（resp/lq_complete → taint_reg）",
          f1["edges"]["L3->L4"] == "proven", str(f1["edges"].get("L3->L4")))
    check("L4→L5 proven（taint_reg/consumer → chain_end）",
          f1["edges"]["L4->L5"] == "proven", str(f1["edges"].get("L4->L5")))
    check("L0→L1/L1→L2/L2→L3 missing（请求路径先于注入，不回溯——"
          "T01-postfix 同类结构性缺席）",
          f1["edges"]["L0->L1"] == "missing"
          and f1["edges"]["L1->L2"] == "missing"
          and f1["edges"]["L2->L3"] == "missing",
          str([f1["edges"].get(k) for k in
               ("L0->L1", "L1->L2", "L2->L3")]))
    check("terminal = provable_to_L0_then_unknown（缺事件只报 Unknown）",
          f1["terminal"] == "provable_to_L0_then_unknown", f1["terminal"])
    check("beyond = Unknown（绝不推断 Masked）", f1["beyond"] == "Unknown",
          f1["beyond"])

    print("[2] L0 注入行契约（lsq_fwd_injections.log 实际格式，_INJ_RE 契约）")
    inj_line = ("Tick: 12631850, Site: completeDataAccess_response_pairing, "
                "mode=resp_pairing (L04-b target exchange), "
                "source_dyn_inst_seq=42, source_lq_idx=4, "
                "source_request_id=42, source_va=0x48fb70, "
                "target_dyn_inst_seq=57, target_lq_idx=9, "
                "target_request_id=57, target_va=0x496798, "
                "faults_injected: 1")
    l0 = OBS.parse_l0(
        "CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=2449 "
        "eligible=812 injected=1",
        inj_line)
    check("无 L0 violation（注入行可解析——Tick/Site/mode 契约）",
          not l0["violations"], str(l0["violations"]))
    check("漏斗四元组从 stdout 解析",
          (l0["attempted"], l0["eligible"], l0["injected"]) == (2449, 812, 1),
          str((l0["attempted"], l0["eligible"], l0["injected"])))
    check("注入明细 mode=resp_pairing…（source/target ID 保存于行内）",
          len(l0["injections"]) == 1
          and l0["injections"][0]["mode"].startswith("resp_pairing"),
          str(l0["injections"]))

    print("[3] 注入端源码契约（触发纪律 + 端到端接线 + 顺序契约）")
    lhh = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh")
    lcc = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc")
    lpy = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py")
    lu = src("CHAOS/gem5/src/cpu/o3/lsq_unit.cc")
    lsq = src("CHAOS/gem5/src/cpu/o3/lsq.cc")
    trig_hh = src("CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh")
    prop_hh = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.hh")
    prop_cc = src("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.cc")
    check("CHAOSLSQFwd.hh 声明 RespPairKeys/RespPairCand/"
          "maybeSwapResponseTarget + l04 pending 态",
          "struct RespPairKeys" in lhh
          and "struct RespPairCand" in lhh
          and "maybeSwapResponseTarget" in lhh
          and "l04_pending_tgt_seq" in lhh)
    check("lsq_unit.cc 配对点（completeDataAccess）咨询钩子",
          "maybeSwapResponseTarget" in lu
          and "cpu->lsqFwd->maybeSwapResponseTarget" in lu)
    # 顺序契约：替换 target 用于交付面（squash 检查/观测/writeback），
    # 请求侧（HTM/probe）保持原 inst
    cda = lu[lu.index("LSQUnit::completeDataAccess(PacketPtr pkt)"):]
    cda = cda[:cda.index("\nLSQUnit::LSQUnit(")]
    check("交付面用 target（noteMemResponse(target…)）",
          "noteMemResponse(target.get()" in cda)
    check("交付面用 target（writeback(target…)）",
          "writeback(target, request->mainPacket())" in cda)
    check("squash 检查在 target 上（!target->isSquashed()）",
          "!target->isSquashed()" in cda)
    check("请求侧保持原 inst（ppDataAccessComplete->notify(inst)）",
          "std::make_pair(inst, pkt)" in cda)
    # 候选门（同尺寸/同 byte-enable/在途包已发出——completeAcc 越界防护）
    check("候选门：同尺寸（cr->_size != request->_size 拒绝）",
          "cr->_size != request->_size" in lu)
    check("候选门：同 byte-enable（防越界读）",
          "cr->_byteEnable != request->_byteEnable" in lu)
    check("候选门：候选请求有在途包（响应必回——未发出的 load 可能被"
          "forward 满足而永不响应）",
          "cr->_numOutstandingPackets == 0" in lu)
    check("候选门：plain WB load（isLoad 且非 atomic/SC、未执行未 squash）",
          "c->isAtomic()" in lu and "c->isStoreConditional()" in lu
          and "c->isExecuted()" in lu)
    hook = lcc[lcc.index(
        "CHAOSLSQFwd::maybeSwapResponseTarget"):]
    # [R4-5.7] the S10 callbacks were appended after maybeSwapResponseTarget
    # in the same namespace tail — bound the slice at the S10 section so the
    # L04 per-function pins below (single onAttempt etc.) keep testing the
    # L04 body only (the namespace-end cut would swallow the S10 bodies).
    hook = hook[:hook.index("    // [MDSPEC][R4-5.7] S10 StoreSet SSIT-ID 换值")]
    check("half-2 先于 maxFaults cap（封顶不掐断已建交换——否则 src 悬挂）",
          hook.index("l04_pending_tgt_seq") < hook.index("max_faults"),
          "order")
    check("触发语义走 ChaOSLsuTrigger（onAttempt/onEligible/onF6Event）",
          "onAttempt()" in hook and "onEligible()" in hook
          and "onF6Event(false)" in hook)
    check("F6 事件门不重复计 attempted（onF6Event(false)，"
          "R4-5.1-review-I1 形态）",
          "lsuTrigger->onF6Event(false);" in hook
          and hook.count("lsuTrigger->onAttempt();") == 1)
    check("half-2 不计 attempt（避免注入事件自身足迹双计）",
          hook.index("l04_pending_tgt_seq") < hook.index("onAttempt"))
    check("配对点函数无手搓概率检查（无 Bernoulli/uniform_real）",
          "uniform_real_distribution" not in hook)
    check("corrupt() 在 l04_mode 下旁路（配对点流分裂，L03 纪律）",
          "if (l04_mode) return;" in lcc)
    ctor = lcc[:lcc.index("CHAOSLSQFwd::~CHAOSLSQFwd")]
    check("l04 模式拒绝 lsuTier=off（大声失败，不静默）",
          "l04_mode && !lsuTrigger" in ctor and "panic" in ctor)
    check("CHAOSPropagation 提供 registerRespPairFault",
          "registerRespPairFault" in prop_hh
          and "CHAOSPropagation::registerRespPairFault" in prop_cc)
    reg = prop_cc[prop_cc.index("CHAOSPropagation::registerRespPairFault"):]
    reg = reg[:reg.index("\n    }")]
    check("inj before/after = 配对映射 src-seq → tgt-seq（old_addr/new_addr "
          "lift 键）",
          '";old_addr=" << src_seq' in reg
          and '";new_addr=" << tgt_seq' in reg)
    check("inj.dyn_inst_seq = tgt（错消费者，与 resp/lq_complete 同 seq）",
          'writeNode(ptag, "inj", tgt_seq' in reg)
    check("交换配对表 = 两条 seq-bound addr_registry 条目"
          "（[src_va]→tgt_seq 与 [tgt_va]→src_seq）",
          reg.count("addr_registry[") == 2
          and "e.dyn_seq = tgt_seq;" in reg
          and "e2.dyn_seq = src_seq;" in reg)
    check("L04 注册无 address-only fallback（无 blk_registry 条目——"
          "09 sheet 禁止地址单键连接）",
          "blk_registry" not in reg)
    check("同 VA 碰撞只留 half-1 绑定（tgt_va != src_va 才注册第二条）",
          "if (tgt_va != src_va)" in reg)
    check("第七 F6 事件源（LQ response-pairing 点）已在 trigger 头登记",
          "SEVENTH source" in trig_hh and "completeDataAccess" in trig_hh
          and "--lsqfwd_l04" in trig_hh)
    check("lsq.cc CasSuccess observe 保留（计数），注入决策移至配对点"
          "（旧 'redirect to the WRONG LSQ unit' 占位注释已改写为事实）",
          "chaosLsuF6Observe(ChaOSLsuEvent::CasSuccess);" in lsq
          and "WRONG LSQ unit" not in lsq)
    check("CHAOSLSQFwd.py 参数面 l04Mode",
          "l04Mode" in lpy)

    print("[4] 路由契约（lsu_proxy → MODEL_FLAGS → F0 跨度 → 解阻塞）")
    proxy = src("configs/se/lsu_proxy.py")
    check("lsu_proxy --lsqfwd_l04 flag + l04Mode 透传",
          '"--lsqfwd_l04"' in proxy and "l04Mode=args.lsqfwd_l04" in proxy)
    check("MODEL_FLAGS 注册 L04（lsqfwd 家族 + --lsqfwd_l04）",
          LC.MODEL_FLAGS.get("L04") == ("lsqfwd", ["--lsqfwd_l04"]),
          str(LC.MODEL_FLAGS.get("L04")))
    check("L04 已从 MODEL_BLOCKED 删除（实测可跑后才允许）",
          "L04" not in LC.MODEL_BLOCKED)
    check("后续模型未误解锁（C14/C15 仍 BLOCKED；S10 已于 R4-5.7 落地）",
          all(m in LC.MODEL_BLOCKED for m in ("C14", "C15"))
          and "S10" in LC.MODEL_BLOCKED)
    for pair in (("L04", "sq_forward"), ("L04", "sqlite_like")):
        check(f"LSQFWD_F0_SPAN 实测条目 {pair}",
              isinstance(LC.LSQFWD_F0_SPAN.get(pair), int)
              and LC.LSQFWD_F0_SPAN[pair] > 0,
              str(LC.LSQFWD_F0_SPAN.get(pair)))
    check("L04 F0 tier flags 用实测跨度（warmup=1）",
          LC._lsqfwd_tier_flags("L04", "F0", "sq_forward") ==
          ["--lsqfwd_lsu_tier", "F0", "--lsqfwd_warmup_events", "1",
           "--lsqfwd_span_events",
           str(LC.LSQFWD_F0_SPAN[("L04", "sq_forward")])],
          str(LC._lsqfwd_tier_flags("L04", "F0", "sq_forward")))
    check("未实测 (L04, workload) F0 拒绝（loud None）",
          LC._lsqfwd_tier_flags("L04", "F0", "cache_dirtyevict") is None)
    check("S 模型 tier flags 不受 L04 落地影响（逐字节不变）",
          LC._lsqfwd_tier_flags("S01", "F0", "sq_forward") ==
          ["--lsqfwd_lsu_tier", "F0", "--lsqfwd_warmup_events", "1",
           "--lsqfwd_span_events", "7"])
    runid_map_py = src("tools/lsu_runid_map.py")
    check("SPEC_IMPL_LANDED L04 落地登记（机器可读 landed/pending，"
          "源码 pin）",
          '"L04": "implemented(resp_pairing=L04-b' in runid_map_py
          and "pending: L04-a" in runid_map_py)
    runid_json = ROOT / "docs/gem5-fi/lsu/mdspec/runid_map.json"
    l04_partial = l04_spec = l04_landed = 0
    if runid_json.exists():
        import json as _json
        m = _json.loads(runid_json.read_text(encoding="utf-8"))
        l04e = [e for e in m.get("entries", [])
                if e.get("model_id") == "L04"]
        l04_landed = sum(1 for e in l04e if e.get("spec_landed"))
        l04_partial = sum(1 for e in l04e if e.get("status") == "PARTIAL")
        l04_spec = sum(1 for e in l04e
                       if e.get("status") == "BLOCKED"
                       and any("SPEC" in r for r in e.get("status_reasons", [])))
    check("runid_map.json 再生成后 L04 9 条目全带 spec_landed（落地留证）",
          l04_landed == 9, f"spec_landed entries={l04_landed}")
    check("runid_map.json L04 = 6 PARTIAL（可跑）+ 3 SPEC-blocked（W11）",
          l04_partial == 6 and l04_spec == 3,
          f"PARTIAL={l04_partial} SPEC={l04_spec}")

    print("[5] 矩阵解析：L04 的 9 个 cell（6 runnable + 3 SPEC-blocked）")
    header, cells = LC.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    l04 = [c for c in cells if c[LC.COL_MODEL].strip() == "L04"]
    check("L04 cell 数 = 9", len(l04) == 9, str(len(l04)))
    runnable = {"L04-F0-W5", "L04-F0-W12", "L04-F2-W5", "L04-F2-W12",
                "L04-F6-W5", "L04-F6-W12"}
    for c in l04:
        runid = c[LC.COL_RUNID].strip()
        flags, golden, note = LC.resolve_cell(c)
        if runid in runnable:
            ok = (flags is not None and golden
                  and "--lsqfwd_l04" in flags
                  and "--lsqfwd_lsu_tier" in flags)
            check(f"{runid} 解析为 lsqfwd_l04 运行配置", ok,
                  f"flags={flags} note={note}")
        else:
            ok = (flags is None and note and "SPEC" in note)
            check(f"{runid} 保持 SPEC license 阻塞（不属于本任务）", ok,
                  f"note={note}")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
