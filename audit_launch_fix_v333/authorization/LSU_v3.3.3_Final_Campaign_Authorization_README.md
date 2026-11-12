# LSU v3.3.3 — Final Campaign Authorization Packet

**Date:** 2026-11-12  
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`  
**Branch:** `lsu-v3.3.1-context-workload-20261111`  
**HEAD:** `13c029e51d6ef3df4fc3de85e1e21a20a4defa9a`  
**Binary:** `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`  
**Config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`  
**Campaign ID:** `LSU-V333-FORMAL-20261112`

**本包只准备授权，不启动 Campaign。** 正式运行必须在研究者明确下达启动
指令后执行。

## 1. 包内容

| # | 文件 | 内容 |
|---|---|---|
| 1 | `LSU_v3.3.3_Final_Workload_Approval_Report.md` | 最终 workload 审批报告 |
| 2 | `LSU_v3.3.3_Final_Workload_Approval_Packet.xlsx` | 30 个 Override 明细、证据、一致性检查 |
| 2a | `LSU_30_Override_Detail.csv` | 30 个 Override 的机器可读明细（18 列） |
| 3 | `LSU_v3.3.3_Qualified_Evidence_Disclosure.md` | A03/SP05/RP01 证据限制 |
| 3a | `LSU_Qualified_Status_15Contexts.csv` | 15 个受限上下文的逐条状态 |
| 4 | `LSU_Formal_Experiment_Config_Final.xlsx` | 最终实验 Excel（原样副本） |
| 5 | `LSU_120Run_Task_Map.csv` | 120 个任务映射 |
| 6 | `LSU_60Fault_60Control_Pair_Map.csv` | 60 组 Fault-Control 配对 |
| 7 | `LSU_Final_Binary_Provenance.md` | Binary/Config/ELF provenance |
| 8 | `LSU_120Run_Campaign_Manifest.csv` | 120 行设计清单 |
| 9 | `LSU_60Context_Final_Readiness.csv` | 60 行 readiness |
| 10 | `LSU_120Run_Formal_Manifest_Schema.csv` | 46 列 manifest schema |
| 11 | `launch_commands.sh` | 已验证的启动命令 |

## 2. 存活路径与身份

- 必须在 `lsu-platform-v3.2.12` worktree 运行；runner 的 `ROOT` 即该 worktree。
- 主仓库旧 binary `6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4` **不得使用**。
- 正式输出根：`runs/lsu/formal_v333`（当前不存在，不会覆盖 pre-formal
  `audit_v3_3_3/runs/`）。

## 3. Runner 启动命令（已实测）

本节命令的参数来自 `tools/lsu_v332_matrix.py` 的实际 `--help`，并已用
`--dry-run` 实测：**120 commands; no run dirs written**。

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12

# 1) 120 formal runs (60 fault + 60 control)
python3 tools/lsu_v332_matrix.py \
  --models all --roles fault,control --contexts 1,2,3,4,5 \
  --out-base runs/lsu/formal_v333 \
  --out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv \
  --campaign-id LSU-V333-FORMAL-20261112 \
  --expected-binary-sha 1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338 \
  --expected-config-sha 8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
echo "runner_exit=$?"

# 2) collect the formal manifest from THIS campaign root only
python3 tools/lsu_v333_launch.py \
  --runs runs/lsu/formal_v333 \
  --campaign-id LSU-V333-FORMAL-20261112 \
  --design-matrix docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv \
  --design-mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \
  --out runs/lsu/formal_v333/collector \
  --manifest-only
echo "collector_exit=$?"
```

## 4. 资源计划

- 宿主：126 逻辑核，29 GB RAM（约 25 GB available）。
- 硬上限：≤ 4 个并发 gem5 进程；本 runner 为串行（`matrix_lock`），
  实际同时只有 1 个 gem5 进程。
- Binary 大小 1,149,173,888 bytes。
- 不得用 `-j` 并发启动多个 runner 实例；锁文件为
  `runs/lsu/formal_v333/.lsu_v332_matrix.lock`。

## 5. 预计运行时间

- pre-formal 实测：120 runs 共 429.1 s（mean 3.6 s，max 21.3 s）
  → 纯仿真约 7.2 min。
- 正式预计 10–30 min（含每 run 开销与 oracle 检查）。
- 最坏情况由 per-task timeout 限制：A03/RP01 direct 180 s / 400 s；
  `run_pilot` 400 s。

## 6. 失败恢复策略

1. 非零退出：runner 对 FAILED / TIMEOUT / OUTPUT_INCOMPLETE /
   HASH_MISMATCH / CONTROL_PROOF_INCOMPLETE 返回 exit 1；先看 stderr。
2. 已有输出目录时 runner 拒绝覆盖（需 `--force`）；默认**不要**加 `--force`，
   保留现场。
3. 单任务失败：保留失败的 outdir，记录 (ModelID, ContextID, Role)；
   修复外部原因后只重跑该任务（用 `--models <M> --contexts <n>`），
   不要重跑全部 120 个。
4. Binary/Config SHA 不一致：runner 在 preflight 直接失败；检查是否误用
   主仓库 binary。
5. 若 collector 报告 `non_formal` 或 `MISSING_EVIDENCE`：确认 `--runs`
   指向 `runs/lsu/formal_v333`，而不是 `audit_v3_3_3`。
6. 不要在失败后删除 `runs/lsu/formal_v333`；如需全新根目录，改用新的
   `--out-base`（例如 `runs/lsu/formal_v333_rerun1`）。

## 7. 正式结果收集与 Manifest 生成

- runner 在每个任务目录写 `campaign.json`；campaign 根写
  `campaign_identity.json`。
- collector 只从 `--runs` 指向的 campaign 根收集；
  `--manifest-only` 只生成核心 manifest，不导出完整报告。
- collector 结果应满足：`formal=120 non_formal=0`，且 exit 0。
- A03/SP05/RP01 的 `QUALIFIED`/`TRACE_INCOMPLETE` 会原样记录，
  不会被升级。

## 8. 授权前检查清单

- [x] 30/30 Override 有明确研究者批准（A 类）
- [x] 12 模型 / 60 SampleRunID / 60 Seed / 60 ROI / 60 Fault / 60 Control 一致
- [x] 60/60 Fault-Control 配对（同 Seed、同 SampleRunID、同 ROI、同 ordinal）
- [x] Binary SHA = 1126e0fd…（worktree 实测）
- [x] Config SHA = 8309da72…（实测）
- [x] 9 个 ELF SHA 与 oracle audit 一致
- [x] runner dry-run = 120 commands, nothing written
- [x] 输出根 `runs/lsu/formal_v333` 不存在
- [x] QUALIFIED/TRACE_INCOMPLETE 已披露，未升级
- [ ] 研究者明确下达正式 Campaign 启动指令 ← **唯一剩余项**

**最终状态：`READY_FOR_RESEARCHER_AUTHORIZATION`**

