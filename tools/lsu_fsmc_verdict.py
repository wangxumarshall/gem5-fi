#!/usr/bin/env python3
"""[MDSPEC][R4-9-FSMC-A] 35 项 FS-MULTICORE BLOCKED 的逐项裁决表（机读）。

本表最初由 R4-8-FSMC 建立（35 格 4 种根因）。R4-9-FSMC-A 在同一张表上做了
**两处证据化修订**，都是实测/源码级事实推动的，不是措辞美化：

  (1) A 组的 10 格被**拆成两半**。R4-8-FSMC 只知道"多核 FS 平台 + 本地 litmus
      已跑通、但载荷投放臂卡死"，故 10 格共享一条残留理由。R4-9-FSMC-A 把
      载荷投放**解决**了（freestanding ~8 KB 载体，真机端到端跑出三条 oracle
      + FINAL，见报告 §3），于是格子的差异暴露出来：
        * **F0（单次瞬态）/ F5（永久）** 这 4 格，CHAOSExMon 用**已有旋钮**就能
          诚实表达（maxFaults=1 / maxFaults=0），campaign 路由 + golden 已接好，
          载体已由真机运行验证 ⇒ `CARRIER_ROUTED_PENDING_RUN`
          （**routable 但本格自己的 campaign 样本尚未取，故不宣称 PASS**）。
        * **F2 / F6** 这 6 格无法诚实表达：CHAOSExMon 的
          `lsuTier`/`lsuWarmupEvents`/`lsuSpanEvents` 只在 .py 里声明，
          在 .hh/.cc 里**0 次**出现（grep 实证），`inWindow()` 只有
          firstClock/lastClock 的**时钟**窗 ⇒ F2 的 interval 语义与 F6 的
          确定性路径层都没有落点 ⇒ `BLOCKED_TRIGGER_TIER_UNIMPL`。
      注意这与 R4-8-FSMC 的 `CARRIER_READY_RESIDUAL_BLOCKED` 不冲突而是细化：
      原裁决里"载体就绪、残留阻塞"这件事**仍然成立**，只是残留从"平台/载荷"
      收敛成了"档位语义 + §09 CHAOSAtomicTrace"。

  (2) D 组（W13 = PARSEC）的裁决理由补上**实测的不可得证据**：仓库内唯一的
      PARSEC 痕迹是 gem5 上游测试脚手架，而它 (a) 默认被禁用（"PARSEC disk
      image is too big"），(b) `valid_hosts=(host_x86_64_tag,)` **仅 x86_64
      宿主**，(c) 需要 `--resource-directory` 指向预编译磁盘镜像 + KVM。仓库里
      没有 PARSEC 源码/输入集/aarch64 构建（find 实证，见报告 §5）。

纪律（不变，且被测试强制）：
  1. 覆盖恰好 35 格、与任务书列表逐字一致；每格 reason 非空且在仓库里有依据；
  2. 分组计数 = 4（routable·待取样本）/ 6（档位语义未实现）/ 4（注入器宿主
     互斥）/ 15（模型语义未实现）/ 6（规格负载身份）；
  3. **声明 routable 的 4 格必须真的能 resolve 出 FS flag 集**（且 golden ==
     FSMC_GOLDEN_FINAL），**声明档位阻塞的 6 格必须真的被拒**——这是"不静默
     解锁、也不静默阻塞"的双向断言；
  4. 载体指纹（sha256）必须与磁盘实测一致（防止无声漂移）。
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- 裁决取值（枚举，避免自由文本漂移）---------------------------------
CARRIER_ROUTED_PENDING_RUN = "CARRIER_ROUTED_PENDING_RUN"
BLOCKED_TRIGGER_TIER_UNIMPL = "BLOCKED_TRIGGER_TIER_UNIMPL"
BLOCKED_INJECTOR_HOST = "BLOCKED_INJECTOR_HOST"
BLOCKED_MODEL_UNIMPL = "BLOCKED_MODEL_UNIMPL"
BLOCKED_WORKLOAD_IDENTITY = "BLOCKED_WORKLOAD_IDENTITY"

# 每组共享的"证据产物"路径（必须存在，测试逐条校验）
ARTIFACTS = {
    CARRIER_ROUTED_PENDING_RUN: [
        "configs/fs/lsu_multicore_fs.py",
        "configs/fs/litmus_free.rcS",
        "workloads/litmus/litmus_free.c",
        "workloads/litmus/make_free_payload.py",
        "tools/lsu_campaign.py",
    ],
    BLOCKED_TRIGGER_TIER_UNIMPL: [
        "configs/fs/litmus_free.rcS",
        "workloads/litmus/litmus_free.c",
        # 档位语义的**反面证据**（声明了但不消费）也要求在场：改了它就要
        # 一起改本表。
        "CHAOS/gem5/src/arch/arm/CHAOSExMon/CHAOSExMon.py",
        "CHAOS/gem5/src/arch/arm/CHAOSExMon/CHAOSExMon.cc",
    ],
    BLOCKED_INJECTOR_HOST: [
        "configs/fs/lsu_multicore_fs.py",
        "configs/fs/litmus_free.rcS",
    ],
    BLOCKED_MODEL_UNIMPL: [],
    BLOCKED_WORKLOAD_IDENTITY: [
        "configs/fs/lsu_multicore_fs.py",
        "configs/fs/litmus_free.rcS",
    ],
}

# ---- 载体指纹（防无声漂移；测试实测磁盘 sha256 比对）--------------------
CARRIER_SHA256 = {
    "workloads/litmus/litmus_free": (
        "df76d963a0c7bd8b174f2866ad98f8e5ddca18b0baa05448d5747a1056c89ffb"),
    "configs/fs/litmus_free.rcS": (
        "46012d8017cbe87b1fb72754cfc5ae7834e6b9ff8fe333ef3da0a94d5dbacc6d"),
    "configs/fs/litmus_free_diag.rcS": (
        "cf203a2c17efee19c6948424c1fe6bc637e6bf255a43c17fc29cc26137f6a644"),
}

# 逐格理由。
_REASON_A_RUN = (
    "载体+平台+载荷投放全部真机跑通（R4-9-FSMC-A：freestanding 8 KB 载体经 "
    "readfile -> sh heredoc -> base64 -d 在 2 核 Ruby/CHI 检查点上解出并执行，"
    "自报 SB/MP/LDXR-STXR 三条禁出现计数 + FINAL=<16hex>；见报告 §3 原始输出）。"
    "campaign 已接好：家族 exmon-fsmc -> lsu_multicore_fs.py + litmus_free.rcS "
    "+ 检查点（LSU_FS_MC_CHECKPOINT 环境变量，缺省 R4-8-FSMC 产物），golden = "
    "无故障运行的 FINAL。本格档位（F0=单次瞬态 maxFaults=1 / F5=永久 "
    "maxFaults=0）由 CHAOSExMon **真正消费**的旋钮表达 ⇒ routable。"
    "**但本格自己的 campaign 样本尚未取**，故仍记 BLOCKED（不宣称 PASS）"
)
_REASON_A_TIER = (
    "档位语义未实现（源码级实证）：%s 所需的触发语义在 CHAOSExMon 里没有落点 —— "
    "lsuTier/lsuWarmupEvents/lsuSpanEvents 在 CHAOSExMon.py 有声明，在 "
    "CHAOSExMon.hh/.cc 里 **0 次**出现；inWindow() 只有 firstClock/lastClock 的"
    "**时钟**窗，事件计数只有内部 geometric(0.1) 首跳。F2 的 interval 语义"
    "（chaos_trigger.hh：260000 cycles）与 F6 的确定性路径/矩阵规定层都无法用现有"
    "旋钮表达 ⇒ 若硬跑，F2/F6 三格会与 F0 逐字节相同（错标）。解除需给 "
    "CHAOSExMon 接上 chaos_trigger（C++ + 重建，本轮禁 scons）。载体与投放已就绪"
    "（见 R4-9-FSMC-A 报告 §3/§4）"
)
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
           "仓库内无 aarch64 二进制/输入集（find 实证）：唯一痕迹是 gem5 上游测试"
           "脚手架 CHAOS/gem5/tests/gem5/parsec_benchmarks/，而它默认被禁用、"
           "valid_hosts=(host_x86_64_tag,) 仅 x86_64 宿主、需 --resource-directory"
           "指向预编译磁盘镜像 + KVM",
    "P09": "W13 规格负载身份：PARSEC(dedup/ferret/streamcluster) 开源但仓库内无 "
           "aarch64 二进制/输入集；**且** P09 的 dirty-evict 注入走 classic CHAOSCache"
           "（同 B 组宿主互斥）⇒ W13 要求的'多线程真实应用'语义与 P09 能挂载的平台"
           "构造性冲突（classic 多核无一致性），换任何开源替代负载都不成立",
}

_ROWS = [
    # Group A-1: O01/O02/O03 × W7，档位可由现有旋钮诚实表达（F0/F5）
    ("O01-F0-W7", CARRIER_ROUTED_PENDING_RUN, _REASON_A_RUN, "O01"),
    ("O02-F0-W7", CARRIER_ROUTED_PENDING_RUN, _REASON_A_RUN, "O02"),
    ("O02-F5-W7", CARRIER_ROUTED_PENDING_RUN, _REASON_A_RUN, "O02"),
    ("O03-F0-W7", CARRIER_ROUTED_PENDING_RUN, _REASON_A_RUN, "O03"),
    # Group A-2: O01/O02/O03 × W7，档位语义未实现（F2/F6）
    ("O01-F2-W7", BLOCKED_TRIGGER_TIER_UNIMPL, _REASON_A_TIER % "F2", "O01"),
    ("O01-F6-W7", BLOCKED_TRIGGER_TIER_UNIMPL, _REASON_A_TIER % "F6", "O01"),
    ("O02-F2-W7", BLOCKED_TRIGGER_TIER_UNIMPL, _REASON_A_TIER % "F2", "O02"),
    ("O02-F6-W7", BLOCKED_TRIGGER_TIER_UNIMPL, _REASON_A_TIER % "F6", "O02"),
    ("O03-F2-W7", BLOCKED_TRIGGER_TIER_UNIMPL, _REASON_A_TIER % "F2", "O03"),
    ("O03-F6-W7", BLOCKED_TRIGGER_TIER_UNIMPL, _REASON_A_TIER % "F6", "O03"),
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

EXPECTED_COUNTS = {
    CARRIER_ROUTED_PENDING_RUN: 4,
    BLOCKED_TRIGGER_TIER_UNIMPL: 6,
    BLOCKED_INJECTOR_HOST: 4,
    BLOCKED_MODEL_UNIMPL: 15,
    BLOCKED_WORKLOAD_IDENTITY: 6,
}


def sha256_of(rel):
    p = ROOT / rel
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


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
        if verdict not in EXPECTED_COUNTS:
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
    if counts != EXPECTED_COUNTS:
        problems.append(f"group counts drifted: {counts} != {EXPECTED_COUNTS}")

    for rel, want in CARRIER_SHA256.items():
        got = sha256_of(rel)
        if got is None:
            problems.append(f"carrier artifact missing: {rel}")
        elif got != want:
            problems.append(f"carrier drift: {rel} sha256 {got} != pinned {want}")

    return problems, {"counts": counts, "n": len(_ROWS)}


if __name__ == "__main__":
    probs, info = check()
    print(f"rows={info['n']} verdicts={info['counts']}")
    for p in probs:
        print(f"  FAIL {p}")
    print("OK" if not probs else f"PROBLEMS={len(probs)}")
    raise SystemExit(1 if probs else 0)
