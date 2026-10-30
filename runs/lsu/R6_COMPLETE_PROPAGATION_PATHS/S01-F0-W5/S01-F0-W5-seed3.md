# S01-F0-W5 seed3 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S01-F0-W5`；seed：`3`
- oracle：`Masked`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`140`；terminal：`detected_contained`；provable_to：`L5`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3`

## 2. 注入位置、地址、原值/新值与掩码

```
Cycle: 1445, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: bit_flip, Vaddr: 0x7ffffefc68, FwdSize: 8, ByteOffset: 5, Mask: 01000000, StoreSeq: 383, SqIdx: 49, LoadSeq: 397, LqIdx: 15
```
- 注入事件：`event_id=0`，tick=`556325`，va=`7ffffefc68`，field=`lsqfwd_forward`，before=``，after=``，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=6 eligible=6 injected=1 first_eligible_tick=556325 last_eligible_tick=14949935 fires=n/a no_effect=n/a (activated=W3-L0-layer)`
- 检测摘要：`CHAOS_DETECT: layer=Hardware RAS contained=1 tick=19190325 ptag=1 reason=store_discarded_not_retired`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | inj | L0 | — | 556325 | origin | lsqfwd_forward | — | — | — | — | — |
| 1 | sq_entry | L1 | 0 | 556325 | seq_primary | store_entry | — | — | — | — | — |
| 2 | lsq_fwd | L2 | 1 | 556325 | seq_primary | bit_flip | store_data | fwd_corrupt:bit_flip | — | — | — |
| 3 | resp | L3 | 2 | 556325 | seq_primary | bit_flip | — | — | — | — | — |
| 4 | taint_reg | L4 | 3 | 556325 | seq_primary | — | clean | tainted | — | — | — |
| 5 | sq_writeback | L3 | 4 | 557095 | seq_primary | — | — | — | —→packet_built | — | — |
| 6 | resp | L3 | — | 557865 | seq_primary | — | — | — | — | — | — |
| 7 | taint_reg | L4 | 6 | 557865 | seq_primary | — | clean | tainted | — | — | — |
| 8 | sq_complete | L3 | 5 | 557865 | seq_primary | — | — | — | —→completed | — | — |
| 9 | squash_discarded | L4 | 8 | 609840 | seq_primary | load | — | — | load_queue_uncommitted→— | 1 | contained |
| 10 | lsq_push | L1 | 9 | 617925 | addr_fallback | load | — | — | — | — | — |
| 11 | mem_req | L2 | — | 617925 | addr_fallback | — | — | — | — | — | — |
| 12 | lsq_sendfrag | L2 | 11 | 617925 | addr_fallback | load | — | — | — | — | — |
| 13 | tlb_translate | L2 | 12 | 617925 | addr_fallback | — | — | — | — | — | — |
| 14 | lsq_push | L1 | 10 | 643720 | addr_fallback | load | — | — | — | — | — |
| 15 | mem_req | L2 | — | 643720 | addr_fallback | — | — | — | — | — | — |
| 16 | lsq_sendfrag | L2 | 15 | 643720 | addr_fallback | load | — | — | — | — | — |
| 17 | tlb_translate | L2 | 16 | 643720 | addr_fallback | — | — | — | — | — | — |
| 18 | lsq_push | L1 | 14 | 699545 | addr_fallback | load | — | — | — | — | — |
| 19 | mem_req | L2 | — | 699545 | addr_fallback | — | — | — | — | — | — |
| 20 | lsq_sendfrag | L2 | 19 | 699545 | addr_fallback | load | — | — | — | — | — |
| 21 | tlb_translate | L2 | 20 | 699545 | addr_fallback | — | — | — | — | — | — |
| 22 | lsq_push | L1 | 18 | 793485 | addr_fallback | load | — | — | — | — | — |
| 23 | mem_req | L2 | — | 793485 | addr_fallback | — | — | — | — | — | — |
| 24 | lsq_sendfrag | L2 | 23 | 793485 | addr_fallback | load | — | — | — | — | — |
| 25 | tlb_translate | L2 | 24 | 793485 | addr_fallback | — | — | — | — | — | — |
| 26 | lsq_push | L1 | 22 | 10421565 | addr_fallback | store | — | — | — | — | — |
| 27 | mem_req | L2 | — | 10421565 | addr_fallback | — | — | — | — | — | — |
| 28 | lsq_sendfrag | L2 | 27 | 10421565 | addr_fallback | store | — | — | — | — | — |
| 29 | tlb_translate | L2 | 28 | 10421565 | addr_fallback | — | — | — | — | — | — |
| 30 | lsq_push | L1 | 26 | 10646405 | addr_fallback | load | — | — | — | — | — |
| 31 | mem_req | L2 | — | 10646405 | addr_fallback | — | — | — | — | — | — |
| 32 | lsq_sendfrag | L2 | 31 | 10646405 | addr_fallback | load | — | — | — | — | — |
| 33 | tlb_translate | L2 | 32 | 10646405 | addr_fallback | — | — | — | — | — | — |
| 34 | lsq_push | L1 | 30 | 10652950 | addr_fallback | store | — | — | — | — | — |
| 35 | mem_req | L2 | — | 10652950 | addr_fallback | — | — | — | — | — | — |
| 36 | lsq_sendfrag | L2 | 35 | 10652950 | addr_fallback | store | — | — | — | — | — |
| 37 | tlb_translate | L2 | 36 | 10652950 | addr_fallback | — | — | — | — | — | — |
| 38 | lsq_push | L1 | 34 | 10667580 | addr_fallback | load | — | — | — | — | — |
| 39 | mem_req | L2 | — | 10667580 | addr_fallback | — | — | — | — | — | — |
| 40 | lsq_sendfrag | L2 | 39 | 10667580 | addr_fallback | load | — | — | — | — | — |
| 41 | tlb_translate | L2 | 40 | 10667580 | addr_fallback | — | — | — | — | — | — |
| 42 | lsq_push | L1 | 38 | 10752280 | addr_fallback | store | — | — | — | — | — |
| 43 | mem_req | L2 | — | 10752280 | addr_fallback | — | — | — | — | — | — |
| 44 | lsq_sendfrag | L2 | 43 | 10752280 | addr_fallback | store | — | — | — | — | — |
| 45 | tlb_translate | L2 | 44 | 10752280 | addr_fallback | — | — | — | — | — | — |
| 46 | lsq_push | L1 | 42 | 11492250 | addr_fallback | load | — | — | — | — | — |
| 47 | mem_req | L2 | — | 11492250 | addr_fallback | — | — | — | — | — | — |
| 48 | lsq_sendfrag | L2 | 47 | 11492250 | addr_fallback | load | — | — | — | — | — |
| 49 | tlb_translate | L2 | 48 | 11492250 | addr_fallback | — | — | — | — | — | — |
| 50 | lsq_push | L1 | 46 | 11495715 | addr_fallback | store | — | — | — | — | — |
| 51 | mem_req | L2 | — | 11495715 | addr_fallback | — | — | — | — | — | — |
| 52 | lsq_sendfrag | L2 | 51 | 11495715 | addr_fallback | store | — | — | — | — | — |
| 53 | tlb_translate | L2 | 52 | 11495715 | addr_fallback | — | — | — | — | — | — |
| 54 | lsq_push | L1 | 50 | 11510345 | addr_fallback | load | — | — | — | — | — |
| 55 | mem_req | L2 | — | 11510345 | addr_fallback | — | — | — | — | — | — |
| 56 | lsq_sendfrag | L2 | 55 | 11510345 | addr_fallback | load | — | — | — | — | — |
| 57 | tlb_translate | L2 | 56 | 11510345 | addr_fallback | — | — | — | — | — | — |
| 58 | lsq_push | L1 | 54 | 11540760 | addr_fallback | store | — | — | — | — | — |
| 59 | mem_req | L2 | — | 11540760 | addr_fallback | — | — | — | — | — | — |
| 60 | lsq_sendfrag | L2 | 59 | 11540760 | addr_fallback | store | — | — | — | — | — |
| 61 | tlb_translate | L2 | 60 | 11540760 | addr_fallback | — | — | — | — | — | — |
| 62 | lsq_push | L1 | 58 | 11573485 | addr_fallback | load | — | — | — | — | — |
| 63 | mem_req | L2 | — | 11573485 | addr_fallback | — | — | — | — | — | — |
| 64 | lsq_sendfrag | L2 | 63 | 11573485 | addr_fallback | load | — | — | — | — | — |
| 65 | tlb_translate | L2 | 64 | 11573485 | addr_fallback | — | — | — | — | — | — |
| 66 | lsq_push | L1 | 62 | 11580415 | addr_fallback | store | — | — | — | — | — |
| 67 | mem_req | L2 | — | 11580415 | addr_fallback | — | — | — | — | — | — |
| 68 | lsq_sendfrag | L2 | 67 | 11580415 | addr_fallback | store | — | — | — | — | — |
| 69 | tlb_translate | L2 | 68 | 11580415 | addr_fallback | — | — | — | — | — | — |
| 70 | lsq_push | L1 | 66 | 11589655 | addr_fallback | load | — | — | — | — | — |
| 71 | mem_req | L2 | — | 11589655 | addr_fallback | — | — | — | — | — | — |
| 72 | lsq_sendfrag | L2 | 71 | 11589655 | addr_fallback | load | — | — | — | — | — |
| 73 | tlb_translate | L2 | 72 | 11589655 | addr_fallback | — | — | — | — | — | — |
| 74 | lsq_push | L1 | 70 | 11635085 | addr_fallback | store | — | — | — | — | — |
| 75 | mem_req | L2 | — | 11635085 | addr_fallback | — | — | — | — | — | — |
| 76 | lsq_sendfrag | L2 | 75 | 11635085 | addr_fallback | store | — | — | — | — | — |
| 77 | tlb_translate | L2 | 76 | 11635085 | addr_fallback | — | — | — | — | — | — |
| 78 | lsq_push | L1 | 74 | 11644710 | addr_fallback | load | — | — | — | — | — |
| 79 | mem_req | L2 | — | 11644710 | addr_fallback | — | — | — | — | — | — |
| 80 | lsq_sendfrag | L2 | 79 | 11644710 | addr_fallback | load | — | — | — | — | — |
| 81 | tlb_translate | L2 | 80 | 11644710 | addr_fallback | — | — | — | — | — | — |
| 82 | lsq_push | L1 | 78 | 11756360 | addr_fallback | load | — | — | — | — | — |
| 83 | mem_req | L2 | — | 11756360 | addr_fallback | — | — | — | — | — | — |
| 84 | lsq_sendfrag | L2 | 83 | 11756360 | addr_fallback | load | — | — | — | — | — |
| 85 | tlb_translate | L2 | 84 | 11756360 | addr_fallback | — | — | — | — | — | — |
| 86 | lsq_push | L1 | 82 | 12202190 | addr_fallback | store | — | — | — | — | — |
| 87 | mem_req | L2 | — | 12202190 | addr_fallback | — | — | — | — | — | — |
| 88 | lsq_sendfrag | L2 | 87 | 12202190 | addr_fallback | store | — | — | — | — | — |
| 89 | tlb_translate | L2 | 88 | 12202190 | addr_fallback | — | — | — | — | — | — |
| 90 | lsq_push | L1 | 86 | 12547150 | addr_fallback | load | — | — | — | — | — |
| 91 | mem_req | L2 | — | 12547150 | addr_fallback | — | — | — | — | — | — |
| 92 | lsq_sendfrag | L2 | 91 | 12547150 | addr_fallback | load | — | — | — | — | — |
| 93 | tlb_translate | L2 | 92 | 12547150 | addr_fallback | — | — | — | — | — | — |
| 94 | lsq_push | L1 | 90 | 12609135 | addr_fallback | load | — | — | — | — | — |
| 95 | mem_req | L2 | — | 12609135 | addr_fallback | — | — | — | — | — | — |
| 96 | lsq_sendfrag | L2 | 95 | 12609135 | addr_fallback | load | — | — | — | — | — |
| 97 | tlb_translate | L2 | 96 | 12609135 | addr_fallback | — | — | — | — | — | — |
| 98 | lsq_push | L1 | 94 | 12613755 | addr_fallback | store | — | — | — | — | — |
| 99 | mem_req | L2 | — | 12613755 | addr_fallback | — | — | — | — | — | — |
| 100 | lsq_sendfrag | L2 | 99 | 12613755 | addr_fallback | store | — | — | — | — | — |
| 101 | tlb_translate | L2 | 100 | 12613755 | addr_fallback | — | — | — | — | — | — |
| 102 | lsq_push | L1 | 98 | 12636085 | addr_fallback | load | — | — | — | — | — |
| 103 | mem_req | L2 | — | 12636085 | addr_fallback | — | — | — | — | — | — |
| 104 | lsq_sendfrag | L2 | 103 | 12636085 | addr_fallback | load | — | — | — | — | — |
| 105 | tlb_translate | L2 | 104 | 12636085 | addr_fallback | — | — | — | — | — | — |
| 106 | lsq_push | L1 | 102 | 12694990 | addr_fallback | store | — | — | — | — | — |
| 107 | mem_req | L2 | — | 12694990 | addr_fallback | — | — | — | — | — | — |
| 108 | lsq_sendfrag | L2 | 107 | 12694990 | addr_fallback | store | — | — | — | — | — |
| 109 | tlb_translate | L2 | 108 | 12694990 | addr_fallback | — | — | — | — | — | — |
| 110 | lsq_push | L1 | 106 | 12696915 | addr_fallback | load | — | — | — | — | — |
| 111 | mem_req | L2 | — | 12696915 | addr_fallback | — | — | — | — | — | — |
| 112 | lsq_sendfrag | L2 | 111 | 12696915 | addr_fallback | load | — | — | — | — | — |
| 113 | tlb_translate | L2 | 112 | 12696915 | addr_fallback | — | — | — | — | — | — |
| 114 | lsq_push | L1 | 110 | 12702305 | addr_fallback | store | — | — | — | — | — |
| 115 | mem_req | L2 | — | 12702305 | addr_fallback | — | — | — | — | — | — |
| 116 | lsq_sendfrag | L2 | 115 | 12702305 | addr_fallback | store | — | — | — | — | — |
| 117 | tlb_translate | L2 | 116 | 12702305 | addr_fallback | — | — | — | — | — | — |
| 118 | lsq_push | L1 | 114 | 12851300 | addr_fallback | load | — | — | — | — | — |
| 119 | mem_req | L2 | — | 12851300 | addr_fallback | — | — | — | — | — | — |
| 120 | lsq_sendfrag | L2 | 119 | 12851300 | addr_fallback | load | — | — | — | — | — |
| 121 | tlb_translate | L2 | 120 | 12851300 | addr_fallback | — | — | — | — | — | — |
| 122 | lsq_push | L1 | 118 | 12866700 | addr_fallback | load | — | — | — | — | — |
| 123 | mem_req | L2 | — | 12866700 | addr_fallback | — | — | — | — | — | — |
| 124 | lsq_sendfrag | L2 | 123 | 12866700 | addr_fallback | load | — | — | — | — | — |
| 125 | tlb_translate | L2 | 124 | 12866700 | addr_fallback | — | — | — | — | — | — |
| 126 | lsq_push | L1 | 122 | 12985280 | addr_fallback | store | — | — | — | — | — |
| 127 | mem_req | L2 | — | 12985280 | addr_fallback | — | — | — | — | — | — |
| 128 | lsq_sendfrag | L2 | 127 | 12985280 | addr_fallback | store | — | — | — | — | — |
| 129 | tlb_translate | L2 | 128 | 12985280 | addr_fallback | — | — | — | — | — | — |
| 130 | lsq_push | L1 | 126 | 14777070 | addr_fallback | store | — | — | — | — | — |
| 131 | mem_req | L2 | — | 14777070 | addr_fallback | — | — | — | — | — | — |
| 132 | lsq_sendfrag | L2 | 131 | 14777070 | addr_fallback | store | — | — | — | — | — |
| 133 | tlb_translate | L2 | 132 | 14777070 | addr_fallback | — | — | — | — | — | — |
| 134 | lsq_push | L1 | 130 | 15006530 | addr_fallback | load | — | — | — | — | — |
| 135 | mem_req | L2 | — | 15006530 | addr_fallback | — | — | — | — | — | — |
| 136 | lsq_sendfrag | L2 | 135 | 15006530 | addr_fallback | load | — | — | — | — | — |
| 137 | tlb_translate | L2 | 136 | 15006530 | addr_fallback | — | — | — | — | — | — |
| 138 | store_not_retired | L4 | 7 | 19190325 | taint_prop | — | — | — | response_seen_commit_absent→— | 1 | contained |
| 139 | chain_end | L4 | 134 | 19190325 | none | — | — | — | — | 1 | detected_contained |

## 4. 逐步传播语义

- **event 0 · inj（L0 故障注入）**：tick=556325，parent=（根），corr=origin，field=lsqfwd_forward，before=，after=，state=→，contained=，outcome=。
- **event 1 · sq_entry（L1 生产 store 的 SQ 表项（转发源））**：tick=556325，parent=0，corr=seq_primary，field=store_entry，before=，after=，state=→，contained=，outcome=。
- **event 2 · lsq_fwd（L2 store→load 转发决策/传输）**：tick=556325，parent=1，corr=seq_primary，field=bit_flip，before=store_data，after=fwd_corrupt:bit_flip，state=→，contained=，outcome=。
- **event 3 · resp（L3 数据响应）**：tick=556325，parent=2，corr=seq_primary，field=bit_flip，before=，after=，state=→，contained=，outcome=。
- **event 4 · taint_reg（L4 污点进入目的寄存器）**：tick=556325，parent=3，corr=seq_primary，field=，before=clean，after=tainted，state=→，contained=，outcome=。
- **event 5 · sq_writeback（家族事件）**：tick=557095，parent=4，corr=seq_primary，field=，before=，after=，state=→packet_built，contained=，outcome=。
- **event 6 · resp（L3 数据响应）**：tick=557865，parent=（根），corr=seq_primary，field=，before=，after=，state=→，contained=，outcome=。
- **event 7 · taint_reg（L4 污点进入目的寄存器）**：tick=557865，parent=6，corr=seq_primary，field=，before=clean，after=tainted，state=→，contained=，outcome=。
- **event 8 · sq_complete（L3 store 完成）**：tick=557865，parent=5，corr=seq_primary，field=，before=，after=，state=→completed，contained=，outcome=。
- **event 9 · squash_discarded（L4 检测并 squash 丢弃）**：tick=609840，parent=8，corr=seq_primary，field=load，before=，after=，state=load_queue_uncommitted→，contained=1，outcome=contained。
- **event 10 · lsq_push（家族事件）**：tick=617925，parent=9，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 11 · mem_req（L2 请求创建）**：tick=617925，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 12 · lsq_sendfrag（家族事件）**：tick=617925，parent=11，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 13 · tlb_translate（家族事件）**：tick=617925，parent=12，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 14 · lsq_push（家族事件）**：tick=643720，parent=10，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 15 · mem_req（L2 请求创建）**：tick=643720，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 16 · lsq_sendfrag（家族事件）**：tick=643720，parent=15，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 17 · tlb_translate（家族事件）**：tick=643720，parent=16，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 18 · lsq_push（家族事件）**：tick=699545，parent=14，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 19 · mem_req（L2 请求创建）**：tick=699545，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 20 · lsq_sendfrag（家族事件）**：tick=699545，parent=19，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 21 · tlb_translate（家族事件）**：tick=699545，parent=20，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 22 · lsq_push（家族事件）**：tick=793485，parent=18，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 23 · mem_req（L2 请求创建）**：tick=793485，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 24 · lsq_sendfrag（家族事件）**：tick=793485，parent=23，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 25 · tlb_translate（家族事件）**：tick=793485，parent=24，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 26 · lsq_push（家族事件）**：tick=10421565，parent=22，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 27 · mem_req（L2 请求创建）**：tick=10421565，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 28 · lsq_sendfrag（家族事件）**：tick=10421565，parent=27，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 29 · tlb_translate（家族事件）**：tick=10421565，parent=28，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 30 · lsq_push（家族事件）**：tick=10646405，parent=26，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 31 · mem_req（L2 请求创建）**：tick=10646405，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 32 · lsq_sendfrag（家族事件）**：tick=10646405，parent=31，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 33 · tlb_translate（家族事件）**：tick=10646405，parent=32，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 34 · lsq_push（家族事件）**：tick=10652950，parent=30，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 35 · mem_req（L2 请求创建）**：tick=10652950，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 36 · lsq_sendfrag（家族事件）**：tick=10652950，parent=35，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 37 · tlb_translate（家族事件）**：tick=10652950，parent=36，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 38 · lsq_push（家族事件）**：tick=10667580，parent=34，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 39 · mem_req（L2 请求创建）**：tick=10667580，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 40 · lsq_sendfrag（家族事件）**：tick=10667580，parent=39，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 41 · tlb_translate（家族事件）**：tick=10667580，parent=40，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 42 · lsq_push（家族事件）**：tick=10752280，parent=38，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 43 · mem_req（L2 请求创建）**：tick=10752280，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 44 · lsq_sendfrag（家族事件）**：tick=10752280，parent=43，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 45 · tlb_translate（家族事件）**：tick=10752280，parent=44，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 46 · lsq_push（家族事件）**：tick=11492250，parent=42，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 47 · mem_req（L2 请求创建）**：tick=11492250，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 48 · lsq_sendfrag（家族事件）**：tick=11492250，parent=47，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 49 · tlb_translate（家族事件）**：tick=11492250，parent=48，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 50 · lsq_push（家族事件）**：tick=11495715，parent=46，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 51 · mem_req（L2 请求创建）**：tick=11495715，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 52 · lsq_sendfrag（家族事件）**：tick=11495715，parent=51，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 53 · tlb_translate（家族事件）**：tick=11495715，parent=52，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 54 · lsq_push（家族事件）**：tick=11510345，parent=50，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 55 · mem_req（L2 请求创建）**：tick=11510345，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 56 · lsq_sendfrag（家族事件）**：tick=11510345，parent=55，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 57 · tlb_translate（家族事件）**：tick=11510345，parent=56，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 58 · lsq_push（家族事件）**：tick=11540760，parent=54，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 59 · mem_req（L2 请求创建）**：tick=11540760，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 60 · lsq_sendfrag（家族事件）**：tick=11540760，parent=59，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 61 · tlb_translate（家族事件）**：tick=11540760，parent=60，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 62 · lsq_push（家族事件）**：tick=11573485，parent=58，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 63 · mem_req（L2 请求创建）**：tick=11573485，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 64 · lsq_sendfrag（家族事件）**：tick=11573485，parent=63，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 65 · tlb_translate（家族事件）**：tick=11573485，parent=64，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 66 · lsq_push（家族事件）**：tick=11580415，parent=62，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 67 · mem_req（L2 请求创建）**：tick=11580415，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 68 · lsq_sendfrag（家族事件）**：tick=11580415，parent=67，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 69 · tlb_translate（家族事件）**：tick=11580415，parent=68，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 70 · lsq_push（家族事件）**：tick=11589655，parent=66，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 71 · mem_req（L2 请求创建）**：tick=11589655，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 72 · lsq_sendfrag（家族事件）**：tick=11589655，parent=71，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 73 · tlb_translate（家族事件）**：tick=11589655，parent=72，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 74 · lsq_push（家族事件）**：tick=11635085，parent=70，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 75 · mem_req（L2 请求创建）**：tick=11635085，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 76 · lsq_sendfrag（家族事件）**：tick=11635085，parent=75，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 77 · tlb_translate（家族事件）**：tick=11635085，parent=76，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 78 · lsq_push（家族事件）**：tick=11644710，parent=74，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 79 · mem_req（L2 请求创建）**：tick=11644710，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 80 · lsq_sendfrag（家族事件）**：tick=11644710，parent=79，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 81 · tlb_translate（家族事件）**：tick=11644710，parent=80，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 82 · lsq_push（家族事件）**：tick=11756360，parent=78，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 83 · mem_req（L2 请求创建）**：tick=11756360，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 84 · lsq_sendfrag（家族事件）**：tick=11756360，parent=83，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 85 · tlb_translate（家族事件）**：tick=11756360，parent=84，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 86 · lsq_push（家族事件）**：tick=12202190，parent=82，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 87 · mem_req（L2 请求创建）**：tick=12202190，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 88 · lsq_sendfrag（家族事件）**：tick=12202190，parent=87，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 89 · tlb_translate（家族事件）**：tick=12202190，parent=88，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 90 · lsq_push（家族事件）**：tick=12547150，parent=86，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 91 · mem_req（L2 请求创建）**：tick=12547150，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 92 · lsq_sendfrag（家族事件）**：tick=12547150，parent=91，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 93 · tlb_translate（家族事件）**：tick=12547150，parent=92，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 94 · lsq_push（家族事件）**：tick=12609135，parent=90，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 95 · mem_req（L2 请求创建）**：tick=12609135，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 96 · lsq_sendfrag（家族事件）**：tick=12609135，parent=95，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 97 · tlb_translate（家族事件）**：tick=12609135，parent=96，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 98 · lsq_push（家族事件）**：tick=12613755，parent=94，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 99 · mem_req（L2 请求创建）**：tick=12613755，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 100 · lsq_sendfrag（家族事件）**：tick=12613755，parent=99，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 101 · tlb_translate（家族事件）**：tick=12613755，parent=100，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 102 · lsq_push（家族事件）**：tick=12636085，parent=98，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 103 · mem_req（L2 请求创建）**：tick=12636085，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 104 · lsq_sendfrag（家族事件）**：tick=12636085，parent=103，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 105 · tlb_translate（家族事件）**：tick=12636085，parent=104，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 106 · lsq_push（家族事件）**：tick=12694990，parent=102，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 107 · mem_req（L2 请求创建）**：tick=12694990，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 108 · lsq_sendfrag（家族事件）**：tick=12694990，parent=107，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 109 · tlb_translate（家族事件）**：tick=12694990，parent=108，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 110 · lsq_push（家族事件）**：tick=12696915，parent=106，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 111 · mem_req（L2 请求创建）**：tick=12696915，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 112 · lsq_sendfrag（家族事件）**：tick=12696915，parent=111，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 113 · tlb_translate（家族事件）**：tick=12696915，parent=112，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 114 · lsq_push（家族事件）**：tick=12702305，parent=110，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 115 · mem_req（L2 请求创建）**：tick=12702305，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 116 · lsq_sendfrag（家族事件）**：tick=12702305，parent=115，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 117 · tlb_translate（家族事件）**：tick=12702305，parent=116，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 118 · lsq_push（家族事件）**：tick=12851300，parent=114，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 119 · mem_req（L2 请求创建）**：tick=12851300，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 120 · lsq_sendfrag（家族事件）**：tick=12851300，parent=119，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 121 · tlb_translate（家族事件）**：tick=12851300，parent=120，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 122 · lsq_push（家族事件）**：tick=12866700，parent=118，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 123 · mem_req（L2 请求创建）**：tick=12866700，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 124 · lsq_sendfrag（家族事件）**：tick=12866700，parent=123，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 125 · tlb_translate（家族事件）**：tick=12866700，parent=124，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 126 · lsq_push（家族事件）**：tick=12985280，parent=122，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 127 · mem_req（L2 请求创建）**：tick=12985280，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 128 · lsq_sendfrag（家族事件）**：tick=12985280，parent=127，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 129 · tlb_translate（家族事件）**：tick=12985280，parent=128，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 130 · lsq_push（家族事件）**：tick=14777070，parent=126，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 131 · mem_req（L2 请求创建）**：tick=14777070，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 132 · lsq_sendfrag（家族事件）**：tick=14777070，parent=131，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 133 · tlb_translate（家族事件）**：tick=14777070，parent=132，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 134 · lsq_push（家族事件）**：tick=15006530，parent=130，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 135 · mem_req（L2 请求创建）**：tick=15006530，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 136 · lsq_sendfrag（家族事件）**：tick=15006530，parent=135，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 137 · tlb_translate（家族事件）**：tick=15006530，parent=136，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 138 · store_not_retired（家族事件）**：tick=19190325，parent=7，corr=taint_prop，field=，before=，after=，state=response_seen_commit_absent→，contained=1，outcome=contained。
- **event 139 · chain_end（生命周期结束标记（非 L5 证据））**：tick=19190325，parent=134，corr=none，field=，before=，after=，state=→，contained=1，outcome=detected_contained。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`detected_contained`，provable_to=`L5`，admitted=`True`，certified=`True`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`detected_contained`，provable_to=`L5`，beyond=``，event_count=`140`
- containment：layer=`L4`，later_layers_N/A=`['L5']`，reason=`S01-F0-W5 fault 1 显式含住：kind=squash_discarded field='load' detection_layer=L4 outcome=contained`
- containment metrics：`{'L4': {'kind': 'squash_discarded', 'field': 'load', 'outcome': 'contained', 'contained': '1', 'event_id': '9', 'tick': '609840'}}`
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_DETECT: layer=Hardware RAS contained=1 tick=19190325 ptag=1 reason=store_discarded_not_retired`
- guest checksum：`1f4cbf14327717df`
- stats：
- `simTicks                                     19190325                       # Number of ticks simulated (Tick)`
- `simInsts                                         6152                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles            49846                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3/S01-F0-W5/seed3/prop_evt.txt.gz`：`2bae3e18da0a516fd4bf0f9d586fc83ca6b6cbec4cd5e1c98fc23e97fa44a022`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3/S01-F0-W5/chain_report.json`：`0bfde8d16c011eefa15fd1a5718c871aa6fc39af6bfec8be759caff3c8eee863`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3/S01-F0-W5/seed3/chain_report.json`：`cd7c907c23372535494895808d1dc92c62280aaa659e51c2ae7939157b59f8e6`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3/S01-F0-W5/seed3/stats.txt`：`cf6d9e2120f59397fc07bd7e5bdf0930d324324c9a6a82c652558427a34733a4`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3/S01-F0-W5/seed3/run.out`：`b2af7036d6a84f5db7f2a4bcca5b61097df80da163fd545ed93152c0a86454c6`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3/manifest.json`：`7e6e0dad75955c09f57765e02881723194e9b408dca7ab6ffe5cdade4e0cee86`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3/S01-F0-W5/seed3/lsq_fwd_injections.log`：`bb62e125caaad963e97adea18822397f73d327a5ffdeef4804463299fd0e44d7`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3 --cells S01-F0-W5 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S01-F0-W5_s3/S01-F0-W5/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/sq_forward --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 --lsqfwd_span_events 6 --lsq_struct_mode byte_flip --rng_seed 3 --chaos_propagation --prop_run_id S01-F0-W5 --prop_sample_run_id s3`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。

