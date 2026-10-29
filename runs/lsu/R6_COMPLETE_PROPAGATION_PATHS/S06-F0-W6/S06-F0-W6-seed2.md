# S06-F0-W6 seed2 — 完整传播路径（真实事件时间顺序）

> 本文只转录该 seed 自己的原始事件流（`prop_evt.txt.gz`）与权威 `chain_report.json`；未修改事件流，未跨 seed 复用任何数值，未把推测写成事件事实。

## 1. 样本身份

| 项 | 值 |
|---|---|
| RunID | `S06-F0-W6` |
| seed | `2` |
| model | `S06`（Store Queue 状态） |
| frequency | `F0` |
| workload | `W6`（W6:cache_dirtyevict） |
| binary_path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| binary_source_head | `2498573fddaf67bdbca7b1461443ae9e926e650b` |
| analysis_tool_head | `a92f9f6d807dad397047740e163456b0bcc89ed5` |
| prop_evt_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/S06-F0-W6/seed2/prop_evt.txt.gz` |
| prop_evt_sha256 | `6f3d9637089cb06eb69550037c171372e275daeb44434bb1ca6f7e17e5a3bb18` |
| chain_report_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/S06-F0-W6/chain_report.json` |
| chain_report_sha256 | `6a1e3cd445ee8fdbab029108f05d28c63caacdb66b785e2e96cd175588330556` |
| cell_results_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/S06-F0-W6/cell_results.json` |
| cell_results_sha256 | `b418df99f3d0dd06e24291717d7b2ec0c849887fc22342a89306acf5686f4568` |

## 2. 最终判定

| 项 | 值 |
|---|---|
| oracle outcome | `Masked` |
| terminal | `full` |
| provable_to | `L5` |
| beyond | `—` |
| admitted | `True` |
| certified | `True` |
| violations | `[]` |
| conservation | `n/a` |
| count_contradiction | `False` |
| truncated | `False` |
| 事件总数 | `19` |
| containment_event_id | `19` |

## 3. 真实注入

| 项 | 值 |
|---|---|
| 注入 tick | `3382610` |
| event_id | `1` |
| parent_event_id | `—` |
| 注入部件 | `CHAOSAddrPath` |
| 注入字段 | `none` |
| 原值 | `0x4000f8` |
| 新值 | `0x4000f8` |
| mask | `0xff → 0xff` |
| 地址 | `4000f8` |
| request_id | `—` |
| corr | `origin` |
| injected/activated 计数 | `FUNNEL: attempted=417 eligible=417 injected=1`；`CHAOS_L0_FUNNEL: CHAOSAddrPath attempted=417 eligible=417 injected=1 activated=1` |

注入日志原文（本 seed 自己的 `addrpath_injections.log`）：

```text
Tick: 3382610, Site: lsq_pushRequest_PRE, mode=s06_store_state, old_addr=0x4000f8, new_addr=0x4000f8, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=none, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

运行期触发/检测原文（本 seed 自己的 `seed2/run.out`）：

```text
CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=417 eligible=417 injected=1 first_eligible_tick=80080 last_eligible_tick=3382610 fires=n/a no_effect=n/a (activated=W3-L0-layer)
CHAOS_DETECT: layer=None contained=0 tick=3461150 ptag=1 reason=errant_commit
```

## 4. 传播过程（真实事件时间顺序）

本 seed 的 fault_id=1 链共有 19 条真实事件，事件种类序列为：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → chain_end`。以下按该 seed 事件流的原始顺序逐步说明。

**第 1 步** — event_id=1，tick=3382610：L0 故障注入。CHAOSAddrPath 在 lsq_pushRequest_PRE 站点以 s06_store_state 模式写入一个故障；注入字段 field=none，地址 `4000f8` → `4000f8`，dyn_inst_seq=2033，corr=origin。该事件无父事件，是整条传播链的根。 下一步：event_id=2（addr_form）以 parent_event_id=1 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 2 步** — event_id=2（parent=1），tick=3382610：L1 地址形成阶段看到注入后的地址值 `4000f8` → `4000f8`，dyn_inst_seq=2033。注入值在这一步成为第一个被污染的对象（地址计算输入）。 下一步：event_id=3（lsq_push）以 parent_event_id=2 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 3 步** — event_id=3（parent=2），tick=3382610：L1 入队。该请求被推入 load 队列（opcode=ldr，pc=400efc，lq_idx=146，sq_idx=-1，dyn_inst_seq=2033）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4（mem_req）以 parent_event_id=3 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 4 步** — event_id=4（parent=3），tick=3382610：L2 请求创建，request_id=2033，va=`4000f8`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=5（lsq_sendfrag）以 parent_event_id=4 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 5 步** — event_id=5（parent=4），tick=3382610：L2 请求分片，request_id=2033，va=`4000f8`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=6（tlb_translate）以 parent_event_id=5 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 6 步** — event_id=6（parent=5），tick=3382610：L2 地址翻译，request_id=2033，va=`4000f8`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=7（lq_read）以 parent_event_id=6 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 7 步** — event_id=7（parent=6），tick=3382610：L3 load 读取队列项，request_id=2033，va=`4000f8`，lq_idx=146。被污染的 load 请求在此实际被消费，链到达 L3。 下一步：event_id=8（lsq_push）以 parent_event_id=7 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 8 步** — event_id=8（parent=7），tick=3459610：L1 入队。该请求被推入 load 队列（opcode=ldr，pc=400efc，lq_idx=146，sq_idx=-1，dyn_inst_seq=2033）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=9（mem_req）以 parent_event_id=8 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 9 步** — event_id=9（parent=8），tick=3459610：L2 请求创建，request_id=2033，va=`4000f8`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=10（lsq_sendfrag）以 parent_event_id=9 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 10 步** — event_id=10（parent=9），tick=3459610：L2 请求分片，request_id=2033，va=`4000f8`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=11（tlb_translate）以 parent_event_id=10 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 11 步** — event_id=11（parent=10），tick=3459610：L2 地址翻译，request_id=2033，va=`4000f8`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=12（lq_read）以 parent_event_id=11 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 12 步** — event_id=12（parent=11），tick=3459610：L3 load 读取队列项，request_id=2033，va=`4000f8`，lq_idx=146。被污染的 load 请求在此实际被消费，链到达 L3。 下一步：event_id=13（resp）以 parent_event_id=12 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 13 步** — event_id=13（parent=12），tick=3460380：L3 数据响应返回，request_id=2033，va=`f8`，pa=`—`；响应数据进入 LSQ/寄存器路径。 下一步：event_id=14（lq_complete）以 parent_event_id=13 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 14 步** — event_id=14（parent=13），tick=3460380：L3 load 完成，request_id=2033，va=`4000f8`，pa=`f8`；load 数据已可被后续指令读取。 下一步：event_id=15（taint_reg）以 parent_event_id=14 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 15 步** — event_id=15（parent=14），tick=3460380：L4 污点进入体系结构寄存器，request_id=2033，va=`f8`，corr=seq_primary；污染值离开 LSQ 进入寄存器数据通路。 下一步：event_id=16（errant_commit）以 parent_event_id=15 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 16 步** — event_id=16（parent=15），tick=3461150：L5 错误提交。detection_layer=L5，outcome=errant_commit，corr=taint_prop；带污染值的指令真实退休，这是逃逸终局（不是 chain_end 推断）。 下一步：event_id=17（consumer）以 parent_event_id=16 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2033，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 17 步** — event_id=17（parent=15），tick=3461535：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=18（consumer）以 parent_event_id=17 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2044，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 18 步** — event_id=18（parent=17），tick=3462305：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=19（chain_end）以 parent_event_id=18 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2054，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 19 步** — event_id=19（parent=18），tick=58399880：生命周期标记 corr=none，outcome=run_end。它只表示仿真结束，**不是** L5 证据，也从不参与终局判定。 本事件是该 fault 在本 seed 事件流中的最后一条。

## 5. 关键事件表

| 顺序 | event_id | parent_event_id | tick | kind | layer | request_id | corr | 地址/值变化 | 状态变化 | 传播作用 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | — | 3382610 | inj | L0 | — | origin | 4000f8→4000f8 | — | L0 故障注入 |
| 2 | 2 | 1 | 3382610 | addr_form | L1 | — | origin | 4000f8→4000f8 | — | L1 地址形成 |
| 3 | 3 | 2 | 3382610 | lsq_push | L1 | — | seq_primary | va=4000f8 | — | L1 入队（LQ/SQ） |
| 4 | 4 | 3 | 3382610 | mem_req | L2 | 2033 | seq_primary | va=4000f8 | — | L2 请求创建 |
| 5 | 5 | 4 | 3382610 | lsq_sendfrag | L2 | 2033 | seq_primary | va=4000f8 | — | L2 请求分片 |
| 6 | 6 | 5 | 3382610 | tlb_translate | L2 | 2033 | seq_primary | va=4000f8 | — | L2 地址翻译 |
| 7 | 7 | 6 | 3382610 | lq_read | L3 | 2033 | seq_primary | va=4000f8 | — | L3 load 读取队列 |
| 8 | 8 | 7 | 3459610 | lsq_push | L1 | — | seq_primary | va=4000f8 | — | L1 入队（LQ/SQ） |
| 9 | 9 | 8 | 3459610 | mem_req | L2 | 2033 | seq_primary | va=4000f8 | — | L2 请求创建 |
| 10 | 10 | 9 | 3459610 | lsq_sendfrag | L2 | 2033 | seq_primary | va=4000f8 | — | L2 请求分片 |
| 11 | 11 | 10 | 3459610 | tlb_translate | L2 | 2033 | seq_primary | va=4000f8 | — | L2 地址翻译 |
| 12 | 12 | 11 | 3459610 | lq_read | L3 | 2033 | seq_primary | va=4000f8 | — | L3 load 读取队列 |
| 13 | 13 | 12 | 3460380 | resp | L3 | 2033 | seq_primary | va=f8 | — | L3 数据响应 |
| 14 | 14 | 13 | 3460380 | lq_complete | L3 | 2033 | seq_primary | va=4000f8, pa=f8 | — | L3 load 完成 |
| 15 | 15 | 14 | 3460380 | taint_reg | L4 | 2033 | seq_primary | clean→tainted | — | L4 污点进入寄存器 |
| 16 | 16 | 15 | 3461150 | errant_commit | L5 | — | taint_prop | — | contained=0 | L5 错误提交（逃逸） |
| 17 | 17 | 15 | 3461535 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 18 | 18 | 17 | 3462305 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 19 | 19 | 18 | 58399880 | chain_end | L5 | — | none | — | contained=1 | 生命周期结束标记（非 L5 证据） |

## 6. 原始证据与哈希

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/S06-F0-W6/seed2/prop_evt.txt.gz` | `6f3d9637089cb06eb69550037c171372e275daeb44434bb1ca6f7e17e5a3bb18` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/S06-F0-W6/chain_report.json` | `6a1e3cd445ee8fdbab029108f05d28c63caacdb66b785e2e96cd175588330556` |
| cell_results | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/S06-F0-W6/cell_results.json` | `b418df99f3d0dd06e24291717d7b2ec0c849887fc22342a89306acf5686f4568` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/S06-F0-W6/seed2/stats.txt` | `9ac63af7e1268697025ce375805a3faed4117af4a34e95dfed0885cbbbffb015` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/S06-F0-W6/seed2/run.out` | `71ff9e1057b7dc0822b30f0c73999067c57b888c8fa8263dfc38ec476504d5ea` |
| injections.log | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/S06-F0-W6/seed2/addrpath_injections.log` | `fe3dc871659c5c5bb5e02a2f261faf504f8813ac8e3dcb544e2f2e9b7bbb8ce6` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2/manifest.json` | `9378a451e420dd1da024f67264ef6745b95cf2e52c9c46575d287b3152c8a849` |

事件流字节数：1280（gzip 后）；解压后事件行数：19；本 fault 事件数：19。

## 7. 可复现命令

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S06-F0-W6_s2 --cells S06-F0-W6 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --timeout 300
```

环境身份：binary SHA-256 `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046`，binary_source_head `2498573fddaf67bdbca7b1461443ae9e926e650b`，analysis_tool_head `a92f9f6d807dad397047740e163456b0bcc89ed5`，matrix SHA-256 `8f2d6227ca76202fa9b5cb2e5ee5489d83a68643b2b987be7e04ac1d8d515fce`。

## 8. 诚实边界

- 本 doc 只证明该 seed 自己的事件流：已证明的层边为 L0->L1, L1->L2, L2->L3, L3->L4, L4->L5；缺失的层边为 （无）。
- 终局 `full` 与 `provable_to=L5` 直接取自该 seed 的 `chain_report.json`，未做任何推断升级。
- 三方计数：注入日志 `FUNNEL`/`CHAOS_L0_FUNNEL` 与 `run.out` 的 `CHAOS_LSU_TRIGGER` 全部来自本 seed；`stats.txt` 不含 `numFaultsInjected` 统计（addrpath 家族不发射该计数器），故该路为 **n/a**，不以 0 冒充。
- `chain_end` 只是生命周期标记（corr=none），从不作为 L5 证据；本 doc 未把 `chain_end` 当作终局。
- 后续层为 N/A 的含义：本 seed 未在当前事件流中产生该层的真实事件，文档不会补造，也不会据此推断 Masked。
- 本 seed 未重跑；原始事件流未被修改；三个 seed 的数值各自独立，不存在跨 seed 复制。
