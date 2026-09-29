# LSU 故障注入方案 V2.0 原位重锚 — 设计文档（spec）

- **日期**：2026-09-29
- **状态**：设计已经用户逐节确认（五项决策见 §2.2；D5 为 2026-09-29 对齐 OoO 先例增补）
- **落地分支**：`fi-ding`（非 main），逐单元提交 + 推送，绝不 `git add -A`
- **本文作用**：定义"如何把 `docs/gem5-fi/lsu/` 从 V1.0 口径重锚到 V2.0"——它是后续 `superpowers:writing-plans` 实现计划的唯一输入；重锚完成后仓库内容的权威链见 §2.1

---

## 1. 背景与目标

`docs/gem5-fi/lsu/` 现有 16 文件交付（00–08 转录 + 2 CSV + extract.py/verify_extraction.py + 09 实施总纲 + 10/11 试跑结果，2026-09-24 起从 **V1.0** xlsx 机械提取，三重验证链闭合）。2026-09-28 到达 **V2.0 xlsx（重大更新）**，仓库已在 HEAD `c6e07fa6`（"PAUSED for V1.0→V2.0 plan upgrade"）暂停等待本升级。

**目标**：以 V2.0 为唯一权威，原位重锚整个目录为——面向 ARM LSU 微架构单元故障注入的**项目北极星 + 完整实现方案 + 研究与实验宏伟计划**。

**本交付边界**：文档层（含提取机器 extract.py / verify_extraction.py 自身的 V2.0 化）。源码与工具改动（lsu_campaign 325 格、classify 新分类学、子模型上报等）是 09-v2 宏伟计划 V2-W0..V2-W9 各工作包的**执行内容**，另行计划，不在本交付内。

## 2. 裁决规则

### 2.1 权威链（重锚后生效）

1. **V2.0 xlsx**（用户指令 2026-09-28："V2.0 是 V1.0 的重大更新版本，一切以 V2.0 为准"）
2. 转录层 00–08（V2.0 的忠实提取，sha 钉死 + 逐格可验）
3. 计划层 09-v2（实现方案，冲突时让位于上两层）

### 2.2 已确认的四项设计决策

| # | 决策 | 选择 |
|---|---|---|
| D1 | 交付形式 | **原位重锚**（git 历史保全 V1.0；无版本并存漂移） |
| D2 | 北极星形态 | **新建 NORTH-STAR.md**（顶层文档，README 首链） |
| D3 | 09 W 系列重排 | **全新编号 + V1.0 遗产映射表**（V2.0 语义重心从"建注入器"转向"新分类学+完整网格回填"） |
| D4 | V2.0 内部不一致（表3 col10 vs 表7 col12，AGU 系 8 模型 39 格措辞不同步） | **表7 为执行权威**；表3 照实转录旧文 + 提取注记标明差异与裁决理由，不替作者改源表 |
| D5 | 跨轨约定（2026-09-29 增补） | **对齐 OoO 轨道 V2.0 先例（3412c1bc）**：新建 `09-implementation-plan-v2.md` 为现行计划、旧 09 加"已被 V2.0 接替"横幅封存；编号 `V2-W0..V2-W9`、里程碑 `M0'–M6'`；转录层 00–08 仍机器再生不变 |

### 2.3 沿用规则（自 09 v1 §6 继承，未被 V2.0 推翻）

- 机制核实一律以本仓 vendored gem5 v25.1.0.1 为准（xlsx 核对基于上游 stable）；
- 预期结果是可证伪假设；blocked/不适用格如实标注，**不填零**；
- 统一用模型 ID / RunID，不发明新编号；工作包编号带 `V2-` 前缀（与负载 W#（06 表 W0–W13）的同形冲突由前缀消解）；
- 三轨道（LSU / OoO / 鲲鹏920）口径严禁混算。

## 3. 总体架构：五层文档体系

```
docs/gem5-fi/lsu/
├── README.md                  索引层：V2.0 口径导航 + 验证链 + 历史层说明
├── NORTH-STAR.md              北极星层（新建）：使命/口径/现状/目标/路线/裁决链
├── 00-overview.md … 08-references.md + design-matrix.csv + 07-expanded-matrix.csv
│                              转录层：V2.0 机械重提取（sha 钉死、逐格可验）
├── 09-implementation-plan-v2.md  计划层（现行）：V2.0 宏伟计划（V2-W0..V2-W9 + M0'–M6'，新建）
├── 09-implementation-plan.md     计划层（封存）：V1.0 轮计划，顶部加"已被 V2.0 接替"横幅
└── 10-trial-results.md / 11-meta-analysis.md
                               历史层：V1.0 试跑轮遗产，顶部加历史标注保留
```

设计原则（沿用现有交付的成功结构）：**转录层 = 忠实提取（机器生成、verify 逐格回比），综合判断只出现在北极星层与计划层，两层不混**。

## 4. 转录层重提取规格

### 4.1 源与硬钉

- 源：`docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案V2.0.xlsx`
  - sha256 `1f65293669a6bf8a1bcc678555d4a5f2f56193e94fa90e453396c6fbc512441c`
  - 9 工作表（同名同序于 V1.0），总计 7031 非空格（V1.0 为 7402）
- V1.0 xlsx 留档不动（sha256 `2703f81240db0cc71c5fe109a6ff693617907a19c66885019ffe0da350713651`），供溯源与历史层引用
- `extract.py`：XLSX 路径与 `EXPECT_SHA256` 重钉 V2.0；解析方法不变（stdlib zipfile + ElementTree，本机无 openpyxl/pandas）

### 4.2 断言与规模更新（extract.py A 系列自校验 + verify_extraction.py）

| 断言 | V1.0 | V2.0 |
|---|---|---|
| 表3 设计矩阵模型数 | 68 | **64** |
| design-matrix.csv 逻辑行（含表头） | 69 | **65** |
| 表7 展开执行矩阵格数 | 337 | **325** |
| 07-expanded-matrix.csv 逻辑行（含表头） | 338 | **326** |
| 表7 列数 | 27 | **43** |
| col26 黄色"完善版"格 | 77 | **65** |
| 完善版追加 ID 集合（verify APPENDED_IDS） | 10 个（T10、S13、L01–L04、C14、C15、O09、P09） | **10 个，不变**——删除的 T09/S12/C13/O08 全部属原 58 条，不触碰追加集合 |

注意：col26 黄格 77→65（T10 全部 9 格 + S13 的 3 个 F0 格黄→蓝）意味着 V1.0 的"黄格集合 == 完善版模型全集格"推导在 V2.0 **不再成立**——extract.py A6 颜色校验须改为读源色断言（断言黄格数 65 且集合与源逐格一致），不得再从 APPENDED_IDS 推导。

### 4.3 各表转录要点（V2.0 实测结构，已由独立双路解析核实）

| 表 | 规模 | 相对 V1.0 的变化 |
|---|---|---|
| 表0 说明与总览 | 25 行 | 新增第⑥条判定边界（A23：检测×结局二维记录 + RAS-silent + Simulator failure 单列；模型数口径 68→64；"SDC率分母"→"结果率分母"） |
| 表1 单元与现有研究 | 8×7 | **值零变化**（仅 7 格共享串存储类型变化）→ 再生 01-units-and-research.md 应与现版逐字节相同 |
| 表2 LSU参数基线 | 29×5（原 20×5） | 删除"L1D ECC/parity=关闭"参数行；新增 r21–r29"逐单元保护机制核验（只列实际存在且纳入实现的机制）"节（合并区 A21:E21 表头 + 7 单元 × 5 列）；r1–r17 B0 参数逐字不变 |
| 表3 位置×模型矩阵 | 65×14（原 69×12） | **新 col F「故障表现形式/子模型」**：64 模型全部预填子模型枚举（约 180 条，如 `A01-a EA低位单bit；A01-b EA中位单bit；A01-c EA高位单bit`）；**新 col N「保护机制归属」**（7 类功能性约束，全部非 ECC/parity）；删除 4 模型行（T09/S12/C13/O08）；保留模型字段实质修改仅 15 处（C02/L03/P08/S02/S13，主题全部为去保护措辞） |
| 表4 观测点定义 | 7×6 | **整表重写**：L0–L5 改名重定义；L5 新结局分类（首检来源互斥 + Simulator failure 与体系结构结局分栏）；V1 守恒式 `Activated = Masked+Detected+SDC+Crash+Timeout` 废除 |
| 表5 频率与统计 | 20×6 | 新增 F 列「统计单位」（F0/F5/F6=run-level 独立样本；F1–F4=run-level cluster；事件级仅作传播记录）；r12 统计口径重定义（见 4.4） |
| 表6 负载清单 | 15×6 | **值零变化** → 再生 06 应逐字节相同 |
| 表7 展开执行矩阵 | 326×43（原 338×27） | 删除 12 RunID（4 模型 × F0/F5/F6）；col20 `Detected`→`Detected-contained`、col21 `SDC`→`Data Corruption` 原位改名；**新增 16 列（col28–43，AB–AQ）**，见 4.4；col43「故障表现形式/子模型」为唯一预填新列（325 行全填、浅蓝 FFD9E2F3，内容 = 该模型表3 col F 菜单原样复制）；结果槽 col16–25 与 col27–42 全空、col26 全"待执行"；公式仅存 6 个模板行（r2/66/130/194/258/322） |
| 表8 文献与来源 | 12×6 | **值零变化** → 再生 08 应逐字节相同 |

### 4.4 表7 新列 schema 与新统计口径（col28–43）

| 列 | 名称 | 语义 |
|---|---|---|
| 28 (AB) | SDC | 静默数据损坏计数（新分类学） |
| 29–32 (AC–AF) | Hardware RAS / OS / Application / None 首检（互斥） | 首次检出来源，四选一 |
| 33 (AG) | Contained | 检出且被遏制 |
| 34 (AH) | Detected-uncontained | 检出未遏制 |
| 35–36 (AI–AJ) | RAS-silent Crash / RAS-silent Timeout | 无任何检出的崩溃/超时 |
| 37 (AK) | 检测/告警证据 | 证据记录 |
| 38 (AL) | 硬件RAS检测率(任意时点) | col41 / 可分析activated |
| 39 (AM) | 检测计数差额（应为0） | `SUM(col29:32) − (col18 − col42)` |
| 40 (AN) | 结局计数差额（应为0） | `SUM(col19:23) + col42 − col18` |
| 41 (AO) | Hardware RAS检测（任意时点） | RAS 任意时点检出数（可与首检不同） |
| 42 (AP) | Simulator failure | 模拟器自身失败，独立分栏 |
| 43 (AQ) | 故障表现形式/子模型 | 预填菜单；执行时记录实际命中子模型 |

**新统计口径（表5 r12，V2.0 原文）**：激活率 = activated/attempted；**可分析 activated = activated − Simulator failure**；**SDC率 = SDC / 可分析 activated**；硬件检测率 = Hardware RAS 任意时点检出 / 可分析 activated。col24 公式（模板行）：`IF(OR(R="",R-AP<=0),"",AB/(R-AP))`。

**子模型轴语义（已核实）**：col43 的 64 个 distinct 值 = 每模型一份菜单复制到其全部 RunID——**不是网格膨胀轴**，是"实际故障表现形式的记录词汇表"：执行时记录每次注入实际命中的子模型（如位带），供分层分析。网格保持 64 模型 × 325 格。

### 4.5 网格构成（64 模型分布）

A01–A08（8）· T01–T08+T10（9，T09 删）· S01–S11+S13（12，S12 删）· C01–C12+C14+C15（14，C13 删）· O01–O07+O09（8，O08 删）· P01–P09（9）· L01–L04（4）。删除的 4 模型全部是攻击 ECC/parity/syndrome/poison 保护链的模型——B0 不启用这些保护，与 V1.0 试跑轮"不适用 6 格"的经验结论一致（V2.0 把试跑发现的形式化了）。

### 4.6 39 格不一致的落地方式（决策 D4）

- 03-design-matrix：表3 col10 旧措辞**照实转录**；
- 07-expanded-matrix：表7 col12 新措辞（"L5检测层级、控制情况与最终结局"）**照实转录**；
- 两个文件的提取注记各自标明：V2.0 内部此 39 格（AGU 系 8 模型）不同步，裁决为表7 执行权威，理由 = 表7 是 campaign 直接消费的执行矩阵且为作者更新过的一份；
- extract.py 的 A1 重放校验（表3 叉积 == 表7 col1–15）对这 39 格**显式豁免并计数**（39），其余 286 格仍强一致；
- 09-v2 的 V2-W4/V2-W5 消费表7 措辞。

### 4.7 校验链（verify_extraction.py 同步重写）

沿用"独立重解析 + 逐格回比 + 集合断言 + 片段检查"结构，更新为：

1. V1：design CSV 逐格（65 行 × 14 列）；
2. V2：expanded CSV 逐格（326 行 × 43 列）；
3. V3 集合断言：64 模型 / 325 RunID / 完善版 9 ID / RunID 格式与负载前缀匹配 / 模型 ID 唯一；
4. V4a/b/c：00/01/02/04/05/06/08 + README 片段检查（片段随 V2.0 文本更新）；
5. **新增**：col43 全填且每模型菜单与表3 col F 一致；col26 全"待执行"；col16–25、col27–42 结果槽全空；col39/40 守恒列结构存在；表1/6/8 再生输出与 V1.0 版**逐字节相同**（零变化表的不变量检查）；
6. 39 格豁免清单精确枚举（模型×频率×负载级），防止"豁免"变成"漏检"。

## 5. NORTH-STAR.md 规格（新建，北极星层）

无编号顶层文档（不占 00–08 转录序列），README 首行链接。目标长度 ~150 行。六节：

1. **使命**——ARM LSU 七单元（AGU/L1d-TLB/LQ/SQ/L1d-Cache/原子与同步/数据预取器）微架构级故障注入研究的三个研究问题（沿用 09 v1 §1 三问，按 V2.0 口径重述：单元级脆弱性谱、结构化 vs 随机、首检来源与结局分布）；
2. **不可妥协口径（V2.0 版）**——可分析 activated 分母；统计单位（F0/F5/F6 独立样本 vs F1–F4 cluster）；首检来源互斥；Simulator failure 分栏；两条守恒；三轨道不混算；B0 非鲲鹏 920 复刻；指标口径 AVF/条件占比/检出率严禁混算（表1 硬约束）；
3. **我们现在在哪**——V1.0 轮遗产清单：177 格试跑/2624 activated（1583 Masked + 1041 Crash + 0 SDC + 0 Timeout + 0 Detected，旧口径）、11 个 LSU 相关注入器、chaos_lsu_trigger.hh F0–F6 事件归一化触发层、FS 管线（真 B0 平台 + tlb_probe oracle + checkpoint）、已修一系列工具正确性 bug（采样偏差家族 9 员、超时证据丢弃、runner decode 崩溃等）、仓库暂停点 c6e07fa6；
4. **要去哪**——325 格 × 新 16 结果列全回填 + 两条守恒逐格闭合 + 子模型记录覆盖 + 首检×结局矩阵；
5. **怎么去**——指向 09-implementation-plan-v2.md（V2-W0..V2-W9 一览表）；
6. **裁决规则链**——§2.1 + D4。

## 6. 09-implementation-plan-v2.md 规格（计划层，新建为现行计划；旧 09 加"已被 V2.0 接替"横幅封存——对齐 OoO 先例 3412c1bc）

### 6.1 结构

§0 裁决规则（§2 全文收录）→ §1 目标与成功判据（三问 + 最终交付物：325 格 × 16 结果列回填 + 守恒逐格闭合 + 元分析报告）→ §2 机制核实（V1.0 轮九项核实的继承声明 + 表2 新增保护核验节带来的新核实项 + 39 格裁决记录）→ §3 WBS（V2-W0..V2-W9）→ §4 里程碑（M0'–M6'）→ §5 算力预算 → §6 V1.0 遗产映射表 → §7 诚实边界 → §8 风险登记（R1'–Rn'，对齐 OoO 先例）。

### 6.2 V2-W0..V2-W9 工作包（目标 / 依赖 / 验收 / 遗产映射）

| V2-W | 名称 | 目标与验收 | 依赖 | V1.0 遗产映射 |
|---|---|---|---|---|
| V2-W0 | 网格与工具重锚 | lsu_campaign.py 消费 325 格新 CSV；MODEL_FLAGS 删 T09/S12/C13/O08；manifest/schema 适配。验收：`--dry-run` 输出 RunID 集合 == CSV col1 集合（325） | 本交付（文档重锚） | W0(v1) 平台 + W10(v1) campaign 骨架 |
| V2-W1 | **分类学工具链**（最大工作包） | classify.py / lsu_l5_classify.py 适配 V2.0 结局分类学（六结局 + 首检四分 + SimFail 分栏 + 两守恒）；FS 侧 RAS/OS 首检证据通道（Oops/panic 解析 → OS 首检；gem5 内部错误 → Simulator failure）；旧→新映射器（供历史数据有损对照）。验收：单元测试 + 守恒 0 违规 + 映射器损失面如实文档化 | V2-W0 | 新增 |
| V2-W2 | 子模型记录 | 注入器上报实际命中子模型（AddrPath 位带、Cache 字节位置等）→ col43 回填；分层分析脚本。验收：试跑格 col43 非空且 ∈ 该模型菜单 | V2-W0 | 新增 |
| V2-W3 | 观测层 L0–L5 对齐 | 表4 重写版逐层落点核实：每行给出 vendored gem5 file:line 落点或诚实"无实现"。验收：表4 全行覆盖 | V2-W0 | W3(v1) 重定义 |
| V2-W4 | SE 侧 trial 重基线 | 325 格中 SE 可跑格按 V2.0 口径重跑试跑（30 activated/格目标）。验收：SE 格结果列回填 + 守恒闭合 + col43 记录 | V2-W1–V2-W3 | W4–W6、W8(v1) SE 部分 |
| V2-W5 | FS 侧 T 系列 | T05–T08 模式实现（valid/global/ASID 状态、permission 合法替换、hit 伪造/way 选择、walk pairing）；T10 位带参数化（摆脱退化为 T01）；TLB 锚点第二轮（skip-fix 后）；PTW 通路。验收：多 seed 注入点分散 + TC'22 谱 | V2-W1 | W7(v1) + M3-T 系列 |
| V2-W6 | 锚点复验 | TC'23 LQ（SDC=0 锚点）+ TC'22 T01（Crash/Hang/SDC 谱）在 V2.0 口径下复验。验收：锚点断言通过或差异如实报告 | V2-W4/V2-W5 | M2/M3 门(v1) |
| V2-W7 | screening | ≥385 activated/格（325×385≈125,125）。验收：全格达标或 blocked 如实标注 | V2-W4–V2-W6 | W10(v1) 后半 |
| V2-W8 | main | Wilson 95% 半宽 ≤2pp 或 5000 activated/格上限（≤325×5000≈162.5 万）。验收：同上 | V2-W7 | W10(v1) 后半 |
| V2-W9 | 元分析与报告 | 首检×结局矩阵、子模型分层、三问重答（V2.0 口径）、与 V1.0 历史轮的有损对照。验收：11(v2) 报告 + 守恒全闭合 | V2-W8 | W11(v1) |

### 6.3 里程碑

M0' 重锚完成（本交付 + V2-W0）→ M1' 分类学就绪（V2-W1–V2-W3）→ M2' SE 重基线 + 锚点（V2-W4、V2-W6 SE 部分）→ M3' FS T 系列锚点（V2-W5、V2-W6 FS 部分）→ M4' screening（V2-W7）→ M5' main（V2-W8）→ M6' 元分析（V2-W9）。

### 6.4 算力预算（325 格口径）

试跑 325×30 ≈ 9,750；screening 325×385 ≈ 125,125；main 上限 325×5000 ≈ 162.5 万。硬约束不变：≤4 并发 gem5 进程（29 GB 主机）、单次超时 10× 实测中位、≥5 seeds/格批次。**blocked 格数量（多核 FS 等）以 W0 重算为准，本 spec 不预编数字。**

### 6.5 诚实边界（09-v2 §7 必须包含）

- 多核 FS 负载格（O05–O07、W13 PARSEC 等）继续 workload-blocked，如实标注；
- 多单元联合注入不在 V2.0 网格内（显式声明，不偷偷扩范围）；
- V1.0 历史数据 → 新分类学的映射是**有损的**（旧 Crash/Timeout 无法回溯判定 RAS/OS 检出状态），只能做方向性对照；
- B0 非鲲鹏 920 复刻；TLB/PTW/SysReg 注入器 FS-only（SE-inert by construction）；
- F6 消费端腐蚀对 S10/L04/C11/C12/C14/C15 仍 deferred（V2-W0 重锚后清单以 lsu_campaign 实际为准）；
- CHAOSAddrPath 的 .py preMode 枚举缺 s05/s06/s07/s11/l02（.cc 已实现）——配置面与实现面不同步，V2-W4 前修复；
- cache/exmon 族 tier 未消费（legacy firstClock）——V2-W3 一并核实落点。

## 7. 历史层处理（10/11）

`10-trial-results.md` 与 `11-meta-analysis.md` **原地保留**，顶部插入统一标注块：

- 数据口径：V1.0（337 格、旧五分类、旧守恒式 `Activated = Masked+Detected+SDC+Crash+Timeout`）；
- 地位：V1.0 轮试跑证据，数据不作废、不与新轮直接比较；
- 与 V2.0 的关系：网格 12 格已删（T09/S12/C13/O08 × F0/F5/F6，试跑轮"不适用"结论的形式化）；试跑数据格只能经 V2-W1 映射器做**有损**对照——删除的 12 格在试跑轮本就多为"不适用/blocked"（"不适用 6 格"正是删除这 4 模型的经验依据），177 试跑格与 325 格的精确交集以 W0 重算为准，本 spec 不预编数字；
- 新轮结果将写入 V2.0 版 07 CSV 的 col16–25/col27–42，不覆盖本文件。

## 8. README 更新规格

- §数字总账：68/337 → 64/325，新增"16 结果列 / 两条守恒 / 可分析 activated"口径条目；
- §文档地图：加 NORTH-STAR.md 首链、09-implementation-plan-v2.md 现行计划行 + 09 封存横幅说明、历史层标注；
- §溯源与复现：两命令验证链不变（extract.py → `EXTRACTION VERIFICATION PASSED`；verify_extraction.py → `ALL PASSED`），源文件条目改为 V2.0 xlsx + sha256，V1.0 xlsx 留档说明；
- §诚实声明：V2.0 版（含 39 格裁决、子模型轴语义、历史层关系）。

## 9. 验证与验收（本交付，每单元真命令）

| 单元 | 验收命令 | 预期 |
|---|---|---|
| P1：extract.py V2.0 化 + 00–08/2CSV 再生（原子提交） | `cd docs/gem5-fi/lsu && python3 extract.py`；`git diff` 逐文件审查 | 末行 `EXTRACTION VERIFICATION PASSED`（断言 64/325/65/326/65 黄格/39 豁免）；01/06/08 与 HEAD 逐字节相同；03/07/00/02/04/05 差异与 §4.3 一一对应 |
| P2：verify_extraction.py V2.0 化 | `python3 verify_extraction.py` | 末行 `ALL PASSED`（含 §4.7 新断言组） |
| P3：10/11 历史标注 | `git diff` | 仅顶部插入标注块，正文零改动 |
| P4：NORTH-STAR.md | 人工审阅 + 数字与 10/11/09 交叉核对 | 六节齐、无编造数字 |
| P5：09-implementation-plan-v2.md + 旧 09 接替横幅 | 人工审阅 + W 表与源码缺口清单核对 | V2-W0..V2-W9/M0'–M6'/遗产映射/预算/诚实边界/风险登记齐；旧 09 顶部横幅 |
| P6：README 更新 | 片段检查（verify V4c） | `ALL PASSED` 覆盖 |
| 全局隔离与回归 | `git status --porcelain`（仅 docs/ 下预期文件）；canonical SE golden reg_chain（golden `f247ef3fe6f02cfd`，具体命令从 task_plan.md / progress.md 检索既有用法落实） | 源码/工具零触碰；golden 一致（CLAUDE.md 不受影响测试） |

## 10. 实施顺序（writing-plans 的分解骨架，one-patch-per-unit）

P1 extract.py V2.0 化 + 00–08/2CSV 再生（原子提交：机器 + 输出，与 V1.0 史 c96825bf 同构）→ P2 verify_extraction.py V2.0 化（独立校验器，与 V1.0 史 8aac96d8 同构）→ P3 10/11 历史标注 → P4 NORTH-STAR.md → P5 新建 09-implementation-plan-v2.md（现行计划）+ 旧 09 加"已被 V2.0 接替"横幅（一个单元：接替声明与新计划同生）→ P6 README 更新。每 P 一个 commit，验证通过才提交，提交即推送。此后按 09-v2 的 V2-W0..V2-W9 逐包另行计划执行。

## 11. 范围外（显式排除）

- 源码与工具改动（lsu_campaign/classify/注入器上报等）——V2-W0..V2-W9 执行内容；
- 多单元联合注入——V2.0 网格不含；
- 多核 FS 负载格的解锁——继续 blocked；
- 鲲鹏 920 轨道、OoO 轨道的任何改动——不同 scope，严禁混算；
- 修改 V2.0 源表内容——只转录 + 注记，不替作者改源表（39 格不一致也只裁决不修改）。

## 12. 附录：执行所需关键数据

### 12.1 V1.0 → V2.0 变更清单摘要（机器差分，2026-09-28 双路解析核实）

- sheet 级：9 表同名同序；表2 20→29 行；表3 69×12→65×14；表7 338×27→326×43；表5 新 F 列；
- 模型：68→64（删 T09/S12/C13/O08）；运行 337→325（删 12 RunID）；保留模型字段实质修改 15 处（C02/L03/P08/S02/S13）；col1–15 除 89 例外逐字不变；
- 分类学：SDC→Data Corruption、Detected→Detected-contained（原位改名）+ 16 新列 + 旧守恒式废除 + 两条新守恒 + Simulator failure 分栏；
- 统计：可分析 activated 分母、统计单位列、公式缩减为 6 模板行；
- 颜色：col26 黄格 77→65（T10 全部 9 格 + S13 的 3 个 F0 格黄→蓝）；新浅蓝 FFD9E2F3 col43；
- 内部不一致：表3 col10 vs 表7 col12 在 AGU 系 8 模型 39 运行不同步（表7 新措辞，表3 旧文）。

### 12.2 源码缺口清单（V2-W1/V2-W2/V2-W5 的输入，2026-09-28 盘点）

- 分类学：classify.py 五分类（Masked/Detected/SDC/Crash/Timeout）与 V2.0 六结局+首检四分不对应；无 RAS/OS 首检证据通道；
- 子模型：无任何注入器上报实际命中子模型；
- T 系列：T05–T08 未实现（lsu_campaign 标 deferred mode unimplemented）；T10 位带未参数化；
- F6 消费端：S10/L04/C11/C12/C14/C15 notify-only；
- CHAOSAddrPath：.py preMode 枚举缺 s05/s06/s07/s11/l02（.cc 已实现）；
- cache/exmon 族：lsuTier 参数 wire-ready 未消费；
- 多单元：不存在（V2.0 也不要求）。

### 12.3 V1.0 试跑轮遗产数字（历史层引用）

177 试跑 / 108 blocked(fs-infra) / 46 deferred / 6 不适用 = 337；Activated 2624 = 1583 Masked + 1041 Crash + 0 SDC + 0 Timeout + 0 Detected；单元族谱 Crash 率：A 86%、S 88%、C Masked 80%、P Masked 98%、L Masked 100%（TC'23 LQ SDC=0 锚点复现）；零激活 53/177；工具 bug 3 个已修（28e405cc、6e0dcd52、35a57ab3）。

### 12.4 现有源码资产（北极星"我们现在在哪"的引用基础）

11 个 LSU 相关注入器（LSQFwd/L1DForward/AddrPath/ArmTLB/PTW/ArmSysReg/ExMon/Cache/Prefetch/Mem）；chaos_lsu_trigger.hh F0–F6 事件归一化（与 OoO 轨 chaos_trigger.hh 周期制并存，轨道不混）；lsu_campaign.py 三阶段自适应采样；FS 管线（arm_chaos_fs.py 主体化 B0/V110 参数 + tlb_probe oracle golden `b6d81b36…` + boot_ckpt v3 内容分派）；采样偏差家族 9 员已修（含 CHAOSArmTLB events_to_skip，9187ef28）。
