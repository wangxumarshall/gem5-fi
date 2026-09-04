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

**Status: pending**

当前 formal 几乎全是 `target_index=0` + `transient_bit_flip` 单 cell。按设计文档，最优先的三根轴：

1. **PRF（§2.1）位段 × ABI 角色网格**：bit {0,11,31,32,47,63} × 寄存器 {X3(已做), X0-X7 参数类, X19-X28 callee-saved, X29/X30} × fault_model {bit_flip, F2 相邻2位, F4 stuck, F3 数据相关(已实现 triggerValuePattern)}。先 pilot n=100 筛可达率，再对非零 cell formal n=384。
2. **PRF 窗口扫描（H2）**：ROB {96,128,160} × PhysInt {128,160,192} 固定 X3 bit_flip —— kp920_proxy.py 参数化即可。
3. **RAT（§2.2）f5_substitute + freelist mark_free formal**：method1 "历史残留" 主对照实验（§2.2 E 的 P(history_residue) 指标）。f5_substitute 模式已在 CHAOSRenameMap 实现。
4. **多 workload 对照**：cholesky 上的全 Masked（IQ/Exec/FPU/Decode/BPU/RAS）需要在第二 workload（reg_chain / dep_chain / branchy_reduce）上复检 —— 排除"单 workload 伪 Masked"。ExMon formal（spinlock_checksum，pilot 5/5 DUE）也在此批。

**验收**：每单元 ≥2 轴 × ≥3 level 或有书面理由跳过；全 Masked 单元在第二 workload 上置信上界仍 <1% 才写进结论。

## Phase 4 — F5/F6 机理子模式（对齐三现场案例的核心缺口）

**Status: pending**（全部 deferred 状态，逐个补，一补丁一模式）

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

**Status: pending**

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

Phase 3.0 ✅ 完成（32629f7 + c7cc34b）。下一步 Phase 3 网格深化，最优先两件：
1. **FPU 重跑换 workload**：neon_lane 的 FP eligible 流太小（Reach=17%）——用 gemm_float_kernel（FP 密集）重跑 §2.6 formal，恢复 n_valid≥384 量级。
2. **PRF 位段网格（§2.1 C）**：bit {0,11,31,32,47,63} × 寄存器 {X3,X9,X0-X7 参数类,X19-X28} × fault_model {F1, F2 相邻2位, F3 数据相关, F4 stuck}——先 pilot n=100 筛可达率再 formal。
