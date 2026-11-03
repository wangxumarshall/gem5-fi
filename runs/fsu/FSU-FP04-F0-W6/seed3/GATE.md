# FSU-FP04-F0-W6 — W6 gate（非正式，不计 seed）

- suite：`w6-fp-v1` v1 （freq F0）
- suite_hash：`7af52ddcbc1ad03d71e7f683fe87c804a7ddbc0a9ed73a0a5d06e18dc43adf1a`
- suite seed：3
- component runs：3；PASS：3/3
- 正式 seed 计数：**+0**（gate 不计 519/240）
- 结论：**PASS**

| # | program | precision | lane | mask | oracle | 结论 |
|---|---|---|---|---|---|---|
| 1 | svd | fp64 | 64 | `None` | SDC | PASS |
| 2 | fft | fp32 | 32 | `None` | SDC | PASS |
| 3 | sparse-cg | fp32 | 32 | `None` | SDC | PASS |

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

