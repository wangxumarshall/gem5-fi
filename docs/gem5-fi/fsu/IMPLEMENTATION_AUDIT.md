# FSU 30 模型 × 173 RunID 实施审计（阶段 B + D2 事实刷新）

> 设计时基线：`origin/fi-ding` `46ce66cdb9c22f5e591b43b97b68c7d526704211`；当前 HEAD：`68dbd4bef5a582261092cb3f0af0928d542a1a8a`；生成工具：`tools/fsu_implementation_matrix.py`；数据源：工作簿表 7/9/10 + 初始代码审计 + 当前状态实时探测。

## 1. 结论

- RunID 总数：**173**（唯一 173；表 7/表 9 集合相等）
- 模型数：**30**；模型状态：MISSING 17、PARTIAL 13
- RunID 状态：MISSING 87、PARTIAL 86
- workload 身份：NO_FP_ARTIFACT 6、NO_TRUE_ARTIFACT 29、PARTIAL 101、REAL 37
- **可端到端运行（注入器+workload+oracle+传播链）的 RunID：0/173**

工作簿把 FR01/FP04 标为“直接已有”，但代码审计显示二者均只覆盖部分子模型：FR01 无 128-bit lane/FP 字段分层/generation/consumer；FP04 仅 FP64 低 64 位结果字段，FP32 与 NEON 全 lane（FP04-d）缺失。FP04 的 FSU PROP 发射端与 F0/F5 传播链已落地，并已有正式 seed；但子模型覆盖仍不完整。FR01 仍无 FSU PROP 链，不能直接进入三 seed 执行。

- 磁盘权威 seed 索引：历史全量 50/519，活跃 F0/F5 41/240；suite seed 18 个对应 72 个 component run（component 不计 seed）。

## 2. 30 模型审计表

| 模型 | 单元 | 工作簿声明 | 代码审计 | 现有注入器 | 关键缺口 |
|---|---|---|---|---|---|
| FP01 | FSU Pipe | 需新增 | **MISSING** | CHAOSFPU 仅结果侧 XOR，无操作数/A/B/C hook | 操作数/控制/流水线级故障；PROP 事件 |
| FP02 | FSU Pipe | 需新增 | **MISSING** | CHAOSFPU faultMask 仅结果低 64 位多位 XOR | 同 lane 相邻/跨 lane 双 bit 几何、FP32/全 128 位；PROP 事件 |
| FP03 | FSU Pipe | 需新增 | **MISSING** | CHAOSFPU 无；CHAOSDecode 仅有解码级 opcode swap（越界代理） | FSU op-select 换值；PROP 事件 |
| FP04 | FSU Pipe | 直接已有 | **PARTIAL** | CHAOSFPU 结果 XOR + bitseg(sign/exp_hi/exp_lo/mant_hi/mid/lo) | FP32 字段映射；128-bit Vec 全 lane（FP04-d）；dest phys tag/old-correct/consumer/FPSR；F1/F2/F3 rate 语义（D2 实现中）。工作簿“直接已有”高估 |
| FP05 | FSU Pipe | 部分已有 | **PARTIAL** | CHAOSFPU faultMask / recurringStuck | 2–4 事件 burst、burst_id/ordinal、lane mask/跨 lane；PROP 事件 |
| FP06 | FSU Pipe | 部分已有 | **PARTIAL** | CHAOSFPU permanentStuck + f5Warmup（结果侧 stuck；安装一次、多次 exposure） | FP06-d partial-product proxy MISSING（不得用最终结果位冒充）；全向量宽度超过 128-bit；W4/W5/W6 尚未完成正式认证；FP06-a/b/c 的正式认证只覆盖 W3 的 32-bit lane2/结果侧代理 |
| FP07 | FSU Pipe | 部分已有 | **PARTIAL** | CHAOSFPU fmaWeighted（E3 行为代理） | 真实 FMA 中间值不可达（gem5 功能级）；未限定 FMA opClass；partial row drop/dup/align shift；PROP 事件 |
| FP08 | FSU Pipe | 部分已有 | **PARTIAL** | CHAOSFPU roundingSub / fpsrSuppress | FP32、FTZ/DN、异常/FPCR/FPSR 可观测状态；suppressed_count 未输出；PROP 事件 |
| FP09 | FSU Pipe | 需新增 | **MISSING** | 无 | lane swap/rotate、元素宽度替代、mask 移位、新旧拼接；PROP 事件 |
| FP10 | FSU Pipe | 需新增 | **MISSING** | 无 | completion early/late/drop/duplicate、result/dest swap、stale completion、延迟配对；PROP 事件 |
| FQ01 | FP/SIMD Issue Queue | 部分已有 | **PARTIAL** | CHAOSIQ mode=tag_bitflip + targetClass=vec | src0/src1 子模型选择；c 的 active-ready producer 判定；producer_sn/ready/activation 证据；operand hash；PROP 事件 |
| FQ02 | FP/SIMD Issue Queue | 部分已有 | **PARTIAL** | CHAOSIQ mode=tag_bitflip2 + targetClass=vec | 相邻/非相邻/跨子字段分层；候选域与越界计数；target writer/首个读者；PROP 事件 |
| FQ03 | FP/SIMD Issue Queue | 需新增 | **MISSING** | 无（tag_swap 是换成随机 producer，不是 src0↔src1 配对交换） | src0↔src1 配对交换；FMA mul/add 源角色；lane 角色交换；双源配对日志；PROP 事件 |
| FQ04 | FP/SIMD Issue Queue | 部分已有 | **PARTIAL** | CHAOSIQ ready_early / ready_never / ready_never_event | ready_never/_event 硬编码拒绝 FP/vector（CHAOSIQ.cc:745）；stale-ready 缺失；scoreboard 真值/旧值读取/ROB stall；PROP 事件 |
| FQ05 | FP/SIMD Issue Queue | 需新增 | **MISSING** | 无（无 valid/issued/squashed 注入 API） | valid lost/ghost、issued early、squash clear lost、nonSpec 伪造；IQ slot 生命期/occupancy 守恒；PROP 事件 |
| FQ06 | FP/SIMD Issue Queue | 部分已有 | **MISSING** | CHAOSIQ dispatch_misroute（仅 IntAlu↔IntMult） | FP/SIMD add-pipe↔mul-pipe、compatible FU index、scalar↔SIMD route；FU capability/grant/latency 证据；PROP 事件 |
| FQ07 | FP/SIMD Issue Queue | 需新增 | **MISSING** | 无（seqNum 仅用于日志/tag_stuck） | ready-list rank/age swap、seqNum 合法替代、starvation bias；issue 顺序与性能差异；PROP 事件 |
| FQ08 | FP/SIMD Issue Queue | 部分已有 | **PARTIAL** | CHAOSIQ wake_omit / src_ready_bitflip / wake_phase | duplicate wake；victim 非 Vec 限定且未写日志（inst_queue.cc:1272）；producer→consumer sn/tag 配对；b 在无 victim 时仍计注入；c 的延迟事件 squash 断言风险（inst_queue.cc:1160，UNVERIFIED）；PROP 事件 |
| FQ09 | FP/SIMD Issue Queue | 需新增 | **MISSING** | 无（noteIqDeparture 只读） | issue→execute early/late/drop/duplicate/stale slot；FUPool/FUCompletion 事件；PROP 事件 |
| FQ10 | FP/SIMD Issue Queue | 需新增 | **MISSING** | 无（dispatch_misroute 不改 FU index/busy/free） | FU index 替代、busy→free/free→busy、release lost；FU 状态与 grant 证据；PROP 事件 |
| FR01 | FP/SIMD PRF | 直接已有 | **PARTIAL** | CHAOSPhysReg phys/arch modes，VecRegClass，lane 8/16/32/64 | 128-bit lane；FP32/FP64 字段分层；generation；ready/consumer 谓词；old/new value hash；PROP 事件。工作簿“直接已有”高估 |
| FR02 | FP/SIMD PRF | 部分已有 | **PARTIAL** | CHAOSPhysReg bitsToChange=2 / faultMask | 跨 lane、exp+mant 字段对、bit 距离/相邻性分类；越 lane 掩码丢失；PROP 事件 |
| FR03 | FP/SIMD PRF | 部分已有 | **PARTIAL** | CHAOSPhysReg SA0/SA1 + setStuckTarget；FR03 Vec 写路径按 generation 重施加 | FR03-F5-W3 已完成 3/3（L5 commit/squash/first-impact、runner 显式 CHAOSPhysReg 路径、O3 生命周期 gate）；FSU_PROP L0-L5 已接入；FR03-F5-W5/W6 仍 BLOCKED（不得借用 W3 证据）；模型整体仍为 PARTIAL |
| FR04 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | Vec 读地址/tag 替代到另一 active-ready Vec 物理寄存器；PROP 事件 |
| FR05 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | Vec 读端口输出 1-bit 翻转（不回写 PRF）；per-read 记录；PROP 事件 |
| FR06 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | Vec 读端口多位/跨 lane 翻转；PROP 事件 |
| FR07 | FP/SIMD PRF | 部分已有 | **PARTIAL** | CHAOSFPU 执行后目标值 XOR（代理），非 PRF-WB hook | PRF 写回边界 hook；golden result、WB txn、dest tag、wakeup、consumer 链；PROP 事件 |
| FR08 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | Vec 写目标 tag 替代/交换；PROP 事件 |
| FR09 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | write-enable/ready/wakeup 原子性（lost/early/late/split）；PROP 事件 |
| FR10 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | bypass/forwarding mux 与 partial-lane merge；PROP 事件 |

## 2.1 RunID 状态（seed_completion 与 coverage_status 独立）

- seed_completion：0/3 156、2/3 1、3/3 16
- coverage_status：BLOCKED_NOT_IMPLEMENTED 87、BLOCKED_NO_TRUE_ARTIFACT 11、COMPLETE 7、PARTIAL 67、PILOT_SUBMODEL_ONLY 1

| RunID | seed_completion | coverage_status | coverage_reason |
|---|---|---|---|
| FSU-FQ01-F0-W2 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FQ01-F0-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FQ01-F2-W2 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FQ01-F2-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FQ02-F0-W2 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FQ02-F0-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FQ02-F2-W2 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FQ02-F2-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FQ03-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ03-F0-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ03-F2-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ03-F2-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ04-F0-W2 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FQ04-F0-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FQ04-F4-W2 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FQ04-F4-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FQ05-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ05-F0-W7 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ05-F4-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ05-F4-W7 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ06-F0-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ06-F0-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ06-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ06-F2-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ06-F2-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ06-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ07-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ07-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ07-F2-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ07-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ08-F0-W2 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FQ08-F0-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FQ08-F3-W2 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FQ08-F3-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FQ08-F4-W2 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FQ08-F4-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FQ09-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ09-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ09-F4-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ09-F4-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ10-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ10-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ10-F4-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FQ10-F4-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR01-F0-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F0-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F0-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F1-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F1-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F1-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F2-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F2-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F2-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F3-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F3-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR01-F3-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR02-F0-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR02-F0-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR02-F0-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR02-F2-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR02-F2-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR02-F2-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR03-F5-W3 | 2/3 | PARTIAL | FR03-F5-W3 2/3 after protocol review: seed3 attempt-1 is a real Masked/unconsumed outcome; attempt-2 changed the target and is supplemental evidence only |
| FSU-FR03-F5-W5 | 3/3 | COMPLETE | certified 3/3: FR03 permanent Vec-cell suite; components never count as seeds |
| FSU-FR03-F5-W6 | 3/3 | COMPLETE | certified 3/3: FR03 permanent Vec-cell suite; components never count as seeds |
| FSU-FR04-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR04-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR04-F2-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR04-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR05-F0-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR05-F0-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR05-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR05-F2-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR05-F2-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR05-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR06-F0-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR06-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR06-F2-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR06-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR07-F0-W1 | 3/3 | COMPLETE | certified 3/3: result-side WB proxy (FR07-a/c/d masks) on REAL W1 with ARRAYHASH; true PRF-WB hook remains an adapter boundary |
| FSU-FR07-F0-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR07-F0-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR07-F2-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR07-F2-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR07-F2-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FR08-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR08-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR08-F2-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR08-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR09-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR09-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR09-F4-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR09-F4-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR10-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR10-F0-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR10-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR10-F4-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR10-F4-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FR10-F4-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP01-F0-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP01-F0-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP01-F0-W4 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP01-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP01-F2-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP01-F2-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP01-F2-W4 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP01-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP02-F0-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP02-F0-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP02-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP02-F2-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP02-F2-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP02-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP03-F0-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP03-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP03-F2-W1 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP03-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP04-F0-W1 | 3/3 | PARTIAL | official seeds 3/3 admitted under B0-core with the real W1 FP-ScalarProbe; decoded FP32 scalar instructions only (sign bit). The workload exercises FP64, special values, four rounding modes and FPSR/FPCR, but those are not injected per seed |
| FSU-FP04-F0-W3 | 3/3 | PARTIAL | official seeds 3/3 admitted with the real NEON FP32 lane workload; evidence covers FP04-d lane2 sign bit only (32-bit lane domain); FP04-a/b/c fields and the other lanes are not covered |
| FSU-FP04-F0-W4 | 3/3 | PILOT_SUBMODEL_ONLY | pilot covers FP04-c/mant_lo/W4/F0 only; workbook RunID requires FP04-a sign, FP04-b exp_hi/lo, FP04-c mant_hi/mid/lo, FP04-d NEON lane result, plus F1/F2/F3 semantics |
| FSU-FP04-F0-W5 | 3/3 | PARTIAL | certified suite 3/3: each suite seed counts as ONE seed (5 PolyBench component runs per seed, never added to seed totals); workbook W5 submodel coverage is still partial |
| FSU-FP04-F0-W6 | 3/3 | COMPLETE | certified 3/3: SVD/FFT/sparse-CG suite seed, 3 components per seed (components never count as seeds) |
| FSU-FP04-F1-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F1-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F1-W4 | 3/3 | PARTIAL | W4-rate-v1 official seeds 3/3 admitted; 0 remaining. |
| FSU-FP04-F1-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F1-W6 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F2-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F2-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F2-W4 | 3/3 | PARTIAL | W4-rate-v1 official seeds 3/3 admitted; 0 remaining. |
| FSU-FP04-F2-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F2-W6 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F3-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F3-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F3-W4 | 3/3 | PARTIAL | W4-rate-v1 official seeds 3/3 admitted; 0 remaining. The F3 multi-fault gate used the short W4 and is not an official seed |
| FSU-FP04-F3-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP04-F3-W6 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP05-F0-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP05-F0-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP05-F0-W6 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP05-F4-W3 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP05-F4-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP05-F4-W6 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP06-F5-W1 | 3/3 | PARTIAL | certified 3/3, but this RunID covers only the FP06 precision/opClass subset exercised by W1; FP06-d remains MISSING and the full workbook submodels are not covered |
| FSU-FP06-F5-W3 | 3/3 | PARTIAL | certified 3/3: FP06-a SA0 / FP06-b SA1 / FP06-c fixed mantissa, 16,384 exposures each; covers the F5 result-side proxy of FP06-a/b/c only. FP06-d partial-product proxy is MISSING; evidence stays in the W3 32-bit lane2 sign/mantissa domain |
| FSU-FP06-F5-W4 | 3/3 | COMPLETE | certified 3/3: FSU-FP06-F5-W4 formal seeds admitted and audit.ok; bounded F5 evidence |
| FSU-FP06-F5-W5 | 3/3 | COMPLETE | certified 3/3: FSU-FP06-F5-W5 formal seeds admitted and audit.ok; bounded F5 evidence |
| FSU-FP06-F5-W6 | 3/3 | COMPLETE | certified 3/3: SVD/FFT/sparse-CG suite seed, 3 components per seed (components never count as seeds) |
| FSU-FP07-F0-W4 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP07-F0-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP07-F0-W6 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP07-F2-W4 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP07-F2-W5 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP07-F2-W6 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP08-F0-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP08-F0-W7 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FP08-F2-W1 | 0/3 | PARTIAL | injector/model only partially covers the workbook submodels; no 3-seed evidence for this RunID |
| FSU-FP08-F2-W7 | 0/3 | BLOCKED_NO_TRUE_ARTIFACT | workload identity has no真实 artifact / oracle |
| FSU-FP09-F0-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP09-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP09-F0-W9 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP09-F2-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP09-F2-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP09-F2-W9 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP09-F4-W3 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP09-F4-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP09-F4-W9 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP10-F0-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP10-F0-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP10-F0-W7 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP10-F4-W2 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP10-F4-W5 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |
| FSU-FP10-F4-W7 | 0/3 | BLOCKED_NOT_IMPLEMENTED | injector/hook for this model is missing in the audited code |

## 2.2 F5 RunID readiness（代码能力与正式认证分开）

| RunID | f5_readiness | seed_completion | 说明 |
|---|---|---|---|
| FSU-FR03-F5-W3 | PARTIAL_2_OF_3 | 2/3 | FR03-F5-W3 2/3 after protocol review: seed3 attempt-1 is a real Masked/unconsumed outcome; attempt-2 changed the target and is supplemental evidence only |
| FSU-FR03-F5-W5 | COMPLETE_3_OF_3 | 3/3 | certified 3/3: FR03 permanent Vec-cell suite; components never count as seeds |
| FSU-FR03-F5-W6 | COMPLETE_3_OF_3 | 3/3 | certified 3/3: FR03 permanent Vec-cell suite; components never count as seeds |
| FSU-FP06-F5-W1 | COMPLETE_3_OF_3 | 3/3 | certified 3/3, but this RunID covers only the FP06 precision/opClass subset exercised by W1; FP06-d remains MISSING and the full workbook submodels are not covered |
| FSU-FP06-F5-W3 | COMPLETE_3_OF_3 | 3/3 | certified 3/3: FP06-a SA0 / FP06-b SA1 / FP06-c fixed mantissa, 16,384 exposures each; covers the F5 result-side proxy of FP06-a/b/c only. FP06-d partial-product proxy is MISSING; evidence stays in the W3 32-bit lane2 sign/mantissa domain |
| FSU-FP06-F5-W4 | COMPLETE_3_OF_3 | 3/3 | certified 3/3: FSU-FP06-F5-W4 formal seeds admitted and audit.ok; bounded F5 evidence |
| FSU-FP06-F5-W5 | COMPLETE_3_OF_3 | 3/3 | certified 3/3: FSU-FP06-F5-W5 formal seeds admitted and audit.ok; bounded F5 evidence |
| FSU-FP06-F5-W6 | COMPLETE_3_OF_3 | 3/3 | certified 3/3: SVD/FFT/sparse-CG suite seed, 3 components per seed (components never count as seeds) |

## 2.3 capability_evidence（静态代码/测试探测，不等于认证）

| 模型 | 能力 | code_present | certified | 证据 |
|---|---|---|---|---|
| FP06 | permanent_stuck | True | True | CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc: permanentStuck x13; CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py: permanentStuck parameter；FSU-FP06-F5-W3 与 FSU-FP06-F5-W1 正式 seed 各 3/3，逐 seed audit.ok；仅认证 FP06-a/b/c 的结果侧代理（W3 32-bit lane2 域 + W1 scalar FP32/FP64 域），FP06-d 仍 MISSING |
| FP06 | f5_schedule_install_once | True | True | CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc: fault_installed/f5_warmup; CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py: f5Warmup；FSU-FP06-F5-W3 与 FSU-FP06-F5-W1 正式 seed 各 3/3，逐 seed audit.ok；仅认证 FP06-a/b/c 的结果侧代理（W3 32-bit lane2 域 + W1 scalar FP32/FP64 域），FP06-d 仍 MISSING |
| FP06 | sa0_sa1_non_xor | True | True | CHAOS/gem5/src/cpu/o3/CHAOSFPU/chaos_fsu_fields.hh: applyStuck/stuckPolarityValid; CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc: applyStuck x2；FSU-FP06-F5-W3 与 FSU-FP06-F5-W1 正式 seed 各 3/3，逐 seed audit.ok；仅认证 FP06-a/b/c 的结果侧代理（W3 32-bit lane2 域 + W1 scalar FP32/FP64 域），FP06-d 仍 MISSING |
| FP06 | apply_stuck | True | True | CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc: applyStuck x2；FSU-FP06-F5-W3 与 FSU-FP06-F5-W1 正式 seed 各 3/3，逐 seed audit.ok；仅认证 FP06-a/b/c 的结果侧代理（W3 32-bit lane2 域 + W1 scalar FP32/FP64 域），FP06-d 仍 MISSING |
| FP06 | fsu_prop_l0_l5 | True | True | CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc: emitFsu -> notePropEvt; CHAOS/gem5/src/cpu/o3/CHAOSPropagation/；FSU-FP06-F5-W3 与 FSU-FP06-F5-W1 正式 seed 各 3/3，逐 seed audit.ok；仅认证 FP06-a/b/c 的结果侧代理（W3 32-bit lane2 域 + W1 scalar FP32/FP64 域），FP06-d 仍 MISSING |
| FP06 | chain_end | True | True | CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc: chain_end x7；FSU-FP06-F5-W3 与 FSU-FP06-F5-W1 正式 seed 各 3/3，逐 seed audit.ok；仅认证 FP06-a/b/c 的结果侧代理（W3 32-bit lane2 域 + W1 scalar FP32/FP64 域），FP06-d 仍 MISSING |
| FP06 | bounded_exposure_sampling | True | True | CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc: f5_sample_limit/exposures_dropped; tests/test_chaos_fsu_f5_cpp.py；FSU-FP06-F5-W3 与 FSU-FP06-F5-W1 正式 seed 各 3/3，逐 seed audit.ok；仅认证 FP06-a/b/c 的结果侧代理（W3 32-bit lane2 域 + W1 scalar FP32/FP64 域），FP06-d 仍 MISSING |
| FP06 | partial_product_proxy_fp06d | False | False | CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py: gem5 ARM FP is a functional model; no partial-product/alignment-shift injection point; grep partial_product/partialProduct: no injection code；FP06-d MISSING；不得用最终结果位冒充部分积 |
| FR03 | vec_stuck_write_path | True | True | CHAOS/gem5/src/cpu/o3/regfile.hh: setStuckTarget/reapplyVecStuck; CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc: maybeReapplyStuck; tests/unit/chaos_vec_stuck_test.cc; tests/test_chaos_vec_stuck_cpp.py；FSU-FR03-F5-W5/W6 正式 FR03 suite seed 3/3 |
| FR03 | permanent_cell_across_generations | True | True | CHAOS/gem5/src/cpu/o3/regfile.hh: flat_generation/generationOf/armVecStuck generation is identity, not a match/clear key; tests/unit/chaos_physreg_generation_test.cc: cross-generation persistence + chain restart；FSU-FR03-F5-W5/W6 正式 FR03 suite seed 3/3 |
| FR03 | chaosphysreg_fsu_prop | True | True | CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc: notePropEvt x1; CHAOS/gem5/src/cpu/o3/regfile.hh: notePropEvt x0; O3 commit/ROB squash hooks + honest chain_end terminal；FSU-FR03-F5-W5/W6 正式 FR03 suite seed 3/3 |
| FR03 | runner_chaosphysreg_path | True | True | tools/fsu_seed_runner.py: CHAOSPhysReg/phys_reg x5；FSU-FR03-F5-W5/W6 正式 FR03 suite seed 3/3 |
| FR03 | squash_realloc_container_test | False | True | tests/unit/chaos_vec_stuck_test.cc: squash x0, realloc x1; tests/test_chaos_vec_stuck_cpp.py; real O3 gate: F5-FR03-W3-GATE-v3；FSU-FR03-F5-W5/W6 正式 FR03 suite seed 3/3 |
| FR03 | fr03_formal_seeds | True | True | runs/fsu/FSU-FR03-F5-W3: 3/3 certified; W5/W6 remain BLOCKED；FR03-F5-W3 3/3；W5/W6 不得借用 W3 证据 |
| W6_suite | svd_fft_sparse_real_artifacts | True | True | workloads/directed/svd_iterative_kernel.c; workloads/directed/fft_radix2_kernel.c; workloads/directed/sparse_cg_kernel.c; configs/fsu/suites/w6-fp-v1.json；FSU-FP04-F0-W6 与 FSU-FP06-F5-W6 suite seed 各 3/3 |
| W5_suite | five_programs_including_2mm | True | True | workloads/ooo/polybench/2mm; configs/fsu/suites/polybench-fp-v1.json；FSU-FP04-F0-W5 suite seed 3/3（component run 不计 seed） |

## 3. 基线缺口 vs 当前状态

### 3.1 baseline_gap（2026-11-02 最初审计原文，保留不删）

- `gem5_binary_missing`：无 gem5 二进制：/home/sdc/gem5-fi-fsu/build/ARM/gem5.opt 不存在，任何 RunID 都无法运行
- `fsu_prop_evt_missing`：无 FSU PROP-EVT 发射：CHAOSFPU/CHAOSIQ/CHAOSPhysReg 均未调用 CHAOSPropagation::notePropEvt
- `fsu_chain_auditor_missing`：无 FSU 链审计器：无 fsu_prop_fields.py/fsu_chain_check.py；LSU 审计器为硬编码
- `fsu_three_seed_runner_missing`：无 FSU 三 seed 流水线：runner.py/campaign.py 无 FSU RunID/seed1..3/chain_report 支持
- `config_mismatch_b0`：配置不匹配：ooo_proxy.py 默认 ROB=128、IQ=64、4-wide，工作簿 B0 为 ROB=40、IQ=32、3/3/3、8/8/8
- `model_level_tests_missing`：所有模型均无模型级自动化测试；仅有转换器 24 项 + 实施矩阵 5 项

### 3.2 current_status（当前 fsu HEAD 实测）

- HEAD：`68dbd4bef5a582261092cb3f0af0928d542a1a8a`（branch `fsu`）
- gem5 二进制：`/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`；存在=True；SHA-256=`9457531948999dd8241e6c6ad6fb85d0e529d5b7017f238d23c36b3d2302e28d`；size=1234734464
- FSU PROP 发射端：True（CHAOSFPU.cc emitFsu -> CHAOSPropagation::notePropEvt）
- FSU 链审计器：True（`tools/fsu_chain_check.py`）
- FSU 三 seed runner：True（`tools/fsu_seed_runner.py`）
- rate ordinal 工具：True（`tools/fsu_rate_ordinals.py`）
- 模型级测试文件：23 个
- B0 配置匹配：True（B0-core 已实现并经 F0-W1 的 config.ini 逐项校验：ROB=40/IQ=32/fetch-decode-rename 3/3/3/dispatch6/issue-wb-commit 8/8/8/PRF 128/192/48/LQ-SQ16。完整 v7a_3 的 FP FUPool=2 尚未实现，属剩余缺口。）

### 3.3 resolved_by_commit

- `gem5_binary_missing`：已由 f8eb4a22, 2f65a647 解决；权威基线改为 CHAOS/gem5/build/ARM/gem5.opt；Python 3.11.9 构建成功并由 F0 三 seed 使用
- `fsu_prop_evt_missing`：已由 e541beb9 解决；CHAOSFPU emitFsu() 调用 CHAOSPropagation::notePropEvt；F0 三 seed 的 prop_evt 已由链审计器解析
- `fsu_chain_auditor_missing`：已由 15f6cd1b, ccf4c96e, 26c96efe 解决；tools/fsu_prop_fields.py + tools/fsu_chain_check.py + tools/fsu_seed_audit.py；逐 seed audit.json 已持久化
- `fsu_three_seed_runner_missing`：已由 ef6b4036, 8e86d1ba 解决；tools/fsu_seed_runner.py（census→inject→oracle→chain）与 F0 三 seed AUTHORITATIVE 证据
- `model_level_tests_missing`：已由 e541beb9, 15f6cd1b, ccf4c96e, 26c96efe 解决；已新增 FSU rate/chain/runner/audit/index/矩阵测试；但 30 个模型的逐模型行为测试仍未齐全（见 remaining_gaps）

### 3.4 remaining_gaps（当前仍成立，不含已解决事项）

- `config_mismatch_b0`：配置不匹配：ooo_proxy.py 默认 ROB=128、IQ=64、4-wide，工作簿 B0 为 ROB=40、IQ=32、3/3/3、8/8/8
- `per_model_behavior_tests_missing`：30 个模型尚未逐个具备模型级行为测试（现有测试覆盖 rate/链条/runner/audit/矩阵，不等于 30 模型全覆盖）

## 4. Workload 身份审计

| W-ID | 名称 | 身份 | 真实载体 | golden/oracle | 缺口 |
|---|---|---|---|---|---|
| W0 | FSU-MiniCheck | **UNUSED** | `workloads/directed/mini_check` 仅存在 LSU 整数版 workloads/directed/mini_check（无 FP/NEON） | minicheck-golden-v1=07568da9f3ad5665（LSU）；exact 16-hex（但域不符） | 它不是 FSU 探针；173 个 RunID 未使用 W0 |
| W1 | FP-ScalarProbe | **REAL** | `workloads/directed/w1_fp_scalar_probe` w1_fp_scalar_probe（FP32/FP64 add/sub/mul/div/sqrt/FMA；NaN/Inf/±0/subnormal；RN/RP/RM/RZ；FPSR/FPCR 快照） | w1-fpscalarprobe-v1-golden=ffe18c8279bf419d9b0aad0f5e03901874d3440506066d93ede75820f2eba183；ARRAYHASH 64-hex（结果32+结果64+FPSR+FPCR）+ ULP；in-run golden/check | F0-W1 3/3 在 B0-core 下注入 FP32 scalar sign；FP64、特殊值、4 舍入与 FPSR 由 workload 执行但未逐 seed 注入；FPCR trap/异常恢复在 SE 中 N/A |
| W2 | FP-IQ-Dependency | **NO_TRUE_ARTIFACT** | `workloads/ooo/dep_chain/dep_chain_vec` 无专用产物；dep_chain_vec 仅 NEON FMLA 依赖链 | depchainvec-golden-v1=b1e661a247b95774；16-hex checksum（非逐边 oracle） | 缺 FP/NEON fan-out/fan-in、双源非交换、多 ready 竞争、mispredict 消费者 |
| W3 | NEON-LaneProbe | **PARTIAL** | `workloads/directed/neon_fp32_lane_kernel` neon_fp32_lane_kernel（float32x4 FMA，4×32-bit lane；真实 golden/census；旧 neon_lane 为整数 NEON，不在 FSU eligible 域） | neonfp32lane-v1-golden=cb66197d92c7656b9359b312e93180eaaf3c1e774d9264d7d0b595189bce8c2e；ARRAYHASH 64-hex + ULP + LANEHASH0..3（非单一 16-hex FINAL） | F0-W3 3/3 仅覆盖 lane2 sign（bit95）；缺其他 lane/字段、8/16/64-bit lane、extract/insert、widen/narrow、permute、reduce |
| W4 | FMA-DotProduct | **REAL** | `workloads/directed/elemwise_fma_kernel` elemwise_fma_kernel（FP64 c[i]=a[i]*b[i]+d[i]）；D2 另有 W4-rate-v1 扩展版（N=262144，实测 eligible 2,097,155） | elemwisefma-golden-v1=ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7；elemwisefma-rate-v1-golden=e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba；ARRAYHASH 64-hex + ULP | 不是点积归约；FMA 中间值在 gem5 为功能级不可达（工作簿已注明代理）；W4-rate-v1 的 F1/F2/F3-W4 已各 3/3 正式完成，但 F0-W4 仍是短 W4 pilot |
| W5 | PolyBench-FP | **PARTIAL** | `workloads/ooo/polybench/` gemm/2mm/lu/cholesky/jacobi-2d（suite polybench-fp-v1，五程序均已 vendored） | gemm=116849d3adf3227b; 2mm/lu/cholesky/jacobi-2d 见 configs/fsu/suites/polybench-fp-v1.json（逐元素 oracle）；精确 FINAL 16-hex + canonical array 逐元素 abs/rel/ULP | suite 五程序已完成 FSU-FP04-F0-W5 3/3（每 suite seed 只计 1）；workbook 单 RunID 仍绑定 suite 而非单一程序，PolyBench 全集与其他规模未覆盖 |
| W6 | SVD-FFT-Sparse | **PARTIAL** | `workloads/directed/svd_iterative_kernel` svd_iterative_kernel；FFT/稀疏线性系统无固定产物 | svditerative-golden-v1=4afb95b5b32f3820；16-hex checksum | FFT/IFFT 组合与稀疏线性系统组件缺失 |
| W7 | FP-ExceptionRecovery | **NO_FP_ARTIFACT** | `workloads/directed/divzero_loop_kernel` 仅整数除零/NULL 解引用崩溃探针（divzero_loop_kernel/exc_trigger） | 无 golden；无 | 无 FP invalid/div0/overflow/underflow/inexact、FPCR/FPSR、精确恢复载体 |
| W8 | Embench-FP-Selected | **UNUSED** | `workloads/ooo/embench/` nbody/minver 为 FP 项 | nbody=f39b4e8804f279c3; minver=9792f3ee24af3023；FINAL 16-hex | 无单一 W8 身份；173 RunID 未使用 |
| W9 | libjpeg-turbo-NEON | **REAL** | `workloads/ooo/libjpeg/jpeg_wl` libjpeg-turbo 3.2.1 AArch64 NEON jpeg_wl | libjpeg-golden-v1=c712f8f6fb9e21ec；FINAL 16-hex（解码 RGB FNV-1a） | 尚未被任何 FSU 173 RunID campaign 绑定 |
| W10 | SPEC CPU2017 FP SimPoint | **UNUSED** | `—` 无（需许可证） | 无；无 | 仓库无源码/二进制/checkpoint；173 RunID 未使用 |

## 5. 试点现状

**FSU-FP04-F0-W4**（FP04-c/mant_lo + 短 `elemwise_fma_kernel` + ARRAYHASH/ULP）已完成三 seed：
- seed_completion = 3/3，逐 seed admitted/certified=true、violations=[]；
- coverage_status 仍为 PILOT_SUBMODEL_ONLY（只覆盖 FP04-c 的 mant_lo，不是 FP04 全子模型，也不是 F1/F2/F3）。

**FSU-FP04-F0-W5**（PolyBench suite：gemm/2mm/lu/cholesky/jacobi-2d）已完成 3/3 suite seed：每个 suite seed 的 5 个 component run 只计 1 个 seed；2mm 已 vendored 且 gate PASS。

**FSU-FP06-F5-W3**（FP06-a SA0 / FP06-b SA1 / FP06-c fixed mantissa）已完成 3/3：每 seed 16,384 exposures、audit/certified 全过；仅认证结果侧代理的 a/b/c，FP06-d partial-product proxy 仍 MISSING。

- 已解决的全局能力见 3.3；仍缺的能力见 3.4。

## 6. 诚实边界

- 本表不把“不支持/未激活/缺观测字段”记为 Masked；三 seed 状态以磁盘 AUTHORITATIVE + audit.ok 为准，不手写。
- 工作簿声明状态与代码审计状态分列；未观测到的运行时行为标 UNVERIFIED。
- capability_evidence 的 code_present 只表示静态代码/测试存在，不等于正式认证；certified 只来自磁盘审计通过的正式 seed。
- gem5 二进制与正式 seed 状态由 current_status / seed_index 实测；FR03-F5 保持 PARTIAL/BLOCKED。
