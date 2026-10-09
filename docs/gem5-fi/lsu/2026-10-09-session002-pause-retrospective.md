# Session 002 暂停时点总结复盘报告（2026-10-09 09:13）

> 触发：用户指令"暂停任务，释放占用节点"（2026-10-09 09:1x，决策优先级最高层级）。
> 范围：集群 Session 002 全程（2026-09-30 16:43 keeper 起跑 → 2026-10-09 09:13 释放节点）。
> 诚实性：全部陈述对应实际执行过的命令与磁盘/远端证据；未执行不写、未验证不称通过。

## 一、任务定位与边界

- 十天长任务：占最空闲节点（节点名最大→最小遍历）+ dattach + 按 docs/gem5-fi/lsu 方案推进。
- **DR-003 裁决 A**（用户 2026-10-08）：旧机续跑波次 5 + 并发保持 4；**集群侧不跑波次，仅平台工程**。本会话全程遵守。
- **F-041 技术约束**：集群平台 B census 基线 2767 ≠ 旧机 2772（O3 LSQ 错误路径发射计数时序敏感），样本不可交换——旧机/集群隔离升格为技术必需。

## 二、已完成工作盘点（按时间序）

| 阶段 | 内容 | 证据 |
|---|---|---|
| ① 兼容运行时 | gem5 compat loader + 中继依赖库（悬空链接/PYTHONHOME/OpenSSL3/tcmalloc，F-026） | evidence/P3/u1_gate_*.out |
| ② U1 | swap_na 移植 4 槽守卫（全集群无 swap 的门禁适配，F-027/F-028） | evidence/P3/u1port_4slot_swapna_cn23423.out |
| ③ U3b | 二进制身份恢复 CP1-CP6：CP4 守卫重建 af0d784f（gcc10.3.1/py3.9.9/HAVE_PROTOBUF=0 与旧机差异显式记录）→ CP4v PEP604 崩溃修复（F-040）→ CP5 census 两遍法 2767×2 → CP6 确定性双跑 PASS | runs/lsu/det/u3b_*；lsu_keeper/u3b_cp6.log |
| ④ U3 | LSU_GEM5_BIN 接线（gem5_bin() + manifest gem5_invocation + 假阳性响亮化 F-042） | lsu_keeper/u3_verify2.log |
| ⑤ U6 | 守卫槽位复验 T1-T6（含陈旧槽 clear-stale 语义；exit=1 期望修正） | evidence/P3/guard_slots_verify.out |
| ⑥ F-038 draft | campaign v2 十二任务四提交（M1-M12b：2401/385 采样、两层率、config_fp 指纹、per-seed verdict、前缀 resume）；12/12 测试 PASS + dry-run 与正式文件逐字节一致；应用替换待六条安全边界 | tools/draft/；b4de97cf |
| ⑦ 跨会话整合 | 22+ 次并行会话提交合并中继；E-013 F 编号撞号修复 + "fetch 后起号"规则固化 | progress.md ⑩；git log |
| ⑧ keeper | cn23423 连续独占 8 天 16.5 小时（1773102）；续期单竞态加固（dkill 1824007 → 1830226 起跑门控 + prio 100） | djob 记录；progress.md ⑧ |
| ⑨ gap-1 计划 | T05-T08 TLB 模式实施方案（17 缺口分组第一组，15 cell） | 43ab2400 |
| ⑩ gap-1 Task 0 | 集群 FS 管线基线：golden oracle 复现 10/10（wall ~38 min，cap 校准 1800→3600s）；t01 注入基线（~50s Crash） | runs/lsu/guard/gap1_t0_*.log |
| ⑪ gap-1 Task 1 | **T05 状态四子模型**（valid清零/伪置位/global翻转/ASID替换）+ numT05State；E-014 const 视图修复；rebuild2 exit 0 零新增 warning；冒烟×4 全存活（Masked，oracle 金标 10/10）；**T01 回归字节一致** | 015080ba；/tmp/gap1/*；guard 日志 |

## 三、暂停时点状态（2026-10-09 09:13）

- **节点已释放**：dkill 1773102（FAILED，cn23423 于 09:13:01 释放）+ dkill 1830226（FAILED，续期链终止）。
- **自动化全撤**：会话 cron ×2 取消（6h 巡检 + 10-10 16:50 接管核验）——防自动重占。
- **进程全清**：gem5=0/scons=0/cc1plus=0/guard=0（一次 pgrep guard=2 为自匹配伪像，bracket 模式复核为 0）。login01 MemAvailable 316 GiB。dattach×3 非 LSU 会话进程（归属不明，未动）。
- **三仓收敛**：origin = nscc = 集群 fi-ding = **6f062b82**（OOO U3/U4 经 relay-sync 合并 + 暂停记录 860f50f1 + gap1-T05 015080ba）。
- **冻结点**：gap-1 Task 1 完成并验证；Task 2（T06 换值）/Task 3（T07 way-select）/Task 4（T08 walk-refill）/Task 5（DET 双跑 + F-044）未开始（计划框未勾）。

## 四、关键教训（错误→规则）

1. **E-009/F-040 PEP604 运行时求值**：py3.9 面对 simulator.py:104 `Optional[str | Path]` 崩溃——二进制内嵌解释器版本参与行为面，任何平台重建后首跑必须过冒烟门禁。
2. **E-012/F-042 假阳性**：`--item --execute` 静默忽略 --execute、5 秒返回 exit 0——"退出码 0 ≠ 通过"，端到端验证必须证明目标真的运行（时长/输出目录/进程轨迹三重证伪）。
3. **E-014 entryTable const 视图**：tlb.hh:208 无非 const 访问器，跨表项变异需 const_cast（表为非 const tlb 的可变成员，soundness 论证入注释）。
4. **scons -j8 非 keep-going**：单目标失败即停排新任务、整体 exit 2——失败后重试是断点续编，不是全量重来。
5. **pgrep/pkill -f 自匹配**：模式串出现在自身命令行 → 无限循环/自杀；一律 bracket 模式 `[p]attern` 或 -x 精确名。
6. **渠道物理特性**（reach 通道）：~15KB 命令上限（heredoc 分块）；前台 sleep 被封（有界 for 循环替代）；后台任务随机 exit 125 但服务端 setsid 进程存活（以磁盘产物为准，不依赖通知）。
7. **oracle 载体勘误**：计划模板写 console.txt，实际为 board.terminal（lsu_campaign.py:356）——文档断言以代码读取路径为准。
8. **磁盘配额事件**（10-08 23:00）：用户配额 ~1T 触顶致 EIO/EDQUOT——删除 4.8G 冗余传输快照后恢复；大文件不入库纪律再次验证。

## 五、未决事项（恢复时需处理）

| 事项 | 状态 | 责任 |
|---|---|---|
| DR-002（17-gap injector models 用户裁决） | PENDING | 用户 |
| campaign v2 draft 应用替换正式文件 | 待六条安全边界（WAVE_DONE 等） | 集群会话（恢复后） |
| gap-1 Task 2-5（T06/T07/T08 + DET 双跑 + F-044） | 未开始，无阻塞 | 集群会话（恢复后） |
| 波次 5 resume / W1+W13 载体补建 | 旧机会话职责（DR-003-A） | 旧机会话 |
| keeper 重新占位 | 用户恢复指令后按节点名最大→最小遍历重占 | 集群会话 |

## 六、恢复路径（无阻塞验证过）

1. 重占节点（dnode/dqueue 遍历 + 独占 keeper + dattach）。
2. 集群 repo fi-ding@6f062b82 完好；build/ARM/gem5.opt = db6b358c（T05 已编入）。
3. B0 checkpoint runs/fs_lsu/boot_b0/cpt.237949797015 + tlb_probe.rcS 载体就绪（Task 0 已验证）。
4. 直接从计划 Task 2（T06 三子模型）开始，沿用公共模板（--max-seconds 3600、board.terminal 判定、T01 回归 diff）。

## 七、证据索引

- 守卫事件：runs/lsu/guard/gap1_*.log、u3b_*.log
- gap-1 产物：/tmp/gap1/*（注入日志、board.terminal、构建日志）——/tmp 重启后丢失，关键摘录已入 progress.md；F-044 收口时按惯例摘录入库
- 平台工程：lsu_keeper/*.log、evidence/P3/*
- 过程记录：docs/gem5-fi/lsu/progress.md Session 002 ①-⑪ + 暂停记录；findings.md F-026..F-043
