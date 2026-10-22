#!/usr/bin/env python3
"""[MDSPEC][R4-9-FSMC-A] 35 项 FS-MULTICORE 逐项裁决的机读钉死。

钉五件事（任一被破坏都 FAIL，不允许静默漂移）：
  1. 裁决表覆盖恰好 35 格、与任务书原文逐字一致、每格 reason 非空且已把
     blanket 短语（"litmus needs multi-core FS" / "PARSEC needs multi-core
     FS"）换掉；每格引用的证据产物在仓库里真实存在；**载体指纹 sha256 与磁盘
     实测一致**；
  2. 分组计数 = 4（routable·待取样本）/ 6（档位语义未实现）/ 4（注入器宿主
     互斥）/ 15（模型语义未实现）/ 6（规格负载身份）；
  3. **双向断言**（R4-9-FSMC-A 收紧）：
       * 声明 `CARRIER_ROUTED_PENDING_RUN` 的 4 格，若 2 核检查点在场，必须真的
         resolve 出 FS flag 集、且 golden == FSMC_GOLDEN_FINAL；检查点不在场时
         必须给出 `fsmc-infra` 理由（**不是**静默通过）；
       * 声明 `BLOCKED_TRIGGER_TIER_UNIMPL` 的 6 格必须**真的被拒**，且理由指向
         档位语义；
       * 其余 25 格仍被拒且有理由。
  4. campaign 的 WL_BLOCKED 理由串与裁决表一致（不含 blanket 短语，且仍带
     "multicore-fs:" 前缀以便 triage 的互斥分类计数不漂移）；
  5. 断言可跑：本测试不联网、不跑 gem5，全部是纯 Python 判定。

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
    check("verdict_group_counts_4_6_4_15_6",
          info["counts"] == {V.CARRIER_ROUTED_PENDING_RUN: 4,
                             V.BLOCKED_TRIGGER_TIER_UNIMPL: 6,
                             V.BLOCKED_INJECTOR_HOST: 4,
                             V.BLOCKED_MODEL_UNIMPL: 15,
                             V.BLOCKED_WORKLOAD_IDENTITY: 6},
          info["counts"])

    # (2) 载体指纹必须与磁盘实测一致（V.check 已做，这里显式再报一次）。
    for rel, want in V.CARRIER_SHA256.items():
        got = V.sha256_of(rel)
        check(f"carrier_sha256_matches_disk[{rel}]", got == want,
              f"disk={got} pinned={want}")

    # (3) 双向断言：routable 的必须可 resolve（或给出 infra 理由），
    #     tier 阻塞的必须被拒。
    import os
    ckpt = os.environ.get(lc.FSMC_CHECKPOINT_ENV, lc.FSMC_DEFAULT_CHECKPOINT)
    ckpt_present = Path(ckpt).exists()
    print(f"[info] 2-core CHI checkpoint {ckpt} present={ckpt_present}")

    routed_rows = [r for r, v, _a, _m in V._ROWS
                   if v == V.CARRIER_ROUTED_PENDING_RUN]
    tier_rows = [r for r, v, _a, _m in V._ROWS
                 if v == V.BLOCKED_TRIGGER_TIER_UNIMPL]
    bad = []
    for rid in routed_rows:
        flags, golden, reason = lc.resolve_cell(
            _cell(rid, V.MODEL_OF[rid], rid.split("-")[1],
                  _workload_for(rid)))
        if ckpt_present:
            if flags is None:
                bad.append((rid, f"expected runnable, got {reason[:60]}"))
            elif golden != lc.FSMC_GOLDEN_FINAL:
                bad.append((rid, f"golden {golden} != {lc.FSMC_GOLDEN_FINAL}"))
            elif "--num-cores" not in flags or "2" not in flags:
                bad.append((rid, "flag set lacks the 2-core platform"))
            elif lc.FSMC_CARRIER_RC.name not in " ".join(flags):
                bad.append((rid, "flag set lacks the litmus_free carrier"))
        else:
            if flags is not None:
                bad.append((rid, "runnable without a checkpoint present"))
            elif "fsmc-infra" not in reason:
                bad.append((rid, f"missing-checkpoint reason not marked: "
                                f"{reason[:60]}"))
    check(f"routed_rows_resolve_or_refuse_with_infra_reason "
          f"(n={len(routed_rows)})", not bad, bad)

    bad2 = []
    for rid in tier_rows:
        flags, _g, reason = lc.resolve_cell(
            _cell(rid, V.MODEL_OF[rid], rid.split("-")[1],
                  _workload_for(rid)))
        if flags is not None:
            bad2.append((rid, "NOT-BLOCKED (tier silently unblocked)"))
        elif not reason.startswith("blocked(fsmc-trigger"):
            bad2.append((rid, f"unexpected reason: {reason[:60]}"))
    check(f"tier_rows_refused_with_tier_reason (n={len(tier_rows)})",
          not bad2, bad2)

    # 其余 25 格仍然被拒。
    others = [r for r, v, _a, _m in V._ROWS
              if v not in (V.CARRIER_ROUTED_PENDING_RUN,
                           V.BLOCKED_TRIGGER_TIER_UNIMPL)]
    bad3 = []
    for rid in others:
        flags, _g, reason = lc.resolve_cell(
            _cell(rid, V.MODEL_OF[rid], rid.split("-")[1],
                  _workload_for(rid)))
        if flags is not None:
            bad3.append((rid, "NOT-BLOCKED"))
        elif not reason:
            bad3.append((rid, "no reason"))
        elif not (reason.startswith("blocked(")
                  or reason.startswith("deferred")
                  or "不适用" in reason):
            bad3.append((rid, f"suspicious reason: {reason[:40]}"))
    check(f"other_25_rows_still_refused_with_a_reason (n={len(others)})",
          not bad3, bad3)

    # (4) WL_BLOCKED 的理由串与裁决表一致。
    for key, banned in (("Atomic-Litmus", "litmus needs multi-core FS"),
                        ("PARSEC", "PARSEC needs multi-core FS")):
        reason = lc.WL_BLOCKED.get(key, "")
        check(f"WL_BLOCKED[{key}] no longer carries the blanket phrase",
              banned not in reason, reason)
        check(f"WL_BLOCKED[{key}] still names multicore-fs (triage bucket "
              f"must not silently change)", "multicore-fs:" in reason, reason)
    check("WL_BLOCKED[Atomic-Litmus] cites the R4-9-FSMC-A carrier state",
          "R4-9-FSMC-A" in lc.WL_BLOCKED.get("Atomic-Litmus", ""),
          lc.WL_BLOCKED.get("Atomic-Litmus", ""))
    check("WL_BLOCKED[PARSEC] cites the find-verified absence",
          "aarch64" in lc.WL_BLOCKED.get("PARSEC", ""),
          lc.WL_BLOCKED.get("PARSEC", ""))

    # (5) 模型级理由：O05/O06/O07 的"只需多核"说法必须补上模型缺口。
    for model in ("O05", "O06", "O07"):
        reason = lc.MODEL_BLOCKED.get(model, "")
        check(f"MODEL_BLOCKED[{model}] names the model gap, not only "
              f"multi-core", "语义" in reason or "跟踪" in reason, reason)

    print(f"\nFAILURES: {FAILS if FAILS else '无'}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
