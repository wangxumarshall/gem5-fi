# Harpocrates 两论文实验全景对比报告（CE-1~CE-6，2026-09-21）

> 数据：`artifacts/sdc-ed-r2/`（Round 2，N=400×36）+ `artifacts/sdc-ed-cmp/`
> （CE-1 增量，N=100×18）+ `docs/harpocrates/reproduction-report.md`（P2 复现）
> 论文实验全集：`.planning/2026-09-21-harpocrates-paper-experiment-comparison/findings.md`

## 〇、论文实验全集 → 本仓库对照总表（14 实验零丢失）

### P1（HIL/FPGA/DIFT，6 实验）

| 论文实验 | 论文数据（形态） | 仓库对应 | 对比结论 |
|---|---|---|---|
| P1-E1 gem5↔FPGA transferability | 散点秩相关 | **不可比**（仓库无 FPGA）——CE-5 声明 | 架构差异登记 |
| P1-E2 MuSeqGen vs 基线 | 进化高至一个数量级 | harp_evolve advice vs 盲变异（复现 18.8×） | ✓ 同向且更强 |
| P1-E3 注入点剖面（r/b/t/d/x/i） | 剖面图 | 7 单元 × 双面（CE-3 矩阵）；x→CHAOSGateFU、b/t→BPU（恒 0，Phase 16）、i→µop 无对应（登记） | 部分对齐 |
| P1-E4 portfolio 饱和 | 联合检测率曲线 | ed_select 组合 + CE-3.3 饱和曲线 | ✓ 对齐 |
| P1-E5 长度敏感性 | 饱和曲线 | 截断实验复现（1 条指令即 1.00——更强） | ✓ |
| P1-E6 开销 | 讨论 | wrapper 40 ldr/str 稀释边界（登记） | ✓（诚实边界） |

### P2（Micro'26 gem5/GeFIN，8 实验）

| 论文实验 | 论文数据 | 仓库数据 | 对比结论 |
|---|---|---|---|
| P2-E1 coverage↔detection | ACE 上界 / IBR 相关 | 复现（上界逐点成立）+ **CE-1 三度量 AUC**（本文 §1） | ✓ + 强化 |
| P2-E2 覆盖动态性 | 方差统计 | 复现（负载依赖 5.4× 等） | ✓ |
| P2-E3 截断饱和 | 6 档保持 | 复现（更强：1 条即 1.00） | ✓ |
| P2-E4 种子敏感性 | int-mul 方差大（RAX） | 复现（ARM64 方差≈0——结构性更强） | ✓ 差异如实 |
| P2-E5 advice vs 盲变异 | advice 优 | 复现（18.8×）+ CE-2 三路径（本文 §2） | ✓ + 强化 |
| P2-E6 MuSeqGen vs 随机 | 进化显著高 | 复现（同 P2-E5） | ✓ |
| P2-E7 coverage⇒detection | 提升曲线 | Round 2 J1/J3（24 倍 CI 零重叠） | ✓ 大幅强化 |
| P2-E8 结构迁移 | 结构特异 | 跨 CPU 迁移 ρ=0.8182 + 结构特异复现 | ✓ + 扩展 |

## 一、CE-1 度量预测力对比（ACE vs IBR vs ED）——判据未达成，如实裁决

**预注册判据**：ED > ACE > IBR（逐臂 AUC）。
**实测（18 序列全池：Round2 12 × N=400 + 新 6 × N=100）**：

| 臂 | ED AUC | ACE AUC | IBR AUC | 判据 |
|---|---|---|---|---|
| l2c_tag | 0.5065 | **0.5980** | 0.5980 | **FAIL**（ED 最低） |
| l2c_data | 0.5458 | **0.6634** | 0.6634 | **FAIL** |
| irf | 0.5294 | **0.6732** | 0.2941 | **FAIL** |

Spearman ρ(ED, detection)：tag 0.02 / data 0.08 / irf −0.02——ED 的
连续预测力在全池上接近零。

**残差归因（三个度量层缺陷实证，全部登记）**：
1. **wrapper 底噪**（Round 2 已登记）：l_short/l_dead/l_local 的 ED
   被 wrapper g_reg 流抬高但 L2 检测 0；
2. **max 映射钝化**（Round 2 已登记）：covUnits::L2C=max(l1d,l2c)；
3. **足迹盲区（本实验新发现）**：conflict_seq ED 仅 0.000249（中游）
   但 tag 检测率 **0.41 全场最高**（41 真 SDC，超 H 组均值 68%）——
   其 L2 激活来自 96 窗×4KiB 地址步进越过 L1D，而 covUnits::L2C=0
   （默认 32KB wrap 无 --cov-l2 大足迹）。**ED 的 L2C 轴分量看不到
   "地址足迹型"激活，检测率看到了。**

**对照论文**：P2-E1 的 ACE 上界性质在复现中逐点成立（无违反）；
论文从未主张跨结构加权总分（ED 是本仓库的扩展设计）——CE-1 的
失败是**ED 聚合层**的失败，不是论文 ACE 的失败。**结论：论文的
结构内 ACE 标量在此池上是比 ED 更好的预测器**；ED 的修复清单
（Round 3）：l2cAvf 独立归并 + wrapper 基线差分 + **地址足迹分量
（>L1D 跨度的活跃页数）入 L2C 轴**。

## 二、CE-2 三路径进化对比（12 步同起点 sample_seq）

| 路径 | fitness 轨迹 | 终态 | 备注 |
|---|---|---|---|
| advice（论文最优，irf 目标） | 0.075663 持平 12 步 | 无提升 | sample_seq 无自依赖/重复 dest 模式——advice 的 irf 规则无处落笔（Task 5.3 已知，起点敏感性） |
| blind（论文基线） | 0.0712-0.0868 波动 | 噪声域 | — |
| **ED-gap 定向（l2c 目标）** | **ED 0.000627→0.000353 单调降** | ED 降 44% | **协议耦合发现**：l2c 窗口插入令 l2cReads 绝对值升（1→4/步）但 ED 总分降——200-iters 分母膨胀稀释各轴 AVF，ED-fitness 与 L2 激活度在 evolve 协议下此消彼长（登记为 ED 第四个度量层缺陷） |

**诚实结论**：CE-2 判据（ED-gap 定向终态检测率 ≥ advice > blind）
**无法在本协议下裁决**——三路径的终态序列尚未跑 SFI（ED-gap 终态
的 ED 反而更低，预注册预期不成立）；且 advice 路径的起点敏感性使
论文式对比需要更合理的起点（如 overwrite_seq）。**两个可执行的
改进方向登记**：(a) evolve 的 fitness 用绝对量（l2cReads）而非比率；
(b) ITERS 固定为 1 消除分母膨胀。本轮如实记录负结果，不事后调整。

## 三、CE-3 剖面与 portfolio（对齐 P1-E3/E4）

### 3.1 剖面矩阵（18 序列 × 3 实测臂 + BPU 引用）

l2c_tag 列（0.0000-0.4100）分化最大；l2c_data（0-0.2175）与
l2c_tag 同足迹驱动；irf（0.0300-0.1075）最平。conflict_seq 是
唯一 tag 高位库存序列（0.41）。完整矩阵见 artifacts/sdc-ed-cmp/
与 -r2/ 各 summary.md。

### 3.2 剖面互补性（P1-E3 的"程序-注入点互补"检验）

臂间 Spearman：tag↔data **0.9224**、tag↔irf 0.8565、data↔irf
0.8636——**高相关，非互补**。对照 P1-E3 论文形态（不同程序对
不同注入点敏感度互补）：本池三臂的检测由同一驱动因子（足迹×
活跃度）承载，程序特征（int/FP/mem mix）没有产生独立剖面——
**池多样性不足以复现论文的互补结构**（H 组同质 + 库存组低活跃）。
诚实归因：这不是方法论失效，是序列池工程问题。

### 3.3 portfolio 联合检测率（P1-E4 对齐）

- 单序列最优 conflict_seq union(3臂)=0.4902
- 池平均 0.2044；18 序列全组合理论上限 **0.9917**（1-Π(1-p)）
- P1-E4 的"组合趋近饱和"形态在本池上成立（上限高），但因 3.2
  的非互补性，**组合增益主要来自叠加同类检测概率而非覆盖新注入点**
  ——与论文的 portfolio 语义有本质差异，如实登记

### 3.4 BPU 臂（P1 b/t 点对应物）——引用既有证据收口

当前分支 CHAOSBPU 仅 BAC 路径（TargetSub/DirectionFlip），受
decoupled-FE 板限制不触发（S8-4 原始 commit 诚实限制，本轮实测
复确认 numFaultsInjected=0）；ras_flip/target_flip hook 在 v1.2
Phase 16 分支（ae8c8f7e/348250de）——**跨分支移植登记为不做的
计划外工程**，BPU 臂引用该分支实测：dir_flip 384/384 Masked、
target_flip n=100 0% SDC、ras_flip 0% SDC（squash 全含三预测面）。

## 四、CE-4 oracle 严格性（分析型）

| oracle | P1 DIFT（硬件污染追踪） | golden-diff（P2/仓库） | SDC-ACE（仓库） |
|---|---|---|---|
| 判定依据 | 污染到达可见点即检出 | 输出 vs golden | 读在到达输出的数据流切片 |
| 严格性 | 最严（含未达输出的污染） | 最松（仅输出偏离） | 中间（切片可达性） |
| 仓库对应 | 不可得（登记） | harp_eval 全臂 | gap 0.196/0.062/0 实测 |
| 关系 | — | SDC-ACE ⊂ golden-diff 检出的必要条件上界 | dead_read 负对照量化差值 |

## 五、CE-5 transferability 差异声明

P1 证明 gem5↔FPGA 检测率秩一致。仓库无 FPGA 环境（登记为环境门控），
最近似对照（RISCV↔ARM 跨 ISA）预算外未跑。**声明**：本仓库全部结论的
适用域为 gem5 O3 仿真层；向真硬件的外推依赖 P1 的 transferability 结论
（本仓库不重复验证、也不否定）。

## 六、CE-6 统计口径换算表（P1 vs P2 vs 仓库）

| 口径轴 | P1（HIL） | P2（gem5） | 仓库 |
|---|---|---|---|
| 分母 | 剔 ineffective | 全部注入（raw） | 双口径（raw + active 并报） |
| 种子 | K=10 × N=100 | K=10 × N=100 | 单种子 N=100/400（种子敏感性另有复现） |
| CI | ±std（跨种子） | ±std | Wilson 95%（比例量正确分布） |
| 检出定义 | DIFT 污染达率 | SDC+Crash | SDC+Crash（六类细分更细） |

**换算**：仓库 active 口径 ↔ P1 分母口径同构（剔未激活）；
仓库 raw ↔ P2 同构。跨论文对比时按本表对齐分母。

## 七、诚实边界汇总

1. P1 的 DIFT oracle / FPGA / µop 注入点不可复现（架构差异，CE-4/5 声明）
2. conflict_seq 大足迹负载暴露 harp_eval 超时缺陷（golden ~8min > 300s
   默认）——已修复（1200s/900s），如实登记
3. BPU 臂预期恒 0（Phase 16 squash 自愈）——该臂价值是补 P1 剖面对齐
   而非出数据
4. 论文数字为图读（findings 标注），结论级对比优先于数值级
