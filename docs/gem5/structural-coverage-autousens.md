# 结构覆盖度评估与 AutoµSens 原型

本文对应技术路线文档 `sdcfuzz/sdcfuzz-v1.2.md` §5.1（AutoµSens）与 §7
Phase 1 的交付物“自动靶向生成器原型 + 结构覆盖度评估工具”。当前实现是一个
只使用 gem5 O3 已有指标的**原型**：先把“指令 → 微架构结构激活”测出来，
再按目标结构逆向挑选指令、合成候选程序并在 gem5 里评估其覆盖向量。

2026-11-14 的收尾把三处“看起来完成、实际会误报”的问题修掉了：

1. 默认 gem5 路径指向 `build/ARM_ACE_IBR_AUDIT`（x86-64 ELF），在 aarch64
   主机上直接 `Exec format error`；现在优先解析原生 `build/ARM/gem5.opt`。
2. `l1i` 只有 cache-line 级需求读，16 条短探测流都低于逐指令噪声底，旧版
   `target --structure l1i` 会把边界噪声当成信号；现在有逐指令下限并显式拒绝。
3. 回归脚本曾断言 `target l1d` 必须选中 `ldr`，但 `ldr`/`ldxr` 的实测激活
   只差几个事件，谁排第一取决于当次运行；现在断言“选中任一 load 类探针”。

## 1. 可观测结构与可靶向性

原型只映射 gem5 里已经有真实指标的九类结构，不虚构没有实现的覆盖：

| 结构键 | 数据来源 | 单位 | 可逐指令靶向 |
|---|---|---|---|
| `rf` | `*.rfAce.intTrackedReads/intTrackedWrites` | 整数物理寄存器访问次数（读 + 写） | 是 |
| `vec` | `*.rfAce.vecTrackedReads/vecTrackedWrites` | 向量/FP 物理寄存器低 64 位 lane 访问次数 | 是 |
| `l1i` | `l1i-cache-0.l1Ace.trackedDemandReads` | L1I 需求读次数（cache line 事件） | **否**（见下） |
| `l1d` | `l1d-cache-0.l1Ace.trackedDemandReads/trackedDemandWrites` | L1D 需求读 + 需求写次数 | 是 |
| `alu` | `*.fuIbr.inputBits::intAlu` | intAlu 有效输入位数 | 是 |
| `mult` | `*.fuIbr.inputBits::intMult` | intMult 有效输入位数 | 是 |
| `div` | `*.fuIbr.inputBits::intDiv` | intDiv 有效输入位数 | 是 |
| `fpadd` | `*.fuIbr.inputBits::fpAdd` | 标量 fpAdd 有效输入位数 | 是 |
| `fpmul` | `*.fuIbr.inputBits::fpMult` | 标量 fpMult 有效输入位数 | 是 |

`l1i` 的激活是 cache line 事件：探测循环体只有几十字节，稳定落在一行内，
逐指令归因后只剩个位数噪声。`structure_map.json` 的 `targetability` 字段会
给出每个结构的 `best_instruction`、`max_per_instruction`、`floor_per_instruction`
和 `targetable`；`target`/`pareto` 对低于下限的结构直接失败，不会生成一个
“看起来靶向、实际没有激活”的候选。`l1i` 仍由模板覆盖矩阵测量（`l1i-big-body`
约 1.3k 需求读），只是不做逐指令逆向。

指标本身的定义与边界见 `rf-ace-implementation.md`、`l1-cache-ace-implementation.md`
和 `fu-ibr-implementation.md`。不同结构的激活值**量纲不同**（寄存器访问次数、
cache line 事件、输入位数），只能在同一结构内比较不同指令，不能跨结构相加
或比较大小。

SIMD/SVE、TLB 仍没有对应映射；ROB/LSQ/PRF/FU/issue 的“占用深度”由独立的
SAD 指标测量（`sad-implementation.md`）。`autousens evaluate` 和
`coverage_report` 会在 stats 里检测到 `.sad.*` 时一并输出占用表。

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

实测中同一结构内的归因差异是量级级别的。2026-11-14、60 次迭代（3840 条动态
指令）时：`add` 的 `alu=493632`（3840 × 2 端口 × 64 位 = 491520 附近），
`madd` 的 `mult=737280`（3840 × 3 × 64），`ldr` 的 `l1d=3846`（1.002 次
需求读/指令），`fadd` 的 `fpadd=491520`、`vec=11523`。

## 3. 工具用法

工具为 `tools/autousens.py`。默认自动解析原生 `build/ARM/gem5.opt`（可用
`GEM5_OPT` 或 `--gem5` 覆盖）和本机可用的 AArch64 交叉编译器
（`aarch64-openEuler-linux-gcc` / `aarch64-linux-gnu-gcc`，可用 `ARM_CC` 或
`--cc` 覆盖）。`--sad` 可同时采集 SAD 占用。

### 3.1 构建指令 → 结构映射

```bash
python3 tools/autousens.py map \
  --outdir m5out/autousens-map --iterations 60 [--sad]
```

输出 `structure_map.json`：每个探测模式的 `raw`、`net`、`activation`、
`activation_per_instruction`、`coverage`、`clamped`，基线记录、单位说明、
边界说明，以及 `targetability`。控制台按结构打印非零激活：

```text
add      rf=11536 alu=493632
mul      rf=11536 mult=737280
udiv     rf=11536 div=494080
ldr      rf=7700 l1d=3846
str      rf=7695 l1d=3842
```

`targetability` 的实测摘要（60 次迭代）：

```text
rf     best=madd 3.99/instr  targetable
vec    best=fadd 3.00/instr  targetable
l1i    best=udiv 0.029/instr NOT targetable (floor 0.10)
l1d    best=ldxr 1.00/instr  targetable
alu    best=add  128.5/instr targetable
mult   best=mul  192.0/instr targetable
div    best=udiv 128.7/instr targetable
fpadd  best=fadd 128.0/instr targetable
fpmul  best=fmul 129.0/instr targetable
```

### 3.2 逆向靶向生成与评估

```bash
python3 tools/autousens.py target \
  --map m5out/autousens-map/structure_map.json \
  --structure l1d --top 2 \
  --outdir m5out/autousens-l1d --iterations 60 [--sad]
```

按目标结构的**每指令**激活排序（并列时按模式名稳定排序），取前 `--top` 条
指令，生成 `candidate.c`，用交叉编译器编译后在 gem5 中运行，再跑一次同构建
的基线，输出 `candidate_report.json`：候选覆盖向量、基线覆盖向量、净激活、
`clamped`（以及 `--sad` 时的 SAD 占用）。实测 `--structure l1d --top 2`
选中 `ldxr,ldr`，净需求读 7681；`--structure mult --top 1` 选中 `madd`，
净 mult 输入位 737088。

候选程序由已验证的指令片段组合而成，只覆盖“指令组合”这一层：它不做完整
ISA 合法性搜索，也不评估数据值语义；每条指令流的执行正确性由探测负载的
`PASS` 自检保证，候选本身只打印 `status=DONE`，其质量由指标断言。

### 3.3 跨结构加权聚合

```bash
python3 tools/autousens.py target \
  --map m5out/autousens-map/structure_map.json \
  --structure l1d,alu --weights 1,1 --top 1 \
  --outdir m5out/autousens-l1d-alu --iterations 60
```

先按结构归一化每指令激活（不同结构量纲不同，不能直接相加），再按权重从高
到低贪心选择互不重复的指令，合成一个候选并在 gem5 中评估。实测选中
`ldxr,movz`：`l1d` 净 3844、`alu` 净 491584。这是跨结构的加权聚合，与 3.4
的 NSGA-II 多目标序列集是两条并行路径。

### 3.4 NSGA-II 多目标序列集

```bash
python3 tools/autousens.py pareto \
  --map m5out/autousens-map/structure_map.json \
  --structure l1d,alu --length 3 \
  --population 24 --generations 8 --seed 42 \
  --outdir m5out/autousens-pareto --validate [--sad]
```

`pareto` 以每条指令在每个目标结构上的归一化**每指令**激活为决策目标，用
确定性的 NSGA-II（快速非支配排序 + 拥挤距离 + 二元锦标赛 + 均匀交叉 +
逐基因变异）搜索指令序列。输出 `pareto_set.json`（每条序列的基因、指令名、
各目标值、源码路径）与候选 C 文件；`--validate` 会把 knee 点真实编译进
gem5 跑一次，要求每个目标结构的**净激活 > 0**，并报告 coverage、基线与
可选的 SAD。核心算法在 `tools/nsga2.py`，有独立单测
（`tests/test_nsga2.py`）。

实测（iterations=60）：`pareto` 非空（两次运行 size=8–14）
knee=['str','str','movz'] 或 ['add','ldxr','movz'] l1d_net=1920 alu_net=122688`，说明 Pareto 集同时
保留 l1d 与 alu 的不同折中。

### 3.5 对已有结果重算覆盖向量

```bash
python3 tools/autousens.py evaluate \
  --dir m5out/autousens-l1d/run \
  --baseline-dir m5out/autousens-l1d/baseline
```

输出该目录的 `coverage`（九个结构的 ratio）、相对基线的 `net`/`activation`，
以及 stats 中存在 SAD 时的 `sad`（samples、各资源 ratio/usedSum/capacity）。
该子命令可用于任意一次 `--rf_ace --l1_ace --fu_ibr [--sad]` 运行。

### 3.6 结构覆盖度汇总

```bash
python3 -m sdcfuzz.coverage_report \
  --matrix m5out/coverage-matrix/coverage_matrix.json \
  --outdir m5out/coverage-matrix/report \
  --sad-run m5out/sad-test/rob
```

输入 `scripts/test-template-coverage.py` 产出的 `coverage_matrix.json`，输出
`coverage_summary.json`、`coverage_matrix.csv`、`coverage_summary.md`。
汇总用**计数器下限**（而不是 `ratio > 0`）判断“真的激活了”：`rf/vec` 100 次
访问、`l1i/l1d` 50 次事件、五类 FU 1000 输入位。这样 `vec` 不会因为每个模板
都有 8 次寄存器写就被算成覆盖。状态分为：

- `targeted`：有模板以该结构为 target；
- `support`：没有模板以它为 target，但被模板的必需指标覆盖（`rf`、`vec`）；
- `incidental`：只有低于下限的偶然活动；
- `unobserved`：所有模板均为 0。

2026-11-14 的 19 模板矩阵：9/9 结构有真实激活，7 个 `targeted`，`rf/vec`
为 `support`，无 `incidental`/`unobserved`；`l1i` 由 `l1i-big-body` 定向
（target 与 target-metric 契约都为 1）。

### 3.7 Phase 1 一键验收

```bash
bash scripts/test-phase1.sh
```

按顺序跑：5 个纯 Python 单测文件、AutoµSens 全结构回归、19 模板覆盖矩阵、
SAD、RF ACE、L1 ACE、FU IBR、ACE/IBR 交叉正确性、覆盖汇总，共 9 步。每步
完整日志在 `m5out/phase1-gate/<step>.log`，汇总在
`m5out/phase1-gate/phase1_gate.json`；任一步非零退出则整体失败。它也会
自动选择原生 gem5 与 openEuler 交叉编译器，不依赖 conda。

## 4. 边界与已知限制

- **跨结构不可比**：`rf`/`vec`/`l1i`/`l1d` 是事件计数，`alu`/`mult`/`div`/
  `fpadd`/`fpmul` 是输入位数。原型只在同一结构内排序，不输出“综合脆弱度”分数。
- **逐指令噪声底**：靶向下限是每指令激活（`rf/vec` 0.25、`l1d` 0.50、
  五类 FU 32 输入位、`l1i` 0.10）。下限是工程阈值，不是统计显著性检验；
  超过下限只说明信号远高于基线噪声，不说明一定触发 SDC。
- **`l1i` 不可逐指令靶向**：cache-line 粒度，短探测流无法把激活归因到单条
  指令；用模板矩阵（`l1i-big-body`）评估，不用 `target l1i`。
- **边界推测发射**：ROI 结束标记执行前，CPU 可能已经推测发射了标记之后的
  1–2 条指令。RF ACE 按 seqNum 过滤，不受影响；FU IBR 按实际发射计入，因此
  探测净计数里会出现固定的极小噪声。这是 FU IBR 已知的采样口径，不是探测
  负载的 bug。
- **FU IBR 子集**：整数 add/sub、逻辑、MOVZ/MOVK、同宽 MADD/MSUB、UDIV/SDIV，
  以及标量 FADD/FSUB/FMUL/FDIV 计数；二源移位（如 `LSLV`）和 SIMD/SVE
  不在子集内。
- **SAD 独立**：ROB/IQ/LQ/SQ/PRF/FU/issue 的占用深度由 `sad` 指标测量，
  是 ROI 内的占用比例，不是逐指令激活；`--sad` 只是把两者放进同一份报告。
- **生成器范围**：`target` 从映射里挑指令并组合；`pareto` 在离散指令序列
  空间做 NSGA-II。两者都不做完整 ISA 合法性求解，也不评估数据值语义；
  故障注入与功耗应力仍属后续阶段。

## 5. 验证

```bash
bash scripts/test-phase1.sh
# 或单独：
python3 scripts/test-autousens.py --gem5 CHAOS/gem5/build/ARM/gem5.opt
python3 scripts/test-template-coverage.py --gem5 CHAOS/gem5/build/ARM/gem5.opt
python3 -m sdcfuzz.coverage_report --matrix .../coverage_matrix.json --outdir ...
```

`test-autousens.py` 真实编译探测负载、跑完整映射、对**每个**可靶向结构做
target、做 NSGA-II knee 验证，并断言：

- `add/sub/and/orr/eor/movz/add_imm/add_lsl` 的 `alu` 激活 > 300000；
- `mul/madd` 的 `mult` 激活 > 500000，`udiv` 的 `div` 激活 > 300000；
- `ldr/ldxr/str` 的 `l1d` 激活 > 3000，纯 ALU 流低于 2% 噪声；
- `fadd`/`fmul` 的 `fpAdd`/`fpMult` 激活 > 300000，向量 RF 激活 > 3000；
- `ldr` 的每指令 L1D 需求读在 0.95–1.05；
- `l1d` 靶向选出的指令包含任一 load 类探针（`ldr`/`ldxr`），候选净需求读
  > 0；`l1d+alu` 同时选中访存与 ALU 指令，两个结构净激活 > 0；
- 8 个可靶向结构（除 `l1i`）逐一 target 后目标结构净激活 > 0；
- NSGA-II Pareto 集非空、两两非支配、目标值在 `[0,1]`，knee 点在真实 gem5
  中对每个目标结构都有净激活；
- 未知结构、缺少 `baseline` 的探测集、噪声级 `l1i` 靶向都以非零码失败。

实测输出（2026-11-14，原生 aarch64 `build/ARM/gem5.opt`，
`m5out/phase1-verify-20261114/v2/autousens.log`）：

```text
alu: add=493632 sub=493888 and=493504 orr=494272 eor=494016
mult: mul=737280 madd=737280
div: udiv=494080; mul=0 (noise)
l1d: ldr=3846 ldxr=3852 str=3842 (ldr per instruction=1.002)
template forms: movz=497408 add_imm=493120 add_lsl=491072 fadd=491520 fmul=495360
rf: add=11536 ldr=7700 str=7695
vec: fadd=11523 fmul=11523
target l1d: chosen=['ldxr', 'ldr'] net_reads=7681
target l1d+alu: chosen=['ldxr', 'movz'] l1d_net=3844 alu_net=491584
target mult: chosen=['madd'] net_mult=737088
target all: alu div fpadd fpmul l1d mult rf vec
pareto: size=8 knee=['add','ldxr','movz'] l1d_net=967 alu_net=246464
（另一轮：size=14 knee=['str','str','movz'] l1d_net=1920 alu_net=122688）
error handling: unknown structure, missing baseline and noise-only l1i all fail loudly
```

完整输出目录为 `m5out/phase1-verify-20261114/v2/autousens/`，包含每个探测
模式的 `gem5.log` 与 `stats.txt`、映射 JSON、候选源码/报告、Pareto 集和
基线结果；模板矩阵与汇总在 `.../v2/coverage2/`。
