# FSU-FP06-F5-W6 — W6 gate（非正式，不计 seed）

- suite：`w6-fp-v1-f5` v1 （freq F5）
- suite_hash：`2d1a8f9d84d502996724d97adc96b811f81b657fbcbdd0d1026fd34f3c406804`
- suite seed：2 / `FP06-b`
- component runs：3；PASS：3/3
- 正式 seed 计数：**+0**（gate 不计 519/240）
- 结论：**PASS**

| # | program | precision | lane | mask | oracle | 结论 |
|---|---|---|---|---|---|---|
| 1 | svd | fp64 | 64 | `0x8000000000000000` | SDC | PASS |
| 2 | fft | fp32 | 32 | `0x80000000` | SDC | PASS |
| 3 | sparse-cg | fp32 | 32 | `0x80000000` | SDC | PASS |

## 逐 component 检查

### svd

| 检查 | 结果 |
|---|---|
| attempt directory exists | PASS |
| attempt manifest.json exists | PASS |
| manifest injector == resolved per-program injector | PASS |
| manifest effective injector recorded | PASS |
| manifest program_override recorded | PASS |
| manifest binary is the registered program binary | PASS |
| manifest run_id is the gate id | PASS |
| manifest seed_plan_entry == pre-registration | PASS |
| component manifest identity | PASS |
| component_status == admitted | PASS |
| component_oracle is SDC or MASKED | PASS |
| component seed_plan_entry recorded | PASS |
| component_manifest_sha256 == attempt manifest.json | PASS |
| independent audit.ok | PASS |
| independent audit.certified | PASS |
| oracle_elements.json exists | PASS |
| inject/array.bin exists | PASS |
| oracle/array covered by evidence_sha256.json | PASS |
| recorded oracle outcome matches the real arrays | PASS |

### fft

| 检查 | 结果 |
|---|---|
| attempt directory exists | PASS |
| attempt manifest.json exists | PASS |
| manifest injector == resolved per-program injector | PASS |
| manifest effective injector recorded | PASS |
| manifest program_override recorded | PASS |
| manifest binary is the registered program binary | PASS |
| manifest run_id is the gate id | PASS |
| manifest seed_plan_entry == pre-registration | PASS |
| component manifest identity | PASS |
| component_status == admitted | PASS |
| component_oracle is SDC or MASKED | PASS |
| component seed_plan_entry recorded | PASS |
| component_manifest_sha256 == attempt manifest.json | PASS |
| independent audit.ok | PASS |
| independent audit.certified | PASS |
| oracle_elements.json exists | PASS |
| inject/array.bin exists | PASS |
| oracle/array covered by evidence_sha256.json | PASS |
| recorded oracle outcome matches the real arrays | PASS |

### sparse-cg

| 检查 | 结果 |
|---|---|
| attempt directory exists | PASS |
| attempt manifest.json exists | PASS |
| manifest injector == resolved per-program injector | PASS |
| manifest effective injector recorded | PASS |
| manifest program_override recorded | PASS |
| manifest binary is the registered program binary | PASS |
| manifest run_id is the gate id | PASS |
| manifest seed_plan_entry == pre-registration | PASS |
| component manifest identity | PASS |
| component_status == admitted | PASS |
| component_oracle is SDC or MASKED | PASS |
| component seed_plan_entry recorded | PASS |
| component_manifest_sha256 == attempt manifest.json | PASS |
| independent audit.ok | PASS |
| independent audit.certified | PASS |
| oracle_elements.json exists | PASS |
| inject/array.bin exists | PASS |
| oracle/array covered by evidence_sha256.json | PASS |
| recorded oracle outcome matches the real arrays | PASS |

