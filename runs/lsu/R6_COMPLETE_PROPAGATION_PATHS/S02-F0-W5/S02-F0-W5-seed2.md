# S02-F0-W5 seed2 — 完整传播路径（真实事件时间顺序）

> 本文只转录该 seed 自己的原始事件流（`prop_evt.txt.gz`）与权威 `chain_report.json`；未修改事件流，未跨 seed 复用任何数值，未把推测写成事件事实。

## 1. 样本身份

| 项 | 值 |
|---|---|
| RunID | `S02-F0-W5` |
| seed | `2` |
| model | `S02`（Store Queue 双比特翻转） |
| frequency | `F0` |
| workload | `W5`（W5:sq_forward） |
| binary_path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `686458c34ab7199a07ec4a968c3bbfe40e0d7514cccc2ee0d181a68621b7cef9` |
| binary_source_head | `5b550954+dirty:d55db8d6b7bb78fb35addf191a45b3d6bb7b19b9006770aa4c1c9beb7ac2b876` |
| analysis_tool_head | `5b550954207d6ce1e4deb56a6f221357e8a8314f` |
| prop_evt_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/S02-F0-W5/seed2/prop_evt.txt.gz` |
| prop_evt_sha256 | `74adbae3d65ecd25850f234c17684758b45e4376eb46b74b4fc2606a7aab691a` |
| chain_report_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/S02-F0-W5/chain_report.json` |
| chain_report_sha256 | `1a490645774079f9c1c2634d5fb0822fb03912299bb37acf3f506b6ca60f3408` |
| cell_results_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/S02-F0-W5/cell_results.json` |
| cell_results_sha256 | `0484910129b31cce930404001972e777300be967c58ed0f602e5d07ee6e8c5ac` |

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
| conservation | `ok` |
| count_contradiction | `False` |
| truncated | `False` |
| 事件总数 | `652` |
| containment_event_id | `651` |

## 3. 真实注入

| 项 | 值 |
|---|---|
| 注入 tick | `12868240` |
| event_id | `0` |
| parent_event_id | `—` |
| 注入部件 | `CHAOSAddrPath` |
| 注入字段 | `lsqfwd_forward` |
| 原值 | `` |
| 新值 | `` |
| mask | `—` |
| 地址 | `` |
| request_id | `11143` |
| corr | `origin` |
| injected/activated 计数 | `—`；`CHAOS_L0_FUNNEL: CHAOSLSQFwd attempted=6 eligible=6 injected=1 activated=1` |

注入日志原文（本 seed 自己的 `lsq_fwd_injections.log`）：

```text
（无 Tick 注入行）
```

运行期触发/检测原文（本 seed 自己的 `seed2/run.out`）：

```text
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=6 eligible=6 injected=1 first_eligible_tick=556325 last_eligible_tick=33794915 fires=n/a no_effect=n/a (activated=W3-L0-layer)
CHAOS_DETECT: layer=None contained=0 tick=12869395 ptag=1 reason=errant_commit
```

## 4. 传播过程（真实事件时间顺序）

本 seed 的 fault_id=1 链共有 652 条真实事件，事件种类序列为：`inj → sq_entry → lsq_fwd → resp → taint_reg → sq_writeback → errant_commit → resp → taint_reg → sq_complete → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。以下按该 seed 事件流的原始顺序逐步说明。

**第 1 步** — event_id=0，tick=12868240：L0 故障注入。CHAOSAddrPath 在 lsq_pushRequest_PRE 站点以 — 模式写入一个故障；注入字段 field=lsqfwd_forward，地址 `` → ``，dyn_inst_seq=11143，corr=origin。该事件无父事件，是整条传播链的根。 下一步：event_id=1（sq_entry）以 parent_event_id=0 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11143，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 2 步** — event_id=1（parent=0），tick=12868240：sq_entry，va=`48fb70`，request_id=11143，corr=seq_primary。 下一步：event_id=2（lsq_fwd）以 parent_event_id=1 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11143，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 3 步** — event_id=2（parent=1），tick=12868240：lsq_fwd，va=`48fb70`，request_id=11143，corr=seq_primary。 下一步：event_id=3（resp）以 parent_event_id=2 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11143，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 4 步** — event_id=3（parent=2），tick=12868240：L3 数据响应返回，request_id=11143，va=`48fb70`，pa=`—`；响应数据进入 LSQ/寄存器路径。 下一步：event_id=4（taint_reg）以 parent_event_id=3 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11143，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 5 步** — event_id=4（parent=3），tick=12868240：L4 污点进入体系结构寄存器，request_id=11143，va=`48fb70`，corr=seq_primary；污染值离开 LSQ 进入寄存器数据通路。 下一步：event_id=5（sq_writeback）以 parent_event_id=4 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11143，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 6 步** — event_id=5（parent=4），tick=12869010：L3 sq_writeback，request_id=—，va=`—`，pa=`75b70`；store 侧继续携带被污染的值。 下一步：event_id=6（errant_commit）以 parent_event_id=5 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11141，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 7 步** — event_id=6（parent=5），tick=12869395：L5 错误提交。detection_layer=L5，outcome=errant_commit，corr=taint_prop；带污染值的指令真实退休，这是逃逸终局（不是 chain_end 推断）。 下一步：event_id=7（resp）以 parent_event_id=6 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11143，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 8 步** — event_id=7（parent=（根事件，无父）），tick=12869780：L3 数据响应返回，request_id=11141，va=`75b70`，pa=`—`；响应数据进入 LSQ/寄存器路径。 下一步：event_id=8（taint_reg）以 parent_event_id=7 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11141，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 9 步** — event_id=8（parent=7），tick=12869780：L4 污点进入体系结构寄存器，request_id=11141，va=`75b70`，corr=seq_primary；污染值离开 LSQ 进入寄存器数据通路。 下一步：event_id=9（sq_complete）以 parent_event_id=8 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11141，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 10 步** — event_id=9（parent=6），tick=12869780：L3 sq_complete，request_id=—，va=`48fb70`，pa=`—`；store 侧继续携带被污染的值。 下一步：event_id=10（consumer）以 parent_event_id=9 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11141，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 11 步** — event_id=10（parent=4），tick=12869780：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=11（consumer）以 parent_event_id=10 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11144，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 12 步** — event_id=11（parent=10），tick=12870165：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=12（consumer）以 parent_event_id=11 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11146，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 13 步** — event_id=12（parent=10），tick=12870165：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=13（consumer）以 parent_event_id=12 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11146，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 14 步** — event_id=13（parent=10），tick=12870165：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=14（consumer）以 parent_event_id=13 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11146，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 15 步** — event_id=14（parent=10），tick=12870165：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=15（consumer）以 parent_event_id=14 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11147，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 16 步** — event_id=15（parent=10），tick=12870550：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=16（consumer）以 parent_event_id=15 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11150，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 17 步** — event_id=16（parent=10），tick=12870550：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=17（consumer）以 parent_event_id=16 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11150，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 18 步** — event_id=17（parent=10），tick=12870550：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=18（consumer）以 parent_event_id=17 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11150，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 19 步** — event_id=18（parent=14），tick=12922910：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=19（consumer）以 parent_event_id=18 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11153，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 20 步** — event_id=19（parent=14），tick=12924835：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=20（consumer）以 parent_event_id=19 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11158，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 21 步** — event_id=20（parent=10），tick=12924835：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=21（consumer）以 parent_event_id=20 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11160，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 22 步** — event_id=21（parent=10），tick=12924835：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=22（consumer）以 parent_event_id=21 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11160，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 23 步** — event_id=22（parent=10），tick=12924835：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=23（consumer）以 parent_event_id=22 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11160，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 24 步** — event_id=23（parent=14），tick=12924835：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=24（consumer）以 parent_event_id=23 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11162，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 25 步** — event_id=24（parent=23），tick=12926375：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=25（consumer）以 parent_event_id=24 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11163，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 26 步** — event_id=25（parent=19），tick=12926760：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=26（consumer）以 parent_event_id=25 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11164，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 27 步** — event_id=26（parent=24），tick=12926760：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=27（consumer）以 parent_event_id=26 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11164，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 28 步** — event_id=27（parent=26），tick=12927145：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=28（consumer）以 parent_event_id=27 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11165，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 29 步** — event_id=28（parent=26），tick=12927145：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=29（consumer）以 parent_event_id=28 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11165，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 30 步** — event_id=29（parent=26），tick=12927145：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=30（consumer）以 parent_event_id=29 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11165，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 31 步** — event_id=30（parent=14），tick=12927145：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=31（consumer）以 parent_event_id=30 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11165，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 32 步** — event_id=31（parent=23），tick=12979505：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=32（consumer）以 parent_event_id=31 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11168，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 33 步** — event_id=32（parent=10），tick=12979505：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=33（consumer）以 parent_event_id=32 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11169，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 34 步** — event_id=33（parent=10），tick=12979505：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=34（consumer）以 parent_event_id=33 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11169，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 35 步** — event_id=34（parent=10），tick=12979505：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=35（consumer）以 parent_event_id=34 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11169，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 36 步** — event_id=35（parent=31），tick=12985280：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=36（consumer）以 parent_event_id=35 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11197，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 37 步** — event_id=36（parent=25），tick=12985665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=37（consumer）以 parent_event_id=36 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11198，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 38 步** — event_id=37（parent=35），tick=12985665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=38（consumer）以 parent_event_id=37 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11198，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 39 步** — event_id=38（parent=37），tick=12986050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=39（consumer）以 parent_event_id=38 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11199，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 40 步** — event_id=39（parent=37），tick=12986050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=40（consumer）以 parent_event_id=39 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11199，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 41 步** — event_id=40（parent=37），tick=12986050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=41（consumer）以 parent_event_id=40 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11199，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 42 步** — event_id=41（parent=30），tick=12986050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=42（consumer）以 parent_event_id=41 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11199，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 43 步** — event_id=42（parent=31），tick=12986050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=43（consumer）以 parent_event_id=42 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11202，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 44 步** — event_id=43（parent=10），tick=12986050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=44（consumer）以 parent_event_id=43 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11203，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 45 步** — event_id=44（parent=10），tick=12986050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=45（consumer）以 parent_event_id=44 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11203，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 46 步** — event_id=45（parent=10），tick=12986050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=46（consumer）以 parent_event_id=45 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11203，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 47 步** — event_id=46（parent=42），tick=12991055：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=47（consumer）以 parent_event_id=46 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11231，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 48 步** — event_id=47（parent=36），tick=12991440：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=48（consumer）以 parent_event_id=47 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11232，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 49 步** — event_id=48（parent=46），tick=12991440：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=49（consumer）以 parent_event_id=48 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11232，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 50 步** — event_id=49（parent=48），tick=12991825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=50（consumer）以 parent_event_id=49 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11233，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 51 步** — event_id=50（parent=48），tick=12991825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=51（consumer）以 parent_event_id=50 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11233，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 52 步** — event_id=51（parent=48），tick=12991825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=52（consumer）以 parent_event_id=51 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11233，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 53 步** — event_id=52（parent=41），tick=12991825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=53（consumer）以 parent_event_id=52 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11233，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 54 步** — event_id=53（parent=42），tick=12991825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=54（consumer）以 parent_event_id=53 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11236，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 55 步** — event_id=54（parent=10），tick=12991825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=55（consumer）以 parent_event_id=54 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11237，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 56 步** — event_id=55（parent=10），tick=12991825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=56（consumer）以 parent_event_id=55 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11237，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 57 步** — event_id=56（parent=10），tick=12991825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=57（consumer）以 parent_event_id=56 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11237，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 58 步** — event_id=57（parent=53），tick=13050345：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=58（consumer）以 parent_event_id=57 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11265，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 59 步** — event_id=58（parent=47），tick=13050730：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=59（consumer）以 parent_event_id=58 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11266，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 60 步** — event_id=59（parent=57），tick=13050730：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=60（consumer）以 parent_event_id=59 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11266，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 61 步** — event_id=60（parent=59），tick=13051115：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=61（consumer）以 parent_event_id=60 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11267，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 62 步** — event_id=61（parent=59），tick=13051115：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=62（consumer）以 parent_event_id=61 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11267，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 63 步** — event_id=62（parent=59），tick=13051115：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=63（consumer）以 parent_event_id=62 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11267，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 64 步** — event_id=63（parent=52），tick=13051115：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=64（consumer）以 parent_event_id=63 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11267，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 65 步** — event_id=64（parent=53），tick=13051115：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=65（consumer）以 parent_event_id=64 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11270，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 66 步** — event_id=65（parent=10），tick=13051115：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=66（consumer）以 parent_event_id=65 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11271，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 67 步** — event_id=66（parent=10），tick=13051115：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=67（consumer）以 parent_event_id=66 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11271，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 68 步** — event_id=67（parent=10），tick=13051115：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=68（consumer）以 parent_event_id=67 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11271，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 69 步** — event_id=68（parent=64），tick=13051115：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=69（consumer）以 parent_event_id=68 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11299，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 70 步** — event_id=69（parent=58），tick=13051500：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=70（consumer）以 parent_event_id=69 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11300，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 71 步** — event_id=70（parent=68），tick=13051500：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=71（consumer）以 parent_event_id=70 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11300，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 72 步** — event_id=71（parent=70），tick=13051885：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=72（consumer）以 parent_event_id=71 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11301，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 73 步** — event_id=72（parent=70），tick=13051885：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=73（consumer）以 parent_event_id=72 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11301，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 74 步** — event_id=73（parent=70），tick=13051885：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=74（consumer）以 parent_event_id=73 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11301，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 75 步** — event_id=74（parent=63），tick=13051885：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=75（consumer）以 parent_event_id=74 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11301，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 76 步** — event_id=75（parent=64），tick=13051885：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=76（consumer）以 parent_event_id=75 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11304，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 77 步** — event_id=76（parent=10），tick=13051885：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=77（consumer）以 parent_event_id=76 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11305，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 78 步** — event_id=77（parent=10），tick=13051885：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=78（consumer）以 parent_event_id=77 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11305，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 79 步** — event_id=78（parent=10），tick=13051885：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=79（consumer）以 parent_event_id=78 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11305，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 80 步** — event_id=79（parent=75），tick=13061895：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=80（consumer）以 parent_event_id=79 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11333，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 81 步** — event_id=80（parent=69），tick=13062280：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=81（consumer）以 parent_event_id=80 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11334，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 82 步** — event_id=81（parent=79），tick=13062280：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=82（consumer）以 parent_event_id=81 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11334，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 83 步** — event_id=82（parent=81），tick=13062665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=83（consumer）以 parent_event_id=82 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11335，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 84 步** — event_id=83（parent=81），tick=13062665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=84（consumer）以 parent_event_id=83 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11335，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 85 步** — event_id=84（parent=81），tick=13062665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=85（consumer）以 parent_event_id=84 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11335，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 86 步** — event_id=85（parent=74），tick=13062665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=86（consumer）以 parent_event_id=85 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11335，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 87 步** — event_id=86（parent=75），tick=13062665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=87（consumer）以 parent_event_id=86 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11338，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 88 步** — event_id=87（parent=10），tick=13062665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=88（consumer）以 parent_event_id=87 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11339，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 89 步** — event_id=88（parent=10），tick=13062665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=89（consumer）以 parent_event_id=88 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11339，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 90 步** — event_id=89（parent=10），tick=13062665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=90（consumer）以 parent_event_id=89 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11339，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 91 步** — event_id=90（parent=86），tick=13062665：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=91（consumer）以 parent_event_id=90 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11367，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 92 步** — event_id=91（parent=80），tick=13063050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=92（consumer）以 parent_event_id=91 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11368，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 93 步** — event_id=92（parent=90），tick=13063050：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=93（consumer）以 parent_event_id=92 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11368，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 94 步** — event_id=93（parent=92），tick=13063435：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=94（consumer）以 parent_event_id=93 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11369，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 95 步** — event_id=94（parent=92），tick=13063435：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=95（consumer）以 parent_event_id=94 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11369，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 96 步** — event_id=95（parent=92），tick=13063435：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=96（consumer）以 parent_event_id=95 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11369，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 97 步** — event_id=96（parent=85），tick=13063435：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=97（consumer）以 parent_event_id=96 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11369，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 98 步** — event_id=97（parent=86），tick=13063435：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=98（consumer）以 parent_event_id=97 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11372，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 99 步** — event_id=98（parent=10），tick=13063435：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=99（consumer）以 parent_event_id=98 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11373，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 100 步** — event_id=99（parent=10），tick=13063435：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=100（consumer）以 parent_event_id=99 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11373，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 101 步** — event_id=100（parent=10），tick=13063435：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=101（consumer）以 parent_event_id=100 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11373，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 102 步** — event_id=101（parent=97），tick=13115025：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=102（consumer）以 parent_event_id=101 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11424，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 103 步** — event_id=102（parent=91），tick=13115410：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=103（consumer）以 parent_event_id=102 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11425，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 104 步** — event_id=103（parent=101），tick=13115410：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=104（consumer）以 parent_event_id=103 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11425，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 105 步** — event_id=104（parent=103），tick=13115795：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=105（consumer）以 parent_event_id=104 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11426，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 106 步** — event_id=105（parent=103），tick=13115795：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=106（consumer）以 parent_event_id=105 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11426，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 107 步** — event_id=106（parent=103），tick=13115795：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=107（consumer）以 parent_event_id=106 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11426，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 108 步** — event_id=107（parent=96），tick=13115795：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=108（consumer）以 parent_event_id=107 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11426，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 109 步** — event_id=108（parent=97），tick=13115795：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=109（consumer）以 parent_event_id=108 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11429，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 110 步** — event_id=109（parent=10），tick=13115795：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=110（consumer）以 parent_event_id=109 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11430，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 111 步** — event_id=110（parent=10），tick=13115795：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=111（consumer）以 parent_event_id=110 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11430，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 112 步** — event_id=111（parent=10），tick=13115795：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=112（consumer）以 parent_event_id=111 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11430，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 113 步** — event_id=112（parent=108），tick=13115795：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=113（consumer）以 parent_event_id=112 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11458，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 114 步** — event_id=113（parent=102），tick=13116180：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=114（consumer）以 parent_event_id=113 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11459，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 115 步** — event_id=114（parent=112），tick=13116180：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=115（consumer）以 parent_event_id=114 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11459，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 116 步** — event_id=115（parent=114），tick=13116565：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=116（consumer）以 parent_event_id=115 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11460，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 117 步** — event_id=116（parent=114），tick=13116565：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=117（consumer）以 parent_event_id=116 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11460，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 118 步** — event_id=117（parent=114），tick=13116565：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=118（consumer）以 parent_event_id=117 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11460，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 119 步** — event_id=118（parent=107），tick=13116565：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=119（consumer）以 parent_event_id=118 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11460，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 120 步** — event_id=119（parent=108），tick=13116565：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=120（consumer）以 parent_event_id=119 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11463，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 121 步** — event_id=120（parent=10），tick=13116565：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=121（consumer）以 parent_event_id=120 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11464，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 122 步** — event_id=121（parent=10），tick=13116565：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=122（consumer）以 parent_event_id=121 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11464，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 123 步** — event_id=122（parent=10），tick=13116565：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=123（consumer）以 parent_event_id=122 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11464，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 124 步** — event_id=123（parent=119），tick=13201650：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=124（consumer）以 parent_event_id=123 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11563，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 125 步** — event_id=124（parent=113），tick=13202035：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=125（consumer）以 parent_event_id=124 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11564，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 126 步** — event_id=125（parent=123），tick=13202035：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=126（consumer）以 parent_event_id=125 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11564，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 127 步** — event_id=126（parent=125），tick=13202420：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=127（consumer）以 parent_event_id=126 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11565，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 128 步** — event_id=127（parent=125），tick=13202420：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=128（consumer）以 parent_event_id=127 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11565，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 129 步** — event_id=128（parent=125），tick=13202420：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=129（consumer）以 parent_event_id=128 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11565，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 130 步** — event_id=129（parent=118），tick=13202420：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=130（consumer）以 parent_event_id=129 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11565，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 131 步** — event_id=130（parent=119），tick=13202420：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=131（consumer）以 parent_event_id=130 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11568，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 132 步** — event_id=131（parent=10），tick=13202420：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=132（consumer）以 parent_event_id=131 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11569，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 133 步** — event_id=132（parent=10），tick=13202420：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=133（consumer）以 parent_event_id=132 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11569，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 134 步** — event_id=133（parent=10），tick=13202420：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=134（consumer）以 parent_event_id=133 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11569，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 135 步** — event_id=134（parent=124），tick=13202805：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=135（consumer）以 parent_event_id=134 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11598，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 136 步** — event_id=135（parent=48），tick=13203190：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=136（consumer）以 parent_event_id=135 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11599，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 137 步** — event_id=136（parent=48），tick=13203190：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=137（consumer）以 parent_event_id=136 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11599，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 138 步** — event_id=137（parent=48），tick=13203190：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=138（consumer）以 parent_event_id=137 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11599，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 139 步** — event_id=138（parent=129），tick=13203190：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=139（consumer）以 parent_event_id=138 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11599，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 140 步** — event_id=139（parent=130），tick=13203190：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=140（consumer）以 parent_event_id=139 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11602，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 141 步** — event_id=140（parent=10），tick=13203190：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=141（consumer）以 parent_event_id=140 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11603，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 142 步** — event_id=141（parent=10），tick=13203190：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=142（consumer）以 parent_event_id=141 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11603，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 143 步** — event_id=142（parent=10），tick=13203190：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=143（consumer）以 parent_event_id=142 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11603，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 144 步** — event_id=143（parent=139），tick=13205885：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=144（consumer）以 parent_event_id=143 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11631，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 145 步** — event_id=144（parent=134），tick=13206270：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=145（consumer）以 parent_event_id=144 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11632，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 146 步** — event_id=145（parent=143），tick=13206270：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=146（consumer）以 parent_event_id=145 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11632，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 147 步** — event_id=146（parent=145），tick=13206655：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=147（consumer）以 parent_event_id=146 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11633，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 148 步** — event_id=147（parent=145），tick=13206655：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=148（consumer）以 parent_event_id=147 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11633，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 149 步** — event_id=148（parent=145），tick=13206655：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=149（consumer）以 parent_event_id=148 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11633，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 150 步** — event_id=149（parent=138），tick=13206655：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=150（consumer）以 parent_event_id=149 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11633，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 151 步** — event_id=150（parent=139），tick=13206655：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=151（consumer）以 parent_event_id=150 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11636，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 152 步** — event_id=151（parent=10），tick=13206655：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=152（consumer）以 parent_event_id=151 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11637，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 153 步** — event_id=152（parent=10），tick=13206655：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=153（consumer）以 parent_event_id=152 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11637，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 154 步** — event_id=153（parent=10），tick=13206655：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=154（consumer）以 parent_event_id=153 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11637，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 155 步** — event_id=154（parent=59），tick=13208195：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=155（consumer）以 parent_event_id=154 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11667，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 156 步** — event_id=155（parent=59），tick=13208195：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=156（consumer）以 parent_event_id=155 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11667，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 157 步** — event_id=156（parent=59），tick=13208195：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=157（consumer）以 parent_event_id=156 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11667，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 158 步** — event_id=157（parent=149），tick=13208195：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=158（consumer）以 parent_event_id=157 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11667，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 159 步** — event_id=158（parent=10），tick=13208195：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=159（consumer）以 parent_event_id=158 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11671，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 160 步** — event_id=159（parent=10），tick=13208195：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=160（consumer）以 parent_event_id=159 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11671，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 161 步** — event_id=160（parent=10），tick=13208195：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=161（consumer）以 parent_event_id=160 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11671，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 162 步** — event_id=161（parent=74），tick=13266715：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=162（consumer）以 parent_event_id=161 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11723，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 163 步** — event_id=162（parent=161），tick=13267100：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=163（consumer）以 parent_event_id=162 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11724，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 164 步** — event_id=163（parent=162），tick=13267485：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=164（consumer）以 parent_event_id=163 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11725，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 165 步** — event_id=164（parent=162），tick=13267485：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=165（consumer）以 parent_event_id=164 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11725，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 166 步** — event_id=165（parent=162），tick=13267485：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=166（consumer）以 parent_event_id=165 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11725，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 167 步** — event_id=166（parent=74），tick=13267485：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=167（consumer）以 parent_event_id=166 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11728，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 168 步** — event_id=167（parent=10），tick=13267485：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=168（consumer）以 parent_event_id=167 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11729，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 169 步** — event_id=168（parent=10），tick=13267485：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=169（consumer）以 parent_event_id=168 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11729，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 170 步** — event_id=169（parent=10），tick=13267485：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=170（consumer）以 parent_event_id=169 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11729，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 171 步** — event_id=170（parent=64），tick=13267870：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=171（consumer）以 parent_event_id=170 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11758，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 172 步** — event_id=171（parent=90），tick=13268255：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=172（consumer）以 parent_event_id=171 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11759，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 173 步** — event_id=172（parent=90），tick=13268255：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=173（consumer）以 parent_event_id=172 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11759，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 174 步** — event_id=173（parent=90），tick=13268255：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=174（consumer）以 parent_event_id=173 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11759，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 175 步** — event_id=174（parent=68），tick=13268255：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=175（consumer）以 parent_event_id=174 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11759，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 176 步** — event_id=175（parent=10），tick=13268255：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=176（consumer）以 parent_event_id=175 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11763，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 177 步** — event_id=176（parent=10），tick=13268255：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=177（consumer）以 parent_event_id=176 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11763，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 178 步** — event_id=177（parent=10），tick=13268255：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=178（consumer）以 parent_event_id=177 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11763，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 179 步** — event_id=178（parent=86），tick=13313685：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=179（consumer）以 parent_event_id=178 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11791，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 180 步** — event_id=179（parent=178），tick=13314070：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=180（consumer）以 parent_event_id=179 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11792，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 181 步** — event_id=180（parent=179），tick=13314455：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=181（consumer）以 parent_event_id=180 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11793，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 182 步** — event_id=181（parent=179），tick=13314455：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=182（consumer）以 parent_event_id=181 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11793，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 183 步** — event_id=182（parent=179），tick=13314455：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=183（consumer）以 parent_event_id=182 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11793，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 184 步** — event_id=183（parent=10），tick=13314455：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=184（consumer）以 parent_event_id=183 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11797，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 185 步** — event_id=184（parent=10），tick=13314455：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=185（consumer）以 parent_event_id=184 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11797，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 186 步** — event_id=185（parent=10），tick=13314455：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=186（consumer）以 parent_event_id=185 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11797，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 187 步** — event_id=186（parent=112），tick=13315225：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=187（consumer）以 parent_event_id=186 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11827，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 188 步** — event_id=187（parent=112），tick=13315225：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=188（consumer）以 parent_event_id=187 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11827，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 189 步** — event_id=188（parent=112），tick=13315225：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=189（consumer）以 parent_event_id=188 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11827，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 190 步** — event_id=189（parent=10），tick=13315225：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=190（consumer）以 parent_event_id=189 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11831，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 191 步** — event_id=190（parent=10），tick=13315225：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=191（consumer）以 parent_event_id=190 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11831，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 192 步** — event_id=191（parent=10），tick=13315225：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=192（consumer）以 parent_event_id=191 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11831，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 193 步** — event_id=192（parent=35），tick=13315995：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=193（consumer）以 parent_event_id=192 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11884，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 194 步** — event_id=193（parent=35），tick=13315995：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=194（consumer）以 parent_event_id=193 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11884，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 195 步** — event_id=194（parent=35），tick=13315995：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=195（consumer）以 parent_event_id=194 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11884，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 196 步** — event_id=195（parent=108），tick=13315995：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=196（consumer）以 parent_event_id=195 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11887，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 197 步** — event_id=196（parent=10），tick=13315995：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=197（consumer）以 parent_event_id=196 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11888，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 198 步** — event_id=197（parent=10），tick=13315995：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=198（consumer）以 parent_event_id=197 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11888，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 199 步** — event_id=198（parent=10），tick=13315995：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=199（consumer）以 parent_event_id=198 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11888，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 200 步** — event_id=199（parent=195），tick=13315995：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=200（consumer）以 parent_event_id=199 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11890，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 201 步** — event_id=200（parent=113），tick=13316380：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=201（consumer）以 parent_event_id=200 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11891，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 202 步** — event_id=201（parent=199），tick=13316380：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=202（consumer）以 parent_event_id=201 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11891，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 203 步** — event_id=202（parent=201），tick=13316765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=203（consumer）以 parent_event_id=202 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11892，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 204 步** — event_id=203（parent=201），tick=13316765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=204（consumer）以 parent_event_id=203 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11892，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 205 步** — event_id=204（parent=201），tick=13316765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=205（consumer）以 parent_event_id=204 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11892，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 206 步** — event_id=205（parent=118），tick=13316765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=206（consumer）以 parent_event_id=205 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11892，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 207 步** — event_id=206（parent=195），tick=13316765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=207（consumer）以 parent_event_id=206 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11895，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 208 步** — event_id=207（parent=10），tick=13316765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=208（consumer）以 parent_event_id=207 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11896，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 209 步** — event_id=208（parent=10），tick=13316765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=209（consumer）以 parent_event_id=208 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11896，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 210 步** — event_id=209（parent=10），tick=13316765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=210（consumer）以 parent_event_id=209 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11896，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 211 步** — event_id=210（parent=206），tick=13324080：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=211（consumer）以 parent_event_id=210 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11898，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 212 步** — event_id=211（parent=200），tick=13324465：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=212（consumer）以 parent_event_id=211 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11899，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 213 步** — event_id=212（parent=210），tick=13324465：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=213（consumer）以 parent_event_id=212 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11899，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 214 步** — event_id=213（parent=212），tick=13324850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=214（consumer）以 parent_event_id=213 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11900，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 215 步** — event_id=214（parent=212），tick=13324850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=215（consumer）以 parent_event_id=214 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11900，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 216 步** — event_id=215（parent=212），tick=13324850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=216（consumer）以 parent_event_id=215 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11900，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 217 步** — event_id=216（parent=10），tick=13324850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=217（consumer）以 parent_event_id=216 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11904，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 218 步** — event_id=217（parent=10），tick=13324850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=218（consumer）以 parent_event_id=217 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11904，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 219 步** — event_id=218（parent=10），tick=13324850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=219（consumer）以 parent_event_id=218 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11904，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 220 步** — event_id=219（parent=30），tick=13324850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=220（consumer）以 parent_event_id=219 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11906，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 221 步** — event_id=220（parent=42），tick=13325620：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=221（consumer）以 parent_event_id=220 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11908，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 222 步** — event_id=221（parent=42），tick=13325620：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=222（consumer）以 parent_event_id=221 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11908，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 223 步** — event_id=222（parent=42），tick=13325620：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=223（consumer）以 parent_event_id=222 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11908，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 224 步** — event_id=223（parent=10），tick=13325620：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=224（consumer）以 parent_event_id=223 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11912，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 225 步** — event_id=224（parent=10），tick=13325620：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=225（consumer）以 parent_event_id=224 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11912，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 226 步** — event_id=225（parent=10），tick=13325620：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=226（consumer）以 parent_event_id=225 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11912，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 227 步** — event_id=226（parent=46），tick=13328315：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=227（consumer）以 parent_event_id=226 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11914，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 228 步** — event_id=227（parent=24），tick=13328700：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=228（consumer）以 parent_event_id=227 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11915，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 229 步** — event_id=228（parent=226），tick=13328700：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=229（consumer）以 parent_event_id=228 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11915，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 230 步** — event_id=229（parent=228），tick=13329085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=230（consumer）以 parent_event_id=229 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11916，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 231 步** — event_id=230（parent=228），tick=13329085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=231（consumer）以 parent_event_id=230 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11916，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 232 步** — event_id=231（parent=228），tick=13329085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=232（consumer）以 parent_event_id=231 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11916，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 233 步** — event_id=232（parent=46），tick=13329085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=233（consumer）以 parent_event_id=232 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11919，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 234 步** — event_id=233（parent=10），tick=13329085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=234（consumer）以 parent_event_id=233 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11920，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 235 步** — event_id=234（parent=10），tick=13329085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=235（consumer）以 parent_event_id=234 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11920，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 236 步** — event_id=235（parent=10），tick=13329085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=236（consumer）以 parent_event_id=235 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11920，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 237 步** — event_id=236（parent=227），tick=13329470：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=237（consumer）以 parent_event_id=236 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11923，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 238 步** — event_id=237（parent=63），tick=13329855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=238（consumer）以 parent_event_id=237 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11924，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 239 步** — event_id=238（parent=63），tick=13329855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=239（consumer）以 parent_event_id=238 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11924，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 240 步** — event_id=239（parent=63），tick=13329855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=240（consumer）以 parent_event_id=239 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11924，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 241 步** — event_id=240（parent=52），tick=13329855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=241（consumer）以 parent_event_id=240 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11924，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 242 步** — event_id=241（parent=10），tick=13329855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=242（consumer）以 parent_event_id=241 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11928，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 243 步** — event_id=242（parent=10），tick=13329855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=243（consumer）以 parent_event_id=242 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11928，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 244 步** — event_id=243（parent=10），tick=13329855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=244（consumer）以 parent_event_id=243 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11928，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 245 步** — event_id=244（parent=125），tick=13331010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=245（consumer）以 parent_event_id=244 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11932，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 246 步** — event_id=245（parent=125），tick=13331010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=246（consumer）以 parent_event_id=245 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11932，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 247 步** — event_id=246（parent=125），tick=13331010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=247（consumer）以 parent_event_id=246 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11932，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 248 步** — event_id=247（parent=10），tick=13331010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=248（consumer）以 parent_event_id=247 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11936，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 249 步** — event_id=248（parent=10），tick=13331010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=249（consumer）以 parent_event_id=248 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11936，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 250 步** — event_id=249（parent=10），tick=13331010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=250（consumer）以 parent_event_id=249 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11936，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 251 步** — event_id=250（parent=48），tick=13331780：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=251（consumer）以 parent_event_id=250 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11940，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 252 步** — event_id=251（parent=48），tick=13331780：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=252（consumer）以 parent_event_id=251 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11940，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 253 步** — event_id=252（parent=48），tick=13331780：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=253（consumer）以 parent_event_id=252 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11940，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 254 步** — event_id=253（parent=10），tick=13331780：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=254（consumer）以 parent_event_id=253 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11944，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 255 步** — event_id=254（parent=10），tick=13331780：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=255（consumer）以 parent_event_id=254 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11944，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 256 步** — event_id=255（parent=10），tick=13331780：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=256（consumer）以 parent_event_id=255 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11944，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 257 步** — event_id=256（parent=145），tick=13336400：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=257（consumer）以 parent_event_id=256 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11948，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 258 步** — event_id=257（parent=145），tick=13336400：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=258（consumer）以 parent_event_id=257 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11948，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 259 步** — event_id=258（parent=145），tick=13336400：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=259（consumer）以 parent_event_id=258 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11948，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 260 步** — event_id=259（parent=149），tick=13336400：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=260（consumer）以 parent_event_id=259 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11951，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 261 步** — event_id=260（parent=10），tick=13336400：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=261（consumer）以 parent_event_id=260 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11952，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 262 步** — event_id=261（parent=10），tick=13336400：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=262（consumer）以 parent_event_id=261 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11952，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 263 步** — event_id=262（parent=10），tick=13336400：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=263（consumer）以 parent_event_id=262 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11952，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 264 步** — event_id=263（parent=139），tick=13336785：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=264（consumer）以 parent_event_id=263 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11955，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 265 步** — event_id=264（parent=69），tick=13337170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=265（consumer）以 parent_event_id=264 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11956，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 266 步** — event_id=265（parent=69），tick=13337170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=266（consumer）以 parent_event_id=265 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11956，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 267 步** — event_id=266（parent=69），tick=13337170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=267（consumer）以 parent_event_id=266 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11956，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 268 步** — event_id=267（parent=143），tick=13337170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=268（consumer）以 parent_event_id=267 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11956，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 269 步** — event_id=268（parent=10），tick=13337170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=269（consumer）以 parent_event_id=268 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11960，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 270 步** — event_id=269（parent=10），tick=13337170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=270（consumer）以 parent_event_id=269 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11960，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 271 步** — event_id=270（parent=10），tick=13337170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=271（consumer）以 parent_event_id=270 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11960，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 272 步** — event_id=271（parent=59），tick=13341020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=272（consumer）以 parent_event_id=271 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11964，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 273 步** — event_id=272（parent=59），tick=13341020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=273（consumer）以 parent_event_id=272 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11964，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 274 步** — event_id=273（parent=59），tick=13341020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=274（consumer）以 parent_event_id=273 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11964，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 275 步** — event_id=274（parent=10），tick=13341020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=275（consumer）以 parent_event_id=274 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11968，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 276 步** — event_id=275（parent=10），tick=13341020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=276（consumer）以 parent_event_id=275 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11968，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 277 步** — event_id=276（parent=10），tick=13341020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=277（consumer）以 parent_event_id=276 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11968，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 278 步** — event_id=277（parent=79），tick=13341405：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=278（consumer）以 parent_event_id=277 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11971，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 279 步** — event_id=278（parent=277），tick=13341790：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=279（consumer）以 parent_event_id=278 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11972，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 280 步** — event_id=279（parent=277），tick=13341790：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=280（consumer）以 parent_event_id=279 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11972，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 281 步** — event_id=280（parent=277），tick=13341790：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=281（consumer）以 parent_event_id=280 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11972，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 282 步** — event_id=281（parent=75），tick=13341790：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=282（consumer）以 parent_event_id=281 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11975，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 283 步** — event_id=282（parent=10），tick=13341790：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=283（consumer）以 parent_event_id=282 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11976，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 284 步** — event_id=283（parent=10），tick=13341790：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=284（consumer）以 parent_event_id=283 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11976，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 285 步** — event_id=284（parent=10），tick=13341790：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=285（consumer）以 parent_event_id=284 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11976，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 286 步** — event_id=285（parent=85），tick=13343715：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=286（consumer）以 parent_event_id=285 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11979，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 287 步** — event_id=286（parent=102），tick=13344100：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=287（consumer）以 parent_event_id=286 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11980，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 288 步** — event_id=287（parent=102），tick=13344100：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=288（consumer）以 parent_event_id=287 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11980，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 289 步** — event_id=288（parent=102），tick=13344100：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=289（consumer）以 parent_event_id=288 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11980，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 290 步** — event_id=289（parent=80），tick=13344100：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=290（consumer）以 parent_event_id=289 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11980，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 291 步** — event_id=290（parent=10），tick=13344100：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=291（consumer）以 parent_event_id=290 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11984，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 292 步** — event_id=291（parent=10），tick=13344100：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=292（consumer）以 parent_event_id=291 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11984，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 293 步** — event_id=292（parent=10），tick=13344100：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=293（consumer）以 parent_event_id=292 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11984，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 294 步** — event_id=293（parent=64），tick=13344870：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=294（consumer）以 parent_event_id=293 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11988，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 295 步** — event_id=294（parent=64），tick=13344870：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=295（consumer）以 parent_event_id=294 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11988，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 296 步** — event_id=295（parent=64），tick=13344870：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=296（consumer）以 parent_event_id=295 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11988，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 297 步** — event_id=296（parent=10），tick=13344870：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=297（consumer）以 parent_event_id=296 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11992，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 298 步** — event_id=297（parent=10），tick=13344870：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=298（consumer）以 parent_event_id=297 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11992，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 299 步** — event_id=298（parent=10），tick=13344870：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=299（consumer）以 parent_event_id=298 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11992，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 300 步** — event_id=299（parent=170），tick=13347950：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=300（consumer）以 parent_event_id=299 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11996，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 301 步** — event_id=300（parent=170），tick=13347950：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=301（consumer）以 parent_event_id=300 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11996，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 302 步** — event_id=301（parent=170），tick=13347950：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=302（consumer）以 parent_event_id=301 承接本事件，共享 fault_id=1 与 dyn_inst_seq=11996，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 303 步** — event_id=302（parent=10），tick=13347950：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=303（consumer）以 parent_event_id=302 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12000，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 304 步** — event_id=303（parent=10），tick=13347950：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=304（consumer）以 parent_event_id=303 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12000，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 305 步** — event_id=304（parent=10），tick=13347950：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=305（consumer）以 parent_event_id=304 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12000，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 306 步** — event_id=305（parent=114），tick=13348720：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=306（consumer）以 parent_event_id=305 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12004，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 307 步** — event_id=306（parent=114），tick=13348720：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=307（consumer）以 parent_event_id=306 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12004，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 308 步** — event_id=307（parent=114），tick=13348720：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=308（consumer）以 parent_event_id=307 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12004，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 309 步** — event_id=308（parent=10），tick=13348720：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=309（consumer）以 parent_event_id=308 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12008，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 310 步** — event_id=309（parent=10），tick=13348720：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=310（consumer）以 parent_event_id=309 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12008，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 311 步** — event_id=310（parent=10），tick=13348720：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=311（consumer）以 parent_event_id=310 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12008，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 312 步** — event_id=311（parent=179），tick=13401080：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=312（consumer）以 parent_event_id=311 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12012，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 313 步** — event_id=312（parent=179），tick=13401080：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=313（consumer）以 parent_event_id=312 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12012，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 314 步** — event_id=313（parent=179），tick=13401080：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=314（consumer）以 parent_event_id=313 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12012，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 315 步** — event_id=314（parent=10），tick=13401080：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=315（consumer）以 parent_event_id=314 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12016，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 316 步** — event_id=315（parent=10），tick=13401080：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=316（consumer）以 parent_event_id=315 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12016，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 317 步** — event_id=316（parent=10），tick=13401080：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=317（consumer）以 parent_event_id=316 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12016，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 318 步** — event_id=317（parent=112），tick=13401850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=318（consumer）以 parent_event_id=317 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12020，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 319 步** — event_id=318（parent=112），tick=13401850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=319（consumer）以 parent_event_id=318 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12020，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 320 步** — event_id=319（parent=112），tick=13401850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=320（consumer）以 parent_event_id=319 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12020，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 321 步** — event_id=320（parent=10），tick=13401850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=321（consumer）以 parent_event_id=320 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12024，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 322 步** — event_id=321（parent=10），tick=13401850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=322（consumer）以 parent_event_id=321 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12024，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 323 步** — event_id=322（parent=10），tick=13401850：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=323（consumer）以 parent_event_id=322 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12024，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 324 步** — event_id=323（parent=35），tick=13406085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=324（consumer）以 parent_event_id=323 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12028，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 325 步** — event_id=324（parent=35），tick=13406085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=325（consumer）以 parent_event_id=324 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12028，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 326 步** — event_id=325（parent=35），tick=13406085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=326（consumer）以 parent_event_id=325 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12028，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 327 步** — event_id=326（parent=10），tick=13406085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=327（consumer）以 parent_event_id=326 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12032，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 328 步** — event_id=327（parent=10），tick=13406085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=328（consumer）以 parent_event_id=327 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12032，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 329 步** — event_id=328（parent=10），tick=13406085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=329（consumer）以 parent_event_id=328 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12032，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 330 步** — event_id=329（parent=201），tick=13406855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=330（consumer）以 parent_event_id=329 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12036，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 331 步** — event_id=330（parent=201），tick=13406855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=331（consumer）以 parent_event_id=330 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12036，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 332 步** — event_id=331（parent=201），tick=13406855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=332（consumer）以 parent_event_id=331 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12036，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 333 步** — event_id=332（parent=10），tick=13406855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=333（consumer）以 parent_event_id=332 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12040，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 334 步** — event_id=333（parent=10），tick=13406855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=334（consumer）以 parent_event_id=333 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12040，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 335 步** — event_id=334（parent=10），tick=13406855：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=335（consumer）以 parent_event_id=334 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12040，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 336 步** — event_id=335（parent=212），tick=13411090：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=336（consumer）以 parent_event_id=335 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12044，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 337 步** — event_id=336（parent=212），tick=13411090：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=337（consumer）以 parent_event_id=336 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12044，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 338 步** — event_id=337（parent=212），tick=13411090：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=338（consumer）以 parent_event_id=337 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12044，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 339 步** — event_id=338（parent=10），tick=13411090：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=339（consumer）以 parent_event_id=338 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12048，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 340 步** — event_id=339（parent=10），tick=13411090：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=340（consumer）以 parent_event_id=339 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12048，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 341 步** — event_id=340（parent=10），tick=13411090：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=341（consumer）以 parent_event_id=340 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12048，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 342 步** — event_id=341（parent=42），tick=13411860：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=342（consumer）以 parent_event_id=341 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12052，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 343 步** — event_id=342（parent=42），tick=13411860：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=343（consumer）以 parent_event_id=342 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12052，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 344 步** — event_id=343（parent=42），tick=13411860：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=344（consumer）以 parent_event_id=343 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12052，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 345 步** — event_id=344（parent=10），tick=13411860：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=345（consumer）以 parent_event_id=344 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12056，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 346 步** — event_id=345（parent=10），tick=13411860：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=346（consumer）以 parent_event_id=345 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12056，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 347 步** — event_id=346（parent=10），tick=13411860：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=347（consumer）以 parent_event_id=346 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12056，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 348 步** — event_id=347（parent=228），tick=13530825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=348（consumer）以 parent_event_id=347 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12060，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 349 步** — event_id=348（parent=228），tick=13530825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=349（consumer）以 parent_event_id=348 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12060，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 350 步** — event_id=349（parent=228），tick=13530825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=350（consumer）以 parent_event_id=349 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12060，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 351 步** — event_id=350（parent=10），tick=13530825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=351（consumer）以 parent_event_id=350 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12064，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 352 步** — event_id=351（parent=10），tick=13530825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=352（consumer）以 parent_event_id=351 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12064，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 353 步** — event_id=352（parent=10），tick=13530825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=353（consumer）以 parent_event_id=352 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12064，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 354 步** — event_id=353（parent=63），tick=13531595：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=354（consumer）以 parent_event_id=353 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12068，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 355 步** — event_id=354（parent=63），tick=13531595：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=355（consumer）以 parent_event_id=354 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12068，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 356 步** — event_id=355（parent=63），tick=13531595：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=356（consumer）以 parent_event_id=355 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12068，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 357 步** — event_id=356（parent=10），tick=13531595：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=357（consumer）以 parent_event_id=356 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12072，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 358 步** — event_id=357（parent=10），tick=13531595：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=358（consumer）以 parent_event_id=357 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12072，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 359 步** — event_id=358（parent=10），tick=13531595：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=359（consumer）以 parent_event_id=358 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12072，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 360 步** — event_id=359（parent=125），tick=13532365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=360（consumer）以 parent_event_id=359 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12076，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 361 步** — event_id=360（parent=125），tick=13532365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=361（consumer）以 parent_event_id=360 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12076，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 362 步** — event_id=361（parent=125），tick=13532365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=362（consumer）以 parent_event_id=361 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12076，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 363 步** — event_id=362（parent=10），tick=13532365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=363（consumer）以 parent_event_id=362 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12080，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 364 步** — event_id=363（parent=10），tick=13532365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=364（consumer）以 parent_event_id=363 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12080，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 365 步** — event_id=364（parent=10），tick=13532365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=365（consumer）以 parent_event_id=364 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12080，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 366 步** — event_id=365（parent=48），tick=13533135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=366（consumer）以 parent_event_id=365 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12084，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 367 步** — event_id=366（parent=48），tick=13533135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=367（consumer）以 parent_event_id=366 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12084，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 368 步** — event_id=367（parent=48），tick=13533135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=368（consumer）以 parent_event_id=367 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12084，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 369 步** — event_id=368（parent=10），tick=13533135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=369（consumer）以 parent_event_id=368 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12088，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 370 步** — event_id=369（parent=10），tick=13533135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=370（consumer）以 parent_event_id=369 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12088，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 371 步** — event_id=370（parent=10），tick=13533135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=371（consumer）以 parent_event_id=370 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12088，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 372 步** — event_id=371（parent=145），tick=13533905：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=372（consumer）以 parent_event_id=371 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12092，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 373 步** — event_id=372（parent=145），tick=13533905：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=373（consumer）以 parent_event_id=372 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12092，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 374 步** — event_id=373（parent=145），tick=13533905：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=374（consumer）以 parent_event_id=373 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12092，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 375 步** — event_id=374（parent=10），tick=13533905：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=375（consumer）以 parent_event_id=374 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12096，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 376 步** — event_id=375（parent=10），tick=13533905：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=376（consumer）以 parent_event_id=375 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12096，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 377 步** — event_id=376（parent=10），tick=13533905：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=377（consumer）以 parent_event_id=376 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12096，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 378 步** — event_id=377（parent=69），tick=13534675：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=378（consumer）以 parent_event_id=377 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12100，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 379 步** — event_id=378（parent=69），tick=13534675：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=379（consumer）以 parent_event_id=378 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12100，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 380 步** — event_id=379（parent=69），tick=13534675：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=380（consumer）以 parent_event_id=379 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12100，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 381 步** — event_id=380（parent=10），tick=13534675：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=381（consumer）以 parent_event_id=380 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12104，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 382 步** — event_id=381（parent=10），tick=13534675：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=382（consumer）以 parent_event_id=381 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12104，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 383 步** — event_id=382（parent=10），tick=13534675：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=383（consumer）以 parent_event_id=382 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12104，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 384 步** — event_id=383（parent=59），tick=13543530：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=384（consumer）以 parent_event_id=383 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12108，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 385 步** — event_id=384（parent=59），tick=13543530：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=385（consumer）以 parent_event_id=384 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12108，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 386 步** — event_id=385（parent=59），tick=13543530：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=386（consumer）以 parent_event_id=385 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12108，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 387 步** — event_id=386（parent=10），tick=13543530：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=387（consumer）以 parent_event_id=386 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12112，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 388 步** — event_id=387（parent=10），tick=13543530：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=388（consumer）以 parent_event_id=387 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12112，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 389 步** — event_id=388（parent=10），tick=13543530：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=389（consumer）以 parent_event_id=388 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12112，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 390 步** — event_id=389（parent=277），tick=13544300：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=390（consumer）以 parent_event_id=389 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12116，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 391 步** — event_id=390（parent=277），tick=13544300：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=391（consumer）以 parent_event_id=390 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12116，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 392 步** — event_id=391（parent=277），tick=13544300：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=392（consumer）以 parent_event_id=391 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12116，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 393 步** — event_id=392（parent=10），tick=13544300：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=393（consumer）以 parent_event_id=392 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 394 步** — event_id=393（parent=10），tick=13544300：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=394（consumer）以 parent_event_id=393 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 395 步** — event_id=394（parent=10），tick=13544300：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=395（consumer）以 parent_event_id=394 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12120，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 396 步** — event_id=395（parent=102），tick=13545840：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=396（consumer）以 parent_event_id=395 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12124，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 397 步** — event_id=396（parent=102），tick=13545840：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=397（consumer）以 parent_event_id=396 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12124，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 398 步** — event_id=397（parent=102），tick=13545840：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=398（consumer）以 parent_event_id=397 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12124，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 399 步** — event_id=398（parent=10），tick=13545840：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=399（consumer）以 parent_event_id=398 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12128，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 400 步** — event_id=399（parent=10），tick=13545840：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=400（consumer）以 parent_event_id=399 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12128，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 401 步** — event_id=400（parent=10），tick=13545840：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=401（consumer）以 parent_event_id=400 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12128，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 402 步** — event_id=401（parent=64），tick=13546610：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=402（consumer）以 parent_event_id=401 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12132，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 403 步** — event_id=402（parent=64），tick=13546610：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=403（consumer）以 parent_event_id=402 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12132，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 404 步** — event_id=403（parent=64），tick=13546610：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=404（consumer）以 parent_event_id=403 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12132，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 405 步** — event_id=404（parent=10），tick=13546610：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=405（consumer）以 parent_event_id=404 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 406 步** — event_id=405（parent=10），tick=13546610：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=406（consumer）以 parent_event_id=405 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 407 步** — event_id=406（parent=10），tick=13546610：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=407（consumer）以 parent_event_id=406 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12136，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 408 步** — event_id=407（parent=170），tick=13547765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=408（consumer）以 parent_event_id=407 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12140，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 409 步** — event_id=408（parent=170），tick=13547765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=409（consumer）以 parent_event_id=408 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12140，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 410 步** — event_id=409（parent=170），tick=13547765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=410（consumer）以 parent_event_id=409 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12140，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 411 步** — event_id=410（parent=10），tick=13547765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=411（consumer）以 parent_event_id=410 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12144，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 412 步** — event_id=411（parent=10），tick=13547765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=412（consumer）以 parent_event_id=411 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12144，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 413 步** — event_id=412（parent=10），tick=13547765：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=413（consumer）以 parent_event_id=412 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12144，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 414 步** — event_id=413（parent=114），tick=13548535：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=414（consumer）以 parent_event_id=413 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12148，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 415 步** — event_id=414（parent=114），tick=13548535：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=415（consumer）以 parent_event_id=414 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12148，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 416 步** — event_id=415（parent=10），tick=13548535：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=416（consumer）以 parent_event_id=415 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12152，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 417 步** — event_id=416（parent=10），tick=13548535：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=417（consumer）以 parent_event_id=416 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12152，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 418 步** — event_id=417（parent=10），tick=13548535：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=418（consumer）以 parent_event_id=417 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12152，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 419 步** — event_id=418（parent=179），tick=13555465：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=419（consumer）以 parent_event_id=418 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12156，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 420 步** — event_id=419（parent=179），tick=13555465：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=420（consumer）以 parent_event_id=419 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12156，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 421 步** — event_id=420（parent=179），tick=13555465：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=421（consumer）以 parent_event_id=420 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12156，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 422 步** — event_id=421（parent=10），tick=13555465：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=422（consumer）以 parent_event_id=421 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12160，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 423 步** — event_id=422（parent=10），tick=13555465：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=423（consumer）以 parent_event_id=422 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12160，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 424 步** — event_id=423（parent=10），tick=13555465：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=424（consumer）以 parent_event_id=423 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12160，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 425 步** — event_id=424（parent=112），tick=13556235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=425（consumer）以 parent_event_id=424 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12164，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 426 步** — event_id=425（parent=112），tick=13556235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=426（consumer）以 parent_event_id=425 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12164，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 427 步** — event_id=426（parent=112），tick=13556235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=427（consumer）以 parent_event_id=426 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12164，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 428 步** — event_id=427（parent=10），tick=13556235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=428（consumer）以 parent_event_id=427 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12168，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 429 步** — event_id=428（parent=10），tick=13556235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=429（consumer）以 parent_event_id=428 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12168，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 430 步** — event_id=429（parent=35），tick=13558545：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=430（consumer）以 parent_event_id=429 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12172，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 431 步** — event_id=430（parent=35），tick=13558545：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=431（consumer）以 parent_event_id=430 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12172，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 432 步** — event_id=431（parent=35），tick=13558545：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=432（consumer）以 parent_event_id=431 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12172，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 433 步** — event_id=432（parent=10），tick=13558545：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=433（consumer）以 parent_event_id=432 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12176，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 434 步** — event_id=433（parent=201），tick=13559315：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=434（consumer）以 parent_event_id=433 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12180，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 435 步** — event_id=434（parent=212），tick=13560470：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=435（consumer）以 parent_event_id=434 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12188，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 436 步** — event_id=435（parent=212），tick=13560470：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=436（consumer）以 parent_event_id=435 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12188，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 437 步** — event_id=436（parent=10），tick=13560470：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=437（consumer）以 parent_event_id=436 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12192，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 438 步** — event_id=437（parent=10），tick=13560470：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=438（consumer）以 parent_event_id=437 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12192，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 439 步** — event_id=438（parent=42），tick=13561240：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=439（consumer）以 parent_event_id=438 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12196，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 440 步** — event_id=439（parent=228），tick=13567400：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=440（consumer）以 parent_event_id=439 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12204，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 441 步** — event_id=440（parent=10），tick=13567400：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=441（consumer）以 parent_event_id=440 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12208，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 442 步** — event_id=441（parent=63），tick=13568170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=442（consumer）以 parent_event_id=441 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12212，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 443 步** — event_id=442（parent=63），tick=13568170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=443（consumer）以 parent_event_id=442 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12212，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 444 步** — event_id=443（parent=63），tick=13568170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=444（consumer）以 parent_event_id=443 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12212，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 445 步** — event_id=444（parent=10），tick=13568170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=445（consumer）以 parent_event_id=444 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12216，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 446 步** — event_id=445（parent=10），tick=13568170：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=446（consumer）以 parent_event_id=445 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12216，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 447 步** — event_id=446（parent=125），tick=13570480：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=447（consumer）以 parent_event_id=446 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12220，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 448 步** — event_id=447（parent=10），tick=13570480：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=448（consumer）以 parent_event_id=447 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12224，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 449 步** — event_id=448（parent=48），tick=13571250：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=449（consumer）以 parent_event_id=448 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12228，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 450 步** — event_id=449（parent=145），tick=13685595：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=450（consumer）以 parent_event_id=449 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12236，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 451 步** — event_id=450（parent=69），tick=13686365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=451（consumer）以 parent_event_id=450 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12244，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 452 步** — event_id=451（parent=59），tick=13687135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=452（consumer）以 parent_event_id=451 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12252，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 453 步** — event_id=452（parent=10），tick=13687135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=453（consumer）以 parent_event_id=452 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12256，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 454 步** — event_id=453（parent=10），tick=13687135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=454（consumer）以 parent_event_id=453 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12256，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 455 步** — event_id=454（parent=114），tick=13699070：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=455（consumer）以 parent_event_id=454 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12292，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 456 步** — event_id=455（parent=10），tick=13699070：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=456（consumer）以 parent_event_id=455 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12296，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 457 步** — event_id=456（parent=179），tick=13700610：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=457（consumer）以 parent_event_id=456 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12300，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 458 步** — event_id=457（parent=112），tick=13701380：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=458（consumer）以 parent_event_id=457 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12308，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 459 步** — event_id=458（parent=112），tick=13701380：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=459（consumer）以 parent_event_id=458 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12308，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 460 步** — event_id=459（parent=112），tick=13701380：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=460（consumer）以 parent_event_id=459 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12308，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 461 步** — event_id=460（parent=10），tick=13701380：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=461（consumer）以 parent_event_id=460 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12312，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 462 步** — event_id=461（parent=10），tick=13701380：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=462（consumer）以 parent_event_id=461 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12312，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 463 步** — event_id=462（parent=35），tick=13702535：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=463（consumer）以 parent_event_id=462 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12316，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 464 步** — event_id=463（parent=10），tick=13702535：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=464（consumer）以 parent_event_id=463 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12320，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 465 步** — event_id=464（parent=10），tick=13702535：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=465（consumer）以 parent_event_id=464 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12320，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 466 步** — event_id=465（parent=10），tick=13703305：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=466（consumer）以 parent_event_id=465 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12328，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 467 步** — event_id=466（parent=10），tick=13703305：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=467（consumer）以 parent_event_id=466 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12328，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 468 步** — event_id=467（parent=212），tick=13710235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=468（consumer）以 parent_event_id=467 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12332，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 469 步** — event_id=468（parent=212），tick=13710235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=469（consumer）以 parent_event_id=468 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12332，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 470 步** — event_id=469（parent=10），tick=13710235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=470（consumer）以 parent_event_id=469 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12336，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 471 步** — event_id=470（parent=10），tick=13710235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=471（consumer）以 parent_event_id=470 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12336，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 472 步** — event_id=471（parent=10），tick=13710235：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=472（consumer）以 parent_event_id=471 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12336，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 473 步** — event_id=472（parent=10），tick=13711005：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=473（consumer）以 parent_event_id=472 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12344，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 474 步** — event_id=473（parent=10），tick=13711005：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=474（consumer）以 parent_event_id=473 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12344，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 475 步** — event_id=474（parent=228），tick=13713315：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=475（consumer）以 parent_event_id=474 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12348，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 476 步** — event_id=475（parent=228），tick=13713315：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=476（consumer）以 parent_event_id=475 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12348，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 477 步** — event_id=476（parent=10），tick=13713315：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=477（consumer）以 parent_event_id=476 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12352，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 478 步** — event_id=477（parent=10），tick=13713315：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=478（consumer）以 parent_event_id=477 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12352，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 479 步** — event_id=478（parent=63），tick=13714085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=479（consumer）以 parent_event_id=478 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12356，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 480 步** — event_id=479（parent=63），tick=13714085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=480（consumer）以 parent_event_id=479 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12356，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 481 步** — event_id=480（parent=63），tick=13714085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=481（consumer）以 parent_event_id=480 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12356，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 482 步** — event_id=481（parent=10），tick=13714085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=482（consumer）以 parent_event_id=481 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12360，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 483 步** — event_id=482（parent=10），tick=13714085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=483（consumer）以 parent_event_id=482 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12360，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 484 步** — event_id=483（parent=10），tick=13714085：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=484（consumer）以 parent_event_id=483 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12360，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 485 步** — event_id=484（parent=125），tick=13715240：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=485（consumer）以 parent_event_id=484 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12364，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 486 步** — event_id=485（parent=125），tick=13715240：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=486（consumer）以 parent_event_id=485 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12364，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 487 步** — event_id=486（parent=125），tick=13715240：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=487（consumer）以 parent_event_id=486 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12364，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 488 步** — event_id=487（parent=10），tick=13715240：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=488（consumer）以 parent_event_id=487 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12368，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 489 步** — event_id=488（parent=10），tick=13715240：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=489（consumer）以 parent_event_id=488 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12368，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 490 步** — event_id=489（parent=10），tick=13715240：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=490（consumer）以 parent_event_id=489 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12368，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 491 步** — event_id=490（parent=48），tick=13716010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=491（consumer）以 parent_event_id=490 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12372，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 492 步** — event_id=491（parent=48），tick=13716010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=492（consumer）以 parent_event_id=491 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12372，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 493 步** — event_id=492（parent=48），tick=13716010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=493（consumer）以 parent_event_id=492 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12372，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 494 步** — event_id=493（parent=10），tick=13716010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=494（consumer）以 parent_event_id=493 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12376，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 495 步** — event_id=494（parent=10），tick=13716010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=495（consumer）以 parent_event_id=494 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12376，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 496 步** — event_id=495（parent=10），tick=13716010：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=496（consumer）以 parent_event_id=495 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12376，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 497 步** — event_id=496（parent=145），tick=13722555：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=497（consumer）以 parent_event_id=496 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12380，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 498 步** — event_id=497（parent=145），tick=13722555：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=498（consumer）以 parent_event_id=497 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12380，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 499 步** — event_id=498（parent=145），tick=13722555：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=499（consumer）以 parent_event_id=498 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12380，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 500 步** — event_id=499（parent=10），tick=13722555：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=500（consumer）以 parent_event_id=499 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12384，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 501 步** — event_id=500（parent=10），tick=13722555：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=501（consumer）以 parent_event_id=500 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12384，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 502 步** — event_id=501（parent=10），tick=13722555：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=502（consumer）以 parent_event_id=501 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12384，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 503 步** — event_id=502（parent=69），tick=13723325：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=503（consumer）以 parent_event_id=502 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12388，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 504 步** — event_id=503（parent=69），tick=13723325：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=504（consumer）以 parent_event_id=503 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12388，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 505 步** — event_id=504（parent=69），tick=13723325：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=505（consumer）以 parent_event_id=504 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12388，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 506 步** — event_id=505（parent=10），tick=13723325：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=506（consumer）以 parent_event_id=505 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12392，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 507 步** — event_id=506（parent=10），tick=13723325：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=507（consumer）以 parent_event_id=506 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12392，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 508 步** — event_id=507（parent=10），tick=13723325：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=508（consumer）以 parent_event_id=507 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12392，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 509 步** — event_id=508（parent=59），tick=13725250：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=509（consumer）以 parent_event_id=508 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12396，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 510 步** — event_id=509（parent=59），tick=13725250：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=510（consumer）以 parent_event_id=509 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12396，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 511 步** — event_id=510（parent=59），tick=13725250：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=511（consumer）以 parent_event_id=510 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12396，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 512 步** — event_id=511（parent=10），tick=13725250：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=512（consumer）以 parent_event_id=511 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12400，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 513 步** — event_id=512（parent=10），tick=13725250：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=513（consumer）以 parent_event_id=512 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12400，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 514 步** — event_id=513（parent=10），tick=13725250：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=514（consumer）以 parent_event_id=513 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12400，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 515 步** — event_id=514（parent=277），tick=13726020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=515（consumer）以 parent_event_id=514 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12404，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 516 步** — event_id=515（parent=277），tick=13726020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=516（consumer）以 parent_event_id=515 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12404，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 517 步** — event_id=516（parent=277），tick=13726020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=517（consumer）以 parent_event_id=516 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12404，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 518 步** — event_id=517（parent=10），tick=13726020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=518（consumer）以 parent_event_id=517 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12408，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 519 步** — event_id=518（parent=10），tick=13726020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=519（consumer）以 parent_event_id=518 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12408，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 520 步** — event_id=519（parent=10），tick=13726020：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=520（consumer）以 parent_event_id=519 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12408，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 521 步** — event_id=520（parent=102），tick=13810335：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=521（consumer）以 parent_event_id=520 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12412，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 522 步** — event_id=521（parent=102），tick=13810335：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=522（consumer）以 parent_event_id=521 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12412，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 523 步** — event_id=522（parent=102），tick=13810335：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=523（consumer）以 parent_event_id=522 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12412，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 524 步** — event_id=523（parent=10），tick=13810335：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=524（consumer）以 parent_event_id=523 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12416，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 525 步** — event_id=524（parent=10），tick=13810335：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=525（consumer）以 parent_event_id=524 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12416，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 526 步** — event_id=525（parent=10），tick=13810335：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=526（consumer）以 parent_event_id=525 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12416，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 527 步** — event_id=526（parent=64），tick=13811105：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=527（consumer）以 parent_event_id=526 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12420，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 528 步** — event_id=527（parent=64），tick=13811105：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=528（consumer）以 parent_event_id=527 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12420，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 529 步** — event_id=528（parent=64），tick=13811105：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=529（consumer）以 parent_event_id=528 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12420，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 530 步** — event_id=529（parent=10），tick=13811105：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=530（consumer）以 parent_event_id=529 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12424，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 531 步** — event_id=530（parent=10），tick=13811105：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=531（consumer）以 parent_event_id=530 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12424，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 532 步** — event_id=531（parent=10），tick=13811105：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=532（consumer）以 parent_event_id=531 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12424，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 533 步** — event_id=532（parent=170），tick=13811875：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=533（consumer）以 parent_event_id=532 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12428，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 534 步** — event_id=533（parent=170），tick=13811875：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=534（consumer）以 parent_event_id=533 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12428，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 535 步** — event_id=534（parent=170），tick=13811875：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=535（consumer）以 parent_event_id=534 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12428，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 536 步** — event_id=535（parent=10），tick=13811875：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=536（consumer）以 parent_event_id=535 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12432，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 537 步** — event_id=536（parent=10），tick=13811875：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=537（consumer）以 parent_event_id=536 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12432，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 538 步** — event_id=537（parent=10），tick=13811875：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=538（consumer）以 parent_event_id=537 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12432，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 539 步** — event_id=538（parent=114），tick=13812645：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=539（consumer）以 parent_event_id=538 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12436，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 540 步** — event_id=539（parent=114），tick=13812645：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=540（consumer）以 parent_event_id=539 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12436，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 541 步** — event_id=540（parent=114），tick=13812645：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=541（consumer）以 parent_event_id=540 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12436，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 542 步** — event_id=541（parent=10），tick=13812645：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=542（consumer）以 parent_event_id=541 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12440，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 543 步** — event_id=542（parent=10），tick=13812645：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=543（consumer）以 parent_event_id=542 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12440，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 544 步** — event_id=543（parent=10），tick=13812645：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=544（consumer）以 parent_event_id=543 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12440，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 545 步** — event_id=544（parent=179），tick=13813415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=545（consumer）以 parent_event_id=544 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12444，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 546 步** — event_id=545（parent=179），tick=13813415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=546（consumer）以 parent_event_id=545 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12444，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 547 步** — event_id=546（parent=179），tick=13813415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=547（consumer）以 parent_event_id=546 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12444，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 548 步** — event_id=547（parent=10），tick=13813415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=548（consumer）以 parent_event_id=547 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12448，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 549 步** — event_id=548（parent=10），tick=13813415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=549（consumer）以 parent_event_id=548 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12448，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 550 步** — event_id=549（parent=10），tick=13813415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=550（consumer）以 parent_event_id=549 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12448，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 551 步** — event_id=550（parent=112），tick=13814185：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=551（consumer）以 parent_event_id=550 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12452，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 552 步** — event_id=551（parent=112），tick=13814185：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=552（consumer）以 parent_event_id=551 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12452，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 553 步** — event_id=552（parent=112），tick=13814185：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=553（consumer）以 parent_event_id=552 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12452，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 554 步** — event_id=553（parent=10），tick=13814185：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=554（consumer）以 parent_event_id=553 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12456，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 555 步** — event_id=554（parent=10），tick=13814185：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=555（consumer）以 parent_event_id=554 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12456，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 556 步** — event_id=555（parent=10），tick=13814185：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=556（consumer）以 parent_event_id=555 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12456，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 557 步** — event_id=556（parent=35），tick=13823040：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=557（consumer）以 parent_event_id=556 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12460，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 558 步** — event_id=557（parent=35），tick=13823040：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=558（consumer）以 parent_event_id=557 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12460，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 559 步** — event_id=558（parent=35），tick=13823040：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=559（consumer）以 parent_event_id=558 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12460，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 560 步** — event_id=559（parent=10），tick=13823040：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=560（consumer）以 parent_event_id=559 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12464，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 561 步** — event_id=560（parent=10），tick=13823040：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=561（consumer）以 parent_event_id=560 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12464，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 562 步** — event_id=561（parent=10），tick=13823040：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=562（consumer）以 parent_event_id=561 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12464，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 563 步** — event_id=562（parent=201），tick=13823810：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=563（consumer）以 parent_event_id=562 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12468，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 564 步** — event_id=563（parent=201），tick=13823810：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=564（consumer）以 parent_event_id=563 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12468，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 565 步** — event_id=564（parent=201），tick=13823810：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=565（consumer）以 parent_event_id=564 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12468，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 566 步** — event_id=565（parent=10），tick=13823810：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=566（consumer）以 parent_event_id=565 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12472，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 567 步** — event_id=566（parent=10），tick=13823810：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=567（consumer）以 parent_event_id=566 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12472，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 568 步** — event_id=567（parent=10），tick=13823810：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=568（consumer）以 parent_event_id=567 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12472，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 569 步** — event_id=568（parent=212），tick=13825350：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=569（consumer）以 parent_event_id=568 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12476，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 570 步** — event_id=569（parent=212），tick=13825350：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=570（consumer）以 parent_event_id=569 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12476，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 571 步** — event_id=570（parent=212），tick=13825350：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=571（consumer）以 parent_event_id=570 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12476，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 572 步** — event_id=571（parent=10），tick=13825350：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=572（consumer）以 parent_event_id=571 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12480，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 573 步** — event_id=572（parent=10），tick=13825350：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=573（consumer）以 parent_event_id=572 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12480，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 574 步** — event_id=573（parent=10），tick=13825350：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=574（consumer）以 parent_event_id=573 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12480，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 575 步** — event_id=574（parent=42），tick=13826120：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=575（consumer）以 parent_event_id=574 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12484，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 576 步** — event_id=575（parent=42），tick=13826120：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=576（consumer）以 parent_event_id=575 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12484，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 577 步** — event_id=576（parent=42），tick=13826120：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=577（consumer）以 parent_event_id=576 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12484，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 578 步** — event_id=577（parent=10），tick=13826120：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=578（consumer）以 parent_event_id=577 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12488，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 579 步** — event_id=578（parent=10），tick=13826120：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=579（consumer）以 parent_event_id=578 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12488，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 580 步** — event_id=579（parent=10），tick=13826120：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=580（consumer）以 parent_event_id=579 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12488，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 581 步** — event_id=580（parent=228），tick=13827660：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=581（consumer）以 parent_event_id=580 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12492，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 582 步** — event_id=581（parent=228），tick=13827660：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=582（consumer）以 parent_event_id=581 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12492，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 583 步** — event_id=582（parent=228），tick=13827660：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=583（consumer）以 parent_event_id=582 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12492，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 584 步** — event_id=583（parent=10），tick=13827660：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=584（consumer）以 parent_event_id=583 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12496，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 585 步** — event_id=584（parent=10），tick=13827660：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=585（consumer）以 parent_event_id=584 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12496，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 586 步** — event_id=585（parent=10），tick=13827660：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=586（consumer）以 parent_event_id=585 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12496，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 587 步** — event_id=586（parent=63），tick=13828430：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=587（consumer）以 parent_event_id=586 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12500，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 588 步** — event_id=587（parent=63），tick=13828430：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=588（consumer）以 parent_event_id=587 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12500，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 589 步** — event_id=588（parent=63），tick=13828430：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=589（consumer）以 parent_event_id=588 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12500，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 590 步** — event_id=589（parent=10），tick=13828430：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=590（consumer）以 parent_event_id=589 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12504，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 591 步** — event_id=590（parent=10），tick=13828430：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=591（consumer）以 parent_event_id=590 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12504，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 592 步** — event_id=591（parent=10），tick=13828430：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=592（consumer）以 parent_event_id=591 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12504，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 593 步** — event_id=592（parent=125），tick=13834975：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=593（consumer）以 parent_event_id=592 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12508，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 594 步** — event_id=593（parent=125），tick=13834975：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=594（consumer）以 parent_event_id=593 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12508，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 595 步** — event_id=594（parent=125），tick=13834975：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=595（consumer）以 parent_event_id=594 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12508，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 596 步** — event_id=595（parent=10），tick=13834975：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=596（consumer）以 parent_event_id=595 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12512，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 597 步** — event_id=596（parent=10），tick=13834975：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=597（consumer）以 parent_event_id=596 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12512，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 598 步** — event_id=597（parent=10），tick=13834975：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=598（consumer）以 parent_event_id=597 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12512，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 599 步** — event_id=598（parent=48），tick=13835745：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=599（consumer）以 parent_event_id=598 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12516，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 600 步** — event_id=599（parent=48），tick=13835745：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=600（consumer）以 parent_event_id=599 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12516，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 601 步** — event_id=600（parent=48），tick=13835745：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=601（consumer）以 parent_event_id=600 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12516，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 602 步** — event_id=601（parent=10），tick=13835745：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=602（consumer）以 parent_event_id=601 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12520，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 603 步** — event_id=602（parent=10），tick=13835745：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=603（consumer）以 parent_event_id=602 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12520，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 604 步** — event_id=603（parent=10），tick=13835745：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=604（consumer）以 parent_event_id=603 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12520，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 605 步** — event_id=604（parent=145），tick=13838055：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=605（consumer）以 parent_event_id=604 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12524，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 606 步** — event_id=605（parent=145），tick=13838055：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=606（consumer）以 parent_event_id=605 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12524，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 607 步** — event_id=606（parent=145），tick=13838055：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=607（consumer）以 parent_event_id=606 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12524，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 608 步** — event_id=607（parent=10），tick=13838055：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=608（consumer）以 parent_event_id=607 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12528，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 609 步** — event_id=608（parent=10），tick=13838055：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=609（consumer）以 parent_event_id=608 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12528，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 610 步** — event_id=609（parent=10），tick=13838055：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=610（consumer）以 parent_event_id=609 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12528，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 611 步** — event_id=610（parent=69），tick=13838825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=611（consumer）以 parent_event_id=610 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12532，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 612 步** — event_id=611（parent=69），tick=13838825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=612（consumer）以 parent_event_id=611 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12532，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 613 步** — event_id=612（parent=69），tick=13838825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=613（consumer）以 parent_event_id=612 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12532，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 614 步** — event_id=613（parent=10），tick=13838825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=614（consumer）以 parent_event_id=613 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12536，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 615 步** — event_id=614（parent=10），tick=13838825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=615（consumer）以 parent_event_id=614 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12536，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 616 步** — event_id=615（parent=10），tick=13838825：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=616（consumer）以 parent_event_id=615 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12536，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 617 步** — event_id=616（parent=59），tick=13840365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=617（consumer）以 parent_event_id=616 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12540，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 618 步** — event_id=617（parent=59），tick=13840365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=618（consumer）以 parent_event_id=617 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12540，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 619 步** — event_id=618（parent=59），tick=13840365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=619（consumer）以 parent_event_id=618 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12540，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 620 步** — event_id=619（parent=10），tick=13840365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=620（consumer）以 parent_event_id=619 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12544，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 621 步** — event_id=620（parent=10），tick=13840365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=621（consumer）以 parent_event_id=620 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12544，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 622 步** — event_id=621（parent=10），tick=13840365：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=622（consumer）以 parent_event_id=621 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12544，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 623 步** — event_id=622（parent=277），tick=13841135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=623（consumer）以 parent_event_id=622 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12548，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 624 步** — event_id=623（parent=277），tick=13841135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=624（consumer）以 parent_event_id=623 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12548，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 625 步** — event_id=624（parent=277），tick=13841135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=625（consumer）以 parent_event_id=624 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12548，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 626 步** — event_id=625（parent=10），tick=13841135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=626（consumer）以 parent_event_id=625 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12552，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 627 步** — event_id=626（parent=10），tick=13841135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=627（consumer）以 parent_event_id=626 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12552，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 628 步** — event_id=627（parent=10），tick=13841135：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=628（consumer）以 parent_event_id=627 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12552，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 629 步** — event_id=628（parent=102），tick=13845755：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=629（consumer）以 parent_event_id=628 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12556，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 630 步** — event_id=629（parent=102），tick=13845755：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=630（consumer）以 parent_event_id=629 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12556，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 631 步** — event_id=630（parent=102），tick=13845755：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=631（consumer）以 parent_event_id=630 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12556，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 632 步** — event_id=631（parent=10），tick=13845755：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=632（consumer）以 parent_event_id=631 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12560，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 633 步** — event_id=632（parent=10），tick=13845755：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=633（consumer）以 parent_event_id=632 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12560，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 634 步** — event_id=633（parent=10），tick=13845755：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=634（consumer）以 parent_event_id=633 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12560，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 635 步** — event_id=634（parent=64），tick=13846525：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=635（consumer）以 parent_event_id=634 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12564，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 636 步** — event_id=635（parent=63），tick=13967415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=636（consumer）以 parent_event_id=635 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12644，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 637 步** — event_id=636（parent=63），tick=13967415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=637（consumer）以 parent_event_id=636 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12644，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 638 步** — event_id=637（parent=10），tick=13967415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=638（consumer）以 parent_event_id=637 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12648，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 639 步** — event_id=638（parent=10），tick=13967415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=639（consumer）以 parent_event_id=638 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12648，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 640 步** — event_id=639（parent=10），tick=13967415：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=640（consumer）以 parent_event_id=639 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12648，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 641 步** — event_id=640（parent=125），tick=13968955：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=641（consumer）以 parent_event_id=640 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12652，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 642 步** — event_id=641（parent=125），tick=13968955：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=642（consumer）以 parent_event_id=641 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12652，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 643 步** — event_id=642（parent=125），tick=13968955：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=643（consumer）以 parent_event_id=642 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12652，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 644 步** — event_id=643（parent=10），tick=13968955：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=644（consumer）以 parent_event_id=643 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12656，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 645 步** — event_id=644（parent=10），tick=13968955：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=645（consumer）以 parent_event_id=644 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12656，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 646 步** — event_id=645（parent=10），tick=13968955：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=646（consumer）以 parent_event_id=645 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12656，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 647 步** — event_id=646（parent=48），tick=13969725：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=647（consumer）以 parent_event_id=646 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12660，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 648 步** — event_id=647（parent=48），tick=13969725：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=648（consumer）以 parent_event_id=647 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12660，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 649 步** — event_id=648（parent=48），tick=13969725：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=649（consumer）以 parent_event_id=648 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12660，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 650 步** — event_id=649（parent=10），tick=13969725：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=650（consumer）以 parent_event_id=649 承接本事件，共享 fault_id=1 与 dyn_inst_seq=12664，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 651 步** — event_id=650（parent=448），tick=32256840：L4 下游消费者事件，corr=taint_prop；证明污染值被后续指令实际读取/消费。 下一步：event_id=651（chain_end）以 parent_event_id=650 承接本事件，共享 fault_id=1 与 dyn_inst_seq=105122，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 652 步** — event_id=651（parent=650），tick=37833180：生命周期标记 corr=none，outcome=run_end。它只表示仿真结束，**不是** L5 证据，也从不参与终局判定。 本事件是该 fault 在本 seed 事件流中的最后一条。

## 5. 关键事件表

| 顺序 | event_id | parent_event_id | tick | kind | layer | request_id | corr | 地址/值变化 | 状态变化 | 传播作用 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 12868240 | inj | L0 | 11143 | origin | va=48fb70 | — | L0 故障注入 |
| 2 | 1 | 0 | 12868240 | sq_entry | L1 | 11143 | seq_primary | va=48fb70 | — | L1 生产 store 的 SQ 表项（转发源） |
| 3 | 2 | 1 | 12868240 | lsq_fwd | L2 | 11143 | seq_primary | store_data→fwd_corrupt:bit_flip | — | L2 store→load 转发决策/传输 |
| 4 | 3 | 2 | 12868240 | resp | L3 | 11143 | seq_primary | va=48fb70 | — | L3 数据响应 |
| 5 | 4 | 3 | 12868240 | taint_reg | L4 | 11143 | seq_primary | clean→tainted | — | L4 污点进入寄存器 |
| 6 | 5 | 4 | 12869010 | sq_writeback | L3 | — | seq_primary | — | —→packet_built | L3 store 回写 |
| 7 | 6 | 5 | 12869395 | errant_commit | L5 | — | taint_prop | — | contained=0 | L5 错误提交（逃逸） |
| 8 | 7 | — | 12869780 | resp | L3 | 11141 | seq_primary | va=75b70 | — | L3 数据响应 |
| 9 | 8 | 7 | 12869780 | taint_reg | L4 | 11141 | seq_primary | clean→tainted | — | L4 污点进入寄存器 |
| 10 | 9 | 6 | 12869780 | sq_complete | L3 | — | seq_primary | va=48fb70 | —→completed | L3 store 完成 |
| 11 | 10 | 4 | 12869780 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 12 | 11 | 10 | 12870165 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 13 | 12 | 10 | 12870165 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 14 | 13 | 10 | 12870165 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 15 | 14 | 10 | 12870165 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 16 | 15 | 10 | 12870550 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 17 | 16 | 10 | 12870550 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 18 | 17 | 10 | 12870550 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 19 | 18 | 14 | 12922910 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 20 | 19 | 14 | 12924835 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 21 | 20 | 10 | 12924835 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 22 | 21 | 10 | 12924835 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 23 | 22 | 10 | 12924835 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 24 | 23 | 14 | 12924835 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 25 | 24 | 23 | 12926375 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 26 | 25 | 19 | 12926760 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 27 | 26 | 24 | 12926760 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 28 | 27 | 26 | 12927145 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 29 | 28 | 26 | 12927145 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 30 | 29 | 26 | 12927145 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 31 | 30 | 14 | 12927145 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 32 | 31 | 23 | 12979505 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 33 | 32 | 10 | 12979505 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 34 | 33 | 10 | 12979505 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 35 | 34 | 10 | 12979505 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 36 | 35 | 31 | 12985280 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 37 | 36 | 25 | 12985665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 38 | 37 | 35 | 12985665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 39 | 38 | 37 | 12986050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 40 | 39 | 37 | 12986050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 41 | 40 | 37 | 12986050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 42 | 41 | 30 | 12986050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 43 | 42 | 31 | 12986050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 44 | 43 | 10 | 12986050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 45 | 44 | 10 | 12986050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 46 | 45 | 10 | 12986050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 47 | 46 | 42 | 12991055 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 48 | 47 | 36 | 12991440 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 49 | 48 | 46 | 12991440 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 50 | 49 | 48 | 12991825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 51 | 50 | 48 | 12991825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 52 | 51 | 48 | 12991825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 53 | 52 | 41 | 12991825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 54 | 53 | 42 | 12991825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 55 | 54 | 10 | 12991825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 56 | 55 | 10 | 12991825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 57 | 56 | 10 | 12991825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 58 | 57 | 53 | 13050345 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 59 | 58 | 47 | 13050730 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 60 | 59 | 57 | 13050730 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 61 | 60 | 59 | 13051115 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 62 | 61 | 59 | 13051115 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 63 | 62 | 59 | 13051115 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 64 | 63 | 52 | 13051115 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 65 | 64 | 53 | 13051115 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 66 | 65 | 10 | 13051115 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 67 | 66 | 10 | 13051115 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 68 | 67 | 10 | 13051115 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 69 | 68 | 64 | 13051115 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 70 | 69 | 58 | 13051500 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 71 | 70 | 68 | 13051500 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 72 | 71 | 70 | 13051885 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 73 | 72 | 70 | 13051885 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 74 | 73 | 70 | 13051885 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 75 | 74 | 63 | 13051885 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 76 | 75 | 64 | 13051885 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 77 | 76 | 10 | 13051885 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 78 | 77 | 10 | 13051885 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 79 | 78 | 10 | 13051885 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 80 | 79 | 75 | 13061895 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 81 | 80 | 69 | 13062280 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 82 | 81 | 79 | 13062280 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 83 | 82 | 81 | 13062665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 84 | 83 | 81 | 13062665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 85 | 84 | 81 | 13062665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 86 | 85 | 74 | 13062665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 87 | 86 | 75 | 13062665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 88 | 87 | 10 | 13062665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 89 | 88 | 10 | 13062665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 90 | 89 | 10 | 13062665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 91 | 90 | 86 | 13062665 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 92 | 91 | 80 | 13063050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 93 | 92 | 90 | 13063050 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 94 | 93 | 92 | 13063435 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 95 | 94 | 92 | 13063435 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 96 | 95 | 92 | 13063435 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 97 | 96 | 85 | 13063435 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 98 | 97 | 86 | 13063435 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 99 | 98 | 10 | 13063435 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 100 | 99 | 10 | 13063435 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 101 | 100 | 10 | 13063435 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 102 | 101 | 97 | 13115025 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 103 | 102 | 91 | 13115410 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 104 | 103 | 101 | 13115410 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 105 | 104 | 103 | 13115795 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 106 | 105 | 103 | 13115795 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 107 | 106 | 103 | 13115795 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 108 | 107 | 96 | 13115795 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 109 | 108 | 97 | 13115795 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 110 | 109 | 10 | 13115795 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 111 | 110 | 10 | 13115795 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 112 | 111 | 10 | 13115795 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 113 | 112 | 108 | 13115795 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 114 | 113 | 102 | 13116180 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 115 | 114 | 112 | 13116180 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 116 | 115 | 114 | 13116565 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 117 | 116 | 114 | 13116565 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 118 | 117 | 114 | 13116565 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 119 | 118 | 107 | 13116565 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 120 | 119 | 108 | 13116565 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 121 | 120 | 10 | 13116565 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 122 | 121 | 10 | 13116565 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 123 | 122 | 10 | 13116565 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 124 | 123 | 119 | 13201650 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 125 | 124 | 113 | 13202035 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 126 | 125 | 123 | 13202035 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 127 | 126 | 125 | 13202420 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 128 | 127 | 125 | 13202420 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 129 | 128 | 125 | 13202420 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 130 | 129 | 118 | 13202420 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 131 | 130 | 119 | 13202420 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 132 | 131 | 10 | 13202420 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 133 | 132 | 10 | 13202420 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 134 | 133 | 10 | 13202420 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 135 | 134 | 124 | 13202805 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 136 | 135 | 48 | 13203190 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 137 | 136 | 48 | 13203190 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 138 | 137 | 48 | 13203190 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 139 | 138 | 129 | 13203190 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 140 | 139 | 130 | 13203190 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 141 | 140 | 10 | 13203190 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 142 | 141 | 10 | 13203190 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 143 | 142 | 10 | 13203190 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 144 | 143 | 139 | 13205885 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 145 | 144 | 134 | 13206270 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 146 | 145 | 143 | 13206270 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 147 | 146 | 145 | 13206655 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 148 | 147 | 145 | 13206655 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 149 | 148 | 145 | 13206655 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 150 | 149 | 138 | 13206655 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 151 | 150 | 139 | 13206655 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 152 | 151 | 10 | 13206655 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 153 | 152 | 10 | 13206655 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 154 | 153 | 10 | 13206655 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 155 | 154 | 59 | 13208195 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 156 | 155 | 59 | 13208195 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 157 | 156 | 59 | 13208195 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 158 | 157 | 149 | 13208195 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 159 | 158 | 10 | 13208195 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 160 | 159 | 10 | 13208195 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 161 | 160 | 10 | 13208195 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 162 | 161 | 74 | 13266715 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 163 | 162 | 161 | 13267100 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 164 | 163 | 162 | 13267485 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 165 | 164 | 162 | 13267485 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 166 | 165 | 162 | 13267485 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 167 | 166 | 74 | 13267485 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 168 | 167 | 10 | 13267485 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 169 | 168 | 10 | 13267485 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 170 | 169 | 10 | 13267485 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 171 | 170 | 64 | 13267870 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 172 | 171 | 90 | 13268255 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 173 | 172 | 90 | 13268255 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 174 | 173 | 90 | 13268255 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 175 | 174 | 68 | 13268255 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 176 | 175 | 10 | 13268255 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 177 | 176 | 10 | 13268255 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 178 | 177 | 10 | 13268255 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 179 | 178 | 86 | 13313685 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 180 | 179 | 178 | 13314070 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 181 | 180 | 179 | 13314455 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 182 | 181 | 179 | 13314455 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 183 | 182 | 179 | 13314455 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 184 | 183 | 10 | 13314455 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 185 | 184 | 10 | 13314455 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 186 | 185 | 10 | 13314455 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 187 | 186 | 112 | 13315225 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 188 | 187 | 112 | 13315225 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 189 | 188 | 112 | 13315225 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 190 | 189 | 10 | 13315225 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 191 | 190 | 10 | 13315225 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 192 | 191 | 10 | 13315225 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 193 | 192 | 35 | 13315995 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 194 | 193 | 35 | 13315995 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 195 | 194 | 35 | 13315995 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 196 | 195 | 108 | 13315995 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 197 | 196 | 10 | 13315995 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 198 | 197 | 10 | 13315995 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 199 | 198 | 10 | 13315995 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 200 | 199 | 195 | 13315995 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 201 | 200 | 113 | 13316380 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 202 | 201 | 199 | 13316380 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 203 | 202 | 201 | 13316765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 204 | 203 | 201 | 13316765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 205 | 204 | 201 | 13316765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 206 | 205 | 118 | 13316765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 207 | 206 | 195 | 13316765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 208 | 207 | 10 | 13316765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 209 | 208 | 10 | 13316765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 210 | 209 | 10 | 13316765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 211 | 210 | 206 | 13324080 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 212 | 211 | 200 | 13324465 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 213 | 212 | 210 | 13324465 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 214 | 213 | 212 | 13324850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 215 | 214 | 212 | 13324850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 216 | 215 | 212 | 13324850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 217 | 216 | 10 | 13324850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 218 | 217 | 10 | 13324850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 219 | 218 | 10 | 13324850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 220 | 219 | 30 | 13324850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 221 | 220 | 42 | 13325620 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 222 | 221 | 42 | 13325620 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 223 | 222 | 42 | 13325620 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 224 | 223 | 10 | 13325620 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 225 | 224 | 10 | 13325620 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 226 | 225 | 10 | 13325620 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 227 | 226 | 46 | 13328315 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 228 | 227 | 24 | 13328700 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 229 | 228 | 226 | 13328700 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 230 | 229 | 228 | 13329085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 231 | 230 | 228 | 13329085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 232 | 231 | 228 | 13329085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 233 | 232 | 46 | 13329085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 234 | 233 | 10 | 13329085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 235 | 234 | 10 | 13329085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 236 | 235 | 10 | 13329085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 237 | 236 | 227 | 13329470 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 238 | 237 | 63 | 13329855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 239 | 238 | 63 | 13329855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 240 | 239 | 63 | 13329855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 241 | 240 | 52 | 13329855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 242 | 241 | 10 | 13329855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 243 | 242 | 10 | 13329855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 244 | 243 | 10 | 13329855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 245 | 244 | 125 | 13331010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 246 | 245 | 125 | 13331010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 247 | 246 | 125 | 13331010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 248 | 247 | 10 | 13331010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 249 | 248 | 10 | 13331010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 250 | 249 | 10 | 13331010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 251 | 250 | 48 | 13331780 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 252 | 251 | 48 | 13331780 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 253 | 252 | 48 | 13331780 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 254 | 253 | 10 | 13331780 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 255 | 254 | 10 | 13331780 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 256 | 255 | 10 | 13331780 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 257 | 256 | 145 | 13336400 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 258 | 257 | 145 | 13336400 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 259 | 258 | 145 | 13336400 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 260 | 259 | 149 | 13336400 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 261 | 260 | 10 | 13336400 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 262 | 261 | 10 | 13336400 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 263 | 262 | 10 | 13336400 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 264 | 263 | 139 | 13336785 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 265 | 264 | 69 | 13337170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 266 | 265 | 69 | 13337170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 267 | 266 | 69 | 13337170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 268 | 267 | 143 | 13337170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 269 | 268 | 10 | 13337170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 270 | 269 | 10 | 13337170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 271 | 270 | 10 | 13337170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 272 | 271 | 59 | 13341020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 273 | 272 | 59 | 13341020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 274 | 273 | 59 | 13341020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 275 | 274 | 10 | 13341020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 276 | 275 | 10 | 13341020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 277 | 276 | 10 | 13341020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 278 | 277 | 79 | 13341405 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 279 | 278 | 277 | 13341790 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 280 | 279 | 277 | 13341790 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 281 | 280 | 277 | 13341790 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 282 | 281 | 75 | 13341790 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 283 | 282 | 10 | 13341790 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 284 | 283 | 10 | 13341790 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 285 | 284 | 10 | 13341790 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 286 | 285 | 85 | 13343715 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 287 | 286 | 102 | 13344100 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 288 | 287 | 102 | 13344100 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 289 | 288 | 102 | 13344100 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 290 | 289 | 80 | 13344100 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 291 | 290 | 10 | 13344100 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 292 | 291 | 10 | 13344100 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 293 | 292 | 10 | 13344100 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 294 | 293 | 64 | 13344870 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 295 | 294 | 64 | 13344870 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 296 | 295 | 64 | 13344870 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 297 | 296 | 10 | 13344870 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 298 | 297 | 10 | 13344870 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 299 | 298 | 10 | 13344870 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 300 | 299 | 170 | 13347950 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 301 | 300 | 170 | 13347950 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 302 | 301 | 170 | 13347950 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 303 | 302 | 10 | 13347950 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 304 | 303 | 10 | 13347950 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 305 | 304 | 10 | 13347950 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 306 | 305 | 114 | 13348720 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 307 | 306 | 114 | 13348720 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 308 | 307 | 114 | 13348720 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 309 | 308 | 10 | 13348720 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 310 | 309 | 10 | 13348720 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 311 | 310 | 10 | 13348720 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 312 | 311 | 179 | 13401080 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 313 | 312 | 179 | 13401080 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 314 | 313 | 179 | 13401080 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 315 | 314 | 10 | 13401080 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 316 | 315 | 10 | 13401080 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 317 | 316 | 10 | 13401080 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 318 | 317 | 112 | 13401850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 319 | 318 | 112 | 13401850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 320 | 319 | 112 | 13401850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 321 | 320 | 10 | 13401850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 322 | 321 | 10 | 13401850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 323 | 322 | 10 | 13401850 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 324 | 323 | 35 | 13406085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 325 | 324 | 35 | 13406085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 326 | 325 | 35 | 13406085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 327 | 326 | 10 | 13406085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 328 | 327 | 10 | 13406085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 329 | 328 | 10 | 13406085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 330 | 329 | 201 | 13406855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 331 | 330 | 201 | 13406855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 332 | 331 | 201 | 13406855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 333 | 332 | 10 | 13406855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 334 | 333 | 10 | 13406855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 335 | 334 | 10 | 13406855 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 336 | 335 | 212 | 13411090 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 337 | 336 | 212 | 13411090 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 338 | 337 | 212 | 13411090 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 339 | 338 | 10 | 13411090 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 340 | 339 | 10 | 13411090 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 341 | 340 | 10 | 13411090 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 342 | 341 | 42 | 13411860 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 343 | 342 | 42 | 13411860 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 344 | 343 | 42 | 13411860 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 345 | 344 | 10 | 13411860 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 346 | 345 | 10 | 13411860 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 347 | 346 | 10 | 13411860 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 348 | 347 | 228 | 13530825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 349 | 348 | 228 | 13530825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 350 | 349 | 228 | 13530825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 351 | 350 | 10 | 13530825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 352 | 351 | 10 | 13530825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 353 | 352 | 10 | 13530825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 354 | 353 | 63 | 13531595 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 355 | 354 | 63 | 13531595 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 356 | 355 | 63 | 13531595 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 357 | 356 | 10 | 13531595 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 358 | 357 | 10 | 13531595 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 359 | 358 | 10 | 13531595 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 360 | 359 | 125 | 13532365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 361 | 360 | 125 | 13532365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 362 | 361 | 125 | 13532365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 363 | 362 | 10 | 13532365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 364 | 363 | 10 | 13532365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 365 | 364 | 10 | 13532365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 366 | 365 | 48 | 13533135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 367 | 366 | 48 | 13533135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 368 | 367 | 48 | 13533135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 369 | 368 | 10 | 13533135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 370 | 369 | 10 | 13533135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 371 | 370 | 10 | 13533135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 372 | 371 | 145 | 13533905 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 373 | 372 | 145 | 13533905 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 374 | 373 | 145 | 13533905 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 375 | 374 | 10 | 13533905 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 376 | 375 | 10 | 13533905 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 377 | 376 | 10 | 13533905 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 378 | 377 | 69 | 13534675 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 379 | 378 | 69 | 13534675 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 380 | 379 | 69 | 13534675 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 381 | 380 | 10 | 13534675 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 382 | 381 | 10 | 13534675 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 383 | 382 | 10 | 13534675 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 384 | 383 | 59 | 13543530 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 385 | 384 | 59 | 13543530 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 386 | 385 | 59 | 13543530 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 387 | 386 | 10 | 13543530 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 388 | 387 | 10 | 13543530 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 389 | 388 | 10 | 13543530 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 390 | 389 | 277 | 13544300 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 391 | 390 | 277 | 13544300 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 392 | 391 | 277 | 13544300 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 393 | 392 | 10 | 13544300 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 394 | 393 | 10 | 13544300 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 395 | 394 | 10 | 13544300 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 396 | 395 | 102 | 13545840 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 397 | 396 | 102 | 13545840 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 398 | 397 | 102 | 13545840 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 399 | 398 | 10 | 13545840 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 400 | 399 | 10 | 13545840 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 401 | 400 | 10 | 13545840 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 402 | 401 | 64 | 13546610 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 403 | 402 | 64 | 13546610 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 404 | 403 | 64 | 13546610 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 405 | 404 | 10 | 13546610 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 406 | 405 | 10 | 13546610 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 407 | 406 | 10 | 13546610 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 408 | 407 | 170 | 13547765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 409 | 408 | 170 | 13547765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 410 | 409 | 170 | 13547765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 411 | 410 | 10 | 13547765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 412 | 411 | 10 | 13547765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 413 | 412 | 10 | 13547765 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 414 | 413 | 114 | 13548535 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 415 | 414 | 114 | 13548535 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 416 | 415 | 10 | 13548535 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 417 | 416 | 10 | 13548535 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 418 | 417 | 10 | 13548535 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 419 | 418 | 179 | 13555465 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 420 | 419 | 179 | 13555465 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 421 | 420 | 179 | 13555465 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 422 | 421 | 10 | 13555465 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 423 | 422 | 10 | 13555465 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 424 | 423 | 10 | 13555465 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 425 | 424 | 112 | 13556235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 426 | 425 | 112 | 13556235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 427 | 426 | 112 | 13556235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 428 | 427 | 10 | 13556235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 429 | 428 | 10 | 13556235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 430 | 429 | 35 | 13558545 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 431 | 430 | 35 | 13558545 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 432 | 431 | 35 | 13558545 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 433 | 432 | 10 | 13558545 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 434 | 433 | 201 | 13559315 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 435 | 434 | 212 | 13560470 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 436 | 435 | 212 | 13560470 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 437 | 436 | 10 | 13560470 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 438 | 437 | 10 | 13560470 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 439 | 438 | 42 | 13561240 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 440 | 439 | 228 | 13567400 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 441 | 440 | 10 | 13567400 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 442 | 441 | 63 | 13568170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 443 | 442 | 63 | 13568170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 444 | 443 | 63 | 13568170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 445 | 444 | 10 | 13568170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 446 | 445 | 10 | 13568170 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 447 | 446 | 125 | 13570480 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 448 | 447 | 10 | 13570480 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 449 | 448 | 48 | 13571250 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 450 | 449 | 145 | 13685595 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 451 | 450 | 69 | 13686365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 452 | 451 | 59 | 13687135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 453 | 452 | 10 | 13687135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 454 | 453 | 10 | 13687135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 455 | 454 | 114 | 13699070 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 456 | 455 | 10 | 13699070 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 457 | 456 | 179 | 13700610 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 458 | 457 | 112 | 13701380 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 459 | 458 | 112 | 13701380 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 460 | 459 | 112 | 13701380 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 461 | 460 | 10 | 13701380 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 462 | 461 | 10 | 13701380 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 463 | 462 | 35 | 13702535 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 464 | 463 | 10 | 13702535 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 465 | 464 | 10 | 13702535 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 466 | 465 | 10 | 13703305 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 467 | 466 | 10 | 13703305 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 468 | 467 | 212 | 13710235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 469 | 468 | 212 | 13710235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 470 | 469 | 10 | 13710235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 471 | 470 | 10 | 13710235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 472 | 471 | 10 | 13710235 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 473 | 472 | 10 | 13711005 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 474 | 473 | 10 | 13711005 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 475 | 474 | 228 | 13713315 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 476 | 475 | 228 | 13713315 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 477 | 476 | 10 | 13713315 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 478 | 477 | 10 | 13713315 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 479 | 478 | 63 | 13714085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 480 | 479 | 63 | 13714085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 481 | 480 | 63 | 13714085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 482 | 481 | 10 | 13714085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 483 | 482 | 10 | 13714085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 484 | 483 | 10 | 13714085 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 485 | 484 | 125 | 13715240 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 486 | 485 | 125 | 13715240 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 487 | 486 | 125 | 13715240 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 488 | 487 | 10 | 13715240 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 489 | 488 | 10 | 13715240 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 490 | 489 | 10 | 13715240 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 491 | 490 | 48 | 13716010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 492 | 491 | 48 | 13716010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 493 | 492 | 48 | 13716010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 494 | 493 | 10 | 13716010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 495 | 494 | 10 | 13716010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 496 | 495 | 10 | 13716010 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 497 | 496 | 145 | 13722555 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 498 | 497 | 145 | 13722555 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 499 | 498 | 145 | 13722555 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 500 | 499 | 10 | 13722555 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 501 | 500 | 10 | 13722555 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 502 | 501 | 10 | 13722555 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 503 | 502 | 69 | 13723325 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 504 | 503 | 69 | 13723325 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 505 | 504 | 69 | 13723325 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 506 | 505 | 10 | 13723325 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 507 | 506 | 10 | 13723325 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 508 | 507 | 10 | 13723325 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 509 | 508 | 59 | 13725250 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 510 | 509 | 59 | 13725250 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 511 | 510 | 59 | 13725250 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 512 | 511 | 10 | 13725250 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 513 | 512 | 10 | 13725250 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 514 | 513 | 10 | 13725250 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 515 | 514 | 277 | 13726020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 516 | 515 | 277 | 13726020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 517 | 516 | 277 | 13726020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 518 | 517 | 10 | 13726020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 519 | 518 | 10 | 13726020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 520 | 519 | 10 | 13726020 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 521 | 520 | 102 | 13810335 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 522 | 521 | 102 | 13810335 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 523 | 522 | 102 | 13810335 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 524 | 523 | 10 | 13810335 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 525 | 524 | 10 | 13810335 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 526 | 525 | 10 | 13810335 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 527 | 526 | 64 | 13811105 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 528 | 527 | 64 | 13811105 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 529 | 528 | 64 | 13811105 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 530 | 529 | 10 | 13811105 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 531 | 530 | 10 | 13811105 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 532 | 531 | 10 | 13811105 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 533 | 532 | 170 | 13811875 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 534 | 533 | 170 | 13811875 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 535 | 534 | 170 | 13811875 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 536 | 535 | 10 | 13811875 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 537 | 536 | 10 | 13811875 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 538 | 537 | 10 | 13811875 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 539 | 538 | 114 | 13812645 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 540 | 539 | 114 | 13812645 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 541 | 540 | 114 | 13812645 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 542 | 541 | 10 | 13812645 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 543 | 542 | 10 | 13812645 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 544 | 543 | 10 | 13812645 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 545 | 544 | 179 | 13813415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 546 | 545 | 179 | 13813415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 547 | 546 | 179 | 13813415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 548 | 547 | 10 | 13813415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 549 | 548 | 10 | 13813415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 550 | 549 | 10 | 13813415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 551 | 550 | 112 | 13814185 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 552 | 551 | 112 | 13814185 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 553 | 552 | 112 | 13814185 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 554 | 553 | 10 | 13814185 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 555 | 554 | 10 | 13814185 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 556 | 555 | 10 | 13814185 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 557 | 556 | 35 | 13823040 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 558 | 557 | 35 | 13823040 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 559 | 558 | 35 | 13823040 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 560 | 559 | 10 | 13823040 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 561 | 560 | 10 | 13823040 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 562 | 561 | 10 | 13823040 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 563 | 562 | 201 | 13823810 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 564 | 563 | 201 | 13823810 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 565 | 564 | 201 | 13823810 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 566 | 565 | 10 | 13823810 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 567 | 566 | 10 | 13823810 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 568 | 567 | 10 | 13823810 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 569 | 568 | 212 | 13825350 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 570 | 569 | 212 | 13825350 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 571 | 570 | 212 | 13825350 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 572 | 571 | 10 | 13825350 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 573 | 572 | 10 | 13825350 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 574 | 573 | 10 | 13825350 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 575 | 574 | 42 | 13826120 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 576 | 575 | 42 | 13826120 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 577 | 576 | 42 | 13826120 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 578 | 577 | 10 | 13826120 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 579 | 578 | 10 | 13826120 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 580 | 579 | 10 | 13826120 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 581 | 580 | 228 | 13827660 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 582 | 581 | 228 | 13827660 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 583 | 582 | 228 | 13827660 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 584 | 583 | 10 | 13827660 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 585 | 584 | 10 | 13827660 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 586 | 585 | 10 | 13827660 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 587 | 586 | 63 | 13828430 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 588 | 587 | 63 | 13828430 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 589 | 588 | 63 | 13828430 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 590 | 589 | 10 | 13828430 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 591 | 590 | 10 | 13828430 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 592 | 591 | 10 | 13828430 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 593 | 592 | 125 | 13834975 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 594 | 593 | 125 | 13834975 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 595 | 594 | 125 | 13834975 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 596 | 595 | 10 | 13834975 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 597 | 596 | 10 | 13834975 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 598 | 597 | 10 | 13834975 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 599 | 598 | 48 | 13835745 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 600 | 599 | 48 | 13835745 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 601 | 600 | 48 | 13835745 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 602 | 601 | 10 | 13835745 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 603 | 602 | 10 | 13835745 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 604 | 603 | 10 | 13835745 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 605 | 604 | 145 | 13838055 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 606 | 605 | 145 | 13838055 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 607 | 606 | 145 | 13838055 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 608 | 607 | 10 | 13838055 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 609 | 608 | 10 | 13838055 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 610 | 609 | 10 | 13838055 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 611 | 610 | 69 | 13838825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 612 | 611 | 69 | 13838825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 613 | 612 | 69 | 13838825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 614 | 613 | 10 | 13838825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 615 | 614 | 10 | 13838825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 616 | 615 | 10 | 13838825 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 617 | 616 | 59 | 13840365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 618 | 617 | 59 | 13840365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 619 | 618 | 59 | 13840365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 620 | 619 | 10 | 13840365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 621 | 620 | 10 | 13840365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 622 | 621 | 10 | 13840365 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 623 | 622 | 277 | 13841135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 624 | 623 | 277 | 13841135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 625 | 624 | 277 | 13841135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 626 | 625 | 10 | 13841135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 627 | 626 | 10 | 13841135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 628 | 627 | 10 | 13841135 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 629 | 628 | 102 | 13845755 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 630 | 629 | 102 | 13845755 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 631 | 630 | 102 | 13845755 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 632 | 631 | 10 | 13845755 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 633 | 632 | 10 | 13845755 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 634 | 633 | 10 | 13845755 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 635 | 634 | 64 | 13846525 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 636 | 635 | 63 | 13967415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 637 | 636 | 63 | 13967415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 638 | 637 | 10 | 13967415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 639 | 638 | 10 | 13967415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 640 | 639 | 10 | 13967415 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 641 | 640 | 125 | 13968955 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 642 | 641 | 125 | 13968955 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 643 | 642 | 125 | 13968955 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 644 | 643 | 10 | 13968955 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 645 | 644 | 10 | 13968955 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 646 | 645 | 10 | 13968955 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 647 | 646 | 48 | 13969725 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 648 | 647 | 48 | 13969725 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 649 | 648 | 48 | 13969725 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 650 | 649 | 10 | 13969725 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 651 | 650 | 448 | 32256840 | consumer | L4 | — | taint_prop | — | — | L4 下游消费者 |
| 652 | 651 | 650 | 37833180 | chain_end | L5 | — | none | — | contained=1 | 生命周期结束标记（非 L5 证据） |

## 6. 原始证据与哈希

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/S02-F0-W5/seed2/prop_evt.txt.gz` | `74adbae3d65ecd25850f234c17684758b45e4376eb46b74b4fc2606a7aab691a` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/S02-F0-W5/chain_report.json` | `1a490645774079f9c1c2634d5fb0822fb03912299bb37acf3f506b6ca60f3408` |
| cell_results | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/S02-F0-W5/cell_results.json` | `0484910129b31cce930404001972e777300be967c58ed0f602e5d07ee6e8c5ac` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/S02-F0-W5/seed2/stats.txt` | `455463601e919e2d24690f3713d1856cbfe5ec7454ce35099c10b80da40418bf` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/S02-F0-W5/seed2/run.out` | `803c7668d2b3834f67fcf86194ea96856bf90c394f7d152507875c0b38a87d41` |
| injections.log | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/S02-F0-W5/seed2/lsq_fwd_injections.log` | `3c6c7bbeccbc3242c4dbb0c4dae961eaa5b4116cfb420ded24e4423f41d70349` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2/manifest.json` | `deb012cf2fc798af888f18ce293af597c9a93e2dbb12ab1c81e9979fd2091863` |

事件流字节数：40678（gzip 后）；解压后事件行数：652；本 fault 事件数：652。

## 7. 可复现命令

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S02-F0-W5_s2 --cells S02-F0-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --timeout 300
```

环境身份：binary SHA-256 `686458c34ab7199a07ec4a968c3bbfe40e0d7514cccc2ee0d181a68621b7cef9`，binary_source_head `5b550954+dirty:d55db8d6b7bb78fb35addf191a45b3d6bb7b19b9006770aa4c1c9beb7ac2b876`，analysis_tool_head `5b550954207d6ce1e4deb56a6f221357e8a8314f`，matrix SHA-256 `8f2d6227ca76202fa9b5cb2e5ee5489d83a68643b2b987be7e04ac1d8d515fce`。

## 8. 诚实边界

- 本 doc 只证明该 seed 自己的事件流：已证明的层边为 L0->L1, L1->L2, L2->L3, L3->L4, L4->L5；缺失的层边为 （无）。
- 终局 `full` 与 `provable_to=L5` 直接取自该 seed 的 `chain_report.json`，未做任何推断升级。
- 三方计数：注入日志 `FUNNEL`/`CHAOS_L0_FUNNEL` 与 `run.out` 的 `CHAOS_LSU_TRIGGER` 全部来自本 seed；`stats.txt` 不含 `numFaultsInjected` 统计（addrpath 家族不发射该计数器），故该路为 **n/a**，不以 0 冒充。
- `chain_end` 只是生命周期标记（corr=none），从不作为 L5 证据；本 doc 未把 `chain_end` 当作终局。
- 后续层为 N/A 的含义：本 seed 未在当前事件流中产生该层的真实事件，文档不会补造，也不会据此推断 Masked。
- 本 seed 未重跑；原始事件流未被修改；三个 seed 的数值各自独立，不存在跨 seed 复制。
