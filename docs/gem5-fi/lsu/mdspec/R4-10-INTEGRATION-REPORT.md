# LSU MDSPEC R4-10 集成报告（2026-10-22）—— 状态：**NO-GO**

> 主 agent 集成轮。三个 subagent 分支已语义合并、构建并回归。
> **正式 campaign 未启动**；本报告是启动前的最终状态快照。

## 0. 结论（一句话）

**仍为 NO-GO。** 84 项 BLOCKED 中，服务器侧可自解的实现工作已完成并真机验证（T05/T06/T07 三个 TLB
模式族、T08-b/c/d walk/refill 配对、多核 FS 传播链、A06 静默零缺陷修复）；
剩余阻塞为 **LICENSE 12（SPEC CPU2017 授权，真外部）**、**PARSEC/W13 载具（真外部）**、
**FS-MULTICORE 的 Ruby/CHI 与 ExMon F 档位（待构建后可解锁一部分）**、**A06 规格裁决**、
**S01/S02 测量未收敛**。**在 BLOCKED 归零前不得启动正式 campaign。**

## 1. 两套口径（不可互换）

| 口径 | 命令 | 结果 |
|---|---|---|
| **准入（readiness）** | `python3 tools/lsu_ready_contract.py --gate` | **READY=241 / PARTIAL=0 / BLOCKED=84**；`[verdict] NO-GO`，EXIT=1 |
| **覆盖（coverage）** | `python3 tools/lsu_coverage_matrix.py …` | **PASS=245 / BLOCKED=80**（325 行按节点级规格判覆盖） |

两者分母不同：contract 判"该 RunID 能否经 campaign 入口准入"，coverage 判"节点级规格是否已覆盖"。
引用必须注明口径。

## 2. 84 项 BLOCKED 逐项分类与证据

| 类别 | 数量 | RunID | 证据 / 处置 |
|---|---|---|---|
| **FS-INFRA** | 24 | T01-F0/F1/F2-W4, T02-F0/F2-W4, T03-F5-W4, T04-F0/F2/F6-W4, T05-F0/F2/F6-W4, T06-F0/F2/F6-W4, T07-F0/F4/F6-W4, T08-F0/F4/F6-W4, T10-F0/F1/F2-W4 | T01–T04/T08-a/T10 旧"需 FS 基础设施"理由**已被真机证伪**（R4-6.0 修 `CHAOSArmTLB.walker=None` 配置 bug 后 campaign 真机 activated=1）。T05/T06/T07 的 9 格模式**本轮已实现**（`valid_clear/valid_set/global_flip/asid_subst`；`perm_subst/memtype_subst/pagesize_subst`；`false_hit/double_hit/wrong_way`），构建通过；**待真机 FS pilot 解锁**。T10 PPN 位带分层（T10-a/b/c）仍未参数化（诚实残余）。 |
| **FS-MULTICORE** | 35 | C08-F0/F2/F5/F6-W7；O01–O03,W7；O04/O09(RMW),W7；O05/O06/O07,W7；O09-W13；P09-W13 | 已真机：多核 FS 平台 + freestanding litmus 投放 + 传播链（616 事件/586 链节点）+ A 组注入 vs 无故障**逐字节相同 oracle** ⇒ O01-F0=Masked（仍 BLOCKED：未取 campaign 全样本）。C08 4 格为**构造性互斥**（classic `Param.Cache` vs Ruby controller）。O04–O09 W7 钩子已落地（compile-verified，本轮已构建）但未 pilot。W13 6 格：**PARSEC 仓库内无源码/输入集/aarch64 构建**（真外部，不得替换身份）。 |
| **LICENSE** | 12 | C15-F0/F4/F6-W11, L04-F0/F2/F6-W11, S13-F0/F1/F2-W11, T10-F0/F1/F2-W11 | **真外部**：全盘无 SPEC CPU2017 数据（无 binary、无 golden；`workloads/` 仅 `directed/litmus/mibench/ooo`）。**禁止用替代负载冒充。** |
| **RULING** | 6 | A06-F0/F2/F6-W3/W5 | A06 load 侧裁决。本轮独立复核：**load SHRINK 结构性不可达成立**（`mem.isa:499 getMemLE(pkt,Mem,…)` → `memhelpers.hh:80 pkt->get<Mem>()` → `packet_access.hh:55 assert(sizeof(T)<=size)`，`size` 为 Packet 字段 ⇒ 任何读之前必断言）。R4-8 草案"提高目的缓冲保底"前提被证伪。真机复验 `load_shrink=0 / load_shrink_unsafe=1212`，rc=0（**修掉了静默零**）。**需规格裁决**：A06-a load 侧仅保留 widen，或立项改完成语义。 |
| **UNRESOLVED** | 4 | S01-F0-W1, S02-F0-W1, S10-F2-W5, S10-F2-W9 | S10-F2 两格：`chaos_lsu_trigger.hh:203` F2 interval=1e5 且 `:211 next_fire=from+iv/2+…` ⇒ 下界 50000 ≫ 实测流长 3/4 ⇒ **(iii) 规格要求结构性拒绝**（已契约钉死）。S01/S02-F0-W1（MiBench 全量）：census **>55 min 未收敛**，未写估计值。 |
| **MODE-UNIMPL** | 3 | T08-F0/F4/F6-W9 | 本轮已实现 T08-b/c/d（`walk_fill_dup` / `walk_done_early` / `walk_stale_result`，walk_id 配对 + refill field 自描述），构建通过；待真机 pilot 解锁。 |

守恒：6+24+3+4+35+12 = 84。**无一项通过改分类/放宽阈值被"制造"为 READY。**

## 3. 构建 / 测试 / 真机 / 资源

| 项 | 实测 |
|---|---|
| 构建 | `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` → `scons: done building targets`；改动文件**零新增编译告警** |
| 二进制 | `CHAOS/gem5/build/ARM/gem5.opt` sha256 `f4dbfb9a66e0df80…`（1,145,188,760 B） |
| 完整测试 | `python3 -m pytest tests/ -q` → **21 passed, rc=0**（含新增 `test_lsu_ready_contract_verdict.py`） |
| 真机 pilot | A06 shrink：rc=0，`load_shrink_unsafe=1212`（响亮拒绝被计数）；T 系/FS 系见各 agent 报告 |
| 传播链 | 多核 FS：616 事件 / 586 链节点；干净臂为空（链由注入引起） |
| 资源 | disk free **76.0 GiB** ≥ 红线 70.65；MemAvailable 26.7 GiB；并发上限 4 |
| 磁盘回收 | 见 §5 |

## 4. 唯一的正式 campaign 启动命令（**GO 前禁止执行**）

```bash
# 全量 325 RunID，正式筛查口径（清单 §全局实验口径）
LSU_GEM5_BIN=$PWD/CHAOS/gem5/build/ARM/gem5.opt \
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir runs/lsu/formal_325 \
  --phase screening --screening-target 385 --max-seeds-per-cell 100000 \
  --max-parallel 1
```

- 21 个重点 RunID 改 `--screening-target 2401`（逐 RunID 命令见 `ready_contract.md`）。
- **不含** `--phase trial` / `--max-seeds-per-cell 3`（那是 pilot）。
- 仍为 **NO-GO**：不得执行。

## 5. 磁盘审计（本轮）

| 处置 | 路径 | 大小 | 可恢复性 |
|---|---|---|---|
| 已删 | 7 个**已合并且工作树干净**的 worktree（r4-7-a06/fsinfra/s10span, r4-8-fsmc/spec, r4-9-fsmc-a/c） | 2.10 GiB | `git worktree add` 重建 |
| 已删 | 3 个**patch 已全部应用**的 worktree（r4-a06, r4-s10fix, r4-t08walk，`git cherry` 实测 not-applied=0） | 0.91 GiB | 同上 |
| 已删 | `integration-lsu-xlsx2md-20261019`（产物已在主分支） | 0.23 GiB | 同上 |
| 已删 | `/home/sdc/gem5-fi-ding/build/` 陈旧仓库根构建（sha `10590f6295bc4dec`，子代理独立证实**不含** CHAOSPropagation 新参数、会误用） | 6.9 GiB | `scons -j16 build/ARM/gem5.opt` 重建 |
| 压缩 | `runs/lsu/guard/guard_events.log` → `.gz`（**数据保留**） | 0.18 GiB | 解压 |
| 清缓存 | `__pycache__`、`pip cache`、`node-gyp/bazelisk` 缓存 | ~0.4 GiB | 自动重建 |
| **未动** | `r4-8-fsmca`（用户明令：有未提交成果） | — | — |
| **未动** | 其他会话 worktree（lsu-capacity/lsu-p4-fix/r4-8-fsmcc/r4-c14c15/r4-s10rc/r4-t08fs 等，未合并或有未提交改动） | — | — |
| **未动** | `wangxu/`(99G)、`sdc-excite-reproduce/`(61G)、`gem5-fs/`(3G，FS 必需)、`sdc-run/`(用户数据) | — | — |

---

## 附：R5 事实订正（2026-10-22，对抗性核验实测）

以下是对本报告正文的**事实纠错**，不改变任何 RunID 计数或准入结论（仍为 NO-GO）。

| 位置 | 原文 | 实测 | 证据 |
|---|---|---|---|
| §2 FS-MULTICORE 行 | "传播链（616 事件/586 链节点）" | **810 事件 / 585 链节点** | `zcat /tmp/r4-8-fsmcb/run2/prop_evt.txt.gz \| grep -oE 'kind=[A-Za-z_]+' \| sort \| uniq -c`（合计 810）；`zcat …/prop_trace.csv.gz \| grep -cv '^#'` = 585。定性结论（干净臂为空、链由注入引起）不受影响。 |
| §2 FS-INFRA 行 | "FS 载体在预算内不终止 → 无 L5" | **过于笼统**：`T04-F0-W4` 达到 `outcome=Crash` 且链 `L0→L1 proven …`；仅 T01/T03/T08 超时 | `runs/lsu/trial_r48_fs/T04-F0-W4/cell_results.json` |
| §3 "构建"行 | "改动文件零新增编译告警" | **盘上无构建日志可复核**（仅可由冻结二进制 `strings` 间接佐证 C++ 已编入） | 如实披露为"仅散文、无产物" |
| §5 磁盘审计 | 各 worktree 回收 GiB 数 | 无盘上产物可复核 | 同上 |

同时确认（核验为真，无需订正）：A06 load SHRINK 证明链四处 `file:line` 逐字正确；
LICENSE 12 全盘零 SPEC 产物；`e4dcd5da` 为 HEAD 祖先；二进制 sha256 `f4dbfb9a66e0df80…`。
