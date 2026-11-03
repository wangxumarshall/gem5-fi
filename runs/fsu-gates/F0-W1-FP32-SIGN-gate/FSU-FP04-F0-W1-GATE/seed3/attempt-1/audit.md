# FSU-FP04-F0-W1-GATE seed3 审计

- attempt：`attempt-1`
- sample_run_id：`s3`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 7 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | SDC |
| chain terminal | full |
| stats 非空 | True |
| 无跨 seed 复制 | True |
| admitted（主 fault） | True |
| certified（全 fault 门禁） | True |
| fault 数 | 1 |
| 所有 fault admitted | True |
| 所有 fault certified | True |
| violations（主 fault） | [] |

## 逐 fault 审计

| fault | terminal | admitted | certified | direct parent | tick 单调 | layers | violations |
|---|---|---|---|---|---|---|---|
| 1 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP04-F0-W1-GATE-seed3.md` | `fe3593fb98b4e630f4b70464336c443b92cdc89c631020cfb12e852c7e7a98b8` |
| `census.err` | `0417ff9982266f3b600e35fbd8fe02d81e37399ffa90930ea5d638b8a649c218` |
| `census.out` | `2e31ec2e224c57bcd7709e39eeefd092b0230670f67d8cc80917423f7fdb0b67` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `541db5a9cd7817b4958fa9e4fb96d0e35d9695eba89b672e1bd8761ff628a482` |
| `census/config.json` | `b24a9afdd969ccff0e2d89f2a513d163c55c6ed6d3b3e028367e54a3a845a813` |
| `census/fpu_injections.log` | `79b6fba93055242c4fcaebb79021ed59efdaf7b1d80bb5425945394d0edad996` |
| `census/stats.txt` | `784030eb6899213efe66ca4c3ad4c705f4ce9556cfd5465278df2a93fed6f5f3` |
| `chain_report.json` | `22d84ee6156c17161607802f97f39b065fe3c42a47ed299e55e09b1f53168bf4` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `52d9a88ea4c35b716743bbf6d78e66d001d8d8d109a9b663501e3bfe8c480b86` |
| `inject/config.json` | `f3716783daf59c002c3862a356f9415c5c7a730476ab93c42028a4ecb5b1a0d0` |
| `inject/fpu_injections.log` | `ec7d0d51dcf34ee5ebbb75da5209718324d68b107dbd6b1973f4a9717e9d0794` |
| `inject/prop_evt.txt.gz` | `5c33256e317b7561208ac11416e44fa55d381b86c7973cfb629cdae8313d0fd3` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `fa4803ce722a5fdb0e562363dec8cf4c199bd4c5932e8bf5876cb1b10093da31` |
| `manifest.json` | `155885c2d980ffbea95785bc8940fa144bce72ef527f46460174158dd6cf4735` |
| `oracle.json` | `4dcd432eafb777859f6f18a70434c322db9902cadca8755ca9c06d932984db54` |
| `run.err` | `0417ff9982266f3b600e35fbd8fe02d81e37399ffa90930ea5d638b8a649c218` |
| `run.out` | `5250a824576144694bbb2b1bfcad24b10f4410f8cf2155e43174115140368efb` |
| `stats.txt` | `fa4803ce722a5fdb0e562363dec8cf4c199bd4c5932e8bf5876cb1b10093da31` |

## 审计检查

| 检查 | 结果 |
|---|---|
| seed Markdown 存在 | PASS |
| RunID 一致 | PASS |
| seed/sample_run_id 一致 | PASS |
| workload 二进制身份一致 | PASS |
| gem5 二进制身份一致 | PASS |
| 源码 HEAD 一致 | PASS |
| prop_evt 存在 | PASS |
| prop_evt 未截断（reason=ok） | PASS |
| 事件身份全为本 seed（越界 0） | PASS |
| scheduled(1) = fault_applied(1) | PASS |
| 每个 injected fault 均真实激活 | PASS |
| fault 1 字段/lane/mask 语义 | PASS |
| 事件 model_id 与 manifest 一致 | PASS |
| 事件 submodel 与 manifest 一致 | PASS |
| 事件 freq 与 manifest 一致 | PASS |
| 事件 load_id 与 manifest 一致 | PASS |
| fault 1 全链 field 一致 | PASS |
| 重算 admitted_faults 一致 | PASS |
| 重算 truncated 一致 | PASS |
| 事件流 fault 数 = 注入数 | PASS |
| 所有 fault 均 admitted | PASS |
| 所有 fault 均 certified | PASS |
| fault 1 terminal 一致 | PASS |
| fault 1 violations 一致 | PASS |
| fault 1 admitted 一致 | PASS |
| fault 1 certified 一致 | PASS |
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
| MD event 2 存在于原始流 | PASS |
| MD event 2 kind 一致 | PASS |
| MD event 2 parent 一致 | PASS |
| MD event 3 存在于原始流 | PASS |
| MD event 3 kind 一致 | PASS |
| MD event 3 parent 一致 | PASS |
| MD event 4 存在于原始流 | PASS |
| MD event 4 kind 一致 | PASS |
| MD event 4 parent 一致 | PASS |
| MD event 5 存在于原始流 | PASS |
| MD event 5 kind 一致 | PASS |
| MD event 5 parent 一致 | PASS |
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| 链 admitted=True | PASS |
| 链 certified=True | PASS |
| 链 violations=[] | PASS |
| 存在 admitted fault | PASS |
| MD 逐 fault 终局表存在 | PASS |
| fault 1 MD 覆盖主链全部事件 | PASS |
| fault 1 MD/原始流 direct parent | PASS |
| fault 1 MD 逐 fault 终局行存在 | PASS |
| fault 1 MD terminal 一致 | PASS |
| fault 1 MD admitted 一致 | PASS |
| fault 1 MD certified 一致 | PASS |
| MD terminal 与 chain_report 一致 | PASS |
| MD admitted/certified 与 chain_report 一致 | PASS |
| evidence_sha256.json 存在 | PASS |
| 证据 SHA-256 全部匹配（失配 0） | PASS |
| stats.txt 非空 | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
