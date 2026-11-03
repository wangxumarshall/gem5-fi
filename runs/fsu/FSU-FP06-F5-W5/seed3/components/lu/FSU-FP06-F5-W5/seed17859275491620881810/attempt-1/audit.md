# FSU-FP06-F5-W5 seed17859275491620881810 审计

- attempt：`attempt-1`
- sample_run_id：`s17859275491620881810`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '7', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓
- `7` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed17859275491620881810.md` | `11f1e3e1a4345c85b90bf85b800be34145a398c8a024fa37476bbebd8371ba43` |
| `census.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `census.out` | `c4ccb56d248c8b86b7a67db218f9a3af219e5b9ad128c6db50e16319b5880c06` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `c1858c3285fcc9f319d714375ea1898cafbc4b0eee55d8cd904889bd49f1e153` |
| `census/config.json` | `acb5b8b4f79a45b4540ced7205c13a86fcb0de3ba3e503a9952deb843069c509` |
| `census/fpu_injections.log` | `d1d2884aa2699eaa8cd3fe8e5c4f4aafda42e8e12126229c5ffd600c9ad1e806` |
| `census/stats.txt` | `14775312315dbb5ddd396266780be8f3b12b93fbf2906bfa7b691a4eec768125` |
| `chain_report.json` | `571c8fd4c5478dafa0fe8bf2d4b9fa1567cd54f07a6bcd86321d4514dc941869` |
| `component_manifest.json` | `9d73f5afdea9a64a48ba94869025c1eee2dc252849fc666d3d9c1b39d6f01923` |
| `inject/array.bin` | `e2e2708e2802947fd54306f2d71e8f20f5da4931f4109690bbeb7b888b0d05c8` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `1a7bc66bc980290419ce15535b3816a7002ab60412c98ccd7bb5c1886c01fccc` |
| `inject/config.json` | `f4ed900c95b257f9c5c7c9c22281496072848d4afffcbfe90684996f60d4cec7` |
| `inject/fpu_injections.log.gz` | `15355a14f5d5f3698db9569830bacde433ed21204761b1c9604b03798b611c9b` |
| `inject/prop_evt.txt.gz` | `9b7bfe93a778e6aff600e25b5a5e8ef52d6f4bcb3eeaef4c7721482392112bb7` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `4699b104382d824ff057246d31fbf73aa6c0610a4572e41d71d0fb66304ed14c` |
| `injection_log_storage.json` | `705e2da2cea1d4a0a65e6129864c8460132c4450b3e5236455ea8b4cfa700404` |
| `manifest.json` | `c6d7002088f99f62eb2f2d74c5c2b7692cf8b1304c821dbed50c589d31078cfa` |
| `oracle.json` | `8224163a7ed60a33496e7570002ea86d6fa7a37a53a2981bba9d1cd142550c99` |
| `oracle_elements.json` | `38f86789486222bd43d18f659f184f7bb13c918a95398cff5c17ac7a34611b06` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `275417e438185e5b3593debe4a5dc1169c71ecd6caf42b329cc6522115dc3e96` |
| `stats.txt` | `4699b104382d824ff057246d31fbf73aa6c0610a4572e41d71d0fb66304ed14c` |

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
| MD event 2 存在于原始流 | PASS |
| MD event 2 kind 一致 | PASS |
| MD event 2 parent 一致 | PASS |
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
| MD event 520 存在于原始流 | PASS |
| MD event 520 kind 一致 | PASS |
| MD event 520 parent 一致 | PASS |
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
