# 基于 CHAOS/gem5 的 ARM64（鲲鹏 920 导向）SDC 故障注入实验方案

> 版本：源码审计版 v1.0（2026-08-25）  
> 研究对象：ARM64/AArch64，重点为鲲鹏 920/TaiShan v110 的公开特征与可校准代理模型  
> CHAOS 本地源码：`third_party/CHAOS`  
> CHAOS 固定提交：`72cd7e5cbafd494386c20c933f38e7b655e9201b`  
> 本文性质：实验设计与后续实施规范；本轮未编译、未运行 benchmark、未修改 CHAOS 源码

## 0. 一页执行结论

本课题不预设“ARM64 比 x86 更脆弱”。研究假设应写成：**ARM64/鲲鹏特有的状态、弱内存序路径、128B L3 故障域及实现定义的保护边界，是否改变特定结构的条件 SDC 概率与传播路径**。

当前下载的 CHAOS 只能作为起点，不能原样用于正式 ARM64 论文实验：

- `CHAOSReg` 实际注入的是 `ThreadContext` 可见的**架构寄存器态**，不是 O3 物理寄存器堆（PRF）、RAT 或 ROB；其 mask/bitset 仅 32 位，不能可信覆盖 AArch64 X 寄存器高 32 位和 128 位 NEON。
- `CHAOSCache` 只改 classic cache 的数据字节，不覆盖 tag、valid/dirty、替换、一致性或 ECC 元数据；对 `Cache` 的内部访问方式存在不安全下转型，不能直接作为正式结果来源。
- `CHAOSMem` 改的是 `AbstractMemory` 后备存储，不是 DRAM timing/controller/ECC 通路；其故障类型权重和地址边界存在实现问题。
- 三个模块都缺少可控、可记录的随机种子与完整 old/new 日志；“永久故障”语义并不真正永久；概率为 1 时还可能产生零周期重调度。

因此，推荐路线是：

1. 冻结版本并完成七个正确性闸门；以单故障、确定性触发建立 ARM64 GPR/L1I/L1D/内存基线。
2. 先做最小可发表核心：**GPR + L1I/L1D + NEON lane + TLB/系统寄存器 + LSQ 转发**。
3. 再做鲲鹏导向扩展：64B sector 配对的 128B L3 故障域代理、coherence/NUMA；明确它不是鲲鹏内部微架构复现。
4. 最后做同语义、同保护假设的 x86-64 配对对照，并用鲲鹏实机 RAS 能力与日志链路校准。

正式 campaign 默认使用**每次运行恰好一个确定性故障**；概率模式只用于压力筛查，不进入主统计。

---

## 1. 研究问题、范围与声明边界

### 1.1 研究问题

RQ1：AArch64 架构态、NEON lane、地址翻译与弱内存序相关状态的 SDC 敏感性如何随工作负载和故障模型变化？

RQ2：在相同语义靶点、相同 workload intent、相同保护假设下，ARM64 与 x86-64 的条件 SDC 概率和传播时延有哪些稳定差异？

RQ3：鲲鹏 920 的公开特征——64B L1/L2、128B L3、服务器级多核/NUMA/RAS——会产生哪些新的故障域与保护边界？

RQ4：CHAOS 原始抽象、ARM64 扩展和鲲鹏代理模型分别能支持多强的结论？

### 1.2 不做的错误推断

- 不把 gem5 条件传播概率换算成鲲鹏或 x86 产品现场 FIT，除非另有 raw FIT、截面、保护覆盖和部署暴露量。
- 不把 ARM ISA 标签当成微架构、工艺或 ECC/RAS 的替代变量。
- 不把 `ThreadContext::setReg()` 称为 PRF/RAT/ROB 注入。
- 不把无 ECC 的 cache 数据翻转称为“真实鲲鹏残余 SDC”。
- 不把相邻两个 64B block 的联合注入称为精确 128B L3 模型。
- 不把 SVE 作为鲲鹏 920 基线；基线是 128-bit ASIMD/NEON。
- 不通过破坏 C++ 指针、容器长度或非法枚举来模拟硬件故障。

### 1.3 证据等级

| 等级 | 含义 | 可支持结论 |
|---|---|---|
| E1 | ISA、gem5/CHAOS 源码、公开产品规格直接支持 | 机制/参数事实 |
| E2 | 同平台受控实验直接观测 | 条件 SDC/Crash/Masked 概率 |
| E3 | 鲲鹏导向代理模型 | 机制趋势与敏感性分析 |
| E4 | 依赖未公开实现细节 | 仅作为待实机/RTL/厂商资料校准的假设 |

---

## 2. 本地源码基线与只读审计结论

### 2.1 版本底账

| 项目 | 固定值 |
|---|---|
| CHAOS 仓库 | <https://github.com/eliovinciguerra/CHAOS> |
| 本地路径 | `E:/硕博连读/科研/静默故障/故障注入/third_party/CHAOS` |
| CHAOS commit | `72cd7e5cbafd494386c20c933f38e7b655e9201b` |
| 原始示例 ISA | RISC-V |
| 原始示例模式 | SE、`RiscvO3CPU`、classic L1/L2 |
| 后续 gem5 候选基线 | 官方 tag `v25.1.0.1`；实施时记录完整 commit，而非只记 tag |
| 本轮动作 | 只下载、只读审计和撰写方案；未构建、未执行、未改源码 |

不要执行 CHAOS 的 `make all`：该 Makefile 会克隆浮动的 gem5 HEAD、默认构建 RISC-V，并安装/复制系统依赖，既不可复现，也超出本方案的 ARM64 设计范围。

### 2.2 源码证据账本

以下行号对应上述固定提交。

| 模块 | 源码位置 | 实际行为/问题 | 对实验的约束 |
|---|---|---|---|
| CHAOSReg | `CHAOSReg/CHAOSReg.py:15`、`.hh:48`、`.cc:24` | `faultMask`、mask/bitset 为 32 位 | X0-X30 高 32 位与 128 位向量不可信，正式实验前必须宽度感知 |
| CHAOSReg | `CHAOSReg/CHAOSReg.cc:167-190` | 仅枚举 `IntRegClass`、`FloatRegClass` | 未覆盖 Vec/Misc/系统寄存器 |
| CHAOSReg | `CHAOSReg/CHAOSReg.cc:200-231` | 读写 `ThreadContext` 架构态 | 只能称 architectural-state injection |
| CHAOSReg | `CHAOSReg/CHAOSReg.cc:145-153,200-203` | `int mask` 配合潜在 64-bit 长度和 `1 << bit` | 高位可能发生未定义行为，必须以单元测试阻断 |
| CHAOSReg | `CHAOSReg/CHAOSReg.cc:49-51,280-282` | PC target 将概率设为 1；几何分布可给零间隔 | 需要明确的确定性 trigger 与最小 1-cycle 约束 |
| CHAOSReg | `CHAOSReg/CHAOSReg.cc:292-319` | permanent 路径注入一次后关闭 update | 不是持久 stuck-at；不能用原实现报告永久故障 |
| CHAOSCache | `CHAOSCache/CHAOSCache.cc:116-124` | 用派生类指针下转型访问 `Cache::tags` | 不安全内部访问；正式 campaign 前改为受支持窄接口 |
| CHAOSCache | `CHAOSCache/CHAOSCache.cc:139-203` | 从有效块中抽样并改 data byte | 不包含 tag/metadata/ECC；仅是 classic data-array raw fault |
| CHAOSCache | `CHAOSCache/CHAOSCache.cc:224-265` | permanent 检查未形成可靠持续调度 | 持久语义不成立 |
| CHAOSCache | `CHAOSCache/CHAOSCache.py:9` | 参数类型为 classic `Cache` | Ruby/CHI 不适用，必须另建后端 |
| CHAOSMem | `CHAOSMem/CHAOSMem.cc:38-42` | `memory` 未在初始化列表保证为空 | 参数为空时存在未定义行为风险 |
| CHAOSMem | `CHAOSMem/CHAOSMem.cc:91` | 权重列表重复 bit-flip，遗漏 stuck-at-zero 参数 | 故障类型分布与配置不符 |
| CHAOSMem | `CHAOSMem/CHAOSMem.cc:65-67,168` | inclusive end 与分布上界不一致 | 末字节遗漏，一字节区间可能非法 |
| CHAOSMem | `CHAOSMem/CHAOSMem.cc:172-212` | 经 `AbstractMemory::access` 改后备存储 | 不是 timing DRAM/controller/ECC 注入 |
| 三模块 | 各模块日志/RNG/调度代码 | 无用户可控 seed、old/new、统一 target identity；固定 tick ratio | 不能做可重放正式统计，必须先过 G0/G5/G6 |
| 示例 | `examples/two_level.py:77-146` | `RiscvO3CPU`、SE、classic cache | 只能用作连接关系参考，不能作为 ARM64 验证 |

### 2.3 当前能力边界

| 能力 | 原源码状态 | 正式实验状态 |
|---|---|---|
| AArch64 架构 GPR/标量 FP | 部分可连接，但位宽/可重放性错误 | 修复后作为 Phase 1 基线 |
| NEON 128-bit 向量寄存器 | 不支持 | 新增 `VecRegClass`/lane 接口后 |
| L1I/L1D/L2 data array | classic cache 可触达 | 安全 API、确定性目标和日志完成后 |
| cache tag/valid/dirty/ECC | 不支持 | 新建字段级 cache 注入接口 |
| 后备内存 byte | 可触达但实现有缺陷 | 修正后仅称 memory-cell proxy |
| PRF/RAT/ROB/LSQ | 不支持 | O3 `FaultInjectionPort` 扩展后 |
| TLB/walker/system register | 不支持 | ARM 专用白名单接口后 |
| Ruby/CHI/coherence/NUMA | 不支持 | Ruby/CHI 专用接口后 |

---

## 3. 实验平台与配置族

### 3.1 三套配置，禁止混用结论

| 配置 | 目的 | 关键参数 | 结论标签 |
|---|---|---|---|
| C0 方法学基线 | 与 CHAOS 直接能力对齐、验证工具 | ARM O3、SE、classic、全层 64B | ARM64-gem5 baseline |
| C1 受控跨 ISA | 比较 ISA/语义机制 | ARM/x86 同核心资源意图、同 64B cache、同 workload/oracle | controlled cross-ISA |
| C2 鲲鹏导向代理 | 研究鲲鹏公开特征 | ARMv8.2-A 意图、64KB L1I/L1D、512KB 私有 L2、128B L3 fault-domain proxy、NUMA | Kunpeng-informed proxy |

C2 不是鲲鹏 920 周期精确模型。公开资料不足以确定其 ROB/RAT/LSQ、预测器和 ECC 内部实现；这些字段必须标 E3/E4。

### 3.2 SE 与 FS 的职责分工

- SE：GPR、标量 FP、NEON、L1I/L1D/L2 data、后备内存、定向 LSQ 数据转发的快速 campaign。
- FS：EL1 系统寄存器、TLB/walker、ASID、TLBI、异常/中断、Linux 日志、页迁移、多核一致性与 NUMA。
- 同一靶点若 SE/FS 都做，分别报告，不合并分母。

### 3.3 后续目录约定

```text
sdc-arm64/
  upstream/                 # 固定版本源码，不直接改
  patches/                  # 每个 gate 的独立 patch
  configs/{se,fs}/
  workloads/{directed,suites}/
  manifests/                # 每次 campaign 的不可变 YAML/JSON
  golden/                   # 无注入参考输出、hash、trace 摘要
  runs/<campaign>/<run_id>/
  schemas/
  analysis/
  artifacts/{plots,tables,logs}/
```

---

## 4. 正式实验前的七个正确性闸门

### G0：可重放随机性

新增统一 `seed`；所有模块只从记录过的 RNG 派生。相同 binary/config/checkpoint/seed/manifest 必须命中相同触发点、目标字段和 bit mask。连续 20 次重放结果应逐字段一致。

### G1：位宽与合法域

- mask 改为动态位宽或显式 64/128-bit 类型；不使用 `int` 和有符号移位。
- 覆盖 X 寄存器 bit 0、31、32、63；NEON bit 0、31、32、63、64、127。
- XZR 写入必须被识别为 architecturally discarded，而不是算作有效注入。
- SP、PC、NZCV 和系统寄存器单独建 target class；禁止混在普通 GPR 均匀抽样。

### G2：永久/间歇语义

将永久故障拆成：

- cell-stuck：存储单元每次写后强制目标位；
- read-stuck：读取值在输出处被钳位，底层存储不变；
- write-stuck：写入目标位不能改变；
- field-stuck：结构字段在每个相关状态更新后被钳位；
- intermittent：只在指定 active windows 生效。

测试至少跨过 10 次覆盖写、evict/refill 或 rename reuse；永久 fault 不得在第一次重写后消失。

### G3：cache 安全接口与后端分离

移除不安全 `static_cast<CacheAccessor*>`。由 cache/tags 类暴露最小接口，例如按 set/way/block/field 读写，classic 和 Ruby/CHI 分别实现。注入不得破坏 C++ 对象布局。

### G4：内存模块正确性

初始化并检查 `memory`；验证 `[start,end]` 边界；最后一个字节和单字节区间必须可选；故障类型权重使用三项真实参数并归一化；目标地址必须落在 memory range。

### G5：单故障与证据日志

正式运行强制 `max_faults=1`。日志必须同时包含 old/new、宽度、bit mask、target identity、触发事件、seed、当前 PC/seqNum、注入前可达性、保护阶段以及模拟器版本。

### G6：统一触发器与时钟域

支持 `tick/cycle/pc/committedInst/event`；cycle 从目标对象真实 clock domain 换算，不使用固定 `tickToClockRatio`；概率模式的下一事件间隔至少为 1 cycle。跨 ISA 主实验优先按 committed instruction 或语义 event 对齐。

### G7：无模拟器未定义行为

开启编译器警告和 sanitizer 的工具验证属于后续实现阶段；在其通过前，任何 simulator crash 归为 `SimulatorError`，不归为被测架构 Crash/DUE。字段故障只能映射到硬件可表示的合法/受约束状态。

### 闸门出口标准

| 闸门 | 最低出口标准 |
|---|---|
| G0 | 同 manifest 20/20 完全重放 |
| G1 | 64/128 位边界 bit 全覆盖；无 UB |
| G2 | 10 次状态更新后仍符合定义 |
| G3 | classic 定向 set/way 命中正确；Ruby 明确拒绝或专用实现 |
| G4 | 边界/权重 10,000 次抽样符合预期区间 |
| G5 | 1,000 次运行均恰好 0 或 1 次有效注入，无多注入 |
| G6 | 多时钟配置下触发误差为 0 个目标周期 |
| G7 | 定向测试无 sanitizer/断言异常；工具错误独立分类 |

---

## 5. 统一故障描述与调度协议

### 5.1 建议 manifest

```yaml
schema_version: arm-chaos-fi/v1
campaign_id: p1_gpr_mibench
run_id: p1-gpr-qsort-000384
source:
  chaos_commit: 72cd7e5cbafd494386c20c933f38e7b655e9201b
  gem5_commit: <full-commit>
  patchset_sha256: <sha256>
platform:
  isa: ARM64
  mode: SE
  cpu_model: ArmO3CPU
  config_family: C0
workload:
  binary_sha256: <sha256>
  input_sha256: <sha256>
  roi: {begin_symbol: roi_begin, end_symbol: roi_end}
trigger:
  mode: committedInst
  value: 1250000
target:
  layer: architectural
  component: gpr
  instance: cpu0.thread0
  index: 19
  field: value
  width_bits: 64
fault:
  model: transient_bit_flip
  bit_indices: [52]
  duration_events: 1
  stage: raw_pre_protection
rng:
  master_seed: 20260825
  selection_seed: 384
limits:
  max_faults: 1
  max_ticks: <limit>
oracle:
  kind: exact_hash
  golden_id: qsort-inputA-v1
```

当前 CHAOS 没有 `max_faults`、统一 trigger、可控 seed 和这些 target 字段；它们是进入正式 campaign 前的接口要求，不应假装原源码已经支持。

### 5.2 目标选择顺序

为了避免 occupancy bias，显式记录选择链：

```text
ROI → 动态事件/周期 → component instance → active entry → field → bit
```

“从当前有效 cache block 均匀抽样”估计的是**以 active valid block 为条件**的传播概率；如果要估计 bit-time AVF，需按 occupancy × residence time × field bits 加权。两者不可混写。

### 5.3 默认故障模型

| ID | 模型 | 参数 | 使用阶段 |
|---|---|---|---|
| F1 | single-bit transient | bit、一次读/一次事件 | 所有基线，主结果 |
| F2 | local MBU | 2/4/8 bits、相邻/同 lane/同 ECC word | cache、PRF、NEON、TLB |
| F3 | intermittent burst | start、duration、duty cycle | LSQ、interconnect、execution path |
| F4 | read/write/cell/field stuck | 0/1、持续范围 | array/control field |
| F5 | legal-domain substitution | old→另一个合法 id/value | RAT、LSQ tag、TLB PFN/ASID |
| F6 | delay/omission proxy | 延迟 N cycles、漏 wakeup/forward | pipeline/LSQ/互连；明确是代理 |

F1 是跨结构、跨 ISA 的共同主轴。F2-F6 分层报告，不能与 F1 合并成一个“SDC 率”。

### 5.4 保护阶段

每个 cache/memory fault 必须标：

- `raw_pre_protection`：保护检查之前注入，可被 ECC/parity 检出/纠正；
- `post_check_escape`：保护检查之后注入，模拟检测覆盖外逃逸；
- `metadata_or_checker`：保护元数据或 checker 自身故障；
- `no_protection_model`：模型未实现保护，仅用于 raw sensitivity。

至少同时给 raw 与 protection-aware 两组结果。

---

## 6. ARM64/鲲鹏重点靶点与实验优先级

### 6.1 优先矩阵

| 优先级 | 靶点 | 关键字段 | 研究价值 | 所需接口 |
|---|---|---|---|---|
| P0 | AArch64 GPR/标量 FP | X0-X30、SP、FP sign/exponent/mantissa | 基线和工具校准 | 宽度修复后的 CHAOSReg |
| P0 | L1I | opcode/register/immediate、data/tag | 合法错指令与控制流传播 | cache data + tag 扩展 |
| P0 | L1D | data、tag、valid/dirty、byte mask | 最可能静默到输出 | cache 字段接口 + ECC 模型 |
| P1 | LSQ/转发 | addr、size、byte enable、dependency、forward match | ARM 弱内存序与静默旧值/错值 | O3 FaultInjectionPort |
| P1 | TLB/walker | VA tag、PA、ASID/VMID、AP、XN/PXN、AttrIndx、valid | ARM64 特有字段、强 oracle | ARM MMU 专用接口 |
| P1 | 系统寄存器 | TTBR/TCR/MAIR/SCTLR/VBAR/NZCV | 地址翻译、权限、控制流 | 白名单 + 字段合法性 |
| P1 | NEON/FP | V0-V31、lane、FP fields、sat/widen/narrow | 128-bit lane 传播 | VecRegClass + execution proxy |
| P1 | L3 128B fault domain | 两个 64B sector、共同/独立元数据 | 鲲鹏最明确结构差异 | paired-sector，再做精确模型 |
| P1 | coherence/NUMA | owner/sharer/state、route、remote response | 服务器级传播 | Ruby/CHI 专用接口 |
| P2 | PRF/RAT/ROB | data/map/free/ready/dest/done/PC | 微架构状态研究 | O3 窄接口 |
| P2 | barrier/exclusive | DMB/DSB/ISB 标记、exclusive monitor | ARM 内存序语义 | LSQ/commit/memory-system 接口 |
| P3 | GIC/异常/RAS | pending/active/route/error record | FS/产业校准 | GIC/RAS 专用实验 |

### 6.2 最小可发表范围

第一篇工具与方法论文控制为：

```text
CHAOS ARM64 正确性审计
+ GPR/L1I/L1D 可重放基线
+ NEON lane
+ TLB/系统寄存器
+ LSQ forwarding
+ protection-aware 分类与统一 schema
```

L3 128B、coherence/NUMA、完整 PRF/RAT/ROB 可以作为后续论文，避免首个版本范围失控。

---

## 7. 各靶点的可执行实验定义

### 7.1 BM-GPR：AArch64 寄存器角色

构造无内联汇编/定向汇编微基准，使不同 ABI 角色在 ROI 中保持活跃：

| 组 | 寄存器 | 用法 | Oracle |
|---|---|---|---|
| G1 | X0-X7 | 参数、返回值、数据依赖链 | exact checksum |
| G2 | X9-X15 | caller-saved 临时值 | exact checksum + live-range trace |
| G3 | X19-X28 | callee-saved 跨调用值 | 调用前后不变量 |
| G4 | X29/X30 | FP/LR | 正常返回、控制流 hash |
| G5 | SP | 对齐地址/栈帧 | stack canary、异常/地址范围 |
| G6 | XZR | 写丢弃/读零 | 预期 Inactive/Masked，不进有效分母 |

每个 X 寄存器按 bit field 分层：`[0:11]`、`[12:47]`、`[48:63]`，并额外标地址、整数、指针认证不适用等语义。至少覆盖 bit 31/32 边界和高位 canonical/address 行为。

### 7.2 BM-L1I：指令编码字段

- 在固定 PC 区间循环执行已知 32-bit A64 指令序列。
- 将 bit 映射为 opcode、Rn/Rm/Rd、immediate、condition 等语义字段。
- 分 `data-array` 与 `tag/valid` 两条实验；原 CHAOS 只支持前者。
- Oracle：basic-block hash、retired-PC trace 摘要、精确输出、异常原因。
- 区分非法编码导致的 Crash/DUE 与仍合法但语义错误导致的 SDC。

### 7.3 BM-L1D/L2：数据、tag 与保护

- 数据：数组 reduction、pointer chain、结构体字段、CRC 状态。
- tag：将 tag 替换为同 set 的另一个**合法对齐 tag**，观察 false hit/miss；不破坏对象指针。
- metadata：valid/dirty/replacement/coherence 分开；一次只改一个字段。
- ECC：分别按 32/64/自定义 word 粒度注入 1-bit、2-bit、checker/meta fault；具体鲲鹏粒度若无公开证据则标 E4 并做参数扫描。
- Oracle：每行/每 sector checksum、最终 hash、写回后的内存一致性。

### 7.4 BM-NEON：128-bit lane 与 FP 位语义

- 覆盖 V0-V31，每个寄存器按 4×32-bit、2×64-bit、8×16-bit lane 分层。
- 算子：独立 lane 累加、shuffle/permute、widen/narrow、saturating、FMA、horizontal reduction。
- FP32/FP64 分 sign、exponent、mantissa；记录 NaN/Inf/subnormal/finite。
- Oracle：lane checksum + bit-exact；浮点另报 ULP、relative error、task-level threshold。
- 寄存器存储 fault 与执行单元/lane defect 分成两个 campaign，不能互代。

### 7.5 BM-LSQ：旗舰实验

定向构造：

1. 同址 store→load 必须前递；
2. 部分字节重叠、不同 size；
3. 4K alias/低位相同但物理地址不同；
4. 两个候选 store，load 应选最近同址 store；
5. store data/addr 未就绪的 replay；
6. DMB/DSB 与 acquire/release；
7. LDXR/STXR exclusive 成功/失败。

注入字段：地址比较结果、依赖 tag、forward source seqNum、byte-enable、load/store size、ready/replay 状态。所有替换必须指向当前队列中的合法 entry 或合法掩码。

Oracle：每个操作序列号、期望 source store、期望字节拼接值、最终内存不变量、litmus 禁止结果集合。重点识别：漏前递读旧值、错源前递、错误部分覆盖和次序违规。

### 7.6 BM-TLB/SYS：地址翻译与系统状态

FS 中分别注入：

- resident TLB entry：VA tag、PA/PFN、ASID/VMID、global、AP、XN/PXN、AttrIndx、valid；
- lookup-output transient：不改 entry，只改一次翻译结果；
- walker in-flight state：level、descriptor、next-table address、permission accumulation；
- page-table memory：通过普通受保护内存路径注入；
- system register：TTBR0/1_EL1、TCR_EL1、MAIR_EL1、SCTLR_EL1、VBAR_EL1、CONTEXTIDR_EL1、NZCV。

系统寄存器使用字段白名单，记录 RW/RO、RES0/RES1、EL、写副作用及是否需要 TLBI/ISB。非法保留位不进入主 campaign。

Oracle：预期 VA→PA 映射、权限/异常类型、ASID 隔离、页表内容 hash、异常向量、Linux panic/SError/SEA/EDAC/APEI/CPER（若平台实现）。

### 7.7 BM-L3-128：鲲鹏 128B 故障域

三阶段：

1. 64B 共同基线：所有 cache level 保持 64B，用于 x86/ARM 受控对照。
2. paired-sector 代理：把相邻且 128B 对齐的两个 64B L3 block 绑定到同一 `superline_id`；注入同 sector、跨 sector、共同 tag/coherence proxy。分别报告 sector 和 superline 结果。
3. 精确扩展：Ruby/CHI 中实现共同 tag/coherence 状态 + 两个 64B data sector + 64↔128B bridge、fill/evict/snoop 合并；通过 directed coherence tests 验证。

阶段 2 不声称复现 replacement/coherence 行为；论文标题和图注必须使用 “128B fault-domain proxy”。

### 7.8 BM-COH/NUMA

- producer-consumer、false sharing、remote read/write、owner migration、跨 NUMA pointer chase。
- 注入 legal coherence state、sharer/owner id、response data、route/credit 的受约束代理。
- Oracle：单写多读一致值、协议不变量、禁止状态组合、端到端 checksum。
- simulator deadlock 与被测系统 hang 用 heartbeat、协议 watchdog、独立 simulator log 区分。

---

## 8. 工作负载、ROI 与黄金 Oracle

### 8.1 工作负载组合

| 层级 | 工作负载 | 作用 |
|---|---|---|
| Directed | 上述 BM-GPR/L1I/L1D/NEON/LSQ/TLB/L3/NUMA | 注入可达性、单元签名、机制解释 |
| Embedded | MiBench | 与既有跨 ISA 文献方向对照 |
| CPU | SPEC CPU 2017 整数/浮点子集 | 长程传播、编译器敏感性 |
| Parallel | PARSEC、SPLASH-3 | coherence、内存序、共享数据 |
| Memory | STREAM、pointer chasing | L3/TLB/NUMA |
| Kernel | BLAS、CRC、crypto | NEON/整数/FP/数据通路 |
| OS | fork/exec、context switch、page migration、filesystem stress | EL1/TLB/异常/RAS |

任何需要许可证的 workload 只记录本地版本/hash，不分发数据。

### 8.2 ROI 纪律

- 所有随机触发只在 `ROI_BEGIN` 与 `ROI_END` 之间。
- 预热、装载、退出不进入有效注入分母。
- 跨 ISA 使用相同算法、输入和编译优化意图；不可要求指令数相同。
- 触发按 committed-instruction percentile 或语义事件对齐；不按相同 tick 对齐。
- checkpoint 必须位于 ROI 前且无注入；每个 checkpoint 记录 hash。

### 8.3 黄金运行

每个 binary × input × config 至少运行 5 次无注入：

- 输出 hash、退出码、指令数、ROI ticks 和关键 stats 稳定；
- 并发程序若非确定性，使用不变量/允许结果集合，不使用单一 stdout hash；
- 浮点明确是否 bit-exact；否则固定容差并在注入前冻结；
- golden 不稳定的 cell 不进入 campaign。

---

## 9. 结果分类与数据模式

### 9.1 互斥分类

按以下顺序分类，保证每次运行只有一个主标签：

1. `SimulatorError`：模拟器 UB、assert、工具异常、配置错误；排除出架构分母。
2. `Inactive`：预定目标在触发时不存在/无效，或 XZR 写丢弃；单独报告可达率。
3. `Corrected`：保护机制纠正，最终状态与 golden 一致。
4. `DetectedContained`：检测/poison/retry/终止，没有错误输出逃逸。
5. `CrashDUE`：程序/OS 异常退出、panic、不可恢复错误。
6. `Hang`：超过预先冻结的 progress/时间阈值且无输出。
7. `SDC`：程序正常完成或服务仍可用，但 oracle 失败且未被检测。
8. `Latent`：ROI 结束时错误仍在可达状态，最终输出暂时正确；需 checkpoint/trace 证据。
9. `Masked`：有效注入但错误被覆盖、逻辑/架构屏蔽，最终状态符合 oracle。

不得把 Crash/Hang 合并进 SDC；不得把 Inactive 当 Masked；不得把 SimulatorError 当 DUE。

### 9.2 每次运行必记字段

```text
identity:
  run_id, pair_id, campaign_id, schema_version, timestamp
provenance:
  chaos_commit, gem5_commit, patchset_sha256, config_sha256,
  compiler/version/flags, binary_sha256, input_sha256, checkpoint_sha256
platform:
  isa, mode, cpu_model, cores, clocks, cache_geometry, line_size,
  protection_model, config_family
trigger:
  mode, requested_value, actual_tick, actual_cycle,
  committed_inst, pc, seq_num, roi_fraction
target:
  layer, component, instance, index/set/way/address,
  field, width_bits, active/live, semantic_role
fault:
  model, bit_indices, mask, old_value, new_value,
  duration, protection_stage, max_faults, faults_injected
dynamic_context:
  thread, priv_level, opcode, source/dest regs,
  mapped_phys_reg, freelist/renamemap status,
  reads_before_overwrite, overwritten_at_cycle,
  cache_residency, lsq_source_seq, tlb_asid
outcome:
  exit_code, stdout_sha256, stderr_sha256, final_state_sha256,
  classification, detection_signal, propagation_latency,
  panic_text, wall_time, sim_ticks, committed_insts
```

旧方案中的 `is_in_freelist`、`is_in_renamemap`、`reads_before_overwrite` 等字段只对真正的 O3/PRF 扩展有意义；架构态 CHAOSReg 不应伪造这些字段。

---

## 10. 抽样、统计与跨 ISA 比较

### 10.1 分层单位

主分层为：

```text
ISA × config × workload × target × field × fault_model × protection_stage
```

target 内再按 dynamic occupancy、bit role、ROI percentile 分层。先固定层定义，再抽样；禁止看到结果后合并层来制造显著性。

### 10.2 样本量策略

- Pilot：每 cell 100 次，用于可达率、工具错误和大致比例，不做强排名。
- Formal：每 cell 384 次，约对应最保守比例下 ±5% 的 95% 误差量级。
- 关键/低 SDC cell：扩至 663 次或顺序自适应，目标约 ±3.8%；若 0 次 SDC，95% 上界近似 `3/n`，663 次约 0.45%。
- 每个 formal cell 独立保留至少 5% 重放样本；重放不一致则冻结该 campaign。

样本量最终用 pilot 的 Wilson/Jeffreys 区间与预算重新计算，不只依赖上述经验数。

### 10.3 指标

有效注入分母：

```text
N_valid = N_total - N_inactive - N_simulator_error
P_SDC = N_SDC / N_valid
P_DUE = (N_CrashDUE + N_Hang) / N_valid
P_escape = (N_SDC + N_Latent) / N_valid
Reachability = N_valid / (N_total - N_simulator_error)
```

同时报告：

- 95% Wilson 或 Jeffreys 区间；
- per-injection、per-active-entry、per-bit、per-committed-instruction；
- occupancy/bit-time 加权 AVF；
- propagation latency 的中位数与分位数；
- raw 与 protection-aware escape probability。

没有 raw device rate/ECC coverage 时，不计算产品 FIT 点估计；只做参数化 sensitivity sweep。

### 10.4 ARM64 与 x86-64 配对规则

- C1 固定 64B line 与等价 cache capacity/associativity、核心资源意图、输入和 oracle。
- 配对的是语义角色：AArch64 Xn vs x86 GPR role、NEON lane vs SSE/AVX 等宽 lane、DMB/acquire-release vs x86 fence/atomic intent；不是简单相同 bit index。
- 使用同一 `pair_id`、ROI percentile、fault model、field role 和 protection stage。
- 用配对差值/比值及 bootstrap 或分层回归报告 ISA effect；workload、target、protection 为显式因素。
- C2 鲲鹏代理与实际 x86 产品配置另作 product-proxy 比较，不与 C1 混成“ISA 差异”。

现有受控研究只支持克制先验：在特定 gem5/MiBench 配置中，Arm 的 PRF/L1I/L1D transient SDC AVF 常高于 x86，而 LQ/SQ 可能更低；永久 L1D 不存在稳定总排序。本文实验用于检验这些结构性趋势，不用于证明预设排名。

---

## 11. 分阶段 campaign 与验收标准

### Phase 0：版本冻结和工具正确性

**工作：**固定 CHAOS/gem5/patchset；完成 G0-G7；建立单元/定向测试和日志 schema。  
**注入：**仅 synthetic state，不做性能 benchmark。  
**出口：**七个闸门全部通过；0 个未解释的 simulator error；20/20 重放一致。

### Phase 1：ARM64 SE 基线

**靶点：**架构 GPR、标量 FP、L1I/L1D/L2 data、后备内存 byte。  
**工作负载：**Directed + MiBench；每 cell pilot 100，formal 384。  
**出口：**每个目标命中率可解释；故障恰好一次；能分出 L1D 的 silent-value path 和 L1I/GPR 的 crash-heavy path；结果标 raw/no-protection。

### Phase 2：NEON 与保护感知 cache

**靶点：**NEON register/lane、FP fields、cache tag/metadata、ECC/parity 前后。  
**工作负载：**BLAS/CRC/crypto + directed。  
**出口：**128 位边界覆盖；lane/FP oracle 完整；raw 和 protection-aware 结果可分别重放。

### Phase 3：FS 地址翻译与 ARM 状态

**靶点：**TLB、walker、page table、ASID、TTBR/TCR/MAIR/SCTLR/VBAR/NZCV。  
**工作负载：**context switch、fork/exec、page migration、权限和页大小微基准。  
**出口：**entry/lookup/walker/memory fault 分开；系统寄存器全部来自白名单；异常、检测与 SDC oracle 可区分。

### Phase 4：O3 LSQ 与中枢

**优先顺序：**LSQ forwarding → PRF/RAT → ROB。  
**工作负载：**directed LSQ、memory kernels、PARSEC 子集。  
**出口：**同一 fault 可从结构状态追踪到 commit/output；无 C++ 容器破坏；地址/entry 替换始终处于合法域；LSQ 四类错误有强 oracle。

### Phase 5：鲲鹏 128B L3、coherence 与 NUMA

**靶点：**paired sectors、tag/coherence proxy、remote data/route。  
**工作负载：**STREAM、pointer chase、producer-consumer、false sharing。  
**出口：**sector/superline 结果分开；代理误差书面化；任何精确模型先通过 fill/evict/snoop/coherence directed tests。

### Phase 6：x86-ARM64 配对对照

**配置：**C1 共同 64B 基线；相同语义 fault pairs。  
**出口：**配对覆盖率、编译差异、动态指令差异全部报告；结论按 target × workload × protection 给出，不写全局 ISA 排名。

### Phase 7：鲲鹏实机校准

**工作：**只在得到授权的实验机上枚举 RAS capability、ERR* 错误记录、SEA/SError/CPER/EDAC/APEI 日志；运行无破坏性的定向签名。  
**出口：**把 E3/E4 保护假设更新为经证实/被否证/仍未知；不以电压、温度或生产负载施压，除非有单独安全审批。

---

## 12. 后续实施命令模板（本轮未执行）

以下命令用于未来 Linux 构建节点。它们是执行手册，不表示当前已完成构建。

### 12.1 固定源码

```bash
git clone --branch v25.1.0.1 --depth 1 https://github.com/gem5/gem5.git gem5-v25.1.0.1
git -C gem5-v25.1.0.1 rev-parse HEAD
git -C /path/to/CHAOS rev-parse HEAD
```

把输出的**完整** gem5 commit 写入 manifest。不要使用 `stable` 浮动分支作为论文版本标识。

### 12.2 以 patch 形式集成

```bash
cp -a /path/to/CHAOS/CHAOSReg   gem5-v25.1.0.1/src/
cp -a /path/to/CHAOS/CHAOSCache gem5-v25.1.0.1/src/
cp -a /path/to/CHAOS/CHAOSMem   gem5-v25.1.0.1/src/
git -C gem5-v25.1.0.1 diff --binary > patches/0001-chaos-upstream-import.patch
```

随后将 G0-G7 和每个扩展拆成独立 patch；不要直接在 `third_party/CHAOS` 上工作。

### 12.3 未来构建命令

```bash
scons build/ARM/gem5.opt -j"$(nproc)"
```

必须先完成所选 gem5 tag 的 API 兼容检查。当前 CHAOS README 的“All ISA/CPU compatible”不是 ARM64 正确性证据。

### 12.4 未来运行命令形态

```bash
build/ARM/gem5.opt \
  --outdir=runs/p1-gpr-qsort-000384 \
  configs/se/arm_chaos.py \
  --manifest manifests/p1-gpr-qsort-000384.yaml
```

建议所有配置只接收一个 manifest，避免命令行和结果目录中的参数漂移。runner 在启动前验证 source/config/binary/input hash，结束后验证 `faults_injected ∈ {0,1}` 并执行分类器。

---

## 13. 建议的自动化与失败处理

### 13.1 Runner 状态机

```text
validate manifest/hash
  → restore clean checkpoint
  → start simulator
  → enter ROI
  → deterministic inject
  → collect trace/oracle
  → classify
  → schema validate
  → atomic publish result
```

### 13.2 重试纪律

- 基础设施失败可重试，但保留原 run_id 并增加 `attempt`；不得挑选有利结果。
- SimulatorError 先复现与定位，修复后相关 campaign 全部重跑。
- Hang 使用冻结阈值：例如 golden ROI 指令/tick 的 10×与 heartbeat 双条件；阈值在看注入结果前确定。
- 每次 patch 改变注入语义、target enumeration 或 oracle 时，schema/campaign version 必须递增。

### 13.3 最低质量仪表板

- planned/started/completed/valid/inactive/tool-error 数量；
- 每 target/field 的 reachability；
- 单故障合规率；
- 重放一致率；
- 分类分布与 95% 区间；
- seed/bit/ROI 覆盖热图；
- raw vs protection-aware escape；
- ARM/x86 配对缺失率。

---

## 14. 预期分析产物

1. `target × field × bit-role` 的 SDC/Crash/Masked/Detected 热图。
2. GPR ABI role、NEON lane/FP field、L1I encoding field 的敏感性图。
3. LSQ 错源/漏前递/部分覆盖/次序违规的传播路径与时延。
4. TLB entry、walker、page-table memory、system register 的分层逃逸概率。
5. L3 sector 与 128B superline proxy 的 per-bit/per-entry 归一化对照。
6. raw 与 protection-aware 的风险反转图。
7. ARM64-x86 配对 effect，带 workload/target/protection 交互和置信区间。
8. 对 raw FIT、ECC coverage、scrub interval 的参数化 sensitivity sweep；不输出伪精确产品 FIT。

---

## 15. 最终决策清单

- [ ] 固定 CHAOS commit 和完整 gem5 commit，保存 patchset hash。
- [ ] 禁止运行原始 `make all`；按 ARM tag 独立构建（未来阶段）。
- [ ] G0-G7 全通过后才开始论文数据采集。
- [ ] 正式运行每次恰好一个确定性故障；概率模式只筛查。
- [ ] 架构态、PRF、执行单元、cache data/tag/ECC、memory backing-store 分层命名。
- [ ] SE 与 FS、classic 与 Ruby/CHI、raw 与 protection-aware 分开。
- [ ] 鲲鹏 920 基线只用 NEON，不用 SVE。
- [ ] 128B paired-sector 明确标 proxy。
- [ ] LSQ 为第一创新靶点，TLB/SYS 为第二，NEON 为第三。
- [ ] Inactive、SimulatorError、Crash/Hang、SDC 不混分母。
- [ ] x86/ARM 只做同语义配对，不做笼统 ISA 排名。
- [ ] 无 raw rate/保护覆盖时不换算产品 FIT。
- [ ] 实机只做经授权、非破坏性的 RAS 能力和日志校准。

---

## 16. 参考与本地材料

本方案重点继承此前研究报告第 5 章“x86-64 与 ARM64 的敏感性差异”和第 6 章“鲲鹏 920 高价值靶点与优先级”，并以当前下载的 CHAOS 固定提交重新核对实现边界。

本地材料：

- `tmp/pdfs/report-source.md`：此前深度研究报告的可编辑源稿。
- `output/pdf/ARM64_Kunpeng_SDC_Fault_Injection_Plan.pdf`：此前完整研究报告。
- `实验方案与提示词_v3.md`：已有字段、分类和实验记录经验。
- `逐结构注入速查表.md`：结构级靶点与风险速查。
- `third_party/CHAOS/README.md` 及三个模块源码：本次方案的实现审计依据。

外部版本依据：

- CHAOS：<https://github.com/eliovinciguerra/CHAOS>
- gem5 releases：<https://github.com/gem5/gem5/releases>
- gem5 stable source：<https://github.com/gem5/gem5/tree/stable>

## 17. 本轮完成边界

已完成：CHAOS 仓库下载、commit 固定、只读源码审计、ARM64/鲲鹏导向的完整实验方案设计。  
未执行：gem5/CHAOS 编译、benchmark、fault campaign、源码修改、系统依赖安装。  
因此，本文中的命令、接口和验收项是后续实施规范，不是已经运行通过的结果。
