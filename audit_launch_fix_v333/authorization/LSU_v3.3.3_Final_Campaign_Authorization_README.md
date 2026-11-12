# LSU v3.3.3 — Final Campaign Authorization Packet

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**Binary:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
**Config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Campaign ID:** `LSU-V333-FINAL-20261112`
**Campaign root:** `runs/lsu/formal_v333_final_20261112`

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
- 正式输出根：`runs/lsu/formal_v333_final_20261112`（当前不存在，不会覆盖
  pre-formal `audit_v3_3_3/runs/` 或历史 `runs/lsu/formal_v333`）。
- 锁文件与 Campaign ID 绑定：`runs/lsu/formal_v333_final_20261112/.lsu_v332_matrix.lock`。
  旧目录中的锁文件不影响本 Campaign。

## 3. Runner 启动命令（已实测 dry-run）

最终命令块位于
`audit_v3_3_3/trace_closure/final_config/launch_commands_final.sh`，分阶段执行：

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12

# 0) preflight: frozen binary/config hashes only
bash audit_v3_3_3/trace_closure/final_config/launch_commands_final.sh preflight

# 1) dry-run: 120 unique tasks, no dirs, no gem5
bash audit_v3_3_3/trace_closure/final_config/launch_commands_final.sh dry-run

# 2) formal launch (120 runs; 60 fault + 60 control)
bash audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh

# 3) after interruption: resume only unfinished/failed attempts
bash audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh --resume

# 4) collect from THIS campaign root only
bash audit_v3_3_3/trace_closure/final_config/02_manifest_only.sh
bash audit_v3_3_3/trace_closure/final_config/03_full_collector.sh

# 5) final propagation + readiness + 8-sheet Excel
bash audit_v3_3_3/trace_closure/final_config/04_final_reports.sh
```

All four scripts pin the frozen binary, config, Campaign ID and campaign root.
`01` refuses a non-empty campaign root unless `--resume` is given. Attempts are
isolated under `<run>/attempts/attempt_NNN/`; a completed attempt is never
overwritten, and exactly one canonical attempt is accepted per identity.

## 4. 资源计划

- 宿主：126 逻辑核，29 GB RAM（约 25 GB available）。
- 硬上限：≤ 4 个并发 gem5 进程；本 runner 为串行（campaign lock），
  实际同时只有 1 个 gem5 进程。
- Binary 大小 1,149,269,352 bytes。
- 不得用 `-j` 并发启动多个 runner 实例；锁文件为
  `runs/lsu/formal_v333_final_20261112/.lsu_v332_matrix.lock`。
- `--force` 不能绕过锁。

## 5. 预计运行时间

- pre-formal 实测：120 runs 共 429.1 s（mean 3.6 s，max 21.3 s）
  → 纯仿真约 7.2 min。
- 正式预计 10–30 min（含每 run 开销与 oracle 检查）。
- 最坏情况由 per-task timeout 限制：A03/RP01 direct 180 s / 400 s；
  `run_pilot` 400 s。

## 6. 失败恢复策略

1. 非零退出：runner 对 FAILED / TIMEOUT / OUTPUT_INCOMPLETE /
   HASH_MISMATCH / CONTROL_PROOF_INCOMPLETE 返回 exit 1；先看 stderr。
2. 已有输出根时 runner 拒绝启动；使用 `--resume` 只补跑未完成任务。
   已 COMPLETED 的任务被跳过，已接受的原始终点结果不被替换。
3. 单任务失败：保留 `attempt_NNN` 现场，新一次执行写入 `attempt_NNN+1`；
   不允许覆盖旧 Attempt。
4. Binary/Config SHA 不一致：runner 在 preflight 直接失败（HASH_MISMATCH），
   `--resume` 拒绝自动重试；先修正配置，不要删除历史 Attempt。
5. ORACLE_FAIL 是已测量的终点（SDC 等），不是模拟器执行失败；`--resume`
   不会自动重跑并替换它。
6. 若 collector 报告 `non_formal` 或 `MISSING_EVIDENCE`：确认 `--runs`
   指向 `runs/lsu/formal_v333_final_20261112`，而不是 `audit_v3_3_3`
   或历史 `runs/lsu/formal_v333`。
7. 不要在失败后删除 campaign 根；历史结果与 Attempt 必须保留。

## 7. 正式结果收集与 Manifest 生成

- runner 在每个 `<run>/attempts/attempt_NNN/` 写 `attempt.json` 和
  `campaign.json`；在 campaign 根写 `campaign_identity.json` 和原子化
  `campaign_index.json`。
- collector 只从 `--runs` 指向的 campaign 根收集，并通过 `canonical.json`
  选中唯一被接受的 Attempt；`--manifest-only` 只生成核心 manifest。
- Control 零注入判定严格三态：`0 → NO`、`>0 → YES`、缺失/非法 →
  `UNKNOWN`/`INVALID`（不再是默认 `NO`）。任何 Control 缺乏可靠证据时，
  整体 Control Validation 不能报告 PASS。
- collector 结果应满足：`formal=120 non_formal=0`，且 exit 0。
- A03/SP05/RP01 的 `QUALIFIED`/`TRACE_INCOMPLETE` 会原样记录，
  不会被升级为 PASS。

## 8. 授权前检查清单

- [x] 30/30 Override 有明确研究者批准（A 类）
- [x] 12 模型 / 60 SampleRunID / 60 Seed / 60 ROI / 60 Fault / 60 Control 一致
- [x] 60/60 Fault-Control 配对（同 Seed、同 SampleRunID、同 ROI、同 ordinal）
- [x] Binary SHA = `62e1b1be…`（worktree 实测）
- [x] Config SHA = `8309da72…`（实测，`configs/se/lsu_proxy.py`）
- [x] 9 个 ELF SHA 与 oracle audit 一致（真实字节重算）
- [x] runner dry-run = 120 unique commands, nothing written
- [x] 输出根 `runs/lsu/formal_v333_final_20261112` 不存在
- [x] Campaign lock 与 Campaign ID 绑定，旧锁不误判
- [x] Resume/Attempt 恢复路径已测试
- [x] Control Zero Proof 严格三态，缺失证据 fail-closed
- [x] QUALIFIED/TRACE_INCOMPLETE 已披露，未升级
- [ ] 研究者明确下达正式 Campaign 启动指令 ← **唯一剩余项**

**最终状态：`READY_FOR_RESEARCHER_AUTHORIZATION`**
