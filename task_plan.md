# Task Plan — 鲲鹏920 SDC 方案 100% 覆盖收尾计划

> **Goal**: 对《KUNPENG920SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md》做到**任务级零遗漏**：每个待做项要么完成（含真机验证），要么因环境门控显式登记为 deferred（带原因与解锁条件）。产出维度①②已完成大半，本计划补齐缺口并重点建设维度③（openEuler 诊断引擎）与维度④（芯片设计建议）。
>
> **纪律**（CLAUDE.md）：一补丁一单元 → 三步真机自验证（干净构建 + 功能验证 + 不相关回归）→ commit（无 Co-Authored-By 尾注）→ push `fi-wangxu`。每任务勾选 checkbox 前必须引用真机输出。
>
> 状态图例：`in_progress` / `complete` / `blocked(env)`
> 详细差距依据见 `findings.md`（2026-09-07 盘点）。

## Current Phase
Phase 1–2 — **complete**（1.1–1.6 + 2.1–2.4 全勾）。Next: Phase 3 formal 批量补齐（Task 3.1 FSU formal）

---

## Phase 1 — P0 工具/注入器缺口补全（方案 §5.7/§5.8/§4.3）

**Status: complete**

- [x] 1.1 **CHAOSCache tag/valid/dirty/repl/coh 字段级注入**（§5.8B）— `6c672323`
  - 验证实证：tag→SDC `bd34ebf3da704050`；valid/dirty/repl/coh→Masked（诚实）；G0 2/2 sha256 一致；回归 `f247ef3fe6f02cfd`；构建零警告
  - 执行中发现：v1 tag 直写 setTag → snoop_filter panic（SimulatorError），改 findBlock false-hit 分流（v2）
- [x] 1.2 **CHAOSCache victim 注入**（§5.8A hook `base.cc WritebackBlk`）
  - 验证实证：注入日志 `Tick: 20034000 ... Field: victim (writeback-path) ... OldByte: 0x0, NewByte: 0x40` + `numVictimFaults 1`；多注入（32 faults）→ checksum `3858cbed195cd715` ≠ golden → SDC（传播机制实证）；单次注入 Masked（首个写回是 BSS 零页死数据——victim 语义的诚实结果）
  - 回归：l1d_reduce golden `f44d2b9cd4a173cd` 不变；reg_chain `f247ef3fe6f02cfd` 不变；构建零新警告（`-Wreorder` 为 HEAD 预存，stash 对照实证）
  - 执行中发现：victim 为纯事件驱动字段，不能走 attackEvent 采样（会空转消耗 maxFaults 预算导致 0 真注入）——构造时跳过 scheduleAttack，writebackBlk hook 内做概率抽取
- [x] 1.3 **CHAOSArmTLB `pfn_to_mapped_page`（F5→活页静默 SDC，最危险路径）**（§5.7B）
  - 验证实证：FS checkpoint inject ≥1 注入，日志 `Mode: pfn_to_mapped_page (F5 live-page), VA: 0xffffff807fbd3038, old_pfn: 0xffbd3, new_pfn: 0x80c80, donor_size: 0xfff`（new_pfn 来自同 TLB 活条目枚举，同页大小 donor）；首注入直接触发 guest `Internal error: Oops: 9600004f`（ESR DABT L0 WnR=1，core179 同形态）→ gem5 正常 Kernel-oops exit，非 SimulatorError
  - 合法域压力验证：probability=1.0/unlimited → 84,681,246 次注入 0 panic 0 SimulatorError（远超 ≥1000 要求）
  - 回归：reg_chain golden `f247ef3fe6f02cfd` 不变；构建零错误零新警告
  - 实现：TLB 加 `friend class CHAOSArmTLB`（枚举 protected `table` AssociativeCache）；donor 候选 = 同 TLB 其余 valid 且同 pageSize 条目；无候选时诚实 decline（不误落回 bit_flip）
- [x] 1.4 **CHAOSArmTLB iTLB 挂载 + protectionModel 参数**（§5.7B）
  - 验证实证（iTLB）：fs_checkpoint --tlb-itlb 注入日志 `VA: 0xffffffc0080ed974`（kernel text）pfn bit33 翻转 → 取指 BadAddress panic（Crash 结局，i-side 行为可见）
  - 验证实证（parity）：同 seed 同注入对照——none → guest 访问坏地址 `0x280b0a6c0` panic（Crash）；parity_interleaved → 日志 `bits=1 -> DetectedInvalidated (pfn restored + entry invalidated; next access rewalks)` ×2，系统继续正常运行（保护生效）
  - 回归：reg_chain golden `f247ef3fe6f02cfd` 不变；构建零错误零新警告
  - 执行中发现：v1 只 invalidate 不恢复 pfn——当前 lookup 已持有坏翻译仍会 panic；v2 改为恢复原 pfn + invalidate（当前访问走正确翻译，下次 miss 重走），protection 日志改 endl 强制 flush（panic 前 buffer 丢失）
- [x] 1.5 **RAT/ROB read-trace API（H3 跨单元一致性前提）**（§4.3/§6.3）
  - 验证实证（RAT）：dep_chain f5_substitute seed=11 → `ReadTracePoll: cycle 1050 RAT-corrupted PhysReg[27] reads_before_overwrite=0` → `cycle 6050 ... =1` → 稳定 1（坏映射消费者计数 0→1，H3 证据）；run 正常完成 golden 一致（Masked）
  - 验证实证（ROB）：entry_bitflip fc=5000 → `ReadTraceArm: ROB-corrupted head dest PhysReg[78]` + `ReadTracePoll: cycle 5050 ... =0`；head 无 renameable dest 时诚实 `ReadTraceArm: declined`
  - runner：rat/rob 日志的 ReadTrace 正则解析（reads_before_overwrite 列）+ comp=="rob" 路由（--chaos_rob/--rob_mode）+ rob_injections.log 计数
  - 回归：PRF/regfile 零触碰（git diff --stat 实证）；reg_chain golden `f247ef3fe6f02cfd` 不变；构建零错误
  - 执行中发现：100k-cycle 首次 poll 在短 workload（dep_chain ~13k cycles）永不 fire——改 50-cycle 首 poll + 5000-cycle cadence；ROB head 常为 store/branch（无 dest）——declined 诚实登记
- [x] 1.6 **AGENT_TASKS.md 登记簿建立**（附录 G.1）
  - 验证：AGENT_TASKS.md 入库，单行格式 `<id> | depends | owner | status | assert_hint` 与方案 G.1 一致；登记 18 注入器（全 done）+ S0 基础 3 项 + 本计划 Phase 1–7 任务 + 7 项 deferred（含原因与解锁条件）；此后每完成任务同步更新

## Phase 2 — kernel 库补全（方案 §5 各 D 段）

**Status: complete**

**Status: in_progress**

**Status: pending**

- [x] 2.1 **gemm_float / gemm_double**（§5.6D，GEMM popcount 中位 12/28 锚点）
  - gemm_float：origin/fi 提取（golden `d74f24ae79deb7d2` 三方一致：binary/native/gem5）
  - gemm_double：新写（N=32 确定性整数操作数、-fno-tree-vectorize 保标量 FPU 链；golden `6295f007a890b108` native==gem5 逐位一致）
  - F1 注入 SDC 实证：CHAOSFPU v3 源读 hook，seed=6 → checksum `0078f84e140e50b5` ≠ golden → SDC；注入 Old `0x412b774e00000000` New `0x412b774e00080000`（mantissa 单比特），bit_spectrum.py 输出 mantissa 100%/popcount median=1 正常
  - golden IDs 入 runner（gemmfloat/gemmdouble-golden-v1）
  - 回归：reg_chain `f247ef3fe6f02cfd` + gemm_float `d74f24ae79deb7d2` 不变；构建零错误
  - 执行中发现（重要，三连修）：① ARM ISA 不设 IsFloating 标志→CHAOSFPU isFloating() 恒 false（144k 采样 0 命中）→改 dest/src reg class 判定（Float+Vec）；② ROB-head corruptResultRegVal 对 vec 路径完全失效（FP 走 getWritableRegOperand 绕过 setRegOperand；head 的 result 已 pop 5089/5089）→v2 setRegOperand writeback hook（RegVal+blob 双 overload）；③ 背靠背依赖链（fmadd d0→fmadd d0）走 bypass 网络从不回读 PRF，PRF cell 注入被转发击败（15 seed 全 Masked）→v3 getRegOperand 源读 hook（读即破坏，传播保证）；附：CHAOSFPU.hh include guard 与 CHAOSExec 冲突（复制未改）→修复；FPU attackCheck skip 无 backoff（probability=1.0 → 0 间隔死循环）→+1-cycle backoff
- [x] 2.2 **svd_iterative + fma_reduction_kernel**（§5.6D）
  - svd：origin/fi 提取（Jacobi 迭代；golden `4afb95b5b32f3820` 三方一致）
  - fma_reduction：新写（N=4096 精确可表示操作数链式 fma 归约，-fno-tree-vectorize 标量 FMADD；golden `0efaf0ffa70ab1a0` native==gem5）
  - 注入 SDC 实证：svd seed=3 `fc71f4c5671acc34` / seed=4 `4710112277c05327`；fma seed=1 `1a41808b34338752` / seed=2 `0ef2f0ffa6fd19a0`（均 ≠ golden，CHAOSFPU v3 源读 hook）
  - golden IDs 入 runner（svditerative/fmareduction-golden-v1）
  - 回归：reg_chain `f247ef3fe6f02cfd` 不变
- [x] 2.3 **整数对照 kernel：MADD 链 / SMULH / ADDS→B.cond**（§5.10D）
  - madd_chain：origin/fi 提取（golden `9e8050e1503c34ab` 三方一致）
  - smulh_adds：新写（内联 asm 保证 SMULH 链 + ADDS→B.vs→双路径累加形态；golden `58e7676693d02056` native==gem5）
  - CHAOSExec 位段注入非零计数实证：low/mid/high 三段各 1 注入（Mask 0x1/0x1000/0x1000000000000，`Site: int_writeback_result`）
  - golden IDs 入 runner（maddchain/smulhadds-golden-v1）
  - 回归：reg_chain `f247ef3fe6f02cfd` 不变
- [x] 2.4 **indirect_jmp / struct_field / crc_state + movbe 正式入库**（§5.9/§5.8/§5.2D）
  - struct_field/crc_state：origin/fi 提取（golden `afebbd4c86e8cfdf`/`d27806e62c9d3869` 三方一致）
  - indirect_jmp：新写（函数表 BLR 间接分支链，objdump 确认 165 个 blr 位点；golden `3c791622c2f18a00` native==gem5）
  - movbe：fi_research/probes 正式入库（golden `iters=200 fails=0` native==gem5，fail_count oracle 模式）
  - golden IDs 入 runner（structfield/crcstate/indirectjmp-golden-v1 + movbe-failcount-v1）
  - 回归：reg_chain `f247ef3fe6f02cfd` 不变

## Phase 3 — formal campaign 批量补齐（方案 §4.6 n=384 标准）

**Status: pending**

- [ ] 3.1 **FSU formal**（§5.6：位段×算子×精度，gemm/svd/fma kernel，n≥96/cell 起步 → 关键 cell 384）
  - 指标：sign/exp/mantissa 位谱 + popcount 对标 method3（85–93%/0–1/中位 3~28）；向量 PRF vs FSU 通路 KS 检验
- [ ] 3.2 **Exec 阴性对照 formal**（§5.10：`P_SDC(Int) << P_SDC(FSU/转发)` 量化）
- [ ] 3.3 **RAT/freelist/ROB formal**（§5.2/5.3：P_SDC vs 距提交距离 D 曲线；exc_suppress 转化率；损坏 popcount 中位 >16 对标 method1）
- [ ] 3.4 **Cache 字段级×protection formal + L2 size sweep（H4）+ L1I SED vs SECDED**（§5.8）
- [ ] 3.5 **PCE vs raw 对比 formal**（§5.8：CHAOSL1DForward P_SDC 显著高于 raw）
- [ ] 3.6 **FS formal：TLB pfn→活页 / pfn→未映射 + ESR DFSC 分布 vs `0x96000004`；PTW ptwEcc on/off；SysReg 白名单 cell**（§5.7）
- [ ] 3.7 **PRF formal 补样 n=96→384**（现有 8 cell × 96 → 384，保 seed 前缀一致可增量补 288/cell）
- [ ] 3.8 **method2 三根因区分实验**（附录 B：PRF/AGU/TLB 三注入的 ESR/PC/x10 形态比对打分表）
- [ ] 3.9 **F3/F6 相位敏感性曲线**（§6.4：`|phaseOffset|≥1` vs 0 比值 ≥5×；method3 三必要条件去一归零对照 cell）
- [ ] 3.10 **假设表 H0/H3/H4/H8+ 回填**（§6.1，与 3.1–3.9 数据联动更新方案文档）

## Phase 4 — 第 7 章 openEuler 诊断引擎（维度③，整体新建）

**Status: complete**

**Status: pending**

- [x] 4.1 **ESR_ELx EC/FSC 解码器**（§7.3：`tools/diag/esr_decode.py`）
  - 验证实证：`ESR 0x96000044` → `EC 0x25 Data Abort from current EL, WnR=1 (write), FSC=0x04 Translation fault level 0`，SDC 权重 ★★★★（精确匹配计划验收）；`0x96000004` → WnR=0 同族；日志文本提取（ESR=0x... 大小写不敏感）
  - pytest 7/7 通过（tests/test_esr_decode.py）：core179 写/读签名、指令 abort、SError 5★（RAS 记录依赖 note）、Undef/BRK、文本提取、CLI JSON
- [ ] 4.2 **openEuler 日志解析器**（§7.2：`tools/diag/logparse.py`）
  - journalctl -k / dmesg / /var/log/messages 三形态；提取 EC/FSC、CPU 号、pc/lr/backtrace、重启记录（last reboot/--list-boots）、EDAC ce/ue、SEL
  - 验证：core179 案例日志（docs/cases/ 下 6 份 vmcore 诊断报告）解析出 100% CPU179 收敛 + 5/6 同指令；pytest
- [ ] 4.3 **七步法 + P/N 规则 + 置信度引擎**（§7.4–7.6：`tools/diag/sdc_diagnose.py`）
  - Step1 Top-N → Step7 FA；P1–P11/N1–N10 判定；四级置信度输出
  - 验证：core179 六案回放 → 高置信度（P1+P5 命中、N3 未命中）；伪造均匀分布日志 → N1 排除；pytest
- [x] 4.4 **§7.7 反哺：单元 P_SDC → 权重先验回填**
  - rules/flight-rules.md v1.0.0 入库（P/N 规则 + 置信度 + 版本变更表）
  - formal 先验回填：fpu 4 位段（t3-1 n=384×4：sign 18.0%/exp 17.2%/mantissa 13.6%/all 15.9%，CI 紧致）+ lsq_fwd ~0.50 + prf ~0.10；诚实边界（非 FIT/SE 限制/单机未确认）
- [x] 4.5 **指纹库 ↔ 诊断引擎 CLI 集成**（`tools/diag/spectrum_triage.py`）
  - 验证实证（端到端）：lsq masks（t7 LOO 同源 64 xor）→ `XOR 0x1ff (mantissa=9 popcount=9) -> lsq_fwd sim=0.712 P_SDC先验=0.50 ★★★★ + 签名检查建议`；综合排序 lsq_fwd 45.574；联动日志侧 `sdc_diagnose: HIGH / P1-P5 / 立即隔离+FA+RMA`——现场位谱→候选单元→诊断规则→日志侧裁决全链路走通
  - UNIT_DIAGNOSTICS 表：unit → P_SDC 先验（formal campaigns）+ §7.3 星级 + 特征日志签名（§7.7 反哺物）

## Phase 5 — 第 8 章建议产出 + CHAOSRAS（维度④）

**Status: pending**

- [x] 5.1 **CHAOSMem `ecc_logic_fault`（E 机理：ECC 逻辑自身故障）**（§5.11）
  - 验证实证（同 seed 同注入对照）：
    - `secded`（正常 ECC）：`EccCorrected (byte reverted)`，old 0x0 → new **0x0**（1-bit 被纠正恢复）
    - `ecc_logic_fault`：`EccLogicFault: Missed (1-bit error NOT corrected — the corrector logic is dead; escapes)`，old 0x0 → new **0x80**（同一 1-bit 错误漏检逃逸——E 机理直接对照实证）
  - numEccLogicMissed 统计 + `--mem_protection_model` choices 扩展；镜像同步
  - 回归：reg_chain golden `f247ef3fe6f02cfd` 不变；构建零错误
- [x] 5.2 **CHAOSRAS 注入器**（S5-2：hook commit-head 异常提交 + ERR* 记录抑制）
  - 注入实证：fault_kernel → `Cycle: 6080, Site: commit_head_ras_record, Mode: ras_escape (ERR* record suppressed), Seq: 3134, SuppressedFault: Generic page table fault`（RAS 记录缺失事件日志化——逃逸可观测）；SVC/系统调用类 fault 排除（SE syscall 机制非 RAS ERR* 语义，v1 全撞 SVC 的教训）
  - 诚实边界（与 CHAOSROB exc_suppress 同边界，progress.md 既有记录）：gem5 SE 下 page fault 在 translation 阶段 panic（不走 DynInst commit 生命周期），完整 DUE→SDC 转化需 FS 模式；本提交交付机制 + 逃逸记录缺失实证
  - 新增 numRasRecordMisses/numSkippedNoFault 统计；arm_chaos.py --chaos_ras 透传
  - 回归：reg_chain golden `f247ef3fe6f02cfd` 不变；构建零错误
- [x] 5.3 **逃逸分解 B–F 数据补齐**（§8.1）
  - t6 表更新：B=secded-b2 n=384 静默（SED 2-bit 不可检，六类标签口径说明）；C=secded-b3 n=384 静默；D=PCE formal 90.9% [87.6,93.4]（既有 n=384 数据回填）；E=ecc_logic_fault 机制对照实证（T5-1，Corrected vs Missed 同 seed 对照）；F=no formal data 诚实标注（需 secded_poison×local_mbu，deferred 带解锁条件）
- [x] 5.4 **§8.2 保护优先级排序表（formal 数据驱动版）**
  - t8-protection-priority.md 入库：8 结构降序（L1D 回填 90.9% > L1D 阵列 97.7%（secded 风险反转 97.7→0）> wrong-source 37.6% > FSU 13.6-18.0% > LSQ 4.7% > PRF > DRAM B/C > DUE 主导组），全部 n=384 CI 标注
  - 四条投资结论：数据通路三件套稳居前三（occupancy 加权稳健）；DUE 主导结构免 SDC 代理保护；SECDED 边界（B/C 静默 + E 自身故障需 BIST）；FP 窄校验可能足够
- [x] 5.5 **§8.3 DFT 向量打包**
  - dft/{manifest.yaml, run_all.sh} 入库：5 向量（m1 RAT 历史残留 / m2 AddrPath byte7（FS 诚实 skip）/ m3 LSQ 位翻转尾数谱 / d1 撕裂移位 rol1 / e ECC 逻辑故障），各带健康/次品签名 + log_marker
  - 端到端批跑实证：baseline golden `f247ef3fe6f02cfd` 一致；m1 `iters=500 fails=1`、m3 `fails=1`、d1 `fails=1`、e 机制 log `EccLogicFault: Missed`——4/4 向量跑出次品签名，0 fail
- [ ] 5.6 **§8.4 N1 TRM Table 9-1 差距分析文档**（E4 项进"待校准清单"不进正文）

## Phase 6 — 论文与收尾（§9）

**Status: pending**

- [ ] 6.1 **论文扩写至五贡献点全覆盖**（§9.1：逐单元量化/F5+F6 模型/protection-aware 规范/生态效度范式/read-trace 四分类）
  - 回填 Phase 3–5 全部新表；数字溯源逐项过
- [ ] 6.2 **诚实边界终审**（§11.3：每 summary 三条边界 + E1–E4 标注 + 不换算 FIT + 单机未确认标注 + 阴性对照如实）
- [ ] 6.3 **方案文档假设表/回填终态 + progress.md 记录 + AGENT_TASKS.md 全勾**

## Phase 7 — 环境门控项登记（不可本机完成，显式不遗漏）

**Status: complete**

- [x] 7.1 S4 系统级（CHAOSCHI/NoC/HCCS）→ deferred 登记（AGENT_TASKS.md `D-S4-系统级`）：~20 补丁独立子项目（E3/E4）；解锁条件：独立排期立项
- [x] 7.2 S6 健康机复现 → deferred 登记（`D-S6-健康机复现`）：需第二台健康鲲鹏机；解锁：硬件到位
- [x] 7.3 S7 实机校准（RAS/EINJ 枚举）→ deferred 登记（`D-S7-实机校准`）：需授权实机（E3/E4→升级）；解锁：实机授权
- [x] 7.4 D10 G7 sanitizer → deferred 登记（`D-D10-G7-sanitizer`）：SConstruct socket configure 环境受阻；解锁：CI 层解决
- [x] 7.5 CHAOSExMon stale_reservation 多核 → deferred 登记（`D-ExMon-多核`）：需多核 SE/FS 配置；解锁：多核配置落地
- [x] 7.6 CHAOSDecode（P4）→ skipped 登记（`D-Decode-P4`）：方案 §5.11 明示"可跳过"
- [x] 7.7 FS O3-switch → **实测一轮后登记**：atomic-only 下 TLB/sysreg/ptw hooks 已验证可分类（Task 1.3 pfn_to_mapped_page → guest Oops 0x9600004f 正常 Kernel-oops exit + Task 1.4 parity 行为可见 + fs_checkpoint 流水线 84M 注入 0 SimulatorError），分类不受 atomic 限制；O3-switch 本身 deferred（stdlib SimpleProcessor 无 clean switchCpus 路径）——`D-FS-O3-switch`

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| （空 — 计划阶段） | | |

## Next Step
Task 1.1 — CHAOSCache tag/valid/dirty/repl/coh 字段级注入（一补丁一单元流程）
