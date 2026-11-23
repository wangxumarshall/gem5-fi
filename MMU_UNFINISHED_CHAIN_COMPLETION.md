# MMU 剩余 23 条传播链补全 — 完成报告

Round 0202c · `gem5-fi-mmu-when5x3` · 2026-11-17
No git commit / push.  Frozen Where/When semantics unchanged; original 117
Fault / 39 Control raw data untouched; new re-runs in `runs/W5X3_RETRY2/`.

## 1. 最终状态（120 条件）

| 状态 | 数量 |
|---|---|
| FULL | **117** |
| PARTIAL | **0**（上一轮为 23） |
| N/A | 3（M06-C05，冻结配置可行性边界） |

逐模型：

| Model | FULL | N/A |
|---|---:|---:|
| M01 | 15 | 0 |
| M02 | 15 | 0 |
| M03 | 15 | 0 |
| M04 | 15 | 0 |
| M05 | 15 | 0 |
| M06 | 12 | 3 |
| M07 | 15 | 0 |
| M08 | 15 | 0 |

相较上一轮 94 FULL / 23 PARTIAL：**FULL +23**（正是此前剩余的全部 23 条）。

## 2. 实际补采：新增 gem5 观测埋点（observation-only）

不允许修改冻结 Where/Context/Timing 与故障操作语义，只新增观测事件与关联 ID。

### 2.1 取指传播链（12 条）— IFU response/decode/commit

M03-C02 / M04-C02 / M05-C02 / M07-C05 此前止步于 Execute `lsu_request`
（合成取指事务没有真实 DynInst seq）。新增：

- `CHAOSPropagation`: `mmuNoteLsuRequest` 用真实 `Request` 对象身份登记
  取指翻译 id（`mmu_req_txn[req.get()]`）；`mmuTakeFetchTxn` /
  `mmuNoteIfuResponse` / `mmuRegisterFetchSeq` 发射 `ifu_response`、
  `ifu_decode`，并把 DynInst seq 绑定回取指事务（`mmu_seq_txn[seq]=tid`、
  `mmu_traced_seqs.insert(seq)`），使既有 `mmuNoteCommit`/`mmuNoteSquash`
  对取指指令的提交/冲刷打上 fault 标。
- `fetch.cc` / `fetch.hh`: `fetchBufferTxnId[tid]` 在 `finishTranslation`
  恢复取指事务 id，在 `processCacheCompletion` 发射真实 IFU 响应，在
  `buildInst` 注册每个来自错误取指行的 DynInst。

结果（M03-C02-T01 为例，translation_id=5）：
`mmu_fault_activate → tlb_lookup_hit(decoy) → tlb_entry_insert →
permission_eval → translation_result → lsu_request(Execute) → ifu_response
→ ifu_decode(dyn_inst_seq=25252420/21) → commit(fault_id=1)`，全链以
`translation_id` + 真实 `dyn_inst_seq` 关联。

### 2.2 M05 数据侧提交消费者（6 C04/C05 + 3 C03 掩盖）

M05 损坏 partial entry；真正提交 decoy 值的消费者是对被错误 walk 填充的
DTB entry 的**暖命中**负载。此前暖命中不打标。新增：

- `mmuNoteEntryInsert`: M05 下把每个 fault-tagged 完整 entry insert 登记入
  entry-fault 注册表（`mmuRegisterEntryFault(...,"M05")`）。
- `tlb.cc`: `phase3_entry_model` 引入 M05；暖命中消费事务创建受
  `MMU_CONSUMER_REUSE_CAP=16` 界（`mmuEntryFaultReuseCapped`），避免对
  数万次重读的放大。

结果（M05-C04-T01）：`partial_entry_insert → tlb_entry_insert(DTB decoy)
→ fault_entry_reuse → translation_result(decoy PA) → lsu_request →
memory_response → rf_writeback → commit(fault_id=1)`，到达真实提交消费者。

### 2.3 M07-C02 掩盖（2 条）

M07 反转 grant 后翻译成功并发出 lsu_request，但响应在 ROI 结束前未到达、
值未被消费。新增 `mmu_fault_summary.masked_reason =
request_issued_not_completed_at_roi_end`，显式命名掩盖机制（不再是无事件的
“未消费”）。

## 3. 关联边修复（9 条 M05 数据侧）

`partial_entry_insert → tlb_entry_insert → fault_entry_reuse` 的
跨条目交接此前是 UNKNOWN。`propagation.py` 新增 `fault_entry_lineage` 边
依据（同一 fault_id 链 + partial→DTB-entry 结构）与 M05 交接桥恢复，使
mutation→consume 边显式。

## 4. 证据索引与报告一致性修复

- `analysis/retry2_map.json`（SampleRunID → RETRY2 run id）、
  `analysis/retry2_evidence_index.json`（run id + trace 路径 + trace SHA +
  build SHA + rc + activation_count）。
- `finalize.py` / `export_evidence.py` / `acceptance.py` / `validate.py`
  统一经 `retry2_map.json` 解析 fault manifest / ActualOrdinal / oracle /
  EvidencePath，彻底修复“EvidenceSource 用原始路径、Trace SHA 属于 RETRY
  文件”的不一致。

## 5. 构建与验证

- gem5 观测二进制（两个，仅观测差异）：
  - `eb327197c073dddf…`（IFU + masked_reason）
  - `fb1b6f010034f273…`（追加 `MMU_CONSUMER_REUSE_CAP` 界；仅影响 M05
    数据路径 trace 体积，不改故障语义）
- 8 个匹配 Control 全部复现冻结 N（M03/M05/M07 N=3、M04 N=20005、
  M07-C02 N=6）。
- 23 条 Fault 全部 rc=0、activation_count=1、actual ordinal == 计划。
- `campaign/validate.py`：**ALL CHECKS PASSED**。
- A01–A22：全部 PASS（A22 范围声明保留）。

## 6. 保留的唯一技术限制

- M06-C05（3 条）为**冻结配置可行性边界**（speculative wrong-path：冻结
  O3 fetch 不预测间接分支目标），由 pilot 验证，非全局不可行声明，见
  `blocked_tasks.md`。

其余 117 条全部获得完整因果链与真实终点。