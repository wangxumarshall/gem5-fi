# F5 FP06-W3 permanent-stuck gate

- run_id：`FSU-FP06-F5-W3-PERMANENT-GATE`（不计入 519）
- attempt：`runs/fsu-gates/F5-FP06-W3-PERMANENT-GATE/FSU-FP06-F5-W3-PERMANENT-GATE/seed1/attempt-2`
- 预注册：FP06-b SA1，FP32 sign bit，lane2，固定 mask `0x80000000`，warm-up 0
- 观察：1 次安装；16,384 exposures；15,620 activated exposures；
  513 条有界样本（dropped 15,871，容量账目闭合）；L0–L5 full；oracle SDC

| 检查 | 结果 |
|---|---|
| one_install | PASS |
| mask_polarity_constant | PASS |
| every_exposure_forced | PASS |
| same_polarity_not_activated | PASS |
| different_polarity_changes_result | PASS |
| non_target_lane_bit_unchanged | PASS |
| one_fault_full_L0_L5_chain | PASS |
| exposure_total_matches_census_16384 | PASS |
| event_cap_no_silent_truncation | PASS |
| markdown_separates_install_exposure_activation_terminal | PASS |
