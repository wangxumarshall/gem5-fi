# FSU-FR03-F5-W5 seed16065008133739276579 审计

- attempt：`attempt-1`
- sample_run_id：`s16065008133739276579`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 88 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '85', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `13`：✓
- `13` → `21`：✓
- `21` → `33`：✓
- `33` → `42`：✓
- `42` → `47`：✓
- `47` → `56`：✓
- `56` → `61`：✓
- `61` → `70`：✓
- `70` → `78`：✓
- `78` → `83`：✓
- `83` → `84`：✓
- `84` → `85`：✓
- `85` → `86`：✓
- `86` → `87`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-seed16065008133739276579.md` | `3f5205e8dc8452ff7d6cc1e09c84133e549d368154df741dbc535e42909509c4` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `084dd7b75bf36bf8101aa5b8aee6c1652ec5a9ab491d4dd6cca973f31b3eb5f0` |
| `component_manifest.json` | `f7788533aef59dac4ea6a6c2e338ca024c0c9934f410609ce977567e23f7b07a` |
| `inject/array.bin` | `46eb754c53cf2ecffe653675230b55272073383f69806a3169a45ba35733dd60` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `3df5d9cb94f1177a0b1d01ec293eb4c6d98e3346994efb5f7931d97fd83c5193` |
| `inject/config.json` | `ce43dcb1ab319f837ca6e3b117f17003ba18c3c242903e0c36c0cabe61b239e4` |
| `inject/fault_injections.log` | `211e8b8b7482f5388ce3f46f577b814b4b74571621117cebbad36e8a69d5e4f9` |
| `inject/prop_evt.txt.gz` | `020dfdd411846594bcf65806210e25f401154ffc78090d6f90c947d8d4c2f212` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `3c7a7432bad738129c207c16a5e0bea11bff9db4ac4f36477525b4002b4c2be2` |
| `manifest.json` | `382ca370abd0ae4502a39c405664033e121946f1f681ca3014e656acb851ceed` |
| `oracle.json` | `8b9ce4b1f1f40fb123573117b1b93d00f745a2e4c7cd96c7610a58debd577041` |
| `oracle_elements.json` | `6079c0e33c185964bc1aed6a400f8c05e77a14d7d5c9f6cf9669d9fd49bca626` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `c10f25cc70225e5cdbfaf7db1dd4f254e385d83b859d33cf7ac3fee623125907` |
| `stats.txt` | `3c7a7432bad738129c207c16a5e0bea11bff9db4ac4f36477525b4002b4c2be2` |

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
| MD event 13 存在于原始流 | PASS |
| MD event 13 kind 一致 | PASS |
| MD event 13 parent 一致 | PASS |
| MD event 21 存在于原始流 | PASS |
| MD event 21 kind 一致 | PASS |
| MD event 21 parent 一致 | PASS |
| MD event 33 存在于原始流 | PASS |
| MD event 33 kind 一致 | PASS |
| MD event 33 parent 一致 | PASS |
| MD event 42 存在于原始流 | PASS |
| MD event 42 kind 一致 | PASS |
| MD event 42 parent 一致 | PASS |
| MD event 47 存在于原始流 | PASS |
| MD event 47 kind 一致 | PASS |
| MD event 47 parent 一致 | PASS |
| MD event 56 存在于原始流 | PASS |
| MD event 56 kind 一致 | PASS |
| MD event 56 parent 一致 | PASS |
| MD event 61 存在于原始流 | PASS |
| MD event 61 kind 一致 | PASS |
| MD event 61 parent 一致 | PASS |
| MD event 70 存在于原始流 | PASS |
| MD event 70 kind 一致 | PASS |
| MD event 70 parent 一致 | PASS |
| MD event 78 存在于原始流 | PASS |
| MD event 78 kind 一致 | PASS |
| MD event 78 parent 一致 | PASS |
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
| MD event 84 存在于原始流 | PASS |
| MD event 84 kind 一致 | PASS |
| MD event 84 parent 一致 | PASS |
| MD event 85 存在于原始流 | PASS |
| MD event 85 kind 一致 | PASS |
| MD event 85 parent 一致 | PASS |
| MD event 86 存在于原始流 | PASS |
| MD event 86 kind 一致 | PASS |
| MD event 86 parent 一致 | PASS |
| MD event 87 存在于原始流 | PASS |
| MD event 87 kind 一致 | PASS |
| MD event 87 parent 一致 | PASS |
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
