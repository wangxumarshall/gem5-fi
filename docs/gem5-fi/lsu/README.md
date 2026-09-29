# gem5-fi LSU 单元故障注入方案 V2.0 —— 忠实提取层（北极星）

> 本目录是《gem5-fi-LSU单元故障注入方案V2.0.xlsx》（9 表，Microsoft Excel 生成）的忠实提取层，全部文件由 `extract.py` 确定性生成（勿手改；改表后重跑生成器）。
> 历史：V1.0 工作簿与 V1.0 提取层曾并存于本仓库，2026-09-29 随清库移除（commit `26cff381`/`3415ae69`，git 历史可查）；本目录是仓库内唯一现行版本。

## 文件导航

| 文件 | 来源工作表 | 内容 |
|---|---|---|
| `00-overview.md` | 0.说明与总览 | 范围 / B0 基线 / 工作簿结构 / 统计与判定边界 / 完善版增量（R1–R25 单列表） |
| `01-units-and-research.md` | 1.单元与现有研究 | 七单元 × 现有研究 / 证据直接性 / 研究空白 |
| `02-lsu-params-baseline.md` | 2.LSU参数基线 | B0 参数（R2–R19）+ 敏感性配置 + 逐单元保护机制核验（R21–R29，含全簿唯一合并单元格 A21:E21） |
| `03-design-matrix.md` | 3.位置x模型矩阵 | **64 故障模型 × 14 列全量**（按单元分节；A/T/S/L/C/O/P） |
| `design-matrix.csv` | 3.位置x模型矩阵 | 同上机读版（模型ID + Excel行 + 14 列，64 行） |
| `04-observation-points.md` | 4.观测点定义 | L0–L5 传播链观测点（6 层级 × 6 列） |
| `05-frequency-and-sampling.md` | 5.频率与统计 | F0–F6 档位（eligible-event 归一化）+ 9 条统计规则 |
| `06-workloads.md` | 6.负载清单 | W0–W13（14 负载）+ 接线状态提取注（14/14 全部接入） |
| `07-expanded-matrix.csv` | 7.展开执行矩阵 | **325 实验格 × 43 列全量**（+Excel行 管理列） |
| `07-expanded-matrix.md` | 7.展开执行矩阵 | 列文档 + 频率/单元/负载分布 + 每模型格数 |
| `08-references.md` | 8.文献与来源 | 11 条来源（GEM5-O3/BASE/MMU/SYS、IISWC15、TC22/23、HPCA24、MICRO24/25、CHAOS26） |

## 提取方法

- 纯标准库（本机 pip 403 无 openpyxl）：`zipfile` + `xml.etree.ElementTree` 直解 spreadsheetml XML；解析核心复自经读回校验的全量转储器（sharedStrings / inlineStr / str / b / n 全类型覆盖）。
- Excel 生成的工作簿（docProps: Microsoft Excel 16.0300、lastModifiedBy Borise Ding、modified 2026-09-28T11:03:46Z）；rels 为相对路径（解析器对 WPS 绝对路径写法亦兼容）；sheet2 R21 有全簿唯一合并单元格 A21:E21。
- XML 行尾规范化（§2.11）：Excel 在单元格内写入的 CRLF（如「适用负载」多行文本）经 XML 解析规范为 LF——这是一切 XML 一致性解析器（ElementTree/Excel/WPS/openpyxl）的共同行为；本目录 CSV/md 中此类文本为 LF 分行。
- 母公式格以 `值⟦f:公式⟧` 记法保留（27 格，无缓存值）；其余行的 t="shared" 共享公式引用（1622 格，无文本无缓存值）在 CSV 中呈现为空，完整机制见断言 formulas-shared 与诚实性注记 (e)。
- 忠实原则：单元格文字**原文照录**，仅版式/标题/行号标记排版；一切本目录标注以〔提取注〕显式标记。
- 确定性：无时间戳、无随机数；重跑逐字节复现（sha256 不变）。

## 断言结果（`python3 extract.py` 真实运行输出，逐字引用）

```
[source] gem5-fi-LSU单元故障注入方案V2.0.xlsx sha256=1f65293669a6bf8a1bcc678555d4a5f2f56193e94fa90e453396c6fbc512441c
[sheets] PASS — 9 sheets: 0.说明与总览 / 1.单元与现有研究 / 2.LSU参数基线 / 3.位置x模型矩阵 / 4.观测点定义 / 5.频率与统计 / 6.负载清单 / 7.展开执行矩阵 / 8.文献与来源
[cell-counts] PASS — non-empty cells per sheet: 22/56/136/910/42/108/90/5595/72 (total 7031)
[merges] PASS — mergeCells: sheet2 = [A21:E21] (R21 节标题), 其余 8 表均无合并单元格
[design-header] PASS — sheet4 R1 = 14 expected column names
[design-rows] PASS — sheet4 R2-R65 = 64 non-empty design rows x 14 cols
[design-units] PASS — AGU=8, L1d-TLB=9, Store Queue=12, Load Queue=4, L1d-Cache=14, 原子与同步=8, 数据预取器=9 (sum 64)
[design-ids] PASS — model IDs == A01-A08 / T01,T10,T02-T08 / S01-S11,S13 / L01-L04 / C01-C12,C14,C15 / O01-O07,O09 / P01-P09 in source order (T10 after T01; no S12/C13/O08)
[submodels] PASS — total sub-model entries = 178 (per-model 1-4)
[expanded-header] PASS — sheet8 R1 = 43 expected column names
[expanded-rows] PASS — sheet8 R2-R326 = 325 non-empty rows x 43 cols
[runid] PASS — unique 325/325; RunID == 模型ID-频率-负载ID(W#) for all rows; sheet8 负载列以表6 名称开头 325/325
[replay] PASS — design 适用频率x适用负载 replay == sheet8 (模型ID,频率,负载名) as MULTISET 325/325 rows (order differs: True — sheet3 追加模型并入单元块、sheet8 保留原展开序置尾，见 README 注记 (b))
[cross-freq] PASS — sheet8 频率定义 vs sheet6 定义: 13 mismatches / 325 — exactly the F6 rows of L02/L03/L04/C15/P09 (13 rows) carrying an alternative F6 definition text (README 注记 (c)); other 312 rows exact
[cross-loaddef] PASS — sheet8 负载定义/oracle == I列 + 换行 + 表6 D列: 313/325 exact; other 12 rows = SPEC CPU2017 (W11) with rewritten oracle text (README 注记 (d))
[result-slots] PASS — value slots P..AP (excl. Z) all empty in 325 rows; 记录状态(Z)=待执行 325/325
[formulas] PASS — 27 master formula cells (with text) exactly at Excel rows [2, 66, 130, 194, 258] x cols X/Y/AL/AM/AN + row [322] x cols X/Y, no cached values
[formulas-shared] PASS — total <f> elements = 1649 (all t="shared"); with text = 27, non-empty cached <v> = 0 (Excel 写法：每个公式格带自闭合空 <v/> 占位，无缓存值文本); per column {'X': 337, 'Y': 337, 'AL': 325, 'AM': 325, 'AN': 325}; formula rows span 2-338 — X/Y shared formulas extend to R338 (12 template rows below the 325 data rows, no data there), AL/AM/AN exactly cover the data rows
[dist-freq] PASS — F0=105, F1=24, F2=77, F3=4, F4=26, F5=25, F6=64 (sum 325; 全部 7 档均被使用，F3 仅 4 格)
[dist-unit] PASS — AGU=39, L1d-TLB=39, Store Queue=63, Load Queue=30, L1d-Cache=73, 原子与同步=28, 数据预取器=53 (sum 325)
[dist-load] PASS — 14/14 workloads wired (all defined workloads used); cells per W id: W0=6, W1=27, W10=27, W11=12, W12=15, W13=6, W2=6, W3=24, W4=24, W5=54, W6=55, W7=29, W8=25, W9=15
[per-model] PASS — per-model cells == len(适用频率)xlen(适用负载) for all 64 models; cells distribution {2: 6, 3: 16, 4: 6, 6: 28, 8: 2, 9: 5, 12: 1} (range 2-12)
[submodel-bound] PASS — full 子模型 expansion bound = Σ(子模型数x格数) = 922 (derived; sheet8 enumerates 325 with submodels as whole-cell text in AQ)

EXTRACTION VERIFICATION PASSED
```

## 源文件

- 路径：`docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案V2.0.xlsx`
- sha256：`1f65293669a6bf8a1bcc678555d4a5f2f56193e94fa90e453396c6fbc512441c`
- 9 表非空单元格：22 / 56 / 136 / 910 / 42 / 108 / 90 / 5595 / 72（合计 7,031）

## 诚实性注记（HONESTY NOTES）

(a) **子模型维度未展开**：sheet8 的 325 格按 模型×频率×负载 展开，子模型以整格文本附在 AQ 列（178 个子模型）。若按子模型全展开应为 **922 格**（派生计算 Σ(子模型数×格数)，已由本脚本复算核实）。执行时格内按子模型分层记录。

(b) **双表模型顺序不一致（重放为多重集全等）**：sheet3 设计矩阵把 10 个追加模型并入各单元块（T10 插在 T01 之后、S13 接 S11、L01–L04 在 SQ 块后、C14/C15 接 C12、O09 接 O07、P09 殿后）；sheet8 展开矩阵则保留原 54 模型展开序、10 个追加模型置尾（T10 在 R250–R258 一带）。两序不同但多重集全等（断言 replay）；本提取对 sheet3/sheet8 各自原序忠实，不重排。

(c) **13 行 F6 频率定义与表5 不一致**：L02/L03/L04/C15/P09 的 F6 行（共 13 格）在sheet8 的「频率定义」列为「首次出现指定事件时注入一次；仍以故障值被下游消费作为 activated 判据」，而表5 F6 定义为「首次出现指定事件时注入一次，如 TLB hit、SQ forward、dirty eviction、CAS 成功」——语义兼容但文本不同（断言 cross-freq 锁定该 13 行与文本）。其余 312 行频率定义与表5 逐字全等。

(d) **12 行 SPEC CPU2017 的负载定义/oracle 为改写文本**：W11（SPEC CPU2017 采样区间）的 12 格 J 列为「…checkpoint；使用参考输出或结果哈希」，而表6 W11 D 列为「选择 …checkpoint；不跑全程」——非逐字复制（断言 cross-loaddef 锁定该 12 行）。其余 313 行 J == I列 + 换行 +「执行定义与 oracle：」+ 表6 D列 精确成立。

(e) **公式机制与数据区外模板行**：sheet8 的 5 个计算列（X=SDC率(可分析activated) / Y=激活率 / AL=硬件RAS检测率(任意时点) / AM=检测计数差额（应为0） / AN=结局计数差额（应为0））共有 **1649 个公式单元格**，全部 t="shared" 共享公式：27 个母公式文本在 Excel 行 2/66/130/194/258（全 5 列）与 322（仅 X/Y），其余 1622 格为共享引用；**0 个非空缓存值**（Excel 写法：每个公式格带自闭合空 `<v/>` 占位——与 WPS 生成的 OoO V2.0 无 `<v>` 元素的写法不同，但同样无缓存值文本）。逐列：X=337 / Y=337 / AL=325 / AM=325 / AN=325——**X/Y 列的共享公式延伸到 R338**，即数据区（R2–R326）之下有 **12 行无数据的公式模板行**（R327–R338，复制粘贴残留，无任何数据单元格）；AL/AM/AN 恰好只覆盖 325 个数据行。公式语义：`SDC率 = SDC/(Activated − Simulator failure)`、`激活率 = Activated/Attempted`、`检测计数差额 = SUM(首检四类) − (Activated − Simulator failure)`、`结局计数差额 = SUM(五类结局) + Simulator failure − Activated`（两个差额列应为 0，自检审计列）。

(f) **模型 ID 序列特征（源表原样）**：T10 插在 T01 之后；S12/C13/O08 缺号（源表无此三行）；R25 完善版增量称「原58条模型扩展为64条」。本提取按源表原序忠实照录，不补号、不重排。

(g) **全部 325 格 记录状态=待执行**：所有结果槽（22 个值列）在源表中全空——本目录是纯设计提取，不含任何实验结果数据。

## 与仓库源码的映射〔提取注，2026-09-29 grep/ls 核实；非源表内容〕

### 复用（file:line 证据）

| 方案需要 | 仓库现状 |
|---|---|
| B0 = O3_ARM_v7a_3 + LSU 修正 | `CHAOS/gem5/configs/common/cores/arm/O3_ARM_v7a.py:163-166` LQEntries=16 / SQEntries=16 / LSQDepCheckShift=0；`:246-247` StridePrefetcher(degree=8, latency=1, prefetch_on_access=True)；`configs/se/lsu_proxy.py`（C4-LSU B0 平台）按 02 表逐参数落地并固化 L2 TLB=1280/5-way |
| 敏感性配置 S1–S4 | `configs/se/lsu_proxy.py:157-159,589-693` `--variant B0/S1/S2/S3/S4`：S1=DTLB 64（回默认）、S2=64KiB/4-way、S3=LSQDepCheckShift=4、S4=预取器挂 L1D——与表2 敏感性列逐项对应 |
| LSU SE 平台（挂 16+ 注入器） | `configs/se/lsu_proxy.py:30` 导入 CHAOSReg/PhysReg/Mem/Cache/LSQFwd/RenameMap/FreeList/ROB/IQ/Exec/FPU/L1DForward/BPU/AddrPath/Decode/ExMon/RAS/Probe/CommitTrace/MicroSnap/**CHAOSPrefetch** |
| LSU FS 平台（W7 等） | `configs/fs/lsu_b0_fs.py`（经 `arm_chaos_fs.py --lsu_b0` 施加 B0 增量；W7/M3 计划 Task 4 交付） |
| SQ forwarding / L1D 行 注入（S01–S13 / C01–C15 部分） | `tools/runner.py:1108` `elif comp == "lsq_fwd":`；`:1186` `elif comp == "l1d_fwd":`；`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/`、`CHAOSL1DForward/`、`src/mem/cache/CHAOSCache/` |
| L1d-TLB 注入（T01–T10） | `tools/runner.py:1331` `elif comp == "l1_tlb":`——Arm TLB 注入器 FS-only、SE-inert（`l1_tlb requires platform`） |
| 预取器注入器（P01–P09） | `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/`（.cc/.hh/.py 四件套）；`configs/se/lsu_proxy.py:699-713` `--chaos_prefetch` 挂载（W8 P 系列） |
| F0/F1/F2/F3/F5 触发语义 | `CHAOS/gem5/src/cpu/o3/chaos_trigger.hh:23-26` `enum class ChaOSTier { F0, F1, F2, F3, F5 }` |
| 统一分类 / Wilson CI / LSU 工具链 | `tools/classify.py`（runner 与 campaign 共用）；`tools/wilson.py`；`tools/lsu_campaign.py`、`tools/lsu_l5_classify.py`、`tools/lsu_meta_analysis.py`、`tools/event_density.py` |
| 定向负载（已建） | `workloads/directed/`：mini_check(W0)、beebs_kernels(W2)、agu_addrmodes(W3)、sq_forward(W5)、cache_dirtyevict(W6)、atomics_probe(W7)、prefetch_stride(W8)、gap_bfs(W9)、stream_chase+stream_triad(W10)、sqlite_like(≈W12)、stuck_persist/spinlock_checksum（F5/原子辅助） |

### 缺口（如实列出，实施前须补齐）

| 方案需要 | 缺口 |
|---|---|
| F4（短突发）/ F6（确定性事件触发）触发语义 | `chaos_trigger.hh:23-26` 枚举**仅 F0/F1/F2/F3/F5**；展开矩阵 F4=26 格、F6=64 格依赖这两档 |
| AGU 注入器（A01–A08） | `tools/runner.py` 组件分派无 `agu`；`src/cpu/o3/` 无 AGU 类 CHAOS 注入器目录 |
| 原子与同步注入器（O01–O09） | 同上：无 `atomic` 组件分支；且 W7 Atomic-Litmus 依赖多核 FS——`configs/fs/` 仅单核代理 |
| 预取器接线（P 系列端到端） | `CHAOSPrefetch` 注入器与 `lsu_proxy.py` 挂载旗标已在，但`tools/runner.py` 无 `prefetch` 组件分派、`schemas/manifest.schema.json` 组件枚举（21 项）无 `prefetch`——端到端接线缺 runner+schema 两环 |
| LQ 生命周期/响应配对注入器（L01–L04） | `src/cpu/o3/` 仅 `CHAOSLSQFwd`（forwarding 场景），无 LQ 生命周期/violation-replay/response 配对注入器 |
| manifest schema 组件枚举 | `schemas/manifest.schema.json` **缺 bpu/decode/exmon/ras/addr_path**（`tools/runner.py:1197-1388` 有分派但校验层未登记） |
| 负载 W1/W4/W11/W13 | `workloads/directed/` 无 MiBench-TC23（W1）、TLB-AliasPerm FS 探针（W4，FS-only）、SPEC CPU2017（W11，需许可证）、PARSEC-Selected（W13，多核 FS） |

