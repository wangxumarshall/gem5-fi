#!/usr/bin/env python3
"""test_lsu_campaign_admission.py — [LSU][MDSPEC][R6-FIXD] campaign 的最终结论
必须**实际调用 binding 门禁** `lsu_chain_check.check_admission`。

真缺陷（实测）：`lsu_campaign.write_chain_report` 只用 `check_chain` 记录判定，
从不调用 binding 的 `check_admission`。于是 `cell_results.json` / `chain_summary.md`
把**门禁会拒绝**的样本照样呈现为一条看着完整的链（`chain_valid: true` + 一个
terminal/provable_to），与"只凭 coverage PASS 就判 READY"是同一类假象。
外部实证：契约里 `T06-F0-W4` / `T08-F0-W4` 的 chain `admitted=True`，恰恰是在
**截断流**上（gzip 无 EOF + stats.txt 0 字节）判出来的。

钉死：
  1. `write_chain_report` 真的调用 `lsu_chain_check.check_admission`（用 spy 计数）；
  2. 门禁拒绝的样本：`admitted is False` + summary 带 `NOT ADMITTED` 前缀 +
     `chain_report.json` 落盘含 `admitted is False`；
  3. 完整链样本：`admitted is True` 且 summary 不带 `NOT ADMITTED`；
  4. 截断流上**不得**认证（`admitted is False`，与 Lane B 口径一致）；
  5. `cell_results.json` 每样本条目带 `admitted`，cell 级带 `admission_status`；
     `chain_summary.md` 增列 `admitted`。

用法：python3 tests/test_lsu_campaign_admission.py   （退出码 0=全 PASS）
"""
import gzip
import json
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC          # noqa: E402
import lsu_chain_check as CHAIN    # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _evt(kind, eid, parent, tick, **kw):
    fields = [f"{k}={v}" for k, v in kw.items() if v is not None]
    return (f"PROP-EVT: kind={kind} event_id={eid} parent_event_id={parent} "
            f"tick={tick} " + " ".join(fields))


# 完整 L0→L5（terminal=full，check_admission admitted=True）——实测构造。
ADMITTED_CHAIN = [
    _evt("inj", 1, "", 100, fault_id=1, run_id="X01-F0-W1", corr="origin"),
    _evt("addr_form", 2, 1, 105, fault_id=1, va="dead", corr="origin"),
    _evt("mem_req", 3, 2, 110, fault_id=1, va="dead", request_id="r7",
         corr="seq_primary"),
    _evt("resp", 4, 3, 115, fault_id=1, request_id="r7", corr="seq_primary"),
    _evt("taint_reg", 5, 4, 118, fault_id=1, request_id="r7", corr="taint_prop"),
    _evt("errant_commit", 6, 5, 120, fault_id=1, dyn_inst_seq=7,
         detection_layer="Hardware", outcome="SDC", contained="0",
         corr="taint_prop"),
]
# 有激活、check_chain 有 fault 路径，但门禁必拒（既不完整也无 containment）。
REFUSED_CHAIN = ADMITTED_CHAIN[:3]


def _write(d: Path, lines, *, stats="simTicks 1\n"):
    d.mkdir(parents=True, exist_ok=True)
    with gzip.open(d / "prop_evt.txt.gz", "wt") as f:
        f.write("\n".join(lines) + "\n")
    if stats is not None:
        (d / "stats.txt").write_text(stats)


def main():
    print("[0] 前提：两个夹具在真检查器下的判定（RED 依据）")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "refused"
        _write(d, REFUSED_CHAIN)
        adm = LC.admission_gate("X01-F0-W1", _read(d), 1, "SDC", 0) \
            if hasattr(LC, "admission_gate") else None
        check("admission_gate 存在（campaign 会调 binding 门禁）",
              hasattr(LC, "admission_gate"), "lsu_campaign.admission_gate 缺失")

    print("[1] write_chain_report 真实调用 check_admission（spy 计数）")
    calls = {"n": 0}
    real = CHAIN.check_admission

    def spy(bundle):
        calls["n"] += 1
        return real(bundle)

    CHAIN.check_admission = spy
    try:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "refused"
            _write(d, REFUSED_CHAIN)
            rep = LC.write_chain_report(d, "X01-F0-W1", 1,
                                        {"outcome": "Detected/Contained"},
                                        exit_code=0)
        check("check_admission 被调用（>0 次）", calls["n"] > 0, f"n={calls['n']}")
    finally:
        CHAIN.check_admission = real

    print("[2] 门禁拒绝的样本必须响亮标记（绝不呈现为完整链）")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "refused"
        _write(d, REFUSED_CHAIN)
        rep = LC.write_chain_report(d, "X01-F0-W1", 1,
                                    {"outcome": "Detected/Contained"}, exit_code=0)
        check("admitted is False", rep.get("admitted") is False,
              str(rep.get("admitted")))
        check("summary 带 NOT ADMITTED 前缀",
              "NOT ADMITTED" in rep.get("summary", ""), rep.get("summary"))
        on_disk = json.loads((d / "chain_report.json").read_text())
        check("chain_report.json 落盘 admitted=False",
              on_disk.get("admitted") is False, str(on_disk.get("admitted")))
        check("admission 明细含 violations",
              bool((rep.get("admission") or {}).get("violations")),
              str(rep.get("admission")))

    print("[3] 完整链样本 admitted=True（不误拒）")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "ok"
        _write(d, ADMITTED_CHAIN)
        rep = LC.write_chain_report(d, "X01-F0-W1", 1, {"outcome": "SDC"},
                                    exit_code=0)
        check("admitted is True", rep.get("admitted") is True, str(rep.get("admitted")))
        check("summary 不带 NOT ADMITTED",
              "NOT ADMITTED" not in rep.get("summary", ""), rep.get("summary"))

    print("[4] 截断流上不得认证（与 Lane B 的 containment 口径一致）")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "trunc"
        _write(d, ADMITTED_CHAIN, stats="")     # 0 字节 stats → 截断
        raw = (d / "prop_evt.txt.gz").read_bytes()
        (d / "prop_evt.txt.gz").write_bytes(raw[: max(1, len(raw) - 6)])
        rep = LC.write_chain_report(d, "T08-F0-W4", 1, {"outcome": "Timeout"},
                                    exit_code=None)
        check("截断流：evidence_truncated True", rep.get("evidence_truncated") is True,
              str(rep.get("evidence_truncated")))
        check("截断流：即使链形完整也不得 certified",
              rep.get("admitted") is False, str(rep.get("admitted")))

    print("[5] cell 级汇总：per-sample admitted + cell admission_status + md 列")
    with tempfile.TemporaryDirectory() as td:
        cell = [""] * 12
        cell[LC.COL_RUNID] = "X01-F0-W1"
        cell[LC.COL_MODEL] = "A01"
        cell[LC.COL_UNIT] = "U"
        cell[LC.COL_FREQ] = "F0"
        args = types.SimpleNamespace(
            phase="trial", trial_target=1, screening_target=1, main_target=1,
            max_seeds_per_cell=1, wilson_stop_hw=0.02, timeout=300,
            fs_timeout=2700)
        refused = {"outcome": "Detected/Contained", "activated": 1,
                   "attempted": 1, "timeout_seconds": 300,
                   "chain_report": {"run_id": "X01-F0-W1",
                                    "sample_run_id": "s1", "admitted": False,
                                    "chain_valid": True, "stream_present": True,
                                    "truncated": False, "evidence_truncated": False,
                                    "event_count": 3, "terminal": None,
                                    "provable_to": None, "beyond": None}}
        original = LC.run_single_cell
        LC.run_single_cell = lambda c, a, s, o: dict(refused)
        try:
            runid, line = LC.run_cell_adaptive(cell, args, Path(td))
        finally:
            LC.run_single_cell = original
        res = json.loads((Path(td) / runid / "cell_results.json").read_text())
        check("per-sample 条目带 admitted=False",
              res["runs"][0].get("admitted") is False,
              str(res["runs"][0].get("admitted")))
        check("cell 级 admission_status=GATE-REFUSED",
              res.get("admission_status") == "GATE-REFUSED",
              str(res.get("admission_status")))
        md = (Path(td) / runid / "chain_summary.md").read_text()
        check("chain_summary.md 增列 admitted", "admitted" in md.lower(),
              md.splitlines()[1] if len(md.splitlines()) > 1 else md[:80])

    print("[6] 模型级阻塞（MODEL_BLOCKED）是独立阻塞：门禁汇总不得覆盖它")
    with tempfile.TemporaryDirectory() as td:
        blocked_model = next(iter(LC.MODEL_BLOCKED))
        cell = [""] * 12
        cell[LC.COL_RUNID] = "T05-F0-W4"
        cell[LC.COL_MODEL] = blocked_model
        cell[LC.COL_UNIT] = "U"
        cell[LC.COL_FREQ] = "F0"
        args = types.SimpleNamespace(
            phase="trial", trial_target=1, screening_target=1, main_target=1,
            max_seeds_per_cell=1, wilson_stop_hw=0.02, timeout=300,
            fs_timeout=2700)
        original = LC.run_single_cell
        LC.run_single_cell = lambda c, a, s, o: {
            "outcome": "Masked", "activated": 1, "attempted": 1,
            "timeout_seconds": 300,
            "chain_report": {"run_id": "T05-F0-W4", "sample_run_id": "s1",
                             "admitted": False, "chain_valid": True,
                             "stream_present": True, "truncated": False,
                             "evidence_truncated": False, "event_count": 3,
                             "terminal": None, "provable_to": None,
                             "beyond": None}}
        try:
            runid, _ = LC.run_cell_adaptive(cell, args, Path(td))
        finally:
            LC.run_single_cell = original
        res = json.loads((Path(td) / runid / "cell_results.json").read_text())
        check("上游模型阻塞保留 admission_status=BLOCKED",
              res.get("admission_status") == "BLOCKED",
              str(res.get("admission_status")))
        check("门禁汇总单列 admission_gate_status=GATE-REFUSED",
              res.get("admission_gate_status") == "GATE-REFUSED",
              str(res.get("admission_gate_status")))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


def _read(d: Path):
    import lsu_prop_fields as P
    ev, _tr = P.read_events(d / "prop_evt.txt.gz")
    return ev


if __name__ == "__main__":
    sys.exit(main())
