# Findings — 2026-09-07 方案全覆盖差距盘点

> 依据：《KUNPENG920SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md》（1069 行，下称"方案"）
> 方法：逐章核对 `fi-wangxu` HEAD（`ebae0eb3`）实际源码 / artifacts / tools，区分"已完成（有实证）"与"待做"。
> 用途：支撑 `docs/superpowers/plans/2026-09-07-kunpeng920-sdc-complete-coverage.md` 的任务分解，确保无遗漏。

## 1. 已完成且仓库内有实证的项（不在新计划中重复）

| 方案条目 | 实证（仓库内） |
|---|---|
| 18 个注入器（§5 各单元 B 段） | `CHAOS/CHAOS{Reg,PhysReg,Cache,Mem,LSQFwd,ArmTLB,AddrPath,PTW,RenameMap,FreeList,ROB,IQ,FPU,Exec,L1DForward,BPU,ExMon,ArmSysReg}`，vendored 副本齐全（`CHAOS/gem5/src/...` 18 处目录核对） |
| F1–F6 + PCE 全故障模型（§3.1） | F3（`7f538c4`）、F5（RAT/freelist/LSQ/TLB pfnOffset/SysReg value_to_legal/Mem addr_map_sub）、F6（LSQFwd phaseOffset + IQ wake_omit/wake_phase `8850fa66`）、PCE（CHAOSL1DForward `1bb18f0`） |
| 附录 D 缺陷 D1–D7 | `0ae28fe`（D2）、`56023c3`（D1+D5+D6）、`58be899`（D4+D5）、`4ed645b`（D3）；D7 mask==0 早退在 8 个注入器 .cc 中核对存在 |
| campaign/runner/classify 九类 + Wilson + manifest v2 | `tools/campaign.py`（并行+双层超时组杀）、`tools/runner.py`（v2 字段、read-trace、fail_count oracle、PA 分类）、`tools/classify.py` |
| protectionModel ECC 后处理（§4.2） | CHAOSCache `applyProtectionModel()` + CHAOSMem secded；`artifacts/l1d-ecc/`（n=384×6：raw-b1/b2/b3 vs secded-b1/b2/b3，1-bit Corrected / 2-bit 含毒化） |
| kp920_proxy 配置（§4.1） | `configs/se/arm_chaos.py`（--kp920_proxy）+ `arm_chaos_fs.py:54` |
| FS checkpoint 流水线（§10.2） | `configs/se/fs_checkpoint.py`（boot 890s → restore 注入，`c82e59a`） |
| kernel 库（部分） | workloads/directed 21 个：reg_chain/l1d_reduce/l1i_loop/neon_lane/fp_fwd_kernel/cholesky_numeric(±both)/accum_kernel(±both)/ptr_chase/fwd_7case×7/branchy_leak/call_ret_heavy/dep_chain/exmon_kernel/fault_kernel |
| formal 结果（部分） | PRF X3 位段 n=96×8（`artifacts/prf-formal`）；LSQ 5 模式 n=64×5（`artifacts/lsq-matrix`）；method1 Fisher n=384×2（`artifacts/m1-formal-*`，p=1.189e-71 PASS）；L1D ECC n=384×6；H1 read-trace n=384×4（P(SDC\|reads>0)=1.000）；H2 窗口扫描 n=96×12（天花板效应诚实标注） |
| §8.1 逃逸分解工具 | `tools/escape_decomp.py` + `docs/paper/tables/t6-escape-decomp.md`（A 机理 3282 事件 100%；B–F no data 如实标注） |
| §8.3 指纹库 + LOO | `tools/sdc_fingerprint.py` + `tools/loo_validate.py` + t7（76 事件 Top-3 100% ≥60% VALID） |
| H5/H6/H7 闭环（§6.1） | main 分支已闭环（方案 6.1 表标"已闭环"） |
| CHAOSROB spec_leak | `5502276`（doSquash hook，branchy_leak numSpecLeak=3） |
| 论文初稿 | `docs/paper/sdc-fi-paper.md`（125 行，8 章）+ tables t1–t7 |
| x86 配对（C1 前置） | `configs/se/x86_chaos.py` + reg_chain_x86（directed RAX/RCX，`46ddf78`+修正） |

## 2. 待做缺口（新计划的任务来源，逐条对应方案章节）

### 2.1 注入器/工具缺口
- **§5.8B CHAOSCache targetField**：现仅 `data` + L1I 语义字段（rd/rn/rm/opcode，`CHAOSCache.cc:347-381`）；**tag/valid/dirty/repl/coh 字段级未实现**；**victim（`base.cc WritebackBlk` hook）未实现**。
- **§5.7B CHAOSArmTLB**：`pfnOffset`（F5 偏移→DUE 方向）已有；**`pfn_to_mapped_page`（翻到另一活页→静默 SDC，最危险路径）未实现**；iTLB 挂载、L2 TLB、`protectionModel` 参数未实现（`CHAOSArmTLB.py` 无该参数，核对 2026-09-07）。
- **§5.11/S5-2 CHAOSRAS**：注入器未写（分析半边 escape_decomp.py 已有，注入半边缺）。
- **§5.9 CHAOSBPU**：hook 在 `BAC::predict`，但 **decoupledFrontEnd 与 stdlib board 不兼容（空 stats 实测）→ 当前不可用**；联合观测 `P(squash 后架构态==golden)` 未做。
- **§4.3/§6.3 H3 跨单元 read-trace**：ReadTrace 仅 CHAOSPhysReg 有；**RAT/ROB 无 read-trace API**（`CHAOSRenameMap/*.cc`、`CHAOSROB/*.cc` grep 无 ReadTrace）。
- **D9（G6 广触发）**：pc/committedInst/event 触发模式未实现。
- **§4.5 manifest dynamic_context**：mapped_phys_reg/freelist_size/cache_residency/lsq_source_seq/tlb_asid/committed_inst_at_inject 未落。
- **§5.4 CHAOSExMon stale_reservation**：单线程 SE 不可达（需多核场景），诚实标注待做。

### 2.2 kernel 缺口（§5 各 D 段）
- **§5.6D**：gemm_float/gemm_double（GEMM popcount 中位 12/28 锚点）、svd_iterative（单比特中位 1–3）、fma_reduction_kernel。
- **§5.10D**：MADD 链、SMULH、ADDS→B.cond 条件链、整数 reduction、indirect_jmp。
- **§5.2D 对照组**：pure_fma/pure_spmv/pure_gather/tri_solve、movbe_kernel（在 fi_research/probes 有 .c 但未入 workloads/directed 正式库）。
- **§5.8D**：struct_field_kernel、crc_state_kernel。

### 2.3 formal campaign 缺口（§4.6 n=384 标准）
- PRF formal 现 n=96/cell（方案要求 384；关键 cell 663）。
- **§5.6 FSU**：CHAOSFPU 机制就位但 **零 formal 数据**（neon_lane FP 头稀少 REJECT 超时）；向量 PRF vs FSU 通路 KS 检验未做。
- **§5.10 Exec 阴性对照 formal**：`P_SDC(Int) << P_SDC(FSU/转发)` 未正式量化。
- **§5.8**：字段级×protection formal、L2 size sweep {256KiB,512KiB,1MiB}（H4）、L1I SED vs SECDED 两组差、PCE vs raw 对比。
- **§5.7 FS formal**：checkpoint 后 TLB pfn→活页 P_SDC / pfn→未映射 P_DUE + ESR DFSC vs `0x96000004`、PTW ptwEcc on/off（H7 formal）、SysReg 白名单 cell。
- **§5.2/5.3 formal**：RAT/freelist/ROB（P_SDC vs 距提交距离 D 曲线、exc_suppress DUE→SDC 转化率、损坏 popcount 中位 >16）。
- **附录 B method2 三根因区分**：PRF/AGU/TLB 三种注入的 ESR/PC/x10 形态比对打分（现仅 SimulatorError≈method2 野指针形态的定性注记）。
- **§6.4/§8.3.3**：F3/F6 相位敏感性曲线（method3 塌方比 ≥5×、三必要条件去一归零）、电压/相位数据。

### 2.4 第 7 章 openEuler 诊断引擎（维度③，整体缺）
- `tools/` 无任何 ESR 解码/journalctl 解析/七步法 CLI（grep journalctl|dmesg 零命中）。
- `sdc-diagnosis` 项目**本机不存在**（find /home/sdc 无此目录）→ 规则引擎需在本仓库自建（方案 7.9 说"引用而非重写"，但载体缺失时以方案第 7 章为规范源自建并标注）。
- core179 六案回放（P1+P5+N3→高置信度）未做工具化验证。
- §7.7 反哺（单元 P_SDC→权重先验、method 签名→规则库版本化）未做。

### 2.5 第 8 章建议产出（维度④）
- §8.1 逃逸分解 B–F 机理无数据（需 PCE formal→D、ecc_logic_fault→E/F）。
- §8.2 保护优先级排序表（formal 数据驱动版）未产出。
- §8.3 DFT 向量打包（method1/2/3 kernel+触发条件+健康/次品签名对照）未产出。
- §8.4 N1 TRM Table 9-1 差距分析未产出。

### 2.6 论文/登记（§9、附录 G）
- 论文 125 行初稿，未达 §9.1 五贡献点全覆盖。
- **AGENT_TASKS.md 不存在**（方案 G.1 要求的单行登记簿）。
- 方案 §6.1 假设表 H0/H3/H4/H8+ 未回填 formal 判定（H1/H2 已回填）。

### 2.7 环境门控项（不可在本机完成，须显式登记不遗漏）
- S4 系统级 CHAOSCHI/CHAOSNoC/CHAOSHCCS（~20 补丁独立子项目，E3/E4）。
- S6 健康机复现（需第二台健康鲲鹏机）。
- S7 实机校准（需授权实机）。
- D10（G7 ASan/UBSan，SConstruct socket configure 环境受阻，deferred CI）。
- CHAOSDecode（P4，方案 §5.11 明示"低优先级，可跳过"）。

## 3. 关键运行事实（复用）

- 构建产物陷阱：`scons -C CHAOS/gem5` 产物落仓库根 `build/ARM/gem5.opt`，须 cp 回 `CHAOS/gem5/build/ARM/`（memory 已记）。
- campaign 与构建绝不并行（H1 首跑作废教训）。
- `-j16` 上限（29GB 主机 OOM）。
- FS checkpoint：`configs/se/fs_checkpoint.py`，restore 后 Atomic（O3-switch 待续）。
