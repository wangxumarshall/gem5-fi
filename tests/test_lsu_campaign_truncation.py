#!/usr/bin/env python3
"""test_lsu_campaign_truncation.py — [LSU][R6-CAMPAIGN] 截断证据 LOUD 契约。

背景（真实现场，2026-10-23）：FS 运行远超其 timeout 被杀在写入中途，留下不完整传播流：
  * runs/lsu/r6_tlb_C_T08-F0-W4/T08-F0-W4/seed1/prop_evt.txt.gz (635 B) →
    gzip.open(..).read() 抛 EOFError: ... end-of-stream marker ...；stats.txt 存在但 0 字节；
  * runs/lsu/r6_tlb_negative2/seed1/prop_evt.txt.gz (238 B) → 同一 EOFError；stats.txt 0 字节。

钉死三件事：
  1. detect_evidence_truncation(outdir) 对 (a) 不完整 gzip 流、(b) 缺失或 0 字节
     stats.txt 都判 True 并给出**响亮** reason；完整流 + 非空 stats.txt 判 False；
  2. write_chain_report 把该结果显式写入报告：evidence_truncated / truncation_reason /
     chain_valid，summary 前缀响亮告警——绝不静默当作完整链；
  3. unit pilot 的 run_one 把 evidence_truncated 折进 verdict（响亮，不静默 pass）。

用法：python3 tests/test_lsu_campaign_truncation.py   （退出码 0=全 PASS）
"""
import gzip
import json
import sys
import tempfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


BODY = ("# prop-evt v1: header\n"
        "PROP-EVT: kind=inj run_id=X sample_run_id=s1 fault_id=1 event_id=0 tick=10\n"
        "PROP-EVT: kind=tlb_fault run_id=X sample_run_id=s1 fault_id=1 event_id=1 "
        "tick=13 detection_layer=Hardware contained= outcome=GenericPageTableFault\n")


def _write_partial_gz(p):
    """Z_SYNC_FLUSH-ed prefix with NO gzip trailer = killed mid-write."""
    co = zlib.compressobj(9, zlib.DEFLATED, 16 + 15)
    Path(p).write_bytes(co.compress(BODY.encode()) + co.flush(zlib.Z_SYNC_FLUSH))


def _write_complete_gz(p):
    with gzip.open(p, "wt") as f:
        f.write(BODY)


def main():
    print("[1] detect_evidence_truncation 形状")
    check("函数存在", hasattr(LC, "detect_evidence_truncation"),
          "lsu_campaign.detect_evidence_truncation 缺失")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # (a) 不完整 gzip + 0 字节 stats.txt
        d1 = root / "partial_gz_zerostats"
        d1.mkdir()
        _write_partial_gz(d1 / "prop_evt.txt.gz")
        (d1 / "stats.txt").write_bytes(b"")
        t1, r1 = LC.detect_evidence_truncation(d1)
        check("不完整 gzip + 0 字节 stats → True", t1 is True, f"{t1} {r1}")
        check("reason 响亮（含 prop_evt / gzip 字样）",
              any("prop_evt" in x for x in r1) and any(
                  ("gzip" in x or "incomplete" in x or "EOF" in x) for x in r1),
              str(r1))
        check("reason 计 0 字节 stats", any("stats.txt" in x for x in r1), str(r1))

        # (b) 完整 gzip 但 stats.txt 缺失 → 仍截断
        d2 = root / "complete_gz_nostats"
        d2.mkdir()
        _write_complete_gz(d2 / "prop_evt.txt.gz")
        t2, r2 = LC.detect_evidence_truncation(d2)
        check("缺 stats.txt → True", t2 is True, f"{t2} {r2}")
        check("reason 含 stats.txt missing", any("stats.txt" in x and
              ("missing" in x or "缺" in x) for x in r2), str(r2))

        # (c) 完整 gzip + 非空 stats.txt → 不截断
        d3 = root / "good"
        d3.mkdir()
        _write_complete_gz(d3 / "prop_evt.txt.gz")
        (d3 / "stats.txt").write_text("simSeconds 0.1\n")
        t3, r3 = LC.detect_evidence_truncation(d3)
        check("完整流 + 非空 stats → False", t3 is False and r3 == [],
              f"{t3} {r3}")

    print("[2] write_chain_report 响亮标记（绝不静默完整链）")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _write_partial_gz(d / "prop_evt.txt.gz")
        (d / "stats.txt").write_bytes(b"")
        rep = LC.write_chain_report(d, "T08-F0-W4", 1,
                                    {"outcome": "Timeout"}, exit_code=None)
        check("evidence_truncated=True", rep.get("evidence_truncated") is True,
              str(rep))
        check("truncation_reason 非空", bool(rep.get("truncation_reason")),
              str(rep.get("truncation_reason")))
        check("chain_valid=False（不得当作完整链）",
              rep.get("chain_valid") is False, str(rep.get("chain_valid")))
        check("summary 响亮前缀（TRUNCAT）", "TRUNCAT" in rep.get("summary", ""),
              str(rep.get("summary")))
        check("报告落盘含 evidence_truncated",
              json.loads((d / "chain_report.json").read_text())
              .get("evidence_truncated") is True, "chain_report.json 未标")

        # 完整样本不误报
        d2 = Path(td) / "good"
        d2.mkdir()
        _write_complete_gz(d2 / "prop_evt.txt.gz")
        (d2 / "stats.txt").write_text("simSeconds 0.1\n")
        rep2 = LC.write_chain_report(d2, "T05-F0-W4", 1,
                                     {"outcome": "Masked"}, exit_code=0)
        check("完整样本 evidence_truncated=False",
              rep2.get("evidence_truncated") is False, str(rep2))
        check("完整样本 chain_valid=True", rep2.get("chain_valid") is True,
              str(rep2))

    print("[3] 真实截断文件（现场证据）")
    # runs/lsu lives in the MAIN tree, not the worktree — try both explicitly.
    import os
    cands = [os.environ.get("LSU_RUNS_LSU"),
             str(ROOT.parent / "runs/lsu"),
             str(ROOT.parent.parent.parent / "runs/lsu")]
    runs_lsu = next((Path(c) for c in cands if c and Path(c).is_dir()),
                    ROOT.parent / "runs/lsu")
    real = [
        (runs_lsu / "r6_tlb_C_T08-F0-W4/T08-F0-W4/seed1", True),
        (runs_lsu / "r6_tlb_negative2/seed1", True),
        (runs_lsu / "r6_tlb_pilot2/T05-F0-W4/seed1", False),
    ]
    for p, expect in real:
        if not p.exists():
            print(f"[SKIP] {p}（不存在）")
            continue
        got, reasons = LC.detect_evidence_truncation(p)
        check(f"{p.name} evidence_truncated={expect}", got is expect,
              f"{got} {reasons}")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
