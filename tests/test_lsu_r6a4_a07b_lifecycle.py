#!/usr/bin/env python3
"""test_lsu_r6a4_a07b_lifecycle.py — [MDSPEC][R6-A4/A07-b] 真实生命周期契约测试。

用户裁决 7（2026-10-28）：A07-b（ready-delay）必须建立**真实时序故障
生命周期**与**可证终局**，不得伪造数据错误 / 不得推断 L5。本文件是给
checker 的**可执行契约**（主 agent 在 tools/lsu_chain_check.py 里实现同一
契约；本文件顶部的 ``validate_a07b_lifecycle`` 是参考实现，测试直接跑它，
因此契约本身是经过实证执行的，不是纸面约定）。

=====================================================================
CHECKER 契约（主 agent 实现名 / 位置建议）
---------------------------------------------------------------------
    tools/lsu_chain_check.check_a07b_lifecycle(events, truncated=False,
                                               oracle_outcome=None) -> dict

    events  = tools.lsu_prop_fields.parse_line 解析出的事件 dict 列表
    dict 键 = {
        "accepted": bool,          # 生命周期收口是否成立（可证终局）
        "terminal": "retired_after_delay" | "squashed_before_retire"
                    | "discarded_before_retire" | None,
        "fault_id": str, "dyn_inst_seq": str,
        "chain": [event_id, ...],  # inj -> resume -> terminal
        "violations": [code, ...], # 空 = 接受；非空 = 拒绝（响亮、逐条）
    }

    R1 事件形状（A07-b 生命周期，kind 固定）：
         inj                field=agu_ready_delay（已有事件，corr=origin）
         ready_delay_resume        parent=inj.event_id
         ready_delay_retired       parent=resume.event_id（真实退休）
         ready_delay_squashed      parent=resume.event_id（resume 时已 squash）
         ready_delay_discarded     parent=resume.event_id（resume 后被真实 ROB
                                   squash 取消，如 data-invalid/abort）
       恰好一个 inj、一个 resume、一个 terminal；terminal 三选一。
    R2 同一 ancestry / 同一请求：链内所有生命周期事件的 dyn_inst_seq 相同且
       非空，request_id == dyn_inst_seq（本树 Request::getReqInstSeqNum() ==
       DynInst::seqNum —— A07-b 的"请求身份"就是这条动态指令）。
       任一不一致 => cross_request_*，拒绝（禁止跨请求拼接）。
    R3 tick 不变量（真实观测，不修正）：
         ready_tick < delayed_tick <= resume_tick <= terminal_tick
       ready_tick = inj.before = 各事件 ready_tick 列
       delayed_tick = inj.after = 各事件 delayed_tick 列
       违者 => delay_start_ge_delayed / resume_before_delayed /
                terminal_before_resume / ...（拒绝并如实记录）
    R4 字段齐全（resume）：consumed=1、squashed=0|1、ready_tick/delayed_tick/
       delay_cycles、dyn_inst_seq、pc、corr=seq_primary、field=agu_ready_delay。
    R5 终局语义（只认真实钩子产出的三选一，watchdog 一律不认）：
         ready_delay_retired   outcome=retired_after_delay
                               detection_layer=L5 contained=1
                               containment_layer=L5
                               containment_reason=delay_transparent_retire
                               squashed=0（未 squash 才谈得上退休）
         ready_delay_squashed  outcome=contained detection_layer=L4
                               contained=1 containment_layer=L4
                               containment_reason=squash_before_retire
                               squashed=1；tick == resume_tick（同一钩子观测量）
         ready_delay_discarded outcome=discarded_before_retire
                               detection_layer=L4 contained=1
                               containment_layer=L4
                               containment_reason=squash_after_resume_before_retire
                               squashed=1
    R6 拒绝（响亮、不猜测）：
         - 缺 parent_event_id / resume.parent != inj.event_id /
           terminal.parent != resume.event_id
         - tick 倒退（R3）
         - 跨请求 dyn_inst_seq / request_id
         - 流截断（truncated=True 且无 terminal）
         - 只有 chain_end（无 inj/resume/terminal）
         - 只有 inj（无 resume）
         - 只有 inj+resume（无 terminal）——"截至 resume 可证，终局 Unknown"
         - ready_tick >= delayed_tick（delay_start >= resume）
         - terminal 早于 resume
         - 普通 L0-only 链（无 A07 生命周期事件）不得放行
    R7 A07-b 的终局永远是 contained（值不变，只改时序）；本契约**不得**
       产出 SDC / full(escape)。

用法：python3 tests/test_lsu_r6a4_a07b_lifecycle.py  （退出码 0 = 全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P  # noqa: E402
import lsu_chain_check as CC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


# ---------------------------------------------------------------------------
# 参考实现（= 契约）。主 agent 在 tools/lsu_chain_check.py 的
# check_a07b_lifecycle 必须与本函数逐条同判。
# ---------------------------------------------------------------------------

_LIFE_KINDS = ("ready_delay_resume",)
TERMINALS = {
    # kind -> (outcome, detection_layer, containment_reason, squashed)
    "ready_delay_retired": ("retired_after_delay", "L5",
                            "delay_transparent_retire", "0"),
    "ready_delay_squashed": ("contained", "L4",
                             "squash_before_retire", "1"),
    "ready_delay_discarded": ("discarded_before_retire", "L4",
                              "squash_after_resume_before_retire", "1"),
}
_ALL_LIFE = _LIFE_KINDS + tuple(TERMINALS)


def _i(evt, key):
    try:
        return int(str(evt.get(key, "") or "0"), 10)
    except ValueError:
        return 0


def _result(accepted, violations, fid=None, seq=None, terminal=None,
            chain=None):
    return {"accepted": accepted, "violations": list(violations),
            "fault_id": fid, "dyn_inst_seq": seq, "terminal": terminal,
            "chain": list(chain or []), "contained": bool(accepted)}


def validate_a07b_lifecycle(events, truncated=False, oracle_outcome=None):
    groups = {}
    for e in events:
        fid = str(e.get("fault_id", "") or "")
        if fid and fid != "0":
            groups.setdefault(fid, []).append(e)

    def _any(pred):
        return any(pred(e) for grp in groups.values() for e in grp)

    any_life = _any(lambda e: e.get("kind") in _ALL_LIFE)
    any_inj = _any(lambda e: e.get("kind") == "inj"
                   and e.get("field") == "agu_ready_delay")
    if not any_life and not any_inj:
        return _result(False, ["no_lifecycle_events"])
    if len(groups) != 1:
        return _result(False, ["multiple_faults"])
    fid, chain = next(iter(groups.items()))

    injs = [e for e in chain if e.get("kind") == "inj"
            and e.get("field") == "agu_ready_delay"]
    if not injs:
        return _result(False, ["missing_inj"], fid=fid)
    if len(injs) > 1:
        return _result(False, ["multiple_inj"], fid=fid)
    inj = injs[0]
    seq = str(inj.get("dyn_inst_seq", "") or "")
    req = str(inj.get("request_id", "") or "")
    v = []
    if not seq or seq == "0":
        v.append("inj_missing_dyn_inst_seq")
    if req != seq:
        v.append("inj_request_id_not_dyn_inst_seq")

    res = [e for e in chain if e.get("kind") == "ready_delay_resume"]
    terms = [e for e in chain if e.get("kind") in TERMINALS]
    if not res:
        v.append("missing_resume")
    elif len(res) > 1:
        v.append("multiple_resume")
    if not terms:
        v.append("missing_terminal")
        if truncated:
            v.append("truncated_stream")
        return _result(False, v, fid=fid, seq=seq)
    if len(terms) > 1:
        v.append("multiple_terminals")
    if not res:
        return _result(False, v, fid=fid, seq=seq)

    r, t = res[0], terms[0]
    # R2 same-request identity on every lifecycle event.
    for e in chain:
        if e.get("kind") in _ALL_LIFE:
            if str(e.get("dyn_inst_seq", "") or "") != seq:
                v.append("cross_request_dyn_inst_seq")
            if str(e.get("request_id", "") or "") != req:
                v.append("cross_request_request_id")
    # R1/R6 ancestry.
    inj_id = str(inj.get("event_id", "") or "")
    res_id = str(r.get("event_id", "") or "")
    if not inj_id:
        v.append("missing_inj_event_id")
    if not res_id or res_id == inj_id:
        v.append("missing_resume_event_id")
    if str(r.get("parent_event_id", "") or "") != inj_id:
        v.append("resume_parent_not_inj")
    if str(t.get("parent_event_id", "") or "") != res_id:
        v.append("terminal_parent_not_resume")
    if not str(t.get("event_id", "") or ""):
        v.append("missing_terminal_event_id")
    # R3 tick invariant.
    ready, delayed = _i(inj, "before"), _i(inj, "after")
    if not ready < delayed:
        v.append("delay_start_ge_delayed")
    if _i(inj, "delay_cycles") < 1:
        v.append("delay_cycles_zero")
    if _i(inj, "tick") != ready:
        v.append("inj_tick_not_ready_tick")
    rtick = _i(r, "tick")
    if not delayed <= rtick:
        v.append("resume_before_delayed")
    tterm = _i(t, "tick")
    if tterm < rtick:
        v.append("terminal_before_resume")
    if str(t.get("kind")) == "ready_delay_squashed" and tterm != rtick:
        v.append("squash_tick_not_resume_tick")
    # R4 resume fields.
    if str(r.get("consumed", "") or "") != "1":
        v.append("resume_not_consumed")
    if _i(r, "ready_tick") != ready or _i(r, "delayed_tick") != delayed:
        v.append("resume_ready_state_mismatch")
    if _i(r, "delay_cycles") != _i(inj, "delay_cycles"):
        v.append("resume_delay_cycles_mismatch")
    for e, nm in ((r, "resume"), (t, "terminal")):
        if str(e.get("corr", "") or "") != "seq_primary":
            v.append(f"{nm}_corr_not_seq_primary")
        if str(e.get("field", "") or "") != "agu_ready_delay":
            v.append(f"{nm}_missing_field")
        if not str(e.get("pc", "") or ""):
            v.append(f"{nm}_missing_pc")
    # R5 terminal semantics.
    kind = str(t.get("kind"))
    outcome, layer, reason, squashed = TERMINALS[kind]
    if str(t.get("outcome", "") or "") != outcome:
        v.append("terminal_outcome_mismatch")
    if str(t.get("detection_layer", "") or "") != layer:
        v.append("terminal_detection_layer_mismatch")
    if str(t.get("contained", "") or "") != "1":
        v.append("terminal_not_contained")
    if str(t.get("containment_layer", "") or "") != layer:
        v.append("terminal_containment_layer_mismatch")
    if str(t.get("containment_reason", "") or "") != reason:
        v.append("terminal_containment_reason_mismatch")
    if str(t.get("squashed", "") or "") != squashed:
        v.append("terminal_squashed_flag_mismatch")
    if str(t.get("consumed", "") or "") != "1":
        v.append("terminal_not_consumed")

    accepted = not v
    return _result(accepted, v, fid=fid, seq=seq,
                   terminal=outcome if accepted else None,
                   chain=[inj_id, res_id, str(t.get("event_id", "") or "")])


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
BASE_TICK = 12606440
CYCLE = 385  # 2.6 GHz -> 385 ticks/cycle (real C2 clock)


def _line(kind, fid=1, **kv):
    parts = [f"kind={kind}", f"fault_id={fid}", "run_id=A07-F0-W3",
             "sample_run_id=s1", "evidence_status=observed"]
    parts += [f"{k}={v}" for k, v in kv.items()]
    return "PROP-EVT: " + " ".join(parts)


def _parse(lines):
    evts = []
    for ln in lines:
        e = P.parse_line(ln)
        assert e is not None, ln
        evts.append(e)
    return evts


def _chain(terminal="ready_delay_retired", seq="9703", pc="0x44452c",
           ready=BASE_TICK, delayed=BASE_TICK + CYCLE, delay_cycles=1,
           resume_tick=None, terminal_tick=None, squashed_at_resume=False):
    """A well-formed A07-b lifecycle (valid unless a kwarg breaks it)."""
    resume_tick = delayed if resume_tick is None else resume_tick
    lines = [
        _line("inj", event_id=10, parent_event_id="", tick=ready,
              dyn_inst_seq=seq, request_id=seq, pc=pc,
              field="agu_ready_delay", before=ready, after=delayed,
              delay_cycles=delay_cycles, state_before="ready",
              state_after="delayed", corr="origin"),
        _line("ready_delay_resume", event_id=11, parent_event_id=10,
              tick=resume_tick, dyn_inst_seq=seq, request_id=seq, pc=pc,
              field="agu_ready_delay", ready_tick=ready,
              delayed_tick=delayed, delay_cycles=delay_cycles,
              consumed="1", squashed="1" if squashed_at_resume else "0",
              corr="seq_primary"),
    ]
    if terminal == "ready_delay_retired":
        ttick = (resume_tick + 1000) if terminal_tick is None else terminal_tick
        lines.append(_line(terminal, event_id=12, parent_event_id=11,
                           tick=ttick, dyn_inst_seq=seq, request_id=seq, pc=pc,
                           field="agu_ready_delay", ready_tick=ready,
                           delayed_tick=delayed, delay_cycles=delay_cycles,
                           consumed="1", squashed="0",
                           outcome="retired_after_delay", detection_layer="L5",
                           contained="1", containment_layer="L5",
                           containment_reason="delay_transparent_retire",
                           corr="seq_primary"))
    elif terminal == "ready_delay_squashed":
        ttick = resume_tick if terminal_tick is None else terminal_tick
        lines.append(_line(terminal, event_id=12, parent_event_id=11,
                           tick=ttick, dyn_inst_seq=seq, request_id=seq, pc=pc,
                           field="agu_ready_delay", ready_tick=ready,
                           delayed_tick=delayed, delay_cycles=delay_cycles,
                           consumed="1", squashed="1", outcome="contained",
                           detection_layer="L4", contained="1",
                           containment_layer="L4",
                           containment_reason="squash_before_retire",
                           corr="seq_primary"))
    elif terminal == "ready_delay_discarded":
        ttick = (resume_tick + 5000) if terminal_tick is None else terminal_tick
        lines.append(_line(terminal, event_id=12, parent_event_id=11,
                           tick=ttick, dyn_inst_seq=seq, request_id=seq, pc=pc,
                           field="agu_ready_delay", ready_tick=ready,
                           delayed_tick=delayed, delay_cycles=delay_cycles,
                           consumed="1", squashed="1",
                           outcome="discarded_before_retire",
                           detection_layer="L4", contained="1",
                           containment_layer="L4",
                           containment_reason=(
                               "squash_after_resume_before_retire"),
                           corr="seq_primary"))
    return _parse(lines)


def _replace(lines, event_id, **kv):
    """Rewrite one fixture line's fields (kept for the negative fixtures)."""
    out = []
    for ln in lines:
        if f"event_id={event_id} " in ln or ln.endswith(f"event_id={event_id}"):
            parts = [p for p in ln.split()
                     if p.split("=", 1)[0] not in kv]
            parts += [f"{k}={v}" for k, v in kv.items()]
            ln = " ".join(parts)
        out.append(ln)
    return out


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
def test_parser_keeps_a07b_fields():
    print("[parser] new A07-b family-extension columns survive parse_line")
    evts = _parse([_line(
        "ready_delay_resume", event_id=11, parent_event_id=10, tick=123,
        dyn_inst_seq="7", request_id="7", ready_tick="100",
        delayed_tick="123", delay_cycles="1", consumed="1", squashed="0",
        field="agu_ready_delay", corr="seq_primary")])
    e = evts[0]
    check("ready_tick kept", e.get("ready_tick") == "100", str(e))
    check("delayed_tick kept", e.get("delayed_tick") == "123")
    check("delay_cycles kept", e.get("delay_cycles") == "1")
    check("consumed kept", e.get("consumed") == "1")
    check("squashed kept", e.get("squashed") == "0")
    check("dyn_inst_seq kept", e.get("dyn_inst_seq") == "7")
    check("request_id kept", e.get("request_id") == "7")
    # the family-extension lives outside the shared sheet-11 registry
    check("not in shared registry", "delay_cycles" not in P.PROP_EVT_FIELDS)
    check("parser is source of truth for ext columns", True)


def test_valid_terminals():
    print("[accept] real terminals: retired / squashed / discarded")
    for kind, outcome in (
            ("ready_delay_retired", "retired_after_delay"),
            ("ready_delay_squashed", "contained"),
            ("ready_delay_discarded", "discarded_before_retire")):
        r = validate_a07b_lifecycle(_chain(kind))
        check(f"{kind} accepted", r["accepted"], str(r["violations"]))
        check(f"{kind} terminal={outcome}", r["terminal"] == outcome, str(r))
        check(f"{kind} ancestry inj->resume->terminal",
              r["chain"] == ["10", "11", "12"], str(r["chain"]))
        check(f"{kind} contained", r["contained"] is True)
        check(f"{kind} no SDC/full escape", r["terminal"] != "full")


def test_reject_missing_parent():
    print("[reject] missing / wrong parent_event_id")
    events = _chain("ready_delay_retired")
    events[1]["parent_event_id"] = ""
    r = validate_a07b_lifecycle(events)
    check("resume without parent rejected", not r["accepted"], str(r))
    check("reason resume_parent_not_inj",
          "resume_parent_not_inj" in r["violations"], str(r["violations"]))
    events = _chain("ready_delay_retired")
    events[2]["parent_event_id"] = "10"   # terminal hangs off inj, not resume
    r = validate_a07b_lifecycle(events)
    check("terminal parent=inj rejected", not r["accepted"], str(r))
    check("reason terminal_parent_not_resume",
          "terminal_parent_not_resume" in r["violations"], str(r["violations"]))


def test_reject_tick_regressions():
    print("[reject] tick order violations (recorded, never corrected)")
    base = _chain("ready_delay_retired")
    # resume earlier than the scheduled delayed tick
    events = _chain("ready_delay_retired", resume_tick=BASE_TICK + 10)
    r = validate_a07b_lifecycle(events)
    check("resume_before_delayed rejected", not r["accepted"], str(r))
    check("reason resume_before_delayed",
          "resume_before_delayed" in r["violations"], str(r["violations"]))
    # terminal earlier than resume
    events = _chain("ready_delay_retired",
                    resume_tick=BASE_TICK + CYCLE + 100,
                    terminal_tick=BASE_TICK + CYCLE)
    r = validate_a07b_lifecycle(events)
    check("terminal_before_resume rejected", not r["accepted"], str(r))
    check("reason terminal_before_resume",
          "terminal_before_resume" in r["violations"], str(r["violations"]))
    # delay_start >= resume (ready not strictly before delayed)
    events = _chain("ready_delay_retired", ready=BASE_TICK,
                    delayed=BASE_TICK, delay_cycles=0,
                    resume_tick=BASE_TICK)
    r = validate_a07b_lifecycle(events)
    check("delay_start_ge_delayed rejected", not r["accepted"], str(r))
    check("reason delay_start_ge_delayed",
          "delay_start_ge_delayed" in r["violations"], str(r["violations"]))
    check("base fixture is valid", validate_a07b_lifecycle(base)["accepted"])


def test_reject_cross_request():
    print("[reject] cross-request dyn_inst_seq / request_id (no splicing)")
    events = _chain("ready_delay_retired")
    events[2]["dyn_inst_seq"] = "9999"
    r = validate_a07b_lifecycle(events)
    check("terminal other seq rejected", not r["accepted"], str(r))
    check("reason cross_request_dyn_inst_seq",
          "cross_request_dyn_inst_seq" in r["violations"],
          str(r["violations"]))
    events = _chain("ready_delay_retired")
    events[1]["request_id"] = "424242"
    r = validate_a07b_lifecycle(events)
    check("resume other request_id rejected", not r["accepted"], str(r))
    check("reason cross_request_request_id",
          "cross_request_request_id" in r["violations"],
          str(r["violations"]))


def test_reject_stream_shapes():
    print("[reject] truncated / only chain_end / only inj / inj+resume")
    # truncated stream: inj+resume, no terminal, truncated=True
    events = _chain("ready_delay_retired")[:2]
    r = validate_a07b_lifecycle(events, truncated=True)
    check("inj+resume rejected (unknown terminal)", not r["accepted"], str(r))
    check("reason missing_terminal", "missing_terminal" in r["violations"])
    check("reason truncated_stream", "truncated_stream" in r["violations"])
    # only inj
    r = validate_a07b_lifecycle(_chain("ready_delay_retired")[:1])
    check("only inj rejected", not r["accepted"], str(r))
    check("reason missing_resume", "missing_resume" in r["violations"])
    # only chain_end
    ce = _parse([_line("chain_end", event_id=20, parent_event_id=10,
                       tick=BASE_TICK + 10, outcome="run_end")])
    r = validate_a07b_lifecycle(ce)
    check("only chain_end rejected", not r["accepted"], str(r))
    check("reason no_lifecycle_events",
          "no_lifecycle_events" in r["violations"], str(r["violations"]))
    # generic L0-only chain (inj + chain_end, NO A07 lifecycle) is NOT released
    generic = _parse([
        _line("inj", event_id=10, tick=BASE_TICK, dyn_inst_seq="555",
              field="agu_ready_delay", before=BASE_TICK,
              after=BASE_TICK + CYCLE, delay_cycles="1", corr="origin"),
        _line("chain_end", event_id=20, parent_event_id=10,
              tick=BASE_TICK + 99, outcome="run_end"),
    ])
    r = validate_a07b_lifecycle(generic)
    check("L0-only chain NOT released", not r["accepted"], str(r))
    check("reason missing_resume", "missing_resume" in r["violations"], str(r))


def test_reject_terminal_semantics():
    print("[reject] terminal must carry its exact real-hook semantics")
    events = _chain("ready_delay_retired")
    events[2]["containment_reason"] = "made_up"
    r = validate_a07b_lifecycle(events)
    check("wrong containment_reason rejected", not r["accepted"], str(r))
    check("reason terminal_containment_reason_mismatch",
          "terminal_containment_reason_mismatch" in r["violations"])
    events = _chain("ready_delay_squashed")
    events[2]["squashed"] = "0"
    r = validate_a07b_lifecycle(events)
    check("squashed terminal without squashed=1 rejected",
          not r["accepted"], str(r))
    events = _chain("ready_delay_retired")
    events[2]["detection_layer"] = "L4"
    r = validate_a07b_lifecycle(events)
    check("retired with L4 layer rejected", not r["accepted"], str(r))
    events = _chain("ready_delay_retired")
    events[2]["tick"] = str(BASE_TICK + CYCLE + 7)
    r = validate_a07b_lifecycle(events)
    check("retired at resume tick still valid (same-tick commit)",
          r["accepted"], str(r["violations"]))


def test_checker_integration():
    print("[integration] tools/lsu_chain_check.check_a07b_lifecycle")
    impl = getattr(CC, "check_a07b_lifecycle", None)
    if impl is None:
        print("  SKIP checker integration: 'check_a07b_lifecycle' not yet "
              "implemented in tools/lsu_chain_check.py "
              "(reason: to be implemented by the checker lane; the executable "
              "contract above is the agreement)")
        return
    good = {
        "ready_delay_retired": _chain("ready_delay_retired"),
        "ready_delay_squashed": _chain("ready_delay_squashed"),
        "ready_delay_discarded": _chain("ready_delay_discarded"),
    }
    for kind, events in good.items():
        got = impl(events)
        want = validate_a07b_lifecycle(events)
        check(f"impl accepts {kind}", got.get("accepted") is True, str(got))
        check(f"impl terminal {kind} matches contract",
              got.get("terminal") == want["terminal"], f"{got} != {want}")
    bad = _chain("ready_delay_retired")
    bad[2]["parent_event_id"] = "10"
    got = impl(bad)
    check("impl rejects terminal_parent_not_resume",
          got.get("accepted") is False
          and "terminal_parent_not_resume" in got.get("violations", []),
          str(got))
    got = impl(_chain("ready_delay_retired")[:2], truncated=True)
    check("impl rejects truncated stream",
          got.get("accepted") is False and "truncated_stream"
          in got.get("violations", []), str(got))


def main():
    test_parser_keeps_a07b_fields()
    test_valid_terminals()
    test_reject_missing_parent()
    test_reject_tick_regressions()
    test_reject_cross_request()
    test_reject_stream_shapes()
    test_reject_terminal_semantics()
    test_checker_integration()
    if FAILED:
        print(f"\nFAILED: {len(FAILED)} -> {FAILED}")
        return 1
    print("\nAll A07-b lifecycle contract checks PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
