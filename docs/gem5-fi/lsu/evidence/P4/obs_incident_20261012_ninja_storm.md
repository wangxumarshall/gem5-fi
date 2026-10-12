# 事故报告：外部 ninja 构建风暴中止 AGU P4 批次（2026-10-12 18:31-18:35）

> 记录人：服务器总负责人（LSU 轨道）。等级：**基础设施外部干扰**；无数据污染、
> 无二进制漂移、无伪样本。所有保护机制按设计工作。

## 1. 事件时间线（全部为实测证据）

| 时间 | 事件 | 证据 |
|---|---|---|
| 18:09 | 4 driver 正常运行（A ITEM-006 act95/385、B ITEM-004 act79/385、C ITEM-024 act95/385、D ITEM-001 act450/2401） | 巡检记录 + driver logs |
| **18:31:49** | **外部构建启动：`ninja` + 129× `cc1plus`**（非本仓库——本仓库构建用 scons，且 CHAOS/gem5/build 与 repo build/ 在 18:00 后零变化；ninja 产物不在本仓任何路径） | guard_events.log 首个含 cc1plus 的 gate 事件（mem 已跌至 13.88GiB） |
| 18:31:49-18:34 | guard GATE 按总方针 §8.3 拒绝全部新 acquire（"存在编译进程"）；MemAvailable 22.13→**7.22→5.73→4.57GiB**（18:32-18:34 三拍，谷值低于 guard 硬 TRIP 线 6GiB）；blocked=2 | hostmon JSONL 逐拍 + guard_events.log 30 条 gate 记录 |
| 18:31:58-18:34:56 | 4 个 driver 按 F-023 语义级联：每 item 首样本 GATE BLOCKED→GUARD_FAILURE（**不记账、不产生伪样本**）→烧穿剩余 items→进程正常退出（"campaign end"） | driver_{A,B,C,D}.log 尾部（GUARD_FAILURE 明细含 compile_processes 快照） |
| 18:32:40 | E2E watcher（PID 2102199）按设计触发（driver 退出+槽空两轮确认） | e2e_run_log.json |
| 18:32:40-18:40:16 | E2E 三次尝试全部撞上风暴窗口的门禁 → driver rc=1 → **validate=FAIL（诚实失败：无样本 COMPLETE，未伪造任何通过）** | handoff_e2e.json + e2e_watcher.nohup.log |
| ~18:35-18:37 | 外部构建结束（进程消失）；MemAvailable 回升 13.72→17.11→22.64GiB | hostmon JSONL |
| 18:44:06 | hostmon 记录 TRIP_DOWN（cap 保持 4）；si/so 全程 0（无换页） | slot_policy.json |
| 18:46-18:49 | 总负责人巡检发现；取证（二进制 sha `10590f62…` 与 mtime 10-11 02:19 **均未变**；主树 HEAD `3a5e96d5` 未动；claims 空、槽空） | 本报告 §3 |
| **18:49:38** | **E2E 重跑启动**（干净窗口：槽空、MemAvailable 23.3GiB、无编译进程；复用冻结选样；staging 残留自动隔离） | e2e_rerun_20261012_1848.log |

## 2. 影响与完整性判定

- **AGU P4 冻结批次未完成即中止**：31 RunID 中仅 ITEM-002/003/020 达标完成，
  ITEM-001/004/006/024 进行中（样本级可 resume），其余 23 项未启动。批次完整性
  无损：GUARD_FAILURE 样本不记账（F-023），resume 机制复用有效前缀。
- **无数据污染**：所有已落盘 verdict 均为 run-finish 完整周期产物；E2E 失败
  尝试零 COMPLETE（不复活）。
- **无漂移**：gem5.opt sha256/mtime 复核不变；主树 HEAD 不变；冻结 manifest 仍有效。
- **守卫/监控有效性实证**：GATE（编译进程+内存）、TRIP 判定（<8×2）、F-023
  级联不记账、watcher 互锁（两轮确认）、E2E 诚实 FAIL——全部按设计工作。

## 3. 处置决定（总负责人）

1. **不启动阶段二**（旧批次未自然完成；admission B/D/F 待 E2E 重跑落定）。
2. **E2E 立即重跑**（18:49:38 已启动，干净窗口）。
3. E2E 通过后：**恢复 AGU 4 driver**（原命令原样重启，样本级 resume；输出重定向
   至新日志 driver_{A,B,C,D}_r2.log，原日志保留为事故证据）——属协议 §7 常规
   调度（外部原因中止后续跑，非人为打断）。
4. 外部构建来源超出本轨道可见范围（进程已消失、产物不在本仓）；**呈报中央**：
   建议协调方查明 18:31 的 ninja -j~128 构建归属（多会话/其他项目），并约束其
   与实验批次的互斥（CLAUDE.md -j16 纪律仅约束本仓构建）。
5. hostmon TRIP_DOWN 状态保持（cap=4），30 分钟窗口无异常后自然回到 HOLD4。

## 5. 递发与后续（2026-10-12 19:14 追记）

- **风暴复发**：19:14 再现 ninja+cc1plus（本次 3 进程，MemAvailable 19.6GiB——
  远弱于 18:31 的 129 进程/4.57GiB）。外部构建呈**多波次**特征，归属仍不明
  （产物不在本仓）。再次印证 §3-4 呈请：协调方须约束外部构建与实验批次互斥。
- **E2E 重跑（18:49-18:57，干净窗口）结果**：B（golden 正常例）/D（Masked 样本
  五层全链 complete+replay verified）/F（审计+identity+hash）**PASS**；E（crash
  样本）暴露两个真 bug 并当场修复：
  - **跨环境不可复现（科学发现，非 bug）**：同 seed 下历史（PYTHONHASHSEED
    未固定+无 ctrace）与 obs 管线（PYTHONHASHSEED=0+ctrace）注入位点不同
    （s414: 0x48ff08@2799335 vs 0x7ffffefd30@2718100）→ 结局不可跨环境复现；
    管线内 replay 完全确定。E 判据修订 v2（`a5f23b67`）：crash 样本以 obs
    管线真实产出为准。**推论：AGU 历史样本补链必须用 obs 环境新样本。**
  - **BUG-4（`9da24486`）**：crash 早于 ctrace 首个 FLUSH_EVERY 刷盘点 → 0 字节
    trace → commit_diff 误判全量 instruction_flow_change（diverged/8039 点）。
    build_l2 前置守卫 + 审计器配套修复；s416/418/419 误导记录已隔离
    （`.quarantine.BUG4_misleading_diverged.*`，保留为证据），待修复版重生成。
- **自动恢复链**（`runs/lsu/obs/recovery_chain_20261012.sh`，PID 2139251）：
  等风暴清（≤120min）→ 内存门槛复核 → 重跑 3 crash 样本 → validate v2 →
  report → 原命令恢复 4 个 AGU driver。逐步留痕 `recovery_chain.log`。

```bash
cd /home/sdc/gem5-fi-ding
nohup python3 tools/lsu_w1_rerun.py --carrier checklist --unit-dir runs/lsu/pilot/AGU --phase screening --target 385 --campaign p4_agu_formal_20261012 --items ITEM-002 ITEM-006 ITEM-007 ITEM-008 ITEM-010 ITEM-014 ITEM-017 ITEM-018 ITEM-019 ITEM-021 ITEM-022 ITEM-023 ITEM-026 ITEM-027 ITEM-034 ITEM-035 ITEM-038 ITEM-039 > runs/lsu/pilot_w1/formal_logs/driver_A_r2.log 2>&1 &
nohup python3 tools/lsu_w1_rerun.py --carrier w1 --phase screening --target 385 --campaign p4_agu_formal_20261012 --items ITEM-003 ITEM-004 ITEM-005 ITEM-009 ITEM-015 ITEM-016 > runs/lsu/pilot_w1/formal_logs/driver_B_r2.log 2>&1 &
nohup python3 tools/lsu_w1_rerun.py --carrier w1 --phase screening --target 385 --campaign p4_agu_formal_20261012 --items ITEM-020 ITEM-024 ITEM-025 ITEM-036 ITEM-037 > runs/lsu/pilot_w1/formal_logs/driver_C_r2.log 2>&1 &
nohup python3 tools/lsu_w1_rerun.py --carrier checklist --unit-dir runs/lsu/pilot/AGU --phase screening --target 2401 --campaign p4_agu_formal_20261012 --items ITEM-001 ITEM-013 > runs/lsu/pilot_w1/formal_logs/driver_D_r2.log 2>&1 &
```
