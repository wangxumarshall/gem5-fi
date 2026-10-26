# R4-9-FSMC-C：C 组 15 格——模型钩子独立复核 + 落地（O04/O05/O06/O07/O09）

- 分支：`r4-9-fsmc-c`（本 worktree `.claude/worktrees/r4-9-fsmc-c`），base `d5fc8727`。
- 本报告是 **worktree 本地证据**（按任务书要求，不改 MDSPEC worktree 的共享文档）。
- 计划/工作清单：`docs/superpowers/plans/2026-10-22-lsu-mdspec-r4-9-fsmc-c.md`。
- **未做任何 scons 构建**（任务书禁）；全部 C++ 标 `compile-unverified, pending integration`。

## 0. 结论摘要

Agent 4（`r4-8-fs-multicore`）把这 15 格裁决为 `BLOCKED_MODEL_UNIMPL`，理由
"RMW data/operand 钩子缺 cache-side SwapResp hook；RMW ordering；barrier 完成跟踪；
order-tag swap"，并顺带在台账里写成"需要多核"。本轮的独立复核结论：

| 模型 | Agent 4 的诊断 | 本轮独立复核 | 依据 |
|---|---|---|---|
| O04 | 缺 RMW 数据面钩子 | **正确**（节点确存在、钩子确缺） | §2.1 |
| O09 | 缺 RMW operand 钩子 | **正确**（同上；但可钩面比规格窄，见 §4） | §2.2 |
| O05 | RMW ordering 需多核 | **半正确**：lost/dup 与多核无关且已落地；"提前 done"在本平台**无节点** | §2.3 / §4 |
| O06 | barrier 完成跟踪缺 | **正确**，且本轮给出了**精确落点**（Agent 4 只说到"未实现"） | §2.4 |
| O07 | order-tag swap 缺 | **正确**；落点是**诚实近似**（gem5 无显式 ordering queue） | §2.5 |

一句话：**"模型钩子不存在"这半边诊断成立**（5/5）；**"需要多核"这半边对 5 个模型都不成立**
（钩子全部落在单核 SE 可达的 cache/MemDepUnit 节点上）。本轮把 5 个模型的钩子全部落地并
端到端接线；**15 格仍保持 BLOCKED**，因为它们的负载身份（W7 = Atomic-Litmus）本身需要多核 FS
载体——这一条与本轮无关，由 R4-8 的平台结论处理。

## 1. 开工前的事实核查（全部源码级，file:line）

### 1.1 LSE 原子在 gem5 的落地路径（O04/O05/O09 的节点）

| 事实 | 证据 |
|---|---|
| LSE 原子（CAS/SWP/LDADD）由 ISA 生成 `TypedAtomicOpFunctor<T>` | `src/arch/arm/isa/insts/amo64.isa:201-215`（`AtomicSingleOp.emit`：`new AtomicGeneric3Op<T>(Mem<sfx>, valRs, lambda)`） |
| 函子成员即"操作数锁存器"：`a`=替换值/加数，`c`=比较值，`b`=内存 | `src/base/amo.hh:87-105`（`AtomicGeneric3Op`），`:97-100`（`execute(T*b){ op(b,a,c); }`） |
| RMW 的**唯一**执行点 = L1D 的 SwapReq 提交（old 转存返回包、new 写回块） | `src/mem/cache/base.cc:1380-1419`：`pkt->setData(blk_data)`（:1396，old→返回包）→ `(*(pkt->getAtomicOp()))(blk_data)`（:1399，new→内存） |
| 该点**已有**一个 LSU 钩子——只有计数器，没有改写 | `src/mem/cache/base.cc:1405` `chaosLsuF6Observe(ChaOSLsuEvent::CasSuccess)`，定义在 `src/cpu/o3/chaos_lsu_trigger.hh:132-157` |
| 结果锁存器（old value）就是返回包的数据缓冲 | `pkt->setData` 把 old 拷进 packet data（`src/mem/packet.hh` `setData`），`satisfyRequest` 完返回 |

⇒ **O04/O05/O09 的节点客观存在**（Cache 侧 RMW 数据面），只是没有改写钩子。**与多核无关**。

### 1.2 屏障在 gem5 的落地路径（O06/O07 的节点）

| 事实 | 证据 |
|---|---|
| ARM DMB/DSB 指令**本身没有任何内存访问** | `src/arch/arm/isa/insts/misc64.isa:229-233`（`Dmb64` = `ArmStaticInst` + 空 code）；`misc.isa:1216-1230`（DMB code 只有 CP15 trap 检查） |
| 因此平台不存在"屏障完成事件"这种独立信号 | 全仓 `grep -rn 'isFullMemBarrier' src/cpu/` 只命中 `static_inst.hh:176`（= `IsReadBarrier && IsWriteBarrier` 的 flag 判定）与 `commit.cc:1465`（只做计数 `stats.membars[tid]++`） |
| 屏障对访存的**真实**约束 = MemDepUnit 的屏障 SN 记账 | **插入** `src/cpu/o3/mem_dep_unit.cc:160-183`（`insertBarrierSN`）；**门** `src/cpu/o3/mem_dep_unit.hh:246-256`（`loadBarrierSNs/storeBarrierSNs` + `hasLoadBarrier/hasStoreBarrier`）；**释放** `src/cpu/o3/mem_dep_unit.cc:430-457`（`completeInst` 擦除） |
| `insertBarrierSN` 的调用者 | `mem_dep_unit.cc:285`（`insertNonSpec`）与 `:343`（`insertBarrier` ← `iew.cc:1047-1050`） |
| LSQ 侧**没有**屏障/fence 结构 | `grep -n 'barrier\|fence' src/cpu/o3/lsq*.{hh,cc}` → 空 |

⇒ **O06/O07 的节点客观存在**（MemDepUnit 的屏障 SN 记账），且**是单核 SE 可达的**。
ords tag = `InstSeqNum`，valid/ready = `hasLoadBarrier()/hasStoreBarrier()`。**与多核无关**。

## 2. 逐模型：规格 → 节点 → 钩子是否存在（复核）

规格行取自 `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md`（43 列表）。

### 2.1 O04（"LSE 原子读改写的数据选择与返回 MUX"）
- 规格故障：交换 old/new 值、CAS 比较值与替换值，或返回上一条 old value。
- 节点：同 §1.1（`base.cc:1396/1399` 两个锁存器）。
- 钩子存在？**否** ⇒ Agent 4 诊断**正确**。
- 落地子模型：**O04-a（old/new 交换）** 已实现。O04-c（CAS compare/replacement 交换）、
  O04-d（返回上一条 old value）未落地——理由见 §4（操作数在函子内部，不可寻址）。

### 2.2 O09（"compare/replacement/addend/old-value/result 数据锁存器"）
- 节点：同上；可寻址面 = 返回包（result/old-value）+ 块内 new 值。
- 钩子存在？**否** ⇒ 诊断**正确**。
- 落地子模型：**O09-a（result/old-value 锁存器 1 bit 翻转）** 已实现；
  compare/replacement/addend 三个操作数锁存器未落地（§4）。

### 2.3 O05（"原子 RMW 事务 request/done 通路及线性化事件"）
- 节点：`base.cc:1376-1419` 的同步提交（classic 无排队、无 done 事件）。
- 钩子存在？**否**（只有 F6 计数）⇒ 诊断"缺钩子"**正确**；"需多核"**不正确**。
- 落地子模型：**O05-a（lost，丢写）**、**O05-b（dup，施加两次）** 已实现
  （数据载荷保持正确，符合规格的归因要求）。"提前 done 允许后续 load 越过"**不可达**（§4）。

### 2.4 O06（"DMB/DSB 屏障的完成状态与前后内存事务排空条件"）
- 节点：MemDepUnit 屏障 SN 的插入/释放两端（§1.2）。
- 钩子存在？**否**（`grep chaos...MemDepUnit::insertBarrierSN` 无任何钩子）⇒ 诊断**正确**。
- 落地子模型：**O06-a（early，提前 done）** 与 **O06-b（stuck，丢失/卡死 done）** 均已实现。

### 2.5 O07（"LSU 内部 ordering queue 的 order tag、valid/ready 和选择逻辑"）
- 节点：**gem5 O3 没有显式 ordering queue**；最接近的结构 = MemDepUnit 屏障 SN 集
  （SN = order tag，`hasLoadBarrier/hasStoreBarrier` = valid/ready 判定）。
- 钩子存在？**否** ⇒ 诊断**正确**。
- 落地子模型：`--lsqfwd_o07`（**诚实近似**：释放另一个活 SN 代替本 SN）。此近似在
  §2.5 的注释与本报告里都显式标注，绝不当成周期精确的 ordering-queue 模型。

## 3. 实现（沿用仓库既有形制，不新造机制）

### 3.1 O04/O05/O09 —— `CHAOSCache` 三个新 targetField 模式
- 钩子 `CHAOSCache::maybeCorruptRmw(BaseCache*, PacketPtr, uint8_t *blk_data)`
  （`CHAOSCache.hh` 声明 / `CHAOSCache.cc` 实现），由新的静态注册
  `BaseCache::chaosRmwHook` + out-of-line 转发 `BaseCache::chaosRmwCommit`
  （`base.hh` / `base.cc`）在同一 SwapReq 提交点调用。
- 入口守卫 `pkt->isAtomicOp()`（LSE 路径；非 LLSC 的 `cmpAndSwap`），
  与规格触发条件 "CAS/SWP/LDADD" 字面对齐。
- 三条规则：`swap_oldnew`（O04-a）/`result_old`（O09-a）/`lost`|`dup`（O05-a/b），
  由 `--l1d_rmw_rule` 选择；**模式/规则不匹配响亮 panic**（半指定模型绝不静默运行）。
- 触发器沿用 `chaos_lsu_trigger.hh`（事件归一化；F6 = 首个合格 RMW 提交，即 base.cc
  已计数的同一个 `CasSuccess` 事件）；legacy 周期块攻击在这些模式下**关闭**。
- 观测量：`CHAOS_RMW` teardown 行 + prop 流新 kind `rmw_data`(L1)/`rmw_result`(L1)/
  `rmw_order`(L2)。

### 3.2 O06/O07 —— `CHAOSLSQFwd` 两个新模式 + MemDepUnit 钩子
- 新增 header-only 注册表 `CHAOS/gem5/src/cpu/o3/chaos_barrier_hook.hh`
  （`chaosBarrierInsertHook` / `chaosBarrierReleaseHook`，全 `nullptr` 默认 = 零回归）。
  **为什么用注册表而不是指针**：MemDepUnit 不持有 CPU/注入器指针
  （`mem_dep_unit.hh` 只有 `InstructionQueue *iqPtr`；`init()` 的 `CPU *cpu` 仅用于
  `addStatGroup`，`mem_dep_unit.cc:150-170`）——这正是 S10 的既有先例
  （`store_set.cc:34-36` 注释原文："StoreSet has no CPU or injector pointer — the
  S10-armed CHAOSLSQFwd self-registers them"）。
- `mem_dep_unit.cc` 两处调用点：`insertBarrierSN` 顶部（返 true ⇒ 不记账 = O06-a）；
  `completeInst` 的屏障记账段（返 1 ⇒ 跳过擦除 = O06-b；返 2 ⇒ 擦除 substitute = O07）。
  **钩子为 null 时原路径（含 `assert(hasStoreBarrier())`）逐字节不变**。
- `CHAOSLSQFwd`：`--lsqfwd_o06 [--lsqfwd_o06_done early|stuck]` / `--lsqfwd_o07`；
  hook-split 关闭 SQ-forward 数据面（L03/L04/S10 同款）；内建 SN 台账保证 O07 的替换值
  **永远是另一个合法活 SN**（无候选则诚实跳过 = attempted 而非 eligible）。
- 观测量：`CHAOS_BARRIER` teardown 行（含 `live_sns_at_exit`，>0 即 O06-b 的可观测停顿）
  + prop 流新 kind `barrier_done`(L2)/`order_tag`(L2)。

### 3.3 端到端接线（缺失即响亮拒斥）
| 环节 | 落地 |
|---|---|
| 配置面 | `configs/se/lsu_proxy.py`：`--l1d_target_field` 增 `rmw_mux/rmw_latch/rmw_order` + `--l1d_rmw_rule`；`--lsqfwd_o06/--lsqfwd_o06_done/--lsqfwd_o07`；两者都传进 SimObject |
| 路由 | `tools/lsu_campaign.py`：`MODEL_FLAGS[O04/O05/O09]` → cache family；`[O06/O07]` → lsqfwd family |
| F0 门 | `_cache_tier_flags`/`_lsqfwd_tier_flags` 已覆盖五个模型：F0 需按 **(model, workload)** 实测流长，未实测 → `None` → 响亮 `BLOCKED(F0-span-unmeasured)`，并在注释里给出**普查命令**（RMW 流 = 挂载 L1D 的原子 RMW 提交；屏障流 = 屏障 SN 记账） |
| 台账 | `MODEL_BLOCKED` 五项**保留**，理由串改写成精确表述；O05/O06/O07 **故意保留 `multicore-fs:` 前缀**（既真实，又是 `lsu_blocked_triage.py` 的 `r"multicore"` 互斥分桶的载体——去掉会静默改桶） |
| 观测字段 | `tools/lsu_prop_fields.py`：5 个新 kind + `REQUIRED_FIELDS` |
| 契约测试 | `tests/test_lsu_hook_o0x.py`（45 断言） |

## 4. 真实不可达（用代码路径证明，不是"我的负载没触发"）

1. **O05 的"提前 done 允许后续 load 越过"**：classic 内存系统的原子 RMW 在
   `BaseCache::satisfyRequest` 内**同步**完成（`base.cc:1376-1419`，无排队、无 done 事件）；
   LSQ 侧原子请求一次性下发（`lsq.cc:774-884`）。**不存在可被提前的 done 信号** ⇒ 无节点可注入。
   该子模型记为"平台不可达"，不是"载体不合适"。
2. **O04-c/d 与 O09 的 compare/replacement/addend 锁存器**：这些操作数是 ISA 生成的
   `AtomicGeneric3Op<T>` 的**不透明成员**（`amo64.isa:201-215` 的 lambda 捕获 +
   `amo.hh:87-105` 的 `a`/`c` 私有成员），CPU 侧**没有独立可寻址的锁存器**可翻转。
   本平台能钩的只有 result/old-value 面（返回包）与 new 面（块内）。
   该缺口记为 **landed-subset**（已落地子集），不是"载体问题"。
3. **O06 的"延后 done"**：已由 O06-b（stuck）覆盖（SN 永不擦除 = 永不完成）；
   但"延后 N 周期"没有可延后的定时器（同 §4.1 的理由）——记为子模型缺口，落成 stuck 近似。

## 5. 载体（载体 ≠ 模型，逐条判过）

| 载体 | 服务模型 | 构建 | golden（两次运行一致） | sha256 |
|---|---|---|---|---|
| `workloads/directed/lse_rmw` | O04/O05/O09 | `gcc -O2 -static -Wall -Wextra -march=armv8-a+lse` | `e2d502897d3e9d1c` | `05d1bd12120624bb…d392c284` |
| `workloads/directed/barrier_probe` | O06/O07 | `gcc -O2 -static -Wall -Wextra` | `04cc99e6f78e39c4` | `1e40ab5d167a564c…701fe8fc` |

- **必须新建 LSE 载体**：既有 `atomics_probe.c` 走 **LDXR/STXR**（LLSC `cmpAndSwap` 路径），
  **到不了** O04/O05/O09 的 `pkt->isAtomicOp()` 钩子——复用它会"跑通但什么都没证明"。
- `lse_rmw` 的 oracle 两面对称：acc 同时折入 (a) 每次 RMW 的返回值（O04-a/O09-a 污染面）
  与 (b) RMW 后内存值（O05-a/b 污染面）。
- `barrier_probe` 的**诚实边界**写在文件头：单核 SE 无真实乱序，O06-a 的"越过屏障"在进程内
  **无法**表现为 litmus 违约；本载体的作用是产出稠密确定的 DMB/DSB 流（否则普查
  attempted=0）+ 未注入对照臂的稳定 golden。**分类（SDC/Timeout/Masked）是 campaign 的事。**
- 实测证据：`gcc -S | grep -cE '\b(dmb|dsb)\b'` = **4**（屏障指令确实在流里，未被优化掉）。

## 6. 逐行裁决（15 格，机读口径不变）

| 组 | RunID | 本轮后的精确阻塞（仍是 BLOCKED） |
|---|---|---|
| A | O04-F0/F2/F6-W7（3） | 负载身份（W7 = Atomic-Litmus 需多核 FS 载体）+ 钩子 compile-unverified/un-piloted。F0 还额外需 RMW 流普查 |
| B | O05-F0/F4/F6-W7（3） | 同上（lost/dup 钩子已落地；"提前 done"子模型平台不可达，已记 §4.1） |
| C | O06-F0/F4/F6-W7（3） | 同上（early/stuck 钩子已落地） |
| D | O07-F0/F2/F6-W7（3） | 同上（order-tag 为诚实近似，已显式标注） |
| E | O09-F0/F1/F2-W7（3） | 同上（result/old-value 面已落地；操作数锁子模 land-subset，已记 §4.2） |

**triage 守恒实测**：`python3 tools/lsu_runid_map.py … && python3 tools/lsu_blocked_triage.py …`
→ `[triage] BLOCKED=86 RULING=12 LICENSE=12 FS-MULTICORE=35 FS-INFRA=24 MODE-UNIMPL=3 HOOK-UNIMPL=0 OK=0`
（**FS-MULTICORE=35 不变**；五个模型未被静默解锁。）

## 7. 给集成方的操作清单（解除条件逐条）

1. **构建**：本分支的 C++ 全部 `compile-unverified`。集成方需在主干 worktree 上
   `scons -j16 build/ARM/gem5.opt`，确认零新告警（新增文件：`chaos_barrier_hook.hh`，
   header-only，无需改 SConscript；改动的文件：`base.{hh,cc}`、`CHAOSCache.{hh,cc,py}`、
   `mem_dep_unit.cc`、`CHAOSLSQFwd.{hh,cc,py}`）。
2. **RMW 流普查**（F0 格前置；命令已写进 `_cache_tier_flags` 注释）：
   ```
   build/ARM/gem5.opt --outdir=runs/lsu/r4_9_span/<wl> configs/se/lsu_proxy.py \
     --cmd workloads/directed/lse_rmw --cpu O3 --chaos_l1d \
     --l1d_target_field rmw_mux --l1d_rmw_rule swap_oldnew \
     --l1d_lsu_tier F0 --l1d_warmup_events 1 --l1d_span_events 1000000 \
     --l1d_max_faults 1 --l1d_rng_seed 1 --chaos_propagation \
     --prop_run_id O04-SPAN-lse_rmw --prop_sample_run_id s1
   ```
   teardown 的 `CHAOS_LSU_TRIGGER eligible=` 即流长；把 `("O04","lse_rmw"): <n>` 填进
   `CACHE_F0_SPAN`。（O05/O09 同形，改 `--l1d_target_field/--l1d_rmw_rule`。）
   屏障流同理（`--lsqfwd_o06 --lsqfwd_o06_done early --lsqfwd_lsu_tier F0 …`，
   载体重放 `barrier_probe`），填 `LSQFWD_F0_SPAN`。
3. **载体重放协议**：本轮的 15 格负载身份是 W7 = Atomic-Litmus（多核 FS），**不得**用
   `lse_rmw`/`barrier_probe` 静默替代格子（那会静默改格子定义）。正确用法是
   T 系先例：把"载荷替代"写进 backfill note，作为**注入器功能验证载体**（不是格子的
   多核语义），并同时保留 multi-core FS 那条裁决。
4. **pilot**：至少一条 RMW 路径与一条屏障路径跑通（injection log 非空 + 链边记录），
   然后按 C11/C12/L04 的铁律**同一提交内**把 `MODEL_BLOCKED` 五项删除。
5. **测试**：`python3 tests/test_lsu_hook_o0x.py`（45/45 PASS）在集成后必须仍然全绿；
   它会在任何一处静默解锁时立刻失败。

## 8. 本轮真实执行的命令与结果（逐条可复现）

```
$ gcc -O2 -static -Wall -Wextra -march=armv8-a+lse -o workloads/directed/lse_rmw workloads/directed/lse_rmw.c   # 零告警
$ ./workloads/directed/lse_rmw ; ./workloads/directed/lse_rmw            # e2d502897d3e9d1c / e2d502897d3e9d1c
$ gcc -O2 -static -Wall -Wextra -o workloads/directed/barrier_probe workloads/directed/barrier_probe.c         # 零告警
$ ./workloads/directed/barrier_probe ; ./workloads/directed/barrier_probe # 04cc99e6f78e39c4 / 04cc99e6f78e39c4
$ gcc -O2 -static -S -o - workloads/directed/barrier_probe.c | grep -cE '\b(dmb|dsb)\b'   # 4
$ python3 tests/test_lsu_hook_o0x.py                                      # ALL PASS（60 行 PASS，0 FAIL）
$ python3 tests/test_lsu_prop_fields.py                                   # ALL PASS
$ python3 -m pytest tests/ -q --ignore=tests/test_claim_concurrency.py    # 16 passed
$ python3 -m pytest tests/ -q                                             # 16 passed, 5 errors（claim_concurrency 既有 fixture 问题，与本改动无关）
$ python3 tools/lsu_runid_map.py --xlsx … --out /tmp/…json && python3 tools/lsu_blocked_triage.py --map … --out …
  # [runid_map] 325 RunID; status={'PARTIAL': 239, 'BLOCKED': 86}
  # [triage] BLOCKED=86 RULING=12 LICENSE=12 FS-MULTICORE=35 FS-INFRA=24 MODE-UNIMPL=3 HOOK-UNIMPL=0 OK=0
```

未执行（本 worktree 禁止/超出预算，**不宣称**）：gem5 构建、任何 gem5 运行、FS 多核 pilot。
