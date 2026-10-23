#!/usr/bin/env python3
"""test_lsu_handoff.py — campaign handoff/九分类记录缺口单测（[R6-ORACLE] G3）。

审计 G3：缺 stdout 的运行 outcome=INCONCLUSIVE（classify() 早退），而
`lsu_handoff._nine_class_counts` 对它 `continue` —— 一个 activated 样本
被**静默丢弃**。丢弃比 Unknown 更糟：必须响亮、可计数、可追溯。

用法：python3 tests/test_lsu_handoff.py [--only SUBSTR]
退出码 0 = 全 PASS。
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parent
sys.path.insert(0, str(WT / "tools"))
import lsu_handoff as H   # noqa: E402


def obs(outcome=None, activated=1, error=None, runid="A01-F0-W9", sample="s0"):
    l5 = {"outcome": outcome}
    if error:
        l5["error"] = error
    return {"identity": {"runid": runid, "sample": sample, "seed": 1},
            "L0": {"activated": activated}, "L5": l5,
            "execution_complete": True, "evidence_complete": True,
            "chain_complete": False, "needs_backfill": True,
            "missing_levels": ["L3"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="handoff_test_"))
    fails = []

    def check(name, cond, detail=""):
        if args.only and args.only not in name:
            return
        print(("PASS" if cond else "FAIL"), name,
              "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    # ---- 1) 九分类：INCONCLUSIVE / classifier_error 必须显式计数 ----
    obs_list = [
        obs("Masked"),
        obs("SDC"),
        obs("INCONCLUSIVE", error="stdout file missing: /x — 输入不完整"),
        obs("INCONCLUSIVE"),
        obs(error="classifier failed: boom"),
        obs("Crash", activated=0),          # injected-not-activated
    ]
    c = H._nine_class_counts(obs_list)
    check("g3_handoff_inconclusive_recorded",
          c.get("inconclusive") == 2, str(c.get("inconclusive")))
    check("g3_handoff_classifier_error_recorded",
          c.get("classifier_error") == 1, str(c.get("classifier_error")))
    check("g3_handoff_no_silent_drop",
          len(c.get("unrecorded") or []) == 3
          and c.get("samples_total") == 6,
          f"unrecorded={c.get('unrecorded')} n={c.get('samples_total')}")
    check("g3_handoff_decided_counts_unchanged",
          c["five_class"]["Masked"] == 1 and c["five_class"]["SDC"] == 1
          and c["injected_not_activated"] == 1,
          str(c["five_class"]))
    check("g3_handoff_conservation_string",
          "inconclusive" in (c.get("conservation") or "")
          and "classifier_error" in (c.get("conservation") or ""),
          str(c.get("conservation")))
    check("g3_handoff_unrecorded_carries_reason",
          all(u.get("reason") for u in (c.get("unrecorded") or [])),
          str(c.get("unrecorded")))

    # ---- 2) 端到端：campaign handoff 真跑（合成 observation.json） ----
    cdir = tmp / "l3_dry_campaign"
    for i, (runid, outcome, err) in enumerate([
            ("A01-F0-W9", "Masked", None),
            ("A01-F0-W9", "INCONCLUSIVE", "stdout file missing")]):
        d = cdir / f"sample_{i}"
        d.mkdir(parents=True)
        o = obs(outcome, error=err, sample=f"s{i}")
        o["L3"] = {"status": "unsupported", "method": None, "reason": "x"}
        o["L2"] = {"commit_diff": {"first_errant_commit": None}}
        o["chain_status_reason"] = "L3 unsupported"
        (d / "observation.json").write_text(json.dumps(o, ensure_ascii=False))
    h = H.build_campaign_handoff(cdir, tmp / "dry_out")
    check("g3_e2e_handoff_samples",
          h["full_chain"]["samples_total"] == 2, str(h["full_chain"]))
    check("g3_e2e_inconclusive_surfaced",
          h["nine_class"].get("inconclusive") == 1
          and len(h["nine_class"].get("unrecorded") or []) == 1,
          str(h["nine_class"]))
    # CLI 落盘（真子进程；handoff.json + handoff.md）
    r = subprocess.run([sys.executable, str(WT / "tools" / "lsu_handoff.py"),
                        "--campaign-handoff", str(cdir),
                        "--out-dir", str(tmp / "dry_out")],
                       capture_output=True, text=True)
    check("g3_e2e_md_written",
          r.returncode == 0
          and (tmp / "dry_out" / "handoff.md").exists()
          and (tmp / "dry_out" / "handoff.json").exists(),
          f"rc={r.returncode} {r.stdout[-200:]} {r.stderr[-200:]}")

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
