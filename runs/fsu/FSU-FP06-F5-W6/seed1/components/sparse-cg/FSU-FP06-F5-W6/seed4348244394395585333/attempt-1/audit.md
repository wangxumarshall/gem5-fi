# FSU-FP06-F5-W6 seed4348244394395585333 审计

- attempt：`attempt-1`
- sample_run_id：`s4348244394395585333`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 522 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '10', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `3` → `7`：✓
- `7` → `8`：✓
- `8` → `9`：✓
- `9` → `10`：✓
- `10` → `521`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W6-seed4348244394395585333.md` | `964d62c5c25f2bd07abf583360023485a6692a378155ba07f56cc43ba455e8d8` |
| `census.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `census.out` | `aaa3ad592bed190d0c07bea5f2eff404f94545e4d4749bebe8a33e53046b0eec` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `7f93c1cd05b9431106a4b4b07b40acb4d2895f48a9b63ec6d9655dc06c7440e6` |
| `census/config.json` | `a9f83e2d00fa5f65f27a0e5d0e9556b5576e1d7b83836208ac7a1f6263bb11ff` |
| `census/fpu_injections.log` | `7d4a2321eb81215bafc86524bac039b3535e5a09895fc42f5bbe3d1f14e430b2` |
| `census/stats.txt` | `d54f0e31f90696eeb8e13c74f63fd4a46789c007fe5737c4e424e71775c53b0a` |
| `chain_report.json` | `97b17e2a619ed9c1e8901edd865df01ed5dabe9930cef1dc387d844464135bb8` |
| `component_manifest.json` | `99f3168143a79a9d0da4ada2dfd0cb84c6d570021c9ca556110e2283695961e9` |
| `inject/array.bin` | `2ee14262951168f09faa9d755485e02f3017f99f5cc2b33de8cf9223de512b5c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `df4660254572265154168aee8bc614063adaaabd165b143d4472afec200abff6` |
| `inject/config.json` | `03f2dd5c9b817d42c46bf5b2ab217c8b22388523458635086cffa73aafff8662` |
| `inject/fpu_injections.log` | `d9294d0777cf4951cd4d266bde30bbdfa5b77b7f0408ed6ce359fc3fc3896436` |
| `inject/prop_evt.txt.gz` | `d2fe230d0cff50538aa70fb888bebb109e8ecdcc586d32df138bd5d8e53c0eff` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `99ac32e4b22deb756fb86d77f76569e9b6a0eb7441bafa175a579c2dc347bd27` |
| `manifest.json` | `265495f4721e8abfe1d0a6bcc9c3608c2635d8385dc3848196de961a63be332a` |
| `oracle.json` | `b2c103d75b0f5c229df834c4dd6c995ad29ea0b3b1a601a2904453549bb84fc6` |
| `oracle_elements.json` | `7e72dcbdab544ce87fccace2d87464b64fbec118ac8e7499d3cb0eba076105c2` |
| `run.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `run.out` | `90134142f1675bce92e2eb7ebf5814dbb63408cd59c39592345f7f97305b05a1` |
| `stats.txt` | `99ac32e4b22deb756fb86d77f76569e9b6a0eb7441bafa175a579c2dc347bd27` |

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
| fault 1 sampled_unique = 唯一 exposure_id 数 | PASS |
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
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
| MD event 8 存在于原始流 | PASS |
| MD event 8 kind 一致 | PASS |
| MD event 8 parent 一致 | PASS |
| MD event 9 存在于原始流 | PASS |
| MD event 9 kind 一致 | PASS |
| MD event 9 parent 一致 | PASS |
| MD event 10 存在于原始流 | PASS |
| MD event 10 kind 一致 | PASS |
| MD event 10 parent 一致 | PASS |
| MD event 521 存在于原始流 | PASS |
| MD event 521 kind 一致 | PASS |
| MD event 521 parent 一致 | PASS |
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
