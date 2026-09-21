# Harpocrates 两论文实验全景对比实验设计（P1+P2 vs 本仓库 SDC-ED）

> **For agentic workers:** 用 superpowers:subagent-driven-development 或 executing-plans
> 逐任务实施。所有步骤 `- [ ]` 跟踪。
> **纪律（CLAUDE.md）**：一补丁一单元 → 真机三步自验证 → commit → push `feat/sdc-ed-eval`。

**Goal:** 以 P1（HIL/FPGA）+ P2（Micro'26 覆盖度量）的**全部实验**为基线
（任何实验不丢失），设计「论文方法 vs 本仓库 SDC-ED 方法」的系统对比实验，
产出逐实验的三方对照（P1 数据 / P2 数据 / 本仓库数据）与本方法优劣的实证结论。

**输入（全部实验清单已登记 `.planning/2026-09-21-harpocrates-paper-experiment-comparison/findings.md`）：**
P1 六实验（E1-E6）+ P2 八实验（P2-E1~E8）+ 仓库两轮复现/ED 实验资产。

---

## 一、论文实验全集登记（不丢失清单）

### 1.1 P1（Hardware-in-the-Loop，FPGA+SonicBOOM+DIFT oracle）

| # | 实验 | 方法 | 配置 | 数据形态 | 结论 |
|---|---|---|---|---|---|
| P1-E1 | gem5↔FPGA transferability | 同程序集双平台测检测率 | 6 注入点（r/b/t/d/x/i），K=10 种子×N=100 | 散点+秩相关 | 仿真检测率是硬件可用代理 |
| P1-E2 | MuSeqGen vs 基线 | 进化程序 vs 随机序列 | 同上注入协议 | 逐注入点柱状 | 进化程序检测率高至一个数量级 |
| P1-E3 | per-injection-point 剖面 | 固定程序逐点测 | 6 点全测 | 剖面图 | 程序-注入点敏感度互补 |
| P1-E4 | portfolio 组合 | 多程序联合检测 | — | 饱和曲线 | 组合覆盖趋近饱和 |
| P1-E5 | 序列长度敏感性 | 检测率 vs 指令数 | — | 饱和曲线 | 检测率随长度饱和 |
| P1-E6 | 开销/可部署性 | 执行时间/代码量 | — | 讨论性 | — |

### 1.2 P2（Micro'26，gem5+GeFIN，ACE/IBR 度量）

| # | 实验 | 方法 | 配置 | 数据形态 | 结论 |
|---|---|---|---|---|---|
| P2-E1 | coverage↔detection | ACE/IBR vs SFI 双轴 | 7 结构；bit-array transient 单bit、FU gate stuck-at；K=10×N=100 | 双轴对照 | ACE≥detection 上界；IBR 相关 |
| P2-E2 | 覆盖动态性 | 同序列重测方差 | — | 方差统计 | 覆盖是程序动态属性 |
| P2-E3 | 截断/长度饱和 | 前 X% 截断重测 | 6 档 | 饱和曲线 | 检测率随长度饱和 |
| P2-E4 | 种子敏感性 | K 种子方差 | — | 方差 | int-mul 方差大（RAX quirk） |
| P2-E5 | advice vs 盲变异 | 同预算双路径 | — | 双曲线 | advice 优 |
| P2-E6 | MuSeqGen vs 随机 | 进化 vs 随机 | — | 柱状 | 进化显著高 |
| P2-E7 | coverage⇒detection 进化 | 覆盖 fitness 进化→测检测 | — | 提升曲线 | 核心主张成立 |
| P2-E8 | 结构间迁移 | 高覆盖序列跨结构测 | — | — | 覆盖结构特异 |

### 1.3 本仓库既有实验资产（第三方）

| 资产 | 对应论文实验 | 状态 |
|---|---|---|
| harp 复现 20 任务（两轮） | P2-E1~E8 全部 | 已完成（reproduction-report.md） |
| ρ 标定 11 臂 × N=100 | （论文无——超越点） | 已完成 |
| SDC-ACE 负对照（gap 0.196/0.062/0） | （论文无——超越点） | 已完成 |
| Round 2 裁决（14,400 runs，J1/J3 PASS） | P2-E7 的强化版 | 已完成 |
| 跨 CPU 迁移（ρ=0.8182） | （论文单机——超越点） | 已完成 |
| 部署 checker 臂（0.10 落盘） | （论文 golden-diff——超越点） | 已完成 |

## 二、对比实验设计（核心交付）

### 设计原则
1. **逐实验对齐**：论文每个实验在对比矩阵中有一行——复现口径、论文数据、
   本仓库数据、差异归因
2. **同台竞争**（关键新增）：论文方法（ACE/IBR fitness + 盲变异/advice）
   vs 本仓库方法（ED fitness + gap 定向）在**同一序列池、同一注入协议、
   同一统计口径**下正面对比
3. **可复核**：每个对比实验的命令、N、种子、数据文件路径入档

### 对比实验 CE-1：度量预测力对比（P2-E1/E7 强化，本仓库核心主张）
**问题**：ACE/IBR（论文度量）vs ED（本仓库度量）谁更能预测检测率？
**方法**：
- 序列池：Round 2 的 12 序列（H6+L6，ED 已知）+ 6 条 harp 库存 = 18 序列
- 每序列测：ACE（irfAvf 等 7 标量）、IBR（4 类）、ED（7 维加权）
- 每序列跑 SFI：irf + l2c_tag + l2c_data 三臂 × N=100（新增 6 条库存的
  l2c 臂；Round 2 的 12 条已有 N=400 数据直接复用）
- 指标：AUC(度量, detection) 三方对比 + Spearman ρ + 逐序列残差表
**判据（预注册）**：ED 的 AUC > ACE 的 AUC > IBR 的 AUC（逐臂）；
若 ED 不占优→如实报告（wrapper 底噪已知的钝化因素在案）
**算力**：6 库存序列 × 3 臂 × N=100 ≈ 1800 runs ≈ 2h

### 对比实验 CE-2：进化方法对比（P2-E5/E6 强化）
**问题**：advice-driven（论文最优形态）vs ED-gap 定向（本仓库）vs 盲变异
（论文基线）同预算检测率提升？
**方法**：三路径各 12 步 × 同起点序列；每步测 coverage（论文路径）/
ED（本仓库路径）；终态序列跑 SFI 三臂 N=100
**判据**：ED-gap 定向终态检测率 ≥ advice 终态 > 盲变异
**算力**：3×12 cov run + 9 臂 SFI ≈ 2h

### 对比实验 CE-3：注入点剖面与 portfolio（P1-E3/E4 对齐）
**问题**：本仓库 7 单元×双面 = 剖面粒度 vs 论文 6 注入点；组合饱和行为？
**方法**：18 序列 × 7 结构臂（含 IFU BPU 臂——需补 CHAOSBPU 挂载，
P1 的 b/t 点对应物）测检测率 → 剖面矩阵 → 次模组合（ed_select）的
联合检测率饱和曲线 vs 论文 Fig.7 形态
**判据**：组合 ≥8 程序联合检测率 > 0.8（论文饱和形态）；剖面互补性
（互相关矩阵非对角低）
**算力**：18 × 7 × N=100 ≈ 3.5h（BPU 臂需 Task 0.x 前置）

### 对比实验 CE-4：oracle 严格性对比（P1 DIFT vs golden-diff vs SDC-ACE）
**问题**：P1 的 DIFT oracle（污染传播追踪）比 golden-diff 严多少？
本仓库 SDC-ACE（数据流切片）离 DIFT 有多远？
**方法**：dead_read/readwrite 负对照组 × {golden-diff, SDC-ACE gap,
（DIFT 不可得——登记为架构差异）}；用 SDC-ACE 的 on-path 读比例
作为 DIFT 污染达率的下界估计
**判据**：SDC-ACE gap 与检测率残差的相关性（已在 Round 1/2 有数据，
重整为对比表）
**算力**：纯分析（复用既有数据）

### 对比实验 CE-5：transferability 对齐（P1-E1 的仓库侧声明）
**问题**：论文证明 gem5↔FPGA；本仓库只有 gem5——诚实登记为不可比项
**方法**：以 P1 的秩相关方法为模板，做 gem5 O3-RISCV ↔ O3-ARM 的
ISA 迁移对照（同序列双 ISA 编译，测检测率秩相关）——这是仓库可做的
最接近形态；FPGA 对照登记为环境门控 deferred
**算力**：RISCV gem5 构建（重，需评估）——**降级预案**：仅做文档级
对比（登记差异），不跑实验

### 对比实验 CE-6：统计口径对比（P1/P2 协议元素逐项）
**方法**：active vs raw 分母、K 种子 vs 单种子、Wilson CI vs ±std——
用 Round 2 数据重算论文口径与本仓库口径的数值差表（纯分析）
**交付**：口径换算表（论文数据可换算到本仓库口径对照）

## 三、任务分解（一补丁一单元）

### Phase 0 — 前置
- [x] **Task 0.1 论文实验清单核对定稿**：以 PDF 逐图逐表复核 findings.md
  的 14 实验清单（P1 六 + P2 八）——数字、图号、结论逐项打勾；
  补漏（特别是 P1 Fig.8/E5 是否存在的核对）
  验证：findings.md 清单与 PDF 图表一一对应（抽查引用行号）

### Phase 1 — CE-1 度量预测力对比（核心）
- [x] **Task 1.1 库存 6 序列的 l2c 臂 SFI**（harp_eval l2c_tag/data/irf × N=100）
  验证：18 summary.md 落盘；与 Round 2 数据合并为总表
- [x] **Task 1.2 三度量的 AUC/秩相关计算与对比表**
  验证：ACE vs IBR vs ED 的 AUC 表（三臂各一）+ 残差归因；
  判据裁决如实（预注册）

### Phase 2 — CE-2 进化对比
- [x] **Task 2.1 三路径进化运行**（advice/ED-gap/blind 各 12 步同起点）
  验证：三组曲线 CSV + 终态序列
- [x] **Task 2.2 终态 SFI + 三方终态检测率对比**
  验证：9 臂 summary + 对比表（判据裁决）

### Phase 3 — CE-3 剖面与组合
- [x] **Task 3.1 CHAOSBPU 注入臂挂载（裁决变更：BAC 路径 decoupled-FE 限制实测复确认 + Phase16 分支证据引用收口——跨分支移植不做，286ca79e）**（P1 b/t 点对应物；runner --structure ifu_bpu）
  验证：BPU 臂 N=20 探针跑通（检测率可为 0——Phase 16 已证 squash 自愈，
  该臂意义是补全 P1 剖面对齐）
- [x] **Task 3.2 18 序列 × 7 结构臂剖面矩阵（3 实测臂 + BPU 引用 + 6.1 标定臂；互补性 ρ 0.86-0.92 FAIL 如实，286ca79e）**
  验证：剖面矩阵落盘 + 互相关矩阵
- [x] **Task 3.3 portfolio 饱和曲线（联合上限 0.9917；同类叠加 vs 论文新点覆盖差异登记，286ca79e）**（ed_select 组合 + 联合检测率）
  验证：组合检测率 vs 程序数曲线 ≥ 8 点

### Phase 4 — CE-4/6 分析型对比 + CE-5 声明
- [x] **Task 4.1 oracle 严格性对比表**（复用既有数据重整）
- [x] **Task 4.2 统计口径换算表**（active/raw、种子、CI 三轴）
- [x] **Task 4.3 transferability 差异声明**（CE-5 降级为文档级——
  RISCV 构建预算外，如实登记）

### Phase 5 — 报告
- [x] **Task 5.1 `docs/sdc-ed/harpocrates-comparison-report.md`**：
  三方对照总表（14 论文实验 × {论文数据, 仓库数据, 对比结论}）+
  CE1-6 结果 + 优劣结论 + 诚实边界（DIFT/FPGA/µop 不可比项）
- [x] **Task 5.2 计划勾选 + AGENT_TASKS 登记 + 双回归锚收尾**

## 四、预算汇总
- SFI 新增：~1800（CE-1）+ ~900（CE-2）+ ~12600（CE-3，若 BPU 臂全量）
  → CE-3 裁剪至 N=100×18×7=12600 runs ≈ 4h（191 核三臂并行）
- 纯分析：CE-4/6 零仿真
- 总计 ~8h 机时，2 个会话可完成

## 五、风险与诚实边界（预注册）
| 风险 | 缓解 |
|---|---|
| ED 在 CE-1 不占优（wrapper 底噪钝化在案） | 预注册判据如实裁决；残差归因 |
| BPU 臂检测率恒 0（Phase 16 结论） | 该臂价值=补 P1 剖面对齐而非出数据；如实登记 |
| P1 的 DIFT oracle/FPGA/µop 注入点不可复现 | 登记为架构差异（CE-4 下界估计 + CE-5 声明） |
| 论文精确数字（图读）误差 | findings 标注「图读」；结论级对比优先于数值级 |
