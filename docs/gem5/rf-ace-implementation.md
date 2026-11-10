# gem5 O3 整数与向量/FP 物理寄存器 RF ACE 实现说明

## 1. 目标与论文语义

本实现用于在 gem5 O3 CPU 中度量 Harpocrates 使用的寄存器文件 ACE
生命周期覆盖率。论文把位阵列中的 ACE 定义为：某一存储位在某周期发生
瞬态翻转时，错误可能影响架构正确执行。对寄存器文件，相关区间为
write-to-read 和同一值多消费者形成的 read-to-read 区间；覆盖率是 ACE
bit-cycle 占全部可用 bit-cycle 的比例。ACE 是实际故障检出率的上界代理，
不是 SDC 检出率。

bit 模式的非访存整数源宽度由 ARM operand 定义生成，使用源操作数索引查表，
不再把目的宽度应用到所有源。例如 `SMADDL Xd,Wn,Wm,Xa` 的三个源分别
按 32、32、64 位读取；同一物理寄存器出现在不同宽度的源位置也分别处理。

当前实现提供两种粒度。默认 `whole` 保留原有整寄存器模型；`bit` 为每个
物理 GPR 保存 64 位 live/read 掩码和逐位生命周期。AArch64 W 源读取低
32 位，X 源读取 64 位。W 写遵循 AArch64 零扩展语义，仍定义完整 64 位
物理寄存器；只有随后真正读取的位进入 `intAceBitCycles`：

```text
intAceRatio = intAceBitCycles
            / (numPhysIntRegs * rfAceRegWidthBits * measuredCycles)
```

同一 tracker 还跟踪 ARM 的向量/FP 物理寄存器（`VecRegClass`），用于
`fp-add`/`fp-mul` 等模板的寄存器覆盖证据。向量寄存器按 **低 64 位 lane**
建模：标量 D 运算、`FMOV D`、`LDR/STR D` 是精确的；128 位 SIMD 只覆盖
低 64 位，不虚报高 64 位。FP 标量读宽度按编码 type 位（23:22）取
S=32 / D=64 / H=16。向量值不从“ROI 前已存在”的 live-in 推断生命周期：
只有 ROI 内发生写之后，读才进入 ACE；这避免释放后重读造成的重复计数。

```text
vecAceRatio = vecAceBitCycles
            / (numPhysVecRegs * 64 * measuredCycles)
```

## 2. 实现位置

核心跟踪器位于：

- `CHAOS/gem5/src/cpu/o3/rf_ace.hh`
- `CHAOS/gem5/src/cpu/o3/rf_ace.cc`

事件接入点：

1. `dyn_inst.hh`：记录整数物理源寄存器真实读取周期和目的寄存器真实写回周期。
   FP/向量指令通过 `getWritableRegOperand` 原地写入，该路径也登记
   `VecRegClass` 目的写，因此向量 ACE 同时看到读和写。
2. `commit.cc`：只有指令成功提交后，才确认此前记录的读写事件。
3. `rename.cc`：分支恢复时丢弃年轻指令的候选事件；物理寄存器归还 free
   list 时结束当前值的生命周期。
4. `pseudo_inst.cc` / `BaseCPU`：把 m5 work-item ID 传给 O3 CPU，用于隔离
   初始化、封装、签名和输出代码。

stdlib 的 `Simulator` 会用 `exit_on_work_items` 把 marker 转换为
`WORKBEGIN/WORKEND` 退出事件。核心伪指令路径通过独立 CPU marker 钩子先通知
O3 跟踪器，再产生退出事件，避免事件驱动模式绕过跟踪器；原有 BaseCPU/System
work-item 统计的调用位置保持不变。默认 `WORKBEGIN` handler 随后执行 stats
reset；跟踪器会保留已打开的 ROI，并把重置周期作为新的精确起点。

不能在执行钩子直接累加 ACE。年轻指令可能已经读写物理寄存器，随后才因老
分支误预测被 squash。实现以 `(ThreadID, InstSeqNum)` 暂存事件，commit 时
确认、squash 时删除，因此错误路径的生产者和消费者不会增加 ACE。

同一值的多个已提交消费者可能乱序执行。跟踪器保存最后一次实际读取周期：
从写入到最后读取的跨度，等于论文所述 write-to-read 加后续 read-to-read
区间之和，并且不依赖消费者的提交顺序。未被读取就覆盖或释放的值只增加
drop 计数，不增加 ACE。

## 3. 配置

所有参数属于 `BaseO3CPU`，默认 `rfAce=False`，因此普通仿真不启用探测：

| 参数 | 默认值 | 含义 |
| --- | ---: | --- |
| `rfAce` | `False` | 启用 RF ACE |
| `rfAceUseWorkItems` | `False` | 使用第一个匹配的 m5 work-item ROI |
| `rfAceWorkItemId` | `-1` | 目标 work ID，`-1` 表示第一个 |
| `rfAceStartCycle` | `0` | 周期窗口起点 |
| `rfAceEndCycle` | `0` | 周期窗口的排他终点，`0` 表示仿真结束 |
| `rfAceBitGranularity` | `False` | 启用 AArch64 W/X bit 掩码模型 |
| `rfAceRegWidthBits` | `64` | 每个整数物理寄存器的建模位宽 |

`configs/se/arm_chaos.py` 提供命令行入口，例如：

```bash
--rf_ace --rf_ace_window=workitem --rf_ace_work_id=7
```

追加 `--rf_ace_granularity=bit` 启用 bit 模式；省略或设置为 `whole` 时使用
旧的整字模型，便于对同一 workload 前后对比。

或使用显式周期窗口：

```bash
--rf_ace --rf_ace_window=cycle \
  --rf_ace_start_cycle=10000 --rf_ace_end_cycle=20000
```

work-item 模式只测量第一次匹配的区域，边界为 `[work_begin, work_end)`。
ID 为 `-1` 时，第一个 begin 的实际 ID 会被锁定，其他 ID 的 end 不会提前
关闭该区域。
marker 本身、参数解析和 `work_end` 之后的输出不进入指标。
O3 的 non-speculative work marker 在 ROB 头执行。结束时使用实际 CPU
ThreadID 和该 marker 的指令序号，丢弃同线程尚未提交的 marker/年轻指令
候选事件，即使它们已在结束周期之前推测执行。所有 pseudo instruction
的寄存器访问均不参与 RF ACE。单线程测试要求 work-end 与程序退出时导出的
ACE 分子、读写次数和 ratio 完全相同；SMT 的其他线程仍按周期窗口采样，
其未提交事件可能在之后完成确认，因此不能把单线程快照保证推广到未同步的 SMT。

## 4. 输出指标

指标作为标准 gem5 statistics group 输出到 `stats.txt`，前缀随 CPU 对象路径
变化，末级名称固定为：

```text
*.rfAce.intAceRegCycles
*.rfAce.intAceBitCycles
*.rfAce.intAceBitCyclesLow32
*.rfAce.intAceBitCyclesHigh32
*.rfAce.intAceRatio
*.rfAce.bitGranularity
*.rfAce.intTrackedWrites
*.rfAce.intTrackedReads
*.rfAce.intSquashDiscards
*.rfAce.intOverwriteDrops
*.rfAce.vecAceRegCycles
*.rfAce.vecAceBitCycles
*.rfAce.vecAceRatio
*.rfAce.vecTrackedWrites
*.rfAce.vecTrackedReads
*.rfAce.vecSquashDiscards
*.rfAce.vecOverwriteDrops
*.rfAce.measuredCycles
*.rfAce.windowBegins
*.rfAce.windowEnds
```

`intTrackedReads/Writes` 只统计已提交指令。`intSquashDiscards` 统计已真实写回、
但最终被 squash 的错误路径整数目的寄存器写；该值不进入 ACE 分子。

## 5. 一键方向性验证

在仓库根目录运行：

```bash
./scripts/test-rf-ace.sh
```

脚本会在 x86-64 宿主机上增量构建启用 ARM ISA 的
`build/ARM_X86_HOST/gem5.opt`，再用 `aarch64-linux-gnu-gcc` 静态编译
`rf_ace_workload.c`，运行以下 AArch64 ROI：

1. `chain`：长整数依赖链，预期 ACE 高于死写流。
2. `dead`：4 个寄存器反复死写，预期较低 ACE。
3. `pressure`：8 个寄存器反复死写；更高寄存器压力不应超过依赖链。
4. `squash`：冷加载延迟分支解析，让预测错误路径上的寄存器指令先执行，
   要求 `intSquashDiscards > 0`，且这些写不进入 committed write 计数。
5. `width32`：用 W 操作数执行三条整数依赖指令。
6. `width64`：用 X 操作数执行同构的三条整数依赖指令。

脚本在 bit 模式断言 `width32 < width64`，并断言 W 流的高 32 位 ACE cycle
低于 X 流；在 whole 模式，两条流都按完整 64 位读取，ratio 差异不得超过
2%。这同时验证新模型对操作数宽度敏感、兼容模式保持原统计口径。

输出保存在 `m5out/rf-ace-test-arm/`，脚本从每个 `stats.txt` 读取真实指标并对上述
方向关系作硬断言，任一不满足即返回非零。脚本还逐场景从 bit-cycle、256 个
物理整数寄存器、64 位宽和测量周期重算 ratio，并检查其位于 `[0,1]`。此外
要求每个 ROI 恰好开始、结束
一次，测量周期和已提交写次数均非零，`bitGranularity` 与所选模式一致，且
low/high 32-bit cycle 之和等于总 bit-cycle。gem5 构建使用其原生
`--debug-fission --limit-ld-memory-usage` 选项，以降低 `gem5.opt` 的峰值链接
内存，不改变模拟行为。

本实现开发时的一次完整实测结果如下（具体数值会随微架构参数变化，验收只依赖
方向关系）：

```text
chain intAceRatio          = 0.02735228
dead intAceRatio           = 0.01581974
pressure intAceRatio       = 0.01572213
squash intSquashDiscards   = 152
bit width32 intAceRatio    = 0.02151393
bit width64 intAceRatio    = 0.02724970
bit width32 high32 cycles  = 7808544
bit width64 high32 cycles  = 13638272
whole width32 intAceRatio  = 0.02731471
whole width64 intAceRatio  = 0.02725137
```

## 6. 当前边界

额外正确性回归（需先构建 ARM target）：

```bash
python3 scripts/test-ace-ibr-correctness.py \
  --gem5 CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt
```

该回归比较 SMADDL/MADD 的高 32 位生命周期，并检查同一 ROI 在 work-end
与程序结束时的多次导出，避免只读取 `stats.txt` 最后一个同名值而掩盖污染。

- 整数覆盖 O3 CPU 的 `IntRegClass` 物理寄存器文件；向量/FP 覆盖
  `VecRegClass` 的**低 64 位 lane**。
- `whole` 模式会把被消费条目的全部配置位宽视为 ACE，仅用于兼容和对照。
- 当前 `bit` 模式区分 AArch64 整数 W/X 的读取宽度；整数写按 AArch64
  零扩展语义定义完整 GPR。内存指令暂按完整 GPR 保守建模，尚未区分地址源和
  store-data 源。
- 128 位 SIMD 高 lane、谓词和条件码寄存器不在当前向量 ACE 范围；标量
  S/H/D FP 与 D 寄存器访存已覆盖。
- ACE 是硬件覆盖/适应度代理；故障是否传播到程序输出仍需 SFI 单独验证。

论文依据：Harpocrates, ISCA 2024，第 II-D 节和图 3（ACE lifetime），以及
第 VI-B/VI-C 节（IRF 以 ACE 为优化反馈，ACE 是检测能力上界）。

## 7. 向量/FP ACE 实测（2026-11-10，原生 aarch64）

在 `sdc-0103` 的原生 `build/ARM/gem5.opt` 上运行 19 模板覆盖回归，
`fp-add`/`fp-mul` 的向量 RF ACE 真实输出（iterations=40）：

```text
fp-add: vec_reads=1284 vec_writes=646 vecAceRatio=0.01328022
fp-mul: vec_reads=1284 vec_writes=646 vecAceRatio=0.01400148
```

写计数来自 `getWritableRegOperand` 钩子；`vecAceRatio` 均在 `[0,1]` 内且
由 `vecAceBitCycles / (numPhysVecRegs * 64 * measuredCycles)` 逐项复核。
完整矩阵见 `m5out/coverage-matrix/coverage_matrix.json`。
