# FSU-FP04-F0-W4 seed1 attempt lineage

| attempt | status | 原因 |
|---|---|---|
| attempt-1 | superseded | 发射端 v1 的 `unit="FSU Pipe"` 含空格，被 PROP-EVT 解析截断；`fault_mask` 未在 C++ 扩展字段表中而被丢弃；`activated` 被 L3/L4 重复计数为 3。原始证据保留，未修改，不作为权威。 |
| attempt-2 | **authoritative** | 修复后重跑：`unit=FSU_Pipe`、`fault_mask` 落盘、`activated=1`（仅 L2），审计 `certified=true`。 |

- `AUTHORITATIVE` 指向 `attempt-2`。
- `attempt-1` 未被删除、未被覆盖；其原始 `prop_evt`/`stats`/`run.out`/`run.err`/注入日志保持不变。
