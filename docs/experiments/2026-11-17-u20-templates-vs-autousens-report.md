# 20 条上游手工模板 vs AutoµSens：执行级覆盖对比（2026-11-17）

- 主机：`sdc-0103`（aarch64，128 核），gem5 `CHAOS/gem5/build/ARM/gem5.opt`
- 模型：`configs/se/arm_chaos.py --cpu=O3 --kp920_proxy --rf_ace
  --rf_ace_granularity=bit --l1_ace --fu_ibr --sad`
- 模板：`sdcfuzz/upstream/seeds/*.S`，20 条，逐字节来自上游 707db35d
  （`SHA256SUMS` 固定）
- 全部数字来自本轮真实 gem5 运行；预实验发现两处 harness 混淆后已作废并重跑
  （见 §2.4）。最终产物：`m5out/autousens-eval/2026-11-17-u20-fixed/`、
  `m5out/autousens-eval/2026-11-17-u20-budget-fixed/`

> **2026-11-23 更正（远程实机复核）**：本报告 §3/§4 把 `sad.fu.ratio`
> 的 8.62× 解释为“乘加端口占用”，这不成立。`sad.fu` 是全体 FU 的单一
> 聚合，定向运行 `usedSum::fu == issuedOps`，`fu = issueWidth/numUnits ×
> issue`；8.62× 就是 issue 比（0.74023155/0.08583987 = 8.6234）。另外，
> SAD 的 `samples` 是活跃周期，ACE/IBR 的 `measuredCycles` 含 idle 周期
> （实测 `samples = numCycles - idleCycles - 1`），两者不可直接按同一窗口
> 比较；u20 的 0/80 `window_consistent` 是口径差异，不是漏采样。详见
> `docs/sad-review-2026-11-23.md`。历史数值保留，上述解释以本注为准。

> **范围修正（2026-11-17 追加）**：本实验的 Auto 臂是 `target --top 1` 的
> **单模式均匀重复**，不是路线文档 §5.1 的完整 AutoµSens（最高激活子集 +
> 跨结构 NSGA-II/加权聚合 → Pareto 序列集）。因此本文的“模板 vs Auto”
> 胜负只适用于这个**最弱退化基线**，不能判定 AutoµSens 路线整体是否优于
> 手工模板；多模式、顺序优化、多样性、SAD 闭环均未测试。

## 摘要

1. **不存在单一赢家。** 在约 4096 条 ROI 指令的等量执行预算下，20 个单元中
   模板在 **9 个**、top-1 Auto 臂在 **11 个** 单元的头号指标上更高；按结构聚合后
   的结论同样是分结构的（§3.1–3.2）。
2. **模板明显更高的结构**：ALU IBR（e1 2.63×、e3 2.47×，中位 2.55×）、
   L1D ACE 的 c1/m1/v5（2.04×/2.02×/2.16×，且 `aceLineCycles` 分别
   2.66×/2.69×/23.1×）、L1I 的 i1（1.20×，`trackedDemandReads` 9.21×）、
   ROB 的 o1（1.16×，`rob.usedSum` 1.33×）。
3. **top-1 Auto 臂明显更高的结构**：mult（e2 0.99× 持平、v2 0.68×）、
   fpadd（f1 0.56×）、L1D 的 l1/l2/c3/m3/v4（0.13×–0.46×）、
   L1I 的 i2（0.57×）、ROB 的 o2（0.14×）。
4. **指标归一化会改变结论。** ACE 的 `aceRatio` 是“bit-cycles / (容量×周期)”，
   运行更快的模板可以有更高的 ratio、但绝对 bit-cycles 更低：
   v1 `vecAceRatio` 模板 3.09×，而 `vecAceBitCycles` 仅 0.79×；
   v3 `intAceRatio` 模板 2.29×，而 `intAceBitCycles` 仅 0.33×。
   因此本报告同时给出 ratio 与绝对量，不把单一名次当作结论。
5. **D13 对 ACE/IBR/SAD 完全不可见。** 控制 harness 后，20/20 单元、
   153/153 个指标在 `auto-load`（x12=3，每组加载）与 `auto-D13`
   （x12 来自 D13 流）之间 **0 差异**；`D13/load = 1.000000`。
   D13 的“操作数定向”不能被这三族结构覆盖指标区分。
6. **短窗口不足以测 ACE/SAD。** 单次执行的模板 ROI 只有 14–201 条指令，
   c1/l1/l2 的 `aceLineCycles` 为 0（line lifetime 未在窗口内结束），
   SAD 采样窗口在 4096 预算下为 ACE 窗口的 70.0%–98.5%（中位 89.0%），
   单次执行更差（18.4%–81.8%，中位 29.8%）；两种协议均 0/80 行一致。
   所以主对比用 4096 预算；单次执行只作忠实性/敏感性检查（§3.4）。

## 1. 问题与可测边界

用户要求：对 20 条手工模板逐条做等量 AutoµSens 生成，在 gem5 上比对**目标
结构的全部相关覆盖度指标**，然后加入 D13 进一步比对。

本构建的可测边界（实测，非推测）：

| 结构/意图 | 是否有直接计数器 | 本实验的处理 |
|---|---|---|
| RF、vec、L1D、L1I、6 类 FU（int/FP） | 有 | 直接测量 |
| L2、L3 | 无 | 用 L1D ACE 作代理，标注 `proxy` |
| TLB/PTW | 无 | 用 L1D ACE + SAD LQ 作代理，标注 `proxy` |
| BPU/分支预测 | 无 | 用 L1I ACE + SAD IQ/ROB 作代理 |
| crypto/AES/SHA/CRC | 无 | 用 vec ACE + SAD vecPRF 作代理 |
| ROB/IQ/LQ/SQ/PRF/FU 占用 | SAD 有 | 直接测量 |
| 128-bit 向量 FMLA | 标量 `fuIbr.fpMult` 不计数 | v1 改用 vec ACE，明确标注 |

`l1i` 被 AutoµSens 显式判为**不可靶向**（cache-line 粒度低于阈值）；
对 i1/i2，Auto 臂生成 `alu` 流，L1I 只作为被测量结构。因此 i1/i2 是
“生成代理 + 测量目标”混合单元，不能读成“Auto 正面对 L1I 靶向”。

## 2. 实验设计

### 2.1 模板臂

上游模板是完整探针程序，不是可重复的单条 body。wrapper 用 mmap 复现上游初态：

- `x6=0x7_0000_0000`、`x7=0x1007_0000_0000`（各 4 MiB，零填充）
- `sp=0x200_1000`，其余 GPR 清零
- `m5_work_begin(7,0)` 只包住探针；wrapper 初始化在 ROI 外
- 探针末尾追加 `ret`，由 wrapper 走 Linux `exit(0)`；异常落空走 `exit(86)`

**单次执行（one-pass）**：每条模板执行一次，保留上游程序形态。用于
“忠实执行”检查。

**4096 预算（主实验）**：模板程序在同一个 work item 内重复 K 次，
`K` 由实测 ROI 迭代校准（最多 4 次，目标 4096±8%），循环计数器使用
`x29`（20 条模板均未使用 x29），避免循环计数器本身制造 L1D 访问。
这会使后续 pass 带前一次残留架构状态并预热 cache/TLB；这是为拿到有效
ACE/SAD 窗口付出的代价，one-pass 结果单独披露。

### 2.2 AutoµSens 臂

- 目标结构 = 模板映射到的可靶向结构（§2.3）
- 选择 = 工具 top-1 模式，body = 该模式重复 4 次（`OPS_PER_GROUP`）
- 主实验：`iterations=60`，`groups=16` → 3840 条 body 指令 + 循环控制，
  ROI 实测 3977–3985 条
- `auto-load` 控制：同一 body/G，但每个 iteration 从常量表加载 `x12=3`
- `auto-d13`：同一 body/G，每个 iteration 从 D13 逐 bit 复现流加载一个 x12
  （`experiments/autousens/d13.py`，`operand_stream(60)[:60]`）
- 所有 Auto guest 都带 `sdcfuzz/target_oracle.py` 的独立 checksum，
  运行必须 `status=PASS`

`auto-default`（不加载）用于模板 vs Auto 的主对比；
`auto-load` 是 D13 的**同结构控制**；`auto-d13` vs `auto-load` 才是
“只改操作数、不改指令结构”的 D13 效应。

### 2.3 20 条模板的映射

| seed | 模板标称结构 | 测量结构 | Auto 生成结构 | 类型 |
|---|---|---|---|---|
| c1_l2_eviction | L2 | l1d | l1d | proxy |
| c3_l3_128b | L3 | l1d | l1d | proxy |
| e1_carry_chain | ALU | alu | alu | direct |
| e2_mul_extreme | multiplier | mult | mult | direct |
| e3_toggle_rate | ALU | alu | alu | direct |
| f1_subnormal_nan | FSU | fpadd | fpadd | direct |
| i1_icache_boundary | L1I | l1i | alu | proxy |
| i2_branch_dense | BPU/L1I | l1i | alu | proxy |
| l1_disambig | LSU | l1d | l1d | direct |
| l2_dualagu_split | LSU | l1d | l1d | direct |
| m1_tlb_thrash | TLB | l1d | l1d | proxy |
| m3_cross_page | MMU+LSU | l1d | l1d | proxy |
| o1_rob_full_wakeup | ROB | rob | l1d | proxy |
| o2_mispredict_rollback | BPU/PRF | rob | alu | proxy |
| v1_fsu_vdroop | 128-bit FMLA | vec | vec | proxy |
| v2_alu_complex_saturation | ALU+complex | mult | mult | direct |
| v3_prf_mispredict | PRF | rf | rf | direct |
| v4_lsu_cross_boundary | LSU | l1d | l1d | direct |
| v5_lse_cross_die | LSE/LSU | l1d | l1d | direct |
| v6_crypto_toggle | crypto/vector | vec | vec | proxy |

映射原则：优先用模板头注释的标称结构；标称结构无计数器或不可靶向时，
用最近的**可测**结构作代理，并在表中和结果里保留 `proxy` 标记。

### 2.4 两处 harness 混淆（已发现并修正）

预实验的数据在发现以下两点后作废重跑；最终数据全部来自修正后的 harness。

**(a) `--cmd` 路径长度改变 SE 初始栈。** gem5 SE 把 argv/env 放在初始栈；
`--cmd` 字符串长度不同会移动栈顶，改变 ROI 前的 cache 预热。实测同一个
l1d Auto guest，仅因 `--cmd` 路径不同，得到 **1895 vs 1930 cycles、
4308 vs 5254 lineCycles**。修正：把 guest 复制到 run 目录，固定
`cwd=run`、`--cmd=guest`（所有单元 argv[0] 都是 `guest`），并移除
`PWD/OLDPWD` 环境变量。

**(b) 期望 checksum 的立即数改变 ROI 前代码。** `const uint64_t expected =
UINT64_C(0x...)` 的 movz/movk 条数随常数变化；D13 改变了 checksum，于是
ROI 前的指令数和前端状态不同，污染 D13 vs load 对比。修正：
`static volatile const uint64_t expected_storage = ...` + 运行时加载，
使代码逐指令相同、只有数据值不同。

两处修正后，同一个 l1d body 的 `auto-load` 与 `auto-d13` 的 153 个指标
逐项相同；这也解释了为什么预实验中看到的“D13 差异”不能归因于操作数。

### 2.5 D13 为什么没有模板臂

静态扫描 20 条模板的 x12 首次访问：16 条在第一次访问时就是写
（`mov/add/eor/ldr` 或 `LOAD_*` 宏），4 条完全不提 x12
（f1/i1/i2/o2）。**没有任何模板在写之前读 x12**，因此 D13 的 x12
注入无法进入固定模板体；给模板加“D13 预加载”只会多一条 load，
不是 D13 变体。本实验不构造这个伪单元，而是在报告里明确这一边界。

## 3. 结果

### 3.1 4096 预算：头号指标

ROI 指令数：模板 3783–4101，Auto 3977–3985，auto-load/auto-D13
4119–4139。所有 Auto `status=PASS`，模板 exit 0，无 fatal/panic。

| seed | 目标指标 | 模板 | Auto | Auto+D13 | T/A | 胜方 |
|---|---|---:|---:|---:|---:|---|
| c1_l2_eviction | ace.l1d.aceRatio | 0.00179101 | 0.00087753 | 0.00249371 | 2.041 | 模板 |
| c3_l3_128b | ace.l1d.aceRatio | 0.00021192 | 0.00087753 | 0.00249371 | 0.2415 | Auto |
| e1_carry_chain | ibr.intAlu.ibrRatio | 0.398411 | 0.151241 | 0.140464 | 2.634 | 模板 |
| e2_mul_extreme | ibr.intMult.ibrRatio | 0.159648 | 0.161509 | 0.159910 | 0.9885 | Auto（持平） |
| e3_toggle_rate | ibr.intAlu.ibrRatio | 0.373075 | 0.151241 | 0.140464 | 2.467 | 模板 |
| f1_subnormal_nan | ibr.fpAdd.ibrRatio | 0.0665381 | 0.118475 | 0.116859 | 0.5616 | Auto |
| i1_icache_boundary | ace.l1i.aceRatio | 0.00753691 | 0.00626713 | 0.00615385 | 1.203 | 模板 |
| i2_branch_dense | ace.l1i.aceRatio | 0.00359943 | 0.00626713 | 0.00615385 | 0.5743 | Auto |
| l1_disambig | ace.l1d.aceRatio | 0.00011553 | 0.00087753 | 0.00249371 | 0.1317 | Auto |
| l2_dualagu_split | ace.l1d.aceRatio | 0.00012912 | 0.00087753 | 0.00249371 | 0.1471 | Auto |
| m1_tlb_thrash | ace.l1d.aceRatio | 0.00177604 | 0.00087753 | 0.00249371 | 2.024 | 模板 |
| m3_cross_page | ace.l1d.aceRatio | 0.00030051 | 0.00087753 | 0.00249371 | 0.3424 | Auto |
| o1_rob_full_wakeup | sad.rob.ratio | 0.181833 | 0.157014 | 0.209513 | 1.158 | 模板 |
| o2_mispredict_rollback | sad.rob.ratio | 0.0711263 | 0.499767 | 0.510868 | 0.1423 | Auto |
| v1_fsu_vdroop | ace.rf.vecAceRatio | 0.0320913 | 0.0104019 | 0.0104014 | 3.085 | 模板 |
| v2_alu_complex_saturation | ibr.intMult.ibrRatio | 0.109904 | 0.161509 | 0.159910 | 0.6805 | Auto |
| v3_prf_mispredict | ace.rf.intAceRatio | 0.0569556 | 0.0248859 | 0.0361603 | 2.289 | 模板 |
| v4_lsu_cross_boundary | ace.l1d.aceRatio | 0.00040032 | 0.00087753 | 0.00249371 | 0.4562 | Auto |
| v5_lse_cross_die | ace.l1d.aceRatio | 0.00189565 | 0.00087753 | 0.00249371 | 2.160 | 模板 |
| v6_crypto_toggle | ace.rf.vecAceRatio | 0.00812357 | 0.0104019 | 0.0104014 | 0.7810 | Auto |

**按结构聚合（头号指标，中位 T/A）**

| 结构 | n | 头号指标 | 模板胜 | Auto 胜 | 中位 T/A |
|---|---:|---|---:|---:|---:|
| alu | 2 | ibr.intAlu.ibrRatio | 2 | 0 | 2.551 |
| mult | 2 | ibr.intMult.ibrRatio | 0 | 2 | 0.834 |
| fpadd | 1 | ibr.fpAdd.ibrRatio | 0 | 1 | 0.562 |
| l1d | 8 | ace.l1d.aceRatio | 3 | 5 | 0.399 |
| l1i | 2 | ace.l1i.aceRatio | 1 | 1 | 0.888 |
| rob | 2 | sad.rob.ratio | 1 | 1 | 0.650 |
| rf | 1 | ace.rf.intAceRatio | 1 | 0 | 2.289 |
| vec | 2 | ace.rf.vecAceRatio | 1 | 1 | 1.933 |

### 3.2 ratio 与绝对量：不要只读一个数

ACE 的 ratio 是周期归一化的；模板通常执行更快，因此“每周期占比”高不等于
“绝对结构工作量”高。下面这些成对数字是本报告最重要的限制：

| 单元 | ratio（模板/Auto） | 绝对量（模板/Auto） | 解释 |
|---|---|---|---|
| v1_fsu_vdroop | `vecAceRatio` 3.085 | `vecAceBitCycles` 0.791 | 模板快 3.9×；每周期占比高，总 bit-cycles 反而低 |
| v3_prf_mispredict | `intAceRatio` 2.289 | `intAceBitCycles` 0.334 | 同上；模板 1736 vs Auto 11891 cycles |
| e1_carry_chain | `intAlu.ibrRatio` 2.634 | `intAceBitCycles` 0.478 | IBR 是每 op 指标，ACE 是周期归一化 |
| e3_toggle_rate | `intAlu.ibrRatio` 2.467 | `intAceBitCycles` 0.534 | 同上 |
| i1_icache_boundary | `l1i.aceRatio` 1.203 | `trackedDemandReads` 9.214；`sad.iq.ratio` 0.00078 | 模板是取指受限；L1I 高、IQ 几乎不占 |
| o1_rob_full_wakeup | `sad.rob.ratio` 1.158 | `sad.rob.usedSum` 1.333 | 模板在 ROB 两项都高，但 IQ 0.710 |
| c1_l2_eviction | `l1d.aceRatio` 2.041 | `aceLineCycles` 2.659 | 模板触及更多不同 line，line 寿命更长 |
| m1_tlb_thrash | `l1d.aceRatio` 2.024 | `aceLineCycles` 2.686 | 同上 |
| v5_lse_cross_die | `l1d.aceRatio` 2.160 | `aceLineCycles` 23.06 | LSE 原子操作极慢（模板 16634 cycles），line 寿命很长 |

因此本报告**不**给出“模板覆盖更好/更差”的总排名；每个结构、每种指标
（ratio vs 绝对量）都要分开读。完整 60 行目标指标见
`target_metrics.csv`（每行一个 seed×arm，含所有焦点字段）。

### 3.3 D13 对比

控制 `auto-load`（x12=3，加载）与 `auto-d13`（x12 来自 D13）后：

- **20/20 单元、153/153 个指标、3060 次逐项比较：0 差异**
- `D13/load = 1.000000`（每个单元）
- `simInsts`、`cycles`、ACE/IBR/SAD 计数、ratio、派生量全部逐位相同
- 所有 Auto 仍 `status=PASS`；D13 的独立 oracle 校验通过

结论：**D13 的操作数选择对 ACE/IBR/SAD 完全不可见**。这三族指标度量的是
结构事件/占用，不是数据值；D13 若要证明价值，必须用值敏感指标
（翻转率/功耗）或故障注入结局，不能用本实验的覆盖度层。

### 3.4 单次执行 vs 4096 预算

单次执行（one-pass）保留上游程序形态，但窗口太短：

- ROI 指令数 14–201；`aceLineCycles` 在 c1/l1/l2 模板上为 0
  （line 在窗口内没有结束），DRAM/L1 行为未进入稳态
- SAD 采样只有 ACE 窗口的 18.4%–81.8%，中位 29.8%；80/80 行
  `window_consistent=false`
- 例：e1 ALU IBR 单次 0.0205 → 预算 0.3984（模板）、0.0204 → 0.1512（Auto）；
  c1 L1D ACE 单次 0 → 预算 0.00179；v1 vec ACE 0.00965 → 0.0321

单次执行只用于“忠实性/敏感性”检查：它说明短窗口会把比率压到接近 0，
不能拿来做 ACE/SAD 结论。主对比一律用 4096 预算。

## 4. 解释

**模板在 ALU 上更高（e1/e3）**：模板包含多条可并行/半独立的整数操作、
多种操作数构造，`intAlu` 每周期输入位更高；Auto top-1 `add` body 是
`x8 += x12` 的单链，受 RAW 依赖限制，ALU 吞吐上不去。IBR 是每 op 的
结构指标，这个差异不是“跑得久”造成的。

**Auto 在 mult/fpadd 上更高（e2/v2/f1）**：Auto body 是单一目标指令
（`madd`/`fmul`/`fadd`）的高密度重复，模板要把指令预算花在 setup、
验证锚点和多种操作上。e2 的 IBR 几乎持平（0.9885），但模板的
`sad.fu.ratio` 是 Auto 的 8.62×——说明“乘加端口占用”与“IBR 输入位”
不是同一个维度。

**L1D 分裂（3/8 模板胜，5/8 Auto 胜）**：模板 c1（L2 set 冲突）、
m1（TLB/多页）、v5（LSE 原子）制造了多个不同 line 的长寿命
（`aceLineCycles` 2.7×/2.7×/23×），所以 `aceRatio` 更高；
l1/l2/m3/v4/c3 的访问集中在少量 line 或很快结束，Auto 的
高频 `ldr` 反而有更高的每周期 line 占用（0.13×–0.46× 模板/Auto）。
这不是“Auto 更懂 cache”，而是**单行重复**与**多行/多页足迹**的差别。

**i1 vs i2**：i1 是取指边界模板，模板 `trackedDemandReads` 是 Auto 的
9.21×，L1I ACE 1.20×，但 `sad.iq.ratio` 只有 Auto 的 0.00078×——
它把时间花在取指停顿上，而不是填满指令窗口。i2 分支密集但 Auto 的
紧凑循环在 L1I 上更高（0.574× 模板/Auto）。两者不能互相替代。

**v1/v3 的 ratio 反转**：模板更快（v1 2077 vs Auto 8103 cycles；
v3 1736 vs 11891），所以周期归一化的 ACE ratio 高；但绝对
`aceBitCycles` 更低。若目标是“每周期占用”，模板赢；若目标是
“总结构工作量”，Auto 赢。报告同时给出两者。

**D13 为什么为零**：`intAlu` IBR 的输入位按端口×宽度计，`ldr` 的行寿命
按地址/时间计，SAD 按占用计；这些都不读取操作数的具体 0/1 值。D13 改变
x12 的值，但不改变指令数、地址、寄存器读写次数或行生命周期，因此三族
指标逐位不变。这不是“D13 无效”，而是“这三族指标不是 D13 的度量”。

### 4.1 ACE/IBR/SAD 在 AutoµSens 选择中的实际角色

| 指标族 | 是否参与选择 | 具体位置 | 作用 |
|---|---|---|---|
| ACE（RF/vec） | **是** | `COUNTERS.rf_reads/writes、vec_reads/writes` → `activation_from_net` → `STRUCTURE_MAP.activation_per_instruction` → `rank_for_structure`/`target`/`pareto` | 选最高激活指令、排序、代理目标 |
| L1 ACE（l1d/l1i） | **是**（l1i 只测不靶向） | `l1d_reads/writes、l1i_reads` 同上 | 同上 |
| IBR（6 类 FU） | **是** | `alu_bits/mult_bits/div_bits/fpadd_bits/fpmul_bits` 同上 | 同上 |
| SAD（ROB/IQ/LQ/SQ/PRF/FU） | **否** | `--sad` 时写入 map 的 `sad` 字段和 `target`/`pareto` 报告；`rank_for_structure`、`target` 的 `chosen`、`pareto` 的 `objective` 都不读它 | 只做评估/协变量，不做选择 |

关键点：**ACE/IBR 参与的是“单条片段在隔离运行中的每指令净激活”代理**，
不是“拼接后序列在 gem5 中的实测 ACE/IBR/SAD”。`pareto` 的目标函数也是
各结构上单指令归一化激活的均值，不读序列级实测值。SAD 连代理选择都不进。
因此路线文档 §5.1 写的 `coverage(P,s_i)` 目前只落实为单指令可加代理，
没有落实为序列级 ACE/IBR/SAD 反馈。

这些指标并非无用，它们承担了四件事：

1. **选择信号**：ACE/IBR/L1 ACE 是 `STRUCTURE_MAP` 和 `target` 排序的
   唯一测量基础；
2. **评估/证伪**：对我们的 20 模板对比，ACE/IBR/SAD 是实际判据，揭示了
   “top-1 单模式在 ALU/L1D 上并不占优”这一事实；
3. **安全护栏**：候选运行后检查目标结构净激活是否 >0、基线是否被扣干净，
   防止代理排名与实际相反；
4. **后续闭环的测量层**：路线文档 §5.2 的 RL 状态需要 ACE/IBR/SAD；但这些
   指标目前没有回灌到 AutoµSens 的生成/拼接循环。

### 4.2 路线文档要求 vs 当前实现

路线文档 `sdcfuzz/sdcfuzz-v1.2.md` §5.1 的原文要求是：

- 在 gem5 上执行指令，建 `STRUCTURE_MAP[指令] → {结构:激活向量}`；
- 给定目标结构 $s$，**选取对 $s$ 激活最高的指令子集**，用 Microprobe 约束
  保证 ISA 合法，得到候选序列；
- 跨结构联合优化：最大化 $\sum w_i·coverage(P,s_i)$，在 ISA 合法、确定性、
  seccomp 兼容约束下，用 **NSGA-II 或加权聚合**生成 **Pareto 最优序列集**；
- 用 **ACE/IBR/SAD** 做结构覆盖度评估；
- 预期目标是“自动生成任意结构靶向序列并探索跨结构组合”，相对 19 模板
  实现自动化和优化升级。

当前实现与差距：

| 文档要求 | 当前实现 | 差距 |
|---|---|---|
| 指令→结构映射 | `map` 只覆盖 16 条片段 × 9 结构 | 不是“每条 ARM64 指令”；l1i 不可靶向；L2/L3/TLB/ROB 无靶向 |
| 选最高激活子集 | `target` 贪心 top-k | 每个入选模式固定 4 槽，不按激活大小分配，也没有多样性目标 |
| 跨结构 NSGA-II/加权 | `target` 加权贪心；`pareto` NSGA-II | `pareto` 目标是单指令可加代理，不是实测序列级 `coverage(P,s_i)` |
| Microprobe ISA 约束 | 本地 `MicroprobeConstraints` | 无 upstream Microprobe；规则是本地替代 |
| 确定性、seccomp 兼容 | ISA/确定性有部分检查；seccomp 无实现 | 文档写了约束，代码未落实 seccomp |
| Pareto 序列集 | `pareto` 输出 Pareto 集 + knee | 只可选 `--validate` 验 knee；无多样性/顺序指标，无实测反馈闭环 |
| ACE/IBR/SAD 评估 | `metrics.py`/`coverage_report` 有全字段 | 评估有，但**没有回灌选择**；SAD 不参与选择 |
| 超越手工模板 | 路线图的预期目标 | 本实验只测 top-1，不能证实/证伪；需多模式/Pareto 实验 |

路线文档没有规定、当前实现也没有解决的**操作性细节**包括：

- 每种入选指令分配多少条（配额/多样性），而不是固定 4 条；
- 指令之间的拼接顺序、依赖链、端口冲突、cache line 复用、分支行为；
- 序列级多样性度量（模式覆盖、位置/ngram、Pareto 集内多样性）；
- 用实测 ACE/IBR/SAD 做 Gen→Eval→Mutate 的反馈；
- SAD 如何进入 `coverage(P,s)` 目标。

关于“顺序有影响”：仓库已有的 E2 顺序实验只在 **16 条单指令片段库**内
测得组内方差占比 rf=0、l1d=2.51×10⁻⁵、alu=3.53×10⁻⁶，报告明确写了
“仅限该片段库，不外推到依赖链/别名/跨行访问”。本实验的 top-1 根本没有
顺序可变项，因此**不能用它证明顺序无关**，也不能用它证明 AutoµSens 的
多模式顺序设计无效。

## 5. 边界

- **无统计推断**：每个单元 1 条确定性流；Auto 每个结构只有 1 条流
  （20 个模板共享），不是独立样本。没有 CI、没有显著性检验。
- **模板循环不是单次执行**：4096 预算重复模板，后续 pass 带残留架构状态
  并预热 cache/TLB。模板循环长度已校准到 3783–4101 条，但不能把结果
  读成“上游模板单次执行的覆盖率”。单次执行结果单独给出。
- **代理结构**：L2/L3/TLB/BPU/crypto 没有直接计数器；i1/i2 的 Auto 生成
  结构是 `alu`，不是 L1I；v1/v6 的 Auto 是标量 FP/vec，不是 128-bit
  crypto/FMLA。
- **v1 的 128-bit FMLA 不被标量 `fpMult` IBR 计数**（模板
  `ibr.fpMult.ibrRatio=0`）；v1 改用 vec ACE，不能与“标量 fpMult”对比。
- **SAD 窗口**：ACE/IBR 的 `measuredCycles` 与 SAD `samples` 不一致
  （4096 预算中位 89.0%，单次执行中位 29.8%；所有行
  `window_consistent=false`）；SAD ratio 只能作同窗口趋势，不是与 ACE
  严格同域的绝对量。
- **无故障注入**：本实验只测覆盖度，不测 SDC 检出率、不注入故障、
  不声称 AutoµSens/D13 的 SDC 优势。
- **D13 只作用于 Auto 臂**：模板的 x12 首次访问全是写或不存在，
  D13 的 x12 注入无法进入固定模板体；模板/D13 单元被明确列为不适用，
  没有伪造。

## 6. 复现

```bash
cd /home/sdc/sdc-mhw
# 单次执行（忠实性/敏感性）
python3 experiments/autousens/u20_templates.py --run-id 2026-11-17-u20-fixed --workers 8
python3 experiments/autousens/u20_templates.py --verify 2026-11-17-u20-fixed

# 4096 预算（主实验）
python3 experiments/autousens/u20_budget.py --run-id 2026-11-17-u20-budget-fixed --workers 8
python3 experiments/autousens/u20_budget.py --verify 2026-11-17-u20-budget-fixed

# 分析表
python3 experiments/autousens/u20_analyze.py \
  --one-pass m5out/autousens-eval/2026-11-17-u20-fixed/summary.json \
  --budget m5out/autousens-eval/2026-11-17-u20-budget-fixed/summary.json \
  --outdir m5out/autousens-eval/2026-11-17-u20-budget-fixed/analysis
```

产物：

| 文件 | 内容 |
|---|---|
| `.../2026-11-17-u20-budget-fixed/summary.json` | 20 单元 × 4 臂 + 全部 flat 指标 |
| `.../metrics.csv` | 80 行 × 165 列（12 元数据 + 153 个指标） |
| `.../tables.md` | 头号指标、聚合、窗口审计 |
| `.../analysis/d13_audit.csv` | D13 vs load 的逐单元审计 |
| `.../analysis/target_metrics.csv` | 每个目标结构的焦点字段 × 4 臂 |
| `.../analysis/sensitivity.csv` | 单次执行 vs 4096 的主指标 |
| `.../2026-11-17-u20-fixed/` | 单次执行全量产物 |

## 7. 结论

1. **top-1 单模式 Auto 臂不是手工模板的全面替代**：在等执行预算下，它在
   mult/fpadd/ROB/部分 L1D 上更高，但在 ALU IBR、L1D 多行足迹
   （c1/m1/v5）、L1I 取指边界（i1）、ROB（o1）上低于手工模板。
   这个结论**只适用于 top-1 退化基线**，不能外推到路线文档 §5.1 的
   多模式/Pareto 序列集。
2. **覆盖度是向量，不是标量**：同一单元在 IBR、ACE ratio、ACE 绝对
   bit-cycles、SAD 占用上可以给出相反名次（v1/v3 最明显）。任何
   “Auto 更好/模板更好”的单句结论都必须带上指标与归一化口径。
3. **D13 在本实验的覆盖度层没有可测收益**：控制 harness 后 20/20 单元、
   153/153 指标 0 差异。D13 的价值需要值敏感指标或故障注入来证明，
   不能用 ACE/IBR/SAD 冒充。
4. **方法学教训**：SE 的 `--cmd` 路径长度和 checksum 立即数都会改变
   ROI 前的栈/代码布局，足以制造 2%–6% 的假差异和假的 D13 效应。
   固定 argv、把 checksum 常量改为 volatile 数据加载，是复现这类
   gem5 对比的最低要求。
5. **路线文档与实验的范围差距**：§5.1 要求“最高激活子集 + 跨结构
   NSGA-II/加权 → Pareto 序列集 + ACE/IBR/SAD 评估”，本实验只测了
   `target --top 1`。要回答“AutoµSens 是否应优于手工模板”，必须补
   top-2/3、`pareto --length L`、顺序消融、序列级 ACE/IBR/SAD 反馈
   和多样性度量；现有数据既不支持也不否定该路线。
