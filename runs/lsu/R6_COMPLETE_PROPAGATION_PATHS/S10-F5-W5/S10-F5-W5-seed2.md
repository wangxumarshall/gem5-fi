# S10-F5-W5 seed2 传播链（R6-S-REPAIR2）

> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 `prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / 注入日志逐字段生成；未合成任何事件、id、tick 或值。

## 1. 单元与实验定义

- RunID：`S10-F5-W5`；seed：`2`
- oracle：`Masked`；exit_code：`0`
- 二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`
- 源码 HEAD：`43d1bb0833e59559366fdb2d5254d77b0b139351`
- 事件数：`5`；terminal：`detected_contained`；provable_to：`L2`
- admitted：`True`；certified：`True`；truncated：`False`
- 证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2`

## 2. 注入位置、地址、原值/新值与掩码

```
Tick: 3216290, Site: StoreSet_violation_ssid_assign, mode=ssid_subst (S10-a SSIT-ID 换值), old_ssid=485, new_ssid=530, store_pc=0x40c900, load_pc=0x40b5c8, ssid_candidates=1, faults_injected: 1
```
- 注入事件：`event_id=0`，tick=`3216290`，va=``，field=`ssid`，before=`485`，after=`530`，corr=`origin`
- 触发摘要：`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F5 attempted=2 eligible=1 injected=1 first_eligible_tick=3216290 last_eligible_tick=3216290 fires=1 no_effect=0 (activated=W3-L0-layer)`
- 检测摘要：`n/a`

## 3. 事件总览（该 fault 的完整事件流）

| event_id | kind | layer | parent | tick | corr | field | before | after | state | contained | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | inj | L0 | — | 3216290 | origin | ssid | 485 | 530 | — | — | — |
| 1 | ssit_corrupt | L1 | 0 | 3216290 | origin | ssid | 485 | 530 | — | — | — |
| 2 | ssit_consult | L2 | 1 | 3220525 | origin | pred_dep | 0 | 0 | — | — | — |
| 3 | ssit_no_effect | L2 | 2 | 3220525 | origin | pred_dep_unchanged | 0 | 0 | — | 1 | contained |
| 4 | chain_end | L5 | 3 | 19190325 | none | — | — | — | — | 0 | run_end |

## 4. 逐步传播语义

- **event 0 · inj（L0 故障注入）**：tick=3216290，parent=（根），corr=origin，field=ssid，before=485，after=530，state=→，contained=，outcome=。
- **event 1 · ssit_corrupt（L1 SSIT 字段被替换）**：tick=3216290，parent=0，corr=origin，field=ssid，before=485，after=530，state=→，contained=，outcome=。
- **event 2 · ssit_consult（L2 依赖预测查询读取污染 SSIT）**：tick=3220525，parent=1，corr=origin，field=pred_dep，before=0，after=0，state=→，contained=，outcome=。
- **event 3 · ssit_no_effect（L2 查询到污染状态但预测未改变（真实含住））**：tick=3220525，parent=2，corr=origin，field=pred_dep_unchanged，before=0，after=0，state=→，contained=1，outcome=contained。
- **event 4 · chain_end（生命周期结束标记（非 L5 证据））**：tick=19190325，parent=3，corr=none，field=，before=，after=，state=→，contained=0，outcome=run_end。

## 5. 终局判定（权威 checker）

- 样本级 judge：terminal=`detected_contained`，provable_to=`L2`，admitted=`True`，certified=`True`
- 叙述 fault `1`（本 seed 事件数最多者）：terminal=`detected_contained`，provable_to=`L2`，beyond=``，event_count=`5`
- containment：layer=`L2`，later_layers_N/A=`['L3', 'L4', 'L5']`，reason=`S10-F5-W5 fault 1 显式含住：kind=ssit_no_effect field='pred_dep_unchanged' detection_layer=L2 outcome=contained`
- containment metrics：`{'L2': {'kind': 'ssit_no_effect', 'field': 'pred_dep_unchanged', 'outcome': 'contained', 'contained': '1', 'event_id': '3', 'tick': '3220525'}}`
- admission violations：`[]`

## 6. 对 guest / 程序的实际表现

- run.out 末行：`CHAOS_LSU_S10_FORK: injector=CHAOSLSQFwd attempted=2 eligible=1 arm1_events=2 arm1_cand_empty=1 arm1_cand_ok=1 max_live_ssids=1 max_cands=1 distinct_arm1_load_pcs=2`
- guest checksum：`1f4cbf14327717df`
- stats：
- `simTicks                                     19190325                       # Number of ticks simulated (Tick)`
- `simInsts                                         6152                       # Number of instructions simulated (Count)`
- `board.processor.cores.core.numCycles            49846                       # Number of cpu cycles simulated (Cycle)`


## 7. 证据路径与 SHA-256

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2/S10-F5-W5/seed2/prop_evt.txt.gz`：`febd6c99ff5ac10b0cef77195b8e03570dd62f753a98616a3c4e67ab4808c936`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2/S10-F5-W5/chain_report.json`：`116bf3f281bca3fcfcb92c86c72bdd0a8f54f6b02f4d79b2894a1651fd66b80f`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2/S10-F5-W5/seed2/chain_report.json`：`e82bab8902ad1a7ab92aa907f407c5083ce7b6ab9bbed37c40e5da03bebab216`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2/S10-F5-W5/seed2/stats.txt`：`c8c5a5accac0106ed6760c4e4bb930761dc5f9791da21ea91422f2f639c3f0af`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2/S10-F5-W5/seed2/run.out`：`9fc2a81be032300f160783b0a11d12fc695c0416c23d0917d705774a0e2899f9`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2/manifest.json`：`103e1312f1ae7e34e5e4a5c5856b459490dad949981cecf590a026a32d31881d`
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2/S10-F5-W5/seed2/lsq_fwd_injections.log`：`1224088b4e320787646ea1c369bef465b9fca91b7d2acfa6411215216c743b52`

## 8. 可复现命令与诚实边界

```bash
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt \
  python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2 --cells S10-F5-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600
```
- 完整 gem5 命令行：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/S10-F5-W5_s2/S10-F5-W5/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/configs/se/lsu_proxy.py --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/workloads/directed/sq_forward --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F5 --lsqfwd_warmup_events 0 --lsqfwd_span_events 1000 --lsqfwd_s10 --rng_seed 2 --chaos_propagation --prop_run_id S10-F5-W5 --prop_sample_run_id s2`
- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... 的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。 `chain_end` 是生命周期标记，从不充当 L5 证据。
- S10 实测路径：污染 SSIT 被真实 consult 读取，counterfactual 预测与 actual 预测相等（before==after），因此终局是 L2 detected containment；L3/L4/L5 为 N/A，没有伪造 violation/replay/commit。

