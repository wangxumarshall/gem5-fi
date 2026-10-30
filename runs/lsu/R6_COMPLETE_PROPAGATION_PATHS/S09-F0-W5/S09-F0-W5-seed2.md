# S09-F0-W5 seed2 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S09-F0-W5`；seed：`2`
- oracle：`Masked`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`74`；terminal：`full`；provable_to：`L5`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2`

## 2. 注入位置、地址、原值/新值与掩码

```
Cycle: 21975, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: byte_lane_skew, Vaddr: 0x496798, FwdSize: 8, ByteOffset: 1, Mask: 00000000, StoreSeq: 6012, SqIdx: 566, LoadSeq: 6018, LqIdx: 322
```
- 注入事件：`event_id=0`，tick=`8460375`，va=`496798`，field=`lsqfwd_forward`，before=``，after=``，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=7 eligible=7 injected=1 first_eligible_tick=556325 last_eligible_tick=15162455 fires=n/a no_effect=n/a (activated=W3-L0-layer)`
- 检测摘要：`CHAOS_DETECT: layer=None contained=0 tick=8461530 ptag=1 reason=errant_commit`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | inj | L0 | — | 8460375 | origin | lsqfwd_forward | — | — | — | — | — |
| 1 | sq_entry | L1 | 0 | 8460375 | seq_primary | store_entry | — | — | — | — | — |
| 2 | lsq_fwd | L2 | 1 | 8460375 | seq_primary | byte_lane_skew | store_data | fwd_corrupt:byte_lane_skew | — | — | — |
| 3 | resp | L3 | 2 | 8460375 | seq_primary | byte_lane_skew | — | — | — | — | — |
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
| 23 | consumer | L4 | 19 | 8517355 | taint_prop | — | — | — | — | — | — |
| 24 | consumer | L4 | 23 | 8518895 | taint_prop | — | — | — | — | — | — |
| 25 | consumer | L4 | 24 | 8518895 | taint_prop | — | — | — | — | — | — |
| 26 | consumer | L4 | 25 | 8518895 | taint_prop | — | — | — | — | — | — |
| 27 | consumer | L4 | 25 | 8518895 | taint_prop | — | — | — | — | — | — |
| 28 | consumer | L4 | 25 | 8518895 | taint_prop | — | — | — | — | — | — |
| 29 | consumer | L4 | 23 | 8754900 | taint_prop | — | — | — | — | — | — |
| 30 | consumer | L4 | 23 | 8756825 | taint_prop | — | — | — | — | — | — |
| 31 | consumer | L4 | 30 | 8757210 | taint_prop | — | — | — | — | — | — |
| 32 | consumer | L4 | 23 | 8757210 | taint_prop | — | — | — | — | — | — |
| 33 | consumer | L4 | 23 | 8757210 | taint_prop | — | — | — | — | — | — |
| 34 | consumer | L4 | 32 | 8757595 | taint_prop | — | — | — | — | — | — |
| 35 | consumer | L4 | 33 | 8757595 | taint_prop | — | — | — | — | — | — |
| 36 | consumer | L4 | 23 | 8757980 | taint_prop | — | — | — | — | — | — |
| 37 | consumer | L4 | 35 | 8757980 | taint_prop | — | — | — | — | — | — |
| 38 | consumer | L4 | 37 | 8758365 | taint_prop | — | — | — | — | — | — |
| 39 | consumer | L4 | 38 | 8811110 | taint_prop | — | — | — | — | — | — |
| 40 | consumer | L4 | 38 | 8811110 | taint_prop | — | — | — | — | — | — |
| 41 | consumer | L4 | 38 | 8811110 | taint_prop | — | — | — | — | — | — |
| 42 | consumer | L4 | 23 | 8811495 | taint_prop | — | — | — | — | — | — |
| 43 | consumer | L4 | 42 | 8811880 | taint_prop | — | — | — | — | — | — |
| 44 | consumer | L4 | 42 | 8811880 | taint_prop | — | — | — | — | — | — |
| 45 | consumer | L4 | 42 | 8811880 | taint_prop | — | — | — | — | — | — |
| 46 | consumer | L4 | 38 | 8811880 | taint_prop | — | — | — | — | — | — |
| 47 | consumer | L4 | 46 | 8812265 | taint_prop | — | — | — | — | — | — |
| 48 | consumer | L4 | 23 | 8812265 | taint_prop | — | — | — | — | — | — |
| 49 | consumer | L4 | 48 | 8812650 | taint_prop | — | — | — | — | — | — |
| 50 | consumer | L4 | 48 | 8812650 | taint_prop | — | — | — | — | — | — |
| 51 | consumer | L4 | 48 | 8812650 | taint_prop | — | — | — | — | — | — |
| 52 | consumer | L4 | 23 | 8813035 | taint_prop | — | — | — | — | — | — |
| 53 | consumer | L4 | 52 | 8872710 | taint_prop | — | — | — | — | — | — |
| 54 | consumer | L4 | 47 | 8986285 | taint_prop | — | — | — | — | — | — |
| 55 | consumer | L4 | 47 | 8986285 | taint_prop | — | — | — | — | — | — |
| 56 | consumer | L4 | 47 | 8986285 | taint_prop | — | — | — | — | — | — |
| 57 | consumer | L4 | 23 | 8994370 | taint_prop | — | — | — | — | — | — |
| 58 | consumer | L4 | 57 | 8994370 | taint_prop | — | — | — | — | — | — |
| 59 | consumer | L4 | 57 | 8994370 | taint_prop | — | — | — | — | — | — |
| 60 | consumer | L4 | 57 | 8994370 | taint_prop | — | — | — | — | — | — |
| 61 | consumer | L4 | 55 | 9101015 | taint_prop | — | — | — | — | — | — |
| 62 | consumer | L4 | 55 | 9101015 | taint_prop | — | — | — | — | — | — |
| 63 | consumer | L4 | 55 | 9101015 | taint_prop | — | — | — | — | — | — |
| 64 | consumer | L4 | 55 | 9164540 | taint_prop | — | — | — | — | — | — |
| 65 | consumer | L4 | 55 | 9298520 | taint_prop | — | — | — | — | — | — |
| 66 | consumer | L4 | 65 | 9298905 | taint_prop | — | — | — | — | — | — |
| 67 | consumer | L4 | 66 | 9299290 | taint_prop | — | — | — | — | — | — |
| 68 | consumer | L4 | 66 | 9299290 | taint_prop | — | — | — | — | — | — |
| 69 | consumer | L4 | 66 | 9299290 | taint_prop | — | — | — | — | — | — |
| 70 | consumer | L4 | 66 | 9300060 | taint_prop | — | — | — | — | — | — |
| 71 | consumer | L4 | 55 | 9359350 | taint_prop | — | — | — | — | — | — |
| 72 | chain_end | L5 | 71 | 19450585 | none | — | — | — | — | 1 | errant_commit_seen |

## 4. 逐步传播语义

- **event 0 · inj（L0 故障注入）**：tick=8460375，parent=（根），corr=origin，field=lsqfwd_forward，before=，after=，state=→，contained=，outcome=。
- **event 1 · sq_entry（L1 生产 store 的 SQ 表项（转发源））**：tick=8460375，parent=0，corr=seq_primary，field=store_entry，before=，after=，state=→，contained=，outcome=。
- **event 2 · lsq_fwd（L2 store→load 转发决策/传输）**：tick=8460375，parent=1，corr=seq_primary，field=byte_lane_skew，before=store_data，after=fwd_corrupt:byte_lane_skew，state=→，contained=，outcome=。
- **event 3 · resp（L3 数据响应）**：tick=8460375，parent=2，corr=seq_primary，field=byte_lane_skew，before=，after=，state=→，contained=，outcome=。
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
- **event 23 · consumer（L4 下游消费者）**：tick=8517355，parent=19，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 24 · consumer（L4 下游消费者）**：tick=8518895，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 25 · consumer（L4 下游消费者）**：tick=8518895，parent=24，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 26 · consumer（L4 下游消费者）**：tick=8518895，parent=25，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 27 · consumer（L4 下游消费者）**：tick=8518895，parent=25，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 28 · consumer（L4 下游消费者）**：tick=8518895，parent=25，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 29 · consumer（L4 下游消费者）**：tick=8754900，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 30 · consumer（L4 下游消费者）**：tick=8756825，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 31 · consumer（L4 下游消费者）**：tick=8757210，parent=30，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 32 · consumer（L4 下游消费者）**：tick=8757210，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 33 · consumer（L4 下游消费者）**：tick=8757210，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 34 · consumer（L4 下游消费者）**：tick=8757595，parent=32，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 35 · consumer（L4 下游消费者）**：tick=8757595，parent=33，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 36 · consumer（L4 下游消费者）**：tick=8757980，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 37 · consumer（L4 下游消费者）**：tick=8757980，parent=35，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 38 · consumer（L4 下游消费者）**：tick=8758365，parent=37，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 39 · consumer（L4 下游消费者）**：tick=8811110，parent=38，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 40 · consumer（L4 下游消费者）**：tick=8811110，parent=38，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 41 · consumer（L4 下游消费者）**：tick=8811110，parent=38，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 42 · consumer（L4 下游消费者）**：tick=8811495，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 43 · consumer（L4 下游消费者）**：tick=8811880，parent=42，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 44 · consumer（L4 下游消费者）**：tick=8811880，parent=42，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 45 · consumer（L4 下游消费者）**：tick=8811880，parent=42，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 46 · consumer（L4 下游消费者）**：tick=8811880，parent=38，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 47 · consumer（L4 下游消费者）**：tick=8812265，parent=46，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 48 · consumer（L4 下游消费者）**：tick=8812265，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 49 · consumer（L4 下游消费者）**：tick=8812650，parent=48，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 50 · consumer（L4 下游消费者）**：tick=8812650，parent=48，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 51 · consumer（L4 下游消费者）**：tick=8812650，parent=48，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 52 · consumer（L4 下游消费者）**：tick=8813035，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 53 · consumer（L4 下游消费者）**：tick=8872710，parent=52，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 54 · consumer（L4 下游消费者）**：tick=8986285，parent=47，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 55 · consumer（L4 下游消费者）**：tick=8986285，parent=47，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 56 · consumer（L4 下游消费者）**：tick=8986285，parent=47，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 57 · consumer（L4 下游消费者）**：tick=8994370，parent=23，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 58 · consumer（L4 下游消费者）**：tick=8994370，parent=57，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 59 · consumer（L4 下游消费者）**：tick=8994370，parent=57，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 60 · consumer（L4 下游消费者）**：tick=8994370，parent=57，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 61 · consumer（L4 下游消费者）**：tick=9101015，parent=55，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 62 · consumer（L4 下游消费者）**：tick=9101015，parent=55，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 63 · consumer（L4 下游消费者）**：tick=9101015，parent=55，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 64 · consumer（L4 下游消费者）**：tick=9164540，parent=55，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 65 · consumer（L4 下游消费者）**：tick=9298520，parent=55，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 66 · consumer（L4 下游消费者）**：tick=9298905，parent=65，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 67 · consumer（L4 下游消费者）**：tick=9299290，parent=66，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 68 · consumer（L4 下游消费者）**：tick=9299290，parent=66，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 69 · consumer（L4 下游消费者）**：tick=9299290，parent=66，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 70 · consumer（L4 下游消费者）**：tick=9300060，parent=66，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 71 · consumer（L4 下游消费者）**：tick=9359350，parent=55，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 72 · chain_end（生命周期结束标记（非 L5 证据））**：tick=19450585，parent=71，corr=none，field=，before=，after=，state=→，contained=1，outcome=errant_commit_seen。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`full`，provable_to=`L5`，admitted=`True`，certified=`True`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`full`，provable_to=`L5`，beyond=``，event_count=`74`
- containment：`n/a`（链路以 full/其他合法终局收口，或没有显式含住证据）
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_LSU_TRIGGER_ALARM: injector=CHAOSLSQFwd mode=EARLY_BIAS attempted=7 eligible=7 injected=1 fired_at=2 span=6 warmup=1 (observed eligible ran past the F0 draw window [1,6): span under-covers the golden stream = silent early bias, OR span == measured golden and the fault extended the stream past fired_at — adjudicate vs the uninjected golden measurement)`
- guest checksum：`1f4cbf14327717df`
- stats：
- `simTicks                                     19450585                       # Number of ticks simulated (Tick)`
- `simInsts                                         6170                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles            50522                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2/S09-F0-W5/seed2/prop_evt.txt.gz`：`6fc9e18b921f2f3d5216089983354da6697e3e6d95d65f67b5785d5ae319e23e`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2/S09-F0-W5/chain_report.json`：`aa3af91491cf37bdd6bc97d504000412794736b5fc491506b3c6dffd27f84530`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2/S09-F0-W5/seed2/chain_report.json`：`8d0267ee4df55da6567f1414a5671141a0f846c60801f2edd28b8de196a6ccbc`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2/S09-F0-W5/seed2/stats.txt`：`d0fd92a6b84c4c6bc6940dabf6b4e5f9641b308f490557abe9a3c2e1b9dce961`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2/S09-F0-W5/seed2/run.out`：`559d4081869d10bcf1caad93079fe87c396b66149c3c87dde032d2c85a16d869`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2/manifest.json`：`6cb1fb1a5fb37916de6f9de3da88c75312cfd6a83bfb1cdbefde9f8a61902e3c`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2/S09-F0-W5/seed2/lsq_fwd_injections.log`：`281ef765255fc31a8dd932f9cf36c6abee356c386879ad541496675af91899da`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2 --cells S09-F0-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S09-F0-W5_s2/S09-F0-W5/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/sq_forward --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 --lsqfwd_span_events 6 --lsq_struct_mode byte_lane_skew --rng_seed 2 --chaos_propagation --prop_run_id S09-F0-W5 --prop_sample_run_id s2`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。

