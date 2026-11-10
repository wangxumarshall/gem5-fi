# 结构覆盖度评估与 AutoµSens 原型

本文对应技术路线文档 `sdcfuzz/sdcfuzz-v1.2.md` §5.1（AutoµSens）与 §7
Phase 1 的交付物“自动靶向生成器原型 + 结构覆盖度评估工具”。当前实现是一个
只使用 gem5 O3 已有指标的**原型**：先把“指令 → 微架构结构激活”测出来，
再按目标结构逆向挑选指令、合成候选程序并在 gem5 里评估其覆盖向量。

## 1. 可观测结构

原型只映射 gem5 里已经有真实指标的九类结构，不虚构没有实现的覆盖：

| 结构键 | 数据来源 | 单位 |
|---|---|---|
| `rf` | `*.rfAce.intTrackedReads/intTrackedWrites` | 整数物理寄存器访问次数（读 + 写） |
| `vec` | `*.rfAce.vecTrackedReads/vecTrackedWrites` | 向量/FP 物理寄存器低 64 位 lane 访问次数 |
| `l1i` | `l1i-cache-0.l1Ace.trackedDemandReads` | L1I 需求读次数（cache line 事件） |
| `l1d` | `l1d-cache-0.l1Ace.trackedDemandReads/trackedDemandWrites` | L1D 需求读 + 需求写次数 |
| `alu` | `*.fuIbr.inputBits::intAlu` | intAlu 有效输入位数 |
| `mult` | `*.fuIbr.inputBits::intMult` | intMult 有效输入位数 |
| `div` | `*.fuIbr.inputBits::intDiv` | intDiv 有效输入位数 |
| `fpadd` | `*.fuIbr.inputBits::fpAdd` | 标量 fpAdd 有效输入位数 |
| `fpmul` | `*.fuIbr.inputBits::fpMult` | 标量 fpMult 有效输入位数 |

指标本身的定义与边界见 `rf-ace-implementation.md`、`l1-cache-ace-implementation.md`
和 `fu-ibr-implementation.md`。不同结构的激活值**量纲不同**（寄存器访问次数、
cache line 事件、输入位数），只能在同一结构内比较不同指令，不能跨结构相加
或比较大小。

SIMD/SVE、TLB 仍没有对应映射；ROB/LSQ/PRF/FU/issue 的“占用深度”由独立的
SAD 指标测量（`sad-implementation.md`），不与这里的逐指令激活混为一谈。

## 2. 探测负载与基线扣除

`workloads/directed/structural_probe_workload.c` 提供 17 个探测流：
`baseline`（空循环）以及
`add/sub/and/orr/eor/mul/madd/udiv/ldr/str/ldxr/movz/add_imm/add_lsl/fadd/fmul`。
每个流在 `m5_work_begin(7, 0)` 与 `m5_work_end(7, 0)` 之间执行
“16 组 × 4 条目标指令 × iterations”，prologue、结果校验和输出都在窗口之外。
每条流用 C 参考实现校验自己的计算结果，输出 `status=PASS`；探测指令若被执行
错误，先失败在 guest 自检上，而不是污染结构映射。`fadd`/`fmul` 用 `d0/d1`
和 `fmov` 返回 FP 结果位模式。

结构激活定义为同形状空循环基线之上的净计数：

```text
net[counter]        = max(0, probe[counter] - baseline[counter])
activation[struct]  = sum(net counters of that structure)
per_instruction     = activation / (iterations * 16 * 4)
```

负差值钳制为 0，并在映射文件的 `clamped` 字段里逐项列出，不隐藏基线噪声。
基线扣除是必要的：同一循环骨架里的 `subs`/`b.ne`、循环外溢出的推测发射都会
进入统计，直接读绝对值会把所有指令都算成“活跃”。

实测中同一结构内的归因差异是量级级别的，例如 60 次迭代（3840 条动态指令）时
`add` 的 `alu` 激活为 486336（3840 × 2 端口 × 64 位 = 491520 的理论值附近），
`mul` 的 `mult` 激活为 737664（3840 × 3 × 64 = 737280 附近），`ldr` 的 `l1d`
激活为 3850（约等于 1.003 次需求读/指令）。

## 3. 工具用法

工具为 `tools/autousens.py`，需要带 RF ACE / L1 ACE / FU IBR 的 ARM target
gem5 和 `aarch64-linux-gnu-gcc`。

### 3.1 构建指令 → 结构映射

```bash
python3 tools/autousens.py map \
  --gem5 CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt \
  --outdir m5out/autousens-map --iterations 60
```

输出 `m5out/autousens-map/structure_map.json`，包含每个探测模式的 `raw`、
`net`、`activation`、`activation_per_instruction`、`coverage` 和 `clamped`，
以及基线记录、单位说明和边界说明。控制台按结构打印非零激活：

```text
add      rf=11520 alu=486336 mult=192
mul      rf=11519 l1d=2 mult=737664
udiv     rf=11522 mult=192 div=493056
ldr      rf=7679 l1d=3850
str      rf=7680 l1d=3846
```

### 3.2 逆向靶向生成与评估

```bash
python3 tools/autousens.py target \
  --gem5 CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt \
  --map m5out/autousens-map/structure_map.json \
  --structure l1d --top 2 \
  --outdir m5out/autousens-l1d --iterations 60
```

按目标结构的激活量排序（并列时按模式名稳定排序），取前 `--top` 条指令，
生成 `candidate.c`，用交叉编译器编译后在 gem5 中运行，再跑一次同构建的基线，
输出 `candidate_report.json`：候选的覆盖向量、基线覆盖向量、净激活和 `clamped`。
实测 `--structure l1d --top 2` 选中 `ldr, ldxr`，候选的
`l1d aceRatio = 0.0019`，基线为 `0.000974`；`--structure mult --top 1`
选中 `mul`，`mult ibrRatio = 0.162489`，基线为 0。

候选程序由已验证的指令片段组合而成，只覆盖“指令组合”这一层：它不做 ISA
合法性搜索，也不评估数据值语义；每条指令流的执行正确性由探测负载的 `PASS`
自检保证，候选本身只打印 `status=DONE`，其质量由指标断言。

### 3.3 跨结构加权聚合

```bash
python3 tools/autousens.py target \
  --map m5out/autousens-map/structure_map.json \
  --structure l1d,alu --weights 1,1 --top 1 \
  --outdir m5out/autousens-l1d-alu --iterations 60
```

先按结构归一化激活（不同结构量纲不同，不能直接相加），再按权重从高到低
贪心选择互不重复的指令，合成一个候选并在 gem5 中评估。实测选中 `ldr,add`：
`l1d` 覆盖 0.001876（基线 0.000974），`alu` 覆盖 0.300633（基线 0.014472）。
这是跨结构的加权聚合，不是 NSGA-II 多目标序列集；后者仍是路线图 Phase 1
的未完成项，进度图里单独标注。

### 3.4 NSGA-II 多目标序列集

```bash
python3 tools/autousens.py pareto \
  --map m5out/autousens-map/structure_map.json \
  --structure l1d,alu --length 3 \
  --population 32 --generations 20 --seed 42 \
  --outdir m5out/autousens-pareto --validate
```

`pareto` 以每条指令在每个目标结构上的归一化激活为决策目标，用确定性的
NSGA-II（快速非支配排序 + 拥挤距离 + 二元锦标赛 + 均匀交叉 + 逐基因变异）
搜索指令序列。输出 `pareto_set.json`（每条序列的基因、指令名、各目标值、
源码路径）与候选 C 文件；`--validate` 会把 knee 点真实编译进 gem5 跑一次，
要求每个目标结构的**净激活 > 0**，并报告 coverage 与基线。核心算法在
`tools/nsga2.py`，有独立单测（`tests/test_nsga2.py`）。

实测（iterations=60）：`pareto: size=12 knee=['str', 'movz', 'str']
l1d_net=1920 alu_net=123328`，说明 Pareto 集同时保留 l1d 与 alu 的不同折中。

### 3.5 对已有结果重算覆盖向量

```bash
python3 tools/autousens.py evaluate \
  --dir m5out/autousens-l1d/run \
  --baseline-dir m5out/autousens-l1d/baseline
```

输出该目录的 `coverage`（九个结构的 ratio）以及相对基线的 `net`/`activation`。
该子命令可以用于骨架里任意一次 `--rf_ace --l1_ace --fu_ibr` 运行。

## 4. 边界与已知限制

- **跨结构不可比**：`rf`/`vec`/`l1i`/`l1d` 是事件计数，`alu`/`mult`/`div`/
  `fpadd`/`fpmul` 是输入位数。原型只在同一结构内排序，不输出“综合脆弱度”分数。
- **边界推测发射**：ROI 结束标记执行前，CPU 可能已经推测发射了标记之后的
  1–2 条指令。RF ACE 按 seqNum 过滤，不受影响；FU IBR 按实际发射计入，因此
  探测净计数里会出现固定的极小噪声。这是 FU IBR 已知的采样口径，不是探测
  负载的 bug。
- **FU IBR 子集**：整数 add/sub、逻辑、MOVZ/MOVK、同宽 MADD/MSUB、UDIV/SDIV，
  以及标量 FADD/FSUB/FMUL/FDIV 计数；二源移位（如 `LSLV`）和 SIMD/SVE
  不在子集内。
- **SAD 独立**：ROB/IQ/LQ/SQ/PRF/FU/issue 的占用深度由 `sad` 指标测量，
  不属于本文件的逐指令激活映射。
- **生成器范围**：`target` 从映射里挑指令并组合；`pareto` 在离散指令序列
  空间做 NSGA-II。两者都不做完整 ISA 合法性求解，也不评估数据值语义；
  故障注入与功耗应力仍属后续阶段。

## 5. 验证

```bash
python3 scripts/test-autousens.py \
  --gem5 CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt
```

脚本真实编译探测负载、跑完整映射、靶向生成与 NSGA-II 验证，断言：

- `add/sub/and/orr/eor/movz/add_imm/add_lsl` 的 `alu` 激活 > 300000；
- `mul/madd` 的 `mult` 激活 > 500000，`udiv` 的 `div` 激活 > 300000；
- `ldr/ldxr/str` 的 `l1d` 激活 > 3000，纯 ALU 流低于 2% 噪声；
- `fadd`/`fmul` 的 `fpAdd`/`fpMult` 激活 > 300000，向量 RF 激活 > 3000；
- `ldr` 的每指令 L1D 需求读在 0.95–1.05；
- `l1d` 靶向选出的指令包含 `ldr`，候选净需求读 > 0；`l1d+alu` 同时选中
  访存与 ALU 指令，两个结构净激活 > 0；
- NSGA-II Pareto 集非空、两两非支配、目标值在 `[0,1]`，knee 点在真实 gem5
  中对每个目标结构都有净激活；
- 未知结构、缺少 `baseline` 的探测集都以非零码失败。

实测输出（2026-11-10，原生 aarch64 `build/ARM/gem5.opt`）：

```text
alu: add=493760 sub=494272 and=493632 orr=494016 eor=494016
mult: mul=737280 madd=737280
div: udiv=494208; mul=0 (noise)
l1d: ldr=3846 ldxr=3846 str=3842 (ldr per instruction=1.002)
template forms: movz=495936 add_imm=493632 add_lsl=491584 fadd=491520 fmul=495488
rf: add=11536 ldr=7700 str=7695
vec: fadd=11523 fmul=11523
target l1d: chosen=['ldr', 'ldxr'] net_reads=7686 coverage=0.001913
target l1d+alu: chosen=['ldr', 'movz'] l1d_net=3844 alu_net=491584
target mult: chosen=['madd'] net_mult=737088
evaluate: l1d net reads=7686
pareto: size=12 knee=['str', 'movz', 'str'] l1d_net=1920 alu_net=123328
error handling: unknown structure and missing baseline both fail
```

完整输出目录为 `m5out/autousens-test/`，包含每个探测模式的 `gem5.log` 与
`stats.txt`、映射 JSON、候选源码/报告、Pareto 集和基线结果。
