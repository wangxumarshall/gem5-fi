# 鲲鹏 920（Kunpeng-920 / HIP08）CPU 核微架构深度研究 — 本机实测报告

> **文档性质**：本文档由对本设备的**实证采集**（/proc、/sys、ACPI 表、内核日志、自编微基准）构成，
> 所有标注"实测"的数据均来自本机上实际执行的命令及其真实输出；少量无法从 Linux 用户态观测的
> 核内微架构参数（ROB/调度队列等）引自公开资料并明确标注。
> 公开资料视角的 SoC/核微架构全景见姊妹篇 [`kunpeng.md`](kunpeng.md)。
>
> **采集环境**：openEuler 24.03 SP3，内核 6.6.0-145.3.16.148.oe2403sp3.aarch64，采集日期 2026-09-04。
> 本机为共享服务器，微基准数据含背景负载噪声，已在相应处标注。

---

## 1. 设备与 SoC 身份

| 项目 | 实测值 | 采集来源 |
|---|---|---|
| 整机/主板 | RCSIT **TG225 A1**（BC82AMDYC），BIOS 7.15.K | `/sys/class/dmi/id/*` |
| SoC 厂商 | HiSilicon | `lscpu` 厂商 ID |
| SoC 型号 | **Kunpeng-920**（ACPI OEM 表内部代号 **HIP08**） | `lscpu`；内核日志 ACPI 表 OEM ID `HISI HIP08` |
| CPU 核 | TaiShan V110（TSV110） | MIDR_EL1 `part` 字段（见下） |
| 逻辑 CPU | 128（在线 0–121,124–127；**122,123 离线**；possible/present 0–127） | `/sys/devices/system/cpu/{online,offline,possible,present}` |
| Sockets | 2 × 64 核 | `lscpu` |
| SMT | **无**（每核 1 线程，`thread_siblings_list` 仅含自身） | topology sysfs |
| 内核 | 6.6.0-145.3.16.148.oe2403sp3.aarch64（GCC 12.3.1） | `uname -a`、`/proc/version` |
| 引导方式 | ACPI（HIP08 表族）+ devicetree 并存；NUMA 拓扑来自 ACPI SRAT/SLIT/PPTT | 内核日志 |
| BogoMIPS | 200.00（lpj=400000，由定时器频率计算，非总线时钟） | `/proc/cpuinfo`、内核日志 |
| 编译器支持 | `gcc -mcpu=tsv110` 原生可用 | 实测编译通过 |

### 1.1 MIDR_EL1（实测，所有核一致）

```
/sys/devices/system/cpu/cpu0/regs/identification/midr_el1 = 0x00000000481fd010
```

| MIDR 字段 | 位 | 值 | 含义 |
|---|---|---|---|
| Implementer | [31:24] | `0x48` | HiSilicon |
| Variant | [23:20] | `0x1` | 变体 1 |
| Architecture | [19:16] | `0xf` | CPUID scheme（ARMv8 走 ID 寄存器） |
| **PartNum** | [15:4] | **`0xd01`** | **TaiShan V110** |
| Revision | [3:0] | `0x0` | 修订 0 |

REVIDR_EL1 = `0x0`。`/proc/cpuinfo` 中 `CPU implementer: 0x48 / variant: 0x1 / part: 0xd01 / revision: 0` 与之完全一致。

---

## 2. 物理拓扑（ACPI PPTT 驱动下的实测结构）

```
Socket 0 (64 核)                            Socket 1 (64 核)
├─ SCCL 1 (计算 Die) = NUMA node0           ├─ SCCL 5 (计算 Die) = NUMA node2
│   8 × CCL(cluster) × 4 核 = 32 核          │   cpu64–95
│   cpu0–31                                  │
│   L3 32MB / 8×L3C bank / 4×DDRC / 2×HHA    │
├─ SCCL 3 (计算 Die) = NUMA node1            ├─ SCCL 7 (计算 Die) = NUMA node3
│   cpu32–63  ← 本机唯一有内存的节点           │   cpu96–121,124–127
└────────────────────────────────────────────┴────────────────────────────────
```

- **SCCL（Super CPU Cluster，即一个计算 Die）**的存在由 uncore PMU 命名直接实证：
  `/sys/bus/event_source/devices/` 下有 `hisi_sccl{1,3,5,7}_*` 四组设备，每组含
  **8× `l3c` + 4× `ddrc` + 2× `hha`**（Hydra Home Agent，LLC 一致性宿主代理）。
- 每 SCCL 32 核 = 8 cluster × 4 核。SRAT 中 MPIDR 呈现 `Aff2`（Die/SCCL）× `Aff1`（cluster 内 0–3）结构：
  node0 的 MPIDR 从 `0x80000` 起（Aff1 步进 0x100 × 4 核、Aff2 步进 × 8 cluster），node1 从 `0x180000` 起。
- `physical_package_id` 实测为非常规编号（cpu0 = 36，来自固件 PPTT socket id），`core_siblings_list=0-63` 证实 64 核/socket。
- `cpu_capacity=1024`（全部核同构，无能效不对称）。

### 2.1 NUMA 距离矩阵（SLIT 实测）

```
node     0   1   2   3
  0:    10  12  20  22
  1:    12  10  22  24
  2:    20  22  10  12
  3:    22  24  12  10
```

解读：同 SCCL 本地 10；**同 socket 跨 SCCL 12**；跨 socket 20–24。NUMA 域层级为
核 → CCL(4核) → SCCL(32核) → Socket(64核) → 全机(128核)。

### 2.2 ⚠️ 本机特有配置：node0/2/3 memoryless

内核日志实证：

```
NUMA: Initmem setup node 0 [<memory-less node>]
Initmem setup node 0/2/3 as memoryless
NUMA: NODE_DATA(0/2/3) on node 1
```

`numactl -H`：node1 size 30640 MB，node0/2/3 size 0 MB。ghes_edac 报告 32 个 DIMM 槽，
但当前仅一个内存域可用（32GB 全部挂在 node1/SCCL3）。**这是本机部署形态，不是 920 的设计上限**
（920 设计为每 SCCL 4 通道 DDR4-2933）。对本机任何 NUMA 评测都必须考虑
"所有内存访问本质上都是单节点供给"这一事实。

---

## 3. 指令集架构（ISA，实测 HWCAP）

`/proc/cpuinfo` Features（全部 128 核一致）：

```
fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm jscvt fcma dcpop asimddp asimdfhm
```

| 特性 | ISA 归属 | 工程意义 |
|---|---|---|
| `fp asimd` | ARMv8.0 | 31×64b 通用寄存器 + 32×128b NEON |
| `atomics` | ARMv8.1 **LSE** | LDADD/SWCAS 原子，数据库锁/引用计数关键加速；内核已用 LSE 替换 LL/SC |
| `fphp asimdhp` | ARMv8.2 **FP16** | 半精度标量/向量，轻量推理 |
| `aes pmull sha1 sha2 crc32` | v8 Crypto 扩展 | TLS/存储校验硬件加速 |
| `jscvt fcma` | v8.3 子集 | JS 数值转换（服务器 JS 负载）、复数 FMA |
| `asimdrdm asimddp asimdfhm` | v8.x RDM/DP/FHM | 点积类运算（asimddp 含 SDOT/UDOT） |
| `dcpop` | v8.2 DC PoP | 持久内存语义（本机无 NVDIMM，仅指令可用） |
| `cpuid` | v8.0 ID scheme | 按 ID 寄存器枚举特性 |

**明确不支持（实测 HWCAP 缺失，且 cmdline 含 `arm64.nopauth`）**：SVE/SVE2、BTI、PAC/指针认证、
MTE、LRCPC、uscat、LSE128。→ TSV110 是 **ARMv8.2-A 级**核心，无 v8.3 指针认证、无可伸缩向量。
编译器层面 `gcc -mcpu=tsv110` 直接面向该核调优（实测可用）。

### 3.1 内核检测到的系统级特性（内核日志实测）

```
CPU features: detected: GIC system register CPU interface
CPU features: detected: Virtualization Host Extensions      ← VHE，KVM 在 EL2 零切换开销
CPU features: detected: Hardware dirty bit management      ← DBM，脏页追踪硬件化
CPU features: detected: RAS Extension Support              ← ARMv8 RAS，配合 HEST/EINJ
CPU features: detected: Spectre-BHB
CPU features: kernel page table isolation forced ON by KASLR ← KPTI（KASLR 强制）
Detected VIPT I-cache on CPU0（全部核）                      ← L1I 为 VIPT 类型
```

内核 cmdline 另有 `nospectre_bhb`（BHB 填充缓解关闭）。PSCI v1.1 via SMC v1.2 conduit；
cpuidle driver = **none**（无 ACPI LPI 暴露，空闲走 PSCI cpu_off + menu governor）。

---

## 4. 缓存层次与内存子系统（sysfs 实测）

| 层级 | 容量 | 共享域 | Line Size | 组织/策略（sysfs 报告） |
|---|---|---|---|---|
| L1d | 64 KB / 核 | 单核私有 | 64 B | — |
| L1i | 64 KB / 核 | 单核私有 | 64 B | VIPT（内核探测实证） |
| L2 | 512 KB / 核 | 单核私有 | 64 B | Unified |
| **L3 (LLC)** | **32 MB / SCCL** | **32 核（= NUMA 节点）** | **128 B** | Unified；2048 sets；ReadWriteAllocate / WriteBack；`ways_of_associativity=15`（与 32768K/128B/2048=128 ways 不自洽，系 HiSilicon L3C 报告口径，如实记录） |

关键实测结论：

1. **L3 line 128B 而 L1/L2 64B**——跨层级行宽不对称。对随机访问负载，L3 命中一次搬运 128B；
   利用率低于 64B 时读放大。软件侧冷数据块宜按 128B 对齐。
2. **LLC 边界 = SCCL 边界 = NUMA 节点边界**：`L3 shared_cpu_list` 与 NUMA `cpulist` 完全重合
   （0-31 / 32-63 / 64-95 / 96-121,124-127）。跨 cluster 访问同 SCCL 的 L3 走 NoC 环；
   跨 SCCL/Socket 则失去 LLC 亲和性（HHA 目录转发）。
3. 每 SCCL 有 **8 个 L3C PMU 实例**——L3 按 cluster 分 bank（8 bank/Die）。
4. lscpu 汇总口径：L1d/L1i 各 7.9 MiB（126 在线核 × 64KB）、L2 63 MiB、L3 128 MiB（4 实例 × 32MB）。

### 4.1 微基准：指针追逐延迟（实测）

方法：素数步长循环置换链防预取器，`cntvct_el0`（实测 `cntfrq_el0=100000000`，100 MHz）计时，
cpu4 绑核，governor=performance @2.6GHz，两次独立运行结果一致（±5%）。

| 工作集 | ns/访问 | 折算周期 @2.6GHz | 落点解读 |
|---|---|---|---|
| 4–64 KB | 1.91–2.15 | **~5.0–5.6 cyc** | L1D 命中（含依赖链 + 素数步长组冲突开销） |
| 96–128 KB | 3.2–3.9 | 8–10 cyc | 跨出 L1 的过渡 |
| 256–512 KB | 4.2–7.6 | 11–20 cyc | **L2 命中**（与 512KB L2 边界吻合） |
| 768 KB–1 MB | 5–13（非单调） | — | 共享机器噪声区间 |
| 1.5–2 MB | 35–38 | 92–100 cyc | L3/远端系统访问 |
| 8–16 MB | 62–88 | 160–230 cyc | L3 容量内但受共存负载干扰（估值上限） |

> 噪声声明：本机为共享服务器，1–16MB 区间受背景负载干扰明显（8MB 反而慢于 16MB 即为证据）。
> L1 ~5 cyc、L2 ~10–20 cyc 的量级可信；L3 精确延迟需独占复测。
> 公开资料口径（L2 10 cyc、L3 分区模式 ~36 cyc、DRAM unloaded ~96ns）与本次实测量级一致。

### 4.2 微基准：流式带宽（实测，单线程程序，taskset 仅定亲和性）

| 工作集 | 单核 (cpu4) | node1 本地 (cpunodebind=1) | node0 CPU→node1 内存（跨 SCCL） |
|---|---|---|---|
| 16–256 KB (L1/L2) | 23.5–23.9 GB/s | 23.3–24.2 GB/s | 23.6–24.2 GB/s |
| 1 MB | 21.6 GB/s | 19.9 GB/s | 21.9 GB/s |
| 4 MB (L3 域) | 13.5 GB/s | 18.2 GB/s | 16.0 GB/s |
| 16 MB | 6.7 GB/s | **14.8 GB/s** | **6.7 GB/s** |
| 64 MB (DRAM) | 9.5 GB/s | 8.9 GB/s | 10.0 GB/s |

解读（并坦承局限）：
- 小工作集下三个配置相同（~24 GB/s ≈ 9.2 B/cyc）——缓存命中带宽，与公开微架构"L1D 2×128b 访问口"
  一致（受 RMW 指令混排限制，为理论 32 B/cyc 的 ~29%，单线程正常水平）。
- **16MB 工作集下本地 14.8 GB/s vs 跨 SCCL 6.7 GB/s——跨 Die 内存带宽惩罚 ~2.2×**，
  与 SLIT 距离 12（跨 SCCL）直接对应。NUMA 亲和性对带宽敏感型负载在本机是硬指标。
- 局限：测试程序为单线程（taskset 只限定亲和性，不产生并行），多核聚合带宽未测
  （perf 不可用，见 §8）；64MB 点受背景负载干扰。精确带宽数据需独占窗口复测。

### 4.3 页表 / 大页（实测）

- 基本页 4 KB（`getconf PAGESIZE`）；VA 空间 48-bit（SMMUv3 ias/oas 48-bit 实证，无 52-bit PA）。
- THP：`enabled=[always]`；HugeTLB 注册 **64KB / 2MB / 32MB / 1GB** 四档（64KB 档为 ARM CONTIG 特色）。
  当前 `HugePages_Total: 0`；运行态 AnonHugePages 61440 kB、FileHugePages ~1.3 GB（THP 实际在用）。

---

## 5. 频率与功耗管理（实测）

- **驱动**：`cppc_cpufreq`（ACPI CPPC 寄存器接口，PCCT 表实证），**非**离散频表驱动。
- **Governor**：`performance`，4 个 policy 域 = 4 个 SCCL（policy0/32/64/96，`freqdomain_cpus`
  与 NUMA cpulist 一致）——**DVFS 粒度是整个计算 Die（32 核同频）**，无 per-核调频。
- **频率范围**：硬件 200 MHz – 2.6 GHz **连续**（CPPC 无频表，`scaling_available_frequencies` 不存在）；
  当前 4 域全部钉在 2.6 GHz。
- **Boost**：`boost=0`（disabled）——本 SKU 满频 2.6 GHz，无加速频率。
- CPPC 寄存器（cpu0 实测）：`highest_perf=2600000`、`nominal_perf=2600000`（最高性能=标称性能，
  印证无 boost）、`lowest_nonlinear_perf=1000000`、`lowest_perf=200000`、`reference_perf=2600000`；
  energy_perf 读取为 `<unsupported>`。
- **空闲**：cpuidle driver=none，无 ACPI LPI C-state 暴露；空闲经 PSCI `cpu_off` 深睡眠 + menu governor。
  即本机无法从 Linux 侧观测/控制细粒度 P-state，能效管理全部托付 CPPC 固件。

---

## 6. 中断、定时器与虚拟化（实测）

- **GICv3 + ITS ×2**（SRAT: PXM0→ITS0、PXM2→ITS1，每 socket 一个 ITS）；DirectLPI；
  **GICv4**（vCPU DirectLPI）——KVM 直通中断注入零陷出。
- arch_timer（generic timer）每核本地分发（/proc/interrupts 实证 126 列分布均匀），
  `cntfrq_el0=100 MHz`，`clocksource=arch_sys_counter`（max_idle_ns ≈ 440 s）。
- **VHE 实测启用**：KVM 宿主内核直接运行于 EL2。
- SMMUv3 ×≥7 实例（ias/oas 48-bit），每实例配 PMCG 性能计数（`smmuv3_pmcg_*` PMU ×6+）；
  cmdline 对两个设备 `smmu.bypassdev=0x1000:0x17/0x15`（DMA 直通）。
- **虚拟机在线**：/proc/interrupts 存在 `vgic`、`kvm guest ptimer/vtimer` 行——本机承载 KVM 客户机。

---

## 7. RAS 与可靠性设施（实测，与故障注入研究直接相关）

| 设施 | 实测证据 |
|---|---|
| ARMv8 RAS 扩展 | `CPU features: detected: RAS Extension Support` |
| ACPI HEST（0x58C 字节，多错误源） | ACPI 表枚举 |
| **ACPI EINJ（0x170 字节）** | **固件级故障注入接口存在**（错误注入的理论通道，需 root + 固件配合） |
| ACPI BERT / ERST | 启动错误记录 / 错误持久化 |
| SDEI v1.0 | 固件事件（RAS NMI 类）上报通道 |
| ghes_edac | 32 DIMM 槽；mc0 = 32768 MB；`ce_count=0 ue_count=0`（当前无累积错误） |
| kdump | crashkernel 1024MB high + 128MB low 保留实证 |

LLC/DDR/HHA 一致性部件全部暴露 perf PMU（`hisi_sccl*_l3c/ddrc/hha`，事件目录含
`rd_spipe/rd_cpipe`（环/管道读写）、`retry_ring`（NoC 环重试）、`edir-*`（HHA 目录）、
`flux_rd/wr`（DDR 读写流量）等），为故障注入后的缓存一致性行为量化提供硬件计数器
（本机受 perf_event_paranoid=2 限制，需 root 才能采样）。

---

## 8. Linux 内核视角的安全缓解（实测）

`/sys/devices/system/cpu/vulnerabilities/*` 全量 17 项：

- spectre_v1: `Mitigation: __user pointer sanitization`
- spectre_v2: `Mitigation: CSV2, but not BHB`（硬件 CSV2，非软件 return 栈；BHB 缓解被 cmdline 关闭）
- 其余 15 项（meltdown / l1tf / mds / retbleed / tsx_async_abort / spec_store_bypass / srbds /
  gather_data_sampling / mmio_stale_data / reg_file_data_sampling / spec_rstack_overflow / tsa /
  vmscape / itlb_multihit）全部 `Not affected`——ARM 核对 x86 侧信道家族天然免疫；
  KPTI 仅因 KASLR 被强制开启（ARM 上无 Meltdown 必要性）。

perf 事件访问受 `perf_event_paranoid=2` + SELinux 限制（实测 `perf stat` 用户态被拒），
PMU 硬件计数需 root/CAP_PERFMON。

---

## 9. TaiShan V110 核内微架构（公开资料对照，无法从 Linux 用户态直接观测）

以下参数来自公开渠道（详见 [`kunpeng.md`](kunpeng.md) §3），**标注为公开资料，仅作实测数据的解释框架**：

- 前端：4-wide 取指/解码，~8 级流水；L1I 64KB（与实测 VIPT 一致）；两级分支预测 + 31-entry RSB。
- 后端：乱序执行，ROB ~128；3×ALU + 1×复杂（乘除）；双 FSU 浮点流水（FP32 FMA 双发，FP64 半速）；
  2×AGU；PRF 式重命名，含 move elimination。
- LSU：L1D load-to-use 4 cyc、store forwarding 6–7 cyc——与本次实测 L1 ~5 cyc（含素数链开销）吻合。
- L2 512KB 私有 10 cyc（实测 10–20 cyc 区间吻合）；L3 分区模式 ~36 cyc、DRAM unloaded ~96ns
  （实测远端访问 35–90 ns 区间吻合）。
- NoC：每 Die 双环 bufferless mesh；L3 三模式（shared/private/partition）；LSE 原子微架构加速。

---

## 10. 对本仓库（gem5-fi 故障注入研究）的工程启示

1. **真实拓扑 ≠ 默认假设**：本机 128 逻辑核但 122/123 离线、内存全在 node1——任何多核/NUMA 敏感的
   故障注入实验（gem5 对照真机）都应按"4 NUMA 节点 / 单内存节点 / 无 SMT"建模，而非理想对称。
2. **L3 128B 行宽**：注入 cache line 级故障时，模拟器中 L3 行宽应取 128（L1/L2 为 64），
   行宽不匹配会改变故障传播面。
3. **DVFS 域 = 32 核 Die**：频率相关故障模型（降频/超频类）应以 SCCL 为最小粒度。
4. **EINJ/HEST/SDEI/ghes_edac 齐备**：真机侧 RAS 上报链路完整，注入故障的出口观测点包括
   EDAC 计数器与 GHES 事件；uncore PMU（l3c/hha/ddrc）可量化一致性部件级行为。
5. **无 PAC/BTI/SVE**：涉及控制流完整性或向量通路的注入实验，ISA 面以 ARMv8.2 为准。

---

## 附录 A：数据采集命令清单

```bash
lscpu                                   # 概览/漏洞
cat /proc/cpuinfo                       # MIDR 字段/HWCAP/每核信息
cat /sys/devices/system/cpu/cpu0/regs/identification/{midr_el1,revidr_el1}
cat /sys/devices/system/cpu/cpu*/topology/*
cat /sys/devices/system/cpu/cpu*/cache/index*/{level,type,size,shared_cpu_list,coherency_line_size,number_of_sets,ways_of_associativity,allocation_policy,write_policy}
cat /sys/devices/system/node/node*/{cpulist,distance}
numactl -H
cat /sys/devices/system/cpu/cpufreq/policy*/{scaling_driver,scaling_governor,scaling_cur_freq,cpuinfo_min_freq,cpuinfo_max_freq}
cat /sys/devices/system/cpu/cpu0/acpi_cppc/{highest_perf,lowest_perf,nominal_perf,lowest_nonlinear_perf,reference_perf}
cat /sys/devices/system/cpu/{online,offline,possible,present}
cat /sys/devices/system/cpu/cpu0/cpu_capacity
ls /sys/bus/event_source/devices/       # core + uncore PMU 全量
cat /sys/bus/event_source/devices/hisi_sccl*/events/*
cat /sys/devices/system/cpu/vulnerabilities/*
cat /sys/class/dmi/id/{product_name,board_name,board_vendor,bios_version}
journalctl -k -b                        # ACPI 表/SRAT/PPTT/NUMA/特性检测/RAS
cat /proc/cmdline
cat /sys/devices/system/edac/mc/mc0/*   # ghes_edac DIMM/CE/UE
cat /sys/firmware/acpi/tables/          # EINJ/HEST/BERT/ERST/SDEI/MPAM/PPTT…
getconf PAGESIZE; cat /sys/kernel/mm/transparent_hugepage/enabled
cat /proc/interrupts                    # GICv3/arch_timer/KVM 行
```

## 附录 B：微基准方法学

- **延迟**：循环置换指针链，步长取最近素数（≥n/2）破坏预取器与组预测；`mrs cntvct_el0` 计时
  （100 MHz）；warmup 2 轮 + 2 次测量取最小；工作集 4KB–16MB 对数+细粒度扫点。
- **带宽**：`a[i]+=1` 读改写扫描，20 轮 × 3 次取最大；单线程 C 程序（taskset 仅限定亲和性，
  不产生并行）——多核聚合带宽未测量（perf 受限），已如实标注。
- 源码：`/tmp/cpubench/{lat5.c,bw.c}`（gcc -O2）。
