# 鲲鹏920（TaiShan V110，ARM64）微架构单元 SDC 故障注入与规律研究：方案设计、需求开发与实现文档

> **文档定位**：本文是鲲鹏 920 SDC 微架构故障注入与规律研究的**唯一权威工程方案文档**。它吸收并取代了《KUNPENG920-工程设计.md》，同时把《KUNPENG920-微架构SDC分析与故障注入方案.md》的风险分析落成**可编译、可运行、可复现、可验证**的工程蓝图；并深度集成 `sdc-diagnosis` 项目的《SDC诊断完整方法论.md》，形成"注入实验 → 规律提取 → 诊断规则反哺"的闭环。
>
> **四维度**（本文核心诉求）：① 微架构单元 SDC 故障注入研究；② SDC 规律研究；③ SDC 诊断建议（基于 openEuler 系统日志）；④ 对芯片开发设计者的改进建议。目标是同时服务于**顶级学术研究**（论文骨架与贡献点）与**产业应用工具**（SDC 诊断规则引擎 + 注入平台 + 位谱指纹库）。

---

## 第 0 章　文档定位与使用指南（AI 开发者元指令）

### 0.1 文档定位与取代关系

本文是三者合并后的**单一事实源**：

| 来源文档 | 处置 |
|---|---|
| 《KUNPENG920-工程设计.md》（1160 行） | **已吸收并取代**，正文第 1–11 章覆盖其全部有效内容，原文件删除 |
| 《KUNPENG920-的SDC…详细方案…md》（583 行） | **本文即为重构版**，第 0–4 部分内容同构并入第 0–6、10、11 章 |
| 《ARM微架构SDC分析与故障注入方案.md》 | 上游风险分析，本文引用其"为什么"，不重复其"风险清单"，保留入库 |
| 《SDC诊断完整方法论.md》（sdc-diagnosis 项目） | 第 7 章的规则依据，引用而非重写，7.9 节定义对接关系 |

### 0.2 三条强约束（贯穿全文）

1. **实事求是**：所有"已有/已验证"能力以 `fi-wangxu` 分支**实际源码**为准（本文写作时的合并基线与源码核对结论见 0.3 与附录 A）。凡标注"分支原型"的能力须注明当前是否已并入；凡"待新写"的能力绝不标注为已有。
2. **可落地**：每个新注入器给出 hook 文件与行号级位置、SimObject 骨架（Python + C++）、SConscript、挂载方式、验证命令与预期输出。沿用 `CLAUDE.md` 纪律：**一补丁一单元 + 提交前真机自验证**。
3. **诚实边界**：gem5 O3 ≠ TaiShan V110 RTL；SE 模式无 MMU-on 翻译（地址通路/PTW/系统寄存器注入必须 FS）；无 bufferless NoC / HCCS / 周期精确 L3；保护表用 N1 TRM Table 9-1 代理。每个结论标注证据等级 E1–E4（1.3 定义）。

### 0.3 分支与基线（fi-wangxu）

- 分支：`fi-wangxu` = 基于 `fi` 创建后合并 `main`（合并 commit `debbda3`），统一了两分支分裂的能力资产。
- **合并后真实注入器清单（8 个，源码核对）**：

| 注入器 | 目标 | 来源分支 |
|---|---|---|
| CHAOSReg | 架构寄存器（ThreadContext） | fi/main |
| CHAOSPhysReg | O3 物理寄存器堆（int/float/vector） | fi/main |
| CHAOSCache | classic cache 数据字节 | fi/main |
| CHAOSMem | AbstractMemory 后备存储字节 | fi/main |
| CHAOSLSQFwd | store→load 转发数据 | fi/main |
| CHAOSArmTLB | ARM D-TLB 命中表项 pfn | fi |
| CHAOSAddrPath | AGU 地址通路（P-D2） | main |
| CHAOSPTW | 页表走查器描述符（P-D3） | main |

- **关键诚实性修正**：`CHAOSArmSysReg`（ARM 系统寄存器 MRS 读值注入器）**在任何分支都不存在**。两旧文档曾将其标为"已有 + FS 真机验证"，属不实标注。本文统一修正为"**待新写**"，其历史验证描述删除；执行时先查 `progress.md` 是否留有历史会话记录，若有则复验后重新入库，否则从零实现（见 5.7、10.3）。

### 0.4 如何用本文档驱动 AI 开发

1. 每个"注入器/任务"在附录 G 有**任务卡模板**（YAML），含 `context/action/assert` 三段；`assert` 为**机器可判**的验收断言，全过才算完成。
2. 每个单元的 5.x 节固定 A–H 八段（目标与 hook / 注入器 / campaign 网格 / kernel / 指标与预期 / 边界与证据 / 工作量 / 验收断言）。
3. 执行顺序：第 10 章的分阶段计划 + 附录 G 的 `AGENT_TASKS.md` 行格式；Task S0-00（复验卡）完成前，任何后续卡不得开工。
4. 每补丁提交前必须完成 `CLAUDE.md` 三步自验证（干净构建 + 真机功能验证 + 不相关回归），并推送到 `fi-wangxu`（非 main）。

---

## 第 1 章　研究目标与问题定义

### 1.1 SDC 定义与"三无"特征

**Silent Data Corruption (SDC)**：处理器在**无任何即时错误信号**的情况下产生错误计算结果，该错误被上层软件正常使用并传播，最终导致数据丢失、一致性破坏或服务异常。"三无"特征：

- **无错误信号**：不产生 SError / SEA / ECC 等硬件级错误报告；
- **无日志记录**：SEL / RAS Error Records 中无对应硬件故障条目；
- **无即时崩溃**：应用不立即 crash，而是静默产生错误结果。

### 1.2 真实发生率（学术基线）

| 来源 | 报告发生率 | 说明 |
|---|---|---|
| Meta (2021) | ~1/1000 设备 | Hardware Sentinel [ASPLOS 2025] |
| Google (2021) | 每几千台机器数个 mercurial cores | Cores that don't count [HotOS 2021] |
| Alibaba (2023) | 3.61‱ | 100 万+ CPU、32 个月测试 [SOSP 2023] |
| PinDrop (2026) | 0.035% 生命周期内 ≥1 次 SDC | 5 亿+ 执行、12 年数据 [HPCA 2026] |
| 传统软错误模型 | ~1/1,000,000 | Baumann 2005 |

> **关键结论**：真实 SDC 发生率比传统软错误模型高约 3 个数量级。ARM64 在物理寄存器文件与 L1 数据缓存中的 SDC AVF 高于其它架构（Cross-ISA 论文），且 NZCV 条件标志、向量寄存器是 ARM64 独有脆弱点。

### 1.3 证据等级定义

| 等级 | 含义 |
|---|---|
| E1 | ISA/源码/TRM 直接支持 |
| E2 | 同平台受控实验（gem5 SE/FS） |
| E3 | 微架构代理模型（参数近似） |
| E4 | 依赖未公开实现细节，待实机/RTL 校准 |

### 1.4 研究目标

1. **逐单元 SDC 概率量化**：对微架构关键单元（PRF/RAT/freelist/ROB/IQ/LSU 转发/FSU/TLB/PTW/Cache/BPU 等）量化 `P_SDC / P_DUE / P_escape / Reachability`（Wilson 95% CI），raw 与 protection-aware 两组；
2. **SDC 规律研究**：位谱规律、传播规律、相位/时序规律、保护交互规律、跨单元敏感性排序（第 6 章）；
3. **SDC 诊断建议**：基于 openEuler 系统日志的七步法 + P/N 规则 + 置信度模型（第 7 章）；
4. **芯片设计建议**：逃逸集合分解 + 保护优先级排序 + DFT 测试向量 + 位谱指纹库（第 8 章）。

### 1.5 现场证据基线（本文实验的"靶子"）

| 案例 | 现场签名 | 指向单元 |
|---|---|---|
| **method1** | Cholesky → `x[0]` 多位混叠（21–32 bit）、"其它计算数据"覆盖、状态泄漏嫌疑；numeric-only 阶段 SDC ≈ compute-both 的 4× | RAT/freelist、ROB spec_leak |
| **method2** | 欠压 + STL → `x10` 垃圾指针 → ESR_EL1 `0x96000004`（level-0 翻译故障）→ panic | PRF 读出损坏（F3）、AGU、TLB |
| **method3** | LSU 转发时序相位竞争；位谱 float 尾数 85% / double 93% / 符号 562 次 0–1；SVD 单比特中位 1–3、GEMM double 中位 28 最大 39；加 no-op ALU → 触发率 100%→10–20% | LSU 转发（F5/F6）、IQ 唤醒相位 |
| **core179 六案** | 88 起事件 100% 收敛 CPU179、5/6 命中同一指令 `find_busiest_group+0x140`、零塌缩/撕裂移位两子族、RAS 全静默 | LSU 转发字节相位（H5） |

---

## 第 2 章　鲲鹏 920 微架构画像与 SDC 暴露面

### 2.1 TaiShan V110 关键参数（公开资料 + 第三方分析）

| 单元 | 参数 |
|---|---|
| 核心 | ARMv8.2-A，4-wide 超标量乱序，2.6–3.0 GHz，64 核/芯片，3-DIE Chiplet |
| 前端 | 4 发射解码；L1I 64KB/4-way/64B line/ECC；两级动态分支预测 + 64-entry BTB + 31-entry 返回栈；iTLB 32 项 |
| 乱序中枢 | PRF-based 重命名；分布式四调度器（每调度器约 33 项）；flag rename 约 31 项；支持 move elimination |
| 执行单元 | 3× 通用 ALU + 1× 复杂端口（乘除 4 周期）；双 FSU（FP32 FMA 2×128b，FP64 quarter-rate）；2× AGU |
| 访存 | L1D 64KB/4-way/64B/ECC，2×128b 访问/周期，hit load-to-use 4 周期；store 转发 6–7 周期，跨 16B 边界 +1–2 周期；dTLB 32 项全相联 + L2 TLB 1024 项（11 周期） |
| 缓存层次 | 私有 L2 512KB（10 周期）；共享 L3 最高 64MB，按 4 核 Cluster 切片，Tag 在 Cluster、Data 在 NoC 附近，Shared/Private/Partition 三模式（默认分区，约 36 周期） |
| 片上/片间 | 自研 bufferless 双环 mesh NoC（<15ns intra-die）；Die 间 HCCS 一致性（最高 400GB/s）；8 通道 DDR4-2933（≈187GB/s）；每 Compute Die = 1 NUMA 节点 |
| RAS | 指令/数据缓存 ECC、内存毒化隔离、PCIe AER、MCA、错误隔离（标称 99.999%） |

### 2.2 SDC 暴露面模型与单元分级

```
SDC 暴露面(单元) ≈ 未受保护状态位数 × (占用率 × 平均驻留周期) × P(错误传播到最终输出 且 逃过所有检测)
```

| 优先级 | 单元 | 暴露面评级 | 主要依据 |
|---|---|---|---|
| **P0** | PRF | 高 | 无保护（TRM 惯例）、高占用；method1/3 现场指向 |
| **P0** | RAT + freelist | 高 | 无保护；"映射张冠李戴/历史残留"对应 method1 核心假设 |
| **P0** | ROB + 按序提交 | 高 | 无保护；异常位/投机泄漏两类静默逃逸 |
| **P0** | LSU store→load 转发 | 中高 | 无保护；method2 位谱已定量吻合（100% 尾数/0% 符号 vs 现场 93/0/6） |
| P1 | 发射队列/调度器 | 中高 | 无保护；F5 错源、F6 相位竞态 |
| P1 | 浮点/向量执行（双 FSU） | 中高 | 无 ECC 概念组合逻辑；method3 位谱指向数据通路 |
| P1 | 地址翻译（L1 TLB/PTW/系统寄存器） | 中高 | L1 TLB 保守取无保护；method3 已定位 |
| P1 | L3（分区）/RAS 逃逸 | 中 | Tag/Data 分离、128B 故障域；RAS 逃逸元分析 |
| P2 | L1D/L2 数据通路 | 低中 | ECC 后逃逸窗口窄；重点 post-check escape |
| P3 | BPU | 低 | 预测错误被冲刷；重点"投机流是否泄漏" |
| P3 | 整数执行 ALU | 低 | Veritas：整数加法器 SDC 低几个数量级；阴性对照 |
| P2/P3 | 系统级（NoC/HCCS/内存控制器） | 中 | bufferless 无吸收、跨 Die 一致性；E3/E4 代理 |

### 2.3 保护覆盖基线（N1 TRM Table 9-1 代理）

华为不公开 V110 逐结构保护表 → 用同代同级 Neoverse N1 TRM Table 9-1 作代理（`protectionModel` 参数的语义依据，见 4.2）：

| 结构 | 代理保护 | 注入后处理逻辑 |
|---|---|---|
| L1I data | `sed` | 1-bit：行失效重取；≥2-bit：静默（可能 SDC） |
| L1D/L2 data | `secded_poison` | 1-bit：撤销（Corrected）；2-bit：毒化并传播（DetectedContained/Latent）；≥3-bit：静默 |
| L1D/L2 tag | `secded` | 1-bit：撤销；2-bit：invalidate + DetectedContained；≥3-bit：静默 false-hit |
| L1 iTLB/dTLB | `none` | 不处理，raw 即 escape |
| L2 TLB/walk cache | `parity_interleaved` | 1-bit：条目失效重走页表；同奇偶 2-bit：静默 |
| PRF/RAT/freelist/ROB/IQ/store buffer | `none` | 不处理，raw 即 escape |
| L2 victim/BTB/GHB/PHT/MMU 替换 | `none` | 不处理 |
| DRAM | `secded` | 同 L1D data |

---

## 第 3 章　SDC 故障模型定义与分类

### 3.1 F1–F6 + PCE 谱系表

| ID | 模型 | 定义 | 源码现状 | 实现方式 |
|---|---|---|---|---|
| F1 | 单比特瞬态 | 某一位翻转一次 | ✅ 已有注入器 | `faultType=bit_flip` + `faultMask=1<<k` |
| F2 | 局部多位 | 相邻 2/4/8 位同时翻转 | ✅ | `bitsToChange>1` 或多位 `faultMask` |
| F3 | 间歇突发 + 数据相关触发 | 仅当目标当前值匹配某位模式时注入（模拟欠压建立时间违例） | 部分（概率+多次有，数据相关触发无） | 新增 `triggerValueMask`/`triggerValuePattern` |
| F4 | stuck-at | 某位永久卡 0/1 | ✅ PRF 写路径（`setStuckTarget`）；其余仅"注入一次" | 补 write-path 钩子 |
| F5 | 合法域替换 | 换成**另一个合法值/编号**（逻辑决策层故障） | ❌ 全部需新增 | RAT→另一 physReg；freelist 活寄存器误标空闲；LSQ 转发源→另一 store；tag→同 set 合法 tag；TLB pfn→另一活页 |
| F6 | 延迟/遗漏代理（相位） | 唤醒/转发提前或推迟 N 拍 | ❌ 需新增 | IQ 唤醒 phaseOffset；LSQ 转发 phaseOffset |
| PCE | post-check escape | ECC 校验通过**之后**、数据进入流水线中被损坏 | ❌ 需新增 | `CHAOSL1DForward` |

**优先级**：F5 最高（对应 method1 核心假设），PCE 次之（完整 RAM 保护把 SDC 逼到 ECC 之后数据通路的必然出口）。

### 3.2 微架构单元 × 故障模型映射矩阵（逐单元见第 5 章）

（每个单元的"画像 → SDC 机理 → 故障模型表"在第 5 章相应小节展开，避免重复。）

---

## 第 4 章　统一实验框架（所有单元共用）

### 4.1 平台配置族

| 配置族 | 用途 | 关键参数 | 结论标签 |
|---|---|---|---|
| C0 方法学基线 | 注入器正确性、G0–G7 复检 | `arm_chaos.py` 默认 | "ARM64-gem5 baseline"，E2 |
| C2-KP 鲲鹏处理器 | 逐单元 SDC 量化 | 见下 `kp920_proxy` 参数块 | "Kunpeng-informed proxy"，E3 |
| C1 ARM64 架构 | ARM vs x86 同语义配对 | `x86_chaos.py` 镜像 C2-KP | "controlled cross-ISA"，E2 |

**C2-KP 的 O3 参数**（写入 `configs/se/kp920_proxy.py` 与 `configs/fs/kp920_proxy_fs.py`）：

```python
# TaiShan V110 4-wide OoO 代理（E3，非周期精确）
cpu.fetchWidth = cpu.decodeWidth = cpu.renameWidth = cpu.issueWidth = \
    cpu.dispatchWidth = cpu.commitWidth = 4          # 4-wide
cpu.numROBEntries      = 128       # 扫描 {96,128,160}
cpu.numPhysIntRegs     = 160       # 第三方估计 ~128–160；扫描 {128,160,192}
cpu.numPhysFloatRegs   = 192       # 向量/FP，双 FSU
cpu.LQEntries          = 48        # 深 LSQ（弱内存序）；扫描 {32,48,64}
cpu.SQEntries          = 42
cpu.numIQEntries       = 66        # ≈ 2×33（统一 IQ 近似四调度器，标 E3）
# FUPool：IntALU×3 + IntMultDiv×1(lat=4) + MemRead×2/MemWrite×2
#        + FloatMemRead + SIMD/FP×2（FADD lat=4, FMADD lat=7）
# 缓存：L1I 64KiB/4-way/64B；L1D 64KiB/4-way/64B；L2 512KiB/8-way 私有
clk = "2.6GHz"
```

> 诚实标注：gem5 统一 IQ ≠ V110 分布式四调度器；classic cache 无分区 L3 Tag/Data 分离；无 bufferless NoC。对应单元节标 E3/E4。

### 4.2 protection-aware 建模层

实现为 CHAOSCache / CHAOSMem / CHAOSArmTLB 的新参数 `protectionModel ∈ {none, sed, secded, secded_poison, parity_interleaved}`，注入后按下表决定"可观测归宿"（§2.3 表为完整语义）。每个 cell 跑两组：`none`（raw 上界）与 `<代理值>`（protection-aware 逃逸），报告两组并画风险反转图。**不换算产品 FIT**（无 raw device rate）。

### 4.3 结果分类与分母（沿用 `tools/classify.py`）

九类有序：`SimulatorError → Inactive → Corrected → DetectedContained → Crash/DUE → Hang → SDC → Latent → Masked`。

- `N_valid = N_total − N_inactive − N_simerror`；`P_SDC = N_SDC/N_valid`；`P_DUE = (N_crash+N_hang)/N_valid`；`P_escape = (N_SDC+N_latent)/N_valid`；`Reachability = N_valid/(N_total − N_simerror)`。
- **read-trace 四分类**（PRF/RAT/ROB 类）：`reads_before_overwrite=0` → Benign；`>0` 且输出不变 → Masked；`>0` 且输出变且无异常 → SDC；触发异常 → Crash。用于验证 `P(SDC∣reads>0)` 跨单元一致性（H3）。

### 4.4 campaign driver（`tools/campaign.py`）

网格驱动器：`injector / config / grid（笛卡尔积）/ n_per_cell / seeds(base 20260825 + cell_ordinal×1000 + rep) / protection_model / workload`。流程：展开 cells → 生成不可变 manifest → 调 `runner.py` 并发执行 → 收集九类分类 + read-trace + 位谱 + provenance → 每 cell 算 Wilson 95% CI + ≥5% 重放校验（不一致冻结）→ `artifacts/<campaign>/{heatmap.csv, summary.md}`。

### 4.5 manifest schema v2 扩展

- `target.component` enum 增补：`rat, freelist, rob, iq, exec, fsu, lsq_fwd, l1d_fwd, l1_tlb, l2_tlb, sysreg, ptw, l3, noc, coherence, memctrl, l1i, bpu, decode, exmon, ras`。
- `target` 增字段：`sub_field`（pfn/ap/asid；src_ready/dst_tag；map_entry/free_bit）、`semantic_role`（ABI 角色）。
- `fault` 增字段：`f5_substitute_target`、`f6_phase_offset`、`trigger_value_pattern`、`protection_model`。
- `dynamic_context`：`mapped_phys_reg, freelist_size, reads_before_overwrite, overwritten_at_cycle, cache_residency, lsq_source_seq, tlb_asid, committed_inst_at_inject`。

### 4.6 样本量设计

pilot 每 cell n=100（可达率/工具错误/粗略比例）；formal 每 cell n=384（最保守比例 95% Wilson ≈ ±5%）；关键低 SDC cell 扩 n=663（≈ ±3.8%）；0 SDC 时 95% 上界 ≈ 3/n。

---

## 第 5 章　逐微架构单元故障注入设计

> 每节固定八段：**A 目标与 hook / B 注入器 / C campaign 网格 / D kernel / E 指标与预期 / F 边界与证据 / G 工作量 / H 验收断言**。
> 单元按优先级 P0→P3 排序。注入器状态以 fi-wangxu 源码为准（8 个已有 + 13 个新写 + CHAOSArmSysReg 待新写，见附录 A）。

### 5.1 PRF 物理寄存器堆（P0，已有 CHAOSPhysReg 扩展）

**A. 目标与 hook**：整数/向量/flag 物理寄存器堆。Hook 已在 `regfile.hh`（读写 + read-trace + `setStuckTarget`）、`free_list.hh`（`isFree` 探活）、`cpu.hh`（`physRegFile()/frontRenameMap()/physFreeList()` accessor）。

**B. 注入器**：`CHAOSPhysReg`（已有）。扩展：`protectionModel`（占位 none）、F3 数据相关触发 `triggerValueMask/Pattern`（`processFault()` 读目标当前值，仅当 `(val & mask)==pattern` 时注入）、`semanticRole` 日志字段。

**C. campaign 网格**（`kp920_proxy.py`，SE，`--chaos_phys`）：

| 轴 | 取值 |
|---|---|
| 模式 | `phys` / `arch_frontend`（经前端 RAT） |
| 目标寄存器 | ABI 角色分层：X0–X7（参数/返回）、X9–X15（临时）、X19–X28（callee-saved）、X29/X30（FP/LR）、指针类（复现 method2 `x10`） |
| 位段 | bit {0,11,12,31,32,47,48,63} |
| 故障模型 | F1/F2/F4/F3（`triggerValuePattern` 扫 4 模式） |
| 向量 PRF | V0–V31 × lane {4×32b,2×64b,8×16b} × lane offset |
| 窗口扫描（H2） | ROB{96,128,160} × PhysIntRegs{128,160,192} × LQ/SQ{32/48/64} |

**D. kernel**：`reg_chain`（golden `f247ef3fe6f02cfd`）；新增 `ptr_chase_kernel`（链表遍历，复现 method2）、`cholesky_numeric_kernel`（method1，numeric-only/compute-both 两变体）。

**E. 指标**：`P_SDC/P_DUE`（Wilson）按 ABI 角色 × 位段 × 模式热图（预期：指针类→P_DUE 高；累加器类→P_SDC 高全位段；循环计数器→低位 SDC 高位 Hang）；read-trace `P(SDC∣reads>0)` 跨单元一致性（H3）；`reads_before_overwrite` 重尾性；method2 复现（F3 → `P_DUE` + ESR DFSC 分布 vs `0x96000004`）；method1 复现（numeric/compute-both ∈ [2,8]）。

**F. 边界**：E2。gem5 O3 PRF ≠ V110 PRF 几何（E3 绝对值）。

**G. 工作量**：CHAOSPhysReg 3 小补丁 + 2 kernel + campaign 配置。已有 pilot 证据（X2/X3 SDC 可复现），直接进 formal。

**H. 验收断言**：① `reg_chain` golden `f247ef3fe6f02cfd` 20 次重放逐位一致；② `probability=0` 时输出哈希与无注入基线逐位一致（锚点回归）；③ F3 `triggerValuePattern` 命中注入次数与 `fault_injections.log` 严格相等；④ pilot 每 cell n≥100 产生 ≥1 个非 Inactive 结局。

### 5.2 RAT + freelist（P0，新写 CHAOSRenameMap + CHAOSFreeList）

**A. 目标与 hook**：`frontRenameMap[tid]`（archReg→physReg）、`freeList`、move elimination、flag rename。Hook `rename_map.hh`（`rename()/lookup()/setEntry()`）、`free_list.hh`（`getReg()/addReg()/isFree()`）。

**B. 注入器**：新写 `CHAOSRenameMap` + `CHAOSFreeList`（自挂载）。骨架见附录 G（`map_bitflip`/`f5_substitute`/`f4_field_stuck`；`mark_free`/`pop_wrong`）。

**C. campaign**：RAT 模式 {map_bitflip(位域 0..log2(numPhysIntRegs)), f5_substitute, f4_field_stuck} × ABI 角色（重点长存活累加器）；freelist {mark_free, pop_wrong}；flag rename；move elimination。窗口同 §5.1。

**D. kernel**：`cholesky_numeric_kernel`（method1 主 kernel）+ 对照 `pure_fma/pure_spmv/pure_gather/tri_solve` + `mov_heavy_kernel`。

**E. 指标**：**历史残留专项** `P(history_residue)=N(读回值∈其它活变量值集合)/N_SDC > 0` 且显著（method1 核心，Fisher p<0.05）；损坏 popcount 中位数 >16（多位混叠，对标 21–32 bit）；read-trace 与 §5.1 对比（RAT 错是否为独立机制）。

**F. 边界**：E2。`SimpleRenameMap` 是 flat 表，V110 RAT 微结构未知（E3）。

**G. 工作量**：约 6 补丁。**与 method1 对照最直接，最大工具缺口。**

**H. 验收断言**：① kernel golden 各 20 次重放一致；② `f5_substitute`/`mark_free` ≥1000 次注入 `SimulatorError`=0（合法域校验）；③ pilot ≥1 个非 Inactive 结局。

### 5.3 ROB + 按序提交（P0，新写 CHAOSROB）

**A. 目标与 hook**：ROB 条目（result/done/exc_status/dest_phys/spec）、squash、commit RAT。Hook `rob.cc`（`retireHead()`/`squash()`/`doSquash()`）、`commit.cc`（`commitHead()`/`squashAfter()`）。

**B. 注入器**：新写 `CHAOSROB`。模式：`entry_bitflip`（field×distanceFromHead）、`exc_suppress`（清异常位→DUE 变 SDC）、`spec_leak`（squash 保留错误路径 μop 的 PRF 写，复现 method1 状态泄漏）。

**C. campaign**：mode × field{result,done,exc_status,dest_phys,spec} × 距提交距离 D{0,8,16,32,ROB_size−1} × 窗口{96,128,160}；`spec_leak` 需高分支密度 kernel。

**D. kernel**：`cholesky_numeric`（cdiv 制造投机）、`branchy_reduce_kernel`、`reg_chain`。

**E. 指标**：`P_SDC` vs D 曲线（预期单调，H2）；`exc_suppress` 的 `P(DUE→SDC 转化率)`；`spec_leak` 读回值命中率；read-trace `P(SDC∣reads>0)` 与 §5.1/5.2 对比（H3）。

**F. 边界**：E2；gem5 ROB squash 语义 ≠ V110 回滚状态机（E3 绝对值）。

**G. 工作量**：约 4 补丁。

**H. 验收断言**：① `cholesky_numeric` golden 20 次重放一致；② `entry_bitflip` 各 field×D cell ≥1 个非 Inactive；③ `exc_suppress`/`spec_leak` 不触达非法 ROB 索引（≥1000 次注入 `SimulatorError`=0）；④ `exc_suppress` 的 `P(DUE→SDC 转化率)>0` 且 `spec_leak` 联合观测 `P(读回值∈其它活变量值集合)>0`。

### 5.4 LSU + store buffer + store→load 转发（P0，扩已有 + 新注入器）

**A. 目标与 hook**：store buffer 数据、转发 CAM 匹配、转发源 seqNum、部分重叠拼接、AGU 有效地址、ready/replay、独占监视器。Hook `lsq_unit.cc` 转发数据（已有）、转发匹配决策点（新增）、AGU 地址生成（FS）。

**B. 注入器**：
- `CHAOSLSQFwd`（已有）扩展：mask 32→64 位（附录 D 的 D2）；结构化故障 `byte_lane_skew`/`all_zero` 已从 main 并入（H5 已验证），`stale_line_replay` 仅在 `FI_DESIGN_SUPPLEMENT.md` 文档化、**代码未实现需补齐**；F5 `fwd_source_sub`（待写）；F6 `phaseOffset`（待写，−2..+2）。
- `CHAOSAddrPath`（已有，main 并入，FS 已验证 `numAddrFaults=20`）：hook AGU 地址生成，破坏 vaddr（byte7 清零/低位翻转/F5 换址）。**SE 无效，FS 有效**。
- `CHAOSExMon`（新写）：hook 独占监视器 FSM，open↔exclusive 翻转。

**C. campaign**：转发数据 F1/F2/结构化（SE）；F5 转发源（SE）；F6 相位（SE）；AGU 地址（FS，checkpoint 后切 O3）；独占监视器（SE，LDXR/STXR）；F3 数据相关（SE）。

**D. kernel**：`fp_fwd_kernel`、`int_rmw_kernel`、`movbe_kernel`；method3 的 7 类定向构造（同址/部分重叠/4K 别名/双候选/未就绪 replay/DMB-DSB/LDXR-STXR，各"加/不加热路径 no-op ALU"两变体）；`ptr_chase_kernel`。

**E. 指标**（与现场对照最密集）：位谱（尾数/符号/popcount vs method3 的 85–93%/0–1/中位 3~28）；相位敏感性曲线（复现塌方）；method3 三必要条件复现（去 store 推进/同 LLC 域/跨 cache line 任一 → 归零）；method1 复现（F5 fwd_source_sub 损坏固定在结果向量首元素）；AGU byte7 的 FAR MSB=0x00 占比。

**F. 边界**：转发 E2；结构化 E2（H5 闭环）；AGU/PTW E2（FS 已证非零）；F6 相位 E3（gem5 发射时序 ≠ V110）。

**G. 工作量**：CHAOSLSQFwd 扩展约 4 补丁 + CHAOSAddrPath 补闸门 2 补丁 + CHAOSExMon 2 补丁 + method3 7 类 kernel 约 3 补丁。

**H. 验收断言**：① `fp_fwd_kernel` golden 20 次重放一致；② 64 位 mask 高 32 位翻转产生非零高位字节注入计数（H5 闭环）；③ F5 `fwd_source_sub` 仅指向当前转发表源（≥1000 注入 `SimulatorError`=0）；④ method3 三必要条件对照 cell（去 store 推进/同 LLC 域/跨 cache line）各 ≥1 非 Inactive；⑤ AGU byte7 清零 FS 下 `numAddrFaults>0` 且 FAR MSB=0x00 占比非空。

### 5.5 发射队列 IQ（P1，新写 CHAOSIQ）

**A. 目标与 hook**：src-ready 位、src-tag、dst-tag、唤醒广播、选择仲裁。Hook `inst_queue.cc`（`wakeDependents()`/`scheduleReadyInsts()`）。

**B. 注入器**：新写 `CHAOSIQ`。模式 `src_ready_bitflip`/`tag_sub`（F5）/`wake_phase`（F6 ±N）/`wake_omit`（F6）。

**C. campaign**：mode × 目标调度器{int,mem,fp} × 触发相位；与 `CHAOSLSQFwd` F6 **联合注入**复现 method3。

**D. kernel**：`movbe_kernel`/`int_rmw_kernel`/`dep_chain_kernel`。

**E. 指标**：相位敏感性曲线（复现 method3 塌方）；错源唤醒命中率；位谱。

**F. 边界**：E2/E3；gem5 统一 IQ ≠ V110 分布式四调度器。

**G. 工作量**：约 3 补丁。

**H. 验收断言**：① `dep_chain_kernel` golden 20 次重放一致；② `tag_sub`/`src_ready_bitflip` 仅触达当前合法 source tag（≥1000 注入 `SimulatorError`=0）；③ `wake_phase` ±N cell 相位敏感性曲线非平坦（≥1 非 Inactive）；④ 与 CHAOSLSQFwd F6 联合注入产生 ≥1 非 Inactive。

### 5.6 浮点/向量执行单元（双 FSU）（P1，扩已有 + 新写 CHAOSFPU）

**A. 目标与 hook**：向量 PRF（CHAOSPhysReg vector 已覆盖）、FSU 数据通路、FPSR/FPCR。Hook `iew.cc` writeback 按 `opClass ∈ {FloatAdd,FloatMult,FloatMultAcc,SimdFloat*}` 过滤。

**B. 注入器**：`CHAOSPhysReg` vector 模式（已有）；新写 `CHAOSFPU`（`result_bitflip` 按 IEEE754 位段 / `fma_intermediate` / `rounding_sub`(F5) / `fpsr_suppress`）。

**C. campaign**：位段{sign,exp_high/low,mantissa_high/mid/low} × 算子{FADD,FMUL,FMADD,reduction,shuffle,widen/narrow} × 精度{FP32,FP64} × {向量 PRF 存储/FSU 数据通路}两类分开。

**D. kernel**：`gemm_float/double`（复现 GEMM popcount 中位 12/28）、`svd_iterative`（单比特中位 1–3）、`neon_lane`、`fma_reduction_kernel`。

**E. 指标**：位谱（sign/exp/mantissa + popcount，直接对标 method3）；ULP/相对误差；lane×算子热图；归约放大系数；向量 PRF 存储 vs FSU 数据通路的签名可分性（KS 检验）。

**F. 边界**：E2（位谱可对照）；gem5 FSU 是功能模型（E3）；鲲鹏 128b ASIMD 无 SVE。

**G. 工作量**：约 5 补丁。

**H. 验收断言**：① `gemm_float/double` golden 20 次重放一致；② `rounding_sub`/`fpsr_suppress` 合法域校验（≥1000 注入 `SimulatorError`=0）；③ 位段×算子 cell ≥1 非 Inactive；④ GEMM popcount 中位与 method3 标称（12/28）同量级（KS 检验不拒绝）。

### 5.7 地址翻译（iTLB/dTLB/L2 TLB/PTW/系统寄存器）（P1，扩已有 + FS）

**A. 目标与 hook**：dTLB/iTLB 条目（pfn/AP/XN/AttrIndx/nG/ASID）、L2 TLB、PTW 在途状态、系统寄存器白名单。Hook 已有：`arch/arm/tlb.cc`（TLB hit）、`arch/arm/table_walker.cc doLongDescriptor`（CHAOSPTW）。**全部 FS 模式**（SE 无 MMU-on）。

**B. 注入器**：
- `CHAOSArmTLB`（已有）扩展：`pfn_to_mapped_page`（F5，翻到另一活页→静默 SDC）、`targetField ∈ {pfn,ap,xn,attridx,ng,asid}`、I-TLB 挂载、`protectionModel=none`。
- `CHAOSArmSysReg`（**待新写**，任何分支均不存在）：白名单 `ttbr0_el1,ttbr1_el1,tcr_el1,mair_el1,vbar_el1,contextidr_el1,nzcv`；`mode=bitflip/value_to_legal(F5)`。FS 模式。
- `CHAOSPTW`（已有，main 并入，FS 已验证 `numFaultsInjected=7963`）：hook `doLongDescriptor`，翻页表描述符；`ptwEcc` 参数（H7 自变量）。

**C. campaign**（FS，checkpoint 后切 O3/Atomic）：dTLB{pfn→未映射(DUE), pfn→活页(F5,SDC), AP, XN, AttrIndx, nG, ASID}；iTLB；L2 TLB；PTW{单 bit XOR+条件注入, clearValidBit}×{ptwEcc on/off}；系统寄存器{ttbr0/1,tcr,mair,sctlr,vbar,contextidr,nzcv}×{bitflip,value_to_legal}；method2 三根因区分（PRF/AGU/TLB 三种注入的 ESR/PC/x10 形态比对）。

**D. kernel**（FS）：内核调度域链表遍历（复现 method2 `find_busiest_group`）、context switch/fork-exec/页迁移、`ptr_chase`。

**E. 指标**："pfn→活页" cell 的 `P_SDC`（最危险路径）；"pfn→未映射" cell 的 `P_DUE` + ESR DFSC 分布 vs `0x96000004`；PTW ECC 对照（H7）；三根因匹配度打分；AP 位越权率；ASID 隔离违规率。

**F. 边界**：E2（FS hook 已证触发）。FS 慢 → checkpoint 策略必需。`CHAOSArmTLB` 时钟窗口 advisory 须修复（附录 D-D1）。

**G. 工作量**：CHAOSArmTLB 扩展 ≈3 补丁 + CHAOSArmSysReg 新写 ≈2 补丁 + CHAOSPTW 补闸门 + H7 formal ≈3 补丁 + FS checkpoint 流水线 2 补丁。

**H. 验收断言**：① FS checkpoint 后 golden 20 次重放一致；② `CHAOSArmTLB` firstClock/lastClock 时间窗修复后越窗注入计数=0（D1）；③ `value_to_legal`/`pfn_to_mapped_page` 仅指向活页/合法系统寄存器值（≥1000 注入 `SimulatorError`=0）；④ `pfn→活页` cell `P_SDC>0` 且 `pfn→未映射` cell `P_DUE>0`、ESR DFSC 与 `0x96000004` 可比；⑤ PTW `ptwEcc on/off` 对照 cell 差异显著（H7）。

### 5.8 Cache 子系统 L1I/L1D/L2/L3（P2/P1，扩已有）

**A. 目标与 hook**：数据字节（已有）、tag、valid/dirty/repl/coh、victim、post-check escape。Hook CHAOSCache 事件驱动遍历（已有）、victim `mem/cache/base.cc` WritebackBlk（新增）、post-check `lsq_unit.cc` load 回填（新增）。

**B. 注入器**：`CHAOSCache`（已有）扩展 `targetField ∈ {data,tag,valid,dirty,repl,coh,victim}` + `protectionModel`；新写 `CHAOSL1DForward`（PCE）；L3 短期用 `pairedSector` 代理（已有），完整 `CHAOSCHI`（Ruby/CHI）独立排期。

**C. campaign**：字段 × protection{none,secded_poison} × {随机/定向驻留} × ECC 粒度{1-bit,2-bit,3-bit}；L2 size sweep{256KiB,512KiB,1MiB}；L1I 语义字段{opcode,Rn,Rm,Rd,imm,cond}。

**D. kernel**：`l1d_reduce`、`l1i_loop`、`ptr_chain_kernel`、`struct_field_kernel`、`crc_state_kernel`。

**E. 指标**：raw vs protection-aware 风险反转图；post-check escape `P_SDC`（预期显著高于 raw）；tag F5 "读到同 set 别的行"命中率；L2 size 敏感性曲线；L1I SED vs SECDED 两组 `P_SDC` 差。

**F. 边界**：E2（chaoscache 锚点已验证）；华为保护类型未知（E3 映射）；无真实 ECC 逻辑（注入器内建模）。

**G. 工作量**：CHAOSCache 字段级+protectionModel≈3 补丁；CHAOSL1DForward 2 补丁；3 kernel。

**H. 验收断言**：① `l1d_reduce` golden 20 次重放一致（chaoscache 锚点）；② `targetField` 各字段（data/tag/valid/dirty/repl/coh/victim）≥1 非 Inactive；③ protection-aware `secded_poison` 下 raw vs protected 风险反转方向正确；④ `CHAOSL1DForward` PCE cell `P_SDC` 显著高于 raw（post-check escape 验证）。

### 5.9 分支预测 BPU（P3，新写 CHAOSBPU）

**A. 目标与 hook**：BTB 目标、GHB、返回栈、间接预测。Hook `cpu/pred/`（`BPredUnit::lookup()`/`BTB::update()`/`ReturnAddrStack`）。

**B. 注入器**：新写 `CHAOSBPU`（`btb_target_sub`/`ras_top_sub`/`indirect_target_sub`(F5)/`direction_bitflip`(F1)）。重点：**喂给后端的错误投机流是否泄漏**，联合观测（是否 squash/错误路径投机 store/squash 后架构态==golden）。

**C. campaign**：{BTB 目标,返回栈栈顶,间接目标,方向位} × 联合观测。

**D. kernel**：难预测分支循环 + 紧跟 store→load 依赖链（method1 cdiv+rank-1 交错）、`call_ret_heavy.c`、`indirect_jmp.c`。

**E. 指标**：`P(squash 后架构态==golden)`（预期≈1）；与 §5.3 `spec_leak` 对照（投机泄漏是否同一签名）。

**F. 边界**：E2；gem5 `TournamentBP` ≠ V110 两级预测器（E3）。

**G. 工作量**：约 3 补丁（可与 §5.3 合并一轮）。

**H. 验收断言**：① `call_ret_heavy`/`indirect_jmp` golden 20 次重放一致；② `btb_target_sub`/`ras_top_sub`/`indirect_target_sub` 仅指向合法目标地址（≥1000 注入 `SimulatorError`=0）；③ 联合观测 `P(squash 后架构态==golden)` 可计算且≈1；④ 每个 fault mode ≥1 非 Inactive。

### 5.10 整数执行单元（P3，新写 CHAOSExec，阴性对照）

**A. 目标与 hook**：ALU 结果、乘法器、移位器、NZCV。Hook `iew.cc` writeback 按 `opClass ∈ {IntAlu,IntMult,IntDiv}` 过滤。

**B. 注入器**：新写 `CHAOSExec`（`result_bitflip` 位段分层 [0:11]/[12:47]/[48:63]、NZCV 标志）。

**C. campaign**：opClass{IntAlu,IntMult,IntDiv} × 位段 × {结果,NZCV} × {bit_flip,stuck_at}。

**D. kernel**：整数 reduction、`MADD` 链、`SMULH`、`ADDS→B.cond` 条件链。

**E. 指标**：位谱；乘除端口 vs ALU `P_SDC` 比值；**阴性对照 `P_SDC(Int) << P_SDC(FSU/转发)`**（印证 method1 "整数路径完好" + Veritas 结论）。

**F. 边界**：E2；gem5 ALU 是功能模型（E3）。

**G. 工作量**：约 4 补丁。

**H. 验收断言**：① `MADD`/`SMULH` golden 20 次重放一致；② 位段分层 [0:11]/[12:47]/[48:63] 与 NZCV 均产生非零注入计数；③ 每个 opClass×位段 cell ≥1 非 Inactive；④ 阴性对照 `P_SDC(Int) << P_SDC(FSU/转发)` 成立（印证 method1 "整数路径完好"）。

### 5.11 PCE / 译码 / 系统级（S3/S4，依第 10 章排期）

- **PCE：L1D 返回通路**（`CHAOSL1DForward`，见 5.8）。
- **译码单元**（`CHAOSDecode`，P4，低优先级，可跳过）。
- **内存控制器 + DDR**（CHAOSMem 扩展 `addr_map_sub`/`ecc_logic_fault`，P3）。
- **RAS 机制逃逸**（`CHAOSRAS`，P1，元分析为主，见 8.1）。
- **系统级 NoC/HCCS/L3 一致性**（`CHAOSNoC`/`CHAOSHCCS`/`CHAOSCHI`，S4，E3/E4，独立子项目）。

---

## 第 6 章　SDC 规律研究

### 6.1 假设体系

| 假设 | 内容 | 状态 |
|---|---|---|
| H0 | 保护范围外结构（PRF/RAT/ROB/IQ/store buffer/L1 TLB）raw 即 escape | 预登记，待 formal |
| H1 | read-trace `reads_before_overwrite` 决定 AVF：`P(SDC∣reads>0)` 跨单元一致 | 预登记 |
| H2 | 深窗口（ROB/PRF 容量大）→ 驻留长 → SDC 高，`d(P_SDC)/d(window)>0` | 预登记 |
| H3 | RAT 错与 PRF 错走同一传播路径（F5 替换 vs 位翻转的 read-trace 一致） | 预登记 |
| H4 | 长驻留缓存（大 L2）→ 传播概率升高 | 预登记 |
| H5 | 字节相位（byte_lane_skew rol1/rol6）复现 core179 D1 签名 | **已闭环**（main，30 注入 28 检出 93%） |
| H6 | AGU byte7 清零 → 规范内核地址非规范化 → 翻译故障（FS 才有效） | **已闭环**（main，`numAddrFaults=20`） |
| H7 | PTW ECC on → spurious≈0 / off → spurious>0 | **已闭环**（main，5 seed：on 全 0，off 1–4） |
| H8+ | 新假设登记（本文起）：逃逸集合分解、相位敏感性、签名可分性 | 待 formal |

### 6.2 位谱规律

- **FP 尾数主导 / 符号免疫**：method2 现场 float 尾数 85% / double 93% / 符号 0–1/562；CHAOSLSQFwd `fp_fwd_kernel` 复现 100% 尾数 / 0% 符号。`bit_spectrum.py` 输出 sign/exp/mantissa/popcount。
- **popcount 分布**：SVD 单比特中位 1–3；GEMM double 中位 28 最大 39（多比特主导，PinDrop 证实"向量内多比特 > 单比特"）。
- **整数位谱**：整数数据 40.2% 案例有 >100% 精度损失（PinDrop）。

### 6.3 传播规律

- `reads_before_overwrite` 四分类把 AVF 分母拆细（Benign/Masked/SDC/Crash），`reads_before_overwrite=0` → Benign（AVF 分母）；`P(SDC∣reads>0)` 跨 RAT/ROB/PRF 的一致性验证（H1/H3）。
- 历史残留：F5 替换产生"读回值 == 其它活变量值"（method1 签名）。
- 暴露面公式（§2.2）验证：`Reachability × P_SDC × weight` 的分解。

### 6.4 相位/时序规律

- method3 触发率塌方：加一条 no-op ALU → 100%→10–20%；F6 `phaseOffset` 的 `P_SDC` 曲线应复现（`|phaseOffset|≥1` vs 0 比值 ≥5×）。
- 三必要条件：（store 推进 / 同 LLC 域 / 跨 cache line）去一归零。

### 6.5 保护交互规律

- ECC 前后对照（protectionModel）：1-bit→Corrected、2-bit→poison/Latent、≥3-bit→SDC；画风险反转图。
- post-check escape：ECC 校验后数据通路损坏完全不受保护。
- `CHAOSRAS` 元分析：RAS 逃逸率按逃逸机理 A–F 归因（§8.1）。

### 6.6 跨单元敏感性排序（学术定位）

本实验预期排序与已发表工作对照：

| 本实验单元 | 预期 | 对标论文 |
|---|---|---|
| LSU 转发 / FSU / PRF / RAT | 高 P_SDC | Veritas(HPCA'25)、Cross-ISA、PinDrop |
| 整数 ALU | 低 P_SDC（阴性对照） | Veritas（加法器低几个数量级） |
| L1I | 高 Crash（几乎总崩溃） | CHAOS |
| 系统级 | E3/E4 代理 | Gem5-MARVEL |

### 6.7 统计方法

Wilson 95% CI（scipy 独立复算误差 <1e-12）；重放一致性（G0，≥5% 样本重放）；0-SDC 上界 3/n；重尾检验（power-law 拟合）。

---

## 第 7 章　SDC 诊断建议（基于 openEuler 系统日志）

> 本章为用户明确要求的核心维度。**所有方法、规则、命令锚定 openEuler 系统日志形态**，将 `sdc-diagnosis` 的《SDC诊断完整方法论.md》规则操作化为 openEuler 上的日志解析 + 判定流程。

### 7.1 诊断目标与范围

- 目标平台：鲲鹏 920（ARMv8.2-A，64 核 TaiShan v110 同构）+ openEuler 22.03 / 24.03。
- 目标：从 openEuler 主机侧日志（无 BMC 硬件遥测依赖）出发，识别 SDC 诱导机，输出"高/中/低/排除"四级置信度，最终导向 FA（硅片故障分析）+ 隔离。

### 7.2 openEuler 数据源与采集

| 数据源 | openEuler 位置/命令 | 用于 |
|---|---|---|
| 内核环缓冲区 | `dmesg` / `journalctl -k` / `/var/log/messages` | ESR_ELx 解码、Oops、Data Abort、Undefined Instruction |
| 系统日志 | `journalctl --since "..."`、`/var/log/messages`（rsyslog 时间戳 `MMM dd HH:MM:SS`） | 异常时间戳、进程、backtrace |
| 重启记录 | `last reboot`、`who -b`、`journalctl --list-boots` | 非计划重启频率（Step 2/P3） |
| iBMC SEL | `ipmitool sel list/elist`（或 Redfish `curl /redfish/v1/.../SEL/Entries`） | RAS Error Records、CE/UE、SError/SEA |
| EDAC/rasdaemon | `/sys/devices/system/edac/mc/mc*/{ce_count,ue_count}`、`ras-mc-ctl --status`、ghes_edac | RAS 静默性验证（Step 3/P5） |
| GHES/APEI | `dmesg | grep -iE "arm64|ras|error|serror|sea|hisilicon|kunpeng"` | 硬件错误记录 |
| PMU | `perf stat -e armv8_pmuv3_0/...` | 微架构偏差（第 9 章监控场景复用） |

**openEuler 特有实证（core179 案例）**：`ESR 0x96000044`（DABT, WnR=1, FSC=L0 翻译故障）在 `/var/log/messages` 中以重复 `WARN`/`Oops` 记录；ghes_edac 注册 32 DIMM 零 CE/UE、rasnode.ko 192 核×5 ERR 节点全零差异——即"RAS 静默"的铁证。openEuler 对 spurious 翻译故障会保留 chronic 的 WARN 记录，是定位 SDC 的关键日志指纹。

### 7.3 日志解析规则

**ESR_ELx EC/FSC 解码表**（`dmesg`/`journalctl -k` 中标 `EC = 0x..`、`FSC = 0x..`）：

| EC | 异常 | 与 SDC 的相关性 |
|---|---|---|
| 0x00 | Undefined Instruction | 高（参考比率 17.80x） |
| 0x20/0x21 | PXN/UXN Permission Fault | 高（20.03x） |
| 0x24/0x25 | Data Abort（SP-relative 为高相关） | 高（20.77x） |
| 0x26 | Alignment Fault | 低 |
| 0x2F | SError | 取决于有无有效 RAS Record |
| 0x3C | BRK/BKPT | 中（6.92x） |

**异常类型加权表**（`SDC_score = Σ(类型次数×权重) + 核浓度加分 + 多应用加分 + 向量/NZCV 加分`）：

| 类型 | 参考比率 | 权重 |
|---|---|---|
| 嵌套 SError / 递归异常 | 59.35x | ★★★★★ |
| Data Abort (SP-relative) | 20.77x | ★★★★ |
| PXN/UXN Permission Fault | 20.03x | ★★★★ |
| Undefined Instruction | 17.80x | ★★★★ |
| SError 无有效 RAS Record | — | ★★★★ |
| BKPT/BRK | 6.92x | ★★★ |
| Data Abort（通用）/ Alignment / Lockups / Oops | ~1x | ★★/★ |

### 7.4 七步诊断流程（每步附 openEuler 命令）

```
Step 1 Top-N 候选筛选（按异常总量排序，workload-agnostic）
Step 2 重启异常检测（30天窗口：通用≥6次 / AI≥3次）
Step 3 RAS 静默性验证（排除响亮故障）
Step 4 核心浓度分析（单核>60% + 兄弟核聚合 + 多应用≥2 → 强 SDC）
Step 5 异常类型加权（ARM64 高相关类型加分）
Step 6 维修历史交叉验证（30天反复误诊/未诊 → 强 SDC）
Step 7 独立 FA 确认（目标复现率 70%）
```

**Step 1 Top-N**：`journalctl -k | grep -cE "ESR|Data Abort|Oops|Undefined|SError"` 按服务器汇总排序。

**Step 2 重启**：`last reboot | head -50`、`journalctl --list-boots | wc -l`（30 天窗口）；通用 ≥6 / AI ≥3 → 进入 Step 3。

**Step 3 RAS 静默**：

```bash
dmesg | grep -iE "arm64|ras|error|serror|sea|data.abort|hisilicon"
cat /sys/devices/system/edac/mc/mc*/ce_count
cat /sys/devices/system/edac/mc/mc*/ue_count
grep -i "serror\|SError" /proc/interrupts
ipmitool sel list | tail -100
```

判定：RAS Error Records 无 CPU 条目 → SDC 候选；SError+有效 Record → 响亮故障排除；SError 无 Record → SDC 候选；ECC 多比特 → 内存故障排除。

**Step 4 核心浓度**（最关键）：同构鲲鹏 64 核统一 60% 阈值；SMT 兄弟核聚合；多应用 ≥2。

```bash
# 按 CPU 号聚合异常（从 journalctl -k 解析出每次 Oops 的 CPU 字段）
journalctl -k | grep -E "CPU[ :]+[0-9]+" | awk '{...聚合 per-core count...}'
```

**Step 5 异常加权**：按 §7.3 权重矩阵计分。

**Step 6 维修历史**：查维修工单的误诊/未诊记录（30 天窗口）。

**Step 7 FA 确认**：第三方硅片 FA 复现。

### 7.5 正向规则 P1–P11 与负向规则 N1–N10

**铁律（IRON RULE）**：

- **P1 单核异常集中度**：1 周回溯内单核（或兄弟核聚合）异常占比 >60%（同构/big）或 >40%（little cluster）。鲲鹏 920 同构用 60%。原理：软件异常均匀分布，硬件缺陷集中单核。
- **N10 单次测试阴性不可靠**：PinDrop 证明快照测试遗漏一个数量级故障，机可能在测试多年后首次失败；SDC 测试有随机性，单次"通过"不代表健康。必须建 ≤30 天重访的连续测试机制。

**正向规则 P1–P11（每条约日志判据）**：

| 规则 | 条件 | openEuler 日志判据 + 命令 |
|---|---|---|
| P1 | 单核浓度 >60% + 兄弟核聚合 + 多应用 ≥2 | `journalctl -k | grep -E "……"` 按 CPU 号聚合集中度检验 |
| P2 | ≥2 应用在同一核心失败 | 崩溃进程名 ≥2 且同核心 |
| P3 | 30 天非计划重启通用≥6/AI≥3 | `last reboot` |
| P4 | 高相关异常类型同核出现 | §7.3 类型解码 |
| P5 | RAS 静默 | Step 3 命令全零 |
| P6 | 30 天反复误诊/未诊 | 维修工单 |
| P7 | 独立 FA 复现 | ≥70% |
| P8 | 向量指令 SDC 信号 | NEON 跨核对比不一致 |
| P9 | NZCV 条件分支异常 | 控制流偏离 |
| P10 | 失败持续性（≥2 季度持续失败） | PinDrop 连续测试 |
| P11 | 兄弟核共失效 | SMT 兄弟同时失败 |

**负向规则 N1–N10（命中任一即排除）**：

| 规则 | 条件 |
|---|---|
| N1 | 异常均匀分布 → 软件 |
| N2 | 单应用 + 相同 backtrace → 软件缺陷 |
| N3 | RAS 有明确 CPU 硬件故障 → 响亮故障 |
| N4 | fuzzer/测试工具引发 → 排除 |
| N5 | crash dump 有硬件诊断 → 非静默 |
| N6 | 已知 Bug/CVE 模式 → 软件根因 |
| N7 | 大规模同步异常 → 软件/配置变更 |
| N8 | 缺内存屏障 → 软件移植 |
| N9 | 环境瞬态 → 环境异常 |
| N10 | 单次测试阴性 → 不可靠，需连续测试 |

### 7.6 置信度模型

| 级别 | 条件 | 处理 |
|---|---|---|
| 高置信度 | P1+P2+P3+P5 +（P4 任一类型 / P8 / P9） | 立即隔离 + FA |
| 中置信度 | P1+P2+P5（缺 P4） | 增加测试覆盖/延长观察 |
| 低置信度 | 仅 P3 或 P6 | 标记观察，监控 CE/PMU |
| 排除 | 命中任一 N 规则 | — |

### 7.7 注入实验 → 诊断反哺

1. **位谱指纹库 → 日志签名匹配**：第 5/6 章每个单元的 SDC 位谱（sign/exp/mantissa/popcount）建成指纹库，供"现场看到某位谱 → 反推候选单元"（留一法验证，见 8.3）。
2. **单元 P_SDC → 类型加权**：formal 得到的逐单元 P_SDC/P_DUE 回填 §7.3 权重的先验，使权重矩阵有实验依据而非纯论文引用。
3. **method1/2/3 签名 → 规则库**：core179 的零塌缩/撕裂移位子族、ESR `0x96000044` 重复 WARN 等具体签名沉淀为规则，扩充 `sdc-diagnosis/skills/.../case_knowledge`。

### 7.8 实战示例：core179 六案全流程回放

- **事实**：88 起事件 100% 收敛 CPU179、5/6 命中同一指令 `find_busiest_group+0x140`、零塌缩（FSC=L3）/撕裂移位（FSC=L0）两子族、RAS 全静默（ghes_edac 零 CE/UE、rasnode 全零差异）。
- **规则命中**：P1（100% 单核浓度，远超 60%）+ P5（RAS 静默）+ P10 类（5/6 复发同指令）+ N3 未命中（无 RAS 条目）→ **高置信度 SDC** → 建议 offline + FA + RMA。
- **与注入对照**：`byte_lane_skew rot1`（H5）复现撕裂移位签名 93% 检出；`CHAOSAddrPath` byte7 清零（H6）复现零塌缩 FSC=L0 签名。

### 7.9 与 sdc-diagnosis 工具链对接

- 本文第 7 章是《SDC诊断完整方法论.md》的 openEuler 操作化落地；规则编号（P1–P11/N1–N10）、铁律标注、置信度分级保持一致，引用而非重写。
- `sdc-diagnosis/skills/sdc-diagnosis/` 作为规则引擎载体；本文 7.7 的反哺结果回写 `case_knowledge` 与 `case_records`，诊断规则需版本化（新增规则进 `rules/flight-rules.md` 时同步 bump 版本）。

---

## 第 8 章　对芯片开发设计者的改进建议

### 8.1 SDC 逃逸集合分解方法

跑完所有 formal cell 后，按逃逸机理（§6.5、Task S5）归因：

```
总 P_SDC(V110 代理, w) = Σ_unit [ Reachability(unit) × P_SDC(unit, w, protection-aware) × weight(unit) ]
weight(unit) ≈ 未受保护状态位数 × 占用率 × 平均驻留周期（gem5 stats 估计）

逃逸机理归因（每个 SDC 事件打标）：
  A. RAS 范围外结构（PRF/RAT/ROB/IQ/store buffer/L1 TLB/L2 victim）→ raw = escape
  B. SED-only 结构（L1I data 代理）的 ≥2-bit
  C. 任意结构 ≥3-bit（超 SECDED）
  D. post-check escape（ECC 后数据通路）
  E. ECC 逻辑自身故障（漏检/误纠）
  F. 毒化传播丢失
```

产出：逃逸集合分解饼图（按负载分组）+ 逐单元"保护投资回报"排序表。

### 8.2 保护优先级排序

| 结构 | 当前保护（代理） | 建议方向 | 依据 |
|---|---|---|---|
| PRF/RAT/ROB/IQ/store buffer | none（TRM 惯例） | **最高优先级加保护**（parity/dup）——RAS 范围外 + 高贡献重灾区 | method1/3 指向 |
| L1 TLB | none（flop 实现） | parity | method3 已定位 |
| L1I data | sed 代理 | 评估 SED→SECDED 对双比特静默的削减 | 5.8 SED vs SECDED 实验 |
| LSU 转发通路 | none | 转发数据校验 | method2 位谱吻合 |
| PTW | 视保护 | 读 ECC | H7（ECC on→spurious≈0） |
| L2 victim | none | 保护 | 5.8 victim 高于 data 预期 |

**预期结论方向**（待 formal 验证）：乱序后端（PRF/RAT/ROB）+ L1 TLB 是"RAS 范围外 + 高贡献"的重灾区，优先级高于再加固已有 SECDED 的缓存。

### 8.3 DFT/BIST 测试向量与位谱指纹库

1. **DFT 向量**：把复现 method1/2/3 的定向 kernel（`cholesky_numeric`、method3 7 类转发构造、`ptr_chase`）+ 触发条件（满载/特定发射相位/跨 cache line 推进）整理成量产筛选向量；附"健康核 vs 次品核"签名对照。
2. **位谱指纹库**：逐单元 × 负载的位谱存档，供扫描/现场故障的单元定位比对；留一法验证（20% SDC 事件预测来源单元，Top-3 命中率 ≥60% 即有效）。
3. **电压/相位敏感性数据**：F3 数据相关 + F6 相位的 `P_SDC` 曲线 → 量化"欠压 X mV 使某单元 SDC 率上升多少"，供电压裕量/AVS 设计。

### 8.4 与 Neoverse N1 TRM 保护基线的差距分析

逐结构对比 N1 Table 9-1 与 V110 推断保护表，标出差距清单 + 建议补齐项（E4 项进"待校准清单"，不进设计建议正文）。

---

## 第 9 章　学术研究与产业产出

### 9.1 论文骨架与贡献点

**标题方向**：《ARM64 服务器 CPU 微架构级 SDC 注入、规律刻画与诊断闭环：以鲲鹏 920（TaiShan V110）为例》。

**贡献点**：
1. 对 RISC 服务器核（非 x86）的逐微架构单元 SDC 暴露面量化（P_SDC/P_DUE/P_escape/Reachability + Wilson CI），raw 与 protection-aware 两组；
2. F5（合法域替换）+ F6（相位偏移）故障模型：把"位翻转以外的逻辑决策层故障"做成可复现注入原语；
3. protection-aware 分层 + 逃逸集合分解的规范（raw 敏感性 vs protection-aware 逃逸分开报）；
4. **仿真-现场对照生态效度范式**：位谱定量吻合（method2 93/0/6）、触发条件复现（method3 三必要条件）、负反馈复现（method1 4×）作为仿真忠实度的可证伪检验；
5. read-trace 四分类把 AVF 分母拆细，使 AVF/SDC 跨研究可对比。

### 9.2 目标会议与对标

DSN / PRDC / ASPLOS / HPCA / MICRO；对标 Veritas(HPCA'25)、PinDrop(HPCA'26)、SEVI(ASPLOS'26)、Cross-ISA、Differential FI、CHAOS、Gem5-MARVEL、DelayAVF(MICRO'24)、Harpocrates(ISCA'24)。

### 9.3 产业工具

1. **gem5-fi 注入平台**（本文第 4–5 章 + campaign 框架）；
2. **openEuler SDC 诊断规则引擎**（第 7 章规则 + `sdc-diagnosis` 工具链）；
3. **位谱指纹库**（§8.3）。

### 9.4 诚实的结论边界（写进论文与工具文档）

- 所有 `P_SDC` 是 gem5 O3 + C2-KP 代理下的**条件概率**，非产品现场 FIT；无 raw device rate → 不换算 FIT。
- 系统级（L3 分区/bufferless NoC/HCCS）结论 E3/E4，需实机/RTL/厂商资料校准。
- "最该加保护的结构"排序基于 N1 TRM Table 9-1 代理；若 V110 实际保护表不同则需重估。
- 单/多缺陷不可由仿真裁决；本方案主张的是"复现签名到可控环境 + 量化暴露面差异 + 提供 DFT 向量"。
- 本机（cpu179）为故障机 → 关键结果必须第二台健康机复现（Task S6-1）。

---

## 第 10 章　分阶段执行计划

### 10.1 阶段总览

| 阶段 | 内容 | 依赖 | 工作量 |
|---|---|---|---|
| S0 基础设施 | regen params 干净重建 + P0 pilot 复现；campaign.py；kp920_proxy 配置；manifest v2；protectionModel；已知缺陷修复（附录 D） | 无 | ~10 补丁 |
| S1 P0 单元 | PRF 扩/F3；RAT/freelist（CHAOSRenameMap/FreeList）；ROB（CHAOSROB）；LSU 转发扩/AddressPath | S0 | ~20 补丁 |
| S2 P1 单元 | IQ（CHAOSIQ）；FSU（CHAOSFPU）；TLB/SysReg/PTW + FS checkpoint；L3 pairedSector | S1 | ~18 补丁 |
| S3 P2/P3 单元 | L1D 字段级+PCE；L2+victim+size sweep；L1I 语义字段；整数 Exec；BPU；内存控制器 | S1 | ~16 补丁 |
| S4 系统级 | CHAOSCHI/CHAOSNoC/CHAOSHCCS（E3/E4，独立子项目） | S2 | ~20 补丁 |
| S5 元分析+建议 | CHAOSRAS + ras_escape_analysis；逃逸集合分解；DFT 向量 + 指纹库 | S1–S4 | ~4 补丁 |
| S6 健康机复现（贯穿） | 关键结果第二台健康机复现 | 每阶段 | — |
| S7 实机校准（授权后） | 鲲鹏实机 RAS/EINJ 枚举，E3/E4 升级 | 授权机 | — |

### 10.2 关键工程流水线

- **SE campaign**：`tools/campaign.py campaigns/<unit>.yaml` → 网格 → 每 cell n=384 → 单故障 → 九类分类 + read-trace + 位谱 + provenance → Wilson CI + 5% 重放 → artifacts。
- **FS campaign**（TLB/PTW/AGU/系统级）：Atomic boot → `m5 checkpoint` → restore 切 O3 → ROI 单故障 → 分类（raw socket 3456 抓 Linux 日志）。

### 10.3 任务清单（精简索引，详见附录 G 任务卡）

- **S0-6 已知缺陷修复**：CHAOSArmTLB 时间窗（D1）、CHAOSLSQFwd 64 位掩码（D2）、CHAOSMem 永久重放（D3）、CHAOSArmSysReg 时间窗（D4，**随新写一起做**）、拒绝比较统一（D5）、NULL 宿主 warn（D6）、mask==0 早退（D7）。
- **S1-1** CHAOSPhysReg F3+semanticRole；**S1-2** CHAOSRenameMap；**S1-3** CHAOSFreeList；**S1-4** CHAOSROB；**S1-5** CHAOSLSQFwd 扩展。
- **S2-3** CHAOSFPU；**S2-4** CHAOSAddrPath 补闸门；**S2-5** TLB F5 + **CHAOSArmSysReg 新写** + PTW formal + FS 流水线。
- **S3-2** CHAOSL1DForward；**S3-4** CHAOSExec；**S3-5** CHAOSBPU；**S3-6** CHAOSMem 扩展。
- **S5-2** CHAOSRAS；**S5-3** DFT 向量 + 指纹库。

---

## 第 11 章　质量闸门与验证纪律

### 11.1 注入器闸门 G0–G7

| 闸门 | 名称 | 现状 |
|---|---|---|
| G0 | 可重放性（同配置 20 次日志一致） | ✅ 已验证 |
| G1 | 64 位掩码 | ✅ Reg/PhysReg；⚠️ LSQFwd 待修（D2） |
| G2 | write-path stuck | ✅ 已验证 |
| G3 | cache 安全接口（getTags） | ✅ 已验证 |
| G4 | 内存边界/权重 | ✅ 已修复 |
| G5 | 单故障纪律 + 证据日志 | ✅ 已验证 |
| G6 | 最小注入间隔 | ✅ Cache/Mem；⚠️ 新注入器必须内置 |
| G7 | 零新增警告 | ✅ 常规；⚠️ ASan/UBSan deferred 到 CI |

### 11.2 补丁纪律（每任务通用）

1. 一补丁一单元；2. 提交前真机自测（三步自验证）；3. `make sync_chaos` 对齐双副本（Makefile:56–66）；4. 回归三件套（`prob=0` 对照 + 锚点哈希 + 零警告）；5. git 操作在 WSL 内执行（用户约定）。

### 11.3 文档与结论级验收

1. 每个结论挂 E1–E4，E4 不进设计建议正文；2. 每份 summary 复述三条诚实边界；3. 不换算 FIT；4. 未健康机复现的标"单机结果，未确认"；5. 阴性对照如实报告。

---

## 附录 A　注入器与 hook 点总表（源码核对版）

### A.1 已有注入器（8 个，fi-wangxu 源码实读）

| 注入器 | 目标单元 | Hook 位置 | 范式 | 优先级 |
|---|---|---|---|---|
| CHAOSReg | 架构寄存器 | 自调度 attackEvent | C（Python 显式） | 已验证 |
| CHAOSPhysReg | O3 物理寄存器堆 | `regfile.hh`（读/写 stuck）、`free_list.hh`（isFree） | B（状态注入） | P0 主力 |
| CHAOSCache | cache 数据字节 | 事件驱动遍历（`getTags()`） | C（`_pre_instantiate`） | P2/P1 |
| CHAOSMem | AbstractMemory 字节 | `AbstractMemory::access` Packet RMW | C | P3 |
| CHAOSLSQFwd | store→load 转发数据 | `lsq_unit.cc:1493-1502` | A（`cpu->lsqFwd`） | P0 |
| CHAOSArmTLB | D-TLB pfn | `arch/arm/tlb.cc:164-169` | A（`tlb->chaosTLB`） | P1（FS） |
| CHAOSAddrPath | AGU 地址 | `lsq_unit.cc`/`lsq.cc` translateTiming 前 | A | P1（FS） |
| CHAOSPTW | 页表走查描述符 | `arch/arm/table_walker.cc doLongDescriptor` | A | P1（FS） |

### A.2 待新写/待扩展注入器（13 新 + CHAOSArmSysReg 待新写）

| 注入器 | 状态 | Hook 位置 | 任务 |
|---|---|---|---|
| CHAOSRenameMap | 新写 | `rename_map.hh` rename()/setEntry() | S1-2 |
| CHAOSFreeList | 新写 | `free_list.hh` getReg()/addReg() | S1-3 |
| CHAOSROB | 新写 | `rob.cc` retireHead()/squash()/doSquash()；`commit.cc` commitHead() | S1-4 |
| CHAOSIQ | 新写 | `inst_queue.cc` wakeDependents()/scheduleReadyInsts() | S2-1 |
| CHAOSFPU | 新写 | `iew.cc` writeback（Float*） | S2-3 |
| CHAOSExec | 新写 | `iew.cc` writeback（Int*） | S3-4 |
| CHAOSL1DForward | 新写（PCE） | `lsq_unit.cc` load 回填（ECC 后） | S3-2 |
| CHAOSBPU | 新写 | `cpu/pred/` lookup()/BTB::update() | S3-5 |
| CHAOSExMon | 新写 | `lsq_unit.cc` 独占监视器 FSM | S3-7 |
| CHAOSArmSysReg | **待新写**（任何分支不存在） | `arch/arm/isa.cc` MRS 读路径 | S2-5 |
| CHAOSCHI | 新写（大） | Ruby/CHI 目录 + 响应通道 | S4-1 |
| CHAOSNoC | 新写（大） | Garnet flit/路由 | S4-2 |
| CHAOSHCCS | 新写（大） | 跨节点 CHI 事务 | S4-3 |
| CHAOSRAS | 新写 | `commit.cc` 异常提交 + ERR* 写路径 | S5-2 |

另有扩展模式：CHAOSMem `addr_map_sub`/`ecc_logic_fault`、CHAOSCache `targetField` 字段级、CHAOSDecode（低优先级）。

### A.3 宿主访问器（零新增所需）

`cpu->physRegFile()` / `physFreeList()` / `frontRenameMap()` / `commitRenameMapAccess()`（`cpu.hh:477-480`）、`cache->getTags()`（`cache.hh:160-176`）、`make sync_chaos`（Makefile:56–66）。

---

## 附录 B　现场案例对照实验索引

| 案例 | 对照任务 | 关键验收锚点 |
|---|---|---|
| method1（Cholesky `x[0]`） | S1-2/S1-3/S1-4/S1-5/S3-5 | 历史残留 P>0 且 Fisher p<0.05；popcount 中位 >16；numeric/compute 比值 ∈[2,8] |
| method2（`x10` 垃圾指针） | S1-1/S2-4/S2-5 | ESR DFSC 分布 vs `0x96000004`；AGU byte7 FAR MSB=0x00 占比；三根因签名打分 |
| method3（LSU 转发相位） | S1-5/S2-1/S2-3 | H5 复现 93%；位谱尾数∈[80%,100%]/符号∈[0%,2%]；相位塌方比 ≥5×；三必要条件去一归零；GEMM popcount 中位∈[8,40] |
| core179 六案 | S1-5（H5）/ S2-4（H6）/ S2-5（H7） | 撕裂移位（rol1）、零塌缩（byte7）、PTW ECC 对照 |

**公共纪律**：每个对照结论注明"gem5 代理复现（E2/E3）"而非"现场等同"；现场数据为既有事实，本方案只做"签名匹配度"评估。

---

## 附录 C　鲲鹏 920 微架构参数 → gem5 配置映射表

（与本文 §2.1 表 + §4.1 参数块对应，逐项标 E1/E3 证据等级。）

| V110 参数 | gem5 参数（kp920_proxy） | 等级 |
|---|---|---|
| 4-wide 发射 | fetch/decode/rename/issue/dispatch/commit=4 | E1 |
| ROB"规模适中" | numROBEntries=128（扫描{96,128,160}） | E3 |
| 每调度器 ~33 项 | numIQEntries=66（统一 IQ 近似，局限） | E3 |
| Int 物理寄存器 ~128–160 | numPhysIntRegs=160（扫描{128,160,192}） | E3 |
| 双 FSU | numPhysFloatRegs=192 + FUPool FADD lat4/FMADD lat7 | E3 |
| 3 ALU+1 复杂 | IntALU×3 + IntMultDiv×1(lat4) | E1 |
| LQ48/SQ42 | LQEntries=48/SQEntries=42 | E3 |
| L1I/L1D 64KiB/4-way/64B | classic size/assoc | E1 容量/E3 保护 |
| L2 512KiB | classic（sweep{256KiB,512KiB,1MiB}） | E1 容量 |
| L3 分区 Tag/Data 分离 | pairedSector（代理）/ Ruby CHI（S4） | E3/E4 |
| store 转发 6–7cy | CHAOSLSQFwd phaseOffset 实验域 | E3 |
| bufferless NoC | Garnet 偏转代理 | E4 |
| HCCS 400GB/s | 双 NUMA 代理 | E4 |

---

## 附录 D　现有实现已知缺陷清单（源码分析发现，须修复）

| # | 级 | 缺陷 | 位置 | 修复任务 |
|---|---|---|---|---|
| D1 | P0 | CHAOSArmTLB `firstClock/lastClock` 未检查 | `CHAOSArmTLB.cc` | S0-6 |
| D2 | P0 | CHAOSLSQFwd `faultMask` UInt32 且 `&0xff` 单字节 | `CHAOSLSQFwd.cc/.hh` | S0-6 |
| D3 | P0 | CHAOSMem `checkPermanent()` 重放一次后 update=false | `CHAOSMem.cc` | S0-6 |
| D4 | P0 | CHAOSArmSysReg 时间窗 1GHz 假设（该注入器整体待新写） | — | S2-5 |
| D5 | P0 | 拒绝比较不统一（`>` vs `>=`） | TLB/SysReg vs LSQFwd | S0-6 |
| D6 | P0 | CHAOSArmTLB NULL 宿主静默失败 | `CHAOSArmTLB.cc` | S0-6 |
| D7 | P0 | `mask==0` 不早退 | 多注入器 | S0-6 |
| D8 | P1 | CHAOSReg `maxRegIdx=0` 含 Zero/banked 项 | `CHAOSReg.cc` | 使用纪律 |
| D9 | P1 | G6 PC/committedInst/event 触发未实现 | 全局 | S0-5+后续 |
| D10 | P1 | G7 ASan/UBSan 构建受阻 | SConstruct | deferred 到 CI |

---

## 附录 E　openEuler 日志字段与诊断规则映射表

| openEuler 日志字段 | 解析出 | 驱动的 P/N 规则 |
|---|---|---|
| `EC = 0x..` / `FSC = 0x..`（dmesg/journactl） | 异常类型 | P4、Step 5 加权 |
| `CPU: N`（Oops 头） | 核心号 → 核心浓度 | P1、N1、Step 4 |
| `pc/lr/Call trace` | backtrace → 单应用判定 | N2、N6 |
| `last reboot` / `journalctl --list-boots` | 重启频率 | P3、Step 2 |
| `ipmitool sel elist` / EDAC count | RAS 条目 → 静默性 | P5、N3、Step 3 |
| `ESR 0x96000044` 重复 WARN | spurious 翻译故障（core179 指纹） | 反哺规则库 |

---

## 附录 F　术语表

| 术语 | 定义 |
|---|---|
| SDC / DUE | 静默数据损坏 / 检出不可纠正错误 |
| AVF | Architectural Vulnerability Factor |
| F1–F6 / PCE | 故障模型谱系（单比特/局部多位/间歇突发/stuck-at/合法域替换/相位延迟/后校验逃逸） |
| E1–E4 / G0–G7 | 证据等级 / 注入器质量闸门 |
| RAT / PRF / ROB / IQ / LSQ/LSU / FSU / AGU | 重命名表 / 物理寄存器堆 / 重排序缓冲 / 发射队列 / 访存队列单元 / 浮点单元 / 地址生成单元 |
| BTB / RAS(返回栈) | 分支目标缓冲 / 返回地址栈 |
| HCCS / HHA / CHI | 华为跨 Die 一致性 / Hybrid HA 目录 / ARM Coherent Hub Interface |
| SECDED / SED / poison | 单纠双检 / 仅检错 / 毒化标记 |
| protectionModel | 注入器代理保护参数（none/sed/secded/secded_poison/parity_interleaved） |
| campaign / cell / manifest / golden | 网格实验 / 参数组合点 / 参数冻结文件 / 无注入校验和基准 |
| read-trace / 历史残留 | PRF 读传播追踪 / method1"读回值=其它活变量"签名 |
| Wilson CI / pairedSector | 比例置信区间 / L3 128B 故障域代理 |
| method1/2/3 | 现场案例编号（Cholesky/x10 指针/LSU 转发相位） |

---

## 附录 G　AI 开发任务卡与"待新写"注入器 SimObject 骨架

> 本附录把第 5 章各单元 B 段引用的"骨架"与本文贯穿的"任务卡"落成**可被 AI 直接执行**的形态，兑现 0.2 的"可落地"约束（SimObject 骨架 + 挂载 + 验证命令 + 机器可判断言）。

### G.1 任务卡模板与 AGENT_TASKS.md 行格式

每个开发单元用一张 YAML 任务卡驱动，`assert` 为**机器可判**验收断言，全过才算完成。仓库内 `AGENT_TASKS.md` 用单行登记依赖与状态，编排器按拓扑顺序分发（S0-00 复验卡完成前，后续卡不得开工）。

```yaml
# 任务卡模板（示例：S1-2 CHAOSRenameMap）
id: "S1-2-CHAOSRenameMap"
title: "新写 RAT 注入器 CHAOSRenameMap"
context:
  unit: "RAT + freelist（P0）"
  hook: "cpu/o3/rename_map.hh: SimpleRenameMap::rename()/lookup()/setEntry()"
  host_accessor: "cpu->frontRenameMap()（cpu.hh）"
  branch: "fi-wangxu"
  evidence_level: "E2"          # O3 flat 表 ≠ V110 RAT，绝对值 E3
action:
  - "按 G.2 骨架写 CHAOSRenameMap.py / .hh / .cc / SConscript"
  - "模式 map_bitflip / f5_substitute / f4_field_stuck；自挂载"
  - "derive configs/se/kp920_proxy.py 增 --chaos_rename 开关"
  - "f5_substitute 仅指向'当前已分配 physReg'（合法域校验，防 SimulatorError）"
assert:
  - "make sync_chaos 后构建零新增警告（G7）"
  - "probability=0 时 golden 哈希与无注入基线逐位一致（锚点回归）"
  - "同 seed 20 次重放 fault_injections.log 完全一致（G0 可重放）"
  - "f5_substitute ≥1000 次注入 SimulatorError=0"
  - "pilot 每 cell n=100 产生 ≥1 个非 Inactive 结局"
```

**AGENT_TASKS.md 单行格式**：`<id> | depends=[<id>,…] | owner | status | assert_hint`

```
S0-00-复验卡          | depends=[]          | agent | pending | 附录 A"已有"项逐项复验通过
S0-06-已知缺陷修复     | depends=[S0-00]     | agent | pending | 附录 D 的 D1–D10 全绿
S1-01-CHAOSPhysReg扩展 | depends=[S0-06]     | agent | pending | F3 triggerValue* + semanticRole
S1-02-CHAOSRenameMap  | depends=[S0-06]     | agent | pending | 见 G.1 示例 assert
S1-03-CHAOSFreeList   | depends=[S0-06]     | agent | pending | mark_free/pop_wrong
S1-04-CHAOSROB        | depends=[S0-06]     | agent | pending | entry_bitflip/exc_suppress/spec_leak
S1-05-CHAOSLSQFwd扩展 | depends=[S0-06]     | agent | pending | D2 修复 + stale_line_replay 补齐 + fwd_source_sub
S2-05-CHAOSArmSysReg  | depends=[S1-02]     | agent | pending | 待新写（任何分支均不存在）
```

### G.2 待新写 P0/关键注入器 SimObject 骨架（Python 参数面）

> 以下为**参数面骨架（示意）**。`cxx_header`/C++ hook 位置以当前 vendored gem5 版本为准；C++ 侧要点在各骨架后以"实现要点"注明，非最终代码。闸门参数（`firstClock/lastClock/maxFaults/rngSeed/writeLog`）遵循既有注入器统一约定。

**① CHAOSRenameMap（RAT，S1-2）** — 复现 method1"映射张冠李戴"核心假设。

```python
from m5.params import *
from m5.SimObject import SimObject

class CHAOSRenameMap(SimObject):
    type = "CHAOSRenameMap"
    cxx_class = "gem5::CHAOSRenameMap"
    cxx_header = "cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh"

    cpu = Param.BaseCPU(NULL, "Target O3CPU")
    probability = Param.Float(0.0, "Per rename-map write probability of corruption")
    mode = Param.String("map_bitflip",
        "map_bitflip: 翻转 map 表项 physRegIdx 的某一位 | "
        "f5_substitute: 令 archReg K 指向另一'当前已分配'physReg | "
        "f4_field_stuck: 把某表项永久钉到错误 physReg")
    targetArchReg = Param.Int(-1, "目标架构寄存器 (-1 = 随机)")
    faultMask = Param.UInt64(0, "map_bitflip 位掩码 (0 = 随机一位)")
    firstClock = Param.UInt64(0, "最早可注入周期")
    lastClock = Param.UInt64(0, "最晚周期 (0 = 不限)")
    maxFaults = Param.UInt64(0, "最大注入次数 (0 = 不限)")
    rngSeed = Param.UInt64(0, "RNG 种子 (0 = random_device)")
    writeLog = Param.Bool(True, "写 fault_injections.log")
```

> 实现要点：hook `SimpleRenameMap::rename()`（架构寄存器 → physReg 写入点）；`f5_substitute` 只从 `freeList` 的"已分配"集合选目标，做合法性校验；写 `dest_phys` 语义随表项参与后续 `regfile` 读，故天然携带 read-trace（与 §5.1 共用四分类）。

**② CHAOSFreeList（freelist，S1-3）** — 复现 method1"活寄存器被误标空闲/历史残留"。

```python
class CHAOSFreeList(SimObject):
    type = "CHAOSFreeList"
    cxx_class = "gem5::CHAOSFreeList"
    cxx_header = "cpu/o3/CHAOSFreeList/CHAOSFreeList.hh"

    cpu = Param.BaseCPU(NULL, "Target O3CPU")
    probability = Param.Float(0.0, "Per alloc/free event probability")
    mode = Param.String("mark_free",
        "mark_free: 把仍在架构映射中的活 physReg 误标为空闲 | "
        "pop_wrong: 重命名分配时发一个'已活'physReg（双占用）")
    targetPhysReg = Param.Int(-1, "目标 physReg (-1 = 随机)")
    firstClock = Param.UInt64(0, "最早可注入周期")
    lastClock = Param.UInt64(0, "最晚周期 (0 = 不限)")
    maxFaults = Param.UInt64(0, "最大注入次数 (0 = 不限)")
    rngSeed = Param.UInt64(0, "RNG 种子 (0 = random_device)")
    writeLog = Param.Bool(True, "写 fault_injections.log")
```

> 实现要点：hook `PhysRegFile` 释放链路的 `addReg()`（freelist 回填）与分配 `getReg()`；`mark_free` 后旧占有者在被覆写前读回旧值 → 历史残留签名；`pop_wrong` 双占用需在写回时打 `dynamic_context.freelist_size`。

**③ CHAOSROB（ROB，S1-4）** — 复现 method1"投机流状态泄漏 + 异常位静默"。

```python
class CHAOSROB(SimObject):
    type = "CHAOSROB"
    cxx_class = "gem5::CHAOSROB"
    cxx_header = "cpu/o3/CHAOSROB/CHAOSROB.hh"

    cpu = Param.BaseCPU(NULL, "Target O3CPU")
    probability = Param.Float(0.0, "Per-injection probability")
    mode = Param.String("entry_bitflip",
        "entry_bitflip: 翻转某 ROB 条目字段 | "
        "exc_suppress: 清异常位→DUE 转 SDC | "
        "spec_leak: squash 时保留错误路径 μop 的 PRF 写")
    field = Param.String("result", "result | done | exc_status | dest_phys | spec")
    distanceFromHead = Param.Int(0, "距 ROB 头的距离 (0 = 头)")
    faultMask = Param.UInt64(0, "entry_bitflip 位掩码 (0 = 随机一位)")
    firstClock = Param.UInt64(0, "最早可注入周期")
    lastClock = Param.UInt64(0, "最晚周期 (0 = 不限)")
    maxFaults = Param.UInt64(0, "最大注入次数 (0 = 不限)")
    rngSeed = Param.UInt64(0, "RNG 种子 (0 = random_device)")
    writeLog = Param.Bool(True, "写 fault_injections.log")
```

> 实现要点：hook `retireHead()`/`squash()`/`doSquash()`（`rob.cc`）与 `commitHead()`（`commit.cc`）；`exc_suppress` 记录 `P(DUE→SDC 转化率)`；`spec_leak` 与 §5.9 CHAOSBPU 联合观测，验证投机泄漏是否同一签名。

**④ CHAOSArmSysReg（系统寄存器，S2-5，任何分支均不存在，待新写）**

```python
class CHAOSArmSysReg(SimObject):
    type = "CHAOSArmSysReg"
    cxx_class = "gem5::CHAOSArmSysReg"
    cxx_header = "arch/arm/CHAOSArmSysReg/CHAOSArmSysReg.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU")
    probability = Param.Float(0.0, "Per MRS-read probability of corruption")
    mode = Param.String("bitflip", "bitflip: 翻转读值一位 | value_to_legal: 换成一个合法系统寄存器值 (F5)")
    whiteList = Param.String(
        "ttbr0_el1,ttbr1_el1,tcr_el1,mair_el1,vbar_el1,contextidr_el1,nzcv",
        "可注入系统寄存器白名单（逗号分隔）")
    faultMask = Param.UInt64(0, "bitflip 位掩码 (0 = 随机一位)")
    firstClock = Param.UInt64(0, "最早可注入周期")
    lastClock = Param.UInt64(0, "最晚周期 (0 = 不限)")
    maxFaults = Param.UInt64(0, "最大注入次数 (0 = 不限)")
    rngSeed = Param.UInt64(0, "RNG 种子 (0 = random_device)")
    writeLog = Param.Bool(True, "写 fault_injections.log")
```

> 实现要点：hook `arch/arm/isa.cc` 的 `MRS` 读路径（系统寄存器读值返回处），仅白名单内触发；**FS 模式**（SE 无 MMU-on）；`vbar_el1` 翻转属"响亮"（立即异常），与 `ttbr*` 翻转（静默换页表）形成对照；随新写一并修 D4（时间窗 1GHz 假设）。

---

> **文档结束**。本文取代《KUNPENG920-工程设计.md》，与《ARM微架构SDC分析与故障注入方案.md》（风险分析，定"为什么"）构成体系：本文定"做什么、怎么做、怎么验、如何诊断、如何反哺芯片设计"。执行从第 10 章 Task S0-1 开始（fi-wangxu 已合并 `main` 的注入器资产后）。