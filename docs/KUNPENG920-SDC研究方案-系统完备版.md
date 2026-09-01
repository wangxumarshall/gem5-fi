# 鲲鹏920（TaiShan V110）微架构 SDC 故障注入、规律与抗 SDC 设计研究方案

> **文档定位**：本文是基于 `fi-wangxu` 分支**当前源码真实状态**深度核查后撰写的系统完备研究方案，覆盖四个维度：① 微架构单元 SDC 故障注入研究；② SDC 规律研究；③ SDC 诊断建议（openEuler 系统日志，作为注入平台的反哺接口）；④ 对芯片设计者的抗 SDC 微架构改进建议。目标同时服务于**顶级学术研究**（论文骨架与可证伪贡献点）与**产业落地工具**（gem5-fi 故障注入平台 + 抗 SDC 微架构设计指导）。
>
> **诚实第一原则（贯穿全文）**：本文每一处"已有/已验证"能力以 `fi-wangxu` 工作树**实际源码**为准，已逐注入器实读核查（证据见 §0.3 与附录 A）。凡标注"待实现"的能力绝不谎称已有。原《KUNPENG920-的SDC…详细方案…md》中与源码不符的若干声明，本文已在 §0.4 逐条修正——这是实事求是的起点，不是附注。
>
> **双轨诉求**：学术要顶（对标 Veritas/PinDrop/SEVI，可证伪假设体系 + 仿真-现场对照生态效度范式）；产业要实（注入平台为主产出，芯片设计建议指向"如何设计更能抵抗 SDC 的微架构"，而非 DFT 测试向量）。

---

## 第 0 章　文档定位、源码真实状态与诚信修正

### 0.1 文档关系

| 来源 | 处置 |
|---|---|
| 原《KUNPENG920-的SDC…详细方案…md》（1070 行，未入库的工作树文件） | 本文是其**诚信修正 + 系统重组版**：吸收其有效骨架（四维度、F1–F6 故障模型、campaign 设计、openEuler 七步诊断），修正其与源码不符的声明（§0.4），删除其将侧分支能力误标为"主线已有"的表述 |
| `docs/cases/core179-microarch-rootcause-synthesis/paper_zh.md` | 已有的 core179 五转储取证论文骨架（D1/D2/D3 三路径）。本文**引用其现场签名**作为仿真-现场对照靶子，不重复其取证叙事；本文范围更宽（全微架构单元，非仅 core179） |
| `docs/arm64-sdc-STATUS.md` + `docs/ARM SDC故障注入阶段性进展报告` | 已有的工具正确性闸门（G0–G7）与 P0–P3 阶段进展。本文继承其闸门纪律，不重述其 commit 级 provenance |
| `docs/hypothesis/ARM64-SDC-uArch.md` + `docs/hypothesis/cpu.md` | 上游风险分析与 x86-vs-ARM64 微架构对比。本文引用其"为什么"，不重复其风险清单 |

### 0.2 三条强约束（沿用 CLAUDE.md 纪律，全文贯穿）

1. **实事求是**：所有"已有/已验证"以 `fi-wangxu` 工作树实际源码为准（核查结论见 §0.3 与附录 A）。每个结论标注证据等级 E1–E4（§1.3）。
2. **可落地**：每个新注入器给出 hook 文件:行号、SimObject 骨架（Python 参数面 + C++ 要点）、SConscript、挂载方式、验证命令与机器可判 assert。一补丁一单元 + 提交前真机自验证 + 推送 `fi-wangxu`（非 main）。
3. **诚实边界**：gem5 O3 ≠ TaiShan V110 RTL；SE 模式无 MMU-on 翻译（地址通路/PTW/系统寄存器注入必须 FS）；无 bufferless NoC / HCCS / 周期精确 L3；保护表用 Noverse N1 TRM Table 9-1 代理。

### 0.3 分支与源码真实状态（fi-wangxu，核查日期 2026-08-30）

**核查方法**：逐注入器实读 `.py/.hh/.cc/SConscript`；在 vendored gem5 源码树 `CHAOS/gem5/src/` 中 grep 确认 hook 接线；`git log --all` 追溯被删除文件的历史；实跑 `gem5.opt` 验证构建与锚点（§5 已验证锚点表）。

#### 0.3.1 当前工作树真实存在的注入器：**核查时 7 个，现已 13 个**（+CHAOSAddrPath `ffd041e` + CHAOSRenameMap `c5c8c96` + CHAOSFreeList `379e11c` + CHAOSPTW `de48432` + CHAOSROB `7d0756d` + CHAOSIQ `f7a5d72`）

> **2026-08-30 核查时**主线工作树有 7 个注入器（下表）。**S1-5b（`ffd041e`）新增 CHAOSAddrPath**、**S1-2（`c5c8c96`）新增 CHAOSRenameMap**、**S1-3（`379e11c`）新增 CHAOSFreeList**、**S2-5c（`de48432`）新增 CHAOSPTW**、**S1-4（`7d0756d`）新增 CHAOSROB**、**S8-1（`f7a5d72`）新增 CHAOSIQ**，主线现 13 个。下表保留核查时状态以存史；新增注入器见 §A.2 与 §5.2/§5.3/§5.4/§5.5/§5.7。

| 注入器 | 目标单元 | Hook 位置（已核实） | 范式 | 真实参数面（已核实） |
|---|---|---|---|---|
| **CHAOSReg** | 架构寄存器（ThreadContext） | 自调度 attackEvent | C（Python 显式） | 64位 faultMask、rngSeed、targetRegIdx、XZR 跳过（maxRegIdx=31） |
| **CHAOSPhysReg** | O3 物理寄存器堆 int/fp/vector | `regfile.hh` 读/写+setStuckTarget；`cpu.hh:478-489` accessor | B（状态注入） | `injectionMode{phys,arch_frontend,arch_commit}`、`regTargetClass{int,fp,vector,both}`、`vecLaneWidth/Offset`、64位 faultMask、write-path stuck（G2） |
| **CHAOSCache** | classic cache 数据字节 | 事件驱动 `getTags()`（G3 安全接口） | C（`_pre_instantiate`） | 64位 faultMask、`targetBlockAddr/targetByteOffset` 定向、maxFaults（G5）、≥1cycle 间隔（G6） |
| **CHAOSMem** | AbstractMemory 后备存储字节 | `AbstractMemory::access` Packet RMW | C | 闭区间 `[start,end]`（G4）、故障类型权重修复、64位 |
| **CHAOSLSQFwd** | store→load 转发数据 | `lsq_unit.cc:1493-1499`（`cpu->lsqFwd`） | A（自挂载） | ✅ D2 已修 `0ae28fe` + structuralFault 已补齐 `8320daf`（byte_lane_skew/all_zero 复现 core179 D1）；stale_line_replay/fwd_source_sub/phaseOffset 待写 |
| **CHAOSArmTLB** | ARM D-TLB 命中表项 pfn | `arch/arm/tlb.cc:164-168`（`tlb->chaosTLB`） | A（自挂载，FS） | bit_flip/stuck_at_zero/stuck_at_one；**无 targetField/protectionModel/pfn_to_mapped/value_to_legal（待扩展）** |
| **CHAOSArmSysReg** | ARM 系统寄存器 MRS 读值 | `arch/arm/isa.cc:39,452-457` + `isa.hh:179-180`（`isa->chaosSysReg`） | A（自挂载，FS） | bit_flip/stuck_at_zero/stuck_at_one/random；`targetRegs` 白名单（按 miscRegName 解析）；**无 value_to_legal(F5)（待扩展）** |

> **核查结论**：`CHAOS/` 下实际只有 7 个注入器目录（CHAOSReg, CHAOSPhysReg, CHAOSCache, CHAOSMem, CHAOSLSQFwd, CHAOSArmTLB, CHAOSArmSysReg）。

#### 0.3.2 原方案声称"已有 8 个、含 CHAOSAddrPath/CHAOSPTW 来自 main 并入"——**失实，已修正**

- `git ls-tree fi-wangxu` 与 `git ls-tree origin/fi` 均**不含** CHAOSAddrPath/CHAOSPTW 目录。`grep -rn "CHAOSAddrPath\|CHAOSPTW\|chaosAddr\|chaosPtw" CHAOS/gem5/src/` **零匹配**——vendored gem5 树中也无任何 hook 残留（"cleanly removed"，非孤儿引用）。
- `git log --all -- CHAOS/CHAOSAddrPath/ CHAOS/CHAOSPTW/` 显示这两个目录的**唯一** commit 是 `201eac6 fi(P-D2/P-D3): implement CHAOSAddrPath + CHAOSPTW`，该 commit 位于**侧分支**（`origin/fi-h6-h7-fs-verify` / `origin/fix/paper-review-v1-honesty-hardening` 等），**从未并入 `fi` 或 `fi-wangxu` 主线**。
- `git merge-base fi-wangxu origin/fi = 9a4376d`，`fi..fi-wangxu` 仅 1 个 commit，`fi-wangxu..fi` 为空——即 fi-wangxu 是 fi 的直接后继，两者工作树一致地**不含** AddrPath/PTW。
- **诚实修正**：CHAOSAddrPath（AGU 地址通路，P-D2）与 CHAOSPTW（页表走查器，P-D3）原方案写作时在主线均不存在；本文统一标注为"待实现"。**S1-5b 已完成 `ffd041e`：CHAOSAddrPath 已实现并入主线**；**S2-5c 已完成 `de48432`：CHAOSPTW 已实现并入主线**（见 §A.2）。原方案把侧分支能力误标为"主线已有"，本文不继承该误标。

#### 0.3.3 原方案声称"CHAOSArmSysReg 在任何分支都不存在、待新写"——**失实，已修正**

- `CHAOS/CHAOSArmSysReg/` 完整存在（.cc 220 行 / .hh 88 行 / .py 40 行 / SConscript）；git 历史 `997557a Phase3/SYS: CHAOSArmSysReg`（2026-08-28）已并入主线。
- hook 已接线：`isa.cc:39` include、`isa.cc:452-457` 调用 `chaosSysReg->maybeCorrupt(idx, miscRegName[idx], val)`、`isa.hh:179-180` 成员 + `setChaosSysReg()`；自挂载（ctor `isa->chaosSysReg = this`）。
- 实现模式：`bit_flip / stuck_at_zero / stuck_at_one / random`（cc:81-84, 174-188）；白名单按 `ArmISA::miscRegName[]` 名字解析（cc:99-130，未知名 skip+warn）。
- `configs/se/arm_chaos_fs.py:73-84, 165-179` 已暴露 `--chaos_sysreg` 开关并挂载。
- **诚实修正**：CHAOSArmSysReg **已存在并可用**，本文标注为"**已实现，待扩展 value_to_legal(F5) + 时间窗修复(D4)**"（任务 S2-5a）。原方案将其标为"待新写"是失实的。注意 `arm_chaos_fs.py` 文件头注释仍写"a TLB/SYS-reg injector SimObject does not exist yet"——该注释滞后于代码，是另一处需同步修正的文档债。

#### 0.3.4 原方案声称"classify.py 九类"——**失实，已修正**

- `tools/classify.py` 实读（docstring + `classify_run()` 实现 cc:80-127）确认是**六级互斥优先级分类**：`SimulatorError > Hang > Crash > Inactive > Masked > SDC`。
- 原方案的"九类"（含 DetectedContained/Latent/Corrected 等）是**设计意图**，非当前实现。`DetectedContained`/`Latent`/`Corrected` 的细分类**未在 classify.py 实现**——它们是 protectionModel 层（§4.2，待实现）的产物。
- **诚实修正**：本文统一以"六级分类"为现状基准，"九类"作为 protectionModel 落地后的扩展目标（任务 S0-4）。

#### 0.3.5 构建与运行环境（已实测）

- `gem5.opt` 位于 `CHAOS/gem5/build/ARM/gem5.opt`（**非顶层 `build/ARM/`**），约 1.05 GB。
- **运行依赖**：`source /home/sdc/gem5-deps/env.sh` 设置 `LD_LIBRARY_PATH`（含 libprotobuf.so.25.1.0 + libabsl*）；不 source 则报 `cannot open shared object file`。
- **构建滞后问题（已发现并修复）**：初查时 `gem5.opt` mtime 09:13 早于源码 mtime 09:19（顶层 CHAOSPhysReg.py 含 `vecLaneWidth` 但旧二进制不认 → GPR SDC 锚点报 `AttributeError: Invalid assignment ... vecLaneWidth`）。本文撰写期间已用 `scons build/ARM/gem5.opt -j16`（`source env.sh` 后）增量重建，恢复源码-二进制一致（§5 锚点复现基于重建后二进制）。
- 构建命令：`cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh && scons build/ARM/gem5.opt -j16`（j126 在 29GB 主机 OOM，用 j16）。

### 0.4 诚信修正总表（原方案文档失实声明 → 本文修正）

| # | 原方案声明 | 源码真相 | 本文修正 |
|---|---|---|---|
| C1 | "已有 8 个注入器，CHAOSAddrPath/CHAOSPTW 来自 main 并入" | 主线原仅 7 个；AddrPath/PTW 在侧分支未并入。**S1-5b 已实现 CHAOSAddrPath `ffd041e`**，主线现 8 个；PTW 仍待实现 | 标"11 个已有（含 AddrPath/PTW）"（§0.3.2, §A.2） |
| C2 | "CHAOSArmSysReg 任何分支都不存在，待新写" | 已存在并入主线，hook 进 isa.cc:452-457，4 模式 | 标"已实现，待扩展 F5 + 修 D4"（§0.3.3, §5.7） |
| C3 | "classify 九类" | 实读六级（SimulatorError/Hang/Crash/Inactive/Masked/SDC） | 标"六级现状，九类为 protectionModel 扩展目标"（§0.3.4, §4.3） |
| C4 | "H5 已闭环（main，30 注入 28 检出 93%）" | H5 闭环在**侧分支**（fi-h6-h7-fs-verify），基于 `structuralFault` 模式；主线 CHAOSLSQFwd 已回退，**无 structuralFault**，H5 在主线**不可复现** | 标"H5 在侧分支闭环；主线需补 structuralFault 后复现"（§6.1, §10） |
| C5 | "H6 已闭环（main，numAddrFaults=20）" | H6 在侧分支 FS 下钩子触发非零、复现 byte7 清零签名，但 D2-only 50 注入→0 可观察失败，**定量谱可分未确立** | 标"H6 FS 钩子可达性已证，定量未确立"（§6.1） |
| C6 | "H7 已闭环（main，5 seed：on 全 0，off 1–4）" | H7 在侧分支 SE 模式 numFaultsInjected=0（mmu.cc:1213 静态归因）；FS 内核态 ECC 纠正 + spurious 制造两机制各实证，**未在同一实验结合，完整 ECC on/off spurious 率定量未完成** | 标"H7 两机制各实证，完整定量对照未完成"（§6.1） |
| C7 | D2 缺陷"CHAOSLSQFwd 64 位掩码待修" | 确认 `bitset<32>` + `&0xff` 单字节 | ✅ 已修 `0ae28fe`（UInt64 + maskWidth，bit32/63 注入验证通过） |
| C8 | "kp920_proxy.py / kp920_proxy_fs.py" | 不存在（符合"待写"诚实声称） | 保持"待写"（§4.1, §10） |

> **诚信自评**：原方案文档的失实集中在"将侧分支（fi-h6-h7-fs-verify 等）已验证的能力误标为主线已有"。这源于双分支分裂（`fi` 与 `main` 分头开发 H5/H6/H7 与 P0–P3）后，文档未严格区分"侧分支已验证"与"主线已并入"。本文以工作树源码为唯一事实源，恢复了诚实基线。原方案的**设计骨架本身是有效的**——F1–F6 故障模型、campaign 网格、openEuler 七步诊断、抗 SDC 设计建议的方向都成立；失实的只是能力状态的标注。本文继承其设计、修正其标注。

---

## 第 1 章　研究目标与问题定义

### 1.1 SDC 定义与"三无"特征

**Silent Data Corruption (SDC)**：处理器在**无任何即时错误信号**的情况下产生错误计算结果，该错误被上层软件正常使用并传播，最终导致数据丢失、一致性破坏或服务异常。"三无"：

- **无错误信号**：不产生 SError / SEA / ECC 等硬件级错误报告；
- **无日志记录**：SEL / RAS Error Records 中无对应硬件故障条目；
- **无即时崩溃**：应用不立即 crash，而是静默产生错误结果（DUE 是"被检出不可纠正错误"，与 SDC 互补但不同）。

### 1.2 真实发生率（学术基线，引用而非自测）

| 来源 | 报告发生率 | 说明 |
|---|---|---|
| Meta (2021) | ~1/1000 设备 | Hardware Sentinel [ASPLOS 2025] |
| Google (2021) | 每几千台机器数个 mercurial cores | Cores that don't count [HotOS 2021] |
| Alibaba (2023) | 3.61‱ | 100 万+ CPU、32 个月 [SOSP 2023] |
| PinDrop (2026) | 0.035% 生命周期内 ≥1 次 SDC | 5 亿+ 执行、12 年 [HPCA 2026] |
| 传统软错误模型 | ~1/1,000,000 | Baumann 2005 |

> **关键结论**：真实 SDC 发生率比传统软错误模型高约 3 个数量级。ARM64 在 PRF 与 L1D 的 SDC AVF 高于其它架构（Cross-ISA 论文），NZCV 条件标志、向量寄存器是 ARM64 独有脆弱点（详见 §2.2 暴露面分析）。

### 1.3 证据等级定义（贯穿全文每个结论）

| 等级 | 含义 | 本方案中的典型 |
|---|---|---|
| E1 | ISA/源码/TRM 直接支持 | ARMv8 异常语义、寄存器宽度、cache 容量 |
| E2 | 同平台受控实验（gem5 SE/FS） | 注入器实跑锚点、位谱复现、Wilson CI |
| E3 | 微架构代理模型（参数近似） | kp920_proxy O3 参数、N1 TRM 保护表代理 |
| E4 | 依赖未公开实现细节，待实机/RTL 校准 | V110 内部保护表、bufferless NoC、HCCS |

### 1.4 研究目标（四维度）

1. **逐单元 SDC 概率量化**（维度①）：对微架构关键单元（PRF/RAT/freelist/ROB/IQ/LSU 转发/FSU/TLB/PTW/Cache/BPU/Exec）量化 `P_SDC / P_DUE / P_escape / Reachability`（Wilson 95% CI），raw 与 protection-aware 两组。
2. **SDC 规律研究**（维度②）：位谱规律、传播规律（read-trace 四分类）、相位/时序规律、保护交互规律、跨单元敏感性排序（第 6 章）。
3. **SDC 诊断建议**（维度③）：基于 openEuler 系统日志的七步法 + P/N 规则 + 置信度模型，作为注入平台的**反哺接口**（第 7 章）——注入实验产出位谱指纹库与单元 P_SDC，回填诊断权重与签名匹配。
4. **抗 SDC 微架构设计建议**（维度④）：逃逸集合分解 + 保护优先级排序 + **抗 SDC 微架构机制设计建议**（第 8 章）——指导芯片设计者"在哪里加什么保护/冗余/校验、如何抗相位竞争与状态泄漏"，而非 DFT 测试向量。

### 1.5 现场证据基线（本方案的"靶子"，全部来自单一故障机）

> **诚实前提**：以下现场签名全部来自**同一台** Kunpeng-920 故障机（Yangtze R240k V2，HiSilicon HIP08 / TaiShan v110，4×48=192核，768GB，openEuler）。**未在第二台同型号健康机上复现**（CORE179_SDC_ROOTCAUSE_REPORT §15.1 自承）。因此现场证据等级最高 **E2（单机真机多方法交叉验证）**，非 E1（多机独立复现）。本方案的仿真-现场对照是"签名匹配度"评估，非"现场等同"。

| 案例 | 现场签名（精确数字） | 指向单元 |
|---|---|---|
| **method1**（Cholesky `x[0]`） | 损坏固定 `x[0]`；popcount 21–32 bit（非单 bit SEU）；numeric-only 失败率 1.0% ≈ 4× compute-both 0.27%（状态泄漏签名）；N≥256 阈值；满载 ~0.5–1%/单核 0%；A（输入）完好 0/3000、x 错 28/3000；PMU/EDAC 全 0；G5 285/285 全 179 核、G6 140/140 全 179 核 | 乱序后端状态泄漏（PRF 活性误判流程 A / ROB 提交顺序错流程 C） |
| **method2**（`x10` 垃圾指针） | ESR=0x96000004（DFSC=0x04 TF-L0, WnR=0）；崩溃指令 `find_busiest_group+0x1b8 ldr x21,[x10,#0xa0]`（`f9405155`）；x10 每次不同；损坏源 x9=`__per_cpu_offset[cpu]` 高 32 位非 0（`0ffe/a240/00ff`）；CPU2 VDDAVS 0.810V 欠压复现；复位码 0x2C00000F | LSU 数据返回通路；PRF 指针损坏（后重定位为 LSU 数据返回） |
| **method3**（LSU 转发相位） | float 尾数 85%（177/207）、double 尾数 93%（331/355）、符号 0–1/562；GEMM double popcount 中位 28 最大 39、SVD 单比特中位 3（5/11 恰 1 位）；加一条 no-op ALU → 触发率 100%→10–20%（H=1/10, X=1/5）；三必要条件（store + 地址推进 + 同 LLC 域 + 跨 cache line） | core179 公共 store/load 流水线的 instruction-scheduling timing-phase race |
| **core179 六案** | 88 起事件 100% 收敛 CPU179（82 WARNING + 6 Oops）；5/6 命中 `find_busiest_group+0x140`；零塌缩族（FSC=L3, x20=0）/撕裂移位族（FSC=L0, x20=ROL16/≫8）；ESR `0x96000044`（70 例 spurious, WnR=1, bit6 应 RES0 却恒置 1）/`0x96000004`（3 例 + 致命, WnR=0）；寄存器-内存铁证（offset[146] 内存 `ffffcc879ed92000` vs 寄存器 `00ffffcc879da2e0`=offset[0]≫8，Hamming 距离 0）；XOR 汉明重量 35/36 均匀散布无簇；RAS 全静默；MTBF≈5h | D1 数据通路（fill-buffer/replay 合并 mux≈L1D 读出组装）+ D2 地址通路（byte7 清零, 2/5 例确凿）+ D3 PTW 通路（73 例瞬态走查失败） |

> **ESR 解码对照**（method2 vs core179）：`0x96000004` = EC=0x25 (Data Abort current EL), WnR=0 (读), DFSC=0x04 (Translation fault level 0)；`0x96000044` = EC=0x25, WnR=1 (写), DFSC=0x44（含 bit6，ARMv8.2 该位应 RES0，HIP08 实现行为未定，诚实标为局限）。两者关键区别：读 vs 写访问、bit6 是否置位。

---

## 第 2 章　鲲鹏920 微架构画像与 SDC 暴露面

### 2.1 TaiShan V110 关键参数（公开资料 + 第三方分析）

| 单元 | 参数 | 证据等级 |
|---|---|---|
| 核心 | ARMv8.2-A，4-wide 超标量乱序，2.6–3.0 GHz，64 核/芯片，3-DIE Chiplet | E1（ISA/公开）/E3（频率） |
| 前端 | 4 发射解码；L1I 64KB/4-way/64B line/ECC；两级动态分支预测 + 64-entry BTB + 31-entry 返回栈；iTLB 32 项 | E1（容量）/E3（保护） |
| 乱序中枢 | PRF-based 重命名；分布式四调度器（每调度器约 33 项）；flag rename 约 31 项；支持 move elimination | E3（微结构第三方估计） |
| 执行单元 | 3× 通用 ALU + 1× 复杂端口（乘除 4 周期）；双 FSU（FP32 FMA 2×128b，FP64 quarter-rate）；2× AGU | E1/E3 |
| 访存 | L1D 64KB/4-way/64B/ECC，2×128b 访问/周期，hit load-to-use 4 周期；store 转发 6–7 周期，跨 16B 边界 +1–2 周期；dTLB 32 项全相联 + L2 TLB 1024 项（11 周期） | E1/E3 |
| 缓存层次 | 私有 L2 512KB（10 周期）；共享 L3 最高 64MB，按 4 核 Cluster 切片，Tag 在 Cluster、Data 在 NoC 附近，Shared/Private/Partition 三模式（默认分区，约 36 周期） | E1（容量）/E3（拓扑） |
| 片上/片间 | 自研 bufferless 双环 mesh NoC（<15ns intra-die）；Die 间 HCCS 一致性（最高 400GB/s）；8 通道 DDR4-2933（≈187GB/s）；每 Compute Die = 1 NUMA 节点 | E4（未公开实现细节） |
| RAS | 指令/数据缓存 ECC、内存毒化隔离、PCIe AER、MCA、错误隔离（标称 99.999%） | E1（标称）/E4（逐结构） |

### 2.2 SDC 暴露面模型与单元分级

```
SDC 暴露面(unit) ≈ 未受保护状态位数 × (占用率 × 平均驻留周期) × P(传播到最终输出 且 逃过所有检测)
```

| 优先级 | 单元 | 暴露面评级 | 主要依据 | 现有注入器 |
|---|---|---|---|---|
| **P0** | PRF | 高 | 无保护（TRM 惯例）、高占用；method1/3 现场指向 | ✅ CHAOSPhysReg（已验证锚点） |
| **P0** | RAT + freelist | 高 | 无保护；"映射张冠李戴/历史残留"对应 method1 核心假设 | ❌ 待实现 CHAOSRenameMap/FreeList |
| **P0** | ROB + 按序提交 | 高 | 无保护；异常位/投机泄漏两类静默逃逸 | ❌ 待实现 CHAOSROB |
| **P0** | LSU store→load 转发 | 中高 | 无保护；method2 位谱已定量吻合 | ⚠️ CHAOSLSQFwd（基础版，缺 structuralFault） |
| P1 | 发射队列 IQ | 中高 | 无保护；F5 错源、F6 相位竞态 | ❌ 待实现 CHAOSIQ |
| P1 | 浮点/向量执行（双 FSU） | 中高 | 无 ECC 概念组合逻辑；method3 位谱指向 | ⚠️ CHAOSPhysReg vector（已覆盖存储层）/❌ CHAOSFPU 数据通路待实现 |
| P1 | 地址翻译（dTLB/PTW/系统寄存器） | 中高 | L1 TLB 保守取无保护；method3 已定位 | ⚠️ CHAOSArmTLB（基础）/✅ CHAOSAddrPath（已实现 `ffd041e`）/✅ CHAOSPTW（已实现 `de48432`）/✅ CHAOSArmSysReg（已实现） |
| P1 | L3（分区）/RAS 逃逸 | 中 | Tag/Data 分离、128B 故障域；RAS 逃逸元分析 | ❌ pairedSector 代理待实现/❌ CHAOSRAS 待实现 |
| P2 | L1D/L2 数据通路 | 低中 | ECC 后逃逸窗口窄；重点 post-check escape | ⚠️ CHAOSCache（数据字节，缺字段级+PCE） |
| P3 | BPU | 低 | 预测错误被冲刷；重点"投机流是否泄漏" | ❌ 待实现 CHAOSBPU |
| P3 | 整数执行 ALU | 低 | Veritas：整数加法器 SDC 低几个数量级；阴性对照 | ❌ 待实现 CHAOSExec |
| P2/P3 | 系统级（NoC/HCCS/内存控制器） | 中 | bufferless 无吸收、跨 Die 一致性；E3/E4 代理 | ❌ 独立子项目 |

> **现状盘点**：覆盖 P0–P3 全单元需 7（已有）+ 约 11（待实现/扩展）个注入器。其中 P0 的 PRF 已可立即 formal；RAT/ROB 是"最大工具缺口 + 与 method1 对照最直接"，最高开发优先级。

### 2.3 保护覆盖基线（Noverse N1 TRM Table 9-1 代理，E3）

华为不公开 V110 逐结构保护表 → 用同代同级 Noverse N1 TRM Table 9-1 作代理（`protectionModel` 参数的语义依据，§4.2）：

| 结构 | 代理保护 | 注入后处理逻辑 |
|---|---|---|
| L1I data | `sed` | 1-bit：行失效重取；≥2-bit：静默（可能 SDC） |
| L1D/L2 data | `secded_poison` | 1-bit：撤销（Corrected）；2-bit：毒化并传播（DetectedContained/Latent）；≥3-bit：静默 |
| L1D/L2 tag | `secded` | 1-bit：撤销；2-bit：invalidate + DetectedContained；≥3-bit：静默 false-hit |
| L1 iTLB/dTLB | `none` | 不处理，raw 即 escape |
| L2 TLB/walk cache | `parity_interleaved` | 1-bit：条目失效重走页表；同奇偶 2-bit：静默 |
| PRF/RAT/freelist/ROB/IQ/store buffer | `none` | 不处理，raw 即 escape |
| L2 victim/BTB/GHB/PHT/MMU 替换 | `none` | 不处理 |
| DRAM | `secded` | 同 L1D data |

> **诚实标注**：N1 ≠ V110，保护表是代理（E3）。若 V110 实际保护表不同则需重估（§9.4 边界）。这是"protection-aware"建模层的输入，当前主线注入器**尚未实现 protectionModel 参数**（待 S0-3）。

### 2.4 x86 vs ARM64 微架构差异对 SDC 的影响（来自 docs/hypothesis/cpu.md，泛服务器核对比非 V110 实测）

| 差异 | 对 SDC 的影响 | 证据等级 |
|---|---|---|
| ARM64 弱内存序 vs x86 TSO | ARM 可做更深 LSQ/ROB（640–768+项 vs 320–512），更大乱序窗口 → 更长 PRF 驻留 → AVF↑；但无 TSO 的 CAM 全匹配负担 | E3（泛 Neoverse 对比） |
| ARM64 31 GPR vs x86 16 GPR | 寄存器压力小、spill/fill 少 → 减少 LSQ 转发流量（间接影响转发 SDC 暴露面） | E3 |
| NZCV 仅 S 后缀指令更新 vs x86 EFLAGS 隐式改写 | ARM 依赖链更干净，但 NZCV 标志位是 ARM64 独有脆弱点（条件分支异常） | E1（ISA） |
| 分布式多队列调度器 vs 集中保留站 | ARM 分布式 → 单调度器故障影响域小但相位竞争点更多 | E3 |

> 本对比源自 `docs/hypothesis/cpu.md`，其数据是"Intel SPR/AMD Zen4 vs Neoverse V1/V2"——**非 V110 专有**。方案中凡引用此对比，均标 E3（泛 ARM64 服务器核代理），不谎称 V110 实测。

---

## 第 3 章　SDC 故障模型定义与分类

### 3.1 F1–F6 + PCE 谱系表（标注主线实现现状）

| ID | 模型 | 定义 | 主线现状 | 实现方式 |
|---|---|---|---|---|
| F1 | 单比特瞬态 | 某一位翻转一次 | ✅ 已有（Reg/PhysReg/Cache/Mem/LSQFwd/ArmTLB/ArmSysReg） | `faultType=bit_flip` + `faultMask=1<<k` |
| F2 | 局部多位 | 相邻 2/4/8 位同时翻转 | ✅ 已有 | `bitsToChange>1` 或多位 `faultMask` |
| F3 | 间歇突发 + 数据相关触发 | 仅当目标当前值匹配某位模式时注入（模拟欠压建立时间违例） | ✅ CHAOSPhysReg 已实现 `7f538c4` | `triggerValueMask/triggerValuePattern`（CHAOSPhysReg 优先，复现 method2 欠压；已验证 MISS 1.3 亿次正确跳过） |
| F4 | stuck-at | 某位永久卡 0/1 | ✅ PRF 写路径（`setStuckTarget`，G2 已验证）；其余仅"注入一次" | 补 write-path 钩子到 LSQFwd/Cache |
| F5 | 合法域替换 | 换成另一个合法值/编号（逻辑决策层故障） | ❌ 全部待实现 | RAT→另一 physReg；freelist 活寄存器误标空闲；LSQ 转发源→另一 store；TLB pfn→另一活页；SysReg `value_to_legal` |
| F6 | 延迟/遗漏代理（相位） | 唤醒/转发提前或推迟 N 拍 | ❌ 待实现 | IQ 唤醒 phaseOffset；LSQ 转发 phaseOffset |
| PCE | post-check escape | ECC 校验通过之后、数据进入流水线中被损坏 | ❌ 待实现 | `CHAOSL1DForward` |

> **优先级**：F5 最高（对应 method1 核心假设"映射张冠李戴"，当前**零覆盖**）；PCE 次之（完整 RAM 保护把 SDC 逼到 ECC 之后数据通路的必然出口）；F3 第三（对应 method2 欠压复现）。F5/F6/PCE 是"位翻转以外"的逻辑决策层与相位故障，是本方案相对传统 FI 工作的核心创新点（§9.1 贡献点 2）。

### 3.2 微架构单元 × 故障模型映射矩阵（逐单元见第 5 章）

每个单元的"画像 → SDC 机理 → 故障模型表"在第 5 章相应小节展开（避免重复）。总览：P0 单元（PRF/RAT/ROB/LSU）需 F1–F6 全谱；P1 单元（IQ/FSU/TLB）需 F1/F5/F6；P2/P3 单元（Cache/Exec/BPU）以 F1/F2 + 阴性对照为主。

---

## 第 4 章　统一实验框架（所有单元共用）

### 4.1 平台配置族

| 配置族 | 用途 | 关键参数 | 结论标签 | 现状 |
|---|---|---|---|---|
| C0 方法学基线 | 注入器正确性、G0–G7 复检 | `arm_chaos.py` 默认（O3, SE, classic cache, 64B） | "ARM64-gem5 baseline"，E2 | ✅ 已存在并验证 |
| C2-KP 鲲鹏处理器代理 | 逐单元 SDC 量化 | `--kp920_proxy` 开关（arm_chaos.py） | "Kunpeng-informed proxy"，E3 | ✅ 已实现 `1564328`（V110 ROB128/PRF160/192/LQ48/SQ42/4-wide/2.6GHz；numIQEntries 非 Python 可设注释） |
| C1 ARM64 架构 | ARM vs x86 同语义配对 | `x86_chaos.py` 镜像 C2-KP | "controlled cross-ISA"，E2 | ✅ x86_chaos.py 已存在 |

**C2-KP 的 O3 参数**（✅ 已实现 `1564328` 为 arm_chaos.py 的 `--kp920_proxy` 开关；`configs/fs/kp920_proxy_fs.py` 待写）：

```python
# TaiShan V110 4-wide OoO 代理（E3，非周期精确）
cpu.fetchWidth = cpu.decodeWidth = cpu.renameWidth = cpu.issueWidth = \
    cpu.dispatchWidth = cpu.commitWidth = 4          # 4-wide
cpu.numROBEntries      = 128       # 扫描 {96,128,160}
cpu.numPhysIntRegs     = 160       # 第三方估计 ~128–160；扫描 {128,160,192}
cpu.numPhysFloatRegs   = 192       # 向量/FP，双 FSU
cpu.LQEntries          = 48        # 深 LSQ（弱内存序）；扫描 {32,48,64}
cpu.SQEntries          = 42
cpu.numIQEntries       = 66        # ≈ 2×33（统一 IQ 近似四调度器，标 E3）
# FUPool：IntALU×3 + IntMultDiv×1(lat=4) + MemRead×2/MemWrite×2
#        + FloatMemRead + SIMD/FP×2（FADD lat=4, FMADD lat=7）
# 缓存：L1I 64KiB/4-way/64B；L1D 64KiB/4-way/64B；L2 512KiB/8-way 私有
clk = "2.6GHz"
```

> 诚实标注：gem5 统一 IQ ≠ V110 分布式四调度器；classic cache 无分区 L3 Tag/Data 分离；无 bufferless NoC。对应单元节标 E3/E4。

### 4.2 protection-aware 建模层（✅ v1 `a6c5b9c`：classify 九类 + CHAOSCache protectionModel 参数面；.cc ECC 后处理待续）

实现为 CHAOSCache / CHAOSMem / CHAOSArmTLB 的新参数 `protectionModel ∈ {none, sed, secded, secded_poison, parity_interleaved}`，注入后按 §2.3 表决定"可观测归宿"。每个 cell 跑两组：`none`（raw 上界）与 `<代理值>`（protection-aware 逃逸），报告两组并画风险反转图。**不换算产品 FIT**（无 raw device rate）。

> 现状：classify_run_pa 九类 + CHAOSCache protectionModel 参数面已实现 `a6c5b9c`（Corrected/DetectedContained/Latent 分流已验证）；CHAOSCache .cc ECC 后处理逻辑（注入后按 model 决定归宿打标签）待续，raw 路径（none）完全可用。

### 4.3 结果分类与分母（沿用 `tools/classify.py`，六级现状）

**六级互斥优先级**（classify_run，实读 classify.py:80-127，求值顺序；**九类扩展 classify_run_pa `a6c5b9c`** 在此基础上按 ECC 标签分流 Corrected/DetectedContained/Latent）：

```
SimulatorError > Hang > Crash > Inactive > Masked > SDC
```

| 类别 | 判定 | 含义 |
|---|---|---|
| SimulatorError | stderr 含 gem5 panic/assert/SIGSEGV/abort | 模拟器自身 bug，不计入 |
| Hang | 超时且无 checksum 输出 | 控制流破坏死循环（DUE-class） |
| Crash | workload trapped（非法指令/SError/data abort/exit≠0） | 故障被检出（DUE-class） |
| Inactive | 0 次有效注入（目标不存在或 XZR 丢弃） | 实验无效 |
| Masked | exit 0 且 checksum==golden | 故障被掩蔽 |
| SDC | exit 0 且 checksum≠golden | **静默数据损坏** |

- `N_valid = N_total − N_inactive − N_simerror`；`P_SDC = N_SDC/N_valid`；`P_DUE = (N_crash+N_hang)/N_valid`；`P_escape = N_SDC/N_valid`（Latent 待 protectionModel 落地后并入）；`Reachability = N_valid/(N_total − N_simerror)`。
- **read-trace 四分类**（PRF/RAT/ROB 类，CHAOSPhysReg 已有 `reads_before_overwrite`）：`reads_before_overwrite=0` → Benign；`>0` 且输出不变 → Masked；`>0` 且输出变且无异常 → SDC；触发异常 → Crash。用于验证 `P(SDC∣reads>0)` 跨单元一致性（H1）。

### 4.4 campaign driver（✅ 已实现 `f8aecc7`，S0-2 v1 完成；manifest v2 待续）

网格驱动器 `tools/campaign.py`（**已实现**，v1）：`injector / config / grid（笛卡尔积）/ n_per_cell / seeds(base 20260825 + cell_ordinal×1000 + rep) / workload`。流程：展开 cells → 生成不可变 manifest v1 → 调 `runner.py` 执行 → 收集六级分类 → 每 cell 算 Wilson 95% CI（含 0-SDC 的 3/n 上界）→ `artifacts/<campaign>/{cells.csv, summary.md}`（summary 含 §11.3 三条诚实边界）。v1 端到端已验证（1 cell × 1 rep → SDC=1/1 P_SDC=1.000 [0.207,1.000] first=SDC ✓）。

> 现状：`tools/runner.py`（单 manifest + classify，G5 路径已修 `f8aecc7`）+ `tools/campaign.py`（网格编排，已实现）均就绪；`fi_research/bit_spectrum.py`（位谱分析）在 fi_research/（campaign v2 待集成 read-trace + 位谱收集）。manifest v2（§4.5）+ protectionModel（§4.2）+ jobs 并行 + maxinsts 优化待续。

### 4.5 manifest schema（现状 v1，待扩展 v2）

- 现状 `schemas/manifest.schema.json`（v1）：`schema_version, run_id, source(git), platform, workload(binary SHA256, ROI), trigger, target, fault, rng, limits, oracle`。
- v2 扩展（待 S0-2）：`target.component` enum 增补全单元；`target.sub_field`（pfn/ap/asid；src_ready/dst_tag；map_entry/free_bit）、`semantic_role`（ABI 角色）；`fault.f5_substitute_target / f6_phase_offset / trigger_value_pattern / protection_model`；`dynamic_context`（mapped_phys_reg, freelist_size, reads_before_overwrite, cache_residency, lsq_source_seq, tlb_asid, committed_inst_at_inject）。

### 4.6 样本量设计

pilot 每 cell n=100（可达率/工具错误/粗略比例）；formal 每 cell n=384（最保守比例 95% Wilson ≈ ±5%）；关键低 SDC cell 扩 n=663（≈ ±3.8%）；0 SDC 时 95% 上界 ≈ 3/n。

---

## 第 5 章　逐微架构单元故障注入设计

> 每节固定八段：**A 目标与 hook / B 注入器 / C campaign 网格 / D kernel / E 指标与预期 / F 边界与证据 / G 工作量 / H 验收断言**。单元按优先级 P0→P3 排序。注入器状态以 fi-wangxu 工作树源码为准（**9 个已有含 CHAOSAddrPath/CHAOSRenameMap + 9 个待实现/扩展**，见附录 A）。

### 5.0 已验证锚点表（本方案撰写期间实跑，真实 gem5 输出）

> **诚实声明**：以下锚点均在本方案撰写期间用 `CHAOS/gem5/build/ARM/gem5.opt`（重建后，mtime 2026-08-30 10:19，1.05GB）实跑获得，命令与输出可复现。运行前须 `source /home/sdc/gem5-deps/env.sh`（设 LD_LIBRARY_PATH 含 libprotobuf + libabsl）。这是"已验证"而非"预期"。

| 锚点 | 注入器/kernel/配置 | 命令（要点） | 真实输出 | 状态 |
|---|---|---|---|---|
| golden 基线 | 无注入 / `reg_chain` / O3 | `gem5.opt arm_chaos.py --cmd=reg_chain --cpu=O3` | `f247ef3fe6f02cfd` | ✅ 已复现（与 STATUS.md 一致） |
| GPR SDC（X3 bit0） | CHAOSPhysReg arch_frontend / `reg_chain` | `--chaos_phys --phys_mode=arch_frontend --phys_target_arch=3 --probability=1.0 --first_clock=100000 --max_faults=1 --rng_seed=20260825 --fault_type=bit_flip` | 输出 `d43a25d7fcc218b7`（≠ golden → SDC）；注入日志 `Cycle:100000 PhysReg[220] (<= ArchReg[3]) Mask:0x...800...`；read-trace `reads_before_overwrite=25000/50000/75000/100000/125000 overwritten=0` | ✅ 已复现（与 STATUS.md `d43a25d7fcc218b7` 一致） |
| LSQ 转发 SDC | CHAOSLSQFwd / `fp_fwd_kernel` | `--chaos_lsqfwd --probability=1.0 --first_clock=1000000 --max_faults=1 --rng_seed=20260825 --fault_type=bit_flip` | `SDC@it=232 i=58 golden=3ffad444e2800000 actual=3ffad444e6800000 xor=0000000004000000`，`iters=500 fails=1`；对照无注入 `iters=500 fails=0` | ✅ 已复现（XOR bit30 = double 尾数高位，吻合 method3 位谱） |
| **method1 历史残留 SDC** | CHAOSRenameMap f5_substitute / `accum_kernel` X9 | `--chaos_rat --rat_mode=f5_substitute --rat_target_arch=9 --probability=1.0 --first_clock=100000 --max_faults=1 --rng_seed=20260825` | `iters=500 fails=1`（golden `fails=0`）；日志 `ArchReg[9]->PhysReg[199] (stolen from donor arch 13, was PhysReg[62])` | ✅ 已复现（F5 偷映射在长存活累加器传播为 SDC，方案 §5.2 验收锚点 P(history_residue)>0） |
| core179 D1 撕裂移位 | CHAOSLSQFwd byte_lane_skew rol1 / `fp_fwd_kernel` | `--chaos_lsqfwd --lsq_structural_fault=byte_lane_skew --lsq_skew_bytes=1 --first_clock=1000000 --max_faults=1` | `actual=003ffad444e28000`（golden 右旋1字节），`xor=3fc52e90a6628000` 多位散布 | ✅ 已复现（H5 主线就位，rol1 签名方向与现场 35/36 汉明重量一致） |

> **锚点解读**：
> - **GPR SDC** 完整演示 §5.1 机制：arch_frontend 模式经前端 RAT 定位 `ArchReg[3]→PhysReg[220]`，注入后该物理寄存器被读 125000+ 次才覆写（`overwritten=0` 至观察窗口末），SDC 经长读传播窗口扩散——这是 method1 "状态泄漏"签名在仿真侧的可观察代理。
> - **LSQ 转发 SDC** 的 XOR `0x04000000` 落在 double 尾数高位（bit 30，非符号位），与现场 method3 "float 尾数 85% / double 93% / 符号 0–1" 的位谱规律方向一致（§6.2），构成仿真-现场对照生态效度的初步证据（E2）。
>
> **重建背景**：初查时 `gem5.opt`（09:13 构建）早于源码（09:19，含 `vecLaneWidth`），导致 GPR SDC 锚点报 `AttributeError: Invalid assignment for Class CHAOSPhysReg with parameter vecLaneWidth`。本方案撰写期间已用 `scons build/ARM/gem5.opt -j16`（`source env.sh` 后）增量重建（约 25 分钟，含 param_* 全量重编 + 1GB 链接），恢复源码-二进制一致后上表全部复现。这本身印证了 §11.1 G7"源码-二进制一致"的必要性——**构建滞后是真实工程风险，已发现并修复**。

### 5.1 PRF 物理寄存器堆（P0，已有 CHAOSPhysReg，扩展 F3/semanticRole）

**A. 目标与 hook**：整数/向量/flag 物理寄存器堆。Hook 已核实：`regfile.hh`（读写 + `setStuckTarget` 写路径 stuck，G2）、`free_list.hh`（`isFree` 探活）、`cpu.hh:478-489`（`physRegFile()/frontRenameMap()/physFreeList()` accessor，已核实）。

**B. 注入器**：`CHAOSPhysReg`（已有，已验证锚点）。三种 `injectionMode{phys,arch_frontend,arch_commit}`；`regTargetClass{int,fp,vector,both}`；`vecLaneWidth/Offset`；64位 faultMask；write-path stuck（G2）；**F3 数据相关触发 `triggerValueMask/Pattern`（`7f538c4` 已实现，已验证 MISS 1.3 亿次正确跳过）**；**`semanticRole` ABI 角色标签（已实现，已验证日志）**。**待扩展**：`protectionModel=none` 占位。

**C. campaign 网格**（`kp920_proxy.py`，SE，`--chaos_phys`）：

| 轴 | 取值 |
|---|---|
| 模式 | `phys` / `arch_frontend`（经前端 RAT） |
| 目标寄存器 | ABI 角色分层：X0–X7（参数/返回）、X9–X15（临时）、X19–X28（callee-saved）、X29/X30（FP/LR）、指针类（复现 method2 `x10`） |
| 位段 | bit {0,11,12,31,32,47,48,63} |
| 故障模型 | F1/F2/F4/F3（`triggerValuePattern` 扫 4 模式） |
| 向量 PRF | V0–V31 × lane {4×32b,2×64b,8×16b} × lane offset（已有 vecLaneWidth/Offset） |
| 窗口扫描（H2） | ROB{96,128,160} × PhysIntRegs{128,160,192} × LQ/SQ{32/48/64} |

**D. kernel**：`reg_chain`（golden `f247ef3fe6f02cfd`，**已验证锚点**）；**待新增** `ptr_chase_kernel`（链表遍历，复现 method2）、`cholesky_numeric_kernel`（method1，numeric-only/compute-both 两变体）。

**E. 指标**：`P_SDC/P_DUE`（Wilson）按 ABI 角色 × 位段 × 模式热图（预期：指针类→P_DUE 高；累加器类→P_SDC 高全位段；循环计数器→低位 SDC 高位 Hang）；read-trace `P(SDC∣reads>0)` 跨单元一致性（H1/H3）；`reads_before_overwrite` 重尾性；method2 复现（F3 → `P_DUE` + ESR DFSC 分布 vs `0x96000004`）；method1 复现（numeric/compute-both ∈ [2,8]）。

**F. 边界**：E2（实跑锚点已证）。gem5 O3 PRF ≠ V110 PRF 几何（E3 绝对值）。

**G. 工作量**：CHAOSPhysReg F3+semanticRole 3 小补丁 + 2 kernel + campaign 配置。已有 pilot 证据（X2/X3 SDC 可复现，见 §5 已验证锚点表），直接进 formal。

**H. 验收断言**：① `reg_chain` golden `f247ef3fe6f02cfd` 20 次重放逐位一致；② `probability=0` 时输出哈希与无注入基线逐位一致（锚点回归）；③ F3 `triggerValuePattern` 命中注入次数与 `fault_injections.log` 严格相等；④ pilot 每 cell n≥100 产生 ≥1 个非 Inactive 结局。

### 5.2 RAT + freelist（P0，✅ CHAOSRenameMap `c5c8c96` + CHAOSFreeList `379e11c` 均已实现）

**A. 目标与 hook**：`frontRenameMap[tid]`（archReg→physReg）、`freeList`、move elimination、flag rename。Hook `rename_map.hh`（`rename()/lookup()/setEntry()`）、`free_list.hh`（`getReg()/addReg()/isFree()`）。

**B. 注入器**：`CHAOSRenameMap`（✅ 已实现 `c5c8c96`，三模式 `map_bitflip`/`f5_substitute`/`f4_field_stuck` + 合法域校验，自驱动 attackEvent 持 cpu 指针访问 `frontRenameMap()`；已验证 f5_substitute 偷映射 + map_bitflip 翻转 physRegIdx 合法性通过）；`CHAOSFreeList`（✅ 已实现 `379e11c`，两模式 `mark_free`/`pop_wrong` + 扫 RAT 找活 physReg + 合法域校验，已验证 PhysReg[170] donor 协同 RenameMap）。

**C. campaign**：RAT 模式 {map_bitflip(位域 0..log2(numPhysIntRegs)), f5_substitute, f4_field_stuck} × ABI 角色（重点长存活累加器）；freelist {mark_free, pop_wrong}；flag rename；move elimination。窗口同 §5.1。

**D. kernel**：`cholesky_numeric_kernel`（method1 主 kernel）+ 对照 `pure_fma/pure_spmv/pure_gather/tri_solve` + `mov_heavy_kernel`。

**E. 指标**：**历史残留专项** `P(history_residue)=N(读回值∈其它活变量值集合)/N_SDC > 0` 且显著（method1 核心，Fisher p<0.05）；损坏 popcount 中位数 >16（多位混叠，对标 21–32 bit）；read-trace 与 §5.1 对比（RAT 错是否为独立机制，H3）。

**F. 边界**：E2。`SimpleRenameMap` 是 flat 表，V110 RAT 微结构未知（E3）。

**G. 工作量**：约 6 补丁。**与 method1 对照最直接，最大工具缺口，最高开发优先级。**

**H. 验收断言**：① kernel golden 各 20 次重放一致；② `f5_substitute`/`mark_free` ≥1000 次注入 `SimulatorError`=0（合法域校验）；③ pilot ≥1 个非 Inactive 结局。

### 5.3 ROB + 按序提交（P0，待实现 CHAOSROB）

**A. 目标与 hook**：ROB 条目（result/done/exc_status/dest_phys/spec）、squash、commit RAT。Hook `rob.cc`（`retireHead()`/`squash()`/`doSquash()`）、`commit.cc`（`commitHead()`/`squashAfter()`）。

**B. 注入器**：待写 `CHAOSROB`。模式：`entry_bitflip`（field×distanceFromHead）、`exc_suppress`（清异常位→DUE 变 SDC）、`spec_leak`（squash 保留错误路径 μop 的 PRF 写，复现 method1 状态泄漏）。

**C. campaign**：mode × field{result,done,exc_status,dest_phys,spec} × 距提交距离 D{0,8,16,32,ROB_size−1} × 窗口{96,128,160}；`spec_leak` 需高分支密度 kernel。

**D. kernel**：`cholesky_numeric`（cdiv 制造投机）、`branchy_reduce_kernel`、`reg_chain`。

**E. 指标**：`P_SDC` vs D 曲线（预期单调，H2）；`exc_suppress` 的 `P(DUE→SDC 转化率)`；`spec_leak` 读回值命中率；read-trace `P(SDC∣reads>0)` 与 §5.1/5.2 对比（H3）。

**F. 边界**：E2；gem5 ROB squash 语义 ≠ V110 回滚状态机（E3 绝对值）。

**G. 工作量**：约 4 补丁。

**H. 验收断言**：① `cholesky_numeric` golden 20 次重放一致；② `entry_bitflip` 各 field×D cell ≥1 个非 Inactive；③ `exc_suppress`/`spec_leak` 不触达非法 ROB 索引（≥1000 次注入 `SimulatorError`=0）；④ `exc_suppress` 的 `P(DUE→SDC 转化率)>0` 且 `spec_leak` 联合观测 `P(读回值∈其它活变量值集合)>0`。

### 5.4 LSU + store buffer + store→load 转发（P0，扩已有 + 补回退能力 + 新注入器）

**A. 目标与 hook**：store buffer 数据、转发 CAM 匹配、转发源 seqNum、部分重叠拼接、AGU 有效地址、ready/replay、独占监视器。Hook `lsq_unit.cc:1493-1499` 转发数据（已有，已核实）、转发匹配决策点（新增）、AGU 地址生成（FS，待 CHAOSAddrPath）。

**B. 注入器**：
- `CHAOSLSQFwd`（已有，基础版）**需扩展**：① ~~修 D2~~ ✅ 已修 `0ae28fe`（faultMask UInt64 + maskWidth 多字节，bit32/63 可注入）；② ✅ `structuralFault` 模式已补齐 `8320daf`（`byte_lane_skew`/`all_zero`，复现 core179 D1 rol1/空槽签名，已验证）；③ `stale_line_replay`（FI_DESIGN_SUPPLEMENT 有设计，代码未实现）；④ F5 `fwd_source_sub`（待写）；⑤ F6 `phaseOffset`（待写，−2..+2）。
- `CHAOSAddrPath`（✅ 已实现 `ffd041e`，从侧分支移植 + 主线纪律强化）：hook `lsq.cc sendFragmentToTranslation` 翻译前破坏 vaddr（byte7 清零复现 core179 D2；低位翻转/F5 换址待扩）。**SE 无效（mmu.cc:1213 静态归因），FS O3 有效**（Atomic 不触发，需 checkpoint 后切 O3）。
- `CHAOSExMon`（待写）：hook 独占监视器 FSM，open↔exclusive 翻转。

**C. campaign**：转发数据 F1/F2/结构化（SE）；F5 转发源（SE）；F6 相位（SE）；AGU 地址（FS，checkpoint 后切 O3）；独占监视器（SE，LDXR/STXR）；F3 数据相关（SE）。

**D. kernel**：`fp_fwd_kernel`（已有，已验证锚点）、`int_rmw_kernel`、`movbe_kernel`；method3 的 7 类定向构造（同址/部分重叠/4K 别名/双候选/未就绪 replay/DMB-DSB/LDXR-STXR，各"加/不加热路径 no-op ALU"两变体）；`ptr_chase_kernel`。

**E. 指标**（与现场对照最密集）：位谱（尾数/符号/popcount vs method3 的 85–93%/0–1/中位 3~28）；相位敏感性曲线（复现塌方）；method3 三必要条件复现（去 store 推进/同 LLC 域/跨 cache line 任一 → 归零）；method1 复现（F5 fwd_source_sub 损坏固定在结果向量首元素）；AGU byte7 的 FAR MSB=0x00 占比。

**F. 边界**：转发 E2；结构化 E2（✅ 主线 `8320daf` 已补齐 + rol1/空槽签名验证）；AGU/PTW E2（FS 已证非零，侧分支）；F6 相位 E3（gem5 发射时序 ≠ V110）。

**G. 工作量**：CHAOSLSQFwd 扩展（D2 ✅ + structuralFault ✅ `8320daf` + stale_line_replay 待补 + fwd_source_sub 待写 + phaseOffset 待写） + CHAOSAddrPath 实现 2 补丁 + CHAOSExMon 2 补丁 + method3 7 类 kernel 约 3 补丁。

**H. 验收断言**：① `fp_fwd_kernel` golden 20 次重放一致；② 64 位 mask 高 32 位翻转产生非零高位字节注入计数（D2 修复后）；③ F5 `fwd_source_sub` 仅指向当前转发表源（≥1000 注入 `SimulatorError`=0）；④ method3 三必要条件对照 cell 各 ≥1 非 Inactive；⑤ `byte_lane_skew rot1` 复现 core179 撕裂移位签名（H5，侧分支 93%；主线 `8320daf` 已就位——rol1 SDC xor 多位散布已验证）；⑥ AGU byte7 清零 FS 下 `numAddrFaults>0` 且 FAR MSB=0x00 占比非空（H6，侧分支已证钩子触发，主线待实现）。

### 5.5 发射队列 IQ（P1，待实现 CHAOSIQ）

**A. 目标与 hook**：src-ready 位、src-tag、dst-tag、唤醒广播、选择仲裁。Hook `inst_queue.cc`（`wakeDependents()`/`scheduleReadyInsts()`）。

**B. 注入器**：待写 `CHAOSIQ`。模式 `src_ready_bitflip`/`tag_sub`（F5）/`wake_phase`（F6 ±N）/`wake_omit`（F6）。

**C. campaign**：mode × 目标调度器{int,mem,fp} × 触发相位；与 `CHAOSLSQFwd` F6 **联合注入**复现 method3。

**D. kernel**：`movbe_kernel`/`int_rmw_kernel`/`dep_chain_kernel`。

**E. 指标**：相位敏感性曲线（复现 method3 塌方）；错源唤醒命中率；位谱。

**F. 边界**：E2/E3；gem5 统一 IQ ≠ V110 分布式四调度器。

**G. 工作量**：约 3 补丁。

**H. 验收断言**：① `dep_chain_kernel` golden 20 次重放一致；② `tag_sub`/`src_ready_bitflip` 仅触达当前合法 source tag（≥1000 注入 `SimulatorError`=0）；③ `wake_phase` ±N cell 相位敏感性曲线非平坦（≥1 非 Inactive）；④ 与 CHAOSLSQFwd F6 联合注入产生 ≥1 非 Inactive。

### 5.6 浮点/向量执行单元（双 FSU）（P1，扩已有 + 待实现 CHAOSFPU）

**A. 目标与 hook**：向量 PRF（CHAOSPhysReg vector 已覆盖存储层）、FSU 数据通路、FPSR/FPCR。Hook `iew.cc` writeback 按 `opClass ∈ {FloatAdd,FloatMult,FloatMultAcc,SimdFloat*}` 过滤。

**B. 注入器**：`CHAOSPhysReg` vector 模式（已有，已验证 4 lane SDC 锚点）；待写 `CHAOSFPU`（`result_bitflip` 按 IEEE754 位段 / `fma_intermediate` / `rounding_sub`(F5) / `fpsr_suppress`）。

**C. campaign**：位段{sign,exp_high/low,mantissa_high/mid/low} × 算子{FADD,FMUL,FMADD,reduction,shuffle,widen/narrow} × 精度{FP32,FP64} × {向量 PRF 存储/FSU 数据通路}两类分开。

**D. kernel**：`gemm_float/double`（复现 GEMM popcount 中位 12/28）、`svd_iterative`（单比特中位 1–3）、`neon_lane`（已有，已验证锚点）、`fma_reduction_kernel`。

**E. 指标**：位谱（sign/exp/mantissa + popcount，直接对标 method3）；ULP/相对误差；lane×算子热图；归约放大系数；向量 PRF 存储 vs FSU 数据通路的签名可分性（KS 检验）。

**F. 边界**：E2（位谱可对照）；gem5 FSU 是功能模型（E3）；鲲鹏 128b ASIMD 无 SVE。

**G. 工作量**：约 5 补丁。

**H. 验收断言**：① `gemm_float/double` golden 20 次重放一致；② `rounding_sub`/`fpsr_suppress` 合法域校验（≥1000 注入 `SimulatorError`=0）；③ 位段×算子 cell ≥1 非 Inactive；④ GEMM popcount 中位与 method3 标称（12/28）同量级（KS 检验不拒绝）。

### 5.7 地址翻译（dTLB/iTLB/L2 TLB/PTW/系统寄存器）（P1，扩已有 + 待实现 AddrPath/PTW + 已有 SysReg 扩展）

**A. 目标与 hook**：dTLB/iTLB 条目（pfn/AP/XN/AttrIndx/nG/ASID）、L2 TLB、PTW 在途状态、系统寄存器白名单。Hook 已核实：`arch/arm/tlb.cc:164-168`（TLB hit，CHAOSArmTLB）、`arch/arm/isa.cc:452-457`（CHAOSArmSysReg）。**PTW hook 待实现**：`arch/arm/table_walker.cc doLongDescriptor`（侧分支 CHAOSPTW 曾 hook，主线无）。**全部 FS 模式**（SE 无 MMU-on，mmu.cc:1213 静态归因）。

**B. 注入器**：
- `CHAOSArmTLB`（已有，基础）**需扩展**：`pfn_to_mapped_page`（F5，翻到另一活页→静默 SDC）、`targetField ∈ {pfn,ap,xn,attridx,ng,asid}`、I-TLB 挂载、`protectionModel=none`。
- `CHAOSArmSysReg`（**已实现**，待扩展）：现有 `bit_flip/stuck_at_zero/stuck_at_one/random` + 白名单（`targetRegs` 按 miscRegName 解析，默认 `sctlr_el1,ttbr0_el1,ttbr1_el1,tcr_el1,mair_el1,vbar_el1`，**不含 contextidr/nzcv，需用户添加或改默认**）；**待补 `value_to_legal`（F5）** + 时间窗修复（D4，1GHz 假设）。FS 模式。
- `CHAOSPTW`（✅ 已实现 `de48432`，从侧分支移植+主线纪律）：hook `doLongDescriptor`，翻页表描述符；`ptwEcc` 参数（H7 自变量）、`clearValidBit` 模式（FS 下已验证制造 spurious，复现 core179 D3 73 例）。

**C. campaign**（FS，checkpoint 后切 O3/Atomic）：dTLB{pfn→未映射(DUE), pfn→活页(F5,SDC), AP, XN, AttrIndx, nG, ASID}；iTLB；L2 TLB；PTW{单 bit XOR+条件注入, clearValidBit}×{ptwEcc on/off}；系统寄存器{ttbr0/1,tcr,mair,sctlr,vbar,contextidr,nzcv}×{bitflip,value_to_legal}；method2 三根因区分（PRF/AGU/TLB 三种注入的 ESR/PC/x10 形态比对）。

**D. kernel**（FS）：内核调度域链表遍历（复现 method2 `find_busiest_group`）、context switch/fork-exec/页迁移、`ptr_chase`。

**E. 指标**："pfn→活页" cell 的 `P_SDC`（最危险路径）；"pfn→未映射" cell 的 `P_DUE` + ESR DFSC 分布 vs `0x96000004`；PTW ECC 对照（H7）；三根因匹配度打分；AP 位越权率；ASID 隔离违规率。

**F. 边界**：E2（FS hook 已证触发，侧分支）。FS 慢 → checkpoint 策略必需。`CHAOSArmTLB`/`CHAOSArmSysReg` 时钟窗口 advisory（ISA 非 ClockedObject，1GHz 假设，须修 D1/D4）。

**G. 工作量**：CHAOSArmTLB 扩展 ≈3 补丁 + CHAOSArmSysReg 扩展（F5 + D4）≈2 补丁 + CHAOSPTW 实现 + H7 formal ≈4 补丁 + FS checkpoint 流水线 2 补丁。

**H. 验收断言**：① FS checkpoint 后 golden 20 次重放一致；② `CHAOSArmTLB`/`CHAOSArmSysReg` firstClock/lastClock 时间窗修复后越窗注入计数=0（D1/D4）；③ `value_to_legal`/`pfn_to_mapped_page` 仅指向活页/合法系统寄存器值（≥1000 注入 `SimulatorError`=0）；④ `pfn→活页` cell `P_SDC>0` 且 `pfn→未映射` cell `P_DUE>0`、ESR DFSC 与 `0x96000004` 可比；⑤ PTW `ptwEcc on/off` 对照 cell 差异显著（H7，侧分支两机制各实证，主线待结合完成定量）。

### 5.8 Cache 子系统 L1I/L1D/L2/L3（P2/P1，扩已有 + 待实现字段级/PCE）

**A. 目标与 hook**：数据字节（已有）、tag、valid/dirty/repl/coh、victim、post-check escape。Hook CHAOSCache 事件驱动遍历（已有）、victim `mem/cache/base.cc` WritebackBlk（新增）、post-check `lsq_unit.cc` load 回填（新增）。

**B. 注入器**：`CHAOSCache`（已有）**需扩展** `targetField ∈ {data,tag,valid,dirty,repl,coh,victim}` + `protectionModel`；待写 `CHAOSL1DForward`（PCE）；L3 短期用 `pairedSector` 代理（待实现），完整 `CHAOSCHI`（Ruby/CHI）独立排期（S4）。

**C. campaign**：字段 × protection{none,secded_poison} × {随机/定向驻留} × ECC 粒度{1-bit,2-bit,3-bit}；L2 size sweep{256KiB,512KiB,1MiB}；L1I 语义字段{opcode,Rn,Rm,Rd,imm,cond}。

**D. kernel**：`l1d_reduce`（已有，已验证锚点）、`l1i_loop`（已有，已验证锚点）、`ptr_chain_kernel`、`struct_field_kernel`、`crc_state_kernel`。

**E. 指标**：raw vs protection-aware 风险反转图；post-check escape `P_SDC`（预期显著高于 raw）；tag F5 "读到同 set 别的行"命中率；L2 size 敏感性曲线；L1I SED vs SECDED 两组 `P_SDC` 差。

**F. 边界**：E2（chaoscache 锚点已验证）；华为保护类型未知（E3 映射）；无真实 ECC 逻辑（注入器内建模）。

**G. 工作量**：CHAOSCache 字段级+protectionModel≈3 补丁；CHAOSL1DForward 2 补丁；3 kernel。

**H. 验收断言**：① `l1d_reduce` golden 20 次重放一致（chaoscache 锚点）；② `targetField` 各字段（data/tag/valid/dirty/repl/coh/victim）≥1 非 Inactive；③ protection-aware `secded_poison` 下 raw vs protected 风险反转方向正确；④ `CHAOSL1DForward` PCE cell `P_SDC` 显著高于 raw（post-check escape 验证）。

### 5.9 分支预测 BPU（P3，待实现 CHAOSBPU）

**A. 目标与 hook**：BTB 目标、GHB、返回栈、间接预测。Hook `cpu/pred/`（`BPredUnit::lookup()`/`BTB::update()`/`ReturnAddrStack`）。

**B. 注入器**：待写 `CHAOSBPU`（`btb_target_sub`/`ras_top_sub`/`indirect_target_sub`(F5)/`direction_bitflip`(F1)）。重点：**喂给后端的错误投机流是否泄漏**，联合观测（是否 squash/错误路径投机 store/squash 后架构态==golden）。

**C. campaign**：{BTB 目标,返回栈栈顶,间接目标,方向位} × 联合观测。

**D. kernel**：难预测分支循环 + 紧跟 store→load 依赖链（method1 cdiv+rank-1 交错）、`call_ret_heavy.c`、`indirect_jmp.c`。

**E. 指标**：`P(squash 后架构态==golden)`（预期≈1）；与 §5.3 `spec_leak` 对照（投机泄漏是否同一签名）。

**F. 边界**：E2；gem5 `TournamentBP` ≠ V110 两级预测器（E3）。

**G. 工作量**：约 3 补丁（可与 §5.3 合并一轮）。

**H. 验收断言**：① `call_ret_heavy`/`indirect_jmp` golden 20 次重放一致；② `btb_target_sub`/`ras_top_sub`/`indirect_target_sub` 仅指向合法目标地址（≥1000 注入 `SimulatorError`=0）；③ 联合观测 `P(squash 后架构态==golden)` 可计算且≈1；④ 每个 fault mode ≥1 非 Inactive。

### 5.10 整数执行单元（P3，待实现 CHAOSExec，阴性对照）

**A. 目标与 hook**：ALU 结果、乘法器、移位器、NZCV。Hook `iew.cc` writeback 按 `opClass ∈ {IntAlu,IntMult,IntDiv}` 过滤。

**B. 注入器**：待写 `CHAOSExec`（`result_bitflip` 位段分层 [0:11]/[12:47]/[48:63]、NZCV 标志）。

**C. campaign**：opClass{IntAlu,IntMult,IntDiv} × 位段 × {结果,NZCV} × {bit_flip,stuck_at}。

**D. kernel**：整数 reduction、`MADD` 链、`SMULH`、`ADDS→B.cond` 条件链。

**E. 指标**：位谱；乘除端口 vs ALU `P_SDC` 比值；**阴性对照 `P_SDC(Int) << P_SDC(FSU/转发)`**（印证 method1 "整数路径完好" + Veritas 结论）。

**F. 边界**：E2；gem5 ALU 是功能模型（E3）。

**G. 工作量**：约 4 补丁。

**H. 验收断言**：① `MADD`/`SMULH` golden 20 次重放一致；② 位段分层 [0:11]/[12:47]/[48:63] 与 NZCV 均产生非零注入计数；③ 每个 opClass×位段 cell ≥1 非 Inactive；④ 阴性对照 `P_SDC(Int) << P_SDC(FSU/转发)` 成立（印证 method1 "整数路径完好"）。

### 5.11 PCE / 译码 / 系统级（S3/S4，依第 10 章排期）

- **PCE：L1D 返回通路**（`CHAOSL1DForward`，见 5.8）。
- **译码单元**（`CHAOSDecode`，P4，低优先级，可跳过）。
- **内存控制器 + DDR**（CHAOSMem 扩展 `addr_map_sub`/`ecc_logic_fault`，P3）。
- **RAS 机制逃逸**（`CHAOSRAS`，P1，元分析为主，见 8.1）。
- **系统级 NoC/HCCS/L3 一致性**（`CHAOSNoC`/`CHAOSHCCS`/`CHAOSCHI`，S4，E3/E4，独立子项目）。

---

## 第 6 章　SDC 规律研究

### 6.1 假设体系（预登记 + 诚实标注闭环状态）

| 假设 | 内容 | 真实状态（核查后） |
|---|---|---|
| H0 | 保护范围外结构（PRF/RAT/ROB/IQ/store buffer/L1 TLB）raw 即 escape | 预登记，待 formal（protectionModel 未实现） |
| H1 | read-trace `reads_before_overwrite` 决定 AVF：`P(SDC∣reads>0)` 跨单元一致 | 预登记（CHAOSPhysReg 有 read-trace） |
| H2 | 深窗口（ROB/PRF 容量大）→ 驻留长 → SDC 高，`d(P_SDC)/d(window)>0` | 预登记 |
| H3 | RAT 错与 PRF 错走同一传播路径（F5 替换 vs 位翻转的 read-trace 一致） | 预登记（待 CHAOSRenameMap） |
| H4 | 长驻留缓存（大 L2）→ 传播概率升高 | 预登记 |
| H5 | 字节相位（byte_lane_skew rol1/rol6）复现 core179 D1 撕裂移位签名 | ✅ **主线 structuralFault 已补齐 `8320daf`**（byte_lane_skew rol1 SDC xor 多位散布已验证）；侧分支闭环 93%；formal ptrskew_kernel 复现待跑 |
| H6 | AGU byte7 清零 → 规范内核地址非规范化 → 翻译故障（FS 才有效） | ⚠️ **侧分支**：FS 下钩子触发非零、复现 byte7 清零签名（`0xffffffc008b08f30→0xffffc008b08f30`），但 D2-only 50 注入→0 可观察失败，**定量谱可分未确立**；**主线无 CHAOSAddrPath** |
| H7 | PTW ECC on → spurious≈0 / off → spurious>0 | ✅ **主线 CHAOSPTW 已实现 `de48432`**（FS clearValidBit 已验证制造 spurious，5 注入 BecameInvalid:1，复现 core179 D3）；侧分支两机制各实证；完整 ECC on/off spurious 率定量待 formal |
| H8 | 逃逸集合分解（机理 A–F 归因） | 待 formal |
| H9 | 相位敏感性（F6 phaseOffset 的 `P_SDC` 曲线，`|offset|≥1` vs 0 比值 ≥5×） | 待 formal（复现 method3 塌方 100%→10–20%） |
| H10 | 签名可分性（向量 PRF 存储 vs FSU 数据通路 KS 检验可分） | 待 formal |

> **诚信说明**：H5/H6/H7 在侧分支（`origin/fi-h6-h7-fs-verify`、`origin/fix/paper-review-v1-honesty-hardening`）有真实运行验证（证据见 `docs/cases/core179-microarch-rootcause-synthesis/FI_DESIGN_SUPPLEMENT.md`），但**未并入 fi-wangxu 主线**。本文不谎称主线已闭环；需先实现 CHAOSLSQFwd structuralFault / CHAOSAddrPath / CHAOSPTW 到主线，再在主线复现验证。复现侧分支结论是 S1-5/S2-5 的验收内容。

### 6.2 位谱规律（对照 method3 现场）

- **FP 尾数主导 / 符号免疫**：method3 现场 float 尾数 85%（177/207）/ double 93%（331/355）/ 符号 0–1/562；侧分支 CHAOSLSQFwd `fp_fwd_kernel` 复现 100% 尾数 / 0% 符号。`fi_research/bit_spectrum.py` 输出 sign/exp/mantissa/popcount。
- **popcount 分布**：SVD 单比特中位 3（5/11 恰 1 位）；GEMM double 中位 28 最大 39（多比特主导，PinDrop 证实"向量内多比特 > 单比特"）；GEMM float 中位 12。
- **整数位谱**：整数数据 40.2% 案例有 >100% 精度损失（PinDrop）。

### 6.3 传播规律

- `reads_before_overwrite` 四分类把 AVF 分母拆细（Benign/Masked/SDC/Crash），`reads_before_overwrite=0` → Benign（AVF 分母）；`P(SDC∣reads>0)` 跨 RAT/ROB/PRF 的一致性验证（H1/H3）。
- 历史残留：F5 替换产生"读回值 == 其它活变量值"（method1 签名）。
- 暴露面公式（§2.2）验证：`Reachability × P_SDC × weight` 的分解。

### 6.4 相位/时序规律

- method3 触发率塌方：加一条 no-op ALU → 100%→10–20%（H=1/10, X=1/5，方向性非精确率）；F6 `phaseOffset` 的 `P_SDC` 曲线应复现（`|phaseOffset|≥1` vs 0 比值 ≥5×，H9）。
- 三必要条件：（store 推进 / 同 LLC 域 / 跨 cache line）去一归零。

### 6.5 保护交互规律

- ECC 前后对照（protectionModel，✅ `09e31d6`）：1-bit→Corrected、2-bit→poison/DetectedContained、≥3-bit→Latent；风险反转图机制已验证（`S7-5`：raw 2-bit numRawEscaped=1 vs secded 2-bit numDetectedContained=1，方向正确——ECC 把 raw escape 转为 contained DUE）。formal 多 seed 统计待 campaign cache 路径扩展。
- post-check escape：ECC 校验后数据通路损坏完全不受保护。
- `CHAOSRAS` 元分析：RAS 逃逸率按逃逸机理 A–F 归因（§8.1）。

### 6.6 跨单元敏感性排序（学术定位，预期 vs 已发表）

| 本实验单元 | 预期 | 对标论文 |
|---|---|---|
| LSU 转发 / FSU / PRF / RAT | 高 P_SDC | Veritas(HPCA'25)、Cross-ISA、PinDrop |
| 整数 ALU | 低 P_SDC（阴性对照） | Veritas（加法器低几个数量级） |
| L1I | 高 Crash（几乎总崩溃） | CHAOS |
| 系统级 | E3/E4 代理 | Gem5-MARVEL |

### 6.7 统计方法

Wilson 95% CI（scipy 独立复算误差 <1e-12）；重放一致性（G0，≥5% 样本重放）；0-SDC 上界 3/n；重尾检验（power-law 拟合）；KS 检验（签名可分性）。

---

## 第 7 章　SDC 诊断建议（基于 openEuler 系统日志，作为注入平台反哺接口）

> 本章为用户明确要求的维度③。**定位**：诊断规则引擎是注入平台的**反哺接口**而非独立工具主线（用户决定：产业落地以注入平台为主）。所有方法、规则、命令锚定 openEuler 系统日志形态，将 sdc-diagnosis 项目的《SDC诊断完整方法论.md》规则操作化为 openEuler 上的日志解析 + 判定流程。

### 7.1 诊断目标与范围

- 目标平台：鲲鹏 920（ARMv8.2-A，64 核 TaiShan v110 同构）+ openEuler 22.03 / 24.03。
- 目标：从 openEuler 主机侧日志（无 BMC 硬件遥测依赖）出发，识别 SDC 诱导机，输出"高/中/低/排除"四级置信度，最终导向 FA（硅片故障分析）+ 隔离。
- **与注入平台的接口**（§7.7）：formal 实验产出位谱指纹库 + 逐单元 P_SDC → 回填诊断权重先验 + 签名匹配。

### 7.2 openEuler 数据源与采集

| 数据源 | openEuler 位置/命令 | 用于 |
|---|---|---|
| 内核环缓冲区 | `dmesg` / `journalctl -k` / `/var/log/messages` | ESR_ELx 解码、Oops、Data Abort、Undefined Instruction |
| 系统日志 | `journalctl --since "..."`、`/var/log/messages`（rsyslog 时间戳 `MMM dd HH:MM:SS`） | 异常时间戳、进程、backtrace |
| 重启记录 | `last reboot`、`who -b`、`journalctl --list-boots` | 非计划重启频率（Step 2/P3） |
| iBMC SEL | `ipmitool sel list/elist`（或 Redfish `curl /redfish/v1/.../SEL/Entries`） | RAS Error Records、CE/UE、SError/SEA |
| EDAC/rasdaemon | `/sys/devices/system/edac/mc/mc*/{ce_count,ue_count}`、`ras-mc-ctl --status`、ghes_edac | RAS 静默性验证（Step 3/P5） |
| GHES/APEI | `dmesg \| grep -iE "arm64\|ras\|error\|serror\|sea\|hisilicon\|kunpeng"` | 硬件错误记录 |
| PMU | `perf stat -e armv8_pmuv3_0/...` | 微架构偏差（第 9 章监控场景复用） |

**openEuler 特有实证（core179 案例）**：`ESR 0x96000044`（DABT, WnR=1, FSC=L0 翻译故障）在 `/var/log/messages` 中以重复 `WARN`/`Oops` 记录；ghes_edac 注册 32 DIMM 零 CE/UE、rasnode.ko 192 核×5 ERR 节点全零差异——即"RAS 静默"的铁证。openEuler 对 spurious 翻译故障保留 chronic 的 WARN 记录，是定位 SDC 的关键日志指纹。

### 7.3 日志解析规则

**ESR_ELx EC/FSC 解码表**（`dmesg`/`journalctl -k` 中标 `EC = 0x..`、`FSC = 0x..`）：

| EC | 异常 | 与 SDC 的相关性（参考比率） |
|---|---|---|
| 0x00 | Undefined Instruction | 高（17.80x） |
| 0x20/0x21 | PXN/UXN Permission Fault | 高（20.03x） |
| 0x24/0x25 | Data Abort（SP-relative 为高相关） | 高（20.77x） |
| 0x26 | Alignment Fault | 低 |
| 0x2F | SError | 取决于有无有效 RAS Record |
| 0x3C | BRK/BKPT | 中（6.92x） |

**异常类型加权表**（`SDC_score = Σ(类型次数×权重) + 核浓度加分 + 多应用加分 + 向量/NZCV 加分`）：

| 类型 | 参考比率 | 权重 |
|---|---|---|
| 嵌套 SError / 递归异常 | 59.35x | ★★★★★ |
| Data Abort (SP-relative) | 20.77x | ★★★★ |
| PXN/UXN Permission Fault | 20.03x | ★★★★ |
| Undefined Instruction | 17.80x | ★★★★ |
| SError 无有效 RAS Record | — | ★★★★ |
| BKPT/BRK | 6.92x | ★★★ |
| Data Abort（通用）/ Alignment / Lockups / Oops | ~1x | ★★/★ |

> **诚实标注**：上述"参考比率"来自 sdc-diagnosis 项目的方法论文献引用，非本方案自有实验产出。formal 实验后，逐单元 P_SDC 将回填这些权重，使其从"论文引用"升级为"实验依据"（§7.7）。

### 7.4 七步诊断流程（每步附 openEuler 命令）

```
Step 1 Top-N 候选筛选（按异常总量排序，workload-agnostic）
Step 2 重启异常检测（30天窗口：通用≥6次 / AI≥3次）
Step 3 RAS 静默性验证（排除响亮故障）
Step 4 核心浓度分析（单核>60% + 兄弟核聚合 + 多应用≥2 → 强 SDC）
Step 5 异常类型加权（ARM64 高相关类型加分）
Step 6 维修历史交叉验证（30天反复误诊/未诊 → 强 SDC）
Step 7 独立 FA 确认（目标复现率 70%）
```

**Step 1 Top-N**：`journalctl -k | grep -cE "ESR|Data Abort|Oops|Undefined|SError"` 按服务器汇总排序。

**Step 2 重启**：`last reboot | head -50`、`journalctl --list-boots | wc -l`（30 天窗口）；通用 ≥6 / AI ≥3 → 进入 Step 3。

**Step 3 RAS 静默**：
```bash
dmesg | grep -iE "arm64|ras|error|serror|sea|data.abort|hisilicon"
cat /sys/devices/system/edac/mc/mc*/ce_count
cat /sys/devices/system/edac/mc/mc*/ue_count
grep -i "serror\|SError" /proc/interrupts
ipmitool sel list | tail -100
```
判定：RAS Error Records 无 CPU 条目 → SDC 候选；SError+有效 Record → 响亮故障排除；SError 无 Record → SDC 候选；ECC 多比特 → 内存故障排除。

**Step 4 核心浓度**（最关键）：同构鲲鹏 64 核统一 60% 阈值；SMT 兄弟核聚合；多应用 ≥2。
```bash
# 按 CPU 号聚合异常（从 journalctl -k 解析出每次 Oops 的 CPU 字段）
journalctl -k | grep -E "CPU[ :]+[0-9]+" | awk '{...聚合 per-core count...}'
```

**Step 5 异常加权**：按 §7.3 权重矩阵计分。
**Step 6 维修历史**：查维修工单的误诊/未诊记录（30 天窗口）。
**Step 7 FA 确认**：第三方硅片 FA 复现。

### 7.5 正向规则 P1–P11 与负向规则 N1–N10

**铁律（IRON RULE）**：

- **P1 单核异常集中度**：1 周回溯内单核（或兄弟核聚合）异常占比 >60%（同构）或 >40%（little cluster）。鲲鹏 920 同构用 60%。原理：软件异常均匀分布，硬件缺陷集中单核。
- **N10 单次测试阴性不可靠**：PinDrop 证明快照测试遗漏一个数量级故障，机可能在测试多年后首次失败；SDC 测试有随机性，单次"通过"不代表健康。必须建 ≤30 天重访的连续测试机制。

**正向规则 P1–P11（每条约日志判据）**：

| 规则 | 条件 | openEuler 日志判据 + 命令 |
|---|---|---|
| P1 | 单核浓度 >60% + 兄弟核聚合 + 多应用 ≥2 | `journalctl -k` 按 CPU 号聚合集中度 |
| P2 | ≥2 应用在同一核心失败 | 崩溃进程名 ≥2 且同核心 |
| P3 | 30 天非计划重启通用≥6/AI≥3 | `last reboot` |
| P4 | 高相关异常类型同核出现 | §7.3 类型解码 |
| P5 | RAS 静默 | Step 3 命令全零 |
| P6 | 30 天反复误诊/未诊 | 维修工单 |
| P7 | 独立 FA 复现 | ≥70% |
| P8 | 向量指令 SDC 信号 | NEON 跨核对比不一致 |
| P9 | NZCV 条件分支异常 | 控制流偏离 |
| P10 | 失败持续性（≥2 季度持续失败） | PinDrop 连续测试 |
| P11 | 兄弟核共失效 | SMT 兄弟同时失败 |

**负向规则 N1–N10（命中任一即排除）**：

| 规则 | 条件 |
|---|---|
| N1 | 异常均匀分布 → 软件 |
| N2 | 单应用 + 相同 backtrace → 软件缺陷 |
| N3 | RAS 有明确 CPU 硬件故障 → 响亮故障 |
| N4 | fuzzer/测试工具引发 → 排除 |
| N5 | crash dump 有硬件诊断 → 非静默 |
| N6 | 已知 Bug/CVE 模式 → 软件根因 |
| N7 | 大规模同步异常 → 软件/配置变更 |
| N8 | 缺内存屏障 → 软件移植 |
| N9 | 环境瞬态 → 环境异常 |
| N10 | 单次测试阴性 → 不可靠，需连续测试 |

### 7.6 置信度模型

| 级别 | 条件 | 处理 |
|---|---|---|
| 高置信度 | P1+P2+P3+P5 +（P4 任一类型 / P8 / P9） | 立即隔离 + FA |
| 中置信度 | P1+P2+P5（缺 P4） | 增加测试覆盖/延长观察 |
| 低置信度 | 仅 P3 或 P6 | 标记观察，监控 CE/PMU |
| 排除 | 命中任一 N 规则 | — |

### 7.7 注入实验 → 诊断反哺（注入平台 ↔ 诊断接口）

1. **位谱指纹库 → 日志签名匹配**：第 5/6 章每个单元的 SDC 位谱（sign/exp/mantissa/popcount）建成指纹库，供"现场看到某位谱 → 反推候选单元"（留一法验证，见 §8.3）。
2. **单元 P_SDC → 类型加权**：formal 得到的逐单元 P_SDC/P_DUE 回填 §7.3 权重的先验，使权重矩阵有实验依据而非纯论文引用。
3. **method1/2/3 签名 → 规则库**：core179 的零塌缩/撕裂移位子族、ESR `0x96000044` 重复 WARN 等具体签名沉淀为规则，扩充 `sdc-diagnosis/skills/.../case_knowledge`。

### 7.8 实战示例：core179 六案全流程回放

- **事实**：88 起事件 100% 收敛 CPU179、5/6 命中同一指令 `find_busiest_group+0x140`、零塌缩（FSC=L3）/撕裂移位（FSC=L0）两子族、RAS 全静默（ghes_edac 零 CE/UE、rasnode 全零差异）。
- **规则命中**：P1（100% 单核浓度，远超 60%）+ P5（RAS 静默）+ P10 类（5/6 复发同指令）+ N3 未命中（无 RAS 条目）→ **高置信度 SDC** → 建议 offline + FA + RMA。
- **与注入对照**：`byte_lane_skew rot1`（H5，侧分支复现撕裂移位签名 93% 检出）；`CHAOSAddrPath` byte7 清零（H6，侧分支复现零塌缩 FSC=L0 签名）。

### 7.9 与 sdc-diagnosis 工具链对接

- 本文第 7 章是《SDC诊断完整方法论.md》的 openEuler 操作化落地；规则编号（P1–P11/N1–N10）、铁律标注、置信度分级保持一致，引用而非重写。
- `sdc-diagnosis/skills/sdc-diagnosis/` 作为规则引擎载体；本文 7.7 的反哺结果回写 `case_knowledge` 与 `case_records`，诊断规则需版本化（新增规则进 `rules/flight-rules.md` 时同步 bump 版本）。

---

## 第 8 章　对芯片开发设计者的抗 SDC 改进建议

> 本章为用户明确要求的维度④。**定位（用户决定）**：指导芯片设计者**如何设计更能抵抗 SDC 的芯片与微架构**——在哪里加保护/冗余/校验、如何抗相位竞争与状态泄漏，**而非 DFT 测试向量**。建议方向基于 formal 实验的逃逸集合分解 + 保护优先级排序，每条标注"待 formal 验证"或"已由现场/侧分支证据支持"。

### 8.1 SDC 逃逸集合分解方法（formal 后产出）

跑完所有 formal cell 后，按逃逸机理（§6.5、Task S5）归因：

```
总 P_SDC(V110 代理, w) = Σ_unit [ Reachability(unit) × P_SDC(unit, w, protection-aware) × weight(unit) ]
weight(unit) ≈ 未受保护状态位数 × 占用率 × 平均驻留周期（gem5 stats 估计）

逃逸机理归因（每个 SDC 事件打标）：
  A. RAS 范围外结构（PRF/RAT/ROB/IQ/store buffer/L1 TLB/L2 victim）→ raw = escape
  B. SED-only 结构（L1I data 代理）的 ≥2-bit
  C. 任意结构 ≥3-bit（超 SECDED）
  D. post-check escape（ECC 后数据通路）
  E. ECC 逻辑自身故障（漏检/误纠）
  F. 毒化传播丢失
```

产出：逃逸集合分解饼图（按负载分组）+ 逐单元"保护投资回报"排序表。

### 8.2 保护优先级排序（抗 SDC 加固选址）

| 结构 | 当前保护（代理） | 抗 SDC 设计建议方向 | 依据 | 证据等级 |
|---|---|---|---|---|
| PRF/RAT/ROB/IQ/store buffer | none（TRM 惯例） | **最高优先级加保护**：parity 或 duplicated copy + 周期校验；RAT/freelist 的"活/空闲"状态位单独 parity | RAS 范围外 + 高贡献重灾区；method1/3 指向 | 现场 E2 + 待 formal |
| L1 TLB | none（flop 实现） | parity（条目级）；L2 TLB/walk cache 已 parity_interleaved，校 L1 | method3 已定位 | 现场 E2 |
| L1I data | sed 代理 | 评估 SED→SECDED 对双比特静默的削减 | §5.8 SED vs SECDED 实验 | 待 formal |
| LSU 转发通路 | none | 转发数据 parity/CRC + 转发源 seqNum 校验；**转发 CAM 匹配决策点**单独保护 | method2 位谱吻合；core179 D1 签名 | 现场 E2 |
| PTW | 视保护 | 读 ECC（descriptor array）；clearValidBit 类 2-bit 不可纠需 SECDED | H7（ECC on→spurious≈0，侧分支） | 侧分支 E2 |
| L2 victim | none | 保护（victim 比数据更易逃逸） | §5.8 victim 高于 data 预期 | 待 formal |

> **预期结论方向**（待 formal 验证）：乱序后端（PRF/RAT/ROB）+ L1 TLB 是"RAS 范围外 + 高贡献"的重灾区，优先级高于再加固已有 SECDED 的缓存。

### 8.3 抗 SDC 微架构机制设计建议（核心创新，超越"加 ECC"）

单纯加 ECC/parity 是"结构级"加固；本方案基于 F5/F6/PCE 故障模型，提出**机制级**抗 SDC 设计建议：

1. **抗状态泄漏（method1）**：
   - **PRF 活性回收的双校验**：freelist 标记"空闲"前，强制校验该 physReg 不在任何活 RAT 映射中（commit RAT + front RAT 双查）；method1 的"活寄存器误标空闲"在此被拦截。建议硬件：recycle 前的 `in_use` 断言。
   - **投机流 squash 的物理写回溯**：squash 时显式 invalidate 错误路径 μop 的 PRF 写（而非仅回滚 RAT 指针），防止 spec_leak。建议：squash 路径 PRF 写打 `speculative` 标记，squash 时批量清零。

2. **抗相位竞争（method3）**：
   - **store→load 转发的时序护栏**：转发决策与数据组装分离到不同流水级，避免"同相位窗口内转发源选择 + 数据读出"的竞态；或对转发数据加 parity（D1 路径）。method3 的"加一条 no-op ALU 即塌方"证明相位敏感，建议相位解耦设计。
   - **地址通路 byte-lane 一致性校验**：AGU→MMU 地址呈现加 byte-lane parity，core179 D2 的"byte7 清零"在此被检出（2/5 例确凿签名）。

3. **抗 post-check escape（PCE）**：
   - **ECC 后数据通路的延伸保护**：ECC 校验通过后到进入 PRF/转发通路之间的数据段，是 SDC 的"必然出口"（完整 RAM 保护把 SDC 逼到此处）。建议该段加 parity 或与 ECC 联动校验（CHAOSL1DForward 验证该段 P_SDC 显著高于 raw）。

4. **抗合法域替换（F5）**：
   - **编号域冗余校验**：RAT physRegIdx、freelist free-bit、LSQ 转发源 seqNum、TLB pfn 等"编号/指针"字段，是 F5 合法域替换的靶点。建议这些字段加 parity 或 range-check（注入前 `f5_substitute` 的"合法域校验"反向证明：若仿真器都要校验合法性，硬件更应校验）。

### 8.4 与 Noverse N1 TRM 保护基线的差距分析

逐结构对比 N1 Table 9-1 与 V110 推断保护表，标出差距清单 + 建议补齐项（E4 项进"待校准清单"，不进设计建议正文）。这是 §8.2 建议的"当前保护"列的依据来源。

---

## 第 9 章　学术研究与产业产出

### 9.1 论文骨架与贡献点

**标题方向**：《ARM64 服务器 CPU 微架构级 SDC 注入、规律刻画与抗 SDC 设计闭环：以鲲鹏 920（TaiShan V110）为例》。

**贡献点**：
1. 对 RISC 服务器核（非 x86）的逐微架构单元 SDC 暴露面量化（P_SDC/P_DUE/P_escape/Reachability + Wilson CI），raw 与 protection-aware 两组；
2. F5（合法域替换）+ F6（相位偏移）+ PCE（post-check escape）故障模型：把"位翻转以外的逻辑决策层与相位故障"做成可复现注入原语；
3. protection-aware 分层 + 逃逸集合分解的规范（raw 敏感性 vs protection-aware 逃逸分开报）；
4. **仿真-现场对照生态效度范式**：位谱定量吻合（method3 85/93/0-1）、触发条件复现（method3 三必要条件塌方）、签名匹配（method1 历史残留、core179 D1/D2/D3）作为仿真忠实度的可证伪检验；
5. read-trace 四分类把 AVF 分母拆细，使 AVF/SDC 跨研究可对比；
6. **抗 SDC 微架构机制设计建议**（§8.3）：从"加 ECC"上升到"抗状态泄漏/抗相位/抗 PCE"的机制级设计。

### 9.2 目标会议与对标

DSN / PRDC / ASPLOS / HPCA / MICRO；对标 Veritas(HPCA'25)、PinDrop(HPCA'26)、SEVI(ASPLOS'26)、Cross-ISA、Differential FI、CHAOS、Gem5-MARVEL、DelayAVF(MICRO'24)、Harpocrates(ISCA'24)。已有的 `paper_zh.md`（core179 五转储取证）是本方案的一个 case-study 子集。

### 9.3 产业产出（用户决定：注入平台为主）

1. **gem5-fi 故障注入平台**（本文第 4–5 章 + campaign 框架 + 7 已有 + 11 待实现注入器）——**主产出**，可直接用于芯片设计验证阶段的 SDC 暴露面量化与抗 SDC 机制评估；
2. **抗 SDC 微架构设计指导**（第 8 章）——注入平台的下游产物，指导芯片设计者选址与机制设计；
3. **openEuler SDC 诊断规则引擎接口**（第 7 章，反哺接口）——注入平台产出的位谱指纹库 + 单元 P_SDC 回填诊断权重，非独立工具主线。

### 9.4 诚实的结论边界（写进论文与工具文档）

- 所有 `P_SDC` 是 gem5 O3 + C2-KP 代理下的**条件概率**，非产品现场 FIT；无 raw device rate → 不换算 FIT。
- 系统级（L3 分区/bufferless NoC/HCCS）结论 E3/E4，需实机/RTL/厂商资料校准。
- "最该加保护的结构"排序基于 N1 TRM Table 9-1 代理；若 V110 实际保护表不同则需重估。
- 单/多缺陷不可由仿真裁决；本方案主张的是"复现签名到可控环境 + 量化暴露面差异 + 提供抗 SDC 机制建议"。
- 本机（cpu179）为故障机 → 关键结果必须第二台健康机复现（Task S6-1，至今未做，所有现场数据标"单机结果，未确认"）。
- H5/H6/H7 在侧分支验证，主线需补齐注入器后复现（§6.1）。

---

## 第 10 章　分阶段执行计划

### 10.1 阶段总览

| 阶段 | 内容 | 依赖 | 工作量 | 现状 |
|---|---|---|---|---|
| S0 基础设施 | regen params 干净重建（已完成）+ P0 pilot 复现；campaign.py v1（已完成 `f8aecc7`）；kp920_proxy ✅`1564328`；manifest v2 ✅`105bc0f`；protectionModel v1 ✅`a6c5b9c`（.cc 后处理待续）；已知缺陷修复（附录 D 已完成 D1-D6） | 无 | ~10 补丁 | campaign v1/kp920_proxy 待续；manifest v2/protectionModel 待续 |
| S1 P0 单元 | PRF 扩/F3（✅）；RAT（✅ CHAOSRenameMap `c5c8c96`）/freelist（✅ CHAOSFreeList `379e11c`）；ROB（✅ CHAOSROB `7d0756d`）；LSU 转发扩（D2 ✅+structuralFault 待补+AddrPath ✅ `ffd041e`） | S0 | ~20 补丁 | PRF/RAT/AddrPath 已有；FreeList/ROB/structuralFault 待实现 |
| S2 P1 单元 | IQ（CHAOSIQ）；FSU（CHAOSFPU）；TLB/SysReg/PTW + FS checkpoint；L3 pairedSector | S1 | ~18 补丁 | ArmTLB/ArmSysReg 已有基础；IQ/FPU/PTW/AddrPath 待实现 |
| S3 P2/P3 单元 | L1D 字段级+PCE；L2+victim+size sweep；L1I 语义字段；整数 Exec；BPU；内存控制器 | S1 | ~16 补丁 | 全待实现 |
| S4 系统级 | CHAOSCHI/CHAOSNoC/CHAOSHCCS（E3/E4，独立子项目） | S2 | ~20 补丁 | 全待实现 |
| S5 元分析+建议 | CHAOSRAS + ras_escape_analysis；逃逸集合分解；抗 SDC 机制建议（§8.3） | S1–S4 | ~4 补丁 | 待 formal |
| S6 健康机复现（贯穿） | 关键结果第二台健康机复现 | 每阶段 | — | **至今未做**（现场数据标"单机未确认"） |
| S7 实机校准（授权后） | 鲲鹏实机 RAS/EINJ 枚举，E3/E4 升级 | 授权机 | — | 待授权 |

### 10.2 关键工程流水线

- **SE campaign**：`tools/campaign.py campaigns/<unit>.yaml` → 网格 → 每 cell n=384 → 单故障 → 六级分类 + read-trace + 位谱 + provenance → Wilson CI + 5% 重放 → artifacts。
- **FS campaign**（TLB/PTW/AGU/系统级）：Atomic boot → `m5 checkpoint` → restore 切 O3 → ROI 单故障 → 分类（raw socket 3456 抓 Linux 日志）。
- **构建命令**（每次源码改动后）：`cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh && scons build/ARM/gem5.opt -j16`；运行前 `source /home/sdc/gem5-deps/env.sh` 设 LD_LIBRARY_PATH。

### 10.3 任务清单（精简索引，详见附录 G 任务卡）

- **S0-1** 干净重建（本轮已完成：恢复源码-二进制一致）。
- **S0-2** campaign.py v1 ✅ `f8aecc7` + manifest v2 schema ✅ `105bc0f`（runner/campaign 对 v2 字段解析待续）。
- **S0-3** ~~protectionModel 层 + classify 九类扩展~~ classify 九类 + CHAOSCache protectionModel 参数面 ✅ `a6c5b9c`；.cc ECC 后处理待续。
- **S0-4** 已知缺陷修复（附录 D，D1–D6 已完成 `0ae28fe`/`56023c3`/`58be899`/`4ed645b`）：CHAOSArmTLB 时间窗（D1 ✅）、CHAOSLSQFwd 64 位掩码（D2 ✅）、CHAOSMem 永久重放（D3 ✅）、CHAOSArmSysReg 时间窗（D4 ✅）、概率比较统一（D5 ✅）、NULL 宿主 warn（D6 ✅）、mask==0 早退（D7 Cache/ArmTLB/ArmSysReg/PhysReg 已有）。D9（G6 广触发）、D10（G7 sanitizer）deferred。
- **S1-1** CHAOSPhysReg F3+semanticRole（✅ `7f538c4`）；**S1-2** CHAOSRenameMap（✅ `c5c8c96`）；**S1-3** CHAOSFreeList（✅ `379e11c`）；**S1-4** CHAOSROB（待实现）；**S1-5** CHAOSLSQFwd 扩展（D2 ✅+structuralFault 待补+stale_line_replay+fwd_source_sub）；**S1-5b** CHAOSAddrPath（✅ `ffd041e`）。
- **S2-1** CHAOSIQ；**S2-3** CHAOSFPU；**S2-5a** CHAOSArmSysReg 扩展（F5+D4）；**S2-5b** CHAOSArmTLB F5+targetField；**S2-5c** CHAOSPTW ✅ `de48432`（侧分支→主线，FS clearValidBit 验证）；H7 formal 待续。
- **S3-2** CHAOSL1DForward；**S3-4** CHAOSExec；**S3-5** CHAOSBPU；**S3-6** CHAOSMem 扩展。
- **S5-2** CHAOSRAS；**S5-3** 逃逸集合分解 + 抗 SDC 机制建议（§8.3）。
- **S6-1** 第二台健康机复现（贯穿，最高诚信要求）。

---

## 第 11 章　质量闸门与验证纪律

### 11.1 注入器闸门 G0–G7（核查后真实状态）

| 闸门 | 名称 | 现状（核查后） |
|---|---|---|
| G0 | 可重放性（同配置 20 次日志一致） | ✅ 已验证（本轮 golden `f247ef3fe6f02cfd` 复现） |
| G1 | 64 位掩码 | ✅ Reg/PhysReg；⚠️ LSQFwd 待修（D2，`bitset<32>`+`&0xff`） |
| G2 | write-path stuck | ✅ 已验证（PhysReg[80] `00ff0000dee1f5d0`） |
| G3 | cache 安全接口（getTags） | ✅ 已验证 |
| G4 | 内存边界/权重 | ✅ 已修复 |
| G5 | 单故障纪律 + 证据日志 | ✅ 已验证 |
| G6 | 最小注入间隔 | ✅ Cache/Mem；⚠️ 新注入器必须内置；broad triggers（pc/committedInst/event）未实现 |
| G7 | 零新增警告 | ✅ 常规（-Wswitch/-Wunused）；⚠️ ASan/UBSan 构建受阻（socket configure 阻塞），deferred 到 CI |

### 11.2 补丁纪律（每任务通用，沿用 CLAUDE.md）

1. 一补丁一单元；2. 提交前真机自测（三步自验证：干净构建 + 真机功能验证 + 不相关回归）；3. `make sync_chaos` 对齐双副本（Makefile:56–66，vendored 为权威）；4. 回归三件套（`prob=0` 对照 + 锚点哈希 + 零警告）；5. 推送 `fi-wangxu`（非 main）；6. 不附 `Co-Authored-By: Claude` 尾注。

### 11.3 文档与结论级验收

1. 每个结论挂 E1–E4，E4 不进设计建议正文；2. 每份 summary 复述三条诚实边界（不换算 FIT / 系统级 E3-E4 / 单机未确认）；3. 未健康机复现的标"单机结果，未确认"；4. 阴性对照如实报告；5. 侧分支已验证能力并入主线前标"侧分支已验证，主线待复现"。

---

## 附录 A　注入器与 hook 点总表（源码核对版，2026-08-30）

### A.1 已有注入器（13 个，含 CHAOSAddrPath/CHAOSRenameMap/CHAOSFreeList/CHAOSPTW/CHAOSROB/CHAOSIQ）

| 注入器 | 目标单元 | Hook 位置（已核实） | 范式 | 优先级 | 真实模式（已核实） |
|---|---|---|---|---|---|
| CHAOSReg | 架构寄存器 | 自调度 attackEvent | C（Python 显式） | 已验证 | bit_flip/stuck_at_zero/stuck_at_one/random；64位 mask；targetRegIdx；XZR 跳过 |
| CHAOSPhysReg | O3 物理寄存器堆 | `regfile.hh`（读/写 stuck）、`free_list.hh`（isFree）、`cpu.hh:478-489` | B（状态注入） | P0 主力 | phys/arch_frontend/arch_commit；int/fp/vector/both；vecLaneWidth/Offset；64位 mask；G2 write-path stuck |
| CHAOSCache | cache 数据字节 | 事件驱动遍历（`getTags()`，G3） | C（`_pre_instantiate`） | P2/P1 | 64位 mask；targetBlockAddr/targetByteOffset 定向；maxFaults（G5）；≥1cycle（G6） |
| CHAOSMem | AbstractMemory 字节 | `AbstractMemory::access` Packet RMW | C | P3 | 闭区间（G4）；权重修复；64位 |
| CHAOSLSQFwd | store→load 转发数据 | `lsq_unit.cc:1493-1499`（`cpu->lsqFwd`） | A（自挂载） | P0 | ✅ D2 已修（UInt64 + maskWidth 多字节，bit32/63 可注入）；仅 bit_flip/stuck_at_zero/stuck_at_one；**无 structuralFault（已回退，待补齐）** |
| CHAOSArmTLB | D-TLB pfn | `arch/arm/tlb.cc:164-168`（`tlb->chaosTLB`） | A（自挂载，FS） | P1 | bit_flip/stuck_at_zero/stuck_at_one；**无 targetField/protectionModel/pfn_to_mapped（待扩展）** |
| CHAOSArmSysReg | ARM 系统寄存器 MRS 读值 | `arch/arm/isa.cc:39,452-457` + `isa.hh:179-180`（`isa->chaosSysReg`） | A（自挂载，FS） | P1 | bit_flip/stuck_at_zero/stuck_at_one/random；`targetRegs` 白名单（miscRegName 解析）；**无 value_to_legal(F5)（待扩展）** |
| **CHAOSAddrPath** | AGU 地址通路（P-D2） | `lsq.cc sendFragmentToTranslation`（`cpu->addrPath`，`request.hh setVaddr`） | A（自挂载，FS+O3） | P1 | byte7 清零复现 core179 D2；byteOffset 0-7/-1随机；tick 时间窗；rng lambda 修复 |
| **CHAOSRenameMap** | RAT 重命名表（F5） | `rename_map.hh` setEntry() + `cpu->frontRenameMap()` | B（attackEvent 自驱动） | P0 | map_bitflip/f5_substitute/f4_field_stuck 三模式；合法域校验（numLegalityRejects）；method1 历史残留 |
| **CHAOSROB** | ROB 重排序缓冲 | `rob.hh` readHeadInst() + `cpu->robAccess()` | B（attackEvent 自驱动） | P0 | entry_bitflip（seqNum 翻转 200696→200697）/ exc_suppress（清 fault，合法性校验）/ spec_leak（deferred） |
| **CHAOSIQ** | 发射队列 | `dyn_inst.hh` readySrcIdx/renamedSrcIdx + `cpu->robAccess()`（ROB 头代理） | B（attackEvent 自驱动） | P1 | src_ready_bitflip（已验证 src0 1→0 missed wake）/ tag_sub（F5 交换 src tag）/ wake_phase/wake_omit（deferred 需 IQ timing hook） |

### A.2 待实现/待扩展注入器（9 个）

| 注入器 | 状态 | Hook 位置 | 任务 | 侧分支参照 |
|---|---|---|---|---|
| CHAOSRenameMap | ✅ 已实现 `c5c8c96` | `rename_map.hh` rename()/setEntry() + `cpu->frontRenameMap()` | ~~S1-2~~ done | — |
| CHAOSFreeList | ✅ 已实现 `379e11c` | `free_list.hh` addReg()/isFree() + `cpu->physFreeList()` | ~~S1-3~~ done | — |
| CHAOSROB | ✅ 已实现 `7d0756d` | `rob.hh` readHeadInst() + `cpu->robAccess()` | ~~S1-4~~ done | entry_bitflip/exc_suppress 已验证；spec_leak deferred |
| CHAOSIQ | ✅ 已实现 `f7a5d72` | `dyn_inst.hh` readySrcIdx/renamedSrcIdx + `cpu->robAccess()` | ~~S8-1~~ done | src_ready_bitflip/tag_sub 已验证；wake_phase/wake_omit deferred |
| CHAOSFPU | 新写 | `iew.cc` writeback（Float*） | S2-3 | — |
| CHAOSExec | 新写 | `iew.cc` writeback（Int*） | S3-4 | — |
| CHAOSL1DForward | 新写（PCE） | `lsq_unit.cc` load 回填（ECC 后） | S3-2 | — |
| CHAOSBPU | 新写 | `cpu/pred/` lookup()/BTB::update() | S3-5 | — |
| CHAOSExMon | 新写 | `lsq_unit.cc` 独占监视器 FSM | S3-7 | — |
| **CHAOSAddrPath** | ✅ 已实现 `ffd041e`（从侧分支移植+主线纪律） | `lsq.cc` sendFragmentToTranslation 前 | ~~S1-5b~~ done | `origin/fi-h6-h7-fs-verify`（H6，已并入主线） |
| **CHAOSPTW** | ✅ 已实现 `de48432`（从侧分支移植+主线纪律） | `arch/arm/table_walker.cc doLongDescriptor` | ~~S2-5c~~ done | `origin/fi-h6-h7-fs-verify`（H7，已并入主线） |

另有扩展模式：CHAOSMem `addr_map_sub`/`ecc_logic_fault`、CHAOSCache `targetField`+`protectionModel`、CHAOSArmTLB `pfn_to_mapped`/`targetField`/`protectionModel`、CHAOSArmSysReg `value_to_legal`、CHAOSLSQFwd ✅`structuralFault`(`8320daf`)/`stale_line_replay`/`fwd_source_sub`/`phaseOffset` + D2 ✅、CHAOSDecode（低优先级）、CHAOSRAS、CHAOSCHI/CHAOSNoC/CHAOSHCCS（S4）。

### A.3 宿主访问器（零新增所需，已核实）

`cpu->physRegFile()` / `physFreeList()` / `frontRenameMap()` / `commitRenameMapAccess()`（`cpu.hh:478-489`）、`cache->getTags()`（G3）、`make sync_chaos`（Makefile:56–66，vendored 为权威）。

---

## 附录 B　现场案例对照实验索引

| 案例 | 对照任务 | 关键验收锚点 |
|---|---|---|
| method1（Cholesky `x[0]`） | S1-2/S1-3/S1-4/S1-5/S3-5 | 历史残留 P>0 且 Fisher p<0.05；popcount 中位 >16；numeric/compute 比值 ∈[2,8]；**初步锚点：F5 on accum_kernel X9 → fails=1（`09b6424`）** |
| method2（`x10` 垃圾指针） | S1-1/S2-5b/S2-5a | ESR DFSC 分布 vs `0x96000004`；AGU byte7 FAR MSB=0x00 占比；三根因签名打分 |
| method3（LSU 转发相位） | S1-5/S2-1/S2-3 | H5 复现 93%（侧分支，主线补 structuralFault 后）；位谱尾数∈[80%,100%]/符号∈[0%,2%]；相位塌方比 ≥5×；三必要条件去一归零；GEMM popcount 中位∈[8,40] |
| core179 六案 | S1-5（H5）/ S2-5b（H6）/ S2-5c（H7） | 撕裂移位（rol1）、零塌缩（byte7）、PTW ECC 对照 |

**公共纪律**：每个对照结论注明"gem5 代理复现（E2/E3）"而非"现场等同"；现场数据为既有事实，本方案只做"签名匹配度"评估。

---

## 附录 C　鲲鹏 920 微架构参数 → gem5 配置映射表

| V110 参数 | gem5 参数（kp920_proxy） | 等级 |
|---|---|---|
| 4-wide 发射 | fetch/decode/rename/issue/dispatch/commit=4 | E1 |
| ROB"规模适中" | numROBEntries=128（扫描{96,128,160}） | E3 |
| 每调度器 ~33 项 | numIQEntries=66（统一 IQ 近似，局限） | E3 |
| Int 物理寄存器 ~128–160 | numPhysIntRegs=160（扫描{128,160,192}） | E3 |
| 双 FSU | numPhysFloatRegs=192 + FUPool FADD lat4/FMADD lat7 | E3 |
| 3 ALU+1 复杂 | IntALU×3 + IntMultDiv×1(lat4) | E1 |
| LQ48/SQ42 | LQEntries=48/SQEntries=42 | E3 |
| L1I/L1D 64KiB/4-way/64B | classic size/assoc | E1 容量/E3 保护 |
| L2 512KiB | classic（sweep{256KiB,512KiB,1MiB}） | E1 容量 |
| L3 分区 Tag/Data 分离 | pairedSector（代理）/ Ruby CHI（S4） | E3/E4 |
| store 转发 6–7cy | CHAOSLSQFwd phaseOffset 实验域 | E3 |
| bufferless NoC | Garnet 偏转代理 | E4 |
| HCCS 400GB/s | 双 NUMA 代理 | E4 |

---

## 附录 D　现有实现已知缺陷清单（源码分析发现，须修复）

| # | 级 | 缺陷 | 位置 | 修复任务 | 现状 |
|---|---|---|---|---|---|
| D1 | P0 | CHAOSArmTLB `firstClock/lastClock` 未检查 | `CHAOSArmTLB.cc` | S0-4 | ✅ 已修 `56023c3`（startup + curTick 时间窗，三组 FS 对照验证） |
| D2 | P0 | CHAOSLSQFwd `faultMask` UInt32 且 `&0xff` 单字节 | `CHAOSLSQFwd.cc/.hh`（`bitset<32>`） | S0-4 | ✅ 已修 `0ae28fe`（UInt64 + maskWidth 多字节，bit32/63 注入验证） |
| D3 | P0 | CHAOSMem `checkPermanent()` 重放一次后 update=false | `CHAOSMem.cc` | S0-4 | ✅ 已修 `4ed645b`（去掉 update=false + 重施加 stat，numPermanentReapplies=573157 验证） |
| D4 | P0 | CHAOSArmSysReg 时间窗 1GHz 假设 | `CHAOSArmSysReg.cc` | S0-4 | ✅ 已修 `58be899`（startup 用 (Tick)first_clock，消除 *1000；FS 端到端注入待 checkpoint） |
| D5 | P0 | 概率比较不统一（`>` vs `>=`） | TLB/SysReg vs LSQFwd | S0-4 | ✅ 已修 `56023c3`+`58be899`（统一为 `>=`） |
| D6 | P0 | CHAOSArmTLB NULL 宿主静默失败 | `CHAOSArmTLB.cc` | S0-4 | ✅ 已修 `56023c3`（NULL tlb 改为 warn） |
| D7 | P0 | `mask==0` 不早退 | 多注入器 | S0-4 | ⚠️ Cache/ArmTLB/ArmSysReg/PhysReg 已有；Reg/Mem 无显式早退（无害，mask=0 走随机生成或 no-op） |
| D8 | P1 | CHAOSReg `maxRegIdx=0` 含 Zero/banked 项 | `CHAOSReg.cc` | 使用纪律 | 已有 maxRegIdx=31 约束 |
| D9 | P1 | G6 PC/committedInst/event 触发未实现 | 全局 | S0-5+后续 | 未实现 |
| D10 | P1 | G7 ASan/UBSan 构建受阻 | SConstruct | deferred 到 CI | socket configure 阻塞 |

---

## 附录 E　openEuler 日志字段与诊断规则映射表

| openEuler 日志字段 | 解析出 | 驱动的 P/N 规则 |
|---|---|---|
| `EC = 0x..` / `FSC = 0x..`（dmesg/journalctl） | 异常类型 | P4、Step 5 加权 |
| `CPU: N`（Oops 头） | 核心号 → 核心浓度 | P1、N1、Step 4 |
| `pc/lr/Call trace` | backtrace → 单应用判定 | N2、N6 |
| `last reboot` / `journalctl --list-boots` | 重启频率 | P3、Step 2 |
| `ipmitool sel elist` / EDAC count | RAS 条目 → 静默性 | P5、N3、Step 3 |
| `ESR 0x96000044` 重复 WARN | spurious 翻译故障（core179 指纹） | 反哺规则库 |

---

## 附录 F　术语表

| 术语 | 定义 |
|---|---|
| SDC / DUE | 静默数据损坏 / 检出不可纠正错误 |
| AVF | Architectural Vulnerability Factor |
| F1–F6 / PCE | 故障模型谱系（单比特/局部多位/间歇突发/stuck-at/合法域替换/相位延迟/后校验逃逸） |
| E1–E4 / G0–G7 | 证据等级 / 注入器质量闸门 |
| RAT / PRF / ROB / IQ / LSQ/LSU / FSU / AGU | 重命名表 / 物理寄存器堆 / 重排序缓冲 / 发射队列 / 访存队列单元 / 浮点单元 / 地址生成单元 |
| BTB / RAS(返回栈) | 分支目标缓冲 / 返回地址栈 |
| HCCS / HHA / CHI | 华为跨 Die 一致性 / Hybrid HA 目录 / ARM Coherent Hub Interface |
| SECDED / SED / poison | 单纠双检 / 仅检错 / 毒化标记 |
| protectionModel | 注入器代理保护参数（none/sed/secded/secded_poison/parity_interleaved） |
| campaign / cell / manifest / golden | 网格实验 / 参数组合点 / 参数冻结文件 / 无注入校验和基准 |
| read-trace / 历史残留 | PRF 读传播追踪 / method1"读回值=其它活变量"签名 |
| Wilson CI / pairedSector | 比例置信区间 / L3 128B 故障域代理 |
| method1/2/3 | 现场案例编号（Cholesky/x10 指针/LSU 转发相位） |
| D1/D2/D3 | core179 三微架构通路（数据通路/地址通路/PTW 读出通路） |

---

## 附录 G　AI 开发任务卡与待实现注入器 SimObject 骨架

> 本附录把第 5 章各单元 B 段引用的"骨架"与"任务卡"落成可被 AI 直接执行的形态，兑现 0.2 的"可落地"约束。**侧分支已有实现（CHAOSAddrPath/CHAOSPTW）的任务卡应优先 cherry-pick 侧分支代码而非从零写**——既省工作量，又能复用已验证逻辑。

### G.1 任务卡模板与 AGENT_TASKS.md 行格式

每个开发单元用一张 YAML 任务卡驱动，`assert` 为机器可判验收断言，全过才算完成。仓库内 `AGENT_TASKS.md` 用单行登记依赖与状态，编排器按拓扑顺序分发（S0-00 复验卡完成前，后续卡不得开工）。

```yaml
# 任务卡模板（示例：S1-2 CHAOSRenameMap）
id: "S1-2-CHAOSRenameMap"
title: "新写 RAT 注入器 CHAOSRenameMap"
context:
  unit: "RAT + freelist（P0）"
  hook: "cpu/o3/rename_map.hh: SimpleRenameMap::rename()/lookup()/setEntry()"
  host_accessor: "cpu->frontRenameMap()（cpu.hh:478-489）"
  branch: "fi-wangxu"
  evidence_level: "E2"          # O3 flat 表 ≠ V110 RAT，绝对值 E3
action:
  - "按 G.2 骨架写 CHAOSRenameMap.py / .hh / .cc / SConscript"
  - "模式 map_bitflip / f5_substitute / f4_field_stuck；自挂载"
  - "derive configs/se/kp920_proxy.py 增 --chaos_rename 开关"
  - "f5_substitute 仅指向'当前已分配 physReg'（合法域校验，防 SimulatorError）"
assert:
  - "make sync_chaos 后构建零新增警告（G7）"
  - "probability=0 时 golden 哈希与无注入基线逐位一致（锚点回归）"
  - "同 seed 20 次重放 fault_injections.log 完全一致（G0 可重放）"
  - "f5_substitute ≥1000 次注入 SimulatorError=0"
  - "pilot 每 cell n=100 产生 ≥1 个非 Inactive 结局"
```

**AGENT_TASKS.md 单行格式**：`<id> | depends=[<id>,…] | owner | status | assert_hint`

```
S0-00-复验卡          | depends=[]          | agent | done    | 附录 A"已有"7项逐项复验通过（本轮已完成）
S0-01-干净重建        | depends=[]          | agent | done    | 源码-二进制一致，vecLaneWidth 可用（本轮已完成）
S0-02-campaign+manifestv2 | depends=[]      | agent | done    | campaign.py v1 f8aecc7 + manifest v2 schema 105bc0f；runner/campaign v2 字段解析待续
S0-03-protectionModel | depends=[S0-02]     | agent | done(v1)| classify 九类 + CHAOSCache protectionModel 参数面 a6c5b9c；.cc ECC 后处理待续
S0-04-已知缺陷修复    | depends=[S0-01]     | agent | done    | D1/D2/D3/D4/D5/D6 已修（0ae28fe/56023c3/58be899/4ed645b）；D7 部分已有；D9/D10 deferred
S1-01-CHAOSPhysReg扩展| depends=[S0-04]     | agent | done    | F3 triggerValue* + semanticRole（7f538c4，已验证 MISS 1.3e8 跳过）
S1-02-CHAOSRenameMap  | depends=[S0-04]     | agent | done    | 已实现 c5c8c96（f5_substitute+map_bitflip+f4_field_stuck，三模式验证+合法域校验）
S1-03-CHAOSFreeList   | depends=[S0-04]     | agent | done    | 已实现 379e11c（mark_free/pop_wrong+扫RAT+合法域，验证 PhysReg[170] donor）
S1-04-CHAOSROB        | depends=[S0-04]     | agent | done    | 已实现 7d0756d（entry_bitflip+exc_suppress 验证；spec_leak deferred；fault kernel 待续）
S1-05-CHAOSLSQFwd扩展 | depends=[S0-04]    | agent | done(部分)| D2 ✅ + structuralFault ✅ 8320daf（rol1/空槽验证）；stale_line_replay/fwd_source_sub/phaseOffset 待续
S1-05b-CHAOSAddrPath  | depends=[S0-04]     | agent | done    | 已实现 ffd041e（侧分支移植+主线纪律；FS O3 端到端待 checkpoint）
S2-05a-CHAOSArmSysReg扩展| depends=[S1-02]  | agent | pending | value_to_legal(F5) + D4 时间窗
S2-05c-CHAOSPTW       | depends=[S1-05b]   | agent | done    | 已实现 de48432（FS clearValidBit 验证制造 spurious；H7 formal 待续）
```

### G.2 待实现 P0/关键注入器 SimObject 骨架（Python 参数面）

> 以下为参数面骨架（示意）。`cxx_header`/C++ hook 位置以当前 vendored gem5 版本为准；C++ 侧要点在各骨架后注明，非最终代码。闸门参数（`firstClock/lastClock/maxFaults/rngSeed/writeLog`）遵循既有注入器统一约定。**注意 rng 初始化顺序 bug**（侧分支已修：用立即调用 lambda 构造 `std::random_device`，不依赖成员顺序，否则 `rngSeed=0` 必崩——见 FI_DESIGN_SUPPLEMENT patch bc4feb4）。

**① CHAOSRenameMap（RAT，S1-2）** — 复现 method1"映射张冠李戴"核心假设。

```python
from m5.params import *
from m5.SimObject import SimObject

class CHAOSRenameMap(SimObject):
    type = "CHAOSRenameMap"
    cxx_class = "gem5::CHAOSRenameMap"
    cxx_header = "cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh"

    cpu = Param.BaseCPU(NULL, "Target O3CPU")
    probability = Param.Float(0.0, "Per rename-map write probability of corruption")
    mode = Param.String("map_bitflip",
        "map_bitflip: 翻转 map 表项 physRegIdx 的某一位 | "
        "f5_substitute: 令 archReg K 指向另一'当前已分配'physReg | "
        "f4_field_stuck: 把某表项永久钉到错误 physReg")
    targetArchReg = Param.Int(-1, "目标架构寄存器 (-1 = 随机)")
    faultMask = Param.UInt64(0, "map_bitflip 位掩码 (0 = 随机一位)")
    firstClock = Param.UInt64(0, "最早可注入周期")
    lastClock = Param.UInt64(0, "最晚周期 (0 = 不限)")
    maxFaults = Param.UInt64(0, "最大注入次数 (0 = 不限)")
    rngSeed = Param.UInt64(0, "RNG 种子 (0 = random_device)")
    writeLog = Param.Bool(True, "写 fault_injections.log")
```

> 实现要点：hook `SimpleRenameMap::rename()`（架构寄存器 → physReg 写入点）；`f5_substitute` 只从 `freeList` 的"已分配"集合选目标，做合法性校验；写 `dest_phys` 语义随表项参与后续 `regfile` 读，故天然携带 read-trace（与 §5.1 共用四分类）。

**② CHAOSFreeList（freelist，S1-3）** — 复现 method1"活寄存器被误标空闲/历史残留"。

```python
class CHAOSFreeList(SimObject):
    type = "CHAOSFreeList"
    cxx_class = "gem5::CHAOSFreeList"
    cxx_header = "cpu/o3/CHAOSFreeList/CHAOSFreeList.hh"

    cpu = Param.BaseCPU(NULL, "Target O3CPU")
    probability = Param.Float(0.0, "Per alloc/free event probability")
    mode = Param.String("mark_free",
        "mark_free: 把仍在架构映射中的活 physReg 误标为空闲 | "
        "pop_wrong: 重命名分配时发一个'已活'physReg（双占用）")
    targetPhysReg = Param.Int(-1, "目标 physReg (-1 = 随机)")
    firstClock = Param.UInt64(0, "最早可注入周期")
    lastClock = Param.UInt64(0, "最晚周期 (0 = 不限)")
    maxFaults = Param.UInt64(0, "最大注入次数 (0 = 不限)")
    rngSeed = Param.UInt64(0, "RNG 种子 (0 = random_device)")
    writeLog = Param.Bool(True, "写 fault_injections.log")
```

> 实现要点：hook `PhysRegFile` 释放链路的 `addReg()`（freelist 回填）与分配 `getReg()`；`mark_free` 后旧占有者在被覆写前读回旧值 → 历史残留签名；`pop_wrong` 双占用需在写回时打 `dynamic_context.freelist_size`。

**③ CHAOSROB（ROB，S1-4）** — 复现 method1"投机流状态泄漏 + 异常位静默"。

```python
class CHAOSROB(SimObject):
    type = "CHAOSROB"
    cxx_class = "gem5::CHAOSROB"
    cxx_header = "cpu/o3/CHAOSROB/CHAOSROB.hh"

    cpu = Param.BaseCPU(NULL, "Target O3CPU")
    probability = Param.Float(0.0, "Per-injection probability")
    mode = Param.String("entry_bitflip",
        "entry_bitflip: 翻转某 ROB 条目字段 | "
        "exc_suppress: 清异常位→DUE 转 SDC | "
        "spec_leak: squash 时保留错误路径 μop 的 PRF 写")
    field = Param.String("result", "result | done | exc_status | dest_phys | spec")
    distanceFromHead = Param.Int(0, "距 ROB 头的距离 (0 = 头)")
    faultMask = Param.UInt64(0, "entry_bitflip 位掩码 (0 = 随机一位)")
    firstClock = Param.UInt64(0, "最早可注入周期")
    lastClock = Param.UInt64(0, "最晚周期 (0 = 不限)")
    maxFaults = Param.UInt64(0, "最大注入次数 (0 = 不限)")
    rngSeed = Param.UInt64(0, "RNG 种子 (0 = random_device)")
    writeLog = Param.Bool(True, "写 fault_injections.log")
```

> 实现要点：hook `retireHead()`/`squash()`/`doSquash()`（`rob.cc`）与 `commitHead()`（`commit.cc`）；`exc_suppress` 记录 `P(DUE→SDC 转化率)`；`spec_leak` 与 §5.9 CHAOSBPU 联合观测，验证投机泄漏是否同一签名。

**④ CHAOSAddrPath（AGU 地址通路，S1-5b，侧分支已有，cherry-pick）** — 复现 core179 D2 byte7 清零签名。

```python
class CHAOSAddrPath(SimObject):
    type = "CHAOSAddrPath"
    cxx_class = "gem5::CHAOSAddrAddrPath"
    cxx_header = "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"

    cpu = Param.BaseCPU(NULL, "Target O3CPU (mmu reachable)")
    probability = Param.Float(0.0, "Per load-addr-gen probability")
    mode = Param.String("byte7_clear",
        "byte7_clear: byte7 清零 (复现 core179 D2 非规范地址) | "
        "low_bit_flip | f5_sub_addr: 换成另一合法基址")
    targetByte = Param.Int(7, "被破坏的地址字节 (0-7)")
    faultMask = Param.UInt64(0, "位掩码 (0 = 随机一位)")
    firstClock = Param.UInt64(0, "最早可注入周期")
    lastClock = Param.UInt64(0, "最晚周期 (0 = 不限)")
    maxFaults = Param.UInt64(0, "最大注入次数 (0 = 不限)")
    rngSeed = Param.UInt64(0, "RNG 种子 (0 = random_device)")
    writeLog = Param.Bool(True, "写 fault_injections.log")
```

> 实现要点：hook `lsq.cc` 的 `translateTiming` 前（`req->setVaddr(va)` 破坏 vaddr）；**FS 模式必需**（SE 下 byte7 清零后地址仍落物理内存不 fault，mmu.cc:1213 静态归因）；侧分支已实证 FS 下复现 `0xffffffc008b08f30→0xffffc008b08f30` 签名。**优先 cherry-pick `origin/fi-h6-h7-fs-verify`**。

**⑤ CHAOSPTW（页表走查器，S2-5c，侧分支已有，cherry-pick）** — 复现 core179 D3 spurious 翻译故障。

```python
class CHAOSPTW(SimObject):
    type = "CHAOSPTW"
    cxx_class = "gem5::CHAOSPTW"
    cxx_header = "arch/arm/CHAOSPTW/CHAOSPTW.hh"

    tlb = Param.ArmTLB(NULL, "Target ArmTLB (walker reachable)")
    probability = Param.Float(0.0, "Per descriptor-read probability")
    mode = Param.String("bit_flip",
        "bit_flip | clear_valid_bit (2-bit 清零, 绕 ECC 制造 spurious) | f5_sub_desc")
    ptwEcc = Param.Bool(False, "model PTW array ECC (H7 自变量)")
    targetByte = Param.Int(0, "被破坏的描述符字节")
    faultMask = Param.UInt64(0, "位掩码 (0 = 随机一位)")
    firstClock = Param.UInt64(0, "最早可注入周期")
    lastClock = Param.UInt64(0, "最晚周期 (0 = 不限)")
    maxFaults = Param.UInt64(0, "最大注入次数 (0 = 不限)")
    rngSeed = Param.UInt64(0, "RNG 种子 (0 = random_device)")
    writeLog = Param.Bool(True, "写 fault_injections.log")
```

> 实现要点：hook `arch/arm/table_walker.cc doLongDescriptor`（`corruptDescriptor`）；**FS 模式必需**（SE 用 `translateMmuOff`→`setPaddr(vaddr)`，从不调用 walker，numFaultsInjected=0）；侧分支已实证：单 bit XOR 下 ECC-on 纠正（40→0 注入）、clearValidBit 制造 spurious（40→40），**完整 ECC on/off spurious 率定量需结合两者（P3c 条件注入模式，待 formal）**。**优先 cherry-pick 侧分支**。

---

> **文档结束**。本文以 `fi-wangxu` 工作树源码为唯一事实源，修正了原方案文档 8 处失实声明（§0.4），以四维度（注入研究/规律研究/诊断建议/抗 SDC 设计）+ 实验开发验证为骨架。执行从第 10 章 Task S0-2（campaign.py + manifest v2）开始，S1 P0 单元为最高 ROI。诚信边界：所有现场数据来自单一故障机（未第二台健康机复现，标"单机未确认"）；H5/H6/H7 在侧分支验证、主线需补齐注入器后复现；所有 P_SDC 是 gem5 O3 代理条件概率、非产品 FIT。
