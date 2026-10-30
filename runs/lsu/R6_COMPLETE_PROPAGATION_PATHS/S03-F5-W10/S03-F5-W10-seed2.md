# S03-F5-W10 seed2 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S03-F5-W10`；seed：`2`
- oracle：`Crash`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`362`；terminal：`full`；provable_to：`L5`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2`

## 2. 注入位置、地址、原值/新值与掩码

```
Cycle: 1479, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: byte_lane_skew, Vaddr: 0x7ffffefd38, FwdSize: 8, ByteOffset: 1, Mask: 00000000, StoreSeq: 249, SqIdx: 44, LoadSeq: 259, LqIdx: 7
Cycle: 23062, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: byte_lane_skew, Vaddr: 0x4c6698, FwdSize: 8, ByteOffset: 1, Mask: 00000000, StoreSeq: 5967, SqIdx: 565, LoadSeq: 5973, LqIdx: 324
Cycle: 24447, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: byte_lane_skew, Vaddr: 0x7ffffeeb20, FwdSize: 8, ByteOffset: 1, Mask: 00000000, StoreSeq: 6252, SqIdx: 578, LoadSeq: 6267, LqIdx: 339
Cycle: 34191, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: byte_lane_skew, Vaddr: 0x48fb70, FwdSize: 8, ByteOffset: 1, Mask: 00000000, StoreSeq: 10015, SqIdx: 797, LoadSeq: 10018, LqIdx: 589
```
- 注入事件：`event_id=0`，tick=`569030`，va=`7ffffefbd0`，field=`lsqfwd_forward`，before=``，after=``，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F5 attempted=5 eligible=5 injected=5 first_eligible_tick=569030 last_eligible_tick=13163535 fires=5 no_effect=0 (activated=W3-L0-layer)`
- 检测摘要：`CHAOS_DETECT: layer=None contained=0 tick=8880025 ptag=3 reason=errant_commit`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | inj | L0 | — | 569030 | origin | lsqfwd_forward | — | — | — | — | — |
| 1 | sq_entry | L1 | 0 | 569030 | seq_primary | store_entry | — | — | — | — | — |
| 2 | lsq_fwd | L2 | 1 | 569030 | seq_primary | byte_lane_skew | store_data | fwd_corrupt:byte_lane_skew | — | — | — |
| 3 | resp | L3 | 2 | 569030 | seq_primary | byte_lane_skew | — | — | — | — | — |
| 4 | taint_reg | L4 | 3 | 569030 | seq_primary | — | clean | tainted | — | — | — |
| 10 | sq_writeback | L3 | 4 | 570185 | seq_primary | — | — | — | —→packet_built | — | — |
| 12 | resp | L3 | — | 570955 | seq_primary | — | — | — | — | — | — |
| 13 | taint_reg | L4 | 12 | 570955 | seq_primary | — | clean | tainted | — | — | — |
| 14 | sq_complete | L3 | 10 | 570955 | seq_primary | — | — | — | —→completed | — | — |
| 19 | squash_discarded | L4 | 14 | 661045 | seq_primary | load | — | — | load_queue_uncommitted→— | 1 | contained |
| 20 | lsq_push | L1 | 19 | 667205 | addr_fallback | load | — | — | — | — | — |
| 21 | mem_req | L2 | — | 667205 | addr_fallback | — | — | — | — | — | — |
| 22 | lsq_sendfrag | L2 | 21 | 667205 | addr_fallback | load | — | — | — | — | — |
| 23 | tlb_translate | L2 | 22 | 667205 | addr_fallback | — | — | — | — | — | — |
| 28 | lsq_push | L1 | 20 | 672980 | addr_fallback | load | — | — | — | — | — |
| 29 | mem_req | L2 | — | 672980 | addr_fallback | — | — | — | — | — | — |
| 30 | lsq_sendfrag | L2 | 29 | 672980 | addr_fallback | load | — | — | — | — | — |
| 31 | tlb_translate | L2 | 30 | 672980 | addr_fallback | — | — | — | — | — | — |
| 36 | lsq_push | L1 | 28 | 679525 | addr_fallback | load | — | — | — | — | — |
| 37 | mem_req | L2 | — | 679525 | addr_fallback | — | — | — | — | — | — |
| 38 | lsq_sendfrag | L2 | 37 | 679525 | addr_fallback | load | — | — | — | — | — |
| 39 | tlb_translate | L2 | 38 | 679525 | addr_fallback | — | — | — | — | — | — |
| 44 | lsq_push | L1 | 36 | 686070 | addr_fallback | load | — | — | — | — | — |
| 45 | mem_req | L2 | — | 686070 | addr_fallback | — | — | — | — | — | — |
| 46 | lsq_sendfrag | L2 | 45 | 686070 | addr_fallback | load | — | — | — | — | — |
| 47 | tlb_translate | L2 | 46 | 686070 | addr_fallback | — | — | — | — | — | — |
| 52 | lsq_push | L1 | 44 | 775775 | addr_fallback | load | — | — | — | — | — |
| 53 | mem_req | L2 | — | 775775 | addr_fallback | — | — | — | — | — | — |
| 54 | lsq_sendfrag | L2 | 53 | 775775 | addr_fallback | load | — | — | — | — | — |
| 55 | tlb_translate | L2 | 54 | 775775 | addr_fallback | — | — | — | — | — | — |
| 60 | lsq_push | L1 | 52 | 782320 | addr_fallback | load | — | — | — | — | — |
| 61 | mem_req | L2 | — | 782320 | addr_fallback | — | — | — | — | — | — |
| 62 | lsq_sendfrag | L2 | 61 | 782320 | addr_fallback | load | — | — | — | — | — |
| 63 | tlb_translate | L2 | 62 | 782320 | addr_fallback | — | — | — | — | — | — |
| 68 | lsq_push | L1 | 60 | 788865 | addr_fallback | load | — | — | — | — | — |
| 69 | mem_req | L2 | — | 788865 | addr_fallback | — | — | — | — | — | — |
| 70 | lsq_sendfrag | L2 | 69 | 788865 | addr_fallback | load | — | — | — | — | — |
| 71 | tlb_translate | L2 | 70 | 788865 | addr_fallback | — | — | — | — | — | — |
| 76 | lsq_push | L1 | 68 | 789635 | addr_fallback | store | — | — | — | — | — |
| 77 | mem_req | L2 | — | 789635 | addr_fallback | — | — | — | — | — | — |
| 78 | lsq_sendfrag | L2 | 77 | 789635 | addr_fallback | store | — | — | — | — | — |
| 79 | tlb_translate | L2 | 78 | 789635 | addr_fallback | — | — | — | — | — | — |
| 80 | lsq_push | L1 | 76 | 889735 | addr_fallback | load | — | — | — | — | — |
| 81 | mem_req | L2 | — | 889735 | addr_fallback | — | — | — | — | — | — |
| 82 | lsq_sendfrag | L2 | 81 | 889735 | addr_fallback | load | — | — | — | — | — |
| 83 | tlb_translate | L2 | 82 | 889735 | addr_fallback | — | — | — | — | — | — |
| 193 | lsq_push | L1 | 80 | 11424490 | addr_fallback | store | — | — | — | — | — |
| 194 | mem_req | L2 | — | 11424490 | addr_fallback | — | — | — | — | — | — |
| 195 | lsq_sendfrag | L2 | 194 | 11424490 | addr_fallback | store | — | — | — | — | — |
| 196 | tlb_translate | L2 | 195 | 11424490 | addr_fallback | — | — | — | — | — | — |
| 197 | lsq_push | L1 | 193 | 11496100 | addr_fallback | load | — | — | — | — | — |
| 198 | mem_req | L2 | — | 11496100 | addr_fallback | — | — | — | — | — | — |
| 199 | lsq_sendfrag | L2 | 198 | 11496100 | addr_fallback | load | — | — | — | — | — |
| 200 | tlb_translate | L2 | 199 | 11496100 | addr_fallback | — | — | — | — | — | — |
| 201 | lsq_push | L1 | 197 | 11601590 | addr_fallback | store | — | — | — | — | — |
| 202 | mem_req | L2 | — | 11601590 | addr_fallback | — | — | — | — | — | — |
| 203 | lsq_sendfrag | L2 | 202 | 11601590 | addr_fallback | store | — | — | — | — | — |
| 204 | tlb_translate | L2 | 203 | 11601590 | addr_fallback | — | — | — | — | — | — |
| 205 | lsq_push | L1 | 201 | 11673585 | addr_fallback | load | — | — | — | — | — |
| 206 | mem_req | L2 | — | 11673585 | addr_fallback | — | — | — | — | — | — |
| 207 | lsq_sendfrag | L2 | 206 | 11673585 | addr_fallback | load | — | — | — | — | — |
| 208 | tlb_translate | L2 | 207 | 11673585 | addr_fallback | — | — | — | — | — | — |
| 313 | lsq_push | L1 | 205 | 13325620 | addr_fallback | store | — | — | — | — | — |
| 314 | mem_req | L2 | — | 13325620 | addr_fallback | — | — | — | — | — | — |
| 315 | lsq_sendfrag | L2 | 314 | 13325620 | addr_fallback | store | — | — | — | — | — |
| 316 | tlb_translate | L2 | 315 | 13325620 | addr_fallback | — | — | — | — | — | — |
| 330 | lsq_push | L1 | 313 | 13567400 | addr_fallback | store | — | — | — | — | — |
| 331 | mem_req | L2 | — | 13567400 | addr_fallback | — | — | — | — | — | — |
| 332 | lsq_sendfrag | L2 | 331 | 13567400 | addr_fallback | store | — | — | — | — | — |
| 333 | tlb_translate | L2 | 332 | 13567400 | addr_fallback | — | — | — | — | — | — |
| 342 | lsq_push | L1 | 330 | 13787620 | addr_fallback | load | — | — | — | — | — |
| 343 | mem_req | L2 | — | 13787620 | addr_fallback | — | — | — | — | — | — |
| 344 | lsq_sendfrag | L2 | 343 | 13787620 | addr_fallback | load | — | — | — | — | — |
| 345 | tlb_translate | L2 | 344 | 13787620 | addr_fallback | — | — | — | — | — | — |
| 346 | lsq_push | L1 | 342 | 14081375 | addr_fallback | store | — | — | — | — | — |
| 347 | mem_req | L2 | — | 14081375 | addr_fallback | — | — | — | — | — | — |
| 348 | lsq_sendfrag | L2 | 347 | 14081375 | addr_fallback | store | — | — | — | — | — |
| 349 | tlb_translate | L2 | 348 | 14081375 | addr_fallback | — | — | — | — | — | — |
| 350 | store_not_retired | L4 | 13 | 14825965 | taint_prop | — | — | — | response_seen_commit_absent→— | 1 | contained |
| 354 | chain_end | L4 | 346 | 14825965 | none | — | — | — | — | 1 | detected_contained |

## 4. 逐步传播语义

- **event 0 · inj（L0 故障注入）**：tick=569030，parent=（根），corr=origin，field=lsqfwd_forward，before=，after=，state=→，contained=，outcome=。
- **event 1 · sq_entry（L1 生产 store 的 SQ 表项（转发源））**：tick=569030，parent=0，corr=seq_primary，field=store_entry，before=，after=，state=→，contained=，outcome=。
- **event 2 · lsq_fwd（L2 store→load 转发决策/传输）**：tick=569030，parent=1，corr=seq_primary，field=byte_lane_skew，before=store_data，after=fwd_corrupt:byte_lane_skew，state=→，contained=，outcome=。
- **event 3 · resp（L3 数据响应）**：tick=569030，parent=2，corr=seq_primary，field=byte_lane_skew，before=，after=，state=→，contained=，outcome=。
- **event 4 · taint_reg（L4 污点进入目的寄存器）**：tick=569030，parent=3，corr=seq_primary，field=，before=clean，after=tainted，state=→，contained=，outcome=。
- **event 10 · sq_writeback（家族事件）**：tick=570185，parent=4，corr=seq_primary，field=，before=，after=，state=→packet_built，contained=，outcome=。
- **event 12 · resp（L3 数据响应）**：tick=570955，parent=（根），corr=seq_primary，field=，before=，after=，state=→，contained=，outcome=。
- **event 13 · taint_reg（L4 污点进入目的寄存器）**：tick=570955，parent=12，corr=seq_primary，field=，before=clean，after=tainted，state=→，contained=，outcome=。
- **event 14 · sq_complete（L3 store 完成）**：tick=570955，parent=10，corr=seq_primary，field=，before=，after=，state=→completed，contained=，outcome=。
- **event 19 · squash_discarded（L4 检测并 squash 丢弃）**：tick=661045，parent=14，corr=seq_primary，field=load，before=，after=，state=load_queue_uncommitted→，contained=1，outcome=contained。
- **event 20 · lsq_push（家族事件）**：tick=667205，parent=19，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 21 · mem_req（L2 请求创建）**：tick=667205，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 22 · lsq_sendfrag（家族事件）**：tick=667205，parent=21，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 23 · tlb_translate（家族事件）**：tick=667205，parent=22，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 28 · lsq_push（家族事件）**：tick=672980，parent=20，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 29 · mem_req（L2 请求创建）**：tick=672980，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 30 · lsq_sendfrag（家族事件）**：tick=672980，parent=29，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 31 · tlb_translate（家族事件）**：tick=672980，parent=30，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 36 · lsq_push（家族事件）**：tick=679525，parent=28，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 37 · mem_req（L2 请求创建）**：tick=679525，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 38 · lsq_sendfrag（家族事件）**：tick=679525，parent=37，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 39 · tlb_translate（家族事件）**：tick=679525，parent=38，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 44 · lsq_push（家族事件）**：tick=686070，parent=36，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 45 · mem_req（L2 请求创建）**：tick=686070，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 46 · lsq_sendfrag（家族事件）**：tick=686070，parent=45，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 47 · tlb_translate（家族事件）**：tick=686070，parent=46，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 52 · lsq_push（家族事件）**：tick=775775，parent=44，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 53 · mem_req（L2 请求创建）**：tick=775775，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 54 · lsq_sendfrag（家族事件）**：tick=775775，parent=53，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 55 · tlb_translate（家族事件）**：tick=775775，parent=54，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 60 · lsq_push（家族事件）**：tick=782320，parent=52，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 61 · mem_req（L2 请求创建）**：tick=782320，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 62 · lsq_sendfrag（家族事件）**：tick=782320，parent=61，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 63 · tlb_translate（家族事件）**：tick=782320，parent=62，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 68 · lsq_push（家族事件）**：tick=788865，parent=60，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 69 · mem_req（L2 请求创建）**：tick=788865，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 70 · lsq_sendfrag（家族事件）**：tick=788865，parent=69，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 71 · tlb_translate（家族事件）**：tick=788865，parent=70，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 76 · lsq_push（家族事件）**：tick=789635，parent=68，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 77 · mem_req（L2 请求创建）**：tick=789635，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 78 · lsq_sendfrag（家族事件）**：tick=789635，parent=77，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 79 · tlb_translate（家族事件）**：tick=789635，parent=78，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 80 · lsq_push（家族事件）**：tick=889735，parent=76，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 81 · mem_req（L2 请求创建）**：tick=889735，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 82 · lsq_sendfrag（家族事件）**：tick=889735，parent=81，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 83 · tlb_translate（家族事件）**：tick=889735，parent=82，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 193 · lsq_push（家族事件）**：tick=11424490，parent=80，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 194 · mem_req（L2 请求创建）**：tick=11424490，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 195 · lsq_sendfrag（家族事件）**：tick=11424490，parent=194，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 196 · tlb_translate（家族事件）**：tick=11424490，parent=195，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 197 · lsq_push（家族事件）**：tick=11496100，parent=193，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 198 · mem_req（L2 请求创建）**：tick=11496100，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 199 · lsq_sendfrag（家族事件）**：tick=11496100，parent=198，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 200 · tlb_translate（家族事件）**：tick=11496100，parent=199，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 201 · lsq_push（家族事件）**：tick=11601590，parent=197，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 202 · mem_req（L2 请求创建）**：tick=11601590，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 203 · lsq_sendfrag（家族事件）**：tick=11601590，parent=202，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 204 · tlb_translate（家族事件）**：tick=11601590，parent=203，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 205 · lsq_push（家族事件）**：tick=11673585，parent=201，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 206 · mem_req（L2 请求创建）**：tick=11673585，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 207 · lsq_sendfrag（家族事件）**：tick=11673585，parent=206，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 208 · tlb_translate（家族事件）**：tick=11673585，parent=207，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 313 · lsq_push（家族事件）**：tick=13325620，parent=205，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 314 · mem_req（L2 请求创建）**：tick=13325620，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 315 · lsq_sendfrag（家族事件）**：tick=13325620，parent=314，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 316 · tlb_translate（家族事件）**：tick=13325620，parent=315，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 330 · lsq_push（家族事件）**：tick=13567400，parent=313，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 331 · mem_req（L2 请求创建）**：tick=13567400，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 332 · lsq_sendfrag（家族事件）**：tick=13567400，parent=331，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 333 · tlb_translate（家族事件）**：tick=13567400，parent=332，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 342 · lsq_push（家族事件）**：tick=13787620，parent=330，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 343 · mem_req（L2 请求创建）**：tick=13787620，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 344 · lsq_sendfrag（家族事件）**：tick=13787620，parent=343，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 345 · tlb_translate（家族事件）**：tick=13787620，parent=344，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 346 · lsq_push（家族事件）**：tick=14081375，parent=342，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 347 · mem_req（L2 请求创建）**：tick=14081375，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 348 · lsq_sendfrag（家族事件）**：tick=14081375，parent=347，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 349 · tlb_translate（家族事件）**：tick=14081375，parent=348，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 350 · store_not_retired（家族事件）**：tick=14825965，parent=13，corr=taint_prop，field=，before=，after=，state=response_seen_commit_absent→，contained=1，outcome=contained。
- **event 354 · chain_end（生命周期结束标记（非 L5 证据））**：tick=14825965，parent=346，corr=none，field=，before=，after=，state=→，contained=1，outcome=detected_contained。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`full`，provable_to=`L5`，admitted=`True`，certified=`True`
- 多 fault 样本：准入按 checker 的 escape-first 规则选择代表 fault；下表列出全部 fault 的各自终局（不合并、不跨 fault 拼接）：
  - fault `1`：terminal=`detected_contained`，provable_to=`L5`，event_count=`80`
  - fault `2`：terminal=`detected_contained`，provable_to=`L5`，event_count=`68`
  - fault `3`：terminal=`full`，provable_to=`L5`，event_count=`78`
  - fault `4`：terminal=`provable_to_L4_then_unknown`，provable_to=`L4`，event_count=`17`
  - fault `5`：terminal=`provable_to_L4_then_unknown`，provable_to=`L4`，event_count=`119`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`provable_to_L4_then_unknown`，provable_to=`L4`，beyond=`Unknown`，event_count=`119`
- containment：layer=`L4`，later_layers_N/A=`['L5']`，reason=`S03-F5-W10 fault 1 显式含住：kind=squash_discarded field='load' detection_layer=L4 outcome=contained`
- containment metrics：`{'L4': {'kind': 'squash_discarded', 'field': 'load', 'outcome': 'contained', 'contained': '1', 'event_id': '19', 'tick': '661045'}}`
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_DETECT: layer=Hardware RAS contained=1 tick=14825965 ptag=5 reason=store_discarded_not_retired`
- guest checksum：`n/a`
- stats：
- `simTicks                                     14825965                       # Number of ticks simulated (Tick)`
- `simInsts                                         4917                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles            38510                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2/S03-F5-W10/seed2/prop_evt.txt.gz`：`593eefbcfa114ceb4e3d363b27cd31b1bf838a20b7d49bacf15c32562785cd71`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2/S03-F5-W10/chain_report.json`：`a2e1f68a42348920a313cdf456e470cde3efcd2ad853dc0f3c39e99a468654a1`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2/S03-F5-W10/seed2/chain_report.json`：`657300b83681718a1546f9976624efde08b4a62f019a2a3d8311d171d2ff3e1a`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2/S03-F5-W10/seed2/stats.txt`：`109c0ea2e045922819be27c63d94c182193ee255e1d724512d5a951c3be8ff5f`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2/S03-F5-W10/seed2/run.out`：`afcfc660f21cd00fd2e91ca024d79fa148ea8503bd796b945106aa2ac9ea3bed`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2/manifest.json`：`730e0f3106e8c66a8393352b4c1720af2a65fa619f4534204a9e01b9e95bb243`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2/S03-F5-W10/seed2/lsq_fwd_injections.log`：`60b13bfc7cf7a92ffeb885cb759c82cb04f54981fe82712ca1d0e81a89e892e8`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2 --cells S03-F5-W10 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W10_s2/S03-F5-W10/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/stream_chase --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F5 --lsqfwd_warmup_events 0 --lsqfwd_span_events 1000 --lsq_struct_mode byte_lane_skew --rng_seed 2 --chaos_propagation --prop_run_id S03-F5-W10 --prop_sample_run_id s2`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。
- S03-F5 实测路径：errant commit 后 guest 调用超大 mmap；gem5 的 VMA 断言已修为 guest-visible ENOMEM，因此 stats/gzip 完整、链路以真实 L5 收口。

