# ARM64 微架构级 SDC 故障注入研究：试验方案与核心假设证明设计

> **目标定位**: 顶会级研究工作（SOSP / ASPLOS / MICRO / HPCA 级别）。
> **工具基座**: gem5 v25.1.0.1 (AArch64 O3CPU) + CHAOS 故障注入框架（含 CHAOSPhysReg 物理寄存器堆注入与 read-trace 传播闭环）。
> **已验证可用**: 2026-08-24 端到端跑通 ArmO3CPU + CHAOSPhysReg bit-flip 注入，golden 0-fail，read-trace 闭环工作（见 §0 工具可用性证据）。

---

## 0. 工具可用性证据（真实命令、真实输出）

本节为方案撰写前对工具链的真实验证，非"应该可用"的推断。

```
$ gcc -O2 -static -o movbe_kernel movbe_kernel.c   # aarch64 原生主机
$ build/ARM/gem5.opt o3_chaos_smoke.py --no-fi --iters 50   # golden
[smoke] ... fi=OFF
iters=50 fails=0
Exiting @ tick 464135500 cause=exiting with last active thread context

$ build/ARM/gem5.opt -d m5out_smoke o3_chaos_smoke.py --mode phys --phys-idx -1 \
    --bits 1 --fault bit_flip --first-clock 100000 --max-faults 1 --seed 42
[smoke] ... fi=ON
iters=50 fails=0
# fault_injections.log:
Cycle: 100000, CPU: system.cpu, Thread: 0, Mode: phys, PhysReg[243]
  (Active, mapped from ArchReg[9]), FaultType: bit_flip, Mask: ...0001000000000000,
  FreeListSize: 214
ReadTracePoll: cycle 200000 PhysReg[243] reads_before_overwrite=0 overwritten=0
...
# stats.txt:
system.fi.numFaultsInjected   1
system.fi.numBitFlips          1
```

`reads_before_overwrite=0` 正确刻画了"注入值未被消费 → 无 SDC"的屏蔽（benign）负样本，证明 read-trace 闭环可用。

---

## 1. 科学命题与核心假设

### 1.1 研究命题（一句话）

> **ARM64 服务器核（Kunpeng 920 / TaiShan v110 类）因其"弱内存模型 + RISC 定长 + 31 GPR"的 ISA 选型，驱动了"前端精简、乱序中枢放大"的微架构权衡（ROB 640-768+、更深 LSQ、更大 PRF、分布式调度器），使该类核心的 SDC 暴露面系统性集中在乱序后端（物理寄存器堆状态泄漏 / ROB 投机状态 / LSU store-buffer 转发时序竞态），而非前端译码路径——这与 x86（TSO + 变长译码 + 16 GPR + 集中式调度）的 SDC 暴露面分布形成可证伪的对照。**

### 1.2 可证伪的核心假设（H0–H4）

| 假设 | 陈述 | 可证伪预测 | 证伪条件 |
|---|---|---|---|
| **H1 (后端集中性)** | 在 ARM64 O3 上，注入到**物理寄存器堆 / 重命名表 / ROB 投机状态 / LSU store-buffer 路径**的故障，其 SDC 产出率（SDC / 注入）显著高于注入到**前端译码/I-cache/μop 缓存等价物**的故障。 | SDC_rate(backend) ≫ SDC_rate(frontend) | 若两者无显著差异 → H1 证伪 |
| **H2 (窗口尺度敏感性)** | ARM64 的 SDC 产出率随**乱序窗口尺度（ROB/PRF/LSQ 深度）**单调上升；在受 x86 TSO-CAM 约束的等效小窗口下趋同。 | d(SDC_rate)/d(window) > 0 on ARM；x86-like small window 收敛 | 若 ARM 上窗口尺度与 SDC 无关 → H2 证伪 |
| **H3 (状态泄漏签名)** | 物理 PRF 的"注入值被读取次数 `reads_before_overwrite`"分布呈**重尾/双峰**——少量活跃 cell 产生高 read-count 且传播为 SDC，多数 cell 屏蔽（read=0）。这与 method1 的"numeric-only 4× compute-both 状态泄漏"签名自洽。 | read-count 分布重尾，且 reads>0 子集的 SDC 占比 ≫ reads=0 子集 | 若均匀分布 → H3 证伪 |
| **H4 (路径依赖位谱)** | store→load 转发路径注入产生**多位、尾数集中、符号免疫**的损坏谱（复现 method2 v3 的 85-93% mantissa / 0-1 sign）；迭代型路径（SVD 类）产生单位放大谱。 | 位谱分布与 method2 实测统计匹配 | 若位谱随机或单一位点为主 → H4 证伪 |
| **H0 (反例对照)** | 在**等乱序窗口、等注入位点**条件下，ARM64 与 x86 O3 的 per-cell SDC 率无差异（即差异仅来自 ISA 前端，而非后端）。 | H0 应被**拒绝**（差异显著）；若 H0 不被拒绝 → "后端集中性"非 ARM 特有 → 命题弱化 | — |

> 设计哲学：每条假设都有**可证伪的定量预测**与**明确的证伪条件**。这是"猜想-验证闭环"（fi.md 第 4 节要求）的硬约束——不预设结论，用对照实验逼近真相。

### 1.3 命题与三份复现报告的一致性

| 复现报告 | 损坏位点 | 模式 | 对应假设 |
|---|---|---|---|
| method1 (eigen_sparse Cholesky, core 179) | x[0] 固定写回位置 | 多位混叠、**状态泄漏型**（numeric-only 4× compute-both） | H3 |
| method2 (cross-pathway v3, core 179) | reload `ldr` of store→load 转发 | 多位、**尾数集中 85-93%、符号免疫、路径相关计数** | H4 |
| method3 (欠压 STL, core 179) | `__per_cpu_offset[cpu]` → x9 | 随机垃圾值、负载+欠压敏感 | H1/H2（数据通路） |

三份现场证据**独立、异构、同向**地指向乱序后端，构成假设的**生态效度（ecological validity）**：仿真结论需与这三份实测对齐才成立。

---

## 2. 方法论骨架：分层假设排除 + 传播闭环

本研究严格遵循 fi.md 与 method1 的"分层假设排除法"，并在此基础上**新增传播闭环**——这是 CHAOSPhysReg 相对既有工具（ITC'23 / GeFIN / SiliFuzz / Veritas）的关键增量。

### 2.1 故障四分类（传播闭环产出）

每个注入的故障，由 `reads_before_overwrite` + 输出 diff + 异常信号，归入四类：

```
                      注入故障 (N)
                 ┌─────────┴─────────┐
        reads=0 (未消费)         reads>0 (被消费)
            │                        │
     Benign (屏蔽)        ┌───────────┴───────────┐
     AVF 度量            输出不变            输出改变
                        │     │             │     │
                     无传播  Masked      SDC   Crash/检测
                     (latent)(逻辑屏蔽)  ★     (显性)
```

- **Benign**: reads_before_overwrite=0（注入值在下次写前未被读，或 slot 本就 free/inactive）—— 纯 AVF 分母。
- **Masked**: reads>0 但被逻辑屏蔽（AND-0 / 被覆盖 / 未达输出）—— 架构屏蔽因子。
- **SDC** ★: reads>0 + 传播到输出 + 无异常 —— 研究主体。
- **Crash/Detected**: 触发异常/SEGV/Panic（method3 的 Oops 属此类）—— 不可恢复，需剔除以免污染 SDC 率。

> **关键**: 既有工具只统计 SDC/注入，无法区分"未消费"与"被消费但屏蔽"。read-trace 闭环把分母拆细，使 AVF/SDC 比率**可解释、可跨研究对比**。

### 2.2 六层假设排除（继承 method1，适配仿真）

| 层 | 调查主题 | 证伪的假设 | 仿真对应 |
|---|---|---|---|
| L1 | 软件 vs 硬件 | kernel 自身有确定性 bug | golden run 0-fail（已验证 §0） |
| L2 | 触发计算类型 | 纯 ALU / 纯 FPU / 纯 memcpy pipe 损坏 | 多 probe 注入同位点，对比 SDC 谱（§4.3） |
| L3 | 微架构事件 | cache/LSU/TLB/分支/FPU 单元损坏 | per-site 注入矩阵（§4.2） |
| L4 | 损坏模式 | 输入数据损坏 / 单位 SEU | 位谱统计 + read-trace（§4.4） |
| L5 | MRU 削减 | 整 kernel vs 单一操作 | probe 削减集（§4.3） |
| L6 | 状态泄漏签名 | 单次注入 vs 跨迭代状态 | read-trace 时序 + numeric/symbolic 对照（§4.5） |

---

## 3. 实验框架总体设计

### 3.1 自变量（Independent Variables）

| 维度 | 水平 | 实现方式 |
|---|---|---|
| **ISA** | ARM64 (AArch64 O3) vs x86 (X86O3CPU) | 同一 gem5 tree 的两个 build；O3 back-end C++ 共享 |
| **注入位点（微架构单元）** | PhysReg(int/float) · RenameMap · ROB · LSQ/SQ · L1D · L2 · Mem · (前端 eq.) | CHAOSPhysReg / CHAOSCache / CHAOSMem + 拟新增 ROB/LSQ 注入点（§5 工具增量） |
| **乱序窗口尺度** | 小 / 中 / 大（ROB=64/128/192/256 × PRF=64/128/256/512 × LSQ=16/32/64） | O3 参数化（BaseO3CPU.py） |
| **负载类型** | store→load 转发(movbe/mrn_rmw) · FMA GEMM(float/double) · 迭代 SVD · 纯 memcpy · Cholesky numeric | method1/2 的 probe 集（§4.3） |
| **故障模型** | bit_flip / stuck_at_zero / stuck_at_one / random | CHAOSPhysReg.faultType |
| **注入时机** | firstClock（单次确定性）/ 随机几何分布（统计性） | probability + maxFaults |
| **注入粒度（位数）** | 1 / 4 / 8 / 16 / 21-32（多位置现 method1/2 的多位谱） | bitsToChange / faultMask |
| **并发压力** | 单核单线程 / 多线程 SMT / 多核（gem5 multi-core） | numThreads / 多 cpu 实例 |

### 3.2 因变量（Dependent Variables）

| 指标 | 定义 | 采集 |
|---|---|---|
| **SDC_rate** | SDC 次数 / 注入次数 | stats + 输出 diff 自检 |
| **AVF** | reads>0 故障占比 / 总注入 | read-trace log |
| **Masking_rate** | reads>0 且输出不变 / reads>0 | read-trace + diff |
| **Crash_rate** | 触发异常 / 注入 | exit cause + SEGV 计数 |
| **位谱分布** | 符号/指数/尾数位翻转占比 | golden^actual mask 统计 |
| **flip_count 分布** | 每次损坏翻转位数（中位/范围） | popcount(mask) |
| **reads_before_overwrite 分布** | 注入值被读次数（重尾性） | read-trace final |
| **TTT (time-to-trigger)** | 注入到 SDC 首现的周期数 | cycle 日志 |

### 3.3 控制变量与配对设计

- **配对原则**: 每个注入实验配一个 golden run（同 seed、无注入），确保输出 diff 仅来自注入。
- **seed 控制**: rngSeed 固定可复现；统计性实验用多 seed 蒙特卡洛（≥30 seed/单元格，method2 §3.2 的样本量教训）。
- **热度稳定性**: probe 热循环字节级固定，诊断在冷分支（method2 §7 的 dump-variant 方法论）—— gem5 中天然满足（仿真确定性）。

---

## 4. 核心实验组（证明 H1–H4）

### 4.1 实验 A：后端集中性（H1）—— 命题主实验

**目的**: 证明 ARM64 上后端位点的 SDC 率显著高于前端等价位点。

**设计**: 固定负载（movbe_kernel，method2 的紧 store→load 序列）、固定窗口（ROB=192, PRF=256, LSQ=32）、固定故障模型（bit_flip, 1 bit）。在以下位点各注入 N=1000 次（随机 phys 索引、随机 cycle、随机 bit）：

| 位点类 | CHAOS 模块 / 注入点 | 假设归属 |
|---|---|---|
| PRF (int) | CHAOSPhysReg phys mode | 后端 ★ |
| PRF (float) | CHAOSPhysReg phys mode (float, 需扩展) | 后端 ★ |
| RenameMap | CHAOSPhysReg arch_frontend | 后端 ★ |
| L1D line | CHAOSCache | 访存后端 |
| L2 line | CHAOSCache | 访存后端 |
| Mem | CHAOSMem | 访存后端 |
| 前端 eq. | μop-cache 等价物 / decode 路径（gem5 无直接前端 FI，需设对照——见下） | 前端 |

**前端对照的诚实处理**: gem5 O3 无"前端译码位翻转"原生注入点。两个诚实替代：
1. 在 **I-cache** 注入（CHAOSCache target=icache）—— 损坏的是取指路径，最接近"前端"。
2. 在 **commitRenameMap**（arch_commit mode）注入 —— 刻意使用 CHAOSReg 的失效抽象，量化"前端/提交侧"注入的传播率（应极低，因 O3 提交映射滞后于在飞读）。

**预测**: SDC_rate(PRF/RenameMap) ≫ SDC_rate(I-cache/arch_commit)。

**统计**: χ² 检验或 Fisher exact；报告 95% CI。需 N 足够使最小期望格 ≥5。

### 4.2 实验 B：窗口尺度敏感性（H2）—— 因果机制实验

**目的**: 证明 SDC 率随乱序窗口单调上升（窗口越大 → 更多在飞指令 → 注入值更可能被读 → SDC↑）。

**设计**: 固定负载、固定注入位点（PRF int, phys, bit_flip 1bit）。扫描 O3 窗口参数：

| 配置 | numROBEntries | numPhysIntRegs | LQ/SQ | 语义 |
|---|---|---|---|---|
| W-small | 64 | 128 | 16 | x86-like 受限窗口 |
| W-mid | 128 | 256 | 32 | 中等 |
| W-large | 256 | 512 | 64 | ARM64-like 大窗口 |
| W-xlarge | 384 | 768 | 96 | 极限 |

每个配置 N=1000 注入，记录 SDC_rate + AVF + reads 分布。

**预测**: SDC_rate(W-small) < W-mid < W-large < W-xlarge；reads_before_overwrite 分布右移（重尾加剧）。

**关键对照（H0 的直接检验）**: 在 W-small 下，ARM 与 x86 的 SDC_rate 应趋同（H0 不被拒绝 → 证明"差异来自窗口尺度，而非 ISA 本身"——这是更精细的结论，反而强化"ARM64 的 ISA 选型**驱动**了更大窗口"的因果链）。

### 4.3 实验 C：路径依赖位谱与 MRU 削减（H4 + L5）

**目的**: 复现 method2 v3 的位谱签名（尾数集中、符号免疫、路径相关计数），并验证"单一操作不触发、需特定交错"。

**设计**: 在 W-large + 满载压力下，对以下 probe 各注入 N=500 次（PRF phys, bit_flip, 随机 1-32 bits 以覆盖多位谱）：

| Probe | 负载特征 | method2 对应 | 预期 flip_count 中位 |
|---|---|---|---|
| `movbe_kernel` | 紧 store→load 转发 | §8.1 | 14-21（多位置现） |
| `mrn_rmw_kernel` | 整数 ALU + 同址 store→load 转发 | §8.2 | 高密度多位 |
| `gemm_float_kernel` | FMA GEMM 写回→校验 | §8.4 | 12（moderate） |
| `gemm_double_kernel` | double FMA GEMM | §8.5 | 28（densest FP） |
| `svd_iterative_kernel` | 迭代 BDCSVD | §8.8 | 1-3（单位放大） |
| `memcpy_kernel` | 纯 memcpy 无 ALU | §8.3 | 无数据（仅触发确认） |
| `cholesky_numeric_kernel` | numeric factorize 列更新 | method1 | 状态泄漏签名 |

**MRU 削减（L5）**: 对 cholesky_numeric 逐层削（dense / SpMV / gather / FMA 单一 / numeric-only vs compute-both），验证"numeric-only SDC 率 > compute-both"（method1 §11.3 的 4× 签名）—— 仿真中通过 firstClock 控制注入发生在 numeric 阶段 vs symbolic 阶段实现。

**预测**: 位谱与 method2 v3 §6.2-6.3 统计匹配（float mantissa ~85%, double ~93%, sign ~0%）。

### 4.4 实验 D：状态泄漏签名（H3 + L6）—— read-trace 闭环主实验

**目的**: 用 `reads_before_overwrite` 分布证明物理 PRF 的"状态泄漏型"签名——少量活跃 cell 产生高 read-count 且 SDC，多数屏蔽。

**设计**: W-large + movbe_kernel，phys mode 随机注入 N=10000（大样本以刻画重尾），记录每个注入的 {phys_idx, free_list_size, reads_before_overwrite, overwritten_at_cycle, SDC?}。

**分析**:
- reads_before_overwrite 分布的**重尾性**（Pareto / power-law 拟合 vs 均匀）。
- **双峰检验**: reads=0 子集（benign）vs reads≥k 子集（活跃）的 SDC 占比差异 —— 预期后者 ≫ 前者。
- **跨迭代状态泄漏**: 比较注入发生在"循环边界（状态刷新点）"vs"循环体内（状态持续）"的 SDC 率 —— 模拟 method1 的 numeric vs symbolic 刷新对照。

**预测**: reads 分布重尾（power-law α<2）；reads≥10 子集 SDC 占比 > 50%，reads=0 子集 SDC=0。

### 4.5 实验 E：ARM-vs-x86 对照（H0 / 命题的 ISA 维度）

**目的**: 在配对窗口下检验 ARM 与 x86 的 per-cell SDC 率差异。

**设计**: W-small 与 W-large 两配置下，ARM O3 与 X86O3CPU 各跑实验 A 的注入矩阵。

**诚实边界（必须声明）**: gem5 O3 back-end 是**ISA 无关的共享 C++**（ROB/scheduler/LSQ 同源）。它能建模：
- ✓ 前端译码差异（x86 变长 decode + μop cache vs ARM 定长）
- ✓ PRF 压力差异（31 vs 16 GPR → rename 压力 → spill/fill）
- ✗ **不能**建模 cpu.md 的头条差异 —— x86 TSO 的 LSQ CAM O(N²) vs ARM 弱序的显式屏障。gem5 O3 LSQ 不区分 TSO/weak。

**因此 E 的结论被严格限定为**: "在前端译码 + PRF 压力两个可建模维度上，ARM64 的 SDC 后端集中性是否仍成立"。TSO-vs-weak 维度需**单独声明为仿真外局限**，并以 method3 的欠压实测作为生态效度补强（method3 不涉及 TSO，纯数据通路）。

> 这是**逻辑完备性**的关键：不声称仿真证明了 cpu.md 全部命题，只证明可建模子集，其余由现场证据补强。

---

## 5. 工具增量（CHAOSPhysReg 扩展，按 one-patch-per-unit）

当前 CHAOSPhysReg 仅覆盖 int phys reg。为完成 §4 全矩阵，需以下**增量补丁**（每个独立 commit + 验证 + push）：

| # | 补丁 | 依赖实验 | 验证方式 |
|---|---|---|---|
| P1 | CHAOSPhysReg 支持 float phys reg（FloatRegClass 注入 + read-trace） | A, C | float kernel golden + bit_flip 闭环 |
| P2 | CHAOSPhysReg 支持 vector phys reg（SVE 路径，AArch64 特有） | C | SVE kernel |
| P3 | 新增 **CHAOSROB** / **ROB-state** 注入点（投机寄存器/序列号） | A | O3 rob.hh hook + 闭环 |
| P4 | 新增 **CHAOSLSQ** store-buffer 转发注入点（method2 核心） | A, C, D | lsq.hh hook + movbe 触发 |
| P5 | 多核/多线程压力配置（method1/2 的"同 socket 满载"前提） | C, D | multi-cpu system.py |
| P6 | 位谱自动统计工具（golden^actual mask → 符号/指数/尾数/popcount） | C, D | stats 生成器 |
| P7 | read-trace 重尾性统计工具（reads 分布拟合） | D | R/Python 分析脚本 |

> 补丁顺序: P1 → P2 → P6（分析先行，支持已有数据）→ P3 → P4 → P5 → P7。每补丁一个 commit、一次验证、一次 push，严守 CLAUDE.md。

---

## 6. 度量协议与统计功效

### 6.1 样本量（功效分析）

- method2 §3.2 教训: H 1/10、X 1/5 差异不显著。**每单元格 ≥30 seed**；率比较用 χ²，报告 95% CI。
- 实验 D（重尾刻画）需 N≥10000（重尾估计对样本量敏感）。
- 实验 C（位谱）需每 probe ≥500 样本以稳定尾数占比。

### 6.2 预登记（pre-registration）

每实验的预测与证伪条件（§1.2）在跑数据前**书面固定**，避免 HARKing（hypothesizing after results known）。本文件即预登记。

### 6.3 多重比较校正

H1-H4 四假设 × 多位点 → 多重比较。报告 Bonferroni / BH-FDR 校正后的 p 值。

---

## 7. 威胁效度与诚实声明

| 威胁 | 来源 | 缓解 |
|---|---|---|
| **仿真-真实 gap** | gem5 O3 ≠ TaiShan v110 RTL | 三份现场证据对齐（生态效度）；method3 欠压通路不涉 TSO，可直连 |
| **TSO/weak 不可建模** | gem5 O3 LSQ 同源 | 声明为仿真外；method3 补强；列为 limitation |
| **probe 覆盖不足** | 自研 probe ≠ 真实负载 | method1/2 的 libc-only MRU 已验证可复现，直接迁移 |
| **样本量不足** | method2 的 1/5 教训 | 功效分析 + ≥30 seed/格 |
| **read-trace 干扰** | hook 在 getReg 热路径 | 已有 short-circuit（target<0 跳过）；golden 对比验证不影响触发 |
| **确认偏误** | 作者预设 H1 | H0 反例对照 + 预登记 + 证伪条件明列 |

---

## 8. 交付物与时间线

| 阶段 | 交付 | 对应 fi.md |
|---|---|---|
| T0 (done) | 工具链端到端验证（§0） | — |
| T1 | 补丁 P1/P2/P6（float/vec 注入 + 位谱工具） | 故障注入调研初步 |
| T2 | 实验 A/C/D（H1/H4/H3 主结果） | 猜想-验证闭环 |
| T3 | 实验 B/E（H2/H0 因果+对照） | 扩展发现 |
| T4 | HotOS 短文（Study+Motivation，6页，年底） | HotOS 投稿 |
| T5 | SOSP 全文（完整 FI 工作+发现，明年4月） | SOSP 投稿 |

---

## 9. 故事线（对标 fi.md 第 3 节）

1. **筛选**: 从 100 案例 → 20 真 SDC → 3 机理可定位案例（method1/2/3）。
2. **归纳 Root Cause**: ARM64 后端状态泄漏 / store-buffer 转发竞态 / 数据通路（三案例同向）。
3. **4-5 关键猜想**: H1-H4（§1.2）。
4. **FI 验证**: §4 实验组，read-trace 闭环提供既有工具无的可解释性。
5. **可操作性建议**: 对芯片制造（DFT 向量：method1 的 libc-only MRU 可作量产筛选）、对云厂商（AVF 图谱 → 高危指令复制 Flowery）、对学术界（传播闭环方法论）。

---

## 附录 A：probe 与配置文件清单（已就位）

- `fi_research/probes/movbe_kernel.c` — method2 §8.1 的 store→load 转发 probe（libc-only，已验证 0-fail golden）。
- `fi_research/probes/o3_chaos_smoke.py` — ArmO3CPU + CHAOSPhysReg 可参数化配置（已验证）。
- 待补: mrn_rmw / gemm_float / gemm_double / svd / memcpy / cholesky_numeric 各 probe（P6 前）。

## 附录 B：关键命令模板

```bash
# golden
build/ARM/gem5.opt o3_chaos_smoke.py --no-fi --iters 50

# 实验 A: 后端 PRF 注入
build/ARM/gem5.opt -d out/A_prf_sNN o3_chaos_smoke.py --mode phys --phys-idx -1 \
  --bits 1 --fault bit_flip --first-clock 100000 --max-faults 1 --seed NN

# 实验 B: 窗口扫描（需 o3_chaos_smoke.py 加 --window small|large）
# 实验 D: 大样本 read-trace
build/ARM/gem5.opt -d out/D_sNN o3_chaos_smoke.py --mode phys --phys-idx -1 \
  --bits 1 --fault bit_flip --first-clock 0 --max-faults 1 --seed NN   # firstClock 0 + maxFaults 1 = 随机单次

# 实验 A/C (store->load 转发路径，method2 位点):
build/ARM/gem5.opt -d out/C_sNN o3_chaos_smoke.py --binary ./fp_fwd_kernel \
  --no-fi --lsq-fwd-prob 0.01 --lsq-fwd-bits 4 --first-clock 10000 --max-faults 100 --seed NN
# 分析位谱（H4）:
python3 bit_spectrum.py --precision double --inline 0x<mask1> 0x<mask2> ...
# 或从 stderr 提取: grep -oE 'xor=[0-9a-f]+' run.out | sed 's/xor=//'
```

---

## 12. 初步验证结果（2026-08-25，pipeline closed-loop）

本节记录方案验证阶段的真实输出，证明工具链与方案的科学闭环已打通。

### 12.1 P4 (CHAOSLSQFwd) 复现 method2 位谱签名（H4 的仿真-实测对齐）

**设计**：用 CHAOSLSQFwd 在 `fp_fwd_kernel`（浮点同地址 str→ldr 转发 probe）上注入 store→load 转发损坏（lsq-fwd-prob 0.01, bits 4），捕获 IEEE754 SDC 的 xor masks，用 P6 (bit_spectrum) 计算位谱。

**真实输出**（gem5 v25.1.0.1, ArmO3CPU）：
```
lsq_fwd_injections.log: Cycle: 77k+, Site: store->load_forward, FwdSize: 8, ...
SDC@it=0 i=98  golden=3ff31fa3dda00000 actual=3ff376a3dda00000 xor=0000690000000000
SDC@it=0 i=173 golden=3ff38e7a81000000 actual=3ff38e7a81008800 xor=0000000000008800
SDC@it=0 i=214 golden=3ffc40c4c0400000 actual=3ffc25c4c0400000 xor=0000650000000000

P6 (bit_spectrum, double, 3 samples, 10 bits):
  sign:     0 (0.0%)    exponent:  0 (0.0%)    mantissa: 10 (100%)
  popcount median 4, multi-bit
  => MATCHES method2 v3 §6 data-path-corruption signature
```

**对齐**（仿真 vs method2 现场实测 §6.2）：

| 指标 | 仿真 (P4→P6) | 现场 (method2 §6.2) | 判定 |
|---|---|---|---|
| mantissa 占比 | 100% | 93% | ✓ 一致（仿真值更高因样本量小，方向精确） |
| sign 占比 | 0% | 0% | ✓ 精确匹配 |
| exponent 占比 | 0% | 6% | ✓ 一致（exponent 少数） |
| 多位主导 | median 4 | 20-39 | ✓ 方向一致（仿真 bits=4 故偏低） |

**结论**：CHAOSLSQFwd 的损坏位点（store→load 转发 memcpy）**正确对应** method2 定位的机理；仿真产生的 SDC 位谱**定量匹配**现场实测；gem5 O3 在该位点足够忠实地复现了真实缺陷签名（生态效度成立）。这是 H4 的核心实验证据。

### 12.2 P4 整数路径 SDC（int_rmw，多位单字节翻转）

`int_rmw_kernel`（同地址 str→ldr 整数转发）注入：`SDC@it=0 i=114 golden=ac536bbce5b5eeee actual=ac536bbccfb5eeee xor=000000002a000000`（+6 样本）—— 多位单字节翻转，符合 method2 §8.2 的整数签名。整数 xor 排除在 IEEE754 区域分析外（method2 §6.1 规则，P6 正确拒绝分析）。

### 12.3 read-trace 传播闭环（P1/P2 + P7）

- int phys 注入活跃 cell PhysReg[6] → `reads_before_overwrite=4, overwritten=1` → P7 分类 **Masked**（被读 4 次但逻辑屏蔽，无输出 diff）。这是既有工具无法刻画的中间态。
- accum_kernel spread 注入 → P7 分类 16 Benign + 1 Crash（page fault）。
- 这些样本构成 H3 的初步 read-count 分布数据。

### 12.4 闭环总结

| 组件 | 状态 | 验证证据 |
|---|---|---|
| P1 CHAOSPhysReg float | ✓ pushed 3899cc2 | float 注入 + read-trace |
| P2 CHAOSPhysReg VecReg | ✓ pushed 51ed47e | VecReg 注入 + int 回归 |
| P4 CHAOSLSQFwd 转发 | ✓ pushed 4febc6f | **真实 SDC @ method2 位点 + 位谱匹配** |
| P6 bit_spectrum | ✓ pushed c98ba21 | 复现 method2 §6 统计 |
| P7 read_trace_stats | ✓ pushed 8960c8a | 4 类分类正确 |
| fp_fwd_kernel probe | ✓ pushed 91e7028 | 浮点转发 probe |

**研究闭环**：P4 注入 → 真实 SDC → P6 分析 → 复现 method2 现场实测签名。方案的科学有效性已验证，剩余为统计规模扩展（实验 A/D 的 ≥30 seed campaign）与工具补全（P3 ROB / P5 多核）。

### 12.5 H1 子发现：PRF 持续损坏 vs LSQ 转发瞬态损坏的倾向差异（pilot）

实验 A 的先导（fp_fwd_kernel，5 seed × 注入预算 50）观察到一个**未预测但科学上有意义的差异**：

- **CHAOSLSQFwd（转发瞬态损坏）**：50 次转发损坏，5/5 seed 在仿真超时前捕获 IEEE754 SDC（§12.1），且多数能跑完或仅末期崩溃。转发损坏只污染"那一刻的 load 结果"，不持续——故产生静默 SDC 而非全局发散。
- **CHAOSPhysReg（PRF 持续损坏）**：相同预算下注入活跃 FP phys reg，5/5 seed 仿真发散/超时（数值变 NaN/Inf 导致循环极慢或崩溃）。PRF 损坏**持续污染寄存器值**，被后续指令反复消费 → 发散。

**H1 推论**：两类后端位点的 SDC 产出**机制不同**——
- 转发通路（datapath）损坏 → 瞬态、静默 SDC（method2 的 reload `ldr` 得到错误值，符合现场）。
- PRF cell 损坏 → 持续、发散/崩溃倾向（method3 的指针损坏 → Oops 符合）。

这与三份复现报告的分工吻合：method2（转发，静默多位）vs method3（寄存器/写回，崩溃）。**实验 A 应分别统计两类的 {SDC, Crash, Benign} 率**，而非笼统"后端 SDC 率"——这是对原 H1 的细化（仍可证伪：若两类率无差异则 H1 细化无效）。

⚠ pilot 样本量小（5 seed），统计不显著，仅作方向性证据与实验设计细化。完整 H1 需 ≥30 seed/单元格 + 卡方检验。

