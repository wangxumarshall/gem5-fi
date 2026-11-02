# 试点 FSU-FP04-F0-W4：C++ 传播事件发射契约

> 状态：实现前契约（2026-11-02）。发射端落地后，任何偏离必须在
> `chain_report.json` 中显式记录，不得静默改写。

## 1. 目标链

```
L0 fault_applied       CHAOSFPU 在 FSU 结果上施加位翻转
L1 carrier_state       目标物理寄存器确实持有错误值
L2 operand_read        消费者读取该物理寄存器（真实消费 = activated）
L3 execute             消费者为 FP/FSU 操作时，用错误操作数执行
L4 prf_writeback /     消费者的结果/存储副作用进入架构可见路径
   consumer
L5 commit              errant commit（真实架构错误提交）或显式含住
```

- FP04 是结果侧故障：L3 对“存储消费者”不适用时，链审计器把 L3 记
  `layers_na`（N/A），不伪造事件。
- `chain_end` 只是退出回调的生命周期收口，层映射为 None，永不冒充 L5。
- 若故障值在提交前被 squash/覆盖，发射 `squash`/`overwrite`（真实含住），
  后续层 N/A；不得为“完整”伪造 L5。

## 2. 复用统一流

- 发射端复用 `CHAOSPropagation::notePropEvt` 与 `prop_evt.txt.gz`
  （`PROP-EVT:` 前缀）；FSU 事件是统一流中的带 `model_id` 子集。
- `notePropEvt` 改为返回分配的 `event_id`；调用方用返回值设置
  `parent_event_id`，形成直接 parent 链；不得依赖默认游标拼接旁支。
- FSU 扩展字段加入 `PROP_EVT_EXT_FIELDS`（不扩共享 41 字段注册表，
  避免破坏 LSU 的 1:1 镜像约定）：
  `model_id, submodel, unit, freq, load_id, iq_slot, src_slot,
   producer_seq, consumer_seq, reg_generation, lane_width, lane_offset,
   lane_mask, fu_class, fu_index, bit_indices, before_hash, after_hash,
   value_hash, eligible_ordinal, eligible_total, attempted, activated,
   burst_id, burst_ordinal, burst_length, golden_id, config_hash,
   binary_hash, terminal`。

## 3. CHAOSFPU 注入点（L0/L1）

`CHAOSFPU::maybeCorrupt(dyn_inst)` 在成功改写目标后：

1. 记录 `FaultedReg{(tid, regClass, index), fault_id, l0_id, l1_id,
   producer_sn, tick, before, after, mask, bitseg}`；
2. 发射 `fault_applied`：
   - `model_id/submodel/freq/load_id` 来自 CHAOSFPU 参数；
   - `dyn_inst_seq=seqNum`、`pc`、`opcode`、`phys_reg`、`field=bitseg/mode`、
     `fault_mask`、`bit_indices=ctz(mask)`、`lane_width=64`、`lane_offset=0`、
     `before/after`（16-hex）、`before_hash/after_hash`（FNV-1a）、
     `attempted=1`、`activated=`（apply 时未知）；
3. 发射 `carrier_state`（parent=L0）：同一目标寄存器，`after_hash`；
4. 返回 true 后继续原有日志/计数，不改变注入语义。

## 4. 消费者与 activated（L2）

在 `DynInst::getRegOperand` 的两个重载中调用
`CHAOSFPU::noteOperandRead(this, reg, idx)`：

- 若 `(tid,class,index)` 命中活动 `FaultedReg` 且该消费者尚未记录：
  发射 `operand_read`（parent=L1），字段：
  `producer_seq=faulted.producer_sn`、`consumer_seq=this->seqNum`、
  `src_slot=idx`、`phys_reg`、`pc`、`opcode`、`activated=1`、
  `value_hash`（读取时值）；
- 建立 `TaintedConsumer{consumer_sn, fault_id, l2_id, is_store}`；
- `activated` 的定义是**故障值被真实读取**，不是“注入了”；
- 未命中的读取不发射事件（零回归）。

## 5. 消费者执行/写回（L3/L4）

- `DynInst::execute()` 在现有 `maybeCorrupt` 之后调用
  `CHAOSFPU::noteConsumerExecute(this)`：
  - 若该指令是 `TaintedConsumer` 且 opClass 为 FP/FSU：发射 `execute`
    （parent=L2），随后发射 `prf_writeback`（parent=L3，观察点为
    execute 结束、PRF blob 已写入）；
  - 非 FP 消费者（例如 store）不伪造 L3；`is_store` 记录留给提交点。
- 提交点（见 §6）若发现 `is_store` 且无 L3/L4：发射 `consumer`
  （parent=L2）作为真实 L4（存储的架构可见副作用），再发 L5。

## 6. 提交与含住（L5）

在 `Commit::commitHead` 现有 `chaosPropagation->noteCommit` 旁调用
`CHAOSFPU::noteCommit(tid, inst)`：

- 若该指令是 `TaintedConsumer`：
  - 无 L4 时补发 `consumer`（parent=L2）；
  - 发射 `commit`：`detection_layer=L5`、`outcome=errant_commit`、
    `commit_seq=seqNum`、`oracle_diff=`（由 runner 的 oracle 另行记录）、
    `corr=fsu_taint`；
- 若该指令在提交前 squash：`noteSquash(inst)` 发射 `squash`
  （`detection_layer=L4`、`contained=1`、`outcome=squashed`），
  后续 L5 N/A；
- 退出回调：对从未被消费的 `FaultedReg` 发射 `not_activated`
  （parent=L1，`activated=0`），保证 terminal=not_activated，而非未知 Masked。

## 7. ooo_proxy 接线

在 `configs/se/ooo_proxy.py` 增加：

```
--chaos_propagation --prop_trace_file --prop_run_id --prop_sample_run_id
--fsu_model --fsu_freq --fsu_load --fsu_submodel --fsu_eligible_total
```

并像 `lsu_proxy.py` 一样实例化 `CHAOSPropagation(cpu=cpu0, ...)`，
在 `--chaos_fpu` 时把 FSU 参数传给 CHAOSFPU。所有新参数默认关闭/空，
不改变既有 campaign 的行为。

## 8. 非目标与诚实边界

- 不在本试点实现 FQ/FR 的全部模型；不把 CHAOSFPU 的结果侧代理冒充
  门级 FSU 复刻。
- 不伪造 L5；`chain_end` 不占层；缺事件写 Unknown。
- 真实运行仍以 `runs/fsu/<RunID>/seed<N>/attempt-<k>/` 的原始证据为准；
  本契约只定义发射端，不产生任何实验结论。
