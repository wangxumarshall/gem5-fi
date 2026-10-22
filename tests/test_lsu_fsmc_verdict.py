#!/usr/bin/env python3
"""[MDSPEC][R4-8-FSMC] 35 项 FS-MULTICORE 逐项裁决的机读钉死。

钉四件事（任一被破坏都 FAIL，不允许静默漂移）：
  1. 裁决表覆盖恰好 35 格、与任务书原文逐字一致、每格 reason 非空且
     已把 blanket 短语（"litmus needs multi-core FS" / "PARSEC needs
     multi-core FS"）换掉；每格引用的证据产物在仓库里真实存在；
  2. 分组计数 = 10（载体就绪·残留阻塞）/4（注入器宿主互斥）/15（模型语义
     未实现）/6（规格负载身份）；
  3. **每一格当前仍被 campaign 拒绝**（resolve_cell → flags=None）——
     谁把某格接通，本测试就红，逼着把裁决表一起改；
  4. campaign 的 WL_BLOCKED 理由串与裁决表一致（不含 blanket 短语，且仍带
     "multicore-fs:" 前缀以便 triage 的互斥分类计数不漂移）。

用法：python3 tests/test_lsu_fsmc_verdict.py   （rc 0 = 全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as lc          # noqa: E402
import lsu_fsmc_verdict as V       # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + (("   <- " + str(detail)) if not cond else ""))
    if not cond:
        FAILS.append(name)


def _cell(runid, model, freq, workload):
    """构造一个 campaign cell 行（列索引取自 lc 的常量）。"""
    n = max(lc.COL_RUNID, lc.COL_MODEL, lc.COL_FREQ, lc.COL_WORKLOAD) + 1
    row = [""] * n
    row[lc.COL_RUNID] = runid
    row[lc.COL_MODEL] = model
    row[lc.COL_FREQ] = freq
    row[lc.COL_WORKLOAD] = workload
    return row


def _workload_for(runid):
    return ("Atomic-Litmus 并发探针（MP/SB/LB/IRIW/Dekker/…）"
            if runid.endswith("W7") else
            "PARSEC-Selected 多线程应用（dedup/ferret/streamcluster）")


def main():
    probs, info = V.check()
    check("verdict_table_selfcheck", not probs, probs)
    check("verdict_row_count_35", info["n"] == 35, info["n"])
    check("verdict_group_counts_10_4_15_6",
          info["counts"] == {V.CARRIER_READY_RESIDUAL_BLOCKED: 10,
                             V.BLOCKED_INJECTOR_HOST: 4,
                             V.BLOCKED_MODEL_UNIMPL: 15,
                             V.BLOCKED_WORKLOAD_IDENTITY: 6},
          info["counts"])

    # (2) 每格仍被 campaign 拒绝：ledger 与工具必须一致，不得静默解锁。
    still_blocked = []
    for rid in V.TASK_LIST:
        cell = _cell(rid, V.MODEL_OF[rid], rid.split("-")[1],
                     _workload_for(rid))
        flags, _golden, reason = lc.resolve_cell(cell)
        if flags is not None:
            still_blocked.append((rid, "NOT-BLOCKED"))
        elif not reason:
            still_blocked.append((rid, "no reason"))
        elif not reason.startswith("blocked(") and not reason.startswith("deferred"):
            still_blocked.append((rid, f"suspicious reason: {reason[:40]}"))
    check("all_35_still_refused_by_campaign_with_a_reason",
          not still_blocked, still_blocked)

    # (3) WL_BLOCKED 的理由串与裁决表一致。
    for key, banned in (("Atomic-Litmus", "litmus needs multi-core FS"),
                        ("PARSEC", "PARSEC needs multi-core FS")):
        reason = lc.WL_BLOCKED.get(key, "")
        check(f"WL_BLOCKED[{key}] no longer carries the blanket phrase",
              banned not in reason, reason)
        check(f"WL_BLOCKED[{key}] still names multicore-fs (triage bucket "
              f"must not silently change)", "multicore-fs:" in reason, reason)
        check(f"WL_BLOCKED[{key}] cites the R4-8-FSMC artifacts",
              "R4-8-FSMC" in reason, reason)

    # (4) 模型级理由：O05/O06/O07 的"只需多核"说法必须补上模型缺口。
    for model in ("O05", "O06", "O07"):
        reason = lc.MODEL_BLOCKED.get(model, "")
        check(f"MODEL_BLOCKED[{model}] names the model gap, not only "
              f"multi-core", "语义" in reason or "跟踪" in reason, reason)

    print(f"\nFAILURES: {FAILS if FAILS else '无'}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
