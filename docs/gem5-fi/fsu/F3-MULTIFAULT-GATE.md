# F3 多故障机制门禁（短 W4，seed1）

> 注（2026-11-03）：本文为门禁快照，门禁证据不计入正式 seed。正式
> F3-W4 三 seed 已完成；当前状态见 `COVERAGE_STATUS.md` 与
> `FP04-W4-FREQUENCY-CLOSEOUT.md`。
>
> 生成时间：2026-11-02。门禁目的：在正式 W4-rate-v1 三 seed 之前，证明
> F3 真实 rate ordinal 能产生**多个独立 fault**，每个 fault 有独立 L0 root
> 和闭合主链，且逐 fault Markdown/审计不会因单个 fault 达 L5 而误认证全部。
> 本门禁**不是**正式 RunID 三 seed 运行，不计入 3/519。

## 1. 身份

| 项 | 值 |
|---|---|
| RunID（门禁专用） | `FSU-FP04-F3-W4-GATE` |
| manifest | `configs/fsu/FSU-FP04-F3-W4-GATE.json`（SHA-256 `dd341db71a84debe19c529d927199fcf36d8927d39b070e2f1b78197d960704e`） |
| 源码 HEAD | `60b6c6f3646d5cb658b0db96c325e50e90361f47` |
| gem5 二进制 | `CHAOS/gem5/build/ARM/gem5.opt` |
| gem5 SHA-256 | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`（权威 -j4 构建 tag `20261102T211141`） |
| workload | 短 W4 `workloads/directed/elemwise_fma_kernel`（SHA-256 `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97`） |
| model / submodel | FP04 / FP04-c（mant_lo） |
| freq | F3（rate divisor 10,000，jitter ±50%，warmup 0） |
| seed / sample_run_id | 1 / `s1` |
| 权威 attempt | `runs/fsu-gates/F3-multifault-gate-final/FSU-FP04-F3-W4-GATE/seed1/attempt-1` |

> 早先的 `runs/fsu-gates/F3-multifault-gate/.../attempt-1` 保留为历史证据；
> 本报告使用 hardened 逐 fault 文档/审计后的新 attempt，未覆盖旧目录。

## 2. rate ordinal（真实语义）

- eligible census：`CHAOS_ELIGIBLE_COUNT = 57,347`
- generator：`splitmix64-mod-uniform-interval` v1
- interval 边界：`[5000, 15000]`
- ordinals：`[11004, 24122, 34278, 48713]`
- intervals：`[11004, 13118, 10156, 14435]`
- ordinals SHA-256：`2e5b7546da9616a5d99b0160a483607bcf172bfd580ccd6ecb630b988f1ae122`
- 实际注入数 = 期望注入数 = 4；每个 ordinal 精确命中一次。

## 3. 事件链（原始 PROP-EVT，28 事件，gzip 未截断）

| fault | L0 root event | root parent | eligible_ordinal | interval | ordinal_index | 主链 event_id | terminal |
|---|---|---|---|---|---|---|---|
| 1 | `0` | 空（独立 root） | 11,004 | 11,004 | 0 | `0,1,2,3,4,5,24` | full |
| 2 | `6` | 空（独立 root） | 24,122 | 13,118 | 1 | `6,7,8,9,10,11,25` | full |
| 3 | `12` | 空（独立 root） | 34,278 | 10,156 | 2 | `12,13,14,15,16,17,26` | full |
| 4 | `18` | 空（独立 root） | 48,713 | 14,435 | 3 | `18,19,20,21,22,23,27` | full |

每个 fault 的主链均为：

```
fault_applied(L0) -> carrier_state(L1) -> operand_read(L2)
  -> execute(L3) -> prf_writeback(L4) -> commit(L5) -> chain_end(生命周期)
```

- `chain_end` 不占 L0–L5，不是 L5 见证。
- 4 个 L0 root 的 `parent_event_id` 均为空；fault_id 1/2/3/4 互不相同；
  路径事件集合互不共享（0–5/24、6–11/25、12–17/26、18–23/27）。
- 每个 fault 的 `commit` 事件均为 `detection_layer=L5`、`outcome=errant_commit`。

## 4. run-level oracle 与逐 fault terminal（分开记录）

- **run-level oracle**：`SDC`。程序完整退出（exit 0），
  `ARRAYHASH=db3b3dfa483d3d93c47b30482674fb5165cdf7698590069bccd18dbd520b3fab`
  ≠ golden `ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7`。
- **逐 fault terminal**：`{1: full, 2: full, 3: full, 4: full}`。
- run-level oracle 表示整个程序的结局；每个 fault 的 terminal 表示该 fault
  自身传播链的闭合情况。二者不互相替代。

## 5. 审计结果（逐 fault）

`audit.json`：

| 字段 | 值 |
|---|---|
| ok | true |
| certified | true |
| fault_count | 4 |
| all_faults_admitted | true |
| all_faults_certified | true |
| fault_terminals | `{1: full, 2: full, 3: full, 4: full}` |
| gzip_eof_ok | true |
| event_count | 28 |
| identity_ok | true |
| cross_seed_ok | true |

逐 fault：4/4 均 `admitted=true`、`certified=true`、`direct_parent_chain=true`、
`tick_monotonic=true`、`layers=[L0..L5]`、`violations=[]`。

负向门禁（单测 `tests/test_fsu_rate_ordinals.py`）：

- 篡改某个 fault 的 Markdown terminal → audit 失败；
- 删除某个 fault 的一条主链事件 → audit 失败；
- 某个 fault 为 `not_activated` → seed `certified=false`、不得 admitted、
  不进入 `AUTHORITATIVE` / `COMPLETE_PROPAGATION_PATHS`。

## 6. 证据文件 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `c28e3768c5d5f48e54cbde15c2f090c788441cfaca1b2eaf8a259e8ca024d3d4` |
| `ordinals.json` | `2e5b7546da9616a5d99b0160a483607bcf172bfd580ccd6ecb630b988f1ae122` |
| `oracle.json` | `c6a156b55f0b02f6445c5941a0b8a47c8b0ddcb8ff220831e4550a425c431c59` |
| `chain_report.json` | `57aabc59766cb1737cf16399aabea0a625f244072b072e0648fa5b9edcfc3e21` |
| `audit.json` | `32d7001efcc21937f4c0da30ed849e11566dcd784db8ef2a6eaf9919bef8134b` |
| `audit.md` | `dc7a0b7d99b15423ebeb29f4c9a854e894295f9e2d3b6f79fd07f71563277911` |
| `inject/prop_evt.txt.gz` | `80e855a72e6bcc52f8943c13212e872a64af3bba94a0967110674c0007332063` |
| `inject/fpu_injections.log` | `fffbc5da680dd958176a126d744702d746737f376f95337677756d7ed94d915c` |
| `stats.txt` | `d5890184d75166599738e3763bb64cdf533b81e3d069152d2f4470ad0447eecf` |
| seed Markdown | `e8f6d8e7f3360da1ebe0bc92b704251a72bbfb67c71d16b2f337d6661cad5ea1` |

原始目录：`runs/fsu-gates/F3-multifault-gate-final/FSU-FP04-F3-W4-GATE/seed1/attempt-1/`。
提交内的只读副本：`docs/gem5-fi/fsu/evidence/f3-multifault-gate/`。

## 7. 结论与边界

- **F3 多 fault 机制门禁通过**：4 个独立 fault、4 条独立 L0–L5 主链、
  逐 fault Markdown、逐 fault 审计、run-level oracle 分离。
- **不**代表 F3-W4 三 seed 完成；正式 F1/F2/F3-W4 使用 W4-rate-v1，
  尚未启动。当前 seed 总数仍为 **3/519**。
- 门禁使用短 W4 是为了机制验证；W4-rate-v1 的 N=2,097,155 及预注册
  ordinals 见 `docs/gem5-fi/fsu/W4-RATE-V1.md`。
