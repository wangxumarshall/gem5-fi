# OoO W4 Int Rename 注入器 Implementation Plan（首批：D12 + D13）

> **For agentic workers:** REQUIRED SUB-SKILL: subagent-driven-development。checkbox 跟踪。
> **Spec**：`docs/gem5-fi/ooo/04-design-matrix.md` D12/D13/D14 行 + `06-implementation-plan.md` §4 W4。冲突以 04 为准。

**Goal**：实现北极星第一批真故障模型：D12（RAT 双比特翻转）与 D13（RAT 换值 swap_to_active——**北极星推进序第一优先**，"从 ROB 里挑一个活跃物理寄存器号写入 RAT 表项"）。

**Global Constraints**（继承 W0-W2 全部纪律）：one-patch-per-unit（Task 1、Task 2 是两个独立提交单元）；增量构建 `-j126` 零新告警；每单元验证三件套 + smoke golden `45737cc9a76c0dce` 回归；并发 subagent ≤2；代理不 commit（编排者验证后提交）。

---

### Task 1: W4.1 — D12 RAT 映射字段双比特翻转

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh/.cc/.py`（加 `map_bitflip2` 模式：翻转 2 个随机比特）
- Modify: `configs/se/ooo_proxy.py`（`--rename_mode` choices 加 `map_bitflip2`）、`tools/runner.py`（rat 组件 fault.model `local_mbu`→`map_bitflip2` 路由）

**要求**：先读 CHAOSRenameMap.cc 弄清现有 `map_bitflip` 的确切注入位点与写法（注意 W2.4 发现：SimpleRenameMap::rename() 直写不走 setEntry，注入经 squash 回滚落 front 表——以源码实际为准）。`map_bitflip2` 在同一位点对 phys 索引翻转 **2 个随机不同比特**（rng 决定，非固定两比特）；日志行打印 `arch=X old_phys=Y new_phys=Z bits=(b1,b2)`。

**验证**：①构建零新告警；②定向单次注入（smoke + `--chaos_rename --rename_mode map_bitflip2 --rename_first_clock 200000`）：日志出现注入行且 new_phys 与 old_phys 汉明距离恰为 2（贴日志）；③再跑一次同 seed 复现一致（确定性）；④无注入回归 golden；⑤W2 观测链抽查：带 `--chaos_ctrace` 跑一次，commit_diff 对无注入参照应能出 L2 结论（diverged 或 truncated 均算通）。

### Task 2: W4.2a — D13 RAT 换值 swap_to_active（固定间隔）

**Files:** 同 Task 1（加 `swap_to_active` 模式）+ ooo_proxy/runner 路由。

**要求**（04 设计矩阵 D13 原文：「把该架构寄存器的映射，强制改成『另一条当前仍在飞的指令也在用』的物理寄存器号（**从 ROB 里随机挑一个活跃物理寄存器号写入**）」）：
- 同一位点注入时，遍历 ROB in-flight 指令的目的物理寄存器集合（`o3cpu->o3ROB()`，参考 CHAOSROB.cc 里 getEntryAtDistance/遍历用法），随机挑一个 ≠ 当前映射的活跃 phys id 写入 RAT 表项；
- ROB 为空或无候选时跳过本次（不注入、日志说明）；
- 日志行：`arch=X old_phys=Y new_phys=Z(active, rob_dist=D)`；
- F0（单次）/F1（固定间隔）用现有 first_clock/max_faults 机制即可（北极星 F4 事件触发版=D14 是下一单元，不在本 Task）。

**验证**：①构建零告警；②定向单次注入（smoke + branch_mispred 两个负载各一次）：日志出现换值行且 new_phys ∈ ROB 活跃集合（贴日志+ROB 证据）；③同 seed 复现一致；④无注入回归 golden；⑤**观测链端到端**：branch_mispred + swap_to_active 单次注入，带 `--chaos_ctrace` 跑，与无注入参照 commit_diff → L2 五分类结论贴出（这是北极星 D13 的第一份真实观测数据）；⑥L0 接线：注入后该 arch reg 的后续读取计数（用现有 readTrace 或日志说明可观测性）。

---

## 执行序
Task 1 → Task 2 串行（同一文件集，避免冲突）。D14（误预测恢复瞬间事件触发版）与 W4.3-W4.8 后续批次另行派发。

---

### Task 3: W4.3 — D15 RAT 卡死（F5 写路径 mask）
- [x] CHAOSRenameMap 加 `f5_rat_stuck`：运行开始随机选一个 RAT 表项的一个比特永久固定 0/1（各半），每次该表项被写都带着缺陷（**写路径 mask**，仿 CHAOSPhysReg setStuckTarget/G2 先例）直到被覆盖/结束；F5 语义=从存在起持续生效。验证：注入后多次 rename 该 arch 均带同一位缺陷（日志多次采样证明持续性）+ golden 回归 + 无注入回归。

### Task 4: W4.4 — D16 RAT 读到旧数据（stale_read）
- [x] CHAOSRenameMap 加 `stale_read`：在表项即将被下一次重命名写入覆盖的瞬间，让这次写入**静默失效一次**（表项保留旧映射直到再下一次写入才生效）——读到旧数据不换值不卡死。验证：定向注入后下游读到旧 phys 的证据（ctrace commit_diff 出 ④操作数强制切换 或 ⑤数据损坏）+ golden 回归。

### Task 5: W4.5 — D17/D18 空闲表重复分配（固定间隔 + 事件触发）
- [ ] CHAOSFreeList 现有 `mark_free`（把已分配项标回空闲=重复分配）语义核对 + `--freelist_mode` 加事件触发版（空闲表剩余 ≤8 时触发——numFreeRegs(RegClassType) 阈值判断，挂 SimpleFreeList::getReg 后）；D17=固定间隔 F1/F2、D18=事件触发。验证：注入日志（重复分配的 phys id + 阈值时刻）+ golden 回归 + 无注入回归。

**批次 2 执行约束**：Task 3→4→5 串行；每 Task 独立验证（三件套+注入证据）；构建一轮做完三 Task 后统一增量构建亦可但每 Task 注入验证须在其代码入二进制后跑；代理不 commit（编排者按 Task 分批提交）。

---

### Task 6: W4 收官批 — D14/D19/D20-22/D23-24（Int Rename 最后 7 单元，完成后 W4 全齐→暂停）
- [x] **D14**（swap_mispred_event）：同 swap_to_active 模型，但只在分支误预测恢复瞬间触发（挂 commit/bac squash 路径，复用批次 2 的 setEntry_restore 钩子时机 + 误预测事件判定）。〔执行注：触发判定=commitInfo.mispredictInst 非空（commit.cc:840 仅误预测路径置位，squashAll 置 NULL）——rename.cc checkSignalsAndUpdate 在 squash() 前后 notify/clear 上下文，maybeCorrupt 只在 sq_active&&sq_mispredict 窗口内布防；bm 定向证据：注入 Tick 77013475 与 cause=branch_mispred 信号（sn=415954）同 tick、mispred_squash_sn 精确对上，new_phys=43∈ROB 活跃池@dist13；结局 Crash（IQ 依赖图 43 双所有权，与 D13 同构）；8046 条 squash 信号日志证明事件判定区分 branch_mispred/other；同 seed LOGS_IDENTICAL〕
- [x] **D19**（drop_release）：某 phys 该被释放回空闲表时抑制这次释放（一次性触发持续影响；挂 UnifiedFreeList::addReg）。〔执行注：addReg 钩覆盖两条运行时释放路径（removeFromHistory 提交释放+freeingInProgress squash 后释放），init 路径安全（chaosFreeList 构造期为 nullptr）；证据=释放抑制行（idx 85, num_free_at_drop=3, "正常释放应为 4"）+ exit callback 终态对比：注入 run final_free_int=85 vs 零注入对照 86——**恰好 -1 永久缩水**；结局 Masked（程序结果不变——04 矩阵"前兆"口径：价值在空闲池缩水趋势而非 SDC）；同 seed LOGS_IDENTICAL〕
- [x] **D20/D21/D22**（freelist 头/尾指针）：gem5 SimpleFreeList=std::queue 无显式指针——按 spike B 近似：单bit=pop_wrong（返回非 front 索引）、双bit=front 索引 xor 2 位掩码、卡死=反复返回同项不 pop（或 addReg 侧 drop=只出不进）。诚实标注近似口径。〔执行注：D20 head_bitflip=弹出 front 索引 xor 1 随机位（62^bit3=54，target_status=allocated 即时重复分配，真 front 被消耗泄漏）；D21 head_bitflip2=xor 2 个不同随机位（62^(3,2)=50 汉明距恰 2）；D22 head_stuck=F5 预批准"反复返回同项不真正 pop"代理——SimpleFreeList::getReg 前置 maybeStuckHead 钩子（true=不 pop），布防=front idx 一位固定极性（62→54 bit3 stuck_at_zero），5 次曝光全部返回 54 且真 front 冻结 62（固定偏差 -8=04 矩阵"固定模式"观测），结局皆 Crash（依赖图 54/50/54 not empty）；日志均带"approx=...（近似口径）"标注；越界=诚实跳过不钳位；同 seed LOGS_IDENTICAL×3〕
- [x] **D23/D24**（重命名检查点=historyBuffer 表项翻转，单/双bit）：gem5 无 checkpoint 用 historyBuffer（机制核实 N1）——挂 rename.cc 的 historyBuffer 写入/消费路径，翻转 RenameHistory 的 newPhysReg/prevPhysReg 字段，窗口=建立→squash 消费。〔执行注：注入位点=renameDestRegs push_front 前（指令本体保留真实 dest——只翻转检查点副本，故障静默潜伏）；字段 new/prev 各 50/50；D23 证据：sn=415929 newPhysReg 81→89 bits=(3)，潜伏 1540 tick 后 **rename_doSquash 消费错误 phys 89**（freeingInProgress 释放错误寄存器→IQ 依赖图 89 panic）；D24：81→121 bits=(3,5) 汉明距 2，同样 doSquash 消费 121→Crash；消费观察器挂 doSquash+removeFromHistory 双路径（只读）；同 seed LOGS_IDENTICAL×2〕
- [x] 每模式验证三件套 + 注入日志证据 + golden 回归；runner/ooo_proxy 路由接全。〔执行注：增量构建 -j126 BUILD_EXIT=0 **零告警**（两次返工：RefCountingPtr 不接受 !=nullptr/=NULL，改 static_cast<bool>——gem5 惯用法）；无注入 golden 45737cc9a76c0dce 回归 EXIT=0；既有模式回归：mark_free/map_bitflip 日志字节格式不变（legacy 格式保留，D13 Site 标签未动）；runner sub_field 路由 e2e：D14（legal_domain_sub+swap_mispred_event）→Crash faults_injected=1、D19（delay_omission+drop_release）→Masked faults_injected=1（分类器五分类正常）；7 新模式路由全接（rat: swap_mispred_event/hb_bitflip/hb_bitflip2 + freelist: drop_release/head_bitflip/head_bitflip2/head_stuck），schema sub_field 为自由字符串无需改 schema〕
