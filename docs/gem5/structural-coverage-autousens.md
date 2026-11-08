# 结构覆盖度评估与 AutoµSens 原型

本文对应技术路线文档 `sdcfuzz/sdcfuzz-v1.2.md` §5.1（AutoµSens）与 §7
Phase 1 的交付物“自动靶向生成器原型 + 结构覆盖度评估工具”。当前实现是一个
只使用 gem5 O3 已有指标的**原型**：先把“指令 → 微架构结构激活”测出来，
再按目标结构逆向挑选指令、合成候选程序并在 gem5 里评估其覆盖向量。

## 1. 可观测结构

原型只映射 gem5 里已经有真实指标的六类结构，不虚构没有实现的覆盖：

| 结构键 | 数据来源 | 单位 |
|---|---|---|
| `rf` | `*.rfAce.intTrackedReads/intTrackedWrites` | 整数物理寄存器访问次数（读 + 写） |
| `l1i` | `l1i-cache-0.l1Ace.trackedDemandReads` | L1I 需求读次数（cache line 事件） |
| `l1d` | `l1d-cache-0.l1Ace.trackedDemandReads/trackedDemandWrites` | L1D 需求读 + 需求写次数 |
| `alu` | `*.fuIbr.inputBits::intAlu` | intAlu 有效输入位数 |
| `mult` | `*.fuIbr.inputBits::intMult` | intMult 有效输入位数 |
| `div` | `*.fuIbr.inputBits::intDiv` | intDiv 有效输入位数 |

指标本身的定义与边界见 `rf-ace-implementation.md`、`l1-cache-ace-implementation.md`
和 `fu-ibr-implementation.md`。不同结构的激活值**量纲不同**（寄存器访问次数、
cache line 事件、输入位数），只能在同一结构内比较不同指令，不能跨结构相加
或比较大小。

FP/SIMD/SVE、TLB、ROB、LSQ 等结构目前没有对应指标，因此不在 `STRUCTURE_MAP`
里，工具会把它列为不支持而不是给出 0。`SAD`（结构激活深度）仍是路线图上的
后续指标，本原型不冒充 SAD。

## 2. 探测负载与基线扣除

`workloads/directed/structural_probe_workload.c` 提供 12 个探测流：
`baseline`（空循环）以及 `add/sub/and/orr/eor/mul/madd/udiv/ldr/str/ldxr`。
每个流在 `m5_work_begin(7, 0)` 与 `m5_work_end(7, 0)` 之间执行
“16 组 × 4 条目标指令 × iterations”，prologue、结果校验和输出都在窗口之外。
每条流用 C 参考实现校验自己的计算结果，输出 `status=PASS`；探测指令若被执行
错误，先失败在 guest 自检上，而不是污染结构映射。

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

### 3.3 对已有结果重算覆盖向量

```bash
python3 tools/autousens.py evaluate \
  --dir m5out/autousens-l1d/run \
  --baseline-dir m5out/autousens-l1d/baseline
```

输出该目录的 `coverage`（六个结构的 ratio）以及相对基线的 `net`/`activation`。
该子命令可以用于骨架里任意一次 `--rf_ace --l1_ace --fu_ibr` 运行。

## 4. 边界与已知限制

- **跨结构不可比**：`rf`/`l1i`/`l1d` 是事件计数，`alu`/`mult`/`div` 是输入
  位数。原型只在同一结构内排序，不输出“综合脆弱度”分数。
- **边界推测发射**：ROI 结束标记执行前，CPU 可能已经推测发射了标记之后的
  1–2 条指令。RF ACE 按 seqNum 过滤，不受影响；FU IBR 按实际发射计入，因此
  探测净计数里会出现固定的极小噪声（实测约 192 个 intMult 输入位，即 1 条
  MADD）。这是 FU IBR 已知的采样口径，不是探测负载的 bug。
- **FU IBR 子集**：只有 add/sub、逻辑、同宽 MADD/MSUB、UDIV/SDIV 计数。
  二源移位（如 `LSLV`）不在子集内，因此 `lsl` 没有进入探测集；它的 ALU 活动
  在映射里会表现为“没有可观测激活”，加进去只会误导。
- **无 SAD/FP/TLB**：没有门级激活深度、FP/SIMD/SVE、TLB、ROB、LSQ 指标。
- **生成器范围**：只做“从映射里挑指令并组合”，不是 AutoµSens 论文意义上的
  约束求解器；跨结构联合优化、RL 变异和功耗应力仍是后续阶段。

## 5. 验证

```bash
python3 scripts/test-autousens.py \
  --gem5 CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt
```

脚本真实编译探测负载、跑完整映射和两次靶向生成，断言：

- `add/sub/and/orr/eor` 的 `alu` 激活 > 100000，`mul/madd/ldr/str/ldxr` 的
  `alu` 低于同结构参考值的 1%；
- `mul/madd` 的 `mult` 激活 > 500000，其他流低于 1%；
- `udiv` 的 `div` 激活 > 300000，其他流低于 1%；
- `ldr/ldxr/str` 的 `l1d` 激活 > 3000，纯 ALU 流低于 100；
- `ldr` 的每指令 L1D 需求读在 0.95–1.05；
- `l1d` 靶向选出的指令包含 `ldr`，候选源码包含 `ldr x8, [%[buf]]`，候选的
  `l1d` 净需求读 > 0 且覆盖高于基线；
- 未知结构、缺少 `baseline` 的探测集都以非零码失败。

实测输出（2026-11-08，`ARM_ACE_IBR_AUDIT/gem5.opt`）：

```text
alu: add=486336 sub=485312 and=485440 orr=485312 eor=485952
mult: mul=737664 madd=737472
div: udiv=493056; mul=128 (noise)
l1d: ldr=3850 ldxr=3846 str=3846 (ldr per instruction=1.003)
rf: add=11520 ldr=7679 str=7680
target l1d: chosen=['ldr', 'ldxr'] coverage=0.001900 baseline=0.000974
target mult: chosen=['mul'] net_mult=736896
evaluate: l1d net reads=7688
error handling: unknown structure and missing baseline both fail
```

完整输出目录为 `m5out/autousens-test/`，包含每个探测模式的 `gem5.log` 与
`stats.txt`、映射 JSON、两个候选的源码/报告和基线结果。
