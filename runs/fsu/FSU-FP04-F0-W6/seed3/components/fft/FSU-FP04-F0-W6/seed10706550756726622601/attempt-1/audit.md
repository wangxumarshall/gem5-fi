# FSU-FP04-F0-W6 seed10706550756726622601 审计

- attempt：`attempt-1`
- sample_run_id：`s10706550756726622601`

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
- `1` → `2`：✓
- `2` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP04-F0-W6-seed10706550756726622601.md` | `26fb272f9e3187e10bb66785eba7e7e1d9320d785fbe0d8b01043d4a5c45df22` |
| `census.err` | `e798c107ac5ec23672815724a64d0efaab3e9a7a5c4a78f21880c7252f78fe80` |
| `census.out` | `71b0fec718fc3877f1b9d14881b902f6a946569c8e349e47508f127b566107e9` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `7ef82f118bf21a973540822faeba36b77da271e849f1cd1c12bc3c910b697548` |
| `census/config.json` | `ca84ee5379eb524253459c7f6ff2b9dca7816db6ae59b0eb44956d6fe8a11cba` |
| `census/fpu_injections.log` | `087bc3ceedd301bd607f7361e9afb309f73a49379488262b1a933d1238a5d32f` |
| `census/stats.txt` | `b374d6344ed8176d2a309dd09f3a12fac669e2ad8510608fac4b207979fb1ffd` |
| `chain_report.json` | `fe4ad062a8e95f108971af2110a4865601d2d672759dcdd6602ffda263de41e8` |
| `component_manifest.json` | `2761c70e0b7b81cf87a778317e627ff92ff6b3a29e45c6e1ecbdc43113f551e7` |
| `inject/array.bin` | `d51dfc1dadca276ab45df863da4157fe8530b71df8b560f175f86912370106a8` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `72b137d28a0b1d2b2255a17eda4cf78b61c1796ae95209e37757eda933ea7edc` |
| `inject/config.json` | `3420d188f2616774669332dddf743a3934a5dff7955878d52bceeeaaec8914bf` |
| `inject/fpu_injections.log` | `c82d47025bc8fea3ced3ca58d1011c51620a729688d8d58a676ea8c56b1aa662` |
| `inject/prop_evt.txt.gz` | `fd44ed06125b8d25d1d2911e6d48f8ea5ee215cdfe2cc7d79aa0c1ef4a381e09` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `d4c7105235ba98a6cc046c4e4f5f272a2cef2f6d2b1d14055016fba5826e5795` |
| `manifest.json` | `a7d32448627ea9ced3f61e169ae157cc21216cc024610a769c7fad2e99cf2e32` |
| `oracle.json` | `5b6b32056d56c7e5a81010cdcfee0895fa3a098ba2a250d31d77be84d5093de2` |
| `oracle_elements.json` | `877c52e1cede9f984830437ec7ed77c91a132e50bb04263074ac8a556522a25e` |
| `run.err` | `e798c107ac5ec23672815724a64d0efaab3e9a7a5c4a78f21880c7252f78fe80` |
| `run.out` | `4dcd587f77c6b8997162fd8ebaef5b97c68be12bc015e29d1d6d64cdcd212d37` |
| `stats.txt` | `d4c7105235ba98a6cc046c4e4f5f272a2cef2f6d2b1d14055016fba5826e5795` |

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
