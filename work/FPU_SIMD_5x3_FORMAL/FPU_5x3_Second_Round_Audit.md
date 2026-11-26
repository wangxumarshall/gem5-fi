# FPU/SIMD 5×3 第二轮证据审查审计报告

批号 `FPU_SIMD_5x3_FORMAL` · 生成 2026-11-23 · 工作目录 `/home/sdc/gem5-fi-fpu`

本报告基于第二轮原始 Trace 审查，确认了 3 类必须修复的问题，均不改变 12 个
故障模型的语义。

---

## 1. 问题一：C03 错误在覆盖前已被消费（12/12 模型）

**审查结论**：12 个模型的 C03 负载汇编顺序均为：

```
FADD (目标, 故障)          ; s0 = 错误值
FMOV w10, s0               ; ← 消费者读取错误值
STR  w10, [x9]             ; ← 错误值写入输出缓冲区 raw0（软件可见）
FMOV s0, #1.0             ; ← 覆盖（已在消费之后，太晚）
```

因此“错误结果在覆盖之前已经被消费者读入并写入输出缓冲区”，按修订要求应判
**WRONG_RESULT**，不能判 MASKED_OVERWRITE。第一轮的 36 个 C03 分类为
MASKED_OVERWRITE 是**错误的**（基于 `raw0_diff`/`raw2_diff` 的简单组合，未核实
汇编顺序与真实消费关系）。

- 标量模型（M001–M005）：`fmov w10, s0; str w10, [x9]` 在覆盖前消费错误。
- M006（GPR）：`str x0, [x9]` 在 `mov x0, #0` 前导出错误。
- M007（FCMP）：`csel x10, x5, x6, lo; str` 在覆盖前消费 faulted NZCV。
- SIMD（M008–M012）：`str q0, [x9]` 在覆盖前导出错误 lane。

---

## 2. 问题二：C05 未证明 T03 的错误随 squash 消失（12/12 模型）

**审查结论**：第一轮 C05 N=64、T01/T02/T03=7/32/58，ordinal 64 被 squash，但
**T03=58 注入的错误最终 Commit 并成为 SDC**。虽然存在真实误预测，但没有证明
“注入的错误随目标指令 squash 而消失”。

根因：`ordinal=ceil(0.9N)` 只有在下式成立时才命中 squash 的末次事件——
`ceil(0.9N)=N ⇒ N≤9`；而第一轮训练仅 63 次“taken”在 N=64 下才可靠误预测，
N≤9（<14 次训练）时分支预测器（TournamentBP）不稳定，末次迭代不误预测
（实测 N=9/12 无 squash_on_target，N≥14 才有）。

---

## 3. 问题三：传播分析器的物理寄存器误关联

**审查结论**：`analyze_5x3.py` 仅按**物理寄存器编号**匹配所有后续 rename 事件，
未做版本/重用隔离，会把“同一物理寄存器编号被重用后的无关读取”误判为传播链
消费者。必须改为 arch 寄存器 + writer 版本的因果追踪。

---

## 4. 源码/Trace 语义核对（M008、M012）

| 模型 | 汇编源（ELF） | gem5 Trace `op` | 语义确认 |
|---|---|---|---|
| M008 | `uqadd v0.16b, v1.16b, v2.16b` | `uqadd w0, w1, w2` | hook 命中 `neon64.UqaddQX.saturate`（lane=7），证明解码为向量 UQADD |
| M012 | `xtn2 v0.16b, v1.8h` | `Xtn w0, w1` | hook 命中 `neon64.Xtn2X.old_dest_low`（old=0x0807…→0），证明解码为 XTN2 |

> Trace 中 `op` 字符串是 gem5 内部解码器对向量寄存器的渲染（`w0/w1/w2` 实为
> v 寄存器），**不得**将其当作原始 ARM 指令名。实际指令形式由 .S 源 + hook 命中
> 的 fault_inject `site` + 语义行为（lane 级/old-dest 级）交叉确认。M005 同样
> 以 `fp32_sqrt.negative_domain` site 确认。

---

## 5. 受影响实验清单

| 范围 | 影响 | 处置 |
|---|---|---|
| C03（12 模型 × 3 时机 = 36 fault + 12 control） | 分类错误（WRONG_RESULT 被误判 MASKED） | **重跑** |
| C05（12 模型 × 3 时机 = 36 fault + 12 control） | 未证明 T03 squash | **重跑** |
| C01/C02/C04 | 未受影响 | 保留（不重跑） |
| M008/M012 原始证据 | 未受影响 | 保留（不覆盖） |

**重跑规模**：72 Fault + 24 Control = **96 运行** + 24 count-only。

---

## 6. 判定依据

- 修订均为负载结构/分析器修复，**不改 12 个故障模型语义、Hook、fault 操作**。
- C03 修订目标：错误在首次有效消费前被覆盖（真正 MASKED_OVERWRITE）。
- C05 修订目标：T03 落在真实误预测路径并在恢复时被 squash（真正 SQUASHED）。
- 不把 T03 改为 100%，不人工制造 squash，不伪造提交状态。