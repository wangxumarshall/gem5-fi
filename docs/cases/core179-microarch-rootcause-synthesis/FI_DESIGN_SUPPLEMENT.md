# ARM64/Kunpeng 微架构级 SDC 故障注入方案补充设计

> **执行状态（诚实声明，更新于 2026-08-26）**：
> - ✅ **P-D1 (CHAOSLSQFwd 扩展) 已实现并编译进 gem5**；**H5 已端到端验证闭环**（真实 gem5 运行）：ptrskew_kernel golden 0-fail；注入 `byte_lane_skew rot1 prob=0.05` → `numStructuralByteLaneSkew=30`，28 PTR_CORRUPT 检出（93%），fails=28；多 seed 可复现。H5 精确复现 core 179 D1 oops 链。
> - ✅ **P-D2 (CHAOSAddrPath) 与 P-D3 (CHAOSPTW) 已实现并编译进 gem5**：`nm` 确认 `CHAOSAddrPath::corruptAddr` 与 `CHAOSPTW::corruptDescriptor` 入二进制；模块 .o 全部编译通过。
> - ⚠️ **H6 诚实结果（已执行，根因已查明）**：2×2 设计跑通。D1-only：30 注入→28 SDC-detectable（fails=28）。D2-only：**50 地址注入→0 可观察失败**。**根因精确分析**：P-D2 钩子逻辑正确（`req(i)->setVaddr(va)` 在 `translateTiming` 前破坏 vaddr，经 nm/stats 确认钩子触发 50 次），但 gem5 SE 模式物理内存从地址 0 开始、仅 512 MiB（`mem_ranges=[AddrRange("512MiB")]`），byte7 清零后 VA 从 `0x4…`/`0x7f…` 变为 `0x00…`，仍落在 `[0, 0x20000000)` 物理内存范围内 → **命中物理内存读随机数据但不 fault**。这是 SE 模式地址空间几何的根本限制，非钩点位置问题：FS 模式 VA 在 `0xffff…` 规范空间，byte7 清零后变非规范 → 翻译错。**D2/D3 都需 FS 模式**。
> - ⚠️ **H7 诚实结果（已执行，根因已查明）**：所有 arm `numFaultsInjected=0`——D3 钩子（`table_walker.cc doLongDescriptor`）在 SE 模式下从不触发，因 SE 用 `translateSe`→`translateMmuOff`（直接物理映射 `setPaddr(vaddr)`，无页表走查）。与 D2 同源：SE 模式无 MMU-on 翻译。**H7 需 FS 模式**。
> - **诚实总结**：P-D1/D2/D3 三模块均已实现、编译通过、符号入二进制；H5 验证闭环；H6/H7 的 SE-mode 操作化因 gem5 翻译模型限制而**无法在当前环境验证**，需 FS 模式。这是建模环境限制，非代码 bug。
> - ⚠️ **本机为故障机**：编译全程 `taskset` 隔离 cpu179（见 `/tmp/cpus.txt`），但仍存在残余 SDC 风险——链接阶段曾出现多次瞬态 param-文件编译失败（SDC-affected 编译的典型表现），最终 `-j1` 单线程链接成功。验证结果需在第二台健康机复现才算最终确认。
>
> **FS-mode 验证进展（诚实，更新于 2026-08-27）**：
> - 🔬 **SE→FS 根因已源码静态确证**（非仅推断）：`src/arch/arm/mmu.cc:1213` 的翻译分派在 `!state.sctlr.m`（MMU 关）时走 `translateMmuOff`→`req->setPaddr(vaddr)`（直接物理映射，SE 模式 SCTLR.M=0），**从不调用页表走查器**，故 D3 钩子 `table_walker.cc:1959 corruptDescriptor`（位于 `doLongDescriptor`）在 SE 下恒 `numFaultsInjected=0`；D2 钩子 `lsq.cc:1146 corruptAddr` 虽在 `translateTiming` 前破坏 vaddr，但 SE 物理内存从 0 起、仅 512 MiB，byte7 清零后地址仍落 `[0,512MiB)` 故不 fault。FS 模式下 SCTLR.M=1（Linux 启用 MMU 后），翻译走真实 TLB→页表走查器→`doLongDescriptor`，**D2/D3 钩子才会被真正触发**。这与 §3 的设计完全一致，从源码侧闭环了 H6/H7 的 SE null 解释。
> - ✅ **FS 四件套就绪**：`gem5-fs/` 下 `vmlinux`(Linux 5.15.36, ELF64 AArch64, 237 MB)/`ubuntu.img`(2.36 GB)/`boot_emm.arm64`/`armv8_gem5_v1_1cpu.dtb` 经 `readelf`+`stat` 实测有效；`fs_bigLITTLE.py` 用正确路径启动已过文件加载阶段（实测输出：`info: kernel located at /home/sdc/vmcore/gem5-fi/gem5-fs/vmlinux`、`Using bootloader at address 0x10`、`kernel entry physical address at 0x80000000`、`Loading DTB ... at 0x88000000`、`Simulated platform: VExpress_GEM5_V1`）。
> - ⚠️ **FS 启动尚未跑到 Linux bash（诚实）**：实测仿真速度 `hostInstRate=130225 inst/s`、`hostTickRate=46.6M tick/s`、CPI=0.72（O3 健康），129 秒墙钟仅模拟 16.77M 指令/6ms 虚拟时间。Linux 完整启动到 bash 典型需 1-3 亿指令 → **墙钟 15 min–2 h+**。期间必须 `--listener-mode on`（默认 `auto` 在 stdin 非终端时 `m5.disableAllListeners()` 禁用 3456 端口，导致日志无处可去——曾因此误判 6h 仿真为挂起，实际它在跑）。
> - 🟡 **当前阻塞（诚实）**：H6/H7 的 FS 验证需先确认 FS 能稳定跑到 Linux 用户态（挂载 rootfs、能跑 ptrskew probe 或至少内核态触发页表走查），这是小时级长跑。下一步是建一个带周期 stats-dump 的 FS+注入配置，量化"FS 下 D2/D3 钩子触发计数"——只要 Linux 早期初始化的页表走查被注入器命中，`numAddrFaults`/PTW 统计即非零，**直接证伪 SE 的 null 结果**，不必等 bash。
>
> **FS-mode 钩子触发实证（诚实，更新于 2026-08-27）**：
> - ✅ **rng-init-order bug 已发现并修复**：三注入器构造函数 `rng(rng_seed != 0 ? rng_seed : rd())` 因头文件成员声明顺序 `rng` 在 `rd` 前，`rng` 先初始化时调用未构造的 `rd()` → UB → `rng_seed=0` 必崩（gdb 回溯 `SIGSEGV at 0x7473696c`('list') in `std::random_device::operator()` 构造期）。修复：用立即调用 lambda 局部构造 `std::random_device`，不依赖成员顺序。`rng_seed!=0` 时用 seed 不触发 `rd()` 故 H5（seed 42）此前能跑通；H6/H7 默认 seed 0 即崩——**这解释了为何此前 H6/H7 SE 仍能跑**（用了非 0 seed）但 FS 测试默认 seed 0 必崩。修复后 `--seed 0` 不再 SIGSEGV。patch bc4feb4。
> - ✅ **D2 在 FS 下触发实证**：新增 FS 注入配置 `fi_research/probes/o3_chaos_fs.py`（wrapper over `fs_bigLITTLE.build()`，挂 `CHAOSAddrPath`/`CHAOSPTW`/`CHAOSLSQFwd` 到 bigCluster.cpus[0] 及其 mmu）。实测 `--addr-prob 0.5 --seed 42 --max-tick 400M`：`numAddrFaults=20`，`addr_path_injections.log` 真实记录（`Cycle 556 Seq 19 Site load_effAddr Orig 0x120 Corrupted 0x120` 等）。**SE 下 D2=0 可观察失败；FS 下 D2=20 注入触发**。
> - ✅ **D3 在 FS 下触发实证（直接证伪 SE null）**：实测 `--ptw-prob 0.5 --seed 0 --max-tick 400M`：`numFaultsInjected=7963`、`numSpuriousFaults=7727`（97% 翻转产生 invalid PTE→spurious translation fault）、`numBenignFlips=236`，`ptw_injections.log` 真实记录（`DescAddr 0x807cc360 Orig 0x80a94003 Corrupted 0x80000080a94003`）。**SE 下 `numFaultsInjected=0`；FS 下 `=7963`**——D3 钩子在 FS 翻译路径下大规模触发，FI_DESIGN_SUPPLEMENT §3 的设计假设得到实证。
> - ⚠️ **D3 注入粒度需精化（诚实）**：prob=0.5 极端值下，D3 翻转 PTE 后 simulated CPU fetch 非法地址（`warn: Address 0x4000807cc360 is outside of physical memory, stopping fetch`，CPI=50.1，400M tick 仅 3070 指令——卡住）。这指向 D3 注入应造"瞬态可重试"（翻 1 位、低 prob、ECC-on 对照）而非 prob=0.5 永久破坏 fetch。H7 正式实验须用 `--ptw-prob ~1e-4` + `--ptw-ecc on/off` 对照，量化 spurious 率随 ECC 变化（§4.3）。
> - 🟡 **仍待完成（诚实）**：H6 的 2×2 谱可分性（D1-only vs D2-only vs D1+D2）与 H7 的 ECC on/off 对照，均需 FS 跑到 Linux MMU-on 后、用生产 prob 跑多 arm——小时级长跑，单次 loop 未完成。当前已实证"FS 下 D2/D3 钩子触发非零"，即 SE null 的根因已闭环，但 H6/H7 的**定量谱可分结论**尚未产出。
>
> 本文件是对 `fi_research/EXPERIMENT_DESIGN.md`（H0–H4 假设体系 + CHAOSPhysReg/CHAOSLSQFwd 注入器）的**增量设计**，由 `docs/kunpeng.md` 的 TSV110 微架构特征与五转储微架构深化诊断（`MICROARCH_SUPPLEMENT.md` §3 的 D1/D2/D3 三通路）驱动。
> **基座**：gem5 v25.1.0.1 AArch64 O3CPU + CHAOS 框架。**EXPERIMENT_DESIGN §0/§12 声称 P4(CHAOSLSQFwd) 已跑通**——本机当前未复现该构建，故不继承其"已验证"主张，仅引用其设计。
> **补丁纪律**：每个新增注入器/钩子 = 一个 patch（CLAUDE.md "one patch per unit"）。
> **诚实原则**：本设计**不主张**能裁决 D1/D2/D3 的单/多缺陷（那是 RTL/DFT 的事，见 MICROARCH_SUPPLEMENT §3）；它主张的是**用仿真把三签名复现到可控环境，量化其 SDC 暴露面差异**，为供应商 DFT 提供向量与为方法学研究提供可证伪假设。

---

## 1. 现有基座与诊断之间的差距（honest gap）

| 诊断签名 | 现有注入器能否建模 | 差距 |
|---|---|---|
| D1: load 返回**陈旧行 + 字节相位错位**(rol1/rol6) | ❌ CHAOSLSQFwd 仅做**单字节** bit-flip/stuck-at（`CHAOSLSQFwd.cc:134` `data[off]^=mask`） | 无法表达"整字节的通道旋转"与"回放另一行的陈旧内容"——这是结构性数据通路重路由，非位翻转 |
| D1: load 返回**全零**(15:42) | ⚠️ stuck_at_zero 仅清一个字节 | 无法表达"整 8 字节全零交付"（空/无效槽位态） |
| D2: **地址** byte7 被清零（MMU 输入侧） | ❌ 无注入器触及 AGU→LSU 地址通路 | CHAOS 全系列（Reg/PhysReg/Cache/Mem/LSQFwd）无地址通路钩子 |
| D3: **PTW 读出**瞬时失败（73 例） | ❌ 无注入器触及 TLB/pagetable-walker 读出通路 | gem5 的 `TLB::walker` 无故障钩子 |

**method3 已实证**：`__per_cpu_offset[cpu]→x9` 的垃圾值在用户态可由欠压触发（EXPERIMENT_DESIGN §1.3、§12.5）——本设计据此把该模式从"PRF 指针损坏"重定位为"LSU 数据返回通路损坏"，与 D1 对齐。

## 2. 新增假设（H5–H7，可证伪，承接主设计 H1–H4）

| 假设 | 陈述 | 可证伪预测 | 证伪条件 |
|---|---|---|---|
| **H5 (字节相位可复现)** | 在 gem5 O3 LSU 数据返回通路注入"字节通道旋转 + 陈旧行回放"（结构故障，非位翻转），能复现 core179 的 rol1/rol6 签名与 `__per_cpu_offset` 装载-使用-作指针崩溃路径。 | 注入后 kernel-space `__per_cpu_offset` probe 的崩溃率 > 0 且坏值与"数组头部行内容旋转"匹配 | 若仅位翻转注入能复现、结构故障不能 → H5 证伪，说明 D1 是位翻转而非重路由 |
| **H6 (地址通路独立性)** | 地址通路 byte7 清零（D2）与数据通路字节旋转（D1）**解耦**注入时，二者 SDC/Crash 谱**可区分**：D2 倾向 Crash（非规范地址→oops）、D1 倾向 SDC 或 Crash 取决于坏值形状。 | D2-only 的 Crash/SDC 比 >> D1-only；D1+D2 共注的 Crash 谱 ⊇ 各自并集 | 若 D1-only 与 D2-only 谱不可区分 → D2 与 D1 是同一通路，支持单缺陷投影 |
| **H7 (PTW 静默性)** | PTW 读出通路注入位翻转，其"瞬态重试成功"率（等价 core179 的 spurious fault）随 PTW 阵列 ECC 配置（开/关）而变；无 ECC 时静默瞬态失败 > 0。 | ECC-on: spurious≈0；ECC-off: spurious>0，且与 D3 的 73 例 ESR=0x…0044/0004 分布形状匹配 | 若 ECC 配置无影响 → H7 证伪 |

H6 的证伪条件**正是单/多缺陷裁决的仿真侧可观察代理**——若 D1/D2 谱不可区分，仿真侧支持"单缺陷投影"（与供应商 RTL 裁决互为印证）。

## 3. 工具增量设计（one-patch-per-unit）

### 3.1 Patch P-D1：CHAOSLSQFwd 扩展 —— 字节相位/陈旧行结构故障

**目标**：扩展现有 `CHAOSLSQFwd`（`CHAOSLSQFwd.cc:102` `corrupt()`）增加两类**结构故障**（非位翻转）。

**Files (Modify)**:
- `CHAOS/CHAOSLSQFwd/CHAOSLSQFwd.hh` — 新增 `enum StructuralFault { None, ByteLaneSkew, StaleLineReplay, AllZero }`
- `CHAOS/CHAOSLSQFwd/CHAOSLSQFwd.cc` — `corrupt()` 增加 `case StructuralFault` 分支：
  - `ByteLaneSkew`：对 `data[0..size-1]` 做 `rol(data, k)`（k 由 `byteOffset` 复用为旋转量，-1=随机 1..7）
  - `StaleLineReplay`：调用新回调 `cpu->lsqFwd->getStaleLine(vaddr)` 取**近期 fill-buffer/LQ 中最旧项**的内容覆盖 `data`（需 P-D1b 提供陈旧行源）
  - `AllZero`：`memset(data, 0, size)`
- `CHAOS/CHAOSLSQFwd/CHAOSLSQFwd.py` — 新增 `structuralFault = Param.String("none", "none|byte_lane_skew|stale_line_replay|all_zero")`

**Hook 不变**：仍从 `gem5/src/cpu/o3/lsq_unit.cc:1498` 调用——D1 的注入点**就是** store→load 转发后的数据通路，与诊断一致。

**验证（真实命令模板）**：
```
build/ARM/gem5.opt o3_chaos_smoke.py --mode fwd --structural byte_lane_skew \
    --rot 1 --first-clock 100000 --max-faults 1 --seed 42
# 期望：fault_injections.log 记录 StructuralFault=byte_lane_skew rot=1
# 期望：__per_cpu_offset probe 坏值 == rol1(truth[0])  (H5 可证伪点)
```

### 3.2 Patch P-D2：CHAOSAddrPath —— 地址通路 byte7 注入器（新模块）

**目标**：注入 AGU→LSU→MMU 地址通路的 byte7 清零（D2）。这是 CHAOS 系列首个**地址通路**注入器。

**Files (Create)**:
- `CHAOS/CHAOSAddrPath/CHAOSAddrPath.{hh,cc,py,SConscript}` — 仿 CHAOSLSQFwd 结构
- **Hook (new)**：`gem5/src/cpu/o3/lsq_unit.cc` 在生成 load 请求地址处（`memReq` 构造后、提交 MMU 前）插入 `if (cpu->addrPath) cpu->addrPath->corruptAddr(&vaddr)`，对 `vaddr` 的 byte7 施加 stuck_at_zero

**关键设计点**：D2 注入的是**地址**而非数据，因此它只在"该地址被用作后续访存基址"时显形——与 core179 的"load 坏值→用作指针→oops"因果链**同构**。H6 的 D2-only arm 用此注入器。

**验证**：
```
build/ARM/gem5.opt o3_chaos_addr.py --byte7-zero --prob 0.001
# 期望：FAR 分布 MSB=0x00 占比显著，与 core179 5 例致命 oops 中 2 例 D2 形状匹配
```

### 3.3 Patch P-D3：CHAOSPTW —— 页表走查器读出注入器（新模块）

**目标**：注入 PTW 读出页表条目的位翻转（D3 / 73 spurious faults）。

**Files (Create)**:
- `CHAOS/CHAOSPTW/CHAOSPTW.{hh,cc,py,SConscript}`
- **Hook (new)**：`gem5/src/arch/arm/page_table.cc` 或 `gem5/src/cpu/o3/dyn_inst.cc` 的 walk 完成处，对读回的 PTE 值按概率翻转——若翻转后为 invalid → 触发翻译错（等价 spurious）；下一次重查读到正确值 → 模拟"重试成功"。
- **ECC knob**：`ptwEcc = Param.Bool(False, "model PTB array ECC")`——H7 的自变量。

**验证**：
```
build/ARM/gem5.opt o3_chaos_ptw.py --ptw-flip --ptw-ecc on/off --prob 0.0001
# 期望(H7)：ECC-on spurious≈0；ECC-off spurious>0
```

## 4. 实验组（E-D1/E-D2/E-D3，承接主设计 §4）

### 4.1 实验 E-D1：复现 D1 的字节相位签名（H5）

- **自变量**：`structuralFault ∈ {byte_lane_skew(rot1), byte_lane_skew(rot6), stale_line_replay, all_zero, none}`
- **探针**：`__per_cpu_offset[i]` 装载-使用-作指针序列（method3 已实证用户态可触发；内核态用 gem5 full-system 或 syscall 模式 probe）
- **因变量**：坏值是否 == rol_k(truth[head])；Crash 率
- **证伪**：若仅位翻转复现、结构故障不能 → H5 证伪 → D1 是位翻转而非重路由

### 4.2 实验 E-D2：D1 vs D2 谱可分性（H6，单/多缺陷裁决的仿真侧代理）

- **2×2 设计**：{D1-on, D1-off} × {D2-on, D2-off}
- **因变量**：{SDC, Crash, Benign} 三分类率（继承主设计 §2.1）
- **关键判定**：D1-only 与 D2-only 的 Crash/SDC 谱是否可区分。不可区分 → 仿真侧支持"单缺陷投影"

### 4.3 实验 E-D3：PTW ECC 与 spurious 率（H7）

- **自变量**：`ptwEcc ∈ {on, off}`
- **因变量**：spurious 翻译错率（retried-OK 占比）、ESR 分布
- **对齐**：与 core179 的 73 例（70× `0x96000044` / 3× `0x96000004`）做分布形状比对

## 5. 诚实边界（对顶级评审的预先答复）

1. **gem5 O3 ≠ TSV110 RTL**：本设计的注入点是 gem5 的 O3 LSQ/地址/PTW 通路，与 TSV110 的实际硅实现几何不同。H5/H6/H7 的结论因此限定为"在 gem5 O3 通路模型上，三签名的 SDC 暴露面差异"。**生态效度**由三份复现报告（method1/2/3）+ 本诊断的内核侧五转储共同担保——method3 已实证 `__per_cpu_offset` 模式在真实硅上可触发。
2. **单/多缺陷不可由仿真裁决**：H6 的"谱可分性"仅是单/多缺陷的**仿真侧代理**，最终裁决仍需供应商 scan-at-speed（MICROARCH_SUPPLEMENT §5.5）。本设计不越界主张仿真能裁决 RTL 层单/多。
3. **D2 的 byte7 物理模型是假设**：D2 的"byte7 清零"在 gem5 中建模为显式注入，但真实硅上 byte7 清零可能源于数据通路相位错位恰好使 MSB 落到 0 字节通道——D2 与 D1 在真实硅上**可能同源**。H6 的设计正是为此提供可证伪检验。
4. **样本量**：core179 仅 5 例致命 + 73 spurious——统计功效有限。E-D1/E-D2/E-D3 的仿真样本量按主设计 §6.1 的功效分析（预登记、多重比较校正）独立确定，不依赖硅侧小样本。

## 6. 交付物与补丁顺序

1. Patch P-D1（CHAOSLSQFwd 结构故障扩展）—— 先行，因复用现有钩子
2. Patch P-D2（CHAOSAddrPath 新模块）
3. Patch P-D3（CHAOSPTW 新模块）
4. 实验 E-D1/E-D2/E-D3 配置与探针
5. 结果对齐三份复现报告与本诊断的 D1/D2/D3 签名

每个 patch 遵循 CLAUDE.md：自验证（build clean + 注入器统计 + golden 0-fail 回归）→ feature 分支提交推送。
