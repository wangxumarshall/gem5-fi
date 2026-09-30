# OOO P0 工程通过：守卫/租约/恢复原语（G0-10 建立与测试）

日期：2026-09-30 · 分支：ooo-exec（worktree /home/share/suke/wangxu/gem5-fi-ooo）· 依据：docs/gem5-fi/ooo/task_plan.md P0 清单第 8 项 + 总方针 §8

## 背景与目标

P0 要求"建立并测试编译单实例锁、实验 worker lease 注册表、并发上限4、资源守卫、任务心跳、30分钟状态更新、原子 COMPLETE 标记和恢复扫描"。现状：
- 编译单实例锁已实测（flock runs/ooo-node/state/gem5-build.lock，二次获取被拒，2026-09-30 17:25）。
- LSU 轨已有 `tools/lsu_guard.py`（§8 可审计实现）与 campaign/COMPLETE 约定；OOO 轨需要同构原语，路径与语义按 OOO 计划（runs/ooo/…，run_key=campaign/phase/RunID/sample_index/seed/config_sha）。
- 集群事实（findings F-005）：login01 与计算节点均无 swap → SwapFree 门禁结构性不可满足，策略改为"SwapTotal>0 才评估 swap 门禁；MemAvailable 为权威"，写入代码注释与文档。

非目标：注入器/观测链（P1）、负载与 golden（P2）、campaign 主循环（P1 与 ooo_pilot 一并实现）。

## 单元分解（one patch per unit）

> 2026-09-30 修订：远端 fi-ding 前进至 f0a5b249，LSU 轨 F-022/F-023 已把 experiment 锁升级为
> 4 槽位（= worker lease + 并发≤4，含确认释放/陈旧处置/隔离测试目录）。原 Unit 2（独立
> ooo_lease.py）被其覆盖，并入 Unit 1；OOO 适配基座同步切换为 f0a5b249 版 lsu_guard.py。

### Unit 1：`tools/ooo_guard.py` — OOO 资源守卫（适配自 f0a5b249 版 lsu_guard.py，含 4 槽实验锁）
- [x] 实现 gate / acquire / release / clear-stale / status / run / sample 子命令；锁目录 `runs/ooo/guard/`（build.lock、experiment_slot_0..3.lock、guard_events.log；OOO_GUARD_DIR 可覆盖——隔离测试用）。
- [x] build 单实例；experiment 4 槽位 = 实验并发硬上限 4（F-022 同源设计）；释放须 --slot+--confirm-pid 防误删；陈旧锁必须 clear-stale 显式处置（F-023 语义：不静默绕过异常中断的守卫周期）。
- [x] gate：MemAvailable<12GiB 阻断；**SwapTotal>0 且 SwapFree<4GiB 才阻断**（本集群无 swap，findings F-005，豁免并显式标注）；存在编译进程或 build 锁被占阻断。
- [x] WARNING<10GiB；TRIP=MemAvailable<8GiB 连续两次或任一次<6GiB 或（SwapTotal>0 且 SwapFree<2GiB）；TRIP 仅对锁内记录、存活核实的本任务 PGID TERM→KILL。
- 验证（真实命令，2026-09-30 login01 实测引用，f0a5b249 4 槽版）：gate ok=False（编译进程在跑=正确阻断）+swap_exempt_note+slots 字段；4 存活槽→第 5 次 acquire REFUSED（列出全部持有者）；错误 --confirm-pid 释放 REFUSED（不得释放他人槽）；陈旧槽存在时 acquire REFUSED（F-023 显式处置语义）；clear-stale 按槽清除+不匹配 NOTE；清后 re-acquire 成功入槽；status 4 槽归零。**待补（build 完成后）**：`run` 全流程（gate 通过后的真实命令，含采样/TRIP/释放收尾）。

### Unit 2：`tools/ooo_recover.py` — 原子 COMPLETE 标记 + 恢复扫描（原 Unit 3）
- [ ] mark-complete：结果目录内 `COMPLETE.json`（tmp 写入 + rename 原子落位，含 run_key、exit、分类、证据路径、sha256）。
- [ ] scan：遍历 `runs/ooo/`，输出每 run_key 状态 COMPLETE/INTERRUPTED(有 lease 无 COMPLETE)/MISSING(无 lease 无 COMPLETE)/ORPHAN(有 COMPLETE 无记录)，--json 可机读；只报告不修改（恢复动作由 campaign 决策）。
- 验证：在 runs/ooo/selftest/ 下构造 COMPLETE/陈旧 lease/空目录三态 → scan 输出与构造一致。

### Unit 3：文档与 G0 填表（[OOO][P0] 收口提交；原 Unit 4）
- [ ] task_plan.md G0 表：G0-01（build 证据）、G0-03（环境锁定）、G0-05（负载盘点+W1 缺口）、G0-08（seed/run_key 规则落地确认）、G0-10（本计划三单元测试输出）填状态与证据；G0-02/04/06/07/09 保持 UNCHECKED 并注明归属 P1/P2 的缺失项。
- [ ] findings/progress 同步；W1 MiBench 源缺失 + "FS优先" vs SE 基线 → Decision Request 记录。
- [ ] 提交：Unit 1/2/3 各一个 commit，Unit 4 一个 commit，格式 `[OOO][P0] …`。

## 验证总则
每个 Unit 的验证命令必须在 login01 真实执行并引用实际输出；不通过不得 commit。构建中 gem5.opt（gem5-build-001.out）完成前，本计划三单元可并行开发但按序提交。
