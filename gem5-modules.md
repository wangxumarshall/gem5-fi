# gem5 模块概览

本文按 `CHAOS/gem5` 的实际目录结构概括 gem5 的主要模块。重点放在“读源码时该目录负责什么、和其他模块怎样连接”，同时标出本仓库新增的 CHAOS 故障注入模块。路径均以 `CHAOS/gem5/` 为根。

## 总体结构

gem5 可以理解为四层：

| 层 | 代表目录 | 作用 |
|---|---|---|
| 仿真内核 | `src/sim`、`src/base`、`src/python` | 事件队列、SimObject 生命周期、统计、参数、Python/C++ 绑定。 |
| 被仿真硬件 | `src/cpu`、`src/mem`、`src/dev`、`src/arch` | CPU、缓存、内存、设备、ISA 语义和系统寄存器。 |
| 运行环境 | `configs`、`src/kern`、`system` | SE/FS 配置脚本、Linux/FreeBSD/Solaris ABI、启动资源。 |
| 工程支撑 | `ext`、`util`、`tests`、`site_scons`、`build_tools` | 第三方库、工具脚本、测试、构建系统。 |

## `src` 核心源码模块

### `src/sim`

gem5 的仿真运行时核心。这里定义离散事件循环、SimObject 生命周期、端口连接、序列化、退出事件、电源状态、guest ABI 支持等。最重要的文件族是 `eventq.*` 和 `simulate.*`：`EventQueue` 按 tick 和 priority 调度事件，`simulate()` 进入主循环并不断执行队首事件。

注意：`src/sim/eventq.hh` 是 gem5 主事件系统；`src/systemc/core/event.hh` 是 SystemC 兼容层的事件对象，两者服务的抽象层不同。

子模块：

| 子目录 | 说明 |
|---|---|
| `guest_abi` | guest 程序 ABI 适配，用于系统调用参数、结构布局等翻译。 |
| `power` | 电源状态、能耗状态机和 DVFS 相关支持。 |
| `probe` | probe point/监听器机制，供 tracing、统计或外部工具挂接事件。 |

### `src/base`

通用基础库。包括日志、调试、位操作、统计框架、loader、socket/VNC、过滤器、通用容器辅助等。几乎所有 gem5 模块都会依赖 `base`，它不表达具体硬件，只提供基础设施。

| 子目录 | 说明 |
|---|---|
| `stats` | gem5 统计系统，`stats.txt` 的大量字段来自这里的统计对象。 |
| `loader` | ELF/raw/binary 等程序镜像加载支持。 |
| `cache` | 基础缓存式数据结构，非 CPU cache 模型本体。 |
| `filters` | Bloom filter 等过滤器工具。 |
| `vnc` | 图形控制台/VNC 支持。 |
| `gtest` | C++ 单元测试辅助。 |

### `src/python`

Python 侧 gem5 API 和 C++ 绑定。配置脚本创建的 `System`、CPU、Cache、Board 等对象先是 Python SimObject，再由 `m5.instantiate()` 创建 C++ 对象。

| 子目录 | 说明 |
|---|---|
| `m5` | 传统 gem5 Python API，如 `m5.instantiate()`、`m5.simulate()`。 |
| `gem5` | 新 stdlib API，包括 boards、processors、cache hierarchies、resources 等。 |
| `pybind11` | C++/Python 绑定层。 |

### `src/arch`

ISA 和架构语义层。这里定义指令译码、静态指令、寄存器、MMU/TLB、系统寄存器、异常、Linux ABI、gdb XML 等。CPU 模型调用 ISA 层完成“这条指令语义上做什么”。

| 子目录 | 说明 |
|---|---|
| `arm` | AArch64/AArch32 架构支持，是本仓库 ARM64 SDC 工作的主要 ISA 目录。包含 TLB、MMU、页表 walker、系统寄存器、指令语义等。 |
| `x86` | x86 ISA、BIOS/bare metal、KVM 和 Linux ABI 支持。 |
| `riscv` | RISC-V ISA、bare metal、Linux ABI 和寄存器定义。 |
| `mips`、`power`、`sparc` | 其他 ISA 后端。 |
| `amdgpu` | AMD GPU ISA 相关支持。 |
| `generic` | 多 ISA 共享的 Linux/FreeBSD ABI 和通用架构设施。 |
| `isa_parser` | gem5 ISA DSL 解析器，用于从 ISA 描述生成译码/执行代码。 |
| `null` | Null ISA，用于测试或无真实 ISA 语义的场景。 |

本仓库 CHAOS 扩展：

| 模块 | 位置 | 说明 |
|---|---|---|
| `CHAOSArmTLB` | `src/arch/arm/CHAOSArmTLB` | ARM TLB 表项故障注入，支持 PFN/权限/XN/属性等字段扰动。 |
| `CHAOSArmSysReg` | `src/arch/arm/CHAOSArmSysReg` | ARM 系统寄存器读路径注入，用于 TTBR/TCR/SCTLR/MAIR 等配置类故障。 |
| `CHAOSPTW` | `src/arch/arm/CHAOSPTW` | 页表走查器读出故障注入，服务 FS 模式 PTW/translation fault 实验。 |

### `src/cpu`

CPU 模型与 CPU 相关公共设施。gem5 同时支持 fast functional CPU、简单时序 CPU、Minor in-order CPU、O3 out-of-order CPU、KVM CPU 和 Checker CPU。

| 子目录 | 说明 |
|---|---|
| `simple` | AtomicSimpleCPU、TimingSimpleCPU 等简单 CPU。适合快速运行或简单时序。 |
| `minor` | in-order pipeline CPU，介于 simple 和 O3 之间，流水级更显式。 |
| `o3` | 乱序 CPU 模型。包含 Fetch/Decode/Rename/IEW/Commit、ROB、IQ、LSQ、物理寄存器、free list、分支预测连接等。 |
| `checker` | Checker CPU。用于用简单/确定语义复核另一个 CPU 的执行结果；你打开的 `cpu_impl.hh` 就在这里。 |
| `kvm` | 通过宿主 KVM 加速 guest 执行的 CPU。 |
| `pred` | 分支预测器、BTB、RAS、loop predictor 等。 |
| `probes` | CPU probe/tracing 支持。 |
| `trace` | 指令 trace、Intel trace 等轨迹相关支持。 |
| `testers` | 内存系统和 Ruby 等测试用流量发生器，不是正常 workload CPU。 |

#### `src/cpu/o3`

本仓库最重要的 CPU 子系统。核心文件按流水线阶段划分：

| 模块 | 作用 |
|---|---|
| `cpu.*` | O3CPU 顶层对象，驱动每周期 tick，连接各流水级。 |
| `fetch.*`、`decode.*` | 取指和译码阶段。 |
| `rename.*`、`rename_map.*`、`free_list.*` | 寄存器重命名、映射表、物理寄存器分配与释放。 |
| `iew.*` | Issue/Execute/Writeback 聚合阶段，驱动指令执行和写回。 |
| `commit.*` | 提交、异常处理、squash、架构状态更新。 |
| `rob.*` | Reorder Buffer，保存 in-flight 指令直到提交或 squash。 |
| `inst_queue.*` | 发射队列和 wakeup/select 逻辑。 |
| `lsq.*`、`lsq_unit.*` | Load/Store Queue，负责 load/store 执行、转发、内存序检查。 |
| `regfile.*` | O3 物理寄存器堆。 |
| `fu_pool.*`、`FuncUnitConfig.py` | 功能单元池、操作类型到 FU/latency 的映射。 |
| `dyn_inst.*` | 动态指令对象，保存 seqNum、源/目的物理寄存器、执行状态等。 |
| `scoreboard.*`、`mem_dep_unit.*`、`store_set.*` | 就绪位、内存依赖预测和 store set。 |
| `probe` | O3 专用 trace/probe 工具。 |

本仓库 CHAOS O3 扩展：

| 模块 | 目标 | 说明 |
|---|---|---|
| `CHAOSPhysReg` | 物理寄存器堆 | bit flip/stuck fault、物理/架构映射模式、read-trace。 |
| `CHAOSRenameMap` | RAT/rename map | 映射位翻转、合法物理寄存器替换、历史残留类故障。 |
| `CHAOSFreeList` | free list | live reg marked free、pop wrong 等分配器故障。 |
| `CHAOSROB` | ROB | entry bit flip、异常抑制、spec leak 等提交/回滚类故障。 |
| `CHAOSIQ` | 发射队列 | ready bit、tag 替换、wakeup omit/phase 类故障。 |
| `CHAOSLSQFwd` | store-to-load forwarding | 转发数据扰动、错源、陈旧行、byte lane skew、all zero。 |
| `CHAOSAddrPath` | load 地址路径 | 翻译前虚拟地址扰动，主要用于 AGU/MMU 输入故障。 |
| `CHAOSExec` | 整数执行/写回 | 整数执行结果扰动。 |
| `CHAOSFPU` | 浮点/向量执行/写回 | FP/ASIMD 结果扰动和位谱实验。 |
| `CHAOSL1DForward` | L1D 到寄存器后校验路径 | ECC 后数据通路故障，模拟 post-check escape。 |
| `CHAOSBPU` | 分支预测路径 | 预测目标/方向故障，常作负对照。 |
| `CHAOSRAS` | RAS/错误记录逃逸 | 抑制应报告的错误记录，研究 DUE 转静默逃逸。 |

### `src/mem`

内存系统。包括 classic cache、Ruby memory system、QoS、协议描述、SLICC 编译器、内存 probe 和 CHAOS 内存注入器。

| 子目录 | 说明 |
|---|---|
| `cache` | classic cache 层次，包含 BaseCache、tags、replacement policy、prefetcher、compressor 等。 |
| `ruby` | Ruby 内存系统，支持详细一致性协议、network-on-chip、目录协议等。 |
| `protocol` | Ruby/SLICC 协议相关文件。 |
| `slicc` | SLICC 协议编译器，把协议描述生成 C++ 状态机。 |
| `qos` | 内存 QoS/优先级控制。 |
| `probes` | 内存系统 probe。 |
| `CHAOSMem` | 主存字节级故障注入。 |
| `CHAOSExMon` | ARM exclusive monitor/LL-SC 相关故障注入。 |

#### `src/mem/cache`

classic cache 的主体：

| 子目录 | 说明 |
|---|---|
| `tags` | tag store、set associative tags、indexing policy、partitioning policy。 |
| `replacement_policies` | LRU、Random、TreePLRU 等替换策略。 |
| `prefetch` | 硬件预取器。 |
| `compressors` | cache compression 支持。 |
| `CHAOSCache` | cache line、metadata、ECC/protection model、victim/writeback 等故障注入。 |

### `src/dev`

设备模型。FS 模式会大量使用这里的 UART、PCI、virtio、磁盘、网络、平台设备和 ISA 专用设备。

| 子目录 | 说明 |
|---|---|
| `arm`、`x86`、`riscv`、`mips`、`sparc` | ISA/平台相关设备。 |
| `pci` | PCI host/device 支持。 |
| `virtio` | virtio block/net/console 等半虚拟设备。 |
| `storage` | 磁盘、控制器等存储设备。 |
| `net` | 网络设备模型。 |
| `serial`、`ps2`、`i2c` | 常见外设总线和终端设备。 |
| `qemu` | QEMU 相关设备/接口支持。 |
| `amdgpu`、`hsa` | GPU/HSA 设备支持。 |
| `lupio` | RISC-V/教育平台常用设备族。 |

### `src/kern`

guest OS 兼容层。主要用于 SE 模式的 syscall emulation，以及 FS 模式部分内核结构辅助。

| 子目录 | 说明 |
|---|---|
| `linux` | Linux syscall、结构体、常量、loader/auxv 等支持。 |
| `freebsd` | FreeBSD ABI 支持。 |
| `solaris` | Solaris ABI 支持。 |

### `src/systemc`

SystemC/TLM 兼容层。它让 gem5 可以和 SystemC/TLM 组件协同仿真，包含 SystemC kernel、event、process、channel、dt 数据类型、TLM bridge、Python 绑定和测试。

| 子目录 | 说明 |
|---|---|
| `core` | SystemC 核心对象，如 event、process、scheduler。你当前看的 `core/event.hh` 在这里。 |
| `channel` | SystemC channel 抽象。 |
| `dt` | SystemC data types。 |
| `tlm_core`、`tlm_utils`、`tlm_bridge` | TLM 2.0 和 gem5 bridge。 |
| `python` | SystemC Python 集成。 |
| `tests` | SystemC 兼容测试。 |
| `ext`、`utils` | SystemC 支撑代码。 |

### `src/gpu-compute`

GPU compute 模型，主要服务 AMD GPU/HSA 方向。包含 wavefront、compute unit、shader pipeline、GPU memory pipeline、调度等。和本仓库 ARM CPU SDC 主线关系不大，但属于 gem5 可建模硬件的一部分。

### `src/proto`

Protocol Buffer 定义。用于 trace、统计、资源描述或外部工具交换结构化数据。

### `src/sst`

SST 集成接口。用于 gem5 与 Structural Simulation Toolkit 联合仿真。

### `src/learning_gem5`

learning gem5 教程源码，包含简单 SimObject、事件、内存对象等教学示例。适合学习框架，不是核心模型路径。

### `src/test_objects`

测试用 SimObject 和辅助对象，用于验证 gem5 框架能力。

### `src/doc` 与 `src/doxygen`

源码内文档和 Doxygen 支持，不参与仿真执行。

### `src/CHAOSReg`

上游 CHAOS 的架构寄存器注入器。目标是 ThreadContext/architectural register state；在 O3 上它不等价于 in-flight 物理寄存器故障，本仓库文档中已多次标注这个边界。

## `configs` 配置脚本模块

`configs` 是 Python 配置脚本集合，用来搭建 SimObject 树。它不实现硬件行为，但决定实例化哪些 CPU、cache、memory、device。

| 子目录 | 说明 |
|---|---|
| `common` | 传统脚本共享函数和 common options。 |
| `example` | SE/FS/Ruby/stdlib 示例配置。 |
| `ruby` | Ruby memory system 配置脚本。 |
| `topologies` | Ruby/Garnet 网络拓扑。 |
| `network` | 网络模型相关配置。 |
| `boot` | FS boot 辅助脚本。 |
| `dram`、`nvm` | DRAM/NVM 示例配置。 |
| `learning_gem5` | 教程配置。 |
| `splash2` | SPLASH-2 benchmark 配置。 |
| `dist` | 分布式 gem5 相关配置。 |
| `deprecated` | 旧配置脚本，读历史可参考，新实验应尽量避开。 |

本仓库另外在 repo 根的 `configs/se/` 下放置了项目专用配置，如 `arm_chaos.py`、`arm_chaos_cache.py`、`arm_chaos_fs.py`，它们是 CHAOS campaign runner 调用的主要入口。

## `ext` 第三方依赖模块

`ext` 保存 vendored third-party 库或可选模型。它们支撑 gem5 构建和外部模型集成，一般不按 gem5 核心源码方式修改。

| 子目录 | 说明 |
|---|---|
| `pybind11` | C++/Python 绑定库。 |
| `googletest` | C++ 测试框架。 |
| `Kconfiglib` | Kconfig 支持。 |
| `libelf`、`libfdt` | ELF 和 device tree 支持。 |
| `softfloat` | 软件浮点实现。 |
| `drampower`、`dramsim2`、`dramsim3`、`dramsys` | DRAM 功耗/时序外部模型。 |
| `dsent` | NoC/电路功耗建模。你打开的 `ElectricalModel.cc` 属于这里。 |
| `mcpat` | McPAT 功耗/面积建模。 |
| `sst` | SST 集成依赖。 |
| `systemc` | 外部 SystemC 支持库。 |
| `nomali` | Mali GPU 模型相关库。 |
| `gdbremote` | GDB remote protocol 支持。 |
| `dnet`、`fputils`、`iostream3`、`magic_enum`、`ply`、`testlib`、`x11keysym` | 网络、工具、小型库或测试依赖。 |

## `util` 工具模块

`util` 是开发、运行、维护和分析工具集合。

| 子目录 | 说明 |
|---|---|
| `m5` | guest 侧 `m5` 工具和 magic instruction 支持。 |
| `cpt_upgraders` | checkpoint 格式升级脚本。 |
| `gem5art`、`gem5-resources-manager` | 实验 artifact 和 resources 管理。 |
| `dockerfiles`、`github-runners-vagrant` | 容器和 CI 环境。 |
| `maint`、`style`、`update_copyright` | 维护、格式和版权工具。 |
| `minorview` | MinorCPU 可视化工具。 |
| `statetrace` | 状态 trace 工具。 |
| `systemc`、`tlm` | SystemC/TLM 工具。 |
| `tap`、`term` | 网络 TAP 和终端辅助。 |
| `dist` | 分布式 gem5 工具。 |
| `mem`、`plot_dram` | 内存实验和绘图辅助。 |
| `amdgpu`、`streamline`、`gem5_bridge`、`hypercall_external_signal` | GPU、Arm Streamline、bridge、外部信号/超调用等专用工具。 |

## 构建、测试与资源目录

| 路径 | 说明 |
|---|---|
| `build_opts` | 各 ISA/配置的默认构建选项。 |
| `build_tools` | 构建期代码生成和辅助工具。 |
| `site_scons` | SCons 扩展和 site tools。 |
| `build` | 本地构建输出，如 `build/ARM/gem5.opt`。 |
| `include` | 安装/外部包含用头文件。 |
| `system` | FS 模式系统资源示例，如 ARM boot 相关文件。 |
| `tests` | gem5 自带测试，包括 pyunit、gem5 run tests、test-progs。 |
| `docs` | 上游 gem5 文档。 |
| `m5out`、`runs` | 本地运行输出目录，通常不应作为源码依赖。 |

## 本仓库 CHAOS 顶层模块

除 vendored gem5 内的 `src/.../CHAOS*` 外，仓库根 `CHAOS/` 下还保留了独立模块目录。这些目录通常包含 `.py/.hh/.cc/SConscript` 四件套，便于移植或同步到 gem5 树。

| 目录 | 概括 |
|---|---|
| `CHAOSReg` | 架构寄存器故障注入。 |
| `CHAOSPhysReg` | O3 物理寄存器堆注入。 |
| `CHAOSCache` | cache line 和 metadata 注入。 |
| `CHAOSMem` | 主存字节注入。 |
| `CHAOSExMon` | exclusive monitor 注入。 |
| `CHAOSLSQFwd` | LSQ/store-to-load forwarding 注入。 |
| `CHAOSAddrPath` | 地址路径注入。 |
| `CHAOSPTW` | 页表走查器注入。 |
| `CHAOSArmTLB` | ARM TLB 注入。 |
| `CHAOSArmSysReg` | ARM 系统寄存器读路径注入。 |
| `CHAOSRenameMap` | 重命名映射注入。 |
| `CHAOSFreeList` | free list 注入。 |
| `CHAOSROB` | ROB 注入。 |
| `CHAOSIQ` | 发射队列注入。 |
| `CHAOSExec` | 整数执行结果注入。 |
| `CHAOSFPU` | 浮点/向量执行结果注入。 |
| `CHAOSL1DForward` | L1D 后校验路径注入。 |
| `CHAOSBPU` | 分支预测路径注入。 |
| `CHAOSRAS` | RAS/error record 逃逸注入。 |

## 阅读建议

1. 想理解“一次仿真怎么跑”：先读 `src/sim/eventq.hh`、`src/sim/simulate.cc`、`src/python/m5`。
2. 想理解 ARM 指令和 MMU：读 `src/arch/arm`，重点是 TLB、table walker、ISA/system register。
3. 想理解乱序核：读 `src/cpu/o3/cpu.cc`，再沿 `fetch -> decode -> rename -> iew -> commit` 读。
4. 想理解内存系统：classic cache 从 `src/mem/cache/base.*` 开始，Ruby 从 `src/mem/ruby` 和 `src/mem/slicc` 开始。
5. 想理解本仓库 SDC 注入：从 `configs/se/arm_chaos.py` 和 `src/cpu/o3/CHAOS*`、`src/mem/cache/CHAOSCache`、`src/arch/arm/CHAOS*` 开始。
