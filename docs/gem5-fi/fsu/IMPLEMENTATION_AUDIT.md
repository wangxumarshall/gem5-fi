# FSU 30 模型 × 173 RunID 实施审计（阶段 B）

> 基线：`origin/fi-ding` `46ce66cdb9c22f5e591b43b97b68c7d526704211`；生成工具：`tools/fsu_implementation_matrix.py`；数据源：工作簿表 7/9/10 + 2026-11-02 真实代码审计。

## 1. 结论

- RunID 总数：**173**（唯一 173；表 7/表 9 集合相等）
- 模型数：**30**；模型状态：MISSING 17、PARTIAL 13
- RunID 状态：MISSING 87、PARTIAL 86
- workload 身份：NO_FP_ARTIFACT 6、NO_TRUE_ARTIFACT 54、PARTIAL 101、REAL 12
- **可端到端运行（注入器+workload+oracle+传播链）的 RunID：0/173**

工作簿把 FR01/FP04 标为“直接已有”，但代码审计显示二者均只覆盖部分子模型：FR01 无 128-bit lane/FP 字段分层/generation/consumer；FP04 仅 FP64 低 64 位结果字段，FP32 与 NEON 全 lane（FP04-d）缺失。二者均无 FSU PROP 事件，不能直接进入三 seed 执行。

## 2. 30 模型审计表

| 模型 | 单元 | 工作簿声明 | 代码审计 | 现有注入器 | 关键缺口 |
|---|---|---|---|---|---|
| FP01 | FSU Pipe | 需新增 | **MISSING** | CHAOSFPU 仅结果侧 XOR，无操作数/A/B/C hook | 操作数/控制/流水线级故障；PROP 事件 |
| FP02 | FSU Pipe | 需新增 | **MISSING** | CHAOSFPU faultMask 仅结果低 64 位多位 XOR | 同 lane 相邻/跨 lane 双 bit 几何、FP32/全 128 位；PROP 事件 |
| FP03 | FSU Pipe | 需新增 | **MISSING** | CHAOSFPU 无；CHAOSDecode 仅有解码级 opcode swap（越界代理） | FSU op-select 换值；PROP 事件 |
| FP04 | FSU Pipe | 直接已有 | **PARTIAL** | CHAOSFPU 结果 XOR + bitseg(sign/exp_hi/exp_lo/mant_hi/mid/lo) | FP32 字段映射；128-bit Vec 全 lane（FP04-d）；dest phys tag/old-correct/consumer/FPSR；PROP 事件。工作簿“直接已有”高估 |
| FP05 | FSU Pipe | 部分已有 | **PARTIAL** | CHAOSFPU faultMask / recurringStuck | 2–4 事件 burst、burst_id/ordinal、lane mask/跨 lane；PROP 事件 |
| FP06 | FSU Pipe | 部分已有 | **PARTIAL** | CHAOSFPU recurringStuck（结果侧 stuck 代理） | SA0/SA1 极性、全向量宽度、exposure/applied 列表、部分积代理；PROP 事件 |
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
| FR03 | FP/SIMD PRF | 部分已有 | **PARTIAL** | CHAOSPhysReg SA0/SA1 + setStuckTarget（仅标量） | Vec 写路径 stuck 未实现（不调用 setStuckTarget）；checkPermanent 按键号误伤 int PRF；clearStuckTarget 从未调用；exposure/applied 计数；PROP 事件 |
| FR04 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | Vec 读地址/tag 替代到另一 active-ready Vec 物理寄存器；PROP 事件 |
| FR05 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | Vec 读端口输出 1-bit 翻转（不回写 PRF）；per-read 记录；PROP 事件 |
| FR06 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | Vec 读端口多位/跨 lane 翻转；PROP 事件 |
| FR07 | FP/SIMD PRF | 部分已有 | **PARTIAL** | CHAOSFPU 执行后目标值 XOR（代理），非 PRF-WB hook | PRF 写回边界 hook；golden result、WB txn、dest tag、wakeup、consumer 链；PROP 事件 |
| FR08 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | Vec 写目标 tag 替代/交换；PROP 事件 |
| FR09 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | write-enable/ready/wakeup 原子性（lost/early/late/split）；PROP 事件 |
| FR10 | FP/SIMD PRF | 需新增 | **MISSING** | 无 | bypass/forwarding mux 与 partial-lane merge；PROP 事件 |

## 3. 全局阻塞（对全部 173 RunID 生效）

- 无 gem5 二进制：/home/sdc/gem5-fi-fsu/build/ARM/gem5.opt 不存在，任何 RunID 都无法运行
- 无 FSU PROP-EVT 发射：CHAOSFPU/CHAOSIQ/CHAOSPhysReg 均未调用 CHAOSPropagation::notePropEvt
- 无 FSU 链审计器：无 fsu_prop_fields.py/fsu_chain_check.py；LSU 审计器为硬编码
- 无 FSU 三 seed 流水线：runner.py/campaign.py 无 FSU RunID/seed1..3/chain_report 支持
- 配置不匹配：ooo_proxy.py 默认 ROB=128、IQ=64、4-wide，工作簿 B0 为 ROB=40、IQ=32、3/3/3、8/8/8
- 所有模型均无模型级自动化测试；仅有转换器 24 项 + 实施矩阵 5 项

## 4. Workload 身份审计

| W-ID | 名称 | 身份 | 真实载体 | golden/oracle | 缺口 |
|---|---|---|---|---|---|
| W0 | FSU-MiniCheck | **UNUSED** | `workloads/directed/mini_check` 仅存在 LSU 整数版 workloads/directed/mini_check（无 FP/NEON） | minicheck-golden-v1=07568da9f3ad5665（LSU）；exact 16-hex（但域不符） | 它不是 FSU 探针；173 个 RunID 未使用 W0 |
| W1 | FP-ScalarProbe | **NO_TRUE_ARTIFACT** | `workloads/directed/method1_controls` 无专用产物；可用 method1_controls pure_fma 作部分标量 FMA 代理 | purefma-golden-v1=98433fcf09968e6a；16-hex checksum（无 FPSR/FPCR/NaN/4 舍入） | 工作簿要求的 NaN/Inf/±0/subnormal、4 种舍入、FPSR/FPCR 均无载体 |
| W2 | FP-IQ-Dependency | **NO_TRUE_ARTIFACT** | `workloads/ooo/dep_chain/dep_chain_vec` 无专用产物；dep_chain_vec 仅 NEON FMLA 依赖链 | depchainvec-golden-v1=b1e661a247b95774；16-hex checksum（非逐边 oracle） | 缺 FP/NEON fan-out/fan-in、双源非交换、多 ready 竞争、mispredict 消费者 |
| W3 | NEON-LaneProbe | **PARTIAL** | `workloads/directed/neon_lane` neon_lane（仅 32-bit lane；XOR/shift/add） | neon-golden-v1=00000000526925fe；精确 16-hex + 64-hex per-lane 行 | 缺 8/16/64-bit lane、extract/insert、widen/narrow、permute、reduce |
| W4 | FMA-DotProduct | **REAL** | `workloads/directed/elemwise_fma_kernel` elemwise_fma_kernel（FP64 c[i]=a[i]*b[i]+d[i]） | elemwisefma-golden-v1=ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7；ARRAYHASH 64-hex + ULP | 不是点积归约；FMA 中间值在 gem5 为功能级不可达（工作簿已注明代理） |
| W5 | PolyBench-FP | **PARTIAL** | `workloads/ooo/polybench/` gemm/lu/cholesky/jacobi-2d（2mm 未 vendored） | gemm=116849d3adf3227b; lu=74ffe5eb77ea9257; cholesky=ea7e0d0e7c86582d; jacobi-2d=dc867b5f02998c1e；精确 FINAL 16-hex | 工作簿点名的 2mm 缺失；单 RunID 需绑定到具体程序而非“PolyBench-FP”标签 |
| W6 | SVD-FFT-Sparse | **PARTIAL** | `workloads/directed/svd_iterative_kernel` svd_iterative_kernel；FFT/稀疏线性系统无固定产物 | svditerative-golden-v1=4afb95b5b32f3820；16-hex checksum | FFT/IFFT 组合与稀疏线性系统组件缺失 |
| W7 | FP-ExceptionRecovery | **NO_FP_ARTIFACT** | `workloads/directed/divzero_loop_kernel` 仅整数除零/NULL 解引用崩溃探针（divzero_loop_kernel/exc_trigger） | 无 golden；无 | 无 FP invalid/div0/overflow/underflow/inexact、FPCR/FPSR、精确恢复载体 |
| W8 | Embench-FP-Selected | **UNUSED** | `workloads/ooo/embench/` nbody/minver 为 FP 项 | nbody=f39b4e8804f279c3; minver=9792f3ee24af3023；FINAL 16-hex | 无单一 W8 身份；173 RunID 未使用 |
| W9 | libjpeg-turbo-NEON | **REAL** | `workloads/ooo/libjpeg/jpeg_wl` libjpeg-turbo 3.2.1 AArch64 NEON jpeg_wl | libjpeg-golden-v1=c712f8f6fb9e21ec；FINAL 16-hex（解码 RGB FNV-1a） | 尚未被任何 FSU 173 RunID campaign 绑定 |
| W10 | SPEC CPU2017 FP SimPoint | **UNUSED** | `—` 无（需许可证） | 无；无 | 仓库无源码/二进制/checkpoint；173 RunID 未使用 |

## 5. 试点选择

首选 **FSU-FP04-F0-W4**（FP04 + `elemwise_fma_kernel` + ARRAYHASH/ULP）：
- 注入器：CHAOSFPU 已能对 FP64 标量结果做 sign/exp/mant 字段单 bit 翻转；
- workload：`workloads/directed/elemwise_fma_kernel` 存在且 golden 完整；
- 仍缺：FSU PROP-EVT、activated 判定、chain_report、单 seed Markdown 生成器、链审计器、gem5 构建。
在补齐上述传播/审计能力前，试点门禁 1–10 均不能判定通过。

## 6. 诚实边界

- 本表不把“不支持/未激活/缺观测字段”记为 Masked；三 seed 状态一律 0/3。
- 工作簿声明状态与代码审计状态分列；未观测到的运行时行为标 UNVERIFIED。
- 未运行 gem5（服务器上无二进制），本阶段结论仅来自静态代码/工作簿/产物审计。
