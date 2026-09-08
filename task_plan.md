# 下一步计划：鲲鹏920 SDC 故障注入 — S2/S3 收尾 → 网格深化 → F5/F6 → FS → v1.1 补救轮

> 依据 `docs/KUNPENG920-故障注入方案详细工程设计.md`（§3.1 阶段表）× 仓库实际进展（HEAD af64ef7 + 未提交 formal 结果）编写。
> **v1.1 补救轮（Phase 8–12）** 依据工程设计文档 v1.1（§1.3 故障模型必跑矩阵 + §1.7 负载/oracle 纪律 + §2.3/2.6/2.8/2.17）× `KUNPENG920-v1.1补救轮执行计划.md`；落地仓库 `gem5-fi/`（分支 `fix/fi-tool-correctness`，真 HEAD `4bf8d0d` = 238 commits）。
> 本计划是**工作计划**；证据审计结论见 `findings.md`。

## Goal

把"每个单元 1 个 cell 的 n=384 formal"推进为设计文档要求的**有意义网格 + protection-aware 对照 + F5/F6 机理模式 + FS 管线**，期间修复已发现的工具正确性 bug（本分支主题），最终产出可信的 §4.1 逃逸分解与 §4.2 保护投资排序。

## 现状一句话总结（详见 findings.md）

S1 四个 P0 单元 + S2/S3 六个 SE 单元 formal 已完成（单 cell × n=384）；核心格局：**乱序后端（PRF/RAT/LSQFwd）DUE 主导 92–100%，存储（L1D）SDC 主导 97.7%，执行/IQ/译码/BPU/RAS 全 Masked**。但存在：① mem_formal 全 Inactive（CHAOSMem 频率 bug，同 8bff9d1 修过的那类）；② 6 个 formal 结果未提交；③ 几乎所有 formal 只跑了 `protection_model=none` 单组、单 fault_model、target_index=0 单 cell —— 与设计文档 §1.2/§2.x C 的网格规格相差甚远；④ F5/F6 子模式（ROB spec_leak、IQ src_ready/tag_sub、LSQFwd fwd_source_sub/phaseOffset、TLB pfn→活页）全部 deferred；⑤ FS 管线（kp920_proxy_fs V110 参数、checkpoint 流水线、PTW H7 formal）未落地。

---

## Phase 1 — 工具正确性 + 在手结果落盘（本分支主题，最高优先）

**Status: complete（2026-09-03）**

1. ✅ 6 个 formal 提交（d4c9e8b）：bpu/decode/ras/iq 全 Masked 384/384；mem 标注无效。
2. ✅ CHAOSMem 频率 bug 修复（b7433dd）：ratio 由时钟频率按 gem5 舍入规则计算（C2→385，C0→500）。真机验证 Tick 精确等于 first_clock×ratio。
3. ✅ mem_formal 重跑（d88dcc7）：**VALID，384/384 Masked，P_SDC=0% [0,1.0]**——DRAM 后备字节被 L1/L2 缓存掩盖（与 L1D 97.7% SDC 对照鲜明）。附带修复 campaign.py --jobs>1 pickle bug（_PoolRep 模块级类；此前所有 formal 都是串行跑的，掩盖了此 bug）。

**验收**：✅ mem formal n_valid=384>0；✅ reg_chain golden f247ef3fe6f02cfd 回归通过。

## Phase 2 — protection-aware 第二组（§1.2 核心缺口，改结论级别的补强）

**Status: complete（2026-09-03）**

1. ✅ **protection_model 全链路打通**（19d8a4b）：campaign→manifest→runner→config（l1d/cache + memory 路由），pilot 实证 ladder 生效。
2. ✅ **L1D secded_poison formal**（19d8a4b）：384/384 Masked，P_SDC=0% [0,1]——与 raw 97.7% 形成风险反转（对 F1 单 bit）。
3. ✅ **l1dfwd post-check escape formal**（7387649 采样修复 + 7d40912 重跑）：**P_SDC=90.9% [87.6,93.4]**——§2.7 H.③ 验证通过。
4. ⏸ mem+secded 对照（Phase 2.3）：deferred——DRAM 后备字节全 Masked（上游缓存掩盖），protection 对照暂不改变结论，排 Phase 3 网格深化后再评估。

**L1D 三层定论（§4.1 逃逸分解 L1D 部分完成）**：raw 97.7% / +SECDED 0% / post-check 90.9%。
**附带发现**：CHAOSL1DForward 单故障采样偏差 bug（第一 eligible 恒为同一 squashed load）——所有 hook-on-event 注入器需逐一审计（Phase 3 首项）。

设计文档 §1.2 明确"每个 cell 跑两组"，目前 L1D 唯一高 SDC 单元（97.7%）只跑了 `none`。没有 protection 对照，§4.1 的逃逸分解与 §4.2 排序就没有"风险反转"维度。

1. **L1D secded_poison 组 formal**：`§2.7` 加 protection_model=secded_poison 的 campaign（1-bit→Corrected / 2-bit→poison / ≥3-bit→静默），与 none 组对照 → 风险反转图。CHAOSCache protectionModel 已实现（b9f2435）。
2. **L1DForward（post-check escape）formal**：注入器已存在（`CHAOSL1DForward`，runner 有 `l1d_fwd` 映射），l1d_reduce 上 n=384。验收断言 §2.7 H.③：post-check `P_SDC` ≥ raw。
3. **mem formal（Phase 1 修复后）加 secded 组**（DRAM 华为 ECC 代理）。
4. 更新 `tools/ras_escape_analysis.py` 的逃逸归因：区分 raw-escape vs protection-failure。

**验收**：L1D 三组（none / secded_poison / post-check）齐；escape_decomposition.md 更新后 B/C/D 机理不再混在 "?"。

## Phase 3 — 网格深化：单 cell → 最小有意义网格（§2.1/2.2 C 规格）

**Status: complete（2026-09-06，SE 侧 15/15 单元 formal 全齐）**

当前 formal 几乎全是 `target_index=0` + `transient_bit_flip` 单 cell。按设计文档，最优先的三根轴：

1. ✅ **PRF 位段 × ABI 角色网格**（45b2b85 + 1210fa6 + 57a75ac）：X3 位段边界 bit1/bit2 精确定位（无过渡带）；三种寄存器画像（索引/计数类 X2/X3/X5 低位 SDC 窗+高位 DUE、指针类高位 DUE、路径外全 Masked）；3.9% random-bit SDC ≈ 2/64 定量互洽。**剩余子项**：F4 stuck / F3 数据相关模式、第二 workload 交叉验证（reg_chain）。
2. ✅ **PRF 窗口扫描（H2）**（b11d751 + 77e752d + 工具 7ccc801）：ROB {96,128,160} × PhysInt {128,160,192}——**ROB=160 整行掩蔽、PhysInt 零效应、trigger 无关（假说证伪）**；X3 bit0 SDC 对 ROB 深度呈阈值响应（≤128→100%，160→0%），机理 open。
3. ✅ **RAT（§2.2）f5_substitute formal**（99750c9）+ **FreeList mark_free formal**（6ff09bd）：§2.2 rename 子系统三注入点全部落定（map_bitflip 95.8% / f5_substitute 59.7%+40% 自愈 / mark_free 72-77% 目标无关），全 DUE 主导 0% SDC——"历史残留→SDC"三点全否。**ROB/IQ 修正重跑完成**（7025ca9）：ROB 确认全 Masked；IQ 大反转为 Hang 75.3%（旧结论双重伪影）。
4. ✅ **多 workload 对照完成**（2026-09-08，524dc60）：ExMon 100% DUE 单元级 ✅；exec/bpu 在 reg_chain 上 formal 384/384 全 Masked（<1% 上界达标——验收规则满足）；RAS/Decode pilot 方向一致；FPU gemm formal 已确认。**Phase 3.4 收口**。

**验收**：每单元 ≥2 轴 × ≥3 level 或有书面理由跳过；全 Masked 单元在第二 workload 上置信上界仍 <1% 才写进结论。

## Phase 4 — F5/F6 机理子模式（对齐三现场案例的核心缺口）

**Status: complete（2026-09-04，6/6 模式；4.4/4.5 的 FS formal 排 Phase 5）**

3. ✅ **IQ src_ready_bitflip / wake_phase**（9db60d6 + 4aee770 + 9991185）：**三模式图谱全 0% SDC**（wake_omit Hang 75.3% / src_ready_bitflip 100% DUE / wake_phase 100% DUE 平顶）；结局由依赖密度决定（madd_chain 100% vs cholesky ~5%）；**wake_phase 代理不捕获 method3 相位签名**（E3 边界：method3 相位在 LSU 转发时序，不在调度唤醒相位）。
2. ✅ **LSQFwd fwd_source_sub**（05db0e2 + 10a811f）：**P_SDC=37.6% [32.8,42.6] vs byte_flip 4.7%——故障形态 > 故障位置（8 倍 SDC）**，0% Masked；错源=合法域内整字错误。phaseOffset（相位敏感性曲线）仍 deferred。
1. ✅ **ROB spec_leak**（1ca0346 + ccb6eda + 9e549af）：机理落地在 Rename::doSquash 回滚抑制（CHAOSROB.cc:140 的 deferred 注释指向的 squash 路径）。pilot + formal（branchy X3/X9 n=384 each）：**单次回滚抑制全 Masked——泄漏值被正确路径重写覆盖**（X3/X9 短命循环变量无消费者）。下一 cell：X19 callee-saved 长活类（method1 原始目标），跑批中。rename 子系统四注入点全 0% SDC。

| 优先 | 模式 | 位置 | 对照案例 |
|---|---|---|---|
| 1 | **ROB spec_leak**（squash 不回滚错误路径写） | `CHAOSROB.cc:140` deferred 注释处 | method1 投机泄漏 |
| 2 | ✅ **LSQFwd fwd_source_sub + phaseOffset**（05db0e2 + cb31fef + 0c9fa1e） | method1 错源 37.6% SDC / method3 相位平顶 100% DUE（无容忍带） |
| 3 | **IQ src_ready_bitflip / tag_sub** | `CHAOSIQ.py:19` deferred | method3 错源唤醒 |
| 4 | **ArmTLB pfn_to_mapped_page + targetField {ap,xn,attridx,ng,asid}** | `CHAOSArmTLB.py` param surface | method2 静默 SDC 通路 |
| 5 | **SysReg value_to_legal（F5）** | `CHAOSArmSysReg` | §2.10 |
| 6 | **CHAOSMem addr_map_sub**（E3，最后） | `CHAOSMem.py:42` deferred | §2.17 |

每个模式：pilot n=5（触发 + 合法域 0 SimulatorError）→ formal n=384。method3 相位敏感性曲线（phaseOffset ∈ {−2..+2} × P_SDC）是本阶段招牌产物。

## Phase 5 — FS 管线（§2.10/§2.4 AGU/§3.2 checkpoint 流水线）

**Status: in_progress（2026-09-05，工具链 4/5 就绪）**

1. ✅ **kp920_proxy_fs V110 参数落地**（291a431）：_pre_instantiate 链式 patch 应用 V110 O3 参数（与 SE 版同源）；非 O3 boot pass 诚实跳过。
2. ✅ **checkpoint 流水线端到端验证**（291a431 + 85ee4bf）：boot_ckpt.rcS → **cpt.237933688473** → restore（+1332 ticks 注入窗口语义正确）→ TLB F5 活页注入触发。wall-time 瓶颈解除（一次 boot ~30min + 每 rep ~4min）。root=/dev/vda1（virtio_blk）。
3. ✅ **CHAOSPTW 挂载**（1bd05b3）：--chaos_ptw + H7 ptw_ecc 旋钮；runner ptw→C0-FS 路由。H7 pilot yaml 就绪。
4. ✅ **FS campaign 化**（b802606）：campaign `fs:` 块 → runner FS 分支 → classify fs_mode（内核存活 oracle）全链闭环；TLB F5 pilot 2/2 Masked（28s/rep restore 快速路径）。修复 3 个 pilot 暴露的工具 bug（fault 统计清单缺 armtlb/sysreg、FS 无 checksum 的分类伪影、replay 超时配置）。
5. ✅ **TLB F5 活页 formal**（9285a15）：第一个 FS formal（n=384 checkpoint restore，3.5h vs 旧模式 8 天）——384/384 Masked（0% Crash，活页替换绕过崩溃检测=静默通路存在性证明；SDC/Masked 在 fs_mode oracle 下不可区分，量化需内核校验 workload）。✅ **PTW H7 pilot**（43819cd）：12/12 触发全 Masked——触发链验证 ✅，但 H7 双臂对照需 **boot 期注入**（原始预期来自 boot walk 密度；稳态 walk 稀疏无消费者）。✅ **SysReg F5 pilot**（ba27677）：value_to_legal 重入递归 SIGSEGV 修复；10/10 触发全 Masked；runner 补 sysreg 白名单。
✅ **method2 三根因三臂全通**（5c09457）：O3 checkpoint restore 验证（631M ticks 零 panic）；PRF 臂（X10 触发 + 构造期 schedule 断言 bug 修复——rebase 现覆盖 phys）/ AddrPath 臂（byte7_zero：canonical→非规范内核地址签名）/ TLB 臂（活页替换）全部真机触发。**三臂对照 campaign 就绪**——需内核活跃消费 x10 的 workload 才有签名可比（稳态全被吸收）。**SE 侧 PRF 臂定论（2026-09-07，844827f）：不可达——forwarding 掩蔽定律**（chase 紧循环的消费即生产数据流使 PRF 位翻转架构不可见；ptr_chase_long 三种注入方式 n=100 一致全 Masked；方法学坑：userspace 寄存器分配须反汇编定位/每指令重写寄存器用 phys 随机）。**PRF 臂对照须 FS 内核态**（m2_ptrchase.rcS 调度域遍历）。**✅ 三臂 pilot 完成（2026-09-07，9330cf0）：method2 签名指向 AGU 地址路径**——AGU 臂 3/3 Kernel Oops（kfree NULL deref，调度器任务释放路径=现场家族）；PRF/TLB 臂被吸收。附带修复 phys active-only 采样 + gem5 上游 exit_event 翻译 bug（Oops 可分类）。**✅ AGU 臂 formal（2026-09-08）：P_DUE=100.0% [99.0,100.0] 零 SDC——三根因定量闭环**（AGU 100% DUE / PRF 存活 / TLB 静默，三臂结局互异）。**✅ H7 boot 期 pilot（方向性）**：ECC-on 2/2 boot 完成 vs off 2/2 挂起——与原预期一致；formal 需健康机（boot 继续在 cpu179 上超时）。**✅ PRF/TLB 臂 formal（2026-09-08，10de4e9）：三根因定量闭环**——PRF 6.5% DUE（吸收为主）/ TLB 100% DUE（**活跃度依赖定律**：稳态 0% Crash vs 内核活跃 100% 致命完全反转）。method2 实验（§2.10 C）全部完成。剩余：H7 formal（健康机）。

1. `configs/fs/kp920_proxy_fs.py` 现在是 TODO stub（只 print + delegate）——落 V110 参数（`_pre_instantiate` 同 SE 版）。
2. **Atomic→`m5 checkpoint`→O3 restore 流水线**（§3.2）：boot.rcS 已有思路；解决 FS formal 不可重复跑的 wall-time 问题（fb34343 的 4/5 超时根因）。
3. **CHAOSPTW cherry-pick + H7 formal**（分支数据：ECC-on spurious≈0 / off >0，5-seed）→ formal n 扩大。
4. **TLB F5 活页 cell**（依赖 Phase 4.4）：`p_SDC(pfn→活页)` —— 文档标注"最危险路径的量化"。
5. method2 三根因区分实验（§2.10 C 最后一行：PRF vs AddrPath vs TLB 同签名注入）。

## Phase 6 — S5 元分析强化 + 健康机复现（贯穿）

**Status: in_progress（2026-09-06，6.1/6.2/6.4 完成）**

1. `tools/ras_escape_analysis.py` 实现 weight(unit)（gem5 stats occupancy 采集）——目前 priority 表混合 pilot/formal 数据且无权重。
2. 修正 escape_decomposition.md 的 "? (unit not in map)" 行（fpu/lsqfwd 等映射缺失）。
3. **所有 formal 关键 cell 在第二台健康机复现**（S6，cpu179 是故障机 —— 每份 summary.md 的 Honesty note 都在提醒这件事）。复现清单：L1D 97.7%、PRF X3 3.9/92.7、RAT 95.8、LSQFwd 100% DUE。
4. 最终报告骨架：§4.2 三类交付物（DFT 向量、保护排序、位谱指纹库）+ §4.3 诚实边界。

## Phase 7 — S4 系统级（独立子项目，可后置）

CHAOSCHI/CHAOSNoC pilot 已能触发（7c854bb/7582e8c，未提交的 ruby test configs 在工作区）；HCCS/CHI/Garnet formal 排期在设计文档里本就是 S4 独立子项目，等 Phase 2-5 出结果后再决定投入。

---

# ═══ v1.1 补救轮（Phase 8–12）——首轮 formal 伪影修正 ═══

> **背景**：首轮 formal（每单元 1 cell × n=384）的结构性格局里，**FPU / 整数执行 Exec / L2 / DRAM 全 0% SDC + ROB spec_leak 阴性**——这四处与现场 method1/method3 + 文献直接冲突。根因排查确认是**故障模型 + 负载错配**（伪影），不是单元性质：
> | 单元 | 首轮结论 | 存疑原因 |
> |---|---|---|
> | FPU | 0% SDC | 与 method3（第 179 核现场失效就是 FP 尾数 SDC，85–93% 尾数）+ Veritas 冲突。均匀翻结果一位 + gemm/neon_lane 归约 kernel；`svd_iterative` kernel 已有但从未用于 FPU。 |
> | ROB spec_leak | 阴性 | 实验失败：X3 泄漏值被正确路径覆盖；X19 384/384 Inactive（回滚流里没有它）。这是 method1 核心假设。 |
> | L2 / DRAM | 0% SDC | 负载伪影：cholesky/l1d_reduce 工作集在 L1，被注入的 L2/DRAM 字节从不回读。§2.8/§2.17 要求的大工作集 kernel + 定向注入未执行。 |
>
> 能激发这些 SDC 的故障模型（F3 数据相关、F4 `recurring` 反复损坏、`fma_intermediate` 数据通路、合法域替换）**本就在工程设计文档里**，只是没执行。文档已升级 v1.1。**本轮 = 执行 v1.1 的补充，产出 FPU / ROB spec_leak / L2 / DRAM 的可信修正数。** 预期两种产出都有价值：更强模型下出现非零 SDC（修正结构性结论），或**仍然** 0%（此时"该单元对 SDC 钝"才站得住，而非负载伪影）。
>
> **⚠ 执行环境**：build（`scons -C CHAOS/gem5 build/ARM/gem5.opt -j16`）+ campaign 跑批只能在 **Linux 服务器**（openEuler，192 核 HIP08，含 cpu179）。本 Windows 机器仅用于**写代码 + 提交 + push**；每补丁 build/run 自验证在 Linux 上完成，遵 `gem5-fi/CLAUDE.md` 纪律。
> **机器策略**（cpu179 是唯一坏核，同机 ~190 健康核）：`numactl --cpunodebind=0 --membind=0`（集 A，NUMA 0 / socket 0，主跑）/ `--cpunodebind=1 --membind=1`（集 B，NUMA 1 / socket 1，复现）——都远离 cpu179（socket 3 / NUMA 7）。**"复现" = 关键 cell 在集 B 重跑，结局分类一致 + P_SDC 点估落入集 A 的 95% CI**（取代原"需第二台健康机"阻塞项）。残余风险（写进诚实边界）：若 cpu179 缺陷污染 socket 间共享 L3 / 内存控制器 / 一致性目录，A/B 均可能受影响。
> **深度策略**：每新 kernel / 模式先 **n=100 pilot**（看 Reachability + 量级 + 有无非零 SDC）→ 只对"有信号"或 method1/2/3 直接对照的 cell 扩 **formal n=384**（+ 5% 重放 + Wilson CI）。cpu179 wall-time：cholesky ~2s/run（formal 可行），reg_chain ~90s/run（pilot 即可）。

## Phase 8 — v1.1/P0：基础设施（解锁 Phase 9–11，先做）

**Status: complete（2026-09-07，0a–0d 四补丁：89832f6 / 1d2abce / 878db03 / c6d09e6）**

1. ✅ **非 hash oracle**（89832f6）：classify oracle_kind(array_hash/per_element_diff/fp_ulp) + GOLDEN_ARRAYS + campaign/schema 全链。真机验收：ELEMDIFF n=1 first=3425 maxulp=1.8e16;fp_ulp tol 两侧判 Masked/SDC;array_hash 无注入==golden;exact_hash 路径不变。
2. ✅ **events_to_skip 均匀采样**（1d2abce）：chaos_event_sample.hh + countOnly(CHAOS_ELIGIBLE_COUNT) + 五注入器 + campaign dry-run。真机验收：cholesky N_eligible=32,5-seed 注入 sn=13051/13142/74271/90962/96782 均匀分散;legacy geometric byte-identical。
3. ✅ **local_mbu 相邻多位档**（878db03）：generateRandomMask 相邻 n-bit 连发。真机验收：Cache/Mem 双侧 bits=1/2/3 → Corrected/Latent/SilentEscape。附带修出 arm_chaos.py 两个潜伏 bug（addr_map_sub 缺 argparse;CHAOSMem 漏传 bitsToChange——C0 上 --bits_to_change 被静默忽略）。
4. ✅ **recurring 契约松绑**（c6d09e6）：runner 配对强制（该模型要求 max_faults==0）+ campaign 自动发 0 + schema 放开。真机验收：n=3 recurring cell 3/3 跑通、per-rep N=26-29 损坏、九类结局;负例配对错配/validator 拒绝。

**Phase 8 整体验收**：✅ 0a–0d 全过;✅ reg_chain golden f247ef3fe6f02cfd 回归（每补丁各验一次）。

**Phase 8 附带发现（写进 findings，Phase 9 必须处理）**：CHAOSFPU/CHAOSExec 的 corruptFrontResult* 腐蚀 instResult 队列（唯一消费者 checker=Null）——FP/SIMD 结果走 getWritableRegOperand 直达 PRF、整数走 setRegOperand→regFile,**注入点架构不可见**;cholesky 上 6637 个 eligible 事件仅 32 个可腐蚀。**Phase 9 patch 1a 必须重写为 PRF-dest 路径**（比 v1.1 计划诊断的"模型+负载错配"更深一层的根因）。

1. **非 hash oracle**（0a + 载体 0f）：`tools/classify.py` `classify_run()` 加 `oracle_kind` 参数——`array_hash`（kernel 打印 `ARRAYHASH=<64hex>`，比对该行）/ `per_element_diff`（打印 `ELEMDIFF n=<count> first=<idx> maxulp=<n>`，`count>0`→SDC，first/maxulp 带进 reason）/ `fp_ulp`（打印 `ULP=<max_ulp_error>`，`>tol`→SDC，`<=tol`→Masked 即使 bit 不精确一致）。`tools/runner.py` manifest `oracle.kind`/`oracle.tol` → `classify_run`；加 `GOLDEN_ARRAYS` 注册表（`golden_id → artifacts/golden/<id>.bin`，与 `GOLDEN_IDS` 并列，`--golden-array` CLI 覆盖）。`tools/campaign.py` `manifest_for_cell()` 写 `workload.oracle_kind`/`oracle_tol`；`schemas/manifest.schema.json` v2 `oracle.kind` enum 增补。**验收**：临时 elemwise 风格烟雾 kernel + 手工注入，`per_element_diff` 报出 first/maxulp，`fp_ulp` 在 tol 两侧分别判 Masked/SDC，`array_hash` 无注入回归 == golden；`reg_chain` exact_hash 路径不变。**补丁 1–2**。
2. **`events_to_skip` 均匀采样**（0b + 载体 0e，§1.7 rule 4）：现状几何分布 p=0.1（均值 10，前置偏斜——长 ROI 下注入点集中在前 ~30 个 eligible 事件）。新写 `CHAOS/gem5/src/cpu/o3/chaos_event_sample.hh`：`pickSkip(seed, nEligible) = rng(seed) % nEligible` + `countOnlyMode`（消费 eligible 事件、打印 `CHAOS_ELIGIBLE_COUNT=<n>`、不损坏）。注入器加 `--count_only` 模式；`campaign.py` 先对每个 (kernel, trigger) dry-run 计数 ROI 内 eligible 数 `N_eligible` → `skip = uniform(0, N_eligible-1)`（seed 派生，可重放）。`CHAOSFPU / CHAOSExec / CHAOSL1DForward / CHAOSLSQFwd / CHAOSIQ / CHAOSROB` 六注入器采样切到 helper（config 传入固定 `events_to_skip`，不再各自几何分布）。**验收**：同一 cell 换 5 seed，注入的动态事件（tick / seqNum）分散（不再恒为同一条）；`reg_chain` golden 回归。**补丁 2–3**。
3. **CHAOSCache / CHAOSMem `local_mbu` 多位档**（0c，为 L2/DRAM 的 ECC 阶梯）：`faultMask=0` 时按 `bitsToChange` 生成**相邻**多位掩码（当前是随机位）；`applyProtection()` 的 2-bit（poison/Latent）与 ≥3-bit（SilentEscape）分支走通（首轮只走了 1-bit Corrected）。**验收**：`protection_model=secded_poison` + `bits_to_change=2` → log `bits=2 -> Latent`；`bits_to_change=3` → `SilentEscape`。**补丁 1**。
4. **`recurring_result_stuck` 单故障契约松绑**（0d，G5）：`recurring_result_stuck` 用 `maxFaults=0`（每次命中都损坏），违反 `runner.py` 的 `faults_injected ∈ {0,1}` 断言。`runner.py` **仅当** `fault.model == recurring_result_stuck` 时允许 `max_faults==0`；`campaign.py` 对该模型 cell 发 `limits.max_faults=0`；`schemas/*` 相应放开；**不要**把 recurring cell 混进单故障 campaign 的 CI（Wilson CI 仍按 rep 算）。**验收**：一个 recurring cell 跑通、日志 N>1 次损坏、产出有效九类结局 + Wilson CI；`transient_bit_flip` cell 仍断言 `∈{0,1}`。**补丁 2**。

**Phase 8 整体验收**：0a–0d 四项验收全过 + `reg_chain` golden `f247ef3fe6f02cfd` 回归（exit 0，零 SIGSEGV）。**机器**：任意健康核。

## Phase 9 — v1.1/P1：FPU（最高优先，直接与 method3 冲突）

**Status: complete（2026-09-08，pilot 轮全过验收门；formal 轮待跑）**

1. ✅ **patch 1a-0 PRF-dest 重写**（bfa9c4f）：instResult 死路径 → PRF-dest（VecRegClass 经 getWritableReg;Float/VecElem 经 getReg/setReg）。真机：4 seeds 2 SDC/2 Masked——FSU 故障首次产生真实结局分布。cholesky 6637 eligible/32 可腐蚀的死路径定量在案。
2. ✅ **六模式**（f5b3bc8/f3e110b/121a07b/9a79376）：bitseg 六段(验收:6 段×3 seeds mask 全在段内)/fma_intermediate E3(20-seed 设计分布 85% 精确命中)/recurring(6628 发 distinct mask=1,SDC)/rounding_sub(1-ULP 独立 SDC 签名)/f3(窗口正反例)/fpsr(诚实占位)。
3. ✅ **elemwise_fma_kernel**（c2da02b）：全数组输出 ARRAYHASH+ULP;golden ced113fd...;array_hash 兜底必要性实证(kernel 本地 ULP 看不见对称损坏)。
4. ✅ **campaign 全链 + pilots**（dedb669）：runner fault.fpu_mode + schema + campaign 轴;5 组 pilot n=100 零 frozen——baseline/六段 bitseg/fma_weighted/recurring 全 ~100% SDC。
5. ✅ **验收门**：fma_intermediate 位谱尾数占比 **80% (24/30) ≥ 70%**——method3 方向复现;recurring ≥ 单发(cholesky 6628 发 vs 2/4);首轮"FPU 0% SDC"作废原因入 findings。
6. ✅ **formal 轮**（fe5c190，审计补跑）：svd_iterative bitseg formal——**mant_hi 92.4% [89.4,94.7] / mant_lo 83.1% [79.0,86.5]**(n=384×2,零 frozen)。method3 尾数谱第二 workload formal 级确认;mant_hi>mant_lo 位段梯度;归约负载 8-17% Mask(元素被覆盖)vs elemwise 平顶。elemwise_fma 平顶(100%)下 SDC/DUE 结构对比无差异——cholesky 级结构对比由 svd 结果承担。

1. **CHAOSFPU 新模式**（1a，`src/cpu/o3/CHAOSFPU/CHAOSFPU.{py,hh,cc}`，5–6 补丁，每模式 1）：
   - `bitseg`：`--fpu_bitseg ∈ {sign, exp_hi, exp_lo, mant_hi, mant_mid, mant_lo}`——只翻该位段内的位（非均匀翻整个结果）。
   - `fma_intermediate`：新增 hook——FSU 对齐后、规格化前的中间结果施加掩码。**gem5 ARM FP 是纯功能模型（`arch/arm/fplib.cc` 的 `fplibMulAdd`），无真实对齐移位/部分积/规格化微结构** → 标 **E3（行为代理，非微结构复现）**。fallback 两选一：(a) 扩展内部精度算 `t=a*b`，对 `t` 按尾数加权的 `bitseg` 掩码，再 `t+c` 舍入；(b) 在**最终结果**上按 method3 匹配的 `mant_lo` 加权分布抽位翻。验收仍是"尾数占比 ≥ 70%"，文档写清是行为代理。
   - `recurring_result_stuck`：`maxFaults=0`——每次命中 `opClass` 过滤的 FSU 结果都施加同一固定掩码（建模乘法器某位部分积卡死；文献指出这才是执行单元 SDC 主导来源）。
   - `rounding_sub`（F5）：换舍入方向。
   - `f3_data_dependent`：复用 `CHAOSPhysReg` 的 `triggerValueMask/Pattern` 模式——仅当操作数落在 `--fpu_operand_range` 时损坏结果。
   - `fpsr_suppress`：清浮点异常标志。
2. **新 kernel `elemwise_fma_kernel.c`**（1b，`workloads/directed/`，1 补丁）：`for i: c[i] = a[i]*b[i] + d[i]`，**输出整个 `c[]` 数组**（不折叠成标量），打印 `ARRAYHASH=` + `ULP=`（对 golden 数组）。`--n` 可调。静态 AArch64，无 libc。
3. **campaign `campaigns/pwf-v11-fpu.yaml`**（1c，C2-KP，`--chaos_fpu`，1 补丁）：轴 = mode {`bitseg`(6 位段), `fma_intermediate`, `recurring_result_stuck`, `rounding_sub`, `fpsr_suppress`, `f3_data_dependent`} × 算子（`opClass` 过滤 FADD/FMUL/FMADD/reduction/shuffle）× 精度 {FP32,FP64} × 注入层 {向量 PRF 存储 `--chaos_phys --phys_reg_class=vector` / FSU 数据通路 `--chaos_fpu`}。kernel = `elemwise_fma`（主）+ `svd_iterative`（method3 SVD 对照，**已存在**）+ `gemm_float`（归约对照，非唯一）。oracle：`elemwise_fma` 用 `fp_ulp`（+ `array_hash` 兜底）；`svd_iterative` 用现有 checksum + `fp_ulp`。**pilot n=100 → formal n=384**：`fma_intermediate`/`bitseg(mant_*)` on `elemwise_fma`+`svd_iterative`，`recurring_result_stuck` on `elemwise_fma`。
4. **验收断言**：
   - `fma_intermediate` 或 `bitseg(mant_*)` 在 `elemwise_fma`/`svd_iterative` 上的**位谱**（`tools/bit_spectrum.py` 已有）——尾数占比 **≥ 70%** 才算"复现了 method3 方向"；仍是均匀分布 → 注入点或 kernel 还不对，回 1a 修。
   - `recurring_result_stuck` 的 `P_SDC` 显著高于单发 F1；**若 recurring 也全 Masked，才可以写"FSU 数据通路对 SDC 钝"**；只有单发 F1 全 Masked 不构成该结论。
   - 首轮"FPU 0% SDC"在 `plans/microarch-fault-injection-report.md` §7 逐条标注作废原因。

**补丁数**：≈ 8。**机器**：健康核（cholesky 级 wall-time）。

## Phase 10 — v1.1/P2：ROB spec_leak（method1 核心假设，把"实验失败"变成真结果）

**Status: complete（2026-09-08，2a/2b/2c + pilot 全过验收门）**

1. ✅ **2a spec_leak_probe_kernel**（870d7a0）：X10 泄漏窗口探针(v3 设计,经两次真机 trace 诊断迭代——泄漏值须无正确路径写者覆盖)。native==gem5 clean。
2. ✅ **2b 定向触发**（a09289b）：X10 spec_leak fc=25000,20 seeds 3 泄漏(15%);campaign pilot n=100:**P_SDC=14.0% [8.4,22.5],Reach=93%>90% 验收门,零 frozen**。首轮阴性修正为阳性:泄漏真实,窗口几何定转化率。X9/X3 阴性对照:泄漏可见性=消费者身份定律。
3. ✅ **2c 诚实边界**（1c21ab7）：AArch64 整数除零=架构静默(udiv x/0=0);ARM64 SE 无可恢复真异常载体,exc_suppress DUE→SDC 实验面在 ARM SE 诚实穷尽。
4. ✅ **formal 轮**（568021f + 3526fba，审计补跑）：①三寄存器 formal(X10/X9/X3 × n=128)——X10 **16.5% [11.0,24.2]** Reach 94.5%;X9 Reach 0%(无写者);X3 Reach 100% + 0% SDC(有写者无消费者)——**消费者身份定律 formal 级三臂闭环**。②ROB 深度轴(C2, rob∈{96,128,160})——SDC 8.1/9.8/5.6%、**DUE 单调升 11.3→13.1→19.0%**:深 ROB 拉长泄漏 physReg 所有权窗口→rename 一致性先破坏(DUE)后消费(SDC)——新机理,兼解释 C0 vs C2 平台差与首轮"ROB=160 整行掩蔽"之谜。

1. **新 kernel `spec_leak_probe_kernel.c`**（2a，`workloads/directed/`）：`data[]` 随机 → 难预测分支（`data[i] & 1`）→ 大量 squash；只在"跳"路径写目标架构寄存器（约束成 X10）；`t` 每轮重定义、定义后 1–2 条指令内被 `consume(t)` 读回（泄漏窗口 1–2 条指令）；`wrong_path_value` 与 `right_path_value` 差一个大常数（泄漏一眼可辨）；输出整个 `out[]`，`per_element_diff` oracle。用内联汇编或 `register ... asm("x10")` 把 `t` 钉到 X10。
2. **CHAOSROB `spec_leak` 改为定向**（2b，`src/cpu/o3/CHAOSROB/CHAOSROB.{py,hh,cc}` + gem5 新 hook，2–3 补丁）：新增 hook 到 `cpu/o3/commit.cc` 的 `Commit::squashAfter()`（或 `Rename::doSquash` / `RenameMap` restore 路径）。`spec_leak` 不再"随机挑一个错误路径 μop 不回滚"，而是**定位"错误路径上写目标架构寄存器 `--spec_leak_arch_reg`（默认 X10=10）的那条 μop"，只对它跳过 rename-map restore**（保留其 PRF 写）。参数 `spec_leak_arch_reg`（Int，默认 10）。
3. **`exc_suppress` 补真异常 kernel**（2c）：`divzero_loop_kernel.c`（整数除零循环）、`unaligned_ldp_kernel.c`（非对齐 `LDP`）——`exc_suppress` 首轮在 cholesky 上是 no-op（357/357 Masked/Inactive），因为没有 pending 异常可清。
4. **campaign `campaigns/pwf-v11-rob-specleak.yaml`**（2d，C2，`--chaos_rob --rob_mode spec_leak`，1 补丁）：轴 = `spec_leak_arch_reg {X10, X9, X3}` × 分支密度 {`spec_leak_probe` 天然高} × 窗口 ROB {96,128,160}。oracle `per_element_diff`——统计"`out[i] == consume(wrong_path_value(i))` 但分支实际走了 right 路径"的比例 = 投机泄漏 SDC 率。另跑 `exc_suppress` on `divzero_loop`/`unaligned_ldp`（`P(DUE→SDC 转化率)`）。**pilot n=100 → formal n=384**（`spec_leak` on `spec_leak_probe` X10，`exc_suppress` on `divzero_loop`）。
5. **验收断言**：`spec_leak` 的**阴性结论只在 `spec_leak_probe.c` 上 Reachability > 90% 时才成立**（证明注入确实落在泄漏窗口里）；否则记"实验未到位"，不是"泄漏不产生 SDC"。`plans/microarch-fault-injection-report.md` §4.2 更新：区分"spec_leak 阴性（实验到位）"vs 首轮"实验未到位"。

**补丁数**：≈ 6–7。**机器**：健康核。

## Phase 11 — v1.1/P3：L2 + DRAM（负载伪影，机械修）

**Status: complete（2026-09-08，3a/3b/3c + 双 pilot 全过）**

1. ✅ **3a kernels**（54eda38）：stencil_5pt(W=160,400KB,L2 贴身)+ stream_triad(6MB=12×L2 纯 DRAM 流),全数组回读 hash,native==gem5。
2. ✅ **3b 定向链**（9bdcf90）：`fault.addr_window`/`target_block_addr` 全链路;物理窗口真机标定(SE 数组帧 ≤4MB,>4MB 零页——默认全内存抽注命中未触达帧是首轮 DRAM 全 Masked 的根因之一)。
3. ✅ **3c pilots**：**DRAM P_SDC=87.0% [79.0,92.2] / L2 P_SDC=49.0% [39.4,58.7]**,n=100,Reach 100%,零 frozen。首轮"L2/DRAM 全 Masked"修正为**层级掩蔽梯度**(L2 的 51% Mask=L1 副本/重取;DRAM 的 13%=缓存胜出)。附带修 2 个真 bug:classify checksum regex 不认 `FINAL=` 前缀(真 SDC 被判 SimulatorError);stencil/stream golden 注册表错位(GOLDEN_ARRAYS→GOLDEN_IDS)。
4. ✅ **formal 轮**（2d4fd59 + 1ed81c2 + 3526fba，审计补跑）：L2 定向 **49.0% [44.0,53.9]**(n=384,与 pilot 点估计完全一致);DRAM 定向 **85.4% [81.5,88.6]**(n=384);**DRAM addr_map_sub 88.0% [80.2,93.0]**(n=100)——计划预言"stream_triad 上非零 SDC"验证,fwd_checksum 阴性确认为负载伪影。
5. ⏳ **未做(诚实标注)**：L2 tag/victim/TQ 臂与 protection 档对照(secded 等)——需新注入器代码(CHAOSCache targetField=tag、base.cc writeback hook,计划列为 2–3 补丁),本轮未实现;DRAM ecc_logic_fault formal 未跑(旋钮在,无对照需求信号)。L2 size sweep {256/512/1024 KiB} 未跑(kp920 已参数化,机械可跑,排下轮)。

1. **新 kernel**（3a，`workloads/directed/`，2 补丁）：
   - `stencil_5pt_kernel.c`：5 点 stencil，`--n` 让工作集 ≈ 2× L1（强制大量 L2 命中）/ ≈ 2× L2（强制 L2 miss + victim 流量）；逐元素输出 `array_hash`。
   - `stream_triad_kernel.c`：STREAM triad `a[i]=b[i]+q*c[i]`，工作集 ≥ 4× LLC（数组装不进缓存，每次访问真打 DRAM）；逐元素输出 `array_hash`。
2. **定向注入**（3b）：L2 用 `--target_block_addr` 定到 stencil 正在扫的行（不用随机块；CHAOSCache 现有 `targetBlockAddr`）。DRAM 用 `--addr_start/--addr_end` 跟随 stream_triad 扫描进度（缩到当前正在读的区间；CHAOSMem 现有 `addr_start/addr_end`）。
3. **campaign**（3c，2 config + CHAOSCache tag F5 + victim 2–3 补丁）：
   - **L2** `campaigns/pwf-v11-l2.yaml`（C0-CACHE，`configs/se/arm_chaos_cache.py --target=l2`）：{L2 data(定向), L2 tag(F5 同 set 合法对齐 tag——CHAOSCache 加 `targetField=tag` + 找同 set 合法对齐 tag), L2 victim(hook `mem/cache/base.cc` writeback 路径), TQ 地址(F5)} × `L2 size sweep {256/512/1024 KiB}`（`kp920_proxy` 已参数化）× protection {none, secded}。kernel = `stencil_5pt`（工作集 2× L2）。
   - **DRAM** `campaigns/pwf-v11-dram.yaml`（C2/C0，`--chaos_mem`）：{backing_byte(定向), addr_map_sub(F5, 已有), ecc_logic_fault(已有, 补 formal)} × protection {none, secded} × F2 {1,2,3-bit}。kernel = `stream_triad`（工作集 4× LLC）+ 写后立即读回 kernel。
   - **pilot n=100 → formal n=384**（L2 data 定向 on stencil；DRAM backing_byte 定向 on stream_triad；DRAM ecc_logic_fault）。
4. **验收断言**：**"L2/DRAM SDC 低"的结论只在工作集超 L2/LLC 的 stencil/stream 上、定向到活数据跑过才成立**；cholesky/l1d_reduce 上的 0% 明确标"负载伪影，不写进结论"（更新 report §13/§14）。L2 victim（无保护）的 `P_SDC` 预期 > L2 data。DRAM `addr_map_sub`（绕过 cache tag）在 stream_triad 上预期出现非零 SDC（对比 fwd_checksum 上的全 Masked）。

**补丁数**：≈ 6–7。**机器**：健康核（stream_triad 大工作集 → 单 run 可能到 10–30s，pilot 优先）。

## Phase 12 — v1.1 复现 + 报告收尾（贯穿 Phase 8–11）

**Status: complete（2026-09-08）**

1. ✅ **集 B 复现**:四关键 cell(FPU baseline / ROB spec_leak / L2 / DRAM 定向)集 A(node1 CPU) vs 集 B(node2+3 CPU,同 node1 内存)同 seed 同 manifest:**20/20 分类一致 × 4,零冻结**——"reproduced (same host, disjoint NUMA)"。
2. ✅ **报告收尾**:final-report-skeleton 5 处 v1.1 修正标注(零风险带 FPU/Exec/L2/DRAM 作废+修正数字;DFT FP 行;保护投资 L2/DRAM 行;spec_leak 阴性作废;诚实边界 #2 复现状态);ras_escape_analysis v1.1 campaign 映射补齐(163 cells 无 unmapped)。

**v1.1 补救轮(Phase 8–12)全部完成 + formal 补跑轮收官**(2026-09-08):诚实审计发现 pilot 轮漏跑计划指定的 formal 级,补跑六项(svd bitseg / spec_leak 三寄存器 / spec_leak ROB 深度 / L2 / DRAM / DRAM addr_map_sub,commit fe5c190..3526fba),全部 n=384(或 n=100×3 臂)零 frozen。最终 formal 级格局:**FPU mant_hi 92.4% / mant_lo 83.1% (svd) / DRAM 85.4–88.0% / L2 49.0% / spec_leak X10 16.5% (C0) · 8–10% (C2) SDC**;新机理:ROB 深度-DUE 梯度。四处首轮阴性伪影修正、6 个真 bug 修复不变。**仍开放(诚实)**:L2 tag/victim/TQ 臂与 protection 档对照(需新注入器代码)、L2 size sweep、DRAM ecc_logic_fault formal、Exec/IQ 同款修法(计划"本轮不做"清单)。

1. **复现（集 B / NUMA node 1）**：每个进 report 的**非零 SDC 数**、以及本轮触及的对照数（L2 data 定向、DRAM addr_map_sub、FPU recurring、ROB spec_leak）在 NUMA node 1 上重跑同 manifest，结局分类一致 + P_SDC 点估计落在集 A 的 95% CI 内 → 标 "reproduced (same host, disjoint NUMA)"。不一致 → 冻结该 cell，查是 cpu179 污染共享 L3/内存控制器，还是工具非确定性。
2. **报告收尾**：更新 `plans/microarch-fault-injection-report.md`（FPU §7 / ROB §4.2 / L2 §13 / DRAM §14 的"已修正"标注 + 位谱数据）；更新 `tools/ras_escape_analysis.py` 的逃逸分解（fpu/exec 等目前是 "? unit not in map"）。

**v1.1 本轮不做（转入下方 v1.2 深化轮 Phase 13–17）**：整数执行 Exec 同款修法；IQ tag_sub/f3；PRF 网格扩 formal + F3/F4；ROB=160 掩蔽根因；BPU 返回栈/间接预测器 F5 + L1I protection 对照；H7 FS formal；真独立复现。

---

# ═══ v1.2 深化与收口轮（Phase 13–17）——补 v1.1 遗留 + 独立复现 ═══

> **依据**：v1.1 补救轮（Phase 8–12）已在 `gem5-fi` HEAD `f9124d7` 收官（28 commits `4bf8d0d..f9124d7`，已核对——kernel/oracle/campaign 产物齐备）。四处首轮伪影（FPU/Exec/L2/DRAM 0% + spec_leak 阴性）中 **FPU/L2/DRAM/spec_leak 已修正为阳性**（FPU mant 83–92% / L2 49% / DRAM 85–88% / spec_leak X10 16.5%）。本轮补 v1.1 明确列出的遗留缺口 + 首次真正的第二机独立复现。
> **执行环境**：同 v1.1——build + campaign 只在 Linux 服务器（健康机，`numactl` 钉有内存的 NUMA node）。本机仅写代码/提交/push，遵 `gem5-fi/CLAUDE.md`。
> **深度策略**：pilot n=100 → 有信号或与 method1/2/3 直接对照的 cell 扩 formal n=384 + 5% 重放 + Wilson CI。

## Phase 13 — 整数执行 Exec + 发射队列 IQ 同款修法（最高优先，直接类比刚推翻的 FPU）

**Status: pending**

1. **CHAOSExec 注入点重写为 PRF-dest 路径**（同 `bfa9c4f`）：整数结果走 `setRegOperand → cpu->setReg → regFile`，旧 `instResult` 队列是死路径（唯一消费者 checker=Null）——不重写则下列模式全部架构不可见。
2. **CHAOSExec 模式对齐 FPU**：`bitseg`（整数无尾数 → 按 byte/nibble 段）/ `recurring_result_stuck`（Phase 8.4 契约已就绪）/ `f3_data_dependent`（操作数落 `--exec_operand_range` 才损坏）/ stuck-at。
3. **新 kernel `elemwise_int_kernel.c`**（逐元素输出 + `array_hash`/`per_element_diff` oracle）；cholesky + reg_chain 作归约对照。
4. **IQ 深化**：`stale_plausible_kernel.c`（过期值 = 上一轮的**合法**结果，不是垃圾——F6 能读 stale 的真实形态）+ CHAOSIQ `tag_sub`（F5：唤醒 tag 换成另一个合法 in-flight tag）+ `f3`。首轮 IQ 只测了 wake_omit/src_ready/wake_phase，`tag_sub` 是 deferred（`CHAOSIQ.py:19`）。
5. **campaign**：`pwf-v12-exec.yaml` + `pwf-v12-iq.yaml`；pilot n=100 → formal n=384（Exec `recurring` on elemwise_int + cholesky；IQ `tag_sub` on madd_chain + cholesky）。
6. **验收断言**：Exec 只有在**逐元素 kernel + recurring + f3 都跑过仍全 Masked**时，才可写"整数执行对 SDC 钝"——只有首轮的单发 F1 + 归约负载全 Masked 不构成该结论（同 FPU 教训）。报告 §6 定稿（撤 ⚠ 标注或改为定论）。

**补丁数**：CHAOSExec 4–5 + CHAOSIQ 2 + kernel 2 + campaign 2 ≈ 10。

## Phase 14 — 存储层级臂补全 + protection 对照

**Status: pending**

1. **CHAOSCache `targetField=tag`**（F5）：同 set 内换一个合法对齐 tag（不是随机翻位）——建模 tag SRAM 软错误命中合法别名。
2. **victim/writeback 路径 hook**（`mem/cache/base.cc`）：victim buffer / 回写数据错。
3. **L2 事务队列（TQ）地址 F5**。
4. **L2 容量扫描** {256 / 512 / 1024 KiB}（`kp920_proxy` 已参数化，机械可跑）。
5. **L2 + DRAM secded protection 档对照**（`local_mbu` 多位档已就绪 Phase 8.3）：raw vs secded_poison 的风险反转图，1/2/3-bit 各档。
6. **DRAM `ecc_logic_fault` formal**（旋钮在，首轮只有 pilot）。
7. **campaign**：`pwf-v12-l2-arms.yaml` + `pwf-v12-dram-ecc.yaml`；pilot → formal n=384（L2 tag F5 + L2 victim on stencil_5pt；DRAM secded on stream_triad）。
8. **验收**：L2 victim（无保护）P_SDC 预期 > L2 data 定向（49%）；报告 §13/§14 补 victim/tag 行 + protection 反转图。

**补丁数**：CHAOSCache 3–4 + campaign 2 ≈ 6。

## Phase 15 — spec_leak 扩样 + ROB=160 掩蔽根因 + PRF 网格补 formal

**Status: pending**

1. **spec_leak X10 formal 扩到 n=384**（当前 n=128 / n_valid 121）：C0 + C2 双平台，把 16.5% [11.0,24.2] 的 CI 收窄。
2. **ROB=160 整行掩蔽根因排查**：Phase 10 已发现"ROB 深度 96→128→160 → DUE 单调升 11.3→13.1→19.0%"梯度机理（深 ROB 拉长泄漏 physReg 所有权窗口 → rename 一致性先破坏）。用 readtrace 级分析确认 Phase 3 遗留之谜：ROB=160 下 X3 bit0 翻转是否落在 squash 边界 / 被关键路径重算覆盖。读 `rob.cc` `numROBEntries` × `squashWidth` × IQ/LSQ 深度交互。
3. **PRF 位段/ABI 角色/窗口扫描 pilot 网格扩 formal n=384** + F3（数据相关触发）/ F4（stuck-at）轴——Phase 3.1 剩余子项。

**补丁数**：工具 1–2 + campaign 3 ≈ 5。

## Phase 16 — BPU 返回栈/间接预测 + L1I protection 对照

**Status: pending**

1. **BPU 返回地址栈预测器**（分支预测侧的 RAS，非异常 §17 的 RAS）+ **间接预测器 F5**（换成另一个合法跳转目标）。
2. **squash 后架构态 == golden 联合观测**：强化"BPU 错但架构无恙"的确认（当前只有结局分类，没有架构态逐位比对）。
3. **L1I imm/Rm/Rd/cond 字段替换**（当前只做了 opcode/rn）。
4. **L1I sed vs secded 2-bit protection 对照**（N1：L1I data 是 SED、双比特静默）。
5. pilot → formal n=384（BPU 间接预测 F5 on branchy；L1I imm 字段 on l1iloop）。

**补丁数**：CHAOSBPU 2 + CHAOSCache(L1I) 2 + campaign 2 ≈ 6。

## Phase 17 — H7 FS formal + 真·独立复现

**Status: pending**

1. **H7（PTW ECC on/off）boot 期注入 formal**（Phase 5 唯一剩项）：健康机 / `numactl` 钉核多核并行；restore from `cpt.100000000`（boot 早期 walk 密集期）+ PTW clear_valid + ECC {off, on} × n=384；FS boot ~30min + ~4min/rep。验收断言：ECC-on spurious ≈ 0 vs ECC-off > 0（分支原始 5-seed 数据的 formal 级确认）。
2. **真·第二台健康机独立复现**（取代 Phase 12 的"同种子跨 NUMA bit 级一致"——那是确定性仿真必然结果，不算复现）：
   - 关键 cell（L1D 97.7% / PRF X3 3.9 / RAT 95.8 / LSQFwd 37.6 / L1DForward 90.9 / FPU mant_hi 92.4 / DRAM 85.4 / L2 49.0 / spec_leak X10 16.5 / AGU 100% DUE）**换随机种子集**在健康机复跑 n=384。
   - **未改动 cell 的跨机吻合**：L1D 97.7% 在健康机（新 gem5 build、不同 NUMA 域）重跑，点估计落入原 CI → 才证明首轮数字不是 cpu179 污染。
   - 不一致 → 冻结该 cell，查工具非确定性 vs 平台污染。

**补丁数**：主要是 campaign 跑批 + 复现脚本；代码改动 ≈ 2。

---

## 执行顺序与理由

```
Phase 1 (工具正确性+落盘)  ← 本分支主题，1-2 天                              ✅ complete
Phase 2 (protection 对照)  ← 改变结论级别，L1D 97.7% 没有对照组是当前最大科学缺口  ✅ complete
Phase 3 (网格深化)         ← 与 Phase 2 可交错（campaign 跑批时写 Phase 4 代码）    ✅ complete
Phase 4 (F5/F6 模式)       ← method1/2/3 对照的实质内容                          ✅ complete
Phase 5 (FS 管线)          ← 依赖 Phase 4.4 (TLB F5)                            in_progress（工具链就绪，method2 三根因闭环）
Phase 6 (元分析+复现)      ← 贯穿，每完成一个 Phase 更新一次                       in_progress
Phase 7 (系统级)           ← 后置

--- v1.1 补救轮（首轮伪影修正，gem5-fi HEAD f9124d7 已收官）---
Phase 8  (基础设施)        ✅ complete — 非 hash oracle + 均匀采样 helper + 多位 ECC 档 + recurring 契约松绑
Phase 9  (FPU)             ✅ complete — PRF-dest 重写 + 六模式；svd mant_hi 92.4% / mant_lo 83.1% SDC (n=384)
Phase 10 (ROB spec_leak)   ✅ complete — 定向 X10 探针；16.5% SDC (n=128) + 消费者身份定律三臂 + ROB 深度-DUE 梯度
Phase 11 (L2/DRAM)         ✅ complete — stencil_5pt/stream_triad + 定向；L2 49.0% / DRAM 85.4% / addr_map_sub 88% SDC
Phase 12 (复现+报告收尾)   ✅ complete — 集 B 同种子跨 NUMA 一致；report §7/§4.2/§13/§14 已修正

--- v1.2 深化与收口轮（补 v1.1 遗留 + 真独立复现，Linux 健康机）---
Phase 13 (Exec + IQ 同款修法)  ← 最高优先，直接类比刚推翻的 FPU：CHAOSExec PRF-dest 重写 + elemwise_int + IQ tag_sub
Phase 14 (存储层级臂补全)      ← L2 tag F5 / victim / TQ + 容量扫描 + L2/DRAM secded protection 对照
Phase 15 (spec_leak 扩样 + ROB=160 根因 + PRF 网格 formal)  ← spec_leak n=128→384；readtrace 排 ROB=160 掩蔽
Phase 16 (BPU 返回栈/间接预测 + L1I protection)  ← 间接预测器 F5；L1I imm/Rm/Rd/cond + sed vs secded 2-bit
Phase 17 (H7 FS formal + 真独立复现)  ← Phase 5 唯一剩项 + 换种子/第二机复现关键 cell（含未改动的 L1D 97.7%）
```

补丁纪律：沿用 CLAUDE.md（一补丁一单元、真机自验证 100%、自动 push 到 fix/fi-tool-correctness）。**v1.1 补救轮（Phase 8–12）遵 `gem5-fi/CLAUDE.md`**：每补丁 `numactl --cpunodebind=0 --membind=0 -- scons ... -j16`（零新增警告）→ 真机跑受影响行为贴真实输出 → `reg_chain` golden `f247ef3fe6f02cfd` 回归 → commit + push；commit 尾注 `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`。campaign 跑批用后台；pilot n=100 先看 Reachability + 方向，formal n=384 + 5% 重放（不一致冻结）+ Wilson 95% CI。

## Next Step

**Phase 1–4 收官；Phase 5–6 in_progress（H7 formal 移入 Phase 17）；v1.1 补救轮 Phase 8–12 全部收官**（`gem5-fi` HEAD `f9124d7`，28 commits `4bf8d0d..f9124d7` 已核对——kernel/oracle/campaign 产物齐备；FPU/L2/DRAM/spec_leak 四处首轮伪影已修正为阳性）。`microarch-fault-injection-report.md` 已同步 v1.1 结果。

下一步（**Linux 健康机** `gem5-fi/`，分支 `fix/fi-tool-correctness`，`numactl` 钉有内存的 NUMA node）：

**Phase 13.1 — CHAOSExec 注入点重写为 PRF-dest 路径**（最高优先）。直接照搬 FPU 的 `bfa9c4f`：整数结果走 `setRegOperand → cpu->setReg → regFile`，旧 `instResult` 队列是死路径（唯一消费者 checker=Null）。这是 §6「整数执行 0% SDC」大概率是伪影的深层根因——FPU 改完这一处，0% 直接变 92%。
- 真机验收：cholesky 上单发 F1，看是否首次出现非零 SDC / Masked 分布（对照 FPU `bfa9c4f` 的 4 seeds 2 SDC）；`reg_chain` golden `f247ef3fe6f02cfd` 回归。

**接着 Phase 13.2–13.6**：CHAOSExec 六模式（byte/nibble bitseg / recurring / f3 / stuck-at）+ `elemwise_int_kernel.c` + IQ `tag_sub`(F5) + `stale_plausible_kernel.c` + `pwf-v12-exec.yaml`/`pwf-v12-iq.yaml`；pilot n=100 → formal n=384。验收：Exec 只有逐元素 kernel + recurring + f3 都跑过仍全 Masked，才可写「整数执行对 SDC 钝」。

**并行可推进**：Phase 15.1（spec_leak X10 扩 n=384，收窄 16.5% 的 CI）、Phase 17.1（H7 boot 期 formal，健康机多核并行）——两者不依赖 Phase 13 的代码。
