# FR07 真实 PRF-WB 数据边界 hook（v2）与 gate 结果

> 日期：2026-11-04。实现 + 真实 gem5 gate；gate 证据在
> `runs/fsu-gates/FR07-HOOK-GATE-FINAL/`（不计 519，不是正式 seed）。
> 旧的 execute-post-write 三个 seed 仍是 `PROXY_EVIDENCE`，未删除。

## 1. 实现位置与时序

| 阶段 | 代码 | 行为 |
|---|---|---|
| arm（execute 前） | `dyn_inst.cc` → `CHAOSFPU::maybeArm()` | 用与 census 相同的 eligible 谓词选目标；固定 faultMask；快照目的 PRF 到 shadow |
| FU 写结果 | `CPU::getWritableReg()` / `CPU::setReg()` | 向量目的写入 shadow WB buffer；标量 FP 在 `regFile.setReg()` **之前**套 mask |
| commit 到 PRF | `CHAOSFPU::finalizeWb()` | 对 shadow 的目标 lane 施加 mask，然后一次性写入 PRF；golden 值记录在 `before` |
| wakeup | `IEW::writebackInsts()` → `CHAOSFPU::noteProducerWakeup()` | 发射 `wakeup` 事件（parent=L0，含 dependents） |
| squash | `DynInst::setSquashed()` → `CHAOSFPU::noteSquash()` | 取消/记录 squash，撤销 taint，禁止后续复用寄存器误连 |
| commit | `Commit::commitHead()` → `CHAOSFPU::noteCommit()` | 退休 pending 记录 |

关键点：PRF 在 `finalizeWb()` 之前不会持有未加 mask 的 FU 结果（向量走
shadow；标量在 store 前套 mask）。这不是“最终数值相同”的口头等价，而是
写入边界本身。

## 2. L0 事件新增字段（真实发射）

`injection_site=prf_wb_data`、`hook_version=2`、`producer_seq`、
`dest_operand`、`arm_tick`、`writeback_tick`、`wakeup_pending`；
producer `wakeup` 事件带 `wakeup_tick`、`wakeup_dependents`；
squash 事件带 `squash_tick`、`outcome=squashed_[before|after]_wakeup`。
字段已注册到 `tools/fsu_prop_fields.py` 与
`CHAOSPropagation.hh` 的 FSU 扩展表。

## 3. Gate 结果（真实 gem5，seed1）

| gate | 配置 | 结果 |
|---|---|---|
| FP32 scalar | mask 0x80000000, fp32/32/0 | **admitted, full, SDC** |
| FP64 scalar | mask 0x8000000000000000, fp64/64/0 | **admitted, full, SDC** |
| NEON lane2 | mask 0x80000000, fp32 lane_width32 lane_offset2 | **admitted, full, SDC** |
| 双 bit | mask 0x80000001（popcount=2） | **admitted, full, SDC** |
| precision mismatch 负例 | fp64/64/0 on fp32 NEON | eligible=0，无 fault_applied（按预期拒绝） |
| 非 FP 目的 负例 | integer-only workload | eligible=0，无 fault_applied（按预期拒绝） |

双 bit 实测：`fault_mask=0x80000001`，`before=0x7fc00001`，
`after=0xffc00000`，`before ^ after = 0x80000001`（popcount=2）。

## 4. Squash / replay 真实证据

`workloads/directed/fp_branch_squash_probe`：分支条件依赖 32 级
pointer-chase 加载链，预测失败时已执行的 FP 结果必须被 squash。

实测 seed2（`runs/fsu-gates/FR07-HOOK-SQUASH9/.../attempt-1`）事件序列：

```
fault_applied (L0, tick 1998390240, phys_reg=32)
carrier_state (L1, same tick)
wakeup        (parent=L0, wakeup_dependents=1, same tick)
squash        (parent=L0, squash_tick=1998634715, outcome=squashed_after_wakeup)
chain_end     (parent=squash)
```

- 恰好 1 个 `fault_applied`：重放/后续动态指令没有第二次注入；
- squash 之后没有任何 `operand_read/execute/commit` 被错误归到该 fault
  （修复前同一 phys_reg 被复用后曾误连出 L5 链；已加 `squashed` taint 撤销）；
- 运行 oracle 为 Masked（故障未传播），这是 squash gate 的预期结局，
  不是模拟器失败，也不作为正式 seed。

## 5. 计数与后续

- 旧 FR07-F0-W1 三个 proxy seed 仍不计认证（历史 47/519、活跃 38/240）。
- 本 gate 不计 519。下一步按预注册 manifest 跑真实 FR07-F0-W1 的
  seed1→seed2→seed3；通过后历史 +3、活跃 +3。
- 旧 proxy attempt 保留；新 seed 使用新的 attempt（同一 seed 目录，
  AUTHORITATIVE 指向真实 hook attempt）。

## 6. 复现命令

```bash
python3 tools/fsu_seed_runner.py --manifest configs/fsu/FSU-FR07-F0-W1-HOOK-FP32-GATE.json \
  --seed 1 --out-root runs/fsu-gates/FR07-HOOK-GATE-FINAL
# FP64 / W3 lane / dual-bit / squash / negatives 同理
```

## 7. 正式 seed 结果（真实 hook）

| RunID | seed | 结果 | 关键证据 |
|---|---|---|---|
| FSU-FR07-F0-W1 | 1/2/3 | admitted/full/SDC；audit ok | FP32 sign、双 bit、FP32 mantissa field；injection_site=prf_wb_data |
| FSU-FR07-F0-W3 | 1/2/3 | admitted/full/SDC；audit ok | lane2 sign（bit95）、lane2 bits31+0、lane2 FP32 mantissa field；其他 lane 逐字节不变 |
| FSU-FR07-F0-W5 | 1/2/3（suite） | suite_admitted=True，5/5 component；每 suite seed 计 1 | 五程序 fixed suite；component 事件均 injection_site=prf_wb_data；suite_hash cddba2cc… |

计数：历史 **56/519 seed、18/173 RunID**；活跃 F0/F5 **47/240、15/80**。
suite seed 21、component 87；旧 FR07-W1 proxy attempt 保留但不计认证。

`runs/fsu/FSU-FR07-F0-W1/seed{1,2,3}/attempt-2/`、
`runs/fsu/FSU-FR07-F0-W3/seed{1,2,3}/attempt-1/`、
`runs/fsu/FSU-FR07-F0-W5/seed{1,2,3}/`。
