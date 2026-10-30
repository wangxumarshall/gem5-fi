# S08-F0-W5 seed1 — 完整传播路径（真实事件时间顺序）

> 本文只转录该 seed 自己的原始事件流（`prop_evt.txt.gz`）与权威 `chain_report.json`；未修改事件流，未跨 seed 复用任何数值，未把推测写成事件事实。

## 1. 样本身份

| 项 | 值 |
|---|---|
| RunID | `S08-F0-W5` |
| seed | `1` |
| model | `S08`（Store Queue 换值） |
| frequency | `F0` |
| workload | `W5`（W5:sq_forward） |
| binary_path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `686458c34ab7199a07ec4a968c3bbfe40e0d7514cccc2ee0d181a68621b7cef9` |
| binary_source_head | `5b550954+dirty:d55db8d6b7bb78fb35addf191a45b3d6bb7b19b9006770aa4c1c9beb7ac2b876` |
| analysis_tool_head | `5b550954207d6ce1e4deb56a6f221357e8a8314f` |
| prop_evt_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/S08-F0-W5/seed1/prop_evt.txt.gz` |
| prop_evt_sha256 | `113f0ee7966d8e40a1980969d16f1abc3574a7a381927a7d6f7347d572fcf54d` |
| chain_report_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/S08-F0-W5/chain_report.json` |
| chain_report_sha256 | `81ae68a4fae36032b075181c0f46d6b53dc24dfb3bed16baece5b12a11829e9b` |
| cell_results_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/S08-F0-W5/cell_results.json` |
| cell_results_sha256 | `95cb82b33f210c8e337477c603677e5600cfe43e060df55edb957aaea3cb3c70` |

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
| 事件总数 | `55` |
| containment_event_id | `45` |

## 3. 真实注入

| 项 | 值 |
|---|---|
| 注入 tick | `14949935` |
| event_id | `0` |
| parent_event_id | `—` |
| 注入部件 | `CHAOSAddrPath` |
| 注入字段 | `fwd_source_sub` |
| 原值 | `` |
| 新值 | `` |
| mask | `—` |
| 地址 | `` |
| request_id | `12091` |
| corr | `origin` |
| injected/activated 计数 | `—`；`CHAOS_L0_FUNNEL: CHAOSLSQFwd attempted=1 eligible=1 injected=1 activated=1` |

注入日志原文（本 seed 自己的 `lsq_fwd_injections.log`）：

```text
Cycle: 38831, Site: store->load_forward_decision, FaultType: fwd_source_sub, Vaddr: 0x7ffffefc30, TrueSrcSize: 8, AltSrcSize: 8, Copied: 8, faults_injected: 1
```

运行期触发/检测原文（本 seed 自己的 `seed1/run.out`）：

```text
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=1 eligible=1 injected=1 first_eligible_tick=14949935 last_eligible_tick=14949935 fires=n/a no_effect=n/a (activated=W3-L0-layer)
CHAOS_DETECT: layer=None contained=0 tick=14951090 ptag=1 reason=errant_commit
```

## 4. 传播过程（真实事件时间顺序）

本 seed 的 fault_id=1 链共有 55 条真实事件，事件种类序列为：`inj → sq_entry → lsq_fwd → resp → taint_reg → sq_writeback → errant_commit → sq_complete → consumer → lsq_push → request_fork → mem_req → lsq_sendfrag → tlb_translate → lsq_push → request_fork → mem_req → lsq_sendfrag → tlb_translate → lsq_push → request_fork → mem_req → lsq_sendfrag → tlb_translate → lsq_push → request_fork → mem_req → lsq_sendfrag → tlb_translate → lsq_push → request_fork → mem_req → lsq_sendfrag → tlb_translate → lsq_push → request_fork → mem_req → lsq_sendfrag → tlb_translate → lsq_push → request_fork → mem_req → lsq_sendfrag → tlb_translate → lsq_push → request_fork → mem_req → lsq_sendfrag → tlb_translate → lsq_push → request_fork → mem_req → lsq_sendfrag → tlb_translate → chain_end`。以下按该 seed 事件流的原始顺序逐步说明。

**第 1 步** — event_id=0，tick=14949935：L0 故障注入。CHAOSAddrPath 在 lsq_pushRequest_PRE 站点以 — 模式写入一个故障；注入字段 field=fwd_source_sub，地址 `` → ``，dyn_inst_seq=12091，corr=origin。该事件无父事件，是整条传播链的根。 下一步：event_id=1（sq_entry）以 parent_event_id=0 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12091，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 2 步** — event_id=1（parent=0），tick=14949935：sq_entry，va=`7ffffefc30`，request_id=12091，corr=seq_primary。 下一步：event_id=2（lsq_fwd）以 parent_event_id=1 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12091，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 3 步** — event_id=2（parent=1），tick=14949935：lsq_fwd，va=`7ffffefc30`，request_id=12091，corr=seq_primary。 下一步：event_id=3（resp）以 parent_event_id=2 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12091，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 4 步** — event_id=3（parent=2），tick=14949935：L3 数据响应返回，request_id=12091，va=`7ffffefc30`，pa=`—`；响应数据进入 LSQ/寄存器路径。 下一步：event_id=4（taint_reg）以 parent_event_id=3 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12091，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 5 步** — event_id=4（parent=3），tick=14949935：L4 污点进入体系结构寄存器，request_id=12091，va=`7ffffefc30`，corr=seq_primary；污染值离开 LSQ 进入寄存器数据通路。 下一步：event_id=5（sq_writeback）以 parent_event_id=4 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12091，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 6 步** — event_id=5（parent=4），tick=14950705：L3 sq_writeback，request_id=—，va=`—`，pa=`7dc28`；store 侧继续携带被污染的值。 下一步：event_id=6（errant_commit）以 parent_event_id=5 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12083，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 7 步** — event_id=6（parent=5），tick=14951090：L5 错误提交。detection_layer=L5，outcome=errant_commit，corr=taint_prop；带污染值的指令真实退休，这是逃逸终局（不是 chain_end 推断）。 下一步：event_id=7（sq_complete）以 parent_event_id=6 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12091，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 8 步** — event_id=7（parent=6），tick=14951475：L3 sq_complete，request_id=—，va=`7ffffefc30`，pa=`—`；store 侧继续携带被污染的值。 下一步：event_id=8（consumer）以 parent_event_id=7 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12083，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 9 步** — event_id=8（parent=4），tick=15175930：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=9（lsq_push）以 parent_event_id=8 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12133，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 10 步** — event_id=9（parent=8），tick=16251620：L1 入队。该请求被推入 store 队列（opcode=strb，pc=400834，lq_idx=-1，sq_idx=1072，dyn_inst_seq=13930）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4294967296（request_fork）以 parent_event_id=9 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13930，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 11 步** — event_id=4294967296（parent=4），tick=16251620：request_fork，va=`—`，request_id=12091，corr=addr_fallback。 下一步：event_id=10（mem_req）以 parent_event_id=4294967296 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 12 步** — event_id=10（parent=4294967296），tick=16251620：L2 请求创建，request_id=13930，va=`7ffffefc37`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=11（lsq_sendfrag）以 parent_event_id=10 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13930，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 13 步** — event_id=11（parent=10），tick=16251620：L2 请求分片，request_id=13930，va=`7ffffefc37`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=12（tlb_translate）以 parent_event_id=11 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13930，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 14 步** — event_id=12（parent=11），tick=16251620：L2 地址翻译，request_id=13930，va=`7ffffefc37`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=13（lsq_push）以 parent_event_id=12 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13930，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 15 步** — event_id=13（parent=9），tick=16258165：L1 入队。该请求被推入 store 队列（opcode=strb，pc=400834，lq_idx=-1，sq_idx=1073，dyn_inst_seq=13960）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4294967297（request_fork）以 parent_event_id=13 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13960，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 16 步** — event_id=4294967297（parent=4），tick=16258165：request_fork，va=`—`，request_id=12091，corr=addr_fallback。 下一步：event_id=14（mem_req）以 parent_event_id=4294967297 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 17 步** — event_id=14（parent=4294967297），tick=16258165：L2 请求创建，request_id=13960，va=`7ffffefc36`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=15（lsq_sendfrag）以 parent_event_id=14 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13960，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 18 步** — event_id=15（parent=14），tick=16258165：L2 请求分片，request_id=13960，va=`7ffffefc36`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=16（tlb_translate）以 parent_event_id=15 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13960，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 19 步** — event_id=16（parent=15），tick=16258165：L2 地址翻译，request_id=13960，va=`7ffffefc36`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=17（lsq_push）以 parent_event_id=16 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13960，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 20 步** — event_id=17（parent=13），tick=16264710：L1 入队。该请求被推入 store 队列（opcode=strb，pc=400834，lq_idx=-1，sq_idx=1074，dyn_inst_seq=13990）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4294967298（request_fork）以 parent_event_id=17 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13990，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 21 步** — event_id=4294967298（parent=4），tick=16264710：request_fork，va=`—`，request_id=12091，corr=addr_fallback。 下一步：event_id=18（mem_req）以 parent_event_id=4294967298 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 22 步** — event_id=18（parent=4294967298），tick=16264710：L2 请求创建，request_id=13990，va=`7ffffefc35`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=19（lsq_sendfrag）以 parent_event_id=18 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13990，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 23 步** — event_id=19（parent=18），tick=16264710：L2 请求分片，request_id=13990，va=`7ffffefc35`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=20（tlb_translate）以 parent_event_id=19 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13990，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 24 步** — event_id=20（parent=19），tick=16264710：L2 地址翻译，request_id=13990，va=`7ffffefc35`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=21（lsq_push）以 parent_event_id=20 承接本事件，共享 fault_id=1 与 dyn_inst_seq=13990，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 25 步** — event_id=21（parent=17），tick=16271255：L1 入队。该请求被推入 store 队列（opcode=strb，pc=400834，lq_idx=-1，sq_idx=1075，dyn_inst_seq=14020）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4294967299（request_fork）以 parent_event_id=21 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14020，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 26 步** — event_id=4294967299（parent=4），tick=16271255：request_fork，va=`—`，request_id=12091，corr=addr_fallback。 下一步：event_id=22（mem_req）以 parent_event_id=4294967299 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 27 步** — event_id=22（parent=4294967299），tick=16271255：L2 请求创建，request_id=14020，va=`7ffffefc34`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=23（lsq_sendfrag）以 parent_event_id=22 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14020，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 28 步** — event_id=23（parent=22），tick=16271255：L2 请求分片，request_id=14020，va=`7ffffefc34`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=24（tlb_translate）以 parent_event_id=23 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14020，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 29 步** — event_id=24（parent=23），tick=16271255：L2 地址翻译，request_id=14020，va=`7ffffefc34`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=25（lsq_push）以 parent_event_id=24 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14020，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 30 步** — event_id=25（parent=21），tick=16277800：L1 入队。该请求被推入 store 队列（opcode=strb，pc=400834，lq_idx=-1，sq_idx=1076，dyn_inst_seq=14050）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4294967300（request_fork）以 parent_event_id=25 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14050，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 31 步** — event_id=4294967300（parent=4），tick=16277800：request_fork，va=`—`，request_id=12091，corr=addr_fallback。 下一步：event_id=26（mem_req）以 parent_event_id=4294967300 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 32 步** — event_id=26（parent=4294967300），tick=16277800：L2 请求创建，request_id=14050，va=`7ffffefc33`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=27（lsq_sendfrag）以 parent_event_id=26 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14050，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 33 步** — event_id=27（parent=26），tick=16277800：L2 请求分片，request_id=14050，va=`7ffffefc33`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=28（tlb_translate）以 parent_event_id=27 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14050，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 34 步** — event_id=28（parent=27），tick=16277800：L2 地址翻译，request_id=14050，va=`7ffffefc33`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=29（lsq_push）以 parent_event_id=28 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14050，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 35 步** — event_id=29（parent=25），tick=16284345：L1 入队。该请求被推入 store 队列（opcode=strb，pc=400834，lq_idx=-1，sq_idx=1077，dyn_inst_seq=14080）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4294967301（request_fork）以 parent_event_id=29 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14080，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 36 步** — event_id=4294967301（parent=4），tick=16284345：request_fork，va=`—`，request_id=12091，corr=addr_fallback。 下一步：event_id=30（mem_req）以 parent_event_id=4294967301 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 37 步** — event_id=30（parent=4294967301），tick=16284345：L2 请求创建，request_id=14080，va=`7ffffefc32`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=31（lsq_sendfrag）以 parent_event_id=30 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14080，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 38 步** — event_id=31（parent=30），tick=16284345：L2 请求分片，request_id=14080，va=`7ffffefc32`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=32（tlb_translate）以 parent_event_id=31 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14080，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 39 步** — event_id=32（parent=31），tick=16284345：L2 地址翻译，request_id=14080，va=`7ffffefc32`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=33（lsq_push）以 parent_event_id=32 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14080，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 40 步** — event_id=33（parent=29），tick=16290890：L1 入队。该请求被推入 store 队列（opcode=strb，pc=400834，lq_idx=-1，sq_idx=1078，dyn_inst_seq=14110）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4294967302（request_fork）以 parent_event_id=33 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14110，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 41 步** — event_id=4294967302（parent=4），tick=16290890：request_fork，va=`—`，request_id=12091，corr=addr_fallback。 下一步：event_id=34（mem_req）以 parent_event_id=4294967302 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 42 步** — event_id=34（parent=4294967302），tick=16290890：L2 请求创建，request_id=14110，va=`7ffffefc31`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=35（lsq_sendfrag）以 parent_event_id=34 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14110，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 43 步** — event_id=35（parent=34），tick=16290890：L2 请求分片，request_id=14110，va=`7ffffefc31`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=36（tlb_translate）以 parent_event_id=35 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14110，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 44 步** — event_id=36（parent=35），tick=16290890：L2 地址翻译，request_id=14110，va=`7ffffefc31`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=37（lsq_push）以 parent_event_id=36 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14110，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 45 步** — event_id=37（parent=33），tick=16293200：L1 入队。该请求被推入 store 队列（opcode=strb，pc=400834，lq_idx=-1，sq_idx=1079，dyn_inst_seq=14123）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4294967303（request_fork）以 parent_event_id=37 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14123，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 46 步** — event_id=4294967303（parent=4），tick=16293200：request_fork，va=`—`，request_id=12091，corr=addr_fallback。 下一步：event_id=38（mem_req）以 parent_event_id=4294967303 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 47 步** — event_id=38（parent=4294967303），tick=16293200：L2 请求创建，request_id=14123，va=`7ffffefc30`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=39（lsq_sendfrag）以 parent_event_id=38 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14123，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 48 步** — event_id=39（parent=38），tick=16293200：L2 请求分片，request_id=14123，va=`7ffffefc30`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=40（tlb_translate）以 parent_event_id=39 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14123，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 49 步** — event_id=40（parent=39），tick=16293200：L2 地址翻译，request_id=14123，va=`7ffffefc30`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=41（lsq_push）以 parent_event_id=40 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14123，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 50 步** — event_id=41（parent=37），tick=16367120：L1 入队。该请求被推入 store 队列（opcode=strxi_uop，pc=401850，lq_idx=-1，sq_idx=1088，dyn_inst_seq=14281）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4294967304（request_fork）以 parent_event_id=41 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14281，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 51 步** — event_id=4294967304（parent=4），tick=16367120：request_fork，va=`—`，request_id=12091，corr=addr_fallback。 下一步：event_id=42（mem_req）以 parent_event_id=4294967304 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 52 步** — event_id=42（parent=4294967304），tick=16367120：L2 请求创建，request_id=14281，va=`7ffffefc30`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=43（lsq_sendfrag）以 parent_event_id=42 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14281，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 53 步** — event_id=43（parent=42），tick=16367120：L2 请求分片，request_id=14281，va=`7ffffefc30`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=44（tlb_translate）以 parent_event_id=43 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14281，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 54 步** — event_id=44（parent=43），tick=16367120：L2 地址翻译，request_id=14281，va=`7ffffefc30`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=45（chain_end）以 parent_event_id=44 承接本事件，共享 fault_id=1 与 dyn_inst_seq=14281，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 55 步** — event_id=45（parent=41），tick=19190325：生命周期标记 corr=none，outcome=run_end。它只表示仿真结束，**不是** L5 证据，也从不参与终局判定。 本事件是该 fault 在本 seed 事件流中的最后一条。

## 5. 关键事件表

| 顺序 | event_id | parent_event_id | tick | kind | layer | request_id | corr | 地址/值变化 | 状态变化 | 传播作用 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 14949935 | inj | L0 | 12091 | origin | va=7ffffefc30 | — | L0 故障注入 |
| 2 | 1 | 0 | 14949935 | sq_entry | L1 | 12091 | seq_primary | va=7ffffefc30 | — | L1 生产 store 的 SQ 表项（转发源） |
| 3 | 2 | 1 | 14949935 | lsq_fwd | L2 | 12091 | seq_primary | store_data→fwd_corrupt:fwd_source_sub | — | L2 store→load 转发决策/传输 |
| 4 | 3 | 2 | 14949935 | resp | L3 | 12091 | seq_primary | va=7ffffefc30 | — | L3 数据响应 |
| 5 | 4 | 3 | 14949935 | taint_reg | L4 | 12091 | seq_primary | clean→tainted | — | L4 污点进入寄存器 |
| 6 | 5 | 4 | 14950705 | sq_writeback | L3 | — | seq_primary | — | —→packet_built | L3 store 回写 |
| 7 | 6 | 5 | 14951090 | errant_commit | L5 | — | taint_prop | — | contained=0 | L5 错误提交（逃逸） |
| 8 | 7 | 6 | 14951475 | sq_complete | L3 | — | seq_primary | va=7ffffefc30 | —→completed | L3 store 完成 |
| 9 | 8 | 4 | 15175930 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 10 | 9 | 8 | 16251620 | lsq_push | L1 | — | addr_fallback | va=7ffffefc37 | — | L1 入队（LQ/SQ） |
| 11 | 4294967296 | 4 | 16251620 | request_fork | — | 12091 | addr_fallback | — | — | — |
| 12 | 10 | 4294967296 | 16251620 | mem_req | L2 | 13930 | addr_fallback | va=7ffffefc37 | — | L2 请求创建 |
| 13 | 11 | 10 | 16251620 | lsq_sendfrag | L2 | 13930 | addr_fallback | va=7ffffefc37 | — | L2 请求分片 |
| 14 | 12 | 11 | 16251620 | tlb_translate | L2 | 13930 | addr_fallback | va=7ffffefc37 | — | L2 地址翻译 |
| 15 | 13 | 9 | 16258165 | lsq_push | L1 | — | addr_fallback | va=7ffffefc36 | — | L1 入队（LQ/SQ） |
| 16 | 4294967297 | 4 | 16258165 | request_fork | — | 12091 | addr_fallback | — | — | — |
| 17 | 14 | 4294967297 | 16258165 | mem_req | L2 | 13960 | addr_fallback | va=7ffffefc36 | — | L2 请求创建 |
| 18 | 15 | 14 | 16258165 | lsq_sendfrag | L2 | 13960 | addr_fallback | va=7ffffefc36 | — | L2 请求分片 |
| 19 | 16 | 15 | 16258165 | tlb_translate | L2 | 13960 | addr_fallback | va=7ffffefc36 | — | L2 地址翻译 |
| 20 | 17 | 13 | 16264710 | lsq_push | L1 | — | addr_fallback | va=7ffffefc35 | — | L1 入队（LQ/SQ） |
| 21 | 4294967298 | 4 | 16264710 | request_fork | — | 12091 | addr_fallback | — | — | — |
| 22 | 18 | 4294967298 | 16264710 | mem_req | L2 | 13990 | addr_fallback | va=7ffffefc35 | — | L2 请求创建 |
| 23 | 19 | 18 | 16264710 | lsq_sendfrag | L2 | 13990 | addr_fallback | va=7ffffefc35 | — | L2 请求分片 |
| 24 | 20 | 19 | 16264710 | tlb_translate | L2 | 13990 | addr_fallback | va=7ffffefc35 | — | L2 地址翻译 |
| 25 | 21 | 17 | 16271255 | lsq_push | L1 | — | addr_fallback | va=7ffffefc34 | — | L1 入队（LQ/SQ） |
| 26 | 4294967299 | 4 | 16271255 | request_fork | — | 12091 | addr_fallback | — | — | — |
| 27 | 22 | 4294967299 | 16271255 | mem_req | L2 | 14020 | addr_fallback | va=7ffffefc34 | — | L2 请求创建 |
| 28 | 23 | 22 | 16271255 | lsq_sendfrag | L2 | 14020 | addr_fallback | va=7ffffefc34 | — | L2 请求分片 |
| 29 | 24 | 23 | 16271255 | tlb_translate | L2 | 14020 | addr_fallback | va=7ffffefc34 | — | L2 地址翻译 |
| 30 | 25 | 21 | 16277800 | lsq_push | L1 | — | addr_fallback | va=7ffffefc33 | — | L1 入队（LQ/SQ） |
| 31 | 4294967300 | 4 | 16277800 | request_fork | — | 12091 | addr_fallback | — | — | — |
| 32 | 26 | 4294967300 | 16277800 | mem_req | L2 | 14050 | addr_fallback | va=7ffffefc33 | — | L2 请求创建 |
| 33 | 27 | 26 | 16277800 | lsq_sendfrag | L2 | 14050 | addr_fallback | va=7ffffefc33 | — | L2 请求分片 |
| 34 | 28 | 27 | 16277800 | tlb_translate | L2 | 14050 | addr_fallback | va=7ffffefc33 | — | L2 地址翻译 |
| 35 | 29 | 25 | 16284345 | lsq_push | L1 | — | addr_fallback | va=7ffffefc32 | — | L1 入队（LQ/SQ） |
| 36 | 4294967301 | 4 | 16284345 | request_fork | — | 12091 | addr_fallback | — | — | — |
| 37 | 30 | 4294967301 | 16284345 | mem_req | L2 | 14080 | addr_fallback | va=7ffffefc32 | — | L2 请求创建 |
| 38 | 31 | 30 | 16284345 | lsq_sendfrag | L2 | 14080 | addr_fallback | va=7ffffefc32 | — | L2 请求分片 |
| 39 | 32 | 31 | 16284345 | tlb_translate | L2 | 14080 | addr_fallback | va=7ffffefc32 | — | L2 地址翻译 |
| 40 | 33 | 29 | 16290890 | lsq_push | L1 | — | addr_fallback | va=7ffffefc31 | — | L1 入队（LQ/SQ） |
| 41 | 4294967302 | 4 | 16290890 | request_fork | — | 12091 | addr_fallback | — | — | — |
| 42 | 34 | 4294967302 | 16290890 | mem_req | L2 | 14110 | addr_fallback | va=7ffffefc31 | — | L2 请求创建 |
| 43 | 35 | 34 | 16290890 | lsq_sendfrag | L2 | 14110 | addr_fallback | va=7ffffefc31 | — | L2 请求分片 |
| 44 | 36 | 35 | 16290890 | tlb_translate | L2 | 14110 | addr_fallback | va=7ffffefc31 | — | L2 地址翻译 |
| 45 | 37 | 33 | 16293200 | lsq_push | L1 | — | addr_fallback | va=7ffffefc30 | — | L1 入队（LQ/SQ） |
| 46 | 4294967303 | 4 | 16293200 | request_fork | — | 12091 | addr_fallback | — | — | — |
| 47 | 38 | 4294967303 | 16293200 | mem_req | L2 | 14123 | addr_fallback | va=7ffffefc30 | — | L2 请求创建 |
| 48 | 39 | 38 | 16293200 | lsq_sendfrag | L2 | 14123 | addr_fallback | va=7ffffefc30 | — | L2 请求分片 |
| 49 | 40 | 39 | 16293200 | tlb_translate | L2 | 14123 | addr_fallback | va=7ffffefc30 | — | L2 地址翻译 |
| 50 | 41 | 37 | 16367120 | lsq_push | L1 | — | addr_fallback | va=7ffffefc30 | — | L1 入队（LQ/SQ） |
| 51 | 4294967304 | 4 | 16367120 | request_fork | — | 12091 | addr_fallback | — | — | — |
| 52 | 42 | 4294967304 | 16367120 | mem_req | L2 | 14281 | addr_fallback | va=7ffffefc30 | — | L2 请求创建 |
| 53 | 43 | 42 | 16367120 | lsq_sendfrag | L2 | 14281 | addr_fallback | va=7ffffefc30 | — | L2 请求分片 |
| 54 | 44 | 43 | 16367120 | tlb_translate | L2 | 14281 | addr_fallback | va=7ffffefc30 | — | L2 地址翻译 |
| 55 | 45 | 41 | 19190325 | chain_end | L5 | — | none | — | contained=1 | 生命周期结束标记（非 L5 证据） |

## 6. 原始证据与哈希

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/S08-F0-W5/seed1/prop_evt.txt.gz` | `113f0ee7966d8e40a1980969d16f1abc3574a7a381927a7d6f7347d572fcf54d` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/S08-F0-W5/chain_report.json` | `81ae68a4fae36032b075181c0f46d6b53dc24dfb3bed16baece5b12a11829e9b` |
| cell_results | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/S08-F0-W5/cell_results.json` | `95cb82b33f210c8e337477c603677e5600cfe43e060df55edb957aaea3cb3c70` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/S08-F0-W5/seed1/stats.txt` | `b6553b7ecf88a48ae7c800142abf67470cdb1dd3c6451d842ce24d1d5286633f` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/S08-F0-W5/seed1/run.out` | `61dc42d35bb6b0e0d66aeb4168206633b375fc03a332f7d26d6a292a1aed925a` |
| injections.log | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/S08-F0-W5/seed1/lsq_fwd_injections.log` | `0691ff1610193a87c4a5e0a943b67ab38dbf3f639e245f72cee7deb330427b10` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1/manifest.json` | `61721cd2ca2032ad8bfe6d07e334f1a3e23dbb7469aea0d3885c7b93f8be632b` |

事件流字节数：2738（gzip 后）；解压后事件行数：55；本 fault 事件数：55。

## 7. 可复现命令

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S08-F0-W5_s1 --cells S08-F0-W5 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --timeout 300
```

环境身份：binary SHA-256 `686458c34ab7199a07ec4a968c3bbfe40e0d7514cccc2ee0d181a68621b7cef9`，binary_source_head `5b550954+dirty:d55db8d6b7bb78fb35addf191a45b3d6bb7b19b9006770aa4c1c9beb7ac2b876`，analysis_tool_head `5b550954207d6ce1e4deb56a6f221357e8a8314f`，matrix SHA-256 `8f2d6227ca76202fa9b5cb2e5ee5489d83a68643b2b987be7e04ac1d8d515fce`。

## 8. 诚实边界

- 本 doc 只证明该 seed 自己的事件流：已证明的层边为 L0->L1, L1->L2, L2->L3, L3->L4, L4->L5；缺失的层边为 （无）。
- 终局 `full` 与 `provable_to=L5` 直接取自该 seed 的 `chain_report.json`，未做任何推断升级。
- 三方计数：注入日志 `FUNNEL`/`CHAOS_L0_FUNNEL` 与 `run.out` 的 `CHAOS_LSU_TRIGGER` 全部来自本 seed；`stats.txt` 不含 `numFaultsInjected` 统计（addrpath 家族不发射该计数器），故该路为 **n/a**，不以 0 冒充。
- `chain_end` 只是生命周期标记（corr=none），从不作为 L5 证据；本 doc 未把 `chain_end` 当作终局。
- 后续层为 N/A 的含义：本 seed 未在当前事件流中产生该层的真实事件，文档不会补造，也不会据此推断 Masked。
- 本 seed 未重跑；原始事件流未被修改；三个 seed 的数值各自独立，不存在跨 seed 复制。
