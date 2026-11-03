# FSU-FP06-F5-W5-GATE — FP06-F5-W5 suite gate（非正式，不计 seed）

- suite：`polybench-fp-v1-f5` v1
- suite_hash：`29e2f8d30cabf28281caf302a37d163dfdc0f11e44344b0b365269ad87a03581`
- seed_plan：suite seed 1 / `FP06-a` / fp32 / mask `0x00400000` / polarity 0
- component runs：5；PASS：5/5
- 正式 seed 计数：**+0**（gate 不计 519/240）
- 结论：**PASS**

| # | program | eligible | activated | terminal | oracle | audit | 结论 |
|---|---|---|---|---|---|---|---|
| 1 | gemm | 1393944 | 1 | full | SDC | ok | PASS |
| 2 | 2mm | 1145697 | 1 | full | SDC | ok | PASS |
| 3 | lu | 800982 | 1 | full | SDC | ok | PASS |
| 4 | cholesky | 810725 | 1 | full | SDC | ok | PASS |
| 5 | jacobi-2d | 2099624 | 1 | full | SDC | ok | PASS |

## 逐 component 检查

### gemm

| 检查 | 结果 |
|---|---|
| attempt directory exists | PASS |
| attempt manifest.json exists | PASS |
| attempt freq is F5 | PASS |
| attempt model_id is FP06 | PASS |
| attempt load_id is W5 | PASS |
| attempt submodel == seed_plan submodel | PASS |
| injector component is fsu | PASS |
| exactly one component fault (max_faults=1) | PASS |
| permanent_stuck enabled | PASS |
| fault_mask == seed_plan mask | PASS |
| precision == seed_plan precision | PASS |
| stuck_polarity == seed_plan polarity | PASS |
| lane_width == seed_plan lane_width | PASS |
| lane_offset == seed_plan lane_offset | PASS |
| f5_warmup == seed_plan warmup | PASS |
| f5_sample_limit == seed_plan sample.limit | PASS |
| f5_keep_first_last_n == seed_plan sample.keep_first_last_n | PASS |
| op_classes == seed_plan op_classes | PASS |
| reg_class == seed_plan reg_class | PASS |
| decode_guard == seed_plan decode_guard | PASS |
| attempt seed_plan_entry == suite seed_plan entry | PASS |
| binary is the registered program binary | PASS |
| run_id is the gate id, not a formal RunID | PASS |
| component manifest structure/identity | PASS |
| component_status == admitted | PASS |
| component_oracle is SDC or MASKED | PASS |
| component seed_plan_entry == pre-registration | PASS |
| component_manifest_sha256 == attempt manifest.json | PASS |
| independent audit.ok | PASS |
| independent audit.certified | PASS |
| oracle_elements.json exists | PASS |
| inject/array.bin exists | PASS |
| oracle/array covered by evidence_sha256.json | PASS |

### 2mm

| 检查 | 结果 |
|---|---|
| attempt directory exists | PASS |
| attempt manifest.json exists | PASS |
| attempt freq is F5 | PASS |
| attempt model_id is FP06 | PASS |
| attempt load_id is W5 | PASS |
| attempt submodel == seed_plan submodel | PASS |
| injector component is fsu | PASS |
| exactly one component fault (max_faults=1) | PASS |
| permanent_stuck enabled | PASS |
| fault_mask == seed_plan mask | PASS |
| precision == seed_plan precision | PASS |
| stuck_polarity == seed_plan polarity | PASS |
| lane_width == seed_plan lane_width | PASS |
| lane_offset == seed_plan lane_offset | PASS |
| f5_warmup == seed_plan warmup | PASS |
| f5_sample_limit == seed_plan sample.limit | PASS |
| f5_keep_first_last_n == seed_plan sample.keep_first_last_n | PASS |
| op_classes == seed_plan op_classes | PASS |
| reg_class == seed_plan reg_class | PASS |
| decode_guard == seed_plan decode_guard | PASS |
| attempt seed_plan_entry == suite seed_plan entry | PASS |
| binary is the registered program binary | PASS |
| run_id is the gate id, not a formal RunID | PASS |
| component manifest structure/identity | PASS |
| component_status == admitted | PASS |
| component_oracle is SDC or MASKED | PASS |
| component seed_plan_entry == pre-registration | PASS |
| component_manifest_sha256 == attempt manifest.json | PASS |
| independent audit.ok | PASS |
| independent audit.certified | PASS |
| oracle_elements.json exists | PASS |
| inject/array.bin exists | PASS |
| oracle/array covered by evidence_sha256.json | PASS |

### lu

| 检查 | 结果 |
|---|---|
| attempt directory exists | PASS |
| attempt manifest.json exists | PASS |
| attempt freq is F5 | PASS |
| attempt model_id is FP06 | PASS |
| attempt load_id is W5 | PASS |
| attempt submodel == seed_plan submodel | PASS |
| injector component is fsu | PASS |
| exactly one component fault (max_faults=1) | PASS |
| permanent_stuck enabled | PASS |
| fault_mask == seed_plan mask | PASS |
| precision == seed_plan precision | PASS |
| stuck_polarity == seed_plan polarity | PASS |
| lane_width == seed_plan lane_width | PASS |
| lane_offset == seed_plan lane_offset | PASS |
| f5_warmup == seed_plan warmup | PASS |
| f5_sample_limit == seed_plan sample.limit | PASS |
| f5_keep_first_last_n == seed_plan sample.keep_first_last_n | PASS |
| op_classes == seed_plan op_classes | PASS |
| reg_class == seed_plan reg_class | PASS |
| decode_guard == seed_plan decode_guard | PASS |
| attempt seed_plan_entry == suite seed_plan entry | PASS |
| binary is the registered program binary | PASS |
| run_id is the gate id, not a formal RunID | PASS |
| component manifest structure/identity | PASS |
| component_status == admitted | PASS |
| component_oracle is SDC or MASKED | PASS |
| component seed_plan_entry == pre-registration | PASS |
| component_manifest_sha256 == attempt manifest.json | PASS |
| independent audit.ok | PASS |
| independent audit.certified | PASS |
| oracle_elements.json exists | PASS |
| inject/array.bin exists | PASS |
| oracle/array covered by evidence_sha256.json | PASS |

### cholesky

| 检查 | 结果 |
|---|---|
| attempt directory exists | PASS |
| attempt manifest.json exists | PASS |
| attempt freq is F5 | PASS |
| attempt model_id is FP06 | PASS |
| attempt load_id is W5 | PASS |
| attempt submodel == seed_plan submodel | PASS |
| injector component is fsu | PASS |
| exactly one component fault (max_faults=1) | PASS |
| permanent_stuck enabled | PASS |
| fault_mask == seed_plan mask | PASS |
| precision == seed_plan precision | PASS |
| stuck_polarity == seed_plan polarity | PASS |
| lane_width == seed_plan lane_width | PASS |
| lane_offset == seed_plan lane_offset | PASS |
| f5_warmup == seed_plan warmup | PASS |
| f5_sample_limit == seed_plan sample.limit | PASS |
| f5_keep_first_last_n == seed_plan sample.keep_first_last_n | PASS |
| op_classes == seed_plan op_classes | PASS |
| reg_class == seed_plan reg_class | PASS |
| decode_guard == seed_plan decode_guard | PASS |
| attempt seed_plan_entry == suite seed_plan entry | PASS |
| binary is the registered program binary | PASS |
| run_id is the gate id, not a formal RunID | PASS |
| component manifest structure/identity | PASS |
| component_status == admitted | PASS |
| component_oracle is SDC or MASKED | PASS |
| component seed_plan_entry == pre-registration | PASS |
| component_manifest_sha256 == attempt manifest.json | PASS |
| independent audit.ok | PASS |
| independent audit.certified | PASS |
| oracle_elements.json exists | PASS |
| inject/array.bin exists | PASS |
| oracle/array covered by evidence_sha256.json | PASS |

### jacobi-2d

| 检查 | 结果 |
|---|---|
| attempt directory exists | PASS |
| attempt manifest.json exists | PASS |
| attempt freq is F5 | PASS |
| attempt model_id is FP06 | PASS |
| attempt load_id is W5 | PASS |
| attempt submodel == seed_plan submodel | PASS |
| injector component is fsu | PASS |
| exactly one component fault (max_faults=1) | PASS |
| permanent_stuck enabled | PASS |
| fault_mask == seed_plan mask | PASS |
| precision == seed_plan precision | PASS |
| stuck_polarity == seed_plan polarity | PASS |
| lane_width == seed_plan lane_width | PASS |
| lane_offset == seed_plan lane_offset | PASS |
| f5_warmup == seed_plan warmup | PASS |
| f5_sample_limit == seed_plan sample.limit | PASS |
| f5_keep_first_last_n == seed_plan sample.keep_first_last_n | PASS |
| op_classes == seed_plan op_classes | PASS |
| reg_class == seed_plan reg_class | PASS |
| decode_guard == seed_plan decode_guard | PASS |
| attempt seed_plan_entry == suite seed_plan entry | PASS |
| binary is the registered program binary | PASS |
| run_id is the gate id, not a formal RunID | PASS |
| component manifest structure/identity | PASS |
| component_status == admitted | PASS |
| component_oracle is SDC or MASKED | PASS |
| component seed_plan_entry == pre-registration | PASS |
| component_manifest_sha256 == attempt manifest.json | PASS |
| independent audit.ok | PASS |
| independent audit.certified | PASS |
| oracle_elements.json exists | PASS |
| inject/array.bin exists | PASS |
| oracle/array covered by evidence_sha256.json | PASS |

