SHEET 16_CURRENT_Readme dims=A1:B19 rows=19 cols=2
R1: Item | Current plan / source caveat
R2: 当前方案 | MMU/ARM O3CPU · When/How 5×3 补充实验设计（不替换冻结的 MMU 正式实验）
R3: 来源文件 | 用户上传 MMU Final Design v2.0；源文件 00–15 工作表保存作归档，Source Mapping/Where 原样不修改
R4: 正式完成证据 | MMU_FORMAL_CAMPAIGN_20261113；40/40 原有 R01–R05 上下文已执行，证据来自 MMU_40_Context_Evidence_Atlas.csv
R5: 正式结果 | 31 SDC / 5 DETECTED_CONTAINED / 4 SQUASHED；36 FULL / 4 PARTIAL；40 COMPLETE
R6: Where 冻结 | M01–M08 的 FaultType/TargetSubUnit/SourceHook/TargetField/Bit/Operation/Duration 全部引用 05_Injection_Configuration，禁止改动
R7: When 新矩阵 | 8 个模型 × 5 类机制性 Context(C01–C05) × 3 个动态注入时机(T01=10%,T02=50%,T03=90%) = 120 个新的计划条件
R8: Control 原则 | 每个模型/Context 一条可覆盖整个 ROI 的无故障执行基线：最多 40 次新 Control；通过配置、输入与轨迹一致性验证后复用
R9: 规模口径 | 120 Fault + 最多 40 Control = 160 次新运行的计划上限；Pilot、异常重跑另计；既有 40 正式运行不重复统计
R10: 时间采样定义 | 每个 (Model,Context) 在 NoFault 预扫描下枚举满足冻结 Where 谓词的 eligible events，3 个分位按 ceil(p*N) 取序号，N≥3 且不重复
R11: 时机边界 | 10/50/90 是动态事件位置，不代表硬件状态。实际状态需记录并核实；任一目标触发前不得被其他故障改变候选序列
R12: 完成情况 | 新 5×3 矩阵是研究者新计划，所有行 NOT_RUN；不可将 40 个已经完成的 R01–R05 偷换成 T01–T03
R13: 上下文覆盖 | C01 基准、C02 访问/激活变体、C03 弱消费/隔离、C04 深依赖、C05 控制/推测；每模型由 19_Context_5x8 定义，个别不适用记 N/A
R14: 故障类型边界 | M06 会因 descriptor 失效产生 Translation Fault；M07 是权限授予错误，不能强求它们产生‘数据污染被掩盖’的路径
R15: 执行路径 | 0202 既有冻结工作区 /home/sdc/gem5-fi-mmu-impl-v2（只读保护）；新方案只能在独立工作副本及独立结果目录执行
R16: M07 R03/R05 修正 | 正式 R03=PROT_EXEC execute-only + EL0 Read；R05=有效 XN (PROT_READ, UXN=1) + indirect branch；保留旧稿只作历史
R17: Execute 可观测边界 | 若仅证明 MMU Execute 请求而未采集 IFU response/decode/commit，则禁止据此声称端到端 IFU/架构传播完成
R18: 版本约束 | 本工作簿是 2026-11-16 的增补设计；不声称它已经在服务器上运行、验收或替换原正式 MMU 成果
R19: 重要入口 | 17_Legacy_Formal40=既有证据；19_Context_5x8=具体新上下文；20_When_5x3_120=执行矩阵；23/24=How；26_Runtime=时间
