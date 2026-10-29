# S04-F0-W5 seed1 — 完整传播路径（真实事件时间顺序）

> 本文只转录该 seed 自己的原始事件流（`prop_evt.txt.gz`）与权威 `chain_report.json`；未修改事件流，未跨 seed 复用任何数值，未把推测写成事件事实。

## 1. 样本身份

| 项 | 值 |
|---|---|
| RunID | `S04-F0-W5` |
| seed | `1` |
| model | `S04`（Store Queue 换值） |
| frequency | `F0` |
| workload | `W5`（W5:sq_forward） |
| binary_path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| binary_source_head | `2498573fddaf67bdbca7b1461443ae9e926e650b` |
| analysis_tool_head | `a92f9f6d807dad397047740e163456b0bcc89ed5` |
| prop_evt_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/S04-F0-W5/seed1/prop_evt.txt.gz` |
| prop_evt_sha256 | `81317d9bf3cc8dde8be3f142efabf3806c92005e62b11904ec0649ba6776ddde` |
| chain_report_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/S04-F0-W5/chain_report.json` |
| chain_report_sha256 | `16243bf8589f24ffd1734a5c97cc42800bbbb10b0e88e657a3f8ac5760948c7c` |
| cell_results_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/S04-F0-W5/cell_results.json` |
| cell_results_sha256 | `26559083931e2197efa7b961cfd1545eb40c6ec96ee54d74216594a01d6b4783` |

## 2. 最终判定

| 项 | 值 |
|---|---|
| oracle outcome | `Masked` |
| terminal | `detected_contained` |
| provable_to | `L5` |
| beyond | `—` |
| admitted | `True` |
| certified | `True` |
| violations | `[]` |
| conservation | `n/a` |
| count_contradiction | `False` |
| truncated | `False` |
| 事件总数 | `13` |
| containment_event_id | `12` |

## 3. 真实注入

| 项 | 值 |
|---|---|
| 注入 tick | `5808880` |
| event_id | `1` |
| parent_event_id | `—` |
| 注入部件 | `CHAOSAddrPath` |
| 注入字段 | `none` |
| 原值 | `0x4903f8` |
| 新值 | `0x490250` |
| mask | `0xff → 0xff` |
| 地址 | `4903f8` |
| request_id | `—` |
| corr | `origin` |
| injected/activated 计数 | `FUNNEL: attempted=774 eligible=412 injected=1`；`CHAOS_L0_FUNNEL: CHAOSAddrPath attempted=774 eligible=412 injected=1 activated=1` |

注入日志原文（本 seed 自己的 `addrpath_injections.log`）：

```text
Tick: 5808880, Site: lsq_pushRequest_PRE, mode=s04_store_subst, old_addr=0x4903f8, new_addr=0x490250, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

运行期触发/检测原文（本 seed 自己的 `seed1/run.out`）：

```text
CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=774 eligible=412 injected=1 first_eligible_tick=140910 last_eligible_tick=5808880 fires=n/a no_effect=n/a (activated=W3-L0-layer)
CHAOS_DETECT: layer=Hardware RAS contained=1 tick=19190325 ptag=1 reason=store_discarded_not_retired
```

## 4. 传播过程（真实事件时间顺序）

本 seed 的 fault_id=1 链共有 13 条真实事件，事件种类序列为：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。以下按该 seed 事件流的原始顺序逐步说明。

**第 1 步** — event_id=1，tick=5808880：L0 故障注入。CHAOSAddrPath 在 lsq_pushRequest_PRE 站点以 s04_store_subst 模式写入一个故障；注入字段 field=none，地址 `4903f8` → `490250`，dyn_inst_seq=4136，corr=origin。该事件无父事件，是整条传播链的根。 下一步：event_id=2（addr_form）以 parent_event_id=1 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 2 步** — event_id=2（parent=1），tick=5808880：L1 地址形成阶段看到注入后的地址值 `4903f8` → `490250`，dyn_inst_seq=4136。注入值在这一步成为第一个被污染的对象（地址计算输入）。 下一步：event_id=3（lsq_push）以 parent_event_id=2 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 3 步** — event_id=3（parent=2），tick=5808880：L1 入队。该请求被推入 store 队列（opcode=strxi_uop，pc=403498，lq_idx=-1，sq_idx=342，dyn_inst_seq=4136）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4（mem_req）以 parent_event_id=3 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 4 步** — event_id=4（parent=3），tick=5808880：L2 请求创建，request_id=4136，va=`490250`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=5（lsq_sendfrag）以 parent_event_id=4 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 5 步** — event_id=5（parent=4），tick=5808880：L2 请求分片，request_id=4136，va=`490250`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=6（tlb_translate）以 parent_event_id=5 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 6 步** — event_id=6（parent=5），tick=5808880：L2 地址翻译，request_id=4136，va=`490250`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=7（sq_execute）以 parent_event_id=6 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 7 步** — event_id=7（parent=6），tick=5808880：L3 sq_execute，request_id=—，va=`490250`，pa=`—`；store 侧继续携带被污染的值。 下一步：event_id=8（sq_writeback）以 parent_event_id=7 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 8 步** — event_id=8（parent=7），tick=5810420：L3 sq_writeback，request_id=—，va=`—`，pa=`76250`；store 侧继续携带被污染的值。 下一步：event_id=9（resp）以 parent_event_id=8 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 9 步** — event_id=9（parent=8），tick=5811190：L3 数据响应返回，request_id=4136，va=`76250`，pa=`—`；响应数据进入 LSQ/寄存器路径。 下一步：event_id=10（taint_reg）以 parent_event_id=9 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 10 步** — event_id=10（parent=9），tick=5811190：L4 污点进入体系结构寄存器，request_id=4136，va=`76250`，corr=seq_primary；污染值离开 LSQ 进入寄存器数据通路。 下一步：event_id=11（sq_complete）以 parent_event_id=10 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 11 步** — event_id=11（parent=10），tick=5811190：L3 sq_complete，request_id=—，va=`490250`，pa=`—`；store 侧继续携带被污染的值。 下一步：event_id=12（store_not_retired）以 parent_event_id=11 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 12 步** — event_id=12（parent=11），tick=19190325：L4 store 未退休即被丢弃，contained=1，request_id=4136；错误的 store 副作用没有落地。 下一步：event_id=13（chain_end）以 parent_event_id=12 承接本事件，共享 fault_id=1 与 dyn_inst_seq=4136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 13 步** — event_id=13（parent=12），tick=19190325：生命周期标记 corr=none，outcome=run_end。它只表示仿真结束，**不是** L5 证据，也从不参与终局判定。 本事件是该 fault 在本 seed 事件流中的最后一条。

## 5. 关键事件表

| 顺序 | event_id | parent_event_id | tick | kind | layer | request_id | corr | 地址/值变化 | 状态变化 | 传播作用 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | — | 5808880 | inj | L0 | — | origin | 4903f8→490250 | — | L0 故障注入 |
| 2 | 2 | 1 | 5808880 | addr_form | L1 | — | origin | 4903f8→490250 | — | L1 地址形成 |
| 3 | 3 | 2 | 5808880 | lsq_push | L1 | — | seq_primary | va=490250 | — | L1 入队（LQ/SQ） |
| 4 | 4 | 3 | 5808880 | mem_req | L2 | 4136 | seq_primary | va=490250 | — | L2 请求创建 |
| 5 | 5 | 4 | 5808880 | lsq_sendfrag | L2 | 4136 | seq_primary | va=490250 | — | L2 请求分片 |
| 6 | 6 | 5 | 5808880 | tlb_translate | L2 | 4136 | seq_primary | va=490250 | — | L2 地址翻译 |
| 7 | 7 | 6 | 5808880 | sq_execute | L3 | — | seq_primary | va=490250 | issued→— | L3 store 执行 |
| 8 | 8 | 7 | 5810420 | sq_writeback | L3 | — | seq_primary | — | —→packet_built | L3 store 回写 |
| 9 | 9 | 8 | 5811190 | resp | L3 | 4136 | seq_primary | va=76250 | — | L3 数据响应 |
| 10 | 10 | 9 | 5811190 | taint_reg | L4 | 4136 | seq_primary | clean→tainted | — | L4 污点进入寄存器 |
| 11 | 11 | 10 | 5811190 | sq_complete | L3 | — | seq_primary | va=490250 | —→completed | L3 store 完成 |
| 12 | 12 | 11 | 19190325 | store_not_retired | L4 | 4136 | taint_prop | — | response_seen_commit_absent→— | L4 未退休即丢弃 |
| 13 | 13 | 12 | 19190325 | chain_end | L4 | — | none | — | contained=1 | 生命周期结束标记（非 L5 证据） |

## 6. 原始证据与哈希

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/S04-F0-W5/seed1/prop_evt.txt.gz` | `81317d9bf3cc8dde8be3f142efabf3806c92005e62b11904ec0649ba6776ddde` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/S04-F0-W5/chain_report.json` | `16243bf8589f24ffd1734a5c97cc42800bbbb10b0e88e657a3f8ac5760948c7c` |
| cell_results | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/S04-F0-W5/cell_results.json` | `26559083931e2197efa7b961cfd1545eb40c6ec96ee54d74216594a01d6b4783` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/S04-F0-W5/seed1/stats.txt` | `0a3ac886519716f8aeecc75dc490ebdf6dc91d0ce2f2cb2fb7fd433e702226b6` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/S04-F0-W5/seed1/run.out` | `23fb6b86a25c59a7691facd4e0ef81a9d655c8dbd52ac151c5121f7e4ed3df57` |
| injections.log | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/S04-F0-W5/seed1/addrpath_injections.log` | `f1c4f38986f5f3e5ebb13a40b929b936b38abd8033c0e65703990da0c27a7351` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1/manifest.json` | `918f2248c63295f8a90dc5687815b9192482b42276f6c810c30f4872100c9624` |

事件流字节数：1169（gzip 后）；解压后事件行数：13；本 fault 事件数：13。

## 7. 可复现命令

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S04-F0-W5_s1 --cells S04-F0-W5 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --timeout 300
```

环境身份：binary SHA-256 `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046`，binary_source_head `2498573fddaf67bdbca7b1461443ae9e926e650b`，analysis_tool_head `a92f9f6d807dad397047740e163456b0bcc89ed5`，matrix SHA-256 `8f2d6227ca76202fa9b5cb2e5ee5489d83a68643b2b987be7e04ac1d8d515fce`。

## 8. 诚实边界

- 本 doc 只证明该 seed 自己的事件流：已证明的层边为 L0->L1, L1->L2, L2->L3, L3->L4, L4->L5；缺失的层边为 （无）。
- 终局 `detected_contained` 与 `provable_to=L5` 直接取自该 seed 的 `chain_report.json`，未做任何推断升级。
- 三方计数：注入日志 `FUNNEL`/`CHAOS_L0_FUNNEL` 与 `run.out` 的 `CHAOS_LSU_TRIGGER` 全部来自本 seed；`stats.txt` 不含 `numFaultsInjected` 统计（addrpath 家族不发射该计数器），故该路为 **n/a**，不以 0 冒充。
- `chain_end` 只是生命周期标记（corr=none），从不作为 L5 证据；本 doc 未把 `chain_end` 当作终局。
- 后续层为 N/A 的含义：本 seed 未在当前事件流中产生该层的真实事件，文档不会补造，也不会据此推断 Masked。
- 本 seed 未重跑；原始事件流未被修改；三个 seed 的数值各自独立，不存在跨 seed 复制。
