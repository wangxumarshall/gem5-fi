# 鲲鹏920（TaiShan V110，ARM64架构，Neoverse N系列）微架构单元SDC故障注入研究和SDC规律研究的实现方案

> **本文定位**：把 `KUNPENG920-微架构SDC分析与故障注入方案.md`（风险分析）落成**可编译、可运行、可复现**的工程方案。每个微架构单元给出：用哪个注入器（已有 / 需新写，附真实文件路径与 hook 点）、campaign 网格、需要的 kernel、评估指标与预期规律、gem5 建模边界与证据等级、工作量估计（补丁数）。文末给出"从结果到芯片设计建议"的方法论与交付物。
>
> **强约束（贯穿全文）**
> 1. **实事求是**：现有工具能力以仓库 `fi` 分支 HEAD `9a4376d`（已并入 `fix/fi-tool-correctness`）实际代码为准，不含未合并分支。
> 2. **可落地**：每个新注入器都指明 hook 文件与行号级位置、SimObject 骨架、参数面；沿用 `CLAUDE.md` 的"一补丁一单元 + 提交前真机自验证"纪律。
> 3. **诚实边界**：gem5 O3 ≠ TaiShan V110 RTL；无 bufferless NoC / HCCS / 周期精确 L3 模型；SE 模式无 MMU-on 翻译（地址通路 / PTW 注入必须 FS）；鲲鹏实机校准需授权机、不在本环境范围。这些**写进方案**，不回避。

---

## 第 0 部分　现状基线（写方案前必须对齐的事实）

### 0.1 已实现并真机验证的注入器（`fi` 分支，7 个）：务必先做验证，确保真的已100%实现。

| 注入器 | 目标 | Hook 点（真实） | 挂载方式 | 闸门状态 | 关键已验证结果 |
|---|---|---|---|---|---|
| **CHAOSReg** | 架构寄存器（`ThreadContext`） | CPU tick 回调 | Python 显式 `board.chaos_reg=` | G0/G1/G5/G7 ✅ | 64 位掩码；`targetRegIdx` 定向；XZR 写→Inactive |
| **CHAOSPhysReg** | O3 物理寄存器堆 | `cpu/o3/regfile.hh`（读写 + read-trace + `setStuckTarget`）、`cpu/o3/free_list.hh`（`isFree` 探活）、`cpu/o3/cpu.hh`（accessor） | Python 显式 `board.chaos_phys=` | G0–G5/G7 ✅ | X3 arch_frontend bit_flip → **SDC 可复现** `d43a25d7fcc218b7`；`vecLaneWidth/Offset` 4 lane→4 SDC；G2 write-path stuck `00ff...` 跨 rename reuse 存活；read-trace `reads_before_overwrite` 闭环 |
| **CHAOSCache** | classic cache 数据字节 | 事件驱动，`injectFault()` 直接遍历 tag store（`getTags()` / `regenerateBlkAddr` / `blk.isValid()`）；`mem/cache/cache.hh:166` 加了 `getTags()` 受支持访问器 | Python，经 `arm_chaos_cache.py` 的 `_pre_instantiate` hook 挂 L1D/L1I/L2 | G3/G4/G5 ✅ | 定向 `targetBlockAddr`+`targetByteOffset` → L1D 活数据 SDC `d128c62843ca82a1`；`pairedSector` 128B superline proxy（`0xfb700`） |
| **CHAOSMem** | `AbstractMemory` 后备存储字节 | `AbstractMemory::access` 路径 | Python `board.chaos_mem=`，挂 `mem_ctrl[0].dram` | G4/G5/G6 ✅ | maxFaults=1 恰好 1 次；首/中/末/单字节边界可达；权重 `{bf,sz,so}` 已修 |
| **CHAOSLSQFwd** | store→load 转发**数据**（转发后 memcpy） | `cpu/o3/lsq_unit.cc:1493–1499`（`if (cpu->lsqFwd) cpu->lsqFwd->corrupt(load_inst->memData, ...)`） | **自挂载**（构造函数 `cpu->lsqFwd = this`） | 部分（mask 仍 `bitset<32>` / 单字节；`-Wswitch` Random 未补） | `fp_fwd_kernel` → 位谱 **100% 尾数 / 0% 符号**，定量吻合 method2（93/0/6） |
| **CHAOSArmTLB** | ARM D-TLB 命中表项 `pfn` | `arch/arm/tlb.cc:164–168`（`if (retval && chaosTLB) chaosTLB->maybeCorrupt(retval, va)`） | **自挂载**（构造函数 `tlb->chaosTLB = this`），`arm_chaos_fs.py` `--chaos_armtlb` 挂 `cpu0.mmu.dtb` | 部分（clock 窗口 advisory） | **FS 真机**：翻 pfn bit29 → PA `0x40000807cc408` 落未映射区 → `panic: BadAddressError` **真 DUE**；`prob=0` 对照正常启动 |
| **CHAOSArmSysReg** | ARM 系统寄存器 MRS 读路径 | `arch/arm/isa.cc:452–457`（`if (chaosSysReg) chaosSysReg->maybeCorrupt(idx, miscRegName[idx], val)`） | **自挂载**（构造函数 `isa->chaosSysReg = this`），`arm_chaos_fs.py` `--chaos_sysreg` 挂 `cpu0.isa[0]` | 部分（白名单 = 小写 `miscRegName`） | **FS 真机**：`sctlr_el1` idx 518 → `old 0x30500800 new 0x10500800`（bit29），maxFaults=1；`prob=0` 对照 0 注入 |

### 0.2 已实现的基础设施：务必先做验证，确保真的已100%实现。

- **闸门纪律 G0–G7**：G0（统一 seed，20/20 重放一致）、G1（64 位掩码）、G2（write-path stuck）、G3（cache 安全接口）、G4（内存权重/边界）、G5（`maxFaults=1` + 证据日志）、G6（≥1 cycle 间隔）、G7（CHAOS 源零警告）。**未完成**：G6 的 `pc/committedInst/event` 触发；G7 的 ASan/UBSan 构建（本环境卡在 gem5 SConstruct socket configure）。
- **`tools/runner.py`（229 行）**：单 manifest → 校验哈希 → 映射到 `arm_chaos.py` 参数 → 跑 gem5 一次 → 从注入日志数 `faults_injected` → 断言 ∈{0,1} → `classify.py` 分类。**未完成**：checkpoint restore、ROI 符号解析、网格采样、Wilson CI、§9.2 完整 provenance 字段。
- **`tools/classify.py`（147 行）**：九类**有序**分类器（SimulatorError→Hang→Crash→Inactive→Masked→SDC），用 stderr 标记 + 退出码 + 16-hex checksum + timeout 区分。
- **`schemas/manifest.schema.json`**：`arm-chaos-fi/v1`，`fault.stage` 已含 `raw_pre_protection / post_check_escape / metadata_or_checker / no_protection_model`；`target.component` enum 目前只有 `gpr/l1i/l1d/l2/memory/physreg/rat`。
- **配置**：`configs/se/arm_chaos.py`（SE 主 harness）、`arm_chaos_cache.py`（L1D/L1I/L2 挂载）、`arm_chaos_fs.py`（FS，stdlib ArmBoard + VExpress_GEM5_V1 + `gem5-fs/` 四件套，kernel 5.15.36 启动已验证）、`x86_chaos.py`（C1 前置）。
- **research harness**：`fi_research/probes/o3_chaos_smoke.py`（裸 `ArmO3CPU`，`numROBEntries=192 / LQ=SQ=32 / numPhysIntRegs=numPhysFloatRegs=256`，可参数化窗口，挂 CHAOSPhysReg + CHAOSLSQFwd）。
- **kernel**（`workloads/directed/`）：`reg_chain`（golden `f247ef3fe6f02cfd`）、`l1d_reduce`（`f44d2b9cd4a173cd`）、`l1i_loop`（`bb0b1c4cb661236e`）、`neon_lane`（`00000000526925fe`）、`fp_fwd_kernel`、`stuck_persist`、`reg_chain_x86`。
- **分析**：`fi_research/bit_spectrum.py`（IEEE754 sign/exp/mantissa/popcount 位谱）、`fi_research/read_trace_stats.py`（Benign/Masked/SDC/Crash 四分类）。
- **假设体系**：`fi_research/EXPERIMENT_DESIGN.md`（H0–H4，预登记）、`docs/cases/core179-microarch-rootcause-synthesis/FI_DESIGN_SUPPLEMENT.md`（H5–H7 + CHAOSAddrPath / CHAOSPTW / 结构化 CHAOSLSQFwd 设计，**原型在 `fi-h6-h7-*` 分支，未并入 `fi`**）。

### 0.3 已在实验分支验证、但未并入主线的能力（要吸收进方案）

来自 `docs/cases/core179-microarch-rootcause-synthesis/FI_DESIGN_SUPPLEMENT.md`（分支 `fi-h6-h7-fs-verify` commit `eb6518d`）：

| 原型 | 做了什么 | 关键发现（诚实） |
|---|---|---|
| **CHAOSLSQFwd 结构化扩展**（P-D1） | `byte_lane_skew`（整字节通道旋转 rol_k）/ `stale_line_replay`（回放陈旧行）/ `all_zero`（整 8 字节清零） | **H5 闭环**：`byte_lane_skew rot1 prob=0.05` → 30 注入、28 检出（93%），复现 core179 D1 的 rol1/rol6 字节相位签名 |
| **CHAOSAddrPath**（P-D2，新模块） | hook load 请求地址生成处，破坏 vaddr 的 byte7 | **SE 模式无效**：SE 物理内存从 0 起、仅 512MiB，byte7 清零后仍落物理范围不 fault。**FS 下有效**：`numAddrFaults=20`，复现"规范内核地址 byte7 清零→非规范"签名 |
| **CHAOSPTW**（P-D3，新模块） | hook `arch/arm/table_walker.cc doLongDescriptor`，翻页表描述符 | **SE 模式恒 0**：SE 走 `translateMmuOff`（`setPaddr(vaddr)`，无页表走查）。**FS 下**：`numFaultsInjected=7963`，`conditionalValidBit` 模式 + 多 seed → **ECC-on spurious≈0 / ECC-off spurious>0**（H7 闭环）；walk 密度：内核态启动期 0.069%（早期 boot 的 10×） |

**结论**：地址通路 / PTW / 结构化转发这三类注入**在 FS 模式下已被证明可行**，方案把它们作为"需从分支 cherry-pick + 补齐闸门纪律 + formal 化"的既有资产，不是从零设计。

### 0.4 环境与工程约束

| 约束 | 事实 | 方案应对 |
|---|---|---|
| **SE 无 MMU-on 翻译** | SCTLR.M=0 → `mmu.cc:1213` 走 `translateMmuOff`→`setPaddr(vaddr)`，从不调页表走查器 | 地址通路（§11 AGU）、PTW（§15）、系统寄存器"生效"路径的注入**必须 FS 模式** |
| **FS 启动慢 / virtio_blk 挂起** | O3 FS 启动到 virtio_blk 阶段易挂；Atomic 慢（~40k inst/s，到 virtio_blk ~25M 指令） | **AtomicSimpleCPU 快速 boot 到 bash → `m5 checkpoint` → 从 checkpoint 切 O3 跑 ROI**；`boot.rcS` 自动触发 checkpoint |
| **本机为故障机（cpu179）** | 编译期出现过瞬态 param 文件编译失败（SDC 典型表现），`-j1` 单线程链接才稳 | 关键结果必须**第二台健康机复现**才算最终确认；campaign 跑在健康机 |
| **gem5 O3 ≠ TSV110 RTL** | ROB/scheduler/LSQ 是 ISA 无关共享 C++；无 bufferless NoC / HCCS / 分区 L3 Tag-Data 分离 / 周期精确 L3 | 逐单元标 **E1/E2/E3/E4**；C2"鲲鹏代理"配置族明确非周期精确；跨 ISA 结论限"可建模子集" |
| **G7 sanitizer 构建受阻** | `scons --with-ubsan` 卡在 socket `accept()` configure 检查 | 放 CI 层；源码已用 `1ULL<<` / `uint64_t mask` / `buf(vbytes)` 修掉已知 UB 点；诚实记录 deferred |
| **无 x86 交叉编译器（aarch64 主机）** | 只有 clang+lld 能产 freestanding x86-64 ELF；C1 跨 ISA 配对受限 | C1 用 clang 交叉编译的 checksum kernel（`reg_chain_x86` 已验证 golden 跨 ISA 逐字节一致）；formal 跨 ISA 是 P3 优先级 |

---

## 第 1 部分　统一实验框架（所有单元共用）

### 1.1 平台配置族

| 配置族 | 用途 | 关键参数 | 结论标签 |
|---|---|---|---|
| **C0 方法学基线** | 验证注入器正确性、G0–G7 复检 | `arm_chaos.py` 默认（64KiB L1 / 512KiB L2 / stdlib SimpleBoard），全 64B | "ARM64-gem5 baseline"，E2 |
| **C2-KP 鲲鹏处理器** | 逐单元 SDC 量化 | 见下表 | "Kunpeng-informed proxy"，E3 |
| **C1 ARM64架构处理器** | ARM vs x86 同语义配对 | `x86_chaos.py` 镜像 C2-KP 的窗口/缓存意图 | "controlled cross-ISA"，E2（可建模子集） |

**C2-KP 的 O3 参数**（依据 `docs/kunpeng.md` 的 TaiShan V110 画像 + 第三方分析；写入一个新配置 `configs/se/kp920_proxy.py` 与 `configs/fs/kp920_proxy_fs.py`）：

```python
# TaiShan V110 4-wide OoO 代理（E3，非周期精确）
cpu.fetchWidth = cpu.decodeWidth = cpu.renameWidth = cpu.issueWidth = \
    cpu.dispatchWidth = cpu.commitWidth = 4          # 4-wide（kunpeng.md）
cpu.numROBEntries      = 128       # "规模适中"；扫描变量之一 {96,128,160}
cpu.numPhysIntRegs     = 160       # 第三方估计 ~128–160；扫描 {128,160,192}
cpu.numPhysFloatRegs   = 192       # 向量/FP，双 FSU
cpu.LQEntries          = 48        # 深 LSQ（弱内存序）；扫描 {32,48,64}
cpu.SQEntries          = 42
# 分布式四调度器（gem5 用统一 IQ 近似；记为 E3 局限）
cpu.numIQEntries       = 66        # ≈ 2×33（kunpeng.md 每调度器 ~33 项）
# 执行端口：3 通用 ALU + 1 复杂（乘除 4cy）+ 2 AGU + 双 FSU
# 用 gem5 FUPool 自定义：IntALU×3, IntMultDiv×1(lat=4), 
#   MemRead×2/MemWrite×2, FloatMemRead, SIMD/FP×2(FADD lat=4, FMADD lat=7)
cache_hierarchy: L1I=64KiB/4-way/64B, L1D=64KiB/4-way/64B,
                 L2=512KiB/8-way/64B private, (L3: classic 共享 L2 充当 / Ruby 精确)
clk = "2.6GHz"
```

> **诚实标注**：gem5 统一 IQ ≠ V110 分布式四调度器；classic cache 无分区 L3 Tag/Data 分离；无 bufferless NoC。这些在对应单元节标 E3/E4。

### 1.2 protection-aware 建模层（跨所有 cache/TLB/mem 单元）

华为不公开 V110 逐结构保护表 → 用 **N1 TRM Table 9-1 作代理**（同代同级 DynamIQ 云核）。实现为 **CHAOSCache / CHAOSMem / CHAOSArmTLB 的一个新参数 `protectionModel`**，在注入后按下表决定该注入的"可观测归宿"：

| 结构 | `protectionModel` 取值 | 注入后处理逻辑（在注入器内实现） |
|---|---|---|
| L1I data | `sed`（代理） | 1-bit：标记"检出→行失效重取"（记 `Corrected`-like，实际 gem5 里让该 block invalidate）；≥2-bit：**不处理，静默**（→ 可能 SDC） |
| L1D / L2 data | `secded_poison`（代理） | 1-bit：撤销注入（`Corrected`）；2-bit：给该 32b/64b 块打 `poison` 标记并允许传播（`DetectedContained` 或 `Latent`）；≥3-bit：静默 |
| L1D / L2 tag | `secded`（代理） | 1-bit：撤销；2-bit：invalidate block + 记 `DetectedContained`（错误恢复中断）；≥3-bit：静默 false-hit |
| L1 iTLB/dTLB | `none`（代理，TRM 明文 flop 无保护） | 不处理，raw 即 escape |
| L2 TLB / walk cache | `parity_interleaved`（代理） | 1-bit（偶/奇独立）：检出→条目失效重走页表（`DetectedContained`）；同奇偶 2-bit：静默 |
| PRF/RAT/ROB/IQ/store buffer | `none`（TRM 未列 = 无保护） | 不处理，raw 即 escape |
| L2 victim / BTB/GHB/PHT / MMU 替换 | `none` | 不处理 |
| DRAM | `secded`（华为 DDR ECC） | 同 L1D data |

**每个 cell 跑两组**：`protectionModel=none`（raw 敏感性，上界）与 `protectionModel=<代理值>`（protection-aware，逃逸概率）。报告两组，画风险反转图。**不换算产品 FIT**（无 raw device rate）。

工作量：CHAOSCache/CHAOSMem/CHAOSArmTLB 各加一个 `protectionModel` 参数 + 注入后处理分支 —— 3 个小补丁。

### 1.3 故障模型（F1–F6 + post-check-escape）

| ID | 模型 | 已支持？ | 实现 |
|---|---|---|---|
| F1 | 单比特瞬态 | ✅ 全注入器 | `faultType=bit_flip` + `faultMask=1<<k` |
| F2 | 局部多位（相邻 2/4/8） | ✅（`bitsToChange>1` 或 `faultMask` 多位） | 生成相邻位掩码 |
| F3 | 间歇突发 | 部分（`probability<1` + `maxFaults>1`） | **新增"数据相关触发"**：仅当目标当前值某位模式命中时注入（模拟 method2 欠压建立时间违例的数据依赖）—— CHAOSPhysReg/CHAOSLSQFwd 各加 `triggerValueMask`/`triggerValuePattern` 参数 |
| F4 | stuck-at（cell/read/write/field/intermittent） | ✅ PRF write-path（`setStuckTarget`）；其它注入器仅"注入一次卡住" | 其它注入器补 write-path 钩子（按单元优先级） |
| F5 | 合法域替换 | ❌ **全部需新增** | RAT 映射→另一合法 physReg；freelist 活寄存器→误标空闲；LSQ 转发源→另一合法 store seqNum；tag→同 set 合法 tag；TLB pfn→另一映射活页 pfn |
| F6 | 延迟/遗漏代理 | ❌ **需新增** | IQ 唤醒提前/推迟 N 拍；LSQ 转发相位偏移 N 槽；漏一次转发/唤醒 |
| — | **post-check escape** | ❌ **需新增** | 在 cache→CPU 响应路径、ECC 校验之后、写 PRF 之前施加掩码（新注入器 `CHAOSL1DForward`，hook `lsq_unit.cc` load 完成回填处，与 `CHAOSLSQFwd` 同点但语义是"已从 L1D 读出的干净数据被通路损坏"） |

### 1.4 结果分类与分母（沿用 `tools/classify.py`，扩 read-trace 四分类）

九类有序：`SimulatorError → Inactive → Corrected → DetectedContained → Crash/DUE → Hang → SDC → Latent → Masked`。
- `N_valid = N_total − N_inactive − N_simerror`；`P_SDC = N_SDC / N_valid`；`P_DUE = (N_crash + N_hang)/N_valid`；`P_escape = (N_SDC + N_latent)/N_valid`；`Reachability = N_valid/(N_total − N_simerror)`。
- **read-trace 四分类**（PRF/RAT/ROB 类单元）：`reads_before_overwrite=0` → Benign（AVF 分母）；`>0` 且输出不变 → Masked；`>0` 且输出变且无异常 → SDC；触发异常 → Crash。用于验证"SDC∣reads>0"在不同单元间是否一致（H3）。

### 1.5 campaign driver（新增，`tools/campaign.py`，扩展 `runner.py`）

现状：`runner.py` 是单 manifest 单跑。需要一个网格驱动器：

```
tools/campaign.py <campaign.yaml>
  campaign.yaml 定义：
    injector: physreg|cache|lsqfwd|renamemap|...
    config: kp920_proxy | kp920_proxy_fs
    grid:                       # 笛卡尔积展开成 cells
      target_index: [2,3,9,19,29]        # 或 range
      bit: [0, 11, 31, 32, 47, 63]
      fault_model: [transient_bit_flip, stuck_at_one]
    n_per_cell: 384             # formal；pilot 用 100
    seeds: base 20260825 + cell_ordinal*1000 + rep   # 确定性、可重放
    protection_model: [none, secded_poison]          # 两组
    workload: {binary, golden_id, roi_begin, roi_end}
  行为：
    1. 为每个 (cell, rep) 生成一份不可变 manifest（写 runs/<campaign>/<cell>/<run_id>.yaml）
    2. 调 runner.py（或直接 gem5），并发度可控（健康机 -j）
    3. 收集九类分类 + read-trace + 位谱 + provenance §9.2 字段 → runs/<campaign>/<cell>/results.jsonl
    4. 每 cell：Wilson 95% CI(P_SDC, P_DUE, Reachability)；保留 ≥5% 重放样本，重放不一致 → 冻结该 cell
    5. 汇总 → artifacts/<campaign>/{heatmap.csv, summary.md}
```

样本量：pilot 每 cell 100（可达率 + 工具错误 + 粗略比例，不排名）；formal 每 cell **384**（最保守比例 95% Wilson ≈ ±5%）；关键低 SDC cell 扩 **663**（≈ ±3.8%）；0 SDC 时 95% 上界 ≈ 3/n。

工作量：`tools/campaign.py`（~400 行）+ `schemas/campaign.schema.json` + `configs/se/kp920_proxy.py` + `configs/fs/kp920_proxy_fs.py` —— 约 4 个补丁。**这是所有 formal 化的前置，最高优先级。**

### 1.6 manifest schema v2 扩展

`target.component` enum 增补：`rat, freelist, rob, iq, exec, fsu, lsq_fwd, l1_tlb, l2_tlb, sysreg, ptw, l3, noc, coherence, memctrl, l1i`。
`target` 增字段：`sub_field`（如 `pfn/ap/asid` for TLB；`src_ready/dst_tag` for IQ；`map_entry/free_bit` for RAT）、`semantic_role`（ABI 角色 / 寄存器语义）。
`fault` 增字段：`f5_substitute_target`（F5 替换目标描述）、`f6_phase_offset`（F6 相位偏移拍数）、`trigger_value_pattern`（F3 数据相关触发）。
`dynamic_context`（§9.2）落地：`mapped_phys_reg, freelist_size, reads_before_overwrite, overwritten_at_cycle, cache_residency, lsq_source_seq, tlb_asid, committed_inst_at_inject`。

---

## 第 2 部分　逐微架构单元工程设计

> 每节结构固定：**A 目标结构与 hook** / **B 注入器（已有 or 新写 + 骨架）** / **C campaign 网格** / **D 需要的 kernel** / **E 评估指标与预期规律** / **F 建模边界与证据等级** / **G 工作量** / **H 验收断言（Agent 完成标准，机器可判）**。
> 优先级沿用风险分析报告：**P0** = §5 RAT/freelist、§7 ROB、§8 PRF、§11 LSU 转发；**P1** = §6 IQ、§10 FSU、§14 L3、§15 TLB、§19 RAS 元分析；**P2/P3** = 其余。

---

### 2.1　§8 物理寄存器堆 PRF（优先级 P0，已有注入器，扩 formal）

**A. 目标与 hook**：整数/向量/flag 物理寄存器堆。Hook 已在 `cpu/o3/regfile.hh`（读写路径 + read-trace + `setStuckTarget` write-path stuck）、`free_list.hh`（`isFree` 探活）、`cpu.hh`（`physRegFile()/physFreeList()/frontRenameMap()` accessor）。

**B. 注入器**：`CHAOSPhysReg`（已实现，7 参数面见 `CHAOSPhysReg.py`）。需**扩展**：
- 加 `protectionModel`（本单元恒 `none`，占位对齐）。
- 加 F3 数据相关触发 `triggerValueMask` + `triggerValuePattern`（模拟 method2 欠压）：`processFault()` 里读到目标物理寄存器当前值，仅当 `(val & triggerValueMask) == triggerValuePattern` 时才注入。
- 加 `semanticRole` 日志字段（ABI 角色），供 campaign 分层。

**C. campaign 网格**（config `kp920_proxy.py`，SE，`--chaos_phys`）：

| 轴 | 取值 | 说明 |
|---|---|---|
| 模式 | `phys`（次品单元抽象）、`arch_frontend`（按架构名经前端 RAT） | 两套分别报 |
| 目标寄存器 | 按 ABI 角色：X0–X7（参数/返回）、X9–X15（临时）、X19–X28（callee-saved）、X29/X30（FP/LR）、"指针类"（复现 method2 的 `x10`） | `arch_frontend` 模式的 `--phys_target_arch` |
| 位段 | bit {0, 11, 12, 31, 32, 47, 48, 63} | 覆盖 [0:11]/[12:47]/[48:63] 三段 + 31/32/63 边界 |
| 故障模型 | F1 bit_flip、F2（相邻 2 位）、F4 write-stuck（`stuck_at_one`/`zero`）、F3（数据相关，`triggerValuePattern` 扫 4 个模式） | |
| 触发 | `first_clock` 定在 ROI 内（cycle 触发已支持；`committedInst` 待 G6） | |
| 向量 PRF | V0–V31 × lane {4×32b, 2×64b, 8×16b} × lane offset | `--phys_reg_class=vector --vec_lane_width/offset` |
| 窗口扫描（H2） | ROB {96,128,160} × PhysIntRegs {128,160,192} × LQ/SQ {32/48/64} | 固定其它轴，单独一组 |

每 cell n=384（关键低 SDC 扩 663）。pilot 先 n=100 过可达率。

**D. kernel**：`reg_chain`（已有，golden `f247ef3fe6f02cfd`）；新增 `ptr_chase_kernel`（链表遍历 → 指针寄存器长存活，复现 method2 的 `find_busiest_group` 遍历调度域）；`cholesky_numeric_kernel`（method1 数值分解列更新，numeric-only vs compute-both 两变体）。

**E. 指标与预期**：
- `P_SDC / P_DUE / Reachability`（Wilson）按 (ABI 角色 × 位段 × 模式) 分层热图。**预期规律**：指针类寄存器 → `P_DUE` 高（method2 签名：垃圾指针→翻译故障）；数据累加器类（X3 已验证）→ `P_SDC` 高，全位段敏感；循环计数器类（X2 已验证）→ 低位 SDC、高位 Hang。
- read-trace 四分类：`P(SDC∣reads>0)` 应与 §5/§7 相近（H3 闭环）；`reads_before_overwrite` 分布重尾性（power-law α<2 → H3 支持）。
- **method2 复现**：F3 数据相关触发下，`ptr_chase_kernel` 的 `P_DUE` + ESR_EL1 DFSC 分布 vs 现场 `0x96000004` level-0。
- **method1 复现**：`cholesky_numeric` 的 numeric-only / compute-both `P_SDC` 比值（现场 ≈4×）。
- 窗口扫描：`d(P_SDC)/d(window) > 0`？（H2）
- protection：本单元 `none`，raw = escape。

**F. 边界/证据**：E2（受控实验）。gem5 O3 PRF ≠ V110 PRF-based 重命名的具体几何；ABI 角色映射到 `arch_frontend` 是"意图对齐"非"硅片对齐"。窗口扫描的绝对值是 E3（代理），趋势是 E2。

**G. 工作量**：CHAOSPhysReg 3 个小扩展补丁（protectionModel 占位、F3 数据相关、semanticRole 日志）+ 2 个 kernel + campaign 配置。已有 pilot 证据（X2/X3 SDC 可复现），**直接进 formal，最高 ROI。**

---

### 2.2　§5 寄存器重命名 RAT + 空闲链表 freelist（优先级 P0，需新注入器）

**A. 目标与 hook**：前端重命名映射表 `frontRenameMap[tid]`（`archReg → physReg`）、`freeList`（空闲物理寄存器）、move elimination、flag rename。**Hook 位置**：`cpu/o3/rename_map.hh`（`SimpleRenameMap::rename() / lookup() / setEntry()`）、`cpu/o3/free_list.hh`（`getReg() / addReg() / isFree()`；`isFree` accessor 已加）。需**新增 2 处 hook**：`rename_map.hh` 的 `setEntry` 后置钩、`free_list.hh` 的 `getReg`/`addReg` 后置钩。

**B. 注入器**：**新写 `CHAOSRenameMap` + `CHAOSFreeList`**（自挂载，仿 `CHAOSLSQFwd`：构造函数 `cpu->chaosRename = this`）。

`CHAOS/cpu/o3/CHAOSRenameMap/`（新目录，ARM/x86 均可，非 ARM-only）：
```python
class CHAOSRenameMap(SimObject):
    cxx_class = 'gem5::CHAOSRenameMap'
    cpu = Param.BaseCPU(NULL, "O3CPU")
    probability = Param.Float(0.0, "per rename-map write probability")
    mode = Param.String("map_bitflip",
        "map_bitflip: flip a bit of the physRegIdx in a map entry | "
        "f5_substitute: point archReg K to another CURRENTLY-ALLOCATED physReg | "
        "f4_field_stuck: pin one map entry to a wrong physReg permanently")
    targetArchReg = Param.Int(-1, "which arch reg's map entry (-1=random)")
    faultMask / firstClock / lastClock / maxFaults / rngSeed / writeLog  # 闸门参数（同 CHAOSLSQFwd）
```
Hook（`rename_map.hh` `setEntry(archReg, physReg)` 之后）：`if (cpu->chaosRename) cpu->chaosRename->maybeCorrupt(tid, archReg, &physRegRef)` —— 对写入的 `physRegIdx` 施加 bit_flip（`map_bitflip`），或替换成另一个"当前不在 freelist（=已分配=活）"的合法 physReg（`f5_substitute`，制造张冠李戴）。

`CHAOS/cpu/o3/CHAOSFreeList/`：
```python
class CHAOSFreeList(SimObject):
    mode = Param.String("mark_free",
        "mark_free: set the free bit of a CURRENTLY-ALLOCATED physReg (→ it "
        "gets re-handed-out → two arch regs share one phys reg → history "
        "residue) | pop_wrong: getReg() returns a wrong-but-legal id")
```
Hook（`free_list.hh` `getReg()` 返回前 / `addReg()` 之后）：对返回的 physReg id 或 free 位图施加损坏。**关键**：`f5_substitute` / `mark_free` 的替换目标必须校验"是合法 physReg 号且当前已分配"，否则退化成 UB（`classify.py` 会记 `SimulatorError`）。

**C. campaign 网格**（`kp920_proxy.py` + `--chaos_rename` / `--chaos_freelist`）：

| 轴 | 取值 |
|---|---|
| RAT 模式 | `map_bitflip`（bit {0..log2(numPhysIntRegs)}）、`f5_substitute`、`f4_field_stuck` |
| freelist 模式 | `mark_free`、`pop_wrong` |
| 目标架构寄存器 | 同 §8 的 ABI 角色分层，重点"跨迭代长存活累加器"（method1） |
| flag rename | NZCV → 物理 flag 寄存器映射（单独 cell） |
| move elimination | `MOV Xd,Xn` 消除时映射错（单独 cell，需 kernel 含大量 MOV） |
| 窗口 | 同 §8 |

**D. kernel**：`cholesky_numeric_kernel`（method1 主 kernel，四要素交错：cdiv 条件分支 + rank-1 update 标量 FMA + 间接地址生成 + 跨内层循环长存活累加器 + 每次 malloc/free 工作区）；对照 `pure_fma / pure_spmv / pure_gather / tri_solve`（method1 已验证这些单独不触发）；`mov_heavy_kernel`（move elimination）。

**E. 指标与预期**：
- **"历史残留"专项**（本节核心，直接对标 method1）：读回值是否 **== 某条已退休 μop 的旧结果 / 某个其它架构变量的当前值**。定义 `P(history_residue) = N(读回值∈{其它活变量值集合}) / N_SDC`。现场 method1 的损坏是"其它计算数据"覆盖 `x[0]` → 这个指标应 > 0 且显著。
- **损坏位数分布**：现场 21–32 bit 多位混叠。F5 映射错应产生"整个寄存器 = 另一个值"（多位），而非单位 → popcount 分布验证。
- **method1 负反馈复现**：`cholesky_numeric` numeric-only 阶段注入 vs symbolic 阶段注入（用 `first_clock` 控制）的 `P_SDC` 比值 ≈ 4×？
- `P_SDC / P_DUE`（Wilson）分层；read-trace `P(SDC∣reads>0)` 与 §8 对比（若一致 → RAT 错与 PRF 错走同一传播；若不一致 → RAT 错是独立机制）。

**F. 边界/证据**：E2。gem5 `SimpleRenameMap` 是 flat 表，V110 具体 RAT 微结构未知（E3 for 绝对值）。`f5_substitute` 的"当前已分配"判据依赖 `physFreeList().isFree()` accessor（已验证可用）。**这是与 method1 对照最直接的一节，也是当前最大工具缺口。**

**G. 工作量**：`CHAOSRenameMap`（.py/.hh/.cc/SConscript + 1 hook）、`CHAOSFreeList`（+ 2 hook）、kernel `cholesky_numeric` + 4 对照 + `mov_heavy` —— 约 6 个补丁。依赖 `campaign.py`。

**H. 验收断言**：① kernel 先行：`cholesky_numeric` 与 4 个对照 kernel golden 各 20 次重放一致；② `f5_substitute` / `mark_free` 连续 ≥1000 次注入 `SimulatorError`=0（合法域校验生效）；③ pilot `map_bitflip` / `mark_free` 各 ≥1 个非 Inactive 结局（可达性非零）。

---

### 2.3　§7 重排序缓冲 ROB + 按序提交（优先级 P0，需新注入器）

**A. 目标与 hook**：ROB 条目（结果值 / done 位 / 异常状态 / 目的物理寄存器号 / 投机标记）、回滚/squash 逻辑、提交阶段 commit RAT 更新。**Hook**：`cpu/o3/rob.cc`（`ROB::retireHead()` / `ROB::squash()`）、`cpu/o3/commit.cc`（`Commit::commitHead()` / `Commit::squashAfter()`）。新增 3 处 hook。

**B. 注入器**：**新写 `CHAOSROB`**（自挂载 `cpu->chaosROB = this`）。
```python
class CHAOSROB(SimObject):
    mode = Param.String("entry_bitflip",
        "entry_bitflip: flip a bit of a ROB entry field (field=result|done|"
        "  exc_status|dest_phys|spec) at distance D from head | "
        "exc_suppress: clear the exception-status bit (→ silently swallow a "
        "  fault that should have raised SError/DUE) | "
        "spec_leak: on a branch squash, RETAIN one wrong-path µop's phys-reg "
        "  write (→ speculative state leak, method1)")
    field = Param.String("result", "result|done|exc_status|dest_phys|spec")
    distanceFromHead = Param.Int(-1, "inject into the entry D slots from the "
        "ROB head (commit point); -1=random. Stratifies 'time-to-commit'.")
    # + 闸门参数
```
`exc_suppress` 模式：`retireHead()` 前若该 μop 有 pending 异常，按概率清掉 → 量化"ROB 异常位翻转把本该 DUE 的 run 变成 SDC"（对应三案例"零上报"的一个可能解释）。
`spec_leak` 模式：`squash()` 时对指定错误路径 μop，**不回滚其物理寄存器写**（保留在 PRF / store buffer）→ 直接建模 method1 的投机状态泄漏。

**C. campaign 网格**：

| 轴 | 取值 |
|---|---|
| mode | `entry_bitflip` × field {result, done, exc_status, dest_phys, spec} / `exc_suppress` / `spec_leak` |
| 距提交距离 D | {0, 8, 16, 32, ROB_size−1}（H2：ROB 越满暴露面越大） |
| 分支密度 | 低 / 高（`spec_leak` 需高分支密度 kernel 制造 squash） |
| 窗口 | ROB {96,128,160} |

**D. kernel**：`cholesky_numeric`（带 cdiv 条件分支制造投机）；`branchy_reduce_kernel`（高分支密度 + 依赖链）；`reg_chain`（基线）。

**E. 指标与预期**：
- `P_SDC` vs 距提交距离 D 曲线（预期单调，D 大 → read-trace 命中率高 → SDC 高）。
- **`exc_suppress` 专项**：`P(DUE→SDC 转化率)` —— 清掉异常位后本该崩溃变静默算错的比例。这是"ROB 异常位对 RAS 逃逸的贡献"的量化，直接支撑 §19 元分析和芯片建议。
- **`spec_leak` 专项**：读回值 == 错误路径 μop 结果的命中率（复现 method1 的"其它计算数据泄漏到 `x[0]`"）。
- read-trace `P(SDC∣reads>0)` 与 §5/§8 对比（H3）。

**F. 边界/证据**：E2。gem5 ROB 的 squash 语义与 V110 回滚状态机不同（E3 for 绝对值）。`spec_leak` 是"人为制造泄漏"，其生态效度靠 method1 现场证据 + §3 的 BPU 联合实验（BPU 触发的泄漏 vs 直接注入的泄漏是否同签名）。

**G. 工作量**：`CHAOSROB`（.py/.hh/.cc/SConscript + 3 hook）+ `branchy_reduce` kernel —— 约 4 个补丁。

---

### 2.4　§11 Load/Store 单元 + store buffer + store→load 转发（优先级 P0，扩已有 + 新增 F5/F6）

**A. 目标与 hook**：store buffer 数据条目、转发地址比较（CAM 匹配）结果、转发源 seqNum、部分重叠字节拼接（跨 16B）、byte-enable/size、AGU 有效地址、ready/replay、独占监视器 FSM。**Hook**：`cpu/o3/lsq_unit.cc:1493–1499`（转发数据，已有）；新增 `lsq_unit.cc` 的转发匹配决策点（`checkViolations` / `read()` 里选 store 的地方）、AGU 地址生成点（load 请求构造后、`translateTiming` 前 —— FS）。

**B. 注入器**：
- `CHAOSLSQFwd`（已有，`corrupt(data, size, vaddr)`）—— **扩展**：
  - mask `bitset<32>` → `bitset<64>`；`-Wswitch` Random case 补（清 G7 遗留）。
  - 加**结构化故障**（从 `fi-h6-h7` 分支 cherry-pick，H5 已验证）：`byte_lane_skew`（rol_k）、`stale_line_replay`、`all_zero`。
  - 加 **F5 转发源替换**：新参数 `mode=fwd_source_sub` —— 在转发匹配决策点，把选中的 store 换成队列中另一个合法 store（同地址范围内或 4K 别名）。
  - 加 **F6 转发相位偏移**：新参数 `phaseOffset`（−2..+2 发射槽）—— 推迟/提前转发时机，复现 method3 的"加一条 no-op ALU → 触发率 100%→10–20%"。
- **新写 `CHAOSAddrPath`**（从 `fi-h6-h7` 分支 cherry-pick，FS 已验证 `numAddrFaults=20`）：hook AGU 地址生成，破坏 vaddr（byte7 清零 / 低位翻转 / F5 换成另一在飞地址）。**SE 无效，FS 有效**（已源码确证）。
- **新写 `CHAOSExMon`**（独占监视器 FSM）：hook `cpu/o3/lsq_unit.cc` 的 exclusive monitor 状态机（`checkSnoop` / `LSQ::SQEntry`），翻 open↔exclusive → 本该失败的 `STXR` 成功。

**C. campaign 网格**（部分 SE / 部分 FS）：

| 轴 | 取值 | 模式 |
|---|---|---|
| 转发数据故障 | F1 bit_flip（byte offset 扫）、F2、结构化 {rol1, rol6, stale, allzero} | SE |
| 转发源选择 | F5 fwd_source_sub（同址 / 4K 别名 / 双候选 store） | SE |
| 转发相位 | F6 phaseOffset ∈ {−2,−1,+1,+2} | SE |
| AGU 地址 | byte7 清零 / 低位翻转 / F5 换址 | **FS**（checkpoint 后切 O3） |
| 独占监视器 | FSM 状态翻转 | SE（LDXR/STXR kernel） |
| 数据相关触发（method2 欠压） | F3 `triggerValuePattern` | SE |

**D. kernel**：`fp_fwd_kernel`（已有，浮点转发自检）；`int_rmw_kernel`（整数 RMW，已有）；`movbe_kernel`（字节交换 store→reload，已有）；新增 method3 的 7 类定向构造（同址转发、部分重叠、4K 别名、双候选 store、未就绪 replay、DMB/DSB、LDXR/STXR）+ 每个"加/不加热路径 no-op ALU"两变体；`ptr_chase_kernel`（AGU 地址通路，复现 method3 D2）。

**E. 指标与预期**（本节与现场对照最密集）：
- **位谱**：SDC 翻转位落尾数/符号比例 + popcount 分布 —— 直接对标 method2/3（float 尾数 85% / double 93% / sign 0–1/562；SVD 单比特中位 3 / GEMM double 中位 28 最大 39）。`bit_spectrum.py` 已可用。
- **相位敏感性曲线**：`P_SDC` vs phaseOffset N —— 复现 method3 的触发率塌方。
- **method3 触发条件复现**：分别去掉"store 推进 / 同 LLC 域 / 跨 cache line"三个条件，`P_SDC` 是否归零（现场：去掉任一 → PASS）。
- **method1 复现**：F5 fwd_source_sub 在 `cholesky_numeric` 上，损坏是否固定在"结果向量首元素"位置 + 多位混叠。
- **AGU byte7（method3 D2，FS）**：FAR 分布 MSB=0x00 占比 + ESR 分布 vs 现场 5 例致命 oops 中 2 例 D2 形状。
- **PRF 持续损坏 vs 转发瞬态损坏的倾向差异**（`EXPERIMENT_DESIGN §12.5` 已有 pilot 观察）：转发损坏 → 瞬态静默 SDC；PRF 损坏 → 持续发散/崩溃。formal 分别统计 {SDC, Crash, Benign}。

**F. 边界/证据**：转发数据 E2（位谱已定量吻合 method2）；结构化故障 E2（H5 已闭环）；AGU/PTW E2（FS 已验证 hook 触发非零）；相位 F6 是"代理"（gem5 O3 发射时序 ≠ V110，E3）。gem5 O3 LSQ 不区分 TSO/weak —— 弱内存序特有的"候选多"只能靠 kernel 构造近似。

**G. 工作量**：CHAOSLSQFwd 扩展（mask 64 位、结构化、F5、F6）约 4 补丁；`CHAOSAddrPath` cherry-pick + 闸门 2 补丁；`CHAOSExMon` 2 补丁；method3 7 类 kernel 约 3 补丁。**已有位谱吻合 + H5 闭环，进 formal 优先级与 §5 并列。**

---

### 2.5　§6 发射队列 / 调度器（优先级 P1，需新注入器）

**A. 目标与 hook**：四调度器条目 src-ready 位、src-tag、dst-tag、唤醒广播、选择/仲裁。**Hook**：`cpu/o3/inst_queue.cc`（`InstructionQueue::wakeDependents()` / `scheduleReadyInsts()` / `addReadyMemInst()`）。新增 2 处 hook。

**B. 注入器**：**新写 `CHAOSIQ`**（自挂载）。
```python
class CHAOSIQ(SimObject):
    mode = Param.String("src_ready_bitflip",
        "src_ready_bitflip: mark a not-ready µop's source as ready (→ uses a "
        "  stale/garbage value) | "
        "tag_sub (F5): a µop's source tag → another in-flight µop's legal tag "
        "  (→ wrong-source wakeup) | "
        "wake_phase (F6): advance/delay a wakeup by N cycles | "
        "wake_omit (F6): drop one wakeup broadcast")
    phaseOffset = Param.Int(0, "F6 wake_phase: cycles to advance(-)/delay(+)")
    # + 闸门参数
```

**C. campaign 网格**：mode {src_ready_bitflip, tag_sub, wake_phase(±1,±2), wake_omit} × 目标调度器 {int, mem, fp} × 触发相位。与 `CHAOSLSQFwd` 的 F6 **联合注入**（发射相位 + 转发）复现 method3。

**D. kernel**：`movbe_kernel` / `int_rmw_kernel`（加/不加热路径 no-op ALU 两变体）；`dep_chain_kernel`（紧依赖链，唤醒-选择压力）。

**E. 指标与预期**：`P_SDC`（Wilson）；**相位敏感性曲线**（wake_phase N vs `P_SDC`，复现 method3 触发率塌方）；"错源唤醒"命中率（tag_sub）；位谱（尾数占比对照 method3）。

**F. 边界/证据**：E2/E3。gem5 统一 IQ ≠ V110 分布式四调度器（`kp920_proxy.py` 用 `numIQEntries≈66` 近似，标 E3）。wake_phase 是时序代理。

**G. 工作量**：`CHAOSIQ`（.py/.hh/.cc/SConscript + 2 hook）+ `dep_chain` kernel —— 约 3 补丁。

---

### 2.6　§10 浮点/向量执行单元（双 FSU）（优先级 P1，扩已有 + 新注入器）

**A. 目标与 hook**：向量 PRF（`CHAOSPhysReg` vector 模式已覆盖）、FSU 数据通路（FMA 对齐移位 / 部分积 / 规格化 / 舍入）、lane 间串扰、FPSR 异常标志、FPCR 舍入模式。**Hook（新）**：`cpu/o3/`执行完成写回，按 `opClass ∈ {FloatAdd, FloatMult, FloatMultAcc, SimdFloat*}` 过滤。

**B. 注入器**：
- `CHAOSPhysReg` vector 模式（已有，`vecLaneWidth/Offset` 4 lane→4 SDC 已验证）—— 覆盖"向量寄存器存储损坏"。
- **新写 `CHAOSFPU`**（自挂载）—— 覆盖"执行单元数据通路损坏"：hook FSU 结果，按 IEEE754 位段（sign/exp/mantissa）注入；`mode=fma_intermediate` 注入对齐后规格化前的中间结果；`mode=rounding_sub`（F5）换舍入方向；`mode=fpsr_suppress` 清浮点异常标志。

**C. campaign 网格**：位段 {sign, exp[high/low], mantissa[high/mid/low]} × 算子 {FADD, FMUL, FMADD, horizontal reduction, shuffle/permute, widen/narrow} × 精度 {FP32, FP64} × {向量 PRF 存储 / FSU 数据通路} 两类分开。

**D. kernel**：`gemm_float_kernel` / `gemm_double_kernel`（复现 method3 GEMM 高密度多比特，中位 12/28）；`svd_iterative_kernel`（复现 method3 SVD 单比特为主，中位 1–3）；`neon_lane`（已有，lane 分离）；`fma_reduction_kernel`（归约树）。

**E. 指标与预期**：
- **位谱**（`bit_spectrum.py`）：sign/exp/mantissa 占比 + popcount 中位/最大 —— 直接对标 method3（float 尾数 85% / double 93% / sign 0–1；GEMM double 中位 28 最大 39；SVD 中位 1–3）。
- ULP 误差 + relative error + task-level 阈值（数值计算关心"是否超容差"）。
- lane × 算子 `P_SDC` 热图；归约放大系数（单 lane 错 → 最终标量相对误差）。
- **向量 PRF 存储损坏 vs FSU 数据通路损坏的签名可分性**：method1 排除"纯 FSU pipe 损坏"，method3 位谱指向"数据通路" —— 两类注入的位谱/传播应可区分。
- `fpsr_suppress` 专项：`P(浮点异常被静默吞掉)`。

**F. 边界/证据**：E2（位谱可对照）。gem5 FSU 是功能模型（无真实对齐移位/部分积微结构）→ `fma_intermediate` 是近似（E3）。鲲鹏 128b ASIMD 无 SVE（`kp920_proxy` 不开 SVE）。

**G. 工作量**：`CHAOSFPU`（.py/.hh/.cc/SConscript + 1 hook）+ 4 kernel —— 约 5 补丁。

---

### 2.7　§12 L1 数据缓存（优先级 P2，扩已有）

**A. 目标与 hook**：数据字节（已有）、tag、valid/dirty/替换/一致性状态（字段级，未做）、ECC 校验后数据锁存（post-check escape，未做）。**Hook**：CHAOSCache 事件驱动遍历 tag store（已有）；post-check escape 需新 hook 在 `lsq_unit.cc` load 完成回填处（与转发同点，语义不同）。

**B. 注入器**：
- `CHAOSCache`（已有，定向 `targetBlockAddr/targetByteOffset`，`pairedSector`）—— **扩展字段级**：加 `targetField ∈ {data, tag, valid, dirty, repl, coh}`，`injectFault()` 里按字段读写 `blk` 的对应成员（tag 用 `f5_substitute` → 同 set 另一合法对齐 tag）。加 `protectionModel`（`secded_poison` 代理，见 §1.2）。
- **新写 `CHAOSL1DForward`**（post-check escape）：hook load 完成回填 `load_inst->memData`，在数据已从 L1D 读出且（模型上）ECC 校验通过之后施加掩码 —— 这条路径 ECC 完全挡不住。

**C. campaign 网格**：字段 {data(定向活数据), tag(F5), valid, dirty, repl, coh} × protection {none, secded_poison} × {random 采样 / 定向驻留活数据} × ECC 粒度 {1-bit, 2-bit(同 32b word), 3-bit}。

**D. kernel**：`l1d_reduce`（已有，golden `f44d2b9cd4a173cd`，驻留 512KiB 数组）；`ptr_chain_kernel`；`struct_field_kernel`（结构体字段）；`crc_state_kernel`。

**E. 指标与预期**：
- `P_SDC / P_DUE / P_Corrected`（Wilson）；**raw vs protection-aware**（SECDED 下 1-bit → Corrected，2-bit → poison/Latent，≥3-bit → SDC；none 下 raw = escape）—— 画风险反转图。
- **post-check escape 专项** `P_SDC`（预期显著高于 raw cache 注入，因 ECC 挡不住）。
- tag F5 的"读到同 set 别的行"命中率。
- 已验证锚点：定向活数据 byte0/byte4 → 不同 SDC（`d128c62843ca82a1` / `c104da9d94a173cd`）。

**F. 边界/证据**：E2。华为 L1D 是否真 SECDED（vs parity）未知 → 两组 protection 都跑，标 E3 for 华为映射。gem5 classic cache 无真实 ECC 逻辑 → protection 是注入器内建模。

**G. 工作量**：CHAOSCache 字段级 + protectionModel 约 3 补丁；`CHAOSL1DForward` 2 补丁；3 kernel。

**H. 验收断言**：① 定向锚点不回归：L1D 活数据 byte0/byte4 仍命中 `d128c62843ca82a1` / `c104da9d94a173cd`；② `secded_poison`：1-bit → `Corrected` 100%、2-bit → poison 事件非零；③ `CHAOSL1DForward` 同点位 `P_SDC` ≥ raw 注入（post-check 上界性质）。

---

### 2.8　§13 L2 缓存（私有 512KB）（优先级 P2，扩已有）

**A. 目标与 hook**：L2 数据/tag（`CHAOSCache` target=l2 已可）、**L2 victim 缓冲（无保护）**、L2 事务队列 TQ 在途请求。**Hook**：CHAOSCache 遍历（已有）；victim 缓冲需 hook `mem/cache/base.cc` 的 `WritebackBlk` / victim 路径。

**B. 注入器**：`CHAOSCache`（target=l2）+ 新增 `targetField=victim`（hook writeback 路径，对正在驱逐的脏行施加故障，`protectionModel=none`）。

**C. campaign 网格**：{L2 data(定向), L2 tag(F5), L2 victim(无保护), TQ 请求地址(F5)} × **L2 size sweep {256KiB, 512KiB, 1MiB}**（量化"大私有 L2 → 长驻留 → 传播概率"）× protection。

**D. kernel**：大工作集 reduction（覆盖 512KiB）；`ptr_chain`（覆盖 L2）。

**E. 指标与预期**：`P_SDC` vs L2 size 敏感性曲线（本节核心产物）；L2 victim 注入的 `P_SDC`（无保护，预期高于 L2 data）；per-active-entry AVF（按 L2 占用加权）。

**F. 边界/证据**：E2/E3。method1 已排除 cache（PMU 差异 <2%），本节是"总体暴露面"评估非"第 179 核根因"。

**G. 工作量**：CHAOSCache victim 字段 2 补丁 + kernel + L2 size sweep 配置。

---

### 2.9　§14 L3 / LLC（Cluster 切片，Tag/Data 分离，三模式）（优先级 P1，需 Ruby/CHI）

**A. 目标与 hook**：L3 Tag（分区模式在 Cluster 侧）、L3 Data（NoC 附近）、HHA 一致性目录（owner/sharer/state）、分区边界、Cluster 切片路由。**gem5 classic cache 建不了这些** → 需 **Ruby/CHI**。

**B. 注入器**：
- **短期代理**：`CHAOSCache` `pairedSector` 模式（已实现，把共享 L2 当"L3"，128B superline proxy，`0xfb700` 已验证）—— 只能做"128B 故障域跨 sector"这一维度。
- **完整**：**新写 `CHAOSCHI`**（hook Ruby/CHI 的目录 + 响应通道）。按 set/way/field 注入 L3 Tag/Data/coherence state；F5 owner/sharer → 合法但错误的核 ID；hook CHI 事务响应数据。

**C. campaign 网格**：{L3 Tag(F5), L3 Data, HHA owner/sharer(F5), 一致性 state, 分区边界} × 三模式 {Shared, Private, Partition} × protection {none for Tag/state, secded for Data}。多核（≥1 Cluster = 4 核）。

**D. kernel**：producer-consumer（一核写一核读，验证一致性）；false sharing；跨 Cluster pointer chase；method3 的"同 LLC 域 store→reload"。

**E. 指标与预期**：单写多读一致值违规率（HHA 注入 → 读者读旧值）；L3 Tag F5 的"读到同 set 别的行"命中率；三模式 `P_SDC` 对比；传播时延（注入到读者读到错值的周期数）。

**F. 边界/证据**：**E3/E4**。gem5 Ruby/CHI ≠ 鲲鹏 HHA/分区 L3（Tag-Data 物理分离、bufferless NoC 附着都建不了）。`pairedSector` proxy 是 E3，明确标"128B fault-domain proxy 非周期精确"。

**G. 工作量**：`CHAOSCHI`（Ruby/CHI SLICC 集成，工作量大，~8 补丁）+ 多核 FS 配置。**建议先用 `pairedSector` 出初步结果，`CHAOSCHI` 作为独立子项目排期。**

---

### 2.10　§15 地址翻译（iTLB/dTLB/L2 TLB/页表走查器/系统寄存器）（优先级 P1，扩已有 + FS）

**A. 目标与 hook**：dTLB/iTLB 条目（pfn/AP/XN/AttrIndx/nG/ASID）、L2 TLB、页表走查器在途状态、系统寄存器白名单。**Hook 已有**：`arch/arm/tlb.cc:164`（TLB hit → `chaosTLB->maybeCorrupt`）、`arch/arm/isa.cc:452`（MRS 读 → `chaosSysReg->maybeCorrupt`）。PTW 需新 hook `arch/arm/table_walker.cc doLongDescriptor`（`fi-h6-h7` 分支已做 `CHAOSPTW`）。**全部 FS 模式**（SE 无 MMU-on）。

**B. 注入器**：
- `CHAOSArmTLB`（已有，pfn bit_flip，FS DUE 已验证）—— **扩展**：
  - `mode=pfn_to_mapped_page`（F5）：翻 pfn → **另一个已映射活页的 pfn**（需查页表找合法活页）→ 制造**静默 SDC** 而非崩溃（现在只做了"翻到未映射区 → DUE"）。
  - 加属性位旋钮 `targetField ∈ {pfn, ap, xn, attridx, ng, asid}`。
  - I-TLB 挂载（`cpu0.mmu.itb`）。
  - `protectionModel=none`（L1 TLB 代理无保护）。
- `CHAOSArmSysReg`（已有，`sctlr_el1` FS 已验证）—— **扩展**：白名单铺开到 `ttbr0_el1,ttbr1_el1,tcr_el1,mair_el1,vbar_el1,contextidr_el1,nzcv`；加 `mode=value_to_legal`（F5，翻到仍合法的值 → 静默 SDC）。
- **新写/cherry-pick `CHAOSPTW`**（`fi-h6-h7` 分支已验证 `numFaultsInjected=7963`，`conditionalValidBit` 模式 + 多 seed → ECC-on spurious≈0 / ECC-off >0）：hook `table_walker.cc doLongDescriptor`，翻页表描述符；`ptwEcc` 参数（H7 自变量）。

**C. campaign 网格**（**FS，checkpoint 后切 O3 或 Atomic**）：

| 轴 | 取值 |
|---|---|
| dTLB | {pfn→未映射(DUE), pfn→映射活页(F5, SDC), AP, XN, AttrIndx, nG, ASID} |
| iTLB | pfn / 属性 |
| L2 TLB | 条目 pfn / parity 代理 |
| PTW | 描述符位翻转 {单 bit XOR + 条件注入(仅 0b01 PTE), clearValidBit} × ptwEcc {on, off} |
| 系统寄存器 | {ttbr0/1, tcr, mair, sctlr, vbar, contextidr, nzcv} × {bitflip, value_to_legal(F5)} |
| method2 三根因区分 | 同一"x10 垃圾指针→翻译故障"分别用 CHAOSPhysReg(PRF 读出) / CHAOSAddrPath(AGU) / CHAOSArmTLB(翻译) 注入，比对 ESR/故障 PC/x10 形态 |

**D. kernel**（FS 用户态或内核态）：内核调度域链表遍历（复现 method2 `find_busiest_group`）；context switch / fork-exec / 页迁移；权限微基准；`ptr_chase`。

**E. 指标与预期**：
- **"pfn → 活页" cell 的 `P_SDC`**（静默读写别的页 —— 最危险路径的量化）。
- **"pfn → 未映射" cell 的 `P_DUE`** + ESR_EL1 DFSC 分布（对照 method2 `0x96000004` level-0）。
- **PTW ECC 对照**（H7，已闭环）：`ptwEcc=on` spurious≈0 / `off` spurious>0；多 seed 平均（分支已有 5-seed 数据：on 全 0，off 1–4）。
- **method2 三根因匹配度**：三种注入的 panic 签名（ESR / 故障 PC / x10 值形态）与现场相似度打分。
- AP 位注入的"静默越权访问"率；ASID 注入的跨进程隔离违规率。
- 系统寄存器按白名单字段分层报 escape。

**F. 边界/证据**：E2（FS hook 触发已验证）。FS 启动慢 → **checkpoint 策略必需**（Atomic boot to bash → `m5 checkpoint` → 从 checkpoint 切 O3/Atomic 跑 ROI）。PTW walk 密度：内核态启动期 0.069%（够采样，不必到 bash）。`fi-h6-h7` 分支的 CHAOSAddrPath/CHAOSPTW 需 cherry-pick 到 `fi` + 补齐闸门。

**G. 工作量**：CHAOSArmTLB 扩展（F5 活页、属性位、I-TLB）约 3 补丁；CHAOSArmSysReg 白名单铺开 + F5 约 2 补丁；CHAOSPTW cherry-pick + 闸门 + H7 formal 约 3 补丁；FS checkpoint 流水线 2 补丁。

---

### 2.11　§2 前端取指 + L1I（优先级 P3，已有注入器）

**A. 目标与 hook**：L1I 数据字节（`CHAOSCache` target=icache 已可）、L1I tag、取指对齐逻辑。

**B. 注入器**：`CHAOSCache`（target=icache，定向 `targetBlockAddr/targetByteOffset` 已验证 L1I 循环块 51392）—— **扩展**：`targetField` 支持按**语义字段**分层（opcode 位 / Rn·Rm·Rd 域 / 立即数域 / 条件域 —— 需把 32b A64 指令编码字段映射表内建）；`protectionModel ∈ {sed, secded}` 两组（验证"L1I 是否 SED 决定双比特是否静默"）。

**C. campaign 网格**：语义字段 {opcode, Rn, Rm, Rd, imm, cond} × protection {sed, secded} × {data, tag(F5)} × {1-bit, 2-bit}。

**D. kernel**：`l1i_loop`（已有，golden `bb0b1c4cb661236e`，固定 PC 区间已知 A64 序列循环）。

**E. 指标与预期**：`P_SDC / P_DUE / P_Hang`（Wilson）按语义字段分层（预期：imm 域 SDC 占比最高，opcode 域 Crash/Hang 最高 —— 已有 pilot：L1I 定向 → Hang）；SED vs SECDED 两组 `P_SDC` 差值（量化"L1I 是否 SED"对静默率影响）。

**F. 边界/证据**：E2。华为 L1I 保护类型未知（两组都跑，E3 for 映射）。method1 已排除取指路径（本节是总体暴露面）。

**G. 工作量**：CHAOSCache 语义字段映射 + protectionModel 约 3 补丁。

---

### 2.12　§9 整数执行单元（优先级 P3，需新注入器）

**A. 目标与 hook**：ALU 结果、乘法器部分积、移位器、NZCV 标志、转发网络。**Hook（新）**：`cpu/o3/`执行完成写回，按 `opClass ∈ {IntAlu, IntMult, IntDiv}` 过滤。

**B. 注入器**：**新写 `CHAOSExec`**（自挂载）—— hook 执行结果，按 `opClass` 过滤，对结果/标志施加掩码；进位位/部分积位按位段（[0:11]/[12:47]/[48:63]）分层。

**C. campaign 网格**：opClass {IntAlu, IntMult(乘除端口), IntDiv} × 位段 {低/中/高} × {结果, NZCV 标志} × {bit_flip, stuck_at}。

**D. kernel**：整数 reduction；`MADD` 链；`SMULH` 高位乘法；`ADDS→B.cond` 条件链。

**E. 指标与预期**：位谱（整数结果 SDC 翻转位落低/中/高位段）；乘除端口 vs 简单 ALU 的 `P_SDC` 比值；条件标志注入的"SDC : 控制流 Crash"比；**对照确认整数路径 `P_SDC` 显著低于 §10 FSU 与 §11 转发**（印证 method1 "整数路径完好" + `Veritas` "整数加法器 SDC 低几个数量级"）。

**F. 边界/证据**：E2。gem5 ALU 是功能模型（无真实进位链/部分积树）→ 位段注入是近似（E3）。

**G. 工作量**：`CHAOSExec`（.py/.hh/.cc/SConscript + 1 hook）+ 4 kernel —— 约 4 补丁。

---

### 2.13　§3 分支预测 BPU（优先级 P3，需新注入器，重点是间接路径）

**A. 目标与 hook**：BTB 目标 PC、GHB 历史、返回栈、间接预测器。**Hook（新）**：`cpu/pred/`（`BPredUnit::lookup()` / `BTB::update()` / `ReturnAddrStack`）。

**B. 注入器**：**新写 `CHAOSBPU`**（自挂载）—— F5 替换预测目标/方向。**重点不是 BPU 本身产 SDC，而是它喂给后端的错误投机流是否泄漏**（method1 机理的一半）。

**C. campaign 网格**：{BTB 目标 PC(F5), 返回栈栈顶(F5), 间接预测器目标(F5), 方向位} × 联合观测（注入后同时监控：是否被 squash / 错误路径是否发生投机 store-load / squash 后正确路径架构态是否 == golden）。

**D. kernel**：难预测分支循环 + 紧跟 store→load 依赖链（复现 method1 的 cdiv + rank-1 update 交错）。

**E. 指标与预期**：`P(squash 后架构态 == golden)`（预期接近 1；显著 < 1 即"投机状态泄漏"发现）；错误投机路径的 store 数量分布；`P_SDC∣发生了错误投机 store`；**与 §7 ROB `spec_leak` 注入结果对照**（判断"BPU 触发的泄漏"与"直接注入 ROB 的泄漏"是否同一签名）。

**F. 边界/证据**：E2。BPU 结构（BTB/GHB/RSB/间接）是 gem5 `TournamentBP` 等，非 V110 两级预测器（E3 for 绝对值）。method1 已排除 BPU（PMU 差异 <2%），本节主要验证"间接泄漏路径"。

**G. 工作量**：`CHAOSBPU`（.py/.hh/.cc/SConscript + 1 hook）+ 联合观测逻辑 + kernel —— 约 3 补丁。**可与 §7 ROB 合并一轮。**

---

### 2.14　§4 译码单元（优先级 P4，需新注入器）

**A/B**：**新写 `CHAOSDecode`**（hook `cpu/o3/decode.cc`），对 μop 的 `srcRegIdx / destRegIdx / 立即数 / opClass` 施加 F1/F5（寄存器编号 → 另一合法编号 0–30）。

**C. campaign**：{srcRegIdx, destRegIdx, imm, opClass} × {bit_flip, F5}。**D. kernel**：`reg_chain`。**E. 指标**：`P_SDC / P_DUE`；"译码错寄存器编号"与 §5 "RAT 映射错"两组的位谱/read-trace 签名对比（能否区分）。**F**：E2，结构小。**G**：`CHAOSDecode` ~2 补丁。低优先级，可最后做或跳过。

**H. 验收断言**：① `reg_chain` golden `f247ef3fe6f02cfd` 不回归；② 寄存器编号替换域 {0–30} 校验后 `SimulatorError`=0。

---

### 2.15　§16 bufferless 双环 Mesh NoC（优先级 P2，需 Garnet，E3/E4）

**A/B**：**新写 `CHAOSNoC`**（hook gem5 **Ruby + Garnet** 的 flit 传输 / 路由计算）。把 bufferless 双环近似为 Garnet 拓扑（**标 E3/E4，明确非鲲鹏精确 NoC**）。参数 `mode ∈ {payload_bitflip, route_sub(F5), flit_delay(F6), deflect_force}`；配置 Garnet 为无缓冲 + 偏转路由模式，对比"有缓冲"配置的拦截率差异。

**C. campaign**：{报文数据 payload, 路由/目的字段(F5), QoS/MPAM, 偏转决策} × {bufferless, buffered} 对比 × 多核 + 满载合成负载（制造 NoC 拥塞）。

**D. kernel**：全对全通信；跨 Cluster 数据搬运。

**E. 指标**：**bufferless vs buffered 的 `P_SDC` 比值**（量化"无缓冲吸收"对 SDC 的贡献 —— 本节核心产物）；报文 payload 注入 `P_SDC`（若无 CRC，raw = escape）；路由字段注入的"送达错误节点"率与死锁率；满载拥塞下报文在环上停留周期数 vs `P_SDC`。

**F**：**E3/E4**。gem5 Garnet ≠ 鲲鹏 bufferless 双环。**G**：`CHAOSNoC` Garnet 集成 ~6 补丁。独立子项目排期。

---

### 2.16　§17 HCCS 跨 Die 一致性（优先级 P2，需多 NUMA + CHI，E3/E4）

**A/B**：扩展 `CHAOSCHI`（§14）/ 新写 `CHAOSHCCS`（hook 跨节点 CHI 事务与目录）。gem5 双 NUMA 节点模拟 2 Compute Die。参数 `mode ∈ {link_payload(模拟 CRC 逃逸的多比特模式), hha_owner_sub(F5), coh_state_stuck(F4)}`。

**C. campaign**：{Hydra 链路数据(CRC 逃逸), HHA 跨 Die 目录 owner/sharer(F5), NUMA 路由(F5), SLLC 跨 Die 状态} × 跨节点负载。

**D. kernel**：跨 NUMA producer-consumer；跨节点 pointer chase；跨节点原子（LSE far atomic）。

**E. 指标**：跨节点单写多读一致值违规率；Hydra 数据注入的 CRC 逃逸 SDC 率（注入 CRC 检不出的模式）；协议不变量违规；跨 Die 传播时延。

**F**：**E3/E4**。gem5 CHI ≠ 鲲鹏 HCCS/Hydra/SLLC。**G**：`CHAOSHCCS` ~6 补丁。与 §14 同批排期。

---

### 2.17　§18 内存控制器 + DDR（优先级 P3，扩已有）

**A/B**：`CHAOSMem`（已有，后备存储字节）—— **扩展**：加 `mode ∈ {backing_byte(已有), addr_map_sub(F5), ecc_logic_fault}`。`addr_map_sub`：PA → channel/rank/bank/row/col 映射错（换成另一合法 DRAM 坐标 —— 绕过所有 cache tag）。`ecc_logic_fault`：在 `CHAOSMem` 内实现一个 SECDED 编解码器，注入其"漏检 / 误纠"逻辑。`protectionModel=secded`（华为 DDR ECC）。

**C. campaign**：{DRAM 字节(定向), 地址映射(F5), ECC 生成逻辑, ECC 校验逻辑(漏检/误纠), 读/写队列条目} × protection × {1-bit, 2-bit, 3-bit}。

**D. kernel**：`STREAM`；随机 pointer chase；写后立即读回验证。

**E. 指标**：**地址映射错误的 `P_SDC`**（读写到错误 DRAM 位置，绕过 cache tag，预期高且极静默）；**ECC 逻辑错误的 `P(漏检) / P(误纠)`**（量化"ECC 逻辑本身不可靠"对静默率的贡献）；raw vs protection-aware vs "ECC 逻辑故障"三档对比。

**F**：E2（后备存储）/ E3（地址映射、ECC 逻辑，gem5 无真实 DRAM controller 微结构）。method1 已排除内存 ECC（EDAC=0）。

**G**：CHAOSMem 地址映射 + ECC 逻辑约 3 补丁。

**H. 验收断言**：① 原锚点不回归：maxFaults=1 恰好 1 次、首/中/末/单字节边界可达；② `addr_map_sub` 后读回 ≠ 写入（错位命中可判）；③ 内建 SECDED 单测三档：1-bit 纠对 / 2-bit 检出 / ≥3-bit 静默。

---

### 2.18　§19 RAS 机制逃逸（优先级 P1，元分析 + 小注入器）

**A/B**：**新写 `CHAOSRAS`**（hook commit 阶段异常/SError 处理 + 错误记录寄存器写路径 + poison 传播）。参数 `mode ∈ {exc_suppress(与 §7 ROB 共用逻辑), errrec_bitflip(ERR* 寄存器字段 → 误定位), poison_lose(毒化位在无 poison 结构边界丢失)}`。**主体是元分析**：跑完 §2–§18 所有 formal cell 后，对每个 cell 按"该结构是否在 V110（代理）的 RAS 检测范围内"打标。

**C. campaign**：{ROB 异常位(exc_suppress), ERRSTATUS/ERXADDR 字段(bitflip), poison 位(在 store buffer/PRF 入口丢失)} + 元分析（无新注入）。

**D. kernel**：在 §7/§11 的有向注入基础上叠加 RAS 观测。

**E. 指标**（本节产出直接支撑芯片建议）：
- **RAS 逃逸率**：`P(有效注入产生错误传播 且 无任何 RAS 记录 / 无 SError / 无 EDAC)`，按结构分层（预期："RAS 范围外结构"逃逸率 ≈ 100%）。
- **ROB 异常位 → DUE-to-SDC 转化率**。
- **ERR* 翻转 → 误定位率**（记录的单元 ≠ 真实注入单元）。
- **毒化丢失率**。
- **元分析产出**：**V110（代理）SDC 的"逃逸集合"分解饼图** —— RAS 范围外结构 / SED 双比特 / ≥3-bit / post-check escape / ECC 逻辑故障各占多少 → 直接对应"哪些结构最该加保护"的芯片建议。

**F**：E2（逃逸机理）/ E3（V110 RAS 覆盖假设用 N1 代理）。**不使用鲲鹏内建 EINJ**（method1 已确认现场无 EINJ 痕迹，且 EINJ 只测上报不改数据）。

**G**：`CHAOSRAS`（.py/.hh/.cc + 2 hook）+ 元分析脚本 `tools/ras_escape_analysis.py` —— 约 4 补丁。**跑在所有其它单元 formal 完成之后。**

---

## 第 3 部分　执行计划（依赖排序、分阶段）

### 3.1 阶段划分

| 阶段 | 内容 | 交付 | 依赖 | 估计工作量 |
|---|---|---|---|---|
| **S0 前置（1–2 周）** | ① `fi` HEAD 强制 regen params 干净重建 + P0 GPR pilot 复现（堵 progress.md 诚实缺口）② `tools/campaign.py` + `schemas/campaign.schema.json` ③ `configs/se/kp920_proxy.py` + `configs/fs/kp920_proxy_fs.py` ④ manifest schema v2 ⑤ protection-aware 建模层（CHAOSCache/Mem/ArmTLB 各加 `protectionModel`） | campaign 驱动器 + 鲲鹏代理配置 + 两组 protection | 无 | ~10 补丁 |
| **S1 P0 formal（3–5 周）** | §8 PRF（扩 + formal）、§5 RAT/freelist（新 `CHAOSRenameMap`+`CHAOSFreeList` + formal）、§7 ROB（新 `CHAOSROB` + formal）、§11 LSU 转发（扩 CHAOSLSQFwd + cherry-pick CHAOSAddrPath + formal） | 四个 P0 单元的 n=384 网格 + Wilson CI + 与 method1/2/3 对照 | S0 | ~20 补丁 + campaign 跑批 |
| **S2 P1 formal（4–6 周）** | §6 IQ（新 `CHAOSIQ`）、§10 FSU（新 `CHAOSFPU`）、§15 TLB/SYS/PTW（扩 + cherry-pick + FS checkpoint 流水线）、§14 L3（`pairedSector` 初步） | P1 单元 formal；FS checkpoint 流水线可用 | S1 | ~18 补丁 |
| **S3 P2/P3（3–4 周）** | §12 L1D 字段级 + post-check escape、§13 L2 + victim + size sweep、§2 L1I 语义字段、§9 整数执行、§3 BPU、§18 内存控制器 | 其余单元 formal | S1 | ~16 补丁 |
| **S4 系统级（独立子项目，6–10 周）** | §14 `CHAOSCHI`（Ruby/CHI）、§16 `CHAOSNoC`（Garnet）、§17 `CHAOSHCCS`（多 NUMA） | 系统级 formal（E3/E4） | S2 | ~20 补丁 |
| **S5 元分析 + 建议（2–3 周）** | §19 `CHAOSRAS` + `tools/ras_escape_analysis.py`；汇总所有单元结果 → 逃逸集合分解 → 芯片设计建议报告 | 最终报告 + DFT 向量 + AVF 图谱 | S1–S4 | ~4 补丁 + 分析 |
| **S6 健康机复现（贯穿）** | 所有关键结果在第二台健康机复现 | 复现确认清单 | 每阶段 | — |
| **S7 实机校准（授权后，不在本环境）** | 鲲鹏实机 RAS/ERR*/SEA/CPER/EDAC 枚举，把 E3/E4 假设更新为经证实/被否证 | 实机校准报告 | 授权机 | — |

### 3.2 关键工程流水线

**SE campaign（P0 大部分、P2/P3）**：
```
tools/campaign.py campaigns/<unit>.yaml
  → 展开网格 → 每 cell 384 rep
  → 每 rep: 生成 manifest → build/ARM/gem5.opt kp920_proxy.py --<injector> ... 
  → 收集: 九类分类 + read-trace + 位谱 + §9.2 provenance
  → 每 cell: Wilson CI, 5% 重放校验
  → artifacts/<unit>/{heatmap.csv, summary.md}
并发: 健康机 -j<N>（每 gem5 进程 ~1 核 ~2GB）
```

**FS campaign（§15 TLB/SYS/PTW、§11 AGU、系统级）**：
```
1. Atomic boot: kp920_proxy_fs.py --cpu Atomic --script boot_ckpt.rcS
   boot_ckpt.rcS: 启动到 bash → m5 checkpoint → m5 exit
2. 从 checkpoint 切 CPU: --restore-checkpoint cpt.<tick> --cpu O3(或 Atomic)
   注入器在 restore 后挂载，firstClock 相对 checkpoint tick
3. ROI 内单故障 → 收集 → 分类（FS 的 Crash = kernel panic / Oops；用 raw socket 3456 抓 Linux 日志）
```

### 3.3 补丁纪律（沿用 CLAUDE.md）

每个注入器 / hook / kernel = 一个补丁。提交前：`scons -C CHAOS/gem5 build/ARM/gem5.opt -j16` 零新增警告 + 真机跑受影响行为贴真实输出 + 跑一个不相关回归（`reg_chain` golden `f247ef3fe6f02cfd`）。**故障机风险**：关键补丁在健康机复现后才算最终确认。

---

## 第 4 部分　从结果到芯片设计建议（方法论 + 交付物）

### 4.1 "SDC 逃逸集合分解"方法论

跑完所有单元 formal 后，把总 SDC 按"逃逸机理"归因（§19 元分析）：

```
总 P_SDC(V110 代理, workload w) 
  = Σ_unit [ Reachability(unit) × P_SDC(unit, w, protection-aware) × weight(unit) ]

其中 weight(unit) ≈ 该结构的"未受保护状态位数 × 占用率 × 平均驻留周期"
（用 gem5 stats 的 occupancy / residence 计数估计）

逃逸机理归因（每个 SDC 事件打标）：
  A. RAS 检测范围外结构（PRF/RAT/ROB/IQ/store buffer/L1 TLB/L2 victim）→ raw = escape
  B. SED-only 结构（L1I data 代理）的 ≥2-bit
  C. 任意结构的 ≥3-bit（超 SECDED 能力）
  D. post-check escape（ECC 校验后数据通路）
  E. ECC 逻辑自身故障（漏检/误纠）
  F. 毒化传播丢失
```

产出一张**逃逸集合分解饼图**（按 workload 分组）+ 一张**逐单元"保护投资回报"排序表**：

| 结构 | 当前保护（代理） | `P_SDC` 贡献 | 加保护的边际收益 | 加保护的成本估计 | 建议优先级 |
|---|---|---|---|---|---|
| （由 formal 结果填充） | | | | | |

### 4.2 三类交付物

**对芯片厂（华为海思 / DFT 团队）**：
1. **DFT 测试向量**：把复现 method1/2/3 的定向 kernel（`cholesky_numeric`、method3 7 类转发构造、`ptr_chase`）+ 其触发条件（满载 / 特定发射相位 / 跨 cache line 推进）整理成**量产筛选向量**——method1 已证明 libc-only MRU 可作量产筛选。附每个向量的"预期健康核行为 vs 次品核签名"。
2. **"最该加保护的结构"排序**（4.1 的表）：基于 `P_SDC` 贡献 × 逃逸机理，给出"若只能给 N 个结构加 ECC/parity，选哪 N 个"的排序。**预期结论方向**（待 formal 验证）：乱序后端（PRF/RAT/ROB）+ L1 TLB 是"RAS 范围外 + 高贡献"的重灾区，优先级高于再加固已有 SECDED 的缓存。
3. **位谱指纹库**：每个单元的 SDC 位谱（sign/exp/mantissa 占比、popcount 分布）→ 供 RTL/scan-at-speed 侧做故障定位比对（"现场看到这种位谱 → 大概率是这个单元"）。
4. **电压/相位敏感性数据**：F3 数据相关触发 + F6 相位偏移的 `P_SDC` 曲线 → 量化"欠压 X mV 使某单元 SDC 率上升多少"，供电压裕量 / AVS 策略设计。

**对云厂商（用 鲲鹏 的云 / openEuler）**：
1. **AVF 图谱**：`target × field × bit-role` 的 SDC/Crash/Masked/Detected 热图 → 指导"高危指令序列复制 / 校验插桩"（选择性冗余，只保护高 AVF 结构涉及的热路径）。
2. **负载敏感性**：哪些负载模式（长依赖链 + 条件分支 + 间接寻址交错 / 紧 store→load + 跨 line 推进）最易触发 → 运行时监控 / 调度规避。

**对学术界**：
1. **传播闭环方法论**：`reads_before_overwrite` 四分类把 AVF 分母拆细（Benign / Masked / SDC / Crash），使 AVF/SDC 比率可解释、可跨研究对比 —— 相对 GeFIN/MaFIN/ITC'23 的增量。
2. **合法域替换（F5）+ 相位偏移（F6）故障模型**：把"位翻转以外的、逻辑决策层的故障"（错源转发、映射张冠李戴、相位竞态）做成可复现的注入原语。
3. **protection-aware 分层 + 逃逸集合分解**：用厂商保护表（或 N1 代理）把 raw 敏感性和 protection-aware 逃逸概率分开报的规范。
4. **仿真-现场对照的生态效度范式**：位谱定量吻合（method2 的 93/0/6）、触发条件复现（method3 的三必要条件）、负反馈复现（method1 的 4×）作为"仿真忠实度"的可证伪检验。

### 4.3 诚实的结论边界（写进最终报告）

- 所有 `P_SDC` 是 **gem5 O3 + C2-KP 代理**下的**条件概率**，不是鲲鹏产品现场 FIT。无 raw device rate / ECC coverage / 部署暴露量 → **不换算产品 FIT**。
- 系统级（L3 分区 / bufferless NoC / HCCS）结论是 **E3/E4**，需实机 / RTL / 厂商资料校准。
- "最该加保护的结构"排序是**基于代理保护表（N1 Table 9-1）的推断**；若 V110 实际保护表不同（例如乱序后端已有 parity），结论需按实际表重估。
- 单/多缺陷不可由仿真裁决（`FI_DESIGN_SUPPLEMENT §5`）；本方案主张的是"把三签名复现到可控环境 + 量化 SDC 暴露面差异 + 为 DFT 提供向量"，不越界。
- 本机为故障机 → 关键结果必须第二台健康机复现。

---

## 附录 A：新注入器清单与 hook 点汇总

| 注入器 | 状态 | Hook 文件 : 位置 | 自挂载字段 | 依赖 |
|---|---|---|---|---|
| CHAOSPhysReg | 已有，扩 | `cpu/o3/regfile.hh` / `free_list.hh` / `cpu.hh` | Python 显式 | — |
| CHAOSRenameMap | **新** | `cpu/o3/rename_map.hh` : `setEntry()` 后 | `cpu->chaosRename` | free_list `isFree` accessor（已有） |
| CHAOSFreeList | **新** | `cpu/o3/free_list.hh` : `getReg()` / `addReg()` | `cpu->chaosFreeList` | — |
| CHAOSROB | **新** | `cpu/o3/rob.cc` : `retireHead()` / `squash()`；`commit.cc` : `commitHead()` | `cpu->chaosROB` | — |
| CHAOSIQ | **新** | `cpu/o3/inst_queue.cc` : `wakeDependents()` / `scheduleReadyInsts()` | `cpu->chaosIQ` | — |
| CHAOSLSQFwd | 已有，扩（64b mask / 结构化 / F5 / F6） | `cpu/o3/lsq_unit.cc:1493–1499`（已有） | `cpu->lsqFwd`（已有） | — |
| CHAOSAddrPath | 分支原型，cherry-pick | `cpu/o3/lsq_unit.cc` : load 请求地址生成 / `lsq.cc` translateTiming 前 | `cpu->addrPath` | **FS 模式** |
| CHAOSExMon | **新** | `cpu/o3/lsq_unit.cc` : exclusive monitor FSM | `cpu->chaosExMon` | — |
| CHAOSL1DForward | **新**（post-check escape） | `cpu/o3/lsq_unit.cc` : load 完成回填 `memData`（ECC 后） | `cpu->chaosL1DFwd` | — |
| CHAOSFPU | **新** | `cpu/o3/`执行完成写回（`opClass` 过滤 Float*） | `cpu->chaosFPU` | — |
| CHAOSExec | **新** | `cpu/o3/`执行完成写回（`opClass` 过滤 Int*） | `cpu->chaosExec` | — |
| CHAOSBPU | **新** | `cpu/pred/bpred_unit.cc` : `lookup()` / `BTB::update()` | `cpu->chaosBPU` | — |
| CHAOSDecode | **新**（低优先级） | `cpu/o3/decode.cc` : μop 生成后 | `cpu->chaosDecode` | — |
| CHAOSArmTLB | 已有，扩（F5 活页 / 属性位 / I-TLB） | `arch/arm/tlb.cc:164–168`（已有） | `tlb->chaosTLB`（已有） | **FS 模式** |
| CHAOSArmSysReg | 已有，扩（白名单铺开 / F5） | `arch/arm/isa.cc:452–457`（已有） | `isa->chaosSysReg`（已有） | **FS 模式** |
| CHAOSPTW | 分支原型，cherry-pick | `arch/arm/table_walker.cc` : `doLongDescriptor` | `walker->chaosPTW` | **FS 模式** |
| CHAOSCache | 已有，扩（字段级 / protectionModel / victim / 语义字段） | 事件驱动遍历 tag store（`getTags()` 已有） | Python，`_pre_instantiate` hook | — |
| CHAOSMem | 已有，扩（地址映射 / ECC 逻辑） | `AbstractMemory::access`（已有） | Python `board.chaos_mem` | — |
| CHAOSCHI | **新**（大） | Ruby/CHI 目录 + 响应通道 | SLICC 集成 | **Ruby build + FS** |
| CHAOSHCCS | **新**（大） | 跨节点 CHI 事务 + 目录 | — | **多 NUMA + Ruby** |
| CHAOSNoC | **新**（大） | Garnet flit 传输 / 路由计算 | — | **Ruby + Garnet** |
| CHAOSRAS | **新** | `cpu/o3/commit.cc` 异常处理 + ERR* 寄存器写路径 | `cpu->chaosRAS` | 所有单元 formal 完成 |

## 附录 B：与三份现场证据的对照实验索引

| 现场案例 | 主对照单元 | 复现实验 | 关键指标 | 章节 |
|---|---|---|---|---|
| **method1**（Cholesky → `x[0]` 多位混叠，状态泄漏，numeric-only 4×） | §5 RAT/freelist、§7 ROB `spec_leak` | F5 映射替换 + freelist 活寄存器误标空闲 + ROB squash 泄漏，在 `cholesky_numeric` 上 | 历史残留命中率、损坏位数分布、numeric/compute-both `P_SDC` 比值 ≈4×、损坏位置是否固定在结果向量首元素 | §2.2 / §2.3 |
| **method2**（欠压 + STL → `x10` 垃圾指针 → level-0 翻译故障 → panic） | §8 PRF（F3 数据相关）、§11 AGU、§15 TLB | 同一"x10 垃圾指针→翻译故障"分别用 CHAOSPhysReg / CHAOSAddrPath / CHAOSArmTLB 注入 | ESR_EL1 DFSC 分布 vs `0x96000004`、故障 PC、x10 值形态、三根因匹配度打分 | §2.1 / §2.4 / §2.10 |
| **method3**（LSU 转发时序相位竞态，位谱尾数 85–93%/符号免疫，加 no-op → 触发率塌方） | §11 LSU 转发（F5/F6 + 结构化）、§6 IQ（F6） | store→load 转发 F5 错源 + F6 相位偏移 + 结构化 rol_k，在 movbe/mrn_rmw/GEMM/SVD 上，"加/不加热路径 no-op" 两变体 | 位谱（尾数/符号/popcount）对照 method3、相位偏移 N vs `P_SDC` 曲线、去掉三必要条件任一 → `P_SDC` 归零 | §2.4 / §2.5 |

---

## 附录 C：Agent 任务卡模板与 `AGENT_TASKS.md` 格式

### C.1 任务卡模板（一段 YAML，可直接作为 Agent 的完整任务输入）

```yaml
id: S1-PRF-01                      # <阶段>-<单元>-<序号>
section: "2.1"                     # 本方案章节，Agent 必读该节全文再动手
title: CHAOSPhysReg 加 F3 数据相关触发
context:                           # 必读文件（含锚点），缺一不开工
  - CHAOS/cpu/o3/CHAOSPhysReg/*    # 现有实现（7 参数面）
  - configs/se/arm_chaos.py        # 挂载与参数映射
  - 本方案 §2.1 B/C/E 小节
action: |                          # 精确到文件:函数:参数
  processFault() 读出目标物理寄存器当前值后，仅当
  (val & triggerValueMask) == triggerValuePattern 才执行注入；
  新参数 triggerValueMask / triggerValuePattern（Param.UInt64）。
assert:                            # 机器可判，全过才算完成
  - cmd: scons -C CHAOS/gem5 build/ARM/gem5.opt -j16
    expect: 零新增警告
  - cmd: 重跑 §0.1 X3 anchor（arch_frontend, bit_flip）
    expect: 命中 SDC d43a25d7fcc218b7，同 seed 重放 2 次一致
  - cmd: 同配置 prob=0 对照
    expect: faults_injected=0 且 checksum=f247ef3fe6f02cfd
  - cmd: triggerValuePattern 设为不命中模式
    expect: faults_injected=0
patches: 1                         # 补丁数上界，超限即拆卡重报
notes: ""
```

### C.2 `AGENT_TASKS.md` 行格式与状态规则

每卡一行：`| 卡ID | 章节 | 标题 | 状态 | 分支 | 补丁数 | 断言 | 备注 |`

- 状态 ∈ `todo / doing / blocked / done / verified`；`断言` 列记 `n/m 通过`；`备注` 列贴关键输出摘要、健康机复现证据、open question。
- 表头下第一行固定为 `S0-00`（§0.1/§0.2 复验卡）；任何后续卡在其 `done` 前不得开工。

---
