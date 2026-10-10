# MemoryOrderViolation 独立事件源设计（[LSU][SEM-F6]）
# ITEM-289 / L03-F6-W5 capability-gap 的解决方案设计稿

- 设计者：Subagent E（MemoryOrderViolation 事件源设计，只读设计任务）
- 日期：2026-10-10
- 裁决依据：D-2026-10-10-ITEM289（docs/gem5-fi/lsu/task_plan.md:156，用户裁决原文）
- 审计依据：F-047 三源审计（docs/gem5-fi/lsu/findings.md:63）
- 清单依据：ITEM-289（docs/gem5-fi/lsu/完整任务执行清单.md:11142）、L03 模型行（同文件:160）
- 状态：设计稿（零代码变更；本文件是唯一产物，未触碰仓库任何文件、未运行 gem5、未做 git 写操作）

---

## 0. 摘要（一句话）

以 gem5 O3 LSQ **真实的 store-path load-store violation 检测**（`LSQUnit::checkViolations`，lsq_unit.cc:535-621）为事件源，新增第 5 种 F6 事件类型 `MemoryOrderViolation`（独立枚举值、独立计数、独立日志 Site），消费者为补注册的 CHAOSLSQFwd（f6Thunk 模式，照抄 CHAOSAddrPath.cc:74-82），故障写入点 = checkViolations 内**比较地址视图的单 bit 翻转**（L03-a violation 漏报，有效位约束保证比较结果反演）。**关键实证：W5 载体（sq_forward）golden 三副本均测得 4 个真实 violation 事件（runs/lsu/golden/sq_forward/g{1,2,3}/stats.txt:1595/1608），"单线程 SE 下 violation 频率为 0"这一最大科学风险被本轨道自己的 golden 数据直接否定**；F6（首事件注入一次）在 W5 上确定性可触发。

---

## 1. 事件定义（基于 gem5 真实实现）

### 1.1 事件 = O3 LSQ store-path 内存序违规检测

**定义**：在 gem5 O3 CPU 的 LSQ 中，当一个 store（含 atomic，iew.cc:1197-1199 与 1228-1229 都走 `executeStore`）执行完成并计算出场效地址后，`LSQUnit::executeStore`（lsq_unit.cc:699-758，第 756 行）调用 `checkViolations(loadIt, store_inst)` 从该 store 的 LQ 位置向"更年轻"的方向扫描已执行 load；若某个**更年轻且已执行**的 load 的字节区间与该 store 的字节区间重叠（lsq_unit.cc:569 `inst_eff_addr2 >= ld_eff_addr1 && inst_eff_addr1 <= ld_eff_addr2`），则判定发生**内存序违规**：该 load 在老 store 地址解析之前投机执行并读走了陈旧数据。

gem5 自身的处置（事件被消费的路径）：
1. 检测点：`memDepViolator = ld_inst`（lsq_unit.cc:607）、`++stats.memOrderViolation`（lsq_unit.cc:609）、返回 `M5PanicFault`（lsq_unit.cc:611-614；该返回值在 iew.cc 只用于把 store 推进提交队列（iew.cc:1242-1251），**从不写入 `inst->fault`**，因此不会在 commit 触发 panic——commit 读的是 `head_inst->getFault()`（commit.cc:1170），由 `initiateAcc` 设置）。
2. 消费点：IEW::executeInsts 每条指令处理完后检查 `ldstQueue.violation(tid)`（iew.cc:1318；LSQ::violation → lsq.cc:331-343 → lsq_unit.hh:293 `static_cast<bool>(memDepViolator)`），取出 violator（iew.cc:1324，getMemDepViolator 会清除信号），`squashDueToMemOrder(violator, tid)`（iew.cc:1337，squash violator 及更年轻指令并重取指）+ `instQueue.violation`（iew.cc:1334）+ `++iewStats.memOrderViolationEvents`（iew.cc:1339；已在 squashing 时的分支 iew.cc:1356 同样计数）。

即：**事件 = checkViolations store-path 分支发现重叠对**；gem5 用两个独立内建 stat 计数同一事件（`lsq0.memOrderViolation` 检测侧、`iew.memOrderViolationEvents` 消费侧）。本设计的事件计数与这两个 stat 严格对齐（见 §2 与 §5.4 的交叉验证）。

### 1.2 为什么它是"内存序违规"的忠实代表（而非近似）

1. **名字与语义同源**：这是 gem5 官方命名为 "memory ordering violations" 的微架构事件（lsq_unit.cc:273 stat 描述、iew.cc:176-177 stat 名），不是我们为凑数找的代理。对照：lsq.cc:453 的 "CasSuccess" notify 实际挂在**每个 dcache 响应到达**处（lsq.cc:449-453 注释自认 proxy）——那类 looseness 正是本设计要避免的。
2. **与 L03 清单触发条件逐字对应**：ITEM-289 触发条件 = "年轻load先执行且更老store地址在后续周期解析"（完整任务执行清单.md:11167 附近）——checkViolations store-path 的进入前提恰是"年轻 load 已执行（effAddrValid，lsq_unit.cc:549）且更老 store 地址刚解析（executeStore 刚算出 effAddr）"。实施步骤 "当年轻 load 已执行而更老 store 地址稍后解析时，制造 false negative violation"（同文件）描述的就是在这个检测点上动手。
3. **与 SqForward 是两个不同事件**：SqForward（lsq_unit.cc:1557）= load 命中 SQ 中**更老 store 的数据转发**（正常快路径）；MemoryOrderViolation = **本应转发/本应等待的依赖关系被投机破坏后的兜底检测**（异常路径，触发 squash/replay）。二者可以先后发生在同一对 store/load 上，但微架构含义、代码位置、后果（一个给数据、一个触发重放）完全不同——这正是 D-2026-10-10-ITEM289 禁止近似映射的根据，本设计完全不经过 SqForward 事件或其统计。

### 1.3 范围界定（诚实声明）

- **SE 单线程只实现 store-path**。checkViolations 的 load-path 分支（`inst->isLoad()`，lsq_unit.cc:570-596）在 `LSQCheckLoads=true`（B0 配置，lsu_proxy.py:583，config.ini 实证 `LSQCheckLoads=true`）下也会运行，但其 violation 判定依赖 `hitExternalSnoop`（lsq_unit.cc:574）——SE 单核无外部 snoop，该分支只置 `possibleLoadViolation` 标记，**不产生 violation 事件**。事件源对 load-path 对不计数、不通知（调用点以 `!inst->isLoad()` 短路）。
- **TSO/snoop 变体（checkSnoop → ReExec，lsq_unit.cc:500-531）为 FS/多核专属**，本事件源不覆盖，留作 FS 扩展（钩子签名预留 `is_load` 参数）。
- **单消费者单核 SE 范围**：与 chaos_lsu_trigger.hh:27-30 的既有诚实声明一致（337 格网格每 run 挂一个注入器）。

### 1.4 出现频率量级（实证，非推测）

**LSU 轨道自己的 golden（B0 平台、lsu_proxy.py、SE）——同一平台同一载体的直接证据**：

| 载体 | iew.memOrderViolationEvents | lsq0.memOrderViolation | 来源 |
|---|---|---|---|
| **sq_forward（W5，ITEM-289 载体）** | **4**（g1/g2/g3 三副本全同） | **4** | runs/lsu/golden/sq_forward/g{1,2,3}/stats.txt:1595/1608 |
| stream_chase | 5 | — | runs/lsu/golden/stream_chase/g*/stats.txt:1606 |
| agu_addrmodes | 4 | — | runs/lsu/golden/agu_addrmodes/g*/stats.txt:1604 |
| beebs_kernels | 5 | — | runs/lsu/golden/beebs_kernels/g*/stats.txt:1608 |
| sqlite_like（W12） | 4 | — | runs/lsu/golden/sqlite_like/g*/stats.txt:1603 |
| prefetch_stride | 4 | — | runs/lsu/golden/prefetch_stride/g*/stats.txt:1605 |
| gap_bfs | 5 | — | runs/lsu/golden/gap_bfs/g*/stats.txt:1607 |
| mini_check | 4 | — | runs/lsu/golden/mini_check/g*/stats.txt:1600 |
| cache_dirtyevict | 4 | — | runs/lsu/golden/cache_dirtyevict/g*/stats.txt:1604 |

结论：**LSU 轨道 9 个 SE 载体全部非零（4-5 个/run），且跨 g1/g2/g3 完全确定**。"若 B0 平台负载全部零 violation" 的担忧被直接否定。F6 只需 ≥1 个事件 → 在所有现有 SE 载体上确定性可触发。

跨轨道旁证（**OoO 轨道 artifacts，只作为微架构事件频率的旁证，绝不与 LSU 轨道混数**——CLAUDE.md 双轨道纪律）：artifacts/ooo_w8_density/*/stats.txt 的 `iew.memOrderViolationEvents`：crc32=8、wikisort=17、minver=18、md5sum=9、coremark=29、gemm=8、lu=13、cholesky=12、jacobi2d=7、gap=7、jpeg_wl=30、dep_chain=3、branch_mispred=12、**rob_fill=1723**（定向载体可量产千级 violation——对 §6 的 F4 风险评估有意义）。

为什么单线程 SE 会有 violation：O3 的 load 在操作数就绪即可发射，**不等待更老 store 的地址解析**（这正是 checkViolations 存在的原因——投机 load 的兜底）。store 地址经长依赖链晚到 + 年轻 load 同地址已执行 → violation。W5 载体（workloads/directed/sq_forward.c，72 行）的模式 4（alias 交叠 store）与模式 6（交错 store/load 对）即产生此类局面，实测 4 个。

---

## 2. 五阶段口径（event_seen / eligible / triggered / fault_applied / faults_injected）

设计原则：**事件的产生（event_seen）与注入器的资格过滤（eligible）分离**；trigger 的既有 attempted/eligible/injected 漏斗语义不变（chaos_lsu_trigger.hh:20-25, 66-69）；新增 event_seen 专用计数器。所有判定集中在唯一钩子 `CHAOSLSQFwd::violationPairHook`（§4），在 checkViolations 的重叠测试**之前**逐对调用。

| 阶段 | 定义（判定谓词） | 判定点/代码位置 | 计数器 | 备注 |
|---|---|---|---|---|
| **event_seen** | 一个 store-path 违规检查对被评估，且**金视图**（未腐蚀）下区间重叠——即 gem5 本应在此对上检出 violation | `violationPairHook` 内部，先于 F6 通知与任何腐蚀；调用自 lsq_unit.cc checkViolations（新钩子，位置≈:558-567，替换现 violationCorrupt 块） | 新增 `movEventsSeen`（随 exit 回调打进 l0 funnel 行） | 事件源级计数，与 tier 无关；golden 下 `movEventsSeen == lsq0.memOrderViolation`（§5.4 交叉验证）。checkViolations 在首个重叠对即 return（lsq_unit.cc:611-614），故每个检出 store 恰贡献 1 个 event_seen |
| （attempted，既有） | 每次 store-path 对评估（hook 被调），不论重叠 | 同上，钩子第一行 `lsuTrigger->onAttempt()` | `trigger.attempted` | 含非重叠对；load-path 对在调用点被 `!inst->isLoad()` 短路，不计 |
| **eligible** | event_seen 对再通过注入器资格过滤。默认过滤 = 无额外过滤（重叠即资格），对应清单 L03 行"仅当存在真实或潜在地址冲突时计为 eligible"（完整任务执行清单.md:11162 附近） | F0-F5：`lsuTrigger->onEligible()`（仅对 event_seen 对调用）；F6：`onF6Event()` 内部自增（chaos_lsu_trigger.hh:168） | `trigger.eligible` | **修复 F-047 的关键**：现实现 violationCorrupt 对每个对（含非重叠）消耗 onEligible（CHAOSLSQFwd.cc:405-407），且与 corrupt() 的 SqForward 流共用同一 trigger（流混合、531 eligible 来源）。新钩子只在重叠对上消耗资格 |
| **triggered** | tier 逻辑判定"现在开火"。F6 = 首个 MemoryOrderViolation 事件（onF6Event 置 spent，恰好一次）；F0 = eligible 流上均匀抽样；F1-F5 各按 05 r2-r8 | F6：`chaosLsuF6Notify(MemoryOrderViolation)` → `CHAOSLSQFwd::f6Thunk` → `onF6Event()` 返回 true → `f6_pending=true`；同栈内钩子立即消费（同位点模式，见 §4.3）；F0-F5：`onEligible()` 返回 true | `trigger.injected` | F6 事件序确定性：golden 三副本 violation 计数全同（§1.4）证明事件流无 RNG |
| **fault_applied** | 比较地址视图**实际被 XOR 且比较结果被反演**（漏报达成）——有效位约束在代码内验证：翻转后 `!(inst_eff_addr2 >= ld1' && inst_eff_addr1 <= ld2)` 必须成立 | 钩子内，triggered 之后；写入点见 §3 | 新增 stats `numViolationAddrFlips` + `l0_funnel.injected` | 若单 bit 翻转未能反演结果（低位翻转区间仍重叠），在有效位集合内重抽（≤8 次）后回退 MSB（见 §3.3）——**不允许**无效果落账（防 ITEM-271 式幻影激活） |
| **faults_injected** | 落账：日志行 + stats + exit funnel 行 | `writeLog("violation_addr_bitflip", ...)`（log 文件，chaos_l0 纪律）+ `++faults_injected_count` + exit 回调 funnel | `faults_injected_count`、`CHAOS_LSU_TRIGGER ... injected=` | 单一同步写点 ⇒ **fault_applied == faults_injected 恒成立** |

**守恒关系**（exit 时审计，违反即 bug）：

```
attempted ≥ event_seen ≥ eligible ≥ triggered ≥ fault_applied == faults_injected
```

- 默认配置（无额外过滤）下 `event_seen == eligible`；
- F6 下 `triggered == fault_applied == faults_injected == 1`（若事件流非空），`triggered == 0` 当且仅当 `event_seen == 0`；
- count_only（census）：`fault_applied == faults_injected == 0`，`eligible` 为满计数（CHAOS_ELIGIBLE_COUNT / CHAOS_LSU_TRIGGER eligible=N 双通道读出，§5.3）；
- golden 回归（无注入器挂载或 structMode≠violation_addr）：钩子第一行短路，所有计数为 0，行为逐字节等于 golden。

---

## 3. 故障写入点（L03 语义 = violation 比较地址 bitflip）

### 3.1 比较地址在哪个数据结构

比较地址**不是**持久数据结构字段，而是 `LSQUnit::checkViolations` 的**栈上局部视图**（比较器输入寄存器的软件等价物）：

- store 侧：`inst_eff_addr1 = inst->effAddr >> depCheckShift`、`inst_eff_addr2 = (inst->effAddr + inst->effSize - 1) >> depCheckShift`（lsq_unit.cc:539-540）；
- load 侧：`ld_eff_addr1 = ld_inst->effAddr >> depCheckShift`、`ld_eff_addr2 = (ld_inst->effAddr + ld_inst->effSize - 1) >> depCheckShift`（lsq_unit.cc:554-556）；
- 源字段是 `DynInst::effAddr / effSize`（dyn_inst.hh，pushRequest 翻译完成后回填，lsq.cc:828-833）；`depCheckShift` 在 B0 = **0**（逐字节比较；lsu_proxy.py:582 `cpu0.LSQDepCheckShift = 0`，config.ini 实证；BaseO3CPU.py:144-146 默认 4 仅 S3 变体用）。

**bitflip 施加在 load 侧视图 `ld_eff_addr1`（by-reference，沿用现钩子 lsq_unit.cc:563 的传参方式），绝不触碰 `DynInst::effAddr` 本体**——架构地址保持真实，后续任何重放/重执行用真地址；只有**这一次比较**看见腐蚀视图。硬件故事：LQ 违规检查器的地址比较器输入寄存器单周期翻转。腐蚀天然只作用于当前这对（循环下一迭代重新计算局部变量），即"单比较器周期故障"。

### 3.2 对后续执行的可观测影响路径（激活链）

```
ld_eff_addr1 翻转有效位
  → lsq_unit.cc:569 重叠测试失配（该对不检出）
  → memDepViolator 不为该 load 置位 / checkViolations 继续扫描
  → [若该 store 无其它重叠 load] iew.cc:1318 ldstQueue.violation(tid)==false
  → 不 squashDueToMemOrder（iew.cc:1337）、不 instQueue.violation（:1334）
  → 年轻 load 的陈旧值不經重放直接提交（L4 提交值）
  → 若该值喂入 W5 的 FNV 累加器（sq_forward.c:16-18 acc）→ 校验和变化（L5 SDC）
```

两条**确定性可观测信号**（最小注入验证用，§5.5）：
1. **主信号**：`lsq0.memOrderViolation` 4→3、`iew.memOrderViolationEvents` 4→3（本对漏检）；
2. **次信号（部分掩蔽情形）**：若同一 store 还有第二个重叠 load（golden 在第一个重叠对即返回，故此情形 = 故障后检查器在下一个重叠对检出）：计数不降，但 **violator 身份转移**（squash 起点 load 变更）——注意此时第一个 load 仍逃过重放（squash 从更年轻的 violator 起），陈旧值提交的 SDC 路径**依然成立**。故日志必须记录被腐蚀对的 store/load sn+PC+addr，以区分两种结局（漏检 vs violator 转移），两者都算 fault_applied。

### 3.3 位选择：有效位集合约束（防幻影激活的关键设计决策）

现状缺陷（不得继承）：现 `violationCorrupt` 用 `rng() % 20` 翻 0-19 位（CHAOSLSQFwd.cc:408）。B0 下 depCheckShift=0、视图即原始字节地址，8B 对齐访问翻低位（如 bit3=8B）常**不改变重叠判定** → faults_injected++ 但比较结果不变 = 无效果注入（幻影激活，正是 F-047 在 ITEM-271 上实证的病）。

设计：**位从"有效位集合"均匀抽取**——`{b : ld_eff_addr1 ^ (1<<b) 使重叠判定翻转}`。实现为：抽 b∈[0,64) 均匀（种子化 mt19937），施加后**代码内验证**重叠判定确实翻转；未翻转则重抽（≤8 次），仍失败则回退确定性的 bit 63（B0 SE 用户地址 bit63=0，置 1 后视图 ≥2^63，`inst_eff_addr2 >= ld_eff_addr1` 必假 → 必然漏检）。日志记录 `bit=B, orig=0x…, flipped=0x…, fallback=yes/no`。

**诚实声明（模型语义）**：有效位约束 = 故障总体限定在"比较器可观测位翻转"上；不改变比较结果的位翻转按构造不可观测，计入故障总体只会制造幻影激活。此约束作为 L03 模型语义的一部分写入 [LSU][SEM-F6] 提交信息与本设计文档，不是实现偷懒。

### 3.4 子模型边界（本提交只做 L03-a）

清单 L03 三子模型（完整任务执行清单.md:160, 11145 附近）：L03-a violation 漏报 / L03-b replay 丢失 / L03-c replay 目标错误。
- **本事件源 + L03-a 写入点（比较地址 bitflip）= [LSU][SEM-F6] 本提交**；
- L03-b/L03-c 的写入点在**重放消费侧**（iew.cc:1324 `getMemDepViolator` / iew.cc:1337 `squashDueToMemOrder`：丢弃一次 replay / 替换 violator 指针），事件源相同但钩子不同，按 one-patch-per-unit 各自成后续提交，不夹带。

---

## 4. 触发位置与接线

### 4.1 notify 点（事件源发射点）

**唯一新增发射点**：`CHAOSLSQFwd::violationPairHook` 内、event_seen 谓词为真时调 `chaosLsuF6Notify(ChaOSLsuEvent::MemoryOrderViolation)`。发射点在注入器钩子内而非 lsq_unit.cc 裸代码里，理由：发射谓词（金视图重叠）需要两侧地址，只有钩子拿得到；且 structMode≠violation_addr 时绝不发射，天然不污染其它模型的事件流（隔离要求）。

**为什么不挂在"检出之后"**（lsq_unit.cc:604-614 检出点）：F6 语义 = "首次出现指定事件时注入一次"；若事件定义为"已检出"，通知到达时本次比较已完成，腐蚀只能落到下一个事件——语义漂移为"第一个事件之后的第一个事件"，不诚实。因此事件谓词在比较**之前**以金视图判定，写入与触发同位点（见 4.3）。

### 4.2 消费者注册（CHAOSLSQFwd 补注册）

照抄 CHAOSAddrPath 模式（CHAOSAddrPath.cc:349-352 注册、:74-82 thunk；CHAOSPrefetch.cc:35-38 同构）：

- `chaos_lsu_trigger.hh`：`enum class ChaOSLsuEvent` **尾部追加** `MemoryOrderViolation`（=4）。现有 4 值 TlbHit/SqForward/DirtyEviction/CasSuccess（chaos_lsu_trigger.hh:48-49）的数值、含义、全部现有发射点**一字不动**：lsq_unit.cc:1557-1558（SqForward）、lsq.cc:453（CasSuccess proxy）、cache.cc:968-969 与 base.cc:409-410/671/1205-1206（DirtyEviction/CasSuccess）、tlb.cc:174-175（TlbHit）、store_set.cc:129 / mshr_queue.cc:151 / base.cc:621（SqForward 系 proxy 站点）。
- `CHAOSLSQFwd.hh/.cc`：新增 `static void f6Thunk(ChaOSLsuEvent)` + `static CHAOSLSQFwd *f6Consumer` + `bool f6_pending`；ctor 中 `if (lsuTrigger && lsuTrigger->tier == F6) { f6Consumer = this; chaosLsuF6Notify = &CHAOSLSQFwd::f6Thunk; }`。thunk 过滤 `ev == lsuTrigger->f6_event`——**MemoryOrderViolation 消费者收到 SqForward 通知时静默忽略，反之亦然**（双向隔离，靠枚举值过滤，不靠名字）。
- 触发器构造补传事件：`new ChaOSLsuTrigger(tier, seed, warmup, span, eventFromString(p.lsuF6Event))`（现 CHAOSLSQFwd.cc:44-45 未传事件，恒默认 SqForward——F-047 接线缺口之一）。`eventFromString` 本地静态函数，`"mem_order_violation" → MemoryOrderViolation`，并接受既有 4 串以保持参数面统一（模式照抄 CHAOSAddrPath.cc:67-72）。

### 4.3 F6 同位点消费（与 AddrPath 跨位点模式的差异，须写进代码注释）

CHAOSAddrPath 的 f6_pending 是**跨位点**模式：通知在 SqForward 站点、写入在 sendFragmentToTranslation 站点（CHAOSAddrPath.cc:81, 113-114）。本事件源通知与写入在**同一次钩子调用**内：thunk 置 `f6_pending` → 返回 → 钩子紧接检查 `f6_pending` 并应用/清零。理由：W5 事件流只有 4 个，事件间可能相隔整个程序段，"下一个钩子"没有意义；且本事件的写点就是事件点。首个事件：emit → onF6Event()=true → pending → 应用 → fault_applied=1。后续事件：onF6Event() 因 spent 恒 false（chaos_lsu_trigger.hh:166）→ 不再注入。

### 4.4 与 corrupt()/maybeSubstituteSource()/maybeDelayForward() 的流隔离（修 F-047 流混合）

新增 `StructMode::ViolationAddr`（串 `"violation_addr"`）。该模式下：
- `corrupt()`（SqForward 转发数据腐蚀，CHAOSLSQFwd.cc:181）**立即 return**（现只对 FwdSourceSub/PhaseOffset 短路，:192-193——补 ViolationAddr）；
- `maybeSubstituteSource` / `maybeDelayForward` 因 `struct_mode != 各自模式` 已自然短路（CHAOSLSQFwd.cc:301/354），无需改；
- 反向：structMode≠violation_addr 时 `violationPairHook` 第一行 return false（零回归）。
- **删除** `violationCorrupt(Addr&)`（CHAOSLSQFwd.hh:68, .cc:402-421）及其调用（lsq_unit.cc:558-567）——它 per-对无谓词消耗 onEligible、与 corrupt() 共用 trigger 造成流混合、F6 不可达、`rng()%20` 无效位——被 violationPairHook 完整取代。该钩子的唯一消费者就是 L03（全库 grep 证实：cpu.hh:521-523 + lsq_unit.cc:563 唯一调用点），删除属本语义提交范围。

### 4.5 .py 参数与命令行

- `CHAOSLSQFwd.py`：新增 `lsuF6Event = Param.String("sq_forward", "F6 event: sq_forward | dirty_eviction | cas_success | tlb_hit | mem_order_violation")`（镜像 CHAOSAddrPath.py:40）；`structMode` 文档追加 `"violation_addr (W5 L03: memory-order-violation comparison-address bitflip)"`。
- `lsu_proxy.py`：新增 `--lsqfwd_f6_event`（默认 sq_forward）并传入挂载块（lsu_proxy.py:793-812）；**删除死参数 `--lsqfwd_l03`**（lsu_proxy.py:253-255——argparse 收下但从不传入 SimObject，F-047 发现 (b)），L03 的模型选择统一走 `--lsq_struct_mode violation_addr`（单一机制，无双旗标）。
- `lsu_campaign.py`：`MODEL_FLAGS["L03"]`（现 :128 `("lsqfwd", ["--lsqfwd_l03"])`）改为 `("lsqfwd", ["--lsq_struct_mode", "violation_addr", "--lsqfwd_f6_event", "mem_order_violation"])`。tier 旗标沿用 FAMILY_TIER_FLAGS（:224-226）不改。
- `lsu_runner.py`：无结构改动（guard 命令从 LC 映射拼装，docstring 明示 no-drift）；F6 单遍执行，不走 F0 两遍法。
- schema：LSU 轨道 manifest 由 lsu_runner 从清单生成（无 F6 事件枚举字段），schemas/manifest.schema.json 是 KP/ooo 轨道的，**不触碰**（轨道隔离）。

---

## 5. 验证方案（全部为准入门条件，D-2026-10-10-ITEM289 原文要求）

### 5.1 正对照（必然产生事件）

**主正对照（现成，零新负载）**：W5 载体 golden 已实证 4 事件/run（§1.4，三副本确定性）。补丁后 count-pass 在 W5 上必须复现 `eligible=4`。**不需要新 directed 载体即可过门**。

**辅正对照（可选，工程加固）**：violation 定向探针草案（若需要更高事件密度的载体再建）——store 地址经长依赖链晚解析、年轻 load 立即发射同地址：

```c
/* vol_probe.c — 每轮构造一个 "young load executed, old store addr late" 局面 */
for (iter = 0; iter < K; iter++) {
    unsigned long idx = slow_index(iter);   /* 长依赖链: 除法/模链使 store 地址晚解析 */
    buf[idx] = iter;                        /* 老 store, 地址晚到 */
    acc = fnv(acc, buf[idx]);               /* 年轻 load, 地址立即就绪, 先执行 → violation 候选 */
}
```
预期 `lsq0.memOrderViolation` 随 K 增长（rob_fill 1723 的旁证说明定向载体可到千级）。此载体**不在本提交内**（one-patch-per-unit；仅当 W5 的 4 事件不足以支撑后续 F0/F4 需求时立项）。

### 5.2 负对照

1. **事件源隔离负对照（反混数证明）**：W5 + structMode=violation_addr + tier=F6 + **lsuF6Event=sq_forward**：lsq_unit.cc:1557 的 SqForward 通知照常到达，但 thunk 按枚举过滤（≠MemoryOrderViolation）不点火；本钩子的 MemoryOrderViolation 通知也被过滤（配置为 sq_forward）→ `injected=0`、`faults_injected=0`、输出与 golden 逐字节一致、`lsq0.memOrderViolation` 仍 4。证明与 SqForward 事件流双向不串。
2. **模式惰性负对照（零回归证明）**：W5 + structMode=byte_flip（S01 现行模式）+ 挂载注入器：`violationPairHook` 第一行 return（movEventsSeen=0、零发射、零写入），`lsq0.memOrderViolation` 仍 4——证明不选 violation_addr 时新路径完全惰性（golden 回归门）。
3. （无零事件 SE 载体可用作"天然零事件"负对照——9 载体全部 4-5，如实记录；上述两条构造性负对照覆盖同等证明责任。）

### 5.3 count-only（census）

复用 F-012 两遍法与既有 countOnly 机制：tier=F0、span=INT64_MAX（永不点火）、probability>0（挂载前提，CHAOSLSQFwd.cc:71/110）、structMode=violation_addr → `CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=<对评估数> eligible=4 injected=0`（lsu_runner.py 计数 pass 读此行）。双读出通道：countOnly=true 时另有 `CHAOS_ELIGIBLE_COUNT=4`。

**准入门（数值）**：`eligible == golden lsq0.memOrderViolation == 4`（W5）。eligible 与内建 stat 相等 = 事件谓词（金视图重叠、store-path-only）实现正确的**独立交叉验证**——两个计数器代码路径完全不同（gem5 stat vs 注入器谓词），相等非平凡。不等即 bug，禁止进入注入验证。

### 5.4 最小注入（单事件单注入，fault_applied 真实发生的可观测判定）

运行：W5 + tier=F6 + lsuF6Event=mem_order_violation + structMode=violation_addr + maxFaults=1 + **rngSeed=S≠0** + writeLog=true。判定证据（全部须在产物中出现）：

1. `lsq_fwd_injections.log` 一行：`Site: mem_order_violation_pair, FaultType: violation_addr_bitflip, bit=B, orig=0x…, flipped=0x…, store_sn=…, load_sn=…, addr=0x…`（含 sn/PC 供 L1 比较向量与 L2 传播分析——清单传播监控要求）；
2. `CHAOS_LSU_TRIGGER: … injected=1` 且 l0 funnel 行 `injected=1`；
3. **主信号**：`lsq0.memOrderViolation == 3 && iew.memOrderViolationEvents == 3`（golden=4）；**或次信号**：计数仍 4 但被腐蚀对的 load_sn ≠ 最终 violator 的 sn（violator 转移，日志可判）——两者其一成立即 fault_applied 真实发生（比较器消费了腐蚀视图）；
4. activated（L0 口径）：上述 3 成立 = 故障值被下游（比较器）消费；L5 结局由校验和判定（SDC 或 Masked，不预设）。

### 5.5 确定性重放

- 事件流确定性：golden g1/g2/g3 violation 计数全同（§1.4）——检测路径无 RNG；
- F6 点火确定性：首事件序确定；
- 位选择确定性：mt19937(rngSeed)（要求 **rngSeed≠0**；=0 时 random_device 不可重放——须写入 lsu_seed 规则核查项）；
- 验证：同 seed 跑 2 遍，stats.txt 的 `memOrderViolation/memOrderViolationEvents`、日志行（bit/sn/addr）、funnel 行**逐字节相同**；不同 seed 仅 bit（及由此的下游分岔）不同。

### 5.6 准入门汇总（ITEM-289 重跑前置）

| 门 | 条件 | 证据 |
|---|---|---|
| G1 构建 | 零新警告（-j16 规则） | scons 输出 |
| G2 零回归 | §5.2-2 负对照 + golden 校验和不变 | stats + 输出 |
| G3 census | eligible=4 == golden stat（W5） | CHAOS_LSU_TRIGGER 行 |
| G4 隔离 | §5.2-1 负对照 injected=0 且输出=golden | stats + 日志 |
| G5 最小注入 | §5.4 证据 1-3 全成立 | 日志 + stats |
| G6 重放 | 同 seed 双跑逐字节同 | diff |
| G7 守恒 | attempted≥event_seen≥eligible≥triggered≥fault_applied==faults_injected | funnel 行 |

---

## 6. 提交计划与风险

### 6.1 单提交文件清单（[LSU][SEM-F6] Add explicit memory-order-violation event source）

| 文件 | 变更 |
|---|---|
| `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh` | 枚举尾加 `MemoryOrderViolation`；头注释 09 §2.1 映射同步 |
| `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` | :558-567 violationCorrupt 调用块替换为 `violationPairHook` 调用（store-path 短路、传 4 视图 + is_load） |
| `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh` | StructMode::ViolationAddr；violationPairHook 声明；f6Thunk/f6Consumer/f6_pending；movEventsSeen；删 violationCorrupt |
| `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc` | 钩子实现（谓词/计数/发射/触发/有效位翻转/日志）；ctor 注册 f6Thunk + 事件串解析；corrupt() 补 ViolationAddr 短路；exit 回调补 movEventsSeen |
| `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py` | lsuF6Event 参数；structMode 文档 |
| `configs/se/lsu_proxy.py` | --lsqfwd_f6_event 参数 + 挂载传入；删 --lsqfwd_l03 |
| `tools/lsu_campaign.py` | MODEL_FLAGS["L03"] 更新（:128） |
| `docs/gem5-fi/lsu/{findings.md,task_plan.md}` | 语义变更记录 + 本设计文档入库 |

无新文件（SConscript 不动）。提交信息须载明：事件定义、五阶段口径、有效位约束（§3.3 模型语义）、同位点消费与 AddrPath 跨位点模式的差异、L03-b/c 不在本提交。

### 6.2 依赖顺序（F-047 修复时序约束的插入点）

```
golden #2/#3 完成并冻结 W1 golden（C++ 冻结期，平台身份 b64c808d）
  → OBS-1..4（各一 [LSU][OBS] commit）
  → [LSU][SEM-F6]（本提交；取代 F-047 草拟的 SEM-A"LSQFwd F6 消费者注册"，
      并吸收 SEM-B 中 L03 参数接线部分；SEM-B 若有其它模型遗留另行拆分）
  → lsu_runner TIMEOUTS 修复 → 3× census（G3）→ G1-G7 全过 → ITEM-289 单独重跑
```

### 6.3 风险（如实评估）

1. ~~单线程 SE violation 频率为 0~~——**已被 golden 数据否定**（9/9 载体 4-5 个，W5=4，三副本确定）。剩余风险不是"有没有事件"而是"事件流短"。
2. **事件流短（W5=4）的连锁后果（高风险，必须向用户摆明）**：
   - ITEM-289（F6）：可救——首事件确定性点火，G1-G7 可过，pilot 30 activated 可行（每 run 必点火，多样性来自位抽取与下游分岔）；
   - ITEM-285（L03-**F0**-W5）：条件可救——F0 两遍法 span=census N=4 时可确定性落在 4 事件之一（runner 已有机制），但默认 span=1000 永不点火，须 census 驱动；
   - ITEM-287/288（L03-**F4**-W5/W12）：**此事件源救不了**——F4 周期 10^5、首发需 ≥5×10^4 eligible，W5/W12（sqlite_like golden=4）差 4 个数量级；除非建 violation 密集载体（rob_fill 旁证可到 ~1.7×10^3，仍差 30 倍；要到 5×10^4 需长时运行的专业载体，属新负载立项）。**结论：MemoryOrderViolation 事件源解决 ITEM-289（及条件性解决 ITEM-285），不解决 ITEM-287/288**——后者的出路要么 F4→其它档重裁决，要么 violation 密集载体立项，须用户裁决。
3. **部分掩蔽（中风险）**：同 store 多重叠 load 时计数不降只换 violator（§3.2 次信号）——日志含 sn 可判，两结局都计 fault_applied；不影响 SDC 路径成立。
4. **激活多样性（中风险）**：F6 恒在首事件点火，若 W5 首事件对的有效位集合很小或其陈旧值不喂校验和，30 个 pilot 可能聚成少数簇——按清单"runs/clusters"口径如实聚簇，不凑数。
5. **L5 结局未知（低风险，不预设）**：漏检 violation 的陈旧值是否改变 FNV 校验和，须跑后才知道；SDC 与 Masked 都是合法结局，G5 只证 fault_applied。
6. **重建纪律（流程风险）**：本提交须严格排在 W1 golden 冻结之后（F-047 时序约束）。

---

## 7. 明确不做什么

1. **不近似映射**：不把内存序违规映射/冒充为 SqForward（D-2026-10-10-ITEM289 禁令）；SqForward 事件流、名称、统计一概不复用（新枚举值 + 新计数器 + 新日志 Site + §5.2-1 反混数负对照）。
2. **不改现有 4 种 F6 事件源**：TlbHit/SqForward/DirtyEviction/CasSuccess 的含义、枚举值、全部发射点（§4.2 列举的 9 处）一字不动；本设计只**追加**第 5 种。
3. **不动 golden**：golden #2/#3 与 W1 golden 冻结先行；本提交落位其后；§5.2-2 证明不激活时零回归。
4. **不夹带**：L03-b（replay 丢失）/L03-c（replay 目标错误）的重放侧钩子（iew.cc:1324/1337）、violation 密集载体（§5.1 辅正对照）、FS/TSO load-path 事件、多核泛化——全部不在本提交（各自独立 unit）。
5. **不造无效果注入**：有效位约束（§3.3）使每次 fault_applied 必然改变比较结果；不重蹈 ITEM-271 幻影激活。
6. **不混轨道**：OoO 轨道 artifacts 只作微架构频率旁证（§1.4 已标注），任何数字不进 LSU 轨道结果表。

---

## 附：关键源码引用索引

| 主题 | 位置 |
|---|---|
| violation 检测（事件本体） | lsq_unit.cc:535-621（store-path 检出 :604-614；重叠测试 :569；局部视图 :539-540/:554-556） |
| executeStore→checkViolations | lsq_unit.cc:699-758（调用 :756）；executeLoad→（checkLoads）:690-691 |
| 事件消费（squash/replay） | iew.cc:1318-1340（squashDueToMemOrder :497-525；stat :1339/:1356） |
| 内建计数 stat | lsq_unit.cc:273 + :582/:609（memOrderViolation）；iew.cc:176-177 |
| F6 触发器/枚举/通知 | chaos_lsu_trigger.hh:43-56, 155-170 |
| 现有 4 源发射点 | lsq_unit.cc:1557-1558；lsq.cc:449-453；cache.cc:968-969；base.cc:409-410/621/671/1205-1206；tlb.cc:174-175；store_set.cc:129；mshr_queue.cc:151 |
| f6Thunk 消费者模式 | CHAOSAddrPath.cc:74-82, 349-352；CHAOSPrefetch.cc:35-38, 95-102 |
| 现缺陷钩子（被取代） | lsq_unit.cc:558-567；CHAOSLSQFwd.cc:402-421（violationCorrupt） |
| B0 平台参数 | lsu_proxy.py:582-583（DepCheckShift=0, CheckLoads=True）；BaseO3CPU.py:144-149 |
| W5 载体 | workloads/directed/sq_forward.c（72 行）；golden 4 事件：runs/lsu/golden/sq_forward/g{1,2,3}/stats.txt:1595/1608 |
| 裁决/审计 | task_plan.md:156（D-2026-10-10-ITEM289）；findings.md:63（F-047） |
| L03 清单 | 完整任务执行清单.md:160（模型行）、:10990/11066/11142（ITEM-285/287/289） |
