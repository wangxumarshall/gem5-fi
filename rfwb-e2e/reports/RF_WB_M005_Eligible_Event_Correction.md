# RF/WB M005 Eligible-Event Correction

日期：2026-11-24
第二轮基线：`2f4e00b4`

## 1. 修正定义

M005 eligible event 必须同时满足：

1. 生产者已经真实 WB。
2. 指定消费者在该 WB 之后才执行 Rename。
3. 消费者源绑定的 PhysRegId 与故障生产者相同。

旧 Batch01 预扫描把每个 Producer WB 都计为 N；这是错误的。Rename-before-WB
事件不属于 M005 的 `WB-before-Rename` 激活条件。

## 2. 逐事件重建方法

从 Batch02 `traces/SCAN-M005-*.csv` 读取：

- `M005_WB`：tick、producer seq、PhysRegId；
- `M005_CONSUMER_RENAME`：tick、consumer seq、source PhysRegId、global/iq ready。

按同一 PhysRegId 和实际事件顺序配对；同 tick 时使用 CSV 行顺序（真实事件顺序），
不单凭 tick 数值判断。

## 3. 修正结果

| Context | Producer WB | WB-before-Rename (N) | Rename-before-WB | T01 | T02 | T03 |
|---|---:|---:|---:|---:|---:|---:|
| C01 | 8 | 6 | 2 | 1 | 3 | 6 |
| C02 | 8 | 6 | 2 | 1 | 3 | 6 |
| C03 | 8 | 8 | 0 | 1 | 4 | 8 |
| C04 | 8 | 6 | 2 | 1 | 3 | 6 |
| C05 | 8 | 8 | 0 | 1 | 4 | 8 |

逐事件配对明细：`results/M005_Paired_Producer_Consumer_Audit.tsv`。
修正 N/ordinal：`results/corrected_prescan_summary.tsv`。

## 4. 修正后 Target Sequences

| Context | Eligible Producer Sequences |
|---|---|
| C01 | 14798, 14844, 14880, 14920, 14956, 15028 |
| C02 | 14834, 14889, 14925, 14992, 15028, 15100 |
| C03 | 14867, 14918, 14955, 15000, 15037, 15074, 15111, 15148 |
| C04 | 14913, 14965, 15003, 15041, 15079, 15155 |
| C05 | 14907, 14963, 15011, 15059, 15107, 15155, 15203, 15251 |

六个修正 Timing 样本在 Batch03 实际使用 AttemptID `-A3`（Batch02 历史为 A2）：

- `RFWB-M005-C01-T02-F0-A3` target seq 14880
- `RFWB-M005-C01-T03-F0-A3` target seq 15028
- `RFWB-M005-C02-T02-F0-A3` target seq 14925
- `RFWB-M005-C02-T03-F0-A3` target seq 15100
- `RFWB-M005-C04-T02-F0-A3` target seq 15003
- `RFWB-M005-C04-T03-F0-A3` target seq 15155

旧 Batch01 对应样本保留在 `Batch01/`，标记为 `INVALID_TIMING_RANK_FOR_M005`。

## 5. 因果关联修正

第二轮 `RFWB::skipGlobalReady()` 在首次选中时锁定
`FaultProducerSeq/FaultProducerPhysReg/FaultTick`；后续 `onRenameSrc()`、
`onIQRepair()`、`onScalarRead()` 均使用锁定对象，而不是不断更新的
`producerReg`。

修正后 trace 示例（C01-T02-A3）：

- `M005_WB seq=14880 phys=10`
- `M005_SKIP_GLOBAL_READY seq=14880`
- `M005_CONSUMER_RENAME seq=14905 phys=10 global=0 iq=1 target=1`
- `M005_IQ_REPAIR seq=14905 phys=10 target=1`
- `M005_CONSUMER_READ seq=14905 phys=10 value=42`
- `M005_CONSUMER_COMMIT seq=14905`

这证明的是 IQ 独立 scoreboard 补标，不是全局 ready 恢复。
