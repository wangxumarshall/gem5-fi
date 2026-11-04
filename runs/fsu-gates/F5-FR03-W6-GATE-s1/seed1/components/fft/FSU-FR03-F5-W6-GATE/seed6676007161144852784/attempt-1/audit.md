# FSU-FR03-F5-W6-GATE seed6676007161144852784 审计

- attempt：`attempt-1`
- sample_run_id：`s6676007161144852784`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 83 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '80', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `73` → `78`：✓
- `78` → `79`：✓
- `79` → `80`：✓
- `80` → `81`：✓
- `81` → `82`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W6-GATE-seed6676007161144852784.md` | `ee7cef853b0f5803c18c972eb18e92741e5c292be0e0d0ba9313f3ac3ca4a610` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `b11f01889d5d5d8f734904659496e25b9cbd103e2d9ca7459721e09991646eef` |
| `component_manifest.json` | `41e1f65470c90902253a1e1322d0c1ffa259731dc506783c5757f6f5aca8371a` |
| `inject/array.bin` | `dde19526f0354b3a61be193aae24b3c11c4cdfac70e8aa6adbac5be9d9b1f177` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `51d92b0a052daffc83e0433941598c1ef5d61854e3120440e97e73f7be2b3d9e` |
| `inject/config.json` | `ffe7ed0633072be3cc39bbfc98396607450d26dddb2f6fd1a5c407123c64bf19` |
| `inject/fault_injections.log` | `dacc3cd5057e332d213aeb6e0b9c66f4596dcfb736871230e31f1b1018c9cf3f` |
| `inject/prop_evt.txt.gz` | `39de7407c7417e91e9db0ae32c90302535116459e244d584bc992478a5ec729d` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `8691f708578db8c5672f85becc671f5c99040317833dbdf9dd0c8d332fed1934` |
| `manifest.json` | `596e45fef426f2016f13bed9e8488b950204ab9f7d0054ca8b8bb556c2b937cb` |
| `oracle.json` | `4c163af5d25b79df95f30376c6ef619f6fa57a7b221ca5852f7231931381462b` |
| `oracle_elements.json` | `f923ad4b3bf0b3dabfedaa59b6e0c04dd8f52d85caaa3b18c49a419bb737b951` |
| `run.err` | `e798c107ac5ec23672815724a64d0efaab3e9a7a5c4a78f21880c7252f78fe80` |
| `run.out` | `6c356611ce285b9452fb31340d47766eaf66842a67e07c6b0525f6b1c845e368` |
| `stats.txt` | `8691f708578db8c5672f85becc671f5c99040317833dbdf9dd0c8d332fed1934` |

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
| MD event 78 存在于原始流 | PASS |
| MD event 78 kind 一致 | PASS |
| MD event 78 parent 一致 | PASS |
| MD event 79 存在于原始流 | PASS |
| MD event 79 kind 一致 | PASS |
| MD event 79 parent 一致 | PASS |
| MD event 80 存在于原始流 | PASS |
| MD event 80 kind 一致 | PASS |
| MD event 80 parent 一致 | PASS |
| MD event 81 存在于原始流 | PASS |
| MD event 81 kind 一致 | PASS |
| MD event 81 parent 一致 | PASS |
| MD event 82 存在于原始流 | PASS |
| MD event 82 kind 一致 | PASS |
| MD event 82 parent 一致 | PASS |
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
