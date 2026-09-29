# 01 · 单元与现有研究（六单元 × 现有研究 / 空白）

> 来源：《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（WPS 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「1.单元与现有研究」R2–R7（表头 R1），7 列 × 6 单元。

| 单元 | 作用 | 现有文章 | 现有文章结果 | 指标口径 | 证据直接性 | 研究空白/本方案增量 |
|---|---|---|---|---|---|---|
| Int Decode | 把 AArch64 指令字译成内部操作，识别 opcode、源/目的寄存器、立即数、位宽、移位、标志位和异常属性。 | MICRO'24 DelayAVF：Ibex in-order RISC-V，RTL+NanGate 45nm+Verilator；对译码器 1007 根线逐线加入 10%-90% 周期的小延迟故障，并把同一周期产生的状态位错误集合注入后续执行。IISWC'15 与 TC'23 明确不直接注入组合逻辑。 | DelayAVF 排序为 ALU > Decoder > Regfile。d=90% 时 Decoder 的 ACE interference 最大/平均为 13.03%/6.73%，ACE compounding 为 2.47%/1.14%，ORACE 估算偏差最大/平均 21.80%/10.45%。论文只给程序可见失败，不分 SDC/Crash。 | DelayAVF，不是 SDC 率 | 直接机制证据，但核心/ISA/流水线类型不同 | 空白：AArch64 合法 opcode 换值、寄存器字段错配、立即数拼接、uop 序列和 ready/valid 时序。 |
| Int Rename | 用 speculative RAT 把 x0-x30 映射到 Int PRF，分配新物理寄存器，维护 free list、ready/busy 和分支 checkpoint。 | 本地论文无直接注入结果。TC'23 能追踪架构/物理寄存器号但未注入 RAT。HPCA'24 gem5-MARVEL 声称框架可扩展到 register renaming unit，正文结果只覆盖 PRF/L1I/L1D/LQ/SQ。CHAOS 修改架构寄存器值，不修改映射。 | 无直接实测结果。 | 不适用 | 同机制线索 | 空白：RAT 合法标签替换、free-list 泄漏/重复分配、checkpoint 回滚、ready 状态、旧映射读出。 |
| Int Dispatch / ROB | 把重命名后的 uop 分派到 IQ/FU，并在 ROB 中按程序序记录 PC、寄存器标识符、完成/异常/回滚状态，保证精确提交。 | TC'23：Armv8 类 A72/Armv7 类 A15，ROB 128/40 项；MiBench 10 个；单比特瞬态，2000 次/结构/负载；commit 比较 PC、opcode、操作数/立即数和寄存器内容。IISWC'15 只列 ROB 配置，未报告 ROB 结果。 | TC'23 中 ROB 的 SDC 概率为 0.0%（口径：到达软件层的 non-Benign 故障中产生 SDC 的比例）。作者认为 PC/物理寄存器号损坏通常在 commit 前触发依赖检查失败并 Crash；Masked 占多数。 | non-Benign 条件 SDC 占比，不等于总 AVF | 直接 | 空白：ROB 状态位、head/tail、合法标签换值、dispatch steering、commit/squash 时序和 FP 激活子集。 |
| FP/SIMD Decode | 译码 AArch64 标量 FP 和 AdvSIMD/NEON 指令，确定标量/向量模式、元素宽度、lane、舍入/异常行为与 uop 序列。 | 无直接研究。DelayAVF 的 Decoder 是仅整数的 Ibex 译码器；TC'23 的负载无 FP 操作。 | 无直接实测结果。 | 不适用 | 机制类比 | 空白：合法 FP/SIMD opcode 换值、lane/元素宽度、标量/向量模式、FPCR 相关控制和 uop 拆分。 |
| FP/SIMD Rename | 把 V 寄存器的标量 FP/128-bit SIMD 目的和源映射到 Float/Vec PRF，维护对应 free list、ready 状态和 checkpoint。 | 无直接研究。TC'23 明确因 MiBench 无 FP 操作而不注入 FP PRF，更未注入 FP/SIMD RAT。Harpocrates 注入 FP 功能单元，不注入重命名。 | 无直接实测结果。 | 不适用 | 空白 | 空白：FP/Vec RAT、跨类别选择、partial-write/zeroing 语义、free list、checkpoint 和 ready 时序。 |
| FP/SIMD Dispatch/ROB | 将 FP/SIMD uop 分派到可执行对应 opClass 的 FU，并在共享 ROB 中维护完成、FP 异常、目的标签和按序提交。 | TC'23 的统一 ROB 是直接结构证据，但其负载无 FP/SIMD 指令，不能作为 FP 激活结果。Veritas/Harpocrates 对 FP 功能单元的结果不等同于 FP dispatch/ROB。 | 无 FP/SIMD 激活子集的直接结果；只能保留 TC'23 的 ROB 机制结论作为先验。 | 结构直接、激活域不直接 | 部分直接 | 空白：FP FU steering、lane writeback mask、完成事件配对、FP exception/done、squash 和 commit 时序。 |

