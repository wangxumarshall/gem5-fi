# R4-9-FSMC-C：C 组 15 格（O04/O05/O06/O07/O09）模型钩子落地

- 日期：2026-10-22
- 分支：`r4-9-fsmc-c`（worktree `.claude/worktrees/r4-9-fsmc-c`，base `d5fc8727`）
- 任务书：15 个 FS-MULTICORE C 组 RunID（O04-F0/F2/F6-W7、O05-F0/F4/F6-W7、
  O06-F0/F4/F6-W7、O07-F0/F2/F6-W7、O09-F0/F1/F2-W7）。
- 原始裁决（Agent 4，`r4-8-fs-multicore` §表 C）：`BLOCKED_MODEL_UNIMPL`，
  理由串 "RMW data/operand 钩子缺 cache-side SwapResp/operand hook；RMW ordering；
  barrier 完成跟踪；order-tag swap"。**本计划独立复核该裁决**（源码级，file:line），
  然后把真的不存在的钩子补上并端到端接线。

## 0. 复核结论（本计划的事实基础）

| 模型 | 规格单元（07 表） | 规格节点 | 平台里该节点 | 钩子存在？ |
|---|---|---|---|---|
| O04 | LSE 原子读改写的数据选择与返回 MUX（CAS/SWP/LDADD 的 old/new/compare/replacement 选择） | RMW 数据 MUX + 返回口 | `BaseCache::satisfyRequest` SwapReq 分支（`src/mem/cache/base.cc:1376-1401`）：`pkt->setData(blk_data)`（old→返回包）+ `(*pkt->getAtomicOp())(blk_data)`（new→内存） | **否**（只有 F6 计数 `chaosLsuF6Observe(CasSuccess)`，无数据改写钩子）⇒ Agent 4 诊断**正确** |
| O09 | LSE 原子 RMW 的 compare/replacement/addend/old-value/result 数据锁存器 | 操作数/结果锁存器 | 同上 + `src/base/amo.hh:87-105` `AtomicGeneric3Op`（a=replacement，c=compare，b=内存） | **否** ⇒ Agent 4 诊断**正确**（"RMW operand hook"） |
| O05 | 原子 RMW 事务 request/done 通路与线性化（丢失/重复/提前 done） | RMW 完成握手 | 同 SwapReq 提交点；"done" 无独立事件（classic 同步完成） | **否**；且"提前 done 允许后续 load 越过"在本平台**无节点**（见 §4） ⇒ 诊断**部分正确**（丢失/重复可实现；提前 done 不可达） |
| O06 | DMB/DSB 屏障完成状态与前后事务排空 | 屏障完成点 | ARM DMB/DSB 本身**无内存访问**（`misc64.isa:229-233` Dmb64 空 code；`misc.isa:1216-1230`）；唯一实现是 `MemDepUnit` 的屏障 SN 集合（`mem_dep_unit.cc:160-183` 插入、`:430-457` `completeInst` 擦除） | **否**；但 `MemDepUnit` 屏障 SN 释放点**是**可钩的屏障完成门 ⇒ 诊断**正确**，且给出了精确落点 |
| O07 | LSU 内部 ordering queue 的 order tag / valid-ready / 选择逻辑 | ordring 队列条目 | gem5 O3 无独立 "ordering queue"；最接近的结构 = `MemDepUnit::loadBarrierSNs/storeBarrierSNs`（`InstSeqNum` = order tag；`hasLoadBarrier/hasStoreBarrier` = valid/ready 判定，`mem_dep_unit.hh:246-256`） | **否** ⇒ 诊断**正确**；落点为近似（诚实标注 approx） |

## 1. 补的钩子与落点

- **O04 / O05 / O09 → `CHAOSCache` 新 targetField 模式**，落点
  `BaseCache::satisfyRequest` 的 SwapReq 分支（`base.cc:1376`，同一函数内已有
  F6 `CasSuccess` 钩子 = 既有 LSU 项目插入点，C11/C12/C14/C15 同法）。
  - `rmw_mux`（O04）：old/new 交换（O04-a）。
  - `rmw_latch`（O09）：result/old-value 锁存器 1 bit 翻转（O09-a）。
  - `rmw_order`（O05）：`lsuRmwOrder=lost`（内存更新丢弃）/`dup`（原子 op 施加两次）。
- **O06 / O07 → `CHAOSLSQFwd` 新钩子**，落点 `MemDepUnit::insertBarrierSN` /
  `completeInst`（`mem_dep_unit.cc`），经 `cpu->lsqFwd` 到达（o3::CPU 已持有）。
  - `--lsqfwd_o06`：`early`（屏障 SN 提前擦除 = 后续访存越过）/`stuck`（SN 永不擦除）。
  - `--lsqfwd_o07`：`swap`（两个在飞屏障 SN 互换 = order tag 换值；近似）。

## 2. 逐项任务（每项 = 一个 commit）

- [x] **T1** O04/O05/O09 RMW 钩子 + 端到端接线（CHAOSCache.hh/.cc/.py、base.hh/.cc、
      lsu_proxy.py、lsu_campaign.py MODEL_FLAGS/MODEL_BLOCKED、lsu_prop_fields.py）。
- [x] **T2** O06/O07 屏障/order 钩子 + 端到端接线（CHAOSLSQFwd.hh/.cc/.py、mem_dep_unit.cc、
      lsu_proxy.py、lsu_campaign.py、lsu_prop_fields.py）。
- [x] **T3** 定向 SE 载体（RMW/屏障，自 oracle）+ 契约测试 `tests/test_lsu_hook_o0x.py`。
- [x] **T4** 台账订正 + 裁决报告 `docs/gem5-fi/lsu/mdspec/R4-9-FSMC-C-report.md`。

## 3. 测试命令（真实、可跑）

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r4-9-fsmc-c
python3 tests/test_lsu_hook_o04.py     # 退出码 0 = 全 PASS
python3 tests/test_lsu_hook_o0x.py
python3 tools/lsu_runid_map.py ... && python3 tools/lsu_blocked_triage.py   # FS-MULTICORE=35 守恒
python3 -m pytest tests/ -q            # 全量不回归
```

## 4. 真实不可达（须在报告里用代码路径证明）

- O05 "提前 done 允许后续 load 越过"：classic 内存系统的原子 RMW 在
  `satisfyRequest` 内**同步**完成（`base.cc:1376-1401` 无排队/无 done 事件），
  `LSQUnit` 侧原子请求一次性下发（`lsq.cc:774-884`），**不存在可被提前的 done 信号**。
- O04-c/d（CAS compare/replacement 交换、返回上一条 old value）、O09 的
  compare/replacement/addend 操作数锁存器：操作数是 ISA 生成的
  `AtomicGeneric3Op<T>(a=Mem<sfx>, c=valRs, lambda)` 的**不透明内部成员**
  （`amo64.isa:201-215`、`amo.hh:87-105`），CPU 侧无独立锁存器可寻址 ⇒ 只有
  result/old-value 面（返回包）与 new 面（内存）可钩。
- 所有 15 格仍是 W7（Atomic-Litmus）⇒ 即便钩子落地，**格子仍因负载身份
  被 WL_BLOCKED 拦**；本轮的诚实交付是"模型语义阻塞被消除 + 载体就绪"，
  不是"格子解锁"。

## 5. 诚实标记

- 全部 C++ 标 `compile-unverified, pending integration`（本 worktree 禁 scons）。
- 未跑够的 census/pilot 一律拒绝（loud refusal），不填假数。
