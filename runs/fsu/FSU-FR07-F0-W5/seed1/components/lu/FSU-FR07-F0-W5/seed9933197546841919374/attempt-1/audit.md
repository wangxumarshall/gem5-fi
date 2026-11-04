# FSU-FR07-F0-W5 seed9933197546841919374 审计

- attempt：`attempt-1`
- sample_run_id：`s9933197546841919374`

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
| `FSU-FR07-F0-W5-seed9933197546841919374.md` | `8f6be4a84d9e6c6e53a43258d1f94a56602700d110b68a299acfda7304763bb5` |
| `census.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `census.out` | `c4ccb56d248c8b86b7a67db218f9a3af219e5b9ad128c6db50e16319b5880c06` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `2b042eaa1c8e911443586125e2eb97c30ca63bc0cd5d5fdbbabb3c000cbfd200` |
| `census/config.json` | `9384549c7bdec1880e362ab22b7f0aa8aad362524aea149fd08e24fdd2c047ec` |
| `census/fpu_injections.log` | `cd18798cacbd198a4aac41821d50f3f553124f905faf8da29028d785004480ca` |
| `census/stats.txt` | `eab483e258cd656ffa4780c6717965b7f9d35060b140c3164dcb8e102c415549` |
| `chain_report.json` | `354cd534fb37e95ea41d4bf92bdb93e9e3c3178a6be5115b3b28e1afea547bdb` |
| `component_manifest.json` | `cd4cf1046c19b5433b093cef5c91aed03e454290a81ed9c0b5873f82fd000719` |
| `inject/array.bin` | `e101cd93e0956d73e5689616a01f60d84deda5b369c24773d0b2749efb27d90b` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `1845051841bcf123e9f683f5d31cec834f024d91b3b0fe73d10dc8b9d4c4c991` |
| `inject/config.json` | `0d69ef17cfc879ab0790bc8f8d2fc71eb6e4e3fb2d0a8fcd537bc9e3ed99282c` |
| `inject/fpu_injections.log` | `7976ab47a96437879399424569d5f55e1f13b6fd9c638825e269f8371b682c0c` |
| `inject/prop_evt.txt.gz` | `f93f3210da4561adba3bd0dc36cf83b16dfaa304553375a168d547a06611ef4e` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `6fc15c71dc8afb9b66b5bdd5a72748e54b9aec2f2f70808ae971dbcde4e04145` |
| `manifest.json` | `d138a0e7e3b9aa919413c8e63a2a4796a6c05c6726e8978295b5906517cdcd69` |
| `oracle.json` | `f8037cc3ace50740d1e82d1d15be7325465e5de6c02a9a29e1fc7cd25abdc4e8` |
| `oracle_elements.json` | `81b09268fbbabd07b14e7056a168566b9a42281a0f3a4ac226321fa258d4b03b` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `77a170929e188f416360fee01a07d6e0ce733d36e5e48c0b29626b1fca3333ef` |
| `stats.txt` | `6fc15c71dc8afb9b66b5bdd5a72748e54b9aec2f2f70808ae971dbcde4e04145` |

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
