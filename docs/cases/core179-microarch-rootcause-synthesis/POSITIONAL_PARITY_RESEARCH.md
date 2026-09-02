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

本节论证 paper_zh.md §6.2 的核心主张：**对高 AVF 数据通路上的结构性字节通道错位，应部署显式编码通道物理位置的校验（位置锚定校验 / positional parity），而非依赖端到端 ECC**。§2.1 给出数学核心（ECC 结构性盲视命题 + 位置标签检测原理 + 纯 XOR 聚合字的置换不变性定理），§2.2 以 AVF 方法论论证部署位置的优先级，§2.3 以先例谱系与三条反方论证收束。本节同时锁定校验器语义规格（标签函数、位宽、聚合字形式），供 §4 原型（Task 4）与 §5 开销分析（Task 6）直接引用。

### 2.1 合理性：汉明距离 0 故障为何对 ECC 隐形

**(i) ECC 盲视命题（矩阵推导）**【实锤，数学推导 + 数值验证】。考虑任意线性分组码，校验矩阵 H ∈ GF(2)^{r×n}，码字 c = (d‖e)（数据位 d 与校验位 e），伴随式 s = H·cᵀ。设字节通道置换 σ≠id 同时作用于数据字节与校验位（D1 的"同步错位"几何：校验位与数据位在同一组多路复用器/写回总线上相邻走线、同步换相）。关键在于通道对称码（lane-symmetric code）——即按通道交织的线性码，每通道的校验位仅为本通道数据字节的函数（per-byte parity、按字节交织的 SEC-DED、每通道 CRC-8 均属此类，DDR4/PCI 等真实接口校验即此形态）。对这类码，伴随式按通道分解：s(c) = (s_lane(d_0,e_0), …, s_lane(d_7,e_7))。推导（4 行）：

1. 置换后码字 c' 满足：对每个通道 i，(d'_i, e'_i) = (d_{σ(i)}, e_{σ(i)})——即整个**合法通道码字**被搬运到通道 i；
2. 故 s(c')_i = s_lane(d_{σ(i)}, e_{σ(i)})；
3. 由码的通道对称性，σ(i) 通道的原码字合法 ⟺ s_lane(d_{σ(i)}, e_{σ(i)}) = 0；
4. 故 s' = P_σ·s（伴随式各通道分量同步置换），**s' = 0 ⟺ s = 0**。∎

即：ECC 对"数据 + 校验位整体换位"这类汉明距离为 0 的结构故障**盲视**——不是漏检概率小，而是伴随式恒为零、原理性不可见。数值验证：对 per-byte parity 码与按字节交织的 (13,8) SEC 码，在随机数据上做 8 字节旋转 + 校验位同步旋转，全部通道伴随式恒为 0（本节所有数值断言的验证脚本与输出记录于 Task 2 工作笔记，可按本节公式一行 Python 复现）。**诚实划界**：对单一整块（monolithic）SEC-DED 码（一个 H 覆盖全部 72 位、校验位不按通道分解），字节旋转**不是**码自同构，旋转后伴随式一般非零（数值验证：8 位伴随式中 2 位翻转）——即盲视命题的严格成立范围是通道对称码。但这对结论无实质削弱，原因有二【强推】：(a) 真实 LSU 返回通路上的校验形态恰是通道对称的（DDR4 每字节 CRC-8、总线 per-byte parity；且 L1D 填充路径常根本无 ECC——本案例 RAS 零记录即含"未覆盖"情形，paper_zh.md §2.1）；(b) 更根本的几何事实是：ECC 校验点在 L2/内存边界，而 D1 的旋转发生在 fill-buffer 合并级——**校验点在故障点的上游**，ECC 从未见过被旋转的数据。两条独立理由都使端到端 ECC 对 D1 失效；通道对称性只是让"即使搬到下游也无效"这一点在数学上严格化。

**(ii) 位置标签的检测原理与校验器语义规格（锁定）**【实锤，数学证明】。位置锚定校验的核心是把"通道物理位置"从隐式（走线拓扑）变为显式（编码进校验值）。规格（§4 原型与 §5 开销分析直接引用，不得漂移）：

- 通道位置常量：**L_i = (i+1) & 7**，i ∈ [0,7]。常量集 {1,2,3,4,5,6,7,0} 恰为 8 个两两互异值——L 是 8 通道到 3 位空间的双射（tagWidth = 3）。
- 每通道标签：**T_i = L_i ⊕ popcount1(data[i])**（popcount1 为 8 位字节的奇偶，1 级 XOR 树，7 个 XOR2）。标签把位置常量与数据一次一覆盖（数据奇偶）混合：纯常量标签会被"标签随数据同步换位后原样通过"的锁步故障绕过吗？不会——见下。
- 聚合校验字（跨通道兜底，覆盖位翻转）：**必须用非交换混合**——按通道加权的 mod-256 加法（如 W = Σ_i w_i·data[i] + c_i mod 256，w_i 两两不同），**不得用纯 XOR 折叠**（原因见 (iii)，这是本节最重要的理论发现）。

检测论证（锁步模型，标签与数据同走一组 mux）：通道 i 收到来自通道 σ(i) 的 (data[σ(i)], T_{σ(i)})，接收端以本地位置常量重算 L_i ⊕ popcount1(data[σ(i)])，与到达的标签 T_{σ(i)} = L_{σ(i)} ⊕ popcount1(data[σ(i)]) 比较：两者相等 ⟺ L_i = L_{σ(i)} ⟺ i = σ(i)（L 双射）。故**任何非恒等置换 σ 必在某个通道失配，检出概率恰为 1，且与数据内容完全无关**（数值验证：200,000 次随机数据 × 随机旋转，逃逸 0 次）。这优于计划早期表述的"失配概率 1 − 2^(−tag_width)"——那是对**无位置常量设计**（纯随机/纯奇偶标签）的界；对两两互异位置常量 + 锁步换位的模型，检出是确定性的。规格因此选定互异常量设计。位翻转覆盖：聚合字 W 对数据逐位敏感（数值验证：50,000 次单比特翻转，逃逸 0 次）——但须注意位翻转本可由传统奇偶检出，位置标签的独有价值是对旋转的确定性检出（传统奇偶在锁步换位下检出率为 0，见 (i)）。

**(iii) 纯 XOR 聚合字的置换不变性定理（本报告核心理论发现）**【实锤，定理 + 数值验证】。设聚合字为纯 XOR 折叠形式 W = ⊕_i (data[i] ⊕ (L_i ≪ 5))（位置常量移入独立位平面后逐项异或）。对任意字节通道置换 σ：

W(σd) = ⊕_i (data[σ(i)] ⊕ (L_i ≪ 5)) = (⊕_i data[σ(i)]) ⊕ (⊕_i (L_i ≪ 5)) = (⊕_i data[i]) ⊕ (⊕_i (L_i ≪ 5)) = W(d)，

第二个等号用**异或对置换可交换**（⊕_i data[σ(i)] = ⊕_i data[i]，多重集的异或与次序无关）。故 **W' ⊕ W = 0：纯 XOR 聚合字对任意通道置换不变，对字节旋转零检出**（数值验证：28,000 次随机旋转，检出 0 次——不是漏检概率小，是恒为零）。这一发现有三重意义：(a) 它是 §2.1(i) ECC 盲视命题的同一数学根源的另一面——**任何"可交换的"校验聚合（XOR 折叠、普通奇偶）都继承对置换的盲视**，位置锚定的数学本质是显式打破置换对称性；(b) 它否决了一类看似自然的设计（"把位置常量 XOR 进聚合字就够了"——不够，XOR 会把位置信息在置换下重新分布后抵消）；(c) 若需聚合字提供任何旋转敏感度，必须用非交换运算（如按通道加权的 mod-256 加法）。**诚实限定**：加权加法聚合字对旋转也非确定性检出——对常数数据（各字节相同）旋转，Σ_i w_i·d = d·Σ_i w_i 与通道次序无关，恒逃逸（数值验证：随机数据检出率 ~98.6%，常数数据 0%）。因此规格的正确分工是：**旋转的确定性检出由每通道标签 T_i（双射位置常量）独立承担；聚合字只承担位翻转兜底**（其非交换形式仅为"若要求聚合字对旋转提供概率性补充检出"的备选，不作为旋转的主检测器）。§5 开销分析（Task 6）将引用本定理。

**(iv) 与 D2 的划界**【实锤，本案例事实】。D2（地址呈现通路 MSB 字节置零，paper_zh.md §3.3）是**位级 stuck-at** 故障，普通奇偶即可检出（单比特/单字节置零改变奇偶性），不需要位置标签；位置锚定校验针对的是 D1 的字节通道错位成分（位置错误），二者故障模型不同维度。如实声明：位置标签对 D2 无针对性增益，对 D3（PTW 读出瞬态误读）的价值取决于读出数据是否经过带标签的汇聚通路（未在本案例中取证到该细节，【假设】）。

### 2.2 必要性：AVF 视角的设计优先级

**为什么偏偏是 fill-buffer 合并级 / load 返回 mux**。AVF（Architectural Vulnerability Factor）方法论（Mukherjee et al., MICRO-36 2003【诚实注记：paper_zh.md §6.2/§8 引作 "ISCA'03"，经 DBLP 核实其实际 venue 为 MICRO-36 2003，DOI 10.1109/MICRO.2003.1253181；本报告按核实后的 venue 引用】）定义结构的 AVF 为"该结构中一个故障最终导致程序可见错误的概率"，其 ACE 位分析给出判据：**输出直接进入架构寄存器（架构状态）的结构是高 AVF 结构**——原文度量了 Itanium2 类处理器的指令队列 AVF 14–47%、执行单元 4–27%，并明确 AVF × 原始错误率 = 结构错误率的优先级排序框架。**诚实限定**：原文未直接测量 fill-buffer/load-return mux 的 AVF（该文只分析了指令队列与执行单元；其后续 ISCA'05 扩展到地址类结构），将 fill-buffer 合并级判为高 AVF 是**依据 ACE 判据的推断**【强推】，但本案例给了它一个罕见的实证锚点：`ldr x20, [x0, w25, sxtw #3]` 加载 `__per_cpu_offset[i]` 后，坏值经 `add x27, x1, x20` 直接成为指针、下一条 `ldr x23, [x27, #288]` 即解引用崩溃——**load 返回值在两条指令内成为指针并击穿执行**（paper_zh.md §3.2，4/5 致命崩溃同链）【实锤】。这正是"输出直接写架构寄存器 + 高概率被用作指针"的高 AVF 几何：任何逃逸检测的坏值都不需要长潜伏期就转化为 SDC 或崩溃，且指针污染具有错误放大性（下游解引用破坏面远大于单数据字）。10x-escapes 论文从工业侧收敛同一判断：逃逸缺陷芯片中约 1,000 DPM 产生 SDC，且 fleet 级普遍存在【强推，arXiv:2508.01786】。

**设计优先级结论**【强推】。按 AVF × 缺陷率的排序，位置锚定校验应部署于 **load-return 汇聚点**（fill-buffer 合并级 / load 返回多路复用器，即 paper_zh.md §6.2 列出的 load-return、address-presentation、PTW-readout 三条通路中 AVF 最高的第一条），而非全芯片均匀铺设——均匀铺设既无必要（低 AVF 结构的故障大半被 ACE 屏蔽）也不可行（时序/面积预算不允许全局加校验）。这与 DFT/RAS 规划的常规做法一致：保护预算按 AVF 分级投放。

### 2.3 可行性与反方论证

**(i) 先例谱系：位置校验是迁移，不是发明**【强推，各有可核查出处】。位置感知校验在 CPU 外围接口已有四级成熟先例，本提议的增量只是"从片间/接口级搬入片内数据通路"：

| 层级 | 先例 | 位置感知机制 | 可核查出处 |
|---|---|---|---|
| 总线 | PCI/PCIe | PCI **PAR 信号**：对 AD[31::00] + C/BE[3::0]# 全 36 位统一偶校验（PCI Local Bus Spec Rev 2.2 §2.2.2 "Parity is even parity across AD[31::00] and C/BE[3::0]#. Parity generation is required by all PCI agents"）；PCIe 数据链路层对每个 TLP 加 12 位序列号 + 32 位 LCRC，失配经 ACK/NAK 重传——序列号显式编码"链路位置/顺序" | PCI 2.2 规范镜像 https://ics.uci.edu/~iharris/ics216/pci/PCI_22.pdf（该副本为扫描图像版，引文经 PC/104 联盟规范 https://pc104.org/wp-content/uploads/2015/02/PCI104-Express-v2_0.pdf 等独立二手来源交叉核实）；PCIe LCRC/序列号：AMD/Xilinx WP350 https://docs.amd.com/api/khub/documents/4uw~7uS2eK5x7lKbNdxWlw/content（原文摘录 "The DLL adds the sequence number and Link Layer CRC (LCRC) to the packet"） |
| 内存接口 | DDR4 | **每字节通道写 CRC**（JESD79-4 §4.16）：x8 器件对 72 位输入按字节通道算 CRC-8（多项式 x⁸+x²+x+1，即 ATM-HEC），BL8 突发展宽为 10 UI（8 数据 + 2 CRC）；DRAM 重算失配拉 ALERT_n | JEDEC 标准页 https://www.jedec.org/taxonomy/term/2902（正文需注册获取）；CRC-8 多项式/10-UI 帧由实现文献核实：Lee, IJCA 9(4) http://article.nadiapub.com/IJCA/vol9_no4/2.pdf（原文摘录 "ATM-8 HEC code … ~700 XOR gates … 6 stage"、tCCD=5nCK 时序约束） |
| I/O 存栈 | T10 PI / DIX | 8 字节保护信息三元组：16 位 guard（数据 CRC）+ 16 位 application + **32 位 reference tag**——reference tag 含 LBA 低 32 位（Type 1）或按块**递增计数器**（Type 2 / DIX_REF_INCREMENT），显式编码"块位置"，专防乱序与错向写（原文 "the reference tag is being used to protect against out-of-order and misdirected write scenarios"） | Oracle DIX 草案（M. K. Petersen）https://oss.oracle.com/~mkp/docs/dix-draft.pdf（PDF 全文已核实，引文为原文摘录）；T10 04-015r0 https://www.t10.org/ftp/t10/document.04/04-015r0.pdf |
| chiplet 互连 | UCIe 1.1 | Die-to-Die adapter 对每个 flit 插入头部 + CRC，提供 CRC 检测与**重放（replay）**；1.1 版新增 streaming flits，把 AMBA CHI 打包进受 CRC+replay 保护的 flit（此前 Raw Mode 绕过错误检测） | UCIe 联盟官方博客 https://www.uciexpress.org/post/ucie-1-1-provides-streaming-protocol-solution-for-error-detection-and-replay（2023-08-28，作者 NVIDIA/Arm；页面正文为客户端渲染，核心句经多源交叉核实）；规范下载 https://www.uciexpress.org/specifications |
| （对照）网络 | TCP | 链路 CRC **不能**检测的字节重排/乱序正是传输层序列号存在的理由之一：RFC 793 "The TCP must recover from data that is damaged, lost, duplicated, or delivered out of order … achieved by assigning a sequence number to each octet transmitted" | https://www.rfc-editor.org/rfc/rfc793.txt（原文摘录，HTTP 200 核实） |

谱系要点：这些系统的共同教训是**"校验载荷不够，还须校验位置/顺序"**——TCP 序列号、T10 reference tag、PCIe 序列号都是显式位置编码；CPU 内部数据通路是这一原理尚未覆盖的最后一级（片内 mux 的通道位置从未被显式校验）。

**(ii) 三条反方论证的正面处理**。

**反方一：为什么不用端到端 CRC over 64-bit（一次检出任意重排）替代位置标签？** 回应有二【强推】。其一（检测能力层面）：CRC 作为**载荷函数**确实对"载荷+位置"联合敏感——若 CRC 校验点在故障点下游且校验位不与数据同步错位，字节旋转可检出。但其二（时序与解耦层面，决定性）：fill-buffer 合并级是**多源汇聚点**，校验必须逐字节并行、与数据内容解耦才能嵌入现有流水。串行 CRC-64 是 64 级 LFSR 链式移位（每处理 1 位数据经过 64 级异或反馈）；一次性 64 位并行 CRC 需要 ~64×64 = 4096 个 XOR2 等效门的组合网络（对比：每字节奇偶 7 个 XOR2、8 通道共 56 个 + 3 位标签比较 ~50 个 ≈ 100-150 门量级，深度 3-5 级 vs 并行 CRC 树 6+ 级）。DDR4 的工业经验直接印证这一时序压力：其 CRC-8 并行实现在 DRAM 内已需 ~700 XOR 门 / 6 级异或深度，被 tCCD = 5nCK 的无缝传输约束逼到"每级异或 <120 ps"的紧余量（Lee, IJCA 9(4)）——这还是 8 位 CRC，不是 64 位。**并且存在更根本的陷阱**：若把 CRC 位与数据放在同一组通道上同步传输（工程上最省走线），CRC 对"载荷重排 + CRC 位自身重排"的锁步故障同样可能失效（CRC 是线性运算，其置换对称性与 §2.1(i) 同源——具体失效条件取决于 CRC 位是否按通道对称布局）；位置标签的解耦性（标签计算独立于数据内容、逐通道局部、可全并行）是时序可行性的核心。此论证的量级数字标注【假设】（未做 RTL 综合，门数/深度为解析推导的量级估算）。

**反方二：锁步/DMR 替代论——为什么不直接双份通路？** DMR 可检测任意错误（包括位置错位），代价是**整条通路面积翻倍 + 64 位比较器**（数千门量级），且比较器本身在关键路径上；位置标签是 ~100-150 门 + 每 64 位载荷 24-32 位标签寄存器（量级估算【假设】），**面积差约两个数量级**。10x-escapes 论文对冗余路线的工业裁决可直接引用：DMR/TMR"对商品级计算硬件带来大的能耗、执行时间与面积开销"（"Such approaches incur large energy, execution time, and area overheads for commodity compute hardware"），故超大规模数据中心不采用，逃逸缺陷由此成为无人设防的空档【强推，arXiv:2508.01786 原文摘录】。位置标签的定位是"针对单一结构化故障类的轻量定向检测"，与 DMR 的"通用任意错误检测"不在同一成本档位——按 §2.2 的 AVF 分级，只有最高价值通路才值得后者。

**反方三：单案例外推质疑——"真实缺陷真的普遍是字节旋转吗？"** 本案例的取证事实是硬的【实锤】：§3.2 的穷举证伪证明坏值不可由目标槽位任何单字节 bit-flip 产生（1536 个槽位×旋转候选中唯一命中头部槽位，随机命中概率 ~2⁻⁵⁸），这是**取证事实**而非推测。但由此推出"设计规则应普遍引入位置锚定校验"，统计基础确实薄弱——**单案例（n=1 台机器、单一微架构）无法估计字节通道错位类缺陷在缺陷总体中的占比**，本报告如实标注【强推】。工业验证路径的抓手是 10x-escapes 论文的第三叉论点："需要**新的检测实验**以理解新检测技术的有效性，且这些实验必须克服既往工业测试实验的缺陷与陷阱"（原文 "New test experiments to deeply understand the effectiveness of new techniques for detecting defective chips. These new test experiments must overcome the drawbacks and pitfalls of previous industrial test experiments and case studies"）——位置锚定校验的检测有效性（对真实缺陷种群、而非对合成故障模型）正需要这类实验来定标；在此之前，其部署论证停留在"数学合理性 + 单案例必要性 + 先例可行性"，不足以作为无条件的通用设计规则。产业侧的旁证：Intel IFS（In-Field Scan）的公开定位明确承认存在"**parity 或 ECC 检查抓不到的问题**"（kernel 文档原文 "a hardware feature to run circuit level tests on a CPU core to detect problems that are not caught by parity or ECC checks"），其 SAF/ArrayBIST/SBAF 三级现场测试形态（https://docs.kernel.org/arch/x86/ifs.html，SAF <200 ms/核、ArrayBIST <5 ms）证明工业界已为"逃逸 RAS 的缺陷"建立现场结构测试基础设施——这是"问题真实存在"的产业证认；但 IFS 的测试内容与内部结构细节 NDA-gated，公开资料无法核实其对字节通道错位类的覆盖，如实标注不可得【强推，docs.kernel.org 原文摘录 + Intel 支持页 https://www.intel.com/content/www/us/en/support/articles/000098402/processors/intel-xeon-processors.html】。

**(iii) 边界：陈旧行重放成分不在覆盖范围**【实锤，与论文 §6.2 边界声明一致】。D1 包含两个独立成分：(1) 字节通道错位（位置错误）；(2) 陈旧行重放（来源错误——fill-buffer 最旧条目被回放给跨 set 的另一 load，paper_zh.md §3.2 取证）。位置标签只检测成分 (1)；对成分 (2)——**数据值本身正确但来源错误**——需要**来源/起源标签**（如 fill-buffer 槽位 ID 校验：发出端把槽位号编入校验、接收端核对本次 load 命中的槽位与数据来源一致）。本报告的原型（§4）不覆盖成分 (2)，stale-line-replay 注入器在 FI_DESIGN_SUPPLEMENT 中有设计但未实现（paper_zh.md §4.4 诚实边界）——两处边界声明一致，非本节新增让步。

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

**本节（§2，Task 2）引用**：

10. S. S. Mukherjee, C. Weaver, J. Emer, S. K. Reinhardt, T. Austin, "A Systematic Methodology to Compute the Architectural Vulnerability Factors for a High-Performance Microprocessor," MICRO-36, 2003, pp. 29–40. DOI 10.1109/MICRO.2003.1253181. https://doi.org/10.1109/MICRO.2003.1253181 （**诚实注记**：paper_zh.md §6.2/§8 引作 "ISCA'03"；本 Task 于 2026-09-02 经 DBLP（key conf/micro/MukherjeeWERA03）核实其实际 venue 为 MICRO-36 2003，DOI 与 venue 均以 DBLP 为准。原文 PDF 镜像 https://users.ece.northwestern.edu/~rjoseph/ece510-fall2005/papers/austin-MICRO36-AVF.pdf 已下载并全文提取核实：AVF 定义、ACE 位判据、指令队列 AVF 14–47% / 执行单元 4–27% 均为原文摘录；**原文未测量 fill-buffer/load-return 的 AVF**（全文无 "fill buffer" 字样），§2.2 对 fill-buffer 的高 AVF 判定是依据 ACE 判据的推断，已标【强推】。后续论文：Mukherjee et al., "Computing Architectural Vulnerability Factors for Address-Based Structures," ISCA 2005, DOI 10.1109/ISCA.2005.18，DBLP 核实。）
11. PCI Local Bus Specification, Revision 2.2, §2.2.2（PAR 信号："Parity is even parity across AD[31::00] and C/BE[3::0]#. Parity generation is required by all PCI agents."）. 扫描版镜像 https://ics.uci.edu/~iharris/ics216/pci/PCI_22.pdf （HTTP 200 核实，2.1 MB；**该副本为扫描图像版无法文本提取**，引文经以下独立来源交叉核实：PC/104 联盟 PCI/104-Express 规范 https://pc104.org/wp-content/uploads/2015/02/PCI104-Express-v2_0.pdf（同样引用 PAR 定义）及 Encyclopedia.pub "Conventional PCI" 条目。）
12. AMD/Xilinx WP350, "Understanding Performance of PCI Express Systems"（PCIe 数据链路层："The DLL adds the sequence number and Link Layer CRC (LCRC) to the packet to guarantee successful transmission across the link"；TLP 图标注 Sequence 12/16 位 + LCRC 4 字节）. https://docs.amd.com/api/khub/documents/4uw~7uS2eK5x7lKbNdxWlw/content （PDF 已下载并文本提取，引文为原文摘录。）
13. JEDEC Standard JESD79-4 (DDR4 SDRAM), §4.16（每字节通道写 CRC，多项式 x⁸+x²+x+1，BL8 → 10 UI）. 标准页 https://www.jedec.org/taxonomy/term/2902 （正文需 JEDEC 注册获取，未直接核实原文；CRC-8 多项式/10-UI 帧/门数由实现文献交叉核实：J.-H. Lee, "Data Transmission Error Detect Scheme for High Speed Semiconductor Memory," IJCA 9(4), 2016, http://article.nadiapub.com/IJCA/vol9_no4/2.pdf —— PDF 已下载并文本提取，原文摘录 "ATM-8 HEC code … over 700 XOR gates … 6 stage"、"CRC time < tCCD = 5nCK"、"each XOR gate delay time to be allocated less than 120ps"。）
14. M. K. Petersen, "The Data Integrity Field"（Oracle DIX 草案）: "the reference tag is being used to protect against out-of-order and misdirected write scenarios"；Type 2 reference tag 为"由 32 字节 CDB 播种的递增计数器"；DIX_REF_INCREMENT 标志按块递增. https://oss.oracle.com/~mkp/docs/dix-draft.pdf （PDF 已下载并全文提取，引文为原文摘录。）
15. T10/SCSI，块级递增 reference tag 顺序性问题分析. https://www.t10.org/ftp/t10/document.04/04-015r0.pdf （HTTP 200 核实。）
16. UCIe Consortium (M. Denman, NVIDIA; F. Socal, Arm), "UCIe 1.1 Provides Streaming Protocol Solution for Error Detection and Replay," 2023-08-28. https://www.uciexpress.org/post/ucie-1-1-provides-streaming-protocol-solution-for-error-detection-and-replay （页面 HTTP 200 核实，标题/作者/日期经页面元数据确认；**页面正文为客户端渲染不可直接抓取**，"D2D adapter 插入 flit 头与 CRC、提供 CRC 检测与 replay"、"Raw Mode 绕过错误检测"等核心内容经多源交叉核实：Synopsys https://www.synopsys.com/articles/noc-interconnects-ucie-ip.html 等。规范本体需从 https://www.uciexpress.org/specifications 注册下载，未核实原文。）【强推，二手交叉】
17. J. Postel (ed.), RFC 793, "Transmission Control Protocol," 1981, Reliability 节："The TCP must recover from data that is damaged, lost, duplicated, or delivered out of order by the internet communication system. This is achieved by assigning a sequence number to each octet transmitted…" https://www.rfc-editor.org/rfc/rfc793.txt （原文全文已下载，引文为逐字摘录。）
18. Linux 内核文档, "In-Field Scan"（IFS）: "a hardware feature to run circuit level tests on a CPU core to detect problems that are not caught by parity or ECC checks"；SBAF "mimics the manufacturing screening environment and leverages the same test suite… makes use of Design For Test (DFT) observation sites". https://docs.kernel.org/arch/x86/ifs.html （页面已抓取，引文为原文摘录。）
19. Intel, "What Is Intel In-Field Scan on Intel Xeon Processors?"（SAF：扫描链测试核心逻辑、<200 ms/核；ArrayBIST：cache/阵列内建自测、<5 ms；SBFT/Structural-Based Fault Testing）. https://www.intel.com/content/www/us/en/support/articles/000098402/processors/intel-xeon-processors.html （页面已抓取并解析，测试形态与时长为原文摘录；IFS Enabling Guide 细节 NDA-gated 不可得，如实标注。）
20. S. Mitra, S. Banerjee, M. Dixon, M. Fuller, R. Govindaraju, P. Hochschild, E. X. Liu, B. Parthasarathy, P. Ranganathan, "Silent Data Corruption by 10× Test Escapes Threatens Reliable Computing," arXiv:2508.01786, 2025（§2 引用两点：(a) 三叉论点之第三叉 "New test experiments to deeply understand the effectiveness of new techniques for detecting defective chips. These new test experiments must overcome the drawbacks and pitfalls of previous industrial test experiments and case studies"；(b) 对 DMR/TMR 的工业裁决 "Such approaches incur large energy, execution time, and area overheads for commodity compute hardware"。PDF 已下载并全文提取，引文为原文摘录。另见 §1 参考文献 [4]。）. https://arxiv.org/abs/2508.01786
21. F. Angione, P. Bernardi, A. Sinha, "From Structural Test Escapes to Silent Data Errors: A Preliminary Analysis," 2025 IEEE 9th International Test Conference India (ITC India). DOI 10.1109/ITCIndia66078.2025.11141623. https://doi.org/10.1109/ITCIndia66078.2025.11141623 （DOI 解析 302 → ieeexplore.ieee.org/document/11141623 核实；IEEE 全文因反爬不可直读，标题/作者/venue 经 IEEE Xplore 检索结果与 Politecnico di Torino 机构库条目交叉核实。paper_zh.md §8 所记 DOI 尾号 11141623 与此一致。）

（各 Task 随写随补，Task 8 统一去重）
