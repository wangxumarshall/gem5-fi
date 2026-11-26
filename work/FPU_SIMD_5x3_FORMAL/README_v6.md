# FPU/SIMD 5×3 最终统计口径与生产者映射修订 v6 交付

- 批次：`FPU_SIMD_5x3_FORMAL`
- 生成：2026-11-24
- 压缩包：`/home/sdc/gem5-fi-fpu/FPU_SIMD_5x3_Final_Acceptance_v6.tar.gz`

> 仅离线导出，未重跑 gem5、未改原始故障模型/Hook/负载/Trace/实验结果。v1–v5 全部保留。

## 交付文件（完整服务器绝对路径）

| 包内文件 | 服务器绝对路径 |
|---|---|
| `1_FPU_5x3_Causal_Edges_Final_v6.csv` | `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Causal_Edges_Final_v6.csv` |
| `2_FPU_5x3_Propagation_Evidence_Final_v6.csv` | `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Propagation_Evidence_Final_v6.csv` |
| `3_FPU_5x3_Propagation_Summary_Final_v6.json` | `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Propagation_Summary_Final_v6.json` |
| `4_FPU_5x3_Final_Acceptance_Report_v6.md` | `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Final_Acceptance_Report_v6.md` |
| `5_FPU_5x3_Producer_Classification_Audit_v6.csv` | `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Producer_Classification_Audit_v6.csv` |
| `6_FPU_5x3_TargetInput_Provenance_Audit_v6.csv` | `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_TargetInput_Provenance_Audit_v6.csv` |
| `7_analyze_5x3_final_v6.py` | `/home/sdc/gem5-fi-fpu/scripts/analyze_5x3_final_v6.py` |
| `README_v6.md` | `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/README_v6.md` |

## 关键结果

### 四类生产者统计（互斥，校验通过）
- ResolvedProducer = 777693
- SquashedProducer = 10323
- InitialStateSource = 411
- UnresolvedProducer = 1665
- TotalSources = 790092（= 四类之和，逐运行 MutuallyExclusive=True）

### Unresolved 四口径
- GlobalUnresolvedProducerCount = 1665
- TargetInputUnresolvedCount = 0
- ReachableUnresolvedDependency = 0
- DownstreamUnresolvedDependency = 0

### GraphComplete 四语义
- TraversalExhausted = 180/180
- TargetInputProvenanceComplete = 180/180
- DownstreamPropagationGraphComplete = 157/180
- FullCausalGraphComplete = 157/180

### 传播证据等级（不相加）
- FaultValueReachedConsumer = 293
- OperandReadVerified = 2110
- UnknownInfluence = 2050

### 180 Fault 终态（原始证据优先）
- WRONG_RESULT 132 · MASKED_OVERWRITE 36 · SQUASHED 12，其余 0
- Control（CONTROL_OK）= 60
- 分类变化 SampleRunID = 0

## 未解决问题清单

1. M011（TBL 向量）32 条传播子图 phys 不匹配边（28 StoreAddress + 4 StoreData），源于 gem5
   向量指令译码为 64-bit 子寄存器微操作、其 phys 与整向量 arch 键不一致——标 UNKNOWN，未猜测。
2. 1665 个全局 UnresolvedProducer（同一子寄存器现象，传播子图外）。
3. M011 readDest 自依赖链标 UnknownInfluence，不视为确认传播。
4. 23 个 M011 运行 DownstreamPropagationGraphComplete=False。

以上均不改变 132/36/12 终态。
