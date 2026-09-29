# V2.0 忠实层 —— gem5-fi OoO 单元故障注入方案 V2.0（北极星提取）

> 本目录是《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（9 表，WPS 生成）的忠实提取层，全部文件由 `extract_v2.py` 确定性生成（勿手改；改表后重跑生成器）。
> V1.0 忠实层在 `../`；**两版口径不同，数值永不混用**——按用户指令 2026-09-28，V2.0 是 V1.0 的重大更新版本，冲突处以 V2.0 为准（V1.0↔V2.0 行级映射见 `d-bridge-v1-v2.csv`，由 `bridge_v1_v2.py` 生成，属 V2-W0.2 独立单元）。

## 文件导航

| 文件 | 来源工作表 | 内容 |
|---|---|---|
| `00-overview.md` | 0.说明与总览 | 范围 / B0 基线 / 工作簿结构 / 统计与判定边界（R1–R25 单列表） |
| `01-units-and-research.md` | 1.单元与现有研究 | 六单元 × 现有研究 / 证据直接性 / 研究空白 |
| `02-ooo-params-baseline.md` | 2.OOO参数基线 | B0 参数（R2–R24）+ S0–S6 敏感性 + 逐单元保护机制核验（R25–R31） |
| `03-design-matrix.md` | 3.位置x模型矩阵 | **57 故障模型 × 14 列全量**（按单元分节；D/R/B/FD/FR/FB） |
| `design-matrix.csv` | 3.位置x模型矩阵 | 同上机读版（模型ID + Excel行 + 14 列，57 行） |
| `04-observation-points.md` | 4.观测点定义 | L0–L5 传播链观测点（6 层级 × 6 列） |
| `05-frequency-and-statistics.md` | 5.频率与统计 | F0–F6 档位（eligible-event 归一化）+ 8 条统计规则 |
| `06-workloads.md` | 6.负载清单 | W0–W13（14 负载）+ 接线状态提取注（11 接入 / 3 未接入） |
| `07-expanded-matrix.csv` | 7.展开执行矩阵 | **310 实验格 × 43 列全量**（+Excel行 管理列） |
| `07-expanded-matrix.md` | 7.展开执行矩阵 | 列文档 + 频率/单元/负载分布 + 每模型格数模板 |
| `08-references.md` | 8.文献与来源 | 11 条来源（GEM5-O3/BASE、TC23、MICRO24/25、CHAOS26 等） |
| `d-bridge-v1-v2.csv` | （派生） | V1.0 91 行 ↔ V2.0 57 模型映射（V2-W0.2，`bridge_v1_v2.py` 生成） |

## 提取方法

- 纯标准库（本机 pip 403 无 openpyxl）：`zipfile` + `xml.etree.ElementTree` 直解 spreadsheetml XML；解析核心复自经读回校验的全量转储器（sharedStrings / inlineStr / str / b / n 全类型覆盖）。
- WPS 工作簿适配：rels 使用包绝对路径 `/xl/...`（与 Excel 相对路径两种写法都兼容）；母公式格以 `值⟦f:公式⟧` 记法保留（25 格，无缓存值）；其余行的 t="shared" 共享公式引用（1525 格，无文本无缓存值）在 CSV 中呈现为空，完整机制见断言 formulas-shared 与诚实性注记 (b)。
- 忠实原则：单元格文字**原文照录**，仅版式/标题/行号标记排版；一切本目录标注以〔提取注〕显式标记。
- 确定性：无时间戳、无随机数；重跑逐字节复现（sha256 不变）。

## 断言结果（`python3 extract_v2.py` 真实运行输出，逐字引用）

```
[source] gem5-fi-OoO单元故障注入方案V2.0.xlsx sha256=b73b6304005e507f5e8a1f41f0fc979f3d6439e6dda875ec4d2be961b867ae75
[sheets] PASS — 9 sheets: 0.说明与总览 / 1.单元与现有研究 / 2.OOO参数基线 / 3.位置x模型矩阵 / 4.观测点定义 / 5.频率与统计 / 6.负载清单 / 7.展开执行矩阵 / 8.文献与来源
[cell-counts] PASS — non-empty cells per sheet: 22/49/151/812/42/102/90/5338/72 (total 6678)
[design-header] PASS — sheet4 R1 = 14 expected column names
[design-rows] PASS — sheet4 R2-R58 = 57 non-empty design rows x 14 cols
[design-units] PASS — Int Decode=9, Int Rename=9, Int Dispatch / ROB=10, FP/SIMD Decode=9, FP/SIMD Rename=10, FP/SIMD Dispatch/ROB=10 (sum 57)
[design-ids] PASS — model IDs == D01-D09/R01-R09/B01-B10/FD01-FD09/FR01-FR10/FB01-FB10 in order
[submodels] PASS — total sub-model entries = 193 (per-model 2-5)
[expanded-header] PASS — sheet8 R1 = 43 expected column names
[expanded-rows] PASS — sheet8 R2-R311 = 310 non-empty rows x 43 cols
[runid] PASS — unique 310/310; RunID == 模型ID-频率-负载ID for all rows
[replay] PASS — design 适用频率x适用负载 replay == sheet8 (模型ID,频率,负载名) 310/310 rows, order included
[cross-freq] PASS — sheet8 频率定义 vs sheet6 定义 (keyed by 档位): 0 mismatches / 310
[cross-load] PASS — sheet8 负载（真实名称） vs sheet7 负载ID+名称: 0 mismatches / 310
[cross-loaddef] PASS — sheet8 负载定义/oracle == sheet7 名称+（类型）+执行定义与oracle：0 mismatches / 310
[result-slots] PASS — value slots P..AP (excl. Z) all empty in 310 rows; 记录状态(Z)=待执行 310/310
[formulas] PASS — 25 master formula cells (with text) exactly at Excel rows [2, 66, 130, 194, 258] x cols ['X', 'Y', 'AL', 'AM', 'AN'], no cached values
[formulas-shared] PASS — total <f> elements = 1550 (t="shared": 1550); 25 with formula text, 0 with cached <v> — 5 computed cols x ALL 310 rows are formula-bound via shared formulas (si groups 0-19 x64 + 20-24 x54); opens live, NO copy-down needed
[dist-freq] PASS — F0=104, F1=12, F2=76, F3=0, F4=28, F5=10, F6=80 (sum 310)
[dist-unit] PASS — Int Decode=48, Int Rename=48, Int Dispatch / ROB=54, FP/SIMD Decode=52, FP/SIMD Rename=54, FP/SIMD Dispatch/ROB=54 (sum 310)
[dist-load] PASS — W9 NEON-LaneProbe=48 / W5 ROB-Recovery=42 / W10 PolyBench=42 / W8 FP-ScalarProbe=38 / W4 Rename-Dependency=27 / W6 CoreMark+Embench=25 / W3 A64-DecodeProbe=24 / W7 GAP-Selected=21 / W13 FP-ExceptionRecovery=20 / W11 libjpeg-turbo-NEON=12 / W1 MiBench-TC23=11 (sum 310)
[template] PASS — per-model cells by fault type: 单比特翻转=6, 双比特翻转=4, 换值=6, 错位拼接=6, 状态=6, 时序=6, 状态/时序=6, 卡死=2, 状态/换值=6
[submodel-bound] PASS — full 子模型 expansion bound = Σ(子模型数x格数) = 1050 (derived; sheet8 enumerates 310)

EXTRACTION VERIFICATION PASSED
```

## 源文件

- 路径：`docs/gem5-fi/ooo/gem5-fi-OoO单元故障注入方案V2.0.xlsx`
- sha256：`b73b6304005e507f5e8a1f41f0fc979f3d6439e6dda875ec4d2be961b867ae75`
- 9 表非空单元格：22 / 49 / 151 / 812 / 42 / 102 / 90 / 5338 / 72（合计 6,678）

## 诚实性注记（HONESTY NOTES）

(a) **工作簿内部不一致（展开维度）**：sheet1 R15 声称展开维度为「模型×故障表现形式/子模型×频率×负载全展开」，但 sheet8 实际只展开到 **模型×频率×负载 = 310 格**，子模型以整格文本附在 AQ 列。若真按子模型展开应为 **1050 格**（派生计算 Σ(子模型数×格数)，已由本脚本复算核实）。计划裁决 **D4**：执行 310 格，格内按子模型分层记录，不扩建 1050 格。

(b) **公式机制（2026-09-29 编排者独立批判性核验修正——覆盖早先"仅 5 行 25 格、使用前需下拉复制"的机制误读）**：sheet8 的 5 个计算列（X=SDC率(可分析activated) / Y=激活率 / AL=硬件RAS检测率(任意时点) / AM=检测计数差额（应为0） / AN=结局计数差额（应为0））共有 **1550 个公式单元格 = 5 列 × 全部 310 行**，全部为 t="shared" 共享公式：25 个母公式文本在 Excel 行 2/66/130/194/258（每列 5 个 si 组：组 0-19 各 64 格 + 组 20-24 各 54 格），其余 1525 格为共享引用；**0 个缓存值**。共享公式已把 5 列绑定到全表——**打开工作簿即全表可算，无需下拉复制**（delta 报告 §3.8.4 原说法的勘误见其 §7）。公式语义（与 sheet6 统计规则逐条一致，已逐条审计）：`SDC率 = SDC/(Activated − Simulator failure)`、`激活率 = Activated/Attempted`、`检测计数差额 = SUM(首检四类) − (Activated − Simulator failure)`、`结局计数差额 = SUM(五类结局) + Simulator failure − Activated`（两个差额列应为 0，自检审计列）。

(c) **定义了但未接线**：负载 W0（MiniCheck-OOO）/ W2（BEEBS-DelayAVF）/ W12（SPEC CPU2017 SimPoint，需许可证）在 sheet7 有完整定义，但 sheet8 的 310 格中无任何以之为负载的格；频率档 F3（高频压力）在 sheet6 有定义，但 310 格中 0 格使用。

(d) **WPS 生成的工作簿**：无 docProps（创建者/修改时间元数据缺失）；zip 内部时间戳 2026-09-28 16:50（全部条目一致）；rels 用包绝对路径 `/xl/...`。与 V1.0（Excel 生成、有合并单元格）不同，V2.0 九表均无合并单元格。

(e) **全部 310 格 记录状态=待执行**：所有结果槽（22 个值列）在源表中全空，与 V1.0 源表口径一致——本目录是纯设计提取，不含任何实验结果数据。

