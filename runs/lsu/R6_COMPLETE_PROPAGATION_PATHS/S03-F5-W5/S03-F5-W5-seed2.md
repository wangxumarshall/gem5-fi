# S03-F5-W5 seed2 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S03-F5-W5`；seed：`2`
- oracle：`Crash`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`323`；terminal：`full`；provable_to：`L5`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2`

## 2. 注入位置、地址、原值/新值与掩码

```
Cycle: 1445, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: byte_lane_skew, Vaddr: 0x7ffffefc68, FwdSize: 8, ByteOffset: 1, Mask: 00000000, StoreSeq: 383, SqIdx: 49, LoadSeq: 397, LqIdx: 15
Cycle: 21975, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: byte_lane_skew, Vaddr: 0x496798, FwdSize: 8, ByteOffset: 1, Mask: 00000000, StoreSeq: 6012, SqIdx: 566, LoadSeq: 6018, LqIdx: 322
Cycle: 23360, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: byte_lane_skew, Vaddr: 0x7ffffeeb30, FwdSize: 8, ByteOffset: 1, Mask: 00000000, StoreSeq: 6297, SqIdx: 579, LoadSeq: 6312, LqIdx: 337
Cycle: 33298, CPU: board.processor.cores.core, Site: store->load_forward, FaultType: byte_lane_skew, Vaddr: 0x48fb70, FwdSize: 8, ByteOffset: 1, Mask: 00000000, StoreSeq: 10126, SqIdx: 798, LoadSeq: 10129, LqIdx: 587
```
- 注入事件：`event_id=0`，tick=`556325`，va=`7ffffefc68`，field=`lsqfwd_forward`，before=``，after=``，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F5 attempted=4 eligible=4 injected=4 first_eligible_tick=556325 last_eligible_tick=12819730 fires=4 no_effect=0 (activated=W3-L0-layer)`
- 检测摘要：`CHAOS_DETECT: layer=None contained=0 tick=8461530 ptag=2 reason=errant_commit`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | inj | L0 | — | 556325 | origin | lsqfwd_forward | — | — | — | — | — |
| 1 | sq_entry | L1 | 0 | 556325 | seq_primary | store_entry | — | — | — | — | — |
| 2 | lsq_fwd | L2 | 1 | 556325 | seq_primary | byte_lane_skew | store_data | fwd_corrupt:byte_lane_skew | — | — | — |
| 3 | resp | L3 | 2 | 556325 | seq_primary | byte_lane_skew | — | — | — | — | — |
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
| 112 | lsq_push | L1 | 22 | 10719170 | addr_fallback | store | — | — | — | — | — |
| 113 | mem_req | L2 | — | 10719170 | addr_fallback | — | — | — | — | — | — |
| 114 | lsq_sendfrag | L2 | 113 | 10719170 | addr_fallback | store | — | — | — | — | — |
| 115 | tlb_translate | L2 | 114 | 10719170 | addr_fallback | — | — | — | — | — | — |
| 116 | lsq_push | L1 | 112 | 10944010 | addr_fallback | load | — | — | — | — | — |
| 117 | mem_req | L2 | — | 10944010 | addr_fallback | — | — | — | — | — | — |
| 118 | lsq_sendfrag | L2 | 117 | 10944010 | addr_fallback | load | — | — | — | — | — |
| 119 | tlb_translate | L2 | 118 | 10944010 | addr_fallback | — | — | — | — | — | — |
| 120 | lsq_push | L1 | 116 | 10950555 | addr_fallback | store | — | — | — | — | — |
| 121 | mem_req | L2 | — | 10950555 | addr_fallback | — | — | — | — | — | — |
| 122 | lsq_sendfrag | L2 | 121 | 10950555 | addr_fallback | store | — | — | — | — | — |
| 123 | tlb_translate | L2 | 122 | 10950555 | addr_fallback | — | — | — | — | — | — |
| 124 | lsq_push | L1 | 120 | 10965185 | addr_fallback | load | — | — | — | — | — |
| 125 | mem_req | L2 | — | 10965185 | addr_fallback | — | — | — | — | — | — |
| 126 | lsq_sendfrag | L2 | 125 | 10965185 | addr_fallback | load | — | — | — | — | — |
| 127 | tlb_translate | L2 | 126 | 10965185 | addr_fallback | — | — | — | — | — | — |
| 128 | lsq_push | L1 | 124 | 11049885 | addr_fallback | store | — | — | — | — | — |
| 129 | mem_req | L2 | — | 11049885 | addr_fallback | — | — | — | — | — | — |
| 130 | lsq_sendfrag | L2 | 129 | 11049885 | addr_fallback | store | — | — | — | — | — |
| 131 | tlb_translate | L2 | 130 | 11049885 | addr_fallback | — | — | — | — | — | — |
| 132 | lsq_push | L1 | 128 | 11695530 | addr_fallback | load | — | — | — | — | — |
| 133 | mem_req | L2 | — | 11695530 | addr_fallback | — | — | — | — | — | — |
| 134 | lsq_sendfrag | L2 | 133 | 11695530 | addr_fallback | load | — | — | — | — | — |
| 135 | tlb_translate | L2 | 134 | 11695530 | addr_fallback | — | — | — | — | — | — |
| 136 | lsq_push | L1 | 132 | 11698995 | addr_fallback | store | — | — | — | — | — |
| 137 | mem_req | L2 | — | 11698995 | addr_fallback | — | — | — | — | — | — |
| 138 | lsq_sendfrag | L2 | 137 | 11698995 | addr_fallback | store | — | — | — | — | — |
| 139 | tlb_translate | L2 | 138 | 11698995 | addr_fallback | — | — | — | — | — | — |
| 140 | lsq_push | L1 | 136 | 11713625 | addr_fallback | load | — | — | — | — | — |
| 141 | mem_req | L2 | — | 11713625 | addr_fallback | — | — | — | — | — | — |
| 142 | lsq_sendfrag | L2 | 141 | 11713625 | addr_fallback | load | — | — | — | — | — |
| 143 | tlb_translate | L2 | 142 | 11713625 | addr_fallback | — | — | — | — | — | — |
| 144 | lsq_push | L1 | 140 | 11744040 | addr_fallback | store | — | — | — | — | — |
| 145 | mem_req | L2 | — | 11744040 | addr_fallback | — | — | — | — | — | — |
| 146 | lsq_sendfrag | L2 | 145 | 11744040 | addr_fallback | store | — | — | — | — | — |
| 147 | tlb_translate | L2 | 146 | 11744040 | addr_fallback | — | — | — | — | — | — |
| 148 | lsq_push | L1 | 144 | 11776765 | addr_fallback | load | — | — | — | — | — |
| 149 | mem_req | L2 | — | 11776765 | addr_fallback | — | — | — | — | — | — |
| 150 | lsq_sendfrag | L2 | 149 | 11776765 | addr_fallback | load | — | — | — | — | — |
| 151 | tlb_translate | L2 | 150 | 11776765 | addr_fallback | — | — | — | — | — | — |
| 152 | lsq_push | L1 | 148 | 11783695 | addr_fallback | store | — | — | — | — | — |
| 153 | mem_req | L2 | — | 11783695 | addr_fallback | — | — | — | — | — | — |
| 154 | lsq_sendfrag | L2 | 153 | 11783695 | addr_fallback | store | — | — | — | — | — |
| 155 | tlb_translate | L2 | 154 | 11783695 | addr_fallback | — | — | — | — | — | — |
| 156 | lsq_push | L1 | 152 | 11792935 | addr_fallback | load | — | — | — | — | — |
| 157 | mem_req | L2 | — | 11792935 | addr_fallback | — | — | — | — | — | — |
| 158 | lsq_sendfrag | L2 | 157 | 11792935 | addr_fallback | load | — | — | — | — | — |
| 159 | tlb_translate | L2 | 158 | 11792935 | addr_fallback | — | — | — | — | — | — |
| 160 | lsq_push | L1 | 156 | 11840290 | addr_fallback | store | — | — | — | — | — |
| 161 | mem_req | L2 | — | 11840290 | addr_fallback | — | — | — | — | — | — |
| 162 | lsq_sendfrag | L2 | 161 | 11840290 | addr_fallback | store | — | — | — | — | — |
| 163 | tlb_translate | L2 | 162 | 11840290 | addr_fallback | — | — | — | — | — | — |
| 164 | lsq_push | L1 | 160 | 11849915 | addr_fallback | load | — | — | — | — | — |
| 165 | mem_req | L2 | — | 11849915 | addr_fallback | — | — | — | — | — | — |
| 166 | lsq_sendfrag | L2 | 165 | 11849915 | addr_fallback | load | — | — | — | — | — |
| 167 | tlb_translate | L2 | 166 | 11849915 | addr_fallback | — | — | — | — | — | — |
| 168 | lsq_push | L1 | 164 | 11961565 | addr_fallback | load | — | — | — | — | — |
| 169 | mem_req | L2 | — | 11961565 | addr_fallback | — | — | — | — | — | — |
| 170 | lsq_sendfrag | L2 | 169 | 11961565 | addr_fallback | load | — | — | — | — | — |
| 171 | tlb_translate | L2 | 170 | 11961565 | addr_fallback | — | — | — | — | — | — |
| 172 | lsq_push | L1 | 168 | 12411245 | addr_fallback | store | — | — | — | — | — |
| 173 | mem_req | L2 | — | 12411245 | addr_fallback | — | — | — | — | — | — |
| 174 | lsq_sendfrag | L2 | 173 | 12411245 | addr_fallback | store | — | — | — | — | — |
| 175 | tlb_translate | L2 | 174 | 12411245 | addr_fallback | — | — | — | — | — | — |
| 176 | lsq_push | L1 | 172 | 12756205 | addr_fallback | load | — | — | — | — | — |
| 177 | mem_req | L2 | — | 12756205 | addr_fallback | — | — | — | — | — | — |
| 178 | lsq_sendfrag | L2 | 177 | 12756205 | addr_fallback | load | — | — | — | — | — |
| 179 | tlb_translate | L2 | 178 | 12756205 | addr_fallback | — | — | — | — | — | — |
| 180 | lsq_push | L1 | 176 | 12818190 | addr_fallback | load | — | — | — | — | — |
| 181 | mem_req | L2 | — | 12818190 | addr_fallback | — | — | — | — | — | — |
| 182 | lsq_sendfrag | L2 | 181 | 12818190 | addr_fallback | load | — | — | — | — | — |
| 183 | tlb_translate | L2 | 182 | 12818190 | addr_fallback | — | — | — | — | — | — |
| 194 | lsq_push | L1 | 180 | 12822810 | addr_fallback | store | — | — | — | — | — |
| 195 | mem_req | L2 | — | 12822810 | addr_fallback | — | — | — | — | — | — |
| 196 | lsq_sendfrag | L2 | 195 | 12822810 | addr_fallback | store | — | — | — | — | — |
| 197 | tlb_translate | L2 | 196 | 12822810 | addr_fallback | — | — | — | — | — | — |
| 211 | lsq_push | L1 | 194 | 12833205 | addr_fallback | load | — | — | — | — | — |
| 212 | mem_req | L2 | — | 12833205 | addr_fallback | — | — | — | — | — | — |
| 213 | lsq_sendfrag | L2 | 212 | 12833205 | addr_fallback | load | — | — | — | — | — |
| 214 | tlb_translate | L2 | 213 | 12833205 | addr_fallback | — | — | — | — | — | — |
| 309 | lsq_push | L1 | 211 | 13757975 | addr_fallback | store | — | — | — | — | — |
| 310 | mem_req | L2 | — | 13757975 | addr_fallback | — | — | — | — | — | — |
| 311 | lsq_sendfrag | L2 | 310 | 13757975 | addr_fallback | store | — | — | — | — | — |
| 312 | tlb_translate | L2 | 311 | 13757975 | addr_fallback | — | — | — | — | — | — |
| 313 | store_not_retired | L4 | 7 | 14496790 | taint_prop | — | — | — | response_seen_commit_absent→— | 1 | contained |
| 316 | chain_end | L4 | 309 | 14496790 | none | — | — | — | — | 1 | detected_contained |

## 4. 逐步传播语义

- **event 0 · inj（L0 故障注入）**：tick=556325，parent=（根），corr=origin，field=lsqfwd_forward，before=，after=，state=→，contained=，outcome=。
- **event 1 · sq_entry（L1 生产 store 的 SQ 表项（转发源））**：tick=556325，parent=0，corr=seq_primary，field=store_entry，before=，after=，state=→，contained=，outcome=。
- **event 2 · lsq_fwd（L2 store→load 转发决策/传输）**：tick=556325，parent=1，corr=seq_primary，field=byte_lane_skew，before=store_data，after=fwd_corrupt:byte_lane_skew，state=→，contained=，outcome=。
- **event 3 · resp（L3 数据响应）**：tick=556325，parent=2，corr=seq_primary，field=byte_lane_skew，before=，after=，state=→，contained=，outcome=。
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
- **event 112 · lsq_push（家族事件）**：tick=10719170，parent=22，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 113 · mem_req（L2 请求创建）**：tick=10719170，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 114 · lsq_sendfrag（家族事件）**：tick=10719170，parent=113，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 115 · tlb_translate（家族事件）**：tick=10719170，parent=114，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 116 · lsq_push（家族事件）**：tick=10944010，parent=112，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 117 · mem_req（L2 请求创建）**：tick=10944010，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 118 · lsq_sendfrag（家族事件）**：tick=10944010，parent=117，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 119 · tlb_translate（家族事件）**：tick=10944010，parent=118，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 120 · lsq_push（家族事件）**：tick=10950555，parent=116，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 121 · mem_req（L2 请求创建）**：tick=10950555，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 122 · lsq_sendfrag（家族事件）**：tick=10950555，parent=121，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 123 · tlb_translate（家族事件）**：tick=10950555，parent=122，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 124 · lsq_push（家族事件）**：tick=10965185，parent=120，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 125 · mem_req（L2 请求创建）**：tick=10965185，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 126 · lsq_sendfrag（家族事件）**：tick=10965185，parent=125，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 127 · tlb_translate（家族事件）**：tick=10965185，parent=126，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 128 · lsq_push（家族事件）**：tick=11049885，parent=124，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 129 · mem_req（L2 请求创建）**：tick=11049885，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 130 · lsq_sendfrag（家族事件）**：tick=11049885，parent=129，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 131 · tlb_translate（家族事件）**：tick=11049885，parent=130，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 132 · lsq_push（家族事件）**：tick=11695530，parent=128，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 133 · mem_req（L2 请求创建）**：tick=11695530，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 134 · lsq_sendfrag（家族事件）**：tick=11695530，parent=133，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 135 · tlb_translate（家族事件）**：tick=11695530，parent=134，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 136 · lsq_push（家族事件）**：tick=11698995，parent=132，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 137 · mem_req（L2 请求创建）**：tick=11698995，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 138 · lsq_sendfrag（家族事件）**：tick=11698995，parent=137，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 139 · tlb_translate（家族事件）**：tick=11698995，parent=138，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 140 · lsq_push（家族事件）**：tick=11713625，parent=136，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 141 · mem_req（L2 请求创建）**：tick=11713625，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 142 · lsq_sendfrag（家族事件）**：tick=11713625，parent=141，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 143 · tlb_translate（家族事件）**：tick=11713625，parent=142，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 144 · lsq_push（家族事件）**：tick=11744040，parent=140，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 145 · mem_req（L2 请求创建）**：tick=11744040，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 146 · lsq_sendfrag（家族事件）**：tick=11744040，parent=145，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 147 · tlb_translate（家族事件）**：tick=11744040，parent=146，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 148 · lsq_push（家族事件）**：tick=11776765，parent=144，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 149 · mem_req（L2 请求创建）**：tick=11776765，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 150 · lsq_sendfrag（家族事件）**：tick=11776765，parent=149，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 151 · tlb_translate（家族事件）**：tick=11776765，parent=150，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 152 · lsq_push（家族事件）**：tick=11783695，parent=148，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 153 · mem_req（L2 请求创建）**：tick=11783695，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 154 · lsq_sendfrag（家族事件）**：tick=11783695，parent=153，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 155 · tlb_translate（家族事件）**：tick=11783695，parent=154，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 156 · lsq_push（家族事件）**：tick=11792935，parent=152，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 157 · mem_req（L2 请求创建）**：tick=11792935，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 158 · lsq_sendfrag（家族事件）**：tick=11792935，parent=157，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 159 · tlb_translate（家族事件）**：tick=11792935，parent=158，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 160 · lsq_push（家族事件）**：tick=11840290，parent=156，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 161 · mem_req（L2 请求创建）**：tick=11840290，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 162 · lsq_sendfrag（家族事件）**：tick=11840290，parent=161，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 163 · tlb_translate（家族事件）**：tick=11840290，parent=162，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 164 · lsq_push（家族事件）**：tick=11849915，parent=160，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 165 · mem_req（L2 请求创建）**：tick=11849915，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 166 · lsq_sendfrag（家族事件）**：tick=11849915，parent=165，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 167 · tlb_translate（家族事件）**：tick=11849915，parent=166，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 168 · lsq_push（家族事件）**：tick=11961565，parent=164，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 169 · mem_req（L2 请求创建）**：tick=11961565，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 170 · lsq_sendfrag（家族事件）**：tick=11961565，parent=169，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 171 · tlb_translate（家族事件）**：tick=11961565，parent=170，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 172 · lsq_push（家族事件）**：tick=12411245，parent=168，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 173 · mem_req（L2 请求创建）**：tick=12411245，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 174 · lsq_sendfrag（家族事件）**：tick=12411245，parent=173，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 175 · tlb_translate（家族事件）**：tick=12411245，parent=174，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 176 · lsq_push（家族事件）**：tick=12756205，parent=172，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 177 · mem_req（L2 请求创建）**：tick=12756205，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 178 · lsq_sendfrag（家族事件）**：tick=12756205，parent=177，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 179 · tlb_translate（家族事件）**：tick=12756205，parent=178，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 180 · lsq_push（家族事件）**：tick=12818190，parent=176，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 181 · mem_req（L2 请求创建）**：tick=12818190，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 182 · lsq_sendfrag（家族事件）**：tick=12818190，parent=181，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 183 · tlb_translate（家族事件）**：tick=12818190，parent=182，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 194 · lsq_push（家族事件）**：tick=12822810，parent=180，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 195 · mem_req（L2 请求创建）**：tick=12822810，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 196 · lsq_sendfrag（家族事件）**：tick=12822810，parent=195，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 197 · tlb_translate（家族事件）**：tick=12822810，parent=196，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 211 · lsq_push（家族事件）**：tick=12833205，parent=194，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 212 · mem_req（L2 请求创建）**：tick=12833205，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 213 · lsq_sendfrag（家族事件）**：tick=12833205，parent=212，corr=addr_fallback，field=load，before=，after=，state=→，contained=，outcome=。
- **event 214 · tlb_translate（家族事件）**：tick=12833205，parent=213，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 309 · lsq_push（家族事件）**：tick=13757975，parent=211，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 310 · mem_req（L2 请求创建）**：tick=13757975，parent=（根），corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 311 · lsq_sendfrag（家族事件）**：tick=13757975，parent=310，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 312 · tlb_translate（家族事件）**：tick=13757975，parent=311，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 313 · store_not_retired（家族事件）**：tick=14496790，parent=7，corr=taint_prop，field=，before=，after=，state=response_seen_commit_absent→，contained=1，outcome=contained。
- **event 316 · chain_end（生命周期结束标记（非 L5 证据））**：tick=14496790，parent=309，corr=none，field=，before=，after=，state=→，contained=1，outcome=detected_contained。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`full`，provable_to=`L5`，admitted=`True`，certified=`True`
- 多 fault 样本：准入按 checker 的 escape-first 规则选择代表 fault；下表列出全部 fault 的各自终局（不合并、不跨 fault 拼接）：
  - fault `1`：terminal=`detected_contained`，provable_to=`L5`，event_count=`112`
  - fault `2`：terminal=`full`，provable_to=`L5`，event_count=`83`
  - fault `3`：terminal=`provable_to_L4_then_unknown`，provable_to=`L4`，event_count=`17`
  - fault `4`：terminal=`provable_to_L4_then_unknown`，provable_to=`L4`，event_count=`111`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`detected_contained`，provable_to=`L5`，beyond=``，event_count=`112`
- containment：layer=`L4`，later_layers_N/A=`['L5']`，reason=`S03-F5-W5 fault 1 显式含住：kind=squash_discarded field='load' detection_layer=L4 outcome=contained`
- containment metrics：`{'L4': {'kind': 'squash_discarded', 'field': 'load', 'outcome': 'contained', 'contained': '1', 'event_id': '9', 'tick': '609840'}}`
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_DETECT: layer=Hardware RAS contained=1 tick=14496790 ptag=4 reason=store_discarded_not_retired`
- guest checksum：`n/a`
- stats：
- `simTicks                                     14496790                       # Number of ticks simulated (Tick)`
- `simInsts                                         4907                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles            37655                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2/S03-F5-W5/seed2/prop_evt.txt.gz`：`9251a72406b0176a94c189cd6289b1479d6d75b56f19d3933fca9625358b89bd`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2/S03-F5-W5/chain_report.json`：`36398dbd8d927d76fcc7b17e1595e019c5b70c42740520a986c95f55267a1844`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2/S03-F5-W5/seed2/chain_report.json`：`6e3146a1fb5f5d84d9ffc8940f9a03412986d6efd71f2102566bb5818f23ea1d`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2/S03-F5-W5/seed2/stats.txt`：`c48b206c58629967611109e4d6be9c3e26495c1f2682a383622362881c177d9f`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2/S03-F5-W5/seed2/run.out`：`238de2ec690d5f798428d76dd1d106443be53b1d6bae3d1d182b6e2aa4fc6a12`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2/manifest.json`：`323349aab04ace3642aa7d37bdda4396e0797300ec9d9b3374f9b2bf17e8dd07`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2/S03-F5-W5/seed2/lsq_fwd_injections.log`：`e979fd8341463a186b855a9a84d915f09c76d5e066fde9aebb70bbdd1a528978`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2 --cells S03-F5-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S03-F5-W5_s2/S03-F5-W5/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/sq_forward --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F5 --lsqfwd_warmup_events 0 --lsqfwd_span_events 1000 --lsq_struct_mode byte_lane_skew --rng_seed 2 --chaos_propagation --prop_run_id S03-F5-W5 --prop_sample_run_id s2`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。
- S03-F5 实测路径：errant commit 后 guest 调用超大 mmap；gem5 的 VMA 断言已修为 guest-visible ENOMEM，因此 stats/gzip 完整、链路以真实 L5 收口。

