# gem5-fi-FSU单元故障注入方案_逐RunID传播监控（Markdown 转换版）

<!-- fsu-xlsx2md-metadata
Source-File: gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx
Source-SHA256: 4a5b358cb6e12d93f5b25ed0b422c6100a30540c0693482c04af904669b22cd6
Source-MTime-Local: 2026-11-02T10:52:55
Source-Size-Bytes: 95572
Generated-At-Local: 2026-11-02T11:08:33
Sheet-Count: 12
RunID-Count-Sheet7: 173
RunID-Count-Sheet9: 173
RunID-Sets-Equal: true
Tool: tools/fsu_xlsx_to_md.py
-->

> 本文档由上述 SHA256 对应的 xlsx 工作簿**自动完整转换**生成；源文件未被修改。
> 转换规则：单元格换行→`<br>`；`|`→`\|`；全宽合并横幅→`### 分节横幅`；空行→`<!-- blank-row -->`；尾部全空行不列出（各节注记披露）；隐藏行列内容仍完整列出。

## 目录

| # | 工作表 | 规模 | 位置 |
|---|--------|------|------|
| 0 | 0.说明与总览 | 8 列 × 21 行 | [本文 0.说明与总览](#sheet-0) |
| 1 | 1.单元与现有研究 | 7 列 × 8 行 | [本文 1.单元与现有研究](#sheet-1) |
| 2 | 2.FSU参数基线 | 6 列 × 25 行 | [本文 2.FSU参数基线](#sheet-2) |
| 3 | 3.位置x模型矩阵 | 15 列 × 35 行 | [子文档 gem5-fi-FSU单元故障注入方案_逐RunID传播监控-03-位置x模型矩阵.md](gem5-fi-FSU单元故障注入方案_逐RunID传播监控-03-位置x模型矩阵.md) |
| 4 | 4.观测点定义 | 7 列 × 11 行 | [本文 4.观测点定义](#sheet-4) |
| 5 | 5.频率与统计 | 7 列 × 21 行 | [本文 5.频率与统计](#sheet-5) |
| 6 | 6.负载清单 | 7 列 × 16 行 | [本文 6.负载清单](#sheet-6) |
| 7 | 7.展开执行矩阵 | 25 列 × 178 行 | [子文档 gem5-fi-FSU单元故障注入方案_逐RunID传播监控-07-展开执行矩阵.md](gem5-fi-FSU单元故障注入方案_逐RunID传播监控-07-展开执行矩阵.md) |
| 8 | 8.文献与来源 | 8 列 × 16 行 | [本文 8.文献与来源](#sheet-8) |
| 9 | 9.逐RunID传播监控 | 17 列 × 174 行 | [子文档 gem5-fi-FSU单元故障注入方案_逐RunID传播监控-09-逐RunID传播监控.md](gem5-fi-FSU单元故障注入方案_逐RunID传播监控-09-逐RunID传播监控.md) |
| 10 | 10.源码监控映射 | 10 列 × 31 行 | [子文档 gem5-fi-FSU单元故障注入方案_逐RunID传播监控-10-源码监控映射.md](gem5-fi-FSU单元故障注入方案_逐RunID传播监控-10-源码监控映射.md) |
| 11 | 11.传播事件字段规范 | 5 列 × 26 行 | [本文 11.传播事件字段规范](#sheet-11) |

<a id="sheet-0"></a>
## 0.说明与总览
> 8 列 × 21 行；非空单元格 42

<!-- blank-row -->

### 分节横幅：FSU 故障注入方案 - 总览

### 分节横幅：范围：FP/SIMD Issue Queue、FP/SIMD PRF、FSU Pipe。基于 ARM64 参考表、IEX/OOO 口径与 gem5-fi fi-ding 本地快照。

<!-- blank-row -->

| 项目 | 统一约定 | 边界/备注 |  |  |  |  |  |
|---|---|---|---|---|---|---|---|
| 研究目标 | 按FSU功能语义建立可执行的位点×故障模型×频率×负载矩阵，并为每个RunID定义完整传播链监控。 | 设计方案不等于所有源码hook已实现；“实现状态”列如实区分直接已有/部分已有/需新增。 |  |  |  |  |  |
| 单元划分 | FP/SIMD Issue Queue；FP/SIMD PRF；FSU Pipe。 | 来自ARM64 微架构SDC敏感性参考表，三者均为红色高价值注入对象。 |  |  |  |  |  |
| 基线平台 | gem5 ArmO3CPU，AArch64，128-bit NEON，2条FP/SIMD执行资源代理，单线程主基线。 | 不声称精确复刻鲲鹏920商用核；C2/KP920 proxy用于结构敏感性。 |  |  |  |  |  |
| 实验规模 | 30个主模型，173个唯一RunID，F0-F5六类事件归一化频率，11组负载。 | RunID主键=FSU-模型ID-频率-负载；子模型作为预注册分层而非另一条无追溯记录。 |  |  |  |  |  |
| 采样原则 | 先countOnly统计N_eligible，再由seed在可损坏事件流中均匀抽取ordinal；F1-F4按run cluster统计。 | 不得将eligible=0的负载当作Masked；不得将同一run内多个故障事件当成独立样本。 |  |  |  |  |  |
| 统计目标 | 每个RunID先取30个activated工程预试，稳定后累计至385个activated；预登记重点组合可累计至2401。 | 报告attempted/eligible/activated/simulator failure/outcome/detector和Wilson 95%CI。 |  |  |  |  |  |
| 传播完整性 | 完整链必须存在L0 fault_applied，每条边由fault_id/ptag、event_id/parent_event_id和dyn_seq/producer-consumer可达性共同证明，并终止于：(1) errant commit/错误寄存器或内存副作用/oracle差异；(2) 明确检出并contained；或(3) 明确squash/replay/overwrite/mask且证明无错误副作用。任一中间节点缺事件只能标Unknown，不得由最终hash正确推断Masked。 | 无后续日志不等于Masked；链路中断必须标Unknown。 |  |  |  |  |  |
| 源码事实源 | 本地fi-ding快照中的CHAOSIQ/CHAOSPhysReg/CHAOSFPU/tools/runner.py/CHAOSPropagation。 | GitHub页面本次无法直接读取；源码审计标识：ZIP-SHA256:FD6433265F4683604AFDD59188D81D1ECD391E2BC32A899499702BF43421C960 (2026-10-31 local fi-ding snapshot) |  |  |  |  |  |
|  |  |  |  |  |  |  |  |

### 分节横幅：关键数量

| 主模型 | 30 |  |  |  |  |  |  |
|---|---|---|---|---|---|---|---|
| RunID | 173 |  |  |  |  |  |  |
| 单元 | 3 |  |  |  |  |  |  |
| 频率档 | 6 |  |  |  |  |  |  |
| 负载组 | 11 |  |  |  |  |  |  |
| 传播层级 | 6 |  |  |  |  |  |  |

注：合并单元格：A3:H3, A2:H2, A15:H15（全宽横幅已作分节标题；其余仅锚单元格有值）。

<a id="sheet-1"></a>
## 1.单元与现有研究
> 7 列 × 8 行；非空单元格 30

<!-- blank-row -->

### 分节横幅：FSU 单元与现有研究

### 分节横幅：将ARM64参考表中的3类FSU对象映射到gem5可执行对象和本方案增量。

<!-- blank-row -->

| 单元 | 功能语义 | 现有研究 | 现有结果/判定 | 研究空白 | 现有gem5-fi能力 | 本方案增量 |
|---|---|---|---|---|---|---|
| FP/SIMD Issue Queue | 等待FP/向量操作数就绪，执行wakeup/select/issue和FSU资源竞争。 | 参考表无直接FSU IQ论文结果；但结构与调度器的flop/CAM风险一致。 | 参考表对五类ARM核均判为红色高价值。 | 缺少FP/SIMD激活条件下的tag/ready/wakeup逐边传播数据。 | 现有CHAOSIQ targetClass=vec/fpOnly可直接覆盖部分tag/ready/wakeup模型。 | 增加FSU_PROP源事件、Vec受害者限定、issue/FU grant/生命期链。 |
| FP/SIMD PRF | 保存AArch64标量FP与NEON向量实际数据，宽于整数PRF且具有lane语义。 | 参考表指出TC'23因负载无FP未注入；IISWC'15工具支持但无报告结果。 | 五类ARM核均判红；920f的512-bit SVE/SME数据面进一步放大面积风险。 | 缺少真实Vec consumer、lane、物理槽世代和旁路/局部写合并证据。 | 现有CHAOSPhysReg支持VecRegClass、8/16/32/64-bit lane、bit flip和stuck-at。 | 增加PRF_READ/WB_TXN/LANE_MERGE事件，按dyn_sn/src_slot连到consumer和commit。 |
| FSU Pipe | 执行标量FP、NEON/SIMD add/mul/FMA/div/sqrt等运算，并产生结果与FPSR候选。 | 参考表汇总Veritas、ETS'24、Harpocrates；GEMM/SVD/sparse/FFT等FP密集负载敏感性显著。 | 向量单元的相对风险显著高于标量整数加法器，但文献主要是x86门级注入。 | 缺少ARM NEON的lane、FPCR/FPSR、FMA中间语义和完成/写回配对研究。 | 现有CHAOSFPU可直接实施结果bitseg、加权FMA代理、recurring stuck、rounding和指数窗。 | 扩展全128-bit lane、operand/control/completion hook并接入FSU_PROP。 |

注：合并单元格：A3:G3, A2:G2（全宽横幅已作分节标题；其余仅锚单元格有值）。

<a id="sheet-2"></a>
## 2.FSU参数基线
> 6 列 × 25 行；非空单元格 128

<!-- blank-row -->

### 分节横幅：FSU 参数基线

### 分节横幅：主基线优先可复现和功能语义；商用核参数仅作结构敏感性，不冒充精确复刻。

<!-- blank-row -->

| 结构/参数 | B0最终值 | 处理 | 依据/合理性 | 敏感性配置 | 边界说明 |
|---|---|---|---|---|---|
| CPU/ISA | ArmO3CPU / AArch64 | B0主基线 | fi-ding现有arm_chaos/kp920_proxy可执行 | C2=KP920 proxy作结构敏感性 | 不声称与商用鲲鹏920一致 |
| CPU频率 | 2.6 GHz proxy | B0 | kp920_proxy时钟口径；注入窗使用CPU clockPeriod换算 | S0=2.0 GHz；S1=3.0 GHz | F0-F5是故障事件频率，不是CPU频率 |
| 线程 | 1 | B0 | SMT会混入共享IQ/PRF/FU归属 | S2=2 threads单独研究 | SMT不进入主结论 |
| fetch/decode/rename width | 3/3/3 | B0 | O3_ARM_v7a_3/kp920 proxy可复现 | S3=4/4/4 | FSU结果需与eligible密度同时报告 |
| dispatch width | 6 | B0 | kp920 proxy参数 | S4=4/8 | 影响FP-IQ入队密度 |
| issue/writeback/commit width | 8/8/8 | B0 | O3宽发射代理 | S5=4/4/4 | FSU资源仍由FUPool/opClass约束 |
| ROB entries | 40 | B0 | O3_ARM_v7a_3可复现 | S6=64/128 | 用于改变FP长延迟操作在飞深度 |
| IQ entries | 32（gem5共享IQ，以Vec source/opClass逻辑切分FSU人群） | B0 | CHAOSIQ targetClass=vec/fpOnly | S7=16/64 | gem5无独立硬件FP-IQ阵列；必须标为proxy population |
| numPhysFloatRegs | 192 | B0 | kp920_proxy已配置 | S8=128/256 | AArch64标量FP实际重命名路径主要是VecRegClass |
| numPhysVecRegs | 48 | B0 | ooo_proxy北极星向量PRF参数 | S9=32/64/256 | PRF物理索引域必须从实际配置读取 |
| 向量宽度 | 128-bit NEON | B0 | ARM64参考表对鲲鹏920指向AArch64 NEON；无SVE | S10=SVE128/512（仅后续敏感性） | CHAOSFPU现代码主要修改低64 bit，是明确待补缺口 |
| lane宽分层 | 8/16/32/64 bit | B0实验维度 | CHAOSPhysReg已支持vecLaneWidth/Offset | N/A | lane选择必须限于active lane |
| FP/SIMD FU | 2条执行资源proxy | B0 | kp920_proxy的double FSU/FUPool语义 | S11=1/3 | opClass延迟3–33 cycles，以实际FUDesc为准 |
| opClass范围 | FloatAdd/Cmp/Cvt/Mult/MultAcc/Div/Misc/Sqrt + SimdFloat* | B0 | CHAOSFPU::isFpOpClass | N/A | integer SIMD不fpOnly定义的关系需在每个模型明示 |
| 触发采样 | countOnly N_eligible → fixed uniform eventsToSkip | B0 | CHAOSFPU/CHAOSIQ已支持 | legacy geometric仅做回放对照 | maxFaults=1时禁止默认总落在前几个eligible |
| 时间窗 | firstClock=warm-up后；lastClock=0 | B0 | inWindow使用CPU clockPeriod | 按checkpoint定制firstClock | lastClock不作窄窗，避免零注入 |
| 单故障限制 | maxFaults=1 | F0主基线 | run-level因果简洁 | F1-F4用cluster定义 | F5使用maxFaults=0+固定mask持续暴露 |
| 随机数 | selection_seed固定清单；跨模型common random numbers | B0 | runner/manifest已有rngSeed | N/A | seed、eligible ordinal、bit/lane/候选域必须入日志 |
| 保护基线 | none | B0 | ARM64参考表未披露FSU IQ/PRF/Pipe ECC/parity | S12=理想检测/重放仅作对照 | 不得将ROB异常/软件oracle写成硬件RAS |
| 结局分类 | Masked / Detected-contained / Data Corruption / Crash / Timeout / Simulator failure | B0 | IEX/OOO一致口径 | N/A | SDC与首检层级二维分开 |

注：合并单元格：A3:F3, A2:F2（全宽横幅已作分节标题；其余仅锚单元格有值）。

<a id="sheet-4"></a>
## 4.观测点定义
> 7 列 × 11 行；非空单元格 51

<!-- blank-row -->

### 分节横幅：FSU 观测点定义

### 分节横幅：层级是传播证据顺序，不是预设结局；任何结局均需有可达性链证据。

<!-- blank-row -->

| 层级 | 名称 | 定义 | 必须采集量 | 建议实现点 | 判定规则 | 最小输出 |
|---|---|---|---|---|---|---|
| L0 | 故障施加 | 对eligible对象施加故障并产生根event_id/ptag。 | run/sample/fault/event、tick/cycle、sn/PC/opcode、model/submodel、target/old-new/mask/lane、attempted/eligible/activated | CHAOSIQ/CHAOSPhysReg/CHAOSFPU的fault_applied处 | 证明真正改变有效状态；零注入不是Masked | FSU_EVT kind=fault_applied |
| L1 | 直接载体 | 错误已进入IQ entry、Vec PRF、FU输入/控制或结果。 | IQ slot/src tag/ready；phys reg/generation/lane；A/B/C/opClass/FU/FPCR/result/FPSR | inst_queue/regfile/DynInst execute前后 | 区分被写入但未消费的潜伏故障 | FSU_EVT kind=carrier_state |
| L2 | 首个消费/仲裁 | 错误tag/ready/值/控制被select、issue、read或FU接收。 | producer-consumer sn、src slot、read value/lane hash、ready rank、FU grant/accept、issue tick | scheduleReadyInsts/getRegOperand/IEW issue/FUPool | 定义真正传播而不是仅写入存储位 | FSU_EVT kind=consumer_read/issue |
| L3 | 执行与写回 | 错误影响FSU结果、延迟、completion、lane mask、Vec PRF或FPSR候选。 | FU/opClass、expected/actual latency、correct/fault result hash、dest tag、WB txn、ready/wakeup、FPSR delta | DynInst::execute/FUCompletion/IEW writeback/regfile | 证明错误已产生后续可见载荷 | FSU_EVT kind=execute_result/writeback |
| L4 | 下游扇出与恢复 | 污染值被其他FP/整数/地址/存储/分支消费，或被squash/replay/overwrite。 | consumer edge、branch/address/store side effect、squash id/reason、replay、overwrite/free、containment evidence | IQ/LSQ/branch/commit squash/rename release | 证明扇出范围或明确contained；不得根据无日志推断 | FSU_EVT kind=fanout/containment |
| L5 | 提交与最终结局 | 错误达到架构V/FPSR、内存/控制副作用、异常、软件oracle或终端超时。 | commit_seq/PC/opcode/dest+value hash/FPSR、first divergence、Hardware RAS/OS/Application/None首检、outcome | CommitTrace/commit.cc + offline oracle join | 二维报告首检层和最终结局 | FSU_EVT kind=errant_commit/chain_end + offline join |

注：合并单元格：A3:G3, A2:G2（全宽横幅已作分节标题；其余仅锚单元格有值）。

<a id="sheet-5"></a>
## 5.频率与统计
> 7 列 × 21 行；非空单元格 107

<!-- blank-row -->

### 分节横幅：FSU 故障频率与统计规则

### 分节横幅：频率以各模型eligible FSU event归一化；cycle仅用于warm-up/换算，F0与F1-F5不混成一个“故障率”。

<!-- blank-row -->

| 档位 | 名称 | 定义 | 适用故障 | 设计意图 | 统计单位 | FSU注意事项 |
|---|---|---|---|---|---|---|
| F0 | 单次瞬态 | 每次运行只注入1次；warm-up后在本模型eligible event中均匀抽样 | 单/双bit、换值、单事件状态 | 论文对照与主AVF/SDC基线 | run-level独立样本 | 使用countOnly+fixed uniform ordinal；时序/多lane模型按run cluster报告 |
| F1 | 低频事件归一化 | 平均每1,000,000个eligible events注入1次，间隔±50%抖动 | 稀疏瞬态 | 跨负载对比与稀疏场景 | run-level cluster | 使用countOnly+fixed uniform ordinal；时序/多lane模型按run cluster报告 |
| F2 | 中频事件归一化 | 平均每100,000个eligible events注入1次，间隔±50%抖动 | 瞬态/结构化数据 | 定位SDC/Crash转折 | run-level cluster | 使用countOnly+fixed uniform ordinal；时序/多lane模型按run cluster报告 |
| F3 | 高频压力 | 平均每10,000个eligible events注入1次，间隔±50%抖动 | 瞬态压力组 | 仅作上界，不与单故障AVF混合 | run-level cluster | 使用countOnly+fixed uniform ordinal；时序/多lane模型按run cluster报告 |
| F4 | 短突发/时序窗 | 每100,000个eligible events触发一次，连续污2–4个事件或单事件±1周期 | 时序/共享控制/lane burst | 模拟短时持续与事件抖动 | run-level cluster | 使用countOnly+fixed uniform ordinal；时序/多lane模型按run cluster报告 |
| F5 | 永久卡死 | warm-up后第一个eligible event起到运行结束；每运行固定1 bit/字段/极性 | stuck-at/固定mask | 持久缺陷与重复暴露 | run-level独立样本 | 仅正确值与卡死极性不同时activated；按物理槽世代记暴露 |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
| 统计项 | 规则/公式 | 目的 | 备注 | 报告字段 | 区间 | 审计 |
| 分母 | eligible/attempted；activated/eligible；可分析=activated−Simulator failure；条件SDC=SDC/可分析activated | 同时报告四类计数 | 禁止将未触发FP/SIMD的负载当Masked | attempted/eligible/activated/outcome/detector | Wilson 95%CI或cluster bootstrap | 固定seed+配置hash |
| 工程预试 | 每个RunID先获得30个独立activated runs/clusters | 检查触发、日志、oracle和链路 | injector/配置/负载/checkpoint/oracle改变后作废重采 | attempted/eligible/activated/outcome/detector | Wilson 95%CI | 固定seed+配置hash |
| 常规样本 | 385个独立activated；最坏p=0.5时95%CI半宽约5pp | 全部RunID统一筛查精度 | F1-F4按运行聚类计算区间 | outcome/detector/chain completeness | Wilson 95%CI/cluster bootstrap | 不得序贯停止 |
| 重点样本 | 预登记重点组合累计到2401个activated | 最坏绝对误差约2pp | 在看结果前冻结；2401包含前385 | same as above | Wilson 95%CI | 不用于所有RunID |
| 随机化 | seed、entry/phys/FU、bit/field/lane、eligible ordinal分层随机；跨模型用common random numbers | 减少程序相位/槽位/寄存器热点偏差 | 合法换值必须保存候选集大小和实际source-target | seed/ordinal/target/candidate set | N/A | manifest+config hash |
| 超时 | golden sim time或committed inst的10倍，并设绝对上限 | 区分慢化与死锁 | F5和wake-lost可预注册更高上限 | timeout evidence + last chain node | run-level | 不得将host/simulator失败当故障Timeout |
| 传播完整性 | 完整链必须存在L0 fault_applied，每条边由fault_id/ptag、event_id/parent_event_id和dyn_seq/producer-consumer可达性共同证明，并终止于：(1) errant commit/错误寄存器或内存副作用/oracle差异；(2) 明确检出并contained；或(3) 明确squash/replay/overwrite/mask且证明无错误副作用。任一中间节点缺事件只能标Unknown，不得由最终hash正确推断Masked。 | 让比例仅基于可证链路 | Unknown单独报告 | L0-L5 node/edge count + terminal | exact audit | run_id与工作簿一一对应 |

注：合并单元格：A3:G3, A2:G2（全宽横幅已作分节标题；其余仅锚单元格有值）。

<a id="sheet-6"></a>
## 6.负载清单
> 7 列 × 16 行；非空单元格 86

<!-- blank-row -->

### 分节横幅：FSU 负载清单

### 分节横幅：先用定向负载保证eligible/activated和字段级oracle，再用数值程序、Embench和真实应用提供外部有效性。

<!-- blank-row -->

| 负载ID | 名称 | 类型 | 定义/输入与oracle | 主要覆盖单元 | 模式 | 使用边界 |
|---|---|---|---|---|---|---|
| W0 | FSU-MiniCheck | 自设最小探针 | FP32/FP64加乘除开方/FMA、NEON lane、依赖链和特殊值；位级结果+FPSR+终态hash | 全部FSU；注入器冒烟 | SE | 先验证eligible/activated与日志合同，不用于外部有效性 |
| W1 | FP-ScalarProbe | 自设定向 | FP32/FP64 add/sub/mul/div/sqrt/FMA；NaN/Inf/±0/subnormal；4种舍入；位级结果和FPSR/FPCR oracle | PRF、Pipe | SE | 需禁止编译器将所有运算折叠为常量 |
| W2 | FP-IQ-Dependency | 自设定向 | FP/NEON长短RAW链、fan-out/fan-in、双源非交换操作、多ready竞争、mispredict后消费者；逐边oracle | Issue Queue、PRF | SE | 调节指令间距保证一定的FP IQ占用和竞争 |
| W3 | NEON-LaneProbe | 自设定向 | 8/16/32/64-bit lane，整数/浮点AdvSIMD，extract/insert、widen/narrow、permute、reduce；逐lane比对 | IQ、PRF、Pipe | SE | 基线为128-bit NEON；SVE只作后续敏感性 |
| W4 | FMA-DotProduct | 定向数值 | 复用elemwise_fma_kernel，覆盖FMA、dot-product、累加依赖和正负消去；array hash+容差/ULP oracle | Pipe主要 | SE | FMA中间信号在gem5中是行为代理，必须显式标注proxy |
| W5 | PolyBench-FP | 公开通用 | gemm、2mm、lu、cholesky、jacobi-2d；固定规模；输出数组逐元素+容差+哈希校验 | IQ、PRF、Pipe与长依赖链 | SE | 主结果负载；每个子程序独立报告eligible和activated |
| W6 | SVD-FFT-Sparse | 数值应用组 | 复用svd_iterative_kernel，并固定FFT/IFFT、稀疏线性系统输入；残差+数组hash oracle | PRF、Pipe | SE | 与Veritas/ETS参考表中高激活数值类对齐 |
| W7 | FP-ExceptionRecovery | 自设定向 | invalid/div0/overflow/underflow/inexact与branch mispredict、squash、精确恢复交叉；FPSR、目的寄存器和commit边界oracle | IQ、Pipe时序与控制 | SE+FS子集 | 必须记录异常是真实产生、被抑制还是伪造 |
| W8 | Embench-FP-Selected | 公开通用 | 先做opClass/eligible普查，仅保留实际执行FP/NEON的Embench子项；使用内置校验和输出hash | 参考表指定的FSU通用负载 | SE | eligible=0的子项不得当作Masked |
| W9 | libjpeg-turbo-NEON | 真实应用 | 固定图像压缩/解压，启用AArch64 NEON；逐像素、文件hash和格式合法性校验 | PRF、Pipe、lane传播 | SE/FS | 需锁定libjpeg-turbo版本、编译选项和输入图像 |
| W10 | SPEC CPU2017 FP SimPoint | 公开通用（需许可） | 优先lbm/cam4/fotonik3d等FP子项，固定SimPoint/checkpoint，reference输出校验 | 外部有效性 | SE/FS | 只在定向与PolyBench主结果完成后复核 |

注：合并单元格：A3:G3, A2:G2（全宽横幅已作分节标题；其余仅锚单元格有值）。

<a id="sheet-8"></a>
## 8.文献与来源
> 8 列 × 16 行；非空单元格 71

<!-- blank-row -->

### 分节横幅：FSU 文献与来源

### 分节横幅：工作簿中的结构判定、故障模型和源码能力均对应到这里的证据。

<!-- blank-row -->

| 代码 | 标题/资源 | 类型/发表 | 核对方式/定位 | 本工作簿用途 | URL/定位 |  |  |
|---|---|---|---|---|---|---|---|
| ARM64-REF | ARM64_微架构SDC敏感性_故障注入20260921.xlsx | 本地参考工作簿 | FSU行28-30；SDC判定行26-28；统一负载/故障类型 | 定义三类FSU单元、红色价值、Embench/PolyBench和翻转/卡死/换值边界 |  |  |  |
| IEX-BASE | gem5-fi-IEX单元故障注入方案_逐RunID传播监控.xlsx | 本地模板 | Issue Queue/PRF/Pipe结构化分解、F0-F5和逐RunID监控列 | 复用口径与表格形式，不复制整数语义 |  |  |  |
| OOO-BASE | gem5-fi-OOO单元故障注入方案_逐RunID传播监控.xlsx | 本地模板 | FP/SIMD Decode/Rename/Dispatch的lane、FPCR/FPSR、squash/commit链 | 补充FP/SIMD控制和传播字段语义 |  |  |  |
| GEM5-FI | wangxumarshall/gem5-fi fi-ding | 源码快照/GitHub | ZIP-SHA256:FD6433265F4683604AFDD59188D81D1ECD391E2BC32A899499702BF43421C960 (2026-10-31 local fi-ding snapshot)；本地包无.git元数据 | CHAOSIQ/CHAOSPhysReg/CHAOSFPU/runner/PROP-EVT事实源 | https://github.com/wangxumarshall/gem5-fi/tree/fi-ding |  |  |
| CHAOSFPU | CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.{py,cc,hh} | 源码 | isFpOpClass、PRF-dest rewrite、bitseg、fmaWeighted、recurringStuck、roundingSub、f3Dependent、fpsrSuppress | FSU Pipe已有实施范围与诚实代理边界 | https://github.com/wangxumarshall/gem5-fi/tree/fi-ding |  |  |
| CHAOSIQ | CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.{py,cc,hh} | 源码 | targetClass=vec、fpOnly、tag/ready/wakeup/dispatch modes | FP/SIMD IQ部分模型的可执行实现 | https://github.com/wangxumarshall/gem5-fi/tree/fi-ding |  |  |
| CHAOSPhysReg | CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.{py,cc,hh} | 源码 | regTargetClass=vector、vecLaneWidth/Offset、bitflip/stuck-at、read-count/overwrite | FP/SIMD PRF已有实施范围 | https://github.com/wangxumarshall/gem5-fi/tree/fi-ding |  |  |
| CHAOSPropagation | CHAOS/gem5/src/cpu/o3/CHAOSPropagation/* | 源码 | PROP-EVT字段合同与LSU传播链 | FSU_PROP复用字段和终止原则；现有链不自动覆盖FSU | https://github.com/wangxumarshall/gem5-fi/tree/fi-ding |  |  |
| VERITAS | HPCA'25 Veritas（参考表汇总） | 文献证据；x86+gem5+机队数据 | FP/向量密集负载下FADD/FMUL/VADD/VFADD/VMUL/VFMUL风险显著升高 | Pipe负载和持续stuck-at动机 | 见ARM64-REF中的原文条目 |  |  |
| ETS24 | ETS'24（参考表汇总） | 文献证据；x86+gem5+门级模型 | GEMM/sparse/SVD/FFT对VFADD/VFMUL stuck-at有高激活/高敏感 | W5/W6数值负载和FP06模型依据 | 见ARM64-REF中的原文条目 |  |  |
| HARPOCRATES | ISCA'24 / MICRO'25 Harpocrates（参考表汇总） | 文献证据；x86+gem5 | SSE FP加/乘卡死和生成式检测负载 | W0/W10检测率研究；不替代通用负载SDC率 | 见ARM64-REF中的原文条目 |  |  |

注：合并单元格：A3:H3, A2:H2（全宽横幅已作分节标题；其余仅锚单元格有值）。

<a id="sheet-11"></a>
## 11.传播事件字段规范
> 5 列 × 26 行；非空单元格 130

| 字段 | 作用域 | 含义 | 当前代码 | 本方案要求 |
|---|---|---|---|---|
| run_id | campaign | FSU-模型-频率-负载主键 | manifest/目录部分已有 | 每条FSU_EVT必写；与工作簿唯一对应 |
| sample_run_id | 单次运行 | RunID下的seed/样本编号 | observation identity部分已有 | 每条事件必写，不得仅用run_id |
| fault_id/ptag | 故障链 | run内一次故障或burst/stuck实例 | CHAOSPropagation ptag；其他注入日志不统一 | 所有FSU注入器和后续事件必写 |
| event_id | 事件 | run内唯一事件ID | PROP-EVT部分已有 | 每条事件必写；稳定、单调或UUID |
| parent_event_id | 传播边 | 直接因果父事件 | PROP-EVT部分已有 | 除根fault_applied外必写；多父用辅助edge表 |
| kind/stage | 节点 | fault_applied/carrier/consumer/execute/writeback/fanout/commit/terminal | LSU PROP-EVT有kind | 使用固定枚举；映射L0-L5 |
| tick/cycle | 时间 | gem5 tick与CPU本地cycle | tick广泛存在 | tick和cycle都写；禁止假设1GHz |
| core_id/thread_id | 执行上下文 | CPU/core/thread归属 | tid部分日志已有 | 每条事件必写 |
| dyn_inst_seq | 动态指令 | O3 DynInst seqNum | CHAOSIQ/CHAOSFPU日志已有sn | 故障、carrier、consumer、WB、commit全链传递 |
| commit_seq | 提交 | 全局或线程提交序号 | CommitTrace可记录 | 只在commit/terminal写；与DynInst seq分开 |
| pc/opcode/op_class | 指令语义 | PC、原始编码、gem5 opClass | opClass/sn部分已有 | 注入根和消费/提交节点必写 |
| iq_slot/src_slot | 调度结构 | IQ entry与操作数槽 | CHAOSIQ部分有src_slot | 所有IQ/PRF read事件必写 |
| producer_seq/consumer_seq | 依赖边 | 产生者和消费者DynInst seq | wakeup日志仅部分 | 每个Vec源必写；错源也记true/fault producer |
| arch_reg/reg_class/phys_reg/reg_generation | 寄存器载体 | V架构号、VecRegClass、物理号和复用世代 | CHAOSPhysReg有class/index，generation缺失 | 解决物理槽复用误关联 |
| lane_width/lane_offset/lane_mask | 向量语义 | 8/16/32/64-bit lane和active/write mask | CHAOSPhysReg有width/offset；mask缺失 | 所有向量值读写事件必写 |
| value_hash/value_preview | 数据载荷 | 全值hash与可控短摘要 | CommitTrace有部分目的值 | 注入前后、读、执行结果、WB、commit均写；不必泄漏全量大向量 |
| bit_indices/fault_mask/field | 故障定位 | bit集、mask、sign/exp/mant/lane/control字段 | CHAOSFPU/PhysReg有部分 | 注入根必写；双bit记距离/相邻性 |
| FU_class/FU_index | 执行资源 | FSU能力类和实际管线 | 缺少统一输出 | 所有issue/execute/completion事件必写 |
| eligible_ordinal/eligible_total | 采样 | countOnly总数和本次选中序号 | CHAOSFPU/IQ有countOnly/eventsToSkip | 每个F0样本必写；保证均匀抽样可审计 |
| burst_id/ordinal/length | 聚类故障 | F4内同一突发的事件归属 | FSU尚缺 | 所有F4事件必写；区间按run cluster计算 |
| state_before/state_after | 控制状态 | ready/valid/issued/busy/FPSR/FPCR等前后值 | 部分模式日志有 | 状态/时序模型必写，不只写mode名 |
| detection_layer/detector | 检测 | Hardware RAS/OS/Application/None/Unknown和具体证据 | LSU PROP-EVT有部分 | 与outcome分开；首检互斥、any-time可多值 |
| outcome | 终端 | Masked/Detected-contained/Data Corruption/Crash/Timeout/Simulator failure/Unknown | offline classify可提供 | 由链证据+软件oracle联合判定 |
| contained/reason | 终止证据 | squash/replay/overwrite/mask和无错误副作用证据 | LSU链有部分 | 无后续事件不能代替reason和反证 |
| config_hash/binary_hash/golden_id | 复现性 | gem5配置、负载二进制和oracle版本 | manifest部分已有 | 每个sample_run元数据必写 |
