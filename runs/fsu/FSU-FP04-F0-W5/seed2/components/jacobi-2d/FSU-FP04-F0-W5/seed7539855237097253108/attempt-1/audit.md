# FSU-FP04-F0-W5 seed7539855237097253108 审计

- attempt：`attempt-1`
- sample_run_id：`s7539855237097253108`

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
| `FSU-FP04-F0-W5-seed7539855237097253108.md` | `aa229b55d40a359695e68e05fb136ab34040bbd4da294866b25e1a225b76accf` |
| `census.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `census.out` | `a83bf9a08c7f01c1600686f92a34d8f8fa586e8f29b2ef0e41175066b7a8496a` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `974fbbd9da4faaf30d71e68efc7f8fe8deda7e8d1bd4e07046b53bdcf35f203a` |
| `census/config.json` | `80c4368b925690eec2de7a7c4b1d03e53c2b453c0f753817e7331069fd030786` |
| `census/fpu_injections.log` | `a05a9807a610db15416c1398f34e24fecba5944ff6c9c3a1bfc37cfedf1db11a` |
| `census/stats.txt` | `47d768cbb36212ac894d8ec5afcddf18ab51f0f1036281c17e1d72c506d585ab` |
| `chain_report.json` | `e199f9fc4c64e7ccab115d848f47b90d673353ea9aaa6ad6fc8ba8b3acb314b3` |
| `component_manifest.json` | `92e3b6043972b836b676d6865aaf0ce5bcc455acb4c8120ecf0927fa607b5851` |
| `inject/array.bin` | `3b44577b54e90e6e9ac401c98e59e9d94fe8296aa00434348d240870a7e15cb5` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `8622c7feba677b3f11110eae342d900c8b20a4fa491e8bd35d397f7e2533ae13` |
| `inject/config.json` | `967123bd9c9b516fa57adbc65e42ee69e6b5c0ae5e09e9c8a20218b70d007b33` |
| `inject/fpu_injections.log` | `39c4cf9d88a0bfdcce6cc60c295cb0d25193a6048a6f8d85cdf4118fdd676abf` |
| `inject/prop_evt.txt.gz` | `7a1c7400fc92530592291a26e35495c61a699b7d19943c24846dcbf903295cb1` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `2c22cea2ccad88d9e2fbc01c4d5a34f2adedfa3f606a9edfbd616b4abc9348dc` |
| `manifest.json` | `8e4edf41730fa1fd8dc7399247d64ff409d04e65a252d8af8ebc03fa2482c09a` |
| `oracle.json` | `2b5ed54633fed301a3274ad04c3fb6c879c5482855cc673b8ceaf31fda9c0096` |
| `oracle_elements.json` | `59beb6d806575eff00fba3e2be01dd599cbb5324f13f34f868c3c81df5322060` |
| `run.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `run.out` | `2acdfe99f0c7bac75bf154a4a12e9f2ea5596fe581bba5061d55c9954d65ee61` |
| `stats.txt` | `2c22cea2ccad88d9e2fbc01c4d5a34f2adedfa3f606a9edfbd616b4abc9348dc` |

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
