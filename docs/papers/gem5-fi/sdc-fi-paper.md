# ARM64 服务器 CPU 微架构级 SDC 注入、规律刻画与抗 SDC 设计闭环：以鲲鹏 920（TaiShan V110）为例

> **数据溯源声明**：本文每个数字均可溯源到 `artifacts/<campaign>/` 下的 `cells.csv`/`summary.md`（强制入库）或 commit message 中引用的真实 gem5 输出。所有 P_SDC 是 gem5 O3 代理条件概率，**非产品 FIT**。

## 摘要

静默数据损坏（SDC）在真实舰队的发生率比传统软错误模型高约三个数量级（Meta ~1/1000 设备、Alibaba 3.61‱、PinDrop 0.035%），但现有注入工具（LLFI/FIJI/原版 CHAOS）停留在架构态与位翻转层，无法触达乱序服务器核的物理寄存器堆（PRF）、重命名表（RAT）、store→load 转发等 SDC 主要暴露面。本文以鲲鹏 920（TaiShan V110）为目标，构建 **gem5-fi 注入平台**：17 个微架构注入器、F1–F6+PCE 七类故障模型（含 F5 合法域替换——六载体全覆盖、F6 相位偏移、PCE post-check escape）、protection-aware 九类分类、FS checkpoint 流水线。在 V110 代理参数（C2-KP）下产出 4 组正式数据集：①L1D 风险反转（n=384/cell，raw escape vs secded 1-bit 100% Corrected）；②PRF 位段×ABI 角色（n=96/cell）；③LSQ 转发故障模式矩阵（n=64/cell）；④method1 状态泄漏两臂 Fisher 判定（n=384×2，p=1.19e-71 PASS）。基于 18+ 仿真-现场对照锚点（method1 历史残留 SDC、core179 D1/D2/D3 签名）确立生态效度，并给出抗 SDC 微架构设计建议（抗状态泄漏/抗相位/抗 PCE/抗合法域替换）与 openEuler 诊断反哺接口（位谱指纹库 CLI）。

## 1. 引言

SDC 的"三无"特征（无错误信号、无日志、无即时崩溃）使其成为数据中心最危险的硬件故障形态。ARM64 服务器核的 SDC 研究存在三个空白：(a) 现有 FI 工具不触达乱序后端物理状态；(b) 位翻转以外的故障模型（逻辑决策层替换、时序相位）缺失；(c) 仿真结果与现场签名缺乏对照生态效度检验。

本文贡献（对应 §2–§7）：
1. **17 个微架构注入器**（core179 三通路 D1/D2/D3 + method1 状态泄漏 RAT/freelist/ROB + method3 IQ/FP/相位 + PRF/Cache-ECC/Mem/TLB/SysReg/AddrPath/PTW + LSQFwd 五模式）——覆盖 P0–P3 全优先级单元；
2. **F1–F6+PCE 故障模型**，其中 F5（合法域替换）在六载体实现（RAT/freelist/LSQ/TLB pfnOffset/SysReg value_to_legal/Mem addr_map_sub），F6（相位偏移）经 LSQ phaseOffset + IQ src_ready 双载体；
3. **protection-aware 九类分类 + 风险反转**：raw escape 与 ECC 后逃逸分开报，L1D 正式数据（n=384）显示 secded 将 1-bit 逃逸 100% 转为 Corrected；
4. **仿真-现场对照生态效度范式**：18+ 锚点（含 method1 历史残留 SDC fails=1、core179 D1 撕裂移位 rol1 xor 多位散布、D3 spurious BecameInvalid）作为仿真忠实度的可证伪检验；
5. **抗 SDC 微架构机制建议**（抗状态泄漏双校验、抗相位护栏、抗 PCE 延伸保护、抗合法域冗余校验）；
6. **产业工具三件套**：gem5-fi 平台 + SDC 诊断指纹库 CLI（build/lookup）+ openEuler 七步诊断反哺接口。

## 2. 背景与现场动机

### 2.1 SDC 发生率基线
Meta ~1/1000 设备（Hardware Sentinel, ASPLOS'25）；Google mercurial cores（HotOS'21）；Alibaba 3.61‱（SOSP'23，100 万+ CPU/32 个月）；PinDrop 0.035% 生命周期（HPCA'26，5 亿+ 执行/12 年）——比 Baumann 2005 传统软错误模型（~1e-6）高约三个数量级。

### 2.2 现场证据（单机，诚实标注）
研究靶子来自单一故障机（Yangtze R240K V2，HIP08，4×48=192 核，cpu179）：
- **method1**（Cholesky x[0]）：损坏固定首元素，popcount 21–32 bit（非单 bit SEU）；numeric-only 失败率 1.0% ≈ 4× compute-both 0.27%（状态泄漏签名）；
- **method2**（x10 垃圾指针）：ESR 0x96000004（TF-L0），损坏源 `__per_cpu_offset` 高 32 位，-30mV 欠压可复现；
- **method3**（LSU 转发相位）：float 尾数 85%/double 93%/符号 0–1；一条 no-op ALU 使触发率 100%→10–20%；
- **core179 三通路**：D1 数据通路（字节旋转 rol1/rol6、全零交付）、D2 地址通路（byte7 清零）、D3 PTW 通路（73 例 spurious 翻译故障，RAS 全静默）。

**诚实边界**：现场数据未在第二台健康机复现（标"单机结果，未确认"）。

## 3. 方法：gem5-fi 注入平台

### 3.1 十九个注入器

（2026-09-07 收官状态：Phase 1 补全 cache 元数据/victim 写回、TLB 活页替换与 parity、RAT/ROB read-trace；Phase 5 补 CHAOSRAS 逃逸元分析与 ECC 逻辑故障模式。）

| 组 | 注入器 | 单元 | 模式 |
|---|---|---|---|
| core179 三通路 | CHAOSLSQFwd structuralFault | D1 数据通路 | byte_lane_skew rol1/rol6、all_zero |
| | CHAOSAddrPath | D2 地址通路 | byte7 清零（FS） |
| | CHAOSPTW | D3 PTW | bit_flip、clearValidBit（FS） |
| method1 状态泄漏 | CHAOSRenameMap | RAT | map_bitflip、f5_substitute、f4_field_stuck |
| | CHAOSFreeList | freelist | mark_free、pop_wrong |
| | CHAOSROB | ROB | entry_bitflip、exc_suppress、spec_leak（hook Rename::doSquash） |
| method3 | CHAOSIQ | IQ | src_ready_bitflip、tag_sub |
| | CHAOSFPU | FSU writeback | IEEE754 位段 result 翻转 |
| | CHAOSLSQFwd（五模式） | 转发 | bitflip（64 位）、fwd_source_sub、stale_line_replay、phaseOffset |
| 对照/基础 | CHAOSExec（阴性对照）| ALU | int result 位段 |
| | CHAOSPhysReg | PRF | phys/arch_frontend/arch_commit + F3 triggerValue + NEON lane |
| | CHAOSCache | L1D/L1I/L2 | 字节级 + targetField（rd/rn/rm/opcode 指令编码 + tag/valid/dirty/repl/coh 元数据 §5.8B）+ victim 写回载荷破坏（§5.8A）+ protectionModel ECC |
| | CHAOSMem | DRAM | addr_map_sub（F5）+ secded ECC + ecc_logic_fault（§5.11 E 机理——ECC 逻辑自身故障 1-bit 漏检） |
| 逃逸元分析 | CHAOSRAS | commit 路径 RAS 记录 | ERR* 记录抑制（S5-2——DUE 变无记录 SDC；完整转化 FS-only 诚实边界） |
| read-trace | CHAOSRenameMap/CHAOSROB | RAT/ROB | 注入后目标 physReg 消费者计数（H3 跨单元一致性前提 §4.3） |
| | CHAOSArmTLB | D-TLB/i-TLB | pfn/ap/xn/attridx/ng/asid 字段级 + pfnOffset（F5）+ pfn_to_mapped_page（F5 活页替换，最危险静默 SDC 路径）+ parity_interleaved（§2.3 L2 TLB 代理） |
| | CHAOSArmSysReg | 系统寄存器 | bitflip/stuck + value_to_legal（F5） |
| | CHAOSL1DForward | PCE | load result post-ECC 翻转 |
| | CHAOSBPU | BPU | target_sub/direction_flip（hook BAC::predict） |
| | CHAOSReg/CHAOSLSQFwd | 架构寄存器/转发 | 基线（64 位） |

### 3.2 故障模型 F1–F6+PCE
F1 单比特 / F2 局部多位 / F3 数据相关触发（triggerValueMask）/ F4 stuck-at（PRF write-path G2）/ **F5 合法域替换**（六载体）/ **F6 相位偏移**（LSQ phaseOffset 历史深度 + IQ src_ready）/ **PCE post-check escape**（CHAOSL1DForward）。

### 3.3 campaign 框架
六级/九类互斥分类（SimulatorError > Hang > Crash > Inactive > Masked > SDC + PA 分流 Corrected/DetectedContained/Latent）；Wilson 95% CI；fail_count oracle（accum/cholesky 的 fails=N）；C2-KP（V110 代理参数：ROB128/PRF160/192/LQ48/SQ42/4-wide/2.6GHz）；jobs=N 并行；FS checkpoint 流水线（boot→save_checkpoint→restore→Atomic 注入）。

## 4. 正式结果

### 4.1 L1D 风险反转：raw escape vs ECC contained（表 2）

n=384/cell × 6 cell（1/2/3-bit × raw/secded），l1d_reduce，2304 runs：

| cell | 结果 |
|---|---|
| raw-b1/b2/b3 | 100.0% Masked（raw escape——无 ECC 留脏未传播） |
| **secded-b1** | **100.0% Corrected**（1-bit 全部 ECC 纠正恢复） |
| secded-b2/b3 | 100.0% Masked（2/3-bit 毒化/逃逸但 byte 非活数据，PA 标记层已分流） |

**风险反转结论**：secded 将 raw 的 1-bit 逃逸 100% 转为 Corrected——§6.5 保护交互规律的核心正式确证。

### 4.2 PRF 位段×C2-KP（表 1）

X3（数据累加器）× 8 位段（bit 0/11/12/31/32/47/48/63）× n=96，C2-KP V110 代理参数下（768 runs，tables/t1-prf-bits.md）：

**X3 全 8 位段 SDC=96/96 P_SDC=1.000 [0.962,1.000]**（合计 768/768 [0.995,1.000]，0 Hang 0 Crash 0 Masked）——数据累加器的任意单 bit 翻转确定性传播为 SDC，正式确认"X3 所有位 SDC"（与 X2 循环计数器高位 Hang 的对照印证寄存器语义角色决定 SDC-vs-Hang 归宿）。

**read-trace n=384 复测**（4 代表位段 × 384）：SDC=1536/1536 P=1.000 [0.990,1.000]（CI 更紧）；reads_before_overwrite 中位数 **1,975,000**——X3 的注入值在被覆写前被读约 200 万次（状态泄漏窗口实测），P(SDC|reads>0)=1.000，四分类无 Benign/Masked（累加器全程活跃）。**窗口扫描**（ROB{96,128,160}×n=96）：X3 全位段与 X2bit0 保持 SDC=96/96、X2bit63 保持 Hang=96/96——P_SDC 处于饱和区，d(P_SDC)/d(ROB) 不可分辨（诚实边界：窗口敏感性需未饱和 cell 测出）。

### 4.3 LSQ 转发故障模式矩阵（表 3——T4 数据）

fp_fwd_kernel（asm back-to-back store→load）× 5 故障模式 × n=64（tables/t3-lsq-matrix.md）：**bitflip、structural（byte_lane_skew rol1，core179 D1 撕裂移位）、phase（phase_offset=2，F6 相位）SDC 率均 64/64=1.000**；**fwd_source_sub（F5 错源）与 stale_line_replay 为 Masked 阴性**（64/64，注入确认发生——numFwdSourceSub/numStaleLineReplay 计数=1——但 fp_fwd_kernel 的同址转发使替换源 ring buffer 内为等值数据，fails=0）。相位敏感性：|offset|≥1 即 100% SDC，与 method3 现场塌方机制（一条 no-op ALU 使触发率 100%→10–20%——相位错位破坏数据组装）方向一致。**诚实边界**：原计划的 fwd_7case 7 几何轴被废弃——其 volatile-no-barrier C 模式在 -O2 下不触达 gem5 转发路径（注入日志 0 字节），矩阵降为单几何 × 5 模式。

### 4.4 method1 状态泄漏 Fisher 判定（表 4——T5 数据）

F5 合法域替换（RAT 偷映射）× 长存活累加器（accum_kernel asm-pinned x9）× n=384 × 2 臂（numeric/compute-both，tables/t4-method1-fisher.txt）：

- **numeric-only：SDC=114/148，P(history_residue)=0.770 [0.696,0.831]**——偷映射读回 donor 值（method1"读回值=其它活变量"签名）；另有 232/384 注入后表现为 SimulatorError（F5 偷映射 → donor 值被用作指针 → SE 模式 page-table panic——method2 x10 垃圾指针形态在 gem5 SE 下的分类边界，如实报告）；
- **compute-both：SDC=0/266，P=0.000 [0.000,0.011]**——冗余重算（x10 独立累加交叉校验）**完全抑制**状态泄漏 SDC；
- **Fisher exact（单侧）p=1.189e-71 << 0.05，H-acceptance PASS**：`P(history_residue)>0` 且两臂差异极显著——method1 现场"compute-both 使 SDC 降 4×"的抑制方向正式复现。**诚实边界**：本代理下抑制比为 ∞（compute-both SDC=0），强于现场 [2,8] 区间——代理 kernel 的冗余路径单次注入无法同时命中两份累加，现场比值还包含多缺陷/重复触发因素；cholesky V0-V7 载体阴性（40 冒烟 runs 全 Masked——d0 短存活，偷映射在被读前被 rename 覆盖）一并入库作诚实对照。

### 4.5 生态效度锚点（表 5）

18+ 锚点全 pass（tables/t5）——含 golden f247ef3fe6f02cfd、GPR SDC d43a25d7fcc218b7（reads=125000 状态泄漏窗口）、method1 F5 fails=1、core179 D1 rol1 xor 多位散布、D3 PTW BecameInvalid、spec_leak numSpecLeak=3（PhysReg 104/105/106 跳过归还）、Mem addr_map_sub 0x100000→0x101000、TLB pfnOffset 0x403→0x40403 等。

### 4.6 FSU 位段×精度 formal（表 6——t3-1 新数据）

CHAOSFPU v3 源读 hook（背靠背依赖链走 bypass 网络，PRF cell 注入被转发击败——15 seed 全 Masked 的机理发现；读即破坏传播保证）下 n=384/cell：

| workload | sign | exp | mantissa | all |
|---|---|---|---|---|
| gemm_double | 18.0% | 17.2% | 13.6% | 15.9% |
| gemm_float | 65.8% | 61.5% | 60.2% | 62.5% |
| fma_reduction | 53.9% | 52.3% | 47.3% | 52.9% |
| svd_iterative | 67.2% | 65.0% | 65.1% | 69.5% |

规律：链式归约（fma 47–54%）比矩阵累加（gemm 13–18%）传播率高 ~3×（每次 fma 将误差乘操作数量级放大）；float 比 double 高 ~4×（FP32 尾数 23-bit 更窄，同等位翻转占比更大）；位段间差异有限（尾数低位误差被累加舍入吸收）。

### 4.7 保护优先级排序（表 7——t8 数据驱动版）

风险 = Reach×P_SDC 降序：L1D load 回填通路 90.9%（D 机理盲区，TRM 代理表无此行——最大覆盖差距）> L1D 阵列 raw 97.7%（secded 实测风险反转 97.7→0）> store→load wrong-source 37.6% > FSU 通路 13.6–18.0% > LSQ 转发 4.7% > PRF ~10% > DRAM B/C 静默 > DUE 主导组（IQ/ROB/RAT/freelist 0% SDC，免 SDC 代理保护）。

### 4.8 逃逸分解 B–F 补齐（表 8——t6 更新）

B（SED 2-bit 静默）384/384、C（≥3-bit 超 SECDED）384/384、D（post-check）90.9%、E（ECC 逻辑故障）同 seed 对照实证（secded=Corrected 0x0→0x0 vs ecc_logic_fault=Missed 0x0→0x80）、F（毒化传播）no data 诚实标注。

### 4.9 openEuler 诊断引擎（表 9——维度③ 落地）

三件套（tools/diag/）：ESR_ELx EC/FSC 解码器（pytest 7/7；core179 签名 0x96000044 → DABT/WnR=1/FSC=L0 精确匹配）+ 日志解析器（16 份真实 vmcore-dmesg：signature 子集 216/217=99.5% 收敛 CPU179、find_busiest_group+0x140 ×17 跨案复发）+ 七步法/P-N 规则/置信度引擎（core179 六案回放 → HIGH 置信度 P1-P5 全命中，处置=立即隔离+FA+RMA 精确复现 §7.8 结论；伪造均匀分布 → N1 正确排除）。指纹库↔诊断引擎集成 CLI（spectrum_triage.py）：现场位谱 → Top-K 候选单元（含 P_SDC 先验+签名检查建议）→ 日志侧裁决全链路。

## 5. 抗 SDC 微架构设计建议（机制级，非 DFT）

逃逸集合分解（tables/t6-escape-decomp.md，2026-09-07 B–F 补齐版）：A 机理 3282 事件（乱序后端 raw escape 确证）；B/C 机理 384+384 全静默（SED 家族边界）；D 机理 90.9%（PCE formal）；E 机理对照实证（ecc_logic_fault 1-bit 漏检）；F 机理 no data（deferred）。

1. **抗状态泄漏**（method1）：PRF 活性回收双校验（freelist 归还前强制校验不在活 RAT 映射——本平台 spec_leak numSpecLeak=3 证明该路径可被单点跳过）；squash 时错误路径 μop 的 PRF 写显式回溯；
2. **抗相位竞争**（method3）：store→load 转发决策与数据组装分离到不同流水级（一条 no-op ALU 使触发率 100%→10–20% 证明相位敏感）；AGU→MMU 地址呈现加 byte-lane parity（D2 签名 2/5 例确凿）；
3. **抗 PCE**：ECC 校验通过后到 PhysReg 写回之间的数据段加 parity 或与 ECC 联动（完整 RAM 保护把 SDC 逼到此必然出口）；
4. **抗合法域替换**：RAT physRegIdx、freelist free-bit、LSQ 转发源、TLB pfn 等编号/指针字段加 parity 或 range-check（本平台 F5 六载体的"合法域校验"反向证明硬件更应校验）；
5. **TRM 代理表差距**（tables/t9-trm-gap-analysis.md）：N1 Table 9-1 的最大盲区是覆盖范围而非保护强度——load 回填通路与 store→load 转发无对应行；ECC 逻辑自身是横向单点故障（BIST 建议）；5 项 E4（V110 RTL 推断）全部进待校准清单不进正文。

## 6. openEuler 诊断反哺接口

七步法（Top-N 筛选→重启检测→RAS 静默验证→核心浓度→异常加权→维修历史→FA 确认）+ P1–P11/N1–N10 规则 + 置信度四级（方案 §7）；位谱指纹库 CLI（`tools/sdc_fingerprint.py` build/lookup——现场 xor → Top-K 候选单元，lsq_fwd 指纹 mantissa_share=0.7121/popcount_median=16 与 method3 现场签名方向一致）；留一法验证（tables/t7-loo-validation.md，`tools/loo_validate.py`）：76 事件 Top-3 命中率 100%（≥60% 验收线 VALID），Top-1 34.2%（随机单 bit 多落 mantissa 区，区分度有限——诚实呈现）。

## 7. 有效性威胁

1. gem5 O3 ≠ TaiShan V110 RTL（统一 IQ ≠ 分布式四调度器；classic cache 无分区 L3；无 bufferless NoC）——绝对值标 E3；
2. 现场证据来自单一故障机，未第二台健康机复现（"单机结果，未确认"）；
3. 所有 P_SDC 是代理条件概率，无 raw device rate → 不换算 FIT。

## 8. 结论

gem5-fi 平台（19 注入器 + F1–F6+PCE + 九类 PA 分类 + FS checkpoint 流水线 + RAT/ROB read-trace）在 V110 代理参数下产出首批 ARM64 服务器核逐微架构单元 SDC 正式数据：① 逐单元量化（L1D 风险反转 100% Corrected、PRF 位段、LSQ 矩阵、method1 Fisher、FSU 位段×精度新数据）；② 逃逸机理分解 A–F（B/C/D/E 补齐，F 诚实 deferred）；③ protection-aware 保护优先级排序（t8 数据驱动版 + TRM 代理差距分析 t9）；④ 生态效度 18+ 仿真-现场锚点 + openEuler 诊断引擎三件套（ESR 解码/日志解析/七步法置信度——core179 六案回放 HIGH 置信度精确复现）+ 指纹库 CLI 端到端集成；⑤ read-trace 四分类（RAT/ROB 消费者计数，H3 跨单元一致性）。产业工具链（诊断引擎 + 指纹库 + DFT 向量包 dft/）全部开源可溯源（`artifacts/` 强制入库）。
