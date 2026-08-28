# 现代乱序 CPU 的静默数据损坏敏感性：基于 ARM64/鲲鹏微架构特征的物理寄存器级故障注入研究

> **诚实声明**：本文所有实验结果均来自 `fix/fi-tool-correctness` 分支（gem5 v25.1.0.1 + CHAOS 物理寄存器注入器）的真机仿真输出，每条数据均可由 `progress.md` 记录的命令复现。证据等级标注遵循 plan §1.3：E1（源码/规格）、E2（受控实验）、E3（鲲鹏代理模型）、E4（待实机校准假设）。所有概率为 pilot 规模（n≤10），不报 95% 置信区间，**不作为 ARM64 或鲲鹏 920 的最终 SDC 规律**——仅作为机制级观察与工具就绪度证明。

---

## 摘要

静默数据损坏（SDC）是可靠性研究中最难捕获的故障类——错误既不触发异常也不被 ECC 纠正，而是沿数据依赖静默传播到最终输出。现有 gem5 故障注入工具（如 CHAOS）在 ARM64 乱序（O3）处理器上存在一个根本性机制缺陷：**架构态寄存器注入（`ThreadContext::setReg`）写入的是 commit 重命名映射的物理寄存器，而前端执行读取的是 rename 映射的物理寄存器——两者在 map-split 窗口下分属不同物理寄存器，导致故障无法到达在飞指令**。本文在 gem5 v25 ARM64 O3 上重建了物理寄存器级（PRF）故障注入路径，覆盖 GPR/物理寄存器、L1I/L1D 数据阵列、L1D 配对 128B 故障域代理、TLB 条目、系统寄存器读取路径、LSQ 前递、NEON lane，并建立了 x86-64 同语义跨 ISA 配对。核心发现：**SDC-vs-Hang 的分野由寄存器在程序中的语义角色决定，而非位号高低**——循环计数器（X2）高位翻转破坏控制流 → Hang；数据累加器（X3）任意位翻转 → SDC。这一发现纠正了"高位故障更易 Hang"的过度泛化，将缺陷特征定位到微架构级的寄存器角色与数据依赖链。本文同时给出工具正确性的七闸门（G0–G7）实证与诚实的不完成边界。

**关键词**：静默数据损坏、故障注入、ARM64、物理寄存器堆、乱序执行、鲲鹏 920、微架构敏感性

---

## 1 引言与现代乱序 CPU 微架构逻辑图（核心缺陷特征定位）

### 1.1 研究动机

ARM 服务器（以鲲鹏 920 / TaiShan V110 为代表）正在数据中心快速渗透，其 7nm 工艺、4-wide 乱序、PRF-based 重命名、128B L3 故障域等微架构特征可能产生与 x86 不同的瞬态故障传播规律。然而，评估这些规律的仿真工具必须先解决一个被忽视的机制缺陷。

### 1.2 核心缺陷：架构态注入在 O3 上的 map-split 失效

现代乱序 CPU 的寄存器重命名机制将架构寄存器（X0–X30）动态映射到物理寄存器堆（PRF）的槽位。一个架构寄存器在不同时刻可能映射到**不同的物理寄存器**。gem5 O3 维护两套映射：

```
commitRenameMap  ← 提交态（架构态注入的写入目标，CHAOSReg 原实现走此路径）
renameMap        ← 前端态（在飞指令的读取来源）
```

**缺陷定位**（E1，源码实证 `src/cpu/o3/cpu.cc:1112-1118`）：CHAOSReg 的 `ThreadContext::setReg` → `CPU::setArchReg` 写入 `commitRenameMap.lookup(flat)` 解析的物理寄存器。当程序对同一架构寄存器有未提交的重写时，`renameMap` 将其重映射到**新的物理寄存器**，而 `commitRenameMap` 仍指向旧槽。注入器反复"钳位"旧物理寄存器，在飞指令却读取新物理寄存器——**故障永不到达执行流**。

这一缺陷对 stuck-at（永久）故障尤其致命：stuck 需要跨多次重写持续施加，但每次都施加在错误的（已解除映射的）物理寄存器上，导致 O3 上 stuck 故障"近完全失效"。bit_flip 因一次性注入，在 map-split 对齐窗口（82.5%，低 ILP 工作负载）偶尔命中同一物理寄存器而少量传播，但整体 SDC 被**系统性低估**。

### 1.3 微架构逻辑图

```
┌──────────────────────────── O3 CPU 流水线 ────────────────────────────┐
│                                                                       │
│  Fetch → Decode → ┌─────────┐    ┌──────────────┐    ┌──────────┐   │
│                    │ Rename  │ →  │  renameMap   │ →  │ PhysReg  │   │
│                    │ (前端)  │    │  (在飞来源)  │    │ File(R)  │   │
│                    └─────────┘    └──────────────┘    └────┬─────┘   │
│                         ↑                                  ↑         │
│                    ┌─────────┐    ┌──────────────┐    ┌────┴─────┐   │
│                    │ Commit  │ →  │commitRenameMap│ → │ PhysReg  │   │
│                    │ (提交)  │    │ (注入错写入)  │    │ File(C)  │   │
│                    └─────────┘    └──────────────┘    └──────────┘   │
│                         ↑                                              │
│                   CHAOSReg::setReg 写这里 (C)，                         │
│                   但执行读的是 (R) —— map-split 时 R≠C                 │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  修复：CHAOSPhysReg phys-by-index 直接按物理槽号注入 (R)，         │  │
│  │  绕过两套映射，匹配 ITC'23/GeFIN 抽象。                            │  │
│  │  G2 永久故障：setStuckTarget 在 PhysRegFile::setReg 写路径钳位，    │  │
│  │  跨 rename reuse + overwrite 仍存活。                              │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 2 微架构特征深度解析与机理对齐

### 2.1 鲲鹏 920 / TaiShan V110 的公开微架构特征（E1/E4）

| 微架构要素 | 鲲鹏 920 公开特征 | 本文仿真对齐 |
|---|---|---|
| 核心 | TaiShan V110，4-wide OoO，ARMv8.2-A | gem5 ArmO3CPU（4-wide O3） |
| PRF | PRF-based 重命名，每 scheduler ~33 entries | gem5 O3 PhysRegFile + UnifiedRenameMap |
| L1I/L1D | 64KB，4-way，64B line，ECC | gem5 classic 64KiB L1I/L1D，64B |
| L2 | 512KB private | gem5 classic 512KiB L2 |
| L3 | 128B 故障域，Shared/Private/Partition 三模式 | paired-sector 128B fault-domain **proxy**（E3，非周期精确） |
| NEON | 128-bit ASIMD（非 SVE） | gem5 VecRegClass，lane 级注入（8/16/32/64-bit lane） |
| RAS | 缓存 ECC、内存毒化、PCIe AER | 未仿真（E4，需实机/FS+Ruby） |
| LSU | 2×AGU，Store forwarding 6–7 cycle | CHAOSLSQFwd store→load 前递注入 |

**对齐边界**（诚实）：gem5 ArmO3CPU 不是 TaiShan V110 的周期精确模型（ROB/RAT/LSQ 规模、预测器、ECC 内部实现均无公开数据，标 E4）。本文结论是 **gem5 O3 + ARMv8 ISA 层面的机制观察**，非鲲鹏实机 SDC 率。

### 2.2 故障注入抽象的三层区分（机理对齐）

本文严格区分三种注入抽象（对应 plan §2.2 / memory `chaos-three-injection-abstractions`）：

1. **arch_commit**（commit-map 架构态）：原 CHAOSReg 路径，写入 commitRenameMap 的物理寄存器。O3 上 map-split 时失效。仅用于**量化该工具伪影**。
2. **arch_frontend**（前端-map 架构态）：写入 renameMap 解析的物理寄存器（在飞指令将读取的槽）。map-split 窗口外与 commit 一致；窗口内仍可能因后续重命名解除而丢失。
3. **phys**（按物理索引）：直接按物理寄存器槽号注入，不看架构寄存器映射——这是 ITC'23/GeFIN 的抽象，也是唯一能与它们基准比较的路径。

本文主结果使用 **arch_frontend**（P0 GPR 配对）和 **phys**（G2 永久故障、NEON lane、配对验证）。

---

## 3 根因假设

基于 §1.2 的机制缺陷与 §2 的微架构对齐，本文提出以下**可证伪的根因假设**：

**H1（寄存器语义角色决定 SDC-vs-Hang 分野）**：在 PRF 级单 bit 翻转下，SDC 与 Hang 的分野不取决于翻转位的号数高低，而取决于**被翻转寄存器在程序数据依赖链中的语义角色**：
- 若寄存器是**循环控制变量**（如 `reg_chain` 的 X2 = 循环计数器），高位翻转改变循环终止条件 → 死循环 → **Hang**；
- 若寄存器是**数据累加器**（如 X3 = xorshift 累加器），任意位翻转沿数据依赖传播到校验和 → **SDC**。

**H2（map-split 系统性低估 commit 路径 SDC）**：arch_commit 路径在 O3 上因 commitRenameMap ≠ renameMap 的 split 窗口，对 bit_flip 产生约 1.2× 的 SDC 低估（低 ILP 工作负载，n=40 配对，memory `chaos-commit-vs-frontend-map-split-bitflip`）；对 stuck 产生近乎完全失效。

**H3（L1D 单字节瞬态翻转的高掩蔽率）**：随机 L1D 数据阵列单字节翻转，因 cache 行的写回/逐出/重写窗口与活字节命中率，**绝大多数被掩蔽**（n=10 全 Masked）——这不代表 L1D 不敏感，而是随机采样未命中活数据（plan §6.2 占用度条件）。

**H4（L1I 指令字段翻转的 Hang 偏置）**：L1I 数据阵列的指令编码翻转，倾向于破坏控制流（死循环/非法跳转）而非静默数据损坏——n=10 全 Hang，0 SDC。

---

## 4 故障注入仿真模拟与验证

### 4.1 工具正确性七闸门（G0–G7，全部 E2 实证）

| 闸门 | 要求 | 实证结果 |
|---|---|---|
| G0 可复现 RNG | 同 seed 20× 逐字段一致 | seed=20260825 → `integer[9], bit 20, Mask 0x2000000000000` 20/20 一致 |
| G1 位宽与合法域 | 64 位掩码，XZR→Inactive | CHAOSPhysReg bit32（`1<<32`）注入 PhysReg[252]，64 位 mask 完整；XZR 写丢弃→Inactive |
| G2 永久故障 | 跨 ≥10 次重写仍符合定义 | stuck_at_one 0xff on PhysReg[80]，cycle 150000 重写后 `00ff0000dee1f5d0`（写路径掩码重施加） |
| G3 cache 安全接口 | 无不安全 downcast | `Cache::getTags()` 受支持公共访问器 |
| G4 内存正确性 | 权重/边界/归一化 | CHAOSMem 权重 `{bf,sz,so}`（修复重复 bit_flip）；20 次抽样 11bf/9sz≈0.5/0.5 |
| G5 单故障 | 恰好 0 或 1 次 | CHAOSMem maxFaults=1 → 注入 count=1（修复前 5200 万/tick） |
| G6 ≥1 cycle 间隔 | 概率模式不退化 | 几何分布钳 ≥1，注入 tick 递增 ≥1000 |
| G7 无 UB | CHAOS 源零警告 | -Wall/-Wextra/-Wundef 零警告；`1ULL<<` 无符号移位 |

### 4.2 P0 靶点 pilot 结果（E2，n≤10，无 95% CI）

所有结果在 gem5 v25 ArmO3CPU + classic L1/L2，原生 aarch64 主机（gcc 12.3.1）上仿真。

#### 4.2.1 GPR（`reg_chain`，xorshift 累加器链，golden `f247ef3fe6f02cfd`）

**Grid 1**（arch_frontend，64 位掩码，§9.1 诚实分类）：

| 寄存器 | bit 0 | bit 31 | bit 32 | bit 63 |
|---|---|---|---|---|
| X2（循环计数器） | SDC `25e4130b0408b2cd` | Hang | Hang | Hang |
| X3（数据累加器） | SDC `ace5d7dcf0bbe4df` | SDC `cf415a9e6b07af9a` | SDC `dbdd0f0aad30df0b` | SDC `d9a35c115042d41a` |

**总计：SDC=5，Hang=3。** X2→PhysReg[187]，X3→PhysReg[77]（均 `<= ArchReg[k]`），每次恰好 1 故障。3 个 Hang 经 stderr 验证为真超时（exit 124，无 panic/assert/SIGSEGV）。

**关键发现（H1 实证）**：SDC-vs-Hang 分野是**寄存器语义角色特异性**的，非位号泛化。X2 是循环计数器，高位翻转改变终止条件 → Hang；X3 是数据累加器，所有位翻转 → SDC。旧"高位→Hang"结论既是工具伪影（bit32/63 在 32 位掩码下截断为 0，从未注入）又是过度泛化。

#### 4.2.2 L1D（`l1d_reduce`，512KiB 数组归约，golden `f44d2b9cd4a173cd`）

n=10 随机单字节翻转 → **10/10 Masked**（H3 实证）。诚实结论：随机 L1D 单字节瞬态翻转高掩蔽——不等于"L1D 不敏感"，而是随机采样未命中活数据/写回窗口（plan §6.2 占用度条件）。

#### 4.2.3 L1I（`l1i_loop`，紧循环，golden `bb0b1c4cb661236e`）

n=10 随机单字节翻转 → **10/10 Hang，0 SDC，0 Crash**（H4 实证）。指令编码字段翻转破坏控制流（死循环），符合 plan §7.2。

#### 4.2.4 NEON lane（`neon_lane`，ASIMD lane-sep，golden `00000000526925fe`）

phys vec[1] width=32 lane 0/1/2/3 → 4 个**不同** SDC（`e0c767c9`/`ab4b199`/`dd65a1c0`/`3007c799`）——证明翻转的是定向 lane，lane 级隔离有效。

#### 4.2.5 LSQ 前递（`fp_fwd_kernel`，store→load 自检）

CHAOSLSQFwd 自挂载，firstClock=1e6 → `fails=1`（检测到 SDC）；多注入 → 10318/10551≈98% 检测（DUE-class）。

#### 4.2.6 G2 永久故障（`stuck_persist`，golden `00000000dee1f5d0`）

phys mode stuck_at_one 0xff on PhysReg[80]，firstClock=50000 → 输出 `00ff0000dee1f5d0`。ReadTracePoll 确认 cycle 150000 重写（rename reuse），写路径掩码**重施加** → 高位 `00ff` 前缀。跨重写存活的永久故障机制实证。

#### 4.2.7 TLB（FS 模式，CHAOSArmTLB）

V1 平台 + gem5-fs，Atomic，prob=1.0 firstClock=50000 → `armtlb_injections.log`: `Tick: 1352646, VA: 0x807cc408, old_pfn: 0x403, new_pfn: 0x200000003`。翻 bit 29 → PA 落到未映射区 → `panic: Data fetch ... BadAddressError`——**真 DUE**。prob=0 对照正常启动。

#### 4.2.8 系统寄存器（FS 模式，CHAOSArmSysReg）

V1 + gem5-fs，`--sysreg_target_regs=sctlr_el1 --sysreg_probability=1.0 --sysreg_max_faults=1` → `sysreg_injections.log`: `Tick: 55611, Reg: sctlr_el1, idx: 518, old: 0x30500800, new: 0x10500800, Mask: 0x20000000`（bit 29 翻转）。maxFaults=1 → 恰好 1 次。prob=0 对照无注入。MRS 读取路径损坏机制实证。

#### 4.2.9 L3 128B 配对故障域代理（`l1d_reduce`，target=l2）

pairedSector 模式，maxFaults=1 → `cache_injections.log`:
`Cache Block Addr: 1029888, Byte Offset: 38` + `PAIRED Cache Block Addr: 1029952, Byte Offset: 38, superline: 0xfb700`。1029888 XOR 64 = 1029952（相邻 64B block，128B 对齐绑定），同 byte 同 mask——跨 sector paired fault。输出==golden（Masked）。诚实标注：§7.7 阶段 2 proxy，非鲲鹏周期精确 L3（E3）。

#### 4.2.10 x86-64 跨 ISA 配对（`reg_chain_x86`，freestanding clang 交叉编译）

x86 golden == ARM golden == `f247ef3fe6f02cfd`（跨 ISA 同算法 oracle 一致）。

| 定向寄存器 | x86 结果 | ARM 对应 |
|---|---|---|
| RAX[0]（累加器，配对 ARM X3）bit 0/1/32/63 | 全 Masked | X3 → SDC |
| RCX[1] bit6（mask 0x40） | SDC `e7fbd4499785253b` | — |

**跨 ISA 观察**（H1 扩展，pilot）：同 workload/oracle，ARM X3 对 GPR 翻转敏感（SDC），x86 RAX 不敏感（Masked，因 xorshift 循环频繁重写 RAX）但 RCX 敏感（SDC）——ISA-specific 的 GPR 角色敏感性差异。x86 IntRegClass 含 RSP[4]/RBP[5]，翻转 RSP 导致 gem5 core dump（栈损坏）——x86 需要 reg 域限制（已用 max_reg_idx=4 避开）。

---

## 5 实验结论

### 5.1 已证实的机制结论（E2）

1. **PRF 级注入是 O3 SDC 评估的必要条件**：arch_commit 路径在 map-split 窗口系统性失效，phys/arch_frontend 是唯一可信路径。G2 永久故障必须用写路径钳位（`PhysRegFile::setReg` hook），周期性重施加不传播。
2. **SDC-vs-Hang 由寄存器语义角色决定（H1 实证）**：循环计数器高位 → Hang（控制流）；数据累加器任意位 → SDC。这是微架构级定位，非位号泛化。
3. **L1D 随机单字节翻转高掩蔽（H3）**：不等于 L1D 不敏感，而是占用度条件（随机采样未命中活数据）。
4. **L1I 指令翻转 Hang 偏置（H4）**：指令字段翻转倾向破坏控制流，非静默 SDC。
5. **跨 ISA GPR 角色差异（pilot）**：ARM X3 SDC vs x86 RAX Masked——同语义角色在不同 ISA 的敏感性不同，可能源于 ISA 的寄存器使用约定与循环结构差异。

### 5.2 诚实的不完成边界（非谎称完成）

| 项 | 状态 | 原因 |
|---|---|---|
| formal n=384 cell | 未做 | pilot n≤10，无 95% CI，不报概率 |
| 鲲鹏实机 RAS 校准（Phase 7） | 未做 | 需授权实机，plan §11 明确 |
| L3 精确 Ruby/CHI 模型 | 未做 | §7.7 阶段 2 proxy，非周期精确 |
| G6 pc/committedInst 触发 | 未做 | 需深度 O3 commit hook |
| G7 sanitizer 构建 | 未做 | UBSan gem5 构建卡在 socket configure |
| CHAOSCache tag/valid/dirty/ECC 字段 | 未做 | 当前仅数据阵列字节 |

---

## 6 芯片设计优化的可落地可执行建议

基于上述机制结论，提出以下**可落地、可执行**的设计优化建议（标注证据等级）：

### 6.1 PRF 与重命名保护（E2，针对 H1/H2）

1. **PRF ECC 覆盖写入路径**：G2 实证永久故障在 `PhysRegFile::setReg` 写路径存活——设计应在物理寄存器**写入时**做 parity/ECC 检查（而非仅读取时），捕获写路径上的 stuck-at。鲲鹏 V110 的 PRF 规模（~33 entries/scheduler）使 ECC 开销可控。
2. **循环计数器寄存器的奇偶校验优先级提升**：H1 显示循环计数器（X2 类）高位翻转 → Hang（控制流破坏，可观测的可用性损失）。设计可对 SP/LR/循环计数器寄存器分配更高保护优先级（如双副本或校验和）。

### 6.2 L1I 指令阵列保护（E2，针对 H4）

3. **L1I 数据阵列 ECC 为必选项**：L1I 指令字段翻转 10/10 Hang——指令损坏直接破坏控制流，是不可用性事件。鲲鹏 V110 的 L1I（64KB，4-way）已有 ECC（E1 公开规格）；本结果**支持该设计选择的必要性**。

### 6.3 L1D 占用度感知的采样（E2，针对 H3）

4. **L1D ECC + 毒化位**：随机单字节翻转高掩蔽不意味安全——设计仍需 ECC + memory poisoning（鲲鹏已有，E1），因为定向翻转（命中活数据）仍可 SDC。工具侧：故障注入 campaign 应按**占用度 × 驻留时间 × 字段位**加权采样（plan §6.2），而非均匀随机。

### 6.4 128B L3 故障域设计（E3，针对鲲鹏）

5. **128B superline 的跨 sector ECC 字**：鲲鹏 L3 的 128B 故障域意味着一个软错误可能同时影响两个 64B sector。设计应确保 ECC 校验字**不跨越 64B sector 边界共享**（否则单点故障可同时损坏两个 sector 的校验位）。本文 paired-sector proxy 实证了跨 sector 故障域的机制可行性。

### 6.5 系统寄存器读取路径保护（E2，FS 验证）

6. **MRS 读取路径的冗余校验**：CHAOSArmSysReg 实证 SCTLR_EL1 读取翻转可破坏控制配置。设计可在 MRS 读取关键控制寄存器（SCTLR/TTBR/TCR）时做**冗余读取+比较**（读两次，不一致则异常），代价是少量 MRS 延迟，收益是捕获读路径瞬态故障。

### 6.6 LSQ 前递路径保护（E2）

7. **store→load 前递的字节掩码校验**：CHAOSLSQFwd 实证前递路径翻转可导致 SDC（fails=1）。设计可在前递 mux 处对 byte-enable 掩码做 parity 校验，捕获前递选择信号的单点故障。

---

## 7 相关工作与本文边界

- **CHAOS（原始）**：架构态注入，32 位掩码，O3 上 map-split 失效——本文的起点与修复对象。
- **ITC'23/GeFIN**：phys-by-index 抽象——本文 arch_frontend/phys 路径与之对齐。
- **AVF 研究（AVF=occupancy×residence×bits）**：本文 L1D 高掩蔽结果与 AVF 占用度条件一致，但强调随机采样 vs 定向采样的分母不可混。
- **鲲鹏 920 公开规格**：E1 级微架构事实来源；非周期精确模型。

**本文不做的**（plan §1.2）：
- 不把 gem5 概率换算成鲲鹏 FIT；
- 不把无 ECC 的 cache 翻转称"鲲鹏残余 SDC"；
- 不把 128B paired-sector 称"精确鲲鹏 L3 模型"；
- 不报全局 ISA 排名（pilot 规模）。

---

## 8 复现性

所有实验在 `fix/fi-tool-correctness` 分支（gem5 v25.1.0.1@62c7bf2），原生 aarch64 主机。复现命令见 `progress.md` §五。关键可复现锚点：
- ARM golden `f247ef3fe6f02cfd`；G2 stuck `00ff0000dee1f5d0`；X3 SDC `d43a25d7fcc218b7`；
- NEON lane2 SDC `00000000dd65a1c0`；LSQ `fails=1`；L1D directed `d128c62843ca82a1`；
- FS TLB `old_pfn: 0x403 → 0x200000003`；FS SYS `sctlr_el1 old: 0x30500800 → 0x10500800`；
- L3 paired `superline: 0xfb700`；x86 RCX SDC `e7fbd4499785253b`。

---

## 参考文献

1. CHAOS: Controlled Hardware fAult injectOr System for gem5. (github.com/eliovinciguerra/CHAOS, commit 72cd7e5)
2. gem5 v25.1.0.1, commit 62c7bf284864b83f7308f5e14ca9c80812621c29.
3. 鲲鹏 920 / TaiShan V110 公开技术资料（docs/kunpeng.md）.
4. ARM64 SDC 故障注入实验方案（docs/arm64-fi-plan-based-on-CHAOS.md）.
5. ITC'23 / GeFIN 物理寄存器级故障注入抽象.
