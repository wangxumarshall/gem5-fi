# R6 完整故障传播路径（17 RunID × 3 seed = 51）

## 目的

本目录为 17 个 L1d-TLB RunID × 3 个 seed（共 51 个完整样本）逐 seed 记录**从注入到终局（或显式含住）的完整传播过程**。`T03-F5-W9` 的三个 seed （terminal=`full`，admitted=True，certified=True，violations=[]）已全部补齐。

每个 MD 只使用该 seed 自己未经修改的 `prop_evt.txt.gz` 重建；`chain_report*`、`manifest.json`、`run.out`、`run.err`、`stats.txt`、`armtlb_injections.log` 均为只读引用。

## 文档版本（R6-PROPAGATION-NARRATIVE-V3）

- 51 份正文均为七个一级章节：实验身份与复现信息 / 完整故障传播过程 / SDC 诊断分析 / 完整主链事件表 / 相关旁支 / 最终判定与证据完整性 / 原始证据与文件哈希。
- 旧版“30 秒结论”和“一行传播图”已删除；本目录不含这两种结构。
- `analysis tool head` = `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交）。运行期 `manifest.analysis_tool_head` 仍是各 seed 自己的历史值，二者不混用。
- 精确审计：`../r6_reports/R6-PROPAGATION-PATHS-NARRATIVE-AUDIT.{md,json}`（逐文件、逐章、逐事件、逐哈希）。

### 两轴实验状态（chain evidence vs experiment identity）

| 指标 | 数量 |
|---|---|
| 文件总数 | **51** |
| 七章齐全 | **51** |
| 仍含旧章节 | **0** |
| 缺主链叙述 / 单元四列表 / SDC 诊断 | **0 / 0 / 0** |
| chain_evidence_status=PASS | **51** |
| experiment_identity_status=MATCH | **27** |
| experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH | **24** |
| overall_experiment_status=PASS | **27** |
| overall_experiment_status=NOT_MIBENCH_RESULT | **24** |
| overall_experiment_status=REVIEW_REQUIRED | **0** |

`WORKLOAD_IDENTITY_MISMATCH` 的 24 份全部来自 8 个 W1 RunID（T01-F0/F1/F2-W1、T02-F0/F2-W1、T10-F0/F1/F2-W1，各 3 seed）：矩阵标签写 `MiBench-TC23`，但每份 `run.out` 的实际 `--readfile` 都是 `configs/fs/tlb_probe.rcS`。因此：

- 这些文件只证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果；
- 矩阵标签保持原样，未静默改写为 `tlb_probe`，也没有用“实际载体为准”消除身份差异；
- 本轮不自动重跑；补跑真实 MiBench FS workload 作为独立 `WORKLOAD_GAP` 记录。

## 范围与二进制身份

| 二进制 SHA-256 | RunID | 证据根模板 |
|---|---|---|
| `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`（旧冻结二进制） | T01-F0-W4, T02-F0-W4, T02-F2-W4, T04-F0-W4, T04-F2-W4 | `runs/lsu/r6_c9_<RunID>_s3/<RunID>/seed<N>/` |
| `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | T01-F1-W4, T01-F2-W4, T03-F5-W4 | `runs/lsu/r6_n7_<RunID>_s<N>/<RunID>/seed<N>/` |
| `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | T01-F0-W1, T01-F1-W1, T01-F2-W1, T02-F0-W1, T02-F2-W1, T10-F0-W1, T10-F1-W1, T10-F2-W1, T03-F5-W9 | `runs/lsu/r6_n8_<RunID>_s<N>/<RunID>/seed<N>/` |

每个 seed 的权威证据目录与其它目录的分类（EXACT_DUPLICATE / OLD_BINARY_REFERENCE / INTERRUPTED / TRUNCATED / FAILED / ACTIVE / REVIEW_REQUIRED）见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 判定口径

1. 代表故障：权威 checker 的 **escape-first** 规则（`full` > `detected_contained` > `provable_to_*`；同档按可证路径长度、再按 fault id）；
2. `full` ⇒ 终局见证必须是真实 `errant_commit`（`detection_layer=L5`、`outcome=errant_commit`、链关联 corr），**绝不**用生命周期 `chain_end` 冒充 L5；
3. 含住 ⇒ 终局见证必须是真实含住事件（`contained=1` + 显式层/结局 + 链关联 corr）：L2 用 `tlb_translate_result`，L4 用 `squash_masked`；
4. 主链只由 `parent_event_id` 的单祖先构成，每一步都是直接 parent；旁支不得并入主链；
5. 传播链终局与运行结局（oracle: Masked/Crash/Timeout）**分开陈述**。

### 含住 seed 的权威口径（任务已核实事实逐字复现；本批 51 seed 另有 3 个同类 L4 含住 seed）

本批 51 个 seed 中：**44 个 `full`（真实 L5）**，**7 个 `detected_contained`**。任务已核实并逐字复现的 4 个含住 seed 为 T01-F0-W4 seed1/seed3、T01-F2-W4 seed2、T02-F2-W4 seed2；另 3 个 n8 seed（T01-F2-W1 seed2、T02-F2-W1 seed2、T10-F2-W1 seed2）是同类的 L4 `squash_masked` event 68 含住（同一 tick/parent/VA，PA 因故障模型不同而不同），其口径与 T01-F2-W4 seed2 完全同构。

| seed | 权威含住事件 | tick | parent | 层 | reason | 后续层 |
|---|---|---|---|---|---|---|
| T01-F0-W4-seed1 | `tlb_translate_result` event_id=3 | 237950940537 | 2 | L2 | effective_pa_unchanged | L3=N/A; L4=N/A; L5=N/A |
| T01-F0-W4-seed3 | `tlb_translate_result` event_id=3 | 237950233578 | 2 | L2 | effective_pa_unchanged | L3=N/A; L4=N/A; L5=N/A |
| T01-F2-W4-seed2 | `squash_masked` event_id=68 | 238083244768 | 36 | L4 | squash_replay | L5=N/A |
| T02-F2-W4-seed2 | `squash_masked` event_id=68 | 238083244768 | 36 | L4 | squash_replay | L5=N/A |
| T01-F2-W1-seed2 | `squash_masked` event_id=68 | 238083244768 | 36 | L4 | squash_replay | L5=N/A |
| T02-F2-W1-seed2 | `squash_masked` event_id=68 | 238083244768 | 36 | L4 | squash_replay | L5=N/A |
| T10-F2-W1-seed2 | `squash_masked` event_id=68 | 238083244768 | 36 | L4 | squash_replay | L5=N/A |

- T01-F0 seed1/seed3：event_id=2（`tlb_pfn`）**不是**终点；真实含住点是 event_id=3；event_id=4 的 `chain_end` 只是生命周期收口。
- 5 个 L4 含住 seed：权威见证是 **event 68**，不是 1797；event 1797 是同一故障、同一类（L4 squash_replay）但在不同 VA 上更晚的一次含住。原始流另含 event 83 的悬空 `errant_commit`，按 `_errant_commit_escape` 不改变 L4 含住终局。
- T02-F2-W4 seed2 的权威报告是 `chain_report.regrade-20261027T103833.json`；同目录的 plain `chain_report.json` 是 pre-Task-11b 存档，不用于判定。
- **共享注入的唯一合法情形**：T04-F0-W4 seed2 与 seed3 共享同一注入 (tick=237950546931, VA=0xffffff807fbce090, old_pfn=0xffbce→new_pfn=0x81d75)；两份 `prop_evt` SHA-256 不同，是同一确定性注入点的独立运行，不是转抄。其它 RunID 的 seed 之间没有 intra-RunID 共享注入。不同 RunID 之间可能出现相同 (tick, VA)：这是同一确定性 workload/checkpoint 的 eligible 事件（`T03-F5-W9` seed1 与 `T03-F5-W4` seed1 即共享 tick=237951174969、VA=0xffffffc008a16868 的同一确定性注入点，二者 mask 亦相同），但两次运行各自独立、`prop_evt` SHA-256 不同、事件数与注入计数各自计算，不存在转抄；其余跨 RunID 相同 (tick, VA) 的故障值/mask 不同。

## 文件

- 51 个 `<RunID>-seed<N>.md`（见 `INDEX.md`）
- `INDEX.md` / `INDEX.json`：逐 seed 明细 + 12 项校验
- `../R6-AUTHORITATIVE-EVIDENCE.md` / `.json`：每 seed 唯一权威证据目录 + 其它目录分类
- `../r6_reports/R6-PROPAGATION-PATHS-DETAILED-AUDIT.md` / `.json`：逐 seed 12 项审计

## 证据不可变性

- 原始 `prop_evt.txt.gz` / `chain_report*` / `manifest.json` / `run.out` / `run.err` / `stats.txt` 均**未被修改**；本轮未启动 gem5/campaign/scons；未改 checker、准入或守恒逻辑。
- 本轮文档与审计工具的提交见 `git log`（`R6-PROPAGATION-NARRATIVE-V3` 与 `R6-PROPAGATION-AUDIT-V3`）。

## 校验

`INDEX.json → validation` 记录逐 seed 的 12 项检查：事件回查、单祖先 parenting、tick 单调、值取自本 seed、无跨 seed 身份复制、终局匹配权威报告、full 的 L5 真实性、含住事件真实性、人话版与表格一致、唯一合法共享注入（T04-F0-W4 seed2/seed3）、RunID 路径不复用、tier 一致。

## R6-V4 增量（2026-10-28）

本轮新增 **32** 份逐 seed 文档（T 单元 11 个可执行 RunID；`T08-F4-W4` seed3 为
NO_FIRE 非样本，无文档）。总计 **83** 份。增量索引见 [`INDEX-V4.md`](INDEX-V4.md)；
逐格状态见 `../r6_reports/R6-V4-T-STATUS.md`；四子模型覆盖见
`../r6_reports/R6-V4-T08-SUBMODEL-COVERAGE.md`。

两轴口径不变：链证据完整性（每份 = PASS）与实验身份（workload 标签 vs 实际
readfile）分开报告；本轮 W4 载体为 `configs/fs/tlb_probe.rcS`，与矩阵标签
“TLB-AliasPerm 地址翻译探针”一致（同一载体），不构成 W1 那类 mismatch。
