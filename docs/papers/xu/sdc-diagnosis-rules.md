# SDC 诊断结构化判定规则
## ——基于故障传播链的多层级探针协同判定体系

> 依据 `docs/papers/ref/` 目录下 29 篇 SDC 相关论文综合提炼（AVF/ACE 分析谱系、gem5 故障注入谱系、全栈传播机理谱系、生产环境 fleet 实证谱系、硬件/运行时检测谱系、软件/应用级检测谱系）。
> 每条规则标注来源论文，保证可回溯。

---

## 0. 总框架

### 0.1 SDC 的严格定义（判定的一切前提）

SDC 判定是**三条件合取**，缺一不可 [MeRLiN/GeFIN 体系]：

```
SDC ⇔ (程序正常结束) ∧ (输出与 golden run 不一致) ∧ (全程零异常记录：无额外 ISA 异常、无 crash、无超时)
```

配套的六级故障效果分类（一次事件必居其一）：

| 类别 | 判定信号 | 判据 |
|---|---|---|
| **Masked** | 输出 + 异常均与 golden 完全一致 | 故障未到达架构层或被掩蔽 |
| **SDC** | 正常结束 ∧ 输出 diff ≠ 0 ∧ 零异常 | 静默数据损坏 |
| **DUE** | 完成或未完成，但有错误指示（异常/parity/断言）| 再分 true DUE（输出也错）/ false DUE（输出其实正确）|
| **Timeout** | 执行时间 > 3× golden 时间（Deadlock：不再 commit；Livelock：持续重定向）| [MaFIN/GeFIN 的 3× 工程约定] |
| **Crash** | 进程异常终止 / 系统不可恢复（kernel panic）/ 仿真器终止 | 分 process/system/simulator 三级 |
| **Assert** | 仿真/固件断言触发 | |

**应用容差修正** [GemFI]：输出"错"但仍在应用可接受容差内（PSNR>30dB、Monte Carlo 前两位小数正确、迭代收敛）**不是 SDC**，应单列"tolerant-correct"。诊断时必须区分"逐位正确 / 容差内正确 / 超容差（真 SDC）"三级。

### 0.2 故障传播链层级模型

```
L0 电路/物理层      缺陷本体：stuck-at、marginal、aging(BTI)、small delay fault、软错误
      ↓ 激活条件：toggle、时序裕量、电压/温度/频率、输入位模式
L1 微架构层         结构承载：L1D/L1I/L2、RF、FU、TLB、ROB/LQ/SQ、BTB…
      ↓ 掩蔽三情形：invalid entry、被覆写、mis-speculation 被 flush [SVS]
      ↓ 架构可见点：OoO commit stage [SDC-μArch Perspectives]
L2 ISA/指令层       架构状态污染五类：WD(错数据)/WI(错指令)/WOI(错操作数)/时序偏差/执行流改变
      ↓ 软件掩蔽：dead value、位级逻辑掩蔽、算法容错（迭代收敛/进化淘汰）
      ↓ ESC 旁路：输出驻留缓存被直接损坏 → DMA 写回 → 必然 SDC，不经程序流 [SVS]
L3 OS/系统层        kernel 异常、SEL/BMC 遥测、EDAC/MCE、reboot、syscall 行为
      ↓ kernel 无软件防护、syscall/校验器自身可被污染
L4 应用/业务层      输出 diff、CRC 失配、重执行不一致、PMC 签名偏移、业务数据异常
      ↓ 错误数据跨服务传播
L5 fleet/服务层     单机复发模式、跨机扩散、用户可见业务故障
```

**诊断的本质**：沿传播链**自上而下取证**（从症状层向下收集证据）+ **自下而上归因**（用下层机理证据锁定根因），任一单层判定都有结构性盲区，必须多层协同 [ETS2024, SVS]。

---

## 1. 各层探针与单层判定规则

### L0 电路/物理层探针

**P0-1 时序前兆**：aging-aware STA 的 slack/WNS、cell 延迟退化百分比 [Vega]
**P0-2 环境遥测**：核心温度、电压、频率、功耗（BMC/SEL）[SOSP23, SEVI, Sentinel]
**P0-3 输入位模式**：测试输入的位偏置统计（0/1 概率、特定位恒定）[SEVI, SiliFuzz]

**R0-1（前兆预警）**：if 时序违例路径 slack 持续下降 且 BTI 退化模型预测 10 年内违例 → 该 FU 列入 SDC 高危先验（预测性，非已发生）[Vega]
**R0-2（触发条件判定）**：if SDC 频率与温度呈 log-线性相关（Pearson > 0.75）或存在最小触发温度阈值（如仅 >59°C 出错）→ 判定 marginal/aging 类物理缺陷，非软错误 [SOSP23]
**R0-3（规格内出错）**：if 出错均发生在正常温度/频率范围内（95% incidents 频率 <80% max）→ 不可用"降频避险"处置，属设计/制造缺陷 [SEVI]
**R0-4（输入位敏感）**：if 特定输入位（如 1<<23）清零时几乎必错、置位时正常 → 输入依赖型硬件缺陷，可作为指纹判据 [SiliFuzz FCOS 案例]
**R0-5（延迟故障判据）**：if wire 延迟故障 → 必须同时满足 (a)路径静态超时钟周期 (b)信号实际 toggle (c)错误值被锁存 (d)锁存集合 GroupACE 才产生 SDC；注意 ECC 对延迟故障不等价防护（字线延迟可致 sense amp 锁错行且 ECC 校验通过）[DelayAVF]

### L1 微架构层探针

**P1-1 commit-stage trace diff**：逐条比对 commit cycle/PC/opcode/operands/寄存器内容，判定故障首次架构可见的位置与形式 [gem5-MARVEL, SVS]
**P1-2 PMC/性能计数器**：golden run 与疑犯 run 的 HPC 平均绝对百分比偏差（指令数、cache miss、分支误预测、TLB miss 等 20 个）[CHAOS]
**P1-3 结构占用与 ACE 驻留**：ROB/IQ 占用率、B_ACE×L_ACE（可由性能计数器获得）[AVF 奠基论文]
**P1-4 注入映射表**：gem5-fi 离线注入建立的"注入点→症状"查找表 [ETS2024, Harpocrates]

**R1-1（传播前提）**：if 故障位落在 invalid entry、或被覆写先于读取、或位于 wrong-path（mis-speculation 被 flush）、或命中后从未被 committed 读 → 掩蔽，非 SDC [MaFIN/GeFIN 提前停判据；SVS 三情形]
**R1-2（un-ACE 判据库，九类掩蔽）**：命中以下任一即掩蔽——idle/invalid 状态位（但控制位永远算 ACE）；wrong-path 指令；预测器结构（BTB/分支预测器 AVF=0）；ex-ACE（最后一次使用后）；NOP 指令非 opcode 位；非绑定 prefetch；predicated-false 指令；动态死代码（FDD/TDD，含连续写同地址无中间读）；逻辑掩蔽位（OR 常数、只需零/非零的比较、高位 unused）[Mukherjee MICRO-03 九类 un-ACE]
**R1-3（cache 生命周期判据）**：写穿透 cache data 位 ACE 仅当 fill-to-read / read-to-read / write-to-read；idle/被覆写/驱逐后/写前被覆盖均掩蔽；写回 cache 中某字节一旦被写，同行所有未写字节全 ACE 直到 evict [Biswas ISCA-05]
**R1-4（tag 判据）**：tag 单 bit 错 → 仅 false positive（错误命中、hamming distance=1 的位）可能致 SDC；false negative 只触发 miss+refetch 无害；SB/写回 cache 的 tag 从数据首次修改到 evict 全程 ACE（错 tag 会写错内存位置）[Biswas ISCA-05]
**R1-5（HPC 偏差探针）**：if 输出正确但 HPC 偏差巨大（可达 10³~10⁵ %）→ 隐蔽执行轨迹异常，加严观测；**但注意：主存数据值型 SDC 在 HPC 上几乎无痕迹（<0.3%），纯计数器检测对这类 SDC 无效** [CHAOS]
**R1-6（驻留时长放大）**：永久故障在 L1D 的 SDC 率（最高 70.8%）远高于瞬态（最高 43%）→ 症状反复在同一位置出现时，永久缺陷嫌疑上升 [ITC2023, MARVEL]

### L2 ISA/指令层探针

**P2-1 双执行不一致**：同一线程内同指令、相同架构输入、不同 execution context（前导指令序列、缓存状态）下输出对比 [ITHICA]
**P2-2 指令级错误率**：特定指令/指令族的输出错误频率 [Veritas]
**P2-3 受影响指令打印**：注入时打印受影响汇编指令，做事后相关分析 [GemFI]

**R2-1（不一致即硬件证据）**：if 原始指令与复制指令架构输出不一致 → inconsistent error，硬件嫌疑成立并同步定位到 PC。注意：两份都错且错得相同时（consistent error）原理上检不到 [ITHICA]
**R2-2（执行上下文主导）**：错误是否显现取决于前导指令序列塑造的微架构/电气 context，**而非指令使用频率**（59% 检出测试并非失败 opcode 执行频率最高者；单指令 reproducer 几乎全部失败）→ 复现策略必须构造触发序列，不能只轰炸热点指令 [ITHICA]
**R2-3（x87/超越函数指纹）**：x87 legacy 指令单指令错误率 16–77%，可作单指令复现例外 [Veritas]
**R2-4（ESC 旁路）**：if 故障击中 modified cache line 中即将输出的数据且不再被程序读取 → 经 DMA 直接写回，**必然 SDC**，且任何基于程序流/软件层的检测与归因均失效；输出缓冲区本身即观测点，概率与输出尺寸正相关（MB 级输出显著）[SVS, SDC-μArch]

### L3 OS/系统层探针

**P3-1 内核异常日志**：panic/lockup/GPF/MCE/divide error/stack corruption，按类型+频率+core ID 结构化 [Hardware Sentinel]
**P3-2 SEL/BMC 遥测**：ECC/MCE/PCIe/thermal 事件 [Hardware Sentinel]
**P3-3 EDAC/可纠正错误计数**：CE/UCE 记录 [ETS2024]
**P3-4 重启记录**：意外重启次数、时间戳 [Hardware Sentinel]
**P3-5 修理历史**：misdiagnosed/undiagnosed 修理记录 [Hardware Sentinel]

**R3-1（静默性反向判据，关键）**：if 应用异常时刻近旁 SEL 中 CPU 相关硬件故障（ECC/MCE/PCIe/thermal）条目数 = 0 → 保留 SDC 调查；**有任何硬件遥测的是"loud"故障，不是 SDC** [Hardware Sentinel]
**R3-2（罕见异常聚合）**：if 罕见异常类型（doublefault 59.35×、stack segment 20.77×、invalid op 17.80× 等，相对 fleet 检出率倍数）在单核聚合出现 → SDC CPU 强指标 [Hardware Sentinel]
**R3-3（重启规则）**：if 30 天窗口意外重启 ≥6 次（通用 fleet）/ ≥3 次（AI fleet）→ 进入 SDC 候选 [Hardware Sentinel]
**R3-4（EDAC 负证据）**：if 应用层 SDC 症状 ∧ 全程零 EDAC/CE 记录 → **排除受 ECC/SECDED 保护的阵列（L2/L3、服务器内存），指向无保护单元：功能单元、无 ECC 的 L1D、流水线逻辑**；反之若伴随 EDAC 记录则优先走 CE/UCE 通路 [ETS2024]
**R3-5（校验器自身污染）**：if EC/CRC 由向量指令加速计算 → 校验器与数据可能同时被污染，校验和与已坏数据自洽 → "校验通过"不可作为排除证据 [SOSP23]
**R3-6（OS 放大效应）**：OS/kernel 参与使 SDC 率相对裸机最高放大 6.7×（A5 裸机 23.7% → Linux 59.3%）；kernel 代码涉事的 SDC 无软件防护（L1I tag 的 SDC 中 77% 来自 kernel 指令）→ 诊断规则中 syscall/库路径内的错误不能因"应用自身校验通过"而排除 [IOLTS23, SDC-μArch]

### L4 应用/业务层探针

**P4-1 输出校验**：golden diff、checksum/CRC、ABFT（如 matmul 行列 checksum）[SEVI, Orthrus]
**P4-2 重执行比对**：确定性重放 + 跨核重执行，逐字节比较 [Orthrus]
**P4-3 PMC 签名**：以同机同负载干净运行的重复测量分布为基线，ML 分类器判偏差（<2% 开销）[PMC-SpMV]
**P4-4 业务级异常**：查询返回错数据、计算结果偏离、下游数据丢失（如 Spark 缺行）[Ripple]

**R4-1（重执行黄金范式）**：if 相同输入 + 相同初始内存状态 + syscall 结果重放，在不同核心重执行结果不一致 → **硬件非确定性错误**（软件 bug 会确定性复现、比对一致不报警）；验证核必须与执行核物理隔离（核私有 ALU/FPU/向量单元），否则"同一个坏单元算两遍得到同样错误"漏检 [Orthrus]
**R4-2（CRC 边界判据）**：数据跨越控制↔数据路径边界时 CRC 失配 → 搬运途 corruption；注意 checksum 只能发现"数据被改"，不能发现"计算过程算错"（哈希算错查错表），两者互补 [Orthrus]
**R4-3（PMC 触发器定位）**：PMC 签名判据开销低、适作**必要非充分条件的高召回触发器**（疑点扫描），再触发昂贵的重算/复现取证；判据必须按负载类别（访存型/计算型/数值型）分别校准，并显式处理时间漂移 [PMC-SpMV]
**R4-4（容差判定）**：if 输出偏差在应用语义容差内（PSNR/小数位/收敛性）→ 不是 SDC，避免误报 [GemFI]
**R4-5（ABFT canary）**：if 数值负载（matmul）部署 checksum 类 ABFT → 生产负载自身变检测器（机器检出率 88–100%，时间开销 1.35%）[SEVI]

### L5 fleet/服务层探针

**P5-1 持续测试数据**：out-of-production 分钟级（Fleetscanner，45 天 cadence）+ in-production 毫秒级 co-located（Ripple，日级）[Ripple, SEVI, PinDrop]
**P5-2 core 级失败分布**：失败测试的 core ID 遥测 [PinDrop, SiliFuzz, SEVI]
**P5-3 复发史**：跨天/跨周/跨年的失败记录、失败 seed 回放 [PinDrop, SiliFuzz]
**P5-4 差分测试**：向量单元 vs 标量单元参考输出对比（不同硬件单元天然差分）[SEVI]

**R5-1（跨天复现定案）**：仅当**同一核多天可复现同一问题**才判 defective（抑制偶发噪声）；单次失败只进观察池 [SiliFuzz]
**R5-2（单物理核指纹，最强定位证据）**：if 两个 sibling 逻辑核同败同一测试且频率几乎一致、跨物理核不扩散 → 单物理核单一失效单元缺陷；实证比例：SiliFuzz ~70%、SEVI 89%、PinDrop 62%、SOSP23 约一半机器 [四篇一致]
**R5-3（向量输出 vs 标量参考）**：if 向量指令输出 ≠ 标量参考输出 → 向量单元缺陷；>80% SDC cases 首次失败 <10K 轮（1 秒内）[SEVI]
**R5-4（FMA/向量 FP 高危）**：FMA 占向量 SDC cases >75%、incidents >92%；vfm（vector fused multiply）失败率最高 → 检测按硬件单元覆盖优先，FMA/向量 FP 是最高优先级探针 [SEVI, PinDrop, Veritas]
**R5-5（持续测试必要性）**：if 仅做 snapshot 式一次性测试 → 必漏间歇/晚发/低频/磨损类缺陷（PinDrop：机器可于首测近 4 年后才首败；每季度 0.0024% 新增失败机器；Ripple：23%+7% 覆盖仅为两种模式各自独有）→ 判定体系必须内建"持续重测" [PinDrop, Ripple]
**R5-6（复发是常态）**：>71% 失败机器随后 ≥2 年持续稳定失败（单机重复而非随机扩散）→ 复发支持硬件归因；但存在"自愈"异例（119 次失败后 59k+ 测试零失败）与晚发案例 → 单次窗口无失败不能排除 [PinDrop]
**R5-7（晚发与磨损）**：if 机器在长期运行后新开始失败 → 硅退化（比传统 bathtub 更早显现），"今天正确不保证明天正确" [Ripple, PinDrop]

---

## 2. 结构→症状先验表（从症状反查可疑部件）

SDC 诊断的核心先验：**故障位置的结构语义（控制流载体 vs 数据通路载体）× 保护状态 × 负载倾向 → 症状类型**。

### 2.1 微架构结构先验（SDC 概率 = 该结构故障导致 SDC 的比例）

| 结构/部件 | SDC 倾向 | 症状签名 | 来源 |
|---|---|---|---|
| **L1D data（无 ECC）** | **最高**：53.4%；permanent 达 5–71% | SDC 主导，SDC 是其余类别之和的 3–5 倍 | SDC-μArch, ITC2023, MaFIN/GeFIN |
| **向量 FP 加/乘单元** | **最高**：GEMM 98.7%、sparse 97.4%、SVD 45–62%；fleet 相对 scalar adder 高达 3 个数量级 | 数值/线性代数负载下错误几乎必然进入输出 | ETS2024, Veritas |
| L1D tag | 38.0% | SDC 偏高但 crash 也多 | SDC-μArch |
| L2 data | 36.9%（有 ECC 时转为 CE/DUE） | 混合 | SDC-μArch |
| DTLB data | 22.2% | 偏 DUE（crash AVF ≈50%），SDC<1% | SDC-μArch, Arm 芯片实测 |
| 物理寄存器堆 | 注入真值 0–9.9%（ACE 上界 25–30% 高估 3–7×） | crash 偏多 | MeRLiN, ITC2023 |
| 标量整数加法器 | SDC 仅 0–18%（crash >80%） | **SDC 必然伴随极低 BER（~10⁻⁴）**——高烈度错误自我暴露为 crash | Gates-to-SDCs, Veritas |
| 标量乘法器 | SDC 5–20%，掩蔽高于加法器 | 软件常丢弃 64 位乘积高位 | Gates-to-SDCs |
| L1I data | 7.3% | crash 主导（非法指令） | SDC-μArch, CHAOS |
| L1I tag / ITLB | ≈0.2% | 几乎必 crash/DUE | SDC-μArch |
| **ROB / LQ / SQ** | **0%**（架构级兜底：依赖图检查在 commit 前失败） | 必 crash 或 benign | SDC-μArch, MaFIN/GeFIN |
| TLB（整体） | SDC <1%，DUE 为主（crash ≈50%、hang ≈10%） | — | Arm 芯片实测 |
| 主存数据 | SDC/Masked 主导，crash 可忽略 | 随机命中关键数据概率低，**最难靠崩溃察觉的 SDC 源** | CHAOS |
| 分支预测器/BTB | AVF = 0（纯性能结构） | 只影响性能 | Mukherjee MICRO-03 |

### 2.2 指令/数据语义先验

| 受损数据的语义角色 | 症状 | 来源 |
|---|---|---|
| 地址/指针/索引/栈（ret/call/push/pop/leave） | 几乎必 crash（segfault/kernel panic），绝不 SDC | Gates-to-SDCs, GemFI, MARVEL(BFS RegBank) |
| 纯数据值（流向输出的数据、FP/向量运算） | SDC 主导（MARVEL：FFT SPM 45% 全 SDC） | MARVEL, Veritas |
| opcode/指令编码 | illegal instruction → crash（未实现编码）；unused bits → 必 masked | GemFI |
| 指令位移量/基址寄存器选择 | segfault 为主；decode 阶段错误通常演变为 SDC | GemFI |
| load/store 数据值 | 78% 结果正确（高韧度），仅破坏地址性数据才 crash | GemFI |
| 输出驻留缓存行（ESC） | 必然 SDC，不经程序流 | SVS |

### 2.3 fleet 级基线数字（先验概率校准）

| 量 | 值 | 来源 |
|---|---|---|
| CPU 缺陷率 | ~1/1000（1000 DPPM；PinDrop 精确测得终身失败率 0.035% ≈ 1/2850） | Harpocrates, PinDrop |
| crash : SDC（fleet） | ≥ 2–3 : 1 | Veritas/Meta |
| SDC 事件频率 | 10 万 SoC @10 FIT → 每月 ≥1 次 | IOLTS23 |
| 新指令首发代 | 失败率最高，后续代下降（vendor QA 迭代） | PinDrop |
| 位翻非 IID | multi-bit 常见（向量场景 multi > single）；同 setting 固定 mask（>5% 记录同 mask 即成 pattern） | PinDrop, SOSP23 |
| 浮点位翻位置 | 集中在 fraction（f64 99.9% 误差 <0.02%）——精度阈值类检测失效；但指数位可翻（相对误差达 10240） | SOSP23, SEVI |

---

## 3. 跨层协同判定规则（诊断核心）

### 3.1 证据类型学

- **E+（正证据）**：直接指示硬件错误——重执行不一致、双执行分歧、golden diff、差分测试失败
- **E−（负证据）**：排除性证据——零 EDAC 记录（排除受保护阵列）、软件确定性复现（排除硬件）、SEL 静默（排除 loud 故障）
- **ELOC（定位证据）**：core ID 聚集、单物理核 sibling 同败、失败指令 PC、位翻 mask 模式
- **ET（时间证据）**：跨天复现、温度相关、晚发、持续失败史

### 3.2 协同规则集

**SYN-1（硬件归因成立的最小证据组合）**
```
if (L4: 确定性重放跨核比对不一致 ∨ L2: 双执行不一致 ∨ L5: 专用测试跨天复现)
   ∧ (L3: 零 EDAC/SEL 硬件遥测)
   ∧ (L4: 症状跨应用/跨 workload 复现，或与特定指令族强绑定)
→ 判定：硬件 SDC（高置信）
→ 下一步：按 §2 先验表 + ELOC 证据定位可疑单元/core
```
依据：Orthrus R4-1（跨核比对天然排除软件）+ Sentinel R3-1（静默性）+ SiliFuzz R5-1（跨天复现）。

**SYN-2（软件原因排除规则——先于硬件归因执行）**
```
if (相同输入 ∧ 相同软件栈) 下错误确定性复现（每次都在同一点以同样方式出错）
   ∧ 换核心执行症状不变
→ 判定：软件 bug / 数据本身已坏，排除本机硬件归因
```
依据：Orthrus——软件 bug 在两次执行中同样复现、比对一致不报警。**注意反向不成立**：换核症状消失 ≠ 软件原因（单物理核缺陷正是换核即消失，见 SYN-4）。

**SYN-3（负证据定罪：无保护单元指向）**
```
if L4 SDC 症状 ∧ L3 全程零 EDAC/CE/SEL 记录
→ 排除：ECC 保护阵列（L2/L3、ECC 内存）
→ 嫌疑收窄至：功能单元（ALU/FPU/向量单元，通常无 ECC）＞ 无 ECC 的 L1D ＞ 流水线逻辑
→ 结合负载指纹细化：数值/向量负载 → 向量 FP 单元；通用负载 → L1D data
```
依据：ETS2024（FU 无 ECC 是 SDC 无缓释来源）+ Veritas（vector FP 是跨代首要嫌疑）。

**SYN-4（定位到物理核）**
```
if 同一物理核的两个 sibling 逻辑核同败且频率相近 ∧ 跨物理核不扩散
   ∧ (可选) 多个不同应用/测试在该核上失败
→ 判定：单物理核缺陷（62–89% 的 fleet 案例属此）
→ 处置：mask 该物理核（而非整颗退役），见 ACT-1
```
反例分支：if 失败均匀分布所有物理核 → 共享结构（cache）嫌疑 或 同型非共享组件每核皆缺陷 或（首要怀疑）**误报测试**——PinDrop 曾据此剔除 5 个 false-positive 测试；if transactional memory 类测试且无核亲和 → 跨核共享结构根因。

**SYN-5（温度/环境触发的归因与复现策略）**
```
if log(失败频率) 与核心温度线性相关（Pearson > 0.75）或存在最小触发温度
→ 判定：marginal/aging 类物理缺陷（L0 层根因）
→ 复现策略：加温/压制交替测试（Farron：自适应温度边界，实测 0.864 秒/小时压制 <59°C 即可触发）
→ 警告：工具链效率、测试顺序余热、其他核负载（共享散热）都会改变触发条件，复现实验必须记录完整环境状态
```
依据：SOSP23（MIX1 仅 >59°C 出错；最小触发温度与该温度下频率 log-线性 Pearson −0.83）。

**SYN-6（"校验通过"不可作为排除证据）**
```
if EC/CRC/校验和由向量指令加速计算 ∨ SDC 发生在 parity 计算之前
→ 校验器自身可被同一缺陷污染，校验和与已坏数据自洽
→ 必须引入与被检硬件物理隔离的校验路径（跨核/标量参考/软件校验）
```
依据：SOSP23 校验失效链。

**SYN-7（输出正确 ≠ 无异常：轨迹偏移规则）**
```
if 输出与 golden 一致 但 PMC/HPC 偏差巨大（成百上千 %）
→ 判定：隐蔽执行轨迹异常（故障破坏了控制逻辑但碰巧收敛到正确输出）
→ 状态：列入观察池，加严复测（这类机器可能间歇性恶化）
→ 反面警告：主存数据值型 SDC 在 HPC 上几乎无痕迹 → PMC 正常不能排除 SDC，输出校验不可省略
```
依据：CHAOS（Qsort L1D-SDC HPC 偏差 83,211% 但也观察到主存故障偏差 <0.3%）。

**SYN-8（传播阻断造成的假阴性）**
```
if 负载变更后症状消失
→ 不可据此排除硬件故障：同一故障在不同负载下表现不同
   (a) 软件掩蔽：错误数据被算法丢弃/覆盖（HVF 有 Corruption 但 AVF 为 Masked）
   (b) 覆写掩蔽：MARVEL 中输出 SPM 因持续被写而 AVF 远低于输入 SPM
   (c) 触发 context 不再出现：ITHICA——错误显现依赖前导指令序列
→ 处置：记录症状出现时的负载指纹，用原负载/原 seed 回放复现
```

**SYN-9（kernel/系统路径盲区规则）**
```
if SDC 定位到 syscall / 库 / kernel 代码路径
→ 应用层校验（重执行/CRC）不覆盖此路径（syscall 结果直接复用记录、库未插桩）
→ 必须由 L2 指令级检测（ITHICA 式全程序插桩）或 L5 专用测试补位
→ kernel 指令涉事的 SDC 无软件防护且占比可观（L1I tag 的 SDC 中 77% 来自 kernel）
```

**SYN-10（多缺陷判定与指令族交叉验证）**
```
if 仅凭单一指令族测试定位故障单元
→ 不可靠：同一缺陷可跨指令类型以相差 6 个数量级的速率致错（表面是 vector 缺陷，实为多类型受累）
→ 处置：多指令族证据必须交叉验证后才能锁定单元
```
依据：ITHICA Finding D1。

### 3.3 置信度分级

| 级别 | 判定条件组合 | 处置 |
|---|---|---|
| **确认（Confirmed）** | SYN-1 全部成立 ∧ 跨天复现 ∧ 已定位 core/单元 ∧ （金标准）厂商/独立 failure analysis 复现 | 隔离/退役 |
| **高度可疑（Suspect）** | SYN-1 成立但复现轮次不足，或定位证据不完整 | 深度测试（hammering、变温、多 context）、隔离观察 |
| **可疑（Candidate）** | 仅有单层证据（如仅 L4 输出异常，或仅 PMC 偏差） | 列观察池、提升测试 cadence、收集跨层证据 |
| **排除（Excluded）** | SYN-2 软件确定性复现成立，或症状确认为 loud 故障（有 SEL/EDAC 遥测，走 CE/UCE 通路） | 转入对应故障处理流程 |

---

## 4. 处置与运维规则（ACT）

**ACT-1（细粒度退役）**：≤2 个缺陷物理核 → 仅 mask 坏核复用其余核；>2 个缺陷核 → 退役整颗。一轮常规测试 1.02 小时（vs 基线 10.55 小时），总开销 0.017–0.145% [SOSP23 Farron]
**ACT-2（测试优先级三级）**：basic（每次必跑）/ active（suspected 候选机加跑）/ suspected（本机曾检出的用例最高优先）[SOSP23]
**ACT-3（测试多样性）**：91.4% 测试至少失败过一次、31% 测试曾是某机器唯一失败测试 → 测试族须覆盖算术/向量/浮点/cache coherency/事务内存/加密/并发锁全谱，不可只盯算术 [PinDrop, SOSP23]
**ACT-4（双轨持续测试）**：out-of-production（分钟级、全负载、93% 覆盖、5–6 个月周期）+ in-production（毫秒级、co-located、77% 覆盖、15 天快速收敛）必须并存——各自独有覆盖 23%/7%（silicon transition 类缺陷只有负载频繁切换才触发）[Ripple]
**ACT-5（corpus 反哺）**：坏机 snapshot/测试回填语料库（一台机器发现缺陷的测试在另一台有更高概率再发现）；每批测试换伪随机指令/数据序列以扩大输入空间 [SiliFuzz, IOLTS23]
**ACT-6（误报治理）**：持续识别剔除 false-positive 测试（指示全核失败的测试是首要嫌疑）；排除 fuzzer 类故意崩溃负载 [PinDrop, Sentinel]
**ACT-7（复现报告必备字段）**：失败 seed、core ID、温度/频率/电压快照、前导指令序列（execution context）、负载指纹、复现频率（次/分钟）——缺任一项的复现不可用于定案。

---

## 5. 诊断流程（判定规则的操作顺序）

```
第 1 步【L4 症状确认】
  输出/数据异常是否超出应用容差？（R4-4）超容差 → 继续；容差内 → 关闭。
  是否确定性复现？（SYN-2）是 → 软件流程；否 → 继续。

第 2 步【L3 静默性判定】
  SEL/EDAC/MCE 有记录？（R3-1/R3-4）有 → loud 故障，走 CE/UCE 流程；无 → SDC 流程继续。

第 3 步【L4/L2 硬件归因】
  确定性重放跨核比对（R4-1）或双执行插桩（R2-1）→ 不一致 = 硬件证据（SYN-1）。
  校验路径是否与被检硬件隔离？（SYN-6）未隔离 → 重做。

第 4 步【L5 定位】
  core 级失败分布（R5-2/SYN-4）→ 单物理核 / 全核 / 共享结构 三分支。
  跨天复现（R5-1）→ 定案或观察池。

第 5 步【L1 归因到单元】
  负载指纹 + §2 先验表 + 零 EDAC 负证据（SYN-3）→ 嫌疑单元排序
  （数值负载 → 向量 FP；通用 → L1D data；伴随 crash → 控制通路单元）。
  可选用 gem5-fi 注入映射表做"哪类注入能重现该症状"的反向验证。

第 6 步【L0 根因与复现】
  温度相关性（SYN-5）/ 输入位模式（R0-4）/ 晚发史（R5-7）→ marginal/aging/制造缺陷分类。
  短探针反复运行（Harpocrates：前 10% 指令即可检出 permanent 缺陷）+ 变温/变 context 复现。

第 7 步【处置】
  按 §3.3 置信度分级 + ACT-1 细粒度退役；corpus 反哺（ACT-5）。
```

---

## 6. 体系性盲区清单（判定规则必须显式声明的边界）

1. **consistent error**：两份冗余执行都错且错得相同 → 双执行类检测原理性盲区 [ITHICA]
2. **ESC 类**：输出驻留缓存直接被坏 → 绕过一切程序流内检测，输出写入前的缓存数据必须纳入校验 [SVS]
3. **masked error**：不改变输出的错误不可检（设计上可接受，但意味着"检测通过"≠"硬件无故障"）[Orthrus]
4. **主存数据值型 SDC**：HPC/PMC 几乎无痕迹，只能靠输出校验 [CHAOS]
5. **校验器自身污染**：向量加速的 EC/CRC 与数据同时受害 [SOSP23]
6. **软件层评估反推不可靠**：PVF/SVF 与全栈 AVF 结论相反的频率达 27–50%；软件加固可能因延长执行时间使真实故障率反升 30% [SVS]
7. **DUE 的核外低估**：互连/接口/OS 是 DUE 主源，微架构级注入只能给下界 [Arm 芯片实测]
8. **ECC ≠ 无 SDC**：延迟故障可致锁错行且 ECC 校验通过（DelayAVF）；多位翻超出 SECDED 单纠双检（SOSP23）
9. **"自愈"异例与晚发失败**：单窗口无失败永远不能证明无缺陷，判定体系必须建立在持续测试之上 [PinDrop, Ripple]

---

## 附录：来源论文索引

| 简称 | 论文 |
|---|---|
| Mukherjee MICRO-03 / IEEE Micro | A Systematic Methodology to Compute the AVFs…；Measuring AVFs |
| Biswas ISCA-05 | Computing AVFs for Address-Based Structures |
| Nair ISCA-12 | A First-Order Mechanistic Model for AVF |
| Bower SIGMETRICS-06 | Applying AVA to Hard Faults |
| MeRLiN ISCA-17 | MeRLiN |
| DelayAVF MICRO-24 | DelayAVF |
| Arm 芯片实测 TC-22 | Soft Error Effects on Arm Microprocessors |
| MaFIN/GeFIN IISWC-15 | Differential Fault Injection on Microarchitectural Simulators |
| CHAOS 2026 | CHAOS: Controlled Hardware Fault Injector System for Gem5 |
| GemFI DSN-14 | GemFI |
| MARVEL HPCA-24 | Gem5-MARVEL |
| ITC2023 | Estimating the Failures and Silent Errors Rates of CPUs Across ISAs… |
| SVS ISCA-21 | Demystifying the System Vulnerability Stack |
| Gates-to-SDCs DATE-25 | From Gates to SDCs |
| SDC-μArch TC-23 | Silent Data Corruptions: Microarchitectural Perspectives |
| IOLTS23 | SDC: The Stealthy Saboteurs of Digital Integrity |
| Veritas HPCA-25 | Veritas |
| SEVI ASPLOS-26 | SEVI |
| PinDrop HPCA-26 | PinDrop |
| SOSP23 | Understanding SDC in a Large Production CPU Population |
| Ripple | Fleetscanner/Ripple |
| SiliFuzz | SiliFuzz |
| Sentinel ASPLOS-25 | Hardware Sentinel |
| Vega ASPLOS-24 | Proactive Runtime Detection of Aging-Related SDCs |
| ITHICA | ITHICA |
| Orthrus SOSP-25 | Orthrus |
| Harpocrates ISCA-24 / IEEE Micro-26 | Harpocrates 两版 |
| PMC-SpMV | Detecting SDC in Sparse Matrices using HPC |
| ETS2024 | SDC in Computing Systems: Early Predictions and Large-Scale Measurements |
