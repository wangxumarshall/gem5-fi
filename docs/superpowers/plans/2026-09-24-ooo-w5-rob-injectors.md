# OoO W5 Int Dispatch/ROB 注入器 Implementation Plan

> Spec：docs/gem5-fi/ooo/04-design-matrix.md D25-D55 行 + 06-implementation-plan.md §4 W5。机制事实见 .planning/2026-09-22-ooo-fault-injection-implementation-plan/findings.md（spike A：commit 门控=CanCommit@commit.cc:1353、现有 CHAOSROB hook rob.cc:254 在提交后太晚且 Field 枚举只是日志字符串——PC/标识符翻转需真实现；done 提前置位须 setExecuted 规避 commit.cc:1119 assert；结果值在 physRegFile 有旧占用者残留值）。
> 先例：W4 三批（4b6bf482/23ba7bc3/f358e1d6 的 CHAOSRenameMap/CHAOSFreeList——注入位点/日志格式/flat 索引发现/写路径 mask 先例全在）。

### Task 1: W5.1 — D25/D26/D28/D29 ROB PC/标识符 单/双比特（M2 门第一关前置）
- [ ] CHAOSROB 真实现 4 模式：pc_bitflip/pc_bitflip2/destid_bitflip/destid_bitflip2——在 ROB 项写入时（rob insert 或指定距离项）对 head_inst 的 PC 字段（pcState）或目的寄存器标识符（renamedDestIdx 的 phys 索引）翻 1/2 个随机位。注入位点自选（getEntryAtDistance 指定项的 inst 字段级），日志行含 true/new 值与汉明距证明。验证：注入日志+汉明距恰 1/2+同 seed 复现+golden 回归+`--chaos_ctrace` L2 证据一张。
### Task 2: W5.2-W5.3 — D27/D31 ROB PC/标识符卡死 + D30 标识符换值
- [ ] pc_stuck/destid_stuck（写路径 mask）+ destid_swap_active（挑 ROB 内另一活跃 dest phys——复用 W4.2 的 collectRobActiveDests 思路）。
### Task 3: W5.4-W5.5 — D32-D35 done 位提前/延迟置位
- [x] done_early/done_early_event(ROB>80%)/done_delay/done_delay_event——挂 commit.cc:1353 markCompletedInsts（setCanCommit 位点）；提前置位须同 setExecuted（规避 assert）；延迟=条件跳过 setCanCommit（fromIEW 只含当拍项→跳过=永不置位）；事件版用 ROB 占用>80% 判定（countInsts/容量）。（W5 批次 2 已验证：done_early 须另加 isInIQ||isIssued 守卫规避 iew.cc:1064 IQ-dispatch assert；定向+同seed 复现+golden 回归+ctrace L2 ①执行时间错 全过）
### Task 4: W5.6-W5.7 — D36-D39 old-phys（RenameHistory::prevPhysReg 翻转/换值/卡死；squash 事件触发）+ D40 ROB 槽位 stale_read
- [x] （W5 批次 2 已验证：4 oldphys 模式挂 rename.cc push_front 现有钩（maybeCorruptHistory 扩展，无 rename.cc 改动），doSquash 消费错值逐模式日志证明；D39 stuck=共享字段胞解释+F5 永久 mask+多次消费日志；D40 stale_read=retire 环+记录字段回写，STALE_RECORD_COMMITTED 证明 commit 读旧记录）
### Task 5: W5.8-W5.9 — D41-D46 ROB 头/尾指针（单/双/卡死，rob 头尾索引近似口径+approx 标注）
### Task 6: W5.10-W5.11 — D47-D49 IQ ready 提前/永不置位（+IQ>80% 事件）+ D50-D54 IQ tag 族（换值/单/双/卡死/读到旧数据——inst_queue entry 字段）
### Task 7: W5.12 — D55 分发端口路由（探索性——inst_queue.cc:920 getUnit 换 op_class；spike C 结论=仅时序效应，诚实近似口径或 blocker）

**通用**：每 Task 三件套验证+注入日志证据+同 seed 复现+golden 45737cc9a76c0dce 回归；ooo_proxy --rob_mode choices + runner sub_field 路由；代理不 commit。
