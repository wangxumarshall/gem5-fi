# FSU-FR07-F0-W5 seed10778654834131587920 审计

- attempt：`attempt-1`
- sample_run_id：`s10778654834131587920`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 8 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '6', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | SDC |
| chain terminal | full |
| stats 非空 | True |
| 无跨 seed 复制 | True |
| decode_guard | True |
| decoded / legacy roots | 1 / 0 |
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
- `1` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR07-F0-W5-seed10778654834131587920.md` | `16d14d4ef2a93e158d72040ff336b275ace30635010381f8ac3fe71a4ffc7162` |
| `census.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `census.out` | `7a55aea8b3bd6b834ffcf1c6fe9cc2ccaedf2a273080432cce8f8a5121ab862c` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `ba8b5958a03624dd24987233748e9a79fc0af1dede1a6bb6385304b6f62e515c` |
| `census/config.json` | `add27a04f734fd15000d92d64113ba0edb9192d9e7c5bd56aff59e6cca39b2a5` |
| `census/fpu_injections.log` | `6f9016e280ba460670039429e9f0a0256e393cfb5396ebdc914d8115f6905b8f` |
| `census/stats.txt` | `6e36d1504586284e59ee3d799a9cf03207e7d3438e058ce51f5d220a69551003` |
| `chain_report.json` | `f46f6a91aef6f7513b59c496d99c169a0695f8bfc9f814f86514674ef0d581df` |
| `component_manifest.json` | `4f9c718b9728ff25138098b3a0b6fecbbd49ccdc0be3a4408a8b47e7d17c26c7` |
| `inject/array.bin` | `11201ca3a8c439b9061251871f96663cc102641d51d64ffa2a44fc5c429039df` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `d466b5293f69a7c60ca2bb1a9617a6db3be9006bc01bcc1481e2b91c6fa0cc31` |
| `inject/config.json` | `a4845169410660612dbbf3e73ba2a38100513061a5e2d39810d8201307767a32` |
| `inject/fpu_injections.log` | `583423123da52aefa2554f5abb78ceb744e7f66f591f437bb3403eb96b33de55` |
| `inject/prop_evt.txt.gz` | `a069785657c06a5033d18907efb084ae1d9b837ec60ec8feedadf152d80068d9` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `e4456a1d296beeb1d9a22f832ce114797aa3827b9f47c8956c2913aafd716943` |
| `manifest.json` | `e0057acef82bf6825edc9dfa72eef35f01d4ecbb2b367c0392b40d6d4b7bb31d` |
| `oracle.json` | `6a7e9906d95ac2c41ad1139d11d337cb36a6d814aa68d72f69e785917c36fe56` |
| `oracle_elements.json` | `09ef52ad34342b6674267c684ebe1c867b90e5462269ded73d76f69d0c8b27f8` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `d74e51cde08d99068b6ff73254b06f7647c7b4e03625c53315c5ece2e19a8e82` |
| `stats.txt` | `e4456a1d296beeb1d9a22f832ce114797aa3827b9f47c8956c2913aafd716943` |

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
| scheduled(1) = fault_roots(1) | PASS |
| 每个 injected fault 均真实激活 | PASS |
| fault 1 字段/lane/mask 语义 | PASS |
| fault 1 真实指令解码匹配 | PASS |
| decode_guard: 所有 root 含真实解码字段 | PASS |
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
| fault 1 F5 计数/去重/守恒校验 | PASS |
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
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
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
| 链 admitted=True | PASS |
| 链 certified=True | PASS |
| 链 violations=[] | PASS |
| 存在 admitted fault | PASS |
| MD 逐 fault 终局表存在（legacy 单 fault 行） | PASS |
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
| B0 运行态配置匹配（census） | PASS |
| B0 运行态配置匹配（inject） | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
