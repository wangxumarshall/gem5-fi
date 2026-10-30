# S13-F0-W1 seed1 — 完整传播路径（真实事件时间顺序）

> 本文只转录该 seed 自己的原始事件流（`prop_evt.txt.gz`）与权威 `chain_report.json`；未修改事件流，未跨 seed 复用任何数值，未把推测写成事件事实。

## 1. 样本身份

| 项 | 值 |
|---|---|
| RunID | `S13-F0-W1` |
| seed | `1` |
| model | `S13`（Store Queue 单比特翻转） |
| frequency | `F0` |
| workload | `W1`（W1:mibench/bin/w1_all） |
| binary_path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `686458c34ab7199a07ec4a968c3bbfe40e0d7514cccc2ee0d181a68621b7cef9` |
| binary_source_head | `5b550954+dirty:d55db8d6b7bb78fb35addf191a45b3d6bb7b19b9006770aa4c1c9beb7ac2b876` |
| analysis_tool_head | `5b550954207d6ce1e4deb56a6f221357e8a8314f` |
| prop_evt_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/S13-F0-W1/seed1/prop_evt.txt.gz` |
| prop_evt_sha256 | `0944c8db87be47f8a56a45fadec4e960efe922d4de5647eb8e6de73aa462f777` |
| chain_report_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/S13-F0-W1/chain_report.json` |
| chain_report_sha256 | `42f521e1f31a0ed42c6344a5ac025bcd48208cdf3832e467055c472a6a9b04f6` |
| cell_results_path | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/S13-F0-W1/cell_results.json` |
| cell_results_sha256 | `07a66d7a9db631758d446f18c750bb54aff5ba7bf9ed817ecbc30680e8f8e399` |

## 2. 最终判定

| 项 | 值 |
|---|---|
| oracle outcome | `Crash` |
| terminal | `crash_translation_fault` |
| provable_to | `L3` |
| beyond | `—` |
| admitted | `True` |
| certified | `True` |
| violations | `[]` |
| conservation | `n/a` |
| count_contradiction | `False` |
| truncated | `False` |
| 事件总数 | `10` |
| containment_event_id | `—` |

## 3. 真实注入

| 项 | 值 |
|---|---|
| 注入 tick | `5924765` |
| event_id | `1` |
| parent_event_id | `—` |
| 注入部件 | `CHAOSAddrPath` |
| 注入字段 | `none` |
| 原值 | `0x4d2c98` |
| 新值 | `0x20004d2c98` |
| mask | `0xff → 0xff` |
| 地址 | `4d2c98` |
| request_id | `—` |
| corr | `origin` |
| injected/activated 计数 | `FUNNEL: attempted=756 eligible=412 injected=1`；`CHAOS_L0_FUNNEL: CHAOSAddrPath attempted=756 eligible=412 injected=1 activated=1` |

注入日志原文（本 seed 自己的 `addrpath_injections.log`）：

```text
Tick: 5924765, Site: lsq_pushRequest_PRE, mode=s13_store_addr, old_addr=0x4d2c98, new_addr=0x20004d2c98, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

运行期触发/检测原文（本 seed 自己的 `seed1/run.out`）：

```text
CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=756 eligible=412 injected=1 first_eligible_tick=150920 last_eligible_tick=5924765 fires=n/a no_effect=n/a (activated=W3-L0-layer)
（无 CHAOS_DETECT 行）
```

## 4. 传播过程（真实事件时间顺序）

本 seed 的 fault_id=1 链共有 10 条真实事件，事件种类序列为：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → sq_execute → arch_translation_fault → chain_end`。以下按该 seed 事件流的原始顺序逐步说明。

**第 1 步** — event_id=1，tick=5924765：L0 故障注入。CHAOSAddrPath 在 lsq_pushRequest_PRE 站点以 s13_store_addr 模式写入一个故障；注入字段 field=none，地址 `4d2c98` → `20004d2c98`，dyn_inst_seq=3890，corr=origin。该事件无父事件，是整条传播链的根。 下一步：event_id=2（addr_form）以 parent_event_id=1 承接本事件，共享 fault_id=1 与 dyn_inst_seq=3890，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 2 步** — event_id=2（parent=1），tick=5924765：L1 地址形成阶段看到注入后的地址值 `4d2c98` → `20004d2c98`，dyn_inst_seq=3890。注入值在这一步成为第一个被污染的对象（地址计算输入）。 下一步：event_id=3（lsq_push）以 parent_event_id=2 承接本事件，共享 fault_id=1 与 dyn_inst_seq=3890，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 3 步** — event_id=3（parent=2），tick=5924765：L1 入队。该请求被推入 store 队列（opcode=strxi_uop，pc=436378，lq_idx=-1，sq_idx=344，dyn_inst_seq=3890）；污染的地址/状态自此携带在 LSQ 条目中。 下一步：event_id=4（mem_req）以 parent_event_id=3 承接本事件，共享 fault_id=1 与 dyn_inst_seq=3890，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 4 步** — event_id=4（parent=3），tick=5924765：L2 请求创建，request_id=3890，va=`20004d2c98`。request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。 下一步：event_id=5（lsq_sendfrag）以 parent_event_id=4 承接本事件，共享 fault_id=1 与 dyn_inst_seq=3890，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 5 步** — event_id=5（parent=4），tick=5924765：L2 请求分片，request_id=3890，va=`20004d2c98`；同一请求被拆分后仍然保持同一身份。 下一步：event_id=6（tlb_translate）以 parent_event_id=5 承接本事件，共享 fault_id=1 与 dyn_inst_seq=3890，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 6 步** — event_id=6（parent=5），tick=5924765：L2 地址翻译，request_id=3890，va=`20004d2c98`，pa=`—`（该事件未记录 pa 时如实写 —）。 下一步：event_id=7（tlb_fault）以 parent_event_id=6 承接本事件，共享 fault_id=1 与 dyn_inst_seq=3890，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 7 步** — event_id=7（parent=6），tick=5924765：tlb_fault，va=`20004d2c98`，request_id=3890，corr=seq_primary。 下一步：event_id=8（sq_execute）以 parent_event_id=7 承接本事件，共享 fault_id=1 与 dyn_inst_seq=3890，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 8 步** — event_id=8（parent=7），tick=5924765：L3 sq_execute，request_id=—，va=`20004d2c98`，pa=`—`；store 侧继续携带被污染的值。 下一步：event_id=9（arch_translation_fault）以 parent_event_id=8 承接本事件，共享 fault_id=1 与 dyn_inst_seq=3890，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 9 步** — event_id=9（parent=8），tick=5990985：arch_translation_fault，va=`20004d2c98`，request_id=—，corr=seq_primary。 下一步：event_id=10（chain_end）以 parent_event_id=9 承接本事件，共享 fault_id=1，且 tick 不回退，因此该事件是下一步的直接前驱。

**第 10 步** — event_id=10（parent=9），tick=5990985：生命周期标记 corr=none，outcome=run_end。它只表示仿真结束，**不是** L5 证据，也从不参与终局判定。 本事件是该 fault 在本 seed 事件流中的最后一条。

## 5. 关键事件表

| 顺序 | event_id | parent_event_id | tick | kind | layer | request_id | corr | 地址/值变化 | 状态变化 | 传播作用 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | — | 5924765 | inj | L0 | — | origin | 4d2c98→20004d2c98 | — | L0 故障注入 |
| 2 | 2 | 1 | 5924765 | addr_form | L1 | — | origin | 4d2c98→20004d2c98 | — | L1 地址形成 |
| 3 | 3 | 2 | 5924765 | lsq_push | L1 | — | seq_primary | va=20004d2c98 | — | L1 入队（LQ/SQ） |
| 4 | 4 | 3 | 5924765 | mem_req | L2 | 3890 | seq_primary | va=20004d2c98 | — | L2 请求创建 |
| 5 | 5 | 4 | 5924765 | lsq_sendfrag | L2 | 3890 | seq_primary | va=20004d2c98 | — | L2 请求分片 |
| 6 | 6 | 5 | 5924765 | tlb_translate | L2 | 3890 | seq_primary | va=20004d2c98 | — | L2 地址翻译 |
| 7 | 7 | 6 | 5924765 | tlb_fault | Hardware | 3890 | seq_primary | va=20004d2c98 | — | — |
| 8 | 8 | 7 | 5924765 | sq_execute | L3 | — | seq_primary | va=20004d2c98 | issued→— | L3 store 执行 |
| 9 | 9 | 8 | 5990985 | arch_translation_fault | L2 | — | seq_primary | va=20004d2c98 | contained=0 | — |
| 10 | 10 | 9 | 5990985 | chain_end | — | — | none | — | contained=0 | 生命周期结束标记（非 L5 证据） |

## 6. 原始证据与哈希

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/S13-F0-W1/seed1/prop_evt.txt.gz` | `0944c8db87be47f8a56a45fadec4e960efe922d4de5647eb8e6de73aa462f777` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/S13-F0-W1/chain_report.json` | `42f521e1f31a0ed42c6344a5ac025bcd48208cdf3832e467055c472a6a9b04f6` |
| cell_results | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/S13-F0-W1/cell_results.json` | `07a66d7a9db631758d446f18c750bb54aff5ba7bf9ed817ecbc30680e8f8e399` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/S13-F0-W1/seed1/stats.txt` | `4bc75a32f8803b482f0a17f2e236f9ef109b61647e50cb7bfebcec4889e9e5d0` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/S13-F0-W1/seed1/run.out` | `4cf267d0ae3e54fc43b82141a079c0daa025c53eee1d63e1c1b2e1c0a4261d4d` |
| injections.log | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/S13-F0-W1/seed1/addrpath_injections.log` | `febeb6b54d51577cf15af5b5d607f8d4e51a5798b94772a7cd166dfd141d7c94` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1/manifest.json` | `9d8c6581bff27a6f752c38e04737c27a92354a60a26ac4da4e7968b1a5e45f69` |

事件流字节数：1000（gzip 后）；解压后事件行数：10；本 fault 事件数：10。

## 7. 可复现命令

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit_r3/S13-F0-W1_s1 --cells S13-F0-W1 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --timeout 300
```

环境身份：binary SHA-256 `686458c34ab7199a07ec4a968c3bbfe40e0d7514cccc2ee0d181a68621b7cef9`，binary_source_head `5b550954+dirty:d55db8d6b7bb78fb35addf191a45b3d6bb7b19b9006770aa4c1c9beb7ac2b876`，analysis_tool_head `5b550954207d6ce1e4deb56a6f221357e8a8314f`，matrix SHA-256 `8f2d6227ca76202fa9b5cb2e5ee5489d83a68643b2b987be7e04ac1d8d515fce`。

## 8. 诚实边界

- 本 doc 只证明该 seed 自己的事件流：已证明的层边为 L0->L1, L1->L2, L2->L3；缺失的层边为 L3->L4, L4->L5。
- 终局 `crash_translation_fault` 与 `provable_to=L3` 直接取自该 seed 的 `chain_report.json`，未做任何推断升级。
- 三方计数：注入日志 `FUNNEL`/`CHAOS_L0_FUNNEL` 与 `run.out` 的 `CHAOS_LSU_TRIGGER` 全部来自本 seed；`stats.txt` 不含 `numFaultsInjected` 统计（addrpath 家族不发射该计数器），故该路为 **n/a**，不以 0 冒充。
- `chain_end` 只是生命周期标记（corr=none），从不作为 L5 证据；本 doc 未把 `chain_end` 当作终局。
- 本 seed 的终局是严格 `crash_translation_fault`：真实注入 → 连续 L0→L3 ancestry → 真实 `arch_translation_fault`（detection_layer=L2、contained=0、outcome=arch_exception、corr 为链关联值）→ 请求在产生任何内存副作用之前被翻译异常终止。L4/L5 结构性 **N/A**：不是缺失，也不得伪造。
- guest 真实 Crash 的受控证据：该 seed 的 `run.out` 含 `CHAOS_GUEST_SEGV_EXIT: cause=chaos_guest_segv code=139`，gem5 退出码 139（128+SIGSEGV）；admission 走独立的 crash_terminal 路径，与 full/contained 无关。
- 本 seed 未重跑；原始事件流未被修改；三个 seed 的数值各自独立，不存在跨 seed 复制。
