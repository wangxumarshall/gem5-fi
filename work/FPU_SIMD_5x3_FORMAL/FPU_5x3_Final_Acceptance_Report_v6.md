# FPU/SIMD 5×3 最终统计口径与生产者映射验收报告（v6）

批次 `FPU_SIMD_5x3_FORMAL` · 生成 2026-11-24 · 工作目录 `/home/sdc/gem5-fi-fpu`

> 仅离线分析器修订（`analyze_5x3_final_v5.py` → `analyze_5x3_final_v6.py`），未重跑
> gem5、未改原始故障模型/Hook/负载/Trace/实验结果。v1–v5 全部保留。

---

## 1. 修复落实情况

| # | 修复 | 落实 |
|---|---|---|
| 1 | 四分类互斥，消除 ResolvedProducer 与 UnresolvedProducer 重复计数 | ✅ `resolved_producer += 1` 移到物理验证之后；`TotalSources == Resolved+Squashed+Initial+Unresolved` 校验通过 |
| 2 | 生产者状态字段来自真实 commit/squash 事件，不再用 `committed` 误导命名 | ✅ 记录 PriorWriterSeq/Phys/State/Committed/Squashed；未 commit 的推测生产者标 SpeculativeWriter |
| 3 | ReachableUnresolvedDependency 只计 UnresolvedProducer，InitialStateSource 不计入 | ✅ 四口径分离（Global/TargetInput/Reachable/Downstream） |
| 4 | GraphComplete 拆为 TraversalExhausted / TargetInputProvenance / Downstream / Full | ✅ 四语义分别计算 |
| 5 | 传播证据等级保留，不将 OperandReadVerified 与 FaultValueReachedConsumer 相加 | ✅ 分别报告 293/2110/2050 |

## 2. 四类生产者统计（全批 180 个 Fault 运行，互斥）

| 类别 | 数量 |
|---|---:|
| ResolvedProducer | 777693 |
| SquashedProducer | 10323 |
| InitialStateSource | 411 |
| UnresolvedProducer | 1665 |
| **TotalSources（有效源操作数）** | **790092** |

互斥校验：`777693 + 10323 + 411 + 1665 = 790092`，**通过**（每运行 `MutuallyExclusive=True`）。

## 3. 生产者状态字段

每个已解析/Squashed 源操作数记录：PriorWriterSeq、PriorWriterPhys、PriorWriterState
（Committed / Squashed / SpeculativeWriter）、SourcePhys、PhysVerified。Commit 状态来自
真实 `commit` 事件；仅“未 squash”不能判为已提交。目标输入来源 PriorWriterState 分布：
Committed 336 / Squashed 23 / None 1（C05 推测窗口内 load_inputs 被 squash，故部分目标输入
关联 SquashedProducer，如实记录）。

## 4. Unresolved 四口径（不再混淆全局与传播子图）

| 口径 | 数量 |
|---|---:|
| GlobalUnresolvedProducerCount（全 Trace） | 1665 |
| TargetInputUnresolvedCount（目标自身输入） | 0 |
| ReachableUnresolvedDependency（可达子图） | 0 |
| DownstreamUnresolvedDependency（下游） | 0 |

> 1665 个 Global Unresolved 为 M011 向量微操作 64-bit 子寄存器 phys 与整向量 arch 键
> 不一致（子寄存器/别名关系不足以验证），均如实标 UnresolvedProducer，未猜测；全部落在
> 故障传播子图之外，故 Reachable/Downstream 为 0。

## 5. GraphComplete 四语义

| 语义 | 数量 |
|---|---:|
| TraversalExhausted（BFS 队列耗尽） | **180/180** |
| TargetInputProvenanceComplete（目标输入来源充分） | **180/180** |
| DownstreamPropagationGraphComplete（下游无未解析/phys 不匹配/UNKNOWN） | **157/180** |
| FullCausalGraphComplete | **157/180** |

> 23 个非完整运行全部为 M011（向量 TBL 微操作的 32 条 phys 不匹配边 + renamed-not-executed
> 尾部），已按“证据不足标 UNKNOWN”处理，不因队列耗尽误判为完整。

## 6. 传播证据等级（不相加）

| 术语 | 数量 |
|---|---:|
| FaultValueReachedConsumer（直接消费者读取故障目标错误写回值） | **293** |
| OperandReadVerified（生产者写回值 == 消费者读取值，不表故障已影响输出） | **2110** |
| UnknownInfluence（证据不足/无法确认） | **2050** |

> 三者分别报告，不再相加称“已确认错误传播”。StoreAddressDependency 不计入数据传播；
> StoreDataDependency 仅在有明确数据源 phys 关联时确认。

## 7. 180 Fault 终态（原始证据优先，未为保证数字改判定）

| 终态 | 数量 |
|---|---:|
| WRONG_RESULT | **132** |
| MASKED_OVERWRITE | **36** |
| SQUASHED | **12** |
| INJECTION_MISS / PARTIAL_TRACE / OUTPUT_MISMATCH / OTHER | **0** |
| Control（CONTROL_OK） | 60 |

**分类变化 SampleRunID：0 个**（逐 Sid 比对 v5/v6 无翻转）。180 个 SampleRunID 全部存在，
60 个 Control 正确配对。

## 8. 交付文件（8 个）

| 文件 | 位置 |
|---|---|
| `FPU_5x3_Causal_Edges_Final_v6.csv`（4453 条边） | `.../work/FPU_SIMD_5x3_FORMAL/` |
| `FPU_5x3_Propagation_Evidence_Final_v6.csv`（180 行） | 同上 |
| `FPU_5x3_Propagation_Summary_Final_v6.json` | 同上 |
| `FPU_5x3_Final_Acceptance_Report_v6.md`（本报告） | 同上 |
| `FPU_5x3_Producer_Classification_Audit_v6.csv`（180 行） | 同上 |
| `FPU_5x3_TargetInput_Provenance_Audit_v6.csv`（360 行） | 同上 |
| `analyze_5x3_final_v6.py` | `/home/sdc/gem5-fi-fpu/scripts/` |
| `README_v6.md` | 随包 |

## 9. 最终验收结论与未解决问题

**结论**：四类生产者统计互斥且 TotalSources 校验通过；ReachableUnresolvedDependency
真实计算（=0，1665 全局 Unresolved 均为传播子图外的子寄存器现象）；GraphComplete 四语义
有实际计算证据（Traversal 180/180、Downstream/Full 157/180）；180 Fault + 60 Control 终态
与原始证据一致（132/36/12），分类变化 0。

**未解决问题（均已如实标 UNKNOWN，未猜测）**：
1. M011（TBL 向量）32 条传播子图 phys 不匹配边（28 StoreAddress + 4 StoreData），源于
   gem5 将向量指令译码为 64-bit 子寄存器微操作、其 phys 与整向量 arch 键不一致。
2. 1665 个全局 UnresolvedProducer（同一子寄存器现象，传播子图外）。
3. M011 readDest 自依赖链（tbl 将目的寄存器同时列为 source）标 UnknownInfluence，不视为
   确认传播。
4. 23 个 M011 运行 DownstreamPropagationGraphComplete=False（含 renamed-not-executed 尾部）。

以上均不改变 132/36/12 终态。