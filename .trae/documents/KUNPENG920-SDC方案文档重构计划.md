# 计划：重构《KUNPENG920-的SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md》

## 一、总结

在统一分支 `fi-wangxu`（基于 `fi` 创建并合入 `main` 的注入器资产）上，将《KUNPENG920-工程设计.md》（1160 行）与《KUNPENG920-的SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md》（583 行）两份高度重叠的工程设计方案**合并重构为一份权威文档**，并深度集成 `sdc-diagnosis` 项目的《SDC诊断完整方法论.md》（942 行，基于 openEuler 系统日志的 P/N 规则与七步法）。

重构后的文档从四个维度组织：**① 微架构单元 SDC 故障注入研究**（逐单元注入器设计 + campaign 网格 + 验收断言，可指导 AI 开发）；**② SDC 规律研究**（位谱/传播/相位/保护交互规律 + 假设体系）；**③ SDC 诊断建议**（基于 openEuler 系统日志：dmesg/journalctl/SEL/RAS/EDAC → 七步法 → P/N 规则 → 置信度模型，并给出"注入实验→诊断规则反哺"路径）；**④ 对芯片开发设计者的改进建议**（逃逸集合分解、保护优先级排序、DFT 测试向量、位谱指纹库）。

产出为顶级学术研究工作（论文骨架与贡献点）与产业应用工具（SDC 诊断）提供可执行、可验证、诚实的工程蓝图。

## 二、现状分析（Phase 1 实证结论）

### 2.1 分支能力分裂（已核实）

| 能力 | main 分支 | fi 分支 |
|---|---|---|
| 工具链 `tools/runner.py`、`tools/classify.py` | ❌ | ✅（172/248 行） |
| `schemas/manifest.schema.json` | ❌ | ✅ |
| `configs/se/arm_chaos.py`、`arm_chaos_cache.py`、`arm_chaos_fs.py` | ❌ | ✅ |
| `CHAOS/CHAOSArmTLB`（P-D TLB 注入器） | ❌ | ✅ |
| `CHAOS/CHAOSAddrPath`（P-D2，AGU 地址通路） | ✅（93+58+16+4 行） | ❌ |
| `CHAOS/CHAOSPTW`（P-D3，页表走查器） | ✅（127+65+19+4 行） | ❌ |
| `CHAOS/CHAOSLSQFwd` 结构化扩展（P-D1：byte_lane_skew/stale_line_replay/all_zero） | ✅（+102 行） | ❌（仅基础版） |
| `CHAOSReg/CHAOSPhysReg/CHAOSCache/CHAOSMem` | ✅ | ✅ |
| `CHAOS/CHAOSArmSysReg` | ❌ **任何分支都不存在**（文档声称"已有"——不实，须修正） | ❌ |

- merge-base：`46624a7`；main HEAD `c273cfa`（Merge PR #15 fi-h6-h7-fs-verify）；fi HEAD `01c5290`（Merge PR #16 fix/fi-tool-correctness）。
- 两分支变更文件集基本不相交（除 CHAOSLSQFwd），先前已用 `git merge-tree` 验证无冲突（exit 0）。
- 工作树（main 上）：vendored gem5 大量文件呈 `D`（未暂存删除）状态；关键文档为未跟踪（`??`）状态。

### 2.2 文档资产（已核实）

- `docs/KUNPENG920-工程设计.md`（1160 行，未跟踪）— 第 1–7 章 + 附录 A–E：总体约束/微架构画像/故障模型 F1–F6+PCE/注入机制/gem5-fi 对接/任务拆解/验收闸门。
- `docs/KUNPENG920-的SDC...详细方案...md`（583 行，未跟踪）— 第 0–4 部分 + 附录 A–C：现状基线（含不实的 CHAOSArmSysReg "已有"表）/统一实验框架/逐单元设计/执行计划/芯片设计建议。
- `docs/ARM微架构SDC分析与故障注入方案.md`（未跟踪）— 上游风险分析文档，被两份文档引用，保留并入库。
- `docs/ARM64_Kunpeng_SDC_Fault_Injection_Plan.pdf`、`docs/papers/`（14 篇论文）— **fi 分支已跟踪**，与工作树哈希一致（PDF 已核验）。
- `docs/DDI0487M_c_a-profile_architecture_reference_manual/`、`docs/arm_neoverse_n1_trm_100616_0401_02_en/`（未跟踪）— ARM ARM 与 Neoverse N1 TRM 的 markdown 参考资料库。
- `C:\Users\ubuntu\Documents\sdc\sdc-diagnosis\docs\SDC诊断完整方法论.md`（942 行）— 一~十章：SDC 定义/六大数据源/七步法/正向规则 P1–P11/负向规则 N1–N10（含铁律 P1 核浓度、N10 单次阴性不可靠）/置信度模型/NEON-SVE 专项/RAS 集成/PMU 监控/异构适配。
- `sdc-diagnosis/skills/sdc-diagnosis/`：SKILL.md + case_knowledge（case1-25.md，25 个真实案例）+ case_records（28+ 案例日志夹具 dmesg/edac/sel_elist/lscpu）。
- 现场案例：`docs/cases/vmcore-diagnosis-report-*`（core179 六次致命转储深度诊断，含 2026-08-26 第 6 案：88 起事件 100% 收敛 CPU179、5/6 命中同一指令 `find_busiest_group+0x140`、零塌缩/撕裂移位两子族）；`docs/cases/sdc1-01-02-core179-diagnostics/`（method1/2/3 复现）；`docs/cases/core179-microarch-rootcause-synthesis/FI_DESIGN_SUPPLEMENT.md`（H5–H7 假设 + P-D1/D2/D3 设计）。

### 2.3 环境约束

- WSL 曾报错 `Wsl/0x80080005`（上一会话），本会话已验证 **Windows PowerShell 原生 git 可用**（所有核验命令均在 PowerShell 执行成功）。用户偏好 WSL，故执行时先试 WSL、失败即用 PowerShell git。
- CLAUDE.md 纪律：一补丁一单元、提交前真机自验证、自动推送到非 main 分支、commit message 不得以 Co-Authored-By: Claude 结尾。

## 三、实施步骤

### Phase A：分支统一（前置任务，一个独立提交单元）

**A1. 备份未跟踪资产**（防 `checkout -f` 覆盖丢失）：
```powershell
# 备份到仓库外临时目录（PowerShell）
$bk = "C:\Users\ubuntu\Documents\sdc\gem5-fi-backup-docs"
New-Item -ItemType Directory -Force -Path $bk | Out-Null
Copy-Item -Recurse -Force "docs\KUNPENG920-工程设计.md", "docs\KUNPENG920-的SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md", "docs\ARM微架构SDC分析与故障注入方案.md", "docs\DDI0487M_c_a-profile_architecture_reference_manual", "docs\arm_neoverse_n1_trm_100616_0401_02_en", "docs\papers", "docs\ARM64_Kunpeng_SDC_Fault_Injection_Plan.pdf" $bk
# 哈希一致性抽查（PDF 已知一致；papers 若有差异以工作树版为准回补）
git hash-object "docs\ARM64_Kunpeng_SDC_Fault_Injection_Plan.pdf"
git rev-parse "fi:docs/ARM64_Kunpeng_SDC_Fault_Injection_Plan.pdf"
```

**A2. 创建 fi-wangxu 分支并推送**：
```powershell
git checkout -f -b fi-wangxu fi    # -f 丢弃工作树删除状态并恢复被删文件；未跟踪且不在 fi 中的文件（3 份 MD + 2 个参考目录）原样保留
git push -u origin fi-wangxu
```

**A3. 合并 main（带入 P-D1/D2/D3 与案例资产）并推送**：
```powershell
git merge-tree $(git merge-base main fi-wangxu) fi-wangxu main   # 先确认无冲突（预期 exit 0）
git merge main --no-edit
git push origin fi-wangxu
```

**A4. 统一后验证（全部必须为真，否则停下修复）**：
```powershell
git status --short          # 预期：仅 ?? 3 份 MD + 2 个参考目录（DDI0487M、N1 TRM）
Test-Path tools\runner.py, tools\classify.py, schemas\manifest.schema.json, configs\se\arm_chaos_fs.py   # 全 True
Test-Path CHAOS\CHAOSArmTLB, CHAOS\CHAOSAddrPath, CHAOS\CHAOSPTW, CHAOS\CHAOSLSQFwd                     # 全 True
Select-String -Path CHAOS\CHAOSLSQFwd\CHAOSLSQFwd.cc -Pattern "byte_lane_skew|stale_line_replay"        # 命中（P-D1 已并入）
Test-Path docs\cases\vmcore-diagnosis-report-127.0.0.1-2026-08-26-103727   # True（merge 恢复）
Test-Path docs\papers   # True
```

### Phase B：源材料研读（执行者必读清单，重构前完成）

1. 两份被合并文档全文（1160 + 583 行）。
2. `sdc-diagnosis/docs/SDC诊断完整方法论.md` 全文（942 行），重点：二（数据源）、三（七步法）、四/五（P/N 规则）、六（置信度）、七（向量专项）、八（RAS）、九（PMU）。
3. `sdc-diagnosis/skills/sdc-diagnosis/SKILL.md` 与 `case_knowledge/case1-25.md`（诊断规则的操作化形态）。
4. `docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-08-26-103727/...md`（core179 六案综合：方法论落地范本）。
5. `docs/cases/core179-microarch-rootcause-synthesis/FI_DESIGN_SUPPLEMENT.md`（H5–H7 + P-D1/D2/D3 设计依据）。
6. `fi_research/EXPERIMENT_DESIGN.md`、`docs/kunpeng.md`、`docs/cpu/kunpeng.md`（H0–H4 假设、V110 画像）。
7. `docs/papers/` 14 篇论文清单（Veritas/PinDrop/Cross-ISA/SEVI/Hardware Sentinel/Harpocrates/DelayAVF 等——学术定位与规律对照）。
8. 源码抽查（诚实性核对）：`CHAOS/` 下 7+2 个注入器的 `.py/.hh/.cc` 实际参数面与 hook 文件（`CHAOS/gem5/src/cpu/o3/lsq_unit.cc`、`regfile.hh`、`arch/arm/tlb.cc`、`arch/arm/table_walker.cc` 等）行号级核对。

### Phase C：文档重构（核心交付，一个提交单元）

**C1. 新文档结构**（目标约 1800–2400 行，覆盖原两文档全部有效内容）：

```
# 鲲鹏920（TaiShan V110，ARM64）微架构单元 SDC 故障注入与规律研究：方案设计、需求开发与实现文档

第 0 章 文档定位与使用指南（AI 开发者元指令）
  0.1 文档定位（唯一权威源；吸收并取代《KUNPENG920-工程设计.md》）
  0.2 三条强约束（实事求是/可落地/诚实边界）与证据等级 E1–E4
  0.3 分支与基线（fi-wangxu = fi + main 合并；现状以该分支源码为准）
  0.4 如何用本文档驱动 AI 开发（任务卡/验收断言/一补丁一单元纪律）
第 1 章 研究目标与问题定义
  1.1 SDC 定义（三无特征）与真实发生率（Meta/Google/Alibaba/PinDrop 数据）
  1.2 研究目标（逐单元 P_SDC/P_DUE/P_escape/Reachability 量化 + 规律 + 诊断 + 设计建议）
  1.3 现场证据基线：method1（Cholesky 多位混叠）/ method2（欠压→x10 垃圾指针→ESR 0x96000004）/
      method3（LSU 转发相位，尾数 85–93%/符号 0–1）+ core179 六案（100% 单核收敛、同指令、
      零塌缩/撕裂两子族、RAS 全静默）
第 2 章 鲲鹏 920 微架构画像与 SDC 暴露面
  2.1 TaiShan V110 参数表（4-wide OoO/双 FSU/store 转发 6–7cy/L2 TLB 1024/L3 分区 Tag-Data 分离）
  2.2 SDC 暴露面模型与 P0–P3 单元分级（PRF/RAT+freelist/ROB/LSU 转发 = P0）
  2.3 保护覆盖基线（Neoverse N1 TRM Table 9-1 代理 → protectionModel 语义表）
第 3 章 SDC 故障模型定义与分类
  3.1 F1–F6 + PCE 谱系表（定义/源码现状/实现方式）
  3.2 微架构单元 × 故障模型映射矩阵（逐单元小节：画像→机理→模型表）
第 4 章 统一实验框架
  4.1 平台配置族 C0/C1/C2-KP（kp920_proxy 参数块）
  4.2 protection-aware 建模层（none/sed/secded/secded_poison/parity_interleaved）
  4.3 结果分类与分母（九类有序 + read-trace 四分类）
  4.4 campaign driver（tools/campaign.py 规格：网格/种子/Wilson CI/重放冻结）
  4.5 manifest schema v2 扩展（component enum/sub_field/f5_f6_f3 字段/dynamic_context）
  4.6 样本量设计（pilot 100 / formal 384 / 关键 663）
第 5 章 逐微架构单元故障注入设计（每单元固定八段：A 目标与 hook / B 注入器（已有或新写+骨架）/
      C campaign 网格 / D kernel / E 指标与预期规律 / F 建模边界与证据等级 / G 工作量 / H 验收断言）
  5.1 PRF（P0，已有 CHAOSPhysReg 扩展）        5.2 RAT + freelist（P0，新写 CHAOSRenameMap/CHAOSFreeList）
  5.3 ROB（P0，新写 CHAOSROB）                  5.4 LSU 与 store→load 转发（P0，CHAOSLSQFwd 扩展）
  5.5 发射队列 IQ（P1，新写 CHAOSIQ）           5.6 浮点/向量双 FSU（P1，新写 CHAOSFPU）
  5.7 地址翻译 TLB/PTW/系统寄存器（P1，CHAOSArmTLB 扩展 + CHAOSPTW/CHAOSAddrPath cherry-pick + CHAOSArmSysReg 待新写）
  5.8 Cache 子系统 L1/L2/L3（P2/P1，CHAOSCache 扩展 + pairedSector）
  5.9 分支预测器 BPU（P3，新写 CHAOSBPU）       5.10 整数 ALU（P3，新写 CHAOSExec，阴性对照）
  5.11 PCE：L1D 返回通路（新写 CHAOSL1DForward）5.12 独占监视器（新写 CHAOSExMon）
  5.13 系统级 NoC/L3 一致性（S4 长期，CHAOSCHI 代理说明）
第 6 章 SDC 规律研究
  6.1 假设体系 H0–H7（含 core179 扩展：H5 字节相位/H6 地址通路/H7 PTW ECC）→ H8+ 新假设登记
  6.2 位谱规律（FP 尾数主导/符号免疫/popcount 分布；对照 method3 与 SEVI/PinDrop）
  6.3 传播规律（reads_before_overwrite→SDC、暴露面公式验证）
  6.4 相位/时序规律（method3 触发率塌方复现：加 no-op 100%→10–20%）
  6.5 保护交互规律（ECC 前后/poison 传播/post-check escape）
  6.6 跨单元敏感性排序（本实验 vs Veritas/Cross-ISA 论文对照）
  6.7 统计方法（Wilson 95% CI/重放一致性/0-SDC 上界 3/n）
第 7 章 SDC 诊断建议（基于 openEuler 系统日志）
  7.1 诊断目标与范围（鲲鹏 920 + openEuler 22.03/24.03）
  7.2 openEuler 数据源与采集（dmesg/journalctl/rsyslog 格式、SEL via ipmitool/iBMC Redfish、
      rasdaemon+EDAC、GHES/APEI、PMU perf 事件、重启记录）
  7.3 日志解析规则（ESR_ELx EC/FSC 解码表 → 微架构单元映射；异常类型加权表）
  7.4 七步诊断流程（Top-N 筛选/重启异常/RAS 静默/核心浓度/类型加权/维修史/FA 确认，每步附 openEuler 命令）
  7.5 正向规则 P1–P11 与负向规则 N1–N10（铁律 P1 核浓度、N10 单次阴性不可靠；逐条给出日志判据）
  7.6 置信度模型（高/中/低/排除判定树）
  7.7 注入实验 → 诊断反哺（位谱指纹库→日志签名匹配；单元 P_SDC→类型加权；method1/2/3 签名→规则库）
  7.8 实战示例：core179 六案全流程回放（88 事件 100% 收敛、5/6 同指令、RAS 全静默 → P1/P5/P10 命中 → 高置信 → offline+RMA）
  7.9 与 sdc-diagnosis 工具链对接（skill 调用、case_knowledge 扩充、诊断规则版本化）
第 8 章 对芯片开发设计者的改进建议
  8.1 SDC 逃逸集合分解方法（单元 × protectionModel 逃逸贡献饼图）
  8.2 保护优先级排序（暴露面 × 逃逸率 vs 面积/时序代价）
  8.3 分单元设计建议清单（RAT/ROB/PRF 保护策略、L1I SED→SECDED 评估、转发通路校验、
      L2 TLB parity、PTW 读 ECC、TLB 条目保护、fill-buffer 复检）
  8.4 DFT/BIST（method1/2/3 类故障的测试向量与位谱指纹签名）
  8.5 与 Neoverse N1 TRM 保护基线的差距分析
第 9 章 学术研究与产业产出
  9.1 论文骨架与贡献点（ARM64 服务器 CPU 微架构级 SDC 注入+规律+诊断闭环）
  9.2 目标会议（DSN/PRDC/ASPLOS/HPCA/MICRO）与对标论文
  9.3 产业工具（gem5-fi 注入平台 + openEuler SDC 诊断规则引擎 + 指纹库）
第 10 章 分阶段执行计划
  S0 基础设施（campaign.py/schema v2/kp920_proxy 配置/已知缺陷修复：LSQFwd 64 位掩码、ArmTLB 时钟窗口）
  S1 P0 单元（RenameMap/FreeList/ROB/LSQFwd 扩展/PRF F3 触发）
  S2 P1 单元（IQ/FPU/AddrPath+PTW cherry-pick 补闸门/ArmTLB pfn_to_mapped_page/ArmSysReg 新写/L3 pairedSector）
  S3 P2/P3 单元（Exec/BPU/L1DForward/ExMon/CHI 代理）
  S4 元分析与交付（逃逸集合分解/指纹库/论文/工具）
  每任务：依赖排序 + 机器可判验收断言 + 工作量（补丁数）
第 11 章 质量闸门与验证纪律（G0–G7 现状表 + 一补丁一单元 + 自验证三步 + 诚实边界声明）
附录 A 注入器与 hook 点总表（源码核对版）
附录 B 现场案例对照实验索引（method1/2/3 + core179 六案 ↔ 注入 cell）
附录 C 鲲鹏 920 微架构参数 → gem5 配置映射表
附录 D 现有实现已知缺陷清单（源码分析发现，须修复）
附录 E openEuler 日志字段与诊断规则映射表（ESR/SEL/EDAC/rasdaemon 字段 → P/N 规则）
附录 F 术语表
```

**C2. 内容合并映射**（工程设计.md → 新文档，消除重复后删除原文件）：

| 工程设计.md 来源 | 去向 |
|---|---|
| 第 1 章总体约束/证据等级 | 第 0、1 章 |
| 第 2 章画像/暴露面/保护基线/三案例 | 第 1、2 章 |
| 第 3 章故障模型 F1–F6+PCE 与逐单元矩阵 | 第 3 章 + 第 5 章各单元 E 段 |
| 第 4 章注入机制（触发/注入点/时序） | 第 5 章各单元 A/B 段 |
| 第 5 章gem5-fi 框架对接 | 第 4 章 |
| 第 6 章任务拆解/依赖/验收 | 第 10 章 |
| 第 7 章统一验收与质量闸门 | 第 11 章 |
| 附录 A hook 总表 / B 案例索引 / C 参数映射 / D 缺陷清单 / E 术语表 | 附录 A–F |

原目标文档（583 行）的第 0 部分（现状基线，修正后）、第 1 部分（实验框架）、第 2 部分（逐单元）、第 3 部分（执行计划）、第 4 部分（芯片建议）、附录 A–C 同构并入；**第 7、8、9 章为本次重构新增维度**（诊断/openEuler/学术产出在旧两文档中缺失或极薄）。

**C3. 诚实性修正清单**（必须逐项落实）：

1. `CHAOSArmSysReg`：两文档均称"已有 + FS 真机验证"，但**任何分支都不存在**→ 全部改为"待新写"，历史验证描述删除或注明"历史会话曾验证但代码未入任何分支，须重写并复验"（执行时查 `progress.md` 是否留有记录）。
2. 注入器状态表以 **fi-wangxu 合并后**的实际源码为准：合并后 CHAOSAddrPath/CHAOSPTW/结构化 CHAOSLSQFwd 从"分支原型，需 cherry-pick"升级为"已在 fi-wangxu，需补闸门纪律（G0–G7 复检）"。
3. `fi` 分支注入器数量表述：合并后为 9 个（7 基础 + AddrPath + PTW），逐一给出真实路径与 hook 行号（源码抽查核对）。
4. 已知缺陷如实保留：CHAOSLSQFwd `faultMask` 仍 32 位/单字节限制、CHAOSArmTLB 时钟窗口 advisory、G6/G7 未完成项。
5. gem5 边界声明：O3 ≠ V110 RTL、SE 无 MMU-on 翻译（地址通路/PTW 必须 FS）、无 bufferless NoC/HCCS/周期精确 L3。

**C4. 第 7 章（openEuler 诊断）设计要点**（用户明确要求的核心维度）：

- 所有方法、规则、命令**必须锚定 openEuler 日志形态**：`/var/log/messages` 与 dmesg 时间戳格式、`journalctl -k` 输出、openEuler 对 spurious 翻译故障的 `WARN` 记录行为（core179 案例实证：`ESR 0x96000044` WnR=1+FSC=L0 重复 WARN）、iBMC SEL、rasdaemon/EDAC 在鲲鹏上的实际静默表现（ghes_edac 注册 32 DIMM 零 CE/UE、rasnode.ko 192 核×5 ERR 节点全零差异——RAS 静默的铁证）。
- P/N 规则逐条给出"日志判据 + openEuler 命令"二元组（如 P1 核浓度：`journalctl -k | grep -E 'ESR|Data Abort|Oops'` + 按 CPU 号聚合的集中度检验；P5 RAS 静默：`ipmitool sel elist` + `/sys/devices/system/edac/mc/mc*/ce_count` 全零 + rasdaemon 零记录）。
- 7.8 实战回放直接采用六案 vmcore 报告的真实数据（88 事件 100% CPU179、5/6 同指令、撕裂/零塌缩子族 FSC 二分法 L0/L3、反事实验证法），作为方法论的最强落地证据。

### Phase D：旧文档处理与提交（遵循一补丁一单元）

**D1. 删除已吸收的《KUNPENG920-工程设计.md》**（未跟踪文件，直接 `DeleteFile`；其全部有效内容已进入新文档，新文档第 0.1 节声明取代关系）。

**D2. 提交（两个提交单元，均验证后自动推送）**：
- 提交 1（Phase A 的 merge commit 已含）：分支统一。
- 提交 2：文档重构。
  ```powershell
  git add "docs/KUNPENG920-的SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md" "docs/ARM微架构SDC分析与故障注入方案.md" "docs/DDI0487M_c_a-profile_architecture_reference_manual" "docs/arm_neoverse_n1_trm_100616_0401_02_en"
  git commit -m "docs: 重构KUNPENG920 SDC方案文档——吸收工程设计.md，新增openEuler诊断与芯片设计建议维度"
  git push origin fi-wangxu
  ```
  （commit message 不以 Co-Authored-By: Claude 结尾。）

### Phase E：验证（提交前强制，100% 真实命令）

1. **源码一致性核对（诚实性）**：对新文档中每个标注"已有"的注入器/工具，逐一 `Test-Path` + `Select-String` 关键参数名（Renamemap 不存在、AddrPath/PTW 存在、ArmSysReg 标"待新写"）；抽查 ≥5 处 hook 行号（如 `lsq_unit.cc` 的 lsqFwd hook、`tlb.cc` 的 chaosTLB hook、`table_walker.cc` 的 doLongDescriptor）与文档引用一致。
2. **交叉引用检查**：文档内引用的文件路径全部存在（docs/、CHAOS/、tools/、configs/、sdc-diagnosis 路径）；内部章节锚点编号连续无断链。
3. **诊断规则一致性**：新文档第 7 章的 P/N 规则编号、铁律标注、置信度分级与《SDC诊断完整方法论.md》原文一致（逐条 grep 比对规则标题）。
4. **回归**：`git status` 干净（除计划内未跟踪项）；`git log fi-wangxu -5 --oneline` 显示 merge + docs 两个提交；`git push` 成功。
5. **交付确认**：新文档行数 ≥1800；旧《KUNPENG920-工程设计.md》已不存在于工作树与分支。

## 四、假设与决策

1. **分支策略**：fi-wangxu 基于 fi 创建后**立即合并 main**（用户指出的能力分裂必须先统一，否则文档"现状基线"无单一事实源）；merge-tree 已验证无冲突。
2. **旧文档处置**：内容吸收后**删除**《KUNPENG920-工程设计.md》，新文档成为唯一权威源（用户已确认合并消除冗余）。
3. **git 环境**：优先 WSL（用户偏好），WSL 不可用（0x80080005）则用本会话已验证可用的 PowerShell 原生 git。
4. **诊断口径**：第 7 章全部以 openEuler 系统日志为数据源（用户明确要求）；sdc-diagnosis 方法论作为规则库引用而非重写，两文档通过 7.9 节对接。
5. **参考资料入库**：ARM微架构SDC分析.md（上游引用）与 DDI0487M/N1 TRM markdown 参考库随重构提交入库（它们是新文档保护模型与 ISA 依据的自包含来源）；`docs/papers` 与 PDF 已在 fi 中跟踪，无需重复提交。
6. **范围边界**：本任务交付**文档与分支统一**；注入器代码开发（CHAOSRenameMap/ROB/IQ/FPU/ArmSysReg 等）是文档第 10 章规划的后续执行单元，本次不实现。
7. **文档语言**：中文（与现有文档一致），代码/命令保留英文。

## 五、验证步骤汇总（执行完成标准）

- [ ] fi-wangxu 分支存在且已推送，包含两分支全部资产（tools/schemas/configs/CHAOSArmTLB/CHAOSAddrPath/CHAOSPTW/结构化LSQFwd/全部案例文档）
- [ ] 重构文档 ≥1800 行，四维度（注入研究/规律研究/诊断建议/芯片建议）完整成章
- [ ] 每条"已有"能力声明经源码核验为真；CHAOSArmSysReg 等不实标注全部修正
- [ ] 第 7 章规则与《SDC诊断完整方法论.md》逐条一致且全部锚定 openEuler 日志命令
- [ ] 《KUNPENG920-工程设计.md》已删除，无内容丢失（备份目录留存）
- [ ] 两个提交（merge + docs）已推送 fi-wangxu，git status 干净
