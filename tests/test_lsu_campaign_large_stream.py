#!/usr/bin/env python3
"""test_lsu_campaign_large_stream.py — [LSU][MDSPEC][R6-SCAL] 大事件流链报告量级契约。

缺陷（2026-10-23 实测，r6_mc_O01-F0-W7 multicore FS 真实流 222,056 事件）：
`write_chain_report` → `lsu_chain_check.check_chain` → `_edges_for` →
`_best_ordered_path` **对每个事件**各做一次祖先遍历（`_ancestry`）+ 贪心前缀
扫描（`_ordered_prefix`）。consumer 链的祖先深度 ~100 且随下标增长 ⇒ 复杂度
Θ(n²)。实测 check_chain 前缀标度（真流前缀）：n=1000 → 1.19s、n=2000 →
7.31s、n=4000 → 30.9s；cProfile(n=2000) `_best_ordered_path` 占 16.27/16.30s。
后果：222k 事件的 cell 在 gem5 退出后 27+ 分钟仍未写出 cell_results.json。

本套件钉死三件事：
  1. 线性实现 `LC._linear_best_ordered_path` 与出厂 `_best_ordered_path`
     在多形状事件流上给出**逐事件同结果**（含并列时的先到先得）；
  2. `write_chain_report` 在 ~222k 事件流上于限时内完成（真机 < 60s），且
     chain 判定与小流参考形状一致（terminal=full / provable_to=L5）；
  3. 小流参考形状的 chain_report 判定载荷与出厂实现逐字段相同；
  4. 负例：仅生命周期 chain_end（无真实 L5 检测事件）绝不判 full
     （只到 L4、beyond=Unknown、门禁不得 READY）。

[R6-GATE-D1] 合成流须含**真实 L5 检测事件**：errant_commit 富化
detection_layer=L5 + outcome + 链关联 corr（挂于 taint_reg 下，同一条
parent_event_id DAG）——生命周期 chain_end 永不充当 L5。

用法：python3 tests/test_lsu_campaign_large_stream.py   （退出码 0=全 PASS）
"""
import gzip
import json
import signal
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC          # noqa: E402
import lsu_chain_check as CHAIN    # noqa: E402
import lsu_prop_fields as P        # noqa: E402

FAILED = []

# 大流限时：真机实测 222k 事件全路径 < 15s；120s 是"量级正确"的宽容上限
# （出厂实现在同一流上需要小时级，绝不会通过）。
BIG_DEADLINE_S = 120.0
# 大流规模/形状 = 真流形状（r6_mc_O01-F0-W7 实测：**单条线性 consumer 链**，
# depth(i)=i+1、Σdepth=2.47e10、leaves=1 ⇒ 出厂实现 Θ(n²)）。幂等合成，
# 不依赖其他 lane 的 runs/ 现场。
N_CHAINS = 1
CHAIN_LEN = 222000
# 小流参考形状规模（与 T04 参考同族；fan-out 形状，覆盖并列/多叶情形）
SMALL_CHAINS = 6
SMALL_CHAIN_LEN = 40
BIG_NOTE = ("真流实测 shape：单链 depth(i)=i+1（Σdepth=2.47e10, leaves=1）")


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + str(detail) if not cond else ""))
    if not cond:
        FAILED.append(name)


class _Deadline(Exception):
    pass


def _alarm(seconds):
    def _h(signum, frame):
        raise _Deadline("exceeded %.0fs" % seconds)
    signal.signal(signal.SIGALRM, _h)
    signal.setitimer(signal.ITIMER_REAL, seconds)


def _cancel_alarm():
    signal.setitimer(signal.ITIMER_REAL, 0)


# --------------------------------------------------------------------------
# 流生成：与 r6_mc_O01-F0-W7 同形（单 fault_id；spine L0→L5 一条 + consumer
# 链扇形展开，每条链挂到 spine 的 L3 节点上，祖先深度 ~CHAIN_LEN）。
# --------------------------------------------------------------------------
def _spine(n_events_out, real_l5=True):
    """返回 (lines, spine_tail_id)。L0→L1→L2→L3→L4→L5 单链，形状对齐
    T04 参考流（可在同一流内证得 full）。

    [R6-GATE-D1] L5 的唯一合法证据是**真实检测事件**（非生命周期 kind +
    detection_layer + outcome + 链关联 corr）。真实流里 errant_commit 就是
    检测点——未富化时只到 L4；富化后（detection_layer=L5 + outcome=SDC +
    corr=taint_prop）才占 L5，链据此证得 full。生命周期 chain_end 由
    构造永不占 L5（corr=none，kind=chain_end → _layer_of=None）。

    real_l5=False：errant_commit 保持未富化（只到 L4），仅剩生命周期
    chain_end——供负例断言"仅有 chain_end 绝不判 full"。
    """
    errant = "dyn_inst_seq=5 request_id=77 corr=taint_prop"
    if real_l5:
        # 真实 L5 检测事件载荷：检测层 + 结局 + 链关联 corr（挂在 taint_reg 下）
        errant += " detection_layer=L5 outcome=SDC"
    seq = [
        ("inj", "corr=origin"),
        ("addr_form", "va=0x1000 corr=origin"),
        ("mem_req", "dyn_inst_seq=5 va=0x1000 corr=seq_primary"),
        ("resp", "dyn_inst_seq=5 corr=seq_primary"),
        ("taint_reg", "dyn_inst_seq=5 arch_reg=3 phys_reg=9 corr=taint_prop"),
        ("errant_commit", errant),
        # 生命周期终局标记：corr=none；即便带 detection_layer/outcome 也
        # 永不充当 L5（D1 结构性堵死 ready_by_chain_end_only）
        ("chain_end", "detection_layer=Hardware contained= outcome=SDC "
                      "corr=none"),
    ]
    lines = []
    parent = ""
    for i, (kind, extra) in enumerate(seq):
        lines.append(
            "PROP-EVT: kind=%s run_id=R6SCAL-F0-W1 sample_run_id=s1 "
            "fault_id=1 event_id=%d parent_event_id=%s tick=%d %s"
            % (kind, i, parent, 1000 + i, extra))
        parent = str(i)
    n_events_out.append(len(lines))
    return lines, 3   # resp (L3) 的 event_id


def _stream_lines(n_chains, chain_len, n_events_out, real_l5=True):
    """spine + 扇形 consumer 链；事件计数写入 n_events_out。"""
    lines, fanout_parent = _spine(n_events_out, real_l5)
    eid = len(lines)
    for c in range(n_chains):
        parent = str(fanout_parent)
        for _ in range(chain_len):
            lines.append(
                "PROP-EVT: kind=consumer run_id=R6SCAL-F0-W1 sample_run_id=s1 "
                "fault_id=1 event_id=%d parent_event_id=%s tick=%d "
                "dyn_inst_seq=%d arch_reg=%d phys_reg=%d corr=derived"
                % (eid, parent, 1000 + eid, eid, 10 + (eid % 30),
                   200 + (eid % 64)))
            parent = str(eid)
            eid += 1
    n_events_out.append(len(lines))
    return lines


def _write_stream(path, n_chains, chain_len, real_l5=True):
    counts = []
    lines = _stream_lines(n_chains, chain_len, counts, real_l5)
    with gzip.open(str(path), "wt", encoding="utf-8") as f:
        f.write("# prop-evt v1: test_lsu_campaign_large_stream\n")
        f.writelines(ln + "\n" for ln in lines)
    return counts[-1]


# --------------------------------------------------------------------------
def section_equivalence():
    """[1] 线性实现 vs 出厂实现：多形状逐事件同结果。"""
    print("[1] _linear_best_ordered_path vs 出厂 _best_ordered_path（同结果）")
    fast = getattr(LC, "_linear_best_ordered_path", None)
    check("线性实现已就位", fast is not None,
          "lsu_campaign._linear_best_ordered_path 缺失（未修复）")
    if fast is None:
        return

    # 形状 A：本套件的小流（spine + 扇形）
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "small.txt.gz"
        _write_stream(p, SMALL_CHAINS, SMALL_CHAIN_LEN)
        events, _tr = P.read_events(p)
    # 形状 B/C/D：退化但合法的手工流
    def ev(eid, parent, kind, tick, **kw):
        d = {"event_id": str(eid), "parent_event_id": str(parent),
             "kind": kind, "tick": str(tick), "fault_id": "1", "run_id": "X"}
        d.update({k: str(v) for k, v in kw.items()})
        return d

    shapes = {
        "small-real-shape": events,
        "linear-chain": [ev(i, i - 1 if i else "", "consumer", i * 10)
                         for i in range(1, 60)],
        "flat-fanout": [ev(0, "", "inj", 1)] +
                       [ev(i, 0, "consumer", 1 + i) for i in range(1, 30)],
        "no-fault-id": [ev(0, "", "inj", 1)] +
                       [ev(i, i - 1, "consumer", i) for i in range(1, 20)],
        "orphan-parent": [ev(0, "", "inj", 1), ev(1, 999, "resp", 2),
                          ev(2, 1, "taint_reg", 3)],
    }
    for name, evs in shapes.items():
        for family in ("generic", "tlb"):
            got = [e["event_id"] for e in fast(evs, family, CHAIN)]
            want = [e["event_id"] for e in CHAIN._best_ordered_path(evs, family)]
            check("同结果[%s/%s]" % (name, family), got == want,
                  "fast=%s shipped=%s" % (got, want))

    # 事件对象身份：path 必须是流里的同一批对象（chain_check 下游据此取字段）
    got = fast(events, "generic", CHAIN)
    check("path 元素为流内同一对象", all(any(e is x for x in events)
                                         for e in got), "身份不符")


def section_large_bound():
    """[2] ~222k 事件流：限时内完成且判定与参考形状一致。"""
    print("[2] ~222k 事件流：write_chain_report 限时（< %.0fs）"
          % BIG_DEADLINE_S)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        n_expected = _write_stream(d / "prop_evt.txt.gz", N_CHAINS, CHAIN_LEN)
        (d / "stats.txt").write_text("simTicks 1\n")
        check("流规模 ~222k", abs(n_expected - 222000) < 2000, n_expected)
        t0 = time.time()
        try:
            _alarm(BIG_DEADLINE_S)
            rep = LC.write_chain_report(d, "R6SCAL-F0-W1", 1,
                                        {"outcome": "Crash"}, exit_code=0)
        except _Deadline as e:
            dt = time.time() - t0
            check("大流在限时内完成", False,
                  "%.1fs 未完成（%s）——出厂逐事件祖先遍历 Θ(n²)" % (dt, e))
            return
        finally:
            _cancel_alarm()
        dt = time.time() - t0
        print("      实测 wall %.1fs（%d 事件）" % (dt, rep["event_count"]))
        check("大流在限时内完成", dt < BIG_DEADLINE_S, "%.1fs" % dt)
        # 头注释行（'# prop-evt v1:'）不是事件，不计数
        check("事件计数守恒", rep["event_count"] == n_expected,
              "%s vs %s" % (rep["event_count"], n_expected))
        check("判定与参考形状一致（terminal=full）",
              rep["terminal"] == "full", rep["terminal"])
        check("层映射与参考形状一致（provable_to=L5）",
              rep["provable_to"] == "L5", rep["provable_to"])
        check("闭合终局 beyond 为空", rep["beyond"] == "", repr(rep["beyond"]))
        check("截断旗标 = 完整 gzip 流",
              rep["truncated"] is False and rep["evidence_truncated"] is False,
              "%s/%s" % (rep["truncated"], rep["evidence_truncated"]))
        check("chain_report.json 已落盘", (d / "chain_report.json").exists())


def section_small_reference():
    """[3] 小流：判定载荷与出厂 check_chain 逐字段相同（无语义漂移）。"""
    print("[3] 小流参考形状：报告载荷 == 出厂 check_chain（逐字段）")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _write_stream(d / "prop_evt.txt.gz", SMALL_CHAINS, SMALL_CHAIN_LEN)
        (d / "stats.txt").write_text("simTicks 1\n")
        rep = LC.write_chain_report(d, "R6SCAL-F0-W1", 2,
                                    {"outcome": "Crash"}, exit_code=0)
        events, _tr = P.read_events(d / "prop_evt.txt.gz")
        ref = CHAIN.check_chain(events, oracle_outcome="Crash")
        check("faults 载荷逐字段相同",
              json.dumps(rep["faults"], sort_keys=True) ==
              json.dumps(ref["faults"], sort_keys=True),
              "faults 漂移")
        check("terminal/provable_to/beyond 同参考",
              (rep["terminal"], rep["provable_to"], rep["beyond"]) ==
              (ref["faults"]["1"]["terminal"], ref["faults"]["1"]["provable_to"],
               ref["faults"]["1"]["beyond"]),
              str((rep["terminal"], rep["provable_to"], rep["beyond"])))
        check("报告字段齐备",
              all(k in rep for k in ("run_id", "sample_run_id",
                                     "oracle_outcome", "exit_code",
                                     "stream_present", "truncated",
                                     "event_count", "evidence_truncated",
                                     "truncation_reason", "chain_valid",
                                     "summary")), str(sorted(rep)))
        check("未截断 → chain_valid True", rep["chain_valid"] is True)


def section_negative_lifecycle_only():
    """[4] 负例：仅生命周期 chain_end（无真实 L5 检测事件）绝不判 full。

    [R6-GATE-D1] 生命周期 chain_end 由构造不占 L5（ready_by_chain_end_only
    结构性堵死）：即便它带 detection_layer/outcome 文本，也不得把链推成
    full；链只能诚实停在 L4（provable_to_L4_then_unknown，beyond=Unknown），
    门禁不得 READY。
    """
    print("[4] 负例：仅 chain_end（无真实 L5 检测）→ 不得判 full")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _write_stream(d / "prop_evt.txt.gz", 2, 8, real_l5=False)
        (d / "stats.txt").write_text("simTicks 1\n")
        events, _tr = P.read_events(d / "prop_evt.txt.gz")
        ref = CHAIN.check_chain(events, oracle_outcome="Crash")
        f1 = ref["faults"]["1"]
        check("负例 terminal != full", f1["terminal"] != "full",
              f1["terminal"])
        check("负例 terminal=provable_to_L4_then_unknown",
              f1["terminal"] == "provable_to_L4_then_unknown",
              f1["terminal"])
        check("负例 provable_to=L4", f1["provable_to"] == "L4",
              f1["provable_to"])
        check("负例 beyond=Unknown（开放终局，绝不 full）",
              f1["beyond"] == "Unknown", repr(f1["beyond"]))
        adm = CHAIN.check_admission({"run_id": "R6SCAL-F0-W1", "activated": 1,
                                     "events": events,
                                     "oracle_outcome": "Crash"})
        check("负例门禁不得 READY（not admitted）", adm["admitted"] is False,
              adm["admitted"])
        rep = LC.write_chain_report(d, "R6SCAL-F0-W1", 3,
                                    {"outcome": "Crash"}, exit_code=0)
        check("负例 chain_report terminal != full",
              rep["terminal"] != "full", rep["terminal"])


def main():
    section_equivalence()
    section_large_bound()
    section_small_reference()
    section_negative_lifecycle_only()
    print()
    if FAILED:
        print("FAILED (%d): %s" % (len(FAILED), FAILED))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
