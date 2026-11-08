# gem5 classic L1 cache ACE 实现说明

本实现参照整数物理寄存器 RF ACE 的生命周期统计，为 classic L1I/L1D
增加 cache-line 粒度的 ACE 指标。一个 line 在填充或需求写后开始新的值生命
周期；只要该值随后被需求读使用，从写入到最后一次需求读之间的 line-cycle
计入 ACE。替换、失效或再次写入会结束当前生命周期。

当前实现是 line-granularity 近似：一条 line 被消费时，整条 line 的位宽都被
视为 ACE，不追踪部分 store、load byte mask 或单条指令在 cache line 内的精确
位范围。classic cache 看到的是微架构需求请求，因此推测路径请求也可能进入
统计；该指标用于测试生成的覆盖反馈，不等同于 bit-accurate AVF。

需求访问钩子同时覆盖普通加载/写入、LL/SC 和 Swap/AMO。gem5 的
`isDemand()` 不包含后两类，因此不能用它作为唯一入口。成功的 STXR
结束旧生命周期；失败的 STXR 不产生写事件。conditional-swap 和 ARM
LSE CAS/CASP 只在比较成功、实际写入时产生写事件；成功写入相同数值仍是
一次写。Swap/AMO 在修改数据之前记录旧值的读取，
再为写入启动新生命周期。

## 参数

`BaseCache` 新增以下参数，默认全部关闭，不影响普通仿真：

| 参数 | 默认值 | 含义 |
|---|---:|---|
| `l1Ace` | `False` | 启用 L1 ACE |
| `l1AceUseWorkItems` | `False` | 使用 m5 work-item ROI |
| `l1AceWorkItemId` | `-1` | 目标 work ID，`-1` 表示第一个 |
| `l1AceStartCycle` | `0` | 周期窗口起点 |
| `l1AceEndCycle` | `0` | 排他终点，`0` 表示仿真结束 |

work-item ID 为 `-1` 时，跟踪器选择第一个 begin，并锁定其实际 ID；只有
相同 ID 的 end 才会结束窗口。

`configs/se/arm_chaos.py` 和 `configs/se/x86_chaos.py` 提供对应的
`--l1_ace*` 命令行参数，并只为 `l1i-cache-0` 与 `l1d-cache-0` 启用该指标，
不会误把 L2 统计为 L1。

## 指标

每个启用的 L1 cache 在 `l1Ace` 统计组中输出：

- `aceLineCycles`：ACE line-cycle。
- `aceBitCycles`：`aceLineCycles * cache_line_bits`。
- `aceRatio`：`aceBitCycles / (cache_size_bits * measuredCycles)`。
- `trackedFills`、`trackedDemandReads`、`trackedDemandWrites`：事件计数。
- `lifetimeEnds`：因覆盖、替换或失效而结束的生命周期数。
- `measuredCycles`、`windowBegins`、`windowEnds`：ROI 完整性指标。

## 定向测试

`scripts/test-ace-ibr-correctness.py --gem5 <ARM-target-gem5.opt>` 额外运行
4096 次 LDR、LDXR、成功 LL/SC、失败 STXR、LSE SWP、失败 CAS 和
成功同值 CAS，检查独占/原子读写不会漏计，且失败条件写不伪造数据写入。

`workloads/directed/l1_ace_workload.c` 提供四种访存指令流：

1. `reuse`：反复读取 32 KiB 热点集，延长大量 line 的最后消费时间。
2. `dead`：只写不读，用于确认未被消费的新值不形成 ACE 生命周期。
3. `pressure`：反复读取映射到同一 cache set 的 32 条 line，制造 8-way L1
   的持续冲突替换，预期 ACE ratio 低于 `reuse`、fill 数高于 `reuse`。
4. `stream`：一次顺序读取 8 MiB 数据，line 很快被替换，生命周期较短。

完整回归入口为 `scripts/test-l1-ace.sh`。层级里 L2 也会实例化同名的
`l1Ace` 统计组（默认关闭、恒为 0），所以按指标名断言时必须写明确的
`l1i-cache-0`/`l1d-cache-0` 前缀，不能匹配所有 `.l1Ace.` 后缀。脚本检查两个 L1 的 ROI 完整性、
四种 workload 的确定性结果、`reuse` 的 L1D ACE ratio 高于 `stream` 和
`pressure`、`pressure` 的 fill 数高于 `reuse`，以及 `dead` 是写主导的
需求流（需求写远多于需求读）。`dead` 允许出现少量推测需求读：classic cache
的请求路径不能按 seqNum 过滤错误路径，实测约 60 次/百万次写；测试要求
需求读低于需求写的千分之一，而不是断言恰好为零。脚本还从 bit-cycle、64 KiB cache 容量和测量周期逐项重算 ratio，
并检查其位于 `[0,1]`。FU IBR 回归同时启用三种指标，验证默认 ID 下错误 end 不会
提前关闭任一 ACE/IBR 窗口。脚本在 x86-64 宿主机上创建独立的
`build/ARM_X86_HOST`：gem5
自身是可由 x86-64 运行的本机程序，但启用 ARM 模拟 ISA；测试 workload 使用
`aarch64-linux-gnu-gcc` 和 ARM64 m5 ABI 编译，因此 guest 指令流为 AArch64。
