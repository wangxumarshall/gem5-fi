# S11-F0-W5 seed2 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S11-F0-W5`；seed：`2`
- oracle：`Masked`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`7`；terminal：`detected_contained`；provable_to：`L3`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2`

## 2. 注入位置、地址、原值/新值与掩码

```
Tick: 5814270, Site: lsq_pushRequest_PRE, mode=s11_store_lost, old_addr=0x490420, new_addr=0x490420, old_size=8, new_size=0, faults_injected: 1, isLoad=0, isStore=1, fault_field=size, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```
- 注入事件：`event_id=1`，tick=`5814270`，va=`490420`，field=``，before=`490420`，after=`490420`，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=779 eligible=417 injected=1 first_eligible_tick=140910 last_eligible_tick=5814270 fires=n/a no_effect=n/a (activated=W3-L0-layer)`
- 检测摘要：`n/a`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | inj | L0 | — | 5814270 | origin | — | 490420 | 490420 | — | — | — |
| 2 | addr_form | L1 | 1 | 5814270 | origin | — | 490420 | 490420 | — | — | — |
| 3 | request_suppressed | L2 | 2 | 5814270 | seq_primary | request_suppressed:empty_byte_enable | 8 | 0 | byte_enable_empty→— | — | — |
| 4 | sq_execute | L3 | 3 | 5814270 | seq_primary | — | — | — | issued→— | — | — |
| 5 | sq_complete | L3 | 4 | 5815810 | seq_primary | — | — | — | —→completed | — | — |
| 6 | store_lost_contained | L3 | 5 | 5815810 | seq_primary | store_completed_without_mem_request | — | — | —→completed_no_request | 1 | contained |
| 7 | chain_end | L5 | 6 | 19285805 | none | — | — | — | — | 0 | run_end |

## 4. 逐步传播语义

- **event 1 · inj（L0 故障注入）**：tick=5814270，parent=（根），corr=origin，field=，before=490420，after=490420，state=→，contained=，outcome=。
- **event 2 · addr_form（L1 地址/尺寸形成）**：tick=5814270，parent=1，corr=origin，field=，before=490420，after=490420，state=→，contained=，outcome=。
- **event 3 · request_suppressed（L2 请求形成被空 byte-enable 抑制）**：tick=5814270，parent=2，corr=seq_primary，field=request_suppressed:empty_byte_enable，before=8，after=0，state=byte_enable_empty→，contained=，outcome=。
- **event 4 · sq_execute（L3 store 执行）**：tick=5814270，parent=3，corr=seq_primary，field=，before=，after=，state=issued→，contained=，outcome=。
- **event 5 · sq_complete（L3 store 完成）**：tick=5815810，parent=4，corr=seq_primary，field=，before=，after=，state=→completed，contained=，outcome=。
- **event 6 · store_lost_contained（L3 store 完成但无任何内存事务（含住））**：tick=5815810，parent=5，corr=seq_primary，field=store_completed_without_mem_request，before=，after=，state=→completed_no_request，contained=1，outcome=contained。
- **event 7 · chain_end（生命周期结束标记（非 L5 证据））**：tick=19285805，parent=6，corr=none，field=，before=，after=，state=→，contained=0，outcome=run_end。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`detected_contained`，provable_to=`L3`，admitted=`True`，certified=`True`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`detected_contained`，provable_to=`L3`，beyond=``，event_count=`7`
- containment：layer=`L3`，later_layers_N/A=`['L4', 'L5']`，reason=`S11-F0-W5 fault 1 显式含住：kind=store_lost_contained field='store_completed_without_mem_request' detection_layer=L3 outcome=contained`
- containment metrics：`{'L3': {'kind': 'store_lost_contained', 'field': 'store_completed_without_mem_request', 'outcome': 'contained', 'contained': '1', 'event_id': '6', 'tick': '5815810'}}`
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_L0_DECLINE: pre_fired=1 pre_opclass=362 pre_invalid=0 post_fired=0 post_nochange=0 post_geomreject=0 trigger_injected=1`
- guest checksum：`1f4cbf14327717df`
- stats：
- `simTicks                                     19285805                       # Number of ticks simulated (Tick)`
- `simInsts                                         6152                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles            50094                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2/S11-F0-W5/seed2/prop_evt.txt.gz`：`bcf6cb73e40a0f6f06f067813dae7ad3d069224a7f7fd8e2e3d826b0cfa1b8b5`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2/S11-F0-W5/chain_report.json`：`bccdd8fccca001c02640d9b02b9bca9d6ad993fe6b720fee11284670f91cbcb7`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2/S11-F0-W5/seed2/chain_report.json`：`b9a3a6b37f212cffe03d2799522cc8764a96ecd882d0cd33fd6a308edb12a56b`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2/S11-F0-W5/seed2/stats.txt`：`625daf0122999da2b2a5615b3a5a7ca73b86240a69ba378df12fc4e4f3f9814c`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2/S11-F0-W5/seed2/run.out`：`0e56d1e7840545dfa0ce5d9998c04e04f2ab77989392690bd955322f11cfccf0`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2/manifest.json`：`83744a912df6f10d375c2a52bcd6d8fd57814491ec0cf64f11d5fcff1272a9c0`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2/S11-F0-W5/seed2/addrpath_injections.log`：`a4b7a6aa928243975822cf832f4d53eae1dfc1467b8a62992d78b281103300a2`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2 --cells S11-F0-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S11-F0-W5_s2/S11-F0-W5/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/sq_forward --cpu O3 --chaos_addrpath --addrpath_lsu_tier F0 --addrpath_warmup_events 0 --addrpath_span_events 1000 --agu_pre_mode s11_store_lost --addrpath_rng_seed 2 --chaos_propagation --prop_run_id S11-F0-W5 --prop_sample_run_id s2`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。
- S11-F0-W5 实测路径：PRE hook 把 size 置 0，addReq 不创建 Request；request_suppressed 是真实的 L2 观测，store_lost_contained 是真实的 L3 含住；L4/L5 为 N/A，没有伪造 mem_req/consumer。

