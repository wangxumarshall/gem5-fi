# S07-F0-W5 seed2 — 完整传播路径（真实事件时间顺序）

> 本文只转录该 seed 自己的原始事件流（`prop_evt.txt.gz`）与权威 `chain_report.json`；未修改事件流，未跨 seed 复用任何数值，未把推测写成事件事实。

## 1. 样本身份

| 项 | 值 |
|---|---|
| RunID | `S07-F0-W5` |
| seed | `2` |
| model | `S07`（Store Queue 换值） |
| frequency | `F0` |
| workload | `W5`（W5:sq_forward） |
| binary_path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| binary_source_head | `2498573fddaf67bdbca7b1461443ae9e926e650b` |
| analysis_tool_head | `a92f9f6d807dad397047740e163456b0bcc89ed5` |
| prop_evt_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/S07-F0-W5/seed2/prop_evt.txt.gz` |
| prop_evt_sha256 | `ce442ca171b5d0aba3d9a69fe76b5e1e502d47023af20ff164c9cbfc7dc68eb1` |
| chain_report_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/S07-F0-W5/chain_report.json` |
| chain_report_sha256 | `c06c8425fd613eaa6b512ce5b8f817e91b35515a35b1e8b4266ce12734fc9700` |
| cell_results_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/S07-F0-W5/cell_results.json` |
| cell_results_sha256 | `af88fc2a170832cc43b4566cb6828103c1a0f2aae9c5fe9f153902a2bda436f5` |

## 2. 最终判定

| 项 | 值 |
|---|---|
| oracle outcome | `Masked` |
| terminal | `detected_contained` |
| provable_to | `L3` |
| beyond | `—` |
| admitted | `True` |
| certified | `True` |
| violations | `[]` |
| conservation | `n/a` |
| count_contradiction | `False` |
| truncated | `False` |
| 事件总数 | `9` |
| containment_event_id | `8` |

## 3. 真实注入

| 项 | 值 |
|---|---|
| 注入 tick | `3001075` |
| event_id | `1` |
| parent_event_id | `—` |
| 注入部件 | `CHAOSAddrPath` |
| 注入字段 | `none` |
| 原值 | `0x7ffffefca0` |
| 新值 | `0x7ffffefc40` |
| mask | `0xff → 0xff` |
| 地址 | `7ffffefca0` |
| request_id | `—` |
| corr | `origin` |
| injected/activated 计数 | `FUNNEL: attempted=417 eligible=417 injected=1`；`CHAOS_L0_FUNNEL: CHAOSAddrPath attempted=417 eligible=417 injected=1 activated=1` |

注入日志原文（本 seed 自己的 `addrpath_injections.log`）：

```text
Tick: 3001075, Site: lsq_pushRequest_PRE, mode=s07_store_ptr, old_addr=0x7ffffefca0, new_addr=0x7ffffefc40, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

运行期触发/检测原文（本 seed 自己的 `seed2/run.out`）：

```text
CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=417 eligible=417 injected=1 first_eligible_tick=80080 last_eligible_tick=3001075 fires=n/a no_effect=n/a (activated=W3-L0-layer)
（无 CHAOS_DETECT 行）
```

## 4. 传播过程（真实事件时间顺序）

本 seed 的 fault_id=1 链共有 9 条真实事件，事件种类序列为：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → squash_discarded → chain_end`。以下按该 seed 事件流的原始顺序逐步说明。

**第 1 步** — event_id=1，tick=3001075：L0 故障注入。CHAOSAddrPath 在 lsq_pushRequest_PRE 站点以 s07_store_ptr 模式写入一个故障；注入字段 field=none，地址 `7ffffefca0` → `7ffffefc40`，dyn_inst_seq=2120，corr=origin。该事件无父事件，是整条传播链的根。 下一步：event_id=2（addr_form）以 parent_event_id=1 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 2 步** — event_id=2（parent=1），tick=3001075：L1 地址形成阶段看到注入后的地址值 `7ffffefca0` → `7ffffefc40`，dyn_inst_seq=2120。注入值在这一步成为第一个被污染的对象（地址计算输入）。 下一步：event_id=3（lsq_push）以 parent_event_id=2 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 3 步** — event_id=3（parent=2），tick=3001075：L1 入队。该请求被推入 store 队列（opcode=strxi_uop，pc=40b5b8，lq_idx=-1，sq_idx=148，dyn_inst_seq=2120）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4（mem_req）以 parent_event_id=3 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 4 步** — event_id=4（parent=3），tick=3001075：L2 请求创建，request_id=2120，va=`7ffffefc40`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=5（lsq_sendfrag）以 parent_event_id=4 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 5 步** — event_id=5（parent=4），tick=3001075：L2 请求分片，request_id=2120，va=`7ffffefc40`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=6（tlb_translate）以 parent_event_id=5 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 6 步** — event_id=6（parent=5），tick=3001075：L2 地址翻译，request_id=2120，va=`7ffffefc40`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=7（sq_execute）以 parent_event_id=6 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 7 步** — event_id=7（parent=6），tick=3001075：L3 sq_execute，request_id=—，va=`7ffffefc40`，pa=`—`；store 侧继续携带被污染的值。 下一步：event_id=8（squash_discarded）以 parent_event_id=7 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 8 步** — event_id=8（parent=7），tick=3046890：L4 检测并包含。state_before=`store_queue_uncommitted`，contained=1，containment_reason=squash_discarded，request_id=2120；该 store 在提交前被 squash 并从队列丢弃，错误值没有写入体系结构状态。 下一步：event_id=9（chain_end）以 parent_event_id=8 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 9 步** — event_id=9（parent=8），tick=19190325：生命周期标记 corr=none，outcome=run_end。它只表示仿真结束，**不是** L5 证据，也从不参与终局判定。 本事件是该 fault 在本 seed 事件流中的最后一条。

## 5. 关键事件表

| 顺序 | event_id | parent_event_id | tick | kind | layer | request_id | corr | 地址/值变化 | 状态变化 | 传播作用 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | — | 3001075 | inj | L0 | — | origin | 7ffffefca0→7ffffefc40 | — | L0 故障注入 |
| 2 | 2 | 1 | 3001075 | addr_form | L1 | — | origin | 7ffffefca0→7ffffefc40 | — | L1 地址形成 |
| 3 | 3 | 2 | 3001075 | lsq_push | L1 | — | seq_primary | va=7ffffefc40 | — | L1 入队（LQ/SQ） |
| 4 | 4 | 3 | 3001075 | mem_req | L2 | 2120 | seq_primary | va=7ffffefc40 | — | L2 请求创建 |
| 5 | 5 | 4 | 3001075 | lsq_sendfrag | L2 | 2120 | seq_primary | va=7ffffefc40 | — | L2 请求分片 |
| 6 | 6 | 5 | 3001075 | tlb_translate | L2 | 2120 | seq_primary | va=7ffffefc40 | — | L2 地址翻译 |
| 7 | 7 | 6 | 3001075 | sq_execute | L3 | — | seq_primary | va=7ffffefc40 | issued→— | L3 store 执行 |
| 8 | 8 | 7 | 3046890 | squash_discarded | L4 | 2120 | seq_primary | — | store_queue_uncommitted→— | L4 检测并 squash 丢弃 |
| 9 | 9 | 8 | 19190325 | chain_end | — | — | none | — | contained=0 | 生命周期结束标记（非 L5 证据） |

## 6. 原始证据与哈希

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/S07-F0-W5/seed2/prop_evt.txt.gz` | `ce442ca171b5d0aba3d9a69fe76b5e1e502d47023af20ff164c9cbfc7dc68eb1` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/S07-F0-W5/chain_report.json` | `c06c8425fd613eaa6b512ce5b8f817e91b35515a35b1e8b4266ce12734fc9700` |
| cell_results | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/S07-F0-W5/cell_results.json` | `af88fc2a170832cc43b4566cb6828103c1a0f2aae9c5fe9f153902a2bda436f5` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/S07-F0-W5/seed2/stats.txt` | `eb7aacbc946ec277bba04b9f10aaedf0b57f488fbe8e315bba464959eaf522cc` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/S07-F0-W5/seed2/run.out` | `a956f32ec270d2202df569a94f188f7826beb66d7bb819276a2770a50529e4c5` |
| injections.log | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/S07-F0-W5/seed2/addrpath_injections.log` | `c6bf8e1dffa06bcc8c42d026431c4c4fbebeba87c0f89c79fab81f6031a25ec6` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2/manifest.json` | `273d8b9b22c2efc23cec569ffe31f596fc4b9c57bf9eabf2d9262cc309c39a20` |

事件流字节数：963（gzip 后）；解压后事件行数：9；本 fault 事件数：9。

## 7. 可复现命令

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s2 --cells S07-F0-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --timeout 300
```

环境身份：binary SHA-256 `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046`，binary_source_head `2498573fddaf67bdbca7b1461443ae9e926e650b`，analysis_tool_head `a92f9f6d807dad397047740e163456b0bcc89ed5`，matrix SHA-256 `8f2d6227ca76202fa9b5cb2e5ee5489d83a68643b2b987be7e04ac1d8d515fce`。

## 8. 诚实边界

- 本 doc 只证明该 seed 自己的事件流：已证明的层边为 L0->L1, L1->L2, L2->L3；缺失的层边为 L3->L4, L4->L5。
- 终局 `detected_contained` 与 `provable_to=L3` 直接取自该 seed 的 `chain_report.json`，未做任何推断升级。
- 三方计数：注入日志 `FUNNEL`/`CHAOS_L0_FUNNEL` 与 `run.out` 的 `CHAOS_LSU_TRIGGER` 全部来自本 seed；`stats.txt` 不含 `numFaultsInjected` 统计（addrpath 家族不发射该计数器），故该路为 **n/a**，不以 0 冒充。
- `chain_end` 只是生命周期标记（corr=none），从不作为 L5 证据；本 doc 未把 `chain_end` 当作终局。
- 后续层为 N/A 的含义：本 seed 未在当前事件流中产生该层的真实事件，文档不会补造，也不会据此推断 Masked。
- 本 seed 未重跑；原始事件流未被修改；三个 seed 的数值各自独立，不存在跨 seed 复制。
