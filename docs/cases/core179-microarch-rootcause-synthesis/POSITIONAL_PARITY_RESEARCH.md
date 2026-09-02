# 位置锚定校验（Positional Parity）研究 — 三启示论证与验证原型

> 研究对象：paper_zh.md §6 三大启示。本文档自包含：每条主张标注证据等级
> 【实锤】（本仓库命令可复现）/【强推】（多源文献收敛）/【假设】（待 RTL/厂商验证）。

## 0. 执行摘要
（Task 7 填充）

## 1. 启示一：可观测性必须优先于静默修复（fail-fast / 显性化）

本节论证 paper_zh.md §6.1 的核心主张：**可观测性必须优先于静默修复，绝不能让故障核心的脆弱特征消失在黑盒之中**。论证按"合理性 → 必要性 → 可行性 → 反方与边界"四维展开，每条主张挂证据等级。

### 1.1 合理性：D3 前兆信号是免费的，只是无人消费

本案例的实证链【实锤，paper_zh.md §3.1/§3.4，可由 `grep -h 'WARNING: CPU:' dmesg_*.txt | grep -o 'CPU: [0-9]*' | sort | uniq -c` 在原始日志上复现（DIAGNOSIS_REPORT.md §2）】：12 天窗口内 78 次内核异常事件（73 次 `WARN_RATELIMIT` 级虚假翻译错误 + 5 次致命 Oops）100% 聚集于 CPU 179，其余 191 核零事件；APEI/GHES/BERT 全程零条硬件错误记录——缺陷完全逃逸 RAS 监控。关键在于时间结构：首个 D3 事件（虚假翻译错误告警）早于该开机周期的首个致命崩溃出现。以 08-14 开机周期为例【实锤，vmcore-diagnosis-report-127.0.0.1-2026-08-14-190704.md §2】：第 1 次 spurious 告警出现在 uptime ~29.0 h，致命 Oops 在 ~31.7 h——前兆提前约 2.6 小时；DIAGNOSIS_REPORT.md §6 明确记载 73 次告警"全部先于/伴随致命崩溃"。这些信号由 openEuler 内核 `is_spurious_el1_translation_fault()`（`arch/arm64/mm/fault.c`）通过 `AT S1E1R` 软件重试产生：重试成功即判 spurious 放行并 `WARN_RATELIMIT`——**内核已经付出了产生信号的全部成本，却没有任何消费者把它转化为核隔离动作**。若内核在首个 D3 信号出现时即将"单核聚集的 spurious 翻译错误"转化为核下线动作，则 5 次致命崩溃在原理上全部可避免：首个致命崩溃（08-14 19:07，uptime ~31.7 h）之前同开机已积累 12 次前兆（首次于 ~29.0 h），下线动作本可在此之前执行；而一旦该核被下线并标记，后续四个开机周期（08-17/08-24/08-25×2）的崩溃根本不会发生【强推：因果方向由"前兆早于崩溃 + 同核聚集 + 隔离即阻断"三点支撑，但"隔离可完全避免"未在本机上实验执行，属推断】。

文献收敛恰好构成互补而非矛盾：Meta（Dixit et al., arXiv:2102.11245）与 Google（Hochschild et al., HotOS'21）报告的 mercurial cores/SDC 的共同特征是"出厂测试通过、部署后间歇发作、无架构级 RAS 告警"——即**无前兆**【强推，Dixit et al., "Silent Data Corruptions at Scale", arXiv:2102.11245, 2021（Meta；paper_zh.md 引注作 ATC'21，venue 归属未能核实，见参考文献注）；Hochschild et al., "Cores that don't count", HotOS 2021, DOI 10.1145/3458336.3465297（DBLP 确认）】。HotOS'21 明确观测到"每数千台机器出现若干 mercurial cores"（a few mercurial cores per several thousand machines）量级的缺陷率。正因 fleet 级普遍缺陷是"无前兆"的，**有前兆的缺陷子类（本案例 D3 类）是稀缺的免费信号源**，其被动遥测的边际成本为零——信号已在日志里，缺的只是消费策略。这与 10x-escapes 论文（Mitra et al., arXiv:2508.01786）的系统健康与取证（system health and forensics）论点收敛：Google 报告 49% 的缺陷机器由"系统健康与取证"信号（kernel crash、hang、异常进程崩溃等）事后检出，且其 CCKC（Core-Concentrated Kernel Crashes）启发式——"单物理核上 ≥80% 的内核崩溃、≥5 次崩溃、30 天窗口内 ≥3 个不同栈顶符号"——与本案例"5 次崩溃全在 CPU 179、跨越互不相关子系统"的特征完全同构【强推，arXiv:2508.01786 Observation 5/Table 4 与 §3.2.3】。

### 1.2 必要性：静默修复掩盖缺陷，RAS 兜底不可行

反证法【强推】：设系统依赖静默修复（如 ECC 单比特纠正）消化间歇缺陷。被纠正的错误不产生任何架构可见信号，缺陷核因此继续留存于 fleet；同一物理缺陷在高 AVF 通路上的后续触发（本案例 D1：加载返回数据被字节通道偏移污染）没有任何 ECC 纠正机会——因为汉明距离为零的结构性错位对端到端 ECC 不可见（paper_zh.md §6.2），且本案例五次致命崩溃的数据通路本就未被 ECC 覆盖【实锤，paper_zh.md §2.1/§3.1：RAS 零记录即含"未被覆盖"与"未被检查"两种可能，二者对系统软件同样意味着零信号】。结局是：缺陷核从"可观测的软信号阶段"（D3）沉默滑入"不可观测的硬失效阶段"（D1/D2 致命崩溃），期间它还在静默处理业务数据——被撕裂而未致死的加载值（如本案例 73 次告警中被 extable 吞掉的那类窗口）存在污染业务数据的风险面【实锤，vmcore-diagnosis-report-127.0.0.1-2026-08-14-190704.md §7："不排除业务数据已被静默破坏的风险面"】。

工业数据使"依赖 RAS 兜底"进一步不可行【强推，Mitra et al., arXiv:2508.01786】：Google 估计测试逃逸造成约 0.5%（5,000 DPM）的芯片被换，而工业目标为 100–500 DPM——**实际逃逸率超出工业目标至少一个数量级（10×）**；其中导致 SDC 的逃逸芯片约 1,000 DPM。该论文 Observation 5 显示多数缺陷机器是部署后才检出的（其中 system health and forensics 途径 49%、在线/离线测试 29%、用户级检测 10%），且其引言明确指出大规模分布式系统常假设的 fail-stop 故障模型（硬件错误立即以崩溃/挂起显性化）"已不成立"。结论：既然逃逸缺陷系统性存在且不 fail-stop，系统软件层就必须自己把沉默信号显性化——这正是 fail-fast 的必要性所在。ISO 26262 的功能安全哲学从另一端收敛同一原则：其 safe state 定义为"失效情形下不带不合理风险的运行模式"（operating mode, in case of a failure, of an item without an unreasonable level of risk, ISO 26262-1:2018 定义 3.131），即故障反应的目标是进入受控的显性状态而非维持表面正常【强推，ISO 26262-1:2018；转引自 Stolte et al., IEEE TIV 2022, DOI 10.1109/TIV.2021.3129933】。fail-silent（停止输出、静默吞错）在功能安全术语中只被视为子组件级的一种可能反应，绝不是整机级的容许稳态。

### 1.3 可行性：分层成本清单——改动小、机制已有、边界清晰

**(a) D3 遥测消费：纯软件、近零边际成本**【实锤，挂接点已在生产内核存在】。信号产生端已就绪：openEuler `is_spurious_el1_translation_fault()` 的重试路径 + `WARN_RATELIMIT` 打印（paper_zh.md §6.1）。需要的增量只是一个用户态或内核态消费器：按 CPU 聚合"spurious 翻译错误"计数、与核间基线对比、超阈值即触发隔离动作。本仓库文档已给出可直接落地的命令级方案【实锤，vmcore-diagnosis-report §9：`echo 0 > /sys/devices/system/cpu/cpu179/online`，或内核参数 `maxcpus`/`isolcpus`】。

**(b) 核下线：机制现成，粒度问题如实标注**【实锤（机制）+【假设】（粒度）】。CPU 热下线经 sysfs `cpu/N/online` 是 Linux 成熟机制；mcelog 生态甚至已有先例——cache 错误触发器（`cache-error-trigger`）默认在"CPU 报告过量已纠正 cache 错误"时下线受影响核（"The default trigger offlines the affected CPU cores, unless it is the last core running"，mcelog.org/triggers.html）【强推】。未决问题：(i) 本案例机器 SMT 状态未在 vmcore 中显式记录【实锤，paper_zh.md §6.1 边界】，若为 SMT 配置须按物理核粒度下线兄弟线程；(ii) 阈值如何定标（见 §1.4）。主动测试路线的成本对照【强推，paper_zh.md §6.1 所引 fleetscanner 数据（arXiv:2203.08989 原文核实）】：fleetscanner 对已知缺陷家族 93% 覆盖、23% 独有覆盖，但它是侵入式带外测试（需维护窗口、测试时间累计约 4 billion fleet seconds）；被动 D3 遥测全时在线、零算力开销，二者互补而非互替。

**(c) 局限：被动遥测对纯 D1 类无效——这正是启示二/三的入口**【实锤（本案例事实）+强推（外推）】。D1 类缺陷（加载数据静默损坏、无任何异常前兆）不产生架构可见信号：本案例 5 次致命崩溃的 D1 触发时刻没有任何可消费的 D1 前兆（可用的前兆全部是 D3 类翻译错误告警）。被动遥测只能覆盖"有前兆子类"；无前兆子类需要微架构检测（启示二：位置锚定校验）与制造/现场测试（启示三：PEPR/SBST）补位。此边界不是本论证的缺陷，而是三启示分层的逻辑起点。

### 1.4 反方与边界：误报、可用性与未量化项

**反方一：fail-fast 的误报代价**。spurious 翻译错误存在良性来源：主线内核曾处理"另一 CPU 刚建立映射时乱序页表漫游竞态"（Will Deacon 补丁所针对的合法竞态类）与同核 TLB 失效时序窗口【强推，MICROARCH_SUPPLEMENT.md §D3 答辩引主线 commit 42f91093b043】。若不加过滤直接下线，竞态高发环境（频繁 fork/mmap 的负载）可能把健康核误杀，造成可用性损失——Linux MCE 子系统自身的演化即为此权衡的先例：`mce=tolerancelevel` 提供 0（总是 panic）到 3（从不 panic，仅测试用）的频谱、默认 1【强推，内核文档 x86_64 boot-options】，工业界从未选择"最激进即最优"。本案例用三重过滤排除良性来源【实锤，paper_zh.md §3.4：(1) 72/73 目标为静态长生命周期映射，不满足竞态前提；(2) 100% 单核聚集，与跨 CPU 随机分布的竞态模型不相容；(3) 软件重试成功】。但**通用化部署时该过滤器的假阳性/假阴性率未量化**【假设：需在多机型、多负载基线上采集 spurious 告警的背景发生率并回溯标注，方可定标阈值——本仓库单案例无法提供此统计】。可借镜的定性证据：Google CCKC 启发式经目标测试复核后 70% 以上被诉核确为 SDC 核、不足 10% 为假阳性起诉（其余"存疑"）【强推，arXiv:2508.01786 §3.2.3】——说明"多信号聚合 + 事后测试确认"的两段式能把误报压到工程可接受水平，其代价是需要主动测试基础设施配合（与启示三闭环）。

**反方二：下线的吞吐代价与容量侵蚀**。每下线一核即损失 1/192 的机器算力；若误报率不可控，fleet 级累积下线会侵蚀容量。同时 mcelog 的"最后一个运行核不下线"保留条款表明：下线策略必须与最小可用性约束绑定【强推，mcelog.org/triggers.html】。本案例中该代价的量级【实锤（比例）】：单核占 192 核之 0.52%，且诊断证据链（RMA 依据）完整，属"高置信下单点隔离"，非容量性损失。

**边界总结**：(i) 通用阈值未定标【假设】；(ii) SMT 粒度未验证【假设】；(iii) "隔离即完全避免后续崩溃"未在本机实验执行（下线建议在案但故障机持续运行至取证，事后隔离未观察到复发，反向支持但不等于正向实验）【强推】；(iv) 本节所有本案例数字（73/5/78/2.6h/29.0h/31.7h）出自 paper_zh.md、DIAGNOSIS_REPORT.md 与 vmcore-diagnosis-report 系列，命令级复现路径见 DIAGNOSIS_REPORT.md §7【实锤】。

## 2. 启示二：高 AVF 通路的物理位置标签（位置锚定校验）
### 2.1 合理性：汉明距离 0 故障为何对 ECC 隐形
### 2.2 必要性：AVF 视角的设计优先级
### 2.3 可行性与反方论证
（Task 2 填充）

## 3. 启示三：从 ATPG 到 PEPR——物理感知区域穷尽测试
（Task 3 填充）

## 4. 位置锚定校验原型（CHAOSPosParity）
### 4.1 设计
### 4.2 实验方法
### 4.3 结果
（Task 4-5 填充）

## 5. 理论开销分析
（Task 6 填充）

## 6. 综合结论：三启示的合理性/必要性/可行性总裁决
（Task 7 填充）

## 参考文献

**本节（§1，Task 1）引用**：

1. H. D. Dixit, S. Pendharkar, M. Beadon, C. Mason, T. Chakravarthy, B. Muthiah, S. Sankar, "Silent Data Corruptions at Scale," arXiv:2102.11245, 2021. https://arxiv.org/abs/2102.11245 （作者单位 Facebook/Meta。**诚实注记**：paper_zh.md §8 参考文献引作 "USENIX ATC 2021"，本 Task 于 2026-09-02 核实未能确认该 venue——usenix.org/conference/atc21/presentation/dixit 返回 404，ATC'21 议程（67 篇 presentation 页）无此文，DBLP 仅记录 CoRR abs/2102.11245（arXiv 预印本）；另一可核实的相关条目为 Dixit 的 IOLTS 2023 主题报告（DOI 10.1109/IOLTS59296.2023.10224872）。本文正文按 arXiv 预印本引用，不使用未核实的 venue。）
2. P. Hochschild, P. Turner, J. C. Mogul, R. K. Govindaraju, P. Ranganathan, et al., "Cores that don't count," HotOS 2021. DOI 10.1145/3458336.3465297. https://dl.acm.org/doi/10.1145/3458336.3465297 （DBLP 确认 HotOS 2021 收录；"a few mercurial cores per several thousand machines" 的原文措辞经 ACM PDF 因反爬不可直读，由三个独立二手来源交叉核实——The Register 2021-06-04 报道直接引用、Alastair Reid RelatedWork 摘要页、以及多篇学术转引，判定为可靠。）
3. H. D. Dixit, L. Boyle, G. Vunnam, S. Pendharkar, M. Beadon, S. Sankar, "Detecting silent data corruptions in the wild"（fleetscanner/Ripple，Meta）. arXiv:2203.08989, 2022. https://arxiv.org/abs/2203.08989 （93% 已知家族覆盖 / 23% 独有覆盖 / ~4 billion fleet seconds 均自 PDF 原文摘录。**诚实注记**：paper_zh.md §6.1/§8 引注为 OSDI'22，本 Task 于 2026-09-02 核实：DBLP 检索 "Detecting silent data corruptions in the wild" 仅返回 CoRR abs/2203.08989，未见 OSDI'22 收录记录；文中图件命名含 "SELSE2022" 迹象但正文未标注 venue，此处按 arXiv 预印本引用。）
4. S. Mitra, S. Banerjee, M. Dixon, M. Fuller, R. Govindaraju, P. Hochschild, E. X. Liu, B. Parthasarathy, P. Ranganathan, "Silent Data Corruption by 10x Test Escapes Threatens Reliable Computing," arXiv:2508.01786, 2025. https://arxiv.org/abs/2508.01786 （Google；第一作者 Mitra 主要隶属 Stanford。5,000 DPM vs 工业目标 100–500 DPM、SDC 芯片 ~1,000 DPM、Table 4 检出途径分布 49%/29%/10%、CCKC ≥80%/≥5 次/≥3 栈顶与 70%+ 确证/<10% 假阳性——均自 PDF 原文摘录核实。）
5. ISO 26262-1:2018, Road vehicles — Functional safety — Part 1: Vocabulary, 定义 3.131 "safe state". https://www.iso.org/obp/ui/#iso:std:iso:26262:-1:ed-2:v1:en （"operating mode, in case of a failure, of an item without an unreasonable level of risk"；转引佐证：T. Stolte, S. Ackermann, R. Graubohm, B. Maurer, "A taxonomy to unify fault tolerance regimes for automotive systems," IEEE Trans. Intelligent Vehicles 7(2):251–262, 2022, DOI 10.1109/TIV.2021.3129933, https://arxiv.org/abs/2106.11042 —— 该文 §II 引用并统一了 ISO 26262/ISO SOTIF 的 safe state 定义，同时给出 fail-safe 与 fail-silent 的术语辨析。）
6. mcelog triggers 与 cache-error-trigger 文档（CPU 下线先例："The default trigger offlines the affected CPU cores, unless it is the last core running"）. http://www.mcelog.org/triggers.html ；配置阈值见 https://mcelog.org/config.html （ce-error-threshold = 10/24h 等 leaky-bucket 阈值机制。）
7. Linux 内核文档，x86_64 boot options，`mce=tolerancelevel` 0–3 级 fail-fast/可用性频谱（默认 1）. https://www.infradead.org/~mchehab/kernel_docs/x86/x86_64/boot-options.html （docs.kernel.org admin-guide 的镜像页；tolerant 0=always panic、3=never panic。）
8. Linux 内核 RAS 概念文档（Availability/Reliability 定义与"检测→纠正→预警"框架）. https://docs.kernel.org/admin-guide/RAS/main.html
9. 本仓库内部证据（【实锤】级，命令级复现路径见 DIAGNOSIS_REPORT.md §7）：docs/cases/core179-microarch-rootcause-synthesis/paper_zh.md（§3.1/§3.4/§6.1）；DIAGNOSIS_REPORT.md（§2 时间线与复现命令、§3.1 Class A、§6 处置建议）；vmcore-diagnosis-report-127.0.0.1-2026-08-14-190704.md（§2 29.0h 前兆/31.7h 崩溃/2.6h 提前量、§5 前兆证据链、§7 风险面、§9 下线命令）；MICROARCH_SUPPLEMENT.md（§D3 三重过滤与竞态反驳）。

（各 Task 随写随补，Task 8 统一去重）
