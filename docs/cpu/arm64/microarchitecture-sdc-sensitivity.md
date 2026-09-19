# ARM64 CPU 微架构 × SDC 敏感性对比
---

## 1. 基本信息
- A. IFU（指令供给前端）：分支预测 (BP/BRE分支方向预测/BTB/间接预测/GHB/BPIQ/返回栈 RAS)、µop/MOP cache、L1-iTLB、L1i-Cache（tag/data）、Instruction Queue；
- B. OoO（乱序执行引擎）：Int instruction Decode、Int Registor Rename、Int Dispatch、FP/SIMD instruction Decode、FP/SIMD Registor Rename、FP/SIMD Dispatch；ROB（Reorder Buffer，重排序缓冲）
- C1. IEX（Int instr Execute）：ALU Issue Queue、LSU/MDU/SYS Issue Queue、Int Physically Registor File、ALU执行单元、MDU执行单元（整数乘除）、MSR/CP15；
- D. LSU（Load Store Unit）：LS（AGU/load）、STD（AGU/store）、L1-dTLB、Store Queue、L1d-Cache（tag/data/aux tag）；原子与同步单元（执行原子读改写如 CAS/atomic RMW、缓存行锁、总线锁，fence/barrier多核同步）；数据预取器（L1 PHT（prefetch history table）/TLB prefetcher/region prefetcher/L2 prefecther）
- C2. FSU（FP/SIMD Unit）：FP/SIMD Issue Queue、FP/SIMD PRF、FSU Pipe执行单元；
  - Cx. FP/SIMD：2×FP；FP32 FMA 2/cyc（128b），FP64；FADD 4/FMUL 5/FMA 5–7 cyc；NEON128 2/cyc；SVE512 FMA ≥2/cyc；SVE128b FMA
- C3. Crypto：AES+PMULL/SHA1/SHA2/SHA3/SHA256/CRC32/SM3/SM4/EOR3/XAR/BCAX
- E. MMU：L2-TLB、PTW（页表遍历）、PWC（页表遍历缓存）
- F. L2：L2-Cache（tag/data/TQ/victim/uncore/DSU）、核缓存一致性（MESI/MOESI、snooping 或目录协议）
- G. L3：L3-Cache/SLC（tag/data）
- H. RAS：RAM 保护 (ECC/parity 矩阵)、架构化 RAS (寄存器/异常/ESB/poison)、错误注入、平台 RAS 栈 (ACPI/EDAC)

---

## 2. CPU 微架构对比与 SDC 敏感性

### 2.1 微架构分组与单元全景

| 分区 | 逻辑图单元清单 |
|---|---|
| **A. IFU 指令供给前端** | 分支预测（BP/BRE 方向、BTB、间接预测、GHB、BPIQ、返回栈 RAS）· µop/MOP cache · L1i-Cache（tag/data）· L1-iTLB · Instruction Queue |
| **B. OoO 乱序执行引擎** | Int Decode→Rename→Dispatch · FP/SIMD Decode→Rename→Dispatch · **ROB（重排序缓冲：乱序执行/按序提交/精确异常）** |
| **C1. IEX 整数执行** | ALU Issue Queue · LSU/MDU/SYS Issue Queue · Int PRF · ALU×3 · MDU（乘除）· MSR/CP15 |
| **D. LSU 访存单元** | LS1/LS2（AGU/load）· STD1/STD2（AGU/store）· L1-dTLB · Store Queue · L1d-Cache（tag/data/aux tag）· 原子与同步单元 · 数据预取器（PHT/TLB/region/L2） |
| **C2. FSU 浮点/向量 · C3 Crypto** | FP/SIMD Issue Queue · FP/SIMD PRF（V/Z）· FSU Pipe 0/1（FADD/FMUL/FMA/NEON/SVE）· Cx 吞吐参数 · Crypto（AES/PMULL/SHA/SM3/SM4/CRC32） |
| **E. MMU 地址转换** | L2-TLB · PTW（页表遍历）· PWC（遍历缓存） |
| **F. L2 与核缓存一致性** | L2-Cache（tag/data/TQ/victim）· 核缓存一致性（MESI/MOESI/snooping/目录）· 簇/互连（DSU/SCU·CHI·snoop filter） |
| **G. L3/SLC · 内存** | L3-Cache/SLC（多核共享·可选）· DRAM（经 CHI/内存控制器） |
| **H. RAS（横切 A–G）** | H1 RAM 保护（ECC/parity/SED）· H2 架构化 RAS（ERR*/异常/ESB/poison）· H3 错误注入 · H4 平台 RAS 栈（APEI/GHES/EDAC/BMC） |

### 2.2 全单元对比总表

| 分组 | 单元 | Kunpeng 920 (TSV110) | 920f (part 0xd22) | Neoverse N1 | Neoverse N2 | Neoverse N3 |
|---|---|---|---|---|---|---|
| **A. IFU** | BP/BRE 方向预测 | 两级动态 ≈A73；1 taken/cyc | 未测（bpbench 中断） | 动态预测器 | 动态预测器 | 动态预测器 |
| | BTB | L1 64 / L2 ~2048 | 未测 | 有，容量未披露 | 有，容量未披露 | 有，容量未披露 |
| | 间接预测 / GHB / BPIQ | ≈16 目标/分支、全局 ~256 | 未测 | 有 GHB/BPIQ（RAS 表可证，容量未披露） | 有（未披露） | 有（未披露） |
| | 返回栈 RAS | 31–32 项 | 未测 | 有 | 有 | 有 |
| | µop / MOP cache | **无**（L1i 溢出带宽 4→0.25 条/cyc） | 未披露 | 无 | ★ **L0 MOP 1536 项 4-way skewed** | 无（相对 N2 删减） |
| | L1i-Cache | 64KB/4-way **AIVIVT** | 32KB/4-way | 64KB/4-way VIPT→PIPT | 64KB/4-way VIPT→PIPT | 32/64KB(可配)/4-way |
| | L1-iTLB | 32 项全相联 | 未测 | 48 项全相联 | 48 项全相联 | 32 项全相联 |
| | Instruction Queue | 未公开 | 未公开 | 未披露 | 未披露 | 未披露 |
| **B. OoO** | Int Decode | 4 宽 | 未公开 | A32/T32/A64 | A32/T32/A64 | **仅 A64** |
| | Int Rename | PRF ~128 + Flag ~31 | 未公开 | 未披露 | 未披露 | 未披露 |
| | Int Dispatch / ROB | ~128（实测有效 108–110） | 未公开 | 128（公开规格） | 未披露 | 未披露 |
| | FP/SIMD 译码·重命名·分发 | 2×FP 管线 | SVE512 译码 | NEON 128b | SVE2 128b | SVE2 128b |
| | 调度器 Issue Queue | ALU/LS/FP 各 ~33 | 未公开 | issue queues（容量未给） | issue queues | issue queues |
| **C1. IEX** | ALU Issue Queue | ~33 | 未公开 | 未披露 | 未披露 | 未披露 |
| | Int PRF | ~128 | 未公开 | 未披露 | 未披露 | 未披露 |
| | ALU | 3 ALU，分支占 2 口 | 未公开 | 整数执行单元 | 整数执行单元 | 整数执行单元 |
| | MDU 乘除 | 乘 4 / 除 19（早退） | 未公开 | 未披露 | 未披露 | 未披露 |
| | MSR/CP15 | 有 | 有 | 系统寄存器 | 系统寄存器 | 系统寄存器 |
| **D. LSU** | LS×2 / STD×2（AGU） | 2 AGU：2 load 或 1L+1S/cyc | 未公开 | load/store 单元 | LSU | LSU |
| | L1-dTLB | 32 项全相联 | 未测 | 48 项全相联 | 44 项全相联 | 48 项全相联 |
| | Store Queue | 未公开 | 未公开 | 未披露 | 未披露 | 未披露 |
| | L1d-Cache | 64KB/4-way，load-to-use 4 cyc | 32KB/8-way（~10 cyc） | 64KB/4-way，2×128b 读 | 64KB/4-way | 32/64KB(可配)/4-way/16 bank |
| | 原子与同步 | LSE 完整（casal 43 cyc） | LSE + LRCPC2/3 | LSE | LSE | LSE |
| | 数据预取器 | L1/region/L2 预取 | 未测 | L1 PHT（**无保护**） | 有（未披露） | VA/PC 引擎（L2 预取） |
| **C2. FSU** | FP/SIMD Issue Queue | ~33 | 未公开 | 未披露 | 未披露 | 未披露 |
| | FP/SIMD PRF | 偏小（32×128b） | ★ **Z0–Z31 ×512b + SME** | NEON 128b | SVE 128b（32×128b） | SVE2 128b |
| | FSU Pipe | FP32 FMA 2/cyc；FP64 **1/4 rate** | SVE512 FMA ≥2/cyc（实测 13.6 flop/cyc 下限） | NEON 128b | SVE2 128b | SVE2 128b |
| **C3. Crypto** | AES/SHA/SM/CRC | AES+PMULL·SHA1·SHA2(仅 256)·CRC32；无 SHA3/SM3/SM4 | AES·SHA1/2/512·SHA3·SM3/SM4·CRC32·SVE2 crypto | 可选 Crypto | SVE2 crypto + 可选 | v9.2 全量（SHA3 等） |
| **E. MMU** | L2-TLB | 1024 项共用（+11 cyc） | 未测 | 1280 项 5-way | 1280 项 5-way | ★ **分裂：small 1536/6-way + medium 256/4-way + walk cache** |
| | PTW / PWC | 页表遍历 | 未披露 | 4 并发遍历 + 预取 | translation table prefetcher | walk cache + prefetcher |
| | MMU/TLB 保护 | 无披露（RAS=0） | 未披露 | MMUTC 2×交织 parity；**L1 TLB=flops 无保护** | MMUTC SED | TLB 整体 SED |
| **F. L2 一致性** | L2-Cache | 512KB/8-way（10 cyc） | ★ **768KB/12-way（17 cyc）** | 256–1024KB/8-way（TQ 24/36/48） | 512/1024KB/8-way | 128KB–2MB/8-way/2-bank PIPT |
| | L2 RAM 保护 | 声称 ECC（无证据） | 未披露 | tag+data+TQ SECDED | tag+data+TQ SECDED | SECDED（granule 128/256b 可配） |
| | 核缓存一致性 | HHA 目录 + bufferless 环 NoC | HCCS（跨 socket NUMA 61–91） | DSU SCU + snoop filter（MESI） | DSU-110 | DSU-120 · CHI-E 256-bit |
| **G. L3/内存** | L3 / LLC | 32MB/die·15-way·128B 行·tag 在簇·S/P/P | ★ **无 L3/LLC** | DSU 内可选 L3 | DSU-110 L3 | Direct connect，**无 L3/SCU** |
| | 内存接口 | DDR4-2933 ×8ch（~187 GB/s） | 565GB·16+16 NUMA·8×200G | 48-bit PA·GICv4.1 | DSU-110 | 48-bit VA/PA·MPAM·CHI-E |
| **H. RAS** | H2 架构化 RAS | ✗ **RAS=0**（无 ERR*/ESB/poison） | ✓ RAS=1（黑盒，无 TRM） | v8.2 完整（CE/DE/UE） | v9.0 全量，Node0=L1+L2 | v9.2 全量，Node0=L1+L2+MMU/TLB |
| | H3 核心错误注入 | 仅平台级 EINJ（固件） | 未披露 | CE/DE/UC 注入 | CE/DE/UC 注入 | CE/DE/UC 注入 |
| | H4 平台 RAS 栈 | HEST/EINJ/BERT/ghes_edac | 未披露 | FHI/ERI/ESB/poison | FHI/ERI/ESB/poison | FHI/ERI/ESB/poison |

### 2.3 SDC 敏感性：现状 · 薄弱点 · 加固点

五款核在「RAM 阵列保护」这一维度上披露得最多，但**保护范围几乎全部止步于存储阵列 SRAM**。
下面按主题逐层挖掘，其中第 1–4 点是对五款核的**共同**结论，第 5 点是分核画像，第 6 点是加固优先级。

#### 2.3.1 共同盲区之一：执行数据通路与 flop 状态零保护（最高危）

TRM 与 Kunpeng 文档的保护矩阵只覆盖「会保存 dirty/clean 数据的 SRAM 阵列」：cache tag/data、
TLB、TQ、MOP cache。**没有任何一款核披露 ALU、PRF、ROB、调度器（Issue Queue）、scoreboard、
bypass/转发网络、重命名映射表的保护**——这些面向单周期吞吐的结构主要由寄存器堆/flop/CAM 实现，
本身不享受 SRAM 阵列的 ECC 包裹。

最直接的证据来自 N1：「The L1 TLBs are implemented with flops, so there is no cache protection
for L1 TLBs.」——它明确承认 flop 实现 = 无 cache 保护。这一逻辑等价成立于 PRF、ROB、调度
器：它们同样是 flop 结构，同样无 ECC/parity 披露。

> **SDC 含义**：对故障注入（FI）建模而言，执行阵列的翻转是**无保护、且无架构级出口的静默损坏**。
> 一个 ALU 结果 bit 或 PRF 读口 bit 翻转会被当"正确结果"提交到架构状态，五款核无一能检出。
> 这是五款乱序核共同的高危注入面，也是 DIMM 级 ECC 与缓存 ECC 都**覆盖不到**的真空区。

#### 2.3.2 共同盲区之二：分支预测器普遍无保护

N1 的 RAM 保护表把「L1 BTB / L1 GHB / L1 BPIQ / L1 PHT」四行明确标为 **None（无保护）**。
N2/N3 的保护表同样只列 cache/TLB/TQ/MOP，**不含 BTB/GHB/BPIQ**。华为 920 分支预测器的保护
未披露（且 RAS=0 时即使有保护也没有架构出口）。

> **SDC 含义**：方向/目标预测翻转大多表现为误预测→被 ROB 回滚（相对可容错、且可观测为性能
> 恶化）；但**间接目标/GHB 翻转**可能把控制流导向错误却"合法"的代码路径，属于潜在的静默控制流
> 破坏。加固方向明确且成本低：指令侧天然可恢复，给预测器加 parity，命中错误即 flush+refetch——
> N1 的「L1I tag parity + invalidate/refetch」已示范这一策略。

#### 2.3.3 共同盲区之三：SED-only 阵列的双 bit 翻转静默

所有「只保存 clean 数据」的 SRAM 只用 SED（Single Error Detect）parity：L1I tag/data、MOP cache、
MMUC/MMUTC、TLB。SED 只能检单 bit（触发 invalidate + refetch 恢复），**同一 granule 内的双 bit
翻转不检测**，直接静默损坏。N1/N2/N3 的表述完全一致（"For RAMs with only SED, the core does not
detect a double bit error. This might cause data corruption."）。

对比之下，承担 dirty 数据的 L1D/L2 tag/data、TQ 用的是 SECDED（可纠单 bit、检双 bit）。

> **SDC 含义**：clean-data 阵列对「多 bit 累积翻转」（老化、辐射 burst、供电扰动）暴露。特别是
> N2 的 **MOP cache 是全新且 SED-only 的指令面靶点**：它存译码后操作，翻转→执行错误指令→可能
> 直接产出错误结果且无探测。加固方向：对 clean-data 阵列升级 SECDED，或加周期 scrubbing 把
> 单 bit 在积累成双 bit 前刮除。

#### 2.3.4 保护纵深单调递增：920 < 920f(未知) < N1 ≤ N2 < N3

从架构化 RAS 能力看，五款核形成明显的纵深梯度：

- **920（RAS=0）**：无 RAS 架构扩展 → 无 ERR* 寄存器、无 ESB、无 poison。核内任何未保护阵列
  （分支预测器、flop 执行阵列）翻转**绝对静默**——无一架构级可见信号。唯一防线是片外 DDR4
  RDIMM SECDED（DIMM 级）与固件 ghes_edac。文档声称的 I$/D$/L2「ECC」**无架构化证据**（PFR0.RAS=0
  与"有 ECC"矛盾，ECC 若存在也缺错误记录出口）。
- **920f（RAS=1 黑盒）**：PFR0.RAS=1 说明有扩展，但无公开 TRM，保护矩阵不可知。更关键的是
  **SVE512（Z0–Z31×512b = 16 Kbit/核寄存器）与 SME/SME2（ZA tile 大状态）构成全新巨型数据面**，
  其保护完全未披露 → 黑盒按最坏假设（无保护）建模。
- **N1**：披露最透明的参照系——给出完整保护矩阵 + **无保护清单** + SDC 定义（"These are silent
  data corruptions"）。SECDED 盖 dirty，SED 盖 clean，BTB/GHB/BPIQ/PHT/flop 明确无保护。无 SVE，
  向量数据面仅 NEON 128b（小）。
- **N2**：整体 ≈N1，增量是 SVE2 128b 与 **MOP cache（SED-only 指令面附加靶点）**，架构升到 v9.0-A、
  Node0=L1+L2。
- **N3**：披露范围内**最低**（相对而言）。新增 **L1D aux tag 单独 SECDED**（覆盖 N1/N2 未保护的
  L1D 辅助标签状态）、**TLB 整体 SED**、**L2 ECC granule 可配 128/256b**、分裂 L2 TLB + walk cache、
  CHI-E 256-bit、v9.2-A 全量、Node0 覆盖 MMU/TLB。但执行阵列仍无披露。

#### 2.3.5 分核 SDC 画像

| 核 | SDC 敏感性定位 | 关键薄弱点 | 最值得打点的注入靶 |
|---|---|---|---|
| **920** | 最高（核内翻转无架构可见信号） | RAS=0、ECC 声称无证据、分支预测器无保护、flop 执行阵列 | 任意未保护 SRAM + 执行 flop |
| **920f** | 高（黑盒 + 巨型向量数据面） | SVE512/SME 无披露保护、无 TRM 保护矩阵 | Z 寄存器、SME ZA tile |
| **N1** | 参照系（披露最全） | BTB/GHB/BPIQ/PHT 无保护、L1 TLB flops | BTB/GHB、L1d aux 状态 |
| **N2** | ≈N1 + MOP 独立靶点 | MOP cache SED-only（双 bit 静默） | L0 MOP cache |
| **N3** | 披露范围内最低 | 执行阵列仍无披露 | L2 TLB 分裂结构、执行 flop |

#### 2.3.6 潜在加固点（按优先级）

1. **P0 — clean-data SED 阵列升级**：L1I/MOP/MMUTC/TLB 由 SED 升 SECDED，或加周期 scrubbing，
   消除双 bit 静默，这是 Arm 公版核最一致的结构性短板。
2. **P0 — 执行通路加固/披露**：对 PRF、ROB、调度器、ALU 通路至少做「关键字段 parity / residue /
   lockstep」并**披露现状**——当前五款在这块的沉默意味着 FI 只能按最坏假设。
3. **P1 — 分支预测器 parity + flush/refetch**：指令侧可无损恢复，代价极低，收益是消灭静默控制流破坏。
4. **P1 — 华为侧补救**：920 补齐 RAS 架构扩展（ERR*/ESB/poison），把「声称 ECC」翻译为架构可观测；
  920f 披露 SVE512/SME 状态的保护方案。
5. **P2 — FI 建模约定**：「未披露/未测」按**无保护**处理（黑盒最坏假设）；对 SED-only 与无保护
   阵列注入多 bit 翻转，对执行 flop 阵列注入单 bit；优先在 SED-only 阵列做「单→双 bit 累积」实验。

## 3. 各芯片微架构功能图（★ = 独有/标志性设计）

### Kunpeng 920

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1400" width="1480" height="1400" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1400" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">Kunpeng 920 · TaiShan v110 微架构功能图（ARMv8.2-A · 4 宽乱序 · 2.6GHz 实测）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = 920 实测结构：前端 4 宽无 uop-cache → 三类统一调度器 → chiplet 三模式 SLC。红=SDC 高危（无架构 RAS）· 数据出处：kunpeng920_microarchitecture.md 本机实测 + 公开资料</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="190" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（按序 · 4 宽）</text>
  <text x="236" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">无 uop-cache → 取指带宽悬崖：L1I 内 4 条/cyc → L2 ~1.75 → L3/内存 ~0.25</text>
  <rect x="50" y="166" width="260" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="188" font-size="13.5" fill="#1f2937" text-anchor="start" font-weight="700">BPU 分支预测</text>
  <text x="62" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">· BTB 两级：L1 64 项（taken 1c）</text>
  <text x="62" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">· L2 BTB ~2048 项</text>
  <text x="62" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">· 方向：两级动态（≈A73 水平）</text>
  <text x="62" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">· RAS 31–32 · 间接 ~256 目标</text>
  <text x="62" y="276" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 无任何 ECC/parity 披露（无 PAC）</text>
  <text x="62" y="293" font-size="10.5" fill="#6b7280" text-anchor="start">· mcf MPKI 16.64（N1 为 15.03）</text>
  <rect x="50" y="366" width="260" height="0" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="180.0" y="388" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700"></text>
  <rect x="340" y="166" width="200" height="96" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="440.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 64KB 4-way</text>
  <text x="440.0" y="208" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">64B 行 · AIVIVT（L1Ip=2 实测）</text>
  <text x="440.0" y="225" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">厂商称 ECC（无架构化证据）</text>
  <rect x="340" y="276" width="200" height="68" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="440.0" y="298" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">取指+译码</text>
  <text x="440.0" y="318" font-size="10.5" fill="#1f2937" text-anchor="middle">4 条/周期 · 定长 32-bit</text>
  <text x="440.0" y="335" font-size="10.5" fill="#1f2937" text-anchor="middle">仅 AArch64（无 AArch32）</text>
  <path d="M300,250 L334,250" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M440,262 L440,272" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <text x="452" y="258" font-size="10" fill="#7c3aed" text-anchor="start">下一 PC</text>
  <rect x="570" y="166" width="250" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="582" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">Rename / Dispatch</text>
  <text x="582" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">· PRF 式：31 GPR → INT ~128 物理寄存器</text>
  <text x="582" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">· Flag 重命名 ~31 · move elimination</text>
  <text x="582" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">· FP/向量 PRF 偏小（易压满）</text>
  <text x="582" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">· 按类分流 → 三类统一式调度器</text>
  <text x="582" y="276" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· PRF 翻转=直接 SDC（无保护披露）</text>
  <text x="582" y="293" font-size="10.5" fill="#6b7280" text-anchor="start">· squash 回滚依赖历史缓冲正确性</text>
  <path d="M540,250 L564,250" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="850" y="166" width="290" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="862" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">ISA 精确边界（ID 寄存器 EL0 实测）</text>
  <text x="862" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">有：LSE 完整 · AES+PMULL · SHA1/256（无 512）</text>
  <text x="862" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">　　CRC32 · UDOT/SDOT · FHM · JSCVT · FCMA</text>
  <text x="862" y="242" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">无：SVE · PAC · BTI · LRCPC · MTE · AArch32</text>
  <text x="862" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">CTR：DIC=IDC=0（无 I/D 自动一致）· ERG=64B</text>
  <text x="862" y="276" font-size="10.5" fill="#6b7280" text-anchor="start">CASAL 实测 43c · NOP 0.26c ≈ 3.9 IPC</text>
  <text x="862" y="293" font-size="10.5" fill="#6b7280" text-anchor="start">MMFR0/DFR0 部分字段固件实现不全（已判可信边界）</text>
  <path d="M820,250 L844,250" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="150" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute</text>
  <text x="196" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">ROB ~128 uop（实测有效 108–110）· 三类统一式调度器各 ~33 项</text>
  <rect x="50" y="436" width="250" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">发射队列（3 类统一式）</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· ALU 类 ~33 · 访存类 ~33 · FP/向量类 ~33</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 唤醒-选择环路 1–2c</text>
  <text x="62" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 控制触发器密集 = SDC 敏感区</text>
  <text x="62" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· 每源寄存器一条等待链</text>
  <text x="62" y="546" font-size="10.5" fill="#6b7280" text-anchor="start">· 对照：Neoverse V2 为 9 个分立 IQ</text>
  <rect x="330" y="436" width="250" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="342" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">PRF + 旁路网络</text>
  <text x="342" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· INT PRF ~128 · Flag ~31 · FP PRF 偏小</text>
  <text x="342" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 记分牌：读 PRF 或等旁路</text>
  <text x="342" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 旁路=纯导线+传输门，无任何保护</text>
  <text x="342" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· 背靠背链不写 PRF（转发掩蔽）</text>
  <rect x="610" y="436" width="380" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="622" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">执行单元簇</text>
  <text x="622" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· ALU×3（加 1c）· MUL/DIV×1（乘 4c；除 19c/早退 6.2c）</text>
  <text x="622" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· FP0/FP1 双 128-bit FMA（FP32 5c · FP64 quarter-rate）</text>
  <text x="622" y="512" font-size="10.5" fill="#1f2937" text-anchor="start">· 分支两口 · 1 taken/cyc · CRC32X 1c · AESD 3c</text>
  <text x="622" y="529" font-size="10.5" fill="#1f2937" text-anchor="start">· NEON 128b 上限（无 SVE）</text>
  <text x="622" y="546" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 进位链/FMA 树=时序违例重灾区（纯 SDC 通路）</text>
  <rect x="1020" y="436" width="400" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1032" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">ROB ~128 uop + Commit（4 宽）</text>
  <text x="1032" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 按程序序飞行指令账本 · 头部完成且无异常才退休</text>
  <text x="1032" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· squash 从出错点回滚全部后继</text>
  <text x="1032" y="512" font-size="10.5" fill="#1f2937" text-anchor="start">· 结果退休进架构态 · store 放行写 L1D（C7）</text>
  <text x="1032" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· x86 ROB 320–512 vs ARM 640–768+（面积账对照）</text>
  <text x="1032" y="546" font-size="10.5" fill="#6b7280" text-anchor="start">· 反压：ROB/IQ/LSQ 满 → rename 停</text>
  <path d="M300,510 L324,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M580,510 L604,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M990,510 L1014,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="200" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="706" width="150" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">访存 LSU + MMU</text>
  <text x="196" y="723" font-size="11.5" fill="#3f7a58" font-style="italic">AGU×2 · store 不投机 · TLB 无保护（RAS=0）</text>
  <rect x="50" y="766" width="300" height="140" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU：AGU×2 + L1D</text>
  <text x="62" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· 2 load 或 1L+1S /cyc · 2×128b 读</text>
  <text x="62" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· L1D 64KB 4-way · load-to-use 4c</text>
  <text x="62" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· store 转发 6–7c（跨 16B +1~2c）</text>
  <text x="62" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">· LSE 原子在 L1 争用下 43c（CASAL 实测）</text>
  <text x="62" y="876" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 厂商称 ECC（无架构化证据）</text>
  <rect x="380" y="766" width="320" height="140" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="392" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSQ（LQ + SQ）· STLF</text>
  <text x="392" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· store 不投机：退休后才写 L1D</text>
  <text x="392" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· load 乱序但先查 SQ（STLF）</text>
  <text x="392" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· STLF：CAM 匹配直转，不经 cache/PRF</text>
  <text x="392" y="859" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· STLF 段 ECC 全失明</text>
  <text x="392" y="876" font-size="10.5" fill="#6b7280" text-anchor="start">· （五款共同的 SDC 盲区）</text>
  <rect x="730" y="766" width="330" height="140" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="742" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MMU：TLB + PTW</text>
  <text x="742" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· iTLB 32 项全相联 · dTLB 32 项全相联</text>
  <text x="742" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· L2 TLB 1024 项 I/D 共用，命中 +11c</text>
  <text x="742" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· PTW 4KB/16KB/64KB 粒度</text>
  <text x="742" y="859" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· TLB 无保护披露（RAS=0）</text>
  <text x="742" y="876" font-size="10.5" fill="#6b7280" text-anchor="start">· 4KB×4=16KB 恰处 VIPT 别名临界（实测无别名）</text>
  <path d="M680,830 L704,830" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="960" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="936" width="200" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="953.5" font-size="14" fill="#ffffff" font-weight="600">内存层级 Memory（chiplet）</text>
  <text x="246" y="953" font-size="11.5" fill="#6d5aa0" font-style="italic">chiplet：2 计算 die(SCCL)+1 IO die，CoWoS · 每 die 8 CCL(4核簇) · Hydra 互联 · 距离 10/12/20/22</text>
  <rect x="50" y="996" width="240" height="120" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="170.0" y="1018" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 64KB 4-way</text>
  <text x="170.0" y="1038" font-size="10.5" fill="#1f2937" text-anchor="middle">load 54.6 / store 41.2 GB/s</text>
  <text x="170.0" y="1055" font-size="10.5" fill="#1f2937" text-anchor="middle">4c load-to-use（依赖链实测 2.87）</text>
  <text x="170.0" y="1072" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">ECC 强度不可验证</text>
  <text x="170.0" y="1089" font-size="10.5" fill="#1f2937" text-anchor="middle">L1←L2 ~32B/cyc（refill 可观测）</text>
  <rect x="320" y="996" width="250" height="120" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="445.0" y="1018" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 512KB/核 8-way</text>
  <text x="445.0" y="1038" font-size="10.5" fill="#1f2937" text-anchor="middle">10c · 64B · PoU</text>
  <text x="445.0" y="1055" font-size="10.5" fill="#1f2937" text-anchor="middle">实测 4.88ns（256KB 工作集）</text>
  <text x="445.0" y="1072" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">厂商称 ECC（无证据）</text>
  <text x="445.0" y="1089" font-size="10.5" fill="#1f2937" text-anchor="middle">load 42.8 GB/s（256KB）</text>
  <rect x="600" y="996" width="400" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="612" y="1018" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">L3 / SLC 每 die 32MB</text>
  <text x="612" y="1038" font-size="10.5" fill="#1f2937" text-anchor="start">· 8 bank×4MB · 15-way 伪随机</text>
  <text x="612" y="1055" font-size="10.5" fill="#1f2937" text-anchor="start">· 128B 行（L1/L2 是 64B！）</text>
  <text x="612" y="1072" font-size="10.5" fill="#1f2937" text-anchor="start">· tag 在簇侧 · 数据 bank 在 NoC 侧</text>
  <text x="612" y="1089" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· 三模式 Shared/Private/Partition(默认)</text>
  <text x="612" y="1106" font-size="10.5" fill="#1f2937" text-anchor="start">· partition 近端 4MB ~36c → 全容量 &gt;90c</text>
  <text x="612" y="1123" font-size="10.5" fill="#1f2937" text-anchor="start">· 双核共享退化为全容量高延迟</text>
  <rect x="1030" y="996" width="390" height="120" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1225.0" y="1018" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">DDR4-2933 ×8ch</text>
  <text x="1225.0" y="1038" font-size="10.5" fill="#1f2937" text-anchor="middle">每 die 读 ~63 GB/s</text>
  <text x="1225.0" y="1055" font-size="10.5" fill="#1f2937" text-anchor="middle">空载 ~96ns · 实测 163.5ns（256MB）</text>
  <text x="1225.0" y="1072" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">Registered-DDR4 SECDED（ghes_edac 实证）</text>
  <text x="1225.0" y="1089" font-size="10.5" fill="#1f2937" text-anchor="middle">ce/ue 计数实测为 0</text>
  <path d="M290,1056 L314,1056" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M570,1056 L594,1056" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1000,1056 L1024,1056" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="1240" width="1420" height="140" rx="10" fill="#fef2f2" stroke="#b91c1c" stroke-width="2"/>
  <text x="46" y="1266" font-size="15" fill="#b91c1c" font-weight="700">RAS / 保护状态（SDC 视角）——RAS=0，五款中敏感性最高</text>
  <text x="46" y="1288" font-size="11.5" fill="#1f2937">架构化 RAS (ERR*/ESB/poison)</text>
  <text x="406" y="1288" font-size="11.5" fill="#b91c1c">无 —— ID_AA64PFR0_EL1.RAS = 0（EL0 实测）：无 ERR* 记录寄存器、无 ESB、无架构化 poison、无 FHI/ERI、无架构化错误注入</text>
  <text x="46" y="1307" font-size="11.5" fill="#1f2937">核内翻转归宿</text>
  <text x="406" y="1307" font-size="11.5" fill="#b91c1c">性能异常 / 崩溃 / 静默（SDC）——最后一类无任何架构级可见信号</text>
  <text x="46" y="1326" font-size="11.5" fill="#1f2937">厂商宣称冲突</text>
  <text x="406" y="1326" font-size="11.5" fill="#b91c1c">宣称 I$/D$ ECC、Memory Poisoning 与 RAS=0 冲突：即便有也是非架构化私有实现，SDC 实验不可依赖</text>
  <text x="46" y="1345" font-size="11.5" fill="#1f2937">平台级 RAS</text>
  <text x="406" y="1345" font-size="11.5" fill="#047857">ACPI HEST/EINJ/BERT/ERST 全在（EINJ 368B 固件注入可用）· ghes_edac DDR SECDED · MPAM · SDEI</text>
  <text x="46" y="1364" font-size="11.5" fill="#1f2937">uncore 观测</text>
  <text x="406" y="1364" font-size="11.5" fill="#6b7280">每 die L3C×8（back_invalid=一致性干扰）· HHA×2 · DDRC×4 · 需 perf_event_paranoid≤1 · 调频粒度=die 级</text>
</svg>

</div>

独有/标志性：L3/SLC 三模式（Shared/Private/**Partition 默认**）+ **128B 行**（L1/L2 是 64B）+ tag 在簇侧；
无 µop cache（取指带宽悬崖）；**RAS=0**（无架构化 RAS，全图唯一的"裸奔"平台）；AIVIVT L1I；NEON 128b 上限。

### 920f（part 0xd22）

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1400" width="1480" height="1400" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1400" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">920f · HiSilicon part 0xd22 微架构功能图（ARMv9 · SVE512+SME2 · 黑盒实测）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = 黑盒结构：大量未公开（灰虚线）+ SVE512/SME2 宽向量金卡 + 无 LLC 扁平层级 + 64KB 强制页。出处：920f.md NSCC cn23154 实测</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="210" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（规格未公开）</text>
  <text x="256" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">分支预测器容量待测（bpbench 未完成）· 仅 AArch64 · CTR_EL0=0x9444c004（ERG=64B）</text>
  <rect x="50" y="166" width="250" height="130" rx="7" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="6,4"/>
  <text x="175.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">BPU（未公开）</text>
  <text x="175.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">BTB/RAS/间接预测容量</text>
  <text x="175.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">均未测得（待 bpbench）</text>
  <text x="175.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">CSV2/3=1（推测攻击缓解在）</text>
  <rect x="340" y="166" width="210" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="445.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 32KB 4-way</text>
  <text x="445.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行（CTR 实测）</text>
  <text x="445.0" y="225" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">ECC/parity 未披露</text>
  <text x="445.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">（RAS=1 但无 TRM）</text>
  <rect x="580" y="166" width="210" height="130" rx="7" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="6,4"/>
  <text x="685.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">译码 / 重命名 / 派遣</text>
  <text x="685.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">宽度未公开</text>
  <text x="685.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">仅 A64 指令集</text>
  <text x="685.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">（无 AArch32）</text>
  <rect x="820" y="166" width="330" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="832" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">SVE 512-bit + SME/SME2（五款唯一宽向量）</text>
  <text x="832" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">· SVEver=1 · f32mm/f64mm/BF16=1 · 实测 VL=64B</text>
  <text x="832" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">· SME2：f64f64/b16f32/f32f32/i8i32（fa64=0）</text>
  <text x="832" y="242" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· Z0–Z31 × 512b + 矩阵 tile = 新增大面积无保护数据面</text>
  <text x="832" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">· SVE512 FMA 实测 ≥13.6 flop/cyc（理论 16）</text>
  <text x="832" y="276" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 单向量翻转影响 64B 连续数据</text>
  <rect x="1180" y="166" width="240" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1192" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">ISA 扩展（实测）</text>
  <text x="1192" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">SHA1/2/512 · SHA3 · SM3/SM4</text>
  <text x="1192" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">LRCPC2/3 · i8mm · bf16 · RPRES</text>
  <text x="1192" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">WFXT · SVE2 全集 · AES · LSE</text>
  <text x="1192" y="259" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">BTI=0 · MTE=0 · RNDR=0</text>
  <path d="M300,230 L334,230" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <path d="M550,230 L574,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M790,230 L814,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1150,230 L1174,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="210" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute（吞吐实测）</text>
  <text x="256" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">标量 FMA 2/cyc · NEON128 FMA 2/cyc · SVE512 FMA ≥2/cyc——三级向量吞吐阶梯全部双发</text>
  <rect x="50" y="436" width="300" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">标量 / NEON 通路</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 标量 FMADD 8 链：8.0 Gflop/s = 4 flop/cyc</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· NEON128 8×2lane：13.5 Gflop/s ≈ 6.75</text>
  <text x="62" y="512" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· 标量 FMA 双端口实证（920 为 FP 单口怪点）</text>
  <text x="62" y="529" font-size="10.5" fill="#1f2937" text-anchor="start">· 单核理论 128 Gflop/s（SVE512 FP64）</text>
  <rect x="380" y="436" width="330" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="392" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">SVE512 数据通路</text>
  <text x="392" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· SVE512 8×8lane：27.2 Gflop/s 下限（~13.6）</text>
  <text x="392" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 608 核节点理论 ~77.8 Tflop/s（FP64）</text>
  <text x="392" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 单向量翻转影响 64B 连续数据</text>
  <text x="392" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· flopbench 修正版待复测（初版被编译器削链）</text>
  <text x="392" y="546" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 全部数据面无保护披露</text>
  <rect x="740" y="436" width="300" height="150" rx="7" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="6,4"/>
  <text x="890.0" y="458" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">PRF / ROB / 调度器（未公开）</text>
  <text x="890.0" y="478" font-size="10.5" fill="#1f2937" text-anchor="middle">容量/结构黑盒</text>
  <text x="890.0" y="495" font-size="10.5" fill="#1f2937" text-anchor="middle">与五款一致：无任何保护披露</text>
  <text x="890.0" y="512" font-size="10.5" fill="#1f2937" text-anchor="middle">FI 实验按 gem5 O3 通用模型注入</text>
  <rect x="1070" y="436" width="350" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1082" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU / 访存</text>
  <text x="1082" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· LSE 原子 · LRCPC2/3（LDAPR 系增强）</text>
  <text x="1082" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· DC ZVA 64B</text>
  <text x="1082" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· LSQ/store buffer 保护未披露（五款共同盲区）</text>
  <text x="1082" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· 定频 2.0GHz（userspace 锁 MAX）→ 测量无变频噪声</text>
  <path d="M350,510 L374,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M710,510 L734,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1040,510 L1064,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="706" width="210" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">内存层级 + MMU（无 LLC）</text>
  <text x="256" y="723" font-size="11.5" fill="#6d5aa0" font-style="italic">16 计算 NUMA + 16 无 CPU 内存节点（疑似 CXL/近存）· 跨 socket 距离 61–91 · 8×200GbE RoCE 聚合 1.6Tb/s</text>
  <rect x="50" y="766" width="250" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="175.0" y="788" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 32KB 8-way</text>
  <text x="175.0" y="808" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行 · 实测 ~5.0ns（≈10c）</text>
  <text x="175.0" y="825" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">8-way（同代 Neoverse 为 4-way）</text>
  <text x="175.0" y="842" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">ECC 未披露</text>
  <text x="175.0" y="859" font-size="10.5" fill="#1f2937" text-anchor="middle">容量 32KB &lt; 920 的 64KB</text>
  <rect x="330" y="766" width="290" height="150" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="475.0" y="788" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 768KB 12-way</text>
  <text x="475.0" y="808" font-size="10.5" fill="#1f2937" text-anchor="middle">统一 I+D · 实测 ~8.7ns（≈17c）</text>
  <text x="475.0" y="825" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">五款中最大私有 L2（N3 可配 2MB 追平）</text>
  <text x="475.0" y="842" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">12-way 非常规（920:8 / N 系:8）</text>
  <text x="475.0" y="859" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">ECC 未披露</text>
  <rect x="650" y="766" width="300" height="150" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="800.0" y="788" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">无 L3 / LLC</text>
  <text x="800.0" y="808" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">sysfs 无 index3 · CLIDR 陷阱实证</text>
  <text x="800.0" y="825" font-size="10.5" fill="#1f2937" text-anchor="middle">SCN 网状远端 8–16MB → 45–90ns</text>
  <text x="800.0" y="842" font-size="10.5" fill="#1f2937" text-anchor="middle">（网络侧缓存，非核侧 LLC）</text>
  <text x="800.0" y="859" font-size="10.5" fill="#1f2937" text-anchor="middle">少一级缓存 = 少一级 SDC 暴露面</text>
  <rect x="980" y="766" width="440" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="992" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">DRAM / NUMA</text>
  <text x="992" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">565GB · 16×31–33GB 计算节点</text>
  <text x="992" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">远程 NUMA 实测 ~130ns</text>
  <text x="992" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">node16–31 无 CPU 各 4GB（性质待确认：CXL? HBM?）</text>
  <text x="992" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">PMUv3 6 计数器 + SPE + AMU=1 · DIT=1</text>
  <path d="M300,840 L324,840" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M620,840 L644,840" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M950,840 L974,840" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="1010" width="1420" height="170" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="986" width="160" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="1003.5" font-size="14" fill="#ffffff" font-weight="600">MMU：TLB + PTW</text>
  <text x="206" y="1003" font-size="11.5" fill="#3f7a58" font-style="italic">TLB 容量未测（缺口，待补）</text>
  <rect x="50" y="1046" width="620" height="110" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="62" y="1068" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">64KB 强制页（TGran4=0xf）</text>
  <text x="62" y="1088" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 单 TLB entry 翻转波及面 ×16（vs 4KB 页）——SDC 放大器</text>
  <text x="62" y="1105" font-size="10.5" fill="#1f2937" text-anchor="start">· PAGESIZE=4096 是内核兼容层假象</text>
  <text x="62" y="1122" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· 未被文献覆盖的放大器实验设计点</text>
  <rect x="700" y="1046" width="720" height="110" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="712" y="1068" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">uncore 观测</text>
  <text x="712" y="1088" font-size="10.5" fill="#1f2937" text-anchor="start">171 perf 设备 = 8 SCCL×(4 DDRC+4 HHA+16 UC) + 14 SICL L3（hisi_sicl3_pa/h60pa）+ SPE + PCIe PTT</text>
  <text x="712" y="1105" font-size="10.5" fill="#1f2937" text-anchor="start">隔离：isolcpus + nohz_full 覆盖 608 核，每 NUMA 留末核处理中断（FI 实验绑核须避开）</text>
  <text x="712" y="1122" font-size="10.5" fill="#6b7280" text-anchor="start">复现入口：dnode -l cn23154 / dattach -c '/home/share/suke/archprobe/...'（详见 920f.md §6）</text>
  <rect x="30" y="1215" width="1420" height="140" rx="10" fill="#fef2f2" stroke="#b91c1c" stroke-width="2"/>
  <text x="46" y="1241" font-size="15" fill="#b91c1c" font-weight="700">RAS / 保护状态（SDC 视角）——RAS=1 但防御矩阵黑盒</text>
  <text x="46" y="1263" font-size="11.5" fill="#1f2937">架构化 RAS</text>
  <text x="406" y="1263" font-size="11.5" fill="#047857">ID_AA64PFR0_EL1.RAS = 1（实测）—— 有 ARMv8.2+ RAS 架构扩展，但防御矩阵黑盒</text>
  <text x="46" y="1282" font-size="11.5" fill="#1f2937">与 920 的关键代差</text>
  <text x="406" y="1282" font-size="11.5" fill="#1f2937">ERR* 寄存器 / ESB / 架构化 poison 理论上存在 · 具体注入寄存器布局未知（无厂商 TRM）</text>
  <text x="46" y="1301" font-size="11.5" fill="#1f2937">其他</text>
  <text x="406" y="1301" font-size="11.5" fill="#1f2937">DIT=1（数据无关时间）· CSV2/3=1 · AMU=1 · 无 MTE（内存标签纠错不可用）</text>
  <text x="46" y="1320" font-size="11.5" fill="#1f2937">SDC 实验定位</text>
  <text x="406" y="1320" font-size="11.5" fill="#b91c1c">RAS=1 但无文档 → 有防御潜力但强度未知；64KB 页 × TLB 注入是未被文献覆盖的放大器实验</text>
  <text x="46" y="1339" font-size="11.5" fill="#1f2937">未决项（920f.md §7 原文）</text>
  <text x="406" y="1339" font-size="11.5" fill="#6b7280">SVE512 峰值复测 · 分支预测器容量（bpbench 中断过）· node16–31 内存节点性质（需 ddrc PMU 或 dmesg root）</text>
</svg>

</div>

独有/标志性：**SVE 512-bit + SME/SME2**（五款唯一宽向量）；**768KB/12-way L2**（非常规配置）；
**无 L3/LLC**（少一级缓存暴露面）；**64KB 强制页**（TLB 翻转波及面 ×16 放大器）；RAS=1 但防御矩阵黑盒。

### Neoverse N1

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1450" width="1480" height="1450" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1450" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">Arm Neoverse N1 微架构功能图（ARMv8.2-A · 超标量乱序 · DSU）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = N1 TRM 组件结构（章节号随文标注）：三指令集译码 + ETM + 三级原子 + 两级 TLB（L1 flops）。出处：Neoverse N1 TRM 100616_0401_02</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="220" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（按序 · TRM §3.1）</text>
  <text x="266" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">取指→译码→重命名→派遣 · A32/T32/A64 三指令集译码 · I$ 硬件一致性可配（COHERENT_ICACHE，推荐 L2=1MB）</text>
  <rect x="50" y="166" width="260" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">程序流预测（TRM §7.3）</text>
  <text x="62" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">动态分支预测器 + BTB + 间接预测</text>
  <text x="62" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">容量 TRM 未披露</text>
  <text x="62" y="242" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">Table 9-1 明示：BTB / GHB / BPIQ</text>
  <text x="62" y="259" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">全部 None（无保护）</text>
  <rect x="340" y="166" width="220" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="450.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 64KB 4-way</text>
  <text x="450.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行 · 硬件一致性可配（§3.1.1）</text>
  <text x="450.0" y="225" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag: 1 parity/39b · data: SED/72b</text>
  <text x="450.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">错误→行失效重取（无数据丢失）</text>
  <rect x="590" y="166" width="200" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="690.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">译码（§3.1.2）</text>
  <text x="690.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">A32 / T32 / A64</text>
  <text x="690.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">NEON+FP 各态支持</text>
  <text x="690.0" y="242" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">AArch32 EL0（五款唯一）</text>
  <rect x="820" y="166" width="200" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="920.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">重命名（§3.1.3）</text>
  <text x="920.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">寄存器重命名促乱序</text>
  <text x="920.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">分发至各发射队列</text>
  <text x="920.0" y="242" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">PRF 保护无披露</text>
  <rect x="1050" y="166" width="180" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1140.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">发射（§3.1.4）</text>
  <text x="1140.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">issue queues 暂存</text>
  <text x="1140.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">待派发指令</text>
  <text x="1140.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">（容量未披露）</text>
  <rect x="1270" y="166" width="160" height="130" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="1350.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">ETM（§2.2）</text>
  <text x="1350.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">Embedded Trace</text>
  <text x="1350.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">Macrocell</text>
  <text x="1350.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">指令 trace only</text>
  <text x="1350.0" y="259" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">N2/N3 为 ETE+TRBE 型</text>
  <path d="M310,230 L334,230" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <path d="M560,230 L584,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M790,230 L814,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1020,230 L1044,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="150" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute</text>
  <text x="196" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">INT 单元 + 向量单元（NEON+FP，可选 Crypto）· 写回经记分牌仲裁 · 推测错路径经 squash 回滚</text>
  <rect x="50" y="436" width="300" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">整数执行（§3.1.5）</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 算术/逻辑数据处理 · ROB 128（公开规格）</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· LDAPR 系（RCpc v8.3，ISAR1 实证）</text>
  <text x="62" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· ALU 位翻转=纯 SDC 通路（无任何校验）</text>
  <text x="62" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· LOR：4 个 Limited Ordering Region 描述符</text>
  <rect x="380" y="436" width="300" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="392" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">向量执行（§3.1.5）</text>
  <text x="392" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· NEON 128b SIMD + FP32/FP64</text>
  <text x="392" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· Crypto 可选（AES/SHA）· 无 SVE</text>
  <text x="392" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· FMA 树=时序违例重灾区</text>
  <rect x="710" y="436" width="330" height="150" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="722" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">三级原子执行（§7.4.1）</text>
  <text x="722" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· near atomic：L1 命中且 unique 态，核内完成</text>
  <text x="722" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· far atomic：miss/共享 → CHI 接口送互联</text>
  <text x="722" y="512" font-size="10.5" fill="#1f2937" text-anchor="start">· 全簇 miss → DSU L3 分配执行（可配 L3 时）</text>
  <text x="722" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· CPUECTLR 可配各类原子倾向 near · PLDW/PRFM 提示</text>
  <rect x="1080" y="436" width="340" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1250.0" y="458" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">观测单元（§2.2）</text>
  <text x="1250.0" y="478" font-size="10.5" fill="#1f2937" text-anchor="middle">PMU + SPE + AMU</text>
  <text x="1250.0" y="495" font-size="10.5" fill="#1f2937" text-anchor="middle">TrustZone · PBHA</text>
  <text x="1250.0" y="512" font-size="10.5" fill="#1f2937" text-anchor="middle">Crypto 可选扩展</text>
  <path d="M350,510 L374,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M680,510 L704,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="240" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="706" width="150" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">访存 LSU + MMU</text>
  <text x="196" y="723" font-size="11.5" fill="#3f7a58" font-style="italic">L1D 64KB 4-way VIPT · ECC per 32 bits · 两级 TLB</text>
  <rect x="50" y="766" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU + L1D（§3.1.6/§7.4）</text>
  <text x="62" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· L1D 64KB 4-way VIPT 64B · ECC per 32 bits</text>
  <text x="62" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· 内部独占监视器（LL/SC）</text>
  <text x="62" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· transient/non-temporal 特化</text>
  <text x="62" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">· write streaming 模式（§7.2.7）</text>
  <text x="62" y="876" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· L1 PHT 无保护（Table 9-1）</text>
  <rect x="410" y="766" width="280" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="550.0" y="788" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">预取（§7.5）</text>
  <text x="550.0" y="808" font-size="10.5" fill="#1f2937" text-anchor="middle">数据预取器 + L1 PHT</text>
  <text x="550.0" y="825" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">PHT：Table 9-1 明示 None</text>
  <text x="550.0" y="842" font-size="10.5" fill="#1f2937" text-anchor="middle">（预取错地址多被掩盖，低危）</text>
  <rect x="720" y="766" width="700" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="732" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MMU：两级 TLB（§6.2）</text>
  <text x="732" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· iTLB 48 项全相联（4K–32M）· dTLB 48 项全相联（4K–512M）· L1 命中 1c</text>
  <text x="732" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· L2 TLB 1280 项 5-way 共享（§6.2.3）· 4 并行 walk / 2 lookup · 连续 6 miss 停顿</text>
  <text x="732" y="842" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· L1 TLB 用触发器实现 → 无 cache 保护（TRM 原文注释）</text>
  <text x="732" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">· MMUTC 2-bit 交错 parity/71b</text>
  <rect x="30" y="1010" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="986" width="230" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="1003.5" font-size="14" fill="#ffffff" font-weight="600">内存层级（L1 → L2 → DSU）</text>
  <text x="276" y="1003" font-size="11.5" fill="#6d5aa0" font-style="italic">异步 CPU bridge 连 DSU · 组件常在 · 与 DSU 间仅一致性接口可配同步</text>
  <rect x="50" y="1046" width="280" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="190.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 64KB 4-way VIPT</text>
  <text x="190.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行 · ECC per 32 bits（§3.1.6）</text>
  <text x="190.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">Table 9-1: tag SECDED 42+7b</text>
  <text x="190.0" y="1122" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">data SECDED 32+1 poison+7b</text>
  <text x="190.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">poison 粒度 64b（L1D 特例 32b）</text>
  <text x="190.0" y="1156" font-size="10.5" fill="#1f2937" text-anchor="middle">UC→evict 纠正回填（§9.2）</text>
  <rect x="360" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="525.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 256/512/1024KB 8-way</text>
  <text x="525.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">私有统一（§3.1.7）· 2 bank</text>
  <text x="525.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag SECDED（50–57 tag+7 ECC）</text>
  <text x="525.0" y="1122" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">data SECDED 8 ECC/64b</text>
  <text x="525.0" y="1139" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">TQ 24/36/48 项可配（2bank×12/18/24）</text>
  <text x="525.0" y="1156" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">L2 victim 阵列：None（Table 9-1）</text>
  <rect x="720" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="885.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">DSU（簇共享单元）</text>
  <text x="885.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">≤4 核 + 可选 L3 / snoop filter</text>
  <text x="885.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">单核直连配置可无 L3/SCU</text>
  <text x="885.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">L3 保护 = DSU TRM 范围</text>
  <text x="885.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">（core TRM 不披露）</text>
  <rect x="1080" y="1046" width="340" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1250.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">SoC 侧</text>
  <text x="1250.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">48-bit PA · GICv4.1 CPU 接口</text>
  <text x="1250.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">PMU + SPE + AMU（§2.2）</text>
  <text x="1250.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">TrustZone · PBHA</text>
  <text x="1250.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">Crypto 可选扩展</text>
  <path d="M330,1120 L354,1120" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M690,1120 L714,1120" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1050,1120 L1074,1120" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="1290" width="1420" height="160" rx="10" fill="#f0fdf4" stroke="#047857" stroke-width="2"/>
  <text x="46" y="1316" font-size="15" fill="#047857" font-weight="700">RAS 扩展（TRM §9 全披露）——五款中的透明度参照系</text>
  <text x="46" y="1338" font-size="11.5" fill="#1f2937">架构化机制</text>
  <text x="406" y="1338" font-size="11.5" fill="#047857">ERR&lt;n&gt;FR/CTLR/MISC0-1+PFGF · SEA/AEA/ERI · FHI/ERI 中断 · ESB 指令 · poison 传播（64b 粒度，L1D 32b）</text>
  <text x="46" y="1357" font-size="11.5" fill="#1f2937">错误注入（§9.7）</text>
  <text x="406" y="1357" font-size="11.5" fill="#047857">CE/DE/UC/RE 四类全可注入（ERRSELR_EL1 选 record 0 + ERR0CTLR），注入不破坏真实 RAM 数据/校验逻辑</text>
  <text x="46" y="1376" font-size="11.5" fill="#1f2937">tag UC 处置</text>
  <text x="406" y="1376" font-size="11.5" fill="#1f2937">失效整行 + ERI 通知（地址/一致性态未知，无法 poison，软件被告知数据可能丢失——显式非静默）</text>
  <text x="46" y="1395" font-size="11.5" fill="#1f2937">SDC 判定基准</text>
  <text x="406" y="1395" font-size="11.5" fill="#b45309">TRM §9.1 直接给出 SDC 定义（silent data corruptions）——本仓库 SDC 判定基准的引用源</text>
  <text x="46" y="1414" font-size="11.5" fill="#1f2937">明示无保护清单</text>
  <text x="406" y="1414" font-size="11.5" fill="#b91c1c">L1 BTB · GHB · BPIQ · L1 PHT · MMU replacement/biased-repl · L2 victim · L1 TLB（flops）</text>
  <text x="46" y="1433" font-size="11.5" fill="#1f2937">SED 弱点</text>
  <text x="406" y="1433" font-size="11.5" fill="#b91c1c">I$ tag parity+data SED（弱于 L1D SECDED）→ TRM 承认 SED 双位错 might cause data corruption</text>
</svg>

</div>

独有/标志性：**ETM**（指令 trace，N2/N3 改 ETE+TRBE）——五款唯一仍在用 ETM 型 trace 单元；
AArch32 EL0（A32/T32/A64，与 N2 相同；920/920f/N3 无）；
三级原子执行（near L1 → far CHI → DSU L3，N2/N3 亦有同类机制）；L2 TQ 24/36/48 项可配（五款唯一把 TQ 深度列为构建选项）；
TRM 明示无保护清单最完整（BTB/GHB/BPIQ/PHT/L2 victim/L1 TLB flops）——本组"披露透明度参照系"。

### Neoverse N2

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1450" width="1480" height="1450" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1450" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">Arm Neoverse N2 微架构功能图（Armv9.0-A · 超标量乱序 · DSU-110）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = N2 增量结构：L0 MOP cache 前端金卡（五款唯一）+ SVE2 首世代 + MMUTC SED 升级。出处：Neoverse N2 TRM 102099_0003_06</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="250" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（按序 · TRM §3.1 p40）</text>
  <text x="296" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">L1I 64KB 4-way 64B · iTLB 全相联（4K/16K/64K/2M 原生页）· A32/T32/A64 全译码（AArch32 全保留）</text>
  <rect x="50" y="166" width="250" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">程序流预测（§7.3 p66）</text>
  <text x="62" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">BTB（taken 目标）+ 方向预测器（历史）</text>
  <text x="62" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">返回栈 + 静态预测器 + 间接预测器</text>
  <text x="62" y="242" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">BTB/GHB/BIM 保护未列（Table 11-1）</text>
  <text x="62" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">A32↔T32 状态切换分支也预测</text>
  <rect x="330" y="166" width="200" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="430.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 64KB 4-way</text>
  <text x="430.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行 · I$ 硬件一致性（§7.4）</text>
  <text x="430.0" y="225" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SED parity（Table 11-1）</text>
  <text x="430.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">投机取指行为 §7.2 约束</text>
  <rect x="560" y="166" width="310" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="572" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">L0 MOP 缓存（§3.1 p40）</text>
  <text x="572" y="208" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">1536 项 · 4-way 倾斜相联（skewed）</text>
  <text x="572" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">存已译码+已优化指令</text>
  <text x="572" y="242" font-size="10.5" fill="#047857" text-anchor="start" font-weight="600">data: SED（Table 11-1）</text>
  <text x="572" y="259" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">弱保护 × 高命中 × 指令面</text>
  <text x="572" y="276" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">（五款唯一 MOP 结构）</text>
  <rect x="900" y="166" width="250" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1025.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">重命名 / 发射（§3.1）</text>
  <text x="1025.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">重命名促乱序</text>
  <text x="1025.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">分发至各发射队列</text>
  <text x="1025.0" y="242" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">PRF 保护未披露</text>
  <rect x="1190" y="166" width="230" height="130" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="1305.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">ETE + TRBE</text>
  <text x="1305.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">Embedded Trace Ext</text>
  <text x="1305.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">+ Trace Buffer</text>
  <text x="1305.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">（替代 N1 ETM 型式）</text>
  <path d="M300,230 L324,230" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <path d="M530,230 L554,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M870,230 L894,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1150,230 L1174,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="260" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute（TRM §3.1 p41-42）</text>
  <text x="306" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">整数执行 + 向量执行（FPU · NEON · SVE/SVE2 128b 向量长度 · Crypto 可选含 SM3/SM4）</text>
  <rect x="50" y="436" width="290" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">整数执行单元</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 算术/逻辑数据处理（§3.1）</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· RNG 支持（§16，RNDR/RNDRRS）</text>
  <text x="62" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· ALU 数据通路无保护披露</text>
  <rect x="370" y="436" width="350" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="382" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">向量执行：SVE / SVE2（§14）</text>
  <text x="382" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 向量长度 128-bit（与 NEON 等宽，非宽向量）</text>
  <text x="382" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· SVE2 全集：predication/gather/permute</text>
  <text x="382" y="512" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· 五款 Neoverse 侧第一个 SVE 世代（920f 为 512b）</text>
  <rect x="750" y="436" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="762" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">Crypto 扩展（可选 · §3.1）</text>
  <text x="762" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· AES · SHA-1/224/256/384/512</text>
  <text x="762" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· SM3/SM4（v8.2-SM）· 有限域（GCM/ECC）</text>
  <text x="762" y="512" font-size="10.5" fill="#6b7280" text-anchor="start">· 独立授权许可（实现时可含/不含）</text>
  <rect x="1120" y="436" width="300" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1132" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU + L1D（§8 p69-72）</text>
  <text x="1132" y="478" font-size="10.5" fill="#047857" text-anchor="start">· L1D 64KB 4-way 64B · tag/data SECDED</text>
  <text x="1132" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 独占监视器（§8.3）· DC ZVA 64B</text>
  <text x="1132" y="512" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· write streaming（read allocate）L1+L2 双级（§8.5）</text>
  <path d="M340,510 L364,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M720,510 L744,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="240" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="706" width="150" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">预取 + MMU</text>
  <text x="196" y="723" font-size="11.5" fill="#3f7a58" font-style="italic">两级 TLB + MMUTC SED（Table 6-1 p57-58）</text>
  <rect x="50" y="766" width="360" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">预取器（§8.4）</text>
  <text x="62" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">load 侧 VA → L1+L2 · store 侧 PA → 仅 L2（分裂式）</text>
  <text x="62" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">+ TLB 预取器 · region 预取器（CPUECTLR 可控）</text>
  <rect x="440" y="766" width="480" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="452" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MMU：两级 TLB + MMUTC（§6.1）</text>
  <text x="452" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· iTLB 48 项全相联 · dTLB 44 项全相联 · L2 TLB 1280 项 5-way I/D 共享</text>
  <text x="452" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· TRBE TLB 2 项 · 翻译表预取器（ECtlR 可关）· L2 命中 +3c 罚</text>
  <text x="452" y="842" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· MMUTC：SED（Table 11-1）——N1 仅 2-bit 交错 parity，N2 升级</text>
  <rect x="950" y="766" width="470" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="962" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">观测单元</text>
  <text x="962" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">48-bit PA · PMU 6 计数器（§3.1 p42）</text>
  <text x="962" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">SPE（v8.4 可选实现）· AMU</text>
  <text x="962" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">GIC CPU 接口 · RNG</text>
  <text x="962" y="859" font-size="10.5" fill="#6b7280" text-anchor="start">Debug/ELA 可选（§2.5）</text>
  <rect x="30" y="1010" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="986" width="250" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="1003.5" font-size="14" fill="#ffffff" font-weight="600">内存层级（L1 → L2 → DSU-110）</text>
  <text x="296" y="1003" font-size="11.5" fill="#6d5aa0" font-style="italic">异步 CPU bridge 连 DSU-110（缓冲+同步核与簇）· 组件常在（All components always present §3）</text>
  <rect x="50" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="215.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 64KB 4-way</text>
  <text x="215.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行（§3.1 p42）</text>
  <text x="215.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SECDED（Table 11-1）</text>
  <text x="215.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">双位错=检出/上报/延迟</text>
  <text x="215.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">dirty 行双位错→数据可能丢失（显式）</text>
  <rect x="410" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="575.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 512KB/1024KB 8-way</text>
  <text x="575.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">统一 I+D（§3.1 p42 · §9）</text>
  <text x="575.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SECDED</text>
  <text x="575.0" y="1122" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">L2 TQ：SECDED（表 11-1 唯一队列类保护）</text>
  <text x="575.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">victim 表未列（N1 明示 None，N2 未披露）</text>
  <rect x="770" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="935.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">DSU-110 簇</text>
  <text x="935.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">L3/SCU/snoop filter = DSU TRM 范围</text>
  <text x="935.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">CPU bridge 异步（频/电/面积解耦）</text>
  <text x="935.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">DSU 依赖特性见 TRM §2.3</text>
  <rect x="1130" y="1046" width="290" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1275.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">SoC 侧</text>
  <text x="1275.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">48-bit PA</text>
  <text x="1275.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">GIC CPU 接口</text>
  <text x="1275.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">RNG · Debug/ELA</text>
  <rect x="30" y="1290" width="1420" height="160" rx="10" fill="#f0fdf4" stroke="#047857" stroke-width="2"/>
  <text x="46" y="1316" font-size="15" fill="#047857" font-weight="700">RAS 扩展（TRM §11 p96-100）——含至 Armv9.0-A 全量</text>
  <text x="46" y="1338" font-size="11.5" fill="#1f2937">保护矩阵（Table 11-1）</text>
  <text x="406" y="1338" font-size="11.5" fill="#047857">SECDED = L1D tag/data · L2 tag/data · L2 TQ；SED = L1I tag/data · L0 MOP · MMUTC</text>
  <text x="46" y="1357" font-size="11.5" fill="#1f2937">TRM 原文承认</text>
  <text x="406" y="1357" font-size="11.5" fill="#b91c1c">SED RAM 双位错 core does not detect … might cause data corruption——I$/MOP/MMUTC 是承认的 SDC 通道</text>
  <text x="46" y="1376" font-size="11.5" fill="#1f2937">错误遏制（§11.2）</text>
  <text x="406" y="1376" font-size="11.5" fill="#1f2937">数据错误经 poison 传播不静默扩散 · evict 双错可 poison · L1D/L2 tag 不可遏制错误（UC 声明）</text>
  <text x="46" y="1395" font-size="11.5" fill="#1f2937">错误注入（§11.5）</text>
  <text x="406" y="1395" font-size="11.5" fill="#047857">CE（L1D 单 ECC）· DE（L1→L2 evict 双 ECC / snoop）· UC（L1 tag evict 后双 ECC）· ERR0PFGCDN 倒计数</text>
  <text x="46" y="1414" font-size="11.5" fill="#1f2937">报告机制</text>
  <text x="406" y="1414" font-size="11.5" fill="#047857">FHI=nCOREFAULTIRQ · ERI=nCOREERRIRQ · 消费时 SEA/AEA/ERI · MEMORY_ERROR PMU 事件联动 · ESB · Node 0=L1+L2</text>
  <text x="46" y="1433" font-size="11.5" fill="#1f2937">SDC 视角</text>
  <text x="406" y="1433" font-size="11.5" fill="#b45309">N2 相对 N1 的增量 = MMUTC SED + MOP SED；新增 MOP 是弱保护×高命中率×指令面三重叠加的独立注入靶点</text>
</svg>

</div>

独有/标志性：**L0 MOP 缓存 1536 项 4-way skewed**（存已译码优化指令，SED 弱保护×高命中×指令面，五款唯一 MOP）；
**MMUTC 拉进 SED**（N1 仅 2-bit 交错 parity）；AArch32 EL0（A32/T32/A64，与 N1 相同）；write streaming L1+L2 双级；
load VA / store PA 分裂预取器（N3 改为 VA+PC 双源引擎）。

### Neoverse N3

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1450" width="1480" height="1450" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1450" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">Arm Neoverse N3 微架构功能图（Armv9.2-A · 平衡性能核 · DSU-120 Direct connect）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = N3 防御结构：分裂式 L2 TLB（small 1536 + medium 256）+ aux tag + ECC granule 可配 + MPAM。出处：Neoverse N3 TRM 107997_0001_03</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="240" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（按序 · TRM §2.1 p31）</text>
  <text x="286" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">L1I 32KB 或 64KB（可配）4-way 64B · iTLB 全相联 32 项 · 仅 A64 译码（无 AArch32）· 动态分支预测器单列组件</text>
  <rect x="50" y="166" width="260" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">程序流预测（§6.3 p59）</text>
  <text x="62" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">BTB + BP 方向预测器（历史）</text>
  <text x="62" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">返回栈（BL/BLR* push · RET* pop）</text>
  <text x="62" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">静态 + 间接预测器</text>
  <text x="62" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">不预测：ERET/SVC/HVC/SMC</text>
  <rect x="340" y="166" width="230" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="455.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 32/64KB 4-way</text>
  <text x="455.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行（§2.1 · §1.2 可配）</text>
  <text x="455.0" y="225" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SED（Table 10-1）</text>
  <text x="455.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">硬件一致性 §6.4（与 L2 弱包含）</text>
  <rect x="600" y="166" width="220" height="130" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="710.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">译码（§2.1）</text>
  <text x="710.0" y="208" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">仅 A64（无 A32/T32）</text>
  <text x="710.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">AArch64 内部格式</text>
  <text x="710.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">无 MOP 结构（N2 删减）</text>
  <rect x="850" y="166" width="220" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="960.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">重命名 / 发射</text>
  <text x="960.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">重命名 + issue queues</text>
  <text x="960.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">（§2.1 组件图）</text>
  <text x="960.0" y="242" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">PRF 保护未披露</text>
  <rect x="1100" y="166" width="320" height="130" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="1112" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MPAM（§1.1 Cache features）</text>
  <text x="1112" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">Memory System Resource</text>
  <text x="1112" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">Partitioning &amp; Monitoring</text>
  <text x="1112" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">缓存/带宽 QoS 硬件分区</text>
  <text x="1112" y="259" font-size="10.5" fill="#6b7280" text-anchor="start">（920 平台级 MPAM 有 ACPI 表；N3 为核内特性）</text>
  <path d="M310,230 L334,230" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <path d="M570,230 L594,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M820,230 L844,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="260" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute（§2.1 p31-32）</text>
  <text x="306" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">整数执行 + 向量执行（NEON+FP · SVE/SVE2 128b · Crypto 可选含 SHA-3/SM3/SM4）· 平衡性能/低功耗/面积受限定位</text>
  <rect x="50" y="436" width="290" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">整数执行单元</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 算术/逻辑数据处理（§2.1）</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· RNG（§16）· Utility bus（§11）</text>
  <text x="62" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· ALU 数据通路无保护披露</text>
  <rect x="370" y="436" width="350" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="382" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">向量执行：SVE / SVE2（§14）</text>
  <text x="382" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 向量长度 128-bit · NEON+FP32/FP64</text>
  <text x="382" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· Crypto：AES · SHA-1/2 · SHA-3 · SM3/SM4</text>
  <text x="382" y="512" font-size="10.5" fill="#1f2937" text-anchor="start">· EOR3/XAR/BCAX 随 SVE2 免费（免 Crypto 授权）</text>
  <rect x="750" y="436" width="350" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="762" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">L2 预取引擎（VA + PC 双源）</text>
  <text x="762" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· §8 L2 内存系统：虚拟地址 + 程序计数器</text>
  <text x="762" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 各引擎分别向 L2 预取（next-line/stride 类）</text>
  <text x="762" y="512" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· N2 为 load VA / store PA 分裂预取，N3 改双源引擎</text>
  <rect x="1130" y="436" width="290" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1275.0" y="458" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">观测单元</text>
  <text x="1275.0" y="478" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">PMU 6 或 20 计数器（可配）</text>
  <text x="1275.0" y="495" font-size="10.5" fill="#1f2937" text-anchor="middle">SPE（§22 v8.7）· ETE+TRBE</text>
  <text x="1275.0" y="512" font-size="10.5" fill="#1f2937" text-anchor="middle">AMU（§21）· ELA 组件化</text>
  <path d="M340,510 L364,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M720,510 L744,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="240" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="706" width="250" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">访存 + MMU（分裂式 L2 TLB）</text>
  <text x="296" y="723" font-size="11.5" fill="#3f7a58" font-style="italic">L1D 32/64KB 可配 4-way 64B · tag/data/aux tag 全 SECDED · LSE 原子在 L1 内存系统实现（§7.3）</text>
  <rect x="50" y="766" width="360" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU + L1D（§7 p62-65）</text>
  <text x="62" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· L1D 32/64KB（可配）4-way 64B</text>
  <text x="62" y="825" font-size="10.5" fill="#047857" text-anchor="start" font-weight="600">· tag/data/aux tag 全 SECDED</text>
  <text x="62" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· LSE 原子在 L1 内存系统实现（§7.3）</text>
  <text x="62" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">· 独占监视器（§7.4）· write streaming（§7.2）</text>
  <text x="62" y="876" font-size="10.5" fill="#6b7280" text-anchor="start">· 预取（§7.5）</text>
  <rect x="440" y="766" width="480" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="452" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MMU：分裂式 L2 TLB + walk cache（§5.1 p50 Table 5-1）</text>
  <text x="452" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· iTLB 32 项 · dTLB 48 项（全相联）· SPE TLB 1 项 · TRBE TLB 1 项</text>
  <text x="452" y="825" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· small-page TLB（4K/16K/64K）：6-way 1536 项（reduced-area 4-way 1024）</text>
  <text x="452" y="842" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· medium-page TLB（2M/32M/512M）：4-way 256 项 + walk cache</text>
  <text x="452" y="859" font-size="10.5" fill="#047857" text-anchor="start" font-weight="600">· TLB：SED（Table 10-1，措辞从 N2 的 MMUTC 升级为 TLB）</text>
  <rect x="950" y="766" width="470" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="962" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">内存层级补充</text>
  <text x="962" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">单核 Direct connect 配置无 L3/SCU/snoop filter（§1 图 1-1）</text>
  <text x="962" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">CPU bridge 连 DSU-120</text>
  <text x="962" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">48-bit VA/PA（§1.1）</text>
  <rect x="30" y="1010" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="986" width="320" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="1003.5" font-size="14" fill="#ffffff" font-weight="600">内存层级（L1 → L2 → DSU-120 Direct connect）</text>
  <text x="366" y="1003" font-size="11.5" fill="#6d5aa0" font-style="italic">单核 Direct connect 配置无 L3/SCU/snoop filter · CPU bridge 连 DSU-120</text>
  <rect x="50" y="1046" width="350" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="225.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 32/64KB 4-way</text>
  <text x="225.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行（§2.1 · §9.1 编码验证 4-way）</text>
  <text x="225.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SECDED</text>
  <text x="225.0" y="1122" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">aux tag: SECDED（Table 10-1 新增行）</text>
  <text x="225.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">UC 双位错=检出并上报/延迟（显式非静默）</text>
  <rect x="430" y="1046" width="380" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="620.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 128KB–2MB 8-way 2-bank</text>
  <text x="620.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">PIPT · 动态偏置替换策略（Table 8-1）</text>
  <text x="620.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SECDED · TQ 亦 SECDED</text>
  <text x="620.0" y="1122" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">ECC granule 可配 128/256 bit（§1.2）</text>
  <text x="620.0" y="1139" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">五款唯一可配纠错粒度</text>
  <rect x="840" y="1046" width="300" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="990.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">DSU-120（Direct connect）</text>
  <text x="990.0" y="1088" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">CHI Issue E 接口</text>
  <text x="990.0" y="1105" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">256-bit 读/写通道宽</text>
  <text x="990.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">单核配置：无 L3 / 无 SCU</text>
  <text x="990.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">（L3 保护 = DSU TRM 范围）</text>
  <rect x="1170" y="1046" width="250" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1295.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">SoC 侧</text>
  <text x="1295.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">48-bit VA/PA（§1.1）</text>
  <text x="1295.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">GIC CPU 接口 · RNG</text>
  <text x="1295.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">ELA-600 可选（§1.2）</text>
  <rect x="30" y="1290" width="1420" height="160" rx="10" fill="#f0fdf4" stroke="#047857" stroke-width="2"/>
  <text x="46" y="1316" font-size="15" fill="#047857" font-weight="700">RAS 扩展（TRM §10 p76-80）——含至 Armv9.2-A · 五款中防御矩阵最厚</text>
  <text x="46" y="1338" font-size="11.5" fill="#1f2937">保护矩阵（Table 10-1）</text>
  <text x="406" y="1338" font-size="11.5" fill="#047857">SECDED = L1D tag / aux tag / data · L2 tag/data · L2 TQ；SED = L1I tag/data · TLB（措辞从 N2 的 MMUTC 升级为 TLB）</text>
  <text x="46" y="1357" font-size="11.5" fill="#1f2937">错误遏制（§10.2）</text>
  <text x="406" y="1357" font-size="11.5" fill="#1f2937">poison 传播 + evict 双错 poison + ESB 隔离不精确异常 · L1D/L2 tag UC 不可遏制声明与 N2 一致</text>
  <text x="46" y="1376" font-size="11.5" fill="#1f2937">错误注入（§10.5）</text>
  <text x="406" y="1376" font-size="11.5" fill="#047857">CE（L1D 单 ECC）· DE（L1→L2 evict/snoop 双 ECC）· UC（L1 和 L2 tag evict 后双 ECC——比 N2 的仅 L1 tag 扩展）</text>
  <text x="46" y="1395" font-size="11.5" fill="#1f2937">寄存器风格</text>
  <text x="406" y="1395" font-size="11.5" fill="#b45309">带 _EL1 后缀（ER1PFGCDN_EL1，RASv1.1 风格）· FHI/ERI · SEA/AEA/ERI · MEMORY_ERROR PMU 事件</text>
  <text x="46" y="1414" font-size="11.5" fill="#1f2937">Node 0 覆盖</text>
  <text x="406" y="1414" font-size="11.5" fill="#b45309">明确覆盖 L1 + L2 + MMU/TLB（N2 为 L1+L2；N3 把地址翻译部件纳入 RAS 节点）</text>
  <text x="46" y="1433" font-size="11.5" fill="#1f2937">SDC 视角</text>
  <text x="406" y="1433" font-size="11.5" fill="#047857">披露范围内相对敏感性最低——TLB/翻译路径在 N3 获 SED；残余弱点：SED 类双位错仍是 corruption 通道；执行单元/PRF/LSQ 依旧无披露</text>
</svg>

</div>   

---
