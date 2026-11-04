# FSU-FR07-F0-W5 seed10343971370867151644 审计

- attempt：`attempt-1`
- sample_run_id：`s10343971370867151644`

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
| `FSU-FR07-F0-W5-seed10343971370867151644.md` | `1b0856dfd7b8238015dad23d460512d3ff53e99994e48648bc37f18f2952a994` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `887aa76652ca2f4af7d52f1957e1f34c611a8f78aeb4998513b9e4e1ce9c677a` |
| `census/config.json` | `6ee8744a34291a733d547fe54d34d1878fb6bc9499f596fe9b7715f0f917e1b7` |
| `census/fpu_injections.log` | `c9116a76ae73b161bb541b8dc59355881f9ff80d9c5d6f512e36e94acba2210b` |
| `census/stats.txt` | `688e509d5c8a440122186305f8b8172d9dc48e99b85d5cfff29c976e2955c0d7` |
| `chain_report.json` | `d9c6ea6b7e5cc8b314eec6c0d93ce1974272e92089d11cd8b124c10ba14774a7` |
| `component_manifest.json` | `021b4d41b09cf505e43a0172963997e76326e0680813631f487e0654cb8158e5` |
| `inject/array.bin` | `179741a7dc86fa4480eed3d7cc1d2d1462d1f4ee4d5c059a2b2559109822c2b2` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `4c1256cab30b889c21e20b81c6f66e6aab4332d319e3da83ded6e6fe8ad7e67f` |
| `inject/config.json` | `25b1f695b0ce30c313b4cb545d8dc210a04d14493a502064c77d021aca4c531e` |
| `inject/fpu_injections.log` | `13e12e376d892e875606831cffb81841080a4bcf2aa8e99f07ae7a601ddc9db6` |
| `inject/prop_evt.txt.gz` | `9da7c2638c815492b65960b506b9d8e0a76206e5ab60b510b2e33be74d3de099` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `4fdcd78d0e60d2b968e6baef789096706dc84e73fd93774af05099983a083146` |
| `manifest.json` | `4a9bd9028b2dd544abdc228499566cdd4d89f9fb40247ffa4b1c459161e88684` |
| `oracle.json` | `64d586414e97f779d2cc1cc938506bd8f017dd53e7c4cbf5a37f4d8a46355585` |
| `oracle_elements.json` | `63124b337fe574868d14f0376302b9f14674d66bfa8f71c219898b1b629a1ed9` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `551d9895ccf4df19f5f3e2bee681697bf21b33a982bfcf59500b687ba8d3eb16` |
| `stats.txt` | `4fdcd78d0e60d2b968e6baef789096706dc84e73fd93774af05099983a083146` |

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
