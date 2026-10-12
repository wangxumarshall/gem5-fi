# LSU sheet8「7.展开执行矩阵」逐 RunID 回填草案报告（Subagent F）

- 生成日期：2026-10-12；产物：`/tmp/lsu_backfill_draft.json`（40 条）+ 本报告
- 列映射（sheet8）：Q=Attempted, R=Activated, S=Masked, T=Detected-contained, U=SDC, V=Crash, W=Timeout, X=SDC率, Y=激活率, Z=记录状态, AA=实测备注, AP=Simulator failure（AP 列数值= simfail 字段）
- 数据源（全部实读）：`runs/lsu/pilot_w1/ITEM-*/ITEM-*_result.json`（14 项，权威口径已重算：simulator_assert 单列）；`runs/lsu/pilot/{AGU,Load_Queue}/ITEM-*_result.json`（24 项 COMPLETE）；`docs/gem5-fi/lsu/完整任务执行清单.md`（ITEM→RunID→Excel 行）；`docs/gem5-fi/lsu/evidence/f047-phantom-correction-overlay.jsonl`（019/022/271/279 幻影修正）；`docs/gem5-fi/lsu/evidence/lsqfwd_l03_identity_quarantine.jsonl`（285/287/289）；`runs/lsu/engineering/n5/i287_s0/`（287 准入证据）；每项 s0 `config.ini`（身份核验）

## 1. 汇总表（40 条，按 Excel 行序）

| 行 | ITEM | RunID | 波次 | Att | Act | M | DC | SDC | Cr | To | simfail | 未激活 | 激活率 | SDC率 | 记录状态 | backfill | id_ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | ITEM-001 | A01-F0-W3 | 旧 | 30 | 30 | 13 | 0 | 0 | 0 | 0 | 17 | 0 | 100% | 0% | 已完成(pilot-30) | 是 | 是 |
| 3 | ITEM-002 | A01-F0-W9 | 旧 | 30 | 30 | 17 | 0 | 2 | 0 | 0 | 11 | 0 | 100% | 10.5% | 已完成(pilot-30) | 是 | 是 |
| 4 | ITEM-003 | A01-F1-W3 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 5 | ITEM-004 | A01-F1-W9 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 6 | ITEM-005 | A01-F2-W3 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 7 | ITEM-006 | A01-F2-W9 | 旧 | 30 | 30 | 3 | 0 | 1 | 0 | 0 | 26 | 0 | 100% | 25% | 已完成(pilot-30) | 是 | 是 |
| 8 | ITEM-007 | A02-F0-W3 | 旧 | 30 | 30 | 14 | 0 | 2 | 0 | 0 | 14 | 0 | 100% | 12.5% | 已完成(pilot-30) | 是 | 是 |
| 9 | ITEM-008 | A02-F0-W9 | 旧 | 30 | 30 | 3 | 0 | 1 | 0 | 0 | 26 | 0 | 100% | 25% | 已完成(pilot-30) | 是 | 是 |
| 10 | ITEM-009 | A02-F2-W3 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 11 | ITEM-010 | A02-F2-W9 | 旧 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 14 | ITEM-013 | A04-F0-W3 | 旧 | 33 | 33 | 21 | 0 | 5 | 1 | 0 | 6 | 0 | 100% | 18.5% | 已完成(pilot-30) | 是 | 是 |
| 15 | ITEM-014 | A04-F0-W0 | 旧 | 33 | 33 | 22 | 0 | 8 | 0 | 0 | 3 | 0 | 100% | 26.7% | 已完成(pilot-30) | 是 | 是 |
| 16 | ITEM-015 | A04-F2-W3 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 17 | ITEM-016 | A04-F2-W0 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 18 | ITEM-017 | A04-F6-W3 | 旧 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 19 | ITEM-018 | A04-F6-W0 | 旧 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 20 | ITEM-019 | A05-F0-W3 | 旧 | 33 | 31 | 21 | 0 | 3 | 0 | 0 | 7 | 2 | 93.9% | 12.5% | 已完成(pilot-30,数值待核对) | 是 | 是 |
| 21 | ITEM-020 | A05-F2-W3 | W1 | 30 | 30 | 0 | 0 | 0 | 1 | 0 | 29 | 0 | 100% | 0% | 已完成(pilot-30) | 是 | 是 |
| 22 | ITEM-021 | A05-F6-W3 | 旧 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 23 | ITEM-022 | A06-F0-W3 | 旧 | 33 | 32 | 14 | 0 | 1 | 1 | 0 | 16 | 1 | 97.0% | 6.3% | 已完成(pilot-30,数值待核对) | 是 | 是 |
| 24 | ITEM-023 | A06-F0-W5 | 旧 | 33 | 33 | 19 | 0 | 0 | 0 | 0 | 14 | 0 | 100% | 0% | 已完成(pilot-30) | 是 | 是 |
| 25 | ITEM-024 | A06-F2-W3 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 26 | ITEM-025 | A06-F2-W5 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 27 | ITEM-026 | A06-F6-W3 | 旧 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 28 | ITEM-027 | A06-F6-W5 | 旧 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 35 | ITEM-034 | A08-F0-W3 | 旧 | 33 | 33 | 25 | 0 | 3 | 0 | 0 | 5 | 0 | 100% | 10.7% | 已完成(pilot-30) | 是 | 是 |
| 36 | ITEM-035 | A08-F0-W5 | 旧 | 33 | 33 | 27 | 0 | 0 | 0 | 0 | 6 | 0 | 100% | 0% | 已完成(pilot-30) | 是 | 是 |
| 37 | ITEM-036 | A08-F2-W3 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 38 | ITEM-037 | A08-F2-W5 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 39 | ITEM-038 | A08-F6-W3 | 旧 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 40 | ITEM-039 | A08-F6-W5 | 旧 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 272 | ITEM-271 | L01-F0-W5 | 旧 | 30 | 16 | 9 | 0 | 0 | 0 | 0 | 7 | 14 | 53.3% | 0% | 已完成(pilot-30,数值待核对) | 是 | 是 |
| 275 | ITEM-274 | L01-F1-W5 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 278 | ITEM-277 | L01-F2-W5 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 280 | ITEM-279 | L02-F0-W5 | 旧 | 33 | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 14 | 57.6% | 0% | 已完成(pilot-30,数值待核对) | 是 | 是 |
| 282 | ITEM-281 | L02-F2-W5 | W1 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 100% | n/a(全simfail) | 已完成(pilot-30) | 是 | 是 |
| 284 | ITEM-283 | L02-F6-W5 | 旧 | 33 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 0 | 100% | 0% | 已完成(pilot-30) | 是 | 是 |
| 286 | ITEM-285 | L03-F0-W5 | 旧 | — | — | — | — | — | — | — | — | — | — | — | 已阻塞(模型身份失真,待重跑) | 否 | 否 |
| 288 | ITEM-287 | L03-F4-W5 | 旧 | — | — | — | — | — | — | — | — | — | — | — | 进行中(准入s0完成) | 否 | 是 |
| 290 | ITEM-289 | L03-F6-W5 | 旧 | — | — | — | — | — | — | — | — | — | — | — | 已阻塞(capability-gap) | 否 | 否 |

## 2. 每类计数

- 草案总条数：**40**（Excel 行 2–40、272–290 中本批覆盖 40 行，均唯一、无重复）
- **backfill=true（可回填，含数值列）：37 条**
  - 其中 W1 重跑：14 条（全部 30/30，记录状态=已完成(pilot-30)）
  - 旧波次正常：19 条（记录状态=已完成(pilot-30)）
  - 旧波次修正暂定：4 条（019/022/271/279，记录状态=已完成(pilot-30,数值待核对)）
- **backfill=false（仅填记录状态+实测备注，数值列留空）：3 条**
  - ITEM-285（L03-F0-W5）：已阻塞(模型身份失真,待重跑)
  - ITEM-287（L03-F4-W5）：进行中(准入s0完成)
  - ITEM-289（L03-F6-W5）：已阻塞(capability-gap)
- identity_ok=true：38 条；identity_ok=false：2 条（ITEM-285、ITEM-289——均为 backfill=false，无数值计入）

## 3. 身份一致性核验

核验方法：每项抽查 s0 `config.ini` 的注入器段（CHAOSAddrPath/CHAOSLSQFwd 的 mode/preMode/lsuTier/lsuF6Event/structMode）与 `cmd=` 载体，比对清单 RunID 的模型/频率，并做同 W 指数载体组内一致性检查。

- **W1 14 项**：全部 CHAOSAddrPath，lsuTier 与 RunID F 档一致（F1/F2），mode/preMode 与模型一致（a01_bit/a02_2bit/a04_subst/a05_shift/a06_size/a08_subst/l01_load_addr/l02_load_state），载体全部 = `mibench/bin/w1_all`（D-2026-10-09-重跑 载体改指，RunID 不变）→ identity_ok=true
- **旧波次 23 项（回填数值的）**：全部 CHAOSAddrPath，lsuTier/mode/preMode 与 RunID 一致；载体按 W 指数组内完全一致：W0=mini_check、W3=agu_addrmodes、W5=sq_forward、W9=gap_bfs → identity_ok=true
- **ITEM-285**：CHAOSLSQFwd，lsuTier=F0/载体 sq_forward 一致，但 s0 config.ini 实证 `structMode=byte_flip`、无 l03 参数——模型身份失真（F-047(b)/D-2026-10-10-ITEM285撤销）→ identity_ok=false（本就不回填数值）
- **ITEM-287**：条目事实出自准入新证据 i287_s0（`l03Mode=true`、lsuTier=F4、w1_all、checkViolations_L03 站点 12,843 次真实注入）→ identity_ok=true；旧 300/0 身份失真仅归档
- **ITEM-289**：无有效运行数据可核（旧 300/0 未激活且 lsqfwd 未接线）；RunID↔行映射唯一（row 290）→ identity_ok=false（仅状态记录）
- **平台身份**（findings.md F-030/F-050/F-052 + 当前 build/ARM/gem5.opt sha256 实测 10590f62…）：旧波次 24 项 = gem5 b64c808d 平台；W1 重跑 14 项 = gem5 10590f62 平台（OBS/SEM 重建后，progress.md 2026-10-12 11:00 「身份链 10590f62/adf23d2c 不变」）——两波次数值属不同二进制平台+不同载体，已在实测备注逐条注明，不混数

## 4. 待核对清单

1. **幻影修正暂定值（4 条，overlay 标注 TENTATIVE，逐样本证据确认后方可转最终）**：
   - ITEM-271（L01-F0-W5，行272）：暂定 16/30，Masked 23→9（14 例 pre_filter_rejected_after_trigger 剔除），simfail=7 保留
   - ITEM-279（L02-F0-W5，行280）：暂定 19/33，Masked 33→19（14 例剔除），simfail=0
   - ITEM-019（A05-F0-W3，行20）：暂定 31/33，Masked 23→21（2 例 fault_write_noop 剔除），SDC=3、simfail=7 保留
   - ITEM-022（A06-F0-W3，行23）：暂定 32/33，Masked 15→14（1 例剔除），SDC=1、Crash=1、simfail=16 保留
   - 核对方法：overlay 每条 sample_correction 附 run_dir/seed/evidence_path（addrpath_injections.log、l5_verdict.json）
2. **ITEM-287（L03-F4-W5，行288）**：pilot 数值未采（准入 s0 已 PASS，n=5 其余样本/pilot 待跑）——本条仅状态回填
3. 无「无法唯一映射」项：40 条 ITEM→RunID→Excel 行映射全部唯一（清单 ### 头与 Excel 定位字段逐一提取，行号无冲突）

## 5. 旧波次 24 项 COMPLETE 五类/simfail 分布汇总

### 5.1 回填口径（23 项 = 24 项 COMPLETE − ITEM-285 隔离；019/022/271/279 用修正后数值）

| 指标 | 合计 |
|---|---|
| attempted | 741 |
| activated | 710 |
| Masked | 260 |
| DC | 0 |
| SDC | 26 |
| Crash | 2 |
| Timeout | 0 |
| simfail | 422 |
| not_activated | 31 |

五类可分析合计 = 288；simfail 合计 = 422；可分析+simfail+未激活 = 741 = attempted 合计 741（守恒闭合）。

逐项（att/act | M/DC/SDC/Cr/To | simfail | 未激活）：

| ITEM | RunID | att | act | M | DC | SDC | Cr | To | simfail | 未激活(幻影/无效) |
|---|---|---|---|---|---|---|---|---|---|---|
| ITEM-001 | A01-F0-W3 | 30 | 30 | 13 | 0 | 0 | 0 | 0 | 17 | 0 |
| ITEM-002 | A01-F0-W9 | 30 | 30 | 17 | 0 | 2 | 0 | 0 | 11 | 0 |
| ITEM-006 | A01-F2-W9 | 30 | 30 | 3 | 0 | 1 | 0 | 0 | 26 | 0 |
| ITEM-007 | A02-F0-W3 | 30 | 30 | 14 | 0 | 2 | 0 | 0 | 14 | 0 |
| ITEM-008 | A02-F0-W9 | 30 | 30 | 3 | 0 | 1 | 0 | 0 | 26 | 0 |
| ITEM-010 | A02-F2-W9 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 |
| ITEM-013 | A04-F0-W3 | 33 | 33 | 21 | 0 | 5 | 1 | 0 | 6 | 0 |
| ITEM-014 | A04-F0-W0 | 33 | 33 | 22 | 0 | 8 | 0 | 0 | 3 | 0 |
| ITEM-017 | A04-F6-W3 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 |
| ITEM-018 | A04-F6-W0 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 |
| ITEM-019 | A05-F0-W3 | 33 | 31 | 21 | 0 | 3 | 0 | 0 | 7 | 2 |
| ITEM-021 | A05-F6-W3 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 |
| ITEM-022 | A06-F0-W3 | 33 | 32 | 14 | 0 | 1 | 1 | 0 | 16 | 1 |
| ITEM-023 | A06-F0-W5 | 33 | 33 | 19 | 0 | 0 | 0 | 0 | 14 | 0 |
| ITEM-026 | A06-F6-W3 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 |
| ITEM-027 | A06-F6-W5 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 |
| ITEM-034 | A08-F0-W3 | 33 | 33 | 25 | 0 | 3 | 0 | 0 | 5 | 0 |
| ITEM-035 | A08-F0-W5 | 33 | 33 | 27 | 0 | 0 | 0 | 0 | 6 | 0 |
| ITEM-038 | A08-F6-W3 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 |
| ITEM-039 | A08-F6-W5 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 33 | 0 |
| ITEM-271 | L01-F0-W5 | 30 | 16 | 9 | 0 | 0 | 0 | 0 | 7 | 14 |
| ITEM-279 | L02-F0-W5 | 33 | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 14 |
| ITEM-283 | L02-F6-W5 | 33 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 0 |

### 5.2 原始口径（24 项 result.json 原值，未应用 overlay、含 285）

| 指标 | 合计 |
|---|---|
| attempted | 774 |
| activated | 774 |
| 五类（M/DC/SDC/Cr/To） | 324 / 0 / 26 / 2 / 0（合计 352） |
| simfail | 422 |
| 五类+simfail | 774（= attempted，守恒闭合） |

修正净效应（原始 24 项→回填 23 项）：Masked 324→260（−64 = 285 整项隔离 33 + 幻影/无效剔除 31：271 剔14 + 279 剔14 + 019 剔2 + 022 剔1）；activated 774→710（幻影/无效 31 例转未激活 + 285 隔离 33）；simfail 422→422（271/279/019/022 的 simfail 全保留）；attempted 774→741（仅因 285 整项隔离 −33；overlay 修正本身不改 attempted）。

## 6. W1 重跑 14 项分布（对照）

| 指标 | 合计 |
|---|---|
| attempted | 420 |
| activated | 420 |
| Masked | 0 |
| DC | 0 |
| SDC | 0 |
| Crash | 1 |
| Timeout | 0 |
| simfail | 419 |

13 项 30/30 全 simfail（SE page-table fault panic：故障地址越出映射区，gem5 abort −6），仅 ITEM-020（A05-F2-W3）出现 1 例真实架构 Crash（guest_or_unknown，s22，5 次注入全激活）+29 simfail；五类可分析合计 = 1，SDC率口径下 13 项为 n/a(全simfail)。

## 7. 说明与诚实声明

- 全部数值来自实读文件（result.json 聚合字段、overlay item_summary、清单 Excel 定位），无臆测；修正值由 overlay 样本数（271/279 各 14、019 2、022 1，全部 raw_class=Masked）从原值推导并做守恒断言（全部通过）。
- 旧波次 24 项中 6 项 att=30（AGU 001/002/006/007/008 + LQ 271），18 项 att=33（6×30+18×33=774）；记录状态按任务口径统一「已完成(pilot-30)」，实际 att/act 以数值列为准。
- 287/289/285 数值列留空（backfill=false），仅回填 Z 列记录状态与 AA 列实测备注；AP 列（Simulator failure）随之留空。
- 本草案未改动仓库任何文件；Excel 写入由主 agent 校验后以原子回填工具执行。
