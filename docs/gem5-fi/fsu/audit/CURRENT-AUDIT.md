# FSU 当前工具全量复审

- generated_at: `2026-11-05T15:15:56`
- tool_git_sha: `9bca75c3f0ac6f51ac4b8699c6313e23cd77b1d2`
- schema_version: `fsu-full-audit/v1`

| 范围 | total | current_verified | legacy_report_only | current_verification_failed | missing_evidence |
|---|---:|---:|---:|---:|---:|
| suite seed | 21 | 20 | 0 | 1 | 0 |
| component | 87 | 82 | 0 | 5 | 0 |
| 非 suite 权威 seed | 41 | 41 | 0 | 0 | 0 |
| 权威 seed 合计 | 62 | 61 | 0 | 1 | 0 |

## 未通过/缺证据明细

### FSU-FR03-F5-W5/seed1 — current_verification_failed
- suite: suite_hash drift: manifest 864c71cbb3a0c69275a0d8d36a09db2dd98eb21c446533e3ff26c703c90c8ee7 != recomputed 98d88154edeac9992aa73e103cf76d835510cccf03c130c8590d208804a64d17
- identity: gemm: suite_manifest component suite_hash drift
- identity: gemm: attempt target_plan_entry submodel='FR03-c' != 'FR03-a'
- identity: gemm: component_manifest suite_hash='864c71cbb3a0c69275a0d8d36a09db2dd98eb21c446533e3ff26c703c90c8ee7' != '98d88154edeac9992aa73e103cf76d835510cccf03c130c8590d208804a64d17'
- identity: gemm: component target_plan_entry submodel='FR03-c' != 'FR03-a'
- identity: gemm: physical identity: component target_plan_entry submodel='FR03-c' != frozen 'FR03-a'
- identity: 2mm: suite_manifest component suite_hash drift
- identity: 2mm: attempt target_plan_entry submodel='FR03-c' != 'FR03-a'
- identity: 2mm: component_manifest suite_hash='864c71cbb3a0c69275a0d8d36a09db2dd98eb21c446533e3ff26c703c90c8ee7' != '98d88154edeac9992aa73e103cf76d835510cccf03c130c8590d208804a64d17'
- identity: 2mm: component target_plan_entry submodel='FR03-c' != 'FR03-a'
- component gemm: current_verification_failed
- component 2mm: current_verification_failed
- component lu: current_verification_failed
- component cholesky: current_verification_failed
- component jacobi-2d: current_verification_failed

