# 口径纠正记录：`R4-8-GO` 不是 GO（2026-10-22，R4-10）

> **本文件是对提交 `d63a5dd8`（提交名 `[LSU][MDSPEC][R4-8-GO] …`）的正式纠正。**
> 该提交名中的 **GO 仅表示"门禁记录已写入"**，**不代表正式实验已获准**。
> 在纠正被推翻之前，本轨道的准入结论为 **NO-GO**，任何人不得引用 `R4-8-GO` 作为 GO 依据。

## 1. 事实（实测）

| 口径 | 数值 | 来源 |
|---|---|---|
| 契约（READY 口径） | **READY=241 / PARTIAL=0 / BLOCKED=84** | `ready_contract.json` = `ready_contract.md` |
| 覆盖（coverage 口径） | **PASS=245 / BLOCKED=80** | `coverage_matrix.md`（325 行，单位是覆盖节点而非准入） |
| 契约裁决 | **NO-GO** | `python3 tools/lsu_ready_contract.py --gate` → `[verdict] NO-GO` |
| 二进制 | `CHAOS/gem5/build/ARM/gem5.opt` sha256 前缀 `f4dbfb9a66e0df80` | 本次 R4-10 构建产物 |

**两套口径不可互换**：contract 的 84 与 coverage 的 80 是不同判据下的不同分母，
`ready_contract.py` 以 `runid_map + campaign.resolve_cell` 判准入，`coverage_matrix.py`
以节点级规格判覆盖。引用时必须写明是哪一个口径。

BLOCKED 84 的互斥分类（守恒校验通过）：

| 类别 | 数量 | 含义 |
|---|---|---|
| RULING | 6 | A06 load 侧裁决封锁 |
| FS-INFRA | 24 | TLB 系 FS 项（部分已可跑，见 §3） |
| MODE-UNIMPL | 3 | T08-b/c/d（本轮已实现，待真机 pilot 解锁） |
| UNRESOLVED | 4 | S01/S02-F0-W1、S10-F2-W5/W9 |
| FS-MULTICORE | 35 | 多核 FS / litmus / PARSEC |
| LICENSE | 12 | SPEC CPU2017 授权（真外部） |

## 2. NO-GO 的判定条件（已写入 gate，非人工声明）

`tools/lsu_ready_contract.py::verdict()` 在**任一**条件成立时返回 NO-GO 且退出码 1：

1. `BLOCKED > 0`（当前 84）；
2. `PARTIAL > 0`；
3. `pytest_rc != 0`；
4. 磁盘 free < `max(50 GiB, 20%×total)`，或 MemAvailable < 10 GiB；
5. 正式命令中仍出现 `--phase trial`（pilot 口径），或存在非 `screening` phase 的正式命令。

**禁止**：通过改分类、放宽阈值、把 BLOCKED 排除出总数来制造 GO。
契约测试 `tests/test_lsu_ready_contract_verdict.py` 含负向用例，钉死"BLOCKED=1 必须 NO-GO"。

## 3. `--phase trial --max-seeds-per-cell 3` 是 pilot，不是正式命令

R4-8 契约里每个 READY 行给出的命令是 **pilot 口径**（试跑 3 seed，用于验证注入器/载具/oracle）。
正式口径来自 `完整任务执行清单.md` §全局实验口径（2026-10-08 生效）：

- **正式筛查**：每个有效 RunID **固定累计 ≥ 385** 个独立 activated runs/clusters，统一报 Wilson 95% CI；
- **重点扩样**：仅 **21 个固定 RunID** 累计到 **2401**（含前 385，不是额外再取）；
- **采样数量在 campaign 开始前固定**，**不依据**中途点估计或普通 CI 半宽序贯停止。
  ⇒ 因此正式 phase 用 `--phase screening`（到量即停），**刻意不用** `--phase main`
  （其 Wilson 半宽序贯停止违反本政策）。

R4-10 起，`ready_contract` 生成的命令已切换为正式口径（`--phase screening --screening-target
385|2401 --max-seeds-per-cell 100000`）。**pilot 命令不得再冒充正式命令。**

## 4. 结论

- 当前 **NO-GO**，**不得启动正式 campaign**。
- 服务器侧可自解项见 `R4-10-INTEGRATION-REPORT.md` 与各 agent 报告；
  真外部阻塞为 **LICENSE 12（SPEC CPU2017 授权）** 和 **PARSEC/W13 载具**。
