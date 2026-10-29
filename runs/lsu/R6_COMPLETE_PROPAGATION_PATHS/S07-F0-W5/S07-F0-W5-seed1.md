# S07-F0-W5 seed1 — 完整传播路径（真实事件时间顺序）

> 本文只转录该 seed 自己的原始事件流（`prop_evt.txt.gz`）与权威 `chain_report.json`；未修改事件流，未跨 seed 复用任何数值，未把推测写成事件事实。

## 1. 样本身份

| 项 | 值 |
|---|---|
| RunID | `S07-F0-W5` |
| seed | `1` |
| model | `S07`（Store Queue 换值） |
| frequency | `F0` |
| workload | `W5`（W5:sq_forward） |
| binary_path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| binary_source_head | `2498573fddaf67bdbca7b1461443ae9e926e650b` |
| analysis_tool_head | `a92f9f6d807dad397047740e163456b0bcc89ed5` |
| prop_evt_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/S07-F0-W5/seed1/prop_evt.txt.gz` |
| prop_evt_sha256 | `d5e61f32f8cf910f55d3b550088c33dc7c56d63eeb737555a5415492466526a9` |
| chain_report_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/S07-F0-W5/chain_report.json` |
| chain_report_sha256 | `285adb1b33e778fa85e42fdd4180d901d56541f8d0df2a3a970174c557985d2c` |
| cell_results_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/S07-F0-W5/cell_results.json` |
| cell_results_sha256 | `7534c980923111e71afb3279e2cc4067cdf8253e73472a2ea6b3f459a357d247` |

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
| 事件总数 | `12` |
| containment_event_id | `11` |

## 3. 真实注入

| 项 | 值 |
|---|---|
| 注入 tick | `2996840` |
| event_id | `1` |
| parent_event_id | `—` |
| 注入部件 | `CHAOSAddrPath` |
| 注入字段 | `none` |
| 原值 | `0x4000c0` |
| 新值 | `0x400080` |
| mask | `0xff → 0xff` |
| 地址 | `4000c0` |
| request_id | `—` |
| corr | `origin` |
| injected/activated 计数 | `FUNNEL: attempted=412 eligible=412 injected=1`；`CHAOS_L0_FUNNEL: CHAOSAddrPath attempted=412 eligible=412 injected=1 activated=1` |

注入日志原文（本 seed 自己的 `addrpath_injections.log`）：

```text
Tick: 2996840, Site: lsq_pushRequest_PRE, mode=s07_store_ptr, old_addr=0x4000c0, new_addr=0x400080, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

运行期触发/检测原文（本 seed 自己的 `seed1/run.out`）：

```text
CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=412 eligible=412 injected=1 first_eligible_tick=80080 last_eligible_tick=2996840 fires=n/a no_effect=n/a (activated=W3-L0-layer)
（无 CHAOS_DETECT 行）
```

## 4. 传播过程（真实事件时间顺序）

本 seed 的 fault_id=1 链共有 12 条真实事件，事件种类序列为：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → squash_discarded → chain_end`。以下按该 seed 事件流的原始顺序逐步说明。

**第 1 步** — event_id=1，tick=2996840：L0 故障注入。CHAOSAddrPath 在 lsq_pushRequest_PRE 站点以 s07_store_ptr 模式写入一个故障；注入字段 field=none，地址 `4000c0` → `400080`，dyn_inst_seq=2095，corr=origin。该事件无父事件，是整条传播链的根。 下一步：event_id=2（addr_form）以 parent_event_id=1 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 2 步** — event_id=2（parent=1），tick=2996840：L1 地址形成阶段看到注入后的地址值 `4000c0` → `400080`，dyn_inst_seq=2095。注入值在这一步成为第一个被污染的对象（地址计算输入）。 下一步：event_id=3（lsq_push）以 parent_event_id=2 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 3 步** — event_id=3（parent=2），tick=2996840：L1 入队。该请求被推入 load 队列（opcode=ldr，pc=40103c，lq_idx=145，sq_idx=-1，dyn_inst_seq=2095）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4（mem_req）以 parent_event_id=3 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 4 步** — event_id=4（parent=3），tick=2996840：L2 请求创建，request_id=2095，va=`400080`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=5（lsq_sendfrag）以 parent_event_id=4 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 5 步** — event_id=5（parent=4），tick=2996840：L2 请求分片，request_id=2095，va=`400080`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=6（tlb_translate）以 parent_event_id=5 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 6 步** — event_id=6（parent=5），tick=2996840：L2 地址翻译，request_id=2095，va=`400080`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=7（lq_read）以 parent_event_id=6 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 7 步** — event_id=7（parent=6），tick=2996840：L3 load 读取队列项，request_id=2095，va=`400080`，lq_idx=145。被污染的 load 请求在此实际被消费，链到达 L3。 下一步：event_id=8（resp）以 parent_event_id=7 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 8 步** — event_id=8（parent=7），tick=3044967：L3 数据响应返回，request_id=2095，va=`80`，pa=`—`；响应数据进入 LSQ/寄存器路径。 下一步：event_id=9（lq_complete）以 parent_event_id=8 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 9 步** — event_id=9（parent=8），tick=3044967：L3 load 完成，request_id=2095，va=`400080`，pa=`80`；load 数据已可被后续指令读取。 下一步：event_id=10（taint_reg）以 parent_event_id=9 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 10 步** — event_id=10（parent=9），tick=3044967：L4 污点进入体系结构寄存器，request_id=2095，va=`80`，corr=seq_primary；污染值离开 LSQ 进入寄存器数据通路。 下一步：event_id=11（squash_discarded）以 parent_event_id=10 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 11 步** — event_id=11（parent=10），tick=3046890：L4 检测并包含。state_before=`load_queue_uncommitted`，contained=1，containment_reason=squash_discarded，request_id=2095；该 load 在提交前被 squash 并从队列丢弃，错误值没有写入体系结构状态。 下一步：event_id=12（chain_end）以 parent_event_id=11 承接本事件，共享 fault_id=1 与 dyn_inst_seq=2095，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 12 步** — event_id=12（parent=11），tick=19190325：生命周期标记 corr=none，outcome=run_end。它只表示仿真结束，**不是** L5 证据，也从不参与终局判定。 本事件是该 fault 在本 seed 事件流中的最后一条。

## 5. 关键事件表

| 顺序 | event_id | parent_event_id | tick | kind | layer | request_id | corr | 地址/值变化 | 状态变化 | 传播作用 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | — | 2996840 | inj | L0 | — | origin | 4000c0→400080 | — | L0 故障注入 |
| 2 | 2 | 1 | 2996840 | addr_form | L1 | — | origin | 4000c0→400080 | — | L1 地址形成 |
| 3 | 3 | 2 | 2996840 | lsq_push | L1 | — | seq_primary | va=400080 | — | L1 入队（LQ/SQ） |
| 4 | 4 | 3 | 2996840 | mem_req | L2 | 2095 | seq_primary | va=400080 | — | L2 请求创建 |
| 5 | 5 | 4 | 2996840 | lsq_sendfrag | L2 | 2095 | seq_primary | va=400080 | — | L2 请求分片 |
| 6 | 6 | 5 | 2996840 | tlb_translate | L2 | 2095 | seq_primary | va=400080 | — | L2 地址翻译 |
| 7 | 7 | 6 | 2996840 | lq_read | L3 | 2095 | seq_primary | va=400080 | — | L3 load 读取队列 |
| 8 | 8 | 7 | 3044967 | resp | L3 | 2095 | seq_primary | va=80 | — | L3 数据响应 |
| 9 | 9 | 8 | 3044967 | lq_complete | L3 | 2095 | seq_primary | va=400080, pa=80 | — | L3 load 完成 |
| 10 | 10 | 9 | 3044967 | taint_reg | L4 | 2095 | seq_primary | clean→tainted | — | L4 污点进入寄存器 |
| 11 | 11 | 10 | 3046890 | squash_discarded | L4 | 2095 | seq_primary | — | load_queue_uncommitted→— | L4 检测并 squash 丢弃 |
| 12 | 12 | 11 | 19190325 | chain_end | — | — | none | — | contained=0 | 生命周期结束标记（非 L5 证据） |

## 6. 原始证据与哈希

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/S07-F0-W5/seed1/prop_evt.txt.gz` | `d5e61f32f8cf910f55d3b550088c33dc7c56d63eeb737555a5415492466526a9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/S07-F0-W5/chain_report.json` | `285adb1b33e778fa85e42fdd4180d901d56541f8d0df2a3a970174c557985d2c` |
| cell_results | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/S07-F0-W5/cell_results.json` | `7534c980923111e71afb3279e2cc4067cdf8253e73472a2ea6b3f459a357d247` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/S07-F0-W5/seed1/stats.txt` | `5ffe8314912a637ca4c833617edcec2c8b0c0deb51b46e5385ea35e5937e6d8e` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/S07-F0-W5/seed1/run.out` | `055e760db91b2ef4ef32de1d228d3bb2a2735ec978aaa9280bd2a4841664999e` |
| injections.log | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/S07-F0-W5/seed1/addrpath_injections.log` | `c83274260510c629e46ade49ac33a75bc56da08d7aecd1ba2c2773f80e1f728f` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1/manifest.json` | `806e86ed1c35fc573923ca3db06ddecea4d505f6511f91bb802dde5b4b3e05ce` |

事件流字节数：1079（gzip 后）；解压后事件行数：12；本 fault 事件数：12。

## 7. 可复现命令

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/S07-F0-W5_s1 --cells S07-F0-W5 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --timeout 300
```

环境身份：binary SHA-256 `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046`，binary_source_head `2498573fddaf67bdbca7b1461443ae9e926e650b`，analysis_tool_head `a92f9f6d807dad397047740e163456b0bcc89ed5`，matrix SHA-256 `8f2d6227ca76202fa9b5cb2e5ee5489d83a68643b2b987be7e04ac1d8d515fce`。

## 8. 诚实边界

- 本 doc 只证明该 seed 自己的事件流：已证明的层边为 L0->L1, L1->L2, L2->L3, L3->L4, L4->L5；缺失的层边为 （无）。
- 终局 `detected_contained` 与 `provable_to=L5` 直接取自该 seed 的 `chain_report.json`，未做任何推断升级。
- 三方计数：注入日志 `FUNNEL`/`CHAOS_L0_FUNNEL` 与 `run.out` 的 `CHAOS_LSU_TRIGGER` 全部来自本 seed；`stats.txt` 不含 `numFaultsInjected` 统计（addrpath 家族不发射该计数器），故该路为 **n/a**，不以 0 冒充。
- `chain_end` 只是生命周期标记（corr=none），从不作为 L5 证据；本 doc 未把 `chain_end` 当作终局。
- 后续层为 N/A 的含义：本 seed 未在当前事件流中产生该层的真实事件，文档不会补造，也不会据此推断 Masked。
- 本 seed 未重跑；原始事件流未被修改；三个 seed 的数值各自独立，不存在跨 seed 复制。
