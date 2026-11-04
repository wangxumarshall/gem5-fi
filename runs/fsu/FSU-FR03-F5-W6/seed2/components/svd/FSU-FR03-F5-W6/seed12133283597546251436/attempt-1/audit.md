# FSU-FR03-F5-W6 seed12133283597546251436 审计

- attempt：`attempt-1`
- sample_run_id：`s12133283597546251436`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 101 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '98', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | Masked |
| chain terminal | full |
| stats 非空 | True |
| 无跨 seed 复制 | True |
| decode_guard | False |
| decoded / legacy roots | 0 / 1 |
| admitted（主 fault） | True |
| certified（全 fault 门禁） | True |
| fault 数 | 1 |
| 所有 fault admitted | True |
| 所有 fault certified | True |
| violations（主 fault） | [] |

## 逐 fault 审计

| fault | terminal | admitted | certified | direct parent | tick 单调 | layers | violations |
|---|---|---|---|---|---|---|---|
| 1 | full | True | True | True | True | L0, L1, L1, L2, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `3`：✓
- `3` → `11`：✓
- `11` → `16`：✓
- `16` → `19`：✓
- `19` → `27`：✓
- `27` → `30`：✓
- `30` → `38`：✓
- `38` → `41`：✓
- `41` → `49`：✓
- `49` → `57`：✓
- `57` → `65`：✓
- `65` → `73`：✓
- `73` → `75`：✓
- `75` → `83`：✓
- `83` → `91`：✓
- `91` → `96`：✓
- `96` → `97`：✓
- `97` → `98`：✓
- `98` → `99`：✓
- `99` → `100`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W6-seed12133283597546251436.md` | `9fcd85a811f46aba1436f626c423cb21826fddd723b3b40fe5137f47fe039d77` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `d87fe0c8ad24227b3588a61d253fb1a85a08f87edb983fe3d751e3836c97c530` |
| `component_manifest.json` | `709d487232d35df452114d2570ad3f4a9ec74e39c9fd63acb3c0ed371a2a843a` |
| `inject/array.bin` | `c057a7f60984974ab4db131468dbf4f078432f69112593eec44701a207fb531c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `8f7165e97424513a343af1c92ffc0223e997f21e4a29126c966cb0bf96b7ffd7` |
| `inject/config.json` | `fefa5c8ea26e7acaf75c9ab1f1b83e47562d74635caa399e15b01e49f0bbd59f` |
| `inject/fault_injections.log` | `f09047b634674c1ece0ea8f79d33933d59df19ff90466200c8f641c59f71ea57` |
| `inject/prop_evt.txt.gz` | `51b95d877123bc3aa41a145bdb1d33baa546762bc1e4c9e0aa92d76eccc5c30e` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `78d34000b922c69ece75f5e8a5f6dc173ee073ae923bff72506998e8ba2e7c5f` |
| `manifest.json` | `51d2ac031ec07e317ad70737e2c194e0f5c646b4c9505a7cec0e8ba0e887be43` |
| `oracle.json` | `4b4664c8cd42cb9892fd91945c1e8ad44242e2bb8883d73200b8bdb34cec243c` |
| `oracle_elements.json` | `3d7805c049b86b9872056b4f16fa9eb9a9fc286364f8bd6668801eb1b3532a8f` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `ec6f28f0d19e1039acb6e2d1f5a5f9f9ad9c069db0cb40d1191d2204793b3cef` |
| `stats.txt` | `78d34000b922c69ece75f5e8a5f6dc173ee073ae923bff72506998e8ba2e7c5f` |

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
| fault 1 永久故障至少一次 activated exposure | PASS |
| fault 1 字段/lane/mask 语义 | PASS |
| fault 1 真实指令解码匹配 | PASS |
| 事件 model_id 与 manifest 一致 | PASS |
| 事件 submodel 与 manifest 一致 | PASS |
| 事件 freq 与 manifest 一致 | PASS |
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
| MD event 2 存在于原始流 | PASS |
| MD event 2 kind 一致 | PASS |
| MD event 2 parent 一致 | PASS |
| MD event 3 存在于原始流 | PASS |
| MD event 3 kind 一致 | PASS |
| MD event 3 parent 一致 | PASS |
| MD event 11 存在于原始流 | PASS |
| MD event 11 kind 一致 | PASS |
| MD event 11 parent 一致 | PASS |
| MD event 16 存在于原始流 | PASS |
| MD event 16 kind 一致 | PASS |
| MD event 16 parent 一致 | PASS |
| MD event 19 存在于原始流 | PASS |
| MD event 19 kind 一致 | PASS |
| MD event 19 parent 一致 | PASS |
| MD event 27 存在于原始流 | PASS |
| MD event 27 kind 一致 | PASS |
| MD event 27 parent 一致 | PASS |
| MD event 30 存在于原始流 | PASS |
| MD event 30 kind 一致 | PASS |
| MD event 30 parent 一致 | PASS |
| MD event 38 存在于原始流 | PASS |
| MD event 38 kind 一致 | PASS |
| MD event 38 parent 一致 | PASS |
| MD event 41 存在于原始流 | PASS |
| MD event 41 kind 一致 | PASS |
| MD event 41 parent 一致 | PASS |
| MD event 49 存在于原始流 | PASS |
| MD event 49 kind 一致 | PASS |
| MD event 49 parent 一致 | PASS |
| MD event 57 存在于原始流 | PASS |
| MD event 57 kind 一致 | PASS |
| MD event 57 parent 一致 | PASS |
| MD event 65 存在于原始流 | PASS |
| MD event 65 kind 一致 | PASS |
| MD event 65 parent 一致 | PASS |
| MD event 73 存在于原始流 | PASS |
| MD event 73 kind 一致 | PASS |
| MD event 73 parent 一致 | PASS |
| MD event 75 存在于原始流 | PASS |
| MD event 75 kind 一致 | PASS |
| MD event 75 parent 一致 | PASS |
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
| MD event 91 存在于原始流 | PASS |
| MD event 91 kind 一致 | PASS |
| MD event 91 parent 一致 | PASS |
| MD event 96 存在于原始流 | PASS |
| MD event 96 kind 一致 | PASS |
| MD event 96 parent 一致 | PASS |
| MD event 97 存在于原始流 | PASS |
| MD event 97 kind 一致 | PASS |
| MD event 97 parent 一致 | PASS |
| MD event 98 存在于原始流 | PASS |
| MD event 98 kind 一致 | PASS |
| MD event 98 parent 一致 | PASS |
| MD event 99 存在于原始流 | PASS |
| MD event 99 kind 一致 | PASS |
| MD event 99 parent 一致 | PASS |
| MD event 100 存在于原始流 | PASS |
| MD event 100 kind 一致 | PASS |
| MD event 100 parent 一致 | PASS |
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
| physreg census explicitly skipped | PASS |
| B0 运行态配置匹配（inject） | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
