# FP06-F5-W1 gate（非正式，不计 519/240）

- 生成时间：2026-11-03T22:59:01
- 证据目录：`runs/fsu-gates/F5-FP06-W1-v2`
- 结论：**FAIL**

| gate | eligible | oracle | audit.ok | certified | 结论 |
|---|---|---|---|---|---|
| FP32-SIGN | 41216 | SDC | True | True | FAIL |
| FP64-SIGN | 41216 | SDC | True | True | FAIL |
| FP32-MANT | 41216 | SDC | True | True | FAIL |
| PRECISION-MISMATCH | 0 | — | — | — | PASS |

## 逐 gate 检查

### FP32-SIGN

| 检查 | 结果 |
|---|---|
| pre_registration block present | PASS |
| manifest marked gate=true | PASS |
| manifest counts_toward_519=false | PASS |
| manifest config_profile == B0 | PASS |
| pre-registered precision == gate spec | PASS |
| pre-registered lane_width == gate spec | PASS |
| pre-registered mask == gate spec | PASS |
| pre-registered polarity == gate spec | PASS |
| pre-registered op_classes == gate spec | PASS |
| pre-registered reg_class == gate spec | PASS |
| pre-registered decode_guard == true | PASS |
| runtime precision == pre-registered precision | PASS |
| runtime lane_width == pre-registered lane_width | PASS |
| runtime mask == pre-registered mask | PASS |
| runtime polarity == pre-registered polarity | PASS |
| runtime op_classes == pre-registered op_classes | PASS |
| runtime reg_class == pre-registered reg_class | PASS |
| runtime decode_guard == true | PASS |
| runtime permanent_stuck == true | PASS |
| workload is the pre-registered binary | PASS |
| audit.ok | PASS |
| audit.certified | PASS |
| prop_evt not truncated (ok) | PASS |
| oracle category is decidable (not UNKNOWN/Inactive/SimulatorError) | PASS |
| B0 census config.ini matches | PASS |
| B0 injection config.ini matches | PASS |
| census command carries the pre-registered op_classes | PASS |
| census command carries the pre-registered reg_class | PASS |
| census command enables decode_guard | PASS |
| inject command carries the pre-registered op_classes | PASS |
| inject command carries the pre-registered reg_class | PASS |
| inject command enables decode_guard | PASS |
| exactly one fault_installed root | PASS |
| exactly one fault_id in the stream | PASS |
| root fault_id is the only fault_id | PASS |
| root fault_mask == pre-registered mask | PASS |
| root fixed_mask == pre-registered mask | PASS |
| root stuck_polarity == pre-registered polarity | PASS |
| root reg_class == pre-registered reg_class | PASS |
| root op_class inside pre-registered allowlist | PASS |
| root precision == pre-registered precision | PASS |
| exactly one carrier_state | PASS |
| every F5 identity event carries op_class and reg_class | FAIL |
| carrier_state keeps the fixed mask/polarity | PASS |
| exposure events present | PASS |
| exposure_id values are unique | PASS |
| all exposures keep the fixed mask | PASS |
| all exposures keep the fixed polarity | PASS |
| all exposures point at the installation event | PASS |
| all exposures keep one fault_id | PASS |
| all exposure op_class values are inside the allowlist | PASS |
| all exposure reg_class values == pre-registered reg_class | PASS |
| no exposure comes from an FCVT opClass | PASS |
| all exposures decode as scalar_vfp | PASS |
| all exposures decode as fp32 | PASS |
| all exposures declare the pre-registered precision | PASS |
| every exposure has correct_before/stuck_after | PASS |
| activation == stuckActivated(correct_before, mask, polarity) | PASS |
| stuck_after == applyStuck(correct_before, mask, polarity) | PASS |
| at least one exposed-but-NOT-activated exposure | PASS |
| at least one activated exposure | PASS |
| every exposure satisfies total == sampled + dropped | PASS |
| exactly one F5 chain_end (with exposures_total) | PASS |
| chain_end counts are integers | PASS |
| exposures_total == exposures_sampled + exposures_dropped | PASS |
| exposures_sampled == exposure events in the stream | PASS |
| activated_exposure_count >= activated stream events | PASS |
| exposures_total > 0 | PASS |
| chain_end install_event == root event_id | PASS |
| chain_end fixed_mask == pre-registered mask | PASS |
| chain_end stuck_polarity == pre-registered polarity | PASS |
| chain_end op_class inside allowlist | PASS |
| chain_end reg_class == pre-registered reg_class | PASS |
| chain_end terminal is a defined F5 terminal | PASS |
| chain_end outcome agrees with terminal | PASS |
| terminal=committed has a real L5 commit witness | PASS |
| census CHAOS_ELIGIBLE_COUNT present | PASS |
| gate eligible > 0 | PASS |
| sum(per-opClass eligible) == eligible | PASS |
| sum(per-regClass eligible) == eligible | PASS |
| census opClass names are all inside the pre-registered allowlist | PASS |
| census regClass names are all the pre-registered reg_class | PASS |
| census reports >=2 distinct allowed opClasses | PASS |
| census reports the pre-registered reg_class | PASS |
| injection census used the same eligible total | PASS |

### FP64-SIGN

| 检查 | 结果 |
|---|---|
| pre_registration block present | PASS |
| manifest marked gate=true | PASS |
| manifest counts_toward_519=false | PASS |
| manifest config_profile == B0 | PASS |
| pre-registered precision == gate spec | PASS |
| pre-registered lane_width == gate spec | PASS |
| pre-registered mask == gate spec | PASS |
| pre-registered polarity == gate spec | PASS |
| pre-registered op_classes == gate spec | PASS |
| pre-registered reg_class == gate spec | PASS |
| pre-registered decode_guard == true | PASS |
| runtime precision == pre-registered precision | PASS |
| runtime lane_width == pre-registered lane_width | PASS |
| runtime mask == pre-registered mask | PASS |
| runtime polarity == pre-registered polarity | PASS |
| runtime op_classes == pre-registered op_classes | PASS |
| runtime reg_class == pre-registered reg_class | PASS |
| runtime decode_guard == true | PASS |
| runtime permanent_stuck == true | PASS |
| workload is the pre-registered binary | PASS |
| audit.ok | PASS |
| audit.certified | PASS |
| prop_evt not truncated (ok) | PASS |
| oracle category is decidable (not UNKNOWN/Inactive/SimulatorError) | PASS |
| B0 census config.ini matches | PASS |
| B0 injection config.ini matches | PASS |
| census command carries the pre-registered op_classes | PASS |
| census command carries the pre-registered reg_class | PASS |
| census command enables decode_guard | PASS |
| inject command carries the pre-registered op_classes | PASS |
| inject command carries the pre-registered reg_class | PASS |
| inject command enables decode_guard | PASS |
| exactly one fault_installed root | PASS |
| exactly one fault_id in the stream | PASS |
| root fault_id is the only fault_id | PASS |
| root fault_mask == pre-registered mask | PASS |
| root fixed_mask == pre-registered mask | PASS |
| root stuck_polarity == pre-registered polarity | PASS |
| root reg_class == pre-registered reg_class | PASS |
| root op_class inside pre-registered allowlist | PASS |
| root precision == pre-registered precision | PASS |
| exactly one carrier_state | PASS |
| every F5 identity event carries op_class and reg_class | FAIL |
| carrier_state keeps the fixed mask/polarity | PASS |
| exposure events present | PASS |
| exposure_id values are unique | PASS |
| all exposures keep the fixed mask | PASS |
| all exposures keep the fixed polarity | PASS |
| all exposures point at the installation event | PASS |
| all exposures keep one fault_id | PASS |
| all exposure op_class values are inside the allowlist | PASS |
| all exposure reg_class values == pre-registered reg_class | PASS |
| no exposure comes from an FCVT opClass | PASS |
| all exposures decode as scalar_vfp | PASS |
| all exposures decode as fp64 | PASS |
| all exposures declare the pre-registered precision | PASS |
| every exposure has correct_before/stuck_after | PASS |
| activation == stuckActivated(correct_before, mask, polarity) | PASS |
| stuck_after == applyStuck(correct_before, mask, polarity) | PASS |
| at least one exposed-but-NOT-activated exposure | PASS |
| at least one activated exposure | PASS |
| every exposure satisfies total == sampled + dropped | PASS |
| exactly one F5 chain_end (with exposures_total) | PASS |
| chain_end counts are integers | PASS |
| exposures_total == exposures_sampled + exposures_dropped | PASS |
| exposures_sampled == exposure events in the stream | PASS |
| activated_exposure_count >= activated stream events | PASS |
| exposures_total > 0 | PASS |
| chain_end install_event == root event_id | PASS |
| chain_end fixed_mask == pre-registered mask | PASS |
| chain_end stuck_polarity == pre-registered polarity | PASS |
| chain_end op_class inside allowlist | PASS |
| chain_end reg_class == pre-registered reg_class | PASS |
| chain_end terminal is a defined F5 terminal | PASS |
| chain_end outcome agrees with terminal | PASS |
| terminal=committed has a real L5 commit witness | PASS |
| census CHAOS_ELIGIBLE_COUNT present | PASS |
| gate eligible > 0 | PASS |
| sum(per-opClass eligible) == eligible | PASS |
| sum(per-regClass eligible) == eligible | PASS |
| census opClass names are all inside the pre-registered allowlist | PASS |
| census regClass names are all the pre-registered reg_class | PASS |
| census reports >=2 distinct allowed opClasses | PASS |
| census reports the pre-registered reg_class | PASS |
| injection census used the same eligible total | PASS |

### FP32-MANT

| 检查 | 结果 |
|---|---|
| pre_registration block present | PASS |
| manifest marked gate=true | PASS |
| manifest counts_toward_519=false | PASS |
| manifest config_profile == B0 | PASS |
| pre-registered precision == gate spec | PASS |
| pre-registered lane_width == gate spec | PASS |
| pre-registered mask == gate spec | PASS |
| pre-registered polarity == gate spec | PASS |
| pre-registered op_classes == gate spec | PASS |
| pre-registered reg_class == gate spec | PASS |
| pre-registered decode_guard == true | PASS |
| runtime precision == pre-registered precision | PASS |
| runtime lane_width == pre-registered lane_width | PASS |
| runtime mask == pre-registered mask | PASS |
| runtime polarity == pre-registered polarity | PASS |
| runtime op_classes == pre-registered op_classes | PASS |
| runtime reg_class == pre-registered reg_class | PASS |
| runtime decode_guard == true | PASS |
| runtime permanent_stuck == true | PASS |
| workload is the pre-registered binary | PASS |
| audit.ok | PASS |
| audit.certified | PASS |
| prop_evt not truncated (ok) | PASS |
| oracle category is decidable (not UNKNOWN/Inactive/SimulatorError) | PASS |
| B0 census config.ini matches | PASS |
| B0 injection config.ini matches | PASS |
| census command carries the pre-registered op_classes | PASS |
| census command carries the pre-registered reg_class | PASS |
| census command enables decode_guard | PASS |
| inject command carries the pre-registered op_classes | PASS |
| inject command carries the pre-registered reg_class | PASS |
| inject command enables decode_guard | PASS |
| exactly one fault_installed root | PASS |
| exactly one fault_id in the stream | PASS |
| root fault_id is the only fault_id | PASS |
| root fault_mask == pre-registered mask | PASS |
| root fixed_mask == pre-registered mask | PASS |
| root stuck_polarity == pre-registered polarity | PASS |
| root reg_class == pre-registered reg_class | PASS |
| root op_class inside pre-registered allowlist | PASS |
| root precision == pre-registered precision | PASS |
| exactly one carrier_state | PASS |
| every F5 identity event carries op_class and reg_class | FAIL |
| carrier_state keeps the fixed mask/polarity | PASS |
| exposure events present | PASS |
| exposure_id values are unique | PASS |
| all exposures keep the fixed mask | PASS |
| all exposures keep the fixed polarity | PASS |
| all exposures point at the installation event | PASS |
| all exposures keep one fault_id | PASS |
| all exposure op_class values are inside the allowlist | PASS |
| all exposure reg_class values == pre-registered reg_class | PASS |
| no exposure comes from an FCVT opClass | PASS |
| all exposures decode as scalar_vfp | PASS |
| all exposures decode as fp32 | PASS |
| all exposures declare the pre-registered precision | PASS |
| every exposure has correct_before/stuck_after | PASS |
| activation == stuckActivated(correct_before, mask, polarity) | PASS |
| stuck_after == applyStuck(correct_before, mask, polarity) | PASS |
| at least one exposed-but-NOT-activated exposure | PASS |
| at least one activated exposure | PASS |
| every exposure satisfies total == sampled + dropped | PASS |
| exactly one F5 chain_end (with exposures_total) | PASS |
| chain_end counts are integers | PASS |
| exposures_total == exposures_sampled + exposures_dropped | PASS |
| exposures_sampled == exposure events in the stream | PASS |
| activated_exposure_count >= activated stream events | PASS |
| exposures_total > 0 | PASS |
| chain_end install_event == root event_id | PASS |
| chain_end fixed_mask == pre-registered mask | PASS |
| chain_end stuck_polarity == pre-registered polarity | PASS |
| chain_end op_class inside allowlist | PASS |
| chain_end reg_class == pre-registered reg_class | PASS |
| chain_end terminal is a defined F5 terminal | PASS |
| chain_end outcome agrees with terminal | PASS |
| terminal=committed has a real L5 commit witness | PASS |
| census CHAOS_ELIGIBLE_COUNT present | PASS |
| gate eligible > 0 | PASS |
| sum(per-opClass eligible) == eligible | PASS |
| sum(per-regClass eligible) == eligible | PASS |
| census opClass names are all inside the pre-registered allowlist | PASS |
| census regClass names are all the pre-registered reg_class | PASS |
| census reports >=2 distinct allowed opClasses | PASS |
| census reports the pre-registered reg_class | PASS |
| injection census used the same eligible total | PASS |

### PRECISION-MISMATCH

| 检查 | 结果 |
|---|---|
| pre_registration block present | PASS |
| manifest marked gate=true | PASS |
| manifest counts_toward_519=false | PASS |
| manifest config_profile == B0 | PASS |
| pre-registered precision == gate spec | PASS |
| pre-registered lane_width == gate spec | PASS |
| pre-registered mask == gate spec | PASS |
| pre-registered polarity == gate spec | PASS |
| pre-registered op_classes == gate spec | PASS |
| pre-registered reg_class == gate spec | PASS |
| pre-registered decode_guard == true | PASS |
| runtime precision == pre-registered precision | PASS |
| runtime lane_width == pre-registered lane_width | PASS |
| runtime mask == pre-registered mask | PASS |
| runtime polarity == pre-registered polarity | PASS |
| runtime op_classes == pre-registered op_classes | PASS |
| runtime reg_class == pre-registered reg_class | PASS |
| runtime decode_guard == true | PASS |
| runtime permanent_stuck == true | PASS |
| workload is the pre-registered binary | PASS |
| census rc == 0 | PASS |
| census not timed out | PASS |
| census command carries pre-registered op_classes | PASS |
| census command carries pre-registered reg_class | PASS |
| census command enables decode_guard | PASS |
| B0 census config.ini matches | PASS |
| census CHAOS_ELIGIBLE_COUNT present | PASS |
| precision mismatch: eligible == 0 | PASS |
| sum(per-opClass eligible) == eligible | PASS |
| sum(per-regClass eligible) == eligible | PASS |
| census opClass names are all inside the pre-registered allowlist | PASS |
| census regClass names are all the pre-registered reg_class | PASS |
| rejection reason is precision_mismatch | PASS |
| census decode rejects > 0 | PASS |

