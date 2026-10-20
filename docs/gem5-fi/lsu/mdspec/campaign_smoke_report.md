# 正式 campaign 入口 smoke：CHAOSPropagation 全量接入证据

> 目的（用户指令 2026-10-20 第二轮）：证明传播证据可**由正式 campaign 入口产出**，
> 而非只有手工直驱 `lsu_proxy.py` 的特例。

## 变更

`tools/lsu_campaign.py`：
- 新增 `resolve_g5()`：`LSU_GEM5_BIN` 优先 → repo-root `build/ARM/gem5.opt`；
  二者皆缺则**响亮 SystemExit**（此前 `G5` 硬编码 repo-root，worktree 里根本不存在，
  且无任何提示）。
- 新增 `propagation_flags(runid, seed)`：每样本追加
  `--chaos_propagation --prop_run_id <RunID> --prop_sample_run_id s<seed>`；
  **SE 与 FS 两支命令都追加**。
- 测试 `tests/test_lsu_campaign_propagation.py`（RED 已证：HEAD 上
  `propagation_flags`/`resolve_g5` 均不存在）。

## 运行（正式入口，非直驱）

```
LSU_GEM5_BIN=<worktree>/CHAOS/gem5/build/ARM/gem5.opt \
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir runs/lsu/mdspec_campaign_smoke --cells <RunID> \
  --phase trial --max-seeds-per-cell 1 --max-parallel 1
```

## 实测结果

| RunID | campaign 自评 | 注入日志 | prop_evt.txt.gz | 事件数 | 链终局 | provable_to | beyond |
|---|---|---|---|---|---|---|---|
| A01-F0-W3 | activated=1 sdc=0 cons=OK | FUNNEL attempted/eligible=617, injected=1 | `seed1/prop_evt.txt.gz` | 6 | `detected_translation_outcome_pending` | L2 | Unknown |
| P01-F0-W8 | activated=1 sdc=0 cons=OK | `stride 64 -> 262208 (bit 18)` | `seed1/prop_evt.txt.gz` | 630 | `full` | L5 | （闭合） |

事件行**身份由 campaign 注入**：`kind=inj run_id=A01-F0-W3 sample_run_id=s1 …`
——`run_id`/`sample_run_id` 逐事件在案（规格表 11 要求）。

## 诚实说明

1. **A01 的 `truncated_stream=True`**：A01 注入后 guest 走 GenericPageTableFault
   中止（exit 134），退出回调不运行 → gz 无 trailer。这正是 CHAOSPropagation
   的崩溃可存活设计（逐节点 `Z_SYNC_FLUSH`），`lsu_prop_fields.read_events()`
   会抢救前缀并标记 truncated——**不是数据丢失**。
2. **A01 经 campaign 得到 `pending` 而非 `crash_translation_blocked`**：终局
   join 需要 L5 oracle，而 campaign 目前不把 `cell_results.json` 的 outcome
   回灌给 chain checker。chain checker 已支持 `--oracle-outcome`；若要
   campaign 端自动 join，属下一步增强（本轮未做，不虚报）。
3. P01 经正式入口得到与直驱一致的 `full/L5` 全链——**传播证据不再是直驱特例**。
