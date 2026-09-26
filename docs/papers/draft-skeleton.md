# 论文骨架（draft-skeleton）——ooo × LSU 合并工作

> 依据：`docs/papers/competitive-analysis.md`（30 篇定位）+ `artifacts/ooo-harvest/ooo-results.csv`（149 campaign）+ `artifacts/lsu-trial/`（177 格 trial）+ 鲲鹏轨道 findings.md（v1.1/v1.2 正式结论）。
> 状态标注：[已有数据] = 正式/formal 级在手；[trial] = 试跑级方向性；[M3 待产] = FS TLB 结果待 M3 完成；[M4 待产] = 多核结果待 M4 完成。

## 标题候选

1. **Beyond Endpoints: Structured Fault Injection with Full Error-Lifecycle Observation on a Full-System ARM OoO Core**（主打 L0-L5 + 结构化模型）
2. Where Silent Data Corruptions Come From: A Pre-registered Microarchitectural Causal Decomposition on AArch64（主打因果分解 + 统计纪律）
3. CHAOS-LSU: Six Fault-Model Classes × 20 Injectors × Full-System ARM — Closing the Propagation-Chain Gap in SDC Analysis（工具+方法）

## 摘要框架（8 句）

1. 现实背景：产线 SDC（PinDrop/SEVI）只见症状，无微架构因果。[引用批次二]
2. 学术现状：FI 工具与 AVF 方法只报终点、保护无实验臂、统计两极、ARM64 FS 因果分解空白。[引用批次一/三]
3. 本文：gem5 v25 AArch64 上六类结构化故障模型 × 20+ 机理级注入器（OoO 核/存储层级/TLB/SysReg/PTW/预取器/原子监视器）。
4. 方法三支柱：事件归一触发（F0-F6）；L0-L5 错误生命周期观测（漏斗→影子比对→请求配对→commit 首分歧→守恒分类）；保护感知实验臂。
5. 统计纪律：预注册 337 格网格 + 双锚点复现门（TC'23 LQ/SQ SDC=0、TC'22 DTLB）+ 自适应三阶段采样（30→385→Wilson≤2pp）。
6. 结果骨架：SDC 集中带=数据通路与合法换值路径（L1D 97.7%、错源转发 37.6%、FPU 尾数 83-92%）；保护反转（+SECDED 0% 但 post-check 90.9%——ECC 后通路是盲区）；随机翻转在 LSU 侧全域 SDC=0 而 stuck（F5）是 Crash 集中带。[已有数据]
7. FS 内核态与多核结果。[M3/M4 待产]
8. 贡献声明：首个 ARM64 全系统微架构级错误生命周期分解 + 保护逃逸分解 + 开放工具链。

## 贡献列表（bullet，对应竞争矩阵六缺口）

1. **错误生命周期观测框架（L0-L5）**——首个注入运行时逐层观测（对照：全部 30 篇只报终点或分析式）。
2. **结构化故障模型族**（单/双 bit、卡死、合法换值、时序、保护面）证明"随机翻转 SDC=0 ≠ 单元安全"（TC'23 锚点 0% vs fwd_source_sub 37.6% 同位置）。[已有数据]
3. **保护感知三层对照与逃逸分解**：风险反转图（97.7%→0%→90.9%），ECC-后通路（fill→PRF）盲区定量。[已有数据]
4. **ARM64 全系统内核态注入**（TLB/SysReg/PTW + checkpoint 流水线 + panic/Oops 分类）+ TC'22 锚点复现。[M3 待产]
5. **多核原子/同步故障面**（exclusive monitor/原子序/litmus）。[M4 待产]
6. **方法学纪律**：预注册网格、自适应 Wilson 停止、按运行聚类、负对照（C10/P01-P03）、blocked 不伪造、守恒校验、双文献锚点门。

## 章节-数据映射

| 章节 | 内容 | 数据源 |
|---|---|---|
| §3 方法 | 平台（B0/V110）、注入器族、触发语义、L0-L5、保护模型 | 仓 docs + 源码 |
| §4.1 锚点复现 | TC'23（LQ/SQ 单 bit SDC=0 三腿）、TC'22（DTLB） | artifacts/lsu-trial + [M3 待产] |
| §4.2 网格结果 | 337 格结局谱（SE 177 试跑级 + 筛查档升级） | 11-meta-analysis.md → 升级 |
| §4.3 ooo 全景 | 15 单元 formal（149 campaign）排序：SDC 集中带/零风险带 | ooo-harvest CSV |
| §4.4 保护反转 | L1D/L2/DRAM 三层 + ECC 逻辑故障击穿（85%） | 鲲鹏 findings v1.2 Phase 14 |
| §4.5 FS 内核态 | T 系谱 + AGU 100% DUE 三根因闭环 + TLB regime 反转 | [M3 待产] + method2 formal |
| §4.6 多核 | O 系 + litmus | [M4 待产] |
| §5 相关工作 | 竞争矩阵三类 | competitive-analysis.md |

## 核心图表清单

1. **错误生命周期图**（主打图）：L0 漏斗→L1 偏差→L4 首分歧→L5 终点，逐层衰减率（一次已知注入 vs 无故障参照的真实运行数据）。
2. **保护反转图**：L1D/L2/DRAM × none/SECDED/poison/post-check/ecc-logic-fault 五臂。
3. **337 网格结局热图**：单元×故障模型 → {Masked, SDC, Crash, Timeout} 占比。
4. **锚点复现表**：TC'23 三腿 SDC=0 + TC'22 Crash AVF≈50%（M3 门数字）。
5. **结构化 vs 随机配对图**：S01 vs S04 / C01 vs C05 / P01 vs P03 同位置对比。
6. **ooo×LSU 单元全景排序条形图**（P_SDC 带 Wilson CI，149+177 campaign/格）。
7. F5 stuck vs F0 单发结局对比（Crash 集中带证据）。[trial]

## 目标会议评估

| 会议 | fit | 理由 |
|---|---|---|
| **MICRO / HPCA** | ★★★ | 微架构可靠性主战场；DelayAVF(MICRO'24)/MeRLiN(ISCA'17)/Demystifying(ISCA'21) 先例；需 M3/M4 数据齐 + 筛查档升级 |
| **DSN** | ★★★ | FI 方法+统计纪律正对口（GemFI DSN'14 先例）；对性能微架构深度要求略低，SE+FS 侧数据即可支撑 |
| **ASPLOS** | ★★ | 需更强"系统"故事（跨层+检测联动）；产线类（Sentinel/SEVI）主场 |
| **SC / ICS** | ★ | 若转向 HPC ABFT+PMC 检测线（PMC-SpMV 方向）才 fit |

**建议主投 MICRO/HPCA（微架构因果分解主打），DSN 为备选（方法+统计纪律主打）。**

## 风险与补强（诚实清单）

- M3/M4 未完成前不投——TC'22 锚点与多核是贡献 4/5 的实证。
- 筛查档（≥385 activated/格）至少对 SDC 集中带单元完成，否则 CI 过宽被审稿攻击。
- CHAOS.docx/Orthrus.docx 未读——若为同组在投工作需引用并划界（竞争矩阵已标注未读）。
