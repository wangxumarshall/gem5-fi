# FR01/FR02 目标选择补充协议 v2（precision-qualified eligible event）

日期：2026-11-05　状态：冻结用于 FR01/FR02 后续正式运行
关联：`FR01-FR02-PRF-IDENTITY-AUDIT.md`

## 1. 为什么需要版本化

工作簿（`...-07-展开执行矩阵.md:166`）规定 F0 为“每次运行只注入 1 次；
warm-up 后在本模型 eligible event 中均匀抽样（countOnly + fixed uniform
ordinal）”。2026-11-05 的真实审计发现，仅按“已分配 phys 槽”随机抽样会
落在大比例无消费者的死槽上（W1 attempt-1/2：phys=34/gen=1，全运行 0 读），
这不是工作簿的触发条件。工作簿触发条件为
“目标 Vec phys reg active、ready 且后续有 consumer read”，且 FR01-a/b/c
与 FR02-d 明确区分 FP64/FP32/lane 几何。

因此本协议把 **eligible event 的定义**细化并冻结；旧结果保留，不与新
协议样本混算。

## 2. V2 eligible event 定义（已实现）

一个 eligible event 是三元组：

```
(consumer DynInst, source operand index, target phys cell)
```

满足：

1. `source.regClass == VecRegClass`（ARM64 唯一 FP/SIMD PRF）；
2. source cell 已分配（不在 free list）；
3. source 已 ready（producer 已写回）——避免注入后被 producer 覆盖；
4. 消费者真实 AArch64 编码经 `chaos_fsu::decodedPrecision` 解码，
   `precision_bits == target_precision`（0 表示不限）；
5. 注入发生在该消费者 `DynInst::execute()` **之前**，保证本消费者
   真正读取翻转后的值。

选择策略 `target_selection=ready_consumer`：

- 采样时刻（`first_clock` 之后、概率/节拍由既有 attack 事件控制）若 IQ
  中存在上述未发射事件，则在候选事件中均匀抽一个；
- 否则 **arm** 消费者 execute 边界：warm-up 后第一条 precision 合格的
  消费者 execute 触发注入。二者都不回退到无消费者槽；
- `target_phys_idx >= 0` 的显式目标路径（FR03/gate）不受影响；
- 未知 `target_selection` / `target_precision` 组合在构造期 fail closed。

## 3. 与工作簿“均匀抽样”的已知偏差

V2 目前是“首个合格事件（或采样时刻的合格事件集合均匀抽样）”，
**不是**全部 eligible events 上的 fixed uniform ordinal。因此：

- 不得把 V2 的多次 seed 解释为对“全部 eligible events”的无偏均匀样本；
- 正式论文口径仍需实现 countOnly 普查 + `eligible_ordinal`（后续单元）；
- 在此之前，V2 结果按 “first-qualified-event” 采样口径单独报告。

这一偏差已写入事件外的协议文档与 AUTONOMOUS-STATE，不隐藏。

## 4. 事件身份字段（审计要求）

每个 FR01/FR02 事件统一携带：

- `model_id`、`submodel`（来自 `semantic_role`）、`freq=F0`、`load_id`；
- `precision=fp32|fp64`，`field=sign|exp_hi|exp_lo|mant_hi|mant_mid|mant_lo`；
  FR02-d 跨字段时 `field` 取最低位所在字段，`bit_indices` 保留全部位身份；
- `phys_reg`、`arch_reg`、`reg_generation`（安装世代 provenance）；
- 读事件的实际值 `before=after=读取值`、`activated` 仅在读值与安装值
  （完整 128-bit）完全一致时为 1；
- `generation_change` 只作 provenance，不再作为读过滤/终止条件；
- 任何真实写目标 cell 的事件产生 `overwrite` 并终止瞬态。

## 5. Seed1 attempt 处置（全部保留，不删除、不改写）

| attempt | 协议 | 结果 | 处置 |
|---|---|---|---|
| 1 | v0 随机+回退 | 真实 `not_consumed`（phys 34/gen 1/值 0） | `.real_outcome` 保留 |
| 2 | v0 随机+回退 | 同上 | `.real_outcome` 保留 |
| 3 | v1 ready_consumer，无 precision | SDC，但消费者是 FP32 `str s0`，与 FR01-a（FP64）不符 | 保留；**不计入 FR01-a 样本** |
| 4 | v2 ready_consumer + precision=64 | SDC，FP64 `fadd d0`，full/admitted/certified | 保留；审计字段不全（无 load_id/field），被 attempt-5 取代 |
| 5 | v2 + 审计字段 | SDC，FP64 `fadd d0`，full/admitted/certified，`fsu_seed_audit ok=true` | **当前权威 seed1 证据** |

RunID 计数按 seed 计，不按 attempt 计；attempt-3/4 不额外增加计数。

## 6. 后续 gate 待办（不因本协议自动通过）

- overwrite / squash / free-realloc / 连续写 的含住认证样本；
- FR02 两位 bit pair + 几何（相邻/非相邻/跨 lane/跨字段）审计扩展；
- countOnly + fixed uniform ordinal 的 F0 采样实现；
- FR01-b（precision=32）与 FR01-c（NEON lane width）独立 gate。
