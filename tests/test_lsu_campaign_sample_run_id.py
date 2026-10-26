#!/usr/bin/env python3
"""test_lsu_campaign_sample_run_id.py — [LSU][MDSPEC][R6-FIXD] 报告里的
`sample_run_id` 必须与事件流里的**同一个** id。

真缺陷（实测）：事件流由 `propagation_flags` 写 `--prop_sample_run_id s<seed>`
（run_id=`X01-F0-W1` + sample_run_id=`s1`），而 `write_chain_report` 写
`"sample_run_id": str(seed)`（= `"1"`）—— 报告 `"1"` vs 事件流 `"s1"`，
同一份证据里两个不同的样本标识，下游按 sample_run_id join 时直接错配。

钉死：
  1. write_chain_report 的 sample_run_id == 事件流内的 sample_run_id（"sN"）；
  2. seed=3 → "s3"；
  3. chain_summary.md 的 seed 列显示 s<seed>。

用法：python3 tests/test_lsu_campaign_sample_run_id.py   （退出码 0=全 PASS）
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
import lsu_prop_fields as P        # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _evt(sid, kind, eid, parent, tick, **kw):
    fields = [f"{k}={v}" for k, v in kw.items() if v is not None]
    return (f"PROP-EVT: kind={kind} event_id={eid} parent_event_id={parent} "
            f"tick={tick} run_id=X01-F0-W1 sample_run_id={sid} "
            + " ".join(fields))


def _write(d: Path, sid):
    d.mkdir(parents=True, exist_ok=True)
    body = [
        _evt(sid, "inj", 1, "", 100, fault_id=1, corr="origin"),
        _evt(sid, "addr_form", 2, 1, 105, fault_id=1, va="dead", corr="origin"),
        _evt(sid, "mem_req", 3, 2, 110, fault_id=1, va="dead", request_id="r7",
             corr="seq_primary"),
    ]
    with gzip.open(d / "prop_evt.txt.gz", "wt") as f:
        f.write("\n".join(body) + "\n")
    (d / "stats.txt").write_text("simTicks 1\n")


def main():
    print("[1] write_chain_report 的 sample_run_id 与事件流一致")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "seed1"
        _write(d, "s1")
        rep = LC.write_chain_report(d, "X01-F0-W1", 1, {"outcome": "SDC"},
                                    exit_code=0)
        evt_sids = {e.get("sample_run_id") for e in
                    P.read_events(d / "prop_evt.txt.gz")[0]}
        check("事件流内 sample_run_id == {'s1'}", evt_sids == {"s1"},
              str(evt_sids))
        check("报告 sample_run_id == 's1'（与事件流同源）",
              rep.get("sample_run_id") == "s1", str(rep.get("sample_run_id")))
        on_disk = json.loads((d / "chain_report.json").read_text())
        check("chain_report.json 落盘 sample_run_id == 's1'",
              on_disk.get("sample_run_id") == "s1",
              str(on_disk.get("sample_run_id")))

        d3 = Path(td) / "seed3"
        _write(d3, "s3")
        rep3 = LC.write_chain_report(d3, "X01-F0-W1", 3, {"outcome": "SDC"},
                                     exit_code=0)
        check("seed=3 → sample_run_id == 's3'",
              rep3.get("sample_run_id") == "s3", str(rep3.get("sample_run_id")))

    print("[2] chain_summary.md 的 seed 列显示 s<seed>")
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
        original = LC.run_single_cell
        LC.run_single_cell = lambda c, a, s, o: {
            "outcome": "SDC", "activated": 1, "attempted": 1,
            "timeout_seconds": 300,
            "chain_report": {"run_id": "X01-F0-W1", "sample_run_id": "s1",
                             "admitted": True, "chain_valid": True,
                             "stream_present": True, "truncated": False,
                             "evidence_truncated": False, "event_count": 3,
                             "terminal": "full", "provable_to": "L5",
                             "beyond": None}}
        try:
            runid, _ = LC.run_cell_adaptive(cell, args, Path(td))
        finally:
            LC.run_single_cell = original
        md = (Path(td) / runid / "chain_summary.md").read_text()
        check("chain_summary.md 行首 seed 列为 s1", "| s1 |" in md,
              md.splitlines()[-1] if md else "")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
