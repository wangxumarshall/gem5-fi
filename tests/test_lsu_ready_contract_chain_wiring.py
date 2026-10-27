#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-GATE-L29] 链准入门禁必须对**每一行**评估（含上游已阻塞行）。

动机（L28 实测缺陷，三处）：
  1. `build_contract` 只在行**已经**是 READY/PARTIAL 时才调用 `chain_admission`；
     于是链门禁是一条"上游先放行才生效"的门 —— 上游不放行时它永不执行。
  2. 24 个 T 系列行在 `runid_map.status_reasons` 里被预判 FS-INFRA ⇒ `chain`
     恒为 `null`，门禁在它们身上从未运行。
  3. 但 L28 直接调用证明 containment 通路**是通的**：`containment_from_events`
     + `check_admission` 对 T08-F0-W4（`tlb_translate_result` /
     `field=walk_refill_lost` / `detection_layer=L2` / `contained=1` /
     `outcome=translation_blocked`）判 admitted=True。

本测试把修好的接线钉死：链门禁是**附加**门禁，对每一行都运行并记录结果；
上游阻塞是**独立**阻塞，不因链准入而解除；上游可跑的行仍须链准入才能 READY。

  [1] 325 行的 `chain` 全部非 null（门禁对每行都评估并记录）；
  [2] 上游阻塞（FS-INFRA）但链可准入的行：status 仍 BLOCKED、category 仍
      FS-INFRA（独立阻塞不得被链准入解除），且 chain.admitted=True 如实记录；
  [3] 对照组：上游阻塞 + 链**不可**准入 ⇒ chain.admitted=False，category 不变；
  [4] 反向对照：上游可跑（READY）+ 链准入 ⇒ READY（修复不得堵死 READY 路径）。

使用真实 runid_map / coverage_matrix；证据用临时目录合成（只读真实 runs/ 的
T08 流），绝不改真实台账。

用法：python3 tests/test_lsu_ready_contract_chain_wiring.py   （退出码 0=全 PASS）
"""
import gzip
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_ready_contract as RC   # noqa: E402

T08_SRC = Path(os.environ.get(
    "LSU_R6_T08_EVT",
    "/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_C_T08-F0-W4/T08-F0-W4/seed1/"
    "prop_evt.txt.gz"))
FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("" if cond else f"   <- {detail}"))
    if not cond:
        FAILS.append(name)


def write_evt(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as f:
        for ln in lines:
            f.write(ln + "\n")


# 真链（AGU 族 L0→L5 全边 + 真实检测事件 L5）
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
    "PROP-EVT: kind=errant_commit fault_id=1 event_id=7 parent_event_id=6 "
    "tick=8 detection_layer=Software outcome=SDC contained=0 corr=taint_prop",
]
# 伪链：activated 但只有生命周期 chain_end（L5 不得由它补造）
NO_TAIL = FULL[:6] + [
    "PROP-EVT: kind=chain_end fault_id=1 event_id=6 parent_event_id=5 tick=7 "
    "outcome=run_end detection_layer=None contained=0 corr=none",
]

RID_READY = "A04-F0-W3"      # 契约中上游可跑（coverage PASS）的真实行
# [R6-PROPAGATION-V3] T08-F0-W4 left FS-INFRA (now PARTIAL-SUBMODEL).  Use a
# row that is still upstream FS-INFRA blocked (T05-F6-W4, policy-excluded F6)
# to keep testing "independent upstream block is not removed by chain access".
RID_FSINFRA = "T05-F6-W4"

# [R6-FIXB] 已收口的合法含住流（含住主张须建立在完整收口的证据流上）：
# tlb_lookup L1 → tlb_translate_result(dl=L2 contained=1) → chain_end 收口。
CLOSED_CONTAINED = [
    f"PROP-EVT: kind=inj run_id={RID_FSINFRA} fault_id=1 event_id=0 "
    "parent_event_id= tick=1 corr=origin",
    f"PROP-EVT: kind=tlb_lookup run_id={RID_FSINFRA} fault_id=1 event_id=1 "
    "parent_event_id=0 tick=2 dyn_inst_seq=7 request_id=7 va=1000 "
    "entry_index=1 field=post_lookup state_before=x state_after=y corr=origin",
    f"PROP-EVT: kind=tlb_translate_result run_id={RID_FSINFRA} fault_id=1 "
    "event_id=2 parent_event_id=1 tick=3 dyn_inst_seq=7 request_id=7 va=1000 "
    "pa=2000 field=walk_refill_lost detection_layer=L2 contained=1 "
    "outcome=translation_blocked corr=origin",
    f"PROP-EVT: kind=chain_end run_id={RID_FSINFRA} fault_id=1 event_id=3 "
    "parent_event_id=2 tick=4 outcome=run_end detection_layer=None "
    "contained=0 corr=none",
]


def build(pilots, evidence_root):
    return RC.build_contract(str(RC.DEFAULT_MAP), str(RC.DEFAULT_MATRIX),
                             str(RC.MDS / "coverage_matrix.md"),
                             pilots=pilots, evidence_root=str(evidence_root))


def main():
    tmp = Path(tempfile.mkdtemp(prefix="r6l29_"))

    # [1] 真实注册表 + 默认证据根：每行都必须有 chain 判定（非 null）
    real = RC._load_pilots()
    rows = build(real, RC._evidence_root())
    missing = [r["run_id"] for r in rows if r.get("chain") is None]
    check("每一行都带链门禁判定（无 chain=null）", not missing,
          f"{len(missing)} 行 chain=null，例：{missing[:8]}")

    # [2] 上游 FS-INFRA 阻塞 + 链判定在案：status/category 不变
    d = tmp / "e2"
    # A truncated (no chain_end) containment stream: the containment claim is
    # not closed, so the chain is not admitted.
    write_evt(d / RID_FSINFRA / "seed1" / "prop_evt.txt.gz",
              CLOSED_CONTAINED[:-1])
    pl = {RID_FSINFRA: {"unit": "L1d-TLB",
                        "path": f"{RID_FSINFRA}/seed1/prop_evt.txt.gz",
                        "faults": 1, "truncated": True}}
    e2 = build(pl, d)
    row = next(r for r in e2 if r["run_id"] == RID_FSINFRA)
    check("[2] 上游阻塞 + 链判定在案 ⇒ status 仍 BLOCKED",
          row["status"] == "BLOCKED", f"{row['status']}")
    check("[2] category 仍为上游独立阻塞 FS-INFRA",
          row["category"] == "FS-INFRA", f"{row['category']}")
    check("[2] 门禁确实运行过且如实记录（chain 判定非 null）",
          (row.get("chain") or {}).get("admitted") is not None,
          str(row.get("chain")))
    check("[2] 截断流 ⇒ chain.admitted=False（缺陷 #5 修正）",
          (row.get("chain") or {}).get("admitted") is False
          and "containment_on_unclosed_stream"
          in " ".join((row.get("chain") or {}).get("violations") or []),
          str(row.get("chain")))
    check("[2] chain.terminal=detected_contained",
          (row.get("chain") or {}).get("terminal") == "detected_contained",
          str((row.get("chain") or {}).get("terminal")))

    # [3] 对照组：上游阻塞 + 链不可准入 ⇒ admitted=False，category 不变
    d3 = tmp / "e3"
    write_evt(d3 / RID_FSINFRA / "seed1" / "prop_evt.txt.gz", NO_TAIL)
    pl3 = {RID_FSINFRA: {"unit": "L1d-TLB",
                         "path": f"{RID_FSINFRA}/seed1/prop_evt.txt.gz",
                         "faults": 1, "truncated": False}}
    row = next(r for r in build(pl3, d3) if r["run_id"] == RID_FSINFRA)
    check("[3] 伪链 ⇒ chain.admitted=False 且 category 仍 FS-INFRA",
          row["status"] == "BLOCKED" and row["category"] == "FS-INFRA"
          and (row.get("chain") or {}).get("admitted") is False,
          f"{row['status']}/{row['category']}/{row.get('chain')}")

    # [4] 反向对照：上游可跑 + 链准入 ⇒ READY（门禁不得堵死 READY 路径）
    d4 = tmp / "e4"
    write_evt(d4 / RID_READY / "seed1" / "prop_evt.txt.gz", FULL)
    pl4 = {RID_READY: {"unit": "AGU",
                       "path": f"{RID_READY}/seed1/prop_evt.txt.gz",
                       "faults": 1, "truncated": False}}
    row = next(r for r in build(pl4, d4) if r["run_id"] == RID_READY)
    check("[4] 上游可跑 + 链准入 ⇒ READY",
          row["status"] == "READY"
          and (row.get("chain") or {}).get("admitted") is True,
          f"{row['status']} chain={row.get('chain')}")

    # [5] chain_gate 汇总必须覆盖全体并列出"上游阻塞但链已准入"的行。
    # [R6-FIXB] 用**已收口**的合法含住样本（同一 RID，上游 FS-INFRA 不变）——
    # 真实 T08 截断流不再准入（[2]），故此处以合成收口流证明汇总字段仍会列出
    # "准入但被上游独立阻塞"的行（准入≠解锁）。
    d5 = tmp / "e5"
    write_evt(d5 / RID_FSINFRA / "seed1" / "prop_evt.txt.gz", CLOSED_CONTAINED)
    pl5 = {RID_FSINFRA: {"unit": "L1d-TLB",
                         "path": f"{RID_FSINFRA}/seed1/prop_evt.txt.gz",
                         "faults": 1, "truncated": False}}
    e5rows = build(pl5, d5)
    cg = RC.chain_gate_summary(e5rows) if hasattr(RC, "chain_gate_summary") \
        else None
    check("[5] 收口含住样本：链已准入且被上游独立阻塞仍 BLOCKED",
          all(r["status"] == "BLOCKED" for r in e5rows
              if r["run_id"] == RID_FSINFRA)
          and (next(r for r in e5rows
                    if r["run_id"] == RID_FSINFRA).get("chain") or {}
               ).get("admitted") is True,
          str(next(r for r in e5rows if r["run_id"] == RID_FSINFRA)
              .get("chain")))
    check("[5] chain_gate 汇总列出上游阻塞但链已准入的行",
          cg is not None and RID_FSINFRA in cg["blocked_upstream_admitted"],
          str(cg))
    check("[5] chain_gate.recorded == 总行数",
          cg is not None and cg["recorded"] == len(e5rows), str(cg))

    print()
    if FAILS:
        print(f"FAILED ({len(FAILS)}): {FAILS}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
