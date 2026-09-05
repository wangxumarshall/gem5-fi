# 下一步计划：鲲鹏920 SDC 故障注入 — S2/S3 收尾 → 网格深化 → F5/F6 → FS

> 依据 `docs/KUNPENG920-故障注入方案详细工程设计.md`（§3.1 阶段表）× 仓库实际进展（HEAD af64ef7 + 未提交 formal 结果）编写。
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
4. ⏩ **多 workload 对照**：ExMon formal ✅（ac1e131，100% DUE 单元级确认 + 修复第 9 个漏网注入器 7108428）。**剩余**：cholesky 上的全 Masked（IQ/Exec/FPU/Decode/BPU/RAS）在第二 workload（reg_chain）上复检。

**验收**：每单元 ≥2 轴 × ≥3 level 或有书面理由跳过；全 Masked 单元在第二 workload 上置信上界仍 <1% 才写进结论。

## Phase 4 — F5/F6 机理子模式（对齐三现场案例的核心缺口）

**Status: complete（2026-09-04，6/6 模式；4.4/4.5 的 FS formal 排 Phase 5）**

3. ✅ **IQ src_ready_bitflip / wake_phase**（9db60d6 + 4aee770 + 9991185）：**三模式图谱全 0% SDC**（wake_omit Hang 75.3% / src_ready_bitflip 100% DUE / wake_phase 100% DUE 平顶）；结局由依赖密度决定（madd_chain 100% vs cholesky ~5%）；**wake_phase 代理不捕获 method3 相位签名**（E3 边界：method3 相位在 LSU 转发时序，不在调度唤醒相位）。
2. ✅ **LSQFwd fwd_source_sub**（05db0e2 + 10a811f）：**P_SDC=37.6% [32.8,42.6] vs byte_flip 4.7%——故障形态 > 故障位置（8 倍 SDC）**，0% Masked；错源=合法域内整字错误。phaseOffset（相位敏感性曲线）仍 deferred。
1. ✅ **ROB spec_leak**（1ca0346 + ccb6eda + 9e549af）：机理落地在 Rename::doSquash 回滚抑制（CHAOSROB.cc:140 的 deferred 注释指向的 squash 路径）。pilot + formal（branchy X3/X9 n=384 each）：**单次回滚抑制全 Masked——泄漏值被正确路径重写覆盖**（X3/X9 短命循环变量无消费者）。下一 cell：X19 callee-saved 长活类（method1 原始目标），跑批中。rename 子系统四注入点全 0% SDC。

| 优先 | 模式 | 位置 | 对照案例 |
|---|---|---|---|
| 1 | **ROB spec_leak**（squash 不回滚错误路径写） | `CHAOSROB.cc:140` deferred 注释处 | method1 投机泄漏 |
| 2 | **LSQFwd fwd_source_sub + phaseOffset** | `CHAOSLSQFwd.py` param surface（未加） | method1 错源 / method3 相位塌方 |
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
✅ **method2 三根因三臂全通**（5c09457）：O3 checkpoint restore 验证（631M ticks 零 panic）；PRF 臂（X10 触发 + 构造期 schedule 断言 bug 修复——rebase 现覆盖 phys）/ AddrPath 臂（byte7_zero：canonical→非规范内核地址签名）/ TLB 臂（活页替换）全部真机触发。**三臂对照 campaign 就绪**——需内核活跃消费 x10 的 workload 才有签名可比（稳态全被吸收）。剩余：三臂 pilot 跑批（等 workload）、boot 期 checkpoint（H7 双臂）。

1. `configs/fs/kp920_proxy_fs.py` 现在是 TODO stub（只 print + delegate）——落 V110 参数（`_pre_instantiate` 同 SE 版）。
2. **Atomic→`m5 checkpoint`→O3 restore 流水线**（§3.2）：boot.rcS 已有思路；解决 FS formal 不可重复跑的 wall-time 问题（fb34343 的 4/5 超时根因）。
3. **CHAOSPTW cherry-pick + H7 formal**（分支数据：ECC-on spurious≈0 / off >0，5-seed）→ formal n 扩大。
4. **TLB F5 活页 cell**（依赖 Phase 4.4）：`p_SDC(pfn→活页)` —— 文档标注"最危险路径的量化"。
5. method2 三根因区分实验（§2.10 C 最后一行：PRF vs AddrPath vs TLB 同签名注入）。

## Phase 6 — S5 元分析强化 + 健康机复现（贯穿）

**Status: pending**

1. `tools/ras_escape_analysis.py` 实现 weight(unit)（gem5 stats occupancy 采集）——目前 priority 表混合 pilot/formal 数据且无权重。
2. 修正 escape_decomposition.md 的 "? (unit not in map)" 行（fpu/lsqfwd 等映射缺失）。
3. **所有 formal 关键 cell 在第二台健康机复现**（S6，cpu179 是故障机 —— 每份 summary.md 的 Honesty note 都在提醒这件事）。复现清单：L1D 97.7%、PRF X3 3.9/92.7、RAT 95.8、LSQFwd 100% DUE。
4. 最终报告骨架：§4.2 三类交付物（DFT 向量、保护排序、位谱指纹库）+ §4.3 诚实边界。

## Phase 7 — S4 系统级（独立子项目，可后置）

CHAOSCHI/CHAOSNoC pilot 已能触发（7c854bb/7582e8c，未提交的 ruby test configs 在工作区）；HCCS/CHI/Garnet formal 排期在设计文档里本就是 S4 独立子项目，等 Phase 2-5 出结果后再决定投入。

---

## 执行顺序与理由

```
Phase 1 (工具正确性+落盘)  ← 本分支主题，1-2 天
Phase 2 (protection 对照)  ← 改变结论级别，L1D 97.7% 没有对照组是当前最大科学缺口
Phase 3 (网格深化)         ← 与 Phase 2 可交错（campaign 跑批时写 Phase 4 代码）
Phase 4 (F5/F6 模式)       ← method1/2/3 对照的实质内容
Phase 5 (FS 管线)          ← 依赖 Phase 4.4 (TLB F5)
Phase 6 (元分析+复现)      ← 贯穿，每完成一个 Phase 更新一次
Phase 7 (系统级)           ← 后置
```

补丁纪律：沿用 CLAUDE.md（一补丁一单元、真机自验证 100%、自动 push 到 fix/fi-tool-correctness、禁 Co-Authored-By 尾注）。campaign 跑批用后台 + 健康机（如有）。

## Next Step

Phase 3 进行中（#1–#7 网格 + 3 工具补丁已提交）。**今日新增两个重大工具修复**：comp_map 静默改道（8e01219——rob/iq formal 作废重跑中）+ campaign hang 孤儿进程泄漏（7abc72e）。当前后台队列：IQ formal 重跑（修正路由+分散采样，早期信号 Hang 主导）→ freelist mark_free formal。队列完成后：
1. 提交 IQ/freelist formal 结果（与旧"全 Masked"对照，预期结论修正级别）。
2. **rob formal 已完成**（真挂 CHAOSROB，384/384 Masked 有效确认）——随队列一起提交。
3. Phase 3.4 多 workload formal 级复检（reg_chain pilots 已提交 13f4d41，方向一致）。
4. PRF F4 stuck / F3 fault_model 轴扩展。
5. Phase 3 收口后转 Phase 4（F5/F6 机理子模式，ROB spec_leak 优先）。
