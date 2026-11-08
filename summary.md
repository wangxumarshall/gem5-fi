# gem5-fi-fuzz 代码框架总结

本仓库是在 vendored gem5 之上集成 CHAOS 故障注入器的 ARM64 SDC 研究工程。核心分两层：

- `CHAOS/gem5/`：完整 gem5 源码树，已接入 CHAOS SimObject 和若干 O3/ARM/memory hook。
- 仓库根目录的 `configs/`、`tools/`、`campaigns/`、`workloads/`、`artifacts/` 等：围绕 gem5+CHAOS 做单次运行、批量 campaign、结果分类、诊断和论文/实验材料沉淀。

## 1. 上游 gem5 框架

`CHAOS/gem5/` 是 gem5 主体。gem5 本质上是“C++ 模拟内核 + Python 配置脚本 + SCons 构建系统”：

- C++ 源码定义 CPU、cache、memory、device、ISA、event queue、统计等模拟对象。
- Python SimObject 描述参数和对象拓扑，运行时由配置脚本实例化系统。
- `gem5.opt` 启动后先执行 Python 配置脚本，配置脚本创建 board/CPU/cache/memory/workload，然后进入 C++ event-driven simulation。

主要目录职责：

| 目录 | 作用 |
|---|---|
| `CHAOS/gem5/SConstruct` | gem5 顶层 SCons 构建入口。 |
| `CHAOS/gem5/build_opts/` | 不同 ISA/构建目标的预设配置，如 `ARM`、`X86`、`ALL`。 |
| `CHAOS/gem5/build_tools/` | 构建期代码生成和辅助工具。 |
| `CHAOS/gem5/site_scons/` | gem5 自定义 SCons 构建逻辑。 |
| `CHAOS/gem5/src/` | gem5 C++/Python 核心源码。 |
| `CHAOS/gem5/configs/` | gem5 官方示例配置脚本。 |
| `CHAOS/gem5/tests/` | gem5 回归测试和 pyunit/gem5 测试。 |
| `CHAOS/gem5/util/` | m5term、统计处理、调试、转换等实用工具。 |
| `CHAOS/gem5/system/` | full-system 仿真用 bootloader、device tree 等系统侧资源源码。 |
| `CHAOS/gem5/ext/` | 第三方依赖或外部库。 |
| `CHAOS/gem5/include/` | 对外/公共 include 文件。 |

`CHAOS/gem5/src/` 下的关键模块：

| 目录 | 作用 |
|---|---|
| `src/sim/` | 仿真核心：event queue、SimObject 生命周期、统计、序列化/checkpoint、电源/探针基础设施。 |
| `src/python/` | Python 侧 `m5` 包、gem5 stdlib、SimObject 参数系统和 pybind 绑定。 |
| `src/base/` | 通用基础库：日志、trace、loader、stats、bitmap/cache helpers、调试辅助。 |
| `src/arch/` | ISA 相关实现，含 ARM/X86/RISCV 等译码、寄存器、TLB、MMU、系统寄存器、异常模型。 |
| `src/cpu/` | CPU 模型：`simple`、`minor`、`o3`、KVM、checker、branch predictor、probe 等。CHAOS 多数微结构注入点接在 `src/cpu/o3/`。 |
| `src/mem/` | 内存系统：classic cache、Ruby、协议、内存控制器、QoS、SLICC。CHAOSCache/CHAOSMem/CHAOSExMon 接在这里。 |
| `src/dev/` | 平台设备、PCI、virtio、serial、storage、network、ARM/X86/RISCV 设备。 |
| `src/kern/` | Linux/FreeBSD/Solaris 等 guest kernel 辅助模型。 |
| `src/systemc/` | SystemC/TLM 支持与测试。 |
| `src/gpu-compute/` | GPU compute 模型。 |
| `src/proto/` | protobuf 定义。 |
| `src/learning_gem5/` | learning gem5 教程示例对象。 |

## 2. CHAOS 故障注入层

`CHAOS/` 顶层保存各个故障注入器的源码副本；对应实现也被接入到 `CHAOS/gem5/src/` 中并编进 `gem5.opt`。每个注入器一般包含：

- `*.py`：SimObject 参数声明，供 Python 配置脚本实例化。
- `*.hh` / `*.cc`：C++ 注入逻辑。
- `SConscript`：告诉 gem5 构建系统编译该模块。

主要 CHAOS 模块：

| 模块 | 注入对象 | 作用/典型用途 |
|---|---|---|
| `CHAOSReg` | 架构寄存器 | 通过 ThreadContext 修改架构寄存器。适合 simple/timing 语义；在 O3 上不可靠触达在途指令，因此文档中标注为 architectural-state baseline。 |
| `CHAOSPhysReg` | O3 物理寄存器文件 | O3 专用，可按物理寄存器、前端 rename map 或 commit map 定位。支持 int/FP/vector，适合模拟真实 PRF cell 故障和 ABI role/bit/lane 分层实验。 |
| `CHAOSRenameMap` | O3 RAT/rename map | 模拟映射错误、F5 legal-domain substitute、字段 stuck，研究“历史残留/张冠李戴”类故障。 |
| `CHAOSFreeList` | O3 free list | 模拟 live physical register 被误标为空闲、pop 出错误物理寄存器等资源分配错误。 |
| `CHAOSROB` | O3 ROB | 支持 ROB entry bitflip、异常位静默、spec leak 相关模型，用于 DUE->SDC 或提交顺序/异常状态研究。 |
| `CHAOSIQ` | O3 issue queue | 模拟 src ready 位、tag substitute、wake phase/omit 等调度唤醒相关故障。 |
| `CHAOSExec` | O3 整数执行写回路径 | 对 int ALU writeback result 做位翻转，常作为整数路径阴性对照。 |
| `CHAOSFPU` | O3 FP/FSU 源读/写回路径 | 对 FP/向量数据通路注入，支持 sign/exp/mantissa 分段，用于浮点 SDC 位谱实验。 |
| `CHAOSLSQFwd` | O3 store-to-load forwarding | 在 store queue 转发给 load 的数据上注入；支持 bitflip/stuck、byte lane skew、wrong source、stale line、phase offset。是研究 load/store forwarding 错源/错相位的核心模块。 |
| `CHAOSL1DForward` | load result post-check 路径 | 模拟 ECC/check 之后 load 结果再被破坏的 post-check escape。 |
| `CHAOSBPU` | 分支预测路径 | 模拟 branch predictor target substitute / direction flip；当前更偏 hook 机制或负对照面。 |
| `CHAOSCache` | classic cache line/metadata/writeback | 注入 L1D/L1I/L2 数据字节、A64 指令字段、tag/valid/dirty/repl/coh 元数据、victim writeback payload，并支持 ECC/protection proxy。 |
| `CHAOSMem` | AbstractMemory/DRAM backing store | 对主存字节注入，支持地址范围、地址映射替换、SECDED/ecc_logic_fault 代理模型。 |
| `CHAOSExMon` | exclusive monitor | 模拟 LL/SC reservation 清除或 stale reservation，服务 LDXR/STXR 类实验。 |
| `CHAOSAddrPath` | O3 地址路径 | 在地址翻译前破坏虚拟地址字节，FS 模式下才有真实 MMU 可观测效果。 |
| `CHAOSPTW` | ARM page table walker | 破坏页表 walk 读出的 descriptor，可模拟 PTE bitflip、valid 清零、PTW ECC。FS 模式专用。 |
| `CHAOSArmTLB` | ARM iTLB/dTLB entry | 在 TLB hit 上破坏 pfn/AP/XN/attridx/ASID 等字段，支持 mapped-page substitute 和 parity_interleaved 代理。FS 模式专用。 |
| `CHAOSArmSysReg` | ARM system register read path | hook `readMiscRegNoEffect`，对白名单系统寄存器 MRS 返回值注入，如 TTBR/TCR/SCTLR/MAIR/VBAR。FS 模式专用。 |
| `CHAOSRAS` | O3 commit/RAS 记录路径 | 模拟故障指令提交时 ERR* 记录被抑制，即 RAS 机制逃逸。 |

常用共同参数：

- `probability`：每次候选事件/周期触发概率。
- `firstClock` / `lastClock`：注入时间窗口；本仓库通常将 `lastClock=0` 表示不设上界。
- `maxFaults`：最多注入次数；正式单故障实验通常设为 `1`。
- `rngSeed`：固定随机种子，保证 G0 replay。
- `faultType`：`bit_flip`、`stuck_at_zero`、`stuck_at_one`、`random`。
- `faultMask` / `bitsToChange`：指定翻转/强制的 bit 或随机选择 bit 数。
- `writeLog=True`：在 gem5 outdir 中写注入日志，如 `fault_injections.log`、`cache_injections.log`、`rat_injections.log`。

## 3. 本仓库实验层

| 目录/文件 | 作用 |
|---|---|
| `configs/se/arm_chaos.py` | ARM SE 模式主入口。使用 gem5 stdlib `SimpleBoard` + private L1/L2 + DDR3，支持 O3/Timing/Atomic/Minor，并按命令行挂载大多数 CPU/内存 CHAOS 注入器。 |
| `configs/se/arm_chaos_cache.py` | cache 专用 SE 入口。通过 monkey-patch cache hierarchy `_pre_instantiate` 捕获 `l1d-cache-0`/`l1i-cache-0`/`l2-cache-0` 并挂载 `CHAOSCache`。 |
| `configs/se/arm_chaos_fs.py` | ARM full-system 入口。使用 `ArmBoard`、本地 kernel/disk/bootloader，挂载 TLB/sysreg/PTW/addr path 等 FS-only 注入器。 |
| `configs/se/fs_checkpoint.py` | FS checkpoint 相关入口，用于更长 FS 流程。 |
| `configs/se/x86_chaos.py` | X86 SE 机制验证入口，主要挂载 `CHAOSReg`。 |
| `tools/runner.py` | 单 manifest 运行器：校验 manifest，映射 target/fault/trigger 到 gem5 参数，运行 gem5，收集注入日志和 stdout/stderr，输出分类结果。 |
| `tools/campaign.py` | 批量 campaign driver：读取 `campaigns/*.yaml`，展开参数网格，生成 per-run manifest，调用 runner，汇总 Wilson CI 和 `artifacts/<campaign>/summary.md`。 |
| `tools/classify.py` | 六类/九类 outcome 分类逻辑，区分 SDC、Masked、Crash、Hang、SimulatorError、Corrected、DetectedContained 等。 |
| `tools/report.py` | 对 campaign 结果做报告汇总。 |
| `tools/sdc_fingerprint.py`、`tools/escape_decomp.py`、`tools/loo_validate.py`、`tools/fisher_test.py` | 位谱/逃逸分解/留一验证/统计检验工具。 |
| `tools/diag/` | openEuler/ARM 故障诊断工具：ESR 解码、日志解析、规则诊断、spectrum triage。 |
| `campaigns/` | formal/pilot campaign YAML，定义 workload、target axes、fault axes、n_per_cell 等。 |
| `manifests/` | 单次运行 manifest。 |
| `schemas/manifest.schema.json` | manifest JSON schema。 |
| `workloads/directed/` | 定向 C kernel 和已编译二进制，如 `reg_chain`、`l1d_reduce`、`fp_fwd_kernel`、`gemm_*`、`svd_*` 等。 |
| `fi_research/probes/` | 早期/探索性 probe kernel 与分析脚本。 |
| `tests/` | pytest 单元测试和若干 pilot/gem5 replay 脚本。 |
| `artifacts/` | 已跑出的实验结果、cells.csv、summary、日志摘要等。 |
| `docs/` | 案例、论文表格、假设、CPU/设计建议等文档材料。 |
| `dft/` | DFT 向量包，`run_all.sh` 可批量跑若干缺陷签名向量。 |
| `gem5-fs/` | FS 模式需要的本地资源说明/脚本：kernel、disk、bootloader、dtb 等。 |

## 4. 如何构建

本仓库当前已存在 ARM gem5 二进制：

```bash
ls -l CHAOS/gem5/build/ARM/gem5.opt
```

注意：当前仓库里的 `CHAOS/gem5/build/ARM/gem5.opt` 是 `aarch64` 主机二进制。如果当前机器是 `x86_64`，直接执行会报 `Exec format error`。这种情况下需要在 AArch64 主机上运行，或在当前主机重新构建本机架构可执行的 gem5。

如果需要重新构建：

```bash
cd CHAOS/gem5
scons build/ARM/gem5.opt -j"$(nproc)"
```

也可以构建包含所有 ISA 的二进制：

```bash
cd CHAOS/gem5
scons build/ALL/gem5.opt -j"$(nproc)"
```

gem5 常见构建依赖包括 C++ 编译器、Python、SCons、zlib、m4、protobuf 等。仓库中 `CHAOS/Makefile` 是原 CHAOS 项目的 clone/build 封装；当前工程已经 vendored 了 gem5，日常通常直接在 `CHAOS/gem5` 下用 SCons。

## 5. 如何运行

### 5.1 无注入 ARM SE baseline

从仓库根目录执行：

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet --outdir=/tmp/gem5-base \
  configs/se/arm_chaos.py \
  --cmd workloads/directed/reg_chain \
  --cpu O3
```

如果出现 `cannot execute binary file: Exec format error`，先用 `file CHAOS/gem5/build/ARM/gem5.opt` 和 `uname -m` 检查主机/二进制架构是否一致。

`reg_chain` 的已知 golden 输出是：

```text
f247ef3fe6f02cfd
```

### 5.2 单次架构寄存器注入

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet --outdir=/tmp/gem5-chaos-reg \
  configs/se/arm_chaos.py \
  --cmd workloads/directed/reg_chain \
  --cpu O3 \
  --chaos_reg \
  --probability 1.0 \
  --first_clock 100000 \
  --max_faults 1 \
  --rng_seed 20260825 \
  --fault_type bit_flip \
  --fault_mask 0x1 \
  --target_reg_idx 3
```

输出目录中重点看：

```bash
ls /tmp/gem5-chaos-reg
sed -n '1,50p' /tmp/gem5-chaos-reg/fault_injections.log
sed -n '1,80p' /tmp/gem5-chaos-reg/stats.txt
```

### 5.3 O3 物理寄存器注入

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet --outdir=/tmp/gem5-chaos-phys \
  configs/se/arm_chaos.py \
  --cmd workloads/directed/reg_chain \
  --cpu O3 \
  --chaos_phys \
  --phys_mode arch_frontend \
  --phys_target_arch 3 \
  --phys_reg_class integer \
  --probability 1.0 \
  --first_clock 100000 \
  --max_faults 1 \
  --rng_seed 20260825 \
  --fault_type bit_flip \
  --fault_mask 0x1
```

O3 上研究真实在途值传播时，优先使用 `CHAOSPhysReg`，不要把 `CHAOSReg` 的结果直接解释成 PRF 级故障。

### 5.4 cache 注入

cache 注入走专门入口 `arm_chaos_cache.py`：

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet --outdir=/tmp/gem5-chaos-cache \
  configs/se/arm_chaos_cache.py \
  --cmd workloads/directed/l1d_reduce \
  --cpu O3 \
  --target l1d \
  --target_field data \
  --first_clock 10000 \
  --max_faults 1 \
  --rng_seed 20260825 \
  --fault_type bit_flip \
  --bits_to_change 1 \
  --protection_model none
```

metadata 示例：

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet --outdir=/tmp/gem5-chaos-tag \
  configs/se/arm_chaos_cache.py \
  --cmd workloads/directed/l1d_reduce \
  --cpu O3 \
  --target l1d \
  --target_field tag \
  --first_clock 10000 \
  --max_faults 1 \
  --rng_seed 1
```

### 5.5 用 runner 跑 manifest

`tools/runner.py` 是推荐的单次实验封装。它会读 manifest，解析 target/fault，运行 gem5，并统一分类：

```bash
python3 tools/runner.py manifests/v2-rat-f5-accum.yaml \
  --binary workloads/directed/accum_kernel
```

如果 manifest 的 `oracle.golden_id` 在 `tools/runner.py` 的 `GOLDEN_IDS` 表里，runner 会自动解析 golden；否则显式传入：

```bash
python3 tools/runner.py manifests/p1-gpr-regchain-000384.yaml \
  --binary workloads/directed/reg_chain \
  --golden-checksum f247ef3fe6f02cfd
```

runner 最终会打印类似：

```text
[runner] RESULT: run_id=... classification=SDC faults_injected=1 exit=0 timed_out=False
```

### 5.6 批量 campaign

`tools/campaign.py` 展开 YAML 网格并调用 runner：

```bash
python3 tools/campaign.py campaigns/prf-x3-bitscan-smoke.yaml \
  --binary workloads/directed/reg_chain \
  --workload-golden f247ef3fe6f02cfd \
  --n-per-cell 4 \
  --jobs 1 \
  --artifacts artifacts/prf-smoke-local
```

formal 规模常用 `--n-per-cell 384`，耗时会很长。输出通常包括：

- `artifacts/<campaign>/cells.csv`
- `artifacts/<campaign>/summary.md`
- 每个 run 的 manifest 和 stdout/stderr/分类结果

### 5.7 ARM full-system 运行

FS 模式用于 TLB、系统寄存器、PTW、地址路径等必须打开 MMU/Linux 的注入器。示例：

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet --outdir=/tmp/gem5-fs \
  configs/se/arm_chaos_fs.py \
  --kernel gem5-fs/vmlinux \
  --disk gem5-fs/ubuntu.img \
  --bootloader gem5-fs/boot.arm64 \
  --root-partition /dev/vda1 \
  --cpu Atomic \
  --mem-size 2GiB
```

TLB 注入示例：

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet --outdir=/tmp/gem5-fs-tlb \
  configs/se/arm_chaos_fs.py \
  --kernel gem5-fs/vmlinux \
  --disk gem5-fs/ubuntu.img \
  --bootloader gem5-fs/boot.arm64 \
  --root-partition /dev/vda1 \
  --cpu Atomic \
  --chaos_armtlb \
  --tlb_probability 1.0 \
  --tlb_first_clock 100000 \
  --tlb_max_faults 1 \
  --tlb_pfn_select_mode mapped_page
```

注意：FS 启动到 Linux 用户态通常比 SE 慢很多，可能需要数十分钟到数小时墙钟时间。仓库 `gem5-fs/readme.md` 对 kernel/disk/bootloader/dtb 和 m5term 有更详细说明。

### 5.8 运行 Python 单元测试

```bash
python3 -m pytest tests
```

这些测试主要覆盖分类器、报告、指纹、诊断器等 Python 工具，不等价于完整 gem5 仿真回归。

### 5.9 DFT 向量批跑

```bash
./dft/run_all.sh
```

该脚本会跑 baseline 和若干缺陷签名向量。脚本当前会 source `/home/sdc/gem5-deps/env.sh`，如果本机没有该环境文件，需要先调整环境或手动执行里面的 gem5 命令。

## 6. 一次实验的典型数据流

1. 选 workload：例如 `workloads/directed/reg_chain`。
2. 选注入器和 fault model：例如 `CHAOSPhysReg` + `bit_flip` + X3 bit0。
3. 写 manifest 或直接用命令行。
4. `tools/runner.py` 把 manifest 映射成 `configs/se/arm_chaos.py` / `arm_chaos_cache.py` / FS 配置参数。
5. `gem5.opt` 执行 Python 配置，创建 board、CPU、cache、memory 和 CHAOS SimObject。
6. C++ hook 在目标周期/事件触发注入，日志写到 outdir。
7. runner 收集 stdout/stderr、注入日志、退出码、超时状态。
8. `tools/classify.py` 对比 golden，将结果归为 Masked/SDC/Crash/Hang/SimulatorError/Corrected 等。
9. campaign 汇总每个 cell 的 SDC 率和 Wilson CI。

## 7. 读代码建议

建议按这个顺序读：

1. `configs/se/arm_chaos.py`：理解一个 SE 系统如何被搭起来，以及各 SimObject 怎么挂载。
2. `tools/runner.py`：理解 manifest 的 target/fault/trigger 怎么落到 gem5 命令行参数。
3. 某个注入器的 `*.py` + `*.cc`：例如 `CHAOS/CHAOSPhysReg/` 或 `CHAOS/CHAOSLSQFwd/`。
4. 对应 hook 所在的 gem5 源码：例如 O3 CPU 读写寄存器、LSQ forwarding、cache writeback、ARM TLB lookup。
5. `tools/classify.py` 和 `tools/campaign.py`：理解结果如何被分类和统计。
6. `campaigns/*.yaml` 与 `artifacts/*/summary.md`：理解已完成实验的参数网格和结论。

## 8. 重要边界

- `CHAOSReg` 是架构寄存器层注入；O3 在途指令相关结论应优先看 `CHAOSPhysReg`、RAT、ROB、LSQ 等 O3 微结构注入器。
- `CHAOSAddrPath`、`CHAOSPTW`、`CHAOSArmTLB`、`CHAOSArmSysReg` 的真实效果依赖 FS/MMU；SE 模式下可能只能验证 SimObject/hook 接线，不能代表最终故障传播。
- cache/DRAM 的 ECC、parity、SECDED 多为保护模型代理，不是完整物理 ECC controller 时序模型。
- `kp920_proxy` 是 TaiShan V110/Kunpeng 920 的参数代理，不是 cycle-exact 模型；文档中也明确了 unified IQ、classic cache、NoC 等差距。
- formal campaign 默认强调单故障纪律：`maxFaults` 应为 `0` 或 `1`，正式 SDC 率实验通常设 `1`。


1. src/sim/main.cc:47
       main()

2. src/sim/main.cc:87
       m5.main()

3. src/python/m5/main.py:388
       main()

4. src/python/m5/main.py:409
       parse_options()

5. src/python/m5/main.py:687
       exec(filecode, scope)

6. 你的配置脚本
       m5.instantiate()

7. src/python/m5/simulate.py:220
       instantiate()

8. 你的配置脚本
       m5.simulate()

9. src/python/m5/simulate.py:247
       simulate()

10. src/sim/simulate.cc:191
        simulate()

11. src/sim/simulate.cc:293
        doSimLoop()

12. src/sim/eventq.cc:223
        EventQueue::serviceOne()

13. src/cpu/o3/cpu.cc:368
        CPU::tick()

14. src/cpu/o3/fetch.cc:821
        Fetch::tick()