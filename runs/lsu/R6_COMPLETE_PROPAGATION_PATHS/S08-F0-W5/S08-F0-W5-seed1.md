# S08-F0-W5 seed1 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S08-F0-W5`；seed：`1`
- oracle：`Masked`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`55`；terminal：`full`；provable_to：`L5`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1`

## 2. 注入位置、地址、原值/新值与掩码

```
Cycle: 38831, Site: store->load_forward_decision, FaultType: fwd_source_sub, Vaddr: 0x7ffffefc30, TrueSrcSize: 8, AltSrcSize: 8, Copied: 8, faults_injected: 1
```
- 注入事件：`event_id=0`，tick=`14949935`，va=`7ffffefc30`，field=`fwd_source_sub`，before=``，after=``，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=1 eligible=1 injected=1 first_eligible_tick=14949935 last_eligible_tick=14949935 fires=n/a no_effect=n/a (activated=W3-L0-layer)`
- 检测摘要：`CHAOS_DETECT: layer=None contained=0 tick=14951090 ptag=1 reason=errant_commit`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | inj | L0 | — | 14949935 | origin | fwd_source_sub | — | — | — | — | — |
| 1 | sq_entry | L1 | 0 | 14949935 | seq_primary | store_entry | — | — | — | — | — |
| 2 | lsq_fwd | L2 | 1 | 14949935 | seq_primary | fwd_source_sub | store_data | fwd_corrupt:fwd_source_sub | — | — | — |
| 3 | resp | L3 | 2 | 14949935 | seq_primary | fwd_source_sub | — | — | — | — | — |
| 4 | taint_reg | L4 | 3 | 14949935 | seq_primary | — | clean | tainted | — | — | — |
| 5 | sq_writeback | L3 | 4 | 14950705 | seq_primary | — | — | — | —→packet_built | — | — |
| 6 | errant_commit | L5 | 5 | 14951090 | taint_prop | — | — | — | — | 0 | errant_commit |
| 7 | sq_complete | L3 | 6 | 14951475 | seq_primary | — | — | — | —→completed | — | — |
| 8 | consumer | L4 | 4 | 15175930 | taint_prop | — | — | — | — | — | — |
| 9 | lsq_push | L1 | 8 | 16251620 | addr_fallback | store | — | — | — | — | — |
| 4294967296 | request_fork | — | 4 | 16251620 | addr_fallback | — | — | — | — | — | — |
| 10 | mem_req | L2 | 4294967296 | 16251620 | addr_fallback | — | — | — | — | — | — |
| 11 | lsq_sendfrag | L2 | 10 | 16251620 | addr_fallback | store | — | — | — | — | — |
| 12 | tlb_translate | L2 | 11 | 16251620 | addr_fallback | — | — | — | — | — | — |
| 13 | lsq_push | L1 | 9 | 16258165 | addr_fallback | store | — | — | — | — | — |
| 4294967297 | request_fork | — | 4 | 16258165 | addr_fallback | — | — | — | — | — | — |
| 14 | mem_req | L2 | 4294967297 | 16258165 | addr_fallback | — | — | — | — | — | — |
| 15 | lsq_sendfrag | L2 | 14 | 16258165 | addr_fallback | store | — | — | — | — | — |
| 16 | tlb_translate | L2 | 15 | 16258165 | addr_fallback | — | — | — | — | — | — |
| 17 | lsq_push | L1 | 13 | 16264710 | addr_fallback | store | — | — | — | — | — |
| 4294967298 | request_fork | — | 4 | 16264710 | addr_fallback | — | — | — | — | — | — |
| 18 | mem_req | L2 | 4294967298 | 16264710 | addr_fallback | — | — | — | — | — | — |
| 19 | lsq_sendfrag | L2 | 18 | 16264710 | addr_fallback | store | — | — | — | — | — |
| 20 | tlb_translate | L2 | 19 | 16264710 | addr_fallback | — | — | — | — | — | — |
| 21 | lsq_push | L1 | 17 | 16271255 | addr_fallback | store | — | — | — | — | — |
| 4294967299 | request_fork | — | 4 | 16271255 | addr_fallback | — | — | — | — | — | — |
| 22 | mem_req | L2 | 4294967299 | 16271255 | addr_fallback | — | — | — | — | — | — |
| 23 | lsq_sendfrag | L2 | 22 | 16271255 | addr_fallback | store | — | — | — | — | — |
| 24 | tlb_translate | L2 | 23 | 16271255 | addr_fallback | — | — | — | — | — | — |
| 25 | lsq_push | L1 | 21 | 16277800 | addr_fallback | store | — | — | — | — | — |
| 4294967300 | request_fork | — | 4 | 16277800 | addr_fallback | — | — | — | — | — | — |
| 26 | mem_req | L2 | 4294967300 | 16277800 | addr_fallback | — | — | — | — | — | — |
| 27 | lsq_sendfrag | L2 | 26 | 16277800 | addr_fallback | store | — | — | — | — | — |
| 28 | tlb_translate | L2 | 27 | 16277800 | addr_fallback | — | — | — | — | — | — |
| 29 | lsq_push | L1 | 25 | 16284345 | addr_fallback | store | — | — | — | — | — |
| 4294967301 | request_fork | — | 4 | 16284345 | addr_fallback | — | — | — | — | — | — |
| 30 | mem_req | L2 | 4294967301 | 16284345 | addr_fallback | — | — | — | — | — | — |
| 31 | lsq_sendfrag | L2 | 30 | 16284345 | addr_fallback | store | — | — | — | — | — |
| 32 | tlb_translate | L2 | 31 | 16284345 | addr_fallback | — | — | — | — | — | — |
| 33 | lsq_push | L1 | 29 | 16290890 | addr_fallback | store | — | — | — | — | — |
| 4294967302 | request_fork | — | 4 | 16290890 | addr_fallback | — | — | — | — | — | — |
| 34 | mem_req | L2 | 4294967302 | 16290890 | addr_fallback | — | — | — | — | — | — |
| 35 | lsq_sendfrag | L2 | 34 | 16290890 | addr_fallback | store | — | — | — | — | — |
| 36 | tlb_translate | L2 | 35 | 16290890 | addr_fallback | — | — | — | — | — | — |
| 37 | lsq_push | L1 | 33 | 16293200 | addr_fallback | store | — | — | — | — | — |
| 4294967303 | request_fork | — | 4 | 16293200 | addr_fallback | — | — | — | — | — | — |
| 38 | mem_req | L2 | 4294967303 | 16293200 | addr_fallback | — | — | — | — | — | — |
| 39 | lsq_sendfrag | L2 | 38 | 16293200 | addr_fallback | store | — | — | — | — | — |
| 40 | tlb_translate | L2 | 39 | 16293200 | addr_fallback | — | — | — | — | — | — |
| 41 | lsq_push | L1 | 37 | 16367120 | addr_fallback | store | — | — | — | — | — |
| 4294967304 | request_fork | — | 4 | 16367120 | addr_fallback | — | — | — | — | — | — |
| 42 | mem_req | L2 | 4294967304 | 16367120 | addr_fallback | — | — | — | — | — | — |
| 43 | lsq_sendfrag | L2 | 42 | 16367120 | addr_fallback | store | — | — | — | — | — |
| 44 | tlb_translate | L2 | 43 | 16367120 | addr_fallback | — | — | — | — | — | — |
| 45 | chain_end | L5 | 41 | 19190325 | none | — | — | — | — | 1 | errant_commit_seen |

## 4. 逐步传播语义

- **event 0 · inj（L0 故障注入）**：tick=14949935，parent=（根），corr=origin，field=fwd_source_sub，before=，after=，state=→，contained=，outcome=。
- **event 1 · sq_entry（L1 生产 store 的 SQ 表项（转发源））**：tick=14949935，parent=0，corr=seq_primary，field=store_entry，before=，after=，state=→，contained=，outcome=。
- **event 2 · lsq_fwd（L2 store→load 转发决策/传输）**：tick=14949935，parent=1，corr=seq_primary，field=fwd_source_sub，before=store_data，after=fwd_corrupt:fwd_source_sub，state=→，contained=，outcome=。
- **event 3 · resp（L3 数据响应）**：tick=14949935，parent=2，corr=seq_primary，field=fwd_source_sub，before=，after=，state=→，contained=，outcome=。
- **event 4 · taint_reg（L4 污点进入目的寄存器）**：tick=14949935，parent=3，corr=seq_primary，field=，before=clean，after=tainted，state=→，contained=，outcome=。
- **event 5 · sq_writeback（家族事件）**：tick=14950705，parent=4，corr=seq_primary，field=，before=，after=，state=→packet_built，contained=，outcome=。
- **event 6 · errant_commit（L5 错误提交（逃逸））**：tick=14951090，parent=5，corr=taint_prop，field=，before=，after=，state=→，contained=0，outcome=errant_commit。
- **event 7 · sq_complete（L3 store 完成）**：tick=14951475，parent=6，corr=seq_primary，field=，before=，after=，state=→completed，contained=，outcome=。
- **event 8 · consumer（L4 下游消费者）**：tick=15175930，parent=4，corr=taint_prop，field=，before=，after=，state=→，contained=，outcome=。
- **event 9 · lsq_push（家族事件）**：tick=16251620，parent=8，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967296 · request_fork（家族事件）**：tick=16251620，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 10 · mem_req（L2 请求创建）**：tick=16251620，parent=4294967296，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 11 · lsq_sendfrag（家族事件）**：tick=16251620，parent=10，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 12 · tlb_translate（家族事件）**：tick=16251620，parent=11，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 13 · lsq_push（家族事件）**：tick=16258165，parent=9，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967297 · request_fork（家族事件）**：tick=16258165，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 14 · mem_req（L2 请求创建）**：tick=16258165，parent=4294967297，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 15 · lsq_sendfrag（家族事件）**：tick=16258165，parent=14，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 16 · tlb_translate（家族事件）**：tick=16258165，parent=15，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 17 · lsq_push（家族事件）**：tick=16264710，parent=13，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967298 · request_fork（家族事件）**：tick=16264710，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 18 · mem_req（L2 请求创建）**：tick=16264710，parent=4294967298，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 19 · lsq_sendfrag（家族事件）**：tick=16264710，parent=18，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 20 · tlb_translate（家族事件）**：tick=16264710，parent=19，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 21 · lsq_push（家族事件）**：tick=16271255，parent=17，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967299 · request_fork（家族事件）**：tick=16271255，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 22 · mem_req（L2 请求创建）**：tick=16271255，parent=4294967299，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 23 · lsq_sendfrag（家族事件）**：tick=16271255，parent=22，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 24 · tlb_translate（家族事件）**：tick=16271255，parent=23，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 25 · lsq_push（家族事件）**：tick=16277800，parent=21，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967300 · request_fork（家族事件）**：tick=16277800，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 26 · mem_req（L2 请求创建）**：tick=16277800，parent=4294967300，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 27 · lsq_sendfrag（家族事件）**：tick=16277800，parent=26，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 28 · tlb_translate（家族事件）**：tick=16277800，parent=27，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 29 · lsq_push（家族事件）**：tick=16284345，parent=25，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967301 · request_fork（家族事件）**：tick=16284345，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 30 · mem_req（L2 请求创建）**：tick=16284345，parent=4294967301，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 31 · lsq_sendfrag（家族事件）**：tick=16284345，parent=30，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 32 · tlb_translate（家族事件）**：tick=16284345，parent=31，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 33 · lsq_push（家族事件）**：tick=16290890，parent=29，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967302 · request_fork（家族事件）**：tick=16290890，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 34 · mem_req（L2 请求创建）**：tick=16290890，parent=4294967302，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 35 · lsq_sendfrag（家族事件）**：tick=16290890，parent=34，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 36 · tlb_translate（家族事件）**：tick=16290890，parent=35，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 37 · lsq_push（家族事件）**：tick=16293200，parent=33，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967303 · request_fork（家族事件）**：tick=16293200，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 38 · mem_req（L2 请求创建）**：tick=16293200，parent=4294967303，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 39 · lsq_sendfrag（家族事件）**：tick=16293200，parent=38，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 40 · tlb_translate（家族事件）**：tick=16293200，parent=39，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 41 · lsq_push（家族事件）**：tick=16367120，parent=37，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 4294967304 · request_fork（家族事件）**：tick=16367120，parent=4，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 42 · mem_req（L2 请求创建）**：tick=16367120，parent=4294967304，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 43 · lsq_sendfrag（家族事件）**：tick=16367120，parent=42，corr=addr_fallback，field=store，before=，after=，state=→，contained=，outcome=。
- **event 44 · tlb_translate（家族事件）**：tick=16367120，parent=43，corr=addr_fallback，field=，before=，after=，state=→，contained=，outcome=。
- **event 45 · chain_end（生命周期结束标记（非 L5 证据））**：tick=19190325，parent=41，corr=none，field=，before=，after=，state=→，contained=1，outcome=errant_commit_seen。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`full`，provable_to=`L5`，admitted=`True`，certified=`True`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`full`，provable_to=`L5`，beyond=``，event_count=`55`
- containment：`n/a`（链路以 full/其他合法终局收口，或没有显式含住证据）
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_LSU_F6_EVENTS: TlbHit=0 SqForward=1120 DirtyEviction=1707 CasSuccess=2448`
- guest checksum：`1f4cbf14327717df`
- stats：
- `simTicks                                     19190325                       # Number of ticks simulated (Tick)`
- `simInsts                                         6152                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles            49846                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1/S08-F0-W5/seed1/prop_evt.txt.gz`：`113f0ee7966d8e40a1980969d16f1abc3574a7a381927a7d6f7347d572fcf54d`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1/S08-F0-W5/chain_report.json`：`81ae68a4fae36032b075181c0f46d6b53dc24dfb3bed16baece5b12a11829e9b`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1/S08-F0-W5/seed1/chain_report.json`：`8a181889c3ba1a60c7c3c00db6699fd4d380fc8fdc24f7fc2450bba02d3bac23`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1/S08-F0-W5/seed1/stats.txt`：`61d2b9c68b0890844316f3c43b586d6cf044c8b2ccfd42c70daaaebec50fc88e`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1/S08-F0-W5/seed1/run.out`：`dc8a86bbdaa8b0cbdf8457c12366241510dc8c9d83fd8f205f537202edb7d1ce`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1/manifest.json`：`d9e85dffc8f05fe2d2df3d2926f1cf3f413b4492a4a7d4d36289e5706c53457c`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1/S08-F0-W5/seed1/lsq_fwd_injections.log`：`0691ff1610193a87c4a5e0a943b67ab38dbf3f639e245f72cee7deb330427b10`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1 --cells S08-F0-W5 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S08-F0-W5_s1/S08-F0-W5/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/sq_forward --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 --lsqfwd_span_events 1 --lsq_struct_mode fwd_source_sub --rng_seed 1 --chaos_propagation --prop_run_id S08-F0-W5 --prop_sample_run_id s1`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。

