# Task Plan — 鲲鹏920 SDC 方案 100% 覆盖收尾计划

> **Goal**: 对《KUNPENG920SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md》做到**任务级零遗漏**：每个待做项要么完成（含真机验证），要么因环境门控显式登记为 deferred（带原因与解锁条件）。产出维度①②已完成大半，本计划补齐缺口并重点建设维度③（openEuler 诊断引擎）与维度④（芯片设计建议）。
>
> **纪律**（CLAUDE.md）：一补丁一单元 → 三步真机自验证（干净构建 + 功能验证 + 不相关回归）→ commit（无 Co-Authored-By 尾注）→ push `fi-wangxu`。每任务勾选 checkbox 前必须引用真机输出。
>
> 状态图例：`in_progress` / `complete` / `blocked(env)`
> 详细差距依据见 `findings.md`（2026-09-07 盘点）。

## Current Phase
Phase 1（P0-工具补全）— Next Step: Task 1.5 RAT/ROB read-trace API（§4.3/§6.3）

---

## Phase 1 — P0 工具/注入器缺口补全（方案 §5.7/§5.8/§4.3）

**Status: in_progress**

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
- [ ] 1.5 **RAT/ROB read-trace API（H3 跨单元一致性前提）**（§4.3/§6.3）
  - CHAOSRenameMap/CHAOSROB 注入后对目标 physReg 的后续读计数（复用 CHAOSPhysReg 的 ReadTracePoll 范式）
  - 验证：RAT F5 注入后 ReadTrace 行出现且 reads>0；runner 解析 RT_* 列；PRF read-trace 回归不变
- [ ] 1.6 **AGENT_TASKS.md 登记簿建立**（附录 G.1）
  - 按方案 G.1 单行格式登记全部任务（含已完成 18 注入器 + 本计划任务 + deferred 项）
  - 验证：文件入库，格式与方案一致；每完成一任务更新状态

## Phase 2 — kernel 库补全（方案 §5 各 D 段）

**Status: pending**

- [ ] 2.1 **gemm_float / gemm_double**（§5.6D，GEMM popcount 中位 12/28 锚点）
  - 累乘累加矩阵核，native golden 确定；目标：double 位翻转 popcount 分布与 method3 中位 28 可比
  - 验证：native==gem5 golden 一致；F1 注入产出 SDC 且 bit_spectrum.py 可算 popcount
- [ ] 2.2 **svd_iterative + fma_reduction_kernel**（§5.6D）
  - svd 单比特中位 1–3 锚点；fma 归约放大系数
  - 验证：golden 一致 + 注入 SDC 可分类
- [ ] 2.3 **整数对照 kernel：MADD 链 / SMULH / ADDS→B.cond**（§5.10D）
  - 验证：golden 一致；CHAOSExec 位段注入非零计数
- [ ] 2.4 **indirect_jmp / struct_field / crc_state + movbe 正式入库**（§5.9/§5.8/§5.2D）
  - movbe_kernel.c 在 fi_research/probes 已有，入 workloads/directed 并编译验证
  - 验证：各 golden 一致

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

**Status: pending**

- [ ] 4.1 **ESR_ELx EC/FSC 解码器**（§7.3：`tools/diag/esr_decode.py`）
  - EC 0x00/0x20/0x21/0x24/0x25/0x26/0x2F/0x3C → 异常类型 → 相关性权重（★1–5）
  - 验证：`ESR 0x96000044` → DABT/WnR=1/FSC=L0 翻译故障；pytest 用例
- [ ] 4.2 **openEuler 日志解析器**（§7.2：`tools/diag/logparse.py`）
  - journalctl -k / dmesg / /var/log/messages 三形态；提取 EC/FSC、CPU 号、pc/lr/backtrace、重启记录（last reboot/--list-boots）、EDAC ce/ue、SEL
  - 验证：core179 案例日志（docs/cases/ 下 6 份 vmcore 诊断报告）解析出 100% CPU179 收敛 + 5/6 同指令；pytest
- [ ] 4.3 **七步法 + P/N 规则 + 置信度引擎**（§7.4–7.6：`tools/diag/sdc_diagnose.py`）
  - Step1 Top-N → Step7 FA；P1–P11/N1–N10 判定；四级置信度输出
  - 验证：core179 六案回放 → 高置信度（P1+P5 命中、N3 未命中）；伪造均匀分布日志 → N1 排除；pytest
- [ ] 4.4 **§7.7 反哺：单元 P_SDC → 权重先验回填**
  - 用 artifacts/ formal 数据回填 §7.3 权重表的实验依据列；规则版本化（rules/flight-rules.md + version bump）
- [ ] 4.5 **指纹库 ↔ 诊断引擎 CLI 集成**（现场位谱 → Top-K 候选单元 → 关联诊断规则）
  - 验证：t7 LOO 数据走通端到端 CLI

## Phase 5 — 第 8 章建议产出 + CHAOSRAS（维度④）

**Status: pending**

- [ ] 5.1 **CHAOSMem `ecc_logic_fault`（E 机理：ECC 逻辑自身故障）**（§5.11）
  - 验证：注入后 1-bit 错误不被 Corrected（漏检）→ Latent/SDC；≥1 非 Inactive
- [ ] 5.2 **CHAOSRAS 注入器**（S5-2：hook `commit.cc` 异常提交 + ERR* 写路径；模式 = 抑制 ERRID/Disr 记录写入）
  - 验证：注入后 SDC 事件 RAS 记录缺失（模拟 RAS 逃逸）；回归 golden 不变
- [ ] 5.3 **逃逸分解 B–F 数据补齐**（§8.1：PCE formal → D 机理；ecc_logic_fault → E；毒化传播丢失 → F）
  - 更新 t6 表：B–F 有数据或如实标注不可达原因
- [ ] 5.4 **§8.2 保护优先级排序表（formal 数据驱动版）**
  - 用 3.1–3.7 的 P_SDC/P_DUE + §8.1 分解产出排序表；逐结构标代理保护与建议
- [ ] 5.5 **§8.3 DFT 向量打包**
  - method1/2/3 定向 kernel + 触发条件 + 健康/次品签名对照 → `dft/` 目录（manifest + 运行脚本 + 预期签名）
- [ ] 5.6 **§8.4 N1 TRM Table 9-1 差距分析文档**（E4 项进"待校准清单"不进正文）

## Phase 6 — 论文与收尾（§9）

**Status: pending**

- [ ] 6.1 **论文扩写至五贡献点全覆盖**（§9.1：逐单元量化/F5+F6 模型/protection-aware 规范/生态效度范式/read-trace 四分类）
  - 回填 Phase 3–5 全部新表；数字溯源逐项过
- [ ] 6.2 **诚实边界终审**（§11.3：每 summary 三条边界 + E1–E4 标注 + 不换算 FIT + 单机未确认标注 + 阴性对照如实）
- [ ] 6.3 **方案文档假设表/回填终态 + progress.md 记录 + AGENT_TASKS.md 全勾**

## Phase 7 — 环境门控项登记（不可本机完成，显式不遗漏）

**Status: pending**

- [ ] 7.1 S4 系统级（CHAOSCHI/NoC/HCCS，~20 补丁独立子项目，E3/E4）→ 登记 deferred：需独立排期
- [ ] 7.2 S6 健康机复现 → 登记 deferred：需第二台健康鲲鹏机
- [ ] 7.3 S7 实机校准（RAS/EINJ 枚举，E3/E4→升级）→ 登记 deferred：需授权实机
- [ ] 7.4 D10 G7 sanitizer → 登记 deferred：SConstruct socket configure 环境受阻，CI 层解决
- [ ] 7.5 CHAOSExMon stale_reservation 多核场景 → 登记 deferred：需多核 SE/FS 配置
- [ ] 7.6 CHAOSDecode（P4）→ 按方案 §5.11 明示"可跳过"登记跳过
- [ ] 7.7 FS O3-switch（checkpoint restore 后切 O3）→ 登记 deferred 或尝试一轮（若 atomic-only 无法分类则登记）

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| （空 — 计划阶段） | | |

## Next Step
Task 1.1 — CHAOSCache tag/valid/dirty/repl/coh 字段级注入（一补丁一单元流程）
