# R6-A2 证据层修复与真实终局事件（2026-10-28）

## 构建

- 源 HEAD：`748bd8f7` + 本提交工作树（evidence/terminal 改动）。
- `cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt` → `EXIT=0`，0 error；
  新增代码 0 warning（日志中仅既有 CHAOSCache -Wreorder / CHAOSPrefetch
  -Wswitch / 缺 capstone/png/HDF5 的宿主警告）。
- 二进制 `CHAOS/gem5/build/ARM/gem5.opt`
  sha256 `3e9a366badd722b097b2ec5463052ff228f2b2c61a47b1809baba64d7ccb146e`。

## P0 修复：split 响应 data_fnv 空指针

`CHAOSPropagation::noteMemResponse` 对 `pkt->hasData()` 的 split 响应无条件
`getPtr<uint8_t>()`，空指针进入 `fnv1a64` 触发宿主机 SIGSEGV，截断整条证据流。
现在仅在指针非空时计算，否则记 `data_fnv=unavailable`（诚实标注）。

## 新增真实终局事件（不是 chain_end 冒充）

| 事件 | 发射点 | 语义 | 收口层 |
|---|---|---|---|
| `arch_translation_fault` | `sim/faults.cc::GenericPageTableFault::invoke` | SE 页表错误真实交付 guest（SEGV）；仅当 VA 命中已登记注入范围 | L2 |
| `squash_discarded` | `LSQUnit::squash` load/store 弹出点 | 携带注入故障的指令被真实丢弃 | L4 |
| `store_not_retired` | `CHAOSPropagation` 退出回调 | store 响应已观察、自身 commit 从未观察（独立事件，非 chain_end） | L4 |

门禁只接受：非生命周期 kind + 非空 detection_layer/outcome + 链关联 corr +
L0→事件前缀可证。`arch_translation_fault` 额外要求 `contained=1`（真实交付）。

## 真实 canary（本二进制，propagation on）

### E1：A01-F2-W3 seed1（F2 first-fire 106412，repeat=434）

```
arch_translation_fault fault_id=1 event_id=8 parent=7
  detection_layer=L2 contained=1 outcome=arch_exception
  corr=seq_primary containment_reason=arch_translation_fault_delivered
```

`check_chain`：`terminal=detected_contained`；`containment_from_events`
返回 `layer=L2`（修复前：`detected_translation_outcome_pending`）。
证据：`/tmp/r6a2_e1_canary`（临时 canary），stats 257457B，gzip 完整。

### E3：A04-F0-W3 seed1 / A05-F0-W3 seed1 / A08-F0-W3 seed1

load 被真实 squash：
`squash_discarded field=load detection_layer=L4 contained=1 outcome=contained
corr=seq_primary` → `terminal=detected_contained`，`layer=L4`。
证据：`/tmp/r6a2_e4_canary`、`/tmp/r6a2_scan_*`。

### E4：A04-F0-W3 seed3（store 样本）

13 事件链：`inj→addr_form→lsq_push→mem_req→lsq_sendfrag→tlb_translate→
sq_execute→sq_writeback→resp→taint_reg→sq_complete→store_not_retired→
chain_end`；`store_not_retired` 带 `corr=taint_prop`、`detection_layer=L4`、
`outcome=contained`、`last_state=response_seen_commit_absent`
→ `terminal=detected_contained`。

## 负向门禁

`tests/test_lsu_r6a2_gate_negatives.py`：truncated / open chain /
chain_end-only / 未知终局 / corr=none / 无前缀 全部拒绝；
合法 squash 正对照仍收口。`tests/test_lsu_chain_check.py` 与
`tests/test_lsu_r6_contained_chain_contract.py` 全 PASS。
