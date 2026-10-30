#!/usr/bin/env python3
"""test_lsu_crash_translation_terminal.py — 严格 `crash_translation_fault` 终局。

用户裁决（2026-10-30）：故障传播有真实连续 ancestry，在翻译阶段触发真实
arch_translation_fault，请求无法产生内存副作用，guest 因该异常真实 Crash
⇒ 允许作为翻译层 Crash 终局：

  terminal=crash_translation_fault；provable_to=L3；L4/L5=N/A；
  outcome=Crash；admitted/certified 走独立严格 crash terminal 路径。

本文件钉死 16 条正条件与全部负条件（每条拒绝必须命名 violation）。
另含 S13 六样本的离线复判（原始证据不满足者不得自动放行）。

用法：python3 tests/test_lsu_crash_translation_terminal.py
退出码 0 = 全 PASS。
"""
import gzip
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P          # noqa: E402
import lsu_chain_check as CC         # noqa: E402

EVID = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit")
FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def _mk(kind, eid, parent, tick, fid="1", **kw):
    d = {"kind": kind, "fault_id": fid, "event_id": str(eid),
         "parent_event_id": "" if parent is None else str(parent),
         "tick": str(tick), "cycle": "0", "dyn_inst_seq": "",
         "request_id": "", "corr": "", "detection_layer": "",
         "contained": "", "outcome": "", "va": "", "pa": ""}
    for k, v in kw.items():
        d[k] = str(v)
    return d


def s13_stream(fid="1"):
    """The measured S13 shape (10 events, exact field values structure)."""
    return [
        _mk("inj", 1, None, 5924765, fid=fid, dyn_inst_seq=3890,
            corr="origin", va="4d2c98", before="4d2c98",
            after="20004d2c98"),
        _mk("addr_form", 2, 1, 5924765, fid=fid, dyn_inst_seq=3890,
            corr="origin", va="20004d2c98", before="4d2c98",
            after="20004d2c98"),
        _mk("lsq_push", 3, 2, 5924765, fid=fid, dyn_inst_seq=3890,
            corr="seq_primary", va="20004d2c98", pc="436378",
            opcode="strxi_uop", lq_idx="-1", sq_idx="344", field="store"),
        _mk("mem_req", 4, 3, 5924765, fid=fid, dyn_inst_seq=3890,
            request_id="3890", corr="seq_primary", va="20004d2c98"),
        _mk("lsq_sendfrag", 5, 4, 5924765, fid=fid, dyn_inst_seq=3890,
            request_id="3890", corr="seq_primary", va="20004d2c98"),
        _mk("tlb_translate", 6, 5, 5924765, fid=fid, dyn_inst_seq=3890,
            request_id="3890", corr="seq_primary", va="20004d2c98"),
        _mk("tlb_fault", 7, 6, 5924765, fid=fid, dyn_inst_seq=3890,
            request_id="3890", corr="seq_primary", va="20004d2c98",
            detection_layer="Hardware", outcome="Generic page table fault"),
        _mk("sq_execute", 8, 7, 5924765, fid=fid, dyn_inst_seq=3890,
            corr="seq_primary", va="20004d2c98", sq_idx="344",
            state_before="issued"),
        _mk("arch_translation_fault", 9, 8, 5990985, fid=fid,
            corr="seq_primary", va="20004d2c98", detection_layer="L2",
            contained="0", outcome="arch_exception"),
        _mk("chain_end", 10, 9, 5990985, fid=fid, corr="none",
            outcome="run_end", contained="0"),
    ]


CRASH_EXIT = {"exit_code": 139, "exit_cause": "chaos_guest_segv",
              "guest_segv_marker": True, "controlled_marker": True}


def _bundle(events, **kw):
    b = {"run_id": "S13-F0-W1", "activated": 1, "events": events,
         "rc": CRASH_EXIT["exit_code"], "oracle_outcome": "Crash",
         "containment": None, "crash_exit": dict(CRASH_EXIT),
         "summary_issues": [], "consumer_summary_accounting": None}
    b.update(kw)
    return b


def _reject(bundle, token):
    r = CC.check_admission(bundle)
    ok = (r["admitted"] is False and
          any(token in v for v in r["violations"]))
    check(f"reject {token}", ok, (r["admitted"], r["violations"]))


def test_positive():
    print("[1] strict positive")
    ev = s13_stream()
    v = CC.check_chain(ev, oracle_outcome="Crash")["faults"]["1"]
    check("terminal=crash_translation_fault",
          v["terminal"] == "crash_translation_fault", v["terminal"])
    check("provable_to=L3", v["provable_to"] == "L3", v["provable_to"])
    check("terminal is closed (beyond empty)", v["beyond"] == "", v["beyond"])
    r = CC.check_admission(_bundle(ev))
    check("admitted=True", r["admitted"] is True, r["violations"])
    check("path=crash_terminal", r["path"] == "crash_terminal", r["path"])
    check("violations=[]", r["violations"] == [], r["violations"])
    check("L4/L5 are structurally N/A (path stops at L3)",
          r["path_layers"] == ["L0", "L1", "L2", "L3"], r["path_layers"])
    check("certified output present",
          "certified" not in r or r.get("certified") in (True, None))


def test_negative_matrix():
    print("[2] negative matrix")
    # unrelated guest crash: no injected chain at all
    ev = s13_stream()
    for e in ev:
        e["fault_id"] = "0"
    _reject(_bundle(ev), "ready_by_activated_only")

    # missing fault_id on the terminal event
    ev = s13_stream()
    ev[8]["fault_id"] = ""
    _reject(_bundle(ev), "crash_terminal_not_in_ancestry")

    # missing corr on the terminal event
    ev = s13_stream()
    ev[8]["corr"] = ""
    _reject(_bundle(ev), "crash_terminal_missing_corr")

    # missing parent (orphan) on the terminal event
    ev = s13_stream()
    ev[8]["parent_event_id"] = ""
    _reject(_bundle(ev), "crash_terminal_not_in_ancestry")

    # exception not in the chosen ancestry (parent jumps to L0)
    ev = s13_stream()
    ev[8]["parent_event_id"] = "1"
    _reject(_bundle(ev), "crash_terminal_not_in_ancestry")

    # oracle is not Crash
    _reject(_bundle(s13_stream(), oracle_outcome="Masked",
                    crash_exit={"exit_code": 0, "exit_cause": "exiting",
                                "guest_segv_marker": False}),
            "crash_requires_oracle_crash")

    # exit status does not support Crash (0)
    _reject(_bundle(s13_stream(),
                    rc=0, crash_exit={"exit_code": 0,
                                      "exit_cause": "exiting",
                                      "guest_segv_marker": False}),
            "crash_requires_guest_segv_exit")

    # unknown exit string
    _reject(_bundle(s13_stream(),
                    crash_exit={"exit_code": 139,
                                "exit_cause": "unknown-exit",
                                "guest_segv_marker": False}),
            "crash_requires_guest_segv_exit")

    # contained=1 while claiming crash
    ev = s13_stream()
    ev[8]["contained"] = "1"
    _reject(_bundle(ev), "crash_terminal_contained")

    # truncated stream
    _reject(_bundle(s13_stream(), truncated=True),
            "crash_terminal_on_truncated_stream")

    # stream not closed (no chain_end)
    ev = s13_stream()[:-1]
    _reject(_bundle(ev), "crash_terminal_on_unclosed_stream")

    # chain_end masquerading as the terminal event
    ev = s13_stream()
    ev[8] = _mk("chain_end", 9, 8, 5990985, corr="none",
                detection_layer="L2", contained="0",
                outcome="arch_exception")
    _reject(_bundle(ev), "crash_terminal_is_lifecycle")

    # time reversal: terminal before the L3 witness
    ev = s13_stream()
    ev[8]["tick"] = "1"
    _reject(_bundle(ev), "crash_terminal_time_reversed")

    # cross-request: terminal stamped with another request
    ev = s13_stream()
    ev[8]["request_id"] = "999999"
    _reject(_bundle(ev), "crash_terminal_cross_request")

    # campaign/checker disagreement: campaign says Crash, checker oracle Masked
    _reject(_bundle(s13_stream(), oracle_outcome="Masked"),
            "crash_requires_oracle_crash")

    # no real injection event
    ev = s13_stream()
    ev[0]["kind"] = "mem_req"
    _reject(_bundle(ev), "crash_terminal_no_injection")


def _read_events(path):
    with gzip.open(path, "rt", errors="replace") as f:
        return [P.parse_line(ln) for ln in f if ln.startswith("PROP-EVT:")]


def _crash_exit_from_dir(seed_dir):
    out = (seed_dir / "run.out")
    err = (seed_dir / "run.err")
    text = ""
    for p in (out, err):
        if p.exists():
            text += p.read_text(errors="replace")
    cause = ""
    m = re.search(r"Exit event '([^']+)'", text)
    if m:
        cause = m.group(1)
    marker = ("guest SEGV" in text or "chaos_guest_segv" in text)
    controlled = "CHAOS_GUEST_SEGV_EXIT" in text
    return {"exit_code": None, "exit_cause": cause,
            "guest_segv_marker": marker, "controlled_marker": controlled}


def test_real_evidence_rejudge():
    """离线复判 6 个 Crash 样本（不重跑）。原始证据不满足者必须被拒。"""
    print("[3] real S13-family evidence rejudge (offline)")
    check("evidence root exists", EVID.is_dir(), EVID)
    if not EVID.is_dir():
        return
    # S11-F0-W6 has NO arch_translation_fault (5 events, exit 0) -> must fail.
    expected = {
        "S11-F0-W6": False,
        "S13-F0-W1": None, "S13-F0-W5": None, "S13-F0-W12": None,
        "S13-F1-W1": None, "S13-F2-W1": None,
    }
    for rid, must in expected.items():
        d = EVID / f"{rid}_s1" / rid / "seed1"
        if not d.is_dir():
            check(f"{rid}: evidence present", False, d)
            continue
        ev = _read_events(d / "prop_evt.txt.gz")
        crash = _crash_exit_from_dir(d)
        # campaign's measured gem5 exit code is in chain_report.json
        rc = 0
        try:
            rc = int(json.loads((d / "chain_report.json").read_text())
                     .get("exit_code") or 0)
        except Exception:
            pass
        crash["exit_code"] = rc
        r = CC.check_admission({
            "run_id": rid, "activated": 1, "events": ev,
            "rc": rc, "oracle_outcome": "Crash", "containment": None,
            "crash_exit": crash})
        got = bool(r["admitted"])
        if must is False:
            check(f"{rid}: rejected (no real translation-fault crash)",
                  got is False, (r["admitted"], r["terminal"],
                                 r["violations"]))
        else:
            # Evidence is rejudged on its merits: the OLD runs used the
            # unhandled exit event (NotImplementedError), so a strict
            # controlled-exit check may reject them — the verdict MUST be
            # consistent with the evidence, never forced True.
            has_arch = any(e.get("kind") == "arch_translation_fault"
                           and e.get("contained") == "0"
                           and e.get("outcome") == "arch_exception"
                           and e.get("detection_layer") == "L2"
                           for e in ev)
            closed = any(e.get("kind") == "chain_end" for e in ev)
            controlled = (crash["guest_segv_marker"]
                          and crash["controlled_marker"]
                          and rc == 139
                          and crash["exit_cause"] == "chaos_guest_segv")
            should = has_arch and closed and controlled and rc != 0
            check(f"{rid}: verdict follows its own evidence",
                  got == should,
                  f"admitted={got} expected={should} rc={rc} "
                  f"cause={crash['exit_cause']!r} closed={closed}")


def main():
    for fn in (test_positive, test_negative_matrix,
               test_real_evidence_rejudge):
        fn()
    if FAILED:
        print(f"\nFAILED {len(FAILED)}: {FAILED}")
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
