# 鲲鹏920 SDC 方案 100% 覆盖收尾计划（2026-09-07）

> **源文档**：《KUNPENG920SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md》（docs/，1069 行，"方案"）
> **Goal**: 任务级零遗漏——每个待做项要么完成（含真机验证），要么因环境门控显式登记 deferred（带原因与解锁条件）。
> **纪律**（CLAUDE.md）：一补丁一单元 → 三步真机自验证（干净构建 + 功能验证 + 不相关回归）→ commit（无 Co-Authored-By 尾注）→ push `fi-wangxu`。每任务勾选 checkbox 前必须引用真机输出。
> 差距盘点依据：仓库根 `findings.md`（2026-09-07，逐项核对 fi-wangxu HEAD `ebae0eb3` 源码/artifacts）。

## 背景快照（已完成，不在本计划重复）

- 18 注入器、F1–F6+PCE 全模型、D1–D7 修复、campaign/runner/classify 九类、protectionModel ECC、kp920_proxy、FS checkpoint 流水线、21 kernel、x86 配对前置
- formal：PRF X3(96×8)、LSQ 5 模式(64×5)、method1 Fisher(384×2 PASS p=1.189e-71)、L1D ECC(384×6)、H1 read-trace(384×4)、H2 窗口(96×12)
- §8.1 逃逸分解（A 机理 100%）、§8.3 指纹库+LOO（Top-3 100% VALID）、H5/H6/H7 闭环、论文初稿 125 行 + t1–t7

---

## Phase 1 — P0 工具/注入器缺口补全（方案 §5.7/§5.8/§4.3）

- [ ] 1.1 **CHAOSCache tag/valid/dirty/repl/coh 字段级注入**（§5.8B）
  - targetField ∈ {data,tag,valid,dirty,repl,coh}（现仅 data + L1I 语义 rd/rn/rm/opcode）；tag 走 `getTags()`；valid/dirty 改 `CacheBlk` 标志
  - 文件：`CHAOS/CHAOSCache/CHAOSCache.{py,hh,cc}` + vendored 同步（cp 后 make 双向核对）
  - 验证：各字段 ≥1 注入日志行（`Field: tag` 等）；prob=0 回归 golden 不变；构建零警告
- [ ] 1.2 **CHAOSCache victim 注入**（§5.8A，hook `mem/cache/base.cc` WritebackBlk）
  - targetField=victim：writeback 路径破坏写回数据
  - 验证：victim 注入日志 + ≥1 非 Inactive；回归同上
- [ ] 1.3 **CHAOSArmTLB `pfn_to_mapped_page`（F5→活页，最危险静默 SDC 路径）**（§5.7B）
  - 从当前 TLB 活动条目集合选另一活页 pfn（合法域校验）
  - 验证：FS checkpoint 流水线 ≥1 注入且 new_pfn ∈ 活页集合；合法域 ≥1000 次 0 SimulatorError
- [ ] 1.4 **CHAOSArmTLB iTLB 挂载 + protectionModel**（§5.7B；§2.3 L1 TLB=none / L2 TLB=parity_interleaved）
  - `arm_chaos_fs.py` 加 `--chaos_armtlb_itlb`；`protectionModel ∈ {none,parity_interleaved}`
  - 验证：FS iTLB 注入 ≥1；parity 1-bit → 条目失效重走行为可见
- [ ] 1.5 **RAT/ROB read-trace API（H3 前提）**（§4.3/§6.3）
  - 复用 CHAOSPhysReg ReadTracePoll 范式；runner 解析 RT_* 列
  - 验证：RAT F5 后 ReadTrace 行 reads>0；PRF read-trace 回归不变
- [ ] 1.6 **AGENT_TASKS.md 登记簿**（附录 G.1 单行格式，含已完成 18 注入器 + 本计划任务 + deferred 项）

## Phase 2 — kernel 库补全（方案 §5 各 D 段）

- [ ] 2.1 gemm_float/gemm_double（§5.6D，popcount 中位 12/28 锚点）— golden 一致 + 注入 SDC + bit_spectrum 可算
- [ ] 2.2 svd_iterative + fma_reduction_kernel（§5.6D 单比特中位 1–3 / 归约放大）
- [ ] 2.3 MADD 链 / SMULH / ADDS→B.cond（§5.10D 整数对照）
- [ ] 2.4 indirect_jmp / struct_field / crc_state + movbe 正式入库（§5.9/§5.8/§5.2D；movbe.c 在 fi_research/probes）

## Phase 3 — formal campaign 批量补齐（§4.6：pilot n=100 / formal n=384 / 关键 663）

- [ ] 3.1 FSU formal（位段×算子×精度；位谱对标 method3 85–93%/0–1/中位 3~28；PRF-vec vs FSU KS 检验）
- [ ] 3.2 Exec 阴性对照 formal（`P_SDC(Int) << P_SDC(FSU/转发)` 量化）
- [ ] 3.3 RAT/freelist/ROB formal（P_SDC vs 距提交距离 D 曲线；exc_suppress DUE→SDC 转化率；popcount 中位 >16）
- [ ] 3.4 Cache 字段级×protection formal + L2 size sweep {256K,512K,1M}（H4）+ L1I SED vs SECDED
- [ ] 3.5 PCE vs raw 对比 formal（CHAOSL1DForward P_SDC 显著高于 raw）
- [ ] 3.6 FS formal：TLB pfn→活页 P_SDC / pfn→未映射 P_DUE + ESR DFSC vs `0x96000004`；PTW ptwEcc on/off（H7 formal）；SysReg 白名单 cell
- [ ] 3.7 PRF formal 补样 96→384（8 cell × 增量 288，seed 前缀一致）
- [ ] 3.8 method2 三根因区分（PRF/AGU/TLB 注入的 ESR/PC/x10 形态比对打分表，附录 B）
- [ ] 3.9 F3/F6 相位敏感性曲线（|phaseOffset|≥1 vs 0 比值 ≥5×；method3 三必要条件去一归零对照）
- [ ] 3.10 假设表 H0/H3/H4/H8+ 回填（联动 3.1–3.9 更新方案文档 §6.1）

## Phase 4 — 第 7 章 openEuler 诊断引擎（维度③，整体新建；sdc-diagnosis 项目本机不存在 → 以方案第 7 章为规范源自建并标注）

- [ ] 4.1 ESR_ELx EC/FSC 解码器 `tools/diag/esr_decode.py`（§7.3 权重表；`0x96000044` → DABT/WnR=1/FSC=L0；pytest）
- [ ] 4.2 openEuler 日志解析器 `tools/diag/logparse.py`（§7.2：journalctl/dmesg/messages 三形态；EC/FSC、CPU 号、backtrace、重启、EDAC、SEL；core179 六案解析 100% CPU179 收敛验证）
- [ ] 4.3 七步法 + P/N 规则 + 置信度引擎 `tools/diag/sdc_diagnose.py`（§7.4–7.6；core179 回放 → 高置信度；均匀分布 → N1 排除；pytest）
- [ ] 4.4 §7.7 反哺：单元 P_SDC → §7.3 权重先验回填 + 规则版本化（rules/flight-rules.md bump）
- [ ] 4.5 指纹库 ↔ 诊断引擎 CLI 集成（现场位谱 → Top-K 候选 → 关联规则；t7 数据端到端）

## Phase 5 — 第 8 章建议产出 + CHAOSRAS（维度④）

- [ ] 5.1 CHAOSMem `ecc_logic_fault`（E 机理：ECC 逻辑漏检 → Latent/SDC；≥1 非 Inactive）
- [ ] 5.2 CHAOSRAS 注入器（S5-2：hook commit.cc 异常提交 + ERR* 写路径，抑制记录写入；回归 golden 不变）
- [ ] 5.3 逃逸分解 B–F 数据补齐（PCE formal→D；ecc_logic_fault→E；毒化丢失→F；更新 t6）
- [ ] 5.4 §8.2 保护优先级排序表（formal 数据驱动版，逐结构标代理保护与建议）
- [ ] 5.5 §8.3 DFT 向量打包（method1/2/3 kernel + 触发条件 + 健康/次品签名对照 → `dft/` 目录）
- [ ] 5.6 §8.4 N1 TRM Table 9-1 差距分析文档（E4 进待校准清单不进正文）

## Phase 6 — 论文与收尾（§9）

- [ ] 6.1 论文扩写至 §9.1 五贡献点全覆盖（回填 Phase 3–5 新表；数字溯源逐项过）
- [ ] 6.2 诚实边界终审（§11.3 五条：E1–E4 标注/三边界复述/不换算 FIT/单机未确认/阴性如实）
- [ ] 6.3 方案文档假设表终态 + progress.md 记录 + AGENT_TASKS.md 全勾

## Phase 7 — 环境门控项登记（不可本机完成，显式登记防遗漏）

- [ ] 7.1 S4 系统级 CHAOSCHI/NoC/HCCS → deferred（独立子项目，E3/E4）
- [ ] 7.2 S6 健康机复现 → deferred（需第二台健康鲲鹏机）
- [ ] 7.3 S7 实机校准 → deferred（需授权实机）
- [ ] 7.4 D10 G7 sanitizer → deferred（SConstruct socket configure 环境受阻，CI 层）
- [ ] 7.5 CHAOSExMon stale_reservation → deferred（需多核场景）
- [ ] 7.6 CHAOSDecode（P4）→ 方案 §5.11 明示可跳过，登记跳过
- [ ] 7.7 FS O3-switch → 尝试一轮；若 atomic-only 无法分类则登记 deferred

---

## 执行纪律备忘（本仓特有，来自 memory/progress 教训）

- scons 产物落仓库根 `build/ARM/gem5.opt` → 构建后必须 cp 到 `CHAOS/gem5/build/ARM/`
- campaign 与构建绝不并行（gem5.opt 被替换 → cell 行为分裂 → 数据作废）
- `-j16` 上限（29GB 主机 -j126 OOM）
- outdir 放 `runs/` 不放 /tmp（ENOSPC）
- 修改 `CHAOS/CHAOS*` 顶层副本后核对 vendored 同步（Makefile sync_chaos 只覆盖 4 个旧注入器，其余手动 diff）
