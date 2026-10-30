# S10-F0-W9 seed3 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S10-F0-W9`；seed：`3`
- oracle：`Masked`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`5`；terminal：`detected_contained`；provable_to：`L2`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3`

## 2. 注入位置、地址、原值/新值与掩码

```
Tick: 3838065, Site: StoreSet_violation_ssid_assign, mode=ssid_subst (S10-a SSIT-ID 换值), old_ssid=392, new_ssid=933, store_pc=0x40ca8c, load_pc=0x40c1b8, ssid_candidates=3, faults_injected: 1
```
- 注入事件：`event_id=0`，tick=`3838065`，va=``，field=`ssid`，before=`392`，after=`933`，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=4 eligible=3 injected=1 first_eligible_tick=3208205 last_eligible_tick=3838065 fires=n/a no_effect=n/a (activated=W3-L0-layer)`
- 检测摘要：`n/a`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | inj | L0 | — | 3838065 | origin | ssid | 392 | 933 | — | — | — |
| 1 | ssit_corrupt | L1 | 0 | 3838065 | origin | ssid | 392 | 933 | — | — | — |
| 2 | ssit_consult | L2 | 1 | 3841915 | origin | pred_dep | 0 | 0 | — | — | — |
| 3 | ssit_no_effect | L2 | 2 | 3841915 | origin | pred_dep_unchanged | 0 | 0 | — | 1 | contained |
| 4 | chain_end | L5 | 3 | 325381980 | none | — | — | — | — | 0 | run_end |

## 4. 逐步传播语义

- **event 0 · inj（L0 故障注入）**：tick=3838065，parent=（根），corr=origin，field=ssid，before=392，after=933，state=→，contained=，outcome=。
- **event 1 · ssit_corrupt（L1 SSIT 字段被替换）**：tick=3838065，parent=0，corr=origin，field=ssid，before=392，after=933，state=→，contained=，outcome=。
- **event 2 · ssit_consult（L2 依赖预测查询读取污染 SSIT）**：tick=3841915，parent=1，corr=origin，field=pred_dep，before=0，after=0，state=→，contained=，outcome=。
- **event 3 · ssit_no_effect（L2 查询到污染状态但预测未改变（真实含住））**：tick=3841915，parent=2，corr=origin，field=pred_dep_unchanged，before=0，after=0，state=→，contained=1，outcome=contained。
- **event 4 · chain_end（生命周期结束标记（非 L5 证据））**：tick=325381980，parent=3，corr=none，field=，before=，after=，state=→，contained=0，outcome=run_end。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`detected_contained`，provable_to=`L2`，admitted=`True`，certified=`True`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`detected_contained`，provable_to=`L2`，beyond=``，event_count=`5`
- containment：layer=`L2`，later_layers_N/A=`['L3', 'L4', 'L5']`，reason=`S10-F0-W9 fault 1 显式含住：kind=ssit_no_effect field='pred_dep_unchanged' detection_layer=L2 outcome=contained`
- containment metrics：`{'L2': {'kind': 'ssit_no_effect', 'field': 'pred_dep_unchanged', 'outcome': 'contained', 'contained': '1', 'event_id': '3', 'tick': '3841915'}}`
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_LSU_S10_FORK: injector=CHAOSLSQFwd attempted=4 eligible=3 arm1_events=4 arm1_cand_empty=1 arm1_cand_ok=3 max_live_ssids=3 max_cands=3 distinct_arm1_load_pcs=4`
- guest checksum：`030921682b3731f2`
- stats：
- `simTicks                                    325381980                       # Number of ticks simulated (Tick)`
- `simInsts                                      1093665                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles           845149                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3/S10-F0-W9/seed3/prop_evt.txt.gz`：`ff3e95bb97859184b1965b21296e3683f8455d5b139a837529565d8ab41210d3`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3/S10-F0-W9/chain_report.json`：`e9b22cf1f70cd149a817197de39b0e7d239c03279b29bffad632f00159003c71`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3/S10-F0-W9/seed3/chain_report.json`：`3d12358fb9d058f92c72b6b3cf75dd47212b633d5ee89620dd6490b6dd209035`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3/S10-F0-W9/seed3/stats.txt`：`21958896e2b2d92c676e96bf7dcca1cea491110b980060ddbb7a0a6924fcc581`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3/S10-F0-W9/seed3/run.out`：`ecafdbf62563101bc6f46276dd5aec5e28fe9539dbb38fc7454ba33aedbfb450`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3/manifest.json`：`d3c4fe326abb8d91679a06e28fde5c964a2c969d02e07a096eae5528116e6ab2`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3/S10-F0-W9/seed3/lsq_fwd_injections.log`：`9d896d3148f71c8adc0e3e357161c45f68b870d49613a2dbc53b11eabf42da3a`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3 --cells S10-F0-W9 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F0-W9_s3/S10-F0-W9/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/gap_bfs --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 --lsqfwd_span_events 4 --lsqfwd_s10 --rng_seed 3 --chaos_propagation --prop_run_id S10-F0-W9 --prop_sample_run_id s3`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。
- S10 实测路径：污染 SSIT 被真实 consult 读取，counterfactual 预测与 actual 预测相等（before==after），因此终局是 L2 detected containment；L3/L4/L5 为 N/A，没有伪造 violation/replay/commit。

