# FQ08-c / FP08 真实 gate 证据（2026-11-05 补齐）

构建：`CHAOS/gem5/build/ARM/gem5.opt`。

## FQ08-c：delayed wake 真实目标状态

新增可观测字段：`CHAOSIQ.cc` 在 Fire 分支保存
`wakeDependents(inst)` 的返回值并写 `woken=<n>`，退出汇总写
`CHAOS_IQ_COUNTS ... delayed_dependents_woken=<n>`。

| 场景 | 命令要点 | 真实输出 | 结论 |
|---|---|---|---|
| Fire 正例（woken>0） | `dep_chain_kernel`, wake_phase, phase=1, first_clock=5000 | `FIRED ... completed_sn=1469 woken=1`；`delayed_fired=1` | **通过**：目标 dependent ready 状态真实改变 |
| Fire 正例（另一负载） | `branchy_reduce`, phase=1..32, first_clock=5000 | `FIRED ... completed_sn=1493 woken=1` | **通过** |
| Fire 但无 dependent | `elemwise_fma_kernel`, first_clock=5000 | `FIRED ... completed_sn=1379 woken=0` | 诚实：Fire 分支执行但未改变 ready（不能声称 activated 目标变化） |
| squash 安全忽略 | `branchy_reduce`, first_clock=1000, phase=2..32；已有 `FQ08-C-GATE` | `IGNORED reason=ignore_squashed`；`activated=0` | **通过** |
| generation / 旧槽复用 | 多负载/相位扫描 | 未自然出现 `ignore_generation` | **BLOCKED**：真实样本未观测；host 测试证明判定顺序，不能冒充真实 |
| identity 不一致 | — | 不可自然触发（seq/tid 不可变） | **N/A**：仅 host/代码证据 |

证据目录：`runs/fsu-gates/FQ08-C-FIRE/`、`runs/fsu-gates/FQ08-C-GATE/`。

## FP08：rounding 原因分区与 fail-closed

`rounding_sub` 现在把每个 attempted 事件归入且只归入：
`applied` / `rejected_no_vec_dest` / `rejected_no_writable_dest` /
`rejected_nonfinite`；退出汇总写四个计数与 `CHAOS_ROUNDING_CONSERVED`。
拒绝日志有界（每原因前 8 条），避免 13 MB 级日志。

真实运行（`w1_fp_scalar_probe`, `--maxinsts 2000000`, rounding_sub fp64/lane64,
`--fpu_max_faults 20`）：

```
CHAOS_ROUNDING_ATTEMPTED=73
CHAOS_ROUNDING_APPLIED=20
CHAOS_ROUNDING_REJECTED_NO_VEC_DEST=38
CHAOS_ROUNDING_REJECTED_NO_WRITABLE_DEST=0
CHAOS_ROUNDING_REJECTED_NONFINITE=15
CHAOS_ROUNDING_CONSERVED=1
```

73 = 20 + 38 + 0 + 15，守恒成立。目录：
`runs/fsu-gates/FP08-ROUNDING-REASON/`。

### 不兼容组合运行前 fail closed（真实 panic，exit 134）

| 组合 | 结果 |
|---|---|
| rounding_sub + fma_weighted（fp64/lane64） | panic `roundingSub is incompatible with ...` |
| fpsr_suppress + fma_weighted | panic `fpsrSuppress is incompatible with ...` |
| fpsr_suppress + recurring_stuck | 同上 panic |

### 代理分类

`fpsr_suppress` 仍是“FPSR 不在 SE 架构模型中”的显式代理，
`rounding_sub` 仍是 1-ULP 结果代理；事件 `injection_site` 保留
`*_proxy` 标记。工具 PASS 与真实 L0–L5 链不会自动把它们升级为
硬件模型认证。

## 仍未闭合

- FQ08-c generation/free-reuse 的真实忽略样本（BLOCKED）。
- identity 真实负例（N/A）。
- fpsr_suppress 的架构 FPSR 观测仍为代理（不升级）。
