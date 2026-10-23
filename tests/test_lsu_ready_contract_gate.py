#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-GATE] ready_contract 的链准入门禁（Agent B）。

钉住：`ready_contract.json` 的 READY **不再** 仅凭 coverage PASS + activated
计数得出——一个 RunID 只有在 (1) family-specific 完整 L0→L5 链，或
(2) 显式 containment（层级+理由+逐层指标，后续层全 N/A(contained)）时才能
READY；否则 BLOCKED 且响亮点名（CHAIN-UNPROVEN / CHAIN-EVIDENCE-MISSING）。

本测试用真实 runid_map/coverage_matrix，但把某一 READY RunID 的 pilot 证据
指向临时合成的 prop_evt（只读真实契约数据，绝不改真实 runs/）。

用法：python3 tests/test_lsu_ready_contract_gate.py   （退出码 0=全 PASS）
"""
import gzip
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_ready_contract as RC   # noqa: E402
import lsu_chain_check as CC      # noqa: E402

RID = "A04-F0-W3"          # 真实 READY 行（契约中 coverage=PASS）
FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("" if cond else f"   <- {detail}"))
    if not cond:
        FAILS.append(name)


def write_evt(path, lines):
    with gzip.open(path, "wt") as f:
        for ln in lines:
            f.write(ln + "\n")


FULL = [
    "PROP-EVT: kind=inj fault_id=1 event_id=0 parent_event_id= tick=1",
    "PROP-EVT: kind=addr_form fault_id=1 event_id=1 parent_event_id=0 tick=2",
    "PROP-EVT: kind=lsq_push fault_id=1 event_id=2 parent_event_id=1 "
    "tick=3 dyn_inst_seq=42",
    "PROP-EVT: kind=mem_req fault_id=1 event_id=3 parent_event_id=2 tick=4",
    "PROP-EVT: kind=resp fault_id=1 event_id=4 parent_event_id=3 tick=5",
    "PROP-EVT: kind=taint_reg fault_id=1 event_id=5 parent_event_id=4 tick=6",
    "PROP-EVT: kind=errant_commit fault_id=1 event_id=6 parent_event_id=5 "
    "tick=7",
    "PROP-EVT: kind=chain_end fault_id=1 event_id=7 parent_event_id=6 tick=8 "
    "outcome=SDC detection_layer=Software contained=0",
]
# activated=1 但链止于 L4 后 Unknown（表 9：绝不推断 Masked/完成）
NO_TAIL = FULL[:6] + [
    "PROP-EVT: kind=chain_end fault_id=1 event_id=6 parent_event_id=5 tick=7 "
    "outcome=run_end detection_layer=None contained=0",
]


def main():
    tmp = Path(tempfile.mkdtemp(prefix="r6gate_"))
    # 真实契约行的输入（只读）
    rid_map = json.loads(RC.DEFAULT_MAP.read_text())
    cov = RC.MDS / "coverage_matrix.md"

    def build(pilots, evt_lines, tag):
        d = tmp / tag
        d.mkdir(parents=True, exist_ok=True)
        p = d / "prop_evt.txt.gz"
        write_evt(p, evt_lines)
        pl = {RID: {"unit": "AGU", "path": str(p), "events": len(evt_lines),
                    "faults": 1, "truncated": False}}
        rows = RC.build_contract(str(RC.DEFAULT_MAP), str(RC.DEFAULT_MATRIX),
                                 str(cov), pilots=pl, evidence_root="/")
        row = next(r for r in rows if r["run_id"] == RID)
        return row, rows

    # 1) 门禁函数存在且判定正确（对照：真链 admitted / 伪链 not）
    check("check_admission 可导入", hasattr(CC, "check_admission"))
    check("chain_admission 可导入", hasattr(RC, "chain_admission"))

    # 2) 完整链 → 该行仍 READY，且 chain.admitted=True
    row, _ = build(None, FULL, "full")
    check("完整链 RunID 保持 READY",
          row["status"] == "READY" and row["chain"]["admitted"] is True,
          f"{row['status']} chain={row.get('chain')}")

    # 3) activated 但链止于 L4/Unknown → 该行由 READY 降为 BLOCKED 且点名
    row, _ = build(None, NO_TAIL, "notail")
    check("无真链的 RunID 降为 BLOCKED（RED→GREEN 核心）",
          row["status"] == "BLOCKED" and row["category"] == "CHAIN-UNPROVEN",
          f"{row['status']} cat={row['category']}")
    check("降级理由响亮点名 RunID 与违规规则",
          RID in row["why"] and "ready_by_chain_end_only" in row["why"],
          row["why"])

    # 4) 无证据 → CHAIN-EVIDENCE-MISSING（不得默认 READY）
    rows = RC.build_contract(str(RC.DEFAULT_MAP), str(RC.DEFAULT_MATRIX),
                             str(cov), pilots={}, evidence_root="/")
    row = next(r for r in rows if r["run_id"] == RID)
    check("无链证据 → BLOCKED/CHAIN-EVIDENCE-MISSING",
          row["status"] == "BLOCKED"
          and row["category"] == "CHAIN-EVIDENCE-MISSING",
          f"{row['status']} cat={row['category']}")

    # 5) 计数自洽保持（READY+PARTIAL+BLOCKED == total）
    from collections import Counter
    st = Counter(r["status"] for r in rows)
    check("计数自洽", sum(st.values()) == 325, str(dict(st)))

    print()
    if FAILS:
        print(f"FAILED ({len(FAILS)}): {FAILS}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
