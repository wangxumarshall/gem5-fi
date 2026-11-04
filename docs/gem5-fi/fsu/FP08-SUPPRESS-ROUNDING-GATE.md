# FP08 `fpsr_suppress` / `rounding_sub` gate 结果

> 日期：2026-11-04。gate 证据在 `runs/fsu-gates/FP08-GATE/` 与
> `runs/fsu-gates/FP08-FPSR-GATE/`；不计 519，不产生正式 seed。

## 1. 修复内容

| 路径 | 修复 |
|---|---|
| `fpsr_suppress` | 分别累计 `fpsr_attempted/fpsr_applied/suppressed_count`；每次发射 `suppress` 事件（`reason=fpsr_not_architecturally_modeled`）；退出时输出四个 `CHAOS_FPSR_*` 计数 |
| `rounding_sub` | 早退路径改为在完成 1-ULP 改动后调用 `noteFaultApplied`，产生真实 L0/L1；累计 `rounding_attempted/applied`，退出时输出 `CHAOS_ROUNDING_*` |
| runner | `fpu_mode.fpsr_suppress` → `--fpu_fpsr_suppress` |

两者均明确标注为代理边界（`injection_site=fpsr_suppress_proxy` /
`rounding_sub_one_ulp_proxy`），门禁闭合前不产生正式认证。

## 2. 真实 gem5 结果

### 2.1 fpsr_suppress（W1 FP32，真实运行）

```
CHAOS_FPSR_ATTEMPTED=174018
CHAOS_FPSR_APPLIED=174018
CHAOS_FPSR_SUPPRESSED=174018
CHAOS_FPSR_REASON=fpsr_not_architecturally_modeled
```

守恒：`attempted == applied == suppressed`。该模式不改变架构状态，仅证明
每次 eligible 事件都进入了被清晰标注的占位路径。

### 2.2 rounding_sub（W1 FP64，真实 gem5 gate）

`runs/fsu-gates/FP08-GATE/FSU-FP08-F0-W1-ROUNDING-GATE/seed1/attempt-2`：

- `fault_applied` 根：`field=rounding_sub`、
  `injection_site=rounding_sub_one_ulp_proxy`、`phys_reg=45`、
  `before=0x0`、`after=0x1`（真实 1-ULP nudge）；
- `CHAOS_ROUNDING_ATTEMPTED=357`、`CHAOS_ROUNDING_APPLIED=1`
  （`max_faults=1` 后停止，计数如实）；
- 链 `full`、oracle `SDC`，`fsu_seed_audit` 通过。

## 3. 结论

FP08 的两个早退路径已有真实、可复算的 attempted/applied/suppressed 证据，
不再是静默计数。FP08 仍是 **代理模型**；在专门的预注册正式 RunID 与
完整 L0–L5 认证规则确定前，不新增正式 seed。
