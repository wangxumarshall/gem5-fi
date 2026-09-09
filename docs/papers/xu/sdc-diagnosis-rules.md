# SDC 诊断规则 v2：基于跨层证据图与假设驱动实验的 CPU SDC 因果诊断框架

> 本文将原有的 SDC Rule Book 重构为可执行、可证伪、可校准的诊断框架。核心思想不是继续堆叠 Boolean Rule，而是把现场证据、微架构先验、差分执行、故障注入和主动实验选择统一到同一条诊断闭环中。
>
> 适用范围：ARM64 服务器 CPU，尤其是现网疑似 SDC、间歇性错误、跨核不一致、异常数据、异常崩溃和难以解释的 kernel panic。框架也可用于 x86 对照研究。

---

## 0. 核心结论

SDC 诊断应回答五个不同问题，不应混成一个 Boolean 判定：

1. **发生了什么（Manifestation）**：masked / SDC / DUE / crash / hang / performance anomaly。
2. **错误从哪里来（Source）**：software / hardware / environment / unknown。
3. **故障域在哪里（Localization）**：socket → core → cluster → microarchitecture structure。
4. **什么机制最可能（Root-cause hypothesis）**：FU / L1D / LSU datapath / TLB / timing / aging / shared interconnect 等。
5. **下一步做什么（Active diagnosis）**：选择能够最大化区分候选假设的信息增益实验。

因此本文采用：

```text
Raw Evidence
    ↓
Evidence Normalization
    ↓
Manifestation Classification
    ↓
Hardware / Software / Environment Attribution
    ↓
Failure-domain Localization
    ↓
Root-cause Hypothesis Ranking
    ↓
Disambiguation Experiment Selection
    ↓
Confidence Calibration
    ↓
Isolation / Retirement / Failure Analysis
```

### 0.1 最重要的十条诊断原则

| ID | 原则 | 含义 |
|---|---|---|
| P1 | **Symptom ≠ Cause** | 输出错误、panic、PMC 异常只是症状，不能直接等同于根因。 |
| P2 | **Source ≠ Outcome** | 同一个硬件错误可表现为 masked、SDC、DUE、crash；不能用最终 outcome 反推唯一 source。 |
| P3 | **Negative evidence is probabilistic** | 零 RAS、零 EDAC、零失败只能降低某些假设概率，不能逻辑排除它们。 |
| P4 | **Differential execution 是强证据，不是数学证明** | 跨核/跨上下文不一致可以强烈提升硬件嫌疑，但必须排除软件非确定性。 |
| P5 | **Core locality 指向故障域，不直接等于具体结构** | sibling 同败首先支持 core-local hypothesis，再定位到 L1D/LSU/FU/TLB 等。 |
| P6 | **Temporal recurrence > single-shot failure** | 跨天、跨条件复现比单次失败更有诊断价值。 |
| P7 | **Execution context 是一等公民** | 指令是否出错不仅取决于 opcode，还取决于前导指令、缓存、调度、温度、电压和资源占用。 |
| P8 | **Data-path signature > opcode label** | “FPU 负载失败”不是“FPU 坏了”；必须分析错误值形态、地址关系、lane/byte pattern 和传播路径。 |
| P9 | **Fault injection validates hypotheses** | gem5-fi 可以验证“某结构/故障模型能否产生同类症状”，不能单独证明真实硅片根因。 |
| P10 | **Every conclusion must be falsifiable** | 每个结论必须给出反例条件和下一项区分实验。 |

---

# 1. SDC taxonomy：不要把故障源和故障表现混为一谈

## 1.1 两维定义

### Dimension A：Fault source

```text
SOFTWARE
HARDWARE
ENVIRONMENT
UNKNOWN
MIXED
```

### Dimension B：Fault manifestation

```text
MASKED
SDC
DUE
CRASH
HANG
WRONG_CONTROL_FLOW
PERFORMANCE_ONLY
```

于是一个真实事件可以表示为：

```text
Hardware-originated
        ↓
microarchitectural corruption
        ↓
architectural corruption
        ↓
┌─────────────┬─────────────┬──────────────┐
│ MASKED      │ SDC         │ DUE / CRASH  │
│ no visible  │ wrong data  │ visible error│
└─────────────┴─────────────┴──────────────┘
```

### 1.2 Latent corruption 与最终症状

CPU179 类案例必须允许：

```text
latent hardware corruption
        ↓
wrong architectural value
        ↓
wrong address / wrong pointer
        ↓
page fault / kernel panic
```

此类事件最终可能是 `CRASH/DUE`，但其上游仍可能是静默加载错误。故障诊断不应因为最终出现 panic 就把“SDC-originated corruption”从研究集合中删除。

### 1.3 严格的 SDC operational definition

在本文中，**Observed SDC** 定义为：

```text
同一任务/输入的参考正确结果 R
与疑犯执行结果 O
在预先定义的业务/数值语义比较器下不等
且异常不是由显式软件路径错误、已确认 loud RAS 故障或测试框架自身预期行为解释。
```

同时保留：

```text
Latent SDC-inducing corruption
```

用于描述已发现的中间状态污染，即使最终因该污染演化为 crash/DUE。

---

# 2. 六层传播模型 + 一个知识层

```text
L0 Physical / Environment
    ↓ activation: voltage / temperature / frequency / aging / input pattern
L1 Microarchitecture
    ↓ structure: L1D/L1I/L2/RF/FU/LSU/TLB/ROB/LQ/SQ/BTB/bypass/interconnect
L2 Architectural / ISA
    ↓ state: data / instruction / operand / address / control-flow / timing effect
L3 Runtime / OS
    ↓ kernel / syscall / exception / RAS / reboot
L4 Application / Data
    ↓ output / checksum / replay / ABFT / business invariant
L5 Fleet / Temporal
    ↓ core affinity / recurrence / cohort / aging / workload distribution
L6 Diagnostic Knowledge Plane
    ↓ evidence graph / priors / hypothesis / experiment selection / confidence / action
```

**诊断原则：**

```text
自上而下：symptom → evidence collection
自下而上：mechanism → root-cause attribution
横向：cross-layer consistency
时间轴：recurrence / aging / context
```

L6 不再是“第七层故障传播”，而是覆盖 L0–L5 的**诊断推理平面**。

---

# 3. Evidence schema：把 Rule 变成机器可处理的证据

## 3.1 四类证据

### E+：正证据

直接支持某个假设的观测：

- golden diff
- cross-core disagreement
- instruction/context disagreement
- vector-vs-scalar differential failure
- store→reload corruption
- byte rotation / zero-collapse / lane-local corruption
- known gem5-fi injection producing same signature
- temperature threshold
- repeated same-core failure

### E−：负证据

仅用于降低假设概率，不可写成绝对排除：

- zero EDAC / zero SEL
- no MCE/GHES
- no failure under a particular workload
- software deterministic reproduction
- test failure across every core
- checksum passes

### ELOC：定位证据

```text
socket
NUMA node
physical core
SMT sibling
cluster
PC
instruction class
virtual/physical address
cache line
lane
byte offset
bit mask
microarchitecture structure
```

### ET：时间/环境证据

```text
timestamp
uptime
age
core temperature
voltage
frequency
power
workload phase
execution context
failure rate
inter-failure interval
recovery / self-healing episode
```

---

# 4. Evidence normalization：没有时间/空间对齐，跨层诊断容易产生假因果

所有证据进入诊断引擎前统一成：

```yaml
case_id: <unique-case>
timestamp: <monotonic + wall clock>
host_id: <host>
socket_id: <socket>
core_id: <physical-core>
smt_id: <logical-core>
workload_id: <workload>
seed: <seed>
pc: <optional-pc>
instruction: <opcode>
address: <optional-address>
temperature: <C>
voltage: <V>
frequency: <MHz>
ras_state: <structured-r as>
output_signature: <hash/digest/statistics>
error_signature: <structured-signature>
confidence: <0..1>
```

必须区分：

```text
observation timestamp
failure timestamp
first-corruption timestamp
last-known-good timestamp
```

否则很容易把“同时发生”错误解释为“因果关系”。

---

# 5. 分层 Probe 与改进后的判定规则

## 5.1 L0：Physical / Environment

### Probe L0-1：thermal / voltage / frequency

记录：

```text
temperature
voltage
frequency
power
DVFS state
cooling state
neighbor-core load
```

### Probe L0-2：input pattern

记录：

```text
bit population
constant bits
mantissa/exponent distribution
operand Hamming distance
repeated-mask pattern
```

### Probe L0-3：aging / timing

记录：

```text
slack/WNS
critical path
age / uptime
silicon revision
```

### Rule L0-1：thermal-associated evidence

```text
if failure_rate changes consistently with temperature
    → thermal-associated evidence ↑
```

**不能直接写成：**

```text
Pearson > 0.75 → aging defect
```

因为 workload、frequency throttling、execution context 和 cooling interaction 都可能造成伪相关。

只有完成 controlled sweep：

```text
fixed workload
fixed input
fixed frequency
fixed core
controlled temperature sweep
```

才能升级为：

```text
thermal causality evidence
```

### Rule L0-2：marginal timing hypothesis

支持条件：

```text
failure appears above a repeatable thermal/voltage boundary
+ threshold shifts with frequency
+ healthy-core control remains clean under same conditions
```

结论：

```text
marginal/timing hypothesis ↑↑
```

而不是“已证明 aging”。

---

## 5.2 L1：Microarchitecture

### Probe L1-1：architectural visibility

记录：

```text
PC
opcode
source registers
destination registers
architectural value
commit order
faulting address
```

### Probe L1-2：PMC / trace

可收集：

```text
instructions
cycles
cache misses
branch mispredict
TLB miss
stall
load/store activity
```

PMC 的正确语义：

```text
high PMC deviation → anomaly trigger
normal PMC → cannot exclude data-value SDC
```

主存数据值型 SDC 特别容易在 PMC 上保持近似正常，因此 PMC 应作为**必要非充分的低成本触发器**，而不是终局检测器。

### Probe L1-3：ACE / lifetime

使用 AVF/ACE 先验描述：

```text
activation × exposure × architectural vulnerability
```

但不得把 ACE 直接等同于真实 SDC rate：

```text
ACE = upper/structural vulnerability estimate
Observed SDC = activation × propagation × software exposure × detection semantics
```

### Rule L1-1：masking

以下事件优先标记为 `MASKED_CANDIDATE`：

```text
invalid entry
wrong-path and flushed
overwrite-before-read
dead value
logical masking
never committed
```

注意：

```text
masked ≠ healthy hardware
```

它只表示**本次 fault activation 没有形成可观测系统错误**。

### Rule L1-2：structure-specific signatures

```text
byte rotation
zero collapse
lane-select error
store→reload mismatch
wrong address
TLB/translation signature
```

结构签名优先级高于“哪条应用看起来失败”。

---

## 5.3 L2：Architectural / ISA / Execution Context

### Probe L2-1：Context-Sensitive Differential Execution

定义：

```text
F(I, X, C1)
F(I, X, C2)
```

其中：

```text
I = instruction
X = architectural input
C = execution context
```

若：

```text
F(I,X,C1) != F(I,X,C2)
```

产生：

```text
CDI = Context-Dependent Inconsistency
```

CDI 是强硬件嫌疑信号，但必须继续排除软件非确定性。

### Rule L2-1：opcode ≠ cause

```text
vector workload fails
```

不得直接推导：

```text
vector unit defective
```

必须运行结构对照集：

```text
pure FMA
scalar arithmetic
vector arithmetic
load/store
integer load
store→reload
```

### Rule L2-2：execution context is first-class

若失败只在特定前导指令、缓存状态或 resource pressure 出现：

```text
context-sensitive hardware hypothesis ↑
```

而不是简单提升某个 opcode 的故障概率。

### Rule L2-3：consistent error

```text
two executions produce identical wrong output
```

属于：

```text
DIFFERENTIAL-DETECTION BLIND SPOT
```

因此必须引入第三个独立 execution context / independent reference，或者使用物理隔离参考单元。

---

# 6. L3 Runtime / OS：RAS 是证据，不是上帝视角

## 6.1 Probe

```text
GHES
MCE
EDAC CE/UCE
BERT
SEL/BMC
kernel panic
page fault
watchdog
reboot
vmcore
```

### Rule L3-1：RAS silence

正确语义：

```text
if symptom && observed_RAS == 0
    → silent-hardware hypothesis ↑
```

不允许：

```text
RAS == 0 → hardware proven
```

### Rule L3-2：RAS presence

```text
hardware RAS event exists
```

应转化为：

```text
reported-hardware-fault hypothesis ↑
```

但仍保留：

```text
SDC hypothesis > 0
```

因为两个事件可能在同一时间窗口发生，RAS 事件也可能与目标症状无因果关系。

### Rule L3-3：异常类型聚合

rare exception / panic patterns 可以作为 fleet prior：

```text
single-core clustering
+ repeated exception family
+ cross-workload recurrence
```

→ 提升 hardware suspicion。

不能把某一种 panic 类型写死为“SDC CPU 强指标”，除非完成 workload-normalized control comparison。

### Rule L3-4：校验器污染

若 checker 与被检计算共享：

```text
same SIMD/FPU
same execution core
same suspect structure
```

则：

```text
checker-pass is weak evidence
```

应优先采用：

```text
cross-core reference
scalar reference
physically isolated checker
```

---

# 7. L4 Application / Data

## Probe L4-1：golden output

```text
golden digest
golden byte diff
semantic comparator
numeric tolerance
business invariant
```

### Rule L4-1：semantic threshold first

```text
output difference > predefined semantic threshold
```

才进入 corruption diagnosis。

避免把合法浮点 nondeterminism 当作 SDC。

### Probe L4-2：cross-core replay

推荐顺序：

```text
same input
same software image
same initial state
same external side effects
cross-core execution
```

### Rule L4-2：cross-core disagreement

结果不一致：

```text
hardware suspicion ↑↑
```

但不是直接“hardware proof”。必须进一步检查：

```text
software nondeterminism
race
uninitialized state
NUMA / I/O variability
OS scheduler effects
```

### Probe L4-3：checksum / CRC / ABFT

三类检查器应区分：

```text
data-integrity checker
computation-integrity checker
control-flow checker
```

单纯 checksum 能证明“数据变了”，不能证明“计算过程没有算错”。

### Rule L4-3：independent checker

检验器与被检计算必须尽可能做到：

```text
physical isolation
execution-unit diversity
core diversity
software-path diversity
```

---

# 8. L5 Fleet / Temporal

## Probe L5-1：core affinity

记录：

```text
physical core
SMT sibling
socket
NUMA
cluster
```

### Rule L5-1：core-locality hypothesis

```text
same physical core
+ sibling/related logical contexts affected
+ alternate physical cores clean
```

→ `core-local fault-domain hypothesis ↑↑`

但不要直接写成：

```text
single physical core single structure proven
```

因为 core-local domain 仍可能包含：

```text
L1
LSU
scheduler
clock
power
local interconnect
execution resources
```

### Probe L5-2：temporal recurrence

区分：

```text
single-shot failure
repeatable failure
intermittent failure
late-onset failure
self-healing episode
```

### Rule L5-2：recurrence

```text
same seed
same core
same signature
across independent days/windows
```

→ hardware hypothesis 显著增强。

### Rule L5-3：absence of failure

```text
one clean test window
```

不得写成：

```text
machine healthy
```

只能：

```text
no failure observed under tested exposure
```

---

# 9. Structure → Signature Diagnostic Matrix

| Candidate structure | Typical fault signature | High-value discriminating experiment | Negative evidence | Diagnostic confidence |
|---|---|---|---|---|
| L1D data | wrong load value, silent corruption | integer load + store/reload + cache-state variation | clean uncached path | medium/high |
| L1D tag | wrong line selected, false-hit style corruption | same data with controlled tag/cache residency | miss/refetch restores value | medium/high |
| LSU / fill-buffer / datapath | zero-collapse, byte rotation, stale/shifted value | store→load, alignment sweep, NOP/context perturbation | pure-FMA clean | high when signature matches |
| Vector FPU | FMA/vector numerical mismatch | pure FMA + vector-vs-scalar reference | integer/load-store clean | medium/high |
| Scalar ALU | integer result corruption | isolated ALU operands and repetitions | load/store reproducer | medium |
| TLB / page-walk | translation fault, bad descriptor-derived address | page-table walk stress + controlled VA/PA mapping | no translation involvement | medium |
| ROB/LQ/SQ/control metadata | DUE, control-flow anomaly, broad instability | OoO pressure + replay/flush stress | deterministic data-only corruption | low/medium |
| DRAM / memory subsystem | address/data corruption depending on path | DIMM/channel swap + ECC syndrome correlation | cross-DIMM clean | medium |
| Shared interconnect / routing | same-value displacement, byte/lane routing errors | different producers/consumers sharing datapath | private execution-unit test clean | high when signature consistent |
| Timing / marginal path | strong V/F/T threshold, context-sensitive failure | controlled T/V/F sweep with healthy-core control | fixed-condition failure | medium/high |

**重要：** 表中的“Diagnostic confidence”是先验模板，不是固定概率。真实系统必须用现场数据校准。

---

# 10. CPU179：为什么“浮点故障”只是伪标签

CPU179 案例是本框架的标准 end-to-end case study。

已有取证显示：

```text
22 days
147 reproductions
12 kernel panics
4 independent trigger methods
all converge to CORE179
RAS chain silent
```

初期症状来自 Eigen sparse Cholesky / GEMM，因此“FPU defect”是自然假设；但后续差分证据不断削弱该假设：

```text
pure FMA          → clean
SVD               → clean
dense GEMM        → clean
integer / CRC     → clean
memcpy            → fails
integer loads     → fails
store→reload      → fails
```

进一步观察：

```text
zero-collapse
byte/phase rotation
bit-field corruption
NOP changes failure probability
same core across independent workloads
```

因此正确的诊断过程是：

```text
H1: FPU
 ↓ counterexamples
H2: vector datapath
 ↓ memcpy / integer-load evidence
H3: common data movement path
 ↓ byte routing + timing phase evidence
H4: LSU / fill-buffer / routing-local datapath
```

CPU179 说明一个重要方法论原则：

> **“哪个 workload 最先暴露错误”不等于“哪个硬件单元损坏”。真正高价值的是寻找多个 workload 共享而单一功能单元不共享的中间结构。**

---

# 11. Hypothesis Engine：从规则匹配升级到因果诊断

定义候选根因集合：

```text
H1 software bug
H2 data/input corruption
H3 L1D
H4 LSU/fill-buffer/datapath
H5 vector FPU
H6 TLB/page-walk
H7 shared interconnect
H8 memory subsystem
H9 thermal/timing marginality
H10 mixed/unknown
```

## 11.1 证据评分

第一版可以使用可解释线性评分：

```text
Score(Hk | E)
    = Prior(Hk)
    + Σ wi × ei
```

其中：

```text
ei ∈ [-1, +1]
wi = evidence reliability
```

成熟版本可使用 likelihood ratio / Bayesian update：

```text
Posterior(Hk | E)
    ∝ Prior(Hk) × Π LR(Ei | Hk)
```

但必须注意证据之间可能相关，不能机械相乘。例如：

```text
same-core failure
same-core sibling failure
core affinity
```

很可能是同一底层证据族，不能当作三个完全独立样本。

---

# 12. Counterexample-first diagnosis

每个诊断结论必须绑定一个“最强反例”。

| 当前假设 | 强支持证据 | 最危险反例 | 区分实验 |
|---|---|---|---|
| FPU defect | vector numerical error | same-core memcpy failure | pure FMA + integer load |
| L1D defect | load value corruption | byte rotation across structures | cache-disabled / uncached control |
| software bug | deterministic reproduction | cross-core disagreement | alternate-core replay |
| thermal aging | temperature correlation | DVFS/workload confounder | fixed-frequency T sweep |
| core-local defect | same-core recurrence | shared power/clock domain | neighboring-core controlled comparison |
| DRAM | memory-value corruption | CPU datapath corruption | DIMM/channel swap/control pattern |
| TLB | translation fault | bad pointer created by LSU | known-good page tables + direct physical access |

**原则：**

```text
No hypothesis is “confirmed” until its strongest plausible counterexample has been tested.
```

---

# 13. Active Diagnosis：下一轮应该跑什么？

当多个假设都仍然成立时，不再人工凭经验挑测试，而是选择**信息增益最大**的实验。

## 13.1 实验选择

```text
InformationGain(Test)
  = expected uncertainty before test
    - expected uncertainty after test
```

例如 CPU179：

| Test | FPU hypothesis | LSU hypothesis | L1D hypothesis | 预期价值 |
|---|---:|---:|---:|---:|
| pure FMA | 高 | 低 | 低 | 中 |
| integer load | 低 | 高 | 中 | 高 |
| store→reload | 低 | 高 | 高 | 高 |
| vector load | 中 | 高 | 中 | 高 |
| NOP perturbation | 低 | 高 | 中 | 高 |
| temperature sweep | 中 | 中 | 中 | 中 |
| scalar reference | 高 | 中 | 低 | 中 |

因此在已有 pure-FMA clean 之后，再继续堆叠 FMA 测试的信息价值迅速下降；此时应优先转向 integer load / store→reload / NOP-context experiment。

---

# 14. Cross-layer causal evidence graph

建议把一次故障表示成图，而不是一条 Rule：

```text
                    [Temperature ↑]
                           │
                           ↓
                  [Timing margin ↓]
                           │
                           ↓
[CORE179] ───────→ [LSU datapath]
    │                    │
    │                    ↓
    │              [byte rotation]
    │                    │
    │                    ↓
    ├──────→ [bad architectural value]
    │                    │
    │                    ↓
    └──────→ [bad pointer/address]
                         │
                         ↓
                    [kernel panic]
```

旁边附加独立观察：

```text
memcpy failure ──────┐
integer-load failure ┤
GEMM reload failure ──┤ → shared datapath hypothesis
no-op sensitivity ───┘
```

这比“Rule5-2 命中，所以坏核”更适合解释复杂现场。

---

# 15. Confidence model：允许“不知道”

建议采用五级状态：

| State | 含义 | 典型条件 |
|---|---|---|
| UNKNOWN | 信息不足 | 单次异常 / 无可靠 reference |
| CANDIDATE | 有初步异常 | 单层输出异常、PMC 偏移 |
| SUSPECT | 硬件/软件某一方明显领先 | 多证据一致但未完成反例实验 |
| HIGH-CONFIDENCE | 跨层证据高度一致 | cross-core + recurrence + localization + controlled experiment |
| CONFIRMED | 独立 failure analysis / 硅级证据支持 | 厂商 FA、ATE/shmoo 或独立硬件复现 |

必须保留：

```text
ABSTAIN / INSUFFICIENT_EVIDENCE
```

“诊断系统不知道”比错误地给出一个精确根因更有工程价值。

---

# 16. Negative evidence 的正确语义

## 16.1 不能这样写

```text
zero EDAC → ECC-protected array excluded
RAS present → not SDC
one clean window → machine healthy
core-local → exact structure identified
temperature correlation → aging proven
```

## 16.2 应写成

```text
zero EDAC
→ reported-ECC-fault hypothesis decreases

RAS present
→ reported-hardware-fault hypothesis increases

one clean window
→ failure not observed under tested exposure

core-local recurrence
→ core-local fault-domain probability increases

temperature association
→ thermal/timing hypothesis increases
```

这是本文件从 Rule Book 升级为诊断系统最重要的语言规范之一。

---

# 17. gem5-fi 的正确角色：Hypothesis Validator

`gem5-fi` 不应该被描述为“真实硅片根因证明器”，而应该提供：

```text
Fault model
    ↓
structure
    ↓
activation
    ↓
propagation
    ↓
observable signature
```

例如：

```text
inject L1D bit corruption
→ observe wrong-load signature

inject fill-buffer byte shift
→ observe byte-rotation signature

inject TLB/page-walk corruption
→ observe ESR / translation signature
```

然后把真实现场映射到 injection signature：

```text
Real signature
       ↕
Gem5 signature
```

得到：

```text
mechanistic consistency evidence
```

而不是：

```text
proof of physical root cause
```

## 17.1 推荐接口

```yaml
case_signature:
  manifestation: SDC|DUE|CRASH|MASKED
  locality: core/socket/shared
  opcode_family: load/store/vector/integer
  error_shape: zero-collapse|rotation|lane|bitmask|address
  context_sensitivity: low|medium|high
  thermal_sensitivity: low|medium|high

injection_signature:
  structure: LSU/L1D/TLB/FPU/...
  fault_model: bitflip/stuck-at/phase-shift/metadata
  output_signature: ...

match:
  structural_similarity: 0..1
  signature_similarity: 0..1
  context_similarity: 0..1
  confidence: 0..1
```

---

# 18. ARM64-specific diagnostic prior

ARM64 不应被简单描述成：

```text
31 GPR → bigger crossbar → more SDC
```

更严谨的因果链应为：

```text
ISA semantics
      ↓
instruction decomposition
      ↓
µArch resource usage
      ↓
renaming / scheduling / bypass / LSU pressure
      ↓
activation density of shared structures
      ↓
fault exposure
      ↓
observed SDC probability
```

ARM64 研究真正有价值的假设是：

> **特定 ARM64 微架构可能由于 Load-Store 语义、寄存器使用方式、乱序窗口和共享数据通路组织方式，使某些中枢结构获得更高的激活/暴露密度。**

这应作为可验证 hypothesis，而不是已证实的 ISA 定律。

验证至少需要：

```text
ARM64 implementation A
ARM64 implementation B
x86 control
same workload family
same fault model
same exposure metric
```

并区分：

```text
ISA effect
vs
microarchitecture implementation effect
```

---

# 19. Fleet / Temporal model

不要只记录“失败过几次”，建议记录：

```text
machine prevalence
per-test failure probability
new-failure incidence
lifetime failure probability
inter-failure interval
hazard rate
```

可以进一步建模：

```text
λ(t | age, temperature, voltage, workload, prior failures)
```

可采用：

```text
survival analysis
Weibull model
Cox model
hazard regression
```

这样 PinDrop / Ripple 类研究不再只是 ACT 规则，而成为**时间维度上的可靠性先验**。

---

# 20. Operational actions：从固定阈值改成风险决策

不建议写死：

```text
≤2 bad cores → mask
>2 → retire chip
```

改为：

```text
Action = f(
  confidence,
  bad-core count,
  locality,
  failure frequency,
  workload criticality,
  redundancy,
  SLA impact,
  replacement cost,
  repairability
)
```

### Action state

```text
OBSERVE
↑ cadence
TARGETED_RETEST
CORE_ISOLATION
NODE_ISOLATION
SOCKET_RETIREMENT
CHIP_RETIREMENT
VENDOR_FA
```

### 推荐决策

```text
HIGH-CONFIDENCE + core-local
    → core isolation first

HIGH-CONFIDENCE + shared structure suspicion
    → socket/node isolation

MULTIPLE core / temporal worsening
    → chip retirement candidate

UNRESOLVED but high business impact
    → isolate while continuing diagnosis
```

---

# 21. Continuous corpus / knowledge evolution

每次确认案例都必须反哺：

```text
failure seed
core ID
socket/NUMA
PC
instruction sequence
input pattern
temperature
voltage
frequency
load fingerprint
error signature
vmcore
trace
PMU
successful reproducer
failed reproducer
root-cause label
counterexample
```

最终形成：

```text
SDC Case
   ↓
Canonical Signature
   ↓
Hypothesis Prior
   ↓
Best Disambiguation Test
   ↓
Confirmed Mechanism
```

这会让 `gem5-fi` 从“故障注入平台”逐渐形成：

```text
SDC Diagnosis Knowledge Base
```

---

# 22. Machine-readable Rule Schema

后续实现不建议继续维护纯 Markdown Boolean rules，而应同时生成 YAML/JSON：

```yaml
rule_id: DIAG-CORE-LOCAL-001
name: core-locality-hypothesis
layer: L5
inputs:
  - physical_core
  - smt_sibling
  - alternate_core_replay
positive_evidence:
  - same_core_recurrence
  - sibling_agreement
negative_evidence:
  - all_core_failure
conclusion:
  hypothesis: core_local_fault_domain
  confidence_delta: +0.35
counterexamples:
  - shared_clock_domain
  - shared_power_domain
  - shared_L2
next_experiments:
  - move_same_seed_to_neighbor_core
  - stress_shared_structure
```

这样以后可以直接实现：

```text
sdc-diagnose case.json
```

输出：

```text
H1 software bug          0.04
H2 L1D                   0.17
H3 LSU datapath          0.61
H4 vector FPU            0.09
H5 TLB                   0.06
H6 memory subsystem      0.03

Recommended next test:
  integer-load + store-reload + NOP perturbation
Expected information gain: 0.42
```

---

# 23. 端到端诊断流程（推荐实现版本）

```text
STEP 0  Collect
  ↓
output / vmcore / RAS / PMU / core / T-V-F / seed / trace

STEP 1  Normalize
  ↓
time alignment + core topology + workload normalization

STEP 2  Classify manifestation
  ↓
MASKED / SDC / DUE / CRASH / HANG

STEP 3  Reject obvious software explanations
  ↓
deterministic software repro / race / input corruption / intentional crash

STEP 4  Differential execution
  ↓
cross-core / cross-context / scalar-vs-vector / independent checker

STEP 5  Localize fault domain
  ↓
core-local / socket-shared / memory / interconnect / unknown

STEP 6  Extract signatures
  ↓
address / byte / lane / bit / instruction / context / timing

STEP 7  Rank hypotheses
  ↓
Bayesian or explainable weighted evidence model

STEP 8  Choose next experiment
  ↓
maximum information gain

STEP 9  Validate mechanism
  ↓
gem5-fi / fault injection / controlled T-V-F / microbenchmark

STEP 10  Temporal confirmation
  ↓
repeated seed / multiple days / changing environment

STEP 11  Confidence
  ↓
Candidate / Suspect / High-Confidence / Confirmed

STEP 12  Action
  ↓
isolate / retire / FA / corpus feedback
```

---

# 24. 能力边界与已知盲区

1. **Consistent error**：两份冗余执行同步产生同样错误，双执行机制可能漏检。
2. **Output-resident corruption / ESC**：错误可在正常程序流之外写回输出，必须把输出边界本身作为独立观测点。
3. **Masked error**：本次运行未改变结果，不等于硬件无故障。
4. **Main-memory data corruption**：可能几乎没有 PMC/控制流痕迹，应依赖数据完整性检查。
5. **Checker co-corruption**：checker 若共享可疑硬件，pass 只是弱证据。
6. **RAS incompleteness**：零 RAS 不证明“没有硬件错误”，有 RAS 也不证明“不是 SDC”。
7. **Software nondeterminism**：跨核不一致必须排除 race、I/O、NUMA、uninitialized state 等因素。
8. **Microarchitecture injection coverage**：gem5-fi 只能覆盖被建模的结构和 fault model。
9. **ISA generalization**：单个平台结果不能直接上升为“ARM ISA 普遍定律”。
10. **Late-onset / self-healing**：单窗口 clean 不能证明长期健康。
11. **Correlation ≠ causation**：温度、电压、PMC 等相关性必须配合 controlled experiment。
12. **Multiple concurrent faults**：单一根因模型可能失效，必须保留 `MIXED` 假设。

---

# 25. 论文/工业实现的最终创新点

本框架建议最终不以“SDC 规则数量”作为贡献，而以以下五点作为核心：

### C1. Source–Manifestation 二维 SDC taxonomy

解决“SDC、DUE、crash、hardware fault source”互相混淆的问题。

### C2. Cross-layer Evidence Graph

统一：

```text
RAS
vmcore
PMU
execution trace
core affinity
output diff
temperature/voltage
```

并明确区分正证据、负证据、定位证据和时间证据。

### C3. Hypothesis-driven RCA

从：

```text
rule matching
```

升级到：

```text
hypothesis ranking + counterexample testing
```

### C4. Active Diagnosis

自动选择下一项信息增益最大的实验，而不是无限增加测试数量。

### C5. Real-silicon ↔ gem5-fi causal validation

把真实 ARM64 故障签名与模拟故障传播签名对齐，形成：

```text
field evidence
    ↕
gem5 mechanistic evidence
    ↕
microarchitecture hypothesis
```

---

# 26. 推荐的最终研究定位

本文不应再定位成：

> “SDC diagnosis rules collection”

而建议定位为：

> **A Cross-Layer Evidence-Driven and Hypothesis-Guided Framework for CPU Silent Data Corruption Diagnosis**

中文：

> **基于跨层证据图与假设驱动实验的 CPU 静默数据损坏因果诊断框架**

最终目标不是回答：

```text
“这台机器是不是 SDC？”
```

而是回答：

```text
发生了什么？
        ↓
为什么发生？
        ↓
故障域在哪里？
        ↓
最可能是哪一个微架构结构？
        ↓
什么实验能最快证伪当前假设？
        ↓
应该隔离什么？
```

这也是 `gem5-fi` 从 **Fault Injection** 向 **SDC Diagnosis / RCA Engine** 演进的核心方向。

---

# Appendix A. Legacy evidence catalogue

下列知识继续保留为证据/先验库，使用时必须注明适用平台、实验语义和统计 denominator，不得直接写成跨平台定律：

| Knowledge family | 典型用途 |
|---|---|
| AVF / ACE | 结构脆弱性、masking、lifetime |
| gem5-MARVEL | 微架构传播与结构定位 |
| MaFIN / GeFIN | 注入停止条件与差分故障注入 |
| GemFI | ISA/指令级 fault propagation |
| SDC-μArch | 结构→症状先验 |
| ITC / Veritas / Gates-to-SDCs | functional-unit / instruction family 统计先验 |
| SOSP'23 production CPU study | large-fleet SDC characteristics |
| SiliFuzz / Fleetscanner | continuous hardware testing / fingerprint |
| Harpocrates | hardware-in-the-loop program generation |
| Orthrus | cross-core redundant validation |
| ITHICA | context-sensitive instruction-level checking |
| Vega | aging/timing-aware runtime evidence |
| SEVI | vector/FMA characterization与fleet evidence |
| PinDrop | long-horizon recurring and late-onset failures |
| CHAOS | gem5 controlled fault injection + PMC analysis |
| Hardware Sentinel | fleet hardware-error diagnosis |
| ETS2024 | large-scale SDC prediction / measurement |

---

# Appendix B. References

完整参考文献建议在论文版本中使用标准 BibTeX/DOI 条目，并为每个关键 claim 增加 `paper + page/figure/table` 定位。当前仓库中的简称仅作为工程文档索引，不视为完整 bibliography。

---

# Appendix C. Implementation TODO

```text
[ ] docs/schema/sdc-evidence.schema.yaml
[ ] docs/schema/sdc-hypothesis.schema.yaml
[ ] tools/sdc-diagnose/evidence_normalizer.py
[ ] tools/sdc-diagnose/hypothesis_engine.py
[ ] tools/sdc-diagnose/experiment_selector.py
[ ] tools/sdc-diagnose/signature_matcher.py
[ ] gem5-fi integration: injection-signature export
[ ] vmcore integration: register/address/error extraction
[ ] PMU integration: normalized counter features
[ ] ARM64 core-topology integration
[ ] CPU179 regression corpus
[ ] controlled counterexample test suite
[ ] confidence calibration dataset
```
