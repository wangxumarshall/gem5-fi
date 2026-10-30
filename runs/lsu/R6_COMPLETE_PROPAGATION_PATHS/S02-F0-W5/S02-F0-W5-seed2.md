# S02-F0-W5 seed2 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S02-F0-W5`；seed：`2`
- oracle：`Masked`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`96`；terminal：`full`；provable_to：`L5`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2`

## 2. 注入位置、地址、原值/新值与掩码

```
Cycle: 21975, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: bit_flip, Vaddr: 0x496798, FwdSize: 8, ByteOffset: 0, Mask: 10010000, StoreSeq: 6012, SqIdx: 566, LoadSeq: 6018, LqIdx: 322
```
- 注入事件：`event_id=0`，tick=`8460375`，va=`496798`，field=`lsqfwd_forward`，before=``，after=``，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=6 eligible=6 injected=1 first_eligible_tick=556325 last_eligible_tick=14944545 fires=n/a no_effect=n/a (activated=W3-L0-layer)`
- 检测摘要：`CHAOS_DETECT: layer=None contained=0 tick=8461530 ptag=1 reason=errant_commit`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | inj | L0 | — | 8460375 | origin | lsqfwd_forward | — | — | — | — | — |
| 1 | sq_entry | L1 | 0 | 8460375 | seq_primary | store_entry | — | — | — | — | — |
| 2 | lsq_fwd | L2 | 1 | 8460375 | seq_primary | bit_flip | store_data | fwd_corrupt:bit_flip | — | — | — |
| 3 | resp | L3 | 2 | 8460375 | seq_primary | bit_flip | — | — | — | — | — |
| 4 | taint_reg | L4 | 3 | 8460375 | seq_primary | — | clean | tainted | — | — | — |
| 5 | sq_writeback | L3 | 4 | 8460760 | seq_primary | — | — | — | —→packet_built | — | — |
| 6 | resp | L3 | — | 8461530 | seq_primary | — | — | — | — | — | — |
| 7 | taint_reg | L4 | 6 | 8461530 | seq_primary | — | clean | tainted | — | — | — |
| 8 | sq_complete | L3 | 5 | 8461530 | seq_primary | — | — | — | —→completed | — | — |
| 9 | errant_commit | L5 | 8 | 8461530 | taint_prop | — | — | — | — | 0 | errant_commit |
| 10 | consumer | L4 | 4 | 8463840 | taint_prop | — | — | — | — | — | — |
| 11 | consumer | L4 | 10 | 8463840 | taint_prop | — | — | — | — | — | — |
| 12 | consumer | L4 | 10 | 8463840 | taint_prop | — | — | — | — | — | — |
| 13 | consumer | L4 | 10 | 8463840 | taint_prop | — | — | — | — | — | — |
| 14 | consumer | L4 | 10 | 8470385 | taint_prop | — | — | — | — | — | — |
| 15 | lsq_push | L1 | 14 | 8505805 | addr_fallback | store | — | — | — | — | — |
| 4294967296 | request_fork | — | 4 | 8505805 | addr_fallback | — | — | — | — | — | — |
| 16 | mem_req | L2 | 4294967296 | 8505805 | addr_fallback | — | — | — | — | — | — |
| 17 | lsq_sendfrag | L2 | 16 | 8505805 | addr_fallback | store | — | — | — | — | — |
| 18 | tlb_translate | L2 | 17 | 8505805 | addr_fallback | — | — | — | — | — | — |
| 19 | consumer | L4 | 14 | 8506575 | taint_prop | — | — | — | — | — | — |
| 20 | consumer | L4 | 19 | 8506575 | taint_prop | — | — | — | — | — | — |
| 21 | consumer | L4 | 19 | 8506575 | taint_prop | — | — | — | — | — | — |
| 22 | consumer | L4 | 19 | 8506575 | taint_prop | — | — | — | — | — | — |
| 23 | consumer | L4 | 19 | 8508500 | taint_prop | — | — | — | — | — | — |
| 24 | consumer | L4 | 23 | 8509270 | taint_prop | — | — | — | — | — | — |
| 25 | consumer | L4 | 24 | 8509655 | taint_prop | — | — | — | — | — | — |
| 26 | consumer | L4 | 25 | 8509655 | taint_prop | — | — | — | — | — | — |
| 27 | consumer | L4 | 25 | 8509655 | taint_prop | — | — | — | — | — | — |
| 28 | consumer | L4 | 25 | 8509655 | taint_prop | — | — | — | — | — | — |
| 29 | consumer | L4 | 23 | 8529290 | taint_prop | — | — | — | — | — | — |
| 30 | consumer | L4 | 29 | 8652105 | taint_prop | — | — | — | — | — | — |
| 31 | consumer | L4 | 29 | 8652105 | taint_prop | — | — | — | — | — | — |
| 32 | consumer | L4 | 29 | 8652105 | taint_prop | — | — | — | — | — | — |
| 33 | consumer | L4 | 29 | 8655955 | taint_prop | — | — | — | — | — | — |
| 34 | consumer | L4 | 29 | 8655955 | taint_prop | — | — | — | — | — | — |
| 35 | consumer | L4 | 29 | 8655955 | taint_prop | — | — | — | — | — | — |
| 36 | consumer | L4 | 29 | 8701385 | taint_prop | — | — | — | — | — | — |
| 37 | consumer | L4 | 29 | 8701385 | taint_prop | — | — | — | — | — | — |
| 38 | consumer | L4 | 29 | 8701385 | taint_prop | — | — | — | — | — | — |
| 39 | consumer | L4 | 29 | 8710240 | taint_prop | — | — | — | — | — | — |
| 40 | consumer | L4 | 39 | 8710625 | taint_prop | — | — | — | — | — | — |
| 41 | consumer | L4 | 40 | 8713320 | taint_prop | — | — | — | — | — | — |
| 42 | consumer | L4 | 41 | 8713320 | taint_prop | — | — | — | — | — | — |
| 43 | consumer | L4 | 29 | 8713320 | taint_prop | — | — | — | — | — | — |
| 44 | consumer | L4 | 43 | 8713320 | taint_prop | — | — | — | — | — | — |
| 45 | consumer | L4 | 41 | 8767220 | taint_prop | — | — | — | — | — | — |
| 46 | consumer | L4 | 44 | 8767220 | taint_prop | — | — | — | — | — | — |
| 47 | consumer | L4 | 46 | 8767220 | taint_prop | — | — | — | — | — | — |
| 48 | lsq_push | L1 | 47 | 8770300 | addr_fallback | load | — | — | — | — | — |
| 4294967297 | request_fork | — | 4 | 8770300 | addr_fallback | — | — | — | — | — | — |
| 49 | mem_req | L2 | 4294967297 | 8770300 | addr_fallback | — | — | — | — | — | — |
| 50 | lsq_sendfrag | L2 | 49 | 8770300 | addr_fallback | load | — | — | — | — | — |
| 51 | tlb_translate | L2 | 50 | 8770300 | addr_fallback | — | — | — | — | — | — |
| 52 | consumer | L4 | 29 | 8770685 | taint_prop | — | — | — | — | — | — |
| 53 | consumer | L4 | 47 | 8771455 | taint_prop | — | — | — | — | — | — |
| 54 | consumer | L4 | 53 | 8772610 | taint_prop | — | — | — | — | — | — |
| 55 | consumer | L4 | 54 | 8772610 | taint_prop | — | — | — | — | — | — |
| 56 | consumer | L4 | 54 | 8772610 | taint_prop | — | — | — | — | — | — |
| 57 | consumer | L4 | 54 | 8772610 | taint_prop | — | — | — | — | — | — |
| 58 | consumer | L4 | 54 | 8772610 | taint_prop | — | — | — | — | — | — |
| 59 | consumer | L4 | 54 | 8772610 | taint_prop | — | — | — | — | — | — |
| 60 | consumer | L4 | 54 | 8772610 | taint_prop | — | — | — | — | — | — |
| 61 | consumer | L4 | 54 | 8777230 | taint_prop | — | — | — | — | — | — |
| 62 | lsq_push | L1 | 61 | 8789550 | addr_fallback | store | — | — | — | — | — |
| 4294967298 | request_fork | — | 4 | 8789550 | addr_fallback | — | — | — | — | — | — |
| 63 | mem_req | L2 | 4294967298 | 8789550 | addr_fallback | — | — | — | — | — | — |
| 64 | lsq_sendfrag | L2 | 63 | 8789550 | addr_fallback | store | — | — | — | — | — |
| 65 | tlb_translate | L2 | 64 | 8789550 | addr_fallback | — | — | — | — | — | — |
| 66 | consumer | L4 | 23 | 8790320 | taint_prop | — | — | — | — | — | — |
| 67 | consumer | L4 | 66 | 8790320 | taint_prop | — | — | — | — | — | — |
| 68 | consumer | L4 | 66 | 8790320 | taint_prop | — | — | — | — | — | — |
| 69 | consumer | L4 | 66 | 8790320 | taint_prop | — | — | — | — | — | — |
| 70 | consumer | L4 | 23 | 8793015 | taint_prop | — | — | — | — | — | — |
| 71 | consumer | L4 | 24 | 8794555 | taint_prop | — | — | — | — | — | — |
| 72 | consumer | L4 | 24 | 8794555 | taint_prop | — | — | — | — | — | — |
| 73 | consumer | L4 | 47 | 8796095 | taint_prop | — | — | — | — | — | — |
| 74 | consumer | L4 | 47 | 8796095 | taint_prop | — | — | — | — | — | — |
| 75 | consumer | L4 | 23 | 8892345 | taint_prop | — | — | — | — | — | — |
| 76 | consumer | L4 | 23 | 8892345 | taint_prop | — | — | — | — | — | — |
| 77 | consumer | L4 | 72 | 8894270 | taint_prop | — | — | — | — | — | — |
| 78 | consumer | L4 | 77 | 8894655 | taint_prop | — | — | — | — | — | — |
| 79 | consumer | L4 | 47 | 8895040 | taint_prop | — | — | — | — | — | — |
| 80 | consumer | L4 | 79 | 8985130 | taint_prop | — | — | — | — | — | — |
| 81 | consumer | L4 | 79 | 8985130 | taint_prop | — | — | — | — | — | — |
| 82 | consumer | L4 | 79 | 8985130 | taint_prop | — | — | — | — | — | — |
| 83 | consumer | L4 | 75 | 9038260 | taint_prop | — | — | — | — | — | — |
| 84 | consumer | L4 | 83 | 9038645 | taint_prop | — | — | — | — | — | — |
| 85 | consumer | L4 | 84 | 9039030 | taint_prop | — | — | — | — | — | — |
| 86 | consumer | L4 | 84 | 9039030 | taint_prop | — | — | — | — | — | — |
| 87 | consumer | L4 | 84 | 9039030 | taint_prop | — | — | — | — | — | — |
| 88 | consumer | L4 | 84 | 9039800 | taint_prop | — | — | — | — | — | — |
| 89 | consumer | L4 | 75 | 9041725 | taint_prop | — | — | — | — | — | — |
| 90 | consumer | L4 | 88 | 9094855 | taint_prop | — | — | — | — | — | — |
| 91 | consumer | L4 | 75 | 9099090 | taint_prop | — | — | — | — | — | — |
| 92 | chain_end | L5 | 91 | 19190325 | none | — | — | — | — | 1 | errant_commit_seen |

## 4. 逐步传播语义

- **event 0 · inj（L0 故障注入）**：tick=8460375，parent=（根），corr=origin，field=lsqfwd_forward，before=，after=，state=→，contained=，outcome=。
- **event 1 · sq_entry（L1 生产 store 的 SQ 表项（转发源））**：tick=8460375，parent=0，corr=seq_primary，field=store_entry，before=，after=，state=→，contained=，outcome=。
- **event 2 · lsq_fwd（L2 store→load 转发决策/传输）**：tick=8460375，parent=1，corr=seq_primary，field=bit_flip，before=store_data，after=fwd_corrupt:bit_flip，state=→，contained=，outcome=。
- **event 3 · resp（L3 数据响应）**：tick=8460375，parent=2，corr=seq_primary，field=bit_flip，before=，after=，state=→，contained=，outcome=。
- **event 4 · taint_reg（L4 污点进入目的寄存器）**：tick=8460375，parent=3，corr=seq_primary，field=，before=clean，after=tainted，state=→，contained=，outcome=。
- **event 5 · sq_writeback（家族事件）**：tick=8460760，parent=4，corr=seq_primary，field=，before=，after=，state=→packet_built，contained=，outcome=。
- **event 6 · resp（L3 数据响应）**：tick=8461530，parent=（根），corr=seq_primary，field=，before=，after=，state=→，contained=，outcome=。
- **event 7 · taint_reg（L4 污点进入目的寄存器）**：tick=8461530，parent=6，corr=seq_primary，field=，before=clean，after=tainted，state=→，contained=，outcome=。
- **event 8 · sq_complete（L3 store 完成）**：tick=8461530，parent=5，corr=seq_primary，field=，before=，after=，state=→completed，contained=，outcome=。
- **event 9 · errant_commit（L5 错误提交（逃逸））**：tick=8461530，parent=8，corr=taint_prop，field=，before=，after=，state=→，contained=0，outcome=errant_commit。
- **event 10 · consumer（L4 下游消费者）**：tick=8463840，parent=4，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 11 · consumer（L4 下游消费者）**：tick=8463840，parent=10，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 12 · consumer（L4 下游消费者）**：tick=8463840，parent=10，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 13 · consumer（L4 下游消费者）**：tick=8463840，parent=10，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 14 · consumer（L4 下游消费者）**：tick=8470385，parent=10，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 15 · lsq_push（家族事件）**：tick=8505805，parent=14，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967296 · request_fork（家族事件）**：tick=8505805，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 16 · mem_req（L2 请求创建）**：tick=8505805，parent=4294967296，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 17 · lsq_sendfrag（家族事件）**：tick=8505805，parent=16，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 18 · tlb_translate（家族事件）**：tick=8505805，parent=17，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 19 · consumer（L4 下游消费者）**：tick=8506575，parent=14，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 20 · consumer（L4 下游消费者）**：tick=8506575，parent=19，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 21 · consumer（L4 下游消费者）**：tick=8506575，parent=19，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 22 · consumer（L4 下游消费者）**：tick=8506575，parent=19，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 23 · consumer（L4 下游消费者）**：tick=8508500，parent=19，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 24 · consumer（L4 下游消费者）**：tick=8509270，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 25 · consumer（L4 下游消费者）**：tick=8509655，parent=24，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 26 · consumer（L4 下游消费者）**：tick=8509655，parent=25，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 27 · consumer（L4 下游消费者）**：tick=8509655，parent=25，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 28 · consumer（L4 下游消费者）**：tick=8509655，parent=25，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 29 · consumer（L4 下游消费者）**：tick=8529290，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 30 · consumer（L4 下游消费者）**：tick=8652105，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 31 · consumer（L4 下游消费者）**：tick=8652105，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 32 · consumer（L4 下游消费者）**：tick=8652105，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 33 · consumer（L4 下游消费者）**：tick=8655955，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 34 · consumer（L4 下游消费者）**：tick=8655955，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 35 · consumer（L4 下游消费者）**：tick=8655955，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 36 · consumer（L4 下游消费者）**：tick=8701385，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 37 · consumer（L4 下游消费者）**：tick=8701385，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 38 · consumer（L4 下游消费者）**：tick=8701385，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 39 · consumer（L4 下游消费者）**：tick=8710240，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 40 · consumer（L4 下游消费者）**：tick=8710625，parent=39，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 41 · consumer（L4 下游消费者）**：tick=8713320，parent=40，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 42 · consumer（L4 下游消费者）**：tick=8713320，parent=41，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 43 · consumer（L4 下游消费者）**：tick=8713320，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 44 · consumer（L4 下游消费者）**：tick=8713320，parent=43，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 45 · consumer（L4 下游消费者）**：tick=8767220，parent=41，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 46 · consumer（L4 下游消费者）**：tick=8767220，parent=44，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 47 · consumer（L4 下游消费者）**：tick=8767220，parent=46，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 48 · lsq_push（家族事件）**：tick=8770300，parent=47，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 4294967297 · request_fork（家族事件）**：tick=8770300，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 49 · mem_req（L2 请求创建）**：tick=8770300，parent=4294967297，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 50 · lsq_sendfrag（家族事件）**：tick=8770300，parent=49，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 51 · tlb_translate（家族事件）**：tick=8770300，parent=50，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 52 · consumer（L4 下游消费者）**：tick=8770685，parent=29，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 53 · consumer（L4 下游消费者）**：tick=8771455，parent=47，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 54 · consumer（L4 下游消费者）**：tick=8772610，parent=53，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 55 · consumer（L4 下游消费者）**：tick=8772610，parent=54，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 56 · consumer（L4 下游消费者）**：tick=8772610，parent=54，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 57 · consumer（L4 下游消费者）**：tick=8772610，parent=54，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 58 · consumer（L4 下游消费者）**：tick=8772610，parent=54，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 59 · consumer（L4 下游消费者）**：tick=8772610，parent=54，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 60 · consumer（L4 下游消费者）**：tick=8772610，parent=54，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 61 · consumer（L4 下游消费者）**：tick=8777230，parent=54，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 62 · lsq_push（家族事件）**：tick=8789550，parent=61，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967298 · request_fork（家族事件）**：tick=8789550，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 63 · mem_req（L2 请求创建）**：tick=8789550，parent=4294967298，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 64 · lsq_sendfrag（家族事件）**：tick=8789550，parent=63，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 65 · tlb_translate（家族事件）**：tick=8789550，parent=64，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 66 · consumer（L4 下游消费者）**：tick=8790320，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 67 · consumer（L4 下游消费者）**：tick=8790320，parent=66，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 68 · consumer（L4 下游消费者）**：tick=8790320，parent=66，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 69 · consumer（L4 下游消费者）**：tick=8790320，parent=66，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 70 · consumer（L4 下游消费者）**：tick=8793015，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 71 · consumer（L4 下游消费者）**：tick=8794555，parent=24，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 72 · consumer（L4 下游消费者）**：tick=8794555，parent=24，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 73 · consumer（L4 下游消费者）**：tick=8796095，parent=47，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 74 · consumer（L4 下游消费者）**：tick=8796095，parent=47，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 75 · consumer（L4 下游消费者）**：tick=8892345，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 76 · consumer（L4 下游消费者）**：tick=8892345，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 77 · consumer（L4 下游消费者）**：tick=8894270，parent=72，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 78 · consumer（L4 下游消费者）**：tick=8894655，parent=77，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 79 · consumer（L4 下游消费者）**：tick=8895040，parent=47，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 80 · consumer（L4 下游消费者）**：tick=8985130，parent=79，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 81 · consumer（L4 下游消费者）**：tick=8985130，parent=79，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 82 · consumer（L4 下游消费者）**：tick=8985130，parent=79，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 83 · consumer（L4 下游消费者）**：tick=9038260，parent=75，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 84 · consumer（L4 下游消费者）**：tick=9038645，parent=83，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 85 · consumer（L4 下游消费者）**：tick=9039030，parent=84，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 86 · consumer（L4 下游消费者）**：tick=9039030，parent=84，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 87 · consumer（L4 下游消费者）**：tick=9039030，parent=84，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 88 · consumer（L4 下游消费者）**：tick=9039800，parent=84，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 89 · consumer（L4 下游消费者）**：tick=9041725，parent=75，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 90 · consumer（L4 下游消费者）**：tick=9094855，parent=88，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 91 · consumer（L4 下游消费者）**：tick=9099090，parent=75，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 92 · chain_end（生命周期结束标记（非 L5 证据））**：tick=19190325，parent=91，corr=none，field=，before=，after=，state=→，contained=1，outcome=errant_commit_seen。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`full`，provable_to=`L5`，admitted=`True`，certified=`True`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`full`，provable_to=`L5`，beyond=``，event_count=`96`
- containment：`n/a`（链路以 full/其他合法终局收口，或没有显式含住证据）
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_LSU_F6_EVENTS: TlbHit=0 SqForward=1120 DirtyEviction=1692 CasSuccess=2445`
- guest checksum：`1f4cbf14327717df`
- stats：
- `simTicks                                     19190325                       # Number of ticks simulated (Tick)`
- `simInsts                                         6156                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles            49846                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2/S02-F0-W5/seed2/prop_evt.txt.gz`：`9a8e588389e2e901886d34cbd2ad722601f4acd322f110e99c189b7054a5e6bf`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2/S02-F0-W5/chain_report.json`：`4bae5d8596f75a94b7d07879d85772a617e96dd1dd0215a19e6233f8749b07eb`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2/S02-F0-W5/seed2/chain_report.json`：`af94f1f51bd5a3ccde410a90b95e74bd299d2cf4c8492a1f1a8d7cc2c81883cb`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2/S02-F0-W5/seed2/stats.txt`：`aad87bd75710e4aa80db9b19d16c4a4073449aa0c9ba833952b76f073f2e2e81`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2/S02-F0-W5/seed2/run.out`：`301b8b883644ef28e7d22bc01d628151cc7223c3c7115f2cc92073c220940dac`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2/manifest.json`：`14594ea1f3c8389cd556efcafcaf614e5b8a8568703fc81c9fd35f0fda4e056b`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2/S02-F0-W5/seed2/lsq_fwd_injections.log`：`0d7c05b8b12ec846323a1af9f2fa4c04b0a273c8bd097354c477ac938b52871a`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2 --cells S02-F0-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S02-F0-W5_s2/S02-F0-W5/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/sq_forward --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 --lsqfwd_span_events 6 --lsq_struct_mode byte_flip --bits_to_change 2 --rng_seed 2 --chaos_propagation --prop_run_id S02-F0-W5 --prop_sample_run_id s2`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。

