# 竞争矩阵：docs/papers/ref 30 篇 vs 本工作

> 目的：逐篇定位 `docs/papers/ref/` 中的顶会/期刊论文，论证本工作（ooo 轨道 + LSU 轨道合并）的差异化位置。
> 阅读方式：28 篇 PDF 经 pypdf 文本提取逐篇实读（前 3-4 页 + 针对性全文核查）；**CHAOS.docx 与 Orthrus.docx 为二进制 Word 未读，如实标注，不作猜测**。
> 我方资产（用于"它不做什么"判定）：gem5 v25.1.0.1 AArch64 微架构级**结构化**故障注入——六类故障模型（单/双 bit、卡死、合法换值、时序、保护面）× **20+ 注入器**（OoO 核：PRF/RAT/FreeList/ROB/IQ/Exec/FPU/BPU/Decode/RAS/LSQFwd/L1DFwd/AddrPath/ExMon/Probe；存储：L1D/L2/DRAM/CHAOSCache/CHAOSPrefetch；ARM 特有：TLB/SysReg/PTW）× LSU 68 模型 337 格预注册网格 + ooo 轨道 149 campaign 正式结果 × **事件归一触发**（F0-F6，eligible-event 分母）× **L0-L5 错误生命周期观测**（L1 影子比对/L2 请求配对/L4 commit 首分歧/L5 守恒分类）× **FS 内核态**（checkpoint 流水线，panic/Oops 退出事件分类）× 多核 × **保护感知三层对照**（none/SECDED/poison/post-check）× **自适应统计**（试跑 30→筛查 385→Wilson 95% 半宽 ≤2pp 停止、按运行聚类）× 双文献锚点复现（TC'22/TC'23）。

---

## 一、gem5 FI 工具与 AVF 方法类（10 篇）

| 论文 | 会议/年 | 它做什么 | 它不做什么（我方对应资产） |
|---|---|---|---|
| GemFI | DSN 2014 | gem5 FS 行为级注入（架构寄存器/指令/PC/访存），DMTCP 加速；统计规范（2500/组） | 无深微架构结构（PRF/RAT/ROB/LSQ）、无 TLB/SysReg、非 ARM、无传播链、无保护对照、固定 n 无自适应 |
| gem5-MARVEL | HPCA 2024 | 多 ISA（x86/ARM/RISC-V）+DSA 微架构 SFI，AVF+HVF | 无传播链（终点+分层归因非逐步）、无保护开/关臂、无自适应统计、无事件归一触发 |
| CHAOS（直系底座） | arXiv 2026-02 | 三件套注入器（Reg/Cache/Mem）+ 五类终点分类 | **无 OoO 内部结构、无 TLB/SysReg/PTW、无 eligible-event 触发、无 L0-L5、无保护对照**——本工作在其上扩展全部六个维度 |
| MaFIN/GeFIN 差分研究 | IISWC 2015 | 三配置差分注入全部存储阵列 | 只报终点、单核、无保护、无 CI |
| MeRLiN | ISCA 2017 | 等价类分组注入加速 2-3 个量级；统计最强（60K 按置信定容） | x86、无传播链（区间画像最接近但为分析式）、无保护臂、无自适应停止 |
| ACE（Measuring AVF） | IEEE Micro 2003 | ACE 位分析，AVF 上界（IA64） | 纯分析无注入、无 OS、无传播、无统计 |
| First-Order AVF | ISPASS 2012 | 解析模型估 ROB/IQ/LQ/SQ AVF | 同上 |
| Systematic AVF Methodology | MICRO 2003 | AVF 定义+预算级保护权衡 | 同上 |
| Address-Based AVF | ISCA 2005 | D-cache/DTLB/store buffer 的 ACE 生命周期 + flush/scrub 缓解评估 | 分析法；**DTLB 有上界分析但无 FS 注入实测**（我方 T 系格补此空白） |
| DelayAVF | MICRO 2024 | 时序故障 DelayAVF 两步法（RISC-V RTL） | RTL 层、无 FS、无 CI；我方时序类故障模型（S11/C12）在微架构层可注入 |

**共性缺口**：传播链全缺（只报终点）；保护感知零实验臂；统计纪律两极（确定性无 CI 或固定 n）；无一篇同时 ARM64+FS+OoO 内部+TLB+多核+六类故障模型。

## 二、产线 SDC 检测/表征类（8 篇）

| 论文 | 会议/年 | 它做什么 | 它不做什么 |
|---|---|---|---|
| PinDrop | HPCA 2026 | Meta 产线 4 年 SDC 表征（数百万台） | 自认"lack of visibility into underlying hardware"——最细 core 级；无 CI；x86 |
| Hardware Sentinel | ASPLOS 2025 | 崩溃症状聚类关联 SDC 检测 | 根因外包厂商；x86；无机理 |
| SEVI | ASPLOS 2026 | 产线圈定+逐指令长测定位 FMA | 到 lane/位模式级但**到不了单元内位级因果**；x86 |
| Fleetscanner/Ripple | arXiv 2022 | 两条产线 SDC 测试策略 | 定性轶事式；无速率区间 |
| SiliFuzz | arXiv 2022 | 模拟器差分 fuzz 语料回放产线 | CPU 黑盒；纯用户态；x86 |
| PMC-SpMV 检测 | ~2025 短文 | 数据级噪声注入+PMC 分类 | 应用层注入非硬件故障；n 极小 |
| Vega（aging SDC） | ASPLOS 2024 | 门级老化模型→error lifting 测试生成 | 锁死单一老化时序模型、两单元、RISC-V 网表；与负载内传播断开 |
| SDC μArch Perspectives（**TC'23 锚点**） | IEEE TC 2023 | gem5 FS 单 bit 注入 A72 的 11 结构 SDC 归幅 | **单 bit 一类故障模型、无保护对照、无 CI、单核**——我方六类×20+ 注入器×L0-L5×保护臂×Wilson 恰补其每一维；本仓 TC'23 锚点（LQ/SQ SDC=0）即复现此文 |

**共性缺口**：六篇产线类只看终点症状（分母=机器/核/测试轮），无法回答"哪个单元、哪一位、为什么静默"；ARM 服务器 SDC 因果链公开文献基本未测。**正确用法**：产线数字（~0.035% 机器级终生 SDC 率、FMA 主导、单核/lane 局域性）作为现实发生率先验锚点，**不与**微架构因果分解数字混算（分母与观测层级不同）。

## 三、跨层传播与防御类（10 篇）

| 论文 | 会议/年 | 它做什么 | 它不做什么 |
|---|---|---|---|
| Demystifying System Vulnerability Stack | ISCA 2021 | GeFIN 三层（微架构/架构/软件）AVF 对比，证上层近似方向相反 | 传播分解为层间指标非逐层站点记录；保护仅 SWFT 单案例 |
| From Gates to SDCs | DATE 2025 | 门级 FU 模型嵌入 gem5，两级传播量化 | x86；无保护；最细仅 FU 输出 BER |
| Failures Across ISAs | ITC 2023 | 三 ISA 四结构 SDC AVF（1000/部件，4%@99%） | 无传播链、无保护、无 FS 口径 |
| Soft Errors on Arm（TC'22 锚点系） | IEEE TC 2022 | 中子束实测 A5/A9 × gem5 交叉验证 | 无保护对照；束测侧只终点 |
| ETS'24 综述 | ETS 2024 | 早期预测×fleet 实测互证综述 | 综述聚合级 |
| Harpocrates（ISCA'24 + IEEE Micro'26 扩展） | 2024/2026 | 程序生成最大化目标结构检出（gem5 硬件在环） | x86、无 FS、coverage 代理非传播链、评检测能力非逃逸分解 |
| ITHICA | ACM 2026 | LLVM 插桩功能测试，3000+ 台实机 +39% 检出 | 软件层；实机不可控；无微架构因果 |
| H-AVF（Applying AVA to Hard Faults） | DSN-era 2004, 2p | 硬故障容忍方案的 H-AVF+成本合成分 | 2 页短文；ECC/TMR 设计权衡，无运行注入 |
| SDC: Stealthy Saboteurs | Athens+Meta tutorial, 7p | SDC 教程综述（fleet+软件冗余视角） | 综述；无新测量 |
| CHAOS.docx / Orthrus.docx | — | **未读（二进制 Word）** | 如实标注 |

---

## 四、汇总差异声明（我方独有组合，逐条对应上表缺口）

1. **错误生命周期全链（L0-L5）**：attempted/eligible/activated 漏斗 → L1 影子比对微架构偏差 → L2 请求配对 → L4 commit 首分歧 → L5 守恒分类。30 篇中最接近的（MeRLiN 区间画像、DelayAVF 两步归因、DATE'25 两级传播）均为分析式或截断链——**无人做注入运行时的逐层观测**。
2. **结构化六类故障模型 × 机理级注入器**：合法换值/时序/卡死/保护面专门测试"检查之外的静默路径"（TC'23 实证：随机翻转 LQ/SQ SDC=0，而 fwd_source_sub 合法换值 37.6% SDC）——现有工作 90% 只有 bit-flip 一类。
3. **保护感知实验臂与逃逸分解**：none/SECDED/poison/post-check 对照给出风险反转（L1D raw 97.7% → +SECDED 0% → post-check 90.9%）——30 篇中保护要么缺席、要么停在检出率。
4. **FS 内核态 + ARM 特有结构**：TLB/SysReg/PTW 注入 + checkpoint 流水线 + panic/Oops 分类——跨层类仅 ISCA'21/DATE'25 含 OS 且均为 x86；**ARM64 FS 微架构因果分解公开空白**。
5. **统计纪律**：预注册 337 格网格 + 双锚点复现门（TC'22/TC'23）+ 自适应三阶段（30→385→Wilson≤2pp）+ 按运行聚类 + blocked 不伪造——仅 ITC'23（4%@99%）与 GemFI（2500/组）有正式样本量论证，无自适应停止。
6. **多核**：O 系原子/同步故障面 + litmus——工具类无一涉及 SMP 语义注入。

## 五、数字使用纪律

- 产线类数字（PinDrop/SEVI 等）= 现实发生率先验；我方数字 = 条件因果分解（P_SDC|activated, 指定单元/模型/负载）。**两者分母与层级不同，任何表格中并排出现时必须分行分列标注口径，永不换算比较。**
- TC'23/TC'22 锚点复现是工具正确性证明（M2/M3 门），不是结果抄袭——复现数字进"锚点表"，新结论进"网格结果表"，两表分离。
