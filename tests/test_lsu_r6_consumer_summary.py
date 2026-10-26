#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-FIXTOOLS] T04 `consumer_summary` 契约（不跑仿真）。

口径（用户裁决）：**语义状态变化完整保留，重复 consumer 有账聚合；禁止简单截断。**
本套件钉 8 条规则：
  ① summary 不映射 L0–L5 任何一层；
  ② summary 不得充当 L5 / containment / terminal；
  ③ summary 不得成为伪造的 parent ancestry 节点；
  ④ malformed / 负计数 / 计数不守恒 ⇒ 响亮拒绝；
  ⑤ checker 的 path_event_ids/terminal/admitted/violations 在**小型未聚合对照流**
     与**聚合流**上一致；
  ⑥ campaign 报告展示 emitted events / suppressed consumers / logical total /
     conservation 状态；
  ⑦ truncated / resource_abort 仍必须 admitted=False（不得靠 summary 掩盖）；
  ⑧ 原有无 summary 流保持兼容（read_events 行为不变）。

用法：python3 tests/test_lsu_r6_consumer_summary.py   （exit 0 = 全 PASS）
"""
import gzip
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P      # noqa: E402
import lsu_chain_check as CHAIN  # noqa: E402
import lsu_campaign as LC        # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


RUN = "L05-F0-W5"


def _ev(eid, kind, parent, tick, **kw):
    """Build one PROP-EVT line (only the fields we care about; parser fills rest)."""
    parts = [f"kind={kind}", f"run_id={RUN}", "fault_id=1", f"event_id={eid}",
             f"parent_event_id={parent}", f"tick={tick}"]
    for k, v in kw.items():
        parts.append(f"{k}={v}")
    return "PROP-EVT: " + " ".join(parts)


def _summary_line(**kw):
    base = {"schema": "1", "version": "1", "run_id": RUN, "sample_run_id": "s1",
            "fault_id": "1", "source_id": "phys_reg:31",
            "suppressed_consumer_count": "49", "distinct_dyn_seq_count": "1",
            "emitted_consumer_count": "1", "first_tick": "100", "last_tick": "900",
            "min_dyn_seq": "7", "max_dyn_seq": "7",
            "by_kind": "consumer:50", "by_outcome": "sd_observed:50",
            "total_before": "50", "total_after": "50"}
    base.update({k: str(v) for k, v in kw.items()})
    return "CONSUMER-SUMMARY: " + " ".join(f"{k}={v}" for k, v in base.items())


# 五事件 full 链（inj L0 → addr_form L1 → mem_req L2 → resp L3 → errant_commit
# L4/L5 with detection payload corr=taint_prop）+ N 个 consumer（L4 重复）。
def _chain_lines(n_consumers):
    lines = [_ev(1, "inj", "", 10, va="1000"),
             _ev(2, "addr_form", "1", 20, va="1000", corr="origin"),
             _ev(3, "mem_req", "2", 30, va="1000", dyn_inst_seq="7",
                 corr="seq_primary"),
             _ev(4, "resp", "3", 40, dyn_inst_seq="7", corr="seq_primary")]
    parent = "4"
    for i in range(n_consumers):
        eid = 5 + i
        lines.append(_ev(eid, "consumer", parent, 100 + i * 10, dyn_inst_seq="7",
                         phys_reg="31", arch_reg="11", corr="taint_prop"))
        parent = str(eid)
    # L5 终点：固定 event_id=900（与 consumer 条数无关 ⇒ 聚合前后路径逐位相同），
    # contained=0（非含住 ⇒ 终局 full，而非 detected_contained）。
    lines.append(_ev(900, "errant_commit", parent,
                     100 + n_consumers * 10, dyn_inst_seq="7",
                     detection_layer="L5", outcome="errant_commit",
                     contained="0", corr="taint_prop"))
    return lines


def main():
    # ---- 规则 ①：summary 不映射任何层、不是 PROP-EVT ------------------------
    print("[1] summary 不映射 L0–L5（不是 PROP-EVT、kind 空）")
    sl = _summary_line()
    rec = P.parse_consumer_summary(sl)
    check("summary 行被识别（非 None）", rec is not None)
    check("summary 不是 PROP-EVT（parse_line 返回 None）",
          P.parse_line(sl) is None)
    check("summary 不占任何层（_layer_of → None）",
          CHAIN._layer_of(rec) is None, str(CHAIN._layer_of(rec)))
    check("summary 不是真实 L5 检测事件（_explicit_l5 → False）",
          CHAIN._explicit_l5(rec) is False)

    print("[2] summary 不得充当 L5 / containment / terminal（规则 ②）")
    evts_only = [P.parse_line(l) for l in _chain_lines(50)]
    evts_only = [e for e in evts_only if e is not None]
    # 无 summary 时的含住束
    cont_wo = CHAIN.containment_from_events(evts_only, RUN)
    # 把 summary 混进事件集，含住束不得改变
    cont_with = CHAIN.containment_from_events(evts_only + [rec], RUN)
    check("containment 束不因 summary 改变", cont_wo == cont_with,
          f"{cont_wo} vs {cont_with}")

    print("[3] summary 不得成为伪造的 parent ancestry 节点（规则 ③）")
    v_wo = CHAIN.check_chain(evts_only)
    v_with = CHAIN.check_chain(evts_only + [rec])
    check("混入 summary 后 path_event_ids 不变",
          v_wo["faults"]["1"]["path_event_ids"]
          == v_with["faults"]["1"]["path_event_ids"],
          str(v_with["faults"]["1"]["path_event_ids"]))
    check("summary 无 event_id（不能进 DAG）", "event_id" not in rec)

    # ---- 规则 ④：malformed / 负计数 / 不守恒 ⇒ 响亮拒绝 --------------------
    print("[4] malformed / 负计数 / 不守恒 响亮拒绝（规则 ④）")
    check("合法 summary 无错误", P.validate_consumer_summary(rec) == [],
          str(P.validate_consumer_summary(rec)))
    bad_missing = dict(rec)
    bad_missing["source_id"] = ""
    check("缺必录字段 ⇒ 错误", any("source_id" in m for m in
                                   P.validate_consumer_summary(bad_missing)))
    bad_neg = dict(rec, suppressed_consumer_count="-3")
    check("负计数 ⇒ 错误", any("为负" in m for m in
                               P.validate_consumer_summary(bad_neg)))
    bad_nonint = dict(rec, total_before="abc")
    check("非整数 ⇒ 错误", any("非整数" in m for m in
                               P.validate_consumer_summary(bad_nonint)))
    bad_cons = dict(rec, total_after="51")
    check("total_before != total_after ⇒ 不守恒错误",
          any("不守恒" in m for m in P.validate_consumer_summary(bad_cons)))
    bad_emit = dict(rec, emitted_consumer_count="0", suppressed_consumer_count="50")
    check("emitted=0 且 total>0 ⇒ 简单截断错误（禁止全抑无出）",
          any("简单截断" in m for m in P.validate_consumer_summary(bad_emit)))
    bad_kind = dict(rec, by_kind="consumer:49")   # 与 total_before=50 不合
    check("by_kind 合计 != total_before ⇒ 不守恒",
          any("by_kind" in m for m in P.validate_consumer_summary(bad_kind)))

    print("[5] check_admission：malformed summary ⇒ 响亮违规 + 不准入")
    ok_a = CHAIN.check_admission({"run_id": RUN, "activated": 1,
                                 "events": evts_only})
    bad_a = CHAIN.check_admission({"run_id": RUN, "activated": 1,
                                  "events": evts_only,
                                  "summary_issues": ["consumer_summary: x"]})
    check("合法 summary ⇒ admitted 与违规集不变", ok_a["admitted"] is True
          and not any("consumer_summary" in v for v in ok_a["violations"]),
          str(ok_a["violations"]))
    check("malformed summary ⇒ 新增 malformed_consumer_summary 违规",
          any(v.startswith("malformed_consumer_summary") for v in bad_a["violations"]),
          str(bad_a["violations"]))
    check("malformed summary ⇒ admitted=False",
          bad_a["admitted"] is False)
    check("malformed_consumer_summary 是具名门禁 token",
          "malformed_consumer_summary" in CHAIN.GATE_VIOLATIONS)

    # ---- 规则 ⑤：小型未聚合对照流 vs 聚合流，checker 输出一致 --------------
    print("[5'] 小流 vs 聚合流：path_event_ids/terminal/admitted/violations 一致")
    control_events = evts_only                                  # 50 个 consumer
    agg_events = [P.parse_line(l) for l in _chain_lines(1)]      # 1 个 consumer
    agg_events = [e for e in agg_events if e is not None]
    c_chain = CHAIN.check_chain(control_events)
    a_chain = CHAIN.check_chain(agg_events)
    c_adm = CHAIN.check_admission({"run_id": RUN, "activated": 1,
                                   "events": control_events})
    a_adm = CHAIN.check_admission({"run_id": RUN, "activated": 1,
                                   "events": agg_events})
    check("terminal 一致", c_chain["faults"]["1"]["terminal"]
          == a_chain["faults"]["1"]["terminal"],
          f'{c_chain["faults"]["1"]["terminal"]} vs {a_chain["faults"]["1"]["terminal"]}')
    check("path_event_ids 一致", c_chain["faults"]["1"]["path_event_ids"]
          == a_chain["faults"]["1"]["path_event_ids"],
          f'{c_chain["faults"]["1"]["path_event_ids"]} vs '
          f'{a_chain["faults"]["1"]["path_event_ids"]}')
    check("admitted 一致且为 True", c_adm["admitted"] == a_adm["admitted"] is True,
          f'{c_adm["admitted"]} vs {a_adm["admitted"]}')
    check("violations 一致（都为空）",
          c_adm["violations"] == a_adm["violations"] == [],
          f'{c_adm["violations"]} vs {a_adm["violations"]}')

    # ---- 规则 ⑥：campaign 报告展示 emitted/suppressed/logical/conservation --
    print("[6] campaign 报告展示 emitted/suppressed/logical total/conservation")
    tmp = Path(tempfile.mkdtemp(prefix="r6_csum_"))
    outdir = tmp / "s1"
    outdir.mkdir(parents=True)
    with gzip.open(outdir / "prop_evt.txt.gz", "wt") as f:
        for l in _chain_lines(1):
            f.write(l + "\n")
        f.write(_summary_line() + "\n")
    (outdir / "stats.txt").write_text("simTicks 1\n")
    rep = LC.write_chain_report(outdir, RUN, 1, {"outcome": "SDC"}, exit_code=0)
    acct = rep.get("consumer_summary_accounting") or {}
    check("报告含 consumer_summary_accounting", bool(acct), str(acct))
    check("展示 emitted/suppressed/logical_total",
          acct.get("emitted_events") == 1
          and acct.get("suppressed_consumers") == 49
          and acct.get("logical_total") == 50, str(acct))
    check("conservation=ok", acct.get("conservation") == "ok", str(acct))
    check("summary 行文字含 conservation/emitted",
          "conservation=ok" in rep["summary"] and "emitted=1" in rep["summary"],
          rep["summary"])

    # ---- 规则 ⑦：truncated / resource_abort 仍 admitted=False --------------
    print("[7] 截断流（无 chain_end）仍不准入，summary 不得掩盖")
    tmp7 = Path(tempfile.mkdtemp(prefix="r6_csum7_"))
    out7 = tmp7 / "s1"
    out7.mkdir(parents=True)
    # 相同链 + 合法 summary，但**无** chain_end 且流标志截断
    open7 = [P.parse_line(l) for l in _chain_lines(1)]
    open7 = [e for e in open7 if e is not None]
    a7 = CHAIN.check_admission({"run_id": RUN, "activated": 1, "events": open7,
                                "summary_issues": []})
    check("(对照) 有 chain_end 的真实链本身可准入", a7["admitted"] is True,
          str(a7["violations"]))
    with gzip.open(out7 / "prop_evt.txt.gz", "wt") as f:
        for l in _chain_lines(1):
            f.write(l + "\n")
        f.write(_summary_line() + "\n")
    # stats.txt 缺失 ⇒ detect_evidence_truncation 判截断
    rep7 = LC.write_chain_report(out7, RUN, 1, {"outcome": "Crash"}, exit_code=None)
    check("截断流：admitted=False（summary 不得掩盖）",
          rep7["admitted"] is False and rep7["evidence_truncated"] is True,
          f'admitted={rep7["admitted"]} truncated={rep7["evidence_truncated"]}')
    check("截断流：conservation 仍如实记录（summary 合法）",
          (rep7.get("consumer_summary_accounting") or {}).get("conservation") == "ok",
          str(rep7.get("consumer_summary_accounting")))

    # ---- 规则 ⑧：无 summary 流兼容 -----------------------------------------
    print("[8] 无 summary 旧流兼容（read_events 行为不变）")
    tmp8 = Path(tempfile.mkdtemp(prefix="r6_csum8_"))
    p8 = tmp8 / "prop_evt.txt"
    p8.write_text("\n".join(_chain_lines(3)) + "\n")
    ev8, tr8 = P.read_events(p8)
    ev8b, tr8b, su8, iss8 = P.read_stream(p8)
    check("read_events 事件数与 read_stream 一致",
          len(ev8) == len(ev8b) == 8 and tr8 is False and tr8b is False,
          f"{len(ev8)} vs {len(ev8b)}")
    check("无 summary 流 summaries 为空、无 issues", su8 == [] and iss8 == [])
    check("无 summary 流 checker 判定与裸流一致",
          CHAIN.check_chain(ev8)["faults"]["1"]["terminal"]
          == CHAIN.check_chain(ev8b)["faults"]["1"]["terminal"])

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
