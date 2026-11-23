# MMU WHEN-5X3 — 最终冻结交付清单 (final frozen delivery manifest)

Round 0202c-final-close + W5X3-OBS-0222 + final-report-cleanup · `gem5-fi-mmu-when5x3` · 2026-11-19
最终文档清理：统一历史报告为 117 FULL / 0 PARTIAL / 3 N/A，M07-C02 Result B 标记为
被 OBS-0222 取代。不改 Where/Context/Timing/故障注入语义、不重跑实验、无 Git 操作。

## 1. 最终实验结果（权威基线）

| 维度 | 数量 |
|---|---|
| 计划条件 | **120**（8 模型 × 5 上下文 × 3 时机） |
| 已执行 Fault | **117** |
| 严格 FULL | **117** |
| PARTIAL | **0** |
| N/A | **3**（M06-C05） |

### 逐模型

| 模型 | FULL | PARTIAL | N/A |
|---|---:|---:|---:|
| M01 | 15 | 0 | 0 |
| M02 | 15 | 0 | 0 |
| M03 | 15 | 0 | 0 |
| M04 | 15 | 0 | 0 |
| M05 | 15 | 0 | 0 |
| M06 | 12 | 0 | 3 |
| M07 | 15 | 0 | 0 |
| M08 | 15 | 0 | 0 |
| **总计** | **117** | **0** | **3** |

### 终态汇总（120 条）

| TerminalState | Count |
|---|---:|
| SDC | 74 |
| ACTIVATED_MASKED | 15 |
| PROPAGATED_BUT_SQUASHED | 9 |
| DETECTED_DELIVERED | 9 |
| ACTIVATED_UNCONSUMED | 5 |
| DETECTED_LOCALLY | 3 |
| N/A | 3 |
| SQUASHED_BEFORE_MEMORY_ACCESS | 2 |

## 2. 最终证据文件

> **最终报告包**：`MMU_FINAL_REPORT_FINAL.zip` 是本轮文档清理后的最新报告包（21 文件，
> SHA256 `323fe042…`）。`MMU_FINAL_REPORT.zip`（b6a20619…）为上一轮版本，保留作历史，不覆盖。

| 包 | 绝对路径 | 大小 | SHA256 | 文件数 |
|---|---|---|---|---|
| MMU_FINAL_REPORT_FINAL.zip | `/home/sdc/gem5-fi-mmu-when5x3/exports/MMU_FINAL_FROZEN_DELIVERY/MMU_FINAL_REPORT_FINAL.zip` | 2 479 839 B (2.4 MiB) | `323fe04211464efaa794f7af087368ebd35926496c2d0dc969fa4719a5080bc8` | 21 |
| MMU_FINAL_REPORT.zip | `/home/sdc/gem5-fi-mmu-when5x3/exports/MMU_FINAL_FROZEN_DELIVERY/MMU_FINAL_REPORT.zip` | 2 478 369 B (2.4 MiB) | `b6a20619e2816dffb789caceabba3156d89bc38bac90715a58c2a0254657a8fb` | 21 |
| MMU_FINAL_CAUSAL_EVIDENCE.zip | `/home/sdc/gem5-fi-mmu-when5x3/exports/MMU_FINAL_FROZEN_DELIVERY/MMU_FINAL_CAUSAL_EVIDENCE.zip` | 6 815 929 B (6.5 MiB) | `0a48c7ca17b93dc36a1d531717f656ffaee958de648c475a15ea9e5646706bc7` | 141 |
| MMU_FINAL_RAW_AND_SOURCE.zip | `/home/sdc/gem5-fi-mmu-when5x3/exports/MMU_FINAL_FROZEN_DELIVERY/MMU_FINAL_RAW_AND_SOURCE.zip` | 18 671 943 B (17.8 MiB) | `0e688c6f6954ca3fe2010903b31e94623adf325833269cecf8ad1309eb49884f` | 400 |

### 关键文件目录

- **MMU_FINAL_REPORT.zip**（报告 + 统计，21 文件）：`REPORT.md`、`FINAL_EVIDENCE_REPORT.md`、
  `final_acceptance.md`、`acceptance.json`、`experiment_status.csv`、
  `per_condition.json`、`propagation_chains.csv`、`terminal_symptoms.csv`、
  `partial23_repair_comparison.csv`、`control_map.json`、`conditions.json`、
  `fault_control_compare.csv`、`timing_map.csv`、`summary_by_model.csv`、
  `completeness.csv`、`per_model_completeness.csv`、`final_issue_closure.csv`、
  `M07_C02_FINAL_CLOSURE.md`、`M06_C05_PILOT_EVIDENCE.md`、
  `M07_C02_T01_COMPLETE_PROPAGATION.md`、`M07_C02_T02_COMPLETE_PROPAGATION.md`。
- **MMU_FINAL_CAUSAL_EVIDENCE.zip**（因果 DAG）：`causal_nodes.csv`（**953** 节点）、
  `causal_edges.csv`（**836** 边）、`causal_branches.csv`、`chain_edges.csv`、
  `chain_branches.csv`、`authoritative_trace_index.csv`（120 条溯源）、
  `per_sample_e2e_paths/*.md`（120 条逐样本端到端路径）、`PARTIAL23_REPAIR_EVIDENCE/`、
  `retry2_evidence_index.json`、`retry2_map.json`。
- **MMU_FINAL_RAW_AND_SOURCE.zip**（原始数据 + 源码，400 文件）：`runs/W5X3_RETRY2/`
  （0202c 定向补全 Trace）、`runs/W5X3_OBS/`（**0222 定向复跑：CTRL-OBS-M07-C02 +
  M07-F0-W14-W5X3-OBS-C02-T01/T02**）、`runs/pilot/M06-C05/`（M06-C05 Pilot 证据）、
  `gem5_source/`（19 个关键源码文件）、`source_patches/Frozen_Source.patch` +
  `source_patches/gem5_observational_changes.diff` +
  `source_patches/0222_lsq_translation_lifecycle.patch` + `docs/0202c_*.md`、
  `SOURCE_SNAPSHOT.md`、`campaign/`（分析脚本 + rcs）、`workloads/mmu_w5x3/`、
  `disasm/`、`analysis/eligible_events/`、`REPRODUCTION.md`。

## 3. 原始数据来源

| 数据 | 位置 | 内容 | SHA256 |
|---|---|---|---|
| 原始 117 条 Trace（round 0202） | `MMU_Propagation_Traces.tar.zst`（冻结交付目录内，26 815 513 B） | 117 个 `runs/W5X3/M0*-F0-*/` 完整 Trace/日志/manifest，1059 条目 | `2cc957bf46dc5048d4e56c28fb0b7a6c98c70a96249b5e70b208a8269782f836` |
| Golden / Control Trace | `MMU_When_Golden_Evidence.tar.gz`（冻结交付目录内，9 506 960 B） | 39 条 Control + M01 ASID/DISC 发现运行的 Trace、eligible 事件流 | `b7e54cddccc565d2f380d864746069dee7a97d8e23c9a2abc2c45848713bab69` |
| RETRY2 Trace（0202c 定向补全） | `MMU_FINAL_RAW_AND_SOURCE.zip` 内 `runs/W5X3_RETRY2/` | 23 条 Fault + 11 条 Control 完整 Trace | 逐条见 `authoritative_trace_index.csv` |
| W5X3_OBS Trace（0222 定向复跑） | `MMU_FINAL_RAW_AND_SOURCE.zip` 内 `runs/W5X3_OBS/` | M07-C02-T01/T02 Fault + 匹配 Control（新 Build `ce80a9c9…`）完整 Trace | T01 `3dcdd1a9…`、T02 `522e21b8…`、Control `19061f4c…` |
| Pilot Trace（M06-C05） | `MMU_FINAL_RAW_AND_SOURCE.zip` 内 `runs/pilot/M06-C05/` | pilot_result.json / rcS / command / board.terminal / trace | 见 `M06_C05_PILOT_EVIDENCE.md` |
| Fault-Control 对照 | `control_map.json` / `fault_control_compare.csv` | 120 条逐样本 ControlID/ControlRunID/BuildHash/TraceSHA256 | — |

**构建版本对应**：
- `741cdc567f4894448ed9aea08bcf9f9db2d65f42e089becac587890bfe9047b3` — 原构建。
- `eb327197c073dddf039fdb63662d2cfa266394507ae0cb4630d0f4ff4dd76f65` — 0202c + IFU 埋点 + `masked_reason`。
- `fb1b6f010034f27312f2df215e00ada08cb7df811ef7425e4585b623a7e1d3f8` — 0202c + `MMU_CONSUMER_REUSE_CAP=16`。
- `ce80a9c983b31f77c9b4a6626012505fd3484d5c00df5b9399a9d6975ab2b73d` — **0222 LSQ 翻译生命周期观测**（M07-C02-T01/T02 + CTRL-OBS-M07-C02；当前磁盘二进制）。

## 4. 源码信息

- **gem5 版本**：25.1.0.1。
- **Build Hash**：`ce80a9c983b31f77c9b4a6626012505fd3484d5c00df5b9399a9d6975ab2b73d`（0222）。
- **构建命令**：`cd CHAOS/gem5 && scons -j<N> build/ARM/gem5.opt`（build_opts=`ARM`，GCC 10.3.1）。
- **源码 Patch**：`source_patches/Frozen_Source.patch`（故障注入 92 文件）+
  `source_patches/gem5_observational_changes.diff`（0202b）+
  `docs/0202c_source_diff.md`（0202c）+
  `source_patches/0222_lsq_translation_lifecycle.patch`（0222 LSQ squash-discard 观测）。
- **关键源码**：`gem5_source/` 19 文件 + `SOURCE_SNAPSHOT.md`（含 0222 附录 A）。
- **复现入口**：`REPRODUCTION.md`（ZIP3）/ `resume.sh`；0222 定向复跑：`python3 work/rerun_m07_c02_obs.py`。

## 5. 最终证据边界

- **M07-C02-T01/T02 = SQUASHED_BEFORE_MEMORY_ACCESS（FULL，0222 运行时证明）**：M07
  one-shot 权限反转使翻译返回 `NoFault` 并发 `lsu_request`；翻译响应随后被 LSQ 接收，
  因该负载已在页表游走期间被 squash，请求被 `SingleDataRequest::finish ->
  squashTranslation()` 丢弃、并阻止进入 Cache。运行时证据（逐级 `parent_event_id` 相连、
  `fault_id=1`）：`translation_response_received -> squash_translation_decision(
  discard_due_to_prior_squash, released=1) -> squash_translation_invoked ->
  translation_request_discarded(prior_squash_before_translation_completion) ->
  cache_dispatch_decision(cache_dispatch_blocked_by_squash)`。Control（CTRL-OBS-M07-C02，
  同 Build）同 load 为 `translation_result(fault_status=Data)`、无 `lsu_request`，证故障确实
  改变微架构路径但被消耗在已死（squash）指令上。**Guest SIGSEGV 不归因于故障动态指令**
  （`fault_status=NoFault`），而是 execute-only 架构拒绝。详见
  `M07_C02_T01_COMPLETE_PROPAGATION.md` / `M07_C02_T02_COMPLETE_PROPAGATION.md`。
- **M06-C05 三条 N/A（`INFEASIBLE_SPECULATIVE`）**：冻结 O3 fetch 不投机预测 indirect-branch
  目标，speculative wrong-path 冷走查无法在冻结 workload/config 下确定构造。见
  `M06_C05_PILOT_EVIDENCE.md`。
- **FULL 传播链所依据的终态证据**：SDC（74）以故障 oracle ≠ 同配置 Control 为终态，
  多分支 DAG 上 0 条 SDC 以 squash 终止；ACTIVATED_MASKED（15）/PROPAGATED_BUT_SQUASHED（9）/
  DETECTED_DELIVERED（9）/ACTIVATED_UNCONSUMED（5）/DETECTED_LOCALLY（3）/
  SQUASHED_BEFORE_MEMORY_ACCESS（2）均以观测事件为终端。

## 6. 已完成的验收（A01–A22 复跑 + 追加检查）

**A01–A22**：全部 PASS（A09/A13/A19/A22 为 PASS_WITH_DECLARED_GAPS/SCOPE）。0222 轮
A21 引用指向 `M06_C05_PILOT_EVIDENCE.md`。

**追加一致性检查（0222 轮复跑，全部通过）**：

| 检查项 | 结果 |
|---|---|
| 120 条件一致性 | PASS — `experiment_status.csv` 120 行；COMPLETE 117 + N/A 3；FULL 117 + FILE_MISSING 3 |
| 全部因果边连通性 | PASS — `causal_edges.csv` 836 边 / `causal_nodes.csv` 953 节点；dangling source 0 / target 0 |
| Trace SHA256 | PASS — 117/117 逐样本 `TraceSHA256` 与实际文件一致；0 mismatch（3 条 M06-C05 为 N/A） |
| Control Mapping | PASS — `control_map.json` 120 条，40 个逻辑 `ControlID`；T01/T02 `ControlRunID`=CTRL-OBS-M07-C02 |
| T01/T02 完整链 EventID | PASS — T01 351(activate)→352→353→354→355→356→357(discard)→358(blocked)；T02 599→600→601→602→603→604→605(discard)→606(blocked) |
| 七个因果环节 | PASS — activation→translation→LSU→squash decision→squashTranslation→discard→no-cache 全部有运行时事件 |
| 源码完整性 | PASS — `gem5_source/` 19 文件 + 0222 patch 与磁盘 `CHAOS/gem5/src/` 一致 |
| ZIP 解压测试 | PASS — 三包 `unzip -t` 无错；完整解压 21/141/400 文件成功 |

## 7. 冻结声明

MMU 实验设计、M01–M08 故障模型、C01–C05 上下文、T01–T03 注入时机、**117 FULL /
0 PARTIAL / 3 N/A** 结论正式冻结。后续不再主动扩大 MMU 实验范围，亦不执行 Git
add/commit/push/远程仓库操作。V3 历史交付包（`exports/MMU_E2E_V3_FINAL_DELIVERY/`）
保持不变。
