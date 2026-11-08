# gem5 O3 整数功能单元 IBR 监测

论文依据为项目内 [Harpocrates ISCA 2024 论文](../papers/ref/Harpocrates_Breaking_the_Silence_of_CPU_Faults_through_Hardware-in-the-Loop_Program_Generation.pdf)
第 II-D 节及脚注 5（PDF 第 4 页）：
Input Bit Ratio 是执行期间实际送入功能单元的有效输入位总数，除以该单元
在每个执行周期接收满宽输入时的理论最大位总数。它衡量输入端活动，
不是 popcount、不同输入值的数量、相邻值的 Hamming distance 或故障检出率。

## 实现范围与口径

核心位于 `CHAOS/gem5/src/cpu/o3/fu_ibr.{hh,cc}`。与 RF ACE 一样由 O3 CPU
持有跟踪器，默认关闭，使用既有 BaseCPU work-item marker 钩子。
唯一采样入口是 `inst_queue.cc` 中成功分配实际 FU 后的 issue 路径。
NoNeedFU、NoCapableFU、NoFreeFU 和已 squash 未发射的指令均不计入。
已经发射、之后被 squash 的指令确实使用了硬件，计入 IBR；不等到 commit。
多周期运算仅在接收输入时采样一次，不按执行延迟重复累加输入位。

当前监测 AArch64 整数算术输入端，按功能类别分别输出：

| 统计类别 | 支持的指令 | 输入端数量 | 每端最大位宽 |
|---|---|---:|---:|
| `intAlu` | add/sub、逻辑操作的立即数和寄存器编码，包括其别名 | 2 | 64 |
| `intMult` | 同宽 MADD/MSUB，包括 MUL/MNEG 别名 | 3 | 64 |
| `intDiv` | UDIV/SDIV | 2 | 64 |

有效输入宽度使用 ARM decoder 的 `getIntWidth()`：W 运算为 32，X 运算为 64。
这里建模的是完整数据输入端：立即数扩展后的操作数、零寄存器、MUL 中的
零加数也送入输入端，不按立即数字段长度或输入数值大小缩减宽度。
移位/扩展运算的端口按主运算宽度建模，不进一步分析较窄来源和逻辑屏蔽。
不统计指令编码、移位量、条件码等控制输入。其他 ALU 编码、长乘法、FP、
SIMD/SVE、访存、分支和 AArch32 不在本阶段范围；成功 FU issue 中这些
未建模指令增加 `excludedOps`，不伪造为满宽输入。因此这是一项明确范围的
数据端活动近似，不声称全 ISA 或门级精确覆盖。

每类分母从配置中的实际 FUPool 计算支持该类的物理单元数量；共享的 pool
只计算一次，多个 IQ 的不同 pool 则合计。支持多种类别的同一物理 FU 会
出现在各自类别分母中（例如 gem5 默认的乘除共享单元），所以各类别的
IBR 不可直接相加或平均为全 CPU IBR。

```text
inputBits[class]    = sum(inputPorts[class] * instructionWidth)
maxInputBits[class] = capablePhysicalUnits[class] * inputPorts[class]
                   * 64 * measuredCycles
ibrRatio[class]     = inputBits[class] / maxInputBits[class]
```

没有测量周期或对应 FU 数量为零时，ratio 为 0。非流水线单元的空闲/忙碌
周期同样属于分母；不会把理论每周期满输入的上限改成其最大 issue 速率。

## 配置与输出

BaseO3CPU 参数为 `fuIbr`、`fuIbrUseWorkItems`、`fuIbrWorkItemId`、
`fuIbrStartCycle` 和 `fuIbrEndCycle`。开关默认 False，work ID 默认 -1，
周期起止默认 0。ARM SE 配置提供对应入口：

```bash
--fu_ibr --fu_ibr_window=workitem --fu_ibr_work_id=7
--fu_ibr --fu_ibr_window=cycle --fu_ibr_start_cycle=100 --fu_ibr_end_cycle=200
```

work-item 模式只测第一次匹配 ROI；ID 为 `-1` 时锁定第一个 begin 的实际
ID，只有同 ID 的 end 才能结束窗口。周期模式使用 `[start, end)`；end=0
表示仿真结束。统计 reset 清除此前采样，但保留打开的 ROI，并从 reset
周期重新计时，与 ACE 保持一致。结束 ROI 后采样停止，输出代码不进入指标。
work-item 结束周期同样是排他边界。跟踪器保留当前周期的输入位、issue 数
和 excluded 数；若该周期稍后执行匹配的 end marker，会撤销这整个周期的
样本，避免 IQ 与 marker 的处理顺序让分子多算一个周期。错误 ID 的 end
不会撤销样本。ROI 内实际发生的推测 issue 仍按硬件活动计入，不能把这个
周期窗口解释为只统计 marker 之间的已提交指令。具体地说，结束 marker 执行
之前，乱序流水线可能已经发射了 marker 之后的一到数条指令（典型是输出代码
里的 64 位 MADD），它们会计入本 ROI。定向测试因此按“64000 条目标运算必须
逐条符合宽度公式、额外部分只能是整条 64 位 MADD”校验，并断言额外条数不
超过 issue 总数与 64000 的差；这既保留位宽公式的严格性，也不把推测发射
误报成测试失败。

标准 gem5 `stats.txt` 输出以下名称，CPU 路径由配置决定：

```text
*.fuIbr.inputBits::intAlu/intMult/intDiv
*.fuIbr.issuedOps::intAlu/intMult/intDiv
*.fuIbr.unitCount::intAlu/intMult/intDiv
*.fuIbr.maxInputBits::intAlu/intMult/intDiv
*.fuIbr.ibrRatio::intAlu/intMult/intDiv
*.fuIbr.excludedOps
*.fuIbr.measuredCycles
*.fuIbr.windowBegins
*.fuIbr.windowEnds
```

## 定向验证

```bash
./scripts/test-fu-ibr.sh
ISA_CONSTR_CCFLAGS=-g0 JOBS=1 ./scripts/test-rf-ace.sh
python3 scripts/test-ace-ibr-correctness.py \
  --gem5 CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt
```

第一个脚本构建 ARM target gem5 和静态 AArch64 workload，在 ARM 或 x86
宿主执行。构建默认单任务，降低 ARM 生成代码编译的峰值内存；可使用 `JOBS`
覆盖。脚本默认 `ISA_CONSTR_CCFLAGS=-g0`，只为 ISA 构造函数生成代码
省去 DWARF 调试信息，仍使用 O3 优化；该选项也可通过环境或 scons 参数指定，
不设置时普通构建行为保持原样。
内存较小的宿主还可设置 `ISA_EXEC_CCFLAGS=-g0`，为生成的指令执行代码
省去调试信息；验收构建同时设置两个选项并使用 `JOBS=1`。
`alu64/alu32/mul64/mul32/div64` 均在 ID=7 的 ROI 内运行，
每种流每次迭代含 64 条目标运算，输出确定性 result/expected/status。
`sparse` 在同样的 64 位加法流中插入 NOP，验证输入端利用率下降时 IBR
也下降。
脚本断言 64 位流输入位数和 IBR 高于同类 32 位流，乘/除的输入位数
与 issue 数满足精确位宽公式，各类归一化公式正确、ratio 在 [0,1]。
同时验证关闭、未匹配 work ID、默认 ID 下错误 end 不会提前关闭 ROI，以及
固定周期窗口；输出位于
`m5out/fu-ibr-test-arm/`。第二个脚本作为原有 RF ACE 回归。

### 实测结果（2026-10-06）

x86-64 宿主运行 ARM target `build/ARM_X86_HOST/gem5.opt`，静态 AArch64
workload，每个流 1000 次迭代。`./scripts/test-fu-ibr.sh` 实际通过全部
九个场景，guest 均输出 `status=PASS`：

| 场景 | 目标类别 IBR | 有效输入位 | ROI 周期 |
|---|---:|---:|---:|
| alu64 | 0.64570049 | 8321664 | 16781 |
| alu32 | 0.32794930 | 4225792 | 16778 |
| mul64 | 0.65978021 | 12288000 | 48501 |
| mul32 | 0.32991731 | 6144000 | 48497 |
| div64 | 0.04998664 | 8192000 | 640171 |
| sparse | 0.40660213 | 8322944 | 26653 |

ALU 输入位包含循环控制等 ROI 内支持的算术指令，因此略高于 64000 条
目标加法的输入位。乘法/除法场景各计 64000 条目标操作，符合每次输入
的位宽公式；除法未按 20 周期执行延迟重复累加。关闭与不匹配 ID 场景
的输入位、测量周期均为 0；固定 `[100,200)` 窗口实测为 100 周期。
这些值来自各场景 `stats.txt`，只适用于本次默认 O3 配置。

`ISA_CONSTR_CCFLAGS=-g0 JOBS=1 ./scripts/test-rf-ace.sh` 回归实际通过
chain、dead、pressure、squash 四个场景，guest 均为 PASS，无段错误。
对应 ACE ratio 为 0.02734596、0.01569511、0.01575109，squash discards
为 121。ARM target 构建成功，IBR 改动未引入编译告警；环境仍有原有的
tcmalloc、protobuf、capstone、libpng、HDF5 可选依赖提示。
