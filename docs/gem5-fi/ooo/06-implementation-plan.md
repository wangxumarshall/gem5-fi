# 06 · OoO 故障注入实现总纲（宏伟计划）

> **文档地位**：本文件是北极星方案（`00`–`05`，源 xlsx V1.0 的忠实提取）的**落地路线图**，不是设计数据。
> **裁决规则（用户指令 2026-09-22）**：本文件与 `00`–`05` 冲突时，**一律以 `00`–`05` 为准**；本文件只回答「怎么排、怎么建、怎么验」。
> 编号体系沿用设计单元 `D01–D91` 与实验格 `E001–E226`；本文件新增工作包编号 `W0–W9`、里程碑 `M0–M6`。
> 编写日期：2026-09-22 · 分支 `fi-ding` · 依据：北极星全文 + 仓库源码盘点（22 个注入器/runner/campaign/classify/configs/workloads）+ 机制核实（见 §2）。

---

## 1. 目标与成功判据

### 1.1 三问（北极星 §1 原文目标）

1. 哪些位置有**真实 SDC 潜力**（而不是被 gem5 依赖检查拦成 Crash）；
2. SDC 发生前**微架构层有什么可观测前兆**（L1 层，文献空白）；
3. **结构化故障模型相对随机翻转的增量**到底有多大。

### 1.2 最终交付物

| 交付物 | 形态 | 验收 |
|---|---|---|
| 226 实验格 × 7 结果列回填 | `05-expanded-matrix.csv` 的 SDC%/Crash%/Timeout%/Masked%/仿真器断言崩溃占比%/潜伏期/污染扇出数 | 全部非 deferred 格有值（含 CI） |
| L0–L4 五层观测数据 | artifacts + 元分析报告 | 每格 L1 特征量与 L2 五分类可追溯 |
| 三关自检记录 | 自检报告（§5 M2） | D25/D28 复现 TC'23 SDC≈0%；D83–D85 FP 负载一致性 |
| 元分析报告 | 三问的回答 + 位置×SDC 潜力排序 + 前兆特征库 + 结构化增量对照 | 结论每条带 D/E 编号与样本量 |

### 1.3 不可妥协的口径（防口径漂移）

- 样本量：每格统一 **n=2000**（运行计数）或**覆盖 2000 次目标事件**（事件覆盖计数）；深挖档 16,587 仅关键结论格。
- 试跑：每格 F0–F3 × 20 次，只用于挑档（非 Crash 占比最高 2 档），**不得当正式结果引用**。
- L4 双拆分：仿真器断言崩溃 ≠ 架构崩溃（复用 v1.4 三分类/reclassify3 体系）。
- SVE 谓词行 D78–D82 与 PolyBench（SVE 向量化版）**默认 deferred**（920 无 SVE；仅 SVE+SME 版配置适用），不混入 920 建模口径。
- 参数非 920 真值（边界⑤）：一切对外产出注明「A72 公开资料 + gem5 示例估计」。

---

## 2. 机制核实结论（源码级，2026-09-22 完成）

北极星 §6 要求「实验前必须先核实」的三项已核实，另有四项新核实。**这些结论修正若干 D 行的落点（落点修正≠设计变更：注入的故障语义不变，宿主结构按 gem5 实际实现对应）**：

| # | 北极星表述 | gem5 v25.1 实际 | 对 D 行的影响 |
|---|---|---|---|
| N1 | D23/D24「重命名检查点」 | O3 rename **无 checkpoint**，用 history buffer：`rename.cc:1176` `historyBuffer[tid]`（`rename.hh:301` `RenameHistory{instSeqNum, archReg, newPhysReg, prevPhysReg}`）；squash 走 `doSquash` 反向回滚（`rename.cc:935`），commit 后 `removeFromHistory`（`rename.cc:1007`） | D23/D24 注入点 = **historyBuffer 表项字段**；窗口 = push_front → squash 消费/commit 移除 |
| N2 | D36–D39「ROB 的旧物理寄存器字段」 | ROB 项不存 old-phys；squash 回滚用的 prevPhysReg 同样在 **RenameHistory** | D36–D39 注入点 = `RenameHistory::prevPhysReg`；事件 = commit 阶段 squash 处理（语义与北极星一致）。D40（ROB 项整体旧数据）仍在 rob.cc 槽位复用处 |
| N3 | D62 系「标量 FP 与向量是否两套寄存器类」 | **修订（2026-09-24，W1.2/W1.3 实证推翻初判）**：结构上是两套（`rename_map.hh:179` `std::array<SimpleRenameMap, CCRegClass+1>`），**但 AArch64 用法上标量 FP 走 VecRegClass**——三重确认：纯标量 FP 负载 flFloatMin=192 恒满（FloatRegClass 池从未分配）+ 标量 FP 指令在场（objdump + committedInstType 动态计数精确吻合、SimdFloat*=0）+ vec 池压穿到 0（初始 4） | **北极星 D62 行自带合并条款触发**（04 设计理由原文：「如果实际是同一套映射，此行与向量行应合并，不重复跑」）：D62–D66 并入 D67–D71、D72/D73/D76 并入 D74/D75/D77——同挂点 VecRegClass，差异仅指令过滤（opClass Float\* vs SimdFloat\*）；numPhysFloatRegs=192 在 C3 实际闲置（论文口径注明）。原判「不合并」基于结构存在性，被用法证据推翻 |
| N4 | README §7「向量物理寄存器池未出现」 | 参数已存在：`BaseO3CPU.py` `numPhysVecRegs`（默认 256）/`numPhysVecPredRegs`（默认 32） | **vec48 = config-only 改动**；SVE 谓词池同理 |
| N5 | D25/D26「ROB 的 PC 字段」 | 现有 CHAOSROB `Field={Result,Done,ExcStatus,DestPhys,Spec}`，**无 PC** | W5.1 需新增 PC 字段模式 |
| N6 | IQ=64 | v25 O3 `instQueues = VectorParam.IQUnit`（无标量 numIQEntries） | C3 config 用 IQUnit 向量定义 Int/FP IQ，各 64 项 |
| N7 | Decode 注入（D01–D10） | StaticInst 有共享/缓存语义，原地改字段会污染所有实例 | 可行路径：decode 输出对 ExtMachInst（机器指令位）做位级操作 → re-decode → 替换 `DynInst::staticInst`；D08 符号扩展位可能需值级 patch → **W6.0 spike 前置** |

**待执行期 spike 的核实项**（不阻塞 W0–W2）：ROB done 位置位点（writeback 路径）、FreeList 头/尾指针内部结构、D55 分发端口选择在 gem5 FUPool 机制下的对应物、D08 值级 patch 可行性。

---

## 3. 总体架构（四层）

```
┌─ 编排层 tools/campaign.py ──────────────────────────────┐
│ 两阶段编排（pilot F0-F3×20 → 选2档 → formal 2000）        │
│ 事件覆盖计数（密度表倒推运行数） · E/D 编号贯穿 manifest    │
├─ 观测层（新建三大件 + 复用）──────────────────────────────┤
│ L2 CHAOSCommitTrace + commit_diff.py（TC'23 五分类+潜伏期）│
│ L1 CHAOSMicroSnap + micro_diff.py（影子快照比对，最大新建）│
│ L0 注入项生命周期（各注入器内建） · L3 扇出（PRF 读踪复用） │
│ L4 reclassify3 双拆分（复用） · gem5 stats 消费（新建）    │
├─ 注入层（扩展现有 22 注入器 + 3 个新挂点）────────────────┤
│ 统一触发语义 F0–F5（共享 helper） · 新故障模式族（§4 W4-W7）│
│ 新挂点：rename historyBuffer / decode 输出锁存 / ROB insert│
├─ 平台层 configs/se/ooo_proxy.py（config_family C3-OOO）──┤
│ ROB128 · PRF int128/fp192/vec48 · IQ64(Int/FP 各) · 2.6GHz│
└──────────────────────────────────────────────────────────┘
```

**关键架构决策**：

| 决策 | 内容 | 理由 |
|---|---|---|
| A1 | **扩展现有注入器**（CHAOSRenameMap/FreeList/ROB/IQ/Decode 加模式），不另起炉灶 | 挂点/采样/日志骨架已验证（22 个 SimObject 在产）；one-patch-per-unit 粒度天然对齐 |
| A2 | **新建 config_family `C3-OOO`**（configs/se/ooo_proxy.py），不动 C0/C2 | 北极星平台口径（vec48/IQ64）≠ 鲲鹏轨道；隔离防污染 |
| A3 | **触发语义统一到 F0–F5 档位**（共享 `chaos_trigger` helper：单次均匀 / 固定平均间隔±50% 抖动 / 事件回调 / 永久卡死） | 现有 probability 驱动 ≠ 北极星 F1–F3 固定间隔语义；226 格的频率列才能逐格对上 |
| A4 | **L1 影子比对走「快照 + 离线 diff」**：无故障参照运行按 commit 序号采样 dump 微架构状态摘要，故障运行同样采样，按 commit 序号对齐比对 | 全量影子流水线不可行；commit 序号对齐免疫时序扰动；采样开销可控 |
| A5 | **L2 五分类走「两遍法」**：第一遍量产无 trace 判结局（终态 oracle），第二遍对需细分样本（SDC/Crash/Hang）同 seed 带 commit-trace 重放 | 全程开 trace 的减速不可接受；重放量 ≈ 非 Masked 占比 |
| A6 | **manifest schema v3（additive）**：v2 之上加 ooo 扩展块 `design_unit_id / experiment_cell_id / frequency_tier / counting_basis / phase(pilot|formal)` | E 编号贯穿数据链，回填工具按 E 聚合；v2 兼容不动 |
| A7 | **负载 SE 裁剪纪律**：每负载定义 SE 预算（单次运行 ≤60s @O3）的迭代配置并写入负载文档 | 45 万次 × 全尺寸 CoreMark 不可行；北极星未规定迭代数，属实现自由度 |

---

## 4. 工作分解 WBS（W0–W9，每个编号 = 一个 patch 单元）

> 每个 patch 遵守 CLAUDE.md 纪律：**构建零警告 + 定向功能验证（真机输出为证）+ 回归（reg_chain golden `f247ef3fe6f02cfd`，C3 上 int 负载 golden 不变）→ commit → 自动 push**。
> 每个 W 包启动时先用 `superpowers:writing-plans` 写执行计划到 `docs/superpowers/plans/`（两级计划体系：本文件=总纲，执行计划=逐补丁细化）。

### W0 平台与机制底座（3 patch）

| # | 内容 | 主要文件 | 验证 |
|---|---|---|---|
| W0.1 | **C3-OOO 配置**：`configs/se/ooo_proxy.py`（ROB=128, physInt=128, physFloat=192, **physVec=48**, IQUnit Int/FP 各 64, 2.6GHz, NEON；SVE flag 预留 C3-SVE 变体）；runner.py `CONFIG_FAMILY` 加 C3；manifest schema platform 枚举加 `C3-OOO` | configs/se/ooo_proxy.py, tools/runner.py, schemas/manifest.schema.json, tools/manifest_validate.py | reg_chain 在 C3 跑通 golden `f247ef3fe6f02cfd`；`numPhysVecRegs=48` 经 m5 sumlist/stats 证实生效 |
| W0.2 | **统一触发语义层**：共享 helper `chaos_trigger.hh`（F0 单次均匀 / F1–F3 固定平均间隔±50% 抖动（2.6M/260K/26K cycle）/ F4 事件回调注册 / F5 永久）；manifest trigger 加 `fixed_interval+jitter` 模式 | CHAOS/gem5/src/cpu/o3/chaos_trigger.hh(+cc), schema | 定向验证：F1 档在无负载空转下注入时刻间隔实测 ∈ [0.5×, 1.5×]×2.6M cycle（日志为证） |
| W0.3 | **事件密度基线工具**：无故障运行统计每运行事件数（分支误预测 / squash / RAT 覆盖 / ROB>80% 周期 / IQ>80% 周期 / freelist≤阈值周期），产出密度表（负载×事件→次/运行） | tools/event_density.py +（若 stats 不足）CHAOSProbe 采样 | CoreMark 上误预测数与 gem5 stats `branchMispredicts` 一致（两源对照为证） |

### W1 负载建设（6+ patch，每负载一 patch）

| # | 内容 | 验证 |
|---|---|---|
| W1.0 | `workloads/ooo/` 构建框架：Makefile + aarch64-linux-gnu-gcc 交叉编译（-static）+ SE 预算 ≤60s 迭代裁剪纪律 | 空核编译运行通过 |
| W1.1 | CoreMark（迭代数按预算裁剪） | 自带 CRC 校验 + golden 入 `GOLDEN_IDS`，两次运行 checksum 稳定 |
| W1.2 | Embench 整数子集 + 浮点子集（各选 5–8 代表程序） | 每程序自带校验退出码 + golden |
| W1.3 | PolyBench（gemm/lu/cholesky/jacobi-2d） | 全数组输出 `array_hash` oracle |
| W1.4 | GAP（bfs/pr）+ libjpeg-turbo（NEON 路径） | 输出比对 oracle（可拆 2 patch） |
| W1.5 | **自设探针核 ×3**：分支误预测密集核 / 长依赖链压力核（int+vec 两版）/ ROB 填满核（int+fp 两版） | **达标验证**（用 W0.3）：误预测密度、freelist<8 达 N 次/运行、ROB>80% 达 M 次/运行——不达标不算完成 |

### W2 观测层三大件（6 patch）

| # | 内容 | 验证 |
|---|---|---|
| W2.1 | **L2 commit-trace**：CHAOSCommitTrace（hook commit.cc 逐提交指令 dump：commit 序号/PC/opcode/关键操作数值 → gzip） | 定向：100 条指令的 trace 与 `--debug-flags=Commit` 抽查一致；减速比实测记录 |
| W2.2 | **L2 离线五分类器**：tools/commit_diff.py（参照 trace vs 故障 trace 按 commit 序号对齐 → TC'23 五分类{执行时间错/指令流改变/指令替换/操作数强制切换/数据损坏} + 首次分歧 commit 序号=潜伏期） | 构造 5 类定向故障各 1 例，分类正确 |
| W2.3 | **两遍法编排**：campaign 支持 trace 重放遍（对 SDC/Crash/Hang 样本同 seed 带 trace） | 小批次 pilot 端到端跑通，L2 列可回填 |
| W2.4 | **L1 微架构快照**：CHAOSMicroSnap（按 commit 序号间隔采样 dump：RAT int/fp/vec 表、freelist 占用、ROB head/tail、IQ 占用、周期数）+ tools/micro_diff.py（分歧项数/占用偏差/停顿偏差/flush 次数差/IPC 偏差序列 + **隐蔽样本标记**：Masked或SDC 但 IPC 偏差>50%） | 定向：一次已知 RAT 注入运行 vs 无故障参照，分歧项数>0 且随 commit 演化合理 |
| W2.5 | **L0 通用化**：注入项生命周期接口规范（注入即登记：reads_before_overwrite / overwritten / overwritten_at_cycle），各注入器 patch 内接线 | 规范文档 + 第一个接线注入器（W4.2）示范 |
| W2.6 | **L3 扇出 + stats 消费**：污染 PRF 读踪计数（regfile 读踪复用，rat/rob/iq 换值模式记录目标 PRF id）；runner 从 stats.txt 提取摘要进 results.jsonl | 定向：换值注入后扇出数>0；results.jsonl 含 stats 块 |

### W3 编排层（3 patch）

| # | 内容 | 验证 |
|---|---|---|
| W3.1 | **两阶段编排**：campaign pilot（每格 F0–F3×20）→ 自动选非 Crash 占比最高 2 档 → formal 2000；选择记录落盘（可审计） | 玩具网格端到端：pilot→选档→formal 全链产物齐全 |
| W3.2 | **事件覆盖计数模式**：目标事件数 2000，按 W0.3 密度表倒推运行数；覆盖不足自动报告（不静默） | 密度表上高/低密度两事件各跑一例，运行数与倒推公式一致 |
| W3.3 | **回填工具**：tools/backfill_expanded_matrix.py（artifacts → `05-expanded-matrix.csv` 7 结果列 + Wilson CI + E/D 编号聚合） | 玩具数据回填后 CSV 列值与 artifacts 一致（脚本断言） |

### W4 Int Rename 注入器（8 patch，北极星第一优先单元）

统一接线：W0.2 触发语义 + W2.5 L0 生命周期 + A6 manifest v3 扩展块。

| # | D 行 | 新模式 | 挂点 |
|---|---|---|---|
| W4.1 | D11/D12 | map_bitflip 补**双比特**版 | 现有 rename_map.hh:296 |
| W4.2 | D13/D14 | **swap_to_active**（换值：从 ROB in-flight 目的集合挑活跃 PRF ≠ 当前值；F4=误预测恢复瞬间触发） | 现有挂点 + commit/bac 误预测事件回调 |
| W4.3 | D15 | RAT 卡死 F5（永久 bit + **写路径 mask**，借 G2 setStuckTarget 经验：真永久） | rename_map 写路径 |
| W4.4 | D16 | **stale_read**（读到旧数据：表项被覆盖瞬间写入静默失效一次，下游拿旧映射） | setEntry 覆盖时刻 hook |
| W4.5 | D17/D18 | 重复分配（mark_free 语义对齐 + F4=freelist≤8 事件触发） | 现有 free_list.hh:119 |
| W4.6 | D19 | **drop_release**（丢失释放：一次性抑制，持续到运行结束） | freeList 归还路径 |
| W4.7 | D20–D22 | 空闲表头/尾指针 单/双 bit/卡死 | free_list 指针结构（spike 后定字段） |
| W4.8 | D23/D24 | **historyBuffer 字段翻转**（新挂点，N1 结论：窗口=建立→消费） | rename.cc historyBuffer |

每 patch 验证：构建零警告 + 单次注入真机生效证据（evidence log 引用）+ reg_chain golden 回归 + L0 生命周期字段出现在日志。

### W5 Int Dispatch/ROB 注入器（12 patch）

| # | D 行 | 新模式 | 挂点 |
|---|---|---|---|
| W5.1 | D25/D26/D28/D29 | ROB PC/标识符 单/双 bit（Field 加 **PC**，N5） | 现有 rob.cc:254 |
| W5.2 | D27/D31 | ROB PC/标识符 卡死 F5 | rob 写路径 mask |
| W5.3 | D30 | ROB 标识符 **swap_to_active**（复用 W4.2 目标挑选逻辑） | 现有 |
| W5.4 | D32/D33 | **done 提前置位**（未完成先标 done；F4=ROB>80%） | writeback done 标记点（spike 定位） |
| W5.5 | D34/D35 | **done 延迟置位**（已完成不标 → 资源耗尽前兆族） | 同上 |
| W5.6 | D36–D38 | **old-phys 翻转/换值**（N2：RenameHistory::prevPhysReg；F4=commit squash 时） | rename historyBuffer + commit squash |
| W5.7 | D39 | old-phys 卡死（F5 × 事件覆盖计数特例） | 同上 |
| W5.8 | D40 | **ROB 槽位 stale_read**（新指令分派写入静默失效，commit 读旧记录） | rob.cc insert/槽位复用点 |
| W5.9 | D41–D46 | ROB 头/尾指针 单/双 bit/卡死 | rob 指针推进点 |
| W5.10 | D47–D49 | IQ ready **提前/永不置位**（F4=IQ>80%） | inst_queue.cc 现有挂点 |
| W5.11 | D50–D54 | IQ tag 族：**换值/单/双 bit/卡死/读到旧数据**（µop 覆盖瞬间） | inst_queue entry 写入点 |
| W5.12 | D55 | 分发端口选择路由（**探索性**：gem5 FUPool 机制对应物 spike；若机制不匹配 → honest-reject 记录，北极星本就标注置信度低） | issue 路由点 |

### W6 Int Decode 注入器（8 patch，机制风险最高）

| # | D 行 | 内容 |
|---|---|---|
| W6.0 | — | **机制 spike**：ExtMachInst 位级操作 → re-decode → 替换 DynInst::staticInst 原型；产出机制选型记录（含 D08 值级 patch 可行性） |
| W6.1 | D01/D02 | opcode 单/双 bit（编码位翻转后 re-decode；非法编码→非法指令=Crash 正是预期） |
| W6.2 | D03 | opcode **换值**（合法且操作数格式兼容的 opcode 互换，如 ADD↔SUB 类内） |
| W6.3 | D04/D05 | 源/目的寄存器号 单/双 bit（编码 reg 字段位翻转） |
| W6.4 | D06/D07 | 立即数 单/双 bit |
| W6.5 | D08 | 符号扩展位**定向**翻转（按 spike 结论：编码级或值级） |
| W6.6 | D09 | 子字段拼接错位（imm 子字段移位错位重编码；ARM64 各类立即数位宽 ADD12/MOVZ16/B.cond19/B26/ADRP21） |
| W6.7 | D10 | 裂解控制位（该拆不拆/不该拆被拆；gem5 宏裂解机制 spike：m5 v25 O3 裂解在 decode/rendezvous 的实际位置） |

### W7 FP/SIMD 三单元（4+1 patch，复用 W4–W6 机制 × 寄存器类参数化）

| # | D 行 | 内容 |
|---|---|---|
| W7.1 | D56–D61 | FP Decode（W6 机制 + FP/SIMD 指令过滤；含 D61 指令路由判定位） |
| W7.2 | D62–D66, D72/D73/D76 | 标量 FP RAT 族——**修订（N3，2026-09-24）**：与 W7.3 向量族同挂点 VecRegClass 执行，差异仅指令过滤 opClass Float\*（原 FloatRegClass 落点对 AArch64 惰性、阈值 ≤12 作废；D 行编号保留，结果列按合并口径） |
| W7.3 | D67–D71, D74/D75/D77 | 向量 RAT 族（VecRegClass；阈值 ≤6；libjpeg-turbo 压力） |
| W7.4 | D83–D91 | FP Dispatch/ROB（含**三关自检第二/三关** D83–D85：FP 负载重跑 ROB 基线格与高 SDC 格） |
| W7.5 | D78–D82 | SVE 谓词族（**可选阶段**：C3-SVE 变体 + PolyBench SVE 版；默认 deferred，见 §1.3） |

### W8 实验执行（按北极星推进序；批次=数据提交）

| # | 批次 | 门 |
|---|---|---|
| W8.1 | **三关自检**：D25/D28（F0, CoreMark/Embench, n=2000）→ 须复现 TC'23 SDC≈0%；不过关=注入器有错，回修 | M2 门 |
| W8.2 | Int Rename 格群（D11–D24 → E 格，pilot→formal 全流程） | M3 门 |
| W8.3 | Int Dispatch/ROB 格群（D25–D55） | M4 门 |
| W8.4 | Int Decode 格群（D01–D10） | |
| W8.5 | FP/SIMD 三单元格群 + D83–D85 自检 | M5 门 |
| W8.6 | 深挖档：仅论文级关键格加测 16,587 | |
| W8.7 | L1/L2/L3 二遍重放遍（对 W8.2–W8.5 的非 Masked 样本） | |

每批次交付：campaign 结果 commit（artifacts + 回填后的 CSV + 批次小结：n_valid/CI/异常清单）。跑批资源纪律：内存约束下并行槽位上限（参照 FS 4-slot 教训，SE 按实测定），OOM 屠批禁令。

### W9 元分析与交付（3 patch）

| # | 内容 |
|---|---|
| W9.1 | 7 结果列全量回填 + 完整性审计（脚本断言：非 deferred 格无空值，CI 齐） |
| W9.2 | 元分析报告：三问回答；位置×SDC 潜力排序；L1 前兆特征库（资源耗尽族趋势曲线：D19/D34/D35/D48/D49/D76/D77）；结构化 vs 随机增量四联对照（同字段 bit翻转/换值/卡死/旧数据，如 RAT D11–D16）；事件触发 vs 固定间隔配对结论（D14/D18/D33/D36/D50） |
| W9.3 | 论文素材定稿（含边界⑤参数来源声明、SVE 行排除说明、D55 探索性标注） |

---

## 5. 里程碑与推进序

```
M0 平台+负载+密度底座（W0+W1）──────────── 可跑 pilot
M1 观测+编排就绪（W2+W3）───────────────── L0-L4 全链可产出
M2 三关自检第一关通过（W4.1-W4.2+W5.1+W8.1）注入器正确性门 ★北极星自检锚点
M3 Int Rename formal 完成（W4 全+W8.2）──── 北极星第一优先闭环
M4 Int Dispatch/ROB 完成（W5+W8.3）
M5 Int Decode + FP/SIMD 完成（W6+W7+W8.4/W8.5）＋三关自检第二/三关
M6 回填+元分析+论文素材（W9）
```

推进序遵循北极星 §6：自检三关 → Int Rename（D13 是总表「标红但无实验数据」的直接回应）→ Int Dispatch/ROB（D32 done 位预期最高 SDC）→ Int Decode → FP/SIMD（依赖 D62 机制核实=已确认分离，N3）。
**SVE 族（W7.5）与深挖档（W8.6）排在 M5/M6 之间按余力决定，不阻塞主线。**

---

## 6. 算力预算与分批策略（诚实账）

| 项 | 量级 | 估算 |
|---|---|---|
| formal | 226 格 × 2000 = 452,000 次 | 单次 ≤60s（负载裁剪纪律 A7）→ ≈ 7,500 小时纯串行 |
| pilot | 226 格 × 4 档 × 20 = 18,080 次 | ≈ 300 小时 |
| 事件覆盖余量 | 27 格按密度倒推，可能高于 2000 次运行 | 密度表（W0.3）出数后重估 |
| L2/L1 二遍重放 | ≈ 非 Masked 样本比例 × 带.trace 减速 | M1 实测减速比后重估 |

**策略**：① 4–8 并行槽（内存实测定上限）；② **M3 gate**：Int Rename 闭环后用实测吞吐重估全量工期，向用户报告再决定后续批次规模；③ 深挖档仅论文级关键格；④ 事件覆盖不足的格优先换自设探针负载（北极星 02 的既定方案），不硬烧空转运行。

---

## 7. 风险登记册

| # | 风险 | 缓解 |
|---|---|---|
| R1 | Decode re-decode 机制不可行（StaticInst 缓存/共享语义） | W6.0 spike 前置；降级路径=DynInst 级 patch，文档注明偏差 |
| R2 | ROB done 位置位点/FreeList 指针结构无干净 hook | W5.4/W4.7 前置 mini-spike；必要时小改 gem5 原生文件（先例：22 个注入器的 hook patch） |
| R3 | 算力超预算 | §6 分批 + M3 gate + 负载裁剪 |
| R4 | 事件密度不足（如 ROB>80% 在 CoreMark 罕见） | W1.5 探针核达标验证前置；密度表先行 |
| R5 | D55 路由行与 gem5 FUPool 机制不匹配 | honest-reject 记录（北极星已标探索性/置信度低，不算失败） |
| R6 | gem5 依赖检查实际形态 ≠ TC'23 描述 | W8.1 三关自检直接检验——这正是它的用途 |
| R7 | 两轨道（鲲鹏 n=384 / OoO n=2000）口径混淆 | C3 family 隔离 + campaign_id 一律 `ooo_` 前缀 + 结果目录独立 + 文档口径注记 |
| R8 | 45 万次中批量 OOM/机器故障屠批 | 批次断点续跑（campaign 已有 per-rep manifest 产物）+ 资源纪律 |
| R9 | trace 二遍减速比失控 | M1 实测；若 >5× 则只对 SDC 子集重放（Crash 用终态分类） |

---

## 8. 与鲲鹏 920 轨道的隔离纪律

1. `C3-OOO` 独立 config family；**不修改 C0/C2 默认参数**。
2. OoO 轨道 campaign_id 一律 `ooo_` 前缀；artifacts/runs 目录自然分离。
3. manifest v3 为 additive（v2 字段不动），`manifest_validate.py` 向后兼容。
4. 引用结果时必须带轨道标签：鲲鹏轨道（n=384，kp920_proxy）≠ OoO 轨道（n=2000，ooo_proxy）。
5. 本计划不改写鲲鹏轨道既有结论与文档。

---

## 9. 度量与回填闭环

```
E001–E226 (05-expanded-matrix.csv)
   │  W3.1/W3.2 编排（manifest 带 experiment_cell_id）
   ▼
runs/ooo_<cid>/cNNNN/ + artifacts/ooo_<cid>/   （L0-L4 原始产物）
   │  W3.3 backfill_expanded_matrix.py
   ▼
05-expanded-matrix.csv 7 结果列回填（+Wilson CI）
   │  W9.2
   ▼
元分析报告（三问 + 排序 + 前兆库 + 增量对照）
```

回填纪律：只回填 `n_valid` 达标的格；事件覆盖格同时记录覆盖数；pilot 数据永不入结果列；每格可从 CSV 值追溯至 artifacts（E 编号贯穿）。

---

## 10. 执行纪律（对齐 CLAUDE.md）

1. **one-patch-per-unit**：WBS 每个 Wx.y 编号 = 一个 commit；不捆绑、不并行批混。
2. **100% 真实验证**：每 patch 三件套（构建零警告 / 定向功能真机输出为证 / reg_chain golden 回归）；跑批结果 commit 附 n_valid 与 CI。
3. **自动推送**：fi-ding 或专属 feature 分支，verify → commit → push；不推 main。
4. **两级计划体系**：本文件=总纲（What/Why/排序）；每个 W 包启动时 `superpowers:writing-plans` 写 `docs/superpowers/plans/YYYY-MM-DD-ooo-<W包>.md`（逐补丁 How + 验证命令 + checkbox）。
5. **计划变更**：范围变化先改本文件（或其引用的北极星文档若涉设计口径），再动代码。
