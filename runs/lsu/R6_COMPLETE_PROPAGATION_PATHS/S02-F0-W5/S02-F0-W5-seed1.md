# S02-F0-W5 seed1 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S02-F0-W5`；seed：`1`
- oracle：`Masked`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`40`；terminal：`detected_contained`；provable_to：`L5`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1`

## 2. 注入位置、地址、原值/新值与掩码

```
Cycle: 34093, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: bit_flip, Vaddr: 0x7ffffefd10, FwdSize: 8, ByteOffset: 5, Mask: 10000001, StoreSeq: 11234, SqIdx: 856, LoadSeq: 11245, LqIdx: 677
```
- 注入事件：`event_id=0`，tick=`13125805`，va=`7ffffefd10`，field=`lsqfwd_forward`，before=``，after=``，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=6 eligible=6 injected=1 first_eligible_tick=556325 last_eligible_tick=14949935 fires=n/a no_effect=n/a (activated=W3-L0-layer)`
- 检测摘要：`CHAOS_DETECT: layer=Hardware RAS contained=1 tick=19190325 ptag=1 reason=store_discarded_not_retired`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | inj | L0 | — | 13125805 | origin | lsqfwd_forward | — | — | — | — | — |
| 1 | sq_entry | L1 | 0 | 13125805 | seq_primary | store_entry | — | — | — | — | — |
| 2 | lsq_fwd | L2 | 1 | 13125805 | seq_primary | bit_flip | store_data | fwd_corrupt:bit_flip | — | — | — |
| 3 | resp | L3 | 2 | 13125805 | seq_primary | bit_flip | — | — | — | — | — |
| 4 | taint_reg | L4 | 3 | 13125805 | seq_primary | — | clean | tainted | — | — | — |
| 5 | sq_writeback | L3 | 4 | 13125805 | seq_primary | — | — | — | —→packet_built | — | — |
| 6 | resp | L3 | — | 13126575 | seq_primary | — | — | — | — | — | — |
| 7 | taint_reg | L4 | 6 | 13126575 | seq_primary | — | clean | tainted | — | — | — |
| 8 | sq_complete | L3 | 5 | 13126575 | seq_primary | — | — | — | —→completed | — | — |
| 9 | squash_discarded | L4 | 8 | 13128115 | seq_primary | load | — | — | load_queue_uncommitted→— | 1 | contained |
| 10 | lsq_push | L1 | 9 | 13252855 | addr_fallback | load | — | — | — | — | — |
| 11 | mem_req | L2 | — | 13252855 | addr_fallback | — | — | — | — | — | — |
| 12 | lsq_sendfrag | L2 | 11 | 13252855 | addr_fallback | load | — | — | — | — | — |
| 13 | tlb_translate | L2 | 12 | 13252855 | addr_fallback | — | — | — | — | — | — |
| 14 | lsq_push | L1 | 10 | 13664420 | addr_fallback | store | — | — | — | — | — |
| 15 | mem_req | L2 | — | 13664420 | addr_fallback | — | — | — | — | — | — |
| 16 | lsq_sendfrag | L2 | 15 | 13664420 | addr_fallback | store | — | — | — | — | — |
| 17 | tlb_translate | L2 | 16 | 13664420 | addr_fallback | — | — | — | — | — | — |
| 18 | lsq_push | L1 | 14 | 14025165 | addr_fallback | load | — | — | — | — | — |
| 19 | mem_req | L2 | — | 14025165 | addr_fallback | — | — | — | — | — | — |
| 20 | lsq_sendfrag | L2 | 19 | 14025165 | addr_fallback | load | — | — | — | — | — |
| 21 | tlb_translate | L2 | 20 | 14025165 | addr_fallback | — | — | — | — | — | — |
| 22 | lsq_push | L1 | 18 | 14298130 | addr_fallback | store | — | — | — | — | — |
| 23 | mem_req | L2 | — | 14298130 | addr_fallback | — | — | — | — | — | — |
| 24 | lsq_sendfrag | L2 | 23 | 14298130 | addr_fallback | store | — | — | — | — | — |
| 25 | tlb_translate | L2 | 24 | 14298130 | addr_fallback | — | — | — | — | — | — |
| 26 | lsq_push | L1 | 22 | 14518350 | addr_fallback | load | — | — | — | — | — |
| 27 | mem_req | L2 | — | 14518350 | addr_fallback | — | — | — | — | — | — |
| 28 | lsq_sendfrag | L2 | 27 | 14518350 | addr_fallback | load | — | — | — | — | — |
| 29 | tlb_translate | L2 | 28 | 14518350 | addr_fallback | — | — | — | — | — | — |
| 30 | lsq_push | L1 | 26 | 14542220 | addr_fallback | load | — | — | — | — | — |
| 31 | mem_req | L2 | — | 14542220 | addr_fallback | — | — | — | — | — | — |
| 32 | lsq_sendfrag | L2 | 31 | 14542220 | addr_fallback | load | — | — | — | — | — |
| 33 | tlb_translate | L2 | 32 | 14542220 | addr_fallback | — | — | — | — | — | — |
| 34 | lsq_push | L1 | 30 | 14894880 | addr_fallback | store | — | — | — | — | — |
| 35 | mem_req | L2 | — | 14894880 | addr_fallback | — | — | — | — | — | — |
| 36 | lsq_sendfrag | L2 | 35 | 14894880 | addr_fallback | store | — | — | — | — | — |
| 37 | tlb_translate | L2 | 36 | 14894880 | addr_fallback | — | — | — | — | — | — |
| 38 | store_not_retired | L4 | 7 | 19190325 | taint_prop | — | — | — | response_seen_commit_absent→— | 1 | contained |
| 39 | chain_end | L4 | 34 | 19190325 | none | — | — | — | — | 1 | detected_contained |

## 4. 逐步传播语义

- **event 0 · inj（L0 故障注入）**：tick=13125805，parent=（根），corr=origin，field=lsqfwd_forward，before=，after=，state=→，contained=，outcome=。
- **event 1 · sq_entry（L1 生产 store 的 SQ 表项（转发源））**：tick=13125805，parent=0，corr=seq_primary，field=store_entry，before=，after=，state=→，contained=，outcome=。
- **event 2 · lsq_fwd（L2 store→load 转发决策/传输）**：tick=13125805，parent=1，corr=seq_primary，field=bit_flip，before=store_data，after=fwd_corrupt:bit_flip，state=→，contained=，outcome=。
- **event 3 · resp（L3 数据响应）**：tick=13125805，parent=2，corr=seq_primary，field=bit_flip，before=，after=，state=→，contained=，outcome=。
- **event 4 · taint_reg（L4 污点进入目的寄存器）**：tick=13125805，parent=3，corr=seq_primary，field=，before=clean，after=tainted，state=→，contained=，outcome=。
- **event 5 · sq_writeback（家族事件）**：tick=13125805，parent=4，corr=seq_primary，field=，before=，after=，state=→packet_built，contained=，outcome=。
- **event 6 · resp（L3 数据响应）**：tick=13126575，parent=（根），corr=seq_primary，field=，before=，after=，state=→，contained=，outcome=。
- **event 7 · taint_reg（L4 污点进入目的寄存器）**：tick=13126575，parent=6，corr=seq_primary，field=，before=clean，after=tainted，state=→，contained=，outcome=。
- **event 8 · sq_complete（L3 store 完成）**：tick=13126575，parent=5，corr=seq_primary，field=，before=，after=，state=→completed，contained=，outcome=。
- **event 9 · squash_discarded（L4 检测并 squash 丢弃）**：tick=13128115，parent=8，corr=seq_primary，field=load，before=，after=，state=load_queue_uncommitted→，contained=1，outcome=contained。
- **event 10 · lsq_push（家族事件）**：tick=13252855，parent=9，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 11 · mem_req（L2 请求创建）**：tick=13252855，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 12 · lsq_sendfrag（家族事件）**：tick=13252855，parent=11，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 13 · tlb_translate（家族事件）**：tick=13252855，parent=12，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 14 · lsq_push（家族事件）**：tick=13664420，parent=10，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 15 · mem_req（L2 请求创建）**：tick=13664420，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 16 · lsq_sendfrag（家族事件）**：tick=13664420，parent=15，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 17 · tlb_translate（家族事件）**：tick=13664420，parent=16，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 18 · lsq_push（家族事件）**：tick=14025165，parent=14，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 19 · mem_req（L2 请求创建）**：tick=14025165，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 20 · lsq_sendfrag（家族事件）**：tick=14025165，parent=19，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 21 · tlb_translate（家族事件）**：tick=14025165，parent=20，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 22 · lsq_push（家族事件）**：tick=14298130，parent=18，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 23 · mem_req（L2 请求创建）**：tick=14298130，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 24 · lsq_sendfrag（家族事件）**：tick=14298130，parent=23，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 25 · tlb_translate（家族事件）**：tick=14298130，parent=24，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 26 · lsq_push（家族事件）**：tick=14518350，parent=22，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 27 · mem_req（L2 请求创建）**：tick=14518350，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 28 · lsq_sendfrag（家族事件）**：tick=14518350，parent=27，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 29 · tlb_translate（家族事件）**：tick=14518350，parent=28，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 30 · lsq_push（家族事件）**：tick=14542220，parent=26，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 31 · mem_req（L2 请求创建）**：tick=14542220，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 32 · lsq_sendfrag（家族事件）**：tick=14542220，parent=31，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 33 · tlb_translate（家族事件）**：tick=14542220，parent=32，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 34 · lsq_push（家族事件）**：tick=14894880，parent=30，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 35 · mem_req（L2 请求创建）**：tick=14894880，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 36 · lsq_sendfrag（家族事件）**：tick=14894880，parent=35，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 37 · tlb_translate（家族事件）**：tick=14894880，parent=36，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 38 · store_not_retired（家族事件）**：tick=19190325，parent=7，corr=taint_prop，field=，before=，after=，state=response_seen_commit_absent→，contained=1，outcome=contained。
- **event 39 · chain_end（生命周期结束标记（非 L5 证据））**：tick=19190325，parent=34，corr=none，field=，before=，after=，state=→，contained=1，outcome=detected_contained。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`detected_contained`，provable_to=`L5`，admitted=`True`，certified=`True`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`detected_contained`，provable_to=`L5`，beyond=``，event_count=`40`
- containment：layer=`L4`，later_layers_N/A=`['L5']`，reason=`S02-F0-W5 fault 1 显式含住：kind=squash_discarded field='load' detection_layer=L4 outcome=contained`
- containment metrics：`{'L4': {'kind': 'squash_discarded', 'field': 'load', 'outcome': 'contained', 'contained': '1', 'event_id': '9', 'tick': '13128115'}}`
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_DETECT: layer=Hardware RAS contained=1 tick=19190325 ptag=1 reason=store_discarded_not_retired`
- guest checksum：`1f4cbf14327717df`
- stats：
- `simTicks                                     19190325                       # Number of ticks simulated (Tick)`
- `simInsts                                         6152                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles            49846                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1/S02-F0-W5/seed1/prop_evt.txt.gz`：`9c317ab4b29e90312c8b60929990a7f955bf65eab226f1cb67d7dfe4c2721a29`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1/S02-F0-W5/chain_report.json`：`d3c2180aeed5dd448f18a6f6b40aa10f05bdd00f56f5259eeaf10c67ccc635f1`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1/S02-F0-W5/seed1/chain_report.json`：`27d08949fdbc89c4bc58de022da3ce66f3cb9a402e184a6fab038a0fa7c87595`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1/S02-F0-W5/seed1/stats.txt`：`9b4aac0c0bb947d3cf3fbcc69903412a33f2473787c75c82a64987ace8773a47`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1/S02-F0-W5/seed1/run.out`：`06591be0e80975885d045d66fb224599f4490a4f16dca402c4e0398df691b680`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1/manifest.json`：`4905f2e33c8a32ba5dcae852479e3ded878cf578f0102b8a77f99dc345bb51f5`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1/S02-F0-W5/seed1/lsq_fwd_injections.log`：`16a6374304574b1b69ebb0d9faf8843bb66d077e7681e195d7f8d0f95414b74d`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1 --cells S02-F0-W5 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s1/S02-F0-W5/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/sq_forward --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 --lsqfwd_span_events 6 --lsq_struct_mode byte_flip --bits_to_change 2 --rng_seed 1 --chaos_propagation --prop_run_id S02-F0-W5 --prop_sample_run_id s1`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。

