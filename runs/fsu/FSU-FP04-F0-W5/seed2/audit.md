# polybench-fp-v1 suite seed2 审计

- suite_hash：`7282decf461243a8fdff38b6f99f66112c18027ee9a9b0a7dd057c4e2a0a7493`
- component run：**5**（不等于 seed 数；本 suite seed 正式计数为 1）
- component eligible 合计：6250972
- component activated 合计：5

| 检查 | 结果 |
|---|---|
| suite_manifest.json 存在 | PASS |
| suite 身份与 suite_hash | PASS |
| suite_manifest.suite_hash 与重算一致 | PASS |
| component manifest 结构/顺序/哈希 | PASS |
| gemm attempt 存在 | PASS |
| gemm component_manifest.json 存在 | PASS |
| gemm component manifest 校验 | PASS |
| gemm component_manifest_sha256 与 attempt manifest 一致 | PASS |
| gemm 独立 audit.ok | PASS |
| gemm audit.certified | PASS |
| gemm component_status=admitted | PASS |
| gemm oracle_elements.json 存在 | PASS |
| gemm inject/array.bin 存在 | PASS |
| gemm oracle/array 已被证据 SHA 覆盖 | PASS |
| gemm component_oracle 为 SDC/MASKED | PASS |
| 2mm attempt 存在 | PASS |
| 2mm component_manifest.json 存在 | PASS |
| 2mm component manifest 校验 | PASS |
| 2mm component_manifest_sha256 与 attempt manifest 一致 | PASS |
| 2mm 独立 audit.ok | PASS |
| 2mm audit.certified | PASS |
| 2mm component_status=admitted | PASS |
| 2mm oracle_elements.json 存在 | PASS |
| 2mm inject/array.bin 存在 | PASS |
| 2mm oracle/array 已被证据 SHA 覆盖 | PASS |
| 2mm component_oracle 为 SDC/MASKED | PASS |
| lu attempt 存在 | PASS |
| lu component_manifest.json 存在 | PASS |
| lu component manifest 校验 | PASS |
| lu component_manifest_sha256 与 attempt manifest 一致 | PASS |
| lu 独立 audit.ok | PASS |
| lu audit.certified | PASS |
| lu component_status=admitted | PASS |
| lu oracle_elements.json 存在 | PASS |
| lu inject/array.bin 存在 | PASS |
| lu oracle/array 已被证据 SHA 覆盖 | PASS |
| lu component_oracle 为 SDC/MASKED | PASS |
| cholesky attempt 存在 | PASS |
| cholesky component_manifest.json 存在 | PASS |
| cholesky component manifest 校验 | PASS |
| cholesky component_manifest_sha256 与 attempt manifest 一致 | PASS |
| cholesky 独立 audit.ok | PASS |
| cholesky audit.certified | PASS |
| cholesky component_status=admitted | PASS |
| cholesky oracle_elements.json 存在 | PASS |
| cholesky inject/array.bin 存在 | PASS |
| cholesky oracle/array 已被证据 SHA 覆盖 | PASS |
| cholesky component_oracle 为 SDC/MASKED | PASS |
| jacobi-2d attempt 存在 | PASS |
| jacobi-2d component_manifest.json 存在 | PASS |
| jacobi-2d component manifest 校验 | PASS |
| jacobi-2d component_manifest_sha256 与 attempt manifest 一致 | PASS |
| jacobi-2d 独立 audit.ok | PASS |
| jacobi-2d audit.certified | PASS |
| jacobi-2d component_status=admitted | PASS |
| jacobi-2d oracle_elements.json 存在 | PASS |
| jacobi-2d inject/array.bin 存在 | PASS |
| jacobi-2d oracle/array 已被证据 SHA 覆盖 | PASS |
| jacobi-2d component_oracle 为 SDC/MASKED | PASS |
| suite_report.json 存在 | PASS |
| suite_report 声明 5 个 component run | PASS |
| suite_report 未把 component 数当 seed 数 | PASS |
| suite_report suite_hash 一致 | PASS |
| suite_report eligible/activated 汇总一致 | PASS |

**结论：PASS**
