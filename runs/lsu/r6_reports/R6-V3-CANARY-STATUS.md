# R6 V3 代表 canary 状态（2026-10-27）

> 本轮 11 个非 STOP 格的代表 canary。每格独立全新目录；最多并发 2 个 gem5。
> 冻结二进制：`binary_source_head=d1543872e155943893fdd6d18a489ff7c372d97d`，
> `binary_sha256=20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`。
> 本报告不补 seed2/seed3，不启动正式实验。

## 逐格结果

| 格 | 子模型 | 目录 | 注入 | 激活 | tier | chain terminal | admitted/certified | verdict |
|---|---|---|---|---|---|---|---|---|
| T10-F0-W4 | bit_flip | `runs/lsu/r6_v3_T10-F0-W4_s1` | 1（stats=1） | 1 | F0 / enabled=0 | full / L5 | True / True | **PASS** |
| T10-F1-W4 | bit_flip | `runs/lsu/r6_v3_T10-F1-W4_s1` | 1（stats=1） | 1 | F1 / enabled=1 | full / L5 | True / True | **PASS** |
| T10-F2-W4 | bit_flip | `runs/lsu/r6_v3_T10-F2-W4_s1` | 5（stats=5） | 5 | F2 / enabled=1 | full / L5 | True / True | **PASS** |
| T05-F0-W4 | valid_clear | `runs/lsu/r6_v3_T05-F0-W4_s1` | 1（stats=0） | **0** | F0 / enabled=0 | detected_contained / L2 | True / True | **FAIL_NO_ACTIVATION** |
| T06-F0-W4 | perm_subst | `runs/lsu/r6_v3_T06-F0-W4_s1` | 1（stats=0） | **0** | F0 / enabled=0 | detected_contained / L2 | True / True | **FAIL_NO_ACTIVATION** |
| T07-F0-W4 | false_hit | `runs/lsu/r6_v3_T07-F0-W4_s1` | 1（stats=0） | 1 | F0 / enabled=0 | provable_to_L2_then_unknown | **False / False** | **FAIL_TIMEOUT_OPEN_CHAIN** |
| T08-F0-W4 | walk_pairing（T08-a） | `runs/lsu/r6_v3_T08-F0-W4_s1` | 1（stats=1） | 1 | F0 / enabled=1（walk 流） | detected_contained / L2 | True / True | **PASS（仅 T08-a）** |

## 关键事实

### T10（F0/F1/F2 W4）
- 三次运行均真实注入、campaign 激活、完整 L5 链、`violations=[]`、EOF 正常、stats 与注入日志一致。
- T10-F0：`attempted=150162`, `eligible=56`, activated=1, outcome=Crash。
- T10-F1：`attempted=150162`/`eligible=1390245`（campaign funnel 记录异常：attempted 与 eligible 同值；链和注入证据不受影响），activated=1。
- T10-F2：`attempted=560166`, activated=5；per-fault：1 full + 2 L2 contained + 2 open L4，代表 fault 1 为 full/L5。
- 因此 T10 三格 seed1 达到各自允许状态（PASS）。

### T05-F0-W4（valid_clear）
- 注入日志：`old_valid_clear: 1 -> 0`，`injected=1`, `eligible=56`，真实注入。
- 但 campaign `activated=0`、`stats.numFaultsInjected=0`、`count_contradiction=true`；
  `CHAOS_DETECT ... contained=1 reason=effective_pa_unchanged`，链为 L2 containment（admitted/certified）。
- **判定 FAIL_NO_ACTIVATION**：注入和含住存在，但没有达到该子模型的 activation 口径；不宣称已激活，也不补 seed2/3。

### T06-F0-W4（perm_subst）
- 注入日志：`old_perm_subst: 2 -> 0`，`injected=1`, `eligible=66`。
- 同样 `activated=0`、`stats.numFaultsInjected=0`、`count_contradiction=true`；L2 containment（admitted/certified）。
- **判定 FAIL_NO_ACTIVATION**。

### T07-F0-W4（false_hit）
- 注入日志：`CAM: miss -> hit`，真实注入。
- 运行到 `fs_timeout=5400s` 被 graceful timeout 终止；`attempted=0/eligible=0` 而 `injected=1`（计数矛盾）；
  链止于 `provable_to_L2_then_unknown`，admitted=False/certified=False，无 containment；
  `violations` 明确点名 `no_closed_chain_and_no_containment`。
- **判定 FAIL_TIMEOUT_OPEN_CHAIN**：不能作为 T07 可跑证据；不补 seed2/3。

### T08-F0-W4（walk_pairing，T08-a 代表）
- 注入日志：`arm_tlb_walk_issue_drop walk_id=703`；prop_evt 的 `tlb_walk`(event 2) 与 `tlb_refill`(event 3)
  共享 `walk_id=703`，refill `field=lost`；`stats.numFaultsInjected=1`。
- campaign activated=1；链 `detected_contained/L2`，admitted+certified，violations=[]。
- **只能记 `PARTIAL_SUBMODEL_PROVEN`（T08-a）**；T08-b/c/d 无动态覆盖，T08 整体不是 COMPLETE。

## 推进边界

- T10：三格 seed1 已 PASS，可继续相应 F 档位 seed1（本轮未补 seed2/seed3）。
- T05/T06/T07：代表 canary 未通过，**停在 seed1 失败证据**，不补 seed2/3，不启动正式实验。
- T08-W4：仅 `PARTIAL_SUBMODEL_PROVEN`，不宣称 T08 完整；T08-W9 继续 `BLOCKED_WORKLOAD_GAP`，未运行。
- 无 C++/构建输入修改；复用冻结二进制 `20fda699…`。
- 每格 manifest 见 `R6-V3-CANARY-<RunID>-seed1.json`（含 run_id/seed/submodel/workload/readfile/command/binary SHA/source head/analysis head/PID-PGID/log/.done/exit_code/链与注入字段）。
