#!/usr/bin/env python3
"""[MDSPEC][R4-8-FSMC] 35 项 FS-MULTICORE BLOCKED 的逐项裁决表（机读）。

为什么单独有一个表（而不是只写在报告 md 里）：任务书要求"任何一格静默解锁
都算 bug"。`blocked_triage.md` 的类别是**按理由正则**判出来的
（tools/lsu_blocked_triage.py 的 `_FS_MC = re.compile(r"multicore")`），
理由串又来自 `lsu_campaign.WL_BLOCKED` —— 也就是说，一句"litmus needs
multi-core FS"同时描述了 35 格，而实测这 35 格至少有 4 种根因。这里把
**逐格裁决**写成机读常量，测试（tests/test_lsu_fsmc_verdict.py）负责钉死：

  1. 覆盖恰好 35 格、与任务书列表逐字一致；
  2. 每格的 reason 非空且指向具体缺口（不是 blanket 短语）；
  3. 每格声明的证据产物**在仓库里真的存在**（configs/fs/lsu_multicore_fs.py、
     workloads/litmus/*、configs/fs/litmus.rcS …）；
  4. 每格当前**仍被 campaign 拒绝**（resolve_cell → flags=None）——若有人把
     某一格接通，本测试会失败，逼迫把裁决表一起改（不得静默解锁）。

Group A 的语义要在乎一处细节：平台与载体已经真机跑通（见
docs/gem5-fi/lsu/mdspec/R4-8-FSMC-report.md §3），所以它的**workload-level
理由已不成立**；剩下的缺口是 §09 要求的 CHAOSAtomicTrace（L1–L3
monitor/atomic/order-tag/barrier 事件 + core/thread/global_order_id 关联键）
与 campaign 路由/golden。格子仍然 BLOCKED，但理由必须写成这条，不能继续
写 "litmus needs multi-core FS"。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- 裁决取值（枚举，避免自由文本漂移）---------------------------------
CARRIER_READY_RESIDUAL_BLOCKED = "CARRIER_READY_RESIDUAL_BLOCKED"
BLOCKED_INJECTOR_HOST = "BLOCKED_INJECTOR_HOST"
BLOCKED_MODEL_UNIMPL = "BLOCKED_MODEL_UNIMPL"
BLOCKED_WORKLOAD_IDENTITY = "BLOCKED_WORKLOAD_IDENTITY"

# 每组共享的"证据产物"路径（必须存在，测试逐条校验）
ARTIFACTS = {
    CARRIER_READY_RESIDUAL_BLOCKED: [
        "configs/fs/lsu_multicore_fs.py",
        "configs/fs/litmus.rcS",
        "workloads/litmus/litmus_sb.c",
        "workloads/litmus/litmus_mp.c",
        "workloads/litmus/litmus_atomic.c",
        "workloads/litmus/make_payload.py",
    ],
    BLOCKED_INJECTOR_HOST: [
        "configs/fs/lsu_multicore_fs.py",
        "configs/fs/litmus.rcS",
    ],
    BLOCKED_MODEL_UNIMPL: [],
    BLOCKED_WORKLOAD_IDENTITY: [
        "configs/fs/lsu_multicore_fs.py",
        "configs/fs/litmus.rcS",
    ],
}

# 逐格理由。模型粒度共享同一段（同模型同根因），但每格都显式登记，
# 免得"靠模型前缀推"这种隐式逻辑把新格子悄悄吃掉。
_REASON_A = ("载体+平台已落地并真机跑通（R4-8-FSMC：configs/fs/lsu_multicore_fs.py "
             "2 核 Ruby/CHI 检查点 + workloads/litmus 三件套，guest nproc=2）；"
             "workload-level 理由作废。残留缺口 = §09 要求的 CHAOSAtomicTrace"
             "（L1 monitor addr/valid/granule/version、atomic operand/SwapResp 路径、"
             "L3 order tag/barrier 完成点 + core/thread/global_order_id 关联键）"
             "未实现，且 campaign 侧无该载体的路由/golden ⇒ 仍 BLOCKED")
_REASON_B = ("构造性互斥：coherence 状态故障（C08）只能跑在有跨核一致性的平台"
             "（Ruby/CHI），而注入器 CHAOSCache 取 Param.Cache（classic 对象），"
             "Ruby 的 L1 是 cache controller ⇒ 无法挂载；classic 多核又无一致性"
             "（gem5 v25 无 classic coherence，src/mem/cache/noncoherent_cache.*）"
             "⇒ litmus 载体在其上不成立。解除需把注入钩子上到 Ruby cache "
             "controller（C++ 改动 + 重建）")
_REASON_C = {
    "O04": "模型语义未实现（缺 cache-side SwapResp/RMW data hook）—— 与多核无关的独立阻塞",
    "O05": "模型语义未实现（RMW 请求/全局可见性 order 跟踪）—— 独立阻塞",
    "O06": "模型语义未实现（barrier 完成跟踪）—— 独立阻塞",
    "O07": "模型语义未实现（order-tag/ready 跟踪）—— 独立阻塞",
    "O09": "模型语义未实现（缺 RMW operand hook）—— 独立阻塞",
}
_REASON_D = {
    "O09": _REASON_C["O09"] + "；且 W13 规格钉 PARSEC(dedup/ferret/streamcluster)，"
           "仓库内无 aarch64 二进制/输入集（find 实证）",
    "P09": "W13 规格负载身份：PARSEC(dedup/ferret/streamcluster) 开源但仓库内无 "
           "aarch64 二进制/输入集；且 P09 的 dirty-evict 注入走 classic CHAOSCache"
           "（同 B 组宿主互斥）",
}

_ROWS = [
    # Group A: O01/O02/O03 × W7
    ("O01-F0-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O01"),
    ("O01-F2-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O01"),
    ("O01-F6-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O01"),
    ("O02-F0-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O02"),
    ("O02-F2-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O02"),
    ("O02-F5-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O02"),
    ("O02-F6-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O02"),
    ("O03-F0-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O03"),
    ("O03-F2-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O03"),
    ("O03-F6-W7", CARRIER_READY_RESIDUAL_BLOCKED, _REASON_A, "O03"),
    # Group B: C08 × W7
    ("C08-F0-W7", BLOCKED_INJECTOR_HOST, _REASON_B, "C08"),
    ("C08-F2-W7", BLOCKED_INJECTOR_HOST, _REASON_B, "C08"),
    ("C08-F5-W7", BLOCKED_INJECTOR_HOST, _REASON_B, "C08"),
    ("C08-F6-W7", BLOCKED_INJECTOR_HOST, _REASON_B, "C08"),
    # Group C: O04/O05/O06/O07/O09 × W7
    ("O04-F0-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O04"], "O04"),
    ("O04-F2-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O04"], "O04"),
    ("O04-F6-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O04"], "O04"),
    ("O05-F0-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O05"], "O05"),
    ("O05-F4-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O05"], "O05"),
    ("O05-F6-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O05"], "O05"),
    ("O06-F0-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O06"], "O06"),
    ("O06-F4-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O06"], "O06"),
    ("O06-F6-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O06"], "O06"),
    ("O07-F0-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O07"], "O07"),
    ("O07-F2-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O07"], "O07"),
    ("O07-F6-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O07"], "O07"),
    ("O09-F0-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O09"], "O09"),
    ("O09-F1-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O09"], "O09"),
    ("O09-F2-W7", BLOCKED_MODEL_UNIMPL, _REASON_C["O09"], "O09"),
    # Group D: O09 × W13, P09 × W13
    ("O09-F0-W13", BLOCKED_WORKLOAD_IDENTITY, _REASON_D["O09"], "O09"),
    ("O09-F1-W13", BLOCKED_WORKLOAD_IDENTITY, _REASON_D["O09"], "O09"),
    ("O09-F2-W13", BLOCKED_WORKLOAD_IDENTITY, _REASON_D["O09"], "O09"),
    ("P09-F0-W13", BLOCKED_WORKLOAD_IDENTITY, _REASON_D["P09"], "P09"),
    ("P09-F4-W13", BLOCKED_WORKLOAD_IDENTITY, _REASON_D["P09"], "P09"),
    ("P09-F6-W13", BLOCKED_WORKLOAD_IDENTITY, _REASON_D["P09"], "P09"),
]

# 任务书给的 35 格原文（作为外部对照，防止本文件自己漂移）
TASK_LIST = [
    "C08-F0-W7", "C08-F2-W7", "C08-F5-W7", "C08-F6-W7",
    "O01-F0-W7", "O01-F2-W7", "O01-F6-W7",
    "O02-F0-W7", "O02-F2-W7", "O02-F5-W7", "O02-F6-W7",
    "O03-F0-W7", "O03-F2-W7", "O03-F6-W7",
    "O04-F0-W7", "O04-F2-W7", "O04-F6-W7",
    "O05-F0-W7", "O05-F4-W7", "O05-F6-W7",
    "O06-F0-W7", "O06-F4-W7", "O06-F6-W7",
    "O07-F0-W7", "O07-F2-W7", "O07-F6-W7",
    "O09-F0-W13", "O09-F0-W7", "O09-F1-W13", "O09-F1-W7",
    "O09-F2-W13", "O09-F2-W7",
    "P09-F0-W13", "P09-F4-W13", "P09-F6-W13",
]

VERDICT_OF = {r: v for r, v, _reason, _m in _ROWS}
REASON_OF = {r: reason for r, _v, reason, _m in _ROWS}
MODEL_OF = {r: m for r, _v, _reason, m in _ROWS}

# ★ 逐格的禁用短语：blanket 理由必须已被替换掉。
BANNED_PHRASES = ["litmus needs multi-core FS", "PARSEC needs multi-core FS"]


def check():
    """返回 (problems, info)：纯函数，供测试与人工审计共用。"""
    problems = []
    rows = [r for r, _v, _reason, _m in _ROWS]

    if len(_ROWS) != 35:
        problems.append(f"verdict table must cover exactly 35 rows, got {len(_ROWS)}")
    if sorted(rows) != sorted(TASK_LIST):
        only_table = sorted(set(rows) - set(TASK_LIST))
        only_task = sorted(set(TASK_LIST) - set(rows))
        problems.append(f"row set mismatch: extra={only_table} missing={only_task}")

    for rid, verdict, reason, model in _ROWS:
        if not reason or len(reason) < 20:
            problems.append(f"{rid}: reason too short/empty")
        for banned in BANNED_PHRASES:
            if banned in reason:
                problems.append(f"{rid}: blanket reason not replaced ({banned})")
        if verdict not in (CARRIER_READY_RESIDUAL_BLOCKED, BLOCKED_INJECTOR_HOST,
                           BLOCKED_MODEL_UNIMPL, BLOCKED_WORKLOAD_IDENTITY):
            problems.append(f"{rid}: unknown verdict {verdict}")
        if not model:
            problems.append(f"{rid}: missing model id")
        for rel in ARTIFACTS.get(verdict, []):
            if not (ROOT / rel).exists():
                problems.append(f"{rid}: verdict {verdict} cites missing "
                                f"artifact {rel}")

    counts = {}
    for _r, v, _reason, _m in _ROWS:
        counts[v] = counts.get(v, 0) + 1
    return problems, {"counts": counts, "n": len(_ROWS)}


if __name__ == "__main__":
    probs, info = check()
    print(f"rows={info['n']} verdicts={info['counts']}")
    for p in probs:
        print(f"  FAIL {p}")
    print("OK" if not probs else f"PROBLEMS={len(probs)}")
    raise SystemExit(1 if probs else 0)
